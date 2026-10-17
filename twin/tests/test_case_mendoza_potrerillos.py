"""Mendoza River / Potrerillos 2026/27 case: cited construction and native kernel result stay reproducible."""
import json
from pathlib import Path
import unittest

from genius_twin import construction, registry, stockflow

CASE = Path(__file__).parents[1] / 'cases' / 'mendoza_potrerillos_2026' / 'world.json'


class MendozaPotrerillosCaseTests(unittest.TestCase):
    def test_cited_construction_and_kernel_result(self):
        world = json.loads(CASE.read_text())
        result = construction.prepare(world['construction'], dict(id='observation', revision=1, observation=world['observation'], historical_gaps={}))
        self.assertEqual(result['status'], 'READY_FOR_REVIEW')
        model = result['model']
        traces = stockflow.compute_trajectories(model)
        self.assertEqual(traces['dry_allocation']['forecast']['totals']['spilled']['potrerillos'], '1537/2')
        self.assertFalse(traces['reinforced']['like_2025']['daily'][7]['action_executed'])
        decision = registry.evaluate(model)['canonical_results']['decision']
        self.assertEqual(decision['feasible'], ['dry_allocation', 'reinforced', 'reinforced_lagoons'])
        self.assertEqual(decision['failed'], [])
        self.assertIsNone(decision['selected'])
        results = registry.evaluate(model)['canonical_results']
        # A month of drinking water is kept in every scenario; reinforced irrigation trades reserve for irrigation.
        self.assertTrue(all(results['policies'][p]['pvs']['value'] == '1/1' for p in results['policies']))
        like_2025 = {(x['left'], x['right']): x['relation'] for x in decision['wellbeing_comparison']['by_scenario']['like_2025']}
        self.assertEqual(like_2025[('reinforced', 'reinforced_lagoons')], 'EQUIVALENT')
        self.assertEqual(like_2025[('dry_allocation', 'reinforced')], 'INCOMPARABLE')


if __name__ == '__main__':
    unittest.main()
