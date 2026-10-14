"""Consistent SQLite snapshots and privacy-preserving OFFLINE restore.

Never copies an active database with filesystem cp. Restore writes a NEW file;
it never replaces a live database. A current readable database is required to
carry forward deletions. Without that privacy state, do not reopen old data.
"""
from __future__ import annotations

import argparse
import contextlib
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import time

MAX_BACKUP_AGE_SECONDS = 7 * 86400


def digest(path):
    sha = hashlib.sha256()
    with Path(path).open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            sha.update(block)
    return sha.hexdigest()


def read_only(path):
    path = Path(path).resolve(strict=True)
    db = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=10)
    db.execute("PRAGMA foreign_keys=ON")
    return db


def check(db):
    if [tuple(row) for row in db.execute("PRAGMA integrity_check")] != [("ok",)]:
        raise RuntimeError("SQLite integrity check failed")
    if db.execute("PRAGMA foreign_key_check").fetchone() is not None:
        raise RuntimeError("SQLite foreign-key check failed")


def versions(db):
    return db.execute("SELECT version,sha256 FROM schema_migrations ORDER BY version").fetchall()


def manifest_path(path):
    return Path(str(path) + ".manifest.json")


def emit_manifest(path, schema, kind, twins=None):
    doc = {"format": "genius-sqlite-snapshot/1", "kind": kind,
           "created_at": datetime.now(timezone.utc).isoformat(),
           "sha256": digest(path), "bytes": path.stat().st_size,
           "schema_migrations": schema}
    if twins is not None:
        doc['twins'] = twins
    manifest = manifest_path(path)
    with manifest.open("x", encoding="utf-8") as file:
        json.dump(doc, file, indent=2, sort_keys=True)
        file.write("\n")
        file.flush()
        os.fsync(file.fileno())
    return doc


def twin_folder(path):
    return Path(str(path) + '.twins')


def copy_sqlite(source, output):
    """SQLite's backup API includes committed WAL data; destination is new."""
    if output.exists() or output.is_symlink():
        raise FileExistsError('Tenant backup destination must be new')
    with contextlib.closing(read_only(source)) as src, contextlib.closing(sqlite3.connect(output)) as dst:
        src.backup(dst)
        check(dst)
        dst.execute('PRAGMA journal_mode=DELETE')
    os.chmod(output, 0o600)
    with output.open('rb') as file:
        os.fsync(file.fileno())


def snapshot_twins(source, output):
    from genius_beta.twin_integration import IDENTIFIER, lifecycle_lock, tenant_path
    directory = source.parent / 'twins'
    if not directory.exists():
        return None
    if directory.is_symlink():
        raise RuntimeError('Redirected tenant storage')
    destination = twin_folder(output)
    destination.mkdir(mode=0o700)
    entries = []
    with contextlib.closing(read_only(output)) as saved, contextlib.closing(read_only(source)) as current:
        users = {row[0] for row in saved.execute('SELECT id FROM users')}
        for uid in sorted(users):
            if not IDENTIFIER.fullmatch(uid):
                raise RuntimeError('Invalid tenant identifier')
            with lifecycle_lock(source.parent, uid):
                path = tenant_path(source.parent, uid)
                if path.is_symlink():
                    raise RuntimeError('Redirected tenant database')
                if not path.exists() or not current.execute('SELECT 1 FROM users WHERE id=?', (uid,)).fetchone():
                    continue
                target = destination / path.name
                copy_sqlite(path, target)
                entries.append({'user_id': uid, 'sha256': digest(target), 'bytes': target.stat().st_size})
    return entries


def snapshot(source, output, include_twins=True):
    os.umask(0o077)
    source, output = Path(source).resolve(strict=True), Path(output).absolute()
    if output.exists() or manifest_path(output).exists() or twin_folder(output).exists():
        raise FileExistsError("Backup destination must be new")
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".genius-backup-", dir=output.parent)
    os.close(fd)
    try:
        with contextlib.closing(read_only(source)) as src, contextlib.closing(sqlite3.connect(temporary)) as dst:
            src.backup(dst)
            check(dst)
            schema = versions(dst)
            dst.execute("PRAGMA journal_mode=DELETE")
        with open(temporary, "rb") as file:
            os.fsync(file.fileno())
        # Hard-link publishes without overwriting a concurrently created target.
        os.link(temporary, output)
        twins = snapshot_twins(source, output) if include_twins else None
        return emit_manifest(output, schema, "backup", twins)
    finally:
        Path(temporary).unlink(missing_ok=True)


