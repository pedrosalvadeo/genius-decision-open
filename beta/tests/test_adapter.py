"""Author tests: exact answers fixed separately from runtime computation."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from genius_beta.adapter import AdmissionError, ROOT, build_fdq, execute_profile


def hours():
    return {"profile": "hours", "assignments": [{"id": "a", "credit": "6.5"}, {"id": "b", "credit": "7.5"}],
            "target": "15", "permission_confirmed": True, "scope_acknowledged": True}


def fdq(kind="frontier", family="none"):
    source = ROOT / "product_local/examples/fdq" / family
    certificate = json.loads((source / "certificate.json").read_bytes())
    # Explicit test construction of an exclusive query; adapter must not edit it.
    certificate["query"] = {"frontier": kind == "frontier", "selector": kind == "selector"}
    certificate["claim"] = {kind: certificate["claim"][kind]}
    return {"profile": "fdq", "query_kind": kind, "input_json": (source / "input.json").read_text(),
            "result_json": (source / "original_result.json").read_text(), "certificate_json": json.dumps(certificate),
            "permission_confirmed": True, "scope_acknowledged": True}


class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.case = Path(self.temp.name) / "case"

    def run_case(self, payload):
        return execute_profile(payload, self.case)

    def test_exact_hours_real_controller_r3_and_conditional(self):
        outcome = self.run_case(hours())
        response = outcome["response"]
        values = response["decisions"][0]["answers"][0]["value"]
        self.assertEqual({key: values[key]["value"] for key in ("assigned", "excess", "deficit")},
                         {"assigned": "14/1", "excess": "0/1", "deficit": "1/1"})
        self.assertEqual(response["evidence"][0]["state"], "EV_CONDITIONAL")
        self.assertEqual(response["quality"]["utility"]["state"], "NOT_ASSESSED")
        self.assertEqual(outcome["presentation"]["authorization_to_act"], "NOT_ESTABLISHED")
        self.assertTrue((self.case / "store/HEAD").is_file())

    def test_unknown_credit_is_not_zero(self):
        payload = hours()
        payload["assignments"][0]["credit"] = None
        response = self.run_case(payload)["response"]
        value = response["decisions"][0]["observed_values"][0]["value"]
        self.assertTrue(all(cell["state"] == "PV_UNKNOWN" and "value" not in cell for cell in value.values()))
        self.assertTrue(response["closure"]["unresolved_obligations"])

    def test_unknown_target_preserves_known_subresult(self):
        payload = hours()
        payload["target"] = None
        response = self.run_case(payload)["response"]
        value = response["decisions"][0]["observed_values"][0]["value"]
        self.assertEqual(value["assigned"]["value"], "14/1")
        self.assertEqual(value["deficit"]["state"], "PV_UNKNOWN")

    def test_numeric_abuse_and_permissions_rejected(self):
        for number in (6.5, True, "1e20", "-1", "1/0", "9" * 65):
            payload = hours()
            payload["target"] = number
            with self.subTest(number=number), self.assertRaises(AdmissionError):
                # Separate owned path; rejected attempts never become successes.
                execute_profile(payload, Path(self.temp.name) / ("invalid-" + str(len(list(Path(self.temp.name).iterdir())))))
        payload = hours()
        payload["permission_confirmed"] = False
        with self.assertRaises(AdmissionError):
            self.run_case(payload)

    def test_fdq_runs_received_verifier_frontier_does_not_select(self):
        payload = fdq()
        before = deepcopy(payload)
        result = self.run_case(payload)
        self.assertEqual(payload, before)
        decision = result["response"]["decisions"][0]
        self.assertEqual(decision["state"], "PR_SET_OR_INCOMPARABLE")
        self.assertEqual(decision["answers"][0]["value"]["value"], {"frontier": ["p", "s"]})
        self.assertEqual((self.case / "input/input.json").read_bytes(), payload["input_json"].encode())
        self.assertEqual(result["response"]["evidence"][0]["state"], "EV_CONDITIONAL")

    def test_fdq_selector_disabled_is_not_winner(self):
        result = self.run_case(fdq("selector"))
        value = result["response"]["decisions"][0]["answers"][0]["value"]["value"]
        self.assertEqual(value, {"selector": {"state": "OUTSIDE_DOMAIN", "cause": "SELECTION_DISABLED"}})

    def test_fdq_false_claim_is_rejected_by_received_engine(self):
        payload = fdq()
        cert = json.loads(payload["certificate_json"])
        cert["claim"]["frontier"] = ["q"]
        payload["certificate_json"] = json.dumps(cert)
        response = self.run_case(payload)["response"]
        self.assertFalse(response["decisions"][0]["answers"])
        self.assertEqual(response["decisions"][0]["observed_values"][0]["status"], "REJECTED")

    def test_fdq_original_bytes_and_query_not_repaired(self):
        payload = fdq()
        payload["input_json"] += "\n"
        with self.assertRaisesRegex(AdmissionError, "DIGEST"):
            build_fdq(payload, self.case)
        payload = fdq()
        payload["query_kind"] = "selector"
        with self.assertRaisesRegex(AdmissionError, "QUERY"):
            build_fdq(payload, self.case)


if __name__ == "__main__":
    unittest.main()
