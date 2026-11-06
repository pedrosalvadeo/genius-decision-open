"""Territory (AM-06): one template evaluated zone by zone, compared zone by zone, without sums."""
from copy import deepcopy
from fractions import Fraction
import json
from pathlib import Path
import unittest

from genius_twin import territory

CASE = Path(__file__).parents[1] / 'cases' / 'mendoza_arbolado_2027'


def small(zones):
    spec = json.loads((CASE / 'territory.json').read_text())
    spec['zones'] = zones
    return spec


# Hours available follow households; the reference block has 50 trees and 120 households.
RICH = {'id': 'rica', 'label': 'Manzana con muchos vecinos', 'size': '1/1', 'supply': {'horas': '3/2'}, 'provenance': 'prueba'}
POOR = {'id': 'pobre', 'label': 'Manzana con pocos vecinos', 'size': '1/1', 'supply': {'horas': '3/4'}, 'provenance': 'prueba'}
NONE = {'id': 'sin', 'label': 'Manzana fuera del censo', 'missing': 'El censo del arbolado no la cubre', 'provenance': 'prueba'}


class TerritoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = small([RICH, POOR])
        cls.result = territory.evaluate(cls.spec)

    def test_zone_model_scales_exactly_and_supply_only_moves_availability(self):
        template = self.spec['template']
        model = territory.zone_model(template, {'id': 'z', 'label': 'z', 'size': '3/2', 'supply': {'horas': '1/3'}})
        stocks = {s['id']: s for s in model['stocks']}
        self.assertEqual((stocks['tazas']['initial'], stocks['tazas']['capacity']), ('60/1', '120/1'))
        # Renewable hours: availability times size times supply; the capacity follows it.
        self.assertEqual((stocks['horas']['initial'], stocks['horas']['capacity']), ('20/1', '20/1'))
        self.assertEqual(model['scenarios'][0]['events'][0]['renewables']['horas'], '20/1')
        # Demands do not move with supply: watering still needs 30 h per 50 trees, times size.
        riego = next(a for a in model['actions'] if a['id'] == 'riego_comun')
        self.assertEqual(riego['withdrawals'], {'agua': '90/1', 'horas': '45/1'})
        self.assertEqual(model['task']['conditions'][0]['threshold'], '15/1')
        self.assertEqual(model['scenarios'][1]['events'][1]['drains']['tazas'], '90/1')
        # The template is never modified.
        self.assertEqual(next(s for s in template['stocks'] if s['id'] == 'tazas')['initial'], '40/1')

    def test_each_zone_is_verified_by_the_kernel(self):
        for zone in self.result['zones'].values():
            self.assertEqual((zone['verification'], zone['coverage']), ('VALID', 'EXHAUSTIVE'))

    def test_a_zone_that_loses_is_named_and_no_route_wins_by_sum(self):
        zones = self.result['zones']
        # With few neighbours, organizing the padrinos takes hours the block does not have.
        self.assertEqual(zones['rica']['routes']['padrinos']['pvs'], '3/4')
        self.assertEqual(zones['pobre']['routes']['padrinos']['pvs'], '0/1')
        pair = next(p for p in self.result['decision']['pairs'] if (p['left'], p['right']) == ('padrinos', 'hoy'))
        self.assertEqual(pair['by_criterion']['pvs']['worse_in'], ['pobre'])
        # Where organizing fails the block never gains the padrinos network: CAG only grows in the rich block.
        self.assertEqual(pair['by_criterion']['cag']['better_in'], ['rica'])
        self.assertEqual(pair['by_criterion']['cag']['equal_in'], ['pobre'])
        self.assertEqual(pair['weak'], '0')
        self.assertIn('padrinos', self.result['decision']['frontier'])
        self.assertIsNone(self.result['decision']['selected'])

    def test_joint_life_holds_only_where_it_holds_in_every_zone(self):
        for route, row in self.result['by_route'].items():
            for sid, joint in row['joint_life_by_scenario'].items():
                statuses = {z['routes'][route]['task_status'][sid] for z in self.result['zones'].values()}
                expected = 'failure' if 'failure' in statuses else 'undecided' if 'undecided' in statuses else 'success'
                self.assertEqual(joint, expected)
                self.assertEqual(sorted(z for z, v in self.result['zones'].items() if v['routes'][route]['task_status'][sid] == 'failure'),
                                 row['life_fails_in'][sid])
        law = self.spec['template']['law']
        for row in self.result['by_route'].values():
            expected = sum((Fraction(law[s]) for s, v in row['joint_life_by_scenario'].items() if v == 'success'), Fraction())
            self.assertEqual(Fraction(row['joint_pvs']), expected)

    def test_the_territory_order_is_a_preorder(self):
        weak = {(p['left'], p['right']): p['weak'] for p in self.result['decision']['pairs']}
        routes = list(self.result['routes'])
        for a in routes:
            for b in routes:
                for c in routes:
                    if len({a, b, c}) == 3 and weak.get((a, b)) == '1' and weak.get((b, c)) == '1':
                        self.assertEqual(weak.get((a, c)), '1')

    def test_a_zone_without_data_is_never_filled_and_makes_the_result_relative(self):
        result = territory.evaluate(small([RICH, NONE]))
        self.assertNotIn('sin', result['zones'])
        self.assertEqual(result['zones_without_data'], {'sin': 'El censo del arbolado no la cubre'})
        self.assertEqual(result['decision']['coverage'], 'RELATIVE')
        self.assertEqual(result['decision']['relative_to'], 'ZONES_WITH_DATA')
        self.assertIsNone(result['decision']['selected'])

    def test_invalid_territories_are_rejected(self):
        cases = [
            small([RICH, dict(RICH)]),
            small([{**NONE, 'size': '1/1'}]),
            small([{**RICH, 'supply': {'lluvia': '1/1'}}]),
            small([{**RICH, 'size': '0/1'}]),
            small([{k: v for k, v in RICH.items() if k != 'size'}]),
        ]
        with_functions = small([RICH])
        with_functions['template']['functions'] = [{'id': 'f'}]
        cases.append(with_functions)
        for spec in cases:
            with self.assertRaises(ValueError):
                territory.validate(spec)

    def test_frozen_mendoza_result_is_what_the_territory_computes(self):
        spec = json.loads((CASE / 'territory.json').read_text())
        frozen = json.loads((CASE / 'territory_result.json').read_text())
        self.assertEqual(frozen['spec_digest'], territory._digest(spec))
        self.assertEqual(len(frozen['zones']), 60)
        self.assertEqual(json.loads(json.dumps(territory.evaluate(spec))), frozen)


if __name__ == '__main__':
    unittest.main()
