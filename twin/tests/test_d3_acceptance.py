"""Independent D3 acceptance oracles, explicitly hypothetical.

Expected numbers below are elementary balances authored independently of the
compiler and its examples. Tests must exercise real native evaluation; a
completed process is not empirical admission or universal policy superiority.
"""
from copy import deepcopy
from fractions import Fraction
from functools import lru_cache
import json
import os
import select
import subprocess
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
for folder in (ROOT / "twin", ROOT / "kernel"):
    sys.path.insert(0, str(folder))


def event(*, inflows=None, drains=None, remove=None, renewables=None):
    return {"inflows": inflows or {}, "renewables": renewables or {},
            "drains": drains or {}, "remove_capabilities": remove or []}


def action(aid="noop", *, withdrawals=None, deposits=None, add=None, remove=None):
    return {"id": aid, "label": aid, "requires": [],
            "withdrawals": withdrawals or {}, "deposits": deposits or {},
            "add_capabilities": add or [], "remove_capabilities": remove or []}


def path_fixture():
    """Two different paths with the SAME endpoint; probability is 3/4, not 1."""
    return {
        "profile": "STOCK_FLOW_FINITE_V1", "name": "Independent path oracle",
        "horizon": 2, "step_unit": "step",
        "stocks": [{"id": "x", "label": "Shared reserve", "unit": "L",
                    "kind": "persistent", "initial": "2/1", "capacity": "2/1"}],
        "carriers": [{"id": "A", "label": "Declared living carrier", "kind": "living"}],
        "capabilities": [{"id": "base", "label": "Base organization"}],
        "initial_capabilities": ["base"], "actions": [action()],
        "policies": [{"id": "hold", "label": "Hold", "default_action": "noop", "rules": []}],
        "scenarios": [
            {"id": "low", "label": "Low demand", "events": [event(drains={"x": "1/1"}), event(inflows={"x": "1/1"})]},
            {"id": "high", "label": "High demand", "events": [event(drains={"x": "2/1"}), event(inflows={"x": "2/1"})]},
        ],
        "law": {"low": "3/4", "high": "1/4"},
        "welfare": [{"carrier": "A", "dimension": "reserve", "label": "Declared material condition",
                     "stock": "x", "direction": "higher"}],
        "task": {"kind": "life_conditions", "label": "Maintain reserve at every state",
                 "living_carriers": ["A"], "conditions": [{"stock": "x", "op": "ge", "threshold": "1/1"}],
                 "require_action_success": False},
        "require_all_scenarios": True, "selection": "unique",
        "assumptions": [{"id": "Hypothesis", "kind": "SYNTHETIC", "statement": "Hypothetical arithmetic fixture, no observations or real validation.", "provenance": "Independent acceptance design"}],
    }


def atomic_fixture():
    """Unavailable second resource aborts the ENTIRE transaction."""
    model = path_fixture()
    model["name"] = "Independent atomic transfer oracle"
    model["horizon"] = 1
    model["stocks"] = [
        {"id": "x", "label": "Source", "unit": "L", "kind": "persistent", "initial": "2/1", "capacity": "2/1"},
        {"id": "z", "label": "Destination", "unit": "L", "kind": "persistent", "initial": "0/1", "capacity": "1/1"},
        {"id": "time", "label": "Shared time", "unit": "minute", "kind": "renewable", "initial": "0/1", "capacity": "1/1"},
    ]
    model["capabilities"].append({"id": "learned", "label": "Learned organization"})
    model["actions"] = [action("move", withdrawals={"x": "2/1", "time": "1/1"}, deposits={"z": "2/1"}, add=["learned"])]
    model["policies"][0]["default_action"] = "move"
    model["scenarios"] = [
        {"id": "ready", "label": "Time available", "events": [event(renewables={"time": "1/1"})]},
        {"id": "absent", "label": "Time unavailable", "events": [event(renewables={"time": "0/1"})]},
    ]
    model["law"] = {"ready": "1/2", "absent": "1/2"}
    model["task"]["conditions"] = [{"stock": "x", "op": "ge", "threshold": "0/1"}]
    model["task"]["require_action_success"] = True
    return model


