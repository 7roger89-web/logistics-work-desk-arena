// ============================================================================
// C2C DOM acceptance — runs the REAL production bundle
// (component/dist/logi-shell.js) in a DOM (jsdom) against a fixture generated
// from the REAL Logistics backend (scripts/gen_c2c_fixture.py), and drives it
// with real DOM events through the Streamlit Components v2 contract.
//
// Proven here (rendering alone is NOT a pass):
//   1. The "Thu tiền" route is real (not the placeholder), with a heading,
//      per-currency summary tiles and multiple receivable rows.
//   2. Multi-currency separation is stated and no cross-currency grand total
//      is manufactured.
//   3. UNKNOWN != ZERO — an empty actual book renders "—", never "0".
//   4. "Thu tiền" on a row opens a sheet and emits `payment_record` with a
//      stable request identity; a double click replays the SAME id; a new
//      intent mints a NEW id.
//   5. "Mở lô" navigates to the linked shipment's finance tab.
//
// Run: node tests/component/dom_acceptance_c2c.mjs
// ============================================================================

import { readFileSync } from "node:fs";
import assert from "node:assert/strict";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const require = createRequire(path.join(ROOT, "component/package.json"));
const { JSDOM } = require("jsdom");

const FIXTURE = JSON.parse(
  readFileSync(path.join(ROOT, "tests/component/fixtures/view_model_c2c.json"), "utf8")
);
const REC = FIXTURE.journey.receivables;
const SHIPMENT = FIXTURE.shipment;

// ---------------------------------------------------------------------------
// jsdom environment
// ---------------------------------------------------------------------------

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

function findClickable(needle, sel = "a,button", root = window.document) {
  const els = $(sel, root);
  return (
    els.find((el) => text(el) === needle) ||
    els.find((el) => text(el).startsWith(needle)) ||
    els.find((el) => text(el).includes(needle)) ||
    null
  );
}

async function click(needle, sel = "a,button", root = window.document) {
  const el = findClickable(needle, sel, root);
  assert.ok(el, `clickable "${needle}" not found`);
  el.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
  await tick();
  return el;
}

function type(input, value) {
  Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set.call(input, value);
  input.dispatchEvent(new window.Event("input", { bubbles: true }));
  input.dispatchEvent(new window.Event("change", { bubbles: true }));
}

const byPlaceholder = (needle) => {
  const el = $(`input[placeholder^="${needle}"]`)[0];
  assert.ok(el, `input with placeholder "${needle}" not found`);
  return el;
};

const byTestId = (testId) => {
  const el = window.document.querySelector(`[data-testid="${testId}"]`);
  assert.ok(el, `[data-testid=${testId}] not found`);
  return el;
};

async function clickTestId(testId) {
  const el = byTestId(testId);
  el.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
  await tick();
  return el;
}

const bodyText = () => text(window.document.body);
let passed = 0;
function ok(name) {
  passed += 1;
  console.log(`  ✓ ${name}`);
}

// ---------------------------------------------------------------------------
// Simulated Streamlit v2 component invocation
// ---------------------------------------------------------------------------

const host = window.document.createElement("div");
window.document.body.appendChild(host);

let triggers = [];
const mountRef = { current: null };
function invoke(data) {
  return mountRef.current({
    name: "logi_shell",
    data,
    parentElement: host,
    setTriggerValue: (event, value) => triggers.push({ event, value }),
  });
}
const eventsOf = (name) => triggers.filter((t) => t.event === name).map((t) => t.value);
const vi = "vi-VN";
const nf = (n) => Number(n).toLocaleString(vi);

// ---------------------------------------------------------------------------
// STEP 1 — boot bundle, open the "Thu tiền" route
// ---------------------------------------------------------------------------

console.log("STEP 1 — boot bundle and open Thu tiền / Phải thu");
{
  const mod = await import(path.join(ROOT, "component/dist/logi-shell.js"));
  assert.equal(typeof mod.default, "function", "bundle must default-export the mount function");
  mountRef.current = mod.default;
  invoke(FIXTURE.journey);
  await tick(140);
  const t = bodyText();
  assert.ok(!t.includes("process is not defined"), "process is not defined leaked");
  assert.ok(!t.includes("BidiComponent Error"), "BidiComponent Error rendered");

  await click("Thu tiền", "a", $("aside")[0]);
  assert.ok(bodyText().includes("Thu tiền khách · Phải thu"), "global receivables heading missing");
  assert.ok(!bodyText().includes("Màn hình này chưa triển khai"), "route must NOT be the placeholder");
  ok("global receivables route renders (not the placeholder)");
}

// ---------------------------------------------------------------------------
// STEP 2 — summary tiles + rows from real backend truth, currency separated
// ---------------------------------------------------------------------------

