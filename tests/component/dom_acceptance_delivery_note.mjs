/**
 * LOG #156 — DOM acceptance for the "Phiếu giao hàng XLSX" generator surface
 * on the shipment detail "Nhập khẩu & Giao hàng" tab.
 *
 * Runs the REAL production bundle (component/dist/logi-shell.js, rebuilt from
 * the CURRENT source tree) in jsdom and drives it with real DOM events, over
 * the real staging view-model fixture
 * (tests/component/fixtures/view_model_document_review.json). The panel gates
 * on `importInfo.delivered`, so the harness flips only that one fact.
 *
 *   1. NOT delivered: neither the panel nor the generate button is an
 *      executable action; "XÁC NHẬN ĐÃ GIAO HÀNG" is still offered.
 *   2. Delivered: the panel renders, both identity inputs start BLANK, and no
 *      automatic today's date is injected anywhere in the rendered page.
 *   3. Blank identity: clicking emits NO `delivery_note_generate` event and the
 *      operator is told why nothing was created (no silent auto-numbering).
 *   4. Valid identity: one click emits EXACTLY ONE `delivery_note_generate`
 *      event whose payload is bounded to
 *      { shipmentId, deliveryNoteNo, deliveryNoteDate } — no file bytes, no
 *      base64, no template path, no browser-generated legal content.
 *   5. Transport success is NOT persistence success: a `dispatch` that merely
 *      returns true makes the UI say the request was SENT, never that a durable
 *      document was created/saved.
 *
 * NOTE ON NAVIGATION: the shipments list defaults to "THÁNG NÀY + ĐANG LÀM",
 * and this committed fixture's lots are dated 26/09/2026. As the wall clock
 * moves past that month the lots fall outside the default window, so the
 * harness widens the period chip before opening the lot. This is the SAME
 * pre-existing fixture/wall-clock drift that makes
 * dom_acceptance_shipment_document_review.mjs, dom_acceptance_shipment_
 * attachments.mjs and dom_acceptance_shipment_slash_id.mjs unrunnable as of
 * 2026-10-01 — verified identical on unmodified `main`, i.e. not a #156/#157
 * regression. It is worked around here with a UI click, not a source change.
 *
 * Run: node tests/component/dom_acceptance_delivery_note.mjs
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
const SHIPMENT_ID = RAW.fixture.shipmentId; // LO-0306

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
} catch {}
for (const k of [
  "HTMLElement", "HTMLInputElement", "HTMLTextAreaElement", "HTMLSelectElement",
  "HTMLAnchorElement", "HTMLButtonElement", "Event", "CustomEvent", "MouseEvent",
  "KeyboardEvent", "FocusEvent", "Node", "Element", "DocumentFragment",
  "MutationObserver", "File", "FileReader", "Blob", "getComputedStyle",
]) globalThis[k] = window[k];
if (!globalThis.MessageChannel) globalThis.MessageChannel = window.MessageChannel;
window.HTMLElement.prototype.scrollIntoView = () => {};
window.URL.createObjectURL = () => "blob:mock-url";
window.URL.revokeObjectURL = () => {};
if (globalThis.URL) {
  globalThis.URL.createObjectURL = () => "blob:mock-url";
  globalThis.URL.revokeObjectURL = () => {};
}
window.HTMLAnchorElement.prototype.click = function recordClick() {};

const tick = (ms = 90) => new Promise((r) => setTimeout(r, ms));
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
function invoke(data) {
  return mountRef.current({
    name: "logi_shell",
    data,
    parentElement: host,
    setTriggerValue: (event, value) => triggers.push({ event, value }),
  });
}
const clone = (o) => JSON.parse(JSON.stringify(o));
const dnEvents = () => triggers.filter((t) => t.event === "delivery_note_generate");

/** The panel gates on `importInfo.delivered`, so flip only that fact. */
function modelWith({ delivered }) {
  const next = clone(RAW);
  const ship = next.shipments.find((s) => s.id === SHIPMENT_ID);
  assert.ok(ship, `fixture shipment ${SHIPMENT_ID} missing`);
  ship.importInfo.delivered = delivered;
  ship.importInfo.actualDelivery = delivered ? "15/08/2026" : "";
  return next;
}

/** React-controlled input: use the native value setter, then fire `input`. */
function setInput(el, value) {
  const desc = Object.getOwnPropertyDescriptor(Object.getPrototypeOf(el), "value");
  desc.set.call(el, value);
  el.dispatchEvent(new window.Event("input", { bubbles: true }));
}

async function gotoDeliveryTab() {
  await click("Lô Hàng", "a", $("aside")[0]);
  // The list defaults to "THÁNG NÀY + ĐANG LÀM". The committed fixture's lots
  // are dated 26/09/2026, so a static fixture drifts outside that window as the
  // wall clock moves. Widen the period (UI-only) so the lot is reachable.
  await click("Tất cả thời gian", "button");
  await click(SHIPMENT_ID, "a", $("table.tbl")[0]);
  const tabs = window.document.getElementById("workspace-tabs");
  assert.ok(tabs, "workspace tabs must exist");
  await click("Nhập khẩu & Giao hàng", "button", tabs);
}

const mod = await import(bundlePath);
assert.equal(typeof mod.default, "function", "bundle must default-export mount");
mountRef.current = mod.default;

let checks = 0;
const ok = (label) => {
  checks += 1;
  console.log(`PASS | ${label}`);
};

const TODAY_DMY = (() => {
  const d = new Date();
  const p = (n) => String(n).padStart(2, "0");
  return `${p(d.getDate())}/${p(d.getMonth() + 1)}/${d.getFullYear()}`;
})();
const TODAY_ISO = new Date().toISOString().slice(0, 10);

