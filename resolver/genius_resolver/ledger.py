"""A versioned ledger, not an executor of instructions received from the web.

Receipts are evidence reviewed by the operating agent. Schema validation prevents
category mistakes; it does not certify an external claim or an independent user.
"""
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile

SCHEMA = 'genius-problem-ledger/1'
STATES = ('DETECTED', 'INVESTIGATING', 'NEEDS_INFORMATION', 'BLOCKED',
          'SOLUTION_PREPARED', 'APPLIED', 'VERIFIED', 'CLOSED_AT_SOURCE')
TRANSITIONS = {
    'DETECTED': {'INVESTIGATING', 'BLOCKED', 'NEEDS_INFORMATION'},
    'INVESTIGATING': {'SOLUTION_PREPARED', 'BLOCKED', 'NEEDS_INFORMATION'},
    'NEEDS_INFORMATION': {'INVESTIGATING', 'BLOCKED'},
    'BLOCKED': {'INVESTIGATING', 'NEEDS_INFORMATION'},
    'SOLUTION_PREPARED': {'APPLIED', 'INVESTIGATING', 'BLOCKED'},
    'APPLIED': {'VERIFIED', 'INVESTIGATING', 'BLOCKED'},
    'VERIFIED': {'INVESTIGATING'},
    'CLOSED_AT_SOURCE': set(),
}
ISSUE = re.compile(r'https://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)/issues/([1-9][0-9]*)\Z')
MAX_BYTES = 2 * 1024 * 1024


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def timestamp(value=None):
    value = value or datetime.now(timezone.utc).isoformat()
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    require(parsed.tzinfo is not None, 'TIMEZONE_REQUIRED')
    return parsed.astimezone(timezone.utc).isoformat()


def text(value, limit=2000):
    require(isinstance(value, str) and 0 < len(value.strip()) <= limit and '\x00' not in value, 'TEXT')
    return value


def issue_url(value):
    require(isinstance(value, str) and ISSUE.fullmatch(value), 'PUBLIC_ISSUE_URL')
    return value


def new():
    return dict(schema=SCHEMA, revision=0, problems={}, discoveries=[])


def check_receipt(status, receipt, revision, criteria):
    require(isinstance(receipt, dict), 'RECEIPT_REQUIRED')
    require(type(receipt.get('source_revision')) is int and receipt['source_revision'] == revision, 'STALE_SOURCE')
    text(receipt.get('summary'))
    refs = receipt.get('evidence')
    require(isinstance(refs, list) and 1 <= len(refs) <= 20, 'EVIDENCE_REQUIRED')
    for ref in refs:
        text(ref, 1000)
    if status == 'SOLUTION_PREPARED':
        require(criteria, 'SUCCESS_CRITERIA_REQUIRED')
        require(receipt.get('criteria') == criteria, 'CRITERIA_MISMATCH')
        require(receipt.get('checks_passed') is True, 'SOLUTION_CHECKS_REQUIRED')
        text(receipt.get('artifact'), 1000)
    if status == 'APPLIED':
        text(receipt.get('application_ref'), 1000)
        text(receipt.get('authority'), 1000)
        require(receipt.get('target') == 'INTENDED_DESTINATION', 'LOCAL_COPY_IS_NOT_APPLICATION')
    if status == 'VERIFIED':
        require(receipt.get('criteria') == criteria, 'CRITERIA_MISMATCH')
        require(receipt.get('checks_passed') is True, 'VERIFICATION_REQUIRED')
        require(receipt.get('observed_after_application') is True, 'POST_APPLICATION_EVIDENCE_REQUIRED')
        text(receipt.get('observation_ref'), 1000)


