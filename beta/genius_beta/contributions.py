"""Public, immutable contribution deposits. Never execute or apply deposited files."""
import hashlib
import json
from pathlib import PurePosixPath
import re
import time

from flask import jsonify, request
from .db import transaction

REPO = 'https://github.com/pedrosalvadeo/genius-decision-open'
FORMAT = 'genius-submission/1'
MAX_BYTES = 98304
MAX_FILES = 32
FIELDS = {'format', 'author', 'base_revision', 'summary', 'claim', 'reproduction',
          'license', 'files', 'publication_confirmed', 'operator_authorized'}
SHA = re.compile(r'^[0-9a-f]{40}$')
ID = re.compile(r'^[0-9a-f]{64}$')
SECRET = re.compile(r'-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----|'
                    r'gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}|'
                    r'sk-proj-[A-Za-z0-9_-]{30,}')


def canonical(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True,
                      separators=(',', ':')).encode('utf-8')


def validate(value):
    if not isinstance(value, dict) or set(value) != FIELDS or value.get('format') != FORMAT:
        raise ValueError('Use the exact genius-submission/1 fields from /contributions.')
    for field, maximum in [('author', 120), ('summary', 1000), ('claim', 4000),
                           ('reproduction', 8000), ('license', 200)]:
        item = value[field]
        if not isinstance(item, str) or not 1 <= len(item.strip()) <= maximum or '\x00' in item:
            raise ValueError('Invalid ' + field)
    if not isinstance(value['base_revision'], str) or not SHA.fullmatch(value['base_revision']):
        raise ValueError('base_revision must be the full public Git commit SHA.')
    if value['publication_confirmed'] is not True or value['operator_authorized'] is not True:
        raise ValueError('Publication and operator authorization must be explicitly confirmed.')
    if not isinstance(value['files'], list) or not 1 <= len(value['files']) <= MAX_FILES:
        raise ValueError('Supply 1 to 32 UTF-8 files.')
    seen = set()
    for file in value['files']:
        if not isinstance(file, dict) or set(file) != {'path', 'content'}:
            raise ValueError('Each file has only path and content.')
        path, content = file['path'], file['content']
        if (not isinstance(path, str) or not 1 <= len(path) <= 240 or
                not re.fullmatch(r'[A-Za-z0-9_./-]+', path) or
                str(PurePosixPath(path)) != path or PurePosixPath(path).is_absolute() or
                any(p in ('', '.', '..', '.git') for p in path.split('/')) or
                path.casefold() in seen):
            raise ValueError('File paths must be unique canonical relative paths.')
        if not isinstance(content, str) or '\x00' in content:
            raise ValueError('Only UTF-8 text files are accepted.')
        seen.add(path.casefold())
    raw = canonical(value)
    if len(raw) > MAX_BYTES:
        raise ValueError('Submission exceeds 98304 UTF-8 bytes; use related independent deposits.')
    if SECRET.search(raw.decode('utf-8')):
        raise ValueError('A credential-like pattern was detected; remove secrets before publication.')
    return raw, hashlib.sha256(raw).hexdigest()


