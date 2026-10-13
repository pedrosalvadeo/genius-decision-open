"""Strict local product policy. Documentary compatibility is not source truth.

This module never accepts caller-supplied closures or computed outcomes. The
controller calls build_response with results it has executed and persisted.
"""
from __future__ import annotations

import copy
from fractions import Fraction
import hashlib
import json
import re


class PolicyError(ValueError):
    """A request is malformed or exceeds the declared local profile."""


SUPPORTED_VERSIONS = {
    'obligations': 'genius-product-obligations/0.1.0',
    'source_compatibility': 'genius-source-compatibility/0.1.0',
    'response': 'genius-product-response/0.1.0',
    'sufficiency': 'DECISION_SUFFICIENCY/0.1.0',
    'sufficiency_profile': 'FDQ_FINITE_PATCH/0.1.0',
}
CAUSES = frozenset(('DERIVABLE', 'YA_DISPONIBLE', 'IRRELEVANTE_DEMOSTRADO',
                   'DATO_EXTERNO', 'DEFINICION_MODELO', 'PREFERENCIA',
                   'CAPACIDAD_AUSENTE', 'COMPUTO_PENDIENTE', 'DISENO_ESTUDIO'))
AXES = ('identity', 'unit', 'period', 'population', 'method')
EVIDENCE_KINDS = frozenset(('PRIMARY_OBSERVATION', 'PRIMARY_DOCUMENT',
                         'RECEIVED_DERIVATION', 'SYNTHETIC_STIPULATION',
                         'NORMATIVE_DECLARATION', 'SECONDARY_CONTEXT'))
QUALITY_DIMENSIONS = ('formal_correctness', 'coverage', 'data_provenance',
                      'model_fidelity', 'uncertainty_sensitivity', 'utility',
                      'comprehension', 'information_efficiency', 'operation',
                      'adoption_business')


def require(condition, reason):
    if not condition:
        raise PolicyError(reason)


def _text(value, reason='EXPECTED_NONEMPTY_TEXT'):
    require(isinstance(value, str) and bool(value.strip()), reason)
    return value


def _shape(obj, required, optional=(), label='OBJECT'):
    require(isinstance(obj, dict), label + '_NOT_OBJECT')
    require(set(required) <= set(obj), label + '_MISSING_FIELDS:' + ','.join(sorted(set(required) - set(obj))))
    require(set(obj) <= set(required) | set(optional), label + '_UNKNOWN_FIELDS:' + ','.join(sorted(set(obj) - set(required) - set(optional))))


def _no_float(value):
    raise PolicyError('JSON_FLOAT_OR_NONFINITE_FORBIDDEN:' + value)


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'DUPLICATE_JSON_KEY:' + key)
        result[key] = value
    return result


def loads_strict(raw):
    """Parse UTF-8 JSON preserving exact integers and rejecting ambiguity."""
    require(isinstance(raw, (bytes, str)), 'JSON_REQUIRES_BYTES_OR_TEXT')
    if isinstance(raw, bytes):
        require(len(raw) <= 8 * 1024 * 1024, 'JSON_ARTIFACT_TOO_LARGE')
        try:
            raw = raw.decode('utf-8')
        except UnicodeError as exc:
            raise PolicyError('INVALID_UTF8') from exc
    try:
        return json.loads(raw, object_pairs_hook=_pairs,
                          parse_float=_no_float, parse_constant=_no_float)
    except (json.JSONDecodeError, RecursionError, ValueError) as exc:
        if isinstance(exc, PolicyError):
            raise
        raise PolicyError('INVALID_JSON:' + str(exc)) from exc


def canonical_bytes(obj):
    try:
        return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False,
                          allow_nan=False).encode('utf-8')
    except (TypeError, ValueError, RecursionError, UnicodeError) as exc:
        raise PolicyError('NON_JSON_OBJECT') from exc


def query_digest(query):
    return hashlib.sha256(canonical_bytes(query)).hexdigest()


def exact_q(value):
    require(isinstance(value, str) and re.fullmatch(r'-?(0|[1-9][0-9]*)/[1-9][0-9]*', value) is not None,
            'EXPECTED_CANONICAL_RATIONAL')
    result = Fraction(value)
    require(f'{result.numerator}/{result.denominator}' == value, 'NONCANONICAL_RATIONAL')
    return result


def pointer_get(obj, pointer):
    require(isinstance(pointer, str), 'INVALID_JSON_POINTER')
    if pointer == '':
        return obj
    require(pointer.startswith('/'), 'INVALID_JSON_POINTER')
    try:
        for raw in pointer[1:].split('/'):
            require(re.search(r'~(?![01])', raw) is None, 'INVALID_JSON_POINTER_ESCAPE')
            key = raw.replace('~1', '/').replace('~0', '~')
            if isinstance(obj, list):
                require(re.fullmatch(r'0|[1-9][0-9]*', key) is not None, 'INVALID_ARRAY_POINTER')
                obj = obj[int(key)]
            else:
                require(isinstance(obj, dict), 'POINTER_TRAVERSES_SCALAR')
                obj = obj[key]
    except (KeyError, IndexError) as exc:
        raise PolicyError('POINTER_NOT_FOUND') from exc
    return obj


def validate_cell(cell):
    require(isinstance(cell, dict), 'CELL_NOT_OBJECT')
    state = cell.get('state')
    shapes = {
        'PV_KNOWN': ('state', 'value', 'unit', 'basis'),
        'PV_UNKNOWN': ('state', 'reasons', 'obligation_refs'),
        'PV_NOT_APPLICABLE': ('state', 'reasons', 'scope'),
        'PV_OUTSIDE_PROFILE': ('state', 'reasons', 'profile_ref'),
    }
    require(state in shapes, 'INVALID_CELL_STATE')
    _shape(cell, shapes[state], label='CELL')
    if state == 'PV_KNOWN':
        require(cell['value'] is not None and cell['value'] != '', 'KNOWN_VALUE_ABSENT')
        _text(cell['unit'], 'KNOWN_UNIT_ABSENT')
        require(bool(cell['basis']), 'KNOWN_BASIS_ABSENT')
        _reject_math_numbers(cell['value'])
        if isinstance(cell['value'], str) and '/' in cell['value'] and re.fullmatch(r'-?\d+/\d+', cell['value']):
            exact_q(cell['value'])
    else:
        require(isinstance(cell['reasons'], list) and cell['reasons'] and all(isinstance(x, str) and x.strip() for x in cell['reasons']), 'CELL_REASON_ABSENT')
        if state == 'PV_UNKNOWN':
            require(isinstance(cell['obligation_refs'], list) and cell['obligation_refs'] and all(isinstance(x, str) and x for x in cell['obligation_refs']), 'UNKNOWN_OBLIGATION_ABSENT')
    return cell


def _reject_math_numbers(value):
    require(type(value) not in (int, float), 'MATHEMATICAL_NUMBERS_REQUIRE_EXACT_STRINGS')
    if isinstance(value, dict):
        for item in value.values():
            _reject_math_numbers(item)
    elif isinstance(value, list):
        for item in value:
            _reject_math_numbers(item)


