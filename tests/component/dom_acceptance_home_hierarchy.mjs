// ============================================================================
// DOM acceptance — LOGI_FRONTEND_WORKFLOW_OVERHAUL_01 · HOME HIERARCHY (P1.1)
//
// Drives the REAL production bundle with a backend-generated full view-model
// (view_model_phase_b.json — 6 pipeline tiles, a real focus, readiness
// summary, tasks) and proves the ONE-desk composition:
//
//   - ONE priority area: the hero states the focus + direct actions, and the
//     duplicated NextActionBanner section is GONE;
//   - exception/deadline list + running lots stay visible (no visibility was
//     removed to make the page "clean");
//   - ONE operational snapshot: each tile label appears exactly once as a
//     clickable KPI (the old double "VIỆC TIẾP THEO"/"Chỉ số vận hành hôm
//     nay" rows over the SAME tiles cannot come back);
//   - money/docs attention keeps every old data point exactly once
//     (outstanding total + count, đối soát, hồ sơ thiếu, urgent total +
//     deadlineSoon) with direct actions;
//   - every tile links somewhere real (bấm đâu để làm ngay).
// ============================================================================

import { readFileSync } from "node:fs";
import assert from "node:assert/strict";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const require = createRequire(path.join(ROOT, "component/package.json"));
const { JSDOM } = require("jsdom");

const FIXTURE = JSON.parse(
  readFileSync(path.join(ROOT, "tests", "component", "fixtures", "view_model_phase_b.json"), "utf8")
);
const HOME = FIXTURE.home;

const dom = new JSDOM("<!DOCTYPE html><html><body></body></html>", {
  url: "http://localhost:8501/",
  pretendToBeVisual: true,
});
const { window } = dom;
globalThis.window = window;
globalThis.document = window.document;
try { Object.defineProperty(globalThis, "navigator", { value: window.navigator, configurable: true }); } catch {}
for (const k of ["HTMLElement","HTMLInputElement","HTMLTextAreaElement","HTMLSelectElement","HTMLAnchorElement","Event","CustomEvent","MouseEvent","KeyboardEvent","Node","MutationObserver","getComputedStyle"]) {
  globalThis[k] = window[k];
}
if (!globalThis.MessageChannel) globalThis.MessageChannel = window.MessageChannel;
window.HTMLElement.prototype.scrollIntoView = () => {};
window.URL.createObjectURL = () => "blob:mock-url";
window.URL.revokeObjectURL = () => {};

const tick = (ms=60) => new Promise(r=>setTimeout(r,ms));
const $ = (sel, root=window.document) => [...root.querySelectorAll(sel)];
const text = (el) => (el?.textContent||"").replace(/\s+/g," ").trim();
const bodyText = () => text(window.document.body);
let passed=0;
function ok(name){ passed++; console.log(`  ✓ ${name}`); }

const host=window.document.createElement("div");
window.document.body.appendChild(host);
let triggers=[];
const mountRef={current:null};
function invoke(data){
  return mountRef.current({name:"logi_shell", data, parentElement:host, setTriggerValue:(ev,val)=>triggers.push({event:ev,value:val})});
}

const bundle=path.join(ROOT,"component","dist","logi-shell.js");
const mod=await import(bundle);
assert.equal(typeof mod.default,"function","bundle must default-export mount");
mountRef.current=mod.default;

console.log("STEP 0 — boot straight to Home");
await invoke(FIXTURE);
await tick(200);
assert.ok(!bodyText().includes("process is not defined"));

console.log("STEP 1 — ONE priority area (hero carries the focus + actions, banner duplication gone)");
{
  const t = bodyText();
  assert.ok(t.includes("Ưu tiên bây giờ:"), "priority hero missing");
  assert.ok(t.includes(`${HOME.focus.id} — ${HOME.focus.nextAction}`), "hero must name the single most important work");
  assert.ok(t.includes("XỬ LÝ NGAY"), "direct action present");
  // The old page said the same thing twice: hero THEN NextActionBanner with
  // "Việc tiếp theo" over the SAME focus. The banner is gone.
  assert.ok(!t.includes("Việc tiếp theo"), "duplicate NextActionBanner must not render");
  const buttons = $("button, a").filter(b => text(b).includes("XỬ LÝ NGAY"));
  assert.equal(buttons.length, 1, `exactly ONE XỬ LÝ NGAY entry point, got ${buttons.length}`);
  ok("one priority area, one action entry");
}

