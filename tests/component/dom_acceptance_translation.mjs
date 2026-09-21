// ============================================================================
// LOGI_TRANSLATION_LOGISTICS_DEMO_PARITY_01 — DOM/navigation acceptance for
// /dich-thuat (demo-look parity over the REAL DeepL backend).
//
// Runs the REAL production bundle (component/dist/logi-shell.js) in jsdom with
// a REAL-backend fixture (scripts/gen_translation_fixture.py — isolated
// mongomock staging; the DeepL provider boundary is MOCKED, so no real paid
// API call happens anywhere in this suite) and verifies:
//   1. boot (no process/BidiComponent failure) + Trường Thành identity
//   2. sidebar "Dịch thuật" carries NO "Sắp có" marker anymore
//   3. page header + centered compact language direction row + ROUND swap
//      control (backend-derived language options, nothing invented)
//   4. two-column workspace: LEFT source panel / RIGHT result panel on
//      desktop structure, stacked safely on mobile
//   5. quick sample chips fill the SOURCE text ONLY — zero triggers, output
//      untouched, never a fabricated translation
//   6. ONE large full-width DỊCH NGAY; one intent = ONE typed
//      "translate_text" trigger; double click cannot pay twice
//   7. pending stays IN PLACE inside the right result panel (no layout jump)
//   8. fresh readback renders the provider text VERBATIM
//   9. provider error state is honest (no fabricated translation)
//  10. unconfigured deployment: honest "chưa được cấu hình" state, inert
//  11. RBAC-denied deployment: honest permission state, inert
//  12. copy hands over the VERBATIM text, and fails honestly
//  13. privacy disclosure names the external provider
//  14. "Từ điển nghiệp vụ nhanh" reference glossary renders and NEVER
//      triggers a translation
//  15. no provider key material in the DOM; no simulated-translation wording;
//      no local fake translation result anywhere
//  16. mobile: drawer routes here; touch targets; no horizontal-overflow
//      dependency
//
// Run: node tests/component/dom_acceptance_translation.mjs
// ============================================================================

import { readFileSync } from "node:fs";
import assert from "node:assert/strict";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const require = createRequire(path.join(ROOT, "component/package.json"));
const { JSDOM } = require("jsdom");
const VM = JSON.parse(
  readFileSync(path.join(ROOT, "tests/component/fixtures/view_model_translation.json"), "utf8")
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
  "Node", "MutationObserver", "getComputedStyle", "TextEncoder",
]) {
  globalThis[k] = window[k];
}
if (!globalThis.MessageChannel) globalThis.MessageChannel = window.MessageChannel;
window.HTMLElement.prototype.scrollIntoView = () => {};
window.URL.createObjectURL = () => "blob:mock-url";
window.URL.revokeObjectURL = () => {};

const tick = (ms = 60) => new Promise((r) => setTimeout(r, ms));

const $ = (sel, root = window.document) => [...root.querySelectorAll(sel)];
const text = (el) => (el.textContent || "").replace(/\s+/g, " ").trim();
const mainText = () => text($("main")[0] ?? window.document.body);
const bodyText = () => text(window.document.body);
const fullHtml = () => window.document.documentElement.innerHTML;

function findClickable(needle, sel = "a,button", root = window.document) {
  const els = $(sel, root);
  return els.find((el) => text(el) === needle) || els.find((el) => text(el).startsWith(needle)) || null;
}

async function click(needle, sel = "a,button", root = window.document) {
  const el = findClickable(needle, sel, root);
  assert.ok(el, `clickable "${needle}" not found`);
  el.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
  await tick();
  return el;
}

async function clickSelector(sel, root = window.document, index = 0) {
  const el = $(sel, root)[index];
  assert.ok(el, `selector "${sel}[${index}]" not found`);
  el.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
  await tick();
  return el;
}

async function typeTextarea(input, value) {
  const setter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, "value").set;
  setter.call(input, value);
  input.dispatchEvent(new window.Event("input", { bubbles: true }));
  await tick();
}

