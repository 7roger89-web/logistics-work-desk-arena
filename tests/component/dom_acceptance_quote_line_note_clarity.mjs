// ============================================================================
// LOGI_QUOTE_LINE_NOTE_CLARITY_01 — DOM acceptance for Issue #90 (real bundle).
//
// Runs the committed production bundle (component/dist/logi-shell.js) in a DOM
// runtime and proves the Owner's exact contract on the Báo Giá desk:
//
//   1. ONE CARD = ONE SERVICE LINE. With one line there is exactly one card,
//      visibly titled "Dòng dịch vụ 1", and exactly ONE note field labelled
//      "Ghi chú dòng này" living INSIDE that card — with mã dịch vụ / tên dịch
//      vụ / số lượng / giá vốn / giá bán / thuế / tiền tệ.
//   2. "Thêm dòng" creates a separate card whose note is independently blank
//      (line_count === note_count, no quote-level shared note).
//   3. LINE 1 NOTE=A + LINE 2 NOTE=B -> quote_create payload keeps A on
//      serviceLines[0] and B on serviceLines[1], aligned with each line's code.
//   4. Fresh readback: a quote re-opened from the projection shows A on line 1
//      and B on line 2 (each note inside its own card).
//   5. Edit line 2 -> B2 only: line 1's note stays A in the DOM and in the
//      quote_edit payload, and a fresh readback of that edit still shows A/B2.
//   6. Removing line 1 removes only that line and its note: the surviving line
//      keeps ITS OWN note (B2) and A disappears from the payload entirely.
//   7. The per-line identity + note block are structurally inside the card at
//      both viewport classes (mobile 2-col grid / desktop md:grid-cols-4),
//      with a visible (non-sr-only) line badge preceding the note block.
//
// Run: node tests/component/dom_acceptance_quote_line_note_clarity.mjs
// ============================================================================

import { readFileSync } from "node:fs";
import assert from "node:assert/strict";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const require = createRequire(path.join(ROOT, "component/package.json"));
const { JSDOM } = require("jsdom");
const VM = JSON.parse(
  readFileSync(path.join(ROOT, "tests/component/fixtures/view_model_phase_b.json"), "utf8")
);
const CW = JSON.parse(
  readFileSync(path.join(ROOT, "tests/component/fixtures/view_model_contract_workflow.json"), "utf8")
);
if (Array.isArray(CW.success?.quotes) && CW.success.quotes.length > 0) {
  VM.quotes = CW.success.quotes;
}

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
  "Node", "MutationObserver", "getComputedStyle", "TextEncoder",
]) {
  globalThis[k] = window[k];
}
if (!globalThis.MessageChannel) globalThis.MessageChannel = window.MessageChannel;
window.HTMLElement.prototype.scrollIntoView = () => {};
window.URL.createObjectURL = () => "blob:mock-url";
window.URL.revokeObjectURL = () => {};

const tick = (ms = 80) => new Promise((r) => setTimeout(r, ms));
const $ = (sel, root = window.document) => [...root.querySelectorAll(sel)];
const text = (el) => (el.textContent || "").replace(/\s+/g, " ").trim();
const mainText = () => text($("main")[0] ?? window.document.body);
const aside = () => $("aside")[0];
const byTestId = (id) => $(`[data-testid="${id}"]`)[0] ?? null;
const allTestIds = () => $("[data-testid]").map((el) => el.getAttribute("data-testid"));
const cardCount = () => allTestIds().filter((id) => /^quote-line-\d+$/.test(id)).length;
const noteCount = () => allTestIds().filter((id) => /^quote-line-\d+-note$/.test(id)).length;

