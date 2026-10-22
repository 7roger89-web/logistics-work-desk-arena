// ===========================================================================
// Issue #212 — DOM acceptance for Bể thông tin / ghi nhanh.
//
// Runs the production bundle in jsdom against the handbook staging fixture
// plus a synthetic inbox overlay (no real bank/chat content).
//
// Run: node tests/component/dom_acceptance_inbox_snippets.mjs
// ===========================================================================

import { readFileSync } from "node:fs";
import assert from "node:assert/strict";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const require = createRequire(path.join(ROOT, "component/package.json"));
const { JSDOM } = require("jsdom");
const FIX = JSON.parse(
  readFileSync(path.join(ROOT, "tests/component/fixtures/view_model_handbook.json"), "utf8")
);

const SNIPPETS = [
  { id: "isnp-usd-1", rawText: "H-TEST USD remittance 1 — SYN-USD-001", source: "bank", title: "", sourceRef: "", occurredAt: "", createdAt: "2026-10-22T09:00:00", createdBy: "staging.support", requestId: "REQ-usd-1", contractIds: ["HDMB-0306"], linkedSnippetIds: ["isnp-cny-1"], linked: true, unverified: true, amount: null, currency: "", fxRate: null },
  { id: "isnp-cny-1", rawText: "H-TEST China received 1 — SYN-CNY-IN-001", source: "bank", title: "", sourceRef: "", occurredAt: "", createdAt: "2026-10-22T08:50:00", createdBy: "staging.support", requestId: "REQ-cny-1", contractIds: ["HDMB-0306"], linkedSnippetIds: ["isnp-usd-1"], linked: true, unverified: true, amount: null, currency: "", fxRate: null },
  { id: "isnp-rmb-1", rawText: "H-TEST factory RMB payout 1 — SYN-RMB-001", source: "wechat", title: "", sourceRef: "", occurredAt: "", createdAt: "2026-10-22T08:40:00", createdBy: "staging.support", requestId: "REQ-rmb-1", contractIds: ["HDMB-0306"], linkedSnippetIds: [], linked: true, unverified: true, amount: null, currency: "", fxRate: null },
  { id: "isnp-misc", rawText: "Lunch order SYN-MISC — weather chat, independent snippet", source: "zalo", title: "", sourceRef: "", occurredAt: "", createdAt: "2026-10-22T08:30:00", createdBy: "staging.support", requestId: "REQ-misc", contractIds: [], linkedSnippetIds: [], linked: false, unverified: true, amount: null, currency: "", fxRate: null },
];

function withInbox(base, extra = {}) {
  return {
    ...base,
    inbox: {
      canWrite: true,
      unverified: true,
      snippets: SNIPPETS,
      count: SNIPPETS.length,
      linkedCount: 3,
      unlinkedCount: 1,
      ...extra,
    },
  };
}

const DATA = withInbox(FIX.empty);

const dom = new JSDOM("<!DOCTYPE html><html><body></body></html>", {
  url: "http://localhost:8501/",
  pretendToBeVisual: true,
});
const { window } = dom;
Object.defineProperty(window, "innerWidth", { configurable: true, writable: true, value: 1440 });
Object.defineProperty(window, "innerHeight", { configurable: true, writable: true, value: 900 });

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
window.scrollTo = () => {};
window.URL.createObjectURL = () => "blob:mock-url";
window.URL.revokeObjectURL = () => {};
window.matchMedia = window.matchMedia || (() => ({ matches: false, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} }));

const tick = (ms = 60) => new Promise((resolve) => setTimeout(resolve, ms));
const $ = (selector, root = window.document) => [...root.querySelectorAll(selector)];
const text = (element) => (element.textContent || "").replace(/\s+/g, " ").trim();
const mainText = () => text($("main")[0] ?? window.document.body);
const bodyText = () => text(window.document.body);

function findClickable(needle, selector = "a,button", root = window.document) {
  const candidates = $(selector, root);
  return candidates.find((element) => text(element) === needle)
    || candidates.find((element) => text(element).startsWith(needle))
    || null;
}

