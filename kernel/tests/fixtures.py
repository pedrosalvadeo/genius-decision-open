"""Independent finite wire fixtures: no imports from genius_kernel.

Small graphs are built from explicitly requested traces; this is input generation,
not an alternative implementation or an oracle for the kernel's algorithms.
"""
from copy import deepcopy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'baseline/GENIUS_PHASE_1_HANDOFF/GENIUS_PROGRAM/conformance'


def water():
    return json.loads((BASE / 'WATER_HABITAT.input.json').read_text())


def raw(data):
    return json.dumps(data, ensure_ascii=False, separators=(',', ':')).encode('utf-8')


def query(policy, path=()):
    return {'policy': policy, 'path': list(path)}


def qkey(q):
    return q['policy'], tuple(q['path'])


def small(traces=None, *, horizon=None, recipe=None, mode='robust'):
    """traces maps policy IDs to equal-length native identity traces per scenario."""
    traces = traces or {'p': [['o', 'g']]}
    H = len(next(iter(traces.values()))[0]) - 1 if horizon is None else horizon
    count = len(next(iter(traces.values())))
    names = ['r', 's', 'v', 'w'][:count]
    if H == 0:
        names = ['r']
    d = {
        'format': 'genius-fp1/1.0',
        'meta': {'id': 'Test', 'framework': 'F', 'model': 'M', 'context': 'C', 'condition': 'K',
                 'horizon': str(H), 'specification': 'GENIUS-SPEC-1.0.0',
                 'theory_snapshot': 'GENIUS-THEORY-2026-09-23-S2', 'profile': 'FP1_FINITE_EXACT',
                 'claim_scope': 'FORMAL_INSTANCE_ONLY'},
        'assumptions': [{'id': 'A', 'kind': 'SYNTHETIC', 'statement': 'Formal test only.', 'provenance': 'CF fixtures'}],
        'initialization': {'history': 'h0', 'condition': 'K', 'x0': 'x0', 'i0': 'i0', 'basis': ['A']},
        'model': {'states': ['x0'], 'information': ['i0'], 'actions': [], 'observations': ['y'],
                  'exogenous': ['u_' + n for n in names] + (['tick'] if H > 1 else []),
                  'basis': ['A'], 'information_basis': ['A'], 'executable': [], 'admissible': [],
                  'transitions': [], 'updates': []},
        'policies': [], 'scenarios': [{'id': n, 'inputs': ['u_' + n] + ['tick'] * (H-1) if H else []} for n in names],
        'functional': {'indices': [], 'measurements': [], 'reduction': {'ids': [], 'rows': []}},
        'composition': {'ports': [], 'rows': [], 'views': [{'id': 'V', 'columns': ['query']}], 'basis': ['A']},
        'resources': {'kinds': [], 'demands': [], 'values': [], 'basis': ['A']},
        'generative': {'native_ids': [], 'common_ids': [], 'meaning_atoms': [], 'native_meaning': [],
                       'common_meaning': [], 'native_order': [], 'common_order': [], 'identity': [],
                       'translation': [], 'recipe': recipe or {'kind': 'att'}, 'mode': mode, 'basis': ['A']},
        'welfare': {'carriers': [], 'dimensions': [], 'existence': [], 'applicability': [], 'values': [], 'basis': ['A']},
        'semantics': {'states': [], 'references': [], 'task': [], 'protocol': 'FP1_EXACT_ENUM_V1', 'basis': ['A']},
        'law': {'rows': [], 'basis': ['A']}, 'constraints': [], 'selection': {'mode': 'none'}}
    points = {(0, 'x0'): next(iter(traces.values()))[0][0]}
    acts = ['act_' + p for p in traces] if H else []
    d['model']['actions'] = acts
    if H:
        for table in ['executable', 'admissible']:
            d['model'][table].append({'t': '0', 'x': 'x0', 'actions': acts[:]})
    for p, runs in traces.items():
        a = 'act_' + p
        d['policies'].append({'id': p, 'decisions': [{'t': str(t), 'i': 'i0', 'a': a} for t in range(H)]})
        queries = [query(p)]
        if H:
            outcomes = []
            for n, trace in zip(names, runs):
                x = f'x_{p}_{n}_1'
                outcomes.append({'branch': n, 'u': 'u_' + n, 'next_x': x, 'y': 'y'})
                for t in range(1, H+1):
                    path = [n] + ['step'] * (t-1)
                    x = f'x_{p}_{n}_{t}'
                    d['model']['states'].append(x)
                    queries.append(query(p, path))
                    points[t, x] = trace[t]
                    if t < H:
                        for table in ['executable', 'admissible']:
                            d['model'][table].append({'t': str(t), 'x': x, 'actions': [a]})
                        d['model']['transitions'].append({'t': str(t), 'x': x, 'a': a, 'outcomes': [
                            {'branch': 'step', 'u': 'tick', 'next_x': f'x_{p}_{n}_{t+1}', 'y': 'y'}]})
                        d['law']['rows'].append({'query': query(p, path), 'weights': [{'branch': 'step', 'mass': '1/1'}]})
            d['model']['transitions'].append({'t': '0', 'x': 'x0', 'a': a, 'outcomes': outcomes})
            d['model']['updates'].extend({'t': str(t), 'i': 'i0', 'a': a, 'y': 'y', 'next_i': 'i0'} for t in range(H))
            d['law']['rows'].append({'query': query(p), 'weights': [{'branch': n, 'mass': f'1/{count}'} for n in names]})
        d['composition']['rows'].extend({'query': q, 'values': []} for q in queries)
        for n in names:
            leaf = query(p, [n] + ['step']*(H-1) if H else [])
            s = f'sem_{p}_{n}'
            d['semantics']['states'].append(s)
            d['semantics']['references'].append({'leaf': leaf, 'states': [s]})
            d['semantics']['task'].append({'state': s, 'value': '1'})
    identities = sorted(set(points.values()))
    for n in identities:
        d['generative']['native_ids'].append(n)
        d['generative']['common_ids'].append(n)
        atom = 'meaning_' + n
        d['generative']['meaning_atoms'].append(atom)
        for side in ('native', 'common'):
            d['generative'][side + '_meaning'].append({'identity': n, 'atoms': [atom]})
            d['generative'][side + '_order'].append([n, n])
        d['generative']['translation'].append({'native': n, 'common': n})
    for (t, x), n in points.items():
        d['generative']['identity'].append({'t': str(t), 'x': x, 'native': n})
        red = 'red_' + str(t) + '_' + x
        d['functional']['reduction']['ids'].append(red)
        d['functional']['reduction']['rows'].append({'t': str(t), 'x': x, 'reduced': red})
    return d


