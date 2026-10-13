"""Exact FP1 functionality, composition, resources, CAG, and welfare.

Only immutable input tables and causal occurrences are consumed here.  Shared
comparison guards are applied separately, after the engine has established B0.
"""

from copy import deepcopy
from fractions import Fraction

from .common import defined, point, qkey, qstr, query, value


def _support(pointer):
    return [{"document": "INPUT", "pointer": pointer}]


def _points(tree):
    return sorted({(int(n["t"]), n["x"]) for n in tree["nodes"]})


def _point_wire(points):
    return [point(t, x) for t, x in points]


def _conjunction(values):
    """Three-valued conjunction of independently checked obligations."""
    vals = list(values)
    if False in vals:
        return False
    return None if None in vals else True


def _issues_cell(ctx, issues, component, rule, *, policy=None, blocked=False):
    """Retain every missing location and every enumerated failure witness."""
    reasons, checks = [], []
    for issue in issues:
        ctx.tick()
        kwargs = dict(policy=policy, queries=issue.get("queries", ()),
                      points=issue.get("points", ()),
                      pointers=issue.get("pointers", ()),
                      message=issue.get("message", ""))
        cell = (ctx.block(issue["code"], component, **kwargs) if blocked else
                ctx.out(issue["code"], component, rule, **kwargs))
        reasons.extend(cell["reasons"])
        checks.extend(cell.get("checks", ()))
    if blocked:
        return {"state": "BLOCKED", "reasons": list(dict.fromkeys(reasons))}
    return {"state": "OUTSIDE_DOMAIN", "reasons": list(dict.fromkeys(reasons)),
            "checks": list(dict.fromkeys(checks))}


def _dependency(ctx, component, policy, message):
    return ctx.block("DEPENDENCY_BLOCKED", component, policy=policy,
                     message=message)


def _scenario_failure(ctx, component, policy):
    return ctx.out("SCENARIO_COVERAGE", component, "SCENARIO_MAP", policy=policy,
                   pointers=("/scenarios",),
                   message="The complete tree has no certified scenario bijection.")


def _calibration(ctx, cache, scope, *, policy=None):
    """Order reflection on all measured raws in an explicit reached scope.

    An absent nonterminal measurement is a profile-domain failure, not an
    invented raw value.  Every raw actually present is checked, including raws
    at nonterminal points and raws whose calibration is absent.
    """
    missing, invalid = [], []
    for index in cache["indices"]:
        idx = index["id"]
        cal = cache["calibrations"][idx]
        locations = {}
        for p in scope:
            ctx.tick()
            raw = cache["measurements"].get((p[0], p[1], idx))
            if raw is not None:
                locations.setdefault(raw, []).append(point(*p))
        for raw, points in locations.items():
            ctx.tick()
            if raw not in cal:
                missing.append({"code": "CALIBRATION_MISSING", "points": points,
                                "pointers": ["/functional"],
                                "message": f"Index {idx}: raw {qstr(raw)} has no calibration."})
        known = sorted(raw for raw in locations if raw in cal)
        for a in known:
            for b in known:
                ctx.tick()
                if (a <= b) != (cal[a] <= cal[b]):
                    invalid.append({"code": "CALIBRATION_ORDER",
                                    "points": locations[a] + locations[b]
                                    if a != b else locations[a],
                                    "pointers": ["/functional"],
                                    "message": f"Index {idx}: order differs for raws {qstr(a)}, {qstr(b)} and values {qstr(cal[a])}, {qstr(cal[b])}."})
    good = not missing and not invalid
    ctx.check("CALIBRATION", "PASS" if good else "FAIL", policy=policy,
              points=_point_wire(scope), support=_support("/functional"),
              detail="Coverage and both directions of order on all reached measured raw pairs.")
    return {"ok": good, "missing": missing, "invalid": invalid}