def _reject_floats(value):
    require(not isinstance(value, float), 'FLOAT_FORBIDDEN')
    if isinstance(value, dict):
        for item in value.values():
            _reject_floats(item)
    elif isinstance(value, list):
        for item in value:
            _reject_floats(item)


def _artifact_data(artifacts, ref):
    require(ref in artifacts, 'ARTIFACT_NOT_FOUND:' + str(ref))
    entry = artifacts[ref]
    require(isinstance(entry, dict) and 'bytes' in entry and 'metadata' in entry, 'INVALID_ARTIFACT_ENTRY')
    raw = entry['bytes']
    require(isinstance(raw, bytes), 'ARTIFACT_BYTES_REQUIRED')
    metadata = entry['metadata']
    digest = metadata.get('sha256', metadata.get('digest'))
    require(isinstance(digest, str) and hashlib.sha256(raw).hexdigest() == digest, 'ARTIFACT_DIGEST_MISMATCH')
    return raw


def _basis_value(basis, artifacts):
    _shape(basis, ('artifact_ref', 'pointer'), label='BASIS')
    return pointer_get(loads_strict(_artifact_data(artifacts, basis['artifact_ref'])), basis['pointer'])


def _list(value, label, nonempty=False):
    require(isinstance(value, list), label + '_NOT_LIST')
    require(not nonempty or bool(value), label + '_EMPTY')
    return value


def _revision(value):
    require(type(value) is int and value >= 1, 'INVALID_REVISION')


def _refs(value, known, label, nonempty=False):
    _list(value, label, nonempty)
    require(all(isinstance(x, str) and x in known for x in value), label + '_UNKNOWN_REFERENCE')
    require(len(value) == len(set(value)), label + '_DUPLICATE_REFERENCE')


def _descriptor(value):
    require(value is not None and value != '' and value != {}, 'ABSENT_DESCRIPTOR')
    if isinstance(value, dict) and 'state' in value:
        validate_cell(value)
        require(value['state'] != 'PV_KNOWN', 'USE_DEFINED_DESCRIPTOR_OR_UNKNOWN_CELL')
    else:
        require(isinstance(value, (str, dict, list)), 'INVALID_DESCRIPTOR')
        _reject_floats(value)


