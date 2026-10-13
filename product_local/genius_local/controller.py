"""Bounded local orchestration with persisted operation receipts.

Artifact paths are relative to the request's directory and must contain no
parent traversal or symlinks. Recovery closes an interrupted attempt UNKNOWN;
it never silently reruns a partially completed operation.
"""
from __future__ import annotations

import copy
import hashlib
import os
from pathlib import Path
import signal
import stat

from . import policy
from .store import Store, StoreError, UnsafePath, canonical

MAX_REQUEST = 4 * 1024 * 1024
MAX_ARTIFACT = 8 * 1024 * 1024
MAX_TOTAL = 32 * 1024 * 1024
MAX_OUTCOMES = 8 * 1024 * 1024
MAX_RESPONSE = 32 * 1024 * 1024
MAX_SNAPSHOT = 64 * 1024 * 1024
PHASES = (("REUSE", ("REUSE",)),
          ("DERIVE", ("DERIVE_HOURS",)),
          ("IRRELEVANCE", ("CERTIFY_FDQ", "PROVE_IRRELEVANCE")),
          ("EXPAND_MODEL", ("EXPAND_MODEL",)),
          ("ASSESS_SOURCE", ("ASSESS_SOURCE",)),
          ("REQUEST_INPUT", ("REQUEST_INPUT",)))


class ControllerError(ValueError):
    pass


class PublicationBudgetExceeded(ControllerError):
    def __init__(self, reason, head):
        super().__init__(reason)
        self.head = head


def _require(condition, reason):
    if not condition:
        raise ControllerError(reason)


def _read_local(path, maximum):
    path = Path(path).absolute()
    _require(".." not in path.parts, "PATH_TRAVERSAL")
    for part in [*reversed(path.parents), path]:
        if part.is_symlink():
            raise UnsafePath("SYMLINK_INPUT_FORBIDDEN")
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0))
    with os.fdopen(descriptor, "rb") as stream:
        info = os.fstat(stream.fileno())
        _require(stat.S_ISREG(info.st_mode), "INPUT_NOT_REGULAR_FILE")
        _require(info.st_size <= maximum, "INPUT_SIZE_BUDGET_EXHAUSTED")
        raw = stream.read(maximum + 1)
    _require(len(raw) <= maximum, "INPUT_SIZE_BUDGET_EXHAUSTED")
    return raw


def _import_request(request_path):
    request_path = Path(request_path).absolute()
    raw = _read_local(request_path, MAX_REQUEST)
    request = policy.loads_strict(raw)
    _require(isinstance(request, dict), "REQUEST_MUST_BE_OBJECT")
    descriptors = request.get("artifacts")
    _require(isinstance(descriptors, list) and len(descriptors) <= 256, "ARTIFACT_COUNT_LIMIT")
    artifacts = {}
    total = 0
    for entry in descriptors:
        _require(isinstance(entry, dict) and isinstance(entry.get("id"), str) and isinstance(entry.get("path"), str), "INVALID_ARTIFACT_DESCRIPTOR")
        _require(entry["id"] not in artifacts, "DUPLICATE_ARTIFACT_ID")
        relative = Path(entry["path"])
        _require(bool(entry["path"]) and not relative.is_absolute() and ".." not in relative.parts, "ARTIFACT_PATH_MUST_STAY_WITHIN_REQUEST_ROOT")
        data = _read_local(request_path.parent / relative, min(MAX_ARTIFACT, MAX_TOTAL - total))
        total += len(data)
        _require(hashlib.sha256(data).hexdigest() == entry.get("sha256"), "ARTIFACT_DIGEST_MISMATCH")
        artifacts[entry["id"]] = {"metadata": copy.deepcopy(entry), "bytes": data}
    validated = policy.validate_request(request, lambda ref: artifacts[ref]["bytes"])
    return raw, validated, artifacts


def _restore_artifacts(store, snapshot):
    return {key: {"metadata": value["metadata"],
                  "bytes": store.get_bytes(value["stored_ref"]["sha256"])}
            for key, value in snapshot["artifact_records"].items()}


