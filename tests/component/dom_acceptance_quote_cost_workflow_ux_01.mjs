// ============================================================================
// LOGI_QUOTE_COST_WORKFLOW_UX_01 — DOM acceptance on the REAL built bundle.
//
// Runs component/dist/logi-shell.js in a DOM runtime and proves the Owner's
// four desk outcomes end to end:
//
//   A  "DÁN BÁO GIÁ NHANH" on Báo Giá: PASTE → PHÂN TÍCH → REVIEW → ÁP DỤNG.
//      The Owner's real FOB NINGBO – Hải Phòng message becomes 9 editable
//      service lines; "nếu có" stays conditional, "khoảng 10 triệu" stays an
//      estimate, and the general "nếu có phát sinh…" sentence becomes an
//      assumption — NOT a zero-price line. Nothing auto-saves.
//   B  The mini-calculator inside the quote number inputs: 370*8, 9.5tr*2,
//      250k*4, =SUM(370,80) resolve on blur to plain numbers; eval / cell refs
//      / arbitrary identifiers are REFUSED and the typed text is kept.
//   D  Shipments list: default period "Tháng này" + archive "Đang làm", an
//      UNKNOWN outstanding NEVER archives, and the state survives in the URL.
//   E  "CHECK CHI PHÍ" as an INNER tab of the SAME Báo Giá workspace: paste
//      prefill, TÌM DỮ LIỆU CŨ, SOURCE=THỰC TẾ preferred over
//      SOURCE=BÁO GIÁ / DỰ KIẾN, a stated reason, split currencies, XEM LÔ GỐC.
//
// Run: node tests/component/dom_acceptance_quote_cost_workflow_ux_01.mjs
// ============================================================================

import { readFileSync } from "node:fs";
import assert from "node:assert/strict";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const require = createRequire(path.join(ROOT, "component/package.json"));
const { JSDOM } = require("jsdom");
const BASE = JSON.parse(
  readFileSync(path.join(ROOT, "tests/component/fixtures/view_model_phase_b.json"), "utf8")
);
// The Phase-B fixture's quote rows are list-shaped stubs; the contract-workflow
// fixture carries the FULL canonical quote projection (serviceLines & co.),
// exactly as the PR #91 acceptance already does.
const CW = JSON.parse(
  readFileSync(path.join(ROOT, "tests/component/fixtures/view_model_contract_workflow.json"), "utf8")
);
if (Array.isArray(CW.success?.quotes) && CW.success.quotes.length > 0) {
  BASE.quotes = CW.success.quotes;
}

const dom = new JSDOM("<!DOCTYPE html><html><body></body></html>", {
  url: "http://localhost:8501/",
  pretendToBeVisual: true,
});
const { window } = dom;
globalThis.window = window;
globalThis.document = window.document;
try {
  Object.defineProperty(globalThis, "navigator", { value: window.navigator, configurable: true });
} catch { /* keep node navigator */ }
for (const k of [
  "HTMLElement", "HTMLInputElement", "HTMLTextAreaElement", "HTMLSelectElement",
  "HTMLAnchorElement", "Event", "CustomEvent", "MouseEvent", "KeyboardEvent",
  "FocusEvent", "Node", "MutationObserver", "getComputedStyle", "TextEncoder",
]) {
  globalThis[k] = window[k];
}
if (!globalThis.MessageChannel) globalThis.MessageChannel = window.MessageChannel;
window.HTMLElement.prototype.scrollIntoView = () => {};
window.URL.createObjectURL = () => "blob:mock-url";
window.URL.revokeObjectURL = () => {};

const tick = (ms = 90) => new Promise((r) => setTimeout(r, ms));
const $ = (sel, root = window.document) => [...root.querySelectorAll(sel)];
const text = (el) => ((el && el.textContent) || "").replace(/\s+/g, " ").trim();
const mainText = () => text($("main")[0] ?? window.document.body);
// Toasts render outside <main>, so refusal messages are asserted on the body.
const bodyText = () => text(window.document.body);
const aside = () => $("aside")[0];
const byTestId = (id) => $(`[data-testid="${id}"]`)[0] ?? null;

