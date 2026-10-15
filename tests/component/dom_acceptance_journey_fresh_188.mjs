// LOGI #199 follow-up — deterministic zero-node / missing-Journey acceptance.
//
// The zero-node exception uses a full-width map-first chart canvas with a
// compact floating empty-state notice, truthful profile status, no fake nodes,
// and one CTA to the existing Execution Profile editor. This lane mounts the
// current official `component/dist` bundle in jsdom over a fresh-shipment
// projection captured from the canonical `shipment_create` handler on isolated
// mongomock staging, and executes both the nodes=[] and missing-Journey variants.
//
// Usage: node tests/component/dom_acceptance_journey_fresh_188.mjs [fixture.json] [bundle.js] [variant]
// variant: "nodes" (Journey present, nodes=[]) or "absent" (Journey entirely absent).
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
const variant = process.argv[4] || 'nodes';
assert.ok(['nodes', 'absent'].includes(variant), `unknown variant ${variant}`);

// Fixture truth first: this lane only proves anything for a real fresh shipment.
assert.equal(meta.journeyNodes, 0, 'fixture must be a zero-node shipment');
assert.equal(meta.serviceScopeConfirmed, false, 'fixture scope must be unconfirmed');
assert.deepEqual(meta.serviceScope, [], 'fixture must carry no service scope');
assert.equal(meta.firstMode, '', 'fixture must carry no first mode');
assert.equal(meta.transportLegs, 0, 'fixture must carry no transport legs');

const bundleUrl = pathToFileURL(path.resolve(process.argv[3] || path.join(root, 'component/dist/logi-shell.js')));
const label = variant === 'absent' ? 'journey absent' : 'nodes=[]';

