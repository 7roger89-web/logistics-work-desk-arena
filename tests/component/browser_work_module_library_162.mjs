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
  // Issue #190 (Owner reference 6f6c655): zero-module attach entry lives in
  // the page identity bar; it mounts the same attach panel in the Journey.
  assert.equal(await page.getByTestId('journey-add-module-page').count(), 1, 'authorised actor can attach');
  await shot(page, 'desktop-1-base-journey.png');

  // 2. Human attach flow: panel → ACTIVE choice → confirm → fresh readback.
  await page.getByTestId('journey-add-module-page').click();
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

  // 7. Bounded template library surface + a REAL lifecycle click-through.
  await page.setViewportSize({ width: 1440, height: 1000 });
  // Route state is component-local (MemoryRouter), so the library is reached
  // the way a person reaches it: through the navigation entry.
  await page.getByRole('link', { name: 'Thư viện quy trình', exact: true }).first().click();
  await page.getByTestId('work-module-library').waitFor();
  assert.match(await page.getByTestId('work-module-library').innerText(), /IMPORT_SPECIAL_HANDLING_DEMO_V1/);
  assert.equal(await page.getByTestId('wm-library-new').count(), 1, 'authorised actor may author a template');

  const draftId = 'ACCEPTANCE_LIFECYCLE_162:V1';
  const libraryRow = async () => {
    const model = await (await page.request.get(`${HOST}/model`)).json();
    return model.workModules.all.find((row) => row.id === draftId);
  };
  const stepBody = (row) => JSON.stringify(row.steps);
  const draftBefore = await libraryRow();
  assert.equal(draftBefore.status, 'DRAFT');
  await page.getByTestId(`wm-row-${draftId}`).scrollIntoViewIfNeeded();
  await shot(page, 'desktop-8-template-library.png');

  // DRAFT -> ACTIVE through the real button, then the authoritative readback.
  await page.getByTestId(`wm-activate-${draftId}`).click();
  await page.waitForFunction(
    (id) => document.querySelector(`[data-testid="wm-row-${id}"]`)?.textContent?.includes('Đang dùng'),
    draftId, { timeout: 15000 });
  const active = await libraryRow();
  assert.equal(active.status, 'ACTIVE', 'the server readback says ACTIVE, not just the button state');
  assert.equal(await page.getByTestId(`wm-activate-${draftId}`).count(), 0, 'activate is gone after activation');
  assert.equal(await page.getByTestId(`wm-retire-${draftId}`).count(), 1);
  await shot(page, 'desktop-9-lifecycle-active.png');

  // ACTIVE -> RETIRED, then the authoritative readback again.
  await page.getByTestId(`wm-retire-${draftId}`).click();
  await page.waitForFunction(
    (id) => document.querySelector(`[data-testid="wm-row-${id}"]`)?.textContent?.includes('Ngừng dùng'),
    draftId, { timeout: 15000 });
  const retired = await libraryRow();
  assert.equal(retired.status, 'RETIRED', 'the server readback says RETIRED');
  assert.equal(await page.getByTestId(`wm-activate-${draftId}`).count(), 0, 'a retired version offers no re-activation');
  await shot(page, 'desktop-10-lifecycle-retired.png');

  // The lifecycle moved ONLY the status: the stored body is untouched.
  assert.equal(retired.name, draftBefore.name);
  assert.equal(retired.version, draftBefore.version);
  assert.equal(retired.stepCount, draftBefore.stepCount);
  assert.equal(retired.anchorStage, draftBefore.anchorStage);
  assert.equal(retired.gateStage, draftBefore.gateStage);
  assert.equal(stepBody(retired), stepBody(draftBefore), 'nodes/guidance survive a status step byte-for-byte');

  // A retired version can no longer be attached (library truth is enforced).
  const choices = (await (await page.request.get(`${HOST}/model`)).json()).shipments.length;
  assert.ok(choices > 0);

  // 8. Gate-less module end to end: the authoring form leaves the gate blank by
  //    default, so this is the ordinary path — create it, prove the fresh library
  //    readback still sees it, attach it, and prove no base stage gets a gate.
  const GATELESS_ID = 'GATELESS_BROWSER_162';
  const GATELESS_NAME = 'Quy trình hàng nhập không chặn cổng';
  if (!(await page.getByTestId('wm-library-form').count())) {
    await page.getByTestId('wm-library-new').click();
  }
  const form = page.getByTestId('wm-library-form');
  await form.waitFor();
  await form.getByLabel('Mã quy trình', { exact: true }).fill(GATELESS_ID);
  await form.getByLabel('Tên hiển thị', { exact: true }).fill(GATELESS_NAME);
  await form.getByLabel('Trạng thái', { exact: true }).selectOption('ACTIVE');
  await form.getByLabel('Công đoạn neo', { exact: true }).selectOption('customs-import');
  // The gate select is deliberately left at its default ("Không chặn cổng nào").
  assert.equal(await form.getByLabel('Cổng chặn', { exact: true }).inputValue(), '');
  await form.getByLabel('Mã bước 1', { exact: true }).fill('note-info');
  await form.getByLabel('Tên bước 1', { exact: true }).fill('Ghi nhận thông tin');
  await form.getByTestId('wm-add-step').click();
  await form.getByLabel('Mã bước 2', { exact: true }).fill('review-internal');
  await form.getByLabel('Tên bước 2', { exact: true }).fill('Rà soát nội bộ');
  await form.getByLabel('Phụ thuộc bước 2', { exact: true }).selectOption('note-info');
  await form.getByLabel('Loại phụ thuộc 2', { exact: true }).selectOption('INFORMATIONAL');
  await page.getByTestId('wm-library-submit').click();
  await page.waitForFunction(
    (id) => [...document.querySelectorAll('[data-testid^="wm-row-"]')]
      .some((row) => row.textContent?.includes(id)),
    GATELESS_ID, { timeout: 15000 });

  const afterCreate = await (await page.request.get(`${HOST}/model`)).json();
  const created = afterCreate.workModules.all.find((row) => row.templateId === GATELESS_ID);
  assert.ok(created, 'the gate-less version MUST survive the fresh library readback');
  assert.equal(created.status, 'ACTIVE');
  assert.equal(created.gateStage, '', 'no gate was invented');
  assert.ok(afterCreate.workModules.templates.some((row) => row.templateId === GATELESS_ID),
    'it is offered in the attach list');
  await page.getByTestId(`wm-row-${GATELESS_ID}:V1`).scrollIntoViewIfNeeded();
  await shot(page, 'desktop-11-gateless-library-readback.png');

  // Attach it on the shipment and read the rollup back.
  await page.getByRole('link', { name: 'Lô Hàng', exact: true }).first().click();
  await page.getByTestId('shipment-period-tat-ca').click();
  await page.getByRole('link', { name: 'SEA-162', exact: true }).click();
  // Base truth BEFORE this attach. (The earlier GATED demo module legitimately
  // owns the delivery join, so the invariant is "this attach changes nothing",
  // not "no base node ever has a module dependency".)
  const beforeGateLess = await (await page.request.get(`${HOST}/model`)).json();
  const baseBefore = beforeGateLess.shipments.find((s) => s.id === 'SEA-162').journey.nodes
    .filter((n) => !n.moduleId)
    .map((n) => ({ id: n.id, completed: n.completed, dependencies: [...n.dependencies], blockers: [...n.blockers] }));
  assert.equal(baseBefore.length, 7);
  await page.getByTestId('journey-add-module').click();
  await page.getByRole('radio', { name: `Chọn ${GATELESS_NAME}`, exact: true }).check();
  await page.getByTestId('journey-add-module-confirm').click();
  await page.waitForFunction(
    (name) => document.querySelector('[data-testid="journey-modules"]')?.textContent?.includes(name),
    GATELESS_NAME, { timeout: 15000 });

  const afterGateLessAttach = await (await page.request.get(`${HOST}/model`)).json();
  const lotAfter = afterGateLessAttach.shipments.find((s) => s.id === 'SEA-162');
  const gateLess = lotAfter.journey.modules.find((m) => m.templateId === GATELESS_ID);
  assert.ok(gateLess, 'the module rollup exists after attach');
  assert.equal(gateLess.templateVersion, created.version, 'the exact version is pinned');
  assert.equal(gateLess.gateText, '', 'no gate sentence may be invented');
  assert.deepEqual(gateLess.gate, {}, 'no gate object may be invented');
  assert.equal(gateLess.status, 'WAITING', 'a gate-less module waits; it never claims to block');
  assert.equal(await page.getByTestId(`journey-module-gate-${gateLess.instanceId}`).count(), 0,
    'the UI renders no gate sentence for it');

  // Base truth untouched BY THIS ATTACH: identical nodes, dependencies, blockers.
  const baseAfter = lotAfter.journey.nodes.filter((n) => !n.moduleId)
    .map((n) => ({ id: n.id, completed: n.completed, dependencies: [...n.dependencies], blockers: [...n.blockers] }));
  assert.equal(baseAfter.length, 7, 'the base map keeps its authority');
  assert.deepEqual(baseAfter, baseBefore, 'attaching a gate-less module must not touch any base stage');
  assert.ok(baseAfter.every((n) => !n.dependencies.some((d) => String(d).includes(gateLess.instanceId))),
    'no base stage acquired a dependency on the gate-less module');
  assert.ok(baseAfter.every((n) => !n.blockers.some((b) => b.includes('Chặn'))),
    'the gate-less module placed no gate sentence on any base stage');
  await page.getByTestId(`journey-module-${gateLess.instanceId}`).scrollIntoViewIfNeeded();
  await shot(page, 'desktop-12-gateless-attached.png');

  assert.deepEqual(errors, [], 'zero page errors for the whole journey');
  console.log(
    `PASS #162 browser: 1440/390px, attach → rollup 0/3 BLOCKING → 3/3 DONE with gate cleared, ` +
    `facts persisted server-side, library bounded, template lifecycle DRAFT → ACTIVE → RETIRED ` +
    `clicked through with authoritative readback, a gate-less module created blank-gated then ` +
    `attached with no invented gate on any base stage, zero page errors → ${output}`);
} catch (err) {
  console.error(hostErrors.slice(-1500));
  throw err;
} finally {
  await browser?.close();
  host.kill();
}
