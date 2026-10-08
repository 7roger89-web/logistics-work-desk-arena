// Issue #188 real-browser acceptance — fresh-shipment cockpit parity + populated regression.
//
// Real Chromium only (`CHROMIUM_EXECUTABLE`), same contract as the #160/#162
// runners: PLAYWRIGHT_MODULE=/path/to/playwright/index.mjs, CHROMIUM_LIB_PATH
// (BROWSER-ONLY LD_LIBRARY_PATH), PYTHON override for the acceptance host.
//
// Usage:
//   node tests/component/browser_journey_fresh_parity_188.mjs <outdir> [fresh|populated|all]
//
//   fresh     -> scripts/verify_journey_fresh_parity_188.py  (SEA-188, journey.nodes=[])
//   populated -> scripts/verify_visual_shipment_workspace.py (SEA-160, 11 detailed nodes)
import { spawn } from 'node:child_process';
import { mkdirSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import assert from 'node:assert/strict';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const outDir = process.argv[2] || '/tmp/journey-188';
mkdirSync(outDir, { recursive: true });
const mode = (process.argv[3] || 'all').toLowerCase();
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || 'playwright');
const PY = process.env.PYTHON || 'python3';
const LAUNCH = {
  executablePath: process.env.CHROMIUM_EXECUTABLE || undefined,
  headless: true,
  args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--disable-gpu'],
  env: process.env.CHROMIUM_LIB_PATH
    ? { ...process.env, LD_LIBRARY_PATH: process.env.CHROMIUM_LIB_PATH }
    : process.env,
};

const FRESH = { id: 'SEA-188', host: 'scripts/verify_journey_fresh_parity_188.py', port: 9502, extra: ['--port', '9502'] };
const POPULATED = { id: 'SEA-160', host: 'scripts/verify_visual_shipment_workspace.py', port: 9501, extra: [] };

const results = [];
const ok = (line) => { results.push(line); console.log('  ✓ ' + line); };

async function startHost(spec) {
  const host = spawn(PY, [spec.host, ...spec.extra], { cwd: root, stdio: ['ignore', 'pipe', 'pipe'] });
  let err = '';
  host.stderr.on('data', (b) => { err += b; });
  for (let i = 0; i < 200; i++) {
    try { if ((await fetch(`http://127.0.0.1:${spec.port}/model`)).ok) return { host, err: () => err.slice(-1500) }; } catch {}
    await new Promise((r) => setTimeout(r, 100));
  }
  throw new Error(`acceptance host did not start: ${err.slice(-800)}`);
}

async function openShipment(page, spec) {
  await page.goto(`http://127.0.0.1:${spec.port}`);
  await page.getByRole('link', { name: 'Lô Hàng', exact: true }).first().click();
  await page.getByTestId('shipment-period-tat-ca').click();
  await page.getByRole('link', { name: spec.id, exact: true }).click();
  await page.getByTestId('shipment-journey').waitFor();
}

const box = async (page, testid) => {
  const b = await page.getByTestId(testid).first().boundingBox();
  assert.ok(b, `${testid} has no box`);
  return b;
};

async function phaseInfo(page) {
  return page.locator('[data-testid^="journey-phase-"]').evaluateAll((els) =>
    els.filter((e) => e.dataset.testid !== 'journey-phase-strip').map((e) => ({
      id: e.dataset.testid.replace('journey-phase-', ''),
      spans: [...e.querySelectorAll('span')].map((s) => s.textContent.trim()),
      state: e.dataset.state,
      disabled: e.disabled,
    })));
}

// The approved shell (component/src/shell.css) is its OWN scrollport
// (`.logi-shell { height: calc(100vh - toolbar); overflow-y: auto }`), exactly as
// it is inside the Streamlit component. Layout truth therefore has to be read
// from that scrollport, not from viewport-relative boxes of a scrolled page.
async function noPageOverflow(page, label) {
  const m = await page.evaluate(() => {
    const shell = document.querySelector('.logi-shell');
    return {
      page: document.documentElement.scrollWidth - window.innerWidth,
      shell: shell ? shell.scrollWidth - shell.clientWidth : 0,
      body: Math.round(document.body.getBoundingClientRect().width),
      viewport: window.innerWidth,
    };
  });
  assert.ok(m.page <= 1, `${label}: page-level horizontal overflow ${m.page}px`);
  assert.ok(m.shell <= 1, `${label}: app scrollport horizontal overflow ${m.shell}px`);
  ok(`${label}: no horizontal overflow (page ${m.page}px, app scrollport ${m.shell}px, body ${m.body}px ≤ viewport ${m.viewport}px)`);
}

