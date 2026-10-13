"""Reproduce the saved pre-repair parser against the delivered parser."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "protocols"))
from genius_protocols import wire


def classify(module, raw):
    try:
        module.strict_json(raw, candidate=True)
    except module.CandidateTypeError:
        return "CANDIDATE_TYPE"
    except (ValueError, UnicodeError, RecursionError):
        return "CANDIDATE_SYNTAX"
    return "PARSED"


spec = importlib.util.spec_from_file_location("f4_before", HERE / "wire_before.py")
before = importlib.util.module_from_spec(spec)
spec.loader.exec_module(before)
evidence = json.loads((HERE / "before_after.json").read_text())
assert hashlib.sha256((HERE / "wire_before.py").read_bytes()).hexdigest() == evidence["before_source_sha256"]
assert hashlib.sha256((HERE / evidence["after_source"]).read_bytes()).hexdigest() == evidence["after_source_sha256"]
for row in evidence["cases"]:
    raw = (HERE / row["candidate_file"]).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == row["candidate_sha256"]
    observed_before, observed_after = classify(before, raw), classify(wire, raw)
    assert observed_before == row["before"]
    assert observed_after == row["after"] == row["expected"]
    print(json.dumps({"case": row["case"], "before": observed_before,
                      "after": observed_after, "passed": True}))

