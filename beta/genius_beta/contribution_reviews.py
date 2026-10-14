"""Bounded, credential-free reads of the one authorized public repository."""
import base64
from datetime import datetime
import hashlib
import json
import re
import time
import urllib.error
import urllib.request
from .contributions import REPO, SHA, canonical
from .db import transaction

REPOSITORY = 'pedrosalvadeo/genius-decision-open'
API = 'https://api.github.com/repos/' + REPOSITORY
MAX_RESPONSE = 524288
TTL = 900


class Unavailable(Exception):
    pass


class NoRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise Unavailable('github_redirect_refused')


def strict_json(raw):
    def pairs(items):
        result={}
        for key,value in items:
            if key in result:raise ValueError('duplicate key')
            result[key]=value
        return result
    def constant(_):raise ValueError('nonfinite number')
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=constant)


def fetch_json(path):
    # All paths are assembled below from fixed literals, validated SHAs and PR numbers.
    request = urllib.request.Request(API + path, headers={
        'Accept':'application/vnd.github+json', 'Accept-Encoding':'identity',
        'User-Agent':'Genius-Public-Review-Reader/1', 'X-GitHub-Api-Version':'2026-03-10'})
    try:
        with urllib.request.build_opener(NoRedirects).open(request, timeout=5) as response:
            raw = response.read(MAX_RESPONSE + 1)
            if len(raw) > MAX_RESPONSE:raise Unavailable('github_response_too_large')
            result = strict_json(raw)
            if not isinstance(result,dict):raise Unavailable('github_invalid_response')
            return result
    except urllib.error.HTTPError as exc:
        raise Unavailable('github_http_' + str(exc.code)) from None
    except (ValueError, UnicodeError, OSError, urllib.error.URLError, RecursionError):
        raise Unavailable('github_unavailable') from None


