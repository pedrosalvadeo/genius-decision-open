"""AM-02 law for the Lake Mead twins from Lake Powell's water-year unregulated inflow.

Anchors are the water-year 2027 unregulated inflow totals at Lake Powell in Reclamation's
October 2026 minimum, most probable and maximum 24-Month Studies (studies.csv). Each past
water year (powell_unregulated_wy.csv, RISE item 4301) is assigned to the closest anchor.
The law is climatological: it does not use what the October forecast knows. Two windows
are certified, the whole record and the most recent 30 years, because the record is not
known to be stationary (the basin has been drier since 2000).

Run: python twin/history/powell_law.py > twin/history/lake_mead/powell_law_wy2027.json
"""
import csv
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from genius_twin import driver_law  # noqa: E402

STUDY = '2026-10'
SCENARIOS = {'minimum': 'min', 'most_probable': 'most_probable_6', 'maximum': 'max'}


def anchors():
    totals = dict.fromkeys(SCENARIOS.values(), 0)
    with (HERE / 'lake_mead' / 'studies.csv').open() as handle:
        for row in csv.DictReader(handle):
            if (row['study_date'] == STUDY and row['lake'] == 'powell' and row['kind'] == 'projected'
                    and '2026-10' <= row['row_month'] <= '2027-09' and row['scenario'] in totals):
                totals[row['scenario']] += int(row['unregulated_inflow_kaf'])
    return {name: totals[key] * 1000 for name, key in SCENARIOS.items()}


def series():
    with (HERE / 'lake_mead' / 'powell_unregulated_wy.csv').open() as handle:
        return [dict(period=row['water_year'], value=row['unregulated_inflow_af']) for row in csv.DictReader(handle)]


def certificates():
    found, history = anchors(), series()
    windows = {'whole_record': history, 'last_30_years': history[-driver_law.MIN_INDEPENDENT_OUTCOMES:]}
    return {name: driver_law.certificate(periods, found, tie='most_probable', driver='Lake Powell water-year unregulated inflow (af)')
            for name, periods in windows.items()}


if __name__ == '__main__':
    print(json.dumps(certificates(), indent=1, sort_keys=True))
