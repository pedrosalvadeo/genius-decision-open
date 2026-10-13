"""Closed specification-06 grammar used by the result verifier.

Tables and sets are unordered; only explicitly ordered Lists retain position.
The grammar validates shape, scalar encodings, set and table uniqueness before
any normalization, so comparison cannot erase duplicated or extra claims.
"""
from __future__ import annotations

from fractions import Fraction
import re

from .common import ComputationLimit, stable_key


class Rejected(ValueError):
    pass


def enum(*values): return ("enum", frozenset(values))
def seq(item): return ("list", item)
def aset(item, nonempty=False): return ("set", item, nonempty)
def table(item, *keys): return ("table", item, keys)
def cell(item): return ("cell", item)
def nullable(item): return ("nullable", item)

ID = "ID"
TEXT = "Text"
NAT = "Nat"
Q = "Q"
NN = "Qnonneg"
BIT = enum("0", "1")
QUERY = {"policy": ID, "path": seq(ID)}
POINT = {"t": NAT, "x": ID}
REF = {"document": enum("INPUT", "OUTPUT"), "pointer": TEXT}
INPUT_REF = {"document": enum("INPUT"), "pointer": TEXT}
IDS = aset(ID)
QUERIES = aset(QUERY)
POINTS = aset(POINT)
RULES = frozenset([f"G{i:02}" for i in range(1, 16)] + "INPUT_TYPES QUERY_REFERENCE CAUSAL_NODE SCENARIO_MAP CALIBRATION FSUFF RELATIONAL_JOIN RESOURCE_SUM GEN_ORDER GEN_TRANSLATION CAG_RECIPE WELFARE_COVERAGE SEM_UNION DECISIVE_SET LAW_ROW LAW_MASS VPROB HARD_RESOURCE HARD_TASK PAIR_COMPARISON FRONTIER SELECTION".split())
CODES = frozenset("INPUT_SYNTAX INPUT_TYPE DUPLICATE_KEY UNKNOWN_FIELD UNKNOWN_REFERENCE BAD_TIME INVALID_VARIANT QUERY_UNRESOLVED POLICY_MISSING ACTION_DOMAIN_MISSING ACTION_NOT_EXECUTABLE ACTION_NOT_ADMISSIBLE TRANSITION_MISSING TRANSITION_EMPTY UPDATE_MISSING TERMINAL_NO_ACTION SCENARIO_COVERAGE SCENARIO_MULTIPLE FUNCTION_MISSING CALIBRATION_MISSING CALIBRATION_ORDER REDUCTION_MISSING REDUCTION_DOMAIN REDUCTION_VALUE COMPOSITION_COVERAGE COMPOSITION_SPURIOUS RESOURCE_MISSING GEN_IDENTITY_MISSING GEN_TRANSLATION_MISSING GEN_MEANING_MISSING GEN_MEANING_MISMATCH GEN_ORDER_INVALID GEN_ORDER_TRANSPORT WELFARE_MISSING SEM_REFERENCE_MISSING TASK_OUTSIDE_DOMAIN VERDICT_MIXED LAW_INVALID LAW_UNDETERMINED POSITIVE_UNDECIDED_MASS HARD_VIOLATION HARD_UNDECIDED COMPARISON_GUARD RELATIVE_COVERAGE NO_FEASIBLE_POLICY SELECTION_DISABLED SELECTION_NOT_UNIQUE SELECTION_EMPTY SELECTION_SCOPE DEPENDENCY_BLOCKED COMPUTATION_LIMIT INTERNAL_ERROR CERTIFICATE_REJECTED".split())
CHECK = {"id": ID, "rule": ("enum", RULES), "outcome": enum("PASS", "FAIL", "UNDETERMINED"), "policies": IDS, "queries": QUERIES, "points": POINTS, "support": aset(REF), "detail": TEXT}
DIAGNOSTIC = {"id": ID, "code": ("enum", CODES), "component": enum(*"INPUT CAUSAL FUNCTIONAL COMPOSITION RESOURCE CAG WELFARE EVIDENCE LAW HARD DECISION EXECUTION".split()), "policies": IDS, "queries": QUERIES, "points": POINTS, "input_refs": aset(INPUT_REF), "message": TEXT}
VECTOR = table({"index": ID, "value": Q}, "index")
READ = {"leaves": QUERIES, "references": table({"leaf": QUERY, "states": aset(ID, True)}, "leaf"), "states": aset(ID, True)}
DECISIVE = {"id": "CertificateID", "kind": enum("DECISIVE_SET"), "query": QUERY, "protocol": enum("FP1_EXACT_ENUM_V1"), "read": READ, "A": aset(ID, True), "value": BIT, "task_rows": table({"state": ID, "value": BIT}, "state")}
EDGE = {"branch": ID, "u": ID, "next_x": ID, "y": ID, "next_i": cell(ID), "child": QUERY}
NODE = {"query": QUERY, "t": NAT, "x": ID, "i": ID, "action": cell(ID), "outcomes": table(EDGE, "branch")}
CAUSAL = {"complete": cell(BIT), "nodes": table(NODE, "query"), "leaves": QUERIES, "scenarios": cell(table({"scenario": ID, "leaf": QUERY}, "scenario"))}
REDUCTION = {"scope": POINTS, "domain_f": POINTS, "domain_psi": POINTS, "fibers": table({"reduced": ID, "points": POINTS, "value": cell(VECTOR)}, "reduced")}
FUNCTIONAL = {"points": table({"point": POINT, "profile": cell(VECTOR)}, "point"), "terminal": cell(table({"scenario": ID, "profile": VECTOR}, "scenario")), "reduction": cell(REDUCTION)}
PROJECTED = {"query": nullable(QUERY), "values": table({"port": ID, "value": ID}, "port")}
COMPOSITION = cell({"queries": QUERIES, "views": table({"id": ID, "rows": aset(PROJECTED)}, "id"), "join": aset(PROJECTED)})
RESOURCES = table({"query": QUERY, "resource": ID, "total": cell(NN)}, "query", "resource")
GENERATIVE = {"origin": cell(ID), "traces": table({"leaf": QUERY, "identities": cell(seq(ID)), "achievements": cell(IDS)}, "leaf"), "cag": cell(IDS), "additional": cell(IDS), "witnesses": table({"identity": ID, "leaf": QUERY, "t": NAT, "window": seq(NAT)}, "identity", "leaf", "t")}
WELFARE = {"cells": table({"query": QUERY, "carrier": ID, "dimension": ID, "value": cell(Q)}, "query", "carrier", "dimension"), "profile": cell(table({"scenario": ID, "t": NAT, "carrier": ID, "dimension": ID, "value": Q}, "scenario", "t", "carrier", "dimension"))}
EVIDENCE = table({"query": QUERY, "sem": cell(READ), "verdict": cell(DECISIVE)}, "query")
PROBABILITY = {"masses": table({"query": QUERY, "mass": cell(NN)}, "query"), "partition": cell({"positive": QUERIES, "negative": QUERIES, "undecided": QUERIES}), "vector": cell({"success": NN, "failure": NN, "undecided": NN}), "pvs": cell(NN)}
HARD = table({"constraint": ID, "value": cell(BIT), "scope": cell(QUERIES), "known_scope": QUERIES, "checked": QUERIES, "violations": QUERIES, "missing": QUERIES}, "constraint")
POLICY = {"policy": ID, "causal": CAUSAL, "functional": FUNCTIONAL, "composition": COMPOSITION, "resources": RESOURCES, "generative": GENERATIVE, "welfare": WELFARE, "evidence": EVIDENCE, "probability": PROBABILITY, "hard": HARD}
PAIR = {"left": ID, "right": ID, **{k: BIT for k in ("functional", "cag", "welfare", "pvs", "weak", "strict")}}
DECISION = {**{k: IDS for k in ("target", "B", "C", "feasible", "failed", "unknown", "frontier")}, "omitted": table({"policy": ID, "reasons": aset("DiagnosticRef", True)}, "policy"), "pairs": table(PAIR, "left", "right"), "dominators": table({"policy": ID, "by": aset(ID, True)}, "policy"), "coverage": enum("EXHAUSTIVE", "RELATIVE"), "selection": cell(ID)}
INTEGRATION = {"id": "CertificateID", "profile": enum("FP1_FINITE_EXACT"), "theory_snapshot": enum("GENIUS-THEORY-2026-09-23-S2"), "target": IDS, "guards": aset("CheckRef"), "selection_check": "CheckRef", "assumptions": IDS, "claim": enum("CONDITIONAL_FORMAL_INSTANCE")}
RESULT = {"format": enum("genius-fp1-result/1.0"), "input_digest": "Digest", "specification": enum("GENIUS-SPEC-1.0.0"), "execution": {"status": enum("COMPLETE", "LIMITED", "ERROR"), "limits": table({"name": TEXT, "bound": NAT}, "name"), "progress": {"completed_policies": IDS, "expanded_nodes": NAT}}, "presentation": enum("VALID", "INVALID", "UNRESOLVED"), "diagnostics": table(DIAGNOSTIC, "id"), "checks": table(CHECK, "id"), "policies": table(POLICY, "policy"), "decision": cell(DECISION), "integration": cell(INTEGRATION)}
ENVELOPE = {"input_digest": "Digest", "certificate": DECISIVE}


