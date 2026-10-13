"""Focused orchestration tests. Fake provider only; no token, network or cloud."""
from copy import deepcopy
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import urllib.error

import CI_orchestrate as ci

POLICY = json.loads(Path(__file__).with_name('CI_POLICY.json').read_text())
SHA = 'a' * 40
RUN = 'ci-123-1-' + SHA[:12]
SEED_ID = '11111111-1111-4111-8111-111111111111'
VERIFY_ID = '22222222-2222-4222-8222-222222222222'
IMAGE = 'b' * 64


def deployment(identifier):
    return dict(id=identifier, serviceId=POLICY['service_id'], environmentId=POLICY['environment_id'],
                projectId=POLICY['project_id'], status='SUCCESS', deploymentStopped=False,
                instances=[{'id': 'replica', 'status': 'EXITED'}], meta={'commitHash': SHA, 'imageDigest': 'sha256:' + IMAGE}, url=None, staticUrl=None)


def receipt(phase):
    value = dict(format=ci.FORMAT, status='PASS', deployment_id=SEED_ID if phase == 'seed' else VERIFY_ID,
                 source_commit=SHA, run_id=RUN, phase=phase, uid=10001, gid=10001, data_uid=10001,
                 data_mode='0o700', process_id=2, parent_process_id=1, sockets_opened_by_probe=0,
                 container_restart_attested_by_runner=False, volume_mount_checked=True,
                 legal_guard_rejected_startup=True)
    if phase == 'seed':
        value.update(database_uid=10001, database_mode='0o600', engine_profiles=['hours', 'fdq'],
                     synthetic_owner_rows_seeded=2, received_expected_results_matched=True,
                     suspension_marker_written=True, invocation='c' * 32, snapshot_sha256='d' * 64,
                     live_sha256='e' * 64, artifact_sha256={'kept': 'f' * 64, 'deleted': '0' * 64})
    else:
        value.update(prior_deployment_id=SEED_ID, prior_invocation='c' * 32, persisted_database_hash_verified=True,
                     deletion_ledger_preserved=True, credentials_and_consent_revoked=True,
                     artifact_preserved=True, suspension_marker_persisted=True, recovered_sha256='1' * 64)
    return value


def initial_read():
    p, e, s, v = [POLICY[k] for k in ('project_id', 'environment_id', 'service_id', 'volume_id')]
    return dict(projectToken={'projectId': p, 'environmentId': e},
        environment={'id': e, 'config': {'services': {s: {
            'source': {'repo': ci.REPOSITORY, 'branch': 'trial/received-historical', 'commitSha': '9' * 40},
            'build': {'builder': 'DOCKERFILE', 'dockerfilePath': 'beta/deploy/Dockerfile'},
            'deploy': {'startCommand': ci.START, 'restartPolicyType': 'NEVER',
                       'limitOverride': {'containers': {'cpu': 1, 'memoryBytes': 1000000000}},
                       'multiRegionConfig': {ci.REGION: {'numReplicas': 1}}},
            'volumeMounts': {v: {'mountPath': '/data'}}}}},
            'volumeInstances': {'pageInfo': {'hasNextPage': False}, 'edges': [{'node': {
                'id': 'volume-instance', 'serviceId': s, 'environmentId': e, 'mountPath': '/data',
                'sizeMB': 500, 'region': ci.REGION, 'state': 'READY', 'deletedAt': None,
                'isPendingDeletion': False, 'volume': {'id': v}}}]}},
        serviceInstance={'id': 'service-instance', 'serviceId': s, 'environmentId': e,
            'source': {'repo': ci.REPOSITORY, 'image': None}, 'builder': 'RAILPACK',
            'dockerfilePath': 'beta/deploy/Dockerfile', 'startCommand': ci.START, 'healthcheckPath': None,
            'cronSchedule': None, 'restartPolicyType': 'NEVER',
            'domains': {'serviceDomains': [], 'customDomains': []}, 'activeDeployments': [],
            'latestDeployment': deployment('33333333-3333-4333-8333-333333333333')},
        serviceInstanceAutoDeployStatus={'enabled': False}, environmentStagedChanges={'patch': {}},
        tcpProxies=[], variables=dict(ci.BASE_VARIABLES))


