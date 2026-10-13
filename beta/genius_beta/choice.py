"""CHOICE_DECLARED_V1: confirmed finite comparisons, compiled to received FP1.

Narrative is retained, never interpreted as a fact. Quantities and the selection
norm are supplied explicitly. Constant formal CAG/task coordinates are an
embedding of this comparison, NOT measurements of real capabilities or PVS.
No external acquisition, LLM, empirical domain admission or action execution.
"""
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re
import sys

VERSION = 'genius-declared-choice/1'
FIELDS = {'context', 'criteria', 'alternatives', 'selection'}
CATEGORIES = {'leisure', 'personal_organization'}
MAX_ALTERNATIVES = 8
MAX_CRITERIA = 5


class ChoiceError(ValueError):
    def __init__(self, code, message):
        self.code, self.message = code, message
        super().__init__(message)


def need(condition, code, message):
    if not condition:
        raise ChoiceError(code, message)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def text(value, maximum, label):
    need(type(value) is str and 1 <= len(value.strip()) <= maximum and
         not any(ord(c) < 32 or 0xD800 <= ord(c) <= 0xDFFF for c in value),
         'choice_text', 'Completá '+label+' sin datos personales ni saltos de línea.')
    return value.strip()


def quantity(value):
    if value is None:
        return None
    need(type(value) is str and len(value) <= 32 and
         re.fullmatch(r'(?:0|[1-9][0-9]*)(?:\.[0-9]+|/[1-9][0-9]*)?', value) is not None,
         'choice_quantity', 'Usá cantidades no negativas, como 30, 2.5 o 7/2; vacío significa desconocido.')
    q = Fraction(value)
    need(q <= 1000000 and q.denominator <= 1000000,
         'choice_quantity_bound', 'La cantidad o su precisión excede el límite de esta comparación.')
    return q


def qs(value):
    return str(value.numerator)+'/'+str(value.denominator)


def object_fields(value, fields):
    need(type(value) is dict and set(value) == set(fields), 'choice_fields', 'La estructura de la decisión no es compatible con este perfil.')


def validate(model):
    object_fields(model, FIELDS)
    context = model['context']
    object_fields(context, ('question', 'category', 'horizon'))
    text(context['question'], 600, 'qué querés decidir')
    text(context['horizon'], 100, 'el momento o período de la decisión')
    need(type(context['category']) is str and context['category'] in CATEGORIES,
         'choice_outside_scope', 'Esta primera ruta admite ocio y organización personal de bajo riesgo; elegí otro recorrido para decisiones de salud, legales, financieras, laborales o de seguridad.')
    cs, alternatives = model['criteria'], model['alternatives']
    need(type(cs) is list and 1 <= len(cs) <= MAX_CRITERIA, 'choice_criteria', 'Elegí entre 1 y 5 criterios.')
    need(type(alternatives) is list and 2 <= len(alternatives) <= MAX_ALTERNATIVES,
         'choice_alternatives', 'Compará entre 2 y 8 alternativas.')
    def ident(value):
        need(type(value) is str and re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,31}', value), 'choice_id', 'Identificador de criterio o alternativa inválido.')
    cids, aids = set(), set()
    for c in cs:
        object_fields(c, ('id', 'label', 'unit', 'direction', 'limit'))
        ident(c['id']); text(c['label'], 60, 'el criterio'); text(c['unit'], 30, 'la unidad')
        need(c['id'] not in cids and c['direction'] in ('min', 'max'), 'choice_criterion', 'Revisá criterios repetidos o su dirección.')
        cids.add(c['id']); quantity(c['limit'])
    for a in alternatives:
        object_fields(a, ('id', 'label', 'values', 'source'))
        ident(a['id']); text(a['label'], 80, 'el nombre de la alternativa'); text(a['source'], 200, 'la procedencia o estimación de los datos')
        need(a['id'] not in aids, 'choice_duplicate', 'Las alternativas deben tener identificadores diferentes.')
        aids.add(a['id']); object_fields(a['values'], cids)
        for value in a['values'].values(): quantity(value)
    selection = model['selection']
    object_fields(selection, ('mode', 'criteria_order'))
    need(selection['mode'] in ('unique', 'lexicographic') and type(selection['criteria_order']) is list,
         'choice_selection', 'Elegí una regla de selección admitida.')
    order = selection['criteria_order']
    need(all(type(k) is str for k in order) and len(order) == len(set(order)) and
         ((selection['mode'] == 'unique' and not order) or
          (selection['mode'] == 'lexicographic' and set(order) == cids)),
         'choice_preference', 'La prioridad debe ordenar todos los criterios una sola vez; sin prioridad dejá el orden vacío.')
    return model


