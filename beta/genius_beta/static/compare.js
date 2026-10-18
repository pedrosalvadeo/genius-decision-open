"use strict";
const $ = id => document.getElementById(id);
const state = {csrf: null};

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
  if (n === null || Number.isNaN(n)) return "—";
  return n.toLocaleString("es-AR", {maximumFractionDigits: 2});
}
function pct(text) {
  const n = num(text);
  if (n === null || Number.isNaN(n)) return "sin ley";
  return (n * 100).toLocaleString("es-AR", {maximumFractionDigits: 1}) + " %";
}

async function api(path, body) {
  const headers = {Accept: "application/json"};
  if (body !== undefined) {headers["Content-Type"] = "application/json"; headers["X-CSRF-Token"] = state.csrf || "";}
  const response = await fetch(path, {method: body === undefined ? "GET" : "POST", headers, credentials: "same-origin", cache: "no-store",
    body: body === undefined ? undefined : JSON.stringify(body)});
  let data = null;
  try {data = await response.json();} catch (_) {}
  if (!response.ok) {const error = new Error(data?.error?.message || "El servicio no pudo completar la solicitud."); error.status = response.status; throw error;}
  return data;
}

function showMarket(result) {
  const box = $("market");
  if (result.status === "REFUSED") {box.replaceChildren(node("p", {class: "muted"}, "La IA no quiso responder esta pregunta.")); return;}
  box.replaceChildren(node("div", {class: "market-text"}, result.text));
}

function label(summary, rid) {return summary.route_labels[rid] || rid;}

