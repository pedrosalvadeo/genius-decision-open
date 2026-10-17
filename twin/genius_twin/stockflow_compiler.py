"""Causal STOCK_FLOW_FINITE_V1 -> native FP1, with lossless verified runs.

An action in FP1 is an attempted atomic transaction. Failed execution is a
causal outcome, not an omitted branch. No kernel extensions or supplied results.
"""
from copy import deepcopy
from fractions import Fraction
import hashlib

from genius_kernel import evaluate, verify_result
from .modules import module_ledger
from .stockflow import canonical_json, compute_trajectories, function_values, interface_flows, q, validate_model

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
    functions = model.get("functions", [])
    raws = {pid: {sid: function_values(model, tr["daily"]) for sid, tr in traces.items()} for pid, traces in trajectories.items()}
    flows = {pid: {sid: interface_flows(model, tr["daily"]) for sid, tr in traces.items()} for pid, traces in trajectories.items()}
    interfaces, subsystems = model.get("interfaces", []), model.get("subsystems", [])
    flow_ids = {x["id"]: {v: _id("flow_", [x["id"], q(v)]) for per in flows.values() for vals in per.values() for v in vals[x["id"]]} for x in interfaces}
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
        # Module I: one index per declared function, measured at every reached
        # state of every projected twin. Without declared functions the empty
        # vector is equal for every policy and welfare carries the order.
        "functional": {"indices": [{"id": "fn_" + f["id"], "basis": basis, "calibration": [{"raw": q(v), "value": q(v)}
                for v in sorted({v for per in raws.values() for vals in per.values() for v in vals[f["id"]]})]} for f in functions],
            "measurements": [], "reduction": {"ids": [] if functions else ["neutral"], "rows": []}},
        # Module II: with subsystems, one view per subsystem (its stocks and the
        # interfaces it touches); the kernel checks they rejoin to the whole.
        "composition": {"ports": [{"id": "stock_" + s["id"], "values": sorted(set(value_ids[s["id"]].values())), "basis": basis}
                                   for s in model["stocks"]] + [{"id": "iface_" + x["id"], "values": sorted(set(flow_ids[x["id"]].values())), "basis": basis}
                                   for x in interfaces], "rows": [],
            "views": [{"id": "Subsystem_" + sub["id"], "columns": ["query"] + ["stock_" + k for k in sub["stocks"]]
                       + ["iface_" + x["id"] for x in interfaces if sub["id"] in (x["source"], x["target"])]} for sub in subsystems]
                     or [{"id": "StockBalances", "columns": ["query"] + ["stock_" + s["id"] for s in model["stocks"]]}], "basis": basis},
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
                node = {"x": x, "i": info, "record": row, "functions": {f: vals[t] for f, vals in raws[pid][sid].items()},
                        "flows": {f: vals[t] for f, vals in flows[pid][sid].items()}}
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
                reduced = "neutral"
                if functions:
                    # States with the same function profile share one reduced id: a sufficient reduction for Module I.
                    profile = [node["functions"][f["id"]] for f in functions]
                    reduced = _id("profile_", profile)
                    if reduced not in d["functional"]["reduction"]["ids"]:
                        d["functional"]["reduction"]["ids"].append(reduced)
                    d["functional"]["measurements"].extend({"t": str(t), "x": x, "index": "fn_" + f["id"], "raw": q(node["functions"][f["id"]])} for f in functions)
                d["functional"]["reduction"]["rows"].append({"t": str(t), "x": x, "reduced": reduced})
                d["generative"]["identity"].append({"t": str(t), "x": x, "native": row["organization"]})
            d["composition"]["rows"].append({"query": query, "values": [{"port": "stock_" + s["id"], "value": value_ids[s["id"]][row["stocks"][s["id"]]]} for s in model["stocks"]]
                + [{"port": "iface_" + f, "value": flow_ids[f][v]} for f, v in node["flows"].items()]})
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
    d["functional"]["reduction"]["ids"].sort()
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
        "composition_value_dictionary": value_ids, "interface_value_dictionary": {f: {q(v): i for v, i in ids.items()} for f, ids in flow_ids.items()},
        "subsystems": deepcopy(subsystems), "interfaces": deepcopy(interfaces),
        "functional_semantics": "DECLARED_FUNCTIONS_MEASURED_ON_EVERY_PROJECTED_TWIN" if functions else "EMPTY_NEUTRAL_VECTOR_NO_ADDITIONAL_FUNCTIONAL_ORDER",
        "function_definitions": deepcopy(functions),
        "resource_semantics": "One stock occupancy per resource per occurrence; capacity bound. Transition balance and once-only atomic withdrawals are separately checked by the compiler domain and retained in ledgers.",
        "welfare_bindings": deepcopy(model["welfare"]),
        "field_mapping": {"stocks": "/resources/values and /composition/rows", "organization": "/generative/identity",
            "task_status": "/semantics/references (persistent history)", "welfare": "/welfare/values", "law": "/law/rows (conditional prefix masses)",
            "functions": "/functional/indices, /functional/measurements and /functional/reduction"}}
    return d, manifest


