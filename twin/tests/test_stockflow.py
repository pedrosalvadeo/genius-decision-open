"""Domain/compiler regression gates for the configurable finite profile."""
from copy import deepcopy
from fractions import Fraction
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
for directory in (ROOT / "twin", ROOT / "kernel"):
    sys.path.insert(0, str(directory))

from genius_twin.stockflow import default_model, validate_model, compute_trajectories, model_schema
from genius_twin.stockflow_compiler import compile_model, evaluate_model


class StockFlowContracts(unittest.TestCase):
    def test_declared_care_example_and_exact_native_results(self):
        model = default_model()
        before = deepcopy(model)
        result = evaluate_model(model)
        self.assertEqual(model, before)
        self.assertTrue(result["verification"]["valid"])
        policies = result["canonical_results"]["policies"]
        manual, reserve = policies["manual_policy"], policies["reserve_policy"]
        self.assertEqual(manual["pvs"]["value"], "2/3")
        self.assertEqual(reserve["pvs"]["value"], "1/1")
        self.assertEqual(manual["endpoint_probability"]["value"], "1/1")
        self.assertLess(set(manual["cag"]["robust"]), set(reserve["cag"]["robust"]))
        self.assertEqual([r["stocks"]["buffer"] for r in manual["trajectories"]["peak"]["daily"]], ["2/1", "2/1", "0/1", "1/1"])
        self.assertEqual(result["canonical_results"]["decision"]["selected"], "reserve_policy")
        # Removing the explicit universal task leaves a welfare tradeoff at t1:
        # reserve uses 30 minutes, manual uses 20. Better PVS/CAG is no override.
        model["require_all_scenarios"] = False
        unforced = evaluate_model(model)["canonical_results"]
        self.assertEqual(set(unforced["decision"]["frontier"]), {"manual_policy", "reserve_policy"})
        self.assertIsNone(unforced["decision"]["selected"])

    def test_module_one_functions_are_measured_on_every_projected_twin(self):
        model = default_model()
        neutral = evaluate_model(model)["canonical_results"]
        self.assertEqual({m["module"]: m["status"] for m in neutral["modules"]["modules"]}["I"], "NEUTRAL")
        model["functions"] = [
            {"id": "buffer_ok", "label": "Reserva disponible", "serves": ["P"], "measure": "cumulative",
             "when": [{"kind": "stock", "stock": "buffer", "op": "ge", "value": "1/1"}]},
            {"id": "buffer_now", "label": "Reserva ahora", "serves": [], "measure": "current",
             "when": [{"kind": "stock", "stock": "buffer", "op": "ge", "value": "1/1"}]}]
        result = evaluate_model(model)
        self.assertTrue(result["verification"]["valid"])
        results = result["canonical_results"]
        manual = results["policies"]["manual_policy"]["functional"]
        self.assertEqual(manual["native_cell"]["state"], "DEFINED")
        # Buffer 2, 2, 0, 1 in the peak: held, held, missed, held.
        self.assertEqual([(r["function"], r["terminal"], r["steps_held"], r["first_unmet_step"]) for r in manual["by_scenario"]["peak"]],
                         [("buffer_ok", "3/1", 3, 2), ("buffer_now", "1/1", 3, 2)])
        self.assertEqual({m["module"]: m["status"] for m in results["modules"]["modules"]}["I"], "FILLED")
        self.assertEqual(results["decision"]["functional_criterion"], "DECLARED_FUNCTIONS_TERMINAL_PROFILE")
        bad = deepcopy(model)
        bad["functions"][0]["when"][0]["stock"] = "missing"
        with self.assertRaises(ValueError):
            validate_model(bad)
        bad = deepcopy(model)
        bad["functions"][1]["id"] = "buffer_ok"
        with self.assertRaises(ValueError):
            validate_model(bad)

    def test_law_missing_preserves_native_partial_and_zero_branch_still_counts(self):
        model = default_model(); model["law"] = None
        result = evaluate_model(model)
        self.assertTrue(result["verification"]["valid"])
        self.assertEqual(result["native_result"]["integration"]["state"], "OUTSIDE_DOMAIN")
        self.assertIsNone(result["canonical_results"]["policies"]["manual_policy"]["pvs"]["value"])
        self.assertIsNotNone(result["canonical_results"]["policies"]["manual_policy"]["wellbeing"]["profile"])
        model = default_model(); model["law"] = {"ordinary": "1/1", "peak": "0/1"}
        manual = evaluate_model(model)["canonical_results"]["policies"]["manual_policy"]
        self.assertEqual(manual["pvs"]["value"], "1/1")
        self.assertFalse(manual["viability"]["all_scenarios"])

    def test_unknown_not_coerced_to_zero_and_known_failure_dominates(self):
        model = default_model()
        model["task"]["conditions"].append({"stock": "time", "op": "ge", "threshold": None})
        result = evaluate_model(model)["canonical_results"]["policies"]
        self.assertEqual(result["manual_policy"]["task_probability"]["masses"], {"success": "0/1", "failure": "1/3", "undecided": "2/3"})
        self.assertIsNone(result["manual_policy"]["pvs"]["value"])
        self.assertIsNone(result["reserve_policy"]["viability"]["all_scenarios"])

    def test_stock_double_count_and_implicit_unit_conversion_are_rejected(self):
        model = default_model()
        model["actions"][0]["deposits"]["buffer"] = "2/1"
        with self.assertRaisesRegex(ValueError, "deposits exceed withdrawals"):
            validate_model(model)
        model = default_model()
        model["stocks"][2]["unit"] = "kg"
        with self.assertRaisesRegex(ValueError, "deposits exceed withdrawals"):
            validate_model(model)
        # A rejected transaction cannot consume its present first resource.
        model = default_model()
        model["scenarios"][0]["events"][0]["renewables"]["time"] = "0/1"
        row = compute_trajectories(model)["manual_policy"]["ordinary"]["daily"][1]
        self.assertFalse(row["action_executed"])
        self.assertEqual(row["stocks"]["water"], "8/1")
        self.assertEqual(row["ledger"]["water"]["withdrawal"], "0/1")

    def test_policy_is_chosen_before_current_event_and_shared_prefix_is_one_node(self):
        model = default_model()
        model["policies"][0]["rules"] = [{"steps": [2], "when": [{"kind": "stock", "stock": "buffer", "op": "ge", "value": "2/1"}], "action": "prepare"}]
        traces = compute_trajectories(model)["manual_policy"]
        self.assertEqual(traces["ordinary"]["daily"][:2], traces["peak"]["daily"][:2])
        self.assertEqual(traces["ordinary"]["daily"][2]["action_id"], "prepare")
        self.assertEqual(traces["peak"]["daily"][2]["action_id"], "prepare")
        native, manifest = compile_model(model)
        prefix_records = [r for r in manifest["query_records"] if r["query"]["policy"] == "manual_policy" and r["step"] == 1]
        self.assertEqual(len(prefix_records), 1)
        model["policies"][0]["rules"][0]["when"] = [{"kind": "scenario", "id": "peak"}]
        with self.assertRaises(ValueError):
            validate_model(model)

    def test_native_cag_loss_cannot_be_repaired_retroactively(self):
        model = default_model()
        model["policies"] = [model["policies"][1]]
        model["scenarios"] = [model["scenarios"][0]]
        model["law"] = {"ordinary": "1/1"}
        model["scenarios"][0]["events"][0]["remove_capabilities"] = ["care", "reserve_ready"]
        repair = deepcopy(model["actions"][1]); repair["id"] = "repair"; repair["requires"] = []; repair["add_capabilities"] = ["care", "reserve_ready"]
        model["actions"].append(repair)
        model["policies"][0]["rules"].append({"steps": [2], "when": [], "action": "repair"})
        output = evaluate_model(model)["canonical_results"]["policies"]["reserve_policy"]
        final_org = output["trajectories"]["ordinary"]["daily"][-1]["organization"]
        self.assertEqual(output["cag"]["possible"], [output["cag"]["origin"]])
        self.assertNotIn(final_org, output["cag"]["possible"])

    def test_closed_validation_rational_and_occurrence_limits(self):
        for mutation in (lambda m: m.update(secret_future=True),
                         lambda m: m.update(horizon=True),
                         lambda m: m["stocks"][0].update(initial="16/2"),
                         lambda m: m["law"].update(peak="2/3"),
                         lambda m: m["scenarios"][0]["events"][0].update(renewables={})):
            model = default_model(); mutation(model)
            with self.assertRaises(ValueError):
                validate_model(model)
        model = default_model(); model["horizon"] = 30
        model["policies"] += [dict(deepcopy(model["policies"][0]), id="third")]
        with self.assertRaisesRegex(ValueError, "occurrence limit"):
            validate_model(model)
        self.assertEqual(model_schema()["additionalProperties"], False)

    def test_generated_signature_limit_rejects_without_truncation(self):
        model = default_model(); model["horizon"] = 16
        model["capabilities"] = [{"id": "c" + str(i), "label": "Capability " + str(i)} for i in range(5)]
        model["initial_capabilities"] = []
        model["actions"] = []
        for i in range(5):
            for variant in ("add", "remove") if i < 4 else ("add",):
                model["actions"].append({"id": variant + str(i), "label": variant, "requires": [], "withdrawals": {}, "deposits": {}, "add_capabilities": ["c" + str(i)] if variant == "add" else [], "remove_capabilities": ["c" + str(i)] if variant == "remove" else []})
        rules = []
        for step in range(1, 16):
            previous, current = (step-1) ^ ((step-1) >> 1), step ^ (step >> 1)
            bit = (previous ^ current).bit_length() - 1
            rules.append({"steps": [step], "when": [], "action": ("add" if current & (1 << bit) else "remove") + str(bit)})
        rules.append({"steps": [16], "when": [], "action": "add4"})
        model["policies"] = [{"id": "gray", "label": "Gray path", "default_action": "add0", "rules": rules}]
        model["scenarios"] = [{"id": "one", "label": "Single word", "events": [{"inflows": {}, "renewables": {"time": "30/1"}, "drains": {}, "remove_capabilities": []} for _ in range(16)]}]
        model["law"] = {"one": "1/1"}
        with self.assertRaisesRegex(ValueError, "signature limit"):
            validate_model(model)

    def test_operational_hour_example_preserves_generic_profile_and_no_life_claim(self):
        model = json.loads((ROOT / "twin/examples/stockflow_time.json").read_text())
        result = evaluate_model(model)["canonical_results"]
        self.assertEqual(result["horizon"], 4)
        self.assertEqual(result["step_unit"], "hour")
        for policy in result["policies"].values():
            self.assertIsNone(policy["pvs"]["value"])
            self.assertEqual(policy["pvs"]["state"], "NOT_APPLICABLE")
            self.assertIsNone(policy["task_probability"]["value"])
            self.assertFalse(policy["viability"]["all_scenarios"])
            for scenario in policy["trajectories"].values():
                for row in scenario["daily"]:
                    for balance in row["ledger"].values():
                        self.assertEqual(Fraction(balance["before"]) + Fraction(balance["inflow"]) + Fraction(balance["renewal"]) - Fraction(balance["expiry"]) - Fraction(balance["withdrawal"]) + Fraction(balance["deposit"]) - Fraction(balance["drained"]) - Fraction(balance["spill"]), Fraction(balance["after"]))


if __name__ == "__main__":
    unittest.main()