def review(model):
    validate(model)
    questions = []
    for a in model['alternatives']:
        for c in model['criteria']:
            if a['values'][c['id']] is None:
                questions.append(dict(kind='missing_value', alternative=a['id'], criterion=c['id'],
                    question='¿Cuál es '+c['label']+' de '+a['label']+' ('+c['unit']+')?',
                    blocks='complete_recommendation', state='PV_UNKNOWN'))
    return dict(profile='choice', version=VERSION, model=model,
        confirmation=sha(canonical(model)), questions=questions,
        interpretation='guided_explicit_fields', narrative_interpreted=False,
        summary='Comparar '+', '.join(a['label'] for a in model['alternatives'])+' para: '+model['context']['question'],
        selection_notice=('Sólo elegir si queda una alternativa no superada; conservar empates e incomparabilidad.'
            if model['selection']['mode']=='unique' else
            'Entre alternativas no superadas, priorizar los criterios en el orden confirmado. El siguiente criterio se usa sólo en empate; no se calculan puntajes ponderados.'),
        limits=['La comparación depende de cantidades y restricciones declaradas, que no verificamos externamente.',
            'El texto inicial aporta contexto; confirmá que alternativas, criterios y límites representan lo que querés comparar.',
            'No se evalúan efectos no incluidos, capacidades reales, bienestar ni probabilidad de supervivencia.',
            'No se ejecuta ninguna acción ni se autoriza investigación.'])


def validate_payload(payload):
    object_fields(payload, FIELDS | {'profile','model_confirmation','permission_confirmed','scope_acknowledged','evidence_origin'})
    need(payload['profile']=='choice' and payload['permission_confirmed'] is True and payload['scope_acknowledged'] is True,
         'choice_acknowledgment', 'Confirmá permiso sobre los datos y alcance de bajo riesgo.')
    need(payload['evidence_origin'] in ('synthetic','user_declared'), 'choice_provenance', 'Procedencia no admitida.')
    model = {k:payload[k] for k in FIELDS}
    reviewed = review(model)
    need(type(payload['model_confirmation']) is str and payload['model_confirmation']==reviewed['confirmation'],
         'choice_confirmation', 'Revisá y confirmá nuevamente el modelo; cambió desde la última revisión.')
    return reviewed


