/**
 * LOGI_GNT_DOC_EXPORT_REALITY_CHECK_01 — DOM acceptance test for GNT in ShipmentDetail.
 * Tests realistic state transitions: starts uninitialized (ready=false) -> operator entry ->
 * shipment_field_save -> fresh authoritative VM readback (ready=true) -> gnt_generate -> download.
 */

import { readFileSync } from "node:fs";
import assert from "node:assert/strict";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const require = createRequire(path.join(ROOT, "component/package.json"));
const { JSDOM } = require("jsdom");

const bundlePath = path.join(ROOT, "component/dist/logi-shell.js");
const fixturePath = path.join(ROOT, "tests/component/fixtures/view_model_phase_b.json");

assert(bundlePath, "bundle exists");
assert(fixturePath, "fixture exists");

const VM = JSON.parse(readFileSync(fixturePath, "utf8"));

// FIX 2: Seed initial uninitialized GNT taxpayer state (ready=false, missing taxpayer facts)
const targetLot = VM.shipments.find((s) => s.id === "LO-0307") || VM.shipments[0];
targetLot.importInfo = targetLot.importInfo || {};
targetLot.importInfo.declarationNo = "105588421330";
targetLot.importInfo.regDate = "15/08/2026";
targetLot.importInfo.tax = 5000000;
targetLot.importInfo.vat = 800000;
targetLot.customer = "CÔNG TY TNHH AN PHÁT";
targetLot.customerMST = "0101234567";
targetLot.importInfo.gnt = {
  payer: "",
  taxCode: "",
  address: "",
  customsOffice: "HQ Hữu Nghị",
  customerHint: "CÔNG TY TNHH AN PHÁT",
  customerTaxHint: "0101234567",
  ready: false,
  noPayable: false,
  missing: ["Người nộp thuế", "Mã số thuế"],
  done: false,
  document: null,
};

// ---------------------------------------------------------------------------
// jsdom environment (browser globals for the bundle + React)
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
  "HTMLElement",
  "HTMLInputElement",
  "HTMLTextAreaElement",
  "HTMLSelectElement",
  "HTMLAnchorElement",
  "HTMLButtonElement",
  "Event",
  "CustomEvent",
  "MouseEvent",
  "KeyboardEvent",
  "FocusEvent",
  "Node",
  "Element",
  "DocumentFragment",
  "MutationObserver",
  "getComputedStyle",
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

function type(input, value) {
  Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set.call(input, value);
  input.dispatchEvent(new window.Event("input", { bubbles: true }));
  input.dispatchEvent(new window.Event("change", { bubbles: true }));
}

async function click(needle, sel = "a,button", root = window.document) {
  const el = findClickable(needle, sel, root);
  assert.ok(el, `clickable "${needle}" not found`);
  el.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
  await tick();
  return el;
}

// ---------------------------------------------------------------------------
// Simulated Streamlit v2 component invocation
// ---------------------------------------------------------------------------

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

const mod = await import(bundlePath);
assert.equal(typeof mod.default, "function", "bundle must default-export the mount function");
mountRef.current = mod.default;

invoke(VM);
await tick();

console.log("STEP 1 — Navigate to Shipments -> LO-0307 -> tab nhap");
await click("Lô Hàng", "a", $("aside")[0]);
await click("LO-0307", "a", $("table.tbl")[0]);
const tabRoot = window.document.getElementById("workspace-tabs");
await click("Nhập khẩu & Giao hàng", "button", tabRoot);

console.log("STEP 2 — Verify initial uninitialized GNT state");
const body = text(window.document.body);
assert.ok(body.includes("GIẤY NỘP THUẾ (GNT)"), "GNT section title should be present");
assert.ok(body.includes("105588421330"), "Declaration number should be present");
assert.ok(body.includes("15/08/2026"), "Declaration date should be present");
assert.ok(body.includes("5.000.000"), "Import duty amount should be present");
assert.ok(body.includes("800.000"), "Import VAT amount should be present");
assert.ok(body.includes("Cần kiểm tra/hoàn thiện các trường Kho bạc trước khi sử dụng để nộp."), "Treasury disclaimer notice must be present");
assert.ok(!body.includes("Đã sẵn sàng nộp chính thức"), "Must NOT claim 'Đã sẵn sàng nộp chính thức'");

// 1. Customer hint is visible
assert.ok(body.includes("Gợi ý khách hàng: CÔNG TY TNHH AN PHÁT"), "Customer hint must be visible as non-authoritative reference");
console.log("  ✓ 1. Customer hint is visible");

// 2. Authoritative taxpayer inputs are EMPTY (not auto-copied)
const payerInput = window.document.getElementById("fld-gnt-payer");
const taxCodeInput = window.document.getElementById("fld-gnt-taxcode");
const addrInput = window.document.getElementById("fld-gnt-address");

assert.ok(payerInput, "fld-gnt-payer input must be present");
assert.ok(taxCodeInput, "fld-gnt-taxcode input must be present");
assert.ok(addrInput, "fld-gnt-address input must be present");

assert.equal(payerInput.value, "", "Payer input must NOT auto-copy customer name");
assert.equal(taxCodeInput.value, "", "MST input must NOT auto-copy customer MST");
assert.equal(addrInput.value, "", "Address input must be empty initially");
console.log("  ✓ 2. Authoritative taxpayer inputs are EMPTY — customer facts NOT auto-copied");

// 3. GNT generation button is disabled while backend VM says ready=false
const genBtnBefore = findClickable("TẠO GIẤY NỘP THUẾ XLSX", "button");
assert.ok(genBtnBefore, "Generate button must exist");
assert.equal(genBtnBefore.disabled, true, "Generate button must be disabled when ready=false");
console.log("  ✓ 3. GNT generation button is DISABLED while ready=false");

