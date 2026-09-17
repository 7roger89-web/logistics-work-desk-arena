// ============================================================================
// LOGI_NEXT_ACTION_TAB_REPAIR_01 + LOGI_CONTRACT_DOC_HANDOFF_01 — DOM
// acceptance for the two broken employee handoffs on the shipment work desk.
//
// Runs the REAL production bundle (component/dist/logi-shell.js) in jsdom with
// the REAL-backend consolidation fixture (scripts/gen_consolidation_fixture.py
// — isolated mongomock staging) and verifies the fixed contracts:
//
//   1. "XỬ LÝ NGAY" (NextActionBanner) with nextRoute /lo-hang/LO-0295?tab=
//      lay-hang opens the REAL "lay-hang" work section. The old bundle's
//      /\w+/ capture truncated the hyphenated id to the non-existent tab
//      "lay", so no work section appeared at all.
//   2. The non-hyphenated tab routing (nhap) still works — regression guard
//      for the same banner.
//   3. "MỞ CHỨNG TỪ" from a linked contract reaches the EXISTING contract
//      document workdesk (/hop-dong/<id>?tab=chung-tu — the HDNT/PL/HDMB
//      docgen surface). The old bundle only re-selected the shipment's own
//      "chung-tu" tab and toasted, leaving the employee in shipment PXK
//      documents.
//
// Run: node tests/component/dom_acceptance_next_action_handoff.mjs
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
  readFileSync(path.join(ROOT, "tests/component/fixtures/view_model_consolidation.json"), "utf8")
);

const LOT_LAY_HANG = "LO-0295"; // nextRoute …?tab=lay-hang (hyphenated)
const LOT_NHAP = "LO-0306"; // nextRoute …?tab=nhap (non-hyphenated)
const CONTRACT = "HDMB-0295"; // the contract linked to LO-0295

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

let passed = 0;
function ok(name) {
  passed += 1;
  console.log(`  ✓ ${name}`);
}

const host = window.document.createElement("div");
window.document.body.appendChild(host);
const mountRef = { current: null };
function invoke(data) {
  mountRef.current({
    name: "logi_shell",
    data,
    parentElement: host,
    setTriggerValue: () => {},
  });
}

const bundlePath = path.join(ROOT, "component/dist/logi-shell.js");

const mod = await import(bundlePath);
assert.equal(typeof mod.default, "function");
mountRef.current = mod.default;

async function openShipmentDetail(lotId) {
  invoke(VM);
  await tick(120);
  await click("Lô Hàng", "a", $("aside")[0]);
  await click(lotId, "a", $("main")[0]);
  assert.ok(mainText().includes(lotId), `shipment detail for ${lotId} missing`);
}

// ---------------------------------------------------------------------------
console.log("STEP 1 — 'XỬ LÝ NGAY' with tab=lay-hang opens the REAL lay-hang section");
{
  await openShipmentDetail(LOT_LAY_HANG);
  // The banner is the page's own next action; the fixture's nextRoute really
  // carries the hyphenated tab id.
  const lot = VM.shipments.find((s) => s.id === LOT_LAY_HANG);
  assert.equal(lot.nextRoute, `/lo-hang/${LOT_LAY_HANG}?tab=lay-hang`,
    "fixture precondition: the banner route must carry tab=lay-hang");
  assert.equal(lot.nextLabel, "XỬ LÝ NGAY", "fixture precondition: the banner action label");
  assert.ok(!mainText().includes("Nhà máy & xuất khẩu"),
    "precondition: the lay-hang section must not be open on the default tab");

  await click("XỬ LÝ NGAY", "button");
  await tick(120);

  const t = mainText();
  // THE regression: the old /\w+/ capture turned "lay-hang" into tab "lay",
  // which matches NO tab id, so no work section rendered at all.
  assert.ok(t.includes("Nhà máy & xuất khẩu"),
    "the lay-hang work section must actually render (old bundle truncated the tab to 'lay')");
  assert.ok(t.includes("Xuất khẩu —"), "the export status block of the lay-hang section missing");
  // The lay-hang TAB button itself must be the selected one.
  const activeTab = $("button")
    .find((b) => text(b).includes("Xuất khẩu") && (b.getAttribute("class") || "").includes("bg-[#0f2a4a]"));
  assert.ok(activeTab, "the lay-hang tab button must be the active/selected tab");
  ok("'XỬ LÝ NGAY' → tab=lay-hang intact → real work section rendered");
}

// ---------------------------------------------------------------------------
console.log("STEP 2 — regression: non-hyphenated tab routing still works");
{
  await openShipmentDetail(LOT_NHAP);
  const lot = VM.shipments.find((s) => s.id === LOT_NHAP);
  assert.equal(lot.nextRoute, `/lo-hang/${LOT_NHAP}?tab=nhap`,
    "fixture precondition: the banner route must carry tab=nhap");
  assert.ok(!mainText().includes("Tờ khai & thuế nhập khẩu"),
    "precondition: the nhap section must not be open on the default tab");

  await click("XỬ LÝ NGAY", "button");
  await tick(120);
  assert.ok(mainText().includes("Tờ khai & thuế nhập khẩu"),
    "the nhap work section must still render after the regex repair");
  ok("'XỬ LÝ NGAY' → tab=nhap still routes correctly");
}

// ---------------------------------------------------------------------------
console.log("STEP 3 — 'MỞ CHỨNG TỪ' reaches the EXISTING contract document workdesk");
{
  await openShipmentDetail(LOT_LAY_HANG);
  // Open the shipment's own documents tab, where the linked-contract card lives.
  await click("Chứng từ & PXK", "button");
  await tick(120);
  const t = mainText();
  assert.ok(t.includes("Hợp đồng liên kết"), "linked-contract card missing on the docs tab");
  assert.ok(t.includes(CONTRACT), "the linked contract id must be visible");
  assert.ok(t.includes("MỞ CHỨNG TỪ"), "the MỞ CHỨNG TỪ action must exist");
  assert.ok(t.includes("Phiếu xuất kho"), "precondition: we are on the shipment PXK documents surface");
  assert.ok(!t.includes("Chứng từ HDNT · PL · HDMB"),
    "precondition: the contract document desk is not open yet");

  await click("MỞ CHỨNG TỪ", "a");
  await tick(160);

  const after = mainText();
  // The employee must land on the CONTRACT document workdesk for THIS
  // contract — its own Chứng từ tab with the real docgen actions.
  assert.ok(after.includes(CONTRACT), "the contract detail must be open for the linked contract");
  assert.ok(after.includes("Chứng từ HDNT · PL · HDMB"),
    "the contract's own document section must be open (the existing docgen workdesk)");
  assert.ok(after.includes("SINH CHỨNG TỪ"),
    "the real docgen generate action of the contract workdesk must be reachable");
  assert.ok(!after.includes("Phiếu xuất kho (PXK)"),
    "the employee must no longer be on the shipment PXK documents surface");
  ok("'MỞ CHỨNG TỪ' → existing contract document workdesk, correct contract, right tab");
}

console.log(`\nNEXT-ACTION-HANDOFF DOM acceptance PASSED — ${passed} checks`);
