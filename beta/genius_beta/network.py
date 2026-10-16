"""Public discovery and signed view relay; computation stays with the nodes."""
import json
import re
import time
from flask import Blueprint, g, jsonify, request, send_from_directory
from federation.core import canonical, digest, fields, identifier, instant, now, text
from federation.network_protocol import POLICY, ENROLL, identity, verify, verify_view
from .db import transaction

SCOPES=('network:read','network:write')
ID=re.compile('[0-9a-f]{64}')


def required_scope(method,path):
    if path in ('/api/network/me','/api/network/host') and method in ('GET','HEAD'):return 'network:read'
    if path=='/api/network/host' and method=='DELETE':return 'network:write'
    if path in ('/api/network/join','/api/network/heartbeat','/api/network/views','/api/network/hosts',
                '/api/network/host/persist','/api/network/host/request','/api/network/host/cancel','/api/network/host/result') and method=='POST':return 'network:write'
    return None


def install(app,db,body,error,quota,capacity,backup_ready):
    bp=Blueprint('network',__name__)

    def available():
        return app.config['AGENT_ACCESS_ENABLED'] and not app.config['SUSPEND_FILE'].exists() and backup_ready()

    def machine():
        if not g.agent_account or not g.agent_grant or g.agent_account['kind']!='agent':
            raise error('network_agent_required','Se requiere una credencial de agente persistente.',403)
        if request.args:raise error('network_query','Esta operación no admite parámetros.')

    def own():
        machine()
        row=db().execute('SELECT * FROM network_nodes WHERE user_id=?',(g.user['id'],)).fetchone()
        if not row:raise error('network_join_required','Primero incorporá el nodo.',404)
        return row

    def profile(row):
        return dict(id=row['id'],public_key=row['public_key'],label=row['label'],topics=json.loads(row['topics_json']),
                    created_at=row['created_at'],last_seen=row['last_seen'],
                    recently_seen=row['last_seen']>=int(time.time())-900,operator_identity_verified=False)

    def writing():
        machine()
        if not available():raise error('network_paused','Las incorporaciones y publicaciones están pausadas.',503)
        quota('network-write:'+g.user['id'],400)

    def cursor():
        value=request.args.get('after','')
        if value and not ID.fullmatch(value):raise error('network_cursor','Cursor inválido.')
        return value

    @bp.get('/network')
    def page():return send_from_directory(app.static_folder,'network.html')

    @bp.get('/organisms')
    def organisms_page():return send_from_directory(app.static_folder,'organisms.html')

    @bp.get('/network/organisms.json')
    def organisms_status():
        from federation.habitat import STATIONS
        from pathlib import Path
        reports=[];stamp=int(time.time())
        for station,label in STATIONS.items():
            path=Path(app.config['DATA_DIR'])/'living-habitats'/station/'public-report.json'
            if not path.exists():
                reports.append(dict(station=station,label=label,status='NOT_STARTED'));continue
            try:
                if path.stat().st_size>65536:raise ValueError()
                report=json.loads(path.read_bytes())
                if report['format']!='genius-living-report/1' or report['station']!=station:raise ValueError()
                # Explicit public projection; never expose credentials or local file paths.
                keys=('station','label','status','checked_at','next_check_at','node_id','source','source_kind',
                      'latest_observation','last_scored','last_prediction','last_archive','organism',
                      'physical_actions','wellbeing_effect','life_sustainment_probability','reason')
                report={k:report[k] for k in keys if k in report}
                report['report_stale']=stamp-int(instant(report['checked_at']).timestamp())>3*3600
                reports.append(report)
            except (OSError,ValueError,KeyError,TypeError):reports.append(dict(station=station,label=label,status='REPORT_UNAVAILABLE'))
        response=jsonify(format='genius-living-observatory/1',checked_at=stamp,organisms=reports,
            locations='SAME_OPERATOR_AND_HOST_DISTINCT_WEATHER_STATIONS',physical_actions=False,life_sustainment_probability=None)
        response.headers['Cache-Control']='no-store'
        return response

    @bp.get('/network/manifest.json')
    def manifest():
        counts=db().execute('SELECT count(*),sum(last_seen>=?) FROM network_nodes',(int(time.time())-900,)).fetchone()
        return jsonify(format='genius-public-network/1',policy_version=POLICY,available=available(),
            registration_available=available() and app.config['REGISTRATION_OPEN'],
            nodes=counts[0],recently_seen_nodes=counts[1] or 0,
            public_views=db().execute('SELECT count(*) FROM network_views').fetchone()[0],
            directory='/network/nodes',views='/network/views',documentation='/network',
            enrollment='/api/network/join',publication='/api/network/views',
            repository='https://github.com/pedrosalvadeo/genius-decision-open',
            package='https://github.com/pedrosalvadeo/genius-decision-open/tree/main/adaptive/federation',
            signature='Ed25519',node_id='sha256(raw_public_key)',
            topology='PUBLIC_RELAY_LOCAL_COMPUTATION',peer_to_peer=False,
            node_count_meaning='DISTINCT_KEYS_NOT_INDEPENDENT_OPERATORS_OR_TRUTH',
            limits=dict(agent_accounts=app.config['MAX_AGENT_ACCOUNTS'],registrations_daily=app.config['MAX_AGENT_REGISTRATIONS_DAILY'],
                        views_per_node=8,relay_views=160,page_size=20,view_bytes=24000),
            sharing='EXPLICIT_PUBLIC_NON_PERSONAL_WITH_OPERATOR_RIGHTS',
            hosting=dict(directory='/network/hosts',worker='genius-signed-world-reader/1',
                         automatic_only_with_local_authorization=True,max_births_per_grant=4,
                         lifecycle_modes=['TRIAL','PERSISTENT_REVOCABLE'],
                         remote_code_execution=False,recursive_reproduction=False),
            living_observers=dict(status='/network/organisms.json',page='/organisms',
                data='PUBLIC_REPORTED_METAR',stations=['SAME','SAMM'],physical_actions=False),
            genetics=dict(format='genius-genome/1',execution='LOCAL_NODE',
                documentation='https://github.com/pedrosalvadeo/genius-decision-open/blob/main/adaptive/federation/GENETICS.md',
                traits=['estimator','window'],selection='PROSPECTIVE_CONTEXTUAL_ERROR_COMPARISON',
                feedback='EXPLICIT_LOCAL_OBSERVATIONS_AND_LATER_OUTCOMES',code_mutation=False),
            empirical_validation=False,physical_actions=False)

    @bp.get('/network/nodes')
    def directory():
        if set(request.args)-{'after'}:raise error('network_query','Usá sólo after.')
        rows=db().execute('SELECT * FROM network_nodes WHERE id>? ORDER BY id LIMIT 21',(cursor(),)).fetchall()
        return jsonify(nodes=[profile(r) for r in rows[:20]],next_after=rows[19]['id'] if len(rows)>20 else None)

    @bp.get('/network/views')
    def index():
        try:
            if set(request.args)-{'after','world_id'}:raise ValueError()
            world=identifier(request.args.get('world_id'))
        except (ValueError,TypeError):raise error('network_world','Indicá un world_id válido.') from None
        rows=db().execute('SELECT hash,node_id,world_id,view_hash,created_at FROM network_views WHERE world_id=? AND hash>? ORDER BY hash LIMIT 21',(world,cursor())).fetchall()
        return jsonify(format='genius-network-index/1',world_id=world,views=[dict(r) for r in rows[:20]],
                       next_after=rows[19]['hash'] if len(rows)>20 else None)

    @bp.get('/network/worlds')
    def worlds():
        rows=db().execute('SELECT world_id,count(*) AS views,count(DISTINCT node_id) AS signing_nodes FROM network_views GROUP BY world_id ORDER BY world_id LIMIT 160').fetchall()
        return jsonify(worlds=[dict(r) for r in rows],completeness='DECLARED_VIEWS_ONLY_NOT_COVERAGE_OF_REALITY')

    @bp.get('/network/views/<hash_>')
    def read(hash_):
        if not ID.fullmatch(hash_):raise error('not_found','Vista no encontrada.',404)
        row=db().execute('SELECT envelope_json FROM network_views WHERE hash=?',(hash_,)).fetchone()
        if not row:raise error('not_found','Vista no encontrada.',404)
        return jsonify(envelope=json.loads(row['envelope_json']),sha256=hash_,origin_attestation='SIGNING_KEY_ONLY')

    @bp.post('/api/network/join')
    def join():
        writing();value=body()
        try:
            fields(value,'enrollment signature public_sharing_confirmed operator_authorized')
            if value['public_sharing_confirmed'] is not True or value['operator_authorized'] is not True:raise ValueError()
            doc=value['enrollment']
            fields(doc,'format policy_version account_id hub node_id public_key label topics')
            if (doc['format']!=ENROLL or doc['policy_version']!=POLICY or doc['account_id']!=g.user['id'] or
                doc['hub']!=app.config['PUBLIC_URL'] or doc['node_id']!=identity(doc['public_key'])):raise ValueError()
            text(doc['label'],80)
            if any(ord(c)<32 for c in doc['label']):raise ValueError()
            if type(doc['topics']) is not list or not 1<=len(doc['topics'])<=8 or len(set(doc['topics']))!=len(doc['topics']):raise ValueError()
            for topic in doc['topics']:identifier(topic)
            verify(doc,doc['public_key'],value['signature'])
        except (ValueError,TypeError,KeyError,UnicodeError,RecursionError):raise error('invalid_network_enrollment','Revisá identidad, firma, política y confirmaciones.') from None
        with transaction(db()):
            old=db().execute('SELECT * FROM network_nodes WHERE id=? OR user_id=?',(doc['node_id'],g.user['id'])).fetchone()
            if old:
                if old['id']!=doc['node_id'] or old['user_id']!=g.user['id']:raise error('network_identity_conflict','Identidad ya vinculada.',409)
                return jsonify(node=profile(old),duplicate=True)
            capacity(8192)
            stamp=int(time.time())
            db().execute('INSERT INTO network_nodes VALUES(?,?,?,?,?,?,?)',(doc['node_id'],g.user['id'],doc['public_key'],doc['label'],json.dumps(doc['topics']),stamp,stamp))
            result=profile(own())
        return jsonify(node=result,duplicate=False),201

    @bp.get('/api/network/me')
    def me():return jsonify(node=profile(own()))

    @bp.post('/api/network/heartbeat')
    def heartbeat():
        writing();row=own()
        if body():raise error('network_heartbeat','Enviá un objeto vacío.')
        db().execute('UPDATE network_nodes SET last_seen=? WHERE id=?',(int(time.time()),row['id']))
        return jsonify(node=profile(own()))

    @bp.post('/api/network/views')
    def publish():
        writing();node=own();value=body()
        try:
            fields(value,'envelope publication_confirmed operator_authorized')
            if value['publication_confirmed'] is not True or value['operator_authorized'] is not True:raise ValueError()
            signed=value['envelope'];view=verify_view(signed)
            if signed['node_id']!=node['id'] or signed['public_key']!=node['public_key']:raise ValueError()
            current=instant(now())
            if not instant(view['frame']['reference_time'])<=current<instant(view['valid_until']):raise ValueError()
            raw=canonical(signed);hash_=digest(signed)
        except (ValueError,TypeError,KeyError,UnicodeError,RecursionError):raise error('invalid_signed_view','Vista, propietario, firma, vigencia o confirmación inválidos.') from None
        with transaction(db()):
            old=db().execute('SELECT hash FROM network_views WHERE hash=?',(hash_,)).fetchone()
            if old:return jsonify(sha256=hash_,duplicate=True)
            if (db().execute('SELECT count(*) FROM network_views WHERE node_id=?',(node['id'],)).fetchone()[0]>=8 or
                db().execute('SELECT count(*) FROM network_views').fetchone()[0]>=160):
                raise error('network_view_capacity','Capacidad de vistas alcanzada; no se descartan fuentes ni afectados.',429)
            capacity(len(raw)*3+8192)
            db().execute('INSERT INTO network_views VALUES(?,?,?,?,?,?,?)',(hash_,node['id'],view['world_id'],digest(view),raw.decode(),len(raw),int(time.time())))
        return jsonify(sha256=hash_,view_hash=digest(view),duplicate=False),201

    from . import hosting
    hosting.install(bp,app,db,body,error,own,writing,capacity)
    app.register_blueprint(bp)
