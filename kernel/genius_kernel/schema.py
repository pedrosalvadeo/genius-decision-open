"""Strict, closed FP1 input grammar and nominal-domain validation.

Mathematical guards (orders, calibration, normalized laws, coverage) are
intentionally left to their constructors. A missing row of a partial table is
not a malformed input. Every supplied row is nevertheless fully validated.
"""
from __future__ import annotations

import json
import math
import re

from .common import InputError, ComputationLimit


_ID = re.compile(r"[A-Za-z][A-Za-z0-9_.-]*\Z", re.ASCII)
_NAT = re.compile(r"(?:0|[1-9][0-9]*)\Z", re.ASCII)
_Q = re.compile(r"(-?(?:0|[1-9][0-9]*))/([1-9][0-9]*)\Z", re.ASCII)


def _ptr(base, name):
    return base + "/" + str(name).replace("~", "~0").replace("/", "~1")


class _Pairs(list):
    pass


def parse(raw: bytes, limits: dict) -> dict:
    """Decode exact UTF-8 bytes, rejecting duplicate keys before dict creation."""
    if not isinstance(raw, bytes):
        raise InputError("INPUT_TYPE", "", "Input must be UTF-8 bytes")
    if "max_input_bytes" in limits and len(raw) > int(limits["max_input_bytes"]):
        raise ComputationLimit("max_input_bytes")
    try:
        source = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise InputError("INPUT_SYNTAX", "", "Input is not valid UTF-8") from exc

    def number(_):
        raise InputError("INPUT_TYPE", "", "FP1 numbers must use Nat/Q strings")

    def constant(_):
        raise InputError("INPUT_SYNTAX", "", "Nonfinite JSON constants are forbidden")

    try:
        parsed = json.loads(source, object_pairs_hook=_Pairs,
                            parse_int=number, parse_float=number,
                            parse_constant=constant)
    except (json.JSONDecodeError, UnicodeError) as exc:
        raise InputError("INPUT_SYNTAX", "", "Invalid JSON syntax") from exc
    except RecursionError as exc:
        # An interpreter nesting limit is operational, never a grammar verdict.
        raise ComputationLimit("python_recursion_depth") from exc

    def materialize(obj, pointer):
        if isinstance(obj, _Pairs):
            out = {}
            for name, val in obj:
                dest = _ptr(pointer, name)
                if name in out:
                    raise InputError("DUPLICATE_KEY", dest, "Duplicate JSON object key")
                if any(0xD800 <= ord(c) <= 0xDFFF for c in name):
                    raise InputError("INPUT_TYPE", dest, "Object key contains a Unicode surrogate")
                out[name] = materialize(val, dest)
            return out
        if isinstance(obj, list):
            return [materialize(val, _ptr(pointer, n)) for n, val in enumerate(obj)]
        if isinstance(obj, str) and any(0xD800 <= ord(c) <= 0xDFFF for c in obj):
            raise InputError("INPUT_TYPE", pointer, "Text contains a Unicode surrogate")
        return obj

    try:
        result = materialize(parsed, "")
    except RecursionError as exc:
        raise ComputationLimit("python_recursion_depth") from exc
    if not isinstance(result, dict):
        raise InputError("INPUT_TYPE", "", "Instance must be an object")
    return result


