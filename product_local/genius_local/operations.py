"""Bounded local operations. Evidence is tied to the full versioned query.

The received Kernel and FDQ verifier are external read-only dependencies. No
operation authenticates a physical fact, acts on people, or edits FP1 artifacts.
"""
from __future__ import annotations
import base64
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import os

from .fdq_worker import strict_json

HOURS_RULE = "CONTRACT_HOURS/1"
HOURS_UNIT = "h_contractual"
HOURS_FIELDS = ["assigned", "excess", "deficit", "oriented_overtime", "oriented_undertime"]
DIAGNOSIS_SHA256 = "9ede5e7e064b1784faa52270e17402c57cf91ac545e97638245076cbbe39d72d"


class OperationRejected(ValueError):
    pass


class OperationOutsideProfile(ValueError):
    pass


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def query_digest(query):
    return digest(canonical(query))


def require(condition, reason):
    if not condition:
        raise OperationRejected(reason)


def exact_rational(value):
    require(type(value) is str and re.fullmatch(r"-?(0|[1-9][0-9]*)/[1-9][0-9]*", value), "NONCANONICAL_RATIONAL")
    number = Fraction(value)
    require(str(number.numerator) + "/" + str(number.denominator) == value, "NONCANONICAL_RATIONAL")
    return number


def qstring(value):
    return str(value.numerator) + "/" + str(value.denominator)


def json_pointer(value, pointer):
    require(type(pointer) is str and (pointer == "" or pointer.startswith("/")), "INVALID_JSON_POINTER")
    if pointer == "":
        return value
    for raw_token in pointer[1:].split("/"):
        require(re.search(r"~(?![01])", raw_token) is None, "INVALID_JSON_POINTER_ESCAPE")
        token = raw_token.replace("~1", "/").replace("~0", "~")
        if type(value) is list:
            require(re.fullmatch(r"0|[1-9][0-9]*", token) is not None, "INVALID_ARRAY_INDEX")
            require(int(token) < len(value), "POINTER_NOT_FOUND")
            value = value[int(token)]
        elif type(value) is dict:
            require(token in value, "POINTER_NOT_FOUND")
            value = value[token]
        else:
            raise OperationRejected("POINTER_NOT_FOUND")
    return value


def hours_scope():
    return {"operator": HOURS_RULE, "purpose": "FORMAL_CONDITIONAL"}


def derive_hours(data):
    """Exact credit arithmetic; missing credit/target propagates as unknown.

    Rows are assignments, not distinct people or observed physical durations.
    Their identities prevent duplicate counting. Unknowns retain obligations.
    """
    require(type(data) is dict and set(data) == {"assignments", "target_hours"}, "HOURS_INPUT_FIELDS")
    rows = data["assignments"]
    require(type(rows) is list, "HOURS_ASSIGNMENT_LIST")
    ids = set()
    unknown_reasons, unknown_obligations = set(), set()
    def cell(value):
        require(type(value) is dict, "HOURS_CELL_REQUIRED")
        if value.get("state") == "PV_UNKNOWN":
            require(set(value) == {"state", "reasons", "obligation_refs"}, "UNKNOWN_CELL_FIELDS")
            for field in ("reasons", "obligation_refs"):
                require(type(value[field]) is list and bool(value[field]) and
                        all(type(x) is str and bool(x) for x in value[field]), "UNKNOWN_CELL_EVIDENCE")
            unknown_reasons.update(value["reasons"])
            unknown_obligations.update(value["obligation_refs"])
            return None
        require(set(value) == {"state", "value", "unit", "basis"} and value["state"] == "PV_KNOWN", "HOURS_CELL_FIELDS")
        require(value["unit"] == HOURS_UNIT, "HOURS_UNIT_MISMATCH")
        require(type(value["basis"]) is list and bool(value["basis"]), "HOURS_BASIS_REQUIRED")
        result = exact_rational(value["value"])
        require(result >= 0, "NEGATIVE_CONTRACTUAL_HOURS")
        return result
    credits = []
    for row in rows:
        require(type(row) is dict and set(row) == {"id", "credit_hours"}, "ASSIGNMENT_FIELDS")
        require(type(row["id"]) is str and bool(row["id"]) and row["id"] not in ids, "DUPLICATE_ASSIGNMENT")
        ids.add(row["id"])
        credits.append(cell(row["credit_hours"]))
    credits_known = all(v is not None for v in credits)
    assigned = sum(credits, Fraction(0)) if credits_known else None
    target = cell(data["target_hours"])
    if unknown_reasons:
        result = {field: {"state": "PV_UNKNOWN", "reasons": sorted(unknown_reasons),
                          "obligation_refs": sorted(unknown_obligations)} for field in HOURS_FIELDS}
        if credits_known:
            result["assigned"] = {"state": "PV_KNOWN", "value": qstring(assigned),
                                  "unit": HOURS_UNIT, "basis": [HOURS_RULE]}
        return result
    delta = assigned - target
    raw = {"assigned": assigned, "excess": max(delta, Fraction(0)),
           "deficit": max(-delta, Fraction(0)), "oriented_overtime": -max(delta, Fraction(0)),
           "oriented_undertime": -max(-delta, Fraction(0))}
    return {field: {"state": "PV_KNOWN", "value": qstring(value), "unit": HOURS_UNIT,
                    "basis": [HOURS_RULE]} for field, value in raw.items()}


