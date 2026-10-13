"""Three deterministic views; source values remain exact and data-only."""
from __future__ import annotations

import base64
import html
import json
import os
from pathlib import Path
import shutil
import tempfile
import unicodedata

from .reader import (Budget, MAX_EXPORT_BYTES, ViewError, canonical, read_case,
                     require, safe_path, sha)

LABELS = {
    "PT_DELIVERED": "Sobre local recibido", "PT_FAILED": "Entrega fallida",
    "PT_NOT_ATTEMPTED": "Entrega no intentada",
    "PE_COMPLETE": "Ejecución completada", "PE_PARTIAL": "Ejecución parcial",
    "PE_NOT_STARTED": "Ejecución no iniciada", "PE_BUDGET_EXHAUSTED": "Presupuesto agotado",
    "PE_ERROR": "Error de ejecución", "PE_CANCELLED": "Ejecución cancelada",
    "PE_UNKNOWN": "Ejecución desconocida; sin recibo final",
    "PR_JUSTIFIED_RESULT": "Resultado justificado para la consulta exacta",
    "PR_SET_OR_INCOMPARABLE": "Conjunto o incomparabilidad; no implica selección",
    "PR_PROVEN_INFEASIBLE": "Inviabilidad demostrada dentro de la cobertura declarada",
    "PR_PARTIAL": "Resultado parcial", "PR_DEPENDENCY": "Dependencia pendiente",
    "PR_OUTSIDE_PROFILE": "Fuera del perfil", "PR_NOT_EVALUATED": "Decisión no evaluada",
    "EV_SUPPORTED_SCOPED": "Evidencia con apoyo limitado al alcance",
    "EV_CONDITIONAL": "Evidencia condicional", "EV_CONFLICTING": "Evidencia conflictiva",
    "EV_INSUFFICIENT": "Evidencia insuficiente", "EV_OUTSIDE_SCOPE": "Evidencia fuera del alcance",
    "EV_NOT_EVALUATED": "Evidencia no evaluada",
    "PC_ANSWERED_SCOPED": "Consulta respondida dentro del alcance",
    "PC_WAITING_DEPENDENCY": "A la espera de una dependencia", "PC_PARTIAL": "Cierre parcial",
    "PC_CANCELLED": "Cierre por cancelación", "PC_BUDGET_EXHAUSTED": "Cierre por presupuesto",
    "PC_ERROR": "Cierre por error", "PC_OUTSIDE_PROFILE": "Cierre fuera del perfil",
}
CAUSE_LABELS = {
    "DERIVABLE": "Información derivable bajo la regla declarada",
    "YA_DISPONIBLE": "Información ya disponible para verificar",
    "IRRELEVANTE_DEMOSTRADO": "Prueba de irrelevancia dentro del alcance",
    "DATO_EXTERNO": "Dato externo a cargo del responsable indicado",
    "DEFINICION_MODELO": "Definición o admisión del modelo; no equivale a inventar un dato",
    "PREFERENCIA": "Preferencia o norma de selección",
    "CAPACIDAD_AUSENTE": "Capacidad del sistema requerida",
    "COMPUTO_PENDIENTE": "Cálculo dentro del perfil y recepción de su resultado",
    "DISENO_ESTUDIO": "Diseño de estudio y condiciones de admisión",
}
QUALITY_LABELS = {
    "formal_correctness": "Corrección formal", "coverage": "Cobertura",
    "data_provenance": "Procedencia de los datos", "model_fidelity": "Fidelidad del modelo",
    "uncertainty_sensitivity": "Incertidumbre y sensibilidad", "utility": "Utilidad",
    "comprehension": "Comprensión humana", "information_efficiency": "Eficiencia de información",
    "operation": "Operación", "adoption_business": "Adopción y negocio",
}
LIMIT = ("Esta vista conserva un recibo técnico. No demuestra verdad física, comprensión o utilidad humana, "
         "ni autoriza una intervención. Un dato desconocido no es cero ni una probabilidad. "
         "La calidad se conserva por dimensiones, sin puntaje global. "
         "FDQ conserva su alcance formal y condicional: no demuestra pertenencia del sistema real al modelo. "
         "PVS no es un puntaje de confianza ni una probabilidad de supervivencia presumida. "
         "Una fuente compatible no convierte un modelo sintético en evidencia física. "
         "REQUEST_INPUT conserva una solicitud local: no la envía ni acredita respuesta o aceptación humana. "
         "El cierre local no implica que un proceso siga trabajando; la reapertura requiere la condición registrada.")


