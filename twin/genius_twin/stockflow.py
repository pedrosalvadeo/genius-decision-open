"""Bounded, exact stock-flow dynamics under declared assumptions (D3).

No probabilities or CAG results are manufactured here: this module generates
causal states and history monitors; the FP1 compiler delegates those results.
"""
from copy import deepcopy
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re

from .function_catalog import CATALOG

PROFILE = "STOCK_FLOW_FINITE_V1"
ROOT_FIELDS = "profile name horizon step_unit stocks carriers capabilities initial_capabilities actions policies scenarios law welfare task require_all_scenarios selection assumptions functions subsystems interfaces".split()
ID_PATTERN = r"^[A-Za-z][A-Za-z0-9_.-]*$"
Q_PATTERN = r"^(0|[1-9][0-9]*)/[1-9][0-9]*$"
# Policies x scenarios x states. Measured on the blood case scaled to 270 cells: 10 s,
# 14 MB packed output (envelope.py) under production's 16 MB, 136 MB in the web process.
OCCURRENCE_LIMIT = 256
ASSUMPTION_KINDS = ["MODEL", "INITIALIZATION", "INFORMATION", "SEMANTIC", "CALIBRATION", "NORMATIVE", "PROBABILITY", "SYNTHETIC"]


def canonical_json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def q(value):
    n = Fraction(value)
    return f"{n.numerator}/{n.denominator}"


def signature(capabilities):
    return "org_" + hashlib.sha256(canonical_json(sorted(capabilities)).encode()).hexdigest()[:20]


def default_model():
    """A fresh, explicitly hypothetical example, never an empirical default law."""
    return json.loads((Path(__file__).parents[1] / "examples" / "stockflow_care.json").read_text())


