"""Shared HTTP operations; the embedding owns authentication and host policy."""
from __future__ import annotations

import json
from flask import Blueprint, jsonify, request

from . import registry
from .service import ServiceError


def _pairs(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate key")
        value[key] = item
    return value


def _reject_number(value):
    raise ValueError("Use exact quantity strings, not floating-point JSON")


def json_body():
    if request.mimetype != "application/json":
        raise ServiceError("json_required", "Se requiere Content-Type application/json.", 415)
    try:
        raw = request.get_data(cache=False).decode("utf-8", errors="strict")
        value = json.loads(raw, object_pairs_hook=_pairs, parse_float=_reject_number, parse_constant=_reject_number)
        json.dumps(value, ensure_ascii=False).encode("utf-8", errors="strict")
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise ServiceError("invalid_json", "JSON inválido: no se admiten duplicados, floats, valores no finitos ni Unicode inválido.") from exc
    if type(value) is not dict:
        raise ServiceError("invalid_object", "El cuerpo debe ser un objeto JSON.")
    return value


def make_blueprint(service_factory, name="twin_api"):
    """Factory returns the authorized tenant service for this request.

    No authentication is supplied here. Register only under an authenticated
    host gate or the separate loopback-only app; paths contain no user selector.
    """
    bp = Blueprint(name, __name__)

    @bp.errorhandler(ServiceError)
    def service_error(exc):
        return jsonify(error={"code": exc.code, "message": exc.message, "details": exc.details}), exc.status

    @bp.get("/capabilities")
    def capabilities():
        return jsonify(service_factory().capabilities())

    @bp.get("/profiles")
    def profiles():
        return jsonify(profiles=registry.profiles())

    @bp.get("/world/contract")
    def world_contract():
        from .construction import contract
        return jsonify(contract())

    @bp.post("/cases/<cid>/world/prepare")
    def prepare_world(cid):
        return jsonify(service_factory().prepare_world(cid, json_body()))

    @bp.get("/systems/schema")
    def system_schema():
        from .systems import schema
        return jsonify(schema())

    @bp.get("/systems/scope-schema")
    def system_scope_schema():
        from .systems import scope_schema
        return jsonify(scope_schema())

    @bp.get("/systems/example")
    def system_example():
        from .systems import example
        return jsonify(example())

    @bp.get("/cases/<cid>/systems")
    def system_context(cid):
        return jsonify(service_factory().system_context(cid))

    @bp.post("/cases/<cid>/systems")
    def observe_system(cid):
        return jsonify(service_factory().observe_system(cid, json_body())), 201

    @bp.get("/interventions/schema")
    def intervention_schema():
        from .interventions import schema
        return jsonify(schema())

    @bp.get("/interventions/example")
    def intervention_example():
        from .interventions import example
        return jsonify(example())

    @bp.get("/profiles/<profile>/schema")
    def schema(profile):
        try:
            return jsonify(registry.schema(profile))
        except KeyError as exc:
            raise ServiceError("profile_not_found", "Perfil no encontrado.", 404) from exc

    @bp.get("/examples")
    def examples():
        return jsonify(examples=registry.examples())

    @bp.get("/examples/<example_id>")
    def example(example_id):
        try:
            return jsonify(registry.example(example_id))
        except KeyError as exc:
            raise ServiceError("example_not_found", "Ejemplo no encontrado.", 404) from exc

    @bp.get("/field-cases")
    def field_cases():
        return jsonify(field_cases=registry.field_cases())

    @bp.get("/field-cases/<case_id>")
    def field_case(case_id):
        try:
            return jsonify(registry.field_case(case_id))
        except KeyError as exc:
            raise ServiceError("field_case_not_found", "Caso no encontrado.", 404) from exc

    @bp.get("/federations")
    def federations():
        from . import federation
        return jsonify(federations=federation.federations())

    @bp.get("/federations/<name>")
    def federation_case(name):
        from . import federation
        try:
            return jsonify(federation.federation_case(name))
        except KeyError as exc:
            raise ServiceError("federation_not_found", "Federación no encontrada.", 404) from exc

    @bp.get("/cases")
    def cases():
        return jsonify(service_factory().list_cases())

    @bp.post("/cases")
    def create_case():
        return jsonify(service_factory().create_case(json_body())), 201

    @bp.get("/cases/<cid>")
    def read_case(cid):
        return jsonify(service_factory().read_case(cid))

    @bp.patch("/cases/<cid>/draft")
    def save_draft(cid):
        return jsonify(service_factory().save_draft(cid, json_body()))

    @bp.delete("/cases/<cid>")
    def delete_case(cid):
        return jsonify(service_factory().delete_case(cid, json_body()))

    @bp.post("/cases/<cid>/proposals")
    def propose(cid):
        return jsonify(service_factory().propose(cid, json_body())), 201

    @bp.post("/proposals/<pid>/accept")
    def accept(pid):
        return jsonify(service_factory().accept(pid, json_body()))

    @bp.post("/cases/<cid>/evaluate")
    def evaluate(cid):
        return jsonify(service_factory().evaluate(cid, json_body()))

    @bp.get("/jobs/<jid>")
    def read_job(jid):
        return jsonify(service_factory().read_job(jid))

    @bp.post("/cases/<cid>/observations")
    def observe(cid):
        return jsonify(service_factory().observe(cid, json_body())), 201

    @bp.get("/cases/<cid>/compare")
    def compare(cid):
        try:
            before, after = int(request.args["before"]), int(request.args["after"])
        except (KeyError, ValueError) as exc:
            raise ServiceError("compare_versions_required", "Indica before y after como versiones enteras.") from exc
        return jsonify(service_factory().compare(cid, before, after))

    @bp.get("/cases/<cid>/export")
    def export(cid):
        response = jsonify(service_factory().export(cid))
        response.headers["Content-Disposition"] = 'attachment; filename="genius-twin-dossier.json"'
        return response

    return bp
