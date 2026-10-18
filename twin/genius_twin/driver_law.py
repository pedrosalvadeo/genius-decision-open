"""Empirical scenario law from any exogenous driver series (AM-02, any domain).

A twin's scenarios are anchored on one exogenous driver: snow, river inflow, cases
per week, demand, prices. Given the driver's history (one value per independent
period, oldest first) and the anchor value of each scenario, every past period is
assigned to the scenario whose anchor it was closest to. Two candidate procedures
are fixed in advance: equal masses, and the Laplace-smoothed frequency (k + 1) / (n + K)
of the earlier periods. Each is checked prequentially (the forecast for a period
uses only earlier periods): per-scenario calibration with exact Clopper-Pearson
intervals and a Bonferroni correction, and mean log score. Among calibrated
candidates the best score is chosen; the law is admitted only with no refusal.

The driver must not depend on the routes the twin compares, and periods must not
overlap; the caller declares both. Only the most recent WINDOW periods are used (rule
chosen by Pedro on 2026-10-18 for every domain: a drivers' climate or regime can drift, as
the Colorado basin's did after 2000, and the latest 30 periods describe the present best);
`window=None` uses the whole series and is reported as such. The result is labelled RETROSPECTIVE_PREQUENTIAL:
prospective contrasts must later confirm it or the law is revoked. Masses are exact
fractions; confidence bounds are floats used only for the check.
"""
from fractions import Fraction
from itertools import product
import math

FORMAT = "genius-driver-law/1"
MIN_INDEPENDENT_OUTCOMES = 30
MAX_PERIODS = 400
WINDOW = MIN_INDEPENDENT_OUTCOMES


def _fraction(value, where):
    try:
        return Fraction(str(value))
    except (TypeError, ValueError, ZeroDivisionError) as exc:
        raise ValueError(f"{where}: not an exact number") from exc


def uniform(known, scenarios):
    return {s: Fraction(1, len(scenarios)) for s in scenarios}


def frequency(known, scenarios):
    total = len(known) + len(scenarios)
    return {s: Fraction(sum(o == s for o in known) + 1, total) for s in scenarios}


CANDIDATES = {"uniform": uniform, "frequency": frequency}


def _binomial_cdf(k, n, p):
    return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k + 1))


def clopper_pearson(k, n, confidence):
    """Exact two-sided interval for a binomial proportion, by bisection."""
    tail = (1 - confidence) / 2

    def solve(target, cdf_at):
        low, high = 0.0, 1.0
        for _ in range(60):
            mid = (low + high) / 2
            if cdf_at(mid) > target:
                low = mid
            else:
                high = mid
        return (low + high) / 2

    lower = 0.0 if k == 0 else solve(1 - tail, lambda p: _binomial_cdf(k - 1, n, p))
    upper = 1.0 if k == n else solve(tail, lambda p: _binomial_cdf(k, n, p))
    return lower, upper


def evaluate(followed, scenarios, procedure, confidence):
    """Prequential check of one candidate over the classified periods, oldest first."""
    return check([procedure(followed[:i], scenarios) for i in range(len(followed))], followed, scenarios, confidence)


def check(forecasts, followed, scenarios, confidence):
    """Calibration per scenario (Clopper-Pearson, Bonferroni) and mean log score of given forecasts."""
    n = len(forecasts)
    per_band = 1 - (1 - float(confidence)) / len(scenarios)
    bands, calibrated = {}, n > 0
    for s in scenarios:
        k = sum(f == s for f in followed)
        mean_mass = sum(f[s] for f in forecasts) / n if n else Fraction(0)
        low, high = clopper_pearson(k, n, per_band) if n else (0.0, 1.0)
        inside = low <= float(mean_mass) <= high
        calibrated = calibrated and inside
        bands[s] = dict(observed=k, mean_mass=round(float(mean_mass), 4), interval=[round(low, 4), round(high, 4)], inside=inside)
    score = sum(math.log(f[o]) for f, o in zip(forecasts, followed)) / n if n else None
    return dict(count=n, per_band_confidence=round(per_band, 6), bands=bands, calibrated=calibrated,
                mean_log_score=None if score is None else round(score, 6))


