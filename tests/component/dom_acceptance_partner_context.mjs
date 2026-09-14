// ============================================================================
// LOGI_PARTNER_CONTEXT_WORKSPACE_01 — DOM/navigation acceptance for
// /ngu-canh-doi-tac ("Đại Lý Trường Thành").
//
// LOGI_REAL_USE_CREATE_SHIPMENT_AGENT_MASTER_01 extended this suite: the
// visible workspace is now the AGENT MASTER MANAGEMENT desk (CREATE / EDIT of
// the existing authority_agents master through ONE bounded typed event) while
// the linked shipment / document / payable context stays the same READ-ONLY
// projection as before.
//
// Runs the REAL production bundle (component/dist/logi-shell.js) in jsdom with a
// REAL-backend fixture (scripts/gen_partner_context_fixture.py — isolated
// mongomock staging, one C2B obligation + one payment recorded through the
// canonical handlers) and verifies:
//   1. boot (no process/BidiComponent failure)
//   2. sidebar "Đại Lý Trường Thành" carries NO "Sắp có" marker anymore and
//      keeps the existing route /ngu-canh-doi-tac
//   3. the route renders the REAL workspace — new visible label + subtitle,
//      "+ THÊM ĐẠI LÝ" action present, NO misleading whole-page "CHỈ ĐỌC"
//   4. selecting a partner emits the ONE bounded READ-ONLY
//      "partner_context_select" trigger carrying only the entity key
//   5. the fresh readback renders authoritative identity (authority_agents
//      master, verbatim), the real linked shipment with a working Open-Shipment
//      link on the existing /lo-hang/:id route, and the canonical payable
//      figures with their currency — EXISTING CONTEXT PRESERVED
//   6. a partner with no canonical payable stays UNKNOWN (no "0" payable)
//   7. an unknown partner key fails honest (no fabricated record)
//   8. no CRM surface exists (no score/tier/note/activity/tab) and the
//      unavailable-context panel states exactly what the backend lacks
//   9. EDIT flow: form prefills from the master, one authority_agent_save
//      trigger, and the saved master appears only via the authoritative
//      readback (no optimistic persistence)
//  10. CREATE flow: "+ THÊM ĐẠI LÝ" saves a NEW master; it appears in the
//      picker "có master" and its context opens via the same read-only
//      selection event
//  11. RBAC refusal: the ok=False backend outcome is displayed verbatim, the
//      form stays open, nothing is faked as saved
//  12. mobile: drawer routes to the same workspace, cards (not a min-width
//      table) carry the shipment list, touch targets are >= 48px
//
// Run: node tests/component/dom_acceptance_partner_context.mjs
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
  readFileSync(path.join(ROOT, "tests/component/fixtures/view_model_partner_context.json"), "utf8")
);
const VM = FIX.journey;
const EMPTY = FIX.empty;
const NO_FINANCE = FIX.noFinance;
const MISSING = FIX.unknownPartner;
const AGENT_EDIT_OK = FIX.agentEditOk;
const AGENT_CREATE_OK = FIX.agentCreateOk;
const AGENT_SAVE_ERROR = FIX.agentSaveError;
const PARTNER = FIX.partner;          // AGT-PHUANH (authority_agents master)
const SHIPMENT = FIX.shipment;         // LO-0308
const PARTNER_LABEL = "CÔNG TY TNHH PHÚ ANH LOGISTICS";
const NEW_AGENT = "AGT-MINHPHAT";
const NEW_AGENT_LABEL = "CÔNG TY TNHH ĐẠI LÝ MINH PHÁT";
const PAGE_TITLE = "Đại Lý Trường Thành";

/** Rewrite the fixture outcome's requestId to the one the real click produced —
 *  exactly how the live backend echoes the component's request identity. */
function withRequestId(state, requestId) {
  const clone = structuredClone(state);
  for (const w of clone.lastWrites ?? []) w.requestId = requestId;
  return clone;
}

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
  "HTMLAnchorElement", "Event", "CustomEvent", "MouseEvent", "KeyboardEvent",
  "Node", "MutationObserver", "getComputedStyle",
]) {
  globalThis[k] = window[k];
}
if (!globalThis.MessageChannel) globalThis.MessageChannel = window.MessageChannel;
window.HTMLElement.prototype.scrollIntoView = () => {};
window.URL.createObjectURL = () => "blob:mock-url";
window.URL.revokeObjectURL = () => {};

