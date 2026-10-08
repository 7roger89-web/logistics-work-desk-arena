/**
 * Issue #168 — FORM_07 "Biên bản giao nhận hàng hóa" DOM acceptance.
 *
 * Uses the CURRENT production bundle (component/dist/logi-shell.js) in jsdom
 * against a payload produced by the REAL staging stack — never hand-written
 * business data:
 *
 *   python3 scripts/gen_form07_dom_fixture.py --fixture /tmp/form07-dom.json
 *   node tests/component/dom_acceptance_form07_delivery_receipt.mjs /tmp/form07-dom.json
 *
 * The generator runs the real dispatcher on the isolated mongomock/GridFS
 * sandbox: selection save → form07_generate (R1 rendered by core.docgen.form07,
 * stored through the existing durable attachment path) → shipment_projection
 * readback + the real server-owned picker policy. This test then proves the
 * boundary contract in the DOM:
 *   1. FORM_07 reaches the picker ONLY through the server catalog and its
 *      durable selection readback (no hard-coded checkbox);
 *   2. the generated revision renders with its real provenance and the EXACT
 *      stored bytes download through the existing attachment path;
 *   3. regeneration (R+1) dispatches form07_generate with the server-owned
 *      identity snapshot, and missing identity fails closed client-side with
 *      the honest refusal wording (no invented defaults);
 *   4. deselection hides the card but NEVER deletes generated history;
 *   5. a blocked canonical gate (not delivered) renders the server's own
 *      reason/missing facts and the delivery action — the client invents
 *      nothing.
 */

import { readFileSync } from "node:fs";
import { createHash } from "node:crypto";
import assert from "node:assert/strict";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { createRequire } from "node:module";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const require = createRequire(path.join(ROOT, "component/package.json"));
const { JSDOM } = require("jsdom");
const bundlePath = path.join(ROOT, "component/dist/logi-shell.js");
const shellFixturePath = path.join(ROOT, "tests/component/fixtures/view_model_document_review.json");
const RAW = JSON.parse(readFileSync(shellFixturePath, "utf8"));
const FIX = JSON.parse(readFileSync(process.argv[2] || "/tmp/form07-dom.json", "utf8"));

const SHIPMENT_ID = FIX.shipmentId;                 // LO-0295 (delivered staging lot)
const FORM07_LABEL = "Biên bản giao nhận hàng hóa (FORM_07)";
const R1_FILE = FIX.expected.fileName;              // FORM07_LO-0295_BBGN-2026-0295.docx
const R1_ATTACHMENT_ID = FIX.expected.attachmentId;
const R1_SHA256 = FIX.expected.bytesSha256;
const R1_BYTES = Buffer.from(FIX.expected.bytesBase64, "base64");
const FORM07_NO = FIX.expected.form07No;
const ORDER_DATE = FIX.expected.orderDate;

const dom = new JSDOM("<!DOCTYPE html><html><body></body></html>", {
  url: "http://localhost:8501/",
  pretendToBeVisual: true,
});
const { window } = dom;
globalThis.window = window;
globalThis.document = window.document;
try {
  Object.defineProperty(globalThis, "navigator", { value: window.navigator, configurable: true });
} catch { /* use Node's navigator when present */ }
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
const recordBlob = (blob) => { savedFiles.push(blob); return "blob:form07-test"; };
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
const bodyText = () => text(window.document.body);

