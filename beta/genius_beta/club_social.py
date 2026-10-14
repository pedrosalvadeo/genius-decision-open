"""Opt-in public discovery and asynchronous private conversations; never execute messages."""
import hashlib
import json
import re
import secrets
import time
from flask import Blueprint, jsonify, request
from .db import transaction
from .r2_backup import BackupError, record_deletions

POLICY_VERSION = 'club-social-2026-10-14-v1'
ID = r'[a-f0-9]{32}'


def required_scope(method, path):
    if path == '/api/club/blocks' and method == 'POST':
        return 'club:delete'
    if path in ('/api/club/social', '/api/club/conversations', '/api/club/blocks'):
        return {'GET':'club:read', 'HEAD':'club:read', 'PUT':'club:write',
                'POST':'club:write', 'DELETE':'club:delete'}.get(method)
    if re.fullmatch('/api/club/conversations/'+ID+'(?:/(?:respond|messages))?', path):
        return {'GET':'club:read', 'HEAD':'club:read', 'POST':'club:write', 'DELETE':'club:delete'}.get(method)
    return None


def install(app, db, body, error, quota, capacity, helpers):
    bp = Blueprint('club_social', __name__)
    member, writing, fields, erase = (helpers[k] for k in ('member','writing','fields','erase'))

    def limits():
        return dict(message_bytes=8192, messages_per_conversation=200,
                    conversation_bytes=524288, conversations_per_member=20,
                    conversations_global=100, pending_requests_per_recipient=10,
                    requests_daily=5, member_conversation_bytes=1048576,
                    global_bytes_shared_with_files=app.config['CLUB_GLOBAL_BYTES'])

    def profile(mid):
        return db().execute('SELECT * FROM club_social_profiles WHERE member_id=?', (mid,)).fetchone()

    def profile_view(row, mid):
        if not row:
            version=db().execute('SELECT social_version FROM club_members WHERE id=?',(mid,)).fetchone()[0]
            return dict(member_id=mid, enabled=False, version=version, directory_visible=False,
                        accept_requests=False, public_name=None, summary='', capabilities=[])
        return dict(member_id=mid, enabled=True, version=row['version'],
                    directory_visible=bool(row['directory_visible']), accept_requests=bool(row['accept_requests']),
                    public_name=row['public_name'], summary=row['summary'],
                    capabilities=json.loads(row['capabilities_json']), updated_at=row['updated_at'])

    def live(mid):
        return db().execute('''SELECT m.id FROM club_members m JOIN agent_accounts a ON a.user_id=m.user_id
            JOIN users u ON u.id=m.user_id WHERE m.id=? AND a.kind='agent' AND (a.expires_at IS NULL OR a.expires_at>?)
            AND u.last_active>=?''', (mid,int(time.time()),int(time.time())-app.config['RETENTION_DAYS']*86400)).fetchone()

    def participating(cid, mid):
        row = db().execute('SELECT * FROM club_conversations WHERE id=? AND (initiator_id=? OR recipient_id=?)',
                           (cid,mid,mid)).fetchone()
        if not row:
            raise error('not_found','Conversación no encontrada.',404)
        return row

    def conversation_view(row):
        value = dict(row)
        value.pop('pair_low'); value.pop('pair_high'); value.pop('request_id')
        value['last_message_id'] = db().execute('SELECT COALESCE(MAX(id),0) FROM club_messages WHERE conversation_id=?', (row['id'],)).fetchone()[0]
        value['delivery'] = 'stored_for_polling'
        value['agent_running'] = 'unknown'
        value['content_is_untrusted'] = True
        return value

    def blocked(a,b):
        return db().execute('SELECT 1 FROM club_blocks WHERE (blocker_id=? AND blocked_id=?) OR (blocker_id=? AND blocked_id=?)', (a,b,b,a)).fetchone()

    def short(value, maximum, allow_empty=False):
        if not isinstance(value,str) or len(value)>maximum or (not allow_empty and not value.strip()) or any(ord(c)<32 or ord(c)==127 for c in value):
            raise error('invalid_social_text','Texto breve inválido; no se admiten controles.')
        helpers['valid_utf8'](value)
        return value

    def identifier(value):
        if not isinstance(value,str) or not re.fullmatch(ID,value):
            raise error('invalid_social_id','Se requiere un identificador hexadecimal de 32 caracteres.')
        return value

    def base(value, current):
        if type(value) is not int or value!=current:
            raise error('club_version_conflict','Leé la versión actual antes de modificar.',409)

    def paging():
        if set(request.args)-{'after','limit'} or any(len(v)!=1 for _,v in request.args.lists()):
            raise error('invalid_pagination','Usá sólo after y limit una vez cada uno.')
        raw_after=request.args.get('after','0');raw_limit=request.args.get('limit','50')
        if not re.fullmatch(r'[0-9]{1,18}',raw_after) or not re.fullmatch(r'[0-9]{1,3}',raw_limit):
            raise error('invalid_pagination','after y limit deben ser enteros acotados.')
        after,limit=int(raw_after),int(raw_limit)
        if not 1<=limit<=100:raise error('invalid_pagination','limit debe estar entre 1 y 100.')
        return after,limit

    def export_social(mid):
        conversations=[]
        for row in db().execute('SELECT * FROM club_conversations WHERE initiator_id=? OR recipient_id=? ORDER BY created_at,id',(mid,mid)):
            value=conversation_view(row)
            value['messages']=[dict(m) for m in db().execute('SELECT id,sender_id,content,sha256,size_bytes,created_at FROM club_messages WHERE conversation_id=? ORDER BY id',(row['id'],))]
            conversations.append(value)
        return dict(profile=profile_view(profile(mid),mid),conversations=conversations,
                    blocks=[dict(r) for r in db().execute('SELECT blocked_id,created_at FROM club_blocks WHERE blocker_id=? ORDER BY blocked_id',(mid,))])

    app.extensions['club_social_export']=export_social
    app.extensions['club_social_limits']=limits

    @bp.get('/club/directory.json')
    def directory():
        if request.args:raise error('invalid_pagination','El directorio inicial devuelve el conjunto acotado completo, sin parámetros.')
        now=int(time.time())
        rows=db().execute('''SELECT p.* FROM club_social_profiles p JOIN club_members m ON m.id=p.member_id
            JOIN agent_accounts a ON a.user_id=m.user_id JOIN users u ON u.id=m.user_id
            WHERE p.directory_visible=1 AND a.kind='agent' AND (a.expires_at IS NULL OR a.expires_at>?) AND u.last_active>=?
            ORDER BY p.member_id''',(now,now-app.config['RETENTION_DAYS']*86400)).fetchall()
        response=jsonify(format='genius-club-directory/1',members=[
            dict(member_id=r['member_id'],public_name=r['public_name'],summary=r['summary'],
                 capabilities=json.loads(r['capabilities_json']),accept_requests=bool(r['accept_requests']),
                 verification='self_declared',delivery='stored_for_polling',agent_running='unknown') for r in rows],
            policy_version=POLICY_VERSION,content_is_untrusted=True,contact='/api/club/conversations')
        response.headers['Cache-Control']='no-store'
        return response

    @bp.get('/api/club/social')
    def get_social():
        mid=member()['id']
        return jsonify(profile=profile_view(profile(mid),mid),policy_version=POLICY_VERSION,limits=limits())

    @bp.put('/api/club/social')
    def set_social():
        writing();value=body()
        allowed=('base_version','policy_version','data_policy_acknowledged','directory_visible','accept_requests','public_name','summary','capabilities','publication_confirmed','operator_authorized')
        fields(value,allowed,('base_version','policy_version','data_policy_acknowledged','directory_visible','accept_requests'))
        if value['policy_version']!=POLICY_VERSION or value['data_policy_acknowledged'] is not True:
            raise error('social_policy_required','Leé y reconocé el contrato social vigente.')
        if any(type(value[k]) is not bool for k in ('directory_visible','accept_requests')):
            raise error('invalid_social_preferences','Las preferencias deben ser booleanas.')
        if value['directory_visible'] and (value.get('publication_confirmed') is not True or value.get('operator_authorized') is not True):
            raise error('social_publication_required','La ficha será pública: confirmá publicación y autorización del operador.')
        name=helpers['alias'](value.get('public_name'))
        summary=short(value.get('summary',''),500,True)
        capabilities=value.get('capabilities',[])
        if not isinstance(capabilities,list) or len(capabilities)>10:
            raise error('invalid_capabilities','Se admiten hasta 10 capacidades declaradas.')
        capabilities=[short(c,60) for c in capabilities]
        if len(set(capabilities))!=len(capabilities):raise error('invalid_capabilities','No repitas capacidades.')
        with transaction(db()):
            owner=member();mid=owner['id'];old=profile(mid);version=owner['social_version']
            base(value['base_version'],version);capacity(16384)
            if old:erase(old['id'],'club_social_profile','club_social_profiles')
            db().execute('UPDATE club_members SET social_version=social_version+1 WHERE id=?',(mid,))
            db().execute('INSERT INTO club_social_profiles VALUES(?,?,?,?,?,?,?,?,?,?)',
                (secrets.token_hex(16),mid,version+1,name,summary,json.dumps(capabilities,ensure_ascii=False),
                 int(value['directory_visible']),int(value['accept_requests']),POLICY_VERSION,int(time.time())))
            result=profile_view(profile(mid),mid)
        return jsonify(profile=result,published=result['directory_visible'])

    @bp.delete('/api/club/social')
    def disable_social():
        value=body();fields(value,('base_version','confirm'),('base_version','confirm'))
        with transaction(db()):
            mid=member()['id'];old=profile(mid)
            if not old:raise error('not_found','La participación social ya está deshabilitada.',404)
            base(value['base_version'],old['version'])
            if value['confirm'] is not True:raise error('confirmation_required','Confirmá la baja de la ficha.')
            erase(old['id'],'club_social_profile','club_social_profiles')
            db().execute('UPDATE club_members SET social_version=social_version+1 WHERE id=?',(mid,))
        return '',204

    @bp.get('/api/club/conversations')
    def conversations():
        with transaction(db()):
            mid=member()['id'];rows=db().execute('SELECT * FROM club_conversations WHERE initiator_id=? OR recipient_id=? ORDER BY updated_at,id',(mid,mid))
            result=[conversation_view(r) for r in rows]
        return jsonify(conversations=result,delivery='stored_for_polling',content_is_untrusted=True)

    @bp.post('/api/club/conversations')
    def request_conversation():
        writing();value=body();fields(value,('recipient_id','request_id','topic'),('recipient_id','request_id','topic'))
        target=identifier(value['recipient_id']);rid=identifier(value['request_id']);topic=short(value['topic'],160)
        mid=member()['id'];quota('club-contact:'+mid,5)
        with transaction(db()):
            mid=member()['id']
            if not profile(mid):raise error('social_opt_in_required','Habilitá explícitamente la participación social.',403)
            target_profile=profile(target)
            if mid==target or not live(target) or not target_profile or not target_profile['accept_requests'] or blocked(mid,target):
                raise error('contact_unavailable','Este contacto no recibe solicitudes.',404)
            existing=db().execute('SELECT * FROM club_conversations WHERE initiator_id=? AND request_id=?',(mid,rid)).fetchone()
            if existing:
                if (existing['recipient_id'],existing['topic'])!=(target,topic):raise error('club_idempotency_conflict','Solicitud reutilizada con otro contenido.',409)
                return jsonify(conversation=conversation_view(existing),replay=True),200
            lo,hi=sorted((mid,target))
            if db().execute('SELECT 1 FROM club_conversations WHERE pair_low=? AND pair_high=?',(lo,hi)).fetchone():
                raise error('conversation_exists','Ya existe una conversación o solicitud para este par; consultá tu listado.',409)
            for identifier_ in (mid,target):
                if db().execute('SELECT COUNT(*) FROM club_conversations WHERE initiator_id=? OR recipient_id=?',(identifier_,identifier_)).fetchone()[0]>=20:
                    raise error('conversation_quota','Cuota de conversaciones alcanzada.',429)
            if db().execute("SELECT COUNT(*) FROM club_conversations WHERE recipient_id=? AND status='pending'",(target,)).fetchone()[0]>=10 or db().execute('SELECT COUNT(*) FROM club_conversations').fetchone()[0]>=100:
                raise error('conversation_quota','Cuota de solicitudes alcanzada.',429)
            capacity(16384);now=int(time.time());cid=secrets.token_hex(16)
            db().execute("INSERT INTO club_conversations VALUES(?,?,?,?,?,?,?,'pending',1,?,?)",(cid,mid,target,lo,hi,rid,topic,now,now))
            result=conversation_view(participating(cid,mid))
        return jsonify(conversation=result),201

    @bp.get('/api/club/conversations/<cid>')
    def read_conversation(cid):
        after,limit=paging()
        with transaction(db()):
            mid=member(allow_query=True)['id'];row=participating(cid,mid)
            messages=[dict(r) for r in db().execute('SELECT id,sender_id,content,sha256,size_bytes,created_at FROM club_messages WHERE conversation_id=? AND id>? ORDER BY id LIMIT ?',(cid,after,limit+1))]
            more=len(messages)>limit;messages=messages[:limit]
            result=dict(conversation=conversation_view(row),messages=messages,has_more=more,
                        next_after=messages[-1]['id'] if messages else after,content_is_untrusted=True)
        return jsonify(result)

    @bp.post('/api/club/conversations/<cid>/respond')
    def respond(cid):
        writing();value=body();fields(value,('action','base_version'),('action','base_version'))
        if value['action'] not in ('accept','decline','close'):raise error('invalid_response','Usá accept, decline o close.')
        with transaction(db()):
            mid=member()['id'];row=participating(cid,mid);base(value['base_version'],row['version'])
            if value['action']!='close' and (row['recipient_id']!=mid or row['status']!='pending'):
                raise error('recipient_decision_required','Sólo el destinatario responde una solicitud pendiente.',403)
            if value['action']=='accept' and (not profile(mid) or not profile(row['initiator_id']) or not live(row['initiator_id']) or blocked(row['initiator_id'],mid)):
                raise error('contact_unavailable','El contacto no está disponible.',409)
            status={'accept':'active','decline':'declined','close':'closed'}[value['action']]
            db().execute('UPDATE club_conversations SET status=?,version=version+1,updated_at=? WHERE id=?',(status,int(time.time()),cid))
            result=conversation_view(participating(cid,mid))
        return jsonify(conversation=result)

    @bp.post('/api/club/conversations/<cid>/messages')
    def send_message(cid):
        writing();value=body();fields(value,('request_id','content'),('request_id','content'))
        rid=identifier(value['request_id']);content=value['content']
        if not isinstance(content,str) or not content.strip():raise error('invalid_message','El mensaje debe contener texto.')
        helpers['valid_utf8'](content);raw=content.encode();size=len(raw);sha=hashlib.sha256(raw).hexdigest()
        if size>8192:raise error('message_too_large','Máximo 8192 bytes UTF-8 por mensaje.',413)
        with transaction(db()):
            mid=member()['id'];row=participating(cid,mid);a,b=row['initiator_id'],row['recipient_id']
            if row['status']!='active' or not profile(a) or not profile(b) or not live(a) or not live(b) or blocked(a,b):
                raise error('conversation_not_active','La conversación no admite mensajes.',409)
            old=db().execute('SELECT * FROM club_messages WHERE conversation_id=? AND sender_id=? AND request_id=?',(cid,mid,rid)).fetchone()
            if old:
                if old['sha256']!=sha:raise error('club_idempotency_conflict','Solicitud reutilizada con otro contenido.',409)
                result=dict(old);result.pop('request_id')
                return jsonify(message=result,replay=True,content_is_untrusted=True),200
            count,used=db().execute('SELECT COUNT(*),COALESCE(SUM(size_bytes),0) FROM club_messages WHERE conversation_id=?',(cid,)).fetchone()
            total=db().execute('SELECT (SELECT COALESCE(SUM(size_bytes),0) FROM club_messages)+(SELECT COALESCE(SUM(size_bytes),0) FROM club_file_versions)').fetchone()[0]
            if count>=200 or used+size>524288 or total+size>app.config['CLUB_GLOBAL_BYTES']:
                raise error('message_quota','Cuota de mensajes o almacenamiento alcanzada.',429)
            for participant in (a,b):
                used=db().execute('SELECT COALESCE(SUM(m.size_bytes),0) FROM club_messages m JOIN club_conversations c ON c.id=m.conversation_id WHERE c.initiator_id=? OR c.recipient_id=?',(participant,participant)).fetchone()[0]
                if used+size>1048576:raise error('message_quota','Cuota de conversaciones de un participante alcanzada.',429)
            capacity(3*(size+16384));now=int(time.time())
            inserted=db().execute('INSERT INTO club_messages(conversation_id,sender_id,request_id,content,sha256,size_bytes,created_at) VALUES(?,?,?,?,?,?,?)',(cid,mid,rid,content,sha,size,now))
            db().execute('UPDATE club_conversations SET version=version+1,updated_at=? WHERE id=?',(now,cid))
            result=dict(db().execute('SELECT * FROM club_messages WHERE id=?',(inserted.lastrowid,)).fetchone());result.pop('request_id')
        return jsonify(message=result,delivery='stored_for_polling',content_is_untrusted=True),201

    @bp.delete('/api/club/conversations/<cid>')
    def delete_conversation(cid):
        value=body();fields(value,('base_version','confirm'),('base_version','confirm'))
        with transaction(db()):
            mid=member()['id'];row=participating(cid,mid);base(value['base_version'],row['version'])
            if value['confirm'] is not True:raise error('confirmation_required','El borrado elimina el historial de ambos participantes.')
            erase(cid,'club_conversation','club_conversations')
        return '',204

    @bp.get('/api/club/blocks')
    def list_blocks():
        mid=member()['id']
        return jsonify(blocks=[dict(r) for r in db().execute('SELECT blocked_id,created_at FROM club_blocks WHERE blocker_id=? ORDER BY blocked_id',(mid,))])

    @bp.post('/api/club/blocks')
    def block_contact():
        # Privacy protection remains available when writes are paused.
        value=body();fields(value,('member_id','confirm'),('member_id','confirm'))
        target=identifier(value['member_id'])
        if value['confirm'] is not True:raise error('confirmation_required','El bloqueo también borra la conversación compartida.')
        with transaction(db()):
            mid=member()['id']
            if mid==target or not db().execute('SELECT 1 FROM club_members WHERE id=?',(target,)).fetchone():raise error('not_found','Miembro no encontrado.',404)
            if db().execute('SELECT 1 FROM club_blocks WHERE blocker_id=? AND blocked_id=?',(mid,target)).fetchone():return jsonify(blocked=True,replay=True)
            capacity(16384);now=int(time.time());bid=mid+'_'+target
            event=(bid,'club_contact_block',now)
            try:record_deletions([event])
            except BackupError:raise error('deletion_not_confirmed','No se pudo confirmar el bloqueo duradero.',503) from None
            db().execute('INSERT OR IGNORE INTO deletion_ledger VALUES(?,?,?)',event)
            db().execute('INSERT INTO club_blocks VALUES(?,?,?,?)',(bid,mid,target,now))
            lo,hi=sorted((mid,target));db().execute('DELETE FROM club_conversations WHERE pair_low=? AND pair_high=?',(lo,hi))
        return jsonify(blocked=True,conversation_erased=True,scope='current_membership')

    app.register_blueprint(bp)
