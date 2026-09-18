// LOGI_RUNTIME_CONTRACT_SLASH_ROUTE_REPAIR_01 — committed-bundle regression
// for the EXACT production specimen: "HDV 82/VSAL 2025".
//
// Drives the REAL committed bundle (component/dist/logi-shell.js) the way
// web_app.py serves it (same single Components v2 mount + data channel) and
// proves the owner path  Hợp đồng → HDV 82/VSAL 2025 → MỞ  lands on the real
// ContractDetail work desk — never the "Sắp có — chưa triển khai" deferred
// placeholder, never the NotFound wildcard — and that a normal non-slash id
// still opens. Uses the existing canonical contract-workflow fixture
// (isolated mongomock readback), identical harness mechanics to
// dom_acceptance_contract_workflow.mjs.
import { readFileSync } from "node:fs";
import assert from "node:assert/strict";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const require = createRequire(path.join(ROOT, "component/package.json"));
const { JSDOM } = require("jsdom");
const FIX = JSON.parse(
  readFileSync(path.join(ROOT, "tests/component/fixtures/view_model_contract_workflow.json"), "utf8")
);

const dom = new JSDOM("<!DOCTYPE html><html><body></body></html>", {
  url: "http://localhost:8501/",
  pretendToBeVisual: true,
});
const { window } = dom;
globalThis.window = window;
globalThis.document = window.document;
try { Object.defineProperty(globalThis, "navigator", { value: window.navigator, configurable: true }); } catch {}
for (const k of [
  "HTMLElement","HTMLInputElement","HTMLTextAreaElement","HTMLSelectElement",
  "HTMLAnchorElement","Event","CustomEvent","MouseEvent","KeyboardEvent",
  "Node","MutationObserver","getComputedStyle",
]) globalThis[k] = window[k];
if (!globalThis.MessageChannel) globalThis.MessageChannel = window.MessageChannel;
window.HTMLElement.prototype.scrollIntoView = () => {};

const tick = (ms = 60) => new Promise((r) => setTimeout(r, ms));
const $ = (sel, root = window.document) => [...root.querySelectorAll(sel)];
const text = (el) => (el.textContent || "").replace(/\s+/g, " ").trim();
const mainText = () => text($("main")[0] ?? window.document.body);

let passed = 0;
function ok(name) { passed += 1; console.log(`  ✓ ${name}`); }

const host = window.document.createElement("div");
window.document.body.appendChild(host);
const mountRef = { current: null };
function invoke(data) {
  mountRef.current({
    name: "logi_shell",
    data,
    parentElement: host,
    setTriggerValue: () => {},
  });
}

/** Rewrite the contract row(s) to the exact specimen id, keeping the rest. */
function contractsFor(id, { only = false } = {}) {
  const state = structuredClone(FIX.success);
  const rows = only ? state.contracts.slice(0, 1) : state.contracts;
  state.contracts = rows.map((c) => ({ ...c, id, contractNo: id }));
  return state;
}

async function openContract(id, { only = false } = {}) {
  invoke(contractsFor(id, { only })); await tick(140);
  const aside = $("aside")[0];
  const navHd = $("a", aside).find((a) => text(a) === "Hợp đồng");
  assert.ok(navHd, "nav Hợp đồng");
  navHd.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
  await tick(140);

  const encoded = "/hop-dong/" + encodeURIComponent(id);
  const detailLinks = $("main a").filter(
    (a) => (a.getAttribute("href") || "").startsWith("/hop-dong/") && a.getAttribute("href") !== "/hop-dong/moi"
  );
  assert.ok(detailLinks.length >= 3, `expected ≥3 detail links for "${id}", got ${detailLinks.length}`);
  for (const a of detailLinks) assert.equal(a.getAttribute("href"), encoded, "one encoded segment per detail link");

  // Exact Owner action: the MỞ button.
  const openBtn = $("main a").find((a) => text(a).includes("MỞ"));
  assert.ok(openBtn, "MỞ button present");
  openBtn.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
  await tick(140);
  return encoded;
}

const mount = (await import(process.env.BUNDLE_PATH || path.join(ROOT, 'component/dist/logi-shell.js'))).default;
mountRef.current = mount;

const PROD_SPECIMEN = "HDV 82/VSAL 2025";

// A. Exact production slash-containing id → real ContractDetail.
{
  await openContract(PROD_SPECIMEN, { only: true });
  const h1 = $("main h1")[0];
  assert.ok(h1, "detail h1 present");
  assert.equal(text(h1), PROD_SPECIMEN, "exact identity resolves");
  assert.ok(mainText().includes("Danh tính pháp lý"), "ContractDetail work desk rendered");
  for (const banned of ["Sắp có", "chưa triển khai", "Màn hình phụ"])
    assert.ok(!mainText().includes(banned), `must not render "${banned}"`);
  assert.ok(!$("[data-testid='not-found']").length, "must not render NotFound wildcard");
  ok(`HDV 82/VSAL 2025 → MỞ → real ContractDetail (no Sắp có / NotFound)`);
}

// B. Every backend-permitted slash/percent/unicode id from the canonical fixture.
{
  for (const id of FIX.ids) {
    if (id === PROD_SPECIMEN) continue;
    await openContract(id, { only: false });
    assert.equal(text($("main h1")[0]), id, "exact identity resolves");
    assert.ok(!mainText().includes("Sắp có") && !$("[data-testid='not-found']").length);
  }
  ok("canonical slash/percent/unicode fixture ids all resolve to detail");
}

// C. Non-slash contract id still opens correctly.
{
  await openContract("HDMB-0306", { only: true });
  assert.equal(text($("main h1")[0]), "HDMB-0306", "non-slash identity resolves");
  assert.ok(mainText().includes("Danh tính pháp lý"), "non-slash detail rendered");
  assert.ok(!mainText().includes("Sắp có") && !$("[data-testid='not-found']").length);
  ok("normal non-slash id HDMB-0306 still opens ContractDetail");
}

console.log(`PASS contract slash-id specimen (${passed} groups)`);
process.exit(0);
