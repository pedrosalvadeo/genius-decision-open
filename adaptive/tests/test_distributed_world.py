"""Complementary views, declared identity and evidence-bound calculation."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from federation.core import Node
from federation.experiment import Process
from federation.views import compose, validate, MAX_VIEWS
from federation.world_example import example
from federation.world_experiment import run

REFERENCE='2026-01-01T00:00:00Z'
CURRENT='2026-01-01T01:00:00Z'
EXPIRES='2026-01-02T00:00:00Z'


class CompositionTests(unittest.TestCase):
    def setUp(self):self.views=example(REFERENCE,EXPIRES)

    def project(self,views=None):
        return compose(self.views if views is None else views,'pumping-study',['pump'],CURRENT)

    def codes(self,result):return {q['code'] for q in result['questions']}

    def test_complementary_coverage_and_affected_entities(self):
        r=self.project()
        self.assertEqual(r['status'],'READY_FOR_REVIEW')
        self.assertEqual(r['coverage']['local_entity_mentions'],8)
        self.assertEqual(r['coverage']['unique_entities'],6)
        self.assertEqual(set(r['boundary']['dependencies']),{'reserve','energy','hours'})
        self.assertEqual(set(r['boundary']['potential_impacts']),{'delivered','community'})
        self.assertIsNone(r['model']['law'])
        self.assertTrue(r['preparation']['scope_receipt']['review_required'])
        self.assertEqual(r['preparation']['scope_receipt']['unmapped_entities'],['pump'])
        self.assertEqual(r['empirical_validation'],'NOT_ASSESSED')
        self.assertFalse(r['physical_actions'])

    def test_incomplete_views_never_create_missing_stocks_or_people(self):
        for rows in ([self.views[0]],[self.views[1]],[self.views[2]],self.views[:2]):
            r=self.project(rows)
            self.assertIsNone(r['model'])
            self.assertEqual(r['status'],'NEEDS_REVISION')
        r=self.project(self.views[:2])
        self.assertNotIn('community',{e['id'] for e in r['observation']['entities']})
        self.assertIn('INCOMPLETE_MODEL',self.codes(r))

    def test_relay_and_order_do_not_multiply_entities_or_change_calculation(self):
        baseline=self.project()
        relay=self.project(list(reversed(self.views))+deepcopy(self.views))
        self.assertEqual(baseline,relay)
        self.assertEqual(len(relay['fragment_contributors']['/horizon']),3)

    def test_uncertain_identity_is_never_merged_by_matching_label(self):
        self.views[1]['identities'][-1]['status']='proposed'
        self.views[1]['observation']['entities'][-1]['label']='pump_tag'
        r=self.project()
        self.assertIn('IDENTITY_REVIEW',self.codes(r))
        self.assertIsNone(r['model'])
        self.assertEqual(r['coverage']['unique_entities'],7)

    def test_incompatible_identity_types_and_alias_self_edges_block(self):
        self.views[1]['observation']['entities'][-1]['kind']='organization'
        r=self.project()
        self.assertIn('ENTITY_KIND_CONFLICT',self.codes(r))
        self.assertIsNone(r['model'])
        self.views=example(REFERENCE,EXPIRES)
        self.views[0]['identities'][0]['global_id']='pump'
        r=self.project()
        self.assertIn('IDENTITY_COLLAPSES_RELATION',self.codes(r))
        self.assertIsNone(r['model'])

    def test_relationship_denial_and_reverse_equivalence_require_review(self):
        water=self.views[0]
        water['denials']=[dict(source='pump_tag',target='tank',kind='depends_on',evidence_ids=['e'])]
        r=self.project()
        self.assertIn('RELATION_CONFLICT',self.codes(r))
        self.assertIsNone(r['model'])
        self.assertEqual(len(r['denials']),1)

    def test_frame_and_freshness_disagreement_block_silent_snapshot_mix(self):
        for field,value in (('reference_time','2026-01-01T00:01:00Z'),('step_unit','hour'),('horizon',4),('layout','another-layout')):
            rows=deepcopy(self.views);rows[1]['frame'][field]=value
            r=self.project(rows)
            self.assertIn('FRAME_CONFLICT',self.codes(r));self.assertIsNone(r['model'])
        self.views[1]['valid_until']='2026-01-01T00:30:00Z'
        r=self.project()
        self.assertIn('STALE_VIEW',self.codes(r));self.assertIsNone(r['model'])
        self.assertIn('energy',{e['id'] for e in r['observation']['entities']})

    def test_quantities_and_fragment_prefix_conflicts_never_overwrite(self):
        self.views[1]['construction']['fragments'].append(dict(path='/stocks/0',value=dict(id='reserve',label='Changed',unit='litre',kind='persistent',initial='99/1',capacity='99/1'),claim_ids=['interpretation']))
        r=self.project()
        self.assertIn('FRAGMENT_CONFLICT',self.codes(r));self.assertIsNone(r['model'])
        self.views=example(REFERENCE,EXPIRES)
        self.views[1]['construction']['fragments'].append(dict(path='/stocks/0/initial',value='0/1',claim_ids=['interpretation']))
        r=self.project()
        self.assertIn('CONSTRUCTION_REVIEW',self.codes(r));self.assertIsNone(r['model'])

    def test_unit_mismatch_and_duplicate_resource_binding_fail_existing_validator(self):
        next(f for f in self.views[0]['construction']['fragments'] if f['path']=='/stocks/1')['value']['unit']='gallon'
        r=self.project();self.assertIsNone(r['model']);self.assertIn('INCOMPLETE_MODEL',self.codes(r))
        self.views=example(REFERENCE,EXPIRES)
        self.views[1]['bindings'][0]['entity_id']='crew_time'
        r=self.project();self.assertIsNone(r['model'])

    def test_unknowns_and_source_provenance_survive_without_execution(self):
        unknown='Missing consequences for downstream life'
        self.views[2]['observation']['unknowns'].append(unknown)
        source=self.views[2]['construction']['sources'][0]
        source['origin']='https://127.0.0.1/never-fetch'
        r=self.project()
        self.assertIn(unknown,r['observation']['unknowns'])
        self.assertIn(source['origin'],[s['origin'] for s in r['preparation']['receipt']['construction']['sources']])
        self.assertEqual(r['preparation']['receipt']['semantic_entailment'],'NOT_ASSESSED')
        self.assertEqual(r['preparation']['receipt']['claim_counts']['synthetic'],3)

    def test_view_versions_are_not_silently_replaced_and_future_sources_reject(self):
        variant=deepcopy(self.views[0]);variant['observation']['label']='Changed snapshot'
        r=self.project(self.views+[variant])
        self.assertIn('VIEW_VERSION_CONFLICT',self.codes(r));self.assertIsNone(r['model'])
        self.views[0]['construction']['sources'][0]['observed_at']=CURRENT
        with self.assertRaisesRegex(ValueError,'SOURCE_AFTER_REFERENCE'):validate(self.views[0])


class WorldMemoryTests(unittest.TestCase):
    def test_atomic_storage_privacy_budget_and_immutable_relay(self):
        with tempfile.TemporaryDirectory() as temp:
            node=Node(temp,'water',lambda:CURRENT)
            views=example(REFERENCE,EXPIRES)
            private=deepcopy(views[0]);private['shareable']=False
            node.ingest_views([private])
            self.assertEqual(node.export_views(),[])
            with self.assertRaises(ValueError):node.ingest_views([views[1],private],via='energy')
            self.assertEqual(node.hello()['remaining_views'],7)
            node.ingest_views(views[1:],via='energy')
            self.assertEqual(node.ingest_views(views[1:],via='community')['inserted'],0)
            self.assertIsNotNone(node.project_world('pumping-study',['pump'],'connected')['model'])
            self.assertIsNone(node.project_world('pumping-study',['pump'],'isolated')['model'])
            copies=[]
            for i in range(MAX_VIEWS-3):
                row=deepcopy(views[1]);row['view_id']='extra'+str(i);copies.append(row)
            node.ingest_views(copies,via='energy')
            extra=deepcopy(views[1]);extra['view_id']='overflow'
            with self.assertRaisesRegex(ValueError,'VIEW_MEMORY_BUDGET'):node.ingest_views([extra],via='energy')

    def test_peer_reads_cannot_import_or_compose(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Process(Path(temp)/'water','water')
            try:
                self.assertEqual(p.call('/views',peer=True)['records'],[])
                for path,body in (('/observe-views',dict(records=example(REFERENCE,EXPIRES)[:1])),
                    ('/project-world',dict(world_id='pumping-study',focus=['pump'],mode='connected')),
                    ('/sync-world',dict(node_id='energy'))):
                    with self.assertRaisesRegex(ValueError,'401'):p.call(path,body,peer=True)
            finally:p.close()

    def test_real_three_process_composition_and_native_routes(self):
        report=run()
        self.assertTrue(all(report['checks'].values()))
        self.assertEqual(report['connected']['coverage']['unique_entities'],6)
        self.assertEqual(report['trajectories']['restore_supply']['available']['daily'][-1]['stocks']['delivered'],'5/1')
        self.assertNotIn('read_token',json.dumps(report))
        self.assertFalse(report['physical_actions'])


if __name__=='__main__':unittest.main()
