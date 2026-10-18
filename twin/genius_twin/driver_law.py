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
overlap; the caller declares both. The result is labelled RETROSPECTIVE_PREQUENTIAL:
prospective contrasts must later confirm it or the law is revoked. Masses are exact
fractions; confidence bounds are floats used only for the check.
"""
from fractions import Fraction
import math

FORMAT = "genius-driver-law/1"
MIN_INDEPENDENT_OUTCOMES = 30
MAX_PERIODS = 400


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
    forecasts = [procedure(followed[:i], scenarios) for i in range(len(followed))]
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


def certificate(series, anchors, tie=None, confidence=Fraction(95, 100), driver="driver"):
    """`series`: [{"period", "value"}] oldest first; `anchors`: {scenario: value}, 2 to 8 scenarios."""
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
        outcomes=len(series), followed={s: followed.count(s) for s in scenarios},
        classification=[{"period": p, "scenario": f} for p, f in zip(periods, followed)],
        evaluation=dict(kind="RETROSPECTIVE_PREQUENTIAL", confidence=str(confidence), candidates=results),
        chosen=chosen, law=None if law is None else {s: str(v) for s, v in law.items()},
        refusals=refusals, admitted=not refusals,
        declared_by_caller=["the driver does not depend on the compared routes", "periods do not overlap"],
        meaning=("Masa empírica de que cada período se parezca más a cada escenario, según el conductor declarado. "
                 "Retrospectiva precuencial: se revoca si los contrastes prospectivos la descalibran. No es bienestar."))
