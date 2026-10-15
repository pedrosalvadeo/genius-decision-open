"""Frozen offline test of causal failure-history backoff; no production imports."""
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
EXPERIMENT = ROOT/'beta/experiments/regulation-history'


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name,path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


legacy = load_module('regulation_study_frozen', ROOT/'beta/tools/regulation_study.py')
canonical, digest, read = legacy.canonical, legacy.digest, legacy.read
validate_case, inside = legacy.validate_case, legacy.inside
INPUTS = (*legacy.INPUTS,
          'beta/tools/regulation_history_study.py', 'beta/tests/test_regulation_history.py',
          'beta/experiments/regulation-history/generate_fixtures.py',
          *(f'beta/experiments/regulation-history/{name}.json' for name in
            ('plan','training','evaluation','predeclaration')))


def lock_inputs():
    legacy.lock_inputs()  # The preceding experiment and its sources remain intact.
    declared = read(EXPERIMENT/'predeclaration.json')
    for name, expected in declared['files'].items():
        if name not in INPUTS or hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=expected:
            raise ValueError('PREDECLARED_HISTORY_INPUT_CHANGED')
    plan = read(EXPERIMENT/'plan.json')
    if (plan['baseline_policy_sha256']!=baseline.POLICY_SHA or
            plan['candidate_step_seconds']!=[15,30,60] or plan['production_promotion'] is not False):
        raise ValueError('UNSUPPORTED_HISTORY_PLAN')
    return dict(format='genius-regulation-history-lock/1',
                files={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in INPUTS})


def check_lock(lock):
    if lock!=lock_inputs(): raise ValueError('HISTORY_STUDY_INPUT_CHANGED')


def scenarios(name):
    cases = read(EXPERIMENT/name)
    if not isinstance(cases,list) or not 1 <= len(cases) <= 32:
        raise ValueError('INVALID_HISTORY_SCENARIOS')
    for case in cases: validate_case(case)
    if len({c['id'] for c in cases})!=len(cases): raise ValueError('DUPLICATE_SCENARIO_ID')
    return cases


def wait_after_failures(count, increment):
    """Only observed consecutive operational failure count enters this rule."""
    if type(count) is not int or count < 0 or type(increment) is not int or increment not in (0,15,30,60):
        raise ValueError('INVALID_OBSERVED_HISTORY_OR_RULE')
    return min(180,60+increment*max(0,count-3))


def controller(increment, decisions):
    rt = load_module('genius_beta._history_study_controller', ROOT/'beta/genius_beta/regulation.py')
    wait_after_failures(0,increment)
    if increment==0:
        return rt
    rt.POLICY_SHA = digest(dict(format='genius-offline-backoff-policy/1',
                               baseline_policy_sha256=rt.POLICY_SHA, increment_seconds=increment,
                               adapter_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()))
    original_finish = rt.finish
    def finish(db, config, token, outcome, reason):
        if token is None:
            return original_finish(db,config,token,outcome,reason)
        observed = rt.load(db)
        operational_failure = outcome=='failed' and reason in rt.OPERATIONAL_FAILURES
        next_count = observed['failures']+1 if operational_failure else observed['failures']
        delay = wait_after_failures(next_count,increment)
        previous_policy = rt.POLICY
        # Only the private instance sees this value during the existing atomic finish.
        # POLICY_SHA identifies the complete rule and its source, not a changing parameter.
        rt.POLICY = {**previous_policy,'cooldown_seconds':delay}
        try:
            original_finish(db,config,token,outcome,reason)
        finally:
            rt.POLICY = previous_policy
        if operational_failure and next_count>=3:
            state = rt.load(db)
            decision = dict(observed_at=int(rt.time.time()),failures=next_count,wait_seconds=delay)
            rt.event(db,'backoff_selected',state,decision['observed_at'],
                     wait_seconds=delay,increment_seconds=increment)
            decisions.append(decision)
    rt.finish = finish
    return rt


# Versioned simulator fork; step-zero trajectories are checked against frozen v1.
def simulate(case, increment, plan):
    """FIFO offered requests retry every tick; failures are terminal, never rerun.

    Finish, offer/admit, start, then accumulate outstanding-request exposure.
    A process fails if its [start, finish) overlaps a declared failure window.
    Storage/sensor pressure pauses new work without killing an active process.
    """
    validate_case(case, plan['step_seconds'])
    if type(increment) is not int or increment not in [0,*plan['candidate_step_seconds']]:
        raise ValueError('UNDECLARED_HISTORY_POLICY')
    decisions = []
    rt = controller(increment,decisions)
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
        return dict(id=case['id'], offered=len(case['arrivals']), step_seconds=increment,
                    policy_decisions=[{**d,'observed_at':d['observed_at']-epoch} for d in decisions],
                    policy_sha256=rt.POLICY_SHA, metrics=dict(metrics),
                    mode_seconds=dict(sorted(modes.items())), trace_sha256=trace.hexdigest())
    finally:
        db.close()