function findClickable(needle, sel = "a,button", root = window.document) {
  const els = $(sel, root);
  return els.find((el) => text(el) === needle) || els.find((el) => text(el).startsWith(needle)) || null;
}
async function click(needle, sel = "a,button", root = window.document) {
  const el = findClickable(needle, sel, root);
  assert.ok(el, `clickable "${needle}" not found`);
  el.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
  await tick();
  return el;
}
async function clickSelector(sel, root = window.document, index = 0) {
  const el = $(sel, root)[index];
  assert.ok(el, `selector "${sel}[${index}]" not found`);
  el.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
  await tick();
  return el;
}
async function typeInput(input, value) {
  assert.ok(input, "typeInput target missing");
  const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
  setter.call(input, value);
  input.dispatchEvent(new window.Event("input", { bubbles: true }));
  await tick(120);
}

let passed = 0;
function ok(name) {
  passed += 1;
  console.log(`  ✓ ${name}`);
}
function expectedTrigger(event, from) {
  const ev = triggers.slice(from).find((t) => t.event === event);
  assert.ok(ev, `${event} trigger not emitted`);
  return ev.value.payload;
}

const NOTE_A = "Giá đã gồm bốc xếp";
const NOTE_B = "Chưa gồm kiểm hóa";
const NOTE_B2 = "Chưa gồm kiểm hóa — khách tự làm";

function lineFixture(code, name, note, sell = 1000, cost = 900) {
  return {
    code, serviceName: name, unit: "Lần", qty: 1, currency: "VND",
    costUnit: cost, sellUnit: sell, taxPct: 0, note,
  };
}
function quoteFixture(id, lines) {
  return {
    id, quoteNo: id, customerId: "CUST-ANPHAT", customer: "An Phát JSC",
    salesOwner: "Minh Tú", status: "DRAFT", statusLabel: "Nháp",
    origin: "Bằng Tường", destination: "KCN Quế Võ", route: "Hữu Nghị",
    incoterm: "DAP", transportMode: "Road", goodsDescription: "Linh kiện",
    expectedDeliveryDate: "2026-09-20", currency: "VND", total: 1000,
    sellingPriceTotalVnd: 1000, fxRatesToVnd: {}, fxNeededFor: [],
    serviceLines: lines, assumptions: [], statusHistory: [], version: 1,
    shipmentId: "", allowedTransitions: ["READY_FOR_REVIEW"],
  };
}
const vmWithQuote = (id, lines) => {
  const copy = JSON.parse(JSON.stringify(VM));
  copy.quotes = [quoteFixture(id, lines)];
  return copy;
};

const host = window.document.createElement("div");
window.document.body.appendChild(host);
const triggers = [];
const mod = await import(path.join(ROOT, "component/dist/logi-shell.js"));
assert.equal(typeof mod.default, "function");
let cleanup = mod.default({
  name: "logi_shell", data: VM, parentElement: host,
  setTriggerValue: (event, value) => triggers.push({ event, value }),
});
await tick(150);

async function mountWith(vm) {
  cleanup();
  await tick(60);
  cleanup = mod.default({
    name: "logi_shell", data: vm, parentElement: host,
    setTriggerValue: (event, value) => triggers.push({ event, value }),
  });
  await tick(150);
}
const noteIn = (n) => byTestId(`quote-line-${n}-note`);
const card = (n) => byTestId(`quote-line-${n}`);
const fieldIn = (n, placeholder) => card(n).querySelector(`input[placeholder="${placeholder}"]`);

