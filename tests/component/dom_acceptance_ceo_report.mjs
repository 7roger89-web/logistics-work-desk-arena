// ============================================================================
// LOGI_CEO_REPORT_01 — DOM/navigation acceptance for /bao-cao-ceo.
//
// Runs the real production bundle in jsdom with a fixture emitted by the real
// isolated-staging view-model (scripts/gen_ceo_report_fixture.py). It proves:
//   1. the route is activated and the sidebar no longer says "Sắp có";
//   2. empty C2D/reconciliation sources stay explicitly unknown/no-data, not 0;
//   3. operations, C2C, C2D and canonical reconciliation state cards render;
//   4. money is visibly kept in its own VND/CNY block (no cross-currency sum);
//   5. incomplete-finance caveats and read-only scope stay visible;
//   6. quick navigation reaches the pre-existing receivables desk;
//   7. the primary card structure stacks responsively without desktop tables.
//
// Run: node tests/component/dom_acceptance_ceo_report.mjs
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
  readFileSync(path.join(ROOT, "tests/component/fixtures/view_model_ceo_report.json"), "utf8")
);
const EMPTY = FIX.empty;
const JOURNEY = FIX.journey;

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
  /* keep node's built-in navigator */
}
for (const key of [
  "HTMLElement", "HTMLInputElement", "HTMLTextAreaElement", "HTMLSelectElement",
  "HTMLAnchorElement", "Event", "CustomEvent", "MouseEvent", "KeyboardEvent",
  "Node", "MutationObserver", "getComputedStyle",
]) {
  globalThis[key] = window[key];
}
if (!globalThis.MessageChannel) globalThis.MessageChannel = window.MessageChannel;
window.HTMLElement.prototype.scrollIntoView = () => {};
window.URL.createObjectURL = () => "blob:mock-url";
window.URL.revokeObjectURL = () => {};

const tick = (ms = 60) => new Promise((resolve) => setTimeout(resolve, ms));
const $ = (selector, root = window.document) => [...root.querySelectorAll(selector)];
const text = (element) => (element.textContent || "").replace(/\s+/g, " ").trim();
const mainText = () => text($("main")[0] ?? window.document.body);
const bodyText = () => text(window.document.body);

function findClickable(needle, selector = "a,button", root = window.document) {
  const candidates = $(selector, root);
  return candidates.find((element) => text(element) === needle)
    || candidates.find((element) => text(element).startsWith(needle))
    || null;
}

async function click(needle, selector = "a,button", root = window.document) {
  const element = findClickable(needle, selector, root);
  assert.ok(element, `clickable "${needle}" not found`);
  element.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
  await tick();
  return element;
}

let passed = 0;
function ok(label) {
  passed += 1;
  console.log(`  ✓ ${label}`);
}

const host = window.document.createElement("div");
window.document.body.appendChild(host);
const mountRef = { current: null };
function invoke(data) {
  return mountRef.current({
    name: "logi_shell",
    data,
    parentElement: host,
    setTriggerValue: () => {},
  });
}

let cleanup = null;
async function remount(data, item = "Báo cáo CEO") {
  if (cleanup) cleanup();
  cleanup = invoke(data);
  await tick(120);
  await click(item, "a", $("aside")[0]);
}

console.log("STEP 1 — boot production bundle with no canonical C2D record");
{
  const bundle = await import(path.join(ROOT, "component/dist/logi-shell.js"));
  assert.equal(typeof bundle.default, "function");
  mountRef.current = bundle.default;
  cleanup = invoke(EMPTY);
  await tick(120);
  const rendered = bodyText();
  assert.ok(!rendered.includes("process is not defined"), "Node process leaked into browser bundle");
  assert.ok(!rendered.includes("BidiComponent Error"), "component mount failed");
  assert.ok(rendered.includes("TRƯỜNG THÀNH"), "shell did not render");
  ok("production bundle boots cleanly");
}

console.log("STEP 2 — same sidebar route, no deferred marker");
{
  const aside = $("aside")[0];
  const ceoNav = findClickable("Báo cáo CEO", "a", aside);
  assert.ok(ceoNav, "CEO sidebar item missing");
  assert.equal(ceoNav.getAttribute("href"), "/bao-cao-ceo", "CEO route changed");
  assert.ok(!text(ceoNav).includes("Sắp có"), "CEO navigation remains deferred");
  ok("sidebar activates the existing /bao-cao-ceo route");
}

console.log("STEP 3 — no canonical payable/reconciliation record is honest");
await click("Báo cáo CEO", "a", $("aside")[0]);
{
  const rendered = mainText();
  assert.ok(!rendered.includes("Sắp có — chưa triển khai"), "CEO route fell through to placeholder");
  assert.ok(rendered.includes("Báo cáo CEO"), "CEO heading missing");
  assert.ok(rendered.includes("CHỈ ĐỌC"), "read-only marker missing");
  assert.ok(rendered.includes("Chưa có bản ghi nghĩa vụ hoặc thanh toán canonical"), "payable empty state missing");
  assert.ok(rendered.includes("không phải phải trả bằng 0"), "payable empty state is not explicit enough");
  assert.ok(rendered.includes("Chưa có bản ghi đối soát canonical"), "reconciliation empty state missing");
  assert.ok(rendered.includes("không phải công nợ bằng 0"), "reconciliation empty state is not explicit enough");
  ok("no data remains no data, never an invented zero balance");
}