def _producer_identity():
    """Identity of the finite local implementation that verifies receipts.

    This is provenance, not protection against an administrator replacing the
    process or its files. A caller cannot supply this value in a request.
    """
    names = ("__init__.py", "__main__.py", "controller.py", "store.py",
             "policy.py", "operations.py", "fdq_worker.py")
    directory = Path(__file__).parent
    modules = {name: hashlib.sha256((directory / name).read_bytes()).hexdigest() for name in names}
    return {"format": "genius-local-producer/0.1.0", "modules": modules,
            "sha256": hashlib.sha256(canonical(modules)).hexdigest()}


def _semantic_request(request, artifacts):
    """Compare admitted meaning, resolving references only in typed positions.

    Alias names of queries/obligations/operations/assessments/artifacts are not
    new evidence. Conversely, a literal descriptor equal to such a name is
    still a literal; it must never be replaced by a global string rewrite.
    Shared dependency DAGs use memoized digests rather than unfolded trees.
    """
    queries = {q["id"]: q for q in request["queries"]}
    obligations = {o["id"]: o for o in request["obligations"]}
    obligation_signatures = {}

    def unique(items):
        return [value for _, value in sorted({canonical(value): value for value in items}.items())]

    # Only the admitted contractual-hours grammar contains request-local refs
    # inside source JSON. Do not rewrite arbitrary JSON strings or FP1 IDs.
    # Store/cache identities remain the original byte digests.
    from .operations import derive_hours
    hours_sources = {}
    for operation in request["operations"]:
        if operation["kind"] != "DERIVE_HOURS":
            continue
        ref = operation["parameters"]["artifact_ref"]
        try:
            value = policy.loads_strict(artifacts[ref]["bytes"])
            derive_hours(value)
            cells = [("target_hours", value["target_hours"])] + [
                ("assignments/" + str(index) + "/credit_hours", row["credit_hours"])
                for index, row in enumerate(value["assignments"])]
            refs = [(path, cell["obligation_refs"]) for path, cell in cells if cell["state"] == "PV_UNKNOWN"]
            if all(set(bound) <= set(queries[operation["query_ref"]]["obligation_refs"]) for _, bound in refs):
                hours_sources[ref] = (value, refs)
        except (ValueError, TypeError, KeyError):
            pass  # Unsupported sources retain exact-byte identity for comparison.

    def literal(value):
        if isinstance(value, dict):
            if value.get("state") in ("PV_UNKNOWN", "PV_NOT_APPLICABLE", "PV_OUTSIDE_PROFILE"):
                return {"state": value["state"], **({"profile_ref": value["profile_ref"]} if "profile_ref" in value else {})}
            return {key: literal(child) for key, child in value.items()}
        if isinstance(value, list):
            return [literal(child) for child in value]
        return value

    def data(ref, pointer=None):
        entry = artifacts[ref]
        descriptor = {"evidence_kind": entry["metadata"]["evidence_kind"],
                      "permissions": {key: entry["metadata"]["permissions"][key] for key in ("access", "use")}}
        if pointer is None:
            if ref in hours_sources:
                descriptor["contractual_hours"] = literal(hours_sources[ref][0])
            else:
                descriptor["sha256"] = entry["metadata"]["sha256"]
        else:
            descriptor["received_value"] = literal(policy.pointer_get(policy.loads_strict(entry["bytes"]), pointer))
        return descriptor

    def query(q):
        scope = literal(q["scope"])
        if scope.get("operator") == "REUSE/1" and "artifact_ref" in scope:
            scope = {"operator": "REUSE/1", "pointer": scope["pointer"],
                     "received_source": data(scope["artifact_ref"], scope["pointer"])}
        return {"kind": q["kind"], "target_spec": literal(q["target_spec"]),
                "scope": scope, "norm": literal(q["norm"])}

    query_signatures = {ref: hashlib.sha256(canonical(query(q))).hexdigest() for ref, q in queries.items()}

    def claim(ref):
        return {"query": query_signatures[ref]} if ref in queries else {"literal_claim": ref}

    def obligation(ref):
        if ref in obligation_signatures:
            return obligation_signatures[ref]
        item = obligations[ref]
        signature = {"query": query_signatures[item["query_ref"]],
                     "affected_claims": unique(claim(ref) for ref in item["affected_claims"]),
                     "primary_cause": item["primary_cause"],
                     "secondary_causes": sorted(item["secondary_causes"]),
                     "input_spec": literal({k: v for k, v in item["input_spec"].items() if k != "reason"}),
                     "derivation_rule": {key: (obligation(value) if key == "obligation_ref" else
                         basis(value) if key == "basis" else literal(value))
                         for key, value in item["derivation_rule"].items() if key != "reason"},
                     "dependencies": unique({"role": dep["role"], "obligation": obligation(dep["ref"])}
                         for dep in item["dependencies"])}
        obligation_signatures[ref] = hashlib.sha256(canonical(signature)).hexdigest()
        return obligation_signatures[ref]

    def basis(value):
        if isinstance(value, dict) and set(value) == {"artifact_ref", "pointer"}:
            return data(value["artifact_ref"], value["pointer"])
        return literal(value)

    def assessment(a):
        # Only fields that affect the admitted source correspondence enter the
        # comparison. Claim/affected_claims and bridges are resolved as refs;
        # source/target values and rule text retain their literal meaning.
        bridges = {row["id"]: {k: basis(v) if k == "basis" else literal(v)
                   for k, v in row.items() if k != "id"} for row in a["transformation_chain"]}
        axes = {}
        for name, axis in a["axes"].items():
            axes[name] = {k: (basis(v) if k == "basis" else
                         unique(claim(ref) for ref in v) if k == "affected_claims" else
                         bridges[v] if k == "bridge_ref" and v in bridges else literal(v))
                         for k, v in axis.items()}
        conflicts = [{k: ([data(ref) for ref in v] if k == "source_refs" else literal(v))
                      for k, v in conflict.items()} for conflict in a["conflicts"]]
        permissions = {key: a["access_and_permissions"][key] for key in ("access", "use")}
        return {"query": query_signatures[a["query_ref"]], "claim": claim(a["claim"]),
                "source": data(a["source_ref"]) if a["source_ref"] in artifacts else "NOT_ACQUIRED",
                "target_spec": literal(a["target_spec"]), "axes": axes,
                "permissions": permissions, "evidence_kind": a["evidence_kind"],
                "relevant_period": literal(a["relevant_period"]),
                "transformation_chain": sorted(bridges.values(), key=canonical), "conflicts": conflicts}

    operations = []
    for operation in request["operations"]:
        kind, params = operation["kind"], operation["parameters"]
        normalized = {}
        for key, value in params.items():
            if key == "assessment":
                normalized[key] = assessment(value)
            elif key in ("artifact_ref", "input_ref", "result_ref", "certificate_ref"):
                normalized[key] = data(value, params["pointer"] if kind == "REUSE" else None)
            elif key == "obligation_ref":
                normalized[key] = obligation(value)
            elif key == "affected_dependencies":
                normalized[key] = sorted(set(obligation(ref) for ref in operation["obligation_refs"]))
            elif key not in ("reason", "prompt"):
                normalized[key] = literal(value)
        operations.append({"kind": kind, "query": query_signatures[operation["query_ref"]],
                           "obligations": sorted(set(obligation(ref) for ref in operation["obligation_refs"])),
                           "parameters": normalized})
    cell_dependencies = unique({"source": data(ref), "bindings": [
        {"path": path, "obligations": sorted(set(obligation(bound) for bound in refs))}
        for path, refs in cells]} for ref, (_, cells) in hours_sources.items())
    return {"queries": unique(query(q) for q in request["queries"]),
            "obligations": sorted(set(obligation(ref) for ref in obligations)),
            "operations": unique(operations), "source_cell_dependencies": cell_dependencies}