def compile_model(model):
    """Order-preserving criterion embedding; no normalization across units.

    Minimized quantities are negated BEFORE identity calibration. Hard limits
    become nonnegative violations constrained to zero. Missing rows remain
    absent, never a made-up value. All other coordinates are explicit constants.
    """
    cs, alternatives = model['criteria'], model['alternatives']
    ids = [a['id'] for a in alternatives]
    basis = ['Declared', 'Embedding']
    points = [('0','root')]+[('1','x_'+i) for i in ids]
    queries = [{'policy':i,'path':p} for i in ids for p in ([],['r'])]
    d = dict(format='genius-fp1/1.0',
        meta=dict(id='DeclaredChoice',framework='F',model='TableComparison',context='C',condition='K',horizon='1',
            specification='GENIUS-SPEC-1.0.0',theory_snapshot='GENIUS-THEORY-2026-09-23-S2',profile='FP1_FINITE_EXACT',claim_scope='FORMAL_INSTANCE_ONLY'),
        assumptions=[dict(id='Declared',kind='MODEL',statement='Explicit user-declared quantities, units, bounds and one-step alternatives; truth and real-domain adequacy NOT established.',provenance='Confirmed input table'),
            dict(id='Embedding',kind='MODEL',statement='Finite table encoding only: identical formal identity at every point; empty welfare support; task means reaching the declared row with stipulated deterministic mass one. These constants assert NO real CAG, welfare, biological PVS or future probability.',provenance=VERSION),
            dict(id='Preference',kind='NORMATIVE',statement=json.dumps(model['selection'],sort_keys=True),provenance='Confirmed selection norm')],
        initialization=dict(history='h',condition='K',x0='root',i0='i',basis=basis),
        model=dict(states=[x for _,x in points],information=['i'],actions=['a_'+i for i in ids],observations=['y'],exogenous=['u'],basis=basis,information_basis=basis,
            executable=[dict(t='0',x='root',actions=['a_'+i for i in ids])],admissible=[dict(t='0',x='root',actions=['a_'+i for i in ids])],
            transitions=[dict(t='0',x='root',a='a_'+i,outcomes=[dict(branch='r',u='u',next_x='x_'+i,y='y')]) for i in ids],
            updates=[dict(t='0',i='i',a='a_'+i,y='y',next_i='i') for i in ids]),
        policies=[dict(id=i,decisions=[dict(t='0',i='i',a='a_'+i)]) for i in ids],scenarios=[dict(id='declared',inputs=['u'])],
        functional=dict(indices=[],measurements=[],reduction=dict(ids=['red_'+x for _,x in points],rows=[dict(t=t,x=x,reduced='red_'+x) for t,x in points])),
        composition=dict(ports=[],rows=[dict(query=q,values=[]) for q in queries],views=[dict(id='V',columns=['query'])],basis=basis),
        resources=dict(kinds=[],demands=[],values=[],basis=basis),
        generative=dict(native_ids=['g'],common_ids=['g'],meaning_atoms=['declared_row'],native_meaning=[dict(identity='g',atoms=['declared_row'])],common_meaning=[dict(identity='g',atoms=['declared_row'])],native_order=[['g','g']],common_order=[['g','g']],identity=[dict(t=t,x=x,native='g') for t,x in points],translation=[dict(native='g',common='g')],recipe=dict(kind='att'),mode='robust',basis=['Embedding']),
        welfare=dict(carriers=[],dimensions=[],existence=[],applicability=[],values=[],basis=['Embedding']),
        semantics=dict(states=['row'],references=[dict(leaf=dict(policy=i,path=['r']),states=['row']) for i in ids],task=[dict(state='row',value='1')],protocol='FP1_EXACT_ENUM_V1',basis=['Embedding']),
        law=dict(rows=[dict(query=dict(policy=i,path=[]),weights=[dict(branch='r',mass='1/1')]) for i in ids],basis=['Embedding']),
        constraints=[],selection=dict(mode='unique'))
    for c in cs:
        vals = {a['id']:quantity(a['values'][c['id']]) for a in alternatives}
        sign = -1 if c['direction']=='min' else 1
        oriented = {i:v*sign for i,v in vals.items() if v is not None}
        calibration = sorted(set(oriented.values()) | {Fraction(0)})
        d['functional']['indices'].append(dict(id=c['id'],calibration=[dict(raw=qs(v),value=qs(v)) for v in calibration],basis=['Declared']))
        d['functional']['measurements'] += [dict(t='0',x='root',index=c['id'],raw='0/1')]+[dict(t='1',x='x_'+i,index=c['id'],raw=qs(v)) for i,v in oriented.items()]
        bound = quantity(c['limit'])
        if bound is not None:
            rid = 'limit_'+c['id']
            d['resources']['kinds'].append(dict(id=rid,unit='violation'))
            d['resources']['demands'].append(dict(id=rid,resource=rid,unit='violation',basis=['Declared']))
            d['constraints'].append(dict(id=rid,kind='resource_budget',resource=rid,bound='0/1',basis=['Declared']))
            for i,v in vals.items():
                for path in ([],['r']):
                    if not path or v is not None:
                        violation = Fraction(0) if not path else max(Fraction(0),(bound-v)*sign)
                        d['resources']['values'].append(dict(query=dict(policy=i,path=path),demand=rid,value=qs(violation)))
    return d


