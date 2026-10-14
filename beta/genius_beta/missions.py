"""Private persistent missions: fixed adapter, scoped authority and bounded inputs."""
import base64
import io
import zipfile
import json
import re
import secrets
import time
from flask import g, jsonify, request
from .db import dump, transaction
from .mission_state import MAX_BUNDLE, digest

SCOPES = ('missions:read', 'missions:write', 'missions:run', 'missions:delete')
RESERVATION = MAX_BUNDLE + 262144

def required_scope(method, path):
    if path in ('/api/missions', '/api/missions/capabilities') and method == 'GET':
        return 'missions:read'
    if path == '/api/missions' and method == 'POST':
        return 'missions:write'
    if re.fullmatch(r'/api/missions/[a-f0-9]{32}(/artifact|/export)?', path) and method == 'GET':
        return 'missions:read'
    if re.fullmatch(r'/api/missions/[a-f0-9]{32}/(run|cancel)', path) and method == 'POST':
        return 'missions:run'
    if re.fullmatch(r'/api/missions/[a-f0-9]{32}', path) and method == 'DELETE':
        return 'missions:delete'
    return None

def view(row, include_input=False):
    value = {k: row[k] for k in ('id', 'status', 'last_stage', 'state_sha256', 'artifact_name',
        'artifact_sha256', 'attempts', 'error', 'created_at', 'updated_at')}
    value['result'] = json.loads(row['result_json']) if row['result_json'] else None
    if include_input:
        value['input'] = json.loads(row['input_json'])
        value['evidence'] = {}
        if row['state_bundle']:
            raw = row['state_bundle']
            if digest(raw) != row['state_sha256']:
                raise ValueError('STATE_DIGEST')
            with zipfile.ZipFile(io.BytesIO(raw)) as archive:
                for stage in ('measure','represent','evaluate','act','observe','remember'):
                    name = 'evidence/' + stage + '.json'
                    if name in archive.namelist():
                        value['evidence'][stage] = json.loads(archive.read(name))
    return value

