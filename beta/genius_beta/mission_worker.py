"""One mission in the existing worker, with durable stage ACKs and bounded IPC."""
import base64
import contextlib
import fcntl
import json
import os
from pathlib import Path
import selectors
import subprocess
import sys
import tempfile
import time
from .db import dump, transaction
from .mission_state import digest, MAX_BUNDLE
from . import regulation

STAGES = ('measure','represent','evaluate','act','observe','remember')
ARTIFACT_NAMES = {
    'source_distribution_v1': ('source.tar','source.tar.gz','source.zip'),
    'resource_calibration_v1': ('resource-estimate.json',),
}

def recover(db, config=None):
    db.execute("UPDATE adaptive_missions SET status=CASE WHEN attempts<3 THEN 'queued' ELSE 'interrupted' END,error='WORKER_RESTART' WHERE status='running'")
    if config is not None:
        regulation.recover(db,config)

def run_once(worker, after_checkpoint=None):
    if not worker.config['ADAPTIVE_ENABLED']:
        return False
    if worker.stopping or worker.config['SUSPEND_FILE'].exists():
        return False
    regulation.refresh(worker.db,worker.config)
    # Share compiler capacity with synchronous twin evaluations.
    folder = worker.config['DATA_DIR'] / 'twin-locks'
    folder.mkdir(mode=0o700, parents=True, exist_ok=True)
    with (folder / 'compiler.lock').open('a+b') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return False
        return execute(worker, after_checkpoint)

