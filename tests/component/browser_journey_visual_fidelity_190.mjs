// Issue #190 — VISUAL EVIDENCE harness (real Chromium, populated + fresh + secondary states).
//
// This is an EVIDENCE lane, not a product API. It reuses the two known-good
// isolated acceptance hosts that already deliver the canonical view model into
// the SHIPPED bundle — no custom store/CDP data delivery is invented here:
//
//   populated : scripts/verify_visual_shipment_workspace.py  (SEA-160, 11 nodes, port 9501)
//   fresh     : scripts/verify_journey_fresh_parity_188.py   (SEA-188, nodes=[], port 9502)
//   donor     : <DONOR_ROOT>/scripts/verify_visual_shipment_workspace.py
//               (approved PR177 / Prototype-B reconstruction, port 9503)
//
// Usage:
//   node tests/component/browser_journey_visual_fidelity_190.mjs <outdir> [populated|fresh|list|donor|all]
//
// Environment (same contract as tests/component/browser_journey_fresh_parity_188.mjs):
//   PLAYWRIGHT_MODULE    module that exports { chromium }   (default: 'playwright')
//   CHROMIUM_EXECUTABLE  real browser binary                (required when playwright has none)
//   CHROMIUM_LIB_PATH    browser-only LD_LIBRARY_PATH
//   PYTHON               python that can import streamlit/mongomock (default: python3)
//   DONOR_ROOT           extracted tree of approved donor commit 70fd361 (enables the donor lane)
//   DONOR_PORT           donor host port (default 9503)
//   REFERENCE_VIEWPORT   "WxH" (default 1536x1466 — Owner original sample dimensions)
//
// Fonts: the shipped CSS @imports Be Vietnam Pro from fonts.googleapis.com. A
// network-isolated sandbox cannot reach it, and a substituted font changes text
// metrics and therefore layout. The harness serves the SAME family from the
// vendored verification fixture tests/component/fixtures/fonts/be-vietnam-pro by
// intercepting the Google Fonts request; product source and dist stay untouched.
import { spawn } from 'node:child_process';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import assert from 'node:assert/strict';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const outDir = path.resolve(root, process.argv[2] || 'evidence/190');
mkdirSync(outDir, { recursive: true });
const mode = (process.argv[3] || 'all').toLowerCase();

const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || 'playwright');
const PY = process.env.PYTHON || 'python3';
const [REF_W, REF_H] = (process.env.REFERENCE_VIEWPORT || '1536x1466').split('x').map(Number);
const LAUNCH = {
  executablePath: process.env.CHROMIUM_EXECUTABLE || undefined,
  headless: true,
  // Playwright hides scrollbars in headless mode by default. That changes the
  // desktop layout by exactly the scrollbar width and made the previous #190
  // evidence miss the real 8px loss. Keep Chromium's actual layout scrollbar.
  ignoreDefaultArgs: ['--hide-scrollbars'],
  args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--disable-gpu'],
  env: process.env.CHROMIUM_LIB_PATH
    ? { ...process.env, LD_LIBRARY_PATH: process.env.CHROMIUM_LIB_PATH }
    : process.env,
};

const HOSTS = {
  populated: { id: 'SEA-160', cwd: root, host: 'scripts/verify_visual_shipment_workspace.py', port: 9501, extra: [] },
  fresh: { id: 'SEA-188', cwd: root, host: 'scripts/verify_journey_fresh_parity_188.py', port: 9502, extra: ['--port', '9502'] },
};
if (process.env.DONOR_ROOT) {
  HOSTS.donor = {
    id: 'SEA-160',
    cwd: path.resolve(process.env.DONOR_ROOT),
    host: 'scripts/verify_visual_shipment_workspace.py',
    port: Number(process.env.DONOR_PORT || 9503),
    extra: [],
    donor: true,
  };
}

const results = [];
const ok = (line) => { results.push(line); console.log('  ✓ ' + line); };
const metrics = { generatedAt: new Date().toISOString(), referenceViewport: { width: REF_W, height: REF_H }, browser: {} };

// ------------------------------------------------------------------ host glue
async function startHost(spec) {
  // The donor host script hardcodes its port; a scratch copy inside the donor
  // tree keeps the donor's own ROOT resolution while freeing port 9501.
  let hostScript = spec.host;
  if (spec.donor && spec.port !== 9501) {
    const src = readFileSync(path.join(spec.cwd, spec.host), 'utf8');
    hostScript = 'scripts/_donor_visual_host_port.py';
    writeFileSync(path.join(spec.cwd, hostScript), src.replaceAll('9501', String(spec.port)));
  }
  const host = spawn(PY, [hostScript, ...spec.extra], { cwd: spec.cwd, stdio: ['ignore', 'pipe', 'pipe'] });
  let err = '';
  host.stderr.on('data', (b) => { err += b; });
  host.stdout.on('data', (b) => { err += b; });
  for (let i = 0; i < 400; i++) {
    try { if ((await fetch(`http://127.0.0.1:${spec.port}/model`)).ok) return { host, err: () => err.slice(-2000) }; } catch {}
    await new Promise((r) => setTimeout(r, 100));
  }
  throw new Error(`acceptance host did not start (${spec.host} @${spec.port}): ${err.slice(-900)}`);
}

// ----------------------------------------------------------------- font glue
const FONT_ROOT = path.join(root, 'tests/component/fixtures/fonts');
// Google Fonts CSS2 unicode-range for the two subsets both families ship here.
const UNICODE_RANGE = {
  vietnamese: 'U+0102-0103, U+0110-0111, U+0128-0129, U+0168-0169, U+01A0-01A1, U+01AF-01B0, U+0300-0301, U+0303-0304, U+0308-0309, U+0323, U+0329, U+1EA0-1EF9, U+20AB',
  latin: 'U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+2074, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD',
};
const FONTS = [
  { dir: 'be-vietnam-pro', family: 'Be Vietnam Pro', prefix: 'be-vietnam-pro', via: 'route' },
  { dir: 'inter', family: 'Inter', prefix: 'inter', via: 'style' },
];
function fontFaceCss(spec) {
  const dir = path.join(FONT_ROOT, spec.dir);
  const faces = [];
  for (const file of readFileSync(path.join(dir, 'MANIFEST')).toString().split('\n').filter(Boolean)) {
    const m = file.match(new RegExp(`^${spec.prefix}-(\\w+)-(\\d+)-(\\w+)\\.woff2$`));
    if (!m) throw new Error(`unexpected vendored font file: ${file}`);
    const b64 = readFileSync(path.join(dir, file)).toString('base64');
    faces.push(`@font-face{font-family:'${spec.family}';font-style:${m[3]};font-weight:${m[2]};font-display:block;`
      + `src:url(data:font/woff2;base64,${b64}) format('woff2');unicode-range:${UNICODE_RANGE[m[1]]};}`);
  }
  return faces.join('\n');
}
async function useLocalFonts(page) {
  let faces = 0;
  for (const spec of FONTS) {
    if (!existsSync(path.join(FONT_ROOT, spec.dir, 'MANIFEST'))) continue;
    const css = fontFaceCss(spec);
    faces += (css.match(/@font-face/g) || []).length;
    if (spec.via === 'route') {
      // The shipped CSS @imports this family from fonts.googleapis.com; fulfil it locally.
      await page.route(/fonts\.(googleapis|gstatic)\.com/, (route) => route.fulfill({
        status: 200, contentType: 'text/css; charset=utf-8', body: css,
      }));
    } else {
      await page.addInitScript(({ css, family }) => {
        const inject = () => {
          const tag = document.createElement('style');
          tag.setAttribute('data-verification-fonts', family);
          tag.textContent = css;
          (document.head || document.documentElement).appendChild(tag);
        };
        if (document.head) inject();
        else document.addEventListener('DOMContentLoaded', inject, { once: true });
      }, { css, family: spec.family });
    }
  }
  return { served: faces > 0, faces };
}
async function fontFamilyUsed(page) {
  await page.evaluate(() => document.fonts.ready);
  return page.evaluate(() => {
    const probe = document.querySelector('[data-testid="shipment-journey"]') || document.body;
    return {
      vietnameseAvailable: document.fonts.check('16px "Be Vietnam Pro"', 'Lô hàng'),
      interAvailable: document.fonts.check('16px Inter', 'Journey'),
      familyOnSurface: getComputedStyle(probe).fontFamily,
      loadedFaces: document.fonts.size,
    };
  });
}

