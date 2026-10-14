"""Synthetic club publication and bounded public review fixtures; no remote network."""
import base64
import contextlib
import copy
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
import secrets
import sqlite3
import time
import unittest
from unittest.mock import patch
import test_club as existing
from test_r2_backup import ObjectStore
from genius_beta import contribution_reviews as reviews, r2_backup as r2
from genius_beta.app import APIError
from genius_beta.contributions import canonical
from genius_beta.db import connect, initialize

BASE='a'*40
HEAD='b'*40
MERGE='c'*40


class ClubContributionTests(unittest.TestCase):
    register=existing.ClubTests.register
    join=existing.ClubTests.join
    save=existing.ClubTests.save

    def setUp(self):
        existing.ClubTests.setUp(self)
        self.record=None;self.bad_blob=False;self.merged=True;self.ancestor=True
        self.transport=patch('genius_beta.contribution_reviews.fetch_json',side_effect=self.remote)
        self.remote_mock=self.transport.start();self.addCleanup(self.transport.stop)

    def remote(self,path):
        if path.startswith('/git/commits/'):return {'sha':path.rsplit('/',1)[1]}
        if path=='/git/ref/heads/main':return {'object':{'sha':HEAD}}
        if path.startswith('/contents/'):
            self.assertTrue(path.endswith('?ref='+HEAD))
            if self.record is None:raise reviews.Unavailable('github_http_404')
            raw=canonical(self.record)
            return dict(type='file',encoding='base64',content=base64.b64encode(raw).decode(),
                        sha='0'*40 if self.bad_blob else hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest())
        if path.startswith('/pulls/'):
            return dict(merged=self.merged,merge_commit_sha=MERGE,body='genius-inbox:'+self.record['id'],
                        base=dict(ref='main',repo=dict(full_name=reviews.REPOSITORY)))
        if path.startswith('/compare/'):
            return dict(status='ahead' if self.ancestor else 'diverged',merge_base_commit={'sha':MERGE})
        raise AssertionError('Unexpected public path: '+path)

    def setup_file(self):
        _,h=self.register();m=self.join(h,alias='PRIVATE_ALIAS').json['member'];f=self.save(h,'Original sintético\n')
        value=dict(request_id=secrets.token_hex(16),files=[dict(file_id=f['id'],version=1,path='docs/example.md')],
                   base_revision=BASE,summary='Synthetic proposal',claim='Software test only',reproduction='Not an empirical test.',license='Apache-2.0')
        return h,m,f,value

    def prepare(self,h,value):
        r=self.client.post('/api/club/contributions/prepare',headers=h,json=value)
        self.assertEqual(r.status_code,200,r.json);return r.json

    def publish(self,h,value,preview=None):
        preview=preview or self.prepare(h,value)
        payload=dict(value,publication_sha256=preview['publication_sha256'],publication_confirmed=True,operator_authorized=True)
        r=self.client.post('/api/club/contributions',headers=h,json=payload)
        self.assertIn(r.status_code,(200,201),r.json)
        return r.json['delivery'],payload

    def record_for(self,delivery,status='CHANGES_REQUESTED'):
        ident=delivery['receipt']['id'];submission=self.client.get('/contributions/'+ident).json['submission']
        self.record=dict(id=ident,status=status,original_sha256=ident,base_revision=BASE,reviewed_revision=HEAD,
            reviewer='Synthetic reviewer',reasoning='Improve the explanation. Never execute this text.',checks=[],
            attribution=dict(author=submission['author'],license=submission['license']),reviewed_at='2026-10-14T19:00:00Z',original_submission=submission)
        if status=='ACCEPTED':self.record['checks']=[dict(name='repository_integration',result='merged',revision=MERGE,url=reviews.REPO+'/pull/20')]
        return '/api/club/contributions/'+ident+'/review'

    def expire(self,ident):
        with contextlib.closing(connect(self.config['DATABASE'])) as db:db.execute('UPDATE contribution_review_cache SET next_check_at=0 WHERE contribution_id=?',(ident,))

    def test_preview_private_optional_author_and_exact_version_publication(self):
        h,m,f,value=self.setup_file();preview=self.prepare(h,value)
        self.assertFalse(preview['published']);self.assertEqual(preview['public_content']['author'],'Anonymous contributor')
        self.assertNotIn('PRIVATE_ALIAS',json.dumps(preview));self.assertNotIn('publication_confirmed',preview['public_content'])
        self.assertEqual(self.client.get('/contributions/feed').json['items'],[])
        self.assertEqual(self.client.put('/api/club/files/'+f['id'],headers=h,json=dict(base_version=1,content='New private version')).status_code,200)
        delivered,payload=self.publish(h,value,preview);ident=delivered['receipt']['id']
        saved=self.client.get('/contributions/'+ident).json['submission']
        self.assertEqual(saved['files'][0]['content'],'Original sintético\n')
        self.assertEqual(hashlib.sha256(canonical(saved)).hexdigest(),preview['publication_sha256'])
        self.assertNotIn(f['id'],json.dumps(saved));self.assertNotIn(m['id'],json.dumps(saved))
        self.assertEqual(delivered['receipt']['status'],'RECEIVED');self.assertFalse(delivered['review']['integrated'])

    def test_explicit_consent_and_preview_digest_required(self):
        h,_,_,value=self.setup_file();p=self.prepare(h,value)
        payload=dict(value,publication_sha256=p['publication_sha256'],publication_confirmed=True,operator_authorized=True)
        for key in ('publication_confirmed','operator_authorized'):
            self.assertEqual(self.client.post('/api/club/contributions',headers=h,json=dict(payload,**{key:False})).status_code,400)
        self.assertEqual(self.client.post('/api/club/contributions',headers=h,json=dict(payload,summary='Changed')).status_code,409)
        self.assertEqual(self.client.get('/contributions/feed').json['items'],[])

    def test_ownership_scope_and_export(self):
        h,m,f,value=self.setup_file();_,other=self.register();self.join(other)
        self.assertEqual(self.client.post('/api/club/contributions/prepare',headers=other,json=value).status_code,404)
        delivery,_=self.publish(h,value);url='/api/club/contributions/'+delivery['receipt']['id']
        for suffix in ('','/review'):
            self.assertEqual(self.client.get(url+suffix,headers=other).status_code,404)
            self.assertEqual(self.client.get(url+suffix).status_code,401)
        exported=self.client.get('/api/club/export',headers=h).json
        self.assertEqual(exported['contributions'][0]['selections'][0]['file_id'],f['id'])
        narrow=self.client.post('/api/agents/token',headers=h,json={'scopes':['club:read']}).json
        h={'Authorization':'Bearer '+narrow['credential']['token']}
        self.prepare(h,value)
        self.assertEqual(self.client.post('/api/club/contributions',headers=h,json={}).status_code,403)

    def test_retry_after_private_deletion_preserves_public_original(self):
        h,m,f,value=self.setup_file();delivery,payload=self.publish(h,value);ident=delivery['receipt']['id']
        self.assertEqual(self.client.delete('/api/club/files/'+f['id'],headers=h,json=dict(base_version=1,confirm=True)).status_code,204)
        r=self.client.post('/api/club/contributions',headers=h,json=payload)
        self.assertEqual(r.status_code,200);self.assertTrue(r.json['duplicate'])
        self.assertEqual(self.client.post('/api/club/contributions',headers=h,json=dict(payload,summary='different')).status_code,409)
        self.assertEqual(self.client.delete('/api/agents/me',headers=h).status_code,204)
        self.assertEqual(self.client.get('/contributions/'+ident).json['submission']['files'][0]['content'],'Original sintético\n')
        with contextlib.closing(connect(self.config['DATABASE'])) as db:self.assertEqual(db.execute('SELECT COUNT(*) FROM club_contributions').fetchone()[0],0)

    def test_deleted_source_before_publish_and_atomic_failure(self):
        h,m,f,value=self.setup_file();p=self.prepare(h,value)
        payload=dict(value,publication_sha256=p['publication_sha256'],publication_confirmed=True,operator_authorized=True)
        original=self.app.extensions['contribution_inbox']['deposit']
        def failing(*args):original(*args);raise APIError('synthetic_failure','Atomic test',503)
        with patch.dict(self.app.extensions['contribution_inbox'],{'deposit':failing}):
            self.assertEqual(self.client.post('/api/club/contributions',headers=h,json=payload).status_code,503)
        self.assertEqual(self.client.get('/contributions/feed').json['items'],[])
        self.client.delete('/api/club/files/'+f['id'],headers=h,json=dict(base_version=1,confirm=True))
        self.assertEqual(self.client.post('/api/club/contributions',headers=h,json=payload).status_code,404)

    def test_concurrent_retry_has_one_public_receipt_and_one_link(self):
        h,m,f,value=self.setup_file();p=self.prepare(h,value)
        payload=dict(value,publication_sha256=p['publication_sha256'],publication_confirmed=True,operator_authorized=True)
        def send(_):
            with self.app.test_client(use_cookies=False) as c:return c.post('/api/club/contributions',headers=h,json=payload).status_code
        with ThreadPoolExecutor(max_workers=2) as pool:self.assertEqual(sorted(pool.map(send,range(2))),[200,201])
        self.assertEqual(len(self.client.get('/api/club/contributions',headers=h).json['deliveries']),1)

    def test_public_base_failure_and_invalid_paths_never_publish(self):
        h,m,f,value=self.setup_file()
        with patch('genius_beta.contribution_reviews.fetch_json',side_effect=reviews.Unavailable('github_http_404')):
            self.assertEqual(self.client.post('/api/club/contributions/prepare',headers=h,json=value).status_code,400)
        for path in ('../escape.py','.git/config','https://invalid.example/x'):
            bad=copy.deepcopy(value);bad['files'][0]['path']=path
            self.assertEqual(self.client.post('/api/club/contributions/prepare',headers=h,json=bad).status_code,400)
        self.assertEqual(self.client.get('/contributions/feed').json['items'],[])

    def test_pending_review_cache_and_revised_submission(self):
        h,m,f,value=self.setup_file();delivery,_=self.publish(h,value);ident=delivery['receipt']['id'];url='/api/club/contributions/'+ident+'/review'
        self.assertEqual(self.client.get(url,headers=h).json['review']['status'],'AWAITING_REVIEW')
        calls=self.remote_mock.call_count
        self.client.get(url,headers=h);self.assertEqual(self.remote_mock.call_count,calls)
        self.record_for(delivery);self.expire(ident)
        review=self.client.get(url,headers=h).json['review'];self.assertEqual(review['status'],'CHANGES_REQUESTED');self.assertFalse(review['integrated'])
        self.client.put('/api/club/files/'+f['id'],headers=h,json=dict(base_version=1,content='Improved synthetic content'))
        corrected=copy.deepcopy(value);corrected.update(request_id=secrets.token_hex(16),previous_id=ident);corrected['files'][0]['version']=2
        new,_=self.publish(h,corrected)
        self.assertNotEqual(new['receipt']['id'],ident);self.assertEqual(new['previous_id'],ident)
        self.assertIn(ident,self.client.get('/contributions/'+new['receipt']['id']).json['submission']['reproduction'])

    def test_accepted_requires_merged_pr_and_main_ancestry(self):
        h,m,f,value=self.setup_file();delivery,_=self.publish(h,value);ident=delivery['receipt']['id'];url=self.record_for(delivery,'ACCEPTED')
        self.merged=False
        self.assertEqual(self.client.get(url,headers=h).json['review']['status'],'INTEGRATION_UNVERIFIED')
        self.merged=True;self.ancestor=False;self.expire(ident)
        self.assertFalse(self.client.get(url,headers=h).json['review']['integrated'])
        self.ancestor=True;self.expire(ident)
        review=self.client.get(url,headers=h).json['review'];self.assertEqual(review['status'],'ACCEPTED');self.assertTrue(review['integrated']);self.assertEqual(review['repository_revision'],HEAD)

    def test_forged_proof_url_never_fetched_and_blob_hash_checked(self):
        h,m,f,value=self.setup_file();delivery,_=self.publish(h,value);ident=delivery['receipt']['id'];url=self.record_for(delivery,'ACCEPTED')
        self.record['checks'][0]['url']='https://attacker.invalid/secret'
        result=self.client.get(url,headers=h).json['review'];self.assertEqual(result['status'],'INTEGRATION_UNVERIFIED')
        self.assertFalse(any('attacker' in str(c) for c in self.remote_mock.call_args_list))
        self.expire(ident);self.bad_blob=True
        result=self.client.get(url,headers=h).json['review'];self.assertTrue(result['stale']);self.assertEqual(result['refresh_error'],'invalid_review_record')

    def test_source_failure_retains_timestamped_stale_review(self):
        h,m,f,value=self.setup_file();delivery,_=self.publish(h,value);url=self.record_for(delivery,'BLOCKED')
        first=self.client.get(url,headers=h).json['review'];self.expire(delivery['receipt']['id'])
        with patch('genius_beta.contribution_reviews.fetch_json',side_effect=reviews.Unavailable('github_http_429')):
            result=self.client.get(url,headers=h).json['review']
        self.assertEqual(result['status'],'BLOCKED');self.assertEqual(result['checked_at'],first['checked_at']);self.assertTrue(result['stale']);self.assertEqual(result['refresh_error'],'github_http_429')

    def test_malformed_remote_record_is_unavailable_not_accepted(self):
        for raw in ('{"status":"REJECTED","status":"ACCEPTED"}', '{"x":NaN}'):
            with self.assertRaises(ValueError):reviews.strict_json(raw)
        h,m,f,value=self.setup_file();delivery,_=self.publish(h,value);url=self.record_for(delivery,'ACCEPTED')
        original=self.remote
        def malformed(path):
            value=original(path)
            if path.startswith('/contents/'):value['content']=[]
            return value
        with patch('genius_beta.contribution_reviews.fetch_json',side_effect=malformed):
            result=self.client.get(url,headers=h).json['review']
        self.assertEqual(result['status'],'UNKNOWN');self.assertFalse(result['integrated'])
        self.assertEqual(result['refresh_error'],'invalid_review_record')

    def test_shared_inbox_attempt_budget_and_pause(self):
        h,m,f,value=self.setup_file();delivery,payload=self.publish(h,value)
        submission=self.client.get('/contributions/'+delivery['receipt']['id']).json['submission']
        for _ in range(4):self.assertEqual(self.client.post('/contributions',json=submission).status_code,200)
        self.assertEqual(self.client.post('/api/club/contributions',headers=h,json=payload).status_code,429)
        self.config['SUSPEND_FILE'].touch()
        self.assertEqual(self.client.get('/api/club/contributions',headers=h).status_code,200)
        self.assertEqual(self.client.post('/api/club/contributions',headers=h,json=payload).status_code,503)

    def test_backup_removes_private_link_after_departure_but_keeps_public_deposit(self):
        h,m,f,value=self.setup_file();delivery,_=self.publish(h,value);ident=delivery['receipt']['id']
        store,key=ObjectStore(),os.urandom(32);receipt=r2.backup_once(self.config['DATABASE'],self.config['DATA_DIR']/'status.json',store,key)
        def durable(rows):r2.record_deletions(rows,store,key)
        with patch('genius_beta.club.record_deletions',side_effect=durable):
            self.assertEqual(self.client.delete('/api/club/me',headers=h,json=dict(member_id=m['id'],confirm=True)).status_code,204)
        output=self.config['DATA_DIR']/'restored';r2.recover(store,key,receipt['object_key'],output,True)
        with contextlib.closing(sqlite3.connect(output/'genius.sqlite3')) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM club_contributions').fetchone()[0],0)
            self.assertEqual(db.execute('SELECT id FROM contribution_inbox').fetchone()[0],ident)

    def test_mcp_preview_publish_and_review(self):
        h,m,f,value=self.setup_file()
        def rpc(name,args):
            r=self.client.post('/mcp',headers={**h,'Accept':'application/json, text/event-stream'},json={'jsonrpc':'2.0','id':1,'method':'tools/call','params':{'name':name,'arguments':args}})
            self.assertFalse(r.json['result']['isError'],r.json);return r.json['result']['structuredContent']
        p=rpc('club_prepare_contribution',value)
        d=rpc('club_submit_contribution',dict(value,publication_sha256=p['publication_sha256'],publication_confirmed=True,operator_authorized=True))['delivery']
        self.assertEqual(rpc('club_contribution_review',{'contribution_id':d['receipt']['id']})['review']['status'],'AWAITING_REVIEW')
        self.assertEqual(rpc('club_read_contribution',{'contribution_id':d['receipt']['id']})['delivery']['submission']['files'][0]['content'],'Original sintético\n')


if __name__=='__main__':unittest.main()