// ---------------------------------------------------------------------------
console.log("STEP 1 — one line: one card, one visible identity, one note inside it");
{
  await click("Báo Giá", "a", aside());
  assert.ok(mainText().includes("Báo Giá"), "quote page title missing");
  await click("Tạo báo giá", "button");

  assert.equal(cardCount(), 1, "a single-line quote must render exactly one line card");
  assert.equal(noteCount(), 1, "the single line must own exactly one note field");
  assert.equal($('[data-testid="quote-line-2"]').length, 0, "phantom line 2 card");

  const c1 = card(1);
  assert.ok(c1, "service-line card 1 missing");
  assert.ok(text(c1).includes("Dòng dịch vụ 1"), "card 1 has no visible line identity");
  assert.ok(text(c1).includes("Ghi chú dòng này"), "card 1 has no per-line note label");
  // Every canonical per-line field lives in the SAME card as that note.
  for (const label of [
    "Mã dịch vụ", "Tên dịch vụ", "Số lượng", "Giá vốn (unit)",
    "Giá bán (unit)", "Thuế %", "Tiền tệ",
  ]) {
    assert.ok(text(c1).includes(label), `"${label}" is not inside the note's own card`);
  }
  const block = byTestId("quote-line-1-note-block");
  assert.ok(block && c1.contains(block), "note block is not physically inside line card 1");
  assert.ok(c1.contains(noteIn(1)), "note input is not physically inside line card 1");
  assert.equal(noteIn(1).value, "", "a fresh line must start with a blank note");
  assert.equal(noteIn(1).disabled, false, "note input is not editable");
  assert.ok(
    mainText().includes("Mỗi dòng dịch vụ có ô ghi chú riêng của chính dòng đó"),
    "the desk does not state per-line note ownership"
  );
  ok("line 1 card carries identity + its own 'Ghi chú dòng này' beside code/name/qty/cost/sell/tax/currency");
}

// ---------------------------------------------------------------------------
console.log("STEP 2 — 'Thêm dòng' creates a separate line with its own blank note");
{
  await clickSelector('[data-testid="quote-add-line"]');
  assert.equal(cardCount(), 2, "adding a line did not create a second card");
  assert.equal(noteCount(), 2, "line_count != note_count after adding a line");
  assert.ok(text(card(2)).includes("Dòng dịch vụ 2"), "card 2 has no visible line identity");
  assert.ok(text(card(2)).includes("Ghi chú dòng này"), "card 2 has no per-line note label");
  assert.ok(card(2).contains(noteIn(2)), "note 2 is not inside card 2");
  assert.notEqual(noteIn(1), noteIn(2), "both lines share one note input");
  assert.equal(noteIn(1).value, "", "new line polluted line 1's note");
  assert.equal(noteIn(2).value, "", "the new line's note is not independently blank");
  ok("2 cards / 2 independent note inputs; the new note starts blank");
}

// ---------------------------------------------------------------------------
console.log("STEP 3 — LINE 1 NOTE=A + LINE 2 NOTE=B travels on the right line");
{
  await clickSelector('[data-testid="quote-customer-picker-toggle"]');
  await typeInput(byTestId("quote-customer-picker-search"), "an phat");
  await clickSelector('[data-testid="quote-customer-picker-option-CUST-ANPHAT"]');

  await typeInput(fieldIn(1, "DV-VC-TQ"), "DV-VC-TQ");
  await typeInput(fieldIn(1, "Cước xe TQ"), "Cước xe TQ");
  await typeInput(fieldIn(2, "DV-VC-TQ"), "DV-TQ");
  await typeInput(fieldIn(2, "Cước xe TQ"), "Thông quan");
  // Numeric fields in card order: [Số lượng, Giá vốn (unit), Giá bán (unit), Thuế %].
  const numeric = (n) => [...card(n).querySelectorAll('input[inputmode="numeric"]')];
  assert.equal(numeric(1).length, 4, "unexpected numeric field layout in line 1");
  await typeInput(numeric(1)[1], "26000000");
  await typeInput(numeric(1)[2], "28500000");
  await typeInput(numeric(2)[1], "2500000");
  await typeInput(numeric(2)[2], "3000000");
  await typeInput(noteIn(1), NOTE_A);
  await typeInput(noteIn(2), NOTE_B);
  assert.equal(noteIn(1).value, NOTE_A);
  assert.equal(noteIn(2).value, NOTE_B);

  const before = triggers.length;
  await click("💾 TẠO BÁO GIÁ", "button");
  const payload = expectedTrigger("quote_create", before);
  assert.equal(payload.serviceLines.length, 2, "payload lost a service line");
  assert.deepEqual(payload.serviceLines.map((l) => l.note), [NOTE_A, NOTE_B],
    "notes are not attached to their own serviceLines indexes");
  assert.deepEqual(payload.serviceLines.map((l) => l.code), ["DV-VC-TQ", "DV-TQ"],
    "notes are misaligned with the service lines they belong to");
  assert.deepEqual(payload.serviceLines.map((l) => l.costUnit), [26000000, 2500000]);
  assert.deepEqual(payload.serviceLines.map((l) => l.sellUnit), [28500000, 3000000]);
  assert.deepEqual(payload.serviceLines.map((l) => l.taxPct), [8, 8]);
  console.log(`    quote_create.serviceLines = ${JSON.stringify(
    payload.serviceLines.map((l) => ({ code: l.code, costUnit: l.costUnit, sellUnit: l.sellUnit, note: l.note }))
  )}`);
  ok(`quote_create payload keeps [0].note="${NOTE_A}" / [1].note="${NOTE_B}"`);
}