console.log("STEP 4 — authoritative current-position cards and currency separation");
await remount(JOURNEY);
{
  const rendered = mainText();
  assert.ok(rendered.includes("Tổng lô hàng"), "operations total card missing");
  assert.ok(rendered.includes("Lô đang chạy"), "open shipment card missing");
  assert.ok(rendered.includes("Việc ưu tiên"), "actionable task card missing");
  assert.ok(rendered.includes("Phải thu khách"), "C2C heading missing");
  assert.ok(rendered.includes("Phải trả đối tác"), "C2D heading missing");
  assert.ok(rendered.includes("Khả năng nhìn thấy tài chính"), "finance visibility caveat missing");

  const vnd = $("[data-testid='ceo-payable-VND']")[0];
  const cny = $("[data-testid='ceo-payable-CNY']")[0];
  assert.ok(vnd, "VND payable block missing");
  assert.ok(cny, "CNY payable block missing");
  assert.ok(text(vnd).includes("30.000.000 VND"), "VND outstanding amount missing/incorrect");
  assert.ok(!text(vnd).includes("CNY"), "CNY leaked into VND block");
  assert.ok(text(cny).includes("3.000 CNY"), "CNY outstanding amount missing/incorrect");
  assert.ok(!text(cny).includes("VND"), "VND leaked into CNY block");
  assert.ok(!rendered.includes("30.003.000"), "cross-currency grand total leaked into the UI");
  assert.ok(!rendered.includes("33.000.000"), "cross-currency grand total leaked into the UI");

  const receivable = $("[data-testid='ceo-receivable-VND']")[0];
  assert.ok(receivable, "C2C VND block missing");
  assert.ok(text(receivable).includes("260.588.000 VND"), "C2C amount must retain visible currency");
  ok("C2C/C2D monetary positions remain explicitly separated by currency");
}

console.log("STEP 5 — existing reconciliation state semantics are passed through");
{
  const obligations = $("[data-testid='ceo-reconciliation-obligations']")[0];
  const money = $("[data-testid='ceo-reconciliation-money']")[0];
  assert.ok(obligations, "obligation-state summary missing");
  assert.ok(money, "money-state summary missing");
  assert.ok(text(obligations).includes("Đã đối soát"), "MATCHED label missing");
  assert.ok(text(obligations).includes("Một phần"), "PARTIAL label missing");
  assert.ok(text(obligations).includes("Chưa đối soát"), "UNMATCHED label missing");
  assert.ok(text(money).includes("Đã phân bổ"), "ALLOCATED label missing");
  assert.ok(text(money).includes("Chưa phân bổ"), "UNALLOCATED label missing");
  assert.equal($("[data-testid='ceo-reconciliation'] button").length, 0, "CEO reconciliation adds a write action");
  assert.ok(!mainText().includes("EBITDA"), "unsupported KPI leaked into CEO view");
  assert.ok(!mainText().includes("Tăng trưởng"), "unsupported growth KPI leaked into CEO view");
  ok("only canonical allocation-state counts render; no write/KPI surface added");
}

console.log("STEP 6 — quick navigation reaches an existing desk");
{
  const quick = $("[data-testid='ceo-quick-navigation']")[0];
  const receivableLink = findClickable("Mở phải thu khách", "a", quick);
  assert.ok(receivableLink, "receivables quick link missing");
  assert.equal(receivableLink.getAttribute("href"), "/tai-chinh/thu-tien", "quick link target changed");
  await click("Mở phải thu khách", "a", quick);
  assert.ok(mainText().includes("Thu tiền khách · Phải thu"), "quick navigation did not reach C2C desk");
  ok("quick navigation opens the pre-existing receivables desk");
}

console.log("STEP 7 — mobile-first structural contract");
await remount(JOURNEY);
{
  const moneyGrids = [
    $("[data-testid='ceo-receivable-currency-grid']")[0],
    $("[data-testid='ceo-payable-currency-grid']")[0],
  ];
  for (const grid of moneyGrids) {
    assert.ok(grid, "currency grid missing");
    assert.ok(grid.className.includes("grid"), "currency cards are not a responsive grid");
    assert.ok(grid.className.includes("sm:grid-cols-2"), "currency cards do not stack on narrow viewports");
    assert.ok(!grid.className.includes("overflow-x-auto"), "primary currency metrics require horizontal scroll");
  }
  assert.equal($("[data-testid='ceo-header'] table").length, 0, "CEO header uses desktop table markup");
  for (const link of $("[data-testid='ceo-quick-links'] a")) {
    assert.ok(link.className.includes("min-h-[52px]"), "quick link misses mobile touch target");
  }
  assert.ok(text($("[data-testid='ceo-payable-CNY']")[0]).includes("3.000 CNY"), "currency is not paired with mobile amount");
  ok("cards stack, currencies stay paired with amounts, and quick links are touch-sized");
}

if (cleanup) cleanup();
console.log(`CEO REPORT DOM ACCEPTANCE PASS — ${passed} checks`);
