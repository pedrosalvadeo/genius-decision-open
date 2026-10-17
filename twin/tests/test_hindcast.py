"""Hindcasts contrast past projections with later actuals and learn only from information published before each study."""
import csv
from fractions import Fraction
import importlib.util
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).parents[1] / 'history' / 'hindcast.py'
spec = importlib.util.spec_from_file_location('hindcast', SCRIPT)
hindcast = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hindcast)


def actual(index):
    return 6000 + 10 * (index % 12) - index  # seasonal wave with a slow decline


def synthetic_csv(path, first='2020-01', last='2023-12', bias=100):
    start, end = hindcast.month_index(first), hindcast.month_index(last)
    with open(path, 'w', newline='') as handle:
        writer = csv.writer(handle)
        writer.writerow(['study_date', 'scenario', 'source_url', 'row_month', 'lake', 'elevation_ft', 'storage_kaf', 'kind'])
        for study in range(start, end + 1):
            for scenario, shift in (('most_probable', bias), ('min', bias - 150), ('max', bias + 150)):
                for month in range(study - 3, study + 13):
                    historical = month < study
                    value = actual(month) if historical else actual(month) + shift + (month - study) * (1 if scenario == 'most_probable' else 0)
                    writer.writerow([hindcast.month_text(study), scenario, 'synthetic', hindcast.month_text(month), 'mead', '', value,
                                     'historical' if historical else 'projected'])


class HindcastTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / 'studies.csv'
        synthetic_csv(self.path)
        self.rows = hindcast.load(self.path)

    def tearDown(self):
        self.temp.cleanup()

    def test_contrasts_envelope_and_revisions(self):
        result = hindcast.summary(self.rows)
        lead12 = next(r for r in result['errors'] if r['scenario'] == 'most_probable' and r['lead'] == 12)
        self.assertEqual(lead12['mean_error'], '-112')  # projections were 100 + 12 too high
        self.assertEqual(result['revisions'], [])
        self.assertEqual({e['status'] for e in hindcast.envelope(self.rows)}, {'inside'})  # minimum sits 50 below the actual
        high = Path(self.temp.name) / 'high.csv'
        synthetic_csv(high, bias=300)  # minimum sits 150 above the actual
        self.assertEqual({e['status'] for e in hindcast.envelope(hindcast.load(high))}, {'below_minimum'})
        self.assertEqual(result['criterion'], 'OBSERVED_ABSOLUTE_ERROR_NOT_WELLBEING_OR_PVS')

    def test_learning_uses_only_published_past_and_confirms(self):
        result = hindcast.learn(self.rows, 'mead', 12, size=6)
        self.assertEqual(result['trials'][0]['outcome'], 'ADOPTED')
        self.assertNotEqual(result['genome']['correction'], 'none')
        for target in hindcast.targets(self.rows, 'mead', 12):
            # Every past error refers to a month already published when the target study was issued.
            self.assertTrue(all(isinstance(e, Fraction) for e in target['past']))
            self.assertLessEqual(len(target['past']), target['study'] - hindcast.month_index('2020-01') - 12)

    def test_revised_actuals_are_reported(self):
        rows = [dict(r) for r in self.rows]
        for row in rows:
            if row['kind'] == 'historical' and row['month'] == hindcast.month_index('2021-05') and row['study'] == hindcast.month_index('2021-07'):
                row['storage'] += 3
        found = hindcast.revisions(hindcast.history_index(rows))
        self.assertEqual(found, [dict(lake='mead', month='2021-05', values=[str(actual(hindcast.month_index('2021-05'))),
                                                                              str(actual(hindcast.month_index('2021-05')) + 3)], spread='3')])


    def test_conformal_bands_use_past_errors_and_report_coverage(self):
        self.assertEqual(hindcast.conformal_quantile([3, 1, 2], Fraction(1, 2)), 2)
        self.assertIsNone(hindcast.conformal_quantile([1, 2], Fraction(19, 20)))  # too few errors for a 95% bound
        result = hindcast.bands(self.rows, 'mead', 6, Fraction(1, 5), 36)
        # Synthetic most probable errors at lead 6 are constant, so every band is exact and covers.
        self.assertGreater(result['count'], 0)
        self.assertEqual(result['covered'], result['count'])
        self.assertEqual(Fraction(result['mean_width']), 0)

if __name__ == '__main__':
    unittest.main()
