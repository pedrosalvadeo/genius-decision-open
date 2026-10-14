"""Public deposit persistence, authorization and inert-content boundaries."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from genius_beta.app import create_app
from genius_beta.contributions import canonical, validate
from genius_beta.db import connect


class ContributionInboxTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.config = dict(DATA_DIR=self.root, DATABASE=self.root/'db.sqlite3',
            SUSPEND_FILE=self.root/'SUSPENDED', PUBLIC_URL='http://localhost',
            ENV='development', TESTING=True)
        self.app = create_app(self.config)
        self.client = self.app.test_client(use_cookies=False)
        self.payload = dict(format='genius-submission/1', author='external-test-agent',
            base_revision='a'*40, summary='A proposed test', claim='Not executed by receipt',
            reproduction='Not run: delivery test only.', license='Apache-2.0',
            files=[dict(path='tests/example.py', content='raise RuntimeError("never execute a deposit")\n')],
            publication_confirmed=True, operator_authorized=True)

    def tearDown(self):
        self.temp.cleanup()

    def test_public_persistent_receipt_and_duplicate_no_execution(self):
        r = self.client.post('/contributions', json=self.payload)
        self.assertEqual(r.status_code, 201, r.json)
        ident = hashlib.sha256(canonical(self.payload)).hexdigest()
        self.assertEqual(r.json['receipt']['id'], ident)
        self.assertEqual(r.json['receipt']['status'], 'RECEIVED')
        self.assertNotIn('Set-Cookie', r.headers)
        self.assertFalse((self.root/'tests/example.py').exists())
        other_app = create_app(self.config)
        other = other_app.test_client(use_cookies=False)
        self.assertEqual(other.get('/contributions/'+ident).json['submission'], self.payload)
        repeated = other.post('/contributions', json=self.payload)
        self.assertEqual(repeated.status_code, 200)
        self.assertTrue(repeated.json['duplicate'])
        self.assertEqual(repeated.json['receipt'], r.json['receipt'])
        with connect(self.config['DATABASE']) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM users').fetchone()[0], 0)
            self.assertEqual(db.execute('SELECT count(*) FROM contribution_inbox').fetchone()[0], 1)

    def test_exact_contract_authorization_sizes_and_paths(self):
        for field in ('publication_confirmed', 'operator_authorized'):
            value = copy.deepcopy(self.payload); value[field] = False
            with self.assertRaises(ValueError): validate(value)
        for path in ('../escape.py', '/absolute.py', 'a//b.py', 'a/./b.py', '.git/config', 'a\\b.py', 'a b.py'):
            value = copy.deepcopy(self.payload); value['files'][0]['path'] = path
            with self.assertRaises(ValueError): validate(value)
        for alteration in ('duplicate', 'large', 'secret', 'revision', 'extra'):
            value = copy.deepcopy(self.payload)
            if alteration == 'duplicate': value['files'].append(dict(path='Tests/EXAMPLE.py', content='x'))
            elif alteration == 'large': value['files'][0]['content'] = 'x'*100000
            elif alteration == 'secret': value['files'][0]['content'] = '-----BEGIN ' + 'PRIVATE KEY-----'
            elif alteration == 'revision': value['base_revision'] = 'main'
            else: value['execute'] = True
            with self.assertRaises(ValueError): validate(value)

    def test_cross_site_paused_and_backup_unavailable_cannot_write(self):
        r = self.client.post('/contributions', json=self.payload, headers={'Origin':'https://other.invalid'})
        self.assertEqual(r.status_code, 403)
        self.config['SUSPEND_FILE'].touch()
        self.assertFalse(self.client.get('/contributions').json['available'])
        self.assertEqual(self.client.post('/contributions', json=self.payload).status_code, 503)
        self.config['SUSPEND_FILE'].unlink()
        with patch('genius_beta.app.backup_enabled', return_value=True), patch('genius_beta.app.backup_health', return_value='unavailable'):
            self.assertEqual(self.client.post('/contributions', json=self.payload).status_code, 503)

    def test_quota_ignores_forwarded_ip_and_existing_content_remains_readable(self):
        first = self.client.post('/contributions', json=self.payload).json['receipt']['id']
        for i in range(4):
            value = dict(self.payload, summary='Deposit '+str(i))
            self.assertEqual(self.client.post('/contributions', json=value).status_code, 201)
        self.assertEqual(self.client.post('/contributions', json=self.payload,
            headers={'X-Forwarded-For':'192.0.2.10'}).status_code, 429)
        self.assertEqual(self.client.get('/contributions/'+first).status_code, 200)

    def test_feed_pagination_and_unknown_receipt(self):
        self.client.post('/contributions', json=self.payload)
        self.client.post('/contributions', json=dict(self.payload, summary='Second deposit'))
        first = self.client.get('/contributions/feed?limit=1').json
        second = self.client.get('/contributions/feed?after='+str(first['next_after'])).json
        self.assertEqual(len(first['items']), 1); self.assertEqual(len(second['items']), 1)
        self.assertNotEqual(first['items'][0]['id'], second['items'][0]['id'])
        self.assertEqual(self.client.get('/contributions/feed?limit=500').status_code, 400)
        self.assertEqual(self.client.get('/contributions/feed?after=0&after=1').status_code, 400)
        self.assertEqual(self.client.get('/contributions/'+'0'*64).status_code, 404)

    def test_duplicate_json_and_invalid_utf8_are_rejected(self):
        r = self.client.post('/contributions', data='{"format":"x","format":"y"}', content_type='application/json')
        self.assertEqual(r.status_code, 400)
        value = copy.deepcopy(self.payload); value['files'][0]['content'] = '\ud800'
        r = self.client.post('/contributions', data=json.dumps(value), content_type='application/json')
        self.assertEqual(r.status_code, 400)

    def test_mcp_deposit_and_read_without_github_or_service_credentials(self):
        def call(name, args):
            return self.client.post('/mcp', json=dict(jsonrpc='2.0', id=1, method='tools/call',
                params=dict(name=name, arguments=args)),
                headers={'Accept':'application/json,text/event-stream'})
        contract = call('get_contribution_inbox', {})
        self.assertFalse(contract.json['result']['isError'])
        result = call('submit_contribution', {'submission':self.payload}).json['result']
        self.assertFalse(result['isError'], result)
        ident = result['structuredContent']['receipt']['id']
        self.assertEqual(call('get_contribution', {'id':ident}).json['result']['structuredContent']['submission'], self.payload)


if __name__ == '__main__': unittest.main()
