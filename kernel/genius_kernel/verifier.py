"""Strict FP1 result and decisive-certificate verification against frozen bytes.

The full-result verifier shares the evaluator's pure mathematical constructors:
this is recomputation, NOT an independently implemented mathematical algorithm.
The closed wire grammar, proof-reference/DAG validation, digest binding, external
DECISIVE_SET admission, and mutation tests are separate verification work.
Operational exhaustion is INCOMPLETE (valid=None), never a false mathematical
rejection. A historical LIMITED/ERROR trace cannot be proved by rerunning time.
"""
from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
import hashlib
import json
import math
import re
import time

from .common import (Context, InputError, ComputationLimit, defined, qkey,
                     stable_key, validate_limits)
from . import output_schema as wire
from .output_schema import Rejected


def _answer(status, *errors):
    return {"valid": True if status == "VALID" else False if status == "INVALID" else None,
            "status": status, "errors": list(errors)}


def _signature(item, diagnostic=False):
    fields = ("code", "component") if diagnostic else ("rule", "outcome")
    return tuple(item[x] for x in fields) + tuple(
        tuple(sorted(stable_key(x) for x in item[k])) for k in ("policies", "queries", "points"))


def _resolve(root, path):
    if path == "":
        return root
    if not path.startswith("/"):
        raise Rejected("Invalid JSON Pointer: " + path)
    current = root
    for segment in path[1:].split("/"):
        if re.search(r"~(?![01])", segment):
            raise Rejected("Invalid JSON Pointer escape: " + path)
        key = segment.replace("~1", "/").replace("~0", "~")
        if type(current) is dict and key in current:
            current = current[key]
        elif type(current) is list and re.fullmatch(r"0|[1-9][0-9]*", key, re.ASCII):
            # Comparing decimal lengths avoids constructing an unbounded index.
            if len(key) > len(str(len(current))) or int(key) >= len(current):
                raise Rejected("JSON Pointer array index is absent: " + path)
            current = current[int(key)]
        else:
            raise Rejected("JSON Pointer does not resolve: " + path)
    return current


def _under(path, root):
    return path == root or path.startswith(root + "/")


# This is the constructor partial order of specification 05, not an arbitrary
# topological numbering: independent functional/CAG/welfare/evidence branches
# cannot justify each other merely because one happened to run first.
_CONSTRUCTOR_PARENTS = {
    "INPUT": set(), "INITIALIZATION": {"INPUT"},
    "CAUSAL": {"INITIALIZATION"}, "QUERY_REFERENCE": {"CAUSAL"},
    "PRESENTATION": {"QUERY_REFERENCE"}, "SCENARIOS": {"CAUSAL"},
    "FUNCTIONAL": {"CAUSAL"}, "REDUCTION": {"FUNCTIONAL"},
    "COMPOSITION": {"QUERY_REFERENCE"}, "RESOURCE": {"QUERY_REFERENCE"},
    "GEN_ORDER": {"INPUT"}, "GEN_TRANSLATION": {"CAUSAL", "GEN_ORDER"},
    "CAG": {"GEN_TRANSLATION"}, "WELFARE": {"QUERY_REFERENCE", "SCENARIOS"},
    "SEM": {"QUERY_REFERENCE"}, "DECISIVE": {"SEM"},
    "LAW_ROW": {"QUERY_REFERENCE"}, "LAW_MASS": {"LAW_ROW"},
    "PARTITION": {"DECISIVE"}, "VPROB": {"LAW_MASS", "PARTITION"},
    "HARD_RESOURCE": {"RESOURCE"}, "HARD_TASK": {"DECISIVE"},
    "PAIR": {"FUNCTIONAL", "CAG", "WELFARE", "VPROB", "SCENARIOS"},
    "FRONTIER": {"PAIR", "HARD_RESOURCE", "HARD_TASK", "PRESENTATION",
                 "REDUCTION", "COMPOSITION", "RESOURCE"},
    "SELECTION": {"FRONTIER"}, "INTEGRATION": {"SELECTION"},
}
_RULE_CONSTRUCTOR = {
    "INPUT_TYPES": "INPUT", "QUERY_REFERENCE": "QUERY_REFERENCE",
    "CAUSAL_NODE": "CAUSAL", "SCENARIO_MAP": "SCENARIOS",
    "CALIBRATION": "FUNCTIONAL", "FSUFF": "REDUCTION",
    "RELATIONAL_JOIN": "COMPOSITION", "RESOURCE_SUM": "RESOURCE",
    "GEN_ORDER": "GEN_ORDER", "GEN_TRANSLATION": "GEN_TRANSLATION",
    "CAG_RECIPE": "CAG", "WELFARE_COVERAGE": "WELFARE",
    "SEM_UNION": "SEM", "DECISIVE_SET": "DECISIVE", "LAW_ROW": "LAW_ROW",
    "LAW_MASS": "LAW_MASS", "VPROB": "VPROB",
    "HARD_RESOURCE": "HARD_RESOURCE", "HARD_TASK": "HARD_TASK",
    "PAIR_COMPARISON": "PAIR", "FRONTIER": "FRONTIER", "SELECTION": "SELECTION",
    **dict(zip((f"G{i:02}" for i in range(1, 16)),
               ("PRESENTATION", "INITIALIZATION", "CAUSAL", "SCENARIOS",
                "FUNCTIONAL", "REDUCTION", "COMPOSITION", "RESOURCE", "CAG",
                "WELFARE", "DECISIVE", "VPROB", "HARD", "PAIR", "FRONTIER"))),
}
_CONSTRUCTOR_PARENTS["HARD"] = {"HARD_RESOURCE", "HARD_TASK"}
_CONSTRUCTOR_PARENTS["FRONTIER"].add("HARD")


