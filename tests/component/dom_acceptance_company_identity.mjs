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
//   2. The GLOBAL footer reads the SAME display authority
//      ("Trường Thành Logistics · <internal/staging status>") — the Control
//      Tower footer repair removed the hard-coded statutory legal_name AND the
//      global "Đại lý: Phú Anh Logistics Việt Nam" attribution.
//   3. Phú Anh Logistics is NOT rendered as the operating brand anywhere in
//      the global shell (header, footer, or any chrome).
//   4. Partner/agent identities are data, not brand: the vm still carries the
//      AGT-PHUANH partner record (CÔNG TY TNHH PHÚ ANH LOGISTICS) and partner
//      contexts may still render Phú Anh when explicitly identified as a
//      partner/agent — authority_agents and its fixtures are untouched.
//   5. Degradation is truthful: with no vm displayName the header shows the
//      unbranded "Nội bộ" while the footer keeps the prescribed
//      "Trường Thành Logistics" display-brand fallback.
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

console.log("STEP 3 — Phú Anh is rendered nowhere in the global shell");
{
  assert.ok(!bodyText().includes(OLD_BRAND), "old brand subtitle still rendered");
  const footer = $("footer")[0];
  assert.ok(footer, "footer missing");
  assert.ok(!text(footer).includes("Phú Anh"), "global footer must not render Phú Anh");
  ok("no global shell surface renders Phú Anh as the operating brand");
}

console.log("STEP 4 — global footer = display authority + internal/staging status");
{
  const footer = $("footer")[0];
  assert.ok(footer, "footer missing");
  const ft = text(footer);
  // Same ONE display authority as the header (vm environment.displayName).
  assert.ok(ft.startsWith("Trường Thành Logistics · "),
    `footer must read "Trường Thành Logistics · <status>", got: ${ft.slice(0, 160)}`);
  assert.ok(ft.includes("Bản nội bộ"), "existing internal/staging status text missing");
  // The Control Tower repair: no hard-coded statutory legal_name and no global
  // agent attribution in the ordinary footer.
  assert.ok(!ft.includes("CÔNG TY TNHH GIAO NHẬN QUỐC TẾ"), "footer must not hard-code the statutory legal_name");
  assert.ok(!ft.includes("Đại lý: Phú Anh"), "global footer must not carry the Phú Anh agent attribution");
  ok("footer = Trường Thành Logistics · status (display authority only)");
}

console.log("STEP 4b — Phú Anh partner data preserved (data, not brand)");
{
  // The agent master record remains untouched where it belongs: the staging
  // authority_agents seed and the partner-context fixtures that represent it.
  const seedSrc = readFileSync(path.join(ROOT, "views/logi_staging_seed.py"), "utf8");
  assert.ok(seedSrc.includes("AGT-PHUANH"), "authority_agents seed lost the AGT-PHUANH record");
  assert.ok(seedSrc.includes("CÔNG TY TNHH PHÚ ANH LOGISTICS"), "authority_agents seed lost the agent legal_name");
  const partnerFixture = readFileSync(
    path.join(ROOT, "tests/component/fixtures/view_model_partner_context.json"), "utf8"
  );
  assert.ok(partnerFixture.includes("AGT-PHUANH"), "partner-context fixture lost the AGT-PHUANH record");
  assert.ok(partnerFixture.includes("CÔNG TY TNHH PHÚ ANH LOGISTICS"),
    "partner-context fixture lost the agent legal_name");
  // Source-level guard: the global Layout carries no Phú Anh string at all.
  const layoutSrc = readFileSync(path.join(ROOT, "component/src/components/Layout.tsx"), "utf8");
  assert.ok(!layoutSrc.includes("Phú Anh"), "global Layout.tsx still contains a Phú Anh string");
  ok("agent record intact in authority_agents seed + partner fixtures; global Layout source has no Phú Anh");
}

console.log("STEP 5 — remount without vm displayName: truthful degradation");
{
  const degraded = JSON.parse(JSON.stringify(VM));
  delete degraded.environment.displayName;
  await invoke(degraded);
  await tick(200);
  const header = $("header")[0];
  const ht = text(header);
  assert.ok(ht.includes("Nội bộ"), "unbranded subtitle fallback missing");
  assert.ok(!ht.includes("Trường Thành Logistics ·"), "bundle must not hard-code the brand as header fallback");
  assert.ok(!ht.includes("Phú Anh"), "degraded header must not invent a brand");
  // Footer keeps the Control-Tower-prescribed display-brand fallback.
  const ft = text($("footer")[0]);
  assert.ok(ft.startsWith("Trường Thành Logistics · "), "footer display-brand fallback missing");
  assert.ok(!ft.includes("Phú Anh"), "degraded footer must not invent an agent attribution");
  ok("header degrades unbranded; footer keeps the prescribed display-brand fallback");
}

console.log(`\nDOM ACCEPTANCE PASS — ${passed} checks`);
process.exit(0);
