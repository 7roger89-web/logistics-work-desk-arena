// ============================================================================
// LOGI_EXCEL_FIDELITY_INLINE_EDIT_V1 — DOM acceptance on the REAL bundle.
//
// Runs component/dist/logi-shell.js in jsdom (the repository's existing
// no-browser DOM lane) and proves, against REAL Python-produced data
// (scripts/make_excel_inline_text_dom_fixture.py):
//
//   E  clicking the title turns it into an input in place; entering the new
//      wording applies it and the paper shows it immediately;
//   F  a product name (bound to the canonical goods field), a column heading,
//      a payment term and a multi-line note are all editable in place;
//   *  the payload sent to Python carries the edit — an override for presentation
//      wording, the canonical field for a bound region;
//   *  the paper renders PYTHON's resolved text map (an echo that differs from the
//      typed text wins on screen) → the preview is never local-only state;
//   *  amounts/totals are NOT editable regions and expose no edit affordance;
//   *  per-region restore and the global undo return wording to its default;
//   *  "Lưu bản nháp" emits quote_edit with expectedVersion + the edited wording;
//   *  the ORIGINAL workbook viewer renders the file's real sheet tabs in order,
//      merged cells, cached formula results and UNKNOWN for an uncached formula,
//      and keeps an internal cost sheet locked.
//
// VIEWPORT NOTE (honest scope): jsdom performs no layout, so this file makes no
// pixel/viewport claim. Real 1440×900 / 390×844 rendering was NOT measured in
// this environment — see the task's evidence notes.
//
// Run: node tests/component/dom_acceptance_excel_inline_text_edit.mjs
// ============================================================================

import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import assert from "node:assert/strict";
import path from "node:path";
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const require = createRequire(path.join(ROOT, "component/package.json"));
const { JSDOM } = require("jsdom");
const PY = process.env.PYTHON || path.join(ROOT, ".venv/bin/python");
const SCRATCH = path.join(ROOT, ".tmp/excel-inline-text-edit");
mkdirSync(SCRATCH, { recursive: true });
const FIXTURE_FILE = path.join(SCRATCH, "dom_fixture.json");
execFileSync(PY, ["scripts/make_excel_inline_text_dom_fixture.py", FIXTURE_FILE], { cwd: ROOT, stdio: "inherit" });
const FIX = JSON.parse(readFileSync(FIXTURE_FILE, "utf8"));
const BASE = JSON.parse(readFileSync(path.join(ROOT, "tests/component/fixtures/view_model_phase_b.json"), "utf8"));

const TITLE_EDIT = "BÁO GIÁ NHẬP KHẨU BÀN HỌP";
const PYTHON_TITLE = "TIÊU ĐỀ DO PYTHON TRẢ VỀ";
const PRODUCT_EDIT = "Bàn họp nhập khẩu cao cấp";
const PAYMENT_EDIT = "Thanh toán 70% trước khi giao hàng, 30% sau khi nhận hàng.";
const MULTILINE_EDIT = "Dòng ghi chú một\nDòng ghi chú hai";

const dom = new JSDOM("<!DOCTYPE html><html><body></body></html>", { url: "http://localhost:8501/", pretendToBeVisual: true });
const { window } = dom;
globalThis.window = window;
globalThis.document = window.document;
try { Object.defineProperty(globalThis, "navigator", { value: window.navigator, configurable: true }); } catch {}
for (const key of ["HTMLElement", "HTMLInputElement", "HTMLTextAreaElement", "HTMLSelectElement", "HTMLAnchorElement",
  "Event", "CustomEvent", "MouseEvent", "KeyboardEvent", "Node", "MutationObserver", "getComputedStyle"]) {
  globalThis[key] = window[key];
}
if (!globalThis.MessageChannel) globalThis.MessageChannel = window.MessageChannel;
window.HTMLElement.prototype.scrollIntoView = () => {};