def _value(cell):
    return deepcopy(cell.get("value")) if cell.get("state") == "DEFINED" else None


def _shortfall(model, trajectories):
    """How far and how long each scenario misses each task condition; a diagnostic, not wellbeing or PVS."""
    out = {}
    for sid, trajectory in trajectories.items():
        rows = []
        for condition in model["task"]["conditions"]:
            values = [state["stocks"].get(condition["stock"]) for state in trajectory["daily"]]
            if condition.get("threshold") is None or any(v is None for v in values):
                # An unknown threshold or stock is not coerced into a gap.
                rows.append({"stock": condition["stock"], "op": condition["op"], "threshold": condition.get("threshold"),
                             "steps_missed": None, "worst_gap": None, "first_missed_step": None})
                continue
            threshold = Fraction(condition["threshold"])
            gaps = [max(threshold - Fraction(v), Fraction()) if condition["op"] == "ge" else max(Fraction(v) - threshold, Fraction()) for v in values]
            rows.append({"stock": condition["stock"], "op": condition["op"], "threshold": q(threshold),
                         "steps_missed": sum(gap > 0 for gap in gaps), "worst_gap": q(max(gaps)),
                         "first_missed_step": next((i for i, gap in enumerate(gaps) if gap > 0), None)})
        failed = sum(1 for state in trajectory["daily"] if state.get("action_executed") is False)
        out[sid] = {"conditions": rows, "failed_actions": failed if model["task"].get("require_action_success") else None}
    return out


def _oriented(binding, value):
    return Fraction(value) * (1 if binding["direction"] == "higher" else -1)


def _by_scenario(model, trajectories):
    """Per scenario: whether the task holds, the PVS of the law concentrated on that scenario, and each welfare condition."""
    life = model["task"]["kind"] == "life_conditions"
    out = {}
    for sid, trajectory in trajectories.items():
        status = trajectory["daily"][-1]["task_status"]
        given = {"success": "1", "failure": "0"}.get(status)
        rows = []
        for w in model["welfare"]:
            values = [Fraction(state["stocks"][w["stock"]]) for state in trajectory["daily"]]
            worst = min(values) if w["direction"] == "higher" else max(values)
            rows.append({"carrier": w["carrier"], "dimension": w["dimension"], "stock": w["stock"], "direction": w["direction"],
                         "initial": q(values[0]), "final": q(values[-1]), "worst": q(worst)})
        out[sid] = {"task_status": status, "pvs_given_scenario": given if life else None,
                    "task_value_given_scenario": given, "wellbeing": rows}
    return out


def law_range(by_scenario, key):
    """Bounds of sum_s law(s) * value(s) over every law on the declared scenarios; None if any value is undefined."""
    values = [row[key] for row in by_scenario.values()]
    if not values or any(v is None for v in values):
        return None
    low, high = min(map(Fraction, values)), max(map(Fraction, values))
    return {"min": q(low), "max": q(high), "law_invariant": low == high}


def welfare_relation(model, left, right, scenarios):
    """FP1 product comparator restricted to `scenarios`: every (scenario, step, carrier, dimension) coordinate, no sums."""
    better, worse = set(), set()
    for sid in scenarios:
        for a, b in zip(left[sid]["daily"], right[sid]["daily"]):
            for w in model["welfare"]:
                x, y = _oriented(w, a["stocks"][w["stock"]]), _oriented(w, b["stocks"][w["stock"]])
                if x > y:
                    better.add((w["carrier"], w["dimension"]))
                elif x < y:
                    worse.add((w["carrier"], w["dimension"]))
    relation = ("EQUIVALENT" if not better and not worse else "DOMINATES" if not worse else
                "DOMINATED" if not better else "INCOMPARABLE")
    as_list = lambda pairs: [{"carrier": c, "dimension": d} for c, d in sorted(pairs)]
    return {"relation": relation, "better_for": as_list(better), "worse_for": as_list(worse)}


