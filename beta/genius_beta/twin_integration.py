"""Authenticated twin mount and tenant lifecycle, enabled explicitly by config.

The beta authenticates every /api/twin request before these hooks execute.
Each tenant has one private database. A process lock serializes its lifecycle
with account erasure; a separate lock bounds total compiler concurrency.
"""
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import os
from pathlib import Path
import re
import shutil
import time

from flask import g, jsonify, request, send_from_directory
from .agent_access import reserve_agent_job
from .db import transaction

IDENTIFIER = re.compile(r'[0-9a-f]{32}\Z')


def storage_bytes(data_dir):
    """Conservative shared on-volume budget for the encrypted snapshot set."""
    root = Path(data_dir)
    return sum(p.stat().st_size for pattern in ('genius.sqlite3*', 'twins/*.sqlite3*')
               for p in root.glob(pattern) if p.is_file())


def tenant_path(data_dir, uid):
    if not isinstance(uid, str) or not IDENTIFIER.fullmatch(uid):
        raise ValueError('Invalid authenticated tenant identifier')
    return Path(data_dir) / 'twins' / (uid + '.sqlite3')


@contextmanager
def lifecycle_lock(data_dir, uid, blocking=True):
    tenant_path(data_dir, uid)  # validate before any filesystem access
    directory = Path(data_dir) / 'twin-locks'
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (directory / (uid + '.lock')).open('a+b') as lock:
        os.chmod(lock.name, 0o600)
        fcntl.flock(lock, fcntl.LOCK_EX | (0 if blocking else fcntl.LOCK_NB))
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def erase_tenant_files(data_dir, uid):
    """Caller must hold this tenant's lifecycle lock; no active compiler owns it."""
    path = tenant_path(data_dir, uid)
    for suffix in ('', '-wal', '-shm', '-journal'):
        candidate = Path(str(path) + suffix)
        if candidate.is_symlink():
            raise RuntimeError('Refusing redirected tenant storage')
        candidate.unlink(missing_ok=True)


def purge_twins(config, database, now=None):
    """Sweep orphan tenants and stale cases; every erasure has a retained ledger.

    The account purge runs first. Locks coordinate an already-authenticated
    request with erasure, and account existence is rechecked under the lock.
    """
    timestamp = int(time.time()) if now is None else now
    cutoff = timestamp - config['RETENTION_DAYS'] * 86400
    deleted_users = deleted_cases = 0
    folder = Path(config['DATA_DIR']) / 'twins'
    if not folder.exists():
        return {'twin_users': 0, 'twin_cases': 0}
    from genius_twin.store import Store
    for path in sorted(folder.glob('*.sqlite3')):
        uid = path.stem
        if not IDENTIFIER.fullmatch(uid) or path.is_symlink():
            raise RuntimeError('Unexpected tenant storage path')
        with lifecycle_lock(config['DATA_DIR'], uid):
            if not database.execute('SELECT 1 FROM users WHERE id=?', (uid,)).fetchone():
                erase_tenant_files(config['DATA_DIR'], uid)
                deleted_users += 1
                continue
            store = Store(path)
            for row in store.read('SELECT id,updated_at FROM cases'):
                updated = datetime.fromisoformat(row['updated_at']).timestamp()
                if updated < cutoff:
                    from .r2_backup import record_deletions
                    record_deletions([(row['id'], 'twin_case', timestamp)])
                    # Tombstone first: a crash may preserve too much data but
                    # can never authorize its resurrection from a backup.
                    database.execute('INSERT OR IGNORE INTO deletion_ledger VALUES(?,?,?)',
                                     (row['id'], 'twin_case', timestamp))
                    store.erase_case(row['id'])
                    deleted_cases += 1
    return {'twin_users': deleted_users, 'twin_cases': deleted_cases}


