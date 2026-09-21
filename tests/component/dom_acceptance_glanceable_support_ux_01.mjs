// ============================================================================
// LOGI_SHIPMENT_GLANCEABLE_SUPPORT_UX_01 (issue #86) — DOM acceptance.
//
// Runs the REAL production bundle (component/dist/logi-shell.js) in jsdom over
// the REAL-backend fixture produced by
// scripts/gen_shipment_execution_profile_fixture.py (isolated mongomock staging
// driven through the bounded dispatcher → canonical writers → audit → fresh
// read). No production data is touched; the only states a step invents are
// explicitly labelled DISPLAY PROBES — clones of a real row with a field
// blanked, used solely to prove a display rule on data the fixture does not
// happen to contain.
//
// Verified contract:
//
//  1. A. the execution-profile editor collapses ONLY on the authoritative
//     backend success — never because dispatch returned true, never while
//     pending;
//  2. B. a backend REFUSAL leaves the editor OPEN on the stored data, with the
//     backend's own wording visible;
//  3. C. a NOOP ("Không có thay đổi") may collapse, and the compact persisted
//     summary remains visible as the evidence;
//  4. D. the lot-detail header exposes Incoterm + mode + load model + ETD + ETA
//     at the top, and the verbose profile prose is no longer doubled (exactly
//     one execution-profile summary on the page, inside the profile section);
//  5. a CONFIG_CHECK lot still flags itself in the header — no red warning is
//     hidden by the simplification;
//  6. E. every desktop list row carries the same five facts;
//  7. G/H. ETD = first NON-EMPTY ETD by leg sequence, ETA = last NON-EMPTY ETA
//     by leg sequence — the semantics of
//     core.shipment_operations.compatibility_facts(), never a "main leg" guess;
//  8. I. an unknown fact renders as an explicit amber "—" chip (Incoterm —,
//     Phương thức —, Loại hàng —, ETD —, ETA —) so an incomplete lot never
//     looks complete;
//  9. F. the mobile card carries the same facts, wrapping inside the card: no
//     forced horizontal scroll anywhere in the mobile list;
// 10. J/L. s.nextRoute is still the ONE primary action per row and the
//     responsibility wording ("Sale", "Cập nhật bởi") is unchanged;
// 11. K. five missing quick facts change NOTHING about missingDocs, nextAction,
//     status or the task list — they are a display gap only;
// 12. M/N. rendering the list issues no event at all, and the profile is not
//     rebuilt or re-read anywhere in the browser.
//
// Run: node tests/component/dom_acceptance_glanceable_support_ux_01.mjs
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
const LEGACY_LOT = FIX.legacyLot;   // LO-0306 — ROAD + DAP, profile incomplete
const ROAD_LOT = FIX.roadLot;       // LO-0308 — ROAD, FCA/LTL saved in roadLtlSaved
const SEA_LOT = FIX.seaLot;         // LO-0307 — SEA + CIF + FCL saved in seaFclSaved

const clone = (value) => JSON.parse(JSON.stringify(value));
const rowOf = (state, id) => state.shipments.find((s) => s.id === id);

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
const $all = (sel, root = window.document) => [...root.querySelectorAll(sel)];
const text = (el) => (el.textContent || "").replace(/\s+/g, " ").trim();
const mainText = () => text($all("main")[0] ?? window.document.body);
const bodyText = () => text(window.document.body);
const byTestId = (id, root = window.document) => root.querySelector(`[data-testid="${id}"]`);

let passed = 0;
const ok = (name) => { passed += 1; console.log(`  ✓ ${name}`); };

function findClickable(needle, sel = "a,button", root = window.document) {
  const els = $all(sel, root);
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
  await click("Lô Hàng", "a", $all("aside")[0]);
  await click(lot, "a", $all("main")[0]);
  await tick(80);
}

async function bootOnList(state) {
  invoke(state);
  await tick(120);
  await click("Lô Hàng", "a", $all("aside")[0]);
  await tick(80);
}

const mod = await import(path.join(ROOT, "component/dist/logi-shell.js"));
assert.equal(typeof mod.default, "function");
mountRef.current = mod.default;

/** The strip of ONE rendered element (list row or detail header). */
const stripOf = (root) => byTestId("shipment-quick-facts", root);

/**
 * `ETD …` / `ETA …` of one strip, read from the two labelled parts. The arrow
 * between them is flex-spaced, so it is deliberately not part of any assertion.
 */
