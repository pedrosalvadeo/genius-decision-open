"""Compose explicitly aligned partial worlds without guessing identities/values."""
from copy import deepcopy
import json
from .core import canonical, digest, fields, identifier, instant, text, MAX_PEERS
from genius_twin import construction, stockflow, systems

FORMAT = 'genius-partial-world/1'
MAX_VIEWS = 8
MAX_VIEW_BYTES = 24000


def uid(kind, value):
    return kind + digest(value)[:40]


def validate(view):
    construction._bounded(view)
    if len(canonical(view)) > MAX_VIEW_BYTES:
        raise ValueError('VIEW_BYTES_LIMIT')
    fields(view, 'format world_id view_id owner shareable valid_until frame observation identities denials construction bindings')
    if view['format'] != FORMAT or type(view['shareable']) is not bool:
        raise ValueError('INVALID_VIEW_HEADER')
    for key in ('world_id','view_id','owner'):
        identifier(view[key])
    fields(view['frame'], 'reference_time step_unit horizon layout')
    frame = view['frame']
    reference = instant(frame['reference_time'])
    text(frame['layout'])
    if frame['step_unit'] not in ('day','hour','step') or type(frame['horizon']) is not int or not 1 <= frame['horizon'] <= 30:
        raise ValueError('INVALID_FRAME')
    if instant(view['valid_until']) <= reference:
        raise ValueError('INVALID_VIEW_VALIDITY')
    systems.validate(view['observation'])
    if instant(view['observation']['window']['end']) > reference:
        raise ValueError('OBSERVATION_AFTER_REFERENCE')
    construction.validate(view['construction'])
    if any(instant(s['observed_at']) > reference for s in view['construction']['sources']):
        raise ValueError('SOURCE_AFTER_REFERENCE')
    if view['construction']['scope'] is not None:
        raise ValueError('SCOPE_COMPOSED_FROM_IDENTITIES')
    ids = {e['id'] for e in view['observation']['entities']}
    evidence = {e['id'] for e in view['observation']['evidence']}
    if type(view['identities']) is not list or len(view['identities']) != len(ids):
        raise ValueError('IDENTITIES_REQUIRED')
    seen = set()
    for row in view['identities']:
        fields(row, 'local_id global_id status rationale evidence_ids')
        if row['local_id'] not in ids or row['local_id'] in seen:
            raise ValueError('IDENTITY_REFERENCE')
        seen.add(row['local_id'])
        if row['global_id'] is not None:
            stockflow._shape(row['global_id'], systems.ID)
        if row['status'] not in ('confirmed','proposed','unknown') or (row['status']=='confirmed' and row['global_id'] is None):
            raise ValueError('IDENTITY_STATUS')
        text(row['rationale'], 2000)
        if type(row['evidence_ids']) is not list or not row['evidence_ids'] or not set(row['evidence_ids']) <= evidence:
            raise ValueError('IDENTITY_EVIDENCE')
    if type(view['bindings']) is not list or len(view['bindings']) > 12:
        raise ValueError('BINDING_LIMIT')
    for b in view['bindings']:
        fields(b, 'collection model_id entity_id')
        if b['collection'] not in ('stocks','carriers') or b['entity_id'] not in ids:
            raise ValueError('INVALID_BINDING')
        stockflow._shape(b['model_id'], systems.ID)
    if type(view['denials']) is not list or len(view['denials']) > 32:
        raise ValueError('DENIAL_LIMIT')
    for edge in view['denials']:
        fields(edge, 'source target kind evidence_ids')
        if (edge['kind'] not in ('supplies','depends_on','affects','organizes') or
            edge['source'] == edge['target'] or not {edge['source'],edge['target']} <= ids or
            type(edge['evidence_ids']) is not list or not edge['evidence_ids'] or
            not set(edge['evidence_ids']) <= evidence):
            raise ValueError('INVALID_DENIAL')


def ingest(node, views, via=None):
    if type(views) is not list or not 1 <= len(views) <= MAX_VIEWS:
        raise ValueError('VIEW_BATCH_LIMIT')
    if via is not None:
        identifier(via)
        if via == node.node_id:
            raise ValueError('SELF_PEER')
    received = node.clock()
    records = []
    for view in views:
        validate(view)
        if instant(view['frame']['reference_time']) > instant(received):
            raise ValueError('FUTURE_REFERENCE')
        if via and not view['shareable']:
            raise ValueError('PRIVATE_VIEW_IMPORT')
        if via is None and view['owner'] != node.node_id:
            raise ValueError('LOCAL_OWNER_MISMATCH')
        records.append((digest(view),canonical(view).decode()))
    with node.db() as db:
        db.execute('BEGIN IMMEDIATE')
        known = {r[0] for r in db.execute('SELECT hash FROM world_views')}
        incoming = {r[0] for r in records}
        if len(known | incoming) > MAX_VIEWS:
            raise ValueError('VIEW_MEMORY_BUDGET')
        if via:
            peers = {r[0] for r in db.execute('SELECT DISTINCT via FROM view_receipts')}
            if len(peers | {via}) > MAX_PEERS:
                raise ValueError('PEER_BUDGET')
        for hash_, body in records:
            db.execute('INSERT OR IGNORE INTO world_views VALUES (?,?,?,?)', (hash_,body,int(via is None),received))
            if via is None:
                db.execute('UPDATE world_views SET local=1 WHERE hash=?',(hash_,))
            else:
                db.execute('INSERT OR IGNORE INTO view_receipts VALUES (?,?)',(hash_,via))
    return dict(inserted=len(incoming-known), duplicates=len(records)-len(incoming-known))


