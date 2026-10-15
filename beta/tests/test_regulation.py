"""Feedback decisions, real mission execution, restart and bounded private memory."""
import contextlib
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import sqlite3
import tempfile
import subprocess
import sys
import time
import unittest
from unittest.mock import patch

import test_missions as fixture
from genius_beta import regulation as reg
from genius_beta.app import create_app
from genius_beta.config import settings
from genius_beta.db import connect, initialize, transaction, purge
from genius_beta.worker import Worker
from genius_beta.mission_worker import run_once


class Regulation(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        root=Path(self.tmp.name)
        self.config=settings(dict(DATA_DIR=root,DATABASE=root/'db.sqlite3',
            ADAPTIVE_ENABLED=True,MISSION_REGULATION_ENABLED=True))
        initialize(self.config['DATABASE'])
        self.db=connect(self.config['DATABASE']); self.addCleanup(self.db.close)
        self.now=int(time.time())
        self.signals=dict(storage_bytes=1000,free_bytes=1024**3,pending=0)
        sensor=patch.object(reg,'observe',side_effect=lambda *_:dict(self.signals))
        sensor.start(); self.addCleanup(sensor.stop)

    def sample(self, **signals):
        self.signals.update(signals)
        return reg.refresh(self.db,self.config,force=True,now=self.now)

    def attempt(self, outcome='failed', reason='MISSION_TIMEOUT'):
        with patch.object(reg.time,'time',return_value=self.now), transaction(self.db):
            state=self.sample()
            token=reg.begin(self.db,self.config,state)
            reg.finish(self.db,self.config,token,outcome,reason)
        return reg.load(self.db)

    def test_backlog_drains_without_stopping_accepted_work_and_uses_hysteresis(self):
        state=self.sample(pending=4)
        self.assertEqual(state['mode'],'DRAINING')
        self.assertFalse(reg.admits(state)); self.assertTrue(reg.starts(state))
        self.assertEqual(self.sample(pending=2)['mode'],'DRAINING')
        self.assertEqual(self.sample(pending=1)['mode'],'NORMAL')
        receipts=[json.loads(r[0]) for r in self.db.execute('SELECT receipt_json FROM mission_regulation_events')]
        recovery=receipts[-1]
        self.assertTrue(recovery['observed_recovery'])
        self.assertEqual(recovery['previous_signals']['pending'],2)
        self.assertEqual(recovery['signals']['pending'],1)

    def test_disk_pressure_and_free_space_have_separate_recovery_margins(self):
        limit=self.config['MAX_DATABASE_BYTES']; floor=self.config['MIN_FREE_BYTES']
        state=self.sample(storage_bytes=limit*86//100)
        self.assertEqual(state['mode'],'RESOURCE_PAUSED'); self.assertFalse(reg.starts(state))
        self.assertEqual(self.sample(storage_bytes=limit*80//100)['mode'],'RESOURCE_PAUSED')
        self.assertEqual(self.sample(storage_bytes=limit*69//100)['mode'],'NORMAL')
        self.assertEqual(self.sample(free_bytes=floor)['mode'],'RESOURCE_PAUSED')
        self.assertEqual(self.sample(free_bytes=floor+reg.POLICY['free_margin_bytes'])['mode'],'RESOURCE_PAUSED')
        self.assertEqual(self.sample(free_bytes=floor+2*reg.POLICY['free_margin_bytes'])['mode'],'NORMAL')

    def test_failure_cooldown_single_probe_and_measured_success(self):
        self.attempt(); self.attempt(); state=self.attempt()
        self.assertEqual(state['mode'],'COOLDOWN'); self.assertFalse(reg.starts(state))
        self.now+=reg.POLICY['cooldown_seconds']
        state=self.sample(); self.assertEqual(state['mode'],'PROBING')
        self.assertTrue(reg.admits(state))
        state=self.sample(pending=1); self.assertFalse(reg.admits(state))
        with patch.object(reg.time,'time',return_value=self.now), transaction(self.db):
            token=reg.begin(self.db,self.config,state)
            self.assertFalse(reg.starts(reg.load(self.db)))
            reg.finish(self.db,self.config,token,'completed',None)
            with self.assertRaisesRegex(RuntimeError,'IDENTITY_CHANGED'):
                reg.finish(self.db,self.config,token,'completed',None)
        self.assertEqual(reg.load(self.db)['mode'],'NORMAL')
        self.assertEqual(reg.load(self.db)['failures'],0)

    def test_failed_probe_waits_again_and_domain_rejections_are_neutral(self):
        self.attempt(); self.attempt(); self.attempt()
        self.now+=60
        state=self.attempt()
        self.assertEqual(state['mode'],'COOLDOWN')
        self.assertEqual(state['failures'],4)
        self.now+=60
        for outcome,reason in [('cancelled','CANCELLED'),('needs_review','STATE_OR_RUNTIME_REQUIRES_REVIEW'),('failed','MISSION_EXECUTION_FAILED')]:
            state=self.attempt(outcome,reason)
            self.assertEqual(state['failures'],4)
            self.assertEqual(state['mode'],'PROBING')

    def test_restart_preserves_cooldown_and_unknown_attempt_is_not_success(self):
        with transaction(self.db): reg.begin(self.db,self.config,self.sample())
        with contextlib.closing(connect(self.config['DATABASE'])) as reopened:
            reg.recover(reopened,self.config)
            state=reg.load(reopened)
            self.assertIsNone(state['active']); self.assertEqual(state['mode'],'COOLDOWN')
            until=state['cooldown_until']; reg.recover(reopened,self.config)
            self.assertEqual(reg.load(reopened)['cooldown_until'],until)
            self.assertEqual(reopened.execute("SELECT count(*) FROM mission_regulation_events WHERE kind='execution_interrupted'").fetchone()[0],1)

    def test_unavailable_sensor_clock_and_stale_status_never_claim_healthy(self):
        self.sample()
        with patch.object(reg,'observe',side_effect=OSError('private path')):
            state=self.sample()
        self.assertEqual(state['mode'],'SENSOR_PAUSED'); self.assertFalse(reg.starts(state))
        self.assertIsNone(state['signals'])
        self.now-=10; self.assertEqual(self.sample()['mode'],'SENSOR_PAUSED')
        self.now+=10; self.assertEqual(self.sample()['mode'],'NORMAL')
        with patch.object(reg.time,'time',return_value=self.now+16):
            self.assertEqual(reg.public_status(self.db,self.config)['mode'],'OBSERVATION_STALE')
        self.assertNotIn('private path',self.db.execute('SELECT group_concat(receipt_json) FROM mission_regulation_events').fetchone()[0])

    def test_disabled_or_changed_policy_cannot_silently_resume(self):
        state=self.sample()
        with transaction(self.db): state['policy_sha256']='different'; reg.save(self.db,state)
        self.assertEqual(self.sample()['mode'],'REVIEW_REQUIRED')
        self.assertFalse(reg.starts(self.sample()))
        self.assertEqual(reg.load(self.db)['policy_sha256'],'different')
        self.config['MISSION_REGULATION_ENABLED']=False
        self.assertTrue(reg.admits(self.sample()))
        self.assertEqual(reg.public_status(self.db,self.config)['mode'],'DISABLED')

    def test_observation_is_cached_while_idle_and_memory_is_bounded(self):
        self.sample()
        with patch.object(reg,'observe',side_effect=AssertionError('unnecessary resample')):
            reg.refresh(self.db,self.config,now=self.now+1)
        state=reg.load(self.db)
        with transaction(self.db):
            for i in range(520): reg.event(self.db,'test',state,self.now+i)
        self.assertEqual(self.db.execute('SELECT count(*) FROM mission_regulation_events').fetchone()[0],512)
        with transaction(self.db):reg.event(self.db,'test',state,self.now+8*86400)
        self.assertEqual(self.db.execute('SELECT count(*) FROM mission_regulation_events').fetchone()[0],1)


class RegulationAPI(unittest.TestCase):
    register=fixture.Missions.register
    create=fixture.Missions.create
    start=fixture.Missions.start
    get=fixture.Missions.get
    work=fixture.Missions.work

    def setUp(self):
        fixture.Missions.setUp(self)
        self.config['MISSION_REGULATION_ENABLED']=True
        self.app=create_app(self.config); self.client=self.app.test_client(use_cookies=False)

    def sensor(self, db, config):
        return dict(storage_bytes=1000,free_bytes=1024**3,
                    pending=db.execute("SELECT count(*) FROM adaptive_missions WHERE status IN ('queued','running')").fetchone()[0])

    def test_pressure_blocks_without_quota_and_retains_read_cancel_delete_and_replay(self):
        h=self.register(); mid,_=self.create(h)
        with patch.object(reg,'observe',return_value=dict(storage_bytes=10**9,free_bytes=0,pending=0)):
            blocked=self.client.post('/api/missions/'+mid+'/run',headers=h,json={})
        self.assertEqual(blocked.status_code,503); self.assertEqual(blocked.json['error']['code'],'mission_regulated')
        self.assertEqual(blocked.headers['Retry-After'],'5')
        with contextlib.closing(connect(self.config['DATABASE'])) as db:
            self.assertFalse(db.execute("SELECT 1 FROM counters WHERE key='missions-global'").fetchone())
            self.assertEqual(reg.load(db)['mode'],'RESOURCE_PAUSED')
        self.assertEqual(self.get(h,mid)['status'],'draft')
        self.assertEqual(self.client.get('/api/missions/'+mid+'/export',headers=h).status_code,200)
        with patch.object(reg,'observe',side_effect=self.sensor): self.start(h,mid)
        with patch.object(reg,'observe',side_effect=AssertionError('replay must not resample')):
            self.assertEqual(self.client.post('/api/missions/'+mid+'/run',headers=h,json={}).status_code,200)
        self.assertEqual(self.client.post('/api/missions/'+mid+'/cancel',headers=h,json={}).status_code,200)
        self.assertEqual(self.client.delete('/api/missions/'+mid,headers=h,json={'confirm':True}).status_code,204)

    def test_real_failures_pause_restart_then_one_real_success_recovers(self):
        h=self.register(); mids=[self.create(h)[0] for _ in range(3)]
        with patch.object(reg,'observe',side_effect=self.sensor):
            for mid in mids:
                self.start(h,mid)
                with patch('genius_beta.mission_worker.subprocess.Popen',side_effect=OSError('synthetic outage')):
                    self.work()
                self.assertEqual(self.get(h,mid)['error'],'MISSION_PROTOCOL_FAILED')
            other=self.register(); next_mid,_=self.create(other)
            self.assertEqual(self.client.post('/api/missions/'+next_mid+'/run',headers=other,json={}).status_code,503)
            w=Worker(self.config); w.acquire()
            try:self.assertFalse(run_once(w))
            finally:w.close()
            with contextlib.closing(connect(self.config['DATABASE'])) as db:
                until=reg.load(db)['cooldown_until']
            with patch.object(reg.time,'time',return_value=until):
                self.start(other,next_mid)
                second,_=self.create(other)
                self.assertEqual(self.client.post('/api/missions/'+second+'/run',headers=other,json={}).status_code,503)
                self.work()
                self.assertEqual(self.get(other,next_mid)['status'],'completed')
                self.assertEqual(self.client.get('/api/missions/regulation',headers=other).json['regulation']['mode'],'NORMAL')
                self.start(other,second)

    def test_mcp_scopes_and_health_expose_only_coarse_status(self):
        h=self.register(); writer=self.register(('missions:write',))
        self.assertEqual(self.client.get('/api/missions/regulation').status_code,401)
        self.assertEqual(self.client.get('/api/missions/regulation',headers=writer).status_code,403)
        response=self.client.get('/api/missions/regulation',headers=h)
        self.assertEqual(response.status_code,200)
        status=response.json['regulation']
        self.assertNotIn('signals',status); self.assertNotIn('active',status)
        self.assertEqual(self.client.get('/api/health').json['mission_regulation'],status)
        r=self.client.post('/mcp',headers={**h,'Accept':'application/json, text/event-stream','MCP-Protocol-Version':'2025-11-25'},json=dict(jsonrpc='2.0',id=1,method='tools/call',params=dict(name='mission_regulation',arguments={})))
        self.assertEqual(r.status_code,200,r.json)
        self.assertFalse(r.json.get('error'),r.json)
        self.assertIn('QUEUED_ADAPTIVE_MISSIONS',json.dumps(r.json))

    def test_suspension_and_disabled_control_never_lift_existing_guards(self):
        h=self.register(); mid,_=self.create(h)
        self.app.config['MISSION_REGULATION_ENABLED']=False
        Path(self.config['SUSPEND_FILE']).touch()
        self.assertEqual(self.client.post('/api/missions/'+mid+'/run',headers=h,json={}).status_code,503)
        self.assertEqual(self.client.get('/api/missions/'+mid,headers=h).status_code,200)
        w=Worker(self.config); w.acquire()
        try:self.assertFalse(run_once(w))
        finally:w.close()

    def test_concurrent_admission_stops_at_high_water_then_worker_drains(self):
        a=self.register(); b=self.register()
        first=[self.create(a)[0] for _ in range(3)]
        contenders=[self.create(b)[0] for _ in range(2)]
        with patch.object(reg,'observe',side_effect=self.sensor):
            for mid in first:self.start(a,mid)
            def submit(mid):
                with self.app.test_client(use_cookies=False) as client:
                    return client.post('/api/missions/'+mid+'/run',headers=b,json={}).status_code
            with ThreadPoolExecutor(max_workers=2) as pool:
                results=list(pool.map(submit,contenders))
            self.assertEqual(sorted(results),[202,503])
            with contextlib.closing(connect(self.config['DATABASE'])) as db:
                self.assertEqual(reg.load(db)['mode'],'DRAINING')
            # Already accepted missions proceed; admission resumes at low water.
            for _ in range(3):self.work()
            with contextlib.closing(connect(self.config['DATABASE'])) as db:
                self.assertEqual(reg.load(db)['mode'],'NORMAL')
                self.assertEqual(reg.load(db)['signals']['pending'],1)

    def test_killed_worker_waits_before_resuming_durable_mission(self):
        h=self.register(); mid,_=self.create(h); self.start(h,mid)
        code='''import os, signal, sys
from pathlib import Path
from genius_beta.worker import Worker
from genius_beta.mission_worker import run_once
r=Path(sys.argv[1]);w=Worker(dict(DATA_DIR=r,DATABASE=r/'genius.sqlite3',SUSPEND_FILE=r/'SUSPENDED',ADAPTIVE_ENABLED=True,MISSION_REGULATION_ENABLED=True))
w.acquire()
def hook(stage):
 if stage=='evaluate': os.kill(os.getpid(),signal.SIGKILL)
run_once(w,hook)
'''
        process=subprocess.run([sys.executable,'-c',code,str(self.config['DATA_DIR'])],timeout=60,capture_output=True)
        self.assertEqual(process.returncode,-9,process.stderr.decode())
        w=Worker(self.config); w.acquire()
        try:
            self.assertFalse(run_once(w))
            with contextlib.closing(connect(self.config['DATABASE'])) as db:
                state=reg.load(db); self.assertEqual(state['mode'],'COOLDOWN')
                self.assertEqual(db.execute('SELECT last_stage FROM adaptive_missions WHERE id=?',(mid,)).fetchone()[0],'evaluate')
            with patch.object(reg.time,'time',return_value=state['cooldown_until']):
                self.assertTrue(run_once(w))
                self.assertEqual(reg.load(w.db)['mode'],'NORMAL')
            self.assertEqual(self.get(h,mid)['status'],'completed')
            self.assertEqual(self.get(h,mid)['attempts'],2)
        finally:w.close()


if __name__=='__main__': unittest.main()
