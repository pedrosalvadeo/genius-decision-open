"""Lossless packing of evaluation envelopes for transport and storage.

Each native run carries its Result both as an object and as its exact
canonical text, and the envelope repeats the robust run at its top level.
Packing keeps only the text and the run, and records what it left out;
unpacking restores the identical envelope. Nothing is dropped unless it is
equal to what unpacking rebuilds, so consumers never see a different value.
"""
from __future__ import annotations

from copy import deepcopy
import json

PACK = "genius-envelope-pack/1"


def pack(envelope):
    if type(envelope) is not dict or "_packed" in envelope:
        return envelope
    out = dict(envelope)
    runs = out.get("native_runs")
    if type(runs) is not dict:
        return envelope
    runs = {mode: dict(run) if type(run) is dict else run for mode, run in runs.items()}
    dropped = []
    for mode, run in sorted(runs.items()):
        if type(run) is dict and type(run.get("native_result_json")) is str and "native_result" in run \
                and json.loads(run["native_result_json"]) == run["native_result"]:
            del run["native_result"]
            dropped.append(mode)
    out["native_runs"] = runs
    top = []
    robust = envelope["native_runs"].get("robust")
    if "robust" in dropped:
        if "native_result" in out and out["native_result"] == robust["native_result"]:
            del out["native_result"]
            top.append("native_result")
        if "native_input_json" in out and out["native_input_json"] == robust.get("native_input_json"):
            del out["native_input_json"]
            top.append("native_input_json")
    if not dropped:
        return envelope
    out["_packed"] = {"format": PACK, "runs": dropped, "top_from_robust": top}
    return out


def unpack(envelope):
    if type(envelope) is not dict or "_packed" not in envelope:
        return envelope
    out = dict(envelope)
    packed = out.pop("_packed")
    if type(packed) is not dict or packed.get("format") != PACK:
        raise ValueError("Unknown envelope packing")
    runs = {mode: dict(run) for mode, run in out["native_runs"].items()}
    for mode in packed["runs"]:
        runs[mode]["native_result"] = json.loads(runs[mode]["native_result_json"])
    out["native_runs"] = runs
    for key in packed["top_from_robust"]:
        out[key] = deepcopy(runs["robust"][key])
    return out