def pointer(path, key):
    return path + "/" + str(key).replace("~", "~0").replace("/", "~1")


class Grammar:
    def __init__(self, ctx):
        self.ctx = ctx
        self.cells = []
        self.certificates = []
        self.references = []
        self.certificate_ids = set()

    def fail(self, path, message):
        raise Rejected((path or "/") + ": " + message)

    def visit(self, obj, spec, path=""):
        self.ctx.tick()
        if isinstance(spec, dict):
            if type(obj) is not dict or set(obj) != set(spec):
                self.fail(path, "Expected exact fields " + ", ".join(sorted(spec)))
            if spec is DECISIVE:
                self.certificates.append((path, obj))
            return {k: self.visit(obj[k], item, pointer(path, k)) for k, item in spec.items()}
        if isinstance(spec, tuple):
            kind = spec[0]
            if kind == "enum":
                if type(obj) is not str or obj not in spec[1]:
                    self.fail(path, "Unexpected literal")
                return obj
            if kind == "nullable":
                return None if obj is None else self.visit(obj, spec[1], path)
            if kind == "cell":
                if type(obj) is not dict:
                    self.fail(path, "Cell must be an object")
                state = obj.get("state")
                shapes = {
                    "DEFINED": {"state": enum("DEFINED"), "value": spec[1], "checks": aset("CheckRef")},
                    "OUTSIDE_DOMAIN": {"state": enum("OUTSIDE_DOMAIN"), "reasons": aset("DiagnosticRef", True), "checks": aset("CheckRef")},
                    "BLOCKED": {"state": enum("BLOCKED"), "reasons": aset("DiagnosticRef", True)},
                }
                if type(state) is not str or state not in shapes:
                    self.fail(path, "Unknown Cell state")
                self.cells.append((path, obj))
                return self.visit(obj, shapes[state], path)
            if type(obj) is not list:
                self.fail(path, "Expected JSON array")
            if kind == "set" and spec[2] and not obj:
                self.fail(path, "Set must be nonempty")
            result, seen = [], set()
            for i, item in enumerate(obj):
                normalized = self.visit(item, spec[1], pointer(path, i))
                if kind != "list":
                    key = stable_key([normalized[k] for k in spec[2]]) if kind == "table" else stable_key(normalized)
                    if key in seen:
                        self.fail(pointer(path, i), "Duplicate set member or table key")
                    seen.add(key)
                result.append(normalized)
            return result if kind == "list" else sorted(result, key=stable_key)
        if type(obj) is not str:
            self.fail(path, "Expected string scalar, not a JSON number or Boolean")
        if any(0xD800 <= ord(c) <= 0xDFFF for c in obj):
            self.fail(path, "Unicode surrogate is not Text")
        if spec in ("ID", "CertificateID", "CheckRef", "DiagnosticRef"):
            if re.fullmatch(r"[A-Za-z][A-Za-z0-9_.-]*", obj, re.ASCII) is None:
                self.fail(path, "Invalid ID")
            if spec == "CertificateID":
                if obj in self.certificate_ids:
                    self.fail(path, "Duplicate generated certificate ID")
                self.certificate_ids.add(obj)
            if spec in ("CheckRef", "DiagnosticRef"):
                self.references.append((path, spec, obj))
        elif spec == "Nat":
            if re.fullmatch(r"0|[1-9][0-9]*", obj, re.ASCII) is None:
                self.fail(path, "Invalid Nat")
            self.digits(obj)
        elif spec in ("Q", "Qnonneg"):
            match = re.fullmatch(r"(-?(?:0|[1-9][0-9]*))/([1-9][0-9]*)", obj, re.ASCII)
            if not match or match[1] == "-0":
                self.fail(path, "Invalid rational encoding")
            self.digits(match[1].lstrip("-")); self.digits(match[2])
            rational = Fraction(obj)
            if obj != f"{rational.numerator}/{rational.denominator}" or (spec == "Qnonneg" and rational < 0):
                self.fail(path, "Rational must be reduced and satisfy its sign domain")
        elif spec == "Digest":
            if re.fullmatch(r"[0-9a-f]{64}", obj, re.ASCII) is None:
                self.fail(path, "Invalid SHA-256 digest encoding")
        elif spec != "Text":
            raise RuntimeError("Unknown verifier scalar type " + spec)
        return obj

    def digits(self, val):
        if "max_integer_digits" in self.ctx.limits and len(val) > self.ctx.limits["max_integer_digits"]:
            raise ComputationLimit("max_integer_digits")
