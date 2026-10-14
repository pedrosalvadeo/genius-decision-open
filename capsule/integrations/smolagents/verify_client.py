"""Exercise a released smolagents MCP client against Genius, without an LLM.

Live mode creates one disposable machine identity, accepts only a published
synthetic fixture, performs at most one engine evaluation, and deletes that
identity. The credential stays in memory. No automatic evaluation retries.
"""

import argparse
import hashlib
import json
import logging
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import uuid4

from smolagents import MCPClient

BASE = 'https://geniusdecision.app'
SCOPES = ['twins:read', 'twins:write', 'twins:evaluate', 'twins:delete', 'account:delete']


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     ensure_ascii=False).encode()).hexdigest()


def request(method, path, payload=None, token=None):
    headers = {'Accept': 'application/json', 'User-Agent': 'Genius-smolagents-interop/1'}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    data = None if payload is None else json.dumps(payload).encode()
    if data is not None:
        headers['Content-Type'] = 'application/json'
    try:
        response = urlopen(Request(BASE + path, data=data, headers=headers, method=method), timeout=45)
    except HTTPError as exc:
        response = exc
    with response:
        raw = response.read()
        return response.status, json.loads(raw) if raw else {}


def connect(token=None):
    config = {'url': BASE + '/mcp', 'transport': 'streamable-http',
              'timeout': 45.0, 'sse_read_timeout': 45.0}
    if token:
        config['headers'] = {'Authorization': 'Bearer ' + token}
    return MCPClient(config, structured_output=True,
                     adapter_kwargs={'connect_timeout': 45,
                                     'client_session_timeout_seconds': 45.0})


def call(client, name, arguments=None):
    matches = [tool for tool in client if tool.name == name]
    if len(matches) != 1:
        raise RuntimeError('Tool unavailable or ambiguous: ' + name)
    # Invoke the native smolagents Tool returned by MCPClient/MCPAdapt.
    value = matches[0](**(arguments or {}))
    if isinstance(value, str):
        value = json.loads(value)
    if not isinstance(value, dict):
        raise RuntimeError('Expected one JSON observation: ' + name)
    if value.get('error'):
        error = value['error']
        code = error.get('code') if isinstance(error, dict) else 'unspecified'
        raise RuntimeError('Tool failed: ' + name + ' code=' + str(code))
    return value


