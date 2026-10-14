"""Synthetic service probe. Seed before restart, verify and erase after restart.

The state file contains a short-lived credential: mode 0600, never commit it.
Only the separate receipt is public evidence. Never use a real user's account.
"""
import argparse
import base64
import hashlib
import http.client
import io
import json
import os
from pathlib import Path
import secrets
import tarfile
import time
from urllib.parse import urlsplit
import zipfile


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase',choices=('seed','verify'))
    parser.add_argument('--origin',required=True)
    parser.add_argument('--state',type=Path,required=True)
    parser.add_argument('--receipt',type=Path,required=True)
    args=parser.parse_args()
    origin=urlsplit(args.origin)
    if origin.scheme!='https' or not origin.hostname or origin.username or origin.path or origin.query or origin.fragment:
        raise SystemExit('An HTTPS origin without path is required')
    def request(method,path,payload=None,token=None):
        headers={'Accept':'application/json'}
        if token:headers['Authorization']='Bearer '+token
        data=None if payload is None else json.dumps(payload).encode()
        if data is not None:headers['Content-Type']='application/json'
        connection=http.client.HTTPSConnection(origin.hostname,origin.port or 443,timeout=20)
        try:
            connection.request(method,path,body=data,headers=headers)
            response=connection.getresponse();raw=response.read(4*1024*1024)
            value=json.loads(raw) if raw else None
            if response.status>=300:
                code=value.get('error',{}).get('code') if isinstance(value,dict) else 'non_json'
                raise RuntimeError(str(response.status)+':'+str(code))
            return value
        finally:connection.close()
    if args.phase=='seed':
        if args.state.exists():raise SystemExit('State file already exists; verify or erase its probe first')
        manifest=request('GET','/agents/manifest.json')
        issued=request('POST','/api/agents/register',dict(policy_version=manifest['policy_version'],data_policy_acknowledged=True,
            scopes=['missions:read','missions:write','missions:run','missions:delete','account:delete']))
        token=issued['credential']['token']
        state=dict(origin=args.origin,token=token)
        os.umask(0o077)
        args.state.write_text(json.dumps(state));args.state.chmod(0o600)
        files={'probe.txt':'Synthetic persistent Genius mission.\n'*400,'nested/utf8.txt':'Prueba técnica: ñ, á, 🌱.\n'*80}
        mid=request('POST','/api/missions',dict(idempotency_key='probe-'+secrets.token_hex(16),files=files,processing_permission=True,technical_scope_acknowledged=True),token)['mission']['id']
        state['mission_id']=mid;args.state.write_text(json.dumps(state))
        request('POST','/api/missions/'+mid+'/run',{},token)
        deadline=time.monotonic()+75
        while True:
            mission=request('GET','/api/missions/'+mid,token=token)['mission']
            if mission['status']=='completed':break
            if mission['status'] in ('failed','needs_review','cancelled','interrupted') or time.monotonic()>deadline:
                raise RuntimeError('Probe mission did not complete: '+mission['status'])
            time.sleep(1)
        exported=request('GET','/api/missions/'+mid+'/export',token=token)['mission']
        artifact=request('GET','/api/missions/'+mid+'/artifact',token=token)
        raw=base64.b64decode(artifact['content_base64'],validate=True)
        if hashlib.sha256(raw).hexdigest()!=artifact['sha256']:raise RuntimeError('Artifact digest mismatch')
        if artifact['name']=='source.zip':
            with zipfile.ZipFile(io.BytesIO(raw)) as z:actual={name:z.read(name).decode() for name in z.namelist()}
        else:
            with tarfile.open(fileobj=io.BytesIO(raw),mode='r:*') as z:actual={entry.name:z.extractfile(entry).read().decode() for entry in z}
        if actual!=files:raise RuntimeError('Artifact contents mismatch')
        state.update(mission_digest=digest(mission),export_digest=digest(exported),artifact_sha256=artifact['sha256'])
        args.state.write_text(json.dumps(state))
        receipt=dict(phase='seed',status='PASS',origin=args.origin,mission_id=mid,artifact_sha256=artifact['sha256'],
            last_stage=mission['last_stage'],selected=mission['result']['memory']['selected'],observation=mission['result']['memory']['observation'],
            attempts=mission['attempts'],export_digest=state['export_digest'],completed_at=int(time.time()),restart_verified=False)
    else:
        state=json.loads(args.state.read_text())
        if state['origin']!=args.origin:raise SystemExit('Origin mismatch')
        token,mid=state['token'],state['mission_id']
        mission=request('GET','/api/missions/'+mid,token=token)['mission']
        exported=request('GET','/api/missions/'+mid+'/export',token=token)['mission']
        artifact=request('GET','/api/missions/'+mid+'/artifact',token=token)
        if digest(mission)!=state['mission_digest'] or digest(exported)!=state['export_digest'] or artifact['sha256']!=state['artifact_sha256']:
            raise RuntimeError('Durable mission changed')
        if request('POST','/api/missions/'+mid+'/run',{},token)['mission']!=mission:raise RuntimeError('Completed mission reran')
        request('DELETE','/api/agents/me',{},token)
        try:request('GET','/api/missions/'+mid,token=token)
        except RuntimeError as exc:
            if not str(exc).startswith('401:'):raise
        else:raise RuntimeError('Deleted credential still valid')
        receipt=dict(phase='verify',status='PASS',origin=args.origin,mission_id=mid,completed_mission_unchanged=True,
            export_unchanged=True,artifact_sha256=artifact['sha256'],explicit_run_reused=True,probe_account_erased=True,
            credential_revoked=True,verified_at=int(time.time()),restart_attestation='operator must pair with provider restart receipt')
        args.state.unlink()
    args.receipt.write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt))

if __name__=='__main__':main()