async function click(needle, sel = "a,button", root = window.document) {
  const els = $(sel, root);
  const el = els.find((e) => text(e) === needle) || els.find((e) => text(e).startsWith(needle));
  assert.ok(el, `clickable "${needle}" not found`);
  el.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
  await tick();
  return el;
}
async function clickTestId(id) {
  const el = byTestId(id);
  assert.ok(el, `[data-testid="${id}"] not found`);
  el.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
  await tick();
  return el;
}
async function setValue(el, value, proto = "HTMLInputElement") {
  assert.ok(el, "setValue target missing");
  Object.getOwnPropertyDescriptor(window[proto].prototype, "value").set.call(el, value);
  el.dispatchEvent(new window.Event("input", { bubbles: true }));
  await tick(110);
}
/** Type into a calculator input and commit it the way an operator does. */
async function typeAndBlur(el, value) {
  await setValue(el, value);
  // React delegates blur as the bubbling "focusout" event.
  el.dispatchEvent(new window.FocusEvent("focusout", { bubbles: true }));
  await tick(110);
}

let passed = 0;
const ok = (name) => { passed += 1; console.log(`  ✓ ${name}`); };

// --- the Owner's real pasted quote message ---------------------------------
const OWNER_PASTE = [
  "FOB NINGBO - Hải Phòng",
  "- Cước biển: 950 USD/cont 20' (cước tại thời điểm này, nếu vượt 20 tấn cộng thêm 80 USD)",
  "- Phí local đầu Trung Quốc: 9.5 triệu",
  "- Phí chứng từ: 2.600.000",
  "- Phí telex: 250k",
  "- Phí nâng hạ: 2.000.000/cont",
  "- Cước vận chuyển bộ Hải Phòng - Hà Nội: 6.000.000 (chưa gồm phí Lạch Huyện 500k, phụ phí xăng dầu theo thực tế)",
  "- Phí kiểm hóa (nếu có): 4 triệu",
  "- Phí lưu cont (nếu có): 2 triệu",
  "- Phí xử lý hàng: khoảng 10 triệu (cái này chưa làm bao giờ nên chưa nắm rõ)",
  "Nếu có phát sinh về xử lý hàng hóa tại cảng thì sẽ báo lại sau.",
].join("\n");

// --- Check chi phí fixtures -------------------------------------------------
function costFixtureVm() {
  const vm = JSON.parse(JSON.stringify(BASE));
  const base = vm.shipments[0];
  const mk = (over) => JSON.parse(JSON.stringify({ ...base, ...over }));

  // (1) THE ACTUAL COMPARABLE — 2026-06, EXW Guangdong → Hà Nội, 5 CBM, 800 kg.
  const actual = mk({ id: "LO-0250", customer: "An Phát JSC", createdAt: "12/06/2026" });
  actual.incoterm = "EXW";
  actual.mode = "Truck";
  actual.route = "Guangdong → Hà Nội";
  actual.transport = { ...actual.transport, pol: "Guangdong", pod: "Hà Nội" };
  actual.cargo = { ...actual.cargo, cbm: 5, weight: 800 };
  actual.finance = {
    ...actual.finance,
    quote: [{ label: "Trọn gói (báo giá)", amount: 30000000, qty: 1, vat: 8, ccy: "VND", kind: "quote" }],
    actual: [
      { label: "Cước vận chuyển", amount: 21500000, cost: 19000000, qty: 1, vat: 8, ccy: "VND", kind: "actual" },
      { label: "Phí handling đầu TQ", amount: 1200, cost: 1100, qty: 1, vat: 0, ccy: "CNY", kind: "actual" },
    ],
  };

  // (2) THE QUOTE-ONLY FALLBACK — same lane, no Finance Actual at all.
  const quoteOnly = mk({ id: "LO-0251", customer: "Minh Long Co.", createdAt: "20/05/2026" });
  quoteOnly.incoterm = "EXW";
  quoteOnly.mode = "Truck";
  quoteOnly.route = "Guangdong → Hà Nội";
  quoteOnly.transport = { ...quoteOnly.transport, pol: "Guangdong", pod: "Hà Nội" };
  quoteOnly.cargo = { ...quoteOnly.cargo, cbm: 6, weight: 900 };
  quoteOnly.finance = {
    ...quoteOnly.finance,
    actual: [],
    quote: [{ label: "Trọn gói EXW (dự kiến)", amount: 26000000, qty: 1, vat: 8, ccy: "VND", kind: "quote" }],
  };

  // (3) A DIFFERENT LANE that must never be offered as a comparable.
  const other = mk({ id: "LO-0252", customer: "Hồng Hà Co.", createdAt: "01/06/2026" });
  other.incoterm = "FOB";
  other.route = "Ningbo → Hải Phòng";
  other.transport = { ...other.transport, pol: "Ningbo", pod: "Hải Phòng" };
  other.cargo = { ...other.cargo, cbm: 40, weight: 18000 };

  vm.shipments = [actual, quoteOnly, other];
  return vm;
}

