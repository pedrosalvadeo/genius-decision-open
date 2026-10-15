"""Offline real service/worker integration, with synthetic measurements only."""
import json
from pathlib import Path
import unittest
from unittest.mock import Mock
import test_missions as fixture
from observers import http_latency as source
from observers.study import Study


class Integration(unittest.TestCase):
    setUp = fixture.Missions.setUp
    work = fixture.Missions.work

    def test_lost_observation_response_resumes_same_sample_and_seals_before_learning(self):
        test=self
        class LocalAPI:
            token=None
            lost=False
            def request(self,method,path,payload=None,accepted=(200,201,202,204)):
                headers={'Authorization':'Bearer '+self.token} if self.token else {}
                response=test.client.open(path,method=method,headers=headers,json=payload)
                test.assertIn(response.status_code,accepted,response.json)
                if path.endswith('/run') and response.status_code==202:test.work()
                if path.endswith('/observations') and not self.lost:
                    self.lost=True
                    raise RuntimeError('SIMULATED_RESPONSE_LOSS')
                return response.json
        api=LocalAPI()
        values=iter((50,90,100,110,100,110,100,105,100,110,115,120,115,120))
        def measured(sample_id):
            start=source.utc_now();value=next(values)
            measurement=dict(id=sample_id,source_contract_sha256=source.digest(source.contract()),
                started_at=start,completed_at=source.utc_now(),outcome='OBSERVED',elapsed_ns=value*1000000,
                rounded_milliseconds=value)
            sha=source.digest(measurement)
            return dict(measurement=measurement,sha256=sha,observation=source.observation(measurement))
        sampler=Mock(side_effect=measured)
        path=Path(self.tmp.name)/'operator-private.json'
        study=Study(path,count=3,tolerance=10,api=api,sampler=sampler)
        with self.assertRaisesRegex(RuntimeError,'SIMULATED_RESPONSE_LOSS'):study.run()
        self.assertEqual(sampler.call_count,10)
        old=study.state['samples']['prospective-0']
        resumed=Study(path,count=3,tolerance=10,api=api,sampler=sampler)
        result=resumed.run()
        self.assertEqual(sampler.call_count,14)
        self.assertEqual(resumed.state['samples']['prospective-0'],old)
        self.assertEqual(result['steps']['report']['received_count'],3)
        self.assertEqual(result['steps']['report']['report']['outcome'],'NO_CONFIRMED_IMPROVEMENT')
        self.assertEqual(result['steps']['child_completed']['memory']['estimate'],115)
        self.assertTrue(result['old_report_unchanged'])
        token=api.token
        self.assertNotIn(token,json.dumps(result))
        resumed.cleanup()
        self.assertEqual(test.client.get('/api/missions',headers={'Authorization':'Bearer '+token}).status_code,401)
        again=Study(path,count=3,tolerance=10,api=api,sampler=sampler)
        again.run();again.cleanup();self.assertEqual(sampler.call_count,14)


if __name__=='__main__':unittest.main()
