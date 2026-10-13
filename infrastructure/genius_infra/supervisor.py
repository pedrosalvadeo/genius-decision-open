"""One bounded local F4 operation; operational failures never forge Results."""
from __future__ import annotations

import base64
from dataclasses import asdict, dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import re
import selectors
import signal
import subprocess
import sys
import time

from .worker import validate_identity

MIB = 1024**2
LIMIT_NAMES = {"max_nodes", "max_operations", "max_seconds", "max_input_bytes", "max_integer_digits"}
METHODS = {"evaluate", "verify_result", "verify_certificate"}
TRANSPORT_LIMITS = {"max_frame_bytes": "16777216", "max_input_bytes": "2097152",
                    "max_candidate_bytes": "8388608", "max_response_bytes": "33554432",
                    "max_batch_items": "16", "max_limit_digits": "12"}
IDENTITIES = {"protocol_version": "genius-protocols/1.0",
              "protocols_version": "GENIUS-PROTOCOLS-1.0.0",
              "kernel_version": "GENIUS-KERNEL-1.0.1", "specification": "GENIUS-SPEC-1.0.0",
              "theory_snapshot": "GENIUS-THEORY-2026-09-23-S2", "profile": "FP1_FINITE_EXACT",
              "input_format": "genius-fp1/1.0", "result_format": "genius-fp1-result/1.0"}


@dataclass(frozen=True)
class SupervisorLimits:
    cpu_seconds: int
    address_space_bytes: int
    wall_seconds: float
    max_stdout_bytes: int
    max_stderr_bytes: int

    def validate(self):
        for name, low, high in (("cpu_seconds", 1, 3600),
                                ("address_space_bytes", 64*MIB, 8*1024*MIB),
                                ("max_stdout_bytes", 1, 48*MIB),
                                ("max_stderr_bytes", 1, MIB)):
            value = getattr(self, name)
            if type(value) is not int or not low <= value <= high:
                raise ValueError("Unsupported " + name)
        if (type(self.wall_seconds) not in (int, float) or
                not math.isfinite(self.wall_seconds) or not 0 < self.wall_seconds <= 3600):
            raise ValueError("Unsupported wall_seconds")


@dataclass
class Captured:
    reason: str
    stdout: bytes
    stderr: bytes
    returncode: int | None
    wall_seconds: float
    worker_pid: int | None
    events: list
    stdout_observed: int
    stderr_observed: int


@dataclass
class Outcome:
    status: str
    reason: str
    artifacts: dict[str, bytes]
    metadata: dict


