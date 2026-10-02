// Optional real-browser #160 acceptance. Uses an externally installed Playwright.
// PLAYWRIGHT_MODULE=/path/to/playwright/index.mjs CHROMIUM_EXECUTABLE=/path/to/chromium
// node tests/component/browser_visual_shipment_workspace.mjs /tmp/log160-screenshots
// PYTHON=/path/to/python and CHROMIUM_LIB_PATH=/path/to/browser/libs override the
// interpreter and the BROWSER-ONLY LD_LIBRARY_PATH (exporting it globally would
// shadow system libs for the Python host, e.g. libsqlite3). Same contract as the
// #162 runner, so both suites are runnable in an offline sandbox.
import { spawn } from 'node:child_process';
import { mkdirSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import assert from 'node:assert/strict';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const output=process.argv[2] || '/tmp/log160-screenshots';mkdirSync(output,{recursive:true});
const {chromium}=await import(process.env.PLAYWRIGHT_MODULE || 'playwright');
const host=spawn(process.env.PYTHON || 'python',['scripts/verify_visual_shipment_workspace.py'],{cwd:root,stdio:['ignore','ignore','pipe']});
let hostErrors='';host.stderr.on('data',b=>hostErrors+=b);
let browser;
try {
  for(let i=0;i<100;i++) {try {if((await fetch('http://127.0.0.1:9501/model')).ok)break;}catch{}await new Promise(r=>setTimeout(r,100));}
  browser=await chromium.launch({executablePath:process.env.CHROMIUM_EXECUTABLE || undefined,headless:true,args:['--no-sandbox'],
    env:process.env.CHROMIUM_LIB_PATH?{...process.env,LD_LIBRARY_PATH:process.env.CHROMIUM_LIB_PATH}:process.env});
  const page=await browser.newPage({viewport:{width:1440,height:1000}});const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto('http://127.0.0.1:9501');
  await page.getByRole('link',{name:'Lô Hàng',exact:true}).first().click();
  await page.getByTestId('shipment-period-tat-ca').click();
  await page.getByRole('link',{name:'SEA-160',exact:true}).click();
  assert.equal(await page.locator('[data-testid^="journey-node-"]').count(),11);
  await page.getByTestId('journey-node-si-vgm').click();
  await page.getByTestId('shipment-journey').screenshot({path:path.join(output,'desktop.png')});
  await page.getByTestId('journey-open-workspace').click();
  await page.getByTestId('journey-stage-workspace').getByRole('button',{name:'Thông tin',exact:true}).click();
  await page.getByLabel('Trạng thái SI',{exact:true}).selectOption('ACCEPTED');
  await page.getByLabel('Trạng thái VGM',{exact:true}).selectOption('ACCEPTED');
  await page.getByRole('button',{name:'Lưu mốc có bằng chứng',exact:true}).click();
  await page.waitForFunction(()=>document.querySelector('[data-testid="journey-node-si-vgm"]')?.getAttribute('data-state')==='COMPLETED');
  const actual=await (await page.request.get('http://127.0.0.1:9501/model')).json();
  const lot=actual.shipments.find(s=>s.id==='SEA-160');
  assert.equal(lot.journey.seaFacts.si_status,'ACCEPTED');assert.equal(lot.journey.seaFacts.vgm_status,'ACCEPTED');
  assert.equal(lot.journey.primaryAction.text,lot.nextAction);
  await page.getByTestId('sea-export-facts').screenshot({path:path.join(output,'facts-readback.png')});
  await page.setViewportSize({width:390,height:844});
  await page.getByTestId('journey-node-booking').scrollIntoViewIfNeeded();
  await page.screenshot({path:path.join(output,'mobile-map.png')});
  await page.getByTestId('journey-quick-panel').scrollIntoViewIfNeeded();
  await page.screenshot({path:path.join(output,'mobile-panel.png')});
  const overflow=await page.evaluate(()=>document.documentElement.scrollWidth-window.innerWidth);assert.ok(overflow<=1,`page overflow: ${overflow}`);
  const controls=await page.getByTestId('journey-stage-workspace').locator('button').evaluateAll(els=>els.map(e=>({h:e.getBoundingClientRect().height,w:e.getBoundingClientRect().width})));
  assert.ok(controls.every(c=>c.h>=44 && c.w>=44),'44px workspace touch targets');
  assert.deepEqual(errors,[]);
  console.log('PASS #160 browser: 1440/390px, 11 nodes, canonical write/fresh readback, single primary, no page overflow, 44px workspace controls, zero page errors');
} catch(e) { console.error(hostErrors.slice(-1200));throw e; }
finally {await browser?.close();host.kill();}