console.log("STEP 2 — exceptions and operational visibility preserved");
{
  const t = bodyText();
  assert.ok(t.includes("Quá hạn và sắp tới hạn"), "deadline list present");
  assert.ok(t.includes("Trạng thái các lô đang chạy"), "running lots present");
  ok("deadline + running sections intact");
}

console.log("STEP 3 — ONE operational snapshot: each tile rendered exactly once");
{
  const t = bodyText();
  assert.ok(t.includes("Ảnh vận hành hôm nay"), "snapshot section present");
  assert.ok(!t.includes("VIỆC TIẾP THEO"), "old duplicated tile row must be gone");
  assert.ok(!t.includes("Chỉ số vận hành hôm nay"), "old duplicated KPI row must be gone");
  // The invariant is scoped to the snapshot section: elsewhere the same
  // string may legitimately occur (e.g. a shipment whose status badge reads
  // "Chờ lấy hàng" in the running list).
  const snapshot = window.document.querySelector('[data-testid="home-snapshot"]');
  assert.ok(snapshot, "snapshot grid present");
  const snapText = text(snapshot);
  for (const tile of HOME.tiles) {
    const occurrences = snapText.split(tile.label).length - 1;
    assert.ok(occurrences >= 1, `tile "${tile.label}" visible`);
    assert.equal(occurrences, 1, `tile "${tile.label}" must appear EXACTLY once in the snapshot, got ${occurrences}`);
  }
  ok(`all ${HOME.tiles.length} pipeline tiles visible exactly once`);
  // Every tile is clickable into the right list (bấm đâu để làm ngay).
  for (const tile of HOME.tiles) {
    const link = $("a").find((a) => text(a).includes(tile.label) && a.getAttribute("href") === tile.to);
    assert.ok(link, `tile "${tile.label}" links to ${tile.to}`);
  }
  ok("every tile links to its operational list");
}

console.log("STEP 4 — money & docs attention keeps every old data point once, with actions");
{
  const t = bodyText();
  assert.ok(t.includes("Tiền & hồ sơ cần chú ý"), "money section present");
  assert.ok(t.includes("GHI NHẬN THANH TOÁN"), "receipt action present");
  assert.ok(t.includes("ĐỐI SOÁT NGAY"), "reconciliation action present");
  // LOGI_INTERNAL_UX_SIMPLIFY_01 — the missing-docs/urgent work card now
  // routes into the surviving Lô Hàng desk (the tasks desk left the nav).
  assert.ok(t.includes("MỞ LÔ HÀNG"), "urgent-work action present");
  assert.ok(!t.includes("MỞ DANH SÁCH VIỆC"), "stale tasks-desk action lingers");
  const urgentLink = $("a").find((a) => text(a).includes("MỞ LÔ HÀNG"));
  assert.ok(urgentLink && urgentLink.getAttribute("href") === "/lo-hang",
    "urgent-work action must route to /lo-hang");
  assert.equal($('a[href*="viec-can-xu-ly"]').length, 0,
    "no visible link may route to the removed tasks desk");
  assert.ok(t.includes("Việc quá hạn / khẩn"), "urgent work card present");
  const urgentTotal = (HOME.summary.critical ?? 0) + (HOME.urgentCount ?? 0);
  assert.ok(t.includes(`${urgentTotal} việc`), `urgent total ${urgentTotal} visible`);
  assert.ok(t.includes(`${HOME.summary.deadlineSoon} lô sắp tới hạn khách`), "deadlineSoon visible");
  assert.ok(t.includes(`${HOME.summary.financialAttention} lô`), "financialAttention visible");
  ok("money/docs data complete: outstanding, đối soát, hồ sơ thiếu, urgent + deadlineSoon");
}

console.log(`\nHOME_HIERARCHY_DOM_ACCEPTANCE=PASSED checks=${passed}`);
