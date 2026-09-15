// ============================================================================
// C2A DOM acceptance — runs the REAL production bundle
// (component/dist/logi-shell.js) in a DOM (jsdom) against a fixture generated
// from the REAL Logistics backend (scripts/gen_c2a_fixture.py), and drives it
// with real DOM events through the Streamlit Components v2 contract:
// `mount({data, parentElement, setTriggerValue})` re-invoked with new data.
//
// Proven here (screens rendering alone is NOT a pass — every step fires or
// asserts real typed events / real backend values):
//   1. Finance Actual READ renders the real booked line with cost + VAT
//   2. Actual profit + margin render from backend truth (not the quote)
//   3. Currencies are explicit; nothing is labelled VND when it is not
//   4. UNKNOWN != ZERO — an empty actual book shows "—", never "0"
//   5. FINANCE ACTUAL WRITE emits `finance_actual_save` with the real payload
//   6. One receipt emits `payment_record` with a stable request identity;
//      a double click replays the SAME id; a new intent mints a NEW id
//
// Run: node tests/component/dom_acceptance_c2a.mjs
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
  readFileSync(path.join(ROOT, "tests/component/fixtures/view_model_c2a.json"), "utf8")
);
const SHIPMENT = FIXTURE.shipment;
const JOURNEY = FIXTURE.journey;
const LOT = JOURNEY.shipments.find((x) => x.id === SHIPMENT);
const FIN = LOT.finance;

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