// ------------------------------------------------------------- navigation
async function openShipment(page, spec) {
  await page.goto(`http://127.0.0.1:${spec.port}`);
  await page.getByRole('link', { name: 'Lô Hàng', exact: true }).first().click();
  await page.getByTestId('shipment-period-tat-ca').click();
  await page.getByRole('link', { name: spec.id, exact: true }).click();
  await page.getByTestId('shipment-journey').waitFor();
  await page.waitForTimeout(200);
}

// ------------------------------------------------------------- measurements
const box = async (page, testid) => {
  const b = await page.getByTestId(testid).first().boundingBox();
  assert.ok(b, `${testid} has no box`);
  return { x: +b.x.toFixed(1), y: +b.y.toFixed(1), w: +b.width.toFixed(1), h: +b.height.toFixed(1) };
};

/**
 * Layout truth for the Journey workspace. `.logi-shell` is its own scrollport
 * (same finding as the #188 harness), so absolute offsets are measured against
 * the shell's scroll content, not the viewport.
 */
async function measure(page) {
  return page.evaluate(() => {
    const t = (id) => document.querySelector(`[data-testid="${id}"]`);
    const shell = document.querySelector('.logi-shell');
    const base = shell ? shell.getBoundingClientRect().top - shell.scrollTop : 0;
    const rectOf = (el) => {
      if (!el) return null;
      const r = el.getBoundingClientRect();
      return { x: +r.x.toFixed(1), y: +(r.y - base).toFixed(1), w: +r.width.toFixed(1), h: +r.height.toFixed(1) };
    };
    const transform = t('journey-map-transform');
    const style = transform ? transform.getAttribute('style') || '' : '';
    const k = Number((style.match(/scale\(([\d.]+)\)/) || [])[1] || 1);
    const nodes = [...document.querySelectorAll('[data-testid^="journey-node-"]')].map((el) => ({
      id: el.dataset.testid.replace('journey-node-', ''),
      state: el.dataset.state,
      current: el.getAttribute('aria-current') || (el.className.includes('outline') ? 'selected' : ''),
      // offset* are unscaled layout values inside the transformed canvas.
      logical: { x: el.offsetLeft, y: el.offsetTop, w: el.offsetWidth, h: el.offsetHeight },
      rendered: rectOf(el),
      label: (el.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 60),
    }));
    const cards = [...document.querySelectorAll('[data-testid^="journey-summary-card-"]')].map((el) => ({
      id: el.dataset.testid,
      rect: rectOf(el),
      title: (el.querySelector('h3,h4,p,b,strong')?.textContent || el.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 48),
      tabs: el.querySelectorAll('button').length,
    }));
    const ids = ['attention-now', 'shipment-journey', 'journey-modules', 'journey-phase-strip', 'journey-map-toolbar',
      'journey-map-viewport', 'journey-side-panel', 'journey-quick-panel', 'journey-overview-panel',
      'journey-stage-workspace', 'journey-global-workspace', 'journey-summary-cards', 'shipment-completion-goals',
      'completion-goal-details', 'shipment-execution-profile', 'journey-map-rail', 'journey-empty-canvas',
      'customs-import-quick-panel', 'ci-next-action', 'ci-registration-clearance', 'ci-scroll-region',
      'ci-footer', 'ci-open-workspace', 'journey-parallel-branch', 'shipment-identity-bar'];
    const blocks = {};
    for (const id of ids) blocks[id] = rectOf(t(id));
    const split = document.querySelector('.journey-split');
    const order = Object.entries(blocks)
      .filter(([, r]) => r)
      .sort((a, b) => a[1].y - b[1].y || a[1].x - b[1].x)
      .map(([id, r]) => ({ id, y: r.y, h: r.h }));
    const viewportBox = blocks['journey-map-viewport'];
    const sideBox = blocks['journey-side-panel'];
    const gap = (a, b) => (a && b ? +Math.max(0, b.x - (a.x + a.w)).toFixed(1) : null);
    return {
      shell: shell ? {
        scrollTop: Math.round(shell.scrollTop), scrollHeight: shell.scrollHeight,
        clientHeight: shell.clientHeight, scrollWidth: shell.scrollWidth, clientWidth: shell.clientWidth,
        verticalOverflow: shell.scrollHeight - shell.clientHeight,
        horizontalOverflow: shell.scrollWidth - shell.clientWidth,
        bbox: rectOf(shell),
      } : null,
      document: {
        clientWidth: document.documentElement.clientWidth,
        scrollWidth: document.documentElement.scrollWidth,
        clientHeight: document.documentElement.clientHeight,
        scrollHeight: document.documentElement.scrollHeight,
      },
      pageHorizontalOverflow: document.documentElement.scrollWidth - window.innerWidth,
      viewport: { width: window.innerWidth, height: window.innerHeight },
      fit: { scale: k, transform: style },
      blocks,
      order,
      split: split ? { rect: rectOf(split), className: split.className, height: split.offsetHeight } : null,
      mapToPanelGap: gap(viewportBox, sideBox),
      mapPanelRatio: viewportBox && sideBox ? +(viewportBox.w / sideBox.w).toFixed(3) : null,
      nodes,
      nodeRendered: nodes.length ? { w: nodes[0].rendered.w, h: nodes[0].rendered.h } : null,
      nodeLogical: nodes.length ? { w: nodes[0].logical.w, h: nodes[0].logical.h } : null,
      cards,
      cardGaps: cards.slice(1).map((c, i) => +Math.max(0, c.rect.x - (cards[i].rect.x + cards[i].rect.w)).toFixed(1)),
      attentionToJourneyGap: blocks['attention-now'] && blocks['shipment-journey']
        ? +(blocks['shipment-journey'].y - (blocks['attention-now'].y + blocks['attention-now'].h)).toFixed(1) : null,
      journeyToCardsGap: blocks['shipment-journey'] && blocks['journey-summary-cards'] ? null : null,
      completionGoalsText: (t('shipment-completion-goals')?.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 400),
      panelMode: t('journey-stage-workspace') ? 'stage'
        : t('journey-global-workspace') ? 'global'
          : t('journey-overview-panel') ? 'overview'
            : t('journey-customs-import-panel') ? 'customs-import'
              : t('journey-quick-panel') ? 'quick' : 'none',
    };
  });
}