// ---------------------------------------------------------------------------
console.log("STEP 4 — fresh readback restores each note to its own line");
{
  await mountWith(vmWithQuote("Q-TEST-2", [
    lineFixture("DV-VC-TQ", "Cước xe TQ", NOTE_A),
    lineFixture("DV-TQ", "Thông quan", NOTE_B),
  ]));
  await click("Báo Giá", "a", aside());
  await click("Sửa", "button");

  assert.equal(cardCount(), 2, "saved two-line quote did not reopen two cards");
  assert.ok(text(card(1)).includes("Dòng dịch vụ 1"));
  assert.ok(text(card(2)).includes("Dòng dịch vụ 2"));
  assert.equal(fieldIn(1, "DV-VC-TQ").value, "DV-VC-TQ");
  assert.equal(fieldIn(2, "DV-VC-TQ").value, "DV-TQ");
  assert.equal(noteIn(1).value, NOTE_A, "line 1 did not read back its own note");
  assert.equal(noteIn(2).value, NOTE_B, "line 2 did not read back its own note");
  assert.ok(card(1).contains(noteIn(1)) && card(2).contains(noteIn(2)),
    "a read-back note rendered outside its own card");
  assert.ok(!card(1).contains(noteIn(2)) && !card(2).contains(noteIn(1)),
    "notes are not scoped to their own cards");
  ok("fresh readback: line 1 = A, line 2 = B, each inside its own card");
}

// ---------------------------------------------------------------------------
console.log("STEP 5 — edit line 2 only: line 1 keeps A in DOM + payload + readback");
{
  await typeInput(noteIn(2), NOTE_B2);
  assert.equal(noteIn(1).value, NOTE_A, "typing in line 2 changed line 1's note");
  assert.equal(fieldIn(1, "DV-VC-TQ").value, "DV-VC-TQ", "typing a note moved line 1's data");

  const before = triggers.length;
  await click("💾 LƯU BÁO GIÁ", "button");
  const payload = expectedTrigger("quote_edit", before);
  assert.deepEqual(payload.serviceLines.map((l) => l.note), [NOTE_A, NOTE_B2],
    "editing line 2's note did not leave line 1's note untouched");
  assert.deepEqual(payload.serviceLines.map((l) => l.code), ["DV-VC-TQ", "DV-TQ"]);
  console.log(`    quote_edit.serviceLines   = ${JSON.stringify(
    payload.serviceLines.map((l) => ({ code: l.code, note: l.note }))
  )}`);

  // Fresh readback of THAT edit (the persisted projection, presented again).
  await mountWith(vmWithQuote("Q-TEST-2", [
    lineFixture("DV-VC-TQ", "Cước xe TQ", NOTE_A),
    lineFixture("DV-TQ", "Thông quan", NOTE_B2),
  ]));
  await click("Báo Giá", "a", aside());
  await click("Sửa", "button");
  assert.equal(noteIn(1).value, NOTE_A, "line 1 STILL must be A after editing line 2");
  assert.equal(noteIn(2).value, NOTE_B2, "line 2 did not persist B2");
  ok(`line 1 STILL="${NOTE_A}", line 2="${NOTE_B2}" in DOM, payload and readback`);
}

