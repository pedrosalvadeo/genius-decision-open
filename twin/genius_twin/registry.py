"""Closed, versioned profile registry; no user-selected imports or execution."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path


D1 = "SEMILLERO_14D_SYNTHETIC_V1"
STOCKFLOW = "STOCK_FLOW_FINITE_V1"
PROFILES = (D1, STOCKFLOW)


def profiles():
    return [
        {"id": D1, "label": "Semillero D1", "scope": "SYNTHETIC_FIXED_TEMPLATE",
         "confirmation": "acknowledge_synthetic", "observations": True},
        {"id": STOCKFLOW, "label": "Existencias y flujos finitos", "scope": "DECLARED_FINITE_MODEL",
         "confirmation": "acknowledge_declared", "observations": False, "system_observations": True,
         "observation_scope": "Source-attributed system graphs; numerical prediction contrast/calibration not implemented"},
    ]


def validate(model):
    if type(model) is not dict or model.get("profile") not in PROFILES:
        raise ValueError("Unsupported model profile")
    if model["profile"] == D1:
        from .domain import validate_model
    else:
        from .stockflow import validate_model
    validate_model(model)


def evaluate(model):
    validate(model)
    if model["profile"] == D1:
        from .compiler import evaluate_model
    else:
        from .stockflow_compiler import evaluate_model
    return evaluate_model(deepcopy(model))


def execution_identity(profile, context=None):
    """Source identity, not a claim of deterministic runtime or empirical truth."""
    if profile not in PROFILES:
        raise ValueError("Unsupported profile")
    own = Path(__file__).resolve().parent
    import genius_kernel
    kernel = Path(genius_kernel.__file__).resolve().parent
    modules = ("domain.py", "compiler.py") if profile == D1 else ("stockflow.py", "stockflow_compiler.py")
    files = {"twin/" + name: hashlib.sha256((own / name).read_bytes()).hexdigest() for name in modules}
    files.update({"kernel/" + path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                  for path in sorted(kernel.glob("*.py"))})
    files["twin/registry.py"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    files["twin/process_runner.py"] = hashlib.sha256((own / "process_runner.py").read_bytes()).hexdigest()
    return {"format": "genius-twin-execution-identity/1", "profile": profile,
            "source_sha256": files, "execution_context": deepcopy(context or {})}


def examples():
    directory = Path(__file__).resolve().parents[1] / "examples"
    rows = [{"id": "semillero_d1", "title": "Semillero D1 — sintético", "profile": D1}]
    for path in sorted(directory.glob("stockflow_*.json")):
        model = json.loads(path.read_text(encoding="utf-8"))
        if model.get("profile") != STOCKFLOW:
            continue
        rows.append({"id": path.stem, "title": model.get("name", path.stem), "profile": STOCKFLOW})
    return rows


def example(name):
    row = next((row for row in examples() if row["id"] == name), None)
    if row is None:
        raise KeyError(name)
    if name == "semillero_d1":
        from .domain import default_model
        model = default_model()
    else:
        model = json.loads((Path(__file__).resolve().parents[1] / "examples" / (name + ".json")).read_text(encoding="utf-8"))
    return {**row, "model": model, "provenance": "SYNTHETIC_EXAMPLE_NOT_FIELD_EVIDENCE"}


def schema(profile):
    if profile == D1:
        return {"$schema": "https://json-schema.org/draft/2020-12/schema", "title": D1,
                "type": "object", "additionalProperties": False,
                "required": ["profile", "horizon", "policies", "water_budget_liters", "law", "require_all_scenarios"],
                "properties": {"profile": {"const": D1}, "horizon": {"const": 14},
                    "water_budget_liters": {"const": 18}, "require_all_scenarios": {"type": "boolean"},
                    "policies": {"enum": [["C", "R", "E"], ["C", "R", "E_prime"]]},
                    "law": {"type": "object", "additionalProperties": False, "required": ["N", "H", "HA"],
                            "properties": {key: {"type": "string"} for key in ("N", "H", "HA")}}},
                "x-semantic-validation": "Exact normalized rational law; authoritative server validator required"}
    if profile == STOCKFLOW:
        from .stockflow import model_schema
        return model_schema()
    raise KeyError(profile)
