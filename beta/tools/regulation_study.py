"""Offline, deterministic cooldown selection. Never imports a live app or database.

The actual controller runs against in-memory SQLite with simulated clock/sensors.
Only this process's private module instance changes policy. No network or deploy API.
"""
import argparse
from collections import Counter, deque
import hashlib
import importlib.util
import json
from pathlib import Path
import sqlite3
from types import SimpleNamespace

from genius_beta import regulation as baseline
from genius_beta.db import transaction

ROOT = Path(__file__).resolve().parents[2]
EXPERIMENT = ROOT / 'beta/experiments/regulation'
INPUTS = (
    'beta/tools/regulation_study.py', 'beta/tests/test_regulation_study.py',
    'beta/genius_beta/regulation.py', 'beta/genius_beta/db.py',
    'beta/migrations/011_mission_regulation.sql',
    *(f'beta/experiments/regulation/{name}.json' for name in
      ('plan', 'training', 'evaluation', 'predeclaration')),
)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def lock_inputs():
    declared = read(EXPERIMENT / 'predeclaration.json')
    for name, expected in declared['files'].items():
        if name not in INPUTS or hashlib.sha256((ROOT/name).read_bytes()).hexdigest() != expected:
            raise ValueError('PREDECLARED_INPUT_CHANGED')
    plan = read(EXPERIMENT / 'plan.json')
    if plan['baseline_policy_sha256'] != baseline.POLICY_SHA:
        raise ValueError('BASELINE_POLICY_CHANGED')
    if plan['candidate_cooldown_seconds'] != [60, 90, 120, 180] or plan['production_promotion'] is not False:
        raise ValueError('UNSUPPORTED_STUDY_PLAN')
    return dict(format='genius-regulation-study-lock/1',
                files={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in INPUTS})


def check_lock(lock):
    if lock != lock_inputs():
        raise ValueError('STUDY_INPUT_CHANGED')


def validate_case(case, step=5):
    if set(case) != {'id', 'horizon', 'duration', 'arrivals', 'failures', 'storage', 'sensors'}:
        raise ValueError('INVALID_SCENARIO_FIELDS')
    if not isinstance(case['id'], str) or not 1 <= len(case['id']) <= 80:
        raise ValueError('INVALID_SCENARIO_ID')
    for key, low, high in (('horizon', 60, 1800), ('duration', 5, 60)):
        value = case[key]
        if type(value) is not int or not low <= value <= high or value % step:
            raise ValueError('INVALID_SCENARIO_TIME')
    arrivals = case['arrivals']
    if (not isinstance(arrivals, list) or not 1 <= len(arrivals) <= 200 or
            any(type(t) is not int or not 0 <= t < case['horizon'] or t % step for t in arrivals) or
            sorted(arrivals) != arrivals):
        raise ValueError('INVALID_SCENARIO_ARRIVALS')
    for key in ('failures', 'storage', 'sensors'):
        windows = case[key]
        if not isinstance(windows, list) or len(windows) > 20:
            raise ValueError('INVALID_SCENARIO_WINDOWS')
        previous = -1
        for pair in windows:
            if (not isinstance(pair, list) or len(pair) != 2 or
                    any(type(t) is not int or t % step for t in pair) or
                    not 0 <= pair[0] < pair[1] <= case['horizon'] or pair[0] < previous):
                raise ValueError('INVALID_SCENARIO_WINDOWS')
            previous = pair[1]


def scenarios(name):
    cases = read(EXPERIMENT / name)
    if not isinstance(cases, list) or not 1 <= len(cases) <= 20:
        raise ValueError('INVALID_SCENARIO_SET')
    for case in cases:
        validate_case(case)
    if len({case['id'] for case in cases}) != len(cases):
        raise ValueError('DUPLICATE_SCENARIO_ID')
    return cases


def inside(t, windows):
    return any(start <= t < end for start, end in windows)


