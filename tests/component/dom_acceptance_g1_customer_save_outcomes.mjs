// ============================================================================
// G1 PR #228 — Negative & positive DOM acceptance for header customer save on
// /lo-hang/<id> over the REAL production bundle (component/dist/logi-shell.js):
//   1. Dispatch carries exact mixed-case customerId ("Cust-Excel-01") +
//      non-empty requestId, enters pending, and NEVER fires a green toast
//      before backend confirmation.
//   2. Stale/mismatched requestId outcomes are ignored.
//   3. Backend ok=false with matching requestId renders red alert + red toast
//      and retains the operator's selected customer.
//   4. Backend ok=true with mismatched readback (shipment.customerId still old)
//      renders red alert + red toast and retains the operator's selected
//      customer (never claims success).
//   5. Backend ok=true with matching requestId AND matching readback settles
//      pending, clears error, updates header, and fires green toast ONLY then.
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
  readFileSync(path.join(ROOT, "tests/component/fixtures/view_model_contract_shipment_edit.json"), "utf8"),
);
const LOT = FIX.shipment; // LO-0306

const MIXED_CUST = {
  id: "Cust-Excel-01",
  name: "Công Ty Mixed Case G1",
  taxCode: "0109988776",
  mst: "0109988776",
  contactPerson: "Trần Minh",
  phone: "0901234567",
  email: "mixed@example.vn",
  address: "Hà Nội",
  note: "",
};

const baseModel = {
  ...FIX.shipmentBefore,
  customers: [...(FIX.shipmentBefore.customers ?? []), MIXED_CUST],
  lastWrites: [],
};

