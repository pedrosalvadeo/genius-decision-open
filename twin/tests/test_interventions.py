"""Independent balance/outcome oracles for generated resource interventions."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from genius_twin import interventions, registry
from genius_twin.app import create_app
from genius_twin.stockflow import compute_trajectories


class InterventionTests(unittest.TestCase):
    def setUp(self):
        fixture = interventions.example()
        self.base, self.design = fixture['model'], fixture['design']

    def test_enumeration_preserves_common_world_and_exact_balances(self):
        saved = deepcopy(self.base)
        model, receipt = interventions.generate(self.base, self.design)
        self.assertEqual(self.base, saved)
        self.assertEqual(receipt['generated_count'], 2)
        for field in receipt['preserved_fields']:
            self.assertEqual(model[field], self.base[field])
        self.assertEqual(model['policies'][0], self.base['policies'][0])
        traces = compute_trajectories(model)
        expected = {'baseline': ['2/1','1/1','0/1','0/1'],
            'intervention.redistribute.1': ['2/1','1/1','1/1','0/1'],
            'intervention.redistribute.2': ['2/1','1/1','2/1','1/1']}
        for pid, amounts in expected.items():
            self.assertEqual([r['stocks']['target'] for r in traces[pid]['demand']['daily']], amounts)
        rows = traces['intervention.redistribute.2']['demand']['daily']
        self.assertEqual([r['stocks']['source'] for r in rows], ['4/1','4/1','2/1','2/1'])
        self.assertEqual([r['stocks']['time'] for r in rows], ['3/1','2/1','2/1','2/1'])
        self.assertNotIn('relation.pipe', rows[0]['capabilities'])
        self.assertIn('relation.pipe', rows[1]['capabilities'])
        self.assertEqual((model, receipt), interventions.generate(self.base, self.design))

    def test_native_kernel_selects_sufficient_transfer_and_preserves_unknowns(self):
        model, _ = interventions.generate(self.base, self.design)
        result = registry.evaluate(model)
        self.assertTrue(result['verification']['valid'])
        canonical = result['canonical_results']
        self.assertEqual(canonical['decision']['selected'], 'intervention.redistribute.2')
        for pid, expected in [('baseline','0/1'),('intervention.redistribute.1','0/1'),('intervention.redistribute.2','1/1')]:
            self.assertEqual(canonical['policies'][pid]['task_probability']['value'], expected)
            self.assertEqual(canonical['policies'][pid]['pvs']['state'], 'NOT_APPLICABLE')
        self.base['law'] = None
        model, _ = interventions.generate(self.base, self.design)
        result = registry.evaluate(model)
        self.assertTrue(result['verification']['valid'])
        for policy in result['canonical_results']['policies'].values():
            self.assertIsNone(policy['task_probability']['value'])

    def test_closed_relation_failed_setup_and_disconnection_are_causal(self):
        # A closed relation cannot transfer even when resources are available.
        self.design['interventions'][0]['operations'] = [dict(operation='transfer', relation='pipe', at=[1], amounts=['2/1'])]
        model, _ = interventions.generate(self.base, self.design)
        rows = compute_trajectories(model)['intervention.redistribute.1']['demand']['daily']
        self.assertFalse(rows[1]['action_executed'])
        self.assertEqual(rows[1]['stocks']['source'], '4/1')
        # Opening without paying its declared cost must not enable the relation.
        self.design = interventions.example()['design']
        self.base['stocks'][2]['initial'] = '0/1'
        model, _ = interventions.generate(self.base, self.design)
        rows = compute_trajectories(model)['intervention.redistribute.2']['demand']['daily']
        self.assertFalse(rows[1]['action_executed'])
        self.assertFalse(rows[2]['action_executed'])
        self.assertNotIn('relation.pipe', rows[2]['capabilities'])
        # Closing is an action in the trajectory, not a reset of initial state.
        self.base = interventions.example()['model']
        self.design['relations'][0]['initially_open'] = True
        self.design['interventions'][0]['operations'] = [dict(operation='disconnect',relation='pipe',at=[1]),
            dict(operation='transfer',relation='pipe',at=[2],amounts=['2/1'])]
        model, _ = interventions.generate(self.base, self.design)
        rows = compute_trajectories(model)['intervention.redistribute.1']['demand']['daily']
        self.assertIn('relation.pipe', rows[0]['capabilities'])
        self.assertNotIn('relation.pipe', rows[1]['capabilities'])
        self.assertFalse(rows[2]['action_executed'])

    def test_costs_sum_with_transfer_and_destination_spill_is_accounted(self):
        r = self.design['relations'][0]
        r.update(initially_open=True, transfer_costs={'source':'1/1'})
        self.base['stocks'][1]['capacity'] = '2/1'
        self.design['interventions'][0]['operations'] = [dict(operation='transfer',relation='pipe',at=[1],amounts=['2/1'])]
        model, _ = interventions.generate(self.base, self.design)
        row = compute_trajectories(model)['intervention.redistribute.1']['demand']['daily'][1]
        self.assertEqual(row['stocks']['source'], '1/1')
        self.assertEqual(row['ledger']['target']['spill'], '2/1')
        self.assertEqual(row['stocks']['target'], '1/1')

    def test_finite_time_choices_existing_actions_and_no_silent_pruning(self):
        self.design['relations'] = []
        self.design['interventions'][0]['default_action'] = None
        self.design['interventions'][0]['operations'] = [dict(operation='use_action',action='wait',at=[1,2,3])]
        model, receipt = interventions.generate(self.base, self.design)
        self.assertEqual(receipt['generated_count'],3)
        self.assertEqual(len(model['policies']),4)
        self.design['interventions'][0]['operations'].append(dict(operation='use_action',action='wait',at=[3]))
        with self.assertRaisesRegex(ValueError,'two operations'):
            interventions.generate(self.base,self.design)
        self.design = interventions.example()['design']
        self.design['interventions'][0]['operations'][1].update(at=[2,3], amounts=['1/1','2/1','3/1'])
        with self.assertRaisesRegex(ValueError,'no alternatives were truncated'):
            interventions.generate(self.base,self.design)

    def test_invalid_designs_never_mutate_model(self):
        base, design = deepcopy(self.base), deepcopy(self.design)
        changes = [lambda d: d['relations'][0].update(target='time'),
            lambda d: d['relations'][0].update(target='source'),
            lambda d: d['relations'][0].update(open_costs={'unknown':'1/1'}),
            lambda d: d['relations'][0].update(requires=['not_declared']),
            lambda d: d['interventions'][0]['operations'][1].update(amounts=['0/1']),
            lambda d: d['interventions'][0]['operations'][1].update(amounts=['2/2']),
            lambda d: d['interventions'][0]['operations'][1].update(amounts=[1.5]),
            lambda d: d['interventions'][0]['operations'][1].update(at=[4]),
            lambda d: d['interventions'][0]['operations'][1].update(relation='missing'),
            lambda d: d.update(law={'demand':'1/1'}),
            lambda d: d['relations'].append(deepcopy(d['relations'][0]))]
        for change in changes:
            with self.subTest(change=change):
                candidate = deepcopy(design); change(candidate)
                with self.assertRaises(ValueError): interventions.generate(base,candidate)
                self.assertEqual(base,self.base)

    def test_http_proposal_confirmation_export_and_restore(self):
        with tempfile.TemporaryDirectory() as directory:
            app = create_app(Path(directory)/'twins.sqlite3', testing=True, evaluator=registry.evaluate)
            c = app.test_client()
            self.assertEqual(c.get('/api/interventions/schema').json['title'], interventions.FORMAT)
            self.assertEqual(c.get('/api/interventions/example').json['design'],self.design)
            cid = c.post('/api/cases',json={'text':'Ejemplo sintético','profile':registry.STOCKFLOW}).json['case']['id']
            def propose(base, kind, structured):
                return c.post(f'/api/cases/{cid}/proposals',json=dict(base_version=base,kind=kind,text='Diseño explícito',structured=structured))
            def accept(pid, base):
                return c.post('/api/proposals/'+pid+'/accept',json=dict(base_version=base,confirmed=True,acknowledge_declared=True,idempotency_key='accept-version-'+str(base)))
            pid = propose(0,'declared_model',{'model':self.base}).json['proposal']['id']
            self.assertEqual(accept(pid,0).status_code,200)
            response = propose(1,'intervention_design',{'design':self.design})
            self.assertEqual(response.status_code,201,response.json)
            pid=response.json['proposal']['id']
            state=c.get('/api/cases/'+cid).json
            self.assertEqual(state['case']['current_version'],1)
            self.assertEqual(state['jobs'],[])
            accepted=accept(pid,1)
            self.assertEqual(accepted.status_code,200,accepted.json)
            frozen=accepted.json['version']
            self.assertEqual(frozen['metadata']['intervention_design']['model_sha256'],frozen['model_sha256'])
            result=c.post(f'/api/cases/{cid}/evaluate',json={'version':2}).json
            self.assertEqual(result['job']['status'],'completed',result)
            self.assertEqual(result['evaluation']['intervention_design']['generated_count'],2)
            self.assertEqual(propose(1,'intervention_design',{'design':self.design}).status_code,409)
            # Manual edits cannot carry a generation receipt for a different model.
            changed=deepcopy(frozen['model']);changed['name']='Modified hypothesis'
            pid=propose(2,'declared_model',{'model':changed}).json['proposal']['id']
            self.assertNotIn('intervention_design',accept(pid,2).json['version']['metadata'])
            pid=propose(3,'restore',{'version':2}).json['proposal']['id']
            restored=accept(pid,3).json['version']
            self.assertEqual(restored['metadata']['intervention_design'],frozen['metadata']['intervention_design'])
            exported=c.get(f'/api/cases/{cid}/export').json
            self.assertEqual(exported['dossier']['evaluations'][0]['evaluation'],result['evaluation'])
            self.assertEqual(c.delete('/api/cases/'+cid,json={'base_version':4}).status_code,200)


if __name__ == '__main__':
    unittest.main()
