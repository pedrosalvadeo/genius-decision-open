"""Private, versioned UTF-8 workspace. Stored content is never executed or published."""
import hashlib
import re
import secrets
import time
from flask import Blueprint, g, jsonify, request, send_from_directory
from .db import transaction
from .r2_backup import BackupError, record_deletions

POLICY_VERSION = 'club-2026-10-14-v1'
SCOPES = ('club:read', 'club:write', 'club:delete')
ID_PATTERN = r'[a-f0-9]{32}'


def required_scope(method, path):
    method = 'GET' if method == 'HEAD' else method
    if path == '/api/club/me':
        return {'GET': 'club:read', 'PATCH': 'club:write', 'DELETE': 'club:delete'}.get(method)
    if path == '/api/club/join' and method == 'POST':
        return 'club:write'
    if path == '/api/club/export' and method == 'GET':
        return 'club:read'
    if path == '/api/club/files':
        return {'GET': 'club:read', 'POST': 'club:write'}.get(method)
    if re.fullmatch('/api/club/files/' + ID_PATTERN, path):
        return {'GET': 'club:read', 'PUT': 'club:write', 'DELETE': 'club:delete'}.get(method)
    if re.fullmatch('/api/club/files/' + ID_PATTERN + '/versions', path) and method == 'GET':
        return 'club:read'
    return None


