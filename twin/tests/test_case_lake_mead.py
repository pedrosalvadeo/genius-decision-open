"""Lake Mead / Lake Powell water year 2027 case: cited construction reproduces Reclamation's studies and the kernel result."""
import json
from pathlib import Path
import unittest

from genius_twin import construction, registry, stockflow

CASE = Path(__file__).parents[1] / 'cases' / 'lake_mead_2027' / 'world.json'


class LakeMeadCaseTests(unittest.TestCase):
    def test_cited_construction_and_kernel_result(self):
        world = json.loads(CASE.read_text())
        result = construction.prepare(world['construction'], dict(id='observation', revision=1, observation=world['observation'], historical_gaps={}))
        self.assertEqual(result['status'], 'READY_FOR_REVIEW')
        model = result['model']
        traces = stockflow.compute_trajectories(model)

        def path(policy, scenario, lake):
            return [int(state['stocks'][lake].split('/')[0]) for state in traces[policy][scenario]['daily']]
        # The four combinations Reclamation published are reproduced exactly (Mead).
        self.assertEqual(path('release_6', 'most_probable', 'mead')[-6:], [5624, 5227, 4964, 4920, 5055, 5105])
        self.assertEqual(path('release_7', 'most_probable', 'mead')[-6:], [5624, 5397, 5408, 5567, 5918, 6036])
        self.assertEqual(path('release_6', 'minimum', 'powell')[-2:], [4375, 4072])
        self.assertEqual(path('release_7', 'maximum', 'powell')[-1], 11578)
        # In the minimum year Powell drops below 3,510 ft in August with 6 maf and in May with 7 maf.
        self.assertEqual(next(i for i, v in enumerate(path('release_6', 'minimum', 'powell')) if v < 4724), 11)
        self.assertEqual(next(i for i, v in enumerate(path('release_7', 'minimum', 'powell')) if v < 4724), 8)
        self.assertTrue(all(v >= 4478 for p in traces for s in traces[p] for v in path(p, s, 'mead')))
        decision = registry.evaluate(model)['canonical_results']['decision']
        self.assertEqual(decision['feasible'], [])
        self.assertEqual(decision['failed'], ['release_6', 'release_7'])
        self.assertIsNone(decision['selected'])


if __name__ == '__main__':
    unittest.main()
