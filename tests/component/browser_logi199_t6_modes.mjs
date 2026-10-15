/**
 * LOGI-199 T6 — REAL Streamlit v2 + official component/dist, isolated staging.
 * Launches scripts/logi199_t6_staging_app.py (sandbox mongomock, no MONGO_URI,
 * no secrets, AUTH_REQUIRED=false) and verifies SEA FCL / SEA LCL / AIR / ROAD LTL
 * journeys show mode-correct nodes, plus ONE real write -> readback through the UI
 * (FCL on-board evidence). Desktop 1440x900 and mobile 390x844 screenshots.
 * This is staging evidence, NOT production UAT.
 */
import { spawn } from 'node:child_process';
import { mkdirSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';

const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || 'playwright');
const port = 9521;
const url = 'http://127.0.0.1:' + port;
const output = path.resolve(process.cwd(), 'evidence/logi-199-t6');
mkdirSync(output, { recursive: true });
assert.equal(process.env.AUTH_REQUIRED, 'false');
assert.ok(!process.env.MONGO_URI, 'must not connect to a real MongoDB');

const host = spawn('python3', ['-m', 'streamlit', 'run', 'scripts/logi199_t6_staging_app.py', '--server.port', String(port),
  '--server.address', '127.0.0.1', '--server.headless', 'true', '--browser.gatherUsageStats', 'false'],
{ cwd: process.cwd(), env: { ...process.env, AUTH_REQUIRED: 'false', MONGO_URI: '', MONGO_DB_NAME: '' }, stdio: ['ignore', 'pipe', 'pipe'] });
let serverLog = '';
for (const ch of [host.stdout, host.stderr]) ch.on('data', b => { serverLog = (serverLog + b.toString()).slice(-12000); });
const sleep = ms => new Promise(r => setTimeout(r, ms));
async function ready() {
  for (let i = 0; i < 300; i++) {
    if (host.exitCode !== null) throw Error('Streamlit died: ' + serverLog.slice(-1500));
    try { if ((await fetch(url + '/_stcore/health')).ok) return; } catch {}
    await sleep(150);
  }
  throw Error('Streamlit not ready: ' + serverLog.slice(-1500));
}
const overflow = page => page.evaluate(() => Math.max(0, document.documentElement.scrollWidth - window.innerWidth));

const EXPECT = {
  'T6-FCL': { present: ['booking', 'customs-export', 'si-vgm', 'gate-in', 'on-board', 'arrival', 'delivery'], absent: ['cfs-receipt', 'uplift', 'road-ltl'] },
  'T6-LCL': { present: ['booking', 'si-vgm', 'cfs-receipt', 'delivery'], absent: ['gate-in', 'uplift', 'road-ltl'] },
  'T6-AIR': { present: ['air-booking', 'air-acceptance', 'uplift', 'air-arrival', 'delivery'], absent: ['booking', 'si-vgm', 'gate-in', 'on-board', 'cfs-receipt'] },
  'T6-ROAD-FTL': { present: ['road-vehicle', 'delivery'], absent: ['road-ltl', 'booking', 'si-vgm', 'gate-in', 'uplift', 'road-border'] },
  'T6-AIR-CONSOLIDATED': { present: ['air-booking', 'air-acceptance', 'uplift', 'air-arrival', 'delivery'], absent: ['booking', 'si-vgm', 'gate-in', 'on-board', 'cfs-receipt'] },
  'T6-ROAD-LTL': { present: ['road-ltl', 'delivery'], absent: ['booking', 'si-vgm', 'gate-in', 'uplift', 'customs-export', 'customs-import', 'road-border'] },
};

