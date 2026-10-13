"""Executed FP1 conformance through public byte-oriented API only.

Oracles are literal F1 catalogue expectations or independently derived elementary
sets/rational values, never copied kernel implementation helpers.
"""
import copy
import hashlib
import json
import sys
import unittest
from fractions import Fraction

from genius_kernel import evaluate, verify_result, verify_decisive_certificate
from fixtures import BASE, add_function, add_resources, add_welfare, qkey, query, raw, set_order, small, water


def keyed(rows, name='query'):
    return {qkey(r[name]): r for r in rows}


def val(cell):
    if cell['state'] != 'DEFINED':
        raise AssertionError('Expected DEFINED: ' + str(cell))
    return cell['value']


def policies(result):
    return {p['policy']: p for p in result['policies']}


def qset(qs):
    return {qkey(q) for q in qs}


class Conformance(unittest.TestCase):
    def run_data(self, d, limits=None):
        b = raw(d)
        r = evaluate(b, limits=limits)
        self.assertEqual(r['input_digest'], hashlib.sha256(b).hexdigest())
        self.assertNotEqual(r['execution']['status'], 'ERROR', r['diagnostics'])
        return r

    def complete(self, d):
        r = self.run_data(d)
        self.assertEqual(r['execution']['status'], 'COMPLETE', r['diagnostics'])
        self.assertEqual(r['presentation'], 'VALID', r['diagnostics'])
        return r

    def codes(self, r):
        return {x['code'] for x in r['diagnostics']}

    def test_CF001_full_frozen_projection(self):
        b = (BASE/'WATER_HABITAT.input.json').read_bytes()
        e = json.loads((BASE/'WATER_HABITAT.expected.json').read_text())
        r = evaluate(b)
        self.assertEqual(hashlib.sha256(b).hexdigest(), e['input']['sha256'])
        self.assertEqual(r['presentation'], 'VALID')
        self.assertEqual(r['execution']['status'], 'COMPLETE')
        self.assertEqual(r['input_digest'], e['input']['sha256'])
        ps = policies(r)
        self.assertEqual(len(ps), int(e['counts']['policies']))
        self.assertEqual(len(json.loads(b)['scenarios']), int(e['counts']['scenarios']))
        self.assertEqual(sum(len(p['causal']['nodes']) for p in ps.values()), int(e['counts']['queries']))
        self.assertEqual(sum(len(p['causal']['leaves']) for p in ps.values()), int(e['counts']['leaves']))
        self.assertEqual(len({(n['t'],n['x']) for p in ps.values() for n in p['causal']['nodes']}), int(e['counts']['reachable_points']))
        for ep in e['policies']:
            p = ps[ep['policy']]
            self.assertEqual(val(p['causal']['complete']), '1')
            ns = keyed(p['causal']['nodes'])
            self.assertEqual(set(ns), qset(ep['queries']))
            self.assertEqual(len(ns), int(ep['query_count']))
            self.assertEqual(len(p['causal']['leaves']), int(ep['leaf_count']))
            self.assertEqual({x['scenario']:qkey(x['leaf']) for x in val(p['causal']['scenarios'])}, {x['scenario']:qkey(x['leaf']) for x in ep['scenario_leaves']})
            es = keyed(p['evidence'])
            for x in ep['semantics']:
                self.assertEqual(set(val(es[qkey(x['query'])]['sem'])['states']), set(x['states']))
            for x in ep['V']:
                c = es[qkey(x['query'])]['verdict']
                if x['value'] == 'UNDEFINED':
                    self.assertEqual(c['state'], 'OUTSIDE_DOMAIN')
                else:
                    self.assertEqual(val(c)['value'], x['value'])
            masses = keyed(p['probability']['masses'])
            for x in ep['mass_by_query']:
                self.assertEqual(val(masses[qkey(x['query'])]['mass']), x['mass'])
            part = val(p['probability']['partition'])
            for a,bk in [('positive','success'),('negative','failure'),('undecided','undefined')]:
                self.assertEqual(qset(part[a]), qset(ep['leaf_partition'][bk]))
            self.assertEqual(val(p['probability']['vector']), {('undecided' if k=='undefined' else k):v for k,v in ep['VProb'].items()})
            self.assertEqual(val(p['probability']['pvs']), ep['PVS'])
            g = p['generative']
            self.assertEqual(set(val(g['cag'])), set(ep['CAG']))
            self.assertEqual(set(val(g['additional'])), set(ep['additional']))
            for tr in g['traces']:
                self.assertEqual(set(val(tr['achievements'])), set(ep['achievements']))
            self.assertEqual({(qkey(w['leaf']), w['identity'], w['t'], tuple(w['window'])) for w in g['witnesses']},
                             {(qkey(w['leaf']),w['identity'],w['start'],tuple(str(t) for t in range(int(w['start']),int(w['end'])+1))) for w in ep['hold_witnesses']})
            hard = {h['constraint']:h for h in p['hard']}
            totals = keyed(p['resources'])
            for h in ep['hard']:
                self.assertEqual(val(hard[h['constraint']]['value']), h['value'])
                self.assertEqual(qset(hard[h['constraint']]['missing']), qset(h['missing_queries']))
                for x in h['total_by_query']:
                    self.assertEqual(val(totals[qkey(x['query'])]['total']), x['value'])
                if 'refutation_witness' in h:
                    w=h['refutation_witness']
                    self.assertIn(qkey(w['query']),qset(hard[h['constraint']]['violations']))
                    self.assertEqual(val(totals[qkey(w['query'])]['total']),w['total'])
                    self.assertGreater(Fraction(w['total']),Fraction(w['bound']))
                if 'positive_coverage' in h:
                    self.assertEqual(qset(hard[h['constraint']]['checked']), qset(h['positive_coverage']))
            fpoints = {(f['point']['t'],f['point']['x']): {z['index']:z['value'] for z in val(f['profile'])} for f in p['functional']['points']}
            for x in ep['functional_by_query']:
                n = ns[qkey(x['query'])]
                self.assertEqual(fpoints[n['t'],n['x']], dict(zip(ep['functional_indices'],x['values'])))
            self.assertEqual({x['scenario']: {v['index']:v['value'] for v in x['profile']} for x in val(p['functional']['terminal'])},
                             {x['scenario']:dict(zip(ep['functional_indices'],x['values'])) for x in ep['terminal_functional_by_scenario']})
            wp = {(x['scenario'],x['t'],x['carrier'],x['dimension']):x['value'] for x in val(p['welfare']['profile'])}
            expected_wp = {(s['scenario'],t,c['carrier'],s['dimension']):v for s in ep['welfare_by_scenario'] for c in s['carriers'] for t,v in zip(s['times'],c['values'])}
            self.assertEqual(wp, expected_wp)
            self.assertEqual(p['functional']['reduction']['state'], 'DEFINED')
            self.assertEqual(p['composition']['state'], 'DEFINED')
        dec = val(r['decision']); ec = e['comparison']
        for k,ek in [('B','comparison_block'),('C','frontier_input'),('feasible','feasible'),('failed','refuted'),('unknown','unknown'),('frontier','frontier'),('target','objective_policies')]:
            self.assertEqual(set(dec[k]),set(ec[ek]))
        self.assertEqual(dec['coverage'], ec['coverage'])
        pair = {(x['left'],x['right']):x for x in dec['pairs']}
        self.assertEqual(len(pair),9)
        for i,a in enumerate(ec['policy_order']):
            for j,bp in enumerate(ec['policy_order']):
                for k,ek in [('functional','functional_weak'),('cag','CAG_weak'),('welfare','welfare_weak'),('pvs','PVS_weak'),('weak','integrated_weak'),('strict','integrated_strict')]:
                    self.assertEqual(pair[a,bp][k],ec[ek][i][j])
        self.assertEqual(dec['selection']['state'],'OUTSIDE_DOMAIN')
        self.assertEqual(r['integration']['state'],'DEFINED')
        self.assertEqual({c['rule'] for c in r['checks'] if c['id'] in val(r['integration'])['guards']}, {f'G{i:02}' for i in range(1,16)})
        self.assertTrue(verify_result(b,r)['valid'])

    def test_CF002_robust_quantifier_order(self):
        d=small({'p':[['o','u','z'],['o','u','u']], 'q':[['o','v','v'],['o','v','z']]})
        ps=policies(self.complete(d))
        self.assertEqual(set(val(ps['p']['generative']['additional'])),{'u'})
        self.assertEqual(set(val(ps['q']['generative']['additional'])),{'v'})
        d['generative']['mode']='possible'
        ps=policies(self.complete(d))
        self.assertEqual(set(val(ps['p']['generative']['additional'])),{'u','z'})
        self.assertEqual(set(val(ps['q']['generative']['additional'])),{'v','z'})

    def test_CF003_joint_witnesses_keep_policy_and_leaf(self):
        d=small({'p':[['o','u'],['o','v']], 'q':[['o','v'],['o','v']]},mode='possible')
        ps=policies(self.complete(d))
        witnesses=ps['p']['generative']['witnesses']
        self.assertEqual({(w['identity'],tuple(w['leaf']['path'])) for w in witnesses},{('u',('r',)),('v',('s',))})
        self.assertFalse(any({'u','v'} <= {w['identity'] for w in witnesses if w['leaf']==leaf} for leaf in ps['p']['causal']['leaves']))
        d=small({'p':[['o','u'],['o','u']], 'q':[['o','v'],['o','v']]})
        ps=policies(self.complete(d))
        repertoires=[set(val(p['generative']['additional'])) for p in ps.values()]
        self.assertEqual(set.union(*repertoires),{'u','v'})
        self.assertFalse(any({'u','v'}<=x for x in repertoires))

    def test_CF004_zero_missing_and_invalid_are_distinct(self):
        d=small({'p':[['o','g'],['o','g']]})
        d['semantics']['task']=[{'state':'sem_p_r','value':'0'}]
        r=self.complete(d); e=keyed(policies(r)['p']['evidence'])
        self.assertEqual(val(e['p',('r',)]['verdict'])['value'],'0')
        self.assertEqual(e['p',('s',)]['verdict']['state'],'OUTSIDE_DOMAIN')
        self.assertIn('TASK_OUTSIDE_DOMAIN',self.codes(r))
        del d['semantics']['task']
        r=self.run_data(d)
        self.assertEqual(r['presentation'],'INVALID'); self.assertEqual(r['policies'],[])

    def test_CF005_exact_partial_factor(self):
        d=small({'p':[['o','g','g']]})
        add_function(d,{(0,'x0'):['7/1'],(1,'x_p_r_1'):['7/1']})
        d['functional']['reduction']={'ids':['q','r'],'rows':[{'t':'0','x':'x0','reduced':'q'},{'t':'1','x':'x_p_r_1','reduced':'q'},{'t':'2','x':'x_p_r_2','reduced':'r'}]}
        p=policies(self.complete(d))['p']; f=val(p['functional']['reduction'])
        self.assertEqual({(x['t'],x['x']) for x in f['domain_f']},{('0','x0'),('1','x_p_r_1')})
        fibers={x['reduced']:x for x in f['fibers']}
        self.assertEqual(val(fibers['q']['value']),[{'index':'f0','value':'7/1'}])
        self.assertEqual(fibers['r']['value']['state'],'OUTSIDE_DOMAIN')

    def test_CF006_mixed_fiber_not_safe_factor(self):
        d=small(); add_function(d,{(0,'x0'):['0/1']})
        d['functional']['reduction']={'ids':['q'],'rows':[{'t':'0','x':'x0','reduced':'q'},{'t':'1','x':'x_p_r_1','reduced':'q'}]}
        r=self.complete(d); p=policies(r)['p']
        self.assertEqual(p['functional']['reduction']['state'],'OUTSIDE_DOMAIN')
        self.assertIn('REDUCTION_DOMAIN',self.codes(r))
        self.assertEqual(val(p['functional']['points'][0]['profile']),[{'index':'f0','value':'0/1'}])

    def test_CF009_fixed_functional_indices(self):
        d=small({'a':[['o','g']], 'b':[['o','g']], 'c':[['o','g']]})
        add_function(d,{(0,'x0'):['0/1']*3,(1,'x_a_r_1'):['2/1','0/1','1/1'],(1,'x_b_r_1'):['1/1','2/1','0/1'],(1,'x_c_r_1'):['0/1','1/1','2/1']})
        dec=val(self.complete(d)['decision'])
        self.assertEqual(set(dec['B']),{'a','b','c'})
        for p in dec['pairs']:
            self.assertEqual(p['functional'],'1' if p['left']==p['right'] else '0')
        self.assertEqual(set(dec['frontier']),{'a','b','c'})

    def test_CF011_spurious_natural_join(self):
        d=small()
        d['composition']['ports']=[{'id':p,'values':['zero','one'],'basis':['A']} for p in ['Aport','Bport']]
        d['composition']['rows']=[{'query':query('p',path),'values':[{'port':p,'value':v} for p in ['Aport','Bport']]} for path,v in [((),'zero'),(('r',),'one')]]
        d['composition']['views']=[{'id':'VA','columns':['Aport']},{'id':'VQB','columns':['query','Bport']}]
        r=self.complete(d)
        self.assertEqual(policies(r)['p']['composition']['state'],'OUTSIDE_DOMAIN')
        self.assertIn('COMPOSITION_SPURIOUS',self.codes(r))
        self.assertEqual(val(r['decision'])['coverage'],'RELATIVE')
        # Retaining B in the query-free view repairs exactly the lost correlation.
        d['composition']['views'][0]['columns'].append('Bport')
        repaired=self.complete(d)
        self.assertEqual(len(val(policies(repaired)['p']['composition'])['join']),2)
        self.assertEqual(repaired['integration']['state'],'DEFINED')

    def test_CF012_resource_identity_and_instantaneous_budget(self):
        for demands,expected in [(['d1','d2'],'0'),(['d1'],'1')]:
            with self.subTest(demands=demands):
                d=small({'p':[['o','g','g']]})
                add_resources(d,{'water':demands},{('p',tuple(q['query']['path']),dm):('0/1' if not q['query']['path'] else '6/1') for q in d['composition']['rows'] for dm in demands})
                d['composition']['views'].append({'id':'V2','columns':['query']})
                p=policies(self.complete(d))['p']
                self.assertEqual(val(p['hard'][0]['value']),expected)
                self.assertEqual([val(x['total']) for x in p['resources']].count('6/1' if len(demands)==1 else '12/1'),2)

    def test_CF013_translation_before_robust_intersection_noninjective(self):
        d=small({'p':[['o','a'],['o','b']]})
        g=d['generative']; g['common_ids']=['oc','c']; g['meaning_atoms']=['mo','mc']
        g['native_meaning']=[{'identity':n,'atoms':['mo' if n=='o' else 'mc']} for n in ['o','a','b']]
        g['common_meaning']=[{'identity':n,'atoms':['mo' if n=='oc' else 'mc']} for n in ['oc','c']]
        g['common_order']=[['oc','oc'],['c','c']]
        g['translation']=[{'native':n,'common':'oc' if n=='o' else 'c'} for n in ['o','a','b']]
        p=policies(self.complete(d))['p']
        self.assertEqual(set(val(p['generative']['cag'])),{'oc','c'})
        self.assertEqual(set(val(p['generative']['additional'])),{'c'})

    def test_CF014_cardinality_is_not_inclusion_and_origin_not_achievement(self):
        d=small({'p':[['o','a','b']], 'q':[['o','c','c']]})
        r=self.complete(d); ps=policies(r)
        self.assertEqual(set(val(ps['p']['generative']['cag'])),{'o','a','b'})
        self.assertEqual(set(val(ps['q']['generative']['cag'])),{'o','c'})
        for p in val(r['decision'])['pairs']:
            self.assertEqual(p['cag'],'1' if p['left']==p['right'] else '0')
        p=policies(self.complete(small({'p':[['o','a']]})))['p']
        self.assertEqual(set(val(p['generative']['cag'])),{'o','a'})
        self.assertEqual({w['identity'] for w in p['generative']['witnesses']},{'a'})

    def temporal(self,recipe):
        d=small({'p':[['o','a','ab','b','bc','bc']]},recipe=recipe)
        sets={'o':set(),'a':{'a'},'ab':{'a','b'},'b':{'b'},'bc':{'b','c'}}
        set_order(d,[[a,b] for a in sets for b in sets if sets[a]<=sets[b]])
        return d

    def test_CF015_all_temporal_recipe_witnesses(self):
        expected=[({'kind':'att'},{'a','ab','b','bc'},[(1,1),(2,2),(3,3),(4,4),(5,5)]),
                  ({'kind':'hold','length':'1'},{'a','b','bc'},[(1,2),(3,4),(4,5)]),
                  ({'kind':'hold','length':'0'},{'a','ab','b','bc'},[(1,1),(2,2),(3,3),(4,4),(5,5)]),
                  ({'kind':'acc'},{'a','ab'},[(0,1),(0,2)])]
        trace=['o','a','ab','b','bc','bc']
        for recipe,ach,windows in expected:
            with self.subTest(recipe=recipe):
                p=policies(self.complete(self.temporal(recipe)))['p']; g=p['generative']
                self.assertEqual(set(val(g['additional'])),ach)
                target={(trace[e if recipe['kind']=='acc' else s],str(e if recipe['kind']=='acc' else s),tuple(str(t) for t in range(s,e+1))) for s,e in windows}
                self.assertEqual({(w['identity'],w['t'],tuple(w['window'])) for w in g['witnesses']},target)
        p=policies(self.complete(small({'p':[['o','u','v']]})))['p']
        self.assertEqual(set(val(p['generative']['additional'])),{'u','v'})
        self.assertEqual({(w['identity'],w['t']) for w in p['generative']['witnesses']},{('u','1'),('v','2')})

    def test_missing_identity_after_acc_loss_still_invalidates_future(self):
        d=self.temporal({'kind':'acc'})
        d['generative']['identity']=[x for x in d['generative']['identity'] if x['t']!='5']
        r=self.complete(d); g=policies(r)['p']['generative']
        self.assertEqual(val(g['origin']),'o')
        self.assertEqual(g['cag']['state'],'OUTSIDE_DOMAIN')
        self.assertIn('GEN_IDENTITY_MISSING',self.codes(r))

    def test_CF016_history_not_terminal_welfare(self):
        d=small({'good':[['o','g','g']], 'dip':[['o','g','g']]})
        add_welfare(d,{qkey(row['query']):('0/1' if row['query']==query('dip',['r']) else '1/1') for row in d['composition']['rows']})
        d['semantics']['task'][1]['value']='0'
        r=self.complete(d); ps=policies(r)
        self.assertEqual(val(ps['good']['probability']['pvs']),'1/1')
        self.assertEqual(val(ps['dip']['probability']['pvs']),'0/1')
        pairs={(x['left'],x['right']):x for x in val(r['decision'])['pairs']}
        self.assertEqual(pairs['good','dip']['welfare'],'1')
        self.assertEqual(pairs['dip','good']['welfare'],'0')

    def test_CF017_zero_absent_support_and_missing_measurement(self):
        base=small()
        a=copy.deepcopy(base); add_welfare(a,{('p',()):'0/1',('p',('r',)):'0/1'})
        b=copy.deepcopy(base); add_welfare(b,{('p',()):'0/1'},times=[0])
        c=copy.deepcopy(base); add_welfare(c,{('p',()):'0/1',('p',('r',)):None})
        pa,pb,pc=[policies(self.complete(d))['p'] for d in (a,b,c)]
        self.assertEqual(len(val(pa['welfare']['profile'])),2)
        self.assertEqual(len(val(pb['welfare']['profile'])),1)
        self.assertEqual(pc['welfare']['profile']['state'],'OUTSIDE_DOMAIN')
        # FP1 has one GLOBAL support; per-policy support is not an admitted variant.
        bad=copy.deepcopy(a); bad['welfare']['existence'][0]['policy']='p'
        self.assertEqual(self.run_data(bad)['presentation'],'INVALID')

    def test_CF020_policy_information_function_duplicate_key(self):
        d=small({'p':[['o','g','g'],['o','g','g']]})
        self.complete(d)
        d['model']['actions'].append('other')
        d['policies'][0]['decisions'].append({'t':'1','i':'i0','a':'other'})
        r=self.run_data(d)
        self.assertEqual(r['presentation'],'INVALID'); self.assertIn('DUPLICATE_KEY',self.codes(r))

    def test_CF021_empty_scenarios_and_missing_scenario_fiber(self):
        d=small(); d['scenarios']=[]
        self.assertEqual(self.run_data(d)['presentation'],'INVALID')
        d=small(); d['model']['exogenous'].append('u_s'); d['scenarios'].append({'id':'s','inputs':['u_s']})
        r=self.complete(d)
        self.assertIn('SCENARIO_COVERAGE',self.codes(r))
        self.assertEqual(policies(r)['p']['causal']['scenarios']['state'],'OUTSIDE_DOMAIN')
        self.assertNotEqual(r['integration']['state'],'DEFINED')

    def test_CF022_multiple_fiber_and_no_early_terminal_padding(self):
        d=small({'p':[['o','g','g'],['o','g','g'],['o','g','g']]})
        root=next(x for x in d['model']['transitions'] if x['t']=='0')
        root['outcomes'][2]['u']='u_r'; d['scenarios']=d['scenarios'][:2]
        r=self.complete(d)
        self.assertIn('SCENARIO_MULTIPLE',self.codes(r))
        self.assertEqual(len(policies(r)['p']['causal']['leaves']),3)
        d=small({'p':[['o','g','g'],['o','g','g']]})
        next(x for x in d['model']['transitions'] if x['x']=='x_p_s_1')['outcomes']=[]
        # Do not claim references into the disproven continuation.
        for block,field,qfield in [('composition','rows','query'),('semantics','references','leaf'),('law','rows','query')]:
            d[block][field]=[x for x in d[block][field] if not(x[qfield]['path']==['s','step'])]
        r=self.run_data(d)
        self.assertIn('TRANSITION_EMPTY',self.codes(r))
        p=policies(r)['p']; self.assertEqual(qset(p['causal']['leaves']),{('p',('r','step'))})
        self.assertNotEqual(p['causal']['complete']['state'],'DEFINED')
        self.assertNotEqual(r['integration']['state'],'DEFINED')

    def test_CF024_decisive_certificate_rejection_and_superset_acceptance(self):
        d=small({'p':[['o','g'],['o','g']]})
        d['semantics']['task'][1]['value']='0'
        d['semantics']['states'].append('extra')
        d['semantics']['task'].append({'state':'extra','value':'1'})
        b=raw(d); r=self.complete(d); e=keyed(policies(r)['p']['evidence'])
        cert=val(e['p',('r',)]['verdict'])
        def check(c, digest=None):
            return verify_decisive_certificate(b,{'input_digest':digest or hashlib.sha256(b).hexdigest(),'certificate':c})
        self.assertTrue(check(cert)['valid'])
        c=copy.deepcopy(cert); c['A'].append('extra'); c['task_rows'].append({'state':'extra','value':'1'})
        self.assertTrue(check(c)['valid'], 'Valid noncanonical A superset must be accepted')
        rootread=val(e['p',()]['sem'])
        for A in [['sem_p_r'],['sem_p_r','sem_p_s'],[]]:
            c=copy.deepcopy(cert); c['query']=query('p'); c['read']=rootread; c['A']=A
            c['task_rows']=[x for x in d['semantics']['task'] if x['state'] in A]
            self.assertFalse(check(c)['valid'])
        for field, bad in [('value','0'),('protocol','WRONG'),('query',query('p',['ghost'])),('A',[])]:
            c=copy.deepcopy(cert); c[field]=bad
            self.assertFalse(check(c)['valid'])
        self.assertFalse(check(cert,'0'*64)['valid'])
        self.assertFalse(verify_decisive_certificate(b,cert)['valid'])
        # Negative canonical certificates may also have a nonsingleton read.
        d['semantics']['task']=[{'state':x,'value':'0'} for x in d['semantics']['states']]
        b=raw(d); r=self.complete(d); c=val(keyed(policies(r)['p']['evidence'])['p',()]['verdict'])
        self.assertEqual(c['value'],'0'); self.assertEqual(set(c['A']),{'sem_p_r','sem_p_s'})
        self.assertTrue(check(c)['valid'])

    def test_CF025_root_indeterminate_with_defined_PVS(self):
        r=self.complete(water()); p=policies(r)['pi_a']
        self.assertEqual(keyed(p['evidence'])['pi_a',()]['verdict']['state'],'OUTSIDE_DOMAIN')
        self.assertEqual(val(p['probability']['vector']),{'success':'3/4','failure':'1/4','undecided':'0/1'})
        self.assertEqual(val(p['probability']['pvs']),'3/4')
        self.assertEqual(next(c for c in r['checks'] if c['rule']=='G11')['outcome'],'PASS')

    def test_CF026_positive_undecided_mass_not_renormalized(self):
        d=small({'p':[['o','g'],['o','g']]})
        d['law']['rows'][0]['weights']=[{'branch':'r','mass':'3/4'},{'branch':'s','mass':'1/4'}]
        d['semantics']['states'].append('w'); d['semantics']['task'].append({'state':'w','value':'0'})
        d['semantics']['references'][1]['states'].append('w')
        r=self.complete(d); p=policies(r)['p']
        self.assertEqual(val(p['probability']['vector']),{'success':'3/4','failure':'0/1','undecided':'1/4'})
        self.assertEqual(p['probability']['pvs']['state'],'OUTSIDE_DOMAIN')
        self.assertIn('POSITIVE_UNDECIDED_MASS',self.codes(r))

    def test_CF027_zero_mass_keeps_failure_mixed_or_absent_leaf(self):
        for variant in ('negative','mixed','missing'):
            with self.subTest(variant=variant):
                d=small({'p':[['o','g'],['o','g']]})
                d['law']['rows'][0]['weights']=[{'branch':'r','mass':'1/1'},{'branch':'s','mass':'0/1'}]
                d['semantics']['task'][1]['value']='0'
                if variant=='mixed':
                    d['semantics']['references'][1]['states'].append('sem_p_r')
                if variant=='missing':
                    d['semantics']['references'].pop()
                d['constraints']=[{'id':'All','kind':'task_all','scope':'LEAVES','basis':['A']}]
                p=policies(self.complete(d))['p']
                self.assertEqual(len(p['causal']['leaves']),2)
                self.assertEqual(val(p['probability']['vector']),{'success':'1/1','failure':'0/1','undecided':'0/1'})
                self.assertEqual(val(p['probability']['pvs']),'1/1')
                self.assertEqual(p['hard'][0]['value']['state'],'DEFINED' if variant=='negative' else 'OUTSIDE_DOMAIN')
                if variant=='negative': self.assertEqual(val(p['hard'][0]['value']),'0')
                if variant=='missing': self.assertEqual(keyed(p['evidence'])['p',()]['sem']['state'],'OUTSIDE_DOMAIN')

    def test_CF028_invalid_present_law_at_zero_mass(self):
        d=small({'p':[['o','g','g'],['o','g','g']]})
        root=next(x for x in d['law']['rows'] if not x['query']['path'])
        root['weights']=[{'branch':'r','mass':'1/1'},{'branch':'s','mass':'0/1'}]
        # Exact catalogue tree: one positive leaf, two children under null n0.
        d['model']['exogenous'].append('other_u')
        zero_transition=next(x for x in d['model']['transitions'] if x['x']=='x_p_s_1')
        zero_transition['outcomes'].append({'branch':'other','u':'other_u','next_x':'x_p_s_2','y':'y'})
        extra=query('p',['s','other'])
        d['scenarios'].append({'id':'v','inputs':['u_s','other_u']})
        d['composition']['rows'].append({'query':extra,'values':[]})
        d['semantics']['references'].append({'leaf':extra,'states':['sem_p_s']})
        zero=next(x for x in d['law']['rows'] if x['query']['path']==['s'])
        zero['weights']=[{'branch':'step','mass':'1/1'},{'branch':'other','mass':'1/1'}]
        r=self.complete(d); p=policies(r)['p']
        self.assertIn('LAW_INVALID',self.codes(r))
        self.assertEqual(p['probability']['vector']['state'],'BLOCKED')
        self.assertEqual(p['probability']['pvs']['state'],'BLOCKED')
        self.assertEqual(len(p['causal']['leaves']),3)
        for w in zero['weights']: w['mass']='1/2'
        p=policies(self.complete(d))['p']; self.assertEqual(val(p['probability']['pvs']),'1/1')
        masses=keyed(p['probability']['masses'])
        self.assertEqual(val(masses['p',('s','step')]['mass']),'0/1')
        self.assertEqual(val(masses['p',('s','other')]['mass']),'0/1')
        d['law']['rows'].remove(zero)
        p=policies(self.complete(d))['p']; self.assertEqual(val(keyed(p['probability']['masses'])['p',('s','step')]['mass']),'0/1')
        self.assertEqual(val(keyed(p['probability']['masses'])['p',('s','other')]['mass']),'0/1')

    def test_CF029_partial_law_and_leaf_partition_only(self):
        # Exact catalogue topology h -> n -> {e1,e2}; the two leaves may
        # share a physical state while retaining distinct semantic occurrences.
        d=small({'p':[['o','g','g']]})
        d['model']['exogenous'].append('other_u')
        split=next(x for x in d['model']['transitions'] if x['t']=='1')
        split['outcomes'].append({'branch':'other','u':'other_u','next_x':'x_p_r_2','y':'y'})
        extra=query('p',['r','other'])
        d['scenarios'].append({'id':'s','inputs':['u_r','other_u']})
        d['composition']['rows'].append({'query':extra,'values':[]})
        d['semantics']['states'].append('sem_p_s')
        d['semantics']['task'].append({'state':'sem_p_s','value':'0'})
        d['semantics']['references'].append({'leaf':extra,'states':['sem_p_s']})
        split_law=next(x for x in d['law']['rows'] if x['query']['path'])
        split_law['weights']=[{'branch':'step','mass':'1/3'},{'branch':'other','mass':'2/3'}]
        laws=copy.deepcopy(d['law']['rows']); d['law']['rows']=[]
        r=self.complete(d); p=policies(r)['p']
        self.assertEqual(p['probability']['pvs']['state'],'OUTSIDE_DOMAIN')
        self.assertIn('LAW_UNDETERMINED',self.codes(r))
        self.assertEqual(val(keyed(p['probability']['masses'])['p',()]['mass']),'1/1')
        d['law']['rows']=laws
        p=policies(self.complete(d))['p']
        self.assertEqual(val(p['probability']['pvs']),'1/3')
        masses=keyed(p['probability']['masses'])
        self.assertEqual(val(masses['p',('r',)]['mass']),'1/1')
        self.assertEqual(sum(Fraction(val(masses[qkey(q)]['mass'])) for q in p['causal']['leaves']),1)
        self.assertEqual(sum(Fraction(val(x['mass'])) for x in masses.values()),3)

    def test_CF031_hard_refutation_preserves_missing_and_comparison_domain(self):
        d=small({'a':[['o']], 'b':[['o']], 'c':[['o']]})
        add_resources(d,{'R1':['d1'],'R2':['d2']},{('a',(),'d1'):'0/1',('b',(),'d1'):'2/1',('c',(),'d1'):'0/1',('a',(),'d2'):'0/1'},bound='1/1')
        r=self.complete(d); dec=val(r['decision'])
        self.assertEqual(set(dec['feasible']),{'a'}); self.assertEqual(set(dec['failed']),{'b'}); self.assertEqual(set(dec['unknown']),{'c'})
        h={x['constraint']:x for x in policies(r)['b']['hard']}
        self.assertEqual(val(h['Budget_R1']['value']),'0')
        self.assertEqual(h['Budget_R2']['value']['state'],'OUTSIDE_DOMAIN')
        self.assertEqual(qset(h['Budget_R2']['missing']),{('b',())})
        d=water(); d['welfare']['values']=[x for x in d['welfare']['values'] if not(x['query']==query('pi_ah',['regular']) and x['carrier']=='l1')]
        r=self.complete(d); dec=val(r['decision'])
        self.assertEqual(val(policies(r)['pi_ah']['probability']['pvs']),'1/1')
        self.assertNotIn('pi_ah',dec['B'])
        self.assertFalse(any(p['left']=='pi_ah' or p['right']=='pi_ah' for p in dec['pairs']))

    def pvs_instance(self, values):
        d=small({p:[['o','g'],['o','g']] for p in values})
        for x in d['semantics']['task']:
            x['value']='1' if x['state'].endswith('_r') else '0'
        for x in d['law']['rows']:
            q=values[x['query']['policy']]
            x['weights']=[{'branch':'r','mass':str(q.numerator)+'/'+str(q.denominator)},
                          {'branch':'s','mass':str((1-q).numerator)+'/'+str((1-q).denominator)}]
        return d

    def test_CF033_relative_frontier_none_unique_priority(self):
        d=self.pvs_instance({'a':Fraction(1,4),'b':Fraction(1,2),'c':Fraction(3,4)})
        full=self.complete(d); self.assertEqual(val(full['decision'])['frontier'],['c'])
        # Removing a required c semantic reference creates a genuine partial block.
        d['semantics']['references']=[x for x in d['semantics']['references'] if x['leaf']!=query('c',['s'])]
        for selection in [{'mode':'none'},{'mode':'unique'},{'mode':'priority','order':['c','b','a'],'basis':['A']}]:
            d['selection']=selection; r=self.complete(d); dec=val(r['decision'])
            self.assertEqual(set(dec['target']),{'a','b','c'}); self.assertEqual(set(dec['C']),{'a','b'})
            self.assertEqual(dec['frontier'],['b']); self.assertEqual(dec['coverage'],'RELATIVE')
            self.assertEqual(dec['selection']['state'],'OUTSIDE_DOMAIN')
        d=self.pvs_instance({'a':Fraction(1,4),'b':Fraction(1,2)})
        r=self.complete(d); dec=val(r['decision'])
        self.assertEqual(dec['coverage'],'EXHAUSTIVE'); self.assertEqual(dec['frontier'],['b'])
        self.assertEqual(dec['selection']['state'],'OUTSIDE_DOMAIN')
        d['selection']={'mode':'unique'}; self.assertEqual(val(val(self.complete(d)['decision'])['selection']),'b')
        d=self.pvs_instance({'a':Fraction(1,2),'b':Fraction(1,2)})
        d['selection']={'mode':'unique'}; r=self.complete(d)
        self.assertEqual(set(val(r['decision'])['frontier']),{'a','b'})
        self.assertEqual(val(r['decision'])['selection']['state'],'OUTSIDE_DOMAIN')
        d['selection']={'mode':'priority','order':['b','a'],'basis':['A']}
        self.assertEqual(val(val(self.complete(d)['decision'])['selection']),'b')

    def test_CF035_limits_are_operational_never_impossibility(self):
        d=water()
        for limits in [{'max_nodes':0},{'max_nodes':3},{'max_operations':0},{'max_input_bytes':1}]:
            with self.subTest(limits=limits):
                r=self.run_data(d,limits)
                self.assertEqual(r['execution']['status'],'LIMITED')
                self.assertEqual(r['integration']['state'],'BLOCKED')
                self.assertEqual(r['decision']['state'],'BLOCKED')
                self.assertIn('COMPUTATION_LIMIT',self.codes(r))
                self.assertNotIn('NO_FEASIBLE_POLICY',self.codes(r))
                self.assertEqual({x['name']:int(x['bound']) for x in r['execution']['limits']},
                                 {**limits,'python_recursion_depth':sys.getrecursionlimit()})
        r=self.complete(d)
        v=verify_result(raw(d),r,limits={'max_operations':0})
        self.assertIsNone(v['valid']); self.assertEqual(v['status'],'INCOMPLETE')
        # FP1 admits no dependency-graph override; a circular constructor request is invalid input.
        d['construction']={'CAG':['task'],'task':['CAG']}
        self.assertEqual(self.run_data(d)['presentation'],'INVALID')

    def test_H0_root_is_leaf_empty_future_not_missing(self):
        d=small({'p':[['o']]})
        r=self.complete(d); p=policies(r)['p']
        self.assertEqual(len(p['causal']['nodes']),1)
        self.assertEqual(qset(p['causal']['leaves']),{('p',())})
        self.assertEqual(p['causal']['nodes'][0]['action']['state'],'OUTSIDE_DOMAIN')
        self.assertIn('TERMINAL_NO_ACTION',self.codes(r))
        self.assertEqual(val(p['probability']['pvs']),'1/1')
        self.assertEqual(val(p['generative']['cag']),['o'])
        self.assertEqual(val(p['generative']['additional']),[])
        self.assertEqual(p['generative']['witnesses'],[])
        self.assertEqual(r['integration']['state'],'DEFINED')
        d['law']['rows']=[{'query':query('p'),'weights':[]}]
        self.assertEqual(self.run_data(d)['presentation'],'INVALID')

    def test_exact_rational_and_strict_scalar_grammar(self):
        d=small(); huge=10**80+7
        add_resources(d,{'water':['d1','d2']},{('p',(),'d1'):f'{huge}/3',('p',(),'d2'):'1/3',('p',('r',),'d1'):'1/3',('p',('r',),'d2'):'1/3'},bound=f'{huge}/1')
        p=policies(self.complete(d))['p']; masses=keyed(p['resources'])
        expected=Fraction(huge+1,3)
        self.assertEqual(val(masses['p',()]['total']),f'{expected.numerator}/{expected.denominator}')
        for invalid in ['2/4','-0/1','00/1','+1/1','1/0','1/01',0.5,True]:
            with self.subTest(invalid=invalid):
                x=copy.deepcopy(d); x['resources']['values'][0]['value']=invalid
                self.assertEqual(self.run_data(x)['presentation'],'INVALID')
        for invalid in [0,'00','-1',True]:
            x=small(); x['meta']['horizon']=invalid
            self.assertEqual(self.run_data(x)['presentation'],'INVALID')

    def test_structural_duplicates_and_invalid_unreached_references(self):
        d=small(); b=raw(d)
        r=evaluate(b.replace(b'"horizon":"1"',b'"horizon":"1","horizon":"1"'))
        self.assertEqual(r['presentation'],'INVALID'); self.assertIn('DUPLICATE_KEY',self.codes(r))
        for table in [('model','updates'),('semantics','task'),('functional','reduction'),('composition','rows')]:
            x=small()
            rows=x[table[0]][table[1]]
            if isinstance(rows,dict): rows=rows['rows']
            rows.append(copy.deepcopy(rows[0]))
            self.assertEqual(self.run_data(x)['presentation'],'INVALID')
        d=small(); d['functional']['measurements']=[{'t':'0','x':'Ghost','index':'Ghost','raw':'0/1'}]
        self.assertEqual(self.run_data(d)['presentation'],'INVALID')
        d=small(); d['composition']['rows'].append({'query':query('p',['ghost']),'values':[]})
        self.assertEqual(self.run_data(d)['presentation'],'INVALID')
        self.assertEqual(evaluate(b'\xff')['presentation'],'INVALID')

    def test_law_support_error_is_component_failure_but_duplicate_is_invalid(self):
        d=small(); d['law']['rows'][0]['weights'][0]['branch']='ghost'
        r=self.complete(d); self.assertIn('LAW_INVALID',self.codes(r))
        self.assertEqual(policies(r)['p']['probability']['pvs']['state'],'BLOCKED')
        d=small(); d['law']['rows'][0]['weights'].append(copy.deepcopy(d['law']['rows'][0]['weights'][0]))
        self.assertEqual(self.run_data(d)['presentation'],'INVALID')

    def test_invalid_preorder_and_common_calibration_fail_all_dependents(self):
        d=small({'p':[['o','g']], 'q':[['o','g']]})
        d['generative']['common_order']=[]
        r=self.complete(d); self.assertIn('GEN_ORDER_INVALID',self.codes(r))
        self.assertTrue(all(p['generative']['cag']['state']=='BLOCKED' for p in r['policies']))
        d=small({'p':[['o','g']], 'q':[['o','g']]})
        add_function(d,{(0,'x0'):['0/1'],(1,'x_p_r_1'):['1/1'],(1,'x_q_r_1'):['0/1']})
        d['functional']['indices'][0]['calibration'][1]['value']='0/1'
        r=self.complete(d); self.assertIn('CALIBRATION_ORDER',self.codes(r))
        self.assertEqual(val(r['decision'])['B'],[])
        self.assertTrue(all(p['functional']['terminal']['state']=='BLOCKED' for p in r['policies']))

    def test_result_certificate_corruption_is_rejected(self):
        d=water(); b=raw(d); r=self.complete(d)
        def rejected(mutator):
            candidate=copy.deepcopy(r); mutator(candidate)
            report=verify_result(b,candidate)
            self.assertFalse(report['valid'],report)
            self.assertTrue(report['errors'])
        rejected(lambda x:x.__setitem__('input_digest','0'*64))
        rejected(lambda x:x['policies'][0]['causal']['leaves'].pop())
        rejected(lambda x:x['policies'][0]['generative']['witnesses'].pop())
        rejected(lambda x:x['policies'][0]['probability']['pvs'].__setitem__('value','1/1'))
        rejected(lambda x:x['decision']['value'].__setitem__('frontier',['pi_ah']))
        rejected(lambda x:x['decision']['value']['pairs'][0].__setitem__('weak','0'))
        rejected(lambda x:x['integration']['value']['guards'].pop())
        rejected(lambda x:x['checks'][0].__setitem__('outcome','FAIL'))
        rejected(lambda x:x['checks'][0].__setitem__('support',[{'document':'OUTPUT','pointer':'/checks/0'}]))
        rejected(lambda x:x['checks'][0].__setitem__('support',[{'document':'INPUT','pointer':'/does-not-exist'}]))

    def test_set_order_and_generated_identifier_spelling_are_not_semantics(self):
        d=water(); b=raw(d); r=self.complete(d)
        # Output arrays are tables or Sets except these explicit semantic Lists.
        def reverse_tables(x,key=None):
            if isinstance(x,dict): return {k:reverse_tables(v,k) for k,v in x.items()}
            if isinstance(x,list):
                values=[reverse_tables(v) for v in x]
                return values if key in ('path','window','identities','outcomes') else values[::-1]
            return x
        # Identities is a Cell whose value is List[ID], requiring explicit preservation.
        candidate=reverse_tables(r)
        for p in candidate['policies']:
            original=policies(r)[p['policy']]
            traces={qkey(x['leaf']):x for x in original['generative']['traces']}
            for tr in p['generative']['traces']:
                tr['identities']=copy.deepcopy(traces[qkey(tr['leaf'])]['identities'])
        ids={x['id']:'renamed'+str(i) for i,x in enumerate(r['checks']+r['diagnostics'])}
        for p in r['policies']:
            for e in p['evidence']:
                if e['verdict']['state']=='DEFINED': ids[e['verdict']['value']['id']]='cert'+str(len(ids))
        ids[val(r['integration'])['id']]='integrationRenamed'
        def rename(x):
            if isinstance(x,dict): return {k:rename(v) for k,v in x.items()}
            if isinstance(x,list): return [rename(v) for v in x]
            return ids.get(x,x) if isinstance(x,str) else x
        candidate=rename(candidate)
        report=verify_result(b,candidate)
        self.assertTrue(report['valid'],report)
        # Reordering input Sets/tables changes the bytes/hash but not the frontier.
        x=copy.deepcopy(d)
        for k in ['policies','scenarios','assumptions','constraints']: x[k].reverse()
        for block in ['functional','generative','welfare','semantics','law','resources','composition']:
            for k,v in x[block].items():
                if isinstance(v,list): v.reverse()
        rx=self.complete(x)
        self.assertNotEqual(rx['input_digest'],r['input_digest'])
        self.assertEqual(set(val(rx['decision'])['frontier']),set(val(r['decision'])['frontier']))
        self.assertEqual(val(rx['decision'])['selection']['state'],'OUTSIDE_DOMAIN')

    def test_causal_action_value_survives_failed_guard(self):
        for field,code in [('executable','ACTION_NOT_EXECUTABLE'),('admissible','ACTION_NOT_ADMISSIBLE')]:
            d=small(); d['model'][field][0]['actions']=[]
            r=self.run_data(d); p=policies(r)['p']
            self.assertIn(code,self.codes(r))
            self.assertEqual(val(p['causal']['nodes'][0]['action']),'act_p')
            self.assertEqual(p['causal']['complete']['state'],'OUTSIDE_DOMAIN')
            self.assertEqual(p['causal']['leaves'],[])

    def test_causal_missing_update_keeps_edge_without_fabricated_child(self):
        d=small(); d['model']['updates']=[]
        r=self.run_data(d); p=policies(r)['p']
        self.assertEqual(r['presentation'],'UNRESOLVED')
        self.assertIn('UPDATE_MISSING',self.codes(r)); self.assertIn('QUERY_UNRESOLVED',self.codes(r))
        self.assertEqual(len(p['causal']['nodes']),1)
        self.assertEqual(len(p['causal']['nodes'][0]['outcomes']),1)
        self.assertEqual(p['causal']['nodes'][0]['outcomes'][0]['next_i']['state'],'OUTSIDE_DOMAIN')
        self.assertEqual(p['causal']['leaves'],[])

    def test_causal_reconvergence_never_merges_occurrences(self):
        d=small({'p':[['o','g'],['o','g']]})
        root=d['model']['transitions'][0]
        root['outcomes'][1]['next_x']=root['outcomes'][0]['next_x']
        p=policies(self.complete(d))['p']
        self.assertEqual(len(p['causal']['nodes']),3)
        self.assertEqual(len(p['causal']['leaves']),2)
        self.assertEqual({n['x'] for n in p['causal']['nodes'] if n['t']=='1'},{'x_p_r_1'})
        self.assertEqual(len(p['functional']['points']),2)
        self.assertEqual(len(p['evidence']),3)

    def test_all_missing_welfare_coordinates_are_reported(self):
        d=small({'p':[['o','g','g'],['o','g','g']]})
        add_welfare(d,{qkey(x['query']):None for x in d['composition']['rows']})
        r=self.complete(d)
        missing={qkey(q) for x in r['diagnostics'] if x['code']=='WELFARE_MISSING' for q in x['queries']}
        self.assertEqual(missing,{qkey(x['query']) for x in d['composition']['rows']})
        p=policies(r)['p']
        self.assertEqual(len(p['welfare']['cells']),5)
        self.assertTrue(all(x['value']['state']=='OUTSIDE_DOMAIN' for x in p['welfare']['cells']))

    def test_shared_translation_failure_excludes_entire_candidate_block(self):
        d=small({'p':[['o','a']], 'q':[['o','b']]},recipe={'kind':'hold','length':'0'})
        # Each policy locally sees only o and its own endpoint. The violated a<=b
        # comparison is visible only in the common union of their reached alphabets.
        reflexive=[[x,x] for x in ['o','a','b']]
        d['generative']['native_order']=reflexive+[['a','b']]
        d['generative']['common_order']=copy.deepcopy(reflexive)
        r=self.complete(d)
        self.assertIn('GEN_ORDER_TRANSPORT',self.codes(r))
        self.assertEqual(val(r['decision'])['B'],[])
        self.assertTrue(all(p['generative']['cag']['state']=='BLOCKED' for p in r['policies']))

    def test_strong_guards_include_hard_failed_policies(self):
        d=water()
        d['functional']['measurements']=[x for x in d['functional']['measurements'] if not(x['t']=='1' and x['x']=='x_ah_r' and x['index']=='f_water')]
        r=self.complete(d); dec=val(r['decision'])
        self.assertIn('pi_ah',dec['failed'])
        self.assertEqual(next(c for c in r['checks'] if c['rule']=='G05')['outcome'],'FAIL')
        self.assertEqual(dec['coverage'],'RELATIVE')
        self.assertNotEqual(r['integration']['state'],'DEFINED')

    def test_global_reduction_blocked_by_other_incomplete_policy_preserves_local_values(self):
        d=small({'p':[['o','g']], 'q':[['o','g']]})
        d['policies'][1]['decisions']=[]
        r=self.run_data(d); p=policies(r)['p']
        self.assertEqual(p['functional']['reduction']['state'],'BLOCKED')
        self.assertEqual(p['functional']['terminal']['state'],'DEFINED')
        self.assertEqual(p['generative']['cag']['state'],'DEFINED')
        self.assertEqual(val(r['decision'])['B'],['p'])

    def test_task_all_negative_witness_preserves_missing_same_scope(self):
        d=small({'p':[['o','g'],['o','g']]})
        d['semantics']['task']=[{'state':'sem_p_r','value':'0'}]
        d['constraints']=[{'id':'All','kind':'task_all','scope':'LEAVES','basis':['A']}]
        p=policies(self.complete(d))['p']; h=p['hard'][0]
        self.assertEqual(val(h['value']),'0')
        self.assertEqual(qset(h['violations']),{('p',('r',))})
        self.assertEqual(qset(h['missing']),{('p',('s',))})
        self.assertEqual(qset(val(h['scope'])),{('p',('r',)),('p',('s',))})


if __name__ == '__main__':
    unittest.main()
