// LOGI-197 — zero-node -> populated transition hook-ordering regression.
//
// Mounts the REAL ShipmentJourney component (same mounted instance), first
// with zero Journey nodes, then re-renders with a populated Journey for the
// SAME shipment id. If the zero-node early return skipped Hooks that the
// populated path calls, React throws
// "Rendered more hooks than during the previous render" and unmounts.
//
// Usage:
//   1. Build the test bundle (one command):
//      cd component && ./node_modules/.bin/vite build -c ../tests/component/vite.hook-test.config.cjs
//   2. node tests/component/dom_hook_transition_197.mjs [fixture.json] [test-bundle.js]
// Defaults: tests/component/fixtures/view_model_journey_fresh_188.json and
// tests/component/dist-test/hook-transition-test.js.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { fileURLToPath, pathToFileURL } from 'node:url';
import path from 'node:path';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const require = createRequire(path.join(root, 'component/package.json'));
const { JSDOM } = require('jsdom');
const fixture = JSON.parse(readFileSync(process.argv[2] || path.join(root, 'tests/component/fixtures/view_model_journey_fresh_188.json'), 'utf8'));
const meta = fixture.meta || {};
const bundleUrl = pathToFileURL(path.resolve(process.argv[3] || path.join(root, 'tests/component/dist-test/hook-transition-test.js')));

assert.equal(meta.journeyNodes, 0, 'fixture must be a zero-node shipment');
const zeroShip = structuredClone(fixture.before.shipments.find((s) => s.id === meta.shipmentId));
assert.ok(zeroShip, 'SEA-188 must exist in fixture');
assert.equal(zeroShip.journey.nodes.length, 0, 'base shipment must be zero-node');

// Same shipment, now with a populated Journey (one node per macro region).
const node = (id, label, extra = {}) => ({
  id, label, family: 'sea', targetTab: 'van-tai',
  completed: false, state: 'UPCOMING', factState: '', evidence: '', deadline: '',
  owned: true, current: false, blockers: [], dependencies: [],
  documentCategories: [], documentIds: [], ...extra,
});
const populatedShip = structuredClone(zeroShip);
populatedShip.journey = {
  ...structuredClone(zeroShip.journey),
  nodes: [
    node('booking', 'Đặt chỗ', { state: 'COMPLETED', completed: true }),
    node('on-board', 'Lên tàu', { state: 'CURRENT', current: true }),
    node('customs-import', 'Thông quan nhập khẩu'),
    node('delivery', 'Giao hàng'),
  ],
  modules: [],
  currentStageId: 'on-board',
};

const dom = new JSDOM('<!doctype html><body><div id="host"></div>', { url: 'http://localhost:9502', pretendToBeVisual: true, runScripts: 'dangerously' });
globalThis.window = dom.window; globalThis.document = dom.window.document;
Object.defineProperty(globalThis, 'navigator', { value: dom.window.navigator, configurable: true });
for (const k of ['HTMLElement', 'Event', 'MouseEvent', 'Node', 'MutationObserver', 'getComputedStyle']) globalThis[k] = dom.window[k];

const errors = [];
dom.window.addEventListener('error', (e) => errors.push(String(e.message || e.error)));
const origConsoleError = console.error;
console.error = (...a) => { errors.push(a.map(String).join(' ')); origConsoleError(...a); };

const bundlePath = path.resolve(process.argv[3] || path.join(root, 'tests/component/dist-test/hook-transition-test.js'));
const bundleSrc = readFileSync(bundlePath, 'utf8');
const script = document.createElement('script');
script.textContent = bundleSrc;
document.head.appendChild(script);
const { renderJourney } = dom.window.hookTransition;
assert.equal(typeof renderJourney, 'function', 'test bundle must expose renderJourney');
const tick = () => new Promise((r) => setTimeout(r, 300));
const byId = (id) => document.querySelector(`[data-testid="${id}"]`);
const text = (el) => (el ? el.textContent.replace(/\s+/g, ' ').trim() : '');

// Phase 1 — zero-node mount.
renderJourney(document.getElementById('host'), zeroShip);
await tick(); await tick();
let shell = byId('shipment-journey');
assert.ok(shell, 'zero-node: journey shell must mount');
assert.equal(shell.getAttribute('data-empty-journey'), 'true', 'zero-node: renders the empty state');
assert.ok(text(byId('journey-compact-toolbar')).includes('Chưa xác định'), 'zero-node: truthful UNKNOWN');
assert.ok(byId('journey-empty-map'), 'zero-node: empty-map placeholder');
assert.ok(byId('journey-zero-panel'), 'zero-node: action panel');

// Phase 2 — SAME mounted instance, populated Journey.
errors.length = 0;
renderJourney(document.getElementById('host'), populatedShip);
await tick(); await tick();

const hookErr = errors.find((m) => /more hooks than|fewer hooks than/i.test(m));
assert.equal(hookErr, undefined, `no React hook-ordering crash on zero->populated transition (got: ${hookErr || 'none'})`);

shell = byId('shipment-journey');
assert.ok(shell, 'populated: journey shell must still be mounted (no crash-unmount)');
assert.notEqual(shell.getAttribute('data-empty-journey'), 'true', 'populated: must NOT render the empty state');
assert.ok(byId('journey-split-view'), 'populated: split view renders');
assert.ok(byId('journey-map-viewport'), 'populated: map viewport mounted');
const toolbar = text(byId('journey-compact-toolbar'));
assert.ok(toolbar.includes('Chặng chính'), `populated: real current position from Journey (got: ${toolbar.slice(0, 80)})`);
assert.equal(toolbar.includes('Chưa xác định'), false, 'populated: no stale UNKNOWN');

console.error = origConsoleError;
console.log('HOOK_TRANSITION_197: PASS — zero->populated on the same mounted instance, no hook-ordering crash, correct split-view render.');

// Phase 3 — reverse: populated -> zero on the SAME mounted instance.
errors.length = 0;
console.error = (...a) => { errors.push(a.map(String).join(' ')); origConsoleError(...a); };
renderJourney(document.getElementById('host'), zeroShip);
await tick(); await tick();
const hookErr2 = errors.find((m) => /more hooks than|fewer hooks than/i.test(m));
assert.equal(hookErr2, undefined, `no React hook-ordering crash on populated->zero transition (got: ${hookErr2 || 'none'})`);
shell = byId('shipment-journey');
assert.ok(shell, 'zero-again: journey shell must still be mounted');
assert.equal(shell.getAttribute('data-empty-journey'), 'true', 'zero-again: renders the empty state again');
assert.ok(text(byId('journey-compact-toolbar')).includes('Chưa xác định'), 'zero-again: truthful UNKNOWN again');
console.error = origConsoleError;
console.log('HOOK_TRANSITION_197: PASS — populated->zero reverse transition also clean.');