/** Absolute top of each surface inside the shell's scroll content (scroll-independent). */
async function shellOffsets(page, ids) {
  return page.evaluate((list) => {
    const shell = document.querySelector('.logi-shell');
    const base = shell.getBoundingClientRect().top - shell.scrollTop;
    const out = { _shellScrollHeight: shell.scrollHeight, _shellClientHeight: shell.clientHeight };
    for (const id of list) {
      const el = document.querySelector(`[data-testid="${id}"]`);
      out[id] = el ? Math.round(el.getBoundingClientRect().top - base) : null;
    }
    return out;
  }, ids);
}

async function scrollShellTo(page, testid, pad = 10) {
  await page.evaluate(({ id, pad }) => {
    const shell = document.querySelector('.logi-shell');
    const el = document.querySelector(`[data-testid="${id}"]`);
    shell.scrollTop += el.getBoundingClientRect().top - shell.getBoundingClientRect().top - pad;
  }, { id: testid, pad });
  await page.waitForTimeout(120);
}

async function scrollShellTop(page) {
  await page.evaluate(() => { document.querySelector('.logi-shell').scrollTop = 0; });
  await page.waitForTimeout(120);
}

// ---------------------------------------------------------------- fresh lane
async function freshChecks() {
  const host = await startHost(FRESH);
  const server = await (await fetch(`http://127.0.0.1:${FRESH.port}/fixture`)).json();
  // Server-side truth first: the DOM below must belong to a genuinely
  // zero-node, scope-unconfirmed shipment — DOM markers alone prove nothing.
  assert.equal(server.journeyNodes, 0, 'fixture must be zero-node');
  assert.equal(server.serviceScopeConfirmed, false, 'fixture scope must be unconfirmed');
  assert.deepEqual(server.serviceScope, [], 'fixture must carry no service scope');
  assert.equal(server.firstMode, '', 'fixture must carry no mode');
  assert.equal(server.transportLegs, 0, 'fixture must carry no transport legs');
  assert.equal(server.persisted, true);
  ok(`server truth: ${server.shipmentId} persisted v${server.version}, journey.nodes=0, profile=${server.profileState}, scope=[], mode="", legs=0`);

  let browser;
  try {
    browser = await chromium.launch(LAUNCH);
    const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
    const errors = [];
    page.on('pageerror', (e) => errors.push(e.message));
    await openShipment(page, FRESH);

    const cockpit = page.getByTestId('shipment-journey');
    assert.equal(await cockpit.getAttribute('data-empty-journey'), 'true', 'cockpit must render the fresh state');
    ok('cockpit shell rendered for a zero-node shipment (data-empty-journey=true)');

    const phases = await phaseInfo(page);
    assert.equal(phases.length, 6, `expected 6 phases, got ${phases.length}`);
    assert.deepEqual(phases.map((p) => p.spans[1]),
      ['HỒ SƠ', 'ĐẦU ĐI', 'CHẶNG CHÍNH', 'NHẬP KHẨU', 'GIAO HÀNG', 'HOÀN TẤT'], 'six beginner phases');
    ok('six phases visible in order: HỒ SƠ · ĐẦU ĐI · CHẶNG CHÍNH · NHẬP KHẨU · GIAO HÀNG · HOÀN TẤT');

    const profilePhase = phases.find((p) => p.id === 'profile');
    assert.equal(profilePhase.state, 'ACTION', 'HỒ SƠ must be the actionable phase');
    assert.equal(profilePhase.disabled, false, 'HỒ SƠ must be actionable');
    const unknowns = phases.filter((p) => p.id !== 'profile');
    assert.ok(unknowns.every((p) => p.state === 'UNKNOWN' && p.disabled === true), 'downstream phases stay UNKNOWN + inert');
    ok('HỒ SƠ actionable (ACTION); ĐẦU ĐI/CHẶNG CHÍNH/NHẬP KHẨU/GIAO HÀNG/HOÀN TẤT remain UNKNOWN');

    assert.equal(await page.locator('[data-testid^="journey-node-"]').count(), 0, 'no fabricated detailed nodes');
    ok('zero fabricated SEA/ROAD/AIR detailed nodes (no BOOKING/SI-VGM/GATE-IN/Customs/Delivery)');

    assert.ok(await page.getByTestId('journey-empty-canvas').isVisible(), 'empty/onboarding canvas visible');
    assert.ok(await page.getByTestId('journey-side-panel').isVisible(), 'right panel visible');
    assert.ok(await page.getByTestId('journey-quick-panel').isVisible(), 'onboarding Quick Panel visible');
    const side = await box(page, 'journey-side-panel');
    const canvas = await box(page, 'journey-empty-canvas');
    assert.ok(side.x > canvas.x + canvas.width - 2, 'Quick Panel sits on the RIGHT of the canvas');
    ok('onboarding Journey canvas + right-side Quick Panel visible');

    const cta = page.getByTestId('journey-empty-primary-cta');
    assert.equal(await cta.count(), 1, 'exactly one fresh cockpit CTA');
    assert.ok(await cta.isVisible(), 'CTA visible');
    assert.match((await cta.innerText()).trim(), /BỔ SUNG HỒ SƠ/, 'dominant CTA is BỔ SUNG HỒ SƠ');
    const panelText = await page.getByTestId('journey-quick-panel').innerText();
    assert.ok(panelText.includes(server.primaryAction), 'Quick Panel shows the server primary action truthfully');
    ok(`one dominant CTA "BỔ SUNG HỒ SƠ →" bound to the Execution Profile action "${server.primaryAction}"`);

    assert.equal(await page.getByText('Chưa có công đoạn phù hợp').count(), 0, 'old zero-node fallback text is gone');
    ok('old tiny "Chưa có công đoạn phù hợp…" fallback absent from the DOM');

    // The legacy vertical page must not spill open as the default screen.
    assert.equal(await page.getByTestId('journey-global-workspace').count(), 0, 'global workspace closed by default');
    assert.equal(await page.getByTestId('shipment-execution-profile').count(), 0, 'legacy profile editor not auto-opened');
    const cockpitBox = await box(page, 'shipment-journey');
    assert.ok(cockpitBox.width >= 1000, `cockpit is the wide shell (${Math.round(cockpitBox.width)}px wide)`);
    ok(`cockpit is the primary surface (${Math.round(cockpitBox.width)}×${Math.round(cockpitBox.height)}px); legacy workspace stays closed`);

    const off = await shellOffsets(page, ['attention-now', 'shipment-journey', 'shipment-completion-goals']);
    assert.ok(off['attention-now'] < off['shipment-journey'], `Attention above Cockpit (${off['attention-now']} < ${off['shipment-journey']})`);
    assert.ok(off['shipment-journey'] < off['shipment-completion-goals'], `Cockpit above Completion Goals (${off['shipment-journey']} < ${off['shipment-completion-goals']})`);
    const attentionText = await page.getByTestId('attention-now').innerText();
    assert.ok(attentionText.includes(server.primaryAction), 'Attention surfaces the same primary action');
    ok(`composition order in the app scrollport: Attention(y=${off['attention-now']}) → Cockpit(y=${off['shipment-journey']}) → Completion Goals(y=${off['shipment-completion-goals']})`);

    // Default first screen (scrollTop=0): Attention + Cockpit, no legacy surface.
    await scrollShellTop(page);
    const firstScreen = await page.evaluate(() => {
      const shell = document.querySelector('.logi-shell');
      const view = { top: shell.getBoundingClientRect().top, bottom: shell.getBoundingClientRect().bottom };
      const seen = (id) => {
        const el = document.querySelector(`[data-testid="${id}"]`);
        if (!el) return false;
        const r = el.getBoundingClientRect();
        return r.bottom > view.top && r.top < view.bottom;
      };
      return {
        attention: seen('attention-now'), cockpit: seen('shipment-journey'),
        legacyProfile: seen('shipment-execution-profile'), globalWorkspace: seen('journey-global-workspace'),
      };
    });
    assert.deepEqual(firstScreen, { attention: true, cockpit: true, legacyProfile: false, globalWorkspace: false },
      `first screen must be Attention + Cockpit only: ${JSON.stringify(firstScreen)}`);
    ok('default first screen = Attention + Cockpit; the legacy vertical shipment page does NOT spill open');

    await page.screenshot({ path: path.join(outDir, 'fresh-desktop-1-first-screen.png') });
    await page.getByTestId('shipment-journey').screenshot({ path: path.join(outDir, 'fresh-desktop-2-cockpit.png') });
    await page.getByTestId('journey-empty-canvas').screenshot({ path: path.join(outDir, 'fresh-desktop-3-onboarding-canvas.png') });
    await scrollShellTo(page, 'shipment-completion-goals');
    await page.screenshot({ path: path.join(outDir, 'fresh-desktop-4-completion-goals-after-cockpit.png') });
    await scrollShellTop(page);
    ok('desktop 1440×1000 screenshots written (first screen, cockpit, onboarding canvas, goals after cockpit)');

    await noPageOverflow(page, 'fresh 1440');

    // Supervisor B1 — desktop: the dominant CTA must reach the EXISTING
    // Execution Profile editor, not merely be enabled and write-free.
    await cta.click();
    await page.waitForTimeout(250);
    assert.equal(new URL(page.url()).searchParams.get('tab'), 'van-tai',
      'desktop profile CTA must open the tab that owns ShipmentExecutionProfile');
    await page.getByTestId('journey-global-workspace').waitFor({ state: 'visible' });
    await page.getByTestId('shipment-execution-profile').waitFor({ state: 'visible' });
    const desktopProfileInside = await page.evaluate(() =>
      document.querySelector('[data-testid="journey-global-workspace"]')
        ?.contains(document.querySelector('[data-testid="shipment-execution-profile"]')) === true);
    assert.equal(desktopProfileInside, true, 'desktop CTA mounts Execution Profile inside Cockpit Global Workspace');
    ok('desktop BỔ SUNG HỒ SƠ CTA reaches Vận chuyển & Hàng hóa → existing Execution Profile');

    // Reset to the truthful fresh default before the independent 390px challenge.
    await openShipment(page, FRESH);

    // ---------- 390px ----------
    await page.setViewportSize({ width: 390, height: 844 });
    await page.waitForTimeout(150);
    const mPhases = await phaseInfo(page);
    assert.equal(mPhases.length, 6, 'six phases at 390px');
    assert.equal(mPhases.find((p) => p.id === 'profile').state, 'ACTION');
    assert.ok(mPhases.filter((p) => p.id !== 'profile').every((p) => p.state === 'UNKNOWN' && p.disabled));
    const mCta = await box(page, 'journey-empty-primary-cta');
    assert.ok(mCta.x >= -1 && mCta.x + mCta.width <= 391, 'CTA inside 390px viewport');
    assert.ok(await page.getByTestId('journey-empty-canvas').isVisible(), 'canvas visible at 390px');
    assert.ok(await page.getByTestId('journey-quick-panel').isVisible(), 'Quick Panel visible at 390px');
    assert.equal(await page.locator('[data-testid^="journey-node-"]').count(), 0, 'still no fabricated nodes at 390px');
    const mOff = await shellOffsets(page, ['attention-now', 'shipment-journey', 'shipment-completion-goals']);
    assert.ok(mOff['attention-now'] < mOff['shipment-journey'] && mOff['shipment-journey'] < mOff['shipment-completion-goals'],
      '390px keeps Attention → Cockpit → Goals order');
    await noPageOverflow(page, 'fresh 390');
    ok('390px keeps the same semantics (six phases, HỒ SƠ actionable, UNKNOWN downstream, canvas + panel, no overflow)');

    await scrollShellTop(page);
    await page.screenshot({ path: path.join(outDir, 'fresh-mobile-390-1-first-screen.png') });
    await page.getByTestId('shipment-journey').screenshot({ path: path.join(outDir, 'fresh-mobile-390-2-cockpit.png') });
    await scrollShellTo(page, 'journey-empty-primary-cta');
    await page.screenshot({ path: path.join(outDir, 'fresh-mobile-390-3-onboarding-quick-panel.png') });
    await scrollShellTo(page, 'shipment-completion-goals');
    await page.screenshot({ path: path.join(outDir, 'fresh-mobile-390-4-completion-goals-after-cockpit.png') });
    await scrollShellTop(page);
    ok('mobile 390×844 screenshots written (first screen, cockpit, quick panel, goals after cockpit)');

    // Supervisor B1 — 390px: challenge the HỒ SƠ phase itself (same canonical
    // action) and prove the destination, not just the button label.
    await page.getByTestId('journey-phase-profile').click();
    await page.waitForTimeout(250);
    assert.equal(new URL(page.url()).searchParams.get('tab'), 'van-tai',
      '390px HỒ SƠ action must open the tab that owns ShipmentExecutionProfile');
    await page.getByTestId('journey-global-workspace').waitFor({ state: 'visible' });
    await page.getByTestId('shipment-execution-profile').waitFor({ state: 'visible' });
    const mobileProfileInside = await page.evaluate(() =>
      document.querySelector('[data-testid="journey-global-workspace"]')
        ?.contains(document.querySelector('[data-testid="shipment-execution-profile"]')) === true);
    assert.equal(mobileProfileInside, true, '390px HỒ SƠ action mounts Execution Profile inside Cockpit Global Workspace');
    await noPageOverflow(page, 'fresh 390 after profile action');
    ok('390px HỒ SƠ action reaches Vận chuyển & Hàng hóa → existing Execution Profile');

    assert.deepEqual(errors, [], `page errors: ${errors.join(' | ')}`);
    ok('zero application page errors');
    return server;
  } catch (e) {
    console.error(host.err());
    throw e;
  } finally {
    await browser?.close();
    host.host.kill();
  }
}