async function selectOption(select, value) {
  const setter = Object.getOwnPropertyDescriptor(window.HTMLSelectElement.prototype, "value").set;
  setter.call(select, value);
  select.dispatchEvent(new window.Event("change", { bubbles: true }));
  await tick();
}

let passed = 0;
function ok(name) {
  passed += 1;
  console.log(`  ✓ ${name}`);
}

const host = window.document.createElement("div");
window.document.body.appendChild(host);
const triggers = [];
const mountRef = { current: null };
function invoke(data) {
  return mountRef.current({
    name: "logi_shell",
    data,
    parentElement: host,
    setTriggerValue: (event, value) => triggers.push({ event, value }),
  });
}

let lastInvokeCleanup = null;
async function remount(data) {
  if (lastInvokeCleanup) lastInvokeCleanup();
  const cleanup = invoke(data);
  lastInvokeCleanup = cleanup;
  await tick(120);
  const aside = $("aside")[0];
  await click("Dịch thuật", "a", aside);
}

/** No fake-engine wording may ever appear on this page. */
function assertNoSimulatedWording(where) {
  const t = mainText();
  assert.ok(!t.includes("mô phỏng"), `${where}: simulated-translation wording leaked`);
  assert.ok(!t.includes("bản dịch mẫu"), `${where}: sample-translation wording leaked`);
}

const bundlePath = path.join(ROOT, "component/dist/logi-shell.js");

// A fresh intent, different from the fixture's last readback.
const NEW_SOURCE = "Khách hỏi: 什么时候可以提货？\nHS 9403.20.10 · PO-88213";
const NEW_TRANSLATED = "Customer asks: when can the goods be picked up?\nHS 9403.20.10 · PO-88213";

// ---------------------------------------------------------------------------
console.log("STEP 1 — boot production bundle + Trường Thành identity");
{
  const mod = await import(bundlePath);
  assert.equal(typeof mod.default, "function");
  mountRef.current = mod.default;
  lastInvokeCleanup = invoke(VM);
  await tick(120);
  const t = bodyText();
  assert.ok(!t.includes("process is not defined"), "process is not defined leaked");
  assert.ok(!t.includes("BidiComponent Error"), "BidiComponent Error rendered");
  assert.ok(t.includes("TRƯỜNG THÀNH"), "app did not render");
  ok("boot clean, shell rendered");
}

// ---------------------------------------------------------------------------
console.log("STEP 2 — sidebar honesty: no 'Sắp có' on Dịch thuật");
{
  const aside = $("aside")[0];
  const item = findClickable("Dịch thuật", "a", aside);
  assert.ok(item, "sidebar item missing");
  assert.ok(!text(item).includes("Sắp có"), "item still marked 'Sắp có'");
  ok("sidebar item is active, no deferred marker");
  await click("Dịch thuật", "a", aside);
}

