"""Exact finite semantic evidence, occurrence laws, and hard constraints.

This module implements specification 04 with the wire records of specification
06.  In particular, an absent verdict is a legitimate outcome of the partial
evaluator; it is never silently replaced by either Boolean value.
"""

from fractions import Fraction

from .common import defined, qkey, qstr, query, value


def _support(pointer):
    return [{"document": "INPUT", "pointer": pointer}]


def _queries(policy, paths):
    return [query(policy, path) for path in paths]


def _blocked(reasons):
    return {"state": "BLOCKED", "reasons": list(dict.fromkeys(reasons))}


def _domain_summary(cells):
    """Conjoin domain obligations, retaining a decided counterexample."""
    states = [cell["state"] for cell in cells]
    if "OUTSIDE_DOMAIN" in states:
        return False
    if "BLOCKED" in states:
        return None
    return True


def _causal_indexes(data):
    model = data["model"]
    transitions = {
        (row["t"], row["x"], row["a"]): row["outcomes"]
        for row in model["transitions"]
    }
    executable = {
        (row["t"], row["x"]): set(row["actions"])
        for row in model["executable"]
    }
    admissible = {
        (row["t"], row["x"]): set(row["actions"])
        for row in model["admissible"]
    }
    return transitions, executable, admissible


def _subtrees(ctx, tree, indexes):
    """Find complete local subtrees without turning an open node into a leaf."""
    transitions, executable, admissible = indexes
    complete = {}
    leaves = {}
    for path, node in sorted(tree["node_map"].items(), key=lambda item: len(item[0]), reverse=True):
        ctx.tick()
        if len(path) == ctx.H:
            complete[path] = True
            leaves[path] = [path]
            continue
        action = value(node["action"])
        loc = (node["t"], node["x"])
        outcomes = transitions.get((*loc, action)) if action is not None else None
        edges = node["outcomes"]
        expected = {outcome["branch"] for outcome in outcomes or ()}
        actual = {edge["branch"] for edge in edges}
        children = [tuple(edge["child"]["path"]) for edge in edges]
        local_ok = bool(
            outcomes
            and action in executable.get(loc, set())
            and action in admissible.get(loc, set())
            and actual == expected
            and all(defined(edge["next_i"]) for edge in edges)
            and all(complete.get(child, False) for child in children)
        )
        complete[path] = local_ok
        known_leaves = []
        for child in children:
            ctx.tick()
            known_leaves.extend(leaves.get(child, ()))
        leaves[path] = known_leaves
    return complete, leaves