def _ancestors(constructor):
    result = set()
    pending = list(_CONSTRUCTOR_PARENTS[constructor])
    while pending:
        parent = pending.pop()
        if parent not in result:
            result.add(parent)
            pending.extend(_CONSTRUCTOR_PARENTS[parent])
    return result


_CONSTRUCTOR_ANCESTORS = {name: _ancestors(name) for name in _CONSTRUCTOR_PARENTS}


def _output_constructor(pointer, result):
    """Producer identity independent of array positions and generated IDs."""
    parts = pointer.split("/")
    if len(parts) > 2 and parts[1] == "checks":
        return _RULE_CONSTRUCTOR[result["checks"][int(parts[2])]["rule"]]
    if len(parts) > 3 and parts[1] == "policies":
        component = parts[3]
        rest = parts[4:]
        if component == "causal": return "SCENARIOS" if "scenarios" in rest else "CAUSAL"
        if component == "composition": return "COMPOSITION"
        if component == "resources": return "RESOURCE"
        if component == "functional": return "REDUCTION" if "reduction" in rest else "FUNCTIONAL"
        if component == "generative":
            return "GEN_TRANSLATION" if "origin" in rest or "identities" in rest else "CAG"
        if component == "welfare": return "WELFARE"
        if component == "evidence": return "SEM" if "sem" in rest else "DECISIVE"
        if component == "probability":
            return "LAW_MASS" if "masses" in rest else "PARTITION" if "partition" in rest else "VPROB"
        if component == "hard":
            # An entire hard table contains both supported constraint families.
            return "HARD"
    if len(parts) > 1 and parts[1] == "decision":
        return "PAIR" if "pairs" in parts else "SELECTION" if "selection" in parts else "FRONTIER"
    if len(parts) > 1 and parts[1] == "integration": return "INTEGRATION"
    if pointer in ("/input_digest", "/specification", "/format"): return "INPUT"
    return None