def welfare_comparison(model, trajectories):
    """Pairwise welfare relations per scenario and over all scenarios together."""
    ids = [p["id"] for p in model["policies"]]
    scenario_ids = [s["id"] for s in model["scenarios"]]
    def pairs(scope):
        return [{"left": a, "right": b, **welfare_relation(model, trajectories[a], trajectories[b], scope)}
                for i, a in enumerate(ids) for b in ids[i + 1:]]
    return {"by_scenario": {sid: pairs([sid]) for sid in scenario_ids}, "all_scenarios": pairs(scenario_ids),
            "rule": "FP1_PRODUCT_SAME_SCENARIO_STEP_CARRIER_DIMENSION_NO_SUMS"}


def _functions_by_scenario(model, raws):
    """Module I on each projected twin (this route in each scenario): every declared function over the horizon."""
    out = {}
    for sid, values in raws.items():
        rows = []
        for f in model.get("functions", []):
            series = values[f["id"]]
            held = [series[0] > 0] + [b > a for a, b in zip(series, series[1:])] if f["measure"] == "cumulative" else [v > 0 for v in series]
            rows.append({"function": f["id"], "serves": list(f["serves"]), "measure": f["measure"], "terminal": q(series[-1]),
                         "steps_held": sum(held), "steps": len(series), "first_unmet_step": next((i for i, h in enumerate(held) if not h), None)})
        out[sid] = rows
    return out


def functional_comparison(model, raws):
    """Pairwise product order on terminal function values, per scenario and over all scenarios; no sums."""
    ids = [p["id"] for p in model["policies"]]
    scenario_ids = [s["id"] for s in model["scenarios"]]
    functions = [f["id"] for f in model.get("functions", [])]
    def relation(a, b, scope):
        better, worse = set(), set()
        for sid in scope:
            for f in functions:
                x, y = raws[a][sid][f][-1], raws[b][sid][f][-1]
                if x > y:
                    better.add(f)
                elif x < y:
                    worse.add(f)
        kind = ("EQUIVALENT" if not better and not worse else "DOMINATES" if not worse else
                "DOMINATED" if not better else "INCOMPARABLE")
        return {"left": a, "right": b, "relation": kind, "better_on": sorted(better), "worse_on": sorted(worse)}
    def pairs(scope):
        return [relation(a, b, scope) for i, a in enumerate(ids) for b in ids[i + 1:]]
    return {"by_scenario": {sid: pairs([sid]) for sid in scenario_ids}, "all_scenarios": pairs(scenario_ids),
            "rule": "FP1_PRODUCT_ON_TERMINAL_FUNCTION_VALUES_SAME_SCENARIO_NO_SUMS"}