def validate_request(request, blob_reader):
    _shape(request, ('format', 'request_id', 'revision', 'supersedes', 'queries', 'artifacts',
                     'obligations', 'budget', 'operations', 'novelty'), label='REQUEST')
    require(request['format'] == 'genius-local-request/0.1.0', 'UNSUPPORTED_REQUEST_VERSION')
    require(len(canonical_bytes(request)) <= 4 * 1024 * 1024, 'REQUEST_TOO_LARGE')
    _reject_floats(request)
    _text(request['request_id']); _revision(request['revision'])
    if request['supersedes'] is not None:
        require(isinstance(request['supersedes'], (str, dict)) and bool(request['supersedes']), 'INVALID_SUPERSEDES')
    require((request['revision'] == 1) == (request['supersedes'] is None), 'REVISION_SUPERSEDES_MISMATCH')
    _shape(request['novelty'], ('reason', 'changed_refs'), label='NOVELTY')
    _text(request['novelty']['reason'])
    _list(request['novelty']['changed_refs'], 'NOVELTY_CHANGED_REFS')
    require(all(isinstance(x, str) and x for x in request['novelty']['changed_refs']), 'NOVELTY_REFERENCE_INVALID')
    budget = request['budget']
    _shape(budget, ('max_operations', 'max_certificates', 'certificate_timeout_seconds'), label='BUDGET')
    for key, low, high in (('max_operations', 0, 64), ('max_certificates', 0, 2), ('certificate_timeout_seconds', 1, 60)):
        require(type(budget[key]) is int and low <= budget[key] <= high, 'INVALID_BUDGET:' + key)
    queries = _list(request['queries'], 'QUERIES', True)
    obligations = _list(request['obligations'], 'OBLIGATIONS')
    operations = _list(request['operations'], 'OPERATIONS')
    require(len(queries) <= 32 and len(obligations) <= 256 and len(operations) <= 64, 'WORK_LIMIT_EXCEEDED')
    amap = {}
    for artifact in _list(request['artifacts'], 'ARTIFACTS'):
        _shape(artifact, ('id', 'role', 'path', 'sha256', 'evidence_kind', 'permissions'), label='ARTIFACT')
        for key in ('id', 'role', 'path'):
            _text(artifact[key])
        require(artifact['id'] not in amap, 'DUPLICATE_ARTIFACT_ID')
        require(isinstance(artifact['sha256'], str) and re.fullmatch(r'[0-9a-f]{64}', artifact['sha256']) is not None, 'INVALID_ARTIFACT_DIGEST')
        require(artifact['evidence_kind'] in EVIDENCE_KINDS, 'INVALID_EVIDENCE_KIND')
        _shape(artifact['permissions'], ('access', 'use', 'basis'), label='PERMISSIONS')
        require(artifact['permissions']['access'] in ('ALLOWED', 'UNKNOWN', 'DENIED') and artifact['permissions']['use'] in ('ALLOWED', 'UNKNOWN', 'DENIED'), 'INVALID_PERMISSION_STATE')
        _text(artifact['permissions']['basis'])
        raw = blob_reader(artifact['id'])
        require(isinstance(raw, bytes) and len(raw) <= 8 * 1024 * 1024, 'ARTIFACT_BYTE_LIMIT')
        require(hashlib.sha256(raw).hexdigest() == artifact['sha256'], 'ARTIFACT_DIGEST_MISMATCH')
        amap[artifact['id']] = {'metadata': artifact, 'bytes': raw}
    qmap = {}
    for query in queries:
        _shape(query, ('id', 'revision', 'kind', 'target_spec', 'scope', 'norm', 'artifact_refs', 'obligation_refs'), label='QUERY')
        _text(query['id']); _revision(query['revision'])
        require(query['id'] not in qmap, 'DUPLICATE_QUERY_ID')
        require(query['kind'] in ('component', 'frontier', 'selector'), 'UNSUPPORTED_QUERY_KIND')
        _shape(query['target_spec'], AXES, label='TARGET_SPEC')
        for value in query['target_spec'].values():
            _descriptor(value)
        require(isinstance(query['scope'], dict) and bool(query['scope']), 'QUERY_SCOPE_ABSENT')
        require(isinstance(query['norm'], dict) and bool(query['norm']), 'QUERY_NORM_ABSENT')
        if 'state' in query['norm']:
            validate_cell(query['norm'])
        _refs(query['artifact_refs'], amap, 'QUERY_ARTIFACTS')
        qmap[query['id']] = query
    omap = {}
    obligation_fields = ('id', 'revision', 'query_ref', 'affected_claims', 'primary_cause', 'secondary_causes',
                         'classification_basis', 'provenance', 'input_spec', 'derivation_rule', 'dependencies',
                         'owner', 'permitted_use', 'prohibited_inferences', 'status', 'closure', 'reopen',
                         'next_action', 'budget_ref', 'attempts')
    for obligation in obligations:
        _shape(obligation, obligation_fields, label='OBLIGATION')
        _text(obligation['id']); _revision(obligation['revision'])
        require(obligation['id'] not in omap, 'DUPLICATE_OBLIGATION_ID')
        require(obligation['query_ref'] in qmap, 'OBLIGATION_QUERY_UNKNOWN')
        _list(obligation['affected_claims'], 'AFFECTED_CLAIMS', True)
        require(all(isinstance(x, str) and x for x in obligation['affected_claims']), 'INVALID_AFFECTED_CLAIMS')
        require(obligation['primary_cause'] in CAUSES, 'INVALID_PRIMARY_CAUSE')
        _refs(obligation['secondary_causes'], CAUSES, 'SECONDARY_CAUSES')
        require(obligation['primary_cause'] not in obligation['secondary_causes'], 'DUPLICATE_PRIMARY_CAUSE')
        for field in ('classification_basis', 'provenance', 'permitted_use', 'prohibited_inferences'):
            require(bool(obligation[field]), 'MISSING_OBLIGATION_' + field.upper())
        spec = obligation['input_spec']
        _shape(spec, ('object', 'field', 'type', 'unit', 'period', 'population', 'method', 'state', 'reason'), label='INPUT_SPEC')
        require(spec['state'] in ('KNOWN', 'UNKNOWN', 'NOT_APPLICABLE', 'OUTSIDE_PROFILE'), 'INVALID_INPUT_SPEC_STATE')
        for key in ('object', 'field', 'type', 'unit', 'reason'):
            _text(spec[key])
        for key in ('period', 'population', 'method'):
            _descriptor(spec[key])
        rule = obligation['derivation_rule']
        require(isinstance(rule, dict) and rule.get('kind') in ('RULE', 'PENDING_RULE', 'NO_DERIVATION'), 'INVALID_DERIVATION_RULE')
        if rule['kind'] == 'RULE':
            for key in ('id', 'version', 'procedure', 'domain'):
                require(key in rule and bool(rule[key]), 'INCOMPLETE_DERIVATION_RULE:' + key)
            if isinstance(rule.get('basis'), dict) and ('artifact_ref' in rule['basis'] or 'pointer' in rule['basis']):
                _basis_value(rule['basis'], amap)
        elif rule['kind'] == 'PENDING_RULE':
            require(bool(rule.get('reason')), 'PENDING_RULE_WITHOUT_REASON')
        else:
            _text(rule.get('reason'), 'NO_DERIVATION_WITHOUT_REASON')
        owner = obligation['owner']
        _shape(owner, ('role', 'task', 'assigned_person'), label='OWNER')
        for value in owner.values():
            _text(value)
        require(obligation['status'] in ('OPEN', 'READY', 'BLOCKED', 'DEFERRED', 'CANCELLED'), 'CALLER_CLOSURE_FORBIDDEN')
        closure = obligation['closure']
        _shape(closure, ('predicate', 'witness_refs', 'verifier', 'verified'), label='CLOSURE')
        require(closure['verified'] is False, 'CALLER_VERIFIED_FORBIDDEN')
        _text(closure['predicate']); _text(closure['verifier']); _list(closure['witness_refs'], 'WITNESS_REFS')
        _shape(obligation['reopen'], ('condition', 'affected_refs'), label='REOPEN')
        _text(obligation['reopen']['condition']); _list(obligation['reopen']['affected_refs'], 'REOPEN_REFS')
        _text(obligation['next_action']); _text(obligation['budget_ref'])
        _list(obligation['attempts'], 'ATTEMPTS')
        require(not obligation['attempts'], 'CALLER_ATTEMPT_HISTORY_FORBIDDEN')
        omap[obligation['id']] = obligation
    for query in queries:
        _refs(query['obligation_refs'], omap, 'QUERY_OBLIGATIONS', True)
        require(set(query['obligation_refs']) == {o['id'] for o in obligations if o['query_ref'] == query['id']}, 'QUERY_OBLIGATION_BINDING')
    for obligation in obligations:
        seen = set()
        for dep in _list(obligation['dependencies'], 'DEPENDENCIES'):
            _shape(dep, ('ref', 'revision', 'role'), label='DEPENDENCY')
            require(dep['ref'] in omap and dep['ref'] not in seen, 'INVALID_DEPENDENCY_REFERENCE')
            require(dep['revision'] == omap[dep['ref']]['revision'], 'STALE_DEPENDENCY_REVISION')
            require(dep['role'] in ('input', 'rule', 'interface', 'permission', 'guarantee'), 'INVALID_DEPENDENCY_ROLE')
            seen.add(dep['ref'])
        if obligation['derivation_rule']['kind'] == 'PENDING_RULE' and 'obligation_ref' in obligation['derivation_rule']:
            reference = obligation['derivation_rule']['obligation_ref']
            require(reference in omap, 'PENDING_RULE_REFERENCE_UNKNOWN')
            require(any(dep['ref'] == reference and dep['role'] == 'rule' for dep in obligation['dependencies']),
                    'PENDING_RULE_REFERENCE_NOT_IN_DEPENDENCY_DAG')
    visiting, visited = set(), set()
    def visit(oid):
        require(oid not in visiting, 'CYCLIC_OBLIGATIONS')
        if oid in visited:
            return
        visiting.add(oid)
        for dep in omap[oid]['dependencies']:
            visit(dep['ref'])
        visiting.remove(oid); visited.add(oid)
    for oid in omap:
        visit(oid)
    operation_ids = set()
    parameter_fields = {
        'REUSE': ('artifact_ref', 'pointer', 'assessment'),
        'DERIVE_HOURS': ('artifact_ref', 'rule_id', 'assessment'),
        'CERTIFY_FDQ': ('input_ref', 'result_ref', 'certificate_ref'),
        'PROVE_IRRELEVANCE': ('artifact_ref', 'rule_id', 'field'),
        'EXPAND_MODEL': ('reason', 'affected_dependencies'),
        'ASSESS_SOURCE': ('assessment',),
        'REQUEST_INPUT': ('obligation_ref', 'prompt', 'unknown_allowed'),
    }
    for operation in operations:
        _shape(operation, ('id', 'query_ref', 'kind', 'obligation_refs', 'parameters'), label='OPERATION')
        _text(operation['id'])
        require(operation['id'] not in operation_ids, 'DUPLICATE_OPERATION_ID')
        operation_ids.add(operation['id'])
        require(operation['query_ref'] in qmap, 'OPERATION_QUERY_UNKNOWN')
        require(operation['kind'] in parameter_fields, 'UNSUPPORTED_OPERATION_KIND')
        _refs(operation['obligation_refs'], omap, 'OPERATION_OBLIGATIONS', True)
        require(all(omap[x]['query_ref'] == operation['query_ref'] for x in operation['obligation_refs']), 'CROSS_QUERY_OBLIGATION')
        params = operation['parameters']
        _shape(params, parameter_fields[operation['kind']], label='PARAMETERS')
        for key in ('artifact_ref', 'input_ref', 'result_ref', 'certificate_ref'):
            if key in params:
                require(params[key] in amap and params[key] in qmap[operation['query_ref']]['artifact_refs'], 'OPERATION_ARTIFACT_BINDING')
        if 'assessment' in params:
            assessment = params['assessment']
            require(assessment.get('query_ref') == operation['query_ref'], 'ASSESSMENT_QUERY_BINDING')
            require(assessment.get('target_spec') == qmap[operation['query_ref']]['target_spec'], 'ASSESSMENT_TARGET_BINDING')
            require(assessment.get('claim') in {operation['query_ref']} | {claim for oid in operation['obligation_refs'] for claim in omap[oid]['affected_claims']}, 'ASSESSMENT_CLAIM_BINDING')
            assess_source(assessment, amap)
            if 'artifact_ref' in params:
                require(assessment['source_ref'] == params['artifact_ref'], 'ASSESSMENT_SOURCE_BINDING')
        if operation['kind'] == 'REQUEST_INPUT':
            require(params['obligation_ref'] in operation['obligation_refs'], 'REQUEST_INPUT_OBLIGATION_BINDING')
            require(params['unknown_allowed'] is True, 'UNKNOWN_OPTION_REQUIRED')
            _text(params['prompt'])
    return request


