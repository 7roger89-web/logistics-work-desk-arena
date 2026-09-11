// ============================================================================
// LOGI_TARIFF_LOOKUP_01 — DOM/navigation acceptance for /tra-cuu-thue.
//
// Runs the REAL production bundle (component/dist/logi-shell.js) in jsdom
// with a REAL-backend fixture (scripts/gen_tariff_fixture.py — isolated
// mongomock staging + the canonical reader over a governed-schema reference
// DB) and verifies:
//   1. boot (no process/BidiComponent failure)
//   2. sidebar "Tra cứu thuế / HS" carries NO "Sắp có" marker anymore
//   3. the route opens the REAL workspace: heading, source status banner,
//      provenance honesty banner, and the reader's last result
//   4. search interaction emits the bounded READ-ONLY "tariff_lookup"
//      trigger with the typed query (transport contract)
//   5. fresh-readback re-invocation renders the new result (UNKNOWN cells
//      render as "—", never 0)
//   6. no-match state is honest ("Không tìm thấy kết quả")
//   7. mobile drawer routes to the same real workspace; results are
//      duplicated as mobile cards (no horizontal-scroll table dependency)
//
// Run: node tests/component/dom_acceptance_tariff.mjs
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
  readFileSync(path.join(ROOT, "tests/component/fixtures/view_model_tariff.json"), "utf8")
);

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
  return els.find((el) => text(el) === needle) || els.find((el) => text(el).startsWith(needle)) || null;
}

async function click(needle, sel = "a,button", root = window.document) {
  const el = findClickable(needle, sel, root);
  assert.ok(el, `clickable "${needle}" not found`);
  el.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
  await tick();
  return el;
}

