"""Contrast past official projections with what later happened, and learn data-only corrections.

Input: a studies CSV (see twin/history/lake_mead/) with one row per study, scenario,
lake and month. Rows before the study month are "historical"; the rest are "projected".

contrasts  every projected value whose month later became historical, with the actual
           value as published at the latest study, its lead in months and the exact error.
envelope   whether the actual value fell inside the [minimum, maximum] projections of the
           same study.
revisions  historical values that later studies changed (a measurement-robustness signal).
bands      empirical bands from past errors (split-conformal quantiles) and their observed
           out-of-sample coverage, the evidence an empirical law needs (PROPOSAL_AM-02).
learn      selects a data-only correction genome with the discovery/confirmation rule of the
           habitat organisms, using only information published before each target study.

This is an operational prediction experiment. Its errors are not wellbeing, CAG or PVS,
and nothing here edits a kernel, a twin model or a frozen prediction.

Run from the repository root:
  python twin/history/hindcast.py summary twin/history/lake_mead/studies.csv
  python twin/history/hindcast.py learn twin/history/lake_mead/studies.csv --lake mead --lead 12
"""
import argparse
from collections import defaultdict
import csv
from fractions import Fraction
import json
import math
from statistics import median
import sys

PROTOCOL = 'genius-hindcast-learning/1'
CRITERION = 'OBSERVED_ABSOLUTE_ERROR_NOT_WELLBEING_OR_PVS'
SCENARIO_ALIASES = {'most_probable': 'most_probable', 'mp': 'most_probable', 'most_probable_6': 'most_probable',
                    'min': 'minimum', 'minimum': 'minimum', 'max': 'maximum', 'maximum': 'maximum'}
# Data-only genes, mirroring adaptive/federation/genetics.py: neither code nor authority is a gene.
ALLELES = {'correction': ('none', 'median', 'mean'), 'window': (12, 36, 120)}
FOUNDER = {'correction': 'none', 'window': 36}
PHASE_SIZE = 12


def month_index(text):
    year, month = text[:7].split('-')
    return int(year) * 12 + int(month) - 1


def month_text(index):
    return f'{index // 12:04d}-{index % 12 + 1:02d}'


def load(path):
    rows = []
    with open(path, newline='') as handle:
        raws = list(csv.DictReader(handle))
    plain = {raw['study_date'] for raw in raws if raw['scenario'].strip().lower() == 'most_probable'}
    for raw in raws:
        if raw['scenario'].strip().lower() == 'most_probable_6' and raw['study_date'] in plain:
            continue  # the plain most probable study already covers this month
        scenario = SCENARIO_ALIASES.get(raw['scenario'].strip().lower())
        if scenario is None or not raw.get('storage_kaf', '').strip():
            continue  # 7 maf variants and rows without storage are kept in the CSV but not contrasted here
        rows.append(dict(study=month_index(raw['study_date']), scenario=scenario, lake=raw['lake'].strip().lower(),
                         month=month_index(raw['row_month']), storage=Fraction(raw['storage_kaf']), kind=raw['kind'].strip()))
    return rows


def history_index(rows):
    """(lake, month) -> [(study, value)] for historical rows, oldest study first; most probable runs only."""
    seen = defaultdict(dict)
    for row in rows:
        if row['kind'] == 'historical':
            seen[(row['lake'], row['month'])].setdefault(row['study'], row['storage'])
    return {key: sorted(values.items()) for key, values in seen.items()}


def actual_as_of(history, lake, month, study=None):
    """Actual value as published in the latest study up to `study` (None = latest of all)."""
    values = [value for issued, value in history.get((lake, month), []) if study is None or issued <= study]
    return values[-1] if values else None


def revisions(history):
    out = []
    for (lake, month), values in sorted(history.items()):
        distinct = sorted({value for _, value in values})
        if len(distinct) > 1:
            out.append(dict(lake=lake, month=month_text(month), values=[str(v) for v in distinct], spread=str(distinct[-1] - distinct[0])))
    return out


def contrasts(rows, history=None):
    history = history_index(rows) if history is None else history
    out = []
    for row in rows:
        if row['kind'] != 'projected':
            continue
        actual = actual_as_of(history, row['lake'], row['month'])
        if actual is None:
            continue
        out.append(dict(study=row['study'], scenario=row['scenario'], lake=row['lake'], month=row['month'],
                        lead=row['month'] - row['study'], projected=row['storage'], actual=actual, error=actual - row['storage']))
    return out