// ---------------------------------------------------------------------------
console.log("STEP 3 — page header + centered direction row + ROUND swap");
{
  const t = mainText();
  assert.ok(!t.includes("Sắp có — chưa triển khai"), "route still renders the placeholder");
  // LOGI_INTERNAL_UX_SIMPLIFY_01 — donor-case header.
  assert.ok(t.includes("Dịch Thuật"), "page header missing");
  assert.ok(
    t.includes("Công cụ dịch nhanh các cụm từ nghiệp vụ"),
    "demo-parity subtitle missing"
  );
  assert.ok(!t.includes("Phú Anh"), "company branding regressed on this page");

  // Centered compact language direction row.
  const row = $('div[data-testid="language-direction"]')[0];
  assert.ok(row, "language direction row missing");
  assert.ok(row.className.includes("justify-center"), "direction row must be centered");
  assert.ok(row.className.includes("items-center"), "direction row must align controls");

  // Language options are the backend's own supported sets — nothing invented.
  const source = $('select[aria-label="Ngôn ngữ nguồn"]')[0];
  const target = $('select[aria-label="Ngôn ngữ đích"]')[0];
  assert.ok(source && target, "language selectors missing");
  const sourceCodes = [...source.options].map((o) => o.value);
  const targetCodes = [...target.options].map((o) => o.value);
  assert.deepEqual(sourceCodes, VM.translation.capability.sourceLanguages.map((o) => o.code));
  assert.deepEqual(targetCodes, VM.translation.capability.targetLanguages.map((o) => o.code));
  assert.ok(sourceCodes.includes("AUTO"), "auto-detect source option missing");
  assert.ok(!targetCodes.includes("AUTO"), "auto-detect must not be a target");
  assert.ok(!sourceCodes.includes("JA") && !targetCodes.includes("TH"),
    "unsupported language pair must not be offered");

  // Round swap control between the two selectors, dispatching nothing.
  const swap = $('button[aria-label="Đổi chiều dịch"]')[0];
  assert.ok(swap, "swap control missing");
  assert.ok(swap.className.includes("rounded-full"), "swap control must be round");
  const rowControls = [...row.children];
  assert.ok(rowControls.includes(swap), "swap must sit inside the direction row");
  assert.ok(
    rowControls.indexOf(swap) > rowControls.indexOf(source) &&
      rowControls.indexOf(swap) < rowControls.indexOf(target),
    "swap must sit between source and target"
  );
  const triggersBefore = triggers.length;
  await clickSelector('button[aria-label="Đổi chiều dịch"]');
  assert.equal(triggers.length, triggersBefore, "swap must not dispatch");
  // Swap follows the backend's own maps: AUTO/VI → VI/ZH-HANS.
  assert.equal($('select[aria-label="Ngôn ngữ nguồn"]')[0].value, "VI");
  assert.equal($('select[aria-label="Ngôn ngữ đích"]')[0].value, "ZH-HANS");
  await clickSelector('button[aria-label="Đổi chiều dịch"]');
  assert.equal($('select[aria-label="Ngôn ngữ nguồn"]')[0].value, "ZH");
  assert.equal($('select[aria-label="Ngôn ngữ đích"]')[0].value, "VI");

  // Privacy boundary is disclosed — this is not sold as a local translator.
  assert.ok(VM.translation.capability.externalProvider === true);
  assert.ok(t.includes("DeepL"), "provider not named");
  assert.ok(t.includes("KHÔNG phải bộ dịch chạy cục bộ"), "privacy disclosure missing");

  assertNoSimulatedWording("header/direction");
  ok("header + centered direction + round functional swap + privacy disclosure");
}

// ---------------------------------------------------------------------------
console.log("STEP 4 — two-column workspace: LEFT source / RIGHT result");
{
  const workspace = $('div[data-testid="translation-workspace"]')[0];
  assert.ok(workspace, "translation workspace grid missing");
  assert.ok(workspace.className.includes("grid-cols-1"), "workspace must stack on mobile");
  assert.ok(workspace.className.includes("lg:grid-cols-2"), "workspace must split on desktop");

  const sourcePanel = $('div[data-testid="source-panel"]')[0];
  const resultPanel = $('div[data-testid="result-panel"]')[0];
  assert.ok(sourcePanel && resultPanel, "source/result panels missing");
  assert.ok(
    sourcePanel.compareDocumentPosition(resultPanel) & window.Node.DOCUMENT_POSITION_FOLLOWING,
    "source panel must come before (left of) the result panel"
  );
  assert.ok(
    $('textarea[aria-label="Văn bản gốc"]', sourcePanel)[0],
    "source textarea must live in the LEFT panel"
  );
  assert.ok(
    resultPanel.contains($('textarea[aria-label="Bản dịch"]')[0]),
    "translated result must live in the RIGHT panel (no card below)"
  );
  const sourceArea = $('textarea[aria-label="Văn bản gốc"]')[0];
  assert.ok(sourceArea.className.includes("w-full"), "source textarea must be full width");
  assert.ok(sourceArea.className.includes("text-[16px]"),
    "16px text prevents mobile keyboard zoom");
  assert.ok($('button[aria-label="Xóa nội dung nhập"]', sourcePanel)[0],
    "clear action missing from the source panel");

  // The last authoritative readback is present; nothing is fabricated.
  const t = mainText();
  assert.ok(t.includes("Bản dịch"), "result panel heading missing");
  assert.ok(t.includes("SHP-2026-0147"), "last readback text missing");
  assert.ok(t.includes("ZH"), "detected source language missing");
  assertNoSimulatedWording("workspace");
  ok("LEFT source / RIGHT result desktop structure, mobile-safe");
}

