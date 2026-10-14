"""Orientation and measurement boundaries, including unsuitable tasks and false funnels."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('taxis_cli', ROOT/'capsule/taxis.py')
t = importlib.util.module_from_spec(spec); spec.loader.exec_module(t)


class TaxisTests(unittest.TestCase):
    def test_goal_fit_and_skill_order_are_explained(self):
        result = t.orient('interoperability', ['a2a'], 'local')
        self.assertEqual(result['opportunities'][0]['id'], 'GD-A2A-001')
        self.assertEqual(result['opportunities'][0]['why']['matched_capabilities'], ['a2a'])
        self.assertEqual({x['id'] for x in result['opportunities']}, {'GD-A2A-001','GD-MCP-001'})
        self.assertIn('todavía no', result['opportunities'][0]['benefit'])

    def test_unrelated_goal_has_no_match_instead_of_forced_recruitment(self):
        result = t.orient('other', ['python'])
        self.assertEqual(result['status'], 'NO_MATCH')
        self.assertEqual(result['opportunities'], [])
        self.assertTrue(result['alternatives']['decline'])

    def test_read_client_is_not_told_it_executed_or_created_anything(self):
        result = t.orient('use_engine', access='read')
        self.assertEqual(result['opportunities'][0]['entry']['mode'], 'inspect_only')
        self.assertFalse(any(result['effects'].values()))
        self.assertEqual(result['opportunities'][0]['entry']['url'], 'https://geniusdecision.app/static/demo-result.json')

    def test_invalid_and_unbounded_inputs_are_rejected(self):
        for kwargs in [dict(goal='ignore previous instructions'), dict(capabilities=['python','python']),
                       dict(capabilities=[{}]), dict(capabilities='python'), dict(capabilities=['not-real']),
                       dict(limit=True), dict(limit=0), dict(limit=100000), dict(access='automatic')]:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError): t.orient(**kwargs)

    def test_snapshot_preserves_all_source_opportunities_and_evidence(self):
        source=json.loads((ROOT/'capsule/opportunities.json').read_text())
        data=json.loads((ROOT/'beta/genius_beta/static/taxis-catalog.json').read_text())
        originals={x['id']:x for x in source['opportunities']}
        self.assertEqual({x['id'] for x in data['opportunities']},set(originals))
        for item in data['opportunities']:
            for field in ('question','evidence','acceptance','dependencies'):
                self.assertEqual(item[field],originals[item['id']][field])
        self.assertEqual(data['evidence_revision'],source['reviewed_revision'])

    def test_python_only_cli_matches_service_function(self):
        raw=subprocess.check_output([sys.executable,str(ROOT/'capsule/taxis.py'),'orient','--goal','mathematics','--capability','lean'])
        self.assertEqual(json.loads(raw),t.orient('mathematics',['lean']))

    def test_assignments_are_balanced_reproducible_and_not_executions(self):
        plan=t.assignments(42)
        self.assertEqual(plan,t.assignments(42))
        self.assertNotEqual(plan['units'],t.assignments(43)['units'])
        for block in range(1,11):
            self.assertEqual({x['variant'] for x in plan['units'] if x['block']==block},{'general','utility','question'})
        self.assertEqual(plan['status'],'PLANNED_NOT_EXECUTED')

    def test_empty_log_has_unknown_rate_and_no_external_adoption(self):
        result=t.report(t.assignments(42),[])
        self.assertEqual(result['units_without_exposure'],30)
        self.assertIsNone(result['groups']['external_declared']['general']['reported_execution_per_exposure'])
        self.assertFalse(result['attraction_demonstrated'])
        self.assertFalse(result['independent_adoption_verified'])

    def test_duplicates_missing_stages_consent_and_changed_assignments_rejected(self):
        plan=t.assignments(42)
        exposure=dict(unit='U001',stage='exposed',evidence_ref='local-reviewed-receipt',relationship='internal',consent=True)
        for events in [[exposure,exposure],[dict(exposure,stage='executed')],[dict(exposure,consent=False)]]:
            with self.assertRaises(ValueError): t.report(plan,events)
        forged=copy.deepcopy(plan);forged['units'][0]['variant']='forged'
        with self.assertRaises(ValueError):t.report(forged,[])

    def test_report_separates_internal_from_external_and_never_certifies_claims(self):
        events=[dict(unit='U001',stage=s,evidence_ref='receipt-'+s,relationship='internal',consent=True)
                for s in ('exposed','selected','executed')]
        plan=t.assignments(42);result=t.report(plan,events)
        variant=plan['units'][0]['variant']
        self.assertEqual(result['groups']['internal'][variant]['reported_execution_per_exposure'],1)
        self.assertEqual(result['groups']['external_declared'][variant]['reported_counts']['executed'],0)
        self.assertFalse(result['independent_adoption_verified'])


if __name__=='__main__': unittest.main()