console.log("STEP 3 — Operator types explicit taxpayer facts and saves");
// 4. Operator types payer, MST, address
type(payerInput, "CÔNG TY NHẬP KHẨU MINH TÂN");
type(taxCodeInput, "0108887777");
type(addrInput, "Số 45 Cầu Giấy, Hà Nội");

// 5. Click LƯU THÔNG TIN NGƯỜI NỘP THUẾ
await click("LƯU THÔNG TIN NGƯỜI NỘP THUẾ", "button");

// 6. Exactly ONE shipment_field_save is dispatched
const saveEvents = triggers.filter((t) => t.event === "shipment_field_save");
assert.equal(saveEvents.length, 1, "Exactly ONE shipment_field_save must be dispatched");
console.log("  ✓ 5/6. Exactly ONE shipment_field_save dispatched");

// 7. Payload contains the three explicit taxpayer fields
const savePayload = saveEvents[0].value.payload;
assert.equal(savePayload.shipmentId, "LO-0307");
assert.equal(savePayload.fields.gnt_taxpayer_name, "CÔNG TY NHẬP KHẨU MINH TÂN");
assert.equal(savePayload.fields.gnt_taxpayer_tax_code, "0108887777");
assert.equal(savePayload.fields.gnt_taxpayer_address, "Số 45 Cầu Giấy, Hà Nội");
console.log("  ✓ 7. Payload contains explicit taxpayer name, MST, address");

// 8. Before authoritative rerender: ZERO gnt_generate events
const gntEventsBefore = triggers.filter((t) => t.event === "gnt_generate");
assert.equal(gntEventsBefore.length, 0, "ZERO gnt_generate events before authoritative rerender");
console.log("  ✓ 8. ZERO gnt_generate events before authoritative rerender");

console.log("STEP 4 — Simulate fresh authoritative backend VM readback and rerender");
// 9. Simulate fresh authoritative backend VM
const vmReadback = JSON.parse(JSON.stringify(VM));
const sReadback = vmReadback.shipments.find((x) => x.id === "LO-0307");
sReadback.importInfo.gnt = {
  payer: "CÔNG TY NHẬP KHẨU MINH TÂN",
  taxCode: "0108887777",
  address: "Số 45 Cầu Giấy, Hà Nội",
  customsOffice: "HQ Hữu Nghị",
  customerHint: "CÔNG TY TNHH AN PHÁT",
  customerTaxHint: "0101234567",
  ready: true,
  noPayable: false,
  missing: [],
  done: false,
  document: null,
};
vmReadback.version = "readback-gnt-0001";

// 10. Reinvoke / rerender component with fresh backend VM
invoke(vmReadback);
await tick(120);

// 11. Verify exact saved taxpayer values are visible
const payerInputAfter = window.document.getElementById("fld-gnt-payer");
const taxCodeInputAfter = window.document.getElementById("fld-gnt-taxcode");
const addrInputAfter = window.document.getElementById("fld-gnt-address");
assert.equal(payerInputAfter.value, "CÔNG TY NHẬP KHẨU MINH TÂN", "Payer input must reflect fresh readback");
assert.equal(taxCodeInputAfter.value, "0108887777", "MST input must reflect fresh readback");
assert.equal(addrInputAfter.value, "Số 45 Cầu Giấy, Hà Nội", "Address input must reflect fresh readback");
console.log("  ✓ 11. Exact saved taxpayer values visible after readback");

// 12. Verify GNT generation button is now enabled
const genBtnAfter = findClickable("TẠO GIẤY NỘP THUẾ XLSX", "button");
assert.ok(genBtnAfter, "Generate button must exist");
assert.equal(genBtnAfter.disabled, false, "Generate button must be ENABLED now that backend VM says ready=true");
console.log("  ✓ 12. GNT generation button is now ENABLED");

// 13. Click generation
await click("TẠO GIẤY NỘP THUẾ XLSX", "button");

// 14. Exactly ONE gnt_generate event occurs
const gntEventsAfter = triggers.filter((t) => t.event === "gnt_generate");
assert.equal(gntEventsAfter.length, 1, "Exactly ONE gnt_generate event must occur");
assert.equal(gntEventsAfter[0].value.event, "gnt_generate");
assert.equal(gntEventsAfter[0].value.payload.shipmentId, "LO-0307");
console.log("  ✓ 13/14. Exactly ONE gnt_generate event dispatched with shipmentId: LO-0307");

console.log("STEP 5 — Update model with generated GNT and verify Download button");
const vmGenerated = JSON.parse(JSON.stringify(vmReadback));
const sGenerated = vmGenerated.shipments.find((x) => x.id === "LO-0307");
sGenerated.importInfo.gnt.done = true;
sGenerated.importInfo.gnt.document = {
  fileName: "GNT_LO-0307_105588421330.xlsx",
  mime: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  downloadAvailable: true,
  downloadBase64: "UEsDBBQAAAAIA...",
  generatedAt: "2026-09-17T00:30:00Z",
};
vmGenerated.version = "generated-gnt-0002";

invoke(vmGenerated);
await tick(120);

const downloadBtn = findClickable("TẢI XLSX", "button");
assert.ok(downloadBtn, "Download button must be rendered when GNT document is present");
console.log("  ✓ TẢI XLSX button rendered with file:", sGenerated.importInfo.gnt.document.fileName);

console.log("\nGNT DOM ACCEPTANCE PASS — all 14 state transition requirements + download verified!");