def leaves(value, pointer=""):
    if isinstance(value, dict) and value:
        for key in sorted(value):
            yield from leaves(value[key], pointer + "/" + key.replace("~", "~0").replace("/", "~1"))
    elif isinstance(value, list) and value:
        for index, item in enumerate(value):
            yield from leaves(item, pointer + "/" + str(index))
    else:
        yield pointer, value


def literal(value):
    # ASCII JSON escapes make bidi controls, terminal controls and homoglyphs
    # inspectable. json.loads reverses this representation without loss.
    return html.escape(json.dumps(value, ensure_ascii=True, sort_keys=True,
                                  separators=(",", ":"), allow_nan=False), quote=True)


def readable(value):
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, sort_keys=True)
    text = "".join("\\u%04x" % ord(char) if unicodedata.category(char) in {"Cc", "Cf"} else char for char in text)
    return html.escape(text, quote=True)


def value_summary(value):
    if isinstance(value, dict):
        state = value.get("state")
        if state == "PV_UNKNOWN":
            return "<p><strong>Valor desconocido.</strong> " + readable("; ".join(value["reasons"])) + " Obligaciones: " + readable(value["obligation_refs"]) + ".</p>"
        if state == "PV_KNOWN":
            result = "<p><strong>Valor conocido dentro del alcance:</strong> <code>" + readable(value["value"]) + "</code>. Unidad: <code>" + readable(value["unit"]) + "</code>. Base registrada: " + readable(value["basis"]) + ".</p>"
            content = value["value"]
            selector = content.get("selector") if isinstance(content, dict) else None
            if isinstance(selector, dict) and selector.get("state") == "OUTSIDE_DOMAIN":
                cause = selector.get("cause")
                labels = {"SELECTION_DISABLED": "la selección está desactivada", "SELECTION_EMPTY": "el conjunto admitido para selección está vacío", "SELECTION_NOT_UNIQUE": "no hay una elección única bajo la norma recibida"}
                result += "<p><strong>No hay selector definido</strong> porque " + readable(labels.get(cause, "se registró la causa " + str(cause))) + ". Esta respuesta no determina por sí sola la frontera.</p>"
            if isinstance(content, dict) and "frontier" in content:
                result += "<p>La frontera conserva el conjunto recibido; no implica una política seleccionada.</p>"
            return result
        if state in {"PV_NOT_APPLICABLE", "PV_OUTSIDE_PROFILE"}:
            return "<p><strong>" + ("No aplicable" if state == "PV_NOT_APPLICABLE" else "Fuera del perfil") + ":</strong> " + readable(value["reasons"]) + ".</p>"
        names = {"sum": "Suma", "excess": "Exceso", "deficit": "Déficit", "selector": "Selector", "frontier": "Frontera",
                 "assigned": "Total asignado", "oriented_overtime": "Exceso orientado (opuesto del exceso no negativo)",
                 "oriented_undertime": "Déficit orientado (opuesto del déficit no negativo)"}
        return "".join("<div><strong>" + readable(names.get(key, key)) + "</strong>" + value_summary(item) + "</div>" for key, item in value.items())
    if isinstance(value, list):
        return "".join(value_summary(item) for item in value) if value else "<p>Lista vacía conservada.</p>"
    return "<p>" + readable(value) + "</p>"


def _state(value):
    state = value["state"]
    return {"state": state, "label_es": LABELS.get(state, "Estado conservado sin interpretación adicional")}