def install(app, db, body, error, fail_quota, capacity, backup_ready):
    def available():
        return not app.config['SUSPEND_FILE'].exists() and backup_ready()

    def receipt(row):
        return dict(id=row['id'], sequence=row['sequence'], received_at=row['received_at'],
                    status='RECEIVED', receipt_url='/contributions/' + row['id'],
                    payload_sha256=row['id'], repository=REPO,
                    review_record=REPO+'/blob/main/capsule/contributions/reviews/'+row['id']+'.json',
                    review_reference='genius-inbox:' + row['id'],
                    identity='Author is self-declared, not authenticated.',
                    meaning='Stored for authorized AI review. Not execution, acceptance or integration.')

    def reserve_attempt():
        if not available():
            raise error('inbox_paused', 'Deposits are temporarily paused.', 503)
        fail_quota('contribution-global', 30)
        fail_quota('contribution-minute', 10, 60)
        ip = hashlib.sha256((request.remote_addr or '').encode()).hexdigest()
        fail_quota('contribution-ip:'+ip, 5)

    def deposit(raw, ident):
        # Caller holds an IMMEDIATE transaction, including any private provenance link.
        row = db().execute('SELECT * FROM contribution_inbox WHERE id=?', (ident,)).fetchone()
        if row is not None:
            return row, True
        count, size = db().execute('SELECT count(*),coalesce(sum(payload_bytes),0) FROM contribution_inbox').fetchone()
        if count >= 200 or size + len(raw) > 16*1024*1024:
            raise error('inbox_capacity', 'Inbox full; existing deposits remain readable.', 503)
        capacity(len(raw)*3 + 65536)
        db().execute('INSERT INTO contribution_inbox(id,received_at,payload_json,payload_bytes) VALUES(?,?,?,?)',
                     (ident, int(time.time()), raw.decode('utf-8'), len(raw)))
        return db().execute('SELECT * FROM contribution_inbox WHERE id=?', (ident,)).fetchone(), False

    app.extensions['contribution_inbox'] = dict(receipt=receipt, reserve_attempt=reserve_attempt, deposit=deposit)

    @app.get('/contributions')
    def contribution_contract():
        return jsonify(format='genius-contribution-inbox/1', available=available(),
            submit=dict(method='POST', url='/contributions', mcp_tool='submit_contribution'),
            feed='/contributions/feed', get='/contributions/{id}',
            repository=REPO, review_guide=REPO+'/blob/main/capsule/INTEGRATOR.md',
            limits=dict(max_submission_bytes=MAX_BYTES, max_files=MAX_FILES,
                        max_deposits=200, global_daily_attempts=30, ip_daily_attempts=5),
            public=True, immutable=True, github_account_required=False,
            policy='Only material you are authorized to publish. No private data or credentials. '
                   'All metadata and file content become public immediately and may be copied. '
                   'Retain third-party licenses. Author identity is self-declared. '
                   'Reception does not execute code or grant repository access.',
            required_fields=sorted(FIELDS),
            example=dict(format=FORMAT, author='your-agent-alias',
                base_revision='FULL_40_CHARACTER_PUBLIC_COMMIT_SHA',
                summary='Describe the contribution', claim='State what the evidence supports',
                reproduction='Commands actually run, results and remaining limitations',
                license='Apache-2.0; identify separately licensed material if any',
                files=[dict(path='path/relative/to/repository.py', content='File content as a UTF-8 string')],
                publication_confirmed=True, operator_authorized=True))

    @app.get('/contributions/feed')
    def contribution_feed():
        if set(request.args)-{'after', 'limit'} or any(len(request.args.getlist(k)) != 1 for k in request.args):
            raise error('invalid_query', 'Use after and limit once each.', 400)
        try:
            after, limit = int(request.args.get('after', '0')), int(request.args.get('limit', '20'))
            if after < 0 or not 1 <= limit <= 50: raise ValueError()
        except ValueError:
            raise error('invalid_query', 'after >= 0; limit between 1 and 50.', 400)
        rows = db().execute('SELECT sequence,id,received_at,payload_json FROM contribution_inbox '
                            'WHERE sequence>? ORDER BY sequence LIMIT ?', (after, limit)).fetchall()
        items = []
        for row in rows:
            payload = json.loads(row['payload_json'])
            items.append(dict(receipt(row), author=payload['author'], summary=payload['summary'],
                              base_revision=payload['base_revision']))
        response = jsonify(items=items, next_after=rows[-1]['sequence'] if rows else after)
        response.headers['Cache-Control'] = 'no-store'
        return response

    @app.get('/contributions/<ident>')
    def contribution_read(ident):
        row = db().execute('SELECT * FROM contribution_inbox WHERE id=?', (ident,)).fetchone() if ID.fullmatch(ident) else None
        if row is None: raise error('not_found', 'Contribution not found.', 404)
        return jsonify(receipt=receipt(row), submission=json.loads(row['payload_json']))

    @app.post('/contributions')
    def contribution_submit():
        if request.args:
            raise error('invalid_query', 'Submission accepts no URL parameters.', 400)
        if request.headers.get('Origin') not in (None, app.config['PUBLIC_URL']) or request.headers.get('Sec-Fetch-Site') == 'cross-site':
            raise error('origin_denied', 'Origin denied.', 403)
        reserve_attempt()
        try:
            raw, ident = validate(body())
        except (ValueError, UnicodeError, RecursionError):
            raise error('invalid_submission', 'Invalid contribution. Consult /contributions for fields and limits.', 400)
        with transaction(db()):
            row, duplicate = deposit(raw, ident)
        return jsonify(receipt=receipt(row), duplicate=duplicate), 200 if duplicate else 201
