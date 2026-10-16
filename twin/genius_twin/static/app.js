"use strict";

// Every value describing a computed future is obtained from the local API.
// Labels explain the single admitted domain; they never stand in for a result.
const $ = (selector) => document.querySelector(selector);
const TWIN_API_BASE=location.pathname.startsWith("/twin")?"/api/twin":"/api";
let twinRuntime=null;
const ui = {
  capabilities: null, dossier: null, initial: null, evaluation: null,
  view: "review", twinView: "map", policy: null, scenario: "HA", day: 10,
  proposal: null, comparison: null, observed: null, pendingKey: null,
  busy: false, changeText: "", changeKind: "hypothetical_intervention",
  observationDraft: {}, reviewChecks: {}, changeLaw: {}, changeSource: "", changePreference: null,
};
const policyNames = {C:"Continuidad", R:"Reserva y turnos", E:"Preparar propagación", E_prime:"Propagación con relevo"};
const scenarioNames = {N:"Normal", H:"Calor", HA:"Calor + ausencia"};
const orgNames = {q0:"Cuidado manual", q1:"Reserva y turnos operativos", q2:"Unidad de propagación operativa"};
const kindNames = {initial_model:"Modelo inicial", hypothetical_intervention:"Intervención hipotética", preference:"Preferencia", fact_correction:"Corrección de un hecho", restore:"Restauración"};
const stateNames = {completed:"Finalizado",running:"En curso",failed:"Falló el cálculo",CALCULATED_UNDER_DECLARED_ASSUMPTIONS:"Calculado bajo supuestos declarados",SYNTHETIC_ONLY:"Solo modelo sintético",MODEL_REVIEW_REQUIRED:"Requiere revisión del modelo",PROSPECTIVE_REFERENCE:"Dato posterior a la predicción",RETROSPECTIVE_COMPARISON_NOT_PROSPECTIVE_VALIDATION:"Contraste retrospectivo; no valida una predicción futura",unique:"Seleccionar solo una alternativa única",robust:"Robusto",possible:"Posible"};
const EXAMPLE_TEXT = "Necesitamos cuidar un semillero con dos plantas y dos personas, A y B, durante 14 días. Queremos comparar el cuidado manual, la reserva con turnos y la preparación de propagación, sin sobrecargar a quienes lo cuidan. Quiero explorar el modelo sintético del ejemplo.";
const EXAMPLE_CHANGE = "Adelantemos la formación de A y la verificación de B al día 9. Si B falta el día 10, A cubre el riego de emergencia.";

