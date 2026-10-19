"use strict";
// Decision report for companies: one page for /business/report (English) and /empresas/informe (Spanish).
const $ = id => document.getElementById(id);
const EN = document.documentElement.lang.startsWith("en");
const T = EN ? {
  failed: "The service could not complete the request.", offline: "We lost the connection with Genius. Check your connection and try again.", refused: "The AI declined to model this decision.",
  notValid: "The AI could not write a model the validator accepts, so Genius calculates nothing. Add detail: the options, what is uncertain and whom it affects.",
  rejected: "What the validator rejected", kernel: "The model passed validation but the kernel could not calculate it: ",
  recalculated: "Recalculated by the kernel with your corrections", life: "Life condition: ",
  keep: "Keep it in every scenario: ", none: "No route keeps it in every scenario. Genius does not recommend sacrificing it: another route is needed.",
  dropped: "Dropped because they lose it in some scenario: ", lifeTable: "2. Life and PVS by route and scenario",
  route: "Route", lives: "✓ kept", lost: "✗ lost", undecided: "undecided", noLaw: "no law",
  planet: "3. Planetary boundaries", planetLead: "Where each route leaves each boundary at the end of the horizon (worst moment in brackets). Highlighted: the routes that leave the most room in that scenario.",
  start: "at the start", higher: "higher is better", lower: "lower is better", worst: "worst",
  carriers: "4. Best for each affected party", tied: " (tied or incomparable)", noWelfare: "no wellbeing criterion declared",
  disagree: "The affected parties disagree: what is best for one is not for another. Genius shows the conflict instead of adding it into one number.",
  wellbeing: "Wellbeing of each affected party by scenario (end and worst moment)",
  hypotheses: n => "6. Model hypotheses (" + n + ")", download: "Download the full model (JSON)", print: "Print or save as PDF",
  edit: "Correct hypotheses and recalculate", editLead: "Change any number the AI assumed. Decimals or fractions are accepted (for example 2.5 or 1/3). The kernel recalculates without the AI.",
  stocks: "Stocks", stock: "Stock", initial: "At start", capacity: "Maximum", condition: "Life condition", mustBe: "Must be",
  atLeast: "at least", atMost: "at most", threshold: "Threshold", law: "Probability of each scenario (must add up to 1)",
  scenario: "Scenario", probability: "Probability", actions: "Actions, per step", action: "Action", effect: "Effect", amount: "Amount",
  uses: "uses", adds: "adds to", arrives: "arrives at", consumed: "consumed from", available: "available in", step: "Step ",
  recalc: "Recalculate with the kernel", working: "Modelling the decision and calculating with the kernel.",
  steps: (n, unit) => unit ? "horizon " + n + " × " + unit : n + " steps", generated: "Generated on ", rule: "Life condition and PVS first; then, for each affected party, the routes no other beats on what matters to them. Criteria are never added together.",
  locale: "en-US",
  essentials: "The essentials", touches: (n, names) => "This decision touches " + n + " of the 9 planetary boundaries: " + names + ".",
  roomAll: (b, routes) => b + ": " + routes + " leaves the most room in every scenario.", roomMixed: b => b + ": the route that leaves the most room changes with the scenario.",
  conflict: "The affected parties do not agree on the best route; see section 4.", agree: "The affected parties agree on the best route.",
  nine: "The nine checks", crossedNow: "crossed today", safeNow: "safe zone today", touched: "touched by this decision",
  laws: "5. Laws and frameworks that apply", lawsLead: "They ask companies to assess impacts on the boundaries this decision touches. A guide, not legal advice.",
  examplesLabel: "Or start from an example:", wait: s => "Working for " + s + " s. It usually takes about a minute.",
  phases: ["The AI drafts the model: routes, scenarios, people and living systems affected, boundary stocks.", "The validator checks it and sends it back if something does not add up.", "The kernel calculates every route in every scenario."],
  examples: [
    {label: "Winery in Mendoza", company: "Mid-sized winery that exports to Europe", place: "Mendoza, Argentina; irrigates from the Mendoza River downstream of Potrerillos", decision: "Whether to plant 40 more hectares of vineyard in a dry year, keep the current area, or first switch the current 120 hectares to drip irrigation", horizon: "5 years"},
    {label: "Cotton supplier", company: "Clothing brand selling in Europe", place: "Buys cotton from Brazil and India; sews in Bangladesh", decision: "Whether to keep the current conventional cotton supplier, switch to certified organic cotton at a higher price, or move half of the volume to recycled fibres", horizon: "4 years"},
    {label: "Delivery fleet", company: "Logistics company with 300 diesel vans", place: "Greater Buenos Aires, Argentina", decision: "Whether to renew the fleet with diesel vans, switch gradually to electric vans with chargers at the depots, or outsource the last mile", horizon: "6 years"},
  ],
} : {
  failed: "El servicio no pudo completar la solicitud.", offline: "Se perdió la conexión con Genius. Revisá tu conexión y probá de nuevo.", refused: "La IA no quiso modelar esta decisión.",
  notValid: "La IA no logró escribir un modelo que el validador acepte, así que Genius no calcula nada. Agregá detalle: las opciones, qué es incierto y a quién afecta.",
  rejected: "Lo que rechazó el validador", kernel: "El modelo pasó la validación pero el kernel no pudo calcularlo: ",
  recalculated: "Recalculado por el kernel con tus correcciones", life: "Condición de vida: ",
  keep: "La conservan en todos los escenarios: ", none: "Ninguna ruta la conserva en todos los escenarios. Genius no recomienda sacrificarla: hace falta buscar otra ruta.",
  dropped: "Quedan descartadas porque la pierden en algún escenario: ", lifeTable: "2. Vida y PVS por ruta y escenario",
  route: "Ruta", lives: "✓ se conserva", lost: "✗ se pierde", undecided: "indeciso", noLaw: "sin ley",
  planet: "3. Límites planetarios", planetLead: "Dónde deja cada ruta cada límite al final del horizonte (entre paréntesis, el peor momento). Resaltadas: las rutas que dejan más margen en ese escenario.",
  start: "al inicio", higher: "más es mejor", lower: "menos es mejor", worst: "peor",
  carriers: "4. Lo mejor para cada afectado", tied: " (empatadas o incomparables)", noWelfare: "sin criterio de bienestar declarado",
  disagree: "Los afectados no coinciden: lo mejor para uno no lo es para otro. Genius muestra el conflicto en vez de sumarlo en un número.",
  wellbeing: "Bienestar de cada afectado por escenario (final y peor momento)",
  hypotheses: n => "6. Hipótesis del modelo (" + n + ")", download: "Descargar el modelo completo (JSON)", print: "Imprimir o guardar en PDF",
  edit: "Corregir hipótesis y recalcular", editLead: "Cambiá cualquier número que la IA supuso. Se aceptan decimales o fracciones (por ejemplo 2.5 o 1/3). El kernel recalcula sin usar la IA.",
  stocks: "Existencias", stock: "Existencia", initial: "Al inicio", capacity: "Máximo", condition: "Condición de vida", mustBe: "Debe ser",
  atLeast: "al menos", atMost: "a lo sumo", threshold: "Umbral", law: "Probabilidad de cada escenario (deben sumar 1)",
  scenario: "Escenario", probability: "Probabilidad", actions: "Acciones, por paso", action: "Acción", effect: "Efecto", amount: "Cantidad",
  uses: "usa", adds: "aporta a", arrives: "llega a", consumed: "se consume de", available: "disponible de", step: "Paso ",
  recalc: "Recalcular con el kernel", working: "Modelando la decisión y calculando con el kernel.",
  steps: (n, unit) => unit ? "horizonte " + n + " × " + unit : n + " pasos", generated: "Generado el ", rule: "Primero la condición de vida y la PVS; después, para cada afectado, las rutas que ninguna otra supera en lo suyo. Sin sumar criterios.",
  locale: "es-AR",
  essentials: "Lo esencial", touches: (n, names) => "Esta decisión toca " + n + " de los 9 límites planetarios: " + names + ".",
  roomAll: (b, routes) => b + ": " + routes + " deja más margen en todos los escenarios.", roomMixed: b => b + ": la ruta que más margen deja cambia según el escenario.",
  conflict: "Los afectados no coinciden en la mejor ruta; mirá la sección 4.", agree: "Los afectados coinciden en la mejor ruta.",
  nine: "Los nueve checks", crossedNow: "cruzado hoy", safeNow: "en zona segura hoy", touched: "lo toca esta decisión",
  laws: "5. Leyes y marcos que aplican", lawsLead: "Piden a las empresas evaluar los impactos sobre los límites que toca esta decisión. Una guía, no asesoramiento legal.",
  examplesLabel: "O empezá con un ejemplo:", wait: s => "Llevamos " + s + " s. Suele tardar cerca de un minuto.",
  phases: ["La IA redacta el modelo: rutas, escenarios, personas y sistemas vivos afectados, existencias de cada límite.", "El validador lo revisa y lo devuelve si algo no cierra.", "El kernel calcula cada ruta en cada escenario."],
  examples: [
    {label: "Bodega en Mendoza", company: "Bodega mediana que exporta vino a Europa", place: "Mendoza, Argentina; riega del río Mendoza aguas abajo de Potrerillos", decision: "Si plantar 40 hectáreas más de viñedo en un año seco, mantener la superficie actual o pasar primero a riego por goteo en las 120 hectáreas actuales", horizon: "5 años"},
    {label: "Proveedor de algodón", company: "Marca de ropa que vende en Europa", place: "Compra algodón de Brasil y la India; confecciona en Bangladés", decision: "Si mantener el proveedor actual de algodón convencional, pasar a algodón orgánico certificado a mayor precio o llevar la mitad del volumen a fibras recicladas", horizon: "4 años"},
    {label: "Flota de reparto", company: "Empresa de logística con 300 camionetas diésel", place: "Gran Buenos Aires, Argentina", decision: "Si renovar la flota con camionetas diésel, pasar de a poco a camionetas eléctricas con cargadores en los depósitos o tercerizar la última milla", horizon: "6 años"},
  ],
};
const state = {csrf: null, data: null};

