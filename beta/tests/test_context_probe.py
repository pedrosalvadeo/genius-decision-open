"""The deploy probe crosses the real Flask API and isolated mission/native workers."""
import contextlib
import json
from pathlib import Path
import unittest
from unittest.mock import Mock
from deploy.context_probe import Probe
from genius_beta.db import connect
from genius_beta.app import create_app
import test_missions as fixture


class ContextProbe(unittest.TestCase):
    setUp=fixture.Missions.setUp
    work=fixture.Missions.work

    def test_lost_target_reply_resumes_then_closes_exports_and_erases(self):
        outer=self
        class LocalAPI:
            token=None
            lost=False
            def request(self,method,path,payload=None,accepted=(200,201,202,204)):
                headers={'Authorization':'Bearer '+self.token} if self.token else {}
                response=outer.client.open(path,method=method,headers=headers,json=payload)
                outer.assertIn(response.status_code,accepted,(path,response.json))
                if path.endswith('/run') and response.status_code==202:outer.work()
                if path.endswith('/context-forecast/observations') and not self.lost:
                    self.lost=True;raise RuntimeError('SIMULATED_RESPONSE_LOSS')
                return response.json if response.data else None
        api=LocalAPI();path=Path(self.tmp.name)/'private-probe.json'
        first=Probe(path,api=api)
        with self.assertRaisesRegex(RuntimeError,'SIMULATED_RESPONSE_LOSS'):first.run()
        token=api.token
        outer.client=create_app(self.config).test_client(use_cookies=False)
        resumed=Probe(path,api=api);resumed.run()
        self.assertEqual(resumed.state['status'],'PASS')
        self.assertTrue(resumed.state['account_erased']);self.assertTrue(resumed.state['credential_revoked'])
        self.assertNotIn('token',json.loads(path.read_text()))
        self.assertNotIn(token,json.dumps(resumed.public()))
        self.assertEqual(len(resumed.state['steps']['closed']['pairs']),15)
        self.assertEqual(outer.client.get('/api/missions',headers={'Authorization':'Bearer '+token}).status_code,401)
        with contextlib.closing(connect(self.config['DATABASE'])) as db:
            for table in ('adaptive_missions','mission_context_forecasts','mission_context_predictions','mission_context_observations'):
                self.assertEqual(db.execute('SELECT count(*) FROM '+table).fetchone()[0],0)
        resumed.run()  # completed private checkpoint cannot create another account
        self.assertEqual(resumed.state['status'],'PASS')

    def test_missing_deployment_preflight_does_not_create_an_account(self):
        api=Mock();api.token=None;api.request.return_value={'missions':{'enabled':True}}
        probe=Probe(Path(self.tmp.name)/'not-ready.json',api=api)
        with self.assertRaisesRegex(ValueError,'CONTEXT_API_NOT_DEPLOYED'):probe.run()
        self.assertFalse(probe.state.get('registration_attempted',False))
        self.assertEqual(api.request.call_count,1)


if __name__=='__main__':unittest.main()