function scheduleOf(root) {
  const wrap = byTestId("quick-fact-schedule", root);
  assert.ok(wrap, "the ETD → ETA pair is missing");
  return {
    etd: text(byTestId("quick-fact-etd", wrap)),
    eta: text(byTestId("quick-fact-eta", wrap)),
    etdKnown: wrap.getAttribute("data-etd-known"),
    etaKnown: wrap.getAttribute("data-eta-known"),
    title: wrap.getAttribute("title") || "",
  };
}
const chipText = (root, testId) => {
  const chip = byTestId(testId, root);
  assert.ok(chip, `${testId} missing from the rendered quick facts`);
  return { value: text(chip), known: chip.getAttribute("data-known") === "true" };
};

/**
 * The quick facts as the CANONICAL backend semantics say they are, recomputed
 * here from the fixture row: legs ordered by `sequence`, first non-empty ETD
 * forward, last non-empty ETA backward (core.shipment_operations
 * .compatibility_facts). The DOM must match this — not a "main leg" guess.
 */
function expectedFacts(row) {
  const ordered = [...(row.transportLegs ?? [])].sort((a, b) => (a.sequence || 0) - (b.sequence || 0));
  const ddmm = (raw) => {
    const iso = /^(\d{4})-(\d{2})-(\d{2})/.exec((raw || "").trim());
    if (iso) return `${iso[3]}/${iso[2]}`;
    const dmy = /^(\d{1,2})\/(\d{1,2})\/(\d{4})$/.exec((raw || "").trim());
    if (dmy) return `${dmy[1].padStart(2, "0")}/${dmy[2].padStart(2, "0")}`;
    return (raw || "").trim();
  };
  const profile = row.executionProfile ?? {};
  return {
    incoterm: (profile.incoterm || "").trim(),
    modeLabel: (profile.modeLabel || "").trim(),
    loadLabel: (profile.loadModelLabel || "").trim().split("—")[0].trim() || (profile.loadModelLabel || "").trim(),
    etd: ddmm(ordered.map((l) => l.etd).find(Boolean) || ""),
    eta: ddmm([...ordered].reverse().map((l) => l.eta).find(Boolean) || ""),
  };
}

/** Fill the real editor with a COMPLETE profile and send it once. */
async function saveCompleteProfile({ mode, incoterm, place, loadModel }) {
  await clickTestId("shipment-execution-profile-toggle");
  assert.ok(byTestId("profile-mode"), "the editor must be open before saving");
  await setValue(byTestId("profile-mode"), mode);
  await setValue(byTestId("profile-incoterm"), incoterm);
  await setValue(byTestId("profile-named-place"), place, "HTMLInputElement");
  await setValue(byTestId("profile-load-model"), loadModel);
  await clickTestId("profile-scope-confirmed");
  await clickTestId("profile-insurance-UNKNOWN");
  const before = triggers.length;
  await clickTestId("shipment-execution-profile-save");
  await tick(80);
  const sends = triggers.slice(before).filter((tr) => tr.event === "shipment_profile_save");
  assert.equal(sends.length, 1, "exactly one shipment_profile_save per click");
  return sends[0].value.payload.requestId;
}

const outcome = (requestId, { noop = false, ok: accepted = true, error = "" } = {}) => ({
  event: "shipment_profile_save",
  shipmentId: ROAD_LOT,
  ok: accepted,
  noop,
  error,
  requestId,
  readback: null,
});

// ---------------------------------------------------------------------------
console.log("STEP 1 — A: the editor collapses only on the AUTHORITATIVE success");
{
  await bootOnLot(FIX.before, ROAD_LOT);
  const requestId = await saveCompleteProfile({
    mode: "ROAD", incoterm: "FCA", place: "Pingxiang Warehouse", loadModel: "LTL",
  });

  // TRANSPORT_ACCEPTED != SAVED: the click was accepted, no outcome exists yet.
  assert.ok(byTestId("profile-mode"), "PENDING must keep the editor OPEN");
  assert.ok(byTestId("execution-profile-pending"), "the waiting state must be visible");

  // The fresh view-model now carries BOTH the correlated success AND the real
  // backend readback (roadLtlSaved = the row as stored by this very save).
  const success = clone(FIX.roadLtlSaved);
  success.lastWrites = [outcome(requestId)];
  deliver(success);
  await tick(140);

  // NOTE: a DOM element is never handed to assert.equal — Node formats the
  // failure by deep-inspecting the live jsdom subtree, which is both slow and
  // misleading. Booleans keep the message about the BEHAVIOUR.
  assert.equal(byTestId("profile-mode") === null, true,
    "an authoritatively saved profile must no longer occupy the screen");
  assert.ok(byTestId("shipment-execution-profile"), "the profile section itself stays available");
  assert.equal(byTestId("shipment-execution-profile-toggle").textContent.trim(), "Sửa hồ sơ lô",
    "the disclosure must return to its closed label");
  assert.ok(bodyText().includes("Đã lưu hồ sơ lô"), "the success confirmation is the backend's, not the click's");
  ok("collapse happens on lastWrites+readback success, never on dispatch acceptance");
}

