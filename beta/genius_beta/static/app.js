"use strict";

// Private state stays in memory. Authentication is carried by an HttpOnly cookie.
const $ = (id) => document.getElementById(id);
const state = {user: null, csrf: null, config: null, mode: "login", view: "cases", caseId: null, detail: null, detailRaw: null, editId: null, revision: null, poll: null, rawFiles: new Map()};
const activeStates = new Set(["queued", "pending", "running", "QUEUED", "PENDING", "RUNNING"]);
const names = {transport: "Transporte", execution: "Ejecución", evidence: "Evidencia", decision: "Decisión", formal_correctness: "Corrección formal", coverage: "Cobertura", data_provenance: "Procedencia", model_fidelity: "Fidelidad del modelo", uncertainty_sensitivity: "Incertidumbre y sensibilidad", utility: "Utilidad", comprehension: "Comprensión humana", information_efficiency: "Eficiencia informativa", operation: "Operación", adoption_business: "Adopción y negocio", assigned: "Total asignado", sum: "Suma", excess: "Exceso sobre el objetivo", deficit: "Déficit respecto del objetivo", oriented_overtime: "Exceso orientado", oriented_undertime: "Déficit orientado", frontier: "Frontera", selector: "Selector"};
const labels = {PT_DELIVERED: "Solicitud recibida", PT_FAILED: "Entrega fallida", PT_NOT_ATTEMPTED: "Entrega no intentada", PE_COMPLETE: "Ejecución completada", PE_PARTIAL: "Ejecución parcial", PE_NOT_STARTED: "Ejecución no iniciada", PE_BUDGET_EXHAUSTED: "Presupuesto agotado", PE_ERROR: "Error de ejecución", PE_CANCELLED: "Ejecución cancelada", PE_UNKNOWN: "Ejecución desconocida", PR_JUSTIFIED_RESULT: "Resultado justificado en el alcance", PR_SET_OR_INCOMPARABLE: "Conjunto o incomparabilidad; sin selección", PR_PROVEN_INFEASIBLE: "Inviabilidad demostrada en el alcance", PR_PARTIAL: "Respuesta parcial", PR_DEPENDENCY: "Dependencia pendiente", PR_OUTSIDE_PROFILE: "Fuera del perfil", PR_NOT_EVALUATED: "Consulta no evaluada", EV_SUPPORTED_SCOPED: "Apoyo limitado al alcance", EV_CONDITIONAL: "Evidencia condicional", EV_CONFLICTING: "Evidencia conflictiva", EV_INSUFFICIENT: "Evidencia insuficiente", EV_OUTSIDE_SCOPE: "Fuera del alcance", EV_NOT_EVALUATED: "Evidencia no evaluada", PC_ANSWERED_SCOPED: "Consulta respondida dentro del alcance", PC_WAITING_DEPENDENCY: "A la espera de una dependencia", PC_PARTIAL: "Cierre parcial", PC_CANCELLED: "Intento cancelado", PC_BUDGET_EXHAUSTED: "Cierre por presupuesto", PC_ERROR: "Cierre por error", PC_OUTSIDE_PROFILE: "Cierre fuera del perfil", queued: "En cola", pending: "Pendiente", running: "En ejecución", succeeded: "Ejecución terminada; revisar resultado", completed: "Ejecución terminada; revisar resultado", failed: "Fallo de ejecución", error: "Error de ejecución", rejected: "Solicitud rechazada", cancelled: "Cancelado", interrupted: "Interrumpido", unknown: "Estado desconocido"};
function node(tag, text, className) {const el = document.createElement(tag); if (text !== undefined && text !== null) el.textContent = String(text); if (className) el.className = className; return el;}
function button(text, action, className = "button secondary") {const el = node("button", text, className); el.type = "button"; el.addEventListener("click", action); return el;}
function safeText(value) {if (value === undefined) return "no informado"; return typeof value === "string" ? value : JSON.stringify(value, null, 2);}
function dateText(value) {if (!value) return "Fecha no disponible"; const date = new Date(typeof value === "number" && value < 1e12 ? value * 1000 : value); return Number.isNaN(date.getTime()) ? String(value) : date.toLocaleString("es-AR", {dateStyle: "medium", timeStyle: "short"});}
function showNotice(message, error = false) {$('notice').textContent = message; $('notice').className = error ? "notice error" : "notice"; $('notice').hidden = false;}
function clearNotice() {$('notice').hidden = true;}
function fieldError(id, error) {$(id).textContent = error.message || String(error); $(id).hidden = false;}
function clearError(id) {$(id).hidden = true; $(id).textContent = "";}
async function api(path, options = {}, {expireSession = true} = {}) {
  const headers = {Accept: "application/json", ...(options.headers || {})};
  if (options.body !== undefined) headers["Content-Type"] = "application/json";
  if (state.csrf && options.method && options.method !== "GET") headers["X-CSRF-Token"] = state.csrf;
  let response;
  try {response = await fetch(path, {...options, headers, credentials: "same-origin", cache: "no-store", body: options.body === undefined ? undefined : JSON.stringify(options.body)});} catch (_) {throw new Error("No se pudo contactar con el servicio. La operación no está confirmada. Revisá tu conexión y el expediente antes de reintentar.");}
  const raw = await response.text(); let data = null;
  try {data = raw ? JSON.parse(raw) : null;} catch (_) {throw new Error("El servicio devolvió una respuesta no interpretable. No hay un resultado confirmado.");}
  if (!response.ok) {const error = new Error(data?.error?.message || "El servicio no pudo completar la solicitud."); error.status = response.status; error.code = data?.error?.code; if (expireSession && response.status === 401 && state.user) endSession("Tu sesión terminó. Volvé a ingresar para recuperar tus expedientes."); throw error;}
  return {data, raw, response};
}
async function busy(el, work) {el.disabled = true; try {return await work();} finally {el.disabled = false;}}
function download(raw, filename) {const url = URL.createObjectURL(new Blob([raw], {type: "application/json;charset=utf-8"})); const link = node("a"); link.href = url; link.download = filename; document.body.append(link); link.click(); link.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000);}
async function downloadArtifacts(jobId) {try {const response = await fetch("/api/jobs/" + encodeURIComponent(jobId) + "/artifacts", {credentials: "same-origin", cache: "no-store"}); if (!response.ok) {let message = "No se pudieron descargar los artefactos."; try {message = (await response.json()).error.message;} catch (_) {} throw new Error(message);} const blob = await response.blob(); const url = URL.createObjectURL(blob); const link = node("a"); link.href = url; link.download = "genius-artefactos-" + jobId + ".zip"; document.body.append(link); link.click(); link.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000);} catch (error) {showNotice(error.message || "No se pudo descargar el archivo.", true);}}
function confirmAction(title, copy, action) {return new Promise((resolve) => {const dialog = $('confirm-dialog'); $('confirm-title').textContent = title; $('confirm-copy').textContent = copy; $('confirm-action').textContent = action; dialog.returnValue = "cancel"; dialog.addEventListener("close", () => resolve(dialog.returnValue === "confirm"), {once: true}); dialog.showModal();});}
function stopPoll() {if (state.poll) clearTimeout(state.poll); state.poll = null;}
function hideSecret() {$('token-secret').value = ""; $('token-secret-box').hidden = true;}
function endSession(message) {stopPoll(); state.user = null; state.csrf = null; state.caseId = null; state.detail = null; state.detailRaw = null; state.rawFiles.clear(); hideSecret(); $('workspace').hidden = true; $('session').hidden = true; $('access-view').hidden = false; $('case-detail').replaceChildren(); $('cases-list').replaceChildren(); $('tokens-list').replaceChildren(); $('password').value = ""; $('case-form').reset(); resetCaseForm(); if (message) showNotice(message);}
function startSession(data) {state.user = data.user; state.csrf = data.csrf_token; $('password').value = ""; $('username-label').textContent = data.user.username; $('workspace').hidden = false; $('session').hidden = false; $('access-view').hidden = true; $('research-consent').checked = !!data.user.research_consent; $('followup-consent').checked = !!data.user.followup_consent; if (state.config?.twin_enabled && new URLSearchParams(window.location.search).get("next") === "/twin/") {window.location.assign("/twin/"); return;} return showView(new URLSearchParams(window.location.search).get("access") === "api" ? "integrations" : "cases");}
async function showView(view) {stopPoll(); hideSecret(); clearNotice(); state.view = view; for (const section of document.querySelectorAll(".app-view")) section.hidden = section.id !== view + "-view"; for (const nav of document.querySelectorAll(".nav-button")) {nav.classList.toggle("active", nav.dataset.view === view); if (nav.dataset.view === view) nav.setAttribute("aria-current", "page"); else nav.removeAttribute("aria-current");} if (view === "create" && !state.editId) resetCaseForm(); try {if (view === "cases") {state.editId = null; await loadCases();} if (view === "integrations") await loadTokens();} catch (error) {showNotice(error.message, true);} const heading = $(view + "-view")?.querySelector("h1"); if (heading) {heading.tabIndex = -1; heading.focus({preventScroll: true});}}
function privacyText() {
  const privacy = state.config?.privacy || {};
  for (const el of document.querySelectorAll(".privacy-copy")) {
    const link = node("a", "Leer el aviso completo de privacidad y transferencias internacionales");
    link.href = "/static/privacy.html"; link.target = "_blank"; link.rel = "noopener";
    el.replaceChildren(
      node("p", "Responsable: " + (privacy.controller || "no configurado")),
      node("p", "Contacto: " + (privacy.contact || "no configurado")),
      node("p", "Versión del aviso: " + (privacy.version || "no disponible")),
      node("p", "Alojamiento: Railway, región Amsterdam. Respaldos cifrados: Cloudflare R2. Estos proveedores también realizan operaciones internacionales, incluidas las de Estados Unidos; la región del disco no implica residencia exclusiva europea."),
      node("p", privacy.retention_days ? "La cuenta se elimina tras " + privacy.retention_days + " días sin acceso; cada expediente, tras " + privacy.retention_days + " días desde su última actualización o solicitud de ejecución. Los respaldos se conservan 7 días y el registro de supresiones 8 días, con la excepción de transición explicada en el aviso." : "Plazo de conservación no disponible."),
      link
    );
  }
}
function resetCaseForm() {state.editId = null; state.rawFiles.clear(); $('case-form').reset(); if ($('choice-fields').dataset.ready) GeniusChoice.reset(); $('profile').disabled = false; $('create-heading').textContent = "Nueva consulta"; $('case-submit').textContent = "Guardar y revisar"; $('assignments').replaceChildren(); addAssignment("task1", ""); addAssignment("task2", ""); $('synthetic-notice').hidden = true; for (const name of ["input", "result", "certificate"]) $(name + "-file-status").textContent = ""; clearError("case-error"); toggleProfile();}
function toggleProfile() {const choice = $("profile").value === "choice"; $("choice-fields").hidden = !choice; const hours = $('profile').value === "hours"; $('hours-fields').hidden = !hours; $('fdq-fields').hidden = hours || choice; for (const el of $('hours-fields').querySelectorAll("input")) el.disabled = !hours; for (const el of $('fdq-fields').querySelectorAll("textarea")) {el.disabled = hours || choice; el.required = !hours && !choice;}}
let assignmentCounter = 0;
function addAssignment(id = "", credit = "") {if ($('assignments').children.length >= 100) {showNotice("Este perfil admite hasta 100 asignaciones.", true); return;} const index = ++assignmentCounter; const row = node("div", null, "assignment"); const left = node("div"); const label = node("label", "Identificador sin datos personales"); label.htmlFor = "assignment-id-" + index; const idInput = node("input"); idInput.id = label.htmlFor; idInput.value = id; idInput.required = true; idInput.maxLength = 64; idInput.pattern = "[A-Za-z0-9_\\-]+"; idInput.dataset.field = "id"; left.append(label, idInput); const right = node("div"); const creditLabel = node("label", "Crédito (vacío = desconocido)"); creditLabel.htmlFor = "assignment-credit-" + index; const creditInput = node("input"); creditInput.id = creditLabel.htmlFor; creditInput.value = credit ?? ""; creditInput.maxLength = 64; creditInput.dataset.field = "credit"; creditInput.placeholder = "Ej.: 7/2"; right.append(creditLabel, creditInput); const remove = button("×", () => {if ($('assignments').children.length === 1) showNotice("Conservá al menos una asignación.", true); else row.remove();}, "remove-button"); remove.setAttribute("aria-label", "Quitar asignación " + index); row.append(left, right, remove); $('assignments').append(row);}
function readInput() {const input = {permission_confirmed: $('permission-confirmed').checked, scope_acknowledged: $('scope-acknowledged').checked, evidence_origin: $('provenance').value}; if ($('profile').value === 'choice') return {...input,...GeniusChoice.read()}; if ($('profile').value === "hours") {input.assignments = [...$('assignments').children].map((row) => ({id: row.querySelector('[data-field="id"]').value.trim(), credit: row.querySelector('[data-field="credit"]').value.trim() || null})); input.target = $('target').value.trim() || null;} else {input.query_kind = $('query-kind').value; for (const key of ["input", "result", "certificate"]) {const text = state.rawFiles.has(key) ? state.rawFiles.get(key) : $(key + "-json").value; if (!text.trim()) throw new Error("Completá los tres documentos JSON del paquete FDQ."); input[key + "_json"] = text;}} return input;}
async function loadCases() {const area = $('cases-list'); area.replaceChildren(node("p", "Cargando expedientes…", "muted")); const {data} = await api("/api/cases"); area.replaceChildren(); if (!data.cases?.length) {const empty = node("div", null, "empty-state"); if (state.config?.twin_enabled) {const link = node("a", "Modelar un sistema en el gemelo", "button primary"); link.href = "/twin/"; empty.append(node("span", "◎", "empty-icon"), node("h2", "Empezá por el gemelo dinámico"), node("p", "Modelá un sistema real y evaluá sus políticas por perfil funcional, capacidad generativa, bienestar y probabilidad de vida sostenida. Los perfiles formales siguen disponibles en el menú."), link);} else empty.append(node("span", "▤", "empty-icon"), node("h2", "Tu primer expediente empieza acá"), node("p", "Guardá una consulta para ejecutar el motor y conservar el resultado."), button("Crear mi primera consulta", () => showView("create"), "button primary")); area.append(empty); return;} for (const item of data.cases) {const row = button("", () => openCase(item.id), "case-row"); const text = node("span"); text.append(node("strong", item.title), node("span", (item.profile === "choice" ? "Decisión cotidiana" : item.profile === "hours" ? "Créditos formales" : "FDQ formal") + " · Revisión " + item.current_revision + " · " + dateText(item.updated_at || item.created_at), "row-meta")); row.append(text, node("span", "→", "row-arrow")); area.append(row);}}
async function openCase(id, preserveRevision = false) {state.caseId = id; state.detail = null; state.detailRaw = null; if (!preserveRevision) state.revision = null; await showView("detail"); $('case-detail').replaceChildren(node("p", "Recuperando expediente…", "muted")); await refreshCase();}
async function refreshCase() {stopPoll(); const id = state.caseId; if (!id || state.view !== "detail") return; try {const result = await api("/api/cases/" + encodeURIComponent(id)); if (state.caseId !== id || state.view !== "detail") return; const changed = state.detailRaw !== result.raw; const wasActive = state.detail?.jobs?.some(job => activeStates.has(job.status)); const isActive = result.data.jobs?.some(job => activeStates.has(job.status)); if (wasActive && !isActive) showNotice("El intento de ejecución terminó. Revisá sus estados y resultados antes de sacar una conclusión."); state.detail = result.data; state.detailRaw = result.raw; if (changed) renderDetail(); if (!document.hidden && (result.data.jobs || []).some((job) => activeStates.has(job.status))) state.poll = setTimeout(refreshCase, 1500);} catch (error) {showNotice(error.message, true);}}
function details(title, raw, help) {const block = node("details", null, "result-details"); block.append(node("summary", title)); if (help) block.append(node("p", help, "field-help")); block.append(node("pre", typeof raw === "string" ? raw : safeText(raw))); return block;}
function renderValue(value, parent, title) {const block = node("div", null, "value-item"); if (title) block.append(node("h3", names[title] || title)); if (value && typeof value === "object" && !Array.isArray(value) && value.state) {const status = value.state; if (status === "PV_UNKNOWN") {block.append(node("strong", "Desconocido"), node("p", (value.reasons || []).join(" · ")), node("p", "Obligaciones: " + safeText(value.obligation_refs || []), "muted"));} else if (status === "PV_KNOWN") {block.append(node("strong", typeof value.value === "string" ? value.value : safeText(value.value)), node("p", "Unidad: " + (value.unit || "según el recibo") + ". Base: " + safeText(value.basis || []), "muted")); if (value.value?.selector?.state === "OUTSIDE_DOMAIN") block.append(node("p", "No hay un selector definido bajo la norma recibida. Eso no implica que la frontera esté vacía.")); if (value.value?.frontier) block.append(node("p", "La frontera conserva un conjunto; no selecciona un ganador."));} else {block.append(node("strong", status === "PV_NOT_APPLICABLE" ? "No aplicable" : status === "PV_OUTSIDE_PROFILE" ? "Fuera del perfil" : status), node("p", safeText(value.reasons || value)));}} else if (value && typeof value === "object" && !Array.isArray(value)) {for (const [key, child] of Object.entries(value)) renderValue(child, block, key);} else {block.append(node("p", safeText(value)));} parent.append(block);}
const humanPhrases = {
  "Use only the answered scoped conclusions; new purposes require a new query.": "Usá las conclusiones sólo para la consulta y el alcance respondidos. Para otro propósito, creá una consulta nueva.",
  "Continue only with a pertinent new input, rule, query, permission or budget and a linked revision.": "Continuá con una versión nueva cuando cambien datos, reglas, consulta, permisos o presupuesto relevantes.",
  "A relevant premise, source, query, support, rule, permission or capability changes.": "Reabrí el caso si cambia una premisa, fuente, consulta, respaldo, regla, permiso o capacidad relevante.",
  "Pertinent change of source, query, rule or scope under a future explicit revision": "Creá una revisión explícita si cambia la fuente, consulta, regla o alcance.",
  "Supply compatible formal premises and resolve unknown inputs": "Aportar premisas formales compatibles y completar los datos desconocidos.",
  "Run the bounded operation or retain an explicit dependency": "Ejecutar la operación dentro de sus límites o conservar la dependencia pendiente.",
  "EXACT_SCOPED_QUERY_VERIFIED": "La consulta exacta fue verificada dentro de su alcance.",
  "submitting-consumer": "Persona o aplicación que aporta los datos",
  "DERIVABLE": "Información derivable bajo la regla declarada",
  "DATO_EXTERNO": "Dato externo pendiente",
  "COMPUTO_PENDIENTE": "Cálculo pendiente",
  "DEFINICION_MODELO": "Definición o admisión del modelo pendiente",
  "PREFERENCIA": "Preferencia o norma de selección pendiente",
  "DISENO_ESTUDIO": "Diseño del estudio pendiente",
  "CAPACIDAD_AUSENTE": "Capacidad requerida no disponible",
  "CLOSED_SCOPED": "Cerrada dentro del alcance", "OPEN": "Abierta", "BLOCKED": "Bloqueada", "DEFERRED": "Diferida"
};
function phrase(value) {return typeof value === "string" ? humanPhrases[value] || value : safeText(value);}
function mainValue(value, target) {
  if (value && typeof value === "object" && !value.state && (value.assigned || value.sum || value.deficit || value.excess)) {
    const grid = node("div", null, "metric-grid");
    for (const key of [value.assigned ? "assigned" : "sum", "deficit", "excess"]) {
      const metric = value[key]; if (!metric) continue;
      const card = node("div", null, "metric-card"); card.append(node("span", names[key], "metric-label"));
      if (metric.state === "PV_KNOWN") {const exact = typeof metric.value === "string" ? metric.value.replace(/^(-?\d+)\/1$/, "$1") : safeText(metric.value); card.append(node("strong", exact, "metric-number"), node("span", metric.unit || "Unidad según recibo", "field-help"));}
      else {card.append(node("strong", metric.state === "PV_UNKNOWN" ? "Desconocido" : metric.state === "PV_NOT_APPLICABLE" ? "No aplicable" : metric.state === "PV_OUTSIDE_PROFILE" ? "Fuera de perfil" : metric.state, "metric-unknown"), node("p", (metric.reasons || []).map(phrase).join(" · "), "field-help")); if (metric.obligation_refs?.length) card.append(node("p", "Pendiente: " + metric.obligation_refs.join(", "), "field-help"));}
      grid.append(card);
    }
    target.append(grid, node("p", "Créditos formales según los datos y la regla declarados. No representan horas trabajadas ni una evaluación de bienestar.", "field-help"));
  } else renderValue(value, target);
}
function renderResponse(output, target, exactOutput) {
  if(output.format === "genius-declared-choice/1") {GeniusChoice.render(output,target);return;}
  const response = output.response;
  if (!response) {target.append(node("div", "Este intento no tiene un recibo RC01 publicado. Conservá el estado operativo y la causa registrada.", "callout warning")); return;}
  const presentation = output.presentation || {};
  target.append(node("div", "Resultado formal y condicionado a los datos aportados. No prueba su correspondencia con el mundo real ni autoriza una intervención. Un dato desconocido no es cero.", "callout"));
  if (output.evidence_origin === "synthetic") target.append(node("p", "Ejemplo sintético · prueba de operación, no evidencia de campo.", "field-help"));
  for (const query of response.queries || []) {
    const card = node("section", null, "card result-card");
    card.append(node("h2", query.kind === "component" ? "Resultado · créditos formales" : "Resultado · consulta " + query.id));
    for (const decision of (response.decisions || []).filter(item => item.query_ref === query.id)) {
      card.append(node("h3", labels[decision.state] || decision.state));
      const hasAnswers = !!decision.answers?.length;
      if (!hasAnswers) card.append(node("p", "No hay una respuesta completa conocida para esta consulta."));
      for (const answer of decision.answers || []) mainValue(answer.value, card);
      if (!hasAnswers && decision.observed_values?.length) {
        card.append(node("h3", "Valores parciales observados"));
        for (const observation of decision.observed_values) mainValue(observation.value, card);
      }
      const technical = node("details", null, "result-details");
      technical.append(node("summary", "Detalle técnico y valores observados"), node("p", "Motivo: " + phrase(decision.reason), "field-help"));
      for (const answer of decision.answers || []) {renderValue(answer.value, technical); technical.append(node("p", "Procedencia: " + safeText(answer.claim_source) + ". Artefactos: " + safeText(answer.artifact_refs || []), "field-help"));}
      for (const observation of decision.observed_values || []) {technical.append(node("h3", "Valor observado · " + observation.status)); renderValue(observation.value, technical);}
      card.append(technical);
    }
    card.append(details("Alcance, norma y objeto exacto", {query: query.id, kind: query.kind, scope: query.scope, norm: query.norm, target_spec: query.target_spec}));
    target.append(card);
  }
  const grid = node("div", null, "layer-grid");
  for (const key of ["transport", "execution", "evidence", "decision"]) {
    const block = node("div", null, "layer"); block.append(node("h3", names[key]));
    let source = key === "decision" ? response.decisions : response[key]; source = Array.isArray(source) ? source : [source];
    for (const row of source) {if (!row) continue; block.append(node("strong", labels[row.state] || row.state), node("code", (row.query_ref ? row.query_ref + " · " : "") + row.state));}
    grid.append(block);
  }
  target.append(node("h2", "Cuatro capas del resultado"), grid);
  const closure = response.closure || {}, obligations = response.obligations_ref?.record?.obligations || [];
  const unresolved = node("section", null, "card result-card");
  unresolved.append(node("h2", "Pendientes y próxima acción"), node("p", labels[closure.state] || closure.state || "Cierre no informado"), node("p", phrase(closure.next_action)), node("p", phrase(closure.reopen_condition), "field-help"));
  const completed = node("details", null, "result-details"); completed.append(node("summary", "Obligaciones resueltas y trazabilidad")); let hasCompleted = false;
  if (Array.isArray(closure.unresolved_obligations) && !closure.unresolved_obligations.length) unresolved.append(node("p", "Sin obligaciones pendientes en este recibo.", "field-help"));
  for (const obligation of obligations) {
    const block = node("div", null, "obligation");
    block.append(node("strong", obligation.id + " · " + phrase(obligation.status)), node("p", "Causa: " + phrase(obligation.primary_cause)), node("p", "Responsable: " + phrase(obligation.owner?.role || "desconocido") + ". Persona: " + (obligation.owner?.assigned_person === "UNKNOWN" ? "no asignada" : obligation.owner?.assigned_person || "no asignada") + "."), node("p", "Tarea: " + phrase(obligation.owner?.task)), node("p", "Dependencias: " + (obligation.dependencies?.length ? safeText(obligation.dependencies) : "ninguna registrada")), node("p", "Próxima acción: " + phrase(obligation.next_action)), node("p", "Cierre verificado: " + (obligation.closure?.verified ? "sí, sólo bajo el predicado registrado" : "no")), node("p", "Reapertura: " + phrase(obligation.reopen?.condition)));
    if (obligation.closure?.verified) {completed.append(block); hasCompleted = true;} else unresolved.append(block);
  }
  if (hasCompleted) unresolved.append(completed);
  unresolved.append(node("p", "Para continuar con nuevos datos, guardá otra versión y solicitá su ejecución. Este intento no permanece trabajando en segundo plano.", "field-help"));
  target.append(unresolved);
  if (presentation.notice_es) target.append(details("Alcances y límites completos del recibo R3", presentation.notice_es));
  const quality = node("details", null, "result-details"); quality.append(node("summary", "Calidad por dimensión · sin puntaje global"));
  const table = node("table", null, "quality-table"), tbody = node("tbody");
  for (const [key, value] of Object.entries(response.quality || {})) {const tr = node("tr"), th = node("th", names[key] || key), td = node("td"); th.scope = "row"; td.append(node("strong", value.state === "NOT_ASSESSED" ? "No evaluada" : value.state), node("p", "Alcance: " + safeText(value.scope)), node("p", "Límite: " + safeText(value.limit))); tr.append(th, td); tbody.append(tr);}
  table.append(tbody); quality.append(table); target.append(quality);
  const exact = output.response_json || exactOutput;
  target.append(details(exactOutput ? "Recibo RC01 y salida completa · JSON íntegro" : "Recibo RC01 completo", exact || response, exact ? "JSON íntegro recibido del servidor, sin convertir sus números ni modificar los valores. El campo response conserva el recibo RC01 completo." : "Objeto completo del resultado. Para conservar los bytes y enteros originales, descargá el expediente JSON mediante el botón Exportar expediente."));
  if (exact) target.append(button("Descargar salida y RC01", () => download(exact, "genius-resultado-" + state.caseId + ".json"), "text-button"));
}
function renderDetail() {const data = state.detail, info = data.case, area = $('case-detail'); area.replaceChildren(); const revision = state.revision || info.current_revision; state.revision = revision; const heading = node("div", null, "detail-heading"); heading.append(node("p", "EXPEDIENTE PRIVADO", "eyebrow"), node("h1", info.title)); const meta = node("div", null, "meta-strip"); meta.append(node("span", info.profile === "choice" ? "Decisión cotidiana · comparación declarada" : info.profile === "hours" ? "Créditos formales · h_contractual" : "FDQ · verificación formal"), node("span", "ID: " + info.id), node("span", "Creado: " + dateText(info.created_at))); heading.append(meta); area.append(heading);
  const revisions = data.revisions || []; const selectLabel = node("label", "Versión del expediente"); selectLabel.htmlFor = "revision-select"; const select = node("select"); select.id = "revision-select"; for (const entry of revisions) {const option = node("option", "Revisión " + entry.version + (entry.version === info.current_revision ? " · actual" : " · histórica") + " · " + dateText(entry.created_at)); option.value = entry.version; select.append(option);} select.value = String(revision); select.addEventListener("change", () => {state.revision = Number(select.value); renderDetail();}); area.append(selectLabel, select); if (revision !== info.current_revision) area.append(node("div", "Estás viendo una revisión histórica. Los resultados pertenecen a esa versión, no a la actual.", "callout warning"));
  const toolbar = node("div", null, "detail-toolbar"); const running = (data.jobs || []).find((job) => activeStates.has(job.status)); const previous = [...(data.jobs || [])].reverse().find(job => job.revision === revision); const retry = previous && !activeStates.has(previous.status) && previous.status !== "completed"; const run = button(running ? "Ejecución en curso" : previous?.status === "completed" ? "Resultado de esta versión recibido" : retry ? "Reintentar ejecución" : "Admitir y ejecutar esta versión", async (event) => {clearNotice(); await busy(event.currentTarget, async () => {try {await api("/api/cases/" + encodeURIComponent(info.id) + "/run", {method: "POST", body: {revision, ...(retry ? {retry: true} : {})}}); await refreshCase();} catch (error) {showNotice(error.message, true);}});}, "button primary"); run.disabled = !!running || previous?.status === "completed"; toolbar.append(run, button("Editar datos", () => editCase(revision)), button("Exportar expediente", () => download(state.detailRaw, "genius-expediente-" + info.id + ".json")), button("Borrar", async () => {if (await confirmAction("¿Borrar este expediente?", "Se eliminarán sus versiones, resultados y feedback. Esta acción no se puede deshacer desde la aplicación.", "Borrar expediente")) {try {await api("/api/cases/" + encodeURIComponent(info.id), {method: "DELETE"}); state.caseId = null; await showView("cases"); showNotice("Expediente eliminado.");} catch (error) {showNotice(error.message, true);}}}, "button danger")); area.append(toolbar);
  const entry = revisions.find((item) => item.version === revision); if (entry) area.append(details("Datos guardados en esta versión", entry.input)); const jobs = (data.jobs || []).filter((job) => job.revision === revision); if (!jobs.length) {area.append(node("div", "Datos guardados. Todavía no se solicitó la admisión y ejecución de esta versión. El motor comprobará el perfil y las dependencias al ejecutarla.", "callout"));} else {for (let index = jobs.length - 1; index >= 0; index--) {const job = jobs[index]; const jobArea = node("section", null, "job"); jobArea.append(node("h2", "Intento de ejecución"), node("p", "Trabajo " + job.id + " · " + dateText(job.created_at), "field-help"), node("span", labels[job.status] || job.status, "badge" + (activeStates.has(job.status) ? " pending" : ["failed", "rejected", "error", "interrupted"].includes(job.status) ? " error" : ""))); if (activeStates.has(job.status)) {jobArea.append(node("p", "El servidor conserva este trabajo. Podés salir y recuperar su estado después. Esta pantalla consulta el estado mientras permanece abierta.", "field-help"), button("Cancelar este intento", async () => {try {await api("/api/jobs/" + encodeURIComponent(job.id) + "/cancel", {method: "POST", body: {}}); await refreshCase();} catch (error) {showNotice(error.message, true);}}, "text-button"));} if (job.admission?.status === "rejected") {const admission = node("div", null, "callout warning"); admission.append(node("strong", "Admisión rechazada"), node("p", "El caso no pudo admitirse bajo el perfil recibido. Causa: " + job.admission.reason + ". Corregí los datos o el paquete antes de crear una versión nueva.")); jobArea.append(admission);} if (job.error) jobArea.append(node("div", "Causa registrada: " + safeText(job.error) + ". Esto no demuestra inviabilidad de la consulta.", "callout warning")); if (job.result) {renderResponse(job.result, jobArea, job.result_json); if (job.artifacts) jobArea.append(button("Descargar artefactos verificables (ZIP)", () => downloadArtifacts(job.id), "text-button"));} else if (!activeStates.has(job.status)) jobArea.append(node("p", "No se publicó un resultado matemático para este intento.", "field-help")); area.append(jobArea);}}
  if (!running) renderFeedback(data, area);}