def _semantic_evidence(ctx, tree, references, task, indexes):
    policy = tree["policy"]
    subtree_complete, descendants = _subtrees(ctx, tree, indexes)
    result = []
    verdicts = {}
    for ordinal, node in enumerate(tree["nodes"], 1):
        ctx.tick()
        q = node["query"]
        path = tuple(q["path"])
        leaf_paths = descendants[path]
        leaf_queries = _queries(policy, leaf_paths)
        missing = [leaf for leaf in leaf_paths if (policy, leaf) not in references]
        if not subtree_complete[path]:
            ctx.check(
                "SEM_UNION", "UNDETERMINED", policy=policy, queries=[q],
                support=_support("/semantics/references"),
                detail="The complete set of causal completions is not established.",
            )
            sem = ctx.block(
                "DEPENDENCY_BLOCKED", "EVIDENCE", policy=policy, queries=[q],
                pointers=["/model", "/semantics/references"],
                message="Semantic coverage depends on an incomplete causal subtree.",
            )
            verdict = ctx.block(
                "DEPENDENCY_BLOCKED", "EVIDENCE", policy=policy, queries=[q],
                pointers=["/semantics"],
                message="No decisive certificate is available without complete semantic coverage.",
            )
        elif not leaf_paths or missing:
            affected = _queries(policy, missing) or [q]
            sem = ctx.out(
                "SEM_REFERENCE_MISSING", "EVIDENCE", "SEM_UNION",
                policy=policy, queries=affected, pointers=["/semantics/references"],
                message="Semantic union requires a nonempty completion set and every leaf reference.",
            )
            verdict = ctx.out(
                "SEM_REFERENCE_MISSING", "EVIDENCE", "DECISIVE_SET",
                policy=policy, queries=affected, pointers=["/semantics/references"],
                message="The exact partial evaluator is outside its domain because leaf references are missing.",
            )
        else:
            states = set()
            reference_rows = []
            for leaf, leaf_query in zip(leaf_paths, leaf_queries):
                ctx.tick()
                leaf_states = references[(policy, leaf)]
                states.update(leaf_states)
                reference_rows.append({"leaf": leaf_query, "states": sorted(leaf_states)})
            read = {
                "leaves": leaf_queries,
                "references": reference_rows,
                "states": sorted(states),
            }
            sem = ctx.ok(
                read, "SEM_UNION", policy=policy, queries=[q],
                support=_support("/semantics/references"),
                detail="Enumerated every completion and the exact nonempty union of its references.",
            )
            outside_task = sorted(states.difference(task))
            image = {task[state] for state in states if state in task}
            if outside_task:
                verdict = ctx.out(
                    "TASK_OUTSIDE_DOMAIN", "EVIDENCE", "DECISIVE_SET",
                    policy=policy, queries=[q], pointers=["/semantics/task"],
                    message="Task is undefined on semantic states: " + ", ".join(outside_task),
                )
                if len(image) > 1:
                    verdict["reasons"].append(ctx.diag(
                        "VERDICT_MIXED", "EVIDENCE", policy=policy, queries=[q],
                        pointers=["/semantics/task"],
                        message="The present task values also contain both zero and one.",
                    ))
                    verdict["checks"].append(ctx.check(
                        "DECISIVE_SET", "FAIL", policy=policy, queries=[q],
                        support=_support("/semantics/task"),
                        detail="The supplied task rows are not constant on the semantic states.",
                    ))
            elif len(image) != 1:
                verdict = ctx.out(
                    "VERDICT_MIXED", "EVIDENCE", "DECISIVE_SET",
                    policy=policy, queries=[q], pointers=["/semantics/task"],
                    message="The semantic states contain both task values zero and one.",
                )
            else:
                bit = next(iter(image))
                certificate = {
                    "id": f"Cert.{policy}.{ordinal}",
                    "kind": "DECISIVE_SET",
                    "query": q,
                    "protocol": "FP1_EXACT_ENUM_V1",
                    "read": read,
                    "A": sorted(states),
                    "value": bit,
                    "task_rows": [{"state": state, "value": task[state]} for state in sorted(states)],
                }
                verdict = ctx.ok(
                    certificate, "DECISIVE_SET", policy=policy, queries=[q],
                    support=_support("/semantics"),
                    detail="Canonical certificate: A equals Sem, is nonempty, lies in the task domain, and has constant value.",
                )
        result.append({"query": q, "sem": sem, "verdict": verdict})
        verdicts[path] = verdict
    # G11 concerns the exactness of a legitimate partial evaluator, not total V.
    ctx.guard("G11", True if all(subtree_complete.values()) and tree["complete"] else None)
    return result, verdicts


def _law_rows(ctx, tree, law_rows, transitions):
    """Validate every supplied row, including all rows at null occurrences."""
    policy = tree["policy"]
    valid_rows = {}
    invalid = []
    unresolved = []
    for index, row in law_rows:
        ctx.tick()
        q = row["query"]
        path = tuple(q["path"])
        weights = {item["branch"]: Fraction(item["mass"]) for item in row["weights"]}
        total = sum(weights.values(), Fraction(0))
        node = tree["node_map"].get(path)
        expected = None
        if node is not None and defined(node["action"]):
            outcomes = transitions.get((node["t"], node["x"], value(node["action"])))
            if outcomes is not None:
                expected = {outcome["branch"] for outcome in outcomes}
        pointer = f"/law/rows/{index}"
        wrong_support = expected is not None and set(weights) != expected
        if total != 1 or wrong_support:
            details = []
            if total != 1:
                details.append("row mass is " + qstr(total) + " instead of 1/1")
            if wrong_support:
                details.append("missing branches=" + repr(sorted(expected.difference(weights))))
                details.append("extra branches=" + repr(sorted(set(weights).difference(expected))))
            detail = "; ".join(details)
            ctx.check(
                "LAW_ROW", "FAIL", policy=policy, queries=[q],
                support=_support(pointer), detail=detail,
            )
            invalid.append(ctx.diag(
                "LAW_INVALID", "LAW", policy=policy, queries=[q], pointers=[pointer], message=detail,
            ))
        elif expected is None:
            ctx.check(
                "LAW_ROW", "UNDETERMINED", policy=policy, queries=[q],
                support=_support(pointer),
                detail="Normalization is exact but causal child support is not yet known.",
            )
            unresolved.append(ctx.diag(
                "DEPENDENCY_BLOCKED", "LAW", policy=policy, queries=[q], pointers=[pointer, "/model"],
                message="The supplied law row cannot be checked against unresolved causal support.",
            ))
        else:
            ctx.check(
                "LAW_ROW", "PASS", policy=policy, queries=[q],
                support=_support(pointer),
                detail="The supplied row has exactly the causal children and nonnegative masses summing to one.",
            )
            valid_rows[path] = weights
    return valid_rows, invalid, unresolved