def _profiles(ctx, cache, points):
    profiles = {}
    for p in points:
        ctx.tick()
        vector, issues = [], []
        for index in cache["indices"]:
            ctx.tick()
            idx = index["id"]
            raw = cache["measurements"].get((p[0], p[1], idx))
            if raw is None:
                issues.append({"code": "FUNCTION_MISSING", "points": [point(*p)],
                               "pointers": ["/functional/measurements"],
                               "message": f"Missing measurement for functional index {idx}."})
            elif raw not in cache["calibrations"][idx]:
                issues.append({"code": "CALIBRATION_MISSING", "points": [point(*p)],
                               "pointers": ["/functional/indices"],
                               "message": f"Index {idx}: raw {qstr(raw)} is outside calibration domain."})
            else:
                vector.append({"index": idx,
                               "value": qstr(cache["calibrations"][idx][raw])})
        if issues:
            profiles[p] = _issues_cell(ctx, issues, "FUNCTIONAL", "CALIBRATION")
        else:
            profiles[p] = ctx.ok(vector, "CALIBRATION", points=[point(*p)],
                                 support=_support("/functional"),
                                 detail="Numeric profile evaluation only; ordinal accreditation is checked separately.")
    return profiles


def _functional(ctx, tree, cache):
    pid = tree["policy"]
    points = _points(tree)
    profiles = cache["profiles"]
    calibration = _calibration(ctx, cache, points, policy=pid)
    terminal_rows, missing = [], []
    scenarios_ok = defined(tree["causal"]["scenarios"])
    if scenarios_ok:
        for scenario in ctx.data["scenarios"]:
            ctx.tick()
            leaf = tree["scenario_map"][scenario["id"]]
            node = tree["node_map"][tuple(leaf)]
            p = (int(node["t"]), node["x"])
            if not defined(profiles[p]):
                missing.append({"code": "FUNCTION_MISSING", "points": [point(*p)],
                                "queries": [node["query"]], "pointers": ["/functional"],
                                "message": "A terminal scenario profile is outside its table domain."})
            else:
                terminal_rows.append({"scenario": scenario["id"],
                                      "profile": value(profiles[p])})
    raw_complete = scenarios_ok and not missing
    if not tree["complete"]:
        terminal = _dependency(ctx, "FUNCTIONAL", pid, "The terminal scenario scope is not complete.")
    elif not scenarios_ok:
        terminal = _scenario_failure(ctx, "FUNCTIONAL", pid)
    elif missing:
        terminal = _issues_cell(ctx, missing, "FUNCTIONAL", "CALIBRATION", policy=pid)
    elif calibration["invalid"]:
        terminal = _issues_cell(ctx, calibration["invalid"], "FUNCTIONAL", "CALIBRATION", policy=pid, blocked=True)
    elif calibration["missing"]:
        terminal = _issues_cell(ctx, calibration["missing"], "FUNCTIONAL", "CALIBRATION", policy=pid)
    else:
        terminal = ctx.ok(terminal_rows, "CALIBRATION", policy=pid,
                          points=_point_wire(points), support=_support("/functional"),
                          detail="Terminal profiles with calibration on the entire local reached scope.")
    ctx.facts.setdefault(pid, {})["functional_data_complete"] = raw_complete
    return {"points": [{"point": point(*p), "profile": profiles[p]} for p in points],
            "terminal": terminal}, calibration


