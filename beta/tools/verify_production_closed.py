"""Operator-only synthetic receipt on an already running, registration-closed beta.

Run inside the target container. Requires production, a real /data mount and an
empty account database. Creates two disposable fixtures through an in-process
registration client; the public server stays closed. Tests HTTPS, actual worker
execution, isolation and deletion. No credentials are emitted or saved.
This does not attest restart durability, volume-loss recovery or real demand.
"""
import hashlib
import http.cookiejar
import json
import os
from pathlib import Path
import secrets
import sqlite3
import ssl
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, str(Path('/app/beta/deploy')))
from start import MANAGEMENT_VARIABLES, prepare_identity, validate_runtime_environment
from genius_beta.config import settings
from genius_beta.app import create_app


def main():
    # Railway's operator console can carry its own management identity. Remove
    # those variables from this test process before creating application clients
    # or child processes. Do not read their values or change the live server env.
    removed_names = [name for name in MANAGEMENT_VARIABLES if name in os.environ]
    for name in removed_names:
        os.environ.pop(name, None)
    validate_runtime_environment()
    prepare_identity()
    c = settings()
    assert c['ENV'] == 'production' and not c['REGISTRATION_OPEN']
    base = c['PUBLIC_URL']
    assert base == 'https://geniusdecision.app'
    db = sqlite3.connect(c['DATABASE'])
    assert db.execute('SELECT count(*) FROM users').fetchone()[0] == 0
    db.close()
    checks, actors, cleanup = [], [], []
    context = ssl.create_default_context()

    def client():
        return urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()),
            urllib.request.HTTPSHandler(context=context))

    def call(opener, path, method='GET', payload=None, csrf=None, expected=200, origin=base):
        headers = {'Origin': origin}
        if csrf:
            headers['X-CSRF-Token'] = csrf
        if payload is not None:
            headers['Content-Type'] = 'application/json'
        req = urllib.request.Request(base+path, method=method, headers=headers,
            data=json.dumps(payload).encode() if payload is not None else None)
        try:
            response = opener.open(req, timeout=12)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            raw = response.read()
            assert response.status == expected, (path, response.status, expected)
            value = json.loads(raw) if 'application/json' in response.headers.get('Content-Type','') else raw
            return value, response.headers

    provision = create_app({'REGISTRATION_OPEN': True})
    local = provision.test_client()
    try:
        cfg, headers = call(client(), '/api/config')
        assert cfg['registration_open'] is False
        assert headers['Cache-Control'] == 'no-store'
        assert headers.get('Strict-Transport-Security') and headers.get('Content-Security-Policy')
        call(client(), '/api/register', 'POST', {}, expected=503)
        call(client(), '/api/cases', expected=401)
        checks.append('verified_external_https_public_registration_closed_auth_required')
        for suffix in ('a','b'):
            username = 'synthetic_'+secrets.token_hex(6)+'_'+suffix
            password = secrets.token_urlsafe(24)
            payload = dict(username=username,password=password,privacy_accepted=True,
                privacy_version=c['PRIVACY_VERSION'],adult_confirmed=True,
                research_consent=False,followup_consent=False)
            response = local.post('/api/register',json=payload,base_url=base)
            assert response.status_code == 201
            actors.append((username,password))
        a,b = client(),client()
        account,h = call(a,'/api/login','POST',dict(zip(('username','password'),actors[0])))
        csrf=account['csrf_token']
        assert all(flag in h['Set-Cookie'] for flag in ('Secure','HttpOnly','SameSite=Strict'))
        call(b,'/api/login','POST',dict(zip(('username','password'),actors[1])))
        checks.append('two_synthetic_accounts_real_https_login_secure_cookies')
        call(a,'/api/tokens','POST',{'label':'synthetic'},expected=403)
        call(a,'/api/tokens','POST',{'label':'synthetic'},csrf=csrf,origin='https://evil.invalid',expected=403)
        checks.append('csrf_and_foreign_origin_rejected')
        example = json.loads(Path('/app/beta/examples/hours-known.json').read_text())
        profile = example.pop('profile')
        assert example['evidence_origin'] == 'synthetic'
        case,_ = call(a,'/api/cases','POST',dict(title='Synthetic production acceptance',profile=profile,input=example),csrf,201)
        cid = case['case']['id']
        queued,_ = call(a,f'/api/cases/{cid}/run','POST',{},csrf,202)
        jid=queued['job']['id']; deadline=time.monotonic()+45
        while True:
            current,_=call(a,f'/api/jobs/{jid}')
            job=current['job']
            if job['status'] not in ('queued','running'):
                break
            if time.monotonic()>deadline:
                raise RuntimeError('Real worker receipt timed out')
            time.sleep(.5)
        assert job['status']=='completed',job['status']
        archive,_=call(a,job['artifacts']['url'])
        artifact_sha=hashlib.sha256(archive).hexdigest()
        assert artifact_sha==job['artifacts']['sha256']
        for path in (f'/api/cases/{cid}',f'/api/jobs/{jid}',job['artifacts']['url']):
            call(b,path,expected=404)
        exported,_=call(a,'/api/export')
        assert exported['cases'][0]['case']['id']==cid
        call(a,f'/api/cases/{cid}/feedback','POST',{'job_id':jid,'rating':3,'comment':'SYNTHETIC acceptance; not user evidence'},csrf,201)
        checks.append('real_worker_engine_artifact_hash_isolation_export_feedback')
        db=sqlite3.connect(c['DATABASE'])
        assert db.execute('SELECT count(*) FROM research_candidates').fetchone()[0]==0
        assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        db.close()
        checks.append('sqlite_integrity_and_no_research_candidates')
        call(a,'/api/me','DELETE',csrf=csrf,expected=204)
        call(a,'/api/me',expected=401)
        call(b,f'/api/cases/{cid}',expected=404)
        checks.append('deletion_revokes_public_session_and_removes_case')
    finally:
        # Cleanup only the two fixture identities created by this invocation.
        # Credentials stay in memory and are never included in any receipt.
        for username,password in actors:
            response=local.post('/api/login',json=dict(username=username,password=password),base_url=base)
            if response.status_code==200:
                response=local.delete('/api/me',headers={'X-CSRF-Token':response.json['csrf_token']},base_url=base)
                cleanup.append(response.status_code==204)
            else:
                cleanup.append(response.status_code==401)
        assert all(cleanup), 'Synthetic account cleanup failed'
    db=sqlite3.connect(c['DATABASE'])
    counts={t:db.execute('SELECT count(*) FROM '+t).fetchone()[0]
        for t in ('users','cases','jobs','artifacts','research_candidates')}
    assert all(v==0 for v in counts.values()),'Unexpected remaining fixture data'
    ledger_count=db.execute('SELECT count(*) FROM deletion_ledger').fetchone()[0]
    db.close()
    result=dict(format='genius-production-synthetic-receipt/1',status='PASS',synthetic=True,
        origin=base,tls_verified=True,uid=os.geteuid(),checks=checks,cleanup=counts,
        deletion_ledger_count=ledger_count,artifact_sha256=artifact_sha,
        registration_open=False,restart_durability_tested=False,provider_restore_tested=False,
        real_user_evidence=False,operator_management_names_removed=removed_names)
    output=c['DATA_DIR']/'production-acceptance-20261005.json'
    with output.open('x') as file:
        json.dump(result,file,sort_keys=True);file.write('\n');file.flush();os.fsync(file.fileno())
    print('GENIUS_ACCEPTANCE '+json.dumps(result,sort_keys=True))


if __name__=='__main__':
    main()
