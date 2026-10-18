"""Comparison chat: the same question answered by a market AI and by Genius.

Side A is Claude as anyone gets it: the question alone, no system prompt.
Side B is Genius: the same model only drafts a finite stock-flow model of the
decision (routes, scenarios, carriers, life condition, wellbeing), every number
declared as a hypothesis. The validator checks it, the kernel evaluates it and
the answer is read from the kernel's results: life condition and PVS for every
route and scenario, each carrier's wellbeing, the best routes per carrier. The
language model never chooses; nothing here sums criteria.

Questions are not stored. The key comes from ANTHROPIC_API_KEY; without it the
endpoints answer 503 and the page says the comparison is not configured.
"""
from fractions import Fraction
import json
import os
import time

from flask import g, jsonify, request, send_from_directory

MODEL = "claude-opus-5-5"
MAX_QUESTION = 4000
DEADLINE_SECONDS = 105  # gunicorn's twin timeout is 120 s
MAX_HORIZON = 8

MODELLER = """You translate a person's decision into a small finite stock-flow model for the Genius kernel. You never answer the question and never recommend: the kernel evaluates the model and the answer is read from its results.

Return only one JSON object, no prose, in this compact format (omitted optional fields take the defaults shown):
{
 "name": "short title in the user's language",
 "horizon": 1-8 steps, "step_unit": "day" | "hour" | "step",
 "stocks": [{"id", "label", "unit", "kind": "persistent" | "renewable", "initial": number, "capacity": number}],   1-6 stocks
 "carriers": [{"id", "label", "kind": "person" | "living" | "organization"}],   who lives the consequences, 1-6
 "capabilities": [{"id", "label"}],   optional, at most 3; default one capability "act"
 "initial_capabilities": [ids],   default: all capabilities
 "actions": [{"id", "label", "withdrawals": {stock: number}, "deposits": {stock: number}, "requires": [capability ids], "add_capabilities": [], "remove_capabilities": []}],
 "policies": [{"id", "label", "default_action": action id, "rules": [{"steps": [1..horizon], "when": [{"stock", "op": "ge" | "le", "value": number}], "action": action id}]}],   2-4 routes
 "scenarios": [{"id", "label", "events": [exactly horizon items {"inflows": {stock: number}, "drains": {stock: number}, "renewables": {stock: number}}]}],   2-4 scenarios
 "law": {scenario id: "a/b"},   probabilities as exact fractions summing to exactly 1
 "welfare": [{"carrier", "dimension", "label", "stock", "direction": "higher" | "lower"}],   at least one per carrier
 "task": {"label", "living_carriers": [person or living carrier ids], "conditions": [{"stock", "op": "ge" | "le", "threshold": number}]},
 "assumptions": [{"id", "kind", "statement", "provenance"}]
}

How the engine runs each route in each scenario, step by step: renewable stocks are reset to the step's "renewables" availability (default: their capacity); inflows are added (anything above capacity spills); the route picks its action (the first rule whose step matches and whose conditions hold on the state before the step, else the default action); the action runs only if every required capability is present and every withdrawal is available, otherwise nothing moves; then drains remove demand (what is missing stays unmet). The life condition holds when every task condition holds in every state from step 0 to the horizon.

Rules the validator enforces:
- Ids match ^[A-Za-z][A-Za-z0-9_.-]*$ and are unique; every reference names a declared id.
- Numbers are nonnegative; initial <= capacity.
- An action never creates units: per unit, its deposits do not exceed its withdrawals. What an action produces comes from a source stock of the same unit (e.g. "contracts available", "donors reachable"); what the world brings comes as scenario inflows.
- Scenarios differ in their events. A welfare dimension id used by several carriers keeps the same unit and direction.
- routes x scenarios x (horizon + 1) <= 256.
- task.living_carriers name person or living carriers; there is always a life condition: the material condition that keeps those carriers alive or healthy (health, food, water, shelter, money for essentials, an ecosystem's minimum...).
- assumption kinds: MODEL, INITIALIZATION, INFORMATION, SEMANTIC, CALIBRATION, NORMATIVE, PROBABILITY, SYNTHETIC. Every number you had to invent is a hypothesis: list it with provenance "Supuesto del modelador a partir de la pregunta" unless the person gave it. The law is a PROBABILITY assumption.

Modelling guidance: the life condition threshold is the real danger line (where health, livelihood or a living system is actually harmed), and the adverse scenario must be able to cross it when a route really risks it; if every route keeps life in every scenario, check that this is true and not an artifact of generous numbers. Include the routes the person mentions plus the obvious alternatives (keep as is, a prudent one); scenarios cover what is uncertain (good, usual, bad); model every carrier whose wellbeing the decision changes, including people not asking and living systems affected; keep it small and readable. Labels, statements and the name are in the person's language; do not assume the person's gender unless they state it.

If the message contains no decision at all (only a greeting or a fact question), return {"not_a_decision": "one sentence in the person's language saying what Genius needs: a choice between ways of acting"}."""

