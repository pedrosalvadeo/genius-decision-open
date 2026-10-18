/* D3 human-path gate. Runs only against its own loopback fixture database.
 * PLAYWRIGHT_MODULE, CHROMIUM_PATH, PYTHONPATH: same contract as browser_smoke.
 * No real participants, field observations or public deployment.
 */
const fs=require('fs'),path=require('path'),os=require('os'),assert=require('assert/strict');
const {spawn}=require('child_process');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const out=process.env.BROWSER_QA_DIR||fs.mkdtempSync(path.join(os.tmpdir(),'genius-d3-browser-'));
const port=process.env.D3_BROWSER_PORT||'8766',base=`http://127.0.0.1:${port}`;
fs.mkdirSync(out,{recursive:true});
const evidence={scope:'SYNTHETIC_UI_INTEGRATION_NOT_HUMAN_COMPREHENSION_OR_FIELD_VALIDATION',checks:[],page_errors:[],external_requests:[],screens:[]};
const check=(value,label)=>{assert.ok(value,label);evidence.checks.push(label);};
let browser,debugPage;const server=spawn(process.env.PYTHON||'python',['-m','genius_twin','--port',port,'--database',path.join(out,'browser.sqlite3')],{env:process.env});
let logs='';server.stderr.on('data',x=>logs+=x.toString());
(async()=>{
 await new Promise((resolve,reject)=>{const timer=setTimeout(()=>reject(new Error('server start timeout: '+logs)),12000);server.stderr.on('data',x=>{if(x.toString().includes('Running on')){clearTimeout(timer);resolve();}});server.once('exit',c=>reject(new Error('server exited '+c+': '+logs)));});
 browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_PATH,args:['--no-sandbox']});
 const context=await browser.newContext({viewport:{width:1440,height:1000},acceptDownloads:true});const page=await context.newPage();debugPage=page;page.setDefaultTimeout(30000);
 page.on('pageerror',e=>evidence.page_errors.push(e.message));page.on('request',r=>{if(!r.url().startsWith(base)&&!r.url().startsWith('blob:'))evidence.external_requests.push(r.url());});
 const idle=()=>page.waitForFunction(()=>!document.querySelector('#main').hasAttribute('aria-busy'));
 const get=async route=>(await page.request.get(base+route)).json();
 const body=()=>page.locator('body').innerText();
 const nav=async view=>{await page.locator(`#step-nav [data-view="${view}"]`).click();await idle();};
 const section=async id=>{await page.locator(`[data-section="${id}"]`).click();await idle();};
 const shot=async name=>{await idle();await page.screenshot({path:path.join(out,name+'.png'),fullPage:true});check(!(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth)),name+' has no page overflow');evidence.screens.push(name+'.png');};
 const create=async text=>{await page.locator('#intake-mode').selectOption('general');await page.locator('#narrative').fill(text);await page.getByRole('button',{name:/Construir propuesta/}).click();await idle();await page.getByRole('heading',{name:'Construye tu decisión',exact:true}).waitFor();};
 const accept=async()=>{await page.locator('#d3-propose').click();await idle();check(!await page.locator('#error').isVisible(),'proposal accepted by the model validator');await page.locator('#d3-confirm').check();await page.getByRole('button',{name:'Confirmar y explorar',exact:true}).click();await idle();check(!await page.locator('#error').isVisible(),'native evaluation completed without service error');};
 await page.goto(base);await idle();
 await page.locator('#federations [data-actor="mead.glen_canyon"]').waitFor();check((await page.locator('#federations [data-actor="mead.glen_canyon"]').innerText()).includes('Mantener la prohibición todo el año'),'twin of twins shows the best joint route for each actor');
 await shot('desktop-entry');await page.setViewportSize({width:320,height:900});await shot('320-entry');await page.setViewportSize({width:1440,height:1000});
 await create('Quiero comparar cómo organizar un cuidado con un recurso compartido. Prueba sintética de interfaz D3.');
 const cid=await page.evaluate(()=>localStorage.getItem('genius_d1_case'));
 check((await get(`/api/cases/${cid}`)).case.current_version===0,'free narrative creates a persistent draft without inventing a model');
 await page.locator('[data-example="stockflow_care"]').click();await idle();await page.locator('#d3-name').fill('Modelo de cuidado configurado por formulario');await page.locator('#d3-save').click();await idle();
 await page.reload();await idle();check(await page.locator('#d3-name').inputValue()==='Modelo de cuidado configurado por formulario','draft model survives page reload');
 const draftBeforeConflict=await get(`/api/cases/${cid}`);const concurrentModel=JSON.parse(JSON.stringify(draftBeforeConflict.draft.model));concurrentModel.name='Borrador sintético concurrente';
 const concurrent=await page.request.patch(base+`/api/cases/${cid}/draft`,{data:{base_version:0,draft_revision:draftBeforeConflict.draft.revision,text:draftBeforeConflict.draft.text,model:concurrentModel}});check(concurrent.ok(),'concurrent fixture creates a newer draft');
 await page.locator('#d3-name').fill('Modelo de cuidado configurado por formulario');await page.locator('#d3-save').click();await idle();check((await page.locator('#error').innerText()).includes('borrador más reciente'),'stale draft reports a conflict');
 await page.getByRole('button',{name:'Recargar versión vigente',exact:true}).click();await idle();check(await page.locator('#d3-name').inputValue()==='Modelo de cuidado configurado por formulario','conflict reload preserves local form changes');check((await body()).includes('Borrador sintético concurrente'),'conflict reload exposes the saved draft for review');
 await page.locator('#d3-save').click();await idle();check(!await page.locator('#error').isVisible(),'explicit save can proceed after conflict review');
 for(const width of [1440,390,320]){
  await page.setViewportSize({width,height:1000});
  for(const key of ['scope','resources','actions','plans','scenarios','goals']){await section(key);await shot(`${width}-builder-${key}`);}
 }
 await page.setViewportSize({width:1440,height:1000});await section('scope');await accept();
 const accepted=await get(`/api/cases/${cid}`);const result1=accepted.jobs.find(j=>j.version===1&&j.canonical_results).canonical_results;
 check(result1.profile==='STOCK_FLOW_FINITE_V1','configured model uses new admitted profile');check(result1.horizon===3,'horizon is configurable, not semillero14');
 check((await page.locator('.policy-card .metric').allTextContents()).includes('2/3'),'exact native conditional task probability is rendered');
 check(await page.locator('#d3-policy option').count()===2,'dynamic policy selector matches declared family');
 for(const width of [1440,390,320]){await page.setViewportSize({width,height:1000});for(const view of ['twin','futures','conclusion','change']){await nav(view);await shot(`${width}-${view}`);}}
 await page.setViewportSize({width:1440,height:1000});await nav('review');await section('scope');await page.locator('#d3-horizon').fill('2');await page.locator('#d3-name').click();await section('resources');await page.locator('#d3-stock-initial-0').fill('7');await page.getByRole('heading',{name:'Recursos compartidos',exact:true}).click();await accept();
 const edited=await get(`/api/cases/${cid}`);const result2=edited.jobs.find(j=>j.version===2&&j.canonical_results).canonical_results;
 check(edited.versions.length===2&&edited.case.current_version===2,'material form edit creates a second version');check(edited.versions[1].model.stocks[0].initial==='7/1','decimal/integer form quantity converts to exact canonical rational');check(result2.horizon===2&&result2.policies.manual_policy.trajectories.ordinary.daily.length===3,'edited horizon is actually recomputed by engine');
 await nav('change');await page.getByRole('button',{name:'Comparar',exact:true}).click();await idle();check((await body()).includes('Antes y después'),'frozen versions compared in human view');await shot('desktop-comparison');
 const downloadPromise=page.waitForEvent('download');await page.getByRole('button',{name:'Descargar expediente JSON',exact:true}).click();const download=await downloadPromise;await idle();const exportFile=path.join(out,'configured-dossier.json');await download.saveAs(exportFile);const exported=JSON.parse(fs.readFileSync(exportFile));
 check(JSON.stringify(exported.dossier.jobs.find(j=>j.version===2&&j.canonical_results).canonical_results)===JSON.stringify(result2),'human export equals API canonical result');
 check(exported.dossier.evaluations.find(x=>x.job.version===1).evaluation.native_result.input_digest!==exported.dossier.evaluations.find(x=>x.job.version===2).evaluation.native_result.input_digest,'edited quantities/horizon create new native input digest');
 await page.getByRole('button',{name:'Restaurar',exact:true}).click();await idle();await page.locator('#d3-confirm').check();await page.getByRole('button',{name:'Confirmar y explorar',exact:true}).click();await idle();check((await get(`/api/cases/${cid}`)).case.current_version===3,'restore appends a version and runs a new evaluation');
 await page.locator('#case-library').click();await idle();check((await body()).includes('Tus decisiones'),'saved decisions are discoverable through list');await page.getByRole('button',{name:'Abrir decisión',exact:true}).first().click();await idle();check(await page.locator('#d3-name').inputValue()==='Modelo de cuidado configurado por formulario','list reopens the preserved configuration');
 await page.getByRole('button',{name:'Nueva exploración',exact:true}).click();await create('Necesitamos organizar compromisos de tiempo para investigación y servicio. Ejemplo sintético operacional.');await page.locator('[data-example="stockflow_time"]').click();await idle();await accept();
 const secondId=await page.evaluate(()=>localStorage.getItem('genius_d1_case'));const second=await get(`/api/cases/${secondId}`);const secondResult=second.jobs.find(j=>j.canonical_results).canonical_results;
 check(secondResult.horizon===4&&secondResult.task.kind==='operational','second profile configuration changes domain/clock/task semantics');check(secondResult.joint_law===null,'absent law is not silently replaced');check((await page.locator('.policy-card .metric').allTextContents()).every(x=>x==='Sin ley declarada'),'probability absence remains distinct from zero in UI');check(secondResult.policies[Object.keys(secondResult.policies)[0]].cag.possible.length>0,'CAG remains available without a probability law');await shot('desktop-operational-no-law');
 await page.setViewportSize({width:320,height:844});await nav('futures');await shot('320-operational-futures');await nav('conclusion');await shot('320-operational-conclusion');
 check(evidence.page_errors.length===0,'no uncaught browser errors');check(evidence.external_requests.length===0,'no external browser requests');
 evidence.status='PASS';evidence.case_ids=[cid,secondId];fs.writeFileSync(path.join(out,'browser-d3-evidence.json'),JSON.stringify(evidence,null,2));console.log(JSON.stringify(evidence));
})().catch(async error=>{evidence.status='FAIL';evidence.error=String(error);if(debugPage){evidence.last_dom=await debugPage.locator('#step-nav').evaluate(el=>el.outerHTML).catch(()=>null);await debugPage.screenshot({path:path.join(out,'failure.png'),fullPage:true}).catch(()=>{});}fs.writeFileSync(path.join(out,'browser-d3-evidence.json'),JSON.stringify(evidence,null,2));console.error(error);process.exitCode=1;}).finally(async()=>{if(browser)await browser.close();server.kill();});