async function bytesOf(blob) {
  const reader = new window.FileReader();
  const result = await new Promise((resolve, reject) => {
    reader.onload = () => resolve(reader.result);
    reader.onerror = () => reject(reader.error || new Error("Could not read saved Blob"));
    reader.readAsArrayBuffer(blob);
  });
  return Buffer.from(result);
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

async function waitForDom(find, label) {
  for (let attempt = 0; attempt < 50; attempt++) {
    const element = find();
    if (element) return element;
    await tick();
  }
  assert.fail(label);
}

async function clickWhenReady(needle, selector, scopeSelector) {
  const element = await waitForDom(() => {
    const root = $(scopeSelector)[0];
    return root && findClickable(needle, selector, root);
  }, `clickable "${needle}" on ${scopeSelector}`);
  element.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
  await tick();
}

function setInputValue(input, value) {
  Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set.call(input, value);
  input.dispatchEvent(new window.Event("input", { bubbles: true }));
}

const host = window.document.createElement("div");
window.document.body.appendChild(host);
const triggers = [];
const mountRef = { current: null };
const events = (name) => triggers.filter((entry) => entry.event === name);
const clone = (value) => JSON.parse(JSON.stringify(value));

function prepareModel() {
  const model = clone(RAW);
  model.shipmentDocumentReview = null;
  model.lastWrites = [];
  // The REAL server-owned picker policy (catalog + gates) from the generator.
  model.shipmentDocumentPicker = clone(FIX.picker);
  // The REAL projected shipment row (delivery facts, form07, attachments) for
  // the delivered staging lot replaces the shell fixture's undelivered lot so
  // every rendered fact came from the backend, not from this test file.
  model.shipments = model.shipments.filter((row) => row.id !== SHIPMENT_ID);
  model.shipments.unshift(clone(FIX.shipment));
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

async function gotoDocuments() {
  // #190 moved the document tab into Journey's Global Workspace. Wait for each
  // actual navigation target rather than assuming every route mounts in 80 ms.
  await clickWhenReady("Lô Hàng", "a", "aside");
  await clickWhenReady("Tất cả thời gian", "button", "[data-testid='shipment-period-controls']");
  await clickWhenReady(SHIPMENT_ID, "a", "table.tbl");
  await clickWhenReady("Toàn bộ lô hàng", "button", "[data-testid='shipment-identity-bar']");
  await clickWhenReady("Chứng từ", "button", "[data-testid='journey-global-workspace']");
  return waitForDom(
    () => $("[data-testid='shipment-document-picker']")[0],
    "document picker is on the existing Shipment Detail",
  );
}

function form07Card(root = window.document) {
  const card = $("[data-testid='shipment-document-card']", root)
    .find((element) => element.dataset.documentId === "FORM_07");
  assert.ok(card, "FORM_07 card exists in the picker");
  return card;
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

function settleSelection(requestId, selectedIds) {
  currentModel = clone(currentModel);
  const shipment = currentModel.shipments.find((row) => row.id === SHIPMENT_ID);
  shipment.selectedDocumentTemplateIds = selectedIds;
  shipment.version = shipment.version + 1;
  currentModel.version = `form07-selection-${requestId}`;
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

const module = await import(pathToFileURL(bundlePath).href);
assert.equal(typeof module.default, "function");
mountRef.current = module.default;
invoke(currentModel);
await tick();

console.log("STEP 1 — FORM_07 arrives only through the server catalog + durable selection");
let picker = await gotoDocuments();
const catalogIds = FIX.picker.catalog.map((row) => row.id);
assert.ok(catalogIds.includes("FORM_07"), "the REAL server catalog contains FORM_07");
let cards = $("[data-testid='shipment-document-card']", picker);
assert.equal(cards.length, 1, "exactly the persisted selection is rendered");
let card = form07Card(picker);
assert.equal(card.dataset.state, "GENERATED");
assert.ok(text(card).includes(FORM07_LABEL), "card carries the catalog label");
assert.ok(text(card).includes("Giao nhận"), "card carries the catalog category");
assert.ok(text(card).includes(R1_FILE), "card shows the real generated file name");
assert.ok(text(card).includes("Lịch sử (1)"), "card shows the real bounded history");
assert.ok(text(card).includes("Đã có bản tạo"), "generated card keeps its honest reason");
assert.equal($("[data-testid='shipment-document-download-latest']", card)[0].disabled, false);
// No hard-coded checkbox: the dialog renders one option per REAL catalog row,
// and FORM_07 is checked from the server-side selection readback.
await click("Chọn biểu mẫu", "button", picker);
let dialog = $("[data-testid='shipment-document-picker-dialog']")[0];
assert.ok(dialog, "picker opens the existing multi-select sheet");
assert.equal(
  $("[data-testid='shipment-document-template-option']", dialog).length,
  catalogIds.length,
  "dialog options come 1:1 from the server catalog"
);
assert.ok(text(dialog).includes(FORM07_LABEL));
assert.equal(checkbox("FORM_07").checked, true, "durable selection readback checks FORM_07");
await click("Hủy", "button", dialog);
assert.equal($("[data-testid='shipment-document-picker-dialog']").length, 0);
console.log("  ✓ server-owned catalog row + persisted selection; GENERATED card with real provenance");

console.log("STEP 2 — panel renders the server snapshot; download returns the EXACT stored bytes");
const panel = $("[data-testid='shipment-form07-panel']")[0];
assert.ok(panel, "FORM_07 panel exists on the same chung-tu surface");
assert.ok(text(panel).includes("Biên bản giao nhận (FORM_07)"));
assert.ok(text(panel).includes("HDMB-0295"), "panel names the canonical source contract");
const numberInput = window.document.getElementById("fld-form07no");
const orderDateInput = window.document.getElementById("fld-form07orderdate");
assert.equal(numberInput.value, FORM07_NO, "identity number comes from the server snapshot");
assert.equal(orderDateInput.value, ORDER_DATE, "order date comes from the server snapshot");
const done = $("[data-testid='form07-done']", panel)[0];
assert.ok(done, "generated state renders");
assert.ok(text(done).includes(`ĐÃ TẠO ${FORM07_NO}`));
assert.ok(text(done).includes(R1_FILE) && text(done).includes("R1"));
assert.equal(savedFiles.length, 0);
await click(`TẢI ${R1_FILE}`, "button", panel);
assert.equal(savedFiles.length, 1, "the projected base64 hands exactly one Blob to the browser");
const savedBlob = savedFiles[0];
assert.equal(savedBlob.size, R1_BYTES.length, "saved size equals the durable stored size");
assert.equal(
  savedBlob.type,
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "saved MIME is the real DOCX type"
);
const savedBytes = await bytesOf(savedBlob);
assert.equal(createHash("sha256").update(savedBytes).digest("hex"), R1_SHA256,
  "downloaded bytes are byte-identical to the server-stored R1");
assert.equal(savedBytes.subarray(0, 2).toString(), "PK", "a real OOXML package reaches the DOM");
const anchor = clickedAnchors.find((row) => row.download === R1_FILE);
assert.ok(anchor && anchor.href === "blob:form07-test", "download uses the generated file name");
console.log("  ✓ exact-bytes download of the real R1 through the projection (sha256 match)");

console.log("STEP 3 — regeneration dispatches form07_generate; missing identity fails closed");
await click("SINH BẢN MỚI (R+1)", "button", panel);
assert.equal(events("form07_generate").length, 1, "one click emits exactly one form07_generate");
const genPayload = events("form07_generate")[0].value.payload;
assert.equal(genPayload.shipmentId, SHIPMENT_ID);
assert.equal(genPayload.form07No, FORM07_NO);
assert.equal(genPayload.orderDate, ORDER_DATE);
for (const key of Object.keys(genPayload)) {
  assert.ok(["shipmentId", "form07No", "orderDate", "requestId"].includes(key),
    `unexpected payload key ${key}`);
}
// Clear the legal number: the client must refuse with the honest wording and
// never dispatch with an empty or invented identity.
setInputValue(numberInput, "");
await tick();
await click("SINH BẢN MỚI (R+1)", "button", window.document);
assert.equal(events("form07_generate").length, 1, "refused generation dispatches nothing");
assert.ok(bodyText().includes("từ chối khi thiếu Số biên bản"),
  "the refusal names the missing identity field honestly");
console.log("  ✓ R+1 event carries the server identity snapshot; empty identity is refused, not invented");

console.log("STEP 4 — card download-latest: projected bytes first, then the EXISTING attachment path");
// The projection embeds the latest revision's bytes, so the first card click
// saves them directly without a backend round trip (existing card behavior).
const savedBeforeCard = savedFiles.length;
await click("Tải bản mới nhất", "button", form07Card());
assert.equal(savedFiles.length, savedBeforeCard + 1);
assert.equal(
  createHash("sha256").update(await bytesOf(savedFiles.at(-1))).digest("hex"),
  R1_SHA256,
  "card download hands over the exact stored R1 bytes"
);
assert.equal(events("attachment_download").length, 0,
  "bytes already in the session projection must not trigger a second backend read");
// Now the honest remount case: the server projects metadata only (no session
// bytes). The card MUST fall back to the existing bounded attachment_download
// event with the durable attachmentId — the same path PXK uses.
currentModel = clone(currentModel);
currentModel.shipments.find((row) => row.id === SHIPMENT_ID).form07.document.downloadBase64 = null;
currentModel.version = "form07-metadata-only";
currentModel.lastWrites = [];
invoke(currentModel);
await tick(140);
card = form07Card();
await click("Tải bản mới nhất", "button", card);
const downloads = events("attachment_download");
assert.equal(downloads.length, 1, "FORM_07 latest download emits one attachment_download");
const downloadPayload = downloads[0].value.payload;
assert.deepEqual(Object.keys(downloadPayload).sort(), ["attachmentId", "requestId", "shipmentId"]);
assert.equal(downloadPayload.shipmentId, SHIPMENT_ID);
assert.equal(downloadPayload.attachmentId, R1_ATTACHMENT_ID,
  "the durable attachmentId of R1 is the download target");
console.log("  ✓ projected-bytes download + metadata-only fallback through the existing attachment event");

console.log("STEP 5 — deselection hides the card but never deletes generated history");
picker = $("[data-testid='shipment-document-picker']")[0];
await click("Chọn biểu mẫu", "button", picker);
dialog = $("[data-testid='shipment-document-picker-dialog']")[0];
await setChecked("FORM_07", false);
await click("Lưu lựa chọn", "button", dialog);
const selectionEvents = events("shipment_document_selection_save");
assert.equal(selectionEvents.length, 1, "one save click emits exactly one selection event");
const selectionPayload = selectionEvents[0].value.payload;
assert.equal(selectionPayload.shipmentId, SHIPMENT_ID);
assert.deepEqual(selectionPayload.selectedTemplateIds, []);
assert.equal(selectionPayload.expectedVersion, FIX.shipment.version,
  "the save carries the authoritative version from the server row");
settleSelection(selectionPayload.requestId, []);
await tick(140);
picker = $("[data-testid='shipment-document-picker']")[0];
assert.equal($("[data-testid='shipment-document-card']", picker).length, 0,
  "deselection hides the FORM_07 card");
const historyAfter = currentModel.shipments.find((row) => row.id === SHIPMENT_ID)
  .form07.documentHistory[0];
assert.equal(historyAfter.recordId, FIX.shipment.form07.documentHistory[0].recordId,
  "generated history row is untouched by deselection");
assert.equal(historyAfter.attachmentId, R1_ATTACHMENT_ID);
// The panel (independent of the picker selection) still shows the stored R1.
const panelAfter = $("[data-testid='shipment-form07-panel']")[0];
assert.ok(panelAfter && text(panelAfter).includes(`ĐÃ TẠO ${FORM07_NO}`),
  "generated output remains reachable after deselection");
console.log("  ✓ deselection = hide only; durable history + panel output survive");

console.log("STEP 6 — blocked canonical gate renders the SERVER reason, client invents nothing");
const blockedModel = clone(currentModel);
const blockedRow = blockedModel.shipments.find((row) => row.id === SHIPMENT_ID);
blockedRow.form07 = {
  ...blockedRow.form07,
  delivered: false,
  done: false,
  document: null,
  documentHistory: [],
  readiness: {
    state: "MISSING_INFO",
    gate: "BLOCKED_NOT_DELIVERED",
    reason: "Biên bản giao nhận chỉ sẵn sàng sau khi lô được xác nhận đã giao.",
    missing: ["Xác nhận đã giao hàng"],
  },
};
blockedModel.version = "form07-blocked-gate";
blockedModel.lastWrites = [];
currentModel = blockedModel;
blockedRow.selectedDocumentTemplateIds = ["FORM_07"];
invoke(currentModel);
await tick();
picker = await gotoDocuments();
card = form07Card(picker);
assert.equal(card.dataset.state, "MISSING_INFO");
assert.ok(text(card).includes("Xác nhận đã giao hàng"), "server missing fact is rendered verbatim");
const gateAction = $("[data-testid='shipment-document-primary-action']", card)[0];
assert.ok(gateAction, "blocked card exposes the server-mapped action");
assert.equal(text(gateAction), "Mở xác nhận giao hàng",
  "BLOCKED_NOT_DELIVERED maps to the delivery surface, not a fake generate");
assert.equal($("[data-testid='shipment-document-download-latest']", card).length, 0,
  "no output block is invented while blocked");
const blockedPanel = $("[data-testid='shipment-form07-panel']")[0];
assert.ok(text(blockedPanel).includes("xác nhận đã giao hàng"),
  "panel states the missing canonical fact");
assert.equal(blockedPanel.querySelector("#fld-form07no").value, FORM07_NO,
  "typed identity snapshot is preserved across gate changes");
console.log("  ✓ fail-closed gate wording and action come from the server projection");

assert.ok(events("form07_generate").every((entry) => entry.value.payload.shipmentId === SHIPMENT_ID));
console.log("PASS: FORM_07 delivery receipt DOM acceptance");