def restored_capability_fixture():
    model = path_fixture()
    model["capabilities"].append({"id": "learned", "label": "New organization"})
    model["actions"].append(action("rebuild", add=["base", "learned"]))
    model["policies"][0]["rules"] = [{"steps": [2], "when": [], "action": "rebuild"}]
    model["scenarios"] = [{"id": "broken", "label": "Broken then restored", "events": [event(remove=["base"]), event()]}]
    model["law"] = {"broken": "1/1"}
    return model


@lru_cache(maxsize=16)
def _actual_run(model_json):
    from genius_twin.stockflow_compiler import evaluate_model
    return evaluate_model(json.loads(model_json))


def evaluated(model):
    return deepcopy(_actual_run(json.dumps(model, sort_keys=True)))


def native_policy(envelope, policy="hold", mode="robust"):
    return next(row for row in envelope["native_runs"][mode]["native_result"]["policies"] if row["policy"] == policy)


def defined(cell):
    if cell["state"] != "DEFINED":
        raise AssertionError("Formal cell is not defined: " + repr(cell))
    return cell["value"]


class IndependentStockFlowOracles(unittest.TestCase):
    def traces(self, model):
        from genius_twin.stockflow import compute_trajectories, validate_model
        validate_model(model)
        return compute_trajectories(model)["hold"]

    def test_exact_path_balance_and_persistent_violation(self):
        traces = self.traces(path_fixture())
        for scenario, expected in {"low": ["2/1", "1/1", "2/1"], "high": ["2/1", "0/1", "2/1"]}.items():
            days = traces[scenario]["daily"]
            self.assertEqual([d["day"] for d in days], [0, 1, 2])
            self.assertEqual([d["stocks"]["x"] for d in days], expected)
            self.assertEqual([d["violation_seen"] for d in days], [False, scenario == "high", scenario == "high"])
            self.assertEqual(days[1]["action_id"], "noop")
            self.assertEqual(days[2]["action_id"], "noop")
        self.assertEqual(traces["low"]["daily"][0], traces["high"]["daily"][0])

    def test_atomicity_shared_resources_spill_and_unit_conservation(self):
        traces = self.traces(atomic_fixture())
        ready, absent = (traces[s]["daily"][1] for s in ("ready", "absent"))
        self.assertTrue(ready["action_executed"])
        self.assertFalse(absent["action_executed"])
        self.assertEqual(ready["stocks"], {"x": "0/1", "z": "1/1", "time": "0/1"})
        self.assertEqual(absent["stocks"], {"x": "2/1", "z": "0/1", "time": "0/1"})
        self.assertEqual(set(ready["capabilities"]), {"base", "learned"})
        self.assertEqual(set(absent["capabilities"]), {"base"})
        self.assertEqual(ready["ledger"]["z"]["spill"], "1/1")
        self.assertEqual(ready["ledger"]["time"]["withdrawal"], "1/1")
        self.assertEqual(absent["ledger"]["x"]["withdrawal"], "0/1")
        for day in (ready, absent):
            for ledger in day["ledger"].values():
                # Check the conservation identity ourselves, rather than trusting
                # the compiler's balance_valid flag as the only assertion.
                balance = sum(Fraction(ledger[k]) for k in ("before", "renewal", "inflow", "deposit"))
                balance -= sum(Fraction(ledger[k]) for k in ("expiry", "withdrawal", "spill", "drained"))
                self.assertEqual(balance, Fraction(ledger["after"]))
                self.assertTrue(ledger["balance_valid"])

    def test_probability_is_about_the_whole_path_and_zero_mass_is_not_universal(self):
        baseline = evaluated(path_fixture())
        row = native_policy(baseline)
        self.assertEqual(defined(row["probability"]["pvs"]), "3/4")
        self.assertEqual(defined(row["probability"]["vector"]), {"success": "3/4", "failure": "1/4", "undecided": "0/1"})
        model = path_fixture(); model["law"] = {"low": "1/1", "high": "0/1"}
        zero = evaluated(model)
        self.assertEqual(defined(native_policy(zero)["probability"]["pvs"]), "1/1")
        for envelope in (baseline, zero):
            projected = envelope["canonical_results"]["policies"]["hold"]
            self.assertFalse(projected["viability"]["all_scenarios"])
            self.assertEqual(projected["endpoint_probability"]["value"], "1/1")
            self.assertFalse(envelope["canonical_results"]["decision"]["selected"])
            self.assertEqual(set(projected["trajectories"]), {"low", "high"})

    def test_no_law_and_unknown_threshold_do_not_fabricate_a_probability(self):
        model = path_fixture(); model["law"] = None
        no_law = evaluated(model)
        row = native_policy(no_law)
        self.assertNotEqual(row["probability"]["pvs"]["state"], "DEFINED")
        projected = no_law["canonical_results"]["policies"]["hold"]
        self.assertIsNone(projected["pvs"]["value"])
        self.assertTrue(projected["cag"]["robust"])
        self.assertTrue(projected["wellbeing"]["profile"])
        self.assertFalse(projected["viability"]["all_scenarios"])
        model = path_fixture(); model["task"]["conditions"][0]["threshold"] = None
        unknown = evaluated(model)
        row = native_policy(unknown)
        self.assertEqual(defined(row["probability"]["vector"]), {"success": "0/1", "failure": "0/1", "undecided": "1/1"})
        self.assertNotEqual(row["probability"]["pvs"]["state"], "DEFINED")
        self.assertIsNone(unknown["canonical_results"]["policies"]["hold"]["pvs"]["value"])

    def test_acc_does_not_erase_an_intermediate_loss_when_capabilities_return(self):
        model = restored_capability_fixture()
        days = self.traces(model)["broken"]["daily"]
        self.assertEqual([set(d["capabilities"]) for d in days], [{"base"}, set(), {"base", "learned"}])
        projected = evaluated(model)["canonical_results"]["policies"]["hold"]
        origin, restored = days[0]["organization"], days[2]["organization"]
        self.assertNotEqual(origin, restored)
        self.assertEqual(projected["cag"]["recipe"], "acc")
        self.assertNotIn(restored, projected["cag"]["possible"])
        self.assertNotIn(restored, projected["cag"]["robust"])
        self.assertIn(origin, projected["cag"]["possible"])
        # A different model that preserves base through the transfer really does
        # reach the new signature; this is not a blanket refusal to show gains.
        transferred = evaluated(atomic_fixture())["canonical_results"]["policies"]["hold"]
        self.assertGreater(len(transferred["cag"]["possible"]), len(transferred["cag"]["robust"]))

    def test_native_receipts_bind_actual_inputs_and_an_operational_task_is_not_life(self):
        from genius_kernel import verify_result
        baseline = evaluated(path_fixture())
        model = path_fixture(); model["task"]["kind"] = "operational"; model["task"]["living_carriers"] = []
        operational = evaluated(model)
        projected = operational["canonical_results"]["policies"]["hold"]
        self.assertEqual(projected["task_probability"]["value"], "3/4")
        self.assertIsNone(projected["pvs"]["value"])
        for envelope in (baseline, operational):
            for run in envelope["native_runs"].values():
                self.assertTrue(verify_result(run["native_input_json"].encode(), run["native_result"])["valid"])
                self.assertEqual(json.loads(run["native_result_json"]), run["native_result"])
                self.assertEqual(run["native_result"]["execution"]["status"], "COMPLETE")
        # Change an actual condition, not only an interpretative label.
        changed = path_fixture(); changed["task"]["conditions"][0]["threshold"] = "0/1"
        revised = evaluated(changed)
        self.assertEqual(defined(native_policy(revised)["probability"]["pvs"]), "1/1")
        self.assertFalse(verify_result(revised["native_input_json"].encode(), baseline["native_result"])["valid"])


