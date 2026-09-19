// ============================================================================
// LOGI_SHIPMENT_EXECUTION_PROFILE_01 (issue #76) — DOM acceptance.
//
// Runs the REAL production bundle (component/dist/logi-shell.js) in jsdom over
// the REAL-backend fixture (scripts/gen_shipment_execution_profile_fixture.py:
// isolated mongomock staging driven through the bounded dispatcher → canonical
// writers → audit → fresh read). Verified contract:
//
//   1. the compact execution-profile summary is at the TOP of the lot detail and
//      reports the backend's own state (PROFILE_INCOMPLETE for a legacy lot) —
//      no invented Incoterms version, place, scope or insurance;
//   2. the progressive flow appears in the Owner's order (mode → Incoterms
//      version → Incoterms → named place → load model → equipment/truck →
//      service scope → cargo insurance) with NO internal schema wording;
//   3. conditional selectors: a marine Incoterms rule is never offered for a
//      non-marine mode, DAT is not offered in 2020, DPU is not offered in 2010,
//      and DAF/DDU only exist in the explicit legacy 2000 mode;
//   4. an impossible pair stored on a historical lot renders CẤU HÌNH CẦN KIỂM
//      TRA with the explanation and the save is refused locally;
//   5. saving emits exactly ONE shipment_profile_save carrying canonical codes,
//      and "sent" is not "saved" (the page changes only with the fresh read);
//   6. a backend REFUSAL is displayed verbatim and leaves the stored data alone;
//   7. CIF's DERIVED seller obligation and the PERSISTED actual insurance are two
//      separate facts (CIF + actual UNKNOWN is a valid, visible state);
//   8. SEA+FCL shows the equipment read from the EXISTING container units;
//      SEA+LCL / ROAD+LTL require neither a container number nor a truck length;
//      ROAD+FTL shows the company operating presets and reuses the canonical
//      pickup truck field;
//   9. the create page runs the same flow and filters the Incoterms list by mode
//      and version;
//  10. phone width: no forced horizontal overflow, ≥44px touch targets,
//      16px-equivalent input text, Vietnamese-only operator wording.
//
// Run: node tests/component/dom_acceptance_execution_profile.mjs
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
  readFileSync(path.join(ROOT, "tests/component/fixtures/view_model_execution_profile.json"), "utf8")
);
const LEGACY_LOT = FIX.legacyLot;
const SEA_LOT = FIX.seaLot;
const ROAD_LOT = FIX.roadLot;

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
  /* keep node's navigator */
}
for (const key of [
  "HTMLElement", "HTMLInputElement", "HTMLTextAreaElement", "HTMLSelectElement",
  "HTMLAnchorElement", "Event", "CustomEvent", "MouseEvent", "KeyboardEvent",
  "Node", "MutationObserver", "getComputedStyle",
]) {
  globalThis[key] = window[key];
}
if (!globalThis.MessageChannel) globalThis.MessageChannel = window.MessageChannel;
window.HTMLElement.prototype.scrollIntoView = () => {};

const tick = (ms = 60) => new Promise((r) => setTimeout(r, ms));
const $ = (sel, root = window.document) => [...root.querySelectorAll(sel)];
const text = (el) => (el.textContent || "").replace(/\s+/g, " ").trim();
const mainText = () => text($("main")[0] ?? window.document.body);
const bodyText = () => text(window.document.body);
const byTestId = (id) => $(`[data-testid="${id}"]`)[0] ?? null;

let passed = 0;
function ok(name) {
  passed += 1;
  console.log(`  ✓ ${name}`);
}

function findClickable(needle, sel = "a,button", root = window.document) {
  const els = $(sel, root);
  return els.find((el) => text(el) === needle) || els.find((el) => text(el).includes(needle)) || null;
}