const tick = (ms = 60) => new Promise((resolve) => setTimeout(resolve, ms));
const $ = (selector, root = window.document) => [...root.querySelectorAll(selector)];
const text = (el) => (el?.textContent || "").replace(/\s+/g, " ").trim();
const find = (needle, selector = "button,a", root = window.document) => {
  const nodes = $(selector, root);
  return nodes.find((el) => text(el) === needle) || nodes.find((el) => text(el).startsWith(needle)) || nodes.find((el) => text(el).includes(needle)) || null;
};
async function click(el, label) {
  assert.ok(el, `clickable not found: ${label}`);
  el.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
  await tick();
  return el;
}
const byTestId = (id) => window.document.querySelector(`[data-testid="${id}"]`);
const byRegion = (id) => window.document.querySelector(`[data-region="${id}"]`);
const inputFor = (id) => window.document.querySelector(`[data-testid="eq-text-input-${id}"]`);
function setValue(input, value) {
  const proto = input.tagName === "TEXTAREA" ? window.HTMLTextAreaElement.prototype : window.HTMLInputElement.prototype;
  Object.getOwnPropertyDescriptor(proto, "value").set.call(input, value);
  input.dispatchEvent(new window.Event("input", { bubbles: true }));
  input.dispatchEvent(new window.Event("change", { bubbles: true }));
}
async function press(input, key, extra = {}) {
  input.dispatchEvent(new window.KeyboardEvent("keydown", { key, bubbles: true, cancelable: true, ...extra }));
  await tick();
}

let passed = 0;
const checks = [];
const note = (name) => { checks.push(name); passed += 1; console.log(`  ✓ ${name}`); };

const host = window.document.createElement("div");
window.document.body.appendChild(host);
const triggers = [];
const mountRef = { current: null };
const mount = (data) => mountRef.current({
  name: "logi_shell", data, parentElement: host,
  setTriggerValue: (event, value) => triggers.push({ event, value }),
});
const payloadsOf = (name) => triggers.filter((t) => t.event === name).map((t) => t.value.payload);
const lastPayload = (name) => payloadsOf(name).at(-1);

function quoteRow({ excelQuote = FIX.excelQuote, version = 1, status = "DRAFT", statusLabel = "Nháp" } = {}) {
  return {
    id: FIX.quote_id, quoteNo: "BG-2026-DOMFIX1", customerId: FIX.customerId, customer: FIX.customerName,
    salesOwner: "staging.support", status, statusLabel, origin: "Trung Quốc", destination: "Việt Nam",
    route: "Nansha - Hải Phòng", incoterm: "EXW", transportMode: "Sea", goodsDescription: "Bàn họp văn phòng",
    expectedDeliveryDate: "2026-12-20", currency: "VND", total: null, sellingPriceTotalVnd: null,
    estimatedCostVnd: null, estimatedMarginVnd: null, isEstimate: true, ledgerPosted: false,
    fxRatesToVnd: { CNY: 3900 }, fxSource: "", fxNeededFor: [], excelQuote,
    sentVersions: [], serviceLines: [], assumptions: [], customerNotes: [], statusHistory: [],
    version, shipmentId: "", allowedTransitions: ["READY_FOR_REVIEW"], source: "core.database.load_quotes",
  };
}

let vmSeq = 0;
function vmWith({ lastWrites = [], customer = FIX.customer, excelQuote = FIX.excelQuote, version = 1, status = "DRAFT" } = {}) {
  const vm = structuredClone(BASE);
  // Every backend round-trip ships a NEW view model (Streamlit re-renders), so a
  // mount that reuses the previous version string would be ignored as "no change".
  vm.version = `${BASE.version}-${(vmSeq += 1)}`;
  vm.customers = [...(vm.customers || []), { id: FIX.customerId, name: FIX.customerName, short: FIX.customerName, mst: "0109999999" }];
  vm.quotes = [quoteRow({ excelQuote, version, status })];
  vm.lastWrites = lastWrites;
  return vm;
}