def _check_proof_references(data, result, grammar, ctx):
    checks = {c["id"]: c for c in result["checks"]}
    diagnostics = {d["id"]: d for d in result["diagnostics"]}
    for path, kind, ident in grammar.references:
        ctx.tick()
        domain = checks if kind == "CheckRef" else diagnostics
        if ident not in domain:
            raise Rejected(path + ": unknown " + kind + " " + ident)
    for path, cell in grammar.cells:
        if cell["state"] == "DEFINED":
            for ident in cell["checks"]:
                if checks[ident]["outcome"] != "PASS":
                    raise Rejected(path + ": DEFINED cell cites a non-PASS check")
    for diag in diagnostics.values():
        for ref in diag["input_refs"]:
            ctx.tick()
            if data is None:
                raise Rejected("An INPUT pointer cannot resolve in syntactically invalid bytes")
            _resolve(data, ref["pointer"])
    # Resolve first, then derive graph edges from all certified cells/checks
    # enclosing or contained in an OUTPUT target, including scalar descendants.
    # Referencing just one's own value instead of one's whole Cell is still a
    # circular justification and is rejected.
    graph = {ident: set() for ident in checks}
    paths = [(f"/checks/{i}", c["id"]) for i, c in enumerate(result["checks"])]
    cell_roles = {ident: set() for ident in checks}
    for path, cell in grammar.cells:
        role = _output_constructor(path, result)
        for ident in cell.get("checks", []):
            nominal = _RULE_CONSTRUCTOR[checks[ident]["rule"]]
            # VPROB is intentionally reused for the leaf partition and for
            # later masses/PVS. An attachment to the partition refines this
            # check's consumer role; it may not acquire future PVS support just
            # because the wire subtype spelling is shared.
            if role == nominal or role in _CONSTRUCTOR_ANCESTORS[nominal]:
                cell_roles[ident].add(role)
    for ident, check in checks.items():
        if not check["support"]:
            raise Rejected("Check " + ident + " has no reproducible support")
        for ref in check["support"]:
            ctx.tick()
            if ref["document"] == "INPUT":
                if data is None:
                    # Whole frozen bytes support INPUT_TYPES failure even when
                    # they do not parse into an object; no interior path exists.
                    if ref["pointer"] != "" or check["rule"] != "INPUT_TYPES" or check["outcome"] != "FAIL":
                        raise Rejected("INPUT pointer cannot resolve in invalid JSON")
                else:
                    _resolve(data, ref["pointer"])
                continue
            pointer = ref["pointer"]
            _resolve(result, pointer)
            producer = _output_constructor(pointer, result)
            consumers = cell_roles[ident] or {_RULE_CONSTRUCTOR[check["rule"]]}
            if any(producer != consumer and producer not in _CONSTRUCTOR_ANCESTORS[consumer]
                   for consumer in consumers):
                raise Rejected("OUTPUT support depends on a later or independent constructor: " + pointer)
            dependencies = set()
            for owner_path, cell in grammar.cells:
                ctx.tick()
                if _under(pointer, owner_path) or _under(owner_path, pointer):
                    dependencies.update(cell.get("checks", []))
            for owner_path, owner in paths:
                ctx.tick()
                if _under(pointer, owner_path) or _under(owner_path, pointer):
                    dependencies.add(owner)
            # A reference to an unannotated field of an earlier constructor is
            # admitted only if that component has a certified cell. Its cells
            # bind the producer, rather than allowing a bare assertion as proof.
            if not dependencies and pointer.startswith("/policies/"):
                parts = pointer.split("/")
                component = "/".join(parts[:4])
                for owner_path, cell in grammar.cells:
                    ctx.tick()
                    if _under(owner_path, component):
                        dependencies.update(cell.get("checks", []))
            if not dependencies and pointer not in ("/input_digest", "/specification", "/format"):
                raise Rejected("OUTPUT support does not identify a prior certified constructor: " + pointer)
            graph[ident].update(dependencies)
    # Iterative DFS also detects indirect cycles without spending Python stack.
    marks = {}
    for start in graph:
        if marks.get(start) == 2:
            continue
        stack = [(start, False)]
        while stack:
            ctx.tick()
            ident, leaving = stack.pop()
            if leaving:
                marks[ident] = 2
                continue
            if marks.get(ident) == 1:
                raise Rejected("Circular OUTPUT support involving " + ident)
            if marks.get(ident) == 2:
                continue
            marks[ident] = 1
            stack.append((ident, True))
            for child in graph[ident]:
                if child not in graph:
                    raise Rejected("Unresolved check in OUTPUT support")
                if marks.get(child) == 1:
                    raise Rejected("Circular OUTPUT support involving " + child)
                if marks.get(child) != 2:
                    stack.append((child, False))
    integration = result["integration"]
    if defined(integration):
        certificate = integration["value"]
        guards = [checks[g] for g in certificate["guards"]]
        if (len(guards) != 15 or {g["rule"] for g in guards} != {f"G{i:02}" for i in range(1, 16)}
                or any(g["outcome"] != "PASS" for g in guards)):
            raise Rejected("Integration must cite exactly one PASS summary for each G01-G15")
        selection = checks[certificate["selection_check"]]
        if selection["rule"] != "SELECTION" or selection["outcome"] != "PASS":
            raise Rejected("Integration selection_check must name SELECTION PASS")
    return checks, diagnostics


def _derive_read(data, trees, ctx, certificate):
    q = certificate["query"]
    pid, path = qkey(q)
    if pid not in trees:
        raise Rejected("Certificate Query refers to an unknown policy")
    tree = trees[pid]
    if path not in tree["node_map"]:
        raise Rejected("Certificate Query is not a constructed causal occurrence")
    # Causal constructor facts carry all action-domain and update obligations.
    # This permits a complete local subtree even if a sibling is incomplete.
    complete = ctx.facts["_causal"][pid]["subtree_complete"]
    if not complete.get(path, False):
        raise Rejected("Certificate requires a complete causal set of completions")
    references = {qkey(r["leaf"]): r["states"] for r in data["semantics"]["references"]}
    leaves, rows, states = [], [], set()
    for leaf_path, node in tree["node_map"].items():
        ctx.tick()
        if len(leaf_path) != ctx.H or leaf_path[:len(path)] != path:
            continue
        leaf = node["query"]
        semantic = references.get((pid, leaf_path))
        if not semantic:
            raise Rejected("A causal completion has no nonempty semantic reference")
        leaves.append(leaf)
        rows.append({"leaf": leaf, "states": semantic})
        states.update(semantic)
    if not leaves or not states:
        raise Rejected("A decisive certificate requires nonempty Sem")
    return {"leaves": leaves, "references": rows, "states": sorted(states)}


