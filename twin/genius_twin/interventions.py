"""Generate explicit intervention alternatives in one common stock-flow world.

Directed relations are transfer permissions, encoded as effective capabilities.
This is bounded enumeration of declared choices, not empirical causal discovery.
The existing compiler/kernel evaluates every generated alternative afterwards.
"""
from copy import deepcopy
from fractions import Fraction
import hashlib
from itertools import product
import json
from math import prod
from pathlib import Path

from .stockflow import OCCURRENCE_LIMIT, PROFILE, _shape, canonical_json, model_schema, q, validate_model

FORMAT = 'genius-intervention-design/1'


def digest(value):
    return hashlib.sha256(canonical_json(value).encode()).hexdigest()


def schema():
    native = model_schema()['properties']
    ident = dict(type='string', pattern=r'^[A-Za-z][A-Za-z0-9_-]*$', maxLength=24)
    txt = dict(type='string', minLength=1, maxLength=1000)
    amount = native['stocks']['items']['properties']['initial']
    ref = native['stocks']['items']['properties']['id']
    costs = native['actions']['items']['properties']['withdrawals']
    def obj(props):
        return dict(type='object', properties=props, required=list(props), additionalProperties=False)
    def arr(item, minimum=0, maximum=5):
        return dict(type='array', items=item, minItems=minimum, maxItems=maximum, uniqueItems=True)
    at = arr(dict(type='integer', minimum=1, maximum=30), 1, 5)
    relation = obj(dict(id=ident, label=txt, source=ref, target=ref,
        initially_open=dict(type='boolean'), requires=arr(ref, 0, 8),
        open_costs=costs, close_costs=costs, transfer_costs=costs, provenance=txt))
    transfer = obj(dict(operation=dict(type='string', enum=['transfer']), at=at,
        relation=ident, amounts=arr(amount, 1, 5)))
    change = obj(dict(operation=dict(type='string', enum=['connect', 'disconnect']), at=at, relation=ident))
    use = obj(dict(operation=dict(type='string', enum=['use_action']), at=at, action=ref))
    result = obj(dict(format=dict(type='string', enum=[FORMAT]), name=txt,
        relations=arr(relation, 0, 4),
        interventions=arr(obj(dict(id=ident, label=txt,
            default_action={'oneOf': [ref, {'type': 'null'}]},
            operations=arr({'oneOf': [transfer, change, use]}, 1, 12))), 1, 5)))
    result.update({'$schema': 'https://json-schema.org/draft/2020-12/schema',
        'title': FORMAT, 'x-scope': 'Declared directed transfers and scheduled actions; no physical execution',
        'x-limits': 'Base and generated policies together <=6; actions<=12; capabilities<=8; P*S*(H+1)<=' + str(OCCURRENCE_LIMIT) + '. All combinations or reject.'})
    return result


def example():
    root = Path(__file__).resolve().parents[1] / 'examples'
    return dict(model=json.loads((root / 'stockflow_distribution.json').read_text()),
        design=json.loads((root / 'intervention_distribution.json').read_text()),
        provenance='SYNTHETIC_EXAMPLE_NOT_FIELD_EVIDENCE')