def _continuation(store, chain, request, artifacts):
    if not chain:
        _require(request["supersedes"] is None and request["revision"] == 1, "INITIAL_REVISION_REQUIRED")
        return None
    previous = chain[-1]
    payload = _decode_payload(store, previous["payload"])
    producer_changed = payload.get("producer") != _producer_identity()
    _require(payload.get("phase") in ("CLOSED", "RECOVERED_CLOSED", "BUDGET_CLOSED")
             or (payload.get("phase") == "RUNNING" and producer_changed),
             "INTERRUPTED_ATTEMPT_REQUIRES_RECOVER")
    _require(request["supersedes"] == {"revision": previous["revision"], "sha256": previous["sha256"]}, "SUPERSEDES_MUST_MATCH_CURRENT_HEAD")
    _require(request["request_id"] == payload["request"]["request_id"], "CONTINUATION_REQUIRES_SAME_REQUEST_ID")
    _require(request["revision"] == payload["request"]["revision"] + 1, "LOGICAL_REVISION_MUST_INCREMENT")
    _require(payload.get("no_progress_streak", 0) < 2, "TWO_ATTEMPTS_WITHOUT_PROGRESS_REVIEW_REQUIRED")
    changed = request["novelty"]["changed_refs"]
    known_refs = {q["id"] for q in request["queries"]} | {o["id"] for o in request["obligations"]} | set(artifacts) | {"budget"} | {o["id"] for o in request["operations"]}
    _require(bool(changed) and set(changed) <= known_refs, "NOVELTY_REQUIRES_KNOWN_CHANGED_REFS")
    explicit_reverification = (producer_changed
        and request["novelty"]["reason"] == "REVERIFY_IMPLEMENTATION_CHANGED"
        and bool(set(changed) & {operation["id"] for operation in request["operations"]}))
    if explicit_reverification:
        # The old request is preserved history, potentially admitted under a
        # weaker producer. Only the new request passed current validation; do
        # not reinterpret old rule metadata as a newly admitted dependency DAG.
        return payload
    _require(not producer_changed, "IMPLEMENTATION_CHANGED_REQUIRES_EXPLICIT_REVERIFICATION")
    prior_artifacts = _restore_artifacts(store, payload)
    old_semantics = _semantic_request(payload["request"], prior_artifacts)
    new_semantics = _semantic_request(request, artifacts)
    budget_increase = (payload.get("execution", {}).get("state") in ("PE_BUDGET_EXHAUSTED", "PE_UNKNOWN")
                       and any(request["budget"][key] > payload["request"]["budget"][key] for key in request["budget"]))
    explicit_interruption_retry = (payload.get("execution", {}).get("state") == "PE_UNKNOWN"
        and request["novelty"]["reason"] == "RETRY_INTERRUPTED_OPERATION"
        and bool(set(changed) & {o["id"] for o in request["operations"] if o["id"] == payload.get("active_operation") or any(r["operation_id"] == o["id"] and r.get("execution_state") == "PE_UNKNOWN" for r in payload["outcomes"])}))
    _require(old_semantics != new_semantics or budget_increase or explicit_interruption_retry,
             "NO_PERTINENT_NOVELTY")
    return payload