/** Choose an option of a real <select> through React's own value tracking. */
function selectByValue(sel, value) {
  Object.getOwnPropertyDescriptor(window.HTMLSelectElement.prototype, "value").set.call(sel, value);
  sel.dispatchEvent(new window.Event("change", { bubbles: true }));
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
// STEP 1 — boot + open the ONE shipment's Finance Actual tab
// ---------------------------------------------------------------------------

console.log("STEP 1 — boot bundle and open Finance Actual");
{
  const mod = await import(path.join(ROOT, "component/dist/logi-shell.js"));
  assert.equal(typeof mod.default, "function", "bundle must default-export the mount function");
  mountRef.current = mod.default;
  invoke(JOURNEY);
  await tick(140);
  const t = bodyText();
  assert.ok(!t.includes("process is not defined"), "process is not defined leaked");
  assert.ok(!t.includes("BidiComponent Error"), "BidiComponent Error rendered");

  await click("Lô Hàng", "a", $("aside")[0]);
  await click(SHIPMENT, "a", $("table.tbl")[0]);
  assert.equal(text($("h1")[0]), SHIPMENT, "detail header wrong");
  await click("Tài chính / Công nợ", "button", window.document.getElementById("workspace-tabs"));
  ok(`Finance Actual tab open for ${SHIPMENT}`);
}

// ---------------------------------------------------------------------------
// STEP 2 — A: real Finance Actual read rendered
// ---------------------------------------------------------------------------

console.log("STEP 2 — Finance Actual read (real backend values)");
{
  const t = bodyText();
  for (const line of FIN.actual) {
    assert.ok(t.includes(line.label), `actual line missing: ${line.label}`);
    assert.ok(t.includes(`${nf(line.amount)} ${line.ccy}`), `actual sell amount missing for ${line.label}`);
    assert.ok(t.includes(`${nf(line.cost)} ${line.ccy}`), `actual cost missing for ${line.label}`);
    assert.ok(t.includes(`VAT ${nf(line.vat)}%`), `actual VAT missing for ${line.label}`);
  }
  assert.ok(t.includes(`Doanh thu thực tế (chưa VAT)`), "actual revenue row missing");
  assert.ok(t.includes(nf(FIN.receivableNet)), "actual revenue value missing");
  ok(`${FIN.actual.length} actual line(s) rendered with sell + cost + VAT`);
}

// ---------------------------------------------------------------------------
// STEP 3 — J: actual profit / margin from backend truth
// ---------------------------------------------------------------------------

console.log("STEP 3 — actual profit and margin");
{
  const t = bodyText();
  assert.ok(t.includes("Lợi nhuận thực tế"), "actual profit block missing");
  assert.ok(t.includes(nf(FIN.profit)), `actual profit ${FIN.profit} not rendered`);
  assert.ok(t.includes(`${FIN.profitMargin.toLocaleString(vi)}%`), `margin ${FIN.profitMargin}% not rendered`);
  // The formula is stated, and it is the actual-only formula.
  assert.ok(t.includes("Doanh thu thực tế − chi phí thực tế − hoa hồng"), "profit formula note missing");
  assert.ok(t.includes("Không lấy số báo giá để bù chỗ trống"), "quote-independence note missing");
  // Quote Estimate stays in its own, clearly-labelled card.
  assert.ok(t.includes("Báo giá / Dự kiến — chưa phải số thực thu/chi"), "quote-vs-actual separation label missing");
  ok(`profit ${nf(FIN.profit)} ${FIN.currency} / margin ${FIN.profitMargin}% rendered from actuals only`);
}

// ---------------------------------------------------------------------------
// STEP 4 — E + I: currency explicit, outstanding from backend truth
// ---------------------------------------------------------------------------

console.log("STEP 4 — currency explicit + outstanding");
{
  const t = bodyText();
  assert.ok(t.includes(`Phải thu khách hàng (${FIN.currency})`), "AR heading must carry the real currency");
  assert.ok(t.includes(`Phải trả đối tác (${FIN.currency})`), "AP heading must carry the real currency");
  assert.ok(t.includes(`${(FIN.outstanding / 1e6).toLocaleString(vi)} tr ${FIN.currency}`),
    "outstanding must be shown with its currency");
  assert.ok(t.includes("do backend tính"), "outstanding must be attributed to the backend");
  ok(`AR/AP labelled ${FIN.currency}; outstanding ${nf(FIN.outstanding)} ${FIN.currency}`);
}

// ---------------------------------------------------------------------------
// STEP 5 — B: Finance Actual WRITE emits the real typed event
// ---------------------------------------------------------------------------

console.log("STEP 5 — finance_actual_save typed event (restored service entry)");
{
  // LOGI_FINANCE_ACTUAL_ENTRY_PARITY_01 replaced the free-text box with the
  // canonical service picker, so the write is now: pick a catalog service →
  // type the money → save. Same typed event, same canonical row.
  await click("THÊM DỊCH VỤ / CHI PHÍ", "button");
  const form = window.document.getElementById("finance-actual-form");
  assert.ok(form, "the service/cost entry form must open");

  const picker = $("select", form)[0];
  assert.ok(picker, "the service picker must be a real <select>");
  const optionValues = $("option", form).map((o) => o.value).filter(Boolean);
  const catalog = FIXTURE.journey.financeServiceCatalog;
  assert.equal(optionValues.length, catalog.length,
    `picker options must come from the projected catalog (${catalog.length}), got ${optionValues.length}`);
  assert.deepEqual(optionValues, catalog.map((e) => e.code), "the picker IS the backend catalog");

  selectByValue(picker, "PKH");
  await tick();
  const codeInput = $("input[readonly]", form)[0];
  assert.equal(codeInput.value, "PKH", "Mã dịch vụ must arrive auto-filled from the catalog");
  const inputs = $("input", form);
  const unit = inputs.find((i) => i.placeholder === "Lần");
  assert.equal(unit.value, "Lần", "Đơn vị must arrive from the catalog entry");

  const inp = (ph) => {
    const el = $("input", form).find((i) => (i.placeholder || "").startsWith(ph));
    assert.ok(el, `input with placeholder "${ph}" not found in the entry form`);
    return el;
  };
  type(inp("VD: 57000000"), "800000");
  type(inp("VD: 62000000"), "1200000");
  type(inp("1"), "3");
  type(inp("VD: 8"), "8");
  type(inp("Ghi chú cho dòng này"), "Hóa đơn số 12");
  await tick();

  triggers = [];
  await click("LƯU DÒNG THỰC TẾ", "button", form);
  await tick(120);

  const sent = eventsOf("finance_actual_save");
  assert.equal(sent.length, 1, `expected exactly 1 finance_actual_save, got ${sent.length}`);
  const payload = sent[0].payload;
  assert.equal(payload.shipmentId, SHIPMENT);
  assert.equal(payload.line.name, "Phí kiểm hóa", "the catalog name is what gets booked");
  assert.equal(payload.line.code, "PKH");
  assert.equal(payload.line.unit, "Lần");
  assert.equal(payload.line.qty, "3");
  assert.equal(payload.line.price, "1200000");
  assert.equal(payload.line.cost, "800000");
  assert.equal(payload.line.vat, "8");
  assert.equal(payload.line.note, "Hóa đơn số 12");
  assert.ok(!("id" in payload.line), "a NEW line must not carry an id — the backend mints it");
  assert.match(payload.requestId, /^FACTUAL-REQ-/, "the write must carry its request identity");
  assert.ok(typeof sent[0].seq === "number" && sent[0].seq > 0, "seq must be a positive number");
  ok("finance_actual_save emitted with the catalog code + unit + note payload");
}

// ---------------------------------------------------------------------------
// STEP 6 — G + H: one receipt, stable request identity, new intent = new id
// ---------------------------------------------------------------------------

console.log("STEP 6 — payment_record identity and idempotency");
{
  triggers = [];
  await click("GHI NHẬN THANH TOÁN", "button");
  assert.ok(bodyText().includes(`Số tiền (${FIN.currency})`), "payment sheet must carry the real currency");
  assert.ok(bodyText().includes("không quy đổi"), "payment sheet must state there is no FX conversion");

  type(byPlaceholder("VD: 150000000"), "25000000");
  await tick();
  const saveBtn = findClickable("LƯU KHOẢN THU", "button");
  assert.ok(saveBtn, "payment save button missing");

  // Double click with no re-render in between: React has not unmounted the
  // sheet, so the handler runs twice — it MUST replay the same request id.
  saveBtn.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
  saveBtn.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
  await tick(150);

  const sent = eventsOf("payment_record");
  assert.equal(sent.length, 2, `expected the double click to reach the handler twice, got ${sent.length}`);
  const ids = new Set(sent.map((e) => e.payload.requestId));
  assert.equal(ids.size, 1, `one payment intent must replay ONE request id, got ${[...ids].join(", ")}`);
  const first = sent[0].payload;
  assert.equal(first.shipmentId, SHIPMENT);
  assert.equal(first.amount, 25000000);
  assert.match(first.requestId, /^PAY-REQ-/, "request identity must be namespaced");
  ok(`double click replayed one request identity: ${first.requestId}`);

  // A genuinely NEW receipt intent must NOT be swallowed as a replay.
  triggers = [];
  await click("GHI NHẬN THANH TOÁN", "button");
  type(byPlaceholder("VD: 150000000"), "25000000");
  await tick();
  await click("LƯU KHOẢN THU", "button");
  await tick(150);
  const second = eventsOf("payment_record");
  assert.equal(second.length, 1, "a new intent must post exactly one event");
  assert.equal(second[0].payload.amount, 25000000);
  assert.notEqual(second[0].payload.requestId, first.requestId,
    "a second genuine receipt of the same amount must mint a NEW request identity");
  ok(`new intent minted a new request identity: ${second[0].payload.requestId}`);
}

// ---------------------------------------------------------------------------
// STEP 7 — F: UNKNOWN != ZERO on an empty actual book
// ---------------------------------------------------------------------------

console.log("STEP 7 — UNKNOWN != ZERO (empty actual book)");
{
  const empty = FIXTURE.emptyBook.shipments.find((x) => x.id === SHIPMENT).finance;
  assert.equal(empty.profit, null, "fixture precondition: profit must be null");
  assert.equal(empty.profitMargin, null, "fixture precondition: margin must be null");
  assert.equal(empty.hasActualLines, false, "fixture precondition: no booked line");

  invoke(FIXTURE.emptyBook);
  await tick(160);
  const t = bodyText();
  assert.ok(t.includes("Chưa ghi nhận dòng thực tế nào"), "empty-book explanation missing");
  assert.ok(t.includes("chưa xác định"), "empty book must say UNKNOWN, not zero");
  const profitBlock = text($("div").find((d) => d.className.includes("bg-emerald-50") && text(d).includes("Lãi / Lỗ thực tế")));
  assert.ok(profitBlock.includes("— VND"), `profit must render an em dash, got: ${profitBlock}`);
  assert.ok(!profitBlock.includes("0 VND"), "profit must NOT render as 0 for an empty book");
  ok("empty actual book shows — for profit and margin, never 0");
}

// ---------------------------------------------------------------------------
// STEP 8 — E: a non-VND shipment is labelled, never converted
// ---------------------------------------------------------------------------

console.log("STEP 8 — non-VND shipment stays in its own currency");
{
  const usd = FIXTURE.usd.shipments.find((x) => x.id === SHIPMENT).finance;
  assert.equal(usd.currency, "USD", "fixture precondition: USD shipment");

  invoke(FIXTURE.usd);
  await tick(160);
  const t = bodyText();
  assert.ok(t.includes("Phải thu khách hàng (USD)"), "AR heading must say USD");
  assert.ok(t.includes("Phải trả đối tác (USD)"), "AP heading must say USD");
  assert.ok(t.includes(`${nf(usd.receivableNet)} USD`), "USD revenue must render unconverted");
  assert.ok(t.includes(`${nf(usd.profit)} USD`), "USD profit must render unconverted");
  assert.ok(!t.includes("Phải thu khách hàng (VND)"), "no hardcoded VND label may survive");
  ok(`USD shipment labelled USD end to end (revenue ${nf(usd.receivableNet)}, profit ${nf(usd.profit)})`);
}

console.log(`\nC2A DOM ACCEPTANCE PASS — ${passed} checks`);
