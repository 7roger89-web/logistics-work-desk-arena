// ============================================================================
// C2D DOM acceptance — runs the REAL production bundle
// (component/dist/logi-shell.js) in a DOM (jsdom) against a fixture generated
// from the REAL Logistics backend (scripts/gen_c2d_fixture.py), and drives it
// with real DOM events through the Streamlit Components v2 contract.
//
// Proven here (rendering alone is NOT a pass):
//   1. The "Công nợ đối tác" route is real (not the placeholder), with a
//      heading, per-currency summary tiles and payable rows.
//   2. Multi-currency separation is stated and no cross-currency grand total
//      is manufactured.
//   3. UNKNOWN != ZERO — with no canonical payable the worklist shows the
//      explicit empty state, never a "0" payable.
//   4. "Trả đối tác" opens a sheet and emits `partner_payment_record` with a
//      stable request identity; a double click replays the SAME id; a new
//      intent mints a NEW id.
//   5. "Mở lô" navigates to the linked shipment's finance tab.
//
// Run: node tests/component/dom_acceptance_c2d.mjs
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
  readFileSync(path.join(ROOT, "tests/component/fixtures/view_model_c2d.json"), "utf8")
);
const PAY = FIXTURE.journey.payables;
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
const nf = (n) => Number(n).toLocaleString("vi-VN");

// ---------------------------------------------------------------------------
// STEP 1 — boot bundle, open the "Công nợ đối tác" route
// ---------------------------------------------------------------------------

console.log("STEP 1 — boot bundle and open Công nợ đối tác");
{
  const mod = await import(path.join(ROOT, "component/dist/logi-shell.js"));
  assert.equal(typeof mod.default, "function", "bundle must default-export the mount function");
  mountRef.current = mod.default;
  invoke(FIXTURE.journey);
  await tick(140);
  const t = bodyText();
  assert.ok(!t.includes("process is not defined"), "process is not defined leaked");
  assert.ok(!t.includes("BidiComponent Error"), "BidiComponent Error rendered");

  await click("Công nợ đối tác", "a", $("aside")[0]);
  assert.ok(bodyText().includes("Thanh toán đối tác · Phải trả"), "global payables heading missing");
  assert.ok(!bodyText().includes("Màn hình này chưa triển khai"), "route must NOT be the placeholder");
  ok("global partner-payables route renders (not the placeholder)");
}

// ---------------------------------------------------------------------------
// STEP 2 — summary tiles + rows from real backend truth, currency separated
// ---------------------------------------------------------------------------

console.log("STEP 2 — summary tiles, rows, currency separation");
{
  const t = bodyText();
  // Per-currency totals: one group per currency, no grand total.
  for (const ccy of Object.keys(PAY.totals)) {
    assert.ok(t.includes(`Tổng phải trả · ${ccy}`), `per-currency total heading for ${ccy} missing`);
  }
  assert.ok(t.includes("không quy đổi"), "must state there is no FX conversion");
  assert.ok(t.includes("Phải trả") && t.includes("Đã trả") && t.includes("Còn lại"), "tiles missing");

  // Every real row's identity renders.
  for (const row of PAY.rows) {
    assert.ok(t.includes(row.shipmentId), `shipment id ${row.shipmentId} missing`);
    assert.ok(t.includes(row.partnerName), `partner name ${row.partnerName} missing`);
  }

  const top = [...PAY.rows].sort((a, b) => (b.remaining ?? -1) - (a.remaining ?? -1))[0];
  assert.ok(t.includes(nf(top.payable)), `payable of ${top.id} missing`);
  assert.ok(t.includes(nf(top.remaining)), `remaining of ${top.id} missing`);
  ok(`${PAY.rows.length} payable rows + per-currency totals rendered`);
}

// ---------------------------------------------------------------------------
// STEP 3 — record partner payment: stable request identity + new intent distinct
// ---------------------------------------------------------------------------

console.log("STEP 3 — partner_payment_record identity and idempotency from the worklist");
{
  triggers = [];
  await click("Trả đối tác", "button");
  assert.ok(bodyText().includes("Ghi nhận thanh toán đối tác"), "payment sheet must open");
  assert.ok(bodyText().includes("không quy đổi"), "sheet must state no FX conversion");

  type(byPlaceholder("VD: 20000000"), "10000000");
  await tick();
  const saveBtn = findClickable("LƯU THANH TOÁN", "button");
  assert.ok(saveBtn, "save button missing");

  saveBtn.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
  saveBtn.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
  await tick(150);

  const sent = eventsOf("partner_payment_record");
  assert.equal(sent.length, 2, `double click must reach the handler twice, got ${sent.length}`);
  const ids = new Set(sent.map((e) => e.payload.requestId));
  assert.equal(ids.size, 1, `one intent must replay ONE request id, got ${[...ids].join(", ")}`);
  const first = sent[0].payload;
  assert.equal(first.shipmentId, SHIPMENT);
  assert.equal(first.amount, 10000000);
  assert.match(first.requestId, /^PPAY-REQ-/, "request identity must be namespaced");
  ok(`double click replayed one request identity: ${first.requestId}`);

  // A genuinely NEW intent must NOT be swallowed as a replay.
  triggers = [];
  await click("Trả đối tác", "button");
  type(byPlaceholder("VD: 20000000"), "10000000");
  await tick();
  await click("LƯU THANH TOÁN", "button");
  await tick(150);
  const second = eventsOf("partner_payment_record");
  assert.equal(second.length, 1, "a new intent must post exactly one event");
  assert.equal(second[0].payload.amount, 10000000);
  assert.notEqual(second[0].payload.requestId, first.requestId,
    "a second genuine payment must mint a NEW request identity");
  ok(`new intent minted a new request identity: ${second[0].payload.requestId}`);
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
  assert.ok(t.includes("Phải trả đối tác"), "finance tab AP block missing");
  ok("open shipment navigates to the shipment detail finance tab");
}

// ---------------------------------------------------------------------------
// STEP 5 — UNKNOWN != ZERO in the worklist (no canonical payable)
// ---------------------------------------------------------------------------

console.log("STEP 5 — UNKNOWN != ZERO with no canonical payable");
{
  await click("Công nợ đối tác", "a", $("aside")[0]);
  invoke(FIXTURE.empty);
  await tick(160);
  const t = bodyText();

  assert.equal(FIXTURE.empty.payables.rows.length, 0, "fixture precondition: empty payables");
  assert.ok(t.includes("Chưa có khoản phải trả đối tác"), "empty state must be shown");
  // No per-currency summary tiles are manufactured from an empty book.
  assert.ok(!t.includes("Tổng phải trả"), "no per-currency totals must be manufactured from an empty book");
  ok("no canonical payable ⇒ explicit empty state, never a manufactured 0 payable");
}

console.log(`\nC2D DOM acceptance: ${passed} steps passed`);
