"""Three real local processes; deterministic synthetic, non-blind experiment."""
import argparse
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from fractions import Fraction
import json
import os
from pathlib import Path
import secrets
import selectors
import subprocess
import sys
import tempfile

from .core import canonical, digest, now
from .transport import request


def observation(ctx, origin, event, value, *, observed_at, valid_until, shareable=True):
    return dict(format='genius-node-observation/1', context=deepcopy(ctx),
                source=dict(origin=origin, event=event, excerpt=f'Synthetic event {event}: value={value}'),
                value=value, observed_at=observed_at, valid_until=valid_until, shareable=shareable)


class Process:
    def __init__(self, state, name, credentials=None):
        self.name, self.state = name, Path(state)
        self.credentials = credentials or dict(admin_token=secrets.token_hex(24), read_token=secrets.token_hex(24))
        root = Path(__file__).resolve().parents[2]
        env = dict(PATH=os.defpath, PYTHONPATH=os.pathsep.join(str(root/p) for p in ('adaptive','twin','kernel')),
                   PYTHONDONTWRITEBYTECODE='1', PYTHONUNBUFFERED='1', LANG='C.UTF-8')
        self.process = subprocess.Popen([sys.executable, '-m', 'federation.transport',
            '--state', str(self.state), '--node-id', name], stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, env=env)
        try:
            self.process.stdin.write(canonical(self.credentials)+b'\n')
            self.process.stdin.close()
            with selectors.DefaultSelector() as selector:
                selector.register(self.process.stdout, selectors.EVENT_READ)
                if not selector.select(10):
                    raise RuntimeError('NODE_START_TIMEOUT')
            ready = json.loads(self.process.stdout.readline(1024))
            if ready['node_id'] != name:
                raise RuntimeError('NODE_IDENTITY_MISMATCH')
            self.port = ready['port']
        except Exception:
            self.close()
            raise

    def call(self, path, payload=None, *, peer=False):
        return request(self.port, self.credentials['read_token' if peer else 'admin_token'],
                       'GET' if payload is None else 'POST', path, payload)

    def descriptor(self):
        return dict(node_id=self.name, port=self.port, read_token=self.credentials['read_token'])

    def close(self):
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(5)
        if self.process.stdout:
            self.process.stdout.close()


def comparison(scores):
    from genius_adaptive.contextual import comparison_model
    from genius_twin.registry import evaluate
    metrics = {}
    for mode in ('isolated', 'connected'):
        rows = [score for score in scores if score['forecast']['request']['mode'] == mode]
        metrics[mode] = dict(count=len(rows), absolute_error_sum=sum(r['absolute_error'] for r in rows),
                             max_underprediction=max(r['underprediction'] for r in rows))
        metrics[mode]['mean_absolute_error'] = str(Fraction(metrics[mode]['absolute_error_sum'], len(rows)))
    model = comparison_model(metrics)
    model['name'] = 'Federación local: comparación operacional de errores congelados'
    for assumption in model['assumptions']:
        assumption['provenance'] = 'GENIUS_FEDERATION_LAB_V1'
    native = evaluate(model)
    best = min(metrics, key=lambda name: metrics[name]['absolute_error_sum'])
    tied = len({row['absolute_error_sum'] for row in metrics.values()}) == 1
    if (not native['verification']['valid'] or
        native['canonical_results']['decision']['selected'] != (None if tied else best)):
        raise RuntimeError('NATIVE_COMPARISON_MISMATCH')
    return dict(metrics=metrics, native_verification=native['verification'],
                native_decision=native['canonical_results']['decision'], model=model,
                model_sha256=digest(model),
                improvement_observed=metrics['connected']['absolute_error_sum'] < metrics['isolated']['absolute_error_sum'])