def certificate(series, anchors, tie=None, confidence=Fraction(95, 100), driver="driver", window=WINDOW):
    """`series`: [{"period", "value"}] oldest first; `anchors`: {scenario: value}, 2 to 8 scenarios.

    `window`: how many of the most recent periods to use (None for all)."""
    if not isinstance(anchors, dict) or not 2 <= len(anchors) <= 8:
        raise ValueError("anchors: 2 to 8 scenarios")
    scenarios = list(anchors)
    anchor = {s: _fraction(v, f"anchors.{s}") for s, v in anchors.items()}
    if len(set(anchor.values())) != len(anchor):
        raise ValueError("anchors: two scenarios share a value")
    tie = scenarios[0] if tie is None else tie
    if tie not in anchor:
        raise ValueError("tie: not a scenario")
    if not isinstance(series, list) or not 1 <= len(series) <= MAX_PERIODS:
        raise ValueError(f"series: 1 to {MAX_PERIODS} periods")
    periods = [str(p.get("period", "")) for p in series]
    if len(set(periods)) != len(periods) or "" in periods:
        raise ValueError("series: periods must be present and unique")
    if window is not None and (isinstance(window, bool) or not isinstance(window, int) or window < 1):
        raise ValueError("window: a positive integer or null")
    offered = len(series)
    if window is not None:
        series, periods = series[-window:], periods[-window:]
    values = [_fraction(p.get("value"), f"series.{p.get('period')}") for p in series]
    followed = [min(scenarios, key=lambda s: (abs(v - anchor[s]), s != tie)) for v in values]
    results = {name: evaluate(followed, scenarios, procedure, confidence) for name, procedure in CANDIDATES.items()}
    eligible = sorted((r["mean_log_score"], name) for name, r in results.items() if r["calibrated"])
    chosen = eligible[-1][1] if eligible else None
    refusals = []
    if chosen is None:
        refusals.append("NO_CALIBRATED_CANDIDATE")
    if len(series) < MIN_INDEPENDENT_OUTCOMES:
        refusals.append(f"INSUFFICIENT_EVIDENCE: {len(series)} independent outcomes, {MIN_INDEPENDENT_OUTCOMES} required")
    law = None if chosen is None else CANDIDATES[chosen](followed, scenarios)
    return dict(
        format=FORMAT, amendment="AM-02", driver=driver, anchors={s: str(v) for s, v in anchor.items()}, tie=tie,
        window=window, periods_offered=offered, outcomes=len(series), followed={s: followed.count(s) for s in scenarios},
        classification=[{"period": p, "scenario": f} for p, f in zip(periods, followed)],
        evaluation=dict(kind="RETROSPECTIVE_PREQUENTIAL", confidence=str(confidence), candidates=results),
        chosen=chosen, law=None if law is None else {s: str(v) for s, v in law.items()},
        refusals=refusals, admitted=not refusals,
        declared_by_caller=["the driver does not depend on the compared routes", "periods do not overlap"],
        meaning=("Masa empírica de que cada período se parezca más a cada escenario, según el conductor declarado. "
                 "Retrospectiva precuencial: se revoca si los contrastes prospectivos la descalibran. No es bienestar."))


# Proposed amendment AM-02.1 (GENIUS_PROGRAM/theory/PROPOSAL_AM-02.1.md), pending Pedro's review:
# a law over scenarios defined by two or three drivers at once. Not served by the API or MCP.
JOINT_FORMAT = "genius-joint-driver-law/1"
MAX_DRIVERS = 3


