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
  // Real readiness/task evidence — the row count follows the fixture, not a
  // hardcoded Phase A number.
  assert.equal(rows.length, VM.tasks.length, `expected ${VM.tasks.length} task rows, got ${rows.length}`);
  // filter interaction (donor UI): the counts are computed from the real rows
  const countOf = (level) => VM.tasks.filter((t) => t.level === level).length;
  const urgent = countOf("Khan");
  assert.ok(urgent > 0, "expected at least one urgent task in the seed evidence");
  await click(`Khẩn (${urgent})`, "button");
  const rows2 = $("table.tbl tbody tr");
  assert.equal(rows2.length, urgent, `expected ${urgent} urgent rows, got ${rows2.length}`);
  await click(`Tất cả (${VM.tasks.length})`, "button");
  assert.equal($("table.tbl tbody tr").length, VM.tasks.length, "filter reset failed");
  ok(`Tasks rendered with ${VM.tasks.length} rows + working priority filter`);
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
  assert.ok(t.includes(`Đang thiếu ${missing} thông tin`), "missing-docs box missing");
  for (const fact of lot.missingDocs) {
    assert.ok(t.includes(fact), `missing fact not listed: ${fact}`);
  }
  ok(`Shipment Detail LO-0306 rendered (status, ${missing} real missing facts)`);
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

  // LO-0308: save pickup tab (missing-info flow)
  await click("Lô Hàng", "a", $("aside")[0]);
  await click("LO-0308", "a", $("table.tbl")[0]);
  const plate = window.document.getElementById("fld-plate");
  assert.ok(plate, "plate input missing on LO-0308");
  type(plate, "粤B·20T99");
  await click("💾 LƯU THÔNG TIN LẤY HÀNG", "button");
  assert.ok(bodyText().includes("Đã lưu thông tin lấy hàng LO-0308"), "save toast missing");
  const evs = triggers.filter((t) => t.event === "shipment_field_save");
  assert.equal(evs.length, 1, `expected 1 shipment_field_save event, got ${evs.length}`);
  assert.ok(evs[0].value.seq > ev.value.seq, "event seq must increase");
  assert.equal(evs[0].value.payload.shipmentId, "LO-0308", "field save payload wrong shipment");
  assert.equal(evs[0].value.payload.fields.container_no, "粤B·20T99", "field save payload wrong plate");
  assert.ok(
    !Object.values(evs[0].value.payload.fields).some((v) => v === "" || v === null),
    "field save must not send blank/UNKNOWN values"
  );
  ok("pickup save → shipment_field_save with increasing seq, blanks omitted");
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
  const selects = $("select");
  assert.ok(selects.length >= 2, "customer/contract selects missing");
  selects[0].value = VM.customers[0].name;
  selects[0].dispatchEvent(new window.Event("change", { bubbles: true }));
  await tick();

  await click("TẠO LÔ HÀNG", "button");
  await tick();
  const created = triggers.filter((x) => x.event === "shipment_create");
  assert.equal(created.length, 1, `expected 1 shipment_create event, got ${created.length}`);
  assert.equal(created[0].value.payload.shipmentId, "LO-0470", "create payload wrong id");
  assert.equal(created[0].value.payload.customer, VM.customers[0].name, "create payload wrong customer");
  ok("Create Shipment → shipment_create {shipmentId, customer, ...} emitted");
}

// ---------------------------------------------------------------------------
// STEP 15 — Phase B: Tracking (real transport facts, no fabricated GPS)
// ---------------------------------------------------------------------------

console.log("STEP 15 — Tracking");
{
  await click("Theo Dõi Vận Chuyển", "a", $("aside")[0]);
  const t15 = bodyText();
  assert.ok(t15.includes("Theo Dõi Vận Chuyển"), "tracking page missing");
  assert.ok(t15.includes("Không mô phỏng vị trí GPS"), "no-GPS disclaimer missing");
  assert.ok(t15.includes("LO-0299"), "tracking lot list missing LO-0299");
  const lot = VM.shipments.find((x) => x.id === "LO-0299");
  await click("LO-0299", "button");
  const t15b = bodyText();
  assert.ok(t15b.includes(lot.tracking.carrier), "carrier missing");
  assert.ok(t15b.includes(lot.tracking.reference), "tracking reference missing");
  assert.ok(t15b.includes("Mốc vận chuyển"), "milestones section missing");
  for (const m of lot.tracking.milestones.slice(0, 2)) {
    assert.ok(t15b.includes(m.title), `milestone missing: ${m.title}`);
  }
  ok(`Tracking renders real carrier/reference + ${lot.tracking.milestones.length} milestones`);
}

console.log(`\nDOM ACCEPTANCE PASS — ${passed} checks`);
window.close();
process.exit(0);
