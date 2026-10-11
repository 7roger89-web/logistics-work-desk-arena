/**
 * LOGI-195 — Shipment Journey compact + smooth operations DOM acceptance.
 *
 * Uses the CURRENT production bundle (component/dist/logi-shell.js) in jsdom
 * against a payload produced by the REAL staging stack — never hand-written
 * business data:
 *
 *   python3 scripts/gen_logi195_dom_fixture.py --fixture /tmp/logi195-dom.json
 *   node tests/component/dom_acceptance_logi195_compact_journey_smooth.mjs /tmp/logi195-dom.json
 *
 * The fixture bakes in SEA-160 (populated 11-node Journey, WITH customer_id)
 * and SEA-195 (same Journey shape, NO canonical customer_id), plus a picker
 * catalog where PXK is active but currently unavailable (real server
 * project_catalog with pxk_template_available=False).
 *
 * This test then proves the boundary contract in the DOM:
 *  1. the compact overview is the DEFAULT: toolbar + step strip + quick
 *     panel, NO 718px/620px map canvas mounted;
 *  2. "Bản đồ chi tiết" mounts the intact detailed 11-node map and closes it;
 *  3. journey node picks are LOCAL (zero backend dispatch);
 *  4. the CUSTOMER_SELF radio is LOCAL; without customer_id the guided
 *     recovery panel appears and the flow confirm is locked (no dead-end);
 *  5. an active-but-unavailable template checkbox is NOT selection-locked,
 *     toggling it is LOCAL, and Save dispatches exactly ONE
 *     shipment_document_selection_save.
 */

import { readFileSync } from "node:fs";
import assert from "node:assert/strict";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { createRequire } from "node:module";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const require = createRequire(path.join(ROOT, "component/package.json"));
const { JSDOM } = require("jsdom");
const bundlePath = path.join(ROOT, "component/dist/logi-shell.js");
const FIX = JSON.parse(readFileSync(process.argv[2] || "/tmp/logi195-dom.json", "utf8"));

const SHIPMENT_ID = FIX.expected.shipmentId;
const NO_CUSTOMER_ID = FIX.expected.noCustomerShipmentId;
const NODE_IDS = FIX.expected.nodeIds;
const UNAVAILABLE_TEMPLATE = FIX.expected.unavailableTemplateId;

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

const tick = (ms = 80) => new Promise((resolve) => setTimeout(resolve, ms));
const $ = (selector, root = window.document) => [...root.querySelectorAll(selector)];
const text = (element) => (element?.textContent || "").replace(/\s+/g, " ").trim();

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

