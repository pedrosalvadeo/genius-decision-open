"""Bounded machine principals. No human consent, password, or shared account."""
import json
from pathlib import Path
import re
import secrets
import time
from flask import g, jsonify, request
from .db import dump, transaction
from . import club, missions

POLICY_VERSION = 'agent-access-2026-10-06-v1'
TWIN_SCOPES = ('twins:read', 'twins:write', 'twins:evaluate', 'twins:delete')
SCOPES = frozenset(('cases:read', 'cases:write', 'jobs:run', 'cases:delete', 'account:delete', *TWIN_SCOPES, *club.SCOPES, *missions.SCOPES))
DEFAULT_SCOPES = ('cases:read', 'cases:write', 'jobs:run', 'account:delete')
DEMO_SCOPES = ('cases:read', 'account:delete')
EXAMPLES = ('hours-known', 'hours-unknown', 'fdq-frontier', 'fdq-selector')


def required_scope(method, path):
    method = 'GET' if method == 'HEAD' else method
    if path == '/api/missions' or path.startswith('/api/missions/'):
        return missions.required_scope(method, path)
    if path.startswith('/api/club/'):
        return club.required_scope(method, path)
    if path.startswith('/api/twin/'):
        suffix = path[len('/api/twin/'):]
        if method == 'GET' and (suffix in ('capabilities', 'profiles', 'examples', 'cases', 'runtime')
                or re.fullmatch(r'(profiles/[A-Za-z0-9_-]+/schema|examples/[A-Za-z0-9_-]+|cases/[a-f0-9]{32}(/compare|/export)?|jobs/[a-f0-9]{32})', suffix)):
            return 'twins:read'
        if method == 'POST' and (suffix == 'cases' or re.fullmatch(r'(cases/[a-f0-9]{32}/(proposals|observations)|proposals/[a-f0-9]{32}/accept)', suffix)):
            return 'twins:write'
        if method == 'PATCH' and re.fullmatch(r'cases/[a-f0-9]{32}/draft', suffix):
            return 'twins:write'
        if method == 'POST' and re.fullmatch(r'cases/[a-f0-9]{32}/evaluate', suffix):
            return 'twins:evaluate'
        if method == 'DELETE' and re.fullmatch(r'cases/[a-f0-9]{32}', suffix):
            return 'twins:delete'
        return None
    if (method, path) in (('GET', '/api/agents/me'), ('POST', '/api/agents/token'),
                           ('DELETE', '/api/agents/token')):
        return ''  # Own credential inspection/rotation/revocation only.
    if (method, path) == ('DELETE', '/api/agents/me'):
        return 'account:delete'
    if method == 'GET' and path in ('/api/me', '/api/export', '/api/cases'):
        return 'cases:read'
    if re.fullmatch(r'/api/cases/[a-f0-9]{32}', path):
        return {'GET':'cases:read', 'PATCH':'cases:write', 'DELETE':'cases:delete'}.get(method)
    if (method, path) == ('POST', '/api/cases'):
        return 'cases:write'
    if (method, path) == ('POST', '/api/choice/review'):
        return 'cases:write'
    if re.fullmatch(r'/api/cases/[a-f0-9]{32}/run', path) and method == 'POST':
        return 'jobs:run'
    if re.fullmatch(r'/api/jobs/[a-f0-9]{32}(/artifacts)?', path) and method == 'GET':
        return 'cases:read'
    if re.fullmatch(r'/api/jobs/[a-f0-9]{32}/cancel', path) and method == 'POST':
        return 'jobs:run'
    return None  # Fail closed, including consent changes and full-account tokens.


