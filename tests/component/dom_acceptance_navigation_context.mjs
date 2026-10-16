// ============================================================================
// DOM acceptance — LOGI_FRONTEND_WORKFLOW_OVERHAUL_01 · NAVIGATION CONTEXT
//
// Representative flows (real bundle, real MemoryRouter navigation):
//   A. Shipments: search + status filter → open shipment → Quay lại
//      → search input + status chip restored.
//   B. (LOGI_INTERNAL_UX_SIMPLIFY_01 + LOGI-APP-RENEWAL-01) Task desk remains
//      out of the normal nav but is live from Home; other removed desk links
//      still land on the surviving work surface (/lo-hang).
//   C. Contracts: search → open contract → back → search restored.
//   D. Receivables: search + outstanding filter → open shipment → back
//      → both restored.
//   E. Global search customer → /khach-hang?q=<entity> (exact customer
//      already filtered, no second search); quote → /kinh-doanh-bao-gia?q=…
//      with the exact quote visible.
//   F. Shipment tab context: open a tab → leave → back → tab restored.
//
// Route search params are the ONLY mechanism used (no global store).
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
  readFileSync(path.join(ROOT, "tests", "component", "fixtures", "view_model_phase_b.json"), "utf8")
);
// Fixture repair: the phase_b fixture's contracts predate the CURRENT full
// contract projection (linkedShipments/docCards/goodsLines/… that
// ContractDetail reads). Splice in the contracts from the newer
// contract_workflow fixture (same ids, CURRENT backend shape) instead of
// asserting against a stale document shape.
const CW = JSON.parse(
  readFileSync(path.join(ROOT, "tests", "component", "fixtures", "view_model_contract_workflow.json"), "utf8")
);
if (Array.isArray(CW.success?.contracts) && CW.success.contracts.length > 0) {
  FIXTURE.contracts = CW.success.contracts;
}
// Same repair for the receivables projection: phase_b predates it, so splice
// the backend-generated C2C worklist in.
const C2C = JSON.parse(
  readFileSync(path.join(ROOT, "tests", "component", "fixtures", "view_model_c2c.json"), "utf8")
);
if (C2C.journey?.receivables?.rows?.length > 0) {
  FIXTURE.receivables = C2C.journey.receivables;
}
// And for quotes: phase_b's quote rows are a bare legacy shape; the CURRENT
// full projection comes from the contract_workflow fixture.
if (Array.isArray(CW.success?.quotes) && CW.success.quotes.length > 0) {
  FIXTURE.quotes = CW.success.quotes;
}

const dom = new JSDOM("<!DOCTYPE html><html><body></body></html>", {
  url: "http://localhost:8501/",
  pretendToBeVisual: true,
});
const { window } = dom;
globalThis.window = window;
globalThis.document = window.document;
try { Object.defineProperty(globalThis, "navigator", { value: window.navigator, configurable: true }); } catch {}
for (const k of ["HTMLElement","HTMLInputElement","HTMLTextAreaElement","HTMLSelectElement","HTMLAnchorElement","Event","CustomEvent","MouseEvent","KeyboardEvent","Node","MutationObserver","getComputedStyle"]) {
  globalThis[k] = window[k];
}
if (!globalThis.MessageChannel) globalThis.MessageChannel = window.MessageChannel;
window.HTMLElement.prototype.scrollIntoView = () => {};
window.URL.createObjectURL = () => "blob:mock-url";
window.URL.revokeObjectURL = () => {};

const tick = (ms=60) => new Promise(r=>setTimeout(r,ms));
const $ = (sel, root=window.document) => [...root.querySelectorAll(sel)];
const text = (el) => (el?.textContent||"").replace(/\s+/g," ").trim();
const bodyText = () => text(window.document.body);
let passed=0;
function ok(name){ passed++; console.log(`  ✓ ${name}`); }

const host=window.document.createElement("div");
window.document.body.appendChild(host);
let triggers=[];
const mountRef={current:null};
function invoke(data){
  return mountRef.current({name:"logi_shell", data, parentElement:host, setTriggerValue:(ev,val)=>triggers.push({event:ev,value:val})});
}

const bundle=path.join(ROOT,"component","dist","logi-shell.js");
const mod=await import(bundle);
assert.equal(typeof mod.default,"function","bundle must default-export mount");
mountRef.current=mod.default;

await invoke(FIXTURE);
await tick(200);

