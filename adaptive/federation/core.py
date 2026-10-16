"""Bounded local memory, provenance-preserving exchange and frozen forecasts.

Origin/event identifiers are supplied by operators. They deduplicate declared
events, not establish statistical independence or attest empirical truth.
"""
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sqlite3

MAX_BYTES = 262144
MAX_RECORDS = 128
MAX_FORECASTS = 32
MAX_PEERS = 8
RULE = 'MATCHED_CONTEXT_LOWER_MEDIAN_V1'


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False,
                      allow_nan=False).encode('utf-8')


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def decode(raw):
    if len(raw) > MAX_BYTES:
        raise ValueError('MESSAGE_LIMIT')
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('DUPLICATE_FIELD')
            result[key] = value
        return result
    def reject(_):
        raise ValueError('NON_INTEGER_NUMBER')
    return json.loads(raw, object_pairs_hook=unique, parse_float=reject, parse_constant=reject)


def fields(value, names):
    if type(value) is not dict or set(value) != set(names.split()):
        raise ValueError('INVALID_FIELDS')


def text(value, limit=160):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ValueError('INVALID_TEXT')
    value.encode('utf-8')
    return value


def identifier(value):
    if not isinstance(value, str) or re.fullmatch(r'[a-zA-Z0-9_-]{1,64}', value) is None:
        raise ValueError('INVALID_ID')
    return value


def integer(value, maximum=1000000):
    if type(value) is not int or not 0 <= value <= maximum:
        raise ValueError('INVALID_INTEGER')
    return value


def now():
    return datetime.now(timezone.utc).isoformat()


def instant(value):
    text(value, 40)
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if result.tzinfo is None:
        raise ValueError('TIMEZONE_REQUIRED')
    return result


def context(value):
    fields(value, 'system variable unit regime data_kind')
    for entry in value.values():
        text(entry)
    if value['data_kind'] not in ('synthetic', 'reported'):
        raise ValueError('UNATTESTED_DATA_KIND')


def validate(record):
    fields(record, 'format context source value observed_at valid_until shareable')
    if record['format'] != 'genius-node-observation/1':
        raise ValueError('UNSUPPORTED_FORMAT')
    context(record['context'])
    fields(record['source'], 'origin event excerpt')
    text(record['source']['origin'], 256)
    text(record['source']['event'])
    text(record['source']['excerpt'], 512)
    integer(record['value'])
    if instant(record['valid_until']) <= instant(record['observed_at']):
        raise ValueError('INVALID_VALIDITY')
    if type(record['shareable']) is not bool:
        raise ValueError('SHARING_DECISION_REQUIRED')
    if len(canonical(record)) > 1600:
        raise ValueError('RECORD_LIMIT')


def event_key(record):
    return digest({key: record['source'][key] for key in ('origin', 'event')})