def _reduction(ctx, trees, cache):
    all_complete = all(t["complete"] for t in trees.values())
    if not all_complete:
        ctx.check("FSUFF", "UNDETERMINED", support=_support("/functional/reduction"),
                  detail="At least one target tree is incomplete; global P is not established.")
        return _dependency(ctx, "FUNCTIONAL", None, "Global reduction scope requires every target tree complete."), None
    scope = cache["all_points"]
    profiles = cache["profiles"]
    psi = {(int(r["t"]), r["x"]): r["reduced"]
           for r in ctx.data["functional"]["reduction"]["rows"]}
    domain_f = {p for p in scope if defined(profiles[p])}
    domain_psi = set(scope).intersection(psi)
    fibers = {}
    for p in scope:
        ctx.tick()
        if p in domain_psi:
            fibers.setdefault(psi[p], []).append(p)
    issues = []
    for p in sorted(domain_f - domain_psi):
        ctx.tick()
        issues.append({"code": "REDUCTION_MISSING", "points": [point(*p)],
                       "pointers": ["/functional/reduction"],
                       "message": "Defined functional profile is outside reduction domain."})
    for rid, members in fibers.items():
        ctx.tick()
        present = [p for p in members if p in domain_f]
        absent = [p for p in members if p not in domain_f]
        if present and absent:
            issues.append({"code": "REDUCTION_DOMAIN", "points": _point_wire(members),
                           "pointers": ["/functional"],
                           "message": f"Fiber {rid} mixes defined and undefined profiles."})
        for j, p in enumerate(present):
            for r in present[j + 1:]:
                ctx.tick()
                if value(profiles[p]) != value(profiles[r]):
                    issues.append({"code": "REDUCTION_VALUE", "points": [point(*p), point(*r)],
                                   "pointers": ["/functional"],
                                   "message": f"Fiber {rid} contains unequal defined profiles."})
    if issues:
        return _issues_cell(ctx, issues, "FUNCTIONAL", "FSUFF"), False
    fiber_rows = []
    for rid in sorted(fibers):
        ctx.tick()
        members = fibers[rid]
        if members[0] in domain_f:
            cell = ctx.ok(value(profiles[members[0]]), "FSUFF", points=_point_wire(members),
                          support=_support("/functional"),
                          detail="This complete fiber is in Df and its profile is constant.")
        else:
            # Reuse a genuine profile-domain witness; FSuff itself passes for
            # a fiber wholly outside Df, so do not attach an FSuff FAIL here.
            cell = deepcopy(profiles[members[0]])
        fiber_rows.append({"reduced": rid, "points": _point_wire(members), "value": cell})
    cert = {"scope": _point_wire(scope), "domain_f": _point_wire(sorted(domain_f)),
            "domain_psi": _point_wire(sorted(domain_psi)), "fibers": fiber_rows}
    return ctx.ok(cert, "FSUFF", points=_point_wire(scope), support=_support("/functional"),
                  detail="Df subset Dpsi, saturation, and constancy on every reduction fiber."), True


def _projected_wire(row, ports):
    q = row.get("query")
    return {"query": query(q[0], q[1]) if q is not None else None,
            "values": [{"port": p, "value": row[p]} for p in ports if p in row]}


def _row_key(row):
    return tuple(sorted(row.items()))


def _composition(ctx, tree, cache):
    pid = tree["policy"]
    data = ctx.data["composition"]
    queries = [n["query"] for n in tree["nodes"]]
    keys = {qkey(q) for q in queries}
    missing = [q for q in queries if qkey(q) not in cache["composition_rows"]]
    ports = [p["id"] for p in data["ports"]]
    columns = {"query", *ports}
    covered = set()
    for view in data["views"]:
        ctx.tick()
        covered.update(view["columns"])
    issues = []
    for q in missing:
        ctx.tick()
        issues.append({"code": "COMPOSITION_COVERAGE", "queries": [q],
                       "pointers": ["/composition/rows"], "message": "Missing relation row for a reached occurrence."})
    if covered != columns:
        issues.append({"code": "COMPOSITION_COVERAGE", "pointers": ["/composition/views"],
                       "message": "Views do not cover columns: " + ", ".join(sorted(columns - covered))})
    if not tree["complete"]:
        if issues:
            _issues_cell(ctx, issues, "COMPOSITION", "RELATIONAL_JOIN", policy=pid)
        ctx.check("RELATIONAL_JOIN", "UNDETERMINED", policy=pid,
                  support=_support("/composition"), detail="Complete causal relation scope is not established.")
        return _dependency(ctx, "COMPOSITION", pid, "Composition certificate requires the complete causal query scope."), False if issues else None
    if issues:
        return _issues_cell(ctx, issues, "COMPOSITION", "RELATIONAL_JOIN", policy=pid), False
    relation = []
    for q in queries:
        ctx.tick()
        source = cache["composition_rows"][qkey(q)]
        relation.append({"query": qkey(q), **{v["port"]: v["value"] for v in source["values"]}})
    views, joined = [], [{}]
    for view in data["views"]:
        ctx.tick()
        projected = {}
        for row in relation:
            ctx.tick()
            p = {k: row[k] for k in view["columns"]}
            projected[_row_key(p)] = p
        rows = list(projected.values())
        views.append({"id": view["id"], "rows": [_projected_wire(r, ports) for r in rows]})
        next_join = {}
        for left in joined:
            for right in rows:
                ctx.tick()
                compatible = True
                for k in left.keys() & right.keys():
                    ctx.tick()
                    if left[k] != right[k]:
                        compatible = False
                if compatible:
                    merged = {**left, **right}
                    next_join[_row_key(merged)] = merged
        joined = list(next_join.values())
    expected, actual = {_row_key(r) for r in relation}, {_row_key(r) for r in joined}
    if expected != actual:
        issues = []
        for row in joined:
            ctx.tick()
            if _row_key(row) not in expected:
                issues.append({"code": "COMPOSITION_SPURIOUS", "queries": [query(*row["query"])],
                               "pointers": ["/composition"],
                               "message": "Spurious natural-join row: " + repr(_projected_wire(row, ports))})
        # With projections of the same R and full column coverage, R is always
        # contained in the join. Keep a witness if this invariant is violated.
        for row in relation:
            ctx.tick()
            if _row_key(row) not in actual:
                issues.append({"code": "COMPOSITION_COVERAGE", "queries": [query(*row["query"])],
                               "pointers": ["/composition"], "message": "An original row is absent from the join."})
        return _issues_cell(ctx, issues, "COMPOSITION", "RELATIONAL_JOIN", policy=pid), False
    cert = {"queries": queries, "views": views,
            "join": [_projected_wire(r, ports) for r in joined]}
    return ctx.ok(cert, "RELATIONAL_JOIN", policy=pid, queries=queries,
                  support=_support("/composition"), detail="All natural projections rejoin to exactly the per-policy relation."), True


