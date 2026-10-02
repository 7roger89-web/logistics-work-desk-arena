/**
 * Shipment Document Picker V1 DOM acceptance.
 *
 * Uses the current production bundle and a real staging view-model fixture,
 * adding only the picker policy/readiness fields that V1 projects on the server.
 * Verifies shipment-local multi-select, authoritative save/readback, refresh
 * persistence, readiness/history rendering, bounded attachment download, and
 * that deselection hides but never deletes generated history.
 *
 * Run: node tests/component/dom_acceptance_shipment_document_picker_v1.mjs
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
const fixturePath = path.join(ROOT, "tests/component/fixtures/view_model_document_review.json");
const RAW = JSON.parse(readFileSync(fixturePath, "utf8"));
const SHIPMENT_ID = RAW.fixture.shipmentId;
const PXK_ATTACHMENT_ID = "ATT-LO-0306-PXK-R1";
const PXK_FILE = "PXK_LO-0306_R1.xlsx";
const PXK_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet";
const PXK_BYTES = Buffer.from("PXK generated revision one attachment\n", "utf8");
const PXK_BASE64 = PXK_BYTES.toString("base64");

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
  /* use Node's navigator when present */
}
for (const key of [
  "HTMLElement", "HTMLInputElement", "HTMLTextAreaElement", "HTMLSelectElement",
  "HTMLAnchorElement", "HTMLButtonElement", "Event", "CustomEvent", "MouseEvent",
  "KeyboardEvent", "FocusEvent", "Node", "Element", "DocumentFragment",
  "MutationObserver", "File", "FileReader", "Blob", "getComputedStyle",
]) globalThis[key] = window[key];
if (!globalThis.MessageChannel) globalThis.MessageChannel = window.MessageChannel;
window.HTMLElement.prototype.scrollIntoView = () => {};
const savedFiles = [];
const clickedAnchors = [];
const recordBlob = (blob) => { savedFiles.push(blob); return "blob:picker-test"; };
window.URL.createObjectURL = recordBlob;
window.URL.revokeObjectURL = () => {};
if (globalThis.URL) {
  globalThis.URL.createObjectURL = recordBlob;
  globalThis.URL.revokeObjectURL = () => {};
}
window.HTMLAnchorElement.prototype.click = function recordClick() {
  clickedAnchors.push({ download: this.download, href: this.href });
};

const tick = (ms = 80) => new Promise((resolve) => setTimeout(resolve, ms));
const $ = (selector, root = window.document) => [...root.querySelectorAll(selector)];
const text = (element) => (element?.textContent || "").replace(/\s+/g, " ").trim();

async function bytesOf(blob) {
  const reader = new window.FileReader();
  const result = await new Promise((resolve, reject) => {
    reader.onload = () => resolve(reader.result);
    reader.onerror = () => reject(reader.error || new Error("Could not read saved Blob"));
    reader.readAsArrayBuffer(blob);
  });
  return new Uint8Array(result);
}

function findClickable(needle, selector = "a,button", root = window.document) {
  const elements = $(selector, root);
  return elements.find((element) => text(element) === needle)
    || elements.find((element) => text(element).startsWith(needle))
    || elements.find((element) => text(element).includes(needle))
    || null;
}

async function click(needle, selector = "a,button", root = window.document) {
  const element = findClickable(needle, selector, root);
  assert.ok(element, `clickable "${needle}" not found`);
  element.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
  await tick();
  return element;
}

const host = window.document.createElement("div");
window.document.body.appendChild(host);
const triggers = [];
const mountRef = { current: null };
const selectionEvents = () => triggers.filter((entry) => entry.event === "shipment_document_selection_save");
const downloadEvents = () => triggers.filter((entry) => entry.event === "attachment_download");
const clone = (value) => JSON.parse(JSON.stringify(value));