def poll(phase):
    return {'deployment': deployment(SEED_ID if phase == 'seed' else VERIFY_ID),
            'deploymentLogs': [{'message': '', 'attributes': [
                {'key': k, 'value': json.dumps(v)} for k, v in receipt(phase).items()]}],
            'buildLogs': [{'message': 'containerimage.digest: sha256:' + IMAGE}]}


class Clock:
    now = 0
    def __call__(self):
        return self.now
    def sleep(self, seconds):
        self.now += seconds


class Provider:
    def __init__(self):
        self.clock = Clock()
        self.deadline = 600
        self.data = initial_read()
        self.calls = []
        self.seed = poll('seed')
        self.verify = poll('verify')
        self.hook = lambda _query, _variables: None
        self.redeploy_id = VERIFY_ID
    def call(self, query, variables, mutation=False):
        self.calls.append((query, deepcopy(variables), mutation))
        self.hook(query, variables)
        if query == ci.SCOPE:
            return {'projectToken': deepcopy(self.data['projectToken'])}
        if query == ci.READ:
            return deepcopy(self.data)
        if query == ci.UPSERT:
            self.data['variables'].update(variables['input']['variables'])
            return {'variableCollectionUpsert': True}
        if query == ci.DEPLOY:
            return {'serviceInstanceDeployV2': SEED_ID}
        if query == ci.REDEPLOY:
            return {'deploymentRedeploy': {'id': self.redeploy_id}}
        if query == ci.POLL:
            return deepcopy(self.seed if variables['id'] == SEED_ID else self.verify)
        raise AssertionError('Unexpected operation')
    def runner(self):
        return ci.Orchestrator(self, POLICY, SHA, RUN, self.clock, self.clock.sleep)
    def mutations(self):
        return [(q, v) for q, v, mut in self.calls if mut]


