"""Actual encryption/SQLite and adversarial transport fixtures; never real users."""
import base64
import contextlib
from datetime import datetime, timedelta, timezone
import io
import json
import os
from pathlib import Path
import shutil
import sqlite3
import tempfile
import time
import unittest
from unittest.mock import patch
import zipfile

from genius_beta import r2_backup as r2
from genius_beta.app import create_app
from genius_beta.db import initialize, purge


class ObjectStore:
    def __init__(self):
        self.objects = {}
        self.fail_put = self.fail_get = self.fail_list = False
        self.uploads = 0
    def put(self, key, path):
        if self.fail_put:
            raise r2.BackupError('R2_UPLOAD_FAILED')
        self.uploads += 1
        self.objects[key] = Path(path).read_bytes()
    def get(self, key, path, maximum=r2.MAX_OBJECT+128):
        if self.fail_get:
            raise r2.BackupError('R2_DOWNLOAD_FAILED')
        value = self.objects[key]
        if len(value) > maximum:
            raise r2.BackupError('DOWNLOAD_LIMIT')
        with open(path, 'xb') as file:
            file.write(value)
    def list(self, prefix):
        if self.fail_list:
            raise r2.BackupError('R2_LIST_FAILED')
        return [{'key': k, 'size': len(v)} for k,v in self.objects.items() if k.startswith(prefix)]


