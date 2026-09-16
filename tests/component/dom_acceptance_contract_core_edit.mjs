// ============================================================================
// LOGI_CONTRACT_AND_SHIPMENT_CORE_GAPS_01 — DOM acceptance for the contract
// desk's four core facts: the buyer company ("Công ty bên mua"), the visible
// customer search, the operator's explicit "Có PL" / "Không cần PL" decision,
// and the contract date — each shown, editable, and read back from the backend.
//
// Runs the REAL production bundle (component/dist/logi-shell.js) in jsdom over a
// REAL-backend fixture (scripts/gen_contract_shipment_edit_fixture.py — isolated
// mongomock staging; every state was produced by dispatching the same events the
// UI sends through contract_save / customer_getfly_import, then re-reading the
// view-model). Verified contract:
//
//   1. an unset contract renders as UNSET (em dash / "— chưa chọn —" / "Chưa
//      chọn") — the app never shows "Không cần PL" or today's date as a guess
//   2. the buyer is picked through a REAL search over the legal master
//      (visible count, filtered list, explicit no-match), not a hidden id field
//   3. saving emits exactly ONE typed contract_save carrying company_id, date
//      and pl_required — and an untouched counterparty does NOT travel
//   4. the edited values come back from the backend on the next read, including
//      a PL flip made after create (editability, not create-only)
//   5. the GetFly paste on /hop-dong/moi dispatches customer_getfly_import with
//      a requestId, then renders the BACKEND's outcome verbatim (added /
//      skipped), and the "Chấp nhận" refusal keeps its own honest message
//
// Run: node tests/component/dom_acceptance_contract_core_edit.mjs
// ============================================================================

import { readFileSync } from "node:fs";
import assert from "node:assert/strict";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const require = createRequire(path.join(ROOT, "component/package.json"));
const { JSDOM } = require("jsdom");
const FIX = JSON.parse(
  readFileSync(path.join(ROOT, "tests/component/fixtures/view_model_contract_shipment_edit.json"), "utf8")
);

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

const tick = (ms = 60) => new Promise((r) => setTimeout(r, ms));
const $ = (sel, root = window.document) => [...root.querySelectorAll(sel)];
const text = (el) => (el.textContent || "").replace(/\s+/g, " ").trim();
const mainText = () => text($("main")[0] ?? window.document.body);
const byTestId = (id) => $(`[data-testid="${id}"]`)[0] ?? null;
const attr = (id, name) => byTestId(id)?.getAttribute(name) ?? null;

function findClickable(needle, sel = "a,button", root = window.document) {
  const els = $(sel, root);
  return els.find((el) => text(el) === needle) || els.find((el) => text(el).includes(needle)) || null;
}

async function click(needle, sel = "a,button", root = window.document) {
  const el = findClickable(needle, sel, root) ?? (sel === "button" ? byTestId(needle) : null);
  assert.ok(el, `clickable "${needle}" not found`);
  el.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
  await tick();
  return el;
}

async function clickTestId(id) {
  const el = byTestId(id);
  assert.ok(el, `element [data-testid="${id}"] not found`);
  el.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
  await tick();
  return el;
}

async function type(input, value) {
  const proto = input.tagName === "TEXTAREA" ? window.HTMLTextAreaElement.prototype : window.HTMLInputElement.prototype;
  Object.getOwnPropertyDescriptor(proto, "value").set.call(input, value);
  input.dispatchEvent(new window.Event("input", { bubbles: true }));
  await tick();
}

let passed = 0;
function ok(name) {
  passed += 1;
  console.log(`  ✓ ${name}`);
}

/** Rewrite the fixture outcome's requestId to the one the real click produced. */
function withRequestId(state, requestId) {
  const clone = structuredClone(state);
  for (const w of clone.lastWrites ?? []) w.requestId = requestId;
  return clone;
}

const host = window.document.createElement("div");
window.document.body.appendChild(host);
const triggers = [];
const mountRef = { current: null };
let lastInvokeCleanup = null;

function invoke(data) {
  if (lastInvokeCleanup) lastInvokeCleanup();
  const cleanup = mountRef.current({
    name: "logi_shell",
    data,
    parentElement: host,
    setTriggerValue: (event, value) => triggers.push({ event, value }),
  });
  lastInvokeCleanup = cleanup;
  return cleanup;
}

/** Deliver a fresh view-model to the SAME mounted page — exactly what a
 *  Streamlit rerun does: no unmount, so route and local state survive and only
 *  the data channel updates. The outcome of a write must arrive this way,
 *  otherwise the page that is waiting for it is gone. */
function deliver(data) {
  mountRef.current({
    name: "logi_shell",
    data,
    parentElement: host,
    setTriggerValue: (event, value) => triggers.push({ event, value }),
  });
}