def _partition(ctx, tree, verdicts):
    policy = tree["policy"]
    if not tree["complete"]:
        return ctx.block(
            "DEPENDENCY_BLOCKED", "LAW", policy=policy,
            pointers=["/model", "/semantics"],
            message="A complete leaf partition requires the complete causal tree.",
        )
    partition = {"positive": [], "negative": [], "undecided": []}
    for node in tree["nodes"]:
        ctx.tick()
        path = tuple(node["query"]["path"])
        if len(path) != ctx.H:
            continue
        verdict = verdicts[path]
        if verdict["state"] == "BLOCKED":
            return ctx.block(
                "DEPENDENCY_BLOCKED", "LAW", policy=policy, queries=[node["query"]],
                pointers=["/semantics"], message="A leaf verdict has not been evaluated.",
            )
        label = "undecided"
        if defined(verdict):
            label = "positive" if value(verdict)["value"] == "1" else "negative"
        partition[label].append(node["query"])
    return ctx.ok(
        partition, "VPROB", policy=policy,
        support=_support("/semantics"),
        detail="The positive, negative, and outside-domain leaves form a disjoint exhaustive partition independently of the law.",
    )


def _probability(ctx, tree, verdicts, law_rows, indexes):
    policy = tree["policy"]
    rows, invalid, unresolved = _law_rows(ctx, tree, law_rows, indexes[0])
    partition = _partition(ctx, tree, verdicts)
    if invalid or unresolved:
        reasons = invalid + unresolved
        masses = [{"query": node["query"], "mass": _blocked(reasons)} for node in tree["nodes"]]
        ctx.guard("G12", False if invalid else None)
        return {"masses": masses, "partition": partition, "vector": _blocked(reasons), "pvs": _blocked(reasons)}

    mass_values = {(): Fraction(1)}
    mass_cells = {}
    missing_rows = []
    # Sorting by path length guarantees parents precede children even when the
    # causal constructor uses a depth-first presentation order.
    for path, node in sorted(tree["node_map"].items(), key=lambda item: len(item[0])):
        ctx.tick()
        q = node["query"]
        if path:
            parent = path[:-1]
            parent_mass = mass_values.get(parent)
            if parent_mass is not None:
                if parent in rows:
                    mass_values[path] = parent_mass * rows[parent][path[-1]]
                elif parent_mass == 0:
                    # This is unconditional zero mass; no missing conditional
                    # distribution is fabricated or reported as a valid row.
                    mass_values[path] = Fraction(0)
        if path in mass_values:
            mass_cells[path] = ctx.ok(
                qstr(mass_values[path]), "LAW_MASS", policy=policy, queries=[q],
                support=_support("/law"),
                detail="Root mass one, exact row propagation, or zero propagation below a null node.",
            )
        else:
            mass_cells[path] = ctx.out(
                "LAW_UNDETERMINED", "LAW", "LAW_MASS", policy=policy, queries=[q],
                pointers=["/law/rows"],
                message="An absent row at a positive ancestor prevents determining this occurrence mass.",
            )
        if len(path) < ctx.H and path not in rows and mass_values.get(path, Fraction(0)) > 0:
            # An open causal node has no established continuation support;
            # absence there is not itself a completed law-domain judgement.
            if tree["complete"] or node["outcomes"]:
                missing_rows.append(q)
    masses = [{"query": node["query"], "mass": mass_cells[tuple(node["query"]["path"])]} for node in tree["nodes"]]

    if missing_rows:
        ctx.check(
            "LAW_ROW", "FAIL", policy=policy, queries=missing_rows,
            support=_support("/law/rows"), detail="All listed positive-mass nodes lack conditional rows.",
        )
        ctx.diag(
            "LAW_UNDETERMINED", "LAW", policy=policy, queries=missing_rows, pointers=["/law/rows"],
            message="These positive-mass internal occurrences have no conditional distribution.",
        )
    if not tree["complete"] or not defined(partition):
        vector = ctx.block(
            "DEPENDENCY_BLOCKED", "LAW", policy=policy, pointers=["/model", "/semantics", "/law"],
            message="The complete leaf set and its legitimate partition are required for the mass vector.",
        )
        pvs = ctx.block(
            "DEPENDENCY_BLOCKED", "LAW", policy=policy, pointers=["/model", "/semantics", "/law"],
            message="PVS depends on a complete legitimate mass vector.",
        )
        ctx.guard("G12", False if missing_rows else None)
    elif missing_rows:
        vector = ctx.out(
            "LAW_UNDETERMINED", "LAW", "VPROB", policy=policy, queries=missing_rows,
            pointers=["/law/rows"], message="The declared partial law does not determine the leaf distribution.",
        )
        pvs = ctx.out(
            "LAW_UNDETERMINED", "LAW", "VPROB", policy=policy, queries=missing_rows,
            pointers=["/law/rows"], message="PVS has no value for an undetermined law.",
        )
        ctx.guard("G12", False)
    else:
        totals = {}
        for label, field in (("positive", "success"), ("negative", "failure"), ("undecided", "undecided")):
            total = Fraction(0)
            for leaf in value(partition)[label]:
                ctx.tick()
                total += mass_values[tuple(leaf["path"])]
            totals[field] = total
        if sum(totals.values(), Fraction(0)) != 1:
            raise RuntimeError("Exact law propagation violated leaf normalization")
        vector = ctx.ok(
            {field: qstr(total) for field, total in totals.items()}, "VPROB", policy=policy,
            support=_support("/law") + _support("/semantics"),
            detail="Exact sums over the three leaf regions are nonnegative and sum to one; prefixes are not added.",
        )
        if totals["undecided"]:
            unknown_leaves = value(partition)["undecided"]
            pvs = ctx.out(
                "POSITIVE_UNDECIDED_MASS", "LAW", "VPROB", policy=policy, queries=unknown_leaves,
                pointers=["/semantics", "/law"],
                message="Undecided leaf mass is " + qstr(totals["undecided"]) + "; no renormalization is permitted.",
            )
            ctx.guard("G12", False)
        else:
            if not 0 <= totals["success"] <= 1:
                raise RuntimeError("Exact PVS is outside the unit interval")
            pvs = ctx.ok(
                qstr(totals["success"]), "VPROB", policy=policy,
                support=_support("/law") + _support("/semantics"),
                detail="A legitimate normalized law has zero undecided mass; PVS is its success mass in [0,1].",
            )
            ctx.guard("G12", True)
    return {"masses": masses, "partition": partition, "vector": vector, "pvs": pvs}