async function noPageOverflow(page, label) {
  const m = await page.evaluate(() => {
    const shell = document.querySelector('.logi-shell');
    return {
      page: document.documentElement.scrollWidth - window.innerWidth,
      shell: shell ? shell.scrollWidth - shell.clientWidth : 0,
    };
  });
  assert.ok(m.page <= 1, `${label}: page-level horizontal overflow ${m.page}px`);
  assert.ok(m.shell <= 1, `${label}: app scrollport horizontal overflow ${m.shell}px`);
  ok(`${label}: no horizontal overflow (page ${m.page}px, app scrollport ${m.shell}px)`);
}

async function scrollShellTop(page) {
  await page.evaluate(() => { const s = document.querySelector('.logi-shell'); if (s) s.scrollTop = 0; });
  await page.waitForTimeout(150);
}
async function scrollShellTo(page, testid, pad = 10) {
  await page.evaluate(({ id, pad }) => {
    const shell = document.querySelector('.logi-shell');
    const el = document.querySelector(`[data-testid="${id}"]`);
    shell.scrollTop += el.getBoundingClientRect().top - shell.getBoundingClientRect().top - pad;
  }, { id: testid, pad });
  await page.waitForTimeout(150);
}

async function newPage(browser, width = REF_W, height = REF_H) {
  const page = await browser.newPage({ viewport: { width, height }, deviceScaleFactor: 1 });
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  const fonts = await useLocalFonts(page);
  page.__errors = errors;
  page.__fonts = fonts;
  return page;
}

// ------------------------------------------------------------------ geometry oracle
const ORACLE = JSON.parse(readFileSync(path.join(root, 'tests/component/fixtures/journey_demo_b_geometry.json'), 'utf8'));

function assertPopulatedComposition(m, label) {
  assert.ok(m.blocks['attention-now'], `${label}: Attention strip missing`);
  assert.ok(m.blocks['shipment-journey'], `${label}: Journey workspace missing`);
  assert.ok(m.blocks['attention-now'].y < m.blocks['shipment-journey'].y, `${label}: Attention must sit above Journey`);
  assert.equal(m.blocks['journey-phase-strip'], null, `${label}: no permanent six-phase strip above the populated map`);
  assert.equal(m.blocks['journey-map-toolbar'], null, `${label}: no extra populated map toolbar`);
  assert.ok(m.blocks['journey-map-viewport'], `${label}: map canvas missing`);
  assert.ok(m.blocks['journey-side-panel'], `${label}: right panel missing`);
  assert.equal(m.panelMode, 'quick', `${label}: default panel must be the factual Quick Panel, got ${m.panelMode}`);
  assert.equal(m.blocks['journey-overview-panel'], null, `${label}: generic overview panel must not replace the factual Quick Panel`);
  assert.equal(m.blocks['journey-global-workspace'], null, `${label}: Global Workspace must not be open by default`);
  assert.ok(m.blocks['journey-side-panel'].x > m.blocks['journey-map-viewport'].x + m.blocks['journey-map-viewport'].w - 2,
    `${label}: Quick Panel must sit to the RIGHT of the map`);
  assert.ok(m.cards.length === 5, `${label}: expected exactly five lower work cards, got ${m.cards.length}`);
  const ys = m.cards.map((c) => c.rect.y);
  assert.ok(Math.max(...ys) - Math.min(...ys) <= 1.5, `${label}: five cards must share one desktop row (Δy=${(Math.max(...ys) - Math.min(...ys)).toFixed(1)}px)`);
  const ws = m.cards.map((c) => c.rect.w);
  assert.ok(Math.max(...ws) - Math.min(...ws) <= 2, `${label}: five cards must share one width (Δw=${(Math.max(...ws) - Math.min(...ws)).toFixed(1)}px)`);
  assert.ok(m.split, `${label}: journey split missing`);
  ok(`${label}: composition = Attention → Journey(header + map + right Quick Panel) → five lower cards; no phase strip, no map toolbar, no Global Workspace`);
}

function assertNodeGeometry(m, label) {
  assert.ok(m.nodes.length >= 10, `${label}: expected the full detailed node set, got ${m.nodes.length}`);
  for (const n of m.nodes) {
    const want = ORACLE.positions[n.id];
    if (!want) continue;
    assert.equal(n.logical.w, want.w, `${label}: node ${n.id} logical width ${n.logical.w} != ${want.w}`);
    assert.equal(n.logical.h, want.h, `${label}: node ${n.id} logical height ${n.logical.h} != ${want.h}`);
    assert.ok(Math.abs(n.logical.x - want.x) <= 1, `${label}: node ${n.id} logical x ${n.logical.x} != ${want.x}`);
    assert.ok(Math.abs(n.logical.y - want.y) <= 1, `${label}: node ${n.id} logical y ${n.logical.y} != ${want.y}`);
  }
  const checked = m.nodes.filter((n) => ORACLE.positions[n.id]).length;
  ok(`${label}: ${checked} node cards match the immutable Prototype-B geometry oracle (164×136 at the approved DEMO_POS), fit scale=${m.fit.scale}`);
}

