#!/usr/bin/env python3
"""Reproduce four explicitly synthetic request snapshots; never execute them."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "beta"))
sys.path.insert(0, str(ROOT / "beta/tests"))
from test_adapter import fdq, hours  # shared, tested fixture construction


def canonical(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    destination = ROOT / "beta/examples"
    destination.mkdir(parents=True, exist_ok=True)
    known = hours()
    unknown = deepcopy(known)
    unknown["assignments"][0]["credit"] = None
    payloads = {"hours-known": known, "hours-unknown": unknown,
                "fdq-frontier": fdq("frontier", "none"),
                "fdq-selector": fdq("selector", "historical")}
    sources = {"fdq-frontier": "none", "fdq-selector": "historical"}
    rows = []
    for name, payload in payloads.items():
        payload["evidence_origin"] = "synthetic"
        raw = canonical(payload)
        (destination / (name + ".json")).write_bytes(raw)
        row = {"example": name, "payload_sha256": sha(raw), "evidence_kind": "SYNTHETIC_STIPULATION",
               "not_empirical_evidence": True, "source": "beta/tests/test_adapter.py:hours", "source_files": [],
               "transformation": "Explicit illustrative values; no participant or measured observation."}
        if name in sources:
            base = ROOT / "product_local/examples/fdq" / sources[name]
            row["source"] = str(base.relative_to(ROOT))
            row["source_files"] = [{"path": str((base / path).relative_to(ROOT)), "sha256": sha((base / path).read_bytes())}
                                   for path in ("input.json", "original_result.json", "certificate.json")]
            row["transformation"] = "Input/Result exact UTF-8 bytes copied. Certificate explicitly restricted to the requested query and claim using beta/tests/test_adapter.py:fdq; family, witness, target and original byte digests unchanged. This construction is the submitted example, not a repair performed by the runtime adapter."
        rows.append(row)
    # Authored fixed expectations, not generated from engine answers.
    expected = {"format": "genius-beta-example-expectations/0.1.0", "basis": "Received rules and fixed source certificate claims; runtime does not read this file.",
                "not_empirical_evidence": True, "examples": {
                    "hours-known": {"decision": "PR_JUSTIFIED_RESULT", "evidence": "EV_CONDITIONAL", "values": {"assigned": "14/1", "excess": "0/1", "deficit": "1/1"}},
                    "hours-unknown": {"values_state": "PV_UNKNOWN", "unknown_is_not_zero": True, "obligation_open": True},
                    "fdq-frontier": {"decision": "PR_SET_OR_INCOMPARABLE", "evidence": "EV_CONDITIONAL", "value": {"frontier": ["p", "s"]}, "selected_policy": None},
                    "fdq-selector": {"decision": "PR_JUSTIFIED_RESULT", "evidence": "EV_CONDITIONAL", "value": {"selector": {"state": "DEFINED", "value": "p"}}, "selection_rule": {"mode": "unique"}}
                }}
    (destination / "EXPECTED.json").write_bytes(canonical(expected))
    provenance = {"format": "genius-beta-example-provenance/0.1.0", "generator": "beta/tools/generate_examples.py",
                  "source_provenance": "product_local/examples/fdq/PROVENANCE.json", "examples": rows}
    (destination / "PROVENANCE.json").write_bytes(canonical(provenance))
    print("Generated 4 synthetic request snapshots, separate EXPECTED.json and PROVENANCE.json.")


if __name__ == "__main__":
    main()