def assess_source(assessment, artifacts):
    """Check documentary substitution under explicit, unauthenticated premises.

    Equal descriptors and fixed exact unit conversions are mechanical checks.
    Every equality is bound to retained source bytes. They do not authenticate
    the document or establish empirical fidelity of its content.
    """
    fields = ('assessment_id', 'revision', 'query_ref', 'claim', 'intended_use', 'target_spec',
              'source_ref', 'source_locator', 'source_version', 'source_digest',
              'observed_or_received_at', 'relevant_period', 'access_and_permissions',
              'evidence_kind', 'transformation_chain', 'axes', 'conflicts', 'verdict',
              'owner', 'closure', 'reopen')
    _shape(assessment, fields, label='ASSESSMENT')
    for key in ('assessment_id', 'query_ref', 'claim', 'intended_use', 'source_ref',
                'source_locator', 'source_version', 'observed_or_received_at'):
        _text(assessment[key])
    _revision(assessment['revision'])
    require(assessment['verdict'] == 'PENDING', 'CALLER_SOURCE_VERDICT_FORBIDDEN')
    require(assessment['evidence_kind'] in EVIDENCE_KINDS, 'INVALID_SOURCE_EVIDENCE_KIND')
    _shape(assessment['target_spec'], AXES, label='SOURCE_TARGET_SPEC')
    _shape(assessment['axes'], AXES, label='SOURCE_AXES')
    _shape(assessment['access_and_permissions'], ('access', 'use', 'basis'), label='SOURCE_PERMISSIONS')
    for key in ('access', 'use'):
        require(assessment['access_and_permissions'][key] in ('ALLOWED', 'UNKNOWN', 'DENIED'), 'SOURCE_PERMISSION_INVALID')
    _text(assessment['access_and_permissions']['basis'])
    require(bool(assessment['relevant_period']) and bool(assessment['owner']) and bool(assessment['reopen']), 'SOURCE_METADATA_ABSENT')
    require(isinstance(assessment['closure'], dict) and assessment['closure'].get('verified') is False, 'CALLER_SOURCE_CLOSURE_FORBIDDEN')
    source_available = assessment['source_digest'] != 'NOT_ACQUIRED'
    if source_available:
        raw = _artifact_data(artifacts, assessment['source_ref'])
        meta = artifacts[assessment['source_ref']]['metadata']
        require(assessment['source_digest'] == hashlib.sha256(raw).hexdigest(), 'SOURCE_DIGEST_BINDING')
        require(assessment['evidence_kind'] == meta['evidence_kind'], 'SOURCE_EVIDENCE_KIND_BINDING')
        require(assessment['access_and_permissions'] == meta['permissions'], 'SOURCE_PERMISSION_BINDING')
    transforms = {}
    outside = []
    for item in _list(assessment['transformation_chain'], 'TRANSFORMATIONS'):
        _shape(item, ('id', 'rule_id', 'source_unit', 'target_unit', 'factor', 'construct', 'basis'), label='TRANSFORM')
        require(item['id'] not in transforms, 'DUPLICATE_TRANSFORMATION')
        if item['rule_id'] != 'EXACT_UNIT_SCALE/1':
            outside.append('UNSUPPORTED_TRANSFORMATION:' + str(item['rule_id']))
        transforms[item['id']] = item
    result = copy.deepcopy(assessment)
    result['documentary_limit'] = 'BYTE_CORRESPONDENCE_AND_DECLARED_PERMISSION_ONLY; SOURCE_TRUTH_AND_EMPIRICAL_FIDELITY_NOT_AUTHENTICATED'
    computed = {}
    premise_refs = {assessment['source_ref']} if source_available else set()
    transform = None
    allowed_scales = {
        ('duration', 'min', 'h'): Fraction(1, 60),
        ('duration', 'h', 'min'): Fraction(60),
        ('mass', 'g', 'kg'): Fraction(1, 1000),
        ('mass', 'kg', 'g'): Fraction(1000),
    }
    for axis_name in AXES:
        axis = assessment['axes'][axis_name]
        _shape(axis, ('status', 'source_value', 'target_value', 'basis', 'affected_claims'), ('bridge_ref',), label='AXIS')
        require(axis['status'] in ('MATCH', 'BRIDGED', 'MISMATCH', 'UNKNOWN', 'NOT_APPLICABLE'), 'INVALID_AXIS_STATUS')
        _list(axis['affected_claims'], 'AXIS_CLAIMS', True)
        require(assessment['claim'] in axis['affected_claims'], 'AXIS_CLAIM_BINDING')
        require(axis['target_value'] == assessment['target_spec'][axis_name], 'AXIS_TARGET_BINDING')
        require((axis['status'] == 'BRIDGED') == ('bridge_ref' in axis), 'BRIDGE_REF_VARIANT')
        for desc in (axis['source_value'], axis['target_value']):
            _descriptor(desc)
        unknown = any(isinstance(desc, dict) and desc.get('state') in ('PV_UNKNOWN', 'PV_OUTSIDE_PROFILE')
                      for desc in (axis['source_value'], axis['target_value']))
        if not source_available or unknown:
            computed[axis_name] = 'UNKNOWN'
            continue
        if axis['status'] == 'NOT_APPLICABLE':
            # This local profile has no semantic proof procedure for removing an axis.
            computed[axis_name] = 'UNKNOWN'
            outside.append('AXIS_NOT_APPLICABLE_PROOF_NOT_IMPLEMENTED:' + axis_name)
            continue
        basis = axis['basis']
        if isinstance(basis, dict) and basis.get('state') == 'NOT_ACQUIRED':
            _shape(basis, ('state', 'reason'), label='MISSING_BASIS')
            _text(basis['reason'])
            computed[axis_name] = 'UNKNOWN'
            continue
        require(_basis_value(basis, artifacts) == axis['source_value'], 'SOURCE_AXIS_BASIS_MISMATCH:' + axis_name)
        premise_refs.add(basis['artifact_ref'])
        if axis['status'] == 'BRIDGED':
            if axis_name != 'unit' or axis['bridge_ref'] not in transforms:
                computed[axis_name] = 'UNKNOWN'
                outside.append('UNSUPPORTED_AXIS_BRIDGE:' + axis_name)
                continue
            bridge = transforms[axis['bridge_ref']]
            src, dst = axis['source_value'], axis['target_value']
            if bridge['rule_id'] != 'EXACT_UNIT_SCALE/1':
                computed[axis_name] = 'UNKNOWN'
                continue
            _shape(src, ('construct', 'unit'), label='SOURCE_UNIT_DESCRIPTOR')
            _shape(dst, ('construct', 'unit'), label='TARGET_UNIT_DESCRIPTOR')
            require(src['construct'] == dst['construct'] == bridge['construct'], 'UNIT_CONSTRUCT_CHANGED')
            require(src['unit'] == bridge['source_unit'] and dst['unit'] == bridge['target_unit'], 'UNIT_BRIDGE_ENDPOINT_CHANGED')
            key = (bridge['construct'], bridge['source_unit'], bridge['target_unit'])
            if key not in allowed_scales:
                computed[axis_name] = 'UNKNOWN'
                outside.append('UNSUPPORTED_UNIT_SCALE')
                continue
            factor = exact_q(bridge['factor'])
            require(factor > 0 and factor == allowed_scales[key], 'INVALID_FIXED_UNIT_FACTOR')
            statement = {key: value for key, value in bridge.items() if key != 'basis'}
            require(_basis_value(bridge['basis'], artifacts) == statement, 'UNIT_BRIDGE_BASIS_MISMATCH')
            premise_refs.add(bridge['basis']['artifact_ref'])
            computed[axis_name] = 'BRIDGED'
            transform = {'factor': bridge['factor'], 'source_unit': bridge['source_unit'],
                         'target_unit': bridge['target_unit'], 'construct': bridge['construct'],
                         'rule_id': bridge['rule_id'], 'basis': bridge['basis']}
        else:
            # A caller's MATCH/MISMATCH label cannot override actual descriptors.
            computed[axis_name] = 'MATCH' if axis['source_value'] == axis['target_value'] else 'MISMATCH'
    conflicts = _list(assessment['conflicts'], 'CONFLICTS')
    for conflict in conflicts:
        _shape(conflict, ('source_refs', 'condition', 'scope', 'consequences', 'owner', 'resolution', 'rule'), label='CONFLICT')
        _refs(conflict['source_refs'], artifacts, 'CONFLICT_SOURCE_REFS', True)
        require(len(conflict['source_refs']) >= 2, 'CONFLICT_REQUIRES_BOTH_SOURCES')
        for key in ('condition', 'scope', 'consequences', 'owner', 'rule'):
            require(bool(conflict[key]), 'CONFLICT_METADATA_ABSENT:' + key)
        if conflict['resolution'] != 'UNRESOLVED':
            outside.append('MANUAL_CONFLICT_RESOLUTION_NOT_IMPLEMENTED')
    for key in AXES:
        result['axes'][key]['status'] = computed[key]
    premise_metadata = [artifacts[ref]['metadata'] for ref in sorted(premise_refs)]
    blocked_premises = [meta['id'] for meta in premise_metadata if any(meta['permissions'][key] != 'ALLOWED' for key in ('access', 'use'))]
    conditional_premises = [meta['id'] for meta in premise_metadata if meta['evidence_kind'] == 'SYNTHETIC_STIPULATION']
    result['premise_artifact_refs'] = sorted(premise_refs)
    result['conditional_premise_refs'] = conditional_premises
    result['blocked_premise_refs'] = blocked_premises
    if not source_available or blocked_premises or any(assessment['access_and_permissions'][key] != 'ALLOWED' for key in ('access', 'use')):
        verdict = 'SC_ACCESS_BLOCKED'
    elif 'MISMATCH' in computed.values():
        verdict = 'SC_INCOMPATIBLE'
    elif conflicts or outside or 'UNKNOWN' in computed.values():
        verdict = 'SC_UNRESOLVED'
    elif conditional_premises:
        verdict = 'SC_CONDITIONAL_MODEL_ONLY'
    else:
        verdict = 'SC_COMPATIBLE_SCOPED'
    result['verdict'] = verdict
    result['profile_limitations'] = outside
    result['closure'] = {
        'verified': verdict in ('SC_COMPATIBLE_SCOPED', 'SC_CONDITIONAL_MODEL_ONLY', 'SC_INCOMPATIBLE'),
        'predicate': 'DOCUMENTARY_SUBSTITUTION_FOR_EXACT_CLAIM',
        'witness_refs': [assessment['source_ref']] if source_available else [],
        'verifier': 'genius-local-source-policy/0.1.0',
        'scope': {'query_ref': assessment['query_ref'], 'claim': assessment['claim'], 'intended_use': assessment['intended_use']},
    }
    if transform is not None:
        result['unit_transform'] = transform
    return result


