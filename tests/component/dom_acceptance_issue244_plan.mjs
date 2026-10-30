// ============================================================================
// Issue #244 DOM acceptance — Node 00 KẾ HOẠCH inside the REAL Journey Map.
//
// Runs the shipped production bundle (component/dist/logi-shell.js) in jsdom
// against a fixture generated from the REAL Logistics backend
// (scripts/gen_issue244_plan_fixture.py — isolated mongomock staging), and
// drives it with real DOM events through the Streamlit Components v2 contract:
// `mount({data, parentElement, setTriggerValue})`.
//
// Proven here (rendering alone is NOT a pass — every case is a truth boundary):
//   1. Node 00 is the FIRST node of the SAME journey, before booking/pickup,
//      on the compact stepper AND on the detailed map.
//   2. Clicking it opens the plan panel INSIDE the Journey (no global tab jump)
//      and closing it returns to the SAME lot + node.
//   3. Báo giá = the lot's exact quote_id; a second ACCEPTED quote of the same
//      customer never renders.
//   4. Hợp đồng = the customer contract; the TT↔sub-agent purchase contract is
//      never shown, and "Đã ký" is never claimed.
//   5. Tạm ứng: confirmed entrusted → "Chưa xác minh đã nhận" + "cần đối soát"
//      (never a paid amount); CUSTOMER_SELF → "Không áp dụng"; unknown import
//      form → "Chưa xác nhận hình thức nhập khẩu".
//   6. Node 00 conversation still targets the canonical `plan` stage, and the
//      existing booking node keeps its own thread (no #236 regression).
//
// Run: node tests/component/dom_acceptance_issue244_plan.mjs
// ============================================================================

import { readFileSync } from "node:fs";
import assert from "node:assert/strict";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const require = createRequire(path.join(ROOT, "component/package.json"));
const { JSDOM } = require("jsdom");

const FIXTURE = JSON.parse(
  readFileSync(path.join(ROOT, "tests/component/fixtures/view_model_issue244_plan.json"), "utf8")
);
const JOURNEY = FIXTURE.journey;
const LOT_ENTRUSTED = FIXTURE.cases.entrusted;
const LOT_CUSTOMER_SELF = FIXTURE.cases.customerSelf;
const LOT_UNKNOWN_FLOW = FIXTURE.cases.unknownFlow;
const SIBLING_QUOTE = FIXTURE.siblingQuoteThatMustNeverRender;

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
window.URL.createObjectURL = () => "blob:mock-url";
window.URL.revokeObjectURL = () => {};

const tick = (ms = 80) => new Promise((r) => setTimeout(r, ms));
const $ = (sel, root = window.document) => [...root.querySelectorAll(sel)];
const text = (el) => (el.textContent || "").replace(/\s+/g, " ").trim();
const bodyText = () => text(window.document.body);

function findClickable(needle, sel = "a,button", root = window.document) {
  const els = $(sel, root);
  return els.find((el) => text(el) === needle)
    || els.find((el) => text(el).startsWith(needle))
    || els.find((el) => text(el).includes(needle))
    || null;
}

async function click(needle, sel = "a,button", root = window.document) {
  const el = findClickable(needle, sel, root);
  assert.ok(el, `clickable "${needle}" not found`);
  el.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
  await tick();
  return el;
}

const host = window.document.createElement("div");
window.document.body.appendChild(host);

let triggers = [];
const mountRef = { current: null };
function invoke(data) {
  return mountRef.current({
    name: "logi_shell",
    data,
    parentElement: host,
    setTriggerValue: (event, value) => triggers.push({ event, value }),
  });
}

let passed = 0;
function ok(name) {
  passed += 1;
  console.log(`  ✓ ${name}`);
}