def presentation(bundle):
    response = bundle["response"]
    common = {"language": "es-AR", "authority": "PRESENTATION_ONLY", "notice_es": LIMIT,
              "publication_state": bundle["publication_state"],
              "selected_revision": bundle["source"]["selected_revision"],
              "selected_revision_sha256": bundle["source"]["selected_revision_sha256"],
              "source_head": bundle["source"]["head"], "authorization_to_act": "NOT_ESTABLISHED"}
    common["is_historical"] = bundle["source"]["selected_revision_sha256"] != bundle["source"]["head"]
    common["head_revision"] = bundle["source"]["revisions"][-1]["revision"]
    if response is None:
        return {**common, "notice_publication_es": "No hay un RC01 publicado en esta revisión. Los recibos previos permanecen en el historial.",
                "phase": bundle["source"]["selected_snapshot"]["phase"]}
    return {**common, "layers": {
        "transport": _state(response["transport"]), "execution": _state(response["execution"]),
        "evidence": [{"query_ref": row["query_ref"], **_state(row)} for row in response["evidence"]],
        "decision": [{"query_ref": row["query_ref"], **_state(row)} for row in response["decisions"]]},
        "closure": _state(response["closure"]),
        "quality": {key: value["state"] for key, value in response["quality"].items()},
        "unresolved_obligations": response["closure"]["unresolved_obligations"]}


def envelope(bundle, audience, source_digest):
    response = bundle["response"]
    return {"format": "genius-consumer-" + audience + "/0.1.0",
            "publication_state": bundle["publication_state"],
            "response": response, "response_sha256": sha(canonical(response)) if response is not None else None,
            "source_sha256": source_digest, "source_file": "source.json", "presentation": presentation(bundle)}


