"""Focused author tests of exact arithmetic, FDQ binding and real subprocess limits."""
import copy
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from genius_local import operations as op

ROOT = Path(__file__).resolve().parents[2]
R1 = Path(os.environ.get("GENIUS_R1_BASELINE", ROOT / "baseline/R1"))
R0 = Path(os.environ.get("GENIUS_R0_BASELINE", ROOT / "baseline/received_baseline/R0"))


def known(value):
    return {"state": "PV_KNOWN", "value": value, "unit": "h_contractual", "basis": ["stipulated-contract"]}


def unknown():
    return {"state": "PV_UNKNOWN", "reasons": ["NOT_RECEIVED"], "obligation_refs": ["missing"]}


class ExactHoursTests(unittest.TestCase):
    def test_exact_and_oriented(self):
        result = op.derive_hours({"assignments": [{"id": "a", "credit_hours": known("13/2")}, {"id": "b", "credit_hours": known("15/2")}], "target_hours": known("15/1")})
        self.assertEqual({k: v['value'] for k, v in result.items()}, {"assigned": "14/1", "excess": "0/1", "deficit": "1/1", "oriented_overtime": "0/1", "oriented_undertime": "-1/1"})

    def test_more_than_float_precision(self):
        result = op.derive_hours({"assignments": [{"id": "a", "credit_hours": known("9007199254740993/1")}, {"id": "b", "credit_hours": known("1/3")}], "target_hours": known("0/1")})
        self.assertEqual(result['assigned']['value'], '27021597764222980/3')

    def test_missing_credit_is_not_zero(self):
        result = op.derive_hours({"assignments": [{"id": "a", "credit_hours": unknown()}], "target_hours": known("0/1")})
        self.assertTrue(all(v['state'] == 'PV_UNKNOWN' and 'value' not in v for v in result.values()))

    def test_target_unknown_preserves_assigned(self):
        result = op.derive_hours({"assignments": [{"id": "a", "credit_hours": known("13/2")}], "target_hours": unknown()})
        self.assertEqual(result['assigned']['value'], '13/2')
        self.assertEqual(result['deficit']['state'], 'PV_UNKNOWN')

    def test_duplicate_assignments_and_noncanonical_rejected(self):
        with self.assertRaises(op.OperationRejected):
            op.derive_hours({"assignments": [{"id": "a", "credit_hours": known("1/1")}] * 2, "target_hours": known("0/1")})
        for bad in ('2/2', '0/0', '1.0', '-0/1', '01/1'):
            with self.subTest(bad=bad), self.assertRaises(op.OperationRejected):
                op.exact_rational(bad)