function prepareModel() {
  const model = clone(RAW);
  model.shipmentDocumentReview = null;
  model.lastWrites = [];
  model.shipmentDocumentPicker = {
    catalog: [
      { id: "HDNT", label: "Hợp đồng nguyên tắc (HDNT)", category: "Hợp đồng", adapter: "CONTRACT_DOCGEN", documentType: "HDNT", active: true, available: true, availabilityReason: "" },
      { id: "PL", label: "Phụ lục hợp đồng (PL)", category: "Hợp đồng", adapter: "CONTRACT_DOCGEN", documentType: "PL", active: true, available: true, availabilityReason: "" },
      { id: "HDMB", label: "Hợp đồng mua bán (HDMB)", category: "Hợp đồng", adapter: "CONTRACT_DOCGEN", documentType: "HDMB", active: true, available: true, availabilityReason: "" },
      { id: "PXK", label: "Phiếu xuất kho (PXK)", category: "Kho", adapter: "PXK_DOCGEN", documentType: "PXK", active: true, available: true, availabilityReason: "" },
      { id: "GNT", label: "Giấy nộp thuế (GNT)", category: "Hải quan", adapter: "GNT_BUILDER", documentType: "GNT", active: true, available: true, availabilityReason: "" },
    ],
    canSaveSelection: true,
    canGenerate: true,
    storageConfigured: true,
  };
  const shipment = model.shipments.find((row) => row.id === SHIPMENT_ID);
  assert.ok(shipment, "staging fixture shipment must exist");
  shipment.version = 7;
  shipment.selectedDocumentTemplateIds = [];
  shipment.importInfo.gnt.readiness = {
    state: "MISSING_INFO",
    gate: "BLOCKED_MISSING_PREREQUISITES",
    reason: "Chưa đủ thông tin tờ khai và thuế.",
    missing: ["Thuế nhập khẩu", "VAT hàng nhập khẩu"],
  };
  shipment.pxk.readiness = {
    state: "MISSING_INFO",
    gate: "BLOCKED_NOT_DELIVERED",
    reason: "PXK chỉ sẵn sàng sau khi xác nhận giao hàng.",
    missing: ["Xác nhận đã giao hàng"],
  };
  shipment.pxk.done = true;
  shipment.pxk.documentHistory = [{
    recordId: "PXK-LO-0306::R1",
    documentId: "PXK-LO-0306",
    documentType: "PXK",
    revision: 1,
    status: "GENERATED",
    fileName: PXK_FILE,
    mime: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    generatedAt: "2026-09-20T09:30:00+07:00",
    generatedBy: "staging.support",
    attachmentId: PXK_ATTACHMENT_ID,
    downloadAvailable: true,
  }];
  shipment.pxk.document = {
    recordId: "PXK-LO-0306::R1",
    documentId: "PXK-LO-0306",
    revision: 1,
    status: "GENERATED",
    fileName: PXK_FILE,
    mime: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    generatedAt: "2026-09-20T09:30:00+07:00",
    generatedBy: "staging.support",
    attachmentId: PXK_ATTACHMENT_ID,
    downloadAvailable: true,
    downloadBase64: null,
  };
  const contract = model.contracts.find((row) => row.id === shipment.contract);
  assert.ok(contract, "shipment fixture links an existing contract");
  const hdntGate = contract.docCards.find((row) => row.document_type === "HDNT");
  hdntGate.state = "READY";
  hdntGate.reason = "Cổng hợp đồng cho HDNT đã sẵn sàng.";
  hdntGate.missing = [];

  shipment.attachments.push({
    id: PXK_ATTACHMENT_ID,
    name: PXK_FILE,
    category: "other",
    categoryLabel: "Tài liệu khác",
    mime: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    originalSize: 5,
    storedSize: 5,
    sizeLabel: "5 B",
    compressionMode: "NONE",
    compressionLabel: "Giữ nguyên",
    uploadedAt: "2026-09-20T09:30:00+07:00",
    uploadedBy: "staging.support",
    status: "ACTIVE",
    downloadAvailable: false,
    downloadBase64: null,
    downloadSeq: 0,
  });
  return model;
}

