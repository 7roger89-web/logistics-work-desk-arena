// ============================================================================
// LOGI_SHIPMENT_SLASH_ROUTE_REPAIR_01 (Issue #138) — committed-bundle
// regression for the SHIPMENT detail route, mirroring the #59 contract
// specimen test one level over.
//
// Production symptom this guards: an existing completed shipment in the list
// opened the generic invalid-path screen
// ("Không tìm thấy màn hình / đường dẫn không hợp lệ") instead of the real lot.
//
// Reproduced cause: every shipment-detail URL was built by RAW concatenation
// (`"/lo-hang/" + s.id`), while the route table exposes exactly one dynamic
// segment (`/lo-hang/:id`, whose shipped matcher compiles to `([^\/]+)`).
// An identity containing `/` therefore produced a MULTI-segment pathname that
// matched only the `*` wildcard → NotFound. Identities shaped like a document
// number are real in this project (Issue #59 repaired the same shape for
// contracts: "HDV 82/VSAL 2025"), so the defect class is a data-independent
// route-construction bug, not a bad record.
//
// This test drives the REAL committed bundle (component/dist/logi-shell.js) in
// jsdom over a real-backend fixture, and proves:
//
//   1. a slash-containing shipment identity is ONE encoded segment, opens the
//      real ShipmentDetail with the EXACT identity, and never the wildcard;
//   2. the same holds for the mobile card link, the 360° links and the global
//      search result (desktop + mobile search);
//   3. a literal "%2F" inside an identity stays the literal identity (it must
//      NOT decay into "/"), i.e. no double-decode anywhere;
//   4. ordinary (LO-xxxx), canonical decimal-string (108313713320 — the Issue
//      #117 legacy numeric identity) and unicode (LÔ-xxxx) identities keep
//      their previous, unchanged one-segment route;
//   5. identities containing "?" or "#" cannot inject query/anchor syntax;
//   6. a STALE backend-composed route (the pre-fix `nextRoute` shape) still
//      reaches the truthful NotFound wildcard — the shell passes backend route
//      strings through verbatim, which is exactly why the backend producer had
//      to be repaired too, and why this wildcard behaviour stays covered.
//
// Run: node tests/component/dom_acceptance_shipment_slash_id.mjs
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
  readFileSync(path.join(ROOT, "tests/component/fixtures/view_model_contract_workflow.json"), "utf8")
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
  "HTMLAnchorElement", "Event", "CustomEvent", "MouseEvent", "KeyboardEvent", "FocusEvent",
  "Node", "MutationObserver", "getComputedStyle",
]) globalThis[k] = window[k];
if (!globalThis.MessageChannel) globalThis.MessageChannel = window.MessageChannel;
window.HTMLElement.prototype.scrollIntoView = () => {};

const tick = (ms = 60) => new Promise((r) => setTimeout(r, ms));
const $ = (sel, root = window.document) => [...root.querySelectorAll(sel)];
const text = (el) => (el.textContent || "").replace(/\s+/g, " ").trim();
const mainText = () => text($("main")[0] ?? window.document.body);
const byTestId = (id) => $(`[data-testid="${id}"]`)[0] ?? null;
const mainInput = (needle) => $("input").find((i) => (i.placeholder || "").includes(needle));
const h1 = () => text($("main h1")[0] ?? window.document.createElement("i"));

let passed = 0;
function ok(name) {
  passed += 1;
  console.log(`  ✓ ${name}`);
}

const host = window.document.createElement("div");
window.document.body.appendChild(host);
const mountRef = { current: null };
let lastInvokeCleanup = null;

function invoke(state) {
  if (lastInvokeCleanup) lastInvokeCleanup();
  lastInvokeCleanup = mountRef.current({
    name: "logi_shell",
    data: state,
    parentElement: host,
    setTriggerValue: () => {},
  });
}

function typeInto(input, value) {
  Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set.call(input, value);
  input.dispatchEvent(new window.Event("input", { bubbles: true }));
}

async function clickEl(el) {
  assert.ok(el, "clickable element missing");
  el.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
  await tick(140);
}

async function goto(label) {
  const link = $("a", $("aside")[0]).find((a) => text(a) === label);
  assert.ok(link, `nav "${label}" missing`);
  await clickEl(link);
  await tick();
}

