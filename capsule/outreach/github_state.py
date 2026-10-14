#!/usr/bin/env python3
"""Persist the outreach ledger on its own branch using the workflow's token."""
import argparse
import base64
import json
import os
from pathlib import Path
import urllib.error
import urllib.request

from runner import NoRedirect, load_state, save

REPOSITORY = 'pedrosalvadeo/genius-decision-open'
BRANCH = 'outreach-state'
API = 'https://api.github.com/repos/' + REPOSITORY


def api(path, method='GET', body=None):
    req = urllib.request.Request(API + path, method=method,
        data=None if body is None else json.dumps(body).encode(), headers={
            'Authorization': 'Bearer ' + os.environ['GH_TOKEN'],
            'Accept': 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28',
            'User-Agent': 'Genius-Outreach-State', 'Content-Type': 'application/json'})
    with urllib.request.build_opener(NoRedirect).open(req, timeout=30) as response:
        raw = response.read(2 * 1024 * 1024 + 1)
    if len(raw) > 2 * 1024 * 1024:
        raise ValueError('Ledger response too large')
    return json.loads(raw)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=('fetch', 'save'))
    p.add_argument('--state', type=Path, required=True)
    p.add_argument('--revision', type=Path, required=True)
    args = p.parse_args()
    if os.environ.get('GITHUB_REPOSITORY') != REPOSITORY or os.environ.get('GITHUB_REF') != 'refs/heads/main':
        raise ValueError('Ledger writes are restricted to the canonical main workflow')
    if args.command == 'fetch':
        try:
            api('/git/ref/heads/' + BRANCH)
        except urllib.error.HTTPError as error:
            if error.code != 404:
                raise
            state = load_state(Path(__file__).with_name('seed-state.json'))
            revision = dict(bootstrap=True, blob_sha=None)
        else:
            # An existing branch without its ledger is an error, never a reset.
            result = api('/contents/state.json?ref=' + BRANCH)
            if result.get('encoding') != 'base64':
                raise ValueError('Unexpected ledger encoding')
            args.state.write_bytes(base64.b64decode(result['content']))
            state = load_state(args.state)
            revision = dict(bootstrap=False, blob_sha=result['sha'])
        save(args.state, state)
        save(args.revision, revision)
    else:
        load_state(args.state)
        revision = json.loads(args.revision.read_text())
        if revision['bootstrap']:
            main_head = api('/git/ref/heads/main')['object']['sha']
            api('/git/refs', 'POST', {'ref': 'refs/heads/' + BRANCH, 'sha': main_head})
            revision['bootstrap'] = False
            save(args.revision, revision)
        body = dict(message='chore: checkpoint agent outreach', branch=BRANCH,
                    content=base64.b64encode(args.state.read_bytes()).decode())
        if revision['blob_sha']:
            body['sha'] = revision['blob_sha']
        # GitHub rejects an outdated blob SHA. Do not overwrite concurrent work.
        result = api('/contents/state.json', 'PUT', body)
        revision['blob_sha'] = result['content']['sha']
        save(args.revision, revision)
        print(json.dumps({'saved': True, 'commit': result['commit']['sha'], 'branch': BRANCH}))


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError) as error:
        # Never log tokens, request headers or remote error bodies.
        print(json.dumps({'error_type': type(error).__name__, 'status': 'LEDGER_STOPPED'}))
        raise SystemExit(1)