def _registry(snapshot):
    received = [{**value["metadata"], "path": value["stored_ref"]["path"],
                 "size": value["stored_ref"]["size"]} for value in snapshot["artifact_records"].values()]
    return {"received": received, "expected": [
        {"id": item["id"], "state": "RECEIVED", "sha256": item["sha256"], "ref": item["id"]}
        for item in received]}


def _response(snapshot, request_ref):
    return policy.build_response(snapshot["request"], snapshot["outcomes"], {
        "execution": snapshot["execution"], "ledger": snapshot["ledger"],
        "artifacts": _registry(snapshot), "request_ref": request_ref,
        "versions": policy.SUPPORTED_VERSIONS, "budget_used": snapshot["budget_used"],
        "closure_reason": snapshot.get("closure_reason")})


def _save(store, snapshot, head):
    size_exceeded = len(canonical(snapshot)) > MAX_SNAPSHOT
    compact = {key: copy.deepcopy(value) for key, value in snapshot.items() if key not in ("request", "outcomes", "ledger", "response")}
    compact["storage_format"] = "genius-local-snapshot-refs/0.1.0"
    compact["outcome_refs"] = [_store_chunks(store, canonical(item)) for item in snapshot["outcomes"]]
    compact["ledger_ref"] = _store_chunks(store, canonical(snapshot["ledger"]))
    if "response" in snapshot:
        compact["response_ref"] = _store_chunks(store, canonical(snapshot["response"]))
    if size_exceeded:
        compact["phase"] = "BUDGET_CLOSED"
        compact["execution"] = {"state": "PE_BUDGET_EXHAUSTED", "reason": "SNAPSHOT_SIZE_BUDGET_EXHAUSTED", "progress": {"received_operations": len(snapshot["outcomes"])}}
        compact["closure_reason"] = "SNAPSHOT_SIZE_BUDGET_EXHAUSTED"
        if "response_ref" in compact:
            compact["unpublished_response_ref"] = compact.pop("response_ref")
        committed = store.commit(compact, head)["sha256"]
        raise PublicationBudgetExceeded("SNAPSHOT_SIZE_BUDGET_EXHAUSTED", committed)
    return store.commit(compact, head)["sha256"]


