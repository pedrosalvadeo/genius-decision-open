"""Run all local HTTP actors in one namespace, with a fresh synthetic database."""
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request

root = Path(__file__).resolve().parents[2]
env = dict(os.environ)
env['PYTHONPATH'] = os.pathsep.join([str(root/'beta'),str(root/'product_local'),str(root/'consumer_views'),env.get('PYTHONPATH','')])
env['PYTHONDONTWRITEBYTECODE'] = '1'
with socket.socket() as sock:
    sock.bind(('127.0.0.1',0))
    port = sock.getsockname()[1]
env['GENIUS_PUBLIC_URL'] = env['GENIUS_TEST_URL'] = f'http://127.0.0.1:{port}'
with tempfile.TemporaryDirectory(prefix='genius-browser-synthetic-') as directory:
    env['GENIUS_DATA_DIR'] = directory
    server = subprocess.Popen([sys.executable,'-B','-m','gunicorn','--bind',f'127.0.0.1:{port}','--workers','1','--threads','4','genius_beta.app:create_app()'],env=env)
    worker = None
    try:
        for _ in range(100):
            if server.poll() is not None:
                raise RuntimeError('HTTP server did not start')
            try:
                urllib.request.urlopen(env['GENIUS_TEST_URL']+'/api/health',timeout=1).read()
                break
            except OSError:
                time.sleep(.1)
        else:
            raise RuntimeError('HTTP readiness timeout')
        worker = subprocess.Popen([sys.executable,'-B','-m','genius_beta.worker'],env=env)
        result = subprocess.run(['node',str(root/'beta/tests/browser_e2e.cjs')],env=env,timeout=120)
        raise SystemExit(result.returncode)
    finally:
        for p in (worker,server):
            if p is not None:
                p.terminate()
                try:p.wait(timeout=8)
                except subprocess.TimeoutExpired:p.kill();p.wait()