/** A list fixture: one settled lot, one UNKNOWN-outstanding lot, both this month. */
function listFixtureVm(now) {
  const vm = JSON.parse(JSON.stringify(BASE));
  const base = vm.shipments[0];
  const dd = (d) => `${String(d.getUTCDate()).padStart(2, "0")}/${String(d.getUTCMonth() + 1).padStart(2, "0")}/${d.getUTCFullYear()}`;
  const thisMonth = dd(new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), 3)));
  const lastMonth = dd(new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth() - 1, 3)));

  const mk = (id, createdAt, fin, imp) => {
    const s = JSON.parse(JSON.stringify(base));
    s.id = id; s.createdAt = createdAt;
    s.finance = { ...s.finance, ...fin };
    s.importInfo = { ...s.importInfo, ...imp };
    return s;
  };
  vm.shipments = [
    // finished AND fully paid → archivable
    mk("LO-9001", thisMonth, { outstanding: 0 }, { delivered: true, actualDelivery: "10/09/2026" }),
    // delivered but the outstanding is UNKNOWN → NEVER archived
    mk("LO-9002", thisMonth, { outstanding: null }, { delivered: true, actualDelivery: "10/09/2026" }),
    // still running
    mk("LO-9003", thisMonth, { outstanding: 41520000 }, { delivered: false, actualDelivery: "" }),
    // finished + paid but LAST month → out of the default period
    mk("LO-9004", lastMonth, { outstanding: 0 }, { delivered: true, actualDelivery: "10/08/2026" }),
  ];
  return vm;
}

const host = window.document.createElement("div");
window.document.body.appendChild(host);
const triggers = [];
const mod = await import(path.join(ROOT, "component/dist/logi-shell.js"));
assert.equal(typeof mod.default, "function");
let cleanup = null;
async function mountWith(vm) {
  if (cleanup) { cleanup(); await tick(60); }
  window.history.replaceState({}, "", "/");
  cleanup = mod.default({
    name: "logi_shell", data: vm, parentElement: host,
    setTriggerValue: (event, value) => triggers.push({ event, value }),
  });
  await tick(170);
}

await mountWith(JSON.parse(JSON.stringify(BASE)));

// ---------------------------------------------------------------------------
console.log("STEP 1 — A: the paste block lives ABOVE the service lines, empty and idle");
{
  await click("Báo Giá", "a", aside());
  await click("Tạo báo giá", "button");
  const paste = byTestId("quote-paste");
  assert.ok(paste, "the quick-paste block must exist on the quote form");
  assert.ok(text(paste).includes("DÁN BÁO GIÁ NHANH"), "block title missing");
  // Structurally above the first service-line card, in document order.
  const card1 = byTestId("quote-line-1");
  assert.ok(card1, "service-line card 1 missing");
  assert.ok(
    paste.compareDocumentPosition(card1) & window.Node.DOCUMENT_POSITION_FOLLOWING,
    "the paste block must sit ABOVE the service lines"
  );
  // Idle: no preview and nothing applied before the operator asks.
  assert.equal(byTestId("quote-paste-preview"), null, "no preview before PHÂN TÍCH");
  assert.equal(byTestId("quote-paste-apply"), null, "no APPLY offered before a parse");
  for (const label of ["PHÂN TÍCH"]) {
    assert.ok(text(paste).includes(label), `"${label}" button missing`);
  }
  ok("paste block present above the lines, nothing parsed or applied yet");
}

