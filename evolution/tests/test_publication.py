import base64
from copy import deepcopy
import io
import urllib.error
import unittest
from test_evolution import Fixture, BASE
from genius_evolution import pipeline
from genius_evolution.github import Publisher, NoRedirect


class FakeAPI:
    def __init__(self):
        self.main=BASE; self.branch=None; self.files={}; self.pulls=[]; self.calls=[]
        self.lose_branch_reply=False; self.lose_pr_reply=False; self.block_pr=False; self.reject_ref=False
        self.parent=BASE; self.extra_file=False; self.base_manifest=None

    def __call__(self,path,method='GET',body=None):
        self.calls.append((path,method,body))
        if path=='/git/ref/heads/main':return {'object':{'sha':self.main}}
        if path.startswith('/git/ref/heads/'):
            if self.branch:return {'object':{'sha':self.branch}}
            raise urllib.error.HTTPError(path,404,'missing',{},io.BytesIO())
        if path.startswith('/git/commits/') and method=='GET':return {'tree':{'sha':'b'*40},'parents':[{'sha':self.parent}]}
        if path.startswith('/compare/'):
            names=list(self.files)+(['beta/genius_beta/app.py'] if self.extra_file else [])
            return {'total_commits':1,'files':[{'filename':p} for p in names]}
        if path=='/git/trees':
            self.files={r['path']:r['content'] for r in body['tree']}; return {'sha':'c'*40}
        if path=='/git/commits':return {'sha':'d'*40}
        if path=='/git/refs':
            if self.reject_ref:raise urllib.error.HTTPError(path,422,'rejected',{},io.BytesIO())
            self.branch=body['sha']
            if self.lose_branch_reply:self.lose_branch_reply=False; raise TimeoutError()
            return {'ref':body['ref'],'object':{'sha':self.branch}}
        if path.startswith('/contents/'):
            name=path[len('/contents/'):].split('?')[0]
            value=self.base_manifest if name=='PUBLICATION_MANIFEST.json' and path.endswith(BASE) else self.files[name]
            return {'encoding':'base64','content':base64.b64encode(value.encode()).decode()}
        if path.startswith('/pulls?'):return self.pulls
        if path=='/pulls' and method=='POST':
            if self.block_pr:raise urllib.error.HTTPError(path,403,'not allowed',{},io.BytesIO())
            pull=dict(number=101,html_url='https://github.com/example/pull/101',state='open',draft=body['draft'])
            self.pulls=[pull]
            if self.lose_pr_reply:self.lose_pr_reply=False; raise TimeoutError()
            return pull
        raise AssertionError((path,method))


class PublicationTests(Fixture):
    def setUp(self):
        super().setUp(); self.bundle=pipeline.prepare(self.root,BASE); self.api=FakeAPI()
        self.api.base_manifest=(self.root/'PUBLICATION_MANIFEST.json').read_text()
        self.publisher=Publisher(self.root,self.api)

    def test_publishes_draft_without_modifying_main_or_deploying(self):
        r=self.publisher.publish(self.bundle)
        self.assertEqual(r['status'],'PUBLISHED'); self.assertTrue(r['draft'])
        self.assertEqual(r['decision'],'REJECTED_BY_EVALUATION')
        self.assertFalse(r['production_activated']); self.assertEqual(self.api.main,BASE)
        writes=[(p,m) for p,m,b in self.api.calls if m!='GET']
        self.assertEqual(writes,[('/git/trees','POST'),('/git/commits','POST'),('/git/refs','POST'),('/pulls','POST')])

    def test_lost_branch_and_pr_responses_resume_without_duplicate_writes(self):
        for point in ('lose_branch_reply','lose_pr_reply'):
            api=FakeAPI(); setattr(api,point,True); publisher=Publisher(self.root,api)
            api.base_manifest=(self.root/'PUBLICATION_MANIFEST.json').read_text()
            with self.assertRaises(TimeoutError):publisher.publish(self.bundle)
            r=publisher.publish(self.bundle); self.assertTrue(r['reused']); self.assertEqual(r['status'],'PUBLISHED')
            self.assertEqual(sum(p=='/git/refs' and m=='POST' for p,m,b in api.calls),1)
            self.assertEqual(sum(p=='/pulls' and m=='POST' for p,m,b in api.calls),1)

    def test_closed_review_is_not_reopened_and_advanced_main_does_not_rewrite_history(self):
        self.publisher.publish(self.bundle); self.api.pulls[0]['state']='closed'; self.api.main='f'*40
        next_bundle=pipeline.prepare(self.root,'f'*40)
        count=len(self.api.calls); r=self.publisher.publish(next_bundle)
        self.assertEqual(r['review_state'],'closed'); self.assertEqual(r['evaluated_base'],BASE)
        self.assertTrue(all(m=='GET' for p,m,b in self.api.calls[count:]))

    def test_main_moved_aborts_before_any_write(self):
        self.api.main='f'*40
        with self.assertRaisesRegex(ValueError,'MAIN_MOVED'):self.publisher.publish(self.bundle)
        self.assertTrue(all(m=='GET' for p,m,b in self.api.calls))

    def test_changed_existing_branch_is_never_force_pushed(self):
        self.publisher.publish(self.bundle)
        name=next(p for p in self.api.files if p.endswith('.py')); self.api.files[name]+='\n'
        count=len(self.api.calls)
        with self.assertRaisesRegex(ValueError,'EXISTING_SOURCE_CHANGED'):self.publisher.publish(self.bundle)
        self.assertTrue(all(m=='GET' for p,m,b in self.api.calls[count:]))

    def test_pr_permission_block_preserves_branch_and_does_not_try_another_identity(self):
        self.api.block_pr=True; r=self.publisher.publish(self.bundle)
        self.assertEqual(r['status'],'BRANCH_PUBLISHED_PR_BLOCKED'); self.assertEqual(r['http_status'],403)
        self.assertIsNotNone(self.api.branch); self.assertEqual(self.api.main,BASE)
        self.assertTrue(all('/settings' not in p and '/merge' not in p for p,m,b in self.api.calls))

    def test_ref_rejection_does_not_recurse_or_force_push(self):
        self.api.reject_ref=True
        with self.assertRaisesRegex(ValueError,'BRANCH_CREATION_REJECTED'):self.publisher.publish(self.bundle)
        self.assertEqual(sum(p=='/git/refs' and m=='POST' for p,m,b in self.api.calls),1)

    def test_added_runtime_file_or_changed_parent_is_not_accepted_as_a_retry(self):
        self.publisher.publish(self.bundle)
        self.api.extra_file=True
        with self.assertRaisesRegex(ValueError,'EXISTING_SCOPE_CHANGED'):self.publisher.publish(self.bundle)
        self.api.extra_file=False; self.api.parent='e'*40
        with self.assertRaisesRegex(ValueError,'EXISTING_BASE_CHANGED'):self.publisher.publish(self.bundle)

    def test_forged_bundle_cannot_write_files_or_trigger_network(self):
        bad=deepcopy(self.bundle); bad['files']['.github/workflows/attack.yml']='attack'
        with self.assertRaisesRegex(ValueError,'BUNDLE_RECOMPUTATION'):self.publisher.publish(bad)
        self.assertEqual(self.api.calls,[])
        with self.assertRaisesRegex(ValueError,'GITHUB_REDIRECT_REFUSED'):NoRedirect().redirect_request(None)


if __name__=='__main__':unittest.main()
