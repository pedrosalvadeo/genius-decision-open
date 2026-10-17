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
        self.assertEqual(traces['dry_allocation']['forecast']['totals']['spilled']['potrerillos'], '1687/2')
        self.assertEqual(traces['reinforced']['like_2025']['daily'][-1]['stocks']['potrerillos'], '47/4')
        decision = registry.evaluate(model)['canonical_results']['decision']
        self.assertEqual(decision['feasible'], ['dry_allocation'])
        self.assertEqual(decision['failed'], ['reinforced', 'reinforced_lagoons'])
        self.assertIsNone(decision['selected'])


if __name__ == '__main__':
    unittest.main()