/** Boot a state and open the contract workspace on the fixture contract. */
async function bootOnContract(state) {
  invoke(state);
  await tick(120);
  await click("Hợp đồng", "a", $("aside")[0]);
  await click(FIX.contract, "a", $("main")[0]);
  await tick(80);
}

const bundlePath = path.join(ROOT, "component/dist/logi-shell.js");

// ---------------------------------------------------------------------------
console.log("STEP 1 — unset facts render as UNSET, never as an invented answer");
{
  const mod = await import(bundlePath);
  assert.equal(typeof mod.default, "function");
  mountRef.current = mod.default;
  await bootOnContract(FIX.contractUnset);

  const t = mainText();
  assert.ok(t.includes("Danh tính pháp lý"), "overview tab missing");
  assert.ok(t.includes("Công ty bên mua"), "the buyer company must be labelled in business terms");
  // header readback
  assert.ok(t.includes("Ngày hợp đồng"), "the contract date readback row is missing");
  assert.ok(t.includes("Phụ lục (PL)"), "the PL readback row is missing");
  const buyerRow = $("main *").find((el) => text(el) === "Công ty bên mua" && el.children.length === 0);
  assert.ok(buyerRow, "buyer StateRow label not found");
  assert.match(text(buyerRow.parentElement), /^Công ty bên mua\s*—$/, "an unset buyer must read as the unknown dash");

  // the picker is visible and honestly empty
  assert.ok(byTestId("contract-buyer-picker"), "buyer picker missing");
  assert.equal(attr("contract-buyer-picker", "data-selected"), "", "unset buyer must carry no selection");
  assert.equal(text(byTestId("contract-buyer-picker-value")), "— chưa chọn —");
  // PL: the stored answer is still unknown, and the control has NOT defaulted
  assert.ok(t.includes("đang lưu: chưa chọn"), `PL caption must report the stored unknown: ${t.slice(0, 400)}`);
  assert.ok(!t.includes("đang lưu: Không cần PL"), "an unset PL must never be reported as 'Không cần PL'");
  assert.equal(attr("contract-pl-choice-unknown", "aria-pressed"), "true", "PL must rest on 'Chưa chọn'");
  assert.equal(attr("contract-pl-choice-YES", "aria-pressed"), "false");
  assert.equal(attr("contract-pl-choice-NO", "aria-pressed"), "false");
  assert.equal($('input[placeholder="2026-09-05"]')[0].value, "", "no contract date may be pre-filled");
  ok("buyer/date/PL all render as UNKNOWN with no invented default");
}

// ---------------------------------------------------------------------------
console.log("STEP 2 — the buyer is chosen by SEARCH over the legal master");
{
  await clickTestId("contract-buyer-picker-toggle");
  assert.ok(byTestId("contract-buyer-picker-panel"), "search panel did not open");
  const all = $('[data-testid^="contract-buyer-picker-option-"]');
  assert.equal(all.length, 2, "both master companies must be offered");
  assert.ok(all.map((el) => text(el)).join(" | ").includes("TRƯỜNG THÀNH"));

  await type(byTestId("contract-buyer-picker-search"), "PHÚ ANH");
  assert.match(text(byTestId("contract-buyer-picker-count")), /^Thấy 1\/2/, "search count is wrong");
  const filtered = $('[data-testid^="contract-buyer-picker-option-"]');
  assert.equal(filtered.length, 1);
  assert.equal(filtered[0].getAttribute("data-testid"), `contract-buyer-picker-option-${FIX.otherCompany}`);
  assert.ok(text(filtered[0]).includes(FIX.otherCompanyName.split(" ").slice(-2).join(" ")), "label shows the legal name");

  // a query with no hit says so — it never silently picks the first option
  await type(byTestId("contract-buyer-picker-search"), "zzz-khong-ton-tai");
  assert.ok(byTestId("contract-buyer-picker-nomatch"), "an unknown query must report no match");
  assert.ok(!byTestId("contract-buyer-picker-option-TT-COMPANY"), "no option may be clickable when nothing matches");

  await type(byTestId("contract-buyer-picker-search"), "PHÚ ANH");
  await clickTestId(`contract-buyer-picker-option-${FIX.otherCompany}`);
  assert.equal(attr("contract-buyer-picker", "data-selected"), FIX.otherCompany, "the pick must land in the form");
  assert.equal(text(byTestId("contract-buyer-picker-value")), FIX.otherCompanyName);
  assert.equal(byTestId("contract-buyer-picker-panel"), null, "panel must close after picking");
  ok("search, filtered count, explicit no-match, and the chosen legal name");
}

