/**
 * LOGI_TRADE_DOCUMENT_SHIPMENT_REVIEW_RUN3_01 — DOM acceptance for the
 * read-only "KIỂM TRA CHỨNG TỪ" review surface inside the shipment
 * "Chứng từ / Tệp đính kèm" section.
 *
 * Runs the REAL production bundle (component/dist/logi-shell.js, rebuilt from
 * the CURRENT source tree) in jsdom and drives it with real DOM events,
 * against a fixture generated from the real staging view-model by
 * scripts/gen_shipment_document_review_fixture.py — whose review result was
 * produced by the REAL Run 3 orchestration (attachment metadata → server-side
 * byte read → Run 2 located text → Run 1 cross-check → Run 3 projection).
 *
 *   1. shipment detail → "Quy trình & Chứng từ" exposes the review surface;
 *   2. PDF/XLSX rows carry a large usable checkbox; JPG/DOCX rows stay VISIBLE
 *      with their honest non-selectable wording and are never implied damaged;
 *   3. the selected count is visible and the button is disabled at zero;
 *   4. pressing KIỂM TRA CHỨNG TƯ emits EXACTLY ONE `shipment_document_review`
 *      event whose payload carries ONLY { shipmentId, attachmentIds,
 *      requestId } — no bytes, no base64, no storage/GridFS/Drive id, no SHA;
 *   5. a double click cannot start a second request while one is pending, and
 *      the pending state survives a view-model with no matching outcome;
 *   6. a STALE requestId can never settle the current pending request;
 *   7. the settled result renders count chips, CẦN XEM before THAM KHẢO before
 *      ĐÃ KHỚP, every CONFLICT source side, and the explicit "no winner" line;
 *   8. the result always states it is NOT written into the shipment record;
 *   9. a review belonging to another shipment is never projected here;
 *  10. changing shipment clears the stale local selection;
 *  11. the DOM holds no raw SHA-256, storage id, GridFS id or base64 body;
 *  12. mobile-first: no forced horizontal overflow, thumb-sized controls.
 *
 * Run: node tests/component/dom_acceptance_shipment_document_review.mjs
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
const FIX = RAW.fixture;
const SHIPMENT_ID = FIX.shipmentId;
const OTHER_SHIPMENT_ID = FIX.otherShipmentId;

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
window.URL.createObjectURL = () => "blob:mock-url";
window.URL.revokeObjectURL = () => {};
if (globalThis.URL) {
  globalThis.URL.createObjectURL = () => "blob:mock-url";
  globalThis.URL.revokeObjectURL = () => {};
}
window.HTMLAnchorElement.prototype.click = function recordClick() {};

const tick = (ms = 80) => new Promise((r) => setTimeout(r, ms));
const $ = (sel, root = window.document) => [...root.querySelectorAll(sel)];
const text = (el) => (el?.textContent || "").replace(/\s+/g, " ").trim();
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

const reviewEvents = () => triggers.filter((t) => t.event === "shipment_document_review");

function invoke(data) {
  return mountRef.current({
    name: "logi_shell",
    data,
    parentElement: host,
    setTriggerValue: (event, value) => triggers.push({ event, value }),
  });
}

const clone = (vm) => JSON.parse(JSON.stringify(vm));

/** The fixture ships WITH a completed review; the UI flow starts without one. */
function freshModel() {
  const next = clone(RAW);
  next.shipmentDocumentReview = null;
  next.lastWrites = [];
  return next;
}

let currentModel = freshModel();

/** Deliver the backend's authoritative outcome for ONE requestId. */
function settleReview(requestId, { ok = true, review = null, error = "" } = {}) {
  currentModel = clone(currentModel);
  currentModel.version = `review-outcome-${requestId}`;
  currentModel.lastWrites = [
    {
      event: "shipment_document_review",
      shipmentId: SHIPMENT_ID,
      ok,
      error,
      requestId,
      gate: ok ? "REVIEWED" : "REVIEW_REFUSED",
      review: review ?? undefined,
    },
  ];
  if (ok && review) {
    currentModel.shipmentDocumentReview = { ...review, requestId, shipmentId: SHIPMENT_ID };
  }
  invoke(currentModel);
}

