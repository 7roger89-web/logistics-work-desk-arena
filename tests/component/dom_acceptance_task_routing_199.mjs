// LOGI-APP-RENEWAL-01 — active Task desk create → Home → exact Journey node.
//
// Runs the built production React bundle in jsdom. This is structural DOM/event
// evidence only; jsdom has no layout engine and is not a desktop/mobile browser.
// Canonical save/readback/RBAC/audit are separately covered by the isolated
// Python Mongomock integration test.

import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const require = createRequire(path.join(ROOT, "component/package.json"));
const { JSDOM } = require("jsdom");
const model = JSON.parse(readFileSync(
  path.join(ROOT, "tests/component/fixtures/view_model_document_review.json"), "utf8",
));
const shipmentId = model.fixture.shipmentId;
const shipment = model.shipments.find((row) => row.id === shipmentId);
assert.ok(shipment, "fixture shipment exists");

const node = (id, label, targetTab) => ({
  id, label, family: id.toUpperCase(), targetTab, completed: false, state: "UPCOMING",
  factState: "UNKNOWN", evidence: "", deadline: "", owned: true, current: false,
  blockers: [], dependencies: [], documentCategories: [], documentIds: [],
});
shipment.mode = "Sea";
shipment.customer = "An Phát JSC";
shipment.journey = {
  nodes: [node("si-vgm", "SI / VGM", "van-tai"), node("customs-import", "Customs import", "nhap")],
  edges: [], currentStageId: "", owner: "Sale Tester", positionNote: "", seaFacts: {},
  primaryAction: { text: "Kiểm tra lô", detail: "", priority: "BinhThuong", route: shipment.nextRoute },
};
model.tasks = [];
model.attention = [];
model.taskAssignment = {
  canCreate: true,
  assignees: [
    { userId: "", label: "Tất cả (Team)" },
    { userId: "support-user-199", label: "Support Tester" },
  ],
};
model.home = {
  ...(model.home || {}),
  focus: {
    id: shipmentId, customer: shipment.customer, status: shipment.status,
    nextAction: "Kiểm tra lô", nextActionDetail: "", priority: "BinhThuong",
    to: shipment.nextRoute,
  },
  urgentCount: 1,
};

const dom = new JSDOM("<!doctype html><html><body><div id=\"host\"></div></body></html>", {
  url: "http://localhost:9501/",
  pretendToBeVisual: true,
});
const { window } = dom;
globalThis.window = window;
globalThis.document = window.document;
try { Object.defineProperty(globalThis, "navigator", { value: window.navigator, configurable: true }); } catch {}
for (const key of [
  "HTMLElement", "HTMLInputElement", "HTMLSelectElement", "HTMLTextAreaElement",
  "HTMLAnchorElement", "HTMLButtonElement", "Event", "CustomEvent", "MouseEvent",
  "KeyboardEvent", "Node", "Element", "MutationObserver", "getComputedStyle",
]) globalThis[key] = window[key];
window.HTMLElement.prototype.scrollIntoView = () => {};
window.scrollTo = () => {};

const tick = (ms = 80) => new Promise((resolve) => setTimeout(resolve, ms));
const text = (element) => (element?.textContent || "").replace(/\s+/g, " ").trim();
const byTestId = (id) => window.document.querySelector(`[data-testid="${id}"]`);
const triggers = [];
const mount = (await import(pathToFileURL(path.join(ROOT, "component/dist/logi-shell.js")))).default;
const host = window.document.getElementById("host");
const deliver = (data) => mount({
  name: "logi_shell",
  data,
  parentElement: host,
  setTriggerValue: (event, value) => triggers.push({ event, value }),
});
const click = async (element) => {
  assert.ok(element, "expected clickable element");
  element.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
  await tick();
};
const setValue = async (element, value) => {
  assert.ok(element, "expected form field");
  const prototype = element.tagName === "SELECT" ? window.HTMLSelectElement.prototype
    : element.tagName === "TEXTAREA" ? window.HTMLTextAreaElement.prototype
    : window.HTMLInputElement.prototype;
  Object.getOwnPropertyDescriptor(prototype, "value").set.call(element, value);
  element.dispatchEvent(new window.Event("input", { bubbles: true }));
  element.dispatchEvent(new window.Event("change", { bubbles: true }));
  await tick(20);
};