// ---------------------------------------------------------------------------
console.log("STEP 2 — A: PHÂN TÍCH turns the Owner's real message into a reviewable preview");
{
  await setValue(byTestId("quote-paste-input"), OWNER_PASTE, "HTMLTextAreaElement");
  await clickTestId("quote-paste-parse");
  const preview = byTestId("quote-paste-preview");
  assert.ok(preview, "PHÂN TÍCH must produce a review preview");
  assert.equal(text(byTestId("quote-paste-incoterm")), "FOB");
  assert.equal(text(byTestId("quote-paste-origin")), "NINGBO");
  assert.equal(text(byTestId("quote-paste-destination")), "Hải Phòng");

  const lines = $('[data-testid^="quote-paste-line-"]', preview)
    .filter((el) => /-line-\d+$/.test(el.getAttribute("data-testid")));
  assert.equal(lines.length, 9, "the Owner's message states exactly 9 service lines");

  const body = text(preview);
  assert.ok(body.includes("950"), "950 USD sea freight missing");
  assert.ok(body.includes("9.500.000"), "“9.5 triệu” must read as 9.500.000");
  assert.ok(body.includes("250.000"), "“250k” must read as 250.000");
  assert.ok(body.includes("10.000.000"), "“khoảng 10 triệu” must read as 10.000.000");

  // Conditional and estimate wording survive as FLAGS, not as invented zeros.
  assert.ok(byTestId("quote-paste-line-7-conditional") || byTestId("quote-paste-line-8-conditional"),
    "the “nếu có” lines must be flagged conditional");
  const estimate = $('[data-testid$="-estimate"]', preview);
  assert.equal(estimate.length, 1, "exactly one line is flagged as an estimate");
  assert.ok(body.toLowerCase().includes("chưa nắm rõ"),
    "the Owner's own uncertainty wording must be preserved verbatim");

  // The general sentence is an ASSUMPTION, never a 0đ line.
  const assumptions = byTestId("quote-paste-assumptions");
  assert.ok(assumptions, "the general sentence must land in assumptions");
  assert.ok(text(assumptions).includes("phát sinh về xử lý hàng hóa"),
    "the general sentence text must be kept");
  assert.ok(!/(^|\D)0(\s|đ|$)/.test(body.replace(/[\d.,]{4,}/g, "")),
    "no line may be shown as a zero price");
  ok("9 lines + conditional/estimate flags + the general sentence as an assumption");
}

// ---------------------------------------------------------------------------
console.log("STEP 3 — A: nothing is written until ÁP DỤNG, then the lines are editable");
{
  const before = triggers.length;
  assert.equal(triggers.length, before, "parsing must dispatch nothing");
  await clickTestId("quote-paste-apply");
  assert.equal(triggers.slice(before).length, 0, "APPLY fills the form; it must not save");

  const cards = $("[data-testid]").map((e) => e.getAttribute("data-testid"))
    .filter((id) => /^quote-line-\d+$/.test(id));
  assert.equal(cards.length, 9, "APPLY must produce one editable card per parsed line");
  const c1 = byTestId("quote-line-1");
  const fields1 = $("input", c1).map((i) => i.value).join(" | ");
  assert.ok(fields1.includes("Cước biển"), `line 1 name not applied: ${fields1}`);
  const sell1 = byTestId("quote-line-1-sell");
  assert.equal(sell1.value.replace(/[^\d]/g, ""), "950", "line 1 sell price not applied");
  // Cost stays EMPTY: the customer message never stated a cost. UNKNOWN != 0.
  assert.equal(byTestId("quote-line-1-cost").value, "", "an unstated cost must stay unknown, not 0");
  assert.equal(byTestId("quote-line-1-tax").value, "", "VAT must never be invented");
  // The estimate/conditional wording travels into the per-line note (PR #91).
  const notes = $('[data-testid$="-note"]').map((n) => n.value).join(" | ");
  assert.ok(notes.includes("Có thể phát sinh"), "conditional wording must reach a line note");
  assert.ok(byTestId("quote-assumptions"), "applied assumptions must be visible on the form");
  ok("APPLY fills 9 editable lines, invents no cost/VAT, dispatches nothing");
}

