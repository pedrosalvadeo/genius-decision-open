"""Feedback control for queued missions, not a learned policy or a global scheduler.

All mutations serialize with mission admission/claim/completion in SQLite. The
worker samples while idle, so backlog/resource recovery does not need a client.
No inputs, account IDs, tokens, task results or third-party text enter this ledger.
"""
import contextlib
import hashlib
import json
import secrets
import shutil
import time
from .db import dump, transaction

FORMAT = 'genius-mission-regulation/1'
POLICY = dict(queue_high=4, queue_low=1, storage_high_percent=85,
              storage_low_percent=70, free_margin_bytes=8*1024*1024,
              failure_threshold=3, cooldown_seconds=60, sample_seconds=5,
              stale_seconds=15, retained_events=512, retention_seconds=7*86400)
POLICY_SHA = hashlib.sha256(dump(POLICY).encode()).hexdigest()
OPERATIONAL_FAILURES = frozenset(('MISSION_TIMEOUT', 'MISSION_PROCESS_FAILED',
                                 'MISSION_PROTOCOL_FAILED', 'STORAGE_CAPACITY'))


def enabled(config):
    return config['MISSION_REGULATION_ENABLED'] and config['ADAPTIVE_ENABLED']


def initial():
    return dict(format=FORMAT, policy_sha256=POLICY_SHA, mode='OBSERVING',
                reason='FIRST_OBSERVATION_REQUIRED', observed_at=0, signals=None,
                storage_paused=False, draining=False, failures=0, cooldown_until=0,
                active=None, started_at=None)


def load(db):
    row = db.execute('SELECT state_json FROM mission_regulation WHERE singleton=1').fetchone()
    return json.loads(row[0]) if row else initial()


def compatible(state):
    return state.get('format') == FORMAT and state.get('policy_sha256') == POLICY_SHA


def save(db, state):
    assert db.in_transaction
    db.execute('INSERT INTO mission_regulation VALUES(1,?) ON CONFLICT(singleton) DO UPDATE SET state_json=excluded.state_json', (dump(state),))


def event(db, kind, state, now, **details):
    assert db.in_transaction
    receipt = dict(format=FORMAT, policy_sha256=POLICY_SHA, observed_at=now,
                   mode=state['mode'], reason=state['reason'], signals=state['signals'],
                   consecutive_operational_failures=state['failures'], **details)
    db.execute('INSERT INTO mission_regulation_events(created_at,kind,receipt_json) VALUES(?,?,?)', (now,kind,dump(receipt)))
    db.execute('DELETE FROM mission_regulation_events WHERE created_at<? OR sequence NOT IN (SELECT sequence FROM mission_regulation_events ORDER BY sequence DESC LIMIT ?)',
               (now-POLICY['retention_seconds'],POLICY['retained_events']))


def observe(db, config):
    from .twin_integration import storage_bytes
    signals = dict(storage_bytes=storage_bytes(config['DATA_DIR']),
                   free_bytes=shutil.disk_usage(config['DATA_DIR']).free,
                   pending=db.execute("SELECT count(*) FROM adaptive_missions WHERE status IN ('queued','running')").fetchone()[0])
    if any(type(v) is not int or v < 0 for v in signals.values()):
        raise OSError('INVALID_RESOURCE_OBSERVATION')
    return signals


def decide(state, signals, config, now):
    """Hysteresis avoids flapping; cooldown expiry alone never proves recovery."""
    if now < state['observed_at']:
        state.update(mode='SENSOR_PAUSED',reason='CLOCK_MOVED_BACKWARD')
        return
    state.update(observed_at=now,signals=signals)
    if signals is None:
        state.update(mode='SENSOR_PAUSED',reason='OBSERVATION_UNAVAILABLE')
        return
    size, free = signals['storage_bytes'], signals['free_bytes']
    ceiling, floor = config['MAX_DATABASE_BYTES'], config['MIN_FREE_BYTES']
    margin = POLICY['free_margin_bytes']
    if size*100 >= ceiling*POLICY['storage_high_percent'] or free < floor+margin:
        state['storage_paused'] = True
    elif size*100 <= ceiling*POLICY['storage_low_percent'] and free >= floor+2*margin:
        state['storage_paused'] = False
    if signals['pending'] >= POLICY['queue_high']:
        state['draining'] = True
    elif signals['pending'] <= POLICY['queue_low']:
        state['draining'] = False
    if state['storage_paused']:
        state.update(mode='RESOURCE_PAUSED',reason='STORAGE_PRESSURE')
    elif now < state['cooldown_until']:
        state.update(mode='COOLDOWN',reason='REPEATED_OPERATIONAL_FAILURE')
    elif state['failures'] >= POLICY['failure_threshold']:
        state.update(mode='PROBING',reason='RECOVERY_EXECUTION_REQUIRED')
    elif state['draining']:
        state.update(mode='DRAINING',reason='MISSION_BACKLOG')
    else:
        state.update(mode='NORMAL',reason='WITHIN_OPERATING_LIMITS')