def validate(state):
    require(isinstance(state, dict) and state.get('schema') == SCHEMA, 'LEDGER_SCHEMA')
    require(type(state.get('revision')) is int and state['revision'] >= 0, 'REVISION')
    require(isinstance(state.get('problems'), dict) and len(state['problems']) <= 100, 'CAPACITY')
    require(isinstance(state.get('discoveries'), list) and len(state['discoveries']) <= 32, 'DISCOVERIES')
    for pid, row in state['problems'].items():
        require(pid == digest(issue_url(row['source']['url']))[:24], 'PROBLEM_ID')
        require(row['status'] in STATES, 'STATE')
        require(isinstance(row.get('events'), list) and 1 <= len(row['events']) <= 128, 'EVENTS')
        current, revision, criteria, fingerprint = None, 0, [], None
        for e in row['events']:
            timestamp(e['at'])
            kind = e['kind']
            if kind == 'discovered':
                require(current is None, 'DUPLICATE_DISCOVERY_EVENT')
                current, revision, fingerprint = e['status'], 1, e['fingerprint']
                require(current in ('DETECTED', 'CLOSED_AT_SOURCE'), 'INITIAL_STATE')
            elif kind == 'claimed':
                require(current in ('DETECTED', 'INVESTIGATING', 'BLOCKED', 'NEEDS_INFORMATION'), 'CLAIM_HISTORY')
                require(e['source_revision'] == revision, 'STALE_SOURCE')
                current, criteria = 'INVESTIGATING', e['criteria']
                require(isinstance(criteria, list) and 1 <= len(criteria) <= 12, 'SUCCESS_CRITERIA_REQUIRED')
                for criterion in criteria:
                    text(criterion, 500)
            elif kind == 'source_changed':
                require(e['previous_status'] == current and e['previous_fingerprint'] == fingerprint, 'SOURCE_HISTORY')
                current, fingerprint = e['status'], e['fingerprint']
                require(current in ('NEEDS_INFORMATION', 'CLOSED_AT_SOURCE'), 'CHANGED_SOURCE_STATE')
                revision, criteria = revision + 1, []
            elif kind == 'transition':
                require(e['previous_status'] == current and e['status'] in TRANSITIONS[current], 'TRANSITION_HISTORY')
                current = e['status']
                check_receipt(current, e['receipt'], revision, criteria)
                if current == 'INVESTIGATING':
                    criteria = []
            else:
                raise ValueError('EVENT_KIND')
        require(row['status'] == current and row['revision'] == revision and row['criteria'] == criteria, 'EVENT_STATE_MISMATCH')
        require(row['source']['fingerprint'] == fingerprint, 'SOURCE_FINGERPRINT_MISMATCH')
    require(len(canonical(state).encode()) <= MAX_BYTES, 'LEDGER_SIZE')
    return state


def load(path):
    path = Path(path)
    if not path.exists():
        raise ValueError('LEDGER_MISSING_USE_INIT_ONLY_FOR_NEW_LEDGER')
    require(path.stat().st_size <= MAX_BYTES, 'LEDGER_SIZE')
    return validate(json.loads(path.read_text()))


