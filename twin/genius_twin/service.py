"""D1 dossier operations: bounded proposals, immutable versions and native evaluation.

This is a new product envelope, not an R2 receipt. It never rewrites FP1 cells.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from fractions import Fraction
import json
import re
import unicodedata

from .store import Store, dumps, identifier, now, sha
from . import registry


class ServiceError(ValueError):
    def __init__(self, code, message, status=400, details=None):
        super().__init__(message)
        self.code, self.message, self.status, self.details = code, message, status, details


def require(condition, code, message, status=400, details=None):
    if not condition:
        raise ServiceError(code, message, status, details)


def fields(value, allowed, required=()):
    require(type(value) is dict, "invalid_object", "Se requiere un objeto JSON.")
    require(set(value) <= set(allowed) and set(required) <= set(value),
            "invalid_fields", "Campos desconocidos o requeridos ausentes.", details={"allowed": sorted(allowed), "required": sorted(required)})


def text(value, name="text", maximum=10000, minimum=1):
    require(type(value) is str and minimum <= len(value.strip()) <= maximum,
            "invalid_text", f"{name}: texto de {minimum} a {maximum} caracteres requerido.")
    return value.strip()


def integer(value, name, low=0, high=100000):
    require(type(value) is int and low <= value <= high, "invalid_integer", f"{name}: entero entre {low} y {high} requerido.")
    return value


def normalized(value):
    return "".join(c for c in unicodedata.normalize("NFKD", value.lower()) if not unicodedata.combining(c))


def rational(value):
    require(type(value) is str and len(value) <= 64 and re.fullmatch(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+|/[1-9][0-9]*)?", value) is not None,
            "invalid_quantity", "El valor debe ser texto decimal o racional exacto.")
    return Fraction(value)


def q(value):
    return f"{value.numerator}/{value.denominator}"


class TwinService:
    def __init__(self, store: Store, evaluator=None, execution_context=None, before_erase=None):
        self.store = store
        if evaluator is None:
            from .process_runner import ProcessEvaluator
            evaluator = ProcessEvaluator()
        self.evaluator = evaluator
        self.execution_context = {key: getattr(evaluator, key) for key in ("timeout", "memory_mb", "output_bytes") if hasattr(evaluator, key)}
        self.execution_context.update(deepcopy(execution_context or {}))
        self.before_erase = before_erase

    def _case(self, cid, conn=None):
        row = (conn.execute("SELECT * FROM cases WHERE id=?", (cid,)).fetchone() if conn else
               self.store.one("SELECT * FROM cases WHERE id=?", (cid,)))
        require(row is not None, "case_not_found", "Expediente no encontrado.", 404)
        return row

    def _version(self, cid, version, conn=None):
        integer(version, "version", 1)
        row = (conn.execute("SELECT * FROM versions WHERE case_id=? AND version=?", (cid, version)).fetchone() if conn else
               self.store.one("SELECT * FROM versions WHERE case_id=? AND version=?", (cid, version)))
        require(row is not None, "version_not_found", "Versión no encontrada.", 404)
        return Store.version(row)

    def _validate_model(self, model):
        try:
            registry.validate(model)
        except (ValueError, KeyError, TypeError) as exc:
            raise ServiceError("model_outside_profile", "Modelo fuera del perfil admitido.", details=str(exc)) from exc

    def capabilities(self):
        return {"format": "genius-twin-capabilities/0.2.0", "profile": registry.D1,
                "profiles": registry.profiles(), "examples": registry.examples(),
                "scope": "Declared finite models; calculation under assumptions, empirical validity not assessed",
                "transport": "HTTP JSON; access boundary belongs to the embedding", "mcp": self.execution_context.get('mcp', False), "external_acquisition": False,
                "physical_actions": False, "rc01_receipt": False, "default_case_versions": "start at 1 after material confirmation",
                "execution_limits": deepcopy(self.execution_context),
                "edit_operations": ["declared_model", "world_model", "intervention_design", "system_scope", "draft", "apply_relay_policy", "preference", "law_correction", "restore"],
                "world_construction": {"format": "genius-world-construction/1", "contract_path": "/world/contract",
                    "prepare_path": "/cases/{case_id}/world/prepare", "profile": registry.STOCKFLOW,
                    "interpretation_owner": "CONNECTED_AGENT_OR_HUMAN", "server_llm_calls": False,
                    "empirical_validation": "NOT_ASSESSED", "acceptance_required": True},
                "systems": {"observation_format": "genius-system-observation/1", "scope_format": "genius-system-scope/1",
                    "schema_path": "/systems/schema", "scope_schema_path": "/systems/scope-schema", "example_path": "/systems/example",
                    "recognition": "Declared graph components; hypotheses only, no causal discovery",
                    "max_observations": min(64, self.execution_context.get("system_observation_limit", 64)),
                    "empirical_validation": "NOT_ASSESSED"},
                "interventions": {"format": "genius-intervention-design/1", "profile": registry.STOCKFLOW,
                    "schema_path": "/interventions/schema", "example_path": "/interventions/example",
                    "operations": ["transfer", "connect", "disconnect", "use_action"],
                    "generation": "exhaustive declared combinations; shared base, scenarios and criteria",
                    "acceptance_required": True, "physical_actions": False},
                "observation_variables": {"water_in_tray_liters": "L", "minutes_a": "min", "minutes_b": "min"},
                "states": {"job": ["running", "completed", "failed", "interrupted"],
                           "admission": ["DRAFT_NOT_ADMITTED", "SYNTHETIC_ONLY", "DECLARED_MODEL_ONLY", "MODEL_REVIEW_REQUIRED"]}}

    def create_case(self, payload):
        fields(payload, {"text", "title", "profile"}, {"text"})
        narrative = text(payload["text"])
        title = text(payload.get("title", "Nueva decisión"), "title", 160)
        requested = payload.get("profile")
        require(requested is None or requested in registry.PROFILES, "unsupported_profile", "Perfil no admitido.", 422)
        matches = requested == registry.D1 or (requested is None and any(token in normalized(narrative) for token in ("semillero", "huerta", "plantas", "planta")))
        requested = registry.D1 if matches else registry.STOCKFLOW
        obligations = []
        if not matches:
            obligations.append({"id": "domain-model-required", "cause": "MODELO_PENDIENTE", "status": "OPEN",
                                "message": "El relato se conserva. Hace falta declarar un modelo de existencias y flujos admitido; no se infieren sus parámetros de la prosa.",
                                "next_action": "Completar un borrador y proponer el modelo estructurado para confirmar sus premisas.", "owner": "modelizacion"})
        cid, timestamp = identifier(), now()
        with self.store.transaction() as conn:
            conn.execute("INSERT INTO cases(id,title,narrative,current_version,status,created_at,updated_at,obligations_json,profile) VALUES(?,?,?,0,?,?,?,?,?)", (cid, title, narrative,
                         "proposal_pending" if matches else "needs_model", timestamp, timestamp, dumps(obligations), requested))
            conn.execute("INSERT INTO drafts VALUES(?,0,0,?,NULL,?)", (cid, narrative, timestamp))
            proposal = None
            if matches:
                from .domain import default_model
                model = default_model()
                metadata = {"synthetic": True, "interpretation_method": "bounded_domain_match_to_explicit_synthetic_template",
                            "source_narrative": narrative, "evidence_origin": "SYNTHETIC_STIPULATION",
                            "not_inferred_from_narrative": ["two plants", "two people A/B", "14-day horizon", "probability law", "water/temporal thresholds"],
                            "material_changes": ["Ejemplo sintético de dos plantas y dos personas, no reconstrucción empírica del relato.",
                                                 "14 pasos diarios, tres escenarios y ley estipulada; no estima mortalidad real.",
                                                 "La vida de las plantas se presupone; compara condición hídrica, tiempo y CAG acc.",
                                                 "Exigir ninguna violación en los escenarios declarados; cambiar esta norma es una operación explícita."],
                            "empirical_admission": "NOT_VALIDATED", "review_required": False}
                proposal = self._insert_proposal(conn, cid, 0, "initial_model", narrative, model, metadata)
        return {"case": Store.case(self._case(cid)), "proposal": proposal, "obligations": obligations,
                "draft": Store.draft(self.store.one("SELECT * FROM drafts WHERE case_id=?", (cid,)))}

    @staticmethod
    def _insert_proposal(conn, cid, base, kind, message, model, metadata):
        pid = identifier()
        conn.execute("INSERT INTO proposals VALUES(?,?,?,?,?,?,?,'proposed',NULL,?)",
                     (pid, cid, base, kind, message, dumps(model) if model is not None else None, dumps(metadata), now()))
        return Store.proposal(conn.execute("SELECT * FROM proposals WHERE id=?", (pid,)).fetchone())

    def list_cases(self):
        return {"cases": [Store.case(r) for r in self.store.read("SELECT * FROM cases ORDER BY created_at DESC,id")]}

    def read_case(self, cid):
        case = Store.case(self._case(cid))
        observations = [json.loads(r["record_json"]) for r in self.store.read("SELECT * FROM observations WHERE case_id=? ORDER BY created_at,id", (cid,))]
        systems = [o for o in observations if o.get("kind") == "system_observation"]
        return {"case": case,
                "draft": Store.draft(self.store.one("SELECT * FROM drafts WHERE case_id=?", (cid,))),
                "versions": [Store.version(r) for r in self.store.read("SELECT * FROM versions WHERE case_id=? ORDER BY version", (cid,))],
                "proposals": [Store.proposal(r) for r in self.store.read("SELECT * FROM proposals WHERE case_id=? ORDER BY created_at,id", (cid,))],
                "jobs": [Store.job(r) for r in self.store.read("SELECT * FROM jobs WHERE case_id=? ORDER BY created_at,id", (cid,))],
                "observations": [o for o in observations if o.get("kind") != "system_observation"],
                "system_observations": systems, "system_context": self.system_context(cid)}

    def _system_records(self, cid, conn=None):
        sql = "SELECT record_json FROM observations WHERE case_id=? ORDER BY created_at,id"
        rows = conn.execute(sql, (cid,)).fetchall() if conn else self.store.read(sql, (cid,))
        records = [json.loads(r["record_json"]) for r in rows]
        return sorted((r for r in records if r.get("kind") == "system_observation"), key=lambda r: r["revision"])

    def system_context(self, cid, version=None):
        case = self._case(cid)
        records = self._system_records(cid)
        latest = records[-1] if records else None
        if version is None and case["current_version"]:
            version = self._version(cid, case["current_version"])
        receipt = version["metadata"].get("system_scope") if version else None
        state = "NO_OBSERVATIONS"
        if latest:
            state = "REVIEW_REQUIRED"
            if receipt and receipt["observation_revision"] == latest["revision"] and receipt["model_sha256"] == version["model_sha256"]:
                state = "SCOPE_INCOMPLETE" if receipt["review_required"] else "CURRENT_DECLARED_SCOPE"
        return {"status": state, "observation_revision": latest["revision"] if latest else 0,
                "scope": receipt, "latest": latest,
                "meaning": "Current evidence context; frozen model versions and results are not rewritten"}

    def observe_system(self, cid, payload):
        fields(payload, {"base_version", "observation_revision", "idempotency_key", "observation"},
               {"base_version", "observation_revision", "idempotency_key", "observation"})
        base = integer(payload["base_version"], "base_version")
        revision = integer(payload["observation_revision"], "observation_revision")
        key = text(payload["idempotency_key"], "idempotency_key", 128, 8)
        from .systems import recognize
        try:
            recognition = recognize(payload["observation"])
        except (ValueError, KeyError, TypeError) as exc:
            raise ServiceError("invalid_system_observation", "Revisa las entidades, relaciones, fuentes y fechas.", 422, str(exc)) from exc
        fingerprint = sha({"operation": "system_observation", "request": payload})
        with self.store.transaction() as conn:
            case = self._case(cid, conn)
            previous = conn.execute("SELECT * FROM idempotency WHERE case_id=? AND key=?", (cid, key)).fetchone()
            if previous:
                require(previous["request_sha256"] == fingerprint, "idempotency_conflict", "La clave ya identifica otra solicitud.", 409)
                return json.loads(previous["response_json"])
            require(case["profile"] == registry.STOCKFLOW, "observation_profile_not_supported", "Este registro pertenece al gemelo general.", 422)
            require(case["current_version"] == base, "version_conflict", "La versión del modelo cambió.", 409)
            records = self._system_records(cid, conn)
            require(len(records) == revision, "observation_conflict", "Existe una observación de sistemas más reciente.", 409)
            require(revision < min(64, self.execution_context.get("system_observation_limit", 64)),
                    "system_observation_limit", "Límite de observaciones alcanzado. Exporta el expediente para conservarlo.", 429)
            identities = {e["id"]: e["kind"] for r in records for e in r["observation"]["entities"]}
            require(all(e["id"] not in identities or identities[e["id"]] == e["kind"] for e in payload["observation"]["entities"]),
                    "identity_conflict", "Una identidad existente no puede cambiar de tipo. Revisa la correspondencia.", 422)
            current_entities = {e["id"] for e in payload["observation"]["entities"]}
            current_relations = {r["id"]: (r["source"], r["target"], r["kind"]) for r in payload["observation"]["relations"]}
            old_relations = [(r["id"], (r["source"], r["target"], r["kind"])) for record in records for r in record["observation"]["relations"]]
            # Non-observation is not evidence of disappearance. Preserve gaps
            # across ALL prior views, not only the immediately preceding view.
            historical_gaps = {"unobserved_entities": sorted(set(identities) - current_entities),
                               "unobserved_relations": sorted({rid for rid, _ in old_relations if rid not in current_relations}),
                               "conflicting_relations": sorted({rid for rid, edge in old_relations if rid in current_relations and current_relations[rid] != edge})}
            record = {"kind": "system_observation", "id": identifier(), "revision": revision + 1,
                      "base_version": base, "received_at": now(), "observation": deepcopy(payload["observation"]),
                      "recognition": recognition, "historical_gaps": historical_gaps, "empirical_validation": "NOT_ASSESSED"}
            conn.execute("INSERT INTO observations VALUES(?,?,?,?,?,?)",
                         (record["id"], cid, base, base, dumps(record), record["received_at"]))
            conn.execute("UPDATE cases SET updated_at=? WHERE id=?", (record["received_at"], cid))
            response = {"system_observation": record, "model_changed": False, "scope_review_required": True}
            conn.execute("INSERT INTO idempotency VALUES(?,?,?,?)", (cid, key, fingerprint, dumps(response)))
        return response

    def prepare_world(self, cid, payload):
        fields(payload, {"base_version", "construction"}, {"base_version", "construction"})
        base = integer(payload["base_version"], "base_version")
        with self.store.transaction() as conn:
            case = self._case(cid, conn)
            require(case["profile"] == registry.STOCKFLOW, "change_outside_profile", "La construcción requiere un expediente general.", 422)
            require(case["current_version"] == base, "version_conflict", "La versión del expediente cambió.", 409)
            records = self._system_records(cid, conn)
            return self._prepare_world(payload["construction"], records[-1] if records else None)

    @staticmethod
    def _prepare_world(construction, observation):
        from .construction import prepare
        try:
            return prepare(construction, observation)
        except (ValueError, KeyError, TypeError, RecursionError) as exc:
            raise ServiceError("invalid_world_construction", "Revisa fuentes, citas, afirmaciones y fragmentos del modelo.", 422, str(exc)) from exc

    def save_draft(self, cid, payload):
        fields(payload, {"base_version", "draft_revision", "text", "model"}, {"base_version", "draft_revision", "text", "model"})
        base = integer(payload["base_version"], "base_version")
        revision = integer(payload["draft_revision"], "draft_revision")
        narrative = text(payload["text"])
        require(payload["model"] is None or type(payload["model"]) is dict, "invalid_draft", "model debe ser objeto o null en un borrador.")
        with self.store.transaction() as conn:
            case = self._case(cid, conn)
            require(case["current_version"] == base, "version_conflict", "La versión aceptada cambió.", 409)
            draft = conn.execute("SELECT * FROM drafts WHERE case_id=?", (cid,)).fetchone()
            actual = draft["revision"] if draft else 0
            require(actual == revision, "draft_conflict", "Existe un borrador más reciente.", 409, {"draft_revision": actual})
            conn.execute("INSERT INTO drafts VALUES(?,?,?,?,?,?) ON CONFLICT(case_id) DO UPDATE SET revision=excluded.revision,base_version=excluded.base_version,text=excluded.text,model_json=excluded.model_json,updated_at=excluded.updated_at",
                         (cid, revision + 1, base, narrative, dumps(payload["model"]) if payload["model"] is not None else None, now()))
            conn.execute("UPDATE cases SET updated_at=? WHERE id=?", (now(), cid))
            saved = Store.draft(conn.execute("SELECT * FROM drafts WHERE case_id=?", (cid,)).fetchone())
        return {"case": Store.case(self._case(cid)), "draft": saved}

    def delete_case(self, cid, payload):
        fields(payload, {"base_version"}, {"base_version"})
        base = integer(payload["base_version"], "base_version")
        with self.store.transaction() as conn:
            case = self._case(cid, conn)
            require(case["current_version"] == base, "version_conflict", "El expediente cambió antes del borrado.", 409)
            require(not conn.execute("SELECT 1 FROM jobs WHERE case_id=? AND status='running'", (cid,)).fetchone(),
                    "job_running", "Espera la evaluación activa antes de borrar el expediente.", 409)
            if self.before_erase is not None:
                self.before_erase(cid)
            self.store.erase_case(cid, conn)
        return {"case_id": cid, "status": "deleted"}

    def propose(self, cid, payload):
        fields(payload, {"base_version", "kind", "text", "structured"}, {"base_version", "kind", "text"})
        base = integer(payload["base_version"], "base_version")
        message = text(payload["text"])
        kind = payload["kind"]
        require(type(kind) is str and kind in {"declared_model", "world_model", "intervention_design", "system_scope", "hypothetical_intervention", "preference", "fact_correction", "restore"},
                "unsupported_change_kind", "Tipo de cambio no admitido; usa observaciones para incorporar evidencia.")
        structured = payload.get("structured", {})
        require(type(structured) is dict, "invalid_object", "structured debe ser objeto.")
        with self.store.transaction() as conn:
            case = self._case(cid, conn)
            require(case["current_version"] == base, "version_conflict", "El expediente cambió. Revisa la propuesta sobre su versión actual.", 409,
                    {"current_version": case["current_version"], "base_version": base})
            require(base > 0 or kind in ("declared_model", "world_model"), "model_required", "Primero declara un modelo completo.", 422)
            prior = self._version(cid, base, conn) if base else None
            model = deepcopy(prior["model"]) if prior else None
            metadata = deepcopy(prior["metadata"]) if prior else {"review_required": False}
            # A generation receipt belongs to one exact model. Keep old receipts
            # in immutable history, never attach them to an unrelated edit.
            if kind != "system_scope":
                metadata.pop("intervention_design", None)
                metadata.pop("world_construction", None)
            metadata.update({"change_kind": kind, "source_text": message, "material_changes": []})
            if kind == "declared_model":
                fields(structured, {"model"}, {"model"})
                model = deepcopy(structured["model"])
                self._validate_model(model)
                old = prior["model"] if prior else {}
                changed = [key for key in sorted(set(old) | set(model)) if old.get(key) != model.get(key)]
                metadata.update({"synthetic": model["profile"] == registry.D1,
                                 "evidence_origin": "SYNTHETIC_STIPULATION" if model["profile"] == registry.D1 else "USER_DECLARED_MODEL",
                                 "interpretation_method": "explicit_structured_model_not_inferred_from_prose",
                                 "empirical_admission": "NOT_ASSESSED", "changed_fields": changed,
                                 "material_changes": ["Modelo completo declarado; revisar parámetros, reglas, unidades y premisas.",
                                                      "Campos modificados: " + ", ".join(changed),
                                                      "Confirmar el modelo no autentica sus fuentes ni valida empíricamente sus predicciones."]})
            elif kind == "world_model":
                fields(structured, {"construction"}, {"construction"})
                require(case["profile"] == registry.STOCKFLOW, "change_outside_profile", "La construcción requiere un expediente general.", 422)
                records = self._system_records(cid, conn)
                prepared = self._prepare_world(structured["construction"], records[-1] if records else None)
                require(prepared["status"] == "READY_FOR_REVIEW", "world_construction_incomplete",
                        "Resuelve los faltantes antes de proponer este modelo.", 422, prepared["questions"])
                model = deepcopy(prepared["model"])
                receipt = prepared["receipt"]
                metadata.update({"world_construction": receipt, "system_scope": prepared["scope_receipt"],
                    "review_required": prepared["scope_receipt"]["review_required"], "synthetic": False,
                    "evidence_origin": "SOURCE_LINKED_DECLARED_MODEL", "empirical_admission": "NOT_ASSESSED",
                    "interpretation_method": "domain_neutral_assembly_of_agent_or_human_interpretation",
                    "material_changes": ["Modelo ensamblado a partir de fragmentos con afirmaciones, fuentes y supuestos trazables.",
                        "Se comprueban citas literales, estructura, unidades y restricciones del perfil; no verdad, causalidad ni implicación semántica.",
                        "Los límites y correspondencias se conservan con la última observación de sistemas.",
                        "Faltantes probabilísticos y umbrales desconocidos se conservan; no se completan con valores por defecto.",
                        "Revisar las hipótesis antes de confirmar. La propuesta no concede autoridad para actuar."]})
            elif kind == "system_scope":
                fields(structured, {"scope"}, {"scope"})
                require(model["profile"] == registry.STOCKFLOW, "change_outside_profile", "Los límites requieren un modelo general.", 422)
                records = self._system_records(cid, conn)
                require(bool(records), "system_observation_required", "Registra primero las observaciones de sistemas.", 422)
                latest = records[-1]
                from .systems import review_scope
                try:
                    receipt = review_scope(model, latest["observation"], structured["scope"])
                except (ValueError, KeyError, TypeError) as exc:
                    raise ServiceError("invalid_system_scope", "Revisa los límites y las correspondencias del sistema.", 422, str(exc)) from exc
                require(structured["scope"]["observation_revision"] == latest["revision"], "observation_conflict", "Los límites no usan la última observación.", 409)
                receipt.update({"observation_id": latest["id"], "observation_revision": latest["revision"]})
                receipt["historical_gaps"] = deepcopy(latest["historical_gaps"])
                receipt["review_required"] = receipt["review_required"] or any(latest["historical_gaps"].values())
                metadata.update({"system_scope": receipt, "review_required": receipt["review_required"],
                    "material_changes": ["Fronteras del sistema, de intervención y de evaluación conservadas con evidencia y correspondencias.",
                        "El cálculo numérico no cambia; las relaciones observadas aún no calibran su dinámica.",
                        "Entidades de evaluación sin representar: " + (", ".join(receipt["unmapped_entities"]) or "ninguna según las correspondencias declaradas"),
                        "Omisiones o contradicciones respecto de vistas anteriores: " + ("requieren revisión" if any(receipt["historical_gaps"].values()) else "no detectadas"),
                        "Confirmar esta hipótesis no verifica sus fuentes ni autoriza actuar sobre el mundo."]})
            elif kind == "intervention_design":
                fields(structured, {"design"}, {"design"})
                require(model["profile"] == registry.STOCKFLOW, "change_outside_profile",
                        "El diseño de intervenciones requiere un modelo de existencias y flujos confirmado.", 422)
                from .interventions import generate
                try:
                    model, receipt = generate(model, structured["design"])
                except (ValueError, KeyError, TypeError) as exc:
                    raise ServiceError("intervention_outside_profile", "Revisa las intervenciones y los límites del modelo.", 422, str(exc)) from exc
                receipt["base_version"] = base
                metadata.update({"intervention_design": receipt, "synthetic": False,
                    "evidence_origin": "USER_DECLARED_MODEL", "empirical_admission": "NOT_ASSESSED",
                    "interpretation_method": "enumeration_of_declared_interventions",
                    "material_changes": [
                        f"Se conservan {len(receipt['baseline_policies'])} planes de referencia y se generan {receipt['generated_count']} alternativas.",
                        "Las relaciones declaran origen, destino, disponibilidad, requisitos y costos de intercambio.",
                        "Los saldos iniciales, escenarios, ley y criterios se conservan para todas las alternativas.",
                        "Revisar todas las secuencias, cantidades y premisas antes de evaluar. No se ejecutan acciones físicas."]})
            elif kind == "hypothetical_intervention":
                require(model["profile"] == registry.D1, "change_outside_profile", "Este cambio pertenece al perfil semillero; usa declared_model.", 422)
                words = normalized(message)
                prose_match = ("formacion" in words and ("dia 9" in words or "dia9" in words) and
                               any(word in words for word in ("relevo", "ausen", "falta", "emergencia", "cubre")))
                fields(structured, {"operation"})
                require(structured.get("operation") == "apply_relay_policy" or (not structured and prose_match),
                        "change_requires_structure", "El texto no define una intervención admitida. Revisa la propuesta de formación día9 y relevo de A día10.", 422)
                require(model["policies"] == ["C", "R", "E"], "policy_already_changed", "El relevo ya está representado; restaura una versión para comparar de nuevo.", 409)
                model["policies"] = ["C", "R", "E_prime"]
                metadata["historical_policy"] = "E"
                metadata["material_changes"] = ["Formación de A y verificación de B al día9.", "Si B falta el día10, A riega durante10min adicionales.",
                                                "E_prime sustituye E en la familia actual; E permanece histórica.", "Recalcular entrada FP1 completa; no reutilizar certificados anteriores."]
            elif kind == "preference":
                require(model["profile"] == registry.D1, "change_outside_profile", "Usa declared_model para revisar este perfil.", 422)
                fields(structured, {"require_all_scenarios"}, {"require_all_scenarios"})
                require(type(structured["require_all_scenarios"]) is bool, "invalid_preference", "La restricción debe ser true o false.")
                model["require_all_scenarios"] = structured["require_all_scenarios"]
                metadata["material_changes"] = ["Cambiar restricción normativa de ninguna violación en todos los escenarios.", "La preferencia no altera efectos físicos, bienestar ni CAG/PVS por política."]
            elif kind == "fact_correction":
                require(model["profile"] == registry.D1, "change_outside_profile", "Usa declared_model para revisar este perfil.", 422)
                fields(structured, {"law", "source"}, {"law", "source"})
                metadata["law_source"] = text(structured["source"], "source", 2000)
                model["law"] = deepcopy(structured["law"])
                metadata["material_changes"] = ["Corregir la ley conjunta declarada; no cambia trayectorias ni convierte la ley en observación empírica.",
                                                "Los nuevos pesos siguen siendo premisas condicionales; revisar su fundamento antes de uso real."]
            else:
                fields(structured, {"version"}, {"version"})
                restored = self._version(cid, structured["version"], conn)
                model = deepcopy(restored["model"])
                metadata["synthetic"] = model["profile"] == registry.D1
                metadata["evidence_origin"] = "SYNTHETIC_STIPULATION" if metadata["synthetic"] else "USER_DECLARED_MODEL"
                metadata["restored_from"] = restored["version"]
                if "intervention_design" in restored["metadata"]:
                    metadata["intervention_design"] = deepcopy(restored["metadata"]["intervention_design"])
                if "world_construction" in restored["metadata"]:
                    metadata["world_construction"] = deepcopy(restored["metadata"]["world_construction"])
                if "system_scope" in restored["metadata"]:
                    metadata["system_scope"] = deepcopy(restored["metadata"]["system_scope"])
                    metadata["review_required"] = restored["metadata"].get("review_required", False)
                else:
                    metadata.pop("system_scope", None)
                metadata["material_changes"] = ["Restaurar contenido del modelo en una nueva versión, conservando todas las observaciones y la historia."]
            self._validate_model(model)
            require(prior is None or model != prior["model"] or (kind == "system_scope" and metadata.get("system_scope") != prior["metadata"].get("system_scope"))
                    or (kind == "world_model" and metadata.get("world_construction") != prior["metadata"].get("world_construction")),
                    "no_material_change", "La propuesta no cambia el modelo ni sus límites.")
            proposal = self._insert_proposal(conn, cid, base, kind, message, model, metadata)
        return {"proposal": proposal}

    def accept(self, pid, payload):
        fields(payload, {"base_version", "idempotency_key", "confirmed", "acknowledge_synthetic", "acknowledge_declared"},
               {"base_version", "idempotency_key", "confirmed"})
        base = integer(payload["base_version"], "base_version")
        key = text(payload["idempotency_key"], "idempotency_key", 128, 8)
        require(payload["confirmed"] is True, "confirmation_required", "Debes confirmar los cambios materiales.", 422)
        fingerprint = sha({"proposal_id": pid, "request": payload})
        with self.store.transaction() as conn:
            row = conn.execute("SELECT * FROM proposals WHERE id=?", (pid,)).fetchone()
            require(row is not None, "proposal_not_found", "Propuesta no encontrada.", 404)
            cid = row["case_id"]
            previous = conn.execute("SELECT * FROM idempotency WHERE case_id=? AND key=?", (cid, key)).fetchone()
            if previous:
                require(previous["request_sha256"] == fingerprint, "idempotency_conflict", "La clave ya identifica otra solicitud.", 409)
                return json.loads(previous["response_json"])
            case = self._case(cid, conn)
            require(case["current_version"] == base == row["base_version"], "version_conflict", "La versión base dejó de ser actual.", 409,
                    {"current_version": case["current_version"], "base_version": base})
            require(row["status"] == "proposed", "proposal_already_accepted", "La propuesta ya se aceptó.", 409)
            require(row["model_json"] is not None, "model_required", "No existe un modelo admitido para aceptar.", 422)
            model, metadata = json.loads(row["model_json"]), json.loads(row["metadata_json"])
            if row["kind"] in ("system_scope", "world_model"):
                records = self._system_records(cid, conn)
                require(records and metadata["system_scope"]["observation_revision"] == records[-1]["revision"],
                        "observation_conflict", "Hay nueva evidencia; revisa los límites antes de confirmar.", 409)
            self._validate_model(model)
            acknowledgement = "acknowledge_synthetic" if model["profile"] == registry.D1 else "acknowledge_declared"
            require(payload.get(acknowledgement) is True, "confirmation_required",
                    "Debes reconocer el alcance del perfil y sus premisas declaradas.", 422,
                    {"required_acknowledgement": acknowledgement})
            metadata["confirmation"] = {"confirmed_at": now(), "synthetic_acknowledged": model["profile"] == registry.D1,
                                         "declared_acknowledged": model["profile"] != registry.D1, "proposal_id": pid,
                                         "meaning": "Confirmation of a model for analysis, not authentication of facts or permission to act"}
            version = Store.add_version(conn, cid, base, model, metadata)
            conn.execute("UPDATE proposals SET status='accepted',accepted_version=? WHERE id=?", (version["version"], pid))
            response = {"case": Store.case(self._case(cid, conn)), "version": version}
            conn.execute("INSERT INTO idempotency VALUES(?,?,?,?)", (cid, key, fingerprint, dumps(response)))
            return response

    def evaluate(self, cid, payload):
        fields(payload, {"version"}, {"version"})
        self._case(cid)
        version = self._version(cid, payload["version"])
        system_context = self.system_context(cid, version)
        require(system_context["status"] != "REVIEW_REQUIRED", "system_scope_review_required",
                "Revisa los límites frente a la última observación y al modelo actual antes de recalcular.", 409)
        identity = registry.execution_identity(version["model"]["profile"], self.execution_context)
        execution_key = sha({"model_sha256": version["model_sha256"], "identity": identity})
        jid = identifier()
        with self.store.transaction() as conn:
            running = conn.execute("SELECT id FROM jobs WHERE case_id=? AND version=? AND status='running'", (cid, version["version"])).fetchone()
            require(running is None, "job_running", "Esta versión ya se está evaluando.", 409, {"job_id": running["id"]} if running else None)
            existing = conn.execute("SELECT * FROM jobs WHERE case_id=? AND version=? AND execution_key=? AND status='completed' ORDER BY created_at DESC LIMIT 1", (cid, version["version"], execution_key)).fetchone()
            if existing:
                return self._job_response(existing)
            conn.execute("INSERT INTO jobs(id,case_id,version,status,created_at,finished_at,result_json,error_json,execution_key,execution_identity_json) VALUES(?,?,?,'running',?,NULL,NULL,NULL,?,?)", (jid, cid, version["version"], now(), execution_key, dumps(identity)))
        try:
            result = self.evaluator(deepcopy(version["model"]))
            require(type(result) is dict and "native_result" in result and "canonical_results" in result,
                    "invalid_compiler_result", "El compilador no entregó el contrato de evaluación.", 500)
            synthetic = version["model"]["profile"] == registry.D1
            decision = result["canonical_results"].get("decision", {})
            recommendation = ("CONDITIONAL_TO_DECLARED_MODEL" if decision.get("selected") is not None
                              else "NO_SELECTION_UNDER_DECLARED_MODEL")
            if result.get("verification", {}).get("valid") is not True:
                recommendation = "NOT_ISSUED_UNVERIFIED_RESULT"
            envelope = {"format": "genius-twin-evaluation/0.2.0", "case_id": cid, "version": version["version"],
                        "model_sha256": version["model_sha256"], "job_id": jid,
                        "execution_key": execution_key, "execution_identity": identity,
                        "scope": "CONDITIONAL_SYNTHETIC_MODEL_ONLY" if synthetic else "CONDITIONAL_DECLARED_MODEL_ONLY", "rc01_receipt": None,
                        "rc01_status": "NOT_PRODUCED_NEW_FP1_PRODUCT_ENVELOPE",
                        "admission": "MODEL_REVIEW_REQUIRED" if version["metadata"].get("review_required") else ("SYNTHETIC_ONLY" if synthetic else "DECLARED_MODEL_ONLY"),
                        "recommendation_status": "SUSPENDED_PENDING_MODEL_REVIEW" if version["metadata"].get("review_required") else recommendation,
                        "provenance": {"kind": "SYNTHETIC_STIPULATION" if synthetic else "USER_DECLARED_MODEL", "empirical_validation": "NOT_ASSESSED",
                                       "observations_calibrate_model": False},
                        "canonical_results": result["canonical_results"],
                        "native_result": result["native_result"], "verification": result.get("verification"),
                        "native_input_json": result.get("native_input_json"), "native_runs": result.get("native_runs"),
                        "compilation_manifest": result.get("compilation_manifest")}
            if "intervention_design" in version["metadata"]:
                envelope["intervention_design"] = deepcopy(version["metadata"]["intervention_design"])
            if "system_scope" in version["metadata"]:
                envelope["system_scope"] = deepcopy(version["metadata"]["system_scope"])
            if "world_construction" in version["metadata"]:
                envelope["world_construction"] = deepcopy(version["metadata"]["world_construction"])
            with self.store.transaction() as conn:
                conn.execute("UPDATE jobs SET status='completed',finished_at=?,result_json=? WHERE id=? AND status='running'", (now(), dumps(envelope), jid))
        except Exception as exc:
            error = {"code": exc.code if isinstance(exc, ServiceError) else ("evaluation_timeout" if isinstance(exc, TimeoutError) else "evaluation_failed"),
                     "message": exc.message if isinstance(exc, ServiceError) else "La evaluación no pudo completarse; no se infiere inviabilidad."}
            with self.store.transaction() as conn:
                conn.execute("UPDATE jobs SET status='failed',finished_at=?,error_json=? WHERE id=? AND status='running'", (now(), dumps(error), jid))
        return self.read_job(jid)

    def recover_jobs(self):
        """Only call while owning exclusive lifecycle access to this Store.

        Not invoked by construction: another request/process may own a live job.
        The embedding must first rule out any active worker (e.g. tenant lock).
        """
        with self.store.transaction() as conn:
            changed = conn.execute("UPDATE jobs SET status='interrupted',finished_at=?,error_json=? WHERE status='running'",
                (now(), dumps({"code": "execution_interrupted", "message": "La ejecución se interrumpió. Puede reintentarse; no prueba inviabilidad."}))).rowcount
        return {"recovered_jobs": changed}

    @staticmethod
    def _job_response(row):
        job = Store.job(row, full=True)
        result = job.pop("evaluation")
        return {"job": job, "evaluation": result}

    def read_job(self, jid):
        row = self.store.one("SELECT * FROM jobs WHERE id=?", (jid,))
        require(row is not None, "job_not_found", "Evaluación no encontrada.", 404)
        return self._job_response(row)

    def observe(self, cid, payload):
        required = {"base_version", "policy_id", "scenario_id", "day", "variable", "value", "unit", "observed_at", "source", "idempotency_key"}
        fields(payload, required, required)
        base = integer(payload["base_version"], "base_version", 1)
        self._case(cid)
        observed_version = self._version(cid, base)
        model = observed_version["model"]
        require(model["profile"] in (registry.D1, registry.STOCKFLOW), "observation_profile_not_supported",
                "Este perfil todavía no admite registro de observaciones. La comparación de versiones sí está disponible.", 422)
        stockflow = model["profile"] == registry.STOCKFLOW
        day = integer(payload["day"], "day", 0, model["horizon"] if stockflow else 14)
        key = text(payload["idempotency_key"], "idempotency_key", 128, 8)
        source = text(payload["source"], "source", 2000)
        observed_at = text(payload["observed_at"], "observed_at", 80)
        try:
            timestamp = datetime.fromisoformat(observed_at.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ServiceError("invalid_observation_time", "La fecha debe ser ISO8601 con zona horaria.") from exc
        require(timestamp.tzinfo is not None, "invalid_observation_time", "La observación requiere zona horaria.")
        variable = payload["variable"]
        # Stock-flow cases observe a declared stock in its declared unit.
        units = ({stock["id"]: stock["unit"] for stock in model["stocks"]} if stockflow else
                 {"water_in_tray_liters": "L", "minutes_a": "min", "minutes_b": "min"})
        require(type(variable) is str and variable in units and payload["unit"] == units[variable], "observation_unit_mismatch", "Variable o unidad no admitida.")
        measured = rational(payload["value"])
        require(measured >= 0, "invalid_quantity", "La magnitud observada no puede ser negativa.")
        fingerprint = sha({"operation": "observation", "request": payload})
        with self.store.transaction() as conn:
            case = self._case(cid, conn)
            previous = conn.execute("SELECT * FROM idempotency WHERE case_id=? AND key=?", (cid, key)).fetchone()
            if previous:
                require(previous["request_sha256"] == fingerprint, "idempotency_conflict", "La clave ya identifica otra solicitud.", 409)
                return json.loads(previous["response_json"])
            require(case["current_version"] == base, "version_conflict", "Registra la observación contra una versión base actual.", 409)
            prior = self._version(cid, base, conn)
            policies = {policy["id"] for policy in prior["model"]["policies"]} if stockflow else prior["model"]["policies"]
            scenarios = {scenario["id"] for scenario in prior["model"]["scenarios"]} if stockflow else prior["model"]["law"]
            require(type(payload["policy_id"]) is str and type(payload["scenario_id"]) is str and
                    payload["policy_id"] in policies and payload["scenario_id"] in scenarios,
                    "invalid_observation_reference", "Política/escenario no pertenece a esta versión.")
            prediction_job = conn.execute("SELECT * FROM jobs WHERE case_id=? AND version=? AND status='completed' ORDER BY created_at DESC LIMIT 1", (cid, base)).fetchone()
            require(prediction_job is not None, "frozen_prediction_required", "Evalúa primero esta versión para contrastar con una predicción congelada.", 422)
            frozen = json.loads(prediction_job["result_json"])
            state = frozen["canonical_results"]["policies"][payload["policy_id"]]["trajectories"][payload["scenario_id"]]["daily"][day]
            predicted = Fraction(state["stocks"][variable] if stockflow else state[variable])
            prediction_finished = datetime.fromisoformat(prediction_job["finished_at"])
            deviation = measured != predicted
            oid = identifier()
            record = {"id": oid, "case_id": cid, "prediction_version": base, "recorded_version": base + 1,
                      "prediction_job_id": prediction_job["id"], "prediction_model_sha256": prior["model_sha256"],
                      "prediction_input_digest": frozen["native_result"].get("input_digest"),
                      "policy_id": payload["policy_id"], "scenario_id": payload["scenario_id"], "day": day,
                      "variable": variable, "value_exact": q(measured), "unit": payload["unit"],
                      "observed_at": observed_at, "received_at": now(), "source": source,
                      "origin": "USER_DECLARED_OBSERVATION", "source_authentication": "NOT_ESTABLISHED",
                      "comparison": {"predicted_exact": q(predicted), "delta_exact": q(measured-predicted),
                                     "status": "DISCREPANCY_REQUIRES_REVIEW" if deviation else "MATCH_NOT_MODEL_VALIDATION",
                                     "model_was_calibrated": False,
                                     "temporal_relation": "PROSPECTIVE_REFERENCE" if timestamp > prediction_finished else "RETROSPECTIVE_COMPARISON_NOT_PROSPECTIVE_VALIDATION",
                                     "meaning": "Comparison against a frozen synthetic prediction; observation does not validate its model"}}
            metadata = deepcopy(prior["metadata"])
            metadata["observation_ids"] = metadata.get("observation_ids", []) + [oid]
            metadata["review_required"] = bool(metadata.get("review_required") or deviation)
            metadata["change_kind"] = "incorporate_observation"
            metadata["material_changes"] = ["Nueva observación conservada sin sobrescribir la predicción ni calibrar automáticamente el modelo."]
            version = Store.add_version(conn, cid, base, prior["model"], metadata)
            conn.execute("INSERT INTO observations VALUES(?,?,?,?,?,?)", (oid, cid, base, version["version"], dumps(record), now()))
            response = {"case": Store.case(self._case(cid, conn)), "version": version, "observation": record}
            conn.execute("INSERT INTO idempotency VALUES(?,?,?,?)", (cid, key, fingerprint, dumps(response)))
            return response

    def compare(self, cid, before, after):
        self._case(cid)
        old, new = self._version(cid, before), self._version(cid, after)
        changes = [{"field": key, "before": old["model"].get(key), "after": new["model"].get(key)}
                   for key in sorted(set(old["model"]) | set(new["model"])) if old["model"].get(key) != new["model"].get(key)]
        results = {}
        for name, version in (("before", before), ("after", after)):
            row = self.store.one("SELECT * FROM jobs WHERE case_id=? AND version=? AND status='completed' ORDER BY created_at DESC LIMIT 1", (cid, version))
            results[name] = json.loads(row["result_json"])["canonical_results"] if row else None
        return {"case_id": cid, "before": old, "after": new, "model_changes": changes,
                "results": results, "result_versions": {"before": before, "after": after},
                "system_scope_comparison": {"before": old["metadata"].get("system_scope"), "after": new["metadata"].get("system_scope"),
                    "same_scope": old["metadata"].get("system_scope", {}).get("scope_sha256") == new["metadata"].get("system_scope", {}).get("scope_sha256"),
                    "meaning": "Different boundaries/evidence do not establish improvement on a common scope"},
                "claim": "Comparison of frozen versions; unchanged values do not transport an old FP1 certificate"}

    def export(self, cid):
        dossier = self.read_case(cid)
        dossier["evaluations"] = [self._job_response(r) for r in self.store.read("SELECT * FROM jobs WHERE case_id=? ORDER BY created_at,id", (cid,))]
        return {"format": "genius-twin-dossier/0.1.0", "consumer_semantics": "SAME_CANONICAL_OBJECT_FOR_HUMAN_APPLICATION_AGENT",
                "dossier": dossier, "dossier_sha256": sha(dossier)}
