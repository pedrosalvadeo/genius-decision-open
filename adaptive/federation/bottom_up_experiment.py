"""Three nodes initiate their own bounded inquiries; synthetic delayed evidence."""
import argparse
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import tempfile
from threading import Event
import time

from .core import digest, now
from .experiment import Process
from .world_example import example


def statement(view, value):
    doc = view['construction']
    doc['sources'][0]['content'] = value
    doc['claims'][0]['spans'] = [dict(source_id='source', start=0, end=len(value), quote=value)]
    view['observation']['evidence'][0]['statement'] = value


def fixture(reference, expires):
    views = example(reference, expires)
    energy = views[1]
    availability = next(f for f in energy['construction']['fragments'] if f['path'] == '/scenarios/0')
    energy['construction']['fragments'].remove(availability)
    statement(energy, 'Hipótesis sintética: capacidad de 1 kWh y 1 hora. Reparar consume 1 hora y habilita powered. Faltan las disponibilidades por día; no se supone que sean constantes.')
    delayed = deepcopy(energy)
    delayed['view_id'] = 'availability'
    delayed['bindings'] = []
    availability['value']['events'][1]['renewables']['energy'] = '0/1'
    delayed['construction']['fragments'] = [availability]
    statement(delayed, 'Escenario sintético declarado: energía disponible 1, 0, 1 kWh en los días 1, 2 y 3; mantenimiento 1 hora por día. Se comunica tarde la interrupción energética del segundo día. No es una medición real.')
    conflict = deepcopy(delayed)
    conflict['owner'], conflict['view_id'] = 'water', 'opposing-availability'
    conflict['construction']['sources'][0]['origin'] = 'fixture:opposing-report'
    conflict['construction']['fragments'][0]['value']['events'][1]['renewables']['energy'] = '1/1'
    statement(conflict, 'Informe sintético incompatible: se declara energía 1, 1, 1 kWh. No se aporta criterio para resolver la discrepancia con el informe de interrupción.')
    return views, delayed, conflict


def wait_for(read, predicate, timeout=25):
    end = time.monotonic()+timeout
    while time.monotonic() < end:
        value = read()
        if predicate(value):
            return value
        if any(r.get('status') == 'ERROR' for r in value.values()):
            raise RuntimeError('INITIATIVE_ERROR')
        Event().wait(0.05)
    raise RuntimeError('INITIATIVE_TIMEOUT')