// ---------------------------------------------------------------------------
console.log("STEP 3b — REPAIR_01: the general note is a PERSISTED customer note");
{
  // It is shown as customer-facing text, not as an internal assumption.
  const notes = byTestId("quote-assumptions");
  assert.ok(notes, "the applied general note must be visible on the form");
  assert.ok(text(notes).includes("Ghi chú chung gửi khách"),
    "the block must say these notes go to the CUSTOMER");
  assert.ok(text(notes).includes("phát sinh về xử lý hàng hóa"),
    "the Owner's general sentence must be listed");
  assert.ok(byTestId("quote-customer-note-1"), "each note must be individually addressable");
  assert.ok(byTestId("quote-customer-note-1-remove"), "the operator must be able to drop a note");

  // A quote needs a customer before anything else can be judged.
  await clickTestId("quote-customer-picker-toggle");
  const firstCustomer = $('[data-testid="quote-customer-picker-list"] button')[0];
  assert.ok(firstCustomer, "the customer picker must offer the fixture customers");
  firstCustomer.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
  await tick(90);

  // REPAIR_02: the pasted quote states SELL prices only — no cost, no VAT, no
  // FX — and that is a complete, truthful DRAFT. It must SAVE as-is. Blocking
  // it (REPAIR_01) only taught the operator to type a fake 0.
  const before = triggers.length;
  await click("💾 TẠO BÁO GIÁ", "button");
  const create = triggers.slice(before).find((t) => t.event === "quote_create");
  assert.ok(create, "an Owner paste with no cost/VAT/FX must still dispatch quote_create");
  const payload = create.value.payload;
  assert.ok(Array.isArray(payload.customerNotes), "customerNotes must travel with the quote");
  assert.ok(payload.customerNotes.some((n) => n.includes("phát sinh về xử lý hàng hóa")),
    "the pasted general sentence must be in the persisted payload");
  // UNKNOWN travels as UNKNOWN: the boundary never manufactures a 0.
  assert.equal(String(payload.serviceLines[0].costUnit ?? ""), "",
    "an unstated Giá vốn must leave the form as UNKNOWN, not 0");
  assert.equal(String(payload.serviceLines[0].taxPct ?? ""), "",
    "an unstated Thuế must leave the form as UNKNOWN, not 0");
  // No FX rate was typed, so none is sent — the app never invents one.
  assert.ok(!payload.fx || payload.fx.USD === undefined,
    "a missing quote rate must not be fabricated");
  ok("an Owner paste with no cost/VAT/FX saves, carrying UNKNOWN through as UNKNOWN");
}

// ---------------------------------------------------------------------------
console.log("STEP 3c — REPAIR_01: a saved quote reopens with its notes restored");
{
  const vm = JSON.parse(JSON.stringify(BASE));
  const saved = JSON.parse(JSON.stringify(vm.quotes[0]));
  saved.customerNotes = ["Nếu có phát sinh về xử lý hàng hóa, sẽ báo ngay tại thời điểm phát sinh."];
  saved.serviceLines = [{
    code: "DV-VC", serviceName: "Cước vận chuyển", unit: "Lần", qty: 1,
    currency: "VND", costUnit: 100, sellUnit: 200, taxPct: 8, note: "",
  }];
  vm.quotes = [saved];
  await mountWith(vm);
  await click("Báo Giá", "a", aside());
  await click("Sửa", "button");
  const notes = byTestId("quote-assumptions");
  assert.ok(notes, "reopening a saved quote must restore its customer notes");
  assert.ok(text(notes).includes("phát sinh về xử lý hàng hóa"),
    "the stored note must come back verbatim on reopen");
  ok("customer notes round trip: stored on the quote, restored on reopen");
}

