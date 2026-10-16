"""Independent oracles for evidence exchange, lifecycle and local network lab."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from federation.core import Node, MAX_RECORDS, MAX_FORECASTS, decode, digest
from federation.experiment import Process, observation, run

CTX = dict(system='s', variable='demand', unit='litre', regime='r', data_kind='synthetic')
PAST = '2026-01-01T00:00:00Z'
FREEZE = '2026-01-02T00:00:00Z'
TARGET = '2026-01-03T00:00:00Z'
END = '2026-01-04T00:00:00Z'
EXPIRY = '2026-01-05T00:00:00Z'


def record(value=20, event='event', **kwargs):
    return observation(CTX, 'source', event, value, observed_at=PAST, valid_until=EXPIRY, **kwargs)


class MemoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.time = FREEZE
        self.node = Node(Path(self.temp.name)/'a', 'a', lambda: self.time)

    def freeze(self, name='f', mode='connected', ctx=None):
        return self.node.predict(name, ctx or CTX, mode, None, END)

    def test_relay_is_one_event_and_import_does_not_become_local(self):
        self.node.ingest([record(20,'local')])
        remote = record(100,'remote')
        self.node.ingest([remote], via='b')
        self.node.ingest([remote], via='c')
        self.node.ingest([record(100,'third')], via='c')
        self.assertEqual(self.freeze('solo','isolated')['estimate'],20)
        shared = self.freeze()
        self.assertEqual(shared['estimate'],100)
        self.assertEqual(len(shared['evidence']),3)
        with self.node.db() as db:
            self.assertEqual(db.execute('SELECT count(*) FROM receipts').fetchone()[0],3)

    def test_conflict_is_not_a_majority_vote_or_hidden_by_context(self):
        self.node.ingest([record()])
        competing = record(900)
        self.node.ingest([competing],via='b')
        self.node.ingest([competing],via='c')
        f = self.freeze()
        self.assertEqual(f['status'],'CONFLICT_REVIEW')
        self.assertIsNone(f['estimate'])
        self.assertEqual(self.freeze('solo','isolated')['estimate'],20)
        other = deepcopy(record()); other['context']['unit']='kWh'
        n = Node(Path(self.temp.name)/'other','other',lambda: FREEZE)
        n.ingest([record(),other])
        self.assertEqual(n.predict('f',CTX,'connected',None,END)['status'],'CONFLICT_REVIEW')

    def test_expired_incompatible_and_unknown_never_fill_with_zero(self):
        stale=record(); stale['valid_until']=FREEZE
        mismatch=record(0,'mismatch'); mismatch['context']['unit']='kWh'
        self.node.ingest([stale,mismatch])
        f=self.freeze()
        self.assertEqual(f['status'],'INSUFFICIENT_EVIDENCE')
        self.assertIsNone(f['estimate'])
        self.assertEqual(f['excluded']['stale'],1)
        self.assertEqual(f['excluded']['context_mismatch'],1)

    def test_private_export_and_batch_validation_are_atomic(self):
        private=record(20,'private',shareable=False)
        self.node.ingest([private])
        self.assertEqual(self.node.export(),[])
        with self.assertRaises(ValueError): self.node.ingest([record(),private],via='b')
        self.assertEqual(self.node.hello()['remaining_records'],MAX_RECORDS-1)
        invalid=record(30,'bad');invalid['value']=True
        with self.assertRaises(ValueError):self.node.ingest([record(),invalid])
        self.assertEqual(self.node.hello()['remaining_records'],MAX_RECORDS-1)

    def test_forecast_and_result_are_immutable_through_restart(self):
        self.node.ingest([record()])
        f=self.freeze()
        self.node.ingest([record(100,'new'),record(100,'new2')],via='b')
        self.assertEqual(self.freeze(),f)
        self.assertEqual(self.freeze('f2')['estimate'],100)
        self.time=TARGET
        target=record(60,'heldout'); target['observed_at']=TARGET
        score=self.node.observe_target('f',target)
        self.assertEqual(score['absolute_error'],40)
        restarted=Node(self.node.directory,'a',lambda:TARGET)
        self.assertEqual(restarted.observe_target('f',target),score)
        with self.assertRaises(ValueError): restarted.observe_target('f',record(70,'heldout'))
        with self.assertRaises(ValueError): self.freeze('f','isolated')
        with self.assertRaises(ValueError): Node(self.node.directory,'someone-else')

    def test_target_cannot_leak_into_training_or_predate_forecast(self):
        self.node.ingest([record()])
        self.freeze()
        cases=[]
        prior=record(50,'target'); prior['observed_at']=PAST;cases.append(prior)
        future=record(50,'target'); future['observed_at']=TARGET;cases.append(future)
        wrong=record(50,'target'); wrong['context']['regime']='another';cases.append(wrong)
        for bad in cases:
            with self.assertRaises(ValueError):self.node.observe_target('f',bad)
        self.time=TARGET
        same=record(50);same['observed_at']=TARGET
        with self.assertRaises(ValueError):self.node.observe_target('f',same)
        valid=record(50,'heldout');valid['observed_at']=TARGET
        self.node.observe_target('f',valid)
        self.assertEqual(len(self.node.export()),1)  # Targets do not silently train.

    def test_memory_and_forecast_limits_preserve_existing_state(self):
        rows=[record(i,str(i)) for i in range(MAX_RECORDS)]
        self.node.ingest(rows)
        self.assertEqual(self.node.ingest(rows,via='b')['inserted'],0)
        with self.assertRaises(ValueError):self.node.ingest([record(999,'overflow')])
        self.assertEqual(len(self.node.export()),MAX_RECORDS)
        for i in range(MAX_FORECASTS):self.freeze('f'+str(i))
        with self.assertRaises(ValueError):self.freeze('overflow')
        self.assertEqual(self.freeze('f0')['estimate'],63)

    def test_strict_input_and_time_validation(self):
        for raw in (b'{"value":1,"value":2}',b'{"x":NaN}',b'{"x":1.2}',b'x'*262145):
            with self.assertRaises(ValueError):decode(raw)
        variants=[]
        for key,value in (('value',-1),('value',None),('value',1000001),('observed_at',END),('observed_at','2026-01-01'),('shareable',1)):
            row=record();row[key]=value;variants.append(row)
        for row in variants:
            with self.assertRaises(ValueError):self.node.ingest([row])
        self.node.ingest([record()])
        with self.assertRaises(ValueError):self.node.predict('x',CTX,'connected',PAST,END)
        self.assertEqual(digest(record()),digest(deepcopy(record())))

    def test_clock_regression_cannot_move_received_evidence_into_the_past(self):
        self.node.ingest([record()])
        self.time=PAST
        with self.assertRaisesRegex(ValueError,'CLOCK_REGRESSION'):self.freeze()

    def test_peer_budget_is_not_bypassed_by_relaying_same_record(self):
        for i in range(8):self.node.ingest([record()],via='peer'+str(i))
        with self.assertRaisesRegex(ValueError,'PEER_BUDGET'):self.node.ingest([record()],via='peer8')
        self.assertEqual(len(self.node.export()),1)


class NetworkTests(unittest.TestCase):
    def test_peer_credentials_cannot_mutate_and_unknown_peers_cannot_be_contacted(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Process(Path(temp)/'a','a')
            self.addCleanup(p.close)
            self.assertEqual(p.call('/hello',peer=True)['node_id'],'a')
            for path,body in (('/observe',dict(records=[record()])),('/peers',dict(peers=[])),('/sync',dict(node_id='b'))):
                with self.assertRaisesRegex(ValueError,'401'):p.call(path,body,peer=True)
            with self.assertRaisesRegex(ValueError,'422'):p.call('/sync',dict(node_id='unknown'))
            with self.assertRaisesRegex(ValueError,'422'):
                p.call('/peers',dict(peers=[dict(node_id='b',port=80,read_token='x'*32,url='https://example.com')]))
            p.close()

    def test_actual_peer_identity_mismatch_does_not_import(self):
        with tempfile.TemporaryDirectory() as temp:
            a=Process(Path(temp)/'a','a');self.addCleanup(a.close)
            b=Process(Path(temp)/'b','b');self.addCleanup(b.close)
            b.call('/observe',dict(records=[record()]))
            descriptor=b.descriptor();descriptor['node_id']='impostor'
            a.call('/peers',dict(peers=[descriptor]))
            self.assertEqual(a.call('/sync',dict(node_id='impostor'))['status'],'UNAVAILABLE_OR_REJECTED')
            self.assertEqual(a.call('/experiences')['records'],[])
            a.close();b.close()

    def test_three_process_comparison_includes_failure_of_sharing(self):
        result=run()
        self.assertTrue(all(result['checks'].values()))
        helpful=result['comparisons']['helpful']['metrics']
        harmful=result['comparisons']['harmful']['metrics']
        self.assertEqual(helpful['isolated']['absolute_error_sum'],100)
        self.assertEqual(helpful['connected']['absolute_error_sum'],0)
        self.assertEqual(harmful['isolated']['absolute_error_sum'],200)
        self.assertEqual(harmful['connected']['absolute_error_sum'],300)
        self.assertEqual(result['comparisons']['helpful']['native_decision']['selected'],'connected')
        self.assertEqual(result['comparisons']['harmful']['native_decision']['selected'],'isolated')
        self.assertNotIn('admin_token',json.dumps(result))
        self.assertNotIn('read_token',json.dumps(result))
        self.assertFalse(result['physical_actions'])


if __name__ == '__main__':
    unittest.main()