def _resources(ctx, tree, cache):
    result, complete = [], True
    for node in tree["nodes"]:
        for resource in ctx.data["resources"]["kinds"]:
            ctx.tick()
            rid, q = resource["id"], node["query"]
            total, issues = Fraction(0), []
            for demand in cache["demands"].get(rid, []):
                ctx.tick()
                key = (qkey(q), demand)
                if key not in cache["resource_values"]:
                    issues.append({"code": "RESOURCE_MISSING", "queries": [q],
                                   "pointers": ["/resources/values"],
                                   "message": f"Missing demand {demand} for resource {rid}."})
                else:
                    total += cache["resource_values"][key]
            if issues:
                complete = False
                cell = _issues_cell(ctx, issues, "RESOURCE", "RESOURCE_SUM", policy=tree["policy"])
            else:
                cell = ctx.ok(qstr(total), "RESOURCE_SUM", policy=tree["policy"], queries=[q],
                              support=_support("/resources"), detail=f"Sum each physical demand of {rid} once at this occurrence.")
            result.append({"query": q, "resource": rid, "total": cell})
    return result, complete if tree["complete"] or not complete else None


def _preorder(ctx, ids, relation, name):
    issues = []
    successors = {a: set() for a in ids}
    for a, b in relation:
        ctx.tick()
        successors[a].add(b)
    for a in ids:
        ctx.tick()
        if (a, a) not in relation:
            issues.append({"code": "GEN_ORDER_INVALID", "pointers": [f"/generative/{name}_order"],
                           "message": f"{name} order lacks reflexive pair ({a}, {a})."})
        for b in sorted(successors[a]):
            for c in sorted(successors[b]):
                ctx.tick()
                if c not in successors[a]:
                    issues.append({"code": "GEN_ORDER_INVALID", "pointers": [f"/generative/{name}_order"],
                                   "message": f"{name} order violates transitivity at ({a}, {b}, {c})."})
    ctx.check("GEN_ORDER", "FAIL" if issues else "PASS",
              support=_support(f"/generative/{name}_order"),
              detail=f"Reflexivity and transitivity over the entire {name} alphabet.")
    for issue in issues:
        ctx.diag(issue["code"], "CAG", pointers=issue["pointers"], message=issue["message"])
    return issues


