// ============================================================================
// Issue #162 DOM acceptance — REAL production bundle (component/dist/logi-shell.js)
// in jsdom, against backend snapshots produced by the REAL dispatcher.
//
//   python scripts/verify_work_module_library_162.py --fixture /tmp/log162-dom.json
//   node tests/component/dom_acceptance_work_module_library_162.mjs /tmp/log162-dom.json
//
// Proves the accepted UI contract "graph for the machine; rollup/gate for the
// person": the default Journey does NOT expand module steps into the map, the
// rollup carries name/progress/status/gate/next-step/provenance, internal steps
// are revealed on demand through the SAME node interaction, completion only
// appears after the authoritative readback, and a Viewer cannot mutate.
// ============================================================================
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import { fileURLToPath, pathToFileURL } from "node:url";
import path from "node:path";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const require = createRequire(path.join(root, "component/package.json"));
const { JSDOM } = require("jsdom");
const fixture = JSON.parse(readFileSync(process.argv[2], "utf8"));
const dom = new JSDOM('<!doctype html><body><div id="host"></div>', { url: "http://localhost:9502", pretendToBeVisual: true });
globalThis.window = dom.window; globalThis.document = dom.window.document;
Object.defineProperty(globalThis, "navigator", { value: dom.window.navigator, configurable: true });
for (const key of ["HTMLElement", "HTMLInputElement", "HTMLSelectElement", "HTMLTextAreaElement", "Event", "MouseEvent", "Node", "MutationObserver", "getComputedStyle"]) globalThis[key] = dom.window[key];
dom.window.HTMLElement.prototype.scrollIntoView = () => {};

const mount = (await import(pathToFileURL(path.join(root, "component/dist/logi-shell.js")))).default;
const triggers = [];
const deliver = (data) => mount({ name: "logi_shell", data, parentElement: document.getElementById("host"), setTriggerValue: (event, value) => triggers.push({ event, value }) });
const tick = () => new Promise((r) => setTimeout(r, 90));
const byId = (id) => document.querySelector(`[data-testid="${id}"]`);
const click = async (el) => { assert.ok(el, "click target exists"); el.dispatchEvent(new dom.window.MouseEvent("click", { bubbles: true, cancelable: true })); await tick(); };
const button = (label, parent = document) => [...parent.querySelectorAll("button")].find((e) => e.textContent.trim() === label);

async function openShipment() {
  await click([...document.querySelectorAll("a")].find((a) => a.textContent.trim() === "Lô Hàng"));
  await click(byId("shipment-period-tat-ca"));
  await click([...document.querySelectorAll("main a")].find((a) => a.textContent.trim() === "SEA-162"));
}

const INSTANCE = fixture.meta.instanceId;
const BASE_NODES = fixture.meta.baseNodeCount; // booking, etd, on-board, transit, arrival, customs-import, delivery

// ---------------------------------------------------------------- 1. before
deliver(fixture.before);
await tick();
await openShipment();
assert.equal(document.querySelectorAll('[data-testid^="journey-node-"]').length, BASE_NODES, "no modules: base map only");
assert.ok(!byId("journey-modules"), "no rollup section before any module exists");
// The attach action is driven by the SERVER's canAttach flag, not by whether
// modules already exist: this fixture runs as Support, so it is offered.
// Issue #190 (Owner reference 6f6c655): with ZERO modules the entry point
// lives in the page identity bar; opening it mounts the same attach panel.
assert.ok(byId("journey-add-module-page"), "an authorised actor can always open the attach panel");
await click(byId("journey-add-module-page"));
assert.ok(byId("journey-add-module"), "opening the identity-bar entry mounts the attach strip");

// ------------------------------------------------------------- 2. attached
deliver(fixture.attached);
await tick();
assert.equal(document.querySelectorAll('[data-testid^="journey-node-"]').length, BASE_NODES, "DEFAULT: module steps are NOT expanded into the map");
const card = byId(`journey-module-${INSTANCE}`);
assert.ok(card, "rollup card renders");
assert.match(card.textContent, /IMPORT SPECIAL HANDLING/);
assert.match(card.textContent, /0\/3 bước/);
assert.equal(byId(`journey-module-status-${INSTANCE}`).textContent.trim(), "Đang chặn");
assert.match(byId(`journey-module-gate-${INSTANCE}`).textContent, /Chặn DELIVERY — còn thiếu Prepare specialist file, Submit \/ process, Result received/);
assert.match(card.textContent, /Next|Bước tiếp theo/);
assert.match(card.textContent, /Prepare specialist file/);
assert.match(card.textContent, /Thêm thủ công/, "provenance is shown");
assert.ok(!byId(`journey-module-steps-${INSTANCE}`), "internal steps start hidden");
assert.match(byId("journey-quick-panel").textContent, /Next Action/);