/**
 * Every model swap re-renders the component from scratch, so the router is back
 * at its start. Each later step therefore re-walks to the shipment's Chứng từ
 * tab and re-reads the DOM instead of trusting a node captured earlier.
 */
async function gotoReviewTab() {
  await click("Lô Hàng", "a", $("aside")[0]);
  await click("Tất cả thời gian", "button", $("[data-testid='shipment-period-controls']")[0]);
  await click(SHIPMENT_ID, "a", $("table.tbl")[0]);
  const workspaceTabs = window.document.getElementById("workspace-tabs");
  assert.ok(workspaceTabs, "workspace tabs must exist");
  await click("Quy trình & Chứng từ", "button", workspaceTabs);
  const shell = $("[data-testid='shipment-attachments']")[0];
  assert.ok(shell, "attachment section missing after navigation");
  const reviewPanel = $("[data-testid='document-review']", shell)[0];
  assert.ok(reviewPanel, "review surface missing after navigation");
  return { shell, reviewPanel };
}

const mod = await import(bundlePath);
assert.equal(typeof mod.default, "function", "bundle must default-export the mount function");
mountRef.current = mod.default;

let checks = 0;
const ok = (label) => {
  checks += 1;
  console.log(`  ✓ ${label}`);
};

invoke(currentModel);
await tick();

// ===========================================================================
console.log("STEP 1 — shipment detail → Chứng từ tab exposes the review surface");
// ===========================================================================
await click("Lô Hàng", "a", $("aside")[0]);
await click("Tất cả thời gian", "button", $("[data-testid='shipment-period-controls']")[0]);
await click(SHIPMENT_ID, "a", $("table.tbl")[0]);
const tabs = window.document.getElementById("workspace-tabs");
assert.ok(tabs, "workspace tabs must exist");
await click("Quy trình & Chứng từ", "button", tabs);

const section = $("[data-testid='shipment-attachments']")[0];
assert.ok(section, "attachment section missing");
assert.ok(mainText().includes("Tệp đính kèm lô hàng"), "attachment section title missing");
const panel = $("[data-testid='document-review']")[0];
assert.ok(panel, "the read-only review surface must live inside the attachment section");
assert.ok(section.contains(panel), "the review surface must not escape the attachment surface");
assert.ok(text(panel).includes("Kiểm tra chứng từ"), "review surface title missing");
ok("the review surface is one bounded area inside the existing attachment surface");

// ===========================================================================
console.log("STEP 2 — selectable PDF/XLSX vs honest non-selectable JPG/DOCX");
// ===========================================================================
const rows = $("[data-testid='attachment-row']", section);
assert.equal(rows.length, 5, "the backend delivered five attachments");

const rowsByName = new Map();
for (const row of rows) rowsByName.set(text(row.querySelector("p")), row);

for (const name of ["commercial_invoice.xlsx", "packing_list.xlsx", "bill_of_lading.pdf"]) {
  const row = rowsByName.get(name);
  assert.ok(row, `${name} row missing`);
  assert.equal(row.getAttribute("data-review-selectable"), "true", `${name} must be selectable`);
  const toggle = $("[data-testid='attachment-review-toggle']", row)[0];
  assert.ok(toggle, `${name} must offer a selection affordance`);
  const box = toggle.querySelector("input[type='checkbox']");
  assert.ok(box, `${name} checkbox missing`);
  // Mobile-first: a real finger target, not a 13px browser default.
  assert.ok(box.className.includes("h-6") && box.className.includes("w-6"),
    `${name} checkbox must be a large tap target`);
  assert.ok(toggle.className.includes("min-h-[44px]"), `${name} toggle must be thumb-sized`);
  assert.ok(box.getAttribute("aria-label")?.includes(name), `${name} checkbox needs an accessible label`);
}

