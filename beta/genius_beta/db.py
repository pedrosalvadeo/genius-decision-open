"""SQLite durability, schema migration and scoped data lifecycle."""
import contextlib
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import time

MIGRATIONS = Path(__file__).resolve().parents[1] / 'migrations'


def connect(path):
    db = sqlite3.connect(str(path), timeout=10, isolation_level=None)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    db.execute('PRAGMA secure_delete=ON')
    db.execute('PRAGMA busy_timeout=10000')
    return db


def initialize(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with contextlib.closing(connect(path)) as db:
        db.execute('PRAGMA journal_mode=WAL')
        db.execute('PRAGMA synchronous=FULL')
        db.execute('CREATE TABLE IF NOT EXISTS schema_migrations(version TEXT PRIMARY KEY, sha256 TEXT NOT NULL, applied_at INTEGER NOT NULL)')
        for file in sorted(MIGRATIONS.glob('*.sql')):
            sql = file.read_text()
            digest = hashlib.sha256(sql.encode()).hexdigest()
            row = db.execute('SELECT sha256 FROM schema_migrations WHERE version=?', (file.name,)).fetchone()
            if row:
                if row[0] != digest:
                    raise RuntimeError('Applied migration changed: ' + file.name)
                continue
            # Deployment invokes migrations before server; IMMEDIATE also serializes writes.
            db.executescript('BEGIN IMMEDIATE;\n' + sql + "\nINSERT INTO schema_migrations VALUES('" + file.name + "','" + digest + "'," + str(int(time.time())) + ');\nCOMMIT;')
    os.chmod(path, 0o600)
    return path


@contextlib.contextmanager
def transaction(db):
    db.execute('BEGIN IMMEDIATE')
    try:
        yield db
        db.commit()
    except BaseException:
        db.rollback()
        raise


def dump(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(',', ':'))


def purge(db, retention_days=90, now=None):
    """Delete inactive data and expired credentials; counters and deletion tombstones retain seven days. Backups older than seven days are not restorable."""
    now = int(time.time()) if now is None else now
    cutoff = now - retention_days * 86400
    with transaction(db):
        cases = [r[0] for r in db.execute('SELECT id FROM cases WHERE updated_at<?', (cutoff,))]
        users = [r[0] for r in db.execute('SELECT id FROM users WHERE last_active<? OR id IN (SELECT user_id FROM agent_accounts WHERE expires_at<=?)', (cutoff,now))]
        missions = [r[0] for r in db.execute('SELECT id FROM adaptive_missions WHERE updated_at<?', (cutoff,))]
        events = [(i, 'mission', now) for i in missions] + [(i, 'case', now) for i in cases] + [(i, 'user', now) for i in users]
        from .r2_backup import record_deletions
        record_deletions(events)
        db.executemany('INSERT OR IGNORE INTO deletion_ledger VALUES(?,?,?)', events)
        db.execute('DELETE FROM cases WHERE updated_at<?', (cutoff,))
        db.execute('DELETE FROM adaptive_missions WHERE updated_at<?', (cutoff,))
        db.executemany('DELETE FROM users WHERE id=?',[(uid,) for uid in users])
        db.execute('DELETE FROM api_tokens WHERE id IN (SELECT token_id FROM agent_token_grants WHERE expires_at<=?)',(now,))
        db.execute('DELETE FROM sessions WHERE expires_at<?', (now,))
        db.execute('DELETE FROM counters WHERE bucket<?', (now - 7 * 86400,))
        db.execute('DELETE FROM telemetry WHERE created_at<?', (now - 7 * 86400,))
        db.execute('DELETE FROM mission_regulation_events WHERE created_at<?', (now - 7 * 86400,))
        db.execute('DELETE FROM deletion_ledger WHERE deleted_at<?', (now - 7 * 86400,))
    db.execute('PRAGMA wal_checkpoint(TRUNCATE)')
    return {'cases': len(cases), 'users': len(users)}
