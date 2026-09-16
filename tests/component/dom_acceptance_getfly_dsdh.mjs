// ============================================================================
// DOM acceptance — LOGI_GETFLY_DSDH_IMPORT_PARITY_01
//
// Runs against the production component/dist bundle. The browser side is
// allowed to read a real File into base64 for the bounded v2 trigger; all XLSX
// parsing and all commit facts remain server-authoritative in Python.
// ============================================================================

import { readFileSync } from "node:fs";
import assert from "node:assert/strict";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const require = createRequire(path.join(ROOT, "component/package.json"));
const { JSDOM } = require("jsdom");
const BASE = JSON.parse(readFileSync(path.join(ROOT, "tests/component/fixtures/view_model_phase_b.json"), "utf8"));

const dom = new JSDOM("<!DOCTYPE html><html><body></body></html>", {
  url: "http://localhost:8501/",
  pretendToBeVisual: true,
});
const { window } = dom;
globalThis.window = window;
globalThis.document = window.document;
try { Object.defineProperty(globalThis, "navigator", { value: window.navigator, configurable: true }); } catch {}
for (const k of [
  "HTMLElement", "HTMLInputElement", "HTMLTextAreaElement", "HTMLSelectElement",
  "HTMLAnchorElement", "Event", "CustomEvent", "MouseEvent", "KeyboardEvent",
  "Node", "MutationObserver", "File", "FileReader", "Blob", "FormData", "getComputedStyle",
]) globalThis[k] = window[k];
if (!globalThis.MessageChannel) globalThis.MessageChannel = window.MessageChannel;
window.HTMLElement.prototype.scrollIntoView = () => {};

const tick = (ms = 70) => new Promise((resolve) => setTimeout(resolve, ms));
const $ = (selector, root = window.document) => [...root.querySelectorAll(selector)];
const text = (element) => (element?.textContent || "").replace(/\s+/g, " ").trim();
const bodyText = () => text(window.document.body);
const byTestId = (id) => window.document.querySelector(`[data-testid="${id}"]`);

function findClickable(needle, selector = "a,button", root = window.document) {
  return $(selector, root).find((element) => text(element) === needle)
    || $(selector, root).find((element) => text(element).includes(needle))
    || null;
}

async function click(needle, selector = "a,button", root = window.document) {
  const element = findClickable(needle, selector, root);
  assert.ok(element, `clickable ${needle} not found`);
  element.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
  await tick();
  return element;
}

function type(input, value) {
  const proto = input.tagName === "TEXTAREA" ? window.HTMLTextAreaElement.prototype : window.HTMLInputElement.prototype;
  Object.getOwnPropertyDescriptor(proto, "value").set.call(input, value);
  input.dispatchEvent(new window.Event("input", { bubbles: true }));
  input.dispatchEvent(new window.Event("change", { bubbles: true }));
}

function clone(value) {
  return structuredClone(value);
}

function emptyGetFly() {
  return {
    status: "EMPTY", previewId: "", filename: "", orders: [],
    summary: { orders: 0, revenue: null, profit: null }, error: "",
  };
}

const preview = {
  status: "READY",
  previewId: "GF-PREVIEW-DOM-001",
  requestId: "GF-PREVIEW-REQUEST",
  filename: "DSDH.xlsx",
  fingerprint: "sha256-dom-fixture",
  summary: { orders: 2, revenue: 660000, profit: 230000 },
  orders: [
    {
      orderId: "LO-0306", customer: "An Phát JSC", customerName: "An Phát JSC",
      customerCode: "CUST-ANPHAT", customerId: "CUST-ANPHAT", customerMatch: "MATCHED_BY_CODE",
      orderDate: "2026-09-05", sourceStatus: "Đang xử lý", existing: true, revenue: 300000, profit: 100000,
      serviceLines: [
        { lineId: "LO-0306::L1", code: "VC-001", name: "Cước xe", description: "Chuyến chính", qty: 1, cost: 100000, price: 150000, revenue: 150000, profit: 50000 },
      ],
    },
    {
      orderId: "GF-DOM-001", customer: "Đức Long Co.", customerName: "Đức Long Co.",
      customerCode: "", customerId: "CUST-DUCLONG", customerMatch: "MATCHED_BY_NAME",
      orderDate: "2026-09-06", sourceStatus: "Đang xử lý", existing: false, revenue: 360000, profit: 130000,
      serviceLines: [
        { lineId: "GF-DOM-001::L1", code: "VC-NEW", name: "Vận chuyển mới", description: "Hàng mẫu", qty: 1, cost: 200000, price: 300000, revenue: 300000, profit: 100000 },
        { lineId: "GF-DOM-001::L2", code: "DV-NEW", name: "Bốc xếp", description: "Tại kho", qty: 3, cost: 10000, price: 20000, revenue: 60000, profit: 30000 },
      ],
    },
  ],
};