def refresh(db, config, *, force=False, now=None):
    if not enabled(config):
        return dict(mode='DISABLED',reason='OPERATOR_DISABLED',active=None)
    now = int(time.time()) if now is None else now
    # Idle polling reads without taking SQLite's single-writer lock. Admission
    # and execution always force a fresh sample under their owning transaction.
    cached = load(db)
    if not force and compatible(cached) and 0 <= now-cached['observed_at'] < POLICY['sample_seconds']:
        return cached
    with (contextlib.nullcontext() if db.in_transaction else transaction(db)):
        state = load(db)
        if not compatible(state):
            return {**state, 'mode':'REVIEW_REQUIRED','reason':'POLICY_CHANGED'}
        if not force and 0 <= now-state['observed_at'] < POLICY['sample_seconds']:
            return state
        previous = dict(state)
        try:
            signals = observe(db,config)
        except OSError:
            signals = None
        decide(state,signals,config,now)
        save(db,state)
        if (state['mode'],state['reason']) != (previous['mode'],previous['reason']):
            event(db,'transition',state,now,previous_mode=previous['mode'],
                  previous_signals=previous['signals'],
                  observed_recovery=state['mode']=='NORMAL' and previous['mode'] not in ('NORMAL','OBSERVING'))
        return state


def admits(state):
    return state['mode'] in ('NORMAL','DISABLED') or (
        state['mode']=='PROBING' and state['active'] is None and state['signals']['pending']==0)


def starts(state):
    return state['mode']=='DISABLED' or (
        state['mode'] in ('NORMAL','DRAINING','PROBING') and state['active'] is None)


def begin(db, config, state):
    """Call inside the transaction that claims exactly one queued mission."""
    if not enabled(config):
        return None
    assert starts(state)
    token = secrets.token_hex(16)
    state.update(active=token,started_at=int(time.time()))
    save(db,state)
    event(db,'execution_started',state,state['started_at'],probe=state['mode']=='PROBING')
    return token


def finish(db, config, token, outcome, reason):
    if token is None:
        return
    assert db.in_transaction
    state = load(db)
    if not compatible(state) or state['active'] != token:
        raise RuntimeError('REGULATION_EXECUTION_IDENTITY_CHANGED')
    now = int(time.time())
    elapsed = max(0,now-state['started_at'])
    state.update(active=None,started_at=None)
    if outcome == 'completed':
        state.update(failures=0,cooldown_until=0)
        category = 'completed'
    elif outcome == 'failed' and reason in OPERATIONAL_FAILURES:
        state['failures'] += 1
        if state['failures'] >= POLICY['failure_threshold']:
            state['cooldown_until'] = now+POLICY['cooldown_seconds']
        category = 'operational_failure'
    else:
        # Input/domain rejection, review and cancellation are not host failures.
        category = 'neutral'
    save(db,state)
    state = refresh(db,config,force=True,now=now)
    event(db,'execution_finished',state,now,outcome=category,elapsed_seconds=elapsed)


def recover(db, config):
    """An interrupted attempt is unknown, never a successful recovery probe."""
    if not enabled(config):
        return
    with transaction(db):
        state = load(db)
        if compatible(state) and state['active'] is not None:
            now = int(time.time())
            state.update(active=None,started_at=None,
                         failures=max(POLICY['failure_threshold'],state['failures']),
                         cooldown_until=now+POLICY['cooldown_seconds'])
            save(db,state)
            state = refresh(db,config,force=True,now=now)
            event(db,'execution_interrupted',state,now,outcome='UNKNOWN_AFTER_WORKER_RESTART')


def public_status(db, config):
    """Read only, coarse shared status; no other tenant counts or resource data."""
    active = enabled(config)
    state = load(db) if active else dict(mode='DISABLED',observed_at=0)
    now = int(time.time())
    mode = state['mode']
    if active:
        if not compatible(state):
            mode = 'REVIEW_REQUIRED'
        elif not 0 <= now-state['observed_at'] <= POLICY['stale_seconds']:
            mode = 'OBSERVATION_STALE'
    return dict(protocol=FORMAT,enabled=active,mode=mode,
                observed_at=state['observed_at'] or None,scope='QUEUED_ADAPTIVE_MISSIONS',
                policy_sha256=POLICY_SHA)


def blocked_response():
    from flask import jsonify
    response = jsonify(error=dict(code='mission_regulated',message='Las nuevas ejecuciones de misiones están temporalmente pausadas. Podés consultar, exportar o cancelar tus misiones.'))
    response.status_code = 503
    response.headers['Retry-After'] = str(POLICY['sample_seconds'])
    return response


if __name__ == '__main__':
    # Private operator inspection only; does not reset state or trigger work.
    from .config import settings
    from .db import connect
    config = settings()
    with contextlib.closing(connect(config['DATABASE'])) as db:
        print(dump(dict(state=load(db),events=[dict(r) for r in db.execute(
            'SELECT * FROM mission_regulation_events ORDER BY sequence DESC LIMIT 20')])))
