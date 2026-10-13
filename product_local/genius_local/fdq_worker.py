"""Isolated adapter for received R1 FDQ; never edits the received verifier.

The parent owns process deadlines and records stdout/exit independently. This
worker emits a receipt only after calling the pinned R1 verifier. Dependency
paths are explicit; no installed Kernel or implicit network source is used.
"""
from __future__ import annotations
import argparse
import base64
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import resource

PINS = {
    "verify_fdq.py": "9d464705ee0b96cccc87ee4d22be88d40b5003c5bdf9a3c236c71c98b1e98b70",
    "fdq_oracle.py": "5323be701e9fdc622b9a8c3ac4821989ded154c16b02415465d32b827c3bf856",
    "genius_kernel/__init__.py": "1ff2fdf6daf9fcf8bf1c30e6de069491c3c47a78cf7bd75f07910aac8f69a878",
    "genius_kernel/__main__.py": "ef348b46bfde4ec216212bd29eebb3d4d537231268a0d571dce0c543a174ad08",
    "genius_kernel/causal.py": "88cc36a0761968b54c172d70559dc5261a3439b1699d8dafaea5ad9e82ee81e8",
    "genius_kernel/common.py": "4e795fa5079cbb219a98916d1f5d9a0f8de30302074de0d8b51fe4a9cab11665",
    "genius_kernel/decision.py": "4fde6a4e2362d32a87244f8e5906423b98dbce6b3be77d6a350d30349c541a54",
    "genius_kernel/engine.py": "3b751c32be6e5786c742407de48fce769a3db002357e6b8a787941c9382a40da",
    "genius_kernel/evidence.py": "5c3875e59a12325f84aa388c45f7a7f919f61f68ec0198d292d4d4f3296c6614",
    "genius_kernel/output_schema.py": "f0acd1df097caee6c5da0d5ff1a5d982524bed0fefc4116af0b78b2b3e5134a0",
    "genius_kernel/schema.py": "29dd96a04892593a08f03f301177516b6e01e9f9cee157f307a059e74ac9c2d3",
    "genius_kernel/structural.py": "7b59e9230252839a4d4762ae3844e095665434f74ae11a06e2b7659dde941e3b",
    "genius_kernel/verifier.py": "a283c00ceb9f7774a8b9300fb90ac8e4f07d26d16fee59fd0fdf751ec3d419e2",
}
MAX_PAYLOAD = 48 * 1024 * 1024


def strict_json(raw):
    def pairs(items):
        out = {}
        for k, v in items:
            if k in out:
                raise ValueError("DUPLICATE_JSON_KEY")
            out[k] = v
        return out
    def reject_constant(value):
        raise ValueError("NONFINITE_JSON_VALUE")
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=reject_constant)


def check_dependencies(r1, r0):
    roots = (Path(r1) / "research", Path(r0) / "sources/repo/kernel")
    kernel_names = {"genius_kernel/" + p.name for p in (roots[1] / "genius_kernel").glob("*.py")}
    if kernel_names != {k for k in PINS if k.startswith("genius_kernel/")}:
        raise ValueError("DEPENDENCY_MODULE_SET_CHANGED")
    sources = {}
    for name, expected in PINS.items():
        root = roots[1] if name.startswith("genius_kernel/") else roots[0]
        raw = (root / name).read_bytes()
        if hashlib.sha256(raw).hexdigest() != expected:
            raise ValueError("DEPENDENCY_DIGEST_MISMATCH:" + name)
        sources[name] = raw
    return sources


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--r1", required=True, type=Path)
    parser.add_argument("--baseline", required=True, type=Path)
    args = parser.parse_args()
    try:
        # Linux local profile: bounded virtual address space, inherited by all
        # Python allocations during the unchanged verifier execution.
        resource.setrlimit(resource.RLIMIT_AS, (1024 ** 3, 1024 ** 3))
        raw = sys.stdin.buffer.read(MAX_PAYLOAD + 1)
        if len(raw) > MAX_PAYLOAD:
            raise ValueError("WORKER_INPUT_TOO_LARGE")
        payload = strict_json(raw)
        if type(payload) is not dict or set(payload) != {"input_b64", "result_b64", "certificate_b64"}:
            raise ValueError("WORKER_PAYLOAD_FIELDS")
        decoded = {k: base64.b64decode(v, validate=True) for k, v in payload.items()}
        for v in decoded.values():
            if len(v) > 8 * 1024 * 1024:
                raise ValueError("ARTIFACT_TOO_LARGE")
            strict_json(v)
        sources = check_dependencies(args.r1, args.baseline)
        # Import only the exact bytes just checked, from a private clean tree.
        # Adding the received roots to sys.path would also trust unpinned
        # siblings (for example a fractions.py shadowing the standard library).
        sys.dont_write_bytecode = True
        with tempfile.TemporaryDirectory(prefix="genius-fdq-pinned-") as directory:
            clean = Path(directory)
            for name, raw_source in sources.items():
                path = clean / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw_source)
            sys.pycache_prefix = str(clean / "private-cache")
            sys.path.insert(0, str(clean))
            from verify_fdq import verify
            from genius_kernel.engine import evaluate
            from genius_kernel.verifier import verify_result
            result = verify(decoded["input_b64"], decoded["result_b64"],
                            strict_json(decoded["certificate_b64"]), evaluate, verify_result)
            sys.path.remove(str(clean))
        print(json.dumps({"worker_format": "genius-fdq-worker/0.1.0",
                          "dependencies": PINS, "verification": result},
                         ensure_ascii=False, separators=(",", ":")))
        return 0
    except Exception as exc:
        # Adapter failure is not an FP1 Result and not a negative theorem.
        print(json.dumps({"worker_format": "genius-fdq-worker/0.1.0",
                          "adapter_error": type(exc).__name__, "reason": str(exc)},
                         ensure_ascii=False, separators=(",", ":")))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