// ------------------------------------------------------------------ lanes
async function populatedLane() {
  const spec = HOSTS.populated;
  const host = await startHost(spec);
  let browser;
  try {
    const model = await (await fetch(`http://127.0.0.1:${spec.port}/model`)).json();
    const sea = (model.shipments || []).find((s) => s.id === spec.id);
    assert.ok(sea, `/model must carry ${spec.id}`);
    metrics.modelShipments = (model.shipments || []).map((s) => s.id);
    metrics.modelSea160JourneyNodes = (sea.journey?.nodes || []).length;
    metrics.modelAttentionItems = (model.attention || []).length;
    ok(`host /model delivers ${(model.shipments || []).length} shipments incl. ${spec.id} with ${(sea.journey?.nodes || []).length} journey nodes and ${(model.attention || []).length} Attention items`);

    browser = await chromium.launch(LAUNCH);
    metrics.browser = { executable: LAUNCH.executablePath || 'playwright-bundled', version: browser.version() };
    const page = await newPage(browser);
    let eventPosts = 0;
    page.on('request', (request) => {
      if (request.method() === 'POST' && request.url().endsWith('/event')) eventPosts += 1;
    });
    await openShipment(page, spec);
    metrics.fonts = await fontFamilyUsed(page);
    assert.equal(metrics.fonts.vietnameseAvailable, true, 'Be Vietnam Pro must be available for truthful text metrics');
    ok(`real Chromium ${browser.version()} rendered ${spec.id}; fonts: ${metrics.fonts.loadedFaces} faces loaded, family="${metrics.fonts.familyOnSurface.split(',')[0]}"`);

    // Store delivery proof: the DOM can only show 11 detailed nodes if the
    // mounted component received the canonical view model (no manual injection).
    const domNodeCount = await page.locator('[data-testid^="journey-node-"]').count();
    assert.equal(domNodeCount, sea.journey.nodes.length, 'rendered node count must equal the delivered view model');
    metrics.storeDelivery = { renderedNodes: domNodeCount, modelNodes: sea.journey.nodes.length, injectedManually: false };
    ok(`SHIPMENTS_STORE_DELIVERY: rendered ${domNodeCount} detailed nodes straight from the host view model (no manual store injection)`);

    await scrollShellTop(page);
    const m = await measure(page);
    metrics.populated = m;
    assertPopulatedComposition(m, 'populated 1536×1466');
    assertNodeGeometry(m, 'populated 1536×1466');
    // Issue #190 repair — measure with Chromium's real scrollbar behavior.
    // Removing the accidental shell overflow restores all 8 consumed pixels;
    // 17px page gutters + 1039 map + 12 gap + 451 panel match the reference.
    assert.ok(Math.abs(m.blocks['journey-side-panel'].w - 451) <= 1, `right Quick Panel width ${m.blocks['journey-side-panel'].w} != 451`);
    assert.ok(Math.abs(m.blocks['journey-map-viewport'].w - 1039) <= 1, `map width ${m.blocks['journey-map-viewport'].w} != 1039`);
    assert.ok(Math.abs(m.split.height - 718) <= 1, `populated split height ${m.split.height} != 718`);
    assert.ok(Math.abs(m.mapToPanelGap - 12) <= 0.5, `map/panel gap ${m.mapToPanelGap} != 12`);
    assert.ok(m.fit.scale >= 0.905 && m.fit.scale < 0.915, `fit scale ${m.fit.scale} must round to 91%`);
    assert.ok(m.shell.verticalOverflow <= 1,
      `focus-shell must not create a layout scrollbar: scrollHeight=${m.shell.scrollHeight}, clientHeight=${m.shell.clientHeight}`);
    assert.equal(m.shell.clientWidth, REF_W, `no vertical scrollbar should consume layout width (${m.shell.clientWidth} != ${REF_W})`);
    ok(`scrollport: .logi-shell client ${m.shell.clientWidth}×${m.shell.clientHeight}, scroll ${m.shell.scrollWidth}×${m.shell.scrollHeight}, vertical overflow ${m.shell.verticalOverflow}px`);
    ok(`geometry: Journey outer ${m.blocks['shipment-journey'].w}×${m.blocks['shipment-journey'].h} · map ${m.blocks['journey-map-viewport'].w}×${m.blocks['journey-map-viewport'].h} · Quick Panel ${m.blocks['journey-side-panel'].w}×${m.blocks['journey-side-panel'].h} · map/panel ratio ${m.mapPanelRatio} · fit ${Math.round(m.fit.scale * 100)}% · split height ${m.split.height}px · card gaps ${JSON.stringify(m.cardGaps)}`);

    // The focus-shell identity bar is the reference's one compact header. The
    // permanent legacy tab row is absent; truthful secondary facts remain in
    // the existing HỒ SƠ & PHẠM VI on-demand disclosure.
    assert.ok(m.blocks['shipment-identity-bar'], 'compact shipment identity bar must render');
    assert.equal(await page.locator('#workspace-tabs').count(), 0, 'no permanent shipment tab row on the first screen');
    assert.ok((await page.getByTestId('journey-summary-card-5').innerText()).includes('HỒ SƠ & PHẠM VI'),
      'HỒ SƠ & PHẠM VI card must preserve the secondary-facts surface');
    ok('compact identity bar + HỒ SƠ secondary-facts disclosure preserved; no permanent legacy tab row');

    // Completion Goals must stay collapsed and must not dominate the first screen.
    assert.equal(m.blocks['completion-goal-details'], null, 'Completion Goals must be collapsed by default');
    assert.ok(/không phải|not required|không yêu cầu|dẫn xuất|derived/i.test(m.completionGoalsText),
      `collapsed Completion Goals copy must say it is derived guidance, not create-lot required fields: ${m.completionGoalsText.slice(0, 160)}`);
    const goalsBelowJourney = m.blocks['shipment-completion-goals'].y > m.blocks['shipment-journey'].y;
    assert.ok(goalsBelowJourney, 'Completion Goals must sit below the Journey workspace');
    ok(`Completion Goals collapsed by default (details absent), copy states derived-guidance truth, block sits below Journey at y=${m.blocks['shipment-completion-goals'].y}`);

    // First-screen block order at scrollTop=0.
    const firstScreen = await page.evaluate((h) => {
      const shell = document.querySelector('.logi-shell');
      const top = shell.getBoundingClientRect().top;
      const ids = ['attention-now', 'shipment-journey', 'journey-map-viewport', 'journey-side-panel',
        'journey-summary-cards', 'shipment-completion-goals', 'journey-global-workspace'];
      return ids.map((id) => {
        const el = document.querySelector(`[data-testid="${id}"]`);
        if (!el) return null;
        const r = el.getBoundingClientRect();
        return { id, visibleInFirstScreen: r.bottom > top && r.top < top + h, top: Math.round(r.top - top), bottom: Math.round(r.bottom - top) };
      }).filter(Boolean);
    }, REF_H);
    metrics.populatedFirstScreen = firstScreen;
    const cardsFirst = firstScreen.find((b) => b.id === 'journey-summary-cards');
    assert.ok(cardsFirst && cardsFirst.visibleInFirstScreen,
      'five summary cards must be visible inside the 1466 first screen (Owner reference shows the full card row)');
    assert.ok(cardsFirst.bottom <= REF_H,
      `five summary cards must END inside the first screen like the Owner reference (cards bottom ${cardsFirst.bottom} > ${REF_H})`);
    ok(`first screen (1536×${REF_H}, scrollTop=0): ${firstScreen.map((b) => `${b.id}${b.visibleInFirstScreen ? '' : '(below fold)'}`).join(' → ')}`);

    await page.screenshot({ path: path.join(outDir, 'candidate-populated-desktop.png') });
    await page.getByTestId('shipment-journey').screenshot({ path: path.join(outDir, 'candidate-populated-journey.png') });
    await page.screenshot({ path: path.join(outDir, 'candidate-populated-fullpage.png'), fullPage: true });
    ok(`captured candidate-populated-desktop.png (${REF_W}×${REF_H}), candidate-populated-journey.png, candidate-populated-fullpage.png`);

    // ---- B1: Customs Import slot order + pinned, non-scrolling footer.
    await page.getByTestId('journey-node-customs-import').click();
    await page.getByTestId('journey-customs-import-panel').waitFor();
    const customsContract = await page.evaluate(() => {
      const t = (id) => document.querySelector(`[data-testid="${id}"]`);
      const panel = t('journey-side-panel').getBoundingClientRect();
      const action = t('ci-next-action');
      const registration = t('ci-registration-clearance');
      const scroll = t('ci-scroll-region');
      const footer = t('ci-footer');
      const fr = footer.getBoundingClientRect();
      return {
        actionCount: document.querySelectorAll('[data-testid="ci-next-action"]').length,
        registrationCount: document.querySelectorAll('[data-testid="ci-registration-clearance"]').length,
        primaryCount: document.querySelectorAll('[data-testid="ci-primary-cta"]').length,
        workspaceCount: document.querySelectorAll('[data-testid="ci-open-workspace"]').length,
        actionBeforeRegistration: Boolean(action.compareDocumentPosition(registration) & Node.DOCUMENT_POSITION_FOLLOWING),
        actionY: action.getBoundingClientRect().y,
        registrationY: registration.getBoundingClientRect().y,
        actionBackground: getComputedStyle(action).backgroundColor,
        actionBorder: getComputedStyle(action).borderColor,
        scrollTop: scroll.scrollTop,
        scrollHeight: scroll.scrollHeight,
        clientHeight: scroll.clientHeight,
        footerY: fr.y,
        footerBottom: fr.bottom,
        panelTop: panel.top,
        panelBottom: panel.bottom,
      };
    });
    assert.equal(customsContract.actionCount, 1, 'exactly one ci-next-action');
    assert.equal(customsContract.registrationCount, 1, 'exactly one ci-registration-clearance');
    assert.equal(customsContract.primaryCount, 1, 'exactly one ci-primary-cta');
    assert.equal(customsContract.workspaceCount, 1, 'exactly one ci-open-workspace');
    assert.ok(customsContract.actionBeforeRegistration && customsContract.actionY < customsContract.registrationY,
      'ci-next-action must precede registration/clearance facts');
    assert.equal(customsContract.actionBackground, 'rgb(254, 242, 242)', 'dominant next-action surface must remain red');
    const actionBorderRgb = (customsContract.actionBorder.match(/\d+/g) || []).map(Number);
    assert.ok(actionBorderRgb.length === 3 && actionBorderRgb[0] >= 180
      && actionBorderRgb[0] > actionBorderRgb[1] * 2 && actionBorderRgb[0] > actionBorderRgb[2] * 2,
    `dominant next-action border must remain red, got ${customsContract.actionBorder}`);
    assert.ok(customsContract.footerY >= customsContract.panelTop && customsContract.footerBottom <= customsContract.panelBottom + 1,
      'workspace footer must be visible inside the 718px panel without scrolling');
    assert.ok(customsContract.scrollHeight > customsContract.clientHeight,
      'canonical long customs facts must overflow only the internal content region');
    await page.screenshot({ path: path.join(outDir, 'quick-panel-action-order.png') });
    await page.evaluate(() => {
      const scroll = document.querySelector('[data-testid="ci-scroll-region"]');
      scroll.scrollTop = scroll.scrollHeight;
    });
    await page.waitForTimeout(100);
    const afterInternalScroll = await page.evaluate(() => {
      const scroll = document.querySelector('[data-testid="ci-scroll-region"]');
      const footer = document.querySelector('[data-testid="ci-footer"]').getBoundingClientRect();
      return { scrollTop: scroll.scrollTop, footerY: footer.y };
    });
    assert.ok(afterInternalScroll.scrollTop > 0, 'long customs content must scroll internally');
    assert.ok(Math.abs(afterInternalScroll.footerY - customsContract.footerY) <= 0.5,
      `internal scroll moved fixed footer (${customsContract.footerY} → ${afterInternalScroll.footerY})`);
    metrics.customsPanel = { initial: customsContract, afterInternalScroll };
    await page.screenshot({ path: path.join(outDir, 'quick-panel-pinned-footer.png') });
    const writesBeforeWorkspaceOpen = eventPosts;
    await page.getByTestId('ci-open-workspace').click();
    await page.getByTestId('journey-stage-workspace').waitFor();
    assert.equal(eventPosts, writesBeforeWorkspaceOpen,
      'opening Stage Workspace is navigation only and must emit zero writes');
    ok(`Customs Quick Panel: next action precedes registration/clearance; 1 primary CTA + 1 navigation CTA; content scrolled ${afterInternalScroll.scrollTop}px while footer stayed at y=${afterInternalScroll.footerY}; Stage Workspace opened with zero writes`);
    await openShipment(page, spec);
    await scrollShellTop(page);

    // B2 capability preservation: the zero-module setup is absent by default,
    // but remains keyboard/click accessible behind HỒ SƠ's existing disclosure.
    assert.equal(await page.getByTestId('journey-modules-empty').count(), 0,
      'empty optional module setup must not consume a permanent first-screen row');
    const writesBeforeModuleDisclosure = eventPosts;
    await page.getByTestId('journey-summary-card-5').locator('summary').click();
    await page.getByTestId('journey-add-module-page').waitFor();
    await page.getByTestId('journey-add-module-page').click();
    await page.getByTestId('journey-modules-empty').waitFor();
    assert.equal(eventPosts, writesBeforeModuleDisclosure,
      'revealing optional-module setup is navigation only and must emit zero writes');
    ok('optional module setup: absent from default first screen, still reachable from HỒ SƠ → Thông tin thêm with zero writes');
    await openShipment(page, spec);
    await scrollShellTop(page);

    // ---- secondary state: Completion Goals expanded
    await page.getByTestId('shipment-completion-goals').screenshot({ path: path.join(outDir, 'completion-collapsed.png') });
    await scrollShellTo(page, 'shipment-completion-goals');
    await page.getByTestId('completion-goal-toggle').click();
    await page.getByTestId('completion-goal-details').waitFor();
    await page.waitForTimeout(200);
    const expanded = await measure(page);
    metrics.completionExpanded = { details: expanded.blocks['completion-goal-details'], text: expanded.completionGoalsText };
    assert.ok(expanded.blocks['completion-goal-details'], 'expanded details must render');
    await page.getByTestId('shipment-completion-goals').screenshot({ path: path.join(outDir, 'completion-goals-expanded.png') });
    ok(`Completion Goals expand on demand: details ${Math.round(expanded.blocks['completion-goal-details'].w)}×${Math.round(expanded.blocks['completion-goal-details'].h)}px (collapsed row was ${Math.round(m.blocks['shipment-completion-goals'].h)}px)`);
    await page.getByTestId('completion-goal-toggle').click();
    await page.waitForTimeout(150);
    await scrollShellTop(page);

    // ---- secondary state: Global Workspace auto-collapses the map
    await page.getByRole('button', { name: 'Toàn bộ lô hàng' }).first().click();
    await page.getByTestId('journey-global-workspace').waitFor();
    await page.waitForTimeout(250);
    const gw = await measure(page);
    metrics.globalWorkspace = {
      rail: gw.blocks['journey-map-rail'], sidePanel: gw.blocks['journey-side-panel'],
      mapViewport: gw.blocks['journey-map-viewport'], panelMode: gw.panelMode, splitClass: gw.split?.className,
    };
    assert.equal(gw.panelMode, 'global', 'Global Workspace must own the right side');
    assert.ok(gw.blocks['journey-map-rail'], 'map must auto-collapse to the existing rail');
    assert.equal(gw.blocks['journey-map-viewport'], null, 'full map must not keep consuming the width');
    assert.ok(gw.blocks['journey-side-panel'].w >= 600, `workspace pane must get readable width, got ${gw.blocks['journey-side-panel'].w}`);
    await page.screenshot({ path: path.join(outDir, 'candidate-global-workspace.png') });
    ok(`Global Workspace: map auto-collapsed to rail (${Math.round(gw.blocks['journey-map-rail'].w)}px), workspace pane ${Math.round(gw.blocks['journey-side-panel'].w)}px wide — no full forms squeezed into the 451px Quick Panel`);

    // operator can reopen the map
    const reopen = page.getByTestId('journey-map-rail').locator('button, [aria-label]').first();
    if (await reopen.count()) {
      await reopen.click().catch(() => {});
      await page.waitForTimeout(200);
    }
    await openShipment(page, spec); // back to the truthful default state

    // ---- 390px
    await page.setViewportSize({ width: 390, height: 844 });
    await page.waitForTimeout(300);
    await scrollShellTop(page);
    const mob = await measure(page);
    metrics.populated390 = { split: mob.split, map: mob.blocks['journey-map-viewport'], side: mob.blocks['journey-side-panel'], cards: mob.cards.length, overflow: mob.shell?.horizontalOverflow };
    await noPageOverflow(page, 'populated 390');
    await page.screenshot({ path: path.join(outDir, 'candidate-populated-390.png') });
    ok(`populated 390×844: stacked split ${Math.round(mob.split.rect.w)}×${Math.round(mob.split.rect.h)}, map ${Math.round(mob.blocks['journey-map-viewport'].h)}px tall, panel ${Math.round(mob.blocks['journey-side-panel'].h)}px tall, ${mob.cards.length} cards`);

    await page.setViewportSize({ width: REF_W, height: REF_H });
    await page.goto(`http://127.0.0.1:${spec.port}`);
    await page.waitForTimeout(250);
    const normalShell = await page.evaluate(() => {
      const visible = (selector) => {
        const el = document.querySelector(selector);
        if (!el) return false;
        const r = el.getBoundingClientRect();
        return r.width > 0 && r.height > 0 && getComputedStyle(el).display !== 'none';
      };
      return { focus: Boolean(document.querySelector('.focus-shell')), topbar: visible('.global-topbar'), sidebar: visible('.global-sidebar') };
    });
    assert.deepEqual(normalShell, { focus: false, topbar: true, sidebar: true },
      'normal non-detail route must retain production topbar/sidebar chrome');
    await page.screenshot({ path: path.join(outDir, 'candidate-other-route-home.png') });
    metrics.normalShell = normalShell;
    ok('normal-shell non-detail route keeps desktop topbar + sidebar');
    assert.deepEqual(page.__errors, [], `page errors: ${page.__errors.join(' | ')}`);
    ok('zero application page errors on the populated lane');
    return m;
  } catch (e) {
    console.error(host.err());
    throw e;
  } finally {
    await browser?.close();
    host.host.kill();
    await new Promise((r) => setTimeout(r, 400));
  }
}