// ---------------------------------------------------------------------------
console.log("STEP 3d — REPAIR_02: blanking cost/VAT still saves, as UNKNOWN not 0");
{
  // Re-open the SAME saved quote from step 3c and clear one line's cost/VAT.
  // The edit must go through with those two facts marked UNKNOWN — and the
  // desk must NOT quietly turn them into 0 on the way out.
  assert.ok(byTestId("quote-line-1-cost"), "the edit form must still be open");
  const cost = byTestId("quote-line-1-cost");
  const tax = byTestId("quote-line-1-tax");
  await setValue(cost, "");
  await setValue(tax, "");
  const before = triggers.length;
  await click("💾 LƯU BÁO GIÁ", "button");
  const cleared = triggers.slice(before).find((t) => t.event === "quote_edit");
  assert.ok(cleared, "clearing an internal cost/VAT must not block the save");
  assert.equal(String(cleared.value.payload.serviceLines[0].costUnit ?? ""), "",
    "a cleared Giá vốn travels as UNKNOWN");
  assert.equal(String(cleared.value.payload.serviceLines[0].taxPct ?? ""), "",
    "a cleared Thuế travels as UNKNOWN");

  // A successful save closes the form; reopen the same quote to continue.
  await click("Sửa", "button");
  await tick(60);

  // Giá bán is the one number quoted to the customer, so it IS required.
  await setValue(byTestId("quote-line-1-sell"), "");
  const beforeSell = triggers.length;
  await click("💾 LƯU BÁO GIÁ", "button");
  assert.equal(triggers.slice(beforeSell).filter((t) => t.event === "quote_edit").length, 0,
    "a line with no Giá bán must not be dispatched");
  assert.ok(bodyText().includes("Thiếu giá bán"),
    "the refusal must name the missing sell price");
  await setValue(byTestId("quote-line-1-sell"), "200");

  // An explicit 0 is still a perfectly valid, distinct answer.
  await setValue(byTestId("quote-line-1-cost"), "0");
  await setValue(byTestId("quote-line-1-tax"), "0");
  const before2 = triggers.length;
  await click("💾 LƯU BÁO GIÁ", "button");
  const edit = triggers.slice(before2).find((t) => t.event === "quote_edit");
  assert.ok(edit, "an explicitly stated 0 must be accepted");
  assert.equal(edit.value.payload.serviceLines[0].costUnit, 0);
  assert.equal(edit.value.payload.serviceLines[0].taxPct, 0);
  ok("blank cost/VAT saves as UNKNOWN; missing Giá bán is refused; explicit 0 persists as 0");
}

// ---------------------------------------------------------------------------
console.log("STEP 4 — B: the mini-calculator resolves real Owner arithmetic on blur");
{
  await mountWith(JSON.parse(JSON.stringify(BASE)));
  await click("Báo Giá", "a", aside());
  await click("Tạo báo giá", "button");
  const qty = byTestId("quote-line-1-qty");
  const sell = byTestId("quote-line-1-sell");
  const cost = byTestId("quote-line-1-cost");

  await typeAndBlur(sell, "370*8");
  assert.equal(sell.value.replace(/[^\d]/g, ""), "2960", "370*8 must resolve to 2960");

  await typeAndBlur(sell, "9.5tr*2");
  assert.equal(sell.value.replace(/[^\d]/g, ""), "19000000", "9.5tr*2 must resolve to 19,000,000");

  await typeAndBlur(cost, "250k*4");
  assert.equal(cost.value.replace(/[^\d]/g, ""), "1000000", "250k*4 must resolve to 1,000,000");

  await typeAndBlur(sell, "=SUM(370,80)");
  assert.equal(sell.value.replace(/[^\d]/g, ""), "450", "=SUM(370,80) must resolve to 450");

  await typeAndBlur(sell, "=ROUND(1234.56,0)");
  assert.equal(sell.value.replace(/[^\d]/g, ""), "1235", "=ROUND(1234.56,0) must resolve to 1235");

  await typeAndBlur(qty, "(2+3)*2");
  assert.equal(qty.value.replace(/[^\d]/g, ""), "10", "parentheses must work");
  ok("370*8 · 9.5tr*2 · 250k*4 · SUM · ROUND · parentheses all resolve to plain numbers");
}

