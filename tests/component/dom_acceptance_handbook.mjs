// ============================================================================
// LOGI_NOTEBOOK_WORKSPACE_01 — DOM acceptance for the /so-tay handbook.
//
// Runs the real production bundle in jsdom against a fixture emitted by the
// isolated-staging view-model (scripts/gen_handbook_fixture.py). It proves:
//   1. the existing route is activated and "Sắp có" is gone for Sổ tay only —
//      the remaining deferred destination keeps its honest marker;
//   2. static reference rows render exactly as the canonical sources hold them;
//   3. category selection and the plain text filter behave (search + no-result);
//   4. an article opens with real provenance and an explicit way back;
//   5. an empty note corpus stays empty — no fabricated article appears, while
//      notes written through the existing notebook reader pass their own
//      recorded date/category/tags through;
//   6. mobile structure: no table forces horizontal scrolling, touch targets
//      stay sized, neighbouring routes are untouched.
//
// Run: node tests/component/dom_acceptance_handbook.mjs
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
  readFileSync(path.join(ROOT, "tests/component/fixtures/view_model_handbook.json"), "utf8")
);
const EMPTY = FIX.empty;
const JOURNEY = FIX.journey;

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
  /* keep node's built-in navigator */
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
  Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set.call(input, value);
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
function invoke(data) {
  return mountRef.current({
    name: "logi_shell",
    data,
    parentElement: host,
    setTriggerValue: () => {},
  });
}

let cleanup = null;
async function remount(data) {
  if (cleanup) cleanup();
  cleanup = invoke(data);
  await tick(120);
  await click("Sổ tay", "aside a", window.document);
}

const chip = (name) => $(`[data-testid='handbook-categories'] button`).find(
  (element) => text(element).startsWith(name)
);
const cards = () => $("[data-testid='handbook-entry']");

console.log("STEP 1 — boot the production bundle on staging data");
{
  const bundle = await import(path.join(ROOT, "component/dist/logi-shell.js"));
  assert.equal(typeof bundle.default, "function");
  mountRef.current = bundle.default;
  cleanup = invoke(EMPTY);
  await tick(120);
  const rendered = bodyText();
  assert.ok(!rendered.includes("process is not defined"), "Node process leaked into browser bundle");
  assert.ok(!rendered.includes("BidiComponent Error"), "component mount failed");
  assert.ok(rendered.includes("TRƯỜNG THÀNH"), "shell did not render");
  ok("production bundle boots cleanly");
}

console.log("STEP 2 — Sổ tay is a live route; the remaining deferred route stays marked");
{
  const aside = $("aside")[0];
  const noteNav = findClickable("Sổ tay", "a", aside);
  assert.ok(noteNav, "Sổ tay sidebar item missing");
  assert.equal(noteNav.getAttribute("href"), "/so-tay", "route changed instead of activated");
  assert.ok(!text(noteNav).includes("Sắp có"), "Sổ tay still marked deferred");
  // LOGI_USER_ACCESS_WORKSPACE_01 — /nguoi-dung is a real read-only workspace
  // now, so the marker is gone there too and no destination stays deferred.
  const users = findClickable("Người dùng & Vai trò", "a", aside);
  assert.ok(users, "user-access sidebar item missing");
  assert.equal(users.getAttribute("href"), "/nguoi-dung", "user-access route changed");
  assert.ok(!text(users).includes("Sắp có"), "user access still marked deferred");
  const markers = $("aside a", window.document).filter((el) => text(el).includes("Sắp có"));
  assert.equal(markers.length, 0, "a navigation item is still marked deferred");
  ok("real destinations carry no deferred marker — and none is left");
}

console.log("STEP 3 — the placeholder is gone and the page is honestly read-only");
await click("Sổ tay", "aside a");
{
  const rendered = mainText();
  assert.ok(!rendered.includes("Sắp có — chưa triển khai"), "route fell through to placeholder");
  assert.ok(rendered.includes("Sổ tay vận hành"), "handbook heading missing");
  assert.ok(rendered.includes("CHỈ ĐỌC"), "read-only marker missing");
  assert.ok(rendered.includes("5/6 mục có nội dung"), "honest availability count missing");
  assert.ok(rendered.includes("Trang này không có"), "scope-limit disclosure missing");
  assert.ok(!rendered.includes("dữ liệu mẫu"), "sample-data wording leaked in");
  ok("/so-tay renders the real handbook, declaring its own limits");
}