async function clickSelector(sel, root = window.document) {
  const el = $(sel, root)[0];
  assert.ok(el, `selector "${sel}" not found`);
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

const host = window.document.createElement("div");
window.document.body.appendChild(host);
const triggers = [];
const mountRef = { current: null };
function invoke(data) {
  return mountRef.current({
    name: "logi_shell",
    data,
    parentElement: host,
    setTriggerValue: (event, value) => triggers.push({ event, value }),
  });
}

/** Simulate leaving the page and coming back: React remounts with a fresh
 *  local state (route resets to "/") while Python re-delivers the last
 *  authoritative read. Returns a navigate-back callback. */
let lastInvokeCleanup = null;
async function remount(data) {
  if (lastInvokeCleanup) lastInvokeCleanup();
  const cleanup = invoke(data);
  lastInvokeCleanup = cleanup;
  await tick(120);
  const aside = $("aside")[0];
  await click("Tra cứu thuế / HS", "a", aside);
}
const bundlePath = path.join(ROOT, "component/dist/logi-shell.js");

// ---------------------------------------------------------------------------
console.log("STEP 1 — boot production bundle");
{
  const mod = await import(bundlePath);
  assert.equal(typeof mod.default, "function");
  mountRef.current = mod.default;
  lastInvokeCleanup = invoke(VM);
  await tick(120);
  const t = bodyText();
  assert.ok(!t.includes("process is not defined"), "process is not defined leaked");
  assert.ok(!t.includes("BidiComponent Error"), "BidiComponent Error rendered");
  assert.ok(t.includes("TRƯỜNG THÀNH"), "app did not render");
  ok("boot clean, shell rendered");
}

// ---------------------------------------------------------------------------
console.log("STEP 2 — sidebar honesty: no 'Sắp có' on Tra cứu thuế / HS");
{
  const aside = $("aside")[0];
  const item = findClickable("Tra cứu thuế / HS", "a", aside);
  assert.ok(item, "sidebar item missing");
  assert.ok(!text(item).includes("Sắp có"), "item still marked 'Sắp có'");
  ok("sidebar item is active, no deferred marker");
  await click("Tra cứu thuế / HS", "a", aside);
}

// ---------------------------------------------------------------------------
console.log("STEP 3 — /tra-cuu-thue opens the REAL lookup workspace");
await click("Tra cứu thuế / HS", "a");
{
  const t = mainText();
  assert.ok(t.includes("Tra cứu HS & Thuế"), "workspace heading missing");
  assert.ok(t.includes("9401.61.00"), "last reader result not rendered");
  assert.ok(t.includes("Ghế ngồi có lưng, khung bằng gỗ"), "VN description missing");
  assert.ok(t.includes("Seats with wooden frames"), "EN description missing");
  assert.ok(t.includes("tariff_table"), "source status banner missing");
  assert.ok(t.includes("chính thức"), "provenance honesty banner missing");
  assert.ok(t.includes("Tìm thấy 1 dòng"), "honest count line missing");
  // UNKNOWN != ZERO: the canonical schema has no rate fields; the extra
  // column must show the em dash, never a fabricated 0 / 0%.
  const cells = $("td").map((el) => text(el));
  assert.ok(cells.some((c) => c === "—" || c.includes("—")), "unknown cell must render as —");
  assert.ok(!t.includes("0%"), "page must never fabricate a 0% rate");
  ok("real reader result + source status + provenance honesty rendered");
}

// ---------------------------------------------------------------------------
console.log("STEP 4 — search interaction emits the bounded READ-ONLY trigger");
{
  const input = $('input[aria-label="Mã HS hoặc tên hàng"]')[0];
  assert.ok(input, "search input missing");
  await type(input, "9403");
  const before = triggers.length;
  await click("Tra cứu", "button");
  await tick(120);
  const lookup = triggers.slice(before).filter((tr) => tr.event === "tariff_lookup");
  assert.equal(lookup.length, 1, "expected exactly one tariff_lookup trigger");
  assert.equal(lookup[0].value.event, "tariff_lookup");
  assert.equal(lookup[0].value.payload.query, "9403");
  assert.equal(typeof lookup[0].value.seq, "number");
  ok("one typed tariff_lookup trigger with the query payload");
}

// ---------------------------------------------------------------------------
console.log("STEP 5 — fresh readback rerender shows the new result (unknown as —)");
{
  const rows9403 = [{
    hsCode: "9403.20.10",
    descriptionVi: "Bàn kim loại cho văn phòng",
    descriptionEn: "Metal office tables",
    fields: [],
  }];
  lastInvokeCleanup = invoke({
    ...VM,
    tariff: { ...VM.tariff, query: "9403", searched: true, reason: null, rows: rows9403, count: 1 },
  });
  await tick(120);
  const t = mainText();
  assert.ok(t.includes("9403.20.10"), "fresh readback result missing");
  assert.ok(t.includes("Bàn kim loại cho văn phòng"), "fresh VN description missing");
  ok("route + results survive a backend rerun (fresh read delivered)");
}

// ---------------------------------------------------------------------------
console.log("STEP 6 — honest no-match state (page revisited, last read = no match)");
{
  await remount({
    ...VM,
    tariff: {
      ...VM.tariff,
      query: "zzzz-khong-co",
      searched: true,
      rows: [],
      count: 0,
      reason: "Không tìm thấy dòng nào khớp trong cơ sở dữ liệu tham chiếu nội bộ.",
    },
  });
  await tick(120);
  const t = mainText();
  assert.ok(t.includes("Không tìm thấy kết quả"), "no-match heading missing");
  assert.ok(t.includes("Không tìm thấy dòng nào khớp"), "no-match reason missing");
  assert.ok(!t.includes("9403.20.10"), "stale rows must not linger");
  ok("no-match state is explicit, no fabricated rows");
}

// ---------------------------------------------------------------------------
console.log("STEP 7 — mobile: drawer routes to the same workspace; cards exist");
{
  await clickSelector('button[aria-label="Mở menu"]');
  const drawer = $("div.anim-slide-up").filter((el) => text(el).includes("Menu điều hành"))[0]
    ?? $(".fixed.inset-0.z-50")[0];
  assert.ok(drawer, "mobile drawer missing");
  const drawerItem = findClickable("Tra cứu thuế / HS", "a", drawer);
  assert.ok(drawerItem, "drawer item missing");
  assert.ok(!text(drawerItem).includes("Sắp có"), "drawer item still marked 'Sắp có'");
  await click("Tra cứu thuế / HS", "a", drawer);
  assert.ok(mainText().includes("Tra cứu HS & Thuế"), "drawer must open the tariff workspace");
  // The md:hidden card container is present in the DOM (CSS hides it on
  // desktop only), so narrow viewports read cards, not a min-width table.
  const mobileCards = $(".md-hidden").length > 0 || $("div[class*='md:hidden']").length > 0;
  assert.ok(mobileCards, "mobile card container missing");
  const touchInput = $('input[aria-label="Mã HS hoặc tên hàng"]')[0];
  assert.ok(touchInput.className.includes("min-h-[48px]"), "search input below touch target");
  ok("drawer routes to the workspace; mobile cards + 48px touch input present");
}

console.log(`\nDOM acceptance PASSED — ${passed} checks`);
