"""Exact wire values, evidence records, and cooperative operational limits.

These helpers do not decide mathematical module claims. Constructors perform
the checks before recording them; verification recomputes from the input.
"""
from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
import hashlib
import json
import sys
import time

if hasattr(sys, "set_int_max_str_digits"):
    sys.set_int_max_str_digits(0)

SPECIFICATION = "GENIUS-SPEC-1.0.0"
THEORY_SNAPSHOT = "GENIUS-THEORY-2026-09-23-S2"
PROFILE = "FP1_FINITE_EXACT"
VERSION = "1.0.1"
LIMIT_NAMES = frozenset({"max_nodes", "max_operations", "max_seconds",
                         "max_input_bytes", "max_integer_digits"})


class InputError(ValueError):
    def __init__(self, code, pointer, message):
        super().__init__(message)
        self.code, self.pointer, self.message = code, pointer, message


class ComputationLimit(RuntimeError):
    def __init__(self, name):
        super().__init__("Operational limit reached: " + name)
        self.name = name


def validate_limits(limits):
    if limits is None:
        return {}
    if not isinstance(limits, dict) or set(limits) - LIMIT_NAMES:
        raise ValueError("Unknown operational limit; see LIMIT_NAMES")
    for name, bound in limits.items():
        if type(bound) is not int or bound < 0:
            raise ValueError(name + " must be a nonnegative integer")
    return dict(limits)


def qkey(q):
    return q["policy"], tuple(q["path"])


def query(policy, path):
    return {"policy": policy, "path": list(path)}


def point(t, x):
    return {"t": str(t), "x": x}


def qstr(number):
    f = Fraction(number)
    return f"{f.numerator}/{f.denominator}"


def defined(cell):
    return isinstance(cell, dict) and cell.get("state") == "DEFINED"


def value(cell, default=None):
    return cell["value"] if defined(cell) else default


def stable_key(obj):
    return json.dumps(obj, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def unique(items):
    out, seen = [], set()
    for item in items:
        k = stable_key(item)
        if k not in seen:
            out.append(deepcopy(item))
            seen.add(k)
    return out


class Context:
    def __init__(self, data, raw, limits=None):
        self.data = data
        self.raw = raw
        self.digest = hashlib.sha256(raw).hexdigest()
        self.limits = validate_limits(limits)
        # Capture the interpreter's unavoidable stack budget before evaluation.
        # It is reported separately from caller-configurable problem-independent
        # limits and never used as a mathematical horizon or domain restriction.
        self.environment_limits = {"python_recursion_depth": sys.getrecursionlimit()}
        self.H = int(data.get("meta", {}).get("horizon", "0")) if data else 0
        self.checks = []
        self.diagnostics = []
        self.facts = {}
        self.completed_policies = set()
        self.expanded_nodes = 0
        self.operations = 0
        self.started = time.monotonic()
        self.guard_obligations = {f"G{i:02}": [] for i in range(1, 16)}

    def tick(self, n=1):
        self.operations += n
        if ("max_operations" in self.limits and
                self.operations > self.limits["max_operations"]):
            raise ComputationLimit("max_operations")
        if ("max_seconds" in self.limits and
                time.monotonic() - self.started >= self.limits["max_seconds"]):
            raise ComputationLimit("max_seconds")

    def node_tick(self):
        if ("max_nodes" in self.limits and
                self.expanded_nodes >= self.limits["max_nodes"]):
            raise ComputationLimit("max_nodes")
        self.tick()
        self.expanded_nodes += 1

    def check(self, rule, outcome, *, policy=None, queries=(), points=(),
              support=None, detail=""):
        if outcome not in {"PASS", "FAIL", "UNDETERMINED"}:
            raise ValueError("Invalid check outcome")
        item = {
            "id": f"Check.{len(self.checks) + 1}", "rule": rule,
            "outcome": outcome,
            "policies": [] if policy is None else [policy],
            "queries": unique(queries), "points": unique(points),
            "support": deepcopy(support) if support is not None else [
                {"document": "INPUT", "pointer": ""}],
            "detail": detail,
        }
        self.checks.append(item)
        return item["id"]

    def diag(self, code, component, *, policy=None, queries=(), points=(),
             pointers=(), message=""):
        item = {
            "id": f"Diagnostic.{len(self.diagnostics) + 1}",
            "code": code, "component": component,
            "policies": [] if policy is None else [policy],
            "queries": unique(queries), "points": unique(points),
            "input_refs": [{"document": "INPUT", "pointer": p}
                           for p in dict.fromkeys(pointers)],
            "message": message or code,
        }
        self.diagnostics.append(item)
        return item["id"]

    def ok(self, val, rule, **kwargs):
        return {"state": "DEFINED", "value": deepcopy(val),
                "checks": [self.check(rule, "PASS", **kwargs)]}

    def out(self, code, component, rule, **kwargs):
        d = self.diag(code, component, **kwargs)
        args = {k: v for k, v in kwargs.items()
                if k in {"policy", "queries", "points"}}
        return {"state": "OUTSIDE_DOMAIN", "reasons": [d],
                "checks": [self.check(rule, "FAIL", **args,
                                      detail=kwargs.get("message", code))]}

    def block(self, code, component, **kwargs):
        return {"state": "BLOCKED", "reasons": [self.diag(code, component, **kwargs)]}

    def guard(self, name, outcome):
        if name not in self.guard_obligations or outcome not in (True, False, None):
            raise ValueError("Invalid guard")
        self.guard_obligations[name].append(outcome)

    def guard_value(self, name):
        items = self.guard_obligations[name]
        if not items:
            return None
        if any(v is False for v in items):
            return False
        if any(v is None for v in items):
            return None
        return True

    def guard_checks(self):
        result = []
        for name in self.guard_obligations:
            v = self.guard_value(name)
            outcome = "UNDETERMINED" if v is None else "PASS" if v else "FAIL"
            result.append(self.check(name, outcome,
                detail="Conjunction of all required obligations over the declared target."))
        return result

    def execution(self, status):
        return {"status": status,
                "limits": [{"name": n, "bound": str(b)}
                           for n, b in sorted({**self.environment_limits, **self.limits}.items())],
                "progress": {"completed_policies": sorted(self.completed_policies),
                             "expanded_nodes": str(self.expanded_nodes)}}
