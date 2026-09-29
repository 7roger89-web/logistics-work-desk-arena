// Real committed bundle + canonical isolated backend fixtures. See generator.
import { readFileSync } from "node:fs";
import assert from "node:assert/strict";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const require = createRequire(path.join(ROOT, "component/package.json"));
const { JSDOM } = require("jsdom");
const FIX = JSON.parse(
  readFileSync(path.join(ROOT, "tests/component/fixtures/view_model_contract_workflow.json"), "utf8")
);

const dom = new JSDOM("<!DOCTYPE html><html><body></body></html>", {
  url: "http://localhost:8501/",
  pretendToBeVisual: true,
});
const { window } = dom;

globalThis.window = window;
globalThis.document = window.document;
try {
  Object.defineProperty(globalThis, "navigator", { value: window.navigator, configurable: true });
} catch {
  /* keep node navigator */
}
for (const k of [
  "HTMLElement", "HTMLInputElement", "HTMLTextAreaElement", "HTMLSelectElement",
  "HTMLAnchorElement", "Event", "CustomEvent", "MouseEvent", "KeyboardEvent",
  "Node", "MutationObserver", "getComputedStyle",
]) {
  globalThis[k] = window[k];
}
if (!globalThis.MessageChannel) globalThis.MessageChannel = window.MessageChannel;
window.HTMLElement.prototype.scrollIntoView = () => {};

const tick = (ms = 60) => new Promise((r) => setTimeout(r, ms));
const $ = (sel, root = window.document) => [...root.querySelectorAll(sel)];
const text = (el) => (el.textContent || "").replace(/\s+/g, " ").trim();
const mainText = () => text($("main")[0] ?? window.document.body);
const byTestId = (id) => $(`[data-testid="${id}"]`)[0] ?? null;
const attr = (id, name) => byTestId(id)?.getAttribute(name) ?? null;

function findClickable(needle, sel = "a,button", root = window.document) {
  const els = $(sel, root);
  return els.find((el) => text(el) === needle) || els.find((el) => text(el).includes(needle)) || null;
}

async function click(needle, sel = "a,button", root = window.document) {
  const el = findClickable(needle, sel, root) ?? (sel === "button" ? byTestId(needle) : null);
  assert.ok(el, `clickable "${needle}" not found`);
  el.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
  await tick();
  return el;
}

async function clickTestId(id) {
  const el = byTestId(id);
  assert.ok(el, `element [data-testid="${id}"] not found`);
  el.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
  await tick();
  return el;
}

async function type(input, value) {
  const proto = input.tagName === "TEXTAREA" ? window.HTMLTextAreaElement.prototype : window.HTMLInputElement.prototype;
  Object.getOwnPropertyDescriptor(proto, "value").set.call(input, value);
  input.dispatchEvent(new window.Event("input", { bubbles: true }));
  await tick();
}

let passed = 0;
function ok(name) {
  passed += 1;
  console.log(`  ✓ ${name}`);
}

/** Rewrite the fixture outcome's requestId to the one the real click produced. */
function withRequestId(state, requestId) {
  const clone = structuredClone(state);
  for (const w of clone.lastWrites ?? []) w.requestId = requestId;
  return clone;
}

const host = window.document.createElement("div");
window.document.body.appendChild(host);
const triggers = [];
const mountRef = { current: null };
let lastInvokeCleanup = null;

function invoke(data) {
  if (lastInvokeCleanup) lastInvokeCleanup();
  const cleanup = mountRef.current({
    name: "logi_shell",
    data,
    parentElement: host,
    setTriggerValue: (event, value) => triggers.push({ event, value }),
  });
  lastInvokeCleanup = cleanup;
  return cleanup;
}

/** Deliver a fresh view-model to the SAME mounted page — exactly what a
 *  Streamlit rerun does: no unmount, so route and local state survive and only
 *  the data channel updates. The outcome of a write must arrive this way,
 *  otherwise the page that is waiting for it is gone. */
function deliver(data) {
  mountRef.current({
    name: "logi_shell",
    data,
    parentElement: host,
    setTriggerValue: (event, value) => triggers.push({ event, value }),
  });
}

