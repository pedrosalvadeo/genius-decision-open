"""Auditor-only synthetic input built from FP1 01-06, without subject imports."""
from copy import deepcopy


def instance():
    q = lambda path: {'policy': 'audit_policy', 'path': path}
    basis = ['assumption']
    queries = [q([]), q(['good']), q(['bad'])]
    return {
        'format': 'genius-fp1/1.0',
        'meta': {'id': 'audit_instance', 'framework': 'framework', 'model': 'model',
                 'context': 'context', 'condition': 'condition', 'horizon': '1',
                 'specification': 'GENIUS-SPEC-1.0.0',
                 'theory_snapshot': 'GENIUS-THEORY-2026-09-23-S2',
                 'profile': 'FP1_FINITE_EXACT', 'claim_scope': 'FORMAL_INSTANCE_ONLY'},
        'assumptions': [{'id': 'assumption', 'kind': 'SYNTHETIC',
                         'statement': 'Premisa sintética: á, e\u0301, 𝄞, 零; cero ≠ ausente.',
                         'provenance': 'Auditor F4; no observación empírica.'}],
        'initialization': {'history': 'history', 'condition': 'condition',
                           'x0': 'same', 'i0': 'same', 'basis': basis},
        'model': {
            'states': ['same', 'end'], 'information': ['same'], 'actions': ['same'],
            'observations': ['same'], 'exogenous': ['u_good', 'u_bad'],
            'basis': basis, 'information_basis': basis,
            'executable': [{'t': '0', 'x': 'same', 'actions': ['same']}],
            'admissible': [{'t': '0', 'x': 'same', 'actions': ['same']}],
            'transitions': [{'t': '0', 'x': 'same', 'a': 'same', 'outcomes': [
                {'branch': 'good', 'u': 'u_good', 'next_x': 'end', 'y': 'same'},
                {'branch': 'bad', 'u': 'u_bad', 'next_x': 'end', 'y': 'same'}]}],
            'updates': [{'t': '0', 'i': 'same', 'a': 'same', 'y': 'same', 'next_i': 'same'}]},
        'policies': [{'id': 'audit_policy', 'decisions': [{'t': '0', 'i': 'same', 'a': 'same'}]}],
        'scenarios': [{'id': 'scenario_good', 'inputs': ['u_good']},
                      {'id': 'scenario_bad', 'inputs': ['u_bad']}],
        'functional': {
            'indices': [{'id': 'same', 'calibration': [{'raw': '9007199254740993/1',
                         'value': '9007199254740993/1'}], 'basis': basis}],
            'measurements': [{'t': t, 'x': x, 'index': 'same', 'raw': '9007199254740993/1'}
                             for t, x in [('0', 'same'), ('1', 'end')]],
            'reduction': {'ids': ['r0', 'r1'], 'rows': [
                {'t': '0', 'x': 'same', 'reduced': 'r0'},
                {'t': '1', 'x': 'end', 'reduced': 'r1'}]}},
        'composition': {
            'ports': [{'id': 'same', 'values': ['same'], 'basis': basis}],
            'rows': [{'query': query, 'values': [{'port': 'same', 'value': 'same'}]}
                     for query in queries],
            'views': [{'id': 'view', 'columns': ['query', 'same']}], 'basis': basis},
        'resources': {
            'kinds': [{'id': 'same', 'unit': 'same'}],
            'demands': [{'id': 'same', 'resource': 'same', 'unit': 'same', 'basis': basis}],
            'values': [{'query': query, 'demand': 'same', 'value': '1/3'} for query in queries],
            'basis': basis},
        'generative': {
            'native_ids': ['same'], 'common_ids': ['same'], 'meaning_atoms': ['atom'],
            'native_meaning': [{'identity': 'same', 'atoms': ['atom']}],
            'common_meaning': [{'identity': 'same', 'atoms': ['atom']}],
            'native_order': [['same', 'same']], 'common_order': [['same', 'same']],
            'identity': [{'t': t, 'x': x, 'native': 'same'} for t, x in [('0', 'same'), ('1', 'end')]],
            'translation': [{'native': 'same', 'common': 'same'}],
            'recipe': {'kind': 'att'}, 'mode': 'robust', 'basis': basis},
        'welfare': {
            'carriers': ['same'], 'dimensions': [{'id': 'same', 'basis': basis}],
            'existence': [{'t': t, 'carrier': 'same'} for t in ['0', '1']],
            'applicability': [{'t': t, 'carrier': 'same', 'dimension': 'same'} for t in ['0', '1']],
            'values': [{'query': query, 'carrier': 'same', 'dimension': 'same', 'value': value}
                       for query, value in zip(queries, ['0/1', '9007199254740993/9007199254740992',
                                                        '-9007199254740993/9007199254740992'])],
            'basis': basis},
        'semantics': {
            'states': ['yes', 'no', 'extra'],
            'references': [{'leaf': q(['good']), 'states': ['yes']},
                           {'leaf': q(['bad']), 'states': ['no']}],
            'task': [{'state': 'yes', 'value': '1'}, {'state': 'no', 'value': '0'},
                     {'state': 'extra', 'value': '1'}],
            'protocol': 'FP1_EXACT_ENUM_V1', 'basis': basis},
        'law': {'rows': [{'query': q([]), 'weights': [
            {'branch': 'good', 'mass': '1/1'}, {'branch': 'bad', 'mass': '0/1'}]}], 'basis': basis},
        'constraints': [{'id': 'budget', 'kind': 'resource_budget',
                         'resource': 'same', 'bound': '1/3', 'basis': basis}],
        'selection': {'mode': 'unique'}}