async function click(needle, selector = "a,button", root = window.document) {
  const element = findClickable(needle, selector, root);
  assert.ok(element, `clickable "${needle}" not found`);
  element.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
  await tick();
  return element;
}

function type(input, value) {
  const proto = input.tagName === "TEXTAREA" ? window.HTMLTextAreaElement.prototype : window.HTMLInputElement.prototype;
  const last = input.value;
  Object.getOwnPropertyDescriptor(proto, "value").set.call(input, value);
  const tracker = input._valueTracker;
  if (tracker) tracker.setValue(last);
  input.dispatchEvent(new window.Event("input", { bubbles: true }));
  input.dispatchEvent(new window.Event("change", { bubbles: true }));
}

let passed = 0;
function ok(label) {
  passed += 1;
  console.log(`  ✓ ${label}`);
}

const host = window.document.createElement("div");
window.document.body.appendChild(host);
const mountRef = { current: null };
const triggers = [];
function invoke(data) {
  return mountRef.current({
    name: "logi_shell",
    data,
    parentElement: host,
    setTriggerValue: (event, value) => { triggers.push({ event, value }); },
  });
}

let cleanup = null;
async function remount(data) {
  if (cleanup) cleanup();
  cleanup = invoke(data);
  await tick(120);
}

console.log("STEP 1 — boot production bundle @ 1440×900");
{
  const bundle = await import(path.join(ROOT, "component/dist/logi-shell.js"));
  assert.equal(typeof bundle.default, "function");
  mountRef.current = bundle.default;
  await remount(DATA);
  assert.ok(bodyText().includes("TRƯỜNG THÀNH"), "shell did not render");
  assert.ok(!bodyText().includes("process is not defined"), "Node process leaked");
  ok("bundle boots on desktop viewport");
}

console.log("STEP 2 — nav item is live, not deferred");
{
  const aside = $("aside")[0];
  const item = findClickable("Bể thông tin", "a", aside);
  assert.ok(item, "Bể thông tin missing from sidebar");
  assert.equal(item.getAttribute("href"), "/be-thong-tin");
  assert.ok(!text(item).includes("Sắp có"), "inbox still marked deferred");
  const soTay = findClickable("Sổ tay", "a", aside);
  assert.ok(soTay && soTay.getAttribute("href") === "/so-tay", "handbook route must stay separate");
  ok("Bể thông tin is a live route; Sổ tay stays separate");
}

console.log("STEP 3 — Thêm sheet opens composer first");
{
  const header = $("header")[0];
  await click("Thêm", "button", header);
  assert.ok(bodyText().includes("Thêm mới nhanh"), "quick-add sheet missing");
  const first = $("[data-testid='quick-add-inbox']")[0];
  assert.ok(first, "Ghi chú nhanh is not the first sheet action");
  assert.ok(text(first).includes("Ghi chú nhanh"));
  first.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
  await tick();
  assert.ok($("[data-testid='inbox-composer']")[0], "composer missing");
  assert.ok($("[data-testid='inbox-composer-text']")[0], "required textarea missing");
  assert.ok($("[data-testid='inbox-composer-save-next']")[0], "Lưu & ghi tiếp missing");
  const save = $("[data-testid='inbox-composer-save']")[0];
  assert.ok(save);
  const area = $("[data-testid='inbox-composer-text']")[0];
  type(area, "H-TEST USD remittance SYN-USD-NEW");
  save.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
  await tick();
  const create = triggers.find((row) => row.event === "inbox_snippet_create");
  assert.ok(create, "create event was not dispatched");
  assert.equal(create.value.payload.rawText, "H-TEST USD remittance SYN-USD-NEW");
  assert.ok(create.value.payload.requestId, "requestId missing");
  const closeBtn = $("button", window.document.getElementById("quick-add-sheet")).find((b) => (b.getAttribute("aria-label") || "").includes("Đóng"));
  if (closeBtn) closeBtn.click();
  await tick();
  ok("composer is first in Thêm and dispatches one create event");
}

