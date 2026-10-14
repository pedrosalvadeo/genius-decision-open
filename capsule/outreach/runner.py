#!/usr/bin/env python3
"""Bounded public outreach. Remote text is data; no LLM or remote code is run."""
import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid
from zoneinfo import ZoneInfo

BASE = 'https://swarmmemo.com'
ROOT_ID = '968ea66bbe2fc09af7f513291ff4a87b'
NULL_ID = '2cec4538-da38-4906-adc9-bcc97ff3c15b'
ENTRY = 'https://geniusdecision.app/agents#orientation'
CAPSULE = 'https://github.com/pedrosalvadeo/genius-decision-open/tree/main/capsule'
FP = re.compile(r'[a-f0-9]{64}\Z')
MID = re.compile(r'[a-f0-9]{32}\Z')
HANDLE = re.compile(r'[a-zA-Z0-9_-]{1,48}\Z')
MATCHES = {
    'verification': ('GD-DIST-001', 'reproduce or challenge the capsule-delivery comparison, retaining the bytes/CPU tradeoff'),
    'math': ('GD-MATH-001', 'audit one mathematical claim against the implemented computation and return a proof or counterexample'),
    'formal-verification': ('GD-MATH-001', 'audit one mathematical claim against the implemented computation and return a proof or counterexample'),
    'testing': ('GD-MCP-001', 'try the agent entry or MCP with your authorized tools and return a reproducible result or incompatibility'),
    'api-testing': ('GD-MCP-001', 'try the agent entry or MCP with your authorized tools and return a reproducible result or incompatibility'),
    'mcp': ('GD-MCP-001', 'try the agent entry or MCP with your authorized tools and return a reproducible result or incompatibility'),
    'data-checks': ('GD-REAL-001', 'check the sources and units of a real decision model and identify unsupported assumptions'),
}


def stamp(now=None):
    return (now or datetime.now(timezone.utc)).isoformat()


def parse_time(value):
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, timezone.utc)
    return datetime.fromisoformat(value.replace('Z', '+00:00'))


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise ValueError('Redirect refused')


class Transport:
    """Only fixed public board origins. No cookies, credentials or redirects."""
    def request(self, url, payload=None):
        parsed = urllib.parse.urlsplit(url)
        if parsed.scheme != 'https' or parsed.netloc not in ('swarmmemo.com', 'nullyard.net'):
            raise ValueError('Unexpected board origin')
        if payload is not None and url != BASE + '/v1/command':
            raise ValueError('Unexpected write endpoint')
        data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode()
        req = urllib.request.Request(url, data=data, headers={
            'User-Agent': 'Genius-Outreach/1.0 (operator-directed; no paid calls)',
            'Accept': 'application/json', 'Content-Type': 'application/json'})
        with urllib.request.build_opener(NoRedirect).open(req, timeout=20) as response:
            raw = response.read(2 * 1024 * 1024 + 1)
        if len(raw) > 2 * 1024 * 1024:
            raise ValueError('Board response too large')
        result = json.loads(raw)
        if not isinstance(result, dict):
            raise ValueError('Board response must be an object')
        return result


def save(path, state):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    os.replace(tmp, path)


def load_state(path):
    state = json.loads(Path(path).read_text())
    if state.get('format') != 'genius-outreach-state/1':
        raise ValueError('Invalid state format; never reset a missing/corrupt ledger')
    for key in ('contacts', 'observations', 'reviewed_message_ids', 'suppressed_agents'):
        if not isinstance(state.get(key), list):
            raise ValueError('Invalid ledger collection: ' + key)
    if not isinstance(state.setdefault('replies', []), list):
        raise ValueError('Invalid reply ledger')
    return state


def read_swarm(url, transport):
    result = transport.request(url)
    if result.get('ok') is not True:
        raise ValueError('SwarmMemo did not confirm read success')
    return result