console.log("STEP 2 — the collapsed summary keeps showing the stored profile");
{
  const summary = byTestId("execution-profile-summary");
  assert.ok(summary, "the compact persisted summary must remain visible after collapsing");
  const t = text(summary);
  assert.ok(t.includes("FCA"), `the stored Incoterms term must be readable: ${t}`);
  assert.equal(summary.getAttribute("data-state"), "PROFILE_READY",
    "the backend's own state is what the collapsed strip reports");
  assert.ok(byTestId("execution-profile-stages"), "the stage evidence remains on the collapsed card");
  ok("closed editor, persisted summary + stage chips still visible");
}

console.log("STEP 3 — B: a backend refusal keeps the editor OPEN for repair");
{
  await bootOnLot(FIX.before, ROAD_LOT);
  const requestId = await saveCompleteProfile({
    mode: "SEA", incoterm: "CIF", place: "Hai Phong Port", loadModel: "FCL",
  });
  const refusal = clone(FIX.before);
  refusal.lastWrites = [outcome(requestId, {
    ok: false,
    error: "CIF chỉ áp dụng cho chặng chính đường biển / đường thủy nội địa.",
  })];
  deliver(refusal);
  await tick(140);
  assert.ok(byTestId("profile-mode"), "a refusal must NEVER collapse the editor — the operator repairs it");
  assert.ok(bodyText().includes("CIF chỉ áp dụng cho chặng chính đường biển / đường thủy nội địa."),
    "the backend's own refusal wording is shown verbatim");
  assert.equal(byTestId("execution-profile-pending"), null, "the pending state must clear on the outcome");
  assert.ok(text(byTestId("execution-profile-summary")).includes("DAP"),
    "the stored profile stays what the backend has — no optimistic replacement");
  ok("refusal: editor open, draft intact, stored data unchanged");
}

console.log("STEP 4 — C: a NOOP collapses and the persisted summary remains");
{
  await bootOnLot(FIX.before, ROAD_LOT);
  const requestId = await saveCompleteProfile({
    mode: "ROAD", incoterm: "DAP", place: "Đồng Bằng warehouse", loadModel: "LTL",
  });
  const noopState = clone(FIX.before);   // rows unchanged: nothing was written
  noopState.lastWrites = [outcome(requestId, { noop: true })];
  deliver(noopState);
  await tick(140);
  assert.ok(bodyText().includes("Không có thay đổi"), "the noop must be stated truthfully");
  assert.equal(byTestId("profile-mode") === null, true, "a noop may collapse — there is nothing to repair");
  const summary = byTestId("execution-profile-summary");
  assert.ok(summary, "the persisted compact summary must remain after a noop collapse");
  assert.ok(text(summary).includes("DAP"), "the summary still reports the stored facts");
  ok("noop: truthful wording, collapse allowed, summary retained");
}

// ---------------------------------------------------------------------------
console.log("STEP 5 — D: the detail header leads with the five recognition facts");
{
  await bootOnLot(FIX.seaFclSaved, SEA_LOT);
  const row = rowOf(FIX.seaFclSaved, SEA_LOT);
  const expected = expectedFacts(row);
  const strip = stripOf($all("main")[0]);
  assert.ok(strip, "the quick-facts strip is missing from the lot detail header");
  assert.equal(chipText(strip, "quick-fact-incoterm").value, expected.incoterm, "Incoterm must be the profile's own code");
  assert.equal(chipText(strip, "quick-fact-mode").value, expected.modeLabel, "mode must be the profile's own label");
  assert.equal(chipText(strip, "quick-fact-load").value, expected.loadLabel, "load model must be the profile's own label");
  const schedule = scheduleOf(strip);
  assert.equal(schedule.etd, `ETD ${expected.etd}`, "ETD must be the first non-empty leg ETD");
  assert.equal(schedule.eta, `ETA ${expected.eta}`, "ETA must be the last non-empty leg ETA");
  assert.equal(strip.getAttribute("data-gap-count"), "0", "a complete profile shows no gap chip");
  // Hierarchy: recognition at the top, configuration prose in ONE place only.
  assert.equal($all('[data-testid="execution-profile-summary"]').length, 1,
    "the verbose profile summary must not be doubled at equal weight");
  assert.equal(byTestId("execution-profile-state-indicator") === null, true,
    "a PROFILE_READY lot needs no header warning");
  ok("header quick facts = Incoterm · mode · load model · ETD → ETA, no doubled summary");
}

