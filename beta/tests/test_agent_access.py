"""Public discovery must not weaken private API boundaries or fabricate identity."""
import json
from pathlib import Path
import re
import tempfile
import unittest
from genius_beta.app import create_app
from genius_beta.worker import Worker


class AgentAccessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.config = dict(DATA_DIR=root, DATABASE=root/'db.sqlite3',
            SUSPEND_FILE=root/'SUSPENDED', PUBLIC_URL='http://localhost',
            ENV='development', REGISTRATION_OPEN=True, TESTING=True)
        self.app = create_app(self.config)
        self.owner = self.app.test_client()
        self.agent = self.app.test_client(use_cookies=False)

    def tearDown(self):
        self.temp.cleanup()

    def token(self):
        response = self.owner.post('/api/register', json=dict(username='agent_owner',
            password='Synthetic-test-only-123!', privacy_accepted=True,
            privacy_version=self.app.config['PRIVACY_VERSION'], adult_confirmed=True))
        self.assertEqual(response.status_code, 201)
        csrf = response.json['csrf_token']
        response = self.owner.post('/api/tokens', json={'label':'Synthetic agent'},
                                   headers={'X-CSRF-Token':csrf})
        self.assertEqual(response.status_code, 201)
        return response.json, csrf

    def test_public_discovery_works_without_credentials_even_when_suspended(self):
        token, _ = self.token()
        self.config['SUSPEND_FILE'].touch()
        for path, content_type in [('/agents','text/html'),('/llms.txt','text/plain'),
                                  ('/openapi.json','application/vnd.oai.openapi+json')]:
            with self.agent.get(path) as response:
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.mimetype, content_type)
                text = response.get_data(as_text=True)
                self.assertNotIn(token['token'], text)
                self.assertNotIn('agent_owner', text)
                self.assertNotIn('Set-Cookie', response.headers)
                self.assertNotIn('X-Robots-Tag', response.headers)
        self.assertEqual(self.agent.get('/api/cases').status_code, 401)
        self.assertEqual(self.agent.get('/robots.txt').get_data(as_text=True),
                         'User-agent: *\nDisallow: /api/\n')
        self.assertEqual(self.agent.post('/agents', json={}).status_code, 405)

    def test_contract_references_routes_and_security_match_available_operations(self):
        with self.agent.get('/openapi.json') as response:
            spec = response.json
        routes = {(re.sub(r'<([^>]+)>', '{}', rule.rule), method)
                  for rule in self.app.url_map.iter_rules() for method in rule.methods}
        ids = []
        for path, item in spec['paths'].items():
            for method, operation in item.items():
                if method == 'parameters':
                    continue
                self.assertIn((re.sub(r'\{[^}]+\}', '{}', path), method.upper()), routes)
                ids.append(operation['operationId'])
                public = path in ('/api/config','/api/health','/api/examples/{name}',
                    '/agents/manifest.json','/api/agents/register','/api/agents/demo')
                self.assertEqual(operation.get('security', spec['security']),
                                 [] if public else [{'AccountBearer':[]}])
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(spec['x-genius-mcp-available'])
        self.assertEqual(spec['x-genius-credential-scope'],
            {'human':'full-account','automatic_agent':'enforced-scopes-and-expiry'})
        def check_refs(value):
            if isinstance(value, dict):
                if '$ref' in value:
                    target = spec
                    for key in value['$ref'].removeprefix('#/').split('/'):
                        target = target[key]
                for child in value.values():
                    check_refs(child)
            elif isinstance(value, list):
                for child in value:
                    check_refs(child)
        check_refs(spec)

    def test_documented_bearer_workflow_executes_with_isolation_and_revocation(self):
        token, csrf = self.token()
        headers = {'Authorization':'Bearer '+token['token']}
        self.assertEqual(self.agent.get('/api/me', headers=headers).status_code, 200)
        with self.agent.get('/api/examples/hours-known') as response:
            example = response.json
        profile = example.pop('profile')
        self.assertEqual(example['evidence_origin'], 'synthetic')
        response = self.agent.post('/api/cases', json=dict(title='Synthetic agent trial',
            profile=profile, consumer_type='agent', input=example), headers=headers)
        self.assertEqual(response.status_code, 201, response.json)
        case = response.json['case']
        response = self.agent.post('/api/cases/'+case['id']+'/run',
            json={'revision':case['current_revision']}, headers=headers)
        self.assertEqual(response.status_code, 202, response.json)
        job_id = response.json['job']['id']
        worker = Worker(self.config)
        try:
            worker.acquire()
            worker.run_once()
        finally:
            worker.close()
        response = self.agent.get('/api/jobs/'+job_id, headers=headers)
        self.assertEqual(response.status_code, 200)
        job = response.json['job']
        self.assertEqual(job['status'], 'completed', job)
        self.assertEqual(json.loads(job['result_json']), job['result'])
        with self.agent.get(job['artifacts']['url'], headers=headers) as archive:
            self.assertEqual(archive.status_code, 200)
        other = self.app.test_client()
        registration = other.post('/api/register', json=dict(username='other_owner',
            password='Synthetic-test-only-456!', privacy_accepted=True,
            privacy_version=self.app.config['PRIVACY_VERSION'], adult_confirmed=True))
        self.assertEqual(registration.status_code, 201)
        self.assertEqual(other.get('/api/cases/'+case['id']).status_code, 404)
        self.assertEqual(other.get('/api/jobs/'+job_id).status_code, 404)
        self.assertEqual(self.owner.delete('/api/tokens/'+token['id'],
            headers={'X-CSRF-Token':csrf}).status_code, 204)
        self.assertEqual(self.agent.get('/api/me', headers=headers).status_code, 401)
        self.assertEqual(self.agent.get('/api/jobs/'+job_id, headers=headers).status_code, 401)


if __name__ == '__main__':
    unittest.main()