class OrchestrationTests(unittest.TestCase):
    def test_image_inspection_never_emits_arbitrary_metadata_values(self):
        class ImageProvider:
            def call(self, query, variables):
                self.assert_query = query
                dep = deployment(variables['id'])
                dep['meta'].update(imageDigest='sha256:' + IMAGE,
                    image='registry.example/service@sha256:' + IMAGE,
                    token='never-emit-me', config={'variables': {'SECRET': 'never-emit-me'}},
                    imageId='arbitrary-secret')
                return {'deployment': dep, 'buildLogs': []}
        provider = ImageProvider()
        rows = ci.inspect_received_images(provider, POLICY)
        self.assertEqual(provider.assert_query, ci.IMAGE_READ)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['sha256_fields'], {'imageDigest': IMAGE, 'image': IMAGE})
        self.assertNotIn('never-emit-me', json.dumps(rows))
        self.assertNotIn('arbitrary-secret', json.dumps(rows))
        self.assertNotIn('variables', json.dumps(rows))

    def test_provider_metadata_is_scoped_and_cannot_hide_configuration(self):
        data = initial_read()
        data['variables'].update(RAILWAY_PROJECT_ID=POLICY['project_id'],
            RAILWAY_ENVIRONMENT_ID=POLICY['environment_id'], RAILWAY_SERVICE_ID=POLICY['service_id'],
            RAILWAY_PRIVATE_DOMAIN='probe.railway.internal', RAILWAY_VOLUME_MOUNT_PATH='/data',
            RAILWAY_ENVIRONMENT='staging', RAILWAY_VOLUME_ID=POLICY['volume_id'])
        ci.runtime_contract(data, POLICY)
        for key, value, code in [('RAILWAY_SERVICE_ID', 'other', 'PROVIDER_VARIABLE_SCOPE_DRIFT'),
                                 ('RAILWAY_VOLUME_ID', 'other', 'PROVIDER_VARIABLE_SCOPE_DRIFT'),
                                 ('RAILWAY_ENVIRONMENT', 'production', 'PROVIDER_VARIABLE_SCOPE_DRIFT'),
                                 ('RAILWAY_VOLUME_MOUNT_PATH', '/other', 'PROVIDER_VARIABLE_SCOPE_DRIFT'),
                                 ('RAILWAY_PUBLIC_DOMAIN', 'public.example', 'PUBLIC_ENDPOINT_VARIABLE'),
                                 ('RAILWAY_DOCKERFILE_PATH', 'other', 'UNEXPECTED_RUNTIME_VARIABLE'),
                                 ('GENIUS_RAILWAY_STAGING_TOKEN', 'fake-secret', 'UNEXPECTED_RUNTIME_VARIABLE')]:
            with self.subTest(key=key):
                changed = deepcopy(data); changed['variables'][key] = value
                with self.assertRaisesRegex(ci.CIError, '^' + code + '$'):
                    ci.runtime_contract(changed, POLICY)
        data['environment']['config']['services'][POLICY['service_id']]['variables'] = {'RAILWAY_SERVICE_ID': {'value': POLICY['service_id']}}
        with self.assertRaisesRegex(ci.CIError, '^UNEXPECTED_CONFIGURED_VARIABLE$'):
            ci.runtime_contract(data, POLICY)

    def test_effective_dockerfile_and_legacy_fallback_are_both_checked(self):
        for change in ('config_builder', 'config_path', 'config_command', 'instance_builder'):
            with self.subTest(change=change):
                api = Provider()
                config = api.data['environment']['config']['services'][POLICY['service_id']]
                if change == 'config_builder':
                    config['build']['builder'] = 'RAILPACK'
                elif change == 'config_path':
                    config['build']['dockerfilePath'] = 'other/Dockerfile'
                elif change == 'config_command':
                    config['deploy']['startCommand'] = 'other-command'
                else:
                    api.data['serviceInstance']['builder'] = 'NIXPACKS'
                self.expect_failure(api, 'RUNTIME_COMMAND_DRIFT')
                self.assertEqual(api.mutations(), [])

    def test_readonly_diagnostics_never_print_arbitrary_config_or_variable_values(self):
        data = initial_read()
        data['variables']['GENIUS_TRIAL_RUN_ID'] = 'do-not-print-value'
        data['serviceInstance']['startCommand'] = 'do-not-print-value'
        data['serviceInstance']['builder'] = 'do-not-print-value'
        result = ci.read_only_diagnostics(data, POLICY)
        self.assertEqual(result['instance_fields']['startCommand'], 'different')
        self.assertEqual(result['instance_builder'], 'other')
        self.assertNotIn('do-not-print-value', json.dumps(result))

    def expect_failure(self, provider, code):
        with self.assertRaisesRegex(ci.CIError, '^' + code + '$'):
            provider.runner().run()

    def test_success_preserves_exact_commit_volume_and_orders_mutations(self):
        api = Provider()
        result = api.runner().run()
        self.assertEqual(result['status'], 'PASS')
        self.assertEqual(result['volume_id'], POLICY['volume_id'])
        mutations = api.mutations()
        self.assertEqual([q for q, _ in mutations], [ci.UPSERT, ci.DEPLOY, ci.UPSERT, ci.REDEPLOY])
        self.assertEqual(mutations[0][1]['input']['variables'], {
            'GENIUS_TRIAL_PHASE': 'seed', 'GENIUS_TRIAL_EXPECTED_COMMIT': SHA, 'GENIUS_TRIAL_RUN_ID': RUN})
        self.assertTrue(mutations[0][1]['input']['skipDeploys'])
        self.assertFalse(mutations[0][1]['input']['replace'])
        self.assertEqual(mutations[1][1]['commitSha'], SHA)
        self.assertEqual(mutations[2][1]['input']['variables'], {'GENIUS_TRIAL_PHASE': 'verify'})
        self.assertEqual(mutations[3][1], {'id': SEED_ID})
        self.assertIn('usePreviousImageTag:true', ci.REDEPLOY)

    def test_foreign_staged_patch_prevents_all_mutations(self):
        api = Provider()
        api.data['environmentStagedChanges']['patch'] = {'services': {'other': {'deploy': {'startCommand': 'x'}}}}
        self.expect_failure(api, 'FOREIGN_STAGED_CHANGES')
        self.assertEqual(api.mutations(), [])

    def test_unknown_empty_patch_shape_is_not_accepted(self):
        api = Provider()
        api.data['environmentStagedChanges'] = None
        self.expect_failure(api, 'STAGED_READBACK_SHAPE_UNVERIFIED')
        self.assertEqual(api.mutations(), [])

    def test_stopped_flag_does_not_override_active_or_unknown_instance(self):
        for status in ('RUNNING', 'CREATED', 'UNKNOWN', None):
            with self.subTest(status=status):
                api = Provider()
                api.data['serviceInstance']['latestDeployment'].update(
                    deploymentStopped=True, instances=[{'status': status}])
                self.expect_failure(api, 'RUNTIME_NOT_QUIET')
                self.assertEqual(api.mutations(), [])

    def test_retained_success_with_exited_instance_is_quiet(self):
        self.assertTrue(ci.quiet(deployment(SEED_ID)))
        self.assertFalse(ci.quiet({'status': 'SUCCESS', 'instances': []}))

    def test_base_limits_endpoint_and_token_scope_fail_before_mutation(self):
        def changed_limits(d):
            d['environment']['config']['services'][POLICY['service_id']]['deploy']['limitOverride']['containers']['memoryBytes'] = 1073741824
        cases = [
            (lambda d: d['projectToken'].update(environmentId='other'), 'TOKEN_SCOPE_MISMATCH'),
            (lambda d: d['tcpProxies'].append({'id': 'public'}), 'PUBLIC_ENDPOINT_PRESENT'),
            (lambda d: d['variables'].update(GENIUS_RAILWAY_STAGING_TOKEN='unexpected'), 'UNEXPECTED_RUNTIME_VARIABLE'),
            (changed_limits, 'RESOURCE_LIMIT_DRIFT')]
        for change, code in cases:
            with self.subTest(code=code):
                api = Provider(); change(api.data); self.expect_failure(api, code)
                self.assertEqual(api.mutations(), [])

    def test_variable_readback_mismatch_never_deploys(self):
        api = Provider()
        def hook(q, _):
            if q == ci.READ and api.mutations():
                api.data['variables']['GENIUS_TRIAL_EXPECTED_COMMIT'] = '0' * 40
        api.hook = hook
        self.expect_failure(api, 'VARIABLE_READBACK_MISMATCH')
        self.assertEqual([q for q, _ in api.mutations()], [ci.UPSERT])

    def test_seed_fail_and_wrong_metadata_never_activate_verify(self):
        for case in ('runner_fail', 'wrong_sha', 'missing_artifacts', 'false_pass'):
            with self.subTest(case=case):
                api = Provider()
                value = receipt('seed')
                if case == 'runner_fail':
                    value['status'] = 'FAIL'; code = 'RUNNER_REPORTED_FAILURE'
                elif case == 'wrong_sha':
                    api.seed['deployment']['meta']['commitHash'] = '0' * 40; code = 'DEPLOYMENT_SHA_MISMATCH'
                elif case == 'missing_artifacts':
                    value['artifact_sha256'] = {}; code = 'SEED_ARTIFACTS_MISSING'
                else:
                    value['received_expected_results_matched'] = False; code = 'SEED_CHECKS_MISSING'
                api.seed['deploymentLogs'] = [{'message': json.dumps(value)}]
                self.expect_failure(api, code)
                self.assertEqual([q for q, _ in api.mutations()], [ci.UPSERT, ci.DEPLOY])

    def test_receipt_deployment_must_match_provider_deployment(self):
        api = Provider(); value = receipt('seed'); value['deployment_id'] = VERIFY_ID
        api.seed['deploymentLogs'] = [{'message': json.dumps(value)}]
        self.expect_failure(api, 'RECEIPT_IDENTITY_MISMATCH')
        self.assertEqual(len(api.mutations()), 2)

    def test_seed_timeout_is_bounded_and_never_activates_verify(self):
        api = Provider(); api.seed['deploymentLogs'] = []
        self.expect_failure(api, 'PHASE_TIMEOUT_NO_ACCEPTANCE')
        self.assertEqual(api.clock.now, 300)
        self.assertEqual(len(api.mutations()), 2)
        self.assertEqual(sum(q == ci.POLL for q, _, _ in api.calls), 20)

    def test_verify_requires_new_deployment(self):
        api = Provider(); api.redeploy_id = SEED_ID
        self.expect_failure(api, 'VERIFY_DEPLOYMENT_NOT_NEW')

    def test_verify_image_digest_must_be_observable_and_equal(self):
        api = Provider(); api.verify['deployment']['meta']['imageDigest'] = 'sha256:' + 'c' * 64
        self.expect_failure(api, 'VERIFY_IMAGE_MISMATCH')
        api = Provider(); del api.verify['deployment']['meta']['imageDigest']
        self.expect_failure(api, 'PHASE_TIMEOUT_NO_ACCEPTANCE')

    def test_deployment_metadata_identity_works_without_redeploy_build_log(self):
        api = Provider()
        api.seed['buildLogs'] = [{'message': 'containerimage.digest: sha256:' + '7' * 64}]
        api.verify['buildLogs'] = []
        result = api.runner().run()
        self.assertEqual(result['image_sha256'], IMAGE)
        self.assertEqual(result['image_identity_source'], 'Railway deployment.meta.imageDigest')
        self.assertEqual(result['verify_provider_acceptance']['image_sha256'], IMAGE)

    def test_missing_seed_metadata_cannot_fall_back_to_build_or_source(self):
        api = Provider(); api.seed['deployment']['meta']['imageDigest'] = None
        self.expect_failure(api, 'PHASE_TIMEOUT_NO_ACCEPTANCE')
        self.assertEqual(len(api.mutations()), 2)

    def test_image_metadata_rejects_tags_malformed_hashes_and_arbitrary_values(self):
        for value in ['latest', IMAGE, 'sha256:' + 'b' * 63, 'sha256:' + IMAGE + '\n', {}, 'never-emit-me']:
            with self.subTest(value=type(value).__name__):
                api = Provider(); api.seed['deployment']['meta']['imageDigest'] = value
                self.expect_failure(api, 'INVALID_DEPLOYMENT_IMAGE_DIGEST')

    def test_image_identity_cannot_change_while_polling(self):
        api = Provider(); calls = 0
        def hook(query, variables):
            nonlocal calls
            if query == ci.POLL and variables['id'] == SEED_ID:
                calls += 1
                if calls == 1:
                    api.seed['deploymentLogs'] = []
                else:
                    api.seed['deployment']['meta']['imageDigest'] = 'sha256:' + '5' * 64
        api.hook = hook
        self.expect_failure(api, 'DEPLOYMENT_IMAGE_CHANGED')

    def test_verify_source_and_prior_invocation_must_match(self):
        api = Provider(); api.verify['deployment']['meta']['commitHash'] = '1' * 40
        self.expect_failure(api, 'DEPLOYMENT_SHA_MISMATCH')
        api = Provider(); value = receipt('verify'); value['prior_invocation'] = '0' * 32
        api.verify['deploymentLogs'] = [{'message': json.dumps(value)}]
        self.expect_failure(api, 'VERIFY_SEED_LINK_MISMATCH')

    def test_volume_drift_after_seed_prevents_verify(self):
        api = Provider()
        def hook(q, _):
            if q == ci.READ and any(query == ci.POLL for query, _, _ in api.calls):
                api.data['environment']['volumeInstances']['edges'][0]['node']['id'] = 'replacement'
        api.hook = hook
        self.expect_failure(api, 'CONTRACT_CHANGED_AFTER_SEED')
        self.assertEqual(len(api.mutations()), 2)

    def test_context_rejects_manual_other_branch_and_wrong_checkout(self):
        env = {'GITHUB_EVENT_NAME': 'push', 'GITHUB_REF': 'refs/heads/deploy/staging',
               'GITHUB_REPOSITORY': ci.REPOSITORY, 'GITHUB_SHA': SHA, 'GITHUB_RUN_ID': '123', 'GITHUB_RUN_ATTEMPT': '1'}
        self.assertEqual(ci.validate_context(env, SHA), (SHA, RUN))
        for change, head in [({'GITHUB_EVENT_NAME': 'workflow_dispatch'}, SHA),
                             ({'GITHUB_REF': 'refs/heads/main'}, SHA), ({}, '0' * 40)]:
            with self.assertRaises(ci.CIError):
                ci.validate_context(dict(env, **change), head)

    def test_check_only_does_no_mutations_and_needs_no_activation_or_git(self):
        api = Provider()
        with tempfile.TemporaryDirectory() as tmp, patch.object(ci, 'GraphQL', return_value=api), \
             patch.dict(ci.os.environ, {'GENIUS_RAILWAY_STAGING_TOKEN': 'fake'}, clear=True), \
             patch('sys.argv', ['ci', '--check-only', '--output', tmp + '/receipt.json']), \
             patch.object(ci.subprocess, 'check_output', side_effect=AssertionError('No git call')), \
             contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(ci.main(), 0)
            self.assertEqual(json.loads(Path(tmp, 'receipt.json').read_text())['mutations'], 0)
        self.assertEqual(api.mutations(), [])

    def test_check_only_scope_mismatch_stops_before_reading_runtime(self):
        api = Provider()
        api.data['projectToken']['environmentId'] = 'another-environment'
        stdout = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp, patch.object(ci, 'GraphQL', return_value=api), \
             patch.dict(ci.os.environ, {'GENIUS_RAILWAY_STAGING_TOKEN': 'fake'}, clear=True), \
             patch('sys.argv', ['ci', '--check-only', '--output', tmp + '/receipt.json']), \
             contextlib.redirect_stdout(stdout):
            self.assertEqual(ci.main(), 1)
        result = json.loads(stdout.getvalue())
        self.assertEqual(result['code'], 'TOKEN_SCOPE_MISMATCH')
        self.assertEqual(result['mutations'], 0)
        self.assertEqual([q for q, _, _ in api.calls], [ci.SCOPE])
        self.assertNotIn('token_scope_verified', result)

    def test_failure_evidence_contains_stage_ids_but_no_provider_payload(self):
        api = Provider()
        def hook(q, _):
            if q == ci.REDEPLOY:
                raise ci.CIError('MUTATION_OUTCOME_UNKNOWN_NO_RETRY')
        api.hook = hook
        env = {'GENIUS_RAILWAY_STAGING_TOKEN': 'secret-never-print', 'GENIUS_STAGING_AUTOMATION_ENABLED': 'true',
               'GITHUB_EVENT_NAME': 'push', 'GITHUB_REF': 'refs/heads/deploy/staging',
               'GITHUB_REPOSITORY': ci.REPOSITORY, 'GITHUB_SHA': SHA, 'GITHUB_RUN_ID': '123', 'GITHUB_RUN_ATTEMPT': '1'}
        stdout = io.StringIO()
        runner = api.runner()
        with patch.object(ci, 'Orchestrator', return_value=runner), tempfile.TemporaryDirectory() as tmp, patch.object(ci, 'GraphQL', return_value=api), \
             patch.dict(ci.os.environ, env, clear=True), patch.object(ci.subprocess, 'check_output', return_value=SHA), \
             patch('sys.argv', ['ci', '--output', tmp + '/receipt.json']), contextlib.redirect_stdout(stdout):
            self.assertEqual(ci.main(), 1)
        result = json.loads(stdout.getvalue())
        self.assertEqual(result['stage'], 'verify_redeploy')
        self.assertEqual(result['seed_deployment_id'], SEED_ID)
        self.assertEqual(result['source_commit'], SHA)
        self.assertNotIn('secret-never-print', stdout.getvalue())
        self.assertEqual(sum(q == ci.REDEPLOY for q, _ in api.mutations()), 1)


