"""Empirical admitted law (LEA, GENIUS_PROGRAM/theory/AMENDMENTS.md AM-02) for a twin built on official scenarios.

Realizations are the official scenarios of one study (minimum, most probable, maximum). For each past
study, the scenario that reality followed is the one whose projected trajectory was closest to what
was later published, summing absolute errors over the `horizon` projected months. Two candidate
procedures are fixed in advance: equal masses, and the Laplace-smoothed frequency (k + 1) / (n + 3)
of past studies (optionally of the same issue month) whose outcome was already published. Among the
candidates that pass calibration, the one with the best mean log score is chosen. The certificate
then lists every reason the law cannot be admitted (AM-02 repairs); it is admitted only with none.

The certificate checks AM-02's four conditions on a prequential backtest: each historical forecast
uses only outcomes published before its study. It is labelled RETROSPECTIVE_PREQUENTIAL because the
procedure was written after that history existed; prospective contrasts must later confirm it or the
law is revoked. Masses are exact fractions; confidence bounds are floats used only for the check.

Run from the repository root:
  python twin/history/empirical_law.py twin/history/lake_mead/studies.csv --lake mead --horizon 11 --month 10 --driver inflow
"""
import argparse
import csv
from collections import Counter
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
import hindcast  # noqa: E402

PROCEDURE = 'genius-empirical-law/1'
SCENARIOS = ('minimum', 'most_probable', 'maximum')
# Declared before use (AM-02 repairs): an interval that merely fails to reject proves little with few
# independent outcomes, so admission needs at least this many non-overlapping ones.
MIN_INDEPENDENT_OUTCOMES = 30


def outcomes(rows, lake, horizon, month=None):
    """[(study, scenario reality followed, month its last value is published)] oldest first."""
    history = hindcast.history_index(rows)
    paths = {}
    for row in rows:
        if row['kind'] == 'projected' and row['lake'] == lake:
            paths.setdefault((row['study'], row['scenario']), {})[row['month']] = row['storage']
    out = []
    for study in sorted({s for s, _ in paths}):
        if month is not None and study % 12 + 1 != month:
            continue
        if not all((study, s) in paths for s in SCENARIOS):
            continue
        months = range(study + 1, study + horizon + 1)
        if not all(m in paths[(study, s)] for s in SCENARIOS for m in months):
            continue
        actual = [hindcast.actual_as_of(history, lake, m) for m in months]
        if None in actual:
            continue
        distance = {s: sum(abs(a - paths[(study, s)][m]) for a, m in zip(actual, months)) for s in SCENARIOS}
        followed = min(SCENARIOS, key=lambda s: (distance[s], s != 'most_probable'))
        # The last month becomes an actual in the following study, so the outcome is known then.
        out.append(dict(study=study, followed=followed, known=study + horizon + 1))
    return out


def inflow_outcomes(path, horizon, month=None):
    """Like `outcomes`, judged on cumulative unregulated inflow to Lake Powell over the horizon.

    Unregulated inflow is the hydrology each scenario assumes and does not depend on how the dams are
    operated, so the classification holds for every policy the twin compares.
    """
    paths, actual = {}, {}
    with open(path, newline='') as handle:
        for raw in csv.DictReader(handle):
            if raw['lake'] != 'powell' or not raw.get('unregulated_inflow_kaf', '').strip():
                continue
            study, row_month = hindcast.month_index(raw['study_date']), hindcast.month_index(raw['row_month'])
            value = Fraction(raw['unregulated_inflow_kaf'])
            scenario = hindcast.SCENARIO_ALIASES.get(raw['scenario'].strip().lower())
            if raw['kind'] == 'projected' and scenario in SCENARIOS and raw['scenario'] != 'most_probable_6':
                paths.setdefault((study, scenario), {})[row_month] = value
            elif raw['kind'] == 'historical' and raw['scenario'] == 'most_probable':
                actual.setdefault(row_month, {})[study] = value
    out = []
    for study in sorted({s for s, _ in paths}):
        if month is not None and study % 12 + 1 != month:
            continue
        months = range(study + 1, study + horizon + 1)
        if not all((study, s) in paths and all(m in paths[(study, s)] for m in months) for s in SCENARIOS):
            continue
        if not all(m in actual for m in months):
            continue
        # The value as published by the first study that reports the month as historical.
        observed = sum(actual[m][min(actual[m])] for m in months)
        distance = {s: abs(observed - sum(paths[(study, s)][m] for m in months)) for s in SCENARIOS}
        followed = min(SCENARIOS, key=lambda s: (distance[s], s != 'most_probable'))
        out.append(dict(study=study, followed=followed, known=max(min(actual[m]) for m in months)))
    return out


def frequency_law(known):
    """Laplace-smoothed frequencies over the outcomes given; exact and normalized."""
    counts = Counter(o['followed'] for o in known)
    total = len(known) + len(SCENARIOS)
    return {s: Fraction(counts[s] + 1, total) for s in SCENARIOS}


def uniform_law(known):
    return {s: Fraction(1, len(SCENARIOS)) for s in SCENARIOS}


# Candidate procedures, fixed before evaluation; AM-02 picks among the calibrated ones by log score.
CANDIDATES = {'uniform': uniform_law, 'frequency': frequency_law}