for (const [name, expected] of [
  ["To khai hai quan.jpg", "Cần OCR — bước này chưa chạy OCR"],
  ["Hop dong van chuyen.docx", "Chưa hỗ trợ kiểm tra tự động ở bước này"],
]) {
  const row = rowsByName.get(name);
  assert.ok(row, `${name} must remain VISIBLE`);
  assert.equal(row.getAttribute("data-review-selectable"), "false", `${name} must not be selectable`);
  assert.equal($("[data-testid='attachment-review-toggle']", row).length, 0,
    `${name} must not offer a checkbox`);
  const note = $("[data-testid='attachment-review-note']", row)[0];
  assert.ok(note, `${name} must state why it is not selectable`);
  assert.equal(text(note), expected, `${name} wording must be the server's honest reason`);
  // Still a normal, downloadable attachment — never implied to be damaged.
  assert.ok($("[data-testid='attachment-download']", row)[0], `${name} must still be downloadable`);
  assert.ok(!text(row).toLowerCase().includes("hỏng"), `${name} must not be called damaged`);
  assert.ok(!text(row).toLowerCase().includes("lỗi tệp"), `${name} must not be called broken`);
}
ok("PDF/XLSX are selectable; JPG/DOCX stay visible with honest, non-alarming wording");

// ===========================================================================
console.log("STEP 3 — selected count is visible; the button is disabled at zero");
// ===========================================================================
const runButton = $("[data-testid='document-review-run']", panel)[0];
assert.ok(runButton, "KIỂM TRA CHỨNG TỪ button missing");
assert.equal(text(runButton), "KIỂM TRA CHỨNG TỪ", "button wording must be exact");
assert.ok(runButton.disabled, "the button must be disabled before anything is selected");
assert.equal(text($("[data-testid='document-review-count']", panel)[0]), "Đã chọn 0 tệp");
assert.equal(reviewEvents().length, 0, "opening a shipment must NOT auto-run a review");
assert.ok(
  text(panel).includes("Kết quả chỉ để kiểm tra — chưa ghi vào hồ sơ lô hàng."),
  "the ephemeral disclaimer must always be visible"
);
ok("zero selection → disabled button, visible count, no auto-run");

// ===========================================================================
console.log("STEP 4 — selecting files updates the count and enables the action");
// ===========================================================================
async function toggleRow(name) {
  const row = rowsByName.get(name);
  const box = $("[data-testid='attachment-review-toggle'] input", row)[0];
  box.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
  await tick();
}

await toggleRow("commercial_invoice.xlsx");
assert.equal(text($("[data-testid='document-review-count']", panel)[0]), "Đã chọn 1 tệp");
assert.ok(!runButton.disabled, "one selection must enable the action");
await toggleRow("packing_list.xlsx");
await toggleRow("bill_of_lading.pdf");
assert.equal(text($("[data-testid='document-review-count']", panel)[0]), "Đã chọn 3 tệp");

// Un-ticking really removes the file from the selection.
await toggleRow("packing_list.xlsx");
assert.equal(text($("[data-testid='document-review-count']", panel)[0]), "Đã chọn 2 tệp");
await toggleRow("packing_list.xlsx");
assert.equal(text($("[data-testid='document-review-count']", panel)[0]), "Đã chọn 3 tệp");
ok("the selection count tracks the operator's real choices");

// ===========================================================================
console.log("STEP 5 — ONE bounded event carrying ONLY identifiers");
// ===========================================================================
runButton.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
await tick();

const events = reviewEvents();
assert.equal(events.length, 1, "exactly ONE shipment_document_review event");
const sent = events[0].value;
assert.equal(sent.event, "shipment_document_review");
const payload = sent.payload;
assert.deepEqual(
  Object.keys(payload).sort(),
  ["attachmentIds", "requestId", "shipmentId"],
  "the browser payload must carry ONLY bounded identifiers"
);
assert.equal(payload.shipmentId, SHIPMENT_ID);
assert.deepEqual(payload.attachmentIds.sort(), FIX.selectedIds.slice().sort());
assert.ok(payload.requestId && typeof payload.requestId === "string");