/**
 * A fresh view-model whose FIRST shipment carries the specimen identity, so the
 * list row, the desktop table link, the mobile card link and the global search
 * result all describe the same lot. `nextRoute` is normalised to the shape the
 * REPAIRED backend emits (the fixture predates the repair), which is the
 * contract the UI consumes from then on.
 */
function stateWith(id) {
  const state = structuredClone(FIX.success);
  state.shipments = state.shipments.map((s, i) =>
    i === 0 ? { ...s, id, nextRoute: `/lo-hang/${encodeURIComponent(id)}?tab=nhap` } : s
  );
  return state;
}

/** The desktop row + mobile card that represent this exact identity. */
const containersFor = (id) => [
  ...$(`[data-testid="shipment-row"][data-shipment-id="${id}"]`),
  ...$(`[data-testid="shipment-mobile-card"][data-shipment-id="${id}"]`),
];

/** Every shipment-detail anchor of the SAME lot (identity, 360°, XỬ LÝ). */
const shipmentLinks = (id) =>
  containersFor(id).flatMap((c) =>
    $("a", c).filter((a) => (a.getAttribute("href") || "").startsWith("/lo-hang/"))
  );

async function openLotByIdentity(id) {
  invoke(stateWith(id));
  await tick(120);
  await goto("Lô Hàng");
  const containers = containersFor(id);
  const links = shipmentLinks(id);
  const identity = links.find((a) => text(a) === id);
  assert.ok(identity, `identity link for "${id}" present in the shipments desk`);
  return { identity, links, containers };
}

const mount = (await import(process.env.BUNDLE_PATH || path.join(ROOT, "component/dist/logi-shell.js"))).default;
mountRef.current = mount;

