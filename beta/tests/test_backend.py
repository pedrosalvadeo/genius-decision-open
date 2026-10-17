import base64
import io
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch
import zipfile
from genius_beta.adapter import fdq_verifier_available
from genius_beta.app import create_app
from genius_beta.db import connect, initialize, purge
from genius_beta.worker import Worker

BASE=Path(__file__).resolve().parents[1]


class BackendTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        data=Path(self.temp.name)
        self.config=dict(DATA_DIR=data,DATABASE=data/'genius.sqlite3',SUSPEND_FILE=data/'SUSPENDED',PUBLIC_URL='http://localhost',TESTING=True)
        self.app=create_app(self.config)
        self.a=self.app.test_client()
        self.b=self.app.test_client()
        self.ca=self.register(self.a,'alpha')
        self.cb=self.register(self.b,'bravo')

    def tearDown(self):
        self.temp.cleanup()

    def register(self,client,name):
        r=client.post('/api/register',json=dict(username=name,password='A-long-password-123',privacy_accepted=True,privacy_version=self.app.config['PRIVACY_VERSION'],adult_confirmed=True))
        self.assertEqual(r.status_code,201,r.json)
        return r.json['csrf_token']

    def post(self,url,value=None,client=None,csrf=None):
        return (client or self.a).post(url,json={} if value is None else value,headers={'X-CSRF-Token':csrf or self.ca})

    def case(self,client=None,csrf=None,example='hours-known'):
        payload=json.loads((BASE/'examples'/f'{example}.json').read_text())
        profile=payload.pop('profile')
        response=self.post('/api/cases',dict(title='Test',profile=profile,input=payload),client,csrf)
        self.assertEqual(response.status_code,201,response.json)
        return response.json['case']['id']

    def run_job(self,cid):
        response=self.post('/api/cases/'+cid+'/run')
        self.assertEqual(response.status_code,202,response.json)
        worker=Worker(self.config)
        try:
            worker.acquire()
            worker.run_once()
        finally:
            worker.close()
        job=self.a.get('/api/jobs/'+response.json['job']['id']).json['job']
        return job

    def test_real_hours_fdq_and_artifacts(self):
        for example in ('hours-known','hours-unknown','fdq-frontier','fdq-selector'):
            with self.subTest(example=example):
                cid=self.case(example=example)
                job=self.run_job(cid)
                if example.startswith('fdq') and not fdq_verifier_available():
                    self.assertEqual(job['status'],'failed',job)
                    self.assertEqual(job['admission'],{'reason':'FDQ_VERIFIER_NOT_IN_PUBLIC_EDITION','status':'rejected'})
                    continue
                self.assertEqual(job['status'],'completed',job)
                self.assertIn('response',job['result'])
                self.assertIn('presentation',job['result'])
                archive=self.a.get(job['artifacts']['url'])
                self.assertEqual(archive.status_code,200)
                with zipfile.ZipFile(io.BytesIO(archive.data)) as z:
                    self.assertIn('compilation.json',z.namelist())
                    self.assertTrue(any('HEAD' in n for n in z.namelist()))
                self.assertEqual(json.loads(job['result_json']),job['result'])
                repeated=self.post('/api/cases/'+cid+'/run')
                self.assertEqual(repeated.status_code,200)
                self.assertEqual(repeated.json['job']['id'],job['id'])

    def test_owner_isolation_all_objects_and_bearer_revocation(self):
        cid=self.case()
        jid=self.post('/api/cases/'+cid+'/run').json['job']['id']
        for method,url in [('get','/api/cases/'+cid),('delete','/api/cases/'+cid),('patch','/api/cases/'+cid),('get','/api/jobs/'+jid),('get','/api/jobs/'+jid+'/artifacts'),('post','/api/jobs/'+jid+'/cancel'),('post','/api/cases/'+cid+'/feedback')]:
            response=getattr(self.b,method)(url,json={},headers={'X-CSRF-Token':self.cb})
            self.assertEqual(response.status_code,404,(method,url,response.json))
        token=self.post('/api/tokens',{'label':'test'}).json
        external=self.app.test_client()
        headers={'Authorization':'Bearer '+token['token']}
        self.assertEqual(external.get('/api/cases',headers=headers).status_code,200)
        self.assertEqual(len(external.get('/api/cases',headers=headers).json['cases']),1)
        self.assertEqual(self.a.delete('/api/tokens/'+token['id'],headers={'X-CSRF-Token':self.ca}).status_code,204)
        self.assertEqual(external.get('/api/cases',headers=headers).status_code,401)
        with connect(self.config['DATABASE']) as db:
            raw=db.execute('SELECT password_hash FROM users').fetchone()[0]
            self.assertNotIn('A-long-password',raw)

    def test_csrf_origin_body_and_cookie(self):
        self.assertEqual(self.a.post('/api/tokens',json={'label':'x'}).status_code,403)
        self.assertEqual(self.a.post('/api/tokens',json={'label':'x'},headers={'X-CSRF-Token':self.ca,'Origin':'https://evil.test'}).status_code,403)
        self.assertEqual(self.a.post('/api/cases',data='x'*131073,headers={'Content-Type':'application/json','X-CSRF-Token':self.ca}).status_code,413)
        self.assertEqual(self.a.post('/api/tokens',data='{"label":"a","label":"b"}',headers={'Content-Type':'application/json','X-CSRF-Token':self.ca}).status_code,400)
        r=self.a.post('/api/login',json={'username':'alpha','password':'A-long-password-123'})
        self.assertIn('HttpOnly',r.headers['Set-Cookie'])
        self.assertIn('SameSite=Strict',r.headers['Set-Cookie'])
        self.assertNotIn('Access-Control-Allow-Origin',r.headers)

    def test_durable_revisions_restart_cancel_and_quota_after_delete(self):
        self.app.config['MAX_JOBS_DAILY']=1
        cid=self.case()
        detail=self.a.get('/api/cases/'+cid).json
        unchanged=self.a.patch('/api/cases/'+cid,json={'input':detail['revisions'][0]['input']},headers={'X-CSRF-Token':self.ca})
        self.assertEqual(unchanged.json['case']['current_revision'],1)
        first=self.post('/api/cases/'+cid+'/run').json['job']
        duplicate=self.post('/api/cases/'+cid+'/run')
        self.assertEqual(duplicate.json['job']['id'],first['id'])
        cancelled=self.post('/api/jobs/'+first['id']+'/cancel')
        self.assertEqual(cancelled.json['job']['status'],'cancelled')
        self.assertEqual(self.post('/api/cases/'+cid+'/run').status_code,409)
        app2=create_app(self.config)
        self.assertEqual(app2.test_client().get('/api/cases').status_code,401)
        self.a.delete('/api/cases/'+cid,headers={'X-CSRF-Token':self.ca})
        cid2=self.case()
        self.assertEqual(self.post('/api/cases/'+cid2+'/run').status_code,429)

    def test_worker_restart_marks_interrupted_and_single_worker(self):
        cid=self.case()
        jid=self.post('/api/cases/'+cid+'/run').json['job']['id']
        with connect(self.config['DATABASE']) as db:
            db.execute("UPDATE jobs SET status='running' WHERE id=?",(jid,))
        worker=Worker(self.config)
        worker.acquire()
        other=Worker(self.config)
        try:
            self.assertEqual(self.a.get('/api/jobs/'+jid).json['job']['status'],'interrupted')
            with self.assertRaises(RuntimeError):
                other.acquire()
        finally:
            worker.close()
            other.close()
        self.assertEqual(self.post('/api/cases/'+cid+'/run',{'retry':True}).status_code,202)

    def test_admission_reason_synthetic_separation_and_consent(self):
        cid=self.case()
        payload=json.loads((BASE/'examples'/'hours-known.json').read_text())
        payload.pop('profile')
        payload['assignments'][0]['credit']='-1'
        r=self.a.patch('/api/cases/'+cid,json={'input':payload},headers={'X-CSRF-Token':self.ca})
        self.assertEqual(r.status_code,200)
        job=self.run_job(cid)
        self.assertEqual(job['admission']['status'],'rejected',job)
        self.assertEqual(job['admission']['reason'],'HOURS_NONNEGATIVE_DECIMAL_OR_RATIONAL_REQUIRED')
        self.assertIsNone(job['result'])
        self.a.patch('/api/me',json={'research_consent':True},headers={'X-CSRF-Token':self.ca})
        cid2=self.case()
        self.assertEqual(self.run_job(cid2)['status'],'completed')
        self.assertEqual(self.a.get('/api/export').json['research_candidates'],[])
        payload=json.loads((BASE/'examples'/'hours-known.json').read_text())
        payload.pop('profile')
        payload['evidence_origin']='user_declared'
        self.a.patch('/api/cases/'+cid2,json={'input':payload},headers={'X-CSRF-Token':self.ca})
        self.assertEqual(self.run_job(cid2)['status'],'completed')
        self.assertEqual(len(self.a.get('/api/export').json['research_candidates']),1)
        self.a.patch('/api/me',json={'research_consent':False},headers={'X-CSRF-Token':self.ca})
        self.assertEqual(self.a.get('/api/export').json['research_candidates'],[])

    def test_research_includes_failed_cancelled_and_queued_without_backfill(self):
        cid=self.case()
        original=json.loads((BASE/'examples'/'hours-known.json').read_text())
        original.pop('profile')
        original['evidence_origin']='user_declared'
        original['assignments'][0]['credit']='-1'
        self.a.patch('/api/cases/'+cid,json={'input':original},headers={'X-CSRF-Token':self.ca})
        self.a.patch('/api/me',json={'research_consent':True},headers={'X-CSRF-Token':self.ca})
        failed=self.run_job(cid)
        self.assertEqual(failed['admission']['status'],'rejected')
        self.assertEqual(len(self.a.get('/api/export').json['research_candidates']),1)
        original['assignments'][0]['credit']='2'
        self.a.patch('/api/cases/'+cid,json={'input':original},headers={'X-CSRF-Token':self.ca})
        queued=self.post('/api/cases/'+cid+'/run').json['job']
        self.assertEqual(len(self.a.get('/api/export').json['research_candidates']),2)
        self.post('/api/jobs/'+queued['id']+'/cancel')
        candidates=self.a.get('/api/export').json['research_candidates']
        self.assertEqual(len(candidates),2)
        self.assertTrue(all(row['status']=='candidate_not_admitted' for row in candidates))
        self.a.patch('/api/me',json={'research_consent':False},headers={'X-CSRF-Token':self.ca})
        self.a.patch('/api/me',json={'research_consent':True},headers={'X-CSRF-Token':self.ca})
        self.assertEqual(self.a.get('/api/export').json['research_candidates'],[])
        self.app.config['PRIVACY_VERSION']='new-unaccepted-version'
        original['assignments'][0]['credit']='3'
        self.a.patch('/api/cases/'+cid,json={'input':original},headers={'X-CSRF-Token':self.ca})
        self.assertEqual(self.post('/api/cases/'+cid+'/run').status_code,202)
        self.assertEqual(self.a.get('/api/export').json['research_candidates'],[])

    def test_delete_purge_export_no_secret_and_suspension(self):
        cid=self.case()
        job=self.run_job(cid)
        content=self.a.get('/api/export').data.decode()
        self.assertNotIn('password_hash',content)
        self.assertNotIn('csrf',content)
        self.config['SUSPEND_FILE'].touch()
        fresh=self.app.test_client()
        self.assertEqual(fresh.post('/api/login',json={'username':'alpha','password':'A-long-password-123'}).status_code,200)
        self.assertEqual(self.post('/api/cases',{}).status_code,503)
        self.assertEqual(self.a.delete('/api/cases/'+cid,headers={'X-CSRF-Token':self.ca}).status_code,204)
        with connect(self.config['DATABASE']) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM artifacts').fetchone()[0],0)
            self.assertEqual(db.execute('SELECT count(*) FROM deletion_ledger').fetchone()[0],1)
            result=purge(db,90,now=int(time.time())+91*86400)
            self.assertEqual(result['users'],2)
            self.assertEqual(db.execute('SELECT count(*) FROM sessions').fetchone()[0],0)

    def test_storage_capacity_and_production_guard(self):
        self.app.config['MAX_DATABASE_BYTES']=1
        self.assertEqual(self.post('/api/cases',{}).status_code,503)
        with self.assertRaises(ValueError):
            create_app(dict(self.config,ENV='production'))
        secure=create_app(dict(self.config,ENV='production',PUBLIC_URL='https://beta.example',PRIVACY_CONTROLLER='Example',PRIVACY_ADDRESS='Example address',PRIVACY_CONTACT='contact@example.invalid'))
        r=secure.test_client().post('/api/login',json={'username':'alpha','password':'A-long-password-123'})
        self.assertIn('Secure',r.headers['Set-Cookie'])

    def test_timeout_and_cancellation_no_result(self):
        cid=self.case()
        jid=self.post('/api/cases/'+cid+'/run').json['job']['id']
        worker=Worker(dict(self.config,ENGINE_TIMEOUT=0))
        worker.acquire()
        try:
            worker.run_once()
        finally:
            worker.close()
        job=self.a.get('/api/jobs/'+jid).json['job']
        self.assertEqual(job['error'],'execution_timeout')
        self.assertIsNone(job['result'])
        self.assertEqual(list((self.config['DATA_DIR']/'tmp').iterdir()),[])

    def test_deletion_ledger_retention_matches_backup_horizon(self):
        now=int(time.time())
        with connect(self.config['DATABASE']) as db:
            db.execute('INSERT INTO deletion_ledger VALUES(?,?,?)',('old','case',now-8*86400))
            db.execute('INSERT INTO deletion_ledger VALUES(?,?,?)',('recent','user',now-6*86400))
            db.execute('INSERT INTO deletion_ledger VALUES(?,?,?)',('boundary','case',now-7*86400))
            purge(db,90,now=now)
            remaining={r[0] for r in db.execute('SELECT id FROM deletion_ledger')}
            self.assertEqual(remaining,{'recent','boundary'})

    def test_migration_tamper_detected(self):
        with connect(self.config['DATABASE']) as db:
            db.execute("UPDATE schema_migrations SET sha256='changed' WHERE version='001_initial.sql'")
        with self.assertRaises(RuntimeError):
            initialize(self.config['DATABASE'])


if __name__=='__main__':
    unittest.main()
