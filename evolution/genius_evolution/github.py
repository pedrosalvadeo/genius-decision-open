"""Publish one immutable proposal branch and draft PR. Never merge or deploy."""
import base64
import json
import os
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request
from .pipeline import encoded, strict, tree_files, verify_bundle, REVISION, digest
from .model import require

REPOSITORY = 'pedrosalvadeo/genius-decision-open'


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise ValueError('GITHUB_REDIRECT_REFUSED')


class API:
    def __init__(self):
        self.opener = urllib.request.build_opener(NoRedirect())

    def __call__(self, path, method='GET', body=None):
        require(path.startswith('/') and not path.startswith('//'), 'GITHUB_PATH')
        request = urllib.request.Request('https://api.github.com/repos/' + REPOSITORY + path,
            method=method, data=None if body is None else encoded(body), headers={
                'Authorization': 'Bearer ' + os.environ['GH_TOKEN'],
                'Accept': 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28',
                'User-Agent': 'Genius-Code-Evolution', 'Content-Type': 'application/json'})
        with self.opener.open(request, timeout=30) as response:
            raw = response.read(4*1024*1024 + 1)
        require(len(raw) <= 4*1024*1024, 'GITHUB_RESPONSE_LIMIT')
        return strict(raw) if raw else None


class Publisher:
    def __init__(self, root, api):
        self.root, self.api = Path(root), api

    def optional(self, path):
        try:
            return self.api(path)
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return None
            raise

    def read(self, path, sha):
        result = self.api('/contents/' + urllib.parse.quote(path, safe='/') + '?ref=' + sha)
        require(result.get('encoding') == 'base64', 'GITHUB_ENCODING')
        raw = base64.b64decode(''.join(result['content'].split()), validate=True)
        require(len(raw) <= 256*1024, 'PROPOSAL_READ_LIMIT')
        return raw.decode('utf-8')

    def publish(self, bundle):
        verify_bundle(self.root, bundle)
        pid, base = bundle['proposal_id'], bundle['base_revision']
        branch = 'genius/evolution/' + pid
        report_path = f'evolution/proposals/{pid}/proposal.json'
        report = strict(bundle['files'][report_path])
        ref = '/git/ref/heads/' + branch
        existing = self.optional(ref)
        reused = existing is not None
        if existing:
            sha = existing['object']['sha']
            # A completed proposal is historical. Never rewrite it on retry or
            # quietly reopen a closed review. Verify all its generated contents.
            old_report = strict(self.read(report_path, sha))
            old_base = old_report['base_revision']
            require(type(old_base) is str and REVISION.fullmatch(old_base), 'EXISTING_BASE_INVALID')
            old_commit = self.api('/git/commits/' + sha)
            require([p['sha'] for p in old_commit['parents']] == [old_base], 'EXISTING_BASE_CHANGED')
            expected = dict(report, base_revision=old_report['base_revision'])
            require(old_report == expected, 'EXISTING_PROPOSAL_CHANGED')
            for path, text in bundle['files'].items():
                if path != report_path:
                    require(self.read(path, sha) == text, 'EXISTING_SOURCE_CHANGED')
            delta = self.api('/compare/' + old_base + '...' + sha + '?per_page=1')
            require(delta['total_commits'] == 1 and {f['filename'] for f in delta['files']} ==
                    set(bundle['files']) | {'PUBLICATION_MANIFEST.json'}, 'EXISTING_SCOPE_CHANGED')
            old_manifest = strict(self.read('PUBLICATION_MANIFEST.json', old_base))
            old_hashes = dict(bundle['hashes'])
            old_hashes[report_path] = digest(encoded(old_report))
            old_manifest['files'].update(old_hashes)
            require(strict(self.read('PUBLICATION_MANIFEST.json', sha)) == old_manifest, 'EXISTING_MANIFEST_CHANGED')
            evaluated_base = old_report['base_revision']
        else:
            require(self.api('/git/ref/heads/main')['object']['sha'] == base, 'MAIN_MOVED_BEFORE_PUBLICATION')
            parent = self.api('/git/commits/' + base)
            files = tree_files(self.root, bundle)
            tree = self.api('/git/trees', 'POST', dict(base_tree=parent['tree']['sha'], tree=[
                dict(path=path, mode='100644', type='blob', content=text) for path, text in sorted(files.items())]))
            commit = self.api('/git/commits', 'POST', dict(message='Genius: propose ' + pid + ' [' + report['decision'] + ']',
                tree=tree['sha'], parents=[base]))
            sha = commit['sha']; evaluated_base = base
            try:
                self.api('/git/refs', 'POST', dict(ref='refs/heads/' + branch, sha=sha))
            except urllib.error.HTTPError as exc:
                # A concurrent publisher may have committed the exact same branch.
                # Reconcile it; never force-push or reset another author's work.
                if exc.code != 422:
                    raise
                require(self.optional(ref) is not None, 'BRANCH_CREATION_REJECTED')
                return self.publish(bundle)
        query = urllib.parse.urlencode(dict(head='pedrosalvadeo:' + branch, base='main', state='all', per_page=10))
        pulls = self.api('/pulls?' + query)
        require(type(pulls) is list and len(pulls) <= 1, 'AMBIGUOUS_PROPOSAL_REVIEW')
        result = dict(format='genius-code-publication-result/1', proposal_id=pid, branch=branch,
                      commit=sha, evaluated_base=evaluated_base, reused=reused, decision=report['decision'],
                      production_activated=False, branch_url='https://github.com/' + REPOSITORY + '/tree/' + branch)
        if pulls:
            pull = pulls[0]
        else:
            title = 'Genius proposal ' + pid + ': ' + report['decision']
            body = ('Generated by the committed Genius evolution workflow from public synthetic memory.\n\n'
                    'Decision: **' + report['decision'] + '**. Base evaluated: `' + evaluated_base + '`.\n\n'
                    'The branch contains generated Python, the frozen request/data/code identities, training '
                    'results, and every evaluation result, including failures. See `' + report_path + '`.\n\n'
                    'This is a draft for review, not a production activation. A rejected proposal must not be '
                    'promoted under this contract. A synthetic pass would establish only fixture performance, '
                    'not generalization, wellbeing or life sustainment. CI may require platform approval; '
                    'this workflow does not approve, merge, or deploy its own change.')
            try:
                pull = self.api('/pulls', 'POST', dict(title=title, body=body, head=branch, base='main', draft=True))
            except urllib.error.HTTPError as exc:
                if exc.code not in (403, 422):
                    raise
                # Preserve the branch if GitHub disallows bot-created PRs; do not
                # alter repository settings or switch credentials to bypass it.
                result.update(status='BRANCH_PUBLISHED_PR_BLOCKED', http_status=exc.code,
                              review_url='https://github.com/' + REPOSITORY + '/compare/main...' + branch)
                return result
        result.update(status='PUBLISHED', pull_request=pull['number'], review_url=pull['html_url'],
                      review_state=pull['state'], draft=pull.get('draft', False))
        return result