class IndependentD3HTTP(unittest.TestCase):
    def setUp(self):
        from genius_twin.app import create_app
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "independent.db"
        self.app = create_app(self.path, testing=True, evaluator=evaluated)
        self.client = self.app.test_client()

    def request(self, method, path, payload=None, status=200):
        response = self.client.open(path, method=method, json=payload)
        self.assertEqual(response.status_code, status, response.get_json())
        return response.get_json()

    def new_case(self):
        made = self.request("POST", "/api/cases", {"text": "Independent hypothetical reserve decision", "title": "Independent D3", "profile": "STOCK_FLOW_FINITE_V1"}, 201)
        self.assertEqual(made["case"]["current_version"], 0)
        self.assertIsNone(made["proposal"])
        self.assertEqual(made["obligations"][0]["cause"], "MODELO_PENDIENTE")
        return made["case"]["id"]

    def propose(self, cid, base, model):
        return self.request("POST", f"/api/cases/{cid}/proposals", {"base_version": base, "kind": "declared_model", "text": "Explicit independent hypothetical conditions", "structured": {"model": model}}, 201)["proposal"]

    def accept(self, proposal, base, key):
        payload = {"base_version": base, "confirmed": True, "acknowledge_declared": True, "idempotency_key": key}
        return self.request("POST", f"/api/proposals/{proposal['id']}/accept", payload)

    def test_full_declared_model_revision_and_reopened_canonical_receipt(self):
        from genius_twin.app import create_app
        cid = self.new_case()
        proposed = self.propose(cid, 0, path_fixture())
        rejected = self.request("POST", f"/api/proposals/{proposed['id']}/accept", {"base_version": 0, "confirmed": True, "idempotency_key": "independent-noack"}, 422)
        self.assertEqual(rejected["error"]["code"], "confirmation_required")
        accepted = self.accept(proposed, 0, "independent-v1")
        first = self.request("POST", f"/api/cases/{cid}/evaluate", {"version": 1})
        self.assertEqual(first["job"]["status"], "completed", first)
        one = first["evaluation"]
        self.assertEqual(one["admission"], "DECLARED_MODEL_ONLY")
        self.assertEqual(one["provenance"]["empirical_validation"], "NOT_ASSESSED")
        self.assertIsNone(one["rc01_receipt"])
        self.assertEqual(one["canonical_results"]["policies"]["hold"]["pvs"]["value"], "3/4")
        revised_model = path_fixture(); revised_model["task"]["conditions"][0]["threshold"] = "0/1"
        revised = self.propose(cid, 1, revised_model)
        self.accept(revised, 1, "independent-v2")
        history = self.request("GET", f"/api/cases/{cid}")
        self.assertEqual(history["case"]["current_version"], 2)
        self.assertEqual([j["version"] for j in history["jobs"]], [1])
        second = self.request("POST", f"/api/cases/{cid}/evaluate", {"version": 2})
        self.assertEqual(second["job"]["status"], "completed", second)
        two = second["evaluation"]
        self.assertEqual(two["canonical_results"]["policies"]["hold"]["pvs"]["value"], "1/1")
        self.assertNotEqual(one["model_sha256"], two["model_sha256"])
        self.assertNotEqual(one["native_result"]["input_digest"], two["native_result"]["input_digest"])
        comparison = self.request("GET", f"/api/cases/{cid}/compare?before=1&after=2")
        self.assertEqual(comparison["results"]["before"], one["canonical_results"])
        self.assertEqual(comparison["results"]["after"], two["canonical_results"])
        self.assertEqual([c["field"] for c in comparison["model_changes"]], ["task"])
        # Reopen the actual persisted Store, not the previous client state.
        self.client = create_app(self.path, testing=True, evaluator=evaluated).test_client()
        recovered = self.request("GET", f"/api/jobs/{first['job']['id']}")
        self.assertEqual(recovered, first)
        export = self.request("GET", f"/api/cases/{cid}/export")
        self.assertEqual(export["consumer_semantics"], "SAME_CANONICAL_OBJECT_FOR_HUMAN_APPLICATION_AGENT")
        self.assertEqual(export["dossier"]["observations"], [])
        self.assertEqual(len(export["dossier"]["versions"]), 2)
        self.assertEqual(export["dossier"]["versions"][0]["model_sha256"], accepted["version"]["model_sha256"])
        self.assertEqual(export["dossier"]["evaluations"][0], first)
        self.assertEqual(export["dossier"]["evaluations"][1], second)
        unsupported = self.request("POST", f"/api/cases/{cid}/observations", {
            "base_version": 2, "policy_id": "hold", "scenario_id": "high", "day": 1,
            "variable": "x", "value": "0/1", "unit": "L", "observed_at": "2026-10-13T00:00:00Z",
            "source": "Hypothetical rejected payload; not a real observation", "idempotency_key": "independent-observe"
        }, 422)
        self.assertEqual(unsupported["error"]["code"], "observation_profile_not_supported")
        unchanged = self.request("GET", f"/api/cases/{cid}")
        self.assertEqual(unchanged["case"]["current_version"], 2)
        self.assertEqual(unchanged["observations"], [])

    def test_stale_draft_and_repeated_confirmation_preserve_one_version(self):
        cid = self.new_case()
        draft = {"base_version": 0, "draft_revision": 0, "text": "Stored incomplete declared model", "model": {"profile": "STOCK_FLOW_FINITE_V1"}}
        saved = self.request("PATCH", f"/api/cases/{cid}/draft", draft)
        self.assertEqual(saved["draft"]["revision"], 1)
        stale = self.request("PATCH", f"/api/cases/{cid}/draft", draft, 409)
        self.assertEqual(stale["error"]["code"], "draft_conflict")
        proposed = self.propose(cid, 0, path_fixture())
        accepted = self.accept(proposed, 0, "independent-retry")
        self.assertEqual(self.accept(proposed, 0, "independent-retry"), accepted)
        self.request("PATCH", f"/api/cases/{cid}/draft", {**draft, "draft_revision": 1}, 409)
        data = self.request("GET", f"/api/cases/{cid}")
        self.assertEqual(len(data["versions"]), 1)
        self.assertEqual(data["draft"]["model"], draft["model"])
        self.assertEqual(data["jobs"], [])
        self.assertEqual(data["observations"], [])