def _store_chunks(store, raw):
    return {"sha256": hashlib.sha256(raw).hexdigest(), "size": len(raw),
            "chunks": [store.put_bytes(raw[index:index + MAX_ARTIFACT]) for index in range(0, len(raw), MAX_ARTIFACT)]}


def _read_chunks(store, ref):
    _require(type(ref.get("size")) is int and 0 <= ref["size"] <= MAX_SNAPSHOT, "INVALID_CHUNKED_OBJECT_SIZE")
    _require(isinstance(ref.get("chunks"), list) and len(ref["chunks"]) <= 8, "INVALID_CHUNK_COUNT")
    raw = b"".join(store.get_bytes(chunk["sha256"]) for chunk in ref["chunks"])
    _require(len(raw) == ref["size"] and hashlib.sha256(raw).hexdigest() == ref["sha256"], "CHUNKED_OBJECT_MISMATCH")
    return raw


def _decode_payload(store, payload):
    if payload.get("storage_format") != "genius-local-snapshot-refs/0.1.0":
        raise ControllerError("UNSUPPORTED_SNAPSHOT_FORMAT")
    restored = {key: copy.deepcopy(value) for key, value in payload.items() if key not in ("storage_format", "outcome_refs", "ledger_ref", "response_ref")}
    restored["request"] = policy.loads_strict(store.get_bytes(payload["request_artifact"]["sha256"]))
    restored["outcomes"] = [policy.loads_strict(_read_chunks(store, ref)) for ref in payload["outcome_refs"]]
    restored["ledger"] = policy.loads_strict(_read_chunks(store, payload["ledger_ref"]))
    if "response_ref" in payload:
        # A response may exceed one artifact; JSON strict parser's artifact
        # bound is bypassed only after bounded chunks/digest are validated.
        restored["response"] = policy.loads_strict(_read_chunks(store, payload["response_ref"]).decode("utf-8"))
    return restored


def inspect(case_dir):
    store = Store(case_dir)
    result = store.inspect()
    result["latest"] = _decode_payload(store, result["revisions"][-1]["payload"]) if result["revisions"] else None
    return result


def _reuse_key(request, operation, artifacts):
    query = next(q for q in request["queries"] if q["id"] == operation["query_ref"])
    by_id = {o["id"]: o for o in request["obligations"]}
    relevant = set(query["obligation_refs"])
    pending = list(relevant)
    while pending:
        for dep in by_id[pending.pop()]["dependencies"]:
            if dep["ref"] not in relevant:
                relevant.add(dep["ref"])
                pending.append(dep["ref"])
    material = {"producer": _producer_identity(), "query": query,
                "operation": {key: value for key, value in operation.items() if key != "id"},
                "obligations": [by_id[ref] for ref in sorted(relevant)],
                "artifacts": {key: {"sha256": item["metadata"]["sha256"], "evidence_kind": item["metadata"]["evidence_kind"], "permissions": item["metadata"]["permissions"]} for key, item in artifacts.items()}}
    return hashlib.sha256(canonical(material)).hexdigest()


def _lookup_prior_receipt(store, chain, key, operation, query):
    for revision in reversed(chain):
        payload = revision["payload"]
        if payload.get("phase") not in ("CLOSED", "RECOVERED_CLOSED"):
            continue
        snapshot = _decode_payload(store, payload)
        if snapshot.get("producer") != _producer_identity():
            continue
        for outcome in snapshot["outcomes"]:
            if outcome["status"] in ("VERIFIED", "CONDITIONAL") and snapshot.get("reuse_keys", {}).get(outcome["operation_id"]) == key:
                copied = copy.deepcopy(outcome)
                copied["operation_id"] = operation["id"]
                copied["query_ref"] = query["id"]
                copied["query_sha256"] = policy.query_digest(query)
                for effect in copied["obligation_effects"]:
                    effect["witness_refs"] = [operation["id"] if witness == outcome["operation_id"] else witness for witness in effect["witness_refs"]]
                copied["evidence"].append({"type": "LOCAL_RECEIPT_REUSE", "source_revision": revision["sha256"], "source_operation_id": outcome["operation_id"], "source_request_sha256": snapshot["request_artifact"]["sha256"], "new_computation": False})
                return copied
    return None


