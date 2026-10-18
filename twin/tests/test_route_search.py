import unittest

from genius_twin import registry, route_search
from test_decision_window import blood_model


class RouteSearchTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = blood_model()
        cls.result = route_search.search(cls.model, registry.evaluate, batches=2, seed=1)

    def test_every_batch_is_kernel_verified_and_rows_record_each_verdict(self):
        result = self.result
        self.assertEqual(result["format"], "genius-route-search/1")
        self.assertEqual([b["status"] for b in result["batches"]], ["VERIFIED", "VERIFIED"])
        # Batch 0 is the declared model; each later batch holds 3 elites and 3 new routes.
        self.assertEqual(len(result["rows"]), 4 + 2 * 6)
        row = result["rows"][-1]
        self.assertEqual(set(row), {"format", "batch", "route", "origin", "policy", "feasible", "frontier",
                                    "strictly_dominated_by", "pvs", "cag_robust", "by_scenario"})
        self.assertEqual(set(row["by_scenario"]), {"mild", "moderate", "severe"})
        self.assertEqual(result["declared_frontier"], ["defer_below_two_days", "campaign", "campaign_and_defer"])

    def test_candidates_use_only_declared_actions_and_quantities(self):
        actions = {a["id"] for a in self.model["actions"]}
        values = route_search.declared_values(self.model)
        self.assertEqual(values, {"inventory": ["39/5", "78/5"]})
        for row in self.result["rows"]:
            policy = row["policy"]
            self.assertIn(policy["default_action"], actions)
            for rule in policy["rules"]:
                self.assertIn(rule["action"], actions)
                for p in rule["when"]:
                    if p["kind"] == "stock":
                        self.assertIn(p["value"], values[p["stock"]])

    def test_search_is_reproducible_by_seed(self):
        again = route_search.search(self.model, registry.evaluate, batches=1, seed=1)
        self.assertEqual(again["rows"][4:10], self.result["rows"][4:10])

    def test_rejects_no_room_for_candidates(self):
        with self.assertRaises(ValueError):
            route_search.search(self.model, registry.evaluate, elites=6)


if __name__ == "__main__":
    unittest.main()
