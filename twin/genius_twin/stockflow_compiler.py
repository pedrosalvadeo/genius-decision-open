"""Causal STOCK_FLOW_FINITE_V1 -> native FP1, with lossless verified runs.

An action in FP1 is an attempted atomic transaction. Failed execution is a
causal outcome, not an omitted branch. No kernel extensions or supplied results.
"""
from copy import deepcopy
from fractions import Fraction
import hashlib

from genius_kernel import evaluate, verify_result
from .stockflow import canonical_json, compute_trajectories, q, validate_model

COMPILER_VERSION = "GENIUS_STOCK_FLOW_FINITE_V1_COMPILER_1"


def _id(prefix, obj):
    return prefix + hashlib.sha256(canonical_json(obj).encode()).hexdigest()[:24]


def _query(policy, path):
    return {"policy": policy, "path": list(path)}


def compile_model(model, *, cag_mode="robust"):
    """Return (closed FP1 object, manifest); retain event-prefix information."""
    validate_model(model)
    if cag_mode not in ("robust", "possible"):
        raise ValueError("unsupported CAG mode")
    trajectories = compute_trajectories(model)
    H = model["horizon"]
    source = canonical_json(model)
    digest = hashlib.sha256(source.encode()).hexdigest()
    basis = [a["id"] for a in model["assumptions"]]
    events, words = {}, {}
    for scenario in model["scenarios"]:
        word = []
        for event in scenario["events"]:
            eid = _id("event_", event)
            events[eid] = deepcopy(event)
            word.append(eid)
        words[scenario["id"]] = tuple(word)
    signatures = {r["organization"]: r["capabilities"]
                  for traces in trajectories.values() for tr in traces.values() for r in tr["daily"]}
    value_ids = {s["id"]: {v: _id("quantity_", [s["unit"], v])
                 for traces in trajectories.values() for tr in traces.values()
                 for r in tr["daily"] for v in [r["stocks"][s["id"]]]} for s in model["stocks"]}
    d = {
        "format": "genius-fp1/1.0",
        "meta": {"id": "StockFlow_" + digest[:20] + "_" + cag_mode,
            "framework": "GeniusTwinD3", "model": "StockFlowFiniteV1", "context": "DeclaredAssumptions",
            "condition": "SharedInitial", "horizon": str(H), "specification": "GENIUS-SPEC-1.0.0",
            "theory_snapshot": "GENIUS-THEORY-2026-09-23-S2", "profile": "FP1_FINITE_EXACT", "claim_scope": "FORMAL_INSTANCE_ONLY"},
        "assumptions": deepcopy(model["assumptions"]),
        "initialization": {"history": "h0", "condition": "SharedInitial", "x0": "x0", "i0": "i0", "basis": basis},
        "model": {"states": ["x0"], "information": ["i0"], "actions": ["attempt_" + a["id"] for a in model["actions"]],
            "observations": sorted(events), "exogenous": sorted(events), "basis": basis, "information_basis": basis,
            "executable": [], "admissible": [], "transitions": [], "updates": []},
        "policies": [], "scenarios": [{"id": s["id"], "inputs": list(words[s["id"]])} for s in model["scenarios"]],
        # No undeclared functional scoring. Empty vectors are equal for every
        # policy; welfare conditions carry the declared quantitative order.
        "functional": {"indices": [], "measurements": [], "reduction": {"ids": ["neutral"], "rows": []}},
        "composition": {"ports": [{"id": "stock_" + s["id"], "values": sorted(set(value_ids[s["id"]].values())), "basis": basis}
                                   for s in model["stocks"]], "rows": [],
            "views": [{"id": "StockBalances", "columns": ["query"] + ["stock_" + s["id"] for s in model["stocks"]]}], "basis": basis},
        "resources": {"kinds": [{"id": s["id"], "unit": s["unit"]} for s in model["stocks"]],
            "demands": [{"id": "occupancy_" + s["id"], "resource": s["id"], "unit": s["unit"], "basis": basis} for s in model["stocks"]],
            "values": [], "basis": basis},
        "generative": {"native_ids": sorted(signatures), "common_ids": sorted(signatures),
            "meaning_atoms": ["empty_capability_set"] + ["cap_" + c["id"] for c in model["capabilities"]],
            "native_meaning": [], "common_meaning": [], "native_order": [], "common_order": [], "identity": [],
            "translation": [{"native": s, "common": s} for s in sorted(signatures)], "recipe": {"kind": "acc"}, "mode": cag_mode, "basis": basis},
        "welfare": {"carriers": [c["id"] for c in model["carriers"]],
            "dimensions": [{"id": dim, "basis": basis} for dim in sorted({w["dimension"] for w in model["welfare"]})],
            "existence": [], "applicability": [], "values": [], "basis": basis},
        "semantics": {"states": ["success", "failure", "undecided"], "references": [],
            "task": [{"state": "success", "value": "1"}, {"state": "failure", "value": "0"}],
            "protocol": "FP1_EXACT_ENUM_V1", "basis": basis},
        "law": {"rows": [], "basis": basis},
        "constraints": [{"id": "Capacity_" + s["id"], "kind": "resource_budget", "resource": s["id"], "bound": s["capacity"], "basis": basis} for s in model["stocks"]],
        "selection": {"mode": model["selection"]},
    }
    if model["require_all_scenarios"]:
        d["constraints"].append({"id": "SustainAllScenarios", "kind": "task_all", "scope": "LEAVES", "basis": basis})
    for sid, components in sorted(signatures.items()):
        for side in ("native", "common"):
            d["generative"][side + "_meaning"].append({"identity": sid, "atoms": ["cap_" + c for c in components] or ["empty_capability_set"]})
            d["generative"][side + "_order"].extend([[sid, other] for other, other_components in sorted(signatures.items()) if set(components) <= set(other_components)])
    for t in range(H + 1):
        d["welfare"]["existence"].extend({"t": str(t), "carrier": c["id"]} for c in model["carriers"])
        d["welfare"]["applicability"].extend({"t": str(t), "carrier": w["carrier"], "dimension": w["dimension"]} for w in model["welfare"])
    state_records, query_records, semantic_records = {}, [], []
    points, availability, transition_rows, updates = set(), {}, {}, {}
    information, states = {"i0"}, {"x0"}
    for policy in model["policies"]:
        pid = policy["id"]
        nodes = {}
        for sid, tr in trajectories[pid].items():
            history = []
            for t, row in enumerate(tr["daily"]):
                path = words[sid][:t]
                if t:
                    history.append([row["action_id"], words[sid][t - 1]])
                x = "x0" if t == 0 else _id("state_", history)
                info = "i0" if t == 0 else _id("info_", history)
                node = {"x": x, "i": info, "record": row}
                if path in nodes and nodes[path] != node:
                    raise ValueError("Nonanticipation violated: identical event/action history has unequal state")
                nodes[path] = node
        decisions = {}
        for path, node in sorted(nodes.items(), key=lambda item: (len(item[0]), item[0])):
            t, x, info, row = len(path), node["x"], node["i"], node["record"]
            query = _query(pid, path)
            if x in state_records and state_records[x] != row:
                raise RuntimeError("Shared causal state has inconsistent domain values")
            state_records[x] = deepcopy(row)
            states.add(x)
            information.add(info)
            query_records.append({"query": query, "state": x, "information": info, "step": t, "record": deepcopy(row)})
            if (t, x) not in points:
                points.add((t, x))
                d["functional"]["reduction"]["rows"].append({"t": str(t), "x": x, "reduced": "neutral"})
                d["generative"]["identity"].append({"t": str(t), "x": x, "native": row["organization"]})
            d["composition"]["rows"].append({"query": query, "values": [{"port": "stock_" + s["id"], "value": value_ids[s["id"]][row["stocks"][s["id"]]]} for s in model["stocks"]]})
            d["resources"]["values"].extend({"query": query, "demand": "occupancy_" + s["id"], "value": row["stocks"][s["id"]]} for s in model["stocks"])
            d["welfare"]["values"].extend({"query": query, "carrier": w["carrier"], "dimension": w["dimension"],
                "value": q(Fraction(row["stocks"][w["stock"]]) * (1 if w["direction"] == "higher" else -1))} for w in model["welfare"])
            if t == H:
                d["semantics"]["references"].append({"leaf": query, "states": [row["task_status"]]})
                semantic_records.append({"leaf": query, "violation_seen": row["violation_seen"], "indeterminate_seen": row["indeterminate_seen"], "meaning": row["task_status"]})
                continue
            children = {p[-1]: child for p, child in nodes.items() if len(p) == t + 1 and p[:-1] == path}
            chosen = {child["record"]["action_id"] for child in children.values()}
            if len(chosen) != 1:
                raise ValueError("Nonanticipation violated: current event selects action")
            action = "attempt_" + next(iter(chosen))
            decision = {"t": str(t), "i": info, "a": action}
            if (t, info) in decisions and decisions[t, info] != decision:
                raise ValueError("A policy has two decisions for identical information")
            decisions[t, info] = decision
            availability.setdefault((t, x), set()).add(action)
            outcomes = []
            for eid, child in sorted(children.items()):
                outcomes.append({"branch": eid, "u": eid, "next_x": child["x"], "y": eid})
                update = {"t": str(t), "i": info, "a": action, "y": eid, "next_i": child["i"]}
                key = (t, info, action, eid)
                if key in updates and updates[key] != update:
                    raise RuntimeError("Information update collision")
                updates[key] = update
            transition = {"t": str(t), "x": x, "a": action, "outcomes": outcomes}
            key = (t, x, action)
            if key in transition_rows and transition_rows[key] != transition:
                raise RuntimeError("Shared causal transition collision")
            transition_rows[key] = transition
            if model["law"] is not None:
                parent_mass = sum((Fraction(model["law"][s]) for s, word in words.items() if word[:t] == path), Fraction())
                if parent_mass > 0:
                    weights = [{"branch": eid, "mass": q(sum((Fraction(model["law"][s]) for s, word in words.items() if word[:t+1] == path + (eid,)), Fraction()) / parent_mass)} for eid in sorted(children)]
                    d["law"]["rows"].append({"query": query, "weights": weights})
        d["policies"].append({"id": pid, "decisions": list(decisions.values())})
    d["model"]["states"], d["model"]["information"] = sorted(states), sorted(information)
    d["model"]["transitions"], d["model"]["updates"] = list(transition_rows.values()), list(updates.values())
    for (t, x), actions in sorted(availability.items()):
        for table in ("executable", "admissible"):
            d["model"][table].append({"t": str(t), "x": x, "actions": sorted(actions)})
    manifest = {"compiler_version": COMPILER_VERSION, "source_model_digest": digest, "source_model_json": source,
        "profile": model["profile"], "horizon": H, "step_unit": model["step_unit"], "cag_recipe": "acc", "cag_mode": cag_mode,
        "scope": "CONDITIONAL_FORMAL_INSTANCE_UNDER_DECLARED_ASSUMPTIONS", "empirical_validation": "NOT_PERFORMED",
        "action_granularity": "ATTEMPT_ATOMIC_TRANSACTION_BEFORE_CURRENT_EVENT", "joint_law": deepcopy(model["law"]),
        "event": deepcopy(model["task"]), "signature_components": signatures,
        "event_payloads": events, "scenario_words": {k: list(v) for k, v in words.items()},
        "state_records": state_records, "query_records": query_records, "semantic_references": semantic_records,
        "composition_value_dictionary": value_ids,
        "functional_semantics": "EMPTY_NEUTRAL_VECTOR_NO_ADDITIONAL_FUNCTIONAL_ORDER",
        "resource_semantics": "One stock occupancy per resource per occurrence; capacity bound. Transition balance and once-only atomic withdrawals are separately checked by the compiler domain and retained in ledgers.",
        "welfare_bindings": deepcopy(model["welfare"]),
        "field_mapping": {"stocks": "/resources/values and /composition/rows", "organization": "/generative/identity",
            "task_status": "/semantics/references (persistent history)", "welfare": "/welfare/values", "law": "/law/rows (conditional prefix masses)"}}
    return d, manifest