console.log("STEP 6 — a CONFIG_CHECK lot still announces itself in the header");
{
  await bootOnLot(FIX.configCheck, LEGACY_LOT);
  const indicator = byTestId("execution-profile-state-indicator");
  assert.ok(indicator, "the header must keep a compact profile-state indicator");
  assert.equal(indicator.getAttribute("data-state"), "CONFIG_CHECK");
  assert.ok(text(indicator).includes("CẤU HÌNH CẦN KIỂM TRA"), "the red state is not softened");
  assert.ok(byTestId("execution-profile-config-check"),
    "the full CONFIG_CHECK explanation must remain in the profile section");
  ok("no real red warning is hidden by the noise reduction");
}

// ---------------------------------------------------------------------------
console.log("STEP 7 — E: every desktop list row carries the quick facts");
{
  await bootOnList(FIX.seaFclSaved);
  const rows = $all('table.tbl tbody tr[data-testid="shipment-row"]');
  assert.ok(rows.length > 0, "the desktop list must still render table rows");
  assert.equal(rows.length, FIX.seaFclSaved.shipments.length, "one row per lot");
  for (const row of rows) {
    const strip = stripOf(row);
    assert.ok(strip, `row ${row.getAttribute("data-shipment-id")} has no quick facts`);
    const source = rowOf(FIX.seaFclSaved, row.getAttribute("data-shipment-id"));
    const expected = expectedFacts(source);
    assert.equal(chipText(strip, "quick-fact-incoterm").value, expected.incoterm || "Incoterm —");
    assert.equal(chipText(strip, "quick-fact-mode").value, expected.modeLabel || "Phương thức —");
    const schedule = scheduleOf(strip);
    assert.equal(schedule.etd, `ETD ${expected.etd || "—"}`);
    assert.equal(schedule.eta, `ETA ${expected.eta || "—"}`);
  }
  // The Owner's exact example row: a Sea FCL lot readable without opening it.
  const seaRow = rows.find((r) => r.getAttribute("data-shipment-id") === SEA_LOT);
  const seaText = text(stripOf(seaRow));
  assert.ok(seaText.includes("CIF") && seaText.includes("Đường biển") && seaText.includes("FCL"),
    `the CIF / sea / FCL lot must be recognizable from the list alone: ${seaText}`);
  assert.ok(seaText.includes("ETD 05/09") && seaText.includes("ETA 12/09"),
    `ETD/ETA must be readable from the list alone: ${seaText}`);
  // The identity region keeps status + responsibility + the ONE action.
  assert.ok(text(seaRow).includes(rowOf(FIX.seaFclSaved, SEA_LOT).status), "status badge per row");
  assert.equal(rows.filter((r) => $all("a,button", r).filter((el) => text(el).includes("XỬ LÝ")).length !== 1).length, 0,
    "every row keeps exactly one primary-action control");
  ok(`all ${rows.length} desktop rows expose the five facts + status + one action`);
}

console.log("STEP 8 — J: XỬ LÝ still follows s.nextRoute, nothing else was added");
{
  for (const row of $all('table.tbl tbody tr[data-testid="shipment-row"]')) {
    const source = rowOf(FIX.seaFclSaved, row.getAttribute("data-shipment-id"));
    const handles = $all("a", row).filter((a) => text(a).includes("XỬ LÝ"));
    assert.equal(handles.length, 1, "exactly one primary handle per row");
    assert.equal(handles[0].getAttribute("href"), source.nextRoute,
      "the primary handle must stay the backend's composed route");
    assert.ok(text(row).includes(source.nextAction), "the row still shows s.nextAction as the ONE next action");
  }
  const countLine = mainText();
  assert.ok(!countLine.includes("Support phụ trách"), "no invented assignment may appear");
  assert.ok(countLine.includes("Cập nhật bởi"), "updated_by keeps its truthful label");
  ok("one primary action per row + truthful responsibility wording preserved");
}