ASSUMPTION_KINDS = ("MODEL", "INITIALIZATION", "INFORMATION", "SEMANTIC", "CALIBRATION", "NORMATIVE", "PROBABILITY", "SYNTHETIC")


class Unavailable(Exception):
    pass


def client_from_env():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return None
    import anthropic
    return anthropic.Anthropic(max_retries=1)


def _text(response):
    return "".join(block.text for block in response.content if block.type == "text")


def market_answer(client, question):
    """Claude as a person meets it on the market: the question alone."""
    response = client.with_options(timeout=DEADLINE_SECONDS).messages.create(
        model=MODEL, max_tokens=8000, output_config={"effort": "medium"},
        messages=[{"role": "user", "content": question}])
    if response.stop_reason == "refusal":
        return {"status": "REFUSED", "text": ""}
    return {"status": "ANSWERED", "text": _text(response), "model": MODEL}


def _num(value):
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise ValueError(f"not a number: {value!r}")
    n = Fraction(str(value).strip())
    if n < 0:
        raise ValueError(f"negative number: {value!r}")
    return f"{n.numerator}/{n.denominator}"


def _unit(value):
    """A unit as the schema's identifier ("miles de m³" -> "miles_de_m3"); only spelling changes."""
    import re
    import unicodedata
    text = unicodedata.normalize("NFKD", str(value or "unit")).encode("ascii", "ignore").decode()
    text = re.sub(r"[^A-Za-z0-9_.-]+", "_", text).strip("_.-")[:64]
    return text if text[:1].isalpha() else ("u_" + text)[:64] if text else "unit"


def _amounts(values):
    return {k: _num(v) for k, v in (values or {}).items()}


def _predicate(p):
    if "capability" in p:
        return {"kind": "capability", "capability": p["capability"], "present": bool(p.get("present", True))}
    return {"kind": "stock", "stock": p["stock"], "op": p["op"], "value": _num(p["value"])}


def expand(draft):
    """Compact draft -> STOCK_FLOW_FINITE_V1 model: defaults and exact rationals only, no parameter is invented."""
    from genius_twin.stockflow import PROFILE
    stocks = [{"id": s["id"], "label": s.get("label") or s["id"], "unit": _unit(s.get("unit")),
               "kind": s.get("kind", "persistent"), "initial": _num(s["initial"]), "capacity": _num(s["capacity"])}
              for s in draft["stocks"]]
    capabilities = [{"id": c["id"], "label": c.get("label") or c["id"]} for c in draft.get("capabilities") or []] or [{"id": "act", "label": "Capacidad de actuar"}]
    actions = []
    for a in draft["actions"]:
        actions.append({"id": a["id"], "label": a.get("label") or a["id"],
                        "requires": list(a.get("requires") or []), "withdrawals": _amounts(a.get("withdrawals")),
                        "deposits": _amounts(a.get("deposits")), "add_capabilities": list(a.get("add_capabilities") or []),
                        "remove_capabilities": list(a.get("remove_capabilities") or [])})
    policies = [{"id": p["id"], "label": p.get("label") or p["id"], "default_action": p["default_action"],
                 "rules": [{"steps": sorted({int(t) for t in r["steps"]}), "when": [_predicate(x) for x in r.get("when") or []],
                            "action": r["action"]} for r in p.get("rules") or []]} for p in draft["policies"]]
    renewable = {s["id"]: s["capacity"] for s in stocks if s["kind"] == "renewable"}
    scenarios = []
    for s in draft["scenarios"]:
        events = []
        for e in s["events"]:
            given = _amounts(e.get("renewables"))
            events.append({"inflows": _amounts(e.get("inflows")), "renewables": {k: given.get(k, cap) for k, cap in renewable.items()},
                           "drains": _amounts(e.get("drains")), "remove_capabilities": list(e.get("remove_capabilities") or [])})
        scenarios.append({"id": s["id"], "label": s.get("label") or s["id"], "events": events})
    task = draft["task"]
    model = {
        "profile": PROFILE, "name": draft.get("name") or "Decisión", "horizon": int(draft["horizon"]),
        "step_unit": draft.get("step_unit", "step"), "stocks": stocks,
        "carriers": [{"id": c["id"], "label": c.get("label") or c["id"], "kind": c.get("kind", "person")} for c in draft["carriers"]],
        "capabilities": capabilities,
        "initial_capabilities": list(draft["initial_capabilities"]) if "initial_capabilities" in draft else [c["id"] for c in capabilities],
        "actions": actions, "policies": policies, "scenarios": scenarios,
        "law": None if draft.get("law") is None else {k: _num(v) for k, v in draft["law"].items()},
        "welfare": [{"carrier": w["carrier"], "dimension": w["dimension"], "label": w.get("label") or w["dimension"],
                     "stock": w["stock"], "direction": w.get("direction", "higher")} for w in draft["welfare"]],
        "task": {"kind": "life_conditions", "label": task.get("label") or "Condición de vida",
                 "living_carriers": list(task["living_carriers"]),
                 "conditions": [{"stock": c["stock"], "op": c["op"], "threshold": _num(c["threshold"])} for c in task["conditions"]],
                 "require_action_success": False},
        "require_all_scenarios": True, "selection": "none",
        "assumptions": [{"id": a["id"], "kind": a["kind"] if a.get("kind") in ASSUMPTION_KINDS else "MODEL",
                         "statement": a["statement"], "provenance": a.get("provenance") or "Supuesto del modelador a partir de la pregunta"}
                        for a in draft["assumptions"]],
    }
    if model["horizon"] > MAX_HORIZON:
        raise ValueError(f"horizon must be at most {MAX_HORIZON} steps")
    return model