def set_order(d, relation):
    for side in ['native_order', 'common_order']:
        d['generative'][side] = deepcopy(relation)


def add_function(d, profiles):
    """profiles is explicit (t,x)->rational-list; indices use identity calibration."""
    width = len(next(iter(profiles.values())))
    d['functional']['indices'] = []
    d['functional']['measurements'] = []
    for i in range(width):
        vals = sorted({row[i] for row in profiles.values()})
        d['functional']['indices'].append({'id': 'f'+str(i), 'calibration': [{'raw': v, 'value': v} for v in vals], 'basis': ['A']})
    for (t, x), vals in profiles.items():
        d['functional']['measurements'].extend({'t': str(t), 'x': x, 'index': 'f'+str(i), 'raw': v} for i,v in enumerate(vals))


def add_welfare(d, values, *, times=None):
    """values maps (policy,path_tuple) to Q or None (explicit missing measurement)."""
    H = int(d['meta']['horizon'])
    times = list(range(H+1)) if times is None else times
    w = d['welfare']
    w['carriers'] = ['l']
    w['dimensions'] = [{'id': 'j', 'basis': ['A']}]
    w['existence'] = [{'t': str(t), 'carrier': 'l'} for t in times]
    w['applicability'] = [{'t': str(t), 'carrier': 'l', 'dimension': 'j'} for t in times]
    w['values'] = [{'query': query(p,path), 'carrier': 'l', 'dimension': 'j', 'value': v}
                   for (p,path),v in values.items() if v is not None]


def add_resources(d, resources, values, bound='10/1'):
    """resources maps resource -> demand IDs; values maps (policy,path,demand)->Q."""
    d['resources']['kinds'] = [{'id': r, 'unit': 'L'} for r in resources]
    d['resources']['demands'] = [{'id': v, 'resource': r, 'unit': 'L', 'basis': ['A']} for r,vs in resources.items() for v in vs]
    d['resources']['values'] = [{'query': query(p,path), 'demand': v, 'value': q} for (p,path,v),q in values.items()]
    d['constraints'] = [{'id': 'Budget_'+r, 'kind': 'resource_budget', 'resource': r, 'bound': bound, 'basis': ['A']} for r in resources]
