"""Private, bounded R2 backups and durable deletion intents.

R2 account administration is deliberately absent. Runtime uses a bucket-scoped
S3 identity. Credentials and plaintext are never included in receipts/logs.
The object key is authenticated with AES-256-GCM; ciphertext cannot be moved
between snapshot and privacy roles. Decryption publishes only after tag check.
"""
from __future__ import annotations

import base64
import contextlib
from datetime import datetime, timezone
import functools
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import tempfile
import time
import zipfile

MAGIC = b'GENIUS-R2-GCM-1\x00'
MAX_DB = 128 * 1024 * 1024
MAX_OBJECT = MAX_DB + 1024 * 1024
MAX_PRIVACY = 1024 * 1024
MAX_OBJECTS = 20000
MAX_STORAGE = 2 * 1024 * 1024 * 1024
MAX_MONTHLY_UPLOAD = 5 * 1024 * 1024 * 1024
INTERVAL = 86400
MAX_AGE = 7 * INTERVAL
CHUNK = 1024 * 1024
BUCKET = 'genius-production-backups'
OBJECT_PATTERN = re.compile(r'(snapshots|privacy|probes)/[a-zA-Z0-9_-]{1,100}\.gcm\Z')


class BackupError(RuntimeError):
    """Only stable error codes; never SDK exceptions containing request details."""


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def enabled():
    value = os.environ.get('GENIUS_R2_BACKUP_ENABLED', 'false')
    if value not in ('true', 'false'):
        raise BackupError('INVALID_BACKUP_SWITCH')
    return value == 'true'


def encryption_key():
    try:
        key = base64.b64decode(os.environ['GENIUS_BACKUP_ENCRYPTION_KEY'], validate=True)
        if len(key) != 32:
            raise ValueError()
        return key
    except (KeyError, ValueError):
        raise BackupError('BACKUP_KEY_MISSING_OR_INVALID') from None


def validate_object(key):
    if not isinstance(key, str) or not OBJECT_PATTERN.fullmatch(key):
        raise BackupError('INVALID_OBJECT_KEY')


def seal(source, output, key, object_key):
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    validate_object(object_key)
    if len(key) != 32 or Path(source).stat().st_size > MAX_OBJECT:
        raise BackupError('ENCRYPTION_INPUT_LIMIT')
    nonce = os.urandom(12)
    cipher = Cipher(algorithms.AES(key), modes.GCM(nonce)).encryptor()
    cipher.authenticate_additional_data(MAGIC + object_key.encode())
    with open(source, 'rb') as src, open(output, 'xb') as dst:
        os.chmod(output, 0o600)
        dst.write(MAGIC + nonce)
        for block in iter(lambda: src.read(CHUNK), b''):
            dst.write(cipher.update(block))
        dst.write(cipher.finalize())
        dst.write(cipher.tag)
        dst.flush()
        os.fsync(dst.fileno())


def unseal(source, output, key, object_key, maximum=MAX_OBJECT):
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.exceptions import InvalidTag
    validate_object(object_key)
    source, output = Path(source), Path(output)
    size = source.stat().st_size
    overhead = len(MAGIC) + 12 + 16
    if len(key) != 32 or not overhead <= size <= maximum + overhead:
        raise BackupError('CIPHERTEXT_LIMIT')
    if output.exists():
        raise FileExistsError(output)
    fd, temporary = tempfile.mkstemp(prefix='.decrypt-', dir=output.parent)
    try:
        with os.fdopen(fd, 'wb') as dst, source.open('rb') as src:
            if src.read(len(MAGIC)) != MAGIC:
                raise BackupError('CIPHERTEXT_FORMAT')
            nonce = src.read(12)
            src.seek(-16, 2)
            tag = src.read(16)
            src.seek(len(MAGIC) + 12)
            cipher = Cipher(algorithms.AES(key), modes.GCM(nonce, tag)).decryptor()
            cipher.authenticate_additional_data(MAGIC + object_key.encode())
            remaining = size - overhead
            while remaining:
                block = src.read(min(CHUNK, remaining))
                if not block:
                    raise BackupError('TRUNCATED_CIPHERTEXT')
                remaining -= len(block)
                dst.write(cipher.update(block))
            dst.write(cipher.finalize())
            dst.flush()
            os.fsync(dst.fileno())
        os.link(temporary, output)
    except InvalidTag:
        raise BackupError('AUTHENTICATION_FAILED') from None
    finally:
        Path(temporary).unlink(missing_ok=True)


