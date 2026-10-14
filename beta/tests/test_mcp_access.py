"""Real queue execution, protocol failures and authorization boundaries for MCP."""
import hashlib
import json
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from urllib.robotparser import RobotFileParser
from genius_beta.app import create_app
from genius_beta.db import connect
from genius_beta.worker import Worker
from genius_beta.r2_backup import BackupError


class MCPAccessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.config = dict(DATA_DIR=root,DATABASE=root/'db.sqlite3',SUSPEND_FILE=root/'SUSPENDED',
            PUBLIC_URL='http://localhost',ENV='development',REGISTRATION_OPEN=True,TESTING=True,MCP_DEMO_WAIT_SECONDS=1)
        self.app = create_app(self.config)
        self.client = self.app.test_client(use_cookies=False)

    def tearDown(self):
        self.temp.cleanup()

    def rpc(self,method,params=None,auth='',version='2025-11-25',extra=None):
        headers={'Accept':'application/json, text/event-stream','MCP-Protocol-Version':version}
        value=dict(params or {})
        if version=='2026-07-28':
            value['_meta']={'io.modelcontextprotocol/protocolVersion':version,'io.modelcontextprotocol/clientCapabilities':{}}
            headers['Mcp-Method']=method
            if method=='tools/call':headers['Mcp-Name']=value.get('name','')
        if auth:headers['Authorization']=auth
        headers.update(extra or {})
        return self.client.post('/mcp',json={'jsonrpc':'2.0','id':1,'method':method,'params':value},headers=headers)

    def call(self,name,args=None,auth='',**kw):
        return self.rpc('tools/call',{'name':name,'arguments':args or {}},auth=auth,**kw)

    def register(self,scopes=None):
        data=dict(policy_version='agent-access-2026-10-06-v1',data_policy_acknowledged=True)
        if scopes is not None:data['scopes']=scopes
        r=self.client.post('/api/agents/register',json=data)
        self.assertEqual(r.status_code,201)
        return 'Bearer '+r.json['credential']['token']

    def payload(self):
        return json.loads((Path(__file__).resolve().parents[1]/'examples/hours-unknown.json').read_text())

    def create(self,auth):
        data=self.payload(); profile=data.pop('profile')
        r=self.call('create_case',dict(profile=profile,input=data,title='Synthetic MCP test'),auth)
        self.assertFalse(r.json['result']['isError'],r.json)
        return r.json['result']['structuredContent']['case']['id']

    def execute(self):
        w=Worker(self.config)
        try:w.acquire();w.run_once()
        finally:w.close()

    def with_worker(self,operation):
        stop=threading.Event(); errors=[]
        def work():
            w=Worker(self.config)
            try:
                w.acquire()
                while not stop.wait(.03):w.run_once()
            except Exception as exc: errors.append(type(exc).__name__)
            finally:w.close()
        thread=threading.Thread(target=work);thread.start()
        try:return operation()
        finally:
            stop.set();thread.join(5)
            self.assertFalse(thread.is_alive());self.assertEqual(errors,[])

    def test_saved_demo_is_get_readable_complete_and_does_not_create_users(self):
        r=self.client.get('/static/demo-result.json')
        self.assertEqual(r.status_code,200)
        self.assertNotIn('Set-Cookie',r.headers)
        self.assertNotIn('X-Robots-Tag',r.headers)
        parser=RobotFileParser();parser.parse(self.client.get('/robots.txt').text.splitlines())
        self.assertTrue(parser.can_fetch('*','http://localhost/static/demo-result.json'))
        self.assertFalse(parser.can_fetch('*','http://localhost/api/cases'))
        for record in r.json['records']:
            canonical=json.dumps(record['result'],ensure_ascii=False,sort_keys=True,separators=(',',':'))
            self.assertEqual(hashlib.sha256(canonical.encode()).hexdigest(),record['result_sha256'])
            response=record['result']['response']
            for key in ('transport','execution','evidence','decisions','quality','closure'):
                self.assertIn(key,response)
            self.assertEqual(record['result']['evidence_origin'],'synthetic')
            if record['example']=='hours-unknown':
                self.assertIn('PV_UNKNOWN',json.dumps(response))
                self.assertEqual(response['closure']['state'],'PC_WAITING_DEPENDENCY')
        with connect(self.config['DATABASE']) as db:self.assertEqual(db.execute('SELECT count(*) FROM users').fetchone()[0],0)
        r.close()

    def test_discovery_legacy_and_modern_no_sessions_or_cookies(self):
        for version in ('2025-03-26','2025-06-18','2025-11-25'):
            r=self.rpc('initialize',dict(protocolVersion=version,capabilities={},clientInfo={'name':'test','version':'1'}),version=version)
            self.assertEqual(r.json['result']['protocolVersion'],version)
            self.assertEqual(r.headers['Cache-Control'],'no-store')
            self.assertNotIn('Mcp-Session-Id',r.headers)
            self.assertNotIn('Set-Cookie',r.headers)
        r=self.rpc('server/discover',version='2026-07-28')
        self.assertEqual(r.json['result']['resultType'],'complete')
        tools=self.rpc('tools/list',version='2026-07-28').json['result']
        self.assertEqual(tools['cacheScope'],'private')
        self.assertEqual({t['name'] for t in tools['tools']},{'get_capabilities','find_opportunities','read_demo_result','run_demo','get_contribution_inbox','submit_contribution','get_contribution','club_capabilities','club_directory'})
        self.assertEqual(self.client.get('/mcp').status_code,405)
        self.assertEqual(self.client.delete('/mcp').status_code,405)
        self.assertEqual(self.client.post('/mcp',json={'jsonrpc':'2.0','method':'notifications/initialized'},headers={'Accept':'application/json,text/event-stream'}).status_code,202)

    def test_origins_headers_queries_invalid_json_and_size_are_rejected(self):
        for method in ('get','post','delete'):
            self.assertEqual(getattr(self.client,method)('/mcp',headers={'Origin':'https://evil.invalid'}).status_code,403)
        self.assertEqual(self.rpc('ping',extra={'Sec-Fetch-Site':'cross-site'}).status_code,403)
        self.assertEqual(self.rpc('ping',extra={'Accept':'text/html'}).status_code,406)
        self.assertEqual(self.client.post('/mcp?token=placeholder',json={}).status_code,400)
        headers={'Accept':'application/json,text/event-stream','Content-Type':'application/json'}
        for raw in ('{', '[]','{"jsonrpc":"2.0","jsonrpc":"2.0"}','{"jsonrpc":"2.0","id":true,"method":"ping"}'):
            self.assertEqual(self.client.post('/mcp',data=raw,headers=headers).status_code,400)
        self.assertEqual(self.client.post('/mcp',data='x'*140000,headers=headers).status_code,413)
        self.assertEqual(self.rpc('tools/list',version='2026-07-28',extra={'Mcp-Method':'tools/call'}).json['error']['code'],-32020)
        r=self.rpc('ping',version='2099-01-01')
        self.assertEqual(r.json['error']['code'],-32022)
        self.assertIn('2026-07-28',r.json['error']['data']['supported'])

    def test_anonymous_cannot_create_read_private_or_use_human_credentials(self):
        for name,args in [('list_cases',{}),('create_case',{'profile':'hours','input':{}}),('get_job',{'job_id':'a'*32})]:
            result=self.call(name,args).json['result']
            self.assertTrue(result['isError']);self.assertEqual(result['structuredContent']['error']['http_status'],401)
        self.assertEqual(self.rpc('tools/list',auth='Bearer gb_'+'a'*43).status_code,401)
        self.assertEqual(self.call('get_capabilities',{'token':'placeholder'}).json['error']['code'],-32602)
        with connect(self.config['DATABASE']) as db:self.assertEqual(db.execute('SELECT count(*) FROM users').fetchone()[0],0)

    def test_scoped_machine_flow_uses_real_worker_and_revokes_after_deletion(self):
        auth=self.register(['cases:read','cases:write','jobs:run','cases:delete','account:delete'])
        cid=self.create(auth)
        r=self.call('run_case',{'case_id':cid},auth).json['result']
        job=r['structuredContent']['job'];self.assertEqual(job['status'],'queued')
        self.execute()
        r=self.call('get_job',{'job_id':job['id']},auth).json['result']
        self.assertEqual(r['structuredContent']['job']['status'],'completed')
        self.assertIn('PV_UNKNOWN',json.dumps(r))
        self.assertNotIn(auth[7:],json.dumps(r))
        self.assertEqual(self.call('delete_case',{'case_id':cid},auth).json['error']['code'],-32602)
        self.assertFalse(self.call('delete_case',{'case_id':cid,'confirm':True},auth).json['result']['isError'])
        self.assertFalse(self.call('delete_agent_space',{'confirm':True},auth).json['result']['isError'])
        self.assertEqual(self.rpc('tools/list',auth=auth).status_code,401)

    def test_scope_filter_and_isolation_are_enforced_on_calls(self):
        owner=self.register();reader=self.register(['cases:read'])
        cid=self.create(owner)
        names={t['name'] for t in self.rpc('tools/list',auth=reader).json['result']['tools']}
        self.assertIn('get_case',names);self.assertNotIn('create_case',names)
        r=self.call('create_case',{'profile':'hours','input':{}},reader).json['result']
        self.assertEqual(r['structuredContent']['error']['http_status'],403)
        r=self.call('get_case',{'case_id':cid},reader).json['result']
        self.assertEqual(r['structuredContent']['error']['http_status'],404)
        self.assertEqual(self.call('get_case',{'case_id':'../../api/me'},owner).json['error']['code'],-32602)

    def test_invalid_expired_key_never_downgrades_to_public_access(self):
        auth=self.register()
        with connect(self.config['DATABASE']) as db:db.execute('UPDATE agent_token_grants SET expires_at=?',(int(time.time())-1,))
        self.assertEqual(self.call('read_demo_result',auth=auth).status_code,401)
        self.assertEqual(self.call('run_demo',auth='Bearer ga_'+'x'*43).status_code,401)
        with connect(self.config['DATABASE']) as db:self.assertEqual(db.execute('SELECT count(*) FROM jobs').fetchone()[0],0)

    def test_live_demo_is_synthetic_deleted_and_shares_rest_quota(self):
        self.app.config['MAX_AGENT_GLOBAL_JOBS_DAILY']=1
        r=self.with_worker(lambda:self.call('run_demo',{'example':'hours-unknown'})).json['result']
        self.assertFalse(r['isError'],r)
        result=r['structuredContent'];self.assertTrue(result['temporary_space_deleted'])
        self.assertEqual(result['result']['evidence_origin'],'synthetic')
        self.assertIn('PV_UNKNOWN',json.dumps(result))
        self.assertNotIn('credential',result)
        with connect(self.config['DATABASE']) as db:
            for table in ('users','api_tokens','jobs','research_candidates'):
                self.assertEqual(db.execute('SELECT count(*) FROM '+table).fetchone()[0],0)
            self.assertEqual(db.execute("SELECT count FROM counters WHERE key='jobs-agent-global'").fetchone()[0],1)
        self.assertEqual(self.client.post('/api/agents/demo',json={'example':'hours-known'}).status_code,429)

    def test_demo_timeout_cleans_queued_work_without_leaking_credential(self):
        r=self.call('run_demo').json['result']
        self.assertTrue(r['isError'])
        self.assertEqual(r['structuredContent']['error']['code'],'demo_wait_expired')
        with connect(self.config['DATABASE']) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM users').fetchone()[0],0)
            self.assertEqual(db.execute('SELECT count(*) FROM jobs').fetchone()[0],0)

    def test_durable_deletion_failure_is_not_reported_as_success(self):
        with patch('genius_beta.app.record_deletions',side_effect=BackupError('synthetic-failure')):
            r=self.with_worker(lambda:self.call('run_demo')).json['result']
        self.assertTrue(r['isError'])
        self.assertEqual(r['structuredContent']['error']['code'],'deletion_not_confirmed')
        self.assertNotIn('temporary_space_deleted',r['structuredContent'])
        with connect(self.config['DATABASE']) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM agent_accounts WHERE expires_at IS NOT NULL').fetchone()[0],1)

    def test_closures_backup_and_disable_flags_preserve_readable_receipt(self):
        auth=self.register();cid=self.create(auth)
        self.app.config['AGENT_ACCESS_ENABLED']=False
        self.assertFalse(self.call('get_case',{'case_id':cid},auth).json['result']['isError'])
        self.assertTrue(self.call('run_case',{'case_id':cid},auth).json['result']['isError'])
        self.assertTrue(self.call('run_demo').json['result']['isError'])
        self.assertFalse(self.call('delete_agent_space',{'confirm':True},auth).json['result']['isError'])
        self.app.config['AGENT_ACCESS_ENABLED']=True
        with patch('genius_beta.app.backup_enabled',return_value=True),patch('genius_beta.app.backup_health',return_value='stale'):
            self.assertTrue(self.call('run_demo').json['result']['isError'])
            self.assertFalse(self.call('read_demo_result').json['result']['isError'])
        self.config['SUSPEND_FILE'].touch()
        self.assertTrue(self.call('run_demo').json['result']['isError'])
        self.app.config['MCP_ENABLED']=False
        self.assertEqual(self.rpc('tools/list').status_code,503)
        with self.client.get('/static/demo-result.json') as response:
            self.assertEqual(response.status_code,200)

    def test_mcp_global_budget_and_forwarded_ip_do_not_bypass_limits(self):
        self.app.config['MAX_MCP_REQUESTS_DAILY']=1
        self.assertEqual(self.rpc('tools/list').status_code,200)
        self.assertEqual(self.rpc('tools/list',extra={'X-Forwarded-For':'192.0.2.2'}).status_code,429)
        with connect(self.config['DATABASE']) as db:self.assertEqual(db.execute('SELECT count(*) FROM users').fetchone()[0],0)


if __name__=='__main__':unittest.main()
