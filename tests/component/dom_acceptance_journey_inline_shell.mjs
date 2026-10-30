// ============================================================================
// Issue #236 — Journey Map (shell nội bộ) comment/reply INSIDE the node panel.
//
// Mounts the REAL committed bundle (component/dist/logi-shell.js) in jsdom over
// the real projection fixture and proves:
//   1. clicking 💬 on a node renders the conversation INSIDE the map viewport
//      (not a Streamlit form elsewhere): root comment + its one-level reply;
//   2. a reply under the root attaches to that root id and sends ONE typed
//      `journey_note_create` (text only, no customer id, no permission);
//   3. the composer only clears on the backend's authoritative outcome for its
//      own requestId (transport alone is not success);
//   4. a download action sends identifiers only (never bytes) and the delivered
//      server bytes are saved once;
//   5. the panel sits inside the map viewport and its controls stop the map's
//      pan gesture.
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
const row = fixture.before.shipments.find((s) => s.id === LOT);
assert.ok(row, `fixture must carry ${LOT}`);
const NODE = row.journey.nodes.find((n) => n.id === "MAIN_CARRIAGE") || row.journey.nodes[0];
const STAGE = NODE.id;

const dom = new JSDOM('<!doctype html><body><div id="host"></div></body>', {
  url: "http://localhost:9503",
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

// A real file download must not navigate the jsdom page.
const saved = [];
globalThis.URL.createObjectURL = () => "blob:mock";
globalThis.URL.revokeObjectURL = () => {};
const realClick = dom.window.HTMLAnchorElement.prototype.click;
dom.window.HTMLAnchorElement.prototype.click = function mockClick() {
  saved.push({ name: this.download, href: this.href });
};

const triggers = [];
const mount = (await import(pathToFileURL(path.join(root, "component/dist/logi-shell.js")))).default;
const mountData = (extra) => mount({
  name: "logi_shell",
  data: { ...fixture.before, ...extra },
  parentElement: document.getElementById("host"),
  setTriggerValue: (event, value) => triggers.push({ event, value }),
});
mountData({});
const tick = (ms = 220) => new Promise((r) => setTimeout(r, ms));
const byId = (id) => document.querySelector(`[data-testid="${id}"]`);
const text = (el) => (el?.textContent ?? "").replace(/\s+/g, " ").trim();
const click = async (el, what) => {
  assert.ok(el, `${what} not found`);
  el.dispatchEvent(new MouseEvent("click", { bubbles: true, cancelable: true }));
  await tick();
};
const typeInto = async (el, value) => {
  assert.ok(el, "textarea not found");
  const setter = Object.getOwnPropertyDescriptor(dom.window.HTMLTextAreaElement.prototype, "value").set;
  setter.call(el, value);
  el.dispatchEvent(new dom.window.Event("input", { bubbles: true }));
  await tick(60);
};

const discussion = (extra = {}) => ({
  shipmentId: LOT,
  stageId: "transit",
  nodeId: STAGE,
  nodeLabel: NODE.label,
  stageLabel: "Vận chuyển",
  canWrite: true,
  canAttach: true,
  canSeeInternal: true,
  maxFiles: 4,
  maxBytes: 20971520,
  count: 2,
  notes: [{
    id: "jn-root",
    reply_to_id: "",
    body: "Hãng tàu đổi ETD — khách đã đồng ý.",
    visibility: "CUSTOMER",
    author_kind: "user",
    author_name: "sale.thanh",
    author_role: "sale",
    created_at: "2026-10-30T08:00:00+00:00",
    attachments: [{ id: "iatt-1", name: "to-khai.pdf", mime: "application/pdf", sizeLabel: "12 KB" }],
    replies: [{
      id: "jn-reply",
      reply_to_id: "jn-root",
      body: "Khách xác nhận ETD mới.",
      visibility: "CUSTOMER",
      author_kind: "customer",
      author_name: "Lục Giác",
      author_role: "customer",
      created_at: "2026-10-30T08:05:00+00:00",
      attachments: [],
    }],
  }],
  download: null,
  error: "",
  ...extra,
});

async function openLot() {
  await click([...document.querySelectorAll("a")].find((a) => text(a) === "Lô Hàng"), "Lô Hàng");
  await click(byId("shipment-period-tat-ca"), "period control");
  await click([...document.querySelectorAll("main a")].find((a) => text(a) === LOT), `lot ${LOT}`);
  await click(byId("journey-detail-map-toggle"), "map toggle");
  assert.ok(byId("journey-map-viewport"), "journey map must be open");
}

await tick();
mountData({ journeyDiscussion: discussion() });
await openLot();
await click(byId(`journey-node-discussion-${STAGE}`), "discussion action");

// ---- 1. the thread is INSIDE the map, at the node -------------------------
const viewport = byId("journey-map-viewport");
const panel = byId("journey-discussion-panel");
assert.ok(panel, "the node panel must render after the node action");
assert.equal(panel.dataset.node, STAGE);
assert.ok(viewport.contains(panel), "the conversation must live inside the Journey Map");
assert.ok(text(panel).includes("Vận chuyển"), "the panel names its công đoạn");
assert.ok(text(panel).includes("Hãng tàu đổi ETD"), "the root comment must be visible");
assert.ok(text(panel).includes("Khách xác nhận ETD mới."), "the reply must be visible under its root");
assert.ok(byId("journey-discussion-note-jn-root"), "root comment card");
assert.ok(byId("journey-discussion-note-jn-reply"), "reply card");
assert.ok(byId("journey-discussion-reply-jn-root"), "root comment offers Trả lời");
assert.equal(byId("journey-discussion-reply-jn-reply"), null, "a reply is one level only");
assert.ok(byId("journey-discussion-body"), "composer is in the same panel");
assert.equal(byId("journey-discussion-error"), null);

// The panel is a sibling overlay, never a scaled canvas child.
assert.equal(panel.closest('[data-testid="journey-map-transform"]'), null);

// Map gestures must not start from inside the panel.
const transformBefore = byId("journey-map-transform").style.transform;
const pointer = new dom.window.Event("pointerdown", { bubbles: true, cancelable: true });
panel.dispatchEvent(pointer);
await click(byId("journey-discussion-note-jn-root"), "comment body");
assert.equal(byId("journey-map-transform").style.transform, transformBefore,
  "touching the conversation must not pan or zoom the map");

// ---- 2. reply under the right root → ONE typed create ----------------------
const before = triggers.length;
await click(byId("journey-discussion-reply-jn-root"), "reply action");
assert.ok(byId("journey-discussion-reply-banner"), "reply banner must show the parent");
assert.match(text(byId("journey-discussion-reply-banner")), /sale\.thanh/);

await typeInto(byId("journey-discussion-body"), "Đã gửi lại chứng từ cho khách.");
await click(byId("journey-discussion-send"), "send");
const created = triggers.slice(before).filter((t) => t.event === "journey_note_create");
assert.equal(created.length, 1, "exactly one create event per Gửi");
const payload = created[0].value.payload;
assert.equal(payload.body, "Đã gửi lại chứng từ cho khách.");
assert.equal(payload.replyToId, "jn-root", "the reply must attach to the clicked parent");
assert.equal(payload.shipmentId, LOT);
assert.equal(payload.nodeId, STAGE);
assert.equal(payload.visibility, "INTERNAL", "staff default is internal (fail-safe)");
assert.deepEqual(payload.files, []);
const serialized = JSON.stringify(created[0].value);
for (const forbidden of ["CUST-", "@", "customer_id", "customerId", "role", "base64"]) {
  assert.ok(!serialized.includes(forbidden), `create payload leaked ${forbidden}`);
}
assert.ok(byId("journey-discussion-send").disabled, "no second submit while waiting for the backend");
assert.ok(triggers.slice(before).every((t) => t.event === "journey_note_create"),
  "no other business event may fire from the composer");

// ---- 3. only the backend outcome clears the draft -------------------------
const requestId = payload.requestId;
assert.ok(requestId, "the create event must carry a requestId");
mountData({
  lastWrites: [{ event: "journey_note_create", ok: false, error: "Bình luận cha không còn tồn tại.", requestId }],
  journeyDiscussion: discussion(),
});
await tick(200);
assert.equal(byId("journey-discussion-body").value, "Đã gửi lại chứng từ cho khách.",
  "a refusal must NOT clear the operator's text");
assert.match(text(byId("journey-discussion-error") ?? byId("journey-discussion-panel")), /không còn tồn tại/i);

const successId = (() => {
  // The UI is free to clear; resubmit to get a fresh request id.
  return "JRN-SUCCESS";
})();
await click(byId("journey-discussion-send"), "re-send");
const secondCreate = triggers.filter((t) => t.event === "journey_note_create").at(-1);
assert.ok(secondCreate, "a retry must be possible after a refusal");
mountData({
  lastWrites: [{ event: "journey_note_create", ok: true, requestId: secondCreate.value.payload.requestId }],
  journeyDiscussion: discussion({ count: 3 }),
});
await tick(220);
assert.equal(byId("journey-discussion-body").value, "", "the backend's success clears the draft");
assert.equal(byId("journey-discussion-reply-banner"), null, "the reply target is cleared after success");

// Comments are text: user HTML can never become DOM inside the panel.
mountData({
  journeyDiscussion: discussion({
    notes: [{
      ...discussion().notes[0],
      body: '<img src=x onerror="window.__pwned=1"><b>đậm</b>',
      replies: [],
    }],
  }),
});
await tick(160);
assert.ok(text(byId("journey-discussion-note-jn-root")).includes('<img src=x onerror='),
  "the raw text must be preserved");
assert.equal(document.querySelector('[data-testid="journey-discussion-note-jn-root"] img'), null,
  "no user HTML may become DOM");
assert.equal(dom.window.__pwned, undefined, "no user handler may run");

// ---- 4. download sends identifiers only, then saves the server bytes ------
const beforeDownload = triggers.length;
await click(byId("journey-discussion-download-iatt-1"), "download");
const downloads = triggers.slice(beforeDownload).filter((t) => t.event === "journey_note_download");
assert.equal(downloads.length, 1, "one file = one bounded download event");
assert.deepEqual(
  {
    noteId: downloads[0].value.payload.noteId,
    attachmentId: downloads[0].value.payload.attachmentId,
  },
  { noteId: "jn-root", attachmentId: "iatt-1" },
);
const downloadSerialized = JSON.stringify(downloads[0].value);
assert.ok(!downloadSerialized.includes("base64"), "the browser must never send bytes for a download");
assert.ok(!downloadSerialized.includes("customer"), "no tenant identity in a download request");

mountData({
  journeyDiscussion: discussion({
    download: {
      noteId: "jn-root",
      attachmentId: "iatt-1",
      name: "to-khai.pdf",
      mime: "application/pdf",
      base64: Buffer.from("%PDF-1.4 test").toString("base64"),
      seq: 1,
    },
  }),
});
await tick(240);
assert.equal(saved.length, 1, "the server-delivered file must be saved exactly once");
assert.equal(saved[0].name, "to-khai.pdf");

await tick(120);
mountData({ journeyDiscussion: discussion() });
await tick(160);
assert.equal(saved.length, 1, "the same download must not be saved again on a rerun");

console.log(
  `PASS Journey Map inline discussion (shell): node ${STAGE} thread inside the map, reply→root, backend-authoritative clear, bounded download (${requestId}/${successId})`,
);
dom.window.HTMLAnchorElement.prototype.click = realClick;
process.exit(0);
