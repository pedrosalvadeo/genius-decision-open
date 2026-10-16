"""Evidence-linked system hypotheses; graph recognition is not causal discovery.

Each snapshot is a declared view over one observation window. Missing entities
or edges are unknown, not dead/absent. Identity belongs to the dossier, not to
one grouping. Boundaries never silently change the numerical stock-flow model.
"""
from copy import deepcopy
from datetime import datetime
import hashlib
from pathlib import Path

from .stockflow import _shape, validate_model
from .store import sha

FORMAT = 'genius-system-observation/1'
SCOPE_FORMAT = 'genius-system-scope/1'


def _obj(props):
    return dict(type='object', properties=props, required=list(props), additionalProperties=False)


def _arr(item, lo=0, hi=32):
    return dict(type='array', items=item, minItems=lo, maxItems=hi, uniqueItems=True)


ID = dict(type='string', pattern=r'^[A-Za-z][A-Za-z0-9_.-]*$', maxLength=64)
TEXT = dict(type='string', minLength=1, maxLength=2000)
TIME = dict(type='string', minLength=20, maxLength=40)


def schema():
    evidence = _obj(dict(id=ID, observed_at=TIME, source=TEXT,
        basis=dict(type='string', enum=['reported', 'measurement', 'inference', 'synthetic']),
        statement=TEXT, uncertainty=TEXT))
    entity = _obj(dict(id=ID, label=TEXT,
        kind=dict(type='string', enum=['person', 'living', 'organization', 'resource', 'physical']),
        evidence_ids=_arr(ID, 1)))
    relation = _obj(dict(id=ID, source=ID, target=ID,
        kind=dict(type='string', enum=['organizes', 'supplies', 'depends_on', 'affects']),
        evidence_ids=_arr(ID, 1)))
    result = _obj(dict(format=dict(type='string', enum=[FORMAT]), label=TEXT,
        window=_obj(dict(start=TIME, end=TIME)), entities=_arr(entity, 1),
        evidence=_arr(evidence, 1), relations=_arr(relation, 0, 64), unknowns=_arr(TEXT, 1, 16)))
    result.update({'$schema': 'https://json-schema.org/draft/2020-12/schema', 'title': FORMAT,
        'x-semantics': 'Source-attributed snapshot, not authenticated facts. Window is observation time, not prediction horizon. Missing edges are unknown. No automatic causal or probability estimation.'})
    return result


def scope_schema():
    result = _obj(dict(format=dict(type='string', enum=[SCOPE_FORMAT]),
        observation_revision=dict(type='integer', minimum=1, maximum=100000), label=TEXT,
        members=_arr(ID, 1), intervention_entities=_arr(ID), evaluation_entities=_arr(ID, 1),
        bindings=_arr(_obj(dict(collection=dict(type='string', enum=['stocks', 'carriers']),
            model_id=ID, entity_id=ID)), 1, 12), rationale=TEXT))
    result.update({'$schema': 'https://json-schema.org/draft/2020-12/schema', 'title': SCOPE_FORMAT})
    return result


def _date(value):
    try:
        stamp = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError as exc:
        raise ValueError('Fecha ISO8601 inválida') from exc
    if stamp.tzinfo is None:
        raise ValueError('La fecha requiere zona horaria')
    return stamp


def validate(snapshot):
    _shape(snapshot, schema(), 'observation')
    def nonblank(value):
        if isinstance(value, dict):
            for item in value.values():
                nonblank(item)
        elif isinstance(value, list):
            for item in value:
                nonblank(item)
        elif isinstance(value, str) and not value.strip():
            raise ValueError('No se admite texto vacío')
    nonblank(snapshot)
    tables = {}
    for key in ('entities', 'relations', 'evidence'):
        tables[key] = {row['id']: row for row in snapshot[key]}
        if len(tables[key]) != len(snapshot[key]):
            raise ValueError('ID duplicado en ' + key)
    start, end = (_date(snapshot['window'][key]) for key in ('start', 'end'))
    if end < start:
        raise ValueError('La ventana temporal está invertida')
    for item in snapshot['evidence']:
        if not start <= _date(item['observed_at']) <= end:
            raise ValueError('Evidencia fuera de la ventana de observación')
    for row in snapshot['entities'] + snapshot['relations']:
        if not set(row['evidence_ids']) <= tables['evidence'].keys():
            raise ValueError('Referencia a evidencia desconocida')
    for edge in snapshot['relations']:
        if edge['source'] == edge['target'] or not {edge['source'], edge['target']} <= tables['entities'].keys():
            raise ValueError('La relación necesita dos entidades existentes distintas')


