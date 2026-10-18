"""US type O blood supply, winter 2026/27: the first cited case outside water uses the same modules and kernel."""
import json
from pathlib import Path
import unittest

from genius_twin import construction, registry, stockflow

CASE = Path(__file__).parents[1] / 'cases' / 'us_blood_2026' / 'world.json'


class UsBloodCaseTests(unittest.TestCase):
    def test_cited_construction_and_kernel_result(self):
        world = json.loads(CASE.read_text())
        result = construction.prepare(world['construction'], dict(id='observation', revision=1, observation=world['observation'], historical_gaps={}))
        self.assertEqual(result['status'], 'READY_FOR_REVIEW')
        model = result['model']
        traces = stockflow.compute_trajectories(model)
        self.assertEqual(traces['as_usual']['severe']['daily'][8]['stocks']['inventory'], '117/20')
        results = registry.evaluate(model)['canonical_results']
        decision = results['decision']
        self.assertEqual(decision['failed'], ['as_usual'])
        self.assertEqual(decision['frontier'], ['campaign', 'campaign_and_defer', 'defer_below_two_days'])
        self.assertIsNone(decision['selected'])
        self.assertEqual(results['policies']['as_usual']['pvs']['value'], '2/3')
        self.assertEqual(results['policies']['as_usual']['pvs']['law_range'], {'min': '0/1', 'max': '1/1', 'law_invariant': False})
        self.assertTrue(all(results['policies'][p]['pvs']['value'] == '1/1' for p in ('campaign', 'campaign_and_defer', 'defer_below_two_days')))
        actors = decision['by_actor']['by_carrier']
        self.assertEqual(actors['donors']['best'], ['defer_below_two_days'])
        self.assertEqual(actors['surgical_patients']['best'], ['campaign', 'campaign_and_defer'])
        self.assertEqual({m['module']: m['status'] for m in results['modules']['modules']}, dict.fromkeys(['0', 'V', 'I', 'II', 'III', 'IV', 'VI', 'VII'], 'FILLED'))
        self.assertEqual({f['kind'] for f in model['functions']}, {'health', 'safety'})


if __name__ == '__main__':
    unittest.main()