function node(tag, props = {}, ...children) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(props)) {
    if (k === "class") el.className = v; else el.setAttribute(k, v);
  }
  for (const child of children) if (child !== null && child !== undefined) el.append(child);
  return el;
}
function num(text) {
  if (text === null || text === undefined) return null;
  const [a, b] = String(text).split("/");
  return Number(a) / Number(b || 1);
}
function fmt(text) {
  const n = num(text);
  return n === null || Number.isNaN(n) ? "—" : n.toLocaleString(T.locale, {maximumFractionDigits: 2});
}
function pct(text) {
  const n = num(text);
  return n === null || Number.isNaN(n) ? T.noLaw : (n * 100).toLocaleString(T.locale, {maximumFractionDigits: 1}) + " %";
}
async function api(path, body) {
  const headers = {Accept: "application/json"};
  if (body !== undefined) {headers["Content-Type"] = "application/json"; headers["X-CSRF-Token"] = state.csrf || "";}
  const response = await fetch(path, {method: body === undefined ? "GET" : "POST", headers, credentials: "same-origin", cache: "no-store",
    body: body === undefined ? undefined : JSON.stringify(body)});
  let data = null;
  try {data = await response.json();} catch (_) {}
  if (!response.ok) {const error = new Error(data?.error?.message || T.failed); error.status = response.status; throw error;}
  return data;
}
function details(title, ...children) {
  return node("details", {class: "result-details"}, node("summary", {}, title), ...children);
}
function table(head, rows) {
  return node("div", {class: "compare-table-wrap"}, node("table", {class: "compare-table"},
    node("thead", {}, node("tr", {}, ...head.map(h => typeof h === "string" ? node("th", {}, h) : h))), node("tbody", {}, ...rows)));
}