def install(app, db, fail_quota, APIError):
    from genius_twin.http_api import make_blueprint
    from genius_twin.process_runner import ProcessEvaluator
    from genius_twin.service import TwinService
    from genius_twin.store import Store

    static = Path(__file__).resolve().parents[2] / 'twin' / 'genius_twin' / 'static'
    evaluator = app.config.get('TWIN_EVALUATOR') or ProcessEvaluator(
        app.config['TWIN_TIMEOUT'], app.config['TWIN_MEMORY_MB'], app.config['TWIN_OUTPUT_BYTES'])
    context = {'mode': 'authenticated_beta', 'mcp': app.config['MCP_ENABLED'], 'timeout': app.config['TWIN_TIMEOUT'],
               'memory_mb': app.config['TWIN_MEMORY_MB'], 'output_bytes': app.config['TWIN_OUTPUT_BYTES']}

    @app.before_request
    def tenant_gate():
        protected = app.config['TWIN_ENABLED'] and (request.path.startswith('/api/twin/') or request.path == '/api/twin')
        lifecycle = request.path in ('/api/me', '/api/agents/me') and request.method == 'DELETE'
        export = request.path == '/api/export'
        if not (protected or lifecycle or export):
            return
        if not getattr(g, 'user', None):
            raise APIError('unauthorized', 'Inicia sesión.', 401)
        manager = lifecycle_lock(app.config['DATA_DIR'], g.user['id'], blocking=False)
        try:
            manager.__enter__()
        except BlockingIOError:
            raise APIError('twin_busy', 'Tu expediente está ocupado. Espera a que termine la operación y vuelve a intentar.', 409) from None
        g.twin_lock = manager
        if not db().execute('SELECT 1 FROM users WHERE id=?', (g.user['id'],)).fetchone():
            raise APIError('unauthorized', 'La cuenta ya no está disponible.', 401)
        if protected and request.method not in ('GET', 'HEAD', 'OPTIONS', 'DELETE'):
            size = storage_bytes(app.config['DATA_DIR'])
            estimate = 3 * app.config['TWIN_OUTPUT_BYTES'] if request.path.endswith('/evaluate') else 3 * 262144
            if size + estimate > min(app.config['TWIN_STORAGE_BYTES'], app.config['MAX_DATABASE_BYTES']) or shutil.disk_usage(app.config['DATA_DIR']).free < estimate + app.config['MIN_FREE_BYTES']:
                raise APIError('storage_capacity', 'Capacidad de almacenamiento del gemelo alcanzada.', 503)
        if protected and request.path.endswith('/evaluate') and request.method == 'POST':
            lock_path = Path(app.config['DATA_DIR']) / 'twin-locks' / 'compiler.lock'
            handle = lock_path.open('a+b')
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                handle.close()
                raise APIError('compute_capacity', 'Hay otra evaluación en curso. Vuelve a intentar en unos momentos.', 429) from None
            g.twin_compute_lock = handle
            if g.agent_account:
                with transaction(db()):
                    reserve_agent_job(db(), app.config, g.user['id'], int(time.time()), APIError)
            fail_quota('twin-job:' + g.user['id'], app.config['MAX_JOBS_DAILY'])
            fail_quota('twin-job:global', app.config['MAX_GLOBAL_JOBS_DAILY'])

    @app.teardown_request
    def unlock(_error):
        handle = g.pop('twin_compute_lock', None)
        if handle:
            fcntl.flock(handle, fcntl.LOCK_UN)
            handle.close()
        manager = g.pop('twin_lock', None)
        if manager:
            manager.__exit__(None, None, None)

    def service():
        if 'twin_service' not in g:
            if not getattr(g, 'twin_lock', None):
                raise APIError('unauthorized', 'Se requiere contexto autenticado.', 401)
            path = tenant_path(app.config['DATA_DIR'], g.user['id'])
            if path.is_symlink():
                raise RuntimeError('Refusing redirected tenant database')
            store = Store(path)
            os.chmod(path, 0o600)
            def record_erasure(cid):
                from .r2_backup import BackupError, record_deletions
                timestamp = int(time.time())
                try:
                    record_deletions([(cid, 'twin_case', timestamp)])
                except BackupError:
                    raise APIError('deletion_not_confirmed', 'No se pudo confirmar el borrado. Intentá nuevamente.', 503) from None
                db().execute('INSERT OR IGNORE INTO deletion_ledger VALUES(?,?,?)',
                             (cid, 'twin_case', timestamp))
            current = TwinService(store, evaluator=evaluator, execution_context=context, before_erase=record_erasure)
            # This process holds the tenant lock; a previous web process died.
            # The evaluator's parent-death signal prevents live orphan work.
            current.recover_jobs()
            case_limit = app.config['MAX_CASES']
            revision_limit = app.config['MAX_REVISIONS']
            if g.agent_account:
                case_limit = min(case_limit, app.config['MAX_AGENT_CASES'])
                revision_limit = min(revision_limit, app.config['MAX_AGENT_REVISIONS'])
            if request.method == 'POST' and request.path.rstrip('/') == '/api/twin/cases':
                if len(current.list_cases()['cases']) >= case_limit:
                    raise APIError('case_limit', 'Límite de expedientes alcanzado.', 429)
            accepting = re.fullmatch(r'/api/twin/proposals/([0-9a-f]{32})/accept', request.path)
            if request.method == 'POST' and accepting:
                proposal = store.one('SELECT * FROM proposals WHERE id=?', (accepting.group(1),))
                if proposal and proposal['status'] != 'accepted':
                    case = store.one('SELECT current_version FROM cases WHERE id=?', (proposal['case_id'],))
                    if case['current_version'] >= revision_limit:
                        raise APIError('revision_limit', 'Límite de versiones alcanzado. Exporta el expediente para conservarlo.', 429)
            proposing = re.fullmatch(r'/api/twin/cases/([0-9a-f]{32})/proposals', request.path)
            if request.method == 'POST' and proposing:
                count = store.one('SELECT count(*) AS n FROM proposals WHERE case_id=?', (proposing.group(1),))['n']
                if count >= 5 * revision_limit:
                    raise APIError('proposal_limit', 'Límite de propuestas alcanzado para este expediente.', 429)
            observing = re.fullmatch(r'/api/twin/cases/([0-9a-f]{32})/observations', request.path)
            if request.method == 'POST' and observing:
                case = store.one('SELECT current_version FROM cases WHERE id=?', (observing.group(1),))
                # Existing idempotent receipts may still be read at the limit.
                key = (request.get_json(silent=True) or {}).get('idempotency_key')
                prior = store.one('SELECT 1 FROM idempotency WHERE case_id=? AND key=?', (observing.group(1), key)) if isinstance(key, str) else None
                if case and case['current_version'] >= revision_limit and not prior:
                    raise APIError('revision_limit', 'Límite de versiones alcanzado.', 429)
            g.twin_service = current
        return g.twin_service

    def runtime():
        return jsonify(authenticated=True, csrf_token=g.csrf, mode='authenticated_beta')

    def index():
        return send_from_directory(static, 'index.html')

    def assets(filename):
        return send_from_directory(static, filename)

    if app.config['TWIN_ENABLED']:
        app.register_blueprint(make_blueprint(service, name='authenticated_twin'), url_prefix='/api/twin')
        app.add_url_rule('/api/twin/runtime', 'twin_runtime', runtime)
        app.add_url_rule('/twin/', 'twin_index', index)
        app.add_url_rule('/twin/static/<path:filename>', 'twin_assets', assets)

    app.extensions['twin_service_factory'] = service
    app.extensions['twin_erase_user'] = lambda uid: erase_tenant_files(app.config['DATA_DIR'], uid)
    app.extensions['twin_export_user'] = lambda: [service().export(r['id']) for r in service().list_cases()['cases']]
