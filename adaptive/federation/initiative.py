"""Finite, opt-in peer inquiry driven by each node's own evidence state.

This is a fixed generic policy, not learned causality or self-modifying code.
Only enrolled loopback peers are consulted; source text is never executable.
"""
from copy import deepcopy
from http.client import HTTPException
import json
import re
from threading import Event, Lock, Thread

from .core import canonical, digest, fields, identifier, integer
from .views import MAX_VIEWS

MAX_CYCLES = 64
MAX_RUNS = 4
RULE = 'LOCAL_EVIDENCE_INQUIRY_V1'


def catalog(node):
    return dict(format='genius-view-index/1', node_id=node.node_id,
                views=[dict(hash=digest(v), world_id=v['world_id']) for v in node.export_views()])


def checked_index(packet, peer):
    fields(packet, 'format node_id views')
    if packet['format'] != 'genius-view-index/1' or packet['node_id'] != peer:
        raise ValueError('PEER_IDENTITY_OR_PROTOCOL')
    rows = packet['views']
    if type(rows) is not list or len(rows) > MAX_VIEWS:
        raise ValueError('INDEX_LIMIT')
    seen = set()
    for row in rows:
        fields(row, 'hash world_id')
        identifier(row['world_id'])
        if not isinstance(row['hash'], str) or not re.fullmatch('[0-9a-f]{64}', row['hash']) or row['hash'] in seen:
            raise ValueError('INDEX_HASH')
        seen.add(row['hash'])
    return rows


def summarize(projection):
    model = projection['model']
    return dict(status=projection['status'], as_of=projection['as_of'], view_hashes=projection['view_hashes'],
                questions=[dict(code=q['code']) for q in projection['questions']],
                model_sha256=digest(model) if model else None,
                coverage=deepcopy(projection.get('coverage')),
                scope_review_required=((projection.get('preparation') or {}).get('scope_receipt') or {}).get('review_required', True))