class Node:
    def __init__(self, directory, node_id, clock=now):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.node_id, self.clock = identifier(node_id), clock
        self.path = self.directory / 'memory.sqlite3'
        with self.db() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS identity (id TEXT PRIMARY KEY);
                CREATE TABLE IF NOT EXISTS records (
                    hash TEXT PRIMARY KEY, event TEXT NOT NULL, body TEXT NOT NULL,
                    local INTEGER NOT NULL, received_at TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS receipts (
                    hash TEXT NOT NULL, via TEXT NOT NULL, PRIMARY KEY(hash,via));
                CREATE TABLE IF NOT EXISTS forecasts (
                    id TEXT PRIMARY KEY, body TEXT NOT NULL, result TEXT);
                CREATE TABLE IF NOT EXISTS world_views (
                    hash TEXT PRIMARY KEY, body TEXT NOT NULL, local INTEGER NOT NULL,
                    received_at TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS view_receipts (
                    hash TEXT NOT NULL, via TEXT NOT NULL, PRIMARY KEY(hash,via));
            ''')
            rows = db.execute('SELECT id FROM identity').fetchall()
            if rows and rows != [(self.node_id,)]:
                raise ValueError('NODE_IDENTITY_CONFLICT')
            db.execute('INSERT OR IGNORE INTO identity VALUES (?)', (self.node_id,))
        self.path.chmod(0o600)

    @contextmanager
    def db(self):
        db = sqlite3.connect(self.path, timeout=3)
        try:
            with db:
                yield db
        finally:
            db.close()

    def ingest(self, records, via=None):
        if type(records) is not list or not 1 <= len(records) <= MAX_RECORDS:
            raise ValueError('BATCH_LIMIT')
        if via is not None:
            identifier(via)
            if via == self.node_id:
                raise ValueError('SELF_PEER')
        prepared = []
        received = self.clock()
        for record in records:
            validate(record)
            if instant(record['observed_at']) > instant(received):
                raise ValueError('FUTURE_OBSERVATION')
            if via and not record['shareable']:
                raise ValueError('PRIVATE_IMPORT')
            prepared.append((digest(record), event_key(record), canonical(record).decode()))
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            known = {row[0] for row in db.execute('SELECT hash FROM records')}
            incoming = {row[0] for row in prepared}
            if len(known | incoming) > MAX_RECORDS:
                raise ValueError('MEMORY_BUDGET')
            if via:
                peers = {row[0] for row in db.execute('SELECT DISTINCT via FROM receipts')}
                if len(peers | {via}) > MAX_PEERS:
                    raise ValueError('PEER_BUDGET')
            for hash_, event, body in prepared:
                db.execute('INSERT OR IGNORE INTO records VALUES (?,?,?,?,?)',
                           (hash_, event, body, int(via is None), received))
                if via is None:
                    db.execute('UPDATE records SET local=1 WHERE hash=?', (hash_,))
                else:
                    db.execute('INSERT OR IGNORE INTO receipts VALUES (?,?)', (hash_, via))
            return dict(inserted=len(incoming-known), duplicates=len(prepared)-len(incoming-known))

    def export(self):
        with self.db() as db:
            rows = [json.loads(row[0]) for row in db.execute('SELECT body FROM records ORDER BY hash')]
        return [record for record in rows if record['shareable']]

    def hello(self):
        with self.db() as db:
            count = db.execute('SELECT count(*) FROM records').fetchone()[0]
            view_count = db.execute('SELECT count(*) FROM world_views').fetchone()[0]
        return dict(format='genius-node-hello/1', node_id=self.node_id,
                    capabilities=['observation_exchange_v1', 'partial_world_exchange_v1', 'local_evidence_inquiry_v1', RULE],
                    remaining_records=MAX_RECORDS-count, max_records=MAX_RECORDS,
                    remaining_views=8-view_count,
                    physical_actions=False, deployment='LOOPBACK_LAB',
                    source_attestation='NONE', code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())

    def ingest_views(self, records, via=None):
        from .views import ingest
        return ingest(self,records,via)

    def export_views(self):
        from .views import export
        return export(self)

    def project_world(self, world_id, focus, mode):
        from .views import project
        return project(self,world_id,focus,mode)

    def predict(self, forecast_id, ctx, mode, target_after, target_before):
        identifier(forecast_id)
        context(ctx)
        if mode not in ('isolated', 'connected'):
            raise ValueError('INVALID_MODE')
        requested = dict(context=ctx, mode=mode, target_after=target_after, target_before=target_before)
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            previous = db.execute('SELECT body FROM forecasts WHERE id=?', (forecast_id,)).fetchone()
            if previous:
                previous = json.loads(previous[0])
                if previous['request'] != requested:
                    raise ValueError('FORECAST_ID_CONFLICT')
                return previous
            frozen_at = self.clock()
            if not instant(frozen_at) <= instant(target_after or frozen_at) < instant(target_before):
                raise ValueError('FUTURE_TARGET_WINDOW_REQUIRED')
            if db.execute('SELECT count(*) FROM forecasts').fetchone()[0] >= MAX_FORECASTS:
                raise ValueError('FORECAST_BUDGET')
            rows = db.execute('SELECT hash,event,body,local,received_at FROM records ORDER BY hash').fetchall()
            groups = {}
            excluded = dict(stale=0, context_mismatch=0, remote=0)
            for hash_, event, raw, local, received_at in rows:
                record = json.loads(raw)
                if max(instant(received_at), instant(record['observed_at'])) > instant(frozen_at):
                    raise ValueError('CLOCK_REGRESSION')
                # Connected memory never rewrites the counterfactual local baseline.
                if mode == 'isolated' and not local:
                    excluded['remote'] += 1
                    continue
                groups.setdefault(event, []).append((hash_, record))
            included, conflicts = [], []
            for event, variants in sorted(groups.items()):
                matching = [(hash_, r) for hash_, r in variants if r['context'] == ctx]
                if not matching:
                    excluded['context_mismatch'] += len(variants)
                    continue
                # Any competing version of a relevant event requires review, even
                # if its rival changes context/expiry to hide the contradiction.
                if len(variants) > 1:
                    conflicts.append(event)
                    continue
                hash_, record = matching[0]
                if instant(record['valid_until']) < instant(target_before):
                    excluded['stale'] += 1
                    continue
                included.append(dict(hash=hash_, event=event, value=record['value']))
            values = sorted(row['value'] for row in included)
            status = 'CONFLICT_REVIEW' if conflicts else 'FROZEN' if values else 'INSUFFICIENT_EVIDENCE'
            receipt = dict(format='genius-node-forecast/1', node_id=self.node_id, id=forecast_id,
                           request=requested, rule=RULE, frozen_at=frozen_at, status=status,
                           estimate=values[(len(values)-1)//2] if status == 'FROZEN' else None,
                           evidence=included, conflicts=conflicts, excluded=excluded,
                           source_attestation='NONE', statistical_independence='NOT_ESTABLISHED',
                           prediction_probability=None, physical_actions=False)
            receipt['sha256'] = digest(receipt)
            db.execute('INSERT INTO forecasts VALUES (?,?,NULL)', (forecast_id, canonical(receipt).decode()))
            return receipt

    def observe_target(self, forecast_id, target):
        identifier(forecast_id)
        validate(target)
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT body,result FROM forecasts WHERE id=?', (forecast_id,)).fetchone()
            if row is None:
                raise ValueError('UNKNOWN_FORECAST')
            forecast = json.loads(row[0])
            if row[1]:
                result = json.loads(row[1])
                if result['target_sha256'] != digest(target):
                    raise ValueError('TARGET_IMMUTABLE')
                return result
            if forecast['status'] != 'FROZEN':
                raise ValueError('FORECAST_NOT_READY')
            request = forecast['request']
            received = self.clock()
            observed = instant(target['observed_at'])
            if (target['context'] != request['context'] or
                not instant(forecast['frozen_at']) < observed or
                not instant(request['target_after'] or forecast['frozen_at']) <= observed <= instant(request['target_before']) or
                observed > instant(received) or
                event_key(target) in {r['event'] for r in forecast['evidence']}):
                raise ValueError('TARGET_NOT_POSTERIOR_OR_COMPATIBLE')
            result = dict(format='genius-node-score/1', forecast=forecast,
                          target=target, target_sha256=digest(target), received_at=received,
                          absolute_error=abs(forecast['estimate']-target['value']),
                          underprediction=max(0, target['value']-forecast['estimate']),
                          effect_on_life='UNMEASURED')
            db.execute('UPDATE forecasts SET result=? WHERE id=?', (canonical(result).decode(), forecast_id))
            return result