def _closure(seeds, adjacency):
    seen, pending = set(seeds), list(seeds)
    while pending:
        for node in adjacency[pending.pop()]:
            if node not in seen:
                seen.add(node)
                pending.append(node)
    return seen


def boundary(snapshot, members):
    """Trace declared dependencies and potential effects, including uncertain edges.

    organizes is symmetric; supplies A->B and B depends_on A both propagate
    potential effects A->B. affects A->B has no asserted supply dependency.
    No sign, magnitude, probability or empirical causation is inferred.
    """
    ids = {e['id'] for e in snapshot['entities']}
    members = set(members)
    if not members or not members <= ids:
        raise ValueError('Miembros de sistema desconocidos o vacíos')
    impacts = {i: set() for i in ids}
    dependencies = {i: set() for i in ids}
    for edge in snapshot['relations']:
        a, b, kind = edge['source'], edge['target'], edge['kind']
        if kind == 'depends_on':
            a, b = b, a
        impacts[a].add(b)
        if kind != 'affects':
            dependencies[b].add(a)
        if kind == 'organizes':
            impacts[b].add(a)
            dependencies[a].add(b)
    affected = _closure(members, impacts)
    required = _closure(members, dependencies)
    crossing = [r['id'] for r in snapshot['relations'] if (r['source'] in members) != (r['target'] in members)]
    return dict(members=sorted(members), dependencies=sorted(required - members),
        potential_impacts=sorted(affected - members), crossing_relations=sorted(crossing),
        required_evaluation_entities=sorted(affected | required), coverage='DECLARED_GRAPH_ONLY')


def recognize(snapshot):
    validate(snapshot)
    ids = sorted(e['id'] for e in snapshot['entities'])
    candidates, seen = [], set()
    # Two explicit interpretations: organization and wider interaction network.
    # They are alternatives, not confidence-ranked discoveries of real systems.
    for rule in ('organization_components', 'interaction_components'):
        adj = {i: set() for i in ids}
        for edge in snapshot['relations']:
            if rule == 'organization_components' and edge['kind'] != 'organizes':
                continue
            adj[edge['source']].add(edge['target'])
            adj[edge['target']].add(edge['source'])
        remaining = set(ids)
        while remaining:
            members = _closure([min(remaining)], adj)
            remaining -= members
            key = tuple(sorted(members))
            if key in seen:
                continue
            seen.add(key)
            candidates.append(dict(id='system.' + sha(list(key))[:16], rule=rule,
                status='HYPOTHESIS_NOT_VERIFIED', **boundary(snapshot, members)))
    return dict(format='genius-system-recognition/1', observation_sha256=sha(snapshot),
        recognizer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        candidates=candidates, unknowns=deepcopy(snapshot['unknowns']),
        empirical_validation='NOT_ASSESSED', probabilities_inferred=False,
        meaning='Graph candidates from supplied entity/relationship assertions; no unstructured perception or causal discovery')


