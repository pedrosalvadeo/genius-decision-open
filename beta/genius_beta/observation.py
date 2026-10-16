"""Private, read-only summaries of the retained regulation journal.

Shared by the private operator endpoint and CLI. Inputs/IDs/tokens/results are
neither queried nor emitted. Counts describe retained records, never complete traffic.
"""
import argparse
from collections import Counter
import contextlib
import json
import math
import os
from pathlib import Path
import sqlite3
import time

from genius_beta.regulation import FORMAT, POLICY, POLICY_SHA

MODES = frozenset(('OBSERVING', 'NORMAL', 'DRAINING', 'RESOURCE_PAUSED',
                   'COOLDOWN', 'PROBING', 'SENSOR_PAUSED', 'REVIEW_REQUIRED'))
STATUSES = ('draft', 'queued', 'running', 'completed', 'interrupted', 'failed',
            'needs_review', 'cancelled')
OUTCOMES = ('completed', 'operational_failure', 'neutral')
KINDS = ('transition', 'execution_started', 'execution_finished',
         'execution_interrupted')
MAX_JSON_BYTES = 16384


class ObservationError(ValueError):
    """Fixed error codes only: never echo a private path or database content."""


def require(condition, code):
    if not condition:
        raise ObservationError(code)


def natural(value):
    return type(value) is int and value >= 0


def decode(raw):
    require(isinstance(raw, str), 'INVALID_OR_OVERSIZED_RECORD')
    try:
        value = json.loads(raw)
    except (ValueError, RecursionError):
        raise ObservationError('INVALID_RECORD_JSON') from None
    require(isinstance(value, dict), 'INVALID_RECORD_OBJECT')
    require(value.get('format') == FORMAT and value.get('policy_sha256') == POLICY_SHA,
            'UNSUPPORTED_RECORD_IDENTITY')
    require(isinstance(value.get('mode'), str) and value['mode'] in MODES,
            'UNSUPPORTED_RECORDED_MODE')
    require(natural(value.get('observed_at')), 'INVALID_OBSERVATION_TIME')
    require(value.get('reason') != 'CLOCK_MOVED_BACKWARD', 'INCOHERENT_CLOCK')
    return value


def durations(values):
    """Nearest-rank percentiles of recorded whole-second elapsed values only."""
    ordered = sorted(values)
    if not ordered:
        return dict(count=0, min=None, p50=None, p95=None, max=None)
    return dict(count=len(ordered), min=ordered[0],
                p50=ordered[math.ceil(len(ordered)*0.50)-1],
                p95=ordered[math.ceil(len(ordered)*0.95)-1], max=ordered[-1])


def read_snapshot(path):
    """One SQLite read transaction, including the active WAL; never migrate."""
    path = Path(path).resolve()
    require(path.is_file(), 'DATABASE_NOT_FOUND')
    try:
        with contextlib.closing(sqlite3.connect(path.as_uri()+'?mode=ro',
                                              uri=True, timeout=3, isolation_level=None)) as db:
            db.execute('PRAGMA query_only=ON')
            db.execute('PRAGMA trusted_schema=OFF')
            # A bounded VM budget avoids a long read transaction on an unexpected DB.
            budget = 2000
            def progress():
                nonlocal budget
                budget -= 1
                return budget <= 0
            db.set_progress_handler(progress, 10000)
            db.execute('BEGIN')
            tables = {r[0] for r in db.execute(
                "SELECT name FROM sqlite_schema WHERE type='table' AND name IN "
                "('mission_regulation','mission_regulation_events','adaptive_missions')")}
            require(len(tables) == 3, 'OBSERVATION_SCHEMA_UNAVAILABLE')
            state = db.execute('SELECT CASE WHEN length(CAST(state_json AS BLOB))<=? '
                'THEN state_json END FROM mission_regulation WHERE singleton=1',
                (MAX_JSON_BYTES,)).fetchone()
            rows = db.execute('SELECT sequence,created_at,kind,CASE WHEN '
                'length(CAST(receipt_json AS BLOB))<=? THEN receipt_json END '
                'FROM mission_regulation_events ORDER BY sequence LIMIT ?',
                (MAX_JSON_BYTES, POLICY['retained_events']+1)).fetchall()
            require(len(rows) <= POLICY['retained_events'], 'JOURNAL_BOUND_EXCEEDED')
            missions = dict(db.execute('SELECT status,count(*) FROM adaptive_missions GROUP BY status'))
            db.rollback()
        return state, rows, missions
    except sqlite3.Error:
        raise ObservationError('DATABASE_READ_UNAVAILABLE') from None