{
  const data = structuredClone(fixture.before);
  if (variant === 'absent') {
    for (const s of data.shipments) { if (s.id === meta.shipmentId) delete s.journey; }
  }
  const dom = new JSDOM('<!doctype html><body><div id="host"></div>', { url: 'http://localhost:9502', pretendToBeVisual: true });
  globalThis.window = dom.window; globalThis.document = dom.window.document;
  Object.defineProperty(globalThis, 'navigator', { value: dom.window.navigator, configurable: true });
  for (const k of ['HTMLElement', 'HTMLInputElement', 'HTMLSelectElement', 'HTMLTextAreaElement', 'Event', 'MouseEvent', 'Node', 'MutationObserver', 'getComputedStyle']) globalThis[k] = dom.window[k];
  const reveals = [];
  dom.window.HTMLElement.prototype.scrollIntoView = function () { reveals.push(this.id || this.getAttribute?.('data-testid') || '(anonymous)'); };
  const triggers = [];
  const mount = (await import(bundleUrl)).default;
  mount({ name: 'logi_shell', data, parentElement: document.getElementById('host'), setTriggerValue: (event, value) => triggers.push({ event, value }) });
  const tick = () => new Promise((r) => setTimeout(r, 250));
  const byId = (id) => document.querySelector(`[data-testid="${id}"]`);
  const click = async (el) => { assert.ok(el, 'click target'); el.dispatchEvent(new dom.window.MouseEvent('click', { bubbles: true, cancelable: true })); await tick(); };
  const text = (el) => el.textContent.replace(/\s+/g, ' ').trim();

  await tick();
  await click([...document.querySelectorAll('a')].find((a) => text(a) === 'Lô Hàng'));
  await click(byId('shipment-period-tat-ca'));
  await click([...document.querySelectorAll('main a')].find((a) => text(a) === meta.shipmentId));

  // 1. a truthful zero-node Journey renders one full-width map-first canvas.
  const cockpit = byId('shipment-journey');
  assert.ok(cockpit, `[${label}] journey shell must exist`);
  assert.equal(cockpit.getAttribute('data-empty-journey'), 'true', `[${label}] renders the fresh-shipment state`);
  const zeroMap = byId('journey-zero-map-first');
  assert.ok(zeroMap, `[${label}] full-width zero-node map-first canvas renders`);
  assert.equal(zeroMap.getAttribute('data-layout'), 'full-width', `[${label}] explicit full-width layout contract`);
  assert.equal(zeroMap.style.width, '100%', `[${label}] canvas is not constrained to a left rail`);
  assert.ok(zeroMap.classList.contains('journey-map-first'), `[${label}] uses the existing map-first visual family`);
  assert.equal(zeroMap.classList.contains('journey-split-small-map'), false, `[${label}] old split class is inactive`);
  assert.equal(byId('journey-split-view'), null, `[${label}] no old split-view root`);
  assert.equal(document.querySelector('.journey-split-small-map'), null, `[${label}] no old small-map layout anywhere`);
  assert.equal(byId('journey-zero-panel'), null, `[${label}] no right-side action panel`);
  assert.ok(byId('journey-map-viewport'), `[${label}] reuses the real chart-paper Journey map`);
  assert.equal(byId('journey-map-viewport').closest('[data-testid="journey-zero-map-first"]'), zeroMap,
    `[${label}] chart canvas fills the zero-node map-first surface`);
  assert.ok(byId('journey-empty-map'), `[${label}] floating empty-state notice renders`);
  const viewport = byId('journey-map-viewport');
  const transform = byId('journey-map-transform');
  const transformBeforePointer = transform.style.transform;
  viewport.dispatchEvent(new dom.window.MouseEvent('pointerdown', {
    bubbles: true, cancelable: true, button: 0, clientX: 20, clientY: 20,
  }));
  dom.window.dispatchEvent(new dom.window.MouseEvent('pointermove', {
    bubbles: true, cancelable: true, button: 0, clientX: 140, clientY: 90,
  }));
  dom.window.dispatchEvent(new dom.window.MouseEvent('pointerup', {
    bubbles: true, cancelable: true, button: 0, clientX: 140, clientY: 90,
  }));
  await tick();
  assert.equal(transform.style.transform, transformBeforePointer,
    `[${label}] pointer-down/move over the decorative empty canvas must not pan`);
  assert.ok(text(byId('journey-empty-map')).includes('Chưa có sơ đồ Journey'), `[${label}] empty-state is honest`);
  assert.ok(text(byId('journey-empty-map')).includes('Chưa đủ hồ sơ để xác định công đoạn chi tiết.'),
    `[${label}] explains why the Journey cannot yet be determined`);

  // 2. no compact phase cards or fabricated Journey data; UNKNOWN stays truthful.
  assert.equal(document.querySelectorAll('[data-testid^="journey-macro-step-"]').length, 0, `[${label}] no five-phase cards`);
  assert.equal(byId('journey-phase-strip'), null, `[${label}] no six-phase strip`);
  assert.equal(byId('journey-empty-canvas'), null, `[${label}] no alternate onboarding canvas`);
  assert.equal(byId('journey-quick-panel'), null, `[${label}] no Quick Panel`);
  assert.equal(document.querySelectorAll('[data-testid^="journey-node-"]').length, 0, `[${label}] no fabricated detailed nodes`);
  const toolbar = byId('journey-compact-toolbar');
  assert.ok(toolbar, `[${label}] compact map-first toolbar exists`);
  assert.ok(text(toolbar).includes('📍 Đang ở: Chưa xác định'), `[${label}] current reads Chưa xác định`);
  assert.equal(text(toolbar).includes('Đang ở: HỒ SƠ'), false, `[${label}] never invents a current phase`);

  // 3. missing-profile status and server-projected next action remain visible.
  assert.ok(byId('journey-zero-profile'), `[${label}] profile status card renders`);
  assert.ok(text(byId('journey-zero-profile-state')).includes(meta.profileStateLabel), `[${label}] shows the real missing-profile status`);
  assert.ok(text(byId('journey-zero-profile')).includes(meta.primaryAction), `[${label}] profile card states the server primary action`);

  // 4. exactly ONE primary BỔ SUNG HỒ SƠ CTA, wired to the existing editor.
  const ctas = document.querySelectorAll('[data-testid="journey-zero-primary-cta"]');
  const labelledCtas = [...document.querySelectorAll('button')].filter((button) => /BỔ SUNG HỒ SƠ/.test(text(button)));
  assert.equal(ctas.length, 1, `[${label}] exactly one zero-node profile CTA`);
  assert.equal(labelledCtas.length, 1, `[${label}] exactly one button labelled BỔ SUNG HỒ SƠ`);
  assert.equal(labelledCtas[0], ctas[0], `[${label}] no duplicate profile CTA elsewhere`);
  assert.ok(byId('journey-zero-profile').contains(ctas[0]), `[${label}] CTA belongs to the truthful profile state`);

  // 5. navigation is allowed; zero unauthorized business writes are allowed.
  triggers.length = 0;
  await click(ctas[0]);
  const writes = triggers.filter((t) => t.event !== 'navigate').map((t) => t.event);
  assert.deepEqual(writes, [], `[${label}] CTA must not perform a business write (got ${writes.join(',')})`);
  const editor = byId('shipment-execution-profile');
  assert.ok(editor, `[${label}] CTA mounts the existing Execution Profile editor`);
  const workspace = byId('journey-global-workspace');
  assert.ok(workspace, `[${label}] profile editor is reached through the existing Global Workspace`);
  assert.ok(workspace.contains(editor), `[${label}] editor remains inside the Global Workspace`);

  // 10. composition: Attention → Cockpit → Completion Goals
  const order = ['attention-now', 'shipment-journey', 'shipment-completion-goals'].map((id) => {
    const el = byId(id);
    assert.ok(el, `[${label}] ${id} present`);
    return Array.prototype.indexOf.call(document.querySelectorAll('main [data-testid]'), el);
  });
  assert.ok(order[0] < order[1] && order[1] < order[2], `[${label}] Attention → Cockpit → Completion Goals order`);
}

console.log(`PASS journey fresh 188 zero-node [${label}] (deterministic jsdom): full-width map-first empty state, no fake nodes, truthful profile status, one CTA reaches Execution Profile through Global Workspace, zero business writes`);
process.exit(0);