def envelope(rows, history=None):
    history = history_index(rows) if history is None else history
    bounds = defaultdict(dict)
    for row in rows:
        if row['kind'] == 'projected' and row['scenario'] in ('minimum', 'maximum'):
            bounds[(row['study'], row['lake'], row['month'])][row['scenario']] = row['storage']
    out = []
    for (study, lake, month), pair in sorted(bounds.items()):
        actual = actual_as_of(history, lake, month)
        if actual is None or len(pair) < 2:
            continue
        low, high = pair['minimum'], pair['maximum']
        status = 'below_minimum' if actual < low else 'above_maximum' if actual > high else 'inside'
        out.append(dict(study=study, lake=lake, month=month, lead=month - study, minimum=low, maximum=high, actual=actual, status=status))
    return out


def summary(rows):
    history = history_index(rows)
    table = defaultdict(list)
    for c in contrasts(rows, history):
        table[(c['lake'], c['scenario'], c['lead'])].append(c['error'])
    cover = defaultdict(lambda: defaultdict(int))
    for e in envelope(rows, history):
        cover[(e['lake'], e['lead'])][e['status']] += 1
    errors = [dict(lake=lake, scenario=scenario, lead=lead, count=len(v), mean_error=str(sum(v) / len(v)),
                   mean_absolute_error=str(sum(abs(x) for x in v) / len(v)), max_absolute_error=str(max(abs(x) for x in v)))
              for (lake, scenario, lead), v in sorted(table.items())]
    coverage = [dict(lake=lake, lead=lead, **counts) for (lake, lead), counts in sorted(cover.items())]
    return dict(protocol=PROTOCOL, criterion=CRITERION, errors=errors, envelope=coverage, revisions=revisions(history))


def genomes():
    return [dict(correction=c, window=w) for c in ALLELES['correction'] for w in ALLELES['window']]


def express(genome, projected, past_errors):
    """Corrected projection from past errors only (newest last). `none` keeps the official value."""
    window = past_errors[-genome['window']:]
    if genome['correction'] == 'none' or not window:
        return projected
    shift = Fraction(median(window)) if genome['correction'] == 'median' else sum(window) / len(window)
    return projected + shift


def targets(rows, lake, lead, scenario='most_probable'):
    """Chronological targets with the errors that were already knowable when each study was issued."""
    history = history_index(rows)
    resolved = sorted((c for c in contrasts(rows, history) if c['lake'] == lake and c['lead'] == lead and c['scenario'] == scenario),
                      key=lambda c: c['study'])
    out = []
    for target in resolved:
        # A past error is knowable at study s when its month's actual was published by s, and it is
        # measured against the actual as published then, not as later revised.
        past = []
        for c in resolved:
            known = actual_as_of(history, lake, c['month'], target['study']) if c['month'] < target['study'] else None
            if known is not None:
                past.append(known - c['projected'])
        if past:  # targets with no knowable past cannot tell genomes apart
            out.append(dict(target, past=past))
    return out


def metrics(block, genome):
    errors = [abs(t['actual'] - express(genome, t['projected'], t['past'])) for t in block]
    return dict(count=len(errors), absolute_error_sum=sum(errors), max_error=max(errors, default=Fraction(0)))


def improves(candidate, baseline, size=PHASE_SIZE):
    """Same rule as adaptive/federation/organism.py, with a configurable phase size."""
    return (candidate['count'] == baseline['count'] == size and
            candidate['absolute_error_sum'] < baseline['absolute_error_sum'] and
            candidate['max_error'] <= baseline['max_error'])


def mutants(genome):
    out = []
    for name, values in ALLELES.items():
        for value in values:
            if value != genome[name]:
                out.append({**genome, name: value})
    return out