class Initiative:
    def __init__(self, node, peers, fetch):
        self.node, self.peers, self.fetch = node, peers, fetch
        self.lock, self.stop_event = Lock(), Event()
        self.thread = None
        with node.db() as db:
            db.execute('CREATE TABLE IF NOT EXISTS initiative_runs (id TEXT PRIMARY KEY, body TEXT NOT NULL)')
            rows = db.execute('SELECT id,body FROM initiative_runs').fetchall()
            for run_id, raw in rows:
                record = json.loads(raw)
                if record['status'] == 'RUNNING':
                    record['status'] = 'INTERRUPTED'
                    db.execute('UPDATE initiative_runs SET body=? WHERE id=?', (canonical(record).decode(), run_id))

    def save(self, record):
        with self.node.db() as db:
            db.execute('INSERT OR REPLACE INTO initiative_runs VALUES (?,?)',
                       (record['id'], canonical(record).decode()))

    def status(self, run_id):
        identifier(run_id)
        with self.node.db() as db:
            row = db.execute('SELECT body FROM initiative_runs WHERE id=?', (run_id,)).fetchone()
        if not row:
            raise ValueError('UNKNOWN_RUN')
        return json.loads(row[0])

    def start(self, config, *, background=True):
        fields(config, 'id world_id focus cycles interval_ms')
        identifier(config['id']); identifier(config['world_id'])
        integer(config['cycles'], MAX_CYCLES); integer(config['interval_ms'], 30000)
        if not config['cycles'] or config['interval_ms'] < 100:
            raise ValueError('INVALID_CYCLE_BUDGET')
        # Validate the focus and initial projection before starting any work.
        projection = self.node.project_world(config['world_id'], config['focus'], 'connected')
        with self.lock:
            if self.thread is not None and self.thread.is_alive():
                raise ValueError('RUN_ACTIVE')
            with self.node.db() as db:
                rows = [json.loads(r[0]) for r in db.execute('SELECT body FROM initiative_runs')]
            if any(r['status'] == 'RUNNING' for r in rows):
                raise ValueError('RUN_ACTIVE')
            if any(r['id'] == config['id'] for r in rows):
                raise ValueError('RUN_ID_USED')
            if len(rows) >= MAX_RUNS:
                raise ValueError('RUN_BUDGET')
            record = dict(format='genius-local-initiative/1', id=config['id'], node_id=self.node.node_id,
                          config=deepcopy(config), rule=RULE, status='RUNNING', started_at=self.node.clock(),
                          cycles=0, http_requests=0, imports=0, ticks=[], calculations=[],
                          current=summarize(projection), physical_actions=False,
                          empirical_validation='NOT_ASSESSED', learning='FIXED_INQUIRY_POLICY',
                          discovery='ENROLLED_LOOPBACK_PEERS', last_calculated_model=None)
            self.save(record)
            self.stop_event.clear()
            if background:
                self.thread = Thread(target=self._run, args=(config['id'],), daemon=True)
                self.thread.start()
        return self.status(config['id'])

    def _run(self, run_id):
        while not self.stop_event.is_set():
            try:
                record = self.tick(run_id)
            except Exception:
                # Preserve an audit marker, never publish a stale calculation as current.
                with self.lock:
                    record = self.status(run_id)
                    record['status'] = 'ERROR'
                    record['current'] = dict(status='NEEDS_REVISION', model_sha256=None,
                                             questions=[dict(code='CYCLE_ERROR', detail='Inspect locally; no automatic retry.')])
                    self.save(record)
                return
            if record['status'] != 'RUNNING':
                return
            self.stop_event.wait(record['config']['interval_ms'] / 1000)
        with self.lock:
            record = self.status(run_id)
            if record['status'] == 'RUNNING':
                record['status'] = 'STOPPED'
                self.save(record)

    def stop(self, run_id):
        record = self.status(run_id)
        if record['status'] != 'RUNNING':
            return record
        self.stop_event.set()
        if self.thread and self.thread.is_alive():
            return dict(id=run_id, status='STOP_REQUESTED')
        with self.lock:
            record = self.status(run_id)
            if record['status'] == 'RUNNING':
                record['status'] = 'STOPPED'
                self.save(record)
        return record

    def tick(self, run_id):
        with self.lock:
            record = self.status(run_id)
            if record['status'] != 'RUNNING':
                return record
            cfg = record['config']
            before = self.node.project_world(cfg['world_id'], cfg['focus'], 'connected')
            codes = [q['code'] for q in before['questions']]
            reason = ('EVIDENCE_REVIEW' if any(c not in ('INCOMPLETE_MODEL','NO_VIEWS') for c in codes)
                      else 'MODEL_INCOMPLETE' if before['model'] is None else 'REFRESH')
            tick = dict(cycle=record['cycles']+1, at=self.node.clock(), reason=reason,
                        questions=codes, peer=None, outcome='NO_PEERS', inserted=0, http_requests=0)
            # Round-robin is generic and fair. No domain labels or orchestrator-selected order.
            peers = sorted(self.peers().items())
            record['cycles'] += 1
            if peers:
                name, peer = peers[(record['cycles']-1) % len(peers)]
                tick['peer'] = name
                tick['outcome'] = 'INQUIRY_STARTED'
            record['ticks'].append(tick)
            self.save(record)  # Reserve the cycle before external reads; restart does not resume it.
            if peers:
                self._inquire(record, tick, peer, cfg['world_id'], set(before['view_hashes']))
                self.save(record)
            after = self.node.project_world(cfg['world_id'], cfg['focus'], 'connected')
            record['current'] = summarize(after)
            if after['model'] is not None:
                model_hash = digest(after['model'])
                if model_hash not in {c['model_sha256'] for c in record['calculations']}:
                    from genius_twin import registry, stockflow
                    native = registry.evaluate(after['model'])
                    if not native['verification']['valid']:
                        raise ValueError('NATIVE_VERIFICATION_FAILED')
                    traces = stockflow.compute_trajectories(after['model'])
                    record['calculations'].append(dict(model_sha256=model_hash,
                        view_hashes=after['view_hashes'], at=self.node.clock(),
                        native_verification=dict(valid=True),
                        selected=native['canonical_results']['decision']['selected'],
                        trajectories_sha256=digest(traces),
                        final_stocks={p:{s:t['daily'][-1]['stocks'] for s,t in scenarios.items()}
                                      for p,scenarios in traces.items()}))
                record['last_calculated_model'] = model_hash
            tick['result_status'] = after['status']
            tick['model_sha256'] = record['current']['model_sha256']
            if record['cycles'] >= cfg['cycles']:
                record['status'] = 'BUDGET_EXHAUSTED'
            self.save(record)
            return record

    def _inquire(self, record, tick, peer, world_id, known):
        def get(path):
            tick['http_requests'] += 1
            record['http_requests'] += 1
            self.save(record)
            return self.fetch(peer['port'], peer['read_token'], 'GET', path)
        try:
            rows = checked_index(get('/view-index'), tick['peer'])
            wanted = {r['hash'] for r in rows if r['world_id'] == world_id} - known
            if not wanted:
                tick['outcome'] = 'NO_NEW_RELEVANT_VIEWS'
                return
            packet = get('/views')
            fields(packet, 'node_id records')
            if packet['node_id'] != tick['peer'] or type(packet['records']) is not list or len(packet['records']) > MAX_VIEWS:
                raise ValueError('PEER_IDENTITY_OR_PROTOCOL')
            if any(type(v) is not dict for v in packet['records']):
                raise ValueError('INVALID_VIEW_PACKET')
            chosen = [v for v in packet['records'] if digest(v) in wanted and v.get('world_id') == world_id]
            # Reject an inconsistent index/read pair. Retry only in another budgeted cycle.
            if {digest(v) for v in chosen} != wanted:
                raise ValueError('INDEX_CHANGED')
            result = self.node.ingest_views(chosen, via=tick['peer'])
            tick['outcome'] = 'IMPORTED'
            tick['inserted'] = result['inserted']
            record['imports'] += result['inserted']
        except (OSError, HTTPException, ValueError, KeyError, TypeError, RecursionError):
            tick['outcome'] = 'UNAVAILABLE_OR_REJECTED'
            tick['memory_preserved'] = True