def batch(cases, increment, plan):
    runs = [simulate(case,increment,plan) for case in cases]
    return dict(step_seconds=increment,loss=sum(r['metrics']['loss'] for r in runs),cases=runs)


def train(lock):
    check_lock(lock)
    plan = read(EXPERIMENT/'plan.json')
    training = scenarios(plan['training_file'])  # Never parses held-out scenarios.
    control = batch(training,0,plan)
    choices = [batch(training,increment,plan) for increment in plan['candidate_step_seconds']]
    valid = [r for r in choices if all(c['metrics']['safety_violations']==0 for c in r['cases'])]
    if not valid: raise ValueError('NO_SAFE_HISTORY_CANDIDATE')
    selected = min(valid,key=lambda r:(r['loss'],r['step_seconds']))
    frozen = dict(format='genius-regulation-history-candidate/1',lock_sha256=digest(lock),
                  selected_step_seconds=selected['step_seconds'],baseline_training=control,training=choices)
    return {**frozen,'candidate_sha256':digest(frozen)}


def evaluate(lock, candidate):
    check_lock(lock)
    if candidate!=train(lock): raise ValueError('HISTORY_CANDIDATE_NOT_FROZEN_FROM_TRAINING')
    plan = read(EXPERIMENT/'plan.json')
    cases = scenarios(plan['evaluation_file'])
    training_ids = {c['id'] for c in candidate['baseline_training']['cases']}
    if training_ids & {c['id'] for c in cases}: raise ValueError('TRAIN_EVALUATION_OVERLAP')
    control = batch(cases,0,plan)
    result = batch(cases,candidate['selected_step_seconds'],plan)
    pairs = [dict(id=a['id'],baseline=a,candidate=b,gates=legacy.compare_case(a,b,plan))
             for a,b in zip(control['cases'],result['cases'])]
    chosen = next(r for r in candidate['training'] if r['step_seconds']==candidate['selected_step_seconds'])
    gates = dict(training_improved=chosen['loss']<candidate['baseline_training']['loss'],
                 evaluation_improved=result['loss']<control['loss'],
                 every_case_passed=all(all(pair['gates'].values()) for pair in pairs))
    return dict(format='genius-regulation-history-evaluation/1',lock_sha256=digest(lock),
                candidate_sha256=candidate['candidate_sha256'],selected_step_seconds=candidate['selected_step_seconds'],
                status='ELIGIBLE_FOR_REVIEW' if all(gates.values()) else 'REJECTED_BY_EVALUATION',
                production_promotion=False,evidence_origin='synthetic',
                training_loss=dict(baseline=candidate['baseline_training']['loss'],candidate=chosen['loss']),
                evaluation_loss=dict(baseline=control['loss'],candidate=result['loss']),gates=gates,
                cases=pairs,limits=plan['limits'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase',choices=('freeze','train','evaluate','verify'))
    parser.add_argument('--lock',type=Path,required=True)
    parser.add_argument('--candidate',type=Path)
    parser.add_argument('--report',type=Path)
    args = parser.parse_args()
    if args.phase=='freeze':
        legacy.write_new(args.lock,lock_inputs())
    elif args.phase=='train':
        if args.candidate is None: parser.error('--candidate required')
        value = train(read(args.lock)); legacy.write_new(args.candidate,value)
        print(json.dumps(dict(selected_step_seconds=value['selected_step_seconds'],candidate_sha256=value['candidate_sha256'])))
    else:
        if args.candidate is None or args.report is None: parser.error('--candidate and --report required')
        value = evaluate(read(args.lock),read(args.candidate))
        if args.phase=='verify':
            if read(args.report)!=value: raise ValueError('HISTORY_REPORT_RECOMPUTATION_MISMATCH')
        else: legacy.write_new(args.report,value)
        print(json.dumps({key:value[key] for key in ('status','selected_step_seconds','training_loss','evaluation_loss','gates')}))


if __name__=='__main__':
    main()