// ---------------------------------------------------------------------------
console.log("STEP 5 — quick chips fill the SOURCE text only");
{
  // Default direction shows the Vietnamese logistics set.
  await selectOption($('select[aria-label="Ngôn ngữ nguồn"]')[0], "AUTO");
  let chips = $('button[data-testid="quick-chip"]');
  assert.ok(chips.length >= 5, `expected >= 5 quick chips, got ${chips.length}`);
  assert.ok($('div[role="group"][aria-label="Cụm từ nhanh"]')[0], "chip group missing");
  // LOGI_INTERNAL_UX_SIMPLIFY_01 — donor-shape pills show the first 24
  // characters; the full phrase stays on title/aria-label.
  const flagship = chips.find(
    (c) => c.getAttribute("aria-label") === "Vui lòng gửi hóa đơn và phiếu đóng gói trước khi xe lấy hàng."
  );
  assert.ok(flagship, "flagship logistics chip missing");
  assert.ok(flagship.className.includes("rounded-full"), "chip is not the donor pill shape");
  assert.ok(
    text(flagship).startsWith("Vui lòng gửi hóa đơn") && text(flagship).endsWith("…"),
    `chip is not donor-truncated: ${text(flagship)}`
  );

  const source = $('textarea[aria-label="Văn bản gốc"]')[0];
  const resultBefore = $('textarea[aria-label="Bản dịch"]')[0];
  assert.ok(resultBefore, "prior authoritative result missing before chip click");
  const resultValueBefore = resultBefore.value;

  const triggersBefore = triggers.length;
  // LOGI_INTERNAL_UX_SIMPLIFY_01 — the pill shows the donor truncation;
  // the FULL phrase (aria-label) is what fills the source.
  const firstValue = chips[0].getAttribute("aria-label");
  await clickSelector('button[data-testid="quick-chip"]', window.document, 0);
  assert.equal(source.value, firstValue, "chip must fill the SOURCE text");
  assert.equal($('textarea[aria-label="Bản dịch"]')[0].value, resultValueBefore,
    "chip click must NOT change the translated output");
  assert.equal(triggers.length, triggersBefore,
    "chip click must NOT dispatch any event (no paid call)");

  // A second chip simply replaces the source text — still source-only.
  const secondValue = chips[1].getAttribute("aria-label");
  await clickSelector('button[data-testid="quick-chip"]', window.document, 1);
  assert.equal(source.value, secondValue, "second chip must replace the source text");
  assert.equal(triggers.length, triggersBefore, "second chip dispatched an event");

  // A Chinese source direction offers the equivalent Chinese set — still
  // source-only, still zero triggers.
  await selectOption($('select[aria-label="Ngôn ngữ nguồn"]')[0], "ZH");
  chips = $('button[data-testid="quick-chip"]');
  assert.ok(
    chips.some((c) => (c.getAttribute("aria-label") || "").includes("请在车辆提货前发送发票和装箱单")),
    "equivalent Chinese chip set missing for a ZH source"
  );
  await clickSelector('button[data-testid="quick-chip"]', window.document, 0);
  assert.equal(source.value, chips[0].getAttribute("aria-label"), "Chinese chip must fill the SOURCE text");
  assert.equal(triggers.length, triggersBefore, "Chinese chip dispatched an event");
  assert.equal($('textarea[aria-label="Bản dịch"]')[0].value, resultValueBefore,
    "Chinese chip must NOT change the translated output");
  await selectOption($('select[aria-label="Ngôn ngữ nguồn"]')[0], "AUTO");

  assertNoSimulatedWording("chips");
  ok("VI + ZH chip sets render; clicks fill SOURCE only, zero triggers, output untouched");
}

