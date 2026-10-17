'use strict';
(() => {
  const $ = id => document.getElementById(id);
  const root = $('organisms'), status = $('observatory-status'), refresh = $('refresh');
  const names = {
    NOT_STARTED:'Todavía no iniciado', WAITING:'Esperando el próximo ciclo',
    WAITING_FOR_OUTCOME:'Esperando una nueva medición', OPERATOR_PAUSE:'En reposo por decisión del operador',
    RESOURCE_REST:'En reposo por recursos', STALE_OBSERVATIONS:'Observaciones desactualizadas',
    NO_OBSERVATIONS:'Sin observaciones disponibles', EVIDENCE_REVIEW:'Evidencia pendiente de revisión',
    SOURCE_CONFLICT_REVIEW:'Mediciones en conflicto', SOURCE_UNAVAILABLE:'Fuente no disponible',
    SOURCE_ACCESS_REVIEW:'Acceso a la fuente en revisión', PAUSED_OR_REVIEW_REQUIRED:'En pausa · requiere revisión',
    REVOKED:'Autorización retirada', RETIREMENT_PENDING:'Retirada pendiente', REPORT_UNAVAILABLE:'Informe no disponible'
  };
  const explanations = {
    NOT_STARTED:'Todavía no hay un informe de inicio para este observador.',
    WAITING:'El proceso espera su próximo ciclo. Este estado por sí solo no confirma una predicción nueva.',
    WAITING_FOR_OUTCOME:'La predicción ya fue registrada. El organismo espera una medición posterior para compararla con lo que anticipó.',
    OPERATOR_PAUSE:'El operador puso el organismo en reposo. Su memoria e identidad se conservan.',
    RESOURCE_REST:'El organismo está en reposo por disponibilidad de recursos. Conserva su experiencia.',
    STALE_OBSERVATIONS:'La fuente no aporta una medición suficientemente reciente para emitir otra predicción.',
    NO_OBSERVATIONS:'No llegaron mediciones utilizables. La ausencia de datos no cuenta como un resultado.',
    EVIDENCE_REVIEW:'La evidencia necesita revisión antes de continuar el experimento.',
    SOURCE_CONFLICT_REVIEW:'Hay versiones distintas para una misma medición. Se espera revisión antes de evaluarla.',
    SOURCE_UNAVAILABLE:'No se pudo consultar la fuente meteorológica. Los resultados anteriores siguen registrados.',
    SOURCE_ACCESS_REVIEW:'El acceso a la fuente necesita revisión del operador.',
    PAUSED_OR_REVIEW_REQUIRED:'El proceso encontró una condición que requiere revisión antes de continuar.',
    REVOKED:'El operador retiró la autorización de este organismo.',
    RETIREMENT_PENDING:'La retirada fue solicitada y todavía no terminó de confirmarse.',
    REPORT_UNAVAILABLE:'No se pudo leer un informe válido de este organismo.'
  };
  const reasons = {
    ENROLLMENT_REVIEW_REQUIRED:'El registro del organismo en la red necesita revisión. Todavía no se confirmó su incorporación.',
    IDENTITY_REVIEW_REQUIRED:'La identidad guardada necesita revisión antes de continuar.',
    GENERATION_LIMIT:'Se alcanzó el límite configurado de generaciones. El operador debe revisar la continuidad.',
    MEMORY_BUDGET:'Se alcanzó el presupuesto de memoria del organismo.',
    EVOLUTION_TRIAL_BUDGET:'Se alcanzó el límite de experimentos guardados.'
  };
  const methods = {lower_median:'Mediana inferior',mean_floor:'Promedio con redondeo inferior',last_value:'Último valor observado'};
  const phaseNames = {DISCOVERY:'Comparación de variantes',CONFIRMATION:'Confirmación con datos nuevos',ADOPTED:'Mejora adoptada',REJECTED:'Rasgos anteriores conservados',NO_IMPROVEMENT:'Ninguna variante mejoró el resultado',MISSED_TARGET:'Faltó una medición posterior',EVIDENCE_REVIEW:'Evidencia en revisión'};
  const number = value => Number.isFinite(value) && typeof value === 'number';
  const count = value => Number.isSafeInteger(value) && value >= 0;
  const fmt = value => number(value) ? value.toLocaleString('es-AR',{maximumFractionDigits:2}) : '—';
  const stamp = value => typeof value === 'number' ? value * 1000 : (typeof value === 'string' ? Date.parse(value) : NaN);
  const date = value => Number.isFinite(stamp(value)) ? new Date(stamp(value)).toLocaleString('es-AR',{dateStyle:'short',timeStyle:'short'}) : 'Sin registro';
  const temperature = value => Number.isInteger(value) ? fmt((value-27315)/100)+' °C' : 'Pendiente';
  const el = (tag, className, text) => {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  };
  const svg = (tag, attrs = {}, text) => {
    const node = document.createElementNS('http://www.w3.org/2000/svg',tag);
    Object.entries(attrs).forEach(([key,value]) => node.setAttribute(key,String(value)));
    if (text !== undefined) node.textContent = text;
    return node;
  };
  const stale = row => row.report_stale === true || (Number.isFinite(stamp(row.checked_at)) && Date.now()-stamp(row.checked_at)>10800000);
  const group = row => {
    if (stale(row)) return 'attention';
    if (['NOT_STARTED','REVOKED'].includes(row.status)) return 'pending';
    if (['WAITING','WAITING_FOR_OUTCOME'].includes(row.status)) return row.node_id && row.organism ? 'cycle' : 'pending';
    return 'attention';
  };
  const statistic = (label,value,help) => {
    const box=el('article','metric');box.append(el('span','',label),el('strong','',value),el('small','',help));return box;
  };
  const field = (dl,label,value) => dl.append(el('dt','',label),el('dd','',value));
  let latest = null, fingerprint = null, busy = false, timer = null;

  function summary(rows) {
    const available=rows.filter(r=>r.organism);
    const total = key => {
      const known=available.filter(r=>count(r.organism[key]));
      return {value:known.length ? fmt(known.reduce((sum,r)=>sum+r.organism[key],0)) : '—',
        help:known.length===rows.length && rows.length ? 'Acumulado en los informes' : 'Datos disponibles de '+known.length+' de '+rows.length};
    };
    const outcomes=total('scored_outcomes'),changes=total('locally_confirmed_changes');
    $('summary').replaceChildren(
      statistic('Organismos observados',fmt(rows.length),rows.filter(r=>group(r)==='cycle').length+' en ciclo de observación'),
      statistic('Requieren atención',fmt(rows.filter(r=>group(r)==='attention').length),'Pausas, faltantes o informes antiguos'),
      statistic('Resultados evaluados',outcomes.value,outcomes.help),
      statistic('Mejoras confirmadas',changes.value,changes.help)
    );
  }

  function history(card,row) {
    const valid = r => r && number(r.actual_centikelvin) && number(r.predicted_centikelvin) &&
      number(r.absolute_error_centikelvin) && Number.isFinite(stamp(r.observed_at));
    const items=Array.isArray(row.recent_results) ? row.recent_results.filter(valid).slice(-24) : [];
    if (!items.length && valid(row.last_scored)) items.push(row.last_scored);
    card.append(el('h4','card-subtitle','Lo previsto y lo que ocurrió'));
    if (!items.length) {
      card.append(el('p','empty-history','Todavía no hay resultados posteriores evaluados para dibujar una evolución. El gráfico aparecerá cuando lleguen.'));return;
    }
    items.sort((a,b)=>stamp(a.observed_at)-stamp(b.observed_at));
    const figure=el('figure','history-chart');
    const chart=svg('svg',{viewBox:'0 0 440 190',role:'img','aria-labelledby':'chart-title-'+row.station});
    chart.append(svg('title',{id:'chart-title-'+row.station},'Temperatura observada y predicha: '+items.length+' resultados. Valores exactos en la tabla siguiente.'));
    const values=items.flatMap(r=>[(r.actual_centikelvin-27315)/100,(r.predicted_centikelvin-27315)/100]);
    const lo=Math.floor(Math.min(...values)-1),hi=Math.ceil(Math.max(...values)+1);
    const start=stamp(items[0].observed_at),end=stamp(items[items.length-1].observed_at);
    const x=i=>end===start?242:48+(stamp(items[i].observed_at)-start)*376/(end-start),y=v=>146-(v-lo)*124/(hi-lo);
    [lo,(lo+hi)/2,hi].forEach(v=>{
      chart.append(svg('line',{x1:48,y1:y(v),x2:424,y2:y(v),class:'chart-grid'}),svg('text',{x:40,y:y(v)+4,'text-anchor':'end',class:'chart-label'},fmt(v)+'°'));
    });
    chart.append(svg('text',{x:48,y:174,class:'chart-label'},date(items[0].observed_at)));
    if (items.length>1) chart.append(svg('text',{x:424,y:174,'text-anchor':'end',class:'chart-label'},date(items[items.length-1].observed_at)));
    [['actual_centikelvin','actual'],['predicted_centikelvin','predicted']].forEach(([key,kind])=>{
      if(items.length>1) chart.append(svg('polyline',{points:items.map((r,i)=>x(i)+','+y((r[key]-27315)/100)).join(' '),class:kind+'-line'}));
      items.forEach((r,i)=>{
        const dot=svg('circle',{cx:x(i),cy:y((r[key]-27315)/100),r:3.5,class:kind+'-dot'});
        dot.append(svg('title',{},date(r.observed_at)+' · '+(kind==='actual'?'Observada':'Predicha')+': '+temperature(r[key])));chart.append(dot);
      });
    });
    const legend=el('div','chart-legend');legend.append(el('span','','Observada'),el('span','','Predicha'));
    const caption=el('figcaption','history-caption',items.length+' resultado'+(items.length===1?'':'s')+' disponible'+(items.length===1?'':'s')+' · hasta los 24 más recientes. Cada punto compara la predicción con su medición posterior.');
    figure.append(chart,legend,caption);card.append(figure);
    const details=el('details','history-details');details.id='history-'+row.station;
    details.append(el('summary','','Ver valores y fechas'));
    const wrap=el('div','history-table-wrap'),table=el('table','history-table');
    table.append(el('caption','','Temperaturas y error absoluto, en °C.'));
    const head=el('thead'),header=el('tr');['Medición posterior','Predicha','Observada','Error'].forEach(t=>{const th=el('th','',t);th.scope='col';header.append(th);});head.append(header);
    const body=el('tbody');items.forEach(r=>{const tr=el('tr');[date(r.observed_at),fmt((r.predicted_centikelvin-27315)/100),fmt((r.actual_centikelvin-27315)/100),fmt(r.absolute_error_centikelvin/100)].forEach(v=>tr.append(el('td','',v)));body.append(tr);});
    table.append(head,body);wrap.append(table);details.append(wrap);card.append(details);
  }

  function progress(card,row) {
    card.append(el('h4','card-subtitle','Experimento en curso'));
    const trials=Array.isArray(row.organism?.trial_progress)?row.organism.trial_progress:[];
    const trial=trials.find(t=>['DISCOVERY','CONFIRMATION'].includes(t.status));
    if (!trial || !count(trial.discovery_scored) || !count(trial.confirmation_scored) || !count(trial.phase_size) || !trial.phase_size) {
      const known=Object.values(row.organism?.trials||{}).map(v=>phaseNames[v]||'Estado por revisar');
      card.append(el('p','progress-copy',known.length ? known.join(' · ')+'. El detalle de avance todavía no está disponible.' : 'Sin un experimento en curso informado. El progreso aparecerá cuando el organismo publique su siguiente informe.'));return;
    }
    card.append(el('p','progress-copy',phaseNames[trial.status]+(trial.pending_outcome?' · esperando el próximo resultado.':'.')));
    const stages=el('div','trial-progress');
    [['Comparar',trial.discovery_scored],['Confirmar',trial.confirmation_scored]].forEach(([label,value])=>{
      const stage=el('div','trial-stage'),bar=el('progress');bar.max=trial.phase_size;bar.value=Math.min(value,trial.phase_size);
      bar.setAttribute('aria-label',label+': '+value+' de '+trial.phase_size+' resultados');
      stage.append(el('span','',label+' · '+value+' / '+trial.phase_size),bar);stages.append(stage);
    });card.append(stages);
  }

  function card(row) {
    const section=el('article','organism-card');section.id='seed-'+row.station;section.dataset.group=group(row);
    section.setAttribute('aria-labelledby','title-'+row.station);
    const heading=el('div','card-heading'),avatar=el('span','organism-avatar','g');avatar.setAttribute('aria-hidden','true');
    const title=el('h3','',row.label||row.station);title.id='title-'+row.station;
    const identity=el('div');identity.append(title,el('span','station-label',row.station+' / OBSERVADOR DE TEMPERATURA'));heading.append(avatar,identity);
    const badges=el('div','state-line');badges.append(el('span','state-badge '+group(row),names[row.status]||'Estado por revisar'));
    if(stale(row))badges.append(el('span','state-badge stale','Informe desactualizado'));
    section.append(heading,badges,el('p','state-explanation',reasons[row.reason]||explanations[row.status]||'El informe contiene un estado todavía no reconocido por el visualizador.'));
    if(stale(row))section.append(el('p','notice','Este informe tiene más de tres horas. Describe el último estado conocido y no confirma actividad actual.'));
    const times=el('p','report-time');times.append(el('span','','Informe del organismo: '+date(row.checked_at)));
    if(number(row.next_check_at)&&row.next_check_at>0)times.append(el('span','','Próxima comprobación prevista: '+date(row.next_check_at)+(row.next_check_at*1000<Date.now()?' · fecha ya transcurrida':'')));
    section.append(times);
    const temperatures=el('dl','temperature-grid');
    const observed=el('div');observed.append(el('dt','','Última temperatura observada'),el('dd','',temperature(row.latest_observation?.centikelvin)),el('small','',row.latest_observation?'Medida: '+date(row.latest_observation.observed_at):'Esperando una medición de la fuente'));
    const predicted=el('div');predicted.append(el('dt','','Última predicción registrada'),el('dd','',temperature(row.last_prediction?.predicted_centikelvin)),el('small','',row.last_prediction?'Registrada: '+date(row.last_prediction.frozen_at):'Todavía no hay una predicción'));
    temperatures.append(observed,predicted);section.append(temperatures);
    const stats=el('dl','card-stats');
    [['Resultados evaluados',row.organism?.scored_outcomes],['Mejoras confirmadas',row.organism?.locally_confirmed_changes],['Último error',row.last_scored?.absolute_error_centikelvin]].forEach(([label,value])=>{
      const box=el('div');field(box,label,label==='Último error'?(number(value)?fmt(value/100)+' °C':'—'):(count(value)?fmt(value):'—'));stats.append(box);
    });section.append(stats);
    const cycle=el('ol','life-cycle');cycle.setAttribute('aria-label','Hitos registrados, no porcentaje de autonomía');
    [['Identidad',!!row.node_id],['Observación',!!row.latest_observation],['Predicción',!!row.last_prediction],['Evaluación',!!row.last_scored]].forEach(([label,done])=>{
      const li=el('li',done?'done':'',label);li.append(el('small','',done?'Registrada':'Pendiente'));cycle.append(li);
    });section.append(cycle);
    progress(section,row);history(section,row);
    const details=el('details','technical-details');details.id='details-'+row.station;details.append(el('summary','','Identidad, genes y memoria'));
    const info=el('dl');field(info,'Identidad del organismo',row.node_id||'Registro pendiente');
    const o=row.organism;
    if(o){
      field(info,'Linaje',o.parent_node_id?'Descendiente de '+o.parent_node_id:'Fundador · sin progenitor registrado');
      field(info,'Genes de origen',(methods[o.founder_genes?.estimator]||'Método no informado')+' · ventana de '+(count(o.founder_genes?.window)?o.founder_genes.window:'—')+' observaciones');
      if(count(o.founder_generation))field(info,'Generación de origen',String(o.founder_generation));
      (Array.isArray(o.context_traits)?o.context_traits:[]).forEach(t=>{
        field(info,'Rasgos adaptados al contexto',(methods[t.genes?.estimator]||'Método no informado')+' · ventana de '+(count(t.genes?.window)?t.genes.window:'—')+' · generación '+(count(t.generation)?t.generation:'—'));
        field(info,'Evidencia del rasgo',t.evidence==='INHERITED_TRAIT_NOT_LOCAL_VALIDATION'?'Heredado; todavía sin validación local':t.evidence==='LOCAL_PROSPECTIVE_OPERATIONAL_COMPARISON'?'Mejora confirmada con resultados posteriores en este contexto':'Evidencia no reconocida; consultar el informe público');
      });
      field(info,'Experimentos archivados',count(o.archived_trials)?String(o.archived_trials):'Sin dato');
    }else field(info,'Genes y memoria','Todavía no hay información publicada.');
    if(row.last_archive)field(info,'Último experimento cerrado',phaseNames[row.last_archive.status]||row.last_archive.status);
    if(row.reason)field(info,'Código de revisión',String(row.reason));
    field(info,'Bienestar y PVS','Sin medir');details.append(info);section.append(details);
    const link=el('a','card-link','Enlace directo a este observador ↗');link.href='/organisms#'+section.id;section.append(link);
    return section;
  }

  function filter() {
    const value=$('status-filter').value;let visible=0;
    root.querySelectorAll('.organism-card').forEach(node=>{node.hidden=value!=='all'&&node.dataset.group!==value;if(!node.hidden)visible++;});
    $('empty-filter').hidden=!latest || !latest.organisms.length || visible>0;
  }
  function render(data) {
    const signature=JSON.stringify(data.organisms.map(r=>({...r,report_stale:stale(r)})));
    summary(data.organisms);
    if(signature!==fingerprint){
      const opened=new Set(Array.from(root.querySelectorAll('details[open]'),d=>d.id));
      const focused=document.activeElement?.closest('details')?.id;
      root.replaceChildren(...data.organisms.map(card));
      if(!data.organisms.length)root.append(el('p','empty-state','Todavía no hay organismos publicados en este observatorio.'));
      opened.forEach(id=>{const d=$(id);if(d)d.open=true;});
      if(focused)$(focused)?.querySelector('summary')?.focus();
      fingerprint=signature;
    }
    filter();
  }
  async function load() {
    if(busy)return;
    clearTimeout(timer);busy=true;refresh.disabled=true;root.setAttribute('aria-busy','true');
    const controller=new AbortController(),timeout=setTimeout(()=>controller.abort(),15000);
    try{
      const response=await fetch('/network/organisms.json',{credentials:'omit',cache:'no-store',signal:controller.signal});
      if(!response.ok)throw new Error('http');
      const data=await response.json();
      if(data.format!=='genius-living-observatory/1'||!number(data.checked_at)||!Array.isArray(data.organisms)||data.organisms.some(r=>!r||typeof r.station!=='string'||!/^[A-Z0-9_-]{1,20}$/.test(r.station)))throw new Error('format');
      const first=!latest;latest=data;render(data);
      status.textContent='Consulta del panel: '+date(data.checked_at)+'. Actualización automática cada minuto.';
      $('connection-note').hidden=true;
      if(first&&location.hash.startsWith('#seed-')){
        const target=$(location.hash.slice(1));if(target)target.scrollIntoView();
      }
    }catch(_){
      status.textContent=latest?'No se pudo actualizar. Última consulta correcta: '+date(latest.checked_at)+'.':'No se pudo consultar el estado actual.';
      const note=$('connection-note');note.hidden=false;
      note.textContent=latest?'Se conserva el último informe recibido. La actividad actual no está confirmada; podés volver a intentar con “Actualizar datos”.':'No hay datos disponibles para mostrar. Volvé a intentar con “Actualizar datos”.';
      if(latest)render(latest);else root.replaceChildren(el('p','empty-state','Esperando conexión con el observatorio.'));
    }finally{
      clearTimeout(timeout);busy=false;refresh.disabled=false;root.setAttribute('aria-busy','false');
      if(!document.hidden)timer=setTimeout(load,60000);
    }
  }
  refresh.addEventListener('click',load);$('status-filter').addEventListener('change',filter);
  document.addEventListener('visibilitychange',()=>{clearTimeout(timer);if(!document.hidden)load();});
  load();
})();