def model_schema():
    """Closed JSON Schema; semantic guards in validate_model remain authoritative."""
    ident = {"type": "string", "pattern": ID_PATTERN, "maxLength": 64}
    txt = {"type": "string", "minLength": 1, "maxLength": 2000}
    qty = {"type": "string", "pattern": Q_PATTERN, "maxLength": 25, "x-rational": True}
    def arr(item, lo=0, hi=128):
        return {"type": "array", "items": item, "minItems": lo, "maxItems": hi}
    def obj(props):
        return {"type": "object", "properties": props, "required": list(props), "additionalProperties": False}
    def enum(*values):
        return {"type": "string", "enum": list(values)}
    def ids():
        return {**arr(ident, 0, 8), "uniqueItems": True}
    amounts = {"type": "object", "additionalProperties": qty, "maxProperties": 6}
    stock_pred = obj({"kind": enum("stock"), "stock": ident, "op": enum("ge", "le"), "value": qty})
    cap_pred = obj({"kind": enum("capability"), "capability": ident, "present": {"type": "boolean"}})
    event = obj({"inflows": amounts, "renewables": amounts, "drains": amounts, "remove_capabilities": ids()})
    schema = obj({
        "profile": enum(PROFILE), "name": txt,
        "horizon": {"type": "integer", "minimum": 1, "maximum": 30},
        "step_unit": enum("day", "hour", "step"),
        "stocks": arr(obj({"id": ident, "label": txt, "unit": ident,
            "kind": enum("persistent", "renewable"), "initial": qty, "capacity": qty}), 1, 6),
        "carriers": arr(obj({"id": ident, "label": txt, "kind": enum("person", "living", "organization")}), 1, 6),
        "capabilities": arr(obj({"id": ident, "label": txt}), 1, 8),
        "initial_capabilities": ids(),
        "actions": arr(obj({"id": ident, "label": txt, "requires": ids(), "withdrawals": amounts,
            "deposits": amounts, "add_capabilities": ids(), "remove_capabilities": ids()}), 1, 12),
        "policies": arr(obj({"id": ident, "label": txt, "default_action": ident,
            "rules": arr(obj({"steps": {**arr({"type": "integer", "minimum": 1, "maximum": 30}, 1, 30), "uniqueItems": True},
                 "when": arr({"oneOf": [stock_pred, cap_pred]}, 0, 12), "action": ident}), 0, 30)}), 1, 6),
        "scenarios": arr(obj({"id": ident, "label": txt, "events": arr(event, 1, 30)}), 1, 8),
        "law": {"oneOf": [{"type": "null"}, {"type": "object", "additionalProperties": qty, "minProperties": 1, "maxProperties": 8}]},
        "welfare": arr(obj({"carrier": ident, "dimension": ident, "label": txt, "stock": ident,
            "direction": enum("higher", "lower")}), 1, 12),
        "task": obj({"kind": enum("life_conditions", "operational"), "label": txt,
            "living_carriers": {**arr(ident, 0, 6), "uniqueItems": True},
            "conditions": arr(obj({"stock": ident, "op": enum("ge", "le"),
                "threshold": {"oneOf": [qty, {"type": "null"}]}}), 1, 12),
            "require_action_success": {"type": "boolean"}}),
        "require_all_scenarios": {"type": "boolean"}, "selection": enum("none", "unique"),
        "assumptions": arr(obj({"id": ident, "kind": enum(*ASSUMPTION_KINDS), "statement": txt, "provenance": txt}), 1, 24),
    })
    # Module I: functions the system performs, measured on every projected twin
    # (route x scenario). Optional, so models without them keep a neutral profile.
    # An optional `kind` names the shared catalog entry (function_catalog.py).
    function = obj({"id": ident, "label": txt,
        "serves": {**arr(ident, 0, 6), "uniqueItems": True}, "measure": enum("current", "cumulative"),
        "when": arr({"oneOf": [stock_pred, cap_pred]}, 1, 6)})
    function["properties"]["kind"] = enum(*CATALOG)
    schema["properties"]["functions"] = arr(function, 0, 8)
    # Module II: subsystems partition the stocks; an interface carries what
    # actions move from one subsystem's stocks into another's. Optional.
    schema["properties"]["subsystems"] = arr(obj({"id": ident, "label": txt,
        "stocks": {**arr(ident, 1, 6), "uniqueItems": True}, "carriers": {**arr(ident, 0, 6), "uniqueItems": True}}), 0, 6)
    schema["properties"]["interfaces"] = arr(obj({"id": ident, "label": txt, "source": ident, "target": ident}), 0, 8)
    # Any domain: an action may compose 2 to 4 declared actions done in the same step;
    # expand_actions fills its requirements and flows as their union and sum. Optional.
    schema["properties"]["actions"]["items"]["properties"]["compose"] = {**arr(ident, 2, 4), "uniqueItems": True}
    # Module III: a capability with holds_when exists exactly in the states whose
    # stocks satisfy it (e.g. hydropower above a minimum power pool). Optional.
    schema["properties"]["capabilities"]["items"]["properties"]["holds_when"] = arr(stock_pred, 1, 6)
    schema.update({"$schema": "https://json-schema.org/draft/2020-12/schema", "title": PROFILE,
        "x-semantic-rules": ["Reduced nonnegative rationals, numerator/denominator at most 12 digits",
        "Unique IDs and valid references", f"P*S*(H+1)<={OCCURRENCE_LIMIT}; generated signatures<=16",
        "Per-unit deposits<=withdrawals; no implicit conversion", "Complete renewable availability per event",
        "Unique complete event words; law null or exact normalized scenario map",
        "Policies read only prior state; fixed carrier existence; no implicit mortality model"]})
    return schema


def _shape(value, spec, path="model"):
    if "oneOf" in spec:
        matches = 0
        for variant in spec["oneOf"]:
            try:
                _shape(value, variant, path)
                matches += 1
            except ValueError:
                pass
        if matches != 1:
            raise ValueError(f"{path}: invalid variant")
        return
    types = {"object": dict, "array": list, "string": str, "integer": int, "boolean": bool, "null": type(None)}
    expected = spec.get("type")
    if expected and (type(value) is not types[expected]):
        raise ValueError(f"{path}: expected {expected}")
    if "enum" in spec and value not in spec["enum"]:
        raise ValueError(f"{path}: unsupported value")
    if expected == "object":
        props = spec.get("properties", {})
        if not set(spec.get("required", [])) <= set(value):
            raise ValueError(f"{path}: missing required fields")
        if len(value) < spec.get("minProperties", 0) or len(value) > spec.get("maxProperties", 1000):
            raise ValueError(f"{path}: too many/few fields")
        for k, v in value.items():
            if not isinstance(k, str):
                raise ValueError(f"{path}: field names must be strings")
            child = props.get(k, spec.get("additionalProperties", {}))
            if child is False:
                raise ValueError(f"{path}: unknown field {k}")
            _shape(v, child, path + "." + k)
    elif expected == "array":
        if not spec.get("minItems", 0) <= len(value) <= spec.get("maxItems", 1000):
            raise ValueError(f"{path}: invalid collection size")
        if spec.get("uniqueItems") and len({canonical_json(v) for v in value}) != len(value):
            raise ValueError(f"{path}: duplicate member")
        for i, v in enumerate(value):
            _shape(v, spec["items"], f"{path}[{i}]")
    elif expected == "string":
        if not spec.get("minLength", 0) <= len(value) <= spec.get("maxLength", 10000):
            raise ValueError(f"{path}: invalid text length")
        if any(0xD800 <= ord(c) <= 0xDFFF for c in value):
            raise ValueError(f"{path}: invalid Unicode")
        if "pattern" in spec and not re.fullmatch(spec["pattern"], value, re.ASCII):
            raise ValueError(f"{path}: invalid lexical form")
        if spec.get("x-rational"):
            if max(map(len, value.split("/"))) > 12 or q(value) != value:
                raise ValueError(f"{path}: rational must be reduced and <=12 digits per integer")
    elif expected == "integer":
        if not spec.get("minimum", value) <= value <= spec.get("maximum", value):
            raise ValueError(f"{path}: outside finite limit")