def _generative_points(ctx, cache, points):
    g = ctx.data["generative"]
    native = {(int(r["t"]), r["x"]): r["native"] for r in g["identity"]}
    translation = {r["native"]: r["common"] for r in g["translation"]}
    nm = {r["identity"]: frozenset(r["atoms"]) for r in g["native_meaning"]}
    cm = {r["identity"]: frozenset(r["atoms"]) for r in g["common_meaning"]}
    result = {}
    for p in points:
        ctx.tick()
        issues, invalid, n, c = [], [], native.get(p), None
        if n is None:
            issues.append({"code": "GEN_IDENTITY_MISSING", "points": [point(*p)],
                           "pointers": ["/generative/identity"], "message": "No native identity at this reached point."})
        else:
            c = translation.get(n)
            if c is None:
                issues.append({"code": "GEN_TRANSLATION_MISSING", "points": [point(*p)],
                               "pointers": ["/generative/translation"], "message": f"Native identity {n} has no common translation."})
            if n not in nm:
                issues.append({"code": "GEN_MEANING_MISSING", "points": [point(*p)],
                               "pointers": ["/generative/native_meaning"], "message": f"Native identity {n} has no meaning."})
            if c is not None and c not in cm:
                issues.append({"code": "GEN_MEANING_MISSING", "points": [point(*p)],
                               "pointers": ["/generative/common_meaning"], "message": f"Common identity {c} has no meaning."})
            if n in nm and c in cm and nm[n] != cm[c]:
                invalid.append({"code": "GEN_MEANING_MISMATCH", "points": [point(*p)],
                                "pointers": ["/generative"], "message": f"Meanings differ for translation {n} to {c}."})
        if invalid:
            ctx.check("GEN_TRANSLATION", "FAIL", points=[point(*p)], support=_support("/generative"),
                      detail=invalid[0]["message"])
            cell = _issues_cell(ctx, invalid + issues, "CAG", "GEN_TRANSLATION", blocked=True)
        elif issues:
            cell = _issues_cell(ctx, issues, "CAG", "GEN_TRANSLATION")
        else:
            cell = ctx.ok(c, "GEN_TRANSLATION", points=[point(*p)], support=_support("/generative"),
                          detail="Native identity, translation, and equal nonempty meanings at this point.")
        result[p] = {"native": n, "common": c, "cell": cell,
                     "missing": issues, "invalid": invalid, "raw_complete": not issues}
    cache["native_order"] = {tuple(p) for p in g["native_order"]}
    cache["common_order"] = {tuple(p) for p in g["common_order"]}
    cache["translation"] = translation
    cache["gen_points"] = result
    cache["order_issues"] = (
        _preorder(ctx, g["native_ids"], cache["native_order"], "native") +
        _preorder(ctx, g["common_ids"], cache["common_order"], "common"))


def _translation_guard(ctx, cache, scope, *, policy=None):
    missing, invalid = [], list(cache["order_issues"])
    native_points = {}
    for p in scope:
        ctx.tick()
        record = cache["gen_points"][p]
        missing.extend(record["missing"])
        invalid.extend(record["invalid"])
        if record["native"] is not None and record["common"] is not None:
            native_points.setdefault(record["native"], []).append(point(*p))
    if ctx.data["generative"]["recipe"]["kind"] != "att":
        for a in sorted(native_points):
            for b in sorted(native_points):
                ctx.tick()
                ca, cb = cache["translation"][a], cache["translation"][b]
                if ((a, b) in cache["native_order"]) != ((ca, cb) in cache["common_order"]):
                    invalid.append({"code": "GEN_ORDER_TRANSPORT",
                                    "points": native_points[a] + native_points[b] if a != b else native_points[a],
                                    "pointers": ["/generative"],
                                    "message": f"Conservation differs for native pair ({a}, {b}) and translated pair ({ca}, {cb})."})
    ctx.check("GEN_TRANSLATION", "FAIL" if missing or invalid else "PASS", policy=policy,
              points=_point_wire(scope), support=_support("/generative"),
              detail="Full reached identity scope, faithful meanings, and all required native-pair transport directions.")
    return {"ok": not missing and not invalid, "missing": missing, "invalid": invalid}