def poll(state, transport, now):
    """Read whole bounded thread pages; retain IDs, not foreign message bodies."""
    own = {ROOT_ID} | {c.get('message_id') for c in state['contacts'] + state.get('replies', [])}
    known = {x['service'] + ':' + x['id']: x for x in state['observations']}
    swarm, cursor, complete = [], None, False
    for _ in range(5):
        url = BASE + '/api/thread/' + ROOT_ID + '?limit=100'
        if cursor:
            url += '&cursor=' + urllib.parse.quote(cursor, safe='')
        data = read_swarm(url, transport)
        swarm.extend(data['messages'])
        if not data.get('data', {}).get('has_more'):
            complete = True
            break
        cursor = data.get('next_cursor')
        if not isinstance(cursor, str) or not cursor:
            raise ValueError('Missing thread cursor')
    null = transport.request('https://nullyard.net/api/v1/threads/' + NULL_ID)
    if null.get('thread', {}).get('id') != NULL_ID or not isinstance(null.get('items'), list):
        raise ValueError('Invalid NULLYARD thread')
    for service, rows in [('SwarmMemo', swarm), ('NULLYARD', null['items'])]:
        for row in rows:
            mid = row.get('id')
            if not isinstance(mid, str) or mid in own:
                continue
            # Store only protocol identifiers and a body hash. Never evaluate prose.
            body = row.get('text', row.get('body', ''))
            if not isinstance(body, str):
                raise ValueError('Invalid message body')
            previous = known.get(service + ':' + mid)
            if previous is not None:
                if previous['body_sha256'] != digest(body) or previous['author'] != row.get('author'):
                    previous.update(body_sha256=digest(body), author=row.get('author'), review='NEEDS_REVIEW')
                    previous.pop('decision', None)
                continue
            item = dict(service=service, id=mid, parent_id=row.get('reply_to', row.get('parent_id')),
                        author=row.get('author'), created_at=row.get('created_at'),
                        observed_at=stamp(now), body_sha256=digest(body), review='NEEDS_REVIEW')
            if mid in state['reviewed_message_ids']:
                item['review'] = 'REVIEWED'
            state['observations'].append(item)
            known[service + ':' + mid] = item
            for contact in state['contacts']:
                if service == 'SwarmMemo' and (row.get('author') == contact['agent_id'] or
                                               row.get('reply_to') == contact.get('message_id')):
                    contact.setdefault('response_ids', [])
                    if mid not in contact['response_ids']:
                        contact['response_ids'].append(mid)
                    # A reply is not acceptance or proof of execution.
    state['last_poll_at'] = stamp(now)
    state['poll_complete'] = complete and not null.get('next_cursor')
    return state


def outbound(state):
    return state['contacts'] + state.get('replies', [])


def reviewed_source(review, transport):
    """Bind a trusted review to the exact public message and current recipient."""
    mid, aid, handle = review['id'], review['author'], review['handle']
    if not MID.fullmatch(mid) or not FP.fullmatch(aid) or not HANDLE.fullmatch(handle):
        raise ValueError('Invalid reviewed recipient')
    result = read_swarm(BASE + '/e/' + mid + '?format=json', transport)
    rows = [r for r in result.get('messages', []) if r.get('id') == mid]
    if len(rows) != 1:
        raise ValueError('Reviewed source is unavailable')
    row = rows[0]
    if (row.get('author') != aid or row.get('hidden') is not False or
            digest(row.get('text', '')) != review['body_sha256'] or
            row.get('room') != 'coordination-lab' or row.get('page') != 'main'):
        raise ValueError('Reviewed source changed')
    agent = read_swarm(BASE + '/api/agent/' + aid, transport).get('agent', {})
    if agent.get('id') != aid or agent.get('handle') != handle:
        raise ValueError('Reviewed recipient changed')


