// ============================================================================
// LOGI_CONTRACT_AND_SHIPMENT_CORE_GAPS_01 — DOM acceptance for the LOT HEADER
// on /lo-hang/<id>: the lot's creation date and the customer half of its name.
//
// Runs the REAL production bundle (component/dist/logi-shell.js) in jsdom over a
// REAL-backend fixture (scripts/gen_contract_shipment_edit_fixture.py). Every
// "after" state was produced by dispatching the very events this page sends —
// shipment_field_save {created_at} and shipment_customer_save — through the
// bounded dispatcher → RBAC → the existing canonical writers
// (save_shipment_atomic / core.database.update_shipment_customer) → audit → a
// fresh read. Verified contract:
//
//   1. the header renders both facts from the backend (date DD/MM/YYYY, name =
//      lot code · customer) and explains that the CODE is not an editable name
//   2. editing the date emits exactly ONE shipment_field_save with created_at,
//      and a blank is sent as blank (UNKNOWN) — never as today, never as 0
//   3. "sent" is not "saved": the rendered value only changes when the fresh
//      view-model carrying the backend read arrives
//   4. the customer is re-chosen through a real search and only travels as a
//      selection; clicking save with nothing picked dispatches NOTHING
//   5. a refused (RBAC) write leaves the page exactly at the stored values —
//      no locally invented success is ever displayed
//
// Run: node tests/component/dom_acceptance_shipment_header_edit.mjs
// ============================================================================

import { readFileSync } from "node:fs";
import assert from "node:assert/strict";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const require = createRequire(path.join(ROOT, "component/package.json"));
const { JSDOM } = require("jsdom");
const FIX = JSON.parse(
  readFileSync(path.join(ROOT, "tests/component/fixtures/view_model_contract_shipment_edit.json"), "utf8")
);
const LOT = FIX.shipment; // LO-0306

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

const tick = (ms = 60) => new Promise((r) => setTimeout(r, ms));
const $ = (sel, root = window.document) => [...root.querySelectorAll(sel)];
const text = (el) => (el.textContent || "").replace(/\s+/g, " ").trim();
const mainText = () => text($("main")[0] ?? window.document.body);
const bodyText = () => text(window.document.body);
const byTestId = (id) => $(`[data-testid="${id}"]`)[0] ?? null;
const attr = (id, name) => byTestId(id)?.getAttribute(name) ?? null;
const dateInput = () => $("#fld-created-at")[0];

function findClickable(needle, sel = "a,button", root = window.document) {
  const els = $(sel, root);
  return els.find((el) => text(el) === needle) || els.find((el) => text(el).includes(needle)) || null;
}

async function click(needle, sel = "a,button", root = window.document) {
  const el = findClickable(needle, sel, root);
  assert.ok(el, `clickable "${needle}" not found`);
  el.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
  await tick();
  return el;
}

async function clickTestId(id) {
  const el = byTestId(id);
  assert.ok(el, `element [data-testid="${id}"] not found`);
  el.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
  await tick();
  return el;
}

async function type(input, value) {
  assert.ok(input, "input element missing");
  Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set.call(input, value);
  input.dispatchEvent(new window.Event("input", { bubbles: true }));
  await tick();
}

let passed = 0;
function ok(name) {
  passed += 1;
  console.log(`  ✓ ${name}`);
}

const host = window.document.createElement("div");
window.document.body.appendChild(host);
const triggers = [];
const mountRef = { current: null };
let lastInvokeCleanup = null;

function invoke(data) {
  if (lastInvokeCleanup) lastInvokeCleanup();
  const cleanup = mountRef.current({
    name: "logi_shell",
    data,
    parentElement: host,
    setTriggerValue: (event, value) => triggers.push({ event, value }),
  });
  lastInvokeCleanup = cleanup;
  return cleanup;
}

/** A fresh view-model to the SAME mounted page — Streamlit rerun semantics: the
 *  operator's form state survives, only the read-back data changes. */
function deliver(data) {
  mountRef.current({
    name: "logi_shell",
    data,
    parentElement: host,
    setTriggerValue: (event, value) => triggers.push({ event, value }),
  });
}

async function bootOnLot(state) {
  invoke(state);
  await tick(120);
  await click("Lô Hàng", "a", $("aside")[0]);
  await click(LOT, "a", $("main")[0]);
  await tick(80);
}