class R2Store:
    """S3 SDK with explicit credentials, HTTPS, bounded requests and no retries."""
    def __init__(self):
        import boto3
        from botocore.config import Config
        account = os.environ.get('GENIUS_R2_ACCOUNT_ID', '')
        access = os.environ.get('GENIUS_R2_ACCESS_KEY_ID', '')
        secret = os.environ.get('GENIUS_R2_SECRET_ACCESS_KEY', '')
        if not re.fullmatch('[a-f0-9]{32}', account) or not access or not secret:
            raise BackupError('R2_CREDENTIALS_MISSING_OR_INVALID')
        self.client = boto3.client('s3', endpoint_url=f'https://{account}.r2.cloudflarestorage.com',
            region_name='auto', aws_access_key_id=access, aws_secret_access_key=secret,
            config=Config(signature_version='s3v4', connect_timeout=5, read_timeout=20,
                retries={'total_max_attempts': 1}, s3={'addressing_style': 'path'},
                request_checksum_calculation='when_required', response_checksum_validation='when_required'))

    def put(self, key, path):
        validate_object(key)
        if Path(path).stat().st_size > MAX_OBJECT + 128:
            raise BackupError('UPLOAD_LIMIT')
        try:
            with open(path, 'rb') as file:
                self.client.put_object(Bucket=BUCKET, Key=key, Body=file,
                    ContentLength=Path(path).stat().st_size, ContentType='application/octet-stream')
        except Exception:
            raise BackupError('R2_UPLOAD_FAILED') from None

    def get(self, key, path, maximum=MAX_OBJECT + 128):
        validate_object(key)
        created = False
        try:
            response = self.client.get_object(Bucket=BUCKET, Key=key)
            with contextlib.closing(response['Body']) as body, open(path, 'xb') as dst:
                created = True
                if response['ContentLength'] > maximum:
                    raise BackupError('DOWNLOAD_LIMIT')
                total = 0
                for block in iter(lambda: body.read(CHUNK), b''):
                    total += len(block)
                    if total > maximum:
                        raise BackupError('DOWNLOAD_LIMIT')
                    dst.write(block)
                if total != response['ContentLength']:
                    raise BackupError('DOWNLOAD_TRUNCATED')
        except BackupError:
            if created:
                Path(path).unlink(missing_ok=True)
            raise
        except FileExistsError:
            raise
        except Exception:
            if created:
                Path(path).unlink(missing_ok=True)
            raise BackupError('R2_DOWNLOAD_FAILED') from None

    def list(self, prefix):
        if prefix not in ('', 'snapshots/', 'privacy/', 'probes/'):
            raise BackupError('INVALID_PREFIX')
        rows, cursor = [], None
        try:
            while True:
                args = dict(Bucket=BUCKET, Prefix=prefix, MaxKeys=1000)
                if cursor:
                    args['ContinuationToken'] = cursor
                page = self.client.list_objects_v2(**args)
                rows.extend({'key': r['Key'], 'size': r['Size']} for r in page.get('Contents', []))
                if len(rows) > MAX_OBJECTS:
                    raise BackupError('OBJECT_COUNT_LIMIT')
                if not page.get('IsTruncated'):
                    return rows
                new_cursor = page.get('NextContinuationToken')
                if not new_cursor or new_cursor == cursor:
                    raise BackupError('INVALID_LIST_CURSOR')
                cursor = new_cursor
        except BackupError:
            raise
        except Exception:
            raise BackupError('R2_LIST_FAILED') from None


@functools.lru_cache(maxsize=1)
def runtime_store():
    return R2Store()


