"""AM-07 declared unit conversions and partial observation (MV, AM-01) in STOCK_FLOW_FINITE_V1."""
from copy import deepcopy
import json
from pathlib import Path
import unittest

from genius_twin import registry
from genius_twin.stockflow import unit_classes

CASE = Path(__file__).parents[1] / 'cases' / 'mendoza_arbolado_2027' / 'territory.json'


def template():
    return deepcopy(json.loads(CASE.read_text())['template'])


def in_litres(model):
    """The same model with the irrigation turn counted in litres instead of m3."""
    for stock in model['stocks']:
        if stock['id'] == 'agua':
            stock.update(unit='l', initial='100000/1', capacity='100000/1')
    for action in model['actions']:
        if 'agua' in action['withdrawals']:
            n = int(action['withdrawals']['agua'].split('/')[0])
            action['withdrawals']['agua'] = f'{n * 1000}/1'
    for scenario in model['scenarios']:
        for event in scenario['events']:
            n = int(event['renewables']['agua'].split('/')[0])
            event['renewables']['agua'] = f'{n * 1000}/1'
    for binding in model['welfare']:
        if binding['stock'] == 'agua':
            binding['dimension'] = 'agua_sobrante_litros'
    return model


class UnitConversionTests(unittest.TestCase):
    def test_without_a_declared_conversion_litres_never_pay_for_m3(self):
        with self.assertRaisesRegex(ValueError, 'deposits exceed withdrawals'):
            registry.validate(in_litres(template()))

    def test_a_declared_exact_conversion_keeps_every_result(self):
        base = registry.evaluate(template())['canonical_results']
        model = in_litres(template())
        model['conversions'] = [{'from': 'm3', 'to': 'l', 'factor': '1000/1', 'provenance': 'Sistema Internacional'}]
        out = registry.evaluate(model)
        self.assertEqual(out['verification']['status'], 'VALID')
        result = out['canonical_results']
        for pid, row in base['policies'].items():
            self.assertEqual(result['policies'][pid]['pvs']['value'], row['pvs']['value'])
            self.assertEqual(result['policies'][pid]['viability']['all_scenarios'], row['viability']['all_scenarios'])
            self.assertEqual({k: v['task_status'] for k, v in result['policies'][pid]['by_scenario'].items()},
                             {k: v['task_status'] for k, v in row['by_scenario'].items()})
        self.assertEqual(result['decision']['frontier'], base['decision']['frontier'])
        # Stocks keep their own unit; the conversion never rewrites a balance.
        self.assertEqual(next(s for s in result['stocks'] if s['id'] == 'agua')['unit'], 'l')

    def test_classes_are_exact_and_inconsistent_cycles_are_rejected(self):
        model = {'stocks': [{'unit': 'm3'}, {'unit': 'l'}], 'conversions': [
            {'from': 'm3', 'to': 'l', 'factor': '1000/1'}, {'from': 'l', 'to': 'ml', 'factor': '1000/1'}]}
        classes = unit_classes(model)
        self.assertEqual({u for u, _ in classes.values()}, {'l'})
        self.assertEqual(classes['m3'][1] / classes['ml'][1], 1000000)
        model['conversions'].append({'from': 'ml', 'to': 'm3', 'factor': '1/1000'})
        with self.assertRaisesRegex(ValueError, 'cycle'):
            unit_classes(model)
        for bad in ({'from': 'l', 'to': 'l', 'factor': '1/1'}, {'from': 'l', 'to': 'kl', 'factor': '0/1'}):
            with self.assertRaises(ValueError):
                unit_classes({'stocks': [], 'conversions': [bad]})
        with self.assertRaisesRegex(ValueError, 'twice'):
            unit_classes({'stocks': [], 'conversions': [{'from': 'a', 'to': 'b', 'factor': '2/1'}, {'from': 'b', 'to': 'a', 'factor': '1/2'}]})


class PartialObservationTests(unittest.TestCase):
    def model(self):
        model = template()
        # The neighbours see their own hours and whether the networks exist, not the water in the basins.
        model['observable'] = {'stocks': ['horas'], 'capabilities': ['cuadrilla', 'padrinos']}
        model['policies'].append({'id': 'mirar', 'label': 'Regar con padrinos sólo si la red existe', 'default_action': 'riego_comun',
                                  'rules': [{'steps': [1], 'when': [], 'action': 'organizar'},
                                            {'steps': [2, 3, 4], 'when': [{'kind': 'capability', 'capability': 'padrinos', 'present': True}],
                                             'action': 'riego_padrinos'}]})
        return model

    def test_a_rule_cannot_read_what_is_not_observed(self):
        model = self.model()
        model['policies'][-1]['rules'][1]['when'] = [{'kind': 'stock', 'stock': 'tazas', 'op': 'le', 'value': '20/1'}]
        with self.assertRaisesRegex(ValueError, 'not observable'):
            registry.validate(model)
        model = self.model()
        model['observable']['stocks'] = ['lluvia']
        with self.assertRaises(ValueError):
            registry.validate(model)

    def test_information_is_what_was_observed_and_the_kernel_verifies_it(self):
        model = self.model()
        unobserved = deepcopy(model)
        del unobserved['observable']
        full = registry.evaluate(unobserved)
        out = registry.evaluate(model)
        self.assertEqual(out['verification']['status'], 'VALID')
        self.assertEqual(out['canonical_results']['decision']['coverage'], 'EXHAUSTIVE')
        native = json.loads(out['native_input_json'])['model']
        # Branches whose basins differ but look the same to the neighbours share one information.
        self.assertLess(len(native['information']), len(json.loads(full['native_input_json'])['model']['information']))
        self.assertEqual({k: v['pvs']['value'] for k, v in out['canonical_results']['policies'].items()},
                         {k: v['pvs']['value'] for k, v in full['canonical_results']['policies'].items()})
        self.assertTrue(all(y.startswith('obs_') for y in native['observations']))
        self.assertEqual({u['y'] for u in native['updates']}, set(native['observations']))

    def test_without_declared_observation_nothing_changes(self):
        model = template()
        native = json.loads(registry.evaluate(model)['native_input_json'])['model']
        self.assertTrue(all(y.startswith('event_') for y in native['observations']))


if __name__ == '__main__':
    unittest.main()