// ------------------------------------------------------------ populated lane
async function populatedChecks() {
  const host = await startHost(POPULATED);
  let browser;
  try {
    browser = await chromium.launch(LAUNCH);
    const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
    const errors = [];
    page.on('pageerror', (e) => errors.push(e.message));
    await openShipment(page, POPULATED);

    const model = await (await fetch(`http://127.0.0.1:${POPULATED.port}/model`)).json();
    const lot = model.shipments.find((s) => s.id === POPULATED.id);
    assert.equal(await page.locator('[data-testid^="journey-node-"]').count(), 11, 'approved 11-node map');
    assert.equal(lot.journey.nodes.length, 11, 'server truth: 11 detailed nodes');
    ok('approved large horizontal map: 11 factual detailed nodes (DOM == server truth)');

    await page.getByTestId('journey-parallel-branch').waitFor();
    ok('parallel SI/VGM + Gate-in branch rendered');

    const terminal = page.getByText('RÀ SOÁT HOÀN TẤT', { exact: true });
    assert.equal(await terminal.count(), 1, 'one neutral terminal');
    const terminalStyle = await terminal.evaluate((el) => {
      // Chromium 153 reports Tailwind's oklch palette as lab()/oklab(); compare
      // against a same-document slate-500 reference instead of literal rgb()s.
      const ref = document.querySelector('.text-slate-500');
      const white = document.querySelector('[data-testid="shipment-journey"]');
      const c = getComputedStyle(el);
      return {
        border: c.borderTopStyle,
        color: c.color,
        refColor: ref ? getComputedStyle(ref).color : null,
        bg: c.backgroundColor,
        pageBg: white ? getComputedStyle(white).backgroundColor : null,
        cls: el.className,
        text: el.textContent.trim(),
      };
    });
    assert.equal(terminalStyle.border, 'dashed', 'terminal stays the dashed neutral pill');
    assert.equal(terminalStyle.text, 'RÀ SOÁT HOÀN TẤT');
    assert.ok(!/emerald|green|red|amber/.test(terminalStyle.cls), `terminal carries no completion/alert colour class: ${terminalStyle.cls}`);
    assert.equal(terminalStyle.color, terminalStyle.refColor, 'terminal text uses the neutral slate-500 tone');
    assert.ok(
      terminalStyle.bg === terminalStyle.pageBg || /rgba\(0, 0, 0, 0\)|transparent/.test(terminalStyle.bg),
      `terminal has no coloured fill (bg=${terminalStyle.bg}, card=${terminalStyle.pageBg})`);
    const journeyText = await page.getByTestId('shipment-journey').innerText();
    assert.ok(!journeyText.includes('COMPLETED'), 'no fake whole-shipment COMPLETED');
    // The ONLY percentage allowed in the cockpit is the map zoom readout; a
    // percentage standing for shipment progress would be the #186 regression.
    const pctNodes = await page.evaluate(() => [...document.querySelectorAll('[data-testid="shipment-journey"] *')]
      .filter((e) => e.children.length === 0 && /^\d+%$/.test(e.textContent.trim()))
      .map((e) => ({ pct: e.textContent.trim(), inMapControls: !!e.closest('[data-testid^="journey-map"]') })));
    assert.equal(pctNodes.length, 1, `unexpected percentage readouts: ${JSON.stringify(pctNodes)}`);
    assert.ok(pctNodes[0].inMapControls, `the only % is the map zoom control, not a progress claim: ${JSON.stringify(pctNodes)}`);
    const terminalHasPct = await page.evaluate(() => /%|COMPLETED/.test(document.querySelector('[data-testid^="journey-map-rail"], .journey-demo')?.innerText ?? '') &&
      [...document.querySelectorAll('[data-testid="shipment-journey"] span')].some((e) => e.textContent.trim() === 'RÀ SOÁT HOÀN TẤT' && /%|COMPLETED/.test(e.textContent)));
    assert.equal(terminalHasPct, false, 'terminal pill carries no %/COMPLETED claim');
    ok(`B7 stays neutral: dashed slate "RÀ SOÁT HOÀN TẤT", no colour class/fill, no COMPLETED; only % is the map zoom (${pctNodes[0].pct})`);

    await page.getByTestId('journey-node-si-vgm').click();
    const quick = page.getByTestId('journey-quick-panel');
    await quick.waitFor({ state: 'visible' });
    const side = await box(page, 'journey-side-panel');
    const map = await box(page, 'journey-map-viewport');
    assert.ok(side.x > map.x + map.width - 2, 'panel is on the RIGHT of the map');
    await page.getByTestId('journey-open-workspace').click();
    const workspace = page.getByTestId('journey-stage-workspace');
    await workspace.waitFor({ state: 'visible' });
    const sideContains = await page.evaluate(() =>
      document.querySelector('[data-testid="journey-side-panel"]').contains(document.querySelector('[data-testid="journey-stage-workspace"]')));
    assert.ok(sideContains, 'Stage Workspace replaces the Quick Panel inside the right panel');
    assert.equal(await page.locator('[data-testid="journey-quick-panel"]').count(), 1, 'no duplicate Quick Panel');
    ok('right-side Quick Panel → Stage Workspace (exactly one panel column)');

    await page.getByTestId('journey-node-customs-import').click();
    const customs = page.getByTestId('journey-customs-import-panel');
    await customs.waitFor();
    const customsText = await customs.innerText();
    const ciNode = lot.journey.nodes.find((n) => n.id === 'customs-import');
    assert.equal(ciNode.state, 'PROBLEM', 'fixture truth: customs-import has a real blocker to surface');
    const regClearance = await page.getByTestId('ci-registration-clearance').innerText();
    assert.ok(regClearance.includes('Tờ khai (đăng ký)'), 'registration and clearance are separate fields');
    assert.ok(regClearance.includes('Thông quan'), 'clearance is projected separately from registration');
    assert.ok(!/Đã thông quan|HOÀN TẤT|COMPLETED/.test(regClearance), `clearance is never claimed from registration: ${regClearance}`);
    for (const blocker of ciNode.blockers) {
      assert.ok(customsText.includes(blocker), `blocker surfaced verbatim: ${blocker}`);
    }
    assert.ok(customsText.includes('Tạo GNT không đồng nghĩa đã nộp thuế.'), 'tax payment is not inferred from a generated GNT');
    assert.ok((await page.getByTestId('ci-partner-suggested').innerText()).includes('chưa xác nhận đối tác phải trả'), 'suggested partner stays qualified');
    assert.equal(await page.getByTestId('ci-primary-cta').count(), 1, 'exactly one dominant customs CTA');
    const ciCta = (await page.getByTestId('ci-primary-cta').innerText()).trim();
    assert.equal(ciCta, lot.nextLabel, `customs CTA is the ONE canonical primary action label (${ciCta})`);
    assert.ok(customsText.includes(lot.journey.primaryAction.text), 'specialized panel shows the same primary action truth');
    ok(`customs-import truthful panel: registration≠clearance, blocker + tax truth verbatim, qualified partner, ONE dominant CTA "${ciCta}"`);

    const off = await shellOffsets(page, ['attention-now', 'shipment-journey', 'shipment-completion-goals']);
    assert.ok(off['attention-now'] < off['shipment-journey'] && off['shipment-journey'] < off['shipment-completion-goals'],
      'Attention → Cockpit → Completion Goals');
    ok(`composition order preserved: Attention(y=${off['attention-now']}) → Cockpit(y=${off['shipment-journey']}) → Completion Goals(y=${off['shipment-completion-goals']})`);

    // B8 (#186/#187): the finance guest state must be DERIVED from this
    // fixture's real finance facts, never a cosmetic colour.
    const finance = page.getByTestId('completion-goal-finance');
    const financeState = await finance.getAttribute('data-state');
    const financeText = await finance.innerText();
    const outstandingUnknown = lot.finance.outstanding === null || lot.finance.outstanding === undefined;
    const partnerUnresolved = Boolean(lot.finance.partner?.suggested) || (lot.finance.partner?.partners ?? []).length === 0;
    if (outstandingUnknown && partnerUnresolved) {
      assert.equal(financeState, 'UNKNOWN', `B8: unknown finance must stay UNKNOWN, got ${financeState}`);
      assert.ok(/UNKNOWN|Chưa xác định/.test(financeText), 'B8: UNKNOWN is stated verbatim');
      assert.ok(financeText.includes('không đổi thành 0/đã trả'), 'B8: the no-fake-zero rule is stated on the card');
    } else {
      assert.notEqual(financeState, 'EVIDENCED', `B8: open/unknown finance never renders as evidenced (${financeState})`);
    }
    ok(`B8 finance truth: outstanding=${JSON.stringify(lot.finance.outstanding)}, partner.suggested=${Boolean(lot.finance.partner?.suggested)} → goal data-state=${financeState} (never 0/CLOSED)`);

    await scrollShellTo(page, 'shipment-journey');
    await page.screenshot({ path: path.join(outDir, 'populated-desktop-1-map-and-quick-panel.png') });
    await page.getByTestId('shipment-journey').screenshot({ path: path.join(outDir, 'populated-desktop-2-cockpit.png') });
    await page.getByTestId('journey-customs-import-panel').screenshot({ path: path.join(outDir, 'populated-desktop-3-customs-import-panel.png') });
    await scrollShellTo(page, 'shipment-completion-goals');
    await page.screenshot({ path: path.join(outDir, 'populated-desktop-4-completion-goals.png') });
    await scrollShellTop(page);
    await noPageOverflow(page, 'populated 1440');

    await page.setViewportSize({ width: 390, height: 844 });
    await page.waitForTimeout(150);
    assert.equal(await page.locator('[data-testid^="journey-node-"]').count(), 11, '11 nodes at 390px');
    assert.ok(await page.getByTestId('journey-map-viewport').isVisible(), 'map usable at 390px');
    await scrollShellTo(page, 'journey-node-customs-import');
    await page.getByTestId('journey-node-customs-import').click();
    await page.getByTestId('journey-customs-import-panel').waitFor();
    assert.ok(await page.getByTestId('journey-customs-import-panel').isVisible(), 'customs panel readable at 390px');
    await noPageOverflow(page, 'populated 390');
    await page.screenshot({ path: path.join(outDir, 'populated-mobile-390-1-map.png') });
    await page.getByTestId('journey-customs-import-panel').screenshot({ path: path.join(outDir, 'populated-mobile-390-2-customs-panel.png') });
    ok('390px populated: map + customs panel usable, zero horizontal overflow');

    assert.deepEqual(errors, [], `page errors: ${errors.join(' | ')}`);
    ok('zero application page errors');
    return lot;
  } catch (e) {
    console.error(host.err());
    throw e;
  } finally {
    await browser?.close();
    host.host.kill();
  }
}

const summary = { mode, results };
if (mode === 'fresh' || mode === 'all') summary.fresh = await freshChecks();
if (mode === 'populated' || mode === 'all') {
  const lot = await populatedChecks();
  summary.populated = { id: POPULATED.id, journeyNodes: lot.journey.nodes.length, version: lot.version };
}
writeFileSync(path.join(outDir, 'acceptance-188.json'), JSON.stringify(summary, null, 2));
console.log(`PASS journey parity 188 (${mode}): ${results.length} real-browser checks`);
