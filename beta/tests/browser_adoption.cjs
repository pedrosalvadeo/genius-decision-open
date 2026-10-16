/* Local browser test: no external hosts, registrations or real observations. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const {chromium} = require('playwright');
(async () => {
  const base = process.env.GENIUS_TEST_URL || 'http://127.0.0.1:8088';
  const out = process.env.GENIUS_BROWSER_OUTPUT || '/tmp/genius-adoption-browser';
  fs.mkdirSync(out, {recursive:true});
  const browser = await chromium.launch({executablePath:process.env.GENIUS_BROWSER_PATH || '/usr/bin/chromium',headless:true,args:['--no-sandbox']});
  try {
    for (const viewport of [{width:1365,height:1000},{width:390,height:844}]) {
      const context = await browser.newContext({viewport});
      const page = await context.newPage(), errors = [], writes = [];
      page.on('pageerror', e => errors.push(e.message));
      page.on('request', r => { if(r.method() !== 'GET') writes.push(r.url()); });
      await page.goto(base+'/adopt');
      assert(await page.locator('#reveal').isDisabled());
      await page.locator('#predict').click();
      assert(await page.locator('#estimator').isDisabled());
      await page.locator('#reveal').click();
      assert.match(await page.locator('#demo-result').textContent(), /predicción 22 °C; dato posterior 21 °C; error absoluto 1 °C/);
      assert.equal(await page.locator('#demo-link').inputValue(),base+'/adopt#demo-last');
      await page.locator('#reset').click();
      assert.equal(await page.locator('#demo-link').inputValue(),'');
      await page.locator('#estimator').selectOption('mean');
      await page.locator('#predict').click(); await page.locator('#reveal').click();
      assert.match(await page.locator('#demo-result').textContent(), /predicción 20 °C/);
      await page.goto(base+'/adopt#demo-mean');
      assert.equal(await page.locator('#estimator').inputValue(),'mean');
      assert(await page.locator('#reveal').isDisabled());
      // Invalid fragments do not become executable content or a live-result claim.
      await page.goto(base+'/adopt#demo-%3Cscript%3E');
      assert(!(await page.locator('#demo-result').textContent()).includes('<script>'));
      assert(await page.locator('#reveal').isDisabled());
      await page.locator('#policy-form button').click();
      assert(await page.locator('#policy-output').isHidden());
      await page.locator('#policy-consent').check();
      await page.locator('#policy-form button').click();
      const trial=JSON.parse(await page.locator('#policy-json').textContent());
      assert.equal(trial.max_births,1); assert.equal(trial.lease_seconds,86400);
      assert(Math.abs(Date.parse(trial.valid_until)-Date.now()-86400000)<10000);
      await page.locator('#hosting-mode').selectOption('persistent');
      assert(!(await page.locator('#policy-consent').isChecked()));
      assert(await page.locator('#policy-output').isHidden());
      await page.locator('#policy-consent').check(); await page.locator('#policy-form button').click();
      const policy=JSON.parse(await page.locator('#policy-json').textContent());
      assert.deepEqual(policy,{worlds:[{world_id:'genius-reference-synthetic-v1',focus:['pump']}],max_births:1,persistent:true,lease_seconds:null,valid_until:null});
      const download = page.waitForEvent('download'); await page.locator('#download-policy').click();
      const file=await download; assert.equal(file.suggestedFilename(),'policy.json');
      assert.deepEqual(JSON.parse(fs.readFileSync(await file.path(),'utf8')),policy);
      await page.locator('#policy-consent').uncheck(); assert(await page.locator('#policy-output').isHidden());
      assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
      await page.goto(base+'/adopt');
      await page.screenshot({path:out+`/adopt-${viewport.width}.png`,fullPage:true});
      // Public observatory deep links retain stale/error evidence from the actual API contract.
      await page.route('**/network/organisms.json', r => r.fulfill({json:{checked_at:1792180000,organisms:[{station:'SAME',label:'Mendoza',status:'SOURCE_UNAVAILABLE',report_stale:true}]}}));
      await page.goto(base+'/organisms#seed-SAME');
      await page.locator('#seed-SAME').waitFor();
      assert.match(await page.locator('#seed-SAME').textContent(), /no confirma actividad actual/);
      assert.equal(await page.locator('#seed-SAME a').getAttribute('href'),'/organisms#seed-SAME');
      assert.deepEqual(errors,[]); assert.deepEqual(writes,[]);
      await context.close();
    }
    console.log('PASS: desktop/mobile demo, replay, consent reset, download, overflow, evidence and read-only requests');
  } finally { await browser.close(); }
})().catch(e => {console.error(e);process.exit(1);});
