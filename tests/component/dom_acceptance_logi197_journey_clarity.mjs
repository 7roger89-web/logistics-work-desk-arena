/**
 * LOGI-197 — Journey operator-clarity DOM acceptance.
 *
 * Fixture:
 *   python3 scripts/gen_logi195_dom_fixture.py --fixture /tmp/logi197-dom.json
 * Run:
 *   node tests/component/dom_acceptance_logi197_journey_clarity.mjs /tmp/logi197-dom.json
 *
 * Proves the redesigned browser contract against the CURRENT built bundle:
 * - default = five compact macro phases, no 11-node canvas / giant side panel;
 * - detailed 11-node map remains available on demand;
 * - steps 1–4 expose only Công việc + Chứng từ; Chi phí is owned by step 5;
 * - phase Chứng từ uses the existing stage-scoped attachment surface, not the
 *   global document-picker/workflow;
 * - legacy exact-name CUSTOMER_SELF confirms in one action and sends the
 *   canonical customerId on shipment_commercial_flow_save (no separate GÁN);
 * - template planning from LOGI-195 remains selectable independently from
 *   generation readiness.
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
const FIX = JSON.parse(readFileSync(process.argv[2] || "/tmp/logi197-dom.json", "utf8"));

const SHIPMENT_ID = FIX.expected.shipmentId;
const LEGACY_EXACT = FIX.expected.noCustomerShipmentId;
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
} catch {}
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
async function waitForDom(find, label) {
  for (let attempt = 0; attempt < 50; attempt++) {
    const element = find();
    if (element) return element;
    await tick();
  }
  assert.fail(label);
}
async function clickElement(element, label) {
  assert.ok(element, label);
  element.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
  await tick(120);
}
async function clickWhenReady(needle, selector, scopeSelector) {
  const element = await waitForDom(() => {
    const root = $(scopeSelector)[0];
    return root && findClickable(needle, selector, root);
  }, `clickable "${needle}" on ${scopeSelector}`);
  await clickElement(element, `clickable "${needle}"`);
  return element;
}

const host = window.document.createElement("div");
window.document.body.appendChild(host);
const triggers = [];
const mountRef = { current: null };
const events = (name) => triggers.filter((entry) => entry.event === name);
const clone = (value) => JSON.parse(JSON.stringify(value));
let currentModel = { ...clone(FIX.viewModel), lastWrites: [] };

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
  return waitForDom(() => $("[data-testid='shipment-journey']")[0], `shipment ${sid}`);
}

async function openStep5Files() {
  const button = await waitForDom(
    () => $("[data-testid='journey-macro-files-5']")[0],
    "step 5 Hồ sơ button",
  );
  await clickElement(button, "step 5 Hồ sơ button");
  return waitForDom(
    () => $("[data-testid='shipment-document-picker']")[0],
    "global Hồ sơ surface",
  );
}

const module = await import(pathToFileURL(bundlePath).href);
assert.equal(typeof module.default, "function", "built bundle exports component mount");
mountRef.current = module.default;
invoke(currentModel);
await tick(200);

// A — five-phase default, detailed 11-node map only on demand.
await gotoShipment(SHIPMENT_ID);
assert.ok($("[data-testid='journey-compact-overview']")[0], "compact Journey is default");
assert.ok($("[data-testid='journey-macro-steps']")[0], "five-phase Journey exists");
assert.equal($("[data-testid^='journey-macro-step-']").length, 5, "exactly five macro phases");
assert.equal($("[data-testid='journey-map-viewport']").length, 0, "detailed canvas is not mounted by default");
assert.equal($("[data-testid='journey-side-panel']").length, 0, "giant side panel is not mounted by default");
assert.equal($("[data-testid^='journey-macro-work-']").length, 4, "steps 1-4 own Công việc");
assert.equal($("[data-testid^='journey-macro-docs-']").length, 4, "steps 1-4 own Chứng từ");
assert.equal($("[data-testid='journey-macro-finance-5']").length, 1, "step 5 alone owns Chi phí");
assert.equal($("[data-testid^='journey-macro-finance-']").length, 1, "no per-stage Chi phí duplicates");
assert.ok(text($("[data-testid='journey-compact-toolbar']")[0]).includes("Đang ở:"), "position remains visible");

await clickWhenReady("Bản đồ chi tiết", "button", "[data-testid='journey-compact-toolbar']");
await waitForDom(() => $("[data-testid='journey-map-viewport']")[0], "detailed map");
for (const id of NODE_IDS) {
  assert.ok(
    $(`[data-testid='journey-node-${id}']`).some((el) => el.closest("[data-testid='journey-map-viewport']")),
    `detailed node ${id} remains available`,
  );
}
await clickWhenReady("Thu gọn bản đồ", "button", "[data-testid='journey-compact-toolbar']");
assert.equal($("[data-testid='journey-map-viewport']").length, 0, "detailed map closes");

// B — stage documents are scoped; global picker/workflow does not bleed in.
const phase1Docs = $("[data-testid='journey-macro-docs-1']")[0];
await clickElement(phase1Docs, "phase 1 Chứng từ");
const stage = await waitForDom(() => $("[data-testid='journey-stage-workspace']")[0], "phase workspace");
assert.ok($("[data-testid='shipment-attachments']", stage)[0], "phase uses attachment surface");
assert.ok(text(stage).includes("Chứng từ công đoạn"), "phase attachment context is explicit");
assert.equal($("[data-testid='shipment-document-picker']", stage).length, 0, "global document picker is absent from phase");
assert.ok(findClickable("Công việc", "button", stage), "phase has Công việc");
assert.ok(findClickable("Chứng từ", "button", stage), "phase has Chứng từ");
assert.equal(Boolean(findClickable("Chi phí", "button", stage)), false, "phase has no Chi phí tab");
assert.equal(Boolean(findClickable("Lịch sử", "button", stage)), false, "phase has no Lịch sử tab");

// C.1 — a normal modern shipment already has canonical customerId: selecting
// CUSTOMER_SELF must never ask for the same customer again.
await gotoShipment(SHIPMENT_ID);
await clickElement(
  await waitForDom(() => $("[data-testid='journey-macro-work-3']")[0], "modern phase 3 Công việc"),
  "modern phase 3 Công việc",
);
let flowSection = await waitForDom(
  () => $("[data-testid='shipment-commercial-flow']")[0],
  "modern phase 3 commercial-flow section",
);
let radio = $("input[name='commercial-flow'][value='CUSTOMER_SELF']", flowSection)[0];
await clickElement(radio, "modern CUSTOMER_SELF radio");
assert.ok($("[data-testid='commercial-flow-customer-identity']", flowSection)[0], "modern lot reuses canonical customer");
assert.equal($("[data-testid='commercial-flow-customer-recovery']", flowSection).length, 0, "modern lot has no duplicate customer picker");
let confirm = findClickable("XÁC NHẬN HÌNH THỨC NHẬP KHẨU", "button", flowSection);
assert.ok(confirm && !confirm.disabled, "modern lot can confirm immediately");

// C.2 — import identity lives in phase 3; a legacy exact-name CUSTOMER_SELF is
// still one action with no duplicate customer picker.
await gotoShipment(LEGACY_EXACT);
await clickElement(
  await waitForDom(() => $("[data-testid='journey-macro-work-3']")[0], "phase 3 Công việc"),
  "phase 3 Công việc",
);
flowSection = await waitForDom(
  () => $("[data-testid='shipment-commercial-flow']")[0],
  "phase 3 commercial-flow section",
);
assert.ok(flowSection.closest("[data-testid='journey-stage-workspace']"), "import model is owned by phase 3");
radio = $("input[name='commercial-flow'][value='CUSTOMER_SELF']", flowSection)[0];
await clickElement(radio, "CUSTOMER_SELF radio");
assert.ok($("[data-testid='commercial-flow-customer-identity']", flowSection)[0], "exact unique name resolves visibly");
assert.equal($("[data-testid='commercial-flow-customer-recovery']", flowSection).length, 0, "no duplicate customer picker on exact match");
confirm = findClickable("XÁC NHẬN HÌNH THỨC NHẬP KHẨU", "button", flowSection);
assert.ok(confirm && !confirm.disabled, "one confirmation action is enabled");
const beforeFlow = events("shipment_commercial_flow_save").length;
const beforeCustomerSave = events("shipment_customer_save").length;
await clickElement(confirm, "confirm CUSTOMER_SELF");
assert.equal(events("shipment_commercial_flow_save").length, beforeFlow + 1, "one commercial-flow write dispatched");
assert.equal(events("shipment_customer_save").length, beforeCustomerSave, "no separate customer-save write");
const sentFlow = events("shipment_commercial_flow_save").at(-1).value.payload;
assert.equal(sentFlow.mode, "CUSTOMER_SELF");
assert.equal(sentFlow.customerId, "CUST-ANPHAT", "legacy exact match sends canonical customer id");

// D — template selection remains planning-local and generation readiness stays separate.
await gotoShipment(SHIPMENT_ID);
await openStep5Files();
await clickWhenReady("Chọn biểu mẫu", "button", "[data-testid='shipment-document-picker']");
const dialog = await waitForDom(
  () => $("[data-testid='shipment-document-picker-dialog']")[0],
  "template dialog",
);
const option = $(
  `[data-testid='shipment-document-template-option'][data-template-id='${UNAVAILABLE_TEMPLATE}']`,
  dialog,
)[0];
assert.ok(option, "active-but-not-ready template is listed");
const checkbox = $("input[type='checkbox']", option)[0];
assert.ok(checkbox && !checkbox.disabled, "planning selection stays enabled");
const beforeCheck = triggers.length;
await clickElement(checkbox, "template checkbox");
assert.equal(triggers.length, beforeCheck, "checkbox selection is local");
assert.equal(checkbox.checked, true, "template can be selected for the lot");

console.log("LOGI-197 DOM acceptance: five-phase Journey + scoped work + one-action customer identity — all assertions passed.");
