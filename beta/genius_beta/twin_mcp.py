"""Fixed, scoped MCP bindings for the authenticated twin REST API."""
ID = dict(type='string', pattern='^[a-f0-9]{32}$')
NAME = dict(type='string', pattern='^[A-Za-z0-9_-]+$', maxLength=100)
VERSION = dict(type='integer', minimum=0)
PAYLOAD = dict(type='object', description='Exact REST payload documented in beta/docs/AGENT_TWIN.md and twin/docs/D3_API.md. Quantities are exact strings. Never invent evidence or confirmations.')

# (method, fixed path, scope, properties, required, description)
ROUTES = {
    'twin_world_contract': ('GET', '/world/contract', 'twins:read', {}, (),
        'Read the domain-neutral construction protocol and schemas. You interpret source material and propose evidence-linked fragments; the server assembles and checks them. No domain template, server LLM call, authenticated truth or causal discovery. Read before constructing a model.'),
    'twin_field_cases': ('GET', '/field-cases', 'twins:read', {}, (),
        'List the cited real-world field cases (for example Denver Water drought, Mendoza River). Start here to learn the cycle on a real system.'),
    'twin_field_case': ('GET', '/field-cases/{case_id}', 'twins:read', {'case_id': NAME}, ('case_id',),
        'Read one field case: narrative, source-attributed system observation and world construction with exact quotes and declared hypotheses. Use observation with twin_observe_system and construction with twin_propose_world. Its hypotheses stay hypotheses.'),
    'twin_federations': ('GET', '/federations', 'twins:read', {}, (),
        'List twins of twins: cited field cases composed into a larger system (for example Denver and Lake Mead/Powell in the Colorado basin) with declared couplings and shared carriers.'),
    'twin_federation': ('GET', '/federations/{federation_id}', 'twins:read', {'federation_id': NAME}, ('federation_id',),
        'Read one federation and its frozen result: each member twin kernel-verified on its own, joint scenarios and law, joint life condition and PVS per joint route, product-order frontier with no sums, and the best joint routes for each actor. Couplings and alignments are declared hypotheses.'),
    'twin_driver_law': ('POST', '/laws/driver', 'twins:evaluate',
        {'series': dict(type='array', minItems=1, maxItems=400, items=dict(type='object', properties=dict(period=dict(type='string'), value=dict(type='string')), required=['period', 'value'])),
         'anchors': dict(type='object', minProperties=2, maxProperties=8, additionalProperties=dict(type='string')),
         'tie': dict(type='string'), 'driver': dict(type='string', maxLength=200)}, ('series', 'anchors'),
        'Derive an empirical scenario law (AM-02) for any twin from the history of one exogenous driver: snow, river flow, weekly cases, demand, prices. series: one exact value per independent period, oldest first. anchors: the driver value that defines each of the twin\'s scenarios (use the twin\'s scenario ids). Returns a law over those ids ready for the model\'s law field, or the refusals (fewer than 30 outcomes, no calibrated candidate). You declare that the driver does not depend on the compared routes and periods do not overlap; never invent history.'),
    'twin_prepare_world': ('POST', '/cases/{case_id}/world/prepare', 'twins:write',
        {'case_id': ID, 'payload': PAYLOAD}, ('case_id', 'payload'),
        'Preview a construction without saving or accepting it. Payload: base_version, construction following twin_world_contract. Returns draft/model, missing-data questions, formal diagnostics, source-span checks and boundary receipt. Missing quantities are never defaulted; null law/thresholds remain unknown. READY_FOR_REVIEW is not empirical validation.'),
    'twin_propose_world': ('POST', '/cases/{case_id}/proposals', 'twins:write',
        {'case_id': ID, 'base_version': VERSION, 'text': dict(type='string', minLength=1, maxLength=10000), 'construction': PAYLOAD},
        ('case_id', 'base_version', 'text', 'construction'),
        'Assemble a complete source-linked model and scope against the latest system observation, then save a proposal. Requires the same construction reviewed with twin_prepare_world. Uses existing confirmation, versions, quotas and native evaluation. Never invent facts, probabilities or confirmation. No physical action.'),
    'twin_system_schema': ('GET', '/systems/schema', 'twins:read', {}, (),
        'Read the schema for source-attributed observations of entities and relations. Recognition proposes bounded graph hypotheses, not empirically established systems.'),
    'twin_system_scope_schema': ('GET', '/systems/scope-schema', 'twins:read', {}, (),
        'Read the schema for system, intervention and evaluation boundaries and explicit model bindings.'),
    'twin_system_example': ('GET', '/systems/example', 'twins:read', {}, (),
        'Read a synthetic observation, model and scope example with an external affected entity missing from the numerical model.'),
    'twin_system_context': ('GET', '/cases/{case_id}/systems', 'twins:read', {'case_id': ID}, ('case_id',),
        'Read the latest system observation, candidate groupings and whether accepted boundaries require review.'),
    'twin_observe_system': ('POST', '/cases/{case_id}/systems', 'twins:write', {'case_id': ID, 'payload': PAYLOAD}, ('case_id', 'payload'),
        'Record a full source-attributed snapshot, even before a numerical model exists. Payload: base_version, observation_revision, idempotency_key, observation. Read twin_system_schema first. Never fabricate observations or measured evidence. Revisions preserve history; omissions are unknown, not absence. No model calibration or physical execution.'),
    'twin_propose_system_scope': ('POST', '/cases/{case_id}/proposals', 'twins:write',
        {'case_id': ID, 'base_version': dict(type='integer', minimum=1), 'text': dict(type='string', minLength=1, maxLength=10000), 'scope': PAYLOAD},
        ('case_id', 'base_version', 'text', 'scope'),
        'Propose reviewed system boundaries against the latest observation and current model. Read twin_system_scope_schema. Preserve known dependencies and affected entities; missing numerical bindings suspend recommendation. Uses the existing proposal/accept/evaluate flow, without changing numerical dynamics.'),
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
        'Record a source-attributed observation against a frozen prediction. Stockflow cases observe a declared stock in its declared unit: payload base_version, policy_id, scenario_id, day (0..horizon), variable (stock id), value (exact decimal or n/d), unit, observed_at (ISO8601 with zone), source, idempotency_key. The prediction is the latest completed evaluation of base_version; no automatic calibration. Never fabricate measured evidence. See the REST observation contract for required fields.'),
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
    elif name == 'twin_propose_system_scope':
        payload = {'base_version': args['base_version'], 'kind': 'system_scope',
                   'text': args['text'], 'structured': {'scope': args['scope']}}
    elif name == 'twin_propose_world':
        payload = {'base_version': args['base_version'], 'kind': 'world_model',
                   'text': args['text'], 'structured': {'construction': args['construction']}}
    elif name == 'twin_driver_law':
        payload = {k: args[k] for k in ('series', 'anchors', 'tie', 'driver') if k in args}
    elif name == 'twin_delete_case':
        payload = {'base_version': args['base_version']}
    return rest(method, path, payload, authorization)