const tick = (ms = 60) => new Promise((r) => setTimeout(r, ms));

const $ = (sel, root = window.document) => [...root.querySelectorAll(sel)];
const text = (el) => (el.textContent || "").replace(/\s+/g, " ").trim();
const mainText = () => text($("main")[0] ?? window.document.body);
const bodyText = () => text(window.document.body);

function findClickable(needle, sel = "a,button", root = window.document) {
  const els = $(sel, root);
  return els.find((el) => text(el) === needle) || els.find((el) => text(el).startsWith(needle)) || null;
}

async function click(needle, sel = "a,button", root = window.document) {
  const el = findClickable(needle, sel, root);
  assert.ok(el, `clickable "${needle}" not found`);
  el.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
  await tick();
  return el;
}

async function clickSelector(sel, root = window.document) {
  const el = $(sel, root)[0];
  assert.ok(el, `selector "${sel}" not found`);
  el.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
  await tick();
  return el;
}

async function type(input, value) {
  const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
  setter.call(input, value);
  input.dispatchEvent(new window.Event("input", { bubbles: true }));
  await tick();
}

let passed = 0;
function ok(name) {
  passed += 1;
  console.log(`  ✓ ${name}`);
}

const host = window.document.createElement("div");
window.document.body.appendChild(host);
const triggers = [];
const mountRef = { current: null };
function invoke(data) {
  return mountRef.current({
    name: "logi_shell",
    data,
    parentElement: host,
    setTriggerValue: (event, value) => triggers.push({ event, value }),
  });
}

/** Simulate leaving the page and coming back: React remounts (route resets to
 *  "/") while Python re-delivers the last authoritative read. */
let lastInvokeCleanup = null;
async function remount(data, item = PAGE_TITLE) {
  if (lastInvokeCleanup) lastInvokeCleanup();
  const cleanup = invoke(data);
  lastInvokeCleanup = cleanup;
  await tick(120);
  await click(item, "a", $("aside")[0]);
}

const bundlePath = path.join(ROOT, "component/dist/logi-shell.js");

// ---------------------------------------------------------------------------
console.log("STEP 1 — boot production bundle (unselected state)");
{
  const mod = await import(bundlePath);
  assert.equal(typeof mod.default, "function");
  mountRef.current = mod.default;
  lastInvokeCleanup = invoke(EMPTY);
  await tick(120);
  const t = bodyText();
  assert.ok(!t.includes("process is not defined"), "process is not defined leaked");
  assert.ok(!t.includes("BidiComponent Error"), "BidiComponent Error rendered");
  assert.ok(t.includes("TRƯỜNG THÀNH"), "app did not render");
  ok("boot clean, shell rendered");
}

// ---------------------------------------------------------------------------
console.log("STEP 2 — sidebar honesty: no 'Sắp có' on " + PAGE_TITLE);
{
  const aside = $("aside")[0];
  const item = findClickable(PAGE_TITLE, "a", aside);
  assert.ok(item, "sidebar item missing");
  assert.ok(!text(item).includes("Sắp có"), "item still marked 'Sắp có'");
  assert.equal(item.getAttribute("href"), "/ngu-canh-doi-tac", "route must stay the existing one");
  ok("visible label renamed; the route stays /ngu-canh-doi-tac, no deferred marker");
}

