// ============================================================================
// Phase A DOM acceptance — runs the REAL production bundle
// (component/dist/logi-shell.js) in a DOM (jsdom) and drives it with real
// DOM events, simulating the exact Streamlit Components v2 invocation
// contract: `mount({data, parentElement, setTriggerValue})` is re-invoked
// with new data on every backend rerun (same parentElement).
//
// This is the mechanical acceptance checklist for Phase A:
//   1. boot without BidiComponent Error / "process is not defined"
//   2. header renders (logo, subtitle, search, chip, bell, Thêm)
//   3. sidebar renders (5 donor groups + all items)
//   4. click Tổng Quan Công Việc → Home
//   5. simplified nav: removed desks absent from sidebar/drawer; the
//      notification entry lands on the surviving work surface (/lo-hang).
//   6. click Lô Hàng → Shipments
//   7. open LO-0306 → Shipment Detail
//   8. click all five donor tabs
//   9. global search finds a shipment
//  10. Quick Add opens/closes
//  11. Notifications opens/closes
//  12. route + active tab survive a backend rerun (re-invocation w/ new data)
//  +  typed v2 event contract (shipment_update payload on save actions)
//
// Run: node tests/component/dom_acceptance_phase_a.mjs
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
  readFileSync(path.join(ROOT, "tests/component/fixtures/view_model_phase_b.json"), "utf8")
);

// ---------------------------------------------------------------------------
// jsdom environment (browser globals for the bundle + React)
// ---------------------------------------------------------------------------

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
  "HTMLElement",
  "HTMLInputElement",
  "HTMLTextAreaElement",
  "HTMLSelectElement",
  "HTMLAnchorElement",
  "Event",
  "CustomEvent",
  "MouseEvent",
  "KeyboardEvent",
  "Node",
  "MutationObserver",
  "getComputedStyle",
]) {
  globalThis[k] = window[k];
}
if (!globalThis.MessageChannel) globalThis.MessageChannel = window.MessageChannel;
window.HTMLElement.prototype.scrollIntoView = () => {};
window.URL.createObjectURL = () => "blob:mock-url";
window.URL.revokeObjectURL = () => {};

const tick = (ms = 60) => new Promise((r) => setTimeout(r, ms));

// ---------------------------------------------------------------------------
// DOM helpers
// ---------------------------------------------------------------------------

const $ = (sel, root = window.document) => [...root.querySelectorAll(sel)];
const text = (el) => (el.textContent || "").replace(/\s+/g, " ").trim();