console.log("STEP 2 — summary tiles, rows, currency separation");
{
  const t = bodyText();
  // Per-currency totals: one group per currency, no grand total.
  for (const ccy of Object.keys(REC.totals)) {
    assert.ok(t.includes(`Tổng phải thu · ${ccy}`), `per-currency total heading for ${ccy} missing`);
  }
  assert.ok(t.includes("không quy đổi"), "must state there is no FX conversion");
  // The three-tile structure (Phải thu / Đã thu / Còn lại).
  assert.ok(t.includes("Phải thu") && t.includes("Đã thu") && t.includes("Còn lại"), "tiles missing");

  // Multiple real rows.
  for (const row of REC.rows) {
    assert.ok(t.includes(row.id), `row id ${row.id} missing`);
    assert.ok(t.includes(row.customer), `customer ${row.customer} missing`);
  }
  assert.ok(t.includes(nf(REC.totals.VND.outstanding)), "outstanding total must render");

  // One specific row's real figures (first by outstanding desc).
  const top = [...REC.rows].sort((a, b) => b.outstanding - a.outstanding)[0];
  assert.ok(t.includes(nf(top.receivable)), `receivable of ${top.id} missing`);
  assert.ok(t.includes(nf(top.outstanding)), `outstanding of ${top.id} missing`);
  ok(`${REC.rows.length} receivable rows + per-currency totals rendered`);
}

// ---------------------------------------------------------------------------
// STEP 3 — record receipt: stable request identity + new intent distinct
// ---------------------------------------------------------------------------

console.log("STEP 3 — payment_record: authoritative outcome (LOGI_FRONTEND_WORKFLOW_OVERHAUL_01)");
{
  triggers = [];
  await click("Thu tiền", "button");
  assert.ok(bodyText().includes("Ghi nhận khoản thu"), "receipt sheet must open");
  assert.ok(bodyText().includes("không quy đổi"), "sheet must state no FX conversion");

  type(byPlaceholder("VD: 150000000"), "25000000");
  await tick();
  const saveBtn = window.document.querySelector(`button[data-testid="receivable-pay-submit"]`);
  assert.ok(saveBtn, "save button missing");
  assert.equal(saveBtn.disabled, false, "submit enabled before sending");

  // A forced synchronous double click must reach the writer ONCE: the in-flight
  // ref absorbs the second click before React even re-renders.
  saveBtn.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
  saveBtn.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
  await tick(150);

  const sent = eventsOf("payment_record");
  assert.equal(sent.length, 1, `one click = one payment intent dispatched, got ${sent.length}`);
  const first = sent[0].payload;
  assert.equal(first.amount, "25000000"); // raw preserved
  assert.match(first.requestId, /^PAY-REQ-/, "request identity must be namespaced");
  ok(`one intent dispatched with identity ${first.requestId}; double click absorbed`);

  // TRANSPORT ack is NOT persistence: the sheet stays open, pending is named,
  // submit is disabled, and no green success exists yet.
  assert.ok(window.document.getElementById("receivable-pay-sheet"), "sheet stays open while the outcome is in flight");
  const pendingLine = window.document.querySelector('[data-testid="receivable-pay-pending"]');
  assert.ok(pendingLine && pendingLine.textContent.includes("ĐANG CHỜ BACKEND XÁC NHẬN"), "pending state names waiting for the backend");
  assert.ok(saveBtn.disabled, "submit disabled while pending");
  assert.ok(!bodyText().includes("Đã ghi nhận khoản thu"), "no green success before the correlated backend answer");

  // An UNRELATED lastWrites entry (different requestId) must not fake success.
  const unrelated = structuredClone(FIXTURE.journey);
  unrelated.lastWrites = [{ event: "payment_record", ok: true, requestId: "PAY-REQ-NOT-MINE", shipmentId: first.shipmentId }];
  invoke(unrelated); await tick(160);
  assert.ok(window.document.getElementById("receivable-pay-sheet"), "unrelated lastWrites cannot close the sheet or fake success");
  ok("unrelated lastWrites cannot fake success");

  // Backend REFUSAL: sheet open, amount preserved, the writer's message inline.
  const refused = structuredClone(FIXTURE.journey);
  refused.lastWrites = [{ event: "payment_record", ok: false, requestId: first.requestId, shipmentId: first.shipmentId, error: "Request identity Đã được dùng cho financial action khác." }];
  invoke(refused); await tick(160);
  assert.ok(window.document.getElementById("receivable-pay-sheet"), "refusal keeps the sheet open");
  const amountInput = byPlaceholder("VD: 150000000");
  assert.equal(amountInput.value, "25000000", "the original amount survives a refusal");
  const err = window.document.getElementById("receivable-pay-error");
  assert.ok(err && text(err).includes("Request identity"), "actionable backend refusal shown inline");
  assert.ok(!byTestId("receivable-pay-submit").disabled, "submit re-enabled so the operator can retry");
  ok("refusal preserves the form and surfaces the backend's own error");

  // The refused request stays historical: the retry is a NEW write attempt
  // with a FRESH requestId (Control-Tower repair — stale-refusal safety).
  triggers = [];
  const submit2 = window.document.querySelector(`button[data-testid="receivable-pay-submit"]`);
  submit2.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
  await tick(140);
  const retried = eventsOf("payment_record");
  assert.equal(retried.length, 1, "retry dispatches exactly one event");
  const retryId = retried[0].payload.requestId;
  assert.notEqual(retryId, first.requestId, "retry after refusal mints a NEW requestId (≠ refused X)");
  assert.equal(retried[0].payload.amount, "25000000", "amount preserved into the retry intent");
  // The CURRENT lastWrites still carries the OLD refusal (X). It must NOT
  // instantly settle the retry (Y): the retry stays pending with no error.
  assert.ok(window.document.querySelector('[data-testid="receivable-pay-pending"]'),
    "stale refusal X cannot settle the retry — still pending");
  assert.ok(!window.document.getElementById("receivable-pay-error"),
    "stale refusal does not re-pop the inline error");
  ok(`retry minted a NEW identity ${retryId}; old refusal X cannot settle it`);

  // (C) correlated ok for the retry WITHOUT the finance readback: still pending.
  const okNoReadback = structuredClone(FIXTURE.journey);
  okNoReadback.lastWrites = [{ event: "payment_record", ok: true, requestId: retryId, shipmentId: first.shipmentId }];
  invoke(okNoReadback); await tick(160);
  assert.ok(window.document.getElementById("receivable-pay-sheet"), "ok without readback keeps the sheet open");
  assert.ok(window.document.querySelector('[data-testid="receivable-pay-pending"]'), "ok without readback stays pending");
  assert.ok(!bodyText().includes("Đã ghi nhận khoản thu"), "no green without the authoritative readback");
  ok("correlated ok WITHOUT finance readback = still pending, truthful");

  // (D) success requires the SAME fresh view-model to already show the payment
  // (finance.payments[].requestId) — patch the readback like the backend does.
  const succeeded = structuredClone(FIXTURE.journey);
  const lot = succeeded.shipments.find((x) => x.id === first.shipmentId);
  lot.finance.payments = lot.finance.payments ?? [];
  lot.finance.payments.push({
    requestId: retryId,
    date: "18/09/2026",
    kind: "Thu tiền khách",
    amount: 25000000,
    ccy: lot.currency || "VND",
    by: "staging.support",
  });
  succeeded.lastWrites = [{ event: "payment_record", ok: true, requestId: retryId, shipmentId: first.shipmentId }];
  invoke(succeeded); await tick(160);
  assert.ok(!window.document.getElementById("receivable-pay-sheet"), "ok + fresh readback closes the sheet");
  assert.ok(bodyText().includes("Đã ghi nhận khoản thu"), "green success only AFTER ok AND readback");
  ok("success = correlated ok AND finance.payments requestId readback");
}