class R2Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.live = self.root/'volume'
        self.live.mkdir()
        self.db = self.live/'genius.sqlite3'
        initialize(self.db)
        self.status = self.live/'backup-status.json'
        self.key = os.urandom(32)
        self.store = ObjectStore()
        self.now = int(time.time())
        self.env = patch.dict(os.environ, {'GENIUS_R2_BACKUP_ENABLED': 'false'})
        self.env.start()
        self.addCleanup(self.env.stop)
    def seed(self):
        with contextlib.closing(sqlite3.connect(self.db)) as db:
            for user in ('kept', 'deleted'):
                db.execute('INSERT INTO users VALUES(?,?,?,?,?,?)', (user,user,'SYNTHETIC-only',self.now,self.now,'test'))
                db.execute('INSERT INTO consents VALUES(?,?,?,?)', (user,1,1,self.now))
                db.execute('INSERT INTO sessions VALUES(?,?,?,?)', (user,user,'synthetic-csrf',self.now+3600))
                db.execute('INSERT INTO api_tokens VALUES(?,?,?,?,?,?)', (user,user,user,'synthetic',self.now,None))
                db.execute('INSERT INTO cases VALUES(?,?,?,?,?,?,?,?)', (user,user,'synthetic','hours','synthetic',1,self.now,self.now))
                db.execute('INSERT INTO revisions VALUES(?,?,?,?,?)', (user,1,'{}','synthetic',self.now))
                db.execute('INSERT INTO jobs(id,case_id,revision,status,created_at) VALUES(?,?,?,?,?)', (user,user,1,'running',self.now))
            db.commit()
    def backup(self):
        return r2.backup_once(self.db, self.status, self.store, self.key)
    def test_received_schema_v2_backup_upgrades_offline_without_losing_humans(self):
        self.seed()
        with contextlib.closing(sqlite3.connect(self.db)) as db:
            db.executescript("DROP TABLE club_file_versions; DROP TABLE club_files; DROP TABLE club_members; DROP TABLE contribution_inbox; DROP TABLE agent_token_grants; DROP TABLE agent_accounts; DELETE FROM schema_migrations WHERE version >= '003_agent_access.sql';")
        receipt = self.backup()
        output = self.root/'recovered-old-schema'
        r2.recover(self.store,self.key,receipt['object_key'],output,True)
        with contextlib.closing(sqlite3.connect(output/'genius.sqlite3')) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM users').fetchone()[0],2)
            self.assertEqual(db.execute('SELECT count(*) FROM schema_migrations').fetchone()[0],5)
            self.assertEqual(db.execute('SELECT count(*) FROM agent_accounts').fetchone()[0],0)
            self.assertEqual(db.execute('SELECT count(*) FROM api_tokens').fetchone()[0],0)
        self.assertTrue((output/'SUSPENDED').exists())
    def test_pre_club_schema_v4_upgrades_without_changing_existing_data(self):
        self.seed()
        with contextlib.closing(sqlite3.connect(self.db)) as db:
            db.executescript("DROP TABLE club_file_versions; DROP TABLE club_files; DROP TABLE club_members; DELETE FROM schema_migrations WHERE version='005_club.sql';")
        receipt = self.backup()
        output = self.root/'recovered-pre-club'
        r2.recover(self.store,self.key,receipt['object_key'],output,True)
        with contextlib.closing(sqlite3.connect(output/'genius.sqlite3')) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM users').fetchone()[0],2)
            self.assertEqual(db.execute('SELECT count(*) FROM club_members').fetchone()[0],0)
            self.assertEqual(db.execute('SELECT count(*) FROM schema_migrations').fetchone()[0],5)
        self.assertTrue((output/'SUSPENDED').exists())
    def test_unknown_historical_migration_identity_is_not_auto_upgraded(self):
        self.seed()
        with contextlib.closing(sqlite3.connect(self.db)) as db:
            db.executescript("DROP TABLE club_file_versions; DROP TABLE club_files; DROP TABLE club_members; DROP TABLE contribution_inbox; DROP TABLE agent_token_grants; DROP TABLE agent_accounts; DELETE FROM schema_migrations WHERE version >= '003_agent_access.sql'; UPDATE schema_migrations SET sha256='unrecognized' WHERE version='001_initial.sql';")
        receipt = self.backup()
        output = self.root/'must-not-exist'
        with self.assertRaisesRegex(r2.BackupError,'RESTORE_SCHEMA_MISMATCH'):
            r2.recover(self.store,self.key,receipt['object_key'],output,True)
        self.assertFalse(output.exists())
    def test_agent_keys_and_expired_demos_do_not_return_after_recovery(self):
        self.seed()
        with contextlib.closing(sqlite3.connect(self.db)) as db:
            db.execute("INSERT INTO agent_accounts VALUES('kept','agent','test',?,NULL)",(self.now,))
            db.execute("INSERT INTO agent_accounts VALUES('deleted','demo','test',?,?)",(self.now-7200,self.now-3600))
            for tid in ('kept','deleted'):
                db.execute('INSERT INTO agent_token_grants VALUES(?,?,?)',(tid,'["cases:read"]',self.now+3600))
            db.commit()
        receipt = self.backup()
        output = self.root/'recovered-agents'
        r2.recover(self.store,self.key,receipt['object_key'],output,True)
        with contextlib.closing(sqlite3.connect(output/'genius.sqlite3')) as db:
            self.assertEqual(db.execute('SELECT id FROM users').fetchall(),[('kept',)])
            self.assertEqual(db.execute('SELECT count(*) FROM agent_token_grants').fetchone()[0],0)
            self.assertEqual(db.execute('SELECT count(*) FROM api_tokens').fetchone()[0],0)
            self.assertEqual(db.execute('SELECT research,followup FROM consents').fetchall(),[(0,0)])
    def test_volume_loss_recovers_from_remote_and_honors_later_deletions(self):
        self.seed()
        receipt = self.backup()
        r2.record_deletions([('deleted','user',self.now),('kept','case',self.now)], self.store, self.key)
        # No current DB, status file or live volume survives the simulated loss.
        shutil.rmtree(self.live)
        output = self.root/'recovered'
        result = r2.recover(self.store,self.key,receipt['object_key'],output,True)
        self.assertTrue(result['suspended'])
        self.assertTrue((output/'SUSPENDED').exists())
        with contextlib.closing(sqlite3.connect(output/'genius.sqlite3')) as db:
            self.assertEqual(db.execute('SELECT id FROM users').fetchall(), [('kept',)])
            self.assertEqual(db.execute('SELECT count(*) FROM cases').fetchone()[0], 0)
            self.assertEqual(db.execute('SELECT research,followup FROM consents').fetchall(), [(0,0)])
            for table in ('sessions','api_tokens','research_candidates','telemetry'):
                self.assertEqual(db.execute('SELECT count(*) FROM '+table).fetchone()[0], 0)
            self.assertEqual(db.execute('PRAGMA integrity_check').fetchone()[0], 'ok')
        self.assertEqual((output/'genius.sqlite3').stat().st_mode & 0o777, 0o600)
    def test_wrong_key_modified_ciphertext_role_replay_and_truncation_publish_nothing(self):
        source, encrypted = self.root/'plain', self.root/'encrypted'
        source.write_bytes(b'SYNTHETIC SECRET' * 100)
        object_key = 'snapshots/test.gcm'
        r2.seal(source, encrypted, self.key, object_key)
        original = encrypted.read_bytes()
        self.assertNotIn(b'SYNTHETIC SECRET', original)
        trials = [(original, os.urandom(32), object_key),
                  (original, self.key, 'privacy/test.gcm'),
                  (original[:-1], self.key, object_key),
                  (original[:-1] + bytes([original[-1]^1]), self.key, object_key)]
        for content,key,context in trials:
            encrypted.write_bytes(content)
            with self.assertRaises(r2.BackupError):
                r2.unseal(encrypted,self.root/'output',key,context)
            self.assertFalse((self.root/'output').exists())
            self.assertEqual(list(self.root.glob('.decrypt-*')), [])
    def test_success_roundtrip_schedule_and_secret_free_state(self):
        first = self.backup()
        self.assertTrue(first['roundtrip_verified'])
        count = self.store.uploads
        self.assertEqual(self.backup()['status'], 'not_due')
        self.assertEqual(count,self.store.uploads)
        with patch.dict(os.environ, {'GENIUS_R2_BACKUP_ENABLED':'true'}):
            self.assertEqual(r2.health(self.live),'ok')
        self.assertNotIn(base64.b64encode(self.key).decode(), self.status.read_text())
    def test_privacy_retry_does_not_renew_remote_retention(self):
        event=[('deleted','user',self.now)]
        r2.record_deletions(event,self.store,self.key)
        first=dict(self.store.objects)
        r2.record_deletions(event,self.store,self.key)
        self.assertEqual(self.store.uploads,1)
        self.assertEqual(self.store.objects,first)
    def test_upload_failure_reserves_budget_and_backoff_survives_restart(self):
        self.store.fail_put = True
        with self.assertRaisesRegex(r2.BackupError, 'R2_UPLOAD_FAILED'):
            self.backup()
        state = r2.read_state(self.status)
        self.assertGreater(state['uploaded_bytes_reserved'],0)
        self.assertEqual(state['status'],'failed')
        self.assertEqual(self.backup()['status'],'backoff')
        self.assertEqual(self.store.objects,{})
    def test_failed_download_never_claims_success(self):
        self.store.fail_get = True
        with self.assertRaisesRegex(r2.BackupError,'R2_DOWNLOAD_FAILED'):
            self.backup()
        self.assertEqual(r2.read_state(self.status)['status'],'failed')
        self.assertNotIn('last_success',r2.read_state(self.status))
    def test_monthly_budget_and_snapshot_backlog_stop_upload(self):
        r2.write_state(self.status,dict(month=datetime.now(timezone.utc).strftime('%Y-%m'),uploaded_bytes_reserved=r2.MAX_MONTHLY_UPLOAD))
        with self.assertRaisesRegex(r2.BackupError,'MONTHLY_UPLOAD_BUDGET'):
            self.backup()
        self.assertEqual(self.store.uploads,0)
        self.status.unlink()
        self.store.objects={f'snapshots/{i}.gcm':b'fixture' for i in range(8)}
        with self.assertRaisesRegex(r2.BackupError,'SNAPSHOT_RETENTION_BACKLOG'):
            self.backup()
        self.assertEqual(self.store.uploads,0)
    def test_privacy_listing_failure_blocks_restore_without_creating_output(self):
        receipt=self.backup()
        self.store.fail_list=True
        with self.assertRaisesRegex(r2.BackupError,'R2_LIST_FAILED'):
            r2.recover(self.store,self.key,receipt['object_key'],self.root/'restored',True)
        self.assertFalse((self.root/'restored').exists())
    def test_restore_requires_offline_mode_and_never_overwrites(self):
        receipt=self.backup()
        with self.assertRaisesRegex(r2.BackupError,'OFFLINE_RECOVERY_REQUIRED'):
            r2.recover(self.store,self.key,receipt['object_key'],self.root/'new')
        existing=self.root/'existing'; existing.mkdir()
        with self.assertRaises(FileExistsError):
            r2.recover(self.store,self.key,receipt['object_key'],existing,True)

    def test_tenant_archive_rejects_traversal_undeclared_and_symlink_members(self):
        for index, member in enumerate(('../escape.sqlite3', 'genius.sqlite3.twins/'+'a'*32+'.sqlite3', 'genius.sqlite3')):
            bundle, target = self.root/f'hostile-{index}.zip', self.root/f'out-{index}'
            target.mkdir()
            with zipfile.ZipFile(bundle,'w') as z:
                info = zipfile.ZipInfo('genius.sqlite3')
                if index == 2:
                    info.external_attr = (0o120777 << 16)
                z.writestr(info,b'synthetic')
                z.writestr('genius.sqlite3.manifest.json',json.dumps({'twins':[]}))
                if index != 2:
                    z.writestr(member,b'synthetic')
            with self.assertRaises(r2.BackupError):
                r2.unpack(bundle,target)
            self.assertEqual(list(target.iterdir()),[])
    def test_expired_authenticated_snapshot_is_rejected(self):
        saved=self.root/'genius.sqlite3'
        helper=r2.sqlite_backup()
        helper.snapshot(self.db,saved)
        manifest=helper.manifest_path(saved)
        doc=json.loads(manifest.read_text())
        doc['created_at']=(datetime.now(timezone.utc)-timedelta(days=8)).isoformat()
        manifest.write_text(json.dumps(doc))
        bundle=self.root/'bundle'
        with zipfile.ZipFile(bundle,'w') as z:
            z.write(saved,saved.name);z.write(manifest,manifest.name)
        ciphertext=self.root/'expired'
        object_key='snapshots/expired.gcm'
        r2.seal(bundle,ciphertext,self.key,object_key)
        self.store.put(object_key,ciphertext)
        with self.assertRaisesRegex(RuntimeError,'seven-day'):
            r2.recover(self.store,self.key,object_key,self.root/'restored',True)
        self.assertFalse((self.root/'restored').exists())
    def test_retention_purge_requires_remote_intent_before_local_commit(self):
        self.seed()
        env={'GENIUS_R2_BACKUP_ENABLED':'true','GENIUS_BACKUP_ENCRYPTION_KEY':base64.b64encode(self.key).decode()}
        with patch.dict(os.environ,env),patch.object(r2,'runtime_store',return_value=self.store),contextlib.closing(sqlite3.connect(self.db,isolation_level=None)) as db:
            db.execute('PRAGMA foreign_keys=ON')
            self.store.fail_put=True
            with self.assertRaises(r2.BackupError):
                purge(db,90,self.now+91*86400)
            self.assertEqual(db.execute('SELECT count(*) FROM users').fetchone()[0],2)
            self.store.fail_put=False
            purge(db,90,self.now+91*86400)
            self.assertEqual(db.execute('SELECT count(*) FROM users').fetchone()[0],0)
            self.assertEqual(len(r2.read_deletions(self.store,self.key)),4)
    def test_authenticated_delete_returns_503_until_intent_is_durable(self):
        app=create_app(dict(DATA_DIR=self.live,DATABASE=self.db,SUSPEND_FILE=self.live/'SUSPENDED',PUBLIC_URL='http://localhost',TESTING=True))
        client=app.test_client()
        response=client.post('/api/register',json=dict(username='synthetic',password='A-long-password-123',privacy_accepted=True,privacy_version=app.config['PRIVACY_VERSION'],adult_confirmed=True))
        self.assertEqual(response.status_code,201)
        headers={'X-CSRF-Token':response.json['csrf_token']}
        env={'GENIUS_R2_BACKUP_ENABLED':'true','GENIUS_BACKUP_ENCRYPTION_KEY':base64.b64encode(self.key).decode()}
        with patch.dict(os.environ,env),patch.object(r2,'runtime_store',return_value=self.store):
            self.store.fail_put=True
            self.assertEqual(client.delete('/api/me',headers=headers).status_code,503)
            self.assertEqual(client.get('/api/me').status_code,200)
            self.store.fail_put=False
            self.assertEqual(client.delete('/api/me',headers=headers).status_code,204)
            self.assertEqual(client.get('/api/me').status_code,401)
            self.assertEqual(len(r2.read_deletions(self.store,self.key)),1)
    def test_missing_or_stale_backup_pauses_new_writes_but_keeps_reads(self):
        app=create_app(dict(DATA_DIR=self.live,DATABASE=self.db,SUSPEND_FILE=self.live/'SUSPENDED',PUBLIC_URL='http://localhost',TESTING=True))
        with patch.dict(os.environ,{'GENIUS_R2_BACKUP_ENABLED':'true'}):
            response=app.test_client().post('/api/register',json={})
            self.assertEqual(response.status_code,503)
            self.assertEqual(response.json['error']['code'],'backup_unavailable')
            self.assertEqual(app.test_client().get('/api/health').status_code,200)
    def test_s3_download_preserves_existing_file_and_redacts_provider_errors(self):
        store=object.__new__(r2.R2Store)
        class Client:
            def get_object(self,**kwargs):
                return {'ContentLength':3,'Body':io.BytesIO(b'abc')}
            def put_object(self,**kwargs):
                raise RuntimeError('sensitive-credential-should-not-escape')
        store.client=Client()
        target=self.root/'existing';target.write_bytes(b'keep')
        with self.assertRaises(FileExistsError):
            store.get('probes/test.gcm',target)
        self.assertEqual(target.read_bytes(),b'keep')
        with self.assertRaisesRegex(r2.BackupError,'^R2_UPLOAD_FAILED$'):
            store.put('probes/test.gcm',target)
    def test_sdk_uses_only_explicit_bucket_identity_https_and_bounded_retries(self):
        env={'GENIUS_R2_ACCOUNT_ID':'4a275114cfef4b41e73a135f089186ce',
             'GENIUS_R2_ACCESS_KEY_ID':'synthetic-access',
             'GENIUS_R2_SECRET_ACCESS_KEY':'synthetic-secret'}
        with patch.dict(os.environ,env):
            store=r2.R2Store()
        self.assertEqual(store.client.meta.endpoint_url,'https://4a275114cfef4b41e73a135f089186ce.r2.cloudflarestorage.com')
        self.assertEqual(store.client.meta.config.retries['total_max_attempts'],1)
        self.assertEqual(store.client.meta.config.s3['addressing_style'],'path')
        from botocore.stub import Stubber
        with Stubber(store.client) as stub:
            stub.add_response('list_objects_v2', {'IsTruncated':True,'NextContinuationToken':'page2','Contents':[{'Key':'snapshots/a.gcm','Size':12}]}, {'Bucket':r2.BUCKET,'Prefix':'snapshots/','MaxKeys':1000})
            stub.add_response('list_objects_v2', {'IsTruncated':False,'Contents':[{'Key':'snapshots/b.gcm','Size':13}]}, {'Bucket':r2.BUCKET,'Prefix':'snapshots/','MaxKeys':1000,'ContinuationToken':'page2'})
            self.assertEqual(len(store.list('snapshots/')),2)
    def test_startup_refuses_new_empty_database_when_remote_snapshots_exist(self):
        import importlib.util
        spec=importlib.util.spec_from_file_location('backup_start_test',Path(__file__).resolve().parents[1]/'deploy'/'start.py')
        start=importlib.util.module_from_spec(spec);spec.loader.exec_module(start)
        env={'GENIUS_R2_BACKUP_ENABLED':'true','GENIUS_BACKUP_ENCRYPTION_KEY':base64.b64encode(self.key).decode()}
        self.store.objects['snapshots/old.gcm']=b'synthetic-placeholder'
        with patch.dict(os.environ,env),patch.object(start,'validate_runtime_environment'),patch.object(start,'prepare_identity'),patch.object(r2,'R2Store',return_value=self.store),patch('genius_beta.config.settings',return_value={'DATABASE':self.root/'missing.sqlite3'}):
            with self.assertRaisesRegex(r2.BackupError,'REMOTE_BACKUPS_EXIST_RECOVERY_REQUIRED'):
                start.main()
        self.assertFalse((self.root/'missing.sqlite3').exists())


if __name__=='__main__':
    unittest.main(verbosity=2)
