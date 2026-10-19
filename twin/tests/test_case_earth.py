"""A first digital twin of the Earth, 2025-2105: the same modules and kernel at planetary scale."""
import json
from pathlib import Path
import unittest

from genius_twin import construction, registry

CASE = Path(__file__).parents[1] / 'cases' / 'earth_2105' / 'world.json'


class EarthCaseTests(unittest.TestCase):
    def test_cited_construction_and_kernel_result(self):
        world = json.loads(CASE.read_text())
        result = construction.prepare(world['construction'], dict(id='observation', revision=1, observation=world['observation'], historical_gaps={}))
        self.assertEqual(result['status'], 'READY_FOR_REVIEW', result['questions'])
        results = registry.evaluate(result['model'])['canonical_results']
        policies = results['policies']
        self.assertEqual({p: policies[p]['pvs']['value'] for p in policies},
                         {'fast': '1/1', 'medium': '2/3', 'slow': '1/3', 'current_policies': '0/1'})
        self.assertEqual(policies['current_policies']['pvs']['law_range'], {'min': '0/1', 'max': '0/1', 'law_invariant': True})
        self.assertEqual(policies['fast']['pvs']['law_range'], {'min': '1/1', 'max': '1/1', 'law_invariant': True})
        self.assertEqual(results['decision']['failed'], ['current_policies', 'medium', 'slow'])
        self.assertEqual({m['module']: m['status'] for m in results['modules']['modules']}, dict.fromkeys(['0', 'V', 'I', 'II', 'III', 'IV', 'VI', 'VII'], 'FILLED'))


if __name__ == '__main__':
    unittest.main()
