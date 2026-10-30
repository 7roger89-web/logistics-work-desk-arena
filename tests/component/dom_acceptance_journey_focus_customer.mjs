// ============================================================================
// LOGI Issue #236 — Journey Map (cổng khách Lục Giác):
//   1. Bấm node → gửi ĐÚNG MỘT `journey_focus` cho đúng lô + đúng công đoạn,
//      payload không chứa customer_id/email/quyền/nội dung.
//   2. Khi server trả `model.discussion`, bubble của node hiển thị bình luận,
//      phản hồi dưới đúng bình luận cha, ô nhập, đính kèm, nút Tải — NGAY TRONG
//      bubble của Journey Map (không có form Streamlit nào).
//   3. Trả lời + gửi → MỘT `journey_note_create` đúng cha, CUSTOMER, không có
//      customer_id; tệp đính kèm đi dạng base64 có giới hạn.
//   4. Tải → `journey_note_download` chỉ mang mã; bytes do server trả về được
//      lưu đúng một lần.
//   5. Đổi lô/ node: không lẫn hội thoại; 0 lô hoặc không transport: không gửi.
// Assets thật: assets/customer_portal/hexa-portal.{html,js} trong jsdom.
// ============================================================================
import { createRequire } from "node:module";
import { readFileSync } from "node:fs";
import assert from "node:assert/strict";

const require = createRequire(
  new URL("../../component/package.json", import.meta.url),
);
const { JSDOM } = require("jsdom");
const html = readFileSync(
  new URL("../../assets/customer_portal/hexa-portal.html", import.meta.url),
  "utf8",
);
const js = readFileSync(
  new URL("../../assets/customer_portal/hexa-portal.js", import.meta.url),
  "utf8",
);
const dom = new JSDOM(`<div id="root">${html}</div>`, {
  url: "http://localhost:9504",
  pretendToBeVisual: true,
});
globalThis.document = dom.window.document;
globalThis.window = dom.window;
globalThis.requestAnimationFrame = dom.window.requestAnimationFrame.bind(dom.window);
globalThis.FileReader = dom.window.FileReader;
globalThis.File = dom.window.File;
const saved = [];
globalThis.URL.createObjectURL = () => "blob:mock";
globalThis.URL.revokeObjectURL = () => {};
dom.window.HTMLAnchorElement.prototype.click = function mockClick() {
  saved.push({ name: this.download, href: this.href });
};

const { default: mount } = await import(
  "data:text/javascript;base64," + Buffer.from(js).toString("base64")
);
const root = document.querySelector("#root");
const tick = (ms = 30) => new Promise((resolve) => setTimeout(resolve, ms));
const byTestId = (id) => root.querySelector(`[data-testid="${id}"]`);
const text = (el) => (el?.textContent ?? "").replace(/\s+/g, " ").trim();
const click = async (el, what) => {
  assert.ok(el, `${what} not found`);
  el.click();
  await tick();
};

const nodes = [
  { id: "plan", index: "00", label: "Kế hoạch", state: "COMPLETED", evidence: "Đã chốt" },
  { id: "pickup", index: "01", label: "Lấy hàng", state: "COMPLETED", evidence: "Đã lấy" },
  { id: "consolidate", index: "02", label: "Gom hàng", state: "COMPLETED", evidence: "Đã gom" },
  { id: "transit", index: "03", label: "Vận chuyển", state: "CURRENT", evidence: "Đang chạy" },
  { id: "customs", index: "04", label: "Thông quan", state: "WAITING", evidence: "Chờ tờ khai" },
  { id: "delivery", index: "05", label: "Giao hàng", state: "UPCOMING", evidence: "" },
  { id: "finance", index: "06", label: "Thanh toán", state: "UPCOMING", evidence: "" },
];
const lot = (id, label) => ({
  shipment_id: id,
  transport_mode: "SEA",
  verified_stage_title: label,
  verified_stage_label: label,
  documents: [],
  timeline: [],
  journey: { nodes: nodes.map((n) => ({ ...n })), edges: [] },
  publication: { version: "v1", approved_at: "2026-10-30" },
});

