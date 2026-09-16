// ============================================================================
// DOM acceptance — LOGI_USER_MANAGEMENT_01 (Admin write path for /nguoi-dung)
//
// Runs the REAL production bundle (component/dist/logi-shell.js) against the
// backend-generated fixture (scripts/gen_user_access_fixture.py — isolated
// mongomock staging through the canonical writers). Proves:
//
//   - a non-Admin session (journey) never sees ANY management control;
//   - an Admin session (journeyAdmin) sees "+ THÊM TÀI KHOẢN" and, per
//     account, "Đổi vai trò" / "Vô hiệu hóa"|"Kích hoạt lại" / "Đặt mật khẩu
//     mới" — and no delete control anywhere;
//   - CREATE: password/confirm mismatch blocks dispatch locally; a valid
//     submit dispatches exactly one `user_create` with a fresh requestId;
//   - backend REFUSAL (duplicate username) keeps the editor open and visible
//     with the backend's own message;
//   - backend SUCCESS closes the editor only once the matching lastWrites
//     requestId arrives, and the submit button is disabled while pending;
//   - CHANGE ROLE / DEACTIVATE-REACTIVATE / SET NEW PASSWORD each dispatch
//     their own typed event and follow the same pending → outcome contract;
//   - password fields are cleared after completion and the value typed is
//     never found anywhere in the rendered DOM.
//
// Run: node tests/component/dom_acceptance_user_management.mjs
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
const NON_ADMIN = FIX.journey;
const ADMIN = FIX.journeyAdmin;

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
    || candidates.find((element) => text(element).includes(needle))
    || null;
}
function clickNode(el) {
  el.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
}
async function click(needle, selector = "a,button", root = window.document) {
  const element = findClickable(needle, selector, root);
  assert.ok(element, `clickable "${needle}" not found`);
  clickNode(element);
  await tick();
  return element;
}
function type(input, value) {
  const proto = input.tagName === "TEXTAREA" ? window.HTMLTextAreaElement.prototype
    : input.tagName === "SELECT" ? window.HTMLSelectElement.prototype
    : window.HTMLInputElement.prototype;
  Object.getOwnPropertyDescriptor(proto, "value").set.call(input, value);
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
let triggers = [];
const mountRef = { current: null };
function invoke(data) {
  return mountRef.current({
    name: "logi_shell",
    data,
    parentElement: host,
    setTriggerValue: (ev, val) => triggers.push({ event: ev, value: val }),
  });
}
const eventsOf = (name) => triggers.filter((t) => t.event === name).map((t) => t.value);

const bundle = await import(path.join(ROOT, "component", "dist", "logi-shell.js"));
assert.equal(typeof bundle.default, "function", "bundle must default-export mount");
mountRef.current = bundle.default;

let cleanup = null;
async function remount(data) {
  if (cleanup) cleanup();
  cleanup = invoke(data);
  await tick(140);
  await click("Người dùng & Vai trò", "aside a", window.document);
}

console.log("STEP 1 — non-Admin session sees NO management control at all");
await remount(NON_ADMIN);
{
  assert.ok(!bodyText().includes("process is not defined"), "Node process leaked into browser bundle");
  const rendered = mainText();
  assert.ok(rendered.includes("CHỈ ĐỌC"), "non-Admin must still see the read-only badge");
  assert.equal(findClickable("+ THÊM TÀI KHOẢN"), null, "create button must not render for non-Admin");
  assert.equal($("[data-testid='user-access-account-actions']").length, 0, "no per-account actions for non-Admin");
  for (const label of ["Đổi vai trò", "Vô hiệu hóa", "Kích hoạt lại", "Đặt mật khẩu mới", "Xóa"]) {
    assert.equal(findClickable(label, "main button"), null, `unexpected control "${label}" for non-Admin`);
  }
  ok("non-Admin viewer gets zero management controls");
}

console.log("STEP 2 — Admin session sees the management controls; still no delete");
await remount(ADMIN);
{
  const rendered = mainText();
  assert.ok(!rendered.includes("CHỈ ĐỌC"), "Admin header must stop saying CHỈ ĐỌC");
  assert.ok(findClickable("+ THÊM TÀI KHOẢN"), "create button must render for Admin");
  const cards = $("[data-testid='user-access-account']");
  assert.equal(cards.length, 3, "3 accounts expected");
  for (const card of cards) {
    assert.ok(findClickable("Đổi vai trò", "button", card), "role control missing on a card");
    assert.ok(
      findClickable("Vô hiệu hóa", "button", card) || findClickable("Kích hoạt lại", "button", card),
      "active-toggle control missing on a card"
    );
    assert.ok(findClickable("Đặt mật khẩu mới", "button", card), "password-reset control missing on a card");
  }
  for (const label of ["Xóa tài khoản", "XÓA", "Delete"]) {
    assert.equal(findClickable(label, "main button"), null, `no delete-style action (${label})`);
  }
  ok("Admin viewer gets create + per-account role/active/password controls, never delete");
}

console.log("STEP 3 — CREATE: mismatch blocks dispatch; valid submit dispatches ONE user_create");
let firstCreateRequestId = "";
{
  triggers = [];
  await click("+ THÊM TÀI KHOẢN");
  const sheet = window.document.getElementById("user-create-sheet");
  assert.ok(sheet, "create sheet must open");
  const inputs = $("input", sheet);
  const usernameInput = inputs[0];
  const displayInput = inputs[1];
  const emailInput = inputs[2];
  const passwordInput = inputs.find((i) => i.type === "password");
  const confirmInput = inputs.filter((i) => i.type === "password")[1];
  type(usernameInput, "tan.sale");
  type(displayInput, "Tan Sale");
  type(emailInput, "tan.sale@congty.vn");
  type(passwordInput, "sale-passphrase-1");
  type(confirmInput, "different-passphrase-2");
  await tick(60);
  await click("TẠO TÀI KHOẢN", "button", sheet);
  assert.equal(eventsOf("user_create").length, 0, "mismatched confirmation must block dispatch");
  assert.ok(text(sheet).includes("khớp"), "mismatch message shown");
  ok("password/confirm mismatch refused locally, nothing dispatched");

  type(confirmInput, "sale-passphrase-1");
  await tick(60);
  triggers = [];
  await click("TẠO TÀI KHOẢN", "button", sheet);
  const sent = eventsOf("user_create");
  assert.equal(sent.length, 1, "exactly one user_create dispatched");
  const p = sent[0].payload;
  assert.equal(p.username, "tan.sale");
  assert.equal(p.displayName, "Tan Sale");
  assert.equal(p.role, ADMIN.userAccess.roles.assignable[0]);
  assert.equal(p.password, "sale-passphrase-1");
  assert.ok(p.requestId, "requestId minted");
  firstCreateRequestId = p.requestId;
  ok(`dispatched user_create with requestId ${firstCreateRequestId}`);

  const submitAgain = findClickable("ĐANG TẠO", "button", sheet);
  assert.ok(submitAgain && submitAgain.disabled, "submit disabled while pending");
  ok("submit disabled while the outcome is in flight");
}

console.log("STEP 4 — backend REFUSAL (duplicate username) keeps the editor open+visible");
{
  const refused = structuredClone(ADMIN);
  refused.lastWrites = [{
    event: "user_create", ok: false,
    error: "Tài khoản 'tan.sale' đã tồn tại — không tạo trùng.",
    requestId: firstCreateRequestId, username: "tan.sale",
  }];
  invoke(refused);
  await tick(160);
  const sheet = window.document.getElementById("user-create-sheet");
  assert.ok(sheet, "refusal keeps the create sheet open");
  const err = window.document.getElementById("user-create-error");
  assert.ok(err, "backend refusal element present");
  assert.ok(text(err).includes("đã tồn tại"), "shows the writer's own refusal verbatim");
  ok("backend refusal surfaces verbatim; editor stays open and visible");
}

console.log("STEP 5 — a NEW submit (fresh requestId) succeeds and closes the editor");
let secondCreateRequestId = "";
{
  const sheet = window.document.getElementById("user-create-sheet");
  const usernameInput = $("input", sheet)[0];
  type(usernameInput, "tan.sale2");
  await tick(60);
  triggers = [];
  clickNode(findClickable("TẠO TÀI KHOẢN", "button", sheet));
  await tick(100);
  const sent = eventsOf("user_create");
  assert.equal(sent.length, 1, "the resubmitted intent dispatches exactly one event");
  secondCreateRequestId = sent[0].payload.requestId;
  assert.notEqual(secondCreateRequestId, firstCreateRequestId, "a fresh submit mints a NEW requestId");

  const succeeded = structuredClone(ADMIN);
  succeeded.userAccess.users = [
    ...ADMIN.userAccess.users,
    { user_id: "U-NEW", username: "tan.sale2", display_name: "Tan Sale", email: "tan.sale@congty.vn", role: ADMIN.userAccess.roles.assignable[0], active: true },
  ];
  succeeded.userAccess.counts = { ...ADMIN.userAccess.counts, userCount: 4, userShown: 4, activeCount: ADMIN.userAccess.counts.activeCount + 1 };
  succeeded.lastWrites = [{
    event: "user_create", ok: true, requestId: secondCreateRequestId, username: "tan.sale2",
    readback: { user_id: "U-NEW", username: "tan.sale2", display_name: "Tan Sale", role: ADMIN.userAccess.roles.assignable[0], active: true, email: "tan.sale@congty.vn" },
  }];
  invoke(succeeded);
  await tick(160);
  assert.ok(!window.document.getElementById("user-create-sheet"), "authoritative success closes the create sheet");
  const rendered = mainText();
  assert.ok(rendered.includes("tan.sale2"), "fresh VM shows the new account");
  for (const marker of ["sale-passphrase-1", "different-passphrase-2", "pbkdf2_sha256$"]) {
    assert.ok(!bodyText().includes(marker), `password material "${marker}" must never appear in the DOM`);
  }
  ok("success closes only on authoritative outcome; password never leaked into the DOM");
}

console.log("STEP 6 — CHANGE ROLE dispatches user_role_set; refusal keeps the sheet open");
let roleRequestId = "";
await remount(ADMIN);
{
  const card = $("[data-testid='user-access-account']").find((c) => c.getAttribute("data-username") === "thu-hang");
  assert.ok(card, "thu-hang card present");
  triggers = [];
  clickNode(findClickable("Đổi vai trò", "button", card));
  await tick(100);
  const sheet = window.document.getElementById("user-role-sheet");
  assert.ok(sheet, "role sheet opens");
  const select = $("select", sheet)[0];
  const targetRole = ADMIN.userAccess.roles.assignable.find((r) => r !== "support") ?? ADMIN.userAccess.roles.assignable[0];
  type(select, targetRole);
  await tick(60);
  clickNode(findClickable("LƯU VAI TRÒ", "button", sheet));
  await tick(100);
  const sent = eventsOf("user_role_set");
  assert.equal(sent.length, 1, "exactly one user_role_set dispatched");
  assert.equal(sent[0].payload.username, "thu-hang");
  assert.equal(sent[0].payload.role, targetRole);
  roleRequestId = sent[0].payload.requestId;
  ok(`dispatched user_role_set → ${targetRole} for thu-hang`);

  const refused = structuredClone(ADMIN);
  refused.lastWrites = [{ event: "user_role_set", ok: false, error: "Không thể đổi vai trò của Admin đang hoạt động cuối cùng.", requestId: roleRequestId, username: "thu-hang" }];
  invoke(refused);
  await tick(140);
  assert.ok(window.document.getElementById("user-role-sheet"), "refusal keeps the role sheet open");
  assert.ok(text(window.document.getElementById("user-role-error")).includes("Admin đang hoạt động cuối cùng"), "shows backend refusal verbatim");
  ok("role-change refusal keeps the editor open with the backend's own reason");
}

console.log("STEP 7 — DEACTIVATE / REACTIVATE dispatches user_active_set");
await remount(ADMIN);
{
  const card = $("[data-testid='user-access-account']").find((c) => c.getAttribute("data-username") === "minh-tu");
  assert.ok(card, "minh-tu card present (active account)");
  triggers = [];
  clickNode(findClickable("Vô hiệu hóa", "button", card));
  await tick(100);
  const sheet = window.document.getElementById("user-active-sheet");
  assert.ok(sheet, "active sheet opens");
  clickNode(findClickable("VÔ HIỆU HÓA", "button", sheet));
  await tick(100);
  const sent = eventsOf("user_active_set");
  assert.equal(sent.length, 1);
  assert.equal(sent[0].payload.username, "minh-tu");
  assert.equal(sent[0].payload.active, false);
  ok("dispatched user_active_set(active=false) for minh-tu");

  // Deliver the authoritative outcome so the sheet closes before the next
  // action is attempted — otherwise the still-open sheet's overlay would
  // block clicks on the card behind it.
  const afterFirst = structuredClone(ADMIN);
  afterFirst.lastWrites = [{ event: "user_active_set", ok: true, requestId: sent[0].payload.requestId, username: "minh-tu",
    readback: { user_id: "U2", username: "minh-tu", display_name: "Minh Tú", role: "sale", active: false, email: "" } }];
  invoke(afterFirst);
  await tick(140);
  assert.ok(!window.document.getElementById("user-active-sheet"), "success closes the active sheet");

  const reactivateCard = $("[data-testid='user-access-account']").find((c) => c.getAttribute("data-username") === "lan-viewer");
  assert.ok(reactivateCard.querySelector("[data-testid='user-access-account-inactive']"), "lan-viewer starts inactive");
  triggers = [];
  clickNode(findClickable("Kích hoạt lại", "button", reactivateCard));
  await tick(100);
  const sheet2 = window.document.getElementById("user-active-sheet");
  clickNode(findClickable("KÍCH HOẠT LẠI", "button", sheet2));
  await tick(100);
  const sent2 = eventsOf("user_active_set");
  assert.equal(sent2.length, 1);
  assert.equal(sent2[0].payload.username, "lan-viewer");
  assert.equal(sent2[0].payload.active, true);
  ok("dispatched user_active_set(active=true) for lan-viewer");
}

console.log("STEP 8 — SET NEW PASSWORD dispatches user_password_reset; fields never leak");
await remount(ADMIN);
{
  const card = $("[data-testid='user-access-account']").find((c) => c.getAttribute("data-username") === "thu-hang");
  triggers = [];
  clickNode(findClickable("Đặt mật khẩu mới", "button", card));
  await tick(100);
  const sheet = window.document.getElementById("user-password-sheet");
  assert.ok(sheet, "password sheet opens");
  const [pwInput, confirmInput] = $("input[type='password']", sheet);
  type(pwInput, "brand-new-passphrase-1");
  type(confirmInput, "brand-new-passphrase-1");
  await tick(60);
  clickNode(findClickable("ĐẶT MẬT KHẨU MỚI", "button", sheet));
  await tick(100);
  const sent = eventsOf("user_password_reset");
  assert.equal(sent.length, 1);
  assert.equal(sent[0].payload.username, "thu-hang");
  assert.equal(sent[0].payload.newPassword, "brand-new-passphrase-1");
  ok("dispatched user_password_reset for thu-hang");

  const succeeded = structuredClone(ADMIN);
  succeeded.lastWrites = [{ event: "user_password_reset", ok: true, requestId: sent[0].payload.requestId, username: "thu-hang",
    readback: { user_id: "U1", username: "thu-hang", display_name: "Thu Hằng", role: "support", active: true, email: "" } }];
  invoke(succeeded);
  await tick(140);
  assert.ok(!window.document.getElementById("user-password-sheet"), "success closes the password sheet");
  assert.ok(!bodyText().includes("brand-new-passphrase-1"), "the new password value never appears in the DOM");
  ok("password sheet closes on success; typed password never rendered anywhere");
}

if (cleanup) cleanup();
console.log(`\nUSER_MANAGEMENT_DOM_ACCEPTANCE=PASSED checks=${passed}`);