/**
 * The wording Python would resolve from this payload: the base map with the
 * submitted overrides and the bound canonical fields applied — the same rule the
 * backend enforces, so a bound region only changes when ITS field changed.
 */
function echoSnapshot(payload, extra = {}) {
  const x = payload?.excelQuote || {};
  const values = { ...(FIX.customer.text.values || {}), ...(x.customer_text?.overrides || {}), ...extra };
  if (x.goodsDescription) values["doc.goods_description"] = x.goodsDescription;
  if (x.route) values["doc.route"] = x.route;
  if (x.additional_public_notes) values["notes.additional"] = x.additional_public_notes;
  const overrides = x.customer_text?.overrides || {};
  for (const good of x.goods || []) {
    if (!good.id) continue;
    for (const [key, field] of [["name", "description"], ["model", "model"], ["material", "material"], ["note", "note"]]) {
      if (good[field]) values[`goods.${good.id}.${key}`] = good[field];
    }
  }
  for (const option of Object.values(x.options || {})) {
    if (option.scope) values.scope = option.scope;
    for (const line of option.service_lines || []) {
      if (!line.id) continue;
      if (line.service_name) values[`service.${line.id}.name`] = line.service_name;
      if (line.public_note) values[`service.${line.id}.public_note`] = line.public_note;
    }
  }
  const echoed = structuredClone(FIX.customer);
  echoed.text = structuredClone(FIX.customer.text);
  echoed.text.values = values;
  echoed.text.regions = echoed.text.regions.map((region) => values[region.id] === undefined ? region
    : { ...region, value: values[region.id], source: overrides[region.id] ? "SALE_EDITED" : region.source });
  // The paper renders one bullet per PUBLISHED note; its region id is note.<disclosure id>.
  echoed.published_notes = (FIX.customer.published_notes || []).map((note) => ({ id: note.id, text: values[`note.${note.id}`] ?? note.text }));
  echoed.customer_notes = echoed.published_notes.map((note) => note.text);
  return echoed;
}

const answered = [];
const answeredIds = new Set();
const waitingReadbacks = [];
async function waitForPreview() {
  for (let i = 0; i < 40; i += 1) {
    const fresh = triggers.filter((t) => t.event === "quote_preview" && !answeredIds.has(t.value.payload.requestId));
    if (fresh.length) return fresh.at(-1).value.payload;
    await tick(100);
  }
  throw new Error("quote_preview trigger with requestId expected");
}
const hasUnansweredPreview = () => triggers.some((t) => t.event === "quote_preview" && !answeredIds.has(t.value.payload.requestId));
/** Answer every outstanding quote_preview with the snapshot Python would return. */
async function settle({ extra = {}, wait = false } = {}) {
  if (wait && !hasUnansweredPreview()) {   // let the 500 ms preview debounce fire
    for (let i = 0; i < 15 && !hasUnansweredPreview(); i += 1) await tick(100);
  }
  let payload = null;
  for (let i = 0; i < 6; i += 1) {
    const fresh = triggers.filter((t) => t.event === "quote_preview" && !answeredIds.has(t.value.payload.requestId));
    if (!fresh.length) break;
    const request = fresh.at(-1).value;
    payload = request.payload;
    answeredIds.add(payload.requestId);
    const readback = {
      event: "quote_preview", ok: true, requestId: payload.requestId,
      readback: { quote: quoteRow({ excelQuote: payload.excelQuote }), customer: echoSnapshot(payload, extra) },
    };
    answered.push(readback);
    mount(vmWith({ customer: readback.readback.customer, lastWrites: [...answered, ...waitingReadbacks] }));
    await tick(150);
  }
  assert.ok(payload || answered.length, "a quote_preview request was answered");
  return payload;
}
const paperLive = () => byRegion("doc.title")?.className.includes("eq-inline-off") === false;
let paperSnapshot = "";
let workbookSnapshot = "";