// --------------------------------------- 3. reveal internal steps on demand
await click(byId(`journey-module-toggle-${INSTANCE}`));
assert.ok(byId(`journey-module-steps-${INSTANCE}`), "steps revealed on demand");
assert.equal(document.querySelectorAll('[data-testid^="journey-node-"]').length, BASE_NODES + 3, "3 module steps revealed");
assert.equal(document.querySelectorAll('[data-testid^="journey-node-wm-"]').length, 3);
const stepNode = byId(`journey-node-wm-${INSTANCE}-prepare-file`);
assert.equal(stepNode.dataset.state, "UPCOMING");
const eventsBefore = triggers.length;
await click(stepNode);
assert.equal(triggers.length, eventsBefore, "selecting a module step is view state only");
assert.match(byId("journey-module-context").textContent, /IMPORT SPECIAL HANDLING/);
assert.match(byId("journey-module-context").textContent, /V1/);
assert.match(byId("journey-quick-panel").textContent, /Prepare specialist file/);
assert.ok(byId("journey-module-guidance"), "step guidance is available in the Quick Panel");

// ------------------------------------ 4. Stage Workspace + factual completion
await click(byId("journey-open-workspace"));
assert.ok(byId("journey-stage-workspace"));
await click(button("Thông tin", byId("journey-stage-workspace")));
const panel = byId("work-module-step-panel");
assert.ok(panel, "module step panel mounts in the Stage Workspace");
assert.match(panel.textContent, /Tệp đã tải lên không tự xác nhận|không tự xác nhận/);
const completeBtn = byId("work-module-step-complete");
assert.equal(completeBtn.disabled, false);
await click(completeBtn);
const dispatched = triggers.filter((t) => t.event === "work_module_step_complete");
assert.equal(dispatched.length, 1, "exactly ONE bounded completion event");
assert.equal(dispatched[0].value.payload.instanceId, INSTANCE);
assert.equal(dispatched[0].value.payload.nodeId, "prepare-file");
assert.equal(dispatched[0].value.payload.expectedVersion, fixture.meta.versions.attached);
assert.match(panel.textContent, /Đang chờ đọc lại/, "pending is shown, not success");
assert.notEqual(byId(`journey-node-wm-${INSTANCE}-prepare-file`).dataset.state, "COMPLETED", "no local completion before readback");

// ------------------------------------------- 5. refusal never shows success
const refusal = structuredClone(fixture.attached);
refusal.lastWrites = [{
  event: "work_module_step_complete", ok: false, requestId: dispatched[0].value.payload.requestId,
  shipmentId: "SEA-162", error: "Lô đã thay đổi — đọc lại dữ liệu trước khi ghi nhận.",
}];
deliver(refusal);
await tick();
assert.match(document.querySelector('[role="alert"]').textContent, /Lô đã thay đổi/);
assert.notEqual(byId(`journey-node-wm-${INSTANCE}-prepare-file`).dataset.state, "COMPLETED");

// ------------------------------- 6. authoritative readback advances the facts
deliver(fixture.partial);
await tick();
assert.equal(byId(`journey-node-wm-${INSTANCE}-prepare-file`).dataset.state, "COMPLETED", "after the fresh readback the step is factually complete");
assert.equal(byId(`journey-module-progress-${INSTANCE}`).textContent.trim(), "1/3 bước");
assert.match(byId(`journey-module-gate-${INSTANCE}`).textContent, /Chặn DELIVERY — còn thiếu Submit \/ process, Result received/);
assert.match(byId(`journey-module-gate-${INSTANCE}`).textContent, /Result received/);