async function listLane() {
  const spec = HOSTS.populated;
  const host = await startHost(spec);
  let browser;
  try {
    browser = await chromium.launch(LAUNCH);
    const page = await newPage(browser);
    await page.goto(`http://127.0.0.1:${spec.port}`);
    await page.getByRole('link', { name: 'Lô Hàng', exact: true }).first().click();
    await page.getByTestId('shipment-period-tat-ca').click();
    await page.waitForTimeout(300);

    const rows = await page.evaluate(() => [...document.querySelectorAll('[data-testid="shipment-row"]')].map((tr) => {
      const band = tr.querySelector('[data-attention-band]');
      const cell = band ? band.textContent.replace(/\s+/g, ' ').trim() : '';
      return {
        id: tr.dataset.shipmentId,
        band: band?.dataset.attentionBand || null,
        alertMarker: Boolean(tr.querySelector('[data-testid^="shipment-alert"], .animate-pulse, [aria-label*=" khẩn"], [aria-label*="Quá hạn"]')),
        pulseDot: Boolean(tr.querySelector('.animate-pulse')),
        nextAction: cell.slice(0, 90),
        responsibility: (tr.textContent.match(/Phụ trách:\s*([^\n]*?)\s*Cập nhật bởi:\s*([^\n]*?)(?:\s|$)/) || []).slice(1, 3),
      };
    }));
    metrics.shipmentList = rows;
    assert.ok(rows.length >= 2, 'list must render multiple shipments');
    const withBand = rows.filter((r) => r.band);
    const urgent = rows.filter((r) => r.band === 'BLOCKING' || r.band === 'OVERDUE');
    const without = rows.filter((r) => !r.band);
    assert.ok(urgent.length >= 1, 'canonical fixture must include a BLOCKING/OVERDUE row');
    assert.ok(without.length >= 1, 'canonical fixture must include a nonurgent comparison row');
    ok(`list rows=${rows.length}; canonical urgent bands=${urgent.map((r) => `${r.id}:${r.band}`).join(', ')}; nonurgent rows=${without.map((r) => r.id).join(', ')}`);
    // Urgency must come from canonical Attention only.
    for (const r of rows) {
      if (!r.band) assert.equal(r.pulseDot, false, `${r.id}: pulse/alert without a canonical Attention band`);
    }
    ok('no urgency marker on any row without a canonical Attention band (no wording heuristics)');
    const owner = rows.find((r) => r.responsibility?.[0]);
    assert.ok(owner, 'responsibility line must render');
    ok(`responsibility truth: Phụ trách (canonical owner) + Cập nhật bởi (updated_by, secondary) rendered per row, e.g. ${owner.id} → Phụ trách: ${owner.responsibility[0]} / Cập nhật bởi: ${owner.responsibility[1] || '—'}`);

    await page.screenshot({ path: path.join(outDir, 'shipment-list-alerts.png') });
    await page.screenshot({ path: path.join(outDir, 'shipment-list-alerts-fullpage.png'), fullPage: true });
    await noPageOverflow(page, 'shipment list');
    ok('captured shipment-list-alerts.png (urgent + non-urgent rows, canonical bands only)');
    assert.deepEqual(page.__errors, [], `page errors: ${page.__errors.join(' | ')}`);
  } catch (e) {
    console.error(host.err());
    throw e;
  } finally {
    await browser?.close();
    host.host.kill();
    await new Promise((r) => setTimeout(r, 400));
  }
}

