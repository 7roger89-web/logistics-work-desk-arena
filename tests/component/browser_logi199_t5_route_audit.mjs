/**
 * LOGI-199 T5 — app-wide visual audit on the REAL Streamlit staging app
 * (same isolated launcher as T6). For every current route at 1440x900 and
 * 390x844 it records: page/shell horizontal overflow, the mounted UI font,
 * whether IBM Plex Mono is available for codes, and visible body text smaller
 * than 12px (GOAL #199 inv. 8). It FAILS only on horizontal page overflow at
 * 390px or a JavaScript page error; small-text counts are reported as findings.
 */
import { spawn } from 'node:child_process';
import { mkdirSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';

const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || 'playwright');
const port = 9523, url = 'http://127.0.0.1:' + port;
const output = path.resolve(process.cwd(), 'evidence/logi-199-t5');
mkdirSync(output, { recursive: true });
assert.ok(!process.env.MONGO_URI);
// Legacy paths that App.tsx deliberately redirects (Navigate replace). They are
// NOT screens: asserted at source by tests/test_logi199_t5_redirects.py and
// excluded from distinct-surface coverage here.
const REDIRECTS = { '/viec-can-xu-ly': '/lo-hang', '/theo-doi': '/lo-hang', '/thoa-thuan-ban-giao': '/kinh-doanh-bao-gia' };
const ROUTES = ['/', '/dieu-hanh', '/lo-hang', '/lo-hang/T6-FCL', '/tao-lo-moi', '/khach-hang', '/ngu-canh-doi-tac',
  '/kinh-doanh-bao-gia', '/hop-dong', '/tai-chinh/thu-tien', '/tai-chinh/cong-no-doi-tac', '/tai-chinh/doi-soat', '/bao-cao-ceo',
  '/tra-cuu-thue', '/tra-cuu-chinh-sach', '/thanh-toan-quoc-te', '/dich-thuat', '/so-tay', '/bieu-mau', '/quy-trinh', '/nguoi-dung'];
const host = spawn('python3', ['-m', 'streamlit', 'run', 'scripts/logi199_t6_staging_app.py', '--server.port', String(port),
  '--server.address', '127.0.0.1', '--server.headless', 'true', '--browser.gatherUsageStats', 'false'],
{ cwd: process.cwd(), env: { ...process.env, AUTH_REQUIRED: 'false', MONGO_URI: '', MONGO_DB_NAME: '' }, stdio: ['ignore', 'pipe', 'pipe'] });
let log = ''; for (const ch of [host.stdout, host.stderr]) ch.on('data', b => { log = (log + b).slice(-8000); });
const sleep = ms => new Promise(r => setTimeout(r, ms));
for (let i = 0; i < 300; i++) { try { if ((await fetch(url + '/_stcore/health')).ok) break; } catch {} await sleep(150); }

