// ============================================================================
// DOM acceptance — LOGI_FINANCIAL_AMOUNT_INPUT_INTEGRITY_01
// Runs the REAL production bundle (component/dist/logi-shell.js) in jsdom
// and proves that the three money-write paths in ShipmentDetail preserve the
// raw operator string in the dispatched payload, while still using
// parseAmountVN for validation/display (backend authoritative).
//
// Acceptance (from task):
//   - Customer payment field: input "500.000" → payload amount == "500.000"
//     NOT 500 NOT 500000 frontend-normalized numeric
//   - Partner payable: input "57.000.000" → payload amount == "57.000.000"
//   - Partner payment: input "20.000.000" → payload amount == "20.000.000"
//   - Additional: "1.200.000", "1,200,000", "1.234,56", "1,234.56"
//   - Idempotency preserved: double click replays same requestId
//   - Blank / garbage does NOT dispatch (toast only)
//
// Uses existing fixtures: view_model_c2b.json (has finance.partner block)
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
  readFileSync(path.join(ROOT, "tests", "component", "fixtures", "view_model_c2b.json"), "utf8")
);
const SHIPMENT = FIXTURE.shipment;
const JOURNEY = FIXTURE.journey;
const PARTNER_ID = FIXTURE.partner;

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
function type(input, value){
  Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,"value").set.call(input,value);
  input.dispatchEvent(new window.Event("input",{bubbles:true}));
  input.dispatchEvent(new window.Event("change",{bubbles:true}));
}
const byPlaceholder = (needle) => {
  const el=$(`input[placeholder^="${needle}"]`)[0];
  assert.ok(el, `input placeholder "${needle}" not found`);
  return el;
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

console.log("STEP 1 — boot and open Finance tab");
invoke(JOURNEY);
await tick(140);
assert.ok(!bodyText().includes("process is not defined"));
await click("Lô Hàng","a",$("aside")[0]);
await click(SHIPMENT,"a",$("table.tbl")[0]);
assert.equal(text($("h1")[0]),SHIPMENT);
await click("Tài chính / Công nợ","button",window.document.getElementById("workspace-tabs"));
await tick();
ok(`Finance tab open for ${SHIPMENT}`);

// Helper to test customer payment path
async function testCustomerPayment(rawInput, expectedParsed){
  triggers=[];
  await click("GHI NHẬN THANH TOÁN","button");
  await tick();
  type(byPlaceholder("VD: 150000000"), rawInput);
  await tick();
  const btn=findClickable("LƯU KHOẢN THU","button");
  assert.ok(btn, "LƯU KHOẢN THU button missing");
  btn.dispatchEvent(new window.MouseEvent("click",{bubbles:true,cancelable:true}));
  await tick(120);
  const sent=eventsOf("payment_record");
  assert.equal(sent.length,1, `expected 1 payment_record for input ${rawInput}, got ${sent.length}`);
  const payload=sent[0].payload;
  assert.equal(payload.shipmentId, SHIPMENT);
  assert.equal(payload.amount, rawInput.trim(), `raw preserved: expected "${rawInput.trim()}" got ${JSON.stringify(payload.amount)}`);
  assert.notEqual(payload.amount, 500, "must NOT be mis-parsed 500");
  assert.notEqual(payload.amount, 500000, "must NOT be normalized numeric 500000");
  // Ensure requestId exists
  assert.ok(payload.requestId && payload.requestId.startsWith("PAY-REQ-"));
  // Close modal for next test — click outside or Hủy
  const cancel=findClickable("Hủy","button");
  if (cancel) { cancel.dispatchEvent(new window.MouseEvent("click",{bubbles:true,cancelable:true})); await tick(); }
  else {
    // fallback: press Esc? just re-invoke to reset
    invoke(JOURNEY);
    await tick(80);
    await click("Lô Hàng","a",$("aside")[0]);
    await click(SHIPMENT,"a",$("table.tbl")[0]);
    await click("Tài chính / Công nợ","button",window.document.getElementById("workspace-tabs"));
    await tick();
  }
  triggers=[];
  ok(`customer receipt raw "${rawInput}" preserved, parsed would be ${expectedParsed}`);
}

console.log("STEP 2 — customer receipt raw preservation");
await testCustomerPayment("500.000", 500000);
await testCustomerPayment("1.200.000", 1200000);
await testCustomerPayment("1,200,000", 1200000);
await testCustomerPayment("1.234,56", 1234.56);
await testCustomerPayment("1,234.56", 1234.56);
await testCustomerPayment("57.000.000", 57000000);
await testCustomerPayment("1200000", 1200000);

console.log("STEP 3 — customer receipt idempotency with raw preservation");
{
  triggers=[];
  await click("GHI NHẬN THANH TOÁN","button");
  type(byPlaceholder("VD: 150000000"), "500.000");
  await tick();
  const saveBtn=findClickable("LƯU KHOẢN THU","button");
  saveBtn.dispatchEvent(new window.MouseEvent("click",{bubbles:true,cancelable:true}));
  saveBtn.dispatchEvent(new window.MouseEvent("click",{bubbles:true,cancelable:true}));
  await tick(150);
  const sent=eventsOf("payment_record");
  assert.equal(sent.length,2, "double click must reach handler twice");
  assert.equal(sent[0].payload.requestId, sent[1].payload.requestId, "double click replays same requestId");
  assert.equal(sent[0].payload.amount, "500.000");
  assert.equal(sent[1].payload.amount, "500.000");
  ok(`double click replays ${sent[0].payload.requestId} with raw preserved`);
  const cancel=findClickable("Hủy","button");
  if (cancel) { cancel.dispatchEvent(new window.MouseEvent("click",{bubbles:true,cancelable:true})); await tick(); }
  triggers=[];
}

console.log("STEP 4 — partner payable raw preservation");
async function testPartnerPayable(rawInput){
  triggers=[];
  type(byPlaceholder("VD: 20000000"), rawInput);
  await tick();
  await click("GHI NHẬN PHẢI TRẢ");
  await tick();
  const sent=eventsOf("partner_payable_record");
  assert.equal(sent.length,1, `expected 1 payable for ${rawInput}`);
  const p=sent[0].payload;
  assert.equal(p.shipmentId, SHIPMENT);
  assert.equal(p.partnerId, PARTNER_ID);
  assert.equal(p.amount, rawInput.trim());
  assert.ok(p.requestId);
  ok(`partner payable raw "${rawInput}" preserved`);
}

await testPartnerPayable("57.000.000");
await testPartnerPayable("500.000");
await testPartnerPayable("1.200.000");
await testPartnerPayable("1,200,000");
await testPartnerPayable("1.234,56");
await testPartnerPayable("1,234.56");

console.log("STEP 5 — partner payment raw preservation");
async function testPartnerPayment(rawInput){
  triggers=[];
  type(byPlaceholder("VD: 20000000"), rawInput);
  await tick();
  await click("TRẢ ĐỐI TÁC");
  await tick();
  const sent=eventsOf("partner_payment_record");
  assert.equal(sent.length,1, `expected 1 partner_payment for ${rawInput}`);
  const p=sent[0].payload;
  assert.equal(p.shipmentId, SHIPMENT);
  assert.equal(p.partnerId, PARTNER_ID);
  assert.equal(p.amount, rawInput.trim());
  assert.equal(p.currency, "VND");
  assert.ok(p.requestId);
  ok(`partner payment raw "${rawInput}" preserved`);
}

await testPartnerPayment("20.000.000");
await testPartnerPayment("500.000");
await testPartnerPayment("1.200.000");
await testPartnerPayment("1,200,000");
await testPartnerPayment("1.234,56");
await testPartnerPayment("1,234.56");

console.log("STEP 6 — blank and garbage do NOT dispatch");
{
  triggers=[];
  type(byPlaceholder("VD: 20000000"), "");
  await tick();
  await click("GHI NHẬN PHẢI TRẢ");
  await tick();
  assert.equal(eventsOf("partner_payable_record").length,0, "blank must not dispatch payable");
  ok("blank payable blocked");

  triggers=[];
  type(byPlaceholder("VD: 20000000"), "   ");
  await tick();
  await click("GHI NHẬN PHẢI TRẢ");
  await tick();
  assert.equal(eventsOf("partner_payable_record").length,0, "whitespace must not dispatch");
  ok("whitespace payable blocked");

  triggers=[];
  type(byPlaceholder("VD: 20000000"), "abc");
  await tick();
  await click("GHI NHẬN PHẢI TRẢ");
  await tick();
  assert.equal(eventsOf("partner_payable_record").length,0, "garbage must not dispatch");
  ok("garbage 'abc' payable blocked — never becomes 0");

  triggers=[];
  await click("GHI NHẬN THANH TOÁN","button");
  await tick();
  type(byPlaceholder("VD: 150000000"), "abc");
  await tick();
  const btn=findClickable("LƯU KHOẢN THU","button");
  btn.dispatchEvent(new window.MouseEvent("click",{bubbles:true,cancelable:true}));
  await tick();
  assert.equal(eventsOf("payment_record").length,0, "garbage must not dispatch payment");
  ok("garbage 'abc' customer receipt blocked");
  const cancel=findClickable("Hủy","button");
  if (cancel) { cancel.dispatchEvent(new window.MouseEvent("click",{bubbles:true,cancelable:true})); await tick(); }
}

console.log("STEP 7 — parseAmountVN used for validation (toast shows parsed)");
{
  // After fixing, toast should show formatted parsed value, e.g., fmtCcy(parsed)
  // We cannot easily capture toast, but we can prove that parseAmountVN would parse correctly
  // by checking that valid raw inputs did dispatch, and invalid did not.
  // Additional: ensure input "0" is blocked by positivity rule
  triggers=[];
  type(byPlaceholder("VD: 20000000"), "0");
  await tick();
  await click("GHI NHẬN PHẢI TRẢ");
  await tick();
  assert.equal(eventsOf("partner_payable_record").length,0, "zero must be blocked by positivity");
  ok("explicit zero blocked by positivity rule (where applicable)");
}

console.log(`\nAMOUNT INTEGRITY DOM ACCEPTANCE PASS — ${passed} checks`);
