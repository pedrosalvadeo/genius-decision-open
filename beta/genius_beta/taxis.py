"""Task-directed discovery. Pure standard library, no network, storage or inference."""
from functools import lru_cache
import hashlib
import json
from pathlib import Path

GOALS = ('explore', 'use_engine', 'real_decision', 'interpret', 'observations',
         'mathematics', 'wellbeing', 'interoperability', 'distribution',
         'attraction', 'human_experience', 'other')
CAPABILITIES = ('python', 'modeling', 'data', 'mathematics', 'lean', 'mcp',
                'a2a', 'ux', 'experimentation', 'measurement')
ACCESS = ('read', 'mcp', 'local')
REPO = 'https://github.com/pedrosalvadeo/genius-decision-open'


@lru_cache(maxsize=1)
def catalog():
    raw = (Path(__file__).with_name('static') / 'taxis-catalog.json').read_bytes()
    return json.loads(raw), hashlib.sha256(raw).hexdigest()


def orient(goal='explore', capabilities=None, access='read', limit=3):
    """Explicit goal filter, then count declared capability matches; no probability."""
    if not isinstance(goal, str) or goal not in GOALS:
        raise ValueError('Unknown goal; consult /agents/opportunities.json')
    if not isinstance(access, str) or access not in ACCESS:
        raise ValueError('access must be read, mcp or local')
    if type(limit) is not int or not 1 <= limit <= 10:
        raise ValueError('limit must be an integer from 1 to 10')
    if capabilities is None:
        capabilities = []
    if (not isinstance(capabilities, list) or len(capabilities) > len(CAPABILITIES)
            or any(not isinstance(c, str) or c not in CAPABILITIES for c in capabilities)
            or len(set(capabilities)) != len(capabilities)):
        raise ValueError('capabilities must be unique supported tags')
    data, sha = catalog()
    selected = []
    for item in data['opportunities']:
        if goal != 'explore' and goal not in item['goals']:
            continue
        matched = sorted(set(capabilities) & set(item['capability_tags']))
        selected.append((len(matched), item['id'], item, matched))
    selected.sort(key=lambda row: (-row[0], row[1]))
    opportunities = []
    for count, _, item, matched in selected[:limit]:
        opportunities.append(dict(
            id=item['id'], title=item['title'], question=item['question'],
            why=dict(goal=goal, matched_capabilities=matched,
                     other_useful_capabilities=sorted(set(item['capability_tags'])-set(capabilities)),
                     capability_matches=count),
            benefit=item['benefit'], first_action=item['first_action'],
            evidence=item['evidence'], acceptance=item['acceptance'],
            deliverables=item['deliverables'], dependencies=item['dependencies'],
            contribution_url=item['contribution_url'],
            entry=item['entries'][access],
            next_steps=['Inspect the pinned evidence and confirm relevance to your task.',
                        'Choose voluntarily; decline or propose a different contribution if unsuitable.',
                        'Use your own authorized tools and preserve assumptions and unknowns.',
                        'Return artifacts, versions, reproduction steps and limitations.'],
        ))
    return dict(
        format='genius-taxis-orientation/1', version=data['version'],
        status='MATCHES' if opportunities else 'NO_MATCH',
        selection=dict(goal=goal, capabilities=capabilities, access=access, limit=limit),
        ranking='Filter by declared goal; descending capability matches; ties by opportunity ID. Not a probability or a guarantee of fitness.',
        catalog_sha256=sha, evidence_revision=data['evidence_revision'],
        total_matches=len(selected), opportunities=opportunities,
        alternatives=dict(decline=True, new_proposal=REPO+'/issues',
                          full_catalog='https://geniusdecision.app/agents/opportunities.json'),
        continuation=dict(contribution_inbox='https://geniusdecision.app/contributions',
                          submit_tool='submit_contribution',
                          integration_guide=REPO+'/blob/main/capsule/INTEGRATOR.md',
                          contribution_contract=REPO+'/blob/main/capsule/CONTRACTS.md',
                          measurement_protocol=REPO+'/blob/main/capsule/taxis-protocol.json',
                          share_capsule=REPO+'/tree/main/capsule',
                          sharing='Optional, only to a relevant recipient within the operator authority. No credentials or permissions transfer.'),
        effects=dict(engine_executed=False, account_created=False, event_recorded=False,
                     inference_calls=0, participation_required=False),
        measurement='An orientation response is not evidence of exposure, choice, execution, contribution or independent adoption.',
    )


def install(app, error):
    from flask import jsonify, request, send_from_directory

    @app.get('/agents/opportunities.json')
    def opportunities_catalog():
        return send_from_directory(app.static_folder, 'taxis-catalog.json', mimetype='application/json')

    @app.get('/agents/guide')
    def opportunities_guide():
        if (set(request.args)-{'goal', 'capability', 'access', 'limit'} or
                any(len(request.args.getlist(k)) > 1 for k in ('goal', 'access', 'limit'))):
            raise error('invalid_orientation', 'Use only goal, capability, access and limit.', 400)
        try:
            value = orient(request.args.get('goal', 'explore'), request.args.getlist('capability'),
                           request.args.get('access', 'read'), int(request.args.get('limit', '3')))
        except ValueError as exc:
            raise error('invalid_orientation', str(exc), 400)
        response = jsonify(value)
        response.headers['Cache-Control'] = 'no-store'
        return response