/** Open the Excel quote workspace of the fixture quote from the quotes list. */
async function openWorkspace(label) {
  await click(find("Báo Giá", "a", $("aside")[0]), "Báo Giá nav");
  await tick(140);
  if (!byTestId("excel-quote-workspace")) {
    await click(byTestId("quote-workspace-bao-gia") || find("BÁO GIÁ", "button"), "BÁO GIÁ tab");
    await tick(120);
  }
  if (!byTestId("excel-quote-workspace")) await click(find("Sửa", "button"), `Sửa (${label})`);
  assert.ok(byTestId("excel-quote-workspace"), `excel quote workspace open — ${label}`);
}

console.log("BOOT — real bundle, real Python-produced excel quote fixture");
const module = await import(path.join(ROOT, "component/dist/logi-shell.js"));
assert.equal(typeof module.default, "function", "bundle must default-export mount");
mountRef.current = module.default;
mount(vmWith());
await tick(160);
assert.ok(!text(window.document.body).includes("process is not defined"));
await openWorkspace("SYNTHETIC fixture quote");
note(`Real bundle opened the Excel quote workspace on a Python-produced SYNTHETIC quote (${FIX.quote_id})`);

// ---------------------------------------------------------------- E: the title
await click(byTestId("excel-step-3"), "step 3");   // the step nav jumps straight to step 3
const firstPreview = await waitForPreview();
assert.equal(firstPreview.customerId, FIX.customerId);
assert.equal(firstPreview.excelQuote.goods.length, 5);

await settle();
const calculation = answered.at(-1).readback.customer.goods_calculation;
assert.equal(calculation.row_count, 5);
assert.equal(calculation.quantity, 27);
assert.deepEqual(calculation.goods_totals, [{ currency: "CNY", amount: 607180 }]);
assert.equal(calculation.estimate_vnd, null, "no estimate while a customs basis is unconfirmed");
assert.match(String(calculation.unknown_reasons.join(" ")), /chưa xác định/);
note("Acceptance C: the backend read-back carries 5 rows / 27 pcs / 607,180 CNY and no invented total");
assert.ok(byTestId("excel-customer-preview"), "customer paper rendered after backend echo");
const titleRegion = byRegion("doc.title");
assert.ok(titleRegion, "title is a click-to-edit region");
assert.equal(text(titleRegion.querySelector(".eq-inline-value")), "BÁO GIÁ DỊCH VỤ LOGISTICS");
note("Step-3 title renders as an inline text region from the backend text map");

await click(titleRegion, "title region");
const titleInput = inputFor("doc.title");
assert.ok(titleInput && titleInput.tagName === "INPUT", "title turned into an input in place");
setValue(titleInput, TITLE_EDIT);
await press(titleInput, "Enter");
assert.equal(text(byRegion("doc.title").querySelector(".eq-inline-value")), TITLE_EDIT);
assert.equal(byTestId("eq-text-status").dataset.changedRegions, "1");
note(`Acceptance E: title edited in place → "${TITLE_EDIT}" appears immediately`);

assert.equal((await waitForPreview()).excelQuote.customer_text.overrides["doc.title"], TITLE_EDIT);
note("The edit travels to Python as customer_text.overrides['doc.title']");

// The paper must render PYTHON's resolved map, not the browser's own copy.
await settle({ extra: { "doc.title": PYTHON_TITLE } });
assert.equal(text(byRegion("doc.title").querySelector(".eq-inline-value")), PYTHON_TITLE);
note("An echo that differs from the typed text wins on screen → preview reads Python's map");
// …and the browser must NOT quietly restore its own value afterwards.
assert.equal(text(byRegion("doc.title").querySelector(".eq-inline-value")), PYTHON_TITLE);
await settle();