let currentModel = prepareModel();
function invoke(model) {
  return mountRef.current({
    name: "logi_shell",
    data: model,
    parentElement: host,
    setTriggerValue: (event, value) => triggers.push({ event, value }),
  });
}
async function gotoPicker() {
  await click("Lô Hàng", "a", $("aside")[0]);
  // Seeded lots are dated in September 2026; select the explicit all-period
  // view so the fixture remains reachable as the test clock advances.
  await click("Tất cả thời gian", "button", $("[data-testid='shipment-period-controls']")[0]);
  await click(SHIPMENT_ID, "a", $("table.tbl")[0]);
  const tabs = window.document.getElementById("workspace-tabs");
  assert.ok(tabs, "shipment workspace tabs exist");
  await click("Quy trình & Chứng từ", "button", tabs);
  const picker = $("[data-testid='shipment-document-picker']")[0];
  assert.ok(picker, "document picker is on the existing Shipment Detail");
  return picker;
}
function checkbox(id) {
  const input = window.document.getElementById(`document-template-${id}`);
  assert.ok(input, `template ${id} checkbox exists`);
  return input;
}
async function setChecked(id, checked) {
  const input = checkbox(id);
  if (input.checked !== checked) input.click();
  await tick();
}
function settleSelection(requestId, selectedIds, version = null) {
  currentModel = clone(currentModel);
  const shipment = currentModel.shipments.find((row) => row.id === SHIPMENT_ID);
  shipment.selectedDocumentTemplateIds = selectedIds;
  shipment.version = version ?? (shipment.version + 1);
  currentModel.version = `picker-selection-${requestId}`;
  currentModel.lastWrites = [{
    event: "shipment_document_selection_save",
    shipmentId: SHIPMENT_ID,
    ok: true,
    requestId,
    gate: "SAVED",
    readback: { selectedDocumentTemplateIds: selectedIds, version: shipment.version },
  }];
  invoke(currentModel);
}
function settleAttachmentDownload(requestId) {
  currentModel = clone(currentModel);
  const shipment = currentModel.shipments.find((row) => row.id === SHIPMENT_ID);
  const attachment = shipment.attachments.find((row) => row.id === PXK_ATTACHMENT_ID);
  attachment.downloadAvailable = true;
  attachment.downloadBase64 = PXK_BASE64;
  attachment.downloadSeq = 1;
  currentModel.version = `picker-download-${requestId}`;
  currentModel.lastWrites = [{
    event: "attachment_download",
    shipmentId: SHIPMENT_ID,
    ok: true,
    requestId,
    gate: "DOWNLOADED",
    persisted: { attachmentId: PXK_ATTACHMENT_ID, fileName: PXK_FILE, seq: 1 },
  }];
  invoke(currentModel);
}

const module = await import(bundlePath);
assert.equal(typeof module.default, "function");
mountRef.current = module.default;
invoke(currentModel);
await tick();

console.log("STEP 1 — empty state and multi-select on the existing shipment detail");
let picker = await gotoPicker();
assert.ok($("[data-testid='shipment-document-picker-empty']", picker).length === 1);
assert.ok(text(picker).includes("Biểu mẫu & chứng từ"));
await click("Chọn biểu mẫu", "button", picker);
const dialog = $("[data-testid='shipment-document-picker-dialog']")[0];
assert.ok(dialog, "picker opens a single labelled multi-select sheet");
assert.equal($("[data-testid='shipment-document-template-option']", dialog).length, 5);
await setChecked("HDNT", true);
await setChecked("PXK", true);
await setChecked("GNT", true);
await click("Lưu lựa chọn", "button", dialog);
assert.equal(selectionEvents().length, 1, "one save click emits exactly one selection event");
const firstEvent = selectionEvents()[0];
const firstPayload = firstEvent.value.payload;
assert.equal(firstPayload.shipmentId, SHIPMENT_ID);
assert.equal(firstPayload.expectedVersion, 7);
assert.deepEqual(firstPayload.selectedTemplateIds, ["HDNT", "PXK", "GNT"]);
assert.equal(Object.keys(firstPayload).sort().join(","), "expectedVersion,requestId,selectedTemplateIds,shipmentId");
assert.ok($("[data-testid='shipment-document-selection-pending']", dialog).length === 1);
assert.ok($("[data-testid='shipment-document-selection-save']", dialog)[0].disabled);

