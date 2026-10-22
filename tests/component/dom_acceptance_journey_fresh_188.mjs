// Issue #188 deterministic zero-node cockpit acceptance (no browser required).
//
// Root cause C of Issue #188 was that the #186 coverage proved labels EXISTED in
// source but never executed the zero-node render path, so production shipped a
// shipment shape nobody had rendered. This lane mounts the exact committed
// `component/dist` bundle in jsdom over a REAL fresh-shipment projection and
// executes that path deterministically.
//
// The fixture is not hand-written: regenerate it with
//   python scripts/verify_journey_fresh_parity_188.py \
//     --dump-model tests/component/fixtures/view_model_journey_fresh_188.json
// which creates the shipment through the canonical `shipment_create` handler on
// isolated mongomock staging and fails closed unless the persisted shipment is
// genuinely zero-node / scope-unconfirmed.
//
// Usage: node tests/component/dom_acceptance_journey_fresh_188.mjs [fixture.json] [bundle.js]
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { fileURLToPath, pathToFileURL } from 'node:url';
import path from 'node:path';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const require = createRequire(path.join(root, 'component/package.json'));
const { JSDOM } = require('jsdom');
const fixturePath = process.argv[2] || path.join(root, 'tests/component/fixtures/view_model_journey_fresh_188.json');
const fixture = JSON.parse(readFileSync(fixturePath, 'utf8'));
const meta = fixture.meta || {};

// Fixture truth first: this lane only proves anything for a real fresh shipment.
assert.equal(meta.journeyNodes, 0, 'fixture must be a zero-node shipment');
assert.equal(meta.serviceScopeConfirmed, false, 'fixture scope must be unconfirmed');
assert.deepEqual(meta.serviceScope, [], 'fixture must carry no service scope');
assert.equal(meta.firstMode, '', 'fixture must carry no first mode');
assert.equal(meta.transportLegs, 0, 'fixture must carry no transport legs');

const dom = new JSDOM('<!doctype html><body><div id="host"></div>', { url: 'http://localhost:9502', pretendToBeVisual: true });
globalThis.window = dom.window; globalThis.document = dom.window.document;
Object.defineProperty(globalThis, 'navigator', { value: dom.window.navigator, configurable: true });
for (const k of ['HTMLElement', 'HTMLInputElement', 'HTMLSelectElement', 'HTMLTextAreaElement', 'Event', 'MouseEvent', 'Node', 'MutationObserver', 'getComputedStyle']) globalThis[k] = dom.window[k];
// Supervisor B1 — record every anchored reveal target so this lane can prove
// the reveal lands on the MOUNTED editor (Issue #190 removed the workspace-tabs fallback).
const reveals = [];
dom.window.HTMLElement.prototype.scrollIntoView = function () { reveals.push(this.id || this.getAttribute?.('data-testid') || '(anonymous)'); };
// The app routes inside a MemoryRouter (component/src/App.tsx): the query tab
// never reaches window.location. The truthful observation point is the DOM —
// the pressed tab inside the Global Workspace.
const TAB_BY_LABEL = { 'Thông tin': 'van-tai', 'Xuất khẩu': 'lay-hang', 'Nhập & Giao': 'nhap', 'Chứng từ': 'chung-tu', 'Tài chính': 'tai-chinh', 'Lịch sử': 'lich-su' };

const triggers = [];
const mount = (await import(pathToFileURL(path.resolve(process.argv[3] || path.join(root, 'component/dist/logi-shell.js'))))).default;
mount({ name: 'logi_shell', data: fixture.before, parentElement: document.getElementById('host'), setTriggerValue: (event, value) => triggers.push({ event, value }) });
const tick = (ms = 250) => new Promise((r) => setTimeout(r, ms));
const byId = (id) => document.querySelector(`[data-testid="${id}"]`);
const click = async (el) => { assert.ok(el, 'click target'); el.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true })); await tick(); };
const text = (el) => el.textContent.replace(/\s+/g, ' ').trim();
const waitFor = async (fn, ms = 4000) => {
  const deadline = Date.now() + ms;
  while (Date.now() < deadline) {
    const val = fn();
    if (val) return val;
    await tick(50);
  }
  return fn();
};

await tick();
await click([...document.querySelectorAll('a')].find((a) => text(a) === 'Lô Hàng'));
await click(await waitFor(() => byId('shipment-period-tat-ca')));
await click(await waitFor(() => [...document.querySelectorAll('main a')].find((a) => text(a) === meta.shipmentId)));

// 1. the approved map-first Journey shell survives a truthful zero-node Journey
const cockpit = await waitFor(() => byId('shipment-journey'));
assert.ok(
  cockpit,
  `cockpit shell must exist for journey.nodes=[] (mounted testids: ${[...document.querySelectorAll('[data-testid]')].map((e) => e.getAttribute('data-testid')).join(',')})`
);
assert.equal(cockpit.getAttribute('data-empty-journey'), 'true', 'cockpit renders the fresh-shipment state');
const mapFirst = byId('journey-zero-map-first');
assert.ok(mapFirst, 'zero-node map-first container exists');
assert.ok(mapFirst.classList.contains('journey-map-first'), 'uses map-first layout class');
assert.equal(mapFirst.getAttribute('data-layout'), 'full-width', 'map-first shell is full-width');
assert.ok(byId('journey-map-viewport'), 'JourneyMap viewport is mounted inside zero-node shell');
assert.ok(byId('journey-sea-chart'), 'Vietnam East Sea chart background is mounted');

