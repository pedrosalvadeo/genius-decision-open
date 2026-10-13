"use strict";
// Guided explicit interpretation. No LLM, narrative extraction or external data.
window.GeniusChoice = (() => {
  let api, root, criteria = [], alternatives = [], sequence = 0, confirmation = null;
  const $ = id => document.getElementById(id);
  const number = value => String(value).replace(/^(-?\d+)\/1$/, '$1');
  const el = (tag, content, cls) => {const n = document.createElement(tag); if (content !== undefined) n.textContent = content; if (cls) n.className = cls; return n;};
  const button = (label, action) => {const n = el('button',label,'text-button'); n.type='button'; n.addEventListener('click',action); return n;};
  function field(parent, label, value, setter, max=80, placeholder='') {
    const id='choice-field-'+(++sequence), l=el('label',label), input=el('input'); l.htmlFor=id; input.id=id; input.value=value??''; input.maxLength=max; input.placeholder=placeholder;
    input.addEventListener('input',()=>{setter(input.value); invalidate();}); parent.append(l,input); return input;
  }
  function select(parent,label,values,current,setter) {
    const id='choice-select-'+(++sequence), l=el('label',label), s=el('select');l.htmlFor=id;s.id=id;
    for(const [value,label] of values){const o=el('option',label);o.value=value;s.append(o);}s.value=current;
    s.addEventListener('change',()=>{setter(s.value);invalidate();});parent.append(l,s);return s;
  }
  function invalidate() {confirmation=null; $('choice-confirm').checked=false; $('choice-review-result').replaceChildren(); $('choice-confirm-box').hidden=true;}
  function numeric(value) {return value.trim() ? value.trim().replace(',','.') : null;}
  function model() {
    return {context:{question:$('choice-question').value.trim(),category:$('choice-category').value,horizon:$('choice-horizon').value.trim()},
      criteria:criteria.map(c=>({...c,label:c.label.trim(),unit:c.unit.trim(),limit:numeric(c.limit??'')})),
      alternatives:alternatives.map(a=>({id:a.id,label:a.label.trim(),source:a.source.trim(),values:Object.fromEntries(criteria.map(c=>[c.id,numeric(a.values[c.id]??'')]))})),
      selection:{mode:$('choice-selection').value,criteria_order:$('choice-selection').value==='unique'?[]:[...$('choice-priorities').querySelectorAll('select')].map(s=>s.value)}};
  }
  function renderCriteria() {
    const host=$('choice-criteria');host.replaceChildren();
    for(const c of criteria){const card=el('div',undefined,'choice-editor');
      field(card,'Criterio',c.label,v=>{c.label=v;},60,'Tiempo de viaje');
      field(card,'Unidad o escala común',c.unit,v=>{c.unit=v;},30,'Minutos');
      select(card,'Qué preferís', [['min','Menos es mejor'],['max','Más es mejor']],c.direction,v=>{c.direction=v;renderValues();});
      field(card,'Límite obligatorio (opcional)',c.limit,v=>{c.limit=v;},32,'Vacío = sin límite');
      card.append(el('p','Con “menos”, el límite es un máximo. Con “más”, es un mínimo. Usá la misma unidad para todas las alternativas.','field-help'));
      card.append(button('Quitar criterio',()=>{if(criteria.length<=1)return;criteria=criteria.filter(x=>x.id!==c.id);invalidate();renderCriteria();renderValues();renderPriorities();}));host.append(card);
    }
    $('choice-add-criterion').disabled=criteria.length>=5;
  }
  function renderAlternatives() {
    const host=$('choice-alternatives');host.replaceChildren();
    for(const a of alternatives){const card=el('div',undefined,'choice-editor');
      field(card,'Alternativa',a.label,v=>{a.label=v;},80,'Pasear por el parque');
      field(card,'De dónde salen sus datos',a.source,v=>{a.source=v;},200,'Por ejemplo: estimación propia; duración consultada hoy');
      card.append(button('Quitar alternativa',()=>{if(alternatives.length<=2)return;alternatives=alternatives.filter(x=>x.id!==a.id);invalidate();renderAlternatives();renderValues();}));host.append(card);
    }
    $('choice-add-alternative').disabled=alternatives.length>=8;
  }
  function renderValues() {
    const host=$('choice-values');host.replaceChildren();
    for(const a of alternatives){const card=el('div',undefined,'choice-editor');card.append(el('h3',a.label||'Alternativa sin nombre'));
      for(const c of criteria){const i=field(card,(c.label||'Criterio')+' · '+(c.unit||'unidad pendiente'),a.values[c.id],v=>{a.values[c.id]=v;},32,'Vacío = desconocido');i.dataset.alternative=a.id;i.dataset.criterion=c.id;i.inputMode='decimal';}
      host.append(card);
    }
  }
  function renderPriorities(order) {
    const host=$('choice-priorities');const previous=order||[...host.querySelectorAll('select')].map(s=>s.value);host.replaceChildren();host.hidden=$('choice-selection').value!=='lexicographic';
    criteria.forEach((c,i)=>select(host,'Prioridad '+(i+1),criteria.map(c=>[c.id,c.label||'Criterio sin nombre']),previous[i]&&criteria.some(c=>c.id===previous[i])?previous[i]:c.id,()=>{}));
  }
  function step(n) {
    root.querySelectorAll('[data-choice-step]').forEach(s=>s.hidden=Number(s.dataset.choiceStep)!==n);
    $('choice-step-label').textContent='Paso '+n+' de 4';
    if(n===3)renderValues();if(n===4)renderPriorities();
    root.querySelector('[data-choice-step="'+n+'"] h3').focus();
  }
  function reset() {
    criteria=[{id:'c1',label:'',unit:'',direction:'min',limit:null}];
    alternatives=[{id:'a1',label:'',source:'',values:{}},{id:'a2',label:'',source:'',values:{}}];
    $('choice-question').value='';$('choice-horizon').value='';$('choice-category').value='leisure';$('choice-selection').value='unique';
    invalidate();renderCriteria();renderAlternatives();renderPriorities([]);step(1);
  }
  function load(input) {
    criteria=JSON.parse(JSON.stringify(input.criteria));alternatives=JSON.parse(JSON.stringify(input.alternatives));
    $('choice-question').value=input.context.question;$('choice-horizon').value=input.context.horizon;$('choice-category').value=input.context.category;$('choice-selection').value=input.selection.mode;
    invalidate();renderCriteria();renderAlternatives();renderPriorities(input.selection.criteria_order);step(1);
  }
  function read() {
    if(!confirmation||!$('choice-confirm').checked)throw Error('En el paso 4, revisá la comparación y confirmá que representa tu decisión.');
    return {...model(),model_confirmation:confirmation};
  }
  function table(model, host) {
    const wrap=el('div',undefined,'choice-table-wrap'),table=el('table',undefined,'quality-table');
    const head=el('tr');head.append(el('th','Alternativa'));for(const c of model.criteria)head.append(el('th',c.label+' ('+c.unit+')'));const thead=el('thead');thead.append(head);table.append(thead);
    const body=el('tbody');for(const a of model.alternatives){const row=el('tr');row.append(el('th',a.label));for(const c of model.criteria)row.append(el('td',a.values[c.id]??'Desconocido'));body.append(row);}table.append(body);wrap.append(table);host.append(wrap);
  }
  function details(label,data){const d=el('details',undefined,'result-details');d.append(el('summary',label),el('pre',JSON.stringify(data,null,2)));return d;}
  function render(output, host) {
    const labels={RECOMMENDED_CONDITIONAL:'Recomendación según tus datos',NEEDS_INFORMATION:'Falta información para recomendar',NO_FEASIBLE_ALTERNATIVE:'Ninguna opción cumple los límites',PREFERENCE_OR_TIE:'Hay varias opciones; falta distinguirlas'};
    const m=output.model, a=Object.fromEntries(m.alternatives.map(a=>[a.id,a.label])), c=Object.fromEntries(m.criteria.map(c=>[c.id,c.label]));
    const card=el('section',undefined,'card result-card');card.append(el('p','COMPARACIÓN GUIADA','eyebrow'),el('h2',labels[output.state]||output.state));
    if(output.recommendation)card.append(el('h3',a[output.recommendation]));card.append(el('p',output.explanation));
    card.append(el('p',m.selection.mode==='unique'?'Regla confirmada: elegir sólo si queda una opción no superada.':'Regla confirmada: priorizar '+m.selection.criteria_order.map(k=>c[k]).join(' → ')+'. Cada criterio siguiente se usa sólo cuando el anterior empata.'));
    if(output.evidence_origin==='synthetic')card.append(el('p','Ejemplo sintético: demuestra el funcionamiento; no es evidencia de uso real.','field-help'));
    card.append(el('h3','Datos que comparaste'));table(m,card);
    for(const criterion of m.criteria)card.append(el('p',criterion.label+': '+(criterion.direction==='min'?'menos':'más')+' es mejor'+(criterion.limit===null?'; sin límite obligatorio.':'; '+(criterion.direction==='min'?'máximo ':'mínimo ')+criterion.limit+' '+criterion.unit+'.'),'field-help'));
    card.append(el('h3',output.frontier_complete?'Opciones no superadas en tus criterios':'Opciones comparables hasta ahora (conjunto incompleto)'),el('p',output.frontier.map(id=>a[id]).join(', ')||'Ninguna en el resultado disponible.'));
    if(output.tradeoffs.length){card.append(el('h3','Qué cedés con esta elección'));for(const t of output.tradeoffs)card.append(el('p',a[t.alternative]+' tiene un valor más favorable en '+c[t.criterion]+': '+number(t.other_value)+' frente a '+number(t.selected_value)+' '+t.unit+'.'));}
    if(output.excluded.length){card.append(el('h3','Opciones fuera de tus límites'));for(const x of output.excluded)for(const v of x.violations)card.append(el('p',a[x.alternative]+': '+c[v.criterion]+' = '+number(v.value)+'; el límite '+(v.direction==='min'?'máximo':'mínimo')+' es '+number(v.bound)+'.'));}
    if(output.dominated.length){card.append(el('h3','Opciones superadas'));for(const x of output.dominated)card.append(el('p',a[x.policy]+' queda superada por '+x.by.map(id=>a[id]).join(', ')+': igual o mejor en todos los criterios y mejor en al menos uno.'));}
    if(output.questions.length){card.append(el('h3','Qué falta aclarar'));for(const q of output.questions)card.append(el('p',q.question));}
    card.append(el('h3','Próximo paso'),el('p',output.next_action),el('p','Podés usar “Editar datos” para conservar una nueva versión y volver a ejecutar.'));
    card.append(el('h3','Cuándo revisar la recomendación'));for(const condition of output.sensitivity.conditions)card.append(el('p',condition));card.append(el('p','Todavía no se midió su robustez ante escenarios futuros.','field-help'));
    card.append(details('Fuentes declaradas',m.alternatives.map(x=>({alternativa:x.label,fuente:x.source}))),details('Alcance y límites',output.limits),details('Resultado completo verificable',output));host.append(card);
  }
  function feedback(form) {
    const group=el('fieldset');group.append(el('legend','Sobre esta decisión (opcional)'));
    const values={represents_question:'not_answered',helped:'not_answered',acted:'not_answered'};
    const ask=(key,label,choices)=>select(group,label,[['not_answered','Prefiero no responder'],...choices],values[key],v=>{values[key]=v;});
    ask('represents_question','¿La comparación representó lo que querías decidir?',[['yes','Sí'],['partly','En parte'],['no','No']]);
    ask('helped','¿El resultado te ayudó a decidir?',[['yes','Sí'],['partly','En parte'],['no','No'],['not_yet','Todavía no lo sé']]);
    ask('acted','¿Ya tomaste una decisión?',[['not_yet','Todavía no'],['followed','Elegí la opción recomendada'],['different','Elegí otra opción'],['no_recommendation','No hubo una recomendación única']]);
    group.append(el('p','Podés contar en el comentario qué faltó o qué ocurrió, sin datos personales. Es tu percepción declarada; no se interpreta como eficacia demostrada.','field-help'));form.append(group);
    return ()=>({...values,kind:'self_report_not_validated'});
  }
  function init(request) {
    api=request;root=$('choice-fields');
    root.querySelectorAll('[data-choice-next]').forEach(b=>b.addEventListener('click',()=>step(Number(b.dataset.choiceNext))));
    for(const id of ['choice-question','choice-category','choice-horizon','choice-selection'])$(id).addEventListener('input',invalidate);
    $('choice-selection').addEventListener('change',()=>renderPriorities());
    $('choice-add-criterion').addEventListener('click',()=>{if(criteria.length>=5)return;criteria.push({id:'c'+(++sequence),label:'',unit:'',direction:'min',limit:null});invalidate();renderCriteria();renderPriorities();});
    $('choice-add-alternative').addEventListener('click',()=>{if(alternatives.length>=8)return;alternatives.push({id:'a'+(++sequence),label:'',source:'',values:{}});invalidate();renderAlternatives();});
    $('choice-review').addEventListener('click',async()=>{const error=$('choice-error');error.hidden=true;confirmation=null;$('choice-confirm').checked=false;$('choice-review').disabled=true;
      try{const snapshot=model(), {data}=await api('/api/choice/review',{method:'POST',body:snapshot});if(JSON.stringify(snapshot)!==JSON.stringify(model()))throw Error('Los datos cambiaron durante la revisión. Volvé a revisarlos.');
        confirmation=data.confirmation;const area=$('choice-review-result');area.replaceChildren(el('p',data.summary),el('p',data.selection_notice));table(snapshot,area);
        for(const q of data.questions)area.append(el('p',q.question,'callout warning'));area.append(el('p','Confirmá también tus límites y fuentes. Los datos vacíos seguirán siendo desconocidos.','field-help'),details('Modelo que vas a guardar',snapshot));$('choice-confirm-box').hidden=false;
      }catch(e){error.textContent=e.message;error.hidden=false;}finally{$('choice-review').disabled=false;}});
    reset();
  }
  return {init,reset,load,read,render,feedback};
})();
