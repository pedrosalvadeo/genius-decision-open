// DOM behavior verification; this does not claim browser/layout coverage.
// Run: NODE_PATH=<directory containing linkedom> node beta/tests/browser/observatory.cjs
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const {parseHTML} = require('linkedom');
const staticPath = path.resolve(__dirname,'../../genius_beta/static');
const {document,window} = parseHTML(fs.readFileSync(path.join(staticPath,'organisms.html'),'utf8'));
Object.defineProperty(document,'hidden',{value:false,writable:true});
const select = document.getElementById('status-filter');
Object.defineProperty(select,'value',{value:'all',writable:true});
const now = Date.now(), iso = new Date(now).toISOString();
const rows = ['SAME','SAMM'].map(station=>({station,label:station,status:'PAUSED_OR_REVIEW_REQUIRED',reason:'ENROLLMENT_REVIEW_REQUIRED',checked_at:iso,node_id:null,organism:null}));
let response = {format:'genius-living-observatory/1',checked_at:now/1000,organisms:rows};
let fail = false, serial = 0, calls = [], timers = new Map();
const context = {
  document,location:{hash:''},Date,AbortController,
  setTimeout(fn,ms){const id=++serial;timers.set(id,{fn,ms});return id;},clearTimeout(id){timers.delete(id);},
  async fetch(url,options){calls.push({url,options});if(fail)throw Error('offline');return {ok:true,json:async()=>structuredClone(response)};}
};
const get=id=>document.getElementById(id);
const settle=async()=>{for(let i=0;i<12;i++)await Promise.resolve();};
const update=async()=>{get('refresh').dispatchEvent(new window.Event('click'));await settle();};
vm.runInNewContext(fs.readFileSync(path.join(staticPath,'organisms.js'),'utf8'),context);
(async()=>{
  await settle();
  assert.equal(document.querySelectorAll('.organism-card').length,2);
  assert.match(get('seed-SAME').textContent,/registro.*revisión/);
  assert.equal(document.querySelectorAll('.metric strong')[2].textContent,'—','Missing performance is not zero');
  assert.equal(document.querySelectorAll('svg').length,0,'No invented trend');
  assert.equal(calls[0].url,'/network/organisms.json');
  assert.equal(calls[0].options.credentials,'omit');
  select.value='cycle';select.dispatchEvent(new window.Event('change'));
  assert.equal(get('seed-SAME').hidden,true);assert.equal(get('empty-filter').hidden,false);
  select.value='all';select.dispatchEvent(new window.Event('change'));
  const score={observed_at:iso,actual_centikelvin:29315,predicted_centikelvin:29215,absolute_error_centikelvin:100};
  const active={...rows[0],label:'<img src=x onerror=alert(1)>',reason:undefined,status:'WAITING_FOR_OUTCOME',node_id:'node-1',latest_observation:{observed_at:iso,centikelvin:29315},last_prediction:{frozen_at:iso,predicted_centikelvin:29415},last_scored:score,recent_results:[score],organism:{scored_outcomes:13,locally_confirmed_changes:0,archived_trials:1,founder_generation:0,founder_genes:{estimator:'lower_median',window:5},context_traits:[],trials:{t:'CONFIRMATION'},trial_progress:[{id:'t',status:'CONFIRMATION',phase_size:4,discovery_scored:4,confirmation_scored:1,pending_outcome:true}]}};
  response.organisms=[active,rows[1]];await update();
  assert.equal(get('seed-SAME').querySelectorAll('img').length,0,'Text cannot inject markup');
  assert.match(get('seed-SAME').textContent,/<img/);
  assert.equal(get('seed-SAME').querySelectorAll('svg').length,1);
  assert.equal(get('seed-SAME').querySelectorAll('tbody tr').length,1);
  assert.match(get('seed-SAME').textContent,/Confirmar · 1 \/ 4/,'Phase progress is not inferred from lifetime count');
  assert.match(get('seed-SAME').textContent,/1 °C/);
  assert.match(document.querySelectorAll('.metric small')[2].textContent,/1 de 2/,'Partial totals are labelled');
  get('details-SAME').setAttribute('open','');
  response.organisms[0]={...active,organism:{...active.organism,scored_outcomes:14}};await update();
  assert.equal(get('details-SAME').open,true,'Auto refresh preserves expanded details');
  fail=true;await update();
  assert.equal(document.querySelectorAll('.organism-card').length,2);
  assert.match(get('connection-note').textContent,/último informe/);
  assert.equal(get('refresh').disabled,false);
  fail=false;response.organisms[0]={...active,checked_at:new Date(now-4*3600000).toISOString()};await update();
  assert.equal(get('seed-SAME').dataset.group,'attention');
  assert.match(get('seed-SAME').textContent,/Informe desactualizado/);
  response.organisms=[];await update();assert.match(get('organisms').textContent,/Todavía no hay organismos/);
  response.organisms=[{...active,recent_results:undefined}];await update();
  assert.equal(get('seed-SAME').querySelectorAll('tbody tr').length,1,'Older reports fall back to their recorded result');
  const poll=Array.from(timers.values()).find(t=>t.ms===60000);assert.ok(poll,'Schedules a minute between refreshes');
  document.hidden=true;document.dispatchEvent(new window.Event('visibilitychange'));
  assert.equal(Array.from(timers.values()).filter(t=>t.ms===60000).length,0);
  response={unexpected:true};await update();assert.match(get('connection-note').textContent,/último informe/);
  console.log('PASS: paused, missing, filters, real pairs, progress, partial totals, safe text, refresh, history fallback, stale, offline, empty, hidden and malformed states. DOM only; visual browser QA not performed.');
})().catch(error=>{console.error(error);process.exitCode=1;});
