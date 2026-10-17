"""Published example snapshots must run against the actual received engine."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from genius_beta.adapter import AdmissionError, ROOT, execute_profile, fdq_verifier_available


class PublishedExamplesTests(unittest.TestCase):
    def test_examples_keep_provenance_and_received_results(self):
        directory = ROOT / "beta/examples"
        expected = json.loads((directory / "EXPECTED.json").read_bytes())["examples"]
        manifest = json.loads((directory / "PROVENANCE.json").read_bytes())
        with tempfile.TemporaryDirectory() as temporary:
            for row in manifest["examples"]:
                with self.subTest(example=row["example"]):
                    name = row["example"]
                    raw = (directory / (name + ".json")).read_bytes()
                    self.assertEqual(hashlib.sha256(raw).hexdigest(), row["payload_sha256"])
                    for source in row["source_files"]:
                        self.assertEqual(hashlib.sha256((ROOT / source["path"]).read_bytes()).hexdigest(), source["sha256"])
                    payload = json.loads(raw)
                    self.assertEqual(payload["evidence_origin"], "synthetic")
                    if payload["profile"] == "fdq" and not fdq_verifier_available():
                        with self.assertRaisesRegex(AdmissionError, "^FDQ_VERIFIER_NOT_IN_PUBLIC_EDITION$"):
                            execute_profile(payload, Path(temporary) / name)
                        continue
                    actual = execute_profile(payload, Path(temporary) / name)
                    self.assertEqual(actual["evidence_origin"], "synthetic")
                    response = actual["response"]
                    decision = response["decisions"][0]
                    target = expected[name]
                    self.assertEqual(response["quality"]["model_fidelity"]["state"], "NOT_ASSESSED")
                    self.assertEqual(response["quality"]["comprehension"]["state"], "NOT_ASSESSED")
                    if "decision" in target:
                        self.assertEqual(decision["state"], target["decision"])
                        self.assertEqual(response["evidence"][0]["state"], target["evidence"])
                    if "values" in target:
                        cells = decision["answers"][0]["value"]
                        self.assertEqual({key: cells[key]["value"] for key in target["values"]}, target["values"])
                    if "values_state" in target:
                        cells = decision["observed_values"][0]["value"]
                        self.assertTrue(all(cell["state"] == "PV_UNKNOWN" and "value" not in cell for cell in cells.values()))
                        self.assertTrue(response["closure"]["unresolved_obligations"])
                    if "value" in target:
                        self.assertEqual(decision["answers"][0]["value"]["value"], target["value"])


if __name__ == "__main__":
    unittest.main()