// Hard privacy bound on what the browser is willing to send.
const payloadJson = JSON.stringify(payload);
assert.ok(!/[A-Za-z0-9+/]{200,}={0,2}/.test(payloadJson), "no base64 body may be sent");
assert.ok(!/[0-9a-f]{64}/.test(payloadJson), "no raw SHA-256 may be sent");
for (const forbidden of ["storage_file_id", "storageFileId", "driveFileId", "gridfs", "base64", "bytes"]) {
  assert.ok(!payloadJson.toLowerCase().includes(forbidden.toLowerCase()), `${forbidden} must never be sent`);
}
ok("ONE event, identifiers only — no bytes, base64, storage id or SHA");

// ===========================================================================
console.log("STEP 6 — pending state, double-submit guard, stale requestId");
// ===========================================================================
const pendingButton = $("[data-testid='document-review-run']", panel)[0];
assert.equal(text(pendingButton), "ĐANG KIỂM TRA…", "pending wording must be exact");
assert.ok(pendingButton.disabled, "the pending button must be disabled against a double click");

// A double click while pending must NOT produce a second request.
pendingButton.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
pendingButton.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
await tick();
assert.equal(reviewEvents().length, 1, "a double click must not send a duplicate review request");

// A fresh view-model with NO matching outcome must not clear the pending state.
const noOutcome = clone(currentModel);
noOutcome.version = "still-no-outcome";
noOutcome.lastWrites = [];
invoke(noOutcome);
await tick();
assert.equal(text($("[data-testid='document-review-run']", panel)[0]), "ĐANG KIỂM TRA…",
  "transport is never success — the pending state must survive");
assert.equal($("[data-testid='document-review-result']", panel).length, 0,
  "no result may render before the backend answers");

// A STALE result from an earlier request can never settle this one.
const pendingRequestId = payload.requestId;
const stale = clone(currentModel);
stale.version = "stale-outcome";
stale.lastWrites = [
  { event: "shipment_document_review", shipmentId: SHIPMENT_ID, ok: true, error: "",
    requestId: "ATTREV-STALE-REQUEST", gate: "REVIEWED" },
];
invoke(stale);
await tick();
assert.equal(text($("[data-testid='document-review-run']", panel)[0]), "ĐANG KIỂM TRA…",
  "a stale requestId must not settle the current pending request");
assert.notEqual(pendingRequestId, "ATTREV-STALE-REQUEST");
ok("pending survives a missing outcome; a stale requestId cannot settle it");

// ===========================================================================
console.log("STEP 7 — the matching outcome settles and renders the review");
// ===========================================================================
settleReview(pendingRequestId, { ok: true, review: clone(RAW.shipmentDocumentReview) });
await tick(200);

assert.equal(text($("[data-testid='document-review-run']", panel)[0]), "KIỂM TRA CHỨNG TỪ",
  "the matching requestId must clear the pending state");
const result = $("[data-testid='document-review-result']", panel)[0];
assert.ok(result, "the review result must render");

// --- summary chips ---------------------------------------------------------
const chips = $("[data-testid='document-review-chip']", result);
assert.equal(chips.length, 5, "five status chips: Lệch / Chưa xác định / Thiếu / Chỉ một nguồn / Khớp");
// Each chip renders its count in the first <p> and its Vietnamese label in the
// second, so the count is read from the value element itself.
const chipValue = (chip) => Number(text(chip.querySelector("p")));
const chipByLabel = new Map(chips.map((c) => [c.getAttribute("data-status-label"), c]));
for (const [label, expected] of [
  ["Lệch", FIX.expectedStatusCounts.CONFLICT],
  ["Chưa xác định", FIX.expectedStatusCounts.UNKNOWN],
  ["Thiếu", FIX.expectedStatusCounts.MISSING],
  ["Chỉ một nguồn", FIX.expectedStatusCounts.SINGLE_SOURCE],
  ["Khớp", FIX.expectedStatusCounts.SAME],
]) {
  assert.ok(chipByLabel.has(label), `chip "${label}" missing`);
  assert.equal(chipValue(chipByLabel.get(label)), expected,
    `chip "${label}" must show ${expected}`);
}
assert.equal(
  chips.reduce((sum, chip) => sum + chipValue(chip), 0),
  FIX.expectedFacts,
  "the five chips must account for all 19 facts"
);
ok("five honest count chips, no score, no percentage");

