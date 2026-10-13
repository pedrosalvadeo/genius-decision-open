"""Build explicitly synthetic CLI test inputs from received R1 bytes.

Copy/materialize/mutate contract-declared tables without invoking R2 production
or deriving expected answers from the implementation under test. The optional
infeasible fixture uses the received Kernel solely to create its Result input.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys


def encode(obj):
    return (json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def materialize(base, certificate, choice):
    member = deepcopy(base)
    hole = certificate["domain"]["hole"]
    member["functional"]["measurements"].append({**hole, "raw": choice["raw"]})
    index = next(row for row in member["functional"]["indices"] if row["id"] == hole["index"])
    if not any(row["raw"] == choice["raw"] for row in index["calibration"]):
        index["calibration"].append(dict(choice))
    # R1 canonical materialization sorts raw strings lexicographically.
    index["calibration"].sort(key=lambda row: row["raw"])
    return member


def build(received_r1, destination):
    received = Path(received_r1)
    dest = Path(destination)
    dest.mkdir(parents=True, exist_ok=True)
    provenance = []
    for name, received_name in (("historical", "historical_gamma101"),
                                ("welfare", "synthetic_welfare_gamma101"),
                                ("priority", "priority_two_maxima"),
                                ("none", "none_two_maxima"),
                                ("unique", "unique_two_maxima")):
        source = received / "research" / "results" / received_name
        target = dest / name
        target.mkdir(exist_ok=True)
        for member_name in ("input.json", "original_result.json"):
            raw = (source / member_name).read_bytes()
            (target / member_name).write_bytes(raw)
            provenance.append({"path": str((target / member_name).relative_to(dest)),
                               "source": f"R1/research/results/{received_name}/{member_name}",
                               "sha256": hashlib.sha256(raw).hexdigest(), "transformation": "EXACT_COPY"})
        cert = json.loads((source / "certificate.json").read_bytes())
        cert["domain"]["choices"] = [cert["domain"]["choices"][0], cert["domain"]["choices"][-1]]
        (target / "certificate.json").write_bytes(encode(cert))
        provenance.append({"path": f"{name}/certificate.json",
                           "source": f"R1/research/results/{received_name}/certificate.json",
                           "transformation": "Input-defined nonempty family restricted to first and last member; claim retained as fixed expectation.",
                           "synthetic": True})
        base = json.loads((source / "input.json").read_bytes())
        members = [materialize(base, cert, choice) for choice in cert["domain"]["choices"]]
        (target / "members.json").write_bytes(encode(members))
    historical = json.loads((dest / "historical/certificate.json").read_bytes())
    priority = json.loads((dest / "priority/certificate.json").read_bytes())
    mutations = []
    def certificate(case, parent, edit, reason):
        obj = deepcopy(parent)
        edit(obj)
        (dest / (case + ".json")).write_bytes(encode(obj))
        mutations.append({"id": case, "kind": "certificate", "base": "priority" if parent is priority else "historical",
                          "expected_state": "NOT_ACCEPTED", "reason": reason})
    certificate("empty_family", historical, lambda x: x["domain"].update(choices=[]), "NONEMPTY_BOUNDED_FAMILY")
    certificate("omitted_feasible_policy", priority, lambda x: x.update(covered_policies=["p"]), "POTENTIALLY_FEASIBLE_OMITTED")
    certificate("false_claim", historical, lambda x: x["claim"].update(selector={"state":"DEFINED","value":"q"}), "FALSE_CERTIFICATE_CLAIM")
    certificate("missing_hole_index", historical, lambda x: x["domain"]["hole"].update(index="ghost"), "INVALID_HOLE_INDEX_REFERENCE")
    certificate("missing_constraint", historical, lambda x: x["witness"].update(constraint="ghost"), "INVALID_WITNESS_CONSTRAINT_REFERENCE")
    certificate("order_breaking_calibration", historical, lambda x: x["domain"]["choices"][-1].update(value="-1/1"), "COMPLETION_FP1_GUARD_FAILURE")
    def member(case, family, edit):
        obj = json.loads((dest / family / "members.json").read_bytes())
        edit(obj[-1])
        (dest / (case + ".json")).write_bytes(encode(obj))
        mutations.append({"id": case, "kind": "members", "base": family,
                          "expected_state": "NOT_ACCEPTED", "reason": "FROZEN_OR_PATCH_MISMATCH"})
    member("shared_calibration_changed", "historical", lambda x: x["functional"]["indices"][0]["calibration"][0].update(value="9/1"))
    member("translation_changed", "historical", lambda x: x["generative"]["translation"][0].update(common="o"))
    member("welfare_support_changed", "welfare", lambda x: x["welfare"]["applicability"].pop())
    member("interface_changed", "historical", lambda x: x["composition"]["views"][0].update(columns=[]))
    member("joint_law_changed", "historical", lambda x: x["law"]["rows"][0]["weights"][0].update(mass="0/1"))
    member("same_frontier_different_selector", "priority", lambda x: x["selection"].update(order=["s", "p", "q"]))
    (dest / "PROVENANCE.json").write_bytes(encode({"evidence_kind":"SYNTHETIC_STIPULATION", "source_copies":provenance,
        "expected_basis":"Received DS contract; fixed expectations independent of R2 production. No claim of empirical domain membership.",
        "attacks": mutations}))


def build_infeasible(received_r0, destination):
    """Create a synthetic budget input; fixed expectation from 1 > 0 and 2 > 0.

    The received Kernel creates the original Result artifact required by FDQ.
    It is not used to decide the expected frontier/selector or test verdict.
    """
    dest = Path(destination)
    base = json.loads((dest / "priority/input.json").read_bytes())
    next(row for row in base["constraints"] if row["id"] == "Budget_R")["bound"] = "0/1"
    for row in base["resources"]["values"]:
        if row["query"]["policy"] in {"p","s"}:
            row["value"] = "1/1"
    cert = json.loads((dest / "priority/certificate.json").read_bytes())
    raw = encode(base)
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(Path(received_r0).resolve() / "sources/repo/kernel"))
    from genius_kernel.engine import evaluate
    result_raw = encode(evaluate(raw))
    cert["input_sha256"] = hashlib.sha256(raw).hexdigest()
    cert["original_result_sha256"] = hashlib.sha256(result_raw).hexdigest()
    cert["claim"] = {"frontier":[], "selector":{"state":"OUTSIDE_DOMAIN", "cause":"SELECTION_EMPTY"}}
    folder = dest / "infeasible"
    folder.mkdir(exist_ok=True)
    (folder / "input.json").write_bytes(raw)
    (folder / "original_result.json").write_bytes(result_raw)
    (folder / "certificate.json").write_bytes(encode(cert))
    (folder / "EXPECTED_PROOF.json").write_bytes(encode({"evidence_kind":"SYNTHETIC_STIPULATION", "expected":"ALL_POLICIES_REFUTED",
        "argument":"Policies p and s use 1/1 resource, q uses 2/1. Each exceeds stipulated bound 0/1, independently of functional hole choices 0/1 and 100/1. Full target is p,q,s; no policy omitted.",
        "limit":"Formal refutation inside an artificial exact input; no physical infeasibility or domain admission.",
        "generation":"Received Kernel 1.0.1 generates original Result as required input artifact only; expected proof and claim are hand-fixed."}))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
    if len(sys.argv) > 3:
        build_infeasible(sys.argv[3],sys.argv[2])
