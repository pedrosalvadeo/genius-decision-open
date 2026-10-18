"""Joint law (proposed AM-02.1) for the Colorado basin twin of twins: Denver snow and Powell inflow.

The federation colorado_basin_2027 assumes that Denver's winter and Lake Powell's water year
always align (dry with minimum, normal with most probable, wet with maximum). This script tests
that assumption on the record: Denver's April 1 snow index (denver_snow/april1.csv, anchors of
snow_law.py) and Powell's water-year unregulated inflow (lake_mead/powell_unregulated_wy.csv,
anchors of powell_law.py), year by year, over the most recent 30 common water years.

The primary partition follows a rule that does not use the joint record: the federation's three
aligned years, plus a misalignment in each direction (Powell drier than Denver, Powell wetter).
Each misalignment is represented by the cell one step off the diagonal with Denver normal. A
first draft used a partition picked after seeing the table; it and the other partitions tried are
all reported in `partition_sensitivity`, and the law is fragile when the chosen candidate changes.

Run: python twin/history/colorado_joint_law.py > twin/history/colorado_joint_law.json
"""
import csv
from fractions import Fraction
import json
import math
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
from genius_twin import driver_law  # noqa: E402
import powell_law  # noqa: E402

ALIGNED = {'aligned_dry': [['dry', 'dry']], 'aligned_normal': [['normal', 'normal']], 'aligned_wet': [['wet', 'wet']]}
DRIER = [['normal', 'dry'], ['wet', 'dry'], ['wet', 'normal']]   # Denver, Powell: Powell drier than Denver
WETTER = [['normal', 'wet'], ['dry', 'wet'], ['dry', 'normal']]  # Powell wetter than Denver
PRIMARY = dict(ALIGNED, powell_drier_than_denver=dict(cells=DRIER, representative=['normal', 'dry']),
               powell_wetter_than_denver=dict(cells=WETTER, representative=['normal', 'wet']))
TRIED = {
    'by_direction (primary)': PRIMARY,
    'first_draft (picked after seeing the table)': dict(
        ALIGNED, denver_normal_powell_dry=[['normal', 'dry']], denver_normal_powell_wet=[['normal', 'wet']],
        other_misaligned=dict(cells=[['dry', 'normal'], ['dry', 'wet'], ['wet', 'dry'], ['wet', 'normal']], representative=['wet', 'normal'])),
    'by_powell': {c: dict(cells=[[d, c] for d in ('dry', 'normal', 'wet')], representative=['normal', c]) for c in ('dry', 'normal', 'wet')},
    'aligned_or_not': dict(aligned=dict(cells=[['dry', 'dry'], ['normal', 'normal'], ['wet', 'wet']], representative=['normal', 'normal']),
                           misaligned=dict(cells=DRIER + WETTER, representative=['normal', 'dry'])),
}


def drivers():
    rows = list(csv.DictReader((HERE / 'denver_snow' / 'april1.csv').read_text().splitlines()))
    index = {r['year']: Fraction(r['swe_sum_in']) / Fraction(r['median_sum_in']) for r in rows}
    snow = dict(name='Denver April 1 snow index (share of the 1991-2020 median)',
                series=[dict(period=y, value=str(v)) for y, v in index.items()],
                anchors={'dry': str(index['2026']), 'normal': '1', 'wet': '3/2'}, tie='normal')
    found = powell_law.anchors()
    powell = dict(name='Lake Powell water-year unregulated inflow (af)', series=powell_law.series(),
                  anchors={'dry': found['minimum'], 'normal': found['most_probable'], 'wet': found['maximum']}, tie='normal')
    return [snow, powell]


def pearson(cert, both):
    values = [{r['period']: float(Fraction(r['value'])) for r in d['series']} for d in both]
    xs, ys = ([v[c['period']] for c in cert['classification']] for v in values)
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    return round(cov / math.sqrt(sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys)), 3)


def certificate():
    both = drivers()
    cert = driver_law.joint_certificate(both, PRIMARY)
    sensitivity = {}
    for name, partition in TRIED.items():
        c = driver_law.joint_certificate(both, partition)
        sensitivity[name] = dict(chosen=c['chosen'], admitted=c['admitted'], law=c['law'],
                                 scores={k: r['mean_log_score'] for k, r in c['evaluation']['candidates'].items()})
    cert['partition_sensitivity'] = sensitivity
    cert['law_status'] = ('SELECTION_FRAGILE_UNDER_PARTITION' if len({v['chosen'] for v in sensitivity.values()}) > 1
                          else 'STABLE_ACROSS_PARTITIONS_TRIED')
    cert['pearson_raw_values'] = pearson(cert, both)
    aligned = sum(cert['followed'][s] for s in ALIGNED)
    cert['federation_assumption'] = dict(
        statement='SharedHydrology: Denver and Powell years always align (federation colorado_basin_2027).',
        aligned_years=aligned, misaligned_years=cert['outcomes'] - aligned,
        verdict='REFUTED_BY_RECORD' if aligned < cert['outcomes'] else 'NOT_REFUTED',
        caveat='How many years misalign depends on the anchors: Powell wet sits at 194 % of its normal anchor, Denver wet at 150 %.')
    return cert


if __name__ == '__main__':
    print(json.dumps(certificate(), indent=1, ensure_ascii=False))