// ---------------------------------------------------------------------------
console.log("STEP 6 — DỊCH NGAY: ONE trigger; double click cannot pay twice");
{
  const action = $('button[data-testid="translate-action"]')[0];
  assert.ok(action, "DỊCH NGAY action missing");
  assert.ok(action.className.includes("w-full"), "DỊCH NGAY must be full width");
  assert.ok(action.className.includes("min-h-[48px]"), "DỊCH NGAY below touch target");
  assert.ok(text(action).includes("DỊCH NGAY"), "action must read DỊCH NGAY");

  const source = $('textarea[aria-label="Văn bản gốc"]')[0];
  await typeTextarea(source, NEW_SOURCE);
  await selectOption($('select[aria-label="Ngôn ngữ nguồn"]')[0], "ZH");
  await selectOption($('select[aria-label="Ngôn ngữ đích"]')[0], "EN");

  const before = triggers.length;
  await click("DỊCH NGAY", "button");
  // Enthusiastic thumb: a second click while the first intent is in flight.
  const translateBtn = $('button[data-testid="translate-action"]')[0];
  assert.ok(text(translateBtn).includes("ĐANG DỊCH"), "pending label missing on the action");
  assert.ok(translateBtn.disabled, "translate button must be disabled while pending");
  translateBtn.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
  await tick(120);

  const sent = triggers.slice(before).filter((tr) => tr.event === "translate_text");
  assert.equal(sent.length, 1, `expected exactly one translate_text trigger, got ${sent.length}`);
  assert.equal(sent[0].value.event, "translate_text");
  assert.equal(sent[0].value.payload.text, NEW_SOURCE);
  assert.equal(sent[0].value.payload.sourceLang, "ZH");
  assert.equal(sent[0].value.payload.targetLang, "EN");
  assert.equal(typeof sent[0].value.seq, "number");

  // Pending stays IN PLACE inside the right panel — both panels keep shape.
  const resultPanel = $('div[data-testid="result-panel"]')[0];
  const pendingBox = $('div[data-testid="result-pending"]', resultPanel)[0];
  assert.ok(pendingBox, "pending state must live INSIDE the right result panel");
  assert.ok(text(pendingBox).includes("Đang dịch"), "in-place loading text missing");
  assert.ok($('div[data-testid="source-panel"]')[0], "source panel must keep its shape");
  assert.ok($('textarea[aria-label="Văn bản gốc"]')[0], "source text must stay editable");
  assert.ok(!$('textarea[aria-label="Bản dịch"]')[0],
    "no translation text may render while pending");
  assertNoSimulatedWording("pending");
  ok("one typed translate_text trigger; duplicate suppressed; pending in place");
}

// ---------------------------------------------------------------------------
console.log("STEP 7 — fresh readback renders the provider text VERBATIM");
{
  lastInvokeCleanup = invoke({
    ...VM,
    translation: {
      ...VM.translation,
      request: {
        text: NEW_SOURCE, sourceLang: "ZH", targetLang: "EN",
        fingerprint: "readback-fingerprint",
      },
      result: {
        status: "translated",
        text: NEW_TRANSLATED,
        error: null,
        detectedSourceLanguage: "ZH",
        billedCharacters: 61,
        apiLabel: "API 1/1",
        provider: "DeepL",
      },
    },
  });
  await tick(120);
  const resultPanel = $('div[data-testid="result-panel"]')[0];
  const out = $('textarea[aria-label="Bản dịch"]', resultPanel)[0];
  assert.ok(out, "result area missing from the RIGHT panel");
  // VERBATIM: identical string, line break preserved, identifiers untouched.
  assert.equal(out.value, NEW_TRANSLATED);
  assert.ok(out.value.includes("\n"), "line break was not preserved");
  assert.ok(out.readOnly === true, "result must be read-only (no UI rewriting)");
  for (const id of ["HS 9403.20.10", "PO-88213"]) {
    assert.ok(out.value.includes(id), `identifier ${id} was mangled`);
  }
  const t = mainText();
  assert.ok(!t.includes("Đang dịch"), "loading state must clear after readback");
  assert.ok(!t.includes("ĐANG DỊCH"), "action must leave the pending label");
  assert.ok(t.includes("61"), "billed characters missing");
  assert.ok(t.includes("API 1/1"), "api label missing");
  assertNoSimulatedWording("translated");
  ok("result verbatim (line break + identifiers), loading cleared, metadata shown");
}