def execute(payload, case_dir):
    reviewed = validate_payload(payload)
    model = reviewed['model']
    root = Path(__file__).resolve().parents[2]
    # Same immutable vendor package already verified by verify_runtime.py.
    sys.path.insert(0,str(root/'beta/vendor/R0/sources/repo/kernel'))
    from genius_kernel.engine import evaluate
    from genius_kernel.verifier import verify_result as verify
    case_dir = Path(case_dir)
    need(not case_dir.exists(), 'choice_dossier', 'El expediente de ejecución ya existe.')
    case_dir.mkdir(parents=True)
    compiled = compile_model(model)
    raw = canonical(compiled)
    result = evaluate(raw)
    decision = result.get('decision',{}).get('value',{})
    verified = verify(raw, result)
    # Only a complete exhaustive formal comparison can support a recommendation.
    complete = result['execution']['status']=='COMPLETE' and result['presentation']=='VALID' and decision.get('coverage')=='EXHAUSTIVE'
    need(verified.get('valid') is True, 'choice_verification', 'La comprobación del resultado formal no fue aceptada.')
    need(result['execution']['status']=='COMPLETE' and result['presentation']=='VALID' and
         (complete or bool(reviewed['questions'])), 'choice_verification',
         'La ejecución formal no permite emitir una recomendación; conservá la entrada para revisar el problema técnico.')
    frontier = decision.get('frontier',[])
    tied = []
    if complete and frontier and model['selection']['mode']=='lexicographic':
        directions = {c['id']:(-1 if c['direction']=='min' else 1) for c in model['criteria']}
        vectors = {a['id']:tuple(quantity(a['values'][k])*directions[k] for k in model['selection']['criteria_order']) for a in model['alternatives']}
        best = max(vectors[i] for i in frontier)
        tied = sorted(i for i in frontier if vectors[i]==best)
        if len(tied)==1:
            compiled['selection'] = dict(mode='priority',order=sorted(vectors,key=lambda i:vectors[i],reverse=True),basis=['Preference'])
            raw = canonical(compiled); result = evaluate(raw); decision = result.get('decision',{}).get('value',{})
            verified = verify(raw, result)
            need(verified.get('valid') is True and decision.get('coverage')=='EXHAUSTIVE', 'choice_verification', 'La selección formal no fue verificada.')
    selection = decision.get('selection',{})
    selected = selection.get('value') if complete and selection.get('state')=='DEFINED' and len(tied)<=1 else None
    if not complete: state = 'NEEDS_INFORMATION'
    elif not frontier: state = 'NO_FEASIBLE_ALTERNATIVE'
    elif selected: state = 'RECOMMENDED_CONDITIONAL'
    else: state = 'PREFERENCE_OR_TIE'
    by_id = {a['id']:a for a in model['alternatives']}
    explanation = {
        'NEEDS_INFORMATION':'Faltan datos o condiciones para una recomendación completa. Las alternativas con datos incompletos no se descartan por ello.',
        'NO_FEASIBLE_ALTERNATIVE':'Ninguna alternativa declarada cumple todos los límites. Revisá los límites o incorporá otras alternativas.',
        'PREFERENCE_OR_TIE':'Hay varias alternativas no superadas. Conservamos el conjunto: falta una preferencia que las distinga o siguen empatadas.',
        'RECOMMENDED_CONDITIONAL':'La alternativa recomendada cumple los límites y pertenece al conjunto no superado; la elección usa exclusivamente la regla que confirmaste.'}[state]
    tradeoffs = []
    if selected:
        for other in frontier:
            if other==selected: continue
            for c in model['criteria']:
                a,b = quantity(by_id[selected]['values'][c['id']]),quantity(by_id[other]['values'][c['id']])
                if (a>b if c['direction']=='min' else a<b):
                    tradeoffs.append(dict(alternative=other,criterion=c['id'],selected_value=qs(a),other_value=qs(b),unit=c['unit']))
    excluded = []
    for a in model['alternatives']:
        violations = []
        for c in model['criteria']:
            v,b = quantity(a['values'][c['id']]),quantity(c['limit'])
            if v is not None and b is not None and (v>b if c['direction']=='min' else v<b):
                violations.append(dict(criterion=c['id'],value=qs(v),bound=qs(b),direction=c['direction']))
        if violations: excluded.append(dict(alternative=a['id'],violations=violations))
    report = dict(format=VERSION, profile='choice', evidence_origin=payload['evidence_origin'],
        state=state, recommendation=selected, explanation=explanation, model=model,
        frontier=frontier, frontier_complete=complete, tied=tied, excluded=excluded,
        dominated=decision.get('dominators',[]), tradeoffs=tradeoffs, questions=reviewed['questions'],
        sensitivity=dict(kind='qualitative_reopen_conditions',evaluated_scenarios=0,
            conditions=['Cambian cantidades, fuentes o límites.', 'Se agrega o retira una alternativa o criterio.', 'Cambia tu orden de prioridades.'],
            robustness='NOT_ASSESSED'),
        next_action=('Revisá fuentes y condiciones antes de elegir; guardá una nueva versión si cambian.' if selected else explanation),
        limits=reviewed['limits'], narrative_interpreted=False, empirical_domain_admission='NOT_ESTABLISHED',
        real_cag='NOT_ASSESSED', real_welfare='NOT_ASSESSED', real_pvs='NOT_ASSESSED',
        research_admission='NOT_ESTABLISHED', authorization_to_act='NOT_GRANTED',
        verification=dict(kind='received_fp1_recomputation',valid=True),
        submitted_sha256=sha(canonical(payload)), model_sha256=reviewed['confirmation'],
        engine_input_sha256=sha(raw),engine_result_sha256=sha(canonical(result)))
    for filename,value in [('submitted.json',payload),('review.json',reviewed),('fp1-input.json',compiled),('fp1-result.json',result),('verification.json',verified),('report.json',report)]:
        (case_dir/filename).write_bytes(canonical(value))
    return report