def generate(base, design):
    """Return a new common model and a reproducible generation receipt.

    Never edit initial stocks, scenario words/law, goals or base policies. New
    relation availability is a common declared premise for every alternative.
    Exhaustiveness refers only to the supplied finite Cartesian design space.
    """
    validate_model(base)
    if base['profile'] != PROFILE:
        raise ValueError('Interventions require STOCK_FLOW_FINITE_V1')
    _shape(design, schema(), 'design')
    if not design['name'].strip() or any(not r['label'].strip() or not r['provenance'].strip() for r in design['relations']):
        raise ValueError('Design name, relation labels and provenance cannot be blank')
    stocks = {s['id']: s for s in base['stocks']}
    caps = {c['id'] for c in base['capabilities']}
    actions = {a['id']: a for a in base['actions']}
    relations = {r['id']: r for r in design['relations']}
    if len(relations) != len(design['relations']):
        raise ValueError('Duplicate relation ID')
    if len({i['id'] for i in design['interventions']}) != len(design['interventions']):
        raise ValueError('Duplicate intervention ID')
    if len(caps) + len(relations) > 8:
        raise ValueError('Combined capability limit <=8 exceeded')
    for r in relations.values():
        if r['source'] not in stocks or r['target'] not in stocks or r['source'] == r['target']:
            raise ValueError('Relation requires two distinct existing stocks')
        if stocks[r['source']]['unit'] != stocks[r['target']]['unit']:
            raise ValueError('Relation endpoints must have the same unit; no implicit conversion')
        if not set(r['requires']) <= caps:
            raise ValueError('Unknown relation requirement')
        for field in ('open_costs', 'close_costs', 'transfer_costs'):
            if not set(r[field]) <= set(stocks):
                raise ValueError('Unknown resource in relation costs')

    # Bound the expansion before allocating combinations or generated traces.
    count = 0
    for intervention in design['interventions']:
        if intervention['default_action'] is not None and intervention['default_action'] not in actions:
            raise ValueError('Unknown default action')
        choices = []
        occupied = set()
        for operation in intervention['operations']:
            steps = set(operation['at'])
            if max(steps) > base['horizon']:
                raise ValueError('Operation exceeds the declared horizon')
            if occupied & steps:
                raise ValueError('Some combinations schedule two operations in one step; separate their step choices')
            occupied |= steps
            if operation['operation'] == 'use_action':
                if operation['action'] not in actions:
                    raise ValueError('Unknown existing action')
            elif operation['relation'] not in relations:
                raise ValueError('Unknown relation')
            if operation['operation'] == 'transfer' and any(Fraction(v) <= 0 for v in operation['amounts']):
                raise ValueError('Transfer amounts must be positive')
            choices.append(len(steps) * len(operation.get('amounts', [None])))
        count += prod(choices)
        total = len(base['policies']) + count
        if total > 6 or total * len(base['scenarios']) * (base['horizon'] + 1) > OCCURRENCE_LIMIT:
            raise ValueError('Design exceeds combined policy/occurrence limits; no alternatives were truncated')

    model = deepcopy(base)
    binding = {}
    for rid, r in relations.items():
        cid = 'relation.' + rid
        if cid in caps:
            raise ValueError('Relation capability collides with the existing model')
        binding[rid] = cid
        model['capabilities'].append(dict(id=cid, label='Intercambio habilitado: ' + r['label']))
        if r['initially_open']:
            model['initial_capabilities'].append(cid)

    generated_actions, policy_map, action_cache = [], {}, {}

    def add_action(body):
        key = canonical_json(body)
        if key in action_cache:
            return action_cache[key]
        aid = 'intervention.action.' + str(len(generated_actions) + 1)
        if aid in actions:
            raise ValueError('Generated action ID collides with the existing model')
        if len(model['actions']) >= 12:
            raise ValueError('Combined action limit <=12 exceeded; no alternatives were truncated')
        model['actions'].append(dict(id=aid, **body))
        generated_actions.append(aid)
        action_cache[key] = aid
        return aid

    def operation_action(operation, amount):
        kind = operation['operation']
        if kind == 'use_action':
            return operation['action']
        r = relations[operation['relation']]
        cid = binding[r['id']]
        costs = deepcopy(r[{'connect':'open_costs','disconnect':'close_costs','transfer':'transfer_costs'}[kind]])
        label = {'connect': 'Abrir', 'disconnect': 'Cerrar', 'transfer': 'Transferir'}[kind]
        body = dict(label=label + ': ' + r['label'], requires=list(r['requires']),
            withdrawals=costs, deposits={}, add_capabilities=[], remove_capabilities=[])
        if kind == 'connect':
            body['add_capabilities'] = [cid]
        elif kind == 'disconnect':
            body['requires'].append(cid)
            body['remove_capabilities'] = [cid]
        else:
            body['requires'].append(cid)
            costs[r['source']] = q(Fraction(costs.get(r['source'], '0/1')) + Fraction(amount))
            body['deposits'] = {r['target']: amount}
            body['label'] += ' · ' + amount + ' ' + stocks[r['source']]['unit']
        return add_action(body)

    for intervention in design['interventions']:
        default = intervention['default_action']
        if default is None:
            default = add_action(dict(label='Esperar sin intervención', requires=[], withdrawals={},
                deposits={}, add_capabilities=[], remove_capabilities=[]))
        options = [[(step, amount) for step in op['at'] for amount in op.get('amounts', [None])]
                   for op in intervention['operations']]
        for index, combination in enumerate(product(*options), 1):
            pid = 'intervention.' + intervention['id'] + '.' + str(index)
            if any(p['id'] == pid for p in model['policies']):
                raise ValueError('Generated policy ID collides with the existing model')
            scheduled = []
            rules = []
            for op, (step, amount) in zip(intervention['operations'], combination):
                aid = operation_action(op, amount)
                rules.append(dict(steps=[step], when=[], action=aid))
                chosen = {k: deepcopy(v) for k, v in op.items() if k not in ('at', 'amounts')}
                chosen.update(at=step, action_id=aid)
                if amount is not None:
                    chosen['amount'] = amount
                scheduled.append(chosen)
            model['policies'].append(dict(id=pid, label=intervention['label'] + ' · variante ' + str(index),
                default_action=default, rules=sorted(rules, key=lambda r: r['steps'][0])))
            policy_map[pid] = dict(intervention_id=intervention['id'], operations=sorted(scheduled, key=lambda x: x['at']),
                default_action=default)

    assumption_id = 'InterventionDesign.' + digest(design)[:16]
    if any(a['id'] == assumption_id for a in model['assumptions']):
        raise ValueError('This design is already represented')
    model['assumptions'].append(dict(id=assumption_id, kind='MODEL',
        statement='Declared directed resource transfers, availability, requirements, costs and schedules; no empirical causal validation or authorization of physical actions.',
        provenance='Design SHA-256 ' + digest(design) + '; relation provenance retained in the generation receipt.'))
    validate_model(model)
    receipt = dict(format=FORMAT, generator_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        base_model_sha256=digest(base), design_sha256=digest(design), model_sha256=digest(model),
        design=deepcopy(design), relation_capabilities=binding, generated_policies=policy_map,
        generated_actions=generated_actions, baseline_policies=[p['id'] for p in base['policies']],
        generated_count=count, coverage='EXHAUSTIVE_DECLARED_COMBINATIONS',
        empirical_validation='NOT_ASSESSED', physical_actions=False,
        preserved_fields=['stocks', 'carriers', 'scenarios', 'law', 'welfare', 'task', 'horizon', 'step_unit', 'require_all_scenarios', 'selection'],
        limits='Finite declared choices only; no global optimum, causal discovery or external execution claimed')
    return model, receipt