function element(tag, options = {}, ...children) {
  const node = document.createElement(tag);
  Object.entries(options).forEach(([key, value]) => {
    if (value === undefined || value === null || value === false) return;
    if (key === "class") node.className = value;
    else if (key === "text") node.textContent = String(value);
    else if (key.startsWith("on")) node.addEventListener(key.slice(2).toLowerCase(), value);
    else if (["value", "checked", "disabled", "hidden"].includes(key)) node[key] = value;
    else node.setAttribute(key, value === true ? "" : String(value));
  });
  children.flat(Infinity).filter(v => v !== null && v !== undefined && v !== false).forEach(child => node.append(child instanceof Node ? child : document.createTextNode(String(child))));
  return node;
}
const p = (text, cls = "") => element("p", {class:cls, text});
const badge = (text, cls = "") => element("span", {class:`badge ${cls}`, text});
const button = (text, action, cls = "", attrs = {}) => element("button", {type:"button", class:`button ${cls}`, onclick:action, ...attrs}, text);
const panel = (title, children = [], cls = "") => element("section", {class:`panel ${cls}`}, title ? element("h3", {text:title}) : null, children);
const actions = (...children) => element("div", {class:"actions"}, children);
const list = (values) => element("ul", {class:"plain-list"}, values.map(value => element("li", {}, typeof value === "object" ? humanValue(value) : value)));
const factList = (facts) => element("dl", {class:"fact-list"}, facts.map(([label,value]) => [element("dt", {text:label}), element("dd", {text:humanValue(value)})]));
const disclosure = (title, data) => element("details", {class:"disclosure"}, element("summary", {text:title}), element("pre", {class:"code-block", text:JSON.stringify(data,null,2)}));
const humanValue = value => value === null ? "Sin valor declarado (null)" : value === undefined ? "No disponible" : typeof value === "boolean" ? (value ? "Sí" : "No") : typeof value === "object" ? JSON.stringify(value) : String(value);
const fmtPolicy = id => `${policyNames[id] || id} (${id === "E_prime" ? "E′" : id})`;
const fmtSet = values => Array.isArray(values) ? `{ ${values.join(", ")} }` : humanValue(values);
const formatDate = value => value ? new Intl.DateTimeFormat("es-AR", {dateStyle:"short", timeStyle:"short"}).format(new Date(value)) : "Fecha no disponible";
function table(caption, headers, rows, rowClass) {
  return element("div", {class:"data-table-wrap"}, element("table", {}, element("caption", {text:caption}), element("thead", {}, element("tr", {}, headers.map(header => element("th", {scope:"col",text:header})))), element("tbody", {}, rows.map((row,index) => element("tr", {class:rowClass ? rowClass(index) : ""}, row.map((cell,i) => element(i===0?"th":"td", i===0?{scope:"row"}:{}, cell)))))));
}
function heading(title, subtitle, controls = null) {
  return element("div", {class:"section-heading"}, element("div", {}, element("h2", {tabindex:"-1",text:title}), p(subtitle)), controls);
}
function selectField(id, label, options, current, change) {
  return element("div", {}, element("label", {for:id,text:label}), element("select", {id, value:current, onchange:change}, options.map(([value,text]) => element("option", {value, ...(String(value)===String(current)?{selected:true}:{})}, text))));
}
function errorText(error) {
  const messages = {
    DRAFT_CONFLICT:"Existe un borrador más reciente. Tus cambios siguen aquí; recarga y revisa antes de guardar.",
    VERSION_CONFLICT:"La versión cambió mientras trabajabas. Tu texto sigue aquí. Recarga el expediente y revisa la propuesta sobre la versión actual.",
    UNSUPPORTED_DOMAIN:"Este caso no corresponde al modelo que admite D1. Puedes explorar el ejemplo de semillero o conservar tu relato para un modelo futuro.",
    UNSUPPORTED_CHANGE:"Este cambio necesita un modelo o una operación todavía no admitidos. Tu propuesta permanece escrita para revisarla.",
    SYNTHETIC_ACK_REQUIRED:"Confirma que entiendes el alcance sintético antes de aceptar la propuesta.",
  };
  return messages[String(error.code).toUpperCase()] || error.message || "No se pudo completar la operación. Conservamos la pantalla para que puedas reintentar.";
}
function clearError(){ $("#error").replaceChildren(); $("#error").hidden=true; }
function showError(error, retry = null) {
  const box=$("#error"); box.hidden=false; box.replaceChildren(p(errorText(error)));
  const controls=[];
  if(error.status===401)controls.push(element("a",{class:"button small",href:"/"},"Iniciar sesión"));
  if (error.status===409 || String(error.code).toUpperCase().includes("CONFLICT")) controls.push(button("Recargar versión vigente",()=>run(async()=>{await refresh();ui.proposal=null;ui.pendingKey=null;const conflictMessage=typeof refreshGeneralConflict==="function"?refreshGeneralConflict():null;render();announce(conflictMessage||"Expediente actualizado. Revisa tu texto antes de proponerlo nuevamente.");}),"small"));
  else if (retry && (!error.status || error.status>=500)) controls.push(button("Reintentar",()=>run(retry,retry),"small"));
  controls.push(button("Cerrar aviso",clearError,"ghost small")); box.append(actions(controls));
  if (error.details) box.append(disclosure("Ver motivo del servicio",error.details));
  box.scrollIntoView({block:"nearest"});
}
function announce(message){ $("#status").textContent=message; }
async function api(path, body, method) {
  let response;
  path=path.replace(/^\/api(?=\/|$)/,TWIN_API_BASE);
  if(body!==undefined && TWIN_API_BASE!=="/api" && !twinRuntime){const runtimeResponse=await fetch(`${TWIN_API_BASE}/runtime`,{headers:{Accept:"application/json"}});if(!runtimeResponse.ok)throw Object.assign(new Error("Inicia sesión para continuar con tu decisión."),{status:runtimeResponse.status});twinRuntime=await runtimeResponse.json();}
  const headers={Accept:"application/json",...(body===undefined?{}:{"Content-Type":"application/json"}),...(body!==undefined && twinRuntime?.csrf_token?{"X-CSRF-Token":twinRuntime.csrf_token}:{})};
  try {response=await fetch(path,{method:method||(body===undefined?"GET":"POST"),headers,...(body===undefined?{}:{body:JSON.stringify(body)})});}
  catch {throw Object.assign(new Error("No pudimos comunicarnos con el servicio local. Tu texto sigue disponible. Comprueba que esté en marcha y vuelve a intentarlo."),{code:"NETWORK_ERROR"});}
  let data;
  try {data=await response.json();} catch {throw Object.assign(new Error("El servicio respondió en un formato inesperado."),{status:response.status});}
  if (!response.ok){const detail=data.error||{};throw Object.assign(new Error(detail.message||"La operación no se completó."),{status:response.status,code:detail.code,details:detail.details});}
  return data;
}
async function run(action,retry = action) {
  if(ui.busy)return;
  ui.busy=true;clearError();announce("Procesando en el servicio local…");
  const controls=[...document.querySelectorAll("button[type=submit], .button, #step-nav button")];
  const disabled=controls.map(control=>control.disabled); controls.forEach(control=>control.disabled=true);
  $("#main").setAttribute("aria-busy","true");
  try {await action();} catch(error){announce("");showError(error,retry);}
  finally{ui.busy=false;controls.forEach((control,i)=>control.disabled=disabled[i]);$("#main").removeAttribute("aria-busy");if($("#status").textContent==="Procesando en el servicio local…")announce("");}
}
function activeCase(){return ui.dossier?.case || ui.initial?.case;}
function versions(){return ui.dossier?.versions || [];}
function currentVersion(){return versions().find(v=>v.version===activeCase()?.current_version) || versions().at(-1);}
function currentModel(){return currentVersion()?.model || ui.proposal?.model || ui.initial?.proposal?.model;}
function currentResults(){
  if(ui.evaluation?.canonical_results && ui.evaluationVersion===activeCase()?.current_version)return ui.evaluation.canonical_results;
  const job=[...(ui.dossier?.jobs||[])].reverse().find(j=>j.version===activeCase()?.current_version && j.canonical_results);
  return job?.canonical_results || null;
}
function resultJob(){return [...(ui.dossier?.jobs||[])].reverse().find(j=>j.version===activeCase()?.current_version && j.canonical_results);}
function currentProposal(){return ui.proposal || (ui.dossier?.proposals||[]).find(item=>item.status==="proposed" && item.base_version===activeCase()?.current_version) || ui.initial?.proposal;}
function saveCase(){try{localStorage.setItem("genius_d1_case",activeCase().id);}catch{/* Storage availability is optional. */}}
async function refresh(){if(activeCase()?.id)ui.dossier=await api(`/api/cases/${encodeURIComponent(activeCase().id)}`);}
function go(view){ui.view=view;clearError();render();$("#view-content h2")?.focus({preventScroll:true});}
function render(){
  const caseData=activeCase();if(!caseData)return;
  $("#welcome").hidden=true;$("#workspace").hidden=false;$("#start-over").hidden=false;
  $("#case-title").textContent=caseData.title||"Semillero comunitario";
  $("#case-meta").textContent=`${currentModel()?.horizon ?? "—"} días · Versión ${caseData.current_version} · ${caseData.id}`;
  $("#case-badges").replaceChildren(badge(currentModel()?"Modelo sintético":"Modelo pendiente","amber"),badge(reviewRequired()?"Revisión requerida":currentResults()?"Evaluación disponible":"Pendiente de evaluar",reviewRequired()?"amber":"mint"));
  document.querySelectorAll("#step-nav button").forEach(b=>b.setAttribute("aria-current",b.dataset.view===ui.view?"step":"false"));
  const views={review:renderReview,twin:renderTwin,futures:renderFutures,conclusion:renderConclusion,change:renderChanges,evidence:renderEvidence};
  $("#view-content").replaceChildren(activeCase().status==="needs_model"?renderUnsupported():views[ui.view]());
}
async function createCase(){
  const text=$("#narrative").value.trim(); if(!text)return;
  const response=await api("/api/cases",{text,title:"Exploración del semillero",profile:"SEMILLERO_14D_SYNTHETIC_V1"});ui.initial=response;ui.dossier=null;ui.proposal=response.proposal;ui.evaluation=null;ui.reviewChecks={};
  saveCase();await refresh();go("review");announce(response.proposal?"Propuesta construida. Revisa las decisiones materiales antes de aceptarla.":"Tu relato se conservó. Este dominio requiere un modelo todavía no admitido.");
}
function renderUnsupported(){return element("div",{},heading("Este relato necesita un modelo propio","La limitación está en el alcance del producto. Agregar más datos al relato no amplía automáticamente el modelo."),panel("Tu solicitud está conservada",[p(activeCase().narrative,"quote"),list((activeCase().obligations||[]).map(item=>item.message)),p("Puedes iniciar una nueva exploración con el relato didáctico del semillero. Este expediente se mantiene como pendiente de modelización.","note")],"amber"));}
function reviewRequired(){return !!currentVersion()?.metadata?.review_required || resultJob()?.admission==="MODEL_REVIEW_REQUIRED" || ["REVIEW_REQUIRED","SCOPE_INCOMPLETE"].includes(ui.dossier?.system_context?.status);}
function checkRow(id,text){return element("div",{class:"check-row"},element("input",{id,type:"checkbox",checked:!!ui.reviewChecks[id],onchange:e=>{ui.reviewChecks[id]=e.target.checked;}}),element("label",{for:id,text}));}
function renderReview(){
  const model=currentModel();const proposal=currentProposal();const accepted=activeCase().current_version>0;
  const acceptedPanel=accepted?panel("Alcance confirmado",[p("Esta versión conserva los supuestos que aceptaste. Puedes explorar el gemelo, evaluarlo o proponer una nueva revisión.","note"),actions(button("Explorar gemelo",()=>go("twin"),"primary"),button("Evaluar esta versión",()=>run(evaluate),"secondary"))],"mint"):null;
  const material=proposal?.material_changes||[];
  const checks=element("div",{},
    checkRow("scope-check","Revisé portadores, recursos, horizonte y políticas del modelo propuesto."),
    checkRow("synthetic-check","Entiendo que la ley y los datos son sintéticos. Aceptarlos no los convierte en evidencia real."),
    checkRow("support-check","Revisé la dependencia del cuidado y los turnos de A y B; su disponibilidad es un supuesto del ejemplo."));
  return element("div",{},heading("Esto es lo que entendí","Tu relato abre una propuesta. Tú decides qué modelo usar; su evidencia conserva su origen."),
    element("div",{class:"grid aside"},element("div",{class:"stack"},
      panel("Tu intención",[p(proposal?.text || ui.dossier?.case?.narrative || ui.initial?.proposal?.text || "Relato conservado en el expediente.","quote")]),
      panel("Decisiones materiales",[material.length?list(material):p("Revisa la frontera, el calendario, las reglas de cuidado y la ley conjunta.","note"),
        accepted ? acceptedPanel : element("form",{onsubmit:e=>{e.preventDefault();run(acceptInitial);}},checks,element("div",{class:"actions"},element("button",{type:"submit",class:"button primary"},"Confirmar alcance y continuar")))])),
      element("div",{class:"stack"},panel("Tu gemelo propuesto",[badge(accepted?"CONFIRMADO":"PROPUESTO","mint"),element("div",{class:"spacing-top"},factList([
        ["Portadores","Personas A y B; plantas P1 y P2"],["Horizonte",model?`${model.horizon} pasos diarios`:undefined],["Agua adicional",model?`${model.water_budget_liters} L`:undefined],["Políticas",model?.policies?.map(fmtPolicy).join(" · ")],["Restricción",model?.require_all_scenarios?"Ninguna violación en los escenarios declarados":"Sin exigir cumplimiento en todos los escenarios"]]))]),
      panel("Frontera y límites",[p("Semillero, bandeja compartida, agua y tareas de cuidado. El calor y la ausencia crítica se representan como eventos externos.","note"),p("Las plantas se estipulan vivas. Se evalúa una condición hídrica de la tarea: no existe aquí un modelo de mortalidad ni una predicción de supervivencia real.","note"),p("Fuera del modelo: enfermedades, fallos de equipo, ausencias en otros días y condiciones posteriores al horizonte.","note")],"amber"))),
    proposal?disclosure("Ver propuesta estructurada y procedencia",proposal):null);
}
async function acceptInitial(){
  if(!ui.reviewChecks["scope-check"]||!ui.reviewChecks["synthetic-check"]||!ui.reviewChecks["support-check"]){throw new Error("Revisa y confirma las tres decisiones materiales para continuar.");}
  await acceptProposal(currentProposal());go("twin");announce("Alcance confirmado en una nueva versión. Ya puedes evaluar el modelo.");
}
async function acceptProposal(proposal){
  if(!proposal?.id)throw new Error("No hay una propuesta pendiente para aceptar.");
  ui.pendingKey ||= crypto.randomUUID();
  const response=await api(`/api/proposals/${encodeURIComponent(proposal.id)}/accept`,{base_version:proposal.base_version,idempotency_key:ui.pendingKey,confirmed:true,acknowledge_synthetic:true});
  ui.proposal=null;ui.pendingKey=null;ui.evaluation=null;ui.evaluationVersion=null;
  await refresh();saveCase();return response;
}
function renderTwin(){
  const model=currentModel();
  const switcher=element("div",{class:"segmented",role:"group","aria-label":"Vista del gemelo"},button("Mapa",()=>{ui.twinView="map";render();},"",{"aria-pressed":ui.twinView==="map"}),button("Lista",()=>{ui.twinView="list";render();},"",{"aria-pressed":ui.twinView==="list"}));
  const nodes=[
    ["A y B","Personas que distribuyen su tiempo entre riego, formación y preparación.",""],
    ["Reserva de agua",`Presupuesto adicional compartido: ${model?.water_budget_liters ?? "—"} L.`,""],
    ["Bandeja común","Recibe el riego y la demanda de agua. Su estado se conserva día a día.","wide"],
    ["Plantas P1 y P2","Comparten la condición hídrica de la bandeja. La existencia de ambas está estipulada.","wide"]
  ];
  const diagram=element("div",{class:"map-layout"},nodes.slice(0,2).map(([title,text,cls])=>element("div",{class:`map-node ${cls}`},element("h3",{text:title}),p(text))),p("Trabajo de riego + flujo de agua → bandeja","map-relation"),nodes.slice(2,3).map(([title,text,cls])=>element("div",{class:`map-node ${cls}`},element("h3",{text:title}),p(text))),p("Condición hídrica compartida → plantas","map-relation"),nodes.slice(3).map(([title,text,cls])=>element("div",{class:`map-node ${cls}`},element("h3",{text:title}),p(text))));
  const equivalent=table("Entidades y relaciones del modelo",["Elemento","Relación / función","Origen"],nodes.map(([title,text])=>[title,text,"Supuesto sintético del perfil"]));
  return element("div",{},heading("Un modelo que puedes revisar","El mapa y la lista describen las mismas relaciones. Ocultar un elemento en pantalla no lo elimina del modelo.",switcher),element("div",{class:"grid aside"},panel("Personas, recursos y condiciones",[ui.twinView==="map"?diagram:equivalent]),element("div",{class:"stack"},panel("Qué se conserva en el tiempo",[p("El estado hídrico, los recursos usados, la formación y las capacidades avanzan según cada política.","note"),p("Un monitor recuerda si la condición falló en algún día. Recuperar agua después no borra ese fallo.","callout")],"mint"),panel("De este modelo a sus futuros",[p("El cálculo usa las versiones confirmadas. Cada reevaluación conserva su entrada y su resultado para permitir el contraste.","note"),actions(button("Evaluar esta versión",()=>run(evaluate),"primary")),p(activeCase().current_version?"La evaluación se ejecuta en el núcleo local.":"Confirma primero el alcance en Revisión.","hint")]))),disclosure("Ver modelo admitido",model));
}
async function evaluate(){
  if(!activeCase().current_version)throw new Error("Confirma el alcance en Revisión antes de evaluar.");
  const version=activeCase().current_version;const data=await api(`/api/cases/${encodeURIComponent(activeCase().id)}/evaluate`,{version});
  await refresh();
  if(data.job?.status!=="completed" || !data.evaluation?.canonical_results){const failure=data.job?.error||{};throw Object.assign(new Error(failure.message||"El trabajo no produjo una evaluación completa. Esto no significa que la decisión sea inviable."),{code:failure.code});}
  ui.evaluation=data.evaluation;ui.evaluationVersion=version;go("futures");announce(reviewRequired()?"Cálculo disponible; la recomendación permanece suspendida hasta revisar la discrepancia observada.":"Evaluación terminada. Los resultados corresponden a la versión confirmada.");
}
function needsEvaluation(){return element("div",{},heading("Primero, evalúa esta versión","La pantalla se completa con el resultado del servicio local."),element("div",{class:"empty-state"},element("h3",{text:activeCase().current_version?"El gemelo está listo para evaluar":"Revisa el alcance propuesto"}),p("Todavía no hay un resultado calculado para esta versión. Cada cambio material requiere una evaluación nueva."),actions(button(activeCase().current_version?"Evaluar versión":"Revisar propuesta",()=>activeCase().current_version?run(evaluate):go("review"),"primary"))));}