def _generative_guard_cell(ctx, guard, pid):
    return _issues_cell(ctx, guard["invalid"] + guard["missing"], "CAG", "GEN_TRANSLATION",
                        policy=pid, blocked=bool(guard["invalid"]))


def _achievements(ctx, identities, leaf, cache):
    recipe = ctx.data["generative"]["recipe"]
    H, kind = ctx.H, recipe["kind"]
    result, witnesses = set(), []
    # Identity/meaning/order coverage has already been checked over the ENTIRE
    # trace. An acc loss never truncates those checks or the identity list.
    prefix_ok = True
    for t in range(1, H + 1):
        ctx.tick()
        if kind == "att":
            attained, window = True, [t]
        elif kind == "hold":
            length = int(recipe["length"])
            if t + length > H:
                continue
            window = list(range(t, t + length + 1))
            attained = True
            for s in window:
                ctx.tick()
                if (identities[t], identities[s]) not in cache["common_order"]:
                    attained = False
        else:
            step_ok = (identities[t - 1], identities[t]) in cache["common_order"]
            prefix_ok = prefix_ok and step_ok
            attained, window = prefix_ok, list(range(t + 1))
        if attained:
            result.add(identities[t])
            witnesses.append({"identity": identities[t], "leaf": leaf,
                              "t": str(t), "window": [str(s) for s in window]})
    return sorted(result), witnesses


def _generative(ctx, tree, cache):
    pid = tree["policy"]
    points = _points(tree)
    guard = _translation_guard(ctx, cache, points, policy=pid)
    ctx.facts.setdefault(pid, {})["generative_data_complete"] = all(
        cache["gen_points"][p]["raw_complete"] for p in points)
    root = tree["node_map"][()]
    origin = deepcopy(cache["gen_points"][(0, root["x"])]["cell"])
    traces, witnesses, all_achievements = [], [], []
    for node in tree["nodes"]:
        if int(node["t"]) != ctx.H:
            continue
        ctx.tick()
        leaf, path = node["query"], tuple(node["query"]["path"])
        trace_points = []
        for t in range(ctx.H + 1):
            ctx.tick()
            ancestor = tree["node_map"][path[:t]]
            trace_points.append((int(ancestor["t"]), ancestor["x"]))
        records = [cache["gen_points"][p] for p in trace_points]
        point_missing = [i for r in records for i in r["missing"]]
        point_invalid = [i for r in records for i in r["invalid"]]
        if point_invalid or point_missing:
            identities_cell = _issues_cell(ctx, point_invalid + point_missing, "CAG", "GEN_TRANSLATION",
                                           policy=pid, blocked=bool(point_invalid))
        else:
            identities_cell = ctx.ok([r["common"] for r in records], "GEN_TRANSLATION", policy=pid,
                                     queries=[leaf], points=_point_wire(sorted(set(trace_points))),
                                     support=_support("/generative"), detail="Complete translated identity trace, including origin.")
        trace_guard = _translation_guard(ctx, cache, sorted(set(trace_points)), policy=pid)
        if not trace_guard["ok"]:
            achievements_cell = _generative_guard_cell(ctx, trace_guard, pid)
        else:
            achievements, leaf_witnesses = _achievements(ctx, value(identities_cell), leaf, cache)
            witnesses.extend(leaf_witnesses)
            all_achievements.append(set(achievements))
            achievements_cell = ctx.ok(achievements, "CAG_RECIPE", policy=pid, queries=[leaf],
                                       support=_support("/generative"),
                                       detail="Every candidate time checked under the declared recipe; all witnesses retained.")
        traces.append({"leaf": leaf, "identities": identities_cell, "achievements": achievements_cell})
    if not tree["complete"]:
        cag = _dependency(ctx, "CAG", pid, "CAG requires all complete causal realizations.")
        additional = _dependency(ctx, "CAG", pid, "Additional CAG requires all complete causal realizations.")
    elif not defined(tree["causal"]["scenarios"]):
        cag, additional = _scenario_failure(ctx, "CAG", pid), _scenario_failure(ctx, "CAG", pid)
    elif not guard["ok"]:
        cag, additional = _generative_guard_cell(ctx, guard, pid), _generative_guard_cell(ctx, guard, pid)
    else:
        # A complete FP1 tree always has at least one actual H-leaf, including
        # its root at H=0. Never initialize robust achievement by a universe.
        if not all_achievements:
            raise RuntimeError("complete causal tree lacks terminal realization")
        if ctx.data["generative"]["mode"] == "possible":
            achieved = set()
            for part in all_achievements:
                ctx.tick()
                achieved.update(part)
        else:
            achieved = set(all_achievements[0])
            for part in all_achievements[1:]:
                ctx.tick()
                achieved.intersection_update(part)
        o = value(origin)
        cag = ctx.ok(sorted(achieved | {o}), "CAG_RECIPE", policy=pid,
                     queries=[r["leaf"] for r in traces], support=_support("/generative"),
                     detail="Origin plus declared union/intersection of all translated trace achievements.")
        additional = ctx.ok(sorted(achieved - {o}), "CAG_RECIPE", policy=pid,
                            queries=[r["leaf"] for r in traces], support=_support("/generative"),
                            detail="Remove only the origin identity from achieved identities.")
    return {"origin": origin, "traces": traces, "cag": cag,
            "additional": additional, "witnesses": witnesses}, guard