def execute(worker, after_checkpoint):
    db = worker.db
    with transaction(db):
        db.execute("UPDATE adaptive_missions SET status='cancelled',error='AGENT_EXPIRED' WHERE status IN ('queued','running') AND user_id IN (SELECT user_id FROM agent_accounts WHERE expires_at<=?)", (int(time.time()),))
        row = db.execute("SELECT * FROM adaptive_missions WHERE status='queued' ORDER BY updated_at,id LIMIT 1").fetchone()
        if not row:
            return False
        control = regulation.refresh(db,worker.config,force=True)
        if not regulation.starts(control):
            return False
        control_token = regulation.begin(db,worker.config,control)
        db.execute("UPDATE adaptive_missions SET status='running',attempts=attempts+1,updated_at=? WHERE id=?", (int(time.time()),row['id']))
    mid = row['id']
    mission_input = json.loads(row['input_json'])
    kind = mission_input.get('kind', 'source_distribution_v1')
    payload = dict(id=mid, input=mission_input)
    if row['state_bundle'] is not None:
        payload.update(state=base64.b64encode(row['state_bundle']).decode(), state_sha256=row['state_sha256'])
    root = Path(__file__).resolve().parents[2]
    env = dict(PATH=os.defpath, MALLOC_ARENA_MAX='2', PYTHONPATH=os.pathsep.join(str(root/p) for p in ('beta','adaptive','twin','kernel','product_local','consumer_views')),
               PYTHONDONTWRITEBYTECODE='1', LANG='C.UTF-8', GENIUS_WORKER_PID=str(os.getpid()))
    work = worker.config['DATA_DIR'] / 'tmp'
    work.mkdir(mode=0o700, parents=True, exist_ok=True)
    started = time.monotonic()
    final, status, reason = None, 'failed', 'MISSION_PROCESS_FAILED'
    try:
        with tempfile.TemporaryDirectory(prefix='mission-', dir=work) as temp:
            worker.child = subprocess.Popen([sys.executable,'-m','genius_beta.mission_job',temp],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                env=env, start_new_session=True, cwd=temp)
            worker.child.stdin.write((dump(payload)+'\n').encode())
            worker.child.stdin.flush()
            buffer, total = bytearray(), 0
            with selectors.DefaultSelector() as selector:
                selector.register(worker.child.stdout, selectors.EVENT_READ)
                while final is None:
                    regulation.refresh(db,worker.config)
                    active = db.execute("SELECT m.status,m.cancel_requested,a.expires_at FROM adaptive_missions m LEFT JOIN agent_accounts a ON a.user_id=m.user_id WHERE m.id=?", (mid,)).fetchone()
                    if not active or active['status'] != 'running' or active['cancel_requested']:
                        status,reason='cancelled','CANCELLED'
                        break
                    if active['expires_at'] is not None and active['expires_at'] <= int(time.time()):
                        status,reason='cancelled','AGENT_EXPIRED'
                        break
                    if worker.stopping or worker.config['SUSPEND_FILE'].exists():
                        status,reason='interrupted','WORKER_STOPPED'
                        break
                    if time.monotonic()-started > 60:
                        reason='MISSION_TIMEOUT'
                        break
                    ready = selector.select(.1)
                    if not ready:
                        continue
                    chunk = os.read(worker.child.stdout.fileno(),65536)
                    if not chunk:
                        break
                    buffer.extend(chunk); total += len(chunk)
                    if len(buffer) > 2*MAX_BUNDLE or total > 16*MAX_BUNDLE:
                        raise ValueError('IPC_BUDGET')
                    while b'\n' in buffer:
                        line, _, rest = buffer.partition(b'\n'); buffer = bytearray(rest)
                        message = json.loads(line)
                        if message.get('type') != 'checkpoint':
                            final = message
                            break
                        raw = base64.b64decode(message['state'], validate=True)
                        stage = message['stage']
                        if stage not in STAGES or len(raw)>MAX_BUNDLE or digest(raw)!=message['sha256']:
                            raise ValueError('CHECKPOINT_INVALID')
                        # Capacity recheck includes unrelated writers since admission.
                        from .twin_integration import storage_bytes
                        if storage_bytes(worker.config['DATA_DIR']) + len(raw) > worker.config['MAX_DATABASE_BYTES']:
                            reason='STORAGE_CAPACITY'
                            break
                        with transaction(db):
                            changed = db.execute("UPDATE adaptive_missions SET state_bundle=?,state_sha256=?,last_stage=?,updated_at=? WHERE id=? AND status='running' AND cancel_requested=0", (raw,digest(raw),stage,int(time.time()),mid)).rowcount
                        if not changed:
                            status,reason='cancelled','CANCELLED'
                            break
                        if after_checkpoint:
                            after_checkpoint(stage)  # local fault-injection only; never exposed through API
                        worker.child.stdin.write(b'ACK\n'); worker.child.stdin.flush()
                    if reason == 'STORAGE_CAPACITY' or status == 'cancelled':
                        break
            if final:
                if final.get('type') == 'completed':
                    artifact = base64.b64decode(final['artifact'], validate=True)
                    if len(artifact)>262144 or digest(artifact)!=final['artifact_sha256'] or final['artifact_name'] not in ARTIFACT_NAMES.get(kind, ()):
                        raise ValueError('ARTIFACT_INVALID')
                    if final['result'].get('status') != 'completed':
                        raise ValueError('RESULT_INVALID')
                    with transaction(db):
                        changed = db.execute("UPDATE adaptive_missions SET status='completed',result_json=?,artifact=?,artifact_name=?,artifact_sha256=?,error=NULL,updated_at=? WHERE id=? AND status='running' AND cancel_requested=0 AND last_stage='remember'", (dump(final['result']),artifact,final['artifact_name'],digest(artifact),int(time.time()),mid)).rowcount
                        regulation.finish(db,worker.config,control_token,'completed' if changed else 'cancelled',None)
                    return True
                if final.get('type') == 'failed':
                    reason='MISSION_EXECUTION_FAILED'
                if final.get('type') == 'needs_review':
                    status,reason='needs_review','STATE_OR_RUNTIME_REQUIRES_REVIEW'
    except (ValueError, KeyError, OSError, subprocess.SubprocessError):
        status,reason='failed','MISSION_PROTOCOL_FAILED'
    finally:
        worker.terminate_child()
        if worker.child:
            for stream in (worker.child.stdin, worker.child.stdout):
                with contextlib.suppress(OSError):
                    stream.close()
            worker.child = None
    with transaction(db):
        changed = db.execute("UPDATE adaptive_missions SET status=?,error=?,updated_at=? WHERE id=? AND status='running'", (status,reason,int(time.time()),mid)).rowcount
        regulation.finish(db,worker.config,control_token,status if changed else 'cancelled',reason)
    return True