class _Validator:
    def __init__(self, ctx):
        self.ctx = ctx
        self.d = ctx.data
        self.H = 0
        self.refs = []

    def error(self, pointer, message, code="INPUT_TYPE"):
        raise InputError(code, pointer, message)

    def obj(self, val, pointer, fields):
        self.ctx.tick()
        if not isinstance(val, dict):
            self.error(pointer, "Expected an object")
        expected = set(fields.split() if isinstance(fields, str) else fields)
        for field in val:
            if field not in expected:
                self.error(_ptr(pointer, field), "Unknown field", "UNKNOWN_FIELD")
        for field in sorted(expected):
            if field not in val:
                self.error(pointer, "Missing required field: " + field)
        return val

    def array(self, val, pointer, nonempty=False):
        if not isinstance(val, list):
            self.error(pointer, "Expected an array")
        if nonempty and not val:
            self.error(pointer, "Array must be nonempty")
        return val

    def text(self, val, pointer):
        if not isinstance(val, str) or any(0xD800 <= ord(c) <= 0xDFFF for c in val):
            self.error(pointer, "Expected Unicode scalar text")
        return val

    def ident(self, val, pointer):
        if not isinstance(val, str) or not _ID.fullmatch(val):
            self.error(pointer, "Expected a lexical FP1 ID")
        return val

    def literal(self, val, pointer, choices):
        if not isinstance(val, str) or val not in choices:
            self.error(pointer, "Invalid literal or variant", "INVALID_VARIANT")
        return val

    def integer(self, text, pointer):
        # Python's process-wide decimal conversion policy is configured by common.
        bound = self.ctx.limits.get("max_integer_digits")
        if bound is not None and len(text.lstrip("-")) > bound:
            raise ComputationLimit("max_integer_digits")
        return int(text)

    def nat(self, val, pointer, time=False, nonterminal=False):
        if not isinstance(val, str) or not _NAT.fullmatch(val):
            self.error(pointer, "Expected a canonical Nat string")
        number = self.integer(val, pointer)
        if (time and number > self.H) or (nonterminal and number >= self.H):
            self.error(pointer, "Time lies outside its horizon domain", "BAD_TIME")
        return number

    def rational(self, val, pointer, nonnegative=False):
        match = _Q.fullmatch(val) if isinstance(val, str) else None
        if match is None or match[1] == "-0":
            self.error(pointer, "Expected a canonical rational n/d string")
        n, d = self.integer(match[1], pointer), self.integer(match[2], pointer)
        if math.gcd(abs(n), d) != 1 or (nonnegative and n < 0):
            self.error(pointer, "Rational must be reduced and in the required sign domain")
        return val

    def ref(self, val, pointer, domain):
        self.ident(val, pointer)
        if val not in domain:
            self.error(pointer, "Unknown nominal reference: " + val, "UNKNOWN_REFERENCE")
        return val

    def ids(self, val, pointer, domain=None, nonempty=False):
        self.array(val, pointer, nonempty)
        seen = set()
        for j, ident in enumerate(val):
            self.ctx.tick()
            dest = _ptr(pointer, j)
            (self.ident(ident, dest) if domain is None else self.ref(ident, dest, domain))
            if ident in seen:
                self.error(dest, "Duplicate member of Set", "DUPLICATE_KEY")
            seen.add(ident)
        return seen

    def table(self, rows, pointer, fields, key, check, nonempty=False):
        self.array(rows, pointer, nonempty)
        seen = set()
        for j, row in enumerate(rows):
            dest = _ptr(pointer, j)
            self.obj(row, dest, fields)
            check(row, dest)
            k = key(row)
            if k in seen:
                self.error(dest, "Duplicate table key", "DUPLICATE_KEY")
            seen.add(k)
        return seen

    def basis(self, val, pointer):
        return self.ids(val, pointer, self.assumptions, nonempty=True)

    def point(self, row, pointer, nonterminal=False):
        self.nat(row["t"], _ptr(pointer, "t"), time=True, nonterminal=nonterminal)
        self.ref(row["x"], _ptr(pointer, "x"), self.states)

    def query(self, val, pointer, kind="node"):
        self.obj(val, pointer, "policy path")
        self.ref(val["policy"], _ptr(pointer, "policy"), self.policies)
        self.array(val["path"], _ptr(pointer, "path"))
        for j, branch in enumerate(val["path"]):
            self.ident(branch, _ptr(_ptr(pointer, "path"), j))
        t = len(val["path"])
        if t > self.H or (kind == "leaf" and t != self.H) or (kind == "nonterminal" and t >= self.H):
            self.error(pointer, "Query time is outside the required node domain", "BAD_TIME")
        self.refs.append((val, pointer, kind))

    @staticmethod
    def qkey(q):
        return q["policy"], tuple(q["path"])

    def run(self):
        d = self.obj(self.d, "", "format meta assumptions initialization model policies scenarios functional composition resources generative welfare semantics law constraints selection")
        self.literal(d["format"], "/format", {"genius-fp1/1.0"})
        meta = self.obj(d["meta"], "/meta", "id framework model context condition horizon specification theory_snapshot profile claim_scope")
        for name in ("id", "framework", "model", "context", "condition"):
            self.ident(meta[name], "/meta/" + name)
        self.H = self.nat(meta["horizon"], "/meta/horizon")
        self.ctx.H = self.H
        for name, expected in (("specification", "GENIUS-SPEC-1.0.0"), ("theory_snapshot", "GENIUS-THEORY-2026-09-23-S2"), ("profile", "FP1_FINITE_EXACT"), ("claim_scope", "FORMAL_INSTANCE_ONLY")):
            self.literal(meta[name], "/meta/" + name, {expected})

        def assumption(row, p):
            self.ident(row["id"], p + "/id")
            self.literal(row["kind"], p + "/kind", {"MODEL", "INITIALIZATION", "INFORMATION", "SEMANTIC", "CALIBRATION", "NORMATIVE", "PROBABILITY", "SYNTHETIC"})
            self.text(row["statement"], p + "/statement")
            self.text(row["provenance"], p + "/provenance")
        self.assumptions = self.table(d["assumptions"], "/assumptions", "id kind statement provenance", lambda r: r["id"], assumption)

        model = self.obj(d["model"], "/model", "states information actions observations exogenous basis information_basis executable admissible transitions updates")
        self.states = self.ids(model["states"], "/model/states", nonempty=True)
        self.information = self.ids(model["information"], "/model/information", nonempty=True)
        self.actions = self.ids(model["actions"], "/model/actions", nonempty=self.H > 0)
        self.observations = self.ids(model["observations"], "/model/observations", nonempty=self.H > 0)
        self.exogenous = self.ids(model["exogenous"], "/model/exogenous", nonempty=self.H > 0)
        self.basis(model["basis"], "/model/basis")
        self.basis(model["information_basis"], "/model/information_basis")
        init = self.obj(d["initialization"], "/initialization", "history condition x0 i0 basis")
        self.ident(init["history"], "/initialization/history")
        self.ref(init["condition"], "/initialization/condition", {meta["condition"]})
        self.ref(init["x0"], "/initialization/x0", self.states)
        self.ref(init["i0"], "/initialization/i0", self.information)
        self.basis(init["basis"], "/initialization/basis")

        def actionrow(row, p):
            self.point(row, p, nonterminal=True)
            self.ids(row["actions"], p + "/actions", self.actions)
        for table in ("executable", "admissible"):
            self.table(model[table], "/model/" + table, "t x actions", lambda r: (r["t"], r["x"]), actionrow)

        def transition(row, p):
            self.point(row, p, nonterminal=True)
            self.ref(row["a"], p + "/a", self.actions)
            def outcome(out, op):
                self.ident(out["branch"], op + "/branch")
                self.ref(out["u"], op + "/u", self.exogenous)
                self.ref(out["next_x"], op + "/next_x", self.states)
                self.ref(out["y"], op + "/y", self.observations)
            self.table(row["outcomes"], p + "/outcomes", "branch u next_x y", lambda r: r["branch"], outcome)
        self.table(model["transitions"], "/model/transitions", "t x a outcomes", lambda r: (r["t"], r["x"], r["a"]), transition)

        def update(row, p):
            self.nat(row["t"], p + "/t", nonterminal=True)
            self.ref(row["i"], p + "/i", self.information)
            self.ref(row["a"], p + "/a", self.actions)
            self.ref(row["y"], p + "/y", self.observations)
            self.ref(row["next_i"], p + "/next_i", self.information)
        self.table(model["updates"], "/model/updates", "t i a y next_i", lambda r: (r["t"], r["i"], r["a"], r["y"]), update)

        def policy(row, p):
            self.ident(row["id"], p + "/id")
            def decision(dec, dp):
                self.nat(dec["t"], dp + "/t", nonterminal=True)
                self.ref(dec["i"], dp + "/i", self.information)
                self.ref(dec["a"], dp + "/a", self.actions)
            self.table(row["decisions"], p + "/decisions", "t i a", lambda r: (r["t"], r["i"]), decision)
        self.policies = self.table(d["policies"], "/policies", "id decisions", lambda r: r["id"], policy, nonempty=True)

        words = set()
        def scenario(row, p):
            self.ident(row["id"], p + "/id")
            self.array(row["inputs"], p + "/inputs")
            if len(row["inputs"]) != self.H:
                self.error(p + "/inputs", "Scenario word length differs from horizon", "BAD_TIME")
            for j, u in enumerate(row["inputs"]):
                self.ref(u, p + "/inputs/" + str(j), self.exogenous)
            word = tuple(row["inputs"])
            if word in words:
                self.error(p + "/inputs", "Duplicate scenario word", "DUPLICATE_KEY")
            words.add(word)
        self.table(d["scenarios"], "/scenarios", "id inputs", lambda r: r["id"], scenario, nonempty=True)
        self.functional()
        self.composition()
        self.resources()
        self.generative()
        self.welfare()
        self.semantics()
        self.law()
        self.constraints()
        self.selection()
        self.ctx.facts["_query_references"] = self.refs

    def functional(self):
        block = self.obj(self.d["functional"], "/functional", "indices measurements reduction")
        def index(row, p):
            self.ident(row["id"], p + "/id")
            self.basis(row["basis"], p + "/basis")
            def calibration(r, rp):
                self.rational(r["raw"], rp + "/raw")
                self.rational(r["value"], rp + "/value")
            self.table(row["calibration"], p + "/calibration", "raw value", lambda r: r["raw"], calibration)
        indices = self.table(block["indices"], "/functional/indices", "id calibration basis", lambda r: r["id"], index)
        def measurement(row, p):
            self.point(row, p)
            self.ref(row["index"], p + "/index", indices)
            self.rational(row["raw"], p + "/raw")
        self.table(block["measurements"], "/functional/measurements", "t x index raw", lambda r: (r["t"], r["x"], r["index"]), measurement)
        reduction = self.obj(block["reduction"], "/functional/reduction", "ids rows")
        ids = self.ids(reduction["ids"], "/functional/reduction/ids")
        def row(r, p):
            self.point(r, p)
            self.ref(r["reduced"], p + "/reduced", ids)
        self.table(reduction["rows"], "/functional/reduction/rows", "t x reduced", lambda r: (r["t"], r["x"]), row)

    def composition(self):
        block = self.obj(self.d["composition"], "/composition", "ports rows views basis")
        self.basis(block["basis"], "/composition/basis")
        values = {}
        def port(row, p):
            self.ident(row["id"], p + "/id")
            if row["id"] == "query":
                self.error(p + "/id", "Port name query is reserved", "INVALID_VARIANT")
            values[row["id"]] = self.ids(row["values"], p + "/values")
            self.basis(row["basis"], p + "/basis")
        ports = self.table(block["ports"], "/composition/ports", "id values basis", lambda r: r["id"], port)
        def row(r, p):
            self.query(r["query"], p + "/query")
            def cell(c, cp):
                self.ref(c["port"], cp + "/port", ports)
                self.ref(c["value"], cp + "/value", values[c["port"]])
            present = self.table(r["values"], p + "/values", "port value", lambda c: c["port"], cell)
            if present != ports:
                self.error(p + "/values", "Composition row must contain exactly one cell per port")
        self.table(block["rows"], "/composition/rows", "query values", lambda r: self.qkey(r["query"]), row)
        def view(row, p):
            self.ident(row["id"], p + "/id")
            self.ids(row["columns"], p + "/columns", ports | {"query"})
        self.table(block["views"], "/composition/views", "id columns", lambda r: r["id"], view)

    def resources(self):
        block = self.obj(self.d["resources"], "/resources", "kinds demands values basis")
        self.basis(block["basis"], "/resources/basis")
        units = {}
        def kind(row, p):
            self.ident(row["id"], p + "/id")
            self.ident(row["unit"], p + "/unit")
            units[row["id"]] = row["unit"]
        self.kinds = self.table(block["kinds"], "/resources/kinds", "id unit", lambda r: r["id"], kind)
        def demand(row, p):
            self.ident(row["id"], p + "/id")
            self.ref(row["resource"], p + "/resource", self.kinds)
            self.ref(row["unit"], p + "/unit", {units[row["resource"]]})
            self.basis(row["basis"], p + "/basis")
        demands = self.table(block["demands"], "/resources/demands", "id resource unit basis", lambda r: r["id"], demand)
        def row(r, p):
            self.query(r["query"], p + "/query")
            self.ref(r["demand"], p + "/demand", demands)
            self.rational(r["value"], p + "/value", nonnegative=True)
        self.table(block["values"], "/resources/values", "query demand value", lambda r: (self.qkey(r["query"]), r["demand"]), row)

    def generative(self):
        block = self.obj(self.d["generative"], "/generative", "native_ids common_ids meaning_atoms native_meaning common_meaning native_order common_order identity translation recipe mode basis")
        native = self.ids(block["native_ids"], "/generative/native_ids")
        common = self.ids(block["common_ids"], "/generative/common_ids")
        atoms = self.ids(block["meaning_atoms"], "/generative/meaning_atoms")
        for name, domain in (("native", native), ("common", common)):
            def meaning(row, p):
                self.ref(row["identity"], p + "/identity", domain)
                self.ids(row["atoms"], p + "/atoms", atoms, nonempty=True)
            self.table(block[name + "_meaning"], "/generative/" + name + "_meaning", "identity atoms", lambda r: r["identity"], meaning)
            seen = set()
            path = "/generative/" + name + "_order"
            for j, pair in enumerate(self.array(block[name + "_order"], path)):
                self.ctx.tick()
                pp = path + "/" + str(j)
                self.array(pair, pp)
                if len(pair) != 2:
                    self.error(pp, "Order member must be a pair")
                self.ref(pair[0], pp + "/0", domain)
                self.ref(pair[1], pp + "/1", domain)
                key = tuple(pair)
                if key in seen:
                    self.error(pp, "Duplicate order pair", "DUPLICATE_KEY")
                seen.add(key)
        def identity(row, p):
            self.point(row, p)
            self.ref(row["native"], p + "/native", native)
        self.table(block["identity"], "/generative/identity", "t x native", lambda r: (r["t"], r["x"]), identity)
        def translation(row, p):
            self.ref(row["native"], p + "/native", native)
            self.ref(row["common"], p + "/common", common)
        self.table(block["translation"], "/generative/translation", "native common", lambda r: r["native"], translation)
        recipe = block["recipe"]
        if not isinstance(recipe, dict) or "kind" not in recipe:
            self.error("/generative/recipe", "Missing recipe kind")
        self.literal(recipe["kind"], "/generative/recipe/kind", {"att", "acc", "hold"})
        self.obj(recipe, "/generative/recipe", "kind length" if recipe["kind"] == "hold" else "kind")
        if recipe["kind"] == "hold":
            self.nat(recipe["length"], "/generative/recipe/length")
        self.literal(block["mode"], "/generative/mode", {"possible", "robust"})
        self.basis(block["basis"], "/generative/basis")

    def welfare(self):
        block = self.obj(self.d["welfare"], "/welfare", "carriers dimensions existence applicability values basis")
        carriers = self.ids(block["carriers"], "/welfare/carriers")
        def dimension(row, p):
            self.ident(row["id"], p + "/id")
            self.basis(row["basis"], p + "/basis")
        dimensions = self.table(block["dimensions"], "/welfare/dimensions", "id basis", lambda r: r["id"], dimension)
        def existence(row, p):
            self.nat(row["t"], p + "/t", time=True)
            self.ref(row["carrier"], p + "/carrier", carriers)
        exists = self.table(block["existence"], "/welfare/existence", "t carrier", lambda r: (r["t"], r["carrier"]), existence)
        def applicable(row, p):
            existence(row, p)
            self.ref(row["dimension"], p + "/dimension", dimensions)
            if (row["t"], row["carrier"]) not in exists:
                self.error(p, "Applicability requires carrier existence", "UNKNOWN_REFERENCE")
        applies = self.table(block["applicability"], "/welfare/applicability", "t carrier dimension", lambda r: (r["t"], r["carrier"], r["dimension"]), applicable)
        def row(r, p):
            self.query(r["query"], p + "/query")
            self.ref(r["carrier"], p + "/carrier", carriers)
            self.ref(r["dimension"], p + "/dimension", dimensions)
            if (str(len(r["query"]["path"])), r["carrier"], r["dimension"]) not in applies:
                self.error(p, "Welfare value is outside applicability support", "UNKNOWN_REFERENCE")
            self.rational(r["value"], p + "/value")
        self.table(block["values"], "/welfare/values", "query carrier dimension value", lambda r: (self.qkey(r["query"]), r["carrier"], r["dimension"]), row)
        self.basis(block["basis"], "/welfare/basis")

    def semantics(self):
        block = self.obj(self.d["semantics"], "/semantics", "states references task protocol basis")
        states = self.ids(block["states"], "/semantics/states")
        def reference(row, p):
            self.query(row["leaf"], p + "/leaf", kind="leaf")
            self.ids(row["states"], p + "/states", states, nonempty=True)
        self.table(block["references"], "/semantics/references", "leaf states", lambda r: self.qkey(r["leaf"]), reference)
        def task(row, p):
            self.ref(row["state"], p + "/state", states)
            self.literal(row["value"], p + "/value", {"0", "1"})
        self.table(block["task"], "/semantics/task", "state value", lambda r: r["state"], task)
        self.literal(block["protocol"], "/semantics/protocol", {"FP1_EXACT_ENUM_V1"})
        self.basis(block["basis"], "/semantics/basis")

    def law(self):
        block = self.obj(self.d["law"], "/law", "rows basis")
        def row(r, p):
            self.query(r["query"], p + "/query", kind="nonterminal")
            def weight(w, wp):
                self.ident(w["branch"], wp + "/branch")
                self.rational(w["mass"], wp + "/mass", nonnegative=True)
            self.table(r["weights"], p + "/weights", "branch mass", lambda w: w["branch"], weight)
        self.table(block["rows"], "/law/rows", "query weights", lambda r: self.qkey(r["query"]), row)
        self.basis(block["basis"], "/law/basis")

    def constraints(self):
        rows = self.array(self.d["constraints"], "/constraints")
        ids = set()
        for j, row in enumerate(rows):
            p = "/constraints/" + str(j)
            if not isinstance(row, dict) or "kind" not in row:
                self.error(p, "Missing constraint kind")
            kind = self.literal(row["kind"], p + "/kind", {"resource_budget", "task_all"})
            self.obj(row, p, "id kind resource bound basis" if kind == "resource_budget" else "id kind scope basis")
            self.ident(row["id"], p + "/id")
            if row["id"] in ids:
                self.error(p + "/id", "Duplicate constraint ID", "DUPLICATE_KEY")
            ids.add(row["id"])
            self.basis(row["basis"], p + "/basis")
            if kind == "resource_budget":
                self.ref(row["resource"], p + "/resource", self.kinds)
                self.rational(row["bound"], p + "/bound", nonnegative=True)
            else:
                self.literal(row["scope"], p + "/scope", {"ALL_NODES", "LEAVES"})

    def selection(self):
        row = self.d["selection"]
        if not isinstance(row, dict) or "mode" not in row:
            self.error("/selection", "Missing selection mode")
        mode = self.literal(row["mode"], "/selection/mode", {"none", "unique", "priority"})
        self.obj(row, "/selection", "mode order basis" if mode == "priority" else "mode")
        if mode == "priority":
            order = self.ids(row["order"], "/selection/order", self.policies)
            if order != self.policies:
                self.error("/selection/order", "Priority order must permute all target policies", "UNKNOWN_REFERENCE")
            self.basis(row["basis"], "/selection/basis")


def validate(ctx) -> None:
    """Validate every present block and row, including unreachable data."""
    _Validator(ctx).run()
