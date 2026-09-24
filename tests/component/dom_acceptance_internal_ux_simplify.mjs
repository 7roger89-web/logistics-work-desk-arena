// ============================================================================
// LOGI_INTERNAL_UX_SIMPLIFY_01 — DOM acceptance for Issue #88 (real bundle).
//
//   1. Simplified nav: "Việc Cần Xử Lý" / "Theo Dõi Vận Chuyển" /
//      "Thỏa thuận mua bán" are absent from the desktop sidebar AND the mobile
//      drawer; "Báo Giá" is the visible quote label; surviving entries stay.
//   2. Customer runtime search: the input is present and enabled; toneless
//      typing ("An Phat") filters by name, code and MST; the literal string
//      "undefined" never matches a partial record; ?q= deep-links from the
//      desktop AND mobile global search land filtered.
//   3. Quote desk: "Báo Giá" title; create-quote uses the searchable
//      SearchPicker (finds by toneless name / id / MST, binds the exact
//      customerId); each service line has an optional Ghi chú input whose
//      text travels in the quote_create payload; edit keeps the customer
//      read-only and re-opens the persisted note.
//   4. Dead-route audit: no visible link anywhere routes to a removed module.
//   5. Translation donor parity: "Dịch Thuật" header, donor-shape sample
//      pills, 15-item donor-shape glossary; real-provider states untouched.
//
// Run: node tests/component/dom_acceptance_internal_ux_simplify.mjs
// ============================================================================

import { readFileSync } from "node:fs";
import assert from "node:assert/strict";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const require = createRequire(path.join(ROOT, "component/package.json"));
const { JSDOM } = require("jsdom");
const VM = JSON.parse(
  readFileSync(path.join(ROOT, "tests/component/fixtures/view_model_phase_b.json"), "utf8")
);
// The translation slice rides along so /dich-thuat renders its real state.
const TR = JSON.parse(
  readFileSync(path.join(ROOT, "tests/component/fixtures/view_model_translation.json"), "utf8")
);
if (TR.translation) VM.translation = TR.translation;
// phase_b quote rows are a bare legacy shape; the CURRENT full projection
// comes from the contract_workflow fixture (same splice as navigation_context).
const CW = JSON.parse(
  readFileSync(path.join(ROOT, "tests/component/fixtures/view_model_contract_workflow.json"), "utf8")
);
if (Array.isArray(CW.success?.quotes) && CW.success.quotes.length > 0) {
  VM.quotes = CW.success.quotes;
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
} catch {
  /* keep node navigator */
}
for (const k of [
  "HTMLElement", "HTMLInputElement", "HTMLTextAreaElement", "HTMLSelectElement",
  "HTMLAnchorElement", "Event", "CustomEvent", "MouseEvent", "KeyboardEvent",
  "Node", "MutationObserver", "getComputedStyle", "TextEncoder",
]) {
  globalThis[k] = window[k];
}
if (!globalThis.MessageChannel) globalThis.MessageChannel = window.MessageChannel;
window.HTMLElement.prototype.scrollIntoView = () => {};
window.URL.createObjectURL = () => "blob:mock-url";
window.URL.revokeObjectURL = () => {};

const tick = (ms = 80) => new Promise((r) => setTimeout(r, ms));
const $ = (sel, root = window.document) => [...root.querySelectorAll(sel)];
const text = (el) => (el.textContent || "").replace(/\s+/g, " ").trim();
const mainText = () => text($("main")[0] ?? window.document.body);
const bodyText = () => text(window.document.body);
const aside = () => $("aside")[0];

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
async function clickSelector(sel, root = window.document, index = 0) {
  const el = $(sel, root)[index];
  assert.ok(el, `selector "${sel}[${index}]" not found`);
  el.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
  await tick();
  return el;
}
async function typeInput(input, value) {
  const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
  setter.call(input, value);
  input.dispatchEvent(new window.Event("input", { bubbles: true }));
  await tick(120);
}

let passed = 0;
function ok(name) {
  passed += 1;
  console.log(`  ✓ ${name}`);
}

const host = window.document.createElement("div");
window.document.body.appendChild(host);
const triggers = [];
const mod = await import(path.join(ROOT, "component/dist/logi-shell.js"));
assert.equal(typeof mod.default, "function");
let cleanup = mod.default({
  name: "logi_shell",
  data: VM,
  parentElement: host,
  setTriggerValue: (event, value) => triggers.push({ event, value }),
});
await tick(150);

const REMOVED_SLUGS = ["viec-can-xu-ly", "theo-doi", "thoa-thuan-ban-giao"];
function deadLinks(root = window.document) {
  return REMOVED_SLUGS.flatMap((slug) =>
    $(`a[href*="${slug}"]`, root).map((a) => a.getAttribute("href"))
  );
}
const customerCountLine = () =>
  $("p", $("main")[0]).map(text).find((t) => t.startsWith("Tìm thấy")) ?? "(no count line)";

