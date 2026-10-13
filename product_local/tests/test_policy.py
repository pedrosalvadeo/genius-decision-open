import copy
import hashlib
import json
import unittest

from genius_local.policy import (PolicyError, loads_strict, exact_q, validate_cell,
                                 pointer_get, canonical_bytes)


class StrictWireTests(unittest.TestCase):
    def test_duplicate_keys_at_depth_fail(self):
        with self.assertRaises(PolicyError):
            loads_strict(b'{"obligation":{"state":"OPEN","state":"CLOSED_SCOPED"}}')

    def test_floats_and_nonfinite_fail(self):
        for raw in (b'{"value":0.1}', b'{"value":NaN}', b'{"value":Infinity}', b'{"value":1e10}'):
            with self.subTest(raw=raw), self.assertRaises(PolicyError):
                loads_strict(raw)

    def test_exact_rational_has_no_float_round_trip(self):
        self.assertEqual(str(exact_q('9007199254740993/7')), '9007199254740993/7')
        for value in ('0/2', '-0/1', '2/4', '1/0', '1/-2', '01/1', '0.5', 0, True):
            with self.subTest(value=value), self.assertRaises(PolicyError):
                exact_q(value)

    def test_unknown_is_not_zero_false_empty_or_null(self):
        good = {'state': 'PV_UNKNOWN', 'reasons': ['NO_OBSERVATION'], 'obligation_refs': ['o1']}
        validate_cell(good)
        for value in (0, '0/1', False, [], None, ''):
            bad = dict(good, value=value)
            with self.subTest(value=value), self.assertRaises(PolicyError):
                validate_cell(bad)
        for value in (False, [], '0/1'):
            validate_cell({'state': 'PV_KNOWN', 'value': value, 'unit': 'nominal', 'basis': ['fixture']})
        with self.assertRaises(PolicyError):
            validate_cell({'state': 'PV_KNOWN', 'value': None, 'unit': 'nominal', 'basis': ['fixture']})

    def test_pointer_identity_and_array_index_are_exact(self):
        data = {'a/b': {'~': [False, '0/1']}}
        self.assertEqual(pointer_get(data, '/a~1b/~0/1'), '0/1')
        for pointer in ('/a~2b', '/a~1b/~0/01', '/a~1b/~0/-1', '/missing'):
            with self.subTest(pointer=pointer), self.assertRaises(PolicyError):
                pointer_get(data, pointer)


if __name__ == '__main__':
    unittest.main()


