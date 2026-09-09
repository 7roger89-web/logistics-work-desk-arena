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
//   5. click Việc Cần Xử Lý → Tasks (+ filter)
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
  readFileSync(path.join(ROOT, "tests/component/fixtures/view_model_phase_a.json"), "utf8")
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
  for (const s of ["TRƯỜNG THÀNH", "Phú Anh Logistics · Nội bộ", "PROTOTYPE"]) {
    assert.ok(ht.includes(s), `header missing "${s}"`);
  }
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
  for (const it of [
    "Tổng Quan Công Việc",
    "Việc Cần Xử Lý",
    "Lô Hàng",
    "Tạo Lô Mới",
    "Theo Dõi Vận Chuyển",
    "Khách Hàng",
    "Báo giá",
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
  ok("5 donor groups + 16 items present");
}

// ---------------------------------------------------------------------------
// STEP 4 — click Tổng Quan → Home
// ---------------------------------------------------------------------------

console.log("STEP 4 — click Tổng Quan Công Việc");
{
  await click("Tổng Quan Công Việc", "a", $("aside")[0]);
  const t = bodyText();
  assert.ok(t.includes("Hôm nay tôi cần làm gì?"), "Home hero missing");
  assert.ok(t.includes("VIỆC TIẾP THEO"), "next-up section missing");
  assert.ok(t.includes("Chỉ số vận hành hôm nay"), "KPI section missing");
  assert.ok(t.includes("Lô đang chạy"), "KPI cards missing");
  ok("Home rendered after real click");
}

// ---------------------------------------------------------------------------
// STEP 5 — click Việc Cần Xử Lý → Tasks
// ---------------------------------------------------------------------------

console.log("STEP 5 — click Việc Cần Xử Lý");
{
  await click("Việc Cần Xử Ly".replace(" Ly", " Lý"), "a", $("aside")[0]);
  const t = bodyText();
  assert.ok(t.includes("Việc Cần Xử Lý"), "Tasks heading missing");
  const rows = $("table.tbl tbody tr");
  assert.equal(rows.length, 10, `expected 10 task rows, got ${rows.length}`);
  // filter interaction (donor UI): Khẩn (3)
  await click("Khẩn (3)", "button");
  const rows2 = $("table.tbl tbody tr");
  assert.equal(rows2.length, 3, `expected 3 urgent rows, got ${rows2.length}`);
  await click("Tất cả (10)", "button");
  assert.equal($("table.tbl tbody tr").length, 10, "filter reset failed");
  ok("Tasks rendered with 10 rows + working priority filter");
}

// ---------------------------------------------------------------------------
// STEP 6 — click Lô Hàng → Shipments
// ---------------------------------------------------------------------------

console.log("STEP 6 — click Lô Hàng");
{
  await click("Lô Hàng", "a", $("aside")[0]);
  const t = bodyText();
  assert.ok(t.includes("Tìm theo mã lô"), "Shipments page missing");
  const rows = $("table.tbl tbody tr");
  assert.equal(rows.length, 5, `expected 5 shipment rows, got ${rows.length}`);
  for (const id of ["LO-0306", "LO-0307", "LO-0308", "LO-0299", "LO-0295"]) {
    assert.ok(t.includes(id), `shipment ${id} missing`);
  }
  ok("Shipments rendered with 5 sandbox lots");
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
  assert.ok(t.includes("Thiếu 4 thông tin"), "missing-info chip missing");
  assert.ok(t.includes("Đang thiếu 2 thông tin"), "missing-docs box missing");
  ok("Shipment Detail LO-0306 rendered (status, missing states)");
}

// ---------------------------------------------------------------------------
// STEP 8 — all five donor tabs
// ---------------------------------------------------------------------------

console.log("STEP 8 — five donor tabs");
{
  const tabs = {
    "Lấy hàng & Xuất khẩu": "Nhà máy & lịch lấy hàng",
    "Nhập khẩu & Giao hàng": "Tờ khai & thuế nhập khẩu",
    "Tài chính / Công nợ": "Phải thu khách hàng (VND)",
    "Chứng từ & PXK": "Phiếu xuất kho (PXK) — theo từng lô",
    "Lịch sử": "Dòng thời gian — LO-0306",
  };
  const tabRoot = window.document.getElementById("workspace-tabs");
  assert.ok(tabRoot, "workspace tabs missing");
  // default tab
  assert.ok(bodyText().includes(tabs["Lấy hàng & Xuất khẩu"]), "default tab content missing");
  ok("tab 1: Lấy hàng & Xuất khẩu (default)");
  for (const [label, marker] of Object.entries(tabs)) {
    if (label === "Lấy hàng & Xuất khẩu") continue;
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
  assert.ok(t.includes("LO-0306 · An Phát"), "search result for 'an phát' missing");
  const found = findClickable("LO-0306 · An Phát", "button");
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
  ok("search finds LO-0306 · An Phát, navigates, shows empty state");
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
  // close via the X (first svg button inside the sheet)
  const sheet = $("div").find((d) => d.className.includes("sm:max-w-[520px]"));
  const closeBtn = $("button", sheet).find((b) => b.querySelector("svg"));
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
  assert.ok(t.includes("Thông báo · 4 chưa đọc"), "notifications drawer missing");
  for (const n of ["LO-0306 · Chờ số tờ khai — hạn 17:00", "LO-0308 · Chưa có xe TQ", "LO-0306 · Tạm ứng đợt 2", "LO-0295 · Đã giao 07:30"]) {
    assert.ok(t.includes(n), `notification missing: ${n}`);
  }
  // close: X button inside the drawer header
  const drawer = $("div").find((d) => d.className.includes("w-[380px]"));
  const closeBtn = $("button", drawer).find((b) => b.querySelector("svg"));
  assert.ok(closeBtn, "notif close button missing");
  closeBtn.click();
  await tick();
  assert.ok(!bodyText().includes("Thông báo · 4 chưa đọc"), "notifications did not close");
  ok("Notifications opens with 4 items and closes");
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
// STEP 13 — typed v2 event contract (save actions emit shipment_update)
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
  assert.ok(bodyText().includes("ĐÃ GIAO HÀNG XONG"), "delivery confirmation missing");
  const ev = triggers.find((t) => t.event === "shipment_update");
  assert.ok(ev, "shipment_update trigger not emitted");
  assert.ok(ev.value && typeof ev.value.seq === "number", "trigger payload missing seq");
  assert.equal(ev.value.event, "shipment_update", "trigger payload missing event name");
  assert.equal(ev.value.payload.shipment.id, "LO-0299", "trigger payload missing shipment id");
  assert.equal(ev.value.payload.shipment.status, "Đã giao", "trigger shipment not updated");
  ok("delivery save → shipment_update {seq, event, payload.shipment} emitted");

  // LO-0308: save pickup tab (missing-info flow)
  await click("Lô Hàng", "a", $("aside")[0]);
  await click("LO-0308", "a", $("table.tbl")[0]);
  const plate = window.document.getElementById("fld-plate");
  assert.ok(plate, "plate input missing on LO-0308");
  type(plate, "粤B·20T99");
  await click("💾 LƯU THÔNG TIN LẤY HÀNG", "button");
  assert.ok(bodyText().includes("Đã lưu thông tin lấy hàng LO-0308"), "save toast missing");
  const evs = triggers.filter((t) => t.event === "shipment_update");
  assert.equal(evs.length, 2, `expected 2 shipment_update events, got ${evs.length}`);
  assert.ok(evs[1].value.seq > evs[0].value.seq, "event seq must increase");
  assert.equal(evs[1].value.payload.shipment.pickup.plate, "粤B·20T99", "pickup save payload wrong");
  ok("pickup save → second shipment_update with increasing seq");
}

// ---------------------------------------------------------------------------
console.log(`\nDOM ACCEPTANCE PASS — ${passed} checks`);
window.close();
process.exit(0);