const discussion = (shipment, stage, extra = {}) => ({
  shipmentId: shipment,
  stageId: stage,
  nodeId: stage,
  nodeLabel: "",
  stageLabel: "Vận chuyển",
  canWrite: true,
  canAttach: true,
  canSeeInternal: false,
  maxFiles: 4,
  maxBytes: 20971520,
  count: 2,
  notes: [{
    id: "jn-root",
    reply_to_id: "",
    body: "Trường Thành: hãng tàu đổi ETD.",
    visibility: "CUSTOMER",
    author_kind: "user",
    author_name: "sale.thanh",
    author_role: "sale",
    created_at: "2026-10-30T08:00:00+00:00",
    attachments: [{ id: "iatt-9", name: "to-khai.pdf", mime: "application/pdf", sizeLabel: "9 KB" }],
    replies: [{
      id: "jn-reply",
      reply_to_id: "jn-root",
      body: "Lục Giác đã đồng ý ETD mới.",
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

const sent = [];
const paint = (lots, more = {}, withTransport = true) => {
  const model = { customer: { name: "Lục Giác" }, lots, ...more };
  const api = { parentElement: root, data: { model } };
  if (withTransport) api.setTriggerValue = (event, value) => sent.push({ event, value });
  mount(api);
};

async function openJourney(lotId) {
  await click(byTestId(`btn-open-journey-${lotId}`), `dashboard row ${lotId}`);
  assert.ok(byTestId("shipment-journey"), "journey view did not open");
}

async function openNode(nodeId) {
  await click(byTestId(`journey-node-${nodeId}`), `node ${nodeId}`);
  const bubble = byTestId("journey-bubble");
  assert.ok(bubble, "node bubble did not open");
  return bubble;
}

// ---- 1. one clicked node = exactly one read-only focus intent --------------
paint([lot("G1-LG-001", "Lục Giác Logistics")]);
await tick();
await openJourney("G1-LG-001");
await openNode("customs");
assert.equal(sent.length, 1, "one node click must send exactly one trigger");
assert.equal(sent[0].event, "journey_focus");
assert.deepEqual(sent[0].value, {
  seq: 1,
  event: "journey_focus",
  payload: { shipment_id: "G1-LG-001", stage_id: "customs" },
});
const focusSerialized = JSON.stringify(sent[0].value);
for (const forbidden of ["CUST-", "@", "customer_id", "customerId", "visibility", "INTERNAL"]) {
  assert.ok(!focusSerialized.includes(forbidden), `focus payload leaked ${forbidden}`);
}
assert.ok(byTestId("journey-discussion-loading"), "the bubble shows an honest loading state");
assert.equal(byTestId("journey-discussion-list"), null, "no conversation before the server delivered it");

// ---- 2. the delivered thread renders INSIDE the node bubble ----------------
paint([lot("G1-LG-001", "Lục Giác Logistics")], { discussion: discussion("G1-LG-001", "customs") });
await tick(80);
const bubble = byTestId("journey-bubble");
assert.ok(bubble, "the node bubble must survive the data refresh (same node, same lot)");
assert.ok(byTestId("journey-discussion"), "the conversation lives in the node bubble");
// Regression: the old 290px tooltip clipped the thread and composer.
assert.ok(Number.parseFloat(bubble.style.width) >= 500, "desktop conversation must be readable, not 290px wide");
assert.ok(Number.parseFloat(bubble.style.height) >= 450, "conversation needs a full-height dock, not a cramped node tooltip");
assert.equal(bubble.querySelector(".journey-bubble-list")?.firstElementChild?.dataset.testid,
  "journey-discussion", "conversation must precede secondary stage/document summaries");
assert.ok(text(byTestId("journey-discussion")).includes("Trường Thành: hãng tàu đổi ETD."));
assert.ok(text(byTestId("journey-discussion")).includes("Lục Giác đã đồng ý ETD mới."));
assert.ok(byTestId("journey-discussion-note-jn-root"), "root comment card");
assert.ok(byTestId("journey-discussion-note-jn-reply"), "reply rendered under its root");
assert.ok(byTestId("journey-discussion-reply-jn-root"), "root comment offers Trả lời");
assert.equal(byTestId("journey-discussion-reply-jn-reply"), null, "replies are one level only");
assert.ok(byTestId("journey-discussion-body"), "composer is inside the bubble");
assert.equal(sent.length, 1, "a data refresh must not re-emit the focus intent");
// Pan/zoom state survives the refresh: the same node is still open, unmoved.
const transformBefore = byTestId("journey-map-transform").style.transform;
paint([lot("G1-LG-001", "Lục Giác Logistics")], { discussion: discussion("G1-LG-001", "customs") });
await tick(60);
assert.ok(byTestId("journey-bubble"), "the same node must stay open");
assert.equal(byTestId("journey-discussion") !== null, true, "its thread is still shown");
assert.equal(byTestId("journey-map-transform").style.transform, transformBefore,
  "pan/zoom must not be reset by a thread refresh");

// ---- 3. reply under the right root + a bounded attachment ------------------
await click(byTestId("journey-discussion-reply-jn-root"), "reply action");
const banner = byTestId("journey-discussion-reply-banner");
assert.ok(banner, "reply banner must name the parent");
assert.match(text(banner), /sale\.thanh/);

const body = byTestId("journey-discussion-body");
body.value = "Khách đã nhận chứng từ mới.";
body.dispatchEvent(new dom.window.Event("input", { bubbles: true }));
const fileInput = byTestId("journey-discussion-file");
const png = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFAAH/q842iQAAAABJRU5ErkJggg==",
  "base64",
);
const chosen = new dom.window.File([png], "xac-nhan.png", { type: "image/png" });
Object.defineProperty(fileInput, "files", { value: [chosen], configurable: true });
fileInput.dispatchEvent(new dom.window.Event("change", { bubbles: true }));
await tick(80);
assert.ok(text(byTestId("journey-discussion-composer")).includes("Đã chọn: xac-nhan.png"),
  "the picked file must be named before sending");

const beforeCreate = sent.length;
await click(byTestId("journey-discussion-send"), "send");
const creates = sent.slice(beforeCreate).filter((t) => t.event === "journey_note_create");
assert.equal(creates.length, 1, "exactly one create event per Gửi");
const payload = creates[0].value.payload;
assert.equal(payload.body, "Khách đã nhận chứng từ mới.");
assert.equal(payload.replyToId, "jn-root");
assert.equal(payload.shipmentId, "G1-LG-001");
assert.equal(payload.stageId, "customs");
assert.equal(payload.visibility, "CUSTOMER", "the portal can only publish customer-visible text");
assert.equal(payload.files.length, 1);
assert.equal(payload.files[0].name, "xac-nhan.png");
assert.equal(payload.files[0].mime, "image/png");
assert.equal(payload.files[0].base64, png.toString("base64"));
assert.ok(payload.files[0].size <= payload.files[0].base64.length);
const serialized = JSON.stringify(creates[0].value);
for (const forbidden of ["CUST-", "@", "customer_id", "customerId", "role", "INTERNAL"]) {
  assert.ok(!serialized.includes(forbidden), `create payload leaked ${forbidden}`);
}
assert.equal(byTestId("journey-discussion-send").disabled, true, "no duplicate submit while pending");

// ---- 4. only the backend outcome clears / reports --------------------------
paint([lot("G1-LG-001", "Lục Giác Logistics")], {
  discussion: discussion("G1-LG-001", "customs", {
    outcome: {
      requestId: payload.requestId,
      ok: false,
      error: "Bình luận được trả lời không còn tồn tại.",
    },
  }),
});
await tick(80);
assert.equal(byTestId("journey-discussion-body").value, "Khách đã nhận chứng từ mới.",
  "a refusal must not clear what the customer wrote");
assert.match(text(byTestId("journey-discussion-notice")), /không còn tồn tại/i);

await click(byTestId("journey-discussion-send"), "retry");
const retry = sent.filter((t) => t.event === "journey_note_create").at(-1);
paint([lot("G1-LG-001", "Lục Giác Logistics")], {
  discussion: discussion("G1-LG-001", "customs", {
    outcome: { requestId: retry.value.payload.requestId, ok: true },
    count: 3,
  }),
});
await tick(80);
assert.equal(byTestId("journey-discussion-body").value, "", "a proven save clears the draft");
assert.equal(byTestId("journey-discussion-reply-banner"), null, "reply target cleared after success");

// ---- 5. download: identifiers out, server bytes in -------------------------
const beforeDownload = sent.length;
await click(byTestId("journey-discussion-download-iatt-9"), "download");
const downloads = sent.slice(beforeDownload).filter((t) => t.event === "journey_note_download");
assert.equal(downloads.length, 1, "one file = one download request");
assert.equal(downloads[0].value.payload.noteId, "jn-root");
assert.equal(downloads[0].value.payload.attachmentId, "iatt-9");
assert.equal(downloads[0].value.payload.shipmentId, "G1-LG-001");
assert.ok(!JSON.stringify(downloads[0].value).includes("base64"), "browser must not send bytes");

paint([lot("G1-LG-001", "Lục Giác Logistics")], {
  discussion: discussion("G1-LG-001", "customs", {
    download: {
      noteId: "jn-root",
      attachmentId: "iatt-9",
      name: "to-khai.pdf",
      mime: "application/pdf",
      base64: Buffer.from("%PDF-1.4 customer").toString("base64"),
      seq: 1,
    },
  }),
});
await tick(120);
assert.equal(saved.length, 1, "the server-delivered file is saved exactly once");
assert.equal(saved[0].name, "to-khai.pdf");
paint([lot("G1-LG-001", "Lục Giác Logistics")], { discussion: discussion("G1-LG-001", "customs") });
await tick(80);
assert.equal(saved.length, 1, "the same download must not be saved again");

// ---- 6. another node never shows this thread ------------------------------
const beforeOther = sent.length;
await openNode("transit");
assert.equal(sent.length, beforeOther + 1, "a new node asks for its OWN thread");
assert.equal(sent.at(-1).value.payload.stage_id, "transit");
assert.ok(sent.at(-1).value.seq > sent[0].value.seq, "seq advances so a replay cannot re-open");
assert.equal(byTestId("journey-discussion-list"), null, "the customs thread must not appear at transit");
assert.ok(byTestId("journey-discussion-loading"), "the new node shows its own loading state");

// A second lot keeps its own scope: the delivered lot+stage already matches, so
// opening it must NOT re-emit (no loop), and a different node asks for its own.
const focusBeforeSecondLot = sent.filter((t) => t.event === "journey_focus").length;
paint([lot("G1-LG-001", "Lục Giác Logistics"), lot("G1-MD-001", "Minh Đức")], {
  discussion: discussion("G1-MD-001", "transit"),
});
await tick(80);
await openJourney("G1-MD-001");
await openNode("transit");
assert.equal(
  sent.filter((t) => t.event === "journey_focus").length,
  focusBeforeSecondLot,
  "an already-delivered lot+stage must not be requested again",
);
assert.ok(text(byTestId("journey-discussion")).includes("Trường Thành: hãng tàu đổi ETD."));
await openNode("customs");
const lastFocus = sent.filter((t) => t.event === "journey_focus").at(-1);
assert.equal(lastFocus.value.payload.shipment_id, "G1-MD-001");
assert.equal(lastFocus.value.payload.stage_id, "customs");

// ---- 7. user text is rendered as TEXT, never as HTML ----------------------
const hostile = '<img src=x onerror="window.__pwned=1"><b>đậm</b>';
paint([lot("G1-LG-001", "Lục Giác Logistics")], {
  discussion: discussion("G1-LG-001", "customs", {
    notes: [{
      ...discussion("G1-LG-001", "customs").notes[0],
      body: hostile,
      replies: [],
    }],
  }),
});
await tick(80);
await openNode("customs");
assert.ok(text(byTestId("journey-discussion-note-jn-root")).includes(hostile),
  "the raw text must be preserved verbatim");
assert.equal(root.querySelector("img[onerror]"), null, "no user HTML may become DOM");
assert.equal(dom.window.__pwned, undefined, "no user handler may run");

// ---- 8. no transport / no lots → nothing is sent --------------------------
const beforeQuiet = sent.length;
// (same mounted component with a transport-less api)
paint([lot("G1-LG-001", "Lục Giác Logistics")], { discussion: discussion("G1-LG-001", "transit") }, false);
await tick(60);
await openNode("transit");
assert.equal(sent.length, beforeQuiet, "without a transport nothing may be sent");

paint([], {});
await tick(60);
assert.equal(sent.length, beforeQuiet, "zero published lots must not send anything");

console.log(
  `PASS Journey Map node → inline discussion (customer): focus + reply + file + download inside the node bubble, scope separated, ${sent.length} intents`,
);
process.exit(0);
