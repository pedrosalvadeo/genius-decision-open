"""Module VII under a decision window (AM-05): evaluate scenario by scenario, report exact bounds.

When the full evaluation does not fit a decider's window, each scenario is
evaluated as its own model (law {s: "1/1"}, or null when the law is null) and
verified by the kernel. Scenarios run by decreasing law mass; ties follow an
order the decider declares before computing, never one chosen from results.
After the evaluated set E:

- a route that fails the task in a scenario of E is refuted when the model
  requires every scenario; no missing scenario can rescue it;
- with a law and a life-conditions task, PVS(r) lies in
  [mass of successes in E, that + mass of undecided scenarios in E + 1 - m(E)];
- functions, CAG and wellbeing are reported for the evaluated scenarios only.

A route is selected only if the model allows a unique selection and a single
route remains unrefuted; the selection is conditional on the scenarios not yet
evaluated. Nothing missing is filled in.
"""
from copy import deepcopy
from fractions import Fraction
import time

from .stockflow import q, validate_model

FORMAT = "genius-anytime-evaluation/1"
AMENDMENT = "AM-05"


def order(model, tie_order=None):
    """Scenario ids in evaluation order, and the basis of that order."""
    ids = [s["id"] for s in model["scenarios"]]
    if tie_order is not None:
        if type(tie_order) is not list or sorted(tie_order) != sorted(ids):
            raise ValueError("tie_order must list every scenario id once")
        rank = {sid: i for i, sid in enumerate(tie_order)}
    else:
        rank = {sid: i for i, sid in enumerate(ids)}
    if model["law"] is None:
        return sorted(ids, key=rank.get), "DECLARED_ORDER_NULL_LAW" if tie_order else "MODEL_ORDER_NULL_LAW"
    return (sorted(ids, key=lambda sid: (-Fraction(model["law"][sid]), rank[sid])),
            "LAW_MASS_DESCENDING_TIES_" + ("DECLARED_ORDER" if tie_order else "MODEL_ORDER"))


def single(model, sid):
    """The model restricted to one scenario, with all its mass when the law is declared."""
    one = deepcopy(model)
    one["scenarios"] = [deepcopy(s) for s in model["scenarios"] if s["id"] == sid]
    one["law"] = None if model["law"] is None else {sid: "1/1"}
    one["name"] = f"{model['name']} (sólo el escenario {sid})"
    validate_model(one)
    return one


def evaluate(model, evaluate_model, budget_seconds, tie_order=None, clock=time.monotonic):
    """Evaluate scenarios one at a time until the window closes; exact bounds on what is known.

    evaluate_model: the bounded evaluator used for full evaluations.
    budget_seconds: the decider's window. The first scenario always runs; a
    later one starts only if the slowest run so far still fits.
    """
    validate_model(model)
    budget = Fraction(budget_seconds)
    if budget <= 0:
        raise ValueError("budget_seconds must be positive")
    sequence, basis = order(model, tie_order)
    life = model["task"]["kind"] == "life_conditions"
    law = None if model["law"] is None else {sid: Fraction(v) for sid, v in model["law"].items()}
    routes = {p["id"]: {"refuted_in": [], "by_scenario": {}} for p in model["policies"]}
    runs, started, slowest, stopped = [], clock(), Fraction(0), None
    for sid in sequence:
        elapsed = Fraction(clock() - started)
        if runs and elapsed + slowest > budget:
            stopped = "WINDOW_CLOSED"
            break
        t0 = clock()
        result = evaluate_model(single(model, sid))
        seconds = Fraction(clock() - t0)
        slowest = max(slowest, seconds)
        valid = result.get("verification", {}).get("valid") is True
        runs.append({"scenario": sid, "seconds": round(float(seconds), 3), "verification_valid": valid,
                     "native_input_digest": result.get("native_result", {}).get("input_digest")})
        if not valid:
            stopped = "UNVERIFIED_RUN"
            break
        for pid, policy in result["canonical_results"]["policies"].items():
            row = policy["by_scenario"][sid]
            routes[pid]["by_scenario"][sid] = {
                "task_status": row["task_status"], "pvs_given_scenario": row["pvs_given_scenario"],
                "wellbeing": row["wellbeing"], "functional": policy["functional"]["by_scenario"].get(sid),
                "cag_given_scenario": {"possible": policy["cag"]["possible"], "robust": policy["cag"]["robust"]}}
            if row["task_status"] == "failure":
                routes[pid]["refuted_in"].append(sid)
    evaluated = [run["scenario"] for run in runs if run["verification_valid"]]
    complete = len(evaluated) == len(sequence)
    mass = None if law is None else sum((law[s] for s in evaluated), Fraction())
    for pid, route in routes.items():
        statuses = {sid: route["by_scenario"][sid]["task_status"] for sid in evaluated}
        route["refuted"] = bool(route["refuted_in"]) and model["require_all_scenarios"]
        route["pvs_bounds"] = None
        if life and law is not None:
            low = sum((law[s] for s, st in statuses.items() if st == "success"), Fraction())
            open_mass = sum((law[s] for s, st in statuses.items() if st not in ("success", "failure")), Fraction()) + 1 - mass
            route["pvs_bounds"] = {"min": q(low), "max": q(low + open_mass), "exact": open_mass == 0}
        route["law_range"] = None
        if life and law is None and complete and all(st in ("success", "failure") for st in statuses.values()):
            values = [st == "success" for st in statuses.values()]
            route["law_range"] = {"min": q(Fraction(int(all(values)))), "max": q(Fraction(int(any(values))))}
    unrefuted = [pid for pid, route in routes.items() if not route["refuted"]]
    if model["selection"] == "unique" and model["require_all_scenarios"] and len(unrefuted) == 1:
        selected = unrefuted[0]
        status = "ONLY_FEASIBLE_ROUTE" if complete else "CONDITIONAL_ON_UNEVALUATED_SCENARIOS"
    else:
        selected = None
        status = ("NO_SELECTION_BY_MODEL_RULE" if model["selection"] != "unique" else
                  "NO_SELECTION_FULL_EVALUATION_NEEDED_FOR_FRONTIER" if complete else "NO_SELECTION_WITHIN_WINDOW")
    pending = [sid for sid in sequence if sid not in evaluated]
    if law is not None:
        label = f"{len(evaluated)} de {len(sequence)} escenarios evaluados (masa {q(mass)})"
    else:
        label = f"{len(evaluated)} de {len(sequence)} escenarios evaluados (ley nula)"
    return {"format": FORMAT, "amendment": AMENDMENT,
            "status": "COMPLETE_BY_SCENARIO" if complete else (stopped or "WINDOW_CLOSED"),
            "budget_seconds": q(budget), "elapsed_seconds": round(float(Fraction(clock() - started)), 3),
            "order": sequence, "order_basis": basis, "evaluated": evaluated, "not_evaluated": pending,
            "evaluated_mass": None if mass is None else q(mass), "label": label,
            "routes": routes, "unrefuted": unrefuted, "selected": selected, "selection_status": status,
            "runs": runs,
            "assumptions": ["each scenario run is verified by the kernel on its own; the bounds combine them with exact arithmetic outside the FP1 verifier",
                            "the tie order was declared before computing" if tie_order else "ties follow the model's scenario order"],
            "meaning": "Bounds, not estimates: nothing about the scenarios not evaluated is inferred. "
                       "Functions, CAG and wellbeing hold only for the scenarios evaluated."}