def recover(case_dir):
    store = Store(case_dir)
    with store.writer():
        chain = store.load_chain()
        _require(bool(chain), "CASE_HAS_NO_COMMITTED_REQUEST")
        head = chain[-1]
        snapshot = _decode_payload(store, head["payload"])
        if snapshot.get("phase") == "BUDGET_CLOSED":
            raise PublicationBudgetExceeded(snapshot["closure_reason"], head["sha256"])
        if snapshot.get("phase") in ("CLOSED", "RECOVERED_CLOSED"):
            return snapshot["response"]
        _require(snapshot.get("phase") == "RUNNING", "UNRECOGNIZED_SNAPSHOT_STATE")
        _require(snapshot.get("producer") == _producer_identity(),
                 "IMPLEMENTATION_CHANGED_REQUIRES_EXPLICIT_REVERIFICATION")
        _restore_artifacts(store, snapshot)
        snapshot["execution"] = {"state": "PE_UNKNOWN", "reason": "PROCESS_INTERRUPTION_WITHOUT_FINAL_RECEIPT",
                                 "progress": {"received_operations": len(snapshot["outcomes"]), "active_operation": snapshot.get("active_operation")}}
        snapshot["closure_reason"] = "PROCESS_INTERRUPTION"
        snapshot["phase"] = "RECOVERED_CLOSED"
        snapshot["no_progress_streak"] = 0 if _has_progress(snapshot["outcomes"]) else snapshot.get("previous_no_progress_streak", 0) + 1
        snapshot["ledger"]["worklog"].append({"phase": "RECOVERY", "status": "BLOCKED", "reason": "No final receipt exists for the interrupted operation; prior receipts preserved."})
        response = _response(snapshot, {"revision": snapshot["request"]["revision"], "sha256": snapshot["request_artifact"]["sha256"]})
        snapshot["response"] = response
        _save(store, snapshot, head["sha256"])
        return response