def human_document(bundle, source_digest):
    response = bundle["response"]
    source = bundle["source"]
    projected = presentation(bundle)
    parts = ["<!doctype html><html lang=\"es-AR\"><head><meta charset=\"utf-8\">",
             "<meta http-equiv=\"Content-Security-Policy\" content=\"default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'\">",
             "<meta name=\"referrer\" content=\"no-referrer\"><title>Genius · expediente local</title>",
             "<style>body{font-family:system-ui,sans-serif;max-width:1080px;margin:3rem auto;padding:0 1rem;color:#172832;background:#fafbfa}h1,h2{line-height:1.2}table{border-collapse:collapse;width:100%;margin:1rem 0}th,td{text-align:left;vertical-align:top;border:1px solid #bdc9cb;padding:.55rem;overflow-wrap:anywhere}code,.json-value{font-family:monospace;white-space:pre-wrap}aside{border-left:5px solid #21736b;padding:1rem;background:#e6f0ee}a{color:#125c74}small{display:block}dl{display:grid;grid-template-columns:minmax(8rem,1fr) 3fr;gap:.5rem}dd{margin:0}</style></head><body>",
             "<h1>Genius · expediente local</h1><aside>" + html.escape(LIMIT) + "</aside>",
             "<p>Revisión del registro: <strong>" + str(source["selected_revision"]) + "</strong>. Publicación: <code>" + bundle["publication_state"] + "</code>.</p>",
             "<p>Fuente: <code>" + source_digest + "</code>. <a href=\"source.json\" download>Expediente y referencias</a> · <a href=\"app.json\" download>Aplicación</a> · <a href=\"agent.json\" download>Agente</a></p>"]
    if projected["is_historical"]:
        parts.append("<aside><strong>Revisión histórica " + str(source["selected_revision"]) + ".</strong> El HEAD actual es la revisión " + str(projected["head_revision"]) + "; esta vista no es la última. Identidad del HEAD: <code>" + source["head"] + "</code>.</aside>")
    if response is None:
        parts.append("<h2>Sin respuesta publicada</h2><p>" + html.escape(projected["notice_publication_es"]) + "</p><p>Estado del registro: <code>" + html.escape(projected["phase"]) + "</code>.</p>")
    else:
        parts.append("<h2>Cuatro capas independientes</h2><table><thead><tr><th>Capa</th><th>Estado conservado</th></tr></thead><tbody>")
        for key, title in (("transport", "Transporte"), ("execution", "Ejecución"), ("evidence", "Evidencia"), ("decision", "Decisión")):
            rows = projected["layers"][key]
            rows = rows if isinstance(rows, list) else [rows]
            for item in rows:
                query = " · consulta " + literal(item["query_ref"]) if "query_ref" in item else ""
                parts.append("<tr><td>" + title + query + "</td><td>" + html.escape(item["label_es"]) + " <code>" + html.escape(item["state"]) + "</code></td></tr>")
        parts.append("</tbody></table><h2>Consultas, alcance y norma</h2>")
        for query in response["queries"]:
            parts.append("<p>Consulta <code>" + literal(query["id"]) + "</code>; tipo <code>" + literal(query["kind"]) + "</code>.</p><dl><dt>Alcance</dt><dd><code>" + literal(query["scope"]) + "</code></dd><dt>Norma</dt><dd><code>" + literal(query["norm"]) + "</code></dd><dt>Objeto exacto</dt><dd><code>" + literal(query["target_spec"]) + "</code></dd></dl>")
        parts.append("<h2>Resultados exactos y razones</h2>")
        for decision in response["decisions"]:
            parts.append("<p>Consulta <code>" + readable(decision["query_ref"]) + "</code>: <strong>" + html.escape(LABELS[decision["state"]]) + "</strong>. Motivo registrado: <code>" + readable(decision["reason"]) + "</code>.</p>")
            if not decision["answers"]:
                parts.append("<p>No hay una respuesta conocida publicada para esta consulta.</p>")
            for answer in decision["answers"]:
                parts.append(value_summary(answer["value"]) + "<p>Procedencia del resultado: <code>" + readable(answer["claim_source"]) + "</code>. Artefactos: " + readable(answer["artifact_refs"]) + ".</p>")
            if decision["observed_values"]:
                parts.append("<p>Valores observados, cada uno con su estado propio:</p>")
                for observed in decision["observed_values"]:
                    parts.append("<p>Operación <code>" + readable(observed["operation_id"]) + "</code>, estado <code>" + readable(observed["status"]) + "</code>.</p>" + value_summary(observed["value"]))
        parts.append("<h2>Obligaciones, responsables y dependencias</h2><table><thead><tr><th>Obligación</th><th>Estado / responsable / dependencias</th><th>Cierre y reapertura</th></tr></thead><tbody>")
        for obligation in response["obligations_ref"]["record"]["obligations"]:
            owner = obligation["owner"]
            owner_name = "Persona no asignada (UNKNOWN)" if owner["assigned_person"] == "UNKNOWN" else readable(owner["assigned_person"])
            parts.append("<tr><td><code>" + readable(obligation["id"]) + "</code><p>" + html.escape(CAUSE_LABELS[obligation["primary_cause"]]) + "</p></td><td>Estado: <code>" + readable(obligation["status"]) + "</code><p>Responsable funcional: " + readable(owner["role"]) + ". " + owner_name + ".</p><p>Tarea del responsable: " + readable(owner["task"]) + ".</p><p>Dependencias: " + (readable(obligation["dependencies"]) if obligation["dependencies"] else "Ninguna registrada") + ".</p><p>Acción siguiente registrada: " + readable(obligation["next_action"]) + "</p></td><td><p>Cierre verificado: " + ("Sí, sólo bajo el predicado registrado" if obligation["closure"]["verified"] else "No") + ".</p><p>Predicado: " + readable(obligation["closure"]["predicate"]) + ".</p><p>Condición de reapertura: " + readable(obligation["reopen"]["condition"]) + ".</p></td></tr>")
        parts.append("</tbody></table><h2>Calidad por dimensión</h2><p>No se calcula una calidad global.</p><table><thead><tr><th>Dimensión</th><th>Estado, evidencia y límite</th></tr></thead><tbody>")
        for dimension, content in sorted(response["quality"].items()):
            parts.append("<tr><td>" + html.escape(QUALITY_LABELS[dimension]) + "</td><td><strong>" + ("No evaluada" if content["state"] == "NOT_ASSESSED" else "Evaluada en el alcance registrado") + "</strong><p>Alcance: " + readable(content["scope"]) + ".</p><p>Límite: " + readable(content["limit"]) + ".</p></td></tr>")
        parts.append("</tbody></table><h2>Cierre local y reapertura</h2><p>" + html.escape(projected["closure"]["label_es"]) + ".</p><p>Próxima acción registrada: " + readable(response["closure"]["next_action"]) + "</p><p>Reapertura: " + readable(response["closure"]["reopen_condition"]) + "</p>")
    parts.append("<h2>Historial y testigos</h2><p>Los recibos de otras revisiones conservan sus propios resultados y alcances. Un fallo posterior no los reemplaza.</p><table><thead><tr><th>Revisión</th><th>Identidad / fase / publicación</th></tr></thead><tbody>")
    for entry in source["revisions"]:
        parts.append("<tr><td>" + str(entry["revision"]) + "</td><td><code>" + entry["sha256"] + "</code><br>" + literal(entry["payload"].get("phase")) + " · " + ("Respuesta publicada" if "response_ref" in entry["payload"] else "Sin respuesta publicada") + "</td></tr>")
    parts.append("</tbody></table><p>Revisiones huérfanas no promovidas: " + str(len(source["uncommitted_revisions"])) + ". Temporales no interpretados: " + str(len(source["temporary_files"])) + ".</p><ul>")
    for item in source["objects"]:
        parts.append("<li><a href=\"" + item["witness"] + "\" download>" + item["sha256"] + "</a> (" + str(item["size"]) + " bytes originales; testigo codificado en base64)</li>")
    dataset = response if response is not None else source
    parts.append("</ul><h2>Objeto completo, sin pérdida</h2><p>Las rutas son JSON Pointer. Cada celda conserva un literal JSON; las secuencias Unicode escapadas representan el valor original. Los objetos y listas vacíos también se muestran.</p><table id=\"complete-object\" data-root=\"" + ("response" if response is not None else "source") + "\"><thead><tr><th>Ruta</th><th>Valor JSON exacto</th></tr></thead><tbody>")
    for index, (pointer, value) in enumerate(leaves(dataset)):
        if index % 128 == 0:
            bundle["budget"].check()
        parts.append('<tr data-pointer="' + html.escape(pointer, quote=True) + '"><td><code>' + literal(pointer) + '</code></td><td class="json-value">' + literal(value) + '</td></tr>')
    parts.append("</tbody></table></body></html>\n")
    return "".join(parts).encode("utf-8")