// ---------------------------------------------------------------------------
console.log("STEP 3 — ONE contract_save carries the explicit answers only");
{
  await clickTestId("contract-pl-choice-NO");
  await type($('input[placeholder="2026-09-05"]')[0], "2026-09-05");

  let before = triggers.length;
  await click("LƯU TỔNG QUAN", "button");
  await tick(60);
  let saves = triggers.slice(before).filter((tr) => tr.event === "contract_save");
  assert.equal(saves.length, 1, "exactly one contract_save per click");
  const p = saves[0].value.payload;
  assert.equal(p.id, FIX.contract);
  assert.equal(p.company_id, FIX.otherCompany, "the searched buyer must travel as company_id");
  assert.equal(p.date, "2026-09-05");
  assert.equal(p.pl_required, "NO", "the explicit 'Không cần PL' travels as NO");
  assert.ok(!("customerId" in p), "an untouched counterparty must not be sent at all");
  assert.equal(triggers.slice(before).filter((tr) => tr.event === "customer_getfly_import").length, 0);

  // "Chưa chọn" is also an explicit answer and must travel as blank, not vanish.
  before = triggers.length;
  await clickTestId("contract-pl-choice-unknown");
  await click("LƯU TỔNG QUAN", "button");
  await tick(60);
  saves = triggers.slice(before).filter((tr) => tr.event === "contract_save");
  assert.equal(saves.length, 1);
  assert.equal(saves[0].value.payload.pl_required, "", "blank PL must travel as blank (unknown), never dropped");

  // re-picking the counterparty is what makes customerId travel
  before = triggers.length;
  await clickTestId("contract-customer-picker-toggle");
  await type(byTestId("contract-customer-picker-search"), "Minh Đức");
  await clickTestId("contract-customer-picker-option-CUST-MINHDUC");
  await click("LƯU TỔNG QUAN", "button");
  await tick(60);
  saves = triggers.slice(before).filter((tr) => tr.event === "contract_save");
  assert.equal(saves.length, 1, "one click = one save event, no double-send");
  assert.equal(saves[saves.length - 1].value.payload.customerId, "CUST-MINHDUC");
  ok("one typed save per click; explicit answers travel, untouched fields don't");
}

// ---------------------------------------------------------------------------
console.log("STEP 4 — the edited values come back from the backend read");
{
  await bootOnContract(FIX.contractEdited);
  const t = mainText();
  assert.equal(attr("contract-buyer-picker", "data-selected"), FIX.buyerCompany);
  assert.equal(text(byTestId("contract-buyer-picker-value")), FIX.buyerLegalName);
  assert.equal(text(byTestId("contract-customer-picker-value")), "Minh Đức JSC");
  assert.equal($('input[placeholder="2026-09-05"]')[0].value, "2026-09-05");
  assert.ok(t.includes("đang lưu: Có PL"), "the stored PL answer must be shown");
  assert.equal(attr("contract-pl-choice-YES", "aria-pressed"), "true");
  assert.equal(attr("contract-pl-choice-NO", "aria-pressed"), "false");
  ok("buyer, counterparty, date and PL all round-trip into the rendered page");
}

// ---------------------------------------------------------------------------
console.log("STEP 5 — a PL decision made AFTER create stays editable and persists");
{
  await bootOnContract(FIX.contractPlNo);
  const t = mainText();
  assert.ok(t.includes("đang lưu: Không cần PL"), "the flipped PL answer must read back");
  assert.equal(attr("contract-pl-choice-NO", "aria-pressed"), "true");
  // and the fields the operator did not touch are still there (no clobbering)
  assert.equal(attr("contract-buyer-picker", "data-selected"), FIX.buyerCompany);
  assert.equal($('input[placeholder="2026-09-05"]')[0].value, "2026-09-05");
  ok("PL flip survives the rerun without clobbering the other answers");
}