def _json(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode("utf-8")


def _strict(raw):
    def pairs(items):
        out = {}
        for key, value in items:
            if key in out:
                raise ValueError("Duplicate member")
            out[key] = value
        return out
    def number(token):
        if len(token) > 16:
            raise ValueError("Oversized control number")
        return int(token)
    def reject(_):
        raise ValueError("Unsupported control number")
    value = json.loads(raw.decode("utf-8"), object_pairs_hook=pairs,
                       parse_int=number, parse_float=reject, parse_constant=reject)
    pending = [value]
    while pending:
        item = pending.pop()
        if type(item) is str and any(0xD800 <= ord(c) <= 0xDFFF for c in item):
            raise ValueError("Surrogate")
        if type(item) is dict:
            pending.extend(item)
            pending.extend(item.values())
        elif type(item) is list:
            pending.extend(item)
    return value


def _validate_initialization(raw):
    response = _strict(raw)
    if (type(response) is not dict or set(response) != {"jsonrpc", "id", "result"} or
            response["jsonrpc"] != "2.0" or response["id"] != "f5-init"):
        raise ValueError("Initialization envelope")
    result = response["result"]
    extras = {"capabilities", "transport_limits", "default_kernel_limits", "allowed_kernel_limits",
              "environment", "cancellation"}
    if type(result) is not dict or set(result) != set(IDENTITIES) | extras:
        raise ValueError("Initialization keys")
    if any(result.get(key) != value for key, value in IDENTITIES.items()):
        raise ValueError("Incompatible component identity")
    if (type(result["capabilities"]) is not list or sorted(result["capabilities"]) != sorted(METHODS) or
            result["transport_limits"] != TRANSPORT_LIMITS or result["default_kernel_limits"] != {} or
            type(result["allowed_kernel_limits"]) is not list or sorted(result["allowed_kernel_limits"]) != sorted(LIMIT_NAMES) or
            result["cancellation"] != "PROCESS_TERMINATION_ONLY"):
        raise ValueError("Incompatible capability")
    env = result["environment"]
    if (type(env) is not dict or set(env) != {"python_recursion_depth"} or
            type(env["python_recursion_depth"]) is not str or
            not re.fullmatch(r"[1-9][0-9]*", env["python_recursion_depth"])):
        raise ValueError("Invalid runtime environment")
    return result


def _envelope(raw):
    return {"encoding": "base64", "data": base64.b64encode(raw).decode("ascii"),
            "sha256": hashlib.sha256(raw).hexdigest()}


def _decode(envelope, maximum):
    if (type(envelope) is not dict or set(envelope) != {"encoding", "data", "sha256"} or
            envelope["encoding"] != "base64" or type(envelope["data"]) is not str or
            type(envelope["sha256"]) is not str or
            not re.fullmatch(r"[0-9a-f]{64}", envelope["sha256"]) or
            len(envelope["data"]) > 4*((maximum+2)//3)):
        raise ValueError("Invalid byte envelope")
    raw = base64.b64decode(envelope["data"], validate=True)
    if (len(raw) > maximum or base64.b64encode(raw).decode("ascii") != envelope["data"] or
            hashlib.sha256(raw).hexdigest() != envelope["sha256"]):
        raise ValueError("Invalid envelope digest")
    return raw


def _worker_command(limits, *, lab_single_uid_root=False):
    return [sys.executable, "-I", "-S", "-B", str(Path(__file__).with_name("worker.py").resolve()),
            str(limits.cpu_seconds), str(limits.address_space_bytes), str(os.getpid())] + (
                ["--lab-single-uid-root"] if lab_single_uid_root else [])


def _validate_result_shape(obj):
    """Closed outer grammar from Specification06, not mathematical verification.

    Full nested correctness remains the unchanged Kernel verifier's job.
    """
    def ids(value):
        return (type(value) is list and all(type(v) is str and bool(v) for v in value) and
                len(value) == len(set(value)))
    def nat(value):
        return type(value) is str and re.fullmatch(r"0|[1-9][0-9]*", value) is not None
    def cell(value):
        if type(value) is not dict:
            return False
        if value.get("state") == "DEFINED":
            return set(value) == {"state", "value", "checks"} and ids(value["checks"])
        if value.get("state") == "OUTSIDE_DOMAIN":
            return (set(value) == {"state", "reasons", "checks"} and ids(value["reasons"]) and
                    bool(value["reasons"]) and ids(value["checks"]))
        if value.get("state") == "BLOCKED":
            return set(value) == {"state", "reasons"} and ids(value["reasons"]) and bool(value["reasons"])
        return False
    if (type(obj) is not dict or set(obj) != {"format", "input_digest", "specification", "execution",
            "presentation", "diagnostics", "checks", "policies", "decision", "integration"} or
            obj["format"] != "genius-fp1-result/1.0" or obj["specification"] != "GENIUS-SPEC-1.0.0" or
            obj["presentation"] not in ("VALID", "INVALID", "UNRESOLVED")):
        raise ValueError("Result outer grammar")
    execution = obj["execution"]
    if (type(execution) is not dict or set(execution) != {"status", "limits", "progress"} or
            execution["status"] not in ("COMPLETE", "LIMITED", "ERROR") or type(execution["limits"]) is not list):
        raise ValueError("Result execution grammar")
    names = []
    for bound in execution["limits"]:
        if (type(bound) is not dict or set(bound) != {"name", "bound"} or
                type(bound["name"]) is not str or not nat(bound["bound"])):
            raise ValueError("Result limits grammar")
        names.append(bound["name"])
    progress = execution["progress"]
    if (len(names) != len(set(names)) or type(progress) is not dict or
            set(progress) != {"completed_policies", "expanded_nodes"} or
            not ids(progress["completed_policies"]) or not nat(progress["expanded_nodes"])):
        raise ValueError("Result progress grammar")
    shapes = {"diagnostics": {"id", "code", "component", "policies", "queries", "points", "input_refs", "message"},
              "checks": {"id", "rule", "outcome", "policies", "queries", "points", "support", "detail"},
              "policies": {"policy", "causal", "functional", "composition", "resources", "generative", "welfare",
                           "evidence", "probability", "hard"}}
    for field, keys in shapes.items():
        if type(obj[field]) is not list or any(type(item) is not dict or set(item) != keys for item in obj[field]):
            raise ValueError("Result record grammar")
    if not cell(obj["decision"]) or not cell(obj["integration"]):
        raise ValueError("Result cell grammar")
    if obj["presentation"] == "INVALID" and (obj["policies"] or
            obj["decision"]["state"] != "BLOCKED" or obj["integration"]["state"] != "BLOCKED"):
        raise ValueError("Result invalid presentation contract")
    if execution["status"] != "COMPLETE" and obj["integration"]["state"] == "DEFINED":
        raise ValueError("Result interrupted integration contract")


def _run_process(command, *, request_bytes, limits, cancel_event=None):
    """Private trusted-peer test hook; no command is accepted by run_worker."""
    limits.validate()
    start = time.monotonic()
    events = []
    out, err = bytearray(), bytearray()
    observed = {"stdout": 0, "stderr": 0}
    def event(name, **fields):
        events.append({"event": name, "elapsed_seconds": time.monotonic()-start, **fields})
    proc = None
    sel = selectors.DefaultSelector()
    reason = "OK"
    handshake = False
    request_sent = False
    pending = memoryview(_json({"jsonrpc": "2.0", "id": "f5-init", "method": "genius.initialize",
                               "params": {"protocol_versions": ["genius-protocols/1.0"],
                                          "required_capabilities": sorted(METHODS)}}) + b"\n")
    try:
        proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, bufsize=0, close_fds=True, start_new_session=True,
                                cwd="/", env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8"})
        event("worker_started", pid=proc.pid)
        for stream, kind, mask in ((proc.stdin, "stdin", selectors.EVENT_WRITE),
                                   (proc.stdout, "stdout", selectors.EVENT_READ),
                                   (proc.stderr, "stderr", selectors.EVENT_READ)):
            os.set_blocking(stream.fileno(), False)
            sel.register(stream, mask, kind)
        while sel.get_map() or proc.poll() is None:
            if cancel_event is not None and cancel_event.is_set():
                reason = "CANCELLED"
                break
            if time.monotonic()-start >= limits.wall_seconds:
                reason = "WALL_LIMIT"
                break
            for key, _ in sel.select(min(0.02, max(0, limits.wall_seconds-(time.monotonic()-start)))):
                if key.data == "stdin":
                    try:
                        count = os.write(key.fd, pending[:65536])
                        pending = pending[count:]
                    except BrokenPipeError:
                        reason = "PIPE_CLOSED"
                        break
                    if not pending:
                        sel.unregister(key.fileobj)
                        if handshake:
                            request_sent = True
                            event("operation_sent")
                            key.fileobj.close()
                    continue
                raw = os.read(key.fd, 65536)
                if not raw:
                    sel.unregister(key.fileobj)
                    key.fileobj.close()
                    continue
                kind = key.data
                buffer = out if kind == "stdout" else err
                maximum = limits.max_stdout_bytes if kind == "stdout" else limits.max_stderr_bytes
                observed[kind] += len(raw)
                room = maximum-len(buffer)
                buffer.extend(raw[:room])
                if len(raw) > room:
                    reason = kind.upper()+"_LIMIT"
                    break
                if kind == "stdout" and not handshake:
                    split = out.find(b"\n")
                    if split < 0 and len(out) > 65536:
                        reason = "INITIALIZATION_LIMIT"
                        break
                    if split >= 0:
                        try:
                            _validate_initialization(bytes(out[:split]))
                            if len(out) != split+1:
                                raise ValueError("Unsolicited response")
                        except (ValueError, TypeError, RecursionError, UnicodeError):
                            reason = "INITIALIZATION_INVALID"
                            break
                        handshake = True
                        event("initialization_validated")
                        pending = memoryview(request_bytes)
                        sel.register(proc.stdin, selectors.EVENT_WRITE, "stdin")
            if reason != "OK":
                break
        if reason == "OK":
            proc.wait()
            if proc.returncode != 0:
                reason = "EXIT_NONZERO"
            elif not request_sent:
                reason = "TRANSPORT_INCOMPLETE"
    except KeyboardInterrupt:
        reason = "CANCELLED"
    except OSError:
        reason = "LAUNCH_FAILED" if proc is None else "IO_ERROR"
    finally:
        if proc is not None:
            # killpg also handles descendants retaining a pipe after leader exit.
            if reason != "OK" or proc.poll() is None:
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            proc.wait()
            for stream in (proc.stdin, proc.stdout, proc.stderr):
                stream.close()
        sel.close()
    event("worker_finished", reason=reason, returncode=None if proc is None else proc.returncode)
    return Captured(reason, bytes(out), bytes(err), None if proc is None else proc.returncode,
                    time.monotonic()-start, None if proc is None else proc.pid,
                    events, observed["stdout"], observed["stderr"])


def run_worker(method, input_bytes, candidate_bytes=None, kernel_limits=None, *, limits, cancel_event=None,
               lab_single_uid_root=False):
    """Execute an explicit method with original bytes and mandatory hard caps.

    Store admission/lock/retention and signal handlers belong to the caller.
    """
    identity = validate_identity(lab_single_uid_root=lab_single_uid_root)
    limits.validate()
    if method not in METHODS or type(input_bytes) is not bytes or len(input_bytes) > 2*MIB:
        raise ValueError("Invalid method or input size/type")
    if ((method == "evaluate" and candidate_bytes is not None) or
            (method != "evaluate" and (type(candidate_bytes) is not bytes or len(candidate_bytes) > 8*MIB))):
        raise ValueError("Invalid candidate size/type")
    if kernel_limits is not None:
        if (type(kernel_limits) is not dict or set(kernel_limits)-LIMIT_NAMES or
                any(type(v) is not str or not re.fullmatch(r"0|[1-9][0-9]{0,11}", v) for v in kernel_limits.values())):
            raise ValueError("Invalid explicit Kernel limits")
    params = {"input": _envelope(input_bytes)}
    if candidate_bytes is not None:
        params["candidate"] = _envelope(candidate_bytes)
    if kernel_limits is not None:
        params["limits"] = dict(kernel_limits)
    request = _json({"jsonrpc": "2.0", "id": "f5-job", "method": "genius."+method, "params": params}) + b"\n"
    if len(request)-1 > 16*MIB:
        raise ValueError("Request exceeds F4 frame maximum")
    captured = _run_process(_worker_command(limits, lab_single_uid_root=lab_single_uid_root),
                            request_bytes=request, limits=limits, cancel_event=cancel_event)
    artifacts = {"worker.stdout": captured.stdout, "worker.stderr": captured.stderr}
    reason = captured.reason
    response_validated = False
    result_received = False
    # F4 frames terminate only with LF. A later transport anomaly cannot
    # retroactively erase the first complete, validated operation response.
    frames = captured.stdout.split(b"\n", 2)
    trailing_bytes = len(frames[2]) if len(frames) == 3 else 0
    try:
        if len(frames) < 2:
            raise ValueError("Missing initialization")
        _validate_initialization(frames[0])
        artifacts["initialization.json"] = frames[0]+b"\n"
        if len(frames) != 3 or len(frames[1]) > 32*MIB:
            raise ValueError("Incomplete response")
        response = _strict(frames[1])
        if (type(response) is not dict or response.get("jsonrpc") != "2.0" or response.get("id") != "f5-job" or
                set(response) not in ({"jsonrpc", "id", "result"}, {"jsonrpc", "id", "error"})):
            raise ValueError("Response envelope")
        if "error" in response:
            error = response["error"]
            if (type(error) is not dict or set(error) != {"code", "message"} or
                    type(error["code"]) is not int or type(error["message"]) is not str):
                raise ValueError("RPC error")
            if reason == "OK":
                reason = "RPC_ERROR"
        elif method == "evaluate":
            result = response["result"]
            if type(result) is not dict or set(result) != {"input", "result"}:
                raise ValueError("Evaluation response")
            if _decode(result["input"], 2*MIB) != input_bytes:
                raise ValueError("Input changed")
            raw_result = _decode(result["result"], 32*MIB)
            obj = _strict(raw_result)
            _validate_result_shape(obj)
            if obj["input_digest"] != hashlib.sha256(input_bytes).hexdigest():
                raise ValueError("Result identity")
            artifacts["result.json"] = raw_result
            result_received = True
        else:
            result = response["result"]
            if (type(result) is not dict or set(result) != {"input_digest", "artifact_digest", "report"} or
                    result["input_digest"] != hashlib.sha256(input_bytes).hexdigest() or
                    result["artifact_digest"] != hashlib.sha256(candidate_bytes).hexdigest()):
                raise ValueError("Verification identity")
            report = result["report"]
            if (type(report) is not dict or set(report) != {"valid", "status", "errors"} or
                    type(report["errors"]) is not list or any(type(e) is not str for e in report["errors"]) or
                    not ((report["valid"] is True and report["status"] == "VALID") or
                         (report["valid"] is False and report["status"] == "INVALID") or
                         (report["valid"] is None and report["status"] == "INCOMPLETE"))):
                raise ValueError("Verification report")
            artifacts["report.json"] = _json(report)+b"\n"
            result_received = True
        artifacts["response.json"] = frames[1]+b"\n"
        response_validated = True
        if trailing_bytes and reason == "OK":
            reason = "UNEXPECTED_STDOUT_AFTER_RESPONSE"
    except (ValueError, TypeError, RecursionError, UnicodeError):
        if reason == "OK":
            reason = "TRANSPORT_INCOMPLETE_OR_INVALID"
    status = "DELIVERED" if reason == "OK" else "CANCELLED" if reason == "CANCELLED" else "FAILED"
    metadata = {"status": status, "reason": reason, "method": method, "response_validated": response_validated,
                "result_or_report_received": result_received, "returncode": captured.returncode,
                "signal": -captured.returncode if captured.returncode is not None and captured.returncode < 0 else None,
                "wall_seconds": captured.wall_seconds, "worker_pid": captured.worker_pid,
                "supervisor_uid": os.geteuid(), "identity": identity, "limits": asdict(limits),
                "kernel_limits": kernel_limits if kernel_limits is not None else {},
                "stdout_bytes_retained": len(captured.stdout), "stderr_bytes_retained": len(captured.stderr),
                "stdout_bytes_observed_at_least": captured.stdout_observed,
                "stderr_bytes_observed_at_least": captured.stderr_observed,
                "stdout_is_prefix": captured.stdout_observed > len(captured.stdout),
                "stderr_is_prefix": captured.stderr_observed > len(captured.stderr),
                "stdout_after_response_bytes_retained": trailing_bytes,
                "events": captured.events, "component_identities": IDENTITIES}
    return Outcome(status, reason, artifacts, metadata)