// --- section ordering: CẦN XEM → THAM KHẢO → ĐÃ KHỚP ------------------------
const needSection = $("[data-testid='document-review-section-can-xem']", result)[0];
const refSection = $("[data-testid='document-review-section-tham-khao']", result)[0];
const sameSection = $("[data-testid='document-review-section-da-khop']", result)[0];
assert.ok(needSection && refSection && sameSection, "all three sections must render");
assert.equal(text(needSection.querySelector("h5")), "CẦN XEM");
assert.equal(text(refSection.querySelector("h5")), "THAM KHẢO");
assert.equal(text(sameSection.querySelector("h5")), "ĐÃ KHỚP");
const allFacts = $("[data-testid='document-review-fact']", result);
assert.equal(allFacts.length, FIX.expectedFacts, "all 19 facts must be listed");
const needFacts = $("[data-testid='document-review-fact']", needSection);
const sameFacts = $("[data-testid='document-review-fact']", sameSection);
assert.equal(needFacts.length,
  FIX.expectedStatusCounts.CONFLICT + FIX.expectedStatusCounts.UNKNOWN + FIX.expectedStatusCounts.MISSING);
assert.equal(sameFacts.length, FIX.expectedStatusCounts.SAME);
// CẦN XEM must come FIRST in document order.
assert.ok(
  allFacts.indexOf(needFacts[0]) < allFacts.indexOf(sameFacts[0]),
  "a CONFLICT/UNKNOWN/MISSING fact must be listed before any SAME fact"
);
const needOrder = needFacts.map((f) => f.getAttribute("data-status"));
assert.deepEqual(needOrder, ["CONFLICT", "UNKNOWN", "MISSING", "MISSING"],
  "inside CẦN XEM the order must be CONFLICT → UNKNOWN → MISSING");
ok("CẦN XEM (Lệch → Chưa xác định → Thiếu) before THAM KHẢO before ĐÃ KHỚP");

// --- the CONFLICT shows EVERY source side and picks no winner --------------
const conflict = needFacts[0];
assert.equal(conflict.getAttribute("data-field-key"), "package_count");
assert.ok(text(conflict).includes("Số kiện"), "the Vietnamese operator label must lead");
const sides = $("[data-testid='document-review-fact-side']", conflict);
assert.equal(sides.length, 3, "a CONFLICT must show all three source sides");
const sideText = sides.map((side) => text(side));
assert.ok(sideText.some((t) => t.includes("120 CTNS")), "the invoice side must be visible");
assert.ok(sideText.some((t) => t.includes("120 CARTONS")), "the packing list side must be visible");
assert.ok(sideText.some((t) => t.includes("118 CARTONS")), "the B/L side must be visible");
assert.ok(sideText.some((t) => t.includes("Trang ")), "a PDF side must cite its page");
assert.ok(sideText.some((t) => t.includes("Sheet ") && t.includes("ô ")), "an XLSX side must cite sheet + cell");
const note = $("[data-testid='document-review-conflict-note']", conflict)[0];
assert.ok(note, "the conflict note must render");
assert.equal(text(note), "Chưa chọn giá trị đúng — cần người kiểm tra.");
ok("CONFLICT lists all sides with page/sheet-cell provenance and selects no winner");

// --- Vietnamese labels, never canonical keys as the operator wording --------
for (const fact of allFacts) {
  const label = text(fact.querySelector("p"));
  assert.ok(label && !/^[a-z_]+$/.test(label), `fact label must be Vietnamese, got "${label}"`);
}
ok("every fact is labelled in Vietnamese");