def composed(parts):
    """One action doing every part in the same step, all or nothing: union of requirements
    and capability changes, sum of withdrawals and deposits per stock."""
    out = {"requires": [], "withdrawals": {}, "deposits": {}, "add_capabilities": [], "remove_capabilities": []}
    for part in parts:
        for field in ("requires", "add_capabilities", "remove_capabilities"):
            out[field] += [c for c in part[field] if c not in out[field]]
        for field in ("withdrawals", "deposits"):
            for k, v in part[field].items():
                out[field][k] = q(Fraction(out[field].get(k, "0")) + Fraction(v))
    return out


def expand_actions(model):
    """Fill each composed action from its parts; malformed input is left for validate_model."""
    actions = model.get("actions") if isinstance(model, dict) else None
    if not isinstance(actions, list):
        return model
    by_id = {a.get("id"): a for a in actions if isinstance(a, dict)}
    expanded = []
    for action in actions:
        parts = [by_id.get(i) for i in action.get("compose", [])] if isinstance(action, dict) and isinstance(action.get("compose"), list) else []
        if parts and all(isinstance(p, dict) and "compose" not in p and all(f in p for f in ("requires", "withdrawals", "deposits", "add_capabilities", "remove_capabilities")) for p in parts):
            action = {"id": action.get("id"), "label": action.get("label"), **composed(parts), "compose": action["compose"]}
        expanded.append(action)
    return {**model, "actions": expanded}