def _verify_decisive(data, certificate, read, ctx):
    # This function intentionally does not compare A to a canonical certificate.
    # It directly checks 04 section 4.2, so sound noncanonical supersets pass.
    actual_read = wire.Grammar(ctx).visit(certificate["read"], wire.READ)
    expected_read = wire.Grammar(ctx).visit(read, wire.READ)
    if actual_read != expected_read:
        raise Rejected("Certificate read differs from the exact causal completion union")
    semantic = set(read["states"])
    A = set(certificate["A"])
    task = {r["state"]: r["value"] for r in data["semantics"]["task"]}
    if not semantic or not semantic <= A:
        raise Rejected("Certificate requires nonempty Sem contained in A")
    if not A <= set(data["semantics"]["states"]) or not A <= task.keys():
        raise Rejected("Certificate A extends outside the declared semantic or full task domain")
    rows = {r["state"]: r["value"] for r in certificate["task_rows"]}
    if rows.keys() != A:
        raise Rejected("Certificate task_rows must cover exactly A")
    for state in A:
        ctx.tick()
        if rows[state] != task[state] or task[state] != certificate["value"]:
            raise Rejected("Certificate task rows are not the exact constant task image of A")


def _scoped_calibration_pass(item, data, expected_result, ctx):
    """Recompute a noncanonical local ordinal check, not a canonical alias.

    CALIBRATION on a declared reached scope means coverage of every measured
    raw in that scope and preservation/reflection on all its measured pairs.
    A missing measurement is separately a profile-domain issue; no raw value
    is fabricated. This admits an honest local PASS even when another point
    causes the common calibration to fail, without specializing that FAIL.
    """
    if (item["rule"] != "CALIBRATION" or item["outcome"] != "PASS"
            or data is None or expected_result is None
            or expected_result["presentation"] == "INVALID"):
        return None
    if not (item["policies"] or item["queries"] or item["points"]):
        return None  # An additional local claim must state its actual scope.
    policies = {row["policy"]: row for row in expected_result["policies"]}
    selected = set(item["policies"]) or set(policies)
    if not selected <= policies.keys():
        return None
    points_by_policy, locations = {}, {}
    for pid, policy in policies.items():
        points_by_policy[pid] = set()
        for node in policy["causal"]["nodes"]:
            ctx.tick()
            point = (node["t"], node["x"])
            points_by_policy[pid].add(point)
            locations[qkey(node["query"])] = point
    available = set().union(*(points_by_policy[pid] for pid in selected))
    scope = {(p["t"], p["x"]) for p in item["points"]}
    if not scope <= available:
        return None
    for q in item["queries"]:
        ctx.tick()
        key = qkey(q)
        if key not in locations or q["policy"] not in selected:
            return None
        scope.add(locations[key])
    if not item["queries"] and not item["points"]:
        # With only policy names the claim covers their complete reached
        # scope, which cannot be inferred from an unfinished causal tree.
        if any(not defined(policies[pid]["causal"]["complete"]) for pid in selected):
            return None
        scope = available
    if not scope or (item["policies"] and any(
            not points_by_policy[pid].intersection(scope) for pid in selected)):
        return None
    measurements = {}
    for row in data["functional"]["measurements"]:
        ctx.tick()
        measurements[row["t"], row["x"], row["index"]] = Fraction(row["raw"])
    for index in data["functional"]["indices"]:
        calibration = {}
        for row in index["calibration"]:
            ctx.tick()
            calibration[Fraction(row["raw"])] = Fraction(row["value"])
        raws = set()
        for t, x in scope:
            ctx.tick()
            raw = measurements.get((t, x, index["id"]))
            if raw is not None:
                if raw not in calibration:
                    return None
                raws.add(raw)
        for left in raws:
            for right in raws:
                ctx.tick()
                if (left <= right) != (calibration[left] <= calibration[right]):
                    return None
    return frozenset(stable_key({"t": t, "x": x}) for t, x in scope)