def _hard(ctx, tree, verdicts, structural):
    policy = tree["policy"]
    resources = {
        (qkey(row["query"])[1], row["resource"]): row["total"]
        for row in structural["resources"]
    }
    result = []
    for index, constraint in enumerate(ctx.data["constraints"]):
        ctx.tick()
        resource_constraint = constraint["kind"] == "resource_budget"
        rule = "HARD_RESOURCE" if resource_constraint else "HARD_TASK"
        pointer = f"/constraints/{index}"
        known = [
            node["query"] for node in tree["nodes"]
            if resource_constraint or constraint["scope"] == "ALL_NODES" or len(node["query"]["path"]) == ctx.H
        ]
        checked, violations, missing = [], [], []
        for q in known:
            ctx.tick()
            path = tuple(q["path"])
            cell = resources.get((path, constraint["resource"])) if resource_constraint else verdicts[path]
            if cell is None or not defined(cell):
                missing.append(q)
                continue
            checked.append(q)
            passes = Fraction(value(cell)) <= Fraction(constraint["bound"]) if resource_constraint else value(cell)["value"] == "1"
            if not passes:
                violations.append(q)
            ctx.check(
                rule, "PASS" if passes else "FAIL", policy=policy, queries=[q],
                support=_support(pointer) + _support("/resources" if resource_constraint else "/semantics"),
                detail="Local joint demand is within the bound." if resource_constraint and passes else
                       "Local joint demand exceeds the bound." if resource_constraint else
                       "The canonical task verdict is one." if passes else "The canonical task verdict is zero.",
            )
        if tree["complete"]:
            scope = ctx.ok(
                known, rule, policy=policy, queries=known, support=_support(pointer) + _support("/model"),
                detail="The scope is exactly all causal queries, or all terminal leaves, as declared.",
            )
        else:
            scope = ctx.block(
                "DEPENDENCY_BLOCKED", "HARD", policy=policy, queries=known, pointers=[pointer, "/model"],
                message="The complete constraint scope is unknown; known_scope retains legitimate built occurrences.",
            )
            ctx.check(
                rule, "UNDETERMINED", policy=policy, queries=known,
                support=_support(pointer) + _support("/model"), detail="Global scope coverage has not been established.",
            )
        if missing:
            ctx.diag(
                "HARD_UNDECIDED", "HARD", policy=policy, queries=missing,
                pointers=[pointer, "/resources" if resource_constraint else "/semantics"],
                message="These known constraint occurrences have no determined local judgement.",
            )
            ctx.check(
                rule, "UNDETERMINED", policy=policy, queries=missing,
                support=_support(pointer), detail="All missing local judgments are retained, including when another occurrence refutes the constraint.",
            )
        if violations:
            ctx.diag(
                "HARD_VIOLATION", "HARD", policy=policy, queries=violations, pointers=[pointer],
                message="The listed legitimate local witnesses refute the universal constraint.",
            )
            hard_value = ctx.ok(
                "0", rule, policy=policy, queries=violations,
                support=_support(pointer) + _support("/resources" if resource_constraint else "/semantics"),
                detail="A negative witness decides the hard judgement despite any other missing values or unknown scope.",
            )
        elif not tree["complete"]:
            hard_value = ctx.block(
                "DEPENDENCY_BLOCKED", "HARD", policy=policy, queries=missing, pointers=[pointer, "/model"],
                message="No negative witness is known and the universal scope is incomplete.",
            )
        elif missing:
            hard_value = ctx.out(
                "HARD_UNDECIDED", "HARD", rule, policy=policy, queries=missing, pointers=[pointer],
                message="The complete scope has missing local judgments and no negative witness.",
            )
        else:
            hard_value = ctx.ok(
                "1", rule, policy=policy, queries=known,
                support=_support(pointer) + _support("/resources" if resource_constraint else "/semantics"),
                detail="Every occurrence of the completely known scope has a positive local judgement.",
            )
        result.append({
            "constraint": constraint["id"], "value": hard_value, "scope": scope,
            "known_scope": known, "checked": checked, "violations": violations, "missing": missing,
        })
    ctx.guard("G13", _domain_summary([row["value"] for row in result]))
    return result


def evaluate(ctx, trees, structural_results):
    """Return the closed evidence/probability/hard fields for every policy."""
    references = {qkey(row["leaf"]): set(row["states"]) for row in ctx.data["semantics"]["references"]}
    task = {row["state"]: row["value"] for row in ctx.data["semantics"]["task"]}
    indexes = _causal_indexes(ctx.data)
    laws_by_policy = {policy: [] for policy in trees}
    for index, row in enumerate(ctx.data["law"]["rows"]):
        ctx.tick()
        laws_by_policy[row["query"]["policy"]].append((index, row))
    results = {}
    for policy, tree in trees.items():
        ctx.tick()
        evidence, verdicts = _semantic_evidence(ctx, tree, references, task, indexes)
        probability = _probability(ctx, tree, verdicts, laws_by_policy[policy], indexes)
        hard = _hard(ctx, tree, verdicts, structural_results[policy])
        results[policy] = {"evidence": evidence, "probability": probability, "hard": hard}
    return results
