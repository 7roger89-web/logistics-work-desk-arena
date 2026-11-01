// ============================================================================
// LOGI — Journey Map (shell nội bộ Trường Thành) → pane trao đổi đang có.
//
// Mounts the REAL committed bundle (component/dist/logi-shell.js) in jsdom over
// a real projection fixture and proves:
//   1. every journey node carries ONE "Trao đổi / Chứng từ" action and it is a
//      SIBLING of the node button (never a nested button);
//   2. clicking it sends exactly ONE typed `journey_focus` trigger whose payload
//      is { shipment_id, stage_id } — no note body, no attachment, no customer
//      id, no permission, and no business write event;
//   3. clicking the node itself still opens the existing stage panel (the node
//      action did not steal the map interaction);
//   4. the discussion action is not rendered for a lot with zero nodes.
// ============================================================================
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import { fileURLToPath, pathToFileURL } from "node:url";
import path from "node:path";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const require = createRequire(path.join(root, "component/package.json"));
const { JSDOM } = require("jsdom");
const fixture = JSON.parse(
  readFileSync(path.join(root, "tests/component/fixtures/view_model_journey_fresh_188.json"), "utf8"),
);
const LOT = "LO-0307";
const EMPTY_LOT = "SEA-188";
const lot = fixture.before.shipments.find((s) => s.id === LOT);
assert.ok(lot, `fixture must carry ${LOT}`);
assert.ok((lot.journey?.nodes ?? []).length >= 2, `${LOT} must carry journey nodes`);
const STAGE = lot.journey.nodes[0].id;

const dom = new JSDOM('<!doctype html><body><div id="host"></div>', {
  url: "http://localhost:9502",
  pretendToBeVisual: true,
});
globalThis.window = dom.window;
globalThis.document = dom.window.document;
try {
  Object.defineProperty(globalThis, "navigator", { value: dom.window.navigator, configurable: true });
} catch { /* keep node navigator */ }
for (const k of [
  "HTMLElement", "HTMLInputElement", "HTMLSelectElement", "HTMLTextAreaElement",
  "Event", "MouseEvent", "Node", "MutationObserver", "getComputedStyle",
]) globalThis[k] = dom.window[k];
dom.window.HTMLElement.prototype.scrollIntoView = () => {};

const triggers = [];
const mount = (await import(pathToFileURL(path.join(root, "component/dist/logi-shell.js")))).default;
mount({
  name: "logi_shell",
  data: fixture.before,
  parentElement: document.getElementById("host"),
  setTriggerValue: (event, value) => triggers.push({ event, value }),
});
const tick = (ms = 200) => new Promise((r) => setTimeout(r, ms));
const byId = (id) => document.querySelector(`[data-testid="${id}"]`);
const click = async (el, what) => {
  assert.ok(el, `${what} not found`);
  el.dispatchEvent(new MouseEvent("click", { bubbles: true, cancelable: true }));
  await tick();
};
const text = (el) => (el?.textContent ?? "").replace(/\s+/g, " ").trim();

async function openLot(id) {
  await click([...document.querySelectorAll("a")].find((a) => text(a) === "Lô Hàng"), "Lô Hàng");
  await click(byId("shipment-period-tat-ca"), "period control");
  await click([...document.querySelectorAll("main a")].find((a) => text(a) === id), `lot ${id}`);
}

await tick();
await openLot(LOT);
assert.ok(byId("shipment-journey"), "journey cockpit must render for a scoped lot");
// The cockpit opens in compact mode; the map (and therefore a node action) is
// only reachable after the existing "mở bản đồ" toggle — that toggle is the
// product's own affordance, not something this lane invents.
await click(byId("journey-detail-map-toggle"), "map toggle");
assert.ok(byId("journey-map-viewport"), "journey map must be open after the toggle");
assert.ok(byId(`journey-node-${STAGE}`), `journey node ${STAGE} must render`);

// 1. every node owns exactly one discussion action, outside the node button
for (const node of lot.journey.nodes) {
  const action = byId(`journey-node-discussion-${node.id}`);
  assert.ok(action, `discussion action missing for node ${node.id}`);
  assert.equal(action.tagName, "BUTTON");
  assert.equal(
    action.closest(`[data-testid="journey-node-${node.id}"]`),
    null,
    "the discussion action must not be nested inside the node button",
  );
  assert.match(
    action.getAttribute("aria-label") ?? "",
    /Trao đổi \/ Chứng từ/,
    "the action must say what it does (accessible name)",
  );
}

// 2. one click = one READ-ONLY intent for this lot + this stage
const before = triggers.length;
await click(byId(`journey-node-discussion-${STAGE}`), "discussion action");
const sent = triggers.slice(before);
assert.equal(sent.length, 1, `exactly one trigger, got ${sent.map((t) => t.event).join(",")}`);
assert.equal(sent[0].event, "journey_focus");
const payload = sent[0].value.payload;
assert.deepEqual(payload, { shipment_id: LOT, stage_id: STAGE });
const serialized = JSON.stringify(sent[0].value);
for (const forbidden of ["customerId", "customer_id", "body", "attachment", "visibility", "INTERNAL"]) {
  assert.ok(!serialized.includes(forbidden), `payload leaked ${forbidden}`);
}
assert.ok(
  triggers.slice(before).every((t) => t.event === "journey_focus"),
  "the node action must not fire a business write event",
);

// 2b. the OTHER fixture node travels with its own raw id (the 7-stage mapping
// is deliberately server-side: the browser never invents a discussion stage).
const second = lot.journey.nodes[1].id;
await click(byId(`journey-node-discussion-${second}`), "second discussion action");
const secondSent = triggers.slice(before + 1);
assert.equal(secondSent.length, 1);
assert.equal(secondSent[0].event, "journey_focus");
assert.deepEqual(secondSent[0].value.payload, { shipment_id: LOT, stage_id: second },
  "each node must send its own id; mapping to a discussion stage is Python's job");

// 3. the node itself still selects the stage (the map interaction is intact)
await click(byId(`journey-node-${STAGE}`), "journey node");
assert.equal(
  byId(`journey-node-${STAGE}`).getAttribute("aria-pressed"),
  "true",
  "clicking the node must still select that stage",
);
assert.equal(
  triggers.filter((t) => t.event === "journey_focus").length,
  2,
  "selecting a node must not emit an extra discussion intent",
);

// 4. a zero-node lot has no node action at all
await openLot(EMPTY_LOT);
await tick(200);
assert.equal(byId("journey-empty-canvas") !== null || byId("journey-empty-primary-cta") !== null, true,
  "zero-node lot renders the existing fresh state");
assert.equal(
  document.querySelectorAll('[data-testid^="journey-node-discussion-"]').length,
  0,
  "no discussion action may exist without journey nodes",
);

console.log(
  `PASS Journey Map node action (shell): ${lot.journey.nodes.length} nodes each send their own read-only intent (${LOT}: ${STAGE}, ${second}), node interaction intact, zero-node lot inert`,
);
process.exit(0);
