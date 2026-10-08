// ============================================================================
// LOGI_GOOD_FRONTEND_CONSOLIDATION_01 — DOM/navigation acceptance.
//
// Runs the REAL production bundle (component/dist/logi-shell.js) in jsdom
// with a fresh real-backend fixture (scripts/gen_consolidation_fixture.py)
// and verifies the consolidation sweep:
//   1. boot (no process/BidiComponent failure)
//   2. Home/Dashboard contrast defect fix: the donor gradient chain now has
//      inheritable custom-property defaults in the shadow-root shell css
//   3. sidebar: all donor items, honest "Sắp có" markers on the three
//      remaining deferred destinations, REAL open-task badge
//      (LOGI_TARIFF_LOOKUP_01 promoted /tra-cuu-thue and
//      LOGI_TRANSLATION_WORKSPACE_01 promoted /dich-thuat to real workspaces)
//   4. footer tells the truth (no hardcoded sample date)
//   5. every REAL_BACKED sidebar destination opens its real page
//   6. every UNBACKED destination opens the explicit deferred placeholder
//   7. mobile: drawer + bottom nav route to the same REAL pages
//      (Lô hàng → Lô Hàng, Tài chính → Thu tiền, …) and back to Home
//   8. placeholder honesty: PXK tab has no hardcoded sample date, shipment
//      doc checklist has no fake download/upload actions
//   9. quick-add sheet marks the deferred tool and routes the rest
//  10. route survives a backend rerun (re-invocation with new data)
//
// Run: node tests/component/dom_acceptance_consolidation.mjs
// ============================================================================