def run():
    started = datetime.now(timezone.utc)
    views, delayed, conflict = fixture((started-timedelta(minutes=1)).isoformat(),
                                       (started+timedelta(hours=1)).isoformat())
    processes = []
    with tempfile.TemporaryDirectory(prefix='genius-bottom-up-') as temp:
        try:
            for view in views:
                node = Process(Path(temp)/view['owner'], view['owner'])
                processes.append(node)
                node.call('/observe-views', dict(records=[view]))
            for node in processes:
                node.call('/peers', dict(peers=[p.descriptor() for p in processes if p is not node]))
                node.call('/initiative-start', dict(id='trial', world_id='pumping-study', focus=['pump'],
                                                   cycles=64, interval_ms=150))
            def read(nodes=None):
                return {p.name:p.call('/initiative-status',dict(id='trial')) for p in (processes if nodes is None else nodes)}
            incomplete = wait_for(read, lambda rows: all(len(r['current']['view_hashes']) == 3 for r in rows.values()))
            # The harness injects an environmental observation, never a sync order.
            processes[1].call('/observe-views', dict(records=[delayed]))
            complete = wait_for(read, lambda rows: all(r['current']['model_sha256'] is not None for r in rows.values()))
            model = processes[0].call('/project-world', dict(world_id='pumping-study',focus=['pump'],mode='connected'))['model']
            processes[1].close()
            live = [processes[0], processes[2]]
            offline = wait_for(lambda:read(live), lambda rows: all(any(t['peer']=='energy' and t['outcome']=='UNAVAILABLE_OR_REJECTED' for t in r['ticks']) for r in rows.values()))
            processes[0].call('/observe-views', dict(records=[conflict]))
            blocked = wait_for(lambda:read(live), lambda rows: all(any(q['code']=='FRAGMENT_CONFLICT' for q in r['current']['questions']) for r in rows.values()))
            finished = wait_for(lambda:read(live), lambda rows: all(r['status']=='BUDGET_EXHAUSTED' for r in rows.values()))
            # Projections can be replayed from the recorded views by another reader.
            from .views import compose
            from genius_twin import registry, stockflow
            replay = compose(views+[delayed], 'pumping-study', ['pump'], now())
            traces = stockflow.compute_trajectories(model)
            native = registry.evaluate(model)
            paths = {p:[d['stocks']['delivered'] for d in traces[p]['available']['daily']] for p in traces}
            checks = dict(
                three_processes=len({p.process.pid for p in processes})==3,
                missing_evidence_not_invented=all(r['current']['model_sha256'] is None for r in incomplete.values()),
                local_inquiries_reconstruct_same_model=all(r['current']['model_sha256']==digest(model) for r in complete.values()),
                delayed_evidence_detected=all(len(r['current']['view_hashes'])==4 for r in complete.values()),
                no_domain_message_sequence=all(any(t['reason']=='MODEL_INCOMPLETE' for t in r['ticks']) for r in complete.values()),
                independent_oracle=paths['restore_supply']==['1/1','1/1','1/1','3/1'] and paths['wait']==['1/1']*4,
                all_nodes_execute_native_kernel=all(r['calculations'][0]['native_verification']['valid'] for r in complete.values()),
                replay_matches=replay['model']==model and native['verification']['valid'],
                disconnection_retains_current_model=all(r['current']['model_sha256']==digest(model) for r in offline.values()),
                contradiction_suspends_current_calculation=all(r['current']['model_sha256'] is None for r in blocked.values()),
                previous_calculation_is_audit_only=all(r['last_calculated_model']==digest(model) for r in blocked.values()),
                no_relay_multiplication=all(len(r['current']['view_hashes'])==5 and r['current']['coverage']['unique_entities']==6 for r in finished.values()),
                finite_budget=all(r['cycles']==64 and r['http_requests']<=128 for r in finished.values()),
                no_probabilities_or_action=model['law'] is None and all(not r['physical_actions'] for r in finished.values()))
            if not all(checks.values()):
                raise RuntimeError('BOTTOM_UP_CHECK_FAILED: '+str(checks))
            return dict(format='genius-bottom-up-experiment/1', status='PASS', started_at=started.isoformat(),
                completed_at=now(), checks=checks, views=views, delayed=delayed, conflict=conflict,
                checkpoints={name:{n:r['current'] for n,r in rows.items()} for name,rows in
                             [('incomplete',incomplete),('complete',complete),('offline',offline),('blocked',blocked)]},
                receipts=finished, stopped_energy=complete['energy'], model_sha256=digest(model),
                trajectories=traces, native_verification=native['verification'],
                measurements=dict(baseline_prediction=None, declared_synthetic_target='3/1',
                    calculated_final_delivery=paths['restore_supply'][-1], prediction_improvement='NOT_MEASURABLE_FROM_INCOMPLETE_BASELINE',
                    peer_http_requests={n:r['http_requests'] for n,r in finished.items()},
                    metric_scope='PEER_READS_ONLY_EXCLUDES_HARNESS_MONITORING'),
                source_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(Path(__file__).parent.glob('*.py'))},
                scope='SYNTHETIC_LATE_EVIDENCE_SAME_OPERATOR_LOOPBACK', physical_actions=False,
                empirical_validation='NOT_ASSESSED', life_sustainment_effect='UNMEASURED',
                interpretation='MANUAL_IDENTITIES_MECHANISMS_AND_CANDIDATE_ROUTES',
                state_cleanup='TEMPORARY_LAB_ONLY')
        finally:
            for node in processes:
                node.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        parser.error('Output must not exist')
    report = run()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print(json.dumps(dict(status=report['status'], checks=report['checks'], measurements=report['measurements'])))


if __name__ == '__main__':
    main()