def run():
    start = datetime.now(timezone.utc)
    observed = (start-timedelta(hours=1)).isoformat()
    expires = (start+timedelta(hours=2)).isoformat()
    end = (start+timedelta(minutes=10)).isoformat()
    contexts = {name: dict(system='synthetic-system-'+name, variable='resource_requirement',
                          unit='resource_unit', regime='declared-stable-v1', data_kind='synthetic')
                for name in ('helpful', 'harmful', 'conflict', 'private')}
    processes = []
    with tempfile.TemporaryDirectory(prefix='genius-federation-') as temp:
        try:
            nodes = []
            for name in ('alpha','beta','gamma'):
                process = Process(Path(temp)/name, name)
                processes.append(process)
                nodes.append(process)
            def obs(ctx, origin, event, value, **kw):
                return observation(ctx, origin, event, value, observed_at=observed, valid_until=expires, **kw)
            training = ((20,), (80,100), (100,120))
            for index, node in enumerate(nodes):
                rows = [obs(contexts['helpful'], 'fixture:'+node.name, 'help-'+str(i), value)
                        for i, value in enumerate(training[index])]
                rows.append(obs(contexts['harmful'], 'fixture:'+node.name, 'harm', (0,100,100)[index]))
                if index == 0:
                    rows.append(obs(contexts['private'], 'fixture:private', 'private', 999, shareable=False))
                    stale = obs(contexts['helpful'], 'fixture:stale', 'stale', 999)
                    stale['valid_until'] = (start-timedelta(minutes=1)).isoformat()
                    rows.append(stale)
                node.call('/observe', dict(records=rows))
                node.call('/peers', dict(peers=[p.descriptor() for p in nodes if p is not node]))
            forecasts = []
            def freeze(node, name, mode, label=None):
                return node.call('/predict', dict(id=label or name+'-'+mode, context=contexts[name],
                    mode=mode, target_after=None, target_before=end))
            # Freeze local baselines before any exchange. Targets are disclosed
            # fixtures in this program, but are not sent to nodes until later.
            for node in nodes:
                for name in ('helpful','harmful'):
                    forecasts.append(freeze(node, name, 'isolated'))
            exchanges = []
            for node in nodes:
                for peer in nodes:
                    if peer is not node:
                        receipt = node.call('/sync', dict(node_id=peer.name))
                        if receipt['status'] != 'EXCHANGED':
                            raise RuntimeError('EXCHANGE_FAILED')
                        exchanges.append(dict(receiver=node.name, **receipt))
            for node in nodes:
                for name in ('helpful','harmful'):
                    forecasts.append(freeze(node, name, 'connected'))
            scores = {name: [] for name in ('helpful','harmful')}
            for name, value in (('helpful',100), ('harmful',0)):
                target = observation(contexts[name], 'fixture:held-out', name, value,
                                     observed_at=now(), valid_until=expires)
                for node in nodes:
                    for mode in ('isolated','connected'):
                        scores[name].append(node.call('/target', dict(id=name+'-'+mode, target=target)))
            reports = {name: comparison(rows) for name, rows in scores.items()}
            # Exercise a re-relay loop: identical evidence cannot multiply votes.
            duplicate = nodes[0].call('/sync', dict(node_id='gamma'))
            if duplicate['inserted'] != 0:
                raise RuntimeError('DUPLICATION_GUARD_FAILED')
            private_absent = all(r['context'] != contexts['private'] for r in nodes[1].call('/experiences')['records'])
            # Conflicting versions of a single declared event suspend inference.
            for node, value in zip(nodes[:2], (40,90)):
                node.call('/observe', dict(records=[obs(contexts['conflict'], 'fixture:shared-source', 'same-event', value)]))
            nodes[0].call('/sync', dict(node_id='beta'))
            conflict = freeze(nodes[0], 'conflict', 'connected')
            # Stop gamma: alpha can still produce a forecast from its own memory.
            nodes[2].close()
            offline = nodes[0].call('/sync', dict(node_id='gamma'))
            continued = freeze(nodes[0], 'helpful', 'connected', 'after-disconnection')
            # Restart alpha with the same local database: frozen forecasts/results survive.
            original = nodes[0]
            original.close()
            restored = Process(original.state, original.name, original.credentials)
            processes.append(restored)
            replay = freeze(restored, 'helpful', 'connected')
            original_forecast = next(f for f in forecasts if f['node_id']=='alpha' and f['id']=='helpful-connected')
            checks = dict(three_distinct_processes=len({p.process.pid for p in nodes}) == 3,
                separate_databases=len({p.state for p in nodes}) == 3,
                duplicate_does_not_add_evidence=duplicate['inserted'] == 0,
                private_observation_not_exported=private_absent,
                conflicts_suspend_forecast=conflict['status'] == 'CONFLICT_REVIEW' and conflict['estimate'] is None,
                disconnection_preserves_memory=offline['status']=='UNAVAILABLE_OR_REJECTED',
                continues_without_peer=continued['estimate'] == original_forecast['estimate'],
                restart_preserves_frozen_receipt=replay == original_forecast,
                helpful_fixture_improves=reports['helpful']['improvement_observed'],
                harmful_fixture_does_not_improve=not reports['harmful']['improvement_observed'])
            if not all(checks.values()):
                raise RuntimeError('EXPERIMENT_CHECK_FAILED')
            return dict(format='genius-federation-experiment/1', status='PASS', started_at=start.isoformat(),
                completed_at=now(), nodes=[p.name for p in nodes], checks=checks,
                comparisons=reports, forecasts=forecasts, scores=scores, exchanges=exchanges,
                shared_evidence=restored.call('/experiences')['records'],
                conflict=conflict, offline=offline, duplicate=duplicate,
                source_sha256={p.name: __import__('hashlib').sha256(p.read_bytes()).hexdigest()
                               for p in sorted(Path(__file__).parent.glob('*.py'))},
                scope='THREE_LOCAL_PROCESSES_SAME_OPERATOR_SYNTHETIC_NON_BLIND',
                discovery='EXPLICITLY_ENROLLED_PEERS', autonomous_learning='FIXED_ESTIMATOR_ONLY',
                statistical_generalization='NOT_ESTABLISHED', life_sustainment_effect='UNMEASURED',
                physical_actions=False, credentials_in_report=False, state_cleanup='TEMPORARY_LAB_ONLY')
        finally:
            for process in processes:
                process.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    if args.out.exists():
        parser.error('Output must not already exist')
    result = run()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps(dict(status=result['status'], checks=result['checks'],
                         comparisons={k:v['metrics'] for k,v in result['comparisons'].items()})))


if __name__ == '__main__':
    main()