def run(live=False):
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('mcpadapt').setLevel(logging.CRITICAL)
    receipt = {'format': 'genius-smolagents-interop/1', 'started_at': now(),
               'mode': 'live' if live else 'discovery_only', 'service_url': BASE,
               'packages': {n: version(n) for n in ('smolagents', 'mcpadapt', 'mcp', 'websockets', 'pydantic')},
               'client_path': 'MCPClient -> MCPAdapt/SmolAgentsAdapter -> smolagents.Tool.__call__',
               'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               'input_kind': 'published_synthetic_fixture', 'llm_calls': 0,
               'independent_external_adoption': False, 'empirical_validation': False,
               'execution_type': 'deterministic_native_tool_harness',
               'autonomous_llm_agent_tested': False,
               'checks': [], 'cleanup': {}, 'outcome': 'FAILED'}
    token = None

    def check(name, condition):
        receipt['checks'].append({'check': name, 'passed': bool(condition)})
        print(name, 'PASS' if condition else 'FAIL', flush=True)
        if not condition:
            raise RuntimeError('Check failed: ' + name)

    try:
        status, manifest = request('GET', '/agents/manifest.json')
        check('live_manifest', status == 200 and manifest.get('available')
              and manifest.get('mcp_available') and manifest.get('twin', {}).get('available'))
        receipt['manifest_sha256_canonical_json'] = digest(manifest)
        receipt['policy_version'] = manifest['policy_version']
        check('data_policy_and_auth', manifest['data_policy'] == 'synthetic_or_non_personal_only'
              and manifest['oauth_available'] is False)
        with connect() as public:
            receipt['public_tools'] = sorted(t.name for t in public)
            check('client_public_discovery', len(public) == 3)
            check('client_public_capabilities', call(public, 'get_capabilities')['mcp_available'])
            check('client_saved_demo', bool(call(public, 'read_demo_result', {'example': 'hours-unknown'})))
        if live:
            check('required_scopes_available', set(SCOPES) <= set(manifest['registration']['available_scopes']))
            status, issued = request('POST', '/api/agents/register', {
                'policy_version': manifest['policy_version'], 'data_policy_acknowledged': True, 'scopes': SCOPES})
            # Retain the token before assertions so cleanup can run on later failures.
            token = issued.get('credential', {}).get('token')
            check('temporary_registration', status == 201 and bool(token))
            check('exact_scope_grant', set(issued['credential']['scopes']) == set(SCOPES))
            del issued
            with connect(token) as client:
                receipt['private_tools'] = sorted(t.name for t in client)
                check('client_private_discovery', sum('twin_' in t.name for t in client) == 15)
                model = call(client, 'twin_example', {'example': 'stockflow_care'})['model']
                receipt['model_sha256_canonical_json'] = digest(model)
                check('client_twin_schema', bool(call(client, 'twin_schema', {'profile': 'STOCK_FLOW_FINITE_V1'})))
                case = call(client, 'twin_create_case', {'payload': {
                    'title': 'Disposable smolagents client verification', 'text': 'Published synthetic fixture. Software interoperability only.',
                    'profile': 'STOCK_FLOW_FINITE_V1'}})['case']
                check('client_create_case', bool(case['id']))
                proposal = call(client, 'twin_propose', {'case_id': case['id'], 'payload': {
                    'base_version': 0, 'kind': 'declared_model',
                    'text': 'Explicit reuse of the published synthetic fixture; no real-world validity claim.',
                    'structured': {'model': model}}})['proposal']
                call(client, 'twin_accept', {'proposal_id': proposal['id'], 'payload': {
                    'base_version': 0, 'confirmed': True, 'acknowledge_declared': True,
                    'idempotency_key': 'smolagents-interop-' + str(uuid4())}})
                check('client_explicit_fixture_acceptance', True)
                result = call(client, 'twin_evaluate', {'case_id': case['id'], 'version': 1})
                receipt['job_status'] = result['job']['status']
                receipt['verification'] = result.get('evaluation', {}).get('verification', {})
                check('client_engine_completed_and_verified', receipt['job_status'] == 'completed'
                      and receipt['verification'].get('valid') is True)
                check('client_job_readback', call(client, 'twin_get_job', {'job_id': result['job']['id']})['job']['id'] == result['job']['id'])
                exported = call(client, 'twin_export', {'case_id': case['id']})
                check('client_export', bool(exported))
                receipt['export_sha256_canonical_json'] = digest(exported)
                call(client, 'twin_delete_case', {'case_id': case['id'], 'base_version': 1, 'confirm': True})
                check('client_case_deleted', call(client, 'twin_list_cases')['cases'] == [])
                check('client_space_deleted', call(client, 'delete_agent_space', {'confirm': True}).get('deleted') is True)
                receipt['cleanup']['mcp_space_deleted'] = True
        receipt['outcome'] = 'PASSED'
    except Exception as exc:
        # Never serialize exception bodies, headers, configs, or credentials.
        receipt['error_type'] = type(exc).__name__
        if isinstance(exc, RuntimeError) and str(exc).startswith(('Check failed:', 'Tool failed:', 'Tool unavailable', 'Expected one JSON')):
            receipt['error'] = str(exc)
        print('FAILED', receipt['error_type'], receipt.get('error', ''), flush=True)
    finally:
        if token:
            try:
                if not receipt['cleanup'].get('mcp_space_deleted'):
                    status, _ = request('DELETE', '/api/agents/me', token=token)
                    receipt['cleanup']['fallback_delete_http_status'] = status
                    check('fallback_space_deleted', status == 204)
                status, _ = request('GET', '/api/agents/me', token=token)
                receipt['cleanup']['revoked_token_http_status'] = status
                check('temporary_token_revoked', status == 401)
            except Exception as exc:
                receipt['cleanup']['error_type'] = type(exc).__name__
                receipt['outcome'] = 'FAILED'
            token = None
        receipt['finished_at'] = now()
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live', action='store_true', help='Create, evaluate once, and delete a disposable agent space.')
    parser.add_argument('--out', type=Path, required=True, help='New JSON receipt path; credentials are never included.')
    args = parser.parse_args()
    if args.out.exists():
        parser.error('Output must be a new path')
    report = run(args.live)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + '\n')
    print('OUTCOME', report['outcome'], flush=True)
    raise SystemExit(0 if report['outcome'] == 'PASSED' else 1)