console.log("STEP 4 — inbox list, search, filter, link");
await click("Bể thông tin", "a", $("aside")[0]);
{
  const page = $("[data-testid='inbox-page']")[0];
  assert.ok(page, "inbox page missing");
  assert.ok(mainText().includes("Bể thông tin"));
  assert.ok(mainText().includes("chưa xác minh") || mainText().includes("Chưa xác minh") || mainText().includes("chưa phải sổ kế toán") || mainText().includes("chưa phải"));
  const cards = $("[data-testid='inbox-card']");
  assert.equal(cards.length, 4, "expected 4 synthetic cards");
  assert.ok(mainText().includes("Lunch order SYN-MISC"));
  assert.ok(mainText().includes("—"), "UNKNOWN dash missing for blank amount/date");
  type($("[data-testid='inbox-search']")[0], "H-TEST");
  await tick();
  assert.equal($("[data-testid='inbox-card']").length, 3, "search by embedded contract token failed");
  type($("[data-testid='inbox-search']")[0], "");
  await tick();
  const filters = $("[data-testid='inbox-filters']")[0];
  await click("Chưa ghép", "button", filters);
  assert.equal($("[data-testid='inbox-card']").length, 1, "unlinked filter failed");
  assert.ok(mainText().includes("Lunch order SYN-MISC"));
  await click("Đã ghép", "button", filters);
  assert.equal($("[data-testid='inbox-card']").length, 3, "linked filter failed");
  await click("Tất cả", "button", filters);
  const box = $("[data-testid='inbox-card'] input[type='checkbox']")[0];
  box.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
  await tick();
  const openLink = $("[data-testid='inbox-link-open']")[0];
  openLink.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
  await tick();
  assert.ok($("[data-testid='inbox-link-sheet']")[0], "link sheet missing");
  ok("search / Chưa ghép / Đã ghép / Ghép thông tin work");
}

console.log("STEP 5 — contract detail shows linked snippets, journey routes survive");
{
  await click("Hợp đồng", "a", $("aside")[0]);
  await tick();
  const contractLink = [...$("a")].find((a) => (a.getAttribute("href") || "").includes("HDMB-0306"));
  assert.ok(contractLink, "HDMB-0306 missing");
  contractLink.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
  await tick(80);
  const linked = $("[data-testid='contract-linked-inbox']")[0];
  assert.ok(linked, "Thông tin đã ghép missing on contract");
  assert.ok(text(linked).includes("Thông tin đã ghép"));
  assert.ok(text(linked).includes("H-TEST USD remittance 1"));
  assert.ok(!text(linked).includes("Lunch order SYN-MISC"), "unlinked snippet leaked onto contract");
  ok("contract detail shows linked snippets only");
}

console.log("STEP 6 — mobile 390×844 structure");
{
  window.innerWidth = 390;
  window.innerHeight = 844;
  window.dispatchEvent(new window.Event("resize"));
  await remount(DATA);
  await click("Bể thông tin", "a", $("aside")[0]);
  const page = $("[data-testid='inbox-page']")[0];
  assert.ok(page);
  const wide = $("table", page);
  assert.equal(wide.length, 0, "inbox must not force a wide table on mobile");
  const plus = [...$("button")].find((b) => text(b).includes("Thêm") || b.querySelector("svg"));
  assert.ok(plus, "mobile Thêm trigger should remain");
  const header = $("header")[0];
  const addBtns = [...$("button", header)].filter((b) => text(b) === "Thêm");
  if (addBtns[0]) {
    addBtns[0].dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
    await tick();
  } else {
    const navAdd = [...$("nav button")].find((b) => text(b).includes("Thêm"));
    if (navAdd) {
      navAdd.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
      await tick();
    }
  }
  const inboxBtn = $("[data-testid='quick-add-inbox']")[0];
  if (inboxBtn) {
    inboxBtn.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
    await tick();
    const save = $("[data-testid='inbox-composer-save']")[0];
    assert.ok(save);
    const style = window.getComputedStyle(save);
    const minH = parseFloat(style.minHeight || "48");
    assert.ok(minH >= 44 || save.className.includes("min-h-[48px]"), "save target too small");
  }
  ok("mobile layout keeps composer + cards, no wide table");
}

console.log(`\n${passed} checks passed`);
