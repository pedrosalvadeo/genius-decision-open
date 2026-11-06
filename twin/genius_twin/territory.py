"""Territory: one declared model evaluated zone by zone, compared zone by zone (GENIUS_TERRITORY_V1, AM-06).

A map asks the same «¿y si…?» in many places at once: blocks, census tracts,
neighbourhoods. A single FP1 instance for the whole city grows past what can be
evaluated and packed; and a sum over zones would hide a zone that loses. So:

- every zone is its own stock-flow twin, built from one template by exact
  rational factors (`size`: the zone is that many template units; `supply`:
  what the zone has available of a stock, relative to its size). Each zone is
  evaluated and verified by the kernel on its own;
- every zone shares the template's routes, scenarios and law: a city route is
  the same route in every zone and a scenario (an ola de calor) hits every zone;
- a zone without data is declared `missing` and is never evaluated, filled or
  averaged: it stays «sin dato» and the city result is RELATIVE to the zones
  with data;
- the city order is the product of the zones' verified kernel orders (AM-06):
  route A is at least as good as route B for the city if and only if it is in
  every zone with data, criterion by criterion, and its joint PVS (below) is at
  least as high. Nothing is summed across zones,
  carriers or times; anonymous dominance (a zone may lose if another gains as
  much) is deliberately left out (decision of Pedro, 2026-11-06);
- life is read as one joint condition: in a scenario it holds for the city only
  if it holds in every zone, so the joint PVS is the probability that life holds
  everywhere at once. Wellbeing, generative capabilities and life stay separate.

Couplings between zones (water passing downstream) are not part of V1: each
zone's kernel order compares routes inside one instance, and a coupled zone
would need one instance per route. They need their own amendment.
"""
from copy import deepcopy
from fractions import Fraction
import hashlib
import json

from . import registry
from .stockflow import PROFILE, _shape, canonical_json, q

FORMAT = "genius-territory/1"
RESULT_FORMAT = "genius-territory-result/1"
MAX_ZONES = 128
CRITERIA = ("welfare", "cag", "pvs", "functional")


def schema():
    ident = {"type": "string", "pattern": r"^[A-Za-z][A-Za-z0-9_.-]*$", "maxLength": 64}
    txt = {"type": "string", "minLength": 1, "maxLength": 2000}
    qty = {"type": "string", "pattern": r"^(0|[1-9][0-9]*)/[1-9][0-9]*$", "maxLength": 25}
    def obj(props, optional=()):
        return {"type": "object", "properties": props, "required": [k for k in props if k not in optional],
                "additionalProperties": False}
    def arr(item, lo, hi):
        return {"type": "array", "items": item, "minItems": lo, "maxItems": hi}
    zone = obj({"id": ident, "label": txt, "size": qty,
                "supply": {"type": "object", "additionalProperties": qty, "maxProperties": 6},
                "missing": txt, "provenance": txt}, optional=("size", "supply", "missing"))
    return obj({
        "format": {"type": "string", "enum": [FORMAT]}, "name": txt,
        "template": {"type": "object"},
        "zones": arr(zone, 1, MAX_ZONES),
        "assumptions": arr(obj({"id": ident, "statement": txt, "provenance": txt}), 1, 12),
    })


def _scaled_pred(pred, size):
    if pred.get("kind") == "stock":
        return {**pred, "value": q(Fraction(pred["value"]) * size)}
    return pred


def zone_model(template, zone):
    """The template for one zone: every quantity times `size`; supply multiplies availability.

    `size` multiplies every quantity of every stock (initial, capacity, action withdrawals
    and deposits, events, predicates, task thresholds): the zone behaves like `size`
    template units side by side. `supply[s]` multiplies, on top of that, what the zone
    has available of stock s: its initial balance, renewals and external inflows, and the
    capacity of a renewable s. Demands (drains, action withdrawals) are not touched by
    supply. All factors are exact rationals; nothing is rounded.
    """
    size = Fraction(zone["size"])
    supply = {s: Fraction(v) for s, v in zone.get("supply", {}).items()}
    model = deepcopy(template)
    for stock in model["stocks"]:
        f = supply.get(stock["id"], Fraction(1))
        stock["initial"] = q(Fraction(stock["initial"]) * size * f)
        cap = Fraction(stock["capacity"]) * size
        if stock["kind"] == "renewable":
            cap *= f
        stock["capacity"] = q(cap)
    for action in model["actions"]:
        for field in ("withdrawals", "deposits"):
            action[field] = {s: q(Fraction(v) * size) for s, v in action[field].items()}
    for policy in model["policies"]:
        for rule in policy["rules"]:
            rule["when"] = [_scaled_pred(p, size) for p in rule["when"]]
    for capability in model["capabilities"]:
        if "holds_when" in capability:
            capability["holds_when"] = [_scaled_pred(p, size) for p in capability["holds_when"]]
    for scenario in model["scenarios"]:
        for event in scenario["events"]:
            for field in ("inflows", "renewables"):
                event[field] = {s: q(Fraction(v) * size * supply.get(s, Fraction(1))) for s, v in event[field].items()}
            event["drains"] = {s: q(Fraction(v) * size) for s, v in event["drains"].items()}
    for condition in model["task"]["conditions"]:
        if condition["threshold"] is not None:
            condition["threshold"] = q(Fraction(condition["threshold"]) * size)
    model["name"] = f"{template['name']} — {zone['label']}"
    return model


