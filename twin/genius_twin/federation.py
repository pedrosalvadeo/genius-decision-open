"""Twin of twins: compose evaluated twins into a larger system (GENIUS_FEDERATION_V1).

FP1 does not transport between two models (spec 02 §2.4), so the federation
never merges models into one instance. Every member twin is evaluated and
verified by the kernel on its own, with the joint scenarios renamed into it.
A coupling carries what one member's interface moves, step by step, into a
stock of another member as an extra drain (or inflow); the target is then
re-evaluated once per combination of its sources' routes. The joint layer
only reads member results: joint life condition per scenario, joint PVS,
welfare and functions per carrier, and a product-order frontier over joint
routes. Shared carriers keep one identity across members.
"""
from copy import deepcopy
from fractions import Fraction
from itertools import product
import json
from pathlib import Path

from . import construction, registry
from .stockflow import _shape, interface_flows, q

FORMAT = "genius-federation/1"
CASES = Path(__file__).resolve().parents[1] / "cases"
RESULT = "federation_result.json"


def schema():
    ident = {"type": "string", "pattern": r"^[A-Za-z][A-Za-z0-9_.-]*$", "maxLength": 64}
    txt = {"type": "string", "minLength": 1, "maxLength": 2000}
    qty = {"type": "string", "pattern": r"^-?(0|[1-9][0-9]*)/[1-9][0-9]*$", "maxLength": 25}
    def obj(props):
        return {"type": "object", "properties": props, "required": list(props), "additionalProperties": False}
    def arr(item, lo, hi):
        return {"type": "array", "items": item, "minItems": lo, "maxItems": hi}
    mapping = {"type": "object", "additionalProperties": ident, "minProperties": 1, "maxProperties": 4}
    return obj({
        "format": {"type": "string", "enum": [FORMAT]}, "name": txt,
        "members": arr(obj({"id": ident, "label": txt, "case": ident}), 2, 4),
        "scenarios": arr(obj({"id": ident, "label": txt, "members": mapping}), 1, 8),
        "law": {"oneOf": [{"type": "null"}, {"type": "object", "additionalProperties": qty, "minProperties": 1, "maxProperties": 8}]},
        "couplings": arr(obj({"id": ident, "label": txt,
            "source": obj({"member": ident, "interface": ident}), "target": obj({"member": ident, "stock": ident}),
            "factor": qty, "lag": {"type": "integer", "minimum": 0, "maximum": 6}, "provenance": txt}), 0, 6),
        "shared_carriers": arr(obj({"id": ident, "label": txt, "members": mapping}), 0, 8),
        "assumptions": arr(obj({"id": ident, "statement": txt, "provenance": txt}), 1, 12),
    })


def load_case(case):
    world = json.loads((CASES / case / "world.json").read_text())
    prepared = construction.prepare(world["construction"], dict(id="observation", revision=1,
                                    observation=world["observation"], historical_gaps={}))
    if prepared["status"] != "READY_FOR_REVIEW":
        raise ValueError(f"case {case} is not ready: {prepared['status']}")
    return prepared["model"]


