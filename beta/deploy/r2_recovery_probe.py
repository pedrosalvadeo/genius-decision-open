"""Bounded synthetic R2 reception. No live database or credential output.

Run as a pre-deploy command with backups/registration disabled. Virtual backup
roles are mapped exclusively into a unique probes/ namespace (24-hour expiry).
The real backup and recovery functions run unchanged; only object names at the
transport boundary are isolated. Nothing is written to the production volume.
"""
from __future__ import annotations

import contextlib
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import sqlite3
import sys
import tempfile
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from genius_beta import r2_backup as r2
from genius_beta.db import initialize

ACCOUNT = '4a275114cfef4b41e73a135f089186ce'
MAX_PROBE_OBJECT = 1024 * 1024
MAX_PROBE_UPLOAD = 2 * MAX_PROBE_OBJECT
MANAGEMENT = ('RAILWAY_TOKEN', 'RAILWAY_API_TOKEN', 'CLOUDFLARE_API_TOKEN',
              'CLOUDFLARE_API_KEY', 'CF_API_TOKEN', 'GITHUB_TOKEN', 'GH_TOKEN',
              'SUPABASE_ACCESS_TOKEN')


class ProbeStore:
    """Reversible names, no access to real snapshots/ or privacy/ objects."""
    def __init__(self, transport, run_id):
        if not re.fullmatch(r'[0-9]{8}T[0-9]{6}Z_[a-f0-9]{8}', run_id):
            raise r2.BackupError('PROBE_ID_INVALID')
        self.transport = transport
        self.prefix = 'probes/' + run_id + '-'
        self.uploaded = 0
        self.puts = 0

    def physical(self, key):
        r2.validate_object(key)
        role, name = key.split('/')
        if role not in ('snapshots', 'privacy'):
            raise r2.BackupError('PROBE_ROLE_INVALID')
        physical = self.prefix + ('s-' if role == 'snapshots' else 'p-') + name
        r2.validate_object(physical)
        return physical

    def list(self, prefix):
        if prefix not in ('', 'snapshots/', 'privacy/'):
            raise r2.BackupError('PROBE_PREFIX_INVALID')
        rows = self.transport.list('probes/')
        if len(rows) > 64 or sum(row['size'] for row in rows) > 32 * MAX_PROBE_OBJECT:
            raise r2.BackupError('PROBE_RETENTION_BUDGET')
        result = []
        for row in rows:
            if not row['key'].startswith(self.prefix):
                continue
            suffix = row['key'][len(self.prefix):]
            if suffix.startswith('s-'):
                virtual = 'snapshots/' + suffix[2:]
            elif suffix.startswith('p-'):
                virtual = 'privacy/' + suffix[2:]
            else:
                raise r2.BackupError('PROBE_REMOTE_NAME_INVALID')
            if self.physical(virtual) != row['key']:
                raise r2.BackupError('PROBE_REMOTE_NAME_INVALID')
            if virtual.startswith(prefix):
                result.append({'key': virtual, 'size': row['size']})
        return result

    def put(self, key, path):
        physical = self.physical(key)
        size = Path(path).stat().st_size
        if size > MAX_PROBE_OBJECT or self.puts >= 2 or self.uploaded + size > MAX_PROBE_UPLOAD:
            raise r2.BackupError('PROBE_UPLOAD_BUDGET')
        with Path(path).open('rb') as file:
            if file.read(len(r2.MAGIC)) != r2.MAGIC:
                raise r2.BackupError('PROBE_REQUIRES_CIPHERTEXT')
        self.puts += 1
        self.uploaded += size
        self.transport.put(physical, path)

    def get(self, key, path, maximum=r2.MAX_OBJECT + 128):
        self.transport.get(self.physical(key), path, min(maximum, MAX_PROBE_OBJECT))


def check(condition, code):
    if not condition:
        raise r2.BackupError(code)


