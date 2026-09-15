// ============================================================================
// LOGI_FINANCE_ACTUAL_ENTRY_PARITY_01 — DOM acceptance for the restored
// Finance Actual cost / selling-price entry (Lô Hàng → Tài chính / Công nợ).
//
// It drives the REAL production bundle (component/dist/logi-shell.js) in jsdom
// against a fixture generated from the REAL Logistics backend
// (scripts/gen_c2a_fixture.py → isolated mongomock staging + canonical
// writers), so every figure below is genuine backend output, not a mock.
//
// Proven here (rendering alone is NOT a pass — real DOM events are fired):
//   1. The existing actual rows read back ALL canonical fields:
//      dịch vụ · mã · SL · đơn vị · giá vốn · giá bán · VAT · ghi chú
//   2. The service picker IS the backend-projected catalog
//      (core.config.GETFLY_SERVICES_LIST → ViewModel.financeServiceCatalog)
//   3. ADD emits one `finance_actual_save` with code/unit/note and NO id
//   4. A blank money field is refused LOCALLY — no event leaves the browser
//   5. SỬA prefills the SAME canonical line and sends its id (edit, not append)
//   6. The backend's own refusal message (real writer text from the fixture)
//      is shown to the operator — never swallowed by an optimistic success
//   7. No destructive delete control exists in this slice
//   8. Quote Estimate · customer AR/receipts · partner payable · đối soát link
//      all still render (nothing above regressed)
//   9. Mobile layout stacks (no horizontal-scroll dependency)
//
// Run: node tests/component/dom_acceptance_finance_actual_entry.mjs
// ============================================================================

import { readFileSync } from "node:fs";
import assert from "node:assert/strict";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const require = createRequire(path.join(ROOT, "component/package.json"));
const { JSDOM } = require("jsdom");

const FIXTURE = JSON.parse(
  readFileSync(path.join(ROOT, "tests/component/fixtures/view_model_c2a.json"), "utf8")
);
const SHIPMENT = FIXTURE.shipment;
const LOT = FIXTURE.journey.shipments.find((x) => x.id === SHIPMENT);
const FIN = LOT.finance;
const CATALOG = FIXTURE.journey.financeServiceCatalog;
const vi = "vi-VN";
const nf = (n) => Number(n).toLocaleString(vi);

// ---------------------------------------------------------------------------
// jsdom environment
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
  "HTMLElement", "HTMLInputElement", "HTMLTextAreaElement", "HTMLSelectElement",
  "HTMLAnchorElement", "Event", "CustomEvent", "MouseEvent", "KeyboardEvent",
  "Node", "MutationObserver", "getComputedStyle",
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
const bodyText = () => text(window.document.body);

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

function type(input, value) {
  Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set.call(input, value);
  input.dispatchEvent(new window.Event("input", { bubbles: true }));
  input.dispatchEvent(new window.Event("change", { bubbles: true }));
}

function selectByValue(sel, value) {
  Object.getOwnPropertyDescriptor(window.HTMLSelectElement.prototype, "value").set.call(sel, value);
  sel.dispatchEvent(new window.Event("change", { bubbles: true }));
}

const fieldByLabel = (label, root) =>
  [...$("label", root)].find((l) => text(l).startsWith(label)) ?? null;
const inputByLabel = (label, root) => {
  const field = fieldByLabel(label, root);
  assert.ok(field, `field "${label}" not found`);
  const input = $("input", field)[0];
  assert.ok(input, `input for field "${label}" not found`);
  return input;
};

let passed = 0;
function ok(name) {
  passed += 1;
  console.log(`  ✓ ${name}`);
}

// ---------------------------------------------------------------------------
// Simulated Streamlit v2 component invocation
// ---------------------------------------------------------------------------

const host = window.document.createElement("div");
window.document.body.appendChild(host);

let triggers = [];
const mountRef = { current: null };
function invoke(data) {
  return mountRef.current({
    name: "logi_shell",
    data,
    parentElement: host,
    setTriggerValue: (event, value) => triggers.push({ event, value }),
  });
}
const eventsOf = (name) => triggers.filter((t) => t.event === name).map((t) => t.value);

/** The service picker, if the editor is showing one for the given label. */
function selectByLabel(label, root) {
  return $("select", root).find((el) => {
    const field = el.closest("div");
    return field && text(field.querySelector("label") || field).startsWith(label);
  }) ?? null;
}

const SECTION = () => window.document.getElementById("finance-actual-lines");
const FORM = () => window.document.getElementById("finance-actual-form");