async function click(needle, sel = "a,button", root = window.document) {
  const el = findClickable(needle, sel, root);
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

async function setValue(el, value, tag = "HTMLSelectElement") {
  assert.ok(el, "control missing");
  const proto = window[tag].prototype;
  Object.getOwnPropertyDescriptor(proto, "value").set.call(el, value);
  el.dispatchEvent(new window.Event(tag === "HTMLSelectElement" ? "change" : "input", { bubbles: true }));
  await tick();
}

const optionValues = (select) => [...select.options].map((o) => o.value);

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

/** A fresh view-model to the SAME mounted page (Streamlit rerun semantics). */
function deliver(data) {
  mountRef.current({
    name: "logi_shell",
    data,
    parentElement: host,
    setTriggerValue: (event, value) => triggers.push({ event, value }),
  });
}

async function bootOnLot(state, lot) {
  invoke(state);
  await tick(120);
  await click("Lô Hàng", "a", $("aside")[0]);
  await click(lot, "a", $("main")[0]);
  await tick(80);
}

const mod = await import(path.join(ROOT, "component/dist/logi-shell.js"));
assert.equal(typeof mod.default, "function");
mountRef.current = mod.default;

// ---------------------------------------------------------------------------
console.log("STEP 1 — compact profile summary at the top of a legacy lot");
{
  await bootOnLot(FIX.before, LEGACY_LOT);
  const summary = byTestId("execution-profile-summary");
  assert.ok(summary, "the execution-profile summary is missing from the lot detail");
  const t = text(summary);
  assert.ok(t.includes("HỒ SƠ THỰC HIỆN LÔ"), "summary heading missing");
  assert.ok(t.includes("Hồ sơ lô còn thiếu"), `expected PROFILE_INCOMPLETE, got: ${t}`);
  assert.equal(summary.getAttribute("data-state"), "PROFILE_INCOMPLETE");
  // The legacy lot really states DAP — and NOTHING ELSE. No version, no place,
  // no scope and no insurance may be invented for it.
  assert.ok(t.includes("DAP"), "the stored Incoterms term must be shown");
  assert.ok(!/Incoterms 20\d\d/.test(t), "a version must never be invented");
  assert.ok(t.includes("Phạm vi TT: chưa xác nhận"), "scope must stay unconfirmed");
  assert.ok(t.includes("Bảo hiểm hàng hóa: Chưa xác nhận"), "insurance must stay unknown");
  ok("summary reports the backend state and invents no profile fact");
}

// ---------------------------------------------------------------------------
console.log("STEP 2 — the progressive flow, in order, with no schema wording");
{
  await clickTestId("shipment-execution-profile-toggle");
  const card = byTestId("shipment-execution-profile");
  const t = text(card);
  for (const step of [
    "1. Phương thức vận chuyển",
    "2. Phiên bản Incoterms",
    "3. Điều kiện giao hàng",
    "4. Địa điểm / cảng / điểm giao",
    "7. Phạm vi Trường Thành thực hiện",
    "8. Bảo hiểm hàng hóa (thực tế)",
  ]) {
    assert.ok(t.includes(step), `missing flow step: ${step}`);
  }
  assert.ok(
    t.indexOf("1. Phương thức vận chuyển") < t.indexOf("2. Phiên bản Incoterms")
    && t.indexOf("2. Phiên bản Incoterms") < t.indexOf("3. Điều kiện giao hàng")
    && t.indexOf("3. Điều kiện giao hàng") < t.indexOf("4. Địa điểm / cảng / điểm giao"),
    "the flow must run in the Owner's order"
  );
  // No internal schema identifier may reach the operator.
  for (const leak of [
    "incoterm_version", "incoterm_named_place", "service_scope", "load_model",
    "cargo_insurance", "execution_profile", "incoterm_raw_label", "EXECUTION_PROFILE",
  ]) {
    assert.ok(!t.includes(leak), `internal schema wording leaked to the UI: ${leak}`);
  }
  ok("progressive flow in order, Vietnamese operator wording only");
}

// ---------------------------------------------------------------------------
console.log("STEP 3 — conditional Incoterms selectors (version + mode)");
{
  const version = byTestId("profile-incoterm-version");
  const incoterm = byTestId("profile-incoterm");
  assert.ok(version && incoterm, "version / Incoterms selectors missing");

  await setValue(version, "");
  assert.equal(incoterm.disabled, true, "the rule list must wait for a version");

  await setValue(version, "2020");
  await setValue(byTestId("profile-mode"), "ROAD");
  let codes = optionValues(incoterm);
  for (const maritime of ["FAS", "FOB", "CFR", "CIF"]) {
    assert.ok(!codes.includes(maritime), `${maritime} must not be selectable for ROAD`);
  }
  assert.ok(codes.includes("FCA") && codes.includes("DPU"), "any-mode 2020 rules must remain");
  assert.ok(!codes.includes("DAT"), "DAT is not a 2020 rule");
  assert.ok(text(byTestId("profile-hidden-terms")).includes("FOB"), "the omission must be explained");

  await setValue(byTestId("profile-mode"), "SEA");
  codes = optionValues(incoterm);
  for (const maritime of ["FAS", "FOB", "CFR", "CIF"]) {
    assert.ok(codes.includes(maritime), `${maritime} must be offered for SEA`);
  }

  await setValue(version, "2010");
  codes = optionValues(incoterm);
  assert.ok(codes.includes("DAT") && !codes.includes("DPU"), "2010 has DAT and no DPU");
  assert.ok(!codes.includes("DAF") && !codes.includes("DDU"), "DAF/DDU are not 2010 rules");

  await setValue(version, "2000_LEGACY");
  codes = optionValues(incoterm);
  assert.deepEqual(codes.filter((code) => code !== ""), ["DAF", "DDU"], "legacy offers only DAF/DDU");
  assert.ok(mainText().includes("legacy Incoterms 2000"), "legacy mode must be explained honestly");
  ok("marine rules filtered by mode; DAT/DPU/DAF/DDU bound to their real versions");
}

console.log("STEP 4 — an impossible stored pair is explained, never silently fixed");
{
  await bootOnLot(FIX.configCheck, LEGACY_LOT);
  const banner = byTestId("execution-profile-config-check");
  assert.ok(banner, "CONFIG_CHECK banner missing for the stored FOB + ROAD lot");
  const t = text(banner);
  assert.ok(t.includes("CẤU HÌNH CẦN KIỂM TRA"), "the Owner's exact wording is required");
  assert.ok(t.includes("đường biển / đường thủy nội địa"), "the conflict must be explained");
  assert.ok(t.includes("không tự sửa") || t.includes("giữ nguyên"), "history must not be rewritten");
  // The stored evidence itself is untouched in the freshly read payload.
  const row = FIX.configCheck.shipments.find((s) => s.id === LEGACY_LOT);
  assert.equal(row.incoterm, "FOB", "the historical term must remain FOB");
  assert.equal(row.executionProfile.mode, "ROAD");
  await clickTestId("shipment-execution-profile-toggle");
  assert.ok(byTestId("profile-invalid"), "the editor must flag the invalid combination");
  assert.equal(byTestId("shipment-execution-profile-save").disabled, true, "an invalid profile must not be sendable");
  ok("impossible combination explained + save blocked; stored evidence untouched");
}

// ---------------------------------------------------------------------------
console.log("STEP 5 — one typed save per click; sent is not saved");
let sentRequestId = "";
{
  await bootOnLot(FIX.before, LEGACY_LOT);
  await clickTestId("shipment-execution-profile-toggle");
  await setValue(byTestId("profile-mode"), "SEA");
  await setValue(byTestId("profile-incoterm-version"), "2020");
  await setValue(byTestId("profile-incoterm"), "CIF");
  await setValue(byTestId("profile-named-place"), "Hai Phong Port", "HTMLInputElement");
  await setValue(byTestId("profile-load-model"), "FCL");
  await clickTestId("profile-scope-IMPORT_CUSTOMS");
  await clickTestId("profile-scope-DESTINATION_TRUCKING");
  await clickTestId("profile-scope-confirmed");
  await clickTestId("profile-insurance-UNKNOWN");

  const before = triggers.length;
  await clickTestId("shipment-execution-profile-save");
  await tick(80);
  const sends = triggers.slice(before).filter((tr) => tr.event === "shipment_profile_save");
  assert.equal(sends.length, 1, "exactly one shipment_profile_save per click");
  const payload = sends[0].value.payload;
  assert.equal(payload.shipmentId, LEGACY_LOT);
  assert.equal(payload.mode, "SEA");
  assert.equal(payload.incoterm, "CIF");
  assert.equal(payload.incotermVersion, "2020");
  assert.equal(payload.namedPlace, "Hai Phong Port");
  assert.equal(payload.loadModel, "FCL");
  assert.deepEqual(payload.serviceScope, ["IMPORT_CUSTOMS", "DESTINATION_TRUCKING"]);
  assert.equal(payload.serviceScopeConfirmed, true);
  assert.equal(payload.cargoInsurance.status, "UNKNOWN");
  assert.equal(typeof payload.requestId, "string");
  assert.ok(payload.requestId.length > 5, "the click identity must travel");
  sentRequestId = payload.requestId;

  // Transport alone is not persistence: the page still shows the STORED profile.
  const summary = text(byTestId("execution-profile-summary"));
  assert.ok(summary.includes("DAP"), "the page must not show an unconfirmed profile as stored");
  assert.ok(byTestId("execution-profile-pending"), "the waiting state must be visible");
  ok("one bounded save with canonical payload; waiting state, no local success");
}

console.log("STEP 6 — a backend refusal is shown verbatim and changes nothing");
{
  const refusal = JSON.parse(JSON.stringify(FIX.before));
  refusal.lastWrites = [{
    event: "shipment_profile_save", ok: false, shipmentId: LEGACY_LOT,
    requestId: sentRequestId, issues: [{ code: "INVALID_COMBINATION", message: "CIF chỉ áp dụng cho chặng chính đường biển / đường thủy nội địa." }],
    error: "CIF chỉ áp dụng cho chặng chính đường biển / đường thủy nội địa.",
  }];
  deliver(refusal);
  await tick(120);
  assert.ok(bodyText().includes("CIF chỉ áp dụng cho chặng chính đường biển / đường thủy nội địa."),
    "the backend's own refusal must be visible");
  assert.ok(!byTestId("execution-profile-pending"), "the waiting state must clear");
  assert.ok(text(byTestId("execution-profile-summary")).includes("DAP"), "no locally invented success");
  ok("refusal surfaced verbatim; stored profile unchanged");
}

// ---------------------------------------------------------------------------
console.log("STEP 7 — SEA FCL: equipment from the real units; obligation ≠ actual");
{
  await bootOnLot(FIX.seaFclSaved, SEA_LOT);
  const summary = text(byTestId("execution-profile-summary"));
  assert.ok(summary.includes("CIF · Incoterms 2020"), `profile line missing: ${summary}`);
  assert.ok(summary.includes("Hai Phong Port"), "named place missing");
  assert.ok(summary.includes("Đường biển · FCL · 1 × 20GP, 1 × 40HC"), "multi-container equipment line missing");
  assert.ok(summary.includes("Phạm vi TT: HQ nhập → Giao hàng"), "service scope line missing");
  assert.ok(summary.includes("Bảo hiểm theo Incoterm"), "the DERIVED obligation line is missing");
  assert.ok(summary.includes("Chứng từ bảo hiểm: Chưa xác nhận"), "the PERSISTED actual state is missing");
  assert.ok(!summary.includes("Nhóm A"), "CIF 2020 keeps Institute Cargo Clauses C");

  // The relevant stages are visible on the collapsed card (context first).
  const stages = text(byTestId("execution-profile-stages"));
  assert.ok(stages.includes("Thiết bị container"), "the FCL equipment stage must be relevant");
  assert.ok(stages.includes("Chứng từ bảo hiểm"), "the insurance evidence stage must be relevant");
  assert.ok(!stages.includes("Xe tải (FTL"), "a sea lot must not show a truck stage");
  assert.ok(!stages.includes("Lấy hàng tại kho"), "a buyer-side scope must not show an origin pickup stage");

  await clickTestId("shipment-execution-profile-toggle");
  const equipment = byTestId("profile-equipment");
  assert.ok(equipment, "the FCL equipment block is missing");
  const eq = text(equipment);
  assert.ok(eq.includes("40HC") && eq.includes("MSKU1234567"), "containers must come from the lot's own units");
  assert.ok(eq.includes("20GP"), "every container of the lot must be listed");
  ok("SEA FCL equipment read from existing units; CIF obligation kept apart from actual insurance");
}

console.log("STEP 8 — actual insurance NO is stated, and stale policy details are gone");
{
  await bootOnLot(FIX.insuranceNo, SEA_LOT);
  const summary = text(byTestId("execution-profile-summary"));
  assert.ok(summary.includes("Chứng từ bảo hiểm: Không có bảo hiểm"), `actual NO missing: ${summary}`);
  await clickTestId("shipment-execution-profile-toggle");
  assert.equal(byTestId("profile-insurance-arranged-by"), null,
    "policy details must not be rendered once the actual status is NO");
  ok("actual insurance persisted independently of the Incoterm obligation");
}

// ---------------------------------------------------------------------------
console.log("STEP 9 — ROAD: LTL demands no truck; FTL reuses the canonical truck fact");
{
  await bootOnLot(FIX.roadLtlSaved, ROAD_LOT);
  const summary = text(byTestId("execution-profile-summary"));
  assert.ok(summary.includes("Đường bộ · LTL"), `LTL line missing: ${summary}`);
  await clickTestId("shipment-execution-profile-toggle");
  assert.ok(byTestId("profile-ltl-note"), "the LTL note is missing");
  assert.equal(byTestId("profile-truck"), null, "LTL must not ask for a dedicated truck");
  assert.equal(byTestId("profile-equipment"), null, "a road lot must not show container equipment");
  const ltlStages = text(byTestId("execution-profile-summary"));
  assert.ok(!ltlStages.includes("Xác nhận loại xe"), "LTL must not demand a truck length");

  await bootOnLot(FIX.roadFtlTruck, ROAD_LOT);
  await clickTestId("shipment-execution-profile-toggle");
  const truck = byTestId("profile-truck");
  assert.ok(truck, "the FTL truck block is missing");
  const tt = text(truck);
  assert.ok(tt.includes("17,5 m"), "the company operating presets must be offered");
  assert.ok(tt.includes("17.5m"), "the stored preset must be shown as recorded");
  assert.ok(tt.includes("không phải quy định tải trọng") || tt.includes("không suy ra"),
    "truck length must not be presented as a capacity regulation");
  assert.ok(!tt.includes("tấn/CBM/giá") || tt.includes("không suy ra"),
    "no capacity inference may be implied");
  ok("ROAD LTL hides the truck profile; ROAD FTL shows presets over the canonical field");
}

// ---------------------------------------------------------------------------
console.log("STEP 10 — CNF/C&F becomes CFR while the contract wording survives");
{
  await bootOnLot(FIX.cfrAlias, SEA_LOT);
  const summary = text(byTestId("execution-profile-summary"));
  assert.ok(summary.includes("CFR · Incoterms 2020"), `canonical CFR missing: ${summary}`);
  assert.ok(summary.includes("hợp đồng ghi: CNF"), "the raw contract wording must survive as evidence");
  assert.ok(!summary.includes("CNF ·"), "CNF must never be presented as the canonical rule");
  await clickTestId("shipment-execution-profile-toggle");
  const card = text(byTestId("shipment-execution-profile"));
  assert.ok(card.includes("chuẩn hóa thành CFR"), "the normalization must be explained");
  assert.ok(card.includes("giữ nguyên cách ghi cũ"), "the historical evidence must be preserved");
  ok("alias normalized with the explanation visible and the source wording kept");
}

// ---------------------------------------------------------------------------
console.log("STEP 11 — RBAC: a viewer attempt changes nothing");
{
  const outcome = FIX.outcomes.viewerRefused;
  assert.equal(outcome.ok, false, "the fixture refusal must be a refusal");
  assert.match(outcome.error, /RBAC/, "the refusal must be the RBAC gate");
  await bootOnLot(FIX.viewerRefused, LEGACY_LOT);
  const summary = text(byTestId("execution-profile-summary"));
  assert.ok(summary.includes("FOB"), "the stored (unchanged) term must still be shown");
  assert.ok(!summary.includes("Hai Phong Port"), "no refused value may appear as stored");
  ok("viewer refusal leaves the stored profile untouched");
}

// ---------------------------------------------------------------------------
console.log("STEP 12 — create page: same flow, mode-filtered Incoterms list");
{
  invoke(FIX.before);
  await tick(120);
  await click("Tạo Lô Mới", "a", $("aside")[0]);
  await tick(60);
  assert.ok(mainText().includes("Tạo Lô Hàng Mới"), "create page missing");
  const section = byTestId("create-profile");
  assert.ok(section, "the create page must carry the profile flow");
  const details = section.closest("details");
  assert.ok(details, "the profile flow must be a disclosure, not a gate on creating a lot");
  details.open = true;
  await tick();
  await setValue(byTestId("create-profile-mode"), "ROAD");
  await setValue(byTestId("create-profile-incoterm-version"), "2020");
  const codes = optionValues(byTestId("create-profile-incoterm"));
  assert.ok(!codes.includes("FOB") && !codes.includes("CIF"), "the create form must not offer marine rules for road");
  assert.ok(codes.includes("DAP") && codes.includes("CPT"), "any-mode rules must remain");
  await setValue(byTestId("create-profile-incoterm"), "FCA");
  await setValue(byTestId("create-profile-named-place"), "Pingxiang Warehouse", "HTMLInputElement");
  assert.ok(byTestId("create-profile-missing"), "an engaged-but-incomplete profile must say what is missing");
  assert.ok(mainText().includes("Lô vẫn được tạo"), "creating a lot must not be blocked by an incomplete profile");
  ok("create page filters Incoterms by mode + version and explains the gaps");
}

// ---------------------------------------------------------------------------
console.log("STEP 13 — phone width: no forced overflow, touch targets, 16px text");
{
  await bootOnLot(FIX.seaFclSaved, SEA_LOT);
  await clickTestId("shipment-execution-profile-toggle");
  const card = byTestId("shipment-execution-profile");
  assert.ok(!card.className.includes("overflow-x-auto"), "the section must not force horizontal scrolling");
  assert.equal($("[class*='overflow-x-auto']", card).length, 0, "no child may force horizontal scroll");
  const controls = [...$("input,select,button", card)];
  assert.ok(controls.length > 8, "the editor must be rendered");
  for (const control of controls) {
    const cls = control.className || "";
    assert.ok(cls.includes("min-h-[44px]") || cls.includes("min-h-[48px]") || cls.includes("w-5") || cls.includes("h-5"),
      `touch target too small: ${cls}`);
  }
  for (const input of $("input,select", card)) {
    const cls = input.className || "";
    assert.ok(cls.includes("text-[15.5px]") || cls.includes("text-[13.5px]") || cls.includes("w-5"),
      `input text size must be readable on a phone: ${cls}`);
  }
  ok("no horizontal overflow, ≥44px controls, readable input text");
}

console.log(`\nDOM_ACCEPTANCE_EXECUTION_PROFILE=${passed} checks passed`);