function findClickable(needle, sel = "a,button", root = window.document) {
  const els = $(sel, root);
  return (
    els.find((el) => text(el) === needle) ||
    els.find((el) => text(el).startsWith(needle)) ||
    null
  );
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

function type(input, value) {
  const proto =
    input.tagName === "TEXTAREA"
      ? window.HTMLTextAreaElement.prototype
      : input.tagName === "SELECT"
        ? window.HTMLSelectElement.prototype
        : window.HTMLInputElement.prototype;
  Object.getOwnPropertyDescriptor(proto, "value").set.call(input, value);
  input.dispatchEvent(new window.Event("input", { bubbles: true }));
  input.dispatchEvent(new window.Event("change", { bubbles: true }));
}

const bodyText = () => text(window.document.body);
let passed = 0;
function ok(name) {
  passed += 1;
  console.log(`  ✓ ${name}`);
}

// ---------------------------------------------------------------------------
// Simulated Streamlit v2 component invocation
// ---------------------------------------------------------------------------

const host = window.document.createElement("div");
window.document.body.appendChild(host);

const triggers = [];
function invoke(data) {
  // Exactly what the Streamlit frontend does: re-invoke the module default
  // export with the fresh data + a fresh setTriggerValue, same parentElement.
  return mountRef.current({
    name: "logi_shell",
    data,
    parentElement: host,
    setTriggerValue: (event, value) => triggers.push({ event, value }),
  });
}
const mountRef = { current: null };
const bundlePath = path.join(ROOT, "component/dist/logi-shell.js");

// ---------------------------------------------------------------------------
// STEP 1 — boot (this is where "process is not defined" would throw)
// ---------------------------------------------------------------------------

console.log("STEP 1 — boot production bundle");
{
  const mod = await import(bundlePath);
  assert.equal(typeof mod.default, "function", "bundle must default-export the mount function");
  mountRef.current = mod.default;
  invoke(VM);
  await tick(120);
  const t = bodyText();
  assert.ok(!t.includes("process is not defined"), "process is not defined leaked");
  assert.ok(!t.includes("BidiComponent Error"), "BidiComponent Error rendered");
  assert.ok(t.includes("TRƯỜNG THÀNH"), "app did not render");
  ok("no 'process is not defined', no BidiComponent Error, app rendered");
}

// ---------------------------------------------------------------------------
// STEP 2 — header
// ---------------------------------------------------------------------------

console.log("STEP 2 — header parity");
{
  const header = $("header")[0];
  assert.ok(header, "header missing");
  const ht = text(header);
  // DISPLAY_COMPANY_NAME truth (LOGI_COMPANY_IDENTITY_TRUTH_01): the operating
  // brand arrives via the vm `environment.displayName` channel — never a
  // hard-coded bundle constant.
  assert.ok(VM.environment?.displayName, "fixture must carry environment.displayName");
  for (const s of ["TRƯỜNG THÀNH", `${VM.environment.displayName} · Nội bộ`, "PROTOTYPE"]) {
    assert.ok(ht.includes(s), `header missing "${s}"`);
  }
  assert.ok(!ht.includes("Phú Anh"), "header must not present Phú Anh as the operating brand");
  const search = $('input[placeholder^="Tìm mã lô"]', header);
  assert.ok(search, "global search input missing");
  const bell = $('button[aria-label="Thông báo"]', header);
  assert.ok(bell, "notification bell missing");
  assert.ok(findClickable("Thêm", "button", header), "Thêm button missing");
  assert.ok(ht.includes("Thu Hằng"), "user chip missing");
  ok("logo + subtitle + search + user chip + bell + Thêm all present");
}

// ---------------------------------------------------------------------------
// STEP 3 — sidebar
// ---------------------------------------------------------------------------

console.log("STEP 3 — sidebar parity");
{
  const aside = $("aside")[0];
  assert.ok(aside, "sidebar aside missing");
  const at = text(aside);
  for (const g of ["VẬN HÀNH", "KINH DOANH & ĐỐI TÁC", "TÀI CHÍNH & ĐỐI SOÁT", "CÔNG CỤ", "QUẢN TRỊ"]) {
    assert.ok(at.includes(g), `sidebar group missing: ${g}`);
  }
  // LOGI_INTERNAL_UX_SIMPLIFY_01 — removed desks are gone from the nav;
  // "Báo giá" is now "Báo Giá".
  for (const it of [
    "Tổng Quan Công Việc",
    "Lô Hàng",
    "Tạo Lô Mới",
    "Khách Hàng",
    "Báo Giá",
    "Hợp đồng",
    "Thu tiền",
    "Đối soát",
    "Công nợ đối tác",
    "Báo cáo CEO",
    "Tra cứu thuế / HS",
    "Sổ tay",
    "Dịch thuật",
    "Người dùng & Vai trò",
  ]) {
    assert.ok(at.includes(it), `sidebar item missing: ${it}`);
  }
  ok("5 groups + 14 items present (3 desks removed, quote renamed)");
}

// ---------------------------------------------------------------------------
// STEP 4 — click Tổng Quan → Home
// ---------------------------------------------------------------------------

console.log("STEP 4 — click Tổng Quan Công Việc");
{
  await click("Tổng Quan Công Việc", "a", $("aside")[0]);
  const t = bodyText();
  // LOGI_FRONTEND_WORKFLOW_OVERHAUL_01 — ONE priority area, ONE snapshot:
  // the old duplicate "VIỆC TIẾP THEO"/"Chỉ số vận hành hôm nay" tile rows
  // are replaced by a single "Ảnh vận hành hôm nay" snapshot.
  assert.ok(
    t.includes("Ưu tiên bây giờ:") || t.includes("Không có việc khẩn"),
    "Home priority area missing"
  );
  assert.ok(t.includes("Quá hạn và sắp tới hạn"), "deadline list missing");
  assert.ok(t.includes("Trạng thái các lô đang chạy"), "running lots missing");
  assert.ok(t.includes("Ảnh vận hành hôm nay"), "operational snapshot missing");
  assert.ok(t.includes("Tiền & hồ sơ cần chú ý"), "money/docs attention missing");
  assert.ok(!t.includes("VIỆC TIẾP THEO"), "duplicated tile row must be gone");
  assert.ok(!t.includes("Chỉ số vận hành hôm nay"), "duplicated KPI row must be gone");
  ok("Home rendered after real click (single priority + single snapshot)");
}

// ---------------------------------------------------------------------------
// STEP 5 — simplified nav (tasks desk removed from normal navigation)
// ---------------------------------------------------------------------------

console.log("STEP 5 — simplified nav: no removed desks; notif lands on /lo-hang");
{
  // LOGI_INTERNAL_UX_SIMPLIFY_01 — sidebar carries no removed-desk link.
  for (const href of ["/viec-can-xu-ly", "/theo-doi", "/thoa-thuan-ban-giao"]) {
    assert.equal($(`aside a[href="${href}"]`).length, 0, `sidebar still links ${href}`);
  }
  // Mobile drawer agrees.
  await clickSelector('button[aria-label="Mở menu"]');
  const drawer = $("div.anim-slide-up").filter((el) => text(el).includes("Menu điều hành"))[0]
    ?? $(".fixed.inset-0.z-50")[0];
  assert.ok(drawer, "mobile drawer missing");
  for (const href of ["/viec-can-xu-ly", "/theo-doi", "/thoa-thuan-ban-giao"]) {
    assert.equal($(`a[href="${href}"]`, drawer).length, 0, `drawer still links ${href}`);
  }
  await click("Lô Hàng", "a", drawer);
  // Notification drawer entry lands on the surviving work surface.
  await clickSelector("header button[aria-label='Thông báo']");
  await click("Mở Lô Hàng", "button");
  assert.ok(bodyText().includes("Tìm theo mã lô"), "notif entry must open Lô Hàng");
  ok("sidebar + drawer drop the 3 desks; notif opens the surviving surface");
}

console.log("STEP 6 — click Lô Hàng");
{
  await click("Lô Hàng", "a", $("aside")[0]);
  const t = bodyText();
  assert.ok(t.includes("Tìm theo mã lô"), "Shipments page missing");
  const rows = $("table.tbl tbody tr");
  assert.equal(rows.length, VM.shipments.length, `expected ${VM.shipments.length} shipment rows, got ${rows.length}`);
  for (const id of VM.shipments.map((x) => x.id)) {
    assert.ok(t.includes(id), `shipment ${id} missing`);
  }
  ok(`Shipments rendered with ${VM.shipments.length} real lots`);
}

// ---------------------------------------------------------------------------
// STEP 7 — open LO-0306 → Shipment Detail
// ---------------------------------------------------------------------------

console.log("STEP 7 — open LO-0306");
{
  await click("LO-0306", "a", $("table.tbl")[0]);
  const h1 = $("h1")[0];
  assert.equal(text(h1), "LO-0306", `detail header wrong: ${text(h1)}`);
  const t = bodyText();
  assert.ok(t.includes("Chờ thông quan"), "status badge missing");
  assert.ok(t.includes("An Phát"), "customer missing");
  // Real readiness facts: the chip and the box must agree on one count.
  const lot = VM.shipments.find((x) => x.id === "LO-0306");
  const missing = lot.missingDocs.length;
  assert.ok(missing > 0, "expected LO-0306 to have genuinely missing facts");
  assert.ok(t.includes(`Thiếu ${missing} thông tin`), "missing-info chip missing");
  // LOGI_SHIPMENT_GLANCEABLE_SUPPORT_UX_01 · OWNER_RUNTIME_UAT_REPAIR (issue #86):
  // the "Đang thiếu N thông tin — bấm để bổ sung ngay" block no longer occupies
  // the page by default. The COUNT is still visible (same s.missingDocs.length,
  // no second counter) and expanding the disclosure shows the same rows.
  assert.ok(!t.includes("Đang thiếu"), "OLD BEHAVIOUR: the missing-info block is expanded by default");
  await click(`Thiếu ${missing} thông tin`, "button");
  const tExpanded = bodyText();
  for (const fact of lot.missingDocs) {
    assert.ok(tExpanded.includes(fact), `missing fact not listed after expanding: ${fact}`);
  }
  ok(`Shipment Detail LO-0306 rendered (status, ${missing} real missing facts behind one disclosure)`);

  // "Bổ sung ngay" must route to the tab that really owns the fact. The Phase
  // A mapping keyed off label strings the real checklist never emits, so every
  // row fell through to Tài chính. Assert the real labels route correctly.
  // Each tab button renders a desktop label span plus a mobile short-label
  // span; read only the desktop one so the comparison is unambiguous.
  const activeTab = () => {
    const tabs = $("button", window.document.getElementById("workspace-tabs"));
    const on = tabs.find((b) => b.className.includes("bg-[#0f2a4a]"));
    return on ? text($("span", on)[0]) : null;
  };
  const expectRoute = [
    ["Số tờ khai nhập khẩu", "Nhập khẩu & Giao hàng"],
    ["Xe giao VN + tài xế", "Vận chuyển & Hàng hóa"],
    ["Xác nhận đã giao hàng", "Nhập khẩu & Giao hàng"],
  ];
  for (const [fact, expected] of expectRoute) {
    // back to the operational tab so every assertion starts from a known state
    await click("Vận chuyển & Hàng hóa", "button", window.document.getElementById("workspace-tabs"));
    const box = $("div").find((d) => d.className.includes("border-dashed") && text(d).includes("Thiếu " + fact));
    assert.ok(box, `missing box for ${fact} not found`);
    const btn = $("button", box).find((b) => text(b).includes("Bổ sung ngay"));
    assert.ok(btn, `Bổ sung ngay button missing for ${fact}`);
    btn.click();
    await tick(160);
    assert.equal(activeTab(), expected, `"${fact}" routed to ${activeTab()}, expected ${expected}`);
  }
  // restore the default tab so the next step starts from a clean state
  await click("Vận chuyển & Hàng hóa", "button", window.document.getElementById("workspace-tabs"));
  ok("Bổ sung ngay routes each real missing fact to the tab that owns it");
}

// ---------------------------------------------------------------------------
// STEP 8 — all Shipment Detail tabs
// ---------------------------------------------------------------------------

console.log("STEP 8 — Shipment Detail tabs");
{
  const tabs = {
    "Vận chuyển & Hàng hóa": "CÁC CHẶNG VẬN CHUYỂN",
    "Xuất khẩu": "Nhà máy & xuất khẩu",
    "Nhập khẩu & Giao hàng": "Tờ khai & thuế nhập khẩu",
    "Tài chính / Công nợ": "Phải thu khách hàng (VND)",
    "Quy trình & Chứng từ": "Phiếu xuất kho (PXK)",
    "Lịch sử": "Dòng thời gian — LO-0306",
  };
  const tabRoot = window.document.getElementById("workspace-tabs");
  assert.ok(tabRoot, "workspace tabs missing");
  // default tab
  assert.ok(bodyText().includes(tabs["Vận chuyển & Hàng hóa"]), "default tab content missing");
  ok("tab 1: Vận chuyển & Hàng hóa (default)");
  for (const [label, marker] of Object.entries(tabs)) {
    if (label === "Vận chuyển & Hàng hóa") continue;
    // LOGI_SHIPMENT_GLANCEABLE_SUPPORT_UX_01 · OWNER_RUNTIME_UAT_REPAIR (§5).
    // This lot is DAP — a D-family Incoterms rule — so "Xuất khẩu" is now LOCKED
    // BY DEFAULT as an advisory. The capability is not removed: a locked tab must
    // be visibly marked, must NOT open silently, must explain itself, and the
    // manual unlock has to be immediately obvious. Only after unlocking may the
    // export workspace be read. No data changes: this is a UI gate only.
    if (label === "Xuất khẩu") {
      const exportTab = tabRoot.querySelector('[data-testid="export-tab"]');
      assert.ok(exportTab, "the Xuất khẩu tab control is missing");
      assert.equal(exportTab.getAttribute("data-locked"), "true",
        "a D-family lot must show the export tab locked by default");
      await click("Xuất khẩu", "button", tabRoot);
      assert.ok(!bodyText().includes(marker),
        "OLD BEHAVIOUR: a locked export tab opened anyway");
      const notice = window.document.querySelector('[data-testid="export-lock-notice"]');
      assert.ok(notice, "the lock must explain itself instead of doing nothing");
      assert.ok(text(notice).includes("MỞ KHÓA XUẤT KHẨU"),
        "the manual unlock must be offered right next to the explanation");
      await click("MỞ KHÓA XUẤT KHẨU", "button");
      assert.ok(bodyText().includes(marker), "the unlock must actually reach the workspace");
      assert.equal(window.document.querySelector('[data-testid="export-tab"]')?.getAttribute("data-locked") ?? null, null,
        "after the manual unlock the tab stays unlocked for this session");
      ok("tab: Xuất khẩu — advisory F/C/D lock, explained, manually unlockable");
      continue;
    }
    await click(label, "button", tabRoot);
    assert.ok(bodyText().includes(marker), `tab ${label} content missing`);
    ok(`tab: ${label}`);
  }
}

// ---------------------------------------------------------------------------
// STEP 9 — global search finds a shipment
// ---------------------------------------------------------------------------

console.log("STEP 9 — global search");
{
  const search = $('input[placeholder^="Tìm mã lô"]', $("header")[0])[0];
  search.dispatchEvent(new window.FocusEvent("focusin", { bubbles: true }));
  type(search, "an phát");
  await tick();
  const t = bodyText();
  assert.ok(t.includes("LO-0306 · An Phát JSC"), "search result for 'an phát' missing");
  const found = findClickable("LO-0306 · An Phát JSC", "button");
  assert.ok(found, "search result button missing");
  found.click();
  await tick();
  assert.equal(text($("h1")[0]), "LO-0306", "search navigation failed");
  // empty-state hint
  const search2 = $('input[placeholder^="Tìm mã lô"]', $("header")[0])[0];
  search2.dispatchEvent(new window.FocusEvent("focusin", { bubbles: true }));
  type(search2, "zzzzzz");
  await tick();
  assert.ok(bodyText().includes("Không tìm thấy"), "search empty state missing");
  search2.dispatchEvent(new window.Event("blur", { bubbles: true }));
  ok("search finds LO-0306 · An Phát JSC, navigates, shows empty state");
}

// ---------------------------------------------------------------------------
// STEP 10 — Quick Add opens/closes
// ---------------------------------------------------------------------------

console.log("STEP 10 — Quick Add");
{
  const header = $("header")[0];
  await click("Thêm", "button", header);
  assert.ok(bodyText().includes("Thêm mới nhanh"), "quick-add sheet missing");
  for (const a of ["Tạo lô hàng mới", "Tạo hợp đồng mới", "Tạo báo giá", "Ghi nhận thanh toán", "Tra cứu thuế / HS"]) {
    assert.ok(findClickable(a, "button"), `quick-add action missing: ${a}`);
  }
  // close via the X inside the sheet (stable id from SheetDialog)
  const sheet = window.document.getElementById("quick-add-sheet");
  assert.ok(sheet, "quick-add sheet element missing");
  const closeBtn = $("button", sheet).find((b) => b.querySelector("svg") && (b.getAttribute("aria-label") || "").includes("Đóng"));
  assert.ok(closeBtn, "quick-add close button missing");
  closeBtn.click();
  await tick();
  assert.ok(!bodyText().includes("Chọn việc muốn làm"), "quick-add did not close");
  ok("Quick Add opens with 5 actions and closes");
}

// ---------------------------------------------------------------------------
// STEP 11 — Notifications opens/closes
// ---------------------------------------------------------------------------

console.log("STEP 11 — Notifications");
{
  await clickSelector("header button[aria-label='Thông báo']");
  const t = bodyText();
  assert.ok(t.includes(`Thông báo · ${VM.notifications.length} chưa đọc`), "notifications drawer missing");
  for (const n of VM.notifications.map((x) => x.title)) {
    assert.ok(t.includes(n), `notification missing: ${n}`);
  }
  // close: X button inside the drawer header
  const drawer = $("div").find((d) => d.className.includes("w-[380px]"));
  const closeBtn = $("button", drawer).find((b) => b.querySelector("svg"));
  assert.ok(closeBtn, "notif close button missing");
  closeBtn.click();
  await tick();
  assert.ok(!bodyText().includes(`Thông báo · ${VM.notifications.length} chưa đọc`), "notifications did not close");
  ok(`Notifications opens with ${VM.notifications.length} items and closes`);
}

// ---------------------------------------------------------------------------
// STEP 12 — route + tab survive a backend rerun (data re-invocation)
// ---------------------------------------------------------------------------

console.log("STEP 12 — rerender survival");
{
  // Navigate to LO-0306 detail and switch to the Tài chính tab.
  await click("Lô Hàng", "a", $("aside")[0]);
  await click("LO-0306", "a", $("table.tbl")[0]);
  const tabRoot = window.document.getElementById("workspace-tabs");
  await click("Tài chính / Công nợ", "button", tabRoot);
  assert.ok(bodyText().includes("Phải thu khách hàng (VND)"), "tab switch before rerun failed");

  // Simulate the backend rerun: Streamlit re-invokes the mount with fresh
  // data (LO-0306 updated) on the SAME parentElement — no DOM reset.
  const vm2 = JSON.parse(JSON.stringify(VM));
  const s = vm2.shipments.find((x) => x.id === "LO-0306");
  s.timeline = [
    ...s.timeline,
    { time: "09/09 10:00", title: "Rerun check — timeline entry appended", tone: "blue" },
  ];
  s.updated = "09/09/2026 10:00";
  vm2.version = "rerun-0001";
  invoke(vm2);
  await tick(120);

  assert.equal(host.children.length, 1, "component re-mounted (DOM reset!)");
  assert.equal(text($("h1")[0]), "LO-0306", "route lost across rerun");
  assert.ok(bodyText().includes("Phải thu khách hàng (VND)"), "active tab lost across rerun");
  assert.ok(bodyText().includes("09/09/2026 10:00"), "updated data not visible after rerun");
  ok("route + active tab survive backend rerun; new data rendered");
}

// ---------------------------------------------------------------------------
// STEP 13 — typed v2 event contract (Phase B write events)
// ---------------------------------------------------------------------------

console.log("STEP 13 — v2 typed events");
{
  // LO-0299: confirm delivery → modal → ĐÃ GIAO
  await click("Lô Hàng", "a", $("aside")[0]);
  await click("LO-0299", "a", $("table.tbl")[0]);
  const tabRoot = window.document.getElementById("workspace-tabs");
  await click("Nhập khẩu & Giao hàng", "button", tabRoot);
  await click("✅ XÁC NHẬN ĐÃ GIAO HÀNG", "button");
  assert.ok(bodyText().includes("Xác nhận đã giao LO-0299?"), "delivery modal missing");
  await click("✅ ĐÃ GIAO", "button");
  // Phase B: the UI no longer flips the state locally. It emits ONE typed
  // delivery_confirm event; the delivered banner appears only after the
  // backend writes, audits and returns a fresh read.
  assert.ok(bodyText().includes("Đã gửi xác nhận giao hàng LO-0299"), "delivery dispatch toast missing");
  const ev = triggers.find((t) => t.event === "delivery_confirm");
  assert.ok(ev, "delivery_confirm trigger not emitted");
  assert.ok(ev.value && typeof ev.value.seq === "number", "trigger payload missing seq");
  assert.equal(ev.value.event, "delivery_confirm", "trigger payload missing event name");
  assert.equal(ev.value.payload.shipmentId, "LO-0299", "trigger payload missing shipment id");
  assert.ok(ev.value.payload.deliveredAt, "trigger payload missing deliveredAt");
  ok("delivery save → delivery_confirm {seq, event, payload.shipmentId} emitted");

  // LO-0308: add a canonical truck leg and truck unit (missing-info flow)
  await click("Lô Hàng", "a", $("aside")[0]);
  await click("LO-0308", "a", $("table.tbl")[0]);
  await click("+ THÊM CHẶNG", "button");
  const leg = $("details")[0];
  assert.ok(leg, "new transport leg missing on LO-0308");
  $("summary", leg)[0].click();
  await tick();
  await click("+ Thêm xe", "button", leg);
  const plate = $('input[data-field="unit-number"]', leg)[0];
  assert.ok(plate, "canonical truck plate input missing on LO-0308");
  type(plate, "粤B·20T99");
  await click("LƯU CÁC CHẶNG", "button");
  assert.ok(bodyText().includes("Đã gửi các chặng vận chuyển"), "transport save toast missing");
  const evs = triggers.filter((t) => t.event === "shipment_transport_save");
  assert.equal(evs.length, 1, `expected 1 shipment_transport_save event, got ${evs.length}`);
  assert.ok(evs[0].value.seq > ev.value.seq, "event seq must increase");
  assert.equal(evs[0].value.payload.shipmentId, "LO-0308", "transport save payload wrong shipment");
  assert.equal(evs[0].value.payload.transportLegs[0].units[0].number, "粤B·20T99", "truck plate payload wrong");
  ok("transport save → shipment_transport_save with ordered legs/units emitted");
}

// ---------------------------------------------------------------------------
// ---------------------------------------------------------------------------
// STEP 14 — Phase B: Create Shipment (real workflow)
// ---------------------------------------------------------------------------

console.log("STEP 14 — Create Shipment");
{
  await click("Tạo Lô Mới", "a", $("aside")[0]);
  const t14 = bodyText();
  assert.ok(t14.includes("Tạo Lô Hàng Mới"), "create page missing");
  assert.ok(t14.includes("Chọn báo giá đã chốt"), "quote prefill section missing");
  // Pick an accepted quote: this is the real prefill path (known values are
  // carried over so only the genuinely missing fields are asked for).
  const quote = VM.quotes.find((q) => (q.status || "").toLowerCase().includes("accept"));
  assert.ok(quote, "seed has no accepted quote to prefill from");
  assert.ok(t14.includes(quote.id), `accepted quote ${quote.id} not offered`);
  await click(quote.id, "button");
  assert.ok(bodyText().includes("Đã nạp báo giá " + quote.id), "quote prefill toast missing");
  assert.ok(bodyText().includes("Quote Estimate chỉ dùng để điền trước"), "quote/actual separation missing");

  const code = $('input[placeholder="LO-0470"]')[0];
  assert.ok(code, "shipment code input missing");
  type(code, "LO-0470");
  // The customer field is now the SearchPicker (LOGI_QUOTE_COST_WORKFLOW_UX_01),
  // so the contract select is located by its OWN options rather than by index.
  const contractSelect = $("select").find((sel) =>
    [...sel.options].some((o) => text(o).startsWith("HDMB-")));
  assert.ok(contractSelect, "contract select missing");

  // The prefill resolves the contract through the quote's canonical customerId,
  // so the lot is born linked to the contract that PXK later needs as a source.
  const expectedContract = VM.contracts.find((c) => c.customerId === quote.customerId);
  assert.ok(expectedContract, "fixture has no contract for the accepted quote's customer");
  assert.equal(contractSelect.value, expectedContract.id, "accepted quote must prefill the customer's contract");

  // Contract options must be distinguishable by CUSTOMER: `company` is the same
  // seller legal entity on every contract, so it cannot identify a row.
  assert.ok(contractSelect.textContent.includes(expectedContract.client),
    "contract option must name the customer, not only the shared seller entity");

  // Re-pick the customer through the SearchPicker (still one canonical id).
  $('[data-testid="create-customer-picker-toggle"]')[0]
    .dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
  await tick(80);
  const picked = $(`[data-testid="create-customer-picker-option-${VM.customers[0].id}"]`)[0];
  assert.ok(picked, "the first fixture customer must be offered by the picker");
  picked.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
  await tick(80);

  await click("TẠO LÔ HÀNG", "button");
  await tick();
  const created = triggers.filter((x) => x.event === "shipment_create");
  assert.equal(created.length, 1, `expected 1 shipment_create event, got ${created.length}`);
  assert.equal(created[0].value.payload.shipmentId, "LO-0470", "create payload wrong id");
  assert.equal(created[0].value.payload.customer, VM.customers[0].name, "create payload wrong customer");
  // The backend joins on the canonical customer key; sending the display name
  // used to store a bogus customer_id on the new lot.
  assert.equal(created[0].value.payload.customerId, VM.customers[0].id,
    "create payload must carry the canonical customerId");
  ok("Create Shipment → shipment_create {shipmentId, customerId, customer, contractId} emitted");
}

// ---------------------------------------------------------------------------
// STEP 15 — Phase B: Tracking (real transport facts, no fabricated GPS)
// ---------------------------------------------------------------------------

console.log("STEP 15 — removed tracking desk: former entries land on /lo-hang");
{
  // LOGI_INTERNAL_UX_SIMPLIFY_01 — the standalone tracking desk left the nav;
  // operational value stays reachable through Lô Hàng / shipment detail.
  await click("Tổng Quan Công Việc", "a", $("aside")[0]);
  await click("Tất cả lô", "a");
  assert.ok(bodyText().includes("Tìm theo mã lô"), "home exception link must open Lô Hàng");
  await click("Tổng Quan Công Việc", "a", $("aside")[0]);
  await click("MỞ DANH SÁCH LÔ", "a");
  assert.ok(bodyText().includes("Tìm theo mã lô"), "home docs card must open Lô Hàng");
  const dead = ["viec-can-xu-ly", "theo-doi", "thoa-thuan-ban-giao"].flatMap((slug) =>
    $(`a[href*="${slug}"]`).map((a) => a.getAttribute("href"))
  );
  assert.equal(dead.length, 0, `visible links still route to removed desks: ${dead.join(", ")}`);
  ok("former tracking/task entries open Lô Hàng; zero dead links");
}

console.log("STEP 16 — import tax clear semantics");
{
  // A shipment that already has canonical import tax stored.
  const vm3 = JSON.parse(JSON.stringify(VM));
  const lot = vm3.shipments.find((x) => x.id === "LO-0307");
  lot.importInfo.tax = 5000000;
  lot.importInfo.vat = 800000;
  lot.importInfo.regDate = "15/08/2026";
  invoke(vm3);
  await tick(120);

  await click("Lô Hàng", "a", $("aside")[0]);
  await click("LO-0307", "a", $("table.tbl")[0]);
  const tabRoot16 = window.document.getElementById("workspace-tabs");
  await click("Nhập khẩu & Giao hàng", "button", tabRoot16);

  const duty = window.document.getElementById("fld-duty");
  const vat = window.document.getElementById("fld-vat");
  const tkDate = window.document.getElementById("fld-tkdate");
  assert.ok(duty && vat && tkDate, "the three canonical inputs must be mounted");
  // The stored canonical values are what the operator sees.
  assert.equal(duty.value, "5000000", "stored import duty not rendered");
  assert.equal(vat.value, "800000", "stored import VAT not rendered");
  assert.equal(tkDate.value, "15/08/2026", "stored declaration date not rendered");

  const nextSave = () => {
    const evs = triggers.filter((t) => t.event === "shipment_field_save");
    return evs[evs.length - 1].value.payload;
  };

  // (8) UNTOUCHED — an ordinary save on this tab must not touch the three
  // fields. This is what stops a legacy `reg_date` read fallback from being
  // silently migrated into canonical `tk_date`.
  await click("💾 LƯU TỜ KHAI & THUẾ", "button");
  assert.ok(bodyText().includes("Đã lưu tờ khai 105588421330"), "import save toast missing");
  let fields = nextSave().fields;
  assert.equal(fields.tk_no, "105588421330", "declaration number must still be sent");
  for (const key of ["tk_date", "import_duty_amount", "import_vat_amount"]) {
    assert.ok(!(key in fields), `untouched ${key} must be omitted, got ${JSON.stringify(fields[key])}`);
  }
  ok("untouched canonical fields are omitted from the payload");

  // (1-3) CLEAR the import duty → the empty string must travel.
  type(duty, "");
  await click("💾 LƯU TỜ KHAI & THUẾ", "button");
  fields = nextSave().fields;
  assert.ok("import_duty_amount" in fields, "cleared import duty was dropped by the payload");
  assert.equal(fields.import_duty_amount, "", "cleared import duty must be sent as an empty string");
  // The clear is scoped: the VAT the operator did not touch is not sent.
  assert.ok(!("import_vat_amount" in fields), "an untouched VAT must not be sent alongside a clear");
  ok('cleared import duty → import_duty_amount: "" dispatched');

  // (6-7) CLEAR the import VAT and the declaration date together.
  type(vat, "");
  type(tkDate, "");
  await click("💾 LƯU TỜ KHAI & THUẾ", "button");
  fields = nextSave().fields;
  assert.equal(fields.import_vat_amount, "", "cleared import VAT must be sent as an empty string");
  assert.equal(fields.tk_date, "", "cleared declaration date must be sent as an empty string");
  ok('cleared import VAT + declaration date → "" dispatched for both');

  // (B) An active edit still sends the typed value, not a blank.
  type(duty, "4200000");
  await click("💾 LƯU TỜ KHAI & THUẾ", "button");
  fields = nextSave().fields;
  assert.equal(fields.import_duty_amount, "4200000", "an edited amount must be sent verbatim");
  ok("edited import duty → the typed amount is dispatched verbatim");
}

// ---------------------------------------------------------------------------
// STEP 17 — PR #22 pickup truck type remains editable through the canonical
// truck-unit projection. The old scalar writer remains backend-compatible,
// while the Shipment Detail has one operational source of truth.
// ---------------------------------------------------------------------------

console.log("STEP 17 — CN pickup truck type compatibility");
{
  const vm4 = JSON.parse(JSON.stringify(VM));
  const lot = vm4.shipments.find((x) => x.id === "LO-0306");
  lot.transportLegsStructured = false;
  lot.transportLegs = [{
    id: "legacy-primary-leg",
    sequence: 1,
    mode: "Truck",
    origin: lot.transport.pol,
    destination: lot.transport.pod,
    carrier: lot.transport.carrier,
    etd: "",
    eta: "",
    atd: "",
    ata: "",
    bookingNo: "",
    mbl: "",
    hbl: "",
    vessel: "",
    voyage: "",
    mawb: "",
    hawb: "",
    flightNo: "",
    units: [{
      id: "legacy-primary-unit",
      kind: "truck",
      number: lot.pickup.plate,
      typeSize: "17.5m · rộng 3m · tải ≤30t",
      sealNo: "",
      driverName: "",
      driverPhone: "",
    }],
  }];
  invoke(vm4);
  await tick(120);

  await click("Lô Hàng", "a", $("aside")[0]);
  await click("LO-0306", "a", $("table.tbl")[0]);
  const leg = $("details")[0];
  $("summary", leg)[0].click();
  await tick();

  const truck = $('input[data-field="unit-type-size"]', leg)[0];
  assert.ok(truck, "projected truck type input must be mounted");
  assert.ok(!truck.readOnly, "projected truck type must remain editable");
  assert.equal(truck.value, "17.5m · rộng 3m · tải ≤30t", "stored truck type not rendered");

  type(truck, "9.6m · tải 15t");
  await click("LƯU CÁC CHẶNG", "button");
  const evs = triggers.filter((t) => t.event === "shipment_transport_save");
  const payload = evs[evs.length - 1].value.payload;
  assert.equal(payload.transportLegs[0].units[0].type_size, "9.6m · tải 15t",
    "edited truck type must be sent verbatim in the canonical unit");
  assert.ok(!("pickup_truck_type" in payload), "structured save must not flatten back to the scalar field");
  ok("PR #22 truck type projects into the canonical unit and remains editable");
}

// ---------------------------------------------------------------------------
// STEP 18 — independent operational drafts survive unrelated readbacks.
// ---------------------------------------------------------------------------

console.log("STEP 18 — independent Cargo/Transport draft synchronization");
{
  const vm5 = JSON.parse(JSON.stringify(VM));
  const canonical = vm5.shipments.find((x) => x.id === "LO-0306");
  canonical.version = 100;
  canonical.transportLegsStructured = true;
  canonical.transportLegs = [{
    id: "sync-leg",
    sequence: 1,
    mode: "Truck",
    origin: "Factory",
    destination: "Warehouse",
    carrier: "Road Partner",
    etd: "2026-10-01",
    eta: "2026-10-02",
    atd: "",
    ata: "",
    bookingNo: "",
    mbl: "",
    hbl: "",
    vessel: "",
    voyage: "",
    mawb: "",
    hawb: "",
    flightNo: "",
    units: [{
      id: "sync-truck",
      kind: "truck",
      number: "BASE-TRUCK",
      typeSize: "9.6m",
      sealNo: "",
      driverName: "Driver A",
      driverPhone: "0901000000",
    }],
  }];
  canonical.cargoStructured = true;
  canonical.cargo = {
    goodsDescription: "BASE CARGO",
    packs: 10,
    weight: 1200,
    cbm: 4.5,
    dims: "100 x 100 x 100 cm",
    type: "Pallet",
    note: "Base note",
    qtyPkg: "",
  };
  vm5.version = "draft-sync-100";
  invoke(vm5);
  await tick(120);

  // Create independent local edits without saving either one.
  let leg = $("details")[0];
  if (!leg.open) {
    $("summary", leg)[0].click();
    await tick();
  }
  await click("+ Thêm xe", "button", leg);
  let truckNumbers = $('input[data-field="unit-number"]', leg);
  type(truckNumbers[truckNumbers.length - 1], "UNSAVED-TRUCK");
  let cargoInput = $('input[data-field="cargo-goods-description"]')[0];
  type(cargoInput, "UNSAVED CARGO BEFORE REJECTION");

  // An unchanged canonical readback (for example, backend rejection) must not
  // erase either rejected draft even though the parent/version changes.
  const rejectedReadback = JSON.parse(JSON.stringify(vm5));
  rejectedReadback.version = "draft-sync-101";
  rejectedReadback.shipments.find((x) => x.id === "LO-0306").version = 101;
  invoke(rejectedReadback);
  await tick(120);
  assert.ok($('input[data-field="unit-number"]').some((input) => input.value === "UNSAVED-TRUCK"),
    "unchanged readback erased the unsaved transport draft");
  assert.equal($('input[data-field="cargo-goods-description"]')[0].value,
    "UNSAVED CARGO BEFORE REJECTION", "unchanged readback erased the unsaved cargo draft");
  ok("unchanged/rejected readback preserves both local drafts");

  // CASE A + D: a real Cargo readback synchronizes Cargo only; unsaved
  // Transport must survive the unrelated parent/version update.
  const cargoReadback = JSON.parse(JSON.stringify(rejectedReadback));
  cargoReadback.version = "draft-sync-102";
  const cargoLot = cargoReadback.shipments.find((x) => x.id === "LO-0306");
  cargoLot.version = 102;
  cargoLot.cargo.goodsDescription = "SERVER CARGO READBACK";
  invoke(cargoReadback);
  await tick(120);
  assert.ok($('input[data-field="unit-number"]').some((input) => input.value === "UNSAVED-TRUCK"),
    "Cargo readback erased the unsaved transport draft");
  assert.equal($('input[data-field="cargo-goods-description"]')[0].value,
    "SERVER CARGO READBACK", "real Cargo readback did not synchronize Cargo");
  ok("unsaved Transport survives Cargo save/readback");
  ok("real Cargo readback synchronizes the Cargo editor");

  // CASE B + C: now edit Cargo locally, then apply a real Transport readback.
  // Transport must synchronize while the unrelated Cargo draft stays intact.
  cargoInput = $('input[data-field="cargo-goods-description"]')[0];
  type(cargoInput, "UNSAVED-CARGO");
  const transportReadback = JSON.parse(JSON.stringify(cargoReadback));
  transportReadback.version = "draft-sync-103";
  const transportLot = transportReadback.shipments.find((x) => x.id === "LO-0306");
  transportLot.version = 103;
  transportLot.transportLegs[0].units[0].number = "SERVER-TRUCK-READBACK";
  invoke(transportReadback);
  await tick(120);
  truckNumbers = $('input[data-field="unit-number"]');
  assert.deepEqual(truckNumbers.map((input) => input.value), ["SERVER-TRUCK-READBACK"],
    "real Transport readback did not synchronize Transport");
  assert.equal($('input[data-field="cargo-goods-description"]')[0].value, "UNSAVED-CARGO",
    "Transport readback erased the unsaved Cargo draft");
  ok("unsaved Cargo survives Transport save/readback");
  ok("real Transport readback synchronizes the Transport editor");
}

console.log(`\nDOM ACCEPTANCE PASS — ${passed} checks`);
window.close();
process.exit(0);