def _check_maps(actual, expected, diagnostic, ctx, *, data=None, expected_result=None):
    expected_signatures = {_signature(item, diagnostic) for item in expected}
    mapping = {}
    for item in actual:
        ctx.tick()
        signature = _signature(item, diagnostic)
        if signature in expected_signatures:
            mapping[item["id"]] = frozenset([signature])
            continue
        if not diagnostic and item["rule"] == "CALIBRATION" and item["outcome"] == "PASS":
            scope = _scoped_calibration_pass(item, data, expected_result, ctx)
            if scope is None:
                raise Rejected("Check " + item["id"] + " has an unproved local calibration or invalid reached scope")
            # Retain the actual local signature. Mapping it to a larger
            # canonical signature would unsoundly widen its proof coverage.
            mapping[item["id"]] = frozenset([signature])
            ctx.facts.setdefault("_verified_extra_checks", set()).add(signature)
            ctx.facts.setdefault("_local_calibration_scopes", {})[signature] = scope
            continue
        # Scopes may aggregate independently recomputed obligations with the
        # same rule/outcome (or diagnostic class); no arbitrary prose is used.
        parts = [set(component) for component in signature[2:]]
        candidates = []
        unions = [set(), set(), set()]
        for old in expected_signatures:
            ctx.tick()
            if old[:2] != signature[:2]:
                continue
            scopes = [set(component) for component in old[2:]]
            if all(s <= p for s, p in zip(scopes, parts)) and any(scopes):
                candidates.append(old)
                for union, scope in zip(unions, scopes):
                    union.update(scope)
        if not candidates or unions != parts:
            label = "Diagnostic" if diagnostic else "Check"
            raise Rejected(label + " " + item["id"] + " has a false, out-of-scope, or unsupported rule/outcome claim")
        mapping[item["id"]] = frozenset(candidates)
    return mapping


def _entails(actual, needed):
    if actual == needed:
        return True
    if actual[:2] != needed[:2]:
        return False
    # A failed universal check only establishes some counterexample in its
    # scope; it cannot be specialized to an arbitrary contained occurrence.
    if actual[1] != "PASS":
        return False
    # Empty scopes on a global summary cannot be discharged by a local check.
    if not any(needed[2:]):
        return not any(actual[2:])
    return all(set(n) <= set(a) for a, n in zip(actual[2:], needed[2:]))


def _prerequisite(actual, needed, ctx):
    """Recognize a redundant true ancestor claim, without using it as proof
    of the cell's specific operation. Both claims were independently matched
    to recomputation; explicit scopes must describe a relevant occurrence.
    """
    if actual[1] != "PASS":
        return False
    source = _RULE_CONSTRUCTOR[actual[0]]
    destination = _RULE_CONSTRUCTOR[needed[0]]
    if source not in _CONSTRUCTOR_ANCESTORS[destination]:
        return False
    aq, nq = ([json.loads(q) for q in signature[3]] for signature in (actual, needed))
    ap = {json.loads(p) for p in actual[2]} | {q["policy"] for q in aq}
    np = {json.loads(p) for p in needed[2]} | {q["policy"] for q in nq}
    if ap and np and not ap.intersection(np):
        return False
    if aq and nq:
        related = False
        for left in aq:
            for right in nq:
                ctx.tick()
                prefix = min(len(left["path"]), len(right["path"]))
                if left["policy"] == right["policy"] and left["path"][:prefix] == right["path"][:prefix]:
                    related = True
        if not related:
            return False
    locations = ctx.facts.get("_verify_query_points", {})
    a_points = set(actual[4]) | {locations[q] for q in actual[3] if q in locations}
    n_points = set(needed[4]) | {locations[q] for q in needed[3] if q in locations}
    # Different times along a related causal prefix are legitimate prerequisites;
    # explicit point-only claims instead need a point within the target scope.
    if (actual[4] and not aq and n_points and not a_points.intersection(n_points)):
        return False
    if (needed[4] and not nq and a_points and not a_points.intersection(n_points)):
        return False
    return True


def _supplementary_local_calibration(actual, needed, ctx):
    """A proved local subcheck may accompany, never replace, a larger proof."""
    scopes = ctx.facts.get("_local_calibration_scopes", {})
    if actual not in scopes or actual[:2] != needed[:2]:
        return False
    required_points = set(needed[4])
    locations = ctx.facts.get("_verify_query_points", {})
    required_points.update(locations[q] for q in needed[3] if q in locations)
    if not required_points or not scopes[actual] <= required_points:
        return False
    if needed[2] and actual[2] and not set(actual[2]) <= set(needed[2]):
        return False
    return True


