"""Genius for companies: a decision report within the planetary boundaries.

A company describes one decision (a product, a supplier, a site, an investment,
a target). The language model only drafts the model, as in /comparar, with the
company's people and the living systems it touches, and tags the stocks that
measure a planetary boundary. The kernel evaluates every route in every
scenario; the report reads its results: life condition and PVS per route and
scenario, the best routes for each carrier, and how each route leaves each
boundary. Nothing is summed and nothing is stored.
"""
from fractions import Fraction
import os

from flask import g, jsonify, request, send_from_directory

from . import compare

# Planetary Health Check 2025: seven of the nine boundaries are crossed (aerosols and ozone are not).
BOUNDARIES = {
    "climate": ("Cambio climático", "Climate change"),
    "biosphere": ("Integridad de la biosfera", "Biosphere integrity"),
    "land": ("Cambio en el uso del suelo", "Land-system change"),
    "freshwater": ("Agua dulce", "Freshwater change"),
    "nutrients": ("Flujos de nitrógeno y fósforo", "Nitrogen and phosphorus flows"),
    "novel_entities": ("Entidades nuevas (químicos, plásticos)", "Novel entities (chemicals, plastics)"),
    "ocean_acidification": ("Acidificación del océano", "Ocean acidification"),
    "aerosols": ("Aerosoles en la atmósfera", "Atmospheric aerosol loading"),
    "ozone": ("Capa de ozono", "Stratospheric ozone depletion"),
}

GUIDE = """

This is a company's decision (a product, a supplier, a site, an investment, a target, a way of operating). In addition to the rules above:
- Carriers include the company (organization), its workers (person), the people outside it who live the consequences (community, customers or suppliers: person) and every living system the decision touches (living: a river, a forest, a soil, the climate's future generations).
- Planetary boundaries: add "boundary" to every stock that measures the state of, or the room left within, a planetary boundary, using one of: """ + ", ".join(BOUNDARIES) + """. Prefer stocks where higher is better (CO2 budget left, water left in the basin, native habitat area, clean soil). Each such stock is a welfare dimension of a living carrier. At least one stock carries a boundary.
- Use "step_unit": "step" and add "step_label": the period of one step in the person's language (for example "trimestre", "año", "quarter", "year"); 2 to 8 steps.
- The life condition covers both the people's essentials (income or jobs for essentials, health) and the living systems' minimum.
- Routes: the options the company names, plus business as usual and one route that tries to stay within the boundaries; scenarios cover market and nature uncertainty (good, usual, bad)."""

MODELLER = compare.MODELLER + GUIDE
MAX_FIELD = 1500


def tags(draft, model):
    """The boundary tags and period label the kernel does not use."""
    stocks = {s["id"] for s in model["stocks"]}
    found = {}
    for s in draft["stocks"]:
        tag = s.get("boundary")
        if tag in (None, "", "none"):
            continue
        if tag not in BOUNDARIES:
            raise ValueError(f"stock {s['id']}: boundary must be one of {', '.join(BOUNDARIES)}")
        found[s["id"]] = tag
    if not found:
        raise ValueError("no stock carries a planetary boundary; tag at least one with \"boundary\"")
    welfare = {w["stock"] for w in model["welfare"]}
    missing = [sid for sid in found if sid not in welfare or sid not in stocks]
    if missing:
        raise ValueError(f"boundary stocks must be welfare dimensions of a living carrier: {', '.join(missing)}")
    return {"boundaries": found, "step_label": str(draft.get("step_label") or "")[:40]}