async function openLot(shipmentId) {
  await click("Lô Hàng", "a", $("aside")[0]);
  // The seeded lots predate "tháng này"; the list filter is the REAL control,
  // so the test uses it instead of patching the fixture's created date.
  const allTime = findClickable("Tất cả thời gian", "button");
  if (allTime) { allTime.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true })); await tick(); }
  await click(shipmentId, "a", $("table.tbl")[0]);
  await tick(120);
  assert.equal(text($("h1")[0]), "Lô hàng " + shipmentId, `detail header wrong for ${shipmentId}`);
  const journey = $('[data-testid="shipment-journey"]')[0];
  assert.ok(journey, `journey section missing for ${shipmentId}`);
  return journey;
}

async function closePlanPanel() {
  const close = $('[data-testid="plan-panel-close"]')[0];
  assert.ok(close, "plan panel close button missing");
  close.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
  await tick();
}

// ---------------------------------------------------------------------------
console.log("STEP 1 — boot the shipped bundle");
{
  const mod = await import(path.join(ROOT, "component/dist/logi-shell.js"));
  assert.equal(typeof mod.default, "function", "bundle must default-export the mount function");
  mountRef.current = mod.default;
  invoke(JOURNEY);
  await tick(160);
  const t = bodyText();
  assert.ok(!t.includes("process is not defined"), "process is not defined leaked");
  assert.ok(!t.includes("BidiComponent Error"), "BidiComponent Error rendered");
  ok("bundle mounted with the real backend view model");
}

// ---------------------------------------------------------------------------
console.log("STEP 2 — Node 00 is the FIRST journey node and opens a panel in the map");
{
  const journey = await openLot(LOT_ENTRUSTED);
  const stepper = [...journey.querySelectorAll('[data-testid^="journey-step-"]')];
  assert.ok(stepper.length > 1, "compact stepper must render journey nodes");
  assert.equal(stepper[0].getAttribute("data-testid"), "journey-step-plan",
    "Node 00 must be the first journey node");
  assert.ok(text(stepper[0]).toUpperCase().includes("KẾ HOẠCH"), "Node 00 label must be KẾ HOẠCH");
  assert.ok(text(stepper[0]).includes("00"), "Node 00 must be numbered 00");
  const order = stepper.map((el) => el.getAttribute("data-testid"));
  assert.equal(order[0], "journey-step-plan");
  // Node 00 must precede EVERY operational node of the lot. These seeded lots
  // are ROAD lots, so their first operational node is the main carriage; when a
  // booking/pickup node exists it must also come after Node 00.
  const operational = order.filter((id) => id !== "journey-step-plan");
  assert.ok(operational.length > 0, "the lot must still expose its operational nodes");
  ok(`Node 00 rendered first: ${order.join(" → ")}`);
}