def prepare_replies(state, config, reviews, transport, now, batch):
    """Only owner-reviewed literal replies from the repository enter the outbox."""
    if not (0 <= config.get('max_replies_per_day', 0) <= 3 and
            0 <= config.get('max_total_replies', 0) <= 12):
        raise ValueError('Reply limits exceed this implementation')
    if any(c['status'] in ('DELIVERY_UNKNOWN', 'ACCEPTED_UNVERIFIED', 'RESERVED') for c in outbound(state)):
        return
    local_day = now.astimezone(ZoneInfo(config['timezone'])).date()
    today = sum(any(parse_time(c[k]).astimezone(ZoneInfo(config['timezone'])).date() == local_day
                    for k in ('reserved_at', 'attempted_at') if c.get(k)) for c in state['replies'])
    budget = min(config.get('max_replies_per_day', 0) - today,
                 config.get('max_total_replies', 0) - len(state['replies']))
    seen = {r['source']['id'] for r in state['replies']}
    ids = [r['id'] for r in reviews]
    if len(ids) != len(set(ids)) or len(ids) > 50:
        raise ValueError('Duplicate or oversized review plan')
    for review in reviews:
        if review.get('service') != 'SwarmMemo' or review.get('decision') not in ('ADVICE', 'INTEREST', 'REVIEW', 'OFFER', 'DECLINED'):
            raise ValueError('Invalid review decision')
        if not FP.fullmatch(review['body_sha256']) or not review.get('reason'):
            raise ValueError('Invalid archived review')
        observation = next((x for x in state['observations']
                            if x['service'] == 'SwarmMemo' and x['id'] == review['id']), None)
        if observation is None or review['id'] in seen:
            continue
        if (observation['body_sha256'] != review['body_sha256'] or observation['author'] != review['author']):
            continue  # Stale review cannot clear the recruitment pause.
        reviewed_source(review, transport)
        observation.update(review='REVIEWED', decision=review['decision'], reason=review['reason'], reviewed_at=stamp(now))
        if review['id'] not in state['reviewed_message_ids']:
            state['reviewed_message_ids'].append(review['id'])
        if review['decision'] == 'DECLINED':
            if review['author'] not in state['suppressed_agents']:
                state['suppressed_agents'].append(review['author'])
            continue
        text = review.get('reply', '')
        if not text or budget <= 0 or review['author'] in state['suppressed_agents']:
            continue
        if not isinstance(text, str) or len(text) > 4000:
            raise ValueError('Invalid reviewed reply')
        req = dict(operation='post', room='coordination-lab', page='main', kind='note',
                   reply_to=review['id'], to=review['author'], text=text, request_id=str(uuid.uuid4()))
        source = {k: review[k] for k in ('id', 'author', 'handle', 'body_sha256')}
        state['replies'].append(dict(agent_id=review['author'], handle=review['handle'], source=source,
                                    status='RESERVED', reserved_at=stamp(now), batch=batch, request=req))
        budget -= 1
        seen.add(review['id'])


def eligible(agent, state, now):
    profile = agent.get('profile') or {}
    current = profile.get('current_agent') or {}
    aid, handle = current.get('id'), current.get('handle')
    if not isinstance(aid, str) or not FP.fullmatch(aid) or not isinstance(handle, str) or not HANDLE.fullmatch(handle):
        return None
    if profile.get('availability') != 'available' or profile.get('fresh') is not True:
        return None
    if parse_time(profile['fresh_until']) <= now:
        return None
    used = {c['agent_id'] for c in outbound(state)} | set(state['suppressed_agents'])
    handles = {c['handle'].casefold() for c in outbound(state)}
    if aid in used or handle.casefold() in handles:
        return None
    description = profile.get('description', '')
    # This campaign is unpaid; do not solicit explicitly commercial-only profiles.
    if not isinstance(description, str) or re.search(r'\b(paid|usdc|payment|for hire)\b', description, re.I):
        return None
    caps = profile.get('capabilities')
    if not isinstance(caps, list):
        return None
    match = next((x for x in MATCHES if x in caps), None)
    if not match:
        return None
    return aid, handle, match


def invitation(handle, match):
    oid, task = MATCHES[match]
    return (f'@{handle}, this is the automated outreach worker for Genius Decision, authorized by Pedro Salvadeo. '
            f'Your current public profile lists {match}; that is why we are inviting you directly.\n'
            f'Would you be interested in {oid}: {task}? Return versions, steps, evidence and limitations, '
            'or a precise critique. The full engine also welcomes mathematics, interpretation and real-case contributions.\n'
            f'Agent entry: {ENTRY} ; capsule and contribution instructions: {CAPSULE}\n'
            'Club: https://geniusdecision.app/club (optional name; registration quotas apply). '
            'Public contributions: https://geniusdecision.app/contributions (no GitHub account required). '
            'If relevant and authorized by your operator, reply here with the contribution you would investigate. '
            'Voluntary and unpaid; you can decline. No purchases, credentials or private context. '
            'This invitation does not enroll you in the separate randomized pilot.')


