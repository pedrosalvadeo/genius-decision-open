// Home page: world indicators, the nine planetary boundaries, and how the kernel decides.
(function () {
  'use strict';
  var es = (document.documentElement.lang || '').indexOf('es') === 0;
  var t = function (en, sp) { return es ? sp : en; };
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var SVG = 'http://www.w3.org/2000/svg';

  function el(tag, attrs, text) {
    var node = document.createElement(tag);
    for (var k in attrs || {}) node.setAttribute(k, attrs[k]);
    if (text != null) node.textContent = text;
    return node;
  }
  function svg(tag, attrs) {
    var node = document.createElementNS(SVG, tag);
    for (var k in attrs || {}) node.setAttribute(k, attrs[k]);
    return node;
  }
  function getJSON(url, done) {
    fetch(url, { credentials: 'same-origin' }).then(function (r) { return r.ok ? r.json() : null; })
      .then(function (data) { if (data) done(data); }).catch(function () {});
  }

  // ---------- World indicators ----------
  var locale = es ? 'es-AR' : 'en-US';
  function fmt(value, unit) {
    var nf = function (o) { return new Intl.NumberFormat(locale, o).format(value); };
    if (unit === 't') return (value < 1e6 ? nf({ maximumFractionDigits: 0 }) : nf({ notation: 'compact', maximumFractionDigits: 1 })) + ' t';
    if (unit === 'km3') return nf({ maximumFractionDigits: 0 }) + ' km³';
    if (unit === 'Mha') return nf({ maximumFractionDigits: 0 }) + ' Mha';
    if (unit === 'kg/ha') return nf({ maximumFractionDigits: 0 }) + ' kg/ha';
    if (unit === 'ppm') return nf({ maximumFractionDigits: 0 }) + ' ppm';
    if (unit === 'pH') return nf({ minimumFractionDigits: 3, maximumFractionDigits: 3 });
    if (unit === 'index') return nf({ maximumFractionDigits: 0 });
    var digits = value < 10 ? 1 : 0;
    return nf({ maximumFractionDigits: digits, minimumFractionDigits: digits }) + ' %';
  }

  function chart(item, boundary) {
    var crossed = boundary && boundary.crossed;
    var card = el('article', { class: 'indicator ' + (crossed ? 'crossed' : 'safe') });
    var pts = item.points, first = pts[0], last = pts[pts.length - 1];
    var head = el('div', { class: 'indicator-head' });
    if (boundary) {
      var tag = el('p', { class: 'indicator-boundary' });
      tag.appendChild(el('span', null, boundary[es ? 'es' : 'en'].name));
      tag.appendChild(el('strong', null, crossed ? t('Crossed', 'Cruzado') : t('Safe zone', 'Zona segura')));
      head.appendChild(tag);
    }
    head.appendChild(el('h3', null, es ? item.es : item.en));
    var change = el('p', { class: 'indicator-change' });
    change.appendChild(el('span', { class: 'from' }, fmt(first[1], item.unit)));
    change.appendChild(el('span', { class: 'arrow', 'aria-hidden': 'true' }, '→'));
    change.appendChild(el('strong', null, fmt(last[1], item.unit)));
    head.appendChild(change);
    head.appendChild(el('p', { class: 'indicator-years' }, first[0] + ' – ' + last[0]));
    card.appendChild(head);

    var W = 320, H = 130, L = 4, R = 4, T = 10, B = 18;
    var x0 = first[0], x1 = last[0];
    var vals = pts.map(function (p) { return p[1]; });
    if (item.limit != null) vals.push(item.limit);
    var ymax = Math.max.apply(null, vals), ymin = 0;
    if (item.unit === 'ppm' || item.unit === 'pH' || item.unit === 'Mha') { // these never approach zero; show their own range
      ymin = Math.min.apply(null, vals); var pad = (ymax - ymin) * 0.12; ymin -= pad; ymax += pad;
    }
    var X = function (x) { return L + (x - x0) / (x1 - x0 || 1) * (W - L - R); };
    var Y = function (y) { return T + (1 - (Math.max(ymin, y) - ymin) / (ymax - ymin || 1)) * (H - T - B); };
    var line = pts.map(function (p, i) { return (i ? 'L' : 'M') + X(p[0]).toFixed(1) + ' ' + Y(p[1]).toFixed(1); }).join('');
    var plot = svg('svg', { viewBox: '0 0 ' + W + ' ' + H, class: 'indicator-plot', role: 'img',
      'aria-label': (es ? item.es : item.en) + ': ' + fmt(first[1], item.unit) + ' (' + first[0] + ') → ' + fmt(last[1], item.unit) + ' (' + last[0] + ')' });
    plot.appendChild(svg('line', { x1: L, x2: W - R, y1: H - B, y2: H - B, class: 'baseline' }));
    plot.appendChild(svg('path', { d: line + 'L' + X(x1) + ' ' + (H - B) + 'L' + X(x0) + ' ' + (H - B) + 'Z', class: 'area' }));
    if (item.limit != null) {
      plot.appendChild(svg('line', { x1: L, x2: W - R, y1: Y(item.limit), y2: Y(item.limit), class: 'limit' }));
      var lt = svg('text', { x: W - R, y: Y(item.limit) - 4, class: 'tick limit-label', 'text-anchor': 'end' });
      lt.textContent = t('boundary ', 'límite ') + fmt(item.limit, item.unit); plot.appendChild(lt);
    }
    var path = svg('path', { d: line, class: 'line' });
    plot.appendChild(path);
    plot.appendChild(svg('circle', { cx: X(x1), cy: Y(last[1]), r: 4, class: 'end' }));
    var lab0 = svg('text', { x: L, y: H - 3, class: 'tick' }); lab0.textContent = x0; plot.appendChild(lab0);
    var lab1 = svg('text', { x: W - R, y: H - 3, class: 'tick', 'text-anchor': 'end' }); lab1.textContent = x1; plot.appendChild(lab1);
    var cross = svg('line', { y1: T, y2: H - B, class: 'cross' });
    var dot = svg('circle', { r: 4, class: 'hover-dot' });
    plot.appendChild(cross); plot.appendChild(dot);
    var wrap = el('div', { class: 'plot-wrap' });
    var tip = el('div', { class: 'tip', 'aria-hidden': 'true' });
    wrap.appendChild(plot); wrap.appendChild(tip);
    function hover(evt) {
      var box = plot.getBoundingClientRect();
      var px = (evt.clientX - box.left) / box.width * W;
      var best = pts[0];
      pts.forEach(function (p) { if (Math.abs(X(p[0]) - px) < Math.abs(X(best[0]) - px)) best = p; });
      cross.setAttribute('x1', X(best[0])); cross.setAttribute('x2', X(best[0]));
      dot.setAttribute('cx', X(best[0])); dot.setAttribute('cy', Y(best[1]));
      tip.textContent = best[0] + ' · ' + fmt(best[1], item.unit);
      tip.style.left = (X(best[0]) / W * 100) + '%';
      wrap.classList.add('hovering');
    }
    wrap.addEventListener('pointermove', hover);
    wrap.addEventListener('pointerleave', function () { wrap.classList.remove('hovering'); });
    card.appendChild(wrap);
    var note = es ? item.note_es : item.note_en;
    if (note) card.appendChild(el('p', { class: 'indicator-note' }, note));
    var src = el('p', { class: 'indicator-source' });
    var a = el('a', { href: item.chart, rel: 'noopener' }, item.citation);
    src.appendChild(document.createTextNode(t('Source: ', 'Fuente: '))); src.appendChild(a);
    card.appendChild(src);
    var details = el('details', { class: 'indicator-data' });
    details.appendChild(el('summary', null, t('See the data', 'Ver los datos')));
    var table = el('table');
    var thead = el('tr'); thead.appendChild(el('th', null, t('Year', 'Año'))); thead.appendChild(el('th', null, t('Value', 'Valor')));
    table.appendChild(thead);
    pts.forEach(function (p) { var tr = el('tr'); tr.appendChild(el('td', null, p[0])); tr.appendChild(el('td', null, fmt(p[1], item.unit))); table.appendChild(tr); });
    details.appendChild(table); card.appendChild(details);
    // Draw the line when the card is first seen.
    if (!reduce && 'IntersectionObserver' in window) {
      var length = path.getTotalLength ? 1200 : 0;
      path.style.strokeDasharray = length; path.style.strokeDashoffset = length;
      new IntersectionObserver(function (entries, obs) {
        if (entries[0].isIntersecting) { card.classList.add('drawn'); path.style.strokeDashoffset = 0; obs.disconnect(); }
      }, { threshold: 0.35 }).observe(card);
    } else card.classList.add('drawn');
    return card;
  }

  var grid = document.getElementById('indicator-grid');
  if (grid) getJSON('/static/world-indicators.json', function (data) {
    getJSON('/static/boundaries.json', function (bounds) {
      var byId = {}; bounds.boundaries.forEach(function (b) { byId[b.id] = b; });
      var example = document.getElementById('indicator-example');
      grid.textContent = '';
      data.indicators.forEach(function (item) {
        var b = byId[item.boundary];
        if (example && item.id === 'ozone') {
          var intro = el('div', { class: 'example-copy' });
          intro.appendChild(el('p', { class: 'eyebrow' }, t('PROOF THAT IT CAN BE DONE', 'LA PRUEBA DE QUE SE PUEDE')));
          intro.appendChild(el('h3', null, t('The ozone layer, protected by deciding differently.', 'La capa de ozono, protegida al decidir distinto.')));
          intro.appendChild(el('p', null, t('In 1987 the world agreed in the Montreal Protocol to stop the substances that destroyed ozone. Their use fell 99 %, and the boundary is in the safe zone. The other boundaries need the same turn, in every decision.',
            'En 1987 el mundo acordó en el Protocolo de Montreal dejar las sustancias que destruían el ozono. Su uso cayó 99 % y el límite está en zona segura. Los otros límites necesitan el mismo giro, en cada decisión.')));
          example.appendChild(intro); example.appendChild(chart(item, b));
        } else grid.appendChild(chart(item, b));
      });
    });
  });

  // ---------- Nine planetary boundaries ----------
  var ring = document.getElementById('boundary-ring');
  if (ring) getJSON('/static/boundaries.json', function (data) {
    var list = document.getElementById('boundary-list');
    var n = data.boundaries.length, cx = 120, cy = 120, r1 = 70, r2 = 108, gap = 0.035;
    var plot = svg('svg', { viewBox: '0 0 240 240', role: 'img', 'aria-label': t('Nine planetary boundaries: ', 'Nueve límites planetarios: ') +
      data.boundaries.filter(function (b) { return b.crossed; }).length + t(' crossed', ' cruzados') });
    data.boundaries.forEach(function (b, i) {
      var a0 = (i / n) * 2 * Math.PI - Math.PI / 2 + gap, a1 = ((i + 1) / n) * 2 * Math.PI - Math.PI / 2 - gap;
      var p = function (r, a) { return (cx + r * Math.cos(a)).toFixed(1) + ' ' + (cy + r * Math.sin(a)).toFixed(1); };
      var d = 'M' + p(r1, a0) + 'L' + p(r2, a0) + 'A' + r2 + ' ' + r2 + ' 0 0 1 ' + p(r2, a1) + 'L' + p(r1, a1) + 'A' + r1 + ' ' + r1 + ' 0 0 0 ' + p(r1, a0) + 'Z';
      var seg = svg('path', { d: d, class: 'seg ' + (b.crossed ? 'crossed' : 'safe') });
      var title = svg('title'); title.textContent = b[es ? 'es' : 'en'].name + ' · ' + (b.crossed ? t('crossed', 'cruzado') : t('safe zone', 'zona segura'));
      seg.appendChild(title); plot.appendChild(seg);
      if (list) {
        var li = el('li', { class: b.crossed ? 'crossed' : 'safe' });
        li.appendChild(el('span', { class: 'mark', 'aria-hidden': 'true' }));
        li.appendChild(el('span', null, b[es ? 'es' : 'en'].name));
        li.appendChild(el('small', null, b.crossed ? t('crossed', 'cruzado') : t('safe zone', 'zona segura')));
        list.appendChild(li);
      }
    });
    var crossed = data.boundaries.filter(function (b) { return b.crossed; }).length;
    var big = svg('text', { x: cx, y: cy + 4, 'text-anchor': 'middle', class: 'ring-big' }); big.textContent = crossed + '/' + n;
    var small = svg('text', { x: cx, y: cy + 24, 'text-anchor': 'middle', class: 'ring-small' }); small.textContent = t('CROSSED TODAY', 'CRUZADOS HOY');
    plot.appendChild(big); plot.appendChild(small);
    ring.textContent = ''; ring.appendChild(plot);
  });

  // ---------- How the mathematics decides (the Earth twin, 2025-2105) ----------
  var stage = document.getElementById('decide-stage');
  if (!stage) return;
  var DECADE = 422; // GtCO2 emitted per decade at the 2025 rate (42.2 GtCO2 a year, Global Carbon Budget 2025)
  var routes = [
    { id: 'fast', name: t('Zero by 2045', 'A cero en 2045'), f: [0.75, 0.25] },
    { id: 'medium', name: t('Zero by 2065', 'A cero en 2065'), f: [1, 0.75, 0.5, 0.25] },
    { id: 'slow', name: t('Zero by 2085', 'A cero en 2085'), f: [1, 0.75, 0.5, 0.5, 0.25, 0.25] },
    { id: 'current', name: t('Current policies', 'Políticas actuales'), f: [1, 1, 1, 1, 1, 1, 1, 1] }
  ];
  var scenarios = [
    { name: t('More sensitive climate', 'Clima más sensible'), budget: 950 },
    { name: t('Central climate', 'Clima central'), budget: 1150 },
    { name: t('Less sensitive climate', 'Clima menos sensible'), budget: 1500 }
  ];
  var MAX = 1750;
  routes.forEach(function (r) {
    r.cum = []; var c = 0;
    for (var d = 0; d < 8; d++) { c += (r.f[d] || 0) * DECADE; r.cum.push(c); }
    r.total = c;
    r.cells = scenarios.map(function (s) {
      var lost = -1;
      for (var d = 0; d < 8; d++) if (r.cum[d] > s.budget + 1e-9) { lost = d; break; }
      return { lost: lost };
    });
    r.kept = r.cells.filter(function (c) { return c.lost < 0; }).length;
  });
  var decade = function (d) { return (2025 + 10 * d) + '–' + (2035 + 10 * d); };
  var pvsText = function (k) { return k === 3 ? '1' : k === 0 ? '0' : k + '/3'; };

  var matrix = stage.querySelector('.matrix');
  var head = el('div', { class: 'm-row m-head' });
  head.appendChild(el('div', { class: 'm-route' }, t('Route', 'Ruta')));
  scenarios.forEach(function (s) {
    var h = el('div', { class: 'm-scn' });
    h.appendChild(el('strong', null, s.name));
    h.appendChild(el('small', null, t('2 °C budget: ', 'Presupuesto 2 °C: ') + s.budget + ' GtCO₂'));
    head.appendChild(h);
  });
  head.appendChild(el('div', { class: 'm-pvs' }, 'PVS'));
  matrix.appendChild(head);
  routes.forEach(function (r) {
    var row = el('div', { class: 'm-row', 'data-route': r.id });
    var name = el('div', { class: 'm-route' });
    name.appendChild(el('strong', null, r.name));
    name.appendChild(el('small', null, new Intl.NumberFormat(locale).format(r.total) + t(' GtCO₂ by 2105', ' GtCO₂ hasta 2105')));
    row.appendChild(name);
    r.nodes = scenarios.map(function (s, j) {
      var cell = el('div', { class: 'm-cell' });
      var track = el('div', { class: 'track' });
      var fill = el('span', { class: 'fill' });
      var mark = el('span', { class: 'budget' });
      mark.style.left = (s.budget / MAX * 100) + '%';
      track.appendChild(fill); track.appendChild(mark);
      var label = el('span', { class: 'verdict' }, '');
      cell.appendChild(track); cell.appendChild(label);
      row.appendChild(cell);
      return { cell: cell, fill: fill, label: label, info: r.cells[j], budget: s.budget };
    });
    r.pvsNode = el('div', { class: 'm-pvs' }, '');
    row.appendChild(r.pvsNode);
    r.row = row;
    matrix.appendChild(row);
  });

  function setCell(r, n, d) { // show route r in scenario n after decade d (-1 = empty)
    var c = r.nodes[n], v = d < 0 ? 0 : r.cum[Math.min(d, 7)];
    c.fill.style.width = Math.min(v, MAX) / MAX * 100 + '%';
    var over = d >= 0 && c.info.lost >= 0 && d >= c.info.lost;
    c.cell.classList.toggle('over', over);
    c.cell.classList.toggle('done', d >= 7);
    c.cell.classList.toggle('keeps', d >= 7 && c.info.lost < 0);
    c.label.textContent = d < 7 ? (d >= 0 ? decade(d) : '') :
      (c.info.lost < 0 ? t('keeps life', 'conserva la vida') : t('loses life ', 'pierde la vida ') + decade(c.info.lost));
  }
  function fillAll(d) { routes.forEach(function (r) { scenarios.forEach(function (s, n) { setCell(r, n, d); }); }); }

  var carriers = [
    { name: t('Future generations', 'Generaciones futuras'), what: t('carbon budget left', 'presupuesto de carbono que queda'), best: 'fast', any: 'fast' },
    { name: t('Other species', 'Otras especies'), what: t('forests', 'bosques'), best: 'fast', any: 'fast' },
    { name: t('Fossil economies', 'Economías fósiles'), what: t('CO₂ they can emit', 'CO₂ que pueden emitir'), best: 'fast', any: 'current' }
  ];
  var carrierBox = stage.querySelector('.carriers');
  carriers.forEach(function (c) {
    var row = el('div', { class: 'carrier' + (c.any !== c.best ? ' conflict' : '') });
    row.appendChild(el('strong', null, c.name));
    row.appendChild(el('small', null, t('Wellbeing: ', 'Bienestar: ') + c.what));
    var nameOf = function (id) { return routes.filter(function (r) { return r.id === id; })[0].name; };
    row.appendChild(el('span', { class: 'pick' }, c.any !== c.best
      ? t('Would prefer ', 'Preferiría ') + nameOf(c.any) + t(', which loses life everywhere. Among routes that keep it: ', ', que pierde la vida en todos los escenarios. Entre las que la conservan: ') + nameOf(c.best)
      : t('Best route: ', 'Mejor ruta: ') + nameOf(c.best)));
    carrierBox.appendChild(row);
  });

  var steps = Array.prototype.slice.call(document.querySelectorAll('#decide-steps li'));
  var caption = stage.querySelector('.stage-caption');
  var timers = [], current = -1, playing = false, auto = null;
  function clear() { timers.forEach(clearTimeout); timers = []; }
  function later(fn, ms) { timers.push(setTimeout(fn, ms)); }

  function show(n, animate) {
    clear();
    current = n;
    stage.setAttribute('data-step', n);
    steps.forEach(function (li, i) { li.classList.toggle('active', i === n); li.classList.toggle('past', i < n); li.setAttribute('aria-current', i === n ? 'step' : 'false'); });
    caption.textContent = steps[n] ? steps[n].getAttribute('data-caption') : '';
    routes.forEach(function (r) { r.pvsNode.textContent = n >= 3 ? pvsText(r.kept) : ''; r.row.classList.toggle('dropped', n >= 4 && r.kept < 3); r.row.classList.toggle('chosen', n >= 6 && r.id === 'fast'); });
    if (n < 2) fillAll(-1);
    else if (n > 2 || !animate) fillAll(7);
    else { // the kernel walks every route through every scenario, decade by decade
      fillAll(-1);
      var k = 0;
      routes.forEach(function (r) {
        scenarios.forEach(function (s, j) {
          for (var d = 0; d < 8; d++) (function (d, at) { later(function () { setCell(r, j, d); }, at); })(d, k * 520 + d * 60);
          k++;
        });
      });
    }
  }
  var DURATION = [5200, 5200, 8200, 5200, 5600, 6400, 7000];
  function tick() {
    if (!playing) return;
    var next = current + 1 >= steps.length ? 0 : current + 1;
    show(next, true);
    auto = setTimeout(tick, DURATION[next] || 5000);
  }
  var playBtn = document.getElementById('decide-play');
  function setPlaying(on) {
    playing = on; clearTimeout(auto);
    playBtn.textContent = on ? t('Pause', 'Pausa') : t('Play', 'Reproducir');
    playBtn.setAttribute('aria-pressed', on ? 'true' : 'false');
    if (on) auto = setTimeout(tick, current < 0 ? 0 : DURATION[current] || 5000);
  }
  playBtn.addEventListener('click', function () { if (current >= steps.length - 1 && !playing) show(-1); setPlaying(!playing); });
  document.getElementById('decide-prev').addEventListener('click', function () { setPlaying(false); show(Math.max(0, current - 1), true); });
  document.getElementById('decide-next').addEventListener('click', function () { setPlaying(false); show(Math.min(steps.length - 1, current + 1), true); });
  steps.forEach(function (li, i) {
    var b = li.querySelector('button');
    if (b) b.addEventListener('click', function () { setPlaying(false); show(i, true); });
  });
  show(0, false);
  if (!reduce && 'IntersectionObserver' in window) {
    new IntersectionObserver(function (entries, obs) {
      if (entries[0].isIntersecting) { setPlaying(true); obs.disconnect(); }
    }, { threshold: 0.4 }).observe(stage);
  } else { playBtn.textContent = t('Play', 'Reproducir'); }
})();
