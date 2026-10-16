"""Voluntary Internet enrollment, cryptographic identity and local calculation."""
from copy import deepcopy
from datetime import datetime,timedelta,timezone
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from federation.core import digest
from federation.internet import InternetNode, RemoteError, origin
from federation.network_protocol import envelope, verify_view, sign
from federation.world_example import example
from genius_beta.app import create_app
from genius_beta.db import connect,purge


class PublicNetworkTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        root=Path(self.temp.name);self.root=root
        self.env=patch.dict(os.environ,{'GENIUS_R2_BACKUP_ENABLED':'false'})
        self.env.start();self.addCleanup(self.env.stop)
        self.config=dict(DATA_DIR=root/'server',DATABASE=root/'server/db.sqlite3',SUSPEND_FILE=root/'server/SUSPENDED',
            PUBLIC_URL='https://hub.example',TESTING=True,REGISTRATION_OPEN=True,MAX_AGENT_REGISTRATIONS_DAILY=20)
        self.app=create_app(self.config);self.client=self.app.test_client(use_cookies=False);self.serial=0
        start=datetime.now(timezone.utc)
        self.views=example((start-timedelta(minutes=1)).isoformat(),(start+timedelta(hours=1)).isoformat())

    def transport(self,hub,method,path,body=None,token=None):
        self.assertEqual(hub,'https://hub.example')
        r=self.client.open(path,method=method,json=body,headers={'Authorization':'Bearer '+token} if token else {},
                           environ_overrides={'REMOTE_ADDR':'127.0.0.'+str(self.serial)})
        if r.status_code not in (200,201,204):raise RemoteError('REMOTE_HTTP_'+str(r.status_code))
        return r.json if r.data else {}

    def node(self,name):
        self.serial+=1
        node=InternetNode(self.root/name,self.transport)
        node.init('https://hub.example',name,['pumping-study'],True)
        return node

    def owned(self,node,index):
        v=deepcopy(self.views[index]);v['owner']=node.load()['node_id'];v['view_id']='part'+str(index)
        return v

    def post(self,node,path,value):
        return self.client.post(path,json=value,headers={'Authorization':'Bearer '+node.load()['credential']['token']})

    def test_three_installations_publish_exchange_verify_and_compute(self):
        nodes=[self.node(name) for name in ('a','b','c')]
        for i,node in enumerate(nodes):node.publish(self.owned(node,i),True)
        receipts=[node.cycle('pumping-study',['pump']) for node in nodes]
        hashes={r['calculation']['model_sha256'] for r in receipts}
        self.assertEqual(len(hashes),1)
        for r in receipts:
            self.assertTrue(r['calculation']['verification']['valid'])
            self.assertEqual(r['calculation']['trajectories']['restore_supply']['available']['daily'][-1]['stocks']['delivered'],'5/1')
            self.assertEqual(r['verified_envelopes'],3)
            self.assertIsNone(r['calculation']['decision']['selected'])
        again=nodes[0].cycle('pumping-study',['pump'])
        self.assertEqual(again['imported'],0);self.assertEqual(again['public_reads'],1)
        self.assertEqual(self.client.get('/network/manifest.json').json['nodes'],3)

    def test_signatures_detect_tampering_owner_and_private_publication(self):
        node=self.node('a');view=self.owned(node,0);cfg=node.load()
        signed=envelope(view,cfg['keys'])
        changed=deepcopy(signed);changed['view']['world_id']='changed'
        with self.assertRaisesRegex(ValueError,'SIGNATURE_INVALID'):verify_view(changed)
        response=self.post(node,'/api/network/views',dict(envelope=changed,publication_confirmed=True,operator_authorized=True))
        self.assertEqual(response.status_code,400)
        view['shareable']=False
        with self.assertRaises(ValueError):node.publish(view,True)
        self.assertEqual(self.client.get('/network/manifest.json').json['public_views'],0)

    def test_foreign_account_cannot_publish_valid_signature_or_replay_enrollment(self):
        a=self.node('a');b=self.node('b');cfg=a.load()
        signed=envelope(self.owned(a,0),cfg['keys'])
        r=self.post(b,'/api/network/views',dict(envelope=signed,publication_confirmed=True,operator_authorized=True))
        self.assertEqual(r.status_code,400)
        from federation.network_protocol import ENROLL,POLICY
        doc=dict(format=ENROLL,policy_version=POLICY,account_id=cfg['account_id'],hub=cfg['hub'],node_id=cfg['node_id'],
                 public_key=cfg['keys']['public_key'],label='a',topics=['pumping-study'])
        r=self.post(b,'/api/network/join',dict(enrollment=doc,signature=sign(doc,cfg['keys']['private_key']),
                                           public_sharing_confirmed=True,operator_authorized=True))
        self.assertEqual(r.status_code,400)

    def test_explicit_consent_auth_scopes_and_no_secret_disclosure(self):
        node=InternetNode(self.root/'a',self.transport)
        with self.assertRaisesRegex(ValueError,'CONFIRMATION'):node.init('https://hub.example','a',['pumping-study'])
        node=self.node('a');view=self.owned(node,0)
        with self.assertRaisesRegex(ValueError,'CONFIRMATION'):node.publish(view)
        self.assertEqual(self.client.post('/api/network/heartbeat',json={}).status_code,401)
        manifest=self.client.get('/agents/manifest.json').json
        narrow=self.client.post('/api/agents/register',json=dict(policy_version=manifest['policy_version'],
            data_policy_acknowledged=True,scopes=['network:read']),environ_overrides={'REMOTE_ADDR':'127.0.0.99'}).json
        response=self.client.post('/api/network/heartbeat',json={},headers={'Authorization':'Bearer '+narrow['credential']['token']})
        self.assertEqual(response.status_code,403)
        public=json.dumps(self.client.get('/network/nodes').json)
        cfg=node.load()
        for value in (cfg['account_id'],cfg['credential']['token'],cfg['keys']['private_key']):self.assertNotIn(value,public)
        self.assertEqual(os.stat(node.credentials_path).st_mode & 0o777,0o600)

    def test_conflict_preserved_not_majority_and_packet_hash_checked(self):
        a=self.node('a');b=self.node('b')
        a.publish(self.owned(a,0),True)
        for i in (1,2):b.publish(self.owned(b,i),True)
        first=a.cycle('pumping-study',['pump']);self.assertIsNotNone(first['current']['model_sha256'])
        v=self.owned(b,1);v['view_id']='incompatible'
        v['construction']['fragments'][0]['value']['initial']='0/1'
        b.publish(v,True)
        conflict=a.cycle('pumping-study',['pump'])
        self.assertIsNone(conflict['current']['model_sha256']);self.assertNotIn('calculation',conflict)
        self.assertIn('FRAGMENT_CONFLICT',[q['code'] for q in conflict['current']['questions']])

    def test_duplicate_quota_invalid_cursor_and_expiry(self):
        node=self.node('a');v=self.owned(node,0)
        first=node.publish(v,True);again=node.publish(v,True)
        self.assertEqual(first['sha256'],again['sha256']);self.assertTrue(again['duplicate'])
        for i in range(1,8):
            copy=deepcopy(v);copy['view_id']='extra'+str(i);node.publish(copy,True)
        cfg=node.load();copy=deepcopy(v);copy['view_id']='ninth'
        r=self.post(node,'/api/network/views',dict(envelope=envelope(copy,cfg['keys']),publication_confirmed=True,operator_authorized=True))
        self.assertEqual(r.status_code,429)
        self.assertEqual(self.client.get('/network/views?world_id=pumping-study&after=invalid').status_code,400)
        self.assertEqual(self.client.get('/network/views').status_code,400)
        expired=deepcopy(v);expired['valid_until']=expired['frame']['reference_time']
        with self.assertRaises(ValueError):envelope(expired,cfg['keys'])

    def test_leave_and_retention_remove_public_data_and_revoke_token(self):
        node=self.node('a');r=node.publish(self.owned(node,0),True);cfg=node.load()
        self.assertTrue(node.leave()['left'])
        self.assertEqual(self.client.get('/network/views/'+r['sha256']).status_code,404)
        self.assertEqual(self.client.get('/network/manifest.json').json['nodes'],0)
        response=self.client.get('/api/network/me',headers={'Authorization':'Bearer '+cfg['credential']['token']})
        self.assertEqual(response.status_code,401)
        other=self.node('b');other.publish(self.owned(other,0),True)
        db=connect(self.config['DATABASE'])
        try:purge(db,now=int(datetime.now(timezone.utc).timestamp())+91*86400)
        finally:db.close()
        self.assertEqual(self.client.get('/network/manifest.json').json['public_views'],0)

    def test_https_only_no_hub_changes_and_read_only_discovery(self):
        for value in ('http://example.com','https://x@y','https://a/path','https://a?token=secret','https://a:8443'):
            with self.assertRaises(ValueError):origin(value)
        node=self.node('a')
        with self.assertRaises(ValueError):node.init('https://other.example','a',['pumping-study'],True)
        before=self.client.get('/network/manifest.json').json
        self.client.get('/network/nodes');self.client.get('/network/views?world_id=pumping-study')
        after=self.client.get('/network/manifest.json').json
        self.assertEqual(before['nodes'],after['nodes']);self.assertEqual(before['public_views'],after['public_views'])

    def test_pause_keeps_reads_and_delete_available(self):
        node=self.node('a');node.publish(self.owned(node,0),True)
        Path(self.config['SUSPEND_FILE']).touch()
        self.assertFalse(self.client.get('/network/manifest.json').json['available'])
        self.assertEqual(self.post(node,'/api/network/heartbeat',{}).status_code,503)
        self.assertEqual(len(self.client.get('/network/nodes').json['nodes']),1)
        self.assertTrue(node.leave()['left'])

    def test_rotation_keeps_identity_and_invalidates_previous_token(self):
        from federation.internet import save
        node=self.node('a');cfg=node.load();old=cfg['credential']['token']
        cfg['credential']['expires_at']=0;save(node.credentials_path,cfg)
        node.cycle('pumping-study',['pump'])
        new=node.load()
        self.assertEqual(new['node_id'],cfg['node_id']);self.assertNotEqual(new['credential']['token'],old)
        self.assertEqual(self.client.get('/api/network/me',headers={'Authorization':'Bearer '+old}).status_code,401)

    def test_modified_relay_payload_is_rejected_before_local_import(self):
        a=self.node('a');a.publish(self.owned(a,0),True);b=self.node('b')
        original=self.transport
        def tampered(hub,method,path,body=None,token=None):
            value=original(hub,method,path,body,token)
            if path.startswith('/network/views/'):
                value['envelope']['view']['observation']['label']='forged'
            return value
        b.transport=tampered
        with self.assertRaisesRegex(ValueError,'SIGNATURE_INVALID'):b.cycle('pumping-study',['pump'])
        from federation.core import Node
        local=Node(b.state/'memory',b.load()['node_id'])
        self.assertEqual(local.project_world('pumping-study',['pump'],'connected')['view_hashes'],[])

    def test_backup_recovery_honors_account_deletion_for_public_node_and_views(self):
        from genius_beta import r2_backup as r2
        from test_r2_backup import ObjectStore
        a=self.node('a');a.publish(self.owned(a,0),True)
        b=self.node('b');b.publish(self.owned(b,1),True)
        store=ObjectStore();key=os.urandom(32)
        receipt=r2.backup_once(self.config['DATABASE'],self.root/'backup-status.json',store,key)
        r2.record_deletions([(a.load()['account_id'],'user',int(datetime.now(timezone.utc).timestamp()))],store,key)
        output=self.root/'restored'
        r2.recover(store,key,receipt['object_key'],output,True)
        db=connect(output/'genius.sqlite3')
        try:
            self.assertEqual(db.execute('SELECT id FROM network_nodes').fetchall()[0][0],b.load()['node_id'])
            self.assertEqual(db.execute('SELECT count(*) FROM network_nodes').fetchone()[0],1)
            self.assertEqual(db.execute('SELECT count(*) FROM network_views').fetchone()[0],1)
        finally:db.close()

    def test_reference_node_uses_normal_admission_and_restarts_without_new_views(self):
        from genius_beta.network_seed import bootstrap,WORLD
        self.serial+=1
        state=self.root/'reference'
        first=bootstrap(state,'https://hub.example',self.transport)
        result=first.cycle(WORLD,['pump'])
        self.assertTrue(result['calculation']['verification']['valid'])
        restarted=bootstrap(state,'https://hub.example',self.transport)
        self.assertEqual(first.load()['node_id'],restarted.load()['node_id'])
        manifest=self.client.get('/network/manifest.json').json
        self.assertEqual(manifest['nodes'],1);self.assertEqual(manifest['public_views'],3)


if __name__=='__main__':unittest.main()