// 2. truthful unknown position in compact toolbar + profile status overlay (no legacy 6-phase strip)
assert.equal(byId('journey-phase-strip'), null, 'legacy six-phase strip is superseded by map-first ZeroNodeJourney');
const toolbar = byId('journey-compact-toolbar');
assert.ok(toolbar, 'compact toolbar exists in zero-node focus row');
assert.ok(text(toolbar).includes('Đang ở: Chưa xác định'), 'toolbar states unknown current position');
assert.ok(text(toolbar).includes('Chưa đủ hồ sơ để xác định công đoạn chi tiết.'), 'toolbar states why detailed stages are absent');
const emptyMap = byId('journey-empty-map');
assert.ok(emptyMap, 'empty-map notice overlay exists');
assert.equal(emptyMap.getAttribute('role'), 'status', 'empty-map notice is a status region');
assert.equal(text(byId('journey-zero-profile-state')), 'Hồ sơ lô còn thiếu', 'profile state label is shown');

// 3. no fabricated detailed nodes anywhere in the Journey shell
assert.equal(document.querySelectorAll('[data-testid^="journey-node-"]').length, 0, 'no fabricated detailed nodes');
assert.equal(byId('journey-parallel-branch'), null, 'no fabricated SI/VGM + Gate-in group');
assert.equal(document.querySelectorAll('svg path.journey-edge').length, 0, 'no fabricated edges');

// 4. exactly ONE dominant action, bound to the Execution Profile next action
const ctas = document.querySelectorAll('[data-testid="journey-zero-primary-cta"]');
assert.equal(ctas.length, 1, 'one dominant fresh-shipment CTA');
assert.match(text(ctas[0]), /BỔ SUNG HỒ SƠ/, 'dominant CTA label');
assert.equal(text(byId('journey-zero-next-action')), meta.primaryAction, 'zero-node card states the server primary action');
assert.ok(text(byId('journey-zero-profile')).includes(meta.nextActionDetail), 'missing profile facts are stated verbatim');

// 5. the removed legacy fallback must not come back
assert.equal(document.body.textContent.includes('Chưa có công đoạn phù hợp'), false, 'legacy zero-node fallback text is gone');
assert.equal(byId('journey-global-workspace'), null, 'global workspace stays closed by default');

// 6. composition: Attention → Journey → Completion Goals
const order = ['attention-now', 'shipment-journey', 'shipment-completion-goals'].map((id) => {
  const el = byId(id);
  assert.ok(el, `${id} present`);
  return Array.prototype.indexOf.call(document.querySelectorAll('main [data-testid]'), el);
});
assert.ok(order[0] < order[1] && order[1] < order[2], `Attention → Journey → Completion Goals order (${order.join(' < ')})`);
assert.ok(text(byId('attention-now')).includes(meta.primaryAction), 'Attention surfaces the same primary action');

// 7. reading the fresh cockpit, and running its dominant action, writes nothing
assert.equal(triggers.filter((t) => t.event !== 'navigate').length, 0, 'no business write on load');
await click(ctas[0]);
const writes = triggers.filter((t) => t.event !== 'navigate').map((t) => t.event);
assert.deepEqual(writes, [], `fresh-shipment CTA must not invent a business write (got ${writes.join(',')})`);

// Supervisor B1: "actionable" means the click reaches the existing profile
// editor, not merely that a button is enabled and write-free. The tab lives in
// the MemoryRouter search state, so assert it through the rendered DOM truth.
const workspace = await waitFor(() => byId('journey-global-workspace'));
assert.ok(workspace, 'profile CTA opens the Cockpit global workspace');
const pressed = [...workspace.querySelectorAll('button[aria-pressed="true"]')];
assert.equal(pressed.length, 1, 'exactly one selected Global Workspace tab');
assert.equal(TAB_BY_LABEL[text(pressed[0])], 'van-tai',
  'profile CTA must open the tab that owns ShipmentExecutionProfile');
const editor = byId('shipment-execution-profile');
assert.ok(editor, 'profile CTA must mount the existing Execution Profile editor');
assert.ok(workspace.contains(editor), 'profile editor must mount INSIDE the Global Workspace');
await waitFor(() => reveals.includes('shipment-execution-profile'), 1000);
assert.equal(reveals[reveals.length - 1], 'shipment-execution-profile',
  `anchored reveal must land on the mounted editor after the tab mount, got ${JSON.stringify(reveals)}`);

console.log(`PASS journey fresh 188 (deterministic jsdom): ZeroNodeJourney map-first shell kept, 0 fabricated nodes, CTA reaches Execution Profile on tab=van-tai inside Global Workspace with post-mount reveal, zero writes`);
process.exit(0);
