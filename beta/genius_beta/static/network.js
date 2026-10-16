'use strict';
(async function () {
  const status = document.getElementById('network-status');
  try {
    const paths = ['/network/manifest.json', '/network/nodes', '/network/worlds', '/network/hosts'];
    const values = await Promise.all(paths.map(async path => {
      const response = await fetch(path, {credentials: 'omit', cache: 'no-store'});
      if (!response.ok) throw new Error('Unavailable');
      return response.json();
    }));
    const [manifest, directory, catalog, hosting] = values;
    status.textContent = manifest.registration_available ? 'La incorporación de nodos está abierta, sujeta a la capacidad disponible.' : 'La incorporación está pausada. Los aportes publicados siguen disponibles para lectura.';
    document.getElementById('node-count').textContent = manifest.nodes;
    document.getElementById('recent-count').textContent = manifest.recently_seen_nodes;
    document.getElementById('view-count').textContent = manifest.public_views;
    function rows(id, values, empty) {
      const list = document.getElementById(id); list.replaceChildren();
      for (const text of values.length ? values : [empty]) {
        const item = document.createElement('li'); item.textContent = text; list.appendChild(item);
      }
    }
    rows('node-list', directory.nodes.map(n => `${n.label} · ${n.topics.join(', ')} · ${n.recently_seen ? 'actividad reciente' : 'sin actividad reciente'}`), 'Todavía no hay nodos registrados.');
    rows('world-list', catalog.worlds.map(w => `${w.world_id} · ${w.views} vistas · ${w.signing_nodes} claves aportantes`), 'Todavía no se publicaron vistas de sistemas.');
    rows('host-list', hosting.hosts.map(h => {
      const offer = h.signed_offer.offer;
      const state = h.disabled ? 'revocada' : Date.parse(offer.valid_until) <= Date.now() ? 'vencida' : 'publicada';
      return `${h.label} · oferta ${state} · hasta ${offer.max_births} nacimientos totales · ${h.active_requests} solicitudes activas · ${offer.worlds.map(w => w.world_id).join(', ')}`;
    }), 'Todavía no hay ofertas de alojamiento publicadas.');
  } catch (_) {
    status.textContent = 'No pudimos consultar el estado actual. Probá nuevamente más tarde; los enlaces de instalación siguen disponibles.';
    document.getElementById('node-list').textContent = 'Estado no disponible.';
    document.getElementById('world-list').textContent = 'Estado no disponible.';
    document.getElementById('host-list').textContent = 'Estado no disponible.';
  }
})();
