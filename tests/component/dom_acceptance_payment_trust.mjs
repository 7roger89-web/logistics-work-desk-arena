// ============================================================================
// DOM acceptance — LOGI_FRONTEND_WORKFLOW_OVERHAUL_01 · P0 PAYMENT TRUST
// (entry point A: ShipmentDetail.recordPay → payment_record)
//
// Repair round 2 (Control Tower review 5243814200). Proves the FULL
// authoritative-outcome contract on the REAL production bundle:
//
//   A. transport ack + no correlated lastWrites        → pending, no green
//   B. unrelated lastWrites (different requestId)      → pending, no green
//   C. matching lastWrite ok WITHOUT finance readback  → STILL pending, no green
//   D. matching ok AND fresh finance.payments requestId→ close + green
//   E. matching refusal X                              → sheet open, amount
//                                                        preserved, inline error
//   F. retry after refusal                             → NEW requestId Y ≠ X
//   G. old refusal X still in lastWrites               → cannot settle Y
//   H. fresh outcome for Y                             → settles only Y
//   I. synchronous double click                        → one dispatch
//
// Success = correlated lastWrite ok  AND  the SAME fresh view-model already
// shows the payment (shipment.finance.payments[].requestId) — never the
// transport, never lastWrites alone.
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

/** Patch the fixture's shipment finance readback with the written payment —
 *  exactly what the backend's fresh read model does after save_direct_shipment_payment. */
function withFinanceReadback(base, requestId, amountVnd) {
  const vm = structuredClone(base);
  const lot = vm.shipments.find((x) => x.id === SHIPMENT);
  assert.ok(lot, "fixture shipment present");
  lot.finance.payments = lot.finance.payments ?? [];
  lot.finance.payments.push({
    requestId,
    date: "18/09/2026",
    kind: "Thu tiền khách",
    amount: amountVnd,
    ccy: "VND",
    by: "staging.support",
  });
  return vm;
}

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
const text = (el) => (el?.textContent||"").replace(/\s+/g," ").trim();
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
  Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,"value").set.call(input,value);
  input.dispatchEvent(new window.Event("input",{bubbles:true}));
  input.dispatchEvent(new window.Event("change",{bubbles:true}));
}
const pressKey = (key) => {
  window.document.dispatchEvent(new window.KeyboardEvent("keydown", { key, bubbles: true, cancelable: true }));
};
const sheet = () => window.document.getElementById("payment-record-sheet");
const submitBtn = () => window.document.querySelector('button[data-testid="payment-record-submit"]');
const amountInput = () => $('input[placeholder^="VD: 150000000"]')[0];
const pendingLine = () => window.document.querySelector('[data-testid="payment-record-pending"]');
const inlineError = () => window.document.getElementById("payment-record-error");
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

console.log("STEP 0 — boot and open the shipment finance workspace");
await invoke(FIXTURE.before);
await tick(140);
assert.ok(!bodyText().includes("process is not defined"));
{
  await click("Lô Hàng","a",window.document.querySelector("aside"));
  for(let i=0;i<25;i++){ if($("table.tbl")[0] && text($("table.tbl")[0]).includes(SHIPMENT)) break; await tick(60); }
  assert.ok(text($("table.tbl")[0]).includes(SHIPMENT), "shipments table lists "+SHIPMENT);
  await click(SHIPMENT,"a",$("table.tbl")[0]);
  assert.equal(text($("h1")[0]),SHIPMENT);
  await click("Tài chính / Công nợ","button",window.document.getElementById("workspace-tabs"));
  await tick();
  ok("finance workspace open");
}