function prepareModel() {
  const model = clone(FIX.viewModel);
  model.lastWrites = [];
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

async function gotoShipment(sid) {
  await clickWhenReady("Lô Hàng", "a", "aside");
  await clickWhenReady("Tất cả thời gian", "button", "[data-testid='shipment-period-controls']");
  await clickWhenReady(sid, "a", "table.tbl");
  return waitForDom(
    () => $("[data-testid='shipment-journey']")[0],
    `shipment journey for ${sid} is mounted`,
  );
}

async function gotoDocumentsTab() {
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
// A. Compact Journey is the default; the detailed map opens on demand
// ===========================================================================
await gotoShipment(SHIPMENT_ID);

assert.ok($("[data-testid='journey-compact-overview']")[0], "compact overview is the default");
assert.equal($("[data-testid='journey-map-viewport']").length, 0, "no 718px/620px map canvas mounted by default");
const toggle = $("[data-testid='journey-detail-map-toggle']")[0];
assert.ok(toggle, "the explicit detail-map control exists");
assert.ok(text(toggle).includes("Bản đồ chi tiết"), "control is clearly labeled");

const steps = NODE_IDS.map((id) => $(`[data-testid='journey-step-${id}']`)[0]);
assert.ok(steps.every(Boolean), "the compact step strip shows all 11 journey nodes");
assert.ok($("[data-testid='journey-compact-toolbar']")[0], "position/problem toolbar is visible");

// A.3 — node picks are LOCAL: zero backend dispatch, immediate rendered state.
const before = triggers.length;
const customsStep = $(`[data-testid='journey-step-customs-import']`)[0];
customsStep.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
await tick();
assert.equal(triggers.length, before, "journey node pick dispatches nothing to the backend");
assert.equal(customsStep.getAttribute("aria-pressed"), "true", "picked node renders selected immediately");

// The detailed 11-node map opens through the explicit control, intact.
await clickWhenReady("Bản đồ chi tiết", "button", "[data-testid='journey-compact-toolbar']");
await waitForDom(() => $("[data-testid='journey-map-viewport']")[0], "detailed JourneyMap mounts on demand");
const mapNodes = NODE_IDS.map((id) => $(`[data-testid='journey-node-${id}']`).filter((el) => el.closest("[data-testid='journey-map-viewport']"))[0]);
assert.ok(mapNodes.every(Boolean), "all 11 detailed map nodes are intact behind the control");
// A map node pick is local too.
const beforeMap = triggers.length;
mapNodes[3].dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
await tick();
assert.equal(triggers.length, beforeMap, "detailed map node pick dispatches nothing");
await clickWhenReady("Thu gọn bản đồ", "button", "[data-testid='journey-compact-toolbar']");
await tick();
assert.equal($("[data-testid='journey-map-viewport']").length, 0, "the detailed map closes again");

// ===========================================================================
// B. CUSTOMER_SELF without customer_id: guided recovery, no dead-end
// ===========================================================================
await gotoShipment(NO_CUSTOMER_ID);
await gotoDocumentsTab();
const flowSection = await waitForDom(
  () => $("[data-testid='shipment-commercial-flow']")[0],
  "commercial flow section is mounted",
);
const radio = $(`input[name='commercial-flow'][value='CUSTOMER_SELF']`, flowSection)[0];
assert.ok(radio, "the CUSTOMER_SELF radio exists");
const beforeRadio = triggers.length;
radio.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
await tick();
assert.equal(triggers.length, beforeRadio, "commercial-flow radio is a local interaction");
assert.ok(
  $("[data-testid='commercial-flow-customer-recovery']", flowSection)[0],
  "the guided customer recovery panel appears instead of a dead-end error",
);
const confirmBtn = findClickable("XÁC NHẬN HÌNH THỨC NHẬP KHẨU", "button", flowSection);
assert.ok(confirmBtn, "the flow confirm button exists");
assert.equal(confirmBtn.disabled, true, "confirm stays locked until the customer is assigned");

// ===========================================================================
// C. Template selection vs generation availability
// ===========================================================================
await gotoShipment(SHIPMENT_ID);
await gotoDocumentsTab();
await clickWhenReady("Chọn biểu mẫu", "button", "[data-testid='shipment-document-picker']");
const dialog = await waitForDom(
  () => $("[data-testid='shipment-document-picker-dialog']")[0],
  "the template selection dialog opens",
);
const option = $(`[data-testid='shipment-document-template-option'][data-template-id='${UNAVAILABLE_TEMPLATE}']`, dialog)[0];
assert.ok(option, "the active-but-unavailable template option is listed");
const checkbox = $("input[type='checkbox']", option)[0];
assert.ok(checkbox, "the template checkbox exists");
assert.equal(checkbox.disabled, false, "an active template is NOT selection-locked by availability");
const beforeCheck = triggers.length;
checkbox.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
await tick();
assert.equal(triggers.length, beforeCheck, "template checkbox toggle is a local interaction");
assert.equal(checkbox.checked, true, "the unavailable template can be checked for tracking");
// The honest blocked-for-generation note is visible.
assert.ok(text(option).includes("chưa tạo được") || text(option).includes("chưa sẵn sàng"),
  "the option truthfully says generation stays blocked");

const beforeSave = triggers.length;
await click("Lưu lựa chọn", "button", dialog);
await tick(300);
assert.equal(events("shipment_document_selection_save").length, 1, "exactly ONE selection save dispatched");
assert.equal(triggers.length, beforeSave + 1, "no other backend traffic from the save click");

console.log("LOGI-195 DOM acceptance: compact journey + smooth operations — all assertions passed.");