// ---------------------------------------------------------------------------
// STEP 4 — open shipment links to its finance tab
// ---------------------------------------------------------------------------

console.log("STEP 4 — open the linked shipment");
{
  await click("Mở lô", "a");
  await tick(120);
  const t = bodyText();
  assert.ok(t.includes("Tài chính / Công nợ"), "finance tab must be present on the detail page");
  assert.ok(t.includes("Phải thu khách hàng"), "finance tab AR block missing");
  ok("open shipment navigates to the shipment detail finance tab");
}

// ---------------------------------------------------------------------------
// STEP 5 — UNKNOWN != ZERO in the worklist (empty actual book)
// ---------------------------------------------------------------------------

console.log("STEP 5 — UNKNOWN != ZERO on an empty actual book");
{
  // Navigate back to the worklist, then deliver the empty-book backend state.
  await click("Thu tiền", "a", $("aside")[0]);
  invoke(FIXTURE.emptyBook);
  await tick(160);
  const t = bodyText();

  const emptyRow = FIXTURE.emptyBook.receivables.rows.find((r) => r.id === SHIPMENT);
  assert.equal(emptyRow.hasActualLines, false, "fixture precondition: no booked line");
  assert.equal(emptyRow.receivable, null, "fixture precondition: receivable null");

  // The empty row renders UNKNOWN for receivable/outstanding, never 0.
  const rowCells = $("tr").map((tr) => text(tr)).join(" | ");
  assert.ok(rowCells.includes("— VND"), `empty receivable must render an em dash, got rows: ${rowCells}`);
  ok("empty actual book shows — for receivable/outstanding in the worklist, never 0");
}

console.log(`\nC2C DOM acceptance: ${passed} steps passed`);
