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
        self.assertEqual(result['followed'], {'dry': 3, 'normal': 27, 'wet': 6})

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

    def test_http_endpoint(self):
        with tempfile.TemporaryDirectory() as temp:
            client = create_app(Path(temp) / 'db.sqlite3', testing=True, evaluator=registry.evaluate).test_client()
            series, anchors = denver()
            response = client.post('/api/laws/driver', json=dict(series=series, anchors=anchors, tie='normal'))
            self.assertEqual(response.status_code, 200, response.json)
            self.assertEqual(response.json['law'], {'dry': '4/39', 'normal': '28/39', 'wet': '7/39'})
            self.assertEqual(client.post('/api/laws/driver', json=dict(series=series, anchors={'a': '1'})).status_code, 400)
            self.assertEqual(client.post('/api/laws/driver', json=dict(series=series)).status_code, 400)


if __name__ == '__main__':
    unittest.main()
