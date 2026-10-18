"""Machine twin access, real engine receipts and authority/lifecycle boundaries."""
import json
from pathlib import Path
import tempfile
import time
import unittest
from genius_beta.app import create_app
from genius_beta.agent_access import TWIN_SCOPES, required_scope
from genius_beta.db import connect, transaction
from genius_beta.twin_integration import tenant_path, lifecycle_lock
from genius_twin.registry import STOCKFLOW, example


class AgentTwinTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.app = create_app(dict(DATA_DIR=root, DATABASE=root/'db.sqlite3',
            SUSPEND_FILE=root/'SUSPENDED', PUBLIC_URL='http://localhost', TESTING=True,
            ENV='development', REGISTRATION_OPEN=True, TWIN_ENABLED=True))
        self.client = self.app.test_client(use_cookies=False)
        self.headers = self.register([*TWIN_SCOPES, 'account:delete', 'cases:read'])

    def tearDown(self):
        self.temp.cleanup()

    def register(self, scopes=None):
        value = dict(policy_version='agent-access-2026-10-06-v1', data_policy_acknowledged=True)
        if scopes is not None:
            value['scopes'] = scopes
        r = self.client.post('/api/agents/register', json=value)
        self.assertEqual(r.status_code, 201, r.json)
        return {'Authorization': 'Bearer '+r.json['credential']['token']}

    def rpc(self, name=None, args=None, headers=None):
        params = dict(name=name, arguments=args or {}) if name else {}
        return self.client.post('/mcp', json=dict(jsonrpc='2.0', id=1,
            method='tools/call' if name else 'tools/list', params=params),
            headers=dict(headers if headers is not None else self.headers,
                Accept='application/json, text/event-stream', **{'MCP-Protocol-Version': '2025-11-25'}))

    def call(self, name, args=None):
        response = self.rpc(name, args)
        self.assertEqual(response.status_code, 200, response.json)
        result = response.json['result']
        self.assertFalse(result['isError'], result)
        return result['structuredContent']

    def confirmed(self):
        cid = self.call('twin_create_case', {'payload': {'text': 'Recursos declarados de prueba', 'profile': STOCKFLOW}})['case']['id']
        model = example('stockflow_care')['model']
        pid = self.call('twin_propose', dict(case_id=cid, payload=dict(base_version=0,
            kind='declared_model', text='Modelo explícito de prueba', structured={'model': model})))['proposal']['id']
        payload = dict(base_version=0, confirmed=True, acknowledge_declared=True, idempotency_key='test-confirmation')
        self.call('twin_accept', dict(proposal_id=pid, payload=payload))
        return cid, pid

    def test_real_engine_lifecycle_and_cross_tenant_isolation(self):
        cid, pid = self.confirmed()
        result = self.call('twin_evaluate', dict(case_id=cid, version=1))
        self.assertEqual(result['job']['status'], 'completed')
        self.assertTrue(result['evaluation']['verification']['valid'])
        self.assertEqual(self.call('twin_get_job', {'job_id': result['job']['id']})['job']['id'], result['job']['id'])
        self.call('twin_compare', dict(case_id=cid, before=1, after=1))
        self.call('twin_export', {'case_id': cid})
        second = self.register(list(TWIN_SCOPES))
        for path in (f'/cases/{cid}', f'/cases/{cid}/export', f'/jobs/{result["job"]["id"]}'):
            self.assertEqual(self.client.get('/api/twin'+path, headers=second).status_code, 404)
        self.assertEqual(self.client.post(f'/api/twin/cases/{cid}/evaluate', headers=second, json={'version': 1}).status_code, 404)
        self.assertEqual(self.client.post(f'/api/twin/proposals/{pid}/accept', headers=second,
            json=dict(base_version=0, confirmed=True, acknowledge_declared=True, idempotency_key='other-confirmation')).status_code, 404)
        uid = self.client.get('/api/agents/me', headers=self.headers).json['agent']['id']
        path = tenant_path(self.app.config['DATA_DIR'], uid)
        self.assertTrue(path.exists())
        with lifecycle_lock(self.app.config['DATA_DIR'], uid):
            self.assertEqual(self.client.delete('/api/agents/me', headers=self.headers).status_code, 409)
        self.assertEqual(self.client.delete('/api/agents/me', headers=self.headers).status_code, 204)
        self.assertFalse(path.exists())
        self.assertEqual(self.client.get('/api/twin/cases', headers=self.headers).status_code, 401)

    def test_scope_opt_in_export_and_revocation(self):
        self.confirmed()
        default = self.register()
        self.assertEqual(self.client.get('/api/twin/cases', headers=default).status_code, 403)
        self.assertFalse(any(t['name'].startswith('twin_') for t in self.rpc(headers=default).json['result']['tools']))
        rotated = self.client.post('/api/agents/token', headers=self.headers, json={'scopes': ['cases:read', 'account:delete']})
        self.assertEqual(rotated.status_code, 200)
        limited = {'Authorization': 'Bearer '+rotated.json['credential']['token']}
        self.assertNotIn('twins', self.client.get('/api/export', headers=limited).json)
        self.assertEqual(self.client.get('/api/twin/cases', headers=limited).status_code, 403)
        self.assertEqual(self.client.get('/api/twin/cases', headers=self.headers).status_code, 401)
        self.assertEqual(self.client.post('/api/agents/token', headers=limited, json={'scopes': ['twins:read']}).status_code, 400)
        for method, path in [('POST', '/api/twin/runtime'), ('GET', '/api/twin/cases/../runtime'), ('GET', '/api/twin/admin')]:
            self.assertIsNone(required_scope(method, path))

    def test_disabled_feature_and_scoped_read_only(self):
        read = self.register(['twins:read'])
        tools = self.rpc(headers=read).json['result']['tools']
        self.assertIn('twin_schema', [t['name'] for t in tools])
        self.assertNotIn('twin_create_case', [t['name'] for t in tools])
        self.assertEqual(self.rpc('twin_create_case', {'payload': {'text': 'x'}}, read).json['result']['structuredContent']['error']['http_status'], 403)
        self.assertEqual(self.client.get('/api/twin/profiles/'+STOCKFLOW+'/schema', headers=read).status_code, 200)
        self.call('twin_example', {'example': 'stockflow_care'})
        self.app.config['TWIN_ENABLED'] = False
        self.assertFalse(any(t['name'].startswith('twin_') for t in self.rpc().json['result']['tools']))
        self.assertEqual(self.rpc('twin_list_cases').json['result']['structuredContent']['error']['http_status'], 503)

    def test_shared_compute_quota_and_agent_capacity(self):
        self.app.config.update(MAX_AGENT_JOBS_DAILY=1, MAX_AGENT_CASES=1, MAX_AGENT_REVISIONS=1)
        cid, _ = self.confirmed()
        self.assertEqual(self.rpc('twin_create_case', {'payload': {'text': 'Segundo caso'}}).json['result']['structuredContent']['error']['http_status'], 429)
        uid = self.client.get('/api/agents/me', headers=self.headers).json['agent']['id']
        db = connect(self.app.config['DATABASE'])
        try:
            # A prior legacy job uses the same counter as a twin evaluation.
            from genius_beta.agent_access import reserve_agent_job
            from genius_beta.app import APIError
            with transaction(db):
                reserve_agent_job(db, self.app.config, uid, int(time.time()), APIError)
        finally:
            db.close()
        denied = self.rpc('twin_evaluate', dict(case_id=cid, version=1)).json['result']
        self.assertEqual(denied['structuredContent']['error']['code'], 'agent_daily_limit')
        self.assertEqual(self.call('twin_get_case', {'case_id': cid})['jobs'], [])

    def test_delete_requires_explicit_confirmation_and_current_version(self):
        cid, _ = self.confirmed()
        self.assertIn('error', self.rpc('twin_delete_case', dict(case_id=cid, base_version=1)).json)
        self.assertEqual(self.rpc('twin_delete_case', dict(case_id=cid, base_version=0, confirm=True)).json['result']['structuredContent']['error']['http_status'], 409)
        self.call('twin_delete_case', dict(case_id=cid, base_version=1, confirm=True))
        self.assertEqual(self.call('twin_list_cases')['cases'], [])

    def test_intervention_design_mcp_rest_native_result_and_scopes(self):
        fixture = self.call('twin_intervention_example')
        schema = self.call('twin_intervention_schema')
        self.assertEqual(schema['title'], 'genius-intervention-design/1')
        self.assertEqual(self.client.get('/api/twin/interventions/schema', headers=self.headers).json, schema)
        cid = self.call('twin_create_case', {'payload': {'text': 'Synthetic transfers', 'profile': STOCKFLOW}})['case']['id']
        pid = self.call('twin_propose', dict(case_id=cid,payload=dict(base_version=0,kind='declared_model',
            text='Synthetic base assumptions',structured={'model':fixture['model']})))['proposal']['id']
        self.call('twin_accept',dict(proposal_id=pid,payload=dict(base_version=0,confirmed=True,acknowledge_declared=True,idempotency_key='intervention-base')))
        payload = dict(case_id=cid,base_version=1,text='Redistribute declared resources',design=fixture['design'])
        read_only = self.register(['twins:read'])
        denied = self.rpc('twin_design_interventions',payload,read_only).json['result']
        self.assertTrue(denied['isError'])
        self.assertEqual(denied['structuredContent']['error']['http_status'],403)
        self.assertEqual(self.client.post(f'/api/twin/cases/{cid}/proposals',headers=read_only,
            json=dict(base_version=1,kind='intervention_design',text='No write scope',structured={'design':fixture['design']})).status_code,403)
        proposal = self.call('twin_design_interventions',payload)['proposal']
        self.assertEqual(proposal['metadata']['intervention_design']['generated_count'],2)
        self.assertEqual(self.call('twin_get_case',{'case_id':cid})['case']['current_version'],1)
        self.call('twin_accept',dict(proposal_id=proposal['id'],payload=dict(base_version=1,confirmed=True,acknowledge_declared=True,idempotency_key='intervention-confirm')))
        result = self.call('twin_evaluate',dict(case_id=cid,version=2))
        self.assertEqual(result['job']['status'],'completed',result)
        self.assertTrue(result['evaluation']['verification']['valid'])
        self.assertEqual(result['evaluation']['canonical_results']['decision']['selected'],'intervention.redistribute.2')
        self.assertEqual(self.client.get('/api/twin/jobs/'+result['job']['id'],headers=self.headers).json,result)
        self.assertEqual(self.client.get('/api/twin/cases/'+cid,headers=read_only).status_code,404)
        # The convenience tool uses /proposals and cannot bypass its limit.
        self.app.config['MAX_AGENT_REVISIONS'] = 0
        self.assertEqual(self.rpc('twin_design_interventions',dict(payload,base_version=2)).json['result']['structuredContent']['error']['code'],'proposal_limit')
        self.assertEqual(self.client.delete('/api/agents/me',headers=self.headers).status_code,204)

    def test_world_construction_mcp_rest_scopes_quota_and_native_export(self):
        f=json.loads((Path(__file__).parents[2]/'twin/examples/world/workshop.json').read_text())
        contract=self.call('twin_world_contract')
        self.assertEqual(contract['construction_schema']['title'],'genius-world-construction/1')
        self.assertEqual(self.client.get('/api/twin/world/contract',headers=self.headers).json,contract)
        cid=self.call('twin_create_case',{'payload':dict(text=f['narrative'],profile=STOCKFLOW)})['case']['id']
        self.call('twin_observe_system',dict(case_id=cid,payload=dict(base_version=0,observation_revision=0,
            idempotency_key='world-observation',observation=f['observation'])))
        args=dict(case_id=cid,payload=dict(base_version=0,construction=f['construction']))
        another=self.register(list(TWIN_SCOPES))
        self.assertEqual(self.rpc('twin_prepare_world',args,another).json['result']['structuredContent']['error']['http_status'],404)
        rotated=self.client.post('/api/agents/token',headers=another,json={'scopes':['twins:read']})
        self.assertEqual(rotated.status_code,200,rotated.json)
        read_only={'Authorization':'Bearer '+rotated.json['credential']['token']}
        self.assertNotIn('twin_prepare_world',[t['name'] for t in self.rpc(headers=read_only).json['result']['tools']])
        self.assertEqual(self.rpc('twin_prepare_world',args,read_only).json['result']['structuredContent']['error']['http_status'],403)
        preview=self.call('twin_prepare_world',args)
        self.assertEqual(preview['status'],'READY_FOR_REVIEW')
        self.assertEqual(self.client.post('/api/twin/cases/'+cid+'/world/prepare',headers=self.headers,json=args['payload']).json,preview)
        p_args=dict(case_id=cid,base_version=0,text='Synthetic cross-domain construction',construction=f['construction'])
        proposal=self.call('twin_propose_world',p_args)['proposal']
        self.assertEqual(self.call('twin_get_case',dict(case_id=cid))['case']['current_version'],0)
        self.app.config['MAX_AGENT_REVISIONS']=0
        self.assertEqual(self.rpc('twin_propose_world',p_args).json['result']['structuredContent']['error']['code'],'proposal_limit')
        self.app.config['MAX_AGENT_REVISIONS']=10
        self.call('twin_accept',dict(proposal_id=proposal['id'],payload=dict(base_version=0,confirmed=True,
            acknowledge_declared=True,idempotency_key='world-confirm')))
        result=self.call('twin_evaluate',dict(case_id=cid,version=1))
        self.assertTrue(result['evaluation']['verification']['valid'])
        self.assertEqual(result['evaluation']['world_construction'],preview['receipt'])
        exported=self.call('twin_export',dict(case_id=cid))
        self.assertEqual(exported['dossier']['versions'][0]['metadata']['world_construction']['construction'],f['construction'])
        self.assertEqual(self.client.delete('/api/agents/me',headers=self.headers).status_code,204)
        self.assertEqual(self.client.get('/api/twin/world/contract',headers=self.headers).status_code,401)

    def test_field_case_cycle_through_mcp(self):
        # The exact sequence documented in twin/docs/AGENT_QUICKSTART.md.
        listed={row['id'] for row in self.call('twin_field_cases')['field_cases']}
        self.assertIn('denver_water_2026',listed)
        case=self.call('twin_field_case',dict(case_id='denver_water_2026'))
        self.assertEqual(case['provenance'],'CITED_FIELD_CASE_WITH_DECLARED_HYPOTHESES')
        self.assertEqual(self.rpc('twin_field_case',dict(case_id='missing')).json['result']['structuredContent']['error']['http_status'],404)
        self.assertIn('colorado_basin_2027',{row['id'] for row in self.call('twin_federations')['federations']})
        basin=self.call('twin_federation',dict(federation_id='colorado_basin_2027'))
        self.assertEqual(basin['result']['scope'],'EACH_MEMBER_KERNEL_VERIFIED_JOINT_LAYER_READS_MEMBER_RESULTS')
        self.assertEqual(basin['result']['decision']['by_actor']['mead.glen_canyon']['best'],['denver:keep_ban+mead:release_6'])
        self.assertEqual(self.rpc('twin_federation',dict(federation_id='missing')).json['result']['structuredContent']['error']['http_status'],404)
        law=self.call('twin_driver_law',dict(series=[dict(period=str(y),value=str(v)) for y,v in enumerate([3,5,9,4,6],2020)],anchors=dict(low='4',high='8')))
        self.assertEqual((law['format'],law['admitted'],law['followed']),('genius-driver-law/1',False,dict(low=3,high=2)))
        series=lambda values:[dict(period=str(y),value=str(v)) for y,v in enumerate(values,2020)]
        joint=self.call('twin_joint_driver_law',dict(drivers=[dict(name='a',series=series([0,1,0,1]),anchors=dict(low='0',high='1')),
            dict(name='b',series=series([0,0,1,1]),anchors=dict(low='0',high='1'))],
            scenarios=dict(same=dict(cells=[['low','low'],['high','high']],representative=['low','low']),
                           different=dict(cells=[['low','high'],['high','low']],representative=['low','high']))))
        self.assertEqual((joint['format'],joint['admitted'],joint['followed']),('genius-joint-driver-law/1',False,dict(same=2,different=2)))
        cid=self.call('twin_create_case',{'payload':dict(text=case['narrative'],title=case['title'],profile=STOCKFLOW)})['case']['id']
        self.call('twin_observe_system',dict(case_id=cid,payload=dict(base_version=0,observation_revision=0,
            idempotency_key='field-observation',observation=case['observation'])))
        preview=self.call('twin_prepare_world',dict(case_id=cid,payload=dict(base_version=0,construction=case['construction'])))
        self.assertEqual(preview['status'],'READY_FOR_REVIEW')
        proposal=self.call('twin_propose_world',dict(case_id=cid,base_version=0,text=case['narrative'],construction=case['construction']))['proposal']
        self.call('twin_accept',dict(proposal_id=proposal['id'],payload=dict(base_version=0,confirmed=True,
            acknowledge_declared=True,idempotency_key='field-confirm')))
        result=self.call('twin_evaluate',dict(case_id=cid,version=1))
        decision=result['evaluation']['canonical_results']['decision']
        self.assertEqual((decision['feasible'],decision['failed'],decision['selected']),(['keep_ban','resume_if_70','resume_may'],[],None))
        month=30*24*3600
        window=self.call('twin_decision_window',dict(case_id=cid,version=1,window=dict(available_seconds=60,step_seconds=month,first_action_offset_seconds=3600)))
        self.assertEqual((window['format'],window['status'],window['committed_steps']),('genius-decision-window/1','FITS_WINDOW',0))
        late=self.call('twin_decision_window',dict(case_id=cid,version=1,window=dict(available_seconds=2*month,step_seconds=month,
            seconds_per_cell=str(month),committed_route='keep_ban')))
        self.assertEqual((late['status'],late['committed_steps'],late['committed_route']),('DOES_NOT_FIT_WINDOW',2,'keep_ban'))
        observed=self.call('twin_observe',dict(case_id=cid,payload=dict(base_version=1,policy_id='keep_ban',scenario_id='dry',
            day=1,variable='storage',unit='pct_capacity',value='65.5',observed_at='2026-11-15T12:00:00+00:00',
            source='Synthetic test reading; no field data',idempotency_key='field-reading')))['observation']
        self.assertEqual(observed['comparison']['status'],'MATCH_NOT_MODEL_VALIDATION')
        reread=self.call('twin_get_job',dict(job_id=result['job']['id']))
        self.assertEqual(reread['job']['freshness']['observed_after_computation'],[observed['id']])

    def test_system_observations_scopes_limits_identity_and_native_receipt(self):
        fixture=self.call('twin_system_example')
        self.assertEqual(self.call('twin_system_schema')['title'],'genius-system-observation/1')
        self.assertEqual(self.call('twin_system_scope_schema')['title'],'genius-system-scope/1')
        cid=self.call('twin_create_case',{'payload':{'text':'Sistema sintético y su entorno','profile':STOCKFLOW}})['case']['id']
        payload=dict(base_version=0,observation_revision=0,idempotency_key='system-observation',observation=fixture['observation'])
        read_only=self.register(['twins:read'])
        tools=self.rpc(headers=read_only).json['result']['tools']
        self.assertIn('twin_system_context',[t['name'] for t in tools])
        self.assertNotIn('twin_observe_system',[t['name'] for t in tools])
        denied=self.rpc('twin_observe_system',dict(case_id=cid,payload=payload),read_only).json['result']
        self.assertEqual(denied['structuredContent']['error']['http_status'],403)
        self.app.config['MAX_AGENT_REVISIONS']=1
        recorded=self.call('twin_observe_system',dict(case_id=cid,payload=payload))
        self.assertEqual(recorded,self.call('twin_observe_system',dict(case_id=cid,payload=payload)))
        denied=self.rpc('twin_observe_system',dict(case_id=cid,payload=dict(payload,observation_revision=1,idempotency_key='next-system-observation'))).json['result']
        self.assertEqual(denied['structuredContent']['error']['code'],'system_observation_limit')
        state=self.call('twin_system_context',dict(case_id=cid))
        self.assertEqual(state['latest']['recognition']['observation_sha256'],recorded['system_observation']['recognition']['observation_sha256'])
        self.assertEqual(self.client.get('/api/twin/cases/'+cid+'/systems',headers=read_only).status_code,404)
        self.assertEqual(self.client.get('/api/twin/cases/'+cid+'/systems',headers=self.headers).json,state)
        self.app.config['MAX_AGENT_REVISIONS']=10
        pid=self.call('twin_propose',dict(case_id=cid,payload=dict(base_version=0,kind='declared_model',text='Modelo sintético',structured={'model':fixture['model']})))['proposal']['id']
        self.call('twin_accept',dict(proposal_id=pid,payload=dict(base_version=0,confirmed=True,acknowledge_declared=True,idempotency_key='system-base-confirm')))
        args=dict(case_id=cid,base_version=1,text='Incluir afectados externos',scope=fixture['scope'])
        proposal=self.call('twin_propose_system_scope',args)['proposal']
        self.assertEqual(proposal['metadata']['system_scope']['unmapped_entities'],['neighbors'])
        self.call('twin_accept',dict(proposal_id=proposal['id'],payload=dict(base_version=1,confirmed=True,acknowledge_declared=True,idempotency_key='system-scope-confirm')))
        result=self.call('twin_evaluate',dict(case_id=cid,version=2))
        self.assertEqual(result['job']['status'],'completed',result)
        self.assertTrue(result['evaluation']['verification']['valid'])
        self.assertEqual(result['evaluation']['recommendation_status'],'SUSPENDED_PENDING_MODEL_REVIEW')
        self.assertEqual(self.call('twin_export',{'case_id':cid})['dossier']['system_observations'][0],recorded['system_observation'])
        self.app.config['MAX_AGENT_REVISIONS']=0
        self.assertEqual(self.rpc('twin_propose_system_scope',dict(args,base_version=2)).json['result']['structuredContent']['error']['code'],'proposal_limit')
        self.assertEqual(self.client.delete('/api/agents/me',headers=self.headers).status_code,204)
        self.assertEqual(self.client.get('/api/twin/cases/'+cid+'/systems',headers=self.headers).status_code,401)


if __name__ == '__main__':
    unittest.main()