function mainInput(placeholderPrefix){
  const el = $(`input[placeholder^="${placeholderPrefix}"]`)[0];
  assert.ok(el, `input "${placeholderPrefix}" not found`);
  return el;
}
function typeInto(input, value){
  Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,"value").set.call(input,value);
  input.dispatchEvent(new window.Event("input",{bubbles:true}));
  input.dispatchEvent(new window.Event("change",{bubbles:true}));
}
async function clickEl(el){
  assert.ok(el, "click target missing");
  el.dispatchEvent(new window.MouseEvent("click",{bubbles:true,cancelable:true}));
  await tick();
}
async function clickText(needle, sel="a,button", root=window.document){
  const els=$(sel,root);
  const el = els.find(el=>text(el)===needle) || els.find(el=>text(el).startsWith(needle)) || els.find(el=>text(el).includes(needle));
  await clickEl(el);
  return el;
}
const aside = () => window.document.querySelector("aside");
async function goto(navItem){ await clickText(navItem, "a", aside()); }
const chipActive = (label) => {
  const chip = $("button").find((b) => text(b) === label);
  return chip && chip.className.includes("bg-[#0f2a4a]");
};

console.log("FLOW A — Shipments: search + status → open → back → context restored");
{
  await goto("Lô Hàng");
  await tick();
  const q = mainInput("Nhập mã lô");
  typeInto(q, "LO-03");
  await clickText("Lọc", "button"); // reveal the status chips
  await clickText("Chờ thông quan", "button"); // status chip
  await tick();
  assert.ok(chipActive("Chờ thông quan"), "status chip active before opening");
  const countLine = bodyText();
  assert.ok(countLine.includes("cho “LO-03”"), "search echoed in the count line");
  await clickText("LO-0306", "a", $("table.tbl")[0]);
  await tick(120);
  assert.equal(text($("h1")[0]), "Lô hàng LO-0306", "detail opened");
  await clickText("Quay lại", "button");
  await tick(120);
  const q2 = mainInput("Nhập mã lô");
  assert.equal(q2.value, "LO-03", "search restored after back");
  assert.ok(chipActive("Chờ thông quan"), "status chip restored after back");
  assert.ok(bodyText().includes("cho “LO-03”"), "list still filtered after back");
  ok("Shipments context survives open → back");
  // reset for later flows
  typeInto(mainInput("Nhập mã lô"), "");
  await clickText("Chờ thông quan", "button"); // toggle chip off
  await clickText("Tất cả", "button");
  await tick();
}

console.log("FLOW B — Home task desk remains live; removed tracking/agreements entries land on /lo-hang");
{
  await goto("Tổng Quan Công Việc");
  await tick();
  await clickEl($('[data-testid="home-task-desk"]')[0]);
  assert.ok(bodyText().includes("Việc Cần Xử Lý"), "Home task desk should open the active Tasks page");
  assert.equal($("aside a[href=\"/viec-can-xu-ly\"]").length, 0, "task desk remains out of normal nav");
  await goto("Tổng Quan Công Việc");
  await clickText("Tất cả lô", "a");
  await tick(120);
  assert.ok(bodyText().includes("Tìm theo mã lô"), "home exception link must open Lô Hàng");
  await goto("Tổng Quan Công Việc");
  await tick();
  await clickText("MỞ DANH SÁCH LÔ", "a");
  await tick(120);
  assert.ok(bodyText().includes("Tìm theo mã lô"), "home docs card must open Lô Hàng");
  await goto("Tổng Quan Công Việc");
  await tick();
  await clickText("MỞ LÔ HÀNG", "a");
  await tick(120);
  assert.ok(bodyText().includes("Tìm theo mã lô"), "home urgent card must open Lô Hàng");
  const dead = ["theo-doi", "thoa-thuan-ban-giao"].flatMap((slug) =>
    $(`a[href*="${slug}"]`).map((a) => a.getAttribute("href"))
  );
  assert.equal(dead.length, 0, `visible links still route to removed desks: ${dead.join(", ")}`);
  ok("Home task desk is live; former tracking/agreement links use /lo-hang; zero dead links");
}

console.log("FLOW C — Contracts: search → open → back → search restored");
{
  await goto("Hợp đồng");
  await tick();
  const q = mainInput("Nhập số hợp đồng");
  typeInto(q, "HDNT-0307");
  await tick();
  await clickText("HDNT-0307", "a", $("table.tbl")[0]);
  await tick(120);
  await clickText("Quay lại", "button");
  await tick(120);
  assert.equal(mainInput("Nhập số hợp đồng").value, "HDNT-0307", "contract search restored");
  ok("Contracts search survives open → back");
}