def validate(spec, models):
    _shape(spec, schema(), "federation")
    members = {m["id"] for m in spec["members"]}
    if len(members) != len(spec["members"]):
        raise ValueError("duplicate member")
    for scenario in spec["scenarios"]:
        if set(scenario["members"]) != members:
            raise ValueError("each joint scenario must name one scenario of every member")
        for mid, sid in scenario["members"].items():
            if sid not in {s["id"] for s in models[mid]["scenarios"]}:
                raise ValueError(f"unknown scenario {sid} of {mid}")
    for mid in members:
        chosen = [s["members"][mid] for s in spec["scenarios"]]
        if len(set(chosen)) != len(chosen):
            # Two joint scenarios with one member scenario would repeat a complete event word.
            raise ValueError("joint scenarios must map to distinct scenarios of each member")
    ids = [s["id"] for s in spec["scenarios"]]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate joint scenario")
    law = spec["law"]
    if law is not None and (set(law) != set(ids) or any(Fraction(v) < 0 for v in law.values())
                            or sum(map(Fraction, law.values()), Fraction()) != 1):
        raise ValueError("law must cover every joint scenario and sum exactly to one")
    sources = {c["source"]["member"] for c in spec["couplings"]}
    for c in spec["couplings"]:
        src, tgt = c["source"]["member"], c["target"]["member"]
        if src not in members or tgt not in members or src == tgt:
            raise ValueError("coupling joins two different members")
        if tgt in sources:
            raise ValueError("a coupling target cannot also be a source (one level of couplings)")
        if c["source"]["interface"] not in {x["id"] for x in models[src].get("interfaces", [])}:
            raise ValueError(f"unknown interface {c['source']['interface']} of {src}")
        if c["target"]["stock"] not in {s["id"] for s in models[tgt]["stocks"]}:
            raise ValueError(f"unknown stock {c['target']['stock']} of {tgt}")
    for shared in spec["shared_carriers"]:
        for mid, cid in shared["members"].items():
            if mid not in members or cid not in {c["id"] for c in models[mid]["carriers"]}:
                raise ValueError(f"unknown shared carrier {cid} of {mid}")


def _member_model(model, spec, mid):
    """The member with the joint scenarios renamed into it and the joint law."""
    out = deepcopy(model)
    by_id = {s["id"]: s for s in model["scenarios"]}
    out["scenarios"] = [{"id": s["id"], "label": s["label"], "events": deepcopy(by_id[s["members"][mid]]["events"])} for s in spec["scenarios"]]
    out["law"] = deepcopy(spec["law"])
    return out


def _coupled(model, couplings, flows):
    """Add each coupling's step increments, lagged and scaled, to the target stock's events."""
    out = deepcopy(model)
    for c in couplings:
        stock, factor, lag = c["target"]["stock"], Fraction(c["factor"]), c["lag"]
        for scenario in out["scenarios"]:
            series = flows[c["id"]][scenario["id"]]
            for t in range(1, len(series)):
                step = t + lag
                amount = (series[t] - series[t - 1]) * factor
                if amount == 0 or step > out["horizon"]:
                    continue
                event = scenario["events"][step - 1]
                field = "drains" if amount > 0 else "inflows"
                event[field][stock] = q(Fraction(event[field].get(stock, "0/1")) + abs(amount))
    return out


