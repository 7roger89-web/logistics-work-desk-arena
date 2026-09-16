// ============================================================================
// LOGI_USER_ACCESS_WORKSPACE_01 — DOM acceptance for /nguoi-dung.
//
// Runs the real production bundle in jsdom against a fixture emitted by the
// isolated-staging view-model (scripts/gen_user_access_fixture.py). It proves:
//   1. the route is activated, "Sắp có" is gone from the whole navigation
//      (this was the last deferred destination) and no second user route
//      appeared;
//   2. accounts render as readable cards with canonical identity, role and
//      real active/inactive status — and NOTHING credential-shaped (no hash,
//      no token, no passphrases) reaches the DOM;
//   3. an empty user store renders an honest empty state while the canonical
//      permission matrix still renders;
//   4. the permission matrix is the canonical ROLE_PERMISSIONS verbatim
//      (admin wildcard, support's real permission set, legacy roles labelled);
//   5. the current-user indicator and the honest Local Admin auth-mode note
//      render;
//   6. mobile structure: cards wrap instead of forcing a wide table, no
//      horizontal-scroll containers, no <table> on this page at all;
//   7. neighbouring routes are untouched.
//
// Run: node tests/component/dom_acceptance_user_access.mjs
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
  readFileSync(path.join(ROOT, "tests/component/fixtures/view_model_user_access.json"), "utf8")
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
  await click("Người dùng & Vai trò", "aside a", window.document);
}

const accounts = () => $("[data-testid='user-access-account']");
const roleRows = () => $("[data-testid='user-access-role-row']");

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

console.log("STEP 2 — /nguoi-dung is a live route; the last deferred marker is gone");
{
  const aside = $("aside")[0];
  const usersNav = findClickable("Người dùng & Vai trò", "a", aside);
  assert.ok(usersNav, "Người dùng & Vai trò sidebar item missing");
  assert.equal(usersNav.getAttribute("href"), "/nguoi-dung", "route changed instead of activated");
  assert.ok(!text(usersNav).includes("Sắp có"), "/nguoi-dung still marked deferred");
  const markers = $("aside a", window.document).filter((el) => text(el).includes("Sắp có"));
  assert.equal(markers.length, 0, "a navigation item is still marked deferred");
  ok("the last deferred destination is now a real route");
}

console.log("STEP 3 — the page is honestly read-only with its scope stated");
{
  await click("Người dùng & Vai trò", "aside a");
  const rendered = mainText();
  assert.ok(!rendered.includes("Sắp có — chưa triển khai"), "route fell through to placeholder");
  assert.ok(rendered.includes("Người dùng & Vai trò"), "workspace heading missing");
  assert.ok(rendered.includes("CHỈ ĐỌC"), "read-only marker missing");
  assert.ok(rendered.includes("Trang này không có"), "scope-limit disclosure missing");
  assert.ok(rendered.includes("Local Admin"), "Local Admin auth-mode truth missing");
  assert.ok(!rendered.includes("dữ liệu mẫu"), "sample-data wording leaked in");
  ok("/nguoi-dung renders the real workspace, declaring its own limits");
}

console.log("STEP 4 — empty user store: honest empty state, matrix still canonical");
{
  assert.equal(accounts().length, 0, "accounts appeared from an empty store");
  const empty = $("[data-testid='user-access-empty']")[0];
  assert.ok(empty, "honest empty state missing");
  assert.ok(text(empty).includes("không tự bịa"), "empty state does not state its honesty");
  assert.equal(roleRows().length, 7, "canonical matrix missing roles on empty store");
  ok("no fabricated user; the canonical matrix still renders");
}

console.log("STEP 5 — journey: real accounts render as cards with role and status");
{
  await remount(JOURNEY);
  const cards = accounts();
  assert.equal(cards.length, 3, `expected 3 account cards, got ${cards.length}`);

  const byUser = (username) => cards.find((card) => card.getAttribute("data-username") === username);
  const hang = byUser("thu-hang");
  assert.ok(hang, "thu-hang card missing");
  assert.equal(hang.getAttribute("data-role"), "support");
  assert.ok(text(hang).includes("Thu Hằng"), "display name missing");
  assert.ok(text(hang).includes("Điều phối"), "canonical support role label missing");
  assert.ok(text(hang).includes("Hoạt động"), "active status missing");
  assert.ok(text(hang).includes("thu-hang"), "login identifier missing");
  assert.ok(text(hang).includes("ID: "), "account identifier missing");

  const locked = byUser("lan-viewer");
  assert.ok(locked, "lan-viewer card missing");
  assert.ok(text(locked).includes("Đã vô hiệu hóa"), "inactive status missing");
  assert.ok(locked.querySelector("[data-testid='user-access-account-inactive']"), "inactive marker missing");

  const tu = byUser("minh-tu");
  assert.ok(text(tu).includes("Kinh doanh"), "canonical sale role label missing");

  ok("identity, canonical role and real account status render as cards");
}