// ---------------------------------------------------------------------------
console.log("STEP 1 — simplified nav (sidebar + drawer) + Báo Giá label");
{
  const at = text(aside());
  for (const gone of ["Việc Cần Xử Lý", "Theo Dõi Vận Chuyển", "Thỏa thuận mua bán", "Kinh doanh · Báo giá"]) {
    assert.ok(!at.includes(gone), `sidebar still shows "${gone}"`);
  }
  for (const kept of ["Lô Hàng", "Tạo Lô Mới", "Khách Hàng", "Đại Lý Trường Thành", "Báo Giá", "Hợp đồng"]) {
    assert.ok(at.includes(kept), `sidebar lost "${kept}"`);
  }
  assert.equal(deadLinks(aside()).length, 0, "sidebar links to a removed desk");
  await clickSelector('button[aria-label="Mở menu"]');
  const drawer = $("div.anim-slide-up").filter((el) => text(el).includes("Menu điều hành"))[0]
    ?? $(".fixed.inset-0.z-50")[0];
  assert.ok(drawer, "mobile drawer missing");
  const dt = text(drawer);
  for (const gone of ["Việc Cần Xử Lý", "Theo Dõi Vận Chuyển", "Thỏa thuận mua bán"]) {
    assert.ok(!dt.includes(gone), `drawer still shows "${gone}"`);
  }
  assert.ok(dt.includes("Báo Giá"), "drawer lost Báo Giá");
  assert.equal(deadLinks(drawer).length, 0, "drawer links to a removed desk");
  await click("Lô Hàng", "a", drawer);
  ok("sidebar + drawer drop the 3 desks, keep Báo Giá + survivors");
}

// ---------------------------------------------------------------------------
console.log("STEP 2 — customer runtime search (toneless, code, MST, no-undefined)");
{
  await click("Khách Hàng", "a", aside());
  const main = $("main")[0];
  const search = $("input", main).find((i) => (i.placeholder || "").includes("Nhập mã"));
  assert.ok(search, "customer search input missing");
  assert.equal(search.disabled, false, "customer search input disabled");
  assert.ok(customerCountLine().includes("Tìm thấy 5 khách hàng"), `unexpected baseline: ${customerCountLine()}`);
  await typeInput(search, "An Phat"); // toneless typing must still match
  assert.ok(customerCountLine().startsWith("Tìm thấy 1 khách hàng"), `toneless name failed: ${customerCountLine()}`);
  assert.equal($("tbody tr", main).length, 1, "visible list did not filter to 1 row");
  await typeInput(search, "CUST-DUCLONG");
  assert.ok(customerCountLine().startsWith("Tìm thấy 1 khách hàng"), `code search failed: ${customerCountLine()}`);
  await typeInput(search, "0103456789");
  assert.ok(customerCountLine().startsWith("Tìm thấy 1 khách hàng"), `MST search failed: ${customerCountLine()}`);
  await typeInput(search, "undefined");
  assert.ok(customerCountLine().startsWith("Tìm thấy 0 khách hàng"), `undefined-guard failed: ${customerCountLine()}`);
  await typeInput(search, "");
  assert.ok(customerCountLine().includes("Tìm thấy 5 khách hàng"), "clear did not restore the list");
  ok("visible input; name/code/MST filter; toneless typing works; no undefined pollution");
}

// ---------------------------------------------------------------------------
console.log("STEP 3 — ?q= deep-links (desktop + mobile global search)");
{
  // Desktop header search.
  const headerInput = $("header input")[0];
  assert.ok(headerInput, "desktop global search missing");
  headerInput.dispatchEvent(new window.FocusEvent("focusin", { bubbles: true }));
  await typeInput(headerInput, "Hồng Hà");
  const hit = $("header button").find(
    (b) => text(b).includes("Hồng Hà") && text(b).includes("Khách hàng")
  );
  assert.ok(hit, "desktop global search shows no customer hit");
  hit.dispatchEvent(new window.MouseEvent("click", { bubbles: true }));
  await tick(150);
  const landed = $("input", $("main")[0]).find((i) => (i.placeholder || "").includes("Nhập mã"));
  assert.ok(landed && landed.value.includes("Hồng Hà"), "desktop deep-link did not land filtered");
  assert.ok(customerCountLine().startsWith("Tìm thấy 1 khách hàng"), `desktop deep-link count: ${customerCountLine()}`);
  await typeInput(landed, "");
  // Mobile search panel.
  await clickSelector('button[aria-label="Tìm kiếm"]');
  const mobileInput = $("header input").find((i) => (i.placeholder || "").includes("Tìm mã lô · khách"));
  assert.ok(mobileInput, "mobile search input missing");
  await typeInput(mobileInput, "Hồng Hà");
  const mobileHit = $("header button").find(
    (b) => text(b).includes("Hồng Hà") && text(b).includes("Khách hàng")
  );
  assert.ok(mobileHit, "mobile global search shows no customer hit");
  mobileHit.dispatchEvent(new window.MouseEvent("click", { bubbles: true }));
  await tick(150);
  const landedMobile = $("input", $("main")[0]).find((i) => (i.placeholder || "").includes("Nhập mã"));
  assert.ok(landedMobile && landedMobile.value.includes("Hồng Hà"), "mobile deep-link did not land filtered");
  assert.ok(customerCountLine().startsWith("Tìm thấy 1 khách hàng"), `mobile deep-link count: ${customerCountLine()}`);
  await typeInput(landedMobile, "");
  ok("desktop + mobile global search land on /khach-hang?q=… filtered");
}

