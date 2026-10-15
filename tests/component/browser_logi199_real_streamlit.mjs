/**
 * LOGI-199 T0: representative REAL Streamlit v2 + mounted React browser smoke.
 * Isolated GitHub runner only: no MONGO_URI, no Streamlit secrets, AUTH_REQUIRED=false.
 * Evidence is about staging rendering/interaction, NOT production authentication/UAT.
 */
import { spawn } from 'node:child_process';
import { mkdirSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';

const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || 'playwright');
const port = 9519;
const url = 'http://127.0.0.1:' + port;
const output = path.resolve(process.cwd(), 'evidence/logi-199-t0');
mkdirSync(output, { recursive: true });

assert.equal(process.env.AUTH_REQUIRED, 'false', 'isolated runner explicitly disables login only for the staging smoke');
assert.ok(!process.env.MONGO_URI, 'this test must not connect to any real MongoDB');
assert.ok(!process.env.LOGISTICS_PRO_SECRETS_FILE, 'do not provide production secrets to smoke');
const env = {
  ...process.env,
  AUTH_REQUIRED: 'false',
  MONGO_URI: '',
  MONGO_DB_NAME: '',
  STREAMLIT_BROWSER_GATHER_USAGE_STATS: 'false',
};
const host = spawn('python3', [
  '-m', 'streamlit', 'run', 'app.py',
  '--server.port', String(port),
  '--server.address', '127.0.0.1',
  '--server.headless', 'true',
  '--browser.gatherUsageStats', 'false',
], { cwd: process.cwd(), env, stdio: ['ignore', 'pipe', 'pipe'] });
let serverLog = '';
for (const ch of [host.stdout, host.stderr]) {
  ch.on('data', b => { serverLog = (serverLog + b.toString()).slice(-12000); });
}
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

