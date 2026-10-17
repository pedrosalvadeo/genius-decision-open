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


# Older layouts: 2009 has a units block and no Date header; 2012-2025 carry margin letters and "EOM".
FIXTURE_2009 = """
                                Lake Powell

                Unreg       Regulated        Evap PowerPlant      Bypass           Total    Reservoir      Bank          EOM    Lees
               Inflow          Inflow      Losses    Release     Release         Release    Elevation   Storage      Storage   Ferry
                 1000            1000        1000       1000        1000            1000          EOM      1000         1000    1000
                Ac-Ft           Ac-Ft       Ac-Ft      Ac-Ft       Ac-Ft           Ac-Ft         Feet     Ac-Ft        Ac-Ft   Ac-Ft

* Sep 2008            390          555         56        723            0             723     3626.90      17423       14509     738
  WY 2008           12344        12417        396       8885           93            8978                                       9164
                         Hoover Dam - Lake Mead

                Power        Power           EOM       EOM    Change_In       Hoover       Hoover    Hoover      Percent   KWH/AF
              Release      Release     Reservoir   Storage      Storage       Static    Generator     Gross           Of
                 1000         1000     Elevation      1000         1000         Head     Capacity    Energy        Units
                Ac-Ft          CFS          Feet     Ac-Ft        Ac-Ft         Feet           MW      MKWH    Available

* Sep 2008           652        11.0     1105.76      12013           58         0.00      1677.0      252.9         100    387.9
  WY 2008           9530                                                                              3790.6
"""

FIXTURE_2024 = """
                                                                                                    Lake Powell
                       Unreg        Regulated        Evap        PowerPlant       Bypass          Total     Reservoir Elev    Bank           EOM             Lees
                       Inflow         Inflow        Losses         Release        Release        Release    End of Month     Storage        Storage       Ferry Gage
         Date       (1000 Ac-Ft)   (1000 Ac-Ft)   (1000 Ac-Ft)   (1000 Ac-Ft)   (1000 Ac-Ft)   (1000 Ac-Ft)      (Ft)      (1000 Ac-Ft)   (1000 Ac-Ft)   (1000 Ac-Ft)
   *    Jan 2023        361            424             4             500             0            501         3523.45          4490           5456             510
   H    Feb 2023        270            337             4             480             0            480         3521.04          4479           5320             493
                                                                                            Hoover Dam - Lake Mead
                       Power          Power     Reservoir Elev    EOM          Change In        Hoover      Hoover Gen      Hoover       Percent of
                      Release        Release    End of Month     Storage        Storage       Static Head    Capacity    Gross Energy      Units
         Date       (1000 Ac-Ft)   (1000 CFS)        (Ft)      (1000 Ac-Ft)   (1000 Ac-Ft)        (Ft)         MW           MKWH         Available        KWH/AF
   *    Jan 2023         412           6.7          1046.97        7466          152            403.66        866.6         143.8            64           348.8
   H    Feb 2023         494           8.9          1047.02        7469            4            399.03        810.5         175.9            60           356.5
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

    def test_older_layouts_take_end_of_month_storage(self):
        for fixture, study, expected in [
                (FIXTURE_2009, '2009-09', [('powell', '2008-09', '3626.90', '14509'), ('mead', '2008-09', '1105.76', '12013')]),
                (FIXTURE_2024, '2024-01', [('powell', '2023-01', '3523.45', '5456'), ('powell', '2023-02', '3521.04', '5320'),
                                           ('mead', '2023-01', '1046.97', '7466'), ('mead', '2023-02', '1047.02', '7469')])]:
            rows = harvester.parse(fixture, study)
            self.assertEqual([(r['lake'], r['row_month'], r['elevation_ft'], r['storage_kaf']) for r in rows], expected)

    def test_powell_rows_carry_unregulated_inflow(self):
        for fixture, study, month, inflow in [(FIXTURE, '2025-10', '2025-09', '162'), (FIXTURE_2009, '2009-09', '2008-09', '390'),
                                              (FIXTURE_2024, '2024-01', '2023-01', '361')]:
            rows = {(r['lake'], r['row_month']): r for r in harvester.parse(fixture, study)}
            self.assertEqual(rows[('powell', month)]['unregulated_inflow_kaf'], inflow)
            self.assertEqual(rows[('mead', month)]['unregulated_inflow_kaf'], '')

    def test_current_study_also_tries_the_root_files(self):
        listed = list(harvester.urls(2026, 10, current=(2026, 10)))
        self.assertIn(('min', harvester.BASE + '24mo_MIN.pdf'), listed)
        self.assertIn(('min', harvester.BASE + '24mo/2026/OCT26_MIN.pdf'), listed)


if __name__ == '__main__':
    unittest.main()