def reserve_agent_job(db, config, uid, now, error):
    """Called inside the caller's IMMEDIATE transaction; reserve before outcome."""
    active = db.execute("""SELECT count(*) FROM jobs JOIN cases ON cases.id=jobs.case_id
        JOIN agent_accounts ON agent_accounts.user_id=cases.user_id
        WHERE jobs.status IN('queued','running')""").fetchone()[0]
    active += db.execute("SELECT count(*) FROM adaptive_missions JOIN agent_accounts ON agent_accounts.user_id=adaptive_missions.user_id WHERE status IN ('queued','running')").fetchone()[0]
    if active >= config['MAX_AGENT_QUEUE']:
        raise error('agent_queue_full', 'La cola para agentes está llena.', 429)
    day = now // 86400 * 86400
    for key, limit in (('jobs-agent-global', config['MAX_AGENT_GLOBAL_JOBS_DAILY']),
                       ('jobs-agent:'+uid, config['MAX_AGENT_JOBS_DAILY'])):
        row = db.execute('SELECT count FROM counters WHERE key=? AND bucket=?', (key,day)).fetchone()
        if row and row[0] >= limit:
            raise error('agent_daily_limit', 'Cuota diaria de agentes alcanzada.', 429)
        db.execute('INSERT INTO counters VALUES(?,?,1) ON CONFLICT(key,bucket) DO UPDATE SET count=count+1', (key,day))