def evaluate(spec):
    models = {m["id"]: load_case(m["case"]) for m in spec["members"]}
    validate(spec, models)
    members = [m["id"] for m in spec["members"]]
    joint_ids = [s["id"] for s in spec["scenarios"]]
    renamed = {mid: _member_model(models[mid], spec, mid) for mid in members}
    targets = {c["target"]["member"] for c in spec["couplings"]}
    routes = {mid: [p["id"] for p in renamed[mid]["policies"]] for mid in members}
    results, variants = {}, {}
    for mid in members:
        if mid not in targets:
            results[mid] = {(): registry.evaluate(renamed[mid])["canonical_results"]}
    for mid in sorted(targets):
        incoming = [c for c in spec["couplings"] if c["target"]["member"] == mid]
        sources = sorted({c["source"]["member"] for c in incoming})
        results[mid], variants[mid] = {}, {}
        for combo in product(*(routes[s] for s in sources)):
            chosen = dict(zip(sources, combo))
            flows = {}
            for c in incoming:
                src = c["source"]["member"]
                traces = results[src][()]["policies"][chosen[src]]["trajectories"]
                flows[c["id"]] = {sid: interface_flows(renamed[src], traces[sid]["daily"])[c["source"]["interface"]] for sid in joint_ids}
            model = _coupled(renamed[mid], incoming, flows)
            results[mid][combo] = registry.evaluate(model)["canonical_results"]
            variants[mid][combo] = {"sources": chosen, "coupled_totals": {c["id"]: {sid: q(flows[c["id"]][sid][-1] * Fraction(c["factor"]))
                                    for sid in joint_ids} for c in incoming}}
    def member_result(mid, joint):
        if mid not in targets:
            return results[mid][()]
        sources = sorted({c["source"]["member"] for c in spec["couplings"] if c["target"]["member"] == mid})
        return results[mid][tuple(joint[s] for s in sources)]
    shared = {(mid, cid): s["id"] for s in spec["shared_carriers"] for mid, cid in s["members"].items()}
    carrier_id = lambda mid, cid: shared.get((mid, cid), mid + "." + cid)
    law = spec["law"]
    joint_routes, rows = [], {}
    for combo in product(*(routes[m] for m in members)):
        joint = dict(zip(members, combo))
        jid = "+".join(f"{m}:{joint[m]}" for m in members)
        by_scenario, coords = {}, {}
        for sid in joint_ids:
            life = {}
            for mid in members:
                res = member_result(mid, joint)
                row = res["policies"][joint[mid]]["by_scenario"][sid]
                life[mid] = row["task_status"] if renamed[mid]["task"]["kind"] == "life_conditions" else None
                daily = res["policies"][joint[mid]]["trajectories"][sid]["daily"]
                for w in renamed[mid]["welfare"]:
                    sign = 1 if w["direction"] == "higher" else -1
                    for t, state in enumerate(daily):
                        coords[("welfare", carrier_id(mid, w["carrier"]), mid, w["dimension"], sid, t)] = sign * Fraction(state["stocks"][w["stock"]])
                for f in res["policies"][joint[mid]]["functional"]["by_scenario"][sid]:
                    coords[("function", mid, f["function"], sid)] = Fraction(f["terminal"])
            statuses = [v for v in life.values() if v is not None]
            # A failure in any member fails the joint life condition; otherwise an undecided one leaves it undecided.
            given = None if not statuses else 0 if "failure" in statuses else None if "undecided" in statuses else 1
            by_scenario[sid] = {"life_by_member": life, "joint_life_given_scenario": None if given is None else q(given)}
        values = [by_scenario[s]["joint_life_given_scenario"] for s in joint_ids]
        pvs = None if law is None or any(v is None for v in values) else q(sum(Fraction(law[s]) * Fraction(v) for s, v in zip(joint_ids, values)))
        known = [Fraction(v) for v in values if v is not None]
        law_range = None if len(known) != len(values) else {"min": q(min(known)), "max": q(max(known)), "law_invariant": min(known) == max(known)}
        if pvs is not None:
            coords[("pvs",)] = Fraction(pvs)
        joint_routes.append({"id": jid, "routes": joint})
        rows[jid] = {"routes": joint, "joint_pvs": pvs, "joint_pvs_law_range": law_range, "by_scenario": by_scenario,
                     "feasible": all(v == "1/1" for v in values), "_coords": coords}
    ids = [r["id"] for r in joint_routes]
    def relation(a, b):
        better, worse = set(), set()
        for key, x in rows[a]["_coords"].items():
            y = rows[b]["_coords"].get(key)
            if y is None:
                continue
            label = key[1] if key[0] == "welfare" else key[1] + "." + key[2] if key[0] == "function" else "pvs"
            if x > y:
                better.add((key[0], label))
            elif x < y:
                worse.add((key[0], label))
        kind = "EQUIVALENT" if not better and not worse else "DOMINATES" if not worse else "DOMINATED" if not better else "INCOMPARABLE"
        return {"left": a, "right": b, "relation": kind,
                "better_for": [{"criterion": k, "who": w} for k, w in sorted(better)],
                "worse_for": [{"criterion": k, "who": w} for k, w in sorted(worse)]}
    pairs = [relation(a, b) for i, a in enumerate(ids) for b in ids[i + 1:]]
    feasible = [i for i in ids if rows[i]["feasible"]]
    pool = feasible or ids
    dominated = {p["right"] for p in pairs if p["relation"] == "DOMINATES" and p["left"] in pool} | \
                {p["left"] for p in pairs if p["relation"] == "DOMINATED" and p["right"] in pool}
    frontier = [i for i in pool if i not in dominated]
    # Module VII per actor across the federation: a shared carrier is one actor.
    serves = {(mid, f["id"]): [carrier_id(mid, c) for c in f["serves"]] for mid in members for f in renamed[mid].get("functions", [])}
    actors = sorted({carrier_id(mid, c["id"]) for mid in members for c in renamed[mid]["carriers"]})
    def actor_keys(actor, row):
        return {k for k in row["_coords"] if (k[0] == "welfare" and k[1] == actor)
                or (k[0] == "function" and actor in serves.get((k[1], k[2]), []))}
    by_actor = {}
    for actor in actors:
        keys = actor_keys(actor, rows[pool[0]])
        if not keys:
            by_actor[actor] = {"best": None, "status": "NO_CRITERIA"}
            continue
        beaten = {b for a in pool for b in pool if a != b and all(rows[a]["_coords"][k] >= rows[b]["_coords"][k] for k in keys)
                  and any(rows[a]["_coords"][k] > rows[b]["_coords"][k] for k in keys)}
        best = [i for i in pool if i not in beaten]
        by_actor[actor] = {"best": best, "status": "UNIQUE" if len(best) == 1 else "TIED_OR_INCOMPARABLE"}
    for row in rows.values():
        del row["_coords"]
    member_ledgers = {}
    for mid in members:
        variant = next(iter(results[mid].values()))
        member_ledgers[mid] = {m["module"]: m["status"] for m in variant["modules"]["modules"]}
    return {
        "format": "genius-federation-result/1", "name": spec["name"],
        "scope": "EACH_MEMBER_KERNEL_VERIFIED_JOINT_LAYER_READS_MEMBER_RESULTS",
        "members": {mid: {"case": next(m["case"] for m in spec["members"] if m["id"] == mid), "routes": routes[mid],
                          "modules": member_ledgers[mid], "coupled_variants": [
                              {"key": list(k), **v} for k, v in variants.get(mid, {}).items()]} for mid in members},
        "joint_scenarios": deepcopy(spec["scenarios"]), "law": deepcopy(law), "couplings": deepcopy(spec["couplings"]),
        "shared_carriers": deepcopy(spec["shared_carriers"]), "joint_routes": joint_routes, "by_joint_route": rows,
        "decision": {"feasible": feasible, "frontier": frontier, "pairs": pairs, "by_actor": by_actor, "selected": frontier[0] if len(frontier) == 1 else None,
                     "rule": "PRODUCT_ORDER_OVER_MEMBER_WELFARE_STEPS_FUNCTION_TERMINALS_AND_JOINT_PVS_NO_SUMS",
                     "feasibility": "JOINT_LIFE_CONDITION_IN_EVERY_JOINT_SCENARIO"},
        "assumptions": deepcopy(spec["assumptions"]),
        "labels": {"members": {m["id"]: m["label"] for m in spec["members"]},
                   "routes": {mid: {p["id"]: p["label"] for p in renamed[mid]["policies"]} for mid in members},
                   "actors": {**{carrier_id(mid, c["id"]): c["label"] for mid in members for c in renamed[mid]["carriers"]},
                              **{s["id"]: s["label"] for s in spec["shared_carriers"]}}},
    }


def federations():
    """Federations kept in twin/cases, each with its frozen result (written by `main`, checked by the tests)."""
    rows = []
    for path in sorted(CASES.glob("*/federation.json")):
        spec = json.loads(path.read_text())
        rows.append({"id": path.parent.name, "title": spec["name"], "members": [m["case"] for m in spec["members"]],
                     "frozen_result": (path.parent / RESULT).exists()})
    return rows


def federation_case(name):
    if name not in {row["id"] for row in federations()}:
        raise KeyError(name)
    folder = CASES / name
    result = folder / RESULT
    return {"id": name, "spec": json.loads((folder / "federation.json").read_text()),
            "result": json.loads(result.read_text()) if result.exists() else None,
            "provenance": "CITED_FIELD_CASES_COMPOSED_WITH_DECLARED_COUPLINGS"}


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description="Evaluate a federation in twin/cases and freeze its result.")
    parser.add_argument("case")
    args = parser.parse_args(argv)
    result = evaluate(json.loads((CASES / args.case / "federation.json").read_text()))
    (CASES / args.case / RESULT).write_text(json.dumps(result, ensure_ascii=False, indent=1, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
