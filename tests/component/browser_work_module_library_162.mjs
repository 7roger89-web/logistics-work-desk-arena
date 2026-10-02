// Optional real-browser #162 acceptance (Work Module Library V1).
// Uses an externally installed Playwright; the sandbox has no browser download,
// so the runner is told where both live:
//   PLAYWRIGHT_MODULE=/path/to/playwright-core/index.mjs \
//   CHROMIUM_EXECUTABLE=/path/to/chromium \
//   CHROMIUM_LIB_PATH=/path/with/missing/nss/libs   (optional, browser-only LD_LIBRARY_PATH) \
//   node tests/component/browser_work_module_library_162.mjs evidence/162
//
// It boots the isolated acceptance host (mongomock only, loopback:9502), drives
// the SHIPPED bundle in a real browser, exercises the attach + completion flow
// through the real dispatcher, and writes desktop/mobile screenshots.
import { spawn } from 'node:child_process';
import { mkdirSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import assert from 'node:assert/strict';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const output = process.argv[2] || '/tmp/log162-screenshots';
mkdirSync(output, { recursive: true });

const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || 'playwright');
const HOST = 'http://127.0.0.1:9502';
const host = spawn(process.env.PYTHON || 'python', ['scripts/verify_work_module_library_162.py'], {
  cwd: root, stdio: ['ignore', 'ignore', 'pipe'],
});
let hostErrors = '';
host.stderr.on('data', (b) => (hostErrors += b));
let browser;

const shot = (page, name) => page.screenshot({ path: path.join(output, name), fullPage: false });

