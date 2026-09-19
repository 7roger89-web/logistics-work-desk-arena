// ============================================================================
// DOM acceptance — LOGI_COMPANY_IDENTITY_TRUTH_01 · COMPANY IDENTITY AUTHORITY
//
// Drives the REAL production bundle (component/dist/logi-shell.js) and proves
// the Owner-confirmed separation between display identity and legal identity:
//
//   1. Ordinary app branding is the ONE display authority delivered by the
//      Python view-model (`environment.displayName` ← core.config
//      .DISPLAY_COMPANY_NAME): the header subtitle reads
//      "Trường Thành Logistics · Nội bộ".
//   2. Phú Anh Logistics is NOT rendered as the operating brand anywhere
//      (the old hard-coded "Phú Anh Logistics · Nội bộ" brand is gone from
//      the bundle AND from every rendered header).
//   3. The legal/attribution footer surface is UNCHANGED: it still names the
//      authority_companies legal entity (CÔNG TY TNHH GIAO NHẬN QUỐC TẾ
//      TRƯỜNG THÀNH) and the authority_agents partner attribution
//      (Đại lý: Phú Anh Logistics Việt Nam) — data-derived, not brand.
//   4. Degradation is truthful: with no vm displayName the shell shows the
//      unbranded "Nội bộ" instead of inventing or hard-coding any brand.
// ============================================================================

import { readFileSync } from "node:fs";
import assert from "node:assert/strict";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const require = createRequire(path.join(ROOT, "component/package.json"));
const { JSDOM } = require("jsdom");

// The vm fixture carries the display name EXACTLY as the real Python
// view-model delivers it (core.config.DISPLAY_COMPANY_NAME → environment).
const VM = JSON.parse(
  readFileSync(path.join(ROOT, "tests/component/fixtures/view_model_phase_b.json"), "utf8")
);
assert.equal(VM.environment?.displayName, "Trường Thành Logistics",
  "fixture must carry the vm display-name channel value");

const OLD_BRAND = "Phú Anh Logistics · Nội bộ";

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

// Bundle source guard first: the old brand must not even exist in the shipped JS.
console.log("STEP 0 — bundle source carries no hard-coded operating brand");
{
  const bundle = readFileSync(path.join(ROOT, "component", "dist", "logi-shell.js"), "utf8");
  assert.ok(!bundle.includes(OLD_BRAND), "bundle still hard-codes the old Phú Anh operating brand");
  ok("old Phú Anh brand string removed from the production bundle");
}

console.log("STEP 1 — boot with the vm display-name channel");
const bundlePath = path.join(ROOT, "component", "dist", "logi-shell.js");
const mod = await import(bundlePath);
assert.equal(typeof mod.default, "function", "bundle must default-export mount");
mountRef.current = mod.default;
await invoke(VM);
await tick(200);
assert.ok(!bodyText().includes("process is not defined"));

console.log("STEP 2 — header identifies the business as Trường Thành Logistics");
{
  const header = $("header")[0];
  assert.ok(header, "header missing");
  const ht = text(header);
  assert.ok(ht.includes("TRƯỜNG THÀNH"), "logo brand missing");
  assert.ok(ht.includes("Trường Thành Logistics · Nội bộ"),
    `header subtitle must read "Trường Thành Logistics · Nội bộ", got: ${ht.slice(0, 200)}`);
  assert.ok(!ht.includes("Phú Anh"), "header must not present Phú Anh as the operating brand");
  ok("header subtitle = Trường Thành Logistics · Nội bộ (vm-sourced)");
}

console.log("STEP 3 — the old Phú Anh operating brand is rendered nowhere");
{
  assert.ok(!bodyText().includes(OLD_BRAND), "old brand subtitle still rendered");
  ok("no surface renders the old operating brand");
}

console.log("STEP 4 — legal/attribution footer UNCHANGED (authority-derived, not brand)");
{
  const footer = $("footer")[0];
  assert.ok(footer, "footer missing");
  const ft = text(footer);
  assert.ok(ft.includes("CÔNG TY TNHH GIAO NHẬN QUỐC TẾ TRƯỜNG THÀNH"),
    "footer must keep naming the authority_companies legal entity");
  assert.ok(ft.includes("Đại lý: Phú Anh Logistics Việt Nam"),
    "footer agent attribution (authority_agents partner record) must stay unchanged");
  assert.ok(ft.includes("staging"), "sandbox environment disclosure missing");
  ok("footer legal entity + agent attribution untouched");
}

console.log("STEP 5 — remount without vm displayName: truthful unbranded degradation");
{
  const degraded = JSON.parse(JSON.stringify(VM));
  delete degraded.environment.displayName;
  await invoke(degraded);
  await tick(200);
  const header = $("header")[0];
  const ht = text(header);
  assert.ok(ht.includes("Nội bộ"), "unbranded subtitle fallback missing");
  assert.ok(!ht.includes("Trường Thành Logistics ·"), "bundle must not hard-code the brand as fallback");
  assert.ok(!ht.includes("Phú Anh"), "degraded header must not invent a brand");
  ok("no vm value → unbranded 'Nội bộ' (never an invented brand)");
}

console.log(`\nDOM ACCEPTANCE PASS — ${passed} checks`);
process.exit(0);