def learn(rows, lake, lead, size=PHASE_SIZE, founder=FOUNDER):
    """Walk the history in disjoint chronological phases: discover a one-locus mutant, then confirm it on new targets."""
    pending = targets(rows, lake, lead)
    current, trials, cursor = dict(founder), [], 0
    while cursor + 2 * size <= len(pending):
        discovery, confirmation = pending[cursor:cursor + size], pending[cursor + size:cursor + 2 * size]
        cursor += 2 * size
        base = metrics(discovery, current)
        scored = [(metrics(discovery, m), m) for m in mutants(current)]
        eligible = sorted((s for s in scored if improves(s[0], base, size)), key=lambda s: (s[0]['absolute_error_sum'], s[0]['max_error'], json.dumps(s[1], sort_keys=True)))
        trial = dict(discovery=[month_text(t['study']) for t in (discovery[0], discovery[-1])],
                     confirmation=[month_text(t['study']) for t in (confirmation[0], confirmation[-1])],
                     baseline=dict(current), baseline_discovery=_text(base))
        if not eligible:
            trials.append(dict(trial, outcome='NO_ELIGIBLE_VARIANT'))
            continue
        candidate = eligible[0][1]
        confirm_base, confirm_candidate = metrics(confirmation, current), metrics(confirmation, candidate)
        adopted = improves(confirm_candidate, confirm_base, size)
        trials.append(dict(trial, candidate=candidate, candidate_discovery=_text(eligible[0][0]),
                           baseline_confirmation=_text(confirm_base), candidate_confirmation=_text(confirm_candidate),
                           outcome='ADOPTED' if adopted else 'REJECTED_AT_CONFIRMATION'))
        if adopted:
            current = candidate
    return dict(protocol=PROTOCOL, criterion=CRITERION, lake=lake, lead=lead, phase_size=size, targets=len(pending),
                founder=founder, genome=current, trials=trials,
                meaning='Corrección operativa aprendida sólo con información publicada antes de cada estudio. No es bienestar ni PVS.')


def conformal_quantile(errors, level):
    """Rank ceil((n+1)*level) of the sorted errors, or None when the sample is too small for that level."""
    ordered = sorted(errors)
    rank = math.ceil((len(ordered) + 1) * level)
    return ordered[rank - 1] if 1 <= rank <= len(ordered) else None


def bands(rows, lake, lead, alpha=Fraction(1, 10), window=120):
    """Band [projected + q(alpha/2), projected + q(1 - alpha/2)] from the last `window` knowable errors.

    Coverage is counted only on targets whose band could be formed, using information published
    before each study. Nominal coverage 1 - alpha is a claim; `covered / count` is the check.
    """
    out = []
    for target in targets(rows, lake, lead):
        past = target['past'][-window:]
        low, high = conformal_quantile(past, alpha / 2), conformal_quantile(past, 1 - alpha / 2)
        if low is None or high is None:
            continue
        out.append(dict(study=month_text(target['study']), lower=target['projected'] + low, upper=target['projected'] + high,
                        actual=target['actual'], covered=target['projected'] + low <= target['actual'] <= target['projected'] + high))
    covered = sum(b['covered'] for b in out)
    return dict(protocol=PROTOCOL, lake=lake, lead=lead, nominal=str(1 - alpha), window=window, count=len(out), covered=covered,
                mean_width=str(sum(b['upper'] - b['lower'] for b in out) / len(out)) if out else None,
                meaning='Cobertura observada fuera de muestra de bandas empíricas. No es bienestar ni PVS.')


def _text(m):
    return {k: str(v) for k, v in m.items()}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('summary').add_argument('csv')
    learning = commands.add_parser('learn')
    learning.add_argument('csv')
    learning.add_argument('--lake', default='mead')
    learning.add_argument('--lead', type=int, default=12)
    learning.add_argument('--phase-size', type=int, default=PHASE_SIZE)
    banding = commands.add_parser('bands')
    banding.add_argument('csv')
    banding.add_argument('--lake', default='mead')
    banding.add_argument('--lead', type=int, default=12)
    banding.add_argument('--alpha', type=Fraction, default=Fraction(1, 10))
    banding.add_argument('--window', type=int, default=120)
    args = parser.parse_args(argv)
    rows = load(args.csv)
    if args.command == 'summary':
        result = summary(rows)
    elif args.command == 'learn':
        result = learn(rows, args.lake, args.lead, args.phase_size)
    else:
        result = bands(rows, args.lake, args.lead, args.alpha, args.window)
    json.dump(result, sys.stdout, ensure_ascii=False, indent=1, default=str)
    print()


if __name__ == '__main__':
    main()
