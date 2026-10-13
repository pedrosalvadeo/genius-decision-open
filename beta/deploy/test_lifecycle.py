"""Real HTTP/worker lifecycle tests, separate from platform privilege tests.

This runtime maps only UID 0 and has no Docker daemon. The harness exercises
supervise() directly with actual services; it DOES NOT test or bypass the
production main() privilege check. Non-root bootstrap remains a cloud gate.
"""
import json
import os
from pathlib import Path
import re
import signal
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[2]


def run():
    results = []
    harness = """import sys
sys.path.insert(0,sys.argv[1])
from start import supervise,service_commands
from genius_beta.config import settings
from genius_beta.db import initialize
initialize(settings()['DATABASE'])
raise SystemExit(supervise(service_commands(int(sys.argv[2]))))
"""
    for mode in ('graceful_shutdown', 'peer_failure_shutdown'):
        with tempfile.TemporaryDirectory(prefix='genius-lifecycle-') as directory:
            with socket.socket() as sock:
                sock.bind(('127.0.0.1', 0))
                port = sock.getsockname()[1]
            env = {'PATH': os.defpath, 'LANG': 'C.UTF-8', 'PYTHONDONTWRITEBYTECODE': '1',
                   'PYTHONPATH': os.pathsep.join([os.environ.get('PYTHONPATH', ''), str(ROOT/'beta'), str(ROOT/'product_local'), str(ROOT/'consumer_views')]),
                   'GENIUS_ENV': 'development', 'GENIUS_DATA_DIR': directory,
                   'GENIUS_PUBLIC_URL': f'http://127.0.0.1:{port}', 'PORT': str(port)}
            log_path = Path(directory) / 'runtime.log'
            with log_path.open('w') as log:
                process = subprocess.Popen([sys.executable, '-c', harness, str(ROOT/'beta/deploy'), str(port)], env=env, cwd=ROOT, stdout=log, stderr=log)
                descendants = []
                try:
                    deadline = time.monotonic()+10
                    while time.monotonic()<deadline:
                        if process.poll() is not None:
                            raise RuntimeError('Early service exit: '+log_path.read_text())
                        try:
                            with urllib.request.urlopen(f'http://127.0.0.1:{port}/api/health', timeout=1) as response:
                                if response.status==200:
                                    break
                        except OSError:
                            time.sleep(.1)
                    else:
                        raise RuntimeError('Health timeout')
                    direct = {int(index):int(pid) for index,pid in re.findall(r'service_child_started index=(\d+) pid=(\d+)',log_path.read_text())}
                    assert set(direct)=={0,1}, direct
                    descendants = list(direct.values())
                    started = time.monotonic()
                    if mode=='graceful_shutdown':
                        process.send_signal(signal.SIGTERM)
                    else:
                        os.kill(direct[1], signal.SIGKILL)
                    code = process.wait(timeout=10)
                    assert code==(0 if mode=='graceful_shutdown' else 1), code
                    reaped = re.findall(r'service_child_reaped index=(\d+) returncode=(-?\d+)',log_path.read_text())
                    assert {index for index,_ in reaped}=={'0','1'}, reaped
                    try:
                        urllib.request.urlopen(f'http://127.0.0.1:{port}/api/health',timeout=.5)
                    except OSError:
                        pass
                    else:
                        raise AssertionError('HTTP listener survived supervisor shutdown')
                    results.append({'test':mode,'result':'PASS','health_http_status':200,'exit_code':code,
                                    'shutdown_seconds':round(time.monotonic()-started,3),'direct_children_reaped':2,'http_listener_stopped':True})
                finally:
                    if process.poll() is None:
                        process.terminate()
                        try:
                            process.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            process.kill()
                            process.wait()
    report = {'environment':'local Python 3.12; real Gunicorn and durable worker; process supervision harness',
              'effective_test_uid':os.geteuid(),'tests':results,
              'limitations':['Only UID 0 is mapped in this runtime; bootstrap UID10001 could not be exercised.',
                             'Production main privilege guard remains mandatory and unchanged.',
                             'Docker build, Railway volume and HTTPS were not tested.']}
    target=ROOT/'beta/evidence/supervisor.json'
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    run()
