"""Behavior/security checks using only local synthetic agents and disposable storage."""
import contextlib
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import secrets
import sqlite3
import tempfile
import time
import unittest
from unittest.mock import patch

from genius_beta.app import create_app
from genius_beta.agent_access import POLICY_VERSION as AGENT_POLICY
from genius_beta.club import POLICY_VERSION, SCOPES
from genius_beta.db import connect, purge
from genius_beta import r2_backup as r2


class ClubTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.config = dict(DATA_DIR=root, DATABASE=root/'genius.sqlite3',
            SUSPEND_FILE=root/'SUSPENDED', PUBLIC_URL='http://localhost', TESTING=True,
            REGISTRATION_OPEN=True, MAX_AGENT_REGISTRATIONS_DAILY=20)
        self.backup_env = patch.dict(os.environ, {'GENIUS_R2_BACKUP_ENABLED':'false'})
        self.backup_env.start()
        self.addCleanup(self.backup_env.stop)
        self.app = create_app(self.config)
        self.client = self.app.test_client(use_cookies=False)
        self.serial = 0

    def register(self, scopes=None):
        self.serial += 1
        response = self.client.post('/api/agents/register', json={
            'policy_version': AGENT_POLICY, 'data_policy_acknowledged': True,
            'scopes': list(scopes if scopes is not None else (*SCOPES, 'account:delete'))},
            environ_overrides={'REMOTE_ADDR': '127.0.0.'+str(self.serial)})
        self.assertEqual(response.status_code, 201, response.json)
        return response.json, {'Authorization': 'Bearer '+response.json['credential']['token']}

    def join(self, headers, **extra):
        response = self.client.post('/api/club/join', headers=headers,
            json={'policy_version':POLICY_VERSION, 'data_policy_acknowledged':True, **extra})
        self.assertIn(response.status_code, (200,201), response.json)
        return response

    def save(self, headers, content='lote,cantidad\nA,12\n', **extra):
        response = self.client.post('/api/club/files', headers=headers,
            json={'request_id':secrets.token_hex(16), 'name':'ovejas.csv',
                  'media_type':'text/csv', 'content':content, **extra})
        self.assertEqual(response.status_code, 201, response.json)
        return response.json['file']

    def test_optional_alias_membership_restart_and_key_rotation(self):
        issued, headers = self.register()
        result = self.join(headers)
        self.assertEqual(result.status_code,201)
        self.assertIsNone(result.json['member']['alias'])
        self.assertFalse(result.json['contribution_accepted'])
        member = result.json['member']
        self.assertEqual(member['agent_id'],issued['agent']['id'])
        self.assertEqual(self.join(headers,alias='do not overwrite').json['member'],member)
        f = self.save(headers)
        new = create_app(self.config).test_client(use_cookies=False)
        self.assertEqual(new.get('/api/club/files/'+f['id'],headers=headers).json['file']['content'],f['content'])
        rotated = new.post('/api/agents/token',headers=headers,json={})
        self.assertEqual(rotated.status_code,200,rotated.json)
        self.assertEqual(new.get('/api/club/me',headers=headers).status_code,401)
        headers = {'Authorization':'Bearer '+rotated.json['credential']['token']}
        self.assertEqual(new.get('/api/club/me',headers=headers).json['member']['id'],member['id'])
        changed = new.patch('/api/club/me',headers=headers,json={'alias':'Ovejas','base_version':1})
        self.assertEqual(changed.json['member']['alias'],'Ovejas')
        self.assertEqual(new.patch('/api/club/me',headers=headers,json={'alias':'lost','base_version':1}).status_code,409)

    def test_ownership_scope_and_no_publication(self):
        _, a = self.register()
        _, b = self.register()
        _, narrow = self.register(['club:read'])
        self.join(a); self.join(b)
        f = self.save(a)
        for suffix in ('','/versions'):
            self.assertEqual(self.client.get('/api/club/files/'+f['id']+suffix,headers=b).status_code,404)
            self.assertEqual(self.client.get('/api/club/files/'+f['id']+suffix).status_code,401)
        self.assertEqual(self.client.put('/api/club/files/'+f['id'],headers=b,json={'base_version':1,'content':'steal'}).status_code,404)
        self.assertEqual(self.client.delete('/api/club/files/'+f['id'],headers=b,json={'base_version':1,'confirm':True}).status_code,404)
        self.assertEqual(self.client.post('/api/club/join',headers=narrow,json={'policy_version':POLICY_VERSION,'data_policy_acknowledged':True}).status_code,403)
        self.assertEqual(self.client.get('/api/club/export',headers=b).json['files'],[])
        with contextlib.closing(connect(self.config['DATABASE'])) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM contribution_inbox').fetchone()[0],0)

    def test_versions_hashes_idempotence_and_stale_update(self):
        _, h = self.register(); self.join(h)
        text = '<script>fetch("https://example.invalid")</script>\nñ🐑\n'
        rid = secrets.token_hex(16)
        f = self.save(h,text,request_id=rid)
        self.assertEqual(f['sha256'],hashlib.sha256(text.encode()).hexdigest())
        retry = self.client.post('/api/club/files',headers=h,json={'request_id':rid,'name':'ovejas.csv','media_type':'text/csv','content':text})
        self.assertEqual(retry.status_code,200)
        self.assertEqual(retry.json['file']['id'],f['id'])
        conflict = self.client.post('/api/club/files',headers=h,json={'request_id':rid,'name':'other.csv','content':text})
        self.assertEqual(conflict.status_code,409)
        url = '/api/club/files/'+f['id']
        for _ in range(2):
            updated = self.client.put(url,headers=h,json={'base_version':1,'content':'version 2'})
            self.assertEqual(updated.status_code,200,updated.json)
            self.assertEqual(updated.json['file']['current_version'],2)
        self.assertEqual(self.client.put(url,headers=h,json={'base_version':1,'content':'lost'}).status_code,409)
        history = self.client.get(url+'/versions',headers=h).json['versions']
        self.assertEqual([r['content'] for r in history],[text,'version 2'])
        response = self.client.get(url,headers=h)
        self.assertEqual(response.mimetype,'application/json')
        self.assertEqual(response.headers['Cache-Control'],'no-store')
        self.assertNotIn('Set-Cookie',response.headers)

    def test_concurrent_writes_do_not_silently_overwrite(self):
        _, h = self.register(); self.join(h)
        f = self.save(h)
        def update(content):
            return self.app.test_client(use_cookies=False).put('/api/club/files/'+f['id'],
                headers=h,json={'base_version':1,'content':content}).status_code
        with ThreadPoolExecutor(max_workers=2) as pool:
            statuses = list(pool.map(update,['candidate A','candidate B']))
        self.assertEqual(sorted(statuses),[200,409])
        self.assertEqual(len(self.client.get('/api/club/files/'+f['id']+'/versions',headers=h).json['versions']),2)

    def test_quota_counts_history_and_concurrent_creates(self):
        self.app.config.update(CLUB_MEMBER_BYTES=10,CLUB_GLOBAL_BYTES=10)
        _, h = self.register(); self.join(h)
        f = self.save(h,'123456')
        r = self.client.put('/api/club/files/'+f['id'],headers=h,json={'base_version':1,'content':'12345'})
        self.assertEqual(r.status_code,429)
        self.app.config.update(CLUB_MEMBER_BYTES=1000,CLUB_GLOBAL_BYTES=1000,CLUB_MAX_FILES=2)
        def save(_):
            return self.app.test_client(use_cookies=False).post('/api/club/files',headers=h,
                json={'request_id':secrets.token_hex(16),'name':'x','content':'x'}).status_code
        with ThreadPoolExecutor(max_workers=2) as pool:
            statuses = list(pool.map(save,range(2)))
        self.assertEqual(sorted(statuses),[201,429])

    def test_invalid_inputs_origin_and_bounded_content(self):
        _, h = self.register(); self.join(h)
        for extra, expected in [({'name':'../../secret'},400),({'name':'a\x00'},400),
                ({'content':'🐑'*16385},413),({'request_id':'bad'},400),
                ({'content':{'json':'use text instead'}},400),({'content':'\ud800'},400)]:
            value={'request_id':secrets.token_hex(16),'name':'x','content':'text',**extra}
            self.assertEqual(self.client.post('/api/club/files',headers=h,json=value).status_code,expected)
        self.assertEqual(self.client.get('/api/club/files?token=not-a-credential',headers=h).status_code,400)
        self.assertEqual(self.client.post('/api/club/join',headers={**h,'Origin':'https://other.invalid'},json={}).status_code,403)
        for value in ({'policy_version':POLICY_VERSION,'data_policy_acknowledged':False},
                      {'policy_version':'wrong','data_policy_acknowledged':True}):
            self.assertEqual(self.client.post('/api/club/join',headers=h,json=value).status_code,400)

    def test_delete_failure_then_success_and_rejoin(self):
        _, h = self.register(); member = self.join(h).json['member']; f = self.save(h)
        path = '/api/club/files/'+f['id']
        with patch('genius_beta.club.record_deletions',side_effect=r2.BackupError('unavailable')):
            response = self.client.delete(path,headers=h,json={'base_version':1,'confirm':True})
        self.assertEqual(response.status_code,503)
        self.assertEqual(self.client.get(path,headers=h).status_code,200)
        self.assertEqual(self.client.delete(path,headers=h,json={'base_version':2,'confirm':True}).status_code,409)
        self.assertEqual(self.client.delete(path,headers=h,json={'base_version':1,'confirm':True}).status_code,204)
        self.assertEqual(self.client.get(path,headers=h).status_code,404)
        self.save(h)
        response = self.client.delete('/api/club/me',headers=h,json={'member_id':member['id'],'confirm':True})
        self.assertEqual(response.status_code,204)
        fresh = self.join(h).json['member']
        self.assertNotEqual(fresh['id'],member['id'])
        self.assertEqual(fresh['agent_id'],member['agent_id'])
        self.assertEqual(self.client.delete('/api/club/me',headers=h,json={'member_id':member['id'],'confirm':True}).status_code,409)
        with contextlib.closing(connect(self.config['DATABASE'])) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM club_file_versions').fetchone()[0],0)
            self.assertEqual(db.execute("SELECT count(*) FROM deletion_ledger WHERE entity_type IN ('club_file','club_member')").fetchone()[0],2)

    def test_account_deletion_and_retention_cascade_to_club(self):
        issued, h = self.register(); self.join(h); self.save(h)
        self.assertEqual(self.client.delete('/api/agents/me',headers=h).status_code,204)
        issued, h = self.register(); self.join(h); self.save(h)
        with contextlib.closing(connect(self.config['DATABASE'])) as db:
            db.execute('UPDATE users SET last_active=0 WHERE id=?',(issued['agent']['id'],))
            purge(db)
            self.assertEqual(db.execute('SELECT count(*) FROM club_members').fetchone()[0],0)
            self.assertEqual(db.execute('SELECT count(*) FROM club_files').fetchone()[0],0)
            self.assertEqual(db.execute('SELECT count(*) FROM club_file_versions').fetchone()[0],0)

    def test_pauses_keep_export_and_deletion_available(self):
        _, h = self.register(); self.join(h); f = self.save(h)
        for setting in ('CLUB_ENABLED','AGENT_ACCESS_ENABLED'):
            self.app.config[setting] = False
            self.assertFalse(self.client.get('/club/manifest.json').json['available'])
            self.assertEqual(self.client.post('/api/club/files',headers=h,json={}).status_code,503)
            self.assertEqual(self.client.get('/api/club/export',headers=h).status_code,200)
            self.app.config[setting] = True
        self.config['SUSPEND_FILE'].touch()
        self.assertEqual(self.client.post('/api/club/files',headers=h,json={}).status_code,503)
        self.assertEqual(self.client.get('/api/club/export',headers=h).status_code,200)
        self.assertEqual(self.client.delete('/api/club/files/'+f['id'],headers=h,json={'base_version':1,'confirm':True}).status_code,204)

    def test_mcp_scope_discovery_and_complete_workspace(self):
        _, h = self.register()
        def rpc(method, params, headers=None):
            return self.client.post('/mcp',headers={**(headers or {}),'Accept':'application/json, text/event-stream'},
                json={'jsonrpc':'2.0','id':1,'method':method,'params':params}).json['result']
        public = rpc('tools/list',{})
        names = {t['name'] for t in public['tools']}
        self.assertIn('club_capabilities',names); self.assertNotIn('club_save_file',names)
        def call(name,args):
            result = rpc('tools/call',{'name':name,'arguments':args},h)
            self.assertFalse(result['isError'],result)
            return result['structuredContent']
        call('club_join',{'policy_version':POLICY_VERSION,'data_policy_acknowledged':True})
        f = call('club_save_file',{'request_id':secrets.token_hex(16),'name':'mcp.txt','content':'Synthetic'})['file']
        self.assertEqual(call('club_read_file',{'file_id':f['id']})['file']['content'],'Synthetic')
        call('club_update_file',{'file_id':f['id'],'base_version':1,'content':'Updated'})
        exported = call('club_export',{})
        self.assertEqual([v['content'] for v in exported['files'][0]['versions']],['Synthetic','Updated'])
        call('club_delete_file',{'file_id':f['id'],'base_version':2,'confirm':True})
        self.assertEqual(call('club_list_files',{})['files'],[])

    def test_public_contract_matches_routes_and_does_not_leak_private_data(self):
        _, h = self.register(); self.join(h,alias='PRIVATE_ALIAS'); self.save(h,'PRIVATE_CONTENT')
        for path in ('/club','/club/manifest.json','/club/openapi.json','/agents','/agents/manifest.json','/llms.txt'):
            response = self.client.get(path)
            self.assertEqual(response.status_code,200,path)
            self.assertNotIn('PRIVATE_ALIAS',response.get_data(as_text=True))
            self.assertNotIn('PRIVATE_CONTENT',response.get_data(as_text=True))
            response.close()
        with self.client.get('/club/openapi.json') as response:
            spec = response.json
        import re
        routes = {(re.sub(r'<[^>]+>','{}',r.rule), m) for r in self.app.url_map.iter_rules() for m in r.methods}
        for path, ops in spec['paths'].items():
            for method in ops:
                self.assertIn((re.sub(r'\{[^}]+\}','{}',path),method.upper()),routes)

    def test_remote_restore_keeps_originals_but_honors_later_erasures(self):
        from test_r2_backup import ObjectStore
        store, key = ObjectStore(), os.urandom(32)
        _, a = self.register(); self.join(a)
        erased = self.save(a,'erase original'); kept = self.save(a,'keep original')
        _, b = self.register(); membership = self.join(b).json['member']; self.save(b,'erase member')
        receipt = r2.backup_once(self.config['DATABASE'],self.config['DATA_DIR']/'status.json',store,key)
        def durable(rows): r2.record_deletions(rows,store,key)
        with patch('genius_beta.club.record_deletions',side_effect=durable):
            self.assertEqual(self.client.delete('/api/club/files/'+erased['id'],headers=a,json={'base_version':1,'confirm':True}).status_code,204)
            self.assertEqual(self.client.delete('/api/club/me',headers=b,json={'member_id':membership['id'],'confirm':True}).status_code,204)
        output = self.config['DATA_DIR']/'restored'
        r2.recover(store,key,receipt['object_key'],output,True)
        with contextlib.closing(sqlite3.connect(output/'genius.sqlite3')) as db:
            self.assertEqual(db.execute('SELECT id FROM club_files').fetchall(),[(kept['id'],)])
            self.assertEqual(db.execute('SELECT content FROM club_file_versions').fetchall(),[('keep original',)])
            self.assertEqual(db.execute('SELECT count(*) FROM api_tokens').fetchone()[0],0)
        self.assertTrue((output/'SUSPENDED').exists())


if __name__ == '__main__':
    unittest.main()
