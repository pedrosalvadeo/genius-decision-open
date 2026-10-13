"""Reproducible synthetic conformance examples, never empirical observations.

The received R2 test fixture builder constructs typed FDQ requests; real R2
operations and the pinned R1/R0 certificate code then produce the receipts.
"""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / "product_local"))
sys.path.insert(0, str(ROOT.parent / "product_local" / "tests"))
sys.path.insert(0, str(ROOT))

from genius_local.controller import execute
from genius_views import render_case
from test_acceptance import make_fdq, make_hours, unknown, canonical, sha


SCENARIOS = (
    ("fdq_frontier", "historical", "frontier", None, "PR_SET_OR_INCOMPARABLE"),
    ("fdq_selector_absent", "none", "selector", None, "PR_JUSTIFIED_RESULT"),
    ("fdq_infeasible", "infeasible", "frontier", None, "PR_PROVEN_INFEASIBLE"),
    ("fdq_false_claim", "historical", "selector", "false_claim", "PR_DEPENDENCY"),
    ("fdq_outside", "historical", "selector", "profile_boundary", "PR_OUTSIDE_PROFILE"),
)


def scenario_fixture(directory, family, kind, mutation, r0):
    fixture = make_fdq(directory, family, kind, None if mutation == "profile_boundary" else mutation)
    if mutation != "profile_boundary":
        return fixture
    # Same legitimate FP1 recipe boundary as received R1 XT-S01 regression;
    # evaluate an updated original Result instead of falsifying old bytes.
    sys.path.insert(0, str(Path(r0) / "sources/repo/kernel"))
    from genius_kernel.engine import evaluate
    from genius_local.operations import fdq_scope, fdq_target_spec
    base = json.loads((fixture.directory / "input.json").read_bytes())
    base["generative"]["recipe"] = {"kind": "hold", "length": "0"}
    raw = canonical(base)
    result_raw = canonical(evaluate(raw))
    certificate = json.loads((fixture.directory / "certificate.json").read_bytes())
    certificate["input_sha256"] = sha(raw)
    certificate["original_result_sha256"] = sha(result_raw)
    changed = {"input": raw, "result": result_raw, "certificate": canonical(certificate)}
    for meta in fixture.request["artifacts"]:
        content = changed[meta["id"]]
        (fixture.directory / meta["path"]).write_bytes(content)
        meta["sha256"] = sha(content)
    fixture.request["queries"][0]["scope"] = fdq_scope(raw, result_raw, certificate)
    fixture.request["queries"][0]["target_spec"] = fdq_target_spec(raw, kind)
    return fixture


def generate(destination, r0, r1):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    rows = []
    for name, family, kind, mutation, expected in SCENARIOS:
        fixture = scenario_fixture(destination / name / "input", family, kind, mutation, r0)
        case = destination / name / "case"
        response = execute(fixture.save(), case, r0, r1)
        receipt = render_case(case, destination / name / "views")
        rows.append({"name": name, "origin": "NEW_R2_EXECUTION_OF_SYNTHETIC_CONFORMANCE_FIXTURE",
                     "expected_decision_state": expected, "actual_decision_state": response["decisions"][0]["state"],
                     "receipt": receipt})
    fixture = make_hours(destination / "hours_unknown" / "input", credits=("13/2", unknown()))
    response = execute(fixture.save(), destination / "hours_unknown" / "case", r0, r1)
    rows.append({"name": "hours_unknown", "origin": "NEW_R2_EXECUTION_OF_SYNTHETIC_CONFORMANCE_FIXTURE",
                 "expected_decision_state": "PR_DEPENDENCY", "actual_decision_state": response["decisions"][0]["state"],
                 "receipt": render_case(destination / "hours_unknown" / "case", destination / "hours_unknown" / "views")})
    (destination / "RESULTS.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
    if any(row["expected_decision_state"] != row["actual_decision_state"] for row in rows):
        raise AssertionError("EXAMPLE_EXPECTATION_MISMATCH; original results retained")
    return rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--r0", required=True, type=Path)
    parser.add_argument("--r1", required=True, type=Path)
    args = parser.parse_args()
    generate(args.output, args.r0, args.r1)
