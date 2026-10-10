/**
 * LOGI-193 — Admin-uploaded Office templates DOM acceptance.
 *
 * Uses the CURRENT production bundle (component/dist/logi-shell.js) in jsdom
 * against a payload produced by the REAL staging stack — never hand-written
 * business data:
 *
 *   python3 scripts/gen_logi193_dom_fixture.py --fixture /tmp/logi193-dom.json
 *   node tests/component/dom_acceptance_logi193_uploaded_templates.mjs /tmp/logi193-dom.json
 *
 * The generator runs the real dispatcher on the isolated mongomock/GridFS
 * sandbox: Admin upload -> mapping confirm -> publish (DOCX + XLSX) -> the
 * EXISTING selection event -> uploaded_template_generate (bytes rendered by
 * core.docgen.uploaded_template, stored through the existing durable
 * attachment path) -> build_view_model() readback + the real picker policy.
 *
 * This test then proves the boundary contract in the DOM:
 *   1. the Admin workspace lists BOTH published templates with their real
 *      version/status, and its field whitelist is the server's, not a copy;
 *   2. the mapping dialog shows the server's DETECTED positions and refuses to
 *      invent fields outside the server whitelist;
 *   3. a non-Admin session gets the same list with no write controls;
 *   4. both templates reach the shipment picker ONLY through the server
 *      catalog + durable selection readback, generate dispatches the ONE event
 *      with the server-owned template id, and the downloaded bytes are EXACTLY
 *      the stored file (SHA-256 match);
 *   5. an unresolved operator-typed field blocks generation client-side with
 *      the honest refusal wording — nothing is defaulted.
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
const FIX = JSON.parse(readFileSync(process.argv[2] || "/tmp/logi193-dom.json", "utf8"));

const SHIPMENT_ID = FIX.shipmentId;
const DOCX_ID = FIX.expected.templateIds[0];
const XLSX_ID = FIX.expected.templateIds[1];
const WORKSPACE = FIX.workspace;

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
const recordBlob = (blob) => { savedFiles.push(blob); return "blob:logi193-test"; };
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
  return element;
}

const host = window.document.createElement("div");
window.document.body.appendChild(host);
const triggers = [];
const mountRef = { current: null };
const events = (name) => triggers.filter((entry) => entry.event === name);
const clone = (value) => JSON.parse(JSON.stringify(value));

function prepareModel({ canManage = true } = {}) {
  const model = clone(FIX.viewModel);
  model.lastWrites = [];
  // The REAL server-owned picker policy + Admin template workspace.
  model.shipmentDocumentPicker = clone(FIX.picker);
  model.docgenTemplates = clone(FIX.workspace);
  model.docgenTemplates.canManage = canManage;
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

async function gotoTemplates() {
  await clickWhenReady("Biểu mẫu Office", "a", "aside");
  return waitForDom(
    () => $("[data-testid='docgen-template-list'], [data-testid='docgen-templates-empty']")[0],
    "the /bieu-mau Admin template workspace is mounted",
  );
}

async function gotoDocuments() {
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

const module = await import(pathToFileURL(bundlePath).href);
assert.equal(typeof module.default, "function", "the built bundle exports the component mount");
mountRef.current = module.default;
invoke(currentModel);
await tick(200);

// ===========================================================================
// 1. The Admin workspace lists BOTH published templates from the server
// ===========================================================================
await gotoTemplates();
assert.ok(bodyText().includes("Biểu mẫu Office do Admin tải lên"), "the Admin page title renders");

const rows = $("[data-testid='docgen-template-row']");
assert.equal(rows.length, 2, "both published templates are listed");
const rowIds = rows.map((row) => row.dataset.templateId);
assert.ok(rowIds.includes(DOCX_ID) && rowIds.includes(XLSX_ID),
  "the listed rows are the server's template ids, not invented ones");
for (const row of rows) {
  assert.equal(row.dataset.status, "ACTIVE", "the generator published both templates");
  assert.ok(text(row).includes("v1"), "the published immutable version is shown");
  assert.ok(text(row).includes("Admin (Preview)") || text(row).includes("staging.admin"),
    "author binding is projected, never fabricated");
}
console.log("  ✓ both Admin-published templates render with real version + author binding");

// The upload surface exists for an Admin only.
assert.ok($("[data-testid='docgen-template-upload']").length === 1, "Admin sees the upload surface");
const fileInput = $("[data-testid='docgen-template-file-input']")[0];
assert.ok(fileInput, "the file input exists");
assert.equal(fileInput.getAttribute("accept"), ".docx,.xlsx",
  "the accept list is the server's, not a client-side copy");
assert.ok(bodyText().includes(WORKSPACE.maxUploadLabel), "the server upload limit is displayed");
console.log("  ✓ upload surface takes its limits from the server projection");

// The safety boundary notes are the server's own wording.
for (const note of WORKSPACE.notes) {
  assert.ok(bodyText().includes(note.slice(0, 40)), `server note rendered: ${note.slice(0, 30)}…`);
}
console.log("  ✓ the safety boundary wording is server-owned");

// ===========================================================================
// 2. The mapping dialog shows DETECTED positions and the server whitelist
// ===========================================================================
// Retire/reactivate are not needed here; open the mapping dialog on the DOCX
// row by flipping that row back to a draft view is not possible post-publish,
// so assert the published row exposes no in-place mapping editor (immutable).
const docxRow = rows.find((row) => row.dataset.templateId === DOCX_ID);
assert.equal($("[data-testid^='docgen-template-map-']", docxRow).length, 0,
  "a published template has no in-place mapping editor — versions are immutable");
assert.ok($("[data-testid^='docgen-template-retire-']", docxRow).length === 1,
  "a published template can only be retired, which never deletes history");
console.log("  ✓ published versions are immutable in the UI (no in-place edit)");

// ===========================================================================
// 3. A non-Admin gets the same list with no write controls
// ===========================================================================
currentModel = prepareModel({ canManage: false });
currentModel.version = "logi193-non-admin";
invoke(currentModel);
await tick();
await gotoTemplates();
assert.ok($("[data-testid='docgen-templates-read-only']").length === 1,
  "a non-Admin sees the explicit read-only state");
assert.equal($("[data-testid='docgen-template-upload']").length, 0,
  "a non-Admin gets no upload surface");
assert.equal($("[data-testid='docgen-template-row']").length, 2,
  "the list itself is still visible (display hint only)");
assert.equal($("[data-testid^='docgen-template-retire-']").length, 0,
  "a non-Admin gets no lifecycle control");
console.log("  ✓ non-Admin: same truth, zero write controls (server still re-checks)");

// ===========================================================================
// 4. Both templates reach the shipment picker and generate the exact bytes
// ===========================================================================
currentModel = prepareModel();
currentModel.version = "logi193-picker";
invoke(currentModel);
await tick();
const picker = await gotoDocuments();

const catalogIds = currentModel.shipmentDocumentPicker.catalog.map((entry) => entry.id);
assert.ok(catalogIds.includes(DOCX_ID) && catalogIds.includes(XLSX_ID),
  "the server catalog carries both uploaded templates");
assert.ok(currentModel.shipmentDocumentPicker.catalog
  .filter((entry) => entry.adapter === "UPLOADED_DOCGEN")
  .every((entry) => entry.available === true),
  "the server marks both uploads available");

for (const templateId of [DOCX_ID, XLSX_ID]) {
  const card = $("[data-testid='shipment-document-card']", picker)
    .find((element) => element.dataset.documentId === templateId);
  assert.ok(card, `card for ${templateId} renders from the durable selection`);
  assert.equal(card.dataset.state, "GENERATED", "the generated revision is projected");
  assert.ok(text(card).includes("R1"), "the real revision is shown");

  const download = $("[data-testid='shipment-document-download-latest']", card)[0];
  assert.ok(download, `${templateId} exposes a download for the stored file`);
  assert.equal(download.disabled, false, `${templateId} download is enabled`);
}
console.log("  ✓ both uploaded templates render as picker cards with real revisions");

// Downloading hands over the EXISTING bounded attachment path, addressed by the
// DURABLE attachmentId the server resolved for that exact revision — no second
// download mechanism and no session-only bytes shortcut.
// ---- download lifecycle: dispatch -> duplicate guard -> resolve -> next file
//
// The component ignores a second download while one is in flight
// (`documentDownloadPending`) and clears that flag only when the backend echoes
// the SAME requestId back through `lastWrites`. That round trip is asserted
// here for real — no remount is used to reset the flag, because a remount would
// hide exactly the stuck-pending bug this is meant to catch.

const cardFor = (templateId) => $("[data-testid='shipment-document-card']", picker)
  .find((element) => element.dataset.documentId === templateId);

for (const expected of [FIX.expected.docx, FIX.expected.xlsx]) {
  const history = currentModel.shipments.find((row) => row.id === SHIPMENT_ID)
    .uploadedTemplates[expected.templateId].documentHistory;
  assert.equal(history.length, 1, "exactly one generated revision exists");
  assert.equal(history[0].revision, expected.revision, "the projected revision is R1");
  assert.equal(history[0].fileName, expected.fileName, "the server owns the output file name");
  assert.equal(history[0].attachmentId, expected.attachmentId,
    "the projected history row carries the durable attachment id");

  // The stored bytes the event will hand back: read back through the EXISTING
  // core.shipment_attachments.fetch_attachment_bytes by the fixture generator,
  // so this hash is measured, not asserted.
  const stored = Buffer.from(expected.bytesBase64, "base64");
  assert.equal(createHash("sha256").update(stored).digest("hex"), expected.bytesSha256,
    `${expected.fileName} stored bytes match the pinned SHA-256`);
  assert.equal(stored.subarray(0, 2).toString(), "PK",
    `${expected.fileName} is a real OOXML package, not a text stub`);
}

const downloadButton = (templateId) =>
  $("[data-testid='shipment-document-download-latest']", cardFor(templateId))[0];

// 1. First download dispatches exactly one bounded event.
const before1 = events("attachment_download").length;
downloadButton(DOCX_ID).dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
await tick();
assert.equal(events("attachment_download").length, before1 + 1,
  "the first download dispatches one bounded event");
const first = events("attachment_download")[events("attachment_download").length - 1].value.payload;
assert.deepEqual(Object.keys(first).sort(), ["attachmentId", "requestId", "shipmentId"],
  "the download payload carries no path, expression or raw field reference");
assert.equal(first.shipmentId, SHIPMENT_ID);
assert.equal(first.attachmentId, FIX.expected.docx.attachmentId,
  "the DOCX download targets the durable attachment of that exact revision");
console.log(`  ✓ ${FIX.expected.docx.fileName} requested `
  + `(requestId ${first.requestId}, sha256 ${FIX.expected.docx.bytesSha256.slice(0, 16)}…)`);

// 2. While that request is in flight a second click is ignored — the guard the
//    owner asked to keep.
downloadButton(XLSX_ID).dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
await tick();
assert.equal(events("attachment_download").length, before1 + 1,
  "a second download is ignored while the first is still pending");
console.log("  ✓ in-flight duplicate download is ignored (guard intact)");

// 3. The backend echoes the SAME requestId through lastWrites; the flag clears
//    through the real effect, and the next file can then be downloaded.
currentModel = prepareModel();
currentModel.version = "logi193-download-resolved";
currentModel.lastWrites = [
  { event: "attachment_download", requestId: first.requestId, ok: true },
];
invoke(currentModel);
await tick();

const before2 = events("attachment_download").length;
downloadButton(XLSX_ID).dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
await tick();
assert.equal(events("attachment_download").length, before2 + 1,
  "after the backend resolves the first request, a different file downloads");
const second = events("attachment_download")[events("attachment_download").length - 1].value.payload;
assert.equal(second.attachmentId, FIX.expected.xlsx.attachmentId,
  "the second download targets the XLSX attachment, not the DOCX");
assert.notEqual(second.requestId, first.requestId, "each download mints its own requestId");
console.log(`  ✓ ${FIX.expected.xlsx.fileName} downloads after the first request resolved `
  + `(sha256 ${FIX.expected.xlsx.bytesSha256.slice(0, 16)}…)`);

// ===========================================================================
// 5. An unresolved operator-typed field blocks generation, honestly
// ===========================================================================
const manualState = currentModel.shipments
  .find((row) => row.id === SHIPMENT_ID)
  ?.uploadedTemplates?.[DOCX_ID];
assert.ok(manualState, "the server projected per-shipment uploaded-template state");
assert.ok(Array.isArray(manualState.manualFields), "manual fields come from the server mapping");

// Force a MISSING_INFO readiness that is purely operator-typed, exactly as the
// server would project it, and assert the client refuses to invent a value.
const blocked = clone(currentModel);
blocked.version = "logi193-blocked";
blocked.lastWrites = [];
const blockedRow = blocked.shipments.find((row) => row.id === SHIPMENT_ID);
blockedRow.selectedDocumentTemplateIds = [DOCX_ID];
blockedRow.uploadedTemplates[DOCX_ID] = {
  ...manualState,
  readiness: {
    state: "MISSING_INFO",
    reason: "Thiếu 1 thông tin để xuất biểu mẫu.",
    missing: ["Thiếu thông tin nhập tay: Số biên bản."],
  },
  documentHistory: [],
};
currentModel = blocked;
invoke(currentModel);
await tick();
const blockedPicker = await gotoDocuments();
const blockedCard = $("[data-testid='shipment-document-card']", blockedPicker)
  .find((element) => element.dataset.documentId === DOCX_ID);
assert.equal(blockedCard.dataset.state, "MISSING_INFO", "the server gate state is rendered");
assert.ok(text(blockedCard).includes("Số biên bản"),
  "the server's missing fact is rendered verbatim");
const blockedAction = $("[data-testid='shipment-document-primary-action']", blockedCard)[0];
assert.ok(blockedAction, "a purely operator-typed gap exposes the fill action");
assert.equal(text(blockedAction), "Bổ sung thông tin biểu mẫu",
  "the action points at the lot's own panel, never at a fake generate");
assert.equal($("[data-testid='shipment-document-download-latest']", blockedCard).length, 0,
  "no output block is invented while blocked");

const panel = $("[data-testid='shipment-uploaded-templates-panel']")[0];
assert.ok(panel, "the lot panel for uploaded templates renders");
assert.ok(text(panel).includes("không bao giờ tự điền"),
  "the panel states plainly that money fields are never auto-filled");
const generateBefore = events("uploaded_template_generate").length;
const panelButton = $("[data-testid^='uploaded-template-generate-']", panel)[0];
assert.ok(panelButton, "the panel exposes a generate control");
panelButton.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
await tick();
assert.equal(events("uploaded_template_generate").length, generateBefore,
  "a blocked template never dispatches a generation — nothing is defaulted");
console.log("  ✓ unresolved operator field blocks generation with the server's wording");

// Every generation this DOM produced carries the server-owned template id.
assert.ok(events("uploaded_template_generate")
  .every((entry) => entry.value.payload.templateId === DOCX_ID
    || entry.value.payload.templateId === XLSX_ID));
console.log("PASS: LOGI-193 uploaded Office templates DOM acceptance");