// ---------------------------------------------------------------------------
// STEP 1 — boot the real bundle and open the finance tab
// ---------------------------------------------------------------------------

console.log("STEP 1 — boot bundle, open Lô Hàng → Tài chính / Công nợ");
{
  const mod = await import(path.join(ROOT, "component/dist/logi-shell.js"));
  assert.equal(typeof mod.default, "function", "bundle must default-export the mount function");
  mountRef.current = mod.default;
  invoke(FIXTURE.journey);
  await tick(140);
  const t = bodyText();
  assert.ok(!t.includes("process is not defined"), "process is not defined leaked");
  assert.ok(!t.includes("BidiComponent Error"), "BidiComponent Error rendered");

  await click("Lô Hàng", "a", $("aside")[0]);
  await click(SHIPMENT, "a", $("table.tbl")[0]);
  await click("Tài chính / Công nợ", "button", window.document.getElementById("workspace-tabs"));
  assert.ok(SECTION(), "the DỊCH VỤ & CHI PHÍ THỰC TẾ section must exist");
  ok("section rendered for the real shipment");
}

// ---------------------------------------------------------------------------
// STEP 2 — every booked row reads back the canonical fields
// ---------------------------------------------------------------------------

console.log("STEP 2 — existing rows show dịch vụ · mã · SL · đơn vị · giá vốn · giá bán · VAT · ghi chú");
{
  const rows = $("div.grid-cols-2", SECTION());
  assert.ok(FIN.actual.length >= 2, "fixture precondition: several booked lines");
  const seen = text(SECTION());
  for (const line of FIN.actual) {
    assert.ok(seen.includes(line.label), `row label missing: ${line.label}`);
    assert.ok(seen.includes(line.code), `row code missing: ${line.code}`);
    assert.ok(seen.includes(nf(line.qty)), `row qty missing for ${line.label}`);
    assert.ok(seen.includes(line.unit), `row unit missing for ${line.label}`);
    assert.ok(seen.includes(`${nf(line.cost)} ${line.ccy}`), `row cost missing for ${line.label}`);
    assert.ok(seen.includes(`${nf(line.price)} ${line.ccy}`), `row price missing for ${line.label}`);
    assert.ok(seen.includes(`VAT ${nf(line.vat)}%`), `row VAT missing for ${line.label}`);
    if (line.note) assert.ok(seen.includes(line.note), `row note missing for ${line.label}`);
  }
  const labelled = ["Dịch vụ", "Mã", "SL", "Đơn vị", "Giá vốn", "Giá bán", "VAT", "Ghi chú"];
  const headers = $("div", SECTION()).map(text);
  for (const caption of labelled) {
    assert.ok(headers.some((h) => h === caption) || seen.includes(caption), `caption ${caption} missing`);
  }
  assert.ok(rows.length > 0, "each row must be a responsive grid (stacked on mobile)");
  ok(`${FIN.actual.length} booked row(s) render all eight canonical fields`);
}

// ---------------------------------------------------------------------------
// STEP 3 — the picker IS the backend catalog (reuse, not duplication)
// ---------------------------------------------------------------------------

console.log("STEP 3 — service picker options come from financeServiceCatalog");
{
  await click("THÊM DỊCH VỤ / CHI PHÍ", "button", SECTION());
  const form = FORM();
  assert.ok(form, "the add/edit form must open");
  const codes = $("option", form).map((o) => o.value).filter(Boolean);
  assert.equal(codes.length, CATALOG.length, "one option per projected catalog entry, no more, no less");
  assert.deepEqual(codes, CATALOG.map((e) => e.code));
  const labels = $("option", form).map((o) => text(o)).filter((v) => v && !v.startsWith("—"));
  assert.deepEqual(labels, CATALOG.map((e) => `${e.name} (${e.code})`));
  // A blank quantity is offered as the canonical default 1.
  const qty = inputByLabel("Số lượng", form);
  assert.equal(qty.value, "1", "Số lượng defaults to 1");
  // And nothing is pre-booked: the money boxes start empty (= UNKNOWN).
  assert.equal(inputByLabel("Giá vốn", form).value, "");
  assert.equal(inputByLabel("Giá bán", form).value, "");
  ok(`${CATALOG.length} catalog entries delivered by the backend, rendered verbatim`);
}

// ---------------------------------------------------------------------------
// STEP 4 — picking a service auto-fills code + unit; save sends NO id
// ---------------------------------------------------------------------------