@unittest.skipUnless((R1 / 'research/verify_fdq.py').is_file() and (R0 / 'sources/repo/kernel/genius_kernel/engine.py').is_file(), 'received dependency paths required')
class FDQOperationTests(unittest.TestCase):
    def fixture(self, kind='selector'):
        folder = R1 / 'research/results/priority_two_maxima'
        raw = (folder / 'input.json').read_bytes()
        original = (folder / 'original_result.json').read_bytes()
        cert = json.loads((folder / 'certificate.json').read_bytes())
        cert['query'] = {'frontier': kind == 'frontier', 'selector': kind == 'selector'}
        cert['claim'] = {kind: cert['claim'][kind]}
        return raw, original, cert

    def context(self, kind='selector'):
        raw, original, cert = self.fixture(kind)
        data = {'input': raw, 'result': original, 'certificate': op.canonical(cert)}
        artifacts = {ref: {'metadata': {'sha256': op.digest(value)}, 'bytes': value} for ref, value in data.items()}
        query = {'id': 'Q', 'revision': 1, 'kind': kind,
                 'target_spec': op.fdq_target_spec(raw, kind),
                 'scope': op.fdq_scope(raw, original, cert), 'norm': json.loads(raw)['selection'],
                 'artifact_refs': list(data), 'obligation_refs': ['O']}
        operation = {'id': 'C', 'query_ref': 'Q', 'kind': 'CERTIFY_FDQ', 'obligation_refs': ['O'],
                     'parameters': {'input_ref': 'input', 'result_ref': 'result', 'certificate_ref': 'certificate'}}
        context = {'request': {'obligations': [{'id': 'O', 'query_ref': 'Q', 'primary_cause': 'COMPUTO_PENDIENTE', 'affected_claims': ['Q'], 'closure': {'predicate': 'EXACT_QUERY_RESULT_RECEIVED'}}]},
                   'query': query, 'artifacts': artifacts, 'blob_reader': data.__getitem__,
                   'baseline_r1': R1, 'baseline_r0': R0, 'budget': {'certificate_timeout_seconds': 60}, 'cancel_check': lambda: False}
        return operation, context, data

    def test_received_verifier_runs_and_keeps_original(self):
        operation, context, data = self.context()
        originals = copy.deepcopy(data)
        result = op.execute_operation(operation, context)
        self.assertEqual(result['status'], 'CONDITIONAL', result['reason'])
        self.assertEqual(result['value']['value'], {'selector': {'state': 'DEFINED', 'value': 'p'}})
        self.assertEqual(data, originals)
        verification = result['evidence'][0]['fdq_receipt']['verification']
        self.assertEqual(verification['original_answer']['selector']['state'], 'OUTSIDE_DOMAIN')
        self.assertEqual(verification['checked_members'], 2)

    def test_query_norm_digest_mismatch_rejected(self):
        operation, context, data = self.context()
        context['query']['norm']['order'] = ['s', 'p', 'q']
        result = op.execute_operation(operation, context)
        self.assertEqual(result['status'], 'REJECTED')
        self.assertEqual(result['reason'], 'FDQ_NORM_BINDING')
        self.assertFalse(result['obligation_effects'])

    def test_arbitrary_predicate_cannot_close(self):
        operation, context, data = self.context()
        context['request']['obligations'][0]['closure']['predicate'] = 'PLANTS_WILL_SURVIVE'
        result = op.execute_operation(operation, context)
        self.assertEqual(result['status'], 'CONDITIONAL')
        self.assertEqual(result['obligation_effects'], [])

    def test_other_affected_claim_cannot_close(self):
        operation, context, data = self.context()
        context['request']['obligations'][0]['affected_claims'] = ['actual-field-decision']
        result = op.execute_operation(operation, context)
        self.assertEqual(result['status'], 'CONDITIONAL')
        self.assertEqual(result['obligation_effects'], [])

    def test_empirical_target_label_rejected(self):
        operation, context, data = self.context()
        context['query']['target_spec']['population'] = 'REAL_PLANTS'
        result = op.execute_operation(operation, context)
        self.assertEqual(result['status'], 'REJECTED')
        self.assertEqual(result['reason'], 'FDQ_TARGET_SPEC_BINDING')
        self.assertEqual(result['obligation_effects'], [])

    def test_empty_family_is_not_infeasibility(self):
        raw, original, cert = self.fixture()
        cert['domain']['choices'] = []
        result = op.run_fdq(raw, original, op.canonical(cert), R1, R0)
        self.assertEqual(result['verification']['state'], 'NOT_ACCEPTED')
        self.assertEqual(result['verification']['reason'], 'NONEMPTY_BOUNDED_FAMILY')

    def test_false_claim_recomputed(self):
        raw, original, cert = self.fixture()
        cert['claim']['selector']['value'] = 'q'
        result = op.run_fdq(raw, original, op.canonical(cert), R1, R0)
        self.assertEqual(result['verification']['state'], 'NOT_ACCEPTED')
        self.assertEqual(result['verification']['reason'], 'FALSE_CERTIFICATE_CLAIM')

    def test_invalid_reference_is_rejected(self):
        raw, original, cert = self.fixture()
        cert['domain']['hole']['index'] = 'ghost'
        result = op.run_fdq(raw, original, op.canonical(cert), R1, R0)
        self.assertEqual(result['verification']['state'], 'NOT_ACCEPTED')
        self.assertEqual(result['verification']['reason'], 'INVALID_HOLE_INDEX_REFERENCE')

    def test_actual_timeout_has_no_verification(self):
        raw, original, cert = self.fixture()
        result = op.run_fdq(raw, original, op.canonical(cert), R1, R0, timeout_seconds=0.00001)
        self.assertEqual(result['reason'], 'FDQ_PROCESS_TIMEOUT')
        self.assertIsNone(result['verification'])
        self.assertTrue(result['process']['timeout'])

    def test_actual_forced_cancel_is_not_kernel_cancelled(self):
        raw, original, cert = self.fixture()
        result = op.run_fdq(raw, original, op.canonical(cert), R1, R0, cancel_check=lambda: True)
        self.assertEqual(result['reason'], 'FDQ_PROCESS_CANCELLED')
        self.assertIsNone(result['verification'])

    def test_actual_output_bound_has_no_claim(self):
        raw, original, cert = self.fixture()
        with patch.object(op, 'MAX_WORKER_OUTPUT', 64):
            result = op.run_fdq(raw, original, op.canonical(cert), R1, R0)
        self.assertEqual(result['reason'], 'FDQ_OUTPUT_BUDGET')
        self.assertIsNone(result['verification'])
        self.assertTrue(result['process']['truncated'])
        self.assertEqual(result['process']['digest_scope'], 'CAPTURED_PREFIX')

    def test_dependency_mutation_is_adapter_error(self):
        raw, original, cert = self.fixture()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'research').mkdir()
            for name in ('verify_fdq.py', 'fdq_oracle.py'):
                shutil.copyfile(R1 / 'research' / name, root / 'research' / name)
            (root / 'research/fdq_oracle.py').write_text('# changed dependency\n')
            result = op.run_fdq(raw, original, op.canonical(cert), root, R0)
        self.assertEqual(result['reason'], 'WORKER_ERROR')
        self.assertIsNone(result['verification'])
        self.assertEqual(result['worker_error']['reason'], 'DEPENDENCY_DIGEST_MISMATCH:fdq_oracle.py')


if __name__ == '__main__':
    unittest.main()