def _welfare(ctx, tree, cache):
    pid = tree["policy"]
    cells, lookup, missing = [], {}, []
    for node in tree["nodes"]:
        ctx.tick()
        q, t = node["query"], int(node["t"])
        for carrier, dimension in cache["applicable"].get(t, []):
            ctx.tick()
            key = (qkey(q), carrier, dimension)
            if key in cache["welfare_values"]:
                cell = ctx.ok(cache["welfare_values"][key], "WELFARE_COVERAGE", policy=pid,
                              queries=[q], support=_support("/welfare"),
                              detail=f"Applicable measurement for {carrier}, {dimension} at this occurrence.")
            else:
                issue = {"code": "WELFARE_MISSING", "queries": [q],
                         "pointers": ["/welfare/values"],
                         "message": f"Missing applicable welfare measurement for {carrier}, {dimension}."}
                missing.append(issue)
                cell = _issues_cell(ctx, [issue], "WELFARE", "WELFARE_COVERAGE", policy=pid)
            lookup[key] = cell
            cells.append({"query": q, "carrier": carrier, "dimension": dimension, "value": cell})
    if not tree["complete"]:
        profile = _dependency(ctx, "WELFARE", pid, "Historical welfare scope requires complete causal traces.")
    elif not defined(tree["causal"]["scenarios"]):
        profile = _scenario_failure(ctx, "WELFARE", pid)
    elif missing:
        profile = _issues_cell(ctx, missing, "WELFARE", "WELFARE_COVERAGE", policy=pid)
    else:
        rows = []
        for scenario in ctx.data["scenarios"]:
            path = tuple(tree["scenario_map"][scenario["id"]])
            for t in range(ctx.H + 1):
                ctx.tick()
                q = query(pid, path[:t])
                for carrier, dimension in cache["applicable"].get(t, []):
                    ctx.tick()
                    rows.append({"scenario": scenario["id"], "t": str(t), "carrier": carrier,
                                 "dimension": dimension, "value": value(lookup[(qkey(q), carrier, dimension)])})
        profile = ctx.ok(rows, "WELFARE_COVERAGE", policy=pid,
                         queries=[n["query"] for n in tree["nodes"]], support=_support("/welfare"),
                         detail="Complete history on the global existence/applicability support for every scenario.")
    coverage = False if missing else (True if tree["complete"] else None)
    return {"cells": cells, "profile": profile}, coverage