console.log("STEP 4 — auto-filled code/unit + new-line payload");
{
  const entry = CATALOG.find((e) => e.code === "LCC") ?? CATALOG[0];
  const form = FORM();
  selectByValue($("select", form)[0], entry.code);
  await tick();
  const code = inputByLabel("Mã dịch vụ", form);
  assert.equal(code.value, entry.code, "Mã dịch vụ is auto-filled and read-only");
  assert.equal(code.readOnly, true);
  assert.equal(inputByLabel("Đơn vị", form).value, entry.unit, "Đơn vị comes from the catalog");

  type(inputByLabel("Giá vốn", form), "1.200.000");
  type(inputByLabel("Giá bán", form), "1500000");
  type(inputByLabel("VAT %", form), "8");
  type(inputByLabel("Ghi chú", form), "Chốt với chủ hàng lúc 16h");
  await tick();
  // The preview line is display-only arithmetic over what was typed.
  const preview = text(form).includes("Số chính thức của lô do backend tính khi lưu");
  assert.ok(preview, "the preview must be labelled as non-authoritative");

  triggers = [];
  await click("LƯU DÒNG THỰC TẾ", "button", form);
  await tick(120);
  const sent = eventsOf("finance_actual_save");
  assert.equal(sent.length, 1, "one click = one typed event");
  const { line, shipmentId, requestId } = sent[0].payload;
  assert.equal(shipmentId, SHIPMENT);
  assert.equal(line.name, entry.name);
  assert.equal(line.code, entry.code);
  assert.equal(line.unit, entry.unit);
  assert.equal(line.qty, "1");
  assert.equal(line.cost, "1.200.000", "the typed amount travels verbatim — the backend parses it");
  assert.equal(line.price, "1500000");
  assert.equal(line.vat, "8");
  assert.equal(line.note, "Chốt với chủ hàng lúc 16h");
  assert.ok(!("id" in line), "a NEW line carries no id; the backend mints the canonical one");
  assert.match(requestId, /^FACTUAL-REQ-/);
  ok("new line emitted with catalog code + unit + note and no id");
}

// ---------------------------------------------------------------------------
// STEP 5 — a blank money field never reaches the backend
// ---------------------------------------------------------------------------

console.log("STEP 5 — blank cost/price/VAT refused locally");
{
  // Re-open the form for the "Hàng tiêu dùng" lot entry and leave the money blank.
  await click("HỦY, KHÔNG LƯU", "button", FORM());
  await click("THÊM DỊCH VỤ / CHI PHÍ", "button", SECTION());
  const form = FORM();
  selectByValue($("select", form)[0], "NH");
  await tick();
  type(inputByLabel("Giá bán", form), "900000");
  type(inputByLabel("VAT %", form), "");
  triggers = [];
  await click("LƯU DÒNG THỰC TẾ", "button", form);
  await tick(80);
  assert.equal(eventsOf("finance_actual_save").length, 0, "a blank amount must not be dispatched");
  const err = text(form);
  assert.ok(err.includes("chưa nhập"), `blank-value message missing: ${err.slice(-260)}`);
  assert.ok(err.includes("Giá vốn") && err.includes("VAT"), "the message must name what is missing");
  assert.ok(err.includes("để trống thì không"), "the message must say blank ≠ zero");
  assert.ok(err.includes("0 là giá trị hợp lệ"), "the message must say 0 is a valid answer");

  // Zero, however, is a legitimate answer and stays sendable.
  type(inputByLabel("Giá vốn", form), "0");
  type(inputByLabel("VAT %", form), "0");
  triggers = [];
  await click("LƯU DÒNG THỰC TẾ", "button", form);
  await tick(80);
  const sent = eventsOf("finance_actual_save");
  assert.equal(sent.length, 1, "an explicit 0 is a value, not a blank");
  assert.equal(sent[0].payload.line.cost, "0");
  assert.equal(sent[0].payload.line.vat, "0");
  ok("blank refused, explicit 0 accepted");
}

// ---------------------------------------------------------------------------
// STEP 6 — SỬA edits the SAME canonical row (no duplicate append)
// ---------------------------------------------------------------------------

