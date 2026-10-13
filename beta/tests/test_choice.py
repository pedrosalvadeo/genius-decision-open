"""Declared-choice contract and real worker tests; no invented field evidence."""
from copy import deepcopy
from fractions import Fraction
import io
import json
from pathlib import Path
import random
import tempfile
import unittest
import zipfile
from genius_beta.choice import ChoiceError, canonical, execute, review, validate_payload
from genius_beta.app import create_app
from genius_beta.worker import Worker

BASE = Path(__file__).resolve().parents[1]


def example():
    return json.loads((BASE/'examples/choice-leisure.json').read_text())


def confirm(p):
    p['model_confirmation']=review({k:p[k] for k in ('context','criteria','alternatives','selection')})['confirmation']
    return p


class ChoiceTests(unittest.TestCase):
    def run_choice(self,p):
        with tempfile.TemporaryDirectory() as d:
            return execute(confirm(p),Path(d)/'case')

    def test_real_kernel_priorities_and_tradeoff(self):
        p=example();before=deepcopy(p);r=self.run_choice(p)
        self.assertEqual(p,before)
        self.assertEqual(r['recommendation'],'museum')
        self.assertEqual(r['frontier'],['museum','park'])
        self.assertEqual(r['excluded'][0]['alternative'],'far')
        self.assertEqual(r['tradeoffs'][0]['criterion'],'time')
        self.assertEqual(r['real_pvs'],'NOT_ASSESSED')
        self.assertFalse(r['narrative_interpreted'])
        self.assertEqual(r['verification']['valid'],True)

    def test_preference_changes_selection_not_frontier(self):
        p=example();p['selection']['criteria_order']=['time','interest'];r=self.run_choice(p)
        self.assertEqual(r['recommendation'],'park')
        self.assertEqual(r['frontier'],['museum','park'])
        self.assertEqual(r['tradeoffs'][0]['criterion'],'interest')

    def test_no_preference_does_not_invent_winner(self):
        p=example();p['selection']={'mode':'unique','criteria_order':[]};r=self.run_choice(p)
        self.assertEqual(r['state'],'PREFERENCE_OR_TIE');self.assertIsNone(r['recommendation'])

    def test_exact_tie_never_uses_identifier_or_input_order(self):
        p=example();p['alternatives'][1]['values']=deepcopy(p['alternatives'][0]['values'])
        r=self.run_choice(p)
        self.assertIsNone(r['recommendation']);self.assertEqual(r['tied'],['museum','park'])
        p['alternatives'].reverse();self.assertEqual(self.run_choice(p)['tied'],r['tied'])

    def test_unknown_retained_even_if_only_one_complete_option(self):
        p=example();p['alternatives'][1]['values']['interest']=None;r=self.run_choice(p)
        self.assertEqual(r['state'],'NEEDS_INFORMATION');self.assertFalse(r['frontier_complete'])
        self.assertIsNone(r['recommendation']);self.assertEqual(r['questions'][0]['state'],'PV_UNKNOWN')
        self.assertNotIn('museum',[x['alternative'] for x in r['excluded']])

    def test_unknown_bound_cannot_be_assumed_satisfied(self):
        p=example();p['alternatives'][0]['values']['time']=None
        self.assertIsNone(self.run_choice(p)['recommendation'])

    def test_empty_feasible_set_and_minimum_constraint(self):
        p=example();p['criteria'][0]['limit']='1';r=self.run_choice(p)
        self.assertEqual(r['state'],'NO_FEASIBLE_ALTERNATIVE');self.assertEqual(len(r['excluded']),3)
        p=example();p['criteria'][1]['limit']='8';r=self.run_choice(p)
        self.assertEqual(r['recommendation'],'museum')
        self.assertEqual({x['alternative'] for x in r['excluded']},{'park','far'})

    def test_confirmation_binds_all_fields_and_provenance(self):
        for mutate in (lambda p:p['selection'].update(criteria_order=['time','interest']),
                       lambda p:p['alternatives'][0].update(source='Dato actualizado'),
                       lambda p:p['context'].update(question='Otra decisión'),
                       lambda p:p['criteria'][0].update(limit='60')):
            p=example();mutate(p)
            with self.assertRaises(ChoiceError):validate_payload(p)

    def test_invalid_input_is_not_a_recommendation(self):
        for v in (True,1,1.5,'NaN','Infinity','-1','1e10','1/0','9'*33,'1/1000001',{},[]):
            p=example();p['alternatives'][0]['values']['time']=v
            with self.subTest(value=v),self.assertRaises(ChoiceError):confirm(p)
        for category in ('health','investment','employment',None,[]):
            p=example();p['context']['category']=category
            with self.subTest(category=category),self.assertRaises(ChoiceError):confirm(p)

    def test_no_default_preference_or_silent_omission(self):
        for order in (['time'],['time','time'],['time','ghost'],['time',{}]):
            p=example();p['selection']['criteria_order']=order
            with self.assertRaises(ChoiceError):confirm(p)
        p=example();p['alternatives'][0]['values']['ghost']='1'
        with self.assertRaises(ChoiceError):confirm(p)

    def test_comparison_matches_independent_exact_oracle(self):
        # Fixed seed; independent direct inequalities, no kernel oracle imports.
        rng=random.Random(9127)
        for _ in range(18):
            p=example();p['selection']={'mode':'unique','criteria_order':[]}
            for a in p['alternatives']:
                a['values']={'time':str(rng.randrange(1,50))+'/2','interest':str(rng.randrange(1,20))+'/2'}
            rows=p['alternatives'];vals={a['id']:(-Fraction(a['values']['time']),Fraction(a['values']['interest'])) for a in rows}
            expected=sorted(i for i,v in vals.items() if not any(all(x>=y for x,y in zip(w,v)) and any(x>y for x,y in zip(w,v)) for j,w in vals.items() if i!=j))
            r=self.run_choice(p)
            self.assertEqual(r['frontier'],expected)
            self.assertEqual(r['recommendation'],expected[0] if len(expected)==1 else None)

    def test_maximum_profile_stays_within_archive_and_time_budget(self):
        p=example();p['criteria']=[dict(id='c'+str(i),label='Criterio '+str(i),unit='u',direction='max',limit='0') for i in range(5)]
        p['alternatives']=[dict(id='a'+str(i),label='Alternativa '+str(i),source='Sintético',values={c['id']:str(i) for c in p['criteria']}) for i in range(8)]
        p['selection']={'mode':'lexicographic','criteria_order':[c['id'] for c in p['criteria']]}
        with tempfile.TemporaryDirectory() as d:
            r=execute(confirm(p),Path(d)/'case')
            self.assertEqual(r['recommendation'],'a7')
            self.assertLess(sum(x.stat().st_size for x in (Path(d)/'case').iterdir()),2*1024*1024)


class ChoiceServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);d=Path(self.temp.name)
        self.config=dict(DATA_DIR=d,DATABASE=d/'db',SUSPEND_FILE=d/'SUSPENDED',PUBLIC_URL='http://localhost',TESTING=True)
        self.app=create_app(self.config);self.client=self.app.test_client()
        r=self.client.post('/api/register',json=dict(username='choice_test',password='Synthetic-password-42',privacy_accepted=True,privacy_version=self.app.config['PRIVACY_VERSION'],adult_confirmed=True))
        self.auth={'X-CSRF-Token':r.json['csrf_token']}

    def worker(self):
        w=Worker(self.config)
        try:w.acquire();w.run_once()
        finally:w.close()

    def test_human_review_revision_persistence_and_verifiable_archive(self):
        p=example();profile=p.pop('profile');m={k:p[k] for k in ('context','criteria','alternatives','selection')}
        self.assertEqual(self.client.post('/api/choice/review',json=m).status_code,403)
        r=self.client.post('/api/choice/review',json=m,headers=self.auth)
        self.assertEqual(r.status_code,200);p['model_confirmation']=r.json['confirmation']
        c=self.client.post('/api/cases',json=dict(profile=profile,title='Sintético',input=p),headers=self.auth)
        self.assertEqual(c.status_code,201,c.json);cid=c.json['case']['id']
        j=self.client.post('/api/cases/'+cid+'/run',json={},headers=self.auth).json['job']['id'];self.worker()
        result=self.client.get('/api/jobs/'+j).json['job'];self.assertEqual(result['status'],'completed',result)
        self.assertEqual(result['result']['recommendation'],'museum')
        response=self.client.get(result['artifacts']['url'])
        with zipfile.ZipFile(io.BytesIO(response.data)) as z:
            self.assertEqual(json.loads(z.read('report.json')),result['result'])
            self.assertIn('fp1-result.json',z.namelist())
        p['alternatives'][1]['values']['interest']=None
        self.assertEqual(self.client.patch('/api/cases/'+cid,json={'input':p},headers=self.auth).status_code,400)
        confirm(dict(p,profile=profile)) # Real confirmation must be refreshed in the submitted input too.
        p['model_confirmation']=review({k:p[k] for k in m})['confirmation']
        self.assertEqual(self.client.patch('/api/cases/'+cid,json={'input':p},headers=self.auth).status_code,200)
        detail=self.client.get('/api/cases/'+cid).json
        self.assertEqual(len(detail['revisions']),2);self.assertEqual(detail['jobs'][0]['result']['recommendation'],'museum')
        other=self.app.test_client();self.assertEqual(other.get('/api/cases/'+cid).status_code,401)

    def test_mcp_prepare_and_execute_scoped(self):
        r=self.client.post('/api/agents/register',json=dict(policy_version='agent-access-2026-10-06-v1',data_policy_acknowledged=True,scopes=['cases:read','cases:write','jobs:run']))
        auth={'Authorization':'Bearer '+r.json['credential']['token'],'Content-Type':'application/json','Accept':'application/json, text/event-stream','MCP-Protocol-Version':'2025-11-25'}
        def call(name,args):
            r=self.client.post('/mcp',json=dict(jsonrpc='2.0',id=1,method='tools/call',params=dict(name=name,arguments=args)),headers=auth)
            self.assertEqual(r.status_code,200,r.json);self.assertFalse(r.json['result'].get('isError'),r.json)
            return r.json['result']['structuredContent']
        p=example();p.pop('profile');m={k:p[k] for k in ('context','criteria','alternatives','selection')}
        p['model_confirmation']=call('prepare_decision',m)['confirmation']
        cid=call('create_case',dict(title='MCP synthetic choice',profile='choice',input=p))['case']['id']
        jid=call('run_case',dict(case_id=cid))['job']['id'];self.worker()
        self.assertEqual(call('get_job',dict(job_id=jid))['job']['result']['recommendation'],'museum')
        p['selection']={'mode':'unique','criteria_order':[]};m['selection']=p['selection'];p['model_confirmation']=call('prepare_decision',m)['confirmation']
        call('revise_case',dict(case_id=cid,input=p))
        self.assertEqual(len(call('get_case',dict(case_id=cid))['revisions']),2)


if __name__=='__main__':unittest.main()
