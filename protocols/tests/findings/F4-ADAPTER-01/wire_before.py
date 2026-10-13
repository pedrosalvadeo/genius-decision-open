"""Closed transport types; FP1 input bytes are deliberately not parsed here."""
from __future__ import annotations

import base64
import binascii
import hashlib
import json
import re

MAX_FRAME_BYTES = 16 * 1024 * 1024
MAX_INPUT_BYTES = 2 * 1024 * 1024
MAX_CANDIDATE_BYTES = 8 * 1024 * 1024
MAX_RESPONSE_BYTES = 32 * 1024 * 1024
MAX_BATCH_ITEMS = 16
MAX_LIMIT_DIGITS = 12
MAX_SAFE_ID = 2**53 - 1
LIMIT_NAMES = frozenset({"max_nodes", "max_operations", "max_seconds",
                         "max_input_bytes", "max_integer_digits"})
ERROR_MESSAGES = {
    -32700: "Parse error", -32600: "Invalid Request",
    -32601: "Method not found", -32602: "Invalid params",
    -32603: "Internal error", -32001: "Incompatible protocol",
    -32002: "Invalid session state", -32003: "Transport limit exceeded",
}


class RPCError(Exception):
    def __init__(self, code):
        self.code = code
        super().__init__(ERROR_MESSAGES[code])


class CandidateTypeError(ValueError):
    """A JSON number cannot be a value in either candidate FP1 grammar."""


class _JSONNumber:
    """A non-integer/oversized outer token, never coerced into text or an ID.

    The Kernel disables Python's global integer-string conversion limit. Avoid
    letting that process-global setting permit expensive outer int conversion.
    Every permitted numeric field in this protocol is a safe integer RPC ID.
    """


def _outer_integer(token):
    if len(token.lstrip("-")) > 16:
        return _JSONNumber()
    return int(token)


def _reject_number(token):
    raise CandidateTypeError("CANDIDATE_TYPE")


def _reject_constant(token):
    raise ValueError("Non-JSON constant")


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key")
        result[key] = value
    return result


def _unicode_scalars(value):
    # Iterative traversal does not impose an additional Python recursion budget.
    pending = [value]
    while pending:
        item = pending.pop()
        if type(item) is str:
            if any(0xD800 <= ord(char) <= 0xDFFF for char in item):
                raise ValueError("Isolated Unicode surrogate")
        elif type(item) is list:
            pending.extend(item)
        elif type(item) is dict:
            pending.extend(item)
            pending.extend(item.values())


def strict_json(raw, *, candidate=False):
    """Parse UTF-8 JSON without duplicate keys, constants or lone surrogates.

    Candidate FP1 Nat/Q/Bit values are strings, so JSON numbers are rejected as
    types before the verifier; no arbitrary-size integer conversion is needed.
    Outer numeric tokens remain typed objects when they cannot be RPC IDs.
    """
    result = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_pairs,
                        parse_constant=_reject_constant,
                        parse_int=_reject_number if candidate else _outer_integer,
                        parse_float=_reject_number if candidate else lambda _: _JSONNumber())
    _unicode_scalars(result)
    return result


def json_bytes(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False,
                      separators=(",", ":")).encode("utf-8")


def error_response(code, request_id=None):
    return {"jsonrpc": "2.0", "id": request_id,
            "error": {"code": code, "message": ERROR_MESSAGES[code]}}


def valid_id(value):
    return (value is None or
            (type(value) is str and bool(value) and value.isascii()) or
            (type(value) is int and -MAX_SAFE_ID <= value <= MAX_SAFE_ID))


def byte_envelope(raw):
    return {"encoding": "base64", "data": base64.b64encode(raw).decode("ascii"),
            "sha256": hashlib.sha256(raw).hexdigest()}


def decode_envelope(envelope, max_bytes):
    if (type(envelope) is not dict or
            set(envelope) != {"encoding", "data", "sha256"} or
            envelope["encoding"] != "base64" or
            type(envelope["data"]) is not str or
            type(envelope["sha256"]) is not str or
            not re.fullmatch(r"[0-9a-f]{64}", envelope["sha256"], re.ASCII)):
        raise RPCError(-32602)
    encoded = envelope["data"]
    # Decode only after bounding encoded storage. Invalid overlarge data need
    # not be allocated to establish that it exceeds our transport capability.
    if len(encoded) > 4 * ((max_bytes + 2) // 3):
        raise RPCError(-32003)
    try:
        raw = base64.b64decode(encoded, validate=True)
    except (ValueError, binascii.Error):
        raise RPCError(-32602) from None
    if len(raw) > max_bytes:
        raise RPCError(-32003)
    if base64.b64encode(raw).decode("ascii") != encoded:
        raise RPCError(-32602)
    if hashlib.sha256(raw).hexdigest() != envelope["sha256"]:
        raise RPCError(-32602)
    return raw


def kernel_limits(value):
    if type(value) is not dict or set(value) - LIMIT_NAMES:
        raise RPCError(-32602)
    limits = {}
    for name, bound in value.items():
        if (type(bound) is not str or len(bound) > MAX_LIMIT_DIGITS or
                not re.fullmatch(r"0|[1-9][0-9]*", bound, re.ASCII)):
            raise RPCError(-32602)
        limits[name] = int(bound)
    return limits