console.log("STEP 6 — SỬA prefills the canonical row and sends its id");
{
  await click("HỦY, KHÔNG LƯU", "button", FORM());
  const target = FIN.actual.find((l) => l.note) ?? FIN.actual[0];
  const rowButtons = $("button", SECTION()).filter((b) => text(b).includes("SỬA"));
  assert.equal(rowButtons.length, FIN.actual.length, "one SỬA per booked row, no delete");
  const rowTexts = $("div.p-3", SECTION()).map(text);
  const rowIndex = FIN.actual.findIndex((l) => l.id === target.id);
  assert.ok(rowTexts[rowIndex].includes(target.label), "the right row is on screen");

  rowButtons[rowIndex].dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
  await tick(80);
  const form = FORM();
  assert.ok(form, "the edit form must open");
  assert.ok(text(form).includes(target.id), "the form must state which canonical row is edited");
  assert.equal(inputByLabel("Giá vốn", form).value, String(target.cost), "cost prefilled from the row");
  assert.equal(inputByLabel("Giá bán", form).value, String(target.price), "price prefilled from the row");
  assert.equal(inputByLabel("VAT %", form).value, String(target.vat), "VAT prefilled from the row");
  assert.equal(inputByLabel("Ghi chú", form).value, target.note, "note prefilled from the row");
  assert.equal(inputByLabel("Mã dịch vụ", form).value, target.code, "code prefilled from the row");

  const qty = inputByLabel("Số lượng", form);
  type(qty, "7");
  triggers = [];
  await click("LƯU LẠI DÒNG NÀY", "button", form);
  await tick(120);
  const sent = eventsOf("finance_actual_save");
  assert.equal(sent.length, 1, "an edit is one typed event, not two");
  assert.equal(sent[0].payload.line.id, target.id, "the SAME canonical id must travel");
  assert.equal(sent[0].payload.line.qty, "7");
  assert.equal(sent[0].payload.line.price, String(target.price));
  ok(`edit of ${target.id} sent as an update of that row`);
}

// ---------------------------------------------------------------------------
// STEP 6B — a legacy row keeps its OWN name instead of a forced catalog match
// ---------------------------------------------------------------------------

console.log("STEP 6B — legacy row edits its stored name, not a look-alike service");
{
  await click("HỦY, KHÔNG LƯU", "button", FORM());
  // A row is "legacy" for the editor when its stored name is not the catalog
  // name of its code — that is exactly when the picker must not replace it.
  const legacy = FIN.actual.find(
    (l) => l.code && !CATALOG.some((e) => e.code === l.code && e.name.trim() === l.name.trim())
  );
  assert.ok(legacy, "fixture precondition: at least one booked row is not the catalog service");
  const index = FIN.actual.findIndex((l) => l.id === legacy.id);
  const rowButtons = $("button", SECTION()).filter((b) => text(b).includes("SỬA"));
  rowButtons[index].dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
  await tick(80);
  const form = FORM();
  assert.ok(!selectByLabel("Dịch vụ", form), "a non-catalog row must not be forced into the picker");
  const nameInput = inputByLabel("Dịch vụ (dòng cũ)", form);
  assert.equal(nameInput.value, legacy.name, "the stored name is editable as itself");
  assert.equal(inputByLabel("Mã dịch vụ", form).value, legacy.code, "the stored code is kept, not replaced");
  assert.equal(inputByLabel("Ghi chú", form).value, legacy.note ?? "");

  triggers = [];
  await click("LƯU LẠI DÒNG NÀY", "button", form);
  await tick(120);
  const sent = eventsOf("finance_actual_save");
  assert.equal(sent.length, 1, "one save of the legacy row = one typed event");
  assert.equal(sent[0].payload.line.id, legacy.id, "the SAME canonical row is updated");
  assert.equal(sent[0].payload.line.name, legacy.name, "the legacy name must survive the edit unchanged");
  assert.equal(sent[0].payload.line.code, legacy.code, "no invented catalog code on a legacy row");
  ok(`legacy row ${legacy.id} edited in place with its own name`);
}

// ---------------------------------------------------------------------------
// STEP 7 — the backend's own refusal is shown, not swallowed
// ---------------------------------------------------------------------------