async function serverReady() {
  for (let i = 0; i < 300; i++) {
    if (host.exitCode !== null) throw Error('Streamlit died before browser boot: ' + serverLog.slice(-1200));
    try {
      const response = await fetch(url + '/_stcore/health');
      if (response.ok) return;
    } catch {}
    await sleep(150);
  }
  throw Error('Streamlit health endpoint not ready: ' + serverLog.slice(-1500));
}
async function getViewportMetrics(page, label) {
  return page.evaluate(label => {
    const shell = [...document.querySelectorAll('*')].filter(el => el.shadowRoot).flatMap(el => [...el.shadowRoot.querySelectorAll('.logi-shell')])[0] || null;
    return {
      label,
      width: window.innerWidth,
      height: window.innerHeight,
      documentOverflowPx: Math.max(0, document.documentElement.scrollWidth - window.innerWidth),
      streamlitApp: !!document.querySelector('[data-testid="stApp"]'),
      hasShadowShellAtTopLevel: !!shell,
    };
  }, label);
}
async function getShellMetrics(page) {
  return page.locator('.logi-shell').first().evaluate(el => {
    const css = getComputedStyle(el);
    return {
      font: css.fontFamily,
      ink: css.color,
      background: css.backgroundColor,
      overflowPx: Math.max(0, el.scrollWidth - el.clientWidth),
      clientWidth: el.clientWidth,
    };
  });
}
let browser;
const results = { runtime: 'REAL_STREAMLIT_COMPONENTS_V2', app: 'app.py', mode: 'isolated-mongomock-no-production-db', commit: process.env.GITHUB_SHA || '', checks: [] };
try {
  await serverReady();
  browser = await chromium.launch({ headless: true, args: ['--no-sandbox', '--disable-dev-shm-usage'] });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 });
  const errors = [];
  page.on('pageerror', err => errors.push(err.message));
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 45000 });
  await page.locator('.logi-shell').first().waitFor({ state: 'visible', timeout: 90000 });
  assert.ok(await page.locator('[data-testid="stApp"]').count(), 'real Streamlit app wrapper must exist');
  const desk = await getShellMetrics(page);
  assert.match(desk.font, /Be Vietnam Pro/, 'app-wide font missing from actual mounted shell');
  assert.equal(desk.ink, 'rgb(16, 38, 60)', 'actual app shell ink differs from approved palette');
  assert.equal(desk.background, 'rgb(237, 241, 245)', 'actual app shell background differs from approved palette');
  const home = await getViewportMetrics(page, 'desktop-home');
  home.shell = desk;
  assert.ok(home.documentOverflowPx <= 1 && desk.overflowPx <= 1, 'desktop home overflow');
  results.checks.push(home);
  await page.screenshot({ path: path.join(output, 'desktop-home.png'), fullPage: false });

  await page.locator('a[href="/lo-hang"]').first().click({ timeout: 15000 });
  const allPeriods = page.getByTestId('shipment-period-tat-ca');
  if (await allPeriods.count()) await allPeriods.first().click();
  // Streamlit may deliver a fresh view model during filter updates; a locator
  // click can wait forever for layout stability while React replaces the card.
  // Dispatch a normal DOM click into the current canonical shipment link
  // instead; the app's real React Router handler owns the navigation.
  await page.locator('a[href="/lo-hang/LO-0306"]').first().waitFor({ state: 'attached', timeout: 25000 });
  await page.locator('a[href="/lo-hang/LO-0306"]').first().dispatchEvent('click');
  await page.getByTestId('shipment-journey').waitFor({ state: 'visible', timeout: 45000 });

  const journey = await page.getByTestId('shipment-journey').evaluate(el => ({
    font: getComputedStyle(el).fontFamily,
    testid: el.getAttribute('data-testid'),
    text: (el.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 450),
  }));
  assert.match(journey.font, /Be Vietnam Pro/, 'Journey has not inherited new Vietnamese font');
  assert.ok(journey.text.length > 25, 'Journey did not receive populated business text');
  const detail = await getViewportMetrics(page, 'desktop-journey');
  detail.shell = await getShellMetrics(page);
  detail.journey = journey;
  assert.ok(detail.documentOverflowPx <= 1 && detail.shell.overflowPx <= 1, 'desktop shipment horizontal overflow');
  results.checks.push(detail);
  await page.screenshot({ path: path.join(output, 'desktop-journey.png'), fullPage: false });

  const mapToggle = page.getByTestId('journey-detail-map-toggle');
  assert.equal(await mapToggle.getAttribute('aria-expanded'), 'false');
  await mapToggle.click();
  await page.getByTestId('journey-map-viewport').waitFor({ state: 'visible' });
  assert.equal(await mapToggle.getAttribute('aria-expanded'), 'true');
  const nodes = page.locator('[data-testid^="journey-node-"]');
  results.nodeCount = await nodes.count();
  assert.ok(results.nodeCount >= 2, 'detailed map must contain actual LO-0306 nodes');
  const selectedNode = nodes.nth(1);
  const selectedId = await selectedNode.getAttribute('data-testid');
  await selectedNode.click({ timeout: 15000 });
  await page.locator('[data-testid="' + selectedId + '"][aria-pressed="true"]').waitFor({ state: 'attached' });
  await page.getByTestId('journey-quick-panel').waitFor({ state: 'visible' });
  results.checks.push({ label: 'journey-detail-map-node', clicked: selectedId, count: results.nodeCount });
  await page.screenshot({ path: path.join(output, 'desktop-journey-node-open.png'), fullPage: false });
  await mapToggle.click();
  await page.getByTestId('journey-compact-overview').waitFor({ state: 'visible' });

  await page.setViewportSize({ width: 390, height: 844 });
  await page.waitForTimeout(250);
  const mobile = await getViewportMetrics(page, 'mobile-journey');
  mobile.shell = await getShellMetrics(page);
  const journeyMobile = await page.getByTestId('shipment-journey').isVisible();
  mobile.journeyVisible = journeyMobile;
  assert.equal(journeyMobile, true, 'Journey not visible on mobile');
  assert.ok(mobile.documentOverflowPx <= 1 && mobile.shell.overflowPx <= 1, 'mobile shipment horizontal overflow');
  assert.match(mobile.shell.font, /Be Vietnam Pro/, 'mobile font drift');
  const mobileIdentity = await page.getByTestId('shipment-identity-bar').evaluate(card => {
    const info = card.querySelector('[data-testid="shipment-identity-info"]');
    const title = card.querySelector('[data-testid="shipment-identity-title"]');
    const customer = card.querySelector('[data-testid="shipment-identity-customer"]');
    const actions = card.querySelector('[data-testid="shipment-identity-actions"]');
    if (!info || !title || !customer || !actions) return null;
    return {
      title: title.textContent || '', customer: customer.textContent || '',
      noOverlap: info.getBoundingClientRect().bottom <= actions.getBoundingClientRect().top + 1,
      titleOverflow: title.scrollWidth - title.clientWidth,
      actionsOverflow: actions.scrollWidth - actions.clientWidth,
      headerOverflow: card.scrollWidth - card.clientWidth,
      customerEllipsized: getComputedStyle(customer.parentElement).textOverflow === 'ellipsis',
    };
  });
  assert.ok(mobileIdentity, 'mobile shipment identity DOM missing');
  assert.match(mobileIdentity.title, /LO-0306/);
  assert.equal(mobileIdentity.noOverlap, true, 'mobile identity and actions overlap');
  assert.ok(mobileIdentity.titleOverflow <= 1 && mobileIdentity.actionsOverflow <= 1 && mobileIdentity.headerOverflow <= 1,
    'mobile identity title/actions content is clipped');
  assert.equal(mobileIdentity.customerEllipsized, false, 'mobile customer is truncated');
  mobile.identityReadability = mobileIdentity;
  results.checks.push(mobile);
  await page.screenshot({ path: path.join(output, 'mobile-journey.png'), fullPage: false });
  assert.deepEqual(errors, [], 'browser JavaScript page errors: ' + errors.join(' | '));
  results.verdict = 'RUNTIME_SMOKE_PASS';
  console.log('RUNTIME_BROWSER=PASS desktop 1440x900 + mobile 390x844; Streamlit mounted; Journey text/fonts; no page/shell overflow');
} catch (err) {
  results.verdict = 'RUNTIME_SMOKE_FAIL';
  results.failure = String(err && err.stack || err);
  results.serverLogTail = serverLog.slice(-1300);
  console.error(results.failure);
  throw err;
} finally {
  try { writeFileSync(path.join(output, 'browser_metrics.json'), JSON.stringify(results, null, 2)); } catch {}
  if (browser) await browser.close();
  host.kill('SIGTERM');
}