async function editCase(revision) {const entry = state.detail.revisions.find((row) => row.version === revision); if (!entry) return; resetCaseForm(); state.editId = state.detail.case.id; await showView("create"); $('create-heading').textContent = "Nueva versión de la consulta"; $('case-submit').textContent = "Guardar nueva versión"; $('case-title').value = state.detail.case.title; $('profile').value = state.detail.case.profile; $('profile').disabled = true; const input = entry.input; $('provenance').value = input.evidence_origin || "user_declared"; if ($('profile').value === 'choice') {GeniusChoice.load(input);} else if ($('profile').value === "hours") {$('assignments').replaceChildren(); for (const assignment of input.assignments || []) addAssignment(assignment.id, assignment.credit); $('target').value = input.target ?? "";} else {$('query-kind').value = input.query_kind || "frontier"; for (const key of ["input", "result", "certificate"]) {const raw = input[key + "_json"] || ""; state.rawFiles.set(key, raw); $(key + "-json").value = raw; $(key + "-file-status").textContent = "Documento de la versión anterior; cadena original conservada hasta que la edites.";}} $('scope-acknowledged').checked = false; $('permission-confirmed').checked = false; toggleProfile();}
function renderFeedback(data, target) {const section = node("section", null, "card result-card"); section.append(node("h2", "¿Cómo fue tu experiencia con esta consulta?"), node("p", "Tu feedback es voluntario. No acredita por sí solo comprensión humana ni eficacia decisional. Evitá incluir datos personales.")); const form = node("form", null, "feedback-form"); const label = node("label", "Claridad percibida (opcional)"); label.htmlFor = "feedback-rating"; const rating = node("select"); rating.id = "feedback-rating"; for (const [value, text] of [["", "Prefiero no puntuar"], ["1", "1 · Nada claro"], ["2", "2 · Poco claro"], ["3", "3 · Intermedio"], ["4", "4 · Claro"], ["5", "5 · Muy claro"]]) {const option = node("option", text); option.value = value; rating.append(option);} const commentLabel = node("label", "¿Qué entendiste y qué te faltó? (opcional)"); commentLabel.htmlFor = "feedback-comment"; const comment = node("textarea"); comment.id = "feedback-comment"; comment.rows = 3; comment.maxLength = 2000; const submit = node("button", "Guardar feedback", "button secondary"); submit.type = "submit"; const errorBox = node("p", "", "form-error"); errorBox.hidden = true; errorBox.setAttribute("role", "alert"); const choiceFeedback = data.case.profile === "choice" ? GeniusChoice.feedback(form) : null; form.append(label, rating, commentLabel, comment, submit, errorBox); form.addEventListener("submit", async (event) => {event.preventDefault(); errorBox.hidden = true; await busy(submit, async () => {try {await api("/api/cases/" + encodeURIComponent(data.case.id) + "/feedback", {method: "POST", body: {job_id: [...(data.jobs || [])].reverse().find(job => job.revision === state.revision)?.id || null, rating: rating.value ? Number(rating.value) : null, comment: comment.value, understanding: {revision: state.revision, kind: "self_report_not_validated", decision_review: choiceFeedback ? choiceFeedback() : undefined}}}); await refreshCase(); showNotice("Feedback guardado. Tus opciones de investigación y seguimiento no cambiaron.");} catch (error) {errorBox.textContent = error.message; errorBox.hidden = false;}});}); section.append(form); const privacyLink = button("Revisar consentimientos separados", () => showView("account"), "text-button"); section.append(node("p", "Investigación: " + (state.user.research_consent ? "autorizada" : "desactivada") + ". Seguimiento: " + (state.user.followup_consent ? "autorizado" : "desactivado") + ".", "field-help"), privacyLink); if (data.feedback?.length) section.append(details("Feedback ya registrado (" + data.feedback.length + ")", data.feedback)); target.append(section);}
async function loadTokens() {const {data} = await api("/api/tokens"); const area = $('tokens-list'); area.replaceChildren(); if (!data.tokens?.length) area.append(node("p", "Todavía no hay claves activas.", "muted")); for (const token of data.tokens || []) {const row = node("div", null, "token-row"), text = node("div"); text.append(node("strong", token.label), node("small", "Creada: " + dateText(token.created_at) + " · Último uso: " + (token.last_used_at ? dateText(token.last_used_at) : "no registrado"))); row.append(text, button("Revocar", async () => {if (await confirmAction("¿Revocar esta clave?", "Las aplicaciones que usan «" + token.label + "» dejarán de poder acceder. Podés crear una clave nueva después.", "Revocar clave")) {try {await api("/api/tokens/" + encodeURIComponent(token.id), {method: "DELETE"}); hideSecret(); await loadTokens(); showNotice("Clave revocada.");} catch (error) {showNotice(error.message, true);}}}, "button danger")); area.append(row);}}
function clearAuthField(field) {
  clearError(field + "-error");
  $(field).removeAttribute("aria-invalid");
}
function showAuthFieldError(field, error) {
  fieldError(field + "-error", error);
  $(field).setAttribute("aria-invalid", "true");
  $(field).focus();
}
function authFieldMessage(field) {
  const value = $(field).value;
  if (field === "username") {
    if (value.includes("@")) return "Usuario: elegí un alias, no un correo electrónico. Por ejemplo: usuario_42.";
    if (!/^[A-Za-z0-9_-]{3,40}$/.test(value)) return "Usuario: usá de 3 a 40 letras sin acentos, números, guiones o guiones bajos; sin espacios.";
  } else {
    const minimum = state.mode === "register" ? 12 : 1;
    if (Array.from(value).length < minimum || Array.from(value).length > 128) return "Contraseña: usá entre " + minimum + " y 128 caracteres. Se permiten símbolos y espacios.";
  }
  return "";
}
function setMode(mode) {
  if (mode === "register" && !state.config?.registration_open) return;
  state.mode = mode;
  const register = mode === "register";
  $('auth-heading').textContent = register ? "Creá tu espacio" : "Entrá a Genius";
  $('mode-login').setAttribute("aria-pressed", String(!register));
  $('mode-register').setAttribute("aria-pressed", String(register));
  $('registration-info').hidden = !register;
  $('privacy-accepted').required = register;
  $('adult-confirmed').required = register;
  $('password').autocomplete = register ? "new-password" : "current-password";
  $('password').minLength = register ? 12 : 1;
  $('auth-submit').textContent = register ? "Crear cuenta →" : "Ingresar →";
  clearError("auth-error");
  for (const field of ["username", "password"]) clearAuthField(field);
}
document.querySelectorAll("[data-view]").forEach((el) => el.addEventListener("click", () => {state.editId = null; showView(el.dataset.view);}));
$('mode-login').addEventListener("click", () => setMode("login"));
$('mode-register').addEventListener("click", () => setMode("register"));
for (const field of ["username", "password"]) $(field).addEventListener("input", () => {
  clearAuthField(field);
  clearError("auth-error");
});
$('auth-form').addEventListener("submit", async (event) => {
  event.preventDefault();
  clearError("auth-error");
  for (const field of ["username", "password"]) clearAuthField(field);
  $('username').value = $('username').value.trim();
  for (const field of ["username", "password"]) {
    const message = authFieldMessage(field);
    if (message) {showAuthFieldError(field, new Error(message)); return;}
  }
  // Native validity still enforces the required consent checkboxes.
  if (!event.currentTarget.reportValidity()) return;
  await busy($('auth-submit'), async () => {
    try {
      const body = {username: $('username').value, password: $('password').value};
      if (state.mode === "register") Object.assign(body, {
        privacy_accepted: $('privacy-accepted').checked,
        privacy_version: state.config?.privacy?.version,
        adult_confirmed: $('adult-confirmed').checked,
        research_consent: false,
        followup_consent: false
      });
      const {data} = await api("/api/" + (state.mode === "register" ? "register" : "login"), {method: "POST", body});
      await startSession(data);
    } catch (error) {
      if (["invalid_username", "username_unavailable"].includes(error.code)) showAuthFieldError("username", error);
      else if (error.code === "invalid_password") showAuthFieldError("password", error);
      else fieldError("auth-error", error);
    }
  });
});
$('logout').addEventListener("click", async () => {try {await api("/api/logout", {method: "POST", body: {}}); endSession("Sesión cerrada.");} catch (error) {showNotice(error.message, true);}});
$('profile').addEventListener("change", toggleProfile); $('add-assignment').addEventListener("click", () => {const used = new Set([...$('assignments').querySelectorAll('[data-field="id"]')].map(el => el.value)); let i = 1; while (used.has('task' + i)) i++; addAssignment('task' + i, '');});
$('synthetic-example').addEventListener("click", () => {$('assignments').replaceChildren(); addAssignment("task1", "13/2"); addAssignment("task2", "15/2"); $('target').value = "15"; $('provenance').value = "synthetic"; $('synthetic-notice').hidden = false; if (!$('case-title').value) $('case-title').value = "Ejemplo sintético de créditos";});
document.querySelectorAll("[data-example]").forEach((el) => el.addEventListener("click", async () => {clearError("case-error"); if (state.editId && ((el.dataset.example.startsWith("choice") && $("profile").value !== "choice") || (el.dataset.example.startsWith("hours") && $('profile').value !== "hours") || (el.dataset.example.startsWith("fdq") && $('profile').value !== "fdq"))) {fieldError("case-error", new Error("Para cambiar de perfil, creá una consulta nueva.")); return;} await busy(el, async () => {try {const {data} = await api("/api/examples/" + el.dataset.example); const example = data.input || data; $('profile').value = data.profile || example.profile; $('provenance').value = "synthetic"; $('scope-acknowledged').checked = false; $('permission-confirmed').checked = false; if (!$('case-title').value) $('case-title').value = "Ejemplo sintético · " + el.dataset.example; if ($('profile').value === 'choice') {GeniusChoice.load(example);} else if ($('profile').value === "hours") {$('assignments').replaceChildren(); for (const row of example.assignments) addAssignment(row.id, row.credit); $('target').value = example.target ?? ""; $('synthetic-notice').hidden = false;} else {$('query-kind').value = example.query_kind; for (const key of ["input", "result", "certificate"]) {state.rawFiles.set(key, example[key + "_json"]); $(key + "-json").value = example[key + "_json"]; $(key + "-file-status").textContent = "Ejemplo sintético. Documento original conservado hasta que edites el texto.";}} toggleProfile(); showNotice("Ejemplo sintético cargado. Revisalo y aceptá las condiciones sólo si corresponde; todavía no se guardó ni ejecutó.");} catch (error) {fieldError("case-error", error);}});}));
for (const key of ["input", "result", "certificate"]) {$(key + "-json").addEventListener("input", () => {state.rawFiles.delete(key); $(key + "-file-status").textContent = "Texto editado. Se enviará el contenido visible; su certificado debe corresponder a esos bytes.";}); $(key + "-file").addEventListener("change", async (event) => {const file = event.target.files[0]; if (!file) return; try {if (file.size > 110000) throw new Error("El archivo supera 110000 bytes. Los tres documentos juntos deben caber en la entrada máxima de 110000 bytes JSON."); const bytes = await file.arrayBuffer(); const raw = new TextDecoder("utf-8", {fatal: true, ignoreBOM: true}).decode(bytes); state.rawFiles.set(key, raw); $(key + "-json").value = raw; $(key + "-file-status").textContent = file.name + " · " + file.size + " bytes. Original conservado hasta que edites el texto.";} catch (error) {state.rawFiles.delete(key); event.target.value = ""; $(key + "-json").value = ""; $(key + "-file-status").textContent = "No se cargó un documento válido."; fieldError("case-error", error);}});}
$('case-form').addEventListener("submit", async (event) => {event.preventDefault(); clearError("case-error"); await busy($('case-submit'), async () => {try {const input = readInput(); if (new TextEncoder().encode(JSON.stringify(input)).length > 110000) throw new Error("La entrada completa supera 110000 bytes JSON. Reducí el paquete sin alterar su integridad."); const title = $('case-title').value.trim(); let id = state.editId; if (id) await api("/api/cases/" + encodeURIComponent(id), {method: "PATCH", body: {title, input}}); else {const {data} = await api("/api/cases", {method: "POST", body: {title, profile: $('profile').value, consumer_type: "human", input}}); id = data.case.id;} state.editId = null; await openCase(id); showNotice("Datos guardados. Revisá la versión y solicitá la ejecución cuando esté lista.");} catch (error) {fieldError("case-error", error);}});});
$('token-form').addEventListener("submit", async (event) => {event.preventDefault(); clearError("token-error"); const submit = event.currentTarget.querySelector('button[type="submit"]'); await busy(submit, async () => {try {const {data} = await api("/api/tokens", {method: "POST", body: {label: $('token-label').value.trim()}}); $('token-secret').value = data.token; $('token-secret-box').hidden = false; $('token-label').value = ""; await loadTokens(); $('token-secret').focus(); $('token-secret').select();} catch (error) {fieldError("token-error", error);}});});
$('dismiss-secret').addEventListener("click", hideSecret);
$('consent-form').addEventListener("submit", async (event) => {event.preventDefault(); const submit = event.currentTarget.querySelector('button[type="submit"]'); await busy(submit, async () => {try {const body = {research_consent: $('research-consent').checked, followup_consent: $('followup-consent').checked}; const {data} = await api("/api/me", {method: "PATCH", body}); Object.assign(state.user, data?.user || body); showNotice("Preferencias guardadas. No se inició ningún estudio ni contacto automático.");} catch (error) {showNotice(error.message, true);}});});
$('export-account').addEventListener("click", async (event) => {await busy(event.currentTarget, async () => {try {const {raw} = await api("/api/export"); download(raw, "genius-mis-datos.json");} catch (error) {showNotice(error.message, true);}});});
$('delete-account').addEventListener("click", async () => {if (await confirmAction("¿Eliminar la cuenta y sus datos?", "Se eliminarán tu cuenta, expedientes y claves. No podrás recuperarlos desde la aplicación. Descargá primero una exportación si necesitás conservarlos.", "Eliminar mi cuenta")) {try {await api("/api/me", {method: "DELETE"}); endSession("Cuenta y datos activos eliminados.");} catch (error) {showNotice(error.message, true);}}});
document.addEventListener("visibilitychange", () => {if (document.hidden) {hideSecret(); stopPoll();} else if (state.user && state.view === "detail") refreshCase();});
async function initialize() {GeniusChoice.init(api); $("choice-fields").dataset.ready="true"; $("mode-register").disabled = true; resetCaseForm(); try {const {data} = await api("/api/config"); state.config = data; $("twin-link").hidden = !data.twin_enabled; $("mode-register").disabled = !data.registration_open; privacyText(); if (data.suspended) {$('service-notice').textContent = "Servicio suspendido. Las nuevas ejecuciones no están disponibles. El acceso a datos depende de la configuración del servicio."; $('service-notice').hidden = false;} else if (!data.registration_open) {$("service-notice").textContent = "Las nuevas cuentas todavía no están habilitadas. Si ya tenés una cuenta, podés ingresar."; $("service-notice").hidden = false;} else if (data.environment !== "production" || !data.privacy?.controller || !data.privacy?.contact) {$('service-notice').textContent = "Entorno de preparación. La publicación requiere completar la configuración, los datos del responsable y la verificación del servicio público."; $('service-notice').hidden = false;}} catch (error) {privacyText(); showNotice(error.message, true);} try {const {data} = await api("/api/me", {}, {expireSession: false}); await startSession(data);} catch (error) {if (error.status !== 401) showNotice(error.message, true);}}
initialize();