function freshVm() {
  const vm = clone(BASE);
  vm.getfly = emptyGetFly();
  vm.lastWrites = [];
  return vm;
}

function withOutcome(vm, outcome) {
  const next = clone(vm);
  next.lastWrites = [outcome];
  return next;
}

const host = window.document.createElement("div");
window.document.body.appendChild(host);
const triggers = [];
const mountRef = { current: null };

function invoke(data) {
  mountRef.current({
    name: "logi_shell", data, parentElement: host,
    setTriggerValue: (event, value) => triggers.push({ event, value }),
  });
}

function setSelectedFile(input, file) {
  Object.defineProperty(input, "files", { configurable: true, value: [file] });
  input.dispatchEvent(new window.Event("change", { bubbles: true }));
}

let passed = 0;
const ok = (label) => { passed += 1; console.log(`  ✓ ${label}`); };

console.log("STEP 1 — production bundle has the real file input, and no commit before preview");
const mod = await import(path.join(ROOT, "component/dist/logi-shell.js"));
assert.equal(typeof mod.default, "function");
mountRef.current = mod.default;
let vm = freshVm();
invoke(vm);
await tick(120);
await click("Lô Hàng", "a", window.document.querySelector("aside"));
assert.ok(byTestId("getfly-file-input"), "real file input missing");
assert.equal(findClickable("XÁC NHẬN NHẬP"), null, "commit must not exist before preview");

const file = new window.File([new Uint8Array([80, 75, 3, 4, 20, 0])], "DSDH.xlsx", {
  type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
});
const beforePreview = triggers.length;
setSelectedFile(byTestId("getfly-file-input"), file);
await tick(120);
const previewTriggers = triggers.slice(beforePreview).filter((item) => item.event === "getfly_preview");
assert.equal(previewTriggers.length, 1, "selecting one XLSX dispatches one preview intent");
assert.equal(previewTriggers[0].value.payload.filename, "DSDH.xlsx");
assert.ok(previewTriggers[0].value.payload.contentBase64, "file bytes must cross the bounded event");
assert.equal(triggers.slice(beforePreview).filter((item) => item.event === "getfly_import").length, 0);
ok("one real file input and one preview transport intent");

console.log("STEP 2 — server-authoritative preview renders KPI, both orders, service notes, and existing state");
vm = clone(vm);
vm.getfly = preview;
invoke(vm);
await tick(100);
const rendered = bodyText();
assert.ok(rendered.includes("DSDH.xlsx"));
assert.ok(rendered.includes("660.000"), rendered);
assert.ok(rendered.includes("230.000"), rendered);
assert.ok(rendered.includes("LO-0306"));
assert.ok(rendered.includes("GF-DOM-001"));
assert.ok(rendered.includes("Đã có trong hệ thống"));
assert.ok(rendered.includes("Chuyến chính"));
assert.ok(rendered.includes("Kiện gỗ") || rendered.includes("Hàng mẫu"));
assert.ok(byTestId("getfly-mode-shipment-only"));
assert.ok(byTestId("getfly-mode-finance"));
ok("preview card, KPIs, both orders, existing marker, and service descriptions");