def export(node):
    with node.db() as db:
        rows = [json.loads(r[0]) for r in db.execute('SELECT body FROM world_views ORDER BY hash')]
    return [v for v in rows if v['shareable']]


def project(node, world_id, focus, mode):
    identifier(world_id)
    if mode not in ('isolated','connected'):
        raise ValueError('INVALID_MODE')
    with node.db() as db:
        rows = db.execute('SELECT body,local,received_at FROM world_views ORDER BY hash').fetchall()
    current = node.clock()
    chosen = []
    for raw, local, received in rows:
        view = json.loads(raw)
        if view['world_id'] != world_id or (mode=='isolated' and not local):
            continue
        if instant(received) > instant(current):
            raise ValueError('CLOCK_REGRESSION')
        chosen.append(view)
    return compose(chosen, world_id, focus, current)


def compose(views, world_id, focus, as_of):
    """Deterministic finite union; external interpretation supplies alignments."""
    identifier(world_id)
    instant(as_of)
    if type(focus) is not list or not 1 <= len(focus) <= 32 or len(set(focus)) != len(focus):
        raise ValueError('INVALID_FOCUS')
    for eid in focus:
        stockflow._shape(eid, systems.ID)
    if type(views) is not list or len(views) > MAX_VIEWS:
        raise ValueError('VIEW_BATCH_LIMIT')
    for view in views:
        validate(view)
        if view['world_id'] != world_id:
            raise ValueError('WORLD_MISMATCH')
    unique = {digest(v):v for v in views}
    ordered = sorted(unique.items())
    questions, aliases, contributions = [], [], {}
    def issue(code, detail):
        questions.append(dict(code=code,detail=detail))
    receipt = dict(format='genius-distributed-world/1', world_id=world_id, as_of=as_of,
        view_hashes=sorted(unique), focus=sorted(focus), status='NEEDS_REVISION',
        questions=questions, aliases=aliases, fragment_contributors=contributions,
        observation=None, preparation=None, boundary=None, recognition=None,
        model=None, source_attestation='NONE', empirical_validation='NOT_ASSESSED',
        identity_authority='EXPLICIT_OPERATOR_ASSERTIONS', physical_actions=False)
    if not ordered:
        issue('NO_VIEWS','No hay vistas disponibles; no se interpreta como mundo vacío.')
        return receipt
    if len({digest(v['frame']) for _,v in ordered}) != 1:
        issue('FRAME_CONFLICT','Tiempo de referencia, unidad, horizonte o contrato de correspondencias distintos.')
        return receipt
    frame = ordered[0][1]['frame']
    if instant(frame['reference_time']) > instant(as_of):
        issue('FUTURE_REFERENCE','La vista se refiere a un estado futuro.')
    revisions = {}
    entities, evidence, edges, denied = {}, {}, {}, {}
    sources, claims, fragments, bindings, unknowns, unresolved = {}, {}, {}, {}, set(), []
    for vh, view in ordered:
        event=(view['owner'],view['view_id'])
        if event in revisions:
            issue('VIEW_VERSION_CONFLICT',list(event))
        revisions[event]=vh
        if instant(view['valid_until']) < instant(as_of):
            issue('STALE_VIEW',vh)
        snapshot=view['observation']
        evidence_ids={r['id']:uid('e',{k:v for k,v in r.items() if k!='id'}) for r in snapshot['evidence']}
        for row in snapshot['evidence']:
            eid=evidence_ids[row['id']]
            evidence[eid]={**deepcopy(row),'id':eid}
        mapping={}
        for identity in view['identities']:
            local=identity['local_id']
            gid=identity['global_id'] if identity['status']=='confirmed' else uid('u',[vh,local])
            if identity['status']!='confirmed':
                issue('IDENTITY_REVIEW',dict(view=vh,local_id=local,proposed=identity['global_id']))
            mapping[local]=gid
            aliases.append(dict(view=vh,**deepcopy(identity),resolved_id=gid))
        for row in snapshot['entities']:
            gid=mapping[row['id']]
            ev=sorted({evidence_ids[e] for e in row['evidence_ids']})
            if gid in entities:
                if entities[gid]['kind'] != row['kind']:
                    issue('ENTITY_KIND_CONFLICT',gid)
                entities[gid]['evidence_ids']=sorted(set(entities[gid]['evidence_ids'])|set(ev))
            else:
                entities[gid]=dict(id=gid,label=row['label'],kind=row['kind'],evidence_ids=ev)
        def relation(row):
            a,b,kind=mapping[row['source']],mapping[row['target']],row['kind']
            if kind=='depends_on':a,b,kind=b,a,'supplies'
            if kind=='organizes':a,b=sorted((a,b))
            if a==b:issue('IDENTITY_COLLAPSES_RELATION',a)
            key=uid('r',[a,b,kind])
            return key,dict(id=key,source=a,target=b,kind=kind,evidence_ids=sorted({evidence_ids[e] for e in row['evidence_ids']}))
        for rows,table in ((snapshot['relations'],edges),(view['denials'],denied)):
            for row in rows:
                key,edge=relation(row)
                if key in table:edge['evidence_ids']=sorted(set(edge['evidence_ids'])|set(table[key]['evidence_ids']))
                table[key]=edge
        unknowns.update(snapshot['unknowns'])
        document=view['construction']
        smap={r['id']:uid('s',{k:v for k,v in r.items() if k!='id'}) for r in document['sources']}
        cmap={r['id']:uid('c',[vh,r['id']]) for r in document['claims']}
        for row in document['sources']:
            sources[smap[row['id']]]={**deepcopy(row),'id':smap[row['id']]}
        for row in document['claims']:
            updated=deepcopy(row);updated['id']=cmap[row['id']]
            updated['premises']=[cmap[p] for p in row['premises']]
            for span in updated['spans']:span['source_id']=smap[span['source_id']]
            claims[updated['id']]=updated
        for fragment in document['fragments']:
            path=fragment['path'];value=fragment['value']
            contributions.setdefault(path,[]).append(vh)
            ids={cmap[c] for c in fragment['claim_ids']}
            if path in fragments:
                if canonical(fragments[path]['value']) != canonical(value):
                    issue('FRAGMENT_CONFLICT',dict(path=path,views=contributions[path]))
                fragments[path]['claim_ids']=sorted(set(fragments[path]['claim_ids'])|ids)
            else:fragments[path]=dict(path=path,value=deepcopy(value),claim_ids=sorted(ids))
        unresolved.extend(deepcopy(document['unresolved']))
        for b in view['bindings']:
            key=(b['collection'],b['model_id']);gid=mapping[b['entity_id']]
            if key in bindings and bindings[key]['entity_id']!=gid:issue('BINDING_CONFLICT',list(key))
            bindings[key]=dict(collection=key[0],model_id=key[1],entity_id=gid)
    for key in sorted(edges.keys() & denied.keys()):issue('RELATION_CONFLICT',dict(asserted=edges[key],denied=denied[key]))
    receipt['denials']=list(denied.values())
    receipt['coverage']=dict(unique_views=len(ordered),local_entity_mentions=len(aliases),
        unique_entities=len(entities),relations=len(edges),known_unknowns=sorted(unknowns),
        completeness='ONLY_SUPPLIED_VIEWS_NOT_THE_WHOLE_WORLD')
    snapshot=dict(format=systems.FORMAT,label='Vistas integradas: '+world_id,
        window=dict(start=min((v['observation']['window']['start'] for _,v in ordered),key=instant),
                    end=max((v['observation']['window']['end'] for _,v in ordered),key=instant)),
        entities=sorted(entities.values(),key=lambda x:x['id']),evidence=sorted(evidence.values(),key=lambda x:x['id']),
        relations=sorted(edges.values(),key=lambda x:x['id']),unknowns=sorted(unknowns))
    receipt['observation']=snapshot
    try:
        systems.validate(snapshot)
        receipt['recognition']=systems.recognize(snapshot)
        receipt['boundary']=systems.boundary(snapshot,focus)
    except ValueError as exc:issue('GRAPH_REVIEW',str(exc))
    scope=dict(format=systems.SCOPE_FORMAT,observation_revision=1,label='Alcance compuesto para revisión',
        members=sorted(focus),intervention_entities=[],evaluation_entities=sorted(entities),
        bindings=[bindings[k] for k in sorted(bindings)],
        rationale='Identidades y correspondencias declaradas; incluye todas las entidades observadas, sin conceder acciones externas.')
    document=dict(format=construction.FORMAT,sources=list(sources.values()),claims=list(claims.values()),
                  fragments=[fragments[k] for k in sorted(fragments)],scope=scope,unresolved=unresolved)
    for path,expected in (('/horizon',frame['horizon']),('/step_unit',frame['step_unit'])):
        if path in fragments and fragments[path]['value'] != expected:issue('FRAME_MODEL_CONFLICT',path)
    if questions:
        return receipt
    try:
        prepared=construction.prepare(document,dict(id=uid('o',snapshot),revision=1,observation=snapshot,historical_gaps={}))
        receipt['preparation']=prepared
        if prepared['model'] is not None:
            if prepared['model']['horizon']!=frame['horizon'] or prepared['model']['step_unit']!=frame['step_unit']:
                issue('FRAME_MODEL_CONFLICT','El modelo no conserva el marco común.')
            else:
                receipt['model']=prepared['model']
                receipt['status']='READY_FOR_REVIEW'
        else:issue('INCOMPLETE_MODEL',prepared['questions'])
    except ValueError as exc:issue('CONSTRUCTION_REVIEW',str(exc))
    return receipt