class ProductPolicyTests(unittest.TestCase):
    """Contract examples; the receipt objects below are explicit test stubs."""
    def setUp(self):
        import tempfile
        from test_acceptance import make_hours
        self.tmp = tempfile.TemporaryDirectory(prefix='genius-policy-')
        self.addCleanup(self.tmp.cleanup)
        self.fixture = make_hours(self.tmp.name)

    def artifacts(self):
        return {item['id']: {'metadata': item, 'bytes': (self.fixture.directory / item['path']).read_bytes()}
                for item in self.fixture.request['artifacts']}

    def validate(self):
        from genius_local.policy import validate_request
        return validate_request(self.fixture.request, lambda ref: self.artifacts()[ref]['bytes'])

    def assessment(self):
        return self.fixture.request['operations'][0]['parameters']['assessment']

    def test_request_accepts_received_finite_fixture(self):
        self.assertIs(self.validate(), self.fixture.request)

    def test_unlinked_queries_cycles_and_caller_closures_fail(self):
        request = self.fixture.request
        original = copy.deepcopy(request)
        request['obligations'][0]['status'] = 'CLOSED_SCOPED'
        with self.assertRaisesRegex(PolicyError, 'CALLER_CLOSURE_FORBIDDEN'):
            self.validate()
        request.clear(); request.update(copy.deepcopy(original))
        request['obligations'][0]['dependencies'] = [{'ref': 'O', 'revision': 1, 'role': 'input'}]
        with self.assertRaisesRegex(PolicyError, 'CYCLIC_OBLIGATIONS'):
            self.validate()
        request.clear(); request.update(copy.deepcopy(original))
        request['queries'][0]['obligation_refs'] = []
        with self.assertRaises(PolicyError):
            self.validate()
        request.clear(); request.update(copy.deepcopy(original))
        request['operations'][0]['parameters']['assessment']['query_ref'] = 'other'
        with self.assertRaisesRegex(PolicyError, 'ASSESSMENT_QUERY_BINDING'):
            self.validate()

    def test_stipulated_compatibility_does_not_become_empirical_support(self):
        from genius_local.policy import assess_source
        main = self.fixture.request['artifacts'][0]
        main['evidence_kind'] = 'PRIMARY_DOCUMENT'
        self.assessment()['evidence_kind'] = 'PRIMARY_DOCUMENT'
        result = assess_source(self.assessment(), self.artifacts())
        self.assertEqual(result['verdict'], 'SC_CONDITIONAL_MODEL_ONLY')
        self.assertEqual(result['conditional_premise_refs'], ['metadata'])
        self.assertIn('SOURCE_TRUTH', result['documentary_limit'])

    def test_permission_on_supporting_premise_cannot_be_bypassed(self):
        from genius_local.policy import assess_source
        meta = next(a for a in self.fixture.request['artifacts'] if a['id'] == 'metadata')
        meta['permissions']['use'] = 'UNKNOWN'
        result = assess_source(self.assessment(), self.artifacts())
        self.assertEqual(result['verdict'], 'SC_ACCESS_BLOCKED')
        self.assertEqual(result['blocked_premise_refs'], ['metadata'])

    def test_status_label_cannot_override_actual_identity_mismatch(self):
        from genius_local.policy import assess_source
        assessment = self.assessment()
        assessment['axes']['identity']['target_value'] = 'different-person'
        assessment['target_spec']['identity'] = 'different-person'
        result = assess_source(assessment, self.artifacts())
        self.assertEqual(result['axes']['identity']['status'], 'MISMATCH')
        self.assertEqual(result['verdict'], 'SC_INCOMPATIBLE')

    def test_claimed_basis_must_equal_received_descriptor(self):
        from genius_local.policy import assess_source
        self.assessment()['axes']['identity']['source_value'] = 'fabricated-same-person'
        with self.assertRaisesRegex(PolicyError, 'SOURCE_AXIS_BASIS_MISMATCH'):
            assess_source(self.assessment(), self.artifacts())

    def test_exact_unit_scale_has_fixed_math_and_citable_statement(self):
        from genius_local.policy import assess_source
        src = {'construct': 'duration', 'unit': 'min'}
        dst = {'construct': 'duration', 'unit': 'h'}
        bridge = {'id': 'B1', 'rule_id': 'EXACT_UNIT_SCALE/1', 'source_unit': 'min',
                  'target_unit': 'h', 'factor': '1/60', 'construct': 'duration'}
        raw = canonical_bytes({'unit': src, 'bridge': bridge})
        self.fixture.artifact('bridge_source', raw)
        a = self.assessment()
        a['target_spec']['unit'] = dst
        a['axes']['unit'] = {'status': 'BRIDGED', 'source_value': src, 'target_value': dst,
                             'basis': {'artifact_ref': 'bridge_source', 'pointer': '/unit'},
                             'affected_claims': ['Q'], 'bridge_ref': 'B1'}
        a['transformation_chain'] = [{**bridge, 'basis': {'artifact_ref': 'bridge_source', 'pointer': '/bridge'}}]
        result = assess_source(a, self.artifacts())
        self.assertEqual(result['verdict'], 'SC_CONDITIONAL_MODEL_ONLY')
        self.assertEqual(result['unit_transform']['factor'], '1/60')
        a['transformation_chain'][0]['factor'] = '1/1'
        with self.assertRaisesRegex(PolicyError, 'INVALID_FIXED_UNIT_FACTOR'):
            assess_source(a, self.artifacts())

    def test_math_integers_must_be_exact_strings_recursively(self):
        for value in (9007199254740993, {'nested': 9007199254740993}, ['1/1', 0]):
            with self.subTest(value=value), self.assertRaises(PolicyError):
                validate_cell({'state': 'PV_KNOWN', 'value': value, 'unit': 'nominal', 'basis': ['fixture']})
        validate_cell({'state': 'PV_KNOWN', 'value': '9007199254740993', 'unit': 'count', 'basis': ['fixture']})
        validate_cell({'state': 'PV_KNOWN', 'value': False, 'unit': 'truth', 'basis': ['fixture']})

    def stub_outcome(self):
        from genius_local.policy import query_digest
        q = self.fixture.request['queries'][0]
        return {'operation_id': 'OP1', 'query_ref': 'Q', 'query_sha256': query_digest(q),
                'kind': 'DERIVE_HOURS', 'status': 'CONDITIONAL', 'reason': 'SYNTHETIC_TEST_RECEIPT',
                'claim_source': 'CONTRACT_HOURS/1',
                'value': {'state': 'PV_KNOWN', 'value': '14/1', 'unit': 'h_contractual', 'basis': ['fixture']},
                'evidence': [{'state': 'EV_CONDITIONAL', 'premises': ['Synthetic test stub']}],
                'obligation_effects': [{'obligation_ref': 'O', 'status': 'CLOSED_SCOPED', 'reason': 'Test receipt', 'witness_refs': ['OP1']}],
                'artifact_refs': ['hours']}

    def context(self):
        return {'execution': {'state': 'PE_COMPLETE', 'reason': 'SYNTHETIC_TEST_RECEIPT'},
                'ledger': {'obligations': copy.deepcopy(self.fixture.request['obligations']), 'worklog': []},
                'artifacts': {'received': copy.deepcopy(self.fixture.request['artifacts']), 'expected': []},
                'request_ref': {'revision': 1, 'sha256': hashlib.sha256(canonical_bytes(self.fixture.request)).hexdigest()},
                'budget_used': {'operations': 1, 'certificates': 0}}

    def test_response_does_not_verify_arbitrary_caller_predicate(self):
        from genius_local.policy import build_response
        request = self.fixture.request
        request['obligations'][0]['closure']['predicate'] = 'Person consented to the intervention'
        response = build_response(request, [self.stub_outcome()], self.context())
        self.assertEqual(response['decisions'][0]['state'], 'PR_JUSTIFIED_RESULT')
        obligation = response['obligations_ref']['record']['obligations'][0]
        self.assertEqual(obligation['status'], 'OPEN')
        self.assertIs(obligation['closure']['verified'], False)

    def test_open_dependency_blocks_obligation_closure_but_preserves_answer(self):
        from genius_local.policy import build_response
        from test_acceptance import obligation
        request = self.fixture.request
        request['obligations'][0]['closure']['predicate'] = 'EXACT_QUERY_RESULT_RECEIVED'
        request['obligations'][0]['dependencies'] = [{'ref': 'MODEL', 'revision': 1, 'role': 'rule'}]
        request['obligations'].append(obligation('DEFINICION_MODELO', 'MODEL', 'Q'))
        request['queries'][0]['obligation_refs'].append('MODEL')
        response = build_response(request, [self.stub_outcome()], self.context())
        self.assertEqual(response['decisions'][0]['state'], 'PR_JUSTIFIED_RESULT')
        self.assertEqual(response['closure']['state'], 'PC_PARTIAL')
        self.assertTrue(all(o['status'] == 'OPEN' for o in response['obligations_ref']['record']['obligations']))

    def test_query_digest_change_invalidates_prior_outcome(self):
        from genius_local.policy import build_response
        outcome = self.stub_outcome()
        self.fixture.request['queries'][0]['norm'] = {'mode': 'priority', 'order': ['q', 'p']}
        with self.assertRaisesRegex(PolicyError, 'OUTCOME_QUERY_DIGEST_MISMATCH'):
            build_response(self.fixture.request, [outcome], self.context())