def record_deletions(rows, store=None, key=None):
    """Durable remote intent BEFORE committing/acknowledging local deletion.

    Append-only objects avoid overwriting newer privacy state during a crash.
    A remote success followed by a local rollback remains a deletion intent
    and is applied on recovery. Privacy objects expire after eight days, beyond
    the seven-day maximum age of any restorable snapshot. Daily snapshots do
    not refresh these objects; bootstrap exports pre-existing local tombstones.
    """
    if not rows or (store is None and not enabled()):
        return
    clean = []
    for identifier, kind, when in rows:
        if kind not in ('user', 'case', 'mission', 'twin_case', 'club_member', 'club_file', 'club_social_profile', 'club_conversation', 'club_contact_block') or not isinstance(identifier, str) or not 1 <= len(identifier) <= 128 or type(when) is not int:
            raise BackupError('INVALID_PRIVACY_EVENT')
        clean.append([identifier, kind, when])
    payload = canonical({'format': 'genius-deletion-intents/1', 'events': sorted(clean)})
    if len(payload) > MAX_PRIVACY:
        raise BackupError('PRIVACY_BATCH_LIMIT')
    store, key = store or runtime_store(), key or encryption_key()
    object_key = 'privacy/' + hashlib.sha256(payload).hexdigest() + '.gcm'
    existing = store.list('privacy/')
    if any(row['key'] == object_key for row in existing):
        return  # successful idempotent retry; do not renew retention
    if len(existing) >= MAX_OBJECTS - 16 or sum(r['size'] for r in existing) + len(payload) + 128 > 64 * 1024 * 1024:
        raise BackupError('PRIVACY_HISTORY_LIMIT')
    with tempfile.TemporaryDirectory(prefix='genius-privacy-') as temp:
        plain, encrypted = Path(temp)/'plain', Path(temp)/'encrypted'
        plain.write_bytes(payload)
        seal(plain, encrypted, key, object_key)
        store.put(object_key, encrypted)


def read_deletions(store, key):
    rows = store.list('privacy/')
    if sum(r['size'] for r in rows) > 64 * 1024 * 1024:
        raise BackupError('PRIVACY_HISTORY_LIMIT')
    ledger = {}
    for row in rows:
        if row['size'] > MAX_PRIVACY + 128:
            raise BackupError('PRIVACY_OBJECT_LIMIT')
        with tempfile.TemporaryDirectory(prefix='genius-ledger-') as temp:
            encrypted, plain = Path(temp)/'encrypted', Path(temp)/'plain'
            store.get(row['key'], encrypted, MAX_PRIVACY + 128)
            unseal(encrypted, plain, key, row['key'], MAX_PRIVACY)
            doc = json.loads(plain.read_bytes())
            if doc.get('format') != 'genius-deletion-intents/1' or not isinstance(doc.get('events'), list):
                raise BackupError('PRIVACY_FORMAT')
            for identifier, kind, when in doc['events']:
                if kind not in ('user', 'case', 'mission', 'twin_case', 'club_member', 'club_file', 'club_social_profile', 'club_conversation', 'club_contact_block') or not isinstance(identifier, str) or not 1 <= len(identifier) <= 128 or type(when) is not int:
                    raise BackupError('INVALID_PRIVACY_EVENT')
                ledger[identifier, kind] = max(when, ledger.get((identifier, kind), when))
                if len(ledger) > MAX_OBJECTS:
                    raise BackupError('PRIVACY_HISTORY_LIMIT')
    return [(identifier, kind, when) for (identifier, kind), when in ledger.items()]