function showGenius(result) {
  const box = $("genius");
  if (result.status === "NOT_A_DECISION") {box.replaceChildren(node("p", {}, result.explanation)); return;}
  if (result.status === "REFUSED") {box.replaceChildren(node("p", {class: "muted"}, "La IA no quiso modelar esta pregunta.")); return;}
  if (result.status === "MODEL_NOT_VALID") {
    box.replaceChildren(node("p", {}, "La IA no logró escribir un modelo que el validador acepte, así que Genius no calcula nada. Probá con más detalle: qué opciones tenés, qué es incierto y a quién afecta."),
      details("Lo que rechazó el validador", node("ul", {}, ...(result.repairs || []).map(r => node("li", {}, r)))));
    return;
  }
  if (result.status === "KERNEL_ERROR") {box.replaceChildren(node("p", {}, "El modelo pasó la validación pero el kernel no pudo calcularlo: " + result.error)); return;}
  const s = result.summary;
  const parts = [node("h3", {}, s.name)];
  if (result.recalculated) parts.push(node("p", {class: "badge"}, "Recalculado por el kernel con tus correcciones"));
  const keep = s.life_filter.keep_life_everywhere;
  const verdict = node("div", {class: "verdict" + (keep.length ? "" : " alert")});
  verdict.append(node("p", {}, node("strong", {}, "Condición de vida: "), s.life_condition));
  if (keep.length) verdict.append(node("p", {}, "La conservan en todos los escenarios: " + keep.map(r => label(s, r)).join(", ") + "."));
  else verdict.append(node("p", {}, "Ninguna ruta la conserva en todos los escenarios. Genius no recomienda sacrificarla: hace falta buscar otra ruta."));
  const lost = s.routes.filter(r => r.loses_life_in.length);
  if (lost.length && keep.length) verdict.append(node("p", {}, "Quedan descartadas porque la pierden en algún escenario: " + lost.map(r => r.label).join(", ") + "."));
  parts.push(verdict);

  const scen = s.scenarios;
  const head = node("tr", {}, node("th", {}, "Ruta"), ...scen.map(x => node("th", {}, x.label + (x.probability ? " (" + pct(x.probability) + ")" : ""))), node("th", {}, "PVS"));
  const rows = s.routes.map(r => node("tr", {}, node("td", {}, r.label),
    ...scen.map(x => r.keeps_life_in.includes(x.id) ? node("td", {class: "ok"}, "✓ vive") : r.loses_life_in.includes(x.id) ? node("td", {class: "bad"}, "✗ se pierde") : node("td", {}, "indeciso")),
    node("td", {}, r.pvs.value !== null ? pct(r.pvs.value) : r.pvs.law_range ? pct(r.pvs.law_range.min) + "–" + pct(r.pvs.law_range.max) : "—")));
  parts.push(node("h3", {}, "Vida y PVS por ruta y escenario"), node("div", {class: "compare-table-wrap"}, node("table", {class: "compare-table"}, node("thead", {}, head), node("tbody", {}, ...rows))));

  parts.push(node("h3", {}, "Lo mejor para cada portador"));
  parts.push(node("ul", {}, ...s.carriers.map(c => node("li", {}, node("strong", {}, c.label + ": "),
    c.best && c.best.length ? c.best.map(r => label(s, r)).join(" o ") + (c.status === "UNIQUE" ? "" : " (empatadas o incomparables)") : "sin criterio de bienestar declarado"))));
  if (s.carriers_disagree) parts.push(node("p", {class: "small"}, "Los portadores no coinciden: lo mejor para uno no lo es para otro. Genius muestra el conflicto en vez de sumarlo en un número."));

  const wb = details("Bienestar de cada portador por escenario (final y peor momento)");
  for (const x of scen) {
    const carriersHead = s.routes[0].wellbeing[x.id].map(w => node("th", {}, w.label));
    const trs = s.routes.map(r => node("tr", {}, node("td", {}, r.label), ...r.wellbeing[x.id].map(w => node("td", {}, fmt(w.final) + " (peor " + fmt(w.worst) + ")"))));
    wb.append(node("p", {class: "small"}, node("strong", {}, x.label)), node("div", {class: "compare-table-wrap"}, node("table", {class: "compare-table"}, node("thead", {}, node("tr", {}, node("th", {}, "Ruta"), ...carriersHead)), node("tbody", {}, ...trs))));
  }
  parts.push(wb);
  parts.push(details("Hipótesis del modelo (" + s.assumptions.length + ")", node("ul", {}, ...s.assumptions.map(a => node("li", {}, a.statement + " ", node("span", {class: "muted"}, "· " + a.provenance))))));
  const link = node("button", {type: "button", class: "text-button"}, "Descargar el modelo completo (JSON)");
  link.addEventListener("click", () => {
    const url = URL.createObjectURL(new Blob([JSON.stringify(result.model, null, 2)], {type: "application/json"}));
    const a = node("a", {href: url, download: "genius-modelo.json"}); document.body.append(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
  parts.push(editor(result.model));
  parts.push(node("p", {class: "small muted"}, s.rule), link);
  box.replaceChildren(...parts);
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
function editor(original) {
  const model = JSON.parse(JSON.stringify(original));
  const changes = new Map();
  const stockLabel = Object.fromEntries(model.stocks.map(x => [x.id, x.label]));
  const field = (obj, key, what) => {
    const input = node("input", {class: "num-input", inputmode: "decimal", value: shown(obj[key]), "aria-label": what});
    const before = shown(obj[key]);
    input.addEventListener("input", () => {
      const v = input.value.trim().replace(",", ".");
      if (v === "") delete obj[key]; else obj[key] = v;
      if (v === before) changes.delete(what); else changes.set(what, what + ": " + (before || "0") + " → " + (v || "0"));
    });
    return input;
  };
  const table = (head, rows) => node("div", {class: "compare-table-wrap"}, node("table", {class: "compare-table"},
    node("thead", {}, node("tr", {}, ...head.map(h => node("th", {}, h)))), node("tbody", {}, ...rows)));
  const box = details("Corregir hipótesis y recalcular");
  box.append(node("p", {class: "small"}, "Cambiá cualquier número que la IA supuso. Se aceptan decimales o fracciones (por ejemplo 2.5 o 1/3). El kernel recalcula sin usar la IA."));
  box.append(node("h4", {}, "Existencias"), table(["Existencia", "Al inicio", "Máximo"], model.stocks.map(x =>
    node("tr", {}, node("td", {}, x.label + " (" + x.unit + ")"), node("td", {}, field(x, "initial", x.label + " al inicio")), node("td", {}, field(x, "capacity", x.label + " máximo"))))));
  box.append(node("h4", {}, "Condición de vida"), table(["Existencia", "Debe ser", "Umbral"], model.task.conditions.map(c =>
    node("tr", {}, node("td", {}, stockLabel[c.stock]), node("td", {}, c.op === "ge" ? "al menos" : "a lo sumo"), node("td", {}, field(c, "threshold", "Umbral de " + stockLabel[c.stock]))))));
  if (model.law) box.append(node("h4", {}, "Probabilidad de cada escenario (deben sumar 1)"), table(["Escenario", "Probabilidad"], model.scenarios.map(x =>
    node("tr", {}, node("td", {}, x.label), node("td", {}, field(model.law, x.id, "Probabilidad de " + x.label))))));
  const actionRows = [];
  for (const a of model.actions) for (const [kind, name] of [["withdrawals", "usa"], ["deposits", "aporta a"]])
    for (const stock of Object.keys(a[kind])) actionRows.push(node("tr", {}, node("td", {}, a.label), node("td", {}, name + " " + stockLabel[stock]), node("td", {}, field(a[kind], stock, a.label + " " + name + " " + stockLabel[stock]))));
  if (actionRows.length) box.append(node("h4", {}, "Acciones, por paso"), table(["Acción", "Efecto", "Cantidad"], actionRows));
  const names = {inflows: "llega a", drains: "se consume de", renewables: "disponible de"};
  for (const sc of model.scenarios) {
    const pairs = [];
    for (const kind of ["inflows", "drains", "renewables"]) for (const stock of model.stocks.map(x => x.id))
      if (sc.events.some(e => e[kind] && stock in e[kind])) pairs.push([kind, stock]);
    if (!pairs.length) continue;
    box.append(node("h4", {}, "Escenario: " + sc.label), table(["", ...sc.events.map((_, i) => "Paso " + (i + 1))], pairs.map(([kind, stock]) =>
      node("tr", {}, node("td", {}, names[kind] + " " + stockLabel[stock]), ...sc.events.map((e, i) => node("td", {}, field(e[kind], stock, sc.label + ", paso " + (i + 1) + ", " + names[kind] + " " + stockLabel[stock])))))));
  }
  const button = node("button", {type: "button", class: "button primary"}, "Recalcular con el kernel");
  const error = node("p", {class: "form-error", role: "alert", hidden: ""});
  button.addEventListener("click", async () => {
    button.disabled = true; error.hidden = true;
    try {showGenius(await api("/api/compare/recalculate", {model, changes: [...changes.values()]}));}
    catch (e) {error.textContent = e.message; error.hidden = false; button.disabled = false;}
  });
  box.append(button, error);
  return box;
}

function details(title, ...children) {
  return node("details", {class: "result-details"}, node("summary", {}, title), ...children);
}

async function ask(event) {
  event.preventDefault();
  const question = $("question").value.trim();
  if (!question) return;
  $("error").hidden = true;
  $("send").disabled = true;
  $("answers").hidden = false;
  $("market").replaceChildren(node("p", {class: "waiting"}, "Respondiendo…"));
  $("genius").replaceChildren(node("p", {class: "waiting"}, "Modelando la decisión y calculando con el kernel… puede tardar hasta dos minutos."));
  const fail = box => error => {$(box).replaceChildren(node("p", {class: "bad"}, error.message));};
  await Promise.all([
    api("/api/compare/market", {question}).then(showMarket, fail("market")),
    api("/api/compare/genius", {question}).then(showGenius, fail("genius")),
  ]);
  $("send").disabled = false;
}

async function start() {
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
  $("ask").addEventListener("submit", ask);
}

start();
