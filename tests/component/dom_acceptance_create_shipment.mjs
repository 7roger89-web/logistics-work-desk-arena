// ============================================================================
// LOGI_REAL_USE_CREATE_SHIPMENT_AGENT_MASTER_01 — DOM/navigation acceptance
// for the REAL "Tạo Lô Mới" flow (/tao-lo-moi).
//
// Runs the REAL production bundle (component/dist/logi-shell.js) in jsdom with
// a REAL-backend fixture (scripts/gen_create_shipment_fixture.py — isolated
// mongomock staging; the create itself went through RBAC → validate_shipment →
// save_shipment_atomic → audit → fresh read) and verifies the fixed contract:
//
//   1. boot + the create page renders over the existing route
//   2. clicking "TẠO LÔ HÀNG" emits ONE typed shipment_create trigger carrying
//      the canonical payload + a requestId, and the page does NOT navigate on
//      transport alone (it enters the bounded "waiting for backend" state)
//   3. a backend FAILURE (duplicate id) delivered via lastWrites keeps the user
//      on the form and shows the real backend error verbatim
//   4. a backend SUCCESS delivered via lastWrites navigates ONLY THEN to
//      /lo-hang/<id>, and the shipment detail genuinely exists in the fresh
//      view-model
//   5. one click can never double-send: while the outcome is in flight the
//      button is disabled, and no second shipment_create is emitted
//
// Run: node tests/component/dom_acceptance_create_shipment.mjs
// ============================================================================

import { readFileSync } from "node:fs";
import assert from "node:assert/strict";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const require = createRequire(path.join(ROOT, "component/package.json"));
const { JSDOM } = require("jsdom");
const FIX = JSON.parse(
  readFileSync(path.join(ROOT, "tests/component/fixtures/view_model_create_shipment.json"), "utf8")
);
const INITIAL = FIX.initial;
const CREATE_OK = FIX.createOk;
const DUPLICATE_ERROR = FIX.duplicateError;
const SHIPMENT = FIX.shipment; // LO-0470
const CUSTOMER = "An Phát";

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
window.URL.createObjectURL = () => "blob:mock-url";
window.URL.revokeObjectURL = () => {};

const tick = (ms = 60) => new Promise((r) => setTimeout(r, ms));

const $ = (sel, root = window.document) => [...root.querySelectorAll(sel)];
const text = (el) => (el.textContent || "").replace(/\s+/g, " ").trim();
const mainText = () => text($("main")[0] ?? window.document.body);

function findClickable(needle, sel = "a,button", root = window.document) {
  const els = $(sel, root);
  return els.find((el) => text(el) === needle) || els.find((el) => text(el).startsWith(needle)) || null;
}

async function click(needle, sel = "a,button", root = window.document) {
  const el = findClickable(needle, sel, root);
  assert.ok(el, `clickable "${needle}" not found`);
  el.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
  await tick();
  return el;
}

async function type(input, value) {
  const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
  setter.call(input, value);
  input.dispatchEvent(new window.Event("input", { bubbles: true }));
  await tick();
}