// ---------------------------------------------------------------------------
console.log("STEP 8 — provider error state is honest and in place");
{
  await remount({
    ...VM,
    translation: {
      ...VM.translation,
      request: { text: NEW_SOURCE, sourceLang: "ZH", targetLang: "EN", fingerprint: "f" },
      result: {
        status: "error",
        text: null,
        error: "DeepL không thể xử lý yêu cầu lúc này.",
        detectedSourceLanguage: null,
        billedCharacters: null,
        apiLabel: null,
        provider: "DeepL",
      },
    },
  });
  await tick(120);
  const resultPanel = $('div[data-testid="result-panel"]')[0];
  const err = $('div[data-testid="translation-error"]', resultPanel)[0];
  assert.ok(err, "error state must render INSIDE the right result panel");
  const t = mainText();
  assert.ok(t.includes("Chưa dịch được nội dung này"), "error heading missing");
  assert.ok(t.includes("DeepL không thể xử lý yêu cầu lúc này."), "provider message missing");
  assert.ok(!$('textarea[aria-label="Bản dịch"]')[0], "no fake translation may be rendered");
  assertNoSimulatedWording("error");
  ok("error state explicit and in place, zero fabricated translation");
}

// ---------------------------------------------------------------------------
console.log("STEP 9 — idle placeholder before translation");
{
  await remount({
    ...VM,
    translation: { ...VM.translation, request: null, result: null },
  });
  await tick(120);
  const resultPanel = $('div[data-testid="result-panel"]')[0];
  const placeholder = $('div[data-testid="result-placeholder"]', resultPanel)[0];
  assert.ok(placeholder, "idle placeholder must occupy the RIGHT panel");
  assert.ok(text(placeholder).includes("Bản dịch sẽ hiển thị tại đây"),
    "placeholder wording missing");
  assert.ok(!$('textarea[aria-label="Bản dịch"]')[0],
    "no translation text may render before the first translation");
  assertNoSimulatedWording("idle");
  ok("honest idle placeholder in place, nothing fabricated");
}

// ---------------------------------------------------------------------------
console.log("STEP 10 — unconfigured deployment is honest and inert");
{
  const capability = {
    ...VM.translation.capability,
    configured: false,
    apiCount: 0,
    configNotice: "Translation service chưa được cấu hình. Chưa cấu hình API DeepL.",
  };
  await remount({
    ...VM,
    translation: { capability, request: null, result: null },
  });
  await tick(120);
  const t = mainText();
  assert.ok(t.includes("Translation service chưa được cấu hình"), "config state missing");
  assert.ok(t.includes("Bản dịch sẽ hiển thị tại đây"), "idle placeholder missing");
  const translateBtn = $('button[data-testid="translate-action"]')[0];
  assert.ok(translateBtn && translateBtn.disabled, "Translate must be disabled when unconfigured");
  // Typing must not enable a call the backend cannot serve.
  await typeTextarea($('textarea[aria-label="Văn bản gốc"]')[0], "Xin chào");
  assert.ok($('button[data-testid="translate-action"]')[0].disabled, "Translate must stay disabled");
  // A quick chip still fills SOURCE only — it must NOT fabricate a
  // translation on an unconfigured deployment.
  const triggersBefore = triggers.length;
  await clickSelector('button[data-testid="quick-chip"]', window.document, 0);
  assert.ok($('textarea[aria-label="Văn bản gốc"]')[0].value.length > 0,
    "chip must fill source even when unconfigured");
  assert.ok(!$('textarea[aria-label="Bản dịch"]')[0],
    "chip click fabricated a translation on an unconfigured deployment");
  assert.equal(triggers.length, triggersBefore, "chip dispatched on unconfigured deployment");
  assertNoSimulatedWording("unconfigured");
  ok("config-required state honest; action stays disabled; chips never fabricate");
}

