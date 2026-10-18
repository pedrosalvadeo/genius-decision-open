"""Module 0, living twin: re-initialize a declared model from what was observed at one of its steps.

The frozen prediction is never touched. The living twin starts at step k with
the observed stocks and capabilities, keeps the routes' remaining rules and the
scenarios' remaining events, and is evaluated like any other model. Every stock
must be observed: an unobserved stock is not filled from any trajectory.
"""
from copy import deepcopy

from .stockflow import q, validate_model


def reanchor(model, step, stocks, capabilities, label=None):
    """A new model whose step 0 is the observed state at `step` of `model`.

    stocks: {stock id: observed value (n/d)} for every stock.
    capabilities: capabilities observed present, except those that follow the state (holds_when).
    """
    validate_model(model)
    H = model["horizon"]
    if not 0 < step < H:
        raise ValueError("the observed step must leave at least one step to project")
    ids = {s["id"] for s in model["stocks"]}
    if set(stocks) != ids:
        raise ValueError("every stock must be observed; missing: " + ", ".join(sorted(ids - set(stocks))))
    living = deepcopy(model)
    living["name"] = label or f"{model['name']} (desde el paso {step} observado)"
    living["horizon"] = H - step
    for s in living["stocks"]:
        s["initial"] = q(stocks[s["id"]])
    held = {c["id"] for c in model["capabilities"] if "holds_when" in c}
    living["initial_capabilities"] = sorted(set(capabilities) - held)
    for policy in living["policies"]:
        rules = []
        for rule in policy["rules"]:
            later = [t - step for t in rule["steps"] if t > step]
            if later:
                rules.append({**rule, "steps": later})
        policy["rules"] = rules
    words = {}
    for scenario in living["scenarios"]:
        scenario["events"] = scenario["events"][step:]
        key = repr(scenario["events"])
        if key in words:
            raise ValueError(f"scenarios {words[key]} and {scenario['id']} no longer differ after step {step}")
        words[key] = scenario["id"]
    validate_model(living)
    return living
