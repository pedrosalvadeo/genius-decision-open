"""Installable outbound-only node. Explicit enrollment and publication, local compute."""
import argparse
from http.client import HTTPSConnection
import json
import os
from pathlib import Path
import time
from urllib.parse import urlsplit, urlencode

from .core import Node, canonical, decode, digest, identifier, text, MAX_BYTES
from .network_protocol import POLICY, ENROLL, generate, identity, sign, envelope, verify_view


class RemoteError(ValueError):
    pass


def origin(value):
    url=urlsplit(value)
    if (url.scheme!='https' or not url.hostname or url.username or url.password or
        url.path not in ('','/') or url.query or url.fragment or url.port not in (None,443)):
        raise ValueError('HTTPS_ORIGIN_REQUIRED')
    return 'https://'+url.netloc.lower()


def request(hub,method,path,body=None,token=None):
    url=urlsplit(origin(hub))
    if not path.startswith('/') or path.startswith('//') or '\r' in path or '\n' in path:
        raise ValueError('INVALID_PATH')
    headers={'Content-Type':'application/json','User-Agent':'Genius-Node/1'}
    if token:headers['Authorization']='Bearer '+token
    conn=HTTPSConnection(url.hostname,443,timeout=15)
    try:
        conn.request(method,path,body=canonical(body) if body is not None else None,headers=headers)
        reply=conn.getresponse();raw=reply.read(MAX_BYTES+1)
        if reply.status not in (200,201,204):
            # No redirects, URLs, response bodies or credentials in errors/logs.
            raise RemoteError('REMOTE_HTTP_'+str(reply.status))
        return decode(raw) if raw else {}
    finally:conn.close()


def save(path,value):
    path=Path(path)
    temporary=path.with_name(path.name+'.pending')
    fd=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_TRUNC|os.O_NOFOLLOW,0o600)
    try:
        os.fchmod(fd,0o600)
        with os.fdopen(fd,'wb') as stream:
            stream.write(canonical(value));stream.flush();os.fsync(stream.fileno())
        os.replace(temporary,path)
    finally:
        if temporary.exists():temporary.unlink()