console.log("STEP 9 — G/H: ETD = first non-empty leg ETD, ETA = last non-empty leg ETA");
{
  // Real fixture row LO-0299: leg 1 has ETD+ETA, leg 2 has an ETD and NO ETA.
  await bootOnList(FIX.before);
  const real = rowOf(FIX.before, "LO-0299");
  assert.equal(real.transportLegs.length, 2, "the fixture row must have two legs");
  assert.ok(real.transportLegs[1].eta === "", "precondition: the later leg states no ETA");
  const realStrip = stripOf($all('table.tbl tbody tr[data-shipment-id="LO-0299"]')[0]);
  assert.equal(scheduleOf(realStrip).etd, "ETD 05/09",
    "ETD must come from the FIRST leg that states one");
  assert.equal(scheduleOf(realStrip).eta, "ETA 06/09",
    "ETA must be the LAST non-empty leg ETA, not the last leg's blank");

  // DISPLAY PROBE (synthetic, derived from the real fixture row): the first leg
  // states NO dates and the array order is NOT the sequence order — the strip
  // must still read by sequence, and must fall FORWARD to the next leg instead
  // of showing a blank or a main-leg guess.
  const probe = clone(FIX.before);
  const probeRow = rowOf(probe, "LO-0299");
  probeRow.transportLegs = [
    { id: "b", sequence: 3, mode: "Sea", etd: "2026-10-02", eta: "" },
    { id: "a", sequence: 1, mode: "Truck", etd: "", eta: "" },
    { id: "c", sequence: 2, mode: "Sea", etd: "2026-09-20", eta: "2026-09-25" },
  ];
  deliver(probe);
  await tick(120);
  const probeStrip = stripOf($all('table.tbl tbody tr[data-shipment-id="LO-0299"]')[0]);
  assert.equal(scheduleOf(probeStrip).etd, "ETD 20/09",
    "ETD must be the first NON-EMPTY ETD by sequence (leg 1 is blank → leg 2)");
  assert.equal(scheduleOf(probeStrip).eta, "ETA 25/09",
    "ETA must be the LAST non-empty ETA by sequence (leg 3 is blank → leg 2)");
  ok("ETD/ETA follow the ordered legs exactly as compatibility_facts() reads them");
}

console.log("STEP 10 — I: an unknown fact is an honest gap, never a silent hole");
{
  // DISPLAY PROBE: the same real lot with its execution profile absent and no
  // leg dates at all (a lot that genuinely knows nothing yet).
  const probe = clone(FIX.before);
  const probeRow = rowOf(probe, LEGACY_LOT);
  delete probeRow.executionProfile;
  probeRow.transportLegs = [];
  deliver(probe);
  await tick(120);
  const strip = stripOf($all(`table.tbl tbody tr[data-shipment-id="${LEGACY_LOT}"]`)[0]);
  assert.ok(strip, "the strip must render even when nothing is known");
  assert.equal(strip.getAttribute("data-gap-count"), "5", "all five facts are missing");
  for (const [testId, wording] of [
    ["quick-fact-incoterm", "Incoterm —"],
    ["quick-fact-mode", "Phương thức —"],
    ["quick-fact-load", "Loại hàng —"],
  ]) {
    const chip = chipText(strip, testId);
    assert.equal(chip.known, false, `${wording} must be marked unknown`);
    assert.equal(chip.value, wording, `the gap must be spelled out as "${wording}"`);
    assert.ok(byTestId(testId, strip).className.includes("border-amber-400"),
      "a gap uses the restrained amber treatment, never a filled-in look");
  }
  const schedule = scheduleOf(strip);
  assert.equal(schedule.etd, "ETD —", "an unknown ETD stays an em dash");
  assert.equal(schedule.eta, "ETA —", "an unknown ETA stays an em dash");
  assert.equal(schedule.etdKnown, "false");
  assert.equal(schedule.etaKnown, "false");
  assert.equal(schedule.title, "ETD — → ETA —", "the hover hint must stay honest too");
  assert.ok(!text(strip).includes("undefined") && !text(strip).includes("null"),
    "a missing fact never renders as raw nullish text");
  ok("five unknown facts render as five explicit gaps — the lot never looks complete");
}

