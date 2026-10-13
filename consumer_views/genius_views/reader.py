"""Bounded, read-only adapter of the received R2 Store and snapshot contract.

Hash checks identify bytes, not external authenticity or mathematical truth.
This module never invokes execute/recover and never changes the source Store.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import re
import stat
import time

from genius_local import policy
from genius_local.store import Store

MAX_CASE_BYTES = 64 * 1024 * 1024
MAX_REVISIONS = 128
MAX_OBJECTS = 2048
MAX_RESPONSE_BYTES = 32 * 1024 * 1024
MAX_EXPORT_BYTES = 120 * 1024 * 1024
SOFT_SECONDS = 10
DIGEST = re.compile(r"[0-9a-f]{64}\Z")


class ViewError(ValueError):
    """No presentation was published; no mathematical conclusion follows."""


def require(condition, reason):
    if not condition:
        raise ViewError(reason)


def canonical(value):
    return policy.canonical_bytes(value)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


class Budget:
    def __init__(self):
        self.started = time.monotonic()

    def check(self):
        require(time.monotonic() - self.started <= SOFT_SECONDS,
                "CONSUMER_TIME_BUDGET_EXHAUSTED")


def safe_path(path, directory=False):
    path = Path(path).absolute()
    require(".." not in path.parts, "PARENT_TRAVERSAL_FORBIDDEN")
    for part in [*reversed(path.parents), path]:
        require(not part.is_symlink(), "SYMLINK_FORBIDDEN")
    if directory:
        require(path.is_dir(), "EXISTING_DIRECTORY_REQUIRED")
    return path


def read_regular(path, maximum):
    path = safe_path(path)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as stream:
        require(stat.S_ISREG(os.fstat(stream.fileno()).st_mode), "REGULAR_FILE_REQUIRED")
        raw = stream.read(maximum + 1)
    require(len(raw) <= maximum, "FILE_BYTE_BUDGET_EXHAUSTED")
    return raw


def inventory(root, budget):
    """Bound before Store.load_chain, whose own integrity guards are reused."""
    safe_path(root, directory=True)
    files = {}
    total = 0
    allowed = {"HEAD", "COMMIT_LOCK", "WRITER_LOCK", "objects", "revisions", "tmp"}
    for entry in root.iterdir():
        budget.check()
        require(entry.name in allowed, "UNRECOGNIZED_STORE_ENTRY")
        safe_path(entry)
        require(entry.is_dir() if entry.name in {"objects", "revisions", "tmp"}
                else entry.is_file(), "INVALID_STORE_ENTRY_TYPE")
        if entry.name not in {"objects", "revisions", "tmp"}:
            info = entry.stat()
            require(info.st_size <= 1024, "ROOT_FILE_BYTE_BUDGET_EXHAUSTED")
            total += info.st_size
            files[entry.name] = (info.st_size, info.st_mtime_ns, info.st_ino)
    for group, count in (("objects", MAX_OBJECTS), ("revisions", MAX_REVISIONS), ("tmp", MAX_OBJECTS)):
        folder = safe_path(root / group, directory=True)
        for index, entry in enumerate(folder.iterdir()):
            budget.check()
            require(index < count, "STORE_ENTRY_COUNT_BUDGET_EXHAUSTED")
            safe_path(entry)
            info = entry.stat()
            require(stat.S_ISREG(info.st_mode), "REGULAR_FILE_REQUIRED")
            if group != "tmp":
                require(DIGEST.fullmatch(entry.name) is not None, "INVALID_CONTENT_ADDRESS")
                require(info.st_size <= 8 * 1024 * 1024, "R2_FILE_LIMIT_EXCEEDED")
            total += info.st_size
            require(total <= MAX_CASE_BYTES, "STORE_BYTE_BUDGET_EXHAUSTED")
            files[group + "/" + entry.name] = (info.st_size, info.st_mtime_ns, info.st_ino)
    return files


def _strict(raw):
    # policy.loads_strict permits larger bounded logical strings. Physical
    # chunk size and aggregate sizes have already been checked independently.
    value = policy.loads_strict(raw.decode("utf-8"))
    require(isinstance(value, dict), "LOGICAL_OBJECT_REQUIRED")
    return value


def _reference(ref, store):
    require(isinstance(ref, dict) and set(ref) == {"sha256", "path", "size"}, "INVALID_CAS_REFERENCE")
    digest = ref["sha256"]
    require(isinstance(digest, str) and DIGEST.fullmatch(digest), "INVALID_CAS_DIGEST")
    require(ref["path"] == "objects/" + digest, "CAS_PATH_MISMATCH")
    require(type(ref["size"]) is int and 0 <= ref["size"] <= 8 * 1024 * 1024,
            "INVALID_CAS_SIZE")
    raw = store.get_bytes(digest)
    require(len(raw) == ref["size"], "CAS_SIZE_MISMATCH")
    return raw


def _chunks(ref, store, budget, maximum=64 * 1024 * 1024):
    require(isinstance(ref, dict) and set(ref) == {"sha256", "size", "chunks"}, "INVALID_LOGICAL_REFERENCE")
    require(type(ref["size"]) is int and 0 <= ref["size"] <= maximum, "LOGICAL_BYTE_BUDGET_EXHAUSTED")
    require(isinstance(ref["chunks"], list) and len(ref["chunks"]) <= 8, "INVALID_CHUNK_COUNT")
    raw = bytearray()
    for chunk in ref["chunks"]:
        budget.check()
        raw.extend(_reference(chunk, store))
        require(len(raw) <= maximum, "LOGICAL_BYTE_BUDGET_EXHAUSTED")
    raw = bytes(raw)
    require(len(raw) == ref["size"] and sha(raw) == ref["sha256"], "LOGICAL_DIGEST_OR_SIZE_MISMATCH")
    return _strict(raw)


def admit_snapshot_envelope(payload):
    require(isinstance(payload, dict), "INVALID_SNAPSHOT_ENVELOPE")
    require(payload.get("storage_format") == "genius-local-snapshot-refs/0.1.0", "UNSUPPORTED_SNAPSHOT_VERSION")
    require(payload.get("phase") in {"RUNNING", "CLOSED", "RECOVERED_CLOSED", "BUDGET_CLOSED"}, "UNSUPPORTED_SNAPSHOT_PHASE")


def admit_historical_objects(payload, store, budget):
    """Admit formats and manifest identities even outside the selected HEAD.

    This checks structured historical objects, never recomputes operations or
    regenerates a historical response under a different producer.
    """
    admit_snapshot_envelope(payload)
    request = _strict(_reference(payload["request_artifact"], store))
    require(request.get("format") == "genius-local-request/0.1.0", "UNSUPPORTED_HISTORICAL_REQUEST_VERSION")
    _chunks(payload["ledger_ref"], store, budget)
    require(isinstance(payload["outcome_refs"], list) and len(payload["outcome_refs"]) <= 64,
            "INVALID_OUTCOME_COUNT")
    for ref in payload["outcome_refs"]:
        _chunks(ref, store, budget, 8 * 1024 * 1024)
    for field in ("response_ref", "unpublished_response_ref"):
        if field in payload:
            response = _chunks(payload[field], store, budget,
                               MAX_RESPONSE_BYTES if field == "response_ref" else 64 * 1024 * 1024)
            require(response.get("format") == "genius-product-response/0.1.0",
                    "UNSUPPORTED_HISTORICAL_RESPONSE_VERSION")
            require(response.get("versions") == policy.SUPPORTED_VERSIONS,
                    "UNSUPPORTED_HISTORICAL_CONTRACT_VERSIONS")


def decode_snapshot(payload, store, budget):
    admit_snapshot_envelope(payload)
    result = {key: value for key, value in payload.items()
              if key not in {"storage_format", "outcome_refs", "ledger_ref", "response_ref"}}
    result["request"] = _strict(_reference(payload["request_artifact"], store))
    require(isinstance(payload["outcome_refs"], list) and len(payload["outcome_refs"]) <= 64,
            "INVALID_OUTCOME_COUNT")
    result["outcomes"] = [_chunks(ref, store, budget, 8 * 1024 * 1024) for ref in payload["outcome_refs"]]
    require(len(canonical(result["outcomes"])) <= 8 * 1024 * 1024, "R2_OUTCOMES_LIMIT_EXCEEDED")
    result["ledger"] = _chunks(payload["ledger_ref"], store, budget)
    if "response_ref" in payload:
        require(payload["phase"] in {"CLOSED", "RECOVERED_CLOSED"}, "UNPUBLISHED_PHASE_HAS_RESPONSE")
        result["response"] = _chunks(payload["response_ref"], store, budget, MAX_RESPONSE_BYTES)
    elif payload["phase"] in {"CLOSED", "RECOVERED_CLOSED"}:
        raise ViewError("CLOSED_SNAPSHOT_WITHOUT_RESPONSE")
    if "unpublished_response_ref" in payload:
        # Verify but do not expose this candidate as a published RC01.
        _chunks(payload["unpublished_response_ref"], store, budget)
    records = result["artifact_records"]
    require(isinstance(records, dict), "INVALID_ARTIFACT_RECORDS")
    for identifier, record in records.items():
        budget.check()
        raw = _reference(record["stored_ref"], store)
        require(identifier == record["metadata"]["id"] and sha(raw) == record["metadata"]["sha256"],
                "ARTIFACT_METADATA_BINDING_MISMATCH")
    policy.validate_request(result["request"], lambda identifier: _reference(records[identifier]["stored_ref"], store))
    require({a["id"]: a for a in result["request"]["artifacts"]}
            == {identifier: item["metadata"] for identifier, item in records.items()}, "REQUEST_ARTIFACT_BINDING_MISMATCH")
    return result


def verify_response(snapshot):
    response = snapshot.get("response")
    if response is None:
        return
    require(response.get("format") == "genius-product-response/0.1.0", "UNSUPPORTED_RESPONSE_VERSION")
    require(response.get("versions") == policy.SUPPORTED_VERSIONS, "UNSUPPORTED_CONTRACT_VERSIONS")
    expected_received = [{**item["metadata"], "path": item["stored_ref"]["path"], "size": item["stored_ref"]["size"]}
                         for item in snapshot["artifact_records"].values()]
    received = response["artifacts"]["received"]
    require(isinstance(received, list) and len(received) == len(expected_received)
            and {item["id"]: item for item in received} == {item["id"]: item for item in expected_received},
            "RESPONSE_ARTIFACT_BINDING_MISMATCH")
    # Reuse the received public R2 response policy solely for consistency of
    # persisted receipts. No operation/FDQ execution or new scientific claim.
    reconstructed = policy.build_response(snapshot["request"], snapshot["outcomes"], {
        "execution": snapshot["execution"], "ledger": snapshot["ledger"],
        "artifacts": {"received": received, "expected": [
            {"id": item["id"], "state": "RECEIVED", "sha256": item["sha256"], "ref": item["id"]}
            for item in received]},
        "request_ref": {"revision": snapshot["request"]["revision"], "sha256": snapshot["request_artifact"]["sha256"]},
        "versions": policy.SUPPORTED_VERSIONS, "budget_used": snapshot["budget_used"],
        "closure_reason": snapshot.get("closure_reason"),
    })
    require(reconstructed == response, "RESPONSE_RECEIPT_CONSISTENCY_MISMATCH")


def read_case(case_dir, revision=None, *, budget=None):
    budget = budget or Budget()
    root = safe_path(case_dir, directory=True)
    before = inventory(root, budget)
    require((root / "HEAD").is_file(), "EXISTING_HEAD_REQUIRED")
    store = Store(root)  # All directories exist; read-only API calls below.
    first_head = store.head()
    # R2's general Store parser permits JSON floats. Consumer contract does
    # not: validate every revision, including orphan/historical payloads,
    # before any presentation (binary input artifacts remain opaque bytes).
    for name in before:
        if name.startswith("revisions/"):
            budget.check()
            revision_envelope = _strict(read_regular(root / name, 8 * 1024 * 1024))
            admit_historical_objects(revision_envelope.get("payload"), store, budget)
    chain = store.load_chain()
    require(bool(chain), "EMPTY_CASE")
    if revision is None:
        chosen = chain[-1]
    else:
        require(type(revision) is int and 1 <= revision <= len(chain), "COMMITTED_REVISION_NOT_FOUND")
        chosen = chain[revision - 1]
    snapshot = decode_snapshot(chosen["payload"], store, budget)
    verify_response(snapshot)
    committed = {entry["sha256"] for entry in chain}
    orphan_digests = sorted(name.split("/")[1] for name in before
                            if name.startswith("revisions/") and name.split("/")[1] not in committed)
    orphans = []
    for digest in orphan_digests:
        budget.check()
        raw = read_regular(root / "revisions" / digest, 8 * 1024 * 1024)
        require(sha(raw) == digest, "ORPHAN_DIGEST_MISMATCH")
        orphans.append({**_strict(raw), "sha256": digest})
    object_inventory = []
    for name, record in sorted(before.items()):
        if name.startswith("objects/"):
            object_inventory.append({"sha256": name.split("/")[1], "size": record[0],
                                     "witness": "witnesses/" + name.split("/")[1] + ".txt"})
    require(store.head() == first_head and inventory(root, budget) == before, "CASE_CHANGED_DURING_READ")
    source = {"format": "genius-consumer-source/0.1.0", "head": first_head,
              "selected_revision": chosen["revision"], "selected_revision_sha256": chosen["sha256"],
              "revisions": chain, "uncommitted_revisions": orphans,
              "temporary_files": sorted(name[4:] for name in before if name.startswith("tmp/")),
              "objects": object_inventory, "selected_snapshot": snapshot,
              "verification": "BYTE_IDENTITY_AND_R2_RECEIPT_CONSISTENCY_ONLY",
              "limits": "No producer authentication, empirical validation, comprehension study or authorization to intervene."}
    return {"source": source, "response": snapshot.get("response"),
            "publication_state": "PUBLISHED" if "response" in snapshot else "NOT_PUBLISHED",
            "store": store, "budget": budget}