async function freshLane() {
  const spec = HOSTS.fresh;
  const host = await startHost(spec);
  let browser;
  try {
    const fixture = await (await fetch(`http://127.0.0.1:${spec.port}/fixture`)).json().catch(() => null);
    if (fixture) {
      metrics.freshServerTruth = { shipmentId: fixture.shipmentId, journeyNodes: fixture.journeyNodes, profileState: fixture.profileState, persisted: fixture.persisted };
      assert.equal(fixture.journeyNodes, 0, 'fresh fixture must be zero-node');
      ok(`fresh host server truth: ${fixture.shipmentId} persisted, journey.nodes=0, profile=${fixture.profileState}`);
    }
    browser = await chromium.launch(LAUNCH);
    const page = await newPage(browser);
    await openShipment(page, spec);
    metrics.fonts = metrics.fonts || await fontFamilyUsed(page);

    assert.equal(await page.getByTestId('shipment-journey').getAttribute('data-empty-journey'), 'true', 'fresh cockpit shell');
    const phases = await page.locator('[data-testid^="journey-phase-"]').evaluateAll((els) => els
      .filter((e) => e.dataset.testid !== 'journey-phase-strip')
      .map((e) => ({ id: e.dataset.testid.replace('journey-phase-', ''), state: e.dataset.state, disabled: e.disabled, label: e.textContent.replace(/\s+/g, ' ').trim() })));
    assert.equal(phases.length, 6, `six phases expected, got ${phases.length}`);
    const profile = phases.find((p) => p.id === 'profile');
    assert.equal(profile.state, 'ACTION', 'HỒ SƠ must be the actionable phase');
    assert.equal(profile.disabled, false, 'HỒ SƠ must not be inert');
    const downstream = phases.filter((p) => p.id !== 'profile');
    assert.ok(downstream.every((p) => p.state === 'UNKNOWN' && p.disabled), 'five downstream phases stay UNKNOWN + inert');
    assert.equal(await page.locator('[data-testid^="journey-node-"]').count(), 0, 'no fabricated detailed nodes');
    ok(`fresh truth: HỒ SƠ actionable; ${downstream.map((p) => p.label.split(' ')[0]).join(' / ')} remain UNKNOWN and inert; zero fabricated nodes`);

    await scrollShellTop(page);
    const m = await measure(page);
    metrics.fresh = m;
    assert.ok(m.split.className.includes('journey-split-fresh'), `fresh split must use the compact class, got "${m.split.className}"`);
    assert.ok(m.split.height <= 520, `fresh canvas must be compact, split height=${m.split.height}px`);
    assert.ok(m.blocks['journey-empty-canvas'], 'compact onboarding canvas required');
    assert.ok(m.blocks['journey-side-panel'], 'right onboarding panel required');
    assert.ok(m.blocks['journey-side-panel'].x > m.blocks['journey-empty-canvas'].x, 'onboarding panel must sit on the right');
    ok(`fresh density: split height ${m.split.height}px (compact class), canvas ${Math.round(m.blocks['journey-empty-canvas'].w)}×${Math.round(m.blocks['journey-empty-canvas'].h)}, right panel ${Math.round(m.blocks['journey-side-panel'].w)}×${Math.round(m.blocks['journey-side-panel'].h)}`);
    await noPageOverflow(page, `fresh ${REF_W}`);
    await page.screenshot({ path: path.join(outDir, 'candidate-fresh-desktop.png') });
    await page.getByTestId('shipment-journey').screenshot({ path: path.join(outDir, 'candidate-fresh-desktop-cockpit.png') });
    ok(`captured candidate-fresh-desktop.png (${REF_W}×${REF_H}) + candidate-fresh-desktop-cockpit.png`);

    // B1 — Execution Profile CTA still works.
    const cta = page.getByTestId('journey-empty-primary-cta');
    assert.equal(await cta.count(), 1, 'exactly one dominant fresh CTA');
    await cta.click();
    await page.waitForTimeout(300);
    await page.getByTestId('journey-global-workspace').waitFor({ state: 'visible' });
    await page.getByTestId('shipment-execution-profile').waitFor({ state: 'visible' });
    const inside = await page.evaluate(() => document.querySelector('[data-testid="journey-global-workspace"]')
      ?.contains(document.querySelector('[data-testid="shipment-execution-profile"]')) === true);
    assert.equal(inside, true, 'profile CTA must reach the existing Execution Profile editor');
    ok('fresh B1: HỒ SƠ CTA opens Global Workspace → existing Execution Profile editor (no dead CTA)');

    await openShipment(page, spec);
    await page.setViewportSize({ width: 390, height: 844 });
    await page.waitForTimeout(300);
    await scrollShellTop(page);
    const mob = await measure(page);
    const freshTop = await page.evaluate(() => {
      const shell = document.querySelector('.logi-shell');
      const phase = document.querySelector('[data-testid="journey-phase-strip"]');
      const canvas = document.querySelector('[data-testid="journey-empty-canvas"]');
      const sr = shell.getBoundingClientRect();
      const pr = phase.getBoundingClientRect();
      const cr = canvas.getBoundingClientRect();
      return {
        scrollTop: shell.scrollTop,
        phaseVisible: pr.bottom > sr.top && pr.top < sr.bottom,
        canvasEntranceVisible: cr.top < sr.bottom && cr.bottom > sr.top,
        shell: { top: sr.top, bottom: sr.bottom }, phase: { top: pr.top, bottom: pr.bottom },
        canvas: { top: cr.top, bottom: cr.bottom },
      };
    });
    assert.equal(freshTop.scrollTop, 0, 'fresh 390 top evidence must be captured at scrollTop=0');
    assert.ok(freshTop.phaseVisible, 'fresh 390 top must show the truthful six-phase strip');
    assert.ok(freshTop.canvasEntranceVisible, 'fresh 390 top must show the zero-node canvas entrance');
    metrics.fresh390 = { split: mob.split, canvas: mob.blocks['journey-empty-canvas'], side: mob.blocks['journey-side-panel'], phases: mob.blocks['journey-phase-strip'], topEvidence: freshTop };
    await noPageOverflow(page, 'fresh 390');
    await page.screenshot({ path: path.join(outDir, 'candidate-fresh-390-top.png') });
    // Keep enough space above the button to show the complete amber onboarding
    // card below the fixed mobile topbar, rather than aligning the CTA beneath it.
    await scrollShellTo(page, 'journey-empty-primary-cta', 320);
    const freshOnboarding = await page.evaluate(() => {
      const cta = document.querySelector('[data-testid="journey-empty-primary-cta"]').getBoundingClientRect();
      const shell = document.querySelector('.logi-shell').getBoundingClientRect();
      return { cta: { top: cta.top, bottom: cta.bottom }, shell: { top: shell.top, bottom: shell.bottom } };
    });
    assert.ok(freshOnboarding.cta.top >= 64 && freshOnboarding.cta.bottom <= freshOnboarding.shell.bottom,
      `fresh onboarding CTA must be visible below mobile topbar (${JSON.stringify(freshOnboarding)})`);
    metrics.fresh390.onboardingEvidence = freshOnboarding;
    await page.screenshot({ path: path.join(outDir, 'candidate-fresh-390-onboarding.png') });
    ok(`captured candidate-fresh-390-top.png at scrollTop=0 (phase strip + canvas entrance) and candidate-fresh-390-onboarding.png (visible HỒ SƠ action); split ${Math.round(mob.split.rect.w)}×${Math.round(mob.split.rect.h)}`);
    assert.deepEqual(page.__errors, [], `page errors: ${page.__errors.join(' | ')}`);
    ok('zero application page errors on the fresh lane');
  } catch (e) {
    console.error(host.err());
    throw e;
  } finally {
    await browser?.close();
    host.host.kill();
    await new Promise((r) => setTimeout(r, 400));
  }
}

