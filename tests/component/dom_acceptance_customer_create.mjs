// ============================================================================
// LOGI_CUSTOMER_CREATE_TRUTHFULNESS_01 — DOM acceptance for the REAL
// "Khách Hàng" create flow (/khach-hang).
//
// Runs the REAL production bundle (component/dist/logi-shell.js) in jsdom with
// a REAL-backend fixture (scripts/gen_customer_create_fixture.py — isolated
// mongomock staging; the writes went through RBAC → duplicate check →
// save_customer_to_cloud → audit → fresh read) and verifies the fixed
// contract:
//
//   1. boot + the customers page renders over the existing route
//   2. TRANSPORT FAILURE (the bridge is not bound): clicking TẠO KHÁCH HÀNG
//      emits NOTHING, claims NO success, keeps the modal OPEN with the
//      entered data, and shows a red failure state (the old bundle closed
//      the form, cleared it and toasted green "Đã gửi tạo khách hàng")
//   3. TRANSPORT SUCCESS is not persistence: the click emits exactly ONE
//      customer_create trigger carrying a requestId, the modal stays open in
//      a bounded waiting state and the button is locked (no double-send)
//   4. a backend FAILURE (duplicate id) delivered via lastWrites keeps the
//      modal open, retains the entered data and shows the real backend error
//      verbatim
//   5. after fixing the id, a backend SUCCESS delivered via lastWrites closes
//      the modal and the new customer is present in the fresh view-model
//   6. adversarial: an UNRELATED view-model change (version bump + another
//      event's outcome) while the create intent is unanswered can NEVER be
//      consumed as success
//
// Run: node tests/component/dom_acceptance_customer_create.mjs
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
  readFileSync(path.join(ROOT, "tests/component/fixtures/view_model_customer_create.json"), "utf8")
);
const INITIAL = FIX.initial;
const DUPLICATE_ERROR = FIX.duplicateError;
const CREATE_OK = FIX.createOk;
const UNRELATED_CHANGE = FIX.unrelatedChange;
const DUPLICATE_ID = FIX.duplicateId; // CUST-ANPHAT
const NEW_ID = FIX.newId; // CUST-MOI

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
const bodyText = () => text(window.document.body);