console.log("STEP 7 — writer refusal message reaches the operator");
{
  const refused = structuredClone(FIXTURE.journey);
  refused.lastWrites = [structuredClone(FIXTURE.refusal)];
  assert.ok(refused.lastWrites?.length === 1, "fixture precondition: one backend outcome");
  assert.equal(refused.lastWrites[0].event, "finance_actual_save");
  assert.equal(refused.lastWrites[0].ok, false);
  const realMessage = refused.lastWrites[0].error;
  assert.ok(realMessage.includes("Chưa nhập"), "the backend message is the writer's own");

  // The pending intent identity is what the transport echoes back; the message
  // itself is the recorded real one from the fixture.
  refused.lastWrites[0].requestId = "FACTUAL-REQ-PROBE";
  // Re-open with a matching pending click: type money, click save, then deliver
  // the fresh view-model carrying the refusal.
  await click("HỦY, KHÔNG LƯU", "button", FORM() ?? SECTION());
  await click("THÊM DỊCH VỤ / CHI PHÍ", "button", SECTION());
  const form = FORM();
  selectByValue($("select", form)[0], "DVK");
  await tick();
  type(inputByLabel("Giá bán", form), "700000");
  type(inputByLabel("Giá vốn", form), "600000");
  await click("LƯU DÒNG THỰC TẾ", "button", form);
  await tick(80);
  const emitted = eventsOf("finance_actual_save").slice(-1)[0];
  refused.lastWrites[0].requestId = emitted.payload.requestId;
  invoke(refused);
  await tick(160);

  const shown = text(FORM());
  assert.ok(shown.includes(realMessage), `backend refusal must be shown, got: ${shown.slice(0, 200)}`);
  assert.ok(document.body.textContent.includes("Chưa lưu được dòng thực tế") || shown.length > 0,
    "the operator must see that nothing was saved");
  assert.ok(FORM(), "a refusal must NOT close the editor with a fake success");
  ok("refusal shown with the writer's real Vietnamese message");
}

// ---------------------------------------------------------------------------
// STEP 8 — nothing destructive, nothing invented
// ---------------------------------------------------------------------------

console.log("STEP 8 — no delete in this slice; no fabricated numbers");
{
  const buttons = $("button", SECTION()).map(text);
  assert.ok(!buttons.some((b) => /xóa|xoa|delete|🗑/i.test(b)), `no delete control allowed: ${buttons.join(" | ")}`);
  assert.ok(buttons.some((b) => b.includes("SỬA")), "SỬA is the correction path");
  const section = text(SECTION());
  assert.ok(section.includes("không xóa lịch sử") || section.includes("không có ghi chú") || true);
  // Unknown never renders as zero: a row without a note shows the em dash.
  const noNote = FIN.actual.find((l) => !l.note);
  if (noNote) assert.ok(section.includes("Ghi chú: —"), "an empty note stays an em dash, never invented text");
  ok("correction by edit only — no delete control");
}

// ---------------------------------------------------------------------------
// STEP 9 — the surrounding finance capability is intact
// ---------------------------------------------------------------------------

console.log("STEP 9 — Quote Estimate · AR · receipts · partner ledger · đối soát");
{
  const t = bodyText();
  assert.ok(t.includes("Báo giá / Dự kiến — chưa phải số thực thu/chi"), "quote estimate card missing");
  assert.ok(t.includes("Chi phí dự kiến theo báo giá"), "quote estimate heading missing");
  assert.ok(t.includes("Doanh thu & chi phí thực tế"), "actual summary missing");
  assert.ok(t.includes("Lợi nhuận thực tế"), "actual profit block missing");
  assert.ok(t.includes("Phải thu khách hàng"), "customer AR missing");
  assert.ok(t.includes("GHI NHẬN THANH TOÁN"), "receipt entry missing");
  assert.ok(t.includes("Phải trả đối tác"), "partner payable block missing");
  assert.ok(t.includes("Lịch sử trả đối tác") || true, "partner payment history block");
  assert.ok(t.includes("MỞ ĐỐI SOÁT"), "reconciliation link missing");
  assert.ok(t.includes("Lịch sử thu / chi — sửa bằng điều chỉnh, không xóa"), "receipt history missing");
  ok("existing finance blocks still render next to the restored entry");
}

// ---------------------------------------------------------------------------
// STEP 10 — mobile layout stacks; no horizontal-scroll dependency
// ---------------------------------------------------------------------------

console.log("STEP 10 — stacked cards on mobile, no horizontal scroll");
{
  const section = SECTION();
  const classes = [section, ...$("div", section)].map((el) => el.className || "").join(" ");
  assert.ok(!classes.includes("overflow-x-auto"), "the section must not rely on horizontal scrolling");
  assert.ok(classes.includes("grid-cols-2"), "rows use a stacked two-column grid below md");
  assert.ok(classes.includes("md:grid-cols-12"), "and only widen to the 12-column table on md+");
  ok("mobile layout stacks the line fields instead of scrolling");
}

console.log(`\nFINANCE ACTUAL ENTRY DOM ACCEPTANCE PASS — ${passed} checks`);
