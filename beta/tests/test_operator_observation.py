"""Operator authority is isolated; aggregate reads preserve production records."""
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import threading
import unittest
from unittest.mock import patch

from genius_beta.app import create_app
from genius_beta import operator_observation as operator
from genius_beta import regulation as reg
from genius_beta.db import transaction


class OperatorObservationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.now = 1_000_000_000
        self.token = 'go_' + 'a' * 43  # Fixed test-only capability, never provisioned.
        self.grant = dict(sha256=hashlib.sha256(self.token.encode()).hexdigest(),
                          not_before=self.now-60, expires_at=self.now+3600)
        self.config = dict(DATA_DIR=root, DATABASE=root/'db.sqlite3',
            SUSPEND_FILE=root/'SUSPENDED', PUBLIC_URL='http://localhost',
            ENV='development', REGISTRATION_OPEN=True, TESTING=True,
            ADAPTIVE_ENABLED=True, MISSION_REGULATION_ENABLED=True,
            OPERATOR_OBSERVATION_GRANT=json.dumps(self.grant), DEPLOYMENT_ID='test-deployment')
        clock = patch.object(operator.time, 'time', side_effect=lambda: self.now)
        clock.start()
        self.addCleanup(clock.stop)
        self.app = create_app(self.config)
        self.client = self.app.test_client()
        self.db = sqlite3.connect(self.config['DATABASE'], isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.addCleanup(self.db.close)

    def get(self, client=None, headers=None, query=None, **kwargs):
        return (client or self.client).get(operator.PATH,
            query_string=query if query is not None else dict(since=self.now-30, until=self.now),
            headers=headers if headers is not None else {'Authorization':'Bearer '+self.token}, **kwargs)

    def test_aggregate_reads_real_journal_without_writes_or_payload_export(self):
        with patch.object(reg, 'observe', return_value=dict(storage_bytes=1000, free_bytes=10**9, pending=0)):
            with transaction(self.db):
                state = reg.refresh(self.db, self.app.config, force=True, now=self.now)
                marker = reg.begin(self.db, self.app.config, state)
            self.now += 5
            with transaction(self.db):
                reg.finish(self.db, self.app.config, marker, 'completed', None)
        self.now += 1
        self.db.execute('INSERT INTO adaptive_missions '
            '(id,user_id,idempotency_key,request_sha256,input_json,status,result_json,artifact,created_at,updated_at) '
            'VALUES(?,?,?,?,?,?,?,?,?,?)', ('private-mission', 'private-user', 'private-key',
                'private-hash', '{"private-input":1}', 'queued', '{"private-result":1}',
                b'private-artifact', self.now, self.now))
        before = '\n'.join(self.db.iterdump())
        db_bytes = self.config['DATABASE'].read_bytes()
        wal = Path(str(self.config['DATABASE'])+'-wal')
        wal_bytes = wal.read_bytes()
        response = self.get()
        self.assertEqual(response.status_code, 200)
        value = response.json['observation']
        self.assertEqual(value['retained_window_events']['finished']['completed'], 1)
        self.assertEqual(value['recorded_elapsed_seconds']['all_finished']['p95'], 5)
        self.assertEqual(value['current_snapshot']['pending_missions'], 1)
        self.assertFalse(value['coverage']['complete_window_proven'])
        self.assertFalse(value['source']['independently_verified'])
        self.assertFalse(value['eligible_for_policy_promotion'])
        self.assertEqual(response.json['runtime']['deployment_id'], 'test-deployment')
        text = response.get_data(as_text=True)
        for secret in (marker, 'private-', str(self.config['DATABASE']), self.token, self.grant['sha256']):
            self.assertNotIn(secret, text)
        self.assertEqual('\n'.join(self.db.iterdump()), before)
        self.assertEqual(self.config['DATABASE'].read_bytes(), db_bytes)
        self.assertEqual(wal.read_bytes(), wal_bytes)
        self.assertEqual(response.headers['Cache-Control'], 'no-store')
        self.assertEqual(response.headers['X-Robots-Tag'], 'noindex, nofollow')
        self.assertNotIn('Access-Control-Allow-Origin', response.headers)
        self.assertNotIn('Set-Cookie', response.headers)

    def test_missing_invalid_and_out_of_window_grants_fail_closed(self):
        values = ['', '{', 'null', json.dumps(dict(self.grant, extra=True)),
            json.dumps(dict(self.grant, sha256='not-a-hash')),
            json.dumps(dict(self.grant, not_before=True)),
            json.dumps(dict(self.grant, expires_at=self.grant['not_before']+86401)),
            json.dumps(dict(self.grant, expires_at=self.now)),
            json.dumps(dict(self.grant, not_before=self.now+1)),
            json.dumps(self.grant)[:-1]+',"sha256":"'+'f'*64+'"}']
        with patch.object(operator, 'report') as read:
            for raw in values:
                with self.subTest(raw=raw):
                    app = create_app(dict(self.config, OPERATOR_OBSERVATION_GRANT=raw))
                    self.assertEqual(self.get(client=app.test_client()).status_code, 404)
            read.assert_not_called()
        # Expiry is checked for every request, not only during process startup.
        self.now = self.grant['expires_at']
        self.assertEqual(self.get().status_code, 404)

    def test_unauthorized_requests_never_open_database(self):
        with patch.object(operator, 'report') as read:
            for headers in ({}, {'Authorization':'Bearer wrong'},
                    {'Authorization':'Bearer go_'+'b'*43}, {'Authorization':'Bearer '+self.grant['sha256']},
                    {'X-Operator-Token':self.token}):
                self.assertEqual(self.get(headers=headers).status_code, 401)
            self.assertEqual(self.get(headers={}, query={'token':self.token}).status_code, 401)
            read.assert_not_called()

    def test_user_session_api_key_and_operator_key_have_separate_authority(self):
        response = self.client.post('/api/register', json=dict(username='operator_test_user',
            password='Synthetic-test-only-123!', privacy_accepted=True,
            privacy_version=self.app.config['PRIVACY_VERSION'], adult_confirmed=True))
        self.assertEqual(response.status_code, 201)
        key = self.client.post('/api/tokens', json=dict(label='test'),
            headers={'X-CSRF-Token':response.json['csrf_token']}).json['token']
        self.assertEqual(self.get(headers={}).status_code, 401)
        self.assertEqual(self.get(headers={'Authorization':'Bearer '+key}).status_code, 401)
        response = self.client.get('/api/me', headers={'Authorization':'Bearer '+self.token})
        self.assertEqual(response.status_code, 401)

    def test_invalid_parameters_cannot_select_other_data_or_consume_read_slot(self):
        for query in ({}, dict(since=0, until=self.now), dict(since=self.now, until=self.now),
                dict(since=self.now, until=self.now+1), dict(since='NaN', until=self.now),
                dict(since=-1, until=2), dict(since=self.now-30, until=self.now, database='/elsewhere'),
                [('since',str(self.now-30)), ('since','0'), ('until',str(self.now))]):
            self.assertEqual(self.get(query=query).status_code, 400)
        self.assertEqual(self.get(data='secret').status_code, 400)
        self.assertEqual(self.get().status_code, 200)

    def test_cross_site_requests_and_methods_do_not_run_report(self):
        headers = {'Authorization':'Bearer '+self.token}
        with patch.object(operator, 'report') as read:
            for h in (dict(headers, Origin='https://other.example'), dict(headers, **{'Sec-Fetch-Site':'cross-site'})):
                self.assertEqual(self.get(headers=h).status_code, 403)
            for method in ('POST', 'PUT', 'DELETE', 'OPTIONS', 'HEAD'):
                self.assertEqual(self.client.open(operator.PATH, method=method, headers=headers).status_code, 405)
            read.assert_not_called()

    def test_missing_or_incompatible_database_fails_without_creating_empty_report(self):
        with patch.object(operator.time, 'monotonic', side_effect=[100,200]):
            self.db.execute('DROP TABLE mission_regulation_events')
            response = self.get()
            self.assertEqual(response.status_code, 503)
            self.assertEqual(response.json, dict(error=dict(code='observation_unavailable')))
            self.app.config['DATABASE'] = self.config['DATABASE'].with_name('absent.sqlite3')
            self.assertEqual(self.get().status_code, 503)
            self.assertFalse(self.app.config['DATABASE'].exists())

    def test_concurrent_and_repeated_reads_are_bounded_without_persistent_counters(self):
        entered, release = threading.Event(), threading.Event()
        self.addCleanup(release.set)
        results = []
        actual_report = operator.report
        def slow(*args, **kwargs):
            entered.set()
            release.wait(5)
            return actual_report(*args, **kwargs)
        before = self.db.execute('SELECT count(*) FROM counters').fetchone()[0]
        with patch.object(operator, 'report', side_effect=slow) as read, \
                patch.object(operator.time, 'monotonic', side_effect=[100,200,201,202,300]):
            worker = threading.Thread(target=lambda: results.append(self.get(client=self.app.test_client()).status_code))
            worker.start()
            self.assertTrue(entered.wait(5))
            response = self.get()
            self.assertEqual(response.status_code, 429)
            self.assertEqual(response.headers['Retry-After'], '60')
            release.set()
            worker.join(5)
            self.assertFalse(worker.is_alive())
            self.assertEqual(results, [200])
            self.assertEqual(read.call_count, 1)
            # Long-running reads cannot overlap even after the minute expires;
            # after release, the independent clock guard also limits repeats.
            self.assertEqual(self.get().status_code, 200)
            self.assertEqual(self.get().status_code, 429)
            self.assertEqual(self.get().status_code, 200)
        self.assertEqual(self.db.execute('SELECT count(*) FROM counters').fetchone()[0], before)

    def test_endpoint_and_grant_do_not_enter_public_discovery(self):
        for path in ('/openapi.json', '/llms.txt', '/api/config', '/api/health'):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            for secret in (operator.PATH, self.grant['sha256'], self.token):
                self.assertNotIn(secret, response.get_data(as_text=True))


if __name__ == '__main__':
    unittest.main()