console.log("STEP 4 — displayed rows are the canonical source values");
{
  // The list previews the first rows; every remaining value is verified by
  // opening each article, so the assertion covers all the page can show.
  const collected = [mainText()];
  const total = cards().length;
  assert.ok(total >= 9, `fewer articles than the source material provides: ${total}`);
  for (let index = 0; index < total; index += 1) {
    const card = cards()[index];
    card.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
    await tick();
    const article = $("[data-testid='handbook-article']")[0];
    assert.ok(article, `article ${index} did not open`);
    assert.equal(
      $("[data-testid='handbook-provenance']", article).length,
      1,
      `article ${index} opened without provenance`
    );
    collected.push(text(article));
    await click("Về danh mục", "button");
  }
  const rendered = collected.join(" ");
  for (const needle of [
    "Chờ chứng từ",          // core.config STATUS_MAP_FWD
    "Đang thông quan/Giao hàng",
    "NKOF40",                // core.config GETFLY_SERVICES_LIST
    "Cước vận tải biển quốc tế hàng NK cont 40",
    "DAP",                   // core.config INCOTERMS
    "Maersk",                // core.config CARRIER_LINKS
    "https://www.maersk.com/tracking/{ref}",
    "Số tờ khai nhập khẩu",   // views.logi_real_data.document_checklist
    "Hợp đồng nguyên tắc",    // core.docgen.rules
    "Vietnam Customs",        // trade_compliance source registry
    "NOT_RETRIEVED",
    "admin",                  // core.auth ROLE_PERMISSIONS
  ]) {
    assert.ok(rendered.includes(needle), `source value not rendered: ${needle}`);
  }
  // Nothing here is a legal/customs rule asserted by the page itself.
  assert.ok(!rendered.includes("mức phạt"), "handbook invented a penalty rule");
  ok("status, service-code, Incoterm, docgen, source and RBAC rows pass through");
}

console.log("STEP 5 — category control narrows the list and reveals section provenance");
{
  const before = cards().length;
  await click("Chứng từ", "button", $(`[data-testid='handbook-categories']`)[0]);
  const after = cards().length;
  assert.ok(after > 0 && after < before, `category filter did not narrow ${before} → ${after}`);
  for (const card of cards()) {
    assert.ok(text(card).includes("Chứng từ"), "a card from another category stayed listed");
  }
  assert.ok(mainText().includes("views/logi_real_data.py"), "section provenance missing");
  await click("Tất cả", "button", $(`[data-testid='handbook-categories']`)[0]);
  assert.equal(cards().length, before, "reset did not restore the full list");
  ok("category chips filter the list and carry the section source");
}

console.log("STEP 6 — plain text search works and says so when nothing matches");
{
  const input = $("[data-testid='handbook-search']")[0];
  assert.ok(input, "search input missing");
  type(input, "tờ khai");
  await tick();
  assert.ok(cards().length > 0, "search for an existing term found nothing");
  assert.ok(cards().every((card) => text(card).toLowerCase().includes("tờ khai")
    || text(card).includes("Bốn mục kiểm tra")), "search returned unrelated rows");

  type(input, "zzzz-khong-ton-tai");
  await tick();
  assert.equal(cards().length, 0, "nonsense query still returned rows");
  assert.ok($("[data-testid='handbook-no-result']")[0], "no-result state missing");
  assert.ok(mainText().includes("không tạo bài mới"), "empty result is not explicitly honest");

  type(input, "");
  await tick();
  assert.ok(cards().length > 0, "clearing the query did not restore the list");
  ok("search filters the delivered text and never invents a result");
}

console.log("STEP 7 — an article opens with provenance and an explicit way back");
{
  await click("Bốn trạng thái lô hàng", "button", $("main")[0]);
  const article = $("[data-testid='handbook-article']")[0];
  assert.ok(article, "article did not open");
  assert.ok(mainText().includes("core/config.py"), "article provenance missing");
  assert.ok(mainText().includes("không có trong nguồn"), "absent provenance not stated honestly");
  assert.ok($("[data-testid='handbook-provenance']")[0], "provenance block missing");
  const back = $("[data-testid='handbook-back']")[0];
  assert.ok(back && text(back).includes("Về danh mục"), "back-to-list action missing");
  assert.ok(back.className.includes("touch-target"), "back action is not touch sized");
  assert.equal($("a[href='/viec-can-xu-ly']", article).length, 1, "article lost its link to the owning desk");
  await click("Về danh mục", "button");
  assert.ok(!$("[data-testid='handbook-article']")[0], "back did not return to the list");
  ok("article open/back behaves and shows only real provenance");
}