function findClickable(needle, sel = "a,button", root = window.document) {
  const els = $(sel, root);
  // The submit button carries a leading "💾 " icon glyph, so exact/prefix
  // matching alone cannot reach it.
  return els.find((el) => text(el) === needle)
    || els.find((el) => text(el).startsWith(needle))
    || els.find((el) => text(el).includes(needle))
    || null;
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
function invokeWith(api) {
  if (lastInvokeCleanup) lastInvokeCleanup();
  const cleanup = mountRef.current(api);
  lastInvokeCleanup = cleanup;
  return cleanup;
}
function invoke(data) {
  return invokeWith({
    name: "logi_shell",
    data,
    parentElement: host,
    setTriggerValue: (event, value) => triggers.push({ event, value }),
  });
}
/** A mount whose v2 trigger bridge is NOT bound — dispatch() must return
 *  false. This is the real transport-failure boundary (component not yet
 *  bound / torn down), reproduced without faking any UI state. */
function invokeNoTransport(data) {
  return invokeWith({
    name: "logi_shell",
    data,
    parentElement: host,
    setTriggerValue: undefined,
  });
}
/** A fresh view-model delivery on the SAME mounted component. */
function deliver(data) {
  mountRef.current({
    name: "logi_shell",
    data,
    parentElement: host,
    setTriggerValue: (event, value) => triggers.push({ event, value }),
  });
}

function inputByPlaceholder(needle) {
  const el = $("input").find((i) => (i.getAttribute("placeholder") || "").includes(needle));
  assert.ok(el, `input with placeholder containing "${needle}" not found`);
  return el;
}

async function openCreateModal() {
  await click("Khách mới", "button");
  assert.ok(mainText().includes("Tạo khách hàng mới"), "create modal heading missing");
}

const bundlePath = path.join(ROOT, "component/dist/logi-shell.js");

// ---------------------------------------------------------------------------
console.log("STEP 1 — boot + the customers page renders over the existing route");
{
  const mod = await import(bundlePath);
  assert.equal(typeof mod.default, "function");
  mountRef.current = mod.default;
  invoke(INITIAL);
  await tick(120);
  await click("Khách Hàng", "a", $("aside")[0]);
  const t = mainText();
  assert.ok(t.includes("Khách Hàng"), "customers page heading missing");
  assert.ok(t.includes(DUPLICATE_ID), "the existing customer must be listed");
  ok("boot clean; /khach-hang renders the real list");
}

// ---------------------------------------------------------------------------
console.log("STEP 2 — TRANSPORT FAILURE: no trigger, no success claim, form kept");
{
  invokeNoTransport(INITIAL);
  await tick(120);
  await click("Khách Hàng", "a", $("aside")[0]);
  await openCreateModal();
  await type(inputByPlaceholder("VD: CUST-ABC"), "CUST-TRAN");
  await type(inputByPlaceholder("Công ty / cá nhân"), "Công ty Vận chuyển (thử)");

  const before = triggers.length;
  await click("TẠO KHÁCH HÀNG", "button");
  await tick(80);

  // Nothing crossed the bridge…
  assert.equal(triggers.slice(before).filter((tr) => tr.event === "customer_create").length, 0,
    "no customer_create may exist when the transport is not bound");
  // …so no success claim and no close: the entered data must survive.
  const t = bodyText();
  assert.ok(!t.includes("Đã gửi tạo khách hàng"),
    "the false-success toast 'Đã gửi tạo khách hàng' must never appear on transport failure");
  assert.ok(!t.includes("Đã tạo khách hàng"), "no success toast may appear on transport failure");
  assert.ok(mainText().includes("Tạo khách hàng mới"),
    "the modal must STAY OPEN on transport failure (entered data retained)");
  assert.ok(t.includes("Không gửi được"),
    "a useful failure state must be shown on transport failure");
  const idInput = inputByPlaceholder("VD: CUST-ABC");
  assert.equal(idInput.value, "CUST-TRAN", "the entered customer code must be retained");
  assert.equal(inputByPlaceholder("Công ty / cá nhân").value, "Công ty Vận chuyển (thử)",
    "the entered customer name must be retained");
  ok("transport failure → nothing sent, no success claim, modal+data kept, red state");
}

// ---------------------------------------------------------------------------
console.log("STEP 3 — one typed customer_create trigger; modal waits for the backend");
let sentRequestId = "";
{
  invoke(INITIAL);
  await tick(120);
  await click("Khách Hàng", "a", $("aside")[0]);
  await openCreateModal();
  await type(inputByPlaceholder("VD: CUST-ABC"), DUPLICATE_ID);
  await type(inputByPlaceholder("Công ty / cá nhân"), "An Phát JSC (bản thử trùng)");

  const before = triggers.length;
  await click("TẠO KHÁCH HÀNG", "button");
  await tick(60);

  const creates = triggers.slice(before).filter((tr) => tr.event === "customer_create");
  assert.equal(creates.length, 1, "expected exactly one customer_create trigger");
  const payload = creates[0].value.payload;
  assert.equal(payload.id, DUPLICATE_ID);
  assert.equal(typeof payload.requestId, "string");
  assert.equal(typeof creates[0].value.seq, "number");
  sentRequestId = payload.requestId;

  // Transport alone is NOT success: the modal must stay open, waiting.
  const t = bodyText();
  assert.ok(mainText().includes("Tạo khách hàng mới"), "modal closed on transport alone");
  assert.ok(t.includes("ĐANG CHỜ BACKEND XÁC NHẬN…"), "bounded waiting state missing");
  assert.ok(!t.includes("Đã tạo khách hàng"), "no success toast before the backend outcome");
  const btn = findClickable("ĐANG CHỜ BACKEND XÁC NHẬN…", "button");
  assert.ok(btn && btn.disabled, "button must be disabled while the outcome is in flight");
  ok("one customer_create trigger with requestId; modal waits, button locked");
}

// ---------------------------------------------------------------------------
console.log("STEP 4 — backend FAILURE (duplicate) keeps the form + real error verbatim");
{
  deliver(withRequestId(DUPLICATE_ERROR, sentRequestId));
  await tick(140);
  const t = bodyText();
  assert.ok(mainText().includes("Tạo khách hàng mới"), "a refusal must keep the modal open");
  assert.ok(t.includes("Backend từ chối — khách hàng chưa được lưu"), "refusal banner missing");
  assert.ok(t.includes(`Mã khách hàng ${DUPLICATE_ID} đã tồn tại.`),
    "the real duplicate error must be visible verbatim");
  assert.ok(!t.includes("ĐANG CHỜ BACKEND XÁC NHẬN…"), "pending state must clear after the outcome");
  assert.ok(!t.includes("Đã tạo khách hàng"), "no success toast after a refusal");
  // The entered data is still there so the operator can fix the id and retry.
  assert.equal(inputByPlaceholder("VD: CUST-ABC").value, DUPLICATE_ID,
    "the entered (duplicate) code must be retained for correction");
  const btn = findClickable("TẠO KHÁCH HÀNG", "button");
  assert.ok(btn && !btn.disabled, "the form must be usable again after a refusal");
  ok("duplicate refusal → modal kept, data retained, backend error verbatim");
}

// ---------------------------------------------------------------------------
console.log("STEP 5 — after fixing the id, SUCCESS closes the form only on the readback");
{
  await type(inputByPlaceholder("VD: CUST-ABC"), NEW_ID);
  const retryBefore = triggers.length;
  await click("TẠO KHÁCH HÀNG", "button");
  await tick(60);
  const retries = triggers.slice(retryBefore).filter((tr) => tr.event === "customer_create");
  assert.equal(retries.length, 1, "re-submit must emit exactly one new customer_create");
  const retryRequestId = retries[0].value.payload.requestId;
  assert.notEqual(retryRequestId, sentRequestId, "each click carries its own requestId");

  const before = triggers.length;
  deliver(withRequestId(CREATE_OK, retryRequestId));
  await tick(160);
  const t = bodyText();
  assert.ok(!mainText().includes("Tạo khách hàng mới"), "modal must close after a confirmed save");
  assert.ok(t.includes(`Đã tạo khách hàng ${NEW_ID}`), "success toast missing after the readback");
  assert.ok(mainText().includes(NEW_ID), "the fresh view-model must list the new customer");
  const extraCreates = triggers.slice(before).filter((tr) => tr.event === "customer_create");
  assert.equal(extraCreates.length, 0, "success handling must not re-emit customer_create");
  ok("success readback → modal closed, new customer listed, no re-emit");
}

// ---------------------------------------------------------------------------
console.log("STEP 6 — ADVERSARIAL: unrelated change while pending is never success");
{
  invoke(INITIAL);
  await tick(120);
  await click("Khách Hàng", "a", $("aside")[0]);
  await openCreateModal();
  await type(inputByPlaceholder("VD: CUST-ABC"), NEW_ID);
  await type(inputByPlaceholder("Công ty / cá nhân"), "Công ty Mới (thử lại)");

  const before = triggers.length;
  await click("TẠO KHÁCH HÀNG", "button");
  await tick(60);
  const creates = triggers.slice(before).filter((tr) => tr.event === "customer_create");
  assert.equal(creates.length, 1, "expected exactly one customer_create trigger");
  const pendingRequestId = creates[0].value.payload.requestId;
  assert.ok(bodyText().includes("ĐANG CHỜ BACKEND XÁC NHẬN…"), "must wait for the backend outcome");

  // Fixture precondition: the unrelated state really changes the version and
  // carries only ANOTHER event's outcome (customer_edit), never this create's.
  assert.notEqual(UNRELATED_CHANGE.version, INITIAL.version,
    "the unrelated state must really change the payload version");
  assert.ok((UNRELATED_CHANGE.lastWrites ?? []).every((w) => w.event !== "customer_create"),
    "fixture precondition: the unrelated state carries no customer_create outcome");
  deliver(withRequestId(UNRELATED_CHANGE, pendingRequestId));
  await tick(160);

  // Still waiting — no close, no success claim.
  const t = bodyText();
  assert.ok(mainText().includes("Tạo khách hàng mới"),
    "an unrelated version change must NOT close the create form");
  assert.ok(t.includes("ĐANG CHỜ BACKEND XÁC NHẬN…"),
    "the form must keep waiting for the authoritative outcome");
  assert.ok(!t.includes("Đã tạo khách hàng"),
    "no success toast may appear from an unrelated change");
  ok("unrelated version change + another event's outcome never consumed as success");
}

console.log(`\nCUSTOMER-CREATE DOM acceptance PASSED — ${passed} checks`);