// ---------------------------------------------------------------------------
console.log("STEP 3 — /ngu-canh-doi-tac renders " + PAGE_TITLE + " (agent master desk)");
await click(PAGE_TITLE, "a", $("aside")[0]);
{
  const t = mainText();
  assert.ok(!t.includes("Sắp có — chưa triển khai"), "route still falls through to the placeholder");
  assert.ok(t.includes(PAGE_TITLE), "workspace heading missing");
  assert.ok(!t.includes("Ngữ cảnh Đối tác"), "old visible label must be gone");
  // The misleading whole-page "CHỈ ĐỌC" description is removed — the linked
  // shipment/finance context keeps its own read-only notes below.
  assert.ok(!t.includes("CHỈ ĐỌC"), "whole-page read-only badge must be gone");
  assert.ok(!t.includes("Màn hình chỉ đọc — không sửa, không ghi"),
    "misleading whole-page read-only subtitle must be gone");
  assert.ok(t.includes("Quản lý hồ sơ đại lý của Trường Thành"), "new subtitle missing");
  // The agent-master management action is exposed.
  const addBtn = findClickable("THÊM ĐẠI LÝ", "button");
  assert.ok(addBtn, "+ THÊM ĐẠI LÝ action missing");
  // The picker lists the partner the backend really has, and nothing else.
  assert.ok(t.includes(PARTNER_LABEL), "authoritative partner option missing from picker");
  assert.ok(t.includes("có master"), "master/unknown distinction missing");
  assert.ok(t.includes("Bảng ngữ cảnh đang trống"), "idle state missing");
  // No fabricated context: nothing about the unselected partner is rendered.
  assert.ok(!t.includes("57.000.000"), "payable shown before any authoritative read");
  assert.ok(!/điểm quan hệ|rủi ro: |credit|tín dụng: [0-9]/i.test(t), "a score-like surface appeared");
  ok("renamed agent-master desk over the existing picker; no placeholder, no invented context");
}

// ---------------------------------------------------------------------------
console.log("STEP 4 — partner selection emits ONE bounded READ-ONLY trigger");
{
  const before = triggers.length;
  await click(PARTNER_LABEL, "button");
  await tick(40);
  // The readback is what makes context appear, so in the meantime the page must
  // show a bounded pending state and NOTHING computed locally.
  assert.ok(mainText().includes("Đang đọc ngữ cảnh đối tác…"),
    "no bounded pending state while the readback is in flight");
  const selects = triggers.slice(before).filter((tr) => tr.event === "partner_context_select");
  assert.equal(selects.length, 1, "expected exactly one partner_context_select trigger");
  assert.equal(selects[0].value.event, "partner_context_select");
  assert.equal(selects[0].value.payload.entityKey, PARTNER, "trigger must carry the key only");
  assert.equal(typeof selects[0].value.seq, "number");
  // Nothing else was dispatched: a selection never writes business data.
  const others = triggers.slice(before).filter((tr) => tr.event !== "partner_context_select");
  assert.equal(others.length, 0, `selection must not emit other events, got ${others.map((o) => o.event)}`);
  ok("one typed partner_context_select trigger, entity key only, no other event");
}

// ---------------------------------------------------------------------------
console.log("STEP 5 — fresh readback renders authoritative identity + shipment + payable");
{
  lastInvokeCleanup = invoke(VM);
  await tick(120);
  const t = mainText();
  // identity: authority_agents master, verbatim
  assert.ok(t.includes(PARTNER_LABEL), "legal name missing");
  assert.ok(t.includes("AGT-PHUANH"), "master id missing");
  assert.ok(t.includes("0315678910"), "legal/tax code missing");
  assert.ok(t.includes("Số 45, Nguyễn Văn Linh, Quận 7, TP. Hồ Chí Minh"), "legal address missing");
  assert.ok(t.includes("Phạm Văn Thành"), "representative missing");
  assert.ok(t.includes("0281234567"), "phone missing");
  assert.ok(t.includes("sales@phuanh.vn"), "email missing");
  assert.ok(t.includes("Techcombank") && t.includes("9876543210"), "bank details missing");
  assert.ok(t.includes("authority_agents (legal Agent master)"), "identity source not attributed");
  assert.ok(t.includes("master: CÓ HỒ SƠ"), "master status badge missing");
  // linked shipment: authoritative id + existing route only
  const openLink = $('a[href="/lo-hang/LO-0308"]')[0];
  assert.ok(openLink, "Open Shipment link to the existing route missing");
  assert.ok(text(openLink).includes("Mở lô"), "open-link label missing");
  assert.ok(t.includes("Lô hàng liên kết · 1"), "linked shipment count wrong");
  // finance: the canonical C2D figures, currency-labelled, never re-derived
  assert.ok(t.includes("57.000.000 VND"), "payable figure not rendered verbatim");
  assert.ok(t.includes("20.000.000 VND"), "paid figure not rendered verbatim");
  assert.ok(t.includes("37.000.000 VND"), "remaining figure not rendered verbatim");
  assert.ok(t.includes("CONFIRMED"), "payable status missing");
  assert.ok(t.includes("ĐÃ XÁC NHẬN"), "payable status label missing");
  assert.ok($('a[href="/tai-chinh/cong-no-doi-tac"]')[0], "link to the C2D worklist missing");
  assert.ok(t.includes("không quy đổi tiền tệ"), "finance boundary note missing");
  ok("identity + linked shipment + canonical payable rendered from the readback");
}