def fdq_target_spec(input_raw, kind):
    require(kind in ("frontier", "selector"), "FDQ_QUERY_KIND")
    base = strict_json(input_raw)
    policies = sorted(p["id"] for p in base["policies"])
    return {"identity": "FP1_INPUT_SHA256:" + digest(input_raw),
            "unit": "policy_id_set" if kind == "frontier" else "policy_id",
            "period": "H=" + base["meta"]["horizon"],
            "population": "DECLARED_PI:" + canonical(policies).decode("utf-8"),
            "method": "FDQ_FINITE_PATCH/0.1.0"}


def fdq_scope(input_raw, result_raw, certificate):
    base = strict_json(input_raw)
    return {"profile": "FDQ_FINITE_PATCH/0.1.0", "input_sha256": digest(input_raw),
            "original_result_sha256": digest(result_raw),
            "domain_sha256": digest(canonical(certificate["domain"])),
            "target": sorted(p["id"] for p in base["policies"]),
            "horizon": base["meta"]["horizon"],
            "scenarios": sorted(s["id"] for s in base["scenarios"]),
            "query_flags": certificate["query"], "real_domain_membership": "NOT_ESTABLISHED"}


MAX_WORKER_OUTPUT = 2 * 1024 * 1024


def run_fdq(input_raw, result_raw, certificate_raw, r1, baseline,
            timeout_seconds=60, cancel_check=None):
    """Bounded process receipt; timeout/cancel/output bound never proves failure.

    Output is capped at 2 MiB total to keep its raw-byte receipt plus parsed
    verification under the 8 MiB journal artifact limit. Oversized output is
    explicitly incomplete and is never parsed or treated as a verified result.
    """
    require(type(timeout_seconds) in (int, float) and 0 < timeout_seconds <= 60, "FDQ_TIMEOUT_BOUND")
    payload = {k: base64.b64encode(raw).decode("ascii") for k, raw in
               (("input_b64", input_raw), ("result_b64", result_raw), ("certificate_b64", certificate_raw))}
    command = [sys.executable, "-I", "-B", str(Path(__file__).with_name("fdq_worker.py")),
               "--r1", str(r1), "--baseline", str(baseline)]
    cancel_check = cancel_check or (lambda: False)
    with tempfile.TemporaryFile() as inp, tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
        inp.write(canonical(payload))
        inp.seek(0)
        started = time.monotonic()
        proc = subprocess.Popen(command, stdin=inp, stdout=out, stderr=err)
        stopped = None
        try:
            while proc.poll() is None:
                if cancel_check():
                    stopped = "FDQ_PROCESS_CANCELLED"
                elif time.monotonic() - started >= timeout_seconds:
                    stopped = "FDQ_PROCESS_TIMEOUT"
                elif os.fstat(out.fileno()).st_size + os.fstat(err.fileno()).st_size > MAX_WORKER_OUTPUT:
                    stopped = "FDQ_OUTPUT_BUDGET"
                if stopped:
                    proc.kill()
                    break
                time.sleep(0.01)
            proc.wait()
        except BaseException:
            proc.kill()
            proc.wait()
            raise
        output_size, error_size = os.fstat(out.fileno()).st_size, os.fstat(err.fileno()).st_size
        if output_size + error_size > MAX_WORKER_OUTPUT:
            stopped = stopped or "FDQ_OUTPUT_BUDGET"
        out.seek(0)
        err.seek(0)
        stdout = out.read(MAX_WORKER_OUTPUT)
        stderr = err.read(MAX_WORKER_OUTPUT - len(stdout))
        truncated = len(stdout) != output_size or len(stderr) != error_size
        receipt = {"exit_code": proc.returncode, "stdout_b64": base64.b64encode(stdout).decode("ascii"),
                   "stderr_b64": base64.b64encode(stderr).decode("ascii"),
                   "timeout": stopped == "FDQ_PROCESS_TIMEOUT", "cancelled": stopped == "FDQ_PROCESS_CANCELLED",
                   "stdout_sha256": digest(stdout), "stderr_sha256": digest(stderr),
                   "stdout_size": output_size, "stderr_size": error_size, "truncated": truncated,
                   "digest_scope": "CAPTURED_PREFIX" if truncated else "COMPLETE_BYTES"}
        if stopped:
            return {"process": receipt, "reason": stopped, "verification": None}
        try:
            output = strict_json(stdout)
        except (ValueError, UnicodeDecodeError):
            return {"process": receipt, "reason": "WORKER_RECEIPT_INVALID", "verification": None}
        if proc.returncode != 0 or type(output) is not dict or output.get("worker_format") != "genius-fdq-worker/0.1.0":
            return {"process": receipt, "reason": "WORKER_ERROR", "verification": None,
                    "worker_error": output}
        return {"process": receipt, "reason": "WORKER_RECEIVED", "verification": output.get("verification"),
                "dependencies": output.get("dependencies")}