def _json_object(text):
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < start:
        raise ValueError("the answer has no JSON object")
    return json.loads(text[start:end + 1])


def genius_answer(client, question, clock=time.monotonic):
    """Draft, validate (with up to two repairs), evaluate, and read the kernel's results."""
    from genius_twin import registry
    deadline = clock() + DEADLINE_SECONDS
    messages = [{"role": "user", "content": question}]
    errors = []
    for attempt in range(1, 4):
        remaining = deadline - clock()
        if remaining < 20:
            break
        response = client.with_options(timeout=remaining).messages.create(
            model=MODEL, max_tokens=12000, output_config={"effort": "medium"}, system=MODELLER, messages=messages)
        if response.stop_reason == "refusal":
            return {"status": "REFUSED", "attempts": attempt}
        text = _text(response)
        try:
            draft = _json_object(text)
            if isinstance(draft, dict) and "not_a_decision" in draft:
                return {"status": "NOT_A_DECISION", "explanation": str(draft["not_a_decision"]), "attempts": attempt}
            model = expand(draft)
            registry.validate(model)
        except (ValueError, KeyError, TypeError, AttributeError, IndexError, ZeroDivisionError) as error:
            reason = f"{type(error).__name__}: {error}"[:600]
            errors.append(reason)
            messages = messages + [{"role": "assistant", "content": text or "{}"},
                                   {"role": "user", "content": f"The validator rejected the model: {reason}\nReturn the complete corrected JSON object only."}]
            continue
        try:
            results = registry.evaluate(model)["canonical_results"]
        except (RuntimeError, ValueError) as error:
            return {"status": "KERNEL_ERROR", "attempts": attempt, "repairs": errors, "model": model, "error": f"{type(error).__name__}: {error}"[:600]}
        return {"status": "EVALUATED", "attempts": attempt, "repairs": errors, "model": model, "summary": summarize(model, results)}
    return {"status": "MODEL_NOT_VALID", "attempts": len(errors), "repairs": errors}


def recalculate(model, changes=()):
    """The person's corrected model, judged by the kernel alone: no language model, no new hypotheses."""
    from genius_twin import registry
    model = expand(model)
    if changes:
        model["assumptions"] = [a for a in model["assumptions"] if a["id"] != "person_corrections"] + [{
            "id": "person_corrections", "kind": "CALIBRATION",
            "statement": "Valores corregidos por la persona: " + "; ".join(changes)[:1900],
            "provenance": "Corrección de la persona sobre el modelo redactado por la IA"}]
    registry.validate(model)
    results = registry.evaluate(model)["canonical_results"]
    return {"status": "EVALUATED", "recalculated": True, "model": model, "summary": summarize(model, results)}


