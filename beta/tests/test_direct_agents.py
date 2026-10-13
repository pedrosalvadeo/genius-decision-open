"""Autonomous access: permission boundaries, budgets, expiry and human regression."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch
from genius_beta.app import create_app, digest, password_hash
from genius_beta.agent_access import POLICY_VERSION
from genius_beta.db import connect, initialize, purge
from genius_beta.worker import Worker


class DirectAgentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.config = dict(DATA_DIR=root,DATABASE=root/'db.sqlite3',SUSPEND_FILE=root/'SUSPENDED',
            PUBLIC_URL='http://localhost',ENV='development',REGISTRATION_OPEN=True,TESTING=True)
        self.app = create_app(self.config)
        self.client = self.app.test_client(use_cookies=False)

    def tearDown(self):
        self.temp.cleanup()

    def register(self, scopes=None, ip='127.0.0.1'):
        value = dict(policy_version=POLICY_VERSION,data_policy_acknowledged=True)
        if scopes is not None:
            value['scopes'] = scopes
        response = self.client.post('/api/agents/register',json=value,environ_base={'REMOTE_ADDR':ip})
        self.assertEqual(response.status_code,201,response.json)
        return response.json, {'Authorization':'Bearer '+response.json['credential']['token']}

    def case(self, headers):
        with self.client.get('/api/examples/hours-known') as response:
            payload = response.json
        profile = payload.pop('profile')
        response = self.client.post('/api/cases',json=dict(title='Synthetic trial',
            profile=profile,input=payload),headers=headers)
        self.assertEqual(response.status_code,201,response.json)
        self.assertEqual(response.json['case']['consumer_type'],'agent')
        return response.json['case']['id']

    def execute(self):
        worker = Worker(self.config)
        try:
            worker.acquire()
            return worker.run_once()
        finally:
            worker.close()

    def test_manifest_anonymous_registration_has_no_human_identity_or_consent(self):
        manifest = self.client.get('/agents/manifest.json')
        self.assertEqual(manifest.status_code,200)
        self.assertTrue(manifest.json['available'])
        response, headers = self.register()
        self.assertNotIn('Set-Cookie',self.client.get('/api/agents/me',headers=headers).headers)
        me = self.client.get('/api/agents/me',headers=headers).json
        self.assertEqual(me['agent']['id'],response['agent']['id'])
        with connect(self.config['DATABASE']) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM sessions').fetchone()[0],0)
            row = db.execute('SELECT * FROM consents').fetchone()
            self.assertEqual((row['research'],row['followup']),(0,0))
            self.assertEqual(db.execute('SELECT privacy_version FROM users').fetchone()[0],POLICY_VERSION)
            self.assertNotIn(response['credential']['token'],db.execute('SELECT token_hash FROM api_tokens').fetchone()[0])
        self.assertEqual(self.client.get('/api/agents/me',query_string={'token':response['credential']['token']}).status_code,401)

    def test_registration_rejects_personal_fields_false_ack_and_scope_escalation(self):
        base = dict(policy_version=POLICY_VERSION,data_policy_acknowledged=True)
        for extra in ({'email':'test@example.invalid'},{'adult_confirmed':True},
                      {'research_consent':True},{'password':'not-accepted'},
                      {'data_policy_acknowledged':'true'},{'scopes':['*']},
                      {'scopes':['cases:read','cases:read']},{'scopes':[]}):
            response = self.client.post('/api/agents/register',json={**base,**extra})
            self.assertEqual(response.status_code,400,response.json)
        self.assertEqual(self.client.post('/api/agents/register',json={**base,'policy_version':'old'}).status_code,409)
        with connect(self.config['DATABASE']) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM users').fetchone()[0],0)

    def test_machine_workflow_and_permission_denials(self):
        identity, headers = self.register()
        cid = self.case(headers)
        started = self.client.post('/api/cases/'+cid+'/run',json={},headers=headers)
        self.assertEqual(started.status_code,202,started.json)
        self.execute()
        result = self.client.get('/api/jobs/'+started.json['job']['id'],headers=headers).json['job']
        self.assertEqual(result['status'],'completed',result)
        self.assertEqual(json.loads(result['result_json']),result['result'])
        with self.client.get(result['artifacts']['url'],headers=headers) as archive:
            self.assertEqual(archive.status_code,200)
        for method,url,body in [('POST','/api/tokens',{'label':'escalate'}),
                ('GET','/api/tokens',None),('PATCH','/api/me',{'research_consent':True}),
                ('DELETE','/api/me',None),('POST','/api/cases/'+cid+'/feedback',{}),
                ('DELETE','/api/cases/'+cid,None)]:
            response = self.client.open(url,method=method,json=body,headers=headers)
            self.assertEqual(response.status_code,403,(method,url,response.json))
        login = self.client.post('/api/login',json=dict(username='agent_'+identity['agent']['id'],password='any-long-password'))
        self.assertEqual(login.status_code,401)
        with connect(self.config['DATABASE']) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM research_candidates').fetchone()[0],0)
        self.assertEqual(self.client.delete('/api/agents/me',headers=headers).status_code,204)
        self.assertEqual(self.client.get('/api/me',headers=headers).status_code,401)

    def test_scope_narrowing_rotation_and_revocation(self):
        _, headers = self.register()
        cid = self.case(headers)
        rotated = self.client.post('/api/agents/token',json={'scopes':['cases:read']},headers=headers)
        self.assertEqual(rotated.status_code,200,rotated.json)
        limited = {'Authorization':'Bearer '+rotated.json['credential']['token']}
        self.assertEqual(self.client.get('/api/agents/me',headers=headers).status_code,401)
        self.assertEqual(self.client.get('/api/cases/'+cid,headers=limited).status_code,200)
        self.assertEqual(self.client.head('/api/cases/'+cid,headers=limited).status_code,200)
        self.assertEqual(self.client.post('/api/cases/'+cid+'/run',json={},headers=limited).status_code,403)
        self.assertEqual(self.client.delete('/api/agents/me',headers=limited).status_code,403)
        self.assertEqual(self.client.post('/api/agents/token',json={'scopes':['cases:read','jobs:run']},headers=limited).status_code,400)
        self.assertEqual(self.client.delete('/api/agents/token',headers=limited).status_code,204)
        self.assertEqual(self.client.get('/api/me',headers=limited).status_code,401)

    def test_two_concurrent_rotations_cannot_duplicate_a_credential(self):
        _, headers = self.register()
        def rotate(_):
            return self.app.test_client(use_cookies=False).post('/api/agents/token',json={},headers=headers).status_code
        with ThreadPoolExecutor(max_workers=2) as pool:
            statuses = list(pool.map(rotate,range(2)))
        self.assertEqual(sorted(statuses),[200,401])
        with connect(self.config['DATABASE']) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM api_tokens').fetchone()[0],1)

    def test_expired_or_missing_grant_fails_closed(self):
        identity, headers = self.register()
        with connect(self.config['DATABASE']) as db:
            db.execute('UPDATE agent_token_grants SET expires_at=?',(int(time.time())-1,))
        self.assertEqual(self.client.get('/api/agents/me',headers=headers).status_code,401)
        self.assertEqual(self.client.post('/api/agents/token',json={},headers=headers).status_code,401)
        with connect(self.config['DATABASE']) as db:
            db.execute('DELETE FROM agent_token_grants')
        self.assertEqual(self.client.get('/api/cases',headers=headers).status_code,401)

    def test_demo_executes_only_fixed_synthetic_data_and_cannot_write_or_renew(self):
        for value in ({'example':'../../private'},{'example':'hours-known','input':{}},{'example':[]}):
            self.assertEqual(self.client.post('/api/agents/demo',json=value).status_code,400)
        response = self.client.post('/api/agents/demo',json={'example':'hours-known'})
        self.assertEqual(response.status_code,202,response.json)
        headers = {'Authorization':'Bearer '+response.json['credential']['token']}
        self.assertNotIn('Set-Cookie',response.headers)
        self.assertEqual(response.headers['Cache-Control'],'no-store')
        self.assertEqual(self.client.post('/api/cases',json={},headers=headers).status_code,403)
        self.assertEqual(self.client.post('/api/agents/token',json={},headers=headers).status_code,403)
        self.execute()
        job = self.client.get(response.json['poll_url'],headers=headers).json['job']
        self.assertEqual(job['status'],'completed',job)
        self.assertEqual(job['result']['evidence_origin'],'synthetic')
        self.assertEqual(self.client.get(response.json['poll_url']).status_code,401)
        self.assertEqual(self.client.delete('/api/agents/me',headers=headers).status_code,204)

    def test_accounts_and_demo_are_isolated_from_humans_and_each_other(self):
        _, a = self.register()
        _, b = self.register(ip='192.0.2.2')
        cid = self.case(a)
        self.assertEqual(self.client.get('/api/cases/'+cid,headers=b).status_code,404)
        self.assertEqual(self.client.patch('/api/cases/'+cid,json={'title':'changed'},headers=b).status_code,404)
        human = self.app.test_client()
        reg = human.post('/api/register',json=dict(username='human_user',password='Synthetic-human-123',
            privacy_accepted=True,privacy_version=self.app.config['PRIVACY_VERSION'],adult_confirmed=True))
        self.assertEqual(reg.status_code,201,reg.json)
        self.assertEqual(human.get('/api/cases/'+cid).status_code,404)
        self.assertEqual(human.get('/api/agents/me').status_code,403)
        self.assertEqual(human.post('/api/tokens',json={'label':'old path'},headers={'X-CSRF-Token':reg.json['csrf_token']}).status_code,201)
        self.assertEqual(self.client.get('/api/cases',headers=b).json['cases'],[])

    def test_demo_expiry_blocks_read_execution_and_purge_tracks_deletion(self):
        response = self.client.post('/api/agents/demo',json={'example':'hours-known'}).json
        headers = {'Authorization':'Bearer '+response['credential']['token']}
        with connect(self.config['DATABASE']) as db:
            db.execute('UPDATE agent_accounts SET expires_at=?',(int(time.time())-1,))
        self.assertEqual(self.client.get(response['poll_url'],headers=headers).status_code,401)
        self.assertFalse(self.execute())
        with connect(self.config['DATABASE']) as db:
            self.assertEqual(db.execute('SELECT status FROM jobs').fetchone()[0],'cancelled')
            purge(db)
            self.assertEqual(db.execute('SELECT count(*) FROM users').fetchone()[0],0)
            self.assertEqual(db.execute('SELECT count(*) FROM agent_token_grants').fetchone()[0],0)
            self.assertEqual(db.execute('SELECT entity_type FROM deletion_ledger').fetchone()[0],'user')

    def test_bootstrap_closing_suspension_and_backup_failure_preserve_reads(self):
        _, headers = self.register()
        body = dict(policy_version=POLICY_VERSION,data_policy_acknowledged=True)
        self.app.config['REGISTRATION_OPEN'] = False
        self.assertEqual(self.client.post('/api/agents/register',json=body).status_code,503)
        self.assertEqual(self.client.post('/api/agents/demo',json={'example':'hours-known'}).status_code,503)
        self.app.config['REGISTRATION_OPEN'] = True
        self.config['SUSPEND_FILE'].touch()
        self.assertFalse(self.client.get('/agents/manifest.json').json['available'])
        self.assertEqual(self.client.post('/api/agents/demo',json={'example':'hours-known'}).status_code,503)
        self.assertEqual(self.client.get('/api/agents/me',headers=headers).status_code,200)
        self.config['SUSPEND_FILE'].unlink()
        with patch('genius_beta.app.backup_enabled',return_value=True),patch('genius_beta.app.backup_health',return_value='stale'):
            self.assertFalse(self.client.get('/agents/manifest.json').json['available'])
            self.assertEqual(self.client.post('/api/agents/register',json=body).status_code,503)
        self.app.config['AGENT_ACCESS_ENABLED'] = False
        self.assertEqual(self.client.post('/api/cases',json={},headers=headers).status_code,503)
        self.assertEqual(self.client.delete('/api/agents/token',headers=headers).status_code,204)

    def test_global_job_budget_survives_account_deletion_and_new_bootstrap(self):
        self.app.config['MAX_AGENT_GLOBAL_JOBS_DAILY'] = 1
        identity, headers = self.register()
        cid = self.case(headers)
        self.assertEqual(self.client.post('/api/cases/'+cid+'/run',json={},headers=headers).status_code,202)
        self.assertEqual(self.client.delete('/api/agents/me',headers=headers).status_code,204)
        before = self.client.post('/api/agents/demo',json={'example':'hours-known'})
        self.assertEqual(before.status_code,429,before.json)
        with connect(self.config['DATABASE']) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM users').fetchone()[0],0)
            self.assertEqual(db.execute("SELECT count FROM counters WHERE key='jobs-agent-global'").fetchone()[0],1)

    def test_quota_and_capacity_denials_roll_back_demo_rows(self):
        self.app.config['MAX_AGENT_QUEUE'] = 1
        response = self.client.post('/api/agents/demo',json={'example':'hours-known'})
        self.assertEqual(response.status_code,202)
        second = self.client.post('/api/agents/demo',json={'example':'hours-known'})
        self.assertEqual(second.status_code,429,second.json)
        with connect(self.config['DATABASE']) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM agent_accounts').fetchone()[0],1)
            self.assertEqual(db.execute('SELECT count(*) FROM jobs').fetchone()[0],1)
        self.app.config['MAX_AGENT_ACCOUNTS'] = 1
        body = dict(policy_version=POLICY_VERSION,data_policy_acknowledged=True)
        self.assertEqual(self.client.post('/api/agents/register',json=body).status_code,429)

    def test_global_bootstrap_and_ip_limits_cannot_use_forwarded_header_to_reset(self):
        self.app.config['MAX_AGENT_REGISTRATIONS_DAILY'] = 2
        self.register(ip='192.0.2.1')
        self.register(ip='192.0.2.2')
        value = dict(policy_version=POLICY_VERSION,data_policy_acknowledged=True)
        denied = self.client.post('/api/agents/register',json=value,headers={'X-Forwarded-For':'192.0.2.3'})
        self.assertEqual(denied.status_code,429)
        self.app.config['MAX_AGENT_REGISTRATIONS_DAILY'] = 5
        self.register(ip='192.0.2.1')
        denied = self.client.post('/api/agents/register',json=value,environ_base={'REMOTE_ADDR':'192.0.2.1'},headers={'X-Forwarded-For':'192.0.2.4'})
        self.assertEqual(denied.status_code,429)

    def test_additive_migration_keeps_human_credentials_and_backup_token_deletion_cascades(self):
        # A separately received schema-v2 database upgrades without rewriting tables.
        path = Path(self.temp.name)/'old.sqlite3'
        source = Path(__file__).resolve().parents[1]/'migrations'
        with connect(path) as db:
            for name in ('001_initial.sql','002_artifacts.sql'):
                db.executescript((source/name).read_text())
            hashed = password_hash('Synthetic-preserved-123')
            db.execute('INSERT INTO users VALUES(?,?,?,?,?,?)',('human','preserved',hashed,1,1,'notice'))
            db.execute('INSERT INTO api_tokens VALUES(?,?,?,?,?,NULL)',('key','human',digest('old-key'),'old',1))
            # Mark exactly the historical migrations as already received.
            import hashlib
            db.execute('CREATE TABLE schema_migrations(version TEXT PRIMARY KEY,sha256 TEXT NOT NULL,applied_at INTEGER NOT NULL)')
            for name in ('001_initial.sql','002_artifacts.sql'):
                db.execute('INSERT INTO schema_migrations VALUES(?,?,1)',(name,hashlib.sha256((source/name).read_bytes()).hexdigest()))
        initialize(path)
        with connect(path) as db:
            self.assertEqual(db.execute('SELECT password_hash FROM users').fetchone()[0],hashed)
            self.assertEqual(db.execute('SELECT token_hash FROM api_tokens').fetchone()[0],digest('old-key'))
        self.register()
        with connect(self.config['DATABASE']) as db:
            db.execute('DELETE FROM api_tokens')  # Same operation as the offline restore path.
            self.assertEqual(db.execute('SELECT count(*) FROM agent_token_grants').fetchone()[0],0)


if __name__ == '__main__':
    unittest.main()