class TransportTests(unittest.TestCase):
    def test_http_status_and_query_field_diagnostics_do_not_echo_secrets(self):
        for status in (400, 401, 403):
            with self.subTest(status=status):
                class Opener:
                    calls = 0
                    def open(self, *_args, **_kwargs):
                        self.calls += 1
                        body = json.dumps({'errors': [
                            {'message': 'Cannot query field "projectToken" on type "Query". secret-never-print'},
                            {'message': 'Cannot query field "secretNeverPrint" on type "Query".'},
                            {'message': 'secret-never-print'}]}).encode()
                        raise urllib.error.HTTPError(ci.API, status, 'secret-never-print', {}, io.BytesIO(body))
                opener = Opener()
                with self.assertRaises(ci.CIError) as caught:
                    ci.GraphQL('secret-never-print', opener=opener).call(ci.SCOPE, {})
                self.assertEqual(str(caught.exception), 'API_HTTP_REJECTED')
                self.assertEqual(caught.exception.diagnostics['http_status'], status)
                self.assertNotIn('secret', json.dumps(caught.exception.diagnostics))
                self.assertEqual(opener.calls, 1)
                if status == 400:
                    self.assertEqual(caught.exception.diagnostics['unknown_query_fields'], ['projectToken'])

    def test_ambiguous_mutation_is_attempted_once(self):
        class Opener:
            calls = 0
            def open(self, *_args, **_kwargs):
                self.calls += 1
                raise TimeoutError('provider payload may contain secrets')
        opener = Opener(); clock = Clock()
        api = ci.GraphQL('fake-secret', opener=opener, clock=clock, sleep=clock.sleep)
        with self.assertRaisesRegex(ci.CIError, '^MUTATION_OUTCOME_UNKNOWN_NO_RETRY$'):
            api.call(ci.DEPLOY, {}, mutation=True)
        self.assertEqual(opener.calls, 1)
        self.assertEqual(clock.now, 0)

    def test_reads_retry_only_three_times_with_backoff(self):
        class Opener:
            calls = 0
            def open(self, *_args, **_kwargs):
                self.calls += 1
                raise urllib.error.URLError('temporary synthetic outage')
        opener = Opener(); clock = Clock()
        api = ci.GraphQL('fake-secret', opener=opener, clock=clock, sleep=clock.sleep)
        with self.assertRaisesRegex(ci.CIError, '^API_READ_RETRIES_EXHAUSTED$'):
            api.call(ci.READ, {})
        self.assertEqual(opener.calls, 3)
        self.assertEqual(clock.now, 6)

    def test_graphql_200_errors_do_not_echo_provider_payload(self):
        class Opener:
            def open(self, request, **_kwargs):
                self.request = request
                return contextlib.closing(io.BytesIO(b'{"errors":[{"message":"secret-value"}]}'))
        opener = Opener(); api = ci.GraphQL('fake-secret', opener=opener)
        with self.assertRaisesRegex(ci.CIError, '^API_GRAPHQL_ERROR$'):
            api.call(ci.READ, {})
        self.assertEqual(opener.request.get_header('Project-access-token'), 'fake-secret')
        self.assertEqual(opener.request.get_header('User-agent'), ci.USER_AGENT)
        self.assertEqual(opener.request.get_header('Accept'), 'application/json')
        self.assertIsNone(opener.request.get_header('Authorization'))


if __name__ == '__main__':
    unittest.main(verbosity=2)