@unittest.skipUnless(sys.platform == "linux", "The production parent-death guard is Linux-specific")
class IndependentProcessBoundary(unittest.TestCase):
    def test_real_compiler_child_dies_when_its_parent_is_killed(self):
        # The handshake adds only a print AFTER the real resource-limit calls;
        # main(), prctl and the guarded input read are production code. /proc
        # cannot identify virtual PIDs in every test container, so use pipes.
        child_code = """
import resource
original_limit = resource.setrlimit
def observed_limit(kind, limits):
    original_limit(kind, limits)
    if kind == resource.RLIMIT_CORE:
        print('GUARDED', flush=True)
resource.setrlimit = observed_limit
from genius_twin.process_runner import main
main()
"""
        parent_code = f"""
import os, signal, subprocess, sys
child = subprocess.Popen([sys.executable, '-c', {child_code!r}, '--child',
    '--parent', str(os.getpid()), '--seconds', '30', '--memory', '128', '--output', '1048576'],
    stderr=subprocess.DEVNULL)
signal.pause()
"""
        read_fd, write_fd = os.pipe()
        parent = subprocess.Popen([sys.executable, "-c", parent_code], stdin=read_fd,
                                  stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        os.close(read_fd)
        try:
            ready, _, _ = select.select([parent.stdout], [], [], 5)
            self.assertTrue(ready, "Compiler child did not reach guarded input read")
            self.assertEqual(parent.stdout.readline(), b"GUARDED\n")
            parent.kill()
            parent.wait(timeout=5)
            # The test process keeps the stdin writer OPEN. Without parent
            # death enforcement, the child would remain blocked and retain
            # stdout, so EOF here cannot be explained by loss of stdin.
            ready, _, _ = select.select([parent.stdout], [], [], 5)
            self.assertTrue(ready, "Killed web parent left the guarded compiler alive")
            self.assertEqual(parent.stdout.read(1), b"", "Compiler stdout did not close")
        finally:
            # Even a failing guard cannot leave an orphan waiting for input:
            # close the grandparent writer and the real parser exits on EOF.
            os.close(write_fd)
            if parent.poll() is None:
                parent.kill()
                parent.wait(timeout=5)
            if parent.stdout:
                parent.stdout.close()


if __name__ == "__main__":
    unittest.main()
