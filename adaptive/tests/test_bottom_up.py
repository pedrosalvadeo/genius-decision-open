"""Local initiative: real peers, freshness, authority, and finite work budgets."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from federation.bottom_up_experiment import fixture, run
from federation.core import Node, digest
from federation.experiment import Process
from federation.initiative import Initiative, catalog

REFERENCE='2026-01-01T00:00:00Z'
CURRENT='2026-01-01T01:00:00Z'
EXPIRES='2026-01-02T00:00:00Z'


class InitiativeTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.clock=CURRENT
        self.views,self.delayed,self.conflict=fixture(REFERENCE,EXPIRES)
        self.nodes={v['owner']:Node(Path(self.temp.name)/v['owner'],v['owner'],lambda:self.clock) for v in self.views}
        for v in self.views:self.nodes[v['owner']].ingest_views([v])
        self.peers={name:dict(node_id=name,port=i+1,read_token='x'*32) for i,name in enumerate(('energy','community'))}
        self.by_port={p['port']:self.nodes[name] for name,p in self.peers.items()}
        self.requests=[]
        self.offline=set()
        self.initiative=Initiative(self.nodes['water'],lambda:dict(self.peers),self.fetch)

    def fetch(self,port,token,method,path):
        self.requests.append((port,method,path))
        if port in self.offline:raise OSError('offline')
        node=self.by_port[port]
        if path=='/view-index':return catalog(node)
        self.assertEqual(path,'/views')
        return dict(node_id=node.node_id,records=node.export_views())

    def start(self,run_id='trial',cycles=10):
        return self.initiative.start(dict(id=run_id,world_id='pumping-study',focus=['pump'],cycles=cycles,interval_ms=100),background=False)

    def ready(self):
        self.start()
        self.nodes['energy'].ingest_views([self.delayed])
        self.initiative.tick('trial')
        return self.initiative.tick('trial')

    def test_self_selected_inquiry_completes_model_and_does_not_refetch_duplicates(self):
        self.start()
        for _ in range(2):r=self.initiative.tick('trial')
        self.assertIsNone(r['current']['model_sha256'])
        self.assertEqual(r['imports'],2)
        self.nodes['energy'].ingest_views([self.delayed])
        for _ in range(2):r=self.initiative.tick('trial')
        self.assertIsNotNone(r['current']['model_sha256'])
        self.assertEqual(r['calculations'][0]['final_stocks']['restore_supply']['available']['delivered'],'3/1')
        count=sum(path=='/views' for _,_,path in self.requests)
        for _ in range(2):r=self.initiative.tick('trial')
        self.assertEqual(count,sum(path=='/views' for _,_,path in self.requests))
        self.assertEqual(len(r['calculations']),1)
        self.assertEqual(r['ticks'][-1]['reason'],'REFRESH')
        self.assertEqual(r['imports'],3)
        self.assertNotIn('read_token',json.dumps(r))

    def test_new_contradiction_invalidates_current_but_keeps_historical_calculation(self):
        r=self.ready(); original=r['current']['model_sha256']
        self.nodes['water'].ingest_views([self.conflict])
        r=self.initiative.tick('trial')
        self.assertIsNone(r['current']['model_sha256'])
        self.assertIn('FRAGMENT_CONFLICT',[q['code'] for q in r['current']['questions']])
        self.assertEqual(r['last_calculated_model'],original)
        self.assertEqual(len(r['calculations']),1)
        self.assertEqual(r['ticks'][-1]['reason'],'EVIDENCE_REVIEW')

    def test_disconnected_cache_expires_and_cannot_be_reused_as_current(self):
        r=self.ready(); original=r['current']['model_sha256']
        self.offline=set(self.by_port)
        r=self.initiative.tick('trial')
        self.assertEqual(r['current']['model_sha256'],original)
        self.assertEqual(r['ticks'][-1]['outcome'],'UNAVAILABLE_OR_REJECTED')
        self.clock='2026-01-03T00:00:00Z'
        r=self.initiative.tick('trial')
        self.assertIsNone(r['current']['model_sha256'])
        self.assertIn('STALE_VIEW',[q['code'] for q in r['current']['questions']])
        self.assertEqual(r['last_calculated_model'],original)

    def test_private_and_unrelated_views_do_not_trigger_payload_read(self):
        empty=Node(Path(self.temp.name)/'empty','empty',lambda:self.clock)
        private=deepcopy(self.views[2]);private['owner']='empty';private['shareable']=False
        empty.ingest_views([private]);self.assertEqual(catalog(empty)['views'],[])
        unrelated=deepcopy(self.views[2]);unrelated['owner']='empty';unrelated['world_id']='other'
        empty.ingest_views([unrelated])
        self.by_port={1:empty};self.peers={'empty':dict(node_id='empty',port=1,read_token='x'*32)}
        self.start(cycles=1);r=self.initiative.tick('trial')
        self.assertEqual(self.requests,[(1,'GET','/view-index')])
        self.assertEqual(r['imports'],0)

    def test_index_mismatch_and_private_import_preserve_memory(self):
        self.start()
        self.initiative.fetch=lambda *args:dict(format='genius-view-index/1',node_id='intruder',views=[])
        r=self.initiative.tick('trial')
        self.assertEqual(r['ticks'][-1]['outcome'],'UNAVAILABLE_OR_REJECTED')
        private=deepcopy(self.views[1]);private['shareable']=False
        self.initiative.fetch=lambda port,token,method,path: (
            dict(format='genius-view-index/1',node_id='energy',views=[dict(hash=digest(private),world_id=private['world_id'])])
            if path=='/view-index' else dict(node_id='energy',records=[private]))
        r=self.initiative.tick('trial')
        self.assertEqual(r['ticks'][-1]['outcome'],'UNAVAILABLE_OR_REJECTED')
        self.assertEqual(r['current']['view_hashes'],[digest(self.views[0])])

    def test_index_race_rejects_incomplete_payload_atomically(self):
        self.start()
        h=digest(self.views[2])
        self.initiative.fetch=lambda port,token,method,path: (
            dict(format='genius-view-index/1',node_id='community',views=[dict(hash=h,world_id='pumping-study')])
            if path=='/view-index' else dict(node_id='community',records=[]))
        r=self.initiative.tick('trial')
        self.assertEqual(r['imports'],0)
        self.assertEqual(r['ticks'][0]['outcome'],'UNAVAILABLE_OR_REJECTED')

    def test_budget_restart_and_run_identity_do_not_resume_network_work(self):
        self.start(cycles=1);r=self.initiative.tick('trial')
        self.assertEqual(r['status'],'BUDGET_EXHAUSTED')
        n=len(self.requests);self.initiative.tick('trial');self.assertEqual(len(self.requests),n)
        with self.assertRaisesRegex(ValueError,'RUN_ID_USED'):self.start()
        self.start('second');self.initiative.tick('second')
        restored=Initiative(self.nodes['water'],lambda:self.peers,self.fetch)
        self.assertEqual(restored.status('second')['status'],'INTERRUPTED')
        n=len(self.requests);restored.tick('second');self.assertEqual(len(self.requests),n)
        self.assertEqual(restored.status('trial'),r)

    def test_start_limits_and_stop_old_run_does_not_stop_current_run(self):
        for cycles in (0,65,True):
            with self.assertRaises(ValueError):self.start(cycles=cycles)
        self.start(cycles=1)
        with self.assertRaisesRegex(ValueError,'RUN_ACTIVE'):self.start('another')
        self.initiative.tick('trial')
        self.start('second');self.initiative.stop('trial')
        self.assertFalse(self.initiative.stop_event.is_set())
        self.assertEqual(self.initiative.stop('second')['status'],'STOPPED')
        for name in ('third','fourth'):
            self.start(name,cycles=1);self.initiative.tick(name)
        with self.assertRaisesRegex(ValueError,'RUN_BUDGET'):self.start('fifth')

    def test_no_peers_still_stops_at_budget(self):
        self.peers={};self.start(cycles=1)
        r=self.initiative.tick('trial')
        self.assertEqual(r['status'],'BUDGET_EXHAUSTED')
        self.assertEqual(r['http_requests'],0)
        self.assertEqual(r['ticks'][0]['outcome'],'NO_PEERS')

    def test_peer_credentials_cannot_start_stop_or_read_private_activity(self):
        process=Process(Path(self.temp.name)/'process','water')
        try:
            self.assertEqual(process.call('/view-index',peer=True)['views'],[])
            for path in ('/initiative-start','/initiative-status','/initiative-stop'):
                with self.assertRaisesRegex(ValueError,'401'):process.call(path,dict(id='trial'),peer=True)
        finally:process.close()

    def test_real_processes_late_evidence_conflict_and_disconnection(self):
        report=run()
        self.assertTrue(all(report['checks'].values()))
        self.assertEqual(report['measurements']['calculated_final_delivery'],'3/1')
        self.assertIsNone(report['measurements']['baseline_prediction'])
        self.assertNotIn('read_token',json.dumps(report))
        self.assertFalse(report['physical_actions'])


if __name__=='__main__':unittest.main()
