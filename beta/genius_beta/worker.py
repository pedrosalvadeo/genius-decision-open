"""Single bounded worker; SQLite queue survives process restarts, retries are explicit."""
import base64
import contextlib
import fcntl
import hashlib
import json
import os
from pathlib import Path
import selectors
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from .config import settings
from .db import connect, dump, initialize, purge, transaction


class Worker:
    def __init__(self, config=None):
        self.config=settings(config)
        initialize(self.config['DATABASE'])
        self.db=connect(self.config['DATABASE'])
        self.stopping=False
        self.child=None
        self.lock=None
        self.mission_turn=True

    def acquire(self):
        self.lock=open(str(self.config['DATABASE'])+'.worker.lock','a+')
        try:
            fcntl.flock(self.lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except OSError:
            self.lock.close()
            self.lock=None
            raise RuntimeError('A worker already owns this database')
        self.recover()

    def recover(self):
        self.db.execute("UPDATE jobs SET status='interrupted',error='worker_restart',finished_at=? WHERE status='running'",(int(time.time()),))
        from .mission_worker import recover
        recover(self.db,self.config)
        work=self.config['DATA_DIR']/'tmp'
        if work.exists():
            shutil.rmtree(work)
        work.mkdir(mode=0o700,parents=True,exist_ok=True)

    def stop(self,*_):
        self.stopping=True

    def terminate_child(self):
        if self.child and self.child.poll() is None:
            with contextlib.suppress(ProcessLookupError):
                os.killpg(self.child.pid,signal.SIGTERM)
            try:
                self.child.wait(timeout=2)
            except subprocess.TimeoutExpired:
                with contextlib.suppress(ProcessLookupError):
                    os.killpg(self.child.pid,signal.SIGKILL)
                self.child.wait(timeout=2)

    def run_once(self):
        if self.stopping or self.config['SUSPEND_FILE'].exists():
            return False
        from .mission_worker import run_once as run_mission
        if self.mission_turn:
            self.mission_turn=False
            if run_mission(self):
                return True
        self.mission_turn=True
        # Check before opening a transaction; mission execution has its own commits.
        if not self.db.execute("SELECT 1 FROM jobs WHERE status='queued' LIMIT 1").fetchone():
            return run_mission(self)
        with transaction(self.db):
            self.db.execute("""UPDATE jobs SET status='cancelled',error='agent_expired',finished_at=?
                WHERE status='queued' AND case_id IN (SELECT cases.id FROM cases JOIN agent_accounts
                ON agent_accounts.user_id=cases.user_id WHERE agent_accounts.expires_at<=?)""",
                (int(time.time()),int(time.time())))
            job=self.db.execute("SELECT jobs.*,revisions.input_json,cases.profile FROM jobs JOIN revisions ON revisions.case_id=jobs.case_id AND revisions.version=jobs.revision JOIN cases ON cases.id=jobs.case_id WHERE jobs.status='queued' ORDER BY jobs.created_at,jobs.id LIMIT 1").fetchone()
            if not job:
                return False
            self.db.execute("UPDATE jobs SET status='running',started_at=? WHERE id=?",(int(time.time()),job['id']))
        payload=json.loads(job['input_json'])
        payload['profile']=job['profile']
        work=self.config['DATA_DIR']/'tmp'
        work.mkdir(mode=0o700,parents=True,exist_ok=True)
        status,result,archive,error='failed',None,None,'engine_failed'
        started=time.monotonic()
        with tempfile.TemporaryDirectory(prefix='job-',dir=work) as temp:
            # Deliberately do not inherit provider credentials or application secrets.
            env={'PATH':os.defpath,'PYTHONPATH':str(Path(__file__).resolve().parents[1]),'PYTHONDONTWRITEBYTECODE':'1','LANG':'C.UTF-8','GENIUS_WORKER_PID':str(os.getpid())}
            try:
                self.child=subprocess.Popen([sys.executable,'-m','genius_beta.engine_job',temp],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,env=env,start_new_session=True,cwd=temp)
                self.child.stdin.write(dump(payload).encode())
                self.child.stdin.close()
                selector=selectors.DefaultSelector()
                selector.register(self.child.stdout,selectors.EVENT_READ)
                output=bytearray()
                while True:
                    row=self.db.execute('SELECT cancel_requested FROM jobs WHERE id=?',(job['id'],)).fetchone()
                    if self.stopping:
                        status,error='interrupted','worker_stopped'
                        break
                    if not row or row['cancel_requested']:
                        status,error='cancelled','cancelled'
                        break
                    if self.config['SUSPEND_FILE'].exists():
                        status,error='interrupted','service_suspended'
                        break
                    if time.monotonic()-started>self.config['ENGINE_TIMEOUT']:
                        error='execution_timeout'
                        break
                    events=selector.select(timeout=.1)
                    for key,_ in events:
                        chunk=os.read(key.fileobj.fileno(),65536)
                        if chunk:
                            output.extend(chunk)
                        else:
                            selector.unregister(key.fileobj)
                    if len(output)>self.config['ENGINE_OUTPUT_BYTES']:
                        error='output_limit'
                        break
                    if self.child.poll() is not None and not selector.get_map():
                        if self.child.returncode!=0:
                            error='engine_rejected_or_failed'
                            break
                        decoded=json.loads(output)
                        if 'admission_error' in decoded:
                            error='admission_rejected:'+decoded['admission_error']
                            break
                        result=dump(decoded['result'])
                        archive=base64.b64decode(decoded['archive_b64'],validate=True)
                        if len(archive)>1024*1024 or hashlib.sha256(archive).hexdigest()!=decoded['archive_sha256']:
                            raise ValueError('invalid artifact')
                        status,error='completed',None
                        break
                selector.close()
            except (OSError,ValueError,KeyError,TypeError):
                status,error='failed','engine_protocol_error'
            finally:
                self.terminate_child()
                if self.child:
                    if self.child.stdout:
                        self.child.stdout.close()
                    if self.child.stdin and not self.child.stdin.closed:
                        self.child.stdin.close()
                self.child=None
        with transaction(self.db):
            row=self.db.execute('SELECT jobs.*,cases.user_id FROM jobs JOIN cases ON cases.id=jobs.case_id WHERE jobs.id=?',(job['id'],)).fetchone()
            if not row:
                return True
            if row['cancel_requested']:
                status,result,archive,error='cancelled',None,None,'cancelled'
            if status=='completed':
                from .twin_integration import storage_bytes
                pages=storage_bytes(self.config['DATA_DIR'])
                if pages+len(result.encode())+len(archive)>self.config['MAX_DATABASE_BYTES'] or shutil.disk_usage(self.config['DATA_DIR']).free<self.config['MIN_FREE_BYTES']+len(archive)+len(result.encode()):
                    status,result,archive,error='failed',None,None,'storage_capacity'
            self.db.execute('UPDATE jobs SET status=?,result_json=?,error=?,finished_at=? WHERE id=?',(status,result if status=='completed' else None,error,int(time.time()),job['id']))
            self.db.execute('UPDATE cases SET updated_at=? WHERE id=?',(int(time.time()),job['case_id']))
            if status=='completed':
                self.db.execute('INSERT INTO artifacts VALUES(?,?,?,?)',(job['id'],archive,hashlib.sha256(archive).hexdigest(),len(archive)))
            self.db.execute('INSERT INTO telemetry(event,created_at) VALUES(?,?)',('job_'+status,int(time.time())))
        return True

    def close(self):
        self.terminate_child()
        self.db.close()
        if self.lock:
            self.lock.close()
            self.lock=None

    def run(self):
        self.acquire()
        signal.signal(signal.SIGTERM,self.stop)
        signal.signal(signal.SIGINT,self.stop)
        last_purge=0
        try:
            while not self.stopping:
                if time.monotonic()-last_purge>3600:
                    from .r2_backup import BackupError
                    try:
                        purge(self.db,self.config['RETENTION_DAYS'])
                        from .twin_integration import purge_twins
                        purge_twins(self.config, self.db)
                    except BackupError:
                        print('retention_purge_pending_remote_privacy', flush=True)
                    last_purge=time.monotonic()
                if not self.run_once():
                    time.sleep(.25)
        finally:
            self.close()


if __name__=='__main__':
    Worker().run()
