"""Four-criterion preorder, relative/exhaustive frontier and explicit selection."""
from fractions import Fraction

from .common import defined, value, PROFILE, THEORY_SNAPSHOT


def _functional(profile):
    return {(s["scenario"], x["index"]): Fraction(x["value"])
            for s in profile for x in s["profile"]}


def _welfare(profile):
    return {(r["scenario"], r["t"], r["carrier"], r["dimension"]):
            Fraction(r["value"]) for r in profile}


def _product(left, right):
    if left.keys() != right.keys():
        raise ValueError("Internal mismatch of fixed comparison coordinates")
    return all(left[k] >= right[k] for k in left)


def evaluate(ctx, trees, results):
    target = sorted(results)
    feasible, failed, unknown = [], [], []
    for pid in target:
        hard = results[pid]["hard"]
        if any(value(h["value"]) == "0" for h in hard):
            failed.append(pid)
        elif all(value(h["value"]) == "1" for h in hard):
            feasible.append(pid)
        else:
            unknown.append(pid)
    block = [pid for pid in target if trees[pid]["complete"]
             and defined(trees[pid]["causal"]["scenarios"])
             and defined(results[pid]["functional"]["terminal"])
             and defined(results[pid]["generative"]["cag"])
             and defined(results[pid]["welfare"]["profile"])
             and defined(results[pid]["probability"]["pvs"])]
    candidate = sorted(set(block) & set(feasible))
    values = {}
    for pid in block:
        r = results[pid]
        values[pid] = (_functional(value(r["functional"]["terminal"])),
                       set(value(r["generative"]["cag"])),
                       _welfare(value(r["welfare"]["profile"])),
                       Fraction(value(r["probability"]["pvs"])))
    pairs, relation = [], {}
    for left in block:
        for right in block:
            ctx.tick()
            a, b = values[left], values[right]
            components = (_product(a[0], b[0]), b[1] <= a[1],
                          _product(a[2], b[2]), a[3] >= b[3])
            relation[left, right] = all(components)
            pairs.append({"left": left, "right": right,
                **{name: "1" if flag else "0" for name, flag in zip(
                    ("functional", "cag", "welfare", "pvs"), components)},
                "weak": "1" if all(components) else "0", "strict": "0"})
            ctx.check("PAIR_COMPARISON", "PASS", detail=f"Computed all four criteria: {left} >= {right}.")
    for p in pairs:
        p["strict"] = "1" if (relation[p["left"], p["right"]]
                                  and not relation[p["right"], p["left"]]) else "0"
    strict = {(p["left"], p["right"]) for p in pairs if p["strict"] == "1"}
    dominators = [{"policy": p, "by": [q for q in candidate if (q, p) in strict]}
                  for p in candidate if any((q, p) in strict for q in candidate)]
    frontier = [p for p in candidate if not any((q, p) in strict for q in candidate)]
    ctx.guard("G14", block == target)
    ctx.guard("G15", set(candidate) == set(feasible))
    exhaustive = all(ctx.guard_value(f"G{i:02}") is True for i in range(1, 16))
    omitted = []
    for pid in target:
        if pid in candidate:
            continue
        reasons = []
        if pid not in block:
            reasons.append(ctx.diag("COMPARISON_GUARD", "DECISION", policy=pid,
                                   message="At least one complete compatible valuation is unavailable."))
        if pid in failed:
            reasons.append(ctx.diag("HARD_VIOLATION", "HARD", policy=pid,
                                   message="A declared restriction has a verified negative witness."))
        elif pid in unknown:
            reasons.append(ctx.diag("HARD_UNDECIDED", "HARD", policy=pid,
                                   message="Feasibility is not certified and no negative witness decides it."))
        omitted.append({"policy": pid, "reasons": reasons})
    rule = ctx.data["selection"]
    if rule["mode"] == "none":
        selection = ctx.out("SELECTION_DISABLED", "DECISION", "SELECTION")
    elif not exhaustive:
        selection = ctx.out("SELECTION_SCOPE", "DECISION", "SELECTION")
    elif not frontier:
        selection = ctx.out("SELECTION_EMPTY", "DECISION", "SELECTION")
    elif rule["mode"] == "unique" and len(frontier) != 1:
        selection = ctx.out("SELECTION_NOT_UNIQUE", "DECISION", "SELECTION")
    else:
        chosen = frontier[0] if rule["mode"] == "unique" else next(
            p for p in rule["order"] if p in frontier)
        selection = ctx.ok(chosen, "SELECTION")
    selection_check = ctx.check("SELECTION", "PASS",
        detail="The selected value or absence of selection conforms to the explicit rule and scope.")
    decision = ctx.ok({"target": target, "B": block, "C": candidate,
        "feasible": feasible, "failed": failed, "unknown": unknown,
        "omitted": omitted, "pairs": pairs, "frontier": frontier,
        "dominators": dominators,
        "coverage": "EXHAUSTIVE" if exhaustive else "RELATIVE",
        "selection": selection}, "FRONTIER")
    guards = ctx.guard_checks()
    if exhaustive:
        integration = {"state": "DEFINED", "value": {
            "id": "Integration.1", "profile": PROFILE,
            "theory_snapshot": THEORY_SNAPSHOT, "target": target,
            "guards": guards, "selection_check": selection_check,
            "assumptions": sorted(a["id"] for a in ctx.data["assumptions"]),
            "claim": "CONDITIONAL_FORMAL_INSTANCE"}, "checks": guards + [selection_check]}
    else:
        rejected = next((g for g in ctx.guard_obligations if ctx.guard_value(g) is False), None)
        if rejected:
            integration = ctx.out("COMPARISON_GUARD", "DECISION", rejected,
                message=f"Strong integration is outside its domain: {rejected} fails.")
        else:
            integration = ctx.block("DEPENDENCY_BLOCKED", "DECISION",
                message="Strong integration has an unresolved required obligation.")
    return decision, integration