@functools.lru_cache(maxsize=1)
def sqlite_backup():
    spec = importlib.util.spec_from_file_location('genius_sqlite_backup', Path(__file__).resolve().parents[1]/'deploy'/'backup.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_state(path, data):
    path = Path(path)
    fd, temporary = tempfile.mkstemp(prefix='.backup-status-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as file:
            json.dump(data, file, sort_keys=True)
            file.write('\n')
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def read_state(path):
    try:
        if Path(path).stat().st_size > 16384:
            raise ValueError()
        doc = json.loads(Path(path).read_text())
        if not isinstance(doc, dict):
            raise ValueError()
        return doc
    except FileNotFoundError:
        return {}
    except (OSError, ValueError):
        raise BackupError('BACKUP_STATE_UNREADABLE') from None


def health(data_dir):
    if not enabled():
        return 'disabled'
    try:
        state = read_state(Path(data_dir)/'backup-status.json')
        age = time.time() - state.get('last_success', 0)
        return 'ok' if state.get('status') == 'ok' and -300 <= age <= 26 * 3600 else 'unavailable'
    except (BackupError, TypeError):
        return 'unavailable'


def unpack(source, target):
    target = Path(target)
    with zipfile.ZipFile(source) as archive:
        infos = archive.infolist()
        names = {i.filename for i in infos}
        required = {'genius.sqlite3', 'genius.sqlite3.manifest.json'}
        if not 2 <= len(infos) <= 102 or len(names) != len(infos) or not required <= names:
            raise BackupError('ARCHIVE_MEMBERS')
        companions = names - required
        if any(not re.fullmatch(r'genius\.sqlite3\.twins/[0-9a-f]{32}\.sqlite3', name) for name in companions):
            raise BackupError('ARCHIVE_MEMBERS')
        if sum(i.file_size for i in infos if i.filename.endswith('.sqlite3')) > MAX_DB:
            raise BackupError('ARCHIVE_LIMIT')
        for info in infos:
            maximum = 65536 if info.filename.endswith('.json') else MAX_DB
            if info.file_size > maximum or info.compress_type != zipfile.ZIP_STORED or (info.external_attr >> 16) & 0o170000 == 0o120000:
                raise BackupError('ARCHIVE_LIMIT')
        doc = json.loads(archive.read('genius.sqlite3.manifest.json'))
        entries = doc.get('twins', [])
        if not isinstance(entries, list) or any(not isinstance(e, dict) or not isinstance(e.get('user_id'), str) or not re.fullmatch('[0-9a-f]{32}', e['user_id']) for e in entries):
            raise BackupError('ARCHIVE_MEMBERS')
        declared = {'genius.sqlite3.twins/' + e['user_id'] + '.sqlite3' for e in entries}
        if declared != companions or len(declared) != len(entries):
            raise BackupError('ARCHIVE_MEMBERS')
        for info in infos:
            (target/info.filename).parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            with archive.open(info) as src, (target/info.filename).open('xb') as dst:
                shutil.copyfileobj(src, dst, CHUNK)


def backup_once(database, status_path, store=None, key=None, now=None):
    os.umask(0o077)
    store, key = store or runtime_store(), key or encryption_key()
    now = int(time.time()) if now is None else now
    state = read_state(status_path)
    if state.get('last_success', 0) > now - INTERVAL:
        return {'status': 'not_due'}
    month = datetime.fromtimestamp(now, timezone.utc).strftime('%Y-%m')
    if state.get('month') != month:
        state.update(month=month, uploaded_bytes_reserved=0)
    if state.get('last_attempt', 0) > now - 3600:
        return {'status': 'backoff'}
    state.update(last_attempt=now, status='running')
    write_state(status_path, state)
    try:
        rows = store.list('')
        if len(rows) >= MAX_OBJECTS or sum(r['size'] for r in rows) > MAX_STORAGE - MAX_OBJECT:
            raise BackupError('STORAGE_BUDGET')
        if len([r for r in rows if r['key'].startswith('snapshots/')]) >= 8:
            raise BackupError('SNAPSHOT_RETENTION_BACKLOG')
        helper = sqlite_backup()
        if not state.get('privacy_bootstrapped'):
            with contextlib.closing(helper.read_only(database)) as db:
                record_deletions(db.execute('SELECT id,entity_type,deleted_at FROM deletion_ledger').fetchall(), store, key)
            state['privacy_bootstrapped'] = True
            write_state(status_path, state)
        with tempfile.TemporaryDirectory(prefix='genius-backup-') as temp:
            temp = Path(temp)
            if shutil.disk_usage(temp).free < 6 * MAX_OBJECT:
                raise BackupError('TEMPORARY_SPACE_LIMIT')
            saved, bundle, encrypted = temp/'genius.sqlite3', temp/'bundle', temp/'encrypted'
            manifest = helper.snapshot(database, saved)
            companions = [helper.twin_folder(saved)/(e['user_id']+'.sqlite3') for e in manifest.get('twins', [])]
            if len(companions) > 100 or saved.stat().st_size + sum(p.stat().st_size for p in companions) > MAX_DB:
                raise BackupError('DATABASE_SIZE_LIMIT')
            with zipfile.ZipFile(bundle, 'x', compression=zipfile.ZIP_STORED) as archive:
                archive.write(saved, saved.name)
                archive.write(helper.manifest_path(saved), helper.manifest_path(saved).name)
                for companion in companions:
                    archive.write(companion, helper.twin_folder(saved).name + '/' + companion.name)
            object_key = 'snapshots/' + datetime.fromtimestamp(now, timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '_' + os.urandom(8).hex() + '.gcm'
            seal(bundle, encrypted, key, object_key)
            size = encrypted.stat().st_size
            if state.get('uploaded_bytes_reserved', 0) + size > MAX_MONTHLY_UPLOAD:
                raise BackupError('MONTHLY_UPLOAD_BUDGET')
            state['uploaded_bytes_reserved'] = state.get('uploaded_bytes_reserved', 0) + size
            write_state(status_path, state)  # reserve even if a transfer fails
            store.put(object_key, encrypted)
            downloaded, verified = temp/'downloaded', temp/'verified'
            store.get(object_key, downloaded)
            unseal(downloaded, verified, key, object_key)
            if helper.digest(verified) != helper.digest(bundle):
                raise BackupError('ROUNDTRIP_MISMATCH')
            state.update(status='ok', last_success=now, object_key=object_key,
                ciphertext_sha256=helper.digest(encrypted), bytes=size, error=None)
            write_state(status_path, state)
            return {'status': 'ok', 'object_key': object_key, 'bytes': size, 'roundtrip_verified': True}
    except Exception as error:
        code = str(error) if isinstance(error, BackupError) else 'BACKUP_FAILED'
        state.update(status='failed', error=code)
        write_state(status_path, state)
        raise BackupError(code) from None


def recover(store, key, object_key, output, services_stopped=False):
    """Offline recovery from R2 only. Never modifies or restarts a live service."""
    os.umask(0o077)
    validate_object(object_key)
    if not services_stopped or not object_key.startswith('snapshots/'):
        raise BackupError('OFFLINE_RECOVERY_REQUIRED')
    output = Path(output)
    if output.exists():
        raise FileExistsError(output)
    helper = sqlite_backup()
    with tempfile.TemporaryDirectory(prefix='genius-restore-') as temp:
        temp = Path(temp)
        if shutil.disk_usage(temp).free < 6 * MAX_OBJECT:
            raise BackupError('TEMPORARY_SPACE_LIMIT')
        downloaded, bundle = temp/'downloaded', temp/'bundle'
        store.get(object_key, downloaded)
        unseal(downloaded, bundle, key, object_key)
        unpack(bundle, temp)
        saved, privacy = temp/'genius.sqlite3', temp/'privacy.sqlite3'
        ledger = read_deletions(store, key)  # current complete off-volume history
        from .db import MIGRATIONS
        expected = [(p.name, hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(MIGRATIONS.glob('*.sql'))]
        with contextlib.closing(helper.read_only(saved)) as db, contextlib.closing(sqlite3.connect(privacy)) as current:
            saved_versions = helper.versions(db)
            # Reviewed additive migrations 003 through 010 may upgrade exact historical prefixes.
            # Never accept reordered, skipped or modified historical migrations.
            approved = ('003_agent_access.sql', '004_contribution_inbox.sql', '005_club.sql', '006_club_social.sql', '007_club_contributions.sql', '008_adaptive_missions.sql', '009_mission_forecasts.sql', '010_context_forecasts.sql')
            supported = [expected[:n] for n in range(2, len(expected) + 1)
                         if all(name in approved for name, _ in expected[n:])]
            if saved_versions not in supported:
                raise BackupError('RESTORE_SCHEMA_MISMATCH')
            current.executescript('CREATE TABLE schema_migrations(version TEXT,sha256 TEXT); CREATE TABLE users(id TEXT PRIMARY KEY); CREATE TABLE deletion_ledger(id TEXT PRIMARY KEY,entity_type TEXT,deleted_at INTEGER);')
            current.executemany('INSERT INTO schema_migrations VALUES(?,?)', saved_versions)
            current.executemany('INSERT INTO users VALUES(?)', db.execute('SELECT id FROM users'))
            for identifier, kind, when in ledger:
                current.execute('INSERT INTO deletion_ledger VALUES(?,?,?) ON CONFLICT(id) DO UPDATE SET deleted_at=MAX(deleted_at,excluded.deleted_at)', (identifier, kind, when))
                if kind == 'user':
                    current.execute('DELETE FROM users WHERE id=?', (identifier,))
            current.commit()
        # With a lost volume, the encrypted remote intents are the current
        # privacy authority. Seed the helper's live-case filter from the saved
        # tenants, then apply every later remote erasure during restore.
        saved_manifest = json.loads(helper.manifest_path(saved).read_text())
        if saved_manifest.get('twins'):
            (temp/'twins').mkdir(mode=0o700)
            for entry in saved_manifest['twins']:
                name = entry['user_id'] + '.sqlite3'
                helper.copy_sqlite(helper.twin_folder(saved)/name, temp/'twins'/name)
        restored = temp/'restored.sqlite3'
        helper.restore(saved, restored, privacy, services_stopped=True)
        from .db import initialize
        initialize(restored)  # Offline only; preserves the validated historical migrations.
        # Retention still applies when restoring a recent snapshot of old data.
        with contextlib.closing(sqlite3.connect(restored)) as db:
            db.execute('PRAGMA foreign_keys=ON')
            db.execute('PRAGMA secure_delete=ON')
            # A pre-social snapshot had no table in which to apply later blocks.
            # Reapply after additive migration, before the file can be published.
            for identifier, kind, when in ledger:
                if kind != 'club_contact_block':
                    continue
                parts = identifier.split('_')
                if len(parts) != 2 or any(not re.fullmatch(r'[a-f0-9]{32}', p) for p in parts):
                    raise BackupError('INVALID_CONTACT_BLOCK')
                a,b=parts
                if db.execute('SELECT COUNT(*) FROM club_members WHERE id IN (?,?)',(a,b)).fetchone()[0] == 2:
                    db.execute('INSERT OR IGNORE INTO club_blocks VALUES(?,?,?,?)',(identifier,a,b,when))
                    lo,hi=sorted(parts)
                    db.execute('DELETE FROM club_conversations WHERE pair_low=? AND pair_high=?',(lo,hi))
            cutoff = int(time.time()) - 90 * INTERVAL
            db.execute('DELETE FROM cases WHERE updated_at<?', (cutoff,))
            db.execute('DELETE FROM adaptive_missions WHERE updated_at<?', (cutoff,))
            db.execute('DELETE FROM users WHERE last_active<?', (cutoff,))
            db.execute('DELETE FROM users WHERE id IN (SELECT user_id FROM agent_accounts WHERE expires_at<=?)',(int(time.time()),))
            db.commit()
            helper.check(db)
            db.execute('VACUUM')
            schema = helper.versions(db)
            users = {r[0] for r in db.execute('SELECT id FROM users')}
        twins = [] if 'twins' in saved_manifest else None
        for tenant in sorted(helper.twin_folder(restored).glob('*.sqlite3')):
            if tenant.stem not in users:
                tenant.unlink()
                continue
            from genius_twin.store import Store
            twin = Store(tenant)
            for case in twin.read('SELECT id,updated_at FROM cases'):
                if datetime.fromisoformat(case['updated_at']).timestamp() < cutoff:
                    twin.erase_case(case['id'])
            with contextlib.closing(twin.connect()) as db:
                helper.check(db)
                db.execute('PRAGMA wal_checkpoint(TRUNCATE)')
                db.execute('PRAGMA journal_mode=DELETE')
                db.execute('VACUUM')
            twins.append({'user_id': tenant.stem, 'sha256': helper.digest(tenant), 'bytes': tenant.stat().st_size})
        helper.manifest_path(restored).unlink()
        helper.emit_manifest(restored, schema, 'r2_offline_privacy_filtered_suspended', twins)
        output.mkdir(mode=0o700)  # exclusive; caller supplies a NEW destination
        try:
            (output/'SUSPENDED').write_text('R2 recovery: operator validation required before reopening.\n')
            shutil.copyfile(restored, output/'genius.sqlite3')
            shutil.copyfile(helper.manifest_path(restored), output/'genius.sqlite3.manifest.json')
            if twins is not None:
                (output/'twins').mkdir(mode=0o700)
                for entry in twins:
                    name = entry['user_id'] + '.sqlite3'
                    shutil.copyfile(helper.twin_folder(restored)/name, output/'twins'/name)
            for file in output.rglob('*'):
                if file.is_dir():
                    continue
                os.chmod(file, 0o600)
                with file.open('rb') as fd:
                    os.fsync(fd.fileno())
        except BaseException:
            shutil.rmtree(output)
            raise
    return {'status': 'restored_offline', 'suspended': True, 'privacy_events': len(ledger), 'registration_open': False}