def validate_model(model):
    _shape(model, model_schema())
    tables = {}
    for key in ("stocks", "carriers", "capabilities", "actions", "policies", "scenarios", "assumptions"):
        tables[key] = {row["id"]: row for row in model[key]}
        if len(tables[key]) != len(model[key]):
            raise ValueError(f"{key}: duplicate ID")
    stocks, caps, actions = tables["stocks"], tables["capabilities"], tables["actions"]
    def refs(values, domain, where):
        if not set(values) <= set(domain):
            raise ValueError(f"{where}: unknown reference")
    refs(model["initial_capabilities"], caps, "initial_capabilities")
    for stock in stocks.values():
        if Fraction(stock["initial"]) > Fraction(stock["capacity"]):
            raise ValueError("initial stock exceeds capacity")
    for action in actions.values():
        if "compose" in action:
            refs(action["compose"], actions, "action.compose")
            parts = [actions[i] for i in action["compose"]]
            if any("compose" in p for p in parts):
                raise ValueError(f"action {action['id']}: a composed action cannot compose another")
            if {k: action[k] for k in ("requires", "withdrawals", "deposits", "add_capabilities", "remove_capabilities")} != composed(parts):
                raise ValueError(f"action {action['id']}: flows differ from the composition of its parts")
        for field in ("requires", "add_capabilities", "remove_capabilities"):
            refs(action[field], caps, "action." + field)
        if set(action["add_capabilities"]) & set(action["remove_capabilities"]):
            raise ValueError("action cannot add and remove the same capability")
        for field in ("withdrawals", "deposits"):
            refs(action[field], stocks, "action." + field)
        for unit in {s["unit"] for s in stocks.values()}:
            outgoing = sum((Fraction(v) for k, v in action["withdrawals"].items() if stocks[k]["unit"] == unit), Fraction())
            incoming = sum((Fraction(v) for k, v in action["deposits"].items() if stocks[k]["unit"] == unit), Fraction())
            if incoming > outgoing:
                raise ValueError(f"action {action['id']}: deposits exceed withdrawals for unit {unit}")
    H = model["horizon"]
    if len(model["policies"]) * len(model["scenarios"]) * (H + 1) > OCCURRENCE_LIMIT:
        raise ValueError(f"occurrence limit P*S*(H+1)<={OCCURRENCE_LIMIT} exceeded")
    held = {c["id"] for c in caps.values() if "holds_when" in c}
    for cid in held:
        refs([p["stock"] for p in caps[cid]["holds_when"]], stocks, "capability.holds_when")
    if held & (set(model["initial_capabilities"]) | {k for a in actions.values() for k in a["add_capabilities"] + a["remove_capabilities"]}
               | {k for s in model["scenarios"] for e in s["events"] for k in e["remove_capabilities"]}):
        raise ValueError("a capability with holds_when follows the state only: not initial, added or removed")
    for policy in model["policies"]:
        refs([policy["default_action"]], actions, "policy.default_action")
        for rule in policy["rules"]:
            refs([rule["action"]], actions, "rule.action")
            if any(t > H for t in rule["steps"]):
                raise ValueError("rule step exceeds horizon")
            for predicate in rule["when"]:
                if predicate["kind"] == "stock":
                    refs([predicate["stock"]], stocks, "predicate.stock")
                else:
                    refs([predicate["capability"]], caps, "predicate.capability")
    words = set()
    renewables = {s["id"] for s in stocks.values() if s["kind"] == "renewable"}
    for scenario in model["scenarios"]:
        if len(scenario["events"]) != H:
            raise ValueError("event word length differs from horizon")
        word = canonical_json(scenario["events"])
        if word in words:
            raise ValueError("duplicate complete scenario event word")
        words.add(word)
        for event in scenario["events"]:
            for field in ("inflows", "drains"):
                refs(event[field], stocks, "event." + field)
            if set(event["renewables"]) != renewables:
                raise ValueError("event renewables must cover exactly renewable stocks")
            for k, val in event["renewables"].items():
                if Fraction(val) > Fraction(stocks[k]["capacity"]):
                    raise ValueError("renewable availability exceeds capacity")
            refs(event["remove_capabilities"], caps, "event.remove_capabilities")
    law = model["law"]
    if law is not None and (set(law) != set(tables["scenarios"]) or sum(map(Fraction, law.values()), Fraction()) != 1):
        raise ValueError("law must cover all scenarios and sum exactly to one")
    bindings, dimensions = set(), {}
    for binding in model["welfare"]:
        refs([binding["carrier"]], tables["carriers"], "welfare.carrier")
        refs([binding["stock"]], stocks, "welfare.stock")
        key = binding["carrier"], binding["dimension"]
        if key in bindings:
            raise ValueError("duplicate carrier/dimension binding")
        bindings.add(key)
        unit_dir = stocks[binding["stock"]]["unit"], binding["direction"]
        if binding["dimension"] in dimensions and dimensions[binding["dimension"]] != unit_dir:
            raise ValueError("same welfare dimension requires same unit and direction")
        dimensions[binding["dimension"]] = unit_dir
    task = model["task"]
    refs(task["living_carriers"], tables["carriers"], "task.living_carriers")
    if task["kind"] == "life_conditions":
        if not task["living_carriers"] or any(tables["carriers"][c]["kind"] not in ("person", "living") for c in task["living_carriers"]):
            raise ValueError("life_conditions requires declared living/person carriers")
    elif task["living_carriers"]:
        raise ValueError("operational task must not declare life semantics")
    for condition in task["conditions"]:
        refs([condition["stock"]], stocks, "task.condition.stock")
    functions = model.get("functions", [])
    if len({f["id"] for f in functions}) != len(functions):
        raise ValueError("functions: duplicate ID")
    for function in functions:
        refs(function["serves"], tables["carriers"], "function.serves")
        for predicate in function["when"]:
            if predicate["kind"] == "stock":
                refs([predicate["stock"]], stocks, "function.stock")
            else:
                refs([predicate["capability"]], caps, "function.capability")
    subsystems = model.get("subsystems", [])
    if len({x["id"] for x in subsystems}) != len(subsystems):
        raise ValueError("subsystems: duplicate ID")
    owned = [k for x in subsystems for k in x["stocks"]]
    for x in subsystems:
        refs(x["stocks"], stocks, "subsystem.stocks")
        refs(x["carriers"], tables["carriers"], "subsystem.carriers")
    if subsystems and sorted(owned) != sorted(stocks):
        raise ValueError("subsystems must partition the stocks: each stock in exactly one subsystem")
    interfaces = model.get("interfaces", [])
    if interfaces and not subsystems:
        raise ValueError("interfaces require subsystems")
    if len({x["id"] for x in interfaces}) != len(interfaces):
        raise ValueError("interfaces: duplicate ID")
    for x in interfaces:
        refs([x["source"], x["target"]], {s["id"] for s in subsystems}, "interface")
        if x["source"] == x["target"]:
            raise ValueError("interface must join two different subsystems")
    # Generate all reachable signatures here; never truncate excess signatures.
    traces = _compute(model)
    generated = {row["organization"] for policies in traces.values() for tr in policies.values() for row in tr["daily"]}
    if len(generated) > 16:
        raise ValueError("generated organization signature limit <=16 exceeded")


