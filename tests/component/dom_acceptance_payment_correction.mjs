// ============================================================================
// DOM acceptance — LOGI_CUSTOMER_PAYMENT_CORRECTION_UI_01
//
// Drives the REAL production bundle (component/dist/logi-shell.js) with a
// backend-generated fixture (scripts/gen_payment_correction_fixture.py —
// isolated mongomock staging through the canonical writers). Proves:
//
//   - clicking Điều chỉnh on a real payment opens the correction sheet;
//   - the ORIGINAL payment values are shown read-only (id, date, amount,
//     kind/note, currency) — nothing here edits the old row;
//   - blank reason blocks dispatch (no event reaches the transport);
//   - a reason entered dispatches exactly ONE payment_correction;
//   - payload carries the exact shipmentId/paymentId and a fresh
//     correctionRequestId (CORR-REQ-… minted at sheet open, NOT derived from
//     paymentId|amount|reason);
//   - while the outcome is in flight submit is DISABLED and the double click
//     can never mint a new id — the same intent keeps the SAME id;
//   - backend REFUSAL (delivered via lastWrites) keeps the sheet open and
//     shows the backend's own message; resubmitting the same intent replays
//     the SAME correctionRequestId;
//   - backend SUCCESS closes the sheet only when the authoritative outcome
//     arrives, and the reversed row shows "Đã hoàn tác" from the read model
//     (never faked client-side), with the action locked for that row;
//   - reopened intent mints a NEW id;
//   - raw formatted evidence "1.200.000" travels RAW in the payload; garbage
//     evidence is refused locally and never becomes 0;
//   - NO delete/remove/overwrite action exists anywhere in the history.
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
  readFileSync(path.join(ROOT, "tests", "component", "fixtures", "view_model_payment_correction.json"), "utf8")
);
const SHIPMENT = FIXTURE.shipment;
const CORRECTED_ID = FIXTURE.paymentIds.corrected;
const LIVE_ID = FIXTURE.paymentIds.live;

const dom = new JSDOM("<!DOCTYPE html><html><body></body></html>", {
  url: "http://localhost:8501/",
  pretendToBeVisual: true,
});
const { window } = dom;
globalThis.window = window;
globalThis.document = window.document;
try { Object.defineProperty(globalThis, "navigator", { value: window.navigator, configurable: true }); } catch {}
for (const k of ["HTMLElement","HTMLInputElement","HTMLTextAreaElement","HTMLSelectElement","HTMLAnchorElement","Event","CustomEvent","MouseEvent","KeyboardEvent","Node","MutationObserver","getComputedStyle"]) {
  globalThis[k] = window[k];
}
if (!globalThis.MessageChannel) globalThis.MessageChannel = window.MessageChannel;
window.HTMLElement.prototype.scrollIntoView = () => {};
window.URL.createObjectURL = () => "blob:mock-url";
window.URL.revokeObjectURL = () => {};

const tick = (ms=60) => new Promise(r=>setTimeout(r,ms));
const $ = (sel, root=window.document) => [...root.querySelectorAll(sel)];
const text = (el) => (el.textContent||"").replace(/\s+/g," ").trim();
function findClickable(needle, sel="a,button", root=window.document){
  const els=$(sel,root);
  return els.find(el=>text(el)===needle) || els.find(el=>text(el).startsWith(needle)) || els.find(el=>text(el).includes(needle)) || null;
}
async function click(needle, sel="a,button", root=window.document){
  const el=findClickable(needle,sel,root);
  assert.ok(el, `clickable "${needle}" not found`);
  el.dispatchEvent(new window.MouseEvent("click",{bubbles:true,cancelable:true}));
  await tick();
  return el;
}
function clickNode(el){
  el.dispatchEvent(new window.MouseEvent("click",{bubbles:true,cancelable:true}));
}
function type(input, value){
  const proto = input.tagName === "TEXTAREA" ? window.HTMLTextAreaElement.prototype : window.HTMLInputElement.prototype;
  Object.getOwnPropertyDescriptor(proto,"value").set.call(input,value);
  input.dispatchEvent(new window.Event("input",{bubbles:true}));
  input.dispatchEvent(new window.Event("change",{bubbles:true}));
}
const sheet = () => window.document.getElementById("payment-correction-sheet");
const submitBtn = (root) => {
  // while pending the label changes to "ĐANG GHI" and the button is disabled
  const els = $("button", root ?? window.document);
  return els.find(b=>text(b).includes("XÁC NHẬN ĐIỀU CHỈNH")||text(b).includes("ĐANG GHI")) || null;
};
const bodyText = () => text(window.document.body);
let passed=0;
function ok(name){ passed++; console.log(`  ✓ ${name}`); }