def _admit_cell_proofs(actual, expected, spec, checks, expected_checks, ctx):
    """A sound broader obligation may support any contained object scope.

    After checking implication, use internal aliases to the required claims for
    normalization. These aliases are never emitted as wire IDs. This avoids
    accidentally treating the generator's choice of Check ID as contractual.
    """
    ctx.tick()
    if isinstance(spec, dict):
        if spec in (wire.CHECK, wire.DIAGNOSTIC):
            return
        for key, desc in spec.items():
            if spec is wire.RESULT and key in ("checks", "diagnostics"):
                continue
            _admit_cell_proofs(actual[key], expected[key], desc, checks, expected_checks, ctx)
        return
    if not isinstance(spec, tuple):
        return
    kind = spec[0]
    if kind == "cell":
        if actual["state"] != expected["state"]:
            return  # Mathematical comparison reports this domain mismatch.
        if "checks" in actual:
            got = {s for ident in actual["checks"] for s in checks[ident]}
            needed = {s for ident in expected["checks"] for s in expected_checks[ident]}
            if any(not any(_entails(a, n) for a in got) for n in needed):
                raise Rejected("Cell lacks checks proving the recomputed rule and scope")
            if any(not any(_entails(a, n) or _prerequisite(a, n, ctx)
                           or _supplementary_local_calibration(a, n, ctx)
                           for n in needed) for a in got):
                raise Rejected("Cell cites a check unrelated to its recomputed rule and scope")
            aliases = []
            for signature in needed:
                # Leading underscore is outside wire ID grammar, so it cannot
                # collide with a supplied generated identifier.
                alias = "_verified_" + str(len(checks))
                checks[alias] = frozenset([signature])
                aliases.append(alias)
            actual["checks"] = aliases
        if defined(actual):
            _admit_cell_proofs(actual["value"], expected["value"], spec[1], checks, expected_checks, ctx)
    elif kind == "table":
        keys = spec[2]
        reference = {stable_key([row[k] for k in keys]): row for row in expected}
        for row in actual:
            ctx.tick()
            other = reference.get(stable_key([row[k] for k in keys]))
            if other is not None:
                _admit_cell_proofs(row, other, spec[1], checks, expected_checks, ctx)
    elif kind == "list":
        for a, e in zip(actual, expected):
            _admit_cell_proofs(a, e, spec[1], checks, expected_checks, ctx)
    elif kind == "nullable" and actual is not None and expected is not None:
        _admit_cell_proofs(actual, expected, spec[1], checks, expected_checks, ctx)


def _normal(obj, spec, checks, diagnostics, ctx):
    ctx.tick()
    if isinstance(spec, dict):
        if spec is wire.CHECK:
            return sorted(checks[obj["id"]], key=stable_key)
        if spec is wire.DIAGNOSTIC:
            return sorted(diagnostics[obj["id"]], key=stable_key)
        result = {key: _normal(obj[key], desc, checks, diagnostics, ctx) for key, desc in spec.items()}
        if spec is wire.DECISIVE:
            result["id"] = "certificate"
            states = set(obj["read"]["states"])
            result["A"] = sorted(states)
            result["task_rows"] = sorted([row for row in obj["task_rows"] if row["state"] in states], key=stable_key)
        if spec is wire.INTEGRATION:
            result["id"] = "integration"
        if spec is wire.RESULT:
            # Operational settings describe this execution. They do not change
            # the frozen problem and cannot make an incorrect value correct.
            result["execution"]["limits"] = []
            result["checks"] = sorted({stable_key(s) for item in obj["checks"] for s in checks[item["id"]]})
            result["diagnostics"] = sorted({stable_key(s) for item in obj["diagnostics"] for s in diagnostics[item["id"]]})
        return result
    if isinstance(spec, tuple):
        kind = spec[0]
        if kind == "enum": return obj
        if kind == "nullable": return None if obj is None else _normal(obj, spec[1], checks, diagnostics, ctx)
        if kind == "cell":
            result = {"state": obj["state"]}
            if defined(obj):
                result["value"] = _normal(obj["value"], spec[1], checks, diagnostics, ctx)
            if "checks" in obj:
                result["checks"] = sorted({stable_key(s) for ident in obj["checks"] for s in checks[ident]})
            if "reasons" in obj:
                result["reasons"] = sorted({stable_key(s) for ident in obj["reasons"] for s in diagnostics[ident]})
            return result
        values = [_normal(x, spec[1], checks, diagnostics, ctx) for x in obj]
        # Repeated semantic claims with different generated identifiers are not
        # new obligations, while grammar already rejects duplicate wire IDs.
        if kind == "set" and spec[1] in ("CheckRef", "DiagnosticRef"):
            return sorted({stable_key(s) for v in values for s in v})
        return values if kind == "list" else sorted(values, key=stable_key)
    if spec == "CheckRef": return sorted(checks[obj], key=stable_key)
    if spec == "DiagnosticRef": return sorted(diagnostics[obj], key=stable_key)
    return obj