class ConflictClosureRegressionTests(unittest.TestCase):
    """R1-CONFLICT regressions with fixed, independent arithmetic expectations.

    Uses only fixture utilities; previous methods are not counted again.
    """

    setUp = ProductPolicyTests.setUp
    stub_outcome = ProductPolicyTests.stub_outcome
    context = ProductPolicyTests.context

    def two_receipts(self, second_value='16/1'):
        first = self.stub_outcome()
        self.fixture.request['operations'].append({
            **copy.deepcopy(self.fixture.request['operations'][0]), 'id': 'OP2'})
        second = copy.deepcopy(first)
        second['operation_id'] = 'OP2'
        second['value']['value'] = second_value
        second['value']['basis'] = ['different retained receipt']
        second['obligation_effects'][0]['witness_refs'] = ['OP2']
        return first, second

    def test_r1_rule_references_resolve_inside_the_recorded_dag_and_bytes(self):
        from genius_local.policy import validate_request
        from test_acceptance import obligation
        request = self.fixture.request
        request['obligations'].append(obligation('DEFINICION_MODELO', 'MODEL', 'Q'))
        request['queries'][0]['obligation_refs'].append('MODEL')
        primary = request['obligations'][0]
        primary['derivation_rule'] = {'kind': 'PENDING_RULE', 'reason': 'Rule pending', 'obligation_ref': 'MODEL'}
        reader = lambda ref: (self.fixture.directory / next(a['path'] for a in request['artifacts'] if a['id'] == ref)).read_bytes()
        with self.assertRaisesRegex(PolicyError, 'PENDING_RULE_REFERENCE_NOT_IN_DEPENDENCY_DAG'):
            validate_request(request, reader)
        primary['dependencies'] = [{'ref': 'MODEL', 'revision': 1, 'role': 'rule'}]
        validate_request(request, reader)
        primary['derivation_rule']['obligation_ref'] = 'O'
        primary['dependencies'] = [{'ref': 'O', 'revision': 1, 'role': 'rule'}]
        with self.assertRaisesRegex(PolicyError, 'CYCLIC_OBLIGATIONS'):
            validate_request(request, reader)
        primary['dependencies'] = []
        primary['derivation_rule'] = {'kind': 'RULE', 'id': 'CONTRACT_HOURS/1', 'version': '1',
                                     'procedure': 'Exact stipulated credits', 'domain': 'Formal documentary component',
                                     'basis': {'artifact_ref': 'metadata', 'pointer': '/method'}}
        validate_request(request, reader)
        primary['derivation_rule']['basis']['pointer'] = '/nonexistent-rule'
        with self.assertRaisesRegex(PolicyError, 'POINTER_NOT_FOUND'):
            validate_request(request, reader)

    def test_r1_conflicting_receipts_reopen_obligation_and_retain_both(self):
        from genius_local.policy import build_response
        first, second = self.two_receipts()
        earlier = self.context()
        earlier['execution']['state'] = 'PE_PARTIAL'
        before = build_response(self.fixture.request, [first], earlier)
        self.assertEqual(before['obligations_ref']['record']['obligations'][0]['status'], 'CLOSED_SCOPED')
        context = self.context()
        context['ledger'] = before['obligations_ref']['record']
        response = build_response(self.fixture.request, [first, second], context)
        obligation = response['obligations_ref']['record']['obligations'][0]
        self.assertEqual(obligation['status'], 'BLOCKED')
        self.assertFalse(obligation['closure']['verified'])
        self.assertEqual(obligation['closure']['witness_refs'], ['OP1', 'OP2'])
        self.assertEqual(response['decisions'][0]['state'], 'PR_PARTIAL')
        self.assertEqual(response['decisions'][0]['unresolved_obligations'], ['O'])
        self.assertEqual(response['closure']['closed_queries'], [])
        self.assertEqual(response['closure']['unresolved_obligations'], ['O'])
        self.assertEqual({answer['value']['value'] for answer in response['decisions'][0]['answers']}, {'14/1', '16/1'})

    def test_r1_agreeing_receipts_with_distinct_provenance_still_close(self):
        from genius_local.policy import build_response
        first, second = self.two_receipts('14/1')
        response = build_response(self.fixture.request, [first, second], self.context())
        self.assertEqual(response['decisions'][0]['state'], 'PR_JUSTIFIED_RESULT')
        self.assertEqual(response['closure']['state'], 'PC_ANSWERED_SCOPED')
        self.assertEqual(len(response['decisions'][0]['answers']), 2)

    def test_r1_conflict_in_known_partial_component_blocks_full_receipt(self):
        from genius_local.policy import build_response
        first, second = self.two_receipts()
        first['value'] = {'assigned': copy.deepcopy(first['value']), 'deficit': {
            'state': 'PV_KNOWN', 'value': '0/1', 'unit': 'h_contractual', 'basis': ['fixture']}}
        second['value'] = {'assigned': copy.deepcopy(second['value']), 'deficit': {
            'state': 'PV_UNKNOWN', 'reasons': ['Target absent'], 'obligation_refs': ['O']}}
        second['status'] = 'UNRESOLVED'
        second['obligation_effects'] = []
        response = build_response(self.fixture.request, [first, second], self.context())
        self.assertEqual(response['evidence'][0]['state'], 'EV_CONFLICTING')
        self.assertEqual(response['obligations_ref']['record']['obligations'][0]['status'], 'BLOCKED')
        self.assertEqual(response['closure']['unresolved_obligations'], ['O'])

    def test_r1_conflict_invalidates_descendant_even_with_own_receipt(self):
        from genius_local.policy import build_response, query_digest
        from test_acceptance import obligation
        first, second = self.two_receipts()
        request = self.fixture.request
        child_query = copy.deepcopy(request['queries'][0])
        child_query.update(id='Q_child', obligation_refs=['CHILD'])
        request['queries'].append(child_query)
        child = obligation('DERIVABLE', 'CHILD', 'Q_child')
        child['dependencies'] = [{'ref': 'O', 'revision': 1, 'role': 'input'}]
        request['obligations'].append(child)
        child_op = copy.deepcopy(request['operations'][0])
        child_op.update(id='OP_child', query_ref='Q_child', obligation_refs=['CHILD'])
        request['operations'].append(child_op)
        child_receipt = copy.deepcopy(first)
        child_receipt.update(operation_id='OP_child', query_ref='Q_child', query_sha256=query_digest(child_query))
        child_receipt['obligation_effects'] = [{'obligation_ref': 'CHILD', 'status': 'CLOSED_SCOPED',
                                               'reason': 'Scoped receipt', 'witness_refs': ['OP_child']}]
        response = build_response(request, [first, child_receipt, second], self.context())
        rows = {o['id']: o for o in response['obligations_ref']['record']['obligations']}
        self.assertEqual({rows[key]['status'] for key in rows}, {'BLOCKED'})
        self.assertFalse(rows['CHILD']['closure']['verified'])
        self.assertEqual(rows['CHILD']['closure']['reason'], 'UPSTREAM_QUERY_CONFLICT')
        self.assertEqual(rows['CHILD']['closure']['conflict_query_refs'], ['Q'])
        by_query = {d['query_ref']: d for d in response['decisions']}
        self.assertEqual(by_query['Q_child']['state'], 'PR_PARTIAL')
        self.assertEqual(by_query['Q_child']['answers'][0]['value']['value'], '14/1')
        self.assertEqual(set(response['closure']['unresolved_obligations']), {'O', 'CHILD'})

    def test_r1_cli_checkpoint_reopens_conflict_and_does_not_skip_input_request(self):
        import os
        from pathlib import Path
        import subprocess
        import sys
        from test_acceptance import known, obligation
        from independent_client import audit_chain, audit_response
        fixture = self.fixture
        request = fixture.request
        query = request['queries'][0]
        source = fixture.artifact('hours_b', {
            'assignments': [{'id': 'b0', 'credit_hours': known('8/1')},
                            {'id': 'b1', 'credit_hours': known('8/1')}], 'target_hours': known('14/1')})
        query['artifact_refs'].append('hours_b')
        child_query = copy.deepcopy(query)
        child_query.update(id='Q_child', obligation_refs=['CHILD'])
        request['queries'].append(child_query)
        child = obligation('DERIVABLE', 'CHILD', 'Q_child')
        child['dependencies'] = [{'ref': 'O', 'revision': 1, 'role': 'input'}]
        request['obligations'].append(child)
        child_op = copy.deepcopy(request['operations'][0])
        child_op.update(id='OP_child', query_ref='Q_child', obligation_refs=['CHILD'])
        child_op['parameters']['assessment'].update(assessment_id='A_child', query_ref='Q_child', claim='Q_child')
        for axis in child_op['parameters']['assessment']['axes'].values():
            axis['affected_claims'] = ['Q_child']
        request['operations'].append(child_op)
        assessment = fixture.assessment(source, query)
        assessment['assessment_id'] = 'A2'
        request['operations'].append({'id': 'OP_conflict', 'query_ref': 'Q', 'kind': 'DERIVE_HOURS',
                                     'obligation_refs': ['O'], 'parameters': {
                                         'artifact_ref': 'hours_b', 'rule_id': 'CONTRACT_HOURS/1', 'assessment': assessment}})
        request['operations'].append({'id': 'OP_request', 'query_ref': 'Q', 'kind': 'REQUEST_INPUT',
                                     'obligation_refs': ['O'], 'parameters': {'obligation_ref': 'O',
                                         'prompt': 'Resolve the two conflicting compatible documentary credits, if known.',
                                         'unknown_allowed': True}})
        root = Path(__file__).resolve().parents[1]
        r1 = Path(os.environ.get('GENIUS_R1_BASELINE', root.parent / 'baseline/R1')).resolve()
        r0 = Path(os.environ.get('GENIUS_R0_BASELINE', root.parent / 'baseline/received_baseline/R0')).resolve()
        case = fixture.directory / 'case'
        result = subprocess.run([sys.executable, '-B', '-m', 'genius_local', 'run',
                                 '--request', str(fixture.save()), '--case', str(case),
                                 '--r1', str(r1), '--baseline', str(r0)], cwd=root,
                                capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr.decode())
        response = json.loads(result.stdout)
        audit_response(response, case)
        history = audit_chain(case)
        saw_earlier_closed = False
        saw_conflicted_checkpoint = False
        for snapshot in history['snapshots']:
            outcomes = {o['operation_id']: o for o in snapshot['outcomes']}
            ledger = {o['id']: o for o in snapshot['ledger']['obligations']}
            if 'OP_child' in outcomes and 'OP_conflict' not in outcomes:
                saw_earlier_closed |= all(o['status'] == 'CLOSED_SCOPED' for o in ledger.values())
            if 'OP_conflict' in outcomes:
                saw_conflicted_checkpoint = True
                self.assertTrue(all(o['status'] == 'BLOCKED' and not o['closure']['verified'] for o in ledger.values()))
        self.assertTrue(saw_earlier_closed)
        self.assertTrue(saw_conflicted_checkpoint)
        last = history['snapshots'][-1]
        request_outcome = next(o for o in last['outcomes'] if o['operation_id'] == 'OP_request')
        # DERIVABLE is not an admitted REQUEST_INPUT cause. The workflow must
        # reach that guard instead of silently omitting the request because of
        # the invalid CLOSED status that C1 retained after the conflict.
        self.assertEqual(request_outcome['reason'], 'INPUT_REQUEST_CAUSE')
        self.assertEqual(request_outcome['status'], 'REJECTED')
        self.assertEqual(set(response['closure']['unresolved_obligations']), {'O', 'CHILD'})
        self.assertEqual(response['closure']['closed_queries'], [])
