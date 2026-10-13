"""Acceptance checks against the documented independent, hand-worked oracle."""
import copy
from fractions import Fraction
import hashlib
import json
import unittest

from genius_kernel import evaluate, verify_result
from genius_twin.domain import default_model, validate_model, compute_trajectories
from genius_twin.compiler import compile_model, evaluate_model


class DomainArithmetic(unittest.TestCase):
    def test_generated_resource_and_time_oracle(self):
        traces = compute_trajectories(default_model())
        expected = {
            "C": {"N": (14, 280, 0), "H": (16, 290, 0), "HA": (16, 290, 0)},
            "R": {"N": (14, 100, 90), "H": (16, 100, 90), "HA": (16, 100, 90)},
            "E": {"N": (16, 300, 200), "H": (18, 300, 200), "HA": (15, 300, 190)},
        }
        for p, scenarios in expected.items():
            for s, totals in scenarios.items():
                trace = traces[p][s]
                self.assertEqual(tuple(trace["totals"][k] for k in
                                 ("water_liters", "minutes_a", "minutes_b")), totals)
                self.assertEqual(len(trace["daily"]), 15)
                self.assertTrue(all(r["water_used_liters"] <= 18 and r["minutes_a"] <= 60
                                    and r["minutes_b"] <= 60 for r in trace["daily"]))

    def test_recovery_does_not_erase_historical_failure(self):
        for p, s in (("C", "H"), ("C", "HA"), ("E", "HA")):
            daily = compute_trajectories(default_model())[p][s]["daily"]
            self.assertEqual(daily[10]["water_in_tray_liters"], 0)
            self.assertEqual(daily[11]["water_in_tray_liters"], 2)
            self.assertTrue(all(r["violation_seen"] for r in daily[10:]))

    def test_past_is_shared_and_edit_changes_only_edited_policy(self):
        base_model = default_model()
        base = compute_trajectories(base_model)
        edited_model = copy.deepcopy(base_model)
        edited_model["policies"][-1] = "E_prime"
        edited = compute_trajectories(edited_model)
        self.assertEqual(base["C"], edited["C"])
        self.assertEqual(base["R"], edited["R"])
        for policy in base:
            self.assertEqual(base[policy]["N"]["daily"][:10], base[policy]["HA"]["daily"][:10])
        self.assertEqual(edited["E_prime"]["HA"]["totals"],
                         {"water_liters": 18, "minutes_a": 310, "minutes_b": 180})
        self.assertEqual(edited["E_prime"]["HA"]["daily"][10]["water_in_tray_liters"], 2)

    def test_closed_domain_rejects_unsupported_and_unjustified_probability(self):
        changes = [{"law": None}, {"law": {"N": "1/2", "H": "1/2", "HA": "1/2"}},
                   {"law": {"N": "2/4", "H": "1/3", "HA": "1/6"}},
                   {"law": {"N": "1/2", "H": "1/2", "HA": "-0/1"}},
                   {"horizon": 28}, {"water_budget_liters": 19},
                   {"policies": ["C", "R", "E", "E_prime"]},
                   {"require_all_scenarios": "true"}, {"unknown_field": 1}]
        for change in changes:
            with self.subTest(change=change), self.assertRaises(ValueError):
                validate_model({**default_model(), **change})


