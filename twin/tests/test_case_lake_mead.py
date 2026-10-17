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
        results = registry.evaluate(model)['canonical_results']
        decision = results['decision']
        # Life condition (Mead above its dead pool) holds with both releases in every inflow, so PVS is 1 under
        # the declared law and under every other law; welfare separates them without a winner.
        self.assertEqual(decision['feasible'], ['release_6', 'release_7'])
        self.assertEqual(decision['frontier'], ['release_6', 'release_7'])
        self.assertIsNone(decision['selected'])
        self.assertEqual(results['native_integration']['state'], 'DEFINED')
        for policy in ('release_6', 'release_7'):
            self.assertEqual(results['policies'][policy]['pvs']['value'], '1/1')
            self.assertEqual(results['policies'][policy]['pvs']['law_range'], {'min': '1/1', 'max': '1/1', 'law_invariant': True})
            self.assertEqual({s: row['pvs_given_scenario'] for s, row in results['policies'][policy]['by_scenario'].items()},
                             {'minimum': '1', 'most_probable': '1', 'maximum': '1'})
        # In every inflow 7 maf is better for the lower basin (Mead) and worse for Glen Canyon (Powell).
        for pairs in decision['wellbeing_comparison']['by_scenario'].values():
            self.assertEqual(pairs, [{'left': 'release_6', 'right': 'release_7', 'relation': 'INCOMPARABLE',
                                      'better_for': [{'carrier': 'glen_canyon', 'dimension': 'powell_reserve'}],
                                      'worse_for': [{'carrier': 'lower_basin', 'dimension': 'mead_reserve'}]}])
        minimum = results['policies']['release_7']['by_scenario']['minimum']['wellbeing']
        self.assertEqual([(row['dimension'], row['worst']) for row in minimum], [('mead_reserve', '5207/1'), ('powell_reserve', '3141/1')])
        # Module I on each projected twin: in the minimum year Glen Canyon keeps 3,510 ft for 11 months with 6 maf and 8 with 7 maf,
        # so 6 maf is functionally at least as good everywhere; welfare still keeps both options on the frontier.
        for policy, months in (('release_6', 11), ('release_7', 8)):
            functional = results['policies'][policy]['functional']
            self.assertEqual(functional['native_cell']['state'], 'DEFINED')
            self.assertEqual([(row['function'], row['terminal']) for row in functional['by_scenario']['minimum']],
                             [('glen_canyon_3510', f'{months}/1'), ('mead_1000', '13/1')])
        self.assertEqual(decision['functional_comparison']['all_scenarios'],
                         [{'left': 'release_6', 'right': 'release_7', 'relation': 'DOMINATES', 'better_on': ['glen_canyon_3510'], 'worse_on': []}])
        ledger = {row['module']: row['status'] for row in results['modules']['modules']}
        self.assertEqual(ledger, {'0': 'FILLED', 'V': 'FILLED', 'I': 'FILLED', 'II': 'FILLED', 'III': 'FILLED',
                                  'IV': 'FILLED', 'VI': 'FILLED', 'VII': 'FILLED'})
        self.assertTrue(results['modules']['complete'])
        # Module VII per actor: the lower basin is best served by 7 maf, Glen Canyon by 6 maf.
        self.assertEqual({c: row['best'] for c, row in decision['by_actor']['by_carrier'].items()},
                         {'lower_basin': ['release_7'], 'glen_canyon': ['release_6']})
        # Module II: Powell and Mead are subsystems joined by the release; 7 maf carries 931 kaf more, May to September.
        for policy, total in (('release_6', '0/1'), ('release_7', '931/1')):
            composition = results['policies'][policy]['composition']
            self.assertEqual(composition['native_cell_state'], 'DEFINED')
            self.assertEqual({s: [row['total'] for row in rows] for s, rows in composition['interfaces_by_scenario'].items()},
                             {'minimum': [total], 'most_probable': [total], 'maximum': [total]})

if __name__ == '__main__':
    unittest.main()