def simulate(case, cooldown, plan):
    """FIFO offered requests retry every tick; failures are terminal, never rerun.

    Finish, offer/admit, start, then accumulate outstanding-request exposure.
    A process fails if its [start, finish) overlaps a declared failure window.
    Storage/sensor pressure pauses new work without killing an active process.
    """
    validate_case(case, plan['step_seconds'])
    if type(cooldown) is not int or cooldown not in plan['candidate_cooldown_seconds']:
        raise ValueError('UNDECLARED_POLICY')
    spec = importlib.util.spec_from_file_location('genius_beta._study_controller',
                                                ROOT/'beta/genius_beta/regulation.py')
    rt = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rt)
    rt.POLICY = {**rt.POLICY, 'cooldown_seconds':cooldown}
    rt.POLICY_SHA = hashlib.sha256(rt.dump(rt.POLICY).encode()).hexdigest()
    now, epoch, serial = 0, 1_000_000_000, 0
    rt.time = SimpleNamespace(time=lambda:epoch+now)
    def token(_size):
        nonlocal serial
        serial += 1
        return f'{serial:032x}'
    rt.secrets = SimpleNamespace(token_hex=token)
    config = dict(ADAPTIVE_ENABLED=True, MISSION_REGULATION_ENABLED=True,
                  MAX_DATABASE_BYTES=100*1024**2, MIN_FREE_BYTES=10*1024**2)
    offered, queue, active = deque(), deque(), None
    future = deque(enumerate(case['arrivals']))
    metrics = Counter(completed=0, operational_failures=0, exposure_seconds=0,
                      admission_deferrals=0, max_pending=0, safety_violations=0,
                      max_success_latency_seconds=0)
    modes, trace = Counter(), hashlib.sha256()
    def sensor(*_):
        if inside(now, case['sensors']):
            raise OSError('SYNTHETIC_SENSOR_UNAVAILABLE')
        return dict(storage_bytes=(90 if inside(now, case['storage']) else 20)*1024**2,
                    free_bytes=1024**3, pending=len(queue)+int(active is not None))
    rt.observe = sensor
    db = sqlite3.connect(':memory:', isolation_level=None)
    db.row_factory = sqlite3.Row
    db.executescript((ROOT/'beta/migrations/011_mission_regulation.sql').read_text())
    try:
        for now in range(0, case['horizon']+1, plan['step_seconds']):
            finished, started, admitted = None, None, []
            if active is not None and active['end'] == now:
                finished = active
                active = None
                failed = finished['failed']
                with transaction(db):
                    rt.finish(db, config, finished['token'],
                              'failed' if failed else 'completed',
                              'MISSION_PROCESS_FAILED' if failed else None)
                metrics['operational_failures' if failed else 'completed'] += 1
                if not failed:
                    metrics['max_success_latency_seconds'] = max(
                        metrics['max_success_latency_seconds'], now-finished['arrival'])
            while future and future[0][1] == now:
                offered.append(future.popleft())
            state = rt.refresh(db, config, force=True)
            if now < case['horizon']:
                while offered:
                    state = rt.refresh(db, config, force=True)
                    if len(queue)+int(active is not None) >= plan['max_pending'] or not rt.admits(state):
                        metrics['admission_deferrals'] += len(offered)
                        break
                    item = offered.popleft()
                    queue.append(item)
                    admitted.append(item[0])
                    if inside(now, case['storage']) or inside(now, case['sensors']):
                        metrics['safety_violations'] += 1
                state = rt.refresh(db, config, force=True)
                if queue and active is None and rt.starts(state):
                    if (inside(now, case['storage']) or inside(now, case['sensors']) or
                            epoch+now < state['cooldown_until']):
                        metrics['safety_violations'] += 1
                    identity, arrival = queue.popleft()
                    with transaction(db):
                        execution_token = rt.begin(db, config, state)
                    end = now+case['duration']
                    failed = any(now < stop and end > start for start,stop in case['failures'])
                    active = dict(id=identity, arrival=arrival, end=end, failed=failed, token=execution_token)
                    started = identity
                pending = len(queue)+int(active is not None)
                metrics['max_pending'] = max(metrics['max_pending'], pending)
                if pending > plan['max_pending']:
                    metrics['safety_violations'] += 1
                metrics['exposure_seconds'] += (len(offered)+pending)*plan['step_seconds']
                modes[state['mode']] += plan['step_seconds']
            trace.update(canonical([now, state['mode'], admitted, started,
                                    None if finished is None else [finished['id'],finished['failed']],
                                    len(offered), len(queue), active is not None]))
        metrics['unfinished'] = len(offered)+len(queue)+int(active is not None)
        assert len(case['arrivals']) == metrics['completed']+metrics['operational_failures']+metrics['unfinished']
        weights = plan['loss_weights']
        metrics['loss'] = (weights['operational_failure']*metrics['operational_failures']+
                           weights['unfinished']*metrics['unfinished']+
                           weights['exposure_second']*metrics['exposure_seconds'])
        return dict(id=case['id'], offered=len(case['arrivals']), cooldown_seconds=cooldown,
                    policy_sha256=rt.POLICY_SHA, metrics=dict(metrics),
                    mode_seconds=dict(sorted(modes.items())), trace_sha256=trace.hexdigest())
    finally:
        db.close()


def batch(cases, cooldown, plan):
    runs = [simulate(case, cooldown, plan) for case in cases]
    return dict(cooldown_seconds=cooldown, loss=sum(r['metrics']['loss'] for r in runs), cases=runs)