const dom = new JSDOM("<!DOCTYPE html><html><body></body></html>", {
  url: `http://localhost:8501/lo-hang/${LOT}`,
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

const tick = (ms = 80) => new Promise((r) => setTimeout(r, ms));
const $ = (sel, root = window.document) => [...root.querySelectorAll(sel)];
const text = (el) => (el?.textContent || "").replace(/\s+/g, " ").trim();
const bodyText = () => text(window.document.body);
const byTestId = (id) => $(`[data-testid="${id}"]`)[0] ?? null;

function findClickable(needle, sel = "a,button", root = window.document) {
  const els = $(sel, root);
  return els.find((el) => text(el) === needle) || els.find((el) => text(el).includes(needle)) || null;
}

async function click(needle, sel = "a,button", root = window.document) {
  const el = findClickable(needle, sel, root);
  assert.ok(el, `clickable "${needle}" not found`);
  el.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
  await tick();
  return el;
}

async function clickTestId(id) {
  const el = byTestId(id);
  assert.ok(el, `element [data-testid="${id}"] not found`);
  el.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
  await tick();
  return el;
}

async function type(input, value) {
  assert.ok(input, "input element missing");
  Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set.call(input, value);
  input.dispatchEvent(new window.Event("input", { bubbles: true }));
  await tick();
}

const host = window.document.createElement("div");
window.document.body.appendChild(host);
const triggers = [];

const mod = await import(path.join(ROOT, "component/dist/logi-shell.js"));
const mount = mod.default;
let currentModel = baseModel;

function deliver(nextModel) {
  currentModel = nextModel;
  mount({
    name: "logi_shell",
    data: currentModel,
    parentElement: host,
    setTriggerValue: (event, value) => triggers.push({ event, value }),
  });
}

deliver(baseModel);
await tick(150);

// Navigate to /lo-hang/LO-0306 via sidebar + "Tất cả thời gian"
await click("Lô Hàng", "a", $("aside")[0]);
await click("Tất cả thời gian", "button", byTestId("shipment-period-controls"));
await click(LOT, "a", $("main")[0]);
await tick(120);
if (!byTestId("shipment-header-edit-toggle")) {
  const openInfo = findClickable("MỞ THÔNG TIN LÔ", "button") ?? byTestId("journey-global-page");
  if (openInfo) {
    openInfo.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
    await tick(120);
  }
}
assert.ok(byTestId("shipment-header-edit-toggle"), "lot header toggle must render");
await clickTestId("shipment-header-edit-toggle");
assert.equal(byTestId("shipment-header-edit-toggle").getAttribute("aria-expanded"), "true");

// 1. Pick mixed-case Cust-Excel-01 and click save -> NO premature success toast
await clickTestId("shipment-customer-picker-toggle");
await type(byTestId("shipment-customer-picker-search"), "Mixed Case");
await clickTestId("shipment-customer-picker-option-Cust-Excel-01");
assert.equal(byTestId("shipment-customer-picker").getAttribute("data-selected"), "Cust-Excel-01");

const beforeFirst = triggers.length;
await click("LƯU KHÁCH HÀNG CỦA LÔ", "button");
await tick(100);

const firstSaves = triggers.slice(beforeFirst).filter((t) => t.event === "shipment_customer_save");
assert.equal(firstSaves.length, 1, "one shipment_customer_save emitted");
const req1 = firstSaves[0].value.payload.requestId;
assert.ok(typeof req1 === "string" && req1.startsWith("HDRC-"), "requestId minted on save");
assert.equal(firstSaves[0].value.payload.customerId, "Cust-Excel-01", "exact mixed-case customerId preserved");
assert.ok(byTestId("shipment-header-customer-pending"), "pending indicator shown before backend answers");
assert.ok(!bodyText().includes("Đã lưu khách hàng của lô"), "no green toast before backend confirmation");
assert.ok(!bodyText().includes("Đã gửi đổi khách hàng của lô"), "legacy premature green toast removed");

// 2. Unrelated requestId must NOT settle pending or show success
deliver({
  ...currentModel,
  lastWrites: [{
    event: "shipment_customer_save",
    shipmentId: LOT,
    ok: true,
    error: "",
    requestId: "HDRC-OTHER-UNRELATED",
    readback: { id: LOT, customerId: "Cust-Excel-01", customer: "Công Ty Mixed Case G1" },
  }],
});
await tick(120);
assert.ok(byTestId("shipment-header-customer-pending"), "unrelated requestId must not settle pending");
assert.ok(!bodyText().includes("Đã lưu khách hàng của lô"), "unrelated requestId must not toast success");

// 3. Matching requestId with ok=false -> red error + retain selection
deliver({
  ...currentModel,
  lastWrites: [{
    event: "shipment_customer_save",
    shipmentId: LOT,
    ok: false,
    error: "Không có khách hàng Cust-Excel-01 đang hoạt động trong danh bạ.",
    requestId: req1,
    readback: null,
  }],
});
await tick(150);
assert.equal(byTestId("shipment-header-customer-pending"), null, "refusal settles pending");
const errEl1 = byTestId("shipment-header-customer-error");
assert.ok(errEl1, "red error alert rendered on refusal");
assert.equal(errEl1.getAttribute("role"), "alert");
assert.ok(text(errEl1).includes("Cust-Excel-01"), "refusal message rendered verbatim");
assert.equal(byTestId("shipment-customer-picker").getAttribute("data-selected"), "Cust-Excel-01",
  "failed save retains operator selection");
assert.ok(!bodyText().includes("Đã lưu khách hàng của lô"), "no success toast on refusal");

// 4. Retry -> matching requestId with ok=true BUT readback mismatch -> red error + retain selection
const beforeSecond = triggers.length;
await click("LƯU KHÁCH HÀNG CỦA LÔ", "button");
await tick(100);
const secondSaves = triggers.slice(beforeSecond).filter((t) => t.event === "shipment_customer_save");
assert.equal(secondSaves.length, 1, "retry emits fresh shipment_customer_save");
const req2 = secondSaves[0].value.payload.requestId;
assert.notEqual(req2, req1, "retry mints a fresh requestId");

deliver({
  ...currentModel,
  // Note: shipments still carries old customerId = CUST-ANPHAT -> readback mismatch!
  lastWrites: [{
    event: "shipment_customer_save",
    shipmentId: LOT,
    ok: true,
    error: "",
    requestId: req2,
    readback: { id: LOT, customerId: "CUST-ANPHAT", customer: "An Phát JSC" },
  }],
});
await tick(150);
const errEl2 = byTestId("shipment-header-customer-error");
assert.ok(errEl2, "readback mismatch renders red error alert");
assert.ok(text(errEl2).includes("chưa khớp"), "readback mismatch message explains why success was withheld");
assert.equal(byTestId("shipment-customer-picker").getAttribute("data-selected"), "Cust-Excel-01",
  "readback mismatch retains operator selection");
assert.ok(!bodyText().includes("Đã lưu khách hàng của lô"), "readback mismatch never toasts success");

// 5. Retry -> matching requestId + ok=true + verified readback -> green toast & updated header
const beforeThird = triggers.length;
await click("LƯU KHÁCH HÀNG CỦA LÔ", "button");
await tick(100);
const req3 = triggers.slice(beforeThird).filter((t) => t.event === "shipment_customer_save")[0].value.payload.requestId;

deliver({
  ...currentModel,
  shipments: currentModel.shipments.map((row) =>
    row.id === LOT
      ? { ...row, customerId: "Cust-Excel-01", customer: "Công Ty Mixed Case G1" }
      : row,
  ),
  lastWrites: [{
    event: "shipment_customer_save",
    shipmentId: LOT,
    ok: true,
    error: "",
    requestId: req3,
    readback: { id: LOT, customerId: "Cust-Excel-01", customer: "Công Ty Mixed Case G1" },
    persisted: { customerId: "Cust-Excel-01", customer: "Công Ty Mixed Case G1" },
  }],
});
await tick(150);
assert.equal(byTestId("shipment-header-customer-error"), null, "verified readback clears error");
assert.equal(byTestId("shipment-header-customer-pending"), null, "verified readback clears pending");
assert.ok(text(byTestId("shipment-header-edit")).includes(`Tên lô = ${LOT} · Công Ty Mixed Case G1`),
  "header displays verified customer name");
assert.equal(byTestId("shipment-customer-picker").getAttribute("data-selected"), "Cust-Excel-01");
assert.ok(bodyText().includes("Đã lưu khách hàng của lô"), "green toast fires ONLY after ok=true + verified readback");

console.log("G1 PR #228 header customer save outcome DOM acceptance PASSED.");
