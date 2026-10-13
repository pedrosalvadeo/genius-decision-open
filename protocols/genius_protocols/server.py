"""Serial stdio session, with no remote calls or request-directed filesystem IO."""
from __future__ import annotations

import hashlib
import sys

import genius_kernel

from . import PROTOCOL_VERSION, __version__
from . import wire

CAPABILITIES = ("evaluate", "verify_result", "verify_certificate")
METHODS = frozenset({"genius.initialize", *("genius." + c for c in CAPABILITIES)})


def initialization_result():
    return {
        "protocol_version": PROTOCOL_VERSION,
        "protocols_version": "GENIUS-PROTOCOLS-" + __version__,
        "kernel_version": "GENIUS-KERNEL-" + genius_kernel.__version__,
        "specification": "GENIUS-SPEC-1.0.0",
        "theory_snapshot": "GENIUS-THEORY-2026-09-23-S2",
        "profile": "FP1_FINITE_EXACT",
        "input_format": "genius-fp1/1.0",
        "result_format": "genius-fp1-result/1.0",
        "capabilities": list(CAPABILITIES),
        "transport_limits": {
            "max_frame_bytes": str(wire.MAX_FRAME_BYTES),
            "max_input_bytes": str(wire.MAX_INPUT_BYTES),
            "max_candidate_bytes": str(wire.MAX_CANDIDATE_BYTES),
            "max_response_bytes": str(wire.MAX_RESPONSE_BYTES),
            "max_batch_items": str(wire.MAX_BATCH_ITEMS),
            "max_limit_digits": str(wire.MAX_LIMIT_DIGITS),
        },
        "default_kernel_limits": {},
        "allowed_kernel_limits": sorted(wire.LIMIT_NAMES),
        "environment": {"python_recursion_depth": str(sys.getrecursionlimit())},
        "cancellation": "PROCESS_TERMINATION_ONLY",
    }


def _string_set(value, *, nonempty=False):
    if (type(value) is not list or (nonempty and not value) or
            any(type(item) is not str or not item for item in value) or
            len(set(value)) != len(value)):
        raise wire.RPCError(-32602)


class Session:
    def __init__(self):
        self.initialized = False

    def _initialize(self, params, in_batch):
        if self.initialized or in_batch:
            raise wire.RPCError(-32002)
        if type(params) is not dict or set(params) != {"protocol_versions", "required_capabilities"}:
            raise wire.RPCError(-32602)
        _string_set(params["protocol_versions"], nonempty=True)
        _string_set(params["required_capabilities"])
        if (PROTOCOL_VERSION not in params["protocol_versions"] or
                not set(params["required_capabilities"]) <= set(CAPABILITIES)):
            raise wire.RPCError(-32001)
        result = initialization_result()
        self.initialized = True
        return result

    def _compute(self, method, params):
        if not self.initialized:
            raise wire.RPCError(-32002)
        required = {"input"} if method == "genius.evaluate" else {"input", "candidate"}
        if (type(params) is not dict or not required <= set(params) or
                set(params) - required - {"limits"}):
            raise wire.RPCError(-32602)
        limits = wire.kernel_limits(params.get("limits", {}))
        raw = wire.decode_envelope(params["input"], wire.MAX_INPUT_BYTES)
        if method == "genius.evaluate":
            result = genius_kernel.evaluate(raw, limits=limits)
            result_raw = wire.json_bytes(result) + b"\n"
            # Return the exact received envelope: its canonical representation
            # has already been checked, and no input parse/reserialization occurs.
            return {"input": params["input"], "result": wire.byte_envelope(result_raw)}
        candidate_raw = wire.decode_envelope(params["candidate"], wire.MAX_CANDIDATE_BYTES)
        try:
            candidate = wire.strict_json(candidate_raw, candidate=True)
        except wire.CandidateTypeError:
            report = {"valid": False, "status": "INVALID", "errors": ["CANDIDATE_TYPE"]}
        except (ValueError, UnicodeError, RecursionError):
            report = {"valid": False, "status": "INVALID", "errors": ["CANDIDATE_SYNTAX"]}
        else:
            verify = (genius_kernel.verify_result if method == "genius.verify_result"
                      else genius_kernel.verify_decisive_certificate)
            report = verify(raw, candidate, limits=limits)
        return {"input_digest": hashlib.sha256(raw).hexdigest(),
                "artifact_digest": hashlib.sha256(candidate_raw).hexdigest(),
                "report": report}

    def handle_request(self, request, *, in_batch=False):
        if (type(request) is not dict or
                not {"jsonrpc", "method"} <= set(request) or
                set(request) - {"jsonrpc", "method", "params", "id"} or
                request["jsonrpc"] != "2.0" or type(request["method"]) is not str or
                ("params" in request and type(request["params"]) not in (dict, list)) or
                ("id" in request and not wire.valid_id(request["id"]))):
            return wire.error_response(-32600)
        # The selected profile intentionally provides no executable notification
        # methods. Valid notifications are ignored before session or params work.
        if "id" not in request:
            return None
        request_id = request["id"]
        method, params = request["method"], request.get("params", {})
        try:
            if method not in METHODS:
                raise wire.RPCError(-32601)
            result = (self._initialize(params, in_batch) if method == "genius.initialize"
                      else self._compute(method, params))
            response = {"jsonrpc": "2.0", "id": request_id, "result": result}
            if len(wire.json_bytes(response)) > wire.MAX_RESPONSE_BYTES:
                raise wire.RPCError(-32003)
            return response
        except wire.RPCError as exc:
            return wire.error_response(exc.code, request_id)
        except Exception:
            # Adapter failure never fabricates a Kernel Result or a verdict.
            return wire.error_response(-32603, request_id)

    def handle_payload(self, payload):
        try:
            request = wire.strict_json(payload)
        except (ValueError, UnicodeError, RecursionError):
            return wire.error_response(-32700)
        if type(request) is not list:
            return self.handle_request(request)
        if not request:
            return wire.error_response(-32600)
        if len(request) > wire.MAX_BATCH_ITEMS:
            return wire.error_response(-32003)
        responses = []
        for item in request:
            response = self.handle_request(item, in_batch=True)
            if response is not None:
                responses.append(response)
        if not responses:
            return None
        if len(wire.json_bytes(responses)) > wire.MAX_RESPONSE_BYTES:
            return [wire.error_response(-32003, response["id"]) for response in responses]
        return responses


def serve(source, sink):
    """Process bounded LF frames; return 0 at clean EOF or 2 for transport loss.

    Limits count JSON payload bytes excluding LF. An accepted CR in CRLF is
    payload whitespace and counts. No incomplete EOF fragment is executed.
    """
    session = Session()
    try:
        while True:
            frame = source.readline(wire.MAX_FRAME_BYTES + 2)
            if not frame:
                return 0
            terminated = frame.endswith(b"\n")
            payload = frame[:-1] if terminated else frame
            if len(payload) > wire.MAX_FRAME_BYTES:
                sink.write(wire.json_bytes(wire.error_response(-32003)) + b"\n")
                sink.flush()
                return 2
            if not terminated:
                return 2
            response = session.handle_payload(payload)
            if response is not None:
                sink.write(wire.json_bytes(response) + b"\n")
                sink.flush()
    except (BrokenPipeError, OSError):
        return 2