console.log("STEP 1 — Home exposes the existing task desk without changing the main nav");
deliver(model);
await tick();
const homeTaskDesk = byTestId("home-task-desk");
assert.ok(homeTaskDesk);
await click(homeTaskDesk);
assert.ok(window.document.querySelector("main")?.textContent.includes("Việc Cần Xử Lý"));
assert.ok(byTestId("task-create-open"), "Sale/Support capability exposes task create action");

console.log("STEP 2 — active form uses canonical shipment, assignee and Journey choices");
await click(byTestId("task-create-open"));
assert.ok(byTestId("task-create-form"));
await setValue(window.document.querySelector('[aria-label="Nội dung công việc"]'), "Thu công nợ sau khi xác nhận SI");
await setValue(window.document.querySelector('[aria-label="Giao cho ai?"]'), "support-user-199");
await setValue(window.document.querySelector('[aria-label="Gắn với lô (tùy chọn)"]'), shipmentId);
await setValue(window.document.querySelector('[aria-label="Nơi xử lý khi mở từ Home"]'), "STAGE");
const stageSelect = window.document.querySelector('[aria-label="Công đoạn trong Journey"]');
assert.ok(stageSelect, "stage selection appears only for an explicitly selected lot");
assert.deepEqual([...stageSelect.options].map((option) => option.value), ["si-vgm", "customs-import"]);
await setValue(stageSelect, "si-vgm");
await click(byTestId("task-create-submit"));
const request = triggers.find((entry) => entry.event === "task_create")?.value;
assert.ok(request, "active form dispatches the one typed task_create event");
assert.equal(request.event, "task_create");
assert.equal(request.payload.content, "Thu công nợ sau khi xác nhận SI");
assert.equal(request.payload.shipmentId, shipmentId);
assert.equal(request.payload.taskScope, "STAGE");
assert.equal(request.payload.stageId, "si-vgm");
assert.equal(request.payload.assigneeUserId, "support-user-199");
assert.match(request.payload.deadline, /^\d{4}-\d{2}-\d{2}$/);
assert.ok(request.payload.requestId);