def validate(spec):
    _shape(spec, schema(), "territory")
    template = spec["template"]
    if template.get("profile") != PROFILE:
        raise ValueError("the template must be a STOCK_FLOW_FINITE_V1 model")
    for field in ("functions", "subsystems", "interfaces"):
        if template.get(field):
            raise ValueError(f"territory V1 does not scale template {field}; leave them out")
    registry.validate(template)
    stocks = {s["id"] for s in template["stocks"]}
    ids = [z["id"] for z in spec["zones"]]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate zone")
    for zone in spec["zones"]:
        if "missing" in zone:
            if "size" in zone or "supply" in zone:
                raise ValueError(f"zone {zone['id']}: a zone without data declares no size or supply")
            continue
        if "size" not in zone:
            raise ValueError(f"zone {zone['id']}: declare size, or missing with its reason")
        if Fraction(zone["size"]) <= 0:
            raise ValueError(f"zone {zone['id']}: size must be positive")
        unknown = set(zone.get("supply", {})) - stocks
        if unknown:
            raise ValueError(f"zone {zone['id']}: unknown supply stock " + ", ".join(sorted(unknown)))
        registry.validate(zone_model(template, zone))


def _and(values):
    """Kleene conjunction of '1'/'0'/None: a known 0 decides; otherwise an unknown stays unknown."""
    values = list(values)
    if "0" in values:
        return "0"
    if any(v is None for v in values):
        return None
    return "1"


def _digest(value):
    return hashlib.sha256(canonical_json(value).encode()).hexdigest()


def _zone_summary(model, envelope):
    canonical = envelope["canonical_results"]
    decision = canonical["decision"]
    routes = {}
    for pid, row in canonical["policies"].items():
        worst = {}
        for sid, by in row["by_scenario"].items():
            for w in by["wellbeing"]:
                key = f"{w['carrier']}.{w['dimension']}"
                worst.setdefault(key, {})[sid] = {"initial": w["initial"], "worst": w["worst"], "final": w["final"]}
        routes[pid] = {
            "task_status": {sid: by["task_status"] for sid, by in row["by_scenario"].items()},
            "pvs": row["pvs"].get("value"), "pvs_state": row["pvs"].get("state"),
            "all_scenarios": row["viability"].get("all_scenarios"),
            "additional_robust_capabilities": sorted({c for sig in row["cag"]["additional_robust"]
                                                      for c in canonical["signature_components"].get(sig, [])}),
            "wellbeing": worst,
        }
    pairs = {(p["left"], p["right"]): {c: p.get(c) for c in CRITERIA + ("weak", "strict")} for p in decision["pairs"]}
    return {
        "model_digest": _digest(model),
        "verification": envelope["verification"]["status"],
        "coverage": decision["coverage"],
        "feasible": sorted(decision["feasible"]), "failed": sorted(decision["failed"]), "unknown": sorted(decision["unknown"]),
        "frontier": sorted(decision["frontier"]),
        "routes": routes,
        "_pairs": pairs,
    }