// Accessors below follow the canonical domain contract returned by evaluate.
function policies(results){return results?.policies || {};}
function conclusion(results){return results?.decision || {};}
function dailyOf(results,policy,scenario){return policies(results)[policy]?.trajectories?.[scenario]?.daily || [];}
function totalsOf(results,policy,scenario){return policies(results)[policy]?.trajectories?.[scenario]?.totals || {};}
function policyPvs(result){return result?.pvs?.value;}
function policyMasses(result){return result?.pvs?.masses || {};}
function policyCag(result){return result.cag || {};}
function policyCard(id,result){
  const cag=policyCag(result),masses=policyMasses(result);const outcome=currentResults();
  return panel(null,[element("span",{class:"policy-id",text:id==="E_prime"?"E′":id}),element("h3",{text:policyNames[id]||id}),
    p("CONDICIÓN HÍDRICA SOSTENIDA","metric-label"),p(humanValue(policyPvs(result)),"metric"),p("PVS de la tarea · ley sintética","note"),
    factList([["Masa de éxito",masses.success],["Masa de fallo",masses.failure],["Indeterminación",masses.undecided]]),
    element("hr",{class:"card-divider"}),p("CAPACIDADES · RECETA ACC","metric-label"),factList([["Posibles",fmtSet(cag.possible)],["Robustas",fmtSet(cag.robust)]]),
    element("hr",{class:"card-divider"}),p("TIEMPO DE TAREA POR ESCENARIO","metric-label"),table(`Carga A / B · ${id==="E_prime"?"E′":id}`,["Escenario","A (min)","B (min)"],Object.keys(currentModel()?.law||{}).map(s=>{const totals=totalsOf(outcome,id,s);return[scenarioNames[s],humanValue(totals.minutes_a),humanValue(totals.minutes_b)];})),
    p("El tiempo es una condición del perfil. No es una puntuación de bienestar agregado.","result-footnote")],"policy-card");
}
function renderFutures(){
  const results=currentResults();if(!results)return needsEvaluation();
  const ids=Object.keys(policies(results));if(!ids.includes(ui.policy))ui.policy=ids.includes("E_prime")?"E_prime":ids.includes("E")?"E":ids[0];
  const model=currentModel();const allDaily=dailyOf(results,ui.policy,ui.scenario);const record=allDaily.find(r=>r.day===Number(ui.day));
  const controls=element("div",{class:"toolbar"},selectField("policy-select","Política",ids.map(id=>[id,fmtPolicy(id)]),ui.policy,e=>{ui.policy=e.target.value;render();}),selectField("scenario-select","Escenario",Object.keys(model.law).map(id=>[id,`${scenarioNames[id]} · ${model.law[id]}`]),ui.scenario,e=>{ui.scenario=e.target.value;render();}),selectField("day-select","Día",allDaily.map(r=>[r.day,`Día ${r.day}`]),ui.day,e=>{ui.day=Number(e.target.value);render();}));
  const milestones=element("div",{class:"timeline"},[10,11,14].map(day=>{const row=allDaily.find(r=>r.day===day);return element("div",{class:`timepoint ${row?.water_in_tray_liters<1?"fault":""}`},p(`Día ${day}`,"day"),p(`${humanValue(row?.water_in_tray_liters)} L`,"water"),p(row?.water_in_tray_liters<1?"Condición incumplida":"Condición hídrica del día"),p(row?.violation_seen?"Monitor: hubo un fallo":"Monitor: sin fallo registrado"));}));
  const dailyRows=allDaily.map(r=>[String(r.day),`${r.water_in_tray_liters} L`,`${r.minutes_a} / ${r.minutes_b}`,`${r.available_a_minutes} / ${r.available_b_minutes}`,r.organization,r.violation_seen?"Sí":"No"]);
  return element("div",{},heading("Elegir políticas, explorar futuros","Compara condiciones, capacidades e incertidumbre sin reducirlas a un único puntaje."),
    reviewRequired()?panel("Recomendación suspendida",[p("Hay una discrepancia observada que requiere revisar el modelo. Estos valores son cálculos condicionales; recalcular no valida ni calibra sus premisas.","note")],"amber"):null,
    panel("Ley conjunta del ejemplo",[element("div",{class:"pill-list"},Object.entries(model.law).map(([id,weight])=>badge(`${scenarioNames[id]}: ${weight}`,"amber"))),p("Los pesos corresponden a escenarios conjuntos. No se supone independencia entre calor y ausencia. El modelo cubre estas ramas, no todos los futuros del mundo real.","note spacing-top")]),
    element("div",{class:"grid three spacing-top"},ids.map(id=>policyCard(id,policies(results)[id]))),
    element("section",{class:"subsection"},element("h3",{text:"Un final favorable no borra el trayecto"}),controls,
      element("div",{class:"grid aside"},panel("Estados intermedios",[milestones,p("El evento de trayectoria exige cumplir la condición cada día. El evento terminal solo consulta el último día.","note"),factList([["PVS de trayectoria",policyPvs(policies(results)[ui.policy])],["Probabilidad del evento terminal",policies(results)[ui.policy].endpoint_probability?.value]])]),
      panel(`Bienestar · día ${ui.day}`,[p("Perfil de condiciones por portador. Tiempo disponible en el presupuesto diario y condición hídrica compartida.","note"),record?factList([["Persona A",`${record.available_a_minutes} min disponibles; ${record.minutes_a} min de tarea`],["Persona B",`${record.available_b_minutes} min disponibles; ${record.minutes_b} min de tarea`],["Planta P1",`${record.water_in_tray_liters} L en bandeja compartida; viva por estipulación`],["Planta P2",`${record.water_in_tray_liters} L en bandeja compartida; viva por estipulación`],["Recursos usados",`${record.water_used_liters} L adicionales`],["Organización",`${record.organization} · ${orgNames[record.organization]||""}`]]):p("No hay un registro disponible para este día.","note"),p("Cero es un valor del modelo. La ausencia de un dato se conserva como ausencia; no se transforma en cero.","hint")],"mint")),
      element("details",{class:"disclosure"},element("summary",{text:"Ver todos los días y el monitor persistente"}),element("div",{class:"spacing-top"},table(`Trayectoria · ${fmtPolicy(ui.policy)} · ${scenarioNames[ui.scenario]}`,["Día","Agua común","Tarea A/B (min)","Disponible A/B (min)","Organización","Fallo previo"],dailyRows,index=>allDaily[index]?.water_in_tray_liters<1?"row-alert":"")))),
    panel("Cómo leer las capacidades",[element("div",{class:"legend-list"},Object.entries(orgNames).map(([id,name])=>p(`${id} · ${name}`))),p("CAG acc identifica logros con conservación de la organización en cada transición hasta alcanzarlos. Posible: existe una rama que satisface esa receta. Robusta: la satisface cada rama declarada. Se comparan identidades e inclusión; no se cuentan rutas.","note spacing-top")],"spacing-top"),
    actions(button("Ver conclusión integrada",()=>go("conclusion"),"primary"),button("Explorar un cambio",()=>go("change"),"secondary")));
}
function renderConclusion(){
  const results=currentResults();if(!results)return needsEvaluation();const data=conclusion(results);
  const feasible=data.feasible||[],frontier=data.frontier||[];
  const summary=reviewRequired()?"La recomendación está suspendida: revisa el modelo.":data.selected?`${fmtPolicy(data.selected)} es la selección bajo la norma declarada.`:`${feasible.length} políticas cumplen la restricción. No hay una selección única.`;
  return element("div",{},heading("Una conclusión que permite decidir","Conserva la norma aplicada, sus motivos y el alcance de la evaluación."),panel(null,[p("CONCLUSIÓN DE ESTA VERSIÓN","eyebrow"),element("h3",{class:"decision-title",text:summary}),reviewRequired()?p("Una observación discrepa de la predicción congelada. Recalcular no calibra el modelo ni levanta automáticamente la suspensión.","callout amber"):null,factList([["Restricción",data.require_all_scenarios?"Ninguna violación en todos los escenarios declarados":"No se exige cumplimiento en todos los escenarios"],["Políticas factibles",feasible.map(fmtPolicy).join(" · ")||"Ninguna"],["Frontera integrada",frontier.map(fmtPolicy).join(" · ")||"Sin candidatas"],["Selección formal",data.selected===null?"Sin una ganadora única":data.selected===undefined?"No declarada":fmtPolicy(data.selected)],["Regla de selección",stateNames[data.selection_rule]||data.selection_rule],["Modo CAG comparado",stateNames[data.comparison_cag_mode]||data.comparison_cag_mode]]),p("La comparación conserva bienestar por portador y momento, capacidades por inclusión y PVS de la tarea. La frontera muestra las alternativas no descartadas por esa comparación.","spacing-top note")],reviewRequired()?"amber":"mint"),
    element("div",{class:"grid two spacing-top"},panel("Qué significa para tu decisión",[p("El modelo separa el tiempo de A, el tiempo de B, la condición de las plantas y las capacidades. Una suma de minutos no representa el bienestar de todos.","note"),p("Si varias políticas cumplen la restricción y ofrecen ventajas distintas, hace falta una prioridad explícita para elegir.","note")]),panel("Qué todavía debes contrastar",[p("La ley conjunta, la demanda hídrica, el umbral, la disponibilidad y las reglas de respuesta requieren evidencia y permisos propios en un caso real.","note"),p("Esta evaluación verifica un modelo sintético. La comprensión humana y la validación empírica tienen estados separados.","note")],"amber")),
    frontier.length>1?element("div",{class:"spacing-top"},table("Diferencias entre las alternativas de la frontera",["Política","PVS de tarea","CAG acc robusto","A / B · N (min)","A / B · HA (min)"],frontier.map(id=>{const n=totalsOf(results,id,"N"),ha=totalsOf(results,id,"HA");return[fmtPolicy(id),humanValue(policyPvs(policies(results)[id])),fmtSet(policies(results)[id]?.cag?.robust),`${humanValue(n.minutes_a)} / ${humanValue(n.minutes_b)}`,`${humanValue(ha.minutes_a)} / ${humanValue(ha.minutes_b)}`];}))):null,
    data.unknown?.length?p(`Políticas cuya factibilidad permanece indeterminada: ${data.unknown.map(fmtPolicy).join(" · ")}.`,"callout amber"):null,
    actions(button("Proponer un cambio",()=>go("change"),"primary"),button("Ver evidencia y exportar",()=>go("evidence"),"secondary")),disclosure("Conclusión canónica para aplicación y agente",data));
}
function renderChanges(){
  const proposal=ui.proposal?.kind!=="initial_model"?ui.proposal:null;
  const form=element("form",{class:"change-fields",onsubmit:e=>{e.preventDefault();run(proposeChange);}},selectField("change-kind","¿Qué estás cambiando?",[["hypothetical_intervention","Intervención hipotética"],["fact_correction","Corrección de un hecho"],["preference","Preferencia / norma de comparación"]],ui.changeKind,e=>{ui.changeKind=e.target.value;ui.changeText=$("#change-text")?.value||ui.changeText;render();}),element("div",{},element("label",{for:"change-text",text:"Describe el cambio"}),element("textarea",{id:"change-text",rows:"6",maxlength:"12000",required:true,value:ui.changeText,placeholder:"Describe qué cambiarías en el modelo…",oninput:e=>ui.changeText=e.target.value})),renderStructuredChange(),actions(element("button",{type:"submit",class:"button primary"},"Revisar propuesta"),button("Usar cambio con relevo",()=>{ui.changeText=EXAMPLE_CHANGE;ui.changeKind="hypothetical_intervention";render();},"text-button")),p("Una intervención propone un futuro; una corrección modifica un hecho declarado; una preferencia cambia cómo comparas. Ninguna edición actúa sobre el mundo.","hint"));
  const proposed=proposal?panel("Revisa antes de aceptar",[badge("PROPUESTA · NO APLICADA","amber"),p(proposal.text,"quote spacing-top"),list(proposal.material_changes||[]),p("Aceptar crea una revisión y deja el resultado anterior en el historial. Es necesario calcular un resultado nuevo.","note"),actions(button("Aceptar y reevaluar",()=>run(async()=>{const before=activeCase().current_version;await acceptProposal(proposal);await evaluate();ui.comparison=await api(`/api/cases/${encodeURIComponent(activeCase().id)}/compare?before=${before}&after=${activeCase().current_version}`);go("change");announce("Cambio aceptado, nueva evaluación y comparación disponibles.");}),"primary"),button("Descartar esta vista",()=>{ui.proposal=null;render();},"ghost")),disclosure("Ver modificación estructurada",proposal)],"mint"):panel("Una edición completa",[p("El cambio de ejemplo adelanta formación y verificación. Añade una regla de relevo si B falta en el día crítico.","note"),p("Después de aceptar se comprueban nuevamente recursos, trayectoria, bienestar, CAG y PVS de la tarea.","note")],"mint");
  return element("div",{},heading("Explora qué cambia","Conserva el antes, crea una nueva versión y compara una evaluación completa."),element("div",{class:"grid two"},panel("Editar con palabras",[form]),proposed),ui.comparison?renderComparison(ui.comparison):null,renderHistory());
}
async function proposeChange(){
  if(!activeCase().current_version)throw new Error("Confirma primero el alcance inicial.");
  ui.changeText=$("#change-text").value;ui.changeKind=$("#change-kind").value;
  let structured;
  if(ui.changeKind==="preference")structured={require_all_scenarios:$("#change-preference").value==="true"};
  if(ui.changeKind==="fact_correction")structured={law:Object.fromEntries(Object.keys(currentModel().law).map(id=>[id,$(`#law-${id}`).value.trim()])),source:$("#law-source").value};
  const response=await api(`/api/cases/${encodeURIComponent(activeCase().id)}/proposals`,{base_version:activeCase().current_version,kind:ui.changeKind,text:ui.changeText,...(structured?{structured}:{})});
  ui.proposal=response.proposal || response;ui.pendingKey=null;await refresh();render();announce("Propuesta lista. Revisa sus cambios materiales antes de aceptar.");
}
function renderStructuredChange(){
  if(ui.changeKind==="preference")return element("div",{},selectField("change-preference","Restricción que quieres aplicar",[["true","Exigir que se cumpla en todos los escenarios"],["false","No exigir cumplimiento en todos los escenarios"]],String(ui.changePreference??currentModel()?.require_all_scenarios??true),e=>ui.changePreference=e.target.value==="true"),p("Esta norma modifica la comparación. No cambia las trayectorias ni el tiempo, CAG o PVS de cada política.","hint"));
  if(ui.changeKind==="fact_correction")return element("div",{class:"change-fields"},p("D1 admite corregir la ley conjunta declarada. Escribe fracciones reducidas con denominador; su suma debe ser uno. Otras correcciones necesitan ampliar el modelo.","hint"),Object.entries(currentModel()?.law||{}).map(([id,weight])=>element("div",{},element("label",{for:`law-${id}`,text:`Peso de ${scenarioNames[id]}`}),element("input",{id:`law-${id}`,type:"text",required:true,value:ui.changeLaw[id]??weight,pattern:"[0-9]+/[1-9][0-9]*",oninput:e=>ui.changeLaw[id]=e.target.value}))),element("div",{},element("label",{for:"law-source",text:"Fuente y motivo de la corrección"}),element("textarea",{id:"law-source",rows:2,required:true,maxlength:2000,value:ui.changeSource,oninput:e=>ui.changeSource=e.target.value})));
  return null;
}
function renderComparison(data){
  const before=data.results?.before,after=data.results?.after;
  const renderSide=(result,version,label,versionMetadata)=>{
    if(!result)return panel(`${label} · versión ${version}`,[p("No hay una evaluación congelada para esta versión.","note")]);
    const id=Object.keys(policies(result)).find(key=>key.startsWith("E"));const item=policies(result)[id];const row=dailyOf(result,id,"HA").find(record=>record.day===10);const totals=totalsOf(result,id,"HA");
    return panel(`${label} · versión ${version}`,[element("h4",{text:fmtPolicy(id)}),versionMetadata?.review_required?p("Recomendación suspendida: esta versión necesita revisar la discrepancia observada. La selección formal no es una recomendación vigente.","callout amber"):null,element("div",{class:"spacing-top"},factList([["PVS de tarea",policyPvs(item)],["CAG acc posible",fmtSet(item?.cag?.possible)],["CAG acc robusto",fmtSet(item?.cag?.robust)],["HA · agua día 10",`${humanValue(row?.water_in_tray_liters)} L`],["HA · agua usada",`${humanValue(totals.water_liters)} L`],["HA · tiempo A / B",`${humanValue(totals.minutes_a)} / ${humanValue(totals.minutes_b)} min`],["Políticas factibles",(result.decision?.feasible||[]).map(fmtPolicy).join(" · ")],["Selección formal",result.decision?.selected===null?"Sin selección única":fmtPolicy(result.decision?.selected)]]))],label==="Después"?"mint":"");
  };
  return panel("Antes y después",[p("Cada lado conserva su versión, la entrada evaluada y la conclusión correspondiente. Una mejora de capacidad no implica una mejora para todos los portadores.","note"),element("div",{class:"grid two"},renderSide(before,data.result_versions?.before,"Antes",data.before?.metadata),renderSide(after,data.result_versions?.after,"Después",data.after?.metadata)),data.model_changes?.length?element("div",{class:"spacing-top"},table("Campos que cambiaron",["Campo","Antes","Después"],data.model_changes.map(change=>[change.field,humanValue(change.before),humanValue(change.after)]))):null,disclosure("Ver comparación verificable",data)],"spacing-top");
}
function renderHistory(){
  return panel("Historial de versiones",[versions().length?element("div",{},[...versions()].reverse().map(version=>element("div",{class:"history-item"},element("span",{class:"history-marker","aria-hidden":"true"}),element("div",{class:"history-details"},element("h4",{text:`Versión ${version.version}${version.version===activeCase().current_version?" · actual":""}`}),p(`${kindNames[version.metadata?.change_kind]||version.metadata?.change_kind||"Revisión del modelo"} · ${formatDate(version.created_at)}`),p(version.model?.policies?.map(fmtPolicy).join(" · "),"note")),version.version!==activeCase().current_version?element("div",{class:"actions"},button("Comparar",()=>run(async()=>{ui.comparison=await api(`/api/cases/${encodeURIComponent(activeCase().id)}/compare?before=${version.version}&after=${activeCase().current_version}`);render();}),"ghost small",{"aria-label":`Comparar versión ${version.version} con la actual`}),button("Restaurar",()=>run(async()=>{const response=await api(`/api/cases/${encodeURIComponent(activeCase().id)}/proposals`,{base_version:activeCase().current_version,kind:"restore",text:`Restaurar modelo de la versión ${version.version}.`,structured:{version:version.version}});ui.proposal=response.proposal||response;ui.pendingKey=null;go("change");}),"ghost small",{"aria-label":`Proponer restauración de la versión ${version.version}`})):badge("Vigente","mint")))):p("Al confirmar el alcance se guardará la primera versión.","note"),p("Restaurar crea una revisión nueva. El historial y las evaluaciones anteriores se conservan.","hint")],"spacing-top");
}
function renderEvidence(){
  const results=currentResults(),job=resultJob();
  return element("div",{},heading("Evidencia, observación y trazabilidad","Una confirmación, una observación y un cálculo conservan significados distintos."),
    element("div",{class:"grid two"},panel("Procedencia del caso",[factList([["Origen","Modelo sintético estipulado"],["Confirmación",activeCase().current_version?"Alcance confirmado por la persona usuaria":"Propuesta sin confirmar"],["Medición real","No aportada por el ejemplo"],["Validación empírica","Pendiente de un caso real autorizado"]]),p("Aceptar el modelo no confirma su validez en el mundo. Las observaciones posteriores se agregan sin reescribir la predicción.","callout")]),panel("Estados separados",[factList([["Transporte","API local"],["Trabajo de evaluación",stateNames[job?.status]||job?.status||"No solicitado"],["Versión del modelo",activeCase().current_version],["Resultado del producto",stateNames[results?.product_value_status]||results?.product_value_status||"Pendiente"],["Recomendación",reviewRequired()?"Suspendida hasta revisar el modelo":"Condicionada al modelo declarado"],["Admisión empírica",stateNames[results?.empirical_admission]||results?.empirical_admission||"No validada"]]),p("PV_UNKNOWN es un estado de valor del producto. No equivale a PVS desconocida ni a una celda formal FP1.","hint")],"mint")),
    renderObservationForm(),renderObservations(),
    panel("La misma información para personas, aplicaciones y agentes",[p("El archivo exportado conserva versiones, propuestas, observaciones y resultados canónicos. La vista humana lee esos mismos valores y conclusiones.","note"),actions(button("Descargar expediente JSON",()=>run(exportDossier),"primary"),button("Actualizar expediente",()=>run(async()=>{await refresh();render();announce("Expediente actualizado.");}),"secondary")),results?disclosure("Ver resultado canónico de esta versión",results):p("Evalúa una versión para consultar su resultado estructurado.","hint"),job?disclosure("Ver metadatos y referencias del trabajo",job):null],"spacing-top"));
}
function renderObservationForm(){
  const job=resultJob(),results=currentResults();if(!results)return panel("Contrastar una observación",[p("Evalúa esta versión antes de incorporar otra observación. Cada dato se contrasta con una predicción congelada.","note"),ui.observed?renderObservationContrast(ui.observed):null,reviewRequired()?p("La observación requiere revisar el modelo. La recomendación queda suspendida incluso si vuelves a calcular.","callout amber"):null,activeCase().current_version?actions(button("Evaluar esta versión",()=>run(evaluate),"secondary")):null],"spacing-top");
  const values=ui.observationDraft;
  const field=(id,label,type,value,attrs={})=>element("div",{},element("label",{for:id,text:label}),element("input",{id,name:id,type,value:value??"",...attrs,oninput:e=>ui.observationDraft[id]=e.target.value}));
  return panel("Agregar una observación posterior",[p("Registra un dato declarado y su fuente. Un dato aislado contrasta una predicción; no valida por sí solo el modelo ni su ley.","note"),element("form",{id:"observation-form",class:"observation-form",onsubmit:e=>{e.preventDefault();run(saveObservation);}},
    selectField("obs-policy","Política observada",Object.keys(policies(results)).map(id=>[id,fmtPolicy(id)]),values["obs-policy"]||ui.policy||Object.keys(policies(results))[0],e=>ui.observationDraft["obs-policy"]=e.target.value),
    selectField("obs-scenario","Escenario declarado",Object.keys(currentModel().law).map(id=>[id,scenarioNames[id]]),values["obs-scenario"]||"HA",e=>ui.observationDraft["obs-scenario"]=e.target.value),
    field("obs-day","Día observado","number",values["obs-day"],{min:0,max:currentModel().horizon,step:1,required:true}),field("obs-water","Agua en la bandeja (L)","number",values["obs-water"],{min:0,step:"any",required:true}),
    element("div",{class:"full"},field("obs-time","Fecha y hora de la observación (hora local del dispositivo)","datetime-local",values["obs-time"],{required:true})),
    element("div",{class:"full"},element("label",{for:"obs-source",text:"Fuente / origen del dato"}),element("input",{id:"obs-source",type:"text",maxlength:1000,required:true,value:values["obs-source"]||"",placeholder:"Indica quién o qué lo observó, cuándo y con qué método.",oninput:e=>ui.observationDraft["obs-source"]=e.target.value})),
    element("div",{class:"full"},element("label",{for:"obs-note",text:"Notas y contexto"}),element("textarea",{id:"obs-note",rows:2,maxlength:4000,value:values["obs-note"]||"",oninput:e=>ui.observationDraft["obs-note"]=e.target.value})),
    element("div",{class:"full"},checkRow("observation-check","Este registro describe una observación declarada. Si introduzco un dato de prueba, lo identificaré en la fuente.")),
    element("div",{class:"actions full"},element("button",{class:"button primary",type:"submit"},"Guardar y contrastar"))),
    ui.observed?renderObservationContrast(ui.observed):null,
    p(`Se vinculará al trabajo ${job?.id||"de la versión actual"} y a la versión ${activeCase().current_version}.`,"hint")],"spacing-top");
}
function renderObservationContrast(observation){const comparison=observation.comparison||{};return element("div",{class:"contrast-card"},element("h4",{text:comparison.status==="DISCREPANCY_REQUIRES_REVIEW"?"Hay una discrepancia: revisa el modelo":"Coincidencia puntual; el modelo no queda validado"}),element("div",{class:"spacing-top"},factList([["Predicción congelada",`${comparison.predicted_exact} ${observation.unit}`],["Valor declarado",`${observation.value_exact} ${observation.unit}`],["Diferencia exacta",`${comparison.delta_exact} ${observation.unit}`],["Versión predicha",observation.prediction_version],["Modelo recalibrado",comparison.model_was_calibrated],["Fuente",observation.source],["Temporalidad",stateNames[comparison.temporal_relation]||comparison.temporal_relation]])),disclosure("Ver referencia y procedencia completas",observation));}
async function saveObservation(){
  if(!ui.reviewChecks["observation-check"])throw new Error("Confirma el carácter declarado del dato y marca en su fuente si es una prueba.");
  const timestamp=new Date($("#obs-time").value);if(Number.isNaN(timestamp.getTime()))throw new Error("Indica una fecha y hora válidas para la observación.");
  const notes=$("#obs-note").value.trim();const source=$("#obs-source").value.trim()+(notes?`\nContexto: ${notes}`:"");
  const payload={base_version:activeCase().current_version,policy_id:$("#obs-policy").value,scenario_id:$("#obs-scenario").value,day:Number($("#obs-day").value),variable:"water_in_tray_liters",value:$("#obs-water").value,unit:"L",observed_at:timestamp.toISOString(),source};
  const signature=JSON.stringify(payload);if(ui.observationPending?.signature!==signature)ui.observationPending={signature,key:crypto.randomUUID()};
  const response=await api(`/api/cases/${encodeURIComponent(activeCase().id)}/observations`,{...payload,idempotency_key:ui.observationPending.key});
  ui.observed=response.observation;ui.evaluation=null;ui.evaluationVersion=null;ui.observationPending=null;ui.observationDraft={};ui.reviewChecks["observation-check"]=false;await refresh();go("evidence");announce("Observación agregada a una nueva versión. La predicción anterior se conserva sin recalibrar el modelo.");
}
function renderObservations(){const observations=ui.dossier?.observations||[];return observations.length?panel("Observaciones conservadas",observations.map((observation,index)=>element("div",{class:"spacing-top"},element("h4",{text:`Observación ${index+1} · ${formatDate(observation.received_at)}`}),renderObservationContrast(observation))),"spacing-top"):null;}
async function exportDossier(){const data=await api(`/api/cases/${encodeURIComponent(activeCase().id)}/export`);const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:"application/json;charset=utf-8"}));const link=element("a",{href:url,download:`GENIUS_${activeCase().id}_v${activeCase().current_version}.json`});document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);announce("Expediente exportado con su información canónica.");}

