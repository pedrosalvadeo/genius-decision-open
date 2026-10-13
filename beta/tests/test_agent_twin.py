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


if __name__ == '__main__':
    unittest.main()