def restore(source, output, current_db, services_stopped=False):
    if not services_stopped:
        raise RuntimeError("Stop web and worker before restoring; acknowledge --services-stopped")
    source, output, current_db = Path(source).resolve(strict=True), Path(output).absolute(), Path(current_db).resolve(strict=True)
    if source == current_db:
        raise ValueError("Current privacy state must be separate from the backup")
    doc = json.loads(manifest_path(source).read_text())
    if doc.get("format") != "genius-sqlite-snapshot/1" or doc.get("sha256") != digest(source):
        raise RuntimeError("Backup manifest or SHA256 mismatch")
    entries = doc.get('twins', [])
    if not isinstance(entries, list):
        raise RuntimeError('Invalid tenant backup manifest')
    from genius_beta.twin_integration import IDENTIFIER, tenant_path
    seen = set()
    for entry in entries:
        uid = entry.get('user_id') if isinstance(entry, dict) else None
        if not isinstance(uid, str) or not IDENTIFIER.fullmatch(uid) or uid in seen:
            raise RuntimeError('Invalid tenant backup identity')
        seen.add(uid)
        path = twin_folder(source) / (uid + '.sqlite3')
        if twin_folder(source).is_symlink() or path.is_symlink() or not path.is_file() or digest(path) != entry.get('sha256'):
            raise RuntimeError('Tenant backup SHA256 mismatch')
    try:
        created_at = datetime.fromisoformat(doc["created_at"])
        if created_at.tzinfo is None:
            raise ValueError("Missing timezone")
        age = time.time() - created_at.timestamp()
    except (ValueError, KeyError, TypeError):
        raise RuntimeError("Backup creation timestamp is invalid") from None
    if not -300 <= age <= MAX_BACKUP_AGE_SECONDS:
        raise RuntimeError("Backup exceeds the seven-day privacy recovery window or has a future timestamp")
    with contextlib.closing(read_only(current_db)) as current, contextlib.closing(read_only(source)) as saved:
        check(current)
        check(saved)
        if versions(current) != versions(saved):
            raise RuntimeError("Schema differs; review migration compatibility before restore")
        ledger = current.execute("SELECT id,entity_type,deleted_at FROM deletion_ledger").fetchall()
        live_users = {row[0] for row in current.execute("SELECT id FROM users")}
    snapshot(source, output, include_twins=False)
    manifest_path(output).unlink()
    # This file remains unserved throughout. Replace the backup manifest only
    # after validating the restored and privacy-filtered contents.
    with contextlib.closing(sqlite3.connect(output)) as db:
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA secure_delete=ON")
        with db:
            db.executemany("INSERT INTO deletion_ledger VALUES(?,?,?) ON CONFLICT(id) DO UPDATE SET deleted_at=MAX(deleted_at,excluded.deleted_at)", ledger)
            for identifier, entity_type, _ in db.execute("SELECT id,entity_type,deleted_at FROM deletion_ledger").fetchall():
                if entity_type == "user":
                    db.execute("DELETE FROM users WHERE id=?", (identifier,))
                elif entity_type == "case":
                    db.execute("DELETE FROM cases WHERE id=?", (identifier,))
                elif entity_type in ('club_member', 'club_file'):
                    table = 'club_members' if entity_type == 'club_member' else 'club_files'
                    if db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone():
                        db.execute('DELETE FROM ' + table + ' WHERE id=?', (identifier,))
                elif entity_type == 'twin_case':
                    pass  # Applied to the tenant snapshots below.
                else:
                    raise RuntimeError("Unknown deletion entity; keep restored file offline")
            for (identifier,) in db.execute("SELECT id FROM users").fetchall():
                if identifier not in live_users:
                    db.execute("DELETE FROM users WHERE id=?", (identifier,))
            db.execute("DELETE FROM sessions")
            db.execute("DELETE FROM api_tokens")
            db.execute("DELETE FROM research_candidates")
            db.execute("UPDATE consents SET research=0,followup=0,updated_at=?", (int(time.time()),))
            db.execute("UPDATE jobs SET status='interrupted',error='RESTORED_REQUIRES_EXPLICIT_RETRY',finished_at=? WHERE status IN ('running','queued')", (int(time.time()),))
            db.execute("DELETE FROM telemetry")
        check(db)
        schema = versions(db)
        db.execute("VACUUM")
        remaining_users = {r[0] for r in db.execute('SELECT id FROM users')}
        erased_twins = {r[0] for r in db.execute("SELECT id FROM deletion_ledger WHERE entity_type='twin_case'")}
    restored_twins = []
    if 'twins' in doc:
        from genius_twin.store import Store, now
        destination = twin_folder(output)
        destination.mkdir(mode=0o700)
        for entry in entries:
            uid = entry['user_id']
            current_path = tenant_path(current_db.parent, uid)
            if uid not in remaining_users or not current_path.exists():
                continue
            if current_path.is_symlink() or current_path.parent.is_symlink():
                raise RuntimeError('Redirected current tenant database')
            with contextlib.closing(read_only(current_path)) as current:
                check(current)
                live_cases = {r[0] for r in current.execute('SELECT id FROM cases')}
            target = destination / (uid + '.sqlite3')
            copy_sqlite(twin_folder(source) / target.name, target)
            store = Store(target)
            for row in store.read('SELECT id FROM cases'):
                if row['id'] in erased_twins or row['id'] not in live_cases:
                    store.erase_case(row['id'])
            with store.transaction() as conn:
                conn.execute("UPDATE jobs SET status='failed',finished_at=?,error_json=? WHERE status='running'",
                             (now(), json.dumps({'code': 'execution_interrupted', 'message': 'Restored offline; explicit retry required'})))
            with contextlib.closing(store.connect()) as conn:
                check(conn)
                conn.execute('PRAGMA wal_checkpoint(TRUNCATE)')
                conn.execute('PRAGMA journal_mode=DELETE')
                conn.execute('VACUUM')
            restored_twins.append({'user_id': uid, 'sha256': digest(target), 'bytes': target.stat().st_size})
    return emit_manifest(output, schema, "restored_offline_privacy_filtered", restored_twins if 'twins' in doc else None)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    backup = commands.add_parser("backup")
    backup.add_argument("source", type=Path)
    backup.add_argument("output", type=Path)
    recovery = commands.add_parser("restore")
    recovery.add_argument("source", type=Path)
    recovery.add_argument("output", type=Path)
    recovery.add_argument("--current-db", type=Path, required=True)
    recovery.add_argument("--services-stopped", action="store_true")
    args = parser.parse_args()
    if args.command == "backup":
        result = snapshot(args.source, args.output)
    else:
        result = restore(args.source, args.output, args.current_db, args.services_stopped)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