def prepare(state, config, transport, now, batch, contact=False, reviews=None, reply=False):
    state = copy.deepcopy(state)
    state.setdefault('replies', [])
    # A previous reserved batch may have sent before its runner stopped. Never retry it.
    for c in outbound(state):
        if c['status'] == 'RESERVED' and c.get('batch') != batch:
            c['status'] = 'DELIVERY_UNKNOWN'
    poll(state, transport, now)
    state['last_prepare_at'] = stamp(now)
    state['last_batch'] = batch
    state['last_selection'] = []
    if reply and config['enabled'] and now < parse_time(config['ends_at']) and state['poll_complete']:
        prepare_replies(state, config, reviews or [], transport, now, batch)
    if not contact or not config['enabled'] or now >= parse_time(config['ends_at']):
        state['dispatch_reason'] = 'OBSERVE_ONLY_OR_CAMPAIGN_ENDED'
        return state
    if not state['poll_complete'] or any(x['review'] == 'NEEDS_REVIEW' for x in state['observations']):
        state['dispatch_reason'] = 'REVIEW_RESPONSES_FIRST'
        return state
    if any(c['status'] in ('DELIVERY_UNKNOWN', 'ACCEPTED_UNVERIFIED', 'RESERVED') for c in outbound(state)):
        state['dispatch_reason'] = 'RESOLVE_UNCERTAIN_DELIVERY_FIRST'
        return state
    local_day = now.astimezone(ZoneInfo(config['timezone'])).date()
    today = sum(any(parse_time(c[k]).astimezone(ZoneInfo(config['timezone'])).date() == local_day
                    for k in ('reserved_at', 'attempted_at') if c.get(k)) for c in state['contacts'])
    budget = min(config['max_per_day'] - today, config['max_total_contacts'] - len(state['contacts']))
    if budget <= 0:
        state['dispatch_reason'] = 'CONTACT_LIMIT'
        return state
    listing = read_swarm(BASE + '/api/agents?sort=active&limit=50', transport)
    for agent in listing.get('agents', []):
        candidate = eligible(agent, state, now)
        if candidate is None:
            continue
        aid, _, _ = candidate
        # Re-resolve the chosen recipient immediately before reserving it.
        resolved = read_swarm(BASE + '/api/agent/' + aid, transport).get('agent', {})
        checked = eligible(resolved, state, now)
        if checked != candidate:
            continue
        aid, handle, match = checked
        req = dict(operation='post', room='coordination-lab', page='main', kind='request',
                   reply_to=ROOT_ID, to=aid, text=invitation(handle, match), request_id=str(uuid.uuid4()))
        state['contacts'].append(dict(agent_id=aid, handle=handle, match=match, status='RESERVED',
            reserved_at=stamp(now), batch=batch, request=req, response_ids=[],
            profile_url=BASE + '/api/agent/' + aid, profile_checked_at=stamp(now)))
        state['last_selection'].append(handle)
        if len(state['last_selection']) >= budget:
            break
    state['dispatch_reason'] = 'RESERVED' if state['last_selection'] else 'NO_ELIGIBLE_CANDIDATE'
    return state


def verify_contact(contact, transport):
    mid = contact['message_id']
    if not MID.fullmatch(mid):
        raise ValueError('Invalid receipt ID')
    for url in (BASE + '/e/' + mid + '?format=json',
                BASE + '/inbox/' + contact['agent_id'] + '?format=json'):
        result = read_swarm(url, transport)
        matches = [m for m in result.get('messages', []) if m.get('id') == mid]
        if len(matches) != 1:
            raise ValueError('Receipt not visible in readback and recipient inbox')
        message = matches[0]
        if any(message.get(k) != contact['request'][k] for k in ('text', 'to', 'reply_to')) or message.get('hidden') is not False:
            raise ValueError('Readback differs from exact intended delivery')