def evaluate(spec):
    validate(spec)
    template = spec["template"]
    routes = [p["id"] for p in template["policies"]]
    scenarios = [s["id"] for s in template["scenarios"]]
    law = template["law"]
    zones, missing = {}, {}
    for zone in spec["zones"]:
        if "missing" in zone:
            missing[zone["id"]] = zone["missing"]
            continue
        model = zone_model(template, zone)
        zones[zone["id"]] = _zone_summary(model, registry.evaluate(model))
    with_data = list(zones)
    # Joint life: per scenario, it holds for the territory only if it holds in every zone with data.
    by_route = {}
    for r in routes:
        joint = {}
        for sid in scenarios:
            statuses = [zones[z]["routes"][r]["task_status"][sid] for z in with_data]
            joint[sid] = "failure" if "failure" in statuses else "undecided" if "undecided" in statuses else "success"
        pvs = None
        if law is not None and with_data and "undecided" not in joint.values():
            pvs = q(sum((Fraction(law[s]) for s in scenarios if joint[s] == "success"), Fraction()))
        status = {z: zones[z]["routes"][r]["task_status"] for z in with_data}
        by_route[r] = {
            "joint_life_by_scenario": joint, "joint_pvs": pvs,
            "life_fails_in": {sid: sorted(z for z in with_data if status[z][sid] == "failure") for sid in scenarios},
            "life_undecided_in": {sid: sorted(z for z in with_data if status[z][sid] == "undecided") for sid in scenarios},
            "feasible_in": sorted(z for z in with_data if r in zones[z]["feasible"]),
        }
    # AM-06: product order over the zones' verified kernel orders.
    pairs = []
    weak = {}
    for a in routes:
        for b in routes:
            per = {z: zones[z]["_pairs"].get((a, b)) for z in with_data}
            row = {c: _and(p[c] if p else None for p in per.values()) for c in CRITERIA + ("weak",)}
            # Life of the whole territory is a criterion of its own: the joint PVS, never a sum of zone PVS.
            x, y = by_route[a]["joint_pvs"], by_route[b]["joint_pvs"]
            row["joint_pvs"] = None if x is None or y is None else "1" if Fraction(x) >= Fraction(y) else "0"
            row["weak"] = _and([row["weak"], row["joint_pvs"]])
            weak[(a, b)] = row["weak"]
            if a == b:
                continue
            back = {z: zones[z]["_pairs"].get((b, a)) for z in with_data}
            def where(c, x, y):
                return sorted(z for z in with_data if per[z] and back[z] and per[z][c] == x and back[z][c] == y)
            by_criterion = {c: {"better_in": where(c, "1", "0"), "worse_in": where(c, "0", "1"),
                                "incomparable_in": where(c, "0", "0"), "equal_in": where(c, "1", "1"),
                                "unknown_in": sorted(z for z in with_data if not per[z] or not back[z] or per[z][c] is None or back[z][c] is None)}
                            for c in CRITERIA}
            pairs.append({"left": a, "right": b, **row, "by_criterion": by_criterion,
                          "strictly_better_in": sorted(z for z in with_data if per[z] and per[z]["strict"] == "1"),
                          "strictly_worse_in": sorted(z for z in with_data if back[z] and back[z]["strict"] == "1")})
    for p in pairs:
        back = weak[(p["right"], p["left"])]
        p["strict"] = "1" if p["weak"] == "1" and back == "0" else "0" if p["weak"] == "0" or back == "1" else None
    feasible = [r for r in routes if with_data and all(r in zones[z]["feasible"] for z in with_data)]
    strict = {(p["left"], p["right"]): p["strict"] for p in pairs}
    # A route leaves the frontier only on a known strict domination by a feasible route.
    frontier = [r for r in feasible if not any(strict.get((o, r)) == "1" for o in feasible if o != r)]
    exhaustive = (not missing and bool(with_data)
                  and all(zones[z]["coverage"] == "EXHAUSTIVE" and zones[z]["verification"] == "VALID" for z in with_data)
                  and all(p["strict"] is not None for p in pairs))
    coverage = "EXHAUSTIVE" if exhaustive else "RELATIVE"
    for z in zones.values():
        z["pairs"] = [{"left": a, "right": b, **v} for (a, b), v in sorted(z.pop("_pairs").items()) if a != b]
    return {
        "format": RESULT_FORMAT, "name": spec["name"], "spec_digest": _digest(spec),
        "scope": "EACH_ZONE_KERNEL_VERIFIED_TERRITORY_LAYER_READS_ZONE_ORDERS",
        "routes": {p["id"]: p["label"] for p in template["policies"]},
        "scenarios": {s["id"]: s["label"] for s in template["scenarios"]}, "law": deepcopy(law),
        "zones": zones,
        "zones_without_data": missing,
        "zone_labels": {z["id"]: z["label"] for z in spec["zones"]},
        "by_route": by_route,
        "decision": {
            "coverage": coverage,
            "rule": "PRODUCT_ORDER_OVER_ZONE_KERNEL_ORDERS_NO_SUMS_NO_ANONYMOUS_MATCHING",
            "feasibility": "KERNEL_FEASIBLE_IN_EVERY_ZONE_WITH_DATA",
            "feasible": feasible, "frontier": frontier, "pairs": pairs,
            "selected": frontier[0] if coverage == "EXHAUSTIVE" and len(frontier) == 1 else None,
            "relative_to": None if not missing else "ZONES_WITH_DATA",
        },
        "assumptions": deepcopy(spec["assumptions"]),
        "empirical_admission": "DECLARED_ASSUMPTIONS_ONLY",
    }


def main(argv=None):
    import argparse
    from pathlib import Path
    parser = argparse.ArgumentParser(description="Evaluate a territory in twin/cases and freeze its result.")
    parser.add_argument("case")
    args = parser.parse_args(argv)
    folder = Path(__file__).resolve().parents[1] / "cases" / args.case
    result = evaluate(json.loads((folder / "territory.json").read_text()))
    (folder / "territory_result.json").write_text(json.dumps(result, ensure_ascii=False, indent=1, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
