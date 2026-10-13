"""Author platform tests; real F4 workers plus explicit negative peers."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "infrastructure"), str(ROOT / "kernel" / "tests")]
from genius_infra.supervisor import (SupervisorLimits, run_worker as _product_run_worker, _run_process,
                                      _json, IDENTITIES, TRANSPORT_LIMITS, METHODS, LIMIT_NAMES)
from genius_infra.worker import enter_lab_containment
from fixtures import small

EVIDENCE = None
LAB = False
CAPS = SupervisorLimits(10, 256*1024**2, 15, 34*1024**2, 65536)


def run_worker(*args, **kwargs):
    return _product_run_worker(*args, **kwargs, lab_single_uid_root=LAB)


def record(label, outcome):
    if EVIDENCE is not None:
        dest = EVIDENCE / label
        dest.mkdir()
        for name, raw in outcome.artifacts.items():
            (dest / name).write_bytes(raw)
        (dest / "outcome.json").write_text(json.dumps(outcome.metadata, indent=2)+"\n")


def input_bytes():
    obj = small()
    obj["assumptions"][0]["statement"] = "Synthetic: á, >2^53 is still exact, no empirical assertion."
    return b"\r\n" + json.dumps(obj, ensure_ascii=False, indent=2).encode() + b"\n"


def handshake():
    return {"jsonrpc": "2.0", "id": "f5-init", "result": {
        **IDENTITIES, "capabilities": sorted(METHODS), "transport_limits": TRANSPORT_LIMITS,
        "default_kernel_limits": {}, "allowed_kernel_limits": sorted(LIMIT_NAMES),
        "environment": {"python_recursion_depth": "1000"}, "cancellation": "PROCESS_TERMINATION_ONLY"}}


class PlatformTests(unittest.TestCase):
    def test_normal_profile_still_rejects_root(self):
        if os.geteuid() == 0:
            with self.assertRaises(PermissionError):
                _product_run_worker("evaluate", input_bytes(), limits=CAPS)
    def test_real_evaluate_and_verify(self):
        raw = input_bytes()
        result = run_worker("evaluate", raw, limits=CAPS)
        record("real_evaluate", result)
        self.assertEqual(result.status, "DELIVERED", result.metadata)
        obj = json.loads(result.artifacts["result.json"])
        self.assertEqual(obj["execution"]["status"], "COMPLETE")
        self.assertEqual(obj["input_digest"], hashlib.sha256(raw).hexdigest())
        wire = json.loads(result.artifacts["response.json"])["result"]
        self.assertEqual(base64.b64decode(wire["input"]["data"]), raw)
        self.assertEqual(base64.b64decode(wire["result"]["data"]), result.artifacts["result.json"])
        verification = run_worker("verify_result", raw, result.artifacts["result.json"], limits=CAPS)
        record("real_verify", verification)
        self.assertEqual(verification.status, "DELIVERED", verification.metadata)
        self.assertEqual(json.loads(verification.artifacts["report.json"])["status"], "VALID")
        events = [e["event"] for e in result.metadata["events"]]
        self.assertLess(events.index("initialization_validated"), events.index("operation_sent"))

    def test_kernel_limited_is_delivered(self):
        result = run_worker("evaluate", input_bytes(), kernel_limits={"max_nodes": "0"}, limits=CAPS)
        record("kernel_limited", result)
        self.assertEqual(result.status, "DELIVERED", result.metadata)
        self.assertEqual(json.loads(result.artifacts["result.json"])["execution"]["status"], "LIMITED")

    def test_invalid_input_is_kernel_result(self):
        result = run_worker("evaluate", b"{invalid\xff}", limits=CAPS)
        record("invalid_input", result)
        self.assertEqual(result.status, "DELIVERED", result.metadata)
        self.assertEqual(json.loads(result.artifacts["result.json"])["presentation"], "INVALID")

    def test_invalid_candidate_is_report(self):
        result = run_worker("verify_certificate", input_bytes(), b'{"x":0,"x":0}', limits=CAPS)
        record("invalid_candidate", result)
        self.assertEqual(result.status, "DELIVERED", result.metadata)
        report = json.loads(result.artifacts["report.json"])
        self.assertEqual(report, {"valid": False, "status": "INVALID", "errors": ["CANDIDATE_SYNTAX"]})

    def test_cancel_before_send(self):
        cancel = threading.Event()
        cancel.set()
        result = run_worker("evaluate", input_bytes(), limits=CAPS, cancel_event=cancel)
        record("cancelled", result)
        self.assertEqual(result.status, "CANCELLED")
        self.assertNotIn("result.json", result.artifacts)
        self.assertFalse(any(e["event"] == "operation_sent" for e in result.metadata["events"]))

    def test_explicit_caps_and_invalid_limit_map(self):
        for changes in ({"cpu_seconds": True}, {"address_space_bytes": 1}, {"wall_seconds": float("nan")},
                        {"max_stdout_bytes": 0}, {"max_stderr_bytes": 0}):
            with self.assertRaises(ValueError):
                SupervisorLimits(**(vars(CAPS) | changes)).validate()
        for limit in ({"max_nodes": 0}, {"max_nodes": "00"}, {"extra": "1"}, {"max_nodes": "1"*13}):
            with self.assertRaises(ValueError):
                run_worker("evaluate", input_bytes(), kernel_limits=limit, limits=CAPS)

    def test_incompatible_peer_gets_no_instance(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp)
            bad = handshake()
            bad["result"]["kernel_version"] = "OTHER"
            peer = p / "peer.py"
            peer.write_text("import sys\nsys.stdin.buffer.readline()\nsys.stdout.buffer.write("+
                            repr(_json(bad)+b"\n")+");sys.stdout.buffer.flush()\n"+
                            "open("+repr(str(p/"sentinel"))+",'wb').write(sys.stdin.buffer.read())\n")
            result = _run_process([sys.executable, "-I", "-S", "-B", str(peer)],
                                  request_bytes=b"SYNTHETIC_INPUT_MUST_NOT_BE_SENT\n", limits=CAPS)
            self.assertEqual(result.reason, "INITIALIZATION_INVALID")
            self.assertFalse(any(e["event"] == "operation_sent" for e in result.events))
            if (p/"sentinel").exists():
                self.assertEqual((p/"sentinel").read_bytes(), b"")


def main():
    global EVIDENCE, LAB
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--laboratory-root", action="store_true")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output/"invocation.json").write_text(json.dumps({"argv": sys.argv,
        "source_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (Path(__file__), ROOT/"infrastructure/genius_infra/supervisor.py",
                      ROOT/"infrastructure/genius_infra/worker.py")}}, indent=2)+"\n")
    if args.laboratory_root:
        identity = enter_lab_containment()
        LAB = True
        (args.output/"identity.json").write_text(json.dumps(identity, indent=2)+"\n")
    if os.geteuid() == 0 and not LAB:
        # Preparation remains root; product/testing execution is unprivileged.
        with tempfile.TemporaryDirectory(prefix="genius-f5-platform-") as temp:
            dest = Path(temp)
            dest.chmod(0o755)
            for rel in ("infrastructure/genius_infra", "kernel/genius_kernel", "protocols/genius_protocols"):
                shutil.copytree(ROOT/rel, dest/rel, ignore=shutil.ignore_patterns("__pycache__"))
            (dest/"kernel/tests").mkdir()
            shutil.copy2(ROOT/"kernel/tests/fixtures.py", dest/"kernel/tests/fixtures.py")
            (dest/"infrastructure/tests").mkdir()
            target = dest/"infrastructure/tests/test_platform.py"
            shutil.copy2(__file__, target)
            output = dest/"evidence"
            output.mkdir(mode=0o700)
            os.chown(output, 65534, 65534)
            command = [sys.executable, "-I", "-S", "-B", str(target), "--output", str(output)]
            proc = subprocess.run(command, user=65534, group=65534, extra_groups=[],
                                  capture_output=True, timeout=90, env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"})
            for item in output.iterdir():
                if item.is_dir():
                    shutil.copytree(item, args.output/item.name)
                else:
                    shutil.copy2(item, args.output/item.name)
            (args.output/"stdout.log").write_bytes(proc.stdout)
            (args.output/"stderr.log").write_bytes(proc.stderr)
            (args.output/"command.json").write_text(json.dumps({"argv": command, "uid": 65534, "gid": 65534,
                                                               "extra_groups": [], "returncode": proc.returncode}, indent=2)+"\n")
            print(proc.stderr.decode())
            return proc.returncode
    EVIDENCE = args.output
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(PlatformTests))
    (EVIDENCE/"summary.json").write_text(json.dumps({"tests": result.testsRun, "failures": len(result.failures),
                                                   "errors": len(result.errors), "uid": os.geteuid(), "laboratory_root": LAB,
                                                   "result": "PASS" if result.wasSuccessful() else "FAIL"}, indent=2)+"\n")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
