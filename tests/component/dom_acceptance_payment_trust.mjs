// ============================================================================
// DOM acceptance — LOGI_FRONTEND_WORKFLOW_OVERHAUL_01 · P0 PAYMENT TRUST
// (entry point A: ShipmentDetail.recordPay → payment_record)
//
// Drives the REAL production bundle (component/dist/logi-shell.js) with the
// backend-generated payment-correction fixture (isolated mongomock staging).
// Proves the authoritative-outcome contract for the shipment-detail receipt
// sheet:
//
//   - the sheet is a real dialog (role=dialog, aria-modal, accessible name);
//   - initial focus lands inside the sheet and returns to the opener;
//   - blank amount blocks dispatch;
//   - ONE submit = ONE payment_record with a stable PAY-REQ requestId;
//   - the sheet stays open while waiting: pending status names
//     "ĐANG CHỜ BACKEND XÁC NHẬN", submit and Hủy are disabled, fields frozen;
//   - Escape and backdrop click cannot dismiss an in-flight outcome;
//   - no green success exists before the correlated backend answer;
//   - an UNRELATED lastWrites entry (different requestId) cannot fake success;
//   - backend refusal keeps the sheet open, preserves the amount and shows
//     the writer's message inline (role=alert);
//   - retrying the same open intent replays the SAME requestId;
//   - editing the amount mints a NEW requestId (a genuinely new intent);
//   - only the CORRELATED success closes the sheet and then shows green;
//   - reopening mints a fresh id; Escape closes again when not pending.
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

async function openFinanceTab(){
  await click("Lô Hàng","a",window.document.querySelector("aside"));
  for(let i=0;i<25;i++){ if($("table.tbl")[0] && text($("table.tbl")[0]).includes(SHIPMENT)) break; await tick(60); }
  assert.ok(text($("table.tbl")[0]).includes(SHIPMENT), "shipments table lists "+SHIPMENT);
  await click(SHIPMENT,"a",$("table.tbl")[0]);
  assert.equal(text($("h1")[0]),SHIPMENT);
  await click("Tài chính / Công nợ","button",window.document.getElementById("workspace-tabs"));
  await tick();
}

