"use strict";

// The form declares choices. The server generates and validates alternatives;
// the existing confirmation/evaluation flow computes their consequences.
const interventionDrafts = new Map();
let interventionFieldCount = 0;
function activeInterventionDraft() {
  const key = `${activeCase().id}:${activeCase().current_version}`;
  if (!interventionDrafts.has(key)) interventionDrafts.set(key, {
    format: "genius-intervention-design/1", name: "Diseño de intervenciones", relations: [], interventions: []
  });
  return interventionDrafts.get(key);
}
function interventionInput(label, value, set, help="") {
  const id=`intervention-field-${++interventionFieldCount}`;
  return element("div",{class:"builder-field"},element("label",{for:id,text:label}),
    element("input",{id,value,oninput:e=>set(e.target.value)}),help?p(help,"field-help"):null);
}
function interventionSelect(label, value, options, set) {
  return selectField(`intervention-select-${++interventionFieldCount}`,label,options,value,e=>{set(e.target.value);render();});
}
function interventionCheck(label, checked, set) {
  const id=`intervention-check-${++interventionFieldCount}`;
  return element("label",{class:"builder-choice",for:id},element("input",{id,type:"checkbox",checked,onchange:e=>set(e.target.checked)}),label);
}
function interventionRemove(array,index) { array.splice(index,1);render(); }
function interventionCosts(title, values, model) {
  return element("details",{class:"builder-event"},element("summary",{text:title}),
    p("Indica lo que se consume al ejecutar la operación. Cero declara que ese costo queda fuera de este modelo.","hint"),
    element("div",{class:"builder-fields"},model.stocks.map(s=>interventionInput(`${s.label} (${s.unit})`,qText(values[s.id]??"0/1"),v=>values[s.id]=v))));
}
function newInterventionOperation(kind, model, design, previous) {
  const common={operation:kind,at:previous?.at||[1]};
  if(kind==="use_action")return {...common,action:model.actions[0]?.id||""};
  return {...common,relation:design.relations[0]?.id||"",...(kind==="transfer"?{amounts:["1/1"]}:{})};
}
function splitInterventionValues(value) {
  return Array.isArray(value)?value:String(value).split(",").map(s=>s.trim()).filter(Boolean);
}
function normalizedInterventionDesign(design) {
  const normalized=copy(design);
  normalized.relations.forEach(r=>["open_costs","close_costs","transfer_costs"].forEach(key=>
    Object.keys(r[key]).forEach(stock=>r[key][stock]=exactQuantity(String(r[key][stock])))));
  normalized.interventions.forEach(i=>i.operations.forEach(op=>{
    op.at=splitInterventionValues(op.at).map(step=>{
      if(!/^\d+$/.test(String(step)))throw new Error("Los pasos deben ser enteros separados por comas.");
      return Number(step);
    });
    if(op.amounts)op.amounts=splitInterventionValues(op.amounts).map(v=>exactQuantity(String(v)));
  }));
  return normalized;
}
async function proposeInterventions() {
  const design=normalizedInterventionDesign(activeInterventionDraft());
  const response=await api(`/api/cases/${encodeURIComponent(activeCase().id)}/proposals`,{
    base_version:activeCase().current_version,kind:"intervention_design",text:design.name,structured:{design}
  });
  d3.proposal=response.proposal;d3.reviewChecks=false;ui.pendingKey=null;
  await refresh();go("twin");announce("Alternativas generadas. Revisa las secuencias y sus costos antes de confirmar.");
}
async function createInterventionExample() {
  const fixture=await api("/api/interventions/example");
  const response=await api("/api/cases",{text:"Explorar un ejemplo sintético de redistribución entre depósitos.",title:"Intervenciones entre depósitos",profile:D3_PROFILE});
  ui.initial=response;ui.dossier=null;ui.evaluation=null;ui.proposal=null;d3.cid=null;
  await refresh();initializeGeneral();saveCase();
  d3.model=copy(fixture.model);d3.text="Ejemplo sintético: confirmar sus premisas antes de diseñar intervenciones.";
  await proposeGeneral();
  // Seed only the future form; accepting the base remains the user's action.
  interventionDrafts.set(`${activeCase().id}:1`,copy(fixture.design));
}
function renderInterventionRelation(r,index,design,model) {
  const resourceOptions=model.stocks.map(s=>[s.id,`${s.label} (${s.unit})`]);
  return rowPanel(r.label||`Relación ${index+1}`,[
    interventionInput("Nombre de la relación",r.label,v=>r.label=v),
    interventionSelect("Origen",r.source,resourceOptions,v=>r.source=v),
    interventionSelect("Destino",r.target,resourceOptions,v=>r.target=v),
    interventionCheck("La relación ya está abierta al inicio",r.initially_open,v=>r.initially_open=v),
    element("fieldset",{class:"builder-multi"},element("legend",{text:"Capacidades necesarias para operar esta relación"}),
      model.capabilities.map(c=>interventionCheck(c.label,r.requires.includes(c.id),v=>r.requires=v?[...r.requires,c.id]:r.requires.filter(id=>id!==c.id)))),
    interventionInput("Fundamento de esta relación y sus costos",r.provenance,v=>r.provenance=v,"Explica si procede de un supuesto, una medición o una fuente identificada."),
    interventionCosts("Costos de abrir",r.open_costs,model),interventionCosts("Costos de cerrar",r.close_costs,model),
    interventionCosts("Costos adicionales por transferencia",r.transfer_costs,model)
  ],()=>interventionRemove(design.relations,index));
}
function renderInterventionSequence(intervention,index,design,model) {
  const operations=intervention.operations;
  return rowPanel(intervention.label||`Intervención ${index+1}`,[
    interventionInput("Nombre de la intervención",intervention.label,v=>intervention.label=v),
    interventionSelect("En los pasos sin intervención",intervention.default_action??"",[["","Esperar sin acción"],...model.actions.map(a=>[a.id,a.label])],v=>intervention.default_action=v||null),
    element("div",{class:"builder-wide"},operations.map((op,i)=>rowPanel(`Operación ${i+1}`,[
      interventionSelect("Qué cambiar",op.operation,[["connect","Abrir relación"],["disconnect","Cerrar relación"],["transfer","Transferir recurso"],["use_action","Usar una tarea existente"]],v=>operations[i]=newInterventionOperation(v,model,design,op)),
      interventionInput("Paso o pasos alternativos",Array.isArray(op.at)?op.at.join(", "):op.at,v=>op.at=v,"Ejemplo: 2, 3 genera una alternativa para cada momento. Una operación por paso."),
      op.operation==="use_action"?interventionSelect("Tarea",op.action,model.actions.map(a=>[a.id,a.label]),v=>op.action=v):
        interventionSelect("Relación",op.relation,[["","Seleccionar"],...design.relations.map(r=>[r.id,r.label||r.id])],v=>op.relation=v),
      op.operation==="transfer"?interventionInput("Cantidades alternativas",Array.isArray(op.amounts)?op.amounts.map(qText).join(", "):op.amounts,v=>op.amounts=v,"En la unidad común de los depósitos. Ejemplo: 1, 2; usa punto decimal o fracciones."):null
    ],()=>interventionRemove(operations,i))),button("Agregar operación",()=>{operations.push(newInterventionOperation("transfer",model,design));render();},"secondary small"))
  ],()=>interventionRemove(design.interventions,index));
}
function renderInterventionReceipt(receipt,model=currentVersion()?.model) {
  if(!receipt)return null;
  const labels={connect:"Abrir",disconnect:"Cerrar",transfer:"Transferir",use_action:"Usar tarea"};
  const names=Object.fromEntries(receipt.design.relations.map(r=>[r.id,r.label]));
  const stockName=id=>model?.stocks.find(s=>s.id===id)?.label||id;
  const unit=id=>model?.stocks.find(s=>s.id===id)?.unit||"";
  const costs=values=>Object.entries(values).filter(([,v])=>v!=="0/1").map(([id,v])=>`${qText(v)} ${unit(id)} de ${stockName(id)}`).join("; ")||"Sin costo declarado";
  const variantCounts={};
  return panel("Alternativas generadas",[
    p(`${receipt.generated_count} variantes, además de ${receipt.baseline_policies.length} planes de referencia. Todas se evaluarán con las mismas condiciones iniciales y escenarios.`,"note"),
    table("Relaciones declaradas",["Relación","Origen y destino","Estado inicial","Costos"],receipt.design.relations.map(r=>[r.label,`${stockName(r.source)} → ${stockName(r.target)} (${unit(r.source)})`,r.initially_open?"Abierta":"Cerrada",`Abrir: ${costs(r.open_costs)}. Cerrar: ${costs(r.close_costs)}. Por transferencia: ${costs(r.transfer_costs)}.`])),
    list(receipt.design.relations.map(r=>`${r.label}: ${r.provenance}. Requiere: ${r.requires.map(id=>model?.capabilities.find(c=>c.id===id)?.label||id).join(", ")||"sin capacidades adicionales declaradas"}.`)),
    table("Secuencias propuestas",["Alternativa","Operaciones"],Object.values(receipt.generated_policies).map(value=>{
      const definition=receipt.design.interventions.find(i=>i.id===value.intervention_id);
      const index=variantCounts[value.intervention_id]=(variantCounts[value.intervention_id]||0)+1;
      return [`${definition.label} · variante ${index}`,value.operations.map(op=>{
        const relation=receipt.design.relations.find(r=>r.id===op.relation);
        const action=model?.actions.find(a=>a.id===op.action)?.label||op.action;
        return `Paso ${op.at}: ${labels[op.operation]} ${names[op.relation]||action}${op.amount?` · ${qText(op.amount)} ${unit(relation.source)}`:""}`;
      }).join("; ")];
    })),
    p("Se incluyen todas las combinaciones declaradas. Esto no demuestra que se hayan explorado todas las intervenciones posibles en la realidad.","hint")
  ],"spacing-top");
}
function renderInterventions() {
  interventionFieldCount=0;
  const model=currentVersion()?.model;
  const head=heading("Diseña intervenciones","Explora cómo cambian los recorridos al redistribuir recursos o modificar relaciones de intercambio.");
  if(!model||model.profile!==D3_PROFILE)return element("div",{},head,p("Primero construye y confirma un modelo de recursos. También puedes abrir un ejemplo sintético en un expediente nuevo.","note"),
    actions(button("Construir modelo",()=>go("review"),"primary"),button("Abrir ejemplo de depósitos",()=>run(createInterventionExample),"secondary")));
  const design=activeInterventionDraft();
  return element("div",{},head,
    panel("Punto de partida",[p(`Versión confirmada ${activeCase().current_version}: ${model.name}. Se conservan sus recursos iniciales, escenarios y criterios.`,"note"),
      d3.dirty?p("Hay cambios en el constructor que aún no están confirmados. Este diseño usa la versión confirmada.","callout amber"):null,
      interventionInput("Qué quieres explorar",design.name,v=>design.name=v),
      p("Las relaciones de esta versión conectan depósitos de la misma unidad. Sus costos y requisitos son premisas que deberás revisar.","hint")]),
    panel("Relaciones entre recursos",[design.relations.map((r,i)=>renderInterventionRelation(r,i,design,model)),
      button("Agregar relación",()=>{design.relations.push({id:idFor("link",design.relations),label:"Nueva relación",source:model.stocks[0].id,target:model.stocks[1]?.id||"",initially_open:false,requires:[],open_costs:{},close_costs:{},transfer_costs:{},provenance:""});render();},"secondary small")]),
    panel("Intervenciones que quieres explorar",[design.interventions.map((x,i)=>renderInterventionSequence(x,i,design,model)),
      button("Agregar intervención",()=>{design.interventions.push({id:idFor("plan",design.interventions),label:"Nueva intervención",default_action:null,operations:[newInterventionOperation("connect",model,design)]});render();},"secondary small")]),
    p("Generar guarda una propuesta en el expediente. Luego podrás revisarla, confirmarla y calcular sus consecuencias. Los cambios aún no generados se conservan solo mientras esta página permanece abierta.","hint"),
    actions(button("Generar alternativas",()=>run(proposeInterventions),"primary",{id:"intervention-generate"}),button("Abrir ejemplo en otro expediente",()=>run(createInterventionExample),"ghost")),
    renderInterventionReceipt(currentVersion()?.metadata?.intervention_design));
}