const bundlePath = path.join(ROOT, "component/dist/logi-shell.js");

// ---------------------------------------------------------------------------
console.log("STEP 1 — the lot header shows both facts as the backend stored them");
{
  const mod = await import(bundlePath);
  assert.equal(typeof mod.default, "function");
  mountRef.current = mod.default;
  await bootOnLot(FIX.shipmentBefore);

  const card = byTestId("shipment-header-edit");
  assert.ok(card, "the lot-header edit card is missing");
  const cardText = text(card);
  assert.ok(cardText.includes("Tên lô & ngày tạo"), "card heading missing");
  assert.ok(cardText.includes(`Tên lô = ${LOT}`), "the name line must lead with the lot code");
  assert.ok(cardText.includes("An Phát JSC"), "the name line must carry the customer half");
  assert.equal(dateInput().value, "03/09/2026", "the stored creation date must be in the field");
  assert.equal(attr("shipment-customer-picker", "data-selected"), "CUST-ANPHAT");
  assert.equal(text(byTestId("shipment-customer-picker-value")), "An Phát JSC");
  // scope honesty: the code is explained as an identifier, not offered as a name
  assert.match(cardText, /Mã lô\s*LO-0306\s*là định danh và không đổi/);
  const cardInputs = $("input", card);
  assert.equal(cardInputs.length, 1, "the date is the only free input in this card");
  assert.equal(cardInputs[0].id, "fld-created-at");
  assert.ok(card.querySelector(`[data-testid="shipment-customer-picker"]`), "customer search must be the picker");
  assert.ok(!$("textarea", card).length, "no raw-id textarea for the lot code");
  ok("header renders date + name from the backend and keeps the code read-only");
}

// ---------------------------------------------------------------------------
console.log("STEP 2 — the date edit emits ONE shipment_field_save, sent ≠ saved");
{
  await type(dateInput(), "12/09/2026");
  const before = triggers.length;
  await click("LƯU NGÀY TẠO", "button");
  await tick(80);

  const saves = triggers.slice(before).filter((tr) => tr.event === "shipment_field_save");
  assert.equal(saves.length, 1, "exactly one shipment_field_save per click");
  assert.equal(saves[0].value.payload.shipmentId, LOT);
  assert.deepEqual(saves[0].value.payload.fields, { created_at: "12/09/2026" },
    "only the edited header fact may travel — no side fields");
  assert.equal(triggers.slice(before).filter((tr) => tr.event === "shipment_customer_save").length, 0);

  // Until the backend read arrives the page must still show the STORED value.
  assert.equal(dateInput().value, "03/09/2026", "an unconfirmed send must not look like a save");

  deliver(FIX.shipmentDateSaved);
  await tick(120);
  assert.equal(dateInput().value, "12/09/2026", "the fresh read must drive the field");
  ok("one typed field_save; the value updates only with the backend read");
}

// ---------------------------------------------------------------------------
console.log("STEP 3 — a cleared date stays UNKNOWN (never today, never 0)");
{
  await bootOnLot(FIX.shipmentDateSaved);
  await type(dateInput(), "");
  const before = triggers.length;
  await click("LƯU NGÀY TẠO", "button");
  await tick(80);
  const saves = triggers.slice(before).filter((tr) => tr.event === "shipment_field_save");
  assert.equal(saves.length, 1, "clearing is a real edit and must be sent once");
  assert.equal(saves[0].value.payload.fields.created_at, "", "the blank must travel as blank");

  deliver(FIX.shipmentDateCleared);
  await tick(120);
  assert.equal(dateInput().value, "", "the readback keeps the blank");
  const t = mainText();
  assert.ok(!t.includes("01/01/1970") && !t.includes(new Date().toISOString().slice(0, 10)),
    "no epoch or today-default may be invented for an unknown date");
  ok("blank in → blank out: UNKNOWN survives the round trip");
}

// ---------------------------------------------------------------------------
console.log("STEP 4 — nothing edited ⇒ nothing sent (no silent rewrite of the date)");
{
  await bootOnLot(FIX.shipmentBefore);
  const before = triggers.length;
  await click("LƯU NGÀY TẠO", "button");
  await tick(60);
  assert.equal(triggers.slice(before).filter((tr) => tr.event === "shipment_field_save").length, 0,
    "clicking save without editing must not rewrite the stored date");
  assert.ok(bodyText().includes("Chưa sửa ngày"), "the hint that nothing was edited must appear");
  assert.equal(dateInput().value, "03/09/2026", "the stored date stays visible");
  ok("unedited save is refused locally instead of re-asserting a value");
}