// --- honest partial state + the "not saved" line ---------------------------
assert.ok(
  text($("[data-testid='document-review-not-saved']", result)[0])
    .includes("Kết quả chỉ để kiểm tra — chưa ghi vào hồ sơ lô hàng."),
  "the result must state it is not written into the shipment record"
);
const partial = text($("[data-testid='document-review-partial']", result)[0]);
assert.ok(partial.includes("Đã đọc 3/3 tệp"), `partial line must be honest, got "${partial}"`);
assert.ok(partial.includes("Đã có đủ ba loại chứng từ chính để đối chiếu."), partial);
// Per-document states are visible too.
const docs = $("[data-testid='document-review-document']", result);
assert.equal(docs.length, 3);
for (const doc of docs) {
  assert.equal(doc.getAttribute("data-state"), "READABLE");
  assert.ok(text(doc).includes("Đọc được"), "a readable document must say so");
}
ok("document states, partial-review honesty and the not-saved line all render");

// --- no invented score of any kind -----------------------------------------
const resultText = text(result).toLowerCase();
for (const forbidden of ["confidence", "điểm chất lượng", "quality score", "% chính xác", "ai score"]) {
  assert.ok(!resultText.includes(forbidden), `no invented metric: "${forbidden}"`);
}
assert.ok(!/\b\d{1,3}%\b/.test(text(result)), "no confidence percentage may be invented");
ok("no score, no percentage, no invented quality metric");

// ===========================================================================
console.log("STEP 8 — a refusal is shown honestly instead of a fake result");
// ===========================================================================
const beforeRefusal = reviewEvents().length;
const refuseButton = $("[data-testid='document-review-run']", panel)[0];
refuseButton.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
await tick();
assert.equal(reviewEvents().length, beforeRefusal + 1, "a second review is one more request");
const refusedId = reviewEvents().at(-1).value.payload.requestId;
settleReview(refusedId, {
  ok: false,
  review: null,
  error: "Có tệp đính kèm không thuộc lô hàng này. Chưa đọc bất kỳ tệp nào.",
});
await tick(200);
const errorBox = $("[data-testid='document-review-error']", panel)[0];
assert.ok(errorBox, "a refusal must be surfaced");
assert.ok(text(errorBox).includes("không thuộc lô hàng này"), "the backend's own wording must be shown");
assert.equal(text($("[data-testid='document-review-run']", panel)[0]), "KIỂM TRA CHỨNG TỪ",
  "the pending state must clear after a refusal");
// A refused request ran no review, so the server slot still holds the PREVIOUS
// successful one. It stays visible next to the honest refusal instead of being
// silently replaced by an empty result.
const afterRefusal = $("[data-testid='document-review-result']", panel)[0];
assert.ok(afterRefusal, "the previous successful review must remain visible");
assert.equal(afterRefusal.getAttribute("data-request-id"), pendingRequestId,
  "the visible result must still be the one that actually ran");
ok("a refusal is displayed verbatim, never as a fake success");

// ===========================================================================
console.log("STEP 9 — a review belonging to another shipment is never projected");
// ===========================================================================
const foreign = clone(currentModel);
foreign.version = "cross-shipment-review";
foreign.shipmentDocumentReview = {
  ...clone(RAW.shipmentDocumentReview),
  shipmentId: OTHER_SHIPMENT_ID,
  requestId: "ATTREV-OTHER-LOT",
};
foreign.lastWrites = [];
invoke(foreign);
await tick(200);
const crossLot = await gotoReviewTab();
assert.equal($("[data-testid='document-review-result']", crossLot.reviewPanel).length, 0,
  "another lot's review must never render against this shipment");
assert.ok(!mainText().includes(OTHER_SHIPMENT_ID), "another lot's id must not appear here");
ok("cross-shipment session result is never projected");

// ===========================================================================
console.log("STEP 10 — changing shipment clears the stale local selection");
// ===========================================================================
const switched = clone(RAW);
switched.shipmentDocumentReview = null;
switched.lastWrites = [];
switched.version = "switched-shipment";
invoke(switched);
await tick();
const { shell: shellAfter, reviewPanel: panelAfter } = await gotoReviewTab();
assert.equal(text($("[data-testid='document-review-count']", panelAfter)[0]), "Đã chọn 0 tệp",
  "the stale selection must not survive a shipment change");
