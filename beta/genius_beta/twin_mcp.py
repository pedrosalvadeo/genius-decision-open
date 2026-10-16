"""Fixed, scoped MCP bindings for the authenticated twin REST API."""
ID = dict(type='string', pattern='^[a-f0-9]{32}$')
NAME = dict(type='string', pattern='^[A-Za-z0-9_-]+$', maxLength=100)
VERSION = dict(type='integer', minimum=0)
PAYLOAD = dict(type='object', description='Exact REST payload documented in beta/docs/AGENT_TWIN.md and twin/docs/D3_API.md. Quantities are exact strings. Never invent evidence or confirmations.')

# (method, fixed path, scope, properties, required, description)
ROUTES = {
    'twin_capabilities': ('GET', '/capabilities', 'twins:read', {}, (),
        'Read admitted profiles, examples, execution bounds and evidence limitations.'),
    'twin_schema': ('GET', '/profiles/{profile}/schema', 'twins:read', {'profile': NAME}, ('profile',),
        'Read the exact structured model schema for an admitted twin profile.'),
    'twin_example': ('GET', '/examples/{example}/', 'twins:read', {'example': NAME}, ('example',),
        'Read a declared example; its assumptions are not observations of your case.'),
    'twin_intervention_schema': ('GET', '/interventions/schema', 'twins:read', {}, (),
        'Read the exact intervention design schema and finite expansion limits. Relations are declared directed resource transfers.'),
    'twin_intervention_example': ('GET', '/interventions/example', 'twins:read', {}, (),
        'Read a synthetic base model and intervention design; these are not measured evidence.'),
    'twin_design_interventions': ('POST', '/cases/{case_id}/proposals', 'twins:write',
        {'case_id': ID, 'base_version': dict(type='integer', minimum=1), 'text': dict(type='string', minLength=1, maxLength=10000), 'design': PAYLOAD},
        ('case_id', 'base_version', 'text', 'design'),
        'Generate alternatives by declared resource transfers, opening/closing relations and scheduling existing actions. Read twin_intervention_schema first. All finite combinations are included or the request is rejected. Returns a proposal, not an evaluation or authorization to act. Review, accept and evaluate through the existing versioned flow.'),
    'twin_list_cases': ('GET', '/cases', 'twins:read', {}, (), 'List this machine principal’s private twin cases.'),
    'twin_get_case': ('GET', '/cases/{case_id}', 'twins:read', {'case_id': ID}, ('case_id',),
        'Read versions, proposals, frozen evaluations and observations of an own case.'),
    'twin_create_case': ('POST', '/cases', 'twins:write', {'payload': PAYLOAD}, ('payload',),
        'Create an own twin dossier. Payload: text, optional title and profile. Narrative is preserved; it does not supply inferred model parameters. Only synthetic or non-personal data.'),
    'twin_save_draft': ('PATCH', '/cases/{case_id}/draft', 'twins:write', {'case_id': ID, 'payload': PAYLOAD}, ('case_id', 'payload'),
        'Save an unaccepted draft. Payload: base_version, draft_revision, text, model (object or null).'),
    'twin_propose': ('POST', '/cases/{case_id}/proposals', 'twins:write', {'case_id': ID, 'payload': PAYLOAD}, ('case_id', 'payload'),
        'Propose a material change. Payload: base_version, kind, text, structured. For declared_model, structured.model is the complete model. Does not accept the proposal.'),
    'twin_accept': ('POST', '/proposals/{proposal_id}/accept', 'twins:write', {'proposal_id': ID, 'payload': PAYLOAD}, ('proposal_id', 'payload'),
        'Accept reviewed model assumptions only within the authority granted by the decision owner. Payload: base_version, idempotency_key, confirmed=true, acknowledge_declared or acknowledge_synthetic=true. Never invent human confirmation. Acceptance does not validate empirical facts or authorize physical action.'),
    'twin_evaluate': ('POST', '/cases/{case_id}/evaluate', 'twins:evaluate', {'case_id': ID, 'version': dict(type='integer', minimum=1)}, ('case_id', 'version'),
        'Evaluate an accepted version through the real bounded engine. Consumes the shared agent job budget even on retry. Returns a frozen job receipt. Preserve verification, unknowns and all model/evidence limits; no empirical validation is implied.'),
    'twin_get_job': ('GET', '/jobs/{job_id}', 'twins:read', {'job_id': ID}, ('job_id',), 'Read an own frozen twin job and verification receipt.'),
    'twin_observe': ('POST', '/cases/{case_id}/observations', 'twins:write', {'case_id': ID, 'payload': PAYLOAD}, ('case_id', 'payload'),
        'Record a source-attributed observation against a frozen prediction. Supported only by the semillero profile; stockflow observations are not implemented. Never fabricate measured evidence. See the REST observation contract for required fields.'),
    'twin_compare': ('GET', '/cases/{case_id}/compare?before={before}&after={after}', 'twins:read', {'case_id': ID, 'before': dict(type='integer', minimum=1), 'after': dict(type='integer', minimum=1)}, ('case_id', 'before', 'after'),
        'Compare two accepted own versions while preserving changes to assumptions and evidence.'),
    'twin_export': ('GET', '/cases/{case_id}/export', 'twins:read', {'case_id': ID}, ('case_id',),
        'Export an own dossier with model versions and reproducible evaluation evidence.'),
    'twin_delete_case': ('DELETE', '/cases/{case_id}', 'twins:delete', {'case_id': ID, 'base_version': VERSION, 'confirm': dict(type='boolean', const=True)}, ('case_id', 'base_version', 'confirm'),
        'Permanently erase an own twin dossier after a version check and durable deletion record. Requires confirm=true.'),
}


def definitions(tool):
    return [tool(name, description, properties, required, scope=scope,
                 read=method == 'GET', destructive=method == 'DELETE')
            for name, (method, path, scope, properties, required, description) in ROUTES.items()]


def execute(name, args, authorization, rest):
    method, template, *_ = ROUTES[name]
    # Identifiers are validated by MCP schemas before formatting. No supplied URL.
    path = '/api/twin' + template.format(**args).rstrip('/')
    payload = args.get('payload')
    if name == 'twin_evaluate':
        payload = {'version': args['version']}
    elif name == 'twin_design_interventions':
        payload = {'base_version': args['base_version'], 'kind': 'intervention_design',
                   'text': args['text'], 'structured': {'design': args['design']}}
    elif name == 'twin_delete_case':
        payload = {'base_version': args['base_version']}
    return rest(method, path, payload, authorization)