def _artifact(context, ref):
    require(ref in context["artifacts"], "ARTIFACT_REFERENCE_UNKNOWN")
    entry = context["artifacts"][ref]
    raw = context["blob_reader"](ref)
    require(type(raw) is bytes and len(raw) <= 8 * 1024 * 1024, "ARTIFACT_BYTES_REQUIRED")
    require(digest(raw) == entry["metadata"]["sha256"], "ARTIFACT_DIGEST_MISMATCH")
    return raw


def _source(parameters, query, context, ref=None):
    from .policy import assess_source
    assessment = parameters["assessment"]
    require(assessment["query_ref"] == query["id"] and assessment["target_spec"] == query["target_spec"], "SOURCE_QUERY_BINDING")
    if ref is not None:
        require(assessment["source_ref"] == ref, "SOURCE_ARTIFACT_BINDING")
    for source_ref in context["artifacts"]:
        _artifact(context, source_ref)
    return assess_source(assessment, context["artifacts"])


def _unknown(reason, operation):
    return {"state": "PV_UNKNOWN", "reasons": [reason],
            "obligation_refs": operation["obligation_refs"]}


def _bind_unknowns(value, query):
    if type(value) is dict:
        if value.get("state") == "PV_UNKNOWN":
            refs = value.get("obligation_refs")
            require(type(refs) is list and bool(refs) and set(refs) <= set(query["obligation_refs"]),
                    "SOURCE_UNKNOWN_OBLIGATION_BINDING")
        for child in value.values():
            _bind_unknowns(child, query)
    elif type(value) is list:
        for child in value:
            _bind_unknowns(child, query)


def _has_product_cell(value):
    """A nested product cell is not a literal fully known document value."""
    if type(value) is dict:
        if type(value.get("state")) is str and value["state"].startswith("PV_"):
            return True
        return any(_has_product_cell(child) for child in value.values())
    if type(value) is list:
        return any(_has_product_cell(child) for child in value)
    return False