// ---------------------------------------------------------------------------
console.log("STEP 6 — removing line 1 removes only that line and its own note");
{
  await clickSelector('[data-testid="quote-line-1-remove"]');
  assert.equal(cardCount(), 1, "removing line 1 did not leave exactly one card");
  assert.equal(noteCount(), 1, "line_count != note_count after removing a line");
  const survivor = card(1);
  assert.equal(fieldIn(1, "DV-VC-TQ").value, "DV-TQ", "the wrong line survived");
  assert.equal(noteIn(1).value, NOTE_B2, "the surviving line lost its own note");
  assert.ok(text(survivor).includes("Dòng dịch vụ 1"), "surviving card lost its identity");
  assert.ok(!mainText().includes(NOTE_A), "the deleted line's note is still on screen");

  const before = triggers.length;
  await click("💾 LƯU BÁO GIÁ", "button");
  const payload = expectedTrigger("quote_edit", before);
  assert.equal(payload.serviceLines.length, 1, "payload kept the deleted line");
  assert.equal(payload.serviceLines[0].note, NOTE_B2, "note migration detected");
  assert.equal(payload.serviceLines[0].code, "DV-TQ");
  assert.ok(!JSON.stringify(payload).includes(NOTE_A),
    "the deleted line's note survived in the payload");
  console.log(`    after delete line 1       = ${JSON.stringify(
    payload.serviceLines.map((l) => ({ code: l.code, note: l.note }))
  )}`);
  ok("deleted line takes ONLY its own note; survivor keeps B2");
}

// ---------------------------------------------------------------------------
console.log("STEP 7 — per-line ownership is structurally visible (mobile + desktop)");
{
  await mountWith(vmWithQuote("Q-TEST-7", [
    lineFixture("DV-VC-TQ", "Cước xe TQ", NOTE_A),
    lineFixture("DV-TQ", "Thông quan", NOTE_B),
  ]));
  await click("Báo Giá", "a", aside());
  await click("Sửa", "button");

  assert.equal(noteCount(), cardCount(), "a note exists outside the line cards");
  for (const n of [1, 2]) {
    const c = card(n);
    const badge = c.querySelector(`[data-testid="quote-line-${n}-title"]`);
    assert.ok(badge, `line ${n} identity badge missing`);
    assert.equal(text(badge), `Dòng dịch vụ ${n}`);
    assert.ok(!badge.className.includes("sr-only"), `line ${n} identity is not visible`);
    // Visible order inside the card: identity badge -> fields -> this line's note.
    const order = [...c.querySelectorAll("[data-testid]")].map((el) => el.getAttribute("data-testid"));
    assert.ok(order.indexOf(`quote-line-${n}-title`) < order.indexOf(`quote-line-${n}-note`),
      `line ${n}: the note is not presented under its own line identity`);
    // The responsive field grid: 2 columns on mobile, 4 on md+.
    const grid = c.querySelector(".grid");
    assert.ok(grid && grid.className.includes("grid-cols-2") && grid.className.includes("md:grid-cols-4"),
      `line ${n}: field grid is not the responsive 2/4 column layout`);
    // Touch target + card containment for both viewport classes.
    assert.ok(noteIn(n).className.includes("min-h-[48px]"), `line ${n} note is under-sized on mobile`);
    assert.ok(c.className.includes("border-2"), `line ${n} card boundary is not explicit`);
    // Fieldset/legend keeps the group name programmatic for screen readers.
    const legend = c.querySelector("legend");
    assert.ok(legend && text(legend) === `Dòng dịch vụ ${n}`, `line ${n} legend missing`);
  }
  ok("badge + field grid + note block are all inside each card (mobile & desktop markup)");
}

console.log(`\nPASS — ${passed} checks`);
