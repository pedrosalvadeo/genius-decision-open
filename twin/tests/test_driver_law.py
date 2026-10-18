"""Empirical scenario law from any exogenous driver series (Module VI in any domain)."""
import csv
from fractions import Fraction
import json
from pathlib import Path
import tempfile
import unittest

from genius_twin import driver_law, registry
from genius_twin.app import create_app

SNOW = Path(__file__).parents[1] / 'history' / 'denver_snow'


def denver():
    rows = list(csv.DictReader((SNOW / 'april1.csv').open()))
    series = [dict(period=r['year'], value=str(Fraction(r['swe_sum_in']) / Fraction(r['median_sum_in']))) for r in rows]
    return series, {'dry': series[-1]['value'], 'normal': '1', 'wet': '3/2'}


class DriverLawTests(unittest.TestCase):
    def test_reproduces_the_admitted_denver_law(self):
        series, anchors = denver()
        result = driver_law.certificate(series, anchors, tie='normal', driver='april1_snow_index')
        saved = json.loads((SNOW / 'law_certificate.json').read_text())
        self.assertTrue(result['admitted'])
        self.assertEqual(result['law'], saved['law'])
        self.assertEqual(result['evaluation']['candidates']['frequency']['mean_log_score'],
                         saved['evaluation']['candidates']['frequency']['mean_log_score'])
        self.assertEqual((result['followed'], result['periods_offered'], result['window']), ({'dry': 3, 'normal': 23, 'wet': 4}, 36, 30))

    def test_any_domain_and_refusals(self):
        # Weekly hospital admissions against three epidemic scenarios: too few weeks to admit.
        series = [dict(period=f'2025-W{w:02d}', value=str(v)) for w, v in enumerate([40, 55, 90, 140, 120, 60, 45, 50], 1)]
        result = driver_law.certificate(series, {'low': '50', 'medium': '100', 'high': '150'}, driver='weekly_admissions')
        self.assertFalse(result['admitted'])
        self.assertIn('INSUFFICIENT_EVIDENCE: 8 independent outcomes, 30 required', result['refusals'])
        self.assertEqual([c['scenario'] for c in result['classification']], ['low', 'low', 'medium', 'high', 'medium', 'low', 'low', 'low'])
        self.assertEqual(sum(Fraction(v) for v in result['law'].values()), 1)
        for anchors in ({'only': '1'}, {'a': '1', 'b': '1/1'}, {'a': 'x', 'b': '2'}):
            with self.assertRaises(ValueError):
                driver_law.certificate(series, anchors)
        with self.assertRaises(ValueError):
            driver_law.certificate(series + series[:1], {'a': '1', 'b': '2'})

    def test_powell_law_is_frozen(self):
        # The Mead law: 30 recent water years admit thirds; the whole record admits a wetter frequency law.
        import importlib.util
        spec = importlib.util.spec_from_file_location('powell_law', Path(__file__).resolve().parents[1] / 'history' / 'powell_law.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        result = module.certificates()
        saved = json.loads((Path(__file__).resolve().parents[1] / 'history' / 'lake_mead' / 'powell_law_wy2027.json').read_text())
        self.assertEqual(json.loads(json.dumps(result, sort_keys=True)), saved)
        self.assertEqual(result['whole_record']['anchors'], {'minimum': '4070000', 'most_probable': '7800000', 'maximum': '15099000'})
        self.assertEqual((result['last_30_years']['law'], result['last_30_years']['admitted']), ({'minimum': '1/3', 'most_probable': '1/3', 'maximum': '1/3'}, True))
        self.assertEqual((result['whole_record']['law'], result['whole_record']['outcomes']), ({'minimum': '12/65', 'most_probable': '27/65', 'maximum': '2/5'}, 62))

    def test_joint_law_of_two_drivers(self):
        # Proposed AM-02.1: scenarios defined by two drivers; independence is one candidate among three.
        years = [str(1990 + i) for i in range(32)]
        a = [dict(period=y, value=str(i % 2)) for i, y in enumerate(years)]
        b = [dict(period=y, value=str((i // 2) % 2)) for i, y in enumerate(years)] + [dict(period='1800', value='0')]
        drivers = [dict(name='a', series=a, anchors={'low': '0', 'high': '1'}), dict(name='b', series=b, anchors={'low': '0', 'high': '1'})]
        mixed = dict(cells=[['low', 'high'], ['high', 'low']], representative=['low', 'high'])
        scenarios = {'both_low': [['low', 'low']], 'mixed': mixed, 'both_high': [['high', 'high']]}
        result = driver_law.joint_certificate(drivers, scenarios)
        self.assertEqual((result['periods_offered'], result['outcomes'], result['followed']), (32, 30, {'both_low': 7, 'mixed': 15, 'both_high': 8}))
        self.assertEqual(result['classification'][0], {'period': '1992', 'cell': ['low', 'high'], 'scenario': 'mixed'})
        self.assertTrue(result['admitted'])
        self.assertEqual(set(result['evaluation']['candidates']), {'uniform', 'frequency', 'independent_drivers'})
        self.assertEqual(result['representatives']['mixed'], ['low', 'high'])
        # Independent recomputation: product of (k+1)/(n+2) marginals of the earlier periods.
        cells = [tuple(c['cell']) for c in result['classification']]
        def mixed_mass(i):
            pa = Fraction(sum(c[0] == 'low' for c in cells[:i]) + 1, i + 2)
            pb = Fraction(sum(c[1] == 'low' for c in cells[:i]) + 1, i + 2)
            return pa * (1 - pb) + (1 - pa) * pb
        self.assertEqual(mixed_mass(0), Fraction(1, 2))
        expected = round(float(sum(mixed_mass(i) for i in range(30)) / 30), 4)
        self.assertEqual(result['evaluation']['candidates']['independent_drivers']['bands']['mixed']['mean_mass'], expected)
        self.assertEqual(result['periods_without_every_driver'], ['1800'])
        for bad, message in ((dict(scenarios, mixed=[['low', 'high']]), 'without a scenario'),
                             (dict(scenarios, both_high=[['high', 'high'], ['low', 'low']]), 'several cells declares'),
                             (dict(scenarios, mixed=dict(mixed, representative=['low', 'low'])), 'one of its cells'),
                             (dict(scenarios, both_high=[['high']]), 'one category per driver')):
            with self.assertRaisesRegex(ValueError, message):
                driver_law.joint_certificate(drivers, bad)
        with self.assertRaisesRegex(ValueError, 'drivers: 2 to 3'):
            driver_law.joint_certificate(drivers[:1], scenarios)
        with self.assertRaisesRegex(ValueError, 'same order'):
            driver_law.joint_certificate([dict(drivers[0], series=a[::-1]), drivers[1]], scenarios)
        with self.assertRaisesRegex(ValueError, 'non-empty strings'):
            driver_law.joint_certificate([dict(drivers[0], anchors={0: '0', 1: '1'}), drivers[1]], scenarios)

    def test_colorado_joint_law_is_frozen(self):
        # Denver snow and Powell inflow misalign in 14 of the last 30 years: the federation's alignment is refuted,
        # while which candidate wins depends on the partition, so the law is fragile.
        import importlib.util
        history = Path(__file__).resolve().parents[1] / 'history'
        spec = importlib.util.spec_from_file_location('colorado_joint_law', history / 'colorado_joint_law.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        result = module.certificate()
        self.assertEqual(json.loads(json.dumps(result, ensure_ascii=False)), json.loads((history / 'colorado_joint_law.json').read_text()))
        self.assertEqual(result['chosen'], 'frequency')
        self.assertEqual(result['law'], {'aligned_dry': '3/35', 'aligned_normal': '12/35', 'aligned_wet': '4/35',
                                         'powell_drier_than_denver': '9/35', 'powell_wetter_than_denver': '1/5'})
        self.assertEqual(result['law_status'], 'SELECTION_FRAGILE_UNDER_PARTITION')
        self.assertEqual(result['pearson_raw_values'], 0.605)
        self.assertEqual((result['federation_assumption']['aligned_years'], result['federation_assumption']['verdict']), (16, 'REFUTED_BY_RECORD'))

    def test_http_endpoint(self):
        with tempfile.TemporaryDirectory() as temp:
            client = create_app(Path(temp) / 'db.sqlite3', testing=True, evaluator=registry.evaluate).test_client()
            series, anchors = denver()
            response = client.post('/api/laws/driver', json=dict(series=series, anchors=anchors, tie='normal'))
            self.assertEqual(response.status_code, 200, response.json)
            self.assertEqual(response.json['law'], {'dry': '4/33', 'normal': '8/11', 'wet': '5/33'})
            whole = client.post('/api/laws/driver', json=dict(series=series, anchors=anchors, tie='normal', window=None))
            self.assertEqual(whole.json['law'], {'dry': '4/39', 'normal': '28/39', 'wet': '7/39'})
            self.assertEqual(client.post('/api/laws/driver', json=dict(series=series, anchors=anchors, window=0)).status_code, 400)
            self.assertEqual(client.post('/api/laws/driver', json=dict(series=series, anchors={'a': '1'})).status_code, 400)
            self.assertEqual(client.post('/api/laws/driver', json=dict(series=series)).status_code, 400)


if __name__ == '__main__':
    unittest.main()