console.log("STEP 3 — authoritative last-write outcome refreshes task list and Home Attention");
const route = `/lo-hang/${encodeURIComponent(shipmentId)}?tab=van-tai&stage=si-vgm&work=info`;
const createdTask = {
  id: "TASK-CREATE-199", level: "CanXuLy", lot: shipmentId, customer: shipment.customer,
  job: request.payload.content, assignee: "Support Tester", due: "16/10/2026",
  dueNote: "Đã gắn công đoạn: SI / VGM.", status: "Chưa làm", statusTone: "amber",
  route, source: "core.database.load_tasks",
};
const primary = {
  id: "ATT-PRIMARY-199", shipmentId, sourceType: "PRIMARY_ACTION", sourceRef: `PRIMARY:${shipmentId}`,
  band: "ACTION", reason: "Kiểm tra lô", action: "Kiểm tra lô", context: shipment.customer,
  route: shipment.nextRoute, owner: "Sale Tester", deadline: "", deadlineDate: "", blockedGate: "",
  primary: true, provenance: "shipment.primaryAction", unknown: false,
};
const stageAttention = {
  id: "ATT-STAGE-199", shipmentId, sourceType: "TASK", sourceRef: "TASK:TASK-CREATE-199",
  band: "DUE_SOON", reason: "Đã gắn công đoạn: SI / VGM.", action: request.payload.content,
  context: shipment.customer, route, navigationStatus: "STAGE", owner: "Support Tester",
  deadline: "16/10/2026", deadlineDate: "2026-10-16", blockedGate: "", primary: false,
  provenance: "core.database.load_tasks", unknown: false,
};
const unknownAttention = {
  id: "ATT-UNKNOWN-199", shipmentId, sourceType: "TASK", sourceRef: "TASK:LEGACY-UNKNOWN-199",
  band: "ACTION", reason: "Chưa gắn công đoạn; mở workspace lô để xác định nơi xử lý.",
  action: "Việc chưa có công đoạn", context: shipment.customer, route: `/lo-hang/${encodeURIComponent(shipmentId)}`,
  navigationStatus: "UNKNOWN_STAGE", owner: "Support Tester", deadline: "", deadlineDate: "",
  blockedGate: "", primary: false, provenance: "core.database.load_tasks", unknown: false,
};
const updated = structuredClone(model);
updated.tasks = [createdTask, {
  id: "TASK-GENERAL-199", level: "CanXuLy", lot: "—", customer: "—", job: "Việc chung",
  assignee: "Tất cả (Team)", due: "—", dueNote: "Việc được giao", status: "Chưa làm",
  statusTone: "amber", route: "/lo-hang", source: "core.database.load_tasks",
}];
updated.attention = [primary, stageAttention, unknownAttention];
updated.lastWrites = [{
  event: "task_create", ok: true, requestId: request.payload.requestId,
  readback: { taskId: "TASK-CREATE-199", shipmentId, taskScope: "STAGE", stageId: "si-vgm" },
}];
deliver(updated);
await tick(160);
assert.ok(byTestId("task-create-success"), "UI waits for and shows the correlated backend success");
assert.ok(window.document.querySelector("main")?.textContent.includes(request.payload.content));
assert.ok(window.document.querySelector("main")?.textContent.includes("Việc chung"));
assert.ok(window.document.querySelector("main")?.textContent.includes("— · —"), "unlinked task has no fabricated shipment");

// Return to Home using the existing logo route. The focus primary action is
// removed by identity, so the due task is not accidentally sliced away.
const homeLogo = [...window.document.querySelectorAll("header a")].find((link) => link.getAttribute("href") === "/");
await click(homeLogo);
const homeStageItem = window.document.querySelector(`[data-testid="attention-item-ATT-STAGE-199"]`);
const homeStageLink = [...window.document.querySelectorAll("a")]
  .find((link) => link.getAttribute("href") === route);
const secondaryUnknown = window.document.querySelector(`[data-testid="attention-item-ATT-UNKNOWN-199"]`);
assert.ok(homeStageItem, "created, stage-bound task appears in Home after refresh");
assert.ok(homeStageLink, "Home CTA keeps the exact encoded Journey route");
assert.ok(secondaryUnknown, "unbound task remains a secondary compact Attention item");
assert.equal(secondaryUnknown.getAttribute("href"), `/lo-hang/${encodeURIComponent(shipmentId)}`);
const warning = byTestId("attention-task-navigation-warning-ATT-UNKNOWN-199");
assert.ok(warning, "secondary compact item carries the missing-stage warning in the DOM");
assert.ok(warning.className.includes("break-words") && !warning.className.includes("hidden"),
  "warning text is not conditionally hidden and may wrap in the compact row");
assert.match(text(warning), /Chưa gắn công đoạn/);
assert.match(text(warning), /mở workspace lô/);
assert.match(secondaryUnknown.getAttribute("aria-label"), /Mở lô/);

console.log("STEP 4 — Home action opens the exact existing stage workspace");
await click(homeStageLink);
await tick(160);
assert.ok(byTestId("journey-stage-workspace"), "exact stage route opens the existing Journey workspace");
assert.match(text(byTestId("journey-stage-workspace")), /SI \/ VGM/);
assert.equal(triggers.length, 1, "navigation itself adds no write; only the explicit create event was sent");

console.log("PASS #199 DOM: active task desk create event → authoritative task/Home projection → exact SI/VGM destination; secondary missing-stage warning and generic no-fake-lot behavior");