// ---------------------------------------------------------------------------
console.log("A. slash-shaped shipment identity → one encoded segment → real lot");
{
  const ID = "LO/LEGACY/001"; // synthetic, non-sensitive specimen
  const ENCODED = "/lo-hang/LO%2FLEGACY%2F001";
  const { identity, links, containers } = await openLotByIdentity(ID);

  assert.equal(identity.getAttribute("href"), ENCODED, "identity link must carry ONE encoded segment");
  assert.equal(containers.length, 2, "the specimen appears in both the desktop row and the mobile card");
  assert.ok(links.length >= 5, `expected identity + XỬ LÝ + 360° in both layouts, got ${links.length}`);
  for (const a of links) {
    // The PATH is one encoded segment; a backend-composed route may append its
    // query AFTER it (`…%2F001?tab=nhap`) — the query must never be inside it.
    const linkPath = (a.getAttribute("href") || "").split(/[?#]/, 1)[0];
    assert.equal(linkPath, ENCODED, `every shipment detail link must be one encoded segment (got ${a.getAttribute("href")})`);
  }

  await clickEl(identity);
  assert.ok(!byTestId("not-found"), "slash identity must NOT reach the App wildcard");
  assert.ok(!mainText().includes("Không tìm thấy màn hình"), "no invalid-route screen");
  assert.equal(h1(), ID, "the exact identity resolves on the real lot page");
  assert.ok(window.document.getElementById("workspace-tabs"), "real ShipmentDetail rendered");
  ok(`${ID} → 360°/identity link → real ShipmentDetail (never wildcard)`);

  // Backend-composed deep link (repaired payload shape): the tab must survive.
  invoke(stateWith(ID));
  await tick(120);
  await goto("Lô Hàng");
  const handle = $("main a").find((a) => text(a).includes("XỬ LÝ") && !text(a).includes("360"));
  assert.ok(handle, "XỬ LÝ deep-link present");
  assert.equal(handle.getAttribute("href"), `${ENCODED}?tab=nhap`, "composed backend route keeps query AFTER the encoded segment");
  await clickEl(handle);
  assert.ok(!byTestId("not-found"), "composed encoded route must not hit the wildcard");
  assert.equal(h1(), ID, "deep-linked lot resolved");
  const active = $("button", window.document.getElementById("workspace-tabs")).find((b) =>
    b.className.includes("bg-[#0f2a4a]")
  );
  assert.ok(active && text(active).includes("Nhập khẩu"), `requested tab active (${active ? text(active) : "none"})`);
  ok("encoded backend deep-link keeps its tab and opens the lot");

  // Global search (desktop + mobile result lists share the same handler).
  invoke(stateWith(ID));
  await tick(120);
  const search = mainInput("Tìm mã lô");
  search.dispatchEvent(new window.Event("focus", { bubbles: false }));
  search.dispatchEvent(new window.Event("focusin", { bubbles: true }));
  typeInto(search, ID);
  await tick(120);
  const result = $("button").find((b) => text(b).includes(ID) && text(b).includes("Lô hàng —"));
  assert.ok(result, "shipment result appears in global search");
  await clickEl(result);
  assert.ok(!byTestId("not-found"), "global search must not land on the wildcard");
  assert.equal(h1(), ID, "global search opens the exact lot");
  ok("global search reel → exact slash lot (never wildcard)");
}

// ---------------------------------------------------------------------------
console.log("B. identity edge classes: literal %2F, ? and #");
{
  for (const [ID, ENCODED] of [
    ["A%2FB", "/lo-hang/A%252FB"], // literal uppercase %2F — the class the router param collapses
    ["A%2fB", "/lo-hang/A%252fB"], // lowercase survives the param path too; both must be exact
    ["A%20B", "/lo-hang/A%2520B"], // literal %20 must decode to itself, never to a space
    ["A%25B", "/lo-hang/A%2525B"], // literal %25 must decode to itself, never to "%"
    ["A?B", "/lo-hang/A%3FB"],
    ["A#B", "/lo-hang/A%23B"],
  ]) {
    const { identity } = await openLotByIdentity(ID);
    assert.equal(identity.getAttribute("href"), ENCODED, `${ID} encoded route`);
    await clickEl(identity);
    assert.ok(!byTestId("not-found"), `${ID} must not reach the wildcard`);
    assert.equal(h1(), ID, `${ID} resolves to the EXACT identity`);
  }
  ok('literal "%2F"/"%20"/"%25" stay literal (exactly one decode); "?" and "#" cannot inject syntax');
}

// ---------------------------------------------------------------------------
console.log("C. unchanged identities keep their existing one-segment route");
{
  const cases = [
    ["LO-0306", "/lo-hang/LO-0306"], // ordinary
    ["108313713320", "/lo-hang/108313713320"], // canonical decimal string (Issue #117 identity)
    ["LÔ-0307", "/lo-hang/L%C3%94-0307"], // unicode
  ];
  for (const [ID, ENCODED] of cases) {
    const { identity } = await openLotByIdentity(ID);
    assert.equal(identity.getAttribute("href"), ENCODED, `${ID} route byte-identical`);
    await clickEl(identity);
    assert.equal(h1(), ID, `${ID} opens the exact lot`);
    assert.ok(!byTestId("not-found"), `${ID} must not reach the wildcard`);
  }
  ok("ordinary LO-xxxx, decimal-string 108313713320 and unicode LÔ-xxxx behave as before");
}

// ---------------------------------------------------------------------------
console.log("D. a stale backend-composed multi-segment route still shows the truthful wildcard");
{
  const state = structuredClone(FIX.success);
  state.shipments[0].id = "STALE/ROUTE";
  state.shipments[0].nextRoute = "/lo-hang/STALE/ROUTE?tab=nhap"; // pre-fix backend shape
  invoke(state);
  await tick(120);
  await goto("Lô Hàng");
  const handle = $("main a").find((a) => text(a).includes("XỬ LÝ") && !text(a).includes("360"));
  await clickEl(handle);
  assert.ok(byTestId("not-found"), "stale multi-segment backend route must reach the wildcard");
  for (const target of ["/", "/hop-dong", "/lo-hang"]) {
    assert.ok(
      $('[data-testid="not-found"] a').some((a) => a.getAttribute("href") === target),
      `safe destination ${target} offered`
    );
  }
  // …while the app-built link for the SAME lot is already correct.
  invoke(state);
  await tick(120);
  await goto("Lô Hàng");
  const identity = $("main a").find((a) => text(a) === "STALE/ROUTE");
  assert.equal(identity.getAttribute("href"), "/lo-hang/STALE%2FROUTE", "app-built link is encoded");
  ok("stale backend string → truthful NotFound (three safe destinations); app link encoded");
}

if (lastInvokeCleanup) lastInvokeCleanup();
console.log(`PASS shipment slash-id specimen (${passed} groups)`);
process.exit(0);
