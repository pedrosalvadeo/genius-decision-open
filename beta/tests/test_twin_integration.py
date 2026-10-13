"""Authenticated mounting, isolated real execution, and private data lifecycle."""
from contextlib import closing
import fcntl
import importlib.util
import json
import base64
import os
from pathlib import Path
import shutil
import tempfile
import time
import unittest
from unittest.mock import patch

from genius_beta.app import create_app
from genius_beta.db import connect
from genius_beta.twin_integration import lifecycle_lock, tenant_path, purge_twins
from genius_twin.process_runner import ProcessEvaluator
from genius_twin.registry import example, STOCKFLOW
from genius_twin.store import Store

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('twin_backup_test', ROOT/'beta/deploy/backup.py')
backup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backup)


class TwinMountTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        data = Path(self.temp.name)/'live'
        self.config = dict(DATA_DIR=data, DATABASE=data/'genius.sqlite3', SUSPEND_FILE=data/'SUSPENDED',
                           PUBLIC_URL='http://localhost', TESTING=True, TWIN_ENABLED=True)
        self.app = create_app(self.config)
        self.a, self.b = self.app.test_client(), self.app.test_client()
        self.tokens = {}
        for client, name in ((self.a, 'alpha'), (self.b, 'bravo')):
            r = client.post('/api/register', json=dict(username=name, password='A-long-password-123', privacy_accepted=True, privacy_version=self.app.config['PRIVACY_VERSION'], adult_confirmed=True))
            self.assertEqual(r.status_code, 201, r.json)
            self.tokens[client] = r.json['csrf_token']
        self.model = example('stockflow_care')['model']

    def tearDown(self):
        self.temp.cleanup()

    def mutate(self, path, payload=None, client=None, method='post'):
        client = client or self.a
        return getattr(client, method)(path, json={} if payload is None else payload,
                                      headers={'X-CSRF-Token': self.tokens[client]})

    def confirmed(self, client=None):
        client = client or self.a
        r = self.mutate('/api/twin/cases', {'text': 'Plan de recursos hipotético', 'profile': STOCKFLOW}, client)
        self.assertEqual(r.status_code, 201, r.json)
        cid = r.json['case']['id']
        r = self.mutate(f'/api/twin/cases/{cid}/proposals', {'base_version': 0, 'kind': 'declared_model',
                        'text': 'Premisas hipotéticas explícitas', 'structured': {'model': self.model}}, client)
        self.assertEqual(r.status_code, 201, r.json)
        pid = r.json['proposal']['id']
        r = self.mutate(f'/api/twin/proposals/{pid}/accept', {'base_version': 0, 'confirmed': True,
                        'acknowledge_declared': True, 'idempotency_key': 'initial-confirmation'}, client)
        self.assertEqual(r.status_code, 200, r.json)
        return cid, pid

    def uid(self, client=None):
        return (client or self.a).get('/api/me').json['user']['id']

    def test_real_process_and_human_agent_private_parity(self):
        cid, pid = self.confirmed()
        r = self.mutate(f'/api/twin/cases/{cid}/evaluate', {'version': 1})
        self.assertEqual(r.status_code, 200, r.json)
        self.assertEqual(r.json['job']['status'], 'completed', r.json)
        self.assertTrue(r.json['evaluation']['verification']['valid'])
        jid = r.json['job']['id']
        token = self.mutate('/api/tokens', {'label': 'Twin agent'}).json
        agent = self.app.test_client()
        headers = {'Authorization': 'Bearer '+token['token']}
        self.assertEqual(agent.get('/api/twin/jobs/'+jid, headers=headers).json, self.a.get('/api/twin/jobs/'+jid).json)
        self.assertEqual(agent.get('/api/twin/runtime', headers=headers).json['csrf_token'], None)
        for path in (f'/cases/{cid}', f'/cases/{cid}/export', f'/jobs/{jid}', f'/cases/{cid}/compare?before=1&after=1'):
            self.assertEqual(self.b.get('/api/twin'+path).status_code, 404)
        for path, payload in ((f'/cases/{cid}/evaluate', {'version': 1}),
                              (f'/proposals/{pid}/accept', {'base_version': 0, 'confirmed': True, 'acknowledge_declared': True, 'idempotency_key': 'other-user'}),
                              (f'/cases/{cid}/proposals', {'base_version': 1, 'kind': 'restore', 'text': 'Restituir', 'structured': {'version': 1}})):
            self.assertEqual(self.mutate('/api/twin'+path, payload, self.b).status_code, 404)
        self.assertEqual(self.mutate(f'/api/twin/cases/{cid}/draft', {'base_version': 1, 'draft_revision': 0, 'text': 'Borrador ajeno', 'model': None}, self.b, 'patch').status_code, 404)
        self.assertEqual(self.mutate(f'/api/twin/cases/{cid}', {'base_version': 1}, self.b, 'delete').status_code, 404)
        self.assertEqual(len(self.a.get('/api/export').json['twins']), 1)
        self.assertEqual(self.b.get('/api/twin/cases').json['cases'], [])
        self.assertEqual(self.mutate('/api/tokens/'+token['id'], method='delete').status_code, 204)
        self.assertEqual(agent.get('/api/twin/cases', headers=headers).status_code, 401)

    def test_auth_csrf_suspend_and_bounded_output(self):
        self.assertEqual(self.app.test_client().get('/api/twin/cases').status_code, 401)
        self.assertEqual(self.a.post('/api/twin/cases', json={'text': 'No CSRF'}).status_code, 403)
        self.assertEqual(self.a.get('/api/twin/runtime').json['csrf_token'], self.tokens[self.a])
        self.config['SUSPEND_FILE'].touch()
        self.assertEqual(self.mutate('/api/twin/cases', {'text': 'Suspended'}).status_code, 503)
        self.assertEqual(self.a.get('/api/twin/cases').status_code, 200)
        with self.assertRaises(RuntimeError):
            ProcessEvaluator(output_bytes=1024)(self.model)

    def test_case_delete_tombstone_only_after_validation(self):
        cid, _ = self.confirmed()
        for payload, expected in (({'base_version': 0}, 409), ({}, 400)):
            self.assertEqual(self.mutate(f'/api/twin/cases/{cid}', payload, method='delete').status_code, expected)
            with closing(connect(self.config['DATABASE'])) as db:
                self.assertIsNone(db.execute('SELECT 1 FROM deletion_ledger WHERE id=?', (cid,)).fetchone())
        self.assertEqual(self.a.get('/api/twin/cases/'+cid).status_code, 200)
        self.assertEqual(self.mutate(f'/api/twin/cases/{cid}', {'base_version': 1}, method='delete').status_code, 200)
        with closing(connect(self.config['DATABASE'])) as db:
            self.assertEqual(db.execute('SELECT entity_type FROM deletion_ledger WHERE id=?', (cid,)).fetchone()[0], 'twin_case')
        self.assertEqual(self.a.get('/api/twin/cases/'+cid).status_code, 404)

    def test_advertised_capacity_limits_leave_history_unchanged(self):
        self.app.config.update(MAX_CASES=1, MAX_REVISIONS=1)
        cid, _ = self.confirmed()
        self.assertEqual(self.mutate('/api/twin/cases', {'text': 'Otro plan', 'profile': STOCKFLOW}).status_code, 429)
        proposed = self.mutate(f'/api/twin/cases/{cid}/proposals', {'base_version': 1, 'kind': 'declared_model',
                               'text': 'Revisar premisas', 'structured': {'model': dict(self.model, name='Variante limitada')}})
        self.assertEqual(proposed.status_code, 201, proposed.json)
        pid = proposed.json['proposal']['id']
        rejected = self.mutate(f'/api/twin/proposals/{pid}/accept', {'base_version': 1, 'confirmed': True,
                              'acknowledge_declared': True, 'idempotency_key': 'limited-confirmation'})
        self.assertEqual(rejected.status_code, 429, rejected.json)
        with (self.config['DATA_DIR']/'twin-locks'/'compiler.lock').open('a+b') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            r = self.mutate(f'/api/twin/cases/{cid}/evaluate', {'version': 1})
            self.assertEqual(r.status_code, 429, r.json)
        state = self.a.get('/api/twin/cases/'+cid).json
        self.assertEqual(len(state['versions']), 1)
        self.assertEqual(state['jobs'], [])
        self.app.config['TWIN_STORAGE_BYTES'] = 0
        self.assertEqual(self.mutate(f'/api/twin/cases/{cid}/evaluate', {'version': 1}).status_code, 503)

    def test_account_busy_delete_then_erasure_and_disabled_feature(self):
        self.confirmed()
        uid = self.uid()
        path = tenant_path(self.config['DATA_DIR'], uid)
        self.assertTrue(path.exists())
        with lifecycle_lock(self.config['DATA_DIR'], uid):
            self.assertEqual(self.mutate('/api/me', method='delete').status_code, 409)
        self.assertEqual(self.a.get('/api/me').status_code, 200)
        disabled = create_app(dict(self.config, TWIN_ENABLED=False)).test_client()
        login = disabled.post('/api/login', json={'username': 'alpha', 'password': 'A-long-password-123'})
        self.assertEqual(login.status_code, 200, login.json)
        self.assertEqual(disabled.get('/api/twin/cases').status_code, 404)
        self.assertEqual(len(disabled.get('/api/export').json['twins']), 1)
        self.assertEqual(disabled.delete('/api/me', headers={'X-CSRF-Token': login.json['csrf_token']}).status_code, 204)
        self.assertFalse(path.exists())
        self.assertEqual(self.a.get('/api/twin/cases').status_code, 401)

    def test_retention_and_orphan_sweep(self):
        cid, _ = self.confirmed()
        uid = self.uid()
        store = Store(tenant_path(self.config['DATA_DIR'], uid))
        with store.transaction() as db:
            db.execute("UPDATE cases SET updated_at='2020-01-01T00:00:00+00:00' WHERE id=?", (cid,))
        with closing(connect(self.config['DATABASE'])) as db:
            result = purge_twins(self.app.config, db)
            self.assertEqual(result['twin_cases'], 1)
            self.assertEqual(db.execute('SELECT entity_type FROM deletion_ledger WHERE id=?', (cid,)).fetchone()[0], 'twin_case')
            db.execute('DELETE FROM users WHERE id=?', (uid,))
            result = purge_twins(self.app.config, db)
            self.assertEqual(result['twin_users'], 1)
        self.assertFalse(tenant_path(self.config['DATA_DIR'], uid).exists())

    def test_backup_restore_keeps_current_privacy_and_interrupts_jobs(self):
        kept, _ = self.confirmed()
        deleted, _ = self.confirmed()
        self.confirmed(self.b)
        uid, other = self.uid(), self.uid(self.b)
        store = Store(tenant_path(self.config['DATA_DIR'], uid))
        with store.transaction() as db:
            db.execute("INSERT INTO jobs(id,case_id,version,status,created_at) VALUES('interrupted',?,1,'running','2026-01-01T00:00:00+00:00')", (kept,))
        saved = Path(self.temp.name)/'backup'/'saved.sqlite3'
        manifest = backup.snapshot(self.config['DATABASE'], saved)
        self.assertEqual(len(manifest['twins']), 2)
        self.assertEqual(self.mutate(f'/api/twin/cases/{kept}', {'base_version': 0}, method='delete').status_code, 409)
        self.assertEqual(self.mutate(f'/api/twin/cases/{deleted}', {'base_version': 1}, method='delete').status_code, 200)
        self.assertEqual(self.mutate('/api/me', client=self.b, method='delete').status_code, 204)
        output = Path(self.temp.name)/'offline'/'restored.sqlite3'
        result = backup.restore(saved, output, self.config['DATABASE'], services_stopped=True)
        self.assertEqual([r['user_id'] for r in result['twins']], [uid])
        restored = Store(backup.twin_folder(output)/(uid+'.sqlite3'))
        self.assertEqual([r['id'] for r in restored.read('SELECT id FROM cases')], [kept])
        self.assertEqual(restored.one("SELECT status FROM jobs WHERE id='interrupted'")['status'], 'failed')
        self.assertFalse((backup.twin_folder(output)/(other+'.sqlite3')).exists())
        # Verify a tenant digest before any restored output is published.
        with (backup.twin_folder(saved)/(uid+'.sqlite3')).open('ab') as file:
            file.write(b'changed')
        with self.assertRaisesRegex(RuntimeError, 'SHA256'):
            backup.restore(saved, Path(self.temp.name)/'tampered.sqlite3', self.config['DATABASE'], services_stopped=True)

    def test_r2_volume_loss_restores_twins_and_honors_remote_deletion_intents(self):
        from genius_beta import r2_backup as r2
        from test_r2_backup import ObjectStore
        kept, _ = self.confirmed()
        deleted, _ = self.confirmed()
        stale, _ = self.confirmed()
        self.confirmed(self.b)
        uid, other = self.uid(), self.uid(self.b)
        store = Store(tenant_path(self.config['DATA_DIR'], uid))
        with store.transaction() as db:
            db.execute("UPDATE cases SET updated_at='2020-01-01T00:00:00+00:00' WHERE id=?", (stale,))
            db.execute("INSERT INTO jobs(id,case_id,version,status,created_at) VALUES('pending',?,1,'running','2026-01-01T00:00:00+00:00')", (kept,))
        remote, key = ObjectStore(), os.urandom(32)
        receipt = r2.backup_once(self.config['DATABASE'], self.config['DATA_DIR']/'backup-status.json', remote, key)
        env = {'GENIUS_R2_BACKUP_ENABLED': 'true', 'GENIUS_BACKUP_ENCRYPTION_KEY': base64.b64encode(key).decode()}
        with patch.dict(os.environ, env), patch.object(r2, 'runtime_store', return_value=remote):
            self.assertEqual(self.mutate(f'/api/twin/cases/{deleted}', {'base_version': 1}, method='delete').status_code, 200)
            self.assertEqual(self.mutate('/api/me', client=self.b, method='delete').status_code, 204)
        self.assertIn((deleted, 'twin_case'), {(i,k) for i,k,_ in r2.read_deletions(remote,key)})
        shutil.rmtree(self.config['DATA_DIR'])
        output = Path(self.temp.name)/'recovered-r2'
        result = r2.recover(remote, key, receipt['object_key'], output, True)
        self.assertTrue(result['suspended'])
        restored = Store(tenant_path(output, uid))
        self.assertEqual([r['id'] for r in restored.read('SELECT id FROM cases')], [kept])
        self.assertEqual(restored.one("SELECT status FROM jobs WHERE id='pending'")['status'], 'failed')
        self.assertFalse(tenant_path(output, other).exists())
        self.assertEqual(tenant_path(output, uid).stat().st_mode & 0o777, 0o600)
        with closing(connect(output/'genius.sqlite3')) as db:
            self.assertEqual(db.execute('SELECT id FROM users').fetchall()[0][0], uid)
            self.assertEqual(db.execute('SELECT count(*) FROM sessions').fetchone()[0], 0)

    def test_remote_privacy_failure_blocks_twin_erasure_and_retention(self):
        from genius_beta import r2_backup as r2
        cid, _ = self.confirmed()
        with patch.object(r2, 'record_deletions', side_effect=r2.BackupError('R2_UPLOAD_FAILED')):
            response = self.mutate(f'/api/twin/cases/{cid}', {'base_version': 1}, method='delete')
            self.assertEqual(response.status_code, 503)
            self.assertEqual(self.a.get('/api/twin/cases/'+cid).status_code, 200)
            store = Store(tenant_path(self.config['DATA_DIR'], self.uid()))
            with store.transaction() as db:
                db.execute("UPDATE cases SET updated_at='2020-01-01T00:00:00+00:00' WHERE id=?", (cid,))
            with closing(connect(self.config['DATABASE'])) as db:
                with self.assertRaises(r2.BackupError):
                    purge_twins(self.app.config, db)
                self.assertIsNone(db.execute('SELECT 1 FROM deletion_ledger WHERE id=?',(cid,)).fetchone())
            self.assertIsNotNone(store.one('SELECT id FROM cases WHERE id=?',(cid,)))


if __name__ == '__main__':
    unittest.main()