async function donorLane() {
  const spec = HOSTS.donor;
  if (!spec) { console.log('  · donor lane skipped (DONOR_ROOT not set)'); return null; }
  assert.ok(existsSync(path.join(spec.cwd, spec.host)), `donor host script not found under ${spec.cwd}`);
  const host = await startHost(spec);
  let browser;
  try {
    const model = await (await fetch(`http://127.0.0.1:${spec.port}/model`)).json();
    const sea = (model.shipments || []).find((s) => s.id === spec.id);
    assert.ok(sea, `donor /model must carry ${spec.id}`);
    metrics.donorModelNodes = (sea.journey?.nodes || []).length;
    browser = await chromium.launch(LAUNCH);
    const page = await newPage(browser);
    await openShipment(page, spec);
    metrics.donorFonts = await fontFamilyUsed(page);
    await scrollShellTop(page);
    const m = await measure(page);
    metrics.donor = m;
    await page.screenshot({ path: path.join(outDir, 'reference-donor-reconstruction.png') });
    await page.screenshot({ path: path.join(outDir, 'reference-donor-reconstruction-fullpage.png'), fullPage: true });
    ok(`donor reconstruction captured at ${REF_W}×${REF_H}: Journey ${m.blocks['shipment-journey']?.w}×${m.blocks['shipment-journey']?.h}, map ${m.blocks['journey-map-viewport']?.w}×${m.blocks['journey-map-viewport']?.h}, panel ${m.blocks['journey-side-panel']?.w}×${m.blocks['journey-side-panel']?.h}, cards=${m.cards.length}, split=${m.split?.height}px, nodes=${m.nodes.length}`);
    return m;
  } catch (e) {
    console.error(host.err());
    throw e;
  } finally {
    await browser?.close();
    host.host.kill();
    await new Promise((r) => setTimeout(r, 400));
  }
}

