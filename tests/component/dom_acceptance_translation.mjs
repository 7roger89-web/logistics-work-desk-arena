// ============================================================================
// LOGI_TRANSLATION_WORKSPACE_01 — DOM/navigation acceptance for /dich-thuat.
//
// Runs the REAL production bundle (component/dist/logi-shell.js) in jsdom with
// a REAL-backend fixture (scripts/gen_translation_fixture.py — isolated
// mongomock staging; the DeepL provider boundary is MOCKED, so no real paid
// API call happens anywhere in this suite) and verifies:
//   1. boot (no process/BidiComponent failure)
//   2. sidebar "Dịch thuật" carries NO "Sắp có" marker anymore
//   3. the route opens the REAL workspace: heading, backend-derived language
//      options, external-provider privacy disclosure, last readback
//   4. Translate emits ONE typed "translate_text" trigger, and an enthusiastic
//      double click does NOT emit a second one (paid-call guard)
//   5. fresh readback renders the provider text VERBATIM (line breaks + HS
//      code / shipment ID / invoice ref / numbers untouched)
//   6. provider error state is honest (no fabricated translation)
//   7. unconfigured deployment shows the honest "chưa được cấu hình" state and
//      disables the action
//   8. copy action hands the VERBATIM text to the clipboard, and fails honestly
//   9. mobile: drawer routes to the same workspace, touch targets, no
//      fixed-width overflow dependency
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

async function clickSelector(sel, root = window.document) {
  const el = $(sel, root)[0];
  assert.ok(el, `selector "${sel}" not found`);
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

const bundlePath = path.join(ROOT, "component/dist/logi-shell.js");

// A fresh intent, different from the fixture's last readback.
const NEW_SOURCE = "Khách hỏi: 什么时候可以提货？\nHS 9403.20.10 · PO-88213";
const NEW_TRANSLATED = "Customer asks: when can the goods be picked up?\nHS 9403.20.10 · PO-88213";

// ---------------------------------------------------------------------------
console.log("STEP 1 — boot production bundle");
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
console.log("STEP 3 — /dich-thuat opens the REAL translation workspace");
{
  const t = mainText();
  assert.ok(!t.includes("Sắp có — chưa triển khai"), "route still renders the placeholder");
  assert.ok(t.includes("Dịch thuật"), "workspace heading missing");

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

  // Privacy boundary is disclosed — this is not sold as a local translator.
  assert.ok(VM.translation.capability.externalProvider === true);
  assert.ok(t.includes("DeepL"), "provider not named");
  assert.ok(t.includes("KHÔNG phải bộ dịch chạy cục bộ"), "privacy disclosure missing");

  // The last authoritative readback is present; nothing is fabricated.
  assert.ok(t.includes("Kết quả dịch"), "result card missing");
  assert.ok(t.includes("SHP-2026-0147"), "last readback text missing");
  assert.ok(t.includes("ZH"), "detected source language missing");
  ok("real workspace: backend language options + privacy disclosure + last readback");
}

// ---------------------------------------------------------------------------
console.log("STEP 4 — Translate emits ONE trigger; double click cannot pay twice");
{
  const source = $('textarea[aria-label="Văn bản nguồn"]')[0];
  assert.ok(source, "source textarea missing");
  await typeTextarea(source, NEW_SOURCE);
  await selectOption($('select[aria-label="Ngôn ngữ nguồn"]')[0], "ZH");
  await selectOption($('select[aria-label="Ngôn ngữ đích"]')[0], "EN");

  const before = triggers.length;
  await click("Dịch", "button");
  // Enthusiastic thumb: a second click while the first intent is in flight.
  const translateBtn = findClickable("Đang dịch", "button") ?? findClickable("Dịch", "button");
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
  assert.ok(mainText().includes("Đang dịch"), "loading state missing");
  ok("one typed translate_text trigger; duplicate click suppressed + loading state");
}

// ---------------------------------------------------------------------------
console.log("STEP 5 — fresh readback renders the provider text VERBATIM");
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
  const out = $('textarea[aria-label="Bản dịch"]')[0];
  assert.ok(out, "result area missing");
  // VERBATIM: identical string, line break preserved, identifiers untouched.
  assert.equal(out.value, NEW_TRANSLATED);
  assert.ok(out.value.includes("\n"), "line break was not preserved");
  assert.ok(out.readOnly === true, "result must be read-only (no UI rewriting)");
  for (const id of ["HS 9403.20.10", "PO-88213"]) {
    assert.ok(out.value.includes(id), `identifier ${id} was mangled`);
  }
  const t = mainText();
  assert.ok(!t.includes("Đang dịch"), "loading state must clear after readback");
  assert.ok(t.includes("61"), "billed characters missing");
  assert.ok(t.includes("API 1/1"), "api label missing");
  ok("result verbatim (line break + identifiers), loading cleared, metadata shown");
}