def execute(request_path, case_dir, baseline_r0, baseline_r1, cancel_file=None):
    from .operations import execute_operation
    store = Store(case_dir)
    with store.writer():
        chain = store.load_chain()
        raw, request, artifacts = _import_request(request_path)
        previous = _continuation(store, chain, request, artifacts)
        records = {key: {"metadata": item["metadata"], "stored_ref": store.put_bytes(item["bytes"])} for key, item in artifacts.items()}
        request_artifact = store.put_bytes(raw)
        snapshot = {"phase": "RUNNING", "request": request, "request_artifact": request_artifact,
                    "producer": _producer_identity(),
                    "artifact_records": records, "outcomes": [],
                    "ledger": {"obligations": copy.deepcopy(request["obligations"]), "worklog": [], "attempts": []},
                    "budget_used": {"operations": 0, "certificates": 0, "network_acquisitions": 0},
                    "active_operation": None, "reuse_keys": {},
                    "previous_no_progress_streak": previous.get("no_progress_streak", 0) if previous else 0}
        head = _save(store, snapshot, chain[-1]["sha256"] if chain else None)
        cancel_by_signal = [False]
        original_handlers = {}
        def signal_cancel(signum, frame):
            cancel_by_signal[0] = True
        # Library callers may run off the main thread; their cancellation
        # mechanism remains the explicit local cancel file.
        import threading
        if threading.current_thread() is threading.main_thread():
            for signum in (signal.SIGINT, signal.SIGTERM):
                original_handlers[signum] = signal.getsignal(signum)
                signal.signal(signum, signal_cancel)
        def cancelled():
            if cancel_by_signal[0]:
                return True
            if cancel_file is None:
                return False
            candidate = Path(cancel_file)
            if candidate.is_symlink():
                raise UnsafePath("SYMLINK_CANCEL_FILE_FORBIDDEN")
            return candidate.exists()

        execution = {"state": "PE_COMPLETE", "reason": "ALL_CONTRACTED_OPERATIONS_FINISHED", "progress": {}}
        stop = False
        queries = {q["id"]: q for q in request["queries"]}
        try:
            for phase, kinds in PHASES:
                operations = [op for op in request["operations"] if op["kind"] in kinds]
                if not operations:
                    snapshot["ledger"]["worklog"].append({"phase": phase, "status": "NOT_APPLICABLE", "reason": "No operation of this phase is supplied in the admitted request; this is not proof of irrelevance."})
                    continue
                phase_outcomes = []
                for operation in operations:
                    if cancelled():
                        execution = {"state": "PE_CANCELLED", "reason": "COOPERATIVE_CANCEL_BETWEEN_OPERATIONS", "progress": {}}
                        snapshot["closure_reason"] = "CANCELLED"
                        stop = True
                        break
                    query = queries[operation["query_ref"]]
                    key = _reuse_key(request, operation, artifacts)
                    reused = _lookup_prior_receipt(store, chain, key, operation, query)
                    if operation["kind"] == "REQUEST_INPUT":
                        obligation = next(o for o in snapshot["ledger"]["obligations"] if o["id"] == operation["parameters"]["obligation_ref"])
                        if obligation["status"].startswith("CLOSED_") and obligation["closure"]["verified"]:
                            reused = {"operation_id": operation["id"], "query_ref": query["id"], "query_sha256": policy.query_digest(query), "kind": operation["kind"], "status": "UNRESOLVED", "reason": "INPUT_REQUEST_NOT_NEEDED_CLOSED_OBLIGATION", "claim_source": "LOCAL_WORKFLOW", "value": {"state": "PV_NOT_APPLICABLE", "reasons": ["The relevant obligation already has a verified scoped closure; no question is generated."], "scope": {"obligation_ref": obligation["id"]}}, "evidence": [{"closure": copy.deepcopy(obligation["closure"])}], "obligation_effects": [], "artifact_refs": []}
                    snapshot["ledger"]["worklog"].append({"phase": "REUSE_LOOKUP", "operation_ref": operation["id"], "status": "APPLIED" if reused else "NOT_APPLICABLE", "reason": "Matching verified receipt reused with its original provenance." if reused else "No matching receipt in this case's supplied, verified inventory; no claim about other sources."})
                    is_certificate = operation["kind"] == "CERTIFY_FDQ" and reused is None
                    if snapshot["budget_used"]["operations"] >= request["budget"]["max_operations"] or (is_certificate and snapshot["budget_used"]["certificates"] >= request["budget"]["max_certificates"]):
                        execution = {"state": "PE_BUDGET_EXHAUSTED", "reason": "DECLARED_OPERATION_OR_CERTIFICATE_LIMIT", "progress": {}}
                        snapshot["closure_reason"] = "BUDGET_EXHAUSTED"
                        stop = True
                        break
                    snapshot["active_operation"] = operation["id"]
                    snapshot["budget_used"]["operations"] += 1
                    snapshot["budget_used"]["certificates"] += int(is_certificate)
                    head = _save(store, snapshot, head)
                    try:
                        outcome = reused if reused is not None else execute_operation(operation, {"request": request, "query": query,
                            "blob_reader": lambda ref: artifacts[ref]["bytes"], "artifacts": artifacts,
                            "baseline_r0": Path(baseline_r0), "baseline_r1": Path(baseline_r1),
                            "budget": request["budget"], "cancel_check": cancelled})
                    except Exception as exc:
                        outcome = {"operation_id": operation["id"], "query_ref": query["id"],
                                   "query_sha256": policy.query_digest(query), "kind": operation["kind"],
                                   "status": "ERROR", "reason": type(exc).__name__ + ": " + str(exc),
                                   "claim_source": "LOCAL_ADAPTER_ERROR", "value": {"state": "PV_UNKNOWN", "reasons": ["Operation failed without mathematical conclusion."], "obligation_refs": query["obligation_refs"]},
                                   "evidence": [], "obligation_effects": [], "artifact_refs": [], "execution_state": "PE_ERROR"}
                    _require(outcome["operation_id"] == operation["id"] and outcome["query_ref"] == query["id"] and outcome["query_sha256"] == policy.query_digest(query), "INTERNAL_OUTCOME_BINDING_ERROR")
                    if len(canonical(snapshot["outcomes"] + [outcome])) > MAX_OUTCOMES:
                        retained = _store_chunks(store, canonical(outcome))
                        outcome = {"operation_id": operation["id"], "query_ref": query["id"], "query_sha256": policy.query_digest(query), "kind": operation["kind"], "status": "INCONCLUSIVE", "reason": "AGGREGATE_OUTCOME_SIZE_BUDGET_EXHAUSTED", "claim_source": "LOCAL_OUTPUT_BUDGET", "value": {"state": "PV_UNKNOWN", "reasons": ["Outcome exceeded local publication budget; retained bytes are not an admitted conclusion."], "obligation_refs": query["obligation_refs"]}, "evidence": [{"unpublished_outcome": retained}], "obligation_effects": [], "artifact_refs": [], "execution_state": "PE_BUDGET_EXHAUSTED"}
                    snapshot["outcomes"].append(outcome)
                    snapshot["reuse_keys"][operation["id"]] = key
                    phase_outcomes.append(outcome)
                    snapshot["active_operation"] = None
                    provisional = {**snapshot, "execution": {"state": "PE_PARTIAL", "reason": "RECEIPTS_VERIFIED_BEFORE_NEXT_OPERATION", "progress": {"received_operations": len(snapshot["outcomes"])}}}
                    checked = _response(provisional, {"revision": request["revision"], "sha256": request_artifact["sha256"]})
                    snapshot["ledger"]["obligations"] = checked["obligations_ref"]["record"]["obligations"]
                    head = _save(store, snapshot, head)
                    if outcome.get("execution_state") in ("PE_UNKNOWN", "PE_ERROR", "PE_BUDGET_EXHAUSTED", "PE_CANCELLED"):
                        execution = {"state": outcome["execution_state"], "reason": outcome["reason"], "progress": {}}
                        snapshot["closure_reason"] = "CANCELLED" if cancelled() else ("BUDGET_EXHAUSTED" if "BUDGET" in outcome["reason"] or "TIMEOUT" in outcome["reason"] else "OPERATION_INTERRUPTED_OR_ERROR")
                        stop = True
                        break
                snapshot["ledger"]["worklog"].append({"phase": phase, "status": "APPLIED" if phase_outcomes else "BLOCKED", "operation_refs": [item["operation_id"] for item in phase_outcomes], "reason": execution["reason"] if stop else "Executed operations retain individual receipts and limits."})
                if stop:
                    break
        finally:
            for signum, handler in original_handlers.items():
                signal.signal(signum, handler)
        completed_phases = {item["phase"] for item in snapshot["ledger"]["worklog"]}
        for phase, _ in PHASES:
            if phase not in completed_phases:
                snapshot["ledger"]["worklog"].append({"phase": phase, "status": "BLOCKED", "reason": "Attempt stopped before this phase: " + execution["reason"]})
        execution["progress"] = {"received_operations": len(snapshot["outcomes"]), "requested_operations": len(request["operations"])}
        snapshot["execution"] = execution
        snapshot["phase"] = "CLOSED"
        progress = _has_progress(snapshot["outcomes"])
        snapshot["no_progress_streak"] = 0 if progress else snapshot["previous_no_progress_streak"] + 1
        if snapshot["no_progress_streak"] >= 2:
            snapshot["closure_reason"] = "TWO_ATTEMPTS_WITHOUT_PROGRESS_REVIEW_REQUIRED"
        snapshot["ledger"]["attempts"].append({"request_revision": request["revision"], "substantive_progress": progress, "no_progress_streak": snapshot["no_progress_streak"], "novelty": request["novelty"]})
        response = _response(snapshot, {"revision": request["revision"], "sha256": request_artifact["sha256"]})
        if len(canonical(response)) > MAX_RESPONSE:
            snapshot["unpublished_response_ref"] = _store_chunks(store, canonical(response))
            snapshot["phase"] = "BUDGET_CLOSED"
            snapshot["execution"] = {"state": "PE_BUDGET_EXHAUSTED", "reason": "RESPONSE_SIZE_BUDGET_EXHAUSTED", "progress": execution["progress"]}
            snapshot["closure_reason"] = "RESPONSE_SIZE_BUDGET_EXHAUSTED"
            head = _save(store, snapshot, head)
            raise PublicationBudgetExceeded("RESPONSE_SIZE_BUDGET_EXHAUSTED", head)
        snapshot["ledger"]["obligations"] = response["obligations_ref"]["record"]["obligations"]
        snapshot["response"] = response
        _save(store, snapshot, head)
        return response


def _has_progress(outcomes):
    return any(item["status"] in ("VERIFIED", "CONDITIONAL") and not any(e.get("type") == "LOCAL_RECEIPT_REUSE" for e in item["evidence"] if isinstance(e, dict)) for item in outcomes)