console.log("STEP 6 — no credential material anywhere in the rendered DOM");
{
  const rendered = bodyText();
  for (const marker of ["pbkdf2_sha256$", "staging-only-passphrase", "sha256:"]) {
    assert.ok(!rendered.includes(marker), `secret material ${marker} leaked into the DOM`);
  }
  // No form/input exists on this page at all: it cannot even ask for a secret.
  assert.equal($("main input", window.document).length, 0, "unexpected input on a read-only page");
  assert.equal($("main form", window.document).length, 0, "unexpected form on a read-only page");
  // No action button that could imply user management.
  for (const label of ["Tạo tài khoản", "Xóa", "Đổi mật khẩu", "Khóa", "Gán vai trò", "Reset"]) {
    assert.equal(
      findClickable(label, "main button, main a"),
      null,
      `unexpected user-management action "${label}"`
    );
  }
  ok("no hash, token or passphrase; no write control exists on the page");
}

console.log("STEP 7 — the permission matrix is the canonical truth, verbatim");
{
  const admin = roleRows().find((row) => row.getAttribute("data-role") === "admin");
  assert.ok(admin, "admin row missing");
  assert.ok(text(admin).includes("* = toàn quyền"), "admin wildcard not surfaced as such");
  assert.ok(
    !admin.querySelector("[data-testid='user-access-permission']"),
    "admin must not render '*' as a permission name"
  );

  const support = roleRows().find((row) => row.getAttribute("data-role") === "support");
  assert.ok(support, "support row missing");
  const supportPerms = $("[data-testid='user-access-permission']", support).map((el) => text(el));
  assert.ok(supportPerms.includes("finance_write"), "canonical support finance_write missing");
  assert.ok(supportPerms.includes("operations_write"), "canonical support operations_write missing");
  assert.ok(!supportPerms.includes("*"), "wildcard leaked into a non-admin role");
  assert.equal(supportPerms.length, 22, "support permission set changed");

  const viewer = roleRows().find((row) => row.getAttribute("data-role") === "viewer");
  assert.ok(text(viewer).includes("vai trò tương thích cũ"), "legacy role not labelled honestly");
  const sale = roleRows().find((row) => row.getAttribute("data-role") === "sale");
  assert.ok(text(sale).includes("vai trò gán được"), "assignable role not labelled");

  ok("admin wildcard, canonical support set and legacy labels are exact");
}

console.log("STEP 8 — current-user indicator and honest auth-mode note");
{
  const current = $("[data-testid='user-access-current']")[0];
  assert.ok(current, "current-user indicator missing");
  assert.ok(text(current).includes("thu-hang"), "session username missing");
  assert.ok(text(current).includes("Thu Hằng"), "session display name missing");
  assert.ok(text(current).includes("quyền"), "permission indicator missing");

  const note = text($("[data-testid='user-access-mode-note']")[0]);
  assert.ok(note.includes("Local Admin"), "auth-mode label missing");
  assert.ok(note.includes("KHÔNG phải đăng nhập đa người dùng"), "Local Admin not kept honest");

  const counts = text($("[data-testid='user-access-counts']")[0]);
  assert.ok(counts.includes("3 tài khoản"), "account count missing");
  ok("who-is-looking and which auth mode the app really runs are stated");
}

console.log("STEP 9 — mobile structure: cards, no wide table, no horizontal scroll");
{
  for (const card of accounts()) {
    assert.ok(
      card.className.includes("w-full") && card.className.includes("min-w-0"),
      "account card can overflow narrow viewports"
    );
  }
  for (const row of roleRows()) {
    assert.ok(
      row.className.includes("w-full") && row.className.includes("min-w-0"),
      "role row can overflow narrow viewports"
    );
    const chips = $("[data-testid='user-access-role-permissions']", row)[0];
    assert.ok(chips.className.includes("flex-wrap"), "permission chips force a wide row");
  }
  assert.equal($("main table", window.document).length, 0, "a wide table is used where cards suffice");
  assert.equal(
    $("main [class*='overflow-x-auto']", window.document).length,
    0,
    "workspace content requires horizontal scrolling"
  );
  ok("accounts and permissions stay phone-readable without any wide table");
}

console.log("STEP 10 — neighbouring routes are untouched");
{
  const aside = $("aside")[0];
  await click("Báo cáo CEO", "a", aside);
  assert.ok(mainText().includes("Báo cáo CEO"), "CEO report route disturbed");
  await click("Đối soát", "a", aside);
  assert.ok(mainText().includes("Đối soát"), "reconciliation route disturbed");
  await click("Sổ tay", "a", aside);
  assert.ok(mainText().includes("Sổ tay vận hành"), "handbook route disturbed");
  await click("Dịch thuật", "a", aside);
  assert.ok(mainText().includes("Dịch thuật"), "translation route disturbed");
  await click("Người dùng & Vai trò", "a", aside);
  assert.ok(mainText().includes("Người dùng & Vai trò"), "user access did not come back");
  ok("/bao-cao-ceo, /tai-chinh/doi-soat, /so-tay and /dich-thuat still render");
}

if (cleanup) cleanup();
console.log(`USER ACCESS DOM ACCEPTANCE PASS — ${passed} checks`);