def certificate(input_digest, *, negative=False, superset=True):
    """Independent exact read for one leaf; never extracted from evaluate output."""
    query = {'policy': 'audit_policy', 'path': ['bad' if negative else 'good']}
    state = 'no' if negative else 'yes'
    value = '0' if negative else '1'
    members = [state] if negative or not superset else [state, 'extra']
    read = {'leaves': [deepcopy(query)],
            'references': [{'leaf': deepcopy(query), 'states': [state]}], 'states': [state]}
    return {'input_digest': input_digest, 'certificate': {
        'id': 'handmade_certificate', 'kind': 'DECISIVE_SET', 'query': query,
        'protocol': 'FP1_EXACT_ENUM_V1', 'read': read, 'A': members, 'value': value,
        'task_rows': [{'state': s, 'value': value} for s in members]}}


def semantic_projection(result):
    """Small independently specified projection; generated evidence IDs ignored."""
    p = result['policies'][0]
    key = lambda q: (q['policy'], tuple(q['path']))
    cell = lambda c: (c['state'], c.get('value'))
    d = result['decision']['value']
    return {
        'presentation': result['presentation'], 'execution': result['execution']['status'],
        'nodes': sorted((key(n['query']), n['t'], n['x'], n['i']) for n in p['causal']['nodes']),
        'leaves': sorted(key(q) for q in p['causal']['leaves']),
        'scenario_map': sorted((r['scenario'], key(r['leaf'])) for r in p['causal']['scenarios']['value']),
        'functional': sorted((r['scenario'], tuple((v['index'], v['value']) for v in r['profile']))
                             for r in p['functional']['terminal']['value']),
        'resources': sorted((key(r['query']), r['resource'], cell(r['total'])) for r in p['resources']),
        'origin': cell(p['generative']['origin']), 'cag': sorted(p['generative']['cag']['value']),
        'additional': sorted(p['generative']['additional']['value']),
        'welfare': sorted((key(r['query']), r['carrier'], r['dimension'], cell(r['value']))
                          for r in p['welfare']['cells']),
        'masses': sorted((key(r['query']), cell(r['mass'])) for r in p['probability']['masses']),
        'partition': {k: sorted(key(q) for q in v) for k, v in p['probability']['partition']['value'].items()},
        'vector': cell(p['probability']['vector']), 'pvs': cell(p['probability']['pvs']),
        'verdicts': sorted((key(r['query']), r['verdict']['state'],
                            r['verdict'].get('value', {}).get('value')) for r in p['evidence']),
        'hard': [(r['constraint'], cell(r['value'])) for r in p['hard']],
        'decision': {k: sorted(d[k]) for k in ['target', 'B', 'C', 'feasible', 'failed', 'unknown', 'frontier']},
        'coverage': d['coverage'], 'selection': cell(d['selection']),
        'integration': result['integration']['state'],
    }


def expected_projection():
    q = lambda *path: ('audit_policy', path)
    defined = lambda value: ('DEFINED', value)
    return {
        'presentation': 'VALID', 'execution': 'COMPLETE',
        'nodes': [(q(), '0', 'same', 'same'), (q('bad'), '1', 'end', 'same'),
                  (q('good'), '1', 'end', 'same')],
        'leaves': [q('bad'), q('good')],
        'scenario_map': [('scenario_bad', q('bad')), ('scenario_good', q('good'))],
        'functional': [(s, (('same', '9007199254740993/1'),)) for s in ['scenario_bad', 'scenario_good']],
        'resources': [(q(*path), 'same', defined('1/3')) for path in [(), ('bad',), ('good',)]],
        'origin': defined('same'), 'cag': ['same'], 'additional': [],
        'welfare': [(q(), 'same', 'same', defined('0/1')),
                    (q('bad'), 'same', 'same', defined('-9007199254740993/9007199254740992')),
                    (q('good'), 'same', 'same', defined('9007199254740993/9007199254740992'))],
        'masses': [(q(), defined('1/1')), (q('bad'), defined('0/1')), (q('good'), defined('1/1'))],
        'partition': {'positive': [q('good')], 'negative': [q('bad')], 'undecided': []},
        'vector': defined({'success': '1/1', 'failure': '0/1', 'undecided': '0/1'}),
        'pvs': defined('1/1'),
        'verdicts': [(q(), 'OUTSIDE_DOMAIN', None), (q('bad'), 'DEFINED', '0'), (q('good'), 'DEFINED', '1')],
        'hard': [('budget', defined('1'))],
        'decision': {k: ['audit_policy'] for k in ['target', 'B', 'C', 'feasible', 'frontier']}
                    | {'failed': [], 'unknown': []},
        'coverage': 'EXHAUSTIVE', 'selection': defined('audit_policy'), 'integration': 'DEFINED',
    }