// ---------------------------------------------------------------------------
console.log("STEP 4 — quote desk: Báo Giá title + searchable customer picker");
{
  await click("Báo Giá", "a", aside());
  assert.ok(mainText().includes("Báo Giá"), "quote page title missing");
  assert.ok(!mainText().includes("Kinh doanh · Báo giá"), "old quote title lingers");
  await click("Tạo báo giá", "button");
  const picker = $('[data-testid="quote-customer-picker"]')[0];
  assert.ok(picker, "create-quote customer SearchPicker missing");
  assert.equal($("select", picker).length, 0, "native select still used for the customer");
  await clickSelector('[data-testid="quote-customer-picker-toggle"]');
  const search = $('[data-testid="quote-customer-picker-search"]')[0];
  assert.ok(search, "picker search input missing");
  await typeInput(search, "an phat"); // toneless
  const option = $('[data-testid="quote-customer-picker-option-CUST-ANPHAT"]')[0];
  assert.ok(option, "picker did not find CUST-ANPHAT by toneless name");
  option.dispatchEvent(new window.MouseEvent("click", { bubbles: true }));
  await tick();
  assert.equal(
    $('[data-testid="quote-customer-picker"]')[0].getAttribute("data-selected"),
    "CUST-ANPHAT",
    "picker did not bind the exact customerId"
  );
  // MST search path.
  await clickSelector('[data-testid="quote-customer-picker-toggle"]');
  await typeInput($('[data-testid="quote-customer-picker-search"]')[0], "0312987654");
  assert.ok(
    $('[data-testid="quote-customer-picker-option-CUST-DUCLONG"]')[0],
    "picker did not find CUST-DUCLONG by MST"
  );
  await clickSelector('[data-testid="quote-customer-picker-toggle"]'); // close
  ok("searchable picker finds by toneless name + MST and binds the exact id");
}

// ---------------------------------------------------------------------------
console.log("STEP 5 — quote line Ghi chú travels in the payload; edit read-only customer");
{
  // LOGI_QUOTE_LINE_NOTE_CLARITY_01 — the per-line note is now labelled
  // "Ghi chú dòng này" (its wrapping <label> supplies the accessible name) and
  // is hooked by a stable test id; the assertion itself is unchanged.
  const noteInput = $('[data-testid="quote-line-1-note"]')[0];
  assert.ok(noteInput, "service-line Ghi chú input missing");
  await typeInput(noteInput, "giá đã gồm bốc xếp tại kho");
  // Minimal valid line so the payload is accepted shape-wise downstream.
  const serviceInput = $('[data-testid="quote-line-1-service"]')[0];
  assert.ok(serviceInput, "service-name input missing");
  await typeInput(serviceInput, "Cước xe");
  // LOGI_QUOTE_COST_WORKFLOW_UX_01_REPAIR_01 — UNKNOWN != ZERO: a line whose
  // Giá vốn / Giá bán / Thuế was never stated is now REFUSED at Save instead of
  // being persisted as a silent canonical 0. This step is about the per-line
  // NOTE, so the numbers are stated explicitly (0 is a legitimate answer).
  for (const [testId, value] of [
    ["quote-line-1-cost", "0"], ["quote-line-1-sell", "1000"], ["quote-line-1-tax", "0"],
  ]) {
    const field = $(`[data-testid="${testId}"]`)[0];
    assert.ok(field, `${testId} missing`);
    await typeInput(field, value);
  }
  const before = triggers.length;
  await click("💾 TẠO BÁO GIÁ", "button");
  const ev = triggers.slice(before).find((t) => t.event === "quote_create");
  assert.ok(ev, "quote_create trigger not emitted");
  assert.equal(ev.value.payload.customerId, "CUST-ANPHAT", "payload lost the picked customerId");
  assert.equal(
    ev.value.payload.serviceLines[0].note,
    "giá đã gồm bốc xếp tại kho",
    "payload lost the service-line note"
  );
  ok("quote_create carries {customerId, serviceLines[0].note}");
}