def _effects(operation, context, causes, status="CLOSED_SCOPED"):
    effects = []
    obligations = {o["id"]: o for o in context["request"]["obligations"]}
    for ref in operation["obligation_refs"]:
        ob = obligations[ref]
        if (ob["query_ref"] == operation["query_ref"] and ob["primary_cause"] in causes
                and ob.get("affected_claims") == [operation["query_ref"]]
                and ob.get("closure", {}).get("predicate") == "EXACT_QUERY_RESULT_RECEIVED"):
            effects.append({"obligation_ref": ref, "status": status,
                            "reason": "VERIFIED_EXACT_QUERY_SCOPE", "witness_refs": [operation["id"]]})
    return effects


def execute_operation(operation, context):
    """Execute only admitted local operators, never caller-declared conclusions."""
    query = context["query"]
    out = {"operation_id": operation["id"], "query_ref": operation["query_ref"],
           "query_sha256": query_digest(query), "kind": operation["kind"],
           "status": "UNRESOLVED", "reason": "NO_VERIFIED_OPERATION",
           "claim_source": "GENIUS_LOCAL_OPERATION/0.1.0", "value": _unknown("NO_VERIFIED_OPERATION", operation),
           "evidence": [], "obligation_effects": [], "artifact_refs": []}
    try:
        require(operation["query_ref"] == query["id"], "OPERATION_QUERY_BINDING")
        require(set(operation) == {"id", "query_ref", "kind", "obligation_refs", "parameters"}, "OPERATION_FIELDS")
        params, kind = operation["parameters"], operation["kind"]
        require(type(params) is dict, "OPERATION_PARAMETERS")
        if kind in ("REUSE", "DERIVE_HOURS"):
            keys = {"artifact_ref", "assessment", "pointer" if kind == "REUSE" else "rule_id"}
            require(set(params) == keys, "OPERATION_PARAMETER_FIELDS")
            ref = params["artifact_ref"]
            require(query["kind"] == "component" and ref in query["artifact_refs"], "COMPONENT_ARTIFACT_BINDING")
            scope = {"operator": "REUSE/1", "artifact_ref": ref, "pointer": params["pointer"]} if kind == "REUSE" else hours_scope()
            require(query["scope"] == scope, "COMPONENT_QUERY_SCOPE")
            if kind == "DERIVE_HOURS":
                require(params["rule_id"] == HOURS_RULE, "UNSUPPORTED_HOURS_RULE")
                require(query["target_spec"]["unit"] == HOURS_UNIT,
                        "CONTRACTUAL_HOURS_TARGET_UNIT_MISMATCH")
            raw = _artifact(context, ref)
            source = _source(params, query, context, ref)
            out["artifact_refs"] = [ref]
            out["evidence"].append({"source_assessment": source, "query_sha256": out["query_sha256"],
                                    "source_sha256": digest(raw), "source_authenticity": "NOT_AUTHENTICATED"})
            if source.get("profile_limitations"):
                out.update(status="OUTSIDE_PROFILE", reason="SOURCE_PROFILE_LIMITATION",
                           value={"state": "PV_OUTSIDE_PROFILE", "reasons": source["profile_limitations"], "profile_ref": "GENIUS_LOCAL_SOURCE/0.1.0"})
                return out
            if source["verdict"] not in ("SC_COMPATIBLE_SCOPED", "SC_CONDITIONAL_MODEL_ONLY"):
                out.update(reason=source["verdict"], value=_unknown(source["verdict"], operation))
                return out
            from .policy import loads_strict
            source_data = loads_strict(raw)
            if kind == "DERIVE_HOURS":
                require(not source.get("unit_transform"), "CONTRACTUAL_HOURS_BRIDGE_UNSUPPORTED")
                value = derive_hours(source_data)
                _bind_unknowns(value, query)
                unknown = any(v["state"] == "PV_UNKNOWN" for v in value.values())
                out.update(value=value, status="UNRESOLVED" if unknown else "CONDITIONAL",
                           reason="UNKNOWN_HOURS_INPUT" if unknown else "EXACT_CONTRACTUAL_HOURS",
                           claim_source=HOURS_RULE)
                if not unknown:
                    out["obligation_effects"] = _effects(operation, context, {"DERIVABLE", "COMPUTO_PENDIENTE"})
            else:
                value = json_pointer(source_data, params["pointer"])
                require(value is not None, "NULL_IS_NOT_KNOWN_VALUE")
                if type(value) is dict and type(value.get("state")) is str and value["state"].startswith("PV_"):
                    # The strict request validator does not inspect source JSON;
                    # validate each reused cell before assigning product meaning.
                    from .policy import validate_cell
                    validate_cell(value)
                    if _has_product_cell(value.get("value")):
                        raise OperationOutsideProfile("REUSE_NESTED_PRODUCT_STATE_OUTSIDE_PROFILE")
                    if value["state"] == "PV_KNOWN":
                        source_unit = source["axes"]["unit"]["source_value"]
                        source_unit = source_unit["unit"] if type(source_unit) is dict else source_unit
                        require(value["unit"] == source_unit, "SOURCE_VALUE_UNIT_MISMATCH")
                else:
                    if _has_product_cell(value):
                        raise OperationOutsideProfile("REUSE_NESTED_PRODUCT_STATE_OUTSIDE_PROFILE")
                    unit = query["target_spec"]["unit"]
                    unit = unit["unit"] if type(unit) is dict else unit
                    if source.get("unit_transform"):
                        unit = source["unit_transform"]["source_unit"]
                    value = {"state": "PV_KNOWN", "value": value,
                             "unit": unit, "basis": [ref, digest(raw), params["pointer"]]}
                transform = source.get("unit_transform")
                if transform and value["state"] == "PV_KNOWN":
                    require(value["unit"] in (transform["source_unit"], {"construct": transform["construct"], "unit": transform["source_unit"]}), "TRANSFORM_SOURCE_UNIT")
                    value = {**value, "value": qstring(exact_rational(value["value"]) * exact_rational(transform["factor"])),
                             "unit": transform["target_unit"], "basis": [*value["basis"], "EXACT_UNIT_SCALE/1"]}
                _bind_unknowns(value, query)
                unknown = value["state"] == "PV_UNKNOWN"
                out.update(value=value, status="UNRESOLVED" if unknown else "CONDITIONAL" if source["verdict"] == "SC_CONDITIONAL_MODEL_ONLY" else "VERIFIED",
                           reason="SOURCE_VALUE_UNKNOWN" if unknown else "SCOPED_REUSE", claim_source="RECEIVED_ARTIFACT")
                if not unknown:
                    out["obligation_effects"] = _effects(operation, context, {"YA_DISPONIBLE"})
            return out
        if kind == "CERTIFY_FDQ":
            require(set(params) == {"input_ref", "result_ref", "certificate_ref"}, "OPERATION_PARAMETER_FIELDS")
            require(query["kind"] in ("frontier", "selector"), "FDQ_QUERY_KIND")
            refs = [params[k] for k in ("input_ref", "result_ref", "certificate_ref")]
            require(set(refs) <= set(query["artifact_refs"]), "FDQ_ARTIFACT_QUERY_BINDING")
            raw, original, cert_raw = [_artifact(context, ref) for ref in refs]
            cert, base = strict_json(cert_raw), strict_json(raw)
            flags = {"frontier": query["kind"] == "frontier", "selector": query["kind"] == "selector"}
            require(cert["query"] == flags, "FDQ_QUERY_FLAGS")
            require(query["scope"] == fdq_scope(raw, original, cert), "FDQ_QUERY_SCOPE")
            require(query["target_spec"] == fdq_target_spec(raw, query["kind"]), "FDQ_TARGET_SPEC_BINDING")
            require(query["norm"] == base["selection"], "FDQ_NORM_BINDING")
            require(cert["target"] == query["scope"]["target"], "FDQ_TARGET_BINDING")
            out["artifact_refs"] = refs
            run = run_fdq(raw, original, cert_raw, context["baseline_r1"], context["baseline_r0"],
                          context["budget"]["certificate_timeout_seconds"], context.get("cancel_check"))
            out["evidence"].append({"fdq_receipt": run, "query_sha256": out["query_sha256"],
                                    "premises": ["REAL_DOMAIN_MEMBERSHIP_NOT_ESTABLISHED", "RECEIVED_TABULAR_MODEL_ONLY"],
                                    "domain": cert["domain"]})
            verification = run["verification"]
            if verification is None:
                inconclusive = run["reason"] in ("FDQ_PROCESS_TIMEOUT", "FDQ_PROCESS_CANCELLED", "FDQ_OUTPUT_BUDGET")
                out.update(status="INCONCLUSIVE" if inconclusive else "ERROR", reason=run["reason"],
                           execution_state="PE_UNKNOWN" if inconclusive else "PE_ERROR",
                           value=_unknown(run["reason"], operation))
                return out
            state = verification["state"]
            statuses = {"SUFFICIENT": "CONDITIONAL", "NOT_ACCEPTED": "REJECTED", "OUTSIDE_PROFILE": "OUTSIDE_PROFILE", "INCONCLUSIVE": "INCONCLUSIVE"}
            require(state in statuses, "UNRECOGNIZED_FDQ_STATE")
            out.update(status=statuses[state], reason=verification.get("reason", state), claim_source="DECISION_SUFFICIENCY/0.1.0")
            if state == "SUFFICIENT":
                out["value"] = {"state": "PV_KNOWN", "value": verification["claim"],
                                "unit": "policy_id_set_or_selector", "basis": ["FDQ_FINITE_PATCH/0.1.0", *refs]}
                out["evidence"][0]["state"] = "EV_CONDITIONAL"
                records = verification["records"]
                target = query["scope"]["target"]
                all_refuted = bool(target) and bool(records) and all(
                    set(record["hard"]) == set(target) and all(
                        any(flag == "0" for flag in record["hard"][policy].values())
                        for policy in target) for record in records)
                if all_refuted:
                    out["evidence"][0]["all_policies_refuted"] = True
                    out["evidence"][0]["hard_witnesses"] = [
                        {"ordinal": record["ordinal"], "hard": record["hard"], "input_sha256": record["input_sha256"]}
                        for record in records]
                    out["evidence"][0]["coverage"] = {"target": target, "members": len(records), "scope": "ENTIRE_DECLARED_FINITE_FAMILY"}
                out["obligation_effects"] = _effects(operation, context, {"COMPUTO_PENDIENTE", "IRRELEVANTE_DEMOSTRADO"})
            else:
                out["value"] = _unknown(out["reason"], operation)
                if state == "INCONCLUSIVE":
                    out["execution_state"] = "PE_BUDGET_EXHAUSTED"
            return out
        if kind == "PROVE_IRRELEVANCE":
            require(set(params) == {"artifact_ref", "rule_id", "field"}, "OPERATION_PARAMETER_FIELDS")
            field, rule = params["field"], "B01_RECEIVED_CLASSIFICATION/1"
            require(params["rule_id"] == rule and field in ("D4", "H13", "H14"), "RECEIVED_CLASSIFICATION_RULE")
            require(query["kind"] == "component" and query["scope"] == {"operator": rule, "field": field, "purpose": "RECEIVED_DIAGNOSIS_ONLY"}, "RECEIVED_CLASSIFICATION_SCOPE")
            ref = params["artifact_ref"]
            require(ref in query["artifact_refs"], "CLASSIFICATION_ARTIFACT_BINDING")
            raw = _artifact(context, ref)
            require(digest(raw) == DIAGNOSIS_SHA256, "RECEIVED_DIAGNOSIS_DIGEST")
            out.update(status="VERIFIED", reason="RECEIVED_CLASSIFICATION_ONLY", claim_source=rule,
                       artifact_refs=[ref], value={"state": "PV_KNOWN", "value": {
                           "field": field, "primary_cause": "IRRELEVANTE_DEMOSTRADO",
                           "applicability": "INSPECTED_QUERIES_ONLY" if field == "D4" else "NOT_APPLICABLE",
                           "scope": "RECEIVED_B01_DIAGNOSIS_ONLY"}, "unit": "classification", "basis": [ref, DIAGNOSIS_SHA256]})
            out["evidence"] = [{"state": "EV_SUPPORTED_SCOPED", "source_sha256": DIAGNOSIS_SHA256,
                                "limit": "Attribution of received diagnosis; no new B01 calculation or decision.",
                                "query_sha256": out["query_sha256"]}]
            out["obligation_effects"] = _effects(operation, context, {"IRRELEVANTE_DEMOSTRADO"},
                                                  "CLOSED_NOT_APPLICABLE" if field != "D4" else "CLOSED_SCOPED")
            return out
        if kind == "ASSESS_SOURCE":
            require(set(params) == {"assessment"}, "OPERATION_PARAMETER_FIELDS")
            source = _source(params, query, context)
            out.update(reason=source["verdict"], evidence=[{"source_assessment": source}],
                       artifact_refs=([params["assessment"]["source_ref"]]
                                      if params["assessment"]["source_ref"] in context["artifacts"] else []),
                       value=_unknown("COMPATIBILITY_IS_NOT_QUERY_ANSWER", operation))
            return out
        if kind == "EXPAND_MODEL":
            require(set(params) == {"reason", "affected_dependencies"}, "OPERATION_PARAMETER_FIELDS")
            require(type(params["reason"]) is str and bool(params["reason"]) and type(params["affected_dependencies"]) is list, "MODEL_EXPANSION_FIELDS")
            require(any(o["id"] in operation["obligation_refs"] and o["primary_cause"] in ("DEFINICION_MODELO", "CAPACIDAD_AUSENTE") for o in context["request"]["obligations"]), "NO_MODEL_DEPENDENCY")
            out.update(reason="MODEL_ADMISSION_REQUIRED", value=_unknown("MODEL_ADMISSION_REQUIRED", operation),
                       evidence=[{"proposed_reason": params["reason"], "affected_dependencies": params["affected_dependencies"], "model_admitted": False}])
            return out
        if kind == "REQUEST_INPUT":
            require(set(params) == {"obligation_ref", "prompt", "unknown_allowed"}, "OPERATION_PARAMETER_FIELDS")
            require(params["unknown_allowed"] is True and type(params["prompt"]) is str and bool(params["prompt"]), "INPUT_REQUEST_FIELDS")
            require(params["obligation_ref"] in operation["obligation_refs"], "INPUT_REQUEST_OBLIGATION")
            obligation = next(o for o in context["request"]["obligations"] if o["id"] == params["obligation_ref"])
            require(obligation["query_ref"] == query["id"], "INPUT_REQUEST_QUERY")
            require(obligation["primary_cause"] in ("DATO_EXTERNO", "PREFERENCIA", "DEFINICION_MODELO", "CAPACIDAD_AUSENTE"), "INPUT_REQUEST_CAUSE")
            out.update(reason="LOCAL_REQUEST_RECORDED_NOT_SENT", value=_unknown("INPUT_DEPENDENCY", operation),
                       evidence=[{"prompt": params["prompt"], "owner": obligation["owner"], "unknown_allowed": True, "sent": False}])
            return out
        raise OperationRejected("UNSUPPORTED_OPERATION")
    except OperationOutsideProfile as exc:
        out.update(status="OUTSIDE_PROFILE", reason=str(exc),
                   value={"state": "PV_OUTSIDE_PROFILE", "reasons": [str(exc)],
                          "profile_ref": "GENIUS_LOCAL_REUSE/0.1.0"}, obligation_effects=[])
        return out
    except (OperationRejected, KeyError, IndexError, TypeError, ValueError, StopIteration) as exc:
        out.update(status="REJECTED", reason=str(exc), value=_unknown(str(exc), operation), obligation_effects=[])
        return out
    except (OSError, ImportError) as exc:
        out.update(status="ERROR", reason=type(exc).__name__ + ":" + str(exc),
                   execution_state="PE_ERROR", value=_unknown("OPERATION_RUNTIME_ERROR", operation), obligation_effects=[])
        return out