const CID = '05/2026/HDMB';
const baseline = process.env.BASELINE_BUNDLE;
mountRef.current = (await import(baseline || process.env.BUNDLE_PATH || path.join(ROOT, 'component/dist/logi-shell.js'))).default;
async function contracts(state) {
  invoke(state); await tick(120);
  await click('Hợp đồng', 'a', $('aside')[0]);
}
await contracts(FIX.success);
if (baseline) {
  const anchor = findClickable(CID, 'a', $('main')[0]);
  assert.equal(anchor.getAttribute('href'), '/hop-dong/05/2026/HDMB');
  await click(CID, 'a', $('main')[0]);
  assert.ok(mainText().includes('Sắp có'));
  console.log('PASS baseline: raw slash path → wildcard Sắp có');
  process.exit(0);
}
for (const id of FIX.ids) {
  await contracts(FIX.success);
  const links = $('main a').filter(a => a.getAttribute('href') === '/hop-dong/' + encodeURIComponent(id));
  assert.equal(links.length, 3, 'desktop ID/open + mobile open must all be encoded');
  await click(id, 'a', $('main')[0]);
  assert.equal(text($('main h1')[0]), id, 'exact canonical identity resolves');
  assert.ok(!mainText().includes('Không tìm thấy hợp đồng'));
}
ok('6 backend-permitted IDs resolve exactly, including literal %2F');

async function form(state = FIX.initial) {
  await contracts(state);
  await click('Tạo hợp đồng', 'a', $('main')[0]);
  await type($('input[placeholder="VD: HDMB-0310"]')[0], CID);
  await clickTestId('contract-customer-picker-toggle');
  await type(byTestId('contract-customer-picker-search'), 'An Phát');
  await clickTestId('contract-customer-picker-option-CUST-ANPHAT');
}
function createButton() { return findClickable('TẠO HỢP ĐỒNG', 'button'); }
async function send() {
  const before = triggers.length;
  await click('TẠO HỢP ĐỒNG', 'button');
  const emitted = triggers.slice(before).filter(t => t.event === 'contract_create');
  assert.equal(emitted.length, 1);
  assert.ok(emitted[0].value.payload.requestId);
  assert.ok(byTestId('contract-create-pending'));
  assert.equal(createButton().disabled, true);
  await click('TẠO HỢP ĐỒNG', 'button');
  assert.equal(triggers.length, before + 1, 'disabled button must not resend');
  return emitted[0].value.payload.requestId;
}
for (const failure of FIX.failures) {
  await form(FIX.success); // preexisting contract is the adversarial duplicate scenario
  const rid = await send();
  deliver({...FIX.success, lastWrites: [{...failure, requestId: 'UNRELATED'}]});
  await tick();
  assert.ok(byTestId('contract-create-pending'), 'unrelated outcome/readback cannot navigate');
  deliver({...FIX.success, lastWrites: [{...failure, requestId: rid}]});
  await tick();
  assert.equal(text(byTestId('contract-create-error')), failure.error);
  assert.ok(createButton() && !createButton().disabled);
  assert.ok(!byTestId('contract-create-pending'));
}
ok('duplicate/RBAC/validation/writer false/exception: stays on form, backend refusal displayed');
await form();
const rid = await send();
deliver({...FIX.initial, lastWrites: FIX.success.lastWrites.map(w => ({...w, requestId: rid}))});
await tick();
assert.ok(byTestId('contract-create-pending'), 'ok without fresh contract cannot navigate');
const beforeDelivery = triggers.length;
deliver(withRequestId(FIX.success, rid));
await tick();
assert.equal(text($('main h1')[0]), CID);
assert.equal(triggers.length, beforeDelivery, 'effect must never redispatch');
assert.ok(mainText().includes('Danh tính pháp lý'));
for (const [tab, panel] of [['Hàng hóa hợp đồng', 'Mô tả hàng hóa'], ['Chứng từ HDNT/PL/HDMB', 'Chứng từ HDNT · PL · HDMB'], ['Lô liên kết', 'Lô hàng liên kết'], ['Tổng quan', 'Danh tính pháp lý']]) {
  await click(tab, 'button', $('main')[0]);
  assert.ok(mainText().includes(panel), `actual ${tab} panel rendered`);
  assert.equal(text($('main h1')[0]), CID);
  assert.ok(!mainText().includes('Không tìm thấy hợp đồng'));
}
ok('authoritative success + fresh readback navigates without remount; all 4 tabs accessible');