def report(database, *, since, until, source='production', now=None):
    """Report [since, until); the separate mission/state snapshot is current."""
    require(natural(since) and natural(until) and since < until, 'INVALID_WINDOW')
    require(source in ('production', 'synthetic'), 'INVALID_SOURCE_DECLARATION')
    raw_state, rows, missions = read_snapshot(database)
    now = int(time.time()) if now is None else now
    require(natural(now) and until <= now, 'WINDOW_AFTER_SNAPSHOT')
    require(set(missions) <= set(STATUSES), 'UNSUPPORTED_MISSION_STATUS')
    counts = Counter()
    elapsed = {outcome: [] for outcome in OUTCOMES}
    previous_sequence, previous_time, gaps = None, None, 0
    for sequence, created_at, kind, raw in rows:
        require(natural(sequence) and sequence > 0 and natural(created_at), 'INVALID_EVENT_POSITION')
        receipt = decode(raw)
        require(kind in KINDS, 'UNSUPPORTED_EVENT_KIND')
        require(receipt['observed_at'] == created_at and created_at <= now, 'INCOHERENT_CLOCK')
        if previous_sequence is not None:
            require(sequence > previous_sequence, 'INVALID_EVENT_POSITION')
            require(created_at >= previous_time, 'INCOHERENT_CLOCK')
            gaps += sequence-previous_sequence-1
        previous_sequence, previous_time = sequence, created_at
        if kind == 'execution_finished':
            require(receipt.get('outcome') in OUTCOMES, 'UNSUPPORTED_EXECUTION_OUTCOME')
            require(natural(receipt.get('elapsed_seconds')), 'INVALID_RECORDED_DURATION')
            require(receipt['elapsed_seconds'] <= created_at, 'INVALID_RECORDED_DURATION')
        if kind == 'execution_interrupted':
            require(receipt.get('outcome') == 'UNKNOWN_AFTER_WORKER_RESTART',
                    'UNSUPPORTED_INTERRUPTION_OUTCOME')
        if since <= created_at < until:
            counts[kind] += 1
            if kind == 'execution_finished':
                counts[receipt['outcome']] += 1
                elapsed[receipt['outcome']].append(receipt['elapsed_seconds'])

    snapshot = dict(record_present=False, enabled_in_runtime=None, mode=None,
                    observed_at=None, freshness='unobserved', active_attempt=None,
                    active_age_seconds=None, consecutive_operational_failures=None)
    if raw_state:
        state = decode(raw_state[0])
        require(state['observed_at'] <= now, 'INCOHERENT_CLOCK')
        require(natural(state.get('failures')), 'INVALID_PERSISTED_FAILURE_COUNT')
        require('active' in state and 'started_at' in state, 'INVALID_ACTIVE_MARKER')
        active = state.get('active')
        started = state.get('started_at')
        require(active is None or (isinstance(active, str) and bool(active)), 'INVALID_ACTIVE_MARKER')
        if active is not None:
            require(natural(started) and started <= now, 'INCOHERENT_ACTIVE_CLOCK')
        else:
            require(started is None, 'INVALID_ACTIVE_MARKER')
        observed = state['observed_at']
        snapshot.update(record_present=True, mode=state['mode'], observed_at=observed or None,
            freshness=('unobserved' if observed == 0 else 'fresh' if now-observed <= POLICY['stale_seconds'] else 'stale'),
            active_attempt=active is not None, active_age_seconds=now-started if active is not None else None,
            consecutive_operational_failures=state['failures'])

    all_elapsed = [v for values in elapsed.values() for v in values]
    return dict(format='genius-regulation-observation/1',
        source=dict(declared=source, independently_verified=False),
        classification='PRIVATE_OPERATOR_REPORT', policy_sha256=POLICY_SHA,
        requested_window=dict(since_inclusive=since, until_exclusive=until),
        snapshot_captured_at=now,
        coverage=dict(complete_window_proven=False, retained_events=len(rows),
            events_in_window=sum(counts[k] for k in KINDS),
            first_retained_at=rows[0][1] if rows else None,
            last_retained_at=rows[-1][1] if rows else None,
            deleted_prefix_detected=bool(rows and rows[0][0] > 1),
            internal_missing_sequences=gaps,
            record_limit_reached=len(rows) == POLICY['retained_events'],
            requested_start_older_than_retention=since < now-POLICY['retention_seconds'],
            retention_seconds=POLICY['retention_seconds'], event_limit=POLICY['retained_events']),
        retained_window_events=dict(started=counts['execution_started'],
            finished={outcome: counts[outcome] for outcome in OUTCOMES},
            interrupted_unknown=counts['execution_interrupted'], transitions=counts['transition']),
        recorded_elapsed_seconds=dict(method='nearest_rank', all_finished=durations(all_elapsed),
            by_outcome={outcome: durations(elapsed[outcome]) for outcome in OUTCOMES}),
        current_snapshot=dict(regulator=snapshot,
            stored_missions_by_status={status: missions.get(status, 0) for status in STATUSES},
            pending_missions=missions.get('queued', 0)+missions.get('running', 0)),
        unavailable_metrics=['queue_wait_seconds', 'rejected_admissions', 'total_arrival_demand',
            'pending_time_integral', 'downtime_seconds', 'counterfactual_policy_gain',
            'wellbeing_or_life_sustainability'],
        eligible_for_policy_promotion=False)


def write_private(path, value):
    """Exclusive create, 0600; never overwrite an existing report or follow a link."""
    payload = (json.dumps(value, sort_keys=True, indent=2, allow_nan=False)+'\n').encode()
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, 'wb') as output:
            output.write(payload)
    except BaseException:
        Path(path).unlink(missing_ok=True)
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', required=True, type=Path)
    parser.add_argument('--since', required=True, type=int, help='Inclusive Unix second')
    parser.add_argument('--until', required=True, type=int, help='Exclusive Unix second')
    parser.add_argument('--source', choices=('production', 'synthetic'), default='production')
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        value = report(args.database, since=args.since, until=args.until, source=args.source)
        write_private(args.output, value)
    except ObservationError as exc:
        print(json.dumps(dict(status='NOT_WRITTEN', error=str(exc))))
        return 1
    except OSError:
        print(json.dumps(dict(status='NOT_WRITTEN', error='PRIVATE_FILE_ACCESS_UNAVAILABLE')))
        return 1
    print(json.dumps(dict(status='WRITTEN', classification=value['classification'],
                         complete_window_proven=False, eligible_for_policy_promotion=False)))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
