"""Isolated synthetic acceptance over verified TLS. Does not publish or certify Railway.

Starts real Gunicorn and worker against temporary SQLite, with a one-day local
certificate explicitly trusted by the test client. No TLS verification bypass.
Public controller placeholders are confined to this disposable test environment;
the production supervisor/mount/provider guards are not exercised by this test.
"""
import hashlib
import http.cookiejar
import json
import os
from pathlib import Path
import secrets
import socket
import ssl
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[2]


def main():
    checks = []
    with tempfile.TemporaryDirectory(prefix='genius-tls-synthetic-') as directory:
        data = Path(directory)
        cert, key = data/'cert.pem', data/'key.pem'
        subprocess.run(['openssl','req','-x509','-newkey','rsa:2048','-nodes',
            '-keyout',str(key),'-out',str(cert),'-days','1','-subj','/CN=localhost',
            '-addext','subjectAltName=DNS:localhost,IP:127.0.0.1',
            '-addext','basicConstraints=critical,CA:TRUE'], check=True, capture_output=True)
        with socket.socket() as sock:
            sock.bind(('127.0.0.1',0))
            port = sock.getsockname()[1]
        base = f'https://localhost:{port}'
        env = {**os.environ, 'GENIUS_DATA_DIR':str(data), 'GENIUS_ENV':'production',
            'GENIUS_PUBLIC_URL':base, 'GENIUS_REGISTRATION_OPEN':'false',
            'GENIUS_PRIVACY_CONTROLLER':'SYNTHETIC LOCAL TEST ONLY',
            'GENIUS_PRIVACY_ADDRESS':'SYNTHETIC LOCAL TEST ONLY',
            'GENIUS_PRIVACY_CONTACT':'synthetic@example.invalid', 'PYTHONDONTWRITEBYTECODE':'1'}
        env['PYTHONPATH'] = os.pathsep.join([str(ROOT/'beta'),str(ROOT/'product_local'),
            str(ROOT/'consumer_views'),env.get('PYTHONPATH','')])
        context = ssl.create_default_context(cafile=str(cert))

        def client():
            return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()),
                urllib.request.HTTPSHandler(context=context))

        def call(opener, path, method='GET', payload=None, csrf=None, expected=200, origin=base):
            headers = {'Origin':origin}
            if csrf: headers['X-CSRF-Token'] = csrf
            if payload is not None: headers['Content-Type'] = 'application/json'
            request = urllib.request.Request(base+path, method=method, headers=headers,
                data=json.dumps(payload).encode() if payload is not None else None)
            try: response = opener.open(request, timeout=10)
            except urllib.error.HTTPError as error: response = error
            with response:
                raw = response.read()
                assert response.status == expected, (path, response.status, expected)
                body = json.loads(raw) if 'application/json' in response.headers.get('Content-Type','') else raw
                return body, response.headers

        actors = []
        log = open(data/'actors.log','wb')

        def stop():
            for proc in actors: proc.terminate()
            for proc in actors:
                try: proc.wait(timeout=10)
                except subprocess.TimeoutExpired: proc.kill(); proc.wait()
            actors.clear()

        def start(opening):
            env['GENIUS_REGISTRATION_OPEN'] = 'true' if opening else 'false'
            actors.append(subprocess.Popen([sys.executable,'-B','-m','gunicorn','--bind',f'127.0.0.1:{port}',
                '--certfile',str(cert),'--keyfile',str(key),'--workers','1','--threads','4',
                'genius_beta.app:create_app()'], env=env, stdout=log, stderr=log))
            actors.append(subprocess.Popen([sys.executable,'-B','-m','genius_beta.worker'], env=env, stdout=log, stderr=log))
            for _ in range(100):
                if any(proc.poll() is not None for proc in actors): raise RuntimeError('Local TLS actor exited')
                try:
                    call(client(), '/api/health')
                    return
                except (OSError, urllib.error.URLError): time.sleep(.1)
            raise RuntimeError('Local HTTPS startup timed out')

        try:
            start(False)
            cfg, _ = call(client(), '/api/config')
            assert cfg['registration_open'] is False
            call(client(),'/api/register','POST',{},expected=503)
            checks.append('production_registration_closed_before_opening')
            # A client lacking this test CA must fail: no unverified context is used.
            try:
                urllib.request.urlopen(base+'/api/health',timeout=3)
                raise AssertionError('Untrusted certificate was accepted')
            except urllib.error.URLError as error:
                assert isinstance(error.reason, ssl.SSLCertVerificationError)
            checks.append('tls_chain_and_hostname_verified_untrusted_ca_rejected')
            stop(); start(True)
            a,b = client(),client()
            password = secrets.token_urlsafe(24)
            payload = dict(username='synthetic_a',password=password,privacy_accepted=True,
                privacy_version=cfg['privacy']['version'],adult_confirmed=True)
            account, headers = call(a,'/api/register','POST',payload,expected=201)
            csrf = account['csrf_token']
            cookie = headers['Set-Cookie']
            assert all(flag in cookie for flag in ('Secure','HttpOnly','SameSite=Strict'))
            assert headers.get('Strict-Transport-Security')
            assert headers.get('Cache-Control') == 'no-store'
            call(b,'/api/register','POST',{**payload,'username':'synthetic_b'},expected=201)
            checks.append('two_accounts_secure_cookie_hsts_no_store')
            call(a,'/api/tokens','POST',{'label':'synthetic'},expected=403)
            call(a,'/api/tokens','POST',{'label':'synthetic'},csrf=csrf,origin='https://evil.invalid',expected=403)
            checks.append('csrf_and_foreign_origin_rejected')
            example = json.loads((ROOT/'beta/examples/hours-known.json').read_text())
            profile = example.pop('profile')
            created,_ = call(a,'/api/cases','POST',dict(title='Synthetic TLS acceptance',profile=profile,input=example),csrf,201)
            cid = created['case']['id']
            queued,_ = call(a,f'/api/cases/{cid}/run','POST',{},csrf,202)
            jid = queued['job']['id']
            deadline = time.monotonic()+40
            while True:
                current,_ = call(a,f'/api/jobs/{jid}')
                job = current['job']
                if job['status'] not in ('queued','running'): break
                if time.monotonic()>deadline: raise RuntimeError('Real engine timed out')
                time.sleep(.15)
            assert job['status'] == 'completed', job['status']
            archive,_ = call(a,job['artifacts']['url'])
            assert hashlib.sha256(archive).hexdigest() == job['artifacts']['sha256']
            for path in (f'/api/cases/{cid}',f'/api/jobs/{jid}',job['artifacts']['url']):
                call(b,path,expected=404)
            exported,_ = call(a,'/api/export')
            assert exported['cases'][0]['case']['id'] == cid
            checks.append('real_engine_artifact_hash_owner_isolation_export')
            stop(); start(False)
            recovered,_ = call(a,f'/api/jobs/{jid}')
            assert recovered['job']['artifacts']['sha256'] == job['artifacts']['sha256']
            call(client(),'/api/register','POST',payload,expected=503)
            checks.append('server_worker_restart_durable_case_closed_registration_existing_session')
            (data/'SUSPENDED').touch()
            call(a,'/api/cases','POST',{},csrf,503)
            call(a,'/api/export')
            call(a,'/api/me','DELETE',csrf=csrf,expected=204)
            call(a,'/api/me',expected=401)
            call(b,f'/api/cases/{cid}',expected=404)
            checks.append('suspension_preserves_export_and_deletion_revokes_session')
        finally:
            stop(); log.close()
    result = dict(status='PASS',synthetic=True,transport='local HTTPS with explicit test CA; verified chain and hostname',
        cloud_https_verified=False,production_supervisor_verified=False,checks=checks)
    if len(sys.argv)>1: Path(sys.argv[1]).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