def _condition(stocks, condition):
    threshold = condition["threshold"]
    if threshold is None:
        return None
    a, b = Fraction(stocks[condition["stock"]]), Fraction(threshold)
    return a >= b if condition["op"] == "ge" else a <= b


def _matches(pred, stocks, capabilities):
    if pred["kind"] == "capability":
        return (pred["capability"] in capabilities) == pred["present"]
    return _condition(stocks, {"stock": pred["stock"], "op": pred["op"], "threshold": pred["value"]})


def choose_action(policy, step, stocks, capabilities):
    return next((rule["action"] for rule in policy["rules"]
                 if step in rule["steps"] and all(_matches(p, stocks, capabilities) for p in rule["when"])), policy["default_action"])


def interface_flows(model, daily):
    """Module II: cumulative amount each interface carried up to each state of one projected twin.

    At a step, an executed action that withdraws from the source subsystem's
    stocks carries its declared deposits into the target subsystem's stocks.
    """
    actions = {a["id"]: a for a in model["actions"]}
    members = {x["id"]: set(x["stocks"]) for x in model.get("subsystems", [])}
    out = {}
    for x in model.get("interfaces", []):
        total, values = Fraction(), []
        for row in daily:
            action = actions.get(row["action_id"])
            if action and row["action_executed"] and set(action["withdrawals"]) & members[x["source"]]:
                total += sum((Fraction(v) for k, v in action["deposits"].items() if k in members[x["target"]]), Fraction())
            values.append(total)
        out[x["id"]] = values
    return out


def function_values(model, daily):
    """Module I raw values per state of one projected twin: {function id: [raw per step]}.

    current: 1 if every predicate holds at that state, else 0.
    cumulative: number of states up to and including that one where it held.
    The raw is a function of the state's whole history, which is the compiled FP1 state.
    """
    out = {}
    for function in model.get("functions", []):
        held = [int(all(_matches(p, {k: Fraction(v) for k, v in row["stocks"].items()}, set(row["capabilities"]))
                        for p in function["when"])) for row in daily]
        if function["measure"] == "cumulative":
            total, values = 0, []
            for h in held:
                total += h
                values.append(total)
            held = values
        out[function["id"]] = held
    return out


def _state_capabilities(model, balances, capabilities):
    """Module III: capabilities with holds_when exist exactly where the state satisfies them."""
    for c in model["capabilities"]:
        if "holds_when" in c:
            if all(_matches(p, balances, capabilities) for p in c["holds_when"]):
                capabilities.add(c["id"])
            else:
                capabilities.discard(c["id"])
    return capabilities


def _monitor(task, stocks, action_executed, previous_failed, previous_unknown):
    verdicts = [_condition(stocks, c) for c in task["conditions"]]
    failed = previous_failed or any(v is False for v in verdicts)
    if action_executed is not None and task["require_action_success"] and not action_executed:
        failed = True
    unknown = previous_unknown or any(v is None for v in verdicts)
    current = False if any(v is False for v in verdicts) else None if any(v is None for v in verdicts) else True
    return failed, unknown, current