@contextmanager
def transaction(path, expected_revision, initialize=False):
    """Local lock + optimistic revision + atomic replacement; Git still needs CAS."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.with_suffix(path.suffix + '.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if initialize:
            require(not path.exists(), 'LEDGER_ALREADY_EXISTS')
            state = new()
        else:
            state = load(path)
        require(state['revision'] == expected_revision, 'STALE_REVISION')
        before = deepcopy(state)
        yield state
        validate(state)
        if not initialize and state == before:
            return
        state['revision'] += 1
        raw = canonical(validate(state)) + '\n'
        name = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, delete=False) as out:
                name = out.name
                out.write(raw)
                out.flush()
                os.fsync(out.fileno())
            os.replace(name, path)
            name = None
        finally:
            if name:
                os.unlink(name)


def source_from_issue(item):
    require(isinstance(item, dict) and 'pull_request' not in item, 'ISSUE_REQUIRED')
    url = issue_url(item.get('html_url'))
    parts = ISSUE.fullmatch(url)
    require(type(item.get('number')) is int and str(item['number']) == parts[3], 'ISSUE_ID_MISMATCH')
    require(item.get('state') in ('open', 'closed'), 'SOURCE_STATE')
    body = item.get('body') or ''
    require(isinstance(body, str) and len(body.encode()) <= 131072, 'SOURCE_BODY_SIZE')
    title = text(item.get('title'), 512)
    labels = sorted(text(x['name'], 100) for x in item.get('labels', []))
    assignees = sorted(text(x['login'], 100) for x in item.get('assignees', []))
    require(len(labels) <= 100 and len(assignees) <= 100, 'SOURCE_METADATA_LIMIT')
    snapshot = dict(url=url, title=title, body=body, labels=labels,
                    assignees=assignees, state=item['state'])
    # Store a fingerprint, not the issue's full text, commands or personal data.
    return dict(url=url, title=title, labels=labels, assignees=assignees,
                state=item['state'], updated_at=timestamp(item['updated_at']),
                fingerprint=digest(snapshot))


def event(row, kind, at, **details):
    require(len(row['events']) < 128, 'EVENT_CAPACITY_REVIEW_REQUIRED')
    row['events'].append(dict(kind=kind, at=at, **details))


def ingest(state, items, query, observed_at=None, total_count=None, incomplete=False):
    require(isinstance(items, list) and len(items) <= 20, 'DISCOVERY_BATCH')
    text(query, 500)
    at = timestamp(observed_at)
    sources = [source_from_issue(i) for i in items]
    counts = dict(new=0, changed=0, unchanged=0, capacity_skipped=0, stale_skipped=0)
    for source in sources:
        pid = digest(source['url'])[:24]
        row = state['problems'].get(pid)
        if row is None:
            if len(state['problems']) >= 100:
                counts['capacity_skipped'] += 1
                continue
            status = 'DETECTED' if source['state'] == 'open' else 'CLOSED_AT_SOURCE'
            row = dict(id=pid, source=source, status=status, discovered_at=at,
                       last_seen=at, revision=1, criteria=[], events=[],
                       priority=None, reasoning=None, kernel_evaluation=None,
                       wellbeing=None, sustained_life_probability=None)
            event(row, 'discovered', at, fingerprint=source['fingerprint'], status=status)
            state['problems'][pid] = row
            counts['new'] += 1
        else:
            if source['updated_at'] < row['source']['updated_at']:
                counts['stale_skipped'] += 1
                continue
            if source['fingerprint'] != row['source']['fingerprint']:
                event(row, 'source_changed', at, previous_status=row['status'],
                      previous_fingerprint=row['source']['fingerprint'], fingerprint=source['fingerprint'],
                      status='NEEDS_INFORMATION' if source['state'] == 'open' else 'CLOSED_AT_SOURCE')
                row['revision'] += 1
                row['status'] = 'NEEDS_INFORMATION' if source['state'] == 'open' else 'CLOSED_AT_SOURCE'
                row['criteria'] = []
                row['kernel_evaluation'] = None
                row.pop('lease', None)
                counts['changed'] += 1
            else:
                counts['unchanged'] += 1
            row['source'], row['last_seen'] = source, at
    receipt = dict(at=at, query=query, inspected=len(items), total_count=total_count,
                   incomplete_results=bool(incomplete), coverage='ONE_PAGE_SAMPLE', **counts)
    state['discoveries'] = (state['discoveries'] + [receipt])[-32:]
    return receipt


def claim(state, pid, operator, criteria, reason, now=None):
    at = timestamp(now)
    row = state['problems'][pid]
    require(row['status'] != 'CLOSED_AT_SOURCE', 'SOURCE_CLOSED')
    require(isinstance(criteria, list) and 1 <= len(criteria) <= 12, 'SUCCESS_CRITERIA_REQUIRED')
    criteria = [text(x, 500) for x in criteria]
    require(len(set(criteria)) == len(criteria), 'DUPLICATE_CRITERIA')
    operator = text(operator, 100)
    active = row.get('lease')
    if active:
        require(active['owner'] == operator or timestamp(active['expires_at']) <= at, 'PROBLEM_LEASED')
    # Freeze criteria before preparing the solution; restarting must explicitly reopen it.
    require(row['status'] in ('DETECTED', 'INVESTIGATING', 'BLOCKED', 'NEEDS_INFORMATION'), 'REOPEN_REQUIRED')
    if row['status'] == 'INVESTIGATING' and row['criteria']:
        require(row['criteria'] == criteria, 'CRITERIA_FROZEN')
    from datetime import timedelta
    expiry = (datetime.fromisoformat(at) + timedelta(minutes=50)).isoformat()
    row['criteria'], row['status'] = criteria, 'INVESTIGATING'
    row['reasoning'] = text(reason)
    row['lease'] = dict(owner=operator, expires_at=expiry)
    event(row, 'claimed', at, operator=operator, source_revision=row['revision'],
          criteria=criteria, reason=reason)


def transition(state, pid, status, operator, receipt, now=None):
    at = timestamp(now)
    row = state['problems'][pid]
    require(status in TRANSITIONS[row['status']], 'INVALID_TRANSITION')
    check_receipt(status, receipt, row['revision'], row['criteria'])
    lease = row.get('lease')
    if lease and lease['expires_at'] > at:
        require(lease['owner'] == operator, 'PROBLEM_LEASED')
    event(row, 'transition', at, previous_status=row['status'], status=status,
          operator=text(operator, 100), receipt=deepcopy(receipt))
    row['status'] = status
    row.pop('lease', None)
    if status == 'INVESTIGATING':
        row['criteria'] = []


def report(state):
    """Human-readable public report. Escaping prevents injected Markdown links."""
    def safe(value):
        return str(value).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('|', '&#124;').replace('[', '&#91;').replace(']', '&#93;').replace('\n', ' ').replace('\r', ' ')
    rows = sorted(state['problems'].values(), key=lambda r: (r['discovered_at'], r['id']))
    counts = {s: sum(r['status'] == s for r in rows) for s in STATES}
    lines = ['# Genius — problemas y soluciones', '',
             'Estado generado desde `ledger.json`. El buscador inspecciona muestras; no cubre toda Internet.', '',
             f"Problemas registrados: **{len(rows)}** · Soluciones preparadas: **{counts['SOLUTION_PREPARED']}** · "
             f"Aplicadas pendientes de verificación: **{counts['APPLIED']}** · Resultados verificados: **{counts['VERIFIED']}**", '',
             '| Problema público | Estado | Última evidencia |', '|---|---|---|']
    for row in rows:
        last = next((e['receipt']['summary'] for e in reversed(row['events']) if e['kind'] == 'transition'), 'Detectado; pendiente de investigación.')
        lines.append(f"| [{safe(row['source']['title'])}]({row['source']['url']}) | {row['status']} | {safe(last)} |")
    lines += ['', 'Una solución preparada y sus pruebas locales no acreditan adopción externa. '
              'El cierre del issue tampoco acredita que Genius lo resolvió. Bienestar y PVS: sin medir.', '']
    return '\n'.join(lines)
