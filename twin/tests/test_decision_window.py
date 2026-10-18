import json
from pathlib import Path
import unittest

from genius_twin import construction, registry
from genius_twin.decision_window import cells, commit, committed_steps, plan

ROOT = Path(__file__).resolve().parents[1]


def blood_model():
    world = json.loads((ROOT / "cases/us_blood_2026/world.json").read_text())
    prepared = construction.prepare(world["construction"], dict(id="observation", revision=1,
                                                                observation=world["observation"], historical_gaps={}))
    return prepared["model"]


WEEK = 7 * 24 * 3600


class DecisionWindowTest(unittest.TestCase):
    def setUp(self):
        self.model = blood_model()

    def test_committed_steps_count_actions_before_the_decision_takes_effect(self):
        self.assertEqual(committed_steps(0, 8, WEEK, 0), 0)
        self.assertEqual(committed_steps(5, 8, WEEK, 0), 1)
        self.assertEqual(committed_steps(5, 8, WEEK, 10), 0)
        self.assertEqual(committed_steps(2 * WEEK, 8, WEEK, 0), 2)
        self.assertEqual(committed_steps(2 * WEEK + 1, 8, WEEK, 0), 3)
        self.assertEqual(committed_steps(100 * WEEK, 8, WEEK, 0), 8)

    def test_fast_decider_keeps_every_route(self):
        result = plan(self.model, {"available_seconds": 60, "step_seconds": WEEK, "first_action_offset_seconds": 3600})
        self.assertEqual(result["status"], "FITS_WINDOW")
        self.assertEqual(result["cells"], cells(self.model))
        self.assertEqual(result["cells"], 4 * 3 * 9)
        self.assertEqual(result["cost_basis"], "REFERENCE_MEASUREMENT_NOT_THIS_DECIDER")
        self.assertEqual(result["committed_steps"], 0)
        self.assertEqual(result["model"], self.model)

    def test_slow_decision_commits_steps_and_closes_routes(self):
        window = {"available_seconds": 3 * WEEK, "step_seconds": WEEK, "seconds_per_cell": 3 * WEEK // 108 + 1}
        with self.assertRaisesRegex(ValueError, "committed_route"):
            plan(self.model, window)
        result = plan(self.model, {**window, "committed_route": "as_usual"})
        self.assertEqual(result["status"], "DOES_NOT_FIT_WINDOW")
        self.assertEqual(result["committed_steps"], 3)
        # The donor campaign runs in weeks 1-3: once they are committed, it is no longer a choice.
        self.assertEqual(result["identical_routes"], [{"route": "campaign", "same_as": "as_usual"},
                                                      {"route": "campaign_and_defer", "same_as": "defer_below_two_days"}])
        evaluation = registry.evaluate(result["model"])
        self.assertTrue(evaluation["verification"]["valid"])
        decision = evaluation["canonical_results"]["decision"]
        self.assertEqual(decision["frontier"], ["defer_below_two_days"])
        full = registry.evaluate(self.model)["canonical_results"]["decision"]
        self.assertEqual(full["frontier"], ["campaign", "campaign_and_defer", "defer_below_two_days"])

    def test_observation_age_counts_and_merged_committed_route_is_renamed(self):
        window = {"available_seconds": 60, "step_seconds": WEEK, "first_action_offset_seconds": 3600}
        self.assertEqual(plan(self.model, window)["committed_steps"], 0)
        with self.assertRaisesRegex(ValueError, "3 steps are committed"):
            plan(self.model, {**window, "observation_age_seconds": 3 * WEEK})
        late = plan(self.model, {**window, "observation_age_seconds": 3 * WEEK, "committed_route": "campaign"})
        self.assertEqual(late["committed_steps"], 3)
        self.assertEqual(late["committed_route"], "as_usual")
        self.assertIn("as_usual", {p["id"] for p in late["model"]["policies"]})

    def test_commit_keeps_later_rules_and_rejects_empty_choices(self):
        model, identical = commit(self.model, 2, "as_usual")
        self.assertEqual(identical, [])
        campaign = next(p for p in model["policies"] if p["id"] == "campaign")
        self.assertEqual(campaign["rules"][-1], {"steps": [3], "when": [], "action": "campaign_and_electives"})
        self.assertEqual(campaign["rules"][0], {"steps": [1, 2], "when": [], "action": "supply_electives"})
        with self.assertRaisesRegex(ValueError, "at least one step"):
            commit(self.model, 8, "as_usual")
        with self.assertRaisesRegex(ValueError, "unknown"):
            commit(self.model, 2, "nope")

    def test_window_that_ends_after_the_horizon_leaves_nothing_to_decide(self):
        result = plan(self.model, {"available_seconds": 9 * WEEK, "step_seconds": WEEK,
                                   "seconds_per_cell": 9 * WEEK, "committed_route": "as_usual"})
        self.assertEqual(result["status"], "NO_STEP_LEFT_TO_DECIDE")
        self.assertIsNone(result["model"])

    def test_rejects_inexact_or_unknown_fields(self):
        for window in ({"available_seconds": 1.5, "step_seconds": 1}, {"available_seconds": 1, "step_seconds": 0},
                       {"available_seconds": 1, "step_seconds": 1, "speed": 2}, {"available_seconds": True, "step_seconds": 1}):
            with self.assertRaises(ValueError):
                plan(self.model, window)


if __name__ == "__main__":
    unittest.main()