// ------------------------------------------- F: bound name, label, term, note
assert.ok(byRegion("goods.row-8.name"), "goods product name is a region");
await click(byRegion("goods.row-8.name"), "product name");
setValue(inputFor("goods.row-8.name"), PRODUCT_EDIT);
await press(inputFor("goods.row-8.name"), "Enter");
const routed = (await waitForPreview()).excelQuote;
assert.equal(routed.goods[0].description, PRODUCT_EDIT, "bound region writes the canonical goods field");
assert.equal((routed.customer_text?.overrides || {})["goods.row-8.name"], undefined, "…and never a parallel override");
note(`Acceptance F(1): product name "${PRODUCT_EDIT}" written to goods[0].description, not an override`);

await settle();
assert.equal(text(byRegion("doc.title").querySelector(".eq-inline-value")), TITLE_EDIT);
note("The next real backend round-trip echoes the stored override → the browser never overrules Python");

await click(byRegion("col.service.name"), "column heading");
setValue(inputFor("col.service.name"), "Nội dung dịch vụ");
await press(inputFor("col.service.name"), "Enter");
assert.equal((await waitForPreview()).excelQuote.customer_text.overrides["col.service.name"], "Nội dung dịch vụ");
note("Acceptance F(2): service column heading edited in place → col.service.name override");
await settle();

assert.ok(byRegion("note.payment"), "payment term is a region");
await click(byRegion("note.payment"), "payment term");
const paymentInput = inputFor("note.payment");
assert.equal(paymentInput?.tagName, "TEXTAREA", "a long region edits with a textarea");
setValue(paymentInput, PAYMENT_EDIT);
await press(paymentInput, "Enter", { ctrlKey: true });
assert.equal((await waitForPreview()).excelQuote.customer_text.overrides["note.payment"], PAYMENT_EDIT);
note("Acceptance F(3): payment term edited (Ctrl+Enter applies a multi-line region)");
await settle();

assert.ok(byRegion("notes.additional"), "extra note is a region");
await click(byRegion("notes.additional"), "extra note");
setValue(inputFor("notes.additional"), MULTILINE_EDIT);
await press(inputFor("notes.additional"), "Ctrl+Enter", { ctrlKey: true, key: "Enter" });
const multiPayload = await waitForPreview();
assert.equal(multiPayload.excelQuote.additional_public_notes, MULTILINE_EDIT);
note("Acceptance F(4): multi-line note written to the canonical additional_public_notes field");
await settle();
assert.ok(text(byTestId("excel-customer-preview")).includes("Dòng ghi chú một"));

// ---------------------------------------------------------------- numbers
const paper = byTestId("excel-customer-preview");
const editableTexts = $("[data-region]", paper).map((el) => text(el));
assert.ok(editableTexts.length >= 40, "the whole customer document is region-driven");
assert.ok(!editableTexts.some((value) => value.includes("607")), "no amount is an editable region");
assert.ok(!editableTexts.some((value) => value.includes("35.000.000")), "the service amount is not editable");
const total = byTestId("excel-public-total");
assert.ok(total && !total.querySelector("[data-region]"), "the grand total has no edit affordance");
assert.match(text(total), /Chưa xác định/, "an unconfirmed customs basis never becomes an invented total");
note("Amounts / FX / totals render read-only: no region, no edit affordance");

assert.match(text(paper), /607\.180 RMB/, "the per-currency goods total is printed as the table's own total");
assert.match(text(paper), /5 dòng · 27 chiếc/);
note("The paper shows the goods table's own 5-row / 27-pcs / 607,180 CNY subtotal");

// Acceptance I — nothing internal reaches the customer document on screen.
const paperText = text(paper);
for (const leak of ["PRIVATE-SALE-NOTE", "PRIVATE-RATE-SUPPLIER", "31.800.000", "31800000", "Giá vốn", "Lợi nhuận"]) {
  assert.ok(!paperText.includes(leak), `customer paper must not contain "${leak}"`);
}
note("Acceptance I: no cost price, cost source, internal note or margin in the customer paper");

