"""The 24-Month Study parser keeps only end-of-month rows of the Lake Mead and Lake Powell tables."""
import importlib.util
from pathlib import Path
import unittest

SCRIPT = Path(__file__).parents[1] / 'history' / 'reclamation_24mo.py'
spec = importlib.util.spec_from_file_location('reclamation_24mo', SCRIPT)
harvester = importlib.util.module_from_spec(spec)
spec.loader.exec_module(harvester)

# Excerpt of `pdftotext -layout` output of the October 2025 Probable Minimum study (real layout).
FIXTURE = """
       OPERATION PLAN FOR COLORADO RIVER SYSTEM RESERVOIRS
                                     October 2025 24-Month Study
                                           Minimum Probable Inflow
                                          Fontenelle Reservoir
             Regulated     Evaporation       Power         Bypass          Total          Reservoir            Live
Date           Inflow        Losses         Release        Release        Release         Elevation          Storage
            (1000 Ac-Ft)   (1000 Ac-Ft)   (1000 Ac-Ft)   (1000 Ac-Ft)   (1000 Ac-Ft)   End of Month (Ft)   (1000 Ac-Ft)
Oct 2024        30              1             47              4              51            6489.49             215
                                                                        Lake Powell
            Unregulated     Regulated     Evaporation    Power Plant      Bypass          Total          Reservoir            Bank        End Of Month         Lees
Date           Inflow         Inflow        Losses         Release        Release        Release         Elevation           Storage         Storage        Ferry Gage
            (1000 Ac-Ft)   (1000 Ac-Ft)   (1000 Ac-Ft)   (1000 Ac-Ft)   (1000 Ac-Ft)   (1000 Ac-Ft)   End of Month (Ft)    (1000 Ac-Ft)    (1000 Ac-Ft)    (1000 Ac-Ft)
Sep 2025        162            346            28             367            198            565               3544.69          4629            6749             579
WY 2025        4688           5136            239           6994            487           7481                                                                7505
Oct 2025        320            409            19             480             0             480               3543.39          4623            6665             486
                                                             Hoover Dam – Lake Mead
                Glen         Side Inflow    Evaporation       Total          Total        SNWP        Downstream          Bank           Reservoir        End Of Month
Date          Release      Glen to Hoover     Losses         Release        Release        Use        Requirements       Storage         Elevation           Storage
            (1000 Ac-Ft)    (1000 Ac-Ft)    (1000 Ac-Ft)   (1000 Ac-Ft)   (1000 CFS)   (1000 Ac-Ft)    (1000 Ac-Ft)    (1000 Ac-Ft)   End of Month (Ft)    (1000 Ac-Ft)
Sep 2025        565             96              51             457           7.7           18               633            534             1057.25            8216
WY 2025        7481             548             474           7873                         204              8068
Oct 2025        480             52              48             545           8.9           20               545            529             1056.22            8139
 Jul 2026       710             34              46             766           12.5          26               766            490             1048.03            7542
"""


class ParserTests(unittest.TestCase):
    def test_parses_both_lakes_and_ignores_other_tables(self):
        rows = harvester.parse(FIXTURE, '2025-10')
        mead = [r for r in rows if r['lake'] == 'mead']
        powell = [r for r in rows if r['lake'] == 'powell']
        self.assertEqual([(r['row_month'], r['elevation_ft'], r['storage_kaf'], r['kind']) for r in mead],
                         [('2025-09', '1057.25', '8216', 'historical'), ('2025-10', '1056.22', '8139', 'projected'),
                          ('2026-07', '1048.03', '7542', 'projected')])
        # End-of-month storage, not bank storage or Lees Ferry; Fontenelle is ignored.
        self.assertEqual([(r['elevation_ft'], r['storage_kaf']) for r in powell], [('3544.69', '6749'), ('3543.39', '6665')])
        self.assertTrue(harvester.issued(FIXTURE, 2025, 10))
        self.assertFalse(harvester.issued(FIXTURE, 2026, 7))

    def test_current_study_also_tries_the_root_files(self):
        listed = list(harvester.urls(2026, 10, current=(2026, 10)))
        self.assertIn(('min', harvester.BASE + '24mo_MIN.pdf'), listed)
        self.assertIn(('min', harvester.BASE + '24mo/2026/OCT26_MIN.pdf'), listed)


if __name__ == '__main__':
    unittest.main()
