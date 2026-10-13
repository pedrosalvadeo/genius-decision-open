"""Explicit, bounded synthetic semillero model. This is not an empirical predictor.

Each day's committed routine is a causal macro action. Its sensor/attendance
contingencies are evaluated by the transition, not by an anticipatory policy.
No result table, CAG set, probability of success or winning policy is stored here.
"""
from copy import deepcopy
from fractions import Fraction
import re

PROFILE = "SEMILLERO_14D_SYNTHETIC_V1"
SCENARIOS = ("N", "H", "HA")
FIELDS = {"profile", "horizon", "policies", "water_budget_liters", "law",
          "require_all_scenarios"}
SIGNATURES = {
    "q0": ("manual_care",),
    "q1": ("manual_care", "reservoir", "response_protocol", "trained_operators"),
    "q2": ("manual_care", "reservoir", "response_protocol", "trained_operators",
           "verified_propagation_unit"),
}


def default_model():
    """Return a fresh proposal; acceptance/provenance belong to the case service."""
    return {"profile": PROFILE, "horizon": 14, "policies": ["C", "R", "E"],
            "water_budget_liters": 18,
            "law": {"N": "1/2", "H": "1/3", "HA": "1/6"},
            "require_all_scenarios": True}


def validate_model(model):
    """Reject undeclared extension, invalid law and unsupported domain changes."""
    if not isinstance(model, dict) or set(model) != FIELDS:
        raise ValueError("Model requires exactly the declared D1 fields")
    if model["profile"] != PROFILE:
        raise ValueError("Unsupported profile; D1 is a declared synthetic model")
    if type(model["horizon"]) is not int or model["horizon"] != 14:
        raise ValueError("D1 admits exactly 14 daily transitions")
    if type(model["water_budget_liters"]) is not int or model["water_budget_liters"] != 18:
        raise ValueError("D1 declares one shared additional water budget of 18 L")
    if model["policies"] not in (["C", "R", "E"], ["C", "R", "E_prime"]):
        raise ValueError("Admitted families are C/R/E and C/R/E_prime")
    if type(model["require_all_scenarios"]) is not bool:
        raise ValueError("require_all_scenarios is a normative boolean")
    law = model["law"]
    if not isinstance(law, dict) or set(law) != set(SCENARIOS):
        raise ValueError("The joint law must cover N, H and HA exactly")
    weights = []
    for scenario in SCENARIOS:
        text = law[scenario]
        if (not isinstance(text, str) or len(text) > 32 or
                not re.fullmatch(r"(?:0|[1-9][0-9]*)/[1-9][0-9]*", text)):
            raise ValueError("Joint masses must be bounded canonical rational strings")
        value = Fraction(text)
        if text != f"{value.numerator}/{value.denominator}":
            raise ValueError("Joint masses must be reduced canonical rationals")
        if not 0 <= value <= 1:
            raise ValueError("Joint masses must be between zero and one")
        weights.append(value)
    if sum(weights) != 1:
        raise ValueError("The supplied joint law must sum exactly to one")


def _initial(budget):
    return {"day": 0, "water_in_tray_liters": 2, "demand_liters": 0,
            "water_applied_liters": 0, "test_water_liters": 0,
            "water_used_liters": 0, "water_remaining_liters": budget,
            "minutes_a": 0, "minutes_b": 0, "available_a_minutes": 60,
            "available_b_minutes": 60, "violation_seen": False,
            "organization": "q0", "plants_alive": {"P1": True, "P2": True},
            "formation_completed": False, "verification_completed": False,
            "observed_event": "not_observed"}


def daily_transition(previous, day, policy, external_event, budget=18):
    """Execute one declared daily routine on its current state and today's input.

    external_event is absent except at day 10. Future events are never read.
    A routine can prescribe observation followed by irrigation within this
    daily macro step; FP1 treats the whole committed routine as its action.
    """
    if external_event is not None and (day != 10 or external_event not in SCENARIOS):
        raise ValueError("External event is admitted only at the critical day")
    if day == 10 and external_event not in SCENARIOS:
        raise ValueError("Day 10 needs its complete joint event")
    hot = external_event in ("H", "HA")
    absent = external_event == "HA"
    demand = 3 if hot else 1
    water = 1
    soil_before = previous["water_in_tray_liters"]
    if policy == "C":
        a, b = 20, 0
        if soil_before < 1:
            water, a = 3, 30
    elif policy == "R" or day <= 7:
        a, b = ((30, 30) if day == 1 else
                (10, 0) if day % 2 == 0 else (0, 10))
        if day == 10:
            water = demand
    else:
        formation_day = 9 if policy == "E_prime" else 10
        a = 60 if day == formation_day else 30
        b = 0 if absent else 20
        if day == 10:
            if absent and policy == "E":
                water = 0
            else:
                water = demand
                if absent:  # E_prime: A is available and uses the reserve.
                    a += 10
        if soil_before < 1:
            water, b = 3, 30

    formation = previous["formation_completed"]
    verification = previous["verification_completed"]
    if policy in ("E", "E_prime"):
        planned_day = 9 if policy == "E_prime" else 10
        if day == planned_day:
            formation = True
            verification = not absent
    organization = "q0" if policy == "C" or day < 7 else "q1"
    test_water = 0
    if day == 14 and formation and verification:
        organization, test_water = "q2", 2
    soil = max(0, min(2, soil_before + water - demand))
    used = previous["water_used_liters"] + water + test_water
    if used > budget or max(a, b) > 60:
        raise ValueError("Generated transition exceeds the declared resource boundary")
    return {"day": day, "water_in_tray_liters": soil,
            "demand_liters": demand, "water_applied_liters": water,
            "test_water_liters": test_water, "water_used_liters": used,
            "water_remaining_liters": budget - used,
            "minutes_a": a, "minutes_b": b,
            "available_a_minutes": 60 - a, "available_b_minutes": 60 - b,
            "violation_seen": previous["violation_seen"] or soil < 1,
            "organization": organization,
            "plants_alive": deepcopy(previous["plants_alive"]),
            "formation_completed": formation, "verification_completed": verification,
            "observed_event": external_event or previous["observed_event"]}


def compute_trajectories(model):
    """Generate all causal scenarios, retaining even zero-probability branches."""
    validate_model(model)
    result = {}
    for policy in model["policies"]:
        result[policy] = {}
        for scenario in SCENARIOS:
            daily = [_initial(model["water_budget_liters"])]
            for day in range(1, model["horizon"] + 1):
                daily.append(daily_transition(daily[-1], day, policy,
                             scenario if day == 10 else None,
                             model["water_budget_liters"]))
            result[policy][scenario] = {
                "daily": daily,
                "totals": {"water_liters": daily[-1]["water_used_liters"],
                           "minutes_a": sum(r["minutes_a"] for r in daily),
                           "minutes_b": sum(r["minutes_b"] for r in daily)},
            }
    return result