function show(result) {
  const box = $("report");
  box.hidden = false;
  if (result.status === "NOT_A_DECISION") {box.replaceChildren(node("p", {}, result.explanation)); return;}
  if (result.status === "REFUSED") {box.replaceChildren(node("p", {class: "muted"}, T.refused)); return;}
  if (result.status === "MODEL_NOT_VALID") {
    box.replaceChildren(node("p", {}, T.notValid), details(T.rejected, node("ul", {}, ...(result.repairs || []).map(r => node("li", {}, r)))));
    return;
  }
  if (result.status === "KERNEL_ERROR") {box.replaceChildren(node("p", {}, T.kernel + result.error)); return;}
  const s = result.summary;
  const label = rid => s.route_labels[rid] || rid;
  const parts = [node("p", {class: "eyebrow"}, "GENIUS · " + (EN ? "DECISION REPORT" : "INFORME DE DECISIÓN")), node("h2", {}, s.name),
    node("p", {class: "small muted"}, T.generated + new Date().toLocaleDateString(T.locale) + " · " + T.steps(s.horizon, result.step_label) + " · " + s.routes.length + " " + (EN ? "routes" : "rutas") + " × " + s.scenarios.length + " " + (EN ? "scenarios" : "escenarios"))];
  if (result.recalculated) parts.push(node("p", {class: "badge"}, T.recalculated));
  const lang = EN ? "en" : "es";
  const boundaryName = id => (state.data?.boundaries.find(b => b.id === id)?.[lang].name) || id;
  const planetary = result.planetary || [];
  const touchedIds = [...new Set(planetary.map(b => b.boundary))];
  const essentials = node("div", {class: "essentials"}, node("p", {class: "eyebrow"}, "1. " + T.essentials.toUpperCase()));
  const keepIds = s.life_filter.keep_life_everywhere;
  const lostRoutes = s.routes.filter(r => r.loses_life_in.length);
  const verdict = node("div", {class: "verdict" + (keepIds.length ? "" : " alert")}, node("p", {}, node("strong", {}, T.life), s.life_condition),
    node("p", {}, keepIds.length ? T.keep + keepIds.map(label).join(", ") + "." : T.none));
  if (lostRoutes.length && keepIds.length) verdict.append(node("p", {}, T.dropped + lostRoutes.map(r => r.label).join(", ") + "."));
  essentials.append(verdict);
  essentials.append(node("p", {}, T.touches(touchedIds.length, touchedIds.map(boundaryName).join(", "))));
  for (const b of planetary) {
    const sets = Object.values(b.most_room);
    const always = sets.length ? sets.reduce((a, x) => a.filter(r => x.includes(r))) : [];
    const what = boundaryName(b.boundary) + " (" + b.label + ")";
    essentials.append(node("p", {class: "small"}, always.length ? T.roomAll(what, always.map(label).join(EN ? " or " : " o ")) : T.roomMixed(what)));
  }
  essentials.append(node("p", {class: "small"}, s.carriers_disagree ? T.conflict : T.agree));
  parts.push(essentials);

  const scen = s.scenarios;
  parts.push(node("h3", {}, T.lifeTable), table([T.route, ...scen.map(x => x.label + (x.probability ? " (" + pct(x.probability) + ")" : "")), "PVS"],
    s.routes.map(r => node("tr", {}, node("td", {}, r.label),
      ...scen.map(x => r.keeps_life_in.includes(x.id) ? node("td", {class: "ok"}, T.lives) : r.loses_life_in.includes(x.id) ? node("td", {class: "bad"}, T.lost) : node("td", {}, T.undecided)),
      node("td", {}, r.pvs.value !== null ? pct(r.pvs.value) : r.pvs.law_range ? pct(r.pvs.law_range.min) + "–" + pct(r.pvs.law_range.max) : "—")))));

  parts.push(node("h3", {}, T.planet));
  if (state.data) parts.push(node("div", {class: "nine", role: "list", "aria-label": T.nine}, ...state.data.boundaries.map(b => node("span", {
    role: "listitem", class: "nine-chip" + (b.crossed ? " crossed" : " safe") + (touchedIds.includes(b.id) ? " touched" : ""),
    title: (b.crossed ? T.crossedNow : T.safeNow) + (touchedIds.includes(b.id) ? " · " + T.touched : "")}, b[lang].name))));
  parts.push(node("p", {class: "small"}, T.planetLead));
  for (const b of result.planetary || []) {
    const name = b.boundary_label[EN ? 1 : 0];
    parts.push(node("h4", {}, name + " · " + b.label), node("p", {class: "small muted"}, fmt(b.initial) + " " + b.unit + " " + T.start + " · " + (b.direction === "higher" ? T.higher : T.lower)));
    parts.push(table([T.route, ...scen.map(x => x.label)], s.routes.map(r => node("tr", {}, node("td", {}, r.label),
      ...scen.map(x => {const c = b.by_scenario[x.id][r.id]; return node("td", {class: b.most_room[x.id].includes(r.id) ? "room" : ""}, fmt(c.final) + " (" + T.worst + " " + fmt(c.worst) + ")");})))));
  }

  parts.push(node("h3", {}, T.carriers), node("ul", {}, ...s.carriers.map(c => node("li", {}, node("strong", {}, c.label + ": "),
    c.best && c.best.length ? c.best.map(label).join(EN ? " or " : " o ") + (c.status === "UNIQUE" ? "" : T.tied) : T.noWelfare))));
  if (s.carriers_disagree) parts.push(node("p", {class: "small"}, T.disagree));
  const wb = details(T.wellbeing);
  for (const x of scen) {
    wb.append(node("p", {class: "small"}, node("strong", {}, x.label)), table([T.route, ...s.routes[0].wellbeing[x.id].map(w => w.label)],
      s.routes.map(r => node("tr", {}, node("td", {}, r.label), ...r.wellbeing[x.id].map(w => node("td", {}, fmt(w.final) + " (" + T.worst + " " + fmt(w.worst) + ")"))))));
  }
  parts.push(wb);
  const laws = (state.data?.laws || []).filter(x => x.boundaries.some(b => touchedIds.includes(b)));
  if (laws.length) {
    parts.push(node("h3", {}, T.laws), node("p", {class: "small muted"}, T.lawsLead), node("ul", {class: "laws"}, ...laws.map(x => node("li", {},
      node("a", {href: x.url}, x[lang].name), ": " + x[lang].asks + " ", node("span", {class: "muted"}, x[lang].who)))));
  }
  parts.push(node("h3", {}, T.hypotheses(s.assumptions.length)), node("ul", {class: "hypotheses"}, ...s.assumptions.map(a => node("li", {}, a.statement + " ", node("span", {class: "muted"}, "· " + a.provenance)))));
  parts.push(editor(result));
  const download = node("button", {type: "button", class: "text-button no-print"}, T.download);
  download.addEventListener("click", () => {
    const url = URL.createObjectURL(new Blob([JSON.stringify({model: result.model, boundaries: result.boundaries, step_label: result.step_label}, null, 2)], {type: "application/json"}));
    const a = node("a", {href: url, download: "genius-report-model.json"}); document.body.append(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
  const print = node("button", {type: "button", class: "button primary no-print"}, T.print);
  print.addEventListener("click", () => window.print());
  parts.push(node("p", {class: "small muted"}, T.rule), node("div", {class: "report-actions"}, print, download));
  box.replaceChildren(...parts);
  box.scrollIntoView({behavior: "smooth", block: "start"});
}

function shown(text) {
  if (text === null || text === undefined) return "";
  const [a, b = "1"] = String(text).split("/");
  if (b === "1") return a;
  let d = Number(b);
  for (const p of [2, 5]) while (d % p === 0) d /= p;
  return d === 1 ? String(Number(a) / Number(b)) : a + "/" + b;
}

// Every number the language model supposed, editable; the kernel recalculates without the AI.
function editor(result) {
  const model = JSON.parse(JSON.stringify(result.model));
  const changes = new Map();
  const stockLabel = Object.fromEntries(model.stocks.map(x => [x.id, x.label]));
  const field = (obj, key, what) => {
    const before = shown(obj[key]);
    const input = node("input", {class: "num-input", inputmode: "decimal", value: before, "aria-label": what});
    input.addEventListener("input", () => {
      const v = input.value.trim().replace(",", ".");
      if (v === "") delete obj[key]; else obj[key] = v;
      if (v === before) changes.delete(what); else changes.set(what, what + ": " + (before || "0") + " → " + (v || "0"));
    });
    return input;
  };
  const box = details(T.edit);
  box.classList.add("no-print");
  box.append(node("p", {class: "small"}, T.editLead));
  box.append(node("h4", {}, T.stocks), table([T.stock, T.initial, T.capacity], model.stocks.map(x =>
    node("tr", {}, node("td", {}, x.label + " (" + x.unit + ")"), node("td", {}, field(x, "initial", x.label + " " + T.initial)), node("td", {}, field(x, "capacity", x.label + " " + T.capacity))))));
  box.append(node("h4", {}, T.condition), table([T.stock, T.mustBe, T.threshold], model.task.conditions.map(c =>
    node("tr", {}, node("td", {}, stockLabel[c.stock]), node("td", {}, c.op === "ge" ? T.atLeast : T.atMost), node("td", {}, field(c, "threshold", T.threshold + " " + stockLabel[c.stock]))))));
  if (model.law) box.append(node("h4", {}, T.law), table([T.scenario, T.probability], model.scenarios.map(x =>
    node("tr", {}, node("td", {}, x.label), node("td", {}, field(model.law, x.id, T.probability + " " + x.label))))));
  const actionRows = [];
  for (const a of model.actions) for (const [kind, name] of [["withdrawals", T.uses], ["deposits", T.adds]])
    for (const stock of Object.keys(a[kind])) actionRows.push(node("tr", {}, node("td", {}, a.label), node("td", {}, name + " " + stockLabel[stock]), node("td", {}, field(a[kind], stock, a.label + " " + name + " " + stockLabel[stock]))));
  if (actionRows.length) box.append(node("h4", {}, T.actions), table([T.action, T.effect, T.amount], actionRows));
  const names = {inflows: T.arrives, drains: T.consumed, renewables: T.available};
  for (const sc of model.scenarios) {
    const pairs = [];
    for (const kind of ["inflows", "drains", "renewables"]) for (const stock of model.stocks.map(x => x.id))
      if (sc.events.some(e => e[kind] && stock in e[kind])) pairs.push([kind, stock]);
    if (!pairs.length) continue;
    box.append(node("h4", {}, T.scenario + ": " + sc.label), table(["", ...sc.events.map((_, i) => T.step + (i + 1))], pairs.map(([kind, stock]) =>
      node("tr", {}, node("td", {}, names[kind] + " " + stockLabel[stock]), ...sc.events.map((e, i) => node("td", {}, field(e[kind], stock, sc.label + ", " + T.step + (i + 1) + ", " + names[kind] + " " + stockLabel[stock])))))));
  }
  const button = node("button", {type: "button", class: "button primary"}, T.recalc);
  const error = node("p", {class: "form-error", role: "alert", hidden: ""});
  button.addEventListener("click", async () => {
    button.disabled = true; error.hidden = true;
    try {show(await api("/api/business/recalculate", {model, changes: [...changes.values()], boundaries: result.boundaries, step_label: result.step_label}));}
    catch (e) {error.textContent = e.message; error.hidden = false; button.disabled = false;}
  });
  box.append(button, error);
  return box;
}

// The report is computed in the background; ask for it every few seconds. A dropped poll (phone asleep, network
// switch) is retried instead of failing the whole report.
async function collect(job) {
  const until = Date.now() + 6 * 60 * 1000;
  let misses = 0;
  while (Date.now() < until) {
    await new Promise(resolve => setTimeout(resolve, 3000));
    let data;
    try {data = await api("/api/business/report/" + encodeURIComponent(job));}
    catch (error) {if (error.status || ++misses > 40) throw error; continue;}
    misses = 0;
    if (data.status !== "WORKING") return data;
  }
  throw new Error(T.failed);
}

async function submit(event) {
  event.preventDefault();
  const body = {lang: EN ? "en" : "es"};
  for (const key of ["company", "place", "decision", "options", "horizon"]) body[key] = $(key).value.trim();
  if (!body.decision) return;
  $("error").hidden = true;
  $("send").disabled = true;
  $("report").hidden = false;
  const started = Date.now();
  const clock = node("p", {class: "waiting"}, T.wait(0));
  $("report").replaceChildren(node("div", {class: "progress"}, node("span", {class: "spinner", "aria-hidden": "true"}),
    node("div", {}, node("p", {}, node("strong", {}, T.working)), node("ol", {class: "small"}, ...T.phases.map(x => node("li", {}, x))), clock)));
  $("report").scrollIntoView({behavior: "smooth", block: "start"});
  const timer = setInterval(() => {clock.textContent = T.wait(Math.round((Date.now() - started) / 1000));}, 1000);
  try {show(await collect((await api("/api/business/report", body)).job));}
  catch (error) {$("report").replaceChildren(node("p", {class: "bad"}, error.status ? error.message : T.offline));}
  clearInterval(timer);
  $("send").disabled = false;
}

async function start() {
  fetch("/static/boundaries.json", {cache: "no-cache"}).then(r => r.json()).then(d => {state.data = d;}).catch(() => {});
  try {
    const me = await api("/api/me");
    state.csrf = me.csrf_token;
    $("username-label").textContent = me.user.username;
    $("session").hidden = false;
  } catch (error) {
    if (error.status === 401) {$("login-needed").hidden = false; return;}
    $("error").textContent = error.message; $("error").hidden = false; return;
  }
  const status = await api("/api/compare/status").catch(() => ({enabled: false}));
  if (!status.enabled) {$("not-configured").hidden = false; return;}
  $("ask").hidden = false;
  $("ask").addEventListener("submit", submit);
  const box = $("examples");
  box.append(node("span", {class: "small muted"}, T.examplesLabel));
  for (const ex of T.examples) {
    const b = node("button", {type: "button", class: "chip"}, ex.label);
    b.addEventListener("click", () => {for (const k of ["company", "place", "decision", "horizon"]) $(k).value = ex[k] || ""; $("options").value = ""; $("decision").focus();});
    box.append(b);
  }
}

start();
