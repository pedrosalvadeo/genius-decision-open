"""Twin of twins: Denver and Lake Mead/Powell composed in the Colorado basin."""
from copy import deepcopy
import json
from pathlib import Path
import unittest

from genius_twin import federation

SPEC = Path(__file__).parents[1] / 'cases' / 'colorado_basin_2027' / 'federation.json'


class ColoradoBasinFederationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = json.loads(SPEC.read_text())
        cls.result = federation.evaluate(cls.spec)

    def test_members_keep_their_eight_modules_and_the_coupling_reaches_powell(self):
        result = self.result
        for member in result['members'].values():
            self.assertEqual(set(member['modules'].values()), {'FILLED'})
        variants = {tuple(v['key']): v for v in result['members']['mead']['coupled_variants']}
        self.assertEqual(set(variants), {('keep_ban',), ('resume_may',), ('resume_if_70',)})
        # Resuming in May waters 10 points; half of 5.67906 kaf per point leaves Powell.
        self.assertEqual(variants[('resume_may',)]['coupled_totals']['west_slope_diversion'],
                         {'dry': '283953/10000', 'normal': '283953/10000', 'wet': '283953/10000'})
        self.assertEqual(variants[('keep_ban',)]['coupled_totals']['west_slope_diversion']['dry'], '0/1')

    def test_joint_pvs_and_a_cross_twin_tradeoff(self):
        rows = self.result['by_joint_route']
        self.assertEqual(len(rows), 6)
        for row in rows.values():
            self.assertEqual(row['joint_pvs'], '1/1')
            self.assertEqual(row['joint_pvs_law_range'], {'min': '1/1', 'max': '1/1', 'law_invariant': True})
        pair = next(p for p in self.result['decision']['pairs']
                    if p['left'] == 'denver:keep_ban+mead:release_6' and p['right'] == 'denver:resume_may+mead:release_6')
        # Denver's garden water is paid for in Lake Powell: Glen Canyon is better off when Denver keeps the ban.
        self.assertEqual(pair['relation'], 'INCOMPARABLE')
        self.assertIn({'criterion': 'welfare', 'who': 'mead.glen_canyon'}, pair['better_for'])
        self.assertEqual(pair['worse_for'], [{'criterion': 'welfare', 'who': 'denver.residents'}])
        self.assertEqual(len(self.result['decision']['frontier']), 6)
        # Per actor, Denver's choice reaches Glen Canyon: only keeping the ban with 6 maf is best for it.
        self.assertEqual(self.result['decision']['by_actor']['mead.glen_canyon'],
                         {'best': ['denver:keep_ban+mead:release_6'], 'status': 'UNIQUE'})
        self.assertIsNone(self.result['decision']['selected'])

    def test_invalid_alignment_and_cycles_are_rejected(self):
        bad = deepcopy(self.spec)
        bad['scenarios'][1]['members']['mead'] = 'minimum'
        with self.assertRaises(ValueError):
            federation.evaluate(bad)
        bad = deepcopy(self.spec)
        bad['law'] = {'dry': '1/2', 'normal': '1/2', 'wet': '1/2'}
        with self.assertRaises(ValueError):
            federation.evaluate(bad)
        bad = deepcopy(self.spec)
        bad['couplings'][0]['source']['interface'] = 'missing'
        with self.assertRaises(ValueError):
            federation.evaluate(bad)


if __name__ == '__main__':
    unittest.main()
