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
dom.window.HTMLElement.prototype.scrollIntoView = () => {};

const triggers = [];
const mount = (await import(pathToFileURL(path.resolve(process.argv[3] || path.join(root, 'component/dist/logi-shell.js'))))).default;
mount({ name: 'logi_shell', data: fixture.before, parentElement: document.getElementById('host'), setTriggerValue: (event, value) => triggers.push({ event, value }) });
const tick = () => new Promise((r) => setTimeout(r, 250));
const byId = (id) => document.querySelector(`[data-testid="${id}"]`);
const click = async (el) => { assert.ok(el, 'click target'); el.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true })); await tick(); };
const text = (el) => el.textContent.replace(/\s+/g, ' ').trim();

await tick();
await click([...document.querySelectorAll('a')].find((a) => text(a) === 'Lô Hàng'));
await click(byId('shipment-period-tat-ca'));
await click([...document.querySelectorAll('main a')].find((a) => text(a) === meta.shipmentId));

// 1. the approved cockpit shell survives a truthful zero-node Journey
const cockpit = byId('shipment-journey');
assert.ok(cockpit, 'cockpit shell must exist for journey.nodes=[]');
assert.equal(cockpit.getAttribute('data-empty-journey'), 'true', 'cockpit renders the fresh-shipment state');
assert.equal(document.querySelector('.journey-canvas') !== null || byId('journey-empty-canvas') !== null, true);

// 2. six universal phases, HỒ SƠ actionable, downstream UNKNOWN and inert
const phases = [...document.querySelectorAll('[data-testid^="journey-phase-"]')].filter((e) => e.dataset.testid !== 'journey-phase-strip');
assert.equal(phases.length, 6, `six phases, got ${phases.length}`);
const labels = phases.map((p) => p.querySelectorAll('span')[1].textContent.trim());
assert.deepEqual(labels, ['HỒ SƠ', 'ĐẦU ĐI', 'CHẶNG CHÍNH', 'NHẬP KHẨU', 'GIAO HÀNG', 'HOÀN TẤT'], 'exact beginner phase labels');
const profile = phases.find((p) => p.dataset.testid === 'journey-phase-profile');
assert.equal(profile.dataset.state, 'ACTION', 'HỒ SƠ is the actionable phase');
assert.equal(profile.disabled, false, 'HỒ SƠ is actionable');
for (const p of phases.filter((p) => p !== profile)) {
  assert.equal(p.dataset.state, 'UNKNOWN', `${p.dataset.testid} stays UNKNOWN`);
  assert.equal(p.disabled, true, `${p.dataset.testid} is inert until authority exists`);
}

// 3. no fabricated detailed nodes anywhere in the cockpit
assert.equal(document.querySelectorAll('[data-testid^="journey-node-"]').length, 0, 'no fabricated detailed nodes');
assert.equal(byId('journey-parallel-branch'), null, 'no fabricated SI/VGM + Gate-in group');
const empty = byId('journey-empty-canvas');
assert.ok(empty, 'empty/onboarding canvas exists');
assert.ok(byId('journey-side-panel').contains(byId('journey-quick-panel')), 'right onboarding Quick Panel exists');

// 4. exactly ONE dominant action, bound to the Execution Profile next action
const ctas = document.querySelectorAll('[data-testid="journey-empty-primary-cta"]');
assert.equal(ctas.length, 1, 'one dominant fresh-shipment CTA');
assert.match(text(ctas[0]), /BỔ SUNG HỒ SƠ/, 'dominant CTA label');
assert.ok(text(byId('journey-quick-panel')).includes(meta.primaryAction), 'Quick Panel states the server primary action');
assert.ok(text(byId('journey-empty-profile-issues')).includes(meta.nextActionDetail), 'missing profile facts are stated verbatim');

// 5. the removed legacy fallback must not come back
assert.equal(document.body.textContent.includes('Chưa có công đoạn phù hợp'), false, 'legacy zero-node fallback text is gone');
assert.equal(byId('journey-global-workspace'), null, 'global workspace stays closed by default');

// 6. composition: Attention → Cockpit → Completion Goals
const order = ['attention-now', 'shipment-journey', 'shipment-completion-goals'].map((id) => {
  const el = byId(id);
  assert.ok(el, `${id} present`);
  return Array.prototype.indexOf.call(document.querySelectorAll('main [data-testid]'), el);
});
assert.ok(order[0] < order[1] && order[1] < order[2], `Attention → Cockpit → Completion Goals order (${order.join(' < ')})`);
assert.ok(text(byId('attention-now')).includes(meta.primaryAction), 'Attention surfaces the same primary action');

// 7. reading the fresh cockpit, and running its dominant action, writes nothing
assert.equal(triggers.filter((t) => t.event !== 'navigate').length, 0, 'no business write on load');
await click(ctas[0]);
const writes = triggers.filter((t) => t.event !== 'navigate').map((t) => t.event);
assert.deepEqual(writes, [], `fresh-shipment CTA must not invent a business write (got ${writes.join(',')})`);

console.log(`PASS journey fresh 188 (deterministic jsdom): shell kept, 6 phases (HỒ SƠ ACTION, 5 UNKNOWN), 0 fabricated nodes, 1 CTA, Attention → Cockpit → Goals, zero writes`);
process.exit(0);