def run_fixture(transport, key, run_id):
    os.umask(0o077)
    store = ProbeStore(transport, run_id)
    check(store.list('') == [], 'PROBE_ID_ALREADY_EXISTS')
    now = int(time.time())
    with tempfile.TemporaryDirectory(prefix='genius-r2-probe-', dir='/tmp') as folder:
        root = Path(folder)
        live = root / 'synthetic-volume'
        live.mkdir(mode=0o700)
        source = live / 'genius.sqlite3'
        initialize(source)
        with contextlib.closing(sqlite3.connect(source)) as db:
            for user in ('kept', 'deleted'):
                db.execute('INSERT INTO users VALUES(?,?,?,?,?,?)', (user, user, 'SYNTHETIC-NO-LOGIN', now, now, 'test'))
                db.execute('INSERT INTO consents VALUES(?,?,?,?)', (user, 1, 1, now))
                db.execute('INSERT INTO sessions VALUES(?,?,?,?)', (user, user, 'synthetic-csrf', now + 3600))
                db.execute('INSERT INTO api_tokens VALUES(?,?,?,?,?,?)', (user, user, user, 'synthetic', now, None))
                db.execute('INSERT INTO cases VALUES(?,?,?,?,?,?,?,?)', (user, user, 'synthetic', 'hours', 'synthetic', 1, now, now))
                db.execute('INSERT INTO revisions VALUES(?,?,?,?,?)', (user, 1, '{}', 'synthetic', now))
                db.execute('INSERT INTO jobs(id,case_id,revision,status,created_at) VALUES(?,?,?,?,?)', (user, user, 1, 'running', now))
            db.commit()
        receipt = r2.backup_once(source, live / 'backup-status.json', store, key)
        check(receipt.get('roundtrip_verified') is True, 'PROBE_ROUNDTRIP_FAILED')
        events = [('deleted', 'user', now), ('kept', 'case', now)]
        r2.record_deletions(events, store, key)
        r2.record_deletions(events, store, key)
        check(store.puts == 2, 'PROBE_PRIVACY_RETRY_FAILED')
        # Delete only this function's disposable fixture, never /data.
        shutil.rmtree(live)
        check(not live.exists(), 'PROBE_VOLUME_LOSS_FAILED')
        # New adapter derives its inventory from R2; it has no local ledger/cache.
        recovery_store = ProbeStore(transport, run_id)
        output = root / 'recovered-offline'
        restored = r2.recover(recovery_store, key, receipt['object_key'], output, services_stopped=True)
        check(restored['suspended'] and (output / 'SUSPENDED').is_file(), 'PROBE_NOT_SUSPENDED')
        check(restored['privacy_events'] == 2, 'PROBE_PRIVACY_LEDGER_FAILED')
        with contextlib.closing(sqlite3.connect(output / 'genius.sqlite3')) as db:
            check(db.execute('SELECT id FROM users').fetchall() == [('kept',)], 'PROBE_DELETED_USER_RETURNED')
            check(db.execute('SELECT count(*) FROM cases').fetchone()[0] == 0, 'PROBE_DELETED_CASE_RETURNED')
            check(db.execute('SELECT research,followup FROM consents').fetchall() == [(0, 0)], 'PROBE_CONSENT_NOT_RESET')
            for table in ('sessions', 'api_tokens', 'research_candidates', 'telemetry', 'jobs'):
                check(db.execute('SELECT count(*) FROM ' + table).fetchone()[0] == 0, 'PROBE_RECOVERED_ACTIVE_STATE')
            check(db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok', 'PROBE_INTEGRITY_FAILED')
        check((output / 'genius.sqlite3').stat().st_mode & 0o777 == 0o600, 'PROBE_FILE_MODE_FAILED')
        return {'status': 'PASS', 'run_id': run_id, 'roundtrip_verified': True,
                'offline_restore_verified': True, 'synthetic_volume_lost': True,
                'later_deletions_honored': True, 'sessions_tokens_removed': True,
                'consents_reset': True, 'restore_suspended': True,
                'production_volume_touched': False, 'remote_prefix': 'probes/',
                'uploaded_bytes': store.uploaded, 'uploaded_objects': store.puts,
                'retention_hours': 24, 'registration_open': False, 'backup_enabled': False}


def main():
    # Console/pre-deploy environments must not delegate operator credentials.
    for name in MANAGEMENT:
        os.environ.pop(name, None)
    os.umask(0o077)
    if os.geteuid() == 0:
        os.setgroups([])
        os.setgid(10001)
        os.setuid(10001)
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ_') + os.urandom(4).hex()
    result = {'probe': 'r2-synthetic-recovery/1', 'run_id': run_id, 'status': 'FAIL'}
    def timeout(*_):
        raise r2.BackupError('PROBE_TIMEOUT')
    signal.signal(signal.SIGALRM, timeout)
    signal.alarm(150)
    try:
        check(os.geteuid() == 10001, 'PROBE_UID_INVALID')
        check(not r2.enabled(), 'PROBE_BACKUPS_MUST_BE_DISABLED')
        check(os.environ.get('GENIUS_REGISTRATION_OPEN') == 'false', 'PROBE_REGISTRATION_MUST_BE_CLOSED')
        check(os.environ.get('GENIUS_R2_ACCOUNT_ID') == ACCOUNT, 'PROBE_ACCOUNT_MISMATCH')
        key = r2.encryption_key()
        result.update(run_fixture(r2.R2Store(), key, run_id))
        result['runtime_sha256'] = hashlib.sha256(Path(r2.__file__).read_bytes()).hexdigest()
    except r2.BackupError as error:
        result['code'] = str(error)  # stable codes only, no SDK exception text
    except Exception:
        result['code'] = 'PROBE_INTERNAL_ERROR'
    finally:
        signal.alarm(0)
    print(json.dumps(result, sort_keys=True), flush=True)
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