console.log("STEP 3 — Mode A sends no finance payload, and fresh readback makes the new shipment visible");
const beforeModeA = triggers.length;
await click("XÁC NHẬN NHẬP", "button", byTestId("getfly-commit-panel"));
await tick();
const modeA = triggers.slice(beforeModeA).filter((item) => item.event === "getfly_import");
assert.equal(modeA.length, 1);
assert.equal(modeA[0].value.payload.mode, "SHIPMENT_ONLY");
assert.ok(!("vatByLineId" in modeA[0].value.payload));
assert.ok(!("orders" in modeA[0].value.payload));
const modeARequest = modeA[0].value.payload.requestId;
const created = clone(vm);
created.getfly = preview;
created.shipments.push({ ...clone(created.shipments.find((row) => row.id === "LO-0306")), id: "GF-DOM-001", customer: "Đức Long Co.", customerId: "CUST-DUCLONG" });
invoke(withOutcome(created, {
  event: "getfly_import", ok: true, requestId: modeARequest, previewId: preview.previewId,
  results: [
    { orderId: "LO-0306", status: "SKIPPED_ALREADY_EXISTS", message: "Đã có trong hệ thống" },
    { orderId: "GF-DOM-001", status: "CREATED", readback: { id: "GF-DOM-001" } },
  ],
}));
await tick(100);
assert.ok(bodyText().includes("GF-DOM-001"), "fresh shipment read must show the created order");
assert.ok(bodyText().includes("CREATED"), "authoritative result must be visible");
ok("Mode A carries no finance payload and waits for fresh shipment readback");

async function clickTestId(id) {
  const element = byTestId(id);
  assert.ok(element, `test id ${id} not found`);
  element.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
  await tick();
}

console.log("STEP 4 — Mode B exposes blank VAT, blocks blank VAT, then dispatches explicit 0 and 8");
await clickTestId("getfly-mode-finance");
const vatInputs = $('[data-testid^="getfly-vat-"]');
assert.equal(vatInputs.length, 2, "Mode B must expose one VAT input per missing service row");
assert.ok(vatInputs.every((input) => input.value === ""), "VAT starts blank, not 0 or 8");

const beforeBlank = triggers.length;
await click("XÁC NHẬN NHẬP", "button", byTestId("getfly-commit-panel"));
await tick();
assert.equal(triggers.slice(beforeBlank).filter((item) => item.event === "getfly_import").length, 0, "blank VAT must block commit");
assert.ok(bodyText().includes("VAT trống") || bodyText().includes("VAT / tiền bắt buộc chưa đủ"));
ok("blank VAT visibly blocks Finance Actual commit");

type(vatInputs[0], "0");
type(vatInputs[1], "8");
await tick();
const beforeModeB = triggers.length;
await click("XÁC NHẬN NHẬP", "button", byTestId("getfly-commit-panel"));
await tick();
const modeB = triggers.slice(beforeModeB).filter((item) => item.event === "getfly_import");
assert.equal(modeB.length, 1);
assert.equal(modeB[0].value.payload.mode, "SHIPMENT_AND_FINANCE");
assert.deepEqual(Object.values(modeB[0].value.payload.vatByLineId), ["0", "8"]);
const modeBRequest = modeB[0].value.payload.requestId;

const refused = clone(created);
refused.getfly = preview;
invoke(withOutcome(refused, {
  event: "getfly_import", ok: false, requestId: modeBRequest, previewId: preview.previewId,
  error: "Một hoặc nhiều đơn chưa được nhập; xem kết quả từng đơn.",
  results: [{ orderId: "GF-DOM-001", status: "REFUSED_VALIDATION", errors: ["VAT chưa nhập"] }],
}));
await tick(100);
assert.ok(bodyText().includes("REFUSED_VALIDATION"));
assert.ok(bodyText().includes("VAT chưa nhập"));
ok("authoritative VAT refusal remains visible");

console.log("STEP 5 — explicit VAT success result is read back, not inferred from transport");
const beforeSuccess = triggers.length;
await click("XÁC NHẬN NHẬP", "button", byTestId("getfly-commit-panel"));
await tick();
const secondModeB = triggers.slice(beforeSuccess).filter((item) => item.event === "getfly_import");
assert.equal(secondModeB.length, 1);
const successRequest = secondModeB[0].value.payload.requestId;
const success = clone(created);
success.getfly = preview;
invoke(withOutcome(success, {
  event: "getfly_import", ok: true, requestId: successRequest, previewId: preview.previewId,
  results: [{ orderId: "LO-0306", status: "SKIPPED_ALREADY_EXISTS" }, { orderId: "GF-DOM-001", status: "SKIPPED_ALREADY_EXISTS" }],
}));
await tick(100);
assert.ok(bodyText().includes("SKIPPED_ALREADY_EXISTS"));
assert.ok(bodyText().includes("GF-DOM-001"));
ok("explicit 0/8 dispatches once and the backend outcome remains authoritative");

console.log(`DOM_ACCEPTANCE_GETFLY_DSDH: PASS (${passed} checks)`);