// ===========================================================================
// D. NOT delivered — the generator must not be an executable action.
// ===========================================================================
invoke(modelWith({ delivered: false }));
await tick(150);
await gotoDeliveryTab();
{
  const body = mainText();
  assert.ok(!body.includes("Phiếu giao hàng XLSX"), "panel must not render when not delivered");
  assert.equal(findClickable("TẠO PHIẾU GIAO HÀNG XLSX"), null, "button must not exist when not delivered");
  ok("D1 not delivered => no 'Phiếu giao hàng XLSX' panel");
  ok("D2 not delivered => no TẠO PHIẾU GIAO HÀNG XLSX button");
  assert.ok(body.includes("XÁC NHẬN ĐÃ GIAO HÀNG"), "deliver action must still be offered");
  ok("D3 not delivered => XÁC NHẬN ĐÃ GIAO HÀNG still offered");
}

// ===========================================================================
// A/B/C/E. Delivered shipment.
// ===========================================================================
invoke(modelWith({ delivered: true }));
await tick(150);
await gotoDeliveryTab();

const noInput = window.document.querySelector('input[placeholder="VD: PGH-2026-001"]');
const dateInput = window.document.querySelector('input[placeholder="VD: 30/09/2026"]');
const button = findClickable("TẠO PHIẾU GIAO HÀNG XLSX");

// --- A ---
assert.ok(mainText().includes("Phiếu giao hàng XLSX"), "panel must render when delivered");
ok("A1 delivered => panel 'Phiếu giao hàng XLSX' rendered");
assert.ok(noInput, "delivery-note number input missing");
assert.equal(noInput.value, "", "number input must start blank");
ok("A2 number input starts blank");
assert.ok(dateInput, "delivery-note date input missing");
assert.equal(dateInput.value, "", "date input must start blank");
ok("A3 date input starts blank");
assert.ok(dateInput.value !== TODAY_DMY && dateInput.value !== TODAY_ISO, "no auto today's date");
assert.ok(!mainText().includes(TODAY_DMY), `no auto today's date anywhere (${TODAY_DMY})`);
ok("A4 no automatic today's date");
assert.ok(button, "generate button missing");
ok("A5 button TẠO PHIẾU GIAO HÀNG XLSX visible");

// --- B: missing identity emits NO event ---
assert.equal(dnEvents().length, 0, "no events before click");
button.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
await tick();
assert.equal(dnEvents().length, 0, "blank identity must NOT dispatch delivery_note_generate");
ok("B1 blank number+date => NO delivery_note_generate event");
const toastTextEarly = $(".toast-in").map(text).join(" | ");
assert.ok(
  toastTextEarly.includes("Chưa tạo được Phiếu giao hàng"),
  `operator must be told why nothing was sent; toasts=[${toastTextEarly}]`,
);
ok("B2 blank identity => operator is told nothing was created");

// --- C: valid identity emits exactly ONE bounded event ---
setInput(noInput, "PGH-2026-001");
setInput(dateInput, "2026-08-15");
await tick();
assert.equal(
  window.document.querySelector('input[placeholder="VD: PGH-2026-001"]').value,
  "PGH-2026-001",
  "number input must reflect typed value",
);
assert.equal(
  window.document.querySelector('input[placeholder="VD: 30/09/2026"]').value,
  "2026-08-15",
  "date input must reflect typed value",
);
ok("C1 inputs accept operator-supplied number and date");

findClickable("TẠO PHIẾU GIAO HÀNG XLSX").dispatchEvent(
  new window.MouseEvent("click", { bubbles: true, cancelable: true }),
);
await tick();
const evs = dnEvents();
assert.equal(evs.length, 1, `expected exactly 1 event, got ${evs.length}`);
ok("C2 one click => exactly ONE delivery_note_generate event");
const payload = evs[0].value?.payload ?? {};
assert.equal(payload.shipmentId, SHIPMENT_ID, "payload must carry shipmentId");
assert.equal(payload.deliveryNoteNo, "PGH-2026-001", "payload must carry deliveryNoteNo");
assert.equal(payload.deliveryNoteDate, "2026-08-15", "payload must carry deliveryNoteDate");
ok("C3 payload carries shipmentId + deliveryNoteNo + deliveryNoteDate");

const serialized = JSON.stringify(payload);
for (const banned of ["base64", "templatePath", "template", "bytes", "content", "fileBytes"]) {
  assert.ok(
    !serialized.toLowerCase().includes(banned.toLowerCase()),
    `payload must not carry ${banned}`,
  );
}
ok("C4 payload carries no file bytes/base64/template path/legal content");
assert.deepEqual(
  Object.keys(payload).sort(),
  ["deliveryNoteDate", "deliveryNoteNo", "shipmentId"],
  `payload keys must be bounded, got ${Object.keys(payload).sort()}`,
);
ok("C5 payload key set is exactly the bounded identity triple");

// --- E: transport success is NOT persistence success ---
const toastText = $(".toast-in").map(text).join(" | ");
assert.ok(toastText.length > 0, "a toast must be shown after dispatch");
assert.ok(toastText.includes("Đã gửi yêu cầu"), `toast must say request sent, got: ${toastText}`);
ok("E1 dispatch-true => UI says the request was SENT");
for (const claim of ["Đã tạo", "Đã lưu", "thành công", "hoàn tất", "ĐÃ GIAO"]) {
  assert.ok(!toastText.includes(claim), `toast must not claim durable success ("${claim}")`);
}
ok("E2 dispatch-true => UI does NOT claim durable document success");

console.log(`\nDELIVERY_NOTE_DOM: ${checks}/${checks} checks passed`);
