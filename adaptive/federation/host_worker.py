"""Fixed worker for a host lease. No remote code, provisioner or inherited secrets."""
import json
import os
from pathlib import Path
import resource
import sys
import time

from .core import decode,fields
from .hosting_protocol import CHILD,LIMITS,validate_offer,admitted
from .internet import InternetNode,RemoteError
from .network_protocol import sign


def execute(job,transport=None):
    fields(job,'state signed_offer request operation')
    p=validate_offer(job['signed_offer']);r=job['request']
    client=InternetNode(job['state'],**({'transport':transport} if transport else {}))
    if job['operation']=='retire':
        if not client.credentials_path.exists():return dict(retired=True)
        try:cfg=client.load()
        except ValueError as exc:
            if str(exc)=='NODE_LEFT_NETWORK':return dict(retired=True)
            raise
        if 'credential' not in cfg:return dict(retired=True,remote_account_created=False)
        client.leave();return dict(retired=True)
    if job['operation']!='cycle' or r['expires_at']<=int(time.time()):raise ValueError('LEASE_EXPIRED')
    if not admitted(p,r['world_id'],r['focus']):raise ValueError('SCOPE_NOT_AUTHORIZED')
    client.init(p['hub'],'Genius Semilla '+r['id'][:12],[r['world_id']],True)
    cfg=client.load()
    claim=dict(format=CHILD,request_id=r['id'],host_id=p['node_id'],child_id=cfg['node_id'],offer_sha256=r['offer_hash'])
    receipt=client.cycle(r['world_id'],r['focus'])
    return dict(child_proof=dict(claim=claim,signature=sign(claim,cfg['keys']['private_key'])),
        status=receipt['current']['status'],model_sha256=receipt['current']['model_sha256'],
        native_verified=(receipt.get('calculation') or {}).get('verification',{}).get('valid',False))


def main():
    os.umask(0o077)
    resource.setrlimit(resource.RLIMIT_AS,(LIMITS['memory_mb']*1024**2,)*2)
    resource.setrlimit(resource.RLIMIT_CPU,(LIMITS['cpu_seconds'],)*2)
    resource.setrlimit(resource.RLIMIT_FSIZE,(LIMITS['file_bytes'],)*2)
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    try:
        job=decode(sys.stdin.buffer.read(262145))
        print(json.dumps(dict(ok=True,result=execute(job))))
    except Exception as exc:
        print(json.dumps(dict(ok=False,error=str(exc) if isinstance(exc,RemoteError) else type(exc).__name__)))
        raise SystemExit(1)


if __name__=='__main__':main()