$("#fill-example").addEventListener("click",()=>{$("#narrative").value=ui.capabilities?.example_text||EXAMPLE_TEXT;$("#narrative").focus();});
$("#intake-form").addEventListener("submit",event=>{event.preventDefault();run(createCase);});
$("#step-nav").addEventListener("click",event=>{const control=event.target.closest("button[data-view]");if(control)go(control.dataset.view);});
$("#start-over").addEventListener("click",()=>{try{localStorage.removeItem("genius_d1_case");}catch{}ui.dossier=null;ui.initial=null;ui.evaluation=null;ui.proposal=null;ui.comparison=null;ui.observed=null;ui.reviewChecks={};ui.observationDraft={};ui.changeText="";ui.pendingKey=null;$("#workspace").hidden=true;$("#welcome").hidden=false;$("#start-over").hidden=true;clearError();announce("Puedes iniciar otra exploración. El expediente anterior se conserva en el servicio local.");$("#narrative").focus();});
run(async()=>{ui.capabilities=await api("/api/capabilities");let saved;try{saved=localStorage.getItem("genius_d1_case");}catch{}if(saved){try{ui.dossier=await api(`/api/cases/${encodeURIComponent(saved)}`);render();announce("Recuperamos tu expediente local. Puedes continuar desde la versión guardada.");}catch(error){if(error.status===404){try{localStorage.removeItem("genius_d1_case");}catch{}}else throw error;}}});