console.log("STEP 1 — the pay sheet is a real, named dialog with initial focus");
{
  triggers=[];
  const opener = $("button").find(b => text(b).includes("GHI NHẬN THANH TOÁN"));
  opener.focus();
  clickNode(opener); await tick(140);
  const sh = sheet();
  assert.ok(sh, "payment sheet opens");
  const panel = sh.querySelector('[role="dialog"]');
  assert.ok(panel, 'role="dialog" present');
  assert.equal(panel.getAttribute("aria-modal"), "true", "aria-modal=true");
  const heading = window.document.getElementById(panel.getAttribute("aria-labelledby"));
  assert.ok(heading && text(heading).includes("Ghi nhận thanh toán"), "accessible name = visible heading");
  assert.ok(panel.contains(window.document.activeElement), "initial focus lands inside the sheet");
  ok("dialog semantics: role + aria-modal + name + initial focus");
}

console.log("STEP 2 — blank amount still blocks dispatch");
{
  triggers=[];
  clickNode(submitBtn()); await tick(80);
  assert.equal(eventsOf("payment_record").length, 0, "no dispatch without an amount");
  assert.ok(sheet(), "sheet stays open");
  ok("blank amount refused locally");
}

console.log("STEP 3 — (A+I) one submit = one intent X; double click absorbed; pending truthful");
let X = "";
{
  triggers=[];
  type(amountInput(), "50000000"); await tick(80);
  // Synchronous double click: the in-flight ref must absorb the second click.
  clickNode(submitBtn());
  clickNode(submitBtn());
  await tick(140);
  const sent = eventsOf("payment_record");
  assert.equal(sent.length, 1, "exactly one payment_record dispatched");
  const p = sent[0].payload;
  assert.equal(p.shipmentId, SHIPMENT);
  assert.equal(p.amount, "50000000", "raw amount preserved");
  assert.match(p.requestId, /^PAY-REQ-/);
  X = p.requestId;
  assert.ok(text(sheet()).includes(X), "sheet shows the request identity");
  assert.ok(pendingLine()?.textContent.includes("ĐANG CHỜ BACKEND XÁC NHẬN"), 'pending says "ĐANG CHỜ BACKEND XÁC NHẬN…"');
  assert.equal(pendingLine().getAttribute("role"), "status");
  assert.ok(submitBtn().disabled, "submit disabled while pending");
  assert.ok(!bodyText().includes("Đã ghi nhận khoản thu"), "NO green success before the backend answer");
  ok(`(A+I) one intent ${X}; double click absorbed; waiting truthfully with no lastWrites`);
}

console.log("STEP 4 — Escape and backdrop cannot dismiss an in-flight outcome");
{
  pressKey("Escape"); await tick(80);
  assert.ok(sheet(), "Escape does not close while pending");
  clickNode(sheet().firstElementChild); await tick(80);
  assert.ok(sheet(), "backdrop click does not close while pending");
  ok("in-flight outcome cannot be dismissed by accident");
}

console.log("STEP 5 — (B) an unrelated lastWrites entry cannot fake success");
{
  const unrelated = structuredClone(FIXTURE.before);
  unrelated.lastWrites = [{ event: "payment_record", ok: true, requestId: "PAY-REQ-SOMEONE-ELSE", shipmentId: SHIPMENT }];
  invoke(unrelated); await tick(160);
  assert.ok(sheet(), "sheet still open");
  assert.ok(pendingLine(), "still pending — no fake success");
  assert.ok(!bodyText().includes("Đã ghi nhận khoản thu"), "still no success claim");
  ok("(B) unrelated lastWrites cannot fake success");
}

console.log("STEP 6 — (E) backend refusal X: sheet open, amount preserved, inline error");
{
  const refused = structuredClone(FIXTURE.before);
  refused.lastWrites = [{ event: "payment_record", ok: false, requestId: X, shipmentId: SHIPMENT, error: "Bạn không có quyền thực hiện giao dịch tài chính." }];
  invoke(refused); await tick(160);
  assert.ok(sheet(), "refusal keeps the sheet open");
  assert.equal(amountInput().value, "50000000", "original amount still available");
  assert.ok(!amountInput().disabled, "form re-enabled");
  const err = inlineError();
  assert.ok(err, "inline error element present");
  assert.equal(err.getAttribute("role"), "alert");
  assert.ok(text(err).includes("không có quyền"), "backend's own message displayed");
  assert.ok(!bodyText().includes("Đã ghi nhận khoản thu"), "refusal never looks like success");
  ok("(E) refusal preserves the form and shows an actionable inline error");
}