console.log("STEP 11 — K: a quick-facts gap is NOT a new missing-info authority");
{
  // The very same lot, once complete-ish and once stripped of every profile
  // fact: missingDocs, nextAction, status and the task list must be identical,
  // because these gaps are display-only.
  const before = clone(FIX.before);
  const stripped = clone(FIX.before);
  const row = rowOf(stripped, LEGACY_LOT);
  const baseline = rowOf(before, LEGACY_LOT);
  const missingDocsBefore = [...baseline.missingDocs];
  const nextActionBefore = baseline.nextAction;
  const statusBefore = baseline.status;
  row.executionProfile = { ...row.executionProfile, incoterm: "", modeLabel: "", loadModelLabel: "", state: "PROFILE_INCOMPLETE" };
  row.transportLegs = [];
  assert.deepEqual(rowOf(stripped, LEGACY_LOT).missingDocs, missingDocsBefore,
    "the data itself must not gain a missing-doc entry from a display gap");
  await bootOnList(stripped);
  assert.ok(mainText().includes(`Tìm thấy ${before.shipments.length} lô`),
    "the list must not grow rows or warning banners because of a display gap");
  assert.ok(!mainText().includes("Việc cần làm mới"), "a quick-facts gap must not create a task");
  await bootOnLot(stripped, LEGACY_LOT);
  assert.ok(mainText().includes(`Thiếu ${missingDocsBefore.length} thông tin`) || missingDocsBefore.length === 0,
    "the header count stays the backend's own missingDocs count — never count+1");
  assert.ok(mainText().includes(nextActionBefore), "the composed primary action is untouched");
  assert.ok(mainText().includes(statusBefore), "the status is untouched");
  assert.ok(!mainText().includes("missingInfoCount"), "no internal counter may leak into the UI");
  ok("display gap only: missingDocs / nextAction / status / tasks unchanged");
}

console.log("STEP 12 — F: the mobile card carries the same facts, no forced overflow");
{
  await bootOnList(FIX.seaFclSaved);
  const cards = $all('[data-testid="shipment-mobile-card"]');
  assert.equal(cards.length, FIX.seaFclSaved.shipments.length, "one card per lot on phone width");
  for (const card of cards) {
    const strip = stripOf(card);
    assert.ok(strip, `mobile card ${card.getAttribute("data-shipment-id")} has no quick facts`);
    const source = rowOf(FIX.seaFclSaved, card.getAttribute("data-shipment-id"));
    const expected = expectedFacts(source);
    assert.equal(chipText(strip, "quick-fact-incoterm").value, expected.incoterm || "Incoterm —");
    const schedule = scheduleOf(strip);
    assert.equal(schedule.etd, `ETD ${expected.etd || "—"}`);
    assert.equal(schedule.eta, `ETA ${expected.eta || "—"}`);
    // The strip wraps inside the card instead of scrolling it sideways.
    assert.ok(strip.className.includes("flex-wrap"), "quick facts must wrap, not overflow");
    assert.equal($all("[class*='overflow-x-auto']", card).length, 0,
      "no element inside a mobile card may force horizontal scrolling");
    assert.equal($all("*", card).filter((el) => /min-w-\[\d{3,}px\]/.test(String(el.className || ""))).length, 0,
      "a mobile card may not carry a desktop table min-width");
  }
  const dense = stripOf(cards[0]);
  assert.ok(dense.className.includes("gap-1.5"), "chips stay scannable on a phone");
  ok(`all ${cards.length} mobile cards expose the facts without horizontal overflow`);
}

console.log("STEP 13 — M/N: the browser builds and reads nothing new for the strip");
{
  // Rendering the list must not emit any event: the strip consumes the row the
  // backend already projected once (the Python invariants — one profile build
  // per row, zero added reads — are guarded by tests/test_logi_scope_aware_
  // missing_info_01.py and tests/test_logi_shipment_primary_action_unify_01.py).
  const before = triggers.length;
  await bootOnList(FIX.seaFclSaved);
  await tick(120);
  assert.equal(triggers.length, before, "rendering the list must dispatch nothing");
  const html = window.document.body.innerHTML;
  for (const leak of ["build_execution_profile", "execution_profile", "compatibility_facts"]) {
    assert.ok(!html.includes(leak), `internal authority name leaked into the UI: ${leak}`);
  }
  ok("presentational only: zero events, zero new reader, no schema wording");
}

console.log(`\nDOM_ACCEPTANCE_GLANCEABLE_SUPPORT_UX_01=${passed} checks passed`);
