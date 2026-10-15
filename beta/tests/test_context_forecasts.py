"""Real API/worker/native process, scoped receipts, restart and backup boundaries."""
import contextlib
import fcntl
import json
from pathlib import Path
import sqlite3
import unittest
from unittest.mock import patch

import test_missions as fixture
from genius_beta.app import create_app
from genius_beta.db import connect, purge
from genius_beta import context_forecasts as cf, mission_forecasts, r2_backup
from genius_adaptive import contextual

CLOCK = 1_792_040_000_000_000


class ContextForecasts(unittest.TestCase):
    setUp = fixture.Missions.setUp
    register = fixture.Missions.register
    calibration_payload = fixture.Missions.calibration_payload
    start = fixture.Missions.start
    work = fixture.Missions.work
    get = fixture.Missions.get

    def prepare(self, scopes=fixture.SCOPES):
        h = self.register(scopes); payload = self.calibration_payload()
        payload['calibration']['max_underprediction'] = 50
        for row in payload['calibration']['training'] + payload['calibration']['validation']: row['value'] = 50
        r = self.client.post('/api/missions',headers=h,json=payload)
        self.assertEqual(r.status_code,201,r.json)
        mid = r.json['mission']['id']; self.start(h,mid); self.work()
        result = self.get(h,mid); self.assertEqual(result['status'],'completed',result)
        return h,mid,result['artifact_sha256']

    def path(self, mid, suffix=''):
        return '/api/missions/'+mid+'/context-forecast'+suffix

    def freeze(self, h, mid, artifact, count=12):
        data = dict(artifact_sha256=artifact,warmup_count=3,scored_count=count)
        with patch.object(cf,'now_us',return_value=CLOCK):
            r = self.client.post(self.path(mid),headers=h,json=data)
        self.assertEqual(r.status_code,201,r.json)
        return r.json['forecast']

    def predict(self, h, mid, frozen, index):
        data = dict(forecast_sha256=frozen['sha256'],prediction_id='sample-'+str(index))
        with patch.object(cf,'now_us',return_value=CLOCK+index*10000000):
            r = self.client.post(self.path(mid,'/predictions'),headers=h,json=data)
        self.assertEqual(r.status_code,201,r.json)
        return r.json['prediction'],data

    def observe(self, h, mid, frozen, prediction, value):
        at = prediction['receipt']['issued_at_us']
        data = dict(forecast_sha256=frozen['sha256'],prediction_sha256=prediction['sha256'],
            observation=dict(id=prediction['receipt']['prediction_id'],value=value,
                             observed_at=cf.iso(at+1000000),source='Synthetic integration target'))
        with patch.object(cf,'now_us',return_value=at+2000000):
            r = self.client.post(self.path(mid,'/observations'),headers=h,json=data)
        self.assertEqual(r.status_code,201,r.json)
        return r.json['observation'],data

    def fill(self, h, mid, frozen):
        values = ([10,100]*20)[:frozen['frozen']['warmup_count']+frozen['frozen']['scored_count']]
        for index,value in enumerate(values,1):
            predicted,_ = self.predict(h,mid,frozen,index)
            self.observe(h,mid,frozen,predicted,value)
        return values

    def close(self, h, mid, frozen):
        with patch.object(cf,'now_us',return_value=CLOCK+500000000):
            return self.client.post(self.path(mid,'/close'),headers=h,json=dict(forecast_sha256=frozen['sha256']))

    def test_past_only_policy_switches_and_native_close_scores_actual_predictions(self):
        h,mid,artifact = self.prepare(); frozen = self.freeze(h,mid,artifact)
        self.assertEqual(frozen['frozen']['baseline'],50)
        self.fill(h,mid,frozen)
        before = self.client.get(self.path(mid),headers=h).json['forecast']
        self.assertEqual(before['status'],'ready_to_close'); self.assertIsNone(before['report'])
        r = self.close(h,mid,frozen); self.assertEqual(r.status_code,201,r.json)
        final = r.json['forecast']; report = final['report']
        self.assertEqual(report['outcome'],'OBSERVED_GUARDED_IMPROVEMENT')
        self.assertTrue(report['native']['verification']['valid'])
        self.assertGreater(report['selected_counts']['context_median'],0)
        self.assertEqual(report['comparison']['adaptive']['count'],12)
        self.assertEqual(final['pairs'],before['pairs'])
        history = cf.history_of(final,verify=True)
        self.assertEqual(report['comparison']['adaptive']['absolute_error_sum'],
            sum(abs(row['predictions']['adaptive']-row['value']) for row in history[3:]))
        self.assertEqual(report['unit'],frozen['frozen']['unit'])
        self.assertEqual(report['data_kind'],'synthetic')
        self.assertEqual(report['wellbeing_effect'],'UNMEASURED')
        self.assertEqual(cf.fingerprint(report),final['report_sha256'])
        self.app.config['MAX_AGENT_JOBS_DAILY']=0
        repeat = self.close(h,mid,frozen)
        self.assertEqual(repeat.status_code,200); self.assertEqual(repeat.json['forecast'],final)

    def test_prediction_is_durable_before_target_and_retry_cannot_skip_or_change(self):
        h,mid,artifact=self.prepare();frozen=self.freeze(h,mid,artifact)
        pred,data=self.predict(h,mid,frozen,1)
        self.client=create_app(self.config).test_client(use_cookies=False)
        r=self.client.post(self.path(mid,'/predictions'),headers=h,json=data)
        self.assertEqual(r.status_code,200);self.assertEqual(r.json['prediction'],pred)
        self.assertEqual(self.client.get(self.path(mid),headers=h).json['forecast']['status'],'awaiting_observation')
        data['prediction_id']='skip'
        self.assertEqual(self.client.post(self.path(mid,'/predictions'),headers=h,json=data).status_code,409)
        observed,payload=self.observe(h,mid,frozen,pred,100)
        self.client=create_app(self.config).test_client(use_cookies=False)
        retry=self.client.post(self.path(mid,'/observations'),headers=h,json=payload)
        self.assertEqual(retry.status_code,200);self.assertEqual(retry.json['observation'],observed)
        payload['observation']['value']=101
        self.assertEqual(self.client.post(self.path(mid,'/observations'),headers=h,json=payload).status_code,409)
        self.assertEqual(self.close(h,mid,frozen).status_code,409)

    def test_fields_clock_and_observation_identity_validation(self):
        h,mid,artifact=self.prepare(); path=self.path(mid)
        for change in ({'warmup_count':True},{'warmup_count':2},{'scored_count':31},{'scored_count':5},{'surprise':1}):
            r=self.client.post(path,headers=h,json=dict(artifact_sha256=artifact,warmup_count=3,scored_count=6)|change)
            self.assertEqual(r.status_code,400,r.json)
        frozen=self.freeze(h,mid,artifact);pred,payload=self.predict(h,mid,frozen,1)
        at=pred['receipt']['issued_at_us']
        valid=dict(forecast_sha256=frozen['sha256'],prediction_sha256=pred['sha256'],
            observation=dict(id='sample-1',value=100,observed_at=cf.iso(at+1000000),source='synthetic'))
        with patch.object(cf,'now_us',return_value=at+2000000):
            for change in ({'observed_at':cf.iso(at)},{'observed_at':cf.iso(at+3000000)},
                           {'observed_at':'2026-10-15T00:00:00'},{'value':True},{'value':1000001},{'source':''}):
                r=self.client.post(path+'/observations',headers=h,json={**valid,'observation':valid['observation']|change})
                self.assertEqual(r.status_code,400,r.json)
            for change in ({'prediction_sha256':'0'*64},{'forecast_sha256':'0'*64},
                           {'observation':{**valid['observation'],'id':'other'}}):
                self.assertEqual(self.client.post(path+'/observations',headers=h,json=valid|change).status_code,409)
        with patch.object(cf,'now_us',return_value=at):
            self.assertEqual(self.client.post(path+'/observations',headers=h,json=valid).status_code,503)
        self.assertEqual(self.client.get(path,headers=h).json['forecast']['received_count'],0)

    def test_changed_evaluator_blocks_mutation_but_keeps_reads_and_exact_replays(self):
        h,mid,artifact=self.prepare();frozen=self.freeze(h,mid,artifact);pred,data=self.predict(h,mid,frozen,1)
        with patch.object(cf,'scorer_identity',return_value={'changed':True}):
            self.assertEqual(self.client.get(self.path(mid),headers=h).status_code,200)
            self.assertEqual(self.client.get('/api/missions/'+mid+'/export',headers=h).status_code,200)
            self.assertEqual(self.client.post(self.path(mid,'/predictions'),headers=h,json=data).status_code,200)
            obs=dict(forecast_sha256=frozen['sha256'],prediction_sha256=pred['sha256'],
                observation=dict(id='sample-1',value=5,observed_at=cf.iso(CLOCK+11000000),source='synthetic'))
            r=self.client.post(self.path(mid,'/observations'),headers=h,json=obs)
            self.assertEqual(r.status_code,409);self.assertEqual(r.json['error']['code'],'context_review_required')

    def test_tenant_scopes_exports_disable_and_immutable_database(self):
        h,mid,artifact=self.prepare((*fixture.SCOPES,'cases:read'));other=self.register();reader=self.register(('missions:read',))
        frozen=self.freeze(h,mid,artifact);pred,_=self.predict(h,mid,frozen,1);self.observe(h,mid,frozen,pred,50)
        self.assertEqual(self.client.get(self.path(mid),headers=other).status_code,404)
        self.assertEqual(self.client.post(self.path(mid,'/predictions'),headers=other,json=dict(forecast_sha256=frozen['sha256'],prediction_id='x')).status_code,404)
        self.assertEqual(self.client.post(self.path(mid,'/predictions'),headers=reader,json={}).status_code,403)
        writer=self.register(('missions:write',))
        self.assertEqual(self.close(writer,mid,frozen).status_code,403)
        self.assertIn('context_forecast',self.client.get('/api/missions/'+mid+'/export',headers=h).json['mission'])
        self.assertIn('context_forecast',self.client.get('/api/export',headers=h).json['missions'][0])
        with contextlib.closing(connect(self.config['DATABASE'])) as db:
            for table,field in (('mission_context_forecasts','frozen_json'),('mission_context_predictions','receipt_json'),('mission_context_observations','receipt_json')):
                with self.assertRaises(sqlite3.IntegrityError):db.execute('UPDATE '+table+" SET "+field+"='{}'")
        self.app.config['ADAPTIVE_ENABLED']=False
        self.assertEqual(self.client.get(self.path(mid),headers=h).status_code,200)
        self.assertEqual(self.client.post(self.path(mid,'/predictions'),headers=h,json={}).status_code,503)
        self.assertEqual(self.client.delete('/api/missions/'+mid,headers=h,json=dict(confirm=True)).status_code,204)
        with contextlib.closing(connect(self.config['DATABASE'])) as db:
            for table in ('mission_context_forecasts','mission_context_predictions','mission_context_observations'):
                self.assertEqual(db.execute('SELECT count(*) FROM '+table).fetchone()[0],0)

    def test_failed_native_close_preserves_data_and_retries_with_shared_quotas(self):
        h,mid,artifact=self.prepare();frozen=self.freeze(h,mid,artifact,count=6);self.fill(h,mid,frozen)
        before=self.client.get(self.path(mid),headers=h).json['forecast']
        folder=Path(self.tmp.name)/'twin-locks'
        with (folder/'compiler.lock').open('a+b') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            self.assertEqual(self.close(h,mid,frozen).status_code,429)
        with patch('genius_twin.process_runner.ProcessEvaluator.__call__',side_effect=TimeoutError()):
            self.assertEqual(self.close(h,mid,frozen).status_code,503)
        self.assertEqual(self.client.get(self.path(mid),headers=h).json['forecast'],before)
        self.app.config['MAX_AGENT_JOBS_DAILY']=2  # parent + failed native attempt already charged
        self.assertEqual(self.close(h,mid,frozen).status_code,429)
        self.app.config['MAX_AGENT_JOBS_DAILY']=10
        final=self.close(h,mid,frozen);self.assertEqual(final.status_code,201,final.json)
        with contextlib.closing(connect(self.config['DATABASE'])) as db:
            with self.assertRaises(sqlite3.IntegrityError):db.execute("UPDATE mission_context_forecasts SET report_json='{}'")

    def test_native_verification_disagreement_cannot_close(self):
        h,mid,artifact=self.prepare();frozen=self.freeze(h,mid,artifact,count=6);self.fill(h,mid,frozen)
        with patch('genius_twin.process_runner.ProcessEvaluator.__call__',return_value={'verification':{'valid':False}}):
            self.assertEqual(self.close(h,mid,frozen).status_code,503)
        self.assertIsNone(self.client.get(self.path(mid),headers=h).json['forecast']['report'])

    def test_full_plan_rejects_extra_targets_and_changed_freeze(self):
        h,mid,artifact=self.prepare();frozen=self.freeze(h,mid,artifact,count=6)
        data=dict(artifact_sha256=artifact,warmup_count=3,scored_count=6)
        self.assertEqual(self.client.post(self.path(mid),headers=h,json=data).json['forecast'],frozen)
        self.assertEqual(self.client.post(self.path(mid),headers=h,json={**data,'scored_count':7}).status_code,409)
        self.fill(h,mid,frozen)
        r=self.client.post(self.path(mid,'/predictions'),headers=h,json=dict(forecast_sha256=frozen['sha256'],prediction_id='extra'))
        self.assertEqual(r.status_code,409)
        self.assertEqual(self.client.get(self.path(mid),headers=h).json['forecast']['received_count'],9)

    def test_encrypted_restore_retains_pending_prediction_and_remote_erasure_cascades(self):
        from test_r2_backup import ObjectStore
        h,mid,artifact=self.prepare();frozen=self.freeze(h,mid,artifact);self.predict(h,mid,frozen,1)
        before=self.client.get(self.path(mid),headers=h).json['forecast']
        store,key=ObjectStore(),bytes(range(32));root=Path(self.tmp.name)
        saved=r2_backup.backup_once(self.config['DATABASE'],root/'status.json',store,key)
        restored=root/'restored';r2_backup.recover(store,key,saved['object_key'],restored,True)
        with contextlib.closing(connect(restored/'genius.sqlite3')) as db:self.assertEqual(cf.read(db,mid),before)
        r2_backup.record_deletions([(mid,'mission',CLOCK//1000000)],store,key)
        erased=root/'erased';r2_backup.recover(store,key,saved['object_key'],erased,True)
        with contextlib.closing(connect(erased/'genius.sqlite3')) as db:
            for table in ('mission_context_forecasts','mission_context_predictions','mission_context_observations'):
                self.assertEqual(db.execute('SELECT count(*) FROM '+table).fetchone()[0],0)

    def test_account_erasure_and_retention_remove_context_state(self):
        for remove_account in (False,True):
            h,mid,artifact=self.prepare();frozen=self.freeze(h,mid,artifact);self.predict(h,mid,frozen,1)
            if remove_account:self.assertEqual(self.client.delete('/api/agents/me',headers=h,json={}).status_code,204)
            with contextlib.closing(connect(self.config['DATABASE'])) as db:
                if not remove_account:
                    db.execute('UPDATE adaptive_missions SET updated_at=0 WHERE id=?',(mid,));purge(db)
                self.assertIsNone(cf.read(db,mid))

    def test_legacy_forecast_coexists_unchanged_and_future_parent_rejected(self):
        h,mid,artifact=self.prepare()
        with patch.object(cf,'now_us',return_value=0):
            self.assertEqual(self.client.post(self.path(mid),headers=h,json=dict(artifact_sha256=artifact,warmup_count=3,scored_count=6)).status_code,400)
        with patch.object(mission_forecasts,'now_us',return_value=CLOCK):
            old=self.client.post('/api/missions/'+mid+'/forecast',headers=h,json=dict(artifact_sha256=artifact,expected_count=3)).json['forecast']
        frozen=self.freeze(h,mid,artifact);self.predict(h,mid,frozen,1)
        self.assertEqual(self.client.get('/api/missions/'+mid+'/forecast',headers=h).json['forecast'],old)

    def test_mcp_context_binding_and_disabled_discovery(self):
        h,mid,artifact=self.prepare();headers={**h,'Content-Type':'application/json','Accept':'application/json, text/event-stream','MCP-Protocol-Version':'2025-11-25'}
        def rpc(method,params):
            return self.client.post('/mcp',headers=headers,json=dict(jsonrpc='2.0',id=1,method=method,params=params))
        with patch.object(cf,'now_us',return_value=CLOCK):
            r=rpc('tools/call',dict(name='mission_context_freeze',arguments=dict(id=mid,payload=dict(artifact_sha256=artifact,warmup_count=3,scored_count=6))))
        self.assertFalse(r.json['result']['isError'],r.json)
        frozen=self.client.get(self.path(mid),headers=h).json['forecast']
        with patch.object(cf,'now_us',return_value=CLOCK+10000000):
            r=rpc('tools/call',dict(name='mission_context_predict',arguments=dict(id=mid,payload=dict(forecast_sha256=frozen['sha256'],prediction_id='mcp-1'))))
        self.assertFalse(r.json['result']['isError'],r.json)
        self.app.config['ADAPTIVE_ENABLED']=False
        names=[t['name'] for t in rpc('tools/list',{}).json['result']['tools']]
        self.assertIn('mission_context_get',names)
        self.assertFalse(any(n in names for n in ('mission_context_freeze','mission_context_predict','mission_context_observe','mission_context_close')))

    def test_concurrent_predictions_cannot_create_two_outstanding_targets(self):
        from concurrent.futures import ThreadPoolExecutor
        h,mid,artifact=self.prepare();frozen=self.freeze(h,mid,artifact)
        def issue(name):
            client=self.app.test_client(use_cookies=False)
            return client.post(self.path(mid,'/predictions'),headers=h,
                json=dict(forecast_sha256=frozen['sha256'],prediction_id=name)).status_code
        with patch.object(cf,'now_us',return_value=CLOCK+10000000), ThreadPoolExecutor(max_workers=2) as pool:
            outcomes=list(pool.map(issue,('parallel-a','parallel-b')))
        self.assertEqual(sorted(outcomes),[201,409])
        self.assertEqual(len(self.client.get(self.path(mid),headers=h).json['forecast']['pairs']),1)

    def test_erasure_during_native_comparison_cannot_resurrect_the_mission(self):
        from genius_twin.process_runner import ProcessEvaluator
        h,mid,artifact=self.prepare();frozen=self.freeze(h,mid,artifact,count=6);self.fill(h,mid,frozen)
        original=ProcessEvaluator.__call__
        def erase_after_computing(evaluator, model):
            result=original(evaluator,model)
            with contextlib.closing(connect(self.config['DATABASE'])) as other:
                other.execute('DELETE FROM adaptive_missions WHERE id=?',(mid,))
            return result
        with patch.object(ProcessEvaluator,'__call__',erase_after_computing):
            self.assertEqual(self.close(h,mid,frozen).status_code,404)
        with contextlib.closing(connect(self.config['DATABASE'])) as db:self.assertIsNone(cf.read(db,mid))


if __name__=='__main__':unittest.main()