def _classify(series, anchors, tie, where):
    if not isinstance(anchors, dict) or not 2 <= len(anchors) <= 8:
        raise ValueError(f"{where}.anchors: 2 to 8 categories")
    if not all(isinstance(c, str) and c for c in anchors):
        raise ValueError(f"{where}.anchors: categories must be non-empty strings")
    anchor = {c: _fraction(v, f"{where}.anchors.{c}") for c, v in anchors.items()}
    if len(set(anchor.values())) != len(anchor):
        raise ValueError(f"{where}.anchors: two categories share a value")
    tie = list(anchor)[0] if tie is None else tie
    if tie not in anchor:
        raise ValueError(f"{where}.tie: not a category")
    if not isinstance(series, list) or not 1 <= len(series) <= MAX_PERIODS:
        raise ValueError(f"{where}.series: 1 to {MAX_PERIODS} periods")
    out = {}
    for row in series:
        period = str(row.get("period", ""))
        if not period or period in out:
            raise ValueError(f"{where}.series: periods must be present and unique")
        value = _fraction(row.get("value"), f"{where}.series.{period}")
        out[period] = min(anchor, key=lambda c: (abs(value - anchor[c]), c != tie))
    return out, anchor, tie


def joint_certificate(drivers, scenarios, confidence=Fraction(95, 100), window=WINDOW):
    """`drivers`: [{"name", "series", "anchors", "tie"?}], 2 or 3, sharing period labels;
    `scenarios`: {scenario: [[category per driver], ...]}, 2 to 8, partitioning every combination.
    A scenario of several cells is {"cells": [...], "representative": [cell]}: the realization the
    twin computes for it, so a PVS under this law holds for that representative only (AM-02 repair 2).
    The partition must be fixed from the twin and its task before looking at the joint record.

    Each common period, oldest first, falls in the cell of its nearest anchors and so in one
    scenario. Three candidates are fixed in advance: equal masses, the Laplace frequency of the
    scenarios, and the product of each driver's Laplace marginal frequencies (independence of the
    drivers), summed over each scenario's cells. They are checked exactly as in `certificate`."""
    if not isinstance(drivers, list) or not 2 <= len(drivers) <= MAX_DRIVERS:
        raise ValueError(f"drivers: 2 to {MAX_DRIVERS}")
    names = [str(d.get("name", "")) for d in drivers]
    if len(set(names)) != len(names) or "" in names:
        raise ValueError("drivers: names must be present and unique")
    classified, anchors, ties = [], [], []
    for name, d in zip(names, drivers):
        c, a, t = _classify(d.get("series"), d.get("anchors"), d.get("tie"), f"drivers.{name}")
        classified.append(c); anchors.append(a); ties.append(t)
    categories = [list(a) for a in anchors]
    if not isinstance(scenarios, dict) or not 2 <= len(scenarios) <= 8:
        raise ValueError("scenarios: 2 to 8")
    cell_of, representative = {}, {}
    for sid, spec in scenarios.items():
        cells = spec.get("cells") if isinstance(spec, dict) else spec
        if not isinstance(cells, list) or not cells:
            raise ValueError(f"scenarios.{sid}: at least one cell")
        rep = spec.get("representative") if isinstance(spec, dict) else (cells[0] if len(cells) == 1 else None)
        if rep is None:
            raise ValueError(f"scenarios.{sid}: a scenario of several cells declares its representative cell")
        if not isinstance(rep, list) or rep not in cells:
            raise ValueError(f"scenarios.{sid}: the representative must be one of its cells")
        representative[sid] = list(rep)
        for cell in cells:
            cell = tuple(cell) if isinstance(cell, list) else None
            if cell is None or len(cell) != len(drivers) or any(c not in cats for c, cats in zip(cell, categories)):
                raise ValueError(f"scenarios.{sid}: each cell names one category per driver")
            if cell in cell_of:
                raise ValueError(f"scenarios: cell {list(cell)} is in two scenarios")
            cell_of[cell] = sid
    missing = [list(cell) for cell in product(*categories) if cell not in cell_of]
    if missing:
        raise ValueError(f"scenarios: combinations without a scenario: {missing[:4]}")
    if window is not None and (isinstance(window, bool) or not isinstance(window, int) or window < 1):
        raise ValueError("window: a positive integer or null")
    orders = [[p for p in c if all(p in other for other in classified)] for c in classified]
    if any(o != orders[0] for o in orders):
        raise ValueError("drivers: the common periods must be listed in the same order, oldest first")
    common = orders[0]
    dropped = sorted(set().union(*classified) - set(common))
    offered = len(common)
    if window is not None:
        common = common[-window:]
    cells = [tuple(c[p] for c in classified) for p in common]
    sids = list(scenarios)
    followed = [cell_of[cell] for cell in cells]

    def independent(i):
        marginal = [{c: Fraction(sum(cell[j] == c for cell in cells[:i]) + 1, i + len(cats)) for c in cats}
                    for j, cats in enumerate(categories)]
        law = dict.fromkeys(sids, Fraction(0))
        for cell, sid in cell_of.items():
            mass = Fraction(1)
            for j, c in enumerate(cell):
                mass *= marginal[j][c]
            law[sid] += mass
        return law

    forecasts = {"uniform": [uniform(followed[:i], sids) for i in range(len(followed) + 1)],
                 "frequency": [frequency(followed[:i], sids) for i in range(len(followed) + 1)],
                 "independent_drivers": [independent(i) for i in range(len(followed) + 1)]}
    results = {name: check(f[:-1], followed, sids, confidence) for name, f in forecasts.items()}
    eligible = sorted((r["mean_log_score"], name) for name, r in results.items() if r["calibrated"])
    chosen = eligible[-1][1] if eligible else None
    refusals = []
    if chosen is None:
        refusals.append("NO_CALIBRATED_CANDIDATE")
    if len(common) < MIN_INDEPENDENT_OUTCOMES:
        refusals.append(f"INSUFFICIENT_EVIDENCE: {len(common)} independent outcomes, {MIN_INDEPENDENT_OUTCOMES} required")
    law = None if chosen is None else forecasts[chosen][-1]
    table = {" × ".join(cell): sum(c == cell for c in cells) for cell in product(*categories)}
    return dict(
        format=JOINT_FORMAT, amendment="AM-02.1 (PROPOSED, NOT ADMITTED UNTIL REVIEWED)", drivers=[
            dict(name=n, anchors={c: str(v) for c, v in a.items()}, tie=t) for n, a, t in zip(names, anchors, ties)],
        scenarios={sid: [list(cell) for cell, s in cell_of.items() if s == sid] for sid in sids},
        representatives=representative, window=window, periods_offered=offered, periods_without_every_driver=dropped, outcomes=len(common), joint_table=table,
        followed={s: followed.count(s) for s in sids},
        classification=[{"period": p, "cell": list(cell), "scenario": f} for p, cell, f in zip(common, cells, followed)],
        evaluation=dict(kind="RETROSPECTIVE_PREQUENTIAL", confidence=str(confidence), candidates=results),
        chosen=chosen, law=None if law is None else {s: str(v) for s, v in law.items()},
        refusals=refusals, admitted=not refusals,
        low_power=[s for s in sids if followed.count(s) < 5],
        assumptions=["independence of the drivers"] if chosen == "independent_drivers" else [],
        declared_by_caller=["the scenario partition was fixed before looking at the joint record", "no driver depends on the compared routes", "periods do not overlap",
                            "the same period label means the same period for every driver"],
        meaning=("Masa empírica conjunta de que cada período caiga en cada escenario, según varios conductores a la vez. "
                 "La candidata de conductores independientes es un supuesto que la calibración conjunta pone a prueba; "
                 "no rechazarlo no lo demuestra. Retrospectiva precuencial. No es bienestar."))
