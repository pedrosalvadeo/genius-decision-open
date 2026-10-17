"""Bounded public inputs compiled to the unchanged, received R2 controller.

No natural-language solver, empirical admission, or replacement arithmetic.
FDQ source JSON is retained byte for byte because certificates bind its hash.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "product_local"))
sys.path.insert(0, str(ROOT / "consumer_views"))
from genius_local import controller, operations, policy  # noqa: E402
from genius_views.reader import read_case  # noqa: E402
from genius_views.views import presentation  # noqa: E402

VERSION = "genius-beta-adapter/0.1.0"
MAX_ARTIFACT_BYTES = 512 * 1024
MAX_FDQ_CHOICES = 100
MAX_HOURS_ASSIGNMENTS = 100
ACK_FIELDS = {"permission_confirmed", "scope_acknowledged"}


class AdmissionError(ValueError):
    """Public input cannot be compiled into the supported profile."""


def fdq_verifier_available():
    """The received R1 FDQ verifier ships only in beta/vendor, which the public edition omits."""
    research = ROOT / "beta/vendor/R1/research"
    return (research / "verify_fdq.py").is_file() and (research / "fdq_oracle.py").is_file()


def _require(condition, reason):
    if not condition:
        raise AdmissionError(reason)


def _canonical(value):
    return policy.canonical_bytes(value)


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _admit(payload, profile, fields):
    _require(type(payload) is dict, "PAYLOAD_MUST_BE_OBJECT")
    _require(set(payload) - {"evidence_origin"} == {"profile", *ACK_FIELDS, *fields}, "PROFILE_FIELDS")
    _require(payload.get("evidence_origin", "user_declared") in ("user_declared", "synthetic"), "EVIDENCE_ORIGIN")
    _require(payload["profile"] == profile, "PROFILE_MISMATCH")
    _require(payload["permission_confirmed"] is True, "PROCESSING_PERMISSION_REQUIRED")
    _require(payload["scope_acknowledged"] is True, "FORMAL_SCOPE_ACKNOWLEDGEMENT_REQUIRED")


def _permissions():
    return {"access": "ALLOWED", "use": "ALLOWED",
            "basis": "Submitting consumer explicitly declares authority to process these supplied bytes; declaration is not independently authenticated. Processing only; no research permission inferred."}


def _obligation(spec, cause):
    return {"id": "O", "revision": 1, "query_ref": "Q", "affected_claims": ["Q"],
            "primary_cause": cause, "secondary_causes": [],
            "classification_basis": [{"evidence": "Consumer-supplied formal request", "mechanism": cause}],
            "provenance": [{"kind": "SYNTHETIC_STIPULATION", "reason": "User declaration is treated as formal premises, not authenticated empirical observation."}],
            "input_spec": {"object": spec["identity"], "field": "scoped formal answer", "type": "formal component or policy answer",
                           "unit": spec["unit"], "period": spec["period"], "population": spec["population"],
                           "method": spec["method"], "state": "UNKNOWN", "reason": "Await scoped execution; missing supplied values remain unknown."},
            "derivation_rule": {"kind": "NO_DERIVATION", "reason": "Only the explicitly bound received operation can produce a witness."},
            "dependencies": [], "owner": {"role": "submitting-consumer", "task": "Supply compatible formal premises and resolve unknown inputs", "assigned_person": "UNKNOWN"},
            "permitted_use": ["Conditional formal answer to the supplied query"],
            "prohibited_inferences": ["Physical domain admission", "Human comprehension", "Decision utility", "Authority to act", "Empirical CAG or PVS"],
            "status": "OPEN", "closure": {"predicate": "EXACT_QUERY_RESULT_RECEIVED", "witness_refs": [], "verifier": "received R2 controller", "verified": False},
            "reopen": {"condition": "Pertinent change of source, query, rule or scope under a future explicit revision", "affected_refs": ["Q"]},
            "next_action": "Run the bounded operation or retain an explicit dependency", "budget_ref": "request.budget", "attempts": []}


class _Request:
    def __init__(self, directory, profile):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=False)
        self.request = {"format": "genius-local-request/0.1.0", "request_id": "beta-" + profile,
                        "revision": 1, "supersedes": None, "queries": [], "artifacts": [], "obligations": [],
                        "budget": {"max_operations": 1, "max_certificates": 1 if profile == "fdq" else 0,
                                   "certificate_timeout_seconds": 15},
                        "operations": [], "novelty": {"reason": "New consumer-submitted bounded formal case", "changed_refs": []}}

    def artifact(self, identifier, raw):
        _require(len(raw) <= MAX_ARTIFACT_BYTES, "BETA_ARTIFACT_TOO_LARGE")
        path = self.directory / (identifier + ".json")
        path.write_bytes(raw)
        metadata = {"id": identifier, "role": "consumer-supplied formal premises",
                    "path": path.name, "sha256": _sha(raw), "evidence_kind": "SYNTHETIC_STIPULATION",
                    "permissions": _permissions()}
        self.request["artifacts"].append(metadata)
        return metadata

    def query(self, spec, scope, kind, norm, cause):
        query = {"id": "Q", "revision": 1, "kind": kind, "target_spec": deepcopy(spec), "scope": scope,
                 "norm": norm, "artifact_refs": [a["id"] for a in self.request["artifacts"]], "obligation_refs": ["O"]}
        self.request["queries"].append(query)
        self.request["obligations"].append(_obligation(spec, cause))
        return query

    def save(self, kind, parameters):
        self.request["operations"].append({"id": "OP", "query_ref": "Q", "kind": kind,
                                           "obligation_refs": ["O"], "parameters": parameters})
        path = self.directory / "request.json"
        path.write_bytes(_canonical(self.request))
        return path


def _hours_cell(text):
    if text is None:
        return {"state": "PV_UNKNOWN", "reasons": ["Consumer explicitly left this credit or target unknown"], "obligation_refs": ["O"]}
    _require(type(text) is str and 1 <= len(text) <= 64, "HOURS_REQUIRE_EXACT_TEXT_OR_NULL")
    _require(re.fullmatch(r"(?:0|[1-9][0-9]*)(?:\.[0-9]+|/[1-9][0-9]*)?", text) is not None,
             "HOURS_NONNEGATIVE_DECIMAL_OR_RATIONAL_REQUIRED")
    value = Fraction(text)
    return {"state": "PV_KNOWN", "value": f"{value.numerator}/{value.denominator}", "unit": "h_contractual",
            "basis": ["Consumer-declared contractual credit; interpreted as a formal stipulation, not physical time."]}


def build_hours(payload, directory):
    """Return request.json path; directory must be a new service-owned path."""
    _admit(payload, "hours", {"assignments", "target"})
    rows = payload["assignments"]
    _require(type(rows) is list and 1 <= len(rows) <= MAX_HOURS_ASSIGNMENTS, "HOURS_ASSIGNMENT_COUNT")
    assignments = []
    for row in rows:
        _require(type(row) is dict and set(row) == {"id", "credit"}, "HOURS_ASSIGNMENT_FIELDS")
        _require(type(row["id"]) is str and re.fullmatch(r"[A-Za-z0-9_-]{1,64}", row["id"]), "HOURS_ASSIGNMENT_ID")
        assignments.append({"id": row["id"], "credit_hours": _hours_cell(row["credit"])})
    _require(len({row["id"] for row in assignments}) == len(assignments), "DUPLICATE_ASSIGNMENT_ID")
    source = {"assignments": assignments, "target_hours": _hours_cell(payload["target"])}
    spec = {"identity": "consumer-declared-credit-register", "unit": "h_contractual", "period": "declared-plan-scope",
            "population": "DECLARED_ASSIGNMENTS:" + json.dumps(sorted(row["id"] for row in assignments), separators=(",", ":")),
            "method": "CONTRACT_HOURS/1"}
    request = _Request(directory, "hours")
    meta = request.artifact("hours", _canonical(source))
    request.artifact("metadata", _canonical(spec))
    query = request.query(spec, {"operator": "CONTRACT_HOURS/1", "purpose": "FORMAL_CONDITIONAL"}, "component",
                          {"state": "PV_NOT_APPLICABLE", "reasons": ["No policy selection requested"], "scope": "contractual-credit arithmetic"}, "DERIVABLE")
    assessment = {"assessment_id": "A", "revision": 1, "query_ref": "Q", "claim": "Q",
                  "intended_use": "Conditional formal arithmetic only", "target_spec": deepcopy(spec),
                  "source_ref": "hours", "source_locator": "hours.json", "source_version": VERSION,
                  "source_digest": meta["sha256"], "observed_or_received_at": datetime.now(timezone.utc).isoformat(),
                  "relevant_period": spec["period"], "access_and_permissions": _permissions(),
                  "evidence_kind": "SYNTHETIC_STIPULATION", "transformation_chain": [],
                  "axes": {axis: {"status": "MATCH", "source_value": spec[axis], "target_value": spec[axis],
                                  "basis": {"artifact_ref": "metadata", "pointer": "/" + axis}, "affected_claims": ["Q"]} for axis in spec},
                  "conflicts": [], "verdict": "PENDING", "owner": {"role": "submitting-consumer", "task": "Supply formal premises", "assigned_person": "UNKNOWN"},
                  "closure": {"verified": False, "predicate": "Five axes and permission declaration are compatible in stated formal scope", "witness_refs": [], "verifier": "received R2 controller"},
                  "reopen": {"condition": "Source or query changes", "affected_refs": [query["id"]]}}
    return request.save("DERIVE_HOURS", {"artifact_ref": "hours", "rule_id": "CONTRACT_HOURS/1", "assessment": assessment})


def build_fdq(payload, directory):
    """Retain original UTF-8 bytes and invoke the received certificate profile."""
    _admit(payload, "fdq", {"input_json", "result_json", "certificate_json", "query_kind"})
    kind = payload["query_kind"]
    _require(kind in ("frontier", "selector"), "FDQ_QUERY_KIND")
    raw = {}
    parsed = {}
    for key in ("input", "result", "certificate"):
        value = payload[key + "_json"]
        _require(type(value) is str, "FDQ_REQUIRES_ORIGINAL_JSON_TEXT")
        raw[key] = value.encode("utf-8")
        _require(len(raw[key]) <= MAX_ARTIFACT_BYTES, "BETA_ARTIFACT_TOO_LARGE")
        try:
            parsed[key] = policy.loads_strict(raw[key])
        except (ValueError, TypeError, RecursionError) as exc:
            raise AdmissionError("FDQ_INVALID_STRICT_JSON") from exc
        _require(type(parsed[key]) is dict, "FDQ_ARTIFACT_MUST_BE_OBJECT")
    cert = parsed["certificate"]
    _require(cert.get("query") == {"frontier": kind == "frontier", "selector": kind == "selector"}, "FDQ_CERTIFICATE_QUERY_MUST_MATCH_EXACTLY")
    _require(type(cert.get("claim")) is dict and set(cert["claim"]) == {kind}, "FDQ_CERTIFICATE_CLAIM_MUST_MATCH_EXACTLY")
    _require(cert.get("input_sha256") == _sha(raw["input"]) and cert.get("original_result_sha256") == _sha(raw["result"]), "FDQ_ORIGINAL_BYTE_DIGEST_MISMATCH")
    domain = cert.get("domain")
    _require(type(domain) is dict and type(domain.get("choices")) is list and 1 <= len(domain["choices"]) <= MAX_FDQ_CHOICES, "BETA_FDQ_FAMILY_LIMIT")
    try:
        spec = operations.fdq_target_spec(raw["input"], kind)
        scope = operations.fdq_scope(raw["input"], raw["result"], cert)
        norm = deepcopy(parsed["input"]["selection"])
    except (KeyError, TypeError, ValueError) as exc:
        raise AdmissionError("FDQ_INPUT_OUTSIDE_STRUCTURAL_PROFILE") from exc
    _require(scope["horizon"] == "1", "FDQ_ONLY_HORIZON_ONE")
    request = _Request(directory, "fdq")
    for key in ("input", "result", "certificate"):
        request.artifact(key, raw[key])
    request.query(spec, scope, kind, norm, "COMPUTO_PENDIENTE")
    return request.save("CERTIFY_FDQ", {"input_ref": "input", "result_ref": "result", "certificate_ref": "certificate"})


def execute_profile(payload, case_dir):
    """Execute one new dossier; caller owns identity, quota and persistence.

    The raw received response is never rewritten into a favorable status.
    Existing directories are refused; idempotence belongs to the service layer.
    """
    _require(type(payload) is dict, "PAYLOAD_MUST_BE_OBJECT")
    if payload.get('profile') == 'choice':
        from .choice import ChoiceError, execute
        try:
            return execute(payload, case_dir)
        except ChoiceError as exc:
            raise AdmissionError('CHOICE_PROFILE_REJECTED') from exc
    builder = {"hours": build_hours, "fdq": build_fdq}.get(payload.get("profile"))
    _require(builder is not None, "PROFILE_OUTSIDE_BETA")
    _require(payload["profile"] != "fdq" or fdq_verifier_available(), "FDQ_VERIFIER_NOT_IN_PUBLIC_EDITION")
    case_dir = Path(case_dir)
    _require(not case_dir.exists(), "NEW_DOSSIER_PATH_REQUIRED")
    case_dir.mkdir(parents=True, exist_ok=False)
    submitted = _canonical(payload)
    (case_dir / "submitted.json").write_bytes(submitted)
    request_path = builder(payload, case_dir / "input")
    compiled_request = policy.loads_strict(request_path.read_bytes())
    compilation = {"format": "genius-beta-compilation/0.1.0", "adapter_version": VERSION,
                   "submitted_sha256": _sha(submitted), "request_sha256": _sha(request_path.read_bytes()),
                   "artifact_sha256": {entry["id"]: entry["sha256"] for entry in compiled_request["artifacts"]},
                   "transformation": "EXACT_DECIMAL_OR_RATIONAL_TEXT_TO_REDUCED_RATIONAL_NULL_TO_PV_UNKNOWN" if payload["profile"] == "hours" else "PRESERVE_ORIGINAL_UTF8_BYTES_NO_CERTIFICATE_MUTATION",
                   "unit_conversion": "NONE", "scope": "Formal syntactic compilation, not source authentication or empirical model admission"}
    (case_dir / "compilation.json").write_bytes(_canonical(compilation))
    response = controller.execute(request_path, case_dir / "store",
                                  baseline_r0=ROOT / "beta/vendor/R0", baseline_r1=ROOT / "beta/vendor/R1")
    bundle = read_case(case_dir / "store")
    _require(bundle["response"] == response, "R3_RESPONSE_BINDING_FAILED")
    raw = request_path.read_bytes()
    return {"adapter_version": VERSION, "evidence_origin": payload.get("evidence_origin", "user_declared"),
            "request": policy.loads_strict(raw), "request_sha256": _sha(raw), "response": response,
            "presentation": presentation(bundle), "source_receipt": {
                "head": bundle["source"]["head"], "selected_revision": bundle["source"]["selected_revision"],
                "selected_revision_sha256": bundle["source"]["selected_revision_sha256"],
                "verification": bundle["source"]["verification"],
                "limits": bundle["source"]["limits"]}}
