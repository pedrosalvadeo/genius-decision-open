"""The empirical law classifies past studies by the scenario reality followed and certifies candidates prequentially."""
from fractions import Fraction
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

HISTORY = Path(__file__).parents[1] / 'history'
sys.path.insert(0, str(HISTORY))
spec = importlib.util.spec_from_file_location('empirical_law', HISTORY / 'empirical_law.py')
empirical = importlib.util.module_from_spec(spec)
spec.loader.exec_module(empirical)


def rows_for(followed):
    """One study per year (October), horizon 2; reality tracks the named scenario exactly."""
    shift = {'minimum': -100, 'most_probable': 0, 'maximum': 100}
    rows = []
    for year, name in enumerate(followed):
        study = (2010 + year) * 12 + 9
        for month in (study + 1, study + 2):
            for scenario in empirical.SCENARIOS:
                rows.append(dict(study=study, scenario=scenario, lake='mead', month=month, storage=Fraction(1000 + shift[scenario]), kind='projected'))
            # The next study publishes the month as historical.
            rows.append(dict(study=study + 12, scenario='most_probable', lake='mead', month=month,
                             storage=Fraction(1000 + shift[name]), kind='historical'))
    return rows


class EmpiricalLawTests(unittest.TestCase):
    def test_outcomes_follow_the_nearest_trajectory_and_wait_for_publication(self):
        found = empirical.outcomes(rows_for(['minimum', 'maximum', 'maximum']), 'mead', 2, month=10)
        self.assertEqual([o['followed'] for o in found], ['minimum', 'maximum', 'maximum'])
        self.assertEqual(found[0]['known'], found[0]['study'] + 3)

    def test_laws_are_exact_and_normalized(self):
        known = [dict(followed='minimum'), dict(followed='minimum'), dict(followed='maximum')]
        law = empirical.frequency_law(known)
        self.assertEqual(law, {'minimum': Fraction(1, 2), 'most_probable': Fraction(1, 6), 'maximum': Fraction(1, 3)})
        self.assertEqual(sum(empirical.uniform_law(known).values()), 1)

    def test_clopper_pearson_matches_known_bounds(self):
        low, high = empirical.clopper_pearson(0, 10, 0.95)
        self.assertEqual(low, 0.0)
        self.assertAlmostEqual(high, 0.3085, places=3)
        low, high = empirical.clopper_pearson(5, 10, 0.95)
        self.assertAlmostEqual(low, 0.1871, places=3)
        self.assertAlmostEqual(high, 0.8129, places=3)

    def test_a_persistent_pattern_makes_frequency_beat_equal_masses(self):
        history = empirical.outcomes(rows_for(['minimum'] * 12), 'mead', 2, month=10)
        uniform = empirical.evaluate(history, empirical.uniform_law, Fraction(95, 100))
        frequency = empirical.evaluate(history, empirical.frequency_law, Fraction(95, 100))
        self.assertFalse(uniform['calibrated'])  # 1/3 is far below the observed 12 of 12
        self.assertGreater(frequency['mean_log_score'], uniform['mean_log_score'])

    def test_certificate_refuses_without_independent_evidence_or_an_exogenous_driver(self):
        cert = empirical.certificate(Path(__file__).parents[1] / 'history' / 'lake_mead' / 'studies.csv', 'mead', 11, 10)
        self.assertEqual(cert['outcomes'], 14)
        self.assertEqual(cert['chosen'], 'uniform')
        self.assertFalse(cert['admitted'])
        self.assertTrue(any(r.startswith('INSUFFICIENT_EVIDENCE') for r in cert['refusals']))
        self.assertTrue(any(r.startswith('POLICY_DEPENDENT') for r in cert['refusals']))

    def test_law_free_order_follows_scenario_inclusion(self):
        self.assertEqual(empirical.law_free_order({'a': {'x', 'y'}, 'b': {'y'}}), [('a', 'b')])
        # Lake Mead 2027: both releases fail only in the minimum year, so every law gives them equal PVS.
        both = {'release_6': {'most_probable', 'maximum'}, 'release_7': {'most_probable', 'maximum'}}
        self.assertEqual(empirical.law_free_order(both), [('release_6', 'release_7'), ('release_7', 'release_6')])


    def test_inflow_outcomes_judge_hydrology_and_drop_the_policy_refusal(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'studies.csv'
            lines = ['study_date,scenario,source_url,pdf_sha256,row_month,lake,elevation_ft,storage_kaf,kind,unregulated_inflow_kaf']
            for name, inflow in (('most_probable', 300), ('min', 100), ('max', 500)):
                lines += [f'2020-10,{name},u,h,2020-{m},powell,3600.00,9000,projected,{inflow}' for m in ('11', '12')]
            lines += [f'2021-01,most_probable,u,h,2020-{m},powell,3600.00,9000,historical,120' for m in ('11', '12')]
            path.write_text('\n'.join(lines) + '\n')
            found = empirical.inflow_outcomes(path, 2, month=10)
            self.assertEqual(found, [dict(study=2020 * 12 + 9, followed='minimum', known=2021 * 12)])
            cert = empirical.certificate(path, 'mead', 2, 10, driver='inflow')
            self.assertFalse(any(r.startswith('POLICY_DEPENDENT') for r in cert['refusals']))



class DenverSnowLawTests(unittest.TestCase):
    def test_april_snow_admits_a_law_and_rejects_thirds(self):
        import snow_law
        cert = snow_law.certificate(HISTORY / 'denver_snow' / 'april1.csv')
        self.assertEqual((cert['outcomes'], cert['years_offered']), (30, 36))
        self.assertEqual(cert['non_normal_years'], {'dry': [2002, 2012, 2026], 'wet': [1997, 2011, 2014, 2019]})
        self.assertFalse(cert['evaluation']['candidates']['uniform']['calibrated'])
        self.assertEqual((cert['chosen'], cert['law'], cert['admitted']), ('frequency', {'dry': '4/33', 'normal': '8/11', 'wet': '5/33'}, True))
        committed = __import__('json').loads((HISTORY / 'denver_snow' / 'law_certificate.json').read_text())
        self.assertEqual(committed, __import__('json').loads(__import__('json').dumps(cert)))


if __name__ == '__main__':
    unittest.main()