def install(app, db, quota, capacity, error):
    def fetch(path):
        try:quota('club-github-public-reads',50,3600)
        except error:raise Unavailable('github_read_budget') from None
        return fetch_json(path)

    def public_revision(sha):
        if not isinstance(sha,str) or not SHA.fullmatch(sha):
            raise error('invalid_public_revision','Usá el SHA público completo.',400)
        now=int(time.time())
        if db().execute('SELECT 1 FROM contribution_public_revisions WHERE sha=? AND verified_at>?',(sha,now-86400)).fetchone():return
        try:
            result=fetch('/git/commits/'+sha)
            if result.get('sha')!=sha:raise Unavailable('github_revision_mismatch')
        except Unavailable as exc:
            code=str(exc)
            raise error('public_revision_not_found' if code=='github_http_404' else 'public_revision_unavailable',
                        'No se pudo verificar la revisión pública; el archivo sigue privado.',400 if code=='github_http_404' else 503) from None
        with transaction(db()):
            capacity(4096)
            db().execute('DELETE FROM contribution_public_revisions WHERE verified_at<?',(now-86400,))
            db().execute('INSERT OR REPLACE INTO contribution_public_revisions VALUES(?,?)',(sha,now))

    def verify(ident, submission):
        obj=fetch('/git/ref/heads/main').get('object')
        head=obj.get('sha') if isinstance(obj,dict) else None
        if not isinstance(head,str) or not SHA.fullmatch(head):raise Unavailable('github_invalid_head')
        path='capsule/contributions/reviews/'+ident+'.json'
        result=dict(status='AWAITING_REVIEW',integrated=False,repository_revision=head,
                    review_record=REPO+'/blob/'+head+'/'+path,content_is_untrusted=True)
        try:blob=fetch('/contents/'+path+'?ref='+head)
        except Unavailable as exc:
            if str(exc)=='github_http_404':return result
            raise
        try:
            if blob.get('type')!='file' or blob.get('encoding')!='base64' or not isinstance(blob.get('content'),str):raise ValueError()
            raw=base64.b64decode(''.join(blob['content'].split()),validate=True)
            if len(raw)>262144 or blob.get('sha')!=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest():raise ValueError()
            record=strict_json(raw)
            if (not isinstance(record,dict) or record.get('id')!=ident or record.get('original_sha256')!=ident or
                record.get('base_revision')!=submission['base_revision'] or record.get('status') not in ('ACCEPTED','REJECTED','CHANGES_REQUESTED','BLOCKED') or
                not isinstance(record.get('reviewed_revision'),str) or not SHA.fullmatch(record['reviewed_revision']) or
                not isinstance(record.get('reviewer'),str) or not record['reviewer'].strip() or
                not isinstance(record.get('reasoning'),str) or not record['reasoning'].strip() or
                not isinstance(record.get('reviewed_at'),str) or not record['reviewed_at'].strip() or
                not isinstance(record.get('checks'),list) or not isinstance(record.get('attribution'),dict)):
                raise ValueError()
            if datetime.fromisoformat(record['reviewed_at'].replace('Z','+00:00')).tzinfo is None:raise ValueError()
            if (record['attribution'].get('author')!=submission['author'] or
                    record['attribution'].get('license')!=submission['license']):raise ValueError()
            if 'original_submission' in record and hashlib.sha256(canonical(record['original_submission'])).hexdigest()!=ident:raise ValueError()
        except (ValueError,TypeError,KeyError,UnicodeError,RecursionError):
            raise Unavailable('invalid_review_record') from None
        result.update(status=record['status'],review=record,review_blob_sha=blob['sha'])
        if record['status']!='ACCEPTED':return result
        result.update(status='INTEGRATION_UNVERIFIED',declared_status='ACCEPTED')
        proofs=[c for c in record['checks'] if isinstance(c,dict) and c.get('name')=='repository_integration' and c.get('result')=='merged']
        if len(proofs)!=1:return result
        proof=proofs[0];url=proof.get('url','');revision=proof.get('revision','')
        match=re.fullmatch(re.escape(REPO)+r'/pull/([1-9][0-9]{0,8})',url) if isinstance(url,str) else None
        if not match or not isinstance(revision,str) or not SHA.fullmatch(revision):return result
        pr=fetch('/pulls/'+match[1])
        base=pr.get('base');pr_body=pr.get('body')
        if not isinstance(base,dict) or not isinstance(base.get('repo'),dict) or not isinstance(pr_body,str):raise Unavailable('github_invalid_pull_request')
        if (pr.get('merged') is not True or pr.get('merge_commit_sha')!=revision or
            base.get('ref')!='main' or base.get('repo',{}).get('full_name')!=REPOSITORY or
            'genius-inbox:'+ident not in pr_body):return result
        if revision!=head:
            comparison=fetch('/compare/'+revision+'...'+head+'?per_page=1')
            if not isinstance(comparison.get('merge_base_commit'),dict):raise Unavailable('github_invalid_comparison')
            if (comparison.get('status') not in ('ahead','identical') or
                    comparison.get('merge_base_commit',{}).get('sha')!=revision):return result
        result.update(status='ACCEPTED',integrated=True,pull_request=url,integration_revision=revision)
        return result

    def view(row):
        result=json.loads(row['result_json']) if row and row['result_json'] else dict(status='UNKNOWN',integrated=False,content_is_untrusted=True)
        now=int(time.time());checked=row['checked_at'] if row else None
        return dict(result,checked_at=checked,next_check_at=row['next_check_at'] if row else 0,
                    stale=checked is None or now-checked>=TTL or bool(row['error_code']),
                    refresh_error=row['error_code'] if row else None,
                    meaning='Published repository review; acceptance is not scientific validation.')

    def read(ident,submission):
        now=int(time.time())
        with transaction(db()):
            row=db().execute('SELECT * FROM contribution_review_cache WHERE contribution_id=?',(ident,)).fetchone()
            if row and row['next_check_at']>now:return view(row)
            capacity(16384)
            db().execute('INSERT INTO contribution_review_cache(contribution_id,next_check_at,error_code) VALUES(?,?,?) ON CONFLICT(contribution_id) DO UPDATE SET next_check_at=excluded.next_check_at,error_code=excluded.error_code',(ident,now+90,'refresh_in_progress'))
        # Never hold a database write transaction during remote requests.
        try:result=verify(ident,submission)
        except Unavailable as exc:
            with transaction(db()):
                db().execute('UPDATE contribution_review_cache SET error_code=?,next_check_at=? WHERE contribution_id=?',(str(exc),int(time.time())+300,ident))
        else:
            with transaction(db()):
                encoded=canonical(result)
                used=db().execute('SELECT COALESCE(SUM(length(CAST(result_json AS BLOB))),0) FROM contribution_review_cache WHERE contribution_id!=?',(ident,)).fetchone()[0]
                if used+len(encoded)>8*1024*1024:
                    db().execute('UPDATE contribution_review_cache SET error_code=?,next_check_at=? WHERE contribution_id=?',('review_cache_capacity',int(time.time())+300,ident))
                else:
                    capacity(3*len(encoded)+16384)
                    db().execute('UPDATE contribution_review_cache SET result_json=?,checked_at=?,next_check_at=?,error_code=NULL WHERE contribution_id=?',(encoded.decode(),int(time.time()),int(time.time())+TTL,ident))
        return view(db().execute('SELECT * FROM contribution_review_cache WHERE contribution_id=?',(ident,)).fetchone())

    def cached(ident):
        return view(db().execute('SELECT * FROM contribution_review_cache WHERE contribution_id=?',(ident,)).fetchone())

    app.extensions['contribution_reviews']=dict(public_revision=public_revision,read=read,cached=cached)
