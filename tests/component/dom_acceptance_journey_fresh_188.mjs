// Issue #197 follow-up — deterministic zero-node / missing-Journey acceptance.
//
// Owner correction 2026-10-13: no compact five-phase cards anywhere. The
// zero-node view uses the same split language as the populated path — a slim
// empty-map placeholder left, the unchanged action content right — with a
// truthful "Chưa xác định" and one dominant CTA. This lane mounts the exact
// committed `component/dist` bundle in jsdom over a REAL fresh-shipment
// projection (created through the canonical `shipment_create` handler on
// isolated mongomock staging) and executes both the nodes=[] and the
// missing-Journey variants.
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

  // 1. the split-view shell renders for a truthful zero-node Journey
  const cockpit = byId('shipment-journey');
  assert.ok(cockpit, `[${label}] journey shell must exist`);
  assert.equal(cockpit.getAttribute('data-empty-journey'), 'true', `[${label}] renders the fresh-shipment state`);

  // 2. Owner correction 2026-10-13 — no compact five-phase cards anywhere.
  // Left: slim empty-map placeholder. Right: the unchanged action content.
  assert.ok(byId('journey-split-view'), `[${label}] split view renders`);
  assert.ok(byId('journey-empty-map'), `[${label}] empty-map placeholder on the left`);
  assert.ok(text(byId('journey-empty-map')).includes('Chưa có sơ đồ Journey'), `[${label}] placeholder is honest`);
  assert.equal(document.querySelectorAll('[data-testid^="journey-macro-step-"]').length, 0, `[${label}] no five-phase cards`);
  assert.ok(byId('journey-zero-panel'), `[${label}] action panel on the right`);

  // 3. current position is truthful UNKNOWN — never an invented phase
  const toolbar = byId('journey-compact-toolbar');
  assert.ok(toolbar, `[${label}] compact toolbar exists`);
  assert.ok(text(toolbar).includes('📍 Đang ở: Chưa xác định'), `[${label}] current reads Chưa xác định`);
  assert.equal(text(toolbar).includes('Đang ở: HỒ SƠ'), false, `[${label}] never invents a current phase`);

  // 4. no six-phase canvas, no Quick Panel, no fabricated nodes
  assert.equal(byId('journey-phase-strip'), null, `[${label}] no six-phase strip`);
  assert.equal(byId('journey-empty-canvas'), null, `[${label}] no onboarding canvas`);
  assert.equal(byId('journey-quick-panel'), null, `[${label}] no Quick Panel`);
  assert.equal(document.querySelectorAll('[data-testid^="journey-node-"]').length, 0, `[${label}] no fabricated detailed nodes`);

  // 5. exactly ONE dominant action, bound to the Execution Profile next action
  const ctas = document.querySelectorAll('[data-testid="journey-zero-primary-cta"]');
  assert.equal(ctas.length, 1, `[${label}] one dominant fresh-shipment CTA`);
  assert.match(text(ctas[0]), /BỔ SUNG HỒ SƠ/, `[${label}] dominant CTA label`);
  assert.ok(text(byId('journey-zero-profile')).includes(meta.primaryAction), `[${label}] profile card states the server primary action`);

  // 6. the dominant action writes nothing and reaches the Execution Profile editor
  await click(ctas[0]);
  const writes = triggers.filter((t) => t.event !== 'navigate').map((t) => t.event);
  assert.deepEqual(writes, [], `[${label}] CTA must not invent a business write (got ${writes.join(',')})`);
  const editor = byId('shipment-execution-profile');
  assert.ok(editor, `[${label}] CTA mounts the existing Execution Profile editor`);

  // 10. composition: Attention → Cockpit → Completion Goals
  const order = ['attention-now', 'shipment-journey', 'shipment-completion-goals'].map((id) => {
    const el = byId(id);
    assert.ok(el, `[${label}] ${id} present`);
    return Array.prototype.indexOf.call(document.querySelectorAll('main [data-testid]'), el);
  });
  assert.ok(order[0] < order[1] && order[1] < order[2], `[${label}] Attention → Cockpit → Completion Goals order`);
}

console.log(`PASS journey fresh 188 zero-node [${label}] (deterministic jsdom): split view (empty-map placeholder + action panel), current Chua xac dinh, 1 CTA reaching Execution Profile, zero writes`);
process.exit(0);