def train(lock):
    check_lock(lock)
    plan = read(EXPERIMENT/'plan.json')
    # Evaluation bytes are integrity-bound by the lock, but never parsed or scored here.
    training = scenarios(plan['training_file'])
    choices = [batch(training, cooldown, plan) for cooldown in plan['candidate_cooldown_seconds']]
    valid = [r for r in choices if all(c['metrics']['safety_violations']==0 for c in r['cases'])]
    if not valid:
        raise ValueError('NO_SAFE_TRAINING_CANDIDATE')
    selected = min(valid, key=lambda r:(r['loss'],r['cooldown_seconds']))
    frozen = dict(format='genius-regulation-candidate/1', lock_sha256=digest(lock),
                  selected_cooldown_seconds=selected['cooldown_seconds'], training=choices)
    return {**frozen, 'candidate_sha256':digest(frozen)}


def compare_case(reference, candidate, plan):
    before, after = reference['metrics'], candidate['metrics']
    return dict(
        loss_not_worse=after['loss'] <= before['loss'],
        completed_not_fewer=after['completed'] >= before['completed'],
        failures_not_more=after['operational_failures'] <= before['operational_failures'],
        unfinished_not_more=after['unfinished'] <= before['unfinished'],
        latency_within_margin=after['max_success_latency_seconds'] <= before['max_success_latency_seconds']+
            plan['gates']['max_success_latency_regression_seconds'],
        zero_safety_violations=after['safety_violations']==before['safety_violations']==0)


def evaluate(lock, candidate):
    check_lock(lock)
    # Prevent edited training scores, policy substitution or using evaluation to reselect.
    if candidate != train(lock):
        raise ValueError('CANDIDATE_NOT_FROZEN_FROM_TRAINING')
    plan = read(EXPERIMENT/'plan.json')
    training_ids = {r['id'] for r in candidate['training'][0]['cases']}
    cases = scenarios(plan['evaluation_file'])
    if training_ids & {r['id'] for r in cases}:
        raise ValueError('TRAIN_EVALUATION_OVERLAP')
    reference = batch(cases, baseline.POLICY['cooldown_seconds'], plan)
    result = batch(cases, candidate['selected_cooldown_seconds'], plan)
    paired = [dict(id=a['id'], baseline=a, candidate=b, gates=compare_case(a,b,plan))
              for a,b in zip(reference['cases'],result['cases'])]
    base_training = next(r for r in candidate['training'] if r['cooldown_seconds']==baseline.POLICY['cooldown_seconds'])
    chosen_training = next(r for r in candidate['training'] if r['cooldown_seconds']==candidate['selected_cooldown_seconds'])
    gates = dict(training_improved=chosen_training['loss'] < base_training['loss'],
                 evaluation_improved=result['loss'] < reference['loss'],
                 every_case_passed=all(all(case['gates'].values()) for case in paired))
    return dict(format='genius-regulation-evaluation/1', lock_sha256=digest(lock),
                candidate_sha256=candidate['candidate_sha256'],
                status='ELIGIBLE_FOR_REVIEW' if all(gates.values()) else 'REJECTED_BY_EVALUATION',
                production_promotion=False, evidence_origin='synthetic',
                selected_cooldown_seconds=candidate['selected_cooldown_seconds'],
                training_loss=dict(baseline=base_training['loss'],candidate=chosen_training['loss']),
                evaluation_loss=dict(baseline=reference['loss'],candidate=result['loss']),
                gates=gates, cases=paired, limits=plan['limits'])


def write_new(path, value):
    # Preserve previous results; create a new version instead of rewriting evidence.
    with Path(path).open('x') as stream:
        stream.write(json.dumps(value, indent=2, ensure_ascii=False)+'\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('freeze','train','evaluate','verify'))
    parser.add_argument('--lock', type=Path, required=True)
    parser.add_argument('--candidate', type=Path)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    if args.phase=='freeze':
        write_new(args.lock, lock_inputs())
    elif args.phase=='train':
        if args.candidate is None: parser.error('--candidate required')
        value = train(read(args.lock)); write_new(args.candidate,value)
        print(json.dumps(dict(selected_cooldown_seconds=value['selected_cooldown_seconds'],candidate_sha256=value['candidate_sha256'])))
    else:
        if args.candidate is None or args.report is None: parser.error('--candidate and --report required')
        value = evaluate(read(args.lock), read(args.candidate))
        if args.phase=='verify':
            if read(args.report) != value: raise ValueError('REPORT_RECOMPUTATION_MISMATCH')
        else:
            write_new(args.report, value)
        print(json.dumps({key:value[key] for key in ('status','selected_cooldown_seconds','training_loss','evaluation_loss','gates')}))


if __name__=='__main__':
    main()