// ---------------------------------------------------------------------------
console.log("STEP 6 — edit re-opens the persisted note; customer read-only");
{
  // Fresh readback: the persisted note comes back through the projection.
  const vm2 = JSON.parse(JSON.stringify(VM));
  vm2.quotes = [
    {
      id: "Q-TEST-1", quoteNo: "QT-TEST-1", customerId: "CUST-ANPHAT",
      customer: "An Phát JSC", salesOwner: "Minh Tú", status: "DRAFT",
      statusLabel: "Nháp", origin: "Bằng Tường", destination: "KCN Quế Võ",
      route: "Hữu Nghị", incoterm: "DAP", transportMode: "Road",
      goodsDescription: "Linh kiện", expectedDeliveryDate: "2026-09-20",
      currency: "VND", total: 1000, sellingPriceTotalVnd: 1000,
      fxRatesToVnd: {}, fxNeededFor: [],
      serviceLines: [
        {
          code: "DV-VC-TQ", serviceName: "Cước xe", unit: "Lần", qty: 1,
          currency: "VND", costUnit: 900, sellUnit: 1000, taxPct: 0,
          note: "ghi chú đã lưu",
        },
      ],
      assumptions: [], statusHistory: [], version: 1, shipmentId: "",
      allowedTransitions: ["READY_FOR_REVIEW"],
    },
  ];
  cleanup();
  await tick(60);
  cleanup = mod.default({
    name: "logi_shell",
    data: vm2,
    parentElement: host,
    setTriggerValue: (event, value) => triggers.push({ event, value }),
  });
  await tick(150);
  await click("Báo Giá", "a", aside());
  await click("Sửa", "button");
  assert.equal($('[data-testid="quote-customer-picker"]').length, 0, "edit must not offer a customer picker");
  const roCustomer = $('input[aria-label="Khách hàng của báo giá (không đổi khi sửa)"]')[0];
  assert.ok(roCustomer && roCustomer.disabled, "edit customer is not read-only");
  assert.ok(roCustomer.value.includes("CUST-ANPHAT"), `read-only customer wrong: ${roCustomer.value}`);
  const noteBack = $('[data-testid="quote-line-1-note"]')[0];
  assert.ok(noteBack, "edit lost the Ghi chú input");
  assert.equal(noteBack.value, "ghi chú đã lưu", "edit did not re-open the persisted note");
  await click("Hủy", "button");
  ok("edit re-opens the persisted note; customer stays read-only");
}

// ---------------------------------------------------------------------------
console.log("STEP 7 — dead-route audit across the surviving surfaces");
{
  for (const [label] of [
    ["Tổng Quan Công Việc"], ["Lô Hàng"], ["Khách Hàng"], ["Báo Giá"],
    ["Hợp đồng"], ["Dịch thuật"],
  ]) {
    await click(label, "a", aside());
    const dead = deadLinks();
    assert.equal(dead.length, 0, `${label}: links to removed desks: ${dead.join(", ")}`);
  }
  ok("zero visible links to removed modules on 6 surviving surfaces");
}

// ---------------------------------------------------------------------------
console.log("STEP 8 — translation donor parity (structure; provider untouched)");
{
  await click("Dịch thuật", "a", aside());
  const h1 = $("h1", $("main")[0])[0];
  assert.ok(h1 && text(h1) === "Dịch Thuật", "donor-case page header missing");
  const chips = $("button[data-testid='quick-chip']");
  assert.ok(chips.length > 0, "sample chips missing");
  for (const chip of chips) {
    assert.ok(chip.className.includes("rounded-full"), "chip is not the donor pill shape");
  }
  const grid = $("div[data-testid='glossary']")[0];
  assert.ok(grid && grid.className.includes("grid-cols-2"), "glossary is not the donor 2-col grid");
  assert.ok(grid.className.includes("sm:grid-cols-3"), "glossary must widen to 3 columns on sm+");
  const items = $("[data-testid='glossary-item']");
  assert.equal(items.length, 15, `glossary must be the donor 15, got ${items.length}`);
  for (const item of items) {
    assert.ok(item.className.includes("rounded-lg"), "glossary card is not the donor compact shape");
  }
  assert.ok(mainText().includes("Từ điển nghiệp vụ nhanh"), "glossary header missing");
  assert.ok(mainText().includes("DỊCH NGAY"), "DỊCH NGAY action missing");
  const action = findClickable("DỊCH NGAY", "button");
  assert.ok(action && action.className.includes("w-full"), "DỊCH NGAY must stay full width");
  // No fake-engine wording may ever appear on this page.
  assert.ok(!mainText().includes("mô phỏng"), "simulated-translation wording leaked");
  ok("donor header + pills + 15-row glossary; no simulated wording");
}

console.log(`\nPASS — ${passed} checks`);
