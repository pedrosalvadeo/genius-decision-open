/* Local browser integration gate. No remote navigation or real observations.
 * PLAYWRIGHT_MODULE and CHROMIUM_PATH must point to installed tooling.
 * PYTHONPATH must include Flask, twin and kernel; run from repository root.
 * BROWSER_QA_DIR is optional. Synthetic dossier/screen captures remain there.
 */
const fs=require('fs'),path=require('path'),os=require('os'),assert=require('assert/strict');
const {spawn}=require('child_process');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const out=process.env.BROWSER_QA_DIR||fs.mkdtempSync(path.join(os.tmpdir(),'genius-d1-browser-'));
fs.mkdirSync(out,{recursive:true});
const server=spawn(process.env.PYTHON||'python',['-m','genius_twin','--port','8765','--database',path.join(out,'browser.sqlite3')],{env:process.env});
let browser; const findings={scenario:'SYNTHETIC_BROWSER_TEST_NOT_FIELD_DATA',viewports:[],checks:[],page_errors:[],external_requests:[]};
const check=(condition,label)=>{assert.ok(condition,label);findings.checks.push(label);};
(async()=>{
  await new Promise((resolve,reject)=>{const timer=setTimeout(()=>reject(new Error('local server start timeout')),10000);server.stderr.on('data',s=>{if(s.toString().includes('Running on')){clearTimeout(timer);resolve();}});server.once('exit',c=>reject(new Error('server exited '+c)));});
  browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_PATH,args:['--no-sandbox']});
  const context=await browser.newContext({viewport:{width:1440,height:1000},acceptDownloads:true});
  const page=await context.newPage(); page.setDefaultTimeout(20000);
  page.on('pageerror',e=>findings.page_errors.push(e.message));
  page.on('request',r=>{if(!r.url().startsWith('http://127.0.0.1:8765')&&!r.url().startsWith('blob:'))findings.external_requests.push(r.url());});
  const idle=()=>page.waitForFunction(()=>!document.querySelector('#main').hasAttribute('aria-busy'));
  const shot=async name=>{await idle();await page.screenshot({path:path.join(out,name+'.png'),fullPage:true});check(!(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth)),name+' no page overflow');};
  const nav=async view=>{await page.locator(`[data-view="${view}"]`).click();await idle();};
  const body=()=>page.locator('body').innerText();
  await page.goto('http://127.0.0.1:8765');await idle();await shot('desktop-welcome');
  await page.locator('#intake-mode').selectOption('d1');await page.getByRole('button',{name:'Usar relato de ejemplo',exact:true}).click();
  await page.getByRole('button',{name:/Construir propuesta/}).click();await idle();await shot('desktop-review');
  await page.getByRole('button',{name:'Confirmar alcance y continuar'}).click();await idle();check((await page.locator('#error').innerText()).includes('tres decisiones'),'confirmation blocks unchecked proposal');
  for(const id of ['scope-check','synthetic-check','support-check'])await page.locator('#'+id).check();
  await page.getByRole('button',{name:'Confirmar alcance y continuar'}).click();await idle();await shot('desktop-twin');
  await page.getByRole('button',{name:'Lista',exact:true}).click();check((await body()).includes('P1'),'equivalent textual model includes plant identity');
  await page.getByRole('button',{name:'Evaluar esta versión',exact:true}).click();await idle();
  check(await page.locator('.policy-card').count()===3,'three substantive policy cards');
  const metrics=await page.locator('.policy-card .metric').allTextContents();check(JSON.stringify(metrics)===JSON.stringify(['1/2','5/6','1/1'])||JSON.stringify(metrics)===JSON.stringify(['1/2','1/1','5/6']),'native baseline PVS rendered');
  await page.locator('#policy-select').selectOption('E');await page.locator('#scenario-select').selectOption('HA');await page.locator('#day-select').selectOption('10');await shot('desktop-futures');
  check((await body()).includes('Monitor: hubo un fallo'),'persistent historical failure visible');
  await nav('conclusion');check((await body()).includes('es la selección bajo la norma declarada'),'base unique selection visible');await shot('desktop-conclusion');
  const cid=await page.evaluate(()=>localStorage.getItem('genius_d1_case'));
  const get=async endpoint=>(await page.request.get('http://127.0.0.1:8765'+endpoint)).json();
  const base=await get(`/api/cases/${cid}`);const baseCanonical=base.jobs.find(j=>j.version===1).canonical_results;
  check(baseCanonical.decision.selected==='R','baseline UI is tied to R native selection');
  await nav('change');await page.getByRole('button',{name:'Usar cambio con relevo'}).click();await page.getByRole('button',{name:'Revisar propuesta',exact:true}).click();await idle();
  await page.getByRole('button',{name:'Aceptar y reevaluar',exact:true}).click();await idle();await shot('desktop-comparison');
  const revised=await get(`/api/cases/${cid}`);const editCanonical=revised.jobs.find(j=>j.version===2).canonical_results;
  check(revised.case.current_version===2,'material edit creates new version');
  check(editCanonical.policies.E_prime.pvs.value==='1/1'&&editCanonical.decision.selected===null,'edited result preserves no unique winner');
  check(editCanonical.policies.E_prime.trajectories.HA.totals.minutes_a===310,'edited HA time exact');
  await nav('conclusion');check((await body()).includes('No hay una selección única'),'edited UI preserves incomparability');
  for(const width of [390,320]){
    await page.setViewportSize({width,height:844});findings.viewports.push({width,height:844});
    for(const view of ['review','twin','futures','conclusion','change','evidence']){await nav(view);await shot(`mobile-${width}-${view}`);}
  }
  await page.setViewportSize({width:1440,height:1000});findings.viewports.push({width:1440,height:1000});
  await nav('evidence');
  const downloadPromise=page.waitForEvent('download');await page.getByRole('button',{name:'Descargar expediente JSON'}).click();const download=await downloadPromise;await idle();
  const exportPath=path.join(out,'synthetic-dossier.json');await download.saveAs(exportPath);const exp=JSON.parse(fs.readFileSync(exportPath));
  check(JSON.stringify(exp.dossier.jobs.find(j=>j.version===2).canonical_results)===JSON.stringify(editCanonical),'download canonical result equals HTTP result');
  const robust1=exp.dossier.evaluations.find(e=>e.job.version===1).evaluation.native_result.input_digest;
  const robust2=exp.dossier.evaluations.find(e=>e.job.version===2).evaluation.native_result.input_digest;
  check(robust1!==robust2,'material edit changes native input digest');
  await page.locator('#obs-policy').selectOption('E_prime');await page.locator('#obs-scenario').selectOption('HA');await page.locator('#obs-day').fill('10');await page.locator('#obs-water').fill('0');await page.locator('#obs-time').fill('2026-10-01T12:00');await page.locator('#obs-source').fill('SYNTHETIC TEST ONLY: browser acceptance; no real-world measurement.');await page.locator('#observation-check').check();
  await page.getByRole('button',{name:'Guardar y contrastar'}).click();await idle();check((await body()).includes('Hay una discrepancia'),'frozen contrast discrepancy visible');await shot('desktop-observation');
  await page.getByRole('button',{name:'Evaluar esta versión',exact:true}).click();await idle();await nav('conclusion');check((await body()).includes('La recomendación está suspendida'),'reevaluation does not lift discrepancy suspension');
  await page.reload();await idle();await nav('conclusion');check((await body()).includes('La recomendación está suspendida'),'reload preserves current version and suspension');
  await nav('change');await page.getByRole('button',{name:'Proponer restauración de la versión 1',exact:true}).click();await idle();await page.getByRole('button',{name:'Aceptar y reevaluar',exact:true}).click();await idle();
  const restored=await get(`/api/cases/${cid}`);check(restored.case.current_version===4&&restored.versions.length===4,'restore appends fourth revision');check(restored.observations.length===1,'restore preserves declared observation');
  await page.getByRole('button',{name:'Nueva exploración'}).click();await page.locator('#intake-mode').selectOption('general');await page.locator('#narrative').fill('Quiero elegir un discurso para una audiencia');await page.getByRole('button',{name:/Construir propuesta/}).click();await idle();check(await page.getByRole('heading',{name:'Construye tu decisión',exact:true}).isVisible(),'new general narrative opens the configurable builder');const generalId=await page.evaluate(()=>localStorage.getItem('genius_d1_case'));const general=await get(`/api/cases/${generalId}`);check(general.case.status==='needs_model'&&general.draft.model===null&&general.proposals.length===0,'general narrative retains model obligation without invented parameters');await shot('desktop-general-draft');
  check(findings.page_errors.length===0,'no uncaught browser errors');check(findings.external_requests.length===0,'no external browser requests');
  findings.status='PASS';findings.base_input_digest=robust1;findings.edited_input_digest=robust2;findings.finished_at=new Date().toISOString();
  fs.writeFileSync(path.join(out,'browser-evidence.json'),JSON.stringify(findings,null,2));console.log(JSON.stringify(findings));
})().catch(e=>{console.error(e);process.exitCode=1;findings.status='FAIL';findings.error=String(e);fs.writeFileSync(path.join(out,'browser-evidence.json'),JSON.stringify(findings,null,2));}).finally(async()=>{if(browser)await browser.close();server.kill();});