// ---------------------------------------------------------------------------
console.log("STEP 6 — /hop-dong/moi: search-first create with the operator's PL answer");
{
  invoke(FIX.contractUnset);
  await tick(120);
  await click("Hợp đồng", "a", $("aside")[0]);
  await click("Tạo hợp đồng", "a", $("main")[0]);
  await tick(80);
  const t = mainText();
  assert.ok(t.includes("Tạo hợp đồng mới"), "create page did not render");
  assert.ok(byTestId("contract-customer-picker"), "a plain hidden customer field is not acceptable");
  assert.ok(byTestId("contract-pl-choice"), "PL choice missing on create");
  assert.ok(byTestId("contract-getfly-toggle"), "GetFly entry point missing on create");
  assert.equal(attr("contract-pl-choice-unknown", "aria-pressed"), "true", "create must not pre-answer PL");

  await type($('input[placeholder="VD: HDMB-0310"]')[0], "HDMB-0310");
  await clickTestId("contract-customer-picker-toggle");
  await type(byTestId("contract-customer-picker-search"), "An Phát");
  await clickTestId("contract-customer-picker-option-CUST-ANPHAT");
  assert.equal(attr("contract-customer-picker", "data-selected"), "CUST-ANPHAT");
  await clickTestId("contract-pl-choice-YES");

  const before = triggers.length;
  await click("TẠO HỢP ĐỒNG", "button");
  await tick(60);
  const creates = triggers.slice(before).filter((tr) => tr.event === "contract_create");
  assert.equal(creates.length, 1, "exactly one contract_create");
  const payload = creates[0].value.payload;
  assert.equal(payload.id, "HDMB-0310");
  assert.equal(payload.customerId, "CUST-ANPHAT");
  assert.equal(payload.pl_required, "YES");
  assert.equal(payload.date, "", "an empty date stays empty — no invented signing date");
  assert.equal(triggers.slice(before).filter((tr) => tr.event === "contract_save").length, 0);
  ok("create form searches the counterparty and sends the explicit PL answer");
}

// ---------------------------------------------------------------------------
console.log("STEP 7 — GetFly paste: the backend decides, the page shows its words");
{
  invoke(FIX.contractUnset);
  await tick(120);
  await click("Hợp đồng", "a", $("aside")[0]);
  await click("Tạo hợp đồng", "a", $("main")[0]);
  await clickTestId("contract-getfly-toggle");
  assert.ok(byTestId("contract-getfly-panel"), "paste panel did not open");

  await type(byTestId("contract-getfly-text"), FIX.getflyText);
  const before = triggers.length;
  await click("Nhập khách hàng từ GetFly", "button");
  await tick(60);
  const imports = triggers.slice(before).filter((tr) => tr.event === "customer_getfly_import");
  assert.equal(imports.length, 1, "exactly one GetFly import per click");
  assert.equal(imports[0].value.payload.text, FIX.getflyText.trim(), "the pasted block travels as the operator copied it");
  const requestId = imports[0].value.payload.requestId;
  assert.ok(requestId, "the paste must carry a requestId so the outcome can be matched");

  deliver(withRequestId(FIX.getflyOk, requestId));
  await tick(120);
  const outcome = text(byTestId("contract-getfly-outcome"));
  assert.ok(outcome.includes("Đã thêm 1 khách hàng"), `backend's own tally must be shown: ${outcome}`);
  assert.ok(outcome.includes("Bỏ qua (thiếu mã KH hoặc tên KH): Khách thiếu mã"), "skipped lines are reported, not invented");
  await clickTestId(`contract-getfly-use-${FIX.newCustomerId}`);
  assert.equal(attr("contract-customer-picker", "data-selected"), FIX.newCustomerId);
  // the new customer is really in the read-back address book, not only in local state
  await clickTestId("contract-customer-picker-toggle");
  await type(byTestId("contract-customer-picker-search"), "New");
  assert.ok(byTestId(`contract-customer-picker-option-${FIX.newCustomerId}`), "imported customer must come from the backend read");
  ok("paste → one import → backend outcome → the imported customer is selectable");
}

// ---------------------------------------------------------------------------
console.log("STEP 8 — a refused paste keeps the backend's message and adds nothing");
{
  invoke(FIX.contractUnset);
  await tick(120);
  await click("Hợp đồng", "a", $("aside")[0]);
  await click("Tạo hợp đồng", "a", $("main")[0]);
  await clickTestId("contract-getfly-toggle");
  await type(byTestId("contract-getfly-text"), FIX.getflyBadText);
  const before = triggers.length;
  await click("Nhập khách hàng từ GetFly", "button");
  await tick(60);
  const imports = triggers.slice(before).filter((tr) => tr.event === "customer_getfly_import");
  assert.equal(imports.length, 1);
  const badId = imports[0].value.payload.requestId;

  deliver(withRequestId(FIX.getflyRefused, badId));
  await tick(120);
  const outcome = text(byTestId("contract-getfly-outcome"));
  assert.ok(outcome.includes("Không nhận ra cột"), `the refusal text is the backend's: ${outcome}`);
  assert.ok(outcome.includes("Tên KH"), "the missing GetFly column must be named");
  assert.equal(byTestId("contract-getfly-use-CUST-HNNEW"), null, "nothing may be offered for import that failed");
  await clickTestId("contract-customer-picker-toggle");
  await type(byTestId("contract-customer-picker-search"), "thiếu mã");
  assert.ok(byTestId("contract-customer-picker-nomatch"), "a skipped line must not have become a customer");
  ok("fail-closed paste: verbatim refusal, no invented customer");
}

console.log(`\nCONTRACT CORE-EDIT DOM acceptance PASSED — ${passed} checks`);