def shortfall_order(shortfalls):
    """Pairs (a, b) where a misses no condition by more, nor for more steps, than b in any scenario.

    The order holds under every law, so it can separate policies that a binary task ties."""
    def key(policy):
        out = []
        for sid in sorted(shortfalls[policy]):
            scenario = shortfalls[policy][sid]
            if any(row["worst_gap"] is None for row in scenario["conditions"]):
                return None
            out += [(Fraction(row["worst_gap"]), row["steps_missed"]) for row in scenario["conditions"]]
            if scenario["failed_actions"] is not None:
                out.append((Fraction(scenario["failed_actions"]), scenario["failed_actions"]))
        return out
    keys = {policy: key(policy) for policy in shortfalls}
    known = [policy for policy in shortfalls if keys[policy] is not None]
    pairs = []
    for a in known:
        for b in known:
            if a != b and all(x[0] <= y[0] and x[1] <= y[1] for x, y in zip(keys[a], keys[b])) and keys[a] != keys[b]:
                pairs.append([a, b])
    return sorted(pairs)


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
    raws = {pid: {sid: function_values(model, tr["daily"]) for sid, tr in traces.items()} for pid, traces in trajectories.items()}
    flows_by_policy = {pid: {sid: interface_flows(model, tr["daily"]) for sid, tr in traces.items()} for pid, traces in trajectories.items()}
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
            "endpoint_probability": {"value": endpoint, "event": "declared_state_conditions_at_terminal_only", "origin": "EXACT_DOMAIN_DERIVATION_NOT_THE_TRAJECTORY_EVENT"},
            "shortfall": {"by_scenario": _shortfall(model, trajectories[pid]), "interpretation": "SEVERITY_DIAGNOSTIC_NOT_WELLBEING_OR_PVS"},
            "by_scenario": _by_scenario(model, trajectories[pid]),
            "functional": {"functions": [f["id"] for f in model.get("functions", [])], "terminal": _value(r["functional"]["terminal"]),
                "native_cell": deepcopy(r["functional"]["terminal"]), "by_scenario": _functions_by_scenario(model, raws[pid])},
            "composition": {"subsystems": [x["id"] for x in model.get("subsystems", [])], "native_cell_state": r["composition"]["state"],
                "interfaces_by_scenario": {sid: [{"interface": x["id"], "source": x["source"], "target": x["target"],
                    "total": q(vals[x["id"]][-1])} for x in model.get("interfaces", [])] for sid, vals in flows_by_policy[pid].items()}}}
        policies[pid]["pvs"]["law_range"] = law_range(policies[pid]["by_scenario"], "pvs_given_scenario")
        policies[pid]["task_probability"]["law_range"] = law_range(policies[pid]["by_scenario"], "task_value_given_scenario")
    decision_value = _value(native["decision"])
    if decision_value is not None:
        selection = decision_value["selection"]
        decision = {key: deepcopy(decision_value[key]) for key in ("coverage", "feasible", "failed", "unknown", "frontier", "pairs")}
        decision.update({"selected": _value(selection), "selection_status": selection["state"]})
    else:
        decision = {"coverage": None, "feasible": [], "failed": [], "unknown": [], "frontier": [], "pairs": [], "selected": None, "selection_status": native["decision"]["state"]}
    decision["wellbeing_comparison"] = welfare_comparison(model, trajectories)
    decision["functional_comparison"] = functional_comparison(model, raws)
    decision["shortfall_order"] = {"strictly_less_severe": shortfall_order({pid: policies[pid]["shortfall"]["by_scenario"] for pid in policies}),
        "interpretation": "HOLDS_UNDER_EVERY_LAW_DIAGNOSTIC_NOT_SELECTION"}
    decision.update({"native_cell": deepcopy(native["decision"]), "selection_rule": model["selection"],
        "comparison_cag_mode": "robust", "require_all_scenarios": model["require_all_scenarios"],
        "functional_criterion": "DECLARED_FUNCTIONS_TERMINAL_PROFILE" if model.get("functions") else "NEUTRAL_EMPTY_PROFILE"})
    canonical = {"profile": model["profile"], "name": model["name"],
        "product_value_status": "CALCULATED_UNDER_DECLARED_ASSUMPTIONS" if native["integration"]["state"] == "DEFINED" else "PARTIAL_NATIVE_RESULTS_UNDER_DECLARED_ASSUMPTIONS",
        "empirical_admission": "DECLARED_ASSUMPTIONS_ONLY", "horizon": model["horizon"], "step_unit": model["step_unit"],
        "stocks": deepcopy(model["stocks"]), "carriers": deepcopy(model["carriers"]), "welfare": deepcopy(model["welfare"]),
        "task": deepcopy(model["task"]), "event": model["task"]["label"], "joint_law": deepcopy(model["law"]),
        "functions": deepcopy(model.get("functions", [])),
        "subsystems": deepcopy(model.get("subsystems", [])), "interfaces": deepcopy(model.get("interfaces", [])),
        "signature_components": manifests["robust"]["signature_components"], "policies": policies, "decision": decision,
        "native_integration": deepcopy(native["integration"])}
    canonical["modules"] = module_ledger(model, canonical, trajectories)
    return {"canonical_results": canonical, "native_input_json": runs["robust"]["native_input_json"],
        "native_result": native, "verification": runs["robust"]["verification"],
        "compilation_manifest": {**manifests["robust"], "native_runs": {mode: {"input_digest": runs[mode]["native_result"]["input_digest"], "cag_mode": mode} for mode in runs}},
        "native_runs": runs}