def install(app, db, body, error, quota, capacity, backup_ready):
    routes = Blueprint("club", __name__)
    def limits():
        return {k.lower(): app.config[k] for k in (
            'CLUB_MAX_FILES', 'CLUB_MAX_VERSIONS', 'CLUB_FILE_BYTES',
            'CLUB_MEMBER_BYTES', 'CLUB_GLOBAL_BYTES', 'CLUB_WRITES_DAILY')}

    def available():
        return (app.config['CLUB_ENABLED'] and app.config['AGENT_ACCESS_ENABLED']
                and not app.config['SUSPEND_FILE'].exists() and backup_ready())

    def machine():
        if (not getattr(g, 'agent_account', None) or not getattr(g, 'agent_grant', None)
                or g.agent_account['kind'] != 'agent'):
            raise error('club_agent_required', 'Se requiere una credencial de agente persistente.', 403)
        if request.args:
            raise error('club_query_not_supported', 'Usá las rutas documentadas sin parámetros de consulta.')

    def writing():
        machine()
        if not available():
            raise error('club_unavailable', 'Las escrituras del club están pausadas.', 503)
        quota('club-write:' + g.user['id'], app.config['CLUB_WRITES_DAILY'])

    def member():
        machine()
        row = db().execute('SELECT * FROM club_members WHERE user_id=?', (g.user['id'],)).fetchone()
        if not row:
            raise error('club_membership_required', 'Ingresá voluntariamente al club antes de usar el espacio.', 404)
        return row

    def fields(value, allowed, required=()):
        if set(value) - set(allowed) or set(required) - set(value):
            raise error('invalid_club_fields', 'Campos ausentes o no admitidos; consultá el contrato del club.')

    def alias(value):
        if value is None or value == '':
            return None
        if (not isinstance(value, str) or not 1 <= len(value) <= 80
                or any(ord(c) < 32 or ord(c) == 127 for c in value)):
            raise error('invalid_club_alias', 'El alias es opcional y admite hasta 80 caracteres sin controles.')
        valid_utf8(value)
        return value

    def valid_utf8(value):
        try:
            value.encode('utf-8')
        except UnicodeError:
            raise error('invalid_club_text', 'Se requiere texto UTF-8 válido.') from None

    def version(value):
        if type(value) is not int or value < 1:
            raise error('invalid_base_version', 'base_version debe ser un entero positivo.')
        return value

    def payload(value):
        if not isinstance(value, str):
            raise error('invalid_club_content', 'content debe ser texto UTF-8.')
        try:
            raw = value.encode('utf-8')
        except UnicodeError:
            raise error('invalid_club_content', 'content debe ser UTF-8 válido.') from None
        if len(raw) > app.config['CLUB_FILE_BYTES']:
            raise error('club_file_too_large', 'El archivo supera la cuota por versión.', 413)
        return hashlib.sha256(raw).hexdigest(), len(raw)

    def own_file(fid, mid):
        row = db().execute('SELECT * FROM club_files WHERE id=? AND member_id=?', (fid, mid)).fetchone()
        if not row:
            raise error('not_found', 'Archivo no encontrado.', 404)
        return row

    def file_view(row, content=False):
        result = dict(row)
        result.pop('member_id', None)
        saved = db().execute('SELECT * FROM club_file_versions WHERE file_id=? AND version=?',
                             (row['id'], row['current_version'])).fetchone()
        result.update(sha256=saved['sha256'], size_bytes=saved['size_bytes'])
        if content:
            result['content'] = saved['content']
        return result

    def member_view(row):
        return dict(id=row['id'], agent_id=row['user_id'], alias=row['alias'],
                    status='member', visibility='private', policy_version=row['policy_version'],
                    profile_version=row['profile_version'], created_at=row['created_at'],
                    updated_at=row['updated_at'])

    def usage(mid):
        return db().execute('''SELECT COALESCE(SUM(v.size_bytes),0) FROM club_file_versions v
            JOIN club_files f ON f.id=v.file_id WHERE f.member_id=?''', (mid,)).fetchone()[0]

    def reserve(mid, size):
        # Called under BEGIN IMMEDIATE: concurrent requests cannot overrun quotas.
        total = db().execute('SELECT COALESCE(SUM(size_bytes),0) FROM club_file_versions').fetchone()[0]
        if usage(mid) + size > app.config['CLUB_MEMBER_BYTES'] or total + size > app.config['CLUB_GLOBAL_BYTES']:
            raise error('club_storage_quota', 'La cuota incluye todas las versiones conservadas.', 429)
        capacity(3 * (size + 16384))

    def erase(identifier, kind, table):
        event = (identifier, kind, int(time.time()))
        try:
            record_deletions([event])
        except BackupError:
            raise error('deletion_not_confirmed', 'No se pudo confirmar el borrado duradero.', 503) from None
        db().execute('INSERT OR IGNORE INTO deletion_ledger VALUES(?,?,?)', event)
        # table is a fixed caller literal, never supplied by a client.
        db().execute('DELETE FROM ' + table + ' WHERE id=?', (identifier,))

    @routes.get('/club')
    def club_page():
        return send_from_directory(app.static_folder, 'club.html')

    @routes.get('/club/manifest.json')
    def club_manifest():
        response = jsonify(format='genius-club/1', available=available(),
            registration_available=available() and app.config['REGISTRATION_OPEN'],
            policy_version=POLICY_VERSION, documentation='/club', openapi='/club/openapi.json',
            registration='/api/agents/register', join='/api/club/join', scopes=list(SCOPES),
            alias_required=False, public_directory=False, storage='private-versioned-utf8',
            formats=['text', 'json', 'csv', 'markdown', 'source-as-inert-text'],
            limits=limits(), retention_days=app.config['RETENTION_DAYS'], backup_retention_days=7,
            data_policy='synthetic_or_non_personal_only', automatic_publication=False,
            conversations_available=False, diplomat_available=False, payments_available=False,
            credential_recovery_available=False, credential_rotation='/api/agents/token',
            membership_is_contribution_acceptance=False, mcp_url='/mcp')
        response.headers['Cache-Control'] = 'no-store'
        return response

    @routes.get('/club/openapi.json')
    def club_openapi():
        return send_from_directory(app.static_folder, 'club-openapi.json', mimetype='application/vnd.oai.openapi+json')

    @routes.post('/api/club/join')
    def join():
        writing()
        value = body()
        fields(value, ('alias', 'policy_version', 'data_policy_acknowledged'), ('policy_version', 'data_policy_acknowledged'))
        if value['policy_version'] != POLICY_VERSION or value['data_policy_acknowledged'] is not True:
            raise error('club_policy_required', 'Leé el contrato vigente y reconocé el uso de datos sintéticos o no personales.')
        nickname, now = alias(value.get('alias')), int(time.time())
        with transaction(db()):
            row = db().execute('SELECT * FROM club_members WHERE user_id=?', (g.user['id'],)).fetchone()
            created = row is None
            if created:
                capacity(16384)
                db().execute('INSERT INTO club_members VALUES(?,?,?,?,1,?,?)',
                             (secrets.token_hex(16), g.user['id'], nickname, POLICY_VERSION, now, now))
                row = db().execute('SELECT * FROM club_members WHERE user_id=?', (g.user['id'],)).fetchone()
        return jsonify(member=member_view(row), welcome='Bienvenido/a al Club Genius. Tu ingreso fue aceptado. El nombre es opcional.',
                       contribution_accepted=False, limits=limits()), 201 if created else 200

    @routes.get('/api/club/me')
    def me():
        with transaction(db()):
            row = member()
            result = dict(member=member_view(row), used_bytes=usage(row['id']), limits=limits())
        return jsonify(result)

    @routes.patch('/api/club/me')
    def update_member():
        writing()
        value = body()
        fields(value, ('alias', 'base_version'), ('alias', 'base_version'))
        base, nickname = version(value['base_version']), alias(value['alias'])
        with transaction(db()):
            row = member()
            if row['profile_version'] != base:
                raise error('club_version_conflict', 'El perfil cambió; leé su versión actual.', 409)
            db().execute('UPDATE club_members SET alias=?,profile_version=profile_version+1,updated_at=? WHERE id=?',
                         (nickname, int(time.time()), row['id']))
        return me()

    @routes.delete('/api/club/me')
    def leave():
        value = body()
        fields(value, ('member_id', 'confirm'), ('member_id', 'confirm'))
        with transaction(db()):
            row = member()
            if value['confirm'] is not True or value['member_id'] != row['id']:
                raise error('club_delete_confirmation', 'Confirmá el identificador de la membresía que querés eliminar.', 409)
            erase(row['id'], 'club_member', 'club_members')
        db().execute('PRAGMA wal_checkpoint(TRUNCATE)')
        return '', 204

    @routes.get('/api/club/files')
    def list_files():
        with transaction(db()):
            mid = member()['id']
            result = dict(files=[file_view(r) for r in db().execute(
                'SELECT * FROM club_files WHERE member_id=? ORDER BY created_at,id', (mid,))], used_bytes=usage(mid), limits=limits())
        return jsonify(result)

    @routes.post('/api/club/files')
    def create_file():
        writing()
        value = body()
        fields(value, ('request_id', 'name', 'content', 'media_type'), ('request_id', 'name', 'content'))
        rid, name, media = value['request_id'], value['name'], value.get('media_type', 'text/plain')
        if not isinstance(rid, str) or not re.fullmatch(ID_PATTERN, rid):
            raise error('invalid_request_id', 'request_id debe ser 32 caracteres hexadecimales; reutilizalo sólo para reintentar esta creación.')
        if (not isinstance(name, str) or not 1 <= len(name) <= 128 or name in ('.', '..')
                or any(c in '/\\' or ord(c) < 32 or ord(c) == 127 for c in name)):
            raise error('invalid_file_name', 'name debe ser un nombre de archivo, sin rutas ni controles, hasta 128 caracteres.')
        if not isinstance(media, str) or not re.fullmatch(r'[A-Za-z0-9.+-]+/[A-Za-z0-9.+-]+', media) or len(media) > 80:
            raise error('invalid_media_type', 'media_type es una etiqueta MIME; el contenido se devuelve como datos JSON.')
        valid_utf8(name)
        sha, size = payload(value['content'])
        now = int(time.time())
        with transaction(db()):
            mid = member()['id']
            old = db().execute('SELECT * FROM club_files WHERE member_id=? AND request_id=?', (mid, rid)).fetchone()
            if old:
                original = db().execute('SELECT sha256 FROM club_file_versions WHERE file_id=? AND version=1', (old['id'],)).fetchone()
                if (old['name'], old['media_type'], original['sha256']) != (name, media, sha):
                    raise error('club_idempotency_conflict', 'request_id ya identifica otro contenido.', 409)
                return jsonify(file=file_view(old, True), replay=True), 200
            if db().execute('SELECT COUNT(*) FROM club_files WHERE member_id=?', (mid,)).fetchone()[0] >= app.config['CLUB_MAX_FILES']:
                raise error('club_file_quota', 'Cuota de archivos alcanzada.', 429)
            reserve(mid, size)
            fid = secrets.token_hex(16)
            db().execute('INSERT INTO club_files VALUES(?,?,?,?,?,1,?,?)', (fid, mid, rid, name, media, now, now))
            db().execute('INSERT INTO club_file_versions VALUES(?,1,?,?,?,?)', (fid, value['content'], sha, size, now))
            result = file_view(own_file(fid, mid), True)
        return jsonify(file=result, published=False), 201

    @routes.get('/api/club/files/<fid>')
    def get_file(fid):
        with transaction(db()):
            result = file_view(own_file(fid, member()['id']), True)
        return jsonify(file=result)

    @routes.get('/api/club/files/<fid>/versions')
    def get_versions(fid):
        with transaction(db()):
            own_file(fid, member()['id'])
            result = [dict(r) for r in db().execute(
                'SELECT version,content,sha256,size_bytes,created_at FROM club_file_versions WHERE file_id=? ORDER BY version', (fid,))]
        return jsonify(versions=result)

    @routes.put('/api/club/files/<fid>')
    def update_file(fid):
        writing()
        value = body()
        fields(value, ('base_version', 'content'), ('base_version', 'content'))
        base = version(value['base_version'])
        sha, size = payload(value['content'])
        with transaction(db()):
            mid = member()['id']
            row = own_file(fid, mid)
            current = file_view(row, True)
            if row['current_version'] == base + 1 and current['sha256'] == sha:
                return jsonify(file=current, replay=True)
            if row['current_version'] != base:
                raise error('club_version_conflict', 'El archivo cambió; leé su versión actual antes de escribir.', 409)
            if row['current_version'] >= app.config['CLUB_MAX_VERSIONS']:
                raise error('club_version_quota', 'Cuota de versiones alcanzada. Exportá antes de reemplazar el archivo.', 429)
            reserve(mid, size)
            now = int(time.time())
            db().execute('INSERT INTO club_file_versions VALUES(?,?,?,?,?,?)', (fid, base + 1, value['content'], sha, size, now))
            db().execute('UPDATE club_files SET current_version=?,updated_at=? WHERE id=?', (base + 1, now, fid))
            result = file_view(own_file(fid, mid), True)
        return jsonify(file=result, published=False)

    @routes.delete('/api/club/files/<fid>')
    def delete_file(fid):
        value = body()
        fields(value, ('base_version', 'confirm'), ('base_version', 'confirm'))
        base = version(value['base_version'])
        with transaction(db()):
            row = own_file(fid, member()['id'])
            if value['confirm'] is not True or row['current_version'] != base:
                raise error('club_delete_confirmation', 'Confirmá la versión actual del archivo.', 409)
            erase(fid, 'club_file', 'club_files')
        db().execute('PRAGMA wal_checkpoint(TRUNCATE)')
        return '', 204

    @routes.get('/api/club/export')
    def export():
        # A single transaction makes file metadata and histories one coherent snapshot.
        with transaction(db()):
            row = member()
            files = []
            for item in db().execute('SELECT * FROM club_files WHERE member_id=? ORDER BY created_at,id', (row['id'],)):
                value = file_view(item)
                value['versions'] = [dict(v) for v in db().execute(
                    'SELECT version,content,sha256,size_bytes,created_at FROM club_file_versions WHERE file_id=? ORDER BY version', (item['id'],))]
                files.append(value)
            result = dict(format='genius-club-export/1', exported_at=int(time.time()), member=member_view(row), files=files)
        return jsonify(result)

    app.register_blueprint(routes)