// ---------------------------------------------------------------------------
console.log("STEP 3 — the plan panel reads the lot's EXACT quote and the CUSTOMER contract");
{
  const journey = $('[data-testid="shipment-journey"]')[0];
  const planStep = journey.querySelector('[data-testid="journey-step-plan"]');
  planStep.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
  await tick();
  const panel = $('[data-testid="plan-quick-panel"]')[0];
  assert.ok(panel, "clicking Node 00 must open the plan panel INSIDE the journey");
  assert.equal(panel.closest('[data-testid="journey-side-panel"]') !== null, true,
    "the plan panel must be the journey side panel, not a separate screen");

  const quote = panel.querySelector('[data-testid="plan-item-quotation"]');
  const contract = panel.querySelector('[data-testid="plan-item-customer_contract"]');
  const advance = panel.querySelector('[data-testid="plan-item-customer_advance"]');
  assert.ok(quote && contract && advance, "the three plan items must render");

  // 3.1 — the exact quote, never the same customer's other ACCEPTED quote.
  assert.ok(text(quote).includes("BG-244B"), `lot quote missing: ${text(quote)}`);
  assert.equal(quote.getAttribute("data-item-state"), "LINKED");
  assert.ok(!text(quote).includes(SIBLING_QUOTE), "a sibling quote of the same customer leaked");
  assert.ok(text(quote).includes("Đã gửi khách"), "the quote status must be the real one");
  assert.ok(!text(quote).includes("Khách đã chấp nhận"),
    "a linked quote must not be presented as accepted");
  const quoteCta = panel.querySelector('[data-testid="plan-item-cta-quotation"]');
  assert.equal(quoteCta.getAttribute("href"), "/kinh-doanh-bao-gia?q=BG-244B",
    "Mở báo giá must open the EXISTING quote screen for this exact quote");

  // 3.2 — customer contract, never the TT↔sub-agent instrument, never "Đã ký".
  assert.ok(text(contract).includes("HDMB-244"), `customer contract missing: ${text(contract)}`);
  assert.ok(!text(contract).includes("HDMB-SUB-244"),
    "the TT↔sub-agent purchase contract must never be the customer contract");
  assert.equal(contract.getAttribute("data-signature"), "UNVERIFIED");
  assert.ok(!text(contract).includes("Đã ký"), "signature must never be inferred");
  assert.ok(text(contract).includes("Chưa xác minh chữ ký"), "the unverified signature must be explicit");
  const contractCta = panel.querySelector('[data-testid="plan-item-cta-customer_contract"]');
  assert.equal(contractCta.getAttribute("href"), "/hop-dong/HDMB-244",
    "Mở hợp đồng must open the EXISTING contract screen");

  // 3.3 — entrusted advance stays unverified and unclassified receipts are not money.
  assert.equal(advance.getAttribute("data-item-state"), "UNVERIFIED");
  assert.ok(text(advance).includes("Chưa xác minh đã nhận"), "advance state must stay unverified");
  assert.ok(text(advance).includes("cần đối soát"), "unclassified receipts must be surfaced as reconciliation");
  assert.ok(!/20[\.,]?000[\.,]?000/.test(text(panel)), "an unclassified receipt amount must never render");
  assert.ok(panel.querySelector('[data-testid="plan-item-cta-customer_advance"]'),
    "the advance item must offer the EXISTING finance surface");
  ok("quote = exact quote_id, contract = customer contract (unsigned), advance = unverified");
}

// ---------------------------------------------------------------------------
console.log("STEP 4 — 'Đang thiếu gì / cần làm gì tiếp?' comes from the same facts");
{
  const panel = $('[data-testid="plan-quick-panel"]')[0];
  const next = panel.querySelector('[data-testid="plan-next-actions"]');
  const items = [...next.querySelectorAll("li")].map(text);
  assert.ok(items.some((line) => line.includes("chưa có trạng thái khách chấp nhận")),
    `accepted-quote gap missing: ${items.join(" | ")}`);
  assert.ok(items.some((line) => line.includes("chưa có bằng chứng chữ ký")),
    `signature gap missing: ${items.join(" | ")}`);
  assert.ok(items.some((line) => line.includes("Chưa xác minh khoản khách chuyển tiền hàng")),
    `advance gap missing: ${items.join(" | ")}`);
  assert.ok(!/tạo công nợ|phát sinh công nợ/i.test(text(next)),
    "the plan panel must not invent a debt");
  ok(`${items.length} next-action lines derived from the three items`);
}

// ---------------------------------------------------------------------------
console.log("STEP 5 — closing the panel returns to the SAME lot + node");
{
  await closePlanPanel();
  const journey = $('[data-testid="shipment-journey"]')[0];
  assert.ok(text($("h1")[0]).includes(LOT_ENTRUSTED), "closing the plan must keep the same lot");
  const step = journey.querySelector('[data-testid="journey-step-plan"]');
  assert.equal(step.getAttribute("aria-pressed"), "true", "Node 00 must remain the picked node");
  step.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
  await tick();
  assert.ok($('[data-testid="plan-quick-panel"]')[0], "re-opening Node 00 must show the same plan panel");
  ok("panel closed and re-opened on the same lot/node");
}

