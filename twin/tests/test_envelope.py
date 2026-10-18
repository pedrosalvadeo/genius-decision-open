"""Packed envelopes keep each native Result once and unpack to the identical envelope."""
import json
import unittest

from genius_twin import envelope, registry, stockflow
from genius_twin.process_runner import ProcessEvaluator


def size(value):
    return len(json.dumps(value, separators=(",", ":")))


class EnvelopePackingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = stockflow.default_model()
        cls.full = registry.evaluate(cls.model)

    def test_round_trip_is_identical_and_smaller(self):
        packed = envelope.pack(self.full)
        self.assertNotIn("native_result", packed)
        self.assertTrue(all("native_result" not in run for run in packed["native_runs"].values()))
        self.assertEqual(envelope.unpack(json.loads(json.dumps(packed))), self.full)
        self.assertLess(size(packed), size(self.full) / 2)

    def test_unpacked_and_unmatched_values_pass_through(self):
        self.assertIs(envelope.unpack(self.full), self.full)
        tampered = json.loads(json.dumps(self.full))
        tampered["native_runs"]["possible"]["native_result"]["input_digest"] = "0" * 64
        packed = envelope.pack(tampered)
        self.assertEqual(packed["_packed"]["runs"], ["robust"])
        self.assertEqual(envelope.unpack(packed), tampered)
        with self.assertRaises(ValueError):
            envelope.unpack({**packed, "_packed": {"format": "other"}})

    def test_child_process_returns_the_full_envelope(self):
        self.assertEqual(ProcessEvaluator(timeout=60)(self.model), self.full)


if __name__ == "__main__":
    unittest.main()
