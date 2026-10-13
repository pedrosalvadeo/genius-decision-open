"""One CI writer, two bounded private trial phases; stdlib GraphQL client.

No source/infra creation, no native autodeploy, no mutation retries. The token
exists only in this CI process, never in variables sent to the runtime.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import time
import urllib.error
import urllib.request

API = 'https://backboard.railway.com/graphql/v2'
USER_AGENT = 'GeniusDecision-CI/1.0 (+https://github.com/pedrosalvadeo/genius-decision)'
REPOSITORY = 'pedrosalvadeo/genius-decision'
REGION = 'europe-west4-drams3a'
START = 'python /app/beta/deploy/trial_supervisor.py'
FORMAT = 'genius-internal-trial/1'
SHA = re.compile(r'[0-9a-f]{40}')
DIGEST = re.compile(r'[0-9a-f]{64}')
FINISHED_INSTANCES = {'EXITED', 'STOPPED', 'REMOVED'}
BAD_DEPLOYMENTS = {'CRASHED', 'FAILED', 'REMOVED', 'SKIPPED'}
BASE_VARIABLES = {'GENIUS_ENV': 'production', 'GENIUS_DATA_DIR': '/data/genius',
                  'GENIUS_PUBLIC_URL': 'https://trial.invalid', 'RAILWAY_RUN_UID': '0'}
TRIAL_KEYS = {'GENIUS_TRIAL_PHASE', 'GENIUS_TRIAL_RUN_ID', 'GENIUS_TRIAL_EXPECTED_COMMIT'}
PRIVACY_KEYS = {'GENIUS_PRIVACY_CONTROLLER', 'GENIUS_PRIVACY_ADDRESS', 'GENIUS_PRIVACY_CONTACT'}
# Exact provider metadata names from Railway's variables reference; never allow
# the whole RAILWAY_* namespace, which also contains user-controlled settings.
PROVIDER_VARIABLES = {
    'RAILWAY_PUBLIC_DOMAIN', 'RAILWAY_PRIVATE_DOMAIN', 'RAILWAY_TCP_PROXY_DOMAIN',
    'RAILWAY_TCP_PROXY_PORT', 'RAILWAY_TCP_APPLICATION_PORT', 'RAILWAY_PROJECT_NAME',
    'RAILWAY_PROJECT_ID', 'RAILWAY_ENVIRONMENT_NAME', 'RAILWAY_ENVIRONMENT_ID',
    'RAILWAY_SERVICE_NAME', 'RAILWAY_SERVICE_ID', 'RAILWAY_REPLICA_ID',
    'RAILWAY_REPLICA_REGION', 'RAILWAY_DEPLOYMENT_ID', 'RAILWAY_SNAPSHOT_ID',
    'RAILWAY_VOLUME_NAME', 'RAILWAY_VOLUME_MOUNT_PATH', 'RAILWAY_GIT_COMMIT_SHA',
    'RAILWAY_GIT_AUTHOR', 'RAILWAY_GIT_BRANCH', 'RAILWAY_GIT_REPO_NAME',
    'RAILWAY_GIT_REPO_OWNER', 'RAILWAY_GIT_COMMIT_MESSAGE',
    # Additional provider-injected keys observed in the real READ, not present
    # among the seven configured service variables (receipt 37233795081).
    'RAILWAY_ENVIRONMENT', 'RAILWAY_VOLUME_ID'}

# Fields checked against Railway's official CLI schema at 1bc05636f79e9d094edcce48e413254c0a1a6c1d.
READ = '''query CIRead($projectId:String!,$environmentId:String!,$serviceId:String!){
 projectToken { projectId environmentId }
 environment(id:$environmentId,projectId:$projectId){id config(decryptVariables:false)
  volumeInstances(first:20){edges{node{id serviceId environmentId mountPath sizeMB region state deletedAt isPendingDeletion volume{id}}}pageInfo{hasNextPage}}}
 serviceInstance(serviceId:$serviceId,environmentId:$environmentId){id serviceId environmentId source{repo image}
  builder dockerfilePath startCommand healthcheckPath cronSchedule restartPolicyType
  domains{serviceDomains{id}customDomains{id}}
  activeDeployments{id status deploymentStopped instances{id status}}
  latestDeployment{id status deploymentStopped instances{id status}}}
 serviceInstanceAutoDeployStatus(projectId:$projectId,environmentId:$environmentId,serviceId:$serviceId){enabled}
 environmentStagedChanges(environmentId:$environmentId){patch(decryptVariables:false)}
 tcpProxies(serviceId:$serviceId,environmentId:$environmentId){id}
 variables(projectId:$projectId,environmentId:$environmentId,serviceId:$serviceId)
}'''
SCOPE = 'query CIScope { projectToken { projectId environmentId } }'
UPSERT = '''mutation CIVariables($input:VariableCollectionUpsertInput!){variableCollectionUpsert(input:$input)}'''
DEPLOY = '''mutation CISeed($serviceId:String!,$environmentId:String!,$commitSha:String!){serviceInstanceDeployV2(serviceId:$serviceId,environmentId:$environmentId,commitSha:$commitSha)}'''
REDEPLOY = '''mutation CIVerify($id:String!){deploymentRedeploy(id:$id,usePreviousImageTag:true){id}}'''
POLL = '''query CIPoll($id:String!){deployment(id:$id){id serviceId environmentId projectId status deploymentStopped instances{id status} meta url staticUrl}
 deploymentLogs(deploymentId:$id,limit:100){message attributes{key value}}}'''
IMAGE_READ = '''query CIImageRead($id:String!){deployment(id:$id){id serviceId environmentId projectId meta}
 buildLogs(deploymentId:$id,limit:200){message}}'''
RECEIVED_IMAGE_DEPLOYMENTS = ('810c7eee-2b5f-43a2-bf81-aa83439c596d', '670587b2-2c28-4df1-b63f-98072eca8d6a')


class CIError(RuntimeError):
    """Only fixed machine codes reach stdout; provider payloads never do."""

    def __init__(self, code, diagnostics=None):
        super().__init__(code)
        self.diagnostics = diagnostics or {}


def safe_http_diagnostics(error, query):
    """Keep status and query-owned schema field names, never raw error text."""
    result = {'http_status': error.code}
    media_type = str(error.headers.get('Content-Type', '')).lower() if error.headers else ''
    result['response_type'] = 'json' if 'json' in media_type else 'html' if 'html' in media_type else 'other'
    result['explicit_edge_challenge'] = bool(error.headers and error.headers.get('cf-mitigated') == 'challenge')
    if error.code != 400:
        return result
    try:
        raw = error.read(65537)
        if len(raw) > 65536:
            return result
        errors = json.loads(raw).get('errors', [])
        query_names = set(re.findall(r'\b[A-Za-z_][A-Za-z0-9_]*\b', query))
        fields = set()
        for row in errors:
            message = row.get('message', '')
            match = re.match(r'Cannot query field "([A-Za-z_][A-Za-z0-9_]*)" on type ', message)
            if match and match[1] in query_names:
                fields.add(match[1])
        if fields:
            result['unknown_query_fields'] = sorted(fields)
    except (ValueError, TypeError, AttributeError, OSError):
        pass
    return result


def require(condition, code):
    if not condition:
        raise CIError(code)


def empty_patch(value):
    return isinstance(value, (dict, list)) and all(empty_patch(v) for v in (value.values() if isinstance(value, dict) else value))


def quiet(deployment):
    if deployment is None:
        return True
    if deployment.get('status') in {'BUILDING', 'DEPLOYING', 'INITIALIZING', 'QUEUED', 'WAITING', 'NEEDS_APPROVAL', 'REMOVING'}:
        return False
    rows = deployment.get('instances')
    # A stopped flag cannot override an observed running/unknown instance.
    return (isinstance(rows, list) and all(r.get('status') in FINISHED_INSTANCES for r in rows)
            and (bool(rows) or deployment.get('deploymentStopped') is True))


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *_args, **_kwargs):
        raise CIError('API_REDIRECT_REFUSED')


class GraphQL:
    def __init__(self, token, timeout=600, opener=None, clock=time.monotonic, sleep=time.sleep):
        require(isinstance(token, str) and bool(token), 'MISSING_STAGING_SECRET')
        self.token, self.clock, self.sleep = token, clock, sleep
        self.deadline = clock() + timeout
        self.opener = opener or urllib.request.build_opener(NoRedirect)
        self.calls = 0

    def call(self, query, variables, mutation=False):
        for attempt in range(1 if mutation else 3):
            require(self.clock() < self.deadline and self.calls < 60, 'API_BUDGET_EXHAUSTED')
            self.calls += 1
            request = urllib.request.Request(API, data=json.dumps({'query': query, 'variables': variables}).encode(),
                headers={'Content-Type': 'application/json', 'Accept': 'application/json',
                         'User-Agent': USER_AGENT, 'Project-Access-Token': self.token}, method='POST')
            try:
                with self.opener.open(request, timeout=min(20, max(1, self.deadline-self.clock()))) as response:
                    raw = response.read(2097153)
                require(len(raw) <= 2097152, 'API_RESPONSE_TOO_LARGE')
                value = json.loads(raw)
                require(not value.get('errors') and isinstance(value.get('data'), dict), 'API_GRAPHQL_ERROR')
                return value['data']
            except CIError:
                raise
            except urllib.error.HTTPError as error:
                if mutation:
                    raise CIError('MUTATION_NOT_RETRIED') from None
                if error.code != 429 and not 500 <= error.code < 600:
                    raise CIError('API_HTTP_REJECTED', safe_http_diagnostics(error, query)) from None
                retry = error.headers.get('Retry-After', '') if error.headers else ''
                delay = float(retry) if re.fullmatch(r'\d+(?:\.\d+)?', retry) else 2 ** (attempt + 1)
            except (urllib.error.URLError, TimeoutError, OSError):
                if mutation:
                    raise CIError('MUTATION_OUTCOME_UNKNOWN_NO_RETRY') from None
                delay = 2 ** (attempt + 1)
            except (ValueError, TypeError):
                raise CIError('API_INVALID_JSON_NO_RETRY') from None
            require(attempt < 2 and delay < self.deadline-self.clock(), 'API_READ_RETRIES_EXHAUSTED')
            self.sleep(delay)
        raise CIError('API_READ_RETRIES_EXHAUSTED')


def validate_context(env, head):
    require(env.get('GITHUB_EVENT_NAME') == 'push' and env.get('GITHUB_REF') == 'refs/heads/deploy/staging', 'UNTRUSTED_TRIGGER')
    require(env.get('GITHUB_REPOSITORY') == REPOSITORY, 'WRONG_REPOSITORY')
    sha = env.get('GITHUB_SHA', '')
    require(SHA.fullmatch(sha) is not None and head == sha, 'CHECKOUT_SHA_MISMATCH')
    run, attempt = env.get('GITHUB_RUN_ID', ''), env.get('GITHUB_RUN_ATTEMPT', '')
    require(re.fullmatch(r'\d{1,16}', run) and re.fullmatch(r'\d{1,4}', attempt), 'INVALID_ACTION_IDENTITY')
    return sha, f'ci-{run}-{attempt}-{sha[:12]}'


def runtime_contract(data, policy, expected_variables=None):
    p, e, s, v = [policy[k] for k in ('project_id', 'environment_id', 'service_id', 'volume_id')]
    require(data['projectToken'] == {'projectId': p, 'environmentId': e}, 'TOKEN_SCOPE_MISMATCH')
    require(data['environment']['id'] == e, 'ENVIRONMENT_MISMATCH')
    staged = data['environmentStagedChanges']
    require(isinstance(staged, dict) and isinstance(staged.get('patch'), (dict, list)), 'STAGED_READBACK_SHAPE_UNVERIFIED')
    require(empty_patch(staged['patch']), 'FOREIGN_STAGED_CHANGES')
    require(data['serviceInstanceAutoDeployStatus']['enabled'] is False, 'NATIVE_AUTODEPLOY_ENABLED')
    instance = data['serviceInstance']
    config = data['environment']['config']['services'][s]
    build, deploy = config['build'], config['deploy']
    require(instance['serviceId'] == s and instance['environmentId'] == e, 'SERVICE_SCOPE_MISMATCH')
    require(instance['source']['repo'] == REPOSITORY and not instance['source'].get('image'), 'SOURCE_REPO_MISMATCH')
    # Builder is a legacy fallback enum without DOCKERFILE. The live serialized
    # config selects Dockerfile; check both surfaces, not an impossible enum.
    require(instance['builder'] == 'RAILPACK' and build['builder'] == 'DOCKERFILE'
            and instance['startCommand'] == deploy['startCommand'] == START
            and instance['dockerfilePath'] == build['dockerfilePath'] == 'beta/deploy/Dockerfile', 'RUNTIME_COMMAND_DRIFT')
    require(instance['restartPolicyType'] == 'NEVER' and not instance['healthcheckPath'] and not instance['cronSchedule'], 'RUNTIME_POLICY_DRIFT')
    require(instance['domains'] == {'serviceDomains': [], 'customDomains': []} and data['tcpProxies'] == [], 'PUBLIC_ENDPOINT_PRESENT')
    require(quiet(instance['latestDeployment']) and all(quiet(d) for d in instance['activeDeployments']), 'RUNTIME_NOT_QUIET')
    require(deploy['limitOverride']['containers'] == {'cpu': 1, 'memoryBytes': 1000000000}, 'RESOURCE_LIMIT_DRIFT')
    require(deploy['multiRegionConfig'] == {REGION: {'numReplicas': 1}}, 'REGION_OR_REPLICA_DRIFT')
    require(config['volumeMounts'] == {v: {'mountPath': '/data'}}, 'VOLUME_MOUNT_DRIFT')
    source = config['source']
    require(source['repo'] == REPOSITORY and SHA.fullmatch(source.get('commitSha', '')) is not None and not source.get('image'), 'SOURCE_PIN_MISSING')
    volumes = data['environment']['volumeInstances']
    require(volumes['pageInfo']['hasNextPage'] is False, 'VOLUME_READBACK_TRUNCATED')
    attached = [row['node'] for row in volumes['edges'] if row['node']['serviceId'] == s]
    require(len(attached) == 1, 'VOLUME_CARDINALITY')
    volume = attached[0]
    require(volume['volume']['id'] == v and volume['environmentId'] == e and volume['mountPath'] == '/data'
            and volume['sizeMB'] == 500 and volume['region'] == REGION and volume['state'] == 'READY'
            and volume['deletedAt'] is None and volume['isPendingDeletion'] is False, 'VOLUME_CONTRACT_MISMATCH')
    variables = data['variables']
    application_keys = set(BASE_VARIABLES) | TRIAL_KEYS | PRIVACY_KEYS
    require(set(variables) <= application_keys | PROVIDER_VARIABLES, 'UNEXPECTED_RUNTIME_VARIABLE')
    # Provider metadata is allowed only as injected metadata, not as explicit
    # service/environment overrides in the serialized configuration.
    configured_keys = set(config.get('variables', {})) | set(data['environment']['config'].get('variables', {}))
    require(configured_keys <= application_keys, 'UNEXPECTED_CONFIGURED_VARIABLE')
    for name, value in {'RAILWAY_PROJECT_ID': p, 'RAILWAY_ENVIRONMENT_ID': e,
                        'RAILWAY_SERVICE_ID': s, 'RAILWAY_VOLUME_MOUNT_PATH': '/data',
                        'RAILWAY_ENVIRONMENT': 'staging', 'RAILWAY_VOLUME_ID': v}.items():
        require(name not in variables or variables[name] == value, 'PROVIDER_VARIABLE_SCOPE_DRIFT')
    require(not any(variables.get(k) for k in ('RAILWAY_PUBLIC_DOMAIN', 'RAILWAY_TCP_PROXY_DOMAIN',
            'RAILWAY_TCP_PROXY_PORT', 'RAILWAY_TCP_APPLICATION_PORT')), 'PUBLIC_ENDPOINT_VARIABLE')
    require(all(variables.get(k) == value for k, value in BASE_VARIABLES.items()), 'BASE_VARIABLE_DRIFT')
    require(not any(variables.get(k) for k in PRIVACY_KEYS), 'LEGAL_FIXTURE_DRIFT')
    if expected_variables:
        require(all(variables.get(k) == value for k, value in expected_variables.items()), 'VARIABLE_READBACK_MISMATCH')
    return {'service_instance': instance['id'], 'volume_instance': volume['id'], 'volume_id': v,
            'limits': deploy['limitOverride']['containers'], 'region': REGION,
            'source_branch': source.get('branch'), 'source_pin': source['commitSha']}


def read_only_diagnostics(data, policy):
    """Describe contract shape using expected-value comparisons, not payloads."""
    def compare(value, expected):
        return 'match' if value == expected else 'null' if value is None else 'different'
    instance = data.get('serviceInstance') or {}
    config = data.get('environment', {}).get('config', {})
    service = config.get('services', {}).get(policy['service_id'], {}) if isinstance(config, dict) else {}
    build, deploy = service.get('build', {}), service.get('deploy', {})
    expected = {'builder': 'DOCKERFILE', 'dockerfilePath': 'beta/deploy/Dockerfile',
                'startCommand': START, 'restartPolicyType': 'NEVER'}
    effective = dict(build, **deploy)
    return {'instance_fields': {k: compare(instance.get(k), v) for k, v in expected.items()},
            'config_fields': {k: compare(effective.get(k), v) for k, v in expected.items()},
            'instance_builder': instance.get('builder') if instance.get('builder') in ('DOCKERFILE', 'RAILPACK', 'NIXPACKS', None) else 'other',
            'config_type': type(config).__name__,
            'variable_names': sorted(data.get('variables', {})),
            'configured_variable_names': sorted(service.get('variables', {})),
            'config_limits_match': deploy.get('limitOverride', {}).get('containers') == {'cpu': 1, 'memoryBytes': 1000000000},
            'config_regions_match': deploy.get('multiRegionConfig') == {REGION: {'numReplicas': 1}},
            'config_volume_mount_matches': service.get('volumeMounts') == {policy['volume_id']: {'mountPath': '/data'}}}


def log_receipts(rows):
    receipts = {}
    for row in rows:
        candidates = []
        text = row.get('message', '')
        if isinstance(text, str) and text.startswith('{') and len(text) <= 20000:
            try:
                candidates.append(json.loads(text))
            except ValueError:
                pass
        attributes = row.get('attributes') or []
        if attributes:
            obj = {}
            for attr in attributes:
                key, value = attr.get('key'), attr.get('value')
                require(key not in obj, 'DUPLICATE_LOG_ATTRIBUTE')
                try:
                    obj[key] = json.loads(value)
                except (ValueError, TypeError):
                    obj[key] = None
            candidates.append(obj)
        for obj in candidates:
            if isinstance(obj, dict) and obj.get('format') == FORMAT:
                require(obj.get('status') == 'PASS', 'RUNNER_REPORTED_FAILURE')
                receipts[json.dumps(obj, sort_keys=True)] = obj
    require(len(receipts) <= 1, 'CONFLICTING_RUNNER_RECEIPTS')
    return next(iter(receipts.values()), None)


def image_digest(rows):
    """Diagnostic build output only; never the deployed image acceptance gate."""
    found = set()
    for row in rows:
        match = re.fullmatch(r'containerimage\.digest: sha256:([0-9a-f]{64})', row.get('message', '').strip())
        if match:
            found.add(match.group(1))
    require(len(found) <= 1, 'CONFLICTING_IMAGE_DIGESTS')
    return next(iter(found), None)


def deployment_image_digest(deployment):
    """Provider-reported deployed image identity, observed on both cloud03 phases.

    BuildKit's containerimage.digest differs on the received seed and is absent
    on its redeploy. Never substitute it, a tag, source SHA, or snapshot UUID.
    """
    meta = deployment.get('meta')
    require(isinstance(meta, dict), 'DEPLOYMENT_METADATA_MISSING')
    value = meta.get('imageDigest')
    if value is None or value == '':
        return None
    require(isinstance(value, str), 'INVALID_DEPLOYMENT_IMAGE_DIGEST')
    match = re.fullmatch(r'(?:[A-Za-z0-9._:/-]+@)?sha256:([0-9a-f]{64})', value)
    require(match is not None, 'INVALID_DEPLOYMENT_IMAGE_DIGEST')
    return match[1]


def inspect_received_images(api, policy):
    """Bounded read-only diagnosis; never emit raw metadata or variables."""
    observations = []
    for identifier in RECEIVED_IMAGE_DEPLOYMENTS:
        data = api.call(IMAGE_READ, {'id': identifier})
        dep = data['deployment']
        require(dep['id'] == identifier and all(dep[k] == policy[v] for k, v in
            [('projectId', 'project_id'), ('environmentId', 'environment_id'), ('serviceId', 'service_id')]), 'DEPLOYMENT_SCOPE_MISMATCH')
        meta = dep.get('meta')
        require(isinstance(meta, dict), 'DEPLOYMENT_METADATA_MISSING')
        # Names/types only for schema discovery. Values are restricted to
        # explicitly named digest fields and strictly formatted SHA256 hashes.
        names = {k: type(v).__name__ for k, v in meta.items()
                 if re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,63}', k)}
        digests = {}
        for key in ('imageDigest', 'containerImageDigest', 'buildImageDigest', 'image', 'imageId'):
            value = meta.get(key)
            if isinstance(value, str):
                match = re.fullmatch(r'(?:[A-Za-z0-9._:/-]+@)?sha256:([0-9a-f]{64})', value)
                if match:
                    digests[key] = match[1]
        observations.append({'deployment_id': identifier, 'metadata_field_types': names,
            'sha256_fields': digests, 'build_log_image_sha256': image_digest(data['buildLogs']),
            'deployment_image_sha256': deployment_image_digest(dep)})
    return observations


def validate_receipt(receipt, deployment, policy, sha, run_id, phase, prior=None):
    require(deployment['projectId'] == policy['project_id'] and deployment['environmentId'] == policy['environment_id']
            and deployment['serviceId'] == policy['service_id'], 'DEPLOYMENT_SCOPE_MISMATCH')
    require(deployment['meta']['commitHash'] == sha, 'DEPLOYMENT_SHA_MISMATCH')
    require(not deployment['url'] and not deployment['staticUrl'], 'DEPLOYMENT_PUBLIC_URL')
    require(receipt['deployment_id'] == deployment['id'] and receipt['source_commit'] == sha
            and receipt['run_id'] == run_id and receipt['phase'] == phase, 'RECEIPT_IDENTITY_MISMATCH')
    require(receipt['format'] == FORMAT and receipt['status'] == 'PASS', 'RECEIPT_NOT_PASS')
    require(receipt['uid'] == receipt['gid'] == receipt['data_uid'] == 10001 and receipt['data_mode'] == '0o700'
            and receipt['process_id'] > 1 and receipt['parent_process_id'] == 1, 'RECEIPT_PROCESS_OR_PERMISSION')
    require(receipt['sockets_opened_by_probe'] == 0 and receipt['container_restart_attested_by_runner'] is False,
            'RECEIPT_SCOPE_DRIFT')
    for key in ('volume_mount_checked', 'legal_guard_rejected_startup'):
        require(receipt[key] is True, 'RECEIPT_GUARD_FAILED')
    if phase == 'seed':
        require(receipt['database_uid'] == 10001 and receipt['database_mode'] == '0o600', 'DATABASE_PERMISSIONS')
        require(receipt['engine_profiles'] == ['hours', 'fdq'] and receipt['synthetic_owner_rows_seeded'] == 2, 'SEED_CONTENT_MISMATCH')
        require(receipt['received_expected_results_matched'] is True and receipt['suspension_marker_written'] is True, 'SEED_CHECKS_MISSING')
        require(re.fullmatch(r'[0-9a-f]{32}', receipt['invocation']) is not None, 'SEED_INVOCATION_INVALID')
        require(set(receipt['artifact_sha256']) == {'kept', 'deleted'}, 'SEED_ARTIFACTS_MISSING')
        for value in [receipt['snapshot_sha256'], receipt['live_sha256'], *receipt['artifact_sha256'].values()]:
            require(isinstance(value, str) and DIGEST.fullmatch(value), 'INVALID_EVIDENCE_HASH')
    else:
        require(prior is not None and deployment['id'] != prior['deployment_id'], 'VERIFY_DEPLOYMENT_NOT_NEW')
        require(receipt['prior_deployment_id'] == prior['deployment_id'] and receipt['prior_invocation'] == prior['invocation'], 'VERIFY_SEED_LINK_MISMATCH')
        for key in ('persisted_database_hash_verified', 'deletion_ledger_preserved', 'credentials_and_consent_revoked', 'artifact_preserved', 'suspension_marker_persisted'):
            require(receipt[key] is True, 'VERIFY_CHECK_MISSING')
        require(DIGEST.fullmatch(receipt['recovered_sha256']) is not None, 'INVALID_RECOVERY_HASH')


class Orchestrator:
    def __init__(self, client, policy, sha, run_id, clock=time.monotonic, sleep=time.sleep):
        self.api, self.policy, self.sha, self.run_id = client, policy, sha, run_id
        self.clock, self.sleep = clock, sleep
        self.ids = {'projectId': policy['project_id'], 'environmentId': policy['environment_id'], 'serviceId': policy['service_id']}
        self.evidence = {'source_commit': sha, 'run_id': run_id, 'stage': 'preflight'}

    def read(self, expected=None):
        return runtime_contract(self.api.call(READ, self.ids), self.policy, expected)

    def variables(self, values):
        require(set(values) <= TRIAL_KEYS, 'UNEXPECTED_MUTATION_VARIABLE')
        result = self.api.call(UPSERT, {'input': dict(self.ids, variables=values, replace=False, skipDeploys=True)}, mutation=True)
        require(result.get('variableCollectionUpsert') is True, 'VARIABLE_MUTATION_REJECTED')

    def wait(self, deployment_id, phase, prior=None):
        deadline = min(self.api.deadline, self.clock()+300)
        observed_digest = None
        while self.clock() < deadline:
            data = self.api.call(POLL, {'id': deployment_id})
            deployment = data['deployment']
            require(deployment['id'] == deployment_id, 'DEPLOYMENT_ID_MISMATCH')
            require(deployment['status'] not in BAD_DEPLOYMENTS, 'DEPLOYMENT_FAILED')
            if deployment.get('meta', {}).get('commitHash'):
                require(deployment['meta']['commitHash'] == self.sha, 'DEPLOYMENT_SHA_MISMATCH')
            receipt = log_receipts(data['deploymentLogs'])
            digest = deployment_image_digest(deployment)
            require(not observed_digest or not digest or digest == observed_digest, 'DEPLOYMENT_IMAGE_CHANGED')
            observed_digest = digest or observed_digest
            if receipt is not None:
                validate_receipt(receipt, deployment, self.policy, self.sha, self.run_id, phase, prior)
                if deployment['status'] == 'SUCCESS' and quiet(deployment) and digest:
                    self.evidence[phase + '_provider_acceptance'] = {
                        'deployment_id': deployment_id, 'status': deployment['status'],
                        'quiet': True, 'image_sha256': digest,
                        'image_identity_source': 'Railway deployment.meta.imageDigest',
                        'source_commit': deployment['meta']['commitHash'],
                        'instance_statuses': [r['status'] for r in deployment['instances']]}
                    return receipt, digest
            self.sleep(min(15, max(0, deadline-self.clock())))
        raise CIError('PHASE_TIMEOUT_NO_ACCEPTANCE')

    def run(self):
        initial = self.read()
        values = {'GENIUS_TRIAL_EXPECTED_COMMIT': self.sha, 'GENIUS_TRIAL_RUN_ID': self.run_id, 'GENIUS_TRIAL_PHASE': 'seed'}
        self.evidence['stage'] = 'seed_variables'
        self.variables(values)
        require(self.read(values) == initial, 'CONTRACT_CHANGED_BEFORE_SEED')
        self.evidence['stage'] = 'seed_deploy'
        response = self.api.call(DEPLOY, {'environmentId': self.ids['environmentId'], 'serviceId': self.ids['serviceId'], 'commitSha': self.sha}, mutation=True)
        seed_id = response['serviceInstanceDeployV2']
        require(isinstance(seed_id, str) and re.fullmatch(r'[0-9a-f-]{36}', seed_id), 'SEED_ID_MISSING')
        self.evidence.update(seed_deployment_id=seed_id, stage='seed_poll')
        seed, seed_image = self.wait(seed_id, 'seed')
        self.evidence['stage'] = 'after_seed_readback'
        after_seed = self.read(values)
        for key in ('service_instance', 'volume_instance', 'volume_id', 'limits', 'region', 'source_branch'):
            require(after_seed[key] == initial[key], 'CONTRACT_CHANGED_AFTER_SEED')
        require(after_seed['source_pin'] in (initial['source_pin'], self.sha), 'SOURCE_PIN_CHANGED')
        self.evidence['stage'] = 'verify_variables'
        self.variables({'GENIUS_TRIAL_PHASE': 'verify'})
        values['GENIUS_TRIAL_PHASE'] = 'verify'
        require(self.read(values) == after_seed, 'CONTRACT_CHANGED_BEFORE_VERIFY')
        self.evidence['stage'] = 'verify_redeploy'
        response = self.api.call(REDEPLOY, {'id': seed_id}, mutation=True)
        verify_id = response['deploymentRedeploy']['id']
        require(isinstance(verify_id, str) and re.fullmatch(r'[0-9a-f-]{36}', verify_id) and verify_id != seed_id, 'VERIFY_DEPLOYMENT_NOT_NEW')
        self.evidence.update(verify_deployment_id=verify_id, stage='verify_poll')
        verified, verify_image = self.wait(verify_id, 'verify', seed)
        require(verify_image == seed_image, 'VERIFY_IMAGE_MISMATCH')
        self.evidence['stage'] = 'final_readback'
        require(self.read(values) == after_seed, 'CONTRACT_CHANGED_AFTER_VERIFY')
        return {'format': 'genius-ci-trial-receipt/1', 'status': 'PASS', 'source_commit': self.sha,
                'run_id': self.run_id, 'seed_deployment_id': seed_id, 'verify_deployment_id': verify_id,
                'seed_invocation': seed['invocation'], 'volume_id': initial['volume_id'], 'image_sha256': seed_image,
                'image_identity_source': 'Railway deployment.meta.imageDigest',
                'seed_provider_acceptance': self.evidence['seed_provider_acceptance'],
                'verify_provider_acceptance': self.evidence['verify_provider_acceptance'],
                'recovered_sha256': verified['recovered_sha256'], 'scope': 'private synthetic storage/engine trial; not public API/HTTPS acceptance'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--check-only', action='store_true', help='Read-only provider contract check; never changes variables or deploys')
    parser.add_argument('--inspect-images', action='store_true', help='With --check-only, inspect received deployment image metadata without emitting arbitrary values')
    args = parser.parse_args()
    result = {'format': 'genius-ci-trial-receipt/1', 'status': 'FAIL'}
    orchestrator = None
    try:
        require(not args.inspect_images or args.check_only, 'IMAGE_INSPECTION_REQUIRES_READ_ONLY')
        policy = json.loads(Path(__file__).with_name('CI_POLICY.json').read_text())
        token = os.environ.get('GENIUS_RAILWAY_STAGING_TOKEN', '')
        if args.check_only:
            result.update(mode='read_only_preflight', mutations=0, stage='token_scope')
            api = GraphQL(token, timeout=60)
            ids = {k: policy[v] for k, v in [('projectId', 'project_id'), ('environmentId', 'environment_id'), ('serviceId', 'service_id')]}
            scope = api.call(SCOPE, {})
            require(scope.get('projectToken') == {'projectId': policy['project_id'], 'environmentId': policy['environment_id']}, 'TOKEN_SCOPE_MISMATCH')
            result.update(token_scope_verified=True, stage='runtime_contract')
            data = api.call(READ, ids)
            result['readback_diagnostics'] = read_only_diagnostics(data, policy)
            runtime_contract(data, policy)
            if args.inspect_images:
                result['stage'] = 'received_image_inspection'
                result['received_image_observations'] = inspect_received_images(api, policy)
            result = dict(result, status='PASS', stage='complete')
        else:
            require(os.environ.get('GENIUS_STAGING_AUTOMATION_ENABLED') == 'true', 'AUTOMATION_NOT_ENABLED')
            head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True, stderr=subprocess.DEVNULL).strip()
            sha, run_id = validate_context(os.environ, head)
            orchestrator = Orchestrator(GraphQL(token), policy, sha, run_id)
            result = orchestrator.run()
    except Exception as error:
        if orchestrator:
            result.update(orchestrator.evidence)
        result['code'] = str(error) if isinstance(error, CIError) else 'UNEXPECTED_PROVIDER_OR_LOCAL_SCHEMA'
        if isinstance(error, CIError) and error.diagnostics:
            result['diagnostics'] = error.diagnostics
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, sort_keys=True))
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
