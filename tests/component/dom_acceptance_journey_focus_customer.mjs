// ============================================================================
// LOGI — Journey Map (cổng khách Lục Giác) → pane trao đổi/chứng từ đang có.
//
// Exercises the REAL production asset (assets/customer_portal/hexa-portal.js)
// in jsdom, desktop and mobile, with 0 / 1 / 2 published lots:
//   1. Bấm node → bubble → "💬 Trao đổi / Chứng từ" gửi ĐÚNG MỘT trigger
//      `journey_focus` với đúng lô + đúng mã công đoạn 00..06 (seq one-shot).
//   2. Payload không bao giờ chứa customer_id / email / nội dung trao đổi.
//   3. Đổi lô thứ hai thì payload mang đúng lô thứ hai (không lẫn tenancy).
//   4. 0 lô: không có nút mở trao đổi, không gửi gì.
//   5. Không có transport (render tĩnh): nút bị vô hiệu hoá, không gửi gì.
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
  pretendToBeVisual: true,
});
globalThis.document = dom.window.document;
globalThis.window = dom.window;
globalThis.requestAnimationFrame = dom.window.requestAnimationFrame.bind(
  dom.window,
);
const { default: mount } = await import(
  "data:text/javascript;base64," + Buffer.from(js).toString("base64")
);
const root = document.querySelector("#root");
const tick = () => new Promise((resolve) => setTimeout(resolve, 20));
const byTestId = (id) => root.querySelector(`[data-testid="${id}"]`);
const click = async (el, what) => {
  assert.ok(el, `${what} not found`);
  el.click();
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

const sent = [];
const paint = (lots, withTransport = true) => {
  const api = {
    parentElement: root,
    data: { model: { customer: { name: "Lục Giác" }, lots } },
  };
  if (withTransport) api.setTriggerValue = (event, value) => sent.push({ event, value });
  mount(api);
};

async function openJourney(lotId) {
  await click(byTestId(`btn-open-journey-${lotId}`), `dashboard row ${lotId}`);
  assert.ok(byTestId("shipment-journey"), "journey view did not open");
}

async function openDiscussion(nodeId) {
  await click(byTestId(`journey-node-${nodeId}`), `node ${nodeId}`);
  const bubble = byTestId("journey-bubble");
  assert.ok(bubble, "node bubble did not open");
  const action = byTestId("journey-open-discussion");
  assert.ok(action, "Trao đổi / Chứng từ action not rendered in the bubble");
  await click(action, "discussion action");
  return action;
}

// ---- 1. desktop: one clicked node = exactly one read-only intent -----------
paint([lot("G1-LG-001", "Lục Giác Logistics")]);
await tick();
await openJourney("G1-LG-001");
await openDiscussion("customs");
assert.equal(sent.length, 1, "one click must send exactly one trigger");
assert.equal(sent[0].event, "journey_focus");
assert.deepEqual(sent[0].value, {
  seq: 1,
  event: "journey_focus",
  payload: { shipment_id: "G1-LG-001", stage_id: "customs" },
});
const serialized = JSON.stringify(sent[0].value);
for (const forbidden of ["CUST-", "@", "customer_id", "customerId", "visibility", "INTERNAL"]) {
  assert.ok(!serialized.includes(forbidden), `payload leaked ${forbidden}`);
}

// ---- 2. a second node on the same lot targets its own stage ---------------
paint([lot("G1-LG-001", "Lục Giác Logistics")]);
await tick();
await openJourney("G1-LG-001");
await openDiscussion("transit");
assert.equal(sent.length, 2);
assert.equal(sent[1].value.payload.stage_id, "transit");
assert.equal(sent[1].value.seq, 2, "seq must advance so a replay cannot re-open");

// ---- 3. two lots: the clicked lot is the one that travels ------------------
paint([lot("G1-LG-001", "Lục Giác Logistics"), lot("G1-MD-001", "Minh Đức")]);
await tick();
await openJourney("G1-MD-001");
await openDiscussion("pickup");
assert.equal(sent.length, 3);
assert.deepEqual(sent[2].value.payload, {
  shipment_id: "G1-MD-001",
  stage_id: "pickup",
});

// ---- 4. mobile (390px): the same node action exists and is tappable -------
Object.defineProperty(dom.window, "innerWidth", { value: 390, configurable: true });
paint([lot("G1-LG-001", "Lục Giác Logistics")]);
await tick();
await openJourney("G1-LG-001");
await openDiscussion("customs");
assert.equal(sent.length, 4);
assert.deepEqual(sent[3].value.payload, {
  shipment_id: "G1-LG-001",
  stage_id: "customs",
});

// ---- 5. zero published lots: nothing to open, nothing to send -------------
paint([]);
await tick();
assert.equal(byTestId("btn-open-journey-G1-LG-001"), null);
assert.equal(byTestId("journey-open-discussion"), null);
assert.equal(sent.length, 4, "an empty payload must not emit anything");

// ---- 6. no Streamlit transport: the action is disabled, never a fake write -
paint([lot("G1-LG-001", "Lục Giác Logistics")], false);
await tick();
await click(byTestId("btn-open-journey-G1-LG-001"), "dashboard row");
await click(byTestId("journey-node-customs"), "node customs");
const disabled = byTestId("journey-open-discussion");
assert.ok(disabled, "action should still render so the state is honest");
assert.equal(disabled.disabled, true, "no transport must disable the action");
disabled.click();
assert.equal(sent.length, 4, "a disabled action must not emit");

console.log(
  "PASS Journey Map node → discussion intent (desktop/mobile, 0/1/2 lots, no transport)",
);
dom.window.close();
