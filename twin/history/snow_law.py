"""Empirical admitted law (AM-02) for Denver's winters from NRCS April 1 snow.

Each year's outcome is the Denver scenario whose snow it was closest to: dry is anchored at
2026 (the case defines it as "a melt like 2026"), normal at 100 % of the 1991-2020 median and
wet at 150 % (the case defines it as "snow above 150 %"). Ties go to normal. The candidates,
calibration check and log score are those of empirical_law.py; a forecast for year t uses only
outcomes up to t-1, as it would be issued the October before. Snow is exogenous to Denver's
watering rules, and one April 1 per year gives non-overlapping outcomes.

Run from the repository root:
  python twin/history/snow_law.py twin/history/denver_snow/april1.csv
"""
import argparse
import csv
from collections import Counter
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
import empirical_law  # noqa: E402

DENVER = {'minimum': 'dry', 'most_probable': 'normal', 'maximum': 'wet'}


def outcomes(path):
    rows = list(csv.DictReader(Path(path).open()))
    by_year = {int(r['year']): Fraction(r['swe_sum_in']) / Fraction(r['median_sum_in']) for r in rows}
    anchor = {'minimum': by_year[2026], 'most_probable': Fraction(1), 'maximum': Fraction(3, 2)}
    history = []
    for year, index in sorted(by_year.items()):
        followed = min(anchor, key=lambda s: (abs(index - anchor[s]), s != 'most_probable'))
        history.append(dict(study=year - 1, known=year, year=year, index=index, followed=followed))
    return history, anchor


def certificate(path, confidence=Fraction(95, 100)):
    history, anchor = outcomes(path)
    results = {name: empirical_law.evaluate(history, procedure, confidence) for name, procedure in empirical_law.CANDIDATES.items()}
    eligible = sorted((r['mean_log_score'], name) for name, r in results.items() if r['calibrated'])
    chosen = eligible[-1][1] if eligible else None
    refusals = []
    if chosen is None:
        refusals.append('NO_CALIBRATED_CANDIDATE')
    if len(history) < empirical_law.MIN_INDEPENDENT_OUTCOMES:
        refusals.append(f'INSUFFICIENT_EVIDENCE: {len(history)} independent outcomes, {empirical_law.MIN_INDEPENDENT_OUTCOMES} required')
    law = None if chosen is None else empirical_law.CANDIDATES[chosen](history)
    return dict(
        procedure=empirical_law.PROCEDURE, amendment='AM-02', data=Path(path).name,
        data_sha256=hashlib.sha256(Path(path).read_bytes()).hexdigest(), driver='april1_snow_index',
        anchors={DENVER[s]: f'{float(100 * v):.1f}%' for s, v in anchor.items()}, outcomes=len(history),
        followed={DENVER[s]: n for s, n in Counter(o['followed'] for o in history).items()},
        non_normal_years={DENVER[s]: [o['year'] for o in history if o['followed'] == s] for s in ('minimum', 'maximum')},
        evaluation=dict(kind='RETROSPECTIVE_PREQUENTIAL', confidence=str(confidence),
                        candidates={name: {**r, 'bands': {DENVER[s]: b for s, b in r['bands'].items()}} for name, r in results.items()}),
        chosen=chosen, law=None if law is None else {DENVER[s]: str(v) for s, v in law.items()},
        refusals=refusals, admitted=not refusals,
        meaning=('Masa empírica de que el invierno se parezca más a cada escenario de Denver, según la nieve del 1 de abril. '
                 'Retrospectiva precuencial: se revoca si los contrastes prospectivos la descalibran.'))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('csv')
    args = parser.parse_args(argv)
    json.dump(certificate(args.csv), sys.stdout, ensure_ascii=False, indent=1)
    print()


if __name__ == '__main__':
    main()