class InternetNode:
    def __init__(self,state,transport=request):
        self.state=Path(state).resolve()
        self.state.mkdir(parents=True,exist_ok=True,mode=0o700)
        self.transport=transport
        self.credentials_path=self.state/'credentials.json'

    def load(self):
        value=decode(self.credentials_path.read_bytes())
        if value.get('erased'):raise ValueError('NODE_LEFT_NETWORK')
        return value

    def call(self,config,method,path,body=None,authenticated=False):
        token=config.get('credential',{}).get('token') if authenticated else None
        return self.transport(config['hub'],method,path,body,token)

    def init(self,hub,label,topics,confirmed=False):
        if confirmed is not True:raise ValueError('PUBLIC_PROFILE_CONFIRMATION_REQUIRED')
        hub=origin(hub)
        text(label,80)
        if any(ord(c)<32 for c in label) or type(topics) is not list or not 1<=len(topics)<=8 or len(set(topics))!=len(topics):
            raise ValueError('INVALID_PROFILE')
        for topic in topics:identifier(topic)
        if self.credentials_path.exists():
            cfg=self.load()
            if cfg['hub']!=hub:raise ValueError('STATE_ALREADY_BOUND_TO_HUB')
        else:
            keys=generate()
            cfg=dict(hub=hub,keys=keys,node_id=identity(keys['public_key']),label=label,topics=topics)
            save(self.credentials_path,cfg)
        if 'credential' not in cfg:
            manifest=self.call(cfg,'GET','/agents/manifest.json')
            response=self.call(cfg,'POST','/api/agents/register',dict(policy_version=manifest['policy_version'],
                data_policy_acknowledged=True,scopes=['network:read','network:write','account:delete']))
            cfg.update(account_id=response['agent']['id'],credential=response['credential'])
            save(self.credentials_path,cfg)
        doc=dict(format=ENROLL,policy_version=POLICY,account_id=cfg['account_id'],hub=hub,
                 node_id=cfg['node_id'],public_key=cfg['keys']['public_key'],label=cfg['label'],topics=cfg['topics'])
        result=self.call(cfg,'POST','/api/network/join',dict(enrollment=doc,
            signature=sign(doc,cfg['keys']['private_key']),public_sharing_confirmed=True,operator_authorized=True),True)
        Node(self.state/'memory',cfg['node_id'])
        return dict(node=result['node'],hub=hub,credentials_printed=False)

    def renew(self,cfg):
        if cfg['credential']['expires_at']<=int(time.time())+86400:
            response=self.call(cfg,'POST','/api/agents/token',{},True)
            cfg['credential']=response['credential'];save(self.credentials_path,cfg)

    def publish(self,view,confirmed=False):
        if confirmed is not True:raise ValueError('PUBLICATION_CONFIRMATION_REQUIRED')
        cfg=self.load();self.renew(cfg)
        signed=envelope(view,cfg['keys'])
        # Keep local evidence even if the remote write is unavailable.
        Node(self.state/'memory',cfg['node_id']).ingest_views([view])
        result=self.call(cfg,'POST','/api/network/views',dict(envelope=signed,
                         publication_confirmed=True,operator_authorized=True),True)
        if result['sha256']!=digest(signed):raise ValueError('PUBLICATION_HASH_MISMATCH')
        return result

    def cycle(self,world_id,focus):
        identifier(world_id)
        cfg=self.load();self.renew(cfg)
        node=Node(self.state/'memory',cfg['node_id'])
        node.project_world(world_id,focus,'connected')  # Validate scope before any reads.
        self.call(cfg,'POST','/api/network/heartbeat',{},True)
        with node.db() as db:
            db.execute('CREATE TABLE IF NOT EXISTS signed_views (hash TEXT PRIMARY KEY, envelope_json TEXT NOT NULL)')
            known={r[0] for r in db.execute('SELECT hash FROM signed_views')}
        imported=0;after='';reads=0
        for _ in range(8):
            page=self.call(cfg,'GET','/network/views?'+urlencode(dict(world_id=world_id,after=after)));reads+=1
            if page.get('format')!='genius-network-index/1' or page.get('world_id')!=world_id or type(page.get('views')) is not list or len(page['views'])>20:
                raise ValueError('INVALID_NETWORK_INDEX')
            for entry in page['views']:
                hash_=entry['hash']
                if not isinstance(hash_,str) or len(hash_)!=64 or any(c not in '0123456789abcdef' for c in hash_):
                    raise ValueError('INVALID_VIEW_HASH')
                if hash_ in known:continue
                if len(known)>=8:raise ValueError('LOCAL_VIEW_REVIEW_REQUIRED')
                packet=self.call(cfg,'GET','/network/views/'+hash_);reads+=1
                signed=packet['envelope'];view=verify_view(signed)
                if digest(signed)!=hash_ or packet['sha256']!=hash_ or view['world_id']!=world_id:
                    raise ValueError('SIGNED_VIEW_MISMATCH')
                result=node.ingest_views([view],via=None if signed['node_id']==cfg['node_id'] else signed['node_id'])
                with node.db() as db:
                    db.execute('INSERT OR IGNORE INTO signed_views VALUES (?,?)',(hash_,canonical(signed).decode()))
                known.add(hash_);imported+=result['inserted']
            next_after=page['next_after']
            if next_after is None:break
            if not isinstance(next_after,str) or next_after<=after or next_after!=page['views'][-1]['hash']:
                raise ValueError('INVALID_PAGE_CURSOR')
            after=next_after
        else:raise ValueError('NETWORK_SCAN_BUDGET')
        projection=node.project_world(world_id,focus,'connected')
        from .initiative import summarize
        receipt=dict(format='genius-internet-cycle/1',node_id=cfg['node_id'],hub=cfg['hub'],
                     world_id=world_id,imported=imported,public_reads=reads,current=summarize(projection),
                     verified_envelopes=len(known),physical_actions=False,empirical_validation='NOT_ASSESSED')
        if projection['model'] is not None:
            from genius_twin import registry,stockflow
            result=registry.evaluate(projection['model'])
            if not result['verification']['valid']:raise ValueError('NATIVE_VERIFICATION_FAILED')
            receipt['calculation']=dict(model_sha256=digest(projection['model']),verification=result['verification'],
                decision=result['canonical_results']['decision'],trajectories=stockflow.compute_trajectories(projection['model']))
        save(self.state/'latest-cycle.json',receipt)
        return receipt

    def leave(self):
        cfg=self.load()
        self.call(cfg,'DELETE','/api/agents/me',authenticated=True)
        save(self.credentials_path,dict(erased=True,node_id=cfg['node_id']))
        return dict(left=True,local_memory_retained=True,remote_copies_may_remain=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state',type=Path,default=Path('genius-node-state'))
    commands=parser.add_subparsers(dest='command',required=True)
    init=commands.add_parser('init');init.add_argument('--hub',default='https://geniusdecision.app')
    init.add_argument('--label',required=True);init.add_argument('--topic',action='append',required=True)
    init.add_argument('--accept-public-profile',action='store_true')
    publish=commands.add_parser('publish');publish.add_argument('file',type=Path)
    publish.add_argument('--confirm-publication',action='store_true')
    run=commands.add_parser('run');run.add_argument('--world',required=True);run.add_argument('--focus',action='append',required=True)
    run.add_argument('--cycles',type=int,default=1);run.add_argument('--interval',type=int,default=600)
    run.add_argument('--continuous',action='store_true')
    commands.add_parser('leave')
    args=parser.parse_args();client=InternetNode(args.state)
    try:
        if args.command=='init':result=client.init(args.hub,args.label,args.topic,args.accept_public_profile)
        elif args.command=='publish':result=client.publish(decode(args.file.read_bytes()),args.confirm_publication)
        elif args.command=='leave':result=client.leave()
        else:
            if not 1<=args.cycles<=144 or not 300<=args.interval<=86400:parser.error('cycles 1..144; interval 300..86400 seconds')
            done=0
            while args.continuous or done<args.cycles:
                try:
                    result=client.cycle(args.world,args.focus)
                    print(json.dumps({k:v for k,v in result.items() if k!='calculation'}),flush=True)
                except (OSError,ValueError):
                    if not args.continuous:raise
                    print(json.dumps(dict(status='PAUSED_OR_REVIEW_REQUIRED')),flush=True)
                done+=1
                if args.continuous or done<args.cycles:time.sleep(args.interval)
            return
        print(json.dumps(result,ensure_ascii=False))
    except (OSError,ValueError,KeyError):
        parser.exit(1,'La operación no se completó. Revisá conectividad, política, credencial, cuotas y datos; no se imprimen secretos.\n')


if __name__=='__main__':main()