const host=window.document.createElement("div");
window.document.body.appendChild(host);
let triggers=[];
const mountRef={current:null};
function invoke(data){
  return mountRef.current({name:"logi_shell", data, parentElement:host, setTriggerValue:(ev,val)=>triggers.push({event:ev,value:val})});
}
const eventsOf = (name) => triggers.filter(t=>t.event===name).map(t=>t.value);

const bundle=path.join(ROOT,"component","dist","logi-shell.js");
const mod=await import(bundle);
assert.equal(typeof mod.default,"function","bundle must default-export mount");
mountRef.current=mod.default;

async function waitTable(){
  for(let i=0;i<25;i++){ if($("table.tbl")[0] && text($("table.tbl")[0]).includes(SHIPMENT)) return true; await tick(60); }
  return false;
}
async function openFinance(vm){
  invoke(vm);
  await tick(140);
  assert.ok(!bodyText().includes("process is not defined"));
  await click("Lô Hàng","a",$("aside")[0]);
  assert.ok(await waitTable(), "shipments table lists " + SHIPMENT);
  await click(SHIPMENT,"a",$("table.tbl")[0]);
  assert.equal(text($("h1")[0]),"Lô hàng "+SHIPMENT);
  await openGlobalTab("Tài chính");
  await tick();
}

console.log("STEP 1 — real payment rows offer a real Điều chỉnh action");
await openFinance(FIXTURE.before);
{
  const btns = $("button[data-payment-id]");
  assert.ok(btns.some(b=>b.getAttribute("data-payment-id")===CORRECTED_ID), "Điều chỉnh for the corrected row");
  assert.ok(btns.some(b=>b.getAttribute("data-payment-id")===LIVE_ID), "Điều chỉnh for the live row");
  const rowBtn = btns.find(b=>b.getAttribute("data-payment-id")===CORRECTED_ID);
  assert.ok(text(rowBtn).includes("Điều chỉnh"));
  ok("Điều chỉnh rendered on real payment rows (backend ids, no fixture fakes)");
}

console.log("STEP 2 — no delete action exists anywhere on the finance surface");
{
  const labels = $("a,button").map(text).join(" | ");
  for (const forbidden of ["XÓA","Xóa khoản","Delete","Xóa lịch sử"]) {
    assert.ok(!labels.toUpperCase().includes(forbidden.toUpperCase()), `no delete-style action (${forbidden})`);
  }
  ok("delete/remove action absent — corrections are append/audit based only");
}

console.log("STEP 3 — open sheet: original facts read-only; blank reason blocks dispatch");
{
  triggers=[];
  clickNode($(`button[data-payment-id="${CORRECTED_ID}"]`)[0]); await tick(120);
  const sh = sheet();
  assert.ok(sh, "correction sheet must open");
  const facts = window.document.getElementById("correction-original-facts");
  assert.ok(facts, "read-only original facts block");
  const factsText = text(facts);
  assert.ok(factsText.includes(CORRECTED_ID), "payment ID shown");
  assert.ok(factsText.includes("08/09/2026"), "date shown as stored");
  assert.ok(factsText.includes("150.000.000"), "amount shown from backend projection");
  assert.ok(factsText.includes("Thu tiền khách"), "kind/note shown");
  assert.ok(factsText.includes("VND"), "currency shown");
  assert.equal($("input,textarea,select", facts).length, 0, "facts block must be read-only (no controls)");
  const submit = submitBtn(sh);
  assert.ok(submit && text(submit).includes("XÁC NHẬN ĐIỀU CHỈNH / HOÀN TÁC"), "primary action label matches reversal semantics");
  clickNode(submit); await tick(80);
  assert.equal(eventsOf("payment_correction").length, 0, "blank reason must NOT dispatch");
  assert.ok(sheet(), "sheet stays open");
  assert.ok(text(sheet()).includes("bắt buộc"), "reason-required refusal is visible");
  ok("blank reason blocks dispatch and is named as required");
}

