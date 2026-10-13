"""Compile generated daily trajectories to closed FP1; execute the real kernel.

The kernel calculates CAG, historical welfare comparisons, exact probability,
feasibility and the integrated frontier. Native input bytes and Result objects
are retained for independent replay, including the second CAG modality.
"""
from copy import deepcopy
from fractions import Fraction
import hashlib
import json

from genius_kernel import evaluate, verify_result
from .domain import SCENARIOS, SIGNATURES, compute_trajectories, validate_model

COMPILER_VERSION = "GENIUS_TWIN_D1_COMPILER_1"


def _json(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _q(number):
    n = Fraction(number)
    return f"{n.numerator}/{n.denominator}"


def _query(policy, path):
    return {"policy": policy, "path": list(path)}


def _path(scenario, day):
    return tuple(["step"] * min(day, 9) + ([scenario] + ["step"] * (day - 10)
                                                   if day >= 10 else []))


def compile_model(model, *, cag_mode="robust"):
    """Return (native input object, manifest), without executing or mutating input.

    Daily macro routines are selected before the day's event. Their declared
    conditional observation-and-response semantics lives in the causal row.
    Scenario branching occurs only in the day-10 transition. Policy decisions
    never read a future scenario; histories are shared before that transition.
    """
    validate_model(model)
    if cag_mode not in ("robust", "possible"):
        raise ValueError("CAG mode must be robust or possible")
    trajectories = compute_trajectories(model)
    model_json = _json(model)
    model_digest = hashlib.sha256(model_json.encode()).hexdigest()
    assumptions = [
        ("Synthetic", "SYNTHETIC", "Bounded 14-day illustrative model; no empirical survival claims."),
        ("Dynamics", "MODEL", "Daily committed routines, discrete water balance and persistent violation monitor defined by the D1 domain contract."),
        ("Information", "INFORMATION", "Policies commit daily routines without future information. Conditional sensor-and-attendance responses are internal to each routine's causal macro transition; the joint event is revealed during day 10."),
        ("Initial", "INITIALIZATION", "Two living plants, 2 L in the tray and one additional shared 18 L supply; two operators with 60 minutes per day."),
        ("Organizational", "SEMANTIC", "q0/q1/q2 are declared organizational signatures; conservation is component inclusion, independent of daily hydration."),
        ("Welfare", "CALIBRATION", "Fixed carrier-by-day conditions: minutes available for A/B and tray hydration for P1/P2, larger is better within each dimension; no scalar wellbeing index."),
        ("LifeTask", "SEMANTIC", "Plants are stipulated living. Success requires all declared daily states to retain living P1/P2 and water margin at least 1 L; terminal recovery does not erase violation."),
        ("JointLaw", "PROBABILITY", "Explicit synthetic joint event distribution over N/H/HA; no independence or empirical calibration is asserted."),
        ("Norm", "NORMATIVE", "Budgets apply to every occurrence. Universal trajectory task is a separate explicit optional constraint. Select only an exhaustive singleton frontier."),
    ]
    d = {
        "format": "genius-fp1/1.0",
        "meta": {"id": "Twin_" + model_digest[:20] + "_" + cag_mode,
                 "framework": "GeniusTwinD1", "model": "Semillero14D",
                 "context": "SyntheticGarden", "condition": "SharedInitial",
                 "horizon": "14", "specification": "GENIUS-SPEC-1.0.0",
                 "theory_snapshot": "GENIUS-THEORY-2026-09-23-S2",
                 "profile": "FP1_FINITE_EXACT", "claim_scope": "FORMAL_INSTANCE_ONLY"},
        "assumptions": [{"id": i, "kind": k, "statement": s,
                         "provenance": "D1 declared synthetic domain contract"}
                        for i, k, s in assumptions],
        "initialization": {"history": "h0", "condition": "SharedInitial", "x0": "x0",
                           "i0": "i_before", "basis": ["Initial", "Synthetic"]},
        "model": {"states": ["x0"], "information": ["i_before"] + ["i_" + s for s in SCENARIOS],
                  "actions": ["routine_" + p for p in model["policies"]],
                  "observations": ["tick"] + ["event_" + s for s in SCENARIOS],
                  "exogenous": ["tick"] + ["joint_" + s for s in SCENARIOS],
                  "basis": ["Dynamics", "Synthetic"], "information_basis": ["Information"],
                  "executable": [], "admissible": [], "transitions": [], "updates": []},
        "policies": [],
        "scenarios": [{"id": s, "inputs": ["tick"] * 9 + ["joint_" + s] + ["tick"] * 4}
                      for s in SCENARIOS],
        "functional": {"indices": [{"id": "hydration", "calibration": [
                           {"raw": _q(v), "value": _q(v)} for v in (0, 1, 2)],
                           "basis": ["Welfare"]}], "measurements": [],
                       "reduction": {"ids": [], "rows": []}},
        "composition": {"ports": [{"id": "water_stock", "values": ["L" + str(v) for v in range(19)],
                                     "basis": ["Initial", "Dynamics"]}],
                        "rows": [], "views": [{"id": "WaterView", "columns": ["query", "water_stock"]}],
                        "basis": ["Dynamics"]},
        "resources": {"kinds": [{"id": "water", "unit": "L"},
                                {"id": "time_a", "unit": "minute"},
                                {"id": "time_b", "unit": "minute"}],
                      "demands": [{"id": i, "resource": r, "unit": u, "basis": ["Dynamics"]}
                                  for i, r, u in [("water_used", "water", "L"),
                                                   ("task_a", "time_a", "minute"),
                                                   ("task_b", "time_b", "minute")]],
                      "values": [], "basis": ["Initial", "Dynamics"]},
        "generative": {"native_ids": list(SIGNATURES), "common_ids": list(SIGNATURES),
                       "meaning_atoms": sorted(set().union(*map(set, SIGNATURES.values()))),
                       "native_meaning": [], "common_meaning": [], "native_order": [], "common_order": [],
                       "identity": [], "translation": [{"native": q, "common": q} for q in SIGNATURES],
                       "recipe": {"kind": "acc"}, "mode": cag_mode, "basis": ["Organizational"]},
        "welfare": {"carriers": ["A", "B", "P1", "P2"], "dimensions": [
                        {"id": "time_available", "basis": ["Welfare"]},
                        {"id": "hydration", "basis": ["Welfare"]}],
                    "existence": [], "applicability": [], "values": [], "basis": ["Welfare", "Initial"]},
        "semantics": {"states": ["safe_trajectory", "violated_trajectory"],
                      "references": [], "task": [{"state": "safe_trajectory", "value": "1"},
                                                  {"state": "violated_trajectory", "value": "0"}],
                      "protocol": "FP1_EXACT_ENUM_V1", "basis": ["LifeTask", "Dynamics"]},
        "law": {"rows": [], "basis": ["JointLaw"]},
        "constraints": [{"id": "Budget_" + r, "kind": "resource_budget", "resource": r,
                         "bound": _q(b), "basis": ["Norm", "Initial"]}
                        for r, b in [("water", 18), ("time_a", 60), ("time_b", 60)]],
        "selection": {"mode": "unique"},
    }
    if model["require_all_scenarios"]:
        d["constraints"].append({"id": "SustainAllScenarios", "kind": "task_all",
                                 "scope": "LEAVES", "basis": ["Norm", "LifeTask"]})
    for q, atoms in SIGNATURES.items():
        for side in ("native", "common"):
            d["generative"][side + "_meaning"].append({"identity": q, "atoms": list(atoms)})
            d["generative"][side + "_order"].extend(
                [[q, r] for r, other in SIGNATURES.items() if set(atoms) <= set(other)])
    for t in range(15):
        for carrier in d["welfare"]["carriers"]:
            dim = "time_available" if carrier in ("A", "B") else "hydration"
            d["welfare"]["existence"].append({"t": str(t), "carrier": carrier})
            d["welfare"]["applicability"].append({"t": str(t), "carrier": carrier, "dimension": dim})

    state_records, query_records, semantic_records = {}, [], []
    points_seen, availability, update_rows = set(), {}, {}
    for policy in model["policies"]:
        action = "routine_" + policy
        nodes = {}
        for scenario in SCENARIOS:
            for day, row in enumerate(trajectories[policy][scenario]["daily"]):
                path = _path(scenario, day)
                if path in nodes and nodes[path]["record"] != row:
                    raise ValueError("Nonanticipation violation: a shared past depends on a future event")
                x = "x0" if not path else "x_" + policy + "_" + "_".join(path)
                info = "i_before" if day < 10 else "i_" + scenario
                nodes[path] = {"x": x, "i": info, "record": row}
        decisions = {}
        for path, node in sorted(nodes.items(), key=lambda item: (len(item[0]), item[0])):
            day, x, info, row = len(path), node["x"], node["i"], node["record"]
            query = _query(policy, path)
            state_records[x] = deepcopy(row)
            query_records.append({"query": query, "state": x, "day": day,
                                  "domain_policy": policy, "record": deepcopy(row)})
            if x not in d["model"]["states"]:
                d["model"]["states"].append(x)
            point = (day, x)
            if point not in points_seen:
                points_seen.add(point)
                d["functional"]["measurements"].append({"t": str(day), "x": x,
                            "index": "hydration", "raw": _q(row["water_in_tray_liters"])})
                red = "red_" + x
                d["functional"]["reduction"]["ids"].append(red)
                d["functional"]["reduction"]["rows"].append({"t": str(day), "x": x, "reduced": red})
                d["generative"]["identity"].append({"t": str(day), "x": x, "native": row["organization"]})
            d["composition"]["rows"].append({"query": query, "values": [
                {"port": "water_stock", "value": "L" + str(row["water_remaining_liters"])}]})
            for demand, field in [("water_used", "water_used_liters"), ("task_a", "minutes_a"), ("task_b", "minutes_b")]:
                d["resources"]["values"].append({"query": query, "demand": demand, "value": _q(row[field])})
            for carrier in d["welfare"]["carriers"]:
                dim = "time_available" if carrier in ("A", "B") else "hydration"
                field = "available_" + carrier.lower() + "_minutes" if carrier in ("A", "B") else "water_in_tray_liters"
                d["welfare"]["values"].append({"query": query, "carrier": carrier, "dimension": dim,
                                             "value": _q(row[field])})
            if day == 14:
                meaning = "violated_trajectory" if row["violation_seen"] or not all(row["plants_alive"].values()) else "safe_trajectory"
                d["semantics"]["references"].append({"leaf": query, "states": [meaning]})
                semantic_records.append({"leaf": query, "domain_monitor": row["violation_seen"],
                                         "domain_endpoint": row["water_in_tray_liters"], "meaning": meaning})
                continue
            decisions[day, info] = {"t": str(day), "i": info, "a": action}
            availability.setdefault((day, x), set()).add(action)
            branches = SCENARIOS if day == 9 else ("step",)
            outcomes, weights = [], []
            for branch in branches:
                child_path = path + (branch,)
                child = nodes[child_path]
                observation = "event_" + branch if day == 9 else "tick"
                outcomes.append({"branch": branch, "u": "joint_" + branch if day == 9 else "tick",
                                 "next_x": child["x"], "y": observation})
                weights.append({"branch": branch, "mass": model["law"][branch] if day == 9 else "1/1"})
                key = (day, info, action, observation)
                update_rows[key] = {"t": str(day), "i": info, "a": action, "y": observation,
                                    "next_i": child["i"]}
            d["model"]["transitions"].append({"t": str(day), "x": x, "a": action, "outcomes": outcomes})
            d["law"]["rows"].append({"query": query, "weights": weights})
        d["policies"].append({"id": policy, "decisions": list(decisions.values())})
    for (day, x), actions in availability.items():
        for table in ("executable", "admissible"):
            d["model"][table].append({"t": str(day), "x": x, "actions": sorted(actions)})
    d["model"]["updates"] = list(update_rows.values())
    manifest = {"compiler_version": COMPILER_VERSION, "source_model_digest": model_digest,
                "source_model_json": model_json, "profile": model["profile"], "horizon": 14,
                "cag_recipe": "acc", "cag_mode": cag_mode,
                "scope": "SYNTHETIC_CONDITIONAL_FORMAL_INSTANCE",
                "empirical_validation": "NOT_PERFORMED",
                "action_granularity": "COMMITTED_DAILY_ROUTINE_WITH_INTERNAL_OBSERVATION_AND_RESPONSE",
                "branch_day": 10, "joint_law": deepcopy(model["law"]),
                "event": "living P1 and P2 and hydration >= 1 at every daily state 0..14",
                "signature_components": deepcopy(SIGNATURES),
                "state_records": state_records, "query_records": query_records,
                "semantic_references": semantic_records,
                "resource_semantics": {"water_used": "cumulative additional L; counted once per occurrence",
                                       "task_a": "minutes on this day", "task_b": "minutes on this day"},
                "field_mapping": {"water_in_tray_liters": "/functional/measurements and /welfare/values",
                                  "violation_seen": "/semantics/references via persistent history meaning",
                                  "organization": "/generative/identity",
                                  "available_a_minutes": "/welfare/values", "available_b_minutes": "/welfare/values",
                                  "law": "/law/rows at day-9 parent queries"}}
    return d, manifest


def _value(cell, name):
    if cell.get("state") != "DEFINED":
        raise RuntimeError(f"Required native {name} is not DEFINED; no successful product value emitted")
    return cell["value"]


def evaluate_model(model):
    """Execute and verify both native modalities; return a lossless envelope."""
    validate_model(model)
    runs, manifests = {}, {}
    for mode in ("robust", "possible"):
        instance, manifest = compile_model(model, cag_mode=mode)
        text = _json(instance)
        raw = text.encode("utf-8")
        result = evaluate(raw)
        verification = verify_result(raw, result)
        if (verification.get("valid") is not True or result["execution"]["status"] != "COMPLETE"
                or result["presentation"] != "VALID" or result["integration"]["state"] != "DEFINED"):
            raise RuntimeError("D1 compilation/evaluation was not received: " + _json({
                "verification": verification, "execution": result["execution"]["status"],
                "presentation": result["presentation"], "integration": result["integration"],
                "diagnostics": result["diagnostics"][:5]}))
        manifest["native_input_digest"] = result["input_digest"]
        manifests[mode] = manifest
        runs[mode] = {"native_input_json": text, "native_result": result,
                      "native_result_json": _json(result), "verification": verification}
    native = runs["robust"]["native_result"]
    robust = {p["policy"]: p for p in native["policies"]}
    possible = {p["policy"]: p for p in runs["possible"]["native_result"]["policies"]}
    trajectories = compute_trajectories(model)
    policies = {}
    for pid in model["policies"]:
        r, p = robust[pid], possible[pid]
        partition = _value(r["probability"]["partition"], "partition")
        endpoint_mass = sum(Fraction(model["law"][s]) for s in SCENARIOS
                            if trajectories[pid][s]["daily"][-1]["water_in_tray_liters"] >= 1)
        policies[pid] = {
            "policy_id": pid, "trajectories": trajectories[pid],
            "wellbeing": {"representation": "CONDITIONS_PROFILE_NOT_GLOBAL_INDEX",
                          "carriers": ["A", "B", "P1", "P2"],
                          "profile": _value(r["welfare"]["profile"], "welfare profile")},
            "cag": {"recipe": "acc", "origin": _value(r["generative"]["origin"], "origin"),
                    "possible": _value(p["generative"]["cag"], "possible CAG"),
                    "robust": _value(r["generative"]["cag"], "robust CAG"),
                    "additional_possible": _value(p["generative"]["additional"], "additional CAG"),
                    "additional_robust": _value(r["generative"]["additional"], "additional CAG")},
            "pvs": {"value": _value(r["probability"]["pvs"], "PVS"),
                    "masses": _value(r["probability"]["vector"], "mass vector"),
                    "interpretation": "CONDITIONAL_SYNTHETIC_TRAJECTORY_TASK_NOT_EMPIRICAL_SURVIVAL"},
            "viability": {"all_scenarios": not partition["negative"] and not partition["undecided"],
                          "partition": partition},
            "endpoint_probability": {"value": _q(endpoint_mass),
                                     "event": "hydration_at_day_14_at_least_1",
                                     "origin": "EXACT_DOMAIN_DERIVATION_NOT_THE_PVS_EVENT"},
        }
    decision = _value(native["decision"], "decision")
    selection = decision["selection"]
    canonical = {
        "profile": model["profile"], "product_value_status": "CALCULATED_UNDER_DECLARED_ASSUMPTIONS",
        "empirical_admission": "SYNTHETIC_ONLY", "horizon": 14, "policies": policies,
        "event": manifests["robust"]["event"], "joint_law": deepcopy(model["law"]),
        "decision": {"coverage": decision["coverage"], "feasible": decision["feasible"],
                     "failed": decision["failed"], "unknown": decision["unknown"],
                     "frontier": decision["frontier"], "pairs": decision["pairs"],
                     "selected": selection.get("value") if selection["state"] == "DEFINED" else None,
                     "selection_status": selection["state"], "selection_rule": "unique",
                     "comparison_cag_mode": "robust", "require_all_scenarios": model["require_all_scenarios"]},
    }
    return {"canonical_results": canonical,
            "native_input_json": runs["robust"]["native_input_json"],
            "native_result": native, "verification": runs["robust"]["verification"],
            "compilation_manifest": {**manifests["robust"], "native_runs": {
                mode: {"input_digest": runs[mode]["native_result"]["input_digest"],
                       "cag_mode": mode} for mode in runs}},
            "native_runs": runs}
