"""Module VII, route search: propose routes, let the kernel judge, keep the frontier.

A proposer (here seeded random variation; later a learned model) writes new
routes in the twin's own language: default actions and rules over steps and
declared quantities. Nothing about the domain is used, only the model's
actions, stocks, steps and the quantities it already declares. Each batch puts
the current elite routes beside new candidates in one model, so the kernel
compares them exactly; the batch frontier (feasible and not strictly dominated
in the product order over functions, CAG, wellbeing and PVS) becomes the next
elite. No criterion is summed and no verdict comes from the proposer.

Goals. "per_carrier" (Pedro, 2026-10-18): the life condition first, then the
best route for each carrier. A champion per carrier is kept among the routes
that keep the life condition and have the highest PVS in the batch; a new
route replaces it only if the kernel's per-carrier comparison (by_actor) no
longer counts the champion among that carrier's best. "dominance": a new route
replaces an elite only by strictly dominating it in the full product order.

Every verdict is kept as a row: the route, its per-scenario results and its
place in the batch order. Those rows are the training data for a proposer that
learns where better routes are.
"""
from copy import deepcopy
import hashlib
import json
import random
from fractions import Fraction

from .stockflow import validate_model

FORMAT = "genius-route-search/1"
ROWS = "genius-route-verdicts/1"
MAX_ROUTES = 6


def _key(policy):
    return json.dumps([policy["default_action"], policy["rules"]], sort_keys=True, separators=(",", ":"))


def declared_values(model):
    """Quantities the model already declares for each stock (thresholds, conditions); none are invented."""
    values = {s["id"]: set() for s in model["stocks"]}
    preds = [c for c in model["task"]["conditions"] if c.get("threshold") is not None]
    preds = [{"stock": c["stock"], "value": c["threshold"]} for c in preds]
    for f in model.get("functions", []):
        preds += [p for p in f["when"] if p["kind"] == "stock"]
    for c in model["capabilities"]:
        preds += c.get("holds_when", [])
    for p in model["policies"]:
        for rule in p["rules"]:
            preds += [x for x in rule["when"] if x["kind"] == "stock"]
    for p in preds:
        values[p["stock"]].add(p["value"])
    return {k: sorted(v) for k, v in values.items() if v}


