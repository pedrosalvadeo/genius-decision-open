/* Real browser + live HTTP/worker test. Requires externally installed Playwright. */
const {chromium} = require('playwright');
const fs = require('fs');
const path = require('path');

(async () => {
  const base = process.env.GENIUS_TEST_URL || 'http://127.0.0.1:8088';
  const out = process.env.GENIUS_BROWSER_OUTPUT || './browser-evidence';
  fs.mkdirSync(out, {recursive:true});
  const browser = await chromium.launch({executablePath:process.env.GENIUS_BROWSER_PATH,headless:true,args:['--no-sandbox','--disable-gpu','--disable-dev-shm-usage']});
  const page = await browser.newPage({viewport:{width:1440,height:1050}});
  const errors=[];
  page.on('pageerror', e=>errors.push(e.message));
  const results=[];
  try {
    // Failure to load the notice must never offer registration.
    await page.route('**/api/config', route => route.abort());
    await page.goto(base);
    await page.waitForTimeout(250);
    if (!(await page.locator('#mode-register').isDisabled())) throw Error('REGISTRATION_WITHOUT_NOTICE');
    await page.unroute('**/api/config');
    // Hold the initial unauthenticated session response until registration has
    // succeeded: a slow bootstrap must not terminate the newer session.
    let releaseInitialCheck, sessionCheckStarted;
    const heldSession = new Promise(resolve => {releaseInitialCheck = resolve;});
    const capturedSession = new Promise(resolve => {sessionCheckStarted = resolve;});
    let deliveredSession;
    await page.route('**/api/me', route => {
      deliveredSession = (async () => {
        const response = await route.fetch();
        if (response.status() !== 401) throw Error('EXPECTED_INITIAL_ANONYMOUS_SESSION');
        sessionCheckStarted();
        await heldSession;
        await route.fulfill({response});
      })();
      return deliveredSession;
    });
    await page.reload();
    await capturedSession;
    results.push('registration_fails_closed_without_notice');
    await page.locator('#mode-register').click();
    // Report the invalid field before sending credentials or creating an account.
    await page.locator('#username').fill('synthetic@example.invalid');
    await page.locator('#password').fill('SyntheticOnly-Password-42');
    await page.locator('#auth-submit').click();
    if (!(await page.locator('#username-error').innerText()).includes('no un correo')) throw Error('EMAIL_NOT_IDENTIFIED_AS_ALIAS_ERROR');
    if (await page.locator('#password-error').isVisible()) throw Error('EMAIL_MISLABELED_AS_PASSWORD_ERROR');
    if (await page.locator('#username').getAttribute('aria-invalid') !== 'true') throw Error('ALIAS_ERROR_NOT_ACCESSIBLE');
    results.push('email_error_at_username_field');
    await page.locator('#username').fill('qa_'+Date.now());
    await page.locator('#password').fill('short');
    await page.locator('#auth-submit').click();
    if (!(await page.locator('#password-error').innerText()).includes('Contraseña:')) throw Error('PASSWORD_LENGTH_ERROR_NOT_IDENTIFIED');
    results.push('short_password_error_at_password_field');
    await page.locator('#password').fill('SyntheticOnly-Password-42');
    await page.locator('#privacy-accepted').check();
    await page.locator('#adult-confirmed').check();
    await page.screenshot({path:path.join(out,'desktop-access.png'),fullPage:true});
    await page.locator('#auth-submit').click();
    await page.locator('#workspace').waitFor({state:'visible'});
    results.push('registration_real_http');
    releaseInitialCheck();
    await deliveredSession;
    await page.unroute('**/api/me');
    await page.waitForTimeout(100);
    if (!(await page.locator('#workspace').isVisible())) throw Error('STALE_BOOTSTRAP_CLOSED_NEW_SESSION');
    results.push('delayed_anonymous_bootstrap_preserves_new_session');
    await page.locator('.sidebar [data-view="create"]').click();
    await page.locator('#profile').selectOption('hours');
    await page.locator('#case-title').fill('QA synthetic credits');
    await page.locator('#synthetic-example').click();
    await page.locator('#scope-acknowledged').check();
    await page.locator('#permission-confirmed').check();
    await page.locator('#case-submit').click();
    await page.getByRole('button',{name:'Admitir y ejecutar esta versión',exact:true}).click();
    await page.waitForFunction(()=>document.querySelector('#case-detail')?.innerText.includes('Ejecución terminada; revisar resultado'),{},{timeout:20000});
    results.push('guided_request_real_engine_result');
    await page.screenshot({path:path.join(out,'desktop-result.png'),fullPage:true});
    for (const [example, semantic] of [['hours-unknown','Desconocido'],['fdq-frontier','Conjunto o incomparabilidad; sin selección'],['fdq-selector','Resultado justificado en el alcance']]) {
      await page.locator('.sidebar [data-view="create"]').click();
      if (!(await page.locator(`[data-example="${example}"]`).isVisible())) {
        await page.getByText('Otros ejemplos sintéticos, sin envío automático',{exact:true}).click();
      }
      await page.locator(`[data-example="${example}"]`).click();
      await page.locator('#case-title').fill('QA synthetic '+example);
      await page.locator('#scope-acknowledged').check();
      await page.locator('#permission-confirmed').check();
      await page.locator('#case-submit').click();
      await page.getByRole('button',{name:'Admitir y ejecutar esta versión',exact:true}).click();
      await page.waitForFunction(()=>document.querySelector('#case-detail')?.innerText.includes('Ejecución terminada; revisar resultado'),{},{timeout:20000});
      const visible=await page.locator('#case-detail').innerText();
      if(!visible.toLowerCase().includes(semantic.toLowerCase()))throw Error('MISSING_SEMANTIC_'+example);
      results.push('real_browser_'+example);
    }
    await page.locator('.sidebar [data-view="create"]').click();
    await page.locator('#profile').selectOption('choice');
    await page.locator('[data-example="choice-leisure"]').click();
    await page.locator('#case-title').fill('QA synthetic guided decision');
    await page.locator('[data-choice-next="2"]:visible').click();
    await page.locator('[data-choice-next="3"]:visible').first().click();
    await page.setViewportSize({width:390,height:844});
    await page.screenshot({path:path.join(out,'mobile-choice-values.png'),fullPage:true});
    if(await page.evaluate(()=>document.documentElement.scrollWidth>window.innerWidth))throw Error('CHOICE_FORM_OVERFLOW');
    await page.locator('[data-choice-next="4"]:visible').click();
    await page.locator('#choice-review').click();
    await page.locator('#choice-confirm-box').waitFor({state:'visible'});
    await page.locator('#choice-confirm').check();
    // Changing a priority must revoke confirmation, including stale responses.
    await page.locator('#choice-selection').selectOption('unique');
    if(await page.locator('#choice-confirm').isChecked())throw Error('STALE_MODEL_CONFIRMATION');
    await page.locator('#choice-selection').selectOption('lexicographic');
    await page.locator('#choice-priorities select').nth(0).selectOption('interest');
    await page.locator('#choice-priorities select').nth(1).selectOption('time');
    await page.locator('#choice-review').click();
    await page.locator('#choice-confirm-box').waitFor({state:'visible'});
    await page.locator('#choice-confirm').check();
    await page.locator('#scope-acknowledged').check();
    await page.locator('#permission-confirmed').check();
    await page.locator('#case-submit').click();
    await page.getByRole('button',{name:'Admitir y ejecutar esta versión',exact:true}).click();
    await page.getByRole('heading',{name:'Recomendación según tus datos',exact:true}).waitFor({timeout:20000});
    const choiceText=await page.locator('#case-detail').innerText();
    if(!choiceText.includes('Museo')||!choiceText.includes('Qué cedés'))throw Error('CHOICE_RESULT_MISSING');
    await page.screenshot({path:path.join(out,'mobile-choice-result.png'),fullPage:true});
    if(await page.evaluate(()=>document.documentElement.scrollWidth>window.innerWidth))throw Error('CHOICE_RESULT_OVERFLOW');
    await page.setViewportSize({width:1440,height:1050});
    await page.screenshot({path:path.join(out,'desktop-choice-result.png'),fullPage:true});
    await page.getByRole('button',{name:'Editar datos',exact:true}).click();
    await page.locator('[data-choice-next="2"]:visible').click();
    await page.locator('[data-choice-next="3"]:visible').first().click();
    await page.locator('[data-alternative="museum"][data-criterion="interest"]').fill('');
    await page.locator('[data-choice-next="4"]:visible').click();
    await page.locator('#choice-review').click();
    await page.locator('#choice-confirm-box').waitFor({state:'visible'});
    await page.locator('#choice-confirm').check();
    await page.locator('#scope-acknowledged').check();
    await page.locator('#permission-confirmed').check();
    await page.locator('#case-submit').click();
    await page.getByRole('button',{name:'Admitir y ejecutar esta versión',exact:true}).click();
    await page.getByRole('heading',{name:'Falta información para recomendar',exact:true}).waitFor({timeout:20000});
    await page.locator('#revision-select').selectOption('1');
    await page.getByRole('heading',{name:'Recomendación según tus datos',exact:true}).waitFor();
    results.push('choice_real_kernel_recommendation','choice_mobile_form_and_result','choice_confirmation_invalidated','choice_unknown_new_revision','choice_previous_result_preserved');
    await page.reload();
    await page.locator('#workspace').waitFor({state:'visible'});
    results.push('authenticated_reload_persistence');
    await page.setViewportSize({width:390,height:844});
    await page.screenshot({path:path.join(out,'mobile-cases.png'),fullPage:true});
    const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>window.innerWidth);
    if(overflow)throw Error('MOBILE_HORIZONTAL_OVERFLOW');
    if(errors.length)throw Error('BROWSER_JAVASCRIPT_ERRORS: '+errors.join('|'));
    results.push('mobile_no_horizontal_overflow','no_javascript_errors');
    fs.writeFileSync(path.join(out,'result.json'),JSON.stringify({status:'PASS',browser:await browser.version(),synthetic:true,checks:results},null,2));
    console.log(JSON.stringify({status:'PASS',checks:results}));
  } catch(e) {
    await page.screenshot({path:path.join(out,'failure.png'),fullPage:true});
    fs.writeFileSync(path.join(out,'result.json'),JSON.stringify({status:'FAIL',checks:results,error:e.message,errors},null,2));
    throw e;
  } finally {await browser.close();}
})().catch(e=>{console.error(e.message);process.exit(1)});
