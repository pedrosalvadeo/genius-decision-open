"""Independent consumer checks for R2 public artifacts.

This module imports no genius_local/Kernel/verifier implementation. Its checks
are derived from received RC01–RC07 and the declared local journal wire format.
It is a finite adversarial consumer, not a complete grammar or truth validator.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from fractions import Fraction


class ConsumerRejected(ValueError):
    pass


def insist(condition, message):
    if not condition:
        raise ConsumerRejected(message)


def read_json(raw):
    def unique(pairs):
        answer = {}
        for key, value in pairs:
            insist(key not in answer, "duplicate JSON key")
            answer[key] = value
        return answer
    return json.loads(raw, object_pairs_hook=unique)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def audit_chain(case_directory):
    """Follow HEAD and verify every stored immutable revision/object by bytes."""
    root = Path(case_directory)
    revisions = {}
    objects = {}
    for directory, target in (("objects", objects), ("revisions", revisions)):
        for file in (root / directory).iterdir():
            insist(not file.is_symlink() and file.is_file(), "unsafe stored entry")
            insist(re.fullmatch(r"[a-f0-9]{64}", file.name), "non-digest stored name")
            raw = file.read_bytes()
            insist(digest(raw) == file.name, "stored bytes differ from digest")
            target[file.name] = raw
    chain = []
    head_file = root / "HEAD"
    head = read_json(head_file.read_bytes())["sha256"] if head_file.exists() else None
    seen = set()
    while head is not None:
        insist(head not in seen and head in revisions, "missing or cyclic revision")
        seen.add(head)
        item = read_json(revisions[head])
        insist(item["format"] == "genius-local-revision/0.1.0", "unknown journal version")
        insist(type(item["revision"]) is int, "revision must be integer")
        insist(item["objects"] == sorted(set(item["objects"])), "object manifest malformed")
        for reference in item["objects"]:
            insist(reference in objects, "missing historical artifact")
        chain.append({**item, "sha256": head})
        head = item["parent"]
    chain.reverse()
    insist([entry["revision"] for entry in chain] == list(range(1, len(chain) + 1)),
           "non-contiguous history")
    snapshots = []
    def materialize(reference):
        raw = b""
        for chunk in reference["chunks"]:
            insist(chunk["sha256"] in objects, "missing serialized chunk")
            part = objects[chunk["sha256"]]
            insist(len(part) == chunk["size"], "chunk length changed")
            raw += part
        insist(len(raw) == reference["size"] and digest(raw) == reference["sha256"], "reassembled artifact identity mismatch")
        return read_json(raw)
    for entry in chain:
        snapshot = dict(entry["payload"])
        if snapshot.get("storage_format") == "genius-local-snapshot-refs/0.1.0":
            snapshot["ledger"] = materialize(snapshot["ledger_ref"])
            snapshot["outcomes"] = [materialize(ref) for ref in snapshot["outcome_refs"]]
            if "response_ref" in snapshot:
                snapshot["response"] = materialize(snapshot["response_ref"])
        snapshots.append(snapshot)
    return {"chain": chain, "objects": objects, "snapshots":snapshots,
            "uncommitted_revisions": sorted(set(revisions) - seen)}


def audit_product_cells(value):
    if isinstance(value, list):
        for child in value:
            audit_product_cells(child)
    elif isinstance(value, dict):
        state = value.get("state")
        if state in {"PV_UNKNOWN", "PV_NOT_APPLICABLE", "PV_OUTSIDE_PROFILE"}:
            insist("value" not in value, "absence variant carries fabricated value")
            insist(value.get("reasons"), "absence variant needs reasons")
        if state == "PV_KNOWN":
            insist("value" in value and value["value"] is not None,
                   "known variant lacks value")
            scalar = value["value"]
            insist(type(scalar) not in (int, float), "mathematical number is not an exact string")
            if isinstance(scalar, str) and re.fullmatch(r"-?\d+/\d+", scalar):
                try:
                    rational = Fraction(scalar)
                except ZeroDivisionError as exc:
                    raise ConsumerRejected("zero rational denominator") from exc
                insist(scalar == f"{rational.numerator}/{rational.denominator}", "noncanonical rational")
        for child in value.values():
            audit_product_cells(child)


def audit_response(response, case_directory=None):
    required = {"format", "response_id", "revision", "request_ref", "supersedes",
                "versions", "queries", "artifacts", "transport", "execution",
                "evidence", "decisions", "obligations_ref", "quality", "closure",
                "permitted_use"}
    insist(required <= response.keys(), "missing RC01 response fields")
    insist(response["format"] == "genius-product-response/0.1.0", "unknown response version")
    expected_versions = {
        "obligations":"genius-product-obligations/0.1.0",
        "source_compatibility":"genius-source-compatibility/0.1.0",
        "response":"genius-product-response/0.1.0",
        "sufficiency":"DECISION_SUFFICIENCY/0.1.0",
        "sufficiency_profile":"FDQ_FINITE_PATCH/0.1.0",
    }
    insist(all(response["versions"].get(key) == version for key,version in expected_versions.items()),
           "unsupported or absent contract version")
    insist(response["transport"]["state"] in {"PT_DELIVERED", "PT_FAILED", "PT_NOT_ATTEMPTED"},
           "unknown transport state")
    insist(response["execution"]["state"] in {
        "PE_COMPLETE", "PE_PARTIAL", "PE_NOT_STARTED", "PE_BUDGET_EXHAUSTED",
        "PE_ERROR", "PE_CANCELLED", "PE_UNKNOWN"}, "unknown execution state")
    allowed_decisions = {"PR_JUSTIFIED_RESULT", "PR_SET_OR_INCOMPARABLE", "PR_PROVEN_INFEASIBLE",
                         "PR_PARTIAL", "PR_DEPENDENCY", "PR_OUTSIDE_PROFILE", "PR_NOT_EVALUATED"}
    query_ids = {query["id"] for query in response["queries"]}
    query_digests = {query["id"]:digest(json.dumps(query,ensure_ascii=False,sort_keys=True,separators=(",", ":")).encode())
                     for query in response["queries"]}
    seen = set()
    for decision in response["decisions"]:
        insist(decision["state"] in allowed_decisions, "unknown decision state")
        reference = decision.get("query_ref", decision.get("query_id"))
        insist(reference and reference not in seen, "duplicate or absent decision query")
        insist(reference in query_ids, "decision bound to nonexistent query")
        insist(decision.get("query_sha256") == query_digests[reference], "decision changed exact query")
        seen.add(reference)
        if decision["state"] == "PR_PROVEN_INFEASIBLE":
            insist(decision.get("coverage") == "EXHAUSTIVE", "infeasibility needs complete coverage")
            insist(decision.get("witnesses"), "infeasibility needs refutation witnesses")
        # Global execution may be UNKNOWN after another query was interrupted.
        # Completed scoped receipts retain meaning; do not erase them by a
        # blanket rule based on the aggregate execution state (RC02).
    quality = response["quality"]
    insist(not any(name in quality for name in ("score", "confidence", "overall_score", "percentage")),
           "fabricated global quality score")
    for dimension in ("utility", "comprehension", "adoption_business", "model_fidelity"):
        insist(quality.get(dimension, {}).get("state") == "NOT_ASSESSED",
               "synthetic local tests overclaim empirical quality")
    audit_product_cells(response)
    if case_directory is not None:
        historical = audit_chain(case_directory)
        insist(response["request_ref"]["sha256"] in historical["objects"], "original request bytes absent")
        received_ids = {}
        for received in response["artifacts"]["received"]:
            sha = received.get("sha256", received.get("digest"))
            insist(sha in historical["objects"], "response artifact is not received in journal")
            received_ids[received["id"]] = sha
        for expected in response["artifacts"]["expected"]:
            if expected["state"] == "RECEIVED":
                ref = expected.get("ref",expected.get("id"))
                insist(ref in received_ids and expected.get("sha256") == received_ids[ref], "expected artifact falsely claims received")
    return True