class NativeCompilation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = evaluate_model(default_model())
        edited = default_model()
        edited["policies"][-1] = "E_prime"
        cls.edited = evaluate_model(edited)

    def test_native_bytes_results_certificates_and_oracle(self):
        expected = {"C": ("1/2", ["q0"], ["q0"]),
                    "R": ("1/1", ["q0", "q1"], ["q0", "q1"]),
                    "E": ("5/6", ["q0", "q1", "q2"], ["q0", "q1"])}
        for mode, run in self.base["native_runs"].items():
            raw = run["native_input_json"].encode()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), run["native_result"]["input_digest"])
            self.assertEqual(json.loads(run["native_result_json"]), run["native_result"])
            self.assertEqual(run["verification"]["status"], "VALID")
            self.assertEqual(run["native_result"]["integration"]["state"], "DEFINED")
            self.assertEqual(run["native_result"]["execution"]["progress"]["expanded_nodes"], "75")
        for pid, (probability, possible, robust) in expected.items():
            p = self.base["canonical_results"]["policies"][pid]
            self.assertEqual(p["pvs"]["value"], probability)
            self.assertEqual(p["cag"]["possible"], possible)
            self.assertEqual(p["cag"]["robust"], robust)
            self.assertEqual(sum(map(Fraction, p["pvs"]["masses"].values())), 1)
            self.assertEqual(p["endpoint_probability"]["value"], "1/1")
        self.assertEqual(self.base["canonical_results"]["decision"]["selected"], "R")

    def test_edited_native_frontier_has_no_invented_winner(self):
        c = self.edited["canonical_results"]
        self.assertEqual(set(c["decision"]["frontier"]), {"R", "E_prime"})
        self.assertEqual(set(c["decision"]["feasible"]), {"R", "E_prime"})
        self.assertIsNone(c["decision"]["selected"])
        self.assertEqual(c["decision"]["selection_status"], "OUTSIDE_DOMAIN")
        self.assertEqual(c["policies"]["E_prime"]["pvs"]["value"], "1/1")
        self.assertEqual(c["policies"]["E_prime"]["cag"]["robust"], ["q0", "q1", "q2"])
        self.assertNotEqual(self.base["native_result"]["input_digest"], self.edited["native_result"]["input_digest"])

    def test_welfare_preserves_distribution_and_time(self):
        c = self.base["canonical_results"]
        cr = [p for p in c["decision"]["pairs"] if {p["left"], p["right"]} == {"C", "R"}]
        self.assertEqual([p["welfare"] for p in cr], ["0", "0"])
        for policy in c["policies"].values():
            profile = policy["wellbeing"]["profile"]
            self.assertEqual(len(profile), 3 * 15 * 4)
            self.assertEqual({x["carrier"] for x in profile}, {"A", "B", "P1", "P2"})

    def test_semantic_mapping_uses_monitor_not_terminal_hydration(self):
        manifest = self.base["compilation_manifest"]
        failures = [r for r in manifest["semantic_references"] if r["meaning"] == "violated_trajectory"]
        self.assertEqual(len(failures), 3)
        self.assertTrue(all(r["domain_endpoint"] == 2 and r["domain_monitor"] for r in failures))

    def test_zero_probability_does_not_remove_causal_branch(self):
        model = default_model()
        model["law"] = {"N": "1/2", "H": "1/2", "HA": "0/1"}
        r = evaluate_model(model)["canonical_results"]
        self.assertEqual(r["policies"]["E"]["pvs"]["value"], "1/1")
        self.assertEqual(r["policies"]["E"]["cag"]["robust"], ["q0", "q1"])
        self.assertFalse(r["policies"]["E"]["viability"]["all_scenarios"])
        self.assertIn("E", r["decision"]["failed"])

    def test_native_semantic_gap_keeps_positive_indeterminate_mass(self):
        instance, _ = compile_model(default_model())
        instance["semantics"]["references"] = [row for row in instance["semantics"]["references"]
            if not (row["leaf"]["policy"] == "E" and row["leaf"]["path"][9] == "HA")]
        raw = json.dumps(instance, ensure_ascii=False, separators=(",", ":")).encode()
        result = evaluate(raw)
        e = next(p for p in result["policies"] if p["policy"] == "E")
        self.assertEqual(e["probability"]["vector"]["value"]["undecided"], "1/6")
        self.assertEqual(e["probability"]["pvs"]["state"], "OUTSIDE_DOMAIN")
        self.assertEqual(verify_result(raw, result)["status"], "VALID")

    def test_changed_bytes_and_forged_result_fail_verification(self):
        raw = self.base["native_input_json"].encode()
        result = self.base["native_result"]
        self.assertEqual(verify_result(raw + b"\n", result)["status"], "INVALID")
        forged = copy.deepcopy(result)
        next(p for p in forged["policies"] if p["policy"] == "E")["probability"]["pvs"]["value"] = "1/1"
        self.assertEqual(verify_result(raw, forged)["status"], "INVALID")


if __name__ == "__main__":
    unittest.main()