def _value(cell):
    return deepcopy(cell.get("value")) if cell.get("state") == "DEFINED" else None


def evaluate_model(model):
    """Execute/verify both CAG modes; retain legitimate partial native outputs."""
    runs, manifests = {}, {}
    for mode in ("robust", "possible"):
        instance, manifest = compile_model(model, cag_mode=mode)
        text = canonical_json(instance)
        raw = text.encode("utf-8")
        result = evaluate(raw)
        verification = verify_result(raw, result)
        if verification.get("valid") is not True or result["execution"]["status"] != "COMPLETE" or result["presentation"] != "VALID":
            raise RuntimeError("Stock-flow native evaluation was not received: " + canonical_json({
                "verification": verification, "execution": result["execution"], "presentation": result["presentation"], "diagnostics": result["diagnostics"][:8]}))
        manifest["native_input_digest"] = result["input_digest"]
        manifests[mode] = manifest
        runs[mode] = {"native_input_json": text, "native_result": result,
            "native_result_json": canonical_json(result), "verification": verification}
    native = runs["robust"]["native_result"]
    robust = {p["policy"]: p for p in native["policies"]}
    possible = {p["policy"]: p for p in runs["possible"]["native_result"]["policies"]}
    trajectories = compute_trajectories(model)
    policies = {}
    for policy in model["policies"]:
        pid = policy["id"]
        r, p = robust[pid], possible[pid]
        partition = _value(r["probability"]["partition"])
        all_scenarios = None if partition is None else False if partition["negative"] else None if partition["undecided"] else True
        probability = {"value": _value(r["probability"]["pvs"]), "state": r["probability"]["pvs"]["state"],
            "masses": _value(r["probability"]["vector"]), "native_cell": deepcopy(r["probability"]["pvs"]),
            "masses_cell": deepcopy(r["probability"]["vector"]),
            "interpretation": "CONDITIONAL_DECLARED_LIFE_CONDITIONS_NOT_EMPIRICAL_SURVIVAL" if model["task"]["kind"] == "life_conditions" else "CONDITIONAL_OPERATIONAL_TASK_NOT_LIFE_PVS"}
        pvs = deepcopy(probability) if model["task"]["kind"] == "life_conditions" else {
            "value": None, "state": "NOT_APPLICABLE", "masses": None, "interpretation": "OPERATIONAL_TASK_USE_TASK_PROBABILITY"}
        endpoint = None
        if model["law"] is not None and all(tr["daily"][-1]["endpoint_conditions"] is not None for tr in trajectories[pid].values()):
            endpoint = q(sum((Fraction(model["law"][s]) for s, tr in trajectories[pid].items() if tr["daily"][-1]["endpoint_conditions"]), Fraction()))
        policies[pid] = {"policy_id": pid, "label": policy["label"], "trajectories": trajectories[pid],
            "wellbeing": {"representation": "CONDITIONS_PROFILE_NOT_GLOBAL_INDEX", "carriers": [c["id"] for c in model["carriers"]],
                "profile": _value(r["welfare"]["profile"]), "native_cell": deepcopy(r["welfare"]["profile"]), "bindings": deepcopy(model["welfare"])},
            "cag": {"recipe": "acc", "origin": _value(r["generative"]["origin"]),
                "possible": _value(p["generative"]["cag"]), "robust": _value(r["generative"]["cag"]),
                "additional_possible": _value(p["generative"]["additional"]), "additional_robust": _value(r["generative"]["additional"]),
                "native_cells": {"possible": deepcopy(p["generative"]["cag"]), "robust": deepcopy(r["generative"]["cag"])}},
            "pvs": pvs, "task_probability": probability,
            "viability": {"all_scenarios": all_scenarios, "partition": partition, "native_cell": deepcopy(r["probability"]["partition"])},
            "endpoint_probability": {"value": endpoint, "event": "declared_state_conditions_at_terminal_only", "origin": "EXACT_DOMAIN_DERIVATION_NOT_THE_TRAJECTORY_EVENT"}}
    decision_value = _value(native["decision"])
    if decision_value is not None:
        selection = decision_value["selection"]
        decision = {key: deepcopy(decision_value[key]) for key in ("coverage", "feasible", "failed", "unknown", "frontier", "pairs")}
        decision.update({"selected": _value(selection), "selection_status": selection["state"]})
    else:
        decision = {"coverage": None, "feasible": [], "failed": [], "unknown": [], "frontier": [], "pairs": [], "selected": None, "selection_status": native["decision"]["state"]}
    decision.update({"native_cell": deepcopy(native["decision"]), "selection_rule": model["selection"],
        "comparison_cag_mode": "robust", "require_all_scenarios": model["require_all_scenarios"],
        "functional_criterion": "NEUTRAL_EMPTY_PROFILE"})
    canonical = {"profile": model["profile"], "name": model["name"],
        "product_value_status": "CALCULATED_UNDER_DECLARED_ASSUMPTIONS" if native["integration"]["state"] == "DEFINED" else "PARTIAL_NATIVE_RESULTS_UNDER_DECLARED_ASSUMPTIONS",
        "empirical_admission": "DECLARED_ASSUMPTIONS_ONLY", "horizon": model["horizon"], "step_unit": model["step_unit"],
        "stocks": deepcopy(model["stocks"]), "carriers": deepcopy(model["carriers"]), "welfare": deepcopy(model["welfare"]),
        "task": deepcopy(model["task"]), "event": model["task"]["label"], "joint_law": deepcopy(model["law"]),
        "signature_components": manifests["robust"]["signature_components"], "policies": policies, "decision": decision,
        "native_integration": deepcopy(native["integration"])}
    return {"canonical_results": canonical, "native_input_json": runs["robust"]["native_input_json"],
        "native_result": native, "verification": runs["robust"]["verification"],
        "compilation_manifest": {**manifests["robust"], "native_runs": {mode: {"input_digest": runs[mode]["native_result"]["input_digest"], "cag_mode": mode} for mode in runs}},
        "native_runs": runs}