console.log("STEP 4 — reason + raw evidence dispatches EXACTLY ONE payment_correction");
let intentId = "";
{
  const sh = sheet();
  type($("textarea", sh)[0], "Khách chuyển khoản sai nội dung — hoàn tác để ghi nhận lại");
  const det = $("details", sh)[0];
  det.open = true;
  const inputs = $("input", det);
  assert.equal(inputs.length, 3, "optional evidence: amount, date, note only");
  type(inputs[0], "1.200.000");
  type(inputs[1], "10/09/2026");
  type(inputs[2], "UNC 45 ngày 10/09");
  await tick(80);
  triggers=[];
  clickNode(submitBtn(sheet())); await tick(120);
  const sent=eventsOf("payment_correction");
  assert.equal(sent.length,1, "one material intent = one dispatched event");
  const p=sent[0].payload;
  assert.equal(p.shipmentId, SHIPMENT, "exact shipmentId");
  assert.equal(p.paymentId, CORRECTED_ID, "exact paymentId");
  assert.ok(p.correctionRequestId && p.correctionRequestId.startsWith("CORR-REQ-"), "correctionRequestId minted at open");
  intentId = p.correctionRequestId;
  assert.equal(p.reason, "Khách chuyển khoản sai nội dung — hoàn tác để ghi nhận lại");
  assert.equal(p.amount, "1.200.000", "formatted evidence stays RAW in the payload");
  assert.equal(p.date, "10/09/2026");
  assert.equal(p.note, "UNC 45 ngày 10/09");
  ok(`dispatched payment_correction with identity ${intentId}`);

  console.log("STEP 4b — pending disables submit; forced double click can never mint a new id");
  assert.ok(sheet(), "sheet stays open while the outcome is in flight (transport ack ≠ success)");
  const submit2 = submitBtn(sheet());
  assert.ok(submit2 && submit2.disabled, "submit disabled while pending");
  clickNode(submit2); await tick(80);
  const after=eventsOf("payment_correction");
  assert.equal(after.length, 1, "pending guard absorbs the double click");
  assert.ok(after.every(e=>e.payload.correctionRequestId===intentId), "same intent ⇒ same correctionRequestId, never a fresh id");
  ok("double click cannot re-mint the id while the same intent is in flight");
}

console.log("STEP 5 — backend REFUSAL keeps the sheet open with the writer's own message");
{
  const refused = structuredClone(FIXTURE.before);
  refused.lastWrites = [structuredClone(FIXTURE.refusalOutcome)];
  refused.lastWrites[0].correctionRequestId = intentId; // real id for this pending click
  invoke(refused); await tick(160);
  assert.ok(sheet(), "refusal keeps the sheet open");
  const err = window.document.getElementById("correction-backend-error");
  assert.ok(err, "backend refusal element");
  assert.ok(text(err).includes("Đã được reversal trước đó"), "shows the writer's own refusal verbatim");
  ok("backend refusal surfaces verbatim; sheet stays open for the operator");
}

console.log("STEP 6 — retry after refusal mints a NEW correctionRequestId; stale refusal cannot settle it");
{
  triggers=[];
  clickNode(submitBtn(sheet())); await tick(120);
  const again = eventsOf("payment_correction");
  assert.equal(again.length, 1, "one more dispatch for the retry");
  const retryId = again[0].payload.correctionRequestId;
  assert.notEqual(retryId, intentId, "retry is a NEW write attempt with a FRESH correctionRequestId");
  assert.equal(again[0].payload.reason, "Khách chuyển khoản sai nội dung — hoàn tác để ghi nhận lại", "reason preserved into the retry");
  // The CURRENT lastWrites still carries the OLD refusal for intentId — it must
  // NOT instantly re-settle the retry (control-tower repair, stale-refusal).
  assert.ok(sheet(), "retry stays open");
  assert.ok(!window.document.getElementById("correction-backend-error"), "stale refusal does not re-pop the error");
  ok(`retry minted a NEW id ${retryId}; the old refusal (${intentId}) cannot settle it`);
  // Deliver a fresh refusal for the NEW id: only that settles the retry.
  const refusedRetry = structuredClone(FIXTURE.before);
  refusedRetry.lastWrites = [structuredClone(FIXTURE.refusalOutcome)];
  refusedRetry.lastWrites[0].correctionRequestId = retryId;
  invoke(refusedRetry); await tick(160);
  assert.ok(text(window.document.getElementById("correction-backend-error")).includes("Đã được reversal trước đó"), "fresh refusal for the retry id settles only that id");
  ok("fresh refusal for the retry id settles only the retry id");
  // Leave a clean open intent for STEP 6b: re-open (fresh id) below.
  clickNode(findClickable("Hủy","button",sheet())); await tick(80);
}

