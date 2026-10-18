from copy import deepcopy
import unittest

from genius_twin import living, population, registry
from test_decision_window import blood_model

# A declared test observation of every stock at step 2 (not a reading, not taken from any trajectory).
OBSERVED = {"inventory": "14/1", "electives": "30/1", "donor_pool": "10/1"}


class PopulationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = blood_model()
        cls.founded = population.found(cls.model, "us_blood_2026", registry.evaluate, batches=1, seed=1)
        cls.gen0 = cls.founded["generations"][0]
        now = living.reanchor(cls.model, 2, OBSERVED, cls.model["initial_capabilities"])
        cls.pop = population.advance(cls.founded, now, 2, "TEST_OBSERVATION", registry.evaluate, batches=1, seed=1)
        cls.gen1 = cls.pop["generations"][1]

    def test_generation_zero_keeps_life_and_one_route_per_niche(self):
        self.assertEqual(self.founded["format"], "genius-route-population/1")
        self.assertEqual(set(self.gen0["niches"]), {"emergency_patients", "surgical_patients", "red_cross", "donors"})
        # as_usual loses the life condition under severe flu while other routes keep it.
        self.assertIn({"route": "as_usual", "reason": "LOSES_THE_LIFE_CONDITION", "loses_life_in": ["severe"],
                       "evidence": "MODEL_STEP_0"}, self.gen0["died"])
        self.assertEqual(self.gen0["life_condition_kept_by"], sorted(set(self.gen0["niches"].values())))

    def test_the_present_kills_and_the_survivors_reproduce(self):
        self.assertEqual(self.gen1["step"], 2)
        deaths = [d for d in self.gen1["died"] if d["reason"] == "LOSES_THE_LIFE_CONDITION"]
        self.assertTrue(deaths)
        self.assertTrue(all(d["evidence"] == "TEST_OBSERVATION" for d in deaths))
        self.assertEqual(self.gen1["life_condition_kept_by"], sorted(set(self.gen1["niches"].values())))
        alive = population.alive(self.pop)
        self.assertEqual(set(alive), set(self.gen1["niches"].values()))
        for rid in self.gen1["born"]:
            member = alive[rid]
            self.assertEqual((member["born_generation"], member["born_step"]), (1, 2))
            # Routes are kept in the model's original steps; a route born at step 2 acts only later.
            self.assertTrue(all(t > 2 for rule in member["policy"]["rules"] for t in rule["steps"]))

    def test_the_next_generation_inherits_every_verdict(self):
        [learning] = self.gen1["learning"]
        rows_gen0 = [r for r in self.pop["memory"] if r["generation"] == 0]
        own_batch0 = [r for r in self.pop["memory"] if r["generation"] == 1 and r["batch"] == 0]
        self.assertEqual(learning["rows"], len(rows_gen0) + len(own_batch0))
        self.assertTrue(all("policy_original" in r for r in self.pop["memory"]))

    def test_between_observations_the_population_keeps_evolving_on_the_same_present(self):
        now = living.reanchor(self.model, 2, OBSERVED, self.model["initial_capabilities"])
        pop = deepcopy(self.pop)
        before = len(pop["memory"])
        population.evolve(pop, now, registry.evaluate, batches=1, seed=1)
        gen2 = pop["generations"][2]
        self.assertEqual((gen2["generation"], gen2["kind"], gen2["step"]), (2, "SAME_PRESENT", 2))
        self.assertEqual(self.gen1["kind"], "OBSERVED_PRESENT")
        self.assertEqual(gen2["life_condition_kept_by"], sorted(set(gen2["niches"].values())))
        self.assertGreater(gen2["learning"][0]["rows"], self.gen1["learning"][0]["rows"])
        self.assertGreaterEqual(len(pop["memory"]), before)
        with self.assertRaises(ValueError):
            population.evolve(pop, self.model, registry.evaluate)

    def test_a_generation_needs_a_later_full_restart(self):
        now = living.reanchor(self.model, 2, OBSERVED, self.model["initial_capabilities"])
        with self.assertRaises(ValueError):
            population.advance(self.pop, now, 2, "AGAIN", registry.evaluate)
        with self.assertRaises(ValueError):
            population.advance(self.pop, self.model, 3, "NOT_RESTARTED", registry.evaluate)


if __name__ == "__main__":
    unittest.main()