const measure = page => page.evaluate(() => {
  const roots = [document, ...[...document.querySelectorAll('*')].filter(e => e.shadowRoot).map(e => e.shadowRoot)];
  const shell = roots.map(r => r.querySelector('.logi-shell')).find(Boolean);
  const small = []; let monoUsed = 0;
  for (const r of roots) for (const el of r.querySelectorAll('p,span,td,th,li,a,button,label,div,dd,dt,h1,h2,h3,h4')) {
    const own = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim().length > 1);
    if (!own) continue;
    const rect = el.getBoundingClientRect(); if (!rect.width || !rect.height || rect.bottom < 0 || rect.top > innerHeight) continue;
    const cs = getComputedStyle(el); const size = parseFloat(cs.fontSize);
    if (/Plex Mono/.test(cs.fontFamily)) monoUsed++;
    if (size < 12 && !el.closest('[data-testid="journey-map-transform"]')) small.push(`${size}px:${el.textContent.trim().slice(0, 40)}`);
  }
  // Interactive controls must be readable/tappable: a control whose box leaves
  // the viewport or the shell is CLIPPED unless an ancestor is a real,
  // visibly scrollable region (overflow-x auto/scroll with a scrollbar).
  const vw = innerWidth, shellRect = shell ? shell.getBoundingClientRect() : { left: 0, right: vw };
  const clipped = [];
  for (const r of roots) for (const el of r.querySelectorAll('button,a,[role="tab"],input,select,textarea')) {
    const b = el.getBoundingClientRect(); if (b.width < 2 || b.height < 2 || b.bottom < 0 || b.top > innerHeight) continue; // sr-only skip links
    let fixed = false; for (let q = el; q && q.nodeType === 1; q = q.parentElement) if (getComputedStyle(q).position === 'fixed') { fixed = true; break; }
    const cs = getComputedStyle(el); if (cs.visibility === 'hidden' || cs.display === 'none') continue;
    if (el.closest('[data-testid="journey-map-transform"],[data-testid="journey-map-viewport"]')) continue; // pan/zoom canvas
    // Fixed bars (bottom tab bar) are bounded by the viewport; everything else by the shell.
    const right = fixed ? vw : Math.min(vw, shellRect.right), left = fixed ? 0 : Math.max(0, shellRect.left);
    const outside = b.right > right + 1 || b.left < left - 1;
    if (!outside) continue;
    let scroller = null;
    for (let p = el.parentElement; p; p = p.parentElement || (p.getRootNode && p.getRootNode().host) || null) {
      const ox = getComputedStyle(p).overflowX;
      if ((ox === 'auto' || ox === 'scroll') && p.scrollWidth > p.clientWidth + 1 && !/no-scrollbar/.test(p.className || '')) { scroller = p; break; }
      if (p === shell) break;
    }
    if (!scroller) clipped.push(`${Math.round(b.left)}..${Math.round(b.right)}:${(el.textContent || el.getAttribute('aria-label') || el.tagName).trim().slice(0, 30)}`);
  }
  return { clippedControls: clipped.slice(0, 8), clippedCount: clipped.length, docOverflow: Math.max(0, document.documentElement.scrollWidth - innerWidth),
    shellOverflow: shell ? Math.max(0, shell.scrollWidth - shell.clientWidth) : null,
    font: shell ? getComputedStyle(shell).fontFamily.split(',')[0] : '', monoUsed, smallCount: small.length, smallSample: small.slice(0, 6) };
});
const results = { commit: process.env.GITHUB_SHA || '', routes: {} };
let browser, failures = [];
try {
  browser = await chromium.launch({ headless: true, args: ['--no-sandbox', '--disable-dev-shm-usage'] });
  for (const [label, vp] of [['desktop', { width: 1440, height: 900 }], ['mobile', { width: 390, height: 844 }]]) {
    const page = await browser.newPage({ viewport: vp }); const errors = []; page.on('pageerror', e => errors.push(e.message));
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 45000 });
    await page.locator('.logi-shell').first().waitFor({ state: 'visible', timeout: 90000 });
    let previousDigest = null;
    for (const route of ROUTES) {
      // The app uses MemoryRouter: navigate through the app's own router links
      // (a real DOM click on <a href=route>), exactly what a user tap triggers.
      let reached = false;
      if (route === '/lo-hang/T6-FCL') {
        const list = page.locator('a[href="/lo-hang"]').first();
        if (await list.count()) { await list.dispatchEvent('click'); await sleep(800);
          const all = page.getByTestId('shipment-period-tat-ca').first(); if (await all.count()) { await all.dispatchEvent('click'); await sleep(500); } }
      }
      const link = page.locator(`a[href="${route}"]`).first();
      if (await link.count()) { await link.dispatchEvent('click'); reached = true; }
      await sleep(1200);
      const m = await measure(page);
      m.reachedViaAppLink = reached;
      m.textDigest = await page.evaluate(() => { const r = [...document.querySelectorAll('*')].find(e => e.shadowRoot)?.shadowRoot; return (r?.querySelector('main')?.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 80); });
      (results.routes[route] ||= {})[label] = m;
      const name = `${label}${route.replace(/\//g, '_') || '_home'}.png`;
      await page.screenshot({ path: path.join(output, name) });
      if (!reached) failures.push(`${label} ${route}: not reached through an app link`);
      if (m.docOverflow > 1) failures.push(`${label} ${route}: page overflow ${m.docOverflow}px`);
      if ((m.shellOverflow || 0) > 1) failures.push(`${label} ${route}: shell overflow ${m.shellOverflow}px`);
      if (m.clippedCount) failures.push(`${label} ${route}: clipped controls ${m.clippedControls.join(' | ')}`);
      if (previousDigest !== null && m.textDigest === previousDigest && route !== '/lo-hang/T6-FCL') failures.push(`${label} ${route}: content did not change (route not rendered)`);
      previousDigest = m.textDigest;
    }
    if (errors.length) failures.push(`${label} page errors: ${errors.join(' | ')}`);
    await page.close();
  }
  results.failures = failures;
  results.redirects = REDIRECTS;
  results.distinctSurfaces = ROUTES.length;
  results.verdict = failures.length ? 'T5_AUDIT_FAIL' : 'T5_AUDIT_PASS';
  console.log(results.verdict, JSON.stringify(failures));
  if (failures.length) process.exitCode = 1;
} catch (e) { results.verdict = 'T5_AUDIT_ERROR'; results.error = String(e.stack || e); console.error(results.error); process.exitCode = 1; }
finally {
  writeFileSync(path.join(output, 'route_audit.json'), JSON.stringify(results, null, 2));
  if (browser) await browser.close(); host.kill('SIGTERM');
}
