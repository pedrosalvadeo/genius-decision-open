"""Operator-authorized, finite hosting of fixed local reader processes."""
import argparse
from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path
import re
import signal
import shutil
import subprocess
import sys
from threading import Event
import time

from .core import canonical,decode,digest,instant
from .hosting_protocol import FORMAT,WORKER,LIMITS,validate_offer,admitted
from .internet import InternetNode,RemoteError,save
from .network_protocol import sign


def make_offer(node,worlds,max_births,lease_seconds,valid_until):
    cfg=node.load()
    offer=dict(format=FORMAT,node_id=cfg['node_id'],public_key=cfg['keys']['public_key'],hub=cfg['hub'],
               worker=WORKER,worlds=worlds,max_births=max_births,lease_seconds=lease_seconds,
               valid_until=valid_until,limits=LIMITS,automatic_acceptance=True)
    signed=dict(offer=offer,signature=sign(offer,cfg['keys']['private_key']))
    validate_offer(signed)
    return signed


def run_worker(job):
    # No shell, downloaded executable, management credentials or parent environment.
    env={k:os.environ[k] for k in ('PATH','PYTHONPATH') if k in os.environ}
    env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONUNBUFFERED='1')
    timeout=LIMITS['wall_seconds']
    if job['operation']=='cycle':timeout=min(timeout,max(1,job['request']['expires_at']-int(time.time())))
    proc=subprocess.Popen([sys.executable,'-m','federation.host_worker'],stdin=subprocess.PIPE,
                          stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,env=env,start_new_session=True)
    try:
        out,_=proc.communicate(canonical(job),timeout=timeout)
        result=decode(out)
        if proc.returncode or result.get('ok') is not True:raise ValueError('WORKER_FAILED')
        return result['result']
    finally:
        # Also reap any descendant left by a timed-out native calculation.
        try:os.killpg(proc.pid,signal.SIGKILL)
        except ProcessLookupError:pass
        proc.wait()