def _value_states(value):
    """Find exclusive product cells; an arbitrary non-cell is not a result."""
    if isinstance(value, dict) and 'state' in value and str(value['state']).startswith('PV_'):
        validate_cell(value)
        return [value['state']]
    if isinstance(value, dict):
        return [state for item in value.values() for state in _value_states(item)]
    if isinstance(value, list):
        return [state for item in value for state in _value_states(item)]
    return []


def _unknown_refs(value):
    if isinstance(value, dict):
        if value.get('state') == 'PV_UNKNOWN':
            yield value['obligation_refs']
        else:
            for item in value.values():
                yield from _unknown_refs(item)
    elif isinstance(value, list):
        for item in value:
            yield from _unknown_refs(item)


def _answer_content(value):
    """Compare claims, not the different provenance of agreeing receipts."""
    if isinstance(value, dict):
        omitted = {'basis'} if value.get('state') == 'PV_KNOWN' else set()
        return {key: _answer_content(item) for key, item in value.items() if key not in omitted}
    if isinstance(value, list):
        return [_answer_content(item) for item in value]
    return value


def _known_cell_claims(value, path=()):
    """A known component of a partial answer can contradict another receipt."""
    if isinstance(value, dict) and str(value.get('state', '')).startswith('PV_'):
        if value['state'] == 'PV_KNOWN':
            return {path: canonical_bytes(_answer_content(value))}
        return {}
    if isinstance(value, dict):
        return {place: claim for key, item in value.items()
                for place, claim in _known_cell_claims(item, path + (key,)).items()}
    if isinstance(value, list):
        return {place: claim for index, item in enumerate(value)
                for place, claim in _known_cell_claims(item, path + (index,)).items()}
    return {}


