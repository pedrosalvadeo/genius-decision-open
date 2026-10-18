import unittest

from genius_twin import registry, route_search
from genius_twin.route_proposer import Encoding, LearnedProposer, Network
from test_decision_window import blood_model


class RouteProposerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = blood_model()
        cls.values = route_search.declared_values(cls.model)
        cls.result = route_search.search(cls.model, registry.evaluate, batches=1, seed=1, proposer="learned",
                                         candidates_per_batch=12)

    def test_features_read_the_route_in_the_twin_language(self):
        e = Encoding(self.model, self.values)
        policies = {p["id"]: p for p in self.model["policies"]}
        A = len(e.actions)
        # campaign: campaign_and_electives at steps 1-3, then its default supply_electives.
        x = e.features(policies["campaign"])
        self.assertEqual(x[e.actions.index("campaign_and_electives")], 1)
        self.assertEqual(x[3 * A + e.actions.index("supply_electives")], 1)
        # A conditional rule adds a feature for its declared condition; it does not fix the step's action.
        x = e.features(policies["defer_below_two_days"])
        self.assertEqual(x[e.actions.index("defer")], 1)
        self.assertTrue(any(i >= e.H * A for i in x))
        self.assertEqual(len(e.targets), 3 * (1 + 3 * (e.H + 1) + 2))

    def test_network_learns_a_small_table(self):
        xs = [{0: 1}, {1: 1}, {0: 1, 1: 1}, {}]
        ys = [[1.0, 0.0], [0.0, 1.0], [1.0, 1.0], [0.0, 0.0]]
        net = Network(2, 2, hidden=8, seed=0).fit(xs, ys, epochs=400, lr=0.05)
        for x, y in zip(xs, ys):
            self.assertTrue(all(abs(p - t) < 0.2 for p, t in zip(net.predict(x), y)))

    def test_learned_search_sends_its_choices_to_the_kernel(self):
        result = self.result
        self.assertEqual(result["proposer"], "learned")
        self.assertEqual([b["status"] for b in result["batches"]], ["VERIFIED"])
        [learning] = result["learning"]
        self.assertEqual(learning["rows"], 4)
        self.assertEqual(learning["drawn"], 12)
        chosen = learning["chosen"]
        # The champions hold 2 places, so 4 new routes: one aimed at each champion's carrier, one exploration slot.
        self.assertEqual(len(chosen), 4)
        self.assertEqual(sum(1 for c in chosen if c.get("exploration")), 1)
        evaluated = {r["route"] for r in result["rows"] if r["batch"] == 1}
        self.assertTrue({c["route"] for c in chosen} <= evaluated)
        # Champions still change only by the kernel's per-carrier comparison.
        self.assertNotIn("as_usual", result["champions"].values())

    def test_earlier_rows_of_the_same_model_train_the_network(self):
        proposer = LearnedProposer(self.model, self.values, training_rows=self.result["rows"])
        self.assertEqual(proposer.train([])["rows"], len(self.result["rows"]))
        again = route_search.search(self.model, registry.evaluate, batches=1, seed=1, proposer="learned",
                                    candidates_per_batch=12, training_rows=self.result["rows"])
        self.assertEqual(again["learning"][0]["rows"], 4 + len(self.result["rows"]))
        other = route_search.search(self.model, registry.evaluate, batches=1, seed=1, proposer="learned",
                                    candidates_per_batch=12, training_rows=[{**r, "model_sha256": "other"} for r in self.result["rows"]])
        self.assertEqual(other["learning"][0]["rows"], 4)

    def test_learned_proposer_serves_the_per_carrier_goal_only(self):
        with self.assertRaises(ValueError):
            route_search.search(self.model, registry.evaluate, goal="dominance", proposer="learned")
        with self.assertRaises(ValueError):
            route_search.search(self.model, registry.evaluate, proposer="oracle")


if __name__ == "__main__":
    unittest.main()