def review_scope(model, snapshot, scope):
    validate_model(model)
    validate(snapshot)
    _shape(scope, scope_schema(), 'scope')
    if not scope['label'].strip() or not scope['rationale'].strip():
        raise ValueError('Explica el nombre y fundamento de los límites')
    entities = {e['id']: e for e in snapshot['entities']}
    assessed = boundary(snapshot, scope['members'])
    evaluation = set(scope['evaluation_entities'])
    if not evaluation <= entities.keys() or not set(scope['intervention_entities']) <= set(scope['members']):
        raise ValueError('Los límites contienen entidades desconocidas o intervención fuera del sistema')
    missing = set(assessed['required_evaluation_entities']) - evaluation
    if missing:
        raise ValueError('La evaluación omite dependencias o impactos declarados: ' + ', '.join(sorted(missing)))
    expected = {(collection, row['id']) for collection in ('stocks', 'carriers') for row in model[collection]}
    actual = [(b['collection'], b['model_id']) for b in scope['bindings']]
    if set(actual) != expected or len(actual) != len(set(actual)):
        raise ValueError('Cada recurso y portador del modelo requiere exactamente una correspondencia')
    represented = set()
    for binding in scope['bindings']:
        eid = binding['entity_id']
        if eid not in evaluation:
            raise ValueError('Una correspondencia queda fuera de la evaluación')
        represented.add(eid)
        kind = entities[eid]['kind']
        if binding['collection'] == 'stocks' and kind != 'resource':
            raise ValueError('Un recurso del cálculo debe corresponder a una entidad de tipo recurso')
        if binding['collection'] == 'carriers':
            carrier = next(c for c in model['carriers'] if c['id'] == binding['model_id'])
            if carrier['kind'] != kind:
                raise ValueError('La correspondencia debe conservar el tipo de portador')
    carrier_ids = [b['entity_id'] for b in scope['bindings'] if b['collection'] == 'carriers']
    if len(carrier_ids) != len(set(carrier_ids)):
        raise ValueError('La misma entidad no puede duplicarse como dos portadores')
    stock_ids = [b['entity_id'] for b in scope['bindings'] if b['collection'] == 'stocks']
    if len(stock_ids) != len(set(stock_ids)):
        raise ValueError('El mismo recurso no puede duplicarse como dos saldos')
    gaps = sorted(evaluation - represented)
    welfare_carriers = {w['carrier'] for w in model['welfare']}
    unassessed = sorted(b['entity_id'] for b in scope['bindings']
                       if b['collection'] == 'carriers' and b['model_id'] not in welfare_carriers)
    return dict(format='genius-system-scope-receipt/1', scope=deepcopy(scope),
        scope_sha256=sha(scope), observation_sha256=sha(snapshot), model_sha256=sha(model),
        boundary=assessed, unmapped_entities=gaps, carriers_without_welfare=unassessed, review_required=bool(gaps or unassessed),
        mapping_status='INCOMPLETE' if gaps else 'DECLARED_MAPPING_COMPLETE',
        causal_validation='NOT_ASSESSED', evidence_authentication='NOT_ASSESSED',
        numeric_model_changed=False, physical_actions_authorized=False,
        interpretation='Context and identity bindings only; graph edges do not automatically become numerical dynamics or calibrated probabilities')


def example():
    from .interventions import example as distribution
    model = distribution()['model']
    evidence = dict(id='demo', observed_at='2026-01-01T00:00:00Z', source='Ejemplo sintético de sistemas',
        basis='synthetic', statement='Se estipulan depósitos, equipo y usuarios externos para probar límites.',
        uncertainty='Sin observaciones de campo; se desconocen otras relaciones e impactos.')
    entities = [dict(id=s['id'], label=s['label'], kind='resource', evidence_ids=['demo']) for s in model['stocks']]
    entities += [dict(id='team', label='Equipo operador', kind='organization', evidence_ids=['demo']),
                 dict(id='neighbors', label='Usuarios aguas abajo', kind='living', evidence_ids=['demo'])]
    relations = [dict(id='part.' + s['id'], source='team', target=s['id'], kind='organizes', evidence_ids=['demo']) for s in model['stocks']]
    relations.append(dict(id='downstream', source='source', target='neighbors', kind='affects', evidence_ids=['demo']))
    observation = dict(format=FORMAT, label='Depósitos y entorno — hipótesis sintética',
        window=dict(start=evidence['observed_at'], end=evidence['observed_at']),
        entities=entities, evidence=[evidence], relations=relations,
        unknowns=['No se ha observado el mundo real ni establecido la exhaustividad de esta frontera.'])
    scope = dict(format=SCOPE_FORMAT, observation_revision=1, label='Sistema de distribución',
        members=['source', 'target', 'team', 'time'], intervention_entities=['source', 'target'],
        evaluation_entities=[e['id'] for e in entities],
        bindings=[dict(collection=k, model_id=r['id'], entity_id=r['id']) for k in ('stocks', 'carriers') for r in model[k]],
        rationale='Conservar a los usuarios externos en el alcance de evaluación; falta representar sus consecuencias en el cálculo.')
    return dict(model=model, observation=observation, scope=scope, provenance='SYNTHETIC_EXAMPLE_NOT_FIELD_EVIDENCE')
