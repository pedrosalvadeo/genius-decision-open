"""One-shot, no-socket synthetic storage/engine probe. Never starts the app.

Cloud entry point retains production bootstrap and the legal startup rejection.
seed and verify are separately authorized invocations using the same volume,
run ID and reviewed source commit. No routine deletes another run's artifacts.
"""
from __future__ import annotations

import base64
import contextlib
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import signal
import sqlite3
import stat
import subprocess
import sys
import tempfile
import time

import backup
import start

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'beta'))
LIMIT_SECONDS = 120
LEGAL_ERROR = 'Production requires HTTPS origin and privacy controller, address and contact'


class ProbeError(RuntimeError):
    pass


def require(condition, code):
    if not condition:
        raise ProbeError(code)


def record(path, value):
    with path.open('x', encoding='utf-8') as file:
        json.dump(value, file, sort_keys=True, separators=(',', ':'))
        file.write('\n')
        file.flush()
        os.fsync(file.fileno())


def fingerprint(path):
    require(path.is_file() and not path.is_symlink(), 'UNSAFE_FILE')
    return backup.digest(path)


def check_database(db):
    require([tuple(row) for row in db.execute('PRAGMA integrity_check')] == [('ok',)], 'DATABASE_INTEGRITY_FAILED')
    require(db.execute('PRAGMA foreign_key_check').fetchone() is None, 'DATABASE_FOREIGN_KEY_FAILED')


def check_permissions(path, mode):
    info = path.stat()
    require(info.st_uid == os.geteuid() and info.st_gid == os.getegid()
            and stat.S_IMODE(info.st_mode) == mode, 'UNSAFE_OWNER_OR_PERMISSIONS')


def check_expected(example, result):
    expected = json.loads((ROOT / 'beta/examples/EXPECTED.json').read_text())['examples'][example]
    response = result['response']
    require(result['evidence_origin'] == 'synthetic' and len(response['decisions']) == 1, 'RESULT_PROVENANCE_OR_CARDINALITY')
    decision = response['decisions'][0]
    require(decision['state'] == expected['decision'] and response['evidence'][0]['state'] == expected['evidence'], 'UNEXPECTED_DECISION_OR_EVIDENCE')
    require(response['quality']['model_fidelity']['state'] == 'NOT_ASSESSED'
            and response['quality']['comprehension']['state'] == 'NOT_ASSESSED', 'UNSUPPORTED_EMPIRICAL_CLAIM')
    if 'values' in expected:
        cells = decision['answers'][0]['value']
        require({key: cells[key]['value'] for key in expected['values']} == expected['values'], 'UNEXPECTED_FORMAL_VALUES')
    if 'value' in expected:
        require(decision['answers'][0]['value']['value'] == expected['value'], 'UNEXPECTED_FORMAL_VALUE')


def engine(example, directory):
    payload = json.loads((ROOT / 'beta/examples' / (example + '.json')).read_text())
    require(payload['evidence_origin'] == 'synthetic', 'NON_SYNTHETIC_FIXTURE')
    env = {'PATH': os.defpath, 'PYTHONPATH': str(ROOT / 'beta'),
           'PYTHONDONTWRITEBYTECODE': '1', 'LANG': 'C.UTF-8',
           'GENIUS_WORKER_PID': str(os.getpid())}
    with tempfile.TemporaryDirectory(prefix='engine-', dir=directory) as temp:
        child = subprocess.Popen([sys.executable, '-m', 'genius_beta.engine_job', temp],
                                 stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                 stderr=subprocess.DEVNULL, env=env, cwd=temp,
                                 start_new_session=True)
        try:
            output, _ = child.communicate(json.dumps(payload).encode(), timeout=40)
            require(child.returncode == 0 and len(output) <= 2097152, 'ENGINE_FAILED')
            result = json.loads(output)
            archive = base64.b64decode(result['archive_b64'], validate=True)
            require(len(archive) <= 1048576 and hashlib.sha256(archive).hexdigest() == result['archive_sha256'], 'ARTIFACT_INVALID')
            check_expected(example, result['result'])
            return payload, result['result'], archive
        finally:
            if child.poll() is None:
                with contextlib.suppress(ProcessLookupError):
                    os.killpg(child.pid, signal.SIGKILL)
                child.wait(timeout=5)