try {
  let up = false;
  for (let i = 0; i < 150; i++) {
    try { if ((await fetch(`${HOST}/model`)).ok) { up = true; break; } } catch {}
    await new Promise((r) => setTimeout(r, 100));
  }
  assert.ok(up, 'acceptance host came up');

  browser = await chromium.launch({
    executablePath: process.env.CHROMIUM_EXECUTABLE || undefined,
    headless: true,
    args: ['--no-sandbox', '--disable-dev-shm-usage'],
    // Browser-only LD_LIBRARY_PATH: exported globally it would shadow system
    // libs for the Python host (e.g. libsqlite3) and break the dispatcher.
    env: process.env.CHROMIUM_LIB_PATH
      ? { ...process.env, LD_LIBRARY_PATH: process.env.CHROMIUM_LIB_PATH }
      : process.env,
  });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));

  const openShipment = async () => {
    await page.goto(HOST);
    await page.getByRole('link', { name: 'Lô Hàng', exact: true }).first().click();
    await page.getByTestId('shipment-period-tat-ca').click();
    await page.getByRole('link', { name: 'SEA-162', exact: true }).click();
    await page.getByTestId('shipment-journey').waitFor();
  };

  // 1. Zero modules: the base journey keeps its authority and shows no rollup.
  await openShipment();
  assert.equal(await page.locator('[data-testid^="journey-node-"]').count(), 7, 'base map = 7 nodes');
  assert.equal(await page.getByTestId('journey-modules').count(), 0, 'no rollup before attach');
  assert.equal(await page.getByTestId('journey-add-module').count(), 1, 'authorised actor can attach');
  await shot(page, 'desktop-1-base-journey.png');

  // 2. Human attach flow: panel → ACTIVE choice → confirm → fresh readback.
  await page.getByTestId('journey-add-module').click();
  await page.getByTestId('journey-add-module-panel').waitFor();
  await page.getByRole('radio', { name: 'Chọn IMPORT SPECIAL HANDLING', exact: true }).check();
  await shot(page, 'desktop-2-attach-panel.png');
  const beforeAttach = await (await page.request.get(`${HOST}/model`)).json();
  const beforeVersion = beforeAttach.shipments.find((s) => s.id === 'SEA-162').version;
  await page.getByTestId('journey-add-module-confirm').click();
  await page.getByTestId('journey-modules').waitFor();
  const afterAttach = await (await page.request.get(`${HOST}/model`)).json();
  const lot = afterAttach.shipments.find((s) => s.id === 'SEA-162');
  assert.ok(lot.version > beforeVersion, 'attach bumped the shipment version (authoritative write)');
  const instanceId = lot.journey.modules[0].instanceId;

  // The branch appears WITHOUT touching base truth.
  assert.equal(await page.locator('[data-testid^="journey-node-"]').count(), 7, 'base nodes unchanged');
  assert.equal(
    await page.getByTestId(`journey-module-${instanceId}`).getAttribute('data-module-status'), 'BLOCKING');
  assert.match(await page.getByTestId(`journey-module-gate-${instanceId}`).innerText(), /^Chặn DELIVERY — còn thiếu/);
  assert.match(await page.getByTestId(`journey-module-progress-${instanceId}`).innerText(), /0\/3 bước/);
  assert.equal(await page.getByTestId(`journey-module-steps-${instanceId}`).count(), 0, 'internal DAG starts collapsed');
  assert.match(await page.getByTestId('journey-modules').innerText(), /Nguồn: Thêm thủ công[\s\S]*staging\.support/);
  await shot(page, 'desktop-3-rollup-attached.png');

  // 3. Steps on demand; quick panel shows guidance; workspace is the module panel.
  await page.getByTestId(`journey-module-toggle-${instanceId}`).click();
  await page.getByTestId(`journey-module-steps-${instanceId}`).waitFor();
  assert.equal(await page.locator('[data-testid^="journey-node-wm-"]').count(), 3, 'three internal steps');
  await page.getByTestId(`journey-node-wm-${instanceId}-prepare-file`).click();
  await page.getByTestId('journey-module-context').waitFor();
  await page.getByTestId('journey-module-guidance').waitFor();
  await shot(page, 'desktop-4-steps-and-guidance.png');
  await page.getByTestId('journey-open-workspace').click();
  await page.getByTestId('journey-stage-workspace').waitFor();
  await page.getByTestId('journey-stage-workspace').getByRole('button', { name: 'Thông tin', exact: true }).click();
  await page.getByTestId('work-module-step-panel').waitFor();
  await shot(page, 'desktop-5-step-workspace.png');

  // 4. Persisted factual completion drives readiness after readback.
  await page.getByTestId('work-module-step-complete').click();
  await page.waitForFunction(
    (id) => document.querySelector(`[data-testid="journey-module-progress-${id}"]`)?.textContent?.includes('1/3'),
    instanceId, { timeout: 15000 });
  const afterStep = await (await page.request.get(`${HOST}/model`)).json();
  const facts = afterStep.shipments.find((s) => s.id === 'SEA-162').journey.modules[0];
  assert.equal(facts.completedCount, 1, 'canonical fact persisted (not a visual-only change)');
  assert.equal(facts.status, 'BLOCKING', 'gate still blocking until all required steps land');
  assert.deepEqual(errors, [], 'no page errors during the write');
  await shot(page, 'desktop-6-completion-readback.png');

  // 5. The gate clears only once every required step is a persisted fact.
  for (const node of ['submit-process', 'result-received']) {
    await page.getByTestId(`journey-node-wm-${instanceId}-${node}`).click();
    await page.getByTestId('journey-open-workspace').click();
    await page.getByTestId('journey-stage-workspace').getByRole('button', { name: 'Thông tin', exact: true }).click();
    await page.getByTestId('work-module-step-complete').click();
    await page.waitForFunction(
      (sel) => !document.querySelector(sel), `[data-testid="work-module-step-complete"][disabled]`, { timeout: 15000 })
      .catch(() => {});
  }
  await page.waitForFunction(
    (id) => document.querySelector(`[data-testid="journey-module-${id}"]`)?.getAttribute('data-module-status') === 'DONE',
    instanceId, { timeout: 15000 });
  assert.equal(await page.getByTestId(`journey-module-gate-${instanceId}`).count(), 0, 'no gate sentence when done');
  const doneState = await (await page.request.get(`${HOST}/model`)).json();
  const doneModule = doneState.shipments.find((s) => s.id === 'SEA-162').journey.modules[0];
  assert.equal(doneModule.summary, '3/3 bước');
  assert.equal(doneModule.gateText, '');
  await shot(page, 'desktop-7-gate-cleared.png');

  // 6. Mobile layout: same truth, no page overflow, tappable controls.
  await page.setViewportSize({ width: 390, height: 844 });
  await page.getByTestId('shipment-journey').scrollIntoViewIfNeeded();
  await shot(page, 'mobile-1-journey.png');
  await page.getByTestId(`journey-module-${instanceId}`).scrollIntoViewIfNeeded();
  await shot(page, 'mobile-2-rollup.png');
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  assert.ok(overflow <= 1, `no horizontal page overflow (got ${overflow})`);

  // 7. Bounded template library surface.
  await page.setViewportSize({ width: 1440, height: 1000 });
  // Route state is component-local (MemoryRouter), so the library is reached
  // the way a person reaches it: through the navigation entry.
  await page.getByRole('link', { name: 'Thư viện quy trình', exact: true }).first().click();
  await page.getByTestId('work-module-library').waitFor();
  assert.match(await page.getByTestId('work-module-library').innerText(), /IMPORT_SPECIAL_HANDLING_DEMO_V1/);
  assert.equal(await page.getByTestId('wm-library-new').count(), 1, 'authorised actor may author a template');
  await shot(page, 'desktop-8-template-library.png');

  assert.deepEqual(errors, [], 'zero page errors for the whole journey');
  console.log(
    `PASS #162 browser: 1440/390px, attach → rollup 0/3 BLOCKING → 3/3 DONE with gate cleared, ` +
    `facts persisted server-side, library bounded, zero page errors → ${output}`);
} catch (err) {
  console.error(hostErrors.slice(-1500));
  throw err;
} finally {
  await browser?.close();
  host.kill();
}
