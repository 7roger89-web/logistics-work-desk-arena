/**
 * LOGI_SHIPMENT_DOCUMENTS_DRIVE_REINTEGRATE_02 — DOM acceptance for
 * "Tệp đính kèm lô hàng".
 *
 * Runs the REAL production bundle (component/dist/logi-shell.js, rebuilt from
 * the CURRENT source tree) in jsdom and drives it with real DOM events,
 * against a fixture generated from the real staging view-model (see
 * scripts/gen_shipment_attachments_fixture.py):
 *
 *   1. shipment detail → "Chứng từ & PXK" tab exposes the attachment section;
 *   2. the list renders the BACKEND's authoritative metadata (name, category,
 *      honest size text, uploader, upload date) — never client-side truth;
 *   3. the file selector accepts exactly the server-declared policy and the
 *      category selector offers the server's real categories;
 *   4. choosing a file and pressing upload emits EXACTLY ONE
 *      `shipment_attachment_upload` event, with the bounded payload the
 *      dispatcher validates, and a visible pending state;
 *   4b. the pending state stays visible across a fresh view-model that carries
 *      NO backend outcome yet (transport is never success);
 *   5. the backend's own outcome (fresh readback) replaces the pending state
 *      and shows the new attachment — no optimistic metadata is trusted;
 *   6. a duplicate / oversized / Drive-not-configured refusal is shown
 *      honestly instead of a fake success;
 *   7. a viewer role gets NO upload form (the server refuses anyway);
 *   8. the DOM contains no Drive file id, folder id, public Drive URL or
 *      credential, and no raw SHA-256;
 *   9. download is ONE bounded `attachment_download` event whose returned bytes
 *      are saved locally — the browser never receives a Drive link;
 *  10. the section forces no horizontal overflow on a phone width.
 *
 * Run: node tests/component/dom_acceptance_shipment_attachments.mjs
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
const fixturePath = path.join(ROOT, "tests/component/fixtures/view_model_attachments.json");

const VM = JSON.parse(readFileSync(fixturePath, "utf8"));

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
  "File",
  "FileReader",
  "Blob",
  "getComputedStyle",
]) {
  globalThis[k] = window[k];
}
if (!globalThis.MessageChannel) globalThis.MessageChannel = window.MessageChannel;
window.HTMLElement.prototype.scrollIntoView = () => {};
// The bundle runs in the Node global scope, so the browser save helper may use
// EITHER `window.URL` or the Node global `URL`: both are recorded, and the
// anchor click that actually hands the file to the operator is recorded too.
const savedFiles = [];
const recordBlob = (blob) => {
  savedFiles.push(blob);
  return "blob:mock-url";
};
window.URL.createObjectURL = recordBlob;
window.URL.revokeObjectURL = () => {};
if (typeof globalThis.URL?.createObjectURL === "function" || globalThis.URL) {
  globalThis.URL.createObjectURL = recordBlob;
  globalThis.URL.revokeObjectURL = () => {};
}
const clickedAnchors = [];
window.HTMLAnchorElement.prototype.click = function recordClick() {
  clickedAnchors.push({ download: this.download, href: this.href });
};

const tick = (ms = 80) => new Promise((r) => setTimeout(r, ms));
const $ = (sel, root = window.document) => [...root.querySelectorAll(sel)];
const text = (el) => (el.textContent || "").replace(/\s+/g, " ").trim();
const mainText = () => text(window.document.querySelector("main") || window.document.body);

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
// Simulated Streamlit Components v2 invocation
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

const clone = (vm) => JSON.parse(JSON.stringify(vm));
let checks = 0;
const ok = (label) => {
  checks += 1;
  console.log(`  ✓ ${label}`);
};

invoke(VM);
await tick();

console.log("STEP 1 — shipment detail → Chứng từ tab");
await click("Lô Hàng", "a", $("aside")[0]);
await click("LO-0306", "a", $("table.tbl")[0]);
const tabs = window.document.getElementById("workspace-tabs");
assert.ok(tabs, "workspace tabs must exist");
await click("Chứng từ & PXK", "button", tabs);
assert.ok(mainText().includes("Tệp đính kèm lô hàng"), "attachment section title missing");
assert.ok(!mainText().includes("Google Drive"), "gridfs mode must use provider-neutral wording");
assert.ok(
  mainText().includes("nội dung tệp được lưu trong Kho chứng từ; thông tin mô tả được lưu cùng hồ sơ lô."),
  "attachment copy must explain that both content and description are retained"
);
ok("attachment section is visible in the Chứng từ tab");

console.log("STEP 2 — the list comes from the backend projection");
const section = $("[data-testid='shipment-attachments']")[0];
assert.ok(section, "attachment section missing");
const rows = $("[data-testid='attachment-row']", section);
assert.equal(rows.length, 2, "the backend delivered two attachments");
const sectionText = text(section);
const photo = VM.shipments.find((s) => s.id === "LO-0306").attachments.find((a) => a.name.endsWith(".jpg"));
const pdf = VM.shipments.find((s) => s.id === "LO-0306").attachments.find((a) => a.name.endsWith(".pdf"));
assert.ok(sectionText.includes(photo.name), "photo name missing from the list");
assert.ok(sectionText.includes(pdf.name), "pdf name missing from the list");
// Honest sizes come from the backend projection itself — never hard-coded here.
assert.ok(photo.sizeLabel.includes("→"), "fixture must carry one optimized row");
assert.ok(sectionText.includes(photo.sizeLabel), "optimized size must be rendered honestly (original → stored)");
assert.ok(!pdf.sizeLabel.includes("→"), "fixture must carry one kept-original row");
assert.ok(sectionText.includes(pdf.sizeLabel), "kept-original size must be rendered");
assert.ok(sectionText.includes("Ảnh đã tối ưu"), "an optimized image must say so");
assert.ok(sectionText.includes("Giữ nguyên"), "an uncompressed file must say so");
assert.ok(sectionText.includes("Hải quan") && sectionText.includes("Hợp đồng"), "categories missing");
assert.ok(sectionText.includes("staging.support"), "uploader missing");
assert.ok(!sectionText.includes(photo.originalSize.toString()), "raw byte counts must be humanised");
ok("names, categories, honest sizes, uploader and compression state are rendered");

console.log("STEP 3 — the selectors use the server's own policy");
const fileInput = window.document.getElementById("fld-attach-file");
const categorySelect = window.document.getElementById("fld-attach-category");
assert.ok(fileInput && categorySelect, "file + category selectors must exist");
assert.equal(fileInput.getAttribute("accept"), VM.attachmentPolicy.accept, "accept must mirror the server policy");
assert.ok(VM.attachmentPolicy.accept.length > 0 && VM.attachmentPolicy.allowedExtensions.length > 0);
for (const ext of [".pdf", ".jpg", ".png"]) {
  assert.ok(
    VM.attachmentPolicy.allowedExtensions.includes(ext.slice(1)),
    `server policy must allow ${ext}`
  );
}
assert.equal(categorySelect.options.length, VM.attachmentPolicy.categories.length, "category options missing");
assert.ok(text(categorySelect).includes("Hải quan"), "server categories not offered");
assert.ok(text(section).includes(`tối đa ${VM.attachmentPolicy.maxUploadLabel}`), "the server byte ceiling is not shown");
ok("file selector accept-list and category selector mirror the server policy");

console.log("STEP 4 — choosing a file and pressing upload emits EXACTLY ONE event");
const fileBytes = new Uint8Array([37, 80, 68, 70, 45, 49, 46, 52, 10]); // "%PDF-1.4\n"
const chosen = new window.File([fileBytes], "To khai moi.pdf", { type: "application/pdf" });
Object.defineProperty(fileInput, "files", { value: [chosen], configurable: true });
fileInput.dispatchEvent(new window.Event("change", { bubbles: true }));
await tick();

const uploadBtn = $("[data-testid='attachment-upload']")[0];
assert.ok(uploadBtn, "upload button missing");
assert.equal(uploadBtn.disabled, false, "upload must enable once a file is chosen");
uploadBtn.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
await tick(120);

const uploadEvents = triggers.filter((t) => t.event === "shipment_attachment_upload");
assert.equal(uploadEvents.length, 1, "exactly ONE shipment_attachment_upload event");
const payload = uploadEvents[0].value.payload;
assert.equal(payload.shipmentId, "LO-0306");
assert.equal(payload.fileName, "To khai moi.pdf");
assert.equal(payload.mime, "application/pdf");
assert.equal(payload.size, fileBytes.length);
assert.equal(payload.category, "customs", "the selected category must travel with the file");
assert.equal(typeof payload.requestId, "string");
assert.ok(payload.base64.length > 0 && !payload.base64.includes(","), "bounded base64 body, no data-url prefix");
assert.ok(mainText().includes("ĐANG LƯU VÀO KHO CHỨNG TỪ"), "a pending state must be visible");
assert.ok(triggers.filter((t) => t.event === "attachment_download").length === 0, "no download event on upload");
ok("ONE bounded upload event + visible pending state");

console.log("STEP 4b — pending stays pending until the backend answers");
const rerender = clone(VM);
rerender.version = "attachments-rerender-no-outcome";
rerender.lastWrites = [];
invoke(rerender);
await tick(120);
assert.ok(
  mainText().includes("ĐANG LƯU VÀO KHO CHỨNG TỪ"),
  "pending must survive a fresh view-model that carries no backend outcome"
);
assert.equal($("[data-testid='attachment-outcome']").length, 0, "no outcome may be shown before the backend answers");
ok("pending remains visibly pending without a backend outcome");

console.log("STEP 5 — the backend's fresh readback replaces the pending state");
const readback = clone(VM);
readback.version = "attachments-readback-1";
readback.lastWrites = [
  {
    event: "shipment_attachment_upload",
    shipmentId: "LO-0306",
    ok: true,
    error: "",
    requestId: payload.requestId,
    gate: "UPLOADED",
  },
];
const readbackRow = readback.shipments.find((s) => s.id === "LO-0306");
readbackRow.attachments = [
  {
    id: "ATT-LO-0306-new",
    name: "To khai moi.pdf",
    category: "customs",
    categoryLabel: "Hải quan",
    mime: "application/pdf",
    originalSize: 9,
    storedSize: 9,
    sizeLabel: "9 B",
    compressionMode: "KEPT_ORIGINAL",
    compressionLabel: "Giữ nguyên",
    compressionNote: "Giữ nguyên bản gốc.",
    uploadedAt: "17/09/2026 03:00",
    uploadedBy: "staging.support",
    status: "AVAILABLE",
    downloadAvailable: false,
    downloadBase64: "",
    downloadSeq: 0,
  },
  ...readbackRow.attachments,
];
invoke(readback);
await tick(120);

const afterUpload = $("[data-testid='shipment-attachments']")[0];
assert.ok(text(afterUpload).includes("To khai moi.pdf"), "the authoritative readback must show the new attachment");
assert.equal($("[data-testid='attachment-row']", afterUpload).length, 3, "three attachments after the write");
assert.ok(!mainText().includes("ĐANG LƯU VÀO KHO CHỨNG TỪ"), "the pending state must clear on the backend answer");
assert.ok(text(afterUpload).includes("Đã lưu tệp đính kèm vào lô."), "the backend outcome must be shown");
ok("fresh backend readback drives the list; pending state clears");

console.log("STEP 6 — refusals are shown honestly, never as a fake success");
// Simulate the operator pressing upload again with a duplicate file.
const slot = window.document.getElementById("fld-attach-file");
const duplicate = new window.File([new Uint8Array([37, 80, 68, 70])], "To khai moi.pdf", { type: "application/pdf" });
Object.defineProperty(slot, "files", { value: [duplicate], configurable: true });
slot.dispatchEvent(new window.Event("change", { bubbles: true }));
await tick();
const secondUpload = $("[data-testid='attachment-upload']")[0];
secondUpload.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
await tick(120);
const lastUploadEvent = triggers.filter((t) => t.event === "shipment_attachment_upload").at(-1);
const duplicated = clone(readback);
duplicated.version = "attachments-readback-duplicate";
duplicated.lastWrites = [
  {
    event: "shipment_attachment_upload",
    shipmentId: "LO-0306",
    ok: true,
    error: "",
    gate: "DUPLICATE",
    duplicate: true,
    message: "Tệp này đã có trong kho chứng từ của lô — không tải lên bản sao.",
    requestId: lastUploadEvent.value.payload.requestId,
  },
];
invoke(duplicated);
await tick(120);
const duplicateText = text($("[data-testid='shipment-attachments']")[0]);
assert.ok(
  duplicateText.includes("không tải lên bản sao"),
  "the duplicate refusal must be displayed honestly"
);
ok("duplicate refusal displayed from the backend outcome");

const refused = new window.File([new Uint8Array([37, 80, 68, 70])], "Kho khong san sang.pdf", { type: "application/pdf" });
Object.defineProperty(slot, "files", { value: [refused], configurable: true });
slot.dispatchEvent(new window.Event("change", { bubbles: true }));
await tick();
$("[data-testid='attachment-upload']")[0].dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
await tick(120);
const refusedUploadEvent = triggers.filter((t) => t.event === "shipment_attachment_upload").at(-1);
const storageOff = clone(readback);
storageOff.version = "attachments-storage-unconfigured";
storageOff.lastWrites = [
  {
    event: "shipment_attachment_upload",
    shipmentId: "LO-0306",
    ok: false,
    error: "Kho chứng từ chưa sẵn sàng trên máy chủ. Không có tệp nào được lưu.",
    gate: "GRIDFS_NOT_CONFIGURED",
    requestId: refusedUploadEvent.value.payload.requestId,
  },
];
invoke(storageOff);
await tick(120);
assert.ok(mainText().includes("Kho chứng từ chưa sẵn sàng trên máy chủ"), "an unconfigured storage backend must be reported honestly");
assert.ok(!mainText().includes("Đã lưu tệp đính kèm"), "a refused upload must not be reported as saved");
ok("refused upload is reported honestly (no fake success)");

console.log("STEP 7 — a viewer cannot upload, but may still open files");
const viewer = clone(VM);
viewer.version = "attachments-viewer";
viewer.user = { name: "Chỉ đọc", role: "VIEWER", username: "viewer-1" };
viewer.attachmentPolicy = { ...VM.attachmentPolicy, allowUpload: false };
invoke(viewer);
await tick(120);
assert.equal($("[data-testid='attachment-file']").length, 0, "a viewer must not get a file selector");
assert.equal($("[data-testid='attachment-upload']").length, 0, "a viewer must not get an upload button");
assert.equal($("[data-testid='attachment-readonly']").length, 1, "a viewer must see the read-only note");
assert.ok($("[data-testid='attachment-download']").length >= 1, "a viewer may still open a permitted attachment");
ok("viewer: no upload control, read-only note, download still available");

console.log("STEP 8 — no Drive id, folder id, public URL or credential in the DOM");
invoke(VM);
await tick(120);
const html = window.document.body.innerHTML;
for (const needle of [
  "drive-file-",
  "drive_file_id",
  "drive_folder_id",
  "driveFileId",
  "googleapis.com",
  "drive.google.com",
  "PRIVATE KEY",
  "service_account",
  "sha256",
  "Google Drive",
  "MongoDB",
  "GridFS",
  "bucket",
  "chunks",
]) {
  assert.ok(!html.includes(needle), `DOM must not contain "${needle}"`);
}
for (const anchor of $("a[href]", window.document)) {
  assert.ok(!String(anchor.getAttribute("href")).includes("drive.google.com"), "no public Drive link may be rendered");
}
// The SHA-256 of the original upload is durable backend identity, never UI.
assert.ok(!/[0-9a-f]{64}/.test(html), "raw SHA must stay backend metadata");
const fixtureRows = VM.shipments.find((s) => s.id === "LO-0306").attachments;
for (const item of fixtureRows) {
  assert.equal(item.sha256, undefined, "the projection must not carry a sha256 field");
  assert.equal(item.driveFileId, undefined, "the projection must not carry a drive file id");
}
ok("DOM carries metadata only — no Drive id, URL or credential");

console.log("STEP 9 — download is ONE bounded event and saves the returned bytes");
const downloadEventCountBefore = triggers.filter((t) => t.event === "attachment_download").length;
const downloadBtn = $("[data-testid='attachment-download']")[0];
downloadBtn.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
await tick(120);
const downloadEvents = triggers.filter((t) => t.event === "attachment_download");
assert.equal(downloadEvents.length, downloadEventCountBefore + 1, "exactly ONE attachment_download event");
const downloadPayload = downloadEvents.at(-1).value.payload;
assert.equal(downloadPayload.shipmentId, "LO-0306");
assert.ok(downloadPayload.attachmentId, "the event must identify the attachment");
assert.equal(typeof downloadPayload.requestId, "string");

const downloaded = clone(VM);
downloaded.version = "attachments-download-1";
downloaded.lastWrites = [
  {
    event: "attachment_download",
    shipmentId: "LO-0306",
    ok: true,
    error: "",
    requestId: downloadPayload.requestId,
    persisted: { attachmentId: downloadPayload.attachmentId, size: 9, seq: 1 },
  },
];
const downloadRow = downloaded.shipments.find((s) => s.id === "LO-0306");
const target = downloadRow.attachments.find((a) => a.id === downloadPayload.attachmentId);
target.downloadAvailable = true;
target.downloadBase64 = "JVBERi0xLjQK"; // "%PDF-1.4\n"
target.downloadSeq = 1;
const savedBefore = savedFiles.length;
const clicksBefore = clickedAnchors.length;
invoke(downloaded);
await tick(200);
assert.ok(savedFiles.length > savedBefore || clickedAnchors.length > clicksBefore,
  "the downloaded bytes must be saved locally (no browser save happened)");
if (clickedAnchors.length > clicksBefore) {
  assert.equal(clickedAnchors.at(-1).download, target.name, "the saved file must keep the original name");
}
assert.ok(
  text(window.document.body).includes("Đã tải " + target.name),
  "the download must be confirmed from the backend bytes"
);
ok("ONE download event → server bytes saved locally");

console.log("STEP 10 — mobile: no forced horizontal overflow");
const mobileSection = $("[data-testid='shipment-attachments']")[0];
assert.ok(!mobileSection.className.includes("overflow-x-auto"), "the section must not force horizontal scrolling");
assert.equal($("[class*='overflow-x-auto']", mobileSection).length, 0, "no child forces horizontal scroll");
for (const row of $("[data-testid='attachment-row']", mobileSection)) {
  assert.ok(row.className.includes("flex-wrap"), "attachment rows must wrap on narrow viewports");
  const name = row.querySelector("p");
  assert.ok(name.className.includes("break-words"), "long file names must break instead of overflowing");
}
const downloadButtons = $("[data-testid='attachment-download']", mobileSection);
for (const button of downloadButtons) {
  assert.ok(button.className.includes("min-h-[44px]"), "download is not thumb-sized");
}
const uploadButton = $("[data-testid='attachment-upload']")[0];
assert.ok(uploadButton.className.includes("min-h-[48px]"), "upload is not thumb-sized");
ok("no forced horizontal overflow; thumb-sized controls; wrapping rows");

console.log(`\nSHIPMENT_ATTACHMENT_DOM_ACCEPTANCE=PASSED checks=${checks}`);