def seed(directory, metadata):
    """Uses received schema/engine with fixture rows, not API identities."""
    from genius_beta.db import connect, dump, initialize, transaction

    directory.mkdir(mode=0o700, exist_ok=False)
    check_permissions(directory, 0o700)
    database = directory / 'live.sqlite3'
    initialize(database)
    now = int(time.time())
    hashes = {}
    with contextlib.closing(connect(database)) as db:
        for owner, example in (('kept', 'hours-known'), ('deleted', 'fdq-frontier')):
            payload, result, archive = engine(example, directory)
            hashes[owner] = hashlib.sha256(archive).hexdigest()
            raw = dump(payload)
            with transaction(db):
                db.execute('INSERT INTO users VALUES(?,?,?,?,?,?)', (owner, 'synthetic-' + owner, 'DISABLED_SYNTHETIC_IDENTITY', now, now, 'internal-fixture-not-acceptance'))
                db.execute('INSERT INTO consents VALUES(?,?,?,?)', (owner, 1, 1, now))
                db.execute('INSERT INTO sessions VALUES(?,?,?,?)', ('synthetic-session-' + owner, owner, 'synthetic-csrf', now + 3600))
                db.execute('INSERT INTO api_tokens VALUES(?,?,?,?,?,?)', (owner, owner, 'synthetic-hash-' + owner, 'synthetic', now, None))
                db.execute('INSERT INTO cases VALUES(?,?,?,?,?,?,?,?)', (owner, owner, 'synthetic', payload['profile'], 'internal-probe', 1, now, now))
                db.execute('INSERT INTO revisions VALUES(?,?,?,?,?)', (owner, 1, raw, hashlib.sha256(raw.encode()).hexdigest(), now))
                db.execute('INSERT INTO jobs(id,case_id,revision,status,result_json,created_at,finished_at) VALUES(?,?,?,?,?,?,?)', (owner, owner, 1, 'completed', dump(result), now, now))
                db.execute('INSERT INTO artifacts VALUES(?,?,?,?)', (owner, archive, hashes[owner], len(archive)))
        check_database(db)
    snapshot = directory / 'snapshot.sqlite3'
    saved = backup.snapshot(database, snapshot)
    with contextlib.closing(connect(database)) as db:
        with transaction(db):
            db.execute('INSERT INTO deletion_ledger VALUES(?,?,?)', ('deleted', 'user', now))
            db.execute('DELETE FROM users WHERE id=?', ('deleted',))
        check_database(db)
        db.execute('PRAGMA wal_checkpoint(TRUNCATE)')
    (directory / 'SUSPENDED').touch(mode=0o600, exist_ok=False)
    check_permissions(database, 0o600)
    doc = dict(metadata, phase='seed', status='PASS', invocation=secrets.token_hex(16),
               engine_profiles=['hours', 'fdq'], received_expected_results_matched=True,
               synthetic_owner_rows_seeded=2,
               artifact_sha256=hashes, snapshot_sha256=saved['sha256'],
               live_sha256=fingerprint(database), suspension_marker_written=True,
               database_mode=oct(stat.S_IMODE(database.stat().st_mode)),
               database_uid=database.stat().st_uid,
               container_restart_attested_by_runner=False)
    record(directory / 'seed.json', doc)
    return doc


def verify(directory, metadata):
    require(directory.is_dir() and directory.resolve() == directory, 'TRIAL_DIRECTORY_INVALID')
    marker = directory / 'seed.json'
    fingerprint(marker)
    before = json.loads(marker.read_text())
    require(before['phase'] == 'seed' and before['status'] == 'PASS', 'SEED_NOT_COMPLETE')
    require(before['source_commit'] == metadata['source_commit'] and before['run_id'] == metadata['run_id'], 'SOURCE_OR_RUN_CHANGED')
    require(not (directory / 'verify.json').exists(), 'VERIFY_ALREADY_COMPLETED')
    database, snapshot = directory / 'live.sqlite3', directory / 'snapshot.sqlite3'
    require(fingerprint(database) == before['live_sha256'], 'PERSISTED_DATABASE_CHANGED')
    require(fingerprint(snapshot) == before['snapshot_sha256'], 'PERSISTED_SNAPSHOT_CHANGED')
    fingerprint(backup.manifest_path(snapshot))
    require((directory / 'SUSPENDED').is_file() and not (directory / 'SUSPENDED').is_symlink(), 'SUSPENSION_MARKER_LOST')
    recovered = directory / 'recovered.sqlite3'
    # This isolated runner has no web/worker and holds the exclusive probe lock.
    backup.restore(snapshot, recovered, database, services_stopped=True)
    check_permissions(recovered, 0o600)
    with contextlib.closing(backup.read_only(recovered)) as db:
        backup.check(db)
        require(db.execute('SELECT id FROM users').fetchall() == [('kept',)], 'DELETION_NOT_PRESERVED')
        require(db.execute('SELECT id FROM cases').fetchall() == [('kept',)], 'CASE_CASCADE_FAILED')
        require(db.execute('SELECT research,followup FROM consents').fetchall() == [(0, 0)], 'CONSENT_NOT_REVOKED')
        for table in ('sessions', 'api_tokens', 'research_candidates'):
            require(db.execute('SELECT COUNT(*) FROM ' + table).fetchone()[0] == 0, 'CREDENTIALS_OR_CANDIDATES_RESTORED')
        artifact = db.execute('SELECT archive,sha256 FROM artifacts WHERE job_id=?', ('kept',)).fetchone()
        require(artifact is not None and hashlib.sha256(artifact[0]).hexdigest() == artifact[1] == before['artifact_sha256']['kept'], 'ARTIFACT_NOT_PRESERVED')
    doc = dict(metadata, phase='verify', status='PASS', prior_invocation=before['invocation'],
               prior_deployment_id=before.get('deployment_id'), persisted_database_hash_verified=True,
               recovered_sha256=fingerprint(recovered), deletion_ledger_preserved=True,
               credentials_and_consent_revoked=True, artifact_preserved=True,
               suspension_marker_persisted=True, container_restart_attested_by_runner=False)
    record(directory / 'verify.json', doc)
    return doc