console.log("STEP 8 — empty note corpus stays empty; no fabricated article appears");
{
  const rail = $("[data-testid='handbook-empty-sections']")[0];
  assert.ok(rail, "empty-section disclosure missing");
  const railText = text(rail);
  assert.ok(railText.includes("Ghi chú đội ngũ"), "notes section not named in the disclosure");
  assert.ok(railText.includes("chưa có ghi chú nào"), "notes empty state is not explicit");
  for (const needle of ["bill gốc", "phân luồng", "Luồng vàng"]) {
    assert.ok(!mainText().includes(needle), `fixture-only note text leaked into the empty state: ${needle}`);
  }
  ok("an empty work-notes source is reported as empty");
}

console.log("STEP 9 — real notes pass through with their own recorded metadata");
await remount(JOURNEY);
{
  const rendered = mainText();
  assert.ok(rendered.includes("2 ghi chú đội ngũ"), "note count chip not updated");
  assert.ok(rendered.includes("Hàng nhập cần bill gốc trước khi giao"), "note title missing");
  assert.ok(rendered.includes("Khách yêu cầu bản gốc tại cảng"), "note body missing");
  await click("Hàng nhập cần bill gốc", "button", $("main")[0]);
  const article = $("[data-testid='handbook-article']")[0];
  assert.ok(article, "note article did not open");
  const articleText = text(article);
  assert.ok(articleText.includes("04/09/2026 09:12"), "recorded update date not passed through");
  assert.ok(articleText.includes("📄 Chứng Từ (Docs)"), "recorded category not passed through");
  assert.ok(articleText.includes("#bill gốc"), "recorded tags not passed through");
  assert.ok(articleText.includes("knowledge_base"), "note provenance source missing");
  assert.ok(articleText.includes("nội dung người dùng"), "note provenance caveat missing");
  ok("work notes keep the date, category, tags and source recorded with them");
}

console.log("STEP 10 — mobile structure: stacked rows, sized targets, no horizontal scroll");
{
  // Back to the list first: cards are only listed outside the article view.
  await click("Về danh mục", "button");
  assert.ok(cards().length > 0, "no cards after returning to the list");
  for (const card of cards()) {
    assert.ok(
      card.className.includes("w-full") && card.className.includes("min-w-0"),
      "card can overflow narrow viewports"
    );
  }
  // Open an entry that DOES carry a table, then check both responsive blocks.
  await click("Bốn trạng thái lô hàng", "button", $("main")[0]);
  const mobileRows = $("[data-testid='handbook-row-mobile']");
  assert.ok(mobileRows.length > 0, "no mobile row block");
  const mobileBlock = mobileRows[0].parentElement;
  assert.ok(mobileBlock.className.includes("md:hidden"), "mobile block is not narrow-viewport only");
  for (const table of $("main table")) {
    assert.ok(
      table.className.includes("hidden") && table.className.includes("md:table"),
      "a desktop table is visible at narrow width"
    );
  }
  assert.equal(
    $("main [class*='overflow-x-auto']").length,
    0,
    "handbook content requires horizontal scrolling"
  );
  assert.ok($("[data-testid='handbook-search']")[0].className.includes("min-h-[48px]"), "search is not thumb-sized");
  for (const element of $("[data-testid='handbook-categories'] button")) {
    assert.ok(element.className.includes("min-h-[44px]"), "category chip is not thumb-sized");
  }
  // Every cell's value node must be able to wrap: no truncation of long URLs.
  const valueNodes = $("[data-testid='handbook-row-mobile'] > div > *:last-child");
  assert.ok(valueNodes.length > 0, "mobile cells missing");
  for (const node of valueNodes) {
    assert.ok(
      node.className.includes("break-words") || node.className.includes("break-all"),
      "a mobile cell cannot wrap"
    );
  }
  ok("lists, chips, search and tables stay usable on a phone");
}

console.log("STEP 11 — neighbouring routes are untouched");
{
  const aside = $("aside")[0];
  await click("Báo cáo CEO", "a", aside);
  assert.ok(mainText().includes("Báo cáo CEO"), "CEO report route disturbed");
  await click("Đối soát", "a", aside);
  assert.ok(mainText().includes("Đối soát"), "reconciliation route disturbed");
  await click("Sổ tay", "a", aside);
  assert.ok(mainText().includes("Sổ tay vận hành"), "handbook did not come back");
  await click("Ngữ cảnh Đối tác", "a", aside);
  assert.ok(mainText().includes("Ngữ cảnh Đối tác"), "partner-context route disturbed");
  ok("/bao-cao-ceo, /tai-chinh/doi-soat and /ngu-canh-doi-tac still render");
}

if (cleanup) cleanup();
console.log(`HANDBOOK DOM ACCEPTANCE PASS — ${passed} checks`);