class Host:
    def __init__(self,state,node,worker=run_worker):
        self.state=Path(state).resolve();self.state.mkdir(parents=True,exist_ok=True,mode=0o700)
        self.node=node;self.worker=worker
        self.path=self.state/'host.json'

    @contextmanager
    def lock(self):
        fd=os.open(self.state/'controller.lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
        try:
            fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
            yield
        finally:os.close(fd)

    def load(self):
        state=decode(self.path.read_bytes());p=validate_offer(state['signed_offer']);cfg=self.node.load()
        if p['node_id']!=cfg['node_id'] or p['hub']!=cfg['hub']:raise ValueError('HOST_IDENTITY_MISMATCH')
        return state,p

    def call(self,method,path,body=None):
        cfg=self.node.load()
        if method!='DELETE':self.node.renew(cfg)
        return self.node.call(cfg,method,path,body,True)

    def authorize(self,signed_offer,confirmed=False):
        if confirmed is not True:raise ValueError('LOCAL_HOST_AUTHORIZATION_REQUIRED')
        validate_offer(signed_offer)
        with self.lock():
            if self.path.exists():
                state,p=self.load()
                if state['signed_offer']!=signed_offer or state['revoked']:raise ValueError('HOST_POLICY_LOCKED')
            else:
                state=dict(signed_offer=signed_offer,published=False,revoked=False,revocation_published=False,records={})
                save(self.path,state);self.load()
            if not state['published']:
                result=self.call('POST','/api/network/hosts',dict(signed_offer=signed_offer,operator_authorized=True))
                if result['offer_sha256']!=digest(signed_offer):raise ValueError('HOST_OFFER_HASH_MISMATCH')
                state['published']=True;save(self.path,state)
        return dict(offer_sha256=digest(signed_offer),max_births=signed_offer['offer']['max_births'])

    def request(self,host_id,offer_hash,world,focus,confirmed=False):
        if confirmed is not True:raise ValueError('PUBLIC_REQUEST_CONFIRMATION_REQUIRED')
        return self.call('POST','/api/network/host/request',dict(host_id=host_id,offer_sha256=offer_hash,
            world_id=world,focus=focus,public_request_confirmed=True))

    def discover(self,world,focus,confirmed=False):
        if confirmed is not True:raise ValueError('PUBLIC_REQUEST_CONFIRMATION_REQUIRED')
        cfg=self.node.load();result=self.node.call(cfg,'GET','/network/hosts')
        if result.get('format')!='genius-host-directory/1' or type(result.get('hosts')) is not list or len(result['hosts'])>20:
            raise ValueError('INVALID_HOST_DIRECTORY')
        for row in sorted(result['hosts'],key=lambda r:r['node_id']):
            p=validate_offer(row['signed_offer'])
            if row['node_id']!=p['node_id'] or digest(row['signed_offer'])!=row['offer_sha256'] or p['hub']!=cfg['hub']:
                raise ValueError('HOST_OFFER_MISMATCH')
            if row['disabled'] or not row['recently_seen'] or instant(p['valid_until']).timestamp()<=time.time():continue
            if row['births_accepted']>=p['max_births'] or not admitted(p,world,focus):continue
            return self.request(p['node_id'],row['offer_sha256'],world,focus,True)
        return dict(status='NO_AUTHORIZED_CAPACITY')

    def job(self,state,record,operation):
        return dict(state=str(self.state/'children'/record['request']['id']),signed_offer=state['signed_offer'],
                    request=record['request'],operation=operation)

    def retire(self,state,record):
        # Mark locally first; no future cycle can run even if remote deletion fails.
        record['status']='RETIRING';save(self.path,state)
        try:
            result=self.worker(self.job(state,record,'retire'))
            if result.get('retired') is not True:raise ValueError('RETIREMENT_NOT_CONFIRMED')
            record['status']='STOPPED';save(self.path,state)
            try:self.call('POST','/api/network/host/result',dict(request_id=record['request']['id'],status='STOPPED',child_proof=None))
            except (OSError,ValueError):pass
        except (OSError,ValueError,subprocess.TimeoutExpired):
            record['status']='RETIRING';save(self.path,state)

    def step(self):
        with self.lock():
            state,p=self.load();stamp=int(time.time());remote=None;remote_revoked=False
            if state['revoked'] and not state['revocation_published']:
                try:
                    self.call('DELETE','/api/network/host',dict(confirmed=True))
                    state['revocation_published']=True;save(self.path,state)
                except (OSError,ValueError):pass
            if not state['revoked'] and instant(p['valid_until']).timestamp()>stamp:
                try:remote=self.call('GET','/api/network/host')
                except (OSError,ValueError) as exc:
                    remote_revoked=isinstance(exc,RemoteError) and str(exc) in ('REMOTE_HTTP_401','REMOTE_HTTP_403','REMOTE_HTTP_404')
            accepted=(remote is not None and not remote['disabled'] and remote['offer_sha256']==digest(state['signed_offer']) and remote['expires_at']>stamp and not state['revoked'])
            work_allowed=bool(accepted)
            if accepted:
                try:self.call('POST','/api/network/heartbeat',{})
                except (OSError,ValueError):work_allowed=False
            queue=remote['requests'] if accepted else []
            if type(queue) is not list or len(queue)>32:raise ValueError('INVALID_HOST_QUEUE')
            by_id={r['id']:r for r in queue}
            # Lost contact pauses; explicit revocation or expiry retires. No work offline.
            for id_,record in state['records'].items():
                r=by_id.get(id_)
                if record['status']=='STOPPED':continue
                if (record['status']=='RETIRING' or state['revoked'] or remote_revoked or
                    record['request']['expires_at']<=stamp or instant(p['valid_until']).timestamp()<=stamp or
                    (remote is not None and (not accepted or not r or r['status'] not in ('PENDING','ACTIVE') or r['expires_at']<=stamp))):
                    self.retire(state,record)
            for r in queue if work_allowed else []:
                id_=r['id']
                if (not isinstance(id_,str) or not re.fullmatch('[0-9a-f]{64}',id_) or
                    r['offer_hash']!=digest(state['signed_offer']) or r['host_id']!=p['node_id'] or
                    type(r['expires_at']) is not int or r['expires_at']>instant(p['valid_until']).timestamp() or
                    type(r['created_at']) is not int or r['created_at']>stamp or r['expires_at']-r['created_at']>p['lease_seconds'] or
                    not admitted(p,r['world_id'],r['focus'])):raise ValueError('UNAUTHORIZED_HOST_JOB')
                if r['status'] not in ('PENDING','ACTIVE') or r['expires_at']<=stamp:continue
                record=state['records'].get(id_)
                if record is None:
                    if len(state['records'])>=p['max_births']:
                        self.call('POST','/api/network/host/result',dict(request_id=id_,status='REJECTED',child_proof=None));continue
                    if shutil.disk_usage(self.state).free<64*1024**2:raise ValueError('HOST_DISK_RESERVE')
                    record=dict(request=r,status='RESERVED',next_at=0,attempts=0)
                    state['records'][id_]=record;save(self.path,state)
                elif any(record['request'][k]!=r[k] for k in ('id','host_id','offer_hash','world_id','focus','created_at','expires_at','requester_id')):
                    self.retire(state,record);raise ValueError('LEASE_CHANGED')
                if record['status'] in ('STOPPED','RETIRING') or record['next_at']>stamp:continue
                if record['status']=='RESERVED' and record['attempts']>=3:
                    self.retire(state,record);continue
                if record['status']=='RESERVED':record['attempts']+=1
                record['next_at']=stamp+LIMITS['interval_seconds'];save(self.path,state)
                try:
                    result=self.worker(self.job(state,record,'cycle'))
                    if record['status']!='ACTIVE':
                        self.call('POST','/api/network/host/result',dict(request_id=id_,status='ACTIVE',child_proof=result['child_proof']))
                    elif record['child_id']!=result['child_proof']['claim']['child_id']:
                        raise ValueError('CHILD_IDENTITY_CHANGED')
                    record.update(status='ACTIVE',child_id=result['child_proof']['claim']['child_id'],last_result={k:result[k] for k in ('status','model_sha256','native_verified')})
                    save(self.path,state)
                except (OSError,ValueError,subprocess.TimeoutExpired):
                    record['last_error']='PAUSED_OR_REVIEW_REQUIRED';save(self.path,state)
            return dict(format='genius-host-cycle/1',host_id=p['node_id'],authorized=work_allowed,births_reserved=len(state['records']),
                        revocation_pending=state['revoked'] and not state['revocation_published'],
                        children=[dict(request_id=k,status=v['status'],child_id=v.get('child_id'),last_result=v.get('last_result')) for k,v in state['records'].items()])

    def revoke(self):
        with self.lock():
            state,p=self.load();state['revoked']=True;save(self.path,state)
        return self.step()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--node-state',type=Path,required=True)
    parser.add_argument('--state',type=Path,required=True)
    commands=parser.add_subparsers(dest='command',required=True)
    authorize=commands.add_parser('authorize');authorize.add_argument('policy',type=Path)
    authorize.add_argument('--allow-hosting',action='store_true')
    ask=commands.add_parser('request');ask.add_argument('--host');ask.add_argument('--offer')
    ask.add_argument('--world',required=True);ask.add_argument('--focus',action='append',required=True)
    ask.add_argument('--confirm-public-request',action='store_true')
    run=commands.add_parser('run');run.add_argument('--continuous',action='store_true')
    commands.add_parser('revoke')
    args=parser.parse_args();host=Host(args.state,InternetNode(args.node_state));stopped=Event()
    for sig in (signal.SIGTERM,signal.SIGINT):signal.signal(sig,lambda *_:stopped.set())
    try:
        if args.command=='authorize':
            p=decode(args.policy.read_bytes())
            result=host.authorize(make_offer(host.node,**p),args.allow_hosting)
        elif args.command=='request':
            if bool(args.host)!=bool(args.offer):parser.error('--host y --offer deben indicarse juntos')
            result=(host.request(args.host,args.offer,args.world,sorted(args.focus),args.confirm_public_request) if args.host
                    else host.discover(args.world,sorted(args.focus),args.confirm_public_request))
        elif args.command=='revoke':result=host.revoke()
        else:
            while not stopped.is_set():
                print(json.dumps(host.step()),flush=True)
                if not args.continuous:return
                stopped.wait(LIMITS['interval_seconds'])
            # SIGTERM stops local execution; leases are retained for an explicit restart.
            return
        print(json.dumps(result),flush=True)
    except (OSError,ValueError,KeyError,TypeError):parser.exit(1,'Alojamiento pausado: revisá autorización, conectividad, credenciales y cuotas.\n')


if __name__=='__main__':main()
