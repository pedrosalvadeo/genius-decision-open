"""Same-origin web and authenticated REST API. Run through Gunicorn."""
import hashlib
import hmac
import json
import re
import secrets
import io
import shutil
import sqlite3
import time
from pathlib import Path
from flask import Flask, g, jsonify, request, send_from_directory, send_file
from werkzeug.exceptions import HTTPException
from .config import settings
from .db import connect, dump, initialize, transaction
from .r2_backup import BackupError, enabled as backup_enabled, health as backup_health, record_deletions
from .agent_access import install as install_agent_access, required_scope, reserve_agent_job, SCOPES
from .mcp_access import install as install_mcp_access
from .taxis import install as install_taxis
from .contributions import install as install_contributions
from .club import install as install_club


class APIError(Exception):
    def __init__(self, code, message, status=400):
        self.code, self.message, self.status = code, message, status


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def password_hash(password, salt=None):
    salt = salt or secrets.token_hex(16)
    value = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1, dklen=32)
    return salt + ':' + value.hex()


def body():
    if not request.is_json:
        raise APIError('json_required', 'Se requiere application/json.', 415)
    def pairs(items):
        obj = {}
        for key, value in items:
            if key in obj:
                raise ValueError('duplicate')
            obj[key] = value
        return obj
    try:
        value = json.loads(request.get_data(), object_pairs_hook=pairs, parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite')))
    except (ValueError, UnicodeDecodeError, RecursionError):
        raise APIError('invalid_json', 'JSON inválido, repetido o no finito.')
    if not isinstance(value, dict):
        raise APIError('object_required', 'Se requiere un objeto JSON.')
    return value


def bounded_text(value, label, maximum, minimum=0):
    if not isinstance(value, str) or not minimum <= len(value) <= maximum:
        name = {'username': 'Usuario (alias)', 'password': 'Contraseña'}.get(label, label)
        raise APIError('invalid_' + label, f'{name}: usá entre {minimum} y {maximum} caracteres.')
    return value


def valid_input(value, profile):
    if not isinstance(value, dict):
        raise APIError('invalid_input', 'input debe ser un objeto.')
    if 'profile' in value:
        raise APIError('profile_location','profile corresponde al expediente, fuera de input.')
    if value.get('permission_confirmed') is not True or value.get('scope_acknowledged') is not True:
        raise APIError('acknowledgment_required', 'Confirmá permiso sobre los datos y alcance de bajo riesgo.')
    if len(dump(value).encode()) > 110000:
        raise APIError('input_too_large', 'La entrada supera 110000 bytes.', 413)
    if profile == 'hours':
        assignments = value.get('assignments')
        if not isinstance(assignments, list) or not 1 <= len(assignments) <= 100:
            raise APIError('invalid_assignments', 'Ingresá entre 1 y 100 asignaciones.')
        ids = set()
        for row in assignments:
            if not isinstance(row, dict):
                raise APIError('invalid_assignment', 'Asignación inválida.')
            ident = bounded_text(row.get('id'), 'assignment_id', 80, 1)
            if ident in ids:
                raise APIError('duplicate_assignment', 'Identificadores repetidos.')
            ids.add(ident)
            if row.get('credit') is not None:
                bounded_text(row['credit'], 'credit', 64, 1)
        if value.get('target') is not None:
            bounded_text(value['target'], 'target', 64, 1)
    elif profile == 'fdq':
        for field in ('input_json', 'result_json', 'certificate_json'):
            bounded_text(value.get(field), field, 110000, 2)
        if value.get('query_kind') not in ('frontier', 'selector'):
            raise APIError('invalid_query_kind', 'query_kind debe ser frontier o selector.')
    elif profile == 'choice':
        from .choice import ChoiceError, validate_payload
        try:
            validate_payload(dict(value, profile=profile))
        except ChoiceError as exc:
            raise APIError(exc.code, exc.message) from exc
    return value


def create_app(overrides=None):
    app = Flask(__name__, static_folder='static', static_url_path='/static')
    app.config.update(settings(overrides))
    initialize(app.config['DATABASE'])
    dummy_hash = password_hash('dummy-password-do-not-use')

    def db():
        if 'db' not in g:
            g.db = connect(app.config['DATABASE'])
        return g.db

    @app.teardown_appcontext
    def close_db(_error):
        if 'db' in g:
            g.db.close()

    def fail_quota(key, limit, interval=86400):
        now = int(time.time())
        bucket = now // interval * interval
        with transaction(db()):
            row = db().execute('SELECT count FROM counters WHERE key=? AND bucket=?', (key,bucket)).fetchone()
            if row and row[0] >= limit:
                raise APIError('rate_limit', 'Límite temporal alcanzado. Intentá más tarde.', 429)
            db().execute('INSERT INTO counters VALUES(?,?,1) ON CONFLICT(key,bucket) DO UPDATE SET count=count+1', (key,bucket))

    def user_view(row):
        consent = db().execute('SELECT * FROM consents WHERE user_id=?', (row['id'],)).fetchone()
        return dict(id=row['id'],username=row['username'],research_consent=bool(consent['research']),followup_consent=bool(consent['followup']))

    def login_session(user):
        raw, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        now = int(time.time())
        with transaction(db()):
            db().execute('DELETE FROM sessions WHERE user_id=? AND expires_at<?', (user['id'],now))
            sessions = db().execute('SELECT id FROM sessions WHERE user_id=? ORDER BY expires_at DESC', (user['id'],)).fetchall()
            db().executemany('DELETE FROM sessions WHERE id=?', [(r[0],) for r in sessions[9:]])
            db().execute('INSERT INTO sessions VALUES(?,?,?,?)', (digest(raw),user['id'],csrf,now+app.config['SESSION_TTL']))
        response = jsonify(user=user_view(user),csrf_token=csrf)
        response.set_cookie('genius_session',raw,max_age=app.config['SESSION_TTL'],secure=app.config['COOKIE_SECURE'],httponly=True,samesite='Strict',path='/')
        return response

    @app.before_request
    def gate():
        if not request.path.startswith('/api/'):
            return
        if request.method not in ('GET', 'HEAD', 'OPTIONS'):
            origin = request.headers.get('Origin')
            if origin and origin != app.config['PUBLIC_URL']:
                raise APIError('origin_denied', 'Origen no autorizado.', 403)
            if request.headers.get('Sec-Fetch-Site') == 'cross-site':
                raise APIError('origin_denied', 'Solicitud entre sitios no autorizada.', 403)
            if backup_enabled() and backup_health(app.config['DATA_DIR']) != 'ok' and request.method != 'DELETE' and not request.path.endswith('/cancel') and request.path != '/api/club/blocks' and request.path not in ('/api/logout', '/api/login', '/api/me'):
                raise APIError('backup_unavailable', 'Las nuevas operaciones están temporalmente pausadas. Tus datos siguen disponibles.', 503)
            if app.config['SUSPEND_FILE'].exists() and request.method != 'DELETE' and not request.path.endswith('/cancel') and request.path != '/api/club/blocks' and request.path not in ('/api/logout', '/api/login', '/api/me'):
                raise APIError('service_suspended', 'Servicio temporalmente suspendido.', 503)
        if request.path.startswith('/api/examples/') or request.path in ('/api/config', '/api/meta', '/api/health', '/api/register', '/api/login', '/api/agents/register', '/api/agents/demo'):
            return
        now = int(time.time())
        g.token_id, g.agent_grant, g.agent_scopes = None, None, []
        authorization = request.headers.get('Authorization', '')
        if authorization:
            if not authorization.startswith('Bearer ') or len(authorization) > 200:
                raise APIError('unauthorized', 'Credencial inválida.', 401)
            token = db().execute('SELECT * FROM api_tokens WHERE token_hash=?', (digest(authorization[7:]),)).fetchone()
            if not token:
                raise APIError('unauthorized', 'Credencial inválida.', 401)
            uid = token['user_id']
            g.token_id = token['id']
            db().execute('UPDATE api_tokens SET last_used_at=? WHERE id=?', (now,token['id']))
            g.csrf, g.session_id = None, None
        else:
            raw = request.cookies.get('genius_session', '')
            session = db().execute('SELECT * FROM sessions WHERE id=? AND expires_at>?', (digest(raw),now)).fetchone()
            if not session:
                raise APIError('unauthorized', 'Iniciá sesión.', 401)
            uid = session['user_id']
            g.csrf, g.session_id = session['csrf'], session['id']
            if request.method not in ('GET','HEAD','OPTIONS') and not hmac.compare_digest(request.headers.get('X-CSRF-Token',''),g.csrf):
                raise APIError('csrf_required', 'Falta un token CSRF válido.', 403)
        g.user = db().execute('SELECT * FROM users WHERE id=?', (uid,)).fetchone()
        g.agent_account = db().execute('SELECT * FROM agent_accounts WHERE user_id=?',(uid,)).fetchone()
        if g.agent_account:
            grant = db().execute('SELECT * FROM agent_token_grants WHERE token_id=?',(g.token_id,)).fetchone()
            if (not grant or grant['expires_at'] <= now or
                    (g.agent_account['expires_at'] is not None and g.agent_account['expires_at'] <= now)):
                raise APIError('unauthorized','Credencial de agente ausente, revocada o vencida.',401)
            scopes = json.loads(grant['scopes_json'])
            if not isinstance(scopes,list) or any(not isinstance(s,str) or s not in SCOPES for s in scopes):
                raise APIError('unauthorized','Credencial inválida.',401)
            scope = required_scope(request.method,request.path)
            if scope is None or (scope and scope not in scopes):
                raise APIError('insufficient_scope','Esta credencial no permite la operación.',403)
            if (not app.config['AGENT_ACCESS_ENABLED'] and request.method not in ('GET','HEAD','DELETE')
                    and not request.path.endswith('/cancel') and request.path != '/api/club/blocks'):
                raise APIError('agent_access_closed','Las nuevas operaciones de agentes están pausadas.',503)
            g.agent_grant, g.agent_scopes = grant, scopes
        db().execute('UPDATE users SET last_active=? WHERE id=?', (now,uid))
        fail_quota('api:' + uid, 60 if g.agent_account else 240, 60)

    @app.after_request
    def headers(response):
        response.headers['X-Content-Type-Options']='nosniff'
        response.headers['X-Frame-Options']='DENY'
        response.headers['Referrer-Policy']='no-referrer'
        response.headers['Content-Security-Policy']="default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
        response.headers['Permissions-Policy']='camera=(), microphone=(), geolocation=()'
        if app.config['COOKIE_SECURE']:
            response.headers['Strict-Transport-Security']='max-age=31536000'
        if request.path.startswith('/api/') or request.path == '/mcp' or request.path.startswith('/contributions'):
            response.headers['Cache-Control']='no-store'
            response.headers['X-Robots-Tag']='noindex, nofollow'
        return response

    @app.errorhandler(APIError)
    def api_error(error):
        return jsonify(error=dict(code=error.code,message=error.message)), error.status

    @app.errorhandler(HTTPException)
    def http_error(error):
        return jsonify(error=dict(code='http_' + str(error.code),message=error.description)), error.code

    @app.errorhandler(Exception)
    def unexpected(error):
        # No private request bodies, exception strings or credential-bearing URLs in logs.
        app.logger.error('request_failed class=%s', type(error).__name__)
        return jsonify(error=dict(code='internal_error',message='Error interno; la solicitud no se completó.')),500

    def capacity(estimated=262144):
        from .twin_integration import storage_bytes
        allocated=storage_bytes(app.config['DATA_DIR'])
        free=shutil.disk_usage(app.config['DATA_DIR']).free
        if allocated+estimated>app.config['MAX_DATABASE_BYTES'] or free-estimated<app.config['MIN_FREE_BYTES']:
            raise APIError('storage_capacity','Capacidad de almacenamiento alcanzada.',503)

    @app.get('/api/examples/<name>')
    def example(name):
        if name not in ('hours-known','hours-unknown','fdq-frontier','fdq-selector','choice-leisure'):
            raise APIError('not_found','Ejemplo no encontrado.',404)
        return send_from_directory(Path(__file__).resolve().parents[1]/'examples',name+'.json')

    @app.get('/')
    def index():
        return send_from_directory(app.static_folder,'index.html')

    @app.get('/robots.txt')
    def robots():
        return 'User-agent: *\nDisallow: /api/\n', 200, {'Content-Type':'text/plain'}

    # Public discovery documents contain no account data and do not grant access.
    @app.get('/agents')
    def agents():
        return send_from_directory(app.static_folder, 'agents.html')

    @app.get('/llms.txt')
    def agent_guide():
        return send_from_directory(app.static_folder, 'llms.txt', mimetype='text/plain')

    @app.get('/openapi.json')
    def integration_contract():
        return send_from_directory(app.static_folder, 'openapi.json', mimetype='application/vnd.oai.openapi+json')

    @app.get('/api/health')
    def health():
        db().execute('SELECT 1').fetchone()
        return jsonify(status='ok',suspended=app.config['SUSPEND_FILE'].exists(),backup=backup_health(app.config['DATA_DIR']))

    @app.get('/api/config')
    @app.get('/api/meta')
    def config():
        return jsonify(service='Genius beta',version='0.4.0' if app.config['TWIN_ENABLED'] else '0.3.0',adaptive_enabled=app.config['ADAPTIVE_ENABLED'],twin_enabled=app.config['TWIN_ENABLED'],twin_url='/twin/' if app.config['TWIN_ENABLED'] else None,environment=app.config['ENV'],registration_open=app.config['REGISTRATION_OPEN'] and not app.config['SUSPEND_FILE'].exists() and (not backup_enabled() or backup_health(app.config['DATA_DIR']) == 'ok'),scope=('Gemelo dinámico configurable bajo premisas declaradas. ' if app.config['TWIN_ENABLED'] else '')+'Comparación guiada de alternativas declaradas para ocio y organización personal; créditos formales y consultas FDQ. Sin interpretación libre universal ni Radar/Solver general.',limits={k.lower():app.config[k] for k in ('MAX_CONTENT_LENGTH','MAX_CASES','MAX_REVISIONS','MAX_JOBS_DAILY','MAX_GLOBAL_JOBS_DAILY','MAX_GLOBAL_USERS','MAX_QUEUE')},privacy=dict(notice_url='/static/privacy.html',version=app.config['PRIVACY_VERSION'],controller=app.config['PRIVACY_CONTROLLER'] or None,contact=app.config['PRIVACY_CONTACT'] or None,retention_days=app.config['RETENTION_DAYS']),suspended=app.config['SUSPEND_FILE'].exists())

    @app.post('/api/register')
    def register():
        if not app.config['REGISTRATION_OPEN']:
            raise APIError('registration_closed','Las nuevas cuentas todavía no están habilitadas.',503)
        capacity()
        fail_quota('register-ip:' + digest(request.remote_addr or ''), 5, 3600)
        fail_quota('register-global', 20)
        value = body()
        username = value.get('username')
        if isinstance(username, str) and '@' in username:
            raise APIError('invalid_username','Usuario: elegí un alias, no un correo electrónico. Por ejemplo: usuario_42.')
        username = bounded_text(username, 'username', 40, 3).lower()
        if not re.fullmatch(r'[a-z0-9_-]+',username):
            raise APIError('invalid_username','Usuario: usá de 3 a 40 letras sin acentos, números, guiones o guiones bajos; sin espacios.')
        password = bounded_text(value.get('password'), 'password', 128, 12)
        if value.get('privacy_accepted') is not True:
            raise APIError('privacy_required','Aceptá la información de privacidad.')
        if value.get('privacy_version') != app.config['PRIVACY_VERSION']:
            raise APIError('privacy_version_changed','El aviso cambió. Recargá y leé la versión vigente antes de aceptar.',409)
        if value.get('adult_confirmed') is not True:
            raise APIError('adult_required','Esta beta está disponible sólo para mayores de edad.')
        for key in ('research_consent','followup_consent'):
            if key in value and type(value[key]) is not bool:
                raise APIError('invalid_consent','Los consentimientos deben ser booleanos.')
        uid, now = secrets.token_hex(16), int(time.time())
        hashed = password_hash(password)
        try:
            with transaction(db()):
                capacity()
                if db().execute('SELECT count(*) FROM users').fetchone()[0] >= app.config['MAX_GLOBAL_USERS']:
                    raise APIError('capacity_limit','Se alcanzó la capacidad de esta beta.',429)
                db().execute('INSERT INTO users VALUES(?,?,?,?,?,?)', (uid,username,hashed,now,now,app.config['PRIVACY_VERSION']))
                db().execute('INSERT INTO consents VALUES(?,?,?,?)', (uid,int(value.get('research_consent',False)),int(value.get('followup_consent',False)),now))
        except sqlite3.IntegrityError:
            raise APIError('username_unavailable','El nombre de usuario no está disponible.',409)
        response = login_session(db().execute('SELECT * FROM users WHERE id=?',(uid,)).fetchone())
        response.status_code=201
        return response

    @app.post('/api/login')
    def login():
        fail_quota('login-ip:' + digest(request.remote_addr or ''),20,900)
        value=body()
        username=bounded_text(value.get('username'),'username',40,3).lower()
        password=bounded_text(value.get('password'),'password',128,1)
        fail_quota('login-user:' + digest(username),10,900)
        user=db().execute('SELECT * FROM users WHERE username=? AND NOT EXISTS (SELECT 1 FROM agent_accounts WHERE user_id=users.id)',(username,)).fetchone()
        hashed=user['password_hash'] if user else dummy_hash
        checked=password_hash(password,hashed.split(':')[0])
        if not user or not hmac.compare_digest(checked,hashed):
            raise APIError('invalid_credentials','Usuario o contraseña incorrectos.',401)
        return login_session(user)

    @app.get('/api/me')
    def me():
        return jsonify(user=user_view(g.user),csrf_token=g.csrf)

    @app.patch('/api/me')
    def consent():
        value=body()
        if any(k not in ('research_consent','followup_consent') for k in value) or not value or any(type(v) is not bool for v in value.values()):
            raise APIError('invalid_consent','Opciones de consentimiento inválidas.')
        with transaction(db()):
            for field,column in (('research_consent','research'),('followup_consent','followup')):
                if field in value:
                    db().execute(f'UPDATE consents SET {column}=?,updated_at=? WHERE user_id=?',(int(value[field]),int(time.time()),g.user['id']))
            if value.get('research_consent') is False:
                db().execute('DELETE FROM research_candidates WHERE case_id IN(SELECT id FROM cases WHERE user_id=?)',(g.user['id'],))
        return jsonify(user=user_view(g.user),csrf_token=g.csrf)

    @app.post('/api/logout')
    def logout():
        if g.session_id:
            db().execute('DELETE FROM sessions WHERE id=?',(g.session_id,))
        response=app.response_class(status=204)
        response.delete_cookie('genius_session',path='/',secure=app.config['COOKIE_SECURE'],httponly=True,samesite='Strict')
        return response

    def own_case(cid):
        row=db().execute('SELECT * FROM cases WHERE id=? AND user_id=?',(cid,g.user['id'])).fetchone()
        if not row:
            raise APIError('not_found','Expediente no encontrado.',404)
        return row

    def case_view(row):
        return {k:row[k] for k in ('id','title','profile','consumer_type','current_revision','created_at','updated_at')}

    def job_view(row):
        value={k:row[k] for k in ('id','case_id','revision','status','error','created_at','started_at','finished_at')}
        value['result']=json.loads(row['result_json']) if row['result_json'] else None
        value['admission']=dict(status='rejected',reason=row['error'].split(':',1)[1]) if (row['error'] or '').startswith('admission_rejected:') else None
        value['result_json']=row['result_json']
        archive=db().execute('SELECT sha256,size FROM artifacts WHERE job_id=?',(row['id'],)).fetchone()
        value['artifacts']=dict(sha256=archive['sha256'],size=archive['size'],url='/api/jobs/'+row['id']+'/artifacts') if archive else None
        return value

    def details(cid):
        case=own_case(cid)
        revisions=[dict(version=r['version'],input=json.loads(r['input_json']),input_json=r['input_json'],input_sha256=r['input_sha256'],created_at=r['created_at']) for r in db().execute('SELECT * FROM revisions WHERE case_id=? ORDER BY version',(cid,))]
        jobs=[job_view(r) for r in db().execute('SELECT * FROM jobs WHERE case_id=? ORDER BY created_at,id',(cid,))]
        feedback=[dict(id=r['id'],job_id=r['job_id'],data=json.loads(r['data_json']),created_at=r['created_at']) for r in db().execute('SELECT * FROM feedback WHERE case_id=? ORDER BY created_at',(cid,))]
        return dict(case=case_view(case),revisions=revisions,jobs=jobs,feedback=feedback)

    @app.get('/api/cases')
    def list_cases():
        return jsonify(cases=[case_view(r) for r in db().execute('SELECT * FROM cases WHERE user_id=? ORDER BY updated_at DESC',(g.user['id'],))])

    @app.post('/api/choice/review')
    def review_choice():
        from .choice import ChoiceError, review
        try:
            return jsonify(review(body()))
        except ChoiceError as exc:
            raise APIError(exc.code, exc.message) from exc

    @app.post('/api/cases')
    def create_case():
        capacity()
        value=body()
        profile=value.get('profile')
        if profile not in ('hours','fdq','choice'):
            raise APIError('unsupported_profile','Perfil no admitido; usá hours, fdq o choice.')
        consumer=value.get('consumer_type','agent' if g.agent_account else 'human')
        if consumer not in ('human','application','agent'):
            raise APIError('invalid_consumer','Consumidor no admitido.')
        if g.agent_account and consumer != 'agent':
            raise APIError('invalid_consumer','El espacio automático usa consumer_type agent.')
        title=bounded_text(value.get('title','Expediente'),'title',120,1)
        data=dump(valid_input(value.get('input'),profile))
        cid,now=secrets.token_hex(16),int(time.time())
        with transaction(db()):
            capacity()
            case_limit = min(app.config['MAX_CASES'],app.config['MAX_AGENT_CASES']) if g.agent_account else app.config['MAX_CASES']
            if db().execute('SELECT count(*) FROM cases WHERE user_id=?',(g.user['id'],)).fetchone()[0]>=case_limit:
                raise APIError('case_limit','Límite de expedientes alcanzado.',429)
            db().execute('INSERT INTO cases VALUES(?,?,?,?,?,1,?,?)',(cid,g.user['id'],title,profile,consumer,now,now))
            db().execute('INSERT INTO revisions VALUES(?,1,?,?,?)',(cid,data,digest(data),now))
        return jsonify(case=case_view(own_case(cid))),201

    @app.get('/api/cases/<cid>')
    def read_case(cid):
        return jsonify(details(cid))

    @app.patch('/api/cases/<cid>')
    def update_case(cid):
        capacity()
        own_case(cid)
        value=body()
        if not value or any(k not in ('title','input') for k in value):
            raise APIError('invalid_update','Sólo title e input pueden modificarse.')
        with transaction(db()):
            capacity()
            case=own_case(cid)
            if 'title' in value:
                db().execute('UPDATE cases SET title=? WHERE id=?',(bounded_text(value['title'],'title',120,1),cid))
            previous_input=db().execute('SELECT input_json FROM revisions WHERE case_id=? AND version=?',(cid,case['current_revision'])).fetchone()[0]
            if 'input' in value and value['input'] != json.loads(previous_input):
                revision=case['current_revision']+1
                revision_limit = min(app.config['MAX_REVISIONS'],app.config['MAX_AGENT_REVISIONS']) if g.agent_account else app.config['MAX_REVISIONS']
                if revision>revision_limit:
                    raise APIError('revision_limit','Límite de versiones alcanzado.',429)
                data=dump(valid_input(value['input'],case['profile']))
                db().execute('INSERT INTO revisions VALUES(?,?,?,?,?)',(cid,revision,data,digest(data),int(time.time())))
                db().execute('UPDATE cases SET current_revision=? WHERE id=?',(revision,cid))
            db().execute('UPDATE cases SET updated_at=? WHERE id=?',(int(time.time()),cid))
        return jsonify(case=case_view(own_case(cid)))

    @app.post('/api/cases/<cid>/run')
    def run_case(cid):
        case=own_case(cid)
        value=body()
        revision=value.get('revision',case['current_revision'])
        if type(revision) is not int:
            raise APIError('invalid_revision','Versión inválida.')
        if not db().execute('SELECT 1 FROM revisions WHERE case_id=? AND version=?',(cid,revision)).fetchone():
            raise APIError('not_found','Versión no encontrada.',404)
        jid,now=secrets.token_hex(16),int(time.time())
        day=now//86400*86400
        with transaction(db()):
            previous=db().execute('SELECT * FROM jobs WHERE case_id=? AND revision=? ORDER BY created_at DESC,id DESC LIMIT 1',(cid,revision)).fetchone()
            if previous and previous['status'] in ('queued','running','completed'):
                return jsonify(job=job_view(previous)), (200 if previous['status']=='completed' else 202)
            if previous and value.get('retry') is not True:
                raise APIError('retry_required','La ejecución previa terminó sin resultado. Confirmá retry:true para reintentar.',409)
            capacity(2097152)
            if db().execute('SELECT count(*) FROM jobs WHERE case_id=?',(cid,)).fetchone()[0]>=40:
                raise APIError('job_limit','Límite de ejecuciones por expediente alcanzado.',429)
            if db().execute("SELECT count(*) FROM jobs WHERE status IN('queued','running')").fetchone()[0]>=app.config['MAX_QUEUE']:
                raise APIError('queue_full','Cola llena.',429)
            user_count=db().execute('SELECT count FROM counters WHERE key=? AND bucket=?',('jobs-user:'+g.user['id'],day)).fetchone()
            if user_count and user_count[0]>=app.config['MAX_JOBS_DAILY']:
                raise APIError('daily_limit','Cuota diaria alcanzada.',429)
            count=db().execute('SELECT count FROM counters WHERE key=? AND bucket=?',('jobs-global',day)).fetchone()
            if count and count[0]>=app.config['MAX_GLOBAL_JOBS_DAILY']:
                raise APIError('global_daily_limit','Capacidad diaria alcanzada.',429)
            if g.agent_account:
                reserve_agent_job(db(),app.config,g.user['id'],now,APIError)
            try:
                db().execute('INSERT INTO jobs(id,case_id,revision,status,created_at) VALUES(?,?,?,\'queued\',?)',(jid,cid,revision,now))
            except sqlite3.IntegrityError:
                raise APIError('job_active','Ya hay una ejecución pendiente para este expediente.',409)
            db().execute('INSERT INTO counters VALUES(?,?,1) ON CONFLICT(key,bucket) DO UPDATE SET count=count+1',('jobs-global',day))
            db().execute('INSERT INTO counters VALUES(?,?,1) ON CONFLICT(key,bucket) DO UPDATE SET count=count+1',('jobs-user:'+g.user['id'],day))
            db().execute('UPDATE cases SET updated_at=? WHERE id=?',(now,cid))
            submitted=json.loads(db().execute('SELECT input_json FROM revisions WHERE case_id=? AND version=?',(cid,revision)).fetchone()[0])
            consent=db().execute('SELECT research FROM consents WHERE user_id=?',(g.user['id'],)).fetchone()
            # Register before the outcome: failures, cancellations and unknowns stay visible.
            # Permission is a snapshot at enqueue; later opt-in never backfills prior cases.
            if consent and consent['research'] and g.user['privacy_version']==app.config['PRIVACY_VERSION'] and submitted.get('evidence_origin','user_declared')!='synthetic':
                db().execute('INSERT INTO research_candidates(id,case_id,job_id,consent_version,created_at) VALUES(?,?,?,?,?)',(jid,cid,jid,g.user['privacy_version'],now))
        return jsonify(job=job_view(db().execute('SELECT * FROM jobs WHERE id=?',(jid,)).fetchone())),202

    def own_job(jid):
        row=db().execute('SELECT jobs.* FROM jobs JOIN cases ON cases.id=jobs.case_id WHERE jobs.id=? AND cases.user_id=?',(jid,g.user['id'])).fetchone()
        if not row:
            raise APIError('not_found','Ejecución no encontrada.',404)
        return row

    @app.get('/api/jobs/<jid>')
    def read_job(jid):
        return jsonify(job=job_view(own_job(jid)))

    @app.get('/api/jobs/<jid>/artifacts')
    def artifacts(jid):
        own_job(jid)
        row=db().execute('SELECT * FROM artifacts WHERE job_id=?',(jid,)).fetchone()
        if not row:
            raise APIError('not_found','Artefactos no disponibles.',404)
        response=send_file(io.BytesIO(row['archive']),mimetype='application/zip',as_attachment=True,download_name='genius-'+jid+'.zip')
        response.headers['X-Artifact-SHA256']=row['sha256']
        return response

    @app.post('/api/jobs/<jid>/cancel')
    def cancel_job(jid):
        with transaction(db()):
            job=own_job(jid)
            if job['status']=='queued':
                db().execute("UPDATE jobs SET status='cancelled',cancel_requested=1,finished_at=? WHERE id=?",(int(time.time()),jid))
            elif job['status']=='running':
                db().execute('UPDATE jobs SET cancel_requested=1 WHERE id=?',(jid,))
        return jsonify(job=job_view(own_job(jid)))

    @app.post('/api/cases/<cid>/feedback')
    def feedback(cid):
        own_case(cid)
        capacity(16384)
        value=body()
        rating=value.get('rating')
        if rating is not None and (type(rating) is not int or not 1<=rating<=5):
            raise APIError('invalid_rating','La valoración debe estar entre 1 y 5.')
        bounded_text(value.get('comment',''),'comment',2000)
        if len(dump(value))>8000:
            raise APIError('feedback_too_large','Feedback demasiado extenso.',413)
        jid=value.get('job_id')
        if jid is not None and (not isinstance(jid,str) or own_job(jid)['case_id']!=cid):
            raise APIError('invalid_job','La ejecución no corresponde al expediente.')
        fid,now=secrets.token_hex(16),int(time.time())
        with transaction(db()):
            capacity(16384)
            if db().execute('SELECT count(*) FROM feedback WHERE case_id=?',(cid,)).fetchone()[0]>=50:
                raise APIError('feedback_limit','Límite de feedback alcanzado.',429)
            db().execute('INSERT INTO feedback VALUES(?,?,?,?,?)',(fid,cid,jid,dump(value),now))
        return jsonify(feedback=dict(id=fid,created_at=now,data=value)),201

    def delete_entity(identifier,kind):
        with transaction(db()):
            event = (identifier,kind,int(time.time()))
            try:
                record_deletions([event])
            except BackupError:
                raise APIError('deletion_not_confirmed', 'No se pudo confirmar el borrado. Intentá nuevamente.', 503) from None
            db().execute('INSERT OR IGNORE INTO deletion_ledger VALUES(?,?,?)',event)
            db().execute('DELETE FROM '+('users' if kind=='user' else 'cases')+' WHERE id=?',(identifier,))
        db().execute('PRAGMA wal_checkpoint(TRUNCATE)')

    @app.delete('/api/cases/<cid>')
    def delete_case(cid):
        own_case(cid)
        delete_entity(cid,'case')
        return '',204

    @app.delete('/api/me')
    def delete_me():
        delete_entity(g.user['id'],'user')
        if 'twin_erase_user' in app.extensions:
            app.extensions['twin_erase_user'](g.user['id'])
        response=app.response_class(status=204)
        response.delete_cookie('genius_session',path='/')
        return response

    @app.get('/api/export')
    def export():
        ids=[r[0] for r in db().execute('SELECT id FROM cases WHERE user_id=?',(g.user['id'],))]
        response = dict(export_version='1',exported_at=int(time.time()),user=user_view(g.user),cases=[details(cid) for cid in ids],research_candidates=[dict(r) for r in db().execute('SELECT research_candidates.* FROM research_candidates JOIN cases ON cases.id=research_candidates.case_id WHERE cases.user_id=?',(g.user['id'],))])
        if 'twin_export_user' in app.extensions and (not g.agent_account or 'twins:read' in g.agent_scopes):
            response['twins'] = app.extensions['twin_export_user']()
        if not g.agent_account or 'missions:read' in g.agent_scopes:
            response['missions'] = app.extensions['mission_export_user']()
        return jsonify(response)

    @app.get('/api/tokens')
    def tokens():
        return jsonify(tokens=[dict(r) for r in db().execute('SELECT id,label,created_at,last_used_at FROM api_tokens WHERE user_id=? ORDER BY created_at',(g.user['id'],))])

    @app.post('/api/tokens')
    def create_token():
        label=bounded_text(body().get('label','API'),'label',80,1)
        raw='gb_'+secrets.token_urlsafe(32)
        tid,now=secrets.token_hex(16),int(time.time())
        with transaction(db()):
            if db().execute('SELECT count(*) FROM api_tokens WHERE user_id=?',(g.user['id'],)).fetchone()[0]>=app.config['MAX_TOKENS']:
                raise APIError('token_limit','Límite de claves alcanzado.',429)
            db().execute('INSERT INTO api_tokens VALUES(?,?,?,?,?,NULL)',(tid,g.user['id'],digest(raw),label,now))
        return jsonify(id=tid,label=label,token=raw,created_at=now),201

    @app.delete('/api/tokens/<tid>')
    def revoke(tid):
        deleted=db().execute('DELETE FROM api_tokens WHERE id=? AND user_id=?',(tid,g.user['id'])).rowcount
        if not deleted:
            raise APIError('not_found','Clave no encontrada.',404)
        return '',204

    install_agent_access(app,db,body,digest,APIError,fail_quota,capacity,delete_entity,
        lambda: not backup_enabled() or backup_health(app.config['DATA_DIR']) == 'ok',job_view)
    install_club(app,db,body,APIError,fail_quota,capacity,
        lambda: not backup_enabled() or backup_health(app.config['DATA_DIR']) == 'ok')
    from .missions import install as install_missions
    install_missions(app,db,body,APIError,capacity)
    install_mcp_access(app,body,APIError,fail_quota,digest)
    install_taxis(app,APIError)
    install_contributions(app,db,body,APIError,fail_quota,capacity,
        lambda: not backup_enabled() or backup_health(app.config['DATA_DIR']) == 'ok')
    if app.config['TWIN_ENABLED'] or (app.config['DATA_DIR'] / 'twins').exists():
        from .twin_integration import install
        install(app, db, fail_quota, APIError)
    return app