deliver(fixture.done);
await tick();
assert.equal(byId(`journey-node-wm-${INSTANCE}-prepare-file`).dataset.state, "COMPLETED");
assert.equal(byId(`journey-node-wm-${INSTANCE}-submit-process`).dataset.state, "COMPLETED");
assert.equal(byId(`journey-node-wm-${INSTANCE}-result-received`).dataset.state, "COMPLETED");
assert.equal(byId(`journey-module-progress-${INSTANCE}`).textContent.trim(), "3/3 bước");
assert.equal(byId(`journey-module-status-${INSTANCE}`).textContent.trim(), "Hoàn thành");
assert.ok(!byId(`journey-module-gate-${INSTANCE}`), "no blocking gate sentence once the module is done");
assert.equal(document.querySelectorAll('[data-testid^="journey-node-"]').length, BASE_NODES + 3, "still no expanded graph: only the revealed module steps");
assert.match(byId(`journey-module-${INSTANCE}`).textContent, /Đã xong toàn bộ/);

// ------------------------------------------------- 7. Viewer stays read-only
deliver(fixture.attached);
await tick();
deliver(fixture.viewer);
await tick();
await openShipment();
assert.ok(!byId("journey-add-module"), "Viewer sees no attach action");
assert.ok(byId(`journey-module-${INSTANCE}`), "Viewer still reads the rollup");
await click(byId(`journey-module-toggle-${INSTANCE}`));
await click(byId(`journey-node-wm-${INSTANCE}-prepare-file`));
await click(byId("journey-open-workspace"));
await click(button("Thông tin", byId("journey-stage-workspace")));
const viewerPanel = byId("work-module-step-panel");
assert.ok(viewerPanel);
assert.match(viewerPanel.textContent, /chỉ đọc/);
assert.equal(byId("work-module-step-complete").disabled, true, "Viewer cannot complete a module step");

// -------------------------------------- 8. attach flow dispatches ONE event
deliver(fixture.before);
await tick();
await openShipment();
assert.ok(byId("journey-add-module-page"), "an authorised actor sees the attach action");
await click(byId("journey-add-module-page"));
assert.ok(byId("journey-add-module"), "the attach strip mounts with the panel");
const attachPanel = byId("journey-add-module-panel");
assert.ok(attachPanel);
assert.match(attachPanel.textContent, /IMPORT SPECIAL HANDLING/, "ACTIVE templates are listed");
assert.match(attachPanel.textContent, /Chỉ gắn được quy trình đang dùng/);
await click(attachPanel.querySelector('input[type="radio"]'));
await click(byId("journey-add-module-confirm"));
const attachEvents = triggers.filter((t) => t.event === "work_module_attach");
assert.equal(attachEvents.length, 1, "exactly ONE bounded attach event");
assert.equal(attachEvents[0].value.payload.templateId, "IMPORT_SPECIAL_HANDLING_DEMO_V1");
assert.equal(attachEvents[0].value.payload.provenance, "MANUAL_ADDITION");
assert.match(attachPanel.textContent, /Đang chờ đọc lại/, "pending, never optimistic");
assert.ok(!byId("journey-modules"), "the rollup does NOT appear before the authoritative readback");
deliver(fixture.attached);
await tick();
assert.ok(byId(`journey-module-${INSTANCE}`), "after the fresh readback the module appears");

// ------------------------------------------- 9. template library surface (/quy-trinh)
await click([...document.querySelectorAll("a")].find((a) => a.textContent.trim() === "Thư viện quy trình"));
assert.ok(byId("work-module-library"), "the bounded library page renders");
assert.ok([...document.querySelectorAll("[data-testid^='wm-row-']")].length >= 1, "stored versions are listed");
assert.ok(byId("wm-library-new"), "an authorised actor can open the structured form");
await click(byId("wm-library-new"));
assert.ok(byId("wm-library-form"), "structured form (no BPMN canvas, no drag/drop editor)");
assert.ok(byId("wm-step-0"));
assert.ok(byId("wm-add-step"), "steps are an ordered list");
deliver(fixture.viewer);
await tick();
assert.ok(!byId("wm-library-new"), "Viewer cannot open the authoring form");
assert.ok(byId("wm-library-readonly"));
assert.match(byId("wm-library-readonly").textContent, /chỉ xem được thư viện/);

console.log(`PASS #162 DOM: base map stays ${BASE_NODES} nodes, rollup BLOCKING→DONE with gate wording, steps revealed on demand, readback-gated completion, refusal honest, Viewer read-only, attach/library bounded`);