def _binomial_cdf(k, n, p):
    return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k + 1))


def clopper_pearson(k, n, confidence):
    """Exact two-sided interval for a binomial proportion, by bisection."""
    tail = (1 - confidence) / 2

    def solve(target, cdf_at):
        low, high = 0.0, 1.0
        for _ in range(60):
            mid = (low + high) / 2
            if cdf_at(mid) > target:
                low = mid
            else:
                high = mid
        return (low + high) / 2

    lower = 0.0 if k == 0 else solve(1 - tail, lambda p: _binomial_cdf(k - 1, n, p))
    upper = 1.0 if k == n else solve(tail, lambda p: _binomial_cdf(k, n, p))
    return lower, upper


def evaluate(history, procedure, confidence):
    """Prequential check of one candidate: calibration per scenario and mean log score."""
    forecasts = [dict(law=procedure([o for o in history if o['known'] <= t['study']]), followed=t['followed']) for t in history]
    n = len(forecasts)
    # Bonferroni over the scenarios, so the joint check holds at the declared confidence.
    per_band = 1 - (1 - float(confidence)) / len(SCENARIOS)
    bands, calibrated = {}, n > 0
    for s in SCENARIOS:
        k = sum(f['followed'] == s for f in forecasts)
        mean_mass = sum(f['law'][s] for f in forecasts) / n if n else Fraction(0)
        low, high = clopper_pearson(k, n, per_band) if n else (0.0, 1.0)
        inside = low <= float(mean_mass) <= high
        calibrated = calibrated and inside
        bands[s] = dict(observed=k, mean_mass=round(float(mean_mass), 4), interval=[round(low, 4), round(high, 4)], inside=inside)
    score = sum(math.log(f['law'][f['followed']]) for f in forecasts) / n if n else None
    return dict(count=n, per_band_confidence=round(per_band, 6), bands=bands, calibrated=calibrated,
                mean_log_score=None if score is None else round(score, 6))


def certificate(path, lake, horizon, month, confidence=Fraction(95, 100), driver='storage'):
    history = inflow_outcomes(path, horizon, month) if driver == 'inflow' else outcomes(hindcast.load(path), lake, horizon, month)
    results = {name: evaluate(history, procedure, confidence) for name, procedure in CANDIDATES.items()}
    eligible = sorted((r['mean_log_score'], name) for name, r in results.items() if r['calibrated'])
    chosen = eligible[-1][1] if eligible else None
    # Only studies issued 12 or more months apart have non-overlapping horizons.
    independent = month is not None and horizon < 12
    refusals = []
    if chosen is None:
        refusals.append('NO_CALIBRATED_CANDIDATE')
    if not independent:
        refusals.append('OVERLAPPING_OUTCOMES: fix an issue month and a horizon under 12 months')
    if len(history) < MIN_INDEPENDENT_OUTCOMES:
        refusals.append(f'INSUFFICIENT_EVIDENCE: {len(history)} independent outcomes, {MIN_INDEPENDENT_OUTCOMES} required')
    if driver != 'inflow':
        # Storage depends on the operations in force, so it cannot tell which hydrology happened.
        refusals.append('POLICY_DEPENDENT_CLASSIFICATION: judged on storage, not on an exogenous driver such as unregulated inflow')
    return dict(
        procedure=PROCEDURE, amendment='AM-02', data=Path(path).name,
        data_sha256=hashlib.sha256(Path(path).read_bytes()).hexdigest(),
        lake=lake, driver=driver, horizon=horizon, issue_month=month, realizations=list(SCENARIOS), outcomes=len(history),
        followed={s: sum(o['followed'] == s for o in history) for s in SCENARIOS},
        evaluation=dict(kind='RETROSPECTIVE_PREQUENTIAL', confidence=str(confidence), candidates=results),
        chosen=chosen,
        law=None if chosen is None else {s: str(v) for s, v in CANDIDATES[chosen](history).items()},
        refusals=refusals, admitted=not refusals,
        meaning=('Masa empírica de que la realidad siga más de cerca cada escenario oficial. '
                 'Retrospectiva precuencial: aun admitida, se revoca si los contrastes prospectivos la descalibran. No es bienestar.'))


def law_free_order(success):
    """Pairs (a, b) where policy a has PVS at least b's under every law: b's successful scenarios are a subset of a's.

    `success` maps each policy to the set of scenarios where it meets the task. When this order already
    separates the policies, no law is needed; when two policies succeed on the same scenarios, no law can
    separate them.
    """
    return sorted((a, b) for a in success for b in success if a != b and set(success[b]) <= set(success[a]))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('csv')
    parser.add_argument('--lake', default='mead')
    parser.add_argument('--horizon', type=int, default=11)
    parser.add_argument('--month', type=int, default=None, help='issue month to match (1-12); all months if omitted')
    parser.add_argument('--driver', choices=['storage', 'inflow'], default='storage',
                        help='judge the scenario reality followed on storage or on unregulated inflow to Lake Powell')
    args = parser.parse_args(argv)
    json.dump(certificate(args.csv, args.lake, args.horizon, args.month, driver=args.driver), sys.stdout, ensure_ascii=False, indent=1)
    print()


if __name__ == '__main__':
    main()
