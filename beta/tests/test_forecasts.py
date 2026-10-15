"""Prospective receipt order, fixed predictions, scored training and private recovery."""
import contextlib
import json
from pathlib import Path
import secrets
import sqlite3
import unittest
from unittest.mock import patch
import test_missions as missions_fixture
from genius_beta.app import create_app
from genius_beta.db import connect, purge
from genius_beta import mission_forecasts as forecasts, r2_backup

CLOCK = 1_792_040_000_000_000


class Forecasts(unittest.TestCase):
    setUp = missions_fixture.Missions.setUp
    register = missions_fixture.Missions.register
    calibration_payload = missions_fixture.Missions.calibration_payload
    start = missions_fixture.Missions.start
    work = missions_fixture.Missions.work
    get = missions_fixture.Missions.get

    def prepare(self):
        h=self.register()
        r=self.client.post('/api/missions',headers=h,json=self.calibration_payload())
        self.assertEqual(r.status_code,201,r.json)
        mid=r.json['mission']['id'];self.start(h,mid);self.work()
        result=self.get(h,mid);self.assertEqual(result['status'],'completed',result)
        return h,mid,result['artifact_sha256']

    def freeze(self,h,mid,artifact,count=3):
        with patch.object(forecasts,'now_us',return_value=CLOCK):
            r=self.client.post('/api/missions/'+mid+'/forecast',headers=h,json=dict(artifact_sha256=artifact,expected_count=count))
        self.assertEqual(r.status_code,201,r.json)
        return r.json['forecast']

    def record(self,index,value):
        return dict(id='new-'+str(index),value=value,observed_at=forecasts.iso(CLOCK+index*1_000_000),source='Synthetic test observation')

    def post(self,h,mid,frozen,index,value):
        payload=dict(forecast_sha256=frozen['sha256'],observation=self.record(index,value))
        with patch.object(forecasts,'now_us',return_value=CLOCK+index*10_000_000):
            r=self.client.post('/api/missions/'+mid+'/observations',headers=h,json=payload)
        self.assertEqual(r.status_code,201,r.json)
        return r,payload

    def training(self,mid):
        return dict(kind='resource_calibration_v1',forecast_mission_id=mid,idempotency_key=secrets.token_hex(16),
            processing_permission=True,technical_scope_acknowledged=True,
            calibration=dict(validation=[self.record(40,115),self.record(41,120)]))

    def test_fixed_forecast_scores_before_records_can_train_next_model(self):
        h,mid,artifact=self.prepare();frozen=self.freeze(h,mid,artifact)
        self.assertEqual(frozen['frozen']['estimate'],100)
        self.assertEqual(frozen['frozen']['frozen_at_us'],CLOCK)
        self.post(h,mid,frozen,1,110)
        self.assertEqual(self.client.post('/api/missions',headers=h,json=self.training(mid)).status_code,400)
        self.post(h,mid,frozen,2,115);self.post(h,mid,frozen,3,120)
        snapshot=self.client.get('/api/missions/'+mid+'/forecast',headers=h).json['forecast']
        self.assertEqual(snapshot['status'],'complete')
        self.assertEqual(snapshot['frozen'],frozen['frozen'])
        self.assertEqual(snapshot['report']['comparison']['baseline']['absolute_error_sum'],195)
        self.assertEqual(snapshot['report']['comparison']['estimate']['absolute_error_sum'],45)
        self.assertEqual(snapshot['report']['outcome'],'NO_CONFIRMED_IMPROVEMENT')  # tolerance 10, max underprediction 20
        self.assertFalse(snapshot['report']['model_changed'])
        self.assertEqual(snapshot['report']['data_kind'],'synthetic')
        for i,row in enumerate(snapshot['observations'],1):
            self.assertEqual(row['receipt']['received_at_us'],CLOCK+i*10_000_000)
            self.assertGreater(row['receipt']['received_at_us'],forecasts.event_us(row['receipt']['observation']['observed_at']))
        data=self.training(mid)
        r=self.client.post('/api/missions',headers=h,json=data);self.assertEqual(r.status_code,201,r.json)
        child=r.json['mission']['id']
        export=self.client.get('/api/missions/'+child+'/export',headers=h).json['mission']['input']
        self.assertEqual(export['calibration']['baseline'],100)
        self.assertEqual([row['value'] for row in export['calibration']['training']],[110,115,120])
        self.assertEqual(export['lineage']['report_sha256'],snapshot['report_sha256'])
        self.start(h,child);self.work()
        self.assertEqual(self.get(h,child)['result']['memory']['estimate'],115)
        self.assertEqual(self.client.get('/api/missions/'+mid+'/forecast',headers=h).json['forecast'],snapshot)
        self.assertEqual(self.get(h,mid)['artifact_sha256'],artifact)
        # Child is a frozen derivative; parent erasure does not break retry or alter its training.
        self.assertEqual(self.client.delete('/api/missions/'+mid,headers=h,json={'confirm':True}).status_code,204)
        self.assertEqual(self.client.post('/api/missions',headers=h,json=data).json['mission']['id'],child)

    def test_idempotence_and_seal_prevent_changes_or_extra_records(self):
        h,mid,artifact=self.prepare();frozen=self.freeze(h,mid,artifact)
        path='/api/missions/'+mid
        r=self.client.post(path+'/forecast',headers=h,json=dict(artifact_sha256=artifact,expected_count=3))
        self.assertEqual(r.status_code,200);self.assertEqual(r.json['forecast'],frozen)
        self.assertEqual(self.client.post(path+'/forecast',headers=h,json=dict(artifact_sha256=artifact,expected_count=4)).status_code,409)
        first,payload=self.post(h,mid,frozen,1,100)
        r=self.client.post(path+'/observations',headers=h,json=payload)
        self.assertEqual(r.status_code,200);self.assertEqual(r.json['observation'],first.json['observation'])
        changed={**payload,'observation':{**payload['observation'],'value':101}}
        self.assertEqual(self.client.post(path+'/observations',headers=h,json=changed).status_code,409)
        self.post(h,mid,frozen,2,100);self.post(h,mid,frozen,3,100)
        report=self.client.get(path+'/forecast',headers=h).json['forecast']['report']
        self.assertEqual(report['outcome'],'LOWER_ERROR_WITHIN_GUARDS')
        self.assertEqual(self.client.post(path+'/observations',headers=h,json=payload).status_code,200)
        self.assertEqual(self.client.post(path+'/observations',headers=h,json=dict(forecast_sha256=frozen['sha256'],observation=self.record(4,100))).status_code,409)

    def test_timestamps_fields_hash_and_clock_regression(self):
        h,mid,artifact=self.prepare();path='/api/missions/'+mid
        for count in (True,2,31):
            self.assertEqual(self.client.post(path+'/forecast',headers=h,json=dict(artifact_sha256=artifact,expected_count=count)).status_code,400)
        self.assertEqual(self.client.post(path+'/forecast',headers=h,json=dict(artifact_sha256='0'*64,expected_count=3)).status_code,409)
        frozen=self.freeze(h,mid,artifact)
        valid=dict(forecast_sha256=frozen['sha256'],observation=self.record(1,100))
        with patch.object(forecasts,'now_us',return_value=CLOCK+2_000_000):
            for change in ({'observed_at':forecasts.iso(CLOCK)}, {'observed_at':forecasts.iso(CLOCK+3_000_000)},
                           {'observed_at':'2026-10-15T00:00:00'}, {'source':''}, {'value':True}, {'value':-1}, {'received_at':'invented'}):
                r=self.client.post(path+'/observations',headers=h,json={**valid,'observation':{**valid['observation'],**change}})
                self.assertEqual(r.status_code,400,r.json)
            self.assertEqual(self.client.post(path+'/observations',headers=h,json={**valid,'forecast_sha256':'0'*64}).status_code,409)
        with patch.object(forecasts,'now_us',return_value=CLOCK):
            self.assertEqual(self.client.post(path+'/observations',headers=h,json=valid).status_code,503)
        self.assertEqual(self.client.get(path+'/forecast',headers=h).json['forecast']['received_count'],0)
        self.post(h,mid,frozen,1,100)
        with patch.object(forecasts,'now_us',return_value=CLOCK+20_000_000):
            old={**self.record(2,100),'observed_at':forecasts.iso(CLOCK+500_000)}
            self.assertEqual(self.client.post(path+'/observations',headers=h,json={**valid,'observation':old}).status_code,400)

        with patch.object(forecasts,'scorer_identity',return_value={'changed':True}):
            r=self.client.post(path+'/observations',headers=h,json={**valid,'observation':self.record(2,100)})
        self.assertEqual(r.status_code,409,r.json)
        self.assertEqual(r.json['error']['code'],'forecast_review_required')

    def test_tenant_scopes_export_and_feature_off(self):
        h,mid,artifact=self.prepare();other=self.register();reader=self.register(('missions:read',))
        frozen=self.freeze(h,mid,artifact);path='/api/missions/'+mid
        self.assertEqual(self.client.get(path+'/forecast',headers=other).status_code,404)
        self.assertEqual(self.client.post(path+'/forecast',headers=other,json=dict(artifact_sha256=artifact,expected_count=3)).status_code,404)
        payload=dict(forecast_sha256=frozen['sha256'],observation=self.record(1,100))
        self.assertEqual(self.client.post(path+'/observations',headers=other,json=payload).status_code,404)
        self.assertEqual(self.client.post(path+'/observations',headers=reader,json=payload).status_code,403)
        self.assertEqual(self.client.post('/api/missions',headers=other,json=self.training(mid)).status_code,404)
        exported=self.client.get(path+'/export',headers=h).json['mission']
        self.assertEqual(exported['forecast'],frozen)
        self.app.config['ADAPTIVE_ENABLED']=False
        self.assertEqual(self.client.post(path+'/observations',headers=h,json=payload).status_code,503)
        self.assertEqual(self.client.get(path+'/forecast',headers=h).status_code,200)
        self.assertEqual(self.client.delete(path,headers=h,json={'confirm':True}).status_code,204)
        with contextlib.closing(connect(self.config['DATABASE'])) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM mission_forecasts').fetchone()[0],0)

    def test_mcp_freeze_observe_and_disabled_discovery(self):
        h,mid,artifact=self.prepare()
        headers={**h,'Content-Type':'application/json','Accept':'application/json, text/event-stream','MCP-Protocol-Version':'2025-11-25'}
        def rpc(method,params):
            return self.client.post('/mcp',headers=headers,json={'jsonrpc':'2.0','id':1,'method':method,'params':params})
        with patch.object(forecasts,'now_us',return_value=CLOCK):
            r=rpc('tools/call',dict(name='mission_freeze',arguments=dict(id=mid,payload=dict(artifact_sha256=artifact,expected_count=3))))
        self.assertFalse(r.json['result']['isError'],r.json)
        frozen=self.client.get('/api/missions/'+mid+'/forecast',headers=h).json['forecast']
        with patch.object(forecasts,'now_us',return_value=CLOCK+2_000_000):
            r=rpc('tools/call',dict(name='mission_observe',arguments=dict(id=mid,payload=dict(forecast_sha256=frozen['sha256'],observation=self.record(1,100)))))
        self.assertFalse(r.json['result']['isError'],r.json)
        self.app.config['ADAPTIVE_ENABLED']=False
        names=[t['name'] for t in rpc('tools/list',{}).json['result']['tools']]
        self.assertIn('mission_forecast',names)
        self.assertNotIn('mission_freeze',names);self.assertNotIn('mission_observe',names)

    def test_restart_backup_and_remote_erasure_preserve_privacy(self):
        from test_r2_backup import ObjectStore
        h,mid,artifact=self.prepare();frozen=self.freeze(h,mid,artifact);self.post(h,mid,frozen,1,100)
        before=self.client.get('/api/missions/'+mid+'/forecast',headers=h).json
        new=create_app(self.config).test_client(use_cookies=False)
        self.assertEqual(new.get('/api/missions/'+mid+'/forecast',headers=h).json,before)
        store,key=ObjectStore(),bytes(range(32));root=Path(self.tmp.name)
        saved=r2_backup.backup_once(self.config['DATABASE'],root/'backup-status.json',store,key)
        restored=root/'restored-open-forecast'
        r2_backup.recover(store,key,saved['object_key'],restored,True)
        with contextlib.closing(connect(restored/'genius.sqlite3')) as db:
            self.assertEqual(forecasts.read(db,mid),before['forecast'])
        r2_backup.record_deletions([(mid,'mission',int(CLOCK//1_000_000))],store,key)
        erased=root/'restored-after-erasure'
        r2_backup.recover(store,key,saved['object_key'],erased,True)
        with contextlib.closing(connect(erased/'genius.sqlite3')) as db:
            for table in ('adaptive_missions','mission_forecasts','mission_forecast_observations'):
                self.assertEqual(db.execute('SELECT count(*) FROM '+table).fetchone()[0],0)

    def test_database_immutability_and_account_erasure(self):
        h,mid,artifact=self.prepare();frozen=self.freeze(h,mid,artifact)
        for i in range(1,4):self.post(h,mid,frozen,i,100)
        with contextlib.closing(connect(self.config['DATABASE'])) as db:
            for sql in ("UPDATE mission_forecasts SET frozen_json='{}'", "UPDATE mission_forecasts SET report_json='{}'",
                        "UPDATE mission_forecast_observations SET receipt_json='{}'"):
                with self.assertRaises(sqlite3.IntegrityError):db.execute(sql)
        self.assertEqual(self.client.delete('/api/agents/me',headers=h,json={}).status_code,204)
        with contextlib.closing(connect(self.config['DATABASE'])) as db:
            for table in ('mission_forecasts','mission_forecast_observations'):
                self.assertEqual(db.execute('SELECT count(*) FROM '+table).fetchone()[0],0)

    def test_retention_cascades_and_future_parent_cannot_freeze(self):
        h,mid,artifact=self.prepare()
        with patch.object(forecasts,'now_us',return_value=forecasts.event_us('2025-01-01T00:00:00Z')):
            r=self.client.post('/api/missions/'+mid+'/forecast',headers=h,json=dict(artifact_sha256=artifact,expected_count=3))
        self.assertEqual(r.status_code,400,r.json)
        frozen=self.freeze(h,mid,artifact);self.post(h,mid,frozen,1,100)
        with contextlib.closing(connect(self.config['DATABASE'])) as db:
            db.execute('UPDATE adaptive_missions SET updated_at=0 WHERE id=?',(mid,))
            purge(db)
            self.assertEqual(db.execute('SELECT count(*) FROM mission_forecasts').fetchone()[0],0)
            self.assertEqual(db.execute('SELECT count(*) FROM mission_forecast_observations').fetchone()[0],0)
