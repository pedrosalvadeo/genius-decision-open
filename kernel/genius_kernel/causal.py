"""Occurrence-preserving finite causal trees and actual exogenous scenarios."""
from __future__ import annotations

from .common import InputError, query, defined


def _input_ref(pointer):
    return {"document": "INPUT", "pointer": pointer}


def build_trees(ctx) -> dict:
    d, H = ctx.data, ctx.H
    model = d["model"]
    executable = {(r["t"], r["x"]): (r, j) for j, r in enumerate(model["executable"])}
    admissible = {(r["t"], r["x"]): (r, j) for j, r in enumerate(model["admissible"])}
    transitions = {(r["t"], r["x"], r["a"]): (r, j) for j, r in enumerate(model["transitions"])}
    updates = {(r["t"], r["i"], r["a"], r["y"]): (r, j) for j, r in enumerate(model["updates"])}
    trees = {}
    causal_facts = ctx.facts.setdefault("_causal", {})

    for policy_index, policy in enumerate(d["policies"]):
        ctx.tick()
        pid = policy["id"]
        policy_pointer = "/policies/" + str(policy_index)
        decisions = {(r["t"], r["i"]): (r, j) for j, r in enumerate(policy["decisions"])}
        nodes, node_map, words, leaves = [], {}, {}, []
        failures, failure_checks = [], []
        continuation, branch_support = {}, {}
        pending = [((), d["initialization"]["x0"], d["initialization"]["i0"], ())]

        def failed(code, q, pointers, message):
            cell = ctx.out(code, "CAUSAL", "CAUSAL_NODE", policy=pid,
                           queries=[q], pointers=pointers, message=message)
            failures.extend(cell["reasons"])
            failure_checks.extend(cell["checks"])
            return cell

        while pending:
            ctx.node_tick()
            path, x, info, uword = pending.pop()
            t = len(path)
            ts = str(t)
            q = query(pid, path)
            node = {"query": q, "t": ts, "x": x, "i": info,
                    "action": None, "outcomes": []}
            nodes.append(node)
            node_map[path] = node
            if t == H:
                node["action"] = ctx.out("TERMINAL_NO_ACTION", "CAUSAL", "CAUSAL_NODE",
                    policy=pid, queries=[q], pointers=["/meta/horizon"],
                    message="Terminal node has no policy-action domain at H")
                leaves.append(q)
                words[path] = uword
                continuation[path] = True
                branch_support[path] = set()
                ctx.check("CAUSAL_NODE", "PASS", policy=pid, queries=[q],
                          detail="Legitimate occurrence at the declared horizon")
                continue

            decision = decisions.get((ts, info))
            action = decision[0]["a"] if decision else None
            if decision is None:
                node["action"] = failed("POLICY_MISSING", q, [policy_pointer + "/decisions"],
                    "Policy has no decision at this time and information")
            else:
                node["action"] = ctx.ok(action, "CAUSAL_NODE", policy=pid, queries=[q],
                    support=[_input_ref(policy_pointer + "/decisions/" + str(decision[1]))],
                    detail="Action is exactly the tabulated pi(t,i)")

            local_valid = decision is not None
            for kind, table, bad in (("executable", executable, "ACTION_NOT_EXECUTABLE"),
                                     ("admissible", admissible, "ACTION_NOT_ADMISSIBLE")):
                row = table.get((ts, x))
                if row is None:
                    failed("ACTION_DOMAIN_MISSING", q, ["/model/" + kind],
                           "Missing local " + kind + " action-domain row")
                    local_valid = False
                elif action is not None and action not in row[0]["actions"]:
                    failed(bad, q, ["/model/" + kind + "/" + str(row[1])],
                           "The policy action is outside the local " + kind + " set")
                    local_valid = False

            transition = transitions.get((ts, x, action)) if action is not None else None
            branch_support[path] = (None if transition is None else
                                    {o["branch"] for o in transition[0]["outcomes"]})
            if action is not None:
                if transition is None:
                    failed("TRANSITION_MISSING", q, ["/model/transitions"],
                           "The policy action has no tabulated causal transition row")
                    local_valid = False
                elif not transition[0]["outcomes"]:
                    failed("TRANSITION_EMPTY", q, ["/model/transitions/" + str(transition[1])],
                           "Empty transition row cannot terminate a node before H")
                    local_valid = False

            # Specification 05 step 2 and 03 section 4: unaccredited actions
            # preserve the known prefix, but do not create legitimate children.
            # Their tabulated branch support remains available for reference
            # validation, without treating an unavailable child as a leaf.
            continuation[path] = local_valid
            if not local_valid:
                continue

            children = []
            for outcome_index, outcome in enumerate(transition[0]["outcomes"]):
                ctx.tick()
                child_path = path + (outcome["branch"],)
                child_query = query(pid, child_path)
                update = updates.get((ts, info, action, outcome["y"]))
                outcome_pointer = "/model/transitions/" + str(transition[1]) + "/outcomes/" + str(outcome_index)
                if update is None:
                    next_info = failed("UPDATE_MISSING", q, [outcome_pointer, "/model/updates"],
                        "No information update for outcome branch " + outcome["branch"])
                    continuation[path] = False
                else:
                    next_info = ctx.ok(update[0]["next_i"], "CAUSAL_NODE", policy=pid,
                        queries=[q, child_query],
                        support=[_input_ref(outcome_pointer), _input_ref("/model/updates/" + str(update[1]))],
                        detail="Successor information is exactly U(t,i,a,y)")
                    children.append((child_path, outcome["next_x"], update[0]["next_i"], uword + (outcome["u"],)))
                node["outcomes"].append({"branch": outcome["branch"], "u": outcome["u"],
                    "next_x": outcome["next_x"], "y": outcome["y"],
                    "next_i": next_info, "child": child_query})
            pending.extend(reversed(children))
            if continuation[path]:
                ctx.check("CAUSAL_NODE", "PASS", policy=pid, queries=[q],
                          detail="All local action, transition and update obligations hold")

        complete = not failures
        if complete:
            complete_cell = ctx.ok("1", "CAUSAL_NODE", policy=pid,
                queries=[n["query"] for n in nodes],
                detail="Every required occurrence expanded with all branches to H")
        else:
            complete_cell = {"state": "OUTSIDE_DOMAIN", "reasons": failures,
                             "checks": failure_checks}
        ctx.guard("G03", complete)

        scenario_map = {scenario["id"]: None for scenario in d["scenarios"]}
        if not complete:
            scenario_cell = ctx.block("DEPENDENCY_BLOCKED", "CAUSAL", policy=pid,
                pointers=["/scenarios", "/model"],
                message="Complete leaf image is unavailable for scenario correspondence")
            ctx.check("SCENARIO_MAP", "UNDETERMINED", policy=pid,
                      detail="Incomplete causal tree does not determine all scenario fibers")
            ctx.guard("G04", None)
        else:
            fibers = {}
            for path, word in words.items():
                ctx.tick()
                fibers.setdefault(word, []).append(path)
            declared = {tuple(s["inputs"]) for s in d["scenarios"]}
            image_ok = set(fibers) == declared
            multiple = {word: paths for word, paths in fibers.items() if len(paths) != 1}
            scenario_failures, scenario_checks = [], []
            if not image_ok:
                cell = ctx.out("SCENARIO_COVERAGE", "CAUSAL", "SCENARIO_MAP", policy=pid,
                    queries=leaves, pointers=["/scenarios", "/model/transitions"],
                    message="Actual exogenous leaf words differ from the declared scenario set")
                scenario_failures.extend(cell["reasons"])
                scenario_checks.extend(cell["checks"])
            if multiple:
                cell = ctx.out("SCENARIO_MULTIPLE", "CAUSAL", "SCENARIO_MAP", policy=pid,
                    queries=[query(pid, path) for paths in multiple.values() for path in paths],
                    pointers=["/scenarios", "/model/transitions"],
                    message="Distinct causal leaves share one actual exogenous word")
                scenario_failures.extend(cell["reasons"])
                scenario_checks.extend(cell["checks"])
            for scenario in d["scenarios"]:
                paths = fibers.get(tuple(scenario["inputs"]), [])
                if len(paths) == 1:
                    scenario_map[scenario["id"]] = paths[0]
            scenarios_ok = image_ok and not multiple
            if scenarios_ok:
                scenario_cell = ctx.ok([{"scenario": s["id"], "leaf": query(pid, scenario_map[s["id"]])}
                    for s in d["scenarios"]], "SCENARIO_MAP", policy=pid, queries=leaves,
                    detail="Declared exogenous words have exactly one actual leaf each")
            else:
                scenario_cell = {"state": "OUTSIDE_DOMAIN", "reasons": scenario_failures,
                                 "checks": scenario_checks}
            ctx.guard("G04", scenarios_ok)

        causal = {"complete": complete_cell, "nodes": nodes,
                  "leaves": leaves, "scenarios": scenario_cell}
        trees[pid] = {"policy": pid, "nodes": nodes, "node_map": node_map,
                      "complete": complete, "scenario_map": scenario_map,
                      "words": words, "causal": causal}
        subtree_complete = {}
        for node in reversed(nodes):
            ctx.tick()
            path = tuple(node["query"]["path"])
            subtree_complete[path] = continuation[path] and (
                len(path) == H or all(subtree_complete.get(tuple(e["child"]["path"]), False)
                                     for e in node["outcomes"]))
        causal_facts[pid] = {"continuation": continuation,
                             "branch_support": branch_support,
                             "subtree_complete": subtree_complete}
    return trees