// ---------------------------------------------------------------------------
console.log("STEP 6 — UNKNOWN != ZERO for a partner with no canonical payable");
{
  await remount(NO_FINANCE);
  await tick(120);
  const t = mainText();
  assert.ok(t.includes(PARTNER_LABEL), "identity lost in the no-payable state");
  assert.ok(t.includes("CHƯA XÁC ĐỊNH"), "payable must be reported as unknown");
  assert.ok(t.includes("hệ thống không hiển thị 0"), "explicit 'not zero' statement missing");
  assert.ok(!t.includes("57.000.000"), "a payable appeared out of nowhere");
  // The linked shipment list is empty here because the ledger row is what links
  // the partner to a lot — absence is stated, never invented.
  assert.ok(t.includes("Chưa có lô nào liên kết") || t.includes("chưa xác định"), "empty shipment state missing");
  ok("no canonical payable ⇒ UNKNOWN, explicitly not 0");
}

// ---------------------------------------------------------------------------
console.log("STEP 7 — unknown partner key fails honest (no fabricated record)");
{
  await remount(MISSING);
  await tick(120);
  const t = mainText();
  assert.ok(t.includes("Không tìm thấy đối tác"), "not-found heading missing");
  assert.ok(t.includes("AGT-KHONG-TON-TAI"), "the attempted key must be echoed");
  assert.ok(t.includes("không có bản ghi nào được tạo thay thế"), "honest reason missing");
  assert.ok(!t.includes("Hồ sơ pháp lý · danh tính"), "identity must not render for a missing partner");
  assert.ok(!t.includes("master: CÓ HỒ SƠ"), "master badge leaked into a not-found state");
  assert.ok(!t.includes("0315678910"), "master fields leaked into a not-found state");
  // The picker stays usable so the Owner can choose an existing partner instead.
  assert.ok(t.includes(PARTNER_LABEL), "picker lost the partners that do exist");
  ok("PARTNER_NOT_FOUND rendered without inventing anything");
}

// ---------------------------------------------------------------------------
console.log("STEP 8 — no CRM surface; unavailable context is stated, not faked");
{
  await remount(VM);
  await tick(120);
  const t = mainText();
  assert.ok(t.includes("Context không khả dụng trong hệ thống"), "unavailable-context panel missing");
  for (const phrase of ["Điểm quan hệ đối tác", "Hạng đối tác", "Ghi chú, lịch sử liên hệ", "SLA"]) {
    assert.ok(t.includes(phrase), `unavailable list must name: ${phrase}`);
  }
  // Structurally: no tab strip, no note/task/tag editor, no score widget exists.
  assert.equal($('[role="tablist"]').length, 0, "a tab system must not exist here");
  assert.equal($("textarea").length, 0, "no free-text partner note/task surface allowed");
  const labels = $("label").map((el) => text(el));
  assert.ok(!labels.some((l) => /ghi chú đối tác|tag|nhãn|point|rủi ro/i.test(l)), `CRM control leaked: ${labels}`);
  // Search stays on the fields the backend really matches.
  assert.ok(t.includes("mã đối tác") && t.includes("điện thoại"), "supported search terms not declared");
  ok("no CRM controls; missing context is declared instead of padded");
}

