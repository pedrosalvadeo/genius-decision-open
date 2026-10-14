"""Synthetic, isolated behavior checks for consent, ownership and recoverable privacy."""
import contextlib
from concurrent.futures import ThreadPoolExecutor
import hashlib
import os
import secrets
import sqlite3
import time
import unittest
from unittest.mock import patch
import test_club as existing
from test_r2_backup import ObjectStore
from genius_beta import r2_backup as r2
from genius_beta.club_social import POLICY_VERSION
from genius_beta.db import connect, initialize


class ClubSocialTests(unittest.TestCase):
    setUp=existing.ClubTests.setUp
    register=existing.ClubTests.register
    join=existing.ClubTests.join
    save=existing.ClubTests.save

    def agent(self, enabled=True, public=False, **extra):
        issued,h=self.register();m=self.join(h,alias='PRIVATE_ALIAS').json['member']
        if enabled:self.configure(h,directory_visible=public,**extra)
        return m,h

    def configure(self,h,base=0,**extra):
        value=dict(base_version=base,policy_version=POLICY_VERSION,data_policy_acknowledged=True,
                   directory_visible=False,accept_requests=True,**{})
        value.update(extra)
        if value['directory_visible']:value.update(publication_confirmed=True,operator_authorized=True)
        r=self.client.put('/api/club/social',headers=h,json=value)
        self.assertEqual(r.status_code,200,r.json)
        return r.json['profile']

    def request(self,a,b,**extra):
        value=dict(recipient_id=b['id'],request_id=secrets.token_hex(16),topic='Revisión sintética');value.update(extra)
        r=self.client.post('/api/club/conversations',headers=a,json=value)
        self.assertEqual(r.status_code,201,r.json)
        return r.json['conversation']

    def accept(self,h,c):
        r=self.client.post('/api/club/conversations/'+c['id']+'/respond',headers=h,json={'action':'accept','base_version':c['version']})
        self.assertEqual(r.status_code,200,r.json);return r.json['conversation']

    def message(self,h,c,content='Hola sintético',rid=None):
        return self.client.post('/api/club/conversations/'+c['id']+'/messages',headers=h,
            json={'request_id':rid or secrets.token_hex(16),'content':content})

    def test_opt_in_publication_and_private_alias_separation(self):
        m,h=self.agent(enabled=False)
        self.assertEqual(self.client.get('/club/directory.json').json['members'],[])
        value=dict(base_version=0,policy_version=POLICY_VERSION,data_policy_acknowledged=True,directory_visible=True,accept_requests=True)
        self.assertEqual(self.client.put('/api/club/social',headers=h,json=value).status_code,400)
        self.configure(h,directory_visible=True,summary='Ayuda con datos',capabilities=['CSV'])
        r=self.client.get('/club/directory.json');self.assertEqual(r.headers['Cache-Control'],'no-store')
        self.assertIsNone(r.json['members'][0]['public_name']);self.assertNotIn('PRIVATE_ALIAS',r.text)
        self.assertNotIn(m['agent_id'],r.text);self.assertEqual(r.json['members'][0]['verification'],'self_declared')
        self.configure(h,base=1,directory_visible=False)
        self.assertEqual(self.client.get('/club/directory.json').json['members'],[])
        bad=dict(value,base_version=1,directory_visible=False)
        self.assertEqual(self.client.put('/api/club/social',headers=h,json=bad).status_code,409)

    def test_recipient_consent_and_third_party_isolation(self):
        a,ha=self.agent();b,hb=self.agent();c,hc=self.agent()
        conv=self.request(ha,b);url='/api/club/conversations/'+conv['id']
        self.assertEqual(self.message(ha,conv).status_code,409)
        self.assertEqual(self.client.post(url+'/respond',headers=ha,json={'action':'accept','base_version':1}).status_code,403)
        self.assertEqual(self.client.get(url,headers=hc).status_code,404)
        self.assertEqual(self.client.delete(url,headers=hc,json={'base_version':1,'confirm':True}).status_code,404)
        conv=self.accept(hb,conv)
        self.assertEqual(self.message(ha,conv).status_code,201)
        self.assertEqual(self.message(hc,conv).status_code,404)
        self.assertEqual(self.client.get(url).status_code,401)
        self.assertEqual(self.client.get(url,headers=hb).json['messages'][0]['sender_id'],a['id'])
        public=self.client.get('/club/directory.json').text
        self.assertNotIn('Hola sintético',public)

    def test_request_retries_decline_and_closed_inbox(self):
        a,ha=self.agent();b,hb=self.agent(accept_requests=False)
        value=dict(recipient_id=b['id'],request_id=secrets.token_hex(16),topic='Sintético')
        self.assertEqual(self.client.post('/api/club/conversations',headers=ha,json=value).status_code,404)
        self.configure(hb,base=1,accept_requests=True)
        c=self.client.post('/api/club/conversations',headers=ha,json=value).json['conversation']
        self.assertEqual(self.client.post('/api/club/conversations',headers=ha,json=value).status_code,200)
        self.assertEqual(self.client.post('/api/club/conversations',headers=ha,json={**value,'topic':'Otro'}).status_code,409)
        r=self.client.post('/api/club/conversations/'+c['id']+'/respond',headers=hb,json={'base_version':1,'action':'decline'})
        self.assertEqual(r.status_code,200)
        self.assertEqual(self.message(ha,c).status_code,409)
        self.assertEqual(self.client.post('/api/club/conversations',headers=ha,json={**value,'request_id':secrets.token_hex(16)}).status_code,409)

    def test_original_hashes_idempotence_pagination_and_export(self):
        a,ha=self.agent();b,hb=self.agent();c=self.accept(hb,self.request(ha,b));rid=secrets.token_hex(16)
        text='<script>not executed</script>\nñ🐑\n'
        r=self.message(ha,c,text,rid);self.assertEqual(r.status_code,201,r.json)
        first=r.json['message'];self.assertEqual(first['sha256'],hashlib.sha256(text.encode()).hexdigest())
        self.assertEqual(self.message(ha,c,text,rid).status_code,200)
        self.assertEqual(self.message(ha,c,'changed',rid).status_code,409)
        self.assertEqual(self.message(hb,c,'respuesta').status_code,201)
        url='/api/club/conversations/'+c['id']
        page=self.client.get(url+'?after=0&limit=1',headers=hb).json
        self.assertTrue(page['has_more']);self.assertEqual(page['messages'][0]['content'],text)
        last=self.client.get(url+'?after='+str(page['next_after'])+'&limit=1',headers=hb).json
        self.assertFalse(last['has_more']);self.assertEqual(last['messages'][0]['content'],'respuesta')
        for suffix in ('?limit=0','?after=-1','?after=0&after=1','?bogus=1'):
            self.assertEqual(self.client.get(url+suffix,headers=ha).status_code,400)
        exported=self.client.get('/api/club/export',headers=ha).json
        self.assertEqual(exported['social']['conversations'][0]['messages'][0]['content'],text)
        self.assertEqual(self.client.delete(url,headers=ha,json={'base_version':2,'confirm':True}).status_code,409)
        version=last['conversation']['version']
        self.assertEqual(self.client.delete(url,headers=ha,json={'base_version':version,'confirm':True}).status_code,204)
        self.assertEqual(self.client.get(url,headers=hb).status_code,404)

    def test_atomic_same_message_retry_and_shared_storage_budget(self):
        a,ha=self.agent();b,hb=self.agent();c=self.accept(hb,self.request(ha,b));rid=secrets.token_hex(16)
        def send(_):
            with self.app.test_client(use_cookies=False) as client:
                return client.post('/api/club/conversations/'+c['id']+'/messages',headers=ha,json={'request_id':rid,'content':'same'}).status_code
        with ThreadPoolExecutor(max_workers=2) as pool:self.assertEqual(sorted(pool.map(send,range(2))),[200,201])
        self.app.config['CLUB_GLOBAL_BYTES']=7
        self.assertEqual(self.message(hb,c,'1234').status_code,429)
        r=self.client.post('/api/club/files',headers=ha,json={'request_id':secrets.token_hex(16),'name':'x','content':'1234'})
        self.assertEqual(r.status_code,429)
        self.assertEqual(self.message(hb,c,'x'*8193).status_code,413)

    def test_block_requires_delete_scope_erases_pair_and_survives_pause(self):
        a,ha=self.agent();b,hb=self.agent();c=self.accept(hb,self.request(ha,b));self.message(ha,c)
        rotated=self.client.post('/api/agents/token',headers=ha,json={'scopes':['club:read','club:write']}).json
        narrow={'Authorization':'Bearer '+rotated['credential']['token']}
        self.assertEqual(self.client.post('/api/club/blocks',headers=narrow,json={'member_id':b['id'],'confirm':True}).status_code,403)
        self.config['SUSPEND_FILE'].touch();self.app.config['AGENT_ACCESS_ENABLED']=False
        r=self.client.post('/api/club/blocks',headers=hb,json={'member_id':a['id'],'confirm':True})
        self.assertEqual(r.status_code,200,r.json)
        self.assertEqual(self.client.get('/api/club/conversations',headers=hb).json['conversations'],[])
        self.app.config['AGENT_ACCESS_ENABLED']=True;self.config['SUSPEND_FILE'].unlink()
        self.assertEqual(self.client.post('/api/club/conversations',headers=narrow,json={'recipient_id':b['id'],'request_id':secrets.token_hex(16),'topic':'retry'}).status_code,404)
        self.assertEqual(self.client.get('/api/club/blocks',headers=hb).json['blocks'][0]['blocked_id'],a['id'])

    def test_expiry_disable_and_account_erasure(self):
        a,ha=self.agent(public=True);b,hb=self.agent();c=self.accept(hb,self.request(ha,b));self.message(ha,c)
        r=self.client.delete('/api/club/social',headers=ha,json={'base_version':1,'confirm':True})
        self.assertEqual(r.status_code,204)
        self.assertEqual(self.message(hb,c).status_code,409)
        self.assertEqual(self.client.get('/club/directory.json').json['members'],[])
        self.assertEqual(self.client.get('/api/club/export',headers=ha).status_code,200)
        self.assertEqual(self.client.delete('/api/agents/me',headers=ha).status_code,204)
        self.assertEqual(self.client.get('/api/club/conversations',headers=hb).json['conversations'],[])
        self.configure(hb,base=1,directory_visible=True)
        with contextlib.closing(connect(self.config['DATABASE'])) as db:db.execute('UPDATE users SET last_active=0 WHERE id=?',(b['agent_id'],))
        self.assertEqual(self.client.get('/club/directory.json').json['members'],[])

    def test_backup_failures_do_not_confirm_privacy_changes(self):
        a,ha=self.agent(public=True);b,hb=self.agent();c=self.accept(hb,self.request(ha,b));self.message(ha,c)
        with patch('genius_beta.club.record_deletions',side_effect=r2.BackupError('R2_UPLOAD_FAILED')):
            self.assertEqual(self.client.delete('/api/club/social',headers=ha,json={'base_version':1,'confirm':True}).status_code,503)
            self.assertEqual(self.client.get('/club/directory.json').json['members'][0]['member_id'],a['id'])
        with patch('genius_beta.club_social.record_deletions',side_effect=r2.BackupError('R2_UPLOAD_FAILED')):
            self.assertEqual(self.client.post('/api/club/blocks',headers=hb,json={'member_id':a['id'],'confirm':True}).status_code,503)
        self.assertEqual(len(self.client.get('/api/club/conversations',headers=hb).json['conversations']),1)

    def test_offline_remote_restore_honors_later_block_and_hides_profiles(self):
        a,ha=self.agent(public=True);b,hb=self.agent(public=True);c=self.accept(hb,self.request(ha,b));self.message(ha,c,'erase me')
        store,key=ObjectStore(),os.urandom(32)
        receipt=r2.backup_once(self.config['DATABASE'],self.config['DATA_DIR']/'status.json',store,key)
        def durable(rows):r2.record_deletions(rows,store,key)
        with patch('genius_beta.club_social.record_deletions',side_effect=durable):
            self.assertEqual(self.client.post('/api/club/blocks',headers=hb,json={'member_id':a['id'],'confirm':True}).status_code,200)
        output=self.config['DATA_DIR']/'restored'
        r2.recover(store,key,receipt['object_key'],output,True)
        with contextlib.closing(sqlite3.connect(output/'genius.sqlite3')) as db:
            for table in ('club_messages','club_conversations','club_social_profiles','api_tokens'):
                self.assertEqual(db.execute('SELECT COUNT(*) FROM '+table).fetchone()[0],0,table)
            self.assertEqual(db.execute('SELECT blocker_id,blocked_id FROM club_blocks').fetchall(),[(b['id'],a['id'])])

    def test_offline_restore_honors_conversation_and_profile_erasures(self):
        a,ha=self.agent(public=True);b,hb=self.agent();c=self.accept(hb,self.request(ha,b));self.message(ha,c,'original')
        store,key=ObjectStore(),os.urandom(32)
        receipt=r2.backup_once(self.config['DATABASE'],self.config['DATA_DIR']/'status.json',store,key)
        def durable(rows):r2.record_deletions(rows,store,key)
        with patch('genius_beta.club.record_deletions',side_effect=durable):
            self.assertEqual(self.client.delete('/api/club/conversations/'+c['id'],headers=ha,json={'base_version':3,'confirm':True}).status_code,204)
            self.assertEqual(self.client.delete('/api/club/social',headers=ha,json={'base_version':1,'confirm':True}).status_code,204)
        output=self.config['DATA_DIR']/'restored'
        r2.recover(store,key,receipt['object_key'],output,True)
        with contextlib.closing(sqlite3.connect(output/'genius.sqlite3')) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM club_messages').fetchone()[0],0)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM club_social_profiles').fetchone()[0],0)

    def test_mcp_social_roundtrip_filters_and_polling(self):
        a,ha=self.agent();b,hb=self.agent()
        def rpc(name,args,h):
            r=self.client.post('/mcp',headers={**h,'Accept':'application/json, text/event-stream'},json={'jsonrpc':'2.0','id':1,'method':'tools/call','params':{'name':name,'arguments':args}})
            result=r.json['result'];self.assertFalse(result['isError'],result);return result['structuredContent']
        self.assertEqual(rpc('club_directory',{}, {})['members'],[])
        c=rpc('club_request_conversation',{'recipient_id':b['id'],'request_id':secrets.token_hex(16),'topic':'synthetic'},ha)['conversation']
        rpc('club_respond_conversation',{'conversation_id':c['id'],'base_version':1,'action':'accept'},hb)
        rpc('club_send_message',{'conversation_id':c['id'],'request_id':secrets.token_hex(16),'content':'one'},ha)
        page=rpc('club_read_conversation',{'conversation_id':c['id'],'after':0,'limit':1},hb)
        self.assertEqual(page['messages'][0]['content'],'one')
        self.assertEqual(rpc('club_read_conversation',{'conversation_id':c['id'],'after':page['next_after']},hb)['messages'],[])

    def test_disable_reenable_never_reuses_profile_version(self):
        m,h=self.agent()
        self.assertEqual(self.client.delete('/api/club/social',headers=h,json={'base_version':1,'confirm':True}).status_code,204)
        self.assertEqual(self.client.get('/api/club/social',headers=h).json['profile']['version'],2)
        self.assertEqual(self.configure(h,base=2)['version'],3)
        stale=dict(base_version=1,policy_version=POLICY_VERSION,data_policy_acknowledged=True,directory_visible=False,accept_requests=False)
        self.assertEqual(self.client.put('/api/club/social',headers=h,json=stale).status_code,409)

    def test_v5_upgrade_preserves_files_and_later_remote_block(self):
        a,ha=self.agent(enabled=False);b,hb=self.agent(enabled=False);f=self.save(ha)
        with contextlib.closing(connect(self.config['DATABASE'])) as db:
            db.executescript('DROP TABLE adaptive_missions; DROP TABLE club_contributions; DROP TABLE contribution_review_cache; DROP TABLE contribution_public_revisions; DROP TABLE club_messages; DROP TABLE club_conversations; DROP TABLE club_social_profiles; DROP TABLE club_blocks; ALTER TABLE club_members DROP COLUMN social_version; DELETE FROM schema_migrations WHERE version>="006_club_social.sql";')
        store,key=ObjectStore(),os.urandom(32)
        receipt=r2.backup_once(self.config['DATABASE'],self.config['DATA_DIR']/'status.json',store,key)
        initialize(self.config['DATABASE'])
        self.assertEqual(self.client.get('/api/club/files/'+f['id'],headers=ha).json['file']['content'],f['content'])
        self.assertEqual(self.client.get('/api/club/social',headers=ha).json['profile']['version'],0)
        r2.record_deletions([(b['id']+'_'+a['id'],'club_contact_block',int(time.time()))],store,key)
        output=self.config['DATA_DIR']/'restored-v5'
        r2.recover(store,key,receipt['object_key'],output,True)
        with contextlib.closing(sqlite3.connect(output/'genius.sqlite3')) as db:
            self.assertEqual(db.execute('SELECT blocker_id,blocked_id FROM club_blocks').fetchall(),[(b['id'],a['id'])])
            self.assertEqual(db.execute('SELECT content FROM club_file_versions WHERE file_id=?',(f['id'],)).fetchone()[0],f['content'])
            self.assertEqual(db.execute('SELECT COUNT(*) FROM schema_migrations').fetchone()[0],8)

    def test_invalid_social_inputs_and_request_quota(self):
        a,ha=self.agent();b,hb=self.agent()
        value=dict(base_version=1,policy_version=POLICY_VERSION,data_policy_acknowledged=True,directory_visible=False,accept_requests=True)
        for extra in ({'capabilities':['x']*11},{'summary':'x\ny'},{'directory_visible':'true'},{'capabilities':[{}]}):
            self.assertEqual(self.client.put('/api/club/social',headers=ha,json={**value,**extra}).status_code,400)
        for _ in range(5):
            r=self.client.post('/api/club/conversations',headers=ha,json={'recipient_id':'f'*32,'request_id':secrets.token_hex(16),'topic':'unknown'})
            self.assertEqual(r.status_code,404)
        r=self.client.post('/api/club/conversations',headers=ha,json={'recipient_id':b['id'],'request_id':secrets.token_hex(16),'topic':'quota'})
        self.assertEqual(r.status_code,429)

if __name__=='__main__':unittest.main()
