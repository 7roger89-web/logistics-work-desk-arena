// ============================================================================
// DOM acceptance — LOGI_FRONTEND_WORKFLOW_OVERHAUL_01 · P2 POLISH
//   - PROTOTYPE residue: chip renders in sandbox only, absent in production-
//     like runtime;
//   - quick add: real dialog semantics (role/aria-modal/name, Escape closes);
//   - tabular numerals + reduced-motion ship as CSS (checked by bundle scan).
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
  readFileSync(path.join(ROOT, "tests", "component", "fixtures", "view_model_phase_b.json"), "utf8")
);

const dom = new JSDOM("<!DOCTYPE html><html><body></body></html>", { url: "http://localhost:8501/", pretendToBeVisual: true });
const { window } = dom;
globalThis.window = window;
globalThis.document = window.document;
try { Object.defineProperty(globalThis, "navigator", { value: window.navigator, configurable: true }); } catch {}
for (const k of ["HTMLElement","HTMLInputElement","HTMLTextAreaElement","HTMLSelectElement","HTMLAnchorElement","Event","CustomEvent","MouseEvent","KeyboardEvent","Node","MutationObserver","getComputedStyle"]) globalThis[k] = window[k];
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
const mod = await import(path.join(ROOT, "component", "dist", "logi-shell.js"));
mountRef.current = mod.default;

console.log("STEP 1 — PROTOTYPE chip: sandbox yes, production-like no");
{
  const sandbox = structuredClone(FIXTURE);
  sandbox.environment = { ...sandbox.environment, isSandbox: true };
  invoke(sandbox); await tick(200);
  assert.ok(bodyText().includes("PROTOTYPE"), "sandbox shows the PROTOTYPE chip");
  ok("sandbox shows the PROTOTYPE chip");
}
{
  const prod = structuredClone(FIXTURE);
  prod.environment = { ...prod.environment, isSandbox: false, label: "Production", transport: "REAL_MONGO" };
  invoke(prod); await tick(200);
  assert.ok(!bodyText().includes("PROTOTYPE"), "production-like runtime has no PROTOTYPE residue");
  ok("production-like runtime carries no PROTOTYPE residue");
}

console.log("STEP 2 — quick add sheet: dialog semantics + Escape");
{
  const plusBtn = $("button").find((b) => text(b).includes("Thêm"));
  assert.ok(plusBtn, "quick-add trigger present (mobile bottom nav)");
  plusBtn.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
  await tick(140);
  const sheet = window.document.getElementById("quick-add-sheet");
  assert.ok(sheet, "quick add sheet opens");
  const panel = sheet.querySelector('[role="dialog"]');
  assert.ok(panel && panel.getAttribute("aria-modal") === "true", "role=dialog + aria-modal");
  const labelledBy = panel.getAttribute("aria-labelledby");
  assert.ok(text(window.document.getElementById(labelledBy)).includes("Thêm mới nhanh"), "accessible name from the visible heading");
  window.document.dispatchEvent(new window.KeyboardEvent("keydown", { key: "Escape", bubbles: true, cancelable: true }));
  await tick(120);
  assert.ok(!window.document.getElementById("quick-add-sheet"), "Escape closes the quick add sheet");
  ok("quick add is a named modal, closable with Escape");
}

console.log("STEP 3 — CSS ships tabular numerals + prefers-reduced-motion");
{
  const css = readFileSync(path.join(ROOT, "component", "dist", "logi-shell.css"), "utf8");
  assert.ok(css.includes("tabular-nums"), "tabular numerals present in the shipped CSS");
  assert.ok(css.includes("prefers-reduced-motion"), "reduced-motion media query present in the shipped CSS");
  ok("shipped CSS carries tabular numerals + reduced-motion handling");
}

console.log(`\nP2_POLISH_DOM_ACCEPTANCE=PASSED checks=${passed}`);
