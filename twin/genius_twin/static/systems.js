"use strict";

// Source assertions and proposed groupings remain distinct from native dynamics.
const systemDrafts=new Map();
const systemKinds=[["resource","Recurso"],["physical","Elemento físico"],["living","Ser vivo"],["person","Persona"],["organization","Organización"]];
const systemRelationKinds=[["organizes","Se organiza junto con"],["supplies","Suministra a"],["depends_on","Depende de"],["affects","Puede afectar a"]];
const systemBasis=[["reported","Declaración de una fuente"],["measurement","Medición declarada"],["inference","Interpretación / inferencia"],["synthetic","Ejemplo sintético"]];
let systemField=0;
function systemDraft(){
  const cid=activeCase().id;
  if(!systemDrafts.has(cid)){
    const latest=ui.dossier?.system_context?.latest,stamp=new Date().toISOString();
    systemDrafts.set(cid,{revision:latest?.revision||0,dirty:false,scope:null,pending:null,
      observation:copy(latest?.observation||{format:"genius-system-observation/1",label:"",window:{start:stamp,end:stamp},entities:[],relations:[],evidence:[],unknowns:[]})});
  }
  return systemDrafts.get(cid);
}
function systemInput(label,value,set,{area=false,observation=true}={}){
  const id=`system-field-${++systemField}`;
  return element("div",{class:"builder-field"},element("label",{for:id,text:label}),element(area?"textarea":"input",{id,value,rows:area?3:undefined,maxlength:2000,oninput:e=>{set(e.target.value);if(observation)systemDraft().dirty=true;}}));
}
function systemPick(label,value,opts,set,observation=true){return selectField(`system-field-${++systemField}`,label,opts,value,e=>{set(e.target.value);if(observation)systemDraft().dirty=true;render();});}
function systemMulti(label,rows,selected,set,observation=true){
  return element("fieldset",{class:"builder-multi"},element("legend",{text:label}),rows.map(row=>{
    const id=`system-field-${++systemField}`;return element("label",{class:"builder-choice",for:id},element("input",{id,type:"checkbox",checked:selected.includes(row.id),onchange:e=>{set(e.target.checked?[...selected,row.id]:selected.filter(x=>x!==row.id));if(observation)systemDraft().dirty=true;}}),row.label||row.id);
  }));
}
function systemRow(title,children,rows,index){return panel(title,[element("div",{class:"builder-fields"},children),button("Quitar de esta vista",()=>{rows.splice(index,1);systemDraft().dirty=true;render();},"ghost small")],"spacing-top");}
function systemNames(ids,snapshot){const names=Object.fromEntries(snapshot.entities.map(e=>[e.id,e.label]));return ids.map(id=>names[id]||id).join(" · ")||"Ninguno declarado";}
function renderSystemScopeReceipt(receipt){
  if(!receipt)return null;
  const snapshot=ui.dossier?.system_observations?.find(r=>r.revision===receipt.observation_revision)?.observation;
  const name=ids=>snapshot?systemNames(ids,snapshot):ids.join(" · ");
  return panel("Límites de esta hipótesis",[factList([["Sistema",name(receipt.scope.members)],["Intervención declarada",name(receipt.scope.intervention_entities)],["Evaluación",name(receipt.scope.evaluation_entities)],["Observación",String(receipt.observation_revision)]]),
    receipt.unmapped_entities.length?p(`Falta representar en el cálculo: ${name(receipt.unmapped_entities)}. La recomendación queda suspendida.`,"callout amber"):p("Correspondencias declaradas completas. Aún no acreditan la dinámica ni las probabilidades del mundo real.","note"),
    Object.values(receipt.historical_gaps||{}).some(rows=>rows.length)?p("Hay entidades o relaciones de vistas anteriores que ahora faltan o se contradicen. Su ausencia no prueba que hayan dejado de existir; la recomendación queda suspendida.","callout amber"):null,
    receipt.carriers_without_welfare?.length?p(`Faltan condiciones de bienestar para: ${name(receipt.carriers_without_welfare)}.`,"callout amber"):null,
    p("Las relaciones y fuentes se conservan como contexto; los cálculos siguen usando las reglas del modelo confirmado.","hint"),disclosure("Correspondencias y comprobaciones",receipt)],"spacing-top");
}
function renderSystemContextNotice(){
  const context=ui.dossier?.system_context;
  if(!context?.observation_revision)return null;
  return panel("Sistemas y evidencia",[p(context.status==="REVIEW_REQUIRED"?"Hay observaciones o cambios del modelo que requieren revisar los límites. Los resultados anteriores permanecen históricos.":context.status==="SCOPE_INCOMPLETE"?"Hay afectados o dependencias que todavía no están representados en el cálculo. Revisa los límites antes de usar una recomendación.":"El cálculo tiene límites declarados vinculados a la última observación. La validez empírica sigue pendiente.",context.status==="CURRENT_DECLARED_SCOPE"?"note":"callout amber"),button("Revisar sistemas y límites",()=>go("systems"),"secondary small")],"spacing-top");
}
async function saveSystemObservation(){
  const draft=systemDraft(),payload={base_version:activeCase().current_version,observation_revision:draft.revision,observation:draft.observation};
  const signature=JSON.stringify(payload);
  if(draft.pending?.signature!==signature)draft.pending={signature,key:crypto.randomUUID()};
  await api(`/api/cases/${activeCase().id}/systems`,{...payload,idempotency_key:draft.pending.key});
  draft.pending=null;draft.dirty=false;draft.scope=null;await refresh();draft.revision=ui.dossier.system_context.observation_revision;render();
  announce("Observación conservada. Las agrupaciones son hipótesis; revisa sus límites y dependencias.");
}
async function loadSystemExample(){
  const fixture=await api("/api/systems/example"),response=await api("/api/cases",{text:"Exploración sintética de sistemas y efectos externos",title:"Sistemas y entorno — ejemplo sintético",profile:D3_PROFILE});
  ui.initial=response;ui.dossier=null;ui.evaluation=null;ui.proposal=null;d3.cid=null;await refresh();initializeGeneral();saveCase();
  d3.model=copy(fixture.model);d3.text="Modelo sintético de depósitos: no son mediciones de campo.";await saveGeneralDraft();
  const draft=systemDraft();draft.observation=copy(fixture.observation);draft.dirty=true;go("systems");
  announce("Ejemplo abierto en otro expediente. Revisa la fuente sintética antes de registrar.");
}
function chooseSystemCandidate(candidate){
  const context=ui.dossier.system_context,snapshot=context.latest.observation,model=currentVersion()?.model;
  if(!model){go("review");announce("Primero confirma el modelo para vincularlo con estas entidades. La observación ya está conservada.");return;}
  const bindings=["stocks","carriers"].flatMap(collection=>model[collection].map(row=>({collection,model_id:row.id,entity_id:snapshot.entities.some(e=>e.id===row.id)?row.id:""})));
  systemDraft().scope={format:"genius-system-scope/1",observation_revision:context.observation_revision,label:"Hipótesis de sistema",
    members:[...candidate.members],intervention_entities:[],evaluation_entities:[...new Set([...candidate.required_evaluation_entities,...bindings.map(b=>b.entity_id).filter(Boolean)])],bindings,rationale:""};render();
}
async function proposeSystemScope(){
  const draft=systemDraft();if(draft.dirty)throw new Error("Registra primero los cambios de la observación o recupera la vista guardada. Los límites deben referirse a la evidencia conservada.");
  const response=await api(`/api/cases/${activeCase().id}/proposals`,{base_version:activeCase().current_version,kind:"system_scope",text:draft.scope.rationale,structured:{scope:draft.scope}});
  d3.proposal=response.proposal;d3.reviewChecks=false;await refresh();go("twin");
}
function renderSystemScopeForm(snapshot){
  const draft=systemDraft(),scope=draft.scope,model=currentVersion()?.model;if(!scope||!model)return null;
  // Scope edits do not edit the observation; they remain a separate proposal.
  const multi=(label,selected,set)=>systemMulti(label,snapshot.entities,selected,set,false);
  return panel("Revisa el sistema y sus límites",[
    systemInput("Nombre de la hipótesis",scope.label,v=>scope.label=v,{observation:false}),
    multi("Miembros del sistema",scope.members,v=>scope.members=v),
    multi("Entidades sobre las que se propone intervenir",scope.intervention_entities,v=>scope.intervention_entities=v),
    multi("Entidades incluidas al evaluar consecuencias",scope.evaluation_entities,v=>scope.evaluation_entities=v),
    p("Incluye las dependencias y los afectados que muestra la observación. Una entidad puede participar en varias hipótesis conservando su identidad.","hint"),
    scope.bindings.map(b=>systemPick(`Representa ${model[b.collection].find(r=>r.id===b.model_id)?.label||b.model_id}`,b.entity_id,[["","Elige una entidad"],...snapshot.entities.map(e=>[e.id,e.label])],v=>b.entity_id=v,false)),
    systemInput("Fundamento de estos límites",scope.rationale,v=>scope.rationale=v,{area:true,observation:false}),
    actions(button("Proponer límites",()=>run(proposeSystemScope),"primary",{id:"system-propose-scope"})),
    p("Proponer guarda una revisión. Deberás confirmar sus condiciones antes de calcular.","hint")],"spacing-top");
}
function renderSystems(){
  systemField=0;
  const draft=systemDraft(),snapshot=draft.observation,context=ui.dossier?.system_context,latest=context?.latest;
  const refs=snapshot.evidence.map(e=>({id:e.id,label:`${e.id}: ${e.source||"Fuente pendiente"}`}));
  const evidenceRefs=row=>systemMulti("Fuentes que sustentan este registro",refs,row.evidence_ids,v=>row.evidence_ids=v);
  const sourceOptions=[["","Elige una entidad"],...snapshot.entities.map(e=>[e.id,e.label||e.id])];
  const add=(name,fn)=>button(name,()=>{fn();draft.dirty=true;render();},"secondary small");
  return element("div",{},heading("Reconocer sistemas y revisar sus límites","Registra entidades y relaciones con su origen. Genius propone agrupaciones y rastrea dependencias e impactos dentro de esa información."),
    renderSystemContextNotice(),
    panel("Vista de observación",[systemInput("Nombre de la observación",snapshot.label,v=>snapshot.label=v),
      systemInput("Inicio de la ventana (ISO8601 con zona)",snapshot.window.start,v=>snapshot.window.start=v),systemInput("Fin de la ventana (ISO8601 con zona)",snapshot.window.end,v=>snapshot.window.end=v),
      p("Esta ventana indica cuándo se observó. No determina el horizonte futuro del cálculo. Omitir un elemento de una nueva vista no demuestra su desaparición.","hint")]),
    panel("Fuentes y evidencia",[snapshot.evidence.map((e,i)=>systemRow(`Fuente ${e.id}`,[systemInput("Origen de la fuente",e.source,v=>e.source=v),systemPick("Tipo de evidencia",e.basis,systemBasis,v=>e.basis=v),systemInput("Fecha de la evidencia (ISO8601 con zona)",e.observed_at,v=>e.observed_at=v),systemInput("Qué informa la fuente",e.statement,v=>e.statement=v,{area:true}),systemInput("Incertidumbre y limitaciones",e.uncertainty,v=>e.uncertainty=v,{area:true})],snapshot.evidence,i)),
      add("Agregar fuente",()=>snapshot.evidence.push({id:idFor("evidence",snapshot.evidence),observed_at:snapshot.window.start,source:"",basis:"reported",statement:"",uncertainty:""}))],"spacing-top"),
    panel("Entidades",[snapshot.entities.map((e,i)=>systemRow(`Entidad ${e.id}`,[systemInput("Nombre de la entidad",e.label,v=>e.label=v),systemPick("Tipo de entidad",e.kind,systemKinds,v=>e.kind=v),evidenceRefs(e)],snapshot.entities,i)),
      add("Agregar entidad",()=>snapshot.entities.push({id:idFor("entity",[...snapshot.entities,...(ui.dossier?.system_observations||[]).flatMap(r=>r.observation.entities)]),label:"",kind:"resource",evidence_ids:refs.length?[refs[0].id]:[]}))],"spacing-top"),
    panel("Relaciones",[snapshot.relations.map((r,i)=>systemRow(`Relación ${r.id}`,[systemPick("Desde",r.source,sourceOptions,v=>r.source=v),systemPick("Relación",r.kind,systemRelationKinds,v=>r.kind=v),systemPick("Hacia",r.target,sourceOptions,v=>r.target=v),evidenceRefs(r)],snapshot.relations,i)),
      add("Agregar relación",()=>snapshot.relations.push({id:idFor("relation",snapshot.relations),source:snapshot.entities[0]?.id||"",target:snapshot.entities[1]?.id||"",kind:"affects",evidence_ids:refs.length?[refs[0].id]:[]}))],"spacing-top"),
    panel("Qué falta conocer",[systemInput("Información pendiente (una cuestión por línea)",snapshot.unknowns.join("\n"),v=>snapshot.unknowns=v.split("\n").filter(x=>x.trim()),{area:true}),
      p("Los cambios del formulario duran mientras esta página permanezca abierta. Registrar guarda una vista nueva, sus fuentes y las hipótesis generadas; no modifica el cálculo.","hint"),
      actions(button("Registrar y reconocer",()=>run(saveSystemObservation),"primary",{id:"system-record"}),button("Recuperar vista guardada",()=>{systemDrafts.delete(activeCase().id);render();},"secondary"),button("Abrir ejemplo sintético",()=>run(loadSystemExample),"ghost"))],"spacing-top"),
    latest?panel(`Hipótesis a partir de la observación ${latest.revision}`,[p("Son interpretaciones del grafo declarado, sin probabilidades de certeza ni prueba de que sean los únicos sistemas posibles. Las relaciones de organización forman un primer grupo; las demás conexiones sugieren un entorno más amplio.","note"),
      Object.values(latest.historical_gaps||{}).some(rows=>rows.length)?p("Esta vista omite o contradice elementos anteriores. La historia se conserva y estas diferencias requieren revisión.","callout amber"):null,
      latest.recognition.candidates.map((c,i)=>panel(`Hipótesis ${i+1}`,[factList([["Miembros",systemNames(c.members,latest.observation)],["Dependencias externas",systemNames(c.dependencies,latest.observation)],["Posibles afectados externos",systemNames(c.potential_impacts,latest.observation)]]),button("Revisar este límite",()=>chooseSystemCandidate(c),"secondary small",{"data-candidate":c.id})],"spacing-top")),
      disclosure("Datos y método de reconocimiento",latest.recognition)],"spacing-top"):null,
    latest?renderSystemScopeForm(latest.observation):null,
    renderSystemScopeReceipt(currentVersion()?.metadata?.system_scope),
    panel("Historia de observaciones",[(ui.dossier?.system_observations||[]).map(r=>disclosure(`Vista ${r.revision}: ${r.observation.label}`,r)),p("Los registros y límites aceptados se incluyen en la descarga del expediente, junto con los cálculos congelados.","hint")],"spacing-top"));
}
