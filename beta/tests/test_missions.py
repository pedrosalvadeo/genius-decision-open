"""Persistent service missions: real engine, restart, isolation and backup erasure."""
import base64
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import secrets
import signal
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
import zipfile
from genius_beta.app import create_app
from genius_beta.agent_access import POLICY_VERSION
from genius_beta.db import connect
from genius_beta.missions import SCOPES
from genius_beta.worker import Worker
from genius_beta.mission_worker import run_once
from genius_beta import r2_backup
from genius_beta.mission_state import unpack


class Missions(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        root=Path(self.tmp.name)
        self.config=dict(DATA_DIR=root,DATABASE=root/'genius.sqlite3',SUSPEND_FILE=root/'SUSPENDED',
            PUBLIC_URL='http://localhost',TESTING=True,REGISTRATION_OPEN=True,ADAPTIVE_ENABLED=True,
            MAX_AGENT_REGISTRATIONS_DAILY=30,MAX_AGENT_ACCOUNTS=30)
        env=patch.dict(os.environ,{'GENIUS_R2_BACKUP_ENABLED':'false'}); env.start(); self.addCleanup(env.stop)
        self.app=create_app(self.config);self.client=self.app.test_client(use_cookies=False);self.serial=0

    def register(self, scopes=SCOPES):
        self.serial+=1
        r=self.client.post('/api/agents/register',json=dict(policy_version=POLICY_VERSION,data_policy_acknowledged=True,scopes=[*scopes,'account:delete']),environ_overrides={'REMOTE_ADDR':'127.0.0.'+str(self.serial)})
        self.assertEqual(r.status_code,201,r.json)
        return {'Authorization':'Bearer '+r.json['credential']['token']}

    def create(self,h,**extra):
        data=dict(idempotency_key=secrets.token_hex(16),files={'hello.txt':'hello genius\n'*200},processing_permission=True,technical_scope_acknowledged=True,**extra)
        r=self.client.post('/api/missions',headers=h,json=data)
        self.assertEqual(r.status_code,201,r.json)
        return r.json['mission']['id'],data

    def start(self,h,mid):
        r=self.client.post('/api/missions/'+mid+'/run',headers=h,json={})
        self.assertEqual(r.status_code,202,r.json)

    def get(self,h,mid):
        return self.client.get('/api/missions/'+mid,headers=h).json['mission']

    def work(self,hook=None):
        w=Worker(self.config);w.acquire()
        try: self.assertTrue(run_once(w,hook))
        finally: w.close()

    def test_real_execution_completed_survives_restart_and_reuses(self):
        h=self.register();mid,_=self.create(h);self.start(h,mid);self.work()
        result=self.get(h,mid)
        self.assertEqual(result['status'],'completed',result)
        self.assertEqual(result['last_stage'],'remember')
        self.assertEqual(result['result']['memory']['kind'],'EMPIRICAL_SNAPSHOT_MEMORY')
        artifact=self.client.get('/api/missions/'+mid+'/artifact',headers=h).json
        raw=base64.b64decode(artifact['content_base64'])
        self.assertEqual(hashlib.sha256(raw).hexdigest(),artifact['sha256'])
        app=create_app(self.config); new=app.test_client(use_cookies=False)
        self.assertEqual(new.get('/api/missions/'+mid,headers=h).json['mission'],result)
        self.assertEqual(new.post('/api/missions/'+mid+'/run',headers=h,json={}).status_code,200)
        self.assertEqual(self.get(h,mid),result)
        with contextlib.closing(connect(self.config['DATABASE'])) as db:
            self.assertEqual(db.execute("SELECT count FROM counters WHERE key LIKE 'jobs-agent:%'").fetchone()[0],1)

    def test_worker_is_hard_killed_then_resumes_exact_measurements(self):
        h=self.register();mid,_=self.create(h);self.start(h,mid)
        code='''import os, signal, sys
from pathlib import Path
from genius_beta.worker import Worker
from genius_beta.mission_worker import run_once
r=Path(sys.argv[1]);w=Worker(dict(DATA_DIR=r,DATABASE=r/'genius.sqlite3',SUSPEND_FILE=r/'SUSPENDED',ADAPTIVE_ENABLED=True))
w.acquire()
def hook(stage):
 if stage=='evaluate': os.kill(os.getpid(),signal.SIGKILL)
run_once(w,hook)
'''
        p=subprocess.run([sys.executable,'-c',code,str(self.config['DATA_DIR'])],timeout=60,capture_output=True)
        self.assertEqual(p.returncode,-signal.SIGKILL,p.stderr.decode())
        with contextlib.closing(connect(self.config['DATABASE'])) as db:
            row=db.execute('SELECT * FROM adaptive_missions WHERE id=?',(mid,)).fetchone()
            self.assertEqual(row['last_stage'],'evaluate')
            old=Path(self.tmp.name)/'old';unpack(row['state_bundle'],row['state_sha256'],old)
        self.work()
        result=self.get(h,mid);self.assertEqual(result['status'],'completed',result)
        with contextlib.closing(connect(self.config['DATABASE'])) as db:
            row=db.execute('SELECT * FROM adaptive_missions WHERE id=?',(mid,)).fetchone()
            new=Path(self.tmp.name)/'new';unpack(row['state_bundle'],row['state_sha256'],new)
        for stage in ('measure','represent','evaluate'):
            self.assertEqual((old/'evidence'/f'{stage}.json').read_bytes(),(new/'evidence'/f'{stage}.json').read_bytes())
        self.assertEqual(result['attempts'],2)

    def test_scopes_ownership_idempotence_invalid_paths_and_feature_off(self):
        a=self.register();b=self.register();n=self.register(('missions:read',))
        mid,data=self.create(a);path='/api/missions/'+mid
        r=self.client.post('/api/missions',headers=a,json=data)
        self.assertEqual(r.status_code,200);self.assertEqual(r.json['mission']['id'],mid)
        self.assertEqual(self.client.post('/api/missions',headers=a,json={**data,'files':{'other':'x'}}).status_code,409)
        for suffix in ('','/export','/artifact'):
            self.assertEqual(self.client.get(path+suffix,headers=b).status_code,404)
        for suffix in ('/run','/cancel'):
            self.assertEqual(self.client.post(path+suffix,headers=b,json={}).status_code,404)
            self.assertEqual(self.client.post(path+suffix,headers=n,json={}).status_code,403)
        self.assertEqual(self.client.delete(path,headers=b,json={'confirm':True}).status_code,404)
        for files in ({'../secret':'x'},{'a':'x','a/b':'x'},{'.git/config':'x'},{'ok':'\ud800'}):
            self.assertEqual(self.client.post('/api/missions',headers=a,json={**data,'files':files}).status_code,400)
        self.app.config['ADAPTIVE_ENABLED']=False
        self.assertEqual(self.client.post(path+'/run',headers=a,json={}).status_code,503)
        self.assertEqual(self.client.get(path+'/export',headers=a).status_code,200)
        self.assertEqual(self.client.delete(path,headers=a,json={'confirm':True}).status_code,204)

    def test_cancel_and_delete_while_child_waits_cannot_resurrect(self):
        for operation in ('cancel','delete','account'):
            h=self.register();mid,_=self.create(h);self.start(h,mid)
            def hook(stage):
                if stage != 'measure': return
                if operation=='delete':
                    r=self.client.delete('/api/missions/'+mid,headers=h,json={'confirm':True})
                elif operation=='account':
                    r=self.client.delete('/api/agents/me',headers=h,json={})
                else:
                    r=self.client.post('/api/missions/'+mid+'/cancel',headers=h,json={})
                self.assertIn(r.status_code,(200,204),r.json)
            self.work(hook)
            with contextlib.closing(connect(self.config['DATABASE'])) as db:
                row=db.execute('SELECT status,artifact FROM adaptive_missions WHERE id=?',(mid,)).fetchone()
                if operation=='cancel': self.assertEqual(tuple(row),('cancelled',None))
                else: self.assertIsNone(row)

    def test_backup_restore_contains_checkpoint_and_respects_later_delete(self):
        helper=r2_backup.sqlite_backup()
        h=self.register();mid,_=self.create(h);self.start(h,mid)
        def hook(stage):
            if stage=='evaluate':
                # Snapshot while service state is active, before ACK.
                helper.snapshot(self.config['DATABASE'],Path(self.tmp.name)/'snapshot.sqlite3')
                raise ValueError('TEST_INTERRUPT')
        self.work(hook)
        saved=Path(self.tmp.name)/'snapshot.sqlite3'; restored=Path(self.tmp.name)/'restored.sqlite3'
        helper.restore(saved,restored,self.config['DATABASE'],services_stopped=True)
        with contextlib.closing(connect(restored)) as db:
            row=db.execute('SELECT * FROM adaptive_missions WHERE id=?',(mid,)).fetchone()
            self.assertEqual(row['status'],'interrupted');self.assertEqual(row['last_stage'],'evaluate')
            self.assertIsNotNone(row['state_bundle'])
            # Operator/API explicit retry, never automatic effects on restore.
            db.execute("UPDATE adaptive_missions SET status='queued' WHERE id=?",(mid,))
        config={**self.config,'DATABASE':restored}
        w=Worker(config);w.acquire()
        try:self.assertTrue(run_once(w))
        finally:w.close()
        with contextlib.closing(connect(restored)) as db:
            self.assertEqual(db.execute('SELECT status FROM adaptive_missions').fetchone()[0],'completed')
        self.assertEqual(self.client.delete('/api/missions/'+mid,headers=h,json={'confirm':True}).status_code,204)
        erased=Path(self.tmp.name)/'erased.sqlite3';helper.restore(saved,erased,self.config['DATABASE'],services_stopped=True)
        with contextlib.closing(connect(erased)) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM adaptive_missions').fetchone()[0],0)

    def test_bundle_rejects_traversal_and_bad_hash(self):
        output=io.BytesIO()
        with zipfile.ZipFile(output,'w') as z:z.writestr('../escape','x')
        raw=output.getvalue()
        for sha in ('bad',hashlib.sha256(raw).hexdigest()):
            with self.assertRaises(ValueError):unpack(raw,sha,Path(self.tmp.name)/secrets.token_hex(8))

    def test_mcp_scoped_discovery_and_execution(self):
        h=self.register();mid,_=self.create(h)
        headers={**h,'Content-Type':'application/json','Accept':'application/json, text/event-stream','MCP-Protocol-Version':'2025-11-25'}
        def rpc(method,params):return self.client.post('/mcp',headers=headers,json={'jsonrpc':'2.0','id':1,'method':method,'params':params})
        r=rpc('tools/list',{})
        self.assertEqual(r.status_code,200,r.json)
        self.assertIn('mission_run',[t['name'] for t in r.json['result']['tools']])
        r=rpc('tools/call',{'name':'mission_run','arguments':{'id':mid}})
        self.assertFalse(r.json['result']['isError'],r.json)
        self.assertEqual(self.get(h,mid)['status'],'queued')

    def test_quota_admission_and_retry_budget_are_durable(self):
        h=self.register();mid,_=self.create(h)
        for _ in range(2):self.create(h)
        r=self.client.post('/api/missions',headers=h,json=dict(idempotency_key=secrets.token_hex(16),files={'x':'x'},processing_permission=True,technical_scope_acknowledged=True))
        self.assertEqual(r.status_code,429)
        self.app.config['MAX_AGENT_JOBS_DAILY']=1
        self.start(h,mid)
        self.assertEqual(self.client.post('/api/missions/'+mid+'/run',headers=h,json={}).status_code,200)
        self.client.post('/api/missions/'+mid+'/cancel',headers=h,json={})
        self.assertEqual(self.client.post('/api/missions/'+mid+'/run',headers=h,json={}).status_code,429)
        with contextlib.closing(connect(self.config['DATABASE'])) as db:
            self.assertEqual(db.execute("SELECT count FROM counters WHERE key='missions-global'").fetchone()[0],1)
        other=self.register()
        self.app.config['MAX_DATABASE_BYTES']=1
        r=self.client.post('/api/missions',headers=other,json=dict(idempotency_key=secrets.token_hex(16),files={'x':'x'},processing_permission=True,technical_scope_acknowledged=True))
        self.assertEqual(r.status_code,503)
        # Read and erasure remain possible when storage admission is full.
        self.assertEqual(self.client.get('/api/missions',headers=h).status_code,200)

    def test_changed_runtime_needs_review_without_repeating_effect(self):
        from genius_beta.mission_state import pack,digest
        h=self.register();mid,_=self.create(h);self.start(h,mid)
        def interrupt(stage):
            if stage=='evaluate':raise ValueError('TEST_INTERRUPT')
        self.work(interrupt)
        with contextlib.closing(connect(self.config['DATABASE'])) as db:
            row=db.execute('SELECT * FROM adaptive_missions WHERE id=?',(mid,)).fetchone()
            folder=Path(self.tmp.name)/'mutated';unpack(row['state_bundle'],row['state_sha256'],folder)
            with sqlite3.connect(folder/'journal.sqlite3') as state:
                state.execute("UPDATE identity SET body='runtime changed'")
            raw=pack(folder)
            db.execute('UPDATE adaptive_missions SET state_bundle=?,state_sha256=? WHERE id=?',(raw,digest(raw),mid))
        self.start(h,mid);self.work()
        self.assertEqual(self.get(h,mid)['status'],'needs_review')
        self.assertEqual(self.client.post('/api/missions/'+mid+'/run',headers=h,json={}).status_code,409)
        self.assertEqual(self.client.get('/api/missions/'+mid+'/artifact',headers=h).status_code,409)

    def test_encrypted_volume_loss_restore_applies_remote_mission_erasure(self):
        from test_r2_backup import ObjectStore
        store,key=ObjectStore(),bytes(range(32))
        h=self.register();mid,_=self.create(h);self.start(h,mid);self.work()
        root=Path(self.tmp.name)
        receipt=r2_backup.backup_once(self.config['DATABASE'],root/'backup-status.json',store,key)
        r2_backup.record_deletions([(mid,'mission',int(time.time()))],store,key)
        output=root/'volume-restored'
        r2_backup.recover(store,key,receipt['object_key'],output,True)
        with contextlib.closing(connect(output/'genius.sqlite3')) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM adaptive_missions').fetchone()[0],0)
        self.assertTrue((output/'SUSPENDED').exists())

    def test_remote_erasure_failure_keeps_data_and_reports_failure(self):
        h=self.register();mid,_=self.create(h)
        with patch('genius_beta.r2_backup.record_deletions',side_effect=r2_backup.BackupError('SYNTHETIC_OFFLINE')):
            r=self.client.delete('/api/missions/'+mid,headers=h,json={'confirm':True})
        self.assertEqual(r.status_code,503,r.json)
        self.assertEqual(self.client.get('/api/missions/'+mid,headers=h).status_code,200)

    def calibration_payload(self, parent=None, offset=0):
        values = (90,100,110,100,105) if not parent else (110,115,120,115,120)
        rows=[dict(id=f'observation-{i}', value=value, observed_at=f'2026-01-{i+offset:02d}T12:00:00Z',source='Synthetic service test') for i,value in enumerate(values,1)]
        data=dict(kind='resource_calibration_v1',idempotency_key=secrets.token_hex(16),
            processing_permission=True,technical_scope_acknowledged=True,
            calibration=dict(context='Fixed water operation',resource='water',unit='millilitre',
                max_underprediction=10,data_kind='synthetic',training=rows[:3],validation=rows[3:]))
        if parent:data['parent_mission_id']=parent
        else:data['calibration']['baseline']=50
        return data

    def test_calibration_learning_continuation_and_private_lineage(self):
        h=self.register();other=self.register()
        data=self.calibration_payload()
        r=self.client.post('/api/missions',headers=h,json=data)
        self.assertEqual(r.status_code,201,r.json)
        mid=r.json['mission']['id'];self.start(h,mid);self.work()
        result=self.get(h,mid)
        self.assertEqual(result['status'],'completed',result)
        self.assertEqual(result['kind'],'resource_calibration_v1')
        self.assertEqual(result['result']['memory']['estimate'],100)
        data2=self.calibration_payload(mid,offset=5)
        self.assertEqual(self.client.post('/api/missions',headers=other,json=data2).status_code,404)
        for altered in (self.calibration_payload(mid),{**data2,'calibration':{**data2['calibration'],'unit':'hour'}},
                        {**data2,'calibration':{**data2['calibration'],'baseline':1}}):
            self.assertEqual(self.client.post('/api/missions',headers=h,json=altered).status_code,400)
        r=self.client.post('/api/missions',headers=h,json=data2)
        self.assertEqual(r.status_code,201,r.json)
        child=r.json['mission']['id']
        exported=self.client.get('/api/missions/'+child+'/export',headers=h).json['mission']['input']
        self.assertEqual(exported['calibration']['baseline'],100)
        self.assertEqual(exported['lineage']['mission_id'],mid)
        self.assertEqual(self.client.delete('/api/missions/'+mid,headers=h,json={'confirm':True}).status_code,204)
        # Idempotent retry survives deletion of parent; continuation is a frozen snapshot.
        r=self.client.post('/api/missions',headers=h,json=data2)
        self.assertEqual(r.status_code,200,r.json);self.assertEqual(r.json['mission']['id'],child)
        self.start(h,child);self.work()
        result=self.get(h,child);self.assertEqual(result['status'],'completed',result)
        self.assertEqual(result['result']['memory']['baseline'],100)
        self.assertEqual(result['result']['memory']['estimate'],115)
        self.assertEqual(self.client.get('/api/missions/'+child+'/export',headers=other).status_code,404)
        artifact=self.client.get('/api/missions/'+child+'/artifact',headers=h).json
        self.assertEqual(artifact['name'],'resource-estimate.json')
        raw=base64.b64decode(artifact['content_base64'])
        self.assertEqual(hashlib.sha256(raw).hexdigest(),artifact['sha256'])
        self.assertEqual(json.loads(raw)['prospective_validation'],'PENDING')
        self.assertEqual(self.client.delete('/api/agents/me',headers=h,json={}).status_code,204)
        with contextlib.closing(connect(self.config['DATABASE'])) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM adaptive_missions').fetchone()[0],0)

    def test_calibration_checkpoint_restore_and_erasure(self):
        h=self.register();data=self.calibration_payload()
        r=self.client.post('/api/missions',headers=h,json=data);self.assertEqual(r.status_code,201,r.json)
        mid=r.json['mission']['id'];self.start(h,mid)
        def interrupt(stage):
            if stage=='act':raise ValueError('TEST_INTERRUPT')
        self.work(interrupt)
        self.assertEqual(self.get(h,mid)['last_stage'],'act')
        self.start(h,mid);self.work()
        result=self.get(h,mid);self.assertEqual(result['status'],'completed',result)
        self.assertEqual(result['attempts'],2)
        helper=r2_backup.sqlite_backup();saved=Path(self.tmp.name)/'calibration-backup.sqlite3'
        helper.snapshot(self.config['DATABASE'],saved)
        self.assertEqual(self.client.delete('/api/missions/'+mid,headers=h,json={'confirm':True}).status_code,204)
        restored=Path(self.tmp.name)/'calibration-erased.sqlite3'
        helper.restore(saved,restored,self.config['DATABASE'],services_stopped=True)
        with contextlib.closing(connect(restored)) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM adaptive_missions').fetchone()[0],0)

    def test_calibration_contract_is_available_through_mcp(self):
        h=self.register()
        headers={**h,'Content-Type':'application/json','Accept':'application/json, text/event-stream','MCP-Protocol-Version':'2025-11-25'}
        r=self.client.post('/mcp',headers=headers,json={'jsonrpc':'2.0','id':1,'method':'tools/call',
            'params':{'name':'mission_create','arguments':{'payload':self.calibration_payload()}}})
        self.assertEqual(r.status_code,200,r.json)
        self.assertFalse(r.json['result']['isError'],r.json)
        caps=self.client.get('/api/missions/capabilities',headers=h).json
        self.assertIn('resource_calibration_v1',caps['kinds'])
        self.assertTrue(caps['learning']['parameter_updates'])
        self.assertFalse(caps['self_modification'])
