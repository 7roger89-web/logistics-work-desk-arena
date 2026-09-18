// ============================================================================
// DOM acceptance — LOGI_FRONTEND_WORKFLOW_OVERHAUL_01 · ROLE SIMULATOR TRUST
// (P1.5)
//
// The header's ADMIN/SUPPORT/SALE switcher is UI-only — it must never make a
// normal employee feel they can really change their permissions:
//
//   - production-like runtime (environment.isSandbox = false): NO switcher,
//     NO role buttons anywhere — only the actual logged-in identity+role
//     (from the backend view-model's user);
//   - sandbox: the preview switcher remains, but visibly labelled
//     "Xem trước", the menu is announced as display-only, and switching only
//     changes presentation with a truthful "XEM TRƯỚC" toast;
//   - canonical RBAC untouched: no new roles, no auth changes in the UI.
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

const bundlePath = path.join(ROOT, "component", "dist", "logi-shell.js");
const mod = await import(bundlePath);
assert.equal(typeof mod.default, "function", "bundle must default-export mount");
mountRef.current = mod.default;

console.log("SCENARIO 1 — production-like runtime shows ONLY the actual role");
{
  const prod = structuredClone(FIXTURE);
  prod.environment = { ...prod.environment, isSandbox: false, label: "Production", transport: "REAL_MONGO" };
  invoke(prod);
  await tick(200);
  assert.ok(!$('[data-testid="role-preview-switcher"]').length, "no preview switcher in normal runtime");
  assert.ok(!$('[data-testid="role-preview-mobile"]').length, "no mobile role buttons in normal runtime");
  const badge = $('[data-testid="actual-role-badge"]')[0];
  assert.ok(badge, "actual identity block present");
  assert.ok(text(badge).includes(FIXTURE.user.name), "actual user name shown");
  assert.ok(text(badge).includes(FIXTURE.user.role), "actual role shown");
  // No way to switch roles anywhere in the header or drawer.
  const roleButtons = $("button").filter((b) => ["ADMIN", "SUPPORT", "SALE"].includes(text(b)));
  assert.equal(roleButtons.length, 0, "no role-switch buttons in normal runtime");
  ok(`normal runtime shows the actual role only (${FIXTURE.user.role}, no switcher)`);
}

console.log("SCENARIO 2 — sandbox keeps the preview switcher, labelled display-only");
{
  const sandbox = structuredClone(FIXTURE);
  sandbox.environment = { ...sandbox.environment, isSandbox: true, label: "Preview / Staging" };
  triggers = [];
  invoke(sandbox);
  await tick(200);
  const switcher = $('[data-testid="role-preview-switcher"]')[0];
  assert.ok(switcher, "sandbox keeps the role preview switcher");
  assert.ok(text(switcher).includes("Xem trước"), "switcher visibly labelled XEM TRƯỚC");
  const toggle = $("button", switcher)[0];
  assert.equal(toggle.getAttribute("aria-expanded"), "false", "menu collapsed initially");
  toggle.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
  await tick(120);
  const menu = $('[data-testid="role-preview-menu"]')[0];
  assert.ok(menu, "preview menu opens");
  assert.ok(text(menu).includes("chỉ thay hiển thị"), "menu says display-only");
  assert.equal(toggle.getAttribute("aria-expanded"), "true", "aria-expanded tracks the menu");

  // Switching is PREVIEW: truthful toast, presentation only.
  const admin = $("button", menu).find((b) => text(b).includes("ADMIN"));
  admin.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
  await tick(120);
  assert.ok(bodyText().includes("XEM TRƯỚC"), "switching announces itself as PREVIEW, not as a real permission change");
  assert.ok(bodyText().includes("ADMIN"), "preview role reflected in the header");
  ok("sandbox preview switcher labelled and truthful about being display-only");
}

console.log(`\nROLE_TRUST_DOM_ACCEPTANCE=PASSED checks=${passed}`);