console.log("STEP 0 — boot and open the shipment finance workspace");
await invoke(FIXTURE.before);
await tick(140);
assert.ok(!bodyText().includes("process is not defined"));
await openFinanceTab();
{
  const openers = $("button").filter(b => text(b).includes("GHI NHẬN THANH TOÁN"));
  assert.ok(openers.length >= 1, "GHI NHẬN THANH TOÁN entry visible");
  ok("payment entry point rendered on the finance tab");
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
  const labelledBy = panel.getAttribute("aria-labelledby");
  assert.ok(labelledBy, "aria-labelledby present");
  const heading = window.document.getElementById(labelledBy);
  assert.ok(heading && text(heading).includes("Ghi nhận thanh toán"), "accessible name = visible heading");
  const focusInside = panel.contains(window.document.activeElement);
  assert.ok(focusInside, "initial focus lands inside the sheet");
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

console.log("STEP 3 — one submit = one intent; sheet stays open while waiting");
let intentId = "";
{
  triggers=[];
  type(amountInput(), "50000000"); await tick(80);
  clickNode(submitBtn()); await tick(140);
  const sent = eventsOf("payment_record");
  assert.equal(sent.length, 1, "exactly one payment_record dispatched");
  const p = sent[0].payload;
  assert.equal(p.shipmentId, SHIPMENT, "exact shipmentId");
  assert.equal(p.amount, "50000000", "raw amount preserved");
  assert.match(p.requestId, /^PAY-REQ-/, "stable requestId namespaced");
  intentId = p.requestId;
  assert.ok(text(sheet()).includes(intentId), "sheet shows the request identity");
  const pendingLine = window.document.querySelector('[data-testid="payment-record-pending"]');
  assert.ok(pendingLine && pendingLine.textContent.includes("ĐANG CHỜ BACKEND XÁC NHẬN"), 'pending says "ĐANG CHỜ BACKEND XÁC NHẬN…"');
  assert.equal(pendingLine.getAttribute("role"), "status", "pending announced via role=status");
  assert.ok(submitBtn().disabled, "submit disabled while pending");
  assert.ok(amountInput().disabled, "amount frozen while pending");
  const cancel = findClickable("Hủy","button",sheet());
  assert.ok(cancel.disabled, "Hủy disabled while pending");
  assert.ok(!bodyText().includes("Đã ghi nhận khoản thu"), "NO green success before the backend answer");
  ok(`one intent ${intentId}; pending is truthful; nothing looks successful yet`);
}

console.log("STEP 4 — Escape and backdrop cannot dismiss an in-flight outcome");
{
  pressKey("Escape"); await tick(80);
  assert.ok(sheet(), "Escape does not close while pending");
  const backdrop = sheet().firstElementChild;
  clickNode(backdrop); await tick(80);
  assert.ok(sheet(), "backdrop click does not close while pending");
  ok("in-flight outcome cannot be dismissed by accident");
}

console.log("STEP 5 — an unrelated lastWrites entry cannot fake success");
{
  const unrelated = structuredClone(FIXTURE.before);
  unrelated.lastWrites = [{ event: "payment_record", ok: true, requestId: "PAY-REQ-SOMEONE-ELSE", shipmentId: SHIPMENT }];
  invoke(unrelated); await tick(160);
  assert.ok(sheet(), "sheet still open");
  assert.ok(window.document.querySelector('[data-testid="payment-record-pending"]'), "still pending — no fake success");
  assert.ok(!bodyText().includes("Đã ghi nhận khoản thu"), "still no success claim");
  ok("missing/unrelated lastWrites cannot fake success");
}

console.log("STEP 6 — backend refusal: sheet open, amount preserved, inline error");
{
  const refused = structuredClone(FIXTURE.before);
  refused.lastWrites = [{ event: "payment_record", ok: false, requestId: intentId, shipmentId: SHIPMENT, error: "Bạn không có quyền thực hiện giao dịch tài chính." }];
  invoke(refused); await tick(160);
  assert.ok(sheet(), "refusal keeps the sheet open");
  assert.equal(amountInput().value, "50000000", "original amount still available");
  const err = window.document.getElementById("payment-record-error");
  assert.ok(err, "inline error element present");
  assert.equal(err.getAttribute("role"), "alert", "error announced via role=alert");
  assert.ok(text(err).includes("không có quyền"), "backend's own message displayed");
  assert.ok(!bodyText().includes("Đã ghi nhận khoản thu"), "refusal never looks like success");
  assert.ok(!submitBtn().disabled, "submit re-enabled for a retry");
  ok("refusal keeps the form and shows an actionable inline error");
}

console.log("STEP 7 — retrying the same open intent replays the SAME requestId");
{
  triggers=[];
  clickNode(submitBtn()); await tick(120);
  const again = eventsOf("payment_record");
  assert.equal(again.length, 1, "one retry dispatch");
  assert.equal(again[0].payload.requestId, intentId, "same open intent ⇒ same requestId (backend dedupe)");
  ok("retry replays the same request identity");
}

console.log("STEP 8 — editing the amount mints a NEW intent id");
{
  const refused2 = structuredClone(FIXTURE.before);
  refused2.lastWrites = [{ event: "payment_record", ok: false, requestId: intentId, shipmentId: SHIPMENT, error: "Số tiền không hợp lệ." }];
  invoke(refused2); await tick(160);
  triggers=[];
  type(amountInput(), "60000000"); await tick(80);
  clickNode(submitBtn()); await tick(120);
  const sent = eventsOf("payment_record");
  assert.equal(sent.length, 1, "one dispatch for the new intent");
  assert.notEqual(sent[0].payload.requestId, intentId, "edited draft = NEW requestId");
  assert.equal(sent[0].payload.amount, "60000000");
  intentId = sent[0].payload.requestId;
  ok(`new valid intent minted: ${intentId}`);
}

console.log("STEP 9 — correlated success closes the sheet, THEN green");
{
  const succeeded = structuredClone(FIXTURE.before);
  succeeded.lastWrites = [{ event: "payment_record", ok: true, requestId: intentId, shipmentId: SHIPMENT }];
  invoke(succeeded); await tick(160);
  assert.ok(!sheet(), "authoritative success closes the sheet");
  assert.ok(bodyText().includes("Đã ghi nhận khoản thu"), "green success appears only AFTER the correlated answer");
  ok("success path: close + green only after the backend confirmed");
}

console.log("STEP 10 — reopen mints a fresh id; Escape works again when idle; focus returns");
{
  const opener = $("button").find(b => text(b).includes("GHI NHẬN THANH TOÁN"));
  opener.focus();
  clickNode(opener); await tick(140);
  assert.ok(sheet(), "sheet reopened");
  const freshId = text(sheet()).match(/PAY-REQ-[0-9A-Z]+-[0-9A-Z]+/)[0];
  assert.notEqual(freshId, intentId, "reopened sheet = fresh intent id");
  assert.ok(panelHasFocus(), "focus inside the reopened sheet");
  pressKey("Escape"); await tick(80);
  assert.ok(!sheet(), "Escape closes the idle sheet");
  const back = window.document.activeElement;
  assert.ok(back && text(back).includes("GHI NHẬN THANH TOÁN"), "focus returned to the opener");
  ok("fresh intent per open; Escape closes when idle; focus returns to opener");
}

function panelHasFocus(){
  const sh = sheet();
  if (!sh) return false;
  return sh.contains(window.document.activeElement);
}

console.log(`\nPAYMENT_TRUST_DOM_ACCEPTANCE=PASSED checks=${passed}`);
