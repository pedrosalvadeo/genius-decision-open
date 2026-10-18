"""Module VII over time: a living population of routes for one twin.

The population is the artificial-life cycle the other modules already allow:

- genome: each route, written in the twin's language (actions over steps and
  declared conditions); it varies and is inherited through route search;
- metabolism: the living twin, restarted from every fully observed state
  (living.reanchor);
- selection: the kernel, life condition first, then the best route for each
  carrier; each carrier is a niche, so several routes live at once;
- death: a route dies when the twin of the present (the declared model at
  first, then each restart from an observed state) shows it losing the life
  condition in some scenario while another route keeps it, or when its niches
  are taken by better routes (displaced);
- heredity: every kernel verdict is kept and trains the learned proposer of
  the next generation, shifted to the new present.

Fixed and outside evolution: the kernel, the ideal of wellbeing and care for
life, and the declared world (actions, scenarios, law, conditions). Nothing
here contacts anyone or copies itself anywhere. Routes are stored in the
model's original steps, so a route keeps its identity across generations.
"""
from copy import deepcopy
import hashlib
import json

from . import route_search
from .stockflow import validate_model

FORMAT = "genius-route-population/1"
MEMORY_ROWS = 200


def _digest(model):
    return hashlib.sha256(json.dumps(model, sort_keys=True).encode()).hexdigest()


def _shift(policy, step):
    """A route in original steps, as seen from `step`: earlier steps are past and drop out."""
    out = deepcopy(policy)
    rules = []
    for rule in out["rules"]:
        later = [t - step for t in rule["steps"] if t > step]
        if later:
            rules.append({**rule, "steps": later})
    out["rules"] = rules
    return out


def _unshift(policy, step):
    out = deepcopy(policy)
    out["rules"] = [{**rule, "steps": [t + step for t in rule["steps"]]} for rule in out["rules"]]
    return out


def _inherit(rows, step, digest):
    """Earlier verdicts as the new present sees them: same route from `step` on, its path from there."""
    out = []
    for row in rows:
        lag = step - row["step"]
        if lag < 0:
            continue
        policy = _shift(row["policy_original"], step)
        by_scenario = {}
        for sid, cell in row["by_scenario"].items():
            by_scenario[sid] = {**cell, "welfare_path": {k: v[lag:] for k, v in cell["welfare_path"].items()}}
        out.append({**row, "policy": {**policy, "id": row["route"]}, "by_scenario": by_scenario,
                    "model_sha256": digest, "inherited_from_step": row["step"]})
    return out


