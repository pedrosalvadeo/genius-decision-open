'use strict';
(async function () {
  const status = document.getElementById('observatory-status');
  const names = {NOT_STARTED:'Todavía no iniciado', WAITING:'Esperando el próximo ciclo', WAITING_FOR_OUTCOME:'Esperando una medición posterior', OPERATOR_PAUSE:'En reposo por decisión del operador', RESOURCE_REST:'En reposo por recursos', STALE_OBSERVATIONS:'Esperando observaciones actuales', NO_OBSERVATIONS:'Sin observaciones disponibles', EVIDENCE_REVIEW:'Evidencia pendiente de revisión', SOURCE_CONFLICT_REVIEW:'La fuente publicó versiones en conflicto', SOURCE_UNAVAILABLE:'Fuente no disponible', SOURCE_ACCESS_REVIEW:'Acceso a la fuente pendiente de revisión', PAUSED_OR_REVIEW_REQUIRED:'En pausa: requiere revisión', REVOKED:'Autorización retirada', RETIREMENT_PENDING:'Retirada pendiente', REPORT_UNAVAILABLE:'Informe no disponible'};
  const date = value => value ? new Date(value).toLocaleString('es-AR') : '—';
  const temp = value => Number.isInteger(value) ? ((value-27315)/100).toLocaleString('es-AR', {maximumFractionDigits:2})+' °C' : '—';
  try {
    const response = await fetch('/network/organisms.json', {credentials:'omit',cache:'no-store'});
    if (!response.ok) throw new Error();
    const data = await response.json();
    status.textContent = 'Consulta: '+new Date(data.checked_at*1000).toLocaleString('es-AR')+'. Los informes se actualizan aproximadamente cada hora.';
    const root = document.getElementById('organisms');
    for (const row of data.organisms) {
      const section=document.createElement('section'), title=document.createElement('h2');
      title.textContent=row.label+' · '+row.station;section.appendChild(title);
      const p=document.createElement('p');p.textContent=(names[row.status]||row.status)+(row.report_stale?' · Informe sin actualizar: no confirma actividad actual.':'');section.appendChild(p);
      const dl=document.createElement('dl');
      const fields=[['Última observación',row.latest_observation ? temp(row.latest_observation.centikelvin)+' · '+date(row.latest_observation.observed_at) : 'Pendiente'],
        ['Última predicción',row.last_prediction ? temp(row.last_prediction.predicted_centikelvin)+' · registrada '+date(row.last_prediction.frozen_at) : 'Todavía no registrada'],
        ['Último error observado',row.last_scored ? (row.last_scored.absolute_error_centikelvin/100).toLocaleString('es-AR')+' °C · '+date(row.last_scored.observed_at) : 'Todavía no hay resultado posterior'],
        ['Resultados evaluados',row.organism?.scored_outcomes??0],['Mejoras confirmadas',row.organism?.locally_confirmed_changes??0],
        ['Experimentos archivados',row.organism?.archived_trials??0],['Identidad',row.node_id||'Pendiente']];
      for (const [key,value] of fields) {const dt=document.createElement('dt'),dd=document.createElement('dd');dt.textContent=key;dd.textContent=value;dd.style.overflowWrap='anywhere';dl.append(dt,dd);}
      section.appendChild(dl);root.appendChild(section);
    }
  } catch (_) {status.textContent='No pudimos consultar el estado actual. Volvé a intentar más tarde.';}
})();
