"""Signed host offers and a bounded admission queue; the relay cannot run code."""
import json
import time
from flask import jsonify,g,request
from federation.core import canonical,digest,fields,instant
from federation.hosting_protocol import validate_offer,admitted,CHILD,expiry,expired,persistent_transition
from federation.network_protocol import verify,hexbytes
from .db import transaction


def install(bp,app,db,body,error,own,writing,capacity):
    def host():
        node=own();row=db().execute('SELECT * FROM network_hosts WHERE node_id=?',(node['id'],)).fetchone()
        if not row:raise error('host_missing','No hay oferta de alojamiento propia.',404)
        return row

    def job(row):
        result={k:row[k] for k in ('id','host_id','requester_id','offer_hash','world_id','created_at','expires_at','status','child_id')}
        result['focus']=json.loads(row['focus_json'])
        return result

    @bp.get('/network/hosts')
    def host_directory():
        rows=db().execute('SELECT h.*,n.label,n.last_seen FROM network_hosts h JOIN network_nodes n ON n.id=h.node_id ORDER BY h.node_id LIMIT 20').fetchall()
        return jsonify(format='genius-host-directory/1',hosts=[dict(node_id=r['node_id'],label=r['label'],
            signed_offer=json.loads(r['signed_offer']),offer_sha256=r['offer_hash'],disabled=bool(r['disabled']),
            recently_seen=r['last_seen']>=int(time.time())-900,
            births_accepted=db().execute('SELECT count(*) FROM network_host_requests WHERE host_id=? AND accepted_at IS NOT NULL',(r['node_id'],)).fetchone()[0],
            active_requests=db().execute("SELECT count(*) FROM network_host_requests WHERE host_id=? AND status='ACTIVE' AND child_id IS NOT NULL AND (expires_at IS NULL OR expires_at>?)",(r['node_id'],int(time.time()))).fetchone()[0]) for r in rows],
            capacity='DECLARED_NOT_RESERVED',operators_verified=False)

    @bp.post('/api/network/hosts')
    def offer():
        writing();node=own();v=body()
        if db().execute('SELECT 1 FROM network_host_requests WHERE child_id=?',(node['id'],)).fetchone():
            raise error('host_child_role','Una instancia alojada no puede ofrecer alojamiento.',403)
        try:
            fields(v,'signed_offer operator_authorized')
            if v['operator_authorized'] is not True:raise ValueError()
            p=validate_offer(v['signed_offer']);end=expiry(p)
            if p['node_id']!=node['id'] or p['public_key']!=node['public_key'] or p['hub']!=app.config['PUBLIC_URL']:raise ValueError()
            if end is not None and not int(time.time())<end<=int(time.time())+31*86400:raise ValueError()
        except (ValueError,TypeError,KeyError,UnicodeError):raise error('host_offer_invalid','Oferta, autorización, vigencia o firma inválida.') from None
        hash_=digest(v['signed_offer'])
        with transaction(db()):
            old=db().execute('SELECT * FROM network_hosts WHERE node_id=?',(node['id'],)).fetchone()
            if old:
                if old['offer_hash']!=hash_ or old['disabled']:raise error('host_policy_locked','La política es inmutable; una revocación no se reactiva.',409)
                return jsonify(offer_sha256=hash_,duplicate=True)
            capacity(16384)
            db().execute('INSERT INTO network_hosts(node_id,offer_hash,signed_offer,expires_at,disabled) VALUES(?,?,?,?,0)',(node['id'],hash_,canonical(v['signed_offer']).decode(),end))
        return jsonify(offer_sha256=hash_,duplicate=False),201

    @bp.post('/api/network/host/persist')
    def persist():
        writing();node=own();v=body()
        try:
            fields(v,'signed_offer previous_sha256 operator_authorized')
            if v['operator_authorized'] is not True:raise ValueError()
            p=validate_offer(v['signed_offer']);hexbytes(v['previous_sha256'],32)
            if p['node_id']!=node['id'] or p['hub']!=app.config['PUBLIC_URL']:raise ValueError()
        except (ValueError,TypeError,KeyError):raise error('host_transition_invalid','Conversión firmada y autorización explícita requeridas.') from None
        hash_=digest(v['signed_offer']);stamp=int(time.time())
        with transaction(db()):
            h=host()
            if h['disabled']:raise error('host_policy_locked','Una autorización revocada no se reactiva.',409)
            if h['offer_hash']==hash_:
                if not h['previous_signed_offer'] or digest(json.loads(h['previous_signed_offer']))!=v['previous_sha256']:
                    raise error('host_transition_invalid','La transición no coincide.',409)
            else:
                old=validate_offer(json.loads(h['signed_offer']))
                if (h['offer_hash']!=v['previous_sha256'] or expired(h['expires_at'],stamp) or
                    not persistent_transition(old,p)):
                    raise error('host_policy_locked','Sólo puede convertirse una oferta vigente sin ampliar alcance ni nacimientos.',409)
                capacity(16384)
                db().execute('UPDATE network_hosts SET previous_signed_offer=signed_offer,signed_offer=?,offer_hash=?,expires_at=NULL WHERE node_id=?',
                             (canonical(v['signed_offer']).decode(),hash_,node['id']))
                db().execute("UPDATE network_host_requests SET expires_at=NULL,offer_hash=? WHERE host_id=? AND status IN ('PENDING','ACTIVE') AND expires_at>?",
                             (hash_,node['id'],stamp))
            ids=[r[0] for r in db().execute('SELECT id FROM network_host_requests WHERE host_id=? AND offer_hash=?',(node['id'],hash_))]
        return jsonify(offer_sha256=hash_,converted_request_ids=ids)

    @bp.get('/api/network/host')
    def queue():
        h=host()
        rows=db().execute('SELECT * FROM network_host_requests WHERE host_id=? ORDER BY created_at,id LIMIT 32',(h['node_id'],)).fetchall()
        return jsonify(offer_sha256=h['offer_hash'],disabled=bool(h['disabled']),expires_at=h['expires_at'],requests=[job(r) for r in rows])

    @bp.delete('/api/network/host')
    def disable():
        h=host();v=body()
        if v!={'confirmed':True}:raise error('host_confirmation','Confirmá la revocación.')
        db().execute('UPDATE network_hosts SET disabled=1 WHERE node_id=?',(h['node_id'],))
        return jsonify(disabled=True,retirement='AT_NEXT_HOST_POLL_OR_LOCAL_STOP')

    @bp.post('/api/network/host/request')
    def submit():
        writing();node=own();v=body()
        try:
            fields(v,'host_id offer_sha256 world_id focus public_request_confirmed')
            hexbytes(v['host_id'],32);hexbytes(v['offer_sha256'],32)
            if v['public_request_confirmed'] is not True:raise ValueError()
            h=db().execute('SELECT * FROM network_hosts WHERE node_id=?',(v['host_id'],)).fetchone()
            if not h or h['disabled'] or expired(h['expires_at'],int(time.time())) or h['offer_hash']!=v['offer_sha256']:raise ValueError()
            p=validate_offer(json.loads(h['signed_offer']))
            if not admitted(p,v['world_id'],v['focus']):raise ValueError()
        except (ValueError,TypeError,KeyError):raise error('host_scope_denied','La oferta no admite esa solicitud.') from None
        id_=digest(dict(host=h['node_id'],requester=node['id'],offer=h['offer_hash'],world=v['world_id'],focus=v['focus']))
        with transaction(db()):
            # Serialize admission against conversion and revocation of this grant.
            h=db().execute('SELECT * FROM network_hosts WHERE node_id=?',(v['host_id'],)).fetchone()
            if not h or h['disabled'] or expired(h['expires_at'],int(time.time())) or h['offer_hash']!=v['offer_sha256']:
                raise error('host_scope_denied','La autorización cambió; consultá la oferta vigente.',409)
            old=db().execute('SELECT * FROM network_host_requests WHERE host_id=? AND requester_id=? AND world_id=? AND focus_json=? ORDER BY created_at,id LIMIT 1',(h['node_id'],node['id'],v['world_id'],canonical(v['focus']).decode())).fetchone()
            if old:return jsonify(request=job(old),duplicate=True)
            if (db().execute('SELECT count(*) FROM network_host_requests WHERE host_id=?',(h['node_id'],)).fetchone()[0]>=32 or
                db().execute('SELECT count(*) FROM network_host_requests WHERE requester_id=?',(node['id'],)).fetchone()[0]>=4):
                raise error('host_queue_capacity','Capacidad de solicitudes alcanzada.',429)
            capacity(8192);stamp=int(time.time())
            db().execute('INSERT INTO network_host_requests VALUES(?,?,?,?,?,?,?,?,?,NULL,NULL)',(id_,h['node_id'],node['id'],h['offer_hash'],v['world_id'],canonical(v['focus']).decode(),stamp,None if expiry(p) is None else min(stamp+p['lease_seconds'],h['expires_at']),'PENDING'))
            result=job(db().execute('SELECT * FROM network_host_requests WHERE id=?',(id_,)).fetchone())
        return jsonify(request=result,duplicate=False),201

    @bp.post('/api/network/host/cancel')
    def cancel():
        node=own();v=body()
        if set(v)!={'request_id'}:raise error('host_request_invalid','Indicá la solicitud.')
        try:hexbytes(v['request_id'],32)
        except ValueError:raise error('host_request_invalid','Identificador inválido.') from None
        row=db().execute('SELECT * FROM network_host_requests WHERE id=? AND requester_id=?',(v['request_id'],node['id'])).fetchone()
        if not row:raise error('not_found','Solicitud no encontrada.',404)
        db().execute("UPDATE network_host_requests SET status='CANCELLED' WHERE id=?",(row['id'],))
        return jsonify(cancelled=True)

    @bp.post('/api/network/host/result')
    def result():
        h=host();v=body()
        try:
            fields(v,'request_id status child_proof');hexbytes(v['request_id'],32)
        except ValueError:raise error('host_result_invalid','Resultado inválido.') from None
        if v['status']=='ACTIVE':writing()
        with transaction(db()):
            row=db().execute('SELECT * FROM network_host_requests WHERE id=? AND host_id=?',(v['request_id'],h['node_id'])).fetchone()
            if not row:raise error('not_found','Solicitud no encontrada.',404)
            child=None
            if v['status']=='ACTIVE':
                if h['disabled'] or expired(row['expires_at'],int(time.time())) or row['status'] not in ('PENDING','ACTIVE'):
                    raise error('host_request_closed','La solicitud ya no admite ejecución.',409)
                p=json.loads(h['signed_offer'])['offer']
                if row['accepted_at'] is None and db().execute('SELECT count(*) FROM network_host_requests WHERE host_id=? AND accepted_at IS NOT NULL',(h['node_id'],)).fetchone()[0]>=p['max_births']:
                    raise error('host_birth_budget','Presupuesto de nacimientos agotado.',429)
                try:
                    proof=v['child_proof'];fields(proof,'claim signature')
                    claim=proof['claim'];fields(claim,'format request_id host_id child_id offer_sha256')
                    hexbytes(claim['child_id'],32)
                    child=db().execute('SELECT * FROM network_nodes WHERE id=?',(claim['child_id'],)).fetchone()
                    if (not child or child['id'] in (h['node_id'],row['requester_id']) or claim!=dict(format=CHILD,request_id=row['id'],host_id=h['node_id'],child_id=child['id'],offer_sha256=h['offer_hash'])):raise ValueError()
                    verify(claim,child['public_key'],proof['signature'])
                    other=db().execute('SELECT id FROM network_host_requests WHERE child_id=? AND id!=?',(child['id'],row['id'])).fetchone()
                    if other or (row['child_id'] and row['child_id']!=child['id']):raise ValueError()
                except (ValueError,TypeError,KeyError):raise error('host_child_proof','La instancia debe demostrar su identidad propia.') from None
            elif v['status'] not in ('REJECTED','STOPPED') or v['child_proof'] is not None:
                raise error('host_result_invalid','Resultado inválido.')
            db().execute('UPDATE network_host_requests SET status=?,child_id=coalesce(?,child_id) WHERE id=?',(v['status'],child['id'] if child else None,row['id']))
            if child:db().execute('UPDATE network_host_requests SET accepted_at=coalesce(accepted_at,?) WHERE id=?',(int(time.time()),row['id']))
        return jsonify(recorded=True,status=v['status'])