// ---------------------------------------------------------------------------
console.log("STEP 11 — RBAC-denied deployment is honest and inert");
{
  const capability = { ...VM.translation.capability, configured: true, allowed: false };
  await remount({
    ...VM,
    translation: { capability, request: null, result: null },
  });
  await tick(120);
  const t = mainText();
  assert.ok(t.includes("không có quyền dịch thuật"), "RBAC denial state missing");
  assert.ok(t.includes("translation"), "missing permission must be named");
  const translateBtn = $('button[data-testid="translate-action"]')[0];
  assert.ok(translateBtn && translateBtn.disabled, "Translate must be disabled when denied");
  await typeTextarea($('textarea[aria-label="Văn bản gốc"]')[0], "Xin chào");
  assert.ok($('button[data-testid="translate-action"]')[0].disabled, "Translate must stay disabled");
  assert.ok(!$('textarea[aria-label="Bản dịch"]')[0],
    "no translation text may render for a denied role");
  assertNoSimulatedWording("rbac");
  ok("RBAC-denied state honest; action stays disabled; nothing fabricated");
}

// ---------------------------------------------------------------------------
console.log("STEP 12 — copy hands over the VERBATIM text, and fails honestly");
{
  await remount(VM);
  await tick(120);
  let copied = null;
  Object.defineProperty(window.navigator, "clipboard", {
    configurable: true,
    value: { writeText: async (value) => { copied = value; } },
  });
  await click("Sao chép", "button");
  await tick(80);
  assert.equal(copied, VM.translation.result.text, "clipboard did not get the verbatim text");
  assert.ok(mainText().includes("Đã sao chép"), "copy confirmation missing");

  // Without clipboard permission the UI must not pretend it worked.
  Object.defineProperty(window.navigator, "clipboard", {
    configurable: true,
    value: { writeText: async () => { throw new Error("denied"); } },
  });
  await click("Đã sao chép", "button");
  await tick(80);
  assert.ok(mainText().includes("sao chép thủ công"), "honest copy failure missing");
  ok("copy passes verbatim text; failure is disclosed");
}

// ---------------------------------------------------------------------------
console.log("STEP 13 — quick glossary renders and NEVER translates");
{
  const t = mainText();
  assert.ok(t.includes("Từ điển nghiệp vụ nhanh"), "glossary heading missing");
  // LOGI_INTERNAL_UX_SIMPLIFY_01 — donor-shape vertical vi/zh list (15
  // seeded pairs), replacing the old 20-item grid.
  const grid = $('div[data-testid="glossary"]')[0];
  assert.ok(grid, "glossary list missing");
  assert.ok(grid.className.includes("grid-cols-1"), "glossary must be the donor vertical list");
  const items = $('div[data-testid="glossary-item"]');
  assert.equal(items.length, 15, `expected the donor 15 glossary items, got ${items.length}`);
  assert.ok(text(items[0]).includes("Xin chào") && text(items[0]).includes("你好"),
    "glossary item must pair Vietnamese with Chinese");
  for (const item of items) {
    assert.ok(item.className.includes("justify-between"), "glossary row lost the donor vi/zh shape");
  }
  assert.ok(
    items.some((el) => text(el).includes("Hóa đơn") && text(el).includes("发票")),
    "logistics glossary coverage missing"
  );

  // Clicking glossary entries dispatches NOTHING and touches NEITHER panel.
  const source = $('textarea[aria-label="Văn bản gốc"]')[0];
  const sourceBefore = source.value;
  const resultBefore = $('textarea[aria-label="Bản dịch"]')[0].value;
  const triggersBefore = triggers.length;
  await clickSelector('div[data-testid="glossary-item"]', window.document, 3);
  await clickSelector('div[data-testid="glossary-item"]', window.document, 7);
  assert.equal(triggers.length, triggersBefore, "glossary click dispatched an event");
  assert.equal(source.value, sourceBefore, "glossary click touched the source text");
  assert.equal($('textarea[aria-label="Bản dịch"]')[0].value, resultBefore,
    "glossary click touched the translated output");
  assertNoSimulatedWording("glossary");
  ok("donor 15-item reference glossary renders; clicks are inert");
}

