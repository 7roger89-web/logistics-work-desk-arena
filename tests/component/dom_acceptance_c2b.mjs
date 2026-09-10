// ============================================================================
// C2B DOM acceptance — runs the REAL production bundle
// (component/dist/logi-shell.js) in a DOM (jsdom) against a fixture generated
// from the REAL Logistics backend (scripts/gen_c2b_fixture.py), and drives it
// with real DOM events through the Streamlit Components v2 contract:
// `mount({data, parentElement, setTriggerValue})` re-invoked with new data.
//
// Proven here (screens rendering alone is NOT a pass — every step fires or
// asserts real typed events / real backend values):
//   1. The selected partner renders from canonical ledger truth
//      (AGT-PHUANH · CÔNG TY TNHH PHÚ ANH LOGISTICS)
//   2. Payable / paid / remaining render the canonical figures
//      (57.000.000 / 20.000.000 / 37.000.000 VND) — backend-derived
//   3. Partner payment history renders the real transaction
//   4. UNKNOWN != ZERO — before any ledger row the tiles show "—", never "0"
//   5. GHI NHẬN PHẢI TRẢ emits `partner_payable_record` with the real payload
//   6. One payment intent emits `partner_payment_record` with a stable request
//      identity; a double click replays the SAME id; a new intent mints a NEW id
//
// Run: node tests/component/dom_acceptance_c2b.mjs
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
  readFileSync(path.join(ROOT, "tests", "component", "fixtures", "view_model_c2b.json"), "utf8")
);
const SHIPMENT = FIXTURE.shipment;
const PARTNER_ID = FIXTURE.partner;
const JOURNEY = FIXTURE.journey;
const NO_LEDGER = FIXTURE.noLedger;
const LOT = JOURNEY.shipments.find((x) => x.id === SHIPMENT);
const PARTNER = LOT.finance.partner;
assert.ok(PARTNER, "fixture must carry the canonical partner block");

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

// ---------------------------------------------------------------------------
// DOM helpers
// ---------------------------------------------------------------------------

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
const vi = "vi-VN";
const nf = (n) => Number(n).toLocaleString(vi);

// ---------------------------------------------------------------------------

const bundle = path.join(ROOT, "component", "dist", "logi-shell.js");
const mod = await import(bundle);
assert.equal(typeof mod.default, "function", "bundle must default-export the mount function");
mountRef.current = mod.default;

console.log("STEP 1 — canonical partner identity renders");
invoke(JOURNEY);
await tick(140);
assert.ok(!bodyText().includes("process is not defined"), "process is not defined leaked");
await click("Lô Hàng", "a", $("aside")[0]);
await click(SHIPMENT, "a", $("table.tbl")[0]);
assert.equal(text($("h1")[0]), SHIPMENT, "detail header wrong");
await click("Tài chính / Công nợ", "button", window.document.getElementById("workspace-tabs"));
await tick();
let body = bodyText();
assert.ok(body.includes(PARTNER.partnerName), "partner legal name rendered");
assert.ok(body.includes(PARTNER.partnerId), "partner id rendered");
assert.ok(!body.includes("đề xuất từ danh mục"), "no catalog-suggestion badge once the ledger exists");
ok(`partner renders: ${PARTNER.partnerId} · ${PARTNER.partnerName}`);

console.log("STEP 2 — payable / paid / remaining from canonical truth");
body = bodyText();
const tr = (n) => `${(n / 1e6).toLocaleString(vi)} tr`;
assert.ok(body.includes(`Phải trả đối tác (${PARTNER.currency})`), "AP heading must carry the real currency");
assert.ok(body.includes(`${tr(PARTNER.payable)} tr`.replace(" tr tr", " tr")), "payable tile rendered");
assert.ok(body.includes(`${tr(PARTNER.payable)} ${PARTNER.currency}`), `payable ${tr(PARTNER.payable)} ${PARTNER.currency} rendered`);
assert.ok(body.includes(`${tr(PARTNER.paid)} ${PARTNER.currency}`), `paid ${tr(PARTNER.paid)} ${PARTNER.currency} rendered`);
assert.ok(body.includes(`${tr(PARTNER.remaining)} ${PARTNER.currency}`), `remaining ${tr(PARTNER.remaining)} ${PARTNER.currency} rendered`);
ok(`tiles render backend truth: ${tr(PARTNER.payable)} / ${tr(PARTNER.paid)} / ${tr(PARTNER.remaining)} ${PARTNER.currency}`);