def evaluate(ctx, trees):
    """Build all structural policy components and strong G05--G10 guards."""
    data = ctx.data
    all_points = sorted({p for tree in trees.values() for p in _points(tree)})
    cache = {
        "indices": data["functional"]["indices"],
        "calibrations": {i["id"]: {Fraction(r["raw"]): Fraction(r["value"]) for r in i["calibration"]}
                         for i in data["functional"]["indices"]},
        "measurements": {(int(r["t"]), r["x"], r["index"]): Fraction(r["raw"])
                         for r in data["functional"]["measurements"]},
        "all_points": all_points,
        "composition_rows": {qkey(r["query"]): r for r in data["composition"]["rows"]},
        "demands": {},
        "resource_values": {(qkey(r["query"]), r["demand"]): Fraction(r["value"])
                            for r in data["resources"]["values"]},
        "applicable": {},
        "welfare_values": {(qkey(r["query"]), r["carrier"], r["dimension"]): r["value"]
                           for r in data["welfare"]["values"]},
    }
    for row in data["resources"]["demands"]:
        ctx.tick()
        cache["demands"].setdefault(row["resource"], []).append(row["id"])
    for row in data["welfare"]["applicability"]:
        ctx.tick()
        cache["applicable"].setdefault(int(row["t"]), []).append((row["carrier"], row["dimension"]))
    cache["profiles"] = _profiles(ctx, cache, all_points)
    _generative_points(ctx, cache, all_points)
    reduction, g06 = _reduction(ctx, trees, cache)
    result, composition_guards, resource_guards, welfare_guards = {}, [], [], []
    for pid, tree in trees.items():
        ctx.tick()
        functional, _ = _functional(ctx, tree, cache)
        functional["reduction"] = deepcopy(reduction)
        composition, cg = _composition(ctx, tree, cache)
        resources, rg = _resources(ctx, tree, cache)
        generative, _ = _generative(ctx, tree, cache)
        welfare, wg = _welfare(ctx, tree, cache)
        composition_guards.append(cg)
        resource_guards.append(rg)
        welfare_guards.append(wg)
        result[pid] = {"functional": functional, "composition": composition,
                       "resources": resources, "generative": generative, "welfare": welfare}
    all_complete = all(t["complete"] for t in trees.values())
    calibration = _calibration(ctx, cache, all_points)
    full_profiles = all(defined(c) for c in cache["profiles"].values())
    ctx.guard("G05", _conjunction([calibration["ok"], full_profiles, True if all_complete else None]))
    ctx.guard("G06", g06)
    ctx.guard("G07", _conjunction(composition_guards))
    ctx.guard("G08", _conjunction(resource_guards))
    gen_guard = _translation_guard(ctx, cache, all_points)
    # Record witnesses of cross-policy failures even when each local policy
    # happens to satisfy the translation or calibration guard independently.
    if calibration["invalid"] or calibration["missing"]:
        _issues_cell(ctx, calibration["invalid"] + calibration["missing"], "FUNCTIONAL", "CALIBRATION",
                     blocked=bool(calibration["invalid"]))
    if gen_guard["invalid"] or gen_guard["missing"]:
        _generative_guard_cell(ctx, gen_guard, None)
    scenarios_complete = all(defined(t["causal"]["scenarios"]) for t in trees.values())
    ctx.guard("G09", _conjunction([gen_guard["ok"], True if all_complete else None,
                                   scenarios_complete if all_complete else None]))
    ctx.guard("G10", _conjunction(welfare_guards))
    ctx.facts["_structural"] = cache
    return result


def apply_common_guards(ctx, trees, policy_results, b0):
    """Accredit the unique B0 scope, never search for a favorable subgroup.

    This does not overwrite the strong all-target guards. A policy excluded
    from B0 can still refute a strong guard even when B0 remains comparable.
    """
    cache = ctx.facts["_structural"]
    b0 = list(b0)
    scope = sorted({p for pid in b0 for p in _points(trees[pid])})
    calibration = _calibration(ctx, cache, scope)
    gen_guard = _translation_guard(ctx, cache, scope)
    for pid in b0:
        ctx.tick()
        if not calibration["ok"]:
            policy_results[pid]["functional"]["terminal"] = _issues_cell(
                ctx, calibration["invalid"] + calibration["missing"], "FUNCTIONAL", "CALIBRATION",
                policy=pid, blocked=bool(calibration["invalid"]))
        if not gen_guard["ok"]:
            policy_results[pid]["generative"]["cag"] = _generative_guard_cell(ctx, gen_guard, pid)
            policy_results[pid]["generative"]["additional"] = _generative_guard_cell(ctx, gen_guard, pid)
