"""Module VII, decision window: how much of the future a decider can still choose.

Each decider computes at its own speed and has its own window of opportunity.
Reality keeps moving while it computes: the steps whose actions happen before
the decision can take effect are already committed to the route the decider is
following now. plan() measures the evaluation, says whether it fits the window
and, when steps are committed, returns the model in which every route follows
the committed route during those steps. That model is an ordinary declared
model, evaluated like any other; nothing in the mathematics changes. Costs are
the decider's own measurements (or a declared reference); they are never
inferred from the domain.
"""
from copy import deepcopy
from fractions import Fraction
import math

from .stockflow import q, validate_model

FORMAT = "genius-decision-window/1"
FIELDS = {"available_seconds", "step_seconds", "first_action_offset_seconds", "action_latency_seconds",
          "observation_age_seconds", "committed_route", "seconds_per_cell", "fixed_seconds"}
# Measured on 2026-10-18 in the build container: the five field cases took
# 29-44 ms per cell (2.9-4.7 s each). A decider replaces it with its own.
REFERENCE_SECONDS_PER_CELL = Fraction(1, 20)


def _seconds(window, key, default=None, positive=False):
    value = window.get(key, default)
    if value is None:
        raise ValueError(f"{key} is required")
    if type(value) is bool or not isinstance(value, (int, str)):
        raise ValueError(f"{key} must be an exact number of seconds")
    number = Fraction(value)
    if number < 0 or (positive and number == 0):
        raise ValueError(f"{key} must be {'positive' if positive else 'nonnegative'}")
    return number


def cells(model):
    """Projected-twin states the evaluation computes: routes x scenarios x (horizon + 1)."""
    return len(model["policies"]) * len(model["scenarios"]) * (model["horizon"] + 1)


def committed_steps(elapsed, horizon, step_seconds, first_action_offset_seconds):
    """Steps whose action happens before `elapsed` seconds from the observed state."""
    if elapsed <= first_action_offset_seconds:
        return 0
    return min(horizon, math.ceil((elapsed - first_action_offset_seconds) / step_seconds))


def commit(model, steps, route):
    """Every route follows `route` at steps 1..steps; afterwards each keeps its own rules."""
    validate_model(model)
    if not 0 < steps < model["horizon"]:
        raise ValueError("committed steps must leave at least one step to decide")
    routes = {p["id"]: p for p in model["policies"]}
    if route not in routes:
        raise ValueError(f"unknown committed route {route}")
    early = range(1, steps + 1)
    fixed = []
    for rule in routes[route]["rules"]:
        within = [t for t in rule["steps"] if t <= steps]
        if within:
            fixed.append({**deepcopy(rule), "steps": within})
    # Steps no committed rule claims take the committed route's default action.
    fixed.append({"steps": list(early), "when": [], "action": routes[route]["default_action"]})
    out = deepcopy(model)
    seen, identical = {}, []
    policies = []
    for policy in out["policies"]:
        later = [{**rule, "steps": [t for t in rule["steps"] if t > steps]} for rule in policy["rules"]]
        policy["rules"] = deepcopy(fixed) + [rule for rule in later if rule["steps"]]
        if len(policy["rules"]) > 30:
            raise ValueError(f"route {policy['id']} needs more than 30 rules once committed")
        key = repr((policy["default_action"], policy["rules"]))
        if key in seen:
            identical.append({"route": policy["id"], "same_as": seen[key]})
            continue
        seen[key] = policy["id"]
        policies.append(policy)
    if len(policies) < 2:
        raise ValueError("every route is the committed route once committed; nothing is left to compare")
    out["policies"] = policies
    out["name"] = f"{model['name']} (pasos 1 a {steps} comprometidos con {route})"
    validate_model(out)
    return out, identical


def plan(model, window):
    """What a decider with this window can still choose, and the model to evaluate."""
    validate_model(model)
    if type(window) is not dict or not set(window) <= FIELDS:
        raise ValueError("window fields: " + ", ".join(sorted(FIELDS)))
    available = _seconds(window, "available_seconds", positive=True)
    step = _seconds(window, "step_seconds", positive=True)
    # Times are measured from the observed state (the model's step 0); the
    # computation starts observation_age_seconds after it.
    offset = _seconds(window, "first_action_offset_seconds", 0)
    age = _seconds(window, "observation_age_seconds", 0)
    latency = _seconds(window, "action_latency_seconds", 0)
    per_cell = _seconds(window, "seconds_per_cell", q(REFERENCE_SECONDS_PER_CELL))
    fixed_cost = _seconds(window, "fixed_seconds", 0)
    cost_basis = "DECLARED_BY_DECIDER" if "seconds_per_cell" in window else "REFERENCE_MEASUREMENT_NOT_THIS_DECIDER"
    H, n = model["horizon"], cells(model)
    estimate = fixed_cost + per_cell * n
    fits = estimate <= available
    # A decider that cannot finish acts at the end of its window at the latest.
    elapsed = age + min(estimate, available) + latency
    steps = committed_steps(elapsed, H, step, offset)
    result = {"format": FORMAT, "cells": n, "estimated_compute_seconds": q(estimate),
              "available_seconds": q(available), "cost_basis": cost_basis,
              "effect_after_seconds": q(elapsed), "committed_steps": steps,
              "status": "FITS_WINDOW" if fits else "DOES_NOT_FIT_WINDOW",
              "model": None, "identical_routes": [],
              "meaning": "Steps whose action happens before the decision takes effect follow the committed route; "
                         "the evaluation of the returned model is an ordinary declared evaluation."}
    if steps >= H:
        result["status"] = "NO_STEP_LEFT_TO_DECIDE"
        return result
    if steps:
        if "committed_route" not in window:
            raise ValueError(f"{steps} steps are committed before the decision takes effect; declare committed_route")
        result["model"], result["identical_routes"] = commit(model, steps, window["committed_route"])
        # A committed route merged into an identical earlier one is named by the route kept.
        same = {row["route"]: row["same_as"] for row in result["identical_routes"]}
        result["committed_route"] = same.get(window["committed_route"], window["committed_route"])
    else:
        result["model"] = deepcopy(model)
    if not fits:
        result["note"] = ("The full evaluation is estimated to exceed the window. A smaller declared model "
                          "(fewer routes, scenarios or steps) is the decider's choice; nothing is dropped here.")
    return result