def preflight():
    """Validate the received trial request before any bootstrap writes."""
    phase, run_id = os.environ.get('GENIUS_TRIAL_PHASE'), os.environ.get('GENIUS_TRIAL_RUN_ID', '')
    expected = os.environ.get('GENIUS_TRIAL_EXPECTED_COMMIT', '')
    actual = os.environ.get('RAILWAY_GIT_COMMIT_SHA', '')
    require(phase in ('seed', 'verify'), 'EXPLICIT_PHASE_REQUIRED')
    require(re.fullmatch(r'[a-z0-9][a-z0-9-]{5,47}', run_id) is not None, 'INVALID_RUN_ID')
    require(re.fullmatch(r'[0-9a-f]{40}', expected) is not None and actual == expected, 'RECEIVED_SOURCE_MISMATCH')
    require(os.environ.get('GENIUS_ENV') == 'production', 'PRODUCTION_BOOTSTRAP_REQUIRED')
    require(os.environ.get('GENIUS_PUBLIC_URL') == 'https://trial.invalid', 'PRIVATE_PROBE_ORIGIN_REQUIRED')
    require(os.environ.get('RAILWAY_SERVICE_ID') and os.environ.get('RAILWAY_PROJECT_ID'), 'RAILWAY_METADATA_REQUIRED')
    require(not any(os.environ.get('GENIUS_PRIVACY_' + key) for key in ('CONTROLLER', 'ADDRESS', 'CONTACT')), 'PROBE_REQUIRES_NO_REAL_PERSONAL_CONFIGURATION')
    return phase, run_id, actual


def main():
    phase, run_id, actual = preflight()
    start.validate_runtime_environment()
    start.prepare_identity()
    require(os.geteuid() == 10001 and os.getegid() == 10001, 'UNEXPECTED_RUNTIME_IDENTITY')
    from genius_beta.config import settings
    try:
        settings()
    except ValueError as error:
        require(str(error) == LEGAL_ERROR, 'UNEXPECTED_PRODUCTION_REJECTION')
    else:
        raise ProbeError('PRODUCTION_LEGAL_GUARD_NOT_ENFORCED')
    data = Path('/data/genius')
    check_permissions(data, 0o700)
    require(not (data / 'genius.sqlite3').exists(), 'APPLICATION_DATABASE_PRESENT')
    directory = data / ('trial-' + run_id)
    require(directory.resolve() == directory and not directory.is_symlink(), 'TRIAL_DIRECTORY_INVALID')
    metadata = dict(format='genius-internal-trial/1', source_commit=actual, run_id=run_id,
                    timestamp_unix=int(time.time()), deployment_id=os.environ.get('RAILWAY_DEPLOYMENT_ID'),
                    process_id=os.getpid(), parent_process_id=os.getppid(),
                    uid=os.geteuid(), gid=os.getegid(), data_mode=oct(stat.S_IMODE(data.stat().st_mode)),
                    data_uid=data.stat().st_uid, volume_mount_checked=True,
                    legal_guard_rejected_startup=True, sockets_opened_by_probe=0,
                    scope='schema, real engine, volume persistence and offline SQLite recovery; no HTTP/auth/worker or provider snapshot claim')
    fd = os.open(data / ('trial-' + run_id + '.lock'), os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return seed(directory, metadata) if phase == 'seed' else verify(directory, metadata)


if __name__ == '__main__':
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(ProbeError('PROBE_TIMEOUT')))
    signal.alarm(LIMIT_SECONDS)
    try:
        result = main()
    except Exception as error:
        code = str(error) if isinstance(error, ProbeError) else type(error).__name__
        print(json.dumps(dict(format='genius-internal-trial/1', status='FAIL', code=code), sort_keys=True), flush=True)
        raise SystemExit(1)
    finally:
        signal.alarm(0)
    print(json.dumps(result, sort_keys=True, separators=(',', ':')), flush=True)