// ---------------------------------------------------------------------------
console.log("STEP 5 — the customer half of the name is re-chosen by search");
{
  await bootOnLot(FIX.shipmentBefore);
  await clickTestId("shipment-customer-picker-toggle");
  assert.ok(byTestId("shipment-customer-picker-panel"), "search panel did not open");
  await type(byTestId("shipment-customer-picker-search"), "Đức");
  const options = $('[data-testid^="shipment-customer-picker-option-"]');
  assert.ok(options.length >= 1, "the search must offer matches");
  assert.ok(options.some((el) => el.getAttribute("data-testid") === "shipment-customer-picker-option-CUST-MINHDUC"),
    "Minh Đức JSC must be reachable by searching “Đức”");
  await clickTestId("shipment-customer-picker-option-CUST-MINHDUC");
  assert.equal(attr("shipment-customer-picker", "data-selected"), "CUST-MINHDUC");
  // the header line is still what the backend holds — a form pick is not a save
  assert.ok(text(byTestId("shipment-header-edit")).includes(`Tên lô = ${LOT} · An Phát JSC`),
    "the name line must not change before the write is confirmed");

  const before = triggers.length;
  await click("LƯU KHÁCH HÀNG CỦA LÔ", "button");
  await tick(80);
  const saves = triggers.slice(before).filter((tr) => tr.event === "shipment_customer_save");
  assert.equal(saves.length, 1, "exactly one shipment_customer_save per click");
  assert.equal(saves[0].value.payload.shipmentId, LOT);
  assert.equal(saves[0].value.payload.customerId, "CUST-MINHDUC");
  assert.equal(triggers.slice(before).filter((tr) => tr.event === "shipment_field_save").length, 0,
    "a customer change must not smuggle a date write");

  deliver(FIX.shipmentCustomerSaved);
  await tick(120);
  assert.ok(text(byTestId("shipment-header-edit")).includes(`Tên lô = ${LOT} · Minh Đức JSC`),
    "the fresh read must show the new owner in the name line");
  assert.equal(text(byTestId("shipment-customer-picker-value")), "Minh Đức JSC");
  ok("search → one typed event → the read-back name line");
}

// ---------------------------------------------------------------------------
console.log("STEP 6 — saving with nothing picked dispatches nothing");
{
  await bootOnLot(FIX.shipmentCustomerSaved);
  // The picker shows the STORED customer; that is not a change.
  assert.equal(attr("shipment-customer-picker", "data-selected"), "CUST-MINHDUC");
  const before = triggers.length;
  await click("LƯU KHÁCH HÀNG CỦA LÔ", "button");
  await tick(60);
  assert.equal(triggers.slice(before).length, 0, "no event may be emitted for an unchanged pick");
  assert.ok(bodyText().includes("Chưa đổi khách hàng"), "the operator must be told why nothing happened");
  ok("unchanged/blank pick is refused locally, with a reason");
}

// ---------------------------------------------------------------------------
console.log("STEP 7 — a refused (RBAC) write never looks like a success");
{
  const refusals = FIX.shipmentViewerRefused.lastWrites ?? [];
  assert.equal(refusals.length, 2, "fixture must carry both refusals");
  assert.ok(refusals.every((w) => !w.ok && /RBAC/.test(w.error || "")), refusals.map((w) => w.error).join(" / "));

  await bootOnLot(FIX.shipmentViewerRefused);
  const card = text(byTestId("shipment-header-edit"));
  // The page renders EXACTLY the stored truth: the refused date never arrived,
  // the refused customer change never arrived, and the unknown date is blank.
  assert.equal(dateInput().value, "", "a refused date write must not be displayed as saved");
  assert.ok(card.includes(`Tên lô = ${LOT} · Minh Đức JSC`), "the last accepted owner stays visible");
  assert.equal(attr("shipment-customer-picker", "data-selected"), "CUST-MINHDUC");
  assert.ok(!card.includes("Hồng Hà"), "a refused customer must never appear in the header");
  ok("rendered header = stored facts; refusals are not displayed as writes");
}

console.log(`\nSHIPMENT HEADER-EDIT DOM acceptance PASSED — ${passed} checks`);