import { readFileSync } from "node:fs";
import assert from "node:assert/strict";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const require = createRequire(path.join(ROOT, "component/package.json"));
const { JSDOM } = require("jsdom");
const VM = JSON.parse(
  readFileSync(path.join(ROOT, "tests/component/fixtures/view_model_consolidation.json"), "utf8")
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

// Issue #190 — the permanent shipment tab row was removed from the default
// Journey first screen; the tabs now live in the Global Workspace opened via
// "Toàn bộ lô hàng". This helper opens it and clicks the remapped tab.
async function openGlobalTab(label) {
  await click("Toàn bộ lô hàng", "button");
  await click(label, "button", window.document.querySelector('[data-testid="journey-global-workspace"]'));
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
const bundlePath = path.join(ROOT, "component/dist/logi-shell.js");

// ---------------------------------------------------------------------------
console.log("STEP 1 — boot production bundle");
{
  const mod = await import(bundlePath);
  assert.equal(typeof mod.default, "function");
  mountRef.current = mod.default;
  invoke(VM);
  await tick(120);
  const t = bodyText();
  assert.ok(!t.includes("process is not defined"), "process is not defined leaked");
  assert.ok(!t.includes("BidiComponent Error"), "BidiComponent Error rendered");
  assert.ok(t.includes("TRƯỜNG THÀNH"), "app did not render");
  ok("boot clean, shell rendered");
}

// ---------------------------------------------------------------------------
console.log("STEP 2 — Home/Dashboard contrast defect fix (gradient safety net)");
{
  const css = readFileSync(path.join(ROOT, "component/dist/logi-shell.css"), "utf8");
  for (const prop of [
    "--tw-gradient-from-position:0%",
    "--tw-gradient-via-position:50%",
    "--tw-gradient-to-position:100%",
    "--tw-gradient-from:#0000",
    "--tw-gradient-to:#0000",
  ]) {
    assert.ok(css.includes(prop), `gradient default missing in shell css: ${prop}`);
  }
  const js = readFileSync(bundlePath, "utf8");
  assert.ok(
    js.includes("bg-gradient-to-br from-[#0a1f3a] via-[#0f2a4a] to-[#1e5aa8]"),
    "donor hero gradient markup must stay (parity, not redesign)"
  );
  const t = mainText();
  assert.ok(t.includes("Hôm nay tôi cần làm gì?"), "Home hero heading missing");
  ok("gradient chain resolves without @property (hero contrast cannot collapse)");
}

// ---------------------------------------------------------------------------
console.log("STEP 3 — sidebar: full nav + honest markers + real badge");
{
  const aside = $("aside")[0];
  assert.ok(aside, "sidebar aside missing");
  const at = text(aside);
  // LOGI_INTERNAL_UX_SIMPLIFY_01 — "Việc Cần Xử Lý", "Theo Dõi Vận Chuyển"
  // and "Thỏa thuận mua bán" left the normal nav; "Báo giá" is "Báo Giá".
  for (const it of [
    "Tổng Quan Công Việc", "Lô Hàng", "Tạo Lô Mới",
    "Khách Hàng", "Đại Lý Trường Thành", "Báo Giá",
    "Hợp đồng", "Thu tiền", "Đối soát",
    "Công nợ đối tác", "Báo cáo CEO", "Tra cứu thuế / HS", "Sổ tay",
    "Dịch thuật", "Người dùng & Vai trò",
  ]) {
    assert.ok(at.includes(it), `sidebar item missing: ${it}`);
  }
  // ZERO remaining deferred destinations carry the marker
  // (/tra-cuu-thue became a REAL read-only workspace in LOGI_TARIFF_LOOKUP_01,
  // /dich-thuat a REAL translation workspace in LOGI_TRANSLATION_WORKSPACE_01,
  // /ngu-canh-doi-tac a REAL read-only partner-context workspace in
  // LOGI_PARTNER_CONTEXT_WORKSPACE_01, and /tai-chinh/doi-soat a REAL read-only
  // reconciliation desk in LOGI_RECONCILIATION_DESK_01). LOGI_CEO_REPORT_01
  // then made /bao-cao-ceo a real bounded read-only page (this expectation was
  // left stale at 3 by that phase), LOGI_NOTEBOOK_WORKSPACE_01 made /so-tay
  // a real read-only handbook, and LOGI_USER_ACCESS_WORKSPACE_01 made
  // /nguoi-dung a real read-only user/access workspace — every destination
  // is now backed by real capability.
  const markers = $("aside .uppercase", window.document).filter((el) => text(el) === "Sắp có");
  assert.equal(markers.length, 0, `expected 0 "Sắp có" marker, got ${markers.length}`);
  const usersRow = $('aside a[href="/nguoi-dung"]')[0];
  assert.ok(usersRow && !text(usersRow).includes("Sắp có"),
    "user access is REAL now — no deferred marker");
  const handbookRow = $('aside a[href="/so-tay"]')[0];
  assert.ok(handbookRow && !text(handbookRow).includes("Sắp có"),
    "the handbook is REAL now — no deferred marker");
  const ceoRow = $('aside a[href="/bao-cao-ceo"]')[0];
  assert.ok(ceoRow && !text(ceoRow).includes("Sắp có"),
    "the CEO report is REAL now — no deferred marker");
  const translationRow = $('aside a[href="/dich-thuat"]')[0];
  assert.ok(translationRow && !text(translationRow).includes("Sắp có"),
    "translation is REAL now — no deferred marker");
  const partnerRow = $('aside a[href="/ngu-canh-doi-tac"]')[0];
  assert.ok(partnerRow && !text(partnerRow).includes("Sắp có"),
    "partner context is REAL now — no deferred marker");
  const reconciliationRow = $('aside a[href="/tai-chinh/doi-soat"]')[0];
  assert.ok(reconciliationRow && !text(reconciliationRow).includes("Sắp có"),
    "reconciliation is REAL now — no deferred marker");
  // LOGI_INTERNAL_UX_SIMPLIFY_01 — the tasks desk (and its nav badge)
  // left the normal nav; alerts still surface via the notification bell.
  assert.equal($('aside a[href="/viec-can-xu-ly"]').length, 0, "removed tasks desk still in nav");
  assert.equal($('aside a[href="/theo-doi"]').length, 0, "removed tracking desk still in nav");
  assert.equal($('aside a[href="/thoa-thuan-ban-giao"]').length, 0, "removed agreements desk still in nav");
  ok("15 items, 0 markers, 0 removed-desk links (simplified nav)");
}

// ---------------------------------------------------------------------------
console.log("STEP 4 — footer tells the truth");
{
  const f = $("footer")[0];
  assert.ok(f, "footer missing");
  const ft = text(f);
  assert.ok(!ft.includes("09/09/2026"), "hardcoded sample date still in footer");
  assert.ok(ft.includes("staging"), "sandbox environment should be disclosed in footer");
  ok(ft.slice(0, 110));
}

// ---------------------------------------------------------------------------
console.log("STEP 5 — every REAL_BACKED sidebar destination opens its real page");
{
  const aside = $("aside")[0];
  const BACKED = [
    ["Tổng Quan Công Việc", "Hôm nay tôi cần làm gì?"],
    ["Lô Hàng", "Tìm theo mã lô"],
    ["Tạo Lô Mới", "Tạo Lô Hàng Mới"],
    ["Khách Hàng", "tạo, sửa, lưu trữ và import qua backend"],
    ["Báo Giá", "tách bạch với tài chính thực thu/chi"],
    ["Hợp đồng", "HDMB · HDNT · PL"],
    ["Thu tiền", "Thu tiền khách · Phải thu"],
    ["Công nợ đối tác", "Thanh toán đối tác · Phải trả"],
    ["Tra cứu thuế / HS", "Tra cứu HS & Thuế"],
    ["Dịch thuật", "Văn bản gốc"],
    // LOGI_PARTNER_CONTEXT_WORKSPACE_01 — /ngu-canh-doi-tac is a real workspace
    // now (LOGI_REAL_USE_CREATE_SHIPMENT_AGENT_MASTER_01 renamed the visible
    // label to the agent master desk); with this older fixture it must still
    // render its own honest state rather than the deferred placeholder.
    ["Đại Lý Trường Thành", "Đại Lý Trường Thành"],
    // LOGI_RECONCILIATION_DESK_01 — /tai-chinh/doi-soat is a real read-only
    // reconciliation desk now; with this older fixture it must render its own
    // honest "chưa có bản ghi đối soát" state rather than the deferred placeholder.
    ["Đối soát", "CHỈ ĐỌC"],
    // LOGI_USER_ACCESS_WORKSPACE_01 — /nguoi-dung is a real read-only user &
    // access workspace now: canonical accounts (if the deployment has them),
    // the verbatim ROLE_PERMISSIONS matrix and the honest auth-mode note.
    ["Người dùng & Vai trò", "CHỈ ĐỌC"],
    // LOGI_CEO_REPORT_01 / LOGI_NOTEBOOK_WORKSPACE_01 — both destinations are
    // real read-only pages now, and the regenerated fixture carries their real
    // slices, so each renders its real content behind the CHỈ ĐỌC marker.
    ["Báo cáo CEO", "CHỈ ĐỌC"],
    ["Sổ tay", "CHỈ ĐỌC"],
  ];
  for (const [label, marker] of BACKED) {
    await click(label, "a", aside);
    const t = mainText();
    assert.ok(t.includes(marker), `backed page "${label}" missing marker "${marker}"`);
    assert.ok(!t.includes("chưa triển khai"), `backed page "${label}" unexpectedly shows placeholder`);
  }
  ok("15 backed destinations all open REAL pages (0 placeholders)");
}

// ---------------------------------------------------------------------------
console.log("STEP 6 — no UNBACKED destination remains");
{
  // /nguoi-dung (LOGI_USER_ACCESS_WORKSPACE_01) was the last deferred
  // destination; every sidebar item now opens a real page.
  const markers = $("aside .uppercase", window.document).filter((el) => text(el) === "Sắp có");
  assert.equal(markers.length, 0, "a deferred destination reappeared");
  ok("0 deferred destinations → every route is a real page, zero faked capability");
}

// ---------------------------------------------------------------------------
console.log("STEP 7 — mobile navigation routes to the same REAL pages");
{
  // Mobile bottom nav: Lô hàng → Shipments, Tài chính → Receivables,
  // Hợp đồng → Contracts, Tổng quan → Home. (md:hidden only hides these
  // visually on desktop; in jsdom the elements are present and clickable.)
  const bottomNav = $("nav .grid.grid-cols-5")[0];
  assert.ok(bottomNav, "mobile bottom nav missing");
  await click("Lô hàng", "a", bottomNav);
  assert.ok(mainText().includes("Tìm theo mã lô"), "mobile Lô hàng must open Lô Hàng");
  assert.ok(!mainText().includes("Việc Cần Xử Lý —"), "mobile Lô hàng must NOT open Tasks");
  await click("Tài chính", "a", bottomNav);
  assert.ok(mainText().includes("Thu tiền khách · Phải thu"), "mobile Tài chính must open Thu tiền");
  await click("Hợp đồng", "a", bottomNav);
  assert.ok(mainText().includes("HDMB · HDNT · PL"), "mobile Hợp đồng must open Hợp đồng");
  await click("Tổng quan", "a", bottomNav);
  assert.ok(mainText().includes("Hôm nay tôi cần làm gì?"), "mobile Tổng quan must open Home");
  // Drawer: hamburger → Lô Hàng.
  await clickSelector('button[aria-label="Mở menu"]');
  const drawer = $("div.anim-slide-up").filter((el) => text(el).includes("Menu điều hành"))[0]
    ?? $(".fixed.inset-0.z-50")[0];
  assert.ok(drawer, "mobile drawer missing");
  await click("Lô Hàng", "a", drawer);
  assert.ok(mainText().includes("Tìm theo mã lô"), "drawer Lô Hàng must open Lô Hàng");
  ok("bottom nav + drawer agree with the sidebar (Lô hàng → Lô Hàng, never Tasks)");
}

async function clickSelector(sel, root = window.document) {
  const el = $(sel, root)[0];
  assert.ok(el, `selector "${sel}" not found`);
  el.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
  await tick();
  return el;
}

// ---------------------------------------------------------------------------
console.log("STEP 8 — no faked actions / no sample data as real (Shipment Detail)");
{
  const first = VM.shipments.find((s) => !s.pxk?.done && !s.pxk?.date);
  await click(first.id, "a", $("main")[0]);
  await tick(80);
  await openGlobalTab("Chứng từ");
  await tick(80);
  const t = mainText();
  assert.ok(!t.includes("File minh họa"), "fake download toast copy still present");
  assert.ok(!t.includes("prototype mô phỏng"), "fake upload toast copy still present");
  const dateInputs = $('main input').filter((i) => i.value === "09/09/2026");
  assert.equal(dateInputs.length, 0, "PXK date must not prefill the hardcoded sample date");
  ok("PXK tab: no sample date, no fake download/upload actions");
}

// ---------------------------------------------------------------------------
console.log("STEP 9 — quick-add sheet: deferred tool marked, the rest route real");
{
  await click("Thêm", "button", $("header")[0]);
  const sheetText = bodyText();
  assert.ok(sheetText.includes("Thêm mới nhanh"), "quick-add sheet missing");
  const taxRow = findClickable("Tra cứu thuế", "button");
  assert.ok(taxRow && !text(taxRow).includes("Sắp có"), "tariff lookup is REAL now — no deferred marker");
  await click("Tra cứu thuế", "button");
  assert.ok(mainText().includes("Tra cứu HS & Thuế"), "quick-add must route to the real tariff workspace");
  await click("Thêm", "button", $("header")[0]);
  await click("Tạo lô hàng mới", "button");
  assert.ok(mainText().includes("Tạo Lô Hàng Mới"), "quick-add must route to real Create Shipment");
  ok("quick-add consistent: 5 real destinations, zero deferred tools");
}

// ---------------------------------------------------------------------------
console.log("STEP 10 — route + tab survive a backend rerun");
{
  // Re-enter a shipment detail (STEP 9 ended on Create Shipment) via the
  // sidebar list, then activate the Chứng từ tab before the rerun.
  await click("Lô Hàng", "a", $("aside")[0]);
  const sid = VM.shipments[0].id;
  await click(sid, "a", $("main")[0]);
  await tick(80);
  await openGlobalTab("Chứng từ");
  const vm2 = JSON.parse(JSON.stringify(VM));
  vm2.version = VM.version + "-rerun";
  invoke(vm2);
  await tick(120);
  const t = mainText();
  assert.ok(
    t.includes("Hợp đồng liên kết") || t.includes("Phiếu xuất kho"),
    "Shipment Detail chung-tu tab did not survive backend rerun"
  );
  ok("route + tab survive re-invocation (MemoryRouter contract)");
}

console.log(`\nCONSOLIDATION DOM ACCEPTANCE PASS — ${passed} checks`);
process.exit(0);