def _receipt_conflict(outcomes):
    providers = [o for o in outcomes if o['kind'] in
                 ('REUSE', 'DERIVE_HOURS', 'CERTIFY_FDQ', 'PROVE_IRRELEVANCE')]
    full = [o for o in providers if o['status'] in ('VERIFIED', 'CONDITIONAL')
            and all(s in ('PV_KNOWN', 'PV_NOT_APPLICABLE') for s in _value_states(o['value']))]
    conflicting = len({canonical_bytes(_answer_content(o['value'])) for o in full}) > 1
    seen_claims = {}
    for outcome in providers:
        if outcome['status'] not in ('VERIFIED', 'CONDITIONAL', 'UNRESOLVED'):
            continue
        for path, claim in _known_cell_claims(outcome['value']).items():
            if path in seen_claims and seen_claims[path] != claim:
                conflicting = True
            seen_claims[path] = claim
    source_conflict = any(ev.get('source_assessment', {}).get('conflicts')
                          for outcome in outcomes for ev in outcome['evidence'])
    return bool(conflicting or source_conflict)


def build_response(request, operation_results, context):
    """Construct RC01 from controller-owned outcomes, never client assertions."""
    qmap = {q['id']: q for q in request['queries']}
    opmap = {op['id']: op for op in request['operations']}
    ledger = copy.deepcopy(context.get('ledger', {'obligations': request['obligations'], 'worklog': []}))
    # Rebuild closure from received request plus typed results. The controller's
    # provisional ledger is not an independent proof of semantic closure.
    obligations = copy.deepcopy(request['obligations'])
    require(isinstance(obligations, list), 'INVALID_LEDGER_OBLIGATIONS')
    omap = {o['id']: o for o in obligations}
    require(set(omap) == {o['id'] for o in request['obligations']}, 'LEDGER_OBLIGATION_IDENTITY')
    seen = set()
    per_query = {q: [] for q in qmap}
    pending_effects = []
    for outcome in operation_results:
        _shape(outcome, ('operation_id', 'query_ref', 'query_sha256', 'kind', 'status', 'reason',
                         'claim_source', 'value', 'evidence', 'obligation_effects', 'artifact_refs'),
               ('execution_state',), label='OUTCOME')
        oid = outcome['operation_id']
        require(oid in opmap and oid not in seen, 'INVALID_OR_DUPLICATE_OUTCOME_OPERATION')
        seen.add(oid)
        op = opmap[oid]
        require(outcome['query_ref'] == op['query_ref'] and outcome['kind'] == op['kind'], 'OUTCOME_OPERATION_BINDING')
        query = qmap[outcome['query_ref']]
        require(outcome['query_sha256'] == query_digest(query), 'OUTCOME_QUERY_DIGEST_MISMATCH')
        require(outcome['status'] in ('VERIFIED', 'CONDITIONAL', 'UNRESOLVED', 'OUTSIDE_PROFILE', 'REJECTED', 'ERROR', 'INCONCLUSIVE'), 'INVALID_OUTCOME_STATUS')
        _text(outcome['reason']); _text(outcome['claim_source'])
        _list(outcome['evidence'], 'OUTCOME_EVIDENCE'); _list(outcome['artifact_refs'], 'OUTCOME_ARTIFACTS')
        states = _value_states(outcome['value'])
        for refs in _unknown_refs(outcome['value']):
            require(set(refs) <= set(query['obligation_refs']), 'OUTCOME_UNKNOWN_OBLIGATION_BINDING')
        if outcome['status'] in ('VERIFIED', 'CONDITIONAL'):
            require(bool(states), 'VERIFIED_OUTCOME_WITHOUT_PRODUCT_VALUE')
            require(bool(outcome['evidence']) and bool(outcome['artifact_refs']), 'VERIFIED_OUTCOME_WITHOUT_EVIDENCE')
        if outcome['kind'] == 'CERTIFY_FDQ' and outcome['status'] in ('VERIFIED', 'CONDITIONAL'):
            require(outcome['status'] == 'CONDITIONAL', 'FDQ_CANNOT_PROVE_EMPIRICAL_MEMBERSHIP')
            require(query['scope'].get('real_domain_membership') == 'NOT_ESTABLISHED', 'UNSUPPORTED_FDQ_EMPIRICAL_MEMBERSHIP')
        per_query[outcome['query_ref']].append(outcome)
        allowed_causes = {
            'REUSE': {'YA_DISPONIBLE'},
            'DERIVE_HOURS': {'DERIVABLE', 'COMPUTO_PENDIENTE'},
            'CERTIFY_FDQ': {'COMPUTO_PENDIENTE', 'IRRELEVANTE_DEMOSTRADO'},
            'PROVE_IRRELEVANCE': {'IRRELEVANTE_DEMOSTRADO'},
        }
        for effect in _list(outcome['obligation_effects'], 'OBLIGATION_EFFECTS'):
            _shape(effect, ('obligation_ref', 'status', 'reason', 'witness_refs'), label='OBLIGATION_EFFECT')
            ref = effect['obligation_ref']
            require(ref in op['obligation_refs'] and ref in omap and omap[ref]['query_ref'] == op['query_ref'], 'EFFECT_QUERY_BINDING')
            require(outcome['status'] in ('VERIFIED', 'CONDITIONAL'), 'UNVERIFIED_CLOSURE_EFFECT')
            require(omap[ref]['primary_cause'] in allowed_causes.get(op['kind'], set()), 'EFFECT_CANNOT_CLOSE_THIS_CAUSE')
            require(effect['status'] in ('CLOSED_SCOPED', 'CLOSED_NOT_APPLICABLE'), 'UNSUPPORTED_EFFECT_STATUS')
            require('PV_UNKNOWN' not in states and 'PV_OUTSIDE_PROFILE' not in states, 'UNKNOWN_CANNOT_CLOSE_OBLIGATION')
            _list(effect['witness_refs'], 'EFFECT_WITNESSES', True)
            require(all(witness == oid or witness in outcome['artifact_refs'] for witness in effect['witness_refs']), 'EFFECT_WITNESS_BINDING')
            # Model/external/empirical obligations cannot be closed by changing labels.
            original = next(o for o in request['obligations'] if o['id'] == ref)
            require(original['primary_cause'] == omap[ref]['primary_cause'], 'LEDGER_CAUSE_RELABELED')
            pending_effects.append((ref, effect, outcome))
    # Conflicts invalidate closure before publishing either a response or a
    # checkpoint ledger. Rebuilding also reopens a result provisionally closed
    # by an earlier receipt in this same attempt; those old bytes remain intact.
    conflict_queries = {qid for qid, outcomes in per_query.items() if _receipt_conflict(outcomes)}
    conflict_roots = {o['id']: {o['query_ref']} for o in obligations if o['query_ref'] in conflict_queries}
    progress = True
    while progress:
        progress = False
        for obligation in obligations:
            upstream = set().union(*(conflict_roots.get(dep['ref'], set())
                                     for dep in obligation['dependencies']))
            if upstream - conflict_roots.get(obligation['id'], set()):
                conflict_roots.setdefault(obligation['id'], set()).update(upstream)
                progress = True
    for ref, roots in conflict_roots.items():
        obligation = omap[ref]
        witnesses = sorted({outcome['operation_id'] for qid in roots for outcome in per_query[qid]})
        obligation['status'] = 'BLOCKED'
        obligation['closure'] = {
            'predicate': obligation['closure']['predicate'], 'verified': False,
            'witness_refs': witnesses, 'verifier': 'genius-local-operation-policy/0.1.0',
            'reason': 'CONFLICTING_QUERY_EVIDENCE' if obligation['query_ref'] in roots else 'UPSTREAM_QUERY_CONFLICT',
            'conflict_query_refs': sorted(roots),
        }
        obligation['next_action'] = ('Resolve the retained conflicting evidence for queries '
                                     + ', '.join(sorted(roots))
                                     + ' under an admitted rule, then revalidate this obligation and its dependents.')
    # Client prose is not an executable predicate. The implemented closure
    # explicitly concerns receipt of this exact query's result, never an
    # external fact suggested by an obligation's label or free-text predicate.
    progress = True
    while progress:
        progress = False
        for ref, effect, outcome in pending_effects:
            obligation = omap[ref]
            if ref in conflict_roots:
                continue
            if obligation['status'].startswith('CLOSED_'):
                continue
            if (obligation['affected_claims'] != [obligation['query_ref']]
                    or obligation['closure']['predicate'] != 'EXACT_QUERY_RESULT_RECEIVED'
                    or any(not omap[dep['ref']]['status'].startswith('CLOSED_') for dep in obligation['dependencies'])):
                continue
            obligation['status'] = effect['status']
            obligation['closure'] = {
                'predicate': 'EXACT_QUERY_RESULT_RECEIVED',
                'witness_refs': copy.deepcopy(effect['witness_refs']),
                'verifier': 'genius-local-operation-policy/0.1.0', 'verified': True,
                'query_sha256': outcome['query_sha256'], 'reason': effect['reason'],
                'claim_source': outcome['claim_source'],
            }
            progress = True
    evidence, decisions, closed_queries = [], [], []
    for qid, query in qmap.items():
        outcomes = per_query[qid]
        providers = [o for o in outcomes if o['kind'] in ('REUSE', 'DERIVE_HOURS', 'CERTIFY_FDQ', 'PROVE_IRRELEVANCE')]
        positives = [o for o in providers if o['status'] in ('VERIFIED', 'CONDITIONAL')]
        known = [o for o in providers if o['status'] in ('VERIFIED', 'CONDITIONAL', 'UNRESOLVED') and any(s in ('PV_KNOWN', 'PV_NOT_APPLICABLE') for s in _value_states(o['value']))]
        full = [o for o in positives if all(s in ('PV_KNOWN', 'PV_NOT_APPLICABLE') for s in _value_states(o['value']))]
        unknown = [o for o in providers if 'PV_UNKNOWN' in _value_states(o['value'])]
        conflicting = qid in conflict_queries
        source_conflict = any(bool(ev.get('source_assessment', {}).get('conflicts'))
                              for o in outcomes for ev in o['evidence'])
        unresolved = [o['id'] for o in obligations if o['query_ref'] == qid and not o['status'].startswith('CLOSED_')]
        query_evidence = [copy.deepcopy(item) for o in outcomes for item in o['evidence']]
        upstream_conflict = any(o['id'] in conflict_roots for o in obligations if o['query_ref'] == qid)
        if conflicting or source_conflict:
            ev_state, decision_state = 'EV_CONFLICTING', 'PR_PARTIAL' if known else 'PR_DEPENDENCY'
            reason = 'CONFLICTING_VERIFIED_DOCUMENTARY_OUTPUTS_RETAINED_SEPARATELY'
        elif upstream_conflict:
            ev_state = 'EV_INSUFFICIENT'
            decision_state = 'PR_PARTIAL' if known else 'PR_DEPENDENCY'
            reason = 'UPSTREAM_QUERY_CONFLICT_REQUIRES_REVALIDATION'
        elif full:
            conditional = any(o['status'] == 'CONDITIONAL' for o in full)
            ev_state = 'EV_CONDITIONAL' if conditional else 'EV_SUPPORTED_SCOPED'
            decision_state = 'PR_JUSTIFIED_RESULT'
            reason = 'EXACT_SCOPED_QUERY_VERIFIED'
            if query['kind'] == 'frontier':
                decision_state = 'PR_SET_OR_INCOMPARABLE'
            elif query['kind'] == 'selector':
                value = full[-1]['value']
                claim = value.get('value', {}) if isinstance(value, dict) else {}
                selector = claim.get('selector', {}) if isinstance(claim, dict) else {}
                if selector.get('state') != 'DEFINED':
                    decision_state = 'PR_JUSTIFIED_RESULT'
                    reason = 'VERIFIED_SELECTOR_ABSENT_WITH_RECORDED_CAUSE'
            infeasible = next((ev for o in full if o['kind'] == 'CERTIFY_FDQ' for ev in o['evidence']
                               if ev.get('all_policies_refuted') is True and ev.get('hard_witnesses')
                               and ev.get('coverage', {}).get('target') == query['scope'].get('target')
                               and ev.get('coverage', {}).get('scope') == 'ENTIRE_DECLARED_FINITE_FAMILY'), None)
            if infeasible is not None:
                decision_state = 'PR_PROVEN_INFEASIBLE'
                reason = 'ALL_POLICIES_REFUTED_IN_EVERY_MEMBER_OF_DECLARED_FINITE_FAMILY'
            # Only the exact finite formal query is answered by an FDQ outcome.
            closed_queries.append(qid)
        elif known:
            ev_state, decision_state, reason = 'EV_INSUFFICIENT', 'PR_PARTIAL', 'ONLY_SOME_COMPONENTS_VERIFIED'
        elif outcomes and all(o['status'] == 'OUTSIDE_PROFILE' for o in outcomes):
            ev_state, decision_state, reason = 'EV_OUTSIDE_SCOPE', 'PR_OUTSIDE_PROFILE', 'QUERY_OUTSIDE_CONTRACTED_PROFILE'
        elif outcomes or unresolved:
            ev_state, decision_state, reason = 'EV_INSUFFICIENT', 'PR_DEPENDENCY', 'EXACT_QUERY_UNRESOLVED'
        else:
            ev_state, decision_state, reason = 'EV_NOT_EVALUATED', 'PR_NOT_EVALUATED', 'NO_UTILIZABLE_EVALUATION_RECEIVED'
        evidence.append({'query_ref': qid, 'query_sha256': query_digest(query), 'state': ev_state,
                         'records': query_evidence, 'limits': ['No empirical fidelity, utility, understanding or permission to act inferred.']})
        decisions.append({
            'query_ref': qid, 'query_sha256': query_digest(query), 'state': decision_state,
            'reason': reason, 'scope': copy.deepcopy(query['scope']), 'norm': copy.deepcopy(query['norm']),
            'answers': [{'operation_id': o['operation_id'], 'claim_source': o['claim_source'],
                         'value': copy.deepcopy(o['value']), 'artifact_refs': copy.deepcopy(o['artifact_refs'])} for o in known],
            'observed_values': [{'operation_id': o['operation_id'], 'status': o['status'], 'reason': o['reason'],
                                 'claim_source': o['claim_source'], 'value': copy.deepcopy(o['value']),
                                 'artifact_refs': copy.deepcopy(o['artifact_refs'])} for o in providers],
            'unresolved_obligations': unresolved,
            'permitted_use': 'Formal conditional model or documentary component only; no empirical intervention authorized.',
        })
        if decision_state == 'PR_PROVEN_INFEASIBLE':
            decisions[-1]['coverage'] = 'EXHAUSTIVE'
            decisions[-1]['coverage_scope'] = 'DECLARED_FINITE_COMPLETIONS_ONLY; ORIGINAL_PARTIAL_RESULT_UNCHANGED'
            decisions[-1]['witnesses'] = copy.deepcopy(infeasible['hard_witnesses'])
    execution = copy.deepcopy(context['execution'])
    require(execution.get('state') in ('PE_COMPLETE', 'PE_PARTIAL', 'PE_NOT_STARTED', 'PE_BUDGET_EXHAUSTED', 'PE_ERROR', 'PE_CANCELLED', 'PE_UNKNOWN'), 'INVALID_EXECUTION_STATE')
    require(execution['state'] != 'PE_COMPLETE' or len(seen) == len(request['operations']), 'COMPLETE_WITH_UNFINISHED_OPERATIONS')
    unresolved = [o['id'] for o in obligations if not o['status'].startswith('CLOSED_')]
    reason = context.get('closure_reason') or execution.get('reason', 'LOCAL_ATTEMPT_FINISHED')
    if execution['state'] == 'PE_CANCELLED' or reason in ('CANCELLED', 'CANCELLATION_REQUESTED', 'CANCEL_REQUESTED'):
        closure_state = 'PC_CANCELLED'
    elif execution['state'] == 'PE_BUDGET_EXHAUSTED' or reason in ('BUDGET_EXHAUSTED', 'CERTIFICATE_TIMEOUT'):
        closure_state = 'PC_BUDGET_EXHAUSTED'
    elif execution['state'] == 'PE_ERROR':
        closure_state = 'PC_ERROR'
    elif len(closed_queries) == len(qmap) and not unresolved:
        closure_state = 'PC_ANSWERED_SCOPED'
    elif all(d['state'] == 'PR_OUTSIDE_PROFILE' for d in decisions):
        closure_state = 'PC_OUTSIDE_PROFILE'
    elif closed_queries or any(d['state'] == 'PR_PARTIAL' for d in decisions):
        closure_state = 'PC_PARTIAL'
    else:
        closure_state = 'PC_WAITING_DEPENDENCY'
    artifacts = copy.deepcopy(context['artifacts'])
    _shape(artifacts, ('received', 'expected'), label='RESPONSE_ARTIFACTS')
    received = _list(artifacts['received'], 'RECEIVED_ARTIFACTS')
    expected = _list(artifacts['expected'], 'EXPECTED_ARTIFACTS')
    received_ids = {a.get('id') for a in received}
    for obj in expected:
        require(obj.get('state') in ('RECEIVED', 'NOT_CREATED', 'NOT_RECEIVED', 'UNKNOWN'), 'INVALID_EXPECTED_ARTIFACT_STATE')
        if obj['state'] == 'RECEIVED':
            ref = obj.get('ref', obj.get('artifact_ref', obj.get('id')))
            require(ref in received_ids, 'EXPECTED_RECEIVED_WITHOUT_ARTIFACT')
        else:
            require(not any(key in obj for key in ('sha256', 'digest', 'artifact_ref')), 'ABSENT_ARTIFACT_HAS_FAKE_IDENTITY')
            require(bool(obj.get('reason')) and bool(obj.get('obligation_ref', obj.get('obligation_refs'))), 'ABSENT_ARTIFACT_WITHOUT_REASON_OR_OBLIGATION')
    quality = {name: {'state': 'NOT_ASSESSED', 'scope': 'This local attempt', 'evidence': [],
                      'conclusion': 'No empirical assessment performed.',
                      'limit': 'Formal verification and document identity do not establish this dimension.'}
               for name in QUALITY_DIMENSIONS}
    if seen:
        quality['operation'] = {'state': 'ASSESSED', 'scope': 'Observed local operations only',
                                'evidence': sorted(seen), 'conclusion': execution['state'],
                                'limit': 'No availability, concurrency, empirical utility or business claim.'}
    if closed_queries:
        quality['formal_correctness'] = {'state': 'ASSESSED', 'scope': 'Only received exact component or finite FDQ query',
                                       'evidence': closed_queries, 'conclusion': 'Scoped checks completed.',
                                       'limit': 'No general theorem extension or empirical fidelity inferred.'}
    versions = copy.deepcopy(context.get('versions', SUPPORTED_VERSIONS))
    require(versions == SUPPORTED_VERSIONS, 'UNSUPPORTED_RESPONSE_VERSIONS')
    request_ref = copy.deepcopy(context['request_ref'])
    response = {
        'format': 'genius-product-response/0.1.0',
        'response_id': request['request_id'] + ':response:' + str(request['revision']),
        'revision': request['revision'], 'request_ref': request_ref,
        'supersedes': copy.deepcopy(request['supersedes']), 'versions': versions,
        'queries': copy.deepcopy(request['queries']), 'artifacts': artifacts,
        'transport': {'state': 'PT_DELIVERED', 'reason': 'LOCAL_RESPONSE_CONSTRUCTED_AND_VALIDATED',
                      'last_verified_artifacts': sorted(a['id'] for a in received),
                      'limits': 'Delivery describes this received local envelope, not a remote RPC or scientific validity.'},
        'execution': execution, 'evidence': evidence, 'decisions': decisions,
        'obligations_ref': {'request_ref': request_ref, 'record': {'format': 'genius-product-obligations/0.1.0',
                            'record_id': request['request_id'], 'revision': request['revision'],
                            'supersedes': copy.deepcopy(request['supersedes']), 'queries': copy.deepcopy(request['queries']),
                            'obligations': obligations, 'budget': copy.deepcopy(request['budget']),
                            'worklog': copy.deepcopy(ledger.get('worklog', []))}},
        'quality': quality,
        'closure': {'state': closure_state, 'reason': reason, 'closed_queries': closed_queries,
                    'unresolved_obligations': unresolved, 'last_verified_artifacts': sorted(a['id'] for a in received),
                    'budget_used': copy.deepcopy(context['budget_used']),
                    'next_action': 'Continue only with a pertinent new input, rule, query, permission or budget and a linked revision.' if unresolved or closure_state != 'PC_ANSWERED_SCOPED' else 'Use only the answered scoped conclusions; new purposes require a new query.',
                    'owner': 'Local requester and the functional owners named by each obligation',
                    'reopen_condition': 'A relevant premise, source, query, support, rule, permission or capability changes.',
                    'superseded_by': None},
        'permitted_use': ['Documentary or formal conditional local decision support only.',
                          'No empirical validation, human comprehension, utility or permission to intervene is established.'],
    }
    return response
