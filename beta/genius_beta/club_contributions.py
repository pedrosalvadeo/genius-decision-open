"""Explicit publication of selected private versions; private provenance stays private."""
import hashlib
import json
import re
import time
from flask import Blueprint, jsonify
from . import contributions, contribution_reviews
from .db import transaction

ID = re.compile(r'^[a-f0-9]{32}$')
FIELDS = ('request_id','files','author','base_revision','summary','claim','reproduction','license','previous_id')
REQUIRED = ('request_id','files','base_revision','summary','claim','reproduction','license')


def required_scope(method,path):
    method='GET' if method=='HEAD' else method
    if path=='/api/club/contributions/prepare' and method=='POST':return 'club:read'
    if path=='/api/club/contributions':return {'GET':'club:read','POST':'club:write'}.get(method)
    if re.fullmatch(r'/api/club/contributions/[a-f0-9]{64}(?:/review)?',path) and method=='GET':return 'club:read'
    return None


def install(app,db,body,error,quota,capacity,helpers):
    bp=Blueprint('club_contributions',__name__)
    member,writing,fields=(helpers[k] for k in ('member','writing','fields'))
    contribution_reviews.install(app,db,quota,capacity,error)

    def inbox():return app.extensions['contribution_inbox']
    def reviews():return app.extensions['contribution_reviews']

    def own(mid,ident):
        row=db().execute('SELECT * FROM club_contributions WHERE member_id=? AND contribution_id=?',(mid,ident)).fetchone()
        if not row:raise error('not_found','Entrega no encontrada en esta membresía.',404)
        return row

    def request_value(value,publish=False):
        extra=('publication_sha256','publication_confirmed','operator_authorized') if publish else ()
        fields(value,(*FIELDS,*extra),(*REQUIRED,*extra))
        if not isinstance(value['request_id'],str) or not ID.fullmatch(value['request_id']):raise error('invalid_request_id','Usá un request_id hexadecimal aleatorio de 32 caracteres.')
        if publish and (value['publication_confirmed'] is not True or value['operator_authorized'] is not True):
            raise error('publication_confirmation_required','Confirmá la publicación pública y tu autorización para este contenido.')
        if publish and (not isinstance(value['publication_sha256'],str) or not contributions.ID.fullmatch(value['publication_sha256'])):
            raise error('invalid_publication_hash','Usá el SHA-256 de la previsualización.')
        return {k:value[k] for k in FIELDS if k in value}

    def build(value,mid):
        if not isinstance(value['files'],list) or not 1<=len(value['files'])<=32:raise error('invalid_selection','Seleccioná entre 1 y 32 versiones propias.')
        selections=[];files=[]
        for selection in value['files']:
            if not isinstance(selection,dict):raise error('invalid_selection','Selección inválida.')
            fields(selection,('file_id','version','path'),('file_id','version','path'))
            fid,version=selection['file_id'],selection['version']
            if not isinstance(fid,str) or not ID.fullmatch(fid) or type(version) is not int or not 1<=version<=20:raise error('invalid_selection','Indicá identificador y versión concreta del archivo.')
            row=db().execute('SELECT v.* FROM club_file_versions v JOIN club_files f ON f.id=v.file_id WHERE f.id=? AND f.member_id=? AND v.version=?',(fid,mid,version)).fetchone()
            if not row:raise error('not_found','Archivo o versión propia no encontrada.',404)
            files.append(dict(path=selection['path'],content=row['content']))
            selections.append(dict(selection,sha256=row['sha256']))
        previous=value.get('previous_id')
        if previous is not None:
            if not isinstance(previous,str) or not contributions.ID.fullmatch(previous):raise error('invalid_previous_contribution','El recibo previo debe ser un identificador completo.')
            own(mid,previous)
        author=value.get('author')
        if author is None or author=='':author='Anonymous contributor'
        submission=dict(format=contributions.FORMAT,author=author,files=files,
            **{k:value[k] for k in ('base_revision','summary','claim','reproduction','license')},
            publication_confirmed=True,operator_authorized=True)
        if previous and isinstance(submission['reproduction'],str):
            submission['reproduction']+='\n\nRevision of public receipt: https://geniusdecision.app/contributions/'+previous
        try:raw,ident=contributions.validate(submission)
        except (ValueError,UnicodeError,RecursionError):raise error('invalid_submission','La entrega no cumple el contrato público de /contributions.',400) from None
        return submission,raw,ident,selections

    def view(row,content=False):
        deposit=db().execute('SELECT * FROM contribution_inbox WHERE id=?',(row['contribution_id'],)).fetchone()
        value=dict(receipt=inbox()['receipt'](deposit),request_id=row['request_id'],
                   selections=json.loads(row['selections_json']),previous_id=row['previous_id'],
                   created_at=row['created_at'],review=reviews()['cached'](row['contribution_id']),
                   public_deposit_survives_account_deletion=True,content_is_untrusted=True)
        if content:value['submission']=json.loads(deposit['payload_json'])
        return value

    def export(mid):
        return [view(r) for r in db().execute('SELECT * FROM club_contributions WHERE member_id=? ORDER BY created_at,contribution_id',(mid,))]
    app.extensions['club_contributions_export']=export

    @bp.post('/api/club/contributions/prepare')
    def prepare():
        mid=member()['id'];value=request_value(body())
        quota('club-publication-preview:'+mid,50)
        with transaction(db()):submission,raw,ident,selections=build(value,mid)
        reviews()['public_revision'](submission['base_revision'])
        # Confirmation flags are prospective canonical fields, never authorization.
        preview={k:v for k,v in submission.items() if k not in ('publication_confirmed','operator_authorized')}
        return jsonify(status='PREPARED',published=False,public_content=preview,selections=selections,
            publication_sha256=ident,canonical_bytes=len(raw),public_revision_verified=True,
            requires_explicit_confirmation=['publication_confirmed','operator_authorized'],
            meaning='Nothing was published. Confirm only after reviewing the exact public content and license.')

    @bp.post('/api/club/contributions')
    def submit():
        writing();mid=member()['id'];value=body();spec=request_value(value,True)
        try:fingerprint=hashlib.sha256(contributions.canonical(spec)).hexdigest()
        except (ValueError,UnicodeError,RecursionError):raise error('invalid_submission','Se requiere contenido UTF-8 válido.') from None
        inbox()['reserve_attempt']()
        old=db().execute('SELECT * FROM club_contributions WHERE member_id=? AND request_id=?',(mid,spec['request_id'])).fetchone()
        if old:
            if old['request_sha256']!=fingerprint or old['contribution_id']!=value['publication_sha256']:
                raise error('club_idempotency_conflict','La solicitud ya se usó con otra entrega.',409)
            return jsonify(delivery=view(old),duplicate=True),200
        # Only a public SHA leaves the service. No private contents or credentials do.
        reviews()['public_revision'](spec['base_revision'])
        with transaction(db()):
            mid=member()['id'];submission,raw,ident,selections=build(spec,mid)
            if ident!=value['publication_sha256']:raise error('publication_changed','La entrega difiere de la previsualización; revisala nuevamente.',409)
            old=db().execute('SELECT * FROM club_contributions WHERE member_id=? AND (request_id=? OR contribution_id=?)',(mid,spec['request_id'],ident)).fetchone()
            if old:
                if old['contribution_id']!=ident or old['request_sha256']!=fingerprint:raise error('club_idempotency_conflict','Entrega ya vinculada: consultá tu listado y conservá su request_id.',409)
                return jsonify(delivery=view(old),duplicate=True),200
            if db().execute('SELECT COUNT(*) FROM club_contributions WHERE member_id=?',(mid,)).fetchone()[0]>=50:
                raise error('club_contribution_quota','Máximo 50 entregas vinculadas por membresía.',429)
            capacity(len(raw)*3+65536)
            _,duplicate=inbox()['deposit'](raw,ident)
            db().execute('INSERT INTO club_contributions VALUES(?,?,?,?,?,?,?)',(mid,spec['request_id'],ident,fingerprint,json.dumps(selections),spec.get('previous_id'),int(time.time())))
            result=view(own(mid,ident))
        return jsonify(delivery=result,duplicate=duplicate),200 if duplicate else 201

    @bp.get('/api/club/contributions')
    def list_deliveries():
        with transaction(db()):result=export(member()['id'])
        return jsonify(deliveries=result,review_refresh='/api/club/contributions/{id}/review')

    @bp.get('/api/club/contributions/<ident>')
    def read(ident):
        with transaction(db()):result=view(own(member()['id'],ident),True)
        return jsonify(delivery=result)

    @bp.get('/api/club/contributions/<ident>/review')
    def review(ident):
        own(member()['id'],ident)
        submission=json.loads(db().execute('SELECT payload_json FROM contribution_inbox WHERE id=?',(ident,)).fetchone()[0])
        result=reviews()['read'](ident,submission)
        # A concurrent account/membership deletion must not return private linkage.
        own(member()['id'],ident)
        return jsonify(receipt_status='RECEIVED',review=result)

    app.register_blueprint(bp)