def _compute(model):
    stocks = {s["id"]: s for s in model["stocks"]}
    actions = {a["id"]: a for a in model["actions"]}
    initial = {k: Fraction(s["initial"]) for k, s in stocks.items()}
    output = {}
    for policy in model["policies"]:
        output[policy["id"]] = {}
        for scenario in model["scenarios"]:
            balances = initial.copy()
            capabilities = _state_capabilities(model, balances, set(model["initial_capabilities"]))
            failed, unknown, endpoint = _monitor(model["task"], balances, None, False, False)
            daily = [{"day": 0, "step": 0, "stocks": {k: q(v) for k, v in balances.items()},
                      "capabilities": sorted(capabilities), "organization": signature(capabilities),
                      "action_id": None, "action_executed": None, "action_failure_reasons": [], "ledger": {},
                      "violation_seen": failed, "indeterminate_seen": unknown, "endpoint_conditions": endpoint,
                      "task_status": "failure" if failed else "undecided" if unknown else "success"}]
            totals = {field: {k: Fraction() for k in stocks} for field in
                      ("withdrawn", "deposited", "drained", "unmet", "spilled", "expired", "inflows", "renewed")}
            for step, event in enumerate(scenario["events"], 1):
                aid = choose_action(policy, step, balances, capabilities)
                action = actions[aid]
                ledger = {k: {field: Fraction() for field in ("before", "renewal", "expiry", "inflow", "withdrawal", "deposit", "spill", "drained", "unmet", "after")} for k in stocks}
                for k, stock in stocks.items():
                    rec = ledger[k]
                    rec["before"] = balances[k]
                    if stock["kind"] == "renewable":
                        rec["expiry"] = balances[k]
                        rec["renewal"] = Fraction(event["renewables"][k])
                        balances[k] = rec["renewal"]
                    rec["inflow"] = Fraction(event["inflows"].get(k, "0/1"))
                    balances[k] += rec["inflow"]
                    overflow = max(Fraction(), balances[k] - Fraction(stock["capacity"]))
                    balances[k] -= overflow
                    rec["spill"] += overflow
                reasons = ["capability:" + k for k in action["requires"] if k not in capabilities]
                reasons += ["stock:" + k for k, v in action["withdrawals"].items() if balances[k] < Fraction(v)]
                executed = not reasons
                if executed:
                    for k, v in action["withdrawals"].items():
                        amount = Fraction(v)
                        balances[k] -= amount
                        ledger[k]["withdrawal"] = amount
                    for k, v in action["deposits"].items():
                        amount = Fraction(v)
                        balances[k] += amount
                        ledger[k]["deposit"] = amount
                        overflow = max(Fraction(), balances[k] - Fraction(stocks[k]["capacity"]))
                        balances[k] -= overflow
                        ledger[k]["spill"] += overflow
                    capabilities.difference_update(action["remove_capabilities"])
                    capabilities.update(action["add_capabilities"])
                for k, demand in event["drains"].items():
                    demand = Fraction(demand)
                    ledger[k]["drained"] = min(balances[k], demand)
                    ledger[k]["unmet"] = demand - ledger[k]["drained"]
                    balances[k] -= ledger[k]["drained"]
                capabilities.difference_update(event["remove_capabilities"])
                _state_capabilities(model, balances, capabilities)
                for k, rec in ledger.items():
                    rec["after"] = balances[k]
                    if rec["before"] + rec["renewal"] - rec["expiry"] + rec["inflow"] - rec["withdrawal"] + rec["deposit"] - rec["spill"] - rec["drained"] != rec["after"]:
                        raise RuntimeError("Internal stock conservation violation")
                    for total, field in (("withdrawn", "withdrawal"), ("deposited", "deposit"), ("drained", "drained"), ("unmet", "unmet"), ("spilled", "spill"), ("expired", "expiry"), ("inflows", "inflow"), ("renewed", "renewal")):
                        totals[total][k] += rec[field]
                failed, unknown, endpoint = _monitor(model["task"], balances, executed, failed, unknown)
                daily.append({"day": step, "step": step, "stocks": {k: q(v) for k, v in balances.items()},
                    "capabilities": sorted(capabilities), "organization": signature(capabilities),
                    "action_id": aid, "action_executed": executed, "action_failure_reasons": reasons,
                    "ledger": {k: {**{f: q(v) for f, v in rec.items()}, "balance_valid": True} for k, rec in ledger.items()},
                    "violation_seen": failed, "indeterminate_seen": unknown, "endpoint_conditions": endpoint,
                    "task_status": "failure" if failed else "undecided" if unknown else "success"})
            output[policy["id"]][scenario["id"]] = {"daily": daily,
                "totals": {field: {k: q(v) for k, v in values.items()} for field, values in totals.items()}}
    return output


def compute_trajectories(model):
    """Exact causal states by policy/scenario; does not mutate the source model."""
    validate_model(model)
    return _compute(model)