// ---------------------------------------------------------------------------
console.log("STEP 9 — EDIT: form prefills from the master; saved only via readback");
{
  await remount(VM);
  await tick(120);
  // The selected partner (AGT-PHUANH) has a master → the edit action exists.
  const editBtn = findClickable("Sửa hồ sơ đại lý", "button");
  assert.ok(editBtn, "edit action missing for a master-backed agent");
  await click("Sửa hồ sơ đại lý", "button");
  // Prefilled from the canonical master, verbatim; the id is locked on edit.
  const phone = $('input[aria-label="Điện thoại"]')[0];
  const agentId = $('input[aria-label="Mã đại lý"]')[0];
  assert.ok(phone && phone.value === "0281234567", `form must prefill master phone, got "${phone?.value}"`);
  assert.ok(agentId && agentId.value === PARTNER && agentId.disabled,
    "agent id must prefill and stay locked on edit");
  // Change ONE field and save.
  await type(phone, "0289999888");
  const before = triggers.length;
  await click("LƯU HỒ SƠ ĐẠI LÝ", "button");
  await tick(40);
  // While the outcome is in flight: pending, no optimistic display.
  assert.ok(mainText().includes("ĐANG CHỜ BACKEND XÁC NHẬN…"), "no bounded pending state on save");
  const saves = triggers.slice(before).filter((tr) => tr.event === "authority_agent_save");
  assert.equal(saves.length, 1, "expected exactly one authority_agent_save trigger");
  assert.equal(saves[0].value.payload.agentId, PARTNER);
  assert.equal(saves[0].value.payload.phone, "0289999888");
  assert.equal(typeof saves[0].value.payload.requestId, "string");
  const sentReq = saves[0].value.payload.requestId;
  // The authoritative readback arrives → form closes, updated master renders.
  lastInvokeCleanup = invoke(withRequestId(AGENT_EDIT_OK, sentReq));
  await tick(140);
  const t = mainText();
  assert.ok(!t.includes("LƯU HỒ SƠ ĐẠI LÝ"), "form must close after the authoritative readback");
  assert.ok(t.includes("0289999888"), "updated phone must render from the fresh master");
  assert.ok(t.includes(PARTNER_LABEL), "identity must stay rendered after the edit");
  ok("edit goes through ONE authority_agent_save; the saved master arrives via readback");
}

// ---------------------------------------------------------------------------
console.log("STEP 10 — CREATE: + THÊM ĐẠI LÝ saves a NEW master, shown immediately");
{
  await remount(VM);
  await tick(120);
  await click("THÊM ĐẠI LÝ", "button");
  const agentId = $('input[aria-label="Mã đại lý"]')[0];
  const legalName = $('input[aria-label="Tên pháp lý"]')[0];
  const bankName = $('input[aria-label="Ngân hàng"]')[0];
  assert.ok(agentId && !agentId.disabled && agentId.value === "", "create form must start empty/unlocked");
  await type(agentId, NEW_AGENT);
  await type(legalName, NEW_AGENT_LABEL);
  await type(bankName, "Vietcombank");
  const before = triggers.length;
  await click("LƯU HỒ SƠ ĐẠI LÝ", "button");
  await tick(40);
  const saves = triggers.slice(before).filter((tr) => tr.event === "authority_agent_save");
  assert.equal(saves.length, 1, "expected exactly one authority_agent_save trigger");
  assert.equal(saves[0].value.payload.agentId, NEW_AGENT);
  assert.equal(saves[0].value.payload.legalName, NEW_AGENT_LABEL);
  assert.equal(typeof saves[0].value.payload.requestId, "string");
  const sentReq = saves[0].value.payload.requestId;
  // Authoritative readback: the NEW master is in the picker ("có master") and
  // its context opens through the same bounded read-only selection event.
  lastInvokeCleanup = invoke(withRequestId(AGENT_CREATE_OK, sentReq));
  await tick(140);
  const selects = triggers.slice(before + 1).filter((tr) => tr.event === "partner_context_select");
  assert.equal(selects.length, 1, "saved master must be opened via partner_context_select");
  assert.equal(selects[0].value.payload.entityKey, NEW_AGENT);
  const t = mainText();
  assert.ok(t.includes(NEW_AGENT_LABEL), "new master must be visible immediately after save");
  assert.ok(t.includes("AGT-MINHPHAT"), "new master id missing");
  assert.ok(t.includes("Vietcombank"), "new master bank missing");
  assert.ok(!t.includes("LƯU HỒ SƠ ĐẠI LÝ"), "form must close after the authoritative readback");
  ok("create writes through the existing writer; saved master visible immediately");
}

