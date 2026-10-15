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
const ROUTES = ['/', '/viec-can-xu-ly', '/dieu-hanh', '/lo-hang', '/lo-hang/T6-FCL', '/tao-lo-moi', '/khach-hang', '/ngu-canh-doi-tac',
  '/kinh-doanh-bao-gia', '/hop-dong', '/tai-chinh/thu-tien', '/tai-chinh/cong-no-doi-tac', '/tai-chinh/doi-soat', '/bao-cao-ceo',
  '/tra-cuu-thue', '/tra-cuu-chinh-sach', '/thanh-toan-quoc-te', '/dich-thuat', '/so-tay', '/bieu-mau', '/quy-trinh', '/theo-doi',
  '/thoa-thuan-ban-giao', '/nguoi-dung'];
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
  return { docOverflow: Math.max(0, document.documentElement.scrollWidth - innerWidth),
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
    for (const route of ROUTES) {
      await page.evaluate(r => { history.pushState({}, '', r); dispatchEvent(new PopStateEvent('popstate')); }, route);
      await sleep(1200);
      const m = await measure(page);
      (results.routes[route] ||= {})[label] = m;
      const name = `${label}${route.replace(/\//g, '_') || '_home'}.png`;
      await page.screenshot({ path: path.join(output, name) });
      if (label === 'mobile' && m.docOverflow > 1) failures.push(`${route} mobile overflow ${m.docOverflow}px`);
    }
    if (errors.length) failures.push(`${label} page errors: ${errors.join(' | ')}`);
    await page.close();
  }
  results.failures = failures;
  results.verdict = failures.length ? 'T5_AUDIT_FAIL' : 'T5_AUDIT_PASS_WITH_FINDINGS';
  console.log(results.verdict, JSON.stringify(failures));
  if (failures.length) process.exitCode = 1;
} catch (e) { results.verdict = 'T5_AUDIT_ERROR'; results.error = String(e.stack || e); console.error(results.error); process.exitCode = 1; }
finally {
  writeFileSync(path.join(output, 'route_audit.json'), JSON.stringify(results, null, 2));
  if (browser) await browser.close(); host.kill('SIGTERM');
}