def validate_queries(ctx, trees) -> bool:
    """Resolve every supplied Query after causal construction, without guesses.

    A known row excludes labels not in its support even in an incomplete tree.
    An unknown policy/update/continuation cannot prove that a named child exists
    or does not exist, and remains explicitly unresolved.
    """
    resolved = True
    for q, pointer, kind in ctx.facts.get("_query_references", []):
        ctx.tick()
        pid, path = q["policy"], tuple(q["path"])
        tree = trees[pid]
        if path in tree["node_map"]:
            ctx.check("QUERY_REFERENCE", "PASS", policy=pid, queries=[q],
                      support=[_input_ref(pointer)], detail="Query names a constructed legitimate occurrence")
            continue
        support = ctx.facts["_causal"][pid]["branch_support"]
        prefix = ()
        impossible = False
        for branch in path:
            ctx.tick()
            branches = support.get(prefix)
            if branches is not None and branch not in branches:
                impossible = True
                break
            prefix += (branch,)
            if prefix not in tree["node_map"]:
                break
        if impossible or tree["complete"]:
            raise InputError("UNKNOWN_REFERENCE", pointer,
                             "Query follows a branch proved absent from its causal row")
        resolved = False
        ctx.diag("QUERY_UNRESOLVED", "INPUT", policy=pid, queries=[q], pointers=[pointer],
                 message="Causal incompleteness prevents resolving this supplied Query")
        ctx.check("QUERY_REFERENCE", "UNDETERMINED", policy=pid, queries=[q],
                  support=[_input_ref(pointer)], detail="Reference cannot be resolved from known causal prefixes")
    return resolved