def boundary_view(result):
    """For each boundary stock: where every route leaves it in every scenario, and which routes leave the most room."""
    if result.get("status") != "EVALUATED":
        return result
    summary, model = result["summary"], result["model"]
    stocks = {s["id"]: s for s in model["stocks"]}
    rows = []
    for sid, tag in result["boundaries"].items():
        by_scenario, best = {}, {}
        direction = "higher"
        for scenario in summary["scenarios"]:
            cells = {}
            for route in summary["routes"]:
                w = next(x for x in route["wellbeing"][scenario["id"]] if x["stock"] == sid)
                direction = w["direction"]
                cells[route["id"]] = {"final": w["final"], "worst": w["worst"]}
            values = {r: Fraction(c["final"]) for r, c in cells.items()}
            top = (max if direction == "higher" else min)(values.values())
            by_scenario[scenario["id"]] = cells
            best[scenario["id"]] = [r for r, v in values.items() if v == top]
        rows.append({"stock": sid, "label": stocks[sid]["label"], "unit": stocks[sid]["unit"], "boundary": tag,
                     "boundary_label": BOUNDARIES[tag], "initial": stocks[sid]["initial"], "direction": direction,
                     "by_scenario": by_scenario, "most_room": best})
    result["planetary"] = rows
    return result


def report(client, question):
    return boundary_view(compare.genius_answer(client, question, system=MODELLER, extra=tags))


def question_from(data):
    fields = [("company", "Empresa / Company"), ("place", "Dónde opera / Where"), ("decision", "Decisión / Decision"),
              ("options", "Opciones que evalúa / Options"), ("horizon", "Horizonte / Horizon")]
    parts = []
    for key, label in fields:
        value = data.get(key, "") if isinstance(data, dict) else ""
        if not isinstance(value, str) or len(value) > MAX_FIELD:
            return None
        if value.strip():
            parts.append(f"{label}: {value.strip()}")
    if not isinstance(data, dict) or not str(data.get("decision") or "").strip():
        return None
    lang = "English" if data.get("lang") == "en" else "Spanish"
    return "\n".join(parts) + f"\n\nWrite every label, statement and the name in {lang}."


def install(app, APIError, fail_quota, client):
    static = os.path.join(os.path.dirname(__file__), "static")

    @app.get("/business")
    def business_page():
        return send_from_directory(static, "business.html")

    @app.get("/empresas")
    def business_page_es():
        return send_from_directory(static, "empresas.html")

    @app.get("/business/report")
    def business_report_page():
        return send_from_directory(static, "report.html")

    @app.get("/empresas/informe")
    def business_report_page_es():
        return send_from_directory(static, "informe.html")

    @app.post("/api/business/report")
    def business_report():
        text = question_from(request.get_json(silent=True))
        if text is None:
            raise APIError("invalid_decision", f"Describí la decisión (hasta {MAX_FIELD} caracteres por campo).", 400)
        model = client()
        fail_quota(f"business:{g.user['id']}", app.config["MAX_COMPARE_DAILY"])
        fail_quota("business-global", app.config["MAX_GLOBAL_COMPARE_DAILY"])
        try:
            return jsonify(report(model, text))
        except Exception as error:
            if not type(error).__module__.startswith("anthropic"):
                raise
            app.logger.warning("business_upstream_failed class=%s", type(error).__name__)
            raise APIError("compare_upstream", "La IA no respondió a tiempo. Probá de nuevo en un momento.", 502)

    @app.post("/api/business/recalculate")
    def business_recalculate():
        data = request.get_json(silent=True)
        model = data.get("model") if isinstance(data, dict) else None
        changes = data.get("changes", []) if isinstance(data, dict) else []
        boundaries = data.get("boundaries") if isinstance(data, dict) else None
        if not isinstance(model, dict) or not isinstance(boundaries, dict) or not isinstance(changes, list) or len(changes) > 100 \
                or not all(isinstance(c, str) and len(c) <= 200 for c in changes):
            raise APIError("invalid_model", "Mandá el modelo, sus límites planetarios y la lista de correcciones.", 400)
        fail_quota(f"compare-recalculate:{g.user['id']}", app.config["MAX_COMPARE_RECALCULATIONS_DAILY"])
        try:
            result = compare.recalculate(model, changes)
            result.update(tags({"stocks": [{"id": k, "boundary": v} for k, v in boundaries.items()],
                                "step_label": data.get("step_label")}, result["model"]))
            return jsonify(boundary_view(result))
        except (ValueError, KeyError, TypeError, AttributeError, IndexError, ZeroDivisionError, RuntimeError) as error:
            raise APIError("invalid_model", f"El modelo corregido no es válido: {error}"[:400], 400)