paperSnapshot = byTestId("excel-customer-preview").outerHTML;

// ---------------------------------------------------------------- undo/restore
const changedBeforeRestore = Number(byTestId("eq-text-status").dataset.changedRegions);
assert.ok(changedBeforeRestore >= 3, "the title, the label and two notes are still unsaved edits");
await click(byTestId("eq-text-restore-doc.title"), "restore title");
assert.equal(text(byRegion("doc.title").querySelector(".eq-inline-value")), "BÁO GIÁ DỊCH VỤ LOGISTICS");
assert.ok(!byTestId("eq-text-restore-doc.title"), "the restore control disappears once the region is back to its default");
assert.equal(Number(byTestId("eq-text-status").dataset.changedRegions), changedBeforeRestore - 1);
note("Per-region restore returns ONE region to its saved default and leaves the others alone");

await click(byTestId("eq-inline-undo"), "undo unsaved text");
await settle({ wait: true });
await tick(80);
assert.equal(Number(byTestId("eq-text-status").dataset.changedRegions), 0);
assert.equal(text(byRegion("note.payment").querySelector(".eq-inline-value")), "Thanh toán 80% trước khi giao hàng.");
note("Global undo returns every region to the last saved wording");

// ---------------------------------------------------------------- edit mode off
await click(byTestId("eq-inline-toggle"), "toggle edit mode");
await click(byRegion("sec.goods"), "region while read-only");
assert.ok(!inputFor("sec.goods"), "read-only mode does not open an editor");
assert.equal(byTestId("excel-customer-preview").dataset.editing, "false");
await click(byTestId("eq-inline-toggle"), "toggle edit mode back");
note("Chế độ sửa can be switched off for clean reading (no editor opens)");

// ---------------------------------------------------------------- save payload
await click(byRegion("doc.title"), "title again");
setValue(inputFor("doc.title"), TITLE_EDIT);
await press(inputFor("doc.title"), "Enter");
await click(byRegion("goods.row-8.name"), "product name again");
setValue(inputFor("goods.row-8.name"), PRODUCT_EDIT);
await press(inputFor("goods.row-8.name"), "Enter");
await settle({ wait: true });
await tick(120);
assert.ok(paperLive(), "the workspace is live again after the backend echo");
await click(byTestId("excel-save-step3"), "Lưu bản nháp");
const save = lastPayload("quote_edit");
assert.ok(save, "saving emits the existing quote_edit event");
assert.equal(save.expectedVersion, 1);
assert.equal(save.excelQuote.customer_text.overrides["doc.title"], TITLE_EDIT);
assert.equal(save.excelQuote.goods[0].description, PRODUCT_EDIT);
note("Acceptance G/H bridge: Lưu bản nháp emits quote_edit with expectedVersion + the edited wording");

// The backend read-back of that save: the SAME draft, now version 2.
const savedDraft = structuredClone(save.excelQuote);
mount(vmWith({ excelQuote: savedDraft, version: 2, lastWrites: [...answered, ...waitingReadbacks,
  { event: "quote_edit", ok: true, requestId: save.requestId, readback: quoteRow({ excelQuote: savedDraft, version: 2 }) }] }));
await tick(180);
assert.equal(byTestId("excel-quote-workspace").dataset.version, "2");
assert.match(text(byTestId("excel-quote-workspace")), /phiên bản 2/);
note("The save read-back is adopted from the backend (version 2), not from a local guess");

// «Tải lại trang» — a brand-new view model — then reopen the quote: the edited
// wording is still there, because it came from the backend draft.
for (let i = 0; i < 2 && !byRegion("doc.title"); i += 1) {
  mount(vmWith({ excelQuote: savedDraft, version: 2, lastWrites: [...answered, ...waitingReadbacks] }));
  await tick(180);
  await openWorkspace("after reload");
  await click(byTestId("excel-step-3"), "step 3");
  await settle({ wait: true });
}
assert.equal(text(byRegion("doc.title").querySelector(".eq-inline-value")), TITLE_EDIT);
assert.equal(text(byRegion("goods.row-8.name").querySelector(".eq-inline-value")), PRODUCT_EDIT);
note("Acceptance G: after a reload the reopened quote shows the SAVED wording from the backend draft");

