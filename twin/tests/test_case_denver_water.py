"""Denver Water 2026/27 drought case: cited construction and native kernel result stay reproducible."""
import json
from pathlib import Path
import unittest

from genius_twin import construction, registry, stockflow

CASE = Path(__file__).parents[1] / 'cases' / 'denver_water_2026' / 'world.json'


class DenverWaterCaseTests(unittest.TestCase):
    def test_cited_construction_and_kernel_result(self):
        world = json.loads(CASE.read_text())
        result = construction.prepare(world['construction'], dict(id='observation', revision=1, observation=world['observation'], historical_gaps={}))
        self.assertEqual(result['status'], 'READY_FOR_REVIEW')
        model = result['model']
        traces = stockflow.compute_trajectories(model)
        self.assertEqual(traces['keep_ban']['dry']['daily'][6]['stocks']['storage'], '58/1')
        self.assertEqual(traces['resume_may']['dry']['daily'][-1]['stocks']['storage'], '42/1')
        decision = registry.evaluate(model)['canonical_results']['decision']
        self.assertEqual(decision['feasible'], ['keep_ban', 'resume_if_70', 'resume_may'])
        self.assertEqual(decision['failed'], [])
        self.assertIsNone(decision['selected'])
        results = registry.evaluate(model)['canonical_results']
        # A year of winter use (21.5 %) is never broken, so PVS is 1 whatever the law; watering trades reserve for gardens.
        self.assertTrue(all(results['policies'][p]['pvs']['law_range']['law_invariant'] for p in results['policies']))
        dry = {(x['left'], x['right']): x['relation'] for x in decision['wellbeing_comparison']['by_scenario']['dry']}
        self.assertEqual(dry[('keep_ban', 'resume_if_70')], 'EQUIVALENT')
        self.assertEqual(dry[('keep_ban', 'resume_may')], 'INCOMPARABLE')
        self.assertEqual(results['policies']['resume_may']['by_scenario']['dry']['wellbeing'][1]['worst'], '42/1')


if __name__ == '__main__':
    unittest.main()