const checkedBoxes = $("[data-testid='attachment-review-toggle'] input", shellAfter)
  .filter((box) => box.checked);
assert.equal(checkedBoxes.length, 0, "no checkbox may remain ticked after a shipment change");
assert.equal($("[data-testid='document-review-result']", panelAfter).length, 0,
  "the previous review must not linger");
ok("switching lots drops the stale selection and the stale result");

// ===========================================================================
console.log("STEP 11 — the DOM leaks no byte, storage id or raw SHA");
// ===========================================================================
const reviewed = clone(RAW);
reviewed.shipmentDocumentReview = clone(RAW.shipmentDocumentReview);
reviewed.lastWrites = [];
invoke(reviewed);
await tick(200);
const reviewedView = await gotoReviewTab();
assert.ok($("[data-testid='document-review-result']", reviewedView.reviewPanel)[0],
  "the reviewed fixture must render its result for the leak check to mean anything");
const bodyText = text(window.document.body);
assert.ok(!/[0-9a-f]{64}/.test(bodyText), "no raw SHA-256 may reach the DOM");
assert.ok(!bodyText.includes("fixture-gridfs"), "no storage file id may reach the DOM");
assert.ok(!bodyText.includes("shipment_attachment_files"), "no GridFS bucket name may reach the DOM");
assert.ok(!bodyText.includes("storage_file_id"), "no storage key may reach the DOM");
assert.ok(!/[A-Za-z0-9+/]{300,}={0,2}/.test(bodyText), "no base64 body may reach the DOM");
// The full extracted text of a document must never be projected: the fixture's
// own review carries only bounded evidence.
assert.ok(!bodyText.includes("SYNTHETIC — NOT A REAL SHIPMENT"),
  "raw document body text must not be projected into the DOM");
ok("no bytes, base64, storage id, GridFS id or raw SHA in the DOM");

// ===========================================================================
console.log("STEP 12 — mobile-first at 390px: no forced horizontal overflow");
// ===========================================================================
const mobilePanel = reviewedView.reviewPanel;
assert.ok(!mobilePanel.className.includes("overflow-x-auto"), "the surface must not force horizontal scrolling");
assert.equal($("[class*='overflow-x-auto']", mobilePanel).length, 0, "no child forces horizontal scroll");

const reviewButton = $("[data-testid='document-review-run']", mobilePanel)[0];
assert.ok(reviewButton.className.includes("min-h-[48px]"), "the review action is not thumb-sized");
const reviewSection = reviewedView.shell;
for (const toggle of $("[data-testid='attachment-review-toggle']", reviewSection)) {
  assert.ok(toggle.className.includes("min-h-[44px]"), "review checkboxes must be thumb-sized");
}
for (const row of $("[data-testid='attachment-row']", reviewSection)) {
  assert.ok(row.className.includes("flex-wrap"), "attachment rows must wrap on narrow viewports");
  assert.ok(row.querySelector("p").className.includes("break-words"), "long names must break");
}
for (const fact of $("[data-testid='document-review-fact']", mobilePanel)) {
  assert.ok(fact.className.includes("min-w-0"), "a fact card must not force mobile overflow");
}
for (const chip of $("[data-testid='document-review-chip']", mobilePanel)) {
  // The Vietnamese label sits in the chip's second <p>; a long one ("Chỉ một
  // nguồn") must wrap instead of widening the 2-up mobile grid.
  const label = chip.querySelectorAll("p")[1];
  assert.ok(label, "chip label element missing");
  assert.ok(label.className.includes("break-words"), "chip labels must wrap on a phone");
}
// A 2-up chip grid at 390px instead of a 5-up row that would overflow.
const chipGrid = $("[data-testid='document-review-summary']", mobilePanel)[0];
assert.ok(chipGrid.className.includes("grid-cols-2"), "chips must start at a 2-up mobile grid");
ok("no forced horizontal overflow; thumb-sized controls; wrapping cards at 390px");

console.log(`\nSHIPMENT_DOCUMENT_REVIEW_DOM_ACCEPTANCE=PASSED checks=${checks}`);