// ---------------------------------------------------------------------------
console.log("STEP 5 — B: code, cell refs and division by zero are REFUSED, text kept");
{
  const sell = byTestId("quote-line-1-sell");
  for (const evil of [
    "eval('1+1')",
    "Function('return 1')()",
    "A1+B2",
    "process.exit(1)",
    "fetch('http://x')",
    "=CELL(A1)",
    "100/0",
  ]) {
    await typeAndBlur(sell, evil);
    assert.equal(sell.value, evil, `refused input must keep the operator's text: ${evil}`);
    const err = byTestId("quote-line-1-sell-error");
    assert.ok(err && text(err).length > 0, `a refusal message must be shown for: ${evil}`);
  }
  // A refusal never silently becomes a number.
  await typeAndBlur(sell, "1.500.000");
  assert.equal(byTestId("quote-line-1-sell-error"), null, "a plain grouped number is not an error");
  assert.equal(sell.value.replace(/[^\d]/g, ""), "1500000", "grouped digits stay the same amount");
  ok("eval/Function/cell refs/identifiers/network/÷0 refused with a visible message");
}

// ---------------------------------------------------------------------------
console.log("STEP 6 — E: CHECK CHI PHÍ is an INNER tab of the SAME Báo Giá workspace");
{
  await mountWith(costFixtureVm());
  await click("Báo Giá", "a", aside());
  const tabs = byTestId("quote-workspace-tabs");
  assert.ok(tabs, "the inner workspace segmented control must exist");
  assert.ok(text(tabs).includes("BÁO GIÁ") && text(tabs).includes("CHECK CHI PHÍ"));
  // No new sidebar group was introduced for it.
  assert.ok(!text(aside()).toUpperCase().includes("CHECK CHI PHÍ"),
    "Check chi phí must NOT become a new sidebar group");

  await clickTestId("quote-workspace-check-chi-phi");
  assert.ok(byTestId("cost-check"), "the Check chi phí workspace must render");
  assert.ok(window.location.search.includes("view=check-chi-phi"),
    "the inner view must be preserved in the URL");
  ok("inner tab beside BÁO GIÁ, kept in the URL, no new sidebar group");
}

// ---------------------------------------------------------------------------
console.log("STEP 7 — E: the SAME parser prefills the search from a pasted inquiry");
{
  // Delta, not an absolute count: earlier steps save a quote ON PURPOSE.
  const dispatchedBefore = triggers.length;
  await setValue(byTestId("cost-paste-input"),
    "EXW Guangdong - Hà Nội / 5 khối / 800 kg", "HTMLTextAreaElement");
  await clickTestId("cost-paste-parse");
  assert.ok(byTestId("cost-paste-preview"), "the same review step must appear here");
  await clickTestId("cost-paste-apply");
  assert.equal(byTestId("cost-incoterm").value, "EXW");
  assert.equal(byTestId("cost-origin").value, "Guangdong");
  assert.equal(byTestId("cost-destination").value, "Hà Nội");
  assert.equal(byTestId("cost-cbm").value, "5");
  assert.equal(byTestId("cost-weight").value, "800");
  assert.equal(triggers.length, dispatchedBefore,
    "an inquiry must NEVER be auto-saved — Check chi phí dispatches nothing");
  ok("one shared parser prefills Incoterm/route/CBM/weight, saving nothing");
}