// ---------------------------------------------------------------------------
console.log("STEP 6 — provider error state is honest");
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
  const t = mainText();
  assert.ok(t.includes("Chưa dịch được nội dung này"), "error heading missing");
  assert.ok(t.includes("DeepL không thể xử lý yêu cầu lúc này."), "provider message missing");
  assert.ok(!$('textarea[aria-label="Bản dịch"]')[0], "no fake translation may be rendered");
  ok("error state explicit, zero fabricated translation");
}

// ---------------------------------------------------------------------------
console.log("STEP 7 — unconfigured deployment is honest and inert");
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
  assert.ok(t.includes("Chưa có bản dịch"), "honest idle state missing");
  const translateBtn = findClickable("Dịch", "button");
  assert.ok(translateBtn && translateBtn.disabled, "Translate must be disabled when unconfigured");
  // Typing must not enable a call the backend cannot serve.
  await typeTextarea($('textarea[aria-label="Văn bản nguồn"]')[0], "Xin chào");
  assert.ok(findClickable("Dịch", "button").disabled, "Translate must stay disabled");
  ok("config-required state honest; action stays disabled");
}

// ---------------------------------------------------------------------------
console.log("STEP 8 — copy hands over the VERBATIM text, and fails honestly");
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
console.log("STEP 9 — mobile: drawer routes here; touch targets; no fixed overflow");
{
  await clickSelector('button[aria-label="Mở menu"]');
  const drawer = $(".fixed.inset-0.z-50")[0];
  assert.ok(drawer, "mobile drawer missing");
  const drawerItem = findClickable("Dịch thuật", "a", drawer);
  assert.ok(drawerItem, "drawer item missing");
  assert.ok(!text(drawerItem).includes("Sắp có"), "drawer item still marked 'Sắp có'");
  await click("Dịch thuật", "a", drawer);
  assert.ok(mainText().includes("Dịch thuật"), "drawer must open the translation workspace");

  // Structural mobile behaviour: the direction row stacks instead of forcing
  // width, and every primary control keeps a >= 48px touch target.
  const row = $('select[aria-label="Ngôn ngữ nguồn"]')[0].closest("div.flex");
  assert.ok(row.className.includes("flex-col") && row.className.includes("md:flex-row"),
    "language row must stack on narrow viewports");
  const sourceArea = $('textarea[aria-label="Văn bản nguồn"]')[0];
  assert.ok(sourceArea.className.includes("w-full"), "source textarea must be full width");
  assert.ok(sourceArea.className.includes("text-[16px]"),
    "16px text prevents mobile keyboard zoom");
  const swapBtn = $('button[aria-label="Đổi chiều dịch"]')[0];
  assert.ok(swapBtn.className.includes("min-h-[48px]"), "swap control below touch target");
  assert.ok(findClickable("Dịch", "button").className.includes("min-h-[48px]"),
    "translate button below touch target");
  assert.ok($('textarea[aria-label="Bản dịch"]')[0].className.includes("w-full"),
    "result area must be full width");
  ok("drawer routes to the workspace; stacked layout + 48px targets + full-width text areas");
}

console.log(`\nDOM acceptance PASSED — ${passed} checks`);
