"""Lake Mead / Lake Powell over water years 2027-2028 (monthly, then quarterly) from Reclamation's October 2026 studies, with hydropower that follows Powell."""
import json
from pathlib import Path
import unittest

from genius_twin import construction, registry, stockflow

CASE = Path(__file__).parents[1] / 'cases' / 'lake_mead_2028' / 'world.json'


class LakeMead2028CaseTests(unittest.TestCase):
    def test_two_years_hydropower_and_functions(self):
        world = json.loads(CASE.read_text())
        result = construction.prepare(world['construction'], dict(id='observation', revision=1, observation=world['observation'], historical_gaps={}))
        self.assertEqual(result['status'], 'READY_FOR_REVIEW')
        model = result['model']
        self.assertEqual(model['horizon'], 16)
        traces = stockflow.compute_trajectories(model)

        def path(policy, scenario, lake):
            return [int(state['stocks'][lake].split('/')[0]) for state in traces[policy][scenario]['daily']]
        # Three published combinations are reproduced exactly at each quarter end of 2028.
        self.assertEqual(path('release_6', 'most_probable', 'mead')[-4:], [5310, 5827, 5016, 5344])
        self.assertEqual(path('release_6', 'minimum', 'mead')[-4:], [4660, 4202, 3586, 3707])
        self.assertEqual(path('release_7', 'maximum', 'powell')[-1], 11749)
        # Hydropower follows Powell: with 7 maf and minimum inflow it stops in August 2027 and is back by June 2028.
        power = {(p, s): ''.join('1' if 'glen_power' in row['capabilities'] else '0' for row in traces[p][s]['daily'])
                 for p in traces for s in traces[p]}
        self.assertEqual(power[('release_7', 'minimum')], '1' * 11 + '0' * 4 + '1' * 2)
        self.assertEqual({k for k, v in power.items() if '0' in v}, {('release_7', 'minimum')})
        results = registry.evaluate(model)['canonical_results']
        decision = results['decision']
        self.assertEqual(decision['feasible'], ['release_6', 'release_7'])
        self.assertEqual(decision['frontier'], ['release_6', 'release_7'])
        for policy in ('release_6', 'release_7'):
            self.assertEqual(results['policies'][policy]['pvs']['value'], '1/1')
            # The kernel's CAG always contains the origin organization, so losing power does not change it.
            self.assertEqual(results['policies'][policy]['cag']['robust'], [results['policies'][policy]['cag']['origin']])
        # Module I separates them in the minimum inflow: 6 maf keeps power in all 17 states and Mead at 1,000 ft in 14;
        # 7 maf keeps power in 13 and Mead at 1,000 ft in 15.
        terminal = {p: {row['function']: row['terminal'] for row in results['policies'][p]['functional']['by_scenario']['minimum']} for p in ('release_6', 'release_7')}
        self.assertEqual(terminal, {'release_6': {'glen_canyon_3510': '12/1', 'glen_generating': '17/1', 'mead_1000': '14/1'},
                                    'release_7': {'glen_canyon_3510': '9/1', 'glen_generating': '13/1', 'mead_1000': '15/1'}})
        self.assertEqual(decision['functional_comparison']['all_scenarios'],
                         [{'left': 'release_6', 'right': 'release_7', 'relation': 'INCOMPARABLE',
                           'better_on': ['glen_canyon_3510', 'glen_generating'], 'worse_on': ['mead_1000']}])
        # Over two years neither route is best for any one actor on all its own coordinates.
        self.assertEqual({c: row['status'] for c, row in decision['by_actor']['by_carrier'].items()},
                         {'lower_basin': 'TIED_OR_INCOMPARABLE', 'glen_canyon': 'TIED_OR_INCOMPARABLE'})
        flows = results['policies']['release_7']['composition']['interfaces_by_scenario']['most_probable']
        self.assertEqual({row['interface']: row['total'] for row in flows}, {'glen_release': '931/1', 'release_withheld_2028': '947/1'})
        self.assertTrue(results['modules']['complete'])


if __name__ == '__main__':
    unittest.main()