def render_case(case_dir, output_dir, revision=None):
    budget = Budget()
    output = safe_path(output_dir)
    require(not output.exists(), "OUTPUT_MUST_NOT_EXIST")
    safe_path(output.parent, directory=True)
    source_root = safe_path(case_dir, directory=True)
    require(output != source_root and source_root not in output.parents, "OUTPUT_INSIDE_SOURCE_FORBIDDEN")
    bundle = read_case(source_root, revision, budget=budget)
    source_raw = canonical(bundle["source"])
    source_digest = sha(source_raw)
    staging = Path(tempfile.mkdtemp(prefix=".genius-view-", dir=output.parent))
    total = 0
    manifest = []
    try:
        def emit(relative, raw):
            nonlocal total
            budget.check()
            total += len(raw)
            require(total <= MAX_EXPORT_BYTES, "EXPORT_BYTE_BUDGET_EXHAUSTED")
            target = staging / relative
            target.parent.mkdir(exist_ok=True)
            target.write_bytes(raw)
            manifest.append({"path": relative, "sha256": sha(raw), "size": len(raw)})
        emit("source.json", source_raw)
        emit("app.json", canonical(envelope(bundle, "application", source_digest)))
        emit("agent.json", canonical(envelope(bundle, "agent", source_digest)))
        emit("human.html", human_document(bundle, source_digest))
        for record in bundle["source"]["objects"]:
            raw = bundle["store"].get_bytes(record["sha256"])
            emit(record["witness"], canonical({"format": "genius-consumer-witness/0.1.0",
                "sha256": record["sha256"], "size": len(raw), "encoding": "base64",
                "bytes": base64.b64encode(raw).decode("ascii")}))
        summary = {"format": "genius-consumer-manifest/0.1.0", "files": sorted(manifest, key=lambda item: item["path"]),
                   "publication_state": bundle["publication_state"], "source_sha256": source_digest,
                   "response_sha256": sha(canonical(bundle["response"])) if bundle["response"] is not None else None,
                   "authorization_to_act": "NOT_ESTABLISHED"}
        emit("manifest.json", canonical(summary))
        budget.check()
        require(not output.exists(), "OUTPUT_APPEARED_DURING_RENDER")
        os.rename(staging, output)
        return {"format": "genius-consumer-render-receipt/0.1.0", "publication_state": bundle["publication_state"],
                "source_sha256": source_digest, "response_sha256": summary["response_sha256"],
                "selected_revision": bundle["source"]["selected_revision"], "files": len(manifest),
                "export_bytes": total, "mathematical_conclusion": "UNCHANGED_RECEIVED_OBJECT"}
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