console.log("STEP 7 — (F+G) retry mints a NEW id Y; old refusal X cannot settle Y");
let Y = "";
{
  triggers=[];
  clickNode(submitBtn()); await tick(140);
  const retried = eventsOf("payment_record");
  assert.equal(retried.length, 1, "one retry dispatch");
  Y = retried[0].payload.requestId;
  assert.match(Y, /^PAY-REQ-/);
  assert.notEqual(Y, X, "(F) retry after refusal is a NEW write attempt with a NEW requestId");
  assert.equal(retried[0].payload.amount, "50000000", "amount preserved into the retry intent");
  // G: the CURRENT lastWrites still carries the OLD refusal for X (same array
  // as this invoke round). The pending retry is Y — the stale refusal must NOT
  // reconsume it: still pending, error cleared (not re-shown from the old entry).
  assert.ok(pendingLine(), "(G) retry remains pending");
  assert.ok(!inlineError(), "(G) stale refusal X does not re-settle or re-pop the error");
  assert.ok(submitBtn().disabled, "(G) still awaiting the fresh outcome for Y");
  assert.ok(!bodyText().includes("Đã ghi nhận khoản thu"), "(G) nothing succeeded");
  ok(`(F+G) retry intent ${Y} ≠ ${X}; stale refusal X in lastWrites cannot settle it`);
}

console.log("STEP 8 — (C) correlated ok for Y WITHOUT finance readback stays pending");
{
  const okNoReadback = structuredClone(FIXTURE.before);
  okNoReadback.lastWrites = [{ event: "payment_record", ok: true, requestId: Y, shipmentId: SHIPMENT }];
  invoke(okNoReadback); await tick(160);
  assert.ok(sheet(), "sheet stays open");
  assert.ok(pendingLine(), "still pending — ok without the authoritative readback is NOT success");
  assert.ok(!bodyText().includes("Đã ghi nhận khoản thu"), "no green");
  assert.ok(!inlineError(), "not treated as a failure either");
  ok("(C) ok-without-readback = not yet refreshed → pending/truthful, not a failure");
}

console.log("STEP 9 — (D+H) ok for Y AND fresh finance readback → closes + green (settles only Y)");
{
  const succeeded = withFinanceReadback(FIXTURE.before, Y, 50000000);
  succeeded.lastWrites = [{ event: "payment_record", ok: true, requestId: Y, shipmentId: SHIPMENT }];
  invoke(succeeded); await tick(160);
  assert.ok(!sheet(), "authoritative success closes the sheet");
  assert.ok(bodyText().includes("Đã ghi nhận khoản thu"), "green success appears only AFTER ok+readback");
  ok("(D+H) success = correlated ok AND finance.payments requestId readback; only Y settled");
}

console.log("STEP 10 — reopen mints a fresh id; Escape works when idle; focus returns");
{
  const opener = $("button").find(b => text(b).includes("GHI NHẬN THANH TOÁN"));
  opener.focus();
  clickNode(opener); await tick(140);
  assert.ok(sheet(), "sheet reopened");
  const freshId = text(sheet()).match(/PAY-REQ-[0-9A-Z]+-[0-9A-Z]+/)[0];
  assert.notEqual(freshId, Y, "reopened sheet = fresh intent id");
  assert.ok(sheet().contains(window.document.activeElement), "focus inside the reopened sheet");
  pressKey("Escape"); await tick(80);
  assert.ok(!sheet(), "Escape closes the idle sheet");
  assert.ok(text(window.document.activeElement).includes("GHI NHẬN THANH TOÁN"), "focus returned to the opener");
  ok("fresh intent per open; Escape closes when idle; focus returns to opener");
}

console.log(`\nPAYMENT_TRUST_DOM_ACCEPTANCE=PASSED checks=${passed}`);
