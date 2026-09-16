/**
 * LOGI_GNT_DOC_EXPORT_REALITY_CHECK_01 — DOM acceptance test for GNT in ShipmentDetail.
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

// Seed customs and GNT fields on fixture
const targetLot = VM.shipments.find((s) => s.id === "LO-0307") || VM.shipments[0];
targetLot.importInfo = targetLot.importInfo || {};
targetLot.importInfo.declarationNo = "105588421330";
targetLot.importInfo.regDate = "15/08/2026";
targetLot.importInfo.tax = 5000000;
targetLot.importInfo.vat = 800000;
targetLot.customer = "CÔNG TY TNHH AN PHÁT";
targetLot.customerMST = "0101234567";
targetLot.importInfo.gnt = {
  payer: "CÔNG TY TNHH AN PHÁT",
  taxCode: "0101234567",
  address: "Hà Nội",
  customsOffice: "HQ Hữu Nghị",
  ready: true,
  missing: [],
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

console.log("STEP 2 — Check GNT card presence and field values");
const body = text(window.document.body);
assert.ok(body.includes("GIẤY NỘP THUẾ (GNT)"), "GNT section title should be present");
assert.ok(body.includes("105588421330"), "Declaration number should be present");
assert.ok(body.includes("15/08/2026"), "Declaration date should be present");
assert.ok(body.includes("5.000.000"), "Import duty amount should be present");
assert.ok(body.includes("800.000"), "Import VAT amount should be present");
assert.ok(body.includes("Cần kiểm tra/hoàn thiện các trường Kho bạc trước khi sử dụng để nộp."), "Treasury disclaimer notice must be present");
assert.ok(!body.includes("Đã sẵn sàng nộp chính thức"), "Must NOT claim 'Đã sẵn sàng nộp chính thức'");
console.log("  ✓ GNT section rendered faithfully with disclaimer notice and no false official-ready claim");

console.log("STEP 3 — Click TẠO GIẤY NỘP THUẾ XLSX and verify gnt_generate dispatch");
await click("TẠO GIẤY NỘP THUẾ XLSX", "button");

assert.ok(triggers.length > 0, "An event should have been dispatched");
const ev = triggers.find((t) => t.event === "gnt_generate");
assert.ok(ev, "gnt_generate trigger not emitted");
assert.equal(ev.value.event, "gnt_generate", "Event name must be gnt_generate");
assert.equal(ev.value.payload.shipmentId, "LO-0307", "Payload must carry shipmentId");
console.log("  ✓ gnt_generate event successfully dispatched with shipmentId:", ev.value.payload.shipmentId);

console.log("STEP 4 — Update model with generated GNT and verify Download button");
const vm2 = JSON.parse(JSON.stringify(VM));
const s2 = vm2.shipments.find((x) => x.id === "LO-0307");
s2.importInfo.gnt.done = true;
s2.importInfo.gnt.document = {
  fileName: "GNT_LO-0307_105588421330.xlsx",
  mime: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  downloadAvailable: true,
  downloadBase64: "UEsDBBQAAAAIA...",
  generatedAt: "2026-09-16T15:30:00Z",
};
vm2.version = "rerun-gnt-0001";

invoke(vm2);
await tick(120);

const downloadBtn = findClickable("TẢI XLSX", "button");
assert.ok(downloadBtn, "Download button must be rendered when GNT document is present");
console.log("  ✓ TẢI XLSX button rendered with file:", s2.importInfo.gnt.document.fileName);

console.log("\nGNT DOM ACCEPTANCE PASS — all 4 steps verified!");