const noOutcome = clone(currentModel);
noOutcome.version = "picker-no-outcome";
noOutcome.lastWrites = [];
currentModel = noOutcome;
invoke(currentModel);
await tick();
assert.ok($("[data-testid='shipment-document-picker-dialog']").length === 1, "pending selection waits for backend, not transport");
assert.ok($("[data-testid='shipment-document-selection-pending']").length === 1);
console.log("  ✓ one durable-list event with version; pending waits for correlated backend outcome");

console.log("STEP 2 — backend readback, state cards, known blockers and generated history");
settleSelection(firstPayload.requestId, ["HDNT", "PXK", "GNT"]);
await tick(160);
picker = $("[data-testid='shipment-document-picker']")[0];
assert.equal($("[data-testid='shipment-document-picker-dialog']").length, 0, "correlated success closes the sheet");
assert.equal($("[data-testid='shipment-document-card']", picker).length, 3);
const cardsById = new Map($("[data-testid='shipment-document-card']", picker).map((card) => [card.dataset.documentId, card]));
assert.equal(cardsById.get("HDNT").dataset.state, "READY");
assert.equal(cardsById.get("GNT").dataset.state, "MISSING_INFO");
assert.equal(cardsById.get("PXK").dataset.state, "GENERATED");
assert.ok(text(cardsById.get("HDNT")).includes("Sẵn sàng"));
assert.ok(text(cardsById.get("GNT")).includes("Thiếu thông tin"));
assert.ok(text(cardsById.get("GNT")).includes("Thuế nhập khẩu"));
assert.ok(text(cardsById.get("PXK")).includes("Đã tạo"));
assert.ok(text(cardsById.get("PXK")).includes(PXK_FILE));
assert.ok(text(cardsById.get("PXK")).includes("Lịch sử (1)"));
assert.ok(text(cardsById.get("PXK")).includes("Xác nhận đã giao hàng"), "generated output remains visible alongside known revision blockers");
assert.ok($("[data-testid='shipment-document-download-latest']", cardsById.get("PXK"))[0].disabled === false);
console.log("  ✓ READY / MISSING_INFO / GENERATED states use canonical gates and real history");

console.log("STEP 3 — PXK download readback arrives while Shipment Detail is unmounted");
assert.equal(
  currentModel.shipments.find((row) => row.id === SHIPMENT_ID).pxk.documentHistory[0].attachmentId,
  PXK_ATTACHMENT_ID,
  "generated PXK history must retain its durable attachmentId"
);
await click("Tải bản mới nhất", "button", cardsById.get("PXK"));
assert.equal(downloadEvents().length, 1, "the latest-PXK action emits exactly one attachment_download");
const downloadPayload = downloadEvents()[0].value.payload;
assert.deepEqual(Object.keys(downloadPayload).sort(), ["attachmentId", "requestId", "shipmentId"]);
assert.equal(downloadPayload.shipmentId, SHIPMENT_ID);
assert.equal(downloadPayload.attachmentId, PXK_ATTACHMENT_ID);
const savedBeforeRemount = savedFiles.length;
await click("Lô Hàng", "a", $("aside")[0]);
assert.equal($("[data-testid='shipment-document-picker']").length, 0, "leaving Shipment Detail must unmount its picker");
assert.equal($("#workspace-tabs").length, 0, "Shipment Detail workspace must be unmounted before readback");
assert.equal(clickedAnchors.filter((row) => row.download === PXK_FILE).length, 0, "no file is saved before backend readback");

