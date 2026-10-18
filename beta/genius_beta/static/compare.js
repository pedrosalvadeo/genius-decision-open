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
  parts.push(node("p", {class: "small muted"}, s.rule), link);
  box.replaceChildren(...parts);
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