def install(app, db, body, error, capacity):
    def enabled():
        if not app.config['ADAPTIVE_ENABLED']:
            raise error('missions_disabled', 'La ejecución de misiones está desactivada.', 503)
    def own(mid):
        row = db().execute('SELECT * FROM adaptive_missions WHERE id=? AND user_id=?', (mid, g.user['id'])).fetchone()
        if not row:
            raise error('not_found', 'Misión no encontrada.', 404)
        return row
    def export_all():
        return [view(r, True) for r in db().execute('SELECT * FROM adaptive_missions WHERE user_id=? ORDER BY created_at,id', (g.user['id'],))]
    app.extensions['mission_export_user'] = export_all

    @app.get('/api/missions/capabilities')
    def mission_capabilities():
        return jsonify(protocol='genius-service-missions/1', enabled=app.config['ADAPTIVE_ENABLED'],
            kinds=['source_distribution_v1'], stages=['measure','represent','evaluate','act','observe','remember'],
            source='explicit_utf8_snapshot', effects='private_downloadable_archive',
            limits=dict(files=16,input_bytes=65536,missions_per_user=3,global_missions=16,timeout_seconds=60),
            memory='empirical_snapshot_receipts', self_modification=False,
            wellbeing='UNMEASURED', sustained_life_probability='UNMEASURED')

    @app.get('/api/missions')
    def mission_list():
        return jsonify(missions=[view(r) for r in db().execute('SELECT * FROM adaptive_missions WHERE user_id=? ORDER BY created_at,id', (g.user['id'],))])

    @app.post('/api/missions')
    def mission_create():
        enabled()
        data = body()
        if set(data) != {'idempotency_key','files','processing_permission','technical_scope_acknowledged'} or data['processing_permission'] is not True or data['technical_scope_acknowledged'] is not True:
            raise error('mission_input', 'Se requieren archivos y permisos explícitos para el experimento técnico.')
        key, files = data['idempotency_key'], data['files']
        if not isinstance(key, str) or not re.fullmatch(r'[A-Za-z0-9_-]{16,64}', key) or not isinstance(files, dict) or not 1 <= len(files) <= 16:
            raise error('mission_input', 'Clave de idempotencia o archivos inválidos.')
        total = 0
        for name, content in files.items():
            if (not isinstance(name, str) or not re.fullmatch(r'[A-Za-z0-9_-][A-Za-z0-9_./-]{0,119}', name)
                    or any(not p or p.startswith('.') for p in name.split('/')) or not isinstance(content, str)):
                raise error('mission_input', 'Se requieren nombres relativos y contenido UTF-8.')
            try:
                total += len(content.encode('utf-8'))
            except UnicodeEncodeError:
                raise error('mission_input', 'Contenido UTF-8 inválido.')
        if any(a != b and b.startswith(a + '/') for a in files for b in files):
            raise error('mission_input', 'Los nombres de archivos se superponen.')
        if total > 65536:
            raise error('mission_input_limit', 'Máximo de entrada: 65536 bytes.', 413)
        encoded = json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(',', ':'))
        request_sha = digest(encoded.encode())
        mid, now = secrets.token_hex(16), int(time.time())
        with transaction(db()):
            prior = db().execute('SELECT * FROM adaptive_missions WHERE user_id=? AND idempotency_key=?', (g.user['id'],key)).fetchone()
            if prior:
                if prior['request_sha256'] != request_sha:
                    raise error('idempotency_conflict', 'La clave ya identifica otra entrada.', 409)
                return jsonify(mission=view(prior)), 200
            total_count = db().execute('SELECT count(*) FROM adaptive_missions').fetchone()[0]
            own_count = db().execute('SELECT count(*) FROM adaptive_missions WHERE user_id=?', (g.user['id'],)).fetchone()[0]
            if total_count >= 16 or own_count >= 3:
                raise error('mission_capacity', 'Capacidad de misiones alcanzada; exportá y borrá las anteriores.', 429)
            # Reserve the remaining maximum growth of every stored mission, atomically.
            used = db().execute('SELECT COALESCE(sum(length(state_bundle)),0) FROM adaptive_missions').fetchone()[0]
            capacity((total_count + 1) * RESERVATION - used)
            db().execute("INSERT INTO adaptive_missions(id,user_id,idempotency_key,request_sha256,input_json,status,created_at,updated_at) VALUES(?,?,?,?,?,'draft',?,?)", (mid,g.user['id'],key,request_sha,encoded,now,now))
        return jsonify(mission=view(own(mid))), 201

    @app.get('/api/missions/<mid>')
    def mission_get(mid):
        return jsonify(mission=view(own(mid)))

    @app.get('/api/missions/<mid>/export')
    def mission_export(mid):
        return jsonify(mission=view(own(mid), True))

    @app.get('/api/missions/<mid>/artifact')
    def mission_artifact(mid):
        row = own(mid)
        if row['status'] != 'completed' or row['artifact'] is None:
            raise error('artifact_unavailable', 'La misión aún no tiene una entrega completa.', 409)
        # JSON keeps the fixed MCP binding usable without arbitrary download URLs.
        return jsonify(name=row['artifact_name'], sha256=row['artifact_sha256'],
                       bytes=len(row['artifact']), content_base64=base64.b64encode(row['artifact']).decode())

    @app.post('/api/missions/<mid>/run')
    def mission_run(mid):
        enabled()
        if body():
            raise error('mission_input', 'Este endpoint no admite instrucciones ni parámetros.')
        with transaction(db()):
            row = own(mid)
            if row['status'] in ('queued','running','completed'):
                return jsonify(mission=view(row))
            if row['status'] == 'needs_review' or row['attempts'] >= 3:
                raise error('mission_review_required', 'El estado requiere revisión; no se reintentará automáticamente.', 409)
            from .agent_access import reserve_agent_job
            now = int(time.time())
            day = now // 86400 * 86400
            for key, limit in (('missions-global',app.config['MAX_GLOBAL_JOBS_DAILY']),
                               ('missions-user:'+g.user['id'],app.config['MAX_JOBS_DAILY'])):
                count = db().execute('SELECT count FROM counters WHERE key=? AND bucket=?',(key,day)).fetchone()
                if count and count[0] >= limit:
                    raise error('mission_daily_limit','Cuota diaria de misiones alcanzada.',429)
                db().execute('INSERT INTO counters VALUES(?,?,1) ON CONFLICT(key,bucket) DO UPDATE SET count=count+1',(key,day))
            if g.agent_account:
                reserve_agent_job(db(),app.config,g.user['id'],int(time.time()),error)
            db().execute("UPDATE adaptive_missions SET status='queued',cancel_requested=0,error=NULL,updated_at=? WHERE id=?", (int(time.time()),mid))
        return jsonify(mission=view(own(mid))), 202

    @app.post('/api/missions/<mid>/cancel')
    def mission_cancel(mid):
        with transaction(db()):
            row = own(mid)
            if row['status'] in ('queued','running'):
                db().execute("UPDATE adaptive_missions SET cancel_requested=1,status='cancelled',updated_at=? WHERE id=?", (int(time.time()),mid))
        return jsonify(mission=view(own(mid)))

    @app.delete('/api/missions/<mid>')
    def mission_delete(mid):
        if body().get('confirm') is not True:
            raise error('confirmation_required', 'Se requiere confirm=true.')
        with transaction(db()):
            own(mid)
            event = (mid, 'mission', int(time.time()))
            from .r2_backup import record_deletions, BackupError
            try:
                record_deletions([event])
            except BackupError:
                raise error('privacy_backup_unavailable','El borrado requiere registrar su protección en el respaldo. Volvé a intentar.',503) from None
            db().execute('INSERT OR IGNORE INTO deletion_ledger VALUES(?,?,?)', event)
            db().execute('DELETE FROM adaptive_missions WHERE id=? AND user_id=?', (mid,g.user['id']))
        db().execute('PRAGMA wal_checkpoint(TRUNCATE)')
        return '', 204