console.log("STEP 3 — partner payment history renders the real transaction");
body = bodyText();
assert.ok(body.includes("Lịch sử trả đối tác"), "payment history section rendered");
const realPayment = PARTNER.payments[0];
assert.ok(realPayment, "fixture has one real canonical payment");
assert.ok(body.includes(realPayment.requestId), "canonical request id visible in history");
ok(`history shows canonical payment ${realPayment.requestId}`);

console.log("STEP 4 — UNKNOWN != ZERO before any canonical ledger row");
invoke(NO_LEDGER);
await tick(140);
await click("Lô Hàng", "a", $("aside")[0]);
await click(SHIPMENT, "a", $("table.tbl")[0]);
await click("Tài chính / Công nợ", "button", window.document.getElementById("workspace-tabs"));
await tick();
body = bodyText();
assert.ok(body.includes(PARTNER.partnerName), "suggested partner still identifies the catalog agent");
assert.ok(body.includes("đề xuất từ danh mục"), "catalog-suggestion badge shown before any ledger row");
const financePane = body.slice(body.indexOf("Phải trả đối tác"));
const tileZone = financePane.slice(0, financePane.indexOf("Ghi nhận phải trả"));
assert.ok((tileZone.match(/— tr VND/g) || []).length >= 3, "partner tiles show — tr VND for UNKNOWN");
assert.ok(!tileZone.includes("0 tr VND"), "no manufactured 0 tile in the partner block");
ok("no-ledger state shows — (UNKNOWN), never 0");

console.log("STEP 5 — GHI NHẬN PHẢI TRẢ emits partner_payable_record");
invoke(JOURNEY);
await tick(140);
await click("Lô Hàng", "a", $("aside")[0]);
await click(SHIPMENT, "a", $("table.tbl")[0]);
await click("Tài chính / Công nợ", "button", window.document.getElementById("workspace-tabs"));
await tick();
triggers = [];
type(byPlaceholder("VD: 20000000"), "57.000.000");
await click("GHI NHẬN PHẢI TRẢ");
await tick();
const obls = eventsOf("partner_payable_record");
assert.equal(obls.length, 1, "exactly one partner_payable_record trigger");
const oblPayload = obls[0].payload;
assert.equal(oblPayload.shipmentId, SHIPMENT);
assert.equal(oblPayload.partnerId, PARTNER_ID);
assert.equal(oblPayload.amount, 57000000);
assert.equal(oblPayload.currency, "VND");
assert.ok(oblPayload.requestId, "request identity present");
ok(`partner_payable_record emitted for ${oblPayload.partnerId} · ${nf(oblPayload.amount)} ${oblPayload.currency}`);

console.log("STEP 6 — payment intent identity: replay absorbed, new intent distinct");
triggers = [];
type(byPlaceholder("VD: 20000000"), "20.000.000");
await tick();
const payBtn = findClickable("TRẢ ĐỐI TÁC", "button");
assert.ok(payBtn, "partner payment button missing");
// Double click with no re-render in between: React has not cleared the
// amount draft, so the handler runs twice — it MUST replay the same id.
payBtn.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
payBtn.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
await tick(150);
const pays = eventsOf("partner_payment_record");
assert.equal(pays.length, 2, "double click must reach the handler twice");
assert.equal(pays[0].payload.requestId, pays[1].payload.requestId, "double click replays ONE request identity");
assert.equal(pays[0].payload.amount, 20000000);
assert.equal(pays[0].payload.currency, "VND");
assert.equal(pays[0].payload.partnerId, PARTNER_ID);

// A NEW amount draft mints a NEW intent — never swallowed as a replay.
type(byPlaceholder("VD: 20000000"), "17.000.000");
await click("TRẢ ĐỐI TÁC");
await tick();
const pays2 = eventsOf("partner_payment_record");
assert.equal(pays2.length, 3);
assert.notEqual(pays2[2].payload.requestId, pays[0].payload.requestId, "new intent = new request identity");
assert.equal(pays2[2].payload.amount, 17000000);
ok(`double click replayed ${pays[0].payload.requestId}`);
ok(`new intent minted ${pays2[2].payload.requestId}`);

console.log(`\nC2B DOM ACCEPTANCE PASS — ${passed} checks`);