// ---------------------------------------------------------------- workbook view
// Re-mount the bundle (a fresh Streamlit render) and open the SAME saved quote
// again: the original-workbook viewer must be reachable from the list, not only
// straight after an upload.
mount(vmWith({ lastWrites: [...answered, ...waitingReadbacks] }));
await tick(160);
await openWorkspace("reopened from the quote list");
assert.equal(byTestId("excel-quote-workspace").dataset.savedId, FIX.quote_id);
await click(byTestId("excel-step-1"), "back to step 1");   // the viewer lives in step 1
await tick(140);
await click(byTestId("excel-source-workbook-open"), "open original workbook");
const wbRequest = lastPayload("quote_source_workbook_view");
assert.ok(wbRequest, "workbook view request dispatched");
assert.equal(wbRequest.id, FIX.quote_id);
mount(vmWith({ customer: FIX.customer, lastWrites: [...answered, ...waitingReadbacks,
  { event: "quote_source_workbook_view", ok: true, requestId: wbRequest.requestId, readback: FIX.workbookView }] }));
await tick(180);
const tabs = $('[data-testid^="workbook-tab-"]');
assert.deepEqual(FIX.workbookView.overview.sheet_names, ["BÁO GIÁ", "LG nhập - Đại lý TT L Xuất", "Dự kiến Chi phí"]);
assert.equal(tabs.length, 3, "one tab per sheet of the uploaded file");
// Each tab shows "<index><sheet name><classification>"; the NAME span must be the
// file's own sheet name, in the file's own order.
assert.deepEqual(tabs.map((el) => text(el.querySelectorAll("span")[1])),
  ["BÁO GIÁ", "LG nhập - Đại lý TT L Xuất", "Dự kiến Chi phí"]);
assert.deepEqual(tabs.map((el) => el.getAttribute("data-classification")),
  ["CUSTOMER", "INTERNAL", "INTERNAL"]);
assert.equal(text(tabs[0].querySelectorAll("span")[2]), "Sheet khách");
assert.equal(text(tabs[2].querySelectorAll("span")[2]), "Sheet nội bộ");
assert.match(text(byTestId("workbook-sheet-order")), /BÁO GIÁ → LG nhập - Đại lý TT L Xuất → Dự kiến Chi phí/);
note("Acceptance A: real sheet names in the file's own order, as tabs");

const mergedTitle = byTestId("workbook-cell-2:1");
assert.equal(mergedTitle.getAttribute("colspan"), "8", "merged title keeps its span");
assert.equal(text(mergedTitle), "BÁO GIÁ DỊCH VỤ LOGISTICS");
assert.match(mergedTitle.getAttribute("style") || "", /background/);
assert.equal($(".eq-wb-scroll").length, 1, "the workbook grid scrolls inside its own container");
workbookSnapshot = byTestId("excel-source-workbook").outerHTML;
note("Acceptance B: merged cell span, value and fill reproduced from the source workbook");

const sumCell = byTestId("workbook-cell-13:6");
assert.equal(sumCell.dataset.formula, "true", "the cell is still a FORMULA cell, not a stored number");
assert.equal(text(sumCell.querySelector(".eq-wb-badge")), "F");
assert.ok(text(sumCell).startsWith("27"), `cached formula result shown (got "${text(sumCell)}")`);
assert.match(text(byTestId("workbook-cell-13:7")), /607.*180/);
const uncached = byTestId("workbook-cell-22:2");
assert.equal(uncached.dataset.unknown, "true");
assert.match(text(uncached), /chưa có giá trị cache/);
assert.ok(!/^0/.test(text(uncached)), "a formula without a cached value is never shown as 0");
note("Acceptance D: a formula with a cached result shows it; an uncached one is UNKNOWN, never 0");