let browser;
const results = { runtime: 'REAL_STREAMLIT_COMPONENTS_V2', launcher: 'scripts/logi199_t6_staging_app.py', commit: process.env.GITHUB_SHA || '', lots: {}, checks: [] };
try {
  await ready();
  browser = await chromium.launch({ executablePath: process.env.CHROMIUM_EXECUTABLE || undefined, headless: true, args: ['--no-sandbox', '--disable-dev-shm-usage'] });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  const errors = []; page.on('pageerror', e => errors.push(e.message));
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 45000 });
  await page.locator('.logi-shell').first().waitFor({ state: 'visible', timeout: 90000 });

  async function openLot(id) {
    // The shell nav can be collapsed/hidden on detail pages; dispatch a real DOM
    // click to the router link (same handler a user tap reaches).
    const nav = page.locator('a[href="/lo-hang"]').first();
    await nav.waitFor({ state: 'attached', timeout: 15000 }); await nav.dispatchEvent('click');
    const all = page.getByTestId('shipment-period-tat-ca').first();
    await all.waitFor({ state: 'visible', timeout: 30000 }); await all.click();
    const link = page.locator(`a[href="/lo-hang/${id}"]`).first();
    await link.waitFor({ state: 'attached', timeout: 25000 }); await link.dispatchEvent('click');
    await page.getByTestId('shipment-journey').waitFor({ state: 'visible', timeout: 45000 });
    const toggle = page.getByTestId('journey-detail-map-toggle');
    if (await toggle.count() && (await toggle.getAttribute('aria-expanded')) === 'false') await toggle.click();
    await page.getByTestId('journey-map-viewport').waitFor({ state: 'visible', timeout: 20000 });
  }
  const nodeIds = () => page.locator('[data-testid="journey-map-viewport"] [data-testid^="journey-node-"]').evaluateAll(els => els.map(e => e.getAttribute('data-testid').replace('journey-node-', '')));

  for (const [id, want] of Object.entries(EXPECT)) {
    await openLot(id);
    const ids = await nodeIds();
    for (const n of want.present) assert.ok(ids.includes(n), `${id}: expected node ${n}; got ${ids.join(',')}`);
    for (const n of want.absent) assert.ok(!ids.includes(n), `${id}: node ${n} must not appear; got ${ids.join(',')}`);
    results.lots[id] = { nodes: ids, overflowPx: await overflow(page) };
    assert.ok(results.lots[id].overflowPx <= 1, `${id}: desktop overflow`);
    await page.screenshot({ path: path.join(output, `desktop-${id}.png`) });
  }

  async function mapComparison(label) {
    await openLot('T6-FCL');
    const viewport = page.getByTestId('journey-map-viewport');
    await viewport.scrollIntoViewIfNeeded();
    await viewport.evaluate(el => {
      const shell = el.closest('.logi-shell');
      shell.scrollTop += el.getBoundingClientRect().top - (innerWidth < 1100 ? 106 : 70);
    });
    await page.getByRole('button', { name: '↺ Đọc rõ', exact: true }).click();
    const transform = page.getByTestId('journey-map-transform');
    const initial = await transform.getAttribute('style');
    assert.equal(await page.getByTestId('journey-zoom-level').innerText(), '100%');
    const typography = await transform.locator('button').first().evaluate(el => {
      const title = el.querySelector('.font-extrabold');
      return { scale: new DOMMatrix(getComputedStyle(el.parentElement).transform).a, titlePx: parseFloat(getComputedStyle(title).fontSize) };
    });
    assert.ok(typography.scale * typography.titlePx >= 14, 'default node labels must be readable, not just overflow-free');
    await page.screenshot({ path: path.join(output, `${label}-map-B-readable.png`) });
    // Real drag must move the canvas without selecting a node (pointer events).
    const b = await viewport.boundingBox();
    await page.mouse.move(b.x + 20, b.y + b.height * 0.65);
    await page.mouse.down(); await page.mouse.move(b.x + 90, b.y + b.height * 0.65 + 30, { steps: 8 }); await page.mouse.up();
    assert.notEqual(await transform.getAttribute('style'), initial, 'pan must change transform');
    await page.getByRole('button', { name: '⤢ Fit Journey', exact: true }).click();
    const fit = await transform.evaluate(el => {
      const v = el.parentElement.getBoundingClientRect(), c = el.getBoundingClientRect();
      return { scale: new DOMMatrix(getComputedStyle(el).transform).a, inside: c.left >= v.left && c.right <= v.right && c.top >= v.top && c.bottom <= v.bottom };
    });
    assert.ok(fit.scale < 1 && fit.inside, 'Fit must include whole canvas');
    await page.screenshot({ path: path.join(output, `${label}-map-A-fit.png`) });
    await page.getByRole('button', { name: 'Zoom In', exact: true }).click();
    assert.ok(await transform.evaluate(el => new DOMMatrix(getComputedStyle(el).transform).a) > fit.scale);
    await page.getByRole('button', { name: '↺ Đọc rõ', exact: true }).click();
    assert.equal(await page.getByTestId('journey-zoom-level').innerText(), '100%');
    results.checks.push({ label: `${label}-map-fit-readable-pan-zoom`, typography, fit });
  }
  await mapComparison('desktop');
  // T5: extra evidence fields are folded, not removed or made uneditable.
  await openLot('T6-LCL');
  await page.getByRole('button', { name: '⤢ Fit Journey', exact: true }).click();
  await page.getByTestId('journey-node-cfs-receipt').click();
  await page.getByTestId('journey-open-workspace').first().click();
  await page.getByTestId('journey-stage-workspace').getByRole('button', { name: 'Công việc', exact: true }).click();
  const facts = page.getByTestId('sea-export-facts');
  await facts.locator('input,select').first().waitFor({ state: 'visible' });
  const primaryCount = await facts.locator('input:visible,select:visible').count();
  assert.ok(primaryCount >= 1 && primaryCount <= 5);
  const extra = page.getByTestId('fact-fields-secondary');
  await extra.locator('summary').click();
  assert.ok(await extra.locator('input:visible,select:visible').count() > 0);
  assert.equal(await extra.locator('input:disabled,select:disabled').count(), 0);
  results.checks.push({ label: 'popup-primary-fields-and-editable-extras', primaryCount, extraCount: await extra.locator('input,select').count() });
  await page.screenshot({ path: path.join(output, 'desktop-popup-LCL-extra-fields.png') });

  // Real UI write -> canonical writer -> readback: FCL on-board evidence.
  await openLot('T6-FCL');
  const onboard = page.locator('[data-testid="journey-map-viewport"] [data-testid="journey-node-on-board"]');
  assert.notEqual(await onboard.getAttribute('data-state'), 'COMPLETED');
  await page.getByRole('button', { name: '⤢ Fit Journey', exact: true }).click();
  await onboard.click();
  await page.getByTestId('journey-open-workspace').first().click();
  // #198 renames the stage work tab "Thông tin" -> "Công việc"; same panel.
  await page.getByTestId('journey-stage-workspace').getByRole('button', { name: /^(Thông tin|Công việc)$/ }).first().click();
  const input = page.getByLabel('Ngày xếp hàng lên tàu (on-board)', { exact: true });
  await input.waitFor({ state: 'visible', timeout: 15000 });
  await input.fill('2026-10-03');
  await page.getByRole('button', { name: 'Lưu mốc có bằng chứng', exact: true }).click();
  await page.waitForFunction(() => {
    const roots = [document, ...[...document.querySelectorAll('*')].filter(e => e.shadowRoot).map(e => e.shadowRoot)];
    return roots.some(r => r.querySelector('[data-testid="journey-node-on-board"][data-state="COMPLETED"]'));
  }, null, { timeout: 30000 });
  results.checks.push({ label: 'fcl-on-board-write-readback', state: 'COMPLETED' });
  await page.screenshot({ path: path.join(output, 'desktop-T6-FCL-onboard-saved.png') });

  // Mobile 390x844: readable, no horizontal page overflow.
  await page.setViewportSize({ width: 390, height: 844 });
  await sleep(300);
  await mapComparison('mobile');
  for (const id of ['T6-FCL', 'T6-AIR']) {
    await openLot(id);
    const o = await overflow(page);
    results.checks.push({ label: `mobile-${id}`, overflowPx: o });
    assert.ok(o <= 1, `${id}: mobile overflow ${o}px`);
    await page.screenshot({ path: path.join(output, `mobile-${id}.png`) });
  }
  // Navigate away and reopen: a stale local green state cannot satisfy this.
  await openLot('T6-AIR'); await openLot('T6-FCL');
  assert.equal(await onboard.getAttribute('data-state'), 'COMPLETED');
  await page.getByRole('button', { name: '⤢ Fit Journey', exact: true }).click();
  await onboard.click(); await page.getByTestId('journey-open-workspace').first().click();
  await page.getByTestId('journey-stage-workspace').getByRole('button', { name: /^(Thông tin|Công việc)$/ }).first().click();
  assert.equal(await page.getByLabel('Ngày xếp hàng lên tàu (on-board)', { exact: true }).inputValue(), '2026-10-03');
  results.checks.push({ label: 'persisted-on-board-after-reopen', value: '2026-10-03' });
  assert.deepEqual(errors, [], 'page errors: ' + errors.join(' | '));
  results.verdict = 'T6_MODES_STAGING_PASS';
  console.log('T6_BROWSER=PASS FCL/LCL/AIR/ROAD-LTL nodes, FCL on-board write/readback, desktop+mobile no overflow');
} catch (err) {
  results.verdict = 'T6_MODES_STAGING_FAIL';
  results.failure = String(err && err.stack || err);
  results.serverLogTail = serverLog.slice(-1500);
  console.error(results.failure);
  process.exitCode = 1;
} finally {
  try { writeFileSync(path.join(output, 'browser_metrics.json'), JSON.stringify(results, null, 2)); } catch {}
  if (browser) await browser.close();
  host.kill('SIGTERM');
}