def mutate(policy, model, rng, values):
    """One variation of a route, in the model's language."""
    H = model["horizon"]
    actions = [a["id"] for a in model["actions"]]
    child = deepcopy(policy)
    kind = rng.choice(["default", "steps", "condition", "drop", "shift"])
    if kind == "default":
        child["default_action"] = rng.choice(actions)
    elif kind == "steps":
        start = rng.randint(1, H)
        end = rng.randint(start, min(H, start + max(1, H // 3)))
        child["rules"].insert(0, {"steps": list(range(start, end + 1)), "when": [], "action": rng.choice(actions)})
    elif kind == "condition" and values:
        stock = rng.choice(sorted(values))
        child["rules"].insert(0, {"steps": list(range(1, H + 1)), "when": [
            {"kind": "stock", "stock": stock, "op": rng.choice(["ge", "le"]), "value": rng.choice(values[stock])}],
            "action": rng.choice(actions)})
    elif kind == "drop" and child["rules"]:
        child["rules"].pop(rng.randrange(len(child["rules"])))
    elif kind == "shift" and child["rules"]:
        rule = child["rules"][rng.randrange(len(child["rules"]))]
        delta = rng.choice([-1, 1])
        rule["steps"] = sorted({min(H, max(1, t + delta)) for t in rule["steps"]})
    child["rules"] = child["rules"][:30]
    return child


def _rows(model, batch, ids, canonical, origin):
    decision = canonical["decision"]
    strict = {(p["left"], p["right"]) for p in decision["pairs"] if p["strict"] == "1"}
    rows = []
    for pid in ids:
        policy = canonical["policies"][pid]
        rows.append({"format": ROWS, "batch": batch, "route": pid, "origin": origin[pid],
                     "policy": next(p for p in model["policies"] if p["id"] == pid),
                     "feasible": pid in decision["feasible"], "frontier": pid in decision["frontier"],
                     "strictly_dominated_by": sorted(l for l, r in strict if r == pid),
                     "pvs": policy["pvs"]["value"], "cag_robust": policy["cag"]["robust"],
                     "by_scenario": {sid: {"task_status": row["task_status"],
                                           "wellbeing_worst": {f"{w['carrier']}.{w['dimension']}": w["worst"] for w in row["wellbeing"]}}
                                     for sid, row in policy["by_scenario"].items()}})
    return rows


def _pvs_key(value):
    return Fraction(value) if value is not None else Fraction(-1)


def _champions(canonical, ids, champions, children):
    """Per carrier: keep the champion while it stays among that carrier's best; else the best newcomer."""
    by_actor = canonical["decision"]["by_actor"]
    pvs = {pid: _pvs_key(canonical["policies"][pid]["pvs"]["value"]) for pid in by_actor["candidates"]}
    top = max(pvs.values()) if pvs else None
    changes, ties = [], []
    for carrier, row in by_actor["by_carrier"].items():
        if row["best"] is None:
            continue
        best = [pid for pid in row["best"] if pvs.get(pid) == top]
        current = champions.get(carrier)
        if not best:
            continue
        if current not in best:
            new = sorted(best, key=lambda pid: (pid not in children, ids.index(pid)))[0]
            champions[carrier] = new
            if current is not None:
                changes.append({"carrier": carrier, "route": new, "replaces": current})
        else:
            ties += [{"carrier": carrier, "route": pid, "tied_with": current} for pid in best if pid in children]
    return changes, ties


def search(model, evaluate_model, batches=10, elites=3, seed=0, goal="per_carrier"):
    """Batches of elites plus new candidates, judged by the kernel (see the module docstring for goals)."""
    validate_model(model)
    if goal not in ("per_carrier", "dominance"):
        raise ValueError("goal is per_carrier or dominance")
    if not 1 <= elites < MAX_ROUTES:
        raise ValueError(f"elites must leave room for candidates (1 to {MAX_ROUTES - 1})")
    rng = random.Random(seed)
    values = declared_values(model)
    first = evaluate_model(deepcopy(model))
    if first.get("verification", {}).get("valid") is not True:
        raise RuntimeError("the declared model did not verify")
    decision = first["canonical_results"]["decision"]
    order = [p["id"] for p in model["policies"]]
    start = [pid for pid in order if pid in decision["frontier"]] or [pid for pid in order if pid in decision["feasible"]] or order
    routes = {p["id"]: p for p in model["policies"]}
    origin = {pid: "DECLARED" for pid in order}
    rows = _rows(model, 0, order, first["canonical_results"], origin)
    champions = {}
    if goal == "per_carrier":
        _champions(first["canonical_results"], order, champions, set())
        elite = list(dict.fromkeys(champions.values()))[:MAX_ROUTES - 1] or start[:elites]
    else:
        elite = start[:elites]
    declared_champions = dict(champions)
    seen = {_key(p) for p in model["policies"]}
    improvements, history, made = [], [], 0
    pool = list(elite)  # every route left undominated in some batch may be a parent
    for b in range(1, batches + 1):
        children, tries = [], 0
        while len(elite) + len(children) < MAX_ROUTES and tries < 200:
            tries += 1
            parent = routes[rng.choice(pool)]
            child = mutate(parent, model, rng, values)
            if _key(child) in seen:
                continue
            made += 1
            child["id"] = f"r{made}"
            child["label"] = f"Variante {made} de {parent['id']}"
            trial = deepcopy(model)
            trial["policies"] = [routes[pid] for pid in elite] + children + [child]
            try:
                validate_model(trial)
            except ValueError:
                continue
            seen.add(_key(child))
            children.append(child)
            origin[child["id"]] = f"VARIATION_OF:{parent['id']}"
            routes[child["id"]] = child
        if not children:
            break
        batch_model = deepcopy(model)
        batch_model["policies"] = [routes[pid] for pid in elite] + children
        batch_model["selection"] = "none"
        result = evaluate_model(batch_model)
        if result.get("verification", {}).get("valid") is not True:
            history.append({"batch": b, "status": "UNVERIFIED"})
            continue
        canonical = result["canonical_results"]
        ids = [p["id"] for p in batch_model["policies"]]
        rows += _rows(batch_model, b, ids, canonical, origin)
        strict = {(p["left"], p["right"]) for p in canonical["decision"]["pairs"] if p["strict"] == "1"}
        if goal == "per_carrier":
            changes, ties = _champions(canonical, ids, champions, {c["id"] for c in children})
            improvements += [{"batch": b, **c} for c in changes]
            pool += [t["route"] for t in ties if t["route"] not in pool]
            pool += [pid for pid in champions.values() if pid not in pool]
            history.append({"batch": b, "status": "VERIFIED", "candidates": [c["id"] for c in children],
                            "champions": dict(champions), "ties": ties})
            elite = list(dict.fromkeys(champions.values()))[:MAX_ROUTES - 1]
            continue
        for child in children:
            beaten = sorted(pid for pid in elite if (child["id"], pid) in strict)
            if beaten:
                improvements.append({"batch": b, "route": child["id"], "strictly_dominates": beaten})
        frontier = [pid for pid in ids if pid in canonical["decision"]["frontier"]]
        history.append({"batch": b, "status": "VERIFIED", "candidates": [c["id"] for c in children],
                        "frontier": frontier, "kept": frontier[:elites], "overflow": frontier[elites:]})
        pool += [pid for pid in frontier if pid not in pool]
        # Children that strictly dominate an elite replace it; otherwise the elite stays.
        winners = [i["route"] for i in improvements if i["batch"] == b]
        if frontier:
            elite = (winners + [pid for pid in frontier if pid not in winners])[:elites]
    digest = hashlib.sha256(json.dumps(model, sort_keys=True).encode()).hexdigest()
    return {"format": FORMAT, "model_sha256": digest, "seed": seed, "batches": history,
            "goal": goal, "declared_frontier": start, "declared_champions": declared_champions, "champions": champions,
            "elite": elite, "elite_routes": [routes[pid] for pid in elite],
            "improvements": improvements, "undominated_pool": pool, "rows": rows,
            "meaning": "Routes proposed by variation and judged by the kernel batch by batch. Champions are the best route found "
                       "for each carrier among those keeping the life condition with the highest PVS; the dominance elite is "
                       "the last batch frontier. Neither is a global optimum; no criterion is summed and nothing is selected."}