assert.ok(text(byTestId("workbook-fidelity")).includes("CHƯA render"));
assert.ok(text(byTestId("excel-source-workbook")).includes("KHÔNG tuyên bố giữ nguyên 100%"));
note("The viewer states what it does NOT reproduce instead of claiming 100% fidelity");

await click($('[data-testid^="workbook-tab-"]')[2], "Dự kiến Chi phí tab");
const internalRequest = lastPayload("quote_source_workbook_view");
assert.equal(internalRequest.sheet, "Dự kiến Chi phí");
mount(vmWith({ customer: FIX.customer, lastWrites: [...answered, ...waitingReadbacks,
  { event: "quote_source_workbook_view", ok: true, requestId: internalRequest.requestId, readback: FIX.workbookViewInternal }] }));
await tick(180);
assert.ok(byTestId("workbook-locked"), "internal cost sheet stays locked for a lower-privileged role");
assert.ok(!text(byTestId("excel-source-workbook")).includes("12500000"));
note("Internal cost sheet: name visible, content withheld and never rendered as customer data");

// ---------------------------------------------------------------- responsive guard
assert.ok(paper && $(".eq-paper-table-wrap", paper).length >= 2, "customer tables sit in their own scroll container");
assert.ok($(".eq-wb-scroll").length === 0 || $(".eq-wb-scroll").length === 1, "no stray grid outside its container");
note("Responsive guard present: wide tables scroll inside their container, not the page");

// A STATIC DOM snapshot for the Owner to look at in a real browser at any width.
// It is markup produced by the real bundle, not a screenshot: no layout was
// measured, and the jsdom lane cannot certify 1440x900 / 390x844.
const css = readFileSync(path.join(ROOT, "component/dist/logi-shell.css"), "utf8");
writeFileSync(path.join(SCRATCH, "preview-snapshot.html"), `<!DOCTYPE html>
<html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>LOGI_EXCEL_FIDELITY_INLINE_EDIT_V1 — ảnh chụp DOM tĩnh</title><style>${css}
body{margin:0;background:#f1f5f9;font-family:ui-sans-serif,system-ui,sans-serif}.snap{padding:16px;max-width:1300px;margin:0 auto}
.snap h2{font-size:16px;font-weight:800;color:#0f2a4a;margin:24px 0 8px}
.snap .warn{background:#fff7ed;border:1px solid #fdba74;color:#7c2d12;border-radius:10px;padding:10px 12px;font-size:13px}</style></head>
<body><div class="snap">
<p class="warn"><b>Ảnh chụp DOM tĩnh (jsdom), KHÔNG phải screenshot.</b> Markup do chính bundle đang chạy sinh ra, kèm CSS thật, để xem ở mọi khổ màn hình.
Trình duyệt trong môi trường này không có Chromium nên <b>chưa đo được 1440×900 / 390×844</b>; phần này vẫn là gate mở.
Fixture là workbook <b>SYNTHETIC</b>, không phải file Lục Giác thật.</p>
<h2>Bước 3 — bản báo giá khách, mọi vùng chữ sửa được tại chỗ</h2>${paperSnapshot}
<h2>Bản xem workbook gốc (chỉ đọc) — ô gộp, giá trị cache, công thức thiếu cache</h2>${workbookSnapshot}
</div></body></html>`, "utf8");

writeFileSync(path.join(SCRATCH, "dom-checks.json"), JSON.stringify({
  syntheticFixture: true, quoteId: FIX.quote_id, checks, passed,
  regions: FIX.textMap.editable_region_count,
  viewportClaim: "NONE — jsdom performs no layout; 1440x900 / 390x844 were not measured here",
}, null, 2));
console.log(`\nDOM ACCEPTANCE PASS — ${passed} checks (SYNTHETIC fixture; no viewport claim made)`);