def _generation(population, model, step, label, evaluate_model, batches, seed):
    validate_model(model)
    members = population["members"]
    alive = [rid for rid, m in members.items() if m["died_generation"] is None]
    g = len(population["generations"])
    present = deepcopy(model)
    seen, routes, merged = {}, [], []
    for rid in alive:
        policy = {**_shift(members[rid]["policy"], step), "id": rid, "label": members[rid]["label"]}
        key = json.dumps([policy["default_action"], policy["rules"]], sort_keys=True)
        if key in seen:
            merged.append({"route": rid, "same_as": seen[key]})
            continue
        seen[key] = rid
        routes.append(policy)
    died = []
    for row in merged:
        members[row["route"]].update(died_generation=g, death="MERGED_WITH:" + row["same_as"])
        died.append({"route": row["route"], "reason": "MERGED_WITH:" + row["same_as"]})
    present["policies"] = routes
    judged = evaluate_model(present)
    if judged.get("verification", {}).get("valid") is not True:
        raise RuntimeError("the present model did not verify")
    canonical = judged["canonical_results"]
    lost = {p["id"]: sorted(sid for sid, row in canonical["policies"][p["id"]]["by_scenario"].items()
                            if row["task_status"] == "failure") for p in routes}
    survivors = [p for p in routes if not lost[p["id"]]]
    if survivors:
        for policy in routes:
            if lost[policy["id"]]:
                members[policy["id"]].update(died_generation=g, death="LOSES_THE_LIFE_CONDITION")
                died.append({"route": policy["id"], "reason": "LOSES_THE_LIFE_CONDITION", "loses_life_in": lost[policy["id"]],
                             "evidence": label})
    else:
        # No living route keeps the life condition: none dies for it, and the search looks for one that does.
        survivors = routes
    present["policies"] = survivors
    digest = _digest(present)
    inherited = _inherit(population["memory"], step, digest)
    result = route_search.search(present, evaluate_model, batches=batches, seed=seed + g,
                                 proposer="learned", training_rows=inherited)
    champions = result["champions"]
    by_id = {p["id"]: p for p in result["elite_routes"]} | {p["id"]: p for p in survivors}
    names = {}
    for carrier, rid in sorted(champions.items()):
        if rid in members and members[rid]["died_generation"] is None:
            names[rid] = rid
            continue
        if rid not in names:
            new = f"g{g}_{rid}"
            row = next(r for r in result["rows"] if r["route"] == rid)
            origin = row["origin"]
            parent = origin.split(":", 1)[1] if origin.startswith("VARIATION_OF:") else None
            members[new] = {"policy": _unshift({k: v for k, v in by_id.get(rid, row["policy"]).items() if k not in ("id", "label")}, step),
                            "label": f"Ruta nacida en la generación {g}", "born_generation": g, "born_step": step,
                            "parent": names.get(parent, parent), "died_generation": None, "death": None}
            names[rid] = new
    living_ids = set(names.values())
    for policy in survivors:
        rid = policy["id"]
        if rid in members and rid not in living_ids and members[rid]["died_generation"] is None:
            members[rid].update(died_generation=g, death="DISPLACED_IN_EVERY_NICHE")
            died.append({"route": rid, "reason": "DISPLACED_IN_EVERY_NICHE"})
    for row in result["rows"]:
        original = _unshift({k: v for k, v in row["policy"].items() if k not in ("id", "label")}, step)
        population["memory"].append({**{k: v for k, v in row.items() if k not in ("policy", "model_sha256")},
                                     "generation": g, "step": step, "policy_original": original})
    population["memory"] = population["memory"][-MEMORY_ROWS:]
    population["generations"].append({
        "generation": g, "step": step, "observation": label, "model_sha256": digest,
        "niches": {carrier: names[rid] for carrier, rid in sorted(champions.items())},
        "life_condition_kept_by": sorted(names[rid] for rid in set(champions.values()) if _keeps_life(result["rows"], rid)),
        "born": sorted(r for r in living_ids if members[r]["born_generation"] == g),
        "died": died, "improvements": [{**i, "route": names.get(i["route"], i["route"]),
                                        "replaces": names.get(i["replaces"], i["replaces"])} for i in result["improvements"]],
        "kernel_batches": len(result["batches"]) + 1, "learning": [{k: v for k, v in l.items() if k != "chosen"} for l in result["learning"]]})
    return population


def _keeps_life(rows, rid):
    last = [r for r in rows if r["route"] == rid][-1]
    return all(cell["task_status"] == "success" for cell in last["by_scenario"].values())


def found(model, case, evaluate_model, batches=6, seed=0):
    """Generation 0: the declared routes, judged and varied from the model's own step 0."""
    validate_model(model)
    population = {"format": FORMAT, "case": case, "base_model_sha256": _digest(model), "horizon": model["horizon"],
                  "members": {p["id"]: {"policy": {k: v for k, v in p.items() if k not in ("id", "label")}, "label": p["label"],
                                        "born_generation": 0, "born_step": 0, "parent": None,
                                        "died_generation": None, "death": None} for p in model["policies"]},
                  "generations": [], "memory": [],
                  "fixed": ["the kernel FP1", "the ideal of wellbeing and care for life",
                            "the declared world: actions, scenarios, law, life conditions"],
                  "meaning": "A population of routes that lives across observations: the kernel selects, reality kills, "
                             "survivors vary and the next generation inherits every verdict. No criterion is summed; "
                             "nothing contacts anyone."}
    return _generation(population, model, 0, "MODEL_STEP_0", evaluate_model, batches, seed)


def advance(population, living_model, step, label, evaluate_model, batches=6, seed=0):
    """Next generation from the living twin restarted at `step` (living.reanchor of the base model)."""
    if not 0 < step < population["horizon"]:
        raise ValueError("the observed step must leave at least one step to decide")
    if living_model["horizon"] != population["horizon"] - step:
        raise ValueError("the living model must be the base model restarted at this step")
    if population["generations"] and step <= population["generations"][-1]["step"]:
        raise ValueError("a generation needs a later observation than the last one")
    return _generation(population, living_model, step, label, evaluate_model, batches, seed)


def alive(population):
    return {rid: m for rid, m in population["members"].items() if m["died_generation"] is None}
