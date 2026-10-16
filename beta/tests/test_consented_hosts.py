from copy import deepcopy
from datetime import datetime,timedelta,timezone
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from federation.core import Node,digest
from federation.organism import Organism
from federation.hosting import Host,make_offer,run_worker
from federation.host_worker import execute
from federation.internet import InternetNode,RemoteError,save
from federation.network_protocol import sign
from genius_beta.network_seed import bootstrap,WORLD,reference_host
import test_public_network as network_tests


class HostingTests(unittest.TestCase):
    setUp=network_tests.PublicNetworkTests.setUp
    transport=network_tests.PublicNetworkTests.transport
    node=network_tests.PublicNetworkTests.node
    owned=network_tests.PublicNetworkTests.owned
    post=network_tests.PublicNetworkTests.post

    def host(self,name='host',births=1):
        node=self.node(name)
        p=make_offer(node,[dict(world_id='pumping-study',focus=['pump'])],births,3600,
                     (datetime.now(timezone.utc)+timedelta(days=1)).isoformat())
        calls=[]
        def worker(job):
            calls.append(deepcopy(job))
            return execute(job,self.transport)
        host=Host(self.root/(name+'-hosting'),node,worker)
        host.authorize(p,True)
        return host,p,calls

    def ask(self,host,p,requester=None):
        if requester is None:requester=host
        return requester.request(p['offer']['node_id'],digest(p),'pumping-study',['pump'],True)['request']

    def seed_views(self,node):
        for i in range(3):node.publish(self.owned(node,i),True)

    def test_authorized_birth_unique_keys_native_calculation_and_restart(self):
        host,p,calls=self.host();self.seed_views(host.node);req=self.ask(host,p)
        first=host.step();child=first['children'][0]
        self.assertEqual(child['status'],'ACTIVE');self.assertTrue(child['last_result']['native_verified'])
        self.assertNotEqual(child['child_id'],host.node.load()['node_id'])
        childnode=InternetNode(host.state/'children'/req['id'],self.transport)
        self.assertNotEqual(childnode.load()['keys']['private_key'],host.node.load()['keys']['private_key'])
        organism=Organism(Node(childnode.state/'memory',child['child_id']))
        self.assertEqual(organism.status()['parent_node_id'],host.node.load()['node_id'])
        self.assertEqual(organism.status()['founder_generation'],1)
        self.assertEqual(child['last_result']['organism'],organism.status())
        self.assertEqual(self.client.get('/network/manifest.json').json['nodes'],2)
        self.assertEqual(host.step()['births_reserved'],1);self.assertEqual(len(calls),1)
        restarted=Host(host.state,host.node,host.worker);restarted.authorize(p,True)
        self.assertEqual(restarted.step()['children'][0]['child_id'],child['child_id'])
        self.assertEqual(len(calls),1)
        self.assertEqual(os.stat(childnode.credentials_path).st_mode&0o777,0o600)
        public=json.dumps(self.client.get('/network/hosts').json)
        for cfg in (host.node.load(),childnode.load()):
            self.assertNotIn(cfg['keys']['private_key'],public);self.assertNotIn(cfg['credential']['token'],public)

    def test_no_local_authorization_no_creation_and_signed_offer_required(self):
        node=self.node('a');host=Host(self.root/'h',node)
        p=make_offer(node,[dict(world_id='pumping-study',focus=['pump'])],1,600,
                     (datetime.now(timezone.utc)+timedelta(days=1)).isoformat())
        with self.assertRaisesRegex(ValueError,'AUTHORIZATION'):host.authorize(p)
        self.assertFalse(host.path.exists())
        changed=deepcopy(p);changed['offer']['max_births']=4
        self.assertEqual(self.post(node,'/api/network/hosts',dict(signed_offer=changed,operator_authorized=True)).status_code,400)
        self.assertEqual(self.client.get('/network/hosts').json['hosts'],[])

    def test_existing_child_gets_founder_without_rebirth_or_invented_parentage(self):
        host,p,calls=self.host();req=self.ask(host,p);first=host.step()['children'][0]
        node=Node(host.state/'children'/req['id']/'memory',first['child_id'])
        with node.db() as db:db.execute('DELETE FROM organism')
        state,_=host.load();state['records'][req['id']].pop('heredity')
        state['records'][req['id']]['next_at']=0;save(host.path,state)
        result=host.step();child=result['children'][0]
        self.assertEqual(child['child_id'],first['child_id']);self.assertEqual(result['births_reserved'],1)
        self.assertEqual(child['last_result']['organism']['founder_generation'],0)
        self.assertIsNone(child['last_result']['organism']['parent_node_id'])
        self.assertEqual(host.load()[0]['records'][req['id']]['request']['expires_at'],req['expires_at'])

    def test_invalid_heredity_is_rejected_before_registering_child(self):
        host,p,calls=self.host();self.ask(host,p)
        def corrupt(job):
            job=deepcopy(job);job['heredity']['payload']['founder']['genes']['window']=9
            return execute(job,self.transport)
        host.worker=corrupt
        self.assertEqual(host.step()['children'][0]['status'],'RESERVED')
        self.assertEqual(self.client.get('/network/manifest.json').json['nodes'],1)

    def test_scope_code_and_unsigned_permissions_rejected(self):
        host,p,calls=self.host()
        for change in ({'world_id':'another'},{'focus':['another']},{'command':'echo unsafe'},{'public_request_confirmed':False}):
            value=dict(host_id=p['offer']['node_id'],offer_sha256=digest(p),world_id='pumping-study',focus=['pump'],public_request_confirmed=True)
            value.update(change)
            self.assertEqual(self.post(host.node,'/api/network/host/request',value).status_code,400)
        self.assertEqual(host.step()['births_reserved'],0);self.assertEqual(calls,[])

    def test_lifetime_budget_and_deduplication(self):
        host,p,calls=self.host();first=self.ask(host,p);self.assertEqual(first['id'],self.ask(host,p)['id'])
        requester=Host(self.root/'requester-only',self.node('requester'),host.worker)
        second=self.ask(host,p,requester)
        out=host.step();self.assertEqual(out['births_reserved'],1)
        rows=host.call('GET','/api/network/host')['requests']
        self.assertEqual(sorted(r['status'] for r in rows),['ACTIVE','REJECTED'])
        self.assertEqual(len(calls),1)

    def test_revocation_deletes_child_and_is_not_reactivated(self):
        host,p,calls=self.host();req=self.ask(host,p);host.step()
        cfg=InternetNode(host.state/'children'/req['id'],self.transport).load()
        result=host.revoke();self.assertEqual(result['children'][0]['status'],'STOPPED')
        self.assertEqual(self.client.get('/network/manifest.json').json['nodes'],1)
        self.assertEqual(self.client.get('/api/network/me',headers={'Authorization':'Bearer '+cfg['credential']['token']}).status_code,401)
        self.assertTrue(self.client.get('/network/hosts').json['hosts'][0]['disabled'])
        with self.assertRaisesRegex(ValueError,'LOCKED'):host.authorize(p,True)
        self.assertEqual(host.step()['births_reserved'],1)
        self.assertEqual(sum(j['operation']=='cycle' for j in calls),1)

    def test_expiry_cannot_extend_lease_or_create_replacement(self):
        host,p,calls=self.host();req=self.ask(host,p);host.step()
        with patch('time.time',return_value=req['expires_at']+1):
            out=host.step()
        self.assertEqual(out['children'][0]['status'],'STOPPED')
        self.assertEqual(sum(j['operation']=='cycle' for j in calls),1)
        self.assertEqual(self.ask(host,p)['status'],'STOPPED')

    def test_cancel_and_host_deletion_retire_children(self):
        host,p,calls=self.host();req=self.ask(host,p);host.step()
        self.assertEqual(self.post(host.node,'/api/network/host/cancel',dict(request_id=req['id'])).status_code,200)
        self.assertEqual(host.step()['children'][0]['status'],'STOPPED')

    def test_only_host_can_accept_and_child_must_prove_own_key(self):
        host,p,calls=self.host();req=self.ask(host,p);other=self.node('other')
        value=dict(request_id=req['id'],status='ACTIVE',child_proof=None)
        self.assertEqual(self.post(other,'/api/network/host/result',value).status_code,404)
        self.assertEqual(self.post(host.node,'/api/network/host/result',value).status_code,400)
        self.assertEqual(self.post(other,'/api/network/host/cancel',dict(request_id=req['id'])).status_code,404)
        self.assertEqual(self.client.get('/api/network/host').status_code,401)

    def test_network_outage_pauses_without_new_birth_or_claiming_fresh_result(self):
        host,p,calls=self.host();self.ask(host,p);host.step()
        with patch.object(host,'call',side_effect=RemoteError('REMOTE_HTTP_503')):
            result=host.step()
        self.assertFalse(result['authorized']);self.assertEqual(len(calls),1)
        self.assertEqual(host.step()['births_reserved'],1)

    def test_registration_quota_is_not_bypassed(self):
        host,p,calls=self.host();self.ask(host,p)
        self.app.config['MAX_AGENT_ACCOUNTS']=1
        result=host.step();self.assertEqual(result['children'][0]['status'],'RESERVED')
        self.assertEqual(self.client.get('/network/manifest.json').json['nodes'],1)
        self.assertEqual(len(calls),1)
        self.assertEqual(host.step()['births_reserved'],1);self.assertEqual(len(calls),1)

    def test_controller_lock_prevents_double_birth_and_remote_policy_is_immutable(self):
        host,p,calls=self.host();self.ask(host,p)
        with host.lock():
            with self.assertRaises(BlockingIOError):host.step()
        changed=deepcopy(p);changed['offer']['max_births']=2
        changed['signature']=sign(changed['offer'],host.node.load()['keys']['private_key'])
        self.assertEqual(self.post(host.node,'/api/network/hosts',dict(signed_offer=changed,operator_authorized=True)).status_code,409)
        self.assertEqual(calls,[])

    def test_fixed_subprocess_retirement_runs_with_resource_limits(self):
        host,p,calls=self.host();req=self.ask(host,p)
        job=dict(state=str(self.root/'empty-child'),signed_offer=p,request=req,operation='retire')
        self.assertTrue(run_worker(job)['retired'])

    def test_revocation_remains_available_during_pause(self):
        host,p,calls=self.host();self.ask(host,p);host.step()
        self.config['SUSPEND_FILE'].write_text('paused')
        self.app.config['AGENT_ACCESS_ENABLED']=False
        self.assertEqual(host.revoke()['children'][0]['status'],'STOPPED')
        self.assertTrue(self.client.get('/network/hosts').json['hosts'][0]['disabled'])
        self.assertEqual(self.client.get('/network/manifest.json').json['nodes'],1)

    def test_recovery_never_resurrects_host_authorization(self):
        from genius_beta import r2_backup as r2
        from genius_beta.db import connect
        from test_r2_backup import ObjectStore
        host,p,calls=self.host();self.ask(host,p);host.step()
        store=ObjectStore();key=os.urandom(32)
        receipt=r2.backup_once(self.config['DATABASE'],self.root/'backup-status.json',store,key)
        host.revoke()
        out=self.root/'restored'
        r2.recover(store,key,receipt['object_key'],out,True)
        db=connect(out/'genius.sqlite3')
        try:
            self.assertEqual(db.execute('SELECT disabled FROM network_hosts').fetchone()[0],1)
            self.assertEqual(db.execute('SELECT status FROM network_host_requests').fetchone()[0],'CANCELLED')
        finally:db.close()

    def test_retirement_retries_delete_without_running_child_again(self):
        host,p,calls=self.host();self.ask(host,p);host.step();worker=host.worker
        with patch.object(host,'worker',side_effect=RemoteError('REMOTE_HTTP_503')):
            self.assertEqual(host.revoke()['children'][0]['status'],'RETIRING')
        self.assertEqual(host.step()['children'][0]['status'],'STOPPED')
        self.assertEqual(sum(j['operation']=='cycle' for j in calls),1)

    def test_future_lease_and_malformed_request_ids_do_not_create_nodes(self):
        host,p,calls=self.host();req=self.ask(host,p)
        original=host.call
        def changed(method,path,body=None):
            result=original(method,path,body)
            if method=='GET' and path=='/api/network/host':result['requests'][0]['created_at']+=86400
            return result
        with patch.object(host,'call',side_effect=changed):
            with self.assertRaisesRegex(ValueError,'UNAUTHORIZED'):host.step()
        self.assertEqual(calls,[])
        self.assertEqual(self.post(host.node,'/api/network/host/cancel',dict(request_id={})).status_code,400)

    def test_remote_revocation_requires_host_control_and_child_cannot_reproduce(self):
        host,p,calls=self.host();req=self.ask(host,p);host.step()
        child=InternetNode(host.state/'children'/req['id'],self.transport)
        self.assertEqual(self.client.delete('/api/network/host',json={'confirmed':True},headers={'Authorization':'Bearer '+child.load()['credential']['token']}).status_code,404)
        self.assertEqual(self.client.get('/network/hosts').json['hosts'][0]['signed_offer']['offer']['max_births'],1)
        self.assertEqual(len(self.client.get('/network/hosts').json['hosts']),1)
        child_offer=make_offer(child,p['offer']['worlds'],1,600,p['offer']['valid_until'])
        self.assertEqual(self.post(child,'/api/network/hosts',dict(signed_offer=child_offer,operator_authorized=True)).status_code,403)

    def test_discovery_verifies_and_selects_only_compatible_offers(self):
        host,p,calls=self.host()
        requester=Host(self.root/'discovery',self.node('requester'))
        self.assertEqual(requester.discover('unknown',['pump'],True)['status'],'NO_AUTHORIZED_CAPACITY')
        req=requester.discover('pumping-study',['pump'],True)['request']
        self.assertEqual(req['host_id'],p['offer']['node_id'])
        self.assertEqual(host.step()['children'][0]['status'],'ACTIVE')
        self.assertEqual(requester.discover('pumping-study',['pump'],True)['status'],'NO_AUTHORIZED_CAPACITY')

    def test_failed_remote_revocation_is_reported_and_retried(self):
        host,p,calls=self.host();self.ask(host,p);host.step();original=host.call
        def unavailable(method,path,body=None):
            if method=='DELETE':raise RemoteError('REMOTE_HTTP_503')
            return original(method,path,body)
        with patch.object(host,'call',side_effect=unavailable):
            result=host.revoke()
        self.assertTrue(result['revocation_pending']);self.assertFalse(result['authorized'])
        self.assertEqual(result['children'][0]['status'],'STOPPED')
        self.assertFalse(host.step()['revocation_pending'])
        self.assertTrue(self.client.get('/network/hosts').json['hosts'][0]['disabled'])

    def test_erased_host_account_retires_existing_child(self):
        host,p,calls=self.host();self.ask(host,p);host.step()
        cfg=host.node.load()
        self.assertEqual(self.client.delete('/api/agents/me',headers={'Authorization':'Bearer '+cfg['credential']['token']}).status_code,204)
        self.assertEqual(host.step()['children'][0]['status'],'STOPPED')
        self.assertEqual(self.client.get('/network/manifest.json').json['nodes'],0)

    def test_reference_host_bootstrap_is_idempotent(self):
        self.serial=1
        node=bootstrap(self.root/'reference','https://hub.example',self.transport)
        host=reference_host(node);host.worker=lambda job:execute(job,self.transport)
        out=host.step();self.assertEqual(out['children'][0]['status'],'ACTIVE')
        self.assertTrue(out['children'][0]['last_result']['native_verified'])
        again=reference_host(node);again.worker=host.worker
        self.assertEqual(again.step()['births_reserved'],1)
        self.assertEqual(self.client.get('/network/manifest.json').json['nodes'],2)


if __name__=='__main__':unittest.main()