// Deliver the ordinary correlated backend outcome and attachment projection
// while the shipment page (and ShipmentAttachments effect) is genuinely absent.
settleAttachmentDownload(downloadPayload.requestId);
await tick(140);
const readbackShipment = currentModel.shipments.find((row) => row.id === SHIPMENT_ID);
const readbackAttachment = readbackShipment.attachments.find((row) => row.id === PXK_ATTACHMENT_ID);
assert.ok(readbackAttachment, "backend readback must resolve the same durable attachment");
assert.equal(readbackAttachment.downloadAvailable, true);
assert.equal(readbackAttachment.downloadBase64, PXK_BASE64);
assert.equal(readbackAttachment.downloadSeq, 1);
assert.equal(currentModel.lastWrites[0].event, "attachment_download");
assert.equal(currentModel.lastWrites[0].requestId, downloadPayload.requestId);
assert.equal(currentModel.lastWrites[0].ok, true);
assert.equal(savedFiles.length, savedBeforeRemount, "unmounted Shipment Detail cannot consume bytes early");
assert.equal(clickedAnchors.filter((row) => row.download === PXK_FILE).length, 0);

// Re-enter the same lot and tab. The existing attachment path must consume
// that persisted session readback once, under the original generated filename.
picker = await gotoPicker();
await tick(160);
assert.ok(picker, "the same Shipment Detail remounts successfully");
assert.equal(downloadEvents().length, 1, "remount must not issue a second backend download");
const pxkAnchors = clickedAnchors.filter((row) => row.download === PXK_FILE);
assert.equal(pxkAnchors.length, 1, "the attachment path saves the PXK exactly once after remount");
assert.equal(savedFiles.length, savedBeforeRemount + 1, "exactly one local Blob is handed to the browser");
const savedPXK = savedFiles.at(-1);
assert.equal(savedPXK.size, PXK_BYTES.length, "saved output has the backend-read byte length");
assert.equal(savedPXK.type, PXK_MIME, "saved output retains the backend-projected MIME type");
assert.deepEqual([...await bytesOf(savedPXK)], [...PXK_BYTES], "saved file bytes match the backend readback");
assert.equal(pxkAnchors[0].href, "blob:picker-test");
console.log("  ✓ one durable PXK attachmentId → one download event → unmount → normal readback → remount → exact bytes saved once");

console.log("STEP 4 — deselection hides the card but preserves independent output history");
picker = $("[data-testid='shipment-document-picker']")[0];
await click("Chọn biểu mẫu", "button", picker);
const deselectDialog = $("[data-testid='shipment-document-picker-dialog']")[0];
await setChecked("PXK", false);
await click("Lưu lựa chọn", "button", deselectDialog);
assert.equal(selectionEvents().length, 2);
const deselectEvent = selectionEvents()[1].value;
assert.deepEqual(deselectEvent.payload.selectedTemplateIds, ["HDNT", "GNT"]);
settleSelection(deselectEvent.payload.requestId, ["HDNT", "GNT"]);
await tick(140);
picker = $("[data-testid='shipment-document-picker']")[0];
assert.equal($("[data-testid='shipment-document-card']", picker).length, 2);
assert.equal($("[data-document-id='PXK']", picker).length, 0);
assert.equal(currentModel.shipments.find((row) => row.id === SHIPMENT_ID).pxk.documentHistory[0].recordId, "PXK-LO-0306::R1");

// A fresh data delivery after a reload keeps the saved IDs; the generated PXK
// remains in canonical history even though the selection currently hides it.
currentModel = clone(currentModel);
currentModel.version = "picker-reload";
currentModel.lastWrites = [];
invoke(currentModel);
await tick();
picker = await gotoPicker();
assert.equal($("[data-testid='shipment-document-card']", picker).length, 2);
assert.ok(text(picker).includes("Đã chọn 2 biểu mẫu"));
await click("Chọn biểu mẫu", "button", picker);
const reloadDialog = $("[data-testid='shipment-document-picker-dialog']")[0];
assert.equal(checkbox("HDNT").checked, true);
assert.equal(checkbox("GNT").checked, true);
assert.equal(checkbox("PXK").checked, false);
console.log("  ✓ durable selection survives refresh; deselected PXK output remains stored");

assert.ok(!$("[data-testid='shipment-document-selection-error']").some((element) => /unknown|unsupported/i.test(text(element))));
assert.ok(selectionEvents().every((entry) => entry.value.payload.shipmentId === SHIPMENT_ID));
console.log("PASS: Shipment Document Picker V1 DOM acceptance");