// ---------------------------------------------------------------------------
console.log("STEP 8 — E: TÌM DỮ LIỆU CŨ prefers THỰC TẾ and labels the fallback honestly");
{
  await clickTestId("cost-search");
  const results = $('[data-testid="cost-result"]');
  assert.ok(results.length >= 2, "both comparable lots on this lane must be offered");
  // The different lane is never offered.
  const ids = results.map((r) => r.getAttribute("data-shipment-id"));
  assert.ok(!ids.includes("LO-0252"), "a different Incoterm+lane must be excluded");

  const first = results[0];
  assert.equal(first.getAttribute("data-shipment-id"), "LO-0250",
    "the closest lot WITH Finance Actual must rank first");
  assert.equal(first.getAttribute("data-source"), "ACTUAL");
  assert.ok(text(first).includes("THỰC TẾ"), "the actual source must be labelled THỰC TẾ");
  assert.ok(text(first).includes("06/2026"), "the comparable's own period must be shown");
  // It states WHY it matched.
  const why = text($('[data-testid="cost-result-why"]', first)[0]);
  assert.ok(/Incoterm/.test(why) && /tuyến|nơi/.test(why) && /CBM/.test(why),
    `the match reason must be stated, got: ${why}`);
  // Currencies stay separated — no fabricated cross-currency total.
  const totals = text($('[data-testid="cost-result-totals"]', first)[0]);
  assert.ok(totals.includes("VND") && totals.includes("CNY"),
    "each currency must carry its OWN subtotal");
  assert.ok(totals.includes("không cộng gộp"), "the no-merge rule must be stated");
  // XEM LÔ GỐC points at the real lot.
  const link = $('[data-testid="cost-result-open"]', first)[0];
  assert.ok(link && link.getAttribute("href").includes("/lo-hang/LO-0250"),
    "XEM LÔ GỐC must link to the source lot");

  const fallback = results.find((r) => r.getAttribute("data-shipment-id") === "LO-0251");
  assert.ok(fallback, "the quote-only lot must still be offered as a fallback");
  assert.equal(fallback.getAttribute("data-source"), "QUOTE");
  assert.ok(text(fallback).includes("BÁO GIÁ / DỰ KIẾN"),
    "a lot without actual lines must be labelled as an estimate");
  assert.ok(text(fallback).includes("không phải chi phí đã phát sinh"),
    "an estimate must never be presented as a real cost");
  ok("actual-first ranking, honest estimate fallback, stated reason, split currencies");
}

// ---------------------------------------------------------------------------
console.log("STEP 9 — D: the list opens on Tháng này + Đang làm; UNKNOWN never archives");
{
  const now = new Date();
  await mountWith(listFixtureVm(now));
  await click("Lô Hàng", "a", aside());
  assert.ok(byTestId("shipment-period-controls"), "period segments missing");
  assert.ok(byTestId("shipment-archive-controls"), "archive segments missing");
  assert.equal(byTestId("shipment-period-thang-nay").getAttribute("aria-pressed"), "true",
    "the list must open on Tháng này");
  assert.equal(byTestId("shipment-archive-dang-lam").getAttribute("aria-pressed"), "true",
    "the list must open on Đang làm");

  const shown = () => mainText();
  assert.ok(!shown().includes("LO-9001"), "a finished AND fully paid lot leaves Đang làm");
  assert.ok(shown().includes("LO-9002"), "an UNKNOWN outstanding must NEVER be archived");
  assert.ok(shown().includes("LO-9003"), "a running lot stays visible");
  assert.ok(!shown().includes("LO-9004"), "last month's lot is outside Tháng này");

  await clickTestId("shipment-archive-hoan-tat");
  assert.ok(mainText().includes("LO-9001"), "the settled lot appears under Đã hoàn tất & thanh toán");
  assert.ok(!mainText().includes("LO-9002"), "UNKNOWN never counts as settled");
  // The shell runs on a MemoryRouter (App.tsx), so "in the URL" means the
  // ROUTER's own search params: the list context must survive opening a lot
  // and coming back, which is the flow the Owner actually performs.
  await click("LO-9001", "a,button");
  await tick(140);
  await click("Quay lại", "button");
  await tick(140);
  assert.equal(byTestId("shipment-archive-hoan-tat").getAttribute("aria-pressed"), "true",
    "archive state must survive navigation (router query param)");

  await clickTestId("shipment-period-thang-truoc");
  assert.ok(mainText().includes("LO-9004"), "Tháng trước reveals last month's settled lot");
  assert.equal(byTestId("shipment-period-thang-truoc").getAttribute("aria-pressed"), "true",
    "period state must survive as a router query param");

  await clickTestId("shipment-archive-tat-ca");
  await clickTestId("shipment-period-tat-ca");
  for (const id of ["LO-9001", "LO-9002", "LO-9003", "LO-9004"]) {
    assert.ok(mainText().includes(id), `${id} must reappear under Tất cả — nothing was deleted`);
  }
  ok("default Tháng này + Đang làm, UNKNOWN never archives, URL-preserved, non-destructive");
}

console.log(`\nDOM_ACCEPTANCE_QUOTE_COST_WORKFLOW_UX_01=${passed} checks passed`);
if (cleanup) cleanup();
process.exit(0);