def dispatch(state, config, transport, now, batch, persist):
    if not config['enabled'] or now >= parse_time(config['ends_at']):
        return state
    if any(c['status'] in ('DELIVERY_UNKNOWN', 'ACCEPTED_UNVERIFIED') for c in outbound(state)):
        return state
    for contact in outbound(state):
        if contact['status'] != 'RESERVED' or contact.get('batch') != batch:
            continue
        if contact.get('source'):
            try:
                reviewed_source(contact['source'], transport)
            except (OSError, ValueError, KeyError, TypeError) as exc:
                contact.update(status='CANCELLED_STALE_REVIEW', error_type=type(exc).__name__)
                persist(state)
                break
        # The workflow already pushed this reservation. Local crash also fails closed.
        contact['status'] = 'DELIVERY_UNKNOWN'
        contact['attempted_at'] = stamp(now)
        persist(state)
        try:
            result = transport.request(BASE + '/v1/command', contact['request'])
            receipt = result.get('receipt', {})
            if result.get('ok') is not True or not isinstance(receipt.get('id'), str) or not MID.fullmatch(receipt['id']):
                raise ValueError('No accepted publication receipt')
            contact.update(status='ACCEPTED_UNVERIFIED', message_id=receipt['id'],
                           public_url=BASE + '/e/' + receipt['id'], accepted_at=receipt.get('accepted_at'))
            persist(state)
            verify_contact(contact, transport)
            contact['status'] = 'DELIVERED'
            contact['verified_at'] = stamp(now)
            persist(state)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            # Stop this batch; do not retry or print a server response body.
            contact['error_type'] = type(exc).__name__
            persist(state)
            break
    state['last_dispatch_at'] = stamp(now)
    persist(state)
    return state


def report(state):
    return dict(format='genius-outreach-report/1', last_poll_at=state.get('last_poll_at'),
                contacts=len(state['contacts']), delivered=sum(c['status'] == 'DELIVERED' for c in state['contacts']),
                awaiting_delivery_review=sum(c['status'] != 'DELIVERED' for c in state['contacts']),
                replies_reserved=len(state.get('replies', [])),
                replies_delivered=sum(c['status'] == 'DELIVERED' for c in state.get('replies', [])),
                replies_awaiting_delivery_review=sum(c['status'] != 'DELIVERED' for c in state.get('replies', [])),
                reviewed_responses=[{'id':x['id'], 'decision':x.get('decision')} for x in state['observations'] if x['review'] == 'REVIEWED'],
                observations_needing_review=[{'service':x['service'], 'id':x['id']} for x in state['observations'] if x['review'] == 'NEEDS_REVIEW'],
                dispatch_reason=state.get('dispatch_reason'), selected=state.get('last_selection', []),
                collaborations_accepted_by_this_worker=0, executions_verified_by_this_worker=0,
                evidence_note='This worker verifies transport only. Participation and execution require separate evidence review.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('prepare', 'dispatch', 'report'))
    parser.add_argument('--state', type=Path, required=True)
    parser.add_argument('--config', type=Path, default=Path(__file__).with_name('config.json'))
    parser.add_argument('--batch')
    parser.add_argument('--contact', action='store_true')
    parser.add_argument('--reply', action='store_true', help='Reserve literal replies from the reviewed plan')
    parser.add_argument('--reviews', type=Path, default=Path(__file__).with_name('reviews.json'))
    parser.add_argument('--reservation-committed', action='store_true')
    args = parser.parse_args()
    state = load_state(args.state)
    config = json.loads(args.config.read_text())
    if not (0 <= config['max_per_day'] <= 2 and 0 <= config['max_total_contacts'] <= 12):
        raise ValueError('Campaign limits exceed this implementation')
    now, transport = datetime.now(timezone.utc), Transport()
    if args.command != 'report' and not args.batch:
        raise ValueError('A unique execution batch is required')
    if args.command == 'prepare':
        reviews = json.loads(args.reviews.read_text())['reviews'] if args.reply else []
        state = prepare(state, config, transport, now, args.batch, args.contact, reviews, args.reply)
        save(args.state, state)
    elif args.command == 'dispatch':
        if not args.reservation_committed:
            raise ValueError('Persist the reservation remotely before dispatch')
        state = dispatch(state, config, transport, now, args.batch, lambda s: save(args.state, s))
    print(json.dumps(report(state), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({'error_type': type(error).__name__, 'status': 'STOPPED_WITHOUT_RETRY'}), file=sys.stderr)
        raise SystemExit(1)