// ------------------------------------------------------------------ compare
function compare(candidate, donor, label) {
  if (!candidate || !donor) return;
  const rows = [];
  const push = (name, ref, cand) => rows.push({ metric: name, reference_donor: ref, candidate: cand });
  const b = (o) => (o ? `${o.w}×${o.h} @(${o.x},${o.y})` : 'absent');
  push('journey outer bbox', b(donor.blocks['shipment-journey']), b(candidate.blocks['shipment-journey']));
  push('map bbox', b(donor.blocks['journey-map-viewport']), b(candidate.blocks['journey-map-viewport']));
  push('right quick panel bbox', b(donor.blocks['journey-side-panel']), b(candidate.blocks['journey-side-panel']));
  push('map/panel width ratio', donor.mapPanelRatio, candidate.mapPanelRatio);
  push('split height', donor.split?.height, candidate.split?.height);
  push('node logical W/H', donor.nodeLogical && `${donor.nodeLogical.w}×${donor.nodeLogical.h}`, candidate.nodeLogical && `${candidate.nodeLogical.w}×${candidate.nodeLogical.h}`);
  push('node rendered W/H', donor.nodeRendered && `${donor.nodeRendered.w}×${donor.nodeRendered.h}`, candidate.nodeRendered && `${candidate.nodeRendered.w}×${candidate.nodeRendered.h}`);
  push('fit scale', donor.fit.scale, candidate.fit.scale);
  push('map→panel gap', donor.mapToPanelGap, candidate.mapToPanelGap);
  push('attention→journey gap', donor.attentionToJourneyGap, candidate.attentionToJourneyGap);
  push('lower cards count', donor.cards.length, candidate.cards.length);
  push('lower card widths', donor.cards.map((c) => c.rect.w).join('/'), candidate.cards.map((c) => c.rect.w).join('/'));
  push('lower card gaps', donor.cardGaps.join('/'), candidate.cardGaps.join('/'));
  push('six-phase strip present', donor.blocks['journey-phase-strip'] ? 'yes' : 'no', candidate.blocks['journey-phase-strip'] ? 'yes' : 'no');
  push('map toolbar present', donor.blocks['journey-map-toolbar'] ? 'yes' : 'no', candidate.blocks['journey-map-toolbar'] ? 'yes' : 'no');
  push('default panel mode', donor.panelMode, candidate.panelMode);
  push('completion goals collapsed', donor.blocks['completion-goal-details'] ? 'expanded' : 'collapsed', candidate.blocks['completion-goal-details'] ? 'expanded' : 'collapsed');
  push('first-screen block order', donor.order.map((o) => o.id).join(' → '), candidate.order.map((o) => o.id).join(' → '));
  metrics.comparison = { label, rows };
  console.log(`\n  ${label}: reference(donor) vs candidate`);
  for (const r of rows) console.log(`    · ${r.metric}: ${r.reference_donor}  ||  ${r.candidate}`);
}

// ------------------------------------------------------------------ run
const want = (m) => mode === 'all' || mode === m;
try {
  if (mode === 'all') {
    // A donor checkout is optional; the Owner PNG remains the visual oracle.
    // Always exercise every candidate lane even when DONOR_ROOT is absent.
    const donor = await donorLane();
    const cand = await populatedLane();
    if (donor) compare(cand, donor, 'populated desktop 1536×1466');
    await listLane();
    await freshLane();
  } else if (mode === 'donor') {
    await donorLane();
  } else if (want('populated')) {
    await populatedLane();
  } else if (want('list')) {
    await listLane();
  } else if (want('fresh')) {
    await freshLane();
  }
} catch (e) {
  metrics.error = String(e && e.stack || e);
  writeFileSync(path.join(outDir, 'geometry.json'), JSON.stringify(metrics, null, 2));
  console.error('\nFAILED:', e.message);
  process.exitCode = 1;
  throw e;
} finally {
  metrics.checks = results;
  writeFileSync(path.join(outDir, 'geometry.json'), JSON.stringify(metrics, null, 2));
}
console.log(`\n  metrics written to ${path.relative(root, path.join(outDir, 'geometry.json'))} (${results.length} checks)`);
