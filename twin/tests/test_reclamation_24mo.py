"""The 24-Month Study parser keeps only end-of-month rows of the Lake Mead and Lake Powell tables."""
import importlib.util
from pathlib import Path
import unittest

SCRIPT = Path(__file__).parents[1] / 'history' / 'reclamation_24mo.py'
spec = importlib.util.spec_from_file_location('reclamation_24mo', SCRIPT)
harvester = importlib.util.module_from_spec(spec)
spec.loader.exec_module(harvester)

FIXTURE = """
                         October 2025 24-Month Study
                          Minimum Probable Inflow
                     Glen Canyon Dam - Lake Powell
   Date     Unreg Inflow   Total Release   Elevation   Storage
   Sep 2025      353            470         3540.10      6602
   Oct 2025      400            401         3539.23      6519
   WY 2026     6000           6000
                     Hoover Dam - Lake Mead
   Date   Glen Rel  Side  Evap  Total Rel  CFS  SNWP  Downstr  Bank  Elevation  Storage
   Sep 2025   470    46    46     548     9.2   20    547     529    1057.25    8216
   Oct 2025   480    52    48     545     8.9   20    545     529    1056.22    8139
   Nov 2025   500    38    42     488     8.2   15    488     529    1056.13    8133
                     Davis Dam - Lake Mohave
   Oct 2025   545    10     5     540     8.8    0    540       0     643.00     1700
"""


class ParserTests(unittest.TestCase):
    def test_parses_both_lakes_and_ignores_other_tables(self):
        rows = harvester.parse(FIXTURE, '2025-10')
        mead = [r for r in rows if r['lake'] == 'mead']
        powell = [r for r in rows if r['lake'] == 'powell']
        self.assertEqual([(r['row_month'], r['elevation_ft'], r['storage_kaf'], r['kind']) for r in mead],
                         [('2025-09', '1057.25', '8216', 'historical'), ('2025-10', '1056.22', '8139', 'projected'),
                          ('2025-11', '1056.13', '8133', 'projected')])
        self.assertEqual([r['storage_kaf'] for r in powell], ['6602', '6519'])
        self.assertTrue(harvester.issued(FIXTURE, 2025, 10))
        self.assertFalse(harvester.issued(FIXTURE, 2026, 7))

    def test_current_study_also_tries_the_root_files(self):
        listed = list(harvester.urls(2026, 10, current=(2026, 10)))
        self.assertIn(('min', harvester.BASE + '24mo_MIN.pdf'), listed)
        self.assertIn(('min', harvester.BASE + '24mo/2026/OCT26_MIN.pdf'), listed)


if __name__ == '__main__':
    unittest.main()