def summarize(model, results):
    """The kernel's verdict in the order Pedro set (2026-10-18): life condition and PVS first, then each carrier's best routes."""
    policies = results["policies"]
    decision = results["decision"]
    labels = {p["id"]: p["label"] for p in model["policies"]}
    welfare_labels = {(w["carrier"], w["dimension"]): w["label"] for w in model["welfare"]}
    routes = []
    for p in model["policies"]:
        row = policies[p["id"]]
        by_scenario = row["by_scenario"]
        pvs = row["pvs"]
        routes.append({
            "id": p["id"], "label": p["label"],
            "keeps_life_in": [s for s, cell in by_scenario.items() if cell["task_status"] == "success"],
            "loses_life_in": [s for s, cell in by_scenario.items() if cell["task_status"] == "failure"],
            "pvs": {"value": pvs["value"], "state": pvs["state"], "law_range": pvs.get("law_range")},
            "cag_robust": len(row["cag"]["robust"] or []),
            "wellbeing": {s: [{**w, "label": welfare_labels[(w["carrier"], w["dimension"])]} for w in cell["wellbeing"]]
                          for s, cell in by_scenario.items()},
        })
    keep = [r["id"] for r in routes if not r["loses_life_in"] and len(r["keeps_life_in"]) == len(model["scenarios"])]
    carriers = []
    for c in model["carriers"]:
        verdict = decision["by_actor"]["by_carrier"][c["id"]]
        carriers.append({"id": c["id"], "label": c["label"], "kind": c["kind"], "best": verdict["best"], "status": verdict["status"]})
    best_sets = {tuple(sorted(c["best"] or [])) for c in carriers if c["best"]}
    return {
        "name": model["name"], "horizon": model["horizon"], "step_unit": model["step_unit"],
        "life_condition": model["task"]["label"],
        "living_carriers": model["task"]["living_carriers"],
        "scenarios": [{"id": s["id"], "label": s["label"], "probability": (model["law"] or {}).get(s["id"])} for s in model["scenarios"]],
        "routes": routes, "route_labels": labels,
        "life_filter": {"keep_life_everywhere": keep, "none_keeps_life": not keep},
        "carriers": carriers,
        "carriers_disagree": len(best_sets) > 1,
        "candidates": decision["by_actor"]["candidates"],
        "assumptions": model["assumptions"],
        "rule": "Primero la condición de vida y la PVS; después, para cada portador, las rutas que ninguna otra supera en lo suyo. Sin sumar criterios.",
    }


def install(app, APIError, fail_quota):
    static = os.path.join(os.path.dirname(__file__), "static")
    state = {"client": None, "loaded": False}

    def client():
        if not state["loaded"]:
            state["client"] = app.config.get("COMPARE_CLIENT") or client_from_env()
            state["loaded"] = True
        if state["client"] is None:
            raise APIError("compare_not_configured", "La comparación todavía no está configurada en este servidor.", 503)
        return state["client"]

    def question():
        data = request.get_json(silent=True)
        text = data.get("question") if isinstance(data, dict) else None
        if not isinstance(text, str) or not text.strip() or len(text) > MAX_QUESTION:
            raise APIError("invalid_question", f"Escribí una pregunta de hasta {MAX_QUESTION} caracteres.", 400)
        return text.strip()

    def limits(side, uid):
        fail_quota(f"compare-{side}:{uid}", app.config["MAX_COMPARE_DAILY"])
        fail_quota(f"compare-{side}-global", app.config["MAX_GLOBAL_COMPARE_DAILY"])

    @app.get("/comparar")
    def compare_page():
        return send_from_directory(static, "compare.html")

    @app.get("/api/compare/status")
    def compare_status():
        try:
            client()
            enabled = True
        except APIError:
            enabled = False
        return jsonify(enabled=enabled, model=MODEL, stores_questions=False)

    def answer(side, run):
        text = question()
        model = client()
        limits(side, g.user["id"])
        try:
            return jsonify(run(model, text))
        except Exception as error:
            if not type(error).__module__.startswith("anthropic"):
                raise
            app.logger.warning("compare_upstream_failed side=%s class=%s", side, type(error).__name__)
            raise APIError("compare_upstream", "La IA no respondió a tiempo. Probá de nuevo en un momento.", 502)

    @app.post("/api/compare/market")
    def compare_market():
        return answer("market", market_answer)

    @app.post("/api/compare/genius")
    def compare_genius():
        return answer("genius", genius_answer)

    @app.post("/api/compare/recalculate")
    def compare_recalculate():
        data = request.get_json(silent=True)
        model = data.get("model") if isinstance(data, dict) else None
        changes = data.get("changes", []) if isinstance(data, dict) else []
        if not isinstance(model, dict) or not isinstance(changes, list) or len(changes) > 100 \
                or not all(isinstance(c, str) and len(c) <= 200 for c in changes):
            raise APIError("invalid_model", "Mandá el modelo y la lista de correcciones.", 400)
        fail_quota(f"compare-recalculate:{g.user['id']}", app.config["MAX_COMPARE_RECALCULATIONS_DAILY"])
        try:
            return jsonify(recalculate(model, changes))
        except (ValueError, KeyError, TypeError, AttributeError, IndexError, ZeroDivisionError, RuntimeError) as error:
            raise APIError("invalid_model", f"El modelo corregido no es válido: {error}"[:400], 400)