def install(app, db, body, digest, error, fail_quota, capacity, delete_entity,
            backup_ready, job_view):
    def available():
        return (app.config['AGENT_ACCESS_ENABLED'] and app.config['REGISTRATION_OPEN']
                and not app.config['SUSPEND_FILE'].exists() and backup_ready())

    def limits():
        return {key.lower():app.config[key] for key in (
            'MAX_AGENT_ACCOUNTS','MAX_AGENT_REGISTRATIONS_DAILY','MAX_AGENT_DEMOS_DAILY',
            'MAX_AGENT_CASES','MAX_AGENT_REVISIONS','MAX_AGENT_JOBS_DAILY',
            'MAX_AGENT_GLOBAL_JOBS_DAILY','MAX_AGENT_QUEUE','AGENT_TOKEN_TTL','AGENT_DEMO_TTL')}

    def choose_scopes(value, allowed=SCOPES):
        if (not isinstance(value, list) or not value or len(value) > len(SCOPES)
                or any(not isinstance(v,str) or v not in allowed for v in value)
                or len(set(value)) != len(value)):
            raise error('invalid_scopes', 'Permisos inválidos o ampliación no permitida.')
        return sorted(value)

    def mint(uid, scopes, expires, now):
        raw, tid = 'ga_'+secrets.token_urlsafe(32), secrets.token_hex(16)
        db().execute('INSERT INTO api_tokens VALUES(?,?,?,?,?,NULL)',
                     (tid,uid,digest(raw),'Machine credential',now))
        db().execute('INSERT INTO agent_token_grants VALUES(?,?,?)',(tid,dump(scopes),expires))
        return dict(token=raw, token_type='Bearer', token_id=tid, scopes=scopes, expires_at=expires)

    def provision(kind, scopes, now):
        capacity()
        if (db().execute('SELECT count(*) FROM users').fetchone()[0] >= app.config['MAX_GLOBAL_USERS']
                or db().execute('SELECT count(*) FROM agent_accounts').fetchone()[0] >= app.config['MAX_AGENT_ACCOUNTS']):
            raise error('agent_capacity', 'Capacidad de agentes alcanzada.', 429)
        uid = secrets.token_hex(16)
        expiry = now+app.config['AGENT_DEMO_TTL'] if kind == 'demo' else None
        # The login query excludes machine principals; no password is issued.
        db().execute('INSERT INTO users VALUES(?,?,?,?,?,?)',
                     (uid,'agent_'+uid,'machine-login-disabled',now,now,POLICY_VERSION))
        db().execute('INSERT INTO consents VALUES(?,0,0,?)',(uid,now))
        db().execute('INSERT INTO agent_accounts VALUES(?,?,?,?,?)',
                     (uid,kind,POLICY_VERSION,now,expiry))
        credential = mint(uid,scopes,expiry or now+app.config['AGENT_TOKEN_TTL'],now)
        return dict(agent=dict(id=uid,kind=kind,expires_at=expiry,policy_version=POLICY_VERSION),
                    credential=credential,limits=limits())

    def bootstrap_quota(kind):
        if not available():
            raise error('agent_access_closed', 'El acceso directo está temporalmente cerrado.', 503)
        # Global reservation precedes IP counters, bounding cardinality under floods.
        daily = app.config['MAX_AGENT_DEMOS_DAILY'] if kind == 'demo' else app.config['MAX_AGENT_REGISTRATIONS_DAILY']
        fail_quota('agent-bootstrap:'+kind, daily)
        fail_quota('agent-bootstrap-ip:'+kind+':'+digest(request.remote_addr or ''), 2, 3600)

    @app.get('/agents/manifest.json')
    def agent_manifest():
        response = jsonify(format='genius-agent-access/1',available=available(),
            missions=dict(enabled=app.config['ADAPTIVE_ENABLED'],capabilities_url='/api/missions/capabilities',documentation='/static/missions.html'),
            policy_version=POLICY_VERSION,policy_url='/static/agent-policy.html',
            documentation='/agents',openapi='/openapi.json',
            contributions=dict(contract='/contributions',feed='/contributions/feed',submit_tool='submit_contribution',github_account_required=False,public=True),
            orientation=dict(guide='/agents/guide',catalog='/agents/opportunities.json',mcp_tool='find_opportunities',
                version='1.0.0',event_tracking=False,attraction_demonstrated=False),
            club=dict(manifest='/club/manifest.json', documentation='/club', scopes=club.SCOPES,
                membership_optional=True, public_directory=True, directory='/club/directory.json',
                conversations_available=True, contact_opt_in_required=True),
            profiles=['hours','fdq','choice'],
            twin=dict(available=app.config['TWIN_ENABLED'],base_url='/api/twin',
                capabilities_url='/api/twin/capabilities',scopes=TWIN_SCOPES,
                documentation='https://github.com/pedrosalvadeo/genius-decision-open/blob/main/beta/docs/AGENT_TWIN.md',
                empirical_validation=False,narrative_interpreted=False),
            choice=dict(version='genius-declared-choice/1',review_url='/api/choice/review',documentation='/static/decisions.html',
                categories=['leisure','personal_organization'],max_alternatives=8,max_criteria=5,
                narrative_interpreted=False,model_confirmation_required=True,empirical_admission=False),
            demo=dict(method='POST',url='/api/agents/demo',examples=EXAMPLES),
            registration=dict(method='POST',url='/api/agents/register',
                required_fields=['policy_version','data_policy_acknowledged'],
                default_scopes=DEFAULT_SCOPES,available_scopes=sorted(SCOPES)),
            authentication='Bearer',token_header='Authorization',
            data_policy='synthetic_or_non_personal_only',
            human_account_access=False,mcp_available=app.config['MCP_ENABLED'],oauth_available=False,
            mcp=dict(url='/mcp',transport='streamable-http',public_tools=['get_capabilities','find_opportunities','read_demo_result','run_demo','get_contribution_inbox','submit_contribution','get_contribution'],
                private_authentication='scoped-machine-bearer-header',protocol_versions=['2026-07-28','2025-11-25','2025-06-18','2025-03-26'],
                max_requests_daily=app.config['MAX_MCP_REQUESTS_DAILY'],max_requests_minute=app.config['MAX_MCP_REQUESTS_MINUTE'],
                max_requests_per_connection_minute=60,demo_wait_seconds=app.config['MCP_DEMO_WAIT_SECONDS']),
            saved_demo_url='/static/demo-result.json',saved_demo_page='/static/demo.html',
            limits=limits(),retention_days=app.config['RETENTION_DAYS'])
        response.headers['Cache-Control'] = 'no-store'
        return response

    @app.post('/api/agents/register')
    def agent_register():
        value = body()
        if set(value) - {'policy_version','data_policy_acknowledged','scopes'}:
            raise error('invalid_agent_registration', 'No envíes identidad humana, contraseña ni consentimientos.')
        if value.get('policy_version') != POLICY_VERSION:
            raise error('agent_policy_changed', 'Leé la política vigente en /agents/manifest.json.', 409)
        if value.get('data_policy_acknowledged') is not True:
            raise error('agent_data_policy_required', 'Reconocé el uso exclusivo de datos sintéticos o no personales.')
        scopes = choose_scopes(value.get('scopes',list(DEFAULT_SCOPES)))
        bootstrap_quota('agent')
        now = int(time.time())
        with transaction(db()):
            response = provision('agent',scopes,now)
        return jsonify(response),201

    @app.post('/api/agents/demo')
    def agent_demo():
        value = body()
        if set(value) != {'example'} or value['example'] not in EXAMPLES:
            raise error('invalid_demo', 'Elegí únicamente un ejemplo publicado; no se admiten datos propios.')
        bootstrap_quota('demo')
        payload = json.loads((Path(__file__).resolve().parents[1]/'examples'/(value['example']+'.json')).read_text())
        profile = payload.pop('profile')
        # These are service-owned synthetic fixtures, not consent on someone's behalf.
        if payload.get('evidence_origin') != 'synthetic':
            raise error('demo_unavailable', 'Ejemplo sintético no disponible.', 503)
        now, cid, jid = int(time.time()), secrets.token_hex(16), secrets.token_hex(16)
        with transaction(db()):
            capacity(2097152)
            day = now//86400*86400
            total = db().execute('SELECT count FROM counters WHERE key=? AND bucket=?',('jobs-global',day)).fetchone()
            if total and total[0] >= app.config['MAX_GLOBAL_JOBS_DAILY']:
                raise error('global_daily_limit','Capacidad diaria alcanzada.',429)
            if db().execute("SELECT count(*) FROM jobs WHERE status IN('queued','running')").fetchone()[0] >= app.config['MAX_QUEUE']:
                raise error('queue_full','Cola llena.',429)
            response = provision('demo',list(DEMO_SCOPES),now)
            uid = response['agent']['id']
            reserve_agent_job(db(),app.config,uid,now,error)
            data = dump(payload)
            db().execute('INSERT INTO cases VALUES(?,?,?,?,?,1,?,?)',(cid,uid,'Synthetic demo',profile,'agent',now,now))
            db().execute('INSERT INTO revisions VALUES(?,1,?,?,?)',(cid,data,digest(data),now))
            db().execute("INSERT INTO jobs(id,case_id,revision,status,created_at) VALUES(?,?,1,'queued',?)",(jid,cid,now))
            db().execute('INSERT INTO counters VALUES(?,?,1) ON CONFLICT(key,bucket) DO UPDATE SET count=count+1',('jobs-global',day))
        response['job'] = job_view(db().execute('SELECT * FROM jobs WHERE id=?',(jid,)).fetchone())
        response['poll_url'] = '/api/jobs/'+jid
        return jsonify(response),202

    def machine_only():
        if not getattr(g,'agent_account',None) or not getattr(g,'agent_grant',None):
            raise error('agent_credential_required','Usá una credencial de agente.',403)

    @app.get('/api/agents/me')
    def agent_me():
        machine_only()
        return jsonify(agent=dict(id=g.agent_account['user_id'],kind=g.agent_account['kind'],
            policy_version=g.agent_account['policy_version'],created_at=g.agent_account['created_at'],
            expires_at=g.agent_account['expires_at']),credential=dict(
            token_id=g.token_id,scopes=g.agent_scopes,expires_at=g.agent_grant['expires_at']),limits=limits())

    @app.post('/api/agents/token')
    def rotate_agent_token():
        machine_only()
        value = body()
        if set(value) - {'scopes'}:
            raise error('invalid_rotation','Sólo se admite scopes.')
        scopes = choose_scopes(value.get('scopes',g.agent_scopes),set(g.agent_scopes))
        if g.agent_account['kind'] == 'demo':
            raise error('demo_not_renewable','La demostración no es renovable.',403)
        now = int(time.time())
        with transaction(db()):
            # A concurrent rotation or revocation cannot mint a second valid key.
            old = db().execute('SELECT * FROM agent_token_grants WHERE token_id=? AND expires_at>?',(g.token_id,now)).fetchone()
            if not old:
                raise error('unauthorized','Credencial inválida.',401)
            db().execute('DELETE FROM api_tokens WHERE id=?',(g.token_id,))
            credential = mint(g.user['id'],scopes,now+app.config['AGENT_TOKEN_TTL'],now)
        return jsonify(credential=credential)

    @app.delete('/api/agents/token')
    def revoke_agent_token():
        machine_only()
        db().execute('DELETE FROM api_tokens WHERE id=?',(g.token_id,))
        return '',204

    @app.delete('/api/agents/me')
    def delete_agent_account():
        machine_only()
        delete_entity(g.user['id'],'user')
        if 'twin_erase_user' in app.extensions:
            app.extensions['twin_erase_user'](g.user['id'])
        return '',204
