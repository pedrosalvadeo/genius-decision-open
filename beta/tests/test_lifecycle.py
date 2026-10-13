"""Adversarial lifecycle test: real worker, controlled long-lived engine subtree."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest

from genius_beta.app import create_app
from genius_beta.db import connect
from genius_beta.worker import Worker

BASE=Path(__file__).resolve().parents[1]


def active(pid):
    try:
        # A zombie cannot execute or publish; container init may reap later.
        return Path(f'/proc/{pid}/stat').read_text().split(') ',1)[1].split()[0]!='Z'
    except (FileNotFoundError, ProcessLookupError):
        # Linux can reap the process between opening and reading /proc/.../stat.
        return False


@unittest.skipUnless(sys.platform=='linux','Production parent-death guard requires Linux')
class LifecycleTests(unittest.TestCase):
    def test_worker_sigkill_terminates_engine_group_and_recovery_does_not_publish(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            config=dict(DATA_DIR=str(root),DATABASE=str(root/'genius.sqlite3'),SUSPEND_FILE=str(root/'SUSPENDED'),PUBLIC_URL='http://localhost',TESTING=True)
            app=create_app(config)
            client=app.test_client()
            response=client.post('/api/register',json=dict(username='lifecycle',password='A-long-password-123',privacy_accepted=True,privacy_version=app.config['PRIVACY_VERSION'],adult_confirmed=True))
            csrf={'X-CSRF-Token':response.json['csrf_token']}
            payload=json.loads((BASE/'examples'/'hours-known.json').read_text())
            profile=payload.pop('profile')
            cid=client.post('/api/cases',json=dict(title='Lifecycle',profile=profile,input=payload),headers=csrf).json['case']['id']
            jid=client.post('/api/cases/'+cid+'/run',json={},headers=csrf).json['job']['id']
            engine=root/'controlled_engine.py'
            engine.write_text('''import json,os,signal,subprocess,sys,time
from pathlib import Path
from genius_beta.engine_job import install_parent_death_guard
install_parent_death_guard()
sys.stdin.buffer.read()
# The received controller replaces SIGTERM; parent-death must still work.
signal.signal(signal.SIGTERM,lambda *_: None)
child=subprocess.Popen([sys.executable,'-c',"import os,time;print(os.readlink('/proc/self'),flush=True);time.sleep(60)"],stdout=subprocess.PIPE,text=True)
host=Path('/proc/self').resolve().name
descendant_host=child.stdout.readline().strip()
Path(sys.argv[1]).write_text(json.dumps({'engine':os.getpid(),'descendant':child.pid,'proc_engine':int(host),'proc_descendant':int(descendant_host)}))
time.sleep(60)
''')
            harness=root/'worker_harness.py'
            harness.write_text('''import json,subprocess,sys
from genius_beta.worker import Worker
real=subprocess.Popen
def wrapped(command,*args,**kwargs):
    if len(command)>2 and command[2]=='genius_beta.engine_job':
        command=[sys.executable,sys.argv[2],sys.argv[3]]
    return real(command,*args,**kwargs)
subprocess.Popen=wrapped
worker=Worker(json.loads(sys.argv[1]))
worker.acquire()
try: worker.run_once()
finally: worker.close()
''')
            ready=root/'ready.json'
            parent=subprocess.Popen([sys.executable,str(harness),json.dumps(config),str(engine),str(ready)],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
            pids=None
            try:
                deadline=time.monotonic()+8
                while time.monotonic()<deadline and not ready.exists() and parent.poll() is None:
                    time.sleep(.02)
                self.assertTrue(ready.exists(),'Controlled engine failed to start')
                pids=json.loads(ready.read_text())
                proc_pids=[pids['proc_engine'],pids['proc_descendant']]
                self.assertTrue(all(active(pid) for pid in proc_pids), str({'pids':pids,'parent':parent.poll()}))
                os.kill(parent.pid,signal.SIGKILL)
                self.assertEqual(parent.wait(timeout=3),-signal.SIGKILL)
                deadline=time.monotonic()+3
                while time.monotonic()<deadline and any(active(pid) for pid in proc_pids):
                    time.sleep(.02)
                self.assertFalse(any(active(pid) for pid in proc_pids),'Engine process group survived worker SIGKILL')
                with connect(config['DATABASE']) as db:
                    job=db.execute('SELECT status,result_json FROM jobs WHERE id=?',(jid,)).fetchone()
                    self.assertEqual(job['status'],'running')
                    self.assertIsNone(job['result_json'])
                    self.assertEqual(db.execute('SELECT count(*) FROM artifacts').fetchone()[0],0)
                receiver=Worker(config)
                receiver.acquire()
                try:
                    job=client.get('/api/jobs/'+jid).json['job']
                    self.assertEqual(job['status'],'interrupted')
                    self.assertIsNone(job['result'])
                    self.assertEqual(list((root/'tmp').iterdir()),[])
                finally:
                    receiver.close()
            finally:
                if parent.poll() is None:
                    parent.kill()
                    parent.wait(timeout=3)
                if pids and active(pids['proc_engine']):
                    os.killpg(pids['engine'],signal.SIGKILL)
                parent.stderr.close()


if __name__=='__main__':
    unittest.main()