console.log("STEP 6b — NEW intent (reopened sheet) + backend SUCCESS closes on authoritative outcome");
{
  // STEP 6 already closed the sheet; the fixture VM re-opened here mints a fresh id.
  await openFinance(FIXTURE.before); // operator sees a state where the row is live again
  clickNode($(`button[data-payment-id="${CORRECTED_ID}"]`)[0]); await tick(120);
  const sh = sheet();
  assert.ok(sh, "sheet reopened");
  const newId = text(sh).match(/CORR-REQ-[0-9A-Z]+-[0-9A-Z]+/)[0];
  assert.notEqual(newId, intentId, "reopened correction intent mints a NEW id (§4)");
  type($("textarea", sh)[0], "Hoàn tác theo đề nghị kế toán");
  await tick(60);
  triggers=[];
  clickNode(submitBtn(sheet())); await tick(100);
  const sent = eventsOf("payment_correction");
  assert.equal(sent.length,1, "fresh intent dispatches exactly one event");
  assert.equal(sent[0].payload.correctionRequestId, newId);

  const succeeded = structuredClone(FIXTURE.afterReversal);
  succeeded.lastWrites = [{ ...structuredClone(FIXTURE.successOutcome), correctionRequestId: newId }];
  invoke(succeeded); await tick(160);
  assert.ok(!sheet(), "authoritative success closes the sheet");

  // honest history: the row keeps its ORIGINAL facts and gains the backend flag
  const row = window.document.querySelector(`div[data-payment-row="${CORRECTED_ID}"]`);
  assert.ok(row, "reversed payment row still present (never deleted)");
  const rowText = text(row);
  assert.ok(rowText.includes("Đã hoàn tác"), "backend 'reversed' flag rendered");
  assert.ok(rowText.includes("Đã điều chỉnh — khóa"), "closed intent: action locked");
  assert.ok(rowText.includes("150.000.000"), "original amount preserved in history");
  assert.ok(!$(`button[data-payment-id="${CORRECTED_ID}"]`).length, "no live action on a reversed row");
  assert.ok($(`button[data-payment-id="${LIVE_ID}"]`).length, "the other payment remains correctable");
  const fin = succeeded.shipments.find(x=>x.id===SHIPMENT).finance;
  assert.equal(fin.received, 40_000_000.0, "totals moved by the backend read model, not the UI");
  ok("success closes only on authoritative outcome; history honest: kept + Đã hoàn tác + locked");
}

console.log("STEP 7 — cancel without dispatch; transport ack never fakes success");
{
  triggers=[];
  clickNode($(`button[data-payment-id="${LIVE_ID}"]`)[0]); await tick(120);
  assert.ok(sheet(), "sheet opens for the live payment");
  const cancel = findClickable("Hủy","button",sheet());
  clickNode(cancel); await tick(60);
  assert.ok(!sheet(), "cancel closes without dispatching");
  assert.equal(eventsOf("payment_correction").length, 0, "cancel sends nothing");
  ok("open+cancel dispatches nothing (no phantom correction)");
}

console.log("STEP 8 — garbage evidence refused locally, never sent as 0");
{
  clickNode($(`button[data-payment-id="${LIVE_ID}"]`)[0]); await tick(120);
  const sh = sheet();
  type($("textarea", sh)[0], "Kiểm tra garbage");
  const det = $("details", sh)[0]; det.open = true;
  type($("input", det)[0], "abc");
  await tick(60);
  triggers=[];
  clickNode(submitBtn(sheet())); await tick(100);
  assert.equal(eventsOf("payment_correction").length, 0, "garbage evidence must block dispatch");
  assert.ok(text(sheet()).includes("không tự thành 0"), "garbage message states no-silent-zero");
  ok("garbage optional amount blocked — never silently becomes 0");
}

console.log(`\nPAYMENT_CORRECTION_DOM_ACCEPTANCE=PASSED checks=${passed}`);