// ---------------------------------------------------------------------------
console.log("STEP 6 — Node 00 sits above booking on the detailed map and keeps the plan thread");
{
  await closePlanPanel();
  await click("Bản đồ chi tiết", "button");
  const map = $('[data-testid="journey-map-viewport"]')[0];
  assert.ok(map, "the detailed journey map must open");
  const plan = map.querySelector('[data-testid="journey-node-plan"]');
  const firstOperational = map.querySelector('[data-testid="journey-node-MAIN_CARRIAGE"]')
    || map.querySelector('[data-testid="journey-node-booking"]')
    || map.querySelector('[data-testid="journey-node-pickup"]');
  assert.ok(plan, "Node 00 must exist on the detailed map");
  assert.ok(firstOperational, "the lot's first operational node must still exist");
  const planTop = Number(plan.style.top.replace("px", ""));
  const opTop = Number(firstOperational.style.top.replace("px", ""));
  assert.ok(planTop < opTop,
    `Node 00 must be drawn above the first operational node (plan=${planTop}, op=${opTop})`);
  assert.equal(text(map.querySelector('[data-testid="journey-node-number-plan"]')), "00",
    "Node 00 must be numbered 00 on the map");
  assert.equal(text(map.querySelector(`[data-testid="journey-node-number-${firstOperational.dataset.testid.replace("journey-node-", "")}"]`)), "1",
    "the first operational node must keep its original number");
  // #236 regression: the node conversation still exists for BOTH nodes and the
  // Node 00 thread is the canonical `plan` stage.
  assert.ok(map.querySelector('[data-testid="journey-node-discussion-plan"]'),
    "Node 00 must keep its in-map conversation affordance");
  const opId = firstOperational.dataset.testid.replace("journey-node-", "");
  assert.ok(map.querySelector(`[data-testid="journey-node-discussion-${opId}"]`),
    "the operational node's conversation must not regress");
  ok(`Node 00 drawn above ${opId}, numbered 00/1, plan + ${opId} conversations intact`);
}

// ---------------------------------------------------------------------------
console.log("STEP 7 — CUSTOMER_SELF lot: quote missing, advance not applicable");
{
  await openLot(LOT_CUSTOMER_SELF);
  const journey = $('[data-testid="shipment-journey"]')[0];
  journey.querySelector('[data-testid="journey-step-plan"]')
    .dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
  await tick();
  const panel = $('[data-testid="plan-quick-panel"]')[0];
  assert.ok(panel, "the plan panel must open for a customer-self lot too");
  const quote = text(panel.querySelector('[data-testid="plan-item-quotation"]'));
  const advance = text(panel.querySelector('[data-testid="plan-item-customer_advance"]'));
  assert.ok(quote.includes("Chưa gắn báo giá"), `missing-quote state wrong: ${quote}`);
  assert.ok(!quote.includes("BG-244B"), "another lot's quote leaked into this lot");
  assert.ok(advance.includes("Không áp dụng"), `customer-self advance must be N/A: ${advance}`);
  ok("customer-self lot: 'Chưa gắn báo giá' + 'Không áp dụng'");
}

// ---------------------------------------------------------------------------
console.log("STEP 8 — unknown import form: advance stays undetermined");
{
  await openLot(LOT_UNKNOWN_FLOW);
  const journey = $('[data-testid="shipment-journey"]')[0];
  journey.querySelector('[data-testid="journey-step-plan"]')
    .dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
  await tick();
  const advance = text($('[data-testid="plan-item-customer_advance"]')[0]);
  assert.ok(advance.includes("Chưa xác nhận hình thức nhập khẩu"), `unknown flow wording wrong: ${advance}`);
  assert.ok(!advance.includes("Không áp dụng"), "an unknown flow must not be resolved to N/A");
  ok("unknown import form is never resolved into applicable/not-applicable");
}

console.log(`\nISSUE244_PLAN_DOM_ACCEPTANCE=PASS (${passed} checks)`);
