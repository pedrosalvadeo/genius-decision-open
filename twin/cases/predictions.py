"""Frozen predictions of the field cases and their contrast with later readings.

freeze   writes <case>/prediction.json from the committed world.json with the
         same construction and evaluator the twin uses in production.
contrast compares one real reading with every frozen policy and scenario and
         appends the receipt to <case>/observations.json. It never edits the
         prediction or calibrates the model.

Run from the repository root with PYTHONPATH=twin:kernel:
  python twin/cases/predictions.py freeze denver_water_2026
  python twin/cases/predictions.py contrast denver_water_2026 --date 2026-11-14 --value 63.4 \
      --observed-at 2026-11-14T16:00:00+00:00 --source "Denver Water, <url>, <exact quote>"
"""
import argparse
from datetime import date, datetime, timedelta, timezone
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys

from genius_twin import construction, registry
from genius_twin.service import q, rational
from genius_twin.store import sha

CASES = Path(__file__).resolve().parent
FORMAT = 'genius-twin-frozen-prediction/1'
# Matching a reading to a model step is a bookkeeping convention, not a Genius rule.
WINDOW_DAYS = 7


def _month_end(year, month):
    return (date(year + month // 12, month % 12 + 1, 1) - timedelta(days=1))


SETUP = {
    'denver_water_2026': dict(
        stock='storage', unit='pct_capacity',
        calendar=[date(2026 + (9 + k) // 12, (9 + k) % 12 + 1, 15) for k in range(13)],
        calendar_basis='Paso 0 = 15/10/2026; paso k = día 15 de cada mes (claim modelling de world.json).',
        reading='Porcentaje de llenado de los embalses de suministro que publica Denver Water.',
        sources=['https://www.denverwater.org/tap/denver-water-snowpack-and-water-supply-update']),
    'mendoza_potrerillos_2026': dict(
        stock='potrerillos', unit='hm3',
        calendar=[date(2026, 10, 15)] + [_month_end(2026 + (10 + k) // 12, (10 + k) % 12 + 1) for k in range(11)],
        calendar_basis='Paso 0 = mediados de octubre de 2026 (171 hm³); paso k = fin de cada mes de noviembre a septiembre (convención del modelizador).',
        reading='Volumen embalsado en Potrerillos que informa el Departamento General de Irrigación o la prensa que lo cita.',
        sources=['https://www.irrigacion.gov.ar']),
    'lake_mead_2027': dict(
        stock='mead', unit='kaf',
        calendar=[_month_end(2026 + (8 + k) // 12, (8 + k) % 12 + 1) for k in range(13)],
        calendar_basis='Paso 0 = fin de septiembre de 2026 (dato histórico); paso k = fin de cada mes de octubre de 2026 a septiembre de 2027 (claim modelling de world.json).',
        reading='Almacenamiento de Lake Mead a fin de mes (mil acre-pies), fila histórica del 24-Month Study siguiente.',
        sources=['https://www.usbr.gov/lc/region/g4000/24mo.pdf']),
}


def _world(case):
    path = CASES / case / 'world.json'
    raw = path.read_bytes()
    return json.loads(raw), hashlib.sha256(raw).hexdigest()


def compute(case):
    """The prediction exactly as the twin evaluates the committed world, without a timestamp."""
    setup = SETUP[case]
    world, world_sha256 = _world(case)
    prepared = construction.prepare(world['construction'], dict(id='observation', revision=1, observation=world['observation'], historical_gaps={}))
    if prepared['status'] != 'READY_FOR_REVIEW':
        raise SystemExit(f'{case}: world construction is {prepared["status"]}')
    model = prepared['model']
    evaluation = registry.evaluate(model)
    if not evaluation['verification']['valid']:
        raise SystemExit(f'{case}: native verification failed')
    results = evaluation['canonical_results']
    if len(setup['calendar']) != model['horizon'] + 1:
        raise SystemExit(f'{case}: calendar does not cover the horizon')
    decision = results['decision']
    return {
        'format': FORMAT, 'case': case, 'world_sha256': world_sha256, 'model_sha256': sha(model),
        'native_input_digest': evaluation['native_result'].get('input_digest'),
        'decision': {key: decision.get(key) for key in ('feasible', 'failed', 'selected', 'selection_status')},
        'observable': {'stock': setup['stock'], 'unit': setup['unit'], 'reading': setup['reading'], 'sources': setup['sources']},
        'calendar': [day.isoformat() for day in setup['calendar']], 'calendar_basis': setup['calendar_basis'],
        'matching': f'Una lectura se asigna al paso cuya fecha está a {WINDOW_DAYS} días o menos; si no hay ninguno, no se contrasta.',
        'predicted': {policy: {scenario: [state['stocks'][setup['stock']] for state in trajectory['daily']]
                               for scenario, trajectory in row['trajectories'].items()}
                      for policy, row in results['policies'].items()},
        'meaning': 'Predicción condicional al modelo declarado. Sin ley de probabilidad no hay escenario más probable; contrastar no valida el modelo.',
    }


def freeze(case):
    prediction = compute(case)
    prediction['frozen_at'] = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    prediction['prediction_sha256'] = sha({k: v for k, v in prediction.items() if k != 'prediction_sha256'})
    path = CASES / case / 'prediction.json'
    path.write_text(json.dumps(prediction, ensure_ascii=False, indent=1) + '\n')
    return path


def load(case):
    return json.loads((CASES / case / 'prediction.json').read_text())


def contrast(case, reading_date, value, observed_at, source):
    frozen = load(case)
    fresh = compute(case)
    for key in ('world_sha256', 'model_sha256', 'native_input_digest', 'predicted'):
        if fresh[key] != frozen[key]:
            raise SystemExit(f'{case}: the committed world no longer reproduces the frozen prediction ({key})')
    measured = rational(value)
    timestamp = datetime.fromisoformat(observed_at.replace('Z', '+00:00'))
    if timestamp.tzinfo is None:
        raise SystemExit('observed_at needs a time zone')
    calendar = [date.fromisoformat(day) for day in frozen['calendar']]
    gaps = [abs((day - reading_date).days) for day in calendar]
    step = min(range(len(calendar)), key=gaps.__getitem__)
    if gaps[step] > WINDOW_DAYS:
        raise SystemExit(f'{reading_date} is {gaps[step]} days from the nearest step ({calendar[step]})')
    comparisons = {}
    for policy, scenarios in frozen['predicted'].items():
        rows = {scenario: {'predicted_exact': values[step], 'delta_exact': q(measured - Fraction(values[step]))}
                for scenario, values in scenarios.items()}
        nearest = min(abs(Fraction(row['delta_exact'])) for row in rows.values())
        comparisons[policy] = {'scenarios': rows,
                               'nearest_scenarios': sorted(s for s, row in rows.items() if abs(Fraction(row['delta_exact'])) == nearest)}
    record = {
        'case': case, 'prediction_sha256': frozen['prediction_sha256'], 'frozen_at': frozen['frozen_at'],
        'step': step, 'step_date': calendar[step].isoformat(), 'reading_date': reading_date.isoformat(),
        'variable': frozen['observable']['stock'], 'unit': frozen['observable']['unit'], 'value_exact': q(measured),
        'observed_at': timestamp.isoformat(), 'source': source,
        'origin': 'CITED_PUBLIC_READING', 'source_authentication': 'NOT_ESTABLISHED',
        'temporal_relation': ('PROSPECTIVE_REFERENCE' if timestamp > datetime.fromisoformat(frozen['frozen_at'])
                              else 'RETROSPECTIVE_COMPARISON_NOT_PROSPECTIVE_VALIDATION'),
        'model_was_calibrated': False, 'comparisons': comparisons,
        'meaning': 'Diferencias exactas contra cada política y escenario congelados. Los escenarios más cercanos son descriptivos, sin umbral ni probabilidad.',
    }
    path = CASES / case / 'observations.json'
    log = json.loads(path.read_text()) if path.exists() else {'format': 'genius-twin-field-observations/1', 'case': case, 'observations': []}
    if any(row['reading_date'] == record['reading_date'] and row['source'] == source for row in log['observations']):
        raise SystemExit('this reading is already recorded')
    log['observations'].append(record)
    path.write_text(json.dumps(log, ensure_ascii=False, indent=1) + '\n')
    return record


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('freeze').add_argument('case', choices=sorted(SETUP))
    reading = commands.add_parser('contrast')
    reading.add_argument('case', choices=sorted(SETUP))
    reading.add_argument('--date', required=True, type=date.fromisoformat, help='Date the reading refers to')
    reading.add_argument('--value', required=True, help='Exact decimal or n/d in the observable unit')
    reading.add_argument('--observed-at', required=True, help='ISO8601 with time zone, when it was published or read')
    reading.add_argument('--source', required=True, help='Publisher, URL and the exact quoted figure')
    args = parser.parse_args(argv)
    if args.command == 'freeze':
        print(freeze(args.case))
    else:
        json.dump(contrast(args.case, args.date, args.value, args.observed_at, args.source), sys.stdout, ensure_ascii=False, indent=1)
        print()


if __name__ == '__main__':
    main()
