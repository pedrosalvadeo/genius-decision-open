/* Authenticated browser gate: real cookie/CSRF mount, no public deployment. */
const fs=require('fs'),path=require('path'),os=require('os'),assert=require('assert/strict');
const {spawn}=require('child_process');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const out=process.env.BROWSER_QA_DIR||fs.mkdtempSync(path.join(os.tmpdir(),'genius-twin-beta-'));
fs.mkdirSync(out,{recursive:true});
const port=process.env.TWIN_BROWSER_PORT||'8767',base=`http://127.0.0.1:${port}`;
const evidence={scope:'AUTHENTICATED_LOCAL_BROWSER_NOT_PUBLIC_DEPLOYMENT',checks:[],errors:[],external_requests:[]};
const check=(value,label)=>{assert.ok(value,label);evidence.checks.push(label);};
const code="import os; from pathlib import Path; from genius_beta.app import create_app; d=Path(os.environ['QA_DATA']); app=create_app(dict(DATA_DIR=d,DATABASE=d/'genius.sqlite3',SUSPEND_FILE=d/'SUSPENDED',TWIN_ENABLED=True,PUBLIC_URL=os.environ['QA_ORIGIN'])); app.run(host='127.0.0.1',port=int(os.environ['QA_PORT']),threaded=True,use_reloader=False)";
const server=spawn(process.env.PYTHON||'python',['-c',code],{env:{...process.env,QA_DATA:path.join(out,'data'),QA_ORIGIN:base,QA_PORT:port}});
let logs='',browser; server.stderr.on('data',x=>logs+=x.toString());
(async()=>{
 await new Promise((resolve,reject)=>{let timer=setTimeout(()=>reject(Error(logs)),12000);server.stderr.on('data',x=>{if(x.toString().includes('Running on')){clearTimeout(timer);resolve();}});server.on('exit',()=>reject(Error(logs)));});
 browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_PATH,args:['--no-sandbox']});
 const context=await browser.newContext({viewport:{width:1440,height:1000},acceptDownloads:true});
 const page=await context.newPage();page.setDefaultTimeout(30000);
 page.on('pageerror',e=>evidence.errors.push(e.message));page.on('console',m=>{if(m.type()==='error'&&!m.text().includes('401'))evidence.errors.push(m.text());});
 page.on('request',r=>{if(!r.url().startsWith(base)&&!r.url().startsWith('blob:'))evidence.external_requests.push(r.url());});
 const idle=()=>page.waitForFunction(()=>!document.querySelector('#main').hasAttribute('aria-busy'));
 await page.goto(base+'/twin/');await idle();
 check((await page.request.get(base+'/api/twin/cases')).status()===401,'anonymous private API denied');
 await page.goto(base+'/app');await page.locator('#mode-register').click();await page.locator('#username').fill('browser-d3');await page.locator('#password').fill('Browser-test-password-123');await page.locator('#privacy-accepted').check();await page.locator('#adult-confirmed').check();await page.locator('#auth-submit').click();await page.locator('#workspace').waitFor({state:'visible'});
 check(await page.locator('#twin-link').isVisible(),'authenticated account exposes dynamic workspace');
 await page.locator('#twin-link').click();await idle();
 await page.locator('#narrative').fill('Comparar un plan de cuidado: prueba técnica sintética.');await page.getByRole('button',{name:/Construir propuesta/}).click();await idle();await page.locator('[data-example="stockflow_care"]').click();await idle();
 await page.locator('#d3-name').fill('Expediente privado de prueba');await page.locator('#d3-propose').click();await idle();await page.locator('#d3-confirm').check();await page.getByRole('button',{name:'Confirmar y explorar',exact:true}).click();await idle();
 check(!await page.locator('#error').isVisible(),'cookie and runtime CSRF permit confirm and real native calculation');
 const cid=await page.evaluate(()=>localStorage.getItem('genius_d1_case'));
 const read=await page.request.get(base+'/api/twin/cases/'+cid);const data=await read.json();
 check(data.case.current_version===1&&data.jobs[0].status==='completed','authenticated dossier persists evaluated version');
 const localKeys=await page.evaluate(()=>Object.keys(localStorage));check(localKeys.every(k=>!(/token|csrf|secret/i.test(k))),'no credential persisted in browser local storage');
 const exported=await page.request.get(base+'/api/twin/cases/'+cid+'/export');check((await exported.json()).dossier.evaluations[0].evaluation.verification.valid,'private export includes verified native receipt');
 for(const width of [1440,390,320]){await page.setViewportSize({width,height:1000});await page.screenshot({path:path.join(out,`authenticated-${width}.png`),fullPage:true});check(!(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth)),`authenticated view fits ${width}px`);}
 await page.reload();await idle();check(await page.locator('#d3-name').inputValue()==='Expediente privado de prueba','authenticated reload reopens same private dossier');
 const other=await browser.newContext();const denied=await other.request.get(base+'/api/twin/cases/'+cid);check(denied.status()===401,'separate browser context cannot read dossier');await other.close();
 check(evidence.external_requests.length===0,'no external browser requests');check(evidence.errors.length===0,'no JavaScript or CSP errors');
 evidence.status='PASS';console.log(JSON.stringify(evidence));
})().catch(e=>{evidence.status='FAIL';evidence.error=String(e);console.error(e);process.exitCode=1;}).finally(async()=>{fs.writeFileSync(path.join(out,'browser-twin-evidence.json'),JSON.stringify(evidence,null,2));if(browser)await browser.close();server.kill();});