def _first_difference(actual, expected, path=""):
    if type(actual) is not type(expected):
        return path or "/"
    if isinstance(actual, dict):
        if actual.keys() != expected.keys(): return path or "/"
        for key in actual:
            found = _first_difference(actual[key], expected[key], wire.pointer(path, key))
            if found: return found
    elif isinstance(actual, list):
        if len(actual) != len(expected): return path or "/"
        for i, (left, right) in enumerate(zip(actual, expected)):
            found = _first_difference(left, right, wire.pointer(path, i))
            if found: return found
    elif actual != expected:
        return path or "/"
    return None


def _bounded_recompute(raw, limits, ctx):
    from .engine import evaluate
    remaining = dict(limits)
    if "max_operations" in remaining:
        # The evaluator owns its own counter. Reserve and charge its entire
        # allowance so the two stages cannot each spend the full user budget.
        remaining["max_operations"] = max(0, (remaining["max_operations"] - ctx.operations) // 2)
    if "max_seconds" in remaining:
        # Keep one wall-clock deadline, not a fresh budget per stage. The engine
        # accepts integral bounds; the shared deadline is checked immediately
        # after it returns, and a late result is always inconclusive.
        remaining["max_seconds"] = max(0, math.ceil(remaining["max_seconds"] - (time.monotonic() - ctx.started)))
    recomputed = evaluate(raw, remaining)
    if "max_operations" in remaining:
        ctx.operations += remaining["max_operations"]
    ctx.tick()
    if recomputed["execution"]["status"] != "COMPLETE":
        raise ComputationLimit("recomputation_" + recomputed["execution"]["status"].lower())
    return recomputed


def verify_result(raw: bytes, result: dict, limits=None):
    """Verify a full specification-06 Result; never trust its PASS assertions."""
    try:
        if not isinstance(raw, bytes):
            raise Rejected("Verification requires the original immutable UTF-8 bytes")
        limits = validate_limits(limits)
        ctx = Context({}, raw, limits)
        grammar = wire.Grammar(ctx)
        grammar.visit(result, wire.RESULT)
        if result["input_digest"] != hashlib.sha256(raw).hexdigest():
            raise Rejected("Result input_digest differs from the exact input bytes")
        declared = {row["name"]: int(row["bound"]) for row in result["execution"]["limits"]}
        expanded = int(result["execution"]["progress"]["expanded_nodes"])
        if "max_nodes" in declared and expanded > declared["max_nodes"]:
            raise Rejected("Reported expanded_nodes exceeds the reported operational max_nodes bound")
        if result["execution"]["status"] == "COMPLETE" and any(
                declared.get(name) == 0 for name in ("max_operations", "max_seconds")):
            raise Rejected("A COMPLETE result contradicts a reported zero operational execution bound")
        if (result["execution"]["status"] == "COMPLETE" and "max_input_bytes" in declared
                and len(raw) > declared["max_input_bytes"]):
            raise Rejected("A COMPLETE result contradicts its reported max_input_bytes bound")
        from . import schema
        data = None
        try:
            data = schema.parse(raw, limits)
        except InputError:
            pass  # A truthful INVALID result is itself verifiable.
        if (data is not None and result["execution"]["status"] == "COMPLETE"
                and "max_integer_digits" in declared):
            # This bound is applied by the input scalar constructors. Recheck
            # their actual visitation order: a structural error encountered
            # before a long number can legitimately finish INVALID.
            prior_limits, prior_data = ctx.limits, ctx.data
            digit_bound = min(declared["max_integer_digits"],
                              prior_limits.get("max_integer_digits", declared["max_integer_digits"]))
            ctx.limits = {**prior_limits, "max_integer_digits": digit_bound}
            ctx.data = data
            try:
                schema.validate(ctx)
            except InputError:
                pass
            except ComputationLimit as exc:
                if exc.name == "max_integer_digits" and digit_bound == declared["max_integer_digits"]:
                    raise Rejected("A COMPLETE result contradicts its reported integer digit bound") from exc
                raise
            finally:
                ctx.limits, ctx.data = prior_limits, prior_data
        _check_proof_references(data, result, grammar, ctx)
        if result["presentation"] == "INVALID":
            if result["policies"] or result["decision"]["state"] != "BLOCKED" or result["integration"]["state"] != "BLOCKED":
                raise Rejected("INVALID presentation must have no policy conclusions and blocked decision/integration")
        if result["execution"]["status"] in ("LIMITED", "ERROR"):
            if defined(result["integration"]):
                raise Rejected("An interrupted execution cannot certify integration")
            if defined(result["decision"]) and defined(result["decision"]["value"]["selection"]):
                raise Rejected("An interrupted execution cannot select a policy")
            return _answer("INCOMPLETE", "Interrupted execution has no independently reproducible complete result")
        expected = _bounded_recompute(raw, limits, ctx)
        # Validate the constructor's wire shape too: an implementation error is
        # never promoted to a trustworthy canonical oracle by comparison.
        expected_grammar = wire.Grammar(ctx)
        expected_grammar.visit(expected, wire.RESULT)
        _check_proof_references(data, expected, expected_grammar, ctx)
        expected_policies = {row["policy"]: row for row in expected["policies"]}
        for path, certificate in grammar.certificates:
            pid, query_path = qkey(certificate["query"])
            policy = expected_policies.get(pid)
            evidence = None if policy is None else next((row for row in policy["evidence"] if qkey(row["query"])[1] == query_path), None)
            if evidence is None or not defined(evidence["sem"]):
                raise Rejected(path + ": certificate has no completely derived semantic read")
            _verify_decisive(data, certificate, evidence["sem"]["value"], ctx)
        candidate = deepcopy(result)
        if defined(candidate["decision"]) and defined(expected["decision"]):
            expected_dominators = {row["policy"]: set(row["by"]) for row in expected["decision"]["value"]["dominators"]}
            for row in candidate["decision"]["value"]["dominators"]:
                ctx.tick()
                allowed = expected_dominators.get(row["policy"], set())
                if not row["by"] or not set(row["by"]) <= allowed:
                    raise Rejected("Dominator witness is not a strict dominator in the entire candidate set")
                row["by"] = sorted(allowed)
        checks = _check_maps(candidate["checks"], expected["checks"], False, ctx,
                             data=data, expected_result=expected)
        diagnostics = _check_maps(candidate["diagnostics"], expected["diagnostics"], True, ctx)
        expected_checks = {c["id"]: frozenset([_signature(c)]) for c in expected["checks"]}
        expected_diags = {d["id"]: frozenset([_signature(d, True)]) for d in expected["diagnostics"]}
        ctx.facts["_verify_query_points"] = {
            stable_key(node["query"]): stable_key({"t": node["t"], "x": node["x"]})
            for policy in expected["policies"] for node in policy["causal"]["nodes"]}
        _admit_cell_proofs(candidate, expected, wire.RESULT, checks, expected_checks, ctx)
        actual_math = _normal(candidate, wire.RESULT, checks, diagnostics, ctx)
        expected_math = _normal(expected, wire.RESULT, expected_checks, expected_diags, ctx)
        # Expected canonical obligations are all still required. Independently
        # recomputed local additions extend the inventory only by their own
        # exact signatures; none is treated as a full-scope summary.
        expected_math["checks"] = sorted(set(expected_math["checks"]) | {
            stable_key(signature) for signature in ctx.facts.get("_verified_extra_checks", ())})
        difference = _first_difference(actual_math, expected_math)
        if difference:
            raise Rejected("Recomputed output differs at " + difference + " (unordered tables shown in normalized order)")
        return _answer("VALID")
    except (ComputationLimit, RecursionError, MemoryError) as exc:
        return _answer("INCOMPLETE", "Verification could not finish: " + str(exc))
    except (Rejected, InputError, ValueError, TypeError, KeyError) as exc:
        return _answer("INVALID", str(exc))
    except Exception as exc:
        return _answer("INCOMPLETE", "Verifier internal error: " + type(exc).__name__ + ": " + str(exc))


def verify_decisive_certificate(raw: bytes, envelope: dict, limits=None):
    """Admit exactly sound DECISIVE_SET payloads, including A ⊋ Sem supersets."""
    try:
        if not isinstance(raw, bytes):
            raise Rejected("Certificate requires its original immutable input bytes")
        limits = validate_limits(limits)
        ctx = Context({}, raw, limits)
        wire.Grammar(ctx).visit(envelope, wire.ENVELOPE)
        if envelope["input_digest"] != hashlib.sha256(raw).hexdigest():
            raise Rejected("Certificate digest differs from exact input bytes")
        from . import schema, causal
        ctx.data = schema.parse(raw, limits)
        schema.validate(ctx)
        ctx.H = int(ctx.data["meta"]["horizon"])
        trees = causal.build_trees(ctx)
        causal.validate_queries(ctx, trees)
        certificate = envelope["certificate"]
        read = _derive_read(ctx.data, trees, ctx, certificate)
        _verify_decisive(ctx.data, certificate, read, ctx)
        return _answer("VALID")
    except (ComputationLimit, RecursionError, MemoryError) as exc:
        return _answer("INCOMPLETE", "Certificate verification could not finish: " + str(exc))
    except (Rejected, InputError, ValueError, TypeError, KeyError) as exc:
        return _answer("INVALID", str(exc))
    except Exception as exc:
        return _answer("INCOMPLETE", "Verifier internal error: " + type(exc).__name__ + ": " + str(exc))
