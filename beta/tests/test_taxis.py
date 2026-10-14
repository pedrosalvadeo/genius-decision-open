"""Public GET/MCP orientation must not mutate accounts, cases or execution budgets."""
import json
from pathlib import Path
import tempfile
import unittest
from urllib.robotparser import RobotFileParser
from genius_beta.app import create_app
from genius_beta.db import connect
from genius_beta.taxis import orient


class TaxisHTTPTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();root=Path(self.temp.name)
        self.config=dict(DATA_DIR=root,DATABASE=root/'db.sqlite3',SUSPEND_FILE=root/'SUSPENDED',
                         PUBLIC_URL='http://localhost',ENV='development',REGISTRATION_OPEN=True,TESTING=True)
        self.app=create_app(self.config);self.client=self.app.test_client(use_cookies=False)

    def tearDown(self):self.temp.cleanup()

    def call(self,arguments):
        return self.client.post('/mcp',json=dict(jsonrpc='2.0',id=1,method='tools/call',
            params=dict(name='find_opportunities',arguments=arguments)),
            headers={'Accept':'application/json, text/event-stream','MCP-Protocol-Version':'2025-11-25'})

    def test_get_mcp_and_local_agree_without_creating_accounts_or_jobs(self):
        expected=orient('mathematics',['lean'],'local')
        get=self.client.get('/agents/guide?goal=mathematics&capability=lean&access=local')
        self.assertEqual(get.status_code,200);self.assertEqual(get.json,expected)
        mcp=self.call(dict(goal='mathematics',capabilities=['lean'],access='local'))
        self.assertFalse(mcp.json['result']['isError'])
        self.assertEqual(mcp.json['result']['structuredContent'],expected)
        self.assertNotIn('Set-Cookie',get.headers)
        with connect(self.config['DATABASE']) as db:
            for table in ('users','cases','jobs'):
                self.assertEqual(db.execute('SELECT count(*) FROM '+table).fetchone()[0],0)

    def test_get_only_client_discovers_catalog_and_routes(self):
        r=self.client.get('/agents/opportunities.json')
        self.assertEqual(r.status_code,200);self.assertEqual(len(r.json['opportunities']),10);r.close()
        manifest=self.client.get('/agents/manifest.json').json
        self.assertEqual(manifest['orientation']['mcp_tool'],'find_opportunities')
        self.assertIn('find_opportunities',manifest['mcp']['public_tools'])
        robots=RobotFileParser();robots.parse(self.client.get('/robots.txt').text.splitlines())
        for path in ('/agents/guide','/agents/opportunities.json'):
            self.assertTrue(robots.can_fetch('*','http://localhost'+path))

    def test_bad_inputs_cannot_trigger_work_or_echo_arbitrary_query_data(self):
        for query in ('goal=other&secret=x','goal=use_engine&goal=mathematics','limit=NaN','capability=unknown','limit=999'):
            self.assertEqual(self.client.get('/agents/guide?'+query).status_code,400)
        for args in (dict(capabilities=[{}]),dict(limit=11),dict(capabilities=['python','python'])):
            response=self.call(args).json
            self.assertTrue(response.get('error') or response['result']['isError'])


if __name__=='__main__': unittest.main()