// Missing transport is not a business success.
await form();
mountRef.current({name: 'logi_shell', data: FIX.initial, parentElement: host, setTriggerValue: null});
await tick();
const disconnectedBefore = triggers.length;
await click('TẠO HỢP ĐỒNG', 'button');
assert.equal(triggers.length, disconnectedBefore);
assert.ok(text(byTestId('contract-create-error')).includes('Không gửi được'));
assert.ok(createButton() && !createButton().disabled);
ok('transport unavailable: no navigation, no success, connection error');

// Both search surfaces use the real encoded navigation callback.
for (const mobile of [false, true]) {
  invoke(FIX.success); await tick(120);
  if (mobile) {
    const toggle = $('header button').find(b => b.getAttribute('aria-label') === 'Tìm kiếm');
    assert.ok(toggle, 'mobile search toggle');
    toggle.click(); await tick();
  }
  const inputs = $('input').filter(i => i.placeholder.includes('Tìm mã lô'));
  const input = mobile ? inputs.at(-1) : inputs[0];
  input.dispatchEvent(new window.FocusEvent('focusin', {bubbles: true}));
  await type(input, CID);
  const result = $('button').find(b => text(b).includes(CID) && text(b).includes('Hợp đồng —'));
  assert.ok(result, 'contract search result');
  result.click(); await tick();
  assert.equal(text($('main h1')[0]), CID);
}
ok('desktop and mobile contract search reach exact slash ID');

// Fault injection only: one existing shipment carries a slash-shaped identity
// AND the stale backend-composed route an older payload would have sent for it.
//
// LOGI_SHIPMENT_SLASH_ROUTE_REPAIR_01 (Issue #138): the app-built link must now
// be ONE encoded segment and must open the real lot (this very step used to be
// the only in-app path that reached the App wildcard, because `/lo-hang/<id>`
// was concatenated raw). The wildcard behaviour it originally guarded is still
// challenged here through the ONE genuinely reachable malformed target that
// remains: a backend-composed route string (`nextRoute`) that the UI passes
// through verbatim — exactly the stale-route shape the shell must survive.
const broken = structuredClone(FIX.initial);
broken.shipments[0].id = 'BROKEN/ROUTE';
broken.shipments[0].nextRoute = '/lo-hang/BROKEN/ROUTE?tab=van-tai'; // pre-fix backend shape
invoke(broken); await tick(120);
await click('Lô Hàng', 'a', $('aside')[0]);
const slashLink = $('main a').find(a => text(a) === 'BROKEN/ROUTE');
assert.ok(slashLink, 'slash shipment link present in the list');
assert.equal(slashLink.getAttribute('href'), '/lo-hang/BROKEN%2FROUTE', 'one encoded segment');
slashLink.dispatchEvent(new window.MouseEvent('click', { bubbles: true, cancelable: true }));
await tick(140);
assert.ok(!byTestId('not-found'), 'a slash identity must NOT fall to the App wildcard');
assert.equal(text($('main h1')[0]), 'BROKEN/ROUTE', 'the exact identity resolves on the real lot page');
ok('slash shipment identity → one encoded segment → real ShipmentDetail (never wildcard)');

const stale = structuredClone(broken);
invoke(stale); await tick(120);
await click('Lô Hàng', 'a', $('aside')[0]);
await click('XỬ LÝ', 'a');
assert.ok(byTestId('not-found'), 'a stale backend-composed multi-segment route still hits the wildcard');
assert.ok(!mainText().includes('Sắp có'));
for (const target of ['/', '/hop-dong', '/lo-hang']) {
  assert.ok($('[data-testid="not-found"] a').some(a => a.getAttribute('href') === target));
}
ok('malformed route → truthful NotFound with three safe destinations');
if (lastInvokeCleanup) lastInvokeCleanup();
console.log(`PASS contract workflow (${passed} groups)`);
process.exit(0);
