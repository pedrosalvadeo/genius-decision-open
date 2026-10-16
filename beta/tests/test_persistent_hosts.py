"""Persistent permission keeps identity; rest, revocation and evidence expiry differ."""
from copy import deepcopy
from datetime import datetime,timedelta,timezone
import os
from pathlib import Path
import shutil
import time
import unittest
from unittest.mock import patch

import test_consented_hosts as finite
from federation.core import Node,digest
from federation.hosting import Host,make_offer
from federation.hosting_protocol import validate_offer,PERSISTENT
from federation.host_worker import execute
from federation.internet import InternetNode,RemoteError,save
from federation.organism import Organism
from genius_beta.db import connect,initialize,MIGRATIONS
from genius_beta.network_seed import bootstrap,reference_host


class PersistentTests(unittest.TestCase):
    setUp=finite.HostingTests.setUp
    transport=finite.HostingTests.transport
    node=finite.HostingTests.node
    owned=finite.HostingTests.owned
    post=finite.HostingTests.post
    host=finite.HostingTests.host
    ask=finite.HostingTests.ask
    seed_views=finite.HostingTests.seed_views

    def ready(self):
        host,p,calls=self.host();self.seed_views(host.node);req=self.ask(host,p)
        child=host.step()['children'][0]
        return host,p,calls,req,child

    def due(self,host):
        state,_=host.load()
        for record in state['records'].values():record['next_at']=0
        save(host.path,state)

    def test_conversion_preserves_identity_genes_memory_budget_and_request(self):
        host,p,calls,req,child=self.ready()
        client=InternetNode(host.state/'children'/req['id'],self.transport)
        keys=client.load()['keys'];organism=Organism(Node(client.state/'memory',child['child_id'])).status()
        host.persist(True);self.due(host)
        with patch('time.time',return_value=time.time()+2*86400):out=host.step()
        self.assertEqual(out['lifecycle'],'PERSISTENT_REVOCABLE')
        self.assertEqual(out['children'][0]['child_id'],child['child_id'])
        self.assertEqual(out['births_reserved'],1);self.assertEqual(client.load()['keys'],keys)
        self.assertEqual(Organism(Node(client.state/'memory',child['child_id'])).status(),organism)
        row=host.call('GET','/api/network/host')['requests'][0]
        self.assertEqual(row['id'],req['id']);self.assertIsNone(row['expires_at'])
        new=host.load()[0]['signed_offer']
        self.assertEqual(self.ask(host,new)['id'],req['id'])
        self.assertTrue(host.persist(True)['duplicate'])
        self.assertEqual(self.client.get('/network/manifest.json').json['nodes'],2)
        with connect(self.config['DATABASE']) as db:
            self.assertIsNotNone(db.execute('SELECT accepted_at FROM network_host_requests').fetchone()[0])
            self.assertEqual(digest(__import__('json').loads(db.execute('SELECT previous_signed_offer FROM network_hosts').fetchone()[0])),digest(p))

    def test_new_persistent_offer_discovery_and_null_expiry(self):
        node=self.node('host');host=Host(self.root/'hosting',node,lambda job:execute(job,self.transport))
        signed=make_offer(node,[dict(world_id='pumping-study',focus=['pump'])],1,persistent=True)
        host.authorize(signed,True)
        requester=Host(self.root/'requester',self.node('requester'))
        req=requester.discover('pumping-study',['pump'],True)['request']
        self.assertIsNone(req['expires_at']);self.assertEqual(host.step()['births_reserved'],1)
        self.assertEqual(self.client.get('/network/hosts').json['hosts'][0]['active_requests'],1)
        bad=deepcopy(signed);bad['offer']['lease_seconds']=86400
        with self.assertRaises(ValueError):validate_offer(bad)

    def test_explicit_permission_and_unchanged_scope_required(self):
        host,p,calls=self.host()
        with self.assertRaisesRegex(ValueError,'AUTHORIZATION'):host.persist()
        for births,world in ((2,'pumping-study'),(1,'elsewhere')):
            changed=make_offer(host.node,[dict(world_id=world,focus=['pump'])],births,persistent=True)
            response=self.post(host.node,'/api/network/host/persist',dict(signed_offer=changed,previous_sha256=digest(p),operator_authorized=True))
            self.assertEqual(response.status_code,409)
        self.assertEqual(host.load()[0]['signed_offer'],p)

    def test_lost_conversion_response_recovers_after_restart_without_rebirth(self):
        host,p,calls,req,child=self.ready();original=host.call
        def lost(method,path,body=None):
            result=original(method,path,body)
            if path=='/api/network/host/persist':raise RemoteError('REMOTE_HTTP_503')
            return result
        with patch.object(host,'call',side_effect=lost):
            with self.assertRaises(RemoteError):host.persist(True)
        self.assertIn('pending_persistent',host.load()[0])
        restarted=Host(host.state,host.node,host.worker)
        out=restarted.step()
        self.assertEqual(out['children'][0]['child_id'],child['child_id'])
        self.assertEqual(out['births_reserved'],1)
        self.assertNotIn('pending_persistent',host.load()[0])

    def test_pause_restart_renew_and_resume_same_identity(self):
        host,p,calls,req,child=self.ready();host.persist(True)
        client=InternetNode(host.state/'children'/req['id'],self.transport)
        original_token=client.load()['credential']['token'];stamp=time.time()
        host.pause();host=Host(host.state,host.node,host.worker)
        for days in (1,6,12):
            with patch('time.time',return_value=stamp+days*86400):
                out=host.step()
                self.assertEqual(out['children'][0]['activity'],'RESTING')
                self.assertEqual(out['children'][0]['rest_reason'],'OPERATOR_PAUSE')
        self.assertEqual(sum(j['operation']=='cycle' for j in calls),1)
        self.assertNotEqual(client.load()['credential']['token'],original_token)
        self.assertNotIn('maintenance_error',host.load()[0]['records'][req['id']])
        with patch('time.time',return_value=stamp+12*86400+1):
            host.pause(False);self.due(host);out=host.step()
        self.assertEqual(out['children'][0]['child_id'],child['child_id'])
        self.assertEqual(sum(j['operation']=='cycle' for j in calls),2)

    def test_resource_rest_keeps_identity_and_retry_spacing(self):
        host,p,calls,req,child=self.ready();host.persist(True);self.due(host)
        with patch('federation.hosting.shutil.disk_usage',return_value=type('Usage',(),{'free':0})()):
            out=host.step()
        self.assertEqual(out['children'][0]['rest_reason'],'DISK_RESERVE')
        self.assertEqual(len(calls),1)
        out=host.step();self.assertEqual(out['children'][0]['child_id'],child['child_id'])
        self.assertEqual(len(calls),2);host.step();self.assertEqual(len(calls),2)

    def test_persistent_lifetime_does_not_extend_evidence(self):
        host,p,calls,req,child=self.ready();host.persist(True);self.due(host)
        future=(datetime.now(timezone.utc)+timedelta(days=2)).isoformat()
        with patch('federation.internet.Node',side_effect=lambda *a,**kw:Node(*a,clock=lambda:future,**kw)):out=host.step()
        self.assertEqual(out['children'][0]['activity'],'RESTING')
        self.assertFalse(out['children'][0]['last_result']['native_verified'])
        self.assertEqual(out['children'][0]['child_id'],child['child_id'])

    def test_revocation_and_cancel_remain_terminal(self):
        host,p,calls,req,child=self.ready();host.persist(True);host.pause()
        out=host.revoke();self.assertEqual(out['children'][0]['status'],'STOPPED')
        with self.assertRaisesRegex(ValueError,'LOCKED'):host.pause(False)
        with self.assertRaisesRegex(ValueError,'LOCKED'):host.persist(True)
        self.assertEqual(sum(j['operation']=='cycle' for j in calls),1)

    def test_conversion_cannot_revive_expired_or_cancelled_request(self):
        host,p,calls,req,child=self.ready()
        with patch('time.time',return_value=req['expires_at']+1):
            host.persist(True);out=host.step()
        self.assertEqual(out['children'][0]['status'],'STOPPED')
        self.assertEqual(self.ask(host,host.load()[0]['signed_offer'])['id'],req['id'])
        self.assertEqual(sum(j['operation']=='cycle' for j in calls),1)

    def test_cancelled_request_not_converted_or_replaced(self):
        host,p,calls,req,child=self.ready()
        self.post(host.node,'/api/network/host/cancel',dict(request_id=req['id']))
        host.persist(True);self.assertEqual(host.step()['children'][0]['status'],'STOPPED')
        self.assertEqual(self.ask(host,host.load()[0]['signed_offer'])['id'],req['id'])

    def test_expired_offer_cannot_convert(self):
        host,p,calls=self.host()
        with patch('time.time',return_value=time.time()+2*86400):
            with self.assertRaisesRegex(ValueError,'EXPIRED'):host.persist(True)

    def test_reference_conversion_is_opt_in_and_idempotent(self):
        self.serial=1;node=bootstrap(self.root/'reference','https://hub.example',self.transport)
        host=reference_host(node);host.worker=lambda job:execute(job,self.transport)
        old=host.step()['children'][0]
        self.assertNotEqual(reference_host(node).load()[1]['format'],PERSISTENT)
        converted=reference_host(node,True);converted.worker=host.worker
        self.assertEqual(converted.step()['children'][0]['child_id'],old['child_id'])
        self.assertEqual(reference_host(node,True).step()['births_reserved'],1)

    def test_recovery_disables_persistent_authorization(self):
        original=self.host
        def persistent(*args,**kwargs):
            host,p,calls=original(*args,**kwargs);host.persist(True)
            return host,host.load()[0]['signed_offer'],calls
        self.host=persistent
        finite.HostingTests.test_recovery_never_resurrects_host_authorization(self)

    def test_migration_from_013_preserves_rows_and_foreign_keys(self):
        from genius_beta.app import create_app
        old=self.root/'old-migrations';old.mkdir()
        for path in sorted(MIGRATIONS.glob('*.sql')):
            if path.name<'014':shutil.copyfile(path,old/path.name)
        self.config['DATABASE']=self.root/'old.sqlite3'
        with patch('genius_beta.db.MIGRATIONS',old):
            self.app=create_app(self.config);self.client=self.app.test_client(use_cookies=False)
            host,p,calls,req,child=self.ready()
        initialize(self.config['DATABASE'])
        with connect(self.config['DATABASE']) as db:
            self.assertEqual(db.execute('PRAGMA foreign_key_check').fetchall(),[])
            self.assertEqual(db.execute('SELECT child_id FROM network_host_requests').fetchone()[0],child['child_id'])
            self.assertEqual(db.execute('SELECT expires_at FROM network_host_requests').fetchone()[0],req['expires_at'])
        host.persist(True);self.assertEqual(host.step()['children'][0]['child_id'],child['child_id'])


if __name__=='__main__':unittest.main()