// ---------------------------------------------------------------------------
console.log("STEP 11 — RBAC refusal: real backend error shown, nothing faked");
{
  await remount(VM);
  await tick(120);
  await click("THÊM ĐẠI LÝ", "button");
  await type($('input[aria-label="Mã đại lý"]')[0], "AGT-TRAITUYEN");
  await type($('input[aria-label="Tên pháp lý"]')[0], "CÔNG TY TRÁI TUYẾN");
  const before = triggers.length;
  await click("LƯU HỒ SƠ ĐẠI LÝ", "button");
  await tick(40);
  const saves = triggers.slice(before).filter((tr) => tr.event === "authority_agent_save");
  assert.equal(saves.length, 1);
  const sentReq = saves[0].value.payload.requestId;
  // Backend refuses (viewer has no sales_write): the ok=False outcome must be
  // displayed verbatim, the form stays open, nothing is faked as saved.
  lastInvokeCleanup = invoke(withRequestId(AGENT_SAVE_ERROR, sentReq));
  await tick(140);
  const t = mainText();
  assert.ok(t.includes("Backend từ chối — hồ sơ chưa được lưu"), "refusal banner missing");
  assert.ok(t.includes("RBAC: không có quyền sales_write."), "real backend error must be visible");
  assert.ok(t.includes("LƯU HỒ SƠ ĐẠI LÝ"), "form must stay open after a refusal");
  assert.ok(!t.includes("AGT-TRAITUYEN · ") || !t.includes("Hồ sơ pháp lý · danh tính"),
    "a refused agent must not render an identity card");
  ok("RBAC refusal displayed verbatim; form stays, nothing persisted");
}

// ---------------------------------------------------------------------------
console.log("STEP 12 — mobile: drawer reaches the workspace; cards + 48px targets");
{
  await remount(VM);
  await tick(120);
  await clickSelector('button[aria-label="Mở menu"]');
  const drawer = $("div.anim-slide-up").filter((el) => text(el).includes("Menu điều hành"))[0]
    ?? $(".fixed.inset-0.z-50")[0];
  assert.ok(drawer, "mobile drawer missing");
  const drawerItem = findClickable(PAGE_TITLE, "a", drawer);
  assert.ok(drawerItem, "drawer item missing");
  assert.ok(!text(drawerItem).includes("Sắp có"), "drawer item still marked 'Sắp có'");
  await click(PAGE_TITLE, "a", drawer);
  assert.ok(mainText().includes(PAGE_TITLE), "drawer must open the agent-master workspace");
  // The shipment list is a card stack at narrow widths (lg:hidden), and the
  // min-width table is hidden below lg — no unusable horizontal scroll.
  assert.ok($("div[class*='lg:hidden']").length > 0, "mobile card container missing");
  const tableWrap = $("div[class*='hidden lg:block']")[0];
  assert.ok(tableWrap, "desktop table must stay gated behind lg");
  assert.ok(tableWrap.querySelector("table").className.includes("min-w-[900px]"),
    "desktop table must keep its min width only inside the lg gate");
  const search = $('input[aria-label="Tìm đối tác"]')[0];
  assert.ok(search.className.includes("min-h-[48px]"), "search input below touch target");
  const open = $('a[href="/lo-hang/LO-0308"]');
  assert.ok(open.length > 0 && open.every((a) => text(a).includes("Mở lô")), "Open Shipment unreachable on mobile");
  const chips = $("button").filter((b) => text(b).startsWith(PARTNER_LABEL));
  assert.ok(chips.length > 0 && chips.every((b) => b.className.includes("min-h-[48px]")),
    "partner picker below touch target");
  ok("drawer routing, card stack, gated table, 48px controls, reachable Open Shipment");
}

// ---------------------------------------------------------------------------
console.log("STEP 13 — other real routes are undisturbed");
{
  await click("Công nợ đối tác", "a", $("aside")[0]);
  assert.ok(mainText().includes("Thanh toán đối tác"), "C2D route was disturbed");
  await click("Thu tiền", "a", $("aside")[0]);
  assert.ok(mainText().includes("Phải thu") || mainText().includes("Thu tiền"), "C2C route was disturbed");
  ok("/tai-chinh/cong-no-doi-tac and /tai-chinh/thu-tien still render their real pages");
}

console.log(`\nDOM acceptance PASSED — ${passed} checks`);