async function selectOption(select, optionTextIncludes) {
  const option = [...select.options].find((o) => text(o).includes(optionTextIncludes));
  assert.ok(option, `select option containing "${optionTextIncludes}" not found`);
  const setter = Object.getOwnPropertyDescriptor(window.HTMLSelectElement.prototype, "value").set;
  setter.call(select, option.value);
  select.dispatchEvent(new window.Event("change", { bubbles: true }));
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

/** A fresh view-model delivery on the SAME mounted component — exactly what
 *  Streamlit does after the dispatcher's rerun: no unmount, route + component
 *  state survive, only the data channel updates. */
function deliver(data) {
  mountRef.current({
    name: "logi_shell",
    data,
    parentElement: host,
    setTriggerValue: (event, value) => triggers.push({ event, value }),
  });
}

const bundlePath = path.join(ROOT, "component/dist/logi-shell.js");

// ---------------------------------------------------------------------------
console.log("STEP 1 — boot + the create page renders over the existing route");
{
  const mod = await import(bundlePath);
  assert.equal(typeof mod.default, "function");
  mountRef.current = mod.default;
  invoke(INITIAL);
  await tick(120);
  await click("Tạo Lô Mới", "a", $("aside")[0]);
  const t = mainText();
  assert.ok(t.includes("Tạo Lô Hàng Mới"), "create page heading missing");
  assert.ok(!t.includes("Sắp có — chưa triển khai"), "create route fell through to placeholder");
  ok("boot clean; /tao-lo-moi renders the real form");
}

// ---------------------------------------------------------------------------
console.log("STEP 2 — one typed shipment_create trigger; NO navigation on transport");
let sentRequestId = "";
{
  const code = $('input[placeholder="LO-0470"]')[0];
  assert.ok(code, "shipment code input missing");
  await type(code, SHIPMENT);
  // The customer select is the one whose options carry the real customers.
  const customerSelect = $("select").find((s) =>
    [...s.options].some((o) => text(o).includes(CUSTOMER)));
  assert.ok(customerSelect, "customer select missing");
  await selectOption(customerSelect, CUSTOMER);

  const before = triggers.length;
  await click("TẠO LÔ HÀNG", "button");
  await tick(60);

  const creates = triggers.slice(before).filter((tr) => tr.event === "shipment_create");
  assert.equal(creates.length, 1, "expected exactly one shipment_create trigger");
  const payload = creates[0].value.payload;
  assert.equal(payload.shipmentId, SHIPMENT);
  assert.equal(typeof payload.requestId, "string");
  assert.ok(payload.customerId, "canonical customerId must travel with the event");
  assert.equal(payload.transport.incoterm, "DAP");
  assert.equal(typeof creates[0].value.seq, "number");
  sentRequestId = payload.requestId;

  // Transport alone is NOT success: the page must stay on the form, waiting.
  const t = mainText();
  assert.ok(t.includes("Tạo Lô Hàng Mới"), "page navigated on transport alone");
  assert.ok(t.includes("ĐANG CHỜ BACKEND XÁC NHẬN…"), "bounded waiting state missing");
  const btn = findClickable("ĐANG CHỜ BACKEND XÁC NHẬN…", "button");
  assert.ok(btn && btn.disabled, "button must be disabled while the outcome is in flight");
  ok("one shipment_create trigger with requestId; stays on form, button locked");
}

// ---------------------------------------------------------------------------
console.log("STEP 3 — backend FAILURE keeps the form and shows the real error");
{
  // The duplicate refusal arrives in the next fresh view-model (lastWrites).
  deliver(withRequestId(DUPLICATE_ERROR, sentRequestId));
  await tick(140);
  const t = mainText();
  assert.ok(t.includes("Tạo Lô Hàng Mới"), "a refusal must keep the user on the form");
  assert.ok(t.includes("Backend từ chối — lô chưa được tạo"), "refusal banner missing");
  assert.ok(t.includes(`Mã lô ${SHIPMENT} đã tồn tại.`), "real duplicate error must be visible verbatim");
  assert.ok(!t.includes("ĐANG CHỜ BACKEND XÁC NHẬN…"), "pending state must clear after the outcome");
  // The form is usable again (button re-enabled) and nothing navigated.
  const btn = findClickable("TẠO LÔ HÀNG", "button");
  assert.ok(btn && !btn.disabled, "form must be usable again after a refusal");
  ok("failure delivered → stays on form, backend error shown verbatim");
}

// ---------------------------------------------------------------------------
console.log("STEP 4 — backend SUCCESS navigates only after the fresh readback");
{
  // After a refusal the operator fixes the input and re-submits: ONE new click,
  // ONE new requestId — and the backend answers success this time.
  const retryBefore = triggers.length;
  await click("TẠO LÔ HÀNG", "button");
  await tick(60);
  const retries = triggers.slice(retryBefore).filter((tr) => tr.event === "shipment_create");
  assert.equal(retries.length, 1, "re-submit must emit exactly one new shipment_create");
  const retryRequestId = retries[0].value.payload.requestId;
  assert.notEqual(retryRequestId, sentRequestId, "each click carries its own requestId");

  const before = triggers.length;
  deliver(withRequestId(CREATE_OK, retryRequestId));
  await tick(160);
  const t = mainText();
  // Navigation happened to the real shipment detail — which genuinely exists in
  // the fresh view-model delivered with the success outcome.
  assert.ok(!t.includes("Tạo Lô Hàng Mới"), "still on the create form after success");
  assert.ok(t.includes(SHIPMENT), "shipment detail must render after success");
  assert.ok(t.includes(CUSTOMER), "created shipment customer missing on detail");
  // No second create was emitted by the success handling.
  const extraCreates = triggers.slice(before).filter((tr) => tr.event === "shipment_create");
  assert.equal(extraCreates.length, 0, "success handling must not re-emit shipment_create");
  ok("success readback → navigated to the existing shipment detail, no re-emit");
}

console.log(`\nCREATE-SHIPMENT DOM acceptance PASSED — ${passed} checks`);