// ---------------------------------------------------------------------------
console.log("STEP 14 — no secret material, no fake engine in the DOM");
{
  const html = fullHtml();
  assert.ok(!html.includes("fixture-fake-deepl-key"), "provider key material in DOM");
  assert.ok(!html.includes("DeepL-Auth-Key"), "auth header material in DOM");
  assertNoSimulatedWording("secrets");
  ok("DOM carries zero credential material and zero fake-engine wording");
}

// ---------------------------------------------------------------------------
console.log("STEP 15 — mobile: drawer routes here; targets; no overflow trap");
{
  await clickSelector('button[aria-label="Mở menu"]');
  const drawer = $(".fixed.inset-0.z-50")[0];
  assert.ok(drawer, "mobile drawer missing");
  const drawerItem = findClickable("Dịch thuật", "a", drawer);
  assert.ok(drawerItem, "drawer item missing");
  assert.ok(!text(drawerItem).includes("Sắp có"), "drawer item still marked 'Sắp có'");
  await click("Dịch thuật", "a", drawer);
  assert.ok(mainText().includes("Dịch Thuật"), "drawer must open the translation workspace");

  // Structural mobile behaviour: panels stack, text stays 16px, every primary
  // control keeps a >= 44px touch target, nothing forces horizontal width.
  const workspace = $('div[data-testid="translation-workspace"]')[0];
  assert.ok(workspace.className.includes("grid-cols-1"), "panels must stack on mobile");
  const sourceArea = $('textarea[aria-label="Văn bản gốc"]')[0];
  assert.ok(sourceArea.className.includes("w-full"), "source textarea must be full width");
  assert.ok(sourceArea.className.includes("text-[16px]"),
    "16px text prevents mobile keyboard zoom");
  const resultArea = $('textarea[aria-label="Bản dịch"]')[0];
  assert.ok(resultArea.className.includes("w-full"), "result area must be full width");
  assert.ok(resultArea.className.includes("text-[16px]"), "result must stay 16px on mobile");
  const swapBtn = $('button[aria-label="Đổi chiều dịch"]')[0];
  assert.ok(swapBtn.className.includes("w-11") && swapBtn.className.includes("h-11"),
    "swap control must keep a 44px touch target");
  assert.ok($('button[data-testid="translate-action"]')[0].className.includes("min-h-[48px]"),
    "translate button below touch target");
  for (const chip of $('button[data-testid="quick-chip"]')) {
    assert.ok(chip.className.includes("min-h-[28px]"), "chip lost the donor compact pill shape");
    assert.ok(chip.className.includes("max-w-[220px]"), "chip lost the donor truncation width");
  }
  for (const select of [$('select[aria-label="Ngôn ngữ nguồn"]')[0], $('select[aria-label="Ngôn ngữ đích"]')[0]]) {
    assert.ok(select.className.includes("min-w-0"), "direction select must shrink safely");
    assert.ok(select.className.includes("min-h-[44px]"), "direction select below touch target");
  }
  ok("drawer routes to the workspace; stacked layout + targets + full-width text");
}

console.log(`\nDOM acceptance PASSED — ${passed} checks`);
