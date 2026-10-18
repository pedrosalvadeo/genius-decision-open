from copy import deepcopy
import unittest

from genius_twin import anytime, registry
from genius_twin.decision_window import commit
from test_decision_window import blood_model


class FakeTime:
    """Each evaluation takes `step` seconds of a clock the test controls."""
    def __init__(self, step):
        self.now, self.step = 0, step

    def clock(self):
        return self.now

    def evaluator(self, model):
        result = registry.evaluate(model)
        self.now += self.step
        return result


class AnytimeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = blood_model()
        cls.full = registry.evaluate(cls.model)["canonical_results"]

    def test_all_scenarios_reproduce_the_full_pvs_exactly(self):
        result = anytime.evaluate(self.model, registry.evaluate, 600)
        self.assertEqual(result["status"], "COMPLETE_BY_SCENARIO")
        self.assertEqual(result["evaluated_mass"], "1/1")
        for pid, route in result["routes"].items():
            self.assertTrue(route["pvs_bounds"]["exact"])
            self.assertEqual(route["pvs_bounds"]["min"], self.full["policies"][pid]["pvs"]["value"])
        self.assertEqual(result["routes"]["as_usual"]["refuted_in"], ["severe"])
        self.assertEqual(sorted(result["unrefuted"]), sorted(self.full["decision"]["feasible"]))
        self.assertEqual(result["selection_status"], "NO_SELECTION_BY_MODEL_RULE")
        self.assertTrue(all(run["verification_valid"] for run in result["runs"]))

    def test_window_closes_with_exact_bounds_and_declared_ties(self):
        fake = FakeTime(10)
        result = anytime.evaluate(self.model, fake.evaluator, 15, clock=fake.clock)
        self.assertEqual((result["status"], result["evaluated"], result["not_evaluated"]),
                         ("WINDOW_CLOSED", ["mild"], ["moderate", "severe"]))
        self.assertEqual(result["routes"]["as_usual"]["pvs_bounds"], {"min": "1/3", "max": "1/1", "exact": False})
        self.assertEqual(result["label"], "1 de 3 escenarios evaluados (masa 1/3)")
        fake = FakeTime(10)
        worst = anytime.evaluate(self.model, fake.evaluator, 15, ["severe", "moderate", "mild"], clock=fake.clock)
        self.assertEqual(worst["order_basis"], "LAW_MASS_DESCENDING_TIES_DECLARED_ORDER")
        self.assertEqual(worst["evaluated"], ["severe"])
        self.assertTrue(worst["routes"]["as_usual"]["refuted"])
        self.assertEqual(worst["routes"]["as_usual"]["pvs_bounds"], {"min": "0/1", "max": "2/3", "exact": False})
        self.assertEqual(worst["routes"]["campaign"]["pvs_bounds"], {"min": "1/3", "max": "1/1", "exact": False})
        self.assertEqual(worst["selection_status"], "NO_SELECTION_BY_MODEL_RULE")

    def test_selects_only_a_single_unrefuted_route_when_the_model_allows_it(self):
        late, _ = commit(self.model, 3, "as_usual")
        late["selection"] = "unique"
        fake = FakeTime(10)
        result = anytime.evaluate(late, fake.evaluator, 15, ["severe", "moderate", "mild"], clock=fake.clock)
        self.assertEqual((result["selected"], result["selection_status"]),
                         ("defer_below_two_days", "CONDITIONAL_ON_UNEVALUATED_SCENARIOS"))
        fake = FakeTime(10)
        mild_first = anytime.evaluate(late, fake.evaluator, 15, clock=fake.clock)
        self.assertEqual((mild_first["selected"], mild_first["selection_status"]), (None, "NO_SELECTION_WITHIN_WINDOW"))
        loose = deepcopy(late)
        loose["require_all_scenarios"] = False
        fake = FakeTime(10)
        never = anytime.evaluate(loose, fake.evaluator, 15, ["severe", "moderate", "mild"], clock=fake.clock)
        self.assertEqual(never["unrefuted"], ["as_usual", "defer_below_two_days"])
        self.assertIsNone(never["selected"])

    def test_null_law_reports_the_range_only_when_every_scenario_is_known(self):
        model = deepcopy(self.model)
        model["law"] = None
        complete = anytime.evaluate(model, registry.evaluate, 600)
        self.assertEqual(complete["routes"]["as_usual"]["law_range"], {"min": "0/1", "max": "1/1"})
        self.assertEqual(complete["routes"]["campaign"]["law_range"], {"min": "1/1", "max": "1/1"})
        self.assertIsNone(complete["routes"]["campaign"]["pvs_bounds"])
        fake = FakeTime(10)
        partial = anytime.evaluate(model, fake.evaluator, 15, clock=fake.clock)
        self.assertEqual(partial["order_basis"], "MODEL_ORDER_NULL_LAW")
        self.assertIsNone(partial["routes"]["campaign"]["law_range"])
        self.assertIsNone(partial["evaluated_mass"])

    def test_an_unverified_run_stops_the_evaluation(self):
        def broken(model):
            result = registry.evaluate(model)
            result["verification"] = {"valid": False}
            return result
        result = anytime.evaluate(self.model, broken, 600)
        self.assertEqual((result["status"], result["evaluated"]), ("UNVERIFIED_RUN", []))
        self.assertEqual(result["routes"]["campaign"]["pvs_bounds"], {"min": "0/1", "max": "1/1", "exact": False})

    def test_rejects_bad_order_or_budget(self):
        with self.assertRaises(ValueError):
            anytime.evaluate(self.model, registry.evaluate, 10, ["mild"])
        with self.assertRaises(ValueError):
            anytime.evaluate(self.model, registry.evaluate, 0)


if __name__ == "__main__":
    unittest.main()