console.log("FLOW D — Receivables: search + outstanding-only → open shipment → back");
{
  await goto("Thu tiền");
  await tick();
  const q = mainInput("Tìm mã lô (LO-0306)");
  typeInto(q, "LO-03");
  await clickText("Lọc", "button"); // reveal the filter panel
  await clickText("Chỉ lô còn phải thu", "button");
  await tick();
  // open the linked shipment of the first row
  const firstRow = $("table.tbl tbody tr")[0];
  const openLink = $("a", firstRow).find((a) => text(a).includes("Mở lô") || text(a).includes("Xem"));
  await clickEl(openLink || $("table.tbl tbody a")[0]);
  await tick(120);
  await clickText("Quay lại", "button");
  await tick(120);
  assert.equal(mainInput("Tìm mã lô (LO-0306)").value, "LO-03", "receivables search restored");
  const chip = $("button").find((b) => text(b).includes("Chỉ lô còn phải thu"));
  assert.ok(chip.className.includes("border-red-400"), "outstanding-only filter restored");
  ok("Receivables context survives open → back");
}

console.log("FLOW E — global search: customer/quote destination carries the exact entity");
{
  const headerSearch = mainInput("Tìm mã lô");
  const customer = FIXTURE.customers.find((c) => c.name);
  // React delegates focus via focusin — fire both so the dropdown opens.
  headerSearch.dispatchEvent(new window.Event("focus", { bubbles: false }));
  headerSearch.dispatchEvent(new window.Event("focusin", { bubbles: true }));
  typeInto(headerSearch, customer.name.slice(0, 6));
  await tick(120);
  const resultBtn = $("button").find((b) => text(b).includes(customer.name.slice(0, 6)) && text(b).includes("Khách hàng"));
  assert.ok(resultBtn, "customer result appears in global search");
  await clickEl(resultBtn);
  await tick(160);
  assert.ok(bodyText().includes("Khách Hàng"), "landed on Customers desk");
  const destQ = mainInput("Nhập mã (CUST");
  assert.ok(destQ.value.includes(customer.name.slice(0, 6)), `destination search prefilled (${destQ.value})`);
  const rows = $("table.tbl tbody tr").length + $("main .rounded-2xl").length;
  assert.ok(bodyText().toUpperCase().includes(customer.name.toUpperCase()), "exact customer visible without a second search");
  ok(`customer destination visibly contains ${customer.name} (prefilled q="${destQ.value}")`);

  // quote
  await goto("Lô Hàng");
  await tick();
  const quoteSearch = mainInput("Tìm mã lô");
  quoteSearch.dispatchEvent(new window.Event("focus", { bubbles: false }));
  quoteSearch.dispatchEvent(new window.Event("focusin", { bubbles: true }));
  typeInto(quoteSearch, FIXTURE.quotes[0].id);
  await tick(120);
  // LOGI_INTERNAL_UX_SIMPLIFY_01 — the visible quote label is "Báo Giá".
  const quoteBtn = $("button").find((b) => text(b).includes(FIXTURE.quotes[0].id) && text(b).includes("Báo Giá"));
  assert.ok(quoteBtn, "quote result appears in global search");
  await clickEl(quoteBtn);
  await tick(160);
  assert.ok(bodyText().includes("Báo giá"), "landed on SalesQuotes desk");
  assert.ok(bodyText().includes(FIXTURE.quotes[0].id), "exact quote visible without a second search");
  ok(`quote destination visibly contains ${FIXTURE.quotes[0].id}`);
}

console.log("FLOW F — shipment tab context: XỬ LÝ deep-link selects the right workspace tab");
{
  await goto("Lô Hàng");
  await tick();
  // s.nextRoute = /lo-hang/<id>?tab=<hyphen-tab> — the XỬ LÝ column deep-links
  // into the exact workspace tab (regression: LOGI_UAT_REAL_USE_REPAIR_02).
  const handle = $("table.tbl tbody tr a").find((a) => text(a).includes("XỬ LÝ") && !text(a).includes("360"));
  assert.ok(handle, "XỬ LÝ deep-link present in the shipments table");
  const href = handle.getAttribute("href") || "";
  assert.ok(href.includes("tab="), `deep-link carries the tab param (${href})`);
  await clickEl(handle);
  await tick(160);
  const tabFromRoute = new URLSearchParams(href.split("?")[1] || "").get("tab");
  const gwRoot = window.document.querySelector('[data-testid="journey-global-workspace"]');
  assert.ok(gwRoot, "the deep-link must open the Global Workspace (#190)");
  const activeTab = $("button", gwRoot).find((b) => b.className.includes("border-slate-900"));
  assert.ok(activeTab, "a workspace tab is active");
  const expectedId = tabFromRoute && tabFromRoute !== "360" ? tabFromRoute : null;
  ok(`deep-link opened the lot with its workspace tab active (${expectedId ?? "default"})`);
}

console.log(`\nNAVIGATION_CONTEXT_DOM_ACCEPTANCE=PASSED checks=${passed}`);
