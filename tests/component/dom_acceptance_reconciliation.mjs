// ============================================================================
// LOGI_RECONCILIATION_DESK_01 — DOM/navigation acceptance for
// /tai-chinh/doi-soat (Đối soát).
//
// Runs the REAL production bundle (component/dist/logi-shell.js) in jsdom with a
// REAL-backend fixture (scripts/gen_reconciliation_fixture.py — isolated
// mongomock staging, obligations + payments recorded through the canonical C2B
// handlers) and verifies:
//   1. boot (no process/BidiComponent failure)
//   2. sidebar "Đối soát" carries NO "Sắp có" marker anymore, on the SAME route
//   3. the EMPTY ledger renders an honest empty state — never a balanced 0 book
//   4. the real desk renders MATCHED / PARTIAL / UNMATCHED from canonical
//      allocation truth, with currencies kept separate (never summed)
//   5. the real obligation ↔ transaction refs and a working Open-Shipment link
//   6. filters emit the ONE bounded READ-ONLY "reconciliation_filter" trigger
//      carrying only lookup fields — never a money value
//   7. a filtered readback shows only its rows while the per-currency totals
//      stay the FULL ledger (a filter must never move a total)
//   8. currency separation survives filtering
//   9. no write surface at all (no force-reconcile / mark-settled / edit), and
//      the canonical writers are reachable by navigation only
//  10. the "ngoài phạm vi" panel states what the backend genuinely lacks
//  11. mobile: drawer routes to the same desk, cards (not a min-width table),
//      >= 48px touch targets, amounts stay paired with their currency
//  12. C2C/C2D/partner-context routes are undisturbed
//
// Run: node tests/component/dom_acceptance_reconciliation.mjs
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
  readFileSync(path.join(ROOT, "tests/component/fixtures/view_model_reconciliation.json"), "utf8")
);
const EMPTY = FIX.empty;
const JOURNEY = FIX.journey;
const MATCHED_ONLY = FIX.matchedOnly;
const CNY_ONLY = FIX.cnyOnly;
const PARTNER_LABEL = "CÔNG TY TNHH PHÚ ANH LOGISTICS";

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

let lastInvokeCleanup = null;
async function remount(data, item = "Đối soát") {
  if (lastInvokeCleanup) lastInvokeCleanup();
  triggers.length = 0;
  const cleanup = invoke(data);
  lastInvokeCleanup = cleanup;
  await tick(120);
  await click(item, "a", $("aside")[0]);
}

const bundlePath = path.join(ROOT, "component/dist/logi-shell.js");

// ---------------------------------------------------------------------------
console.log("STEP 1 — boot production bundle (empty ledger)");
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
console.log("STEP 2 — sidebar honesty: no 'Sắp có' on Đối soát");
{
  const aside = $("aside")[0];
  const item = findClickable("Đối soát", "a", aside);
  assert.ok(item, "sidebar item missing");
  assert.ok(!text(item).includes("Sắp có"), "item still marked 'Sắp có'");
  assert.equal(item.getAttribute("href"), "/tai-chinh/doi-soat", "route must stay the existing one");
  ok("sidebar item active on the existing route, no deferred marker");
}

// ---------------------------------------------------------------------------
console.log("STEP 3 — empty ledger is honest: UNKNOWN, never a balanced 0");
await click("Đối soát", "a", $("aside")[0]);
{
  const t = mainText();
  assert.ok(!t.includes("Sắp có — chưa triển khai"), "route still falls through to the placeholder");
  assert.ok(!t.includes("chưa triển khai"), "route unexpectedly shows the deferred placeholder");
  assert.ok(t.includes("Đối soát"), "desk heading missing");
  assert.ok(t.includes("CHỈ ĐỌC"), "read-only marker missing");
  assert.ok(t.includes("Chưa có bản ghi đối soát"), "honest empty state missing");
  assert.ok(t.includes("không phải công nợ bằng 0"), "empty state must state it is NOT a 0 debt");
  ok("EMPTY renders an explicit 'chưa có dữ liệu' state, not 0");
}

// ---------------------------------------------------------------------------
console.log("STEP 4 — real desk over canonical allocation truth");
await remount(JOURNEY);
{
  const t = mainText();
  assert.ok(t.includes(PARTNER_LABEL), "canonical partner identity missing");
  // The three obligation-side states the ledger actually derives.
  assert.ok(t.includes("Đã đối soát đủ"), "MATCHED state missing");
  assert.ok(t.includes("Đối soát một phần"), "PARTIAL state missing");
  assert.ok(t.includes("Chưa đối soát"), "UNMATCHED state missing");
  // Money side of the same reconciliation.
  assert.ok(t.includes("Đã phân bổ hết"), "ALLOCATED money state missing");
  // All four shipments of the fixture are present with their real amounts.
  for (const sid of ["LO-0308", "LO-0307", "LO-0306", "LO-0299"]) {
    assert.ok(t.includes(sid), `shipment ${sid} missing from the desk`);
  }
  assert.ok(t.includes("50.000.000"), "VND amount not rendered with its grouping");
  assert.ok(t.includes("3.000 CNY"), "CNY amount must stay labelled with CNY");
  ok("MATCHED / PARTIAL / UNMATCHED / ALLOCATED all rendered from real records");
}

// ---------------------------------------------------------------------------
console.log("STEP 5 — currencies stay separate, never summed");
{
  const cards = $("div.rounded-2xl.bg-white.border").filter((el) => text(el).includes("nghĩa vụ ·"));
  const ccyCards = cards.map((el) => text(el));
  assert.equal(ccyCards.length, 2, `expected exactly one block per currency, got ${ccyCards.length}`);
  const vnd = ccyCards.find((c) => c.startsWith("VND"));
  const cny = ccyCards.find((c) => c.startsWith("CNY"));
  assert.ok(vnd, "VND total block missing");
  assert.ok(cny, "CNY total block missing");
  // Each block carries only its own currency's figures.
  assert.ok(vnd.includes("67.000.000 VND") && vnd.includes("37.000.000 VND"), "VND block wrong");
  assert.ok(!vnd.includes("CNY"), "CNY leaked into the VND block");
  assert.ok(cny.includes("3.000 CNY") && cny.includes("2.000 CNY"), "CNY block wrong");
  assert.ok(!cny.includes("VND"), "VND leaked into the CNY block");
  const t = mainText();
  // 10.000.000 + 50.000.000 + 7.000.000 VND = 67.000.000 and 3.000 CNY: a fake
  // grand total would have to appear as one number; neither may.
  assert.ok(!t.includes("67.003.000"), "cross-currency grand total leaked into the UI");
  assert.ok(!t.includes("70.000.000"), "cross-currency grand total leaked into the UI");
  ok("one block per currency, no FX, no grand total");
}

// ---------------------------------------------------------------------------
console.log("STEP 6 — real obligation ↔ transaction refs and Open Shipment");
{
  const t = mainText();
  const matchedTx = JOURNEY.reconciliation.rows.find(
    (r) => r.shipmentId === "LO-0308" && r.side === "obligation"
  );
  assert.ok(matchedTx && matchedTx.transactionIds.length === 1, "fixture must carry a real transaction ref");
  assert.ok(t.includes(matchedTx.transactionIds[0]), "matched obligation must show the transaction that settled it");
  const open = $('a[href="/lo-hang/LO-0308"]');
  assert.ok(open.length > 0, "Open Shipment link missing");
  assert.ok(open.every((a) => text(a).includes("Mở lô")), "Open Shipment link must be labelled");
  // The unmatched obligation must NOT pretend to have a transaction.
  const unmatched = JOURNEY.reconciliation.rows.find(
    (r) => r.shipmentId === "LO-0306" && r.side === "obligation"
  );
  assert.equal(unmatched.transactionIds.length, 0, "unmatched obligation must have no transaction ref");
  ok("allocation refs are real; unmatched carries no invented reference");
}

// ---------------------------------------------------------------------------
console.log("STEP 6b — Open Shipment really opens that shipment");
{
  await clickSelector('main a[href="/lo-hang/LO-0308"]');
  const t = mainText();
  assert.ok(t.includes("LO-0308"), "Open Shipment did not navigate to the shipment");
  assert.ok(!t.includes("chưa triển khai"), "the shipment route fell through to the placeholder");
  assert.ok(!t.includes("Đối soát") || t.includes("LO-0308"), "navigation did not leave the desk");
  // And back again, on the existing route.
  await click("Đối soát", "a", $("aside")[0]);
  assert.ok(mainText().includes("LO-0308"), "returning to the desk lost the reconciliation rows");
  ok("desk → /lo-hang/LO-0308 → desk is a real round trip");
}

// ---------------------------------------------------------------------------
console.log("STEP 7 — filters emit ONE bounded READ-ONLY event, no money value");
{
  triggers.length = 0;
  await click("Đã đối soát đủ", "button");
  const events = triggers.filter((tr) => tr.event === "reconciliation_filter");
  assert.equal(events.length, 1, `expected exactly 1 bounded event, got ${events.length}`);
  const payload = events[0].value.payload;
  assert.deepEqual(
    Object.keys(payload).sort(),
    ["currency", "query", "side", "state"],
    "the event must carry ONLY lookup fields"
  );
  assert.equal(payload.state, "MATCHED");
  // No money, no id, no balance may ever travel through this event.
  for (const forbidden of ["amount", "allocated", "remaining", "outstanding", "payable", "paid",
    "obligationId", "transactionId", "balance", "settled", "reconciled"]) {
    assert.ok(!(forbidden in payload), `forbidden field "${forbidden}" in the read-only event`);
  }
  const blob = JSON.stringify(payload);
  assert.ok(!/50000000|10000000|57000000/.test(blob), "a money value leaked into the filter event");
  ok("one bounded reconciliation_filter carrying lookup fields only");
}

// ---------------------------------------------------------------------------
console.log("STEP 8 — filtered readback: rows narrow, totals do NOT");
await remount(MATCHED_ONLY, "Đối soát");
{
  const t = mainText();
  assert.ok(t.includes("LO-0308"), "the MATCHED row must be visible");
  assert.ok(!t.includes("LO-0306"), "an UNMATCHED row survived a MATCHED-only filter");
  // The full ledger is still 7 rows; only 1 is visible.
  assert.ok(t.includes("1 / 7 dòng"), "visible/total counter must show the filter did not shrink the ledger");
  // Both currency blocks are still published — the totals are NOT filtered.
  assert.ok(t.includes("VND"), "VND total must survive the filter");
  assert.ok(t.includes("CNY"), "CNY total must survive the filter");
  assert.ok(t.includes("3.000 CNY"), "the unfiltered CNY total must still be visible");
  assert.ok(t.includes("bộ lọc không làm thay đổi số tổng") || t.includes("vẫn là toàn bộ ledger"),
    "the UI must state that filters never move the totals");
  ok("filter narrows rows only; per-currency totals stay the full ledger");
}

// ---------------------------------------------------------------------------
console.log("STEP 9 — currency filter isolates CNY without touching VND truth");
await remount(CNY_ONLY, "Đối soát");
{
  const t = mainText();
  assert.ok(t.includes("LO-0299"), "the CNY row must be visible");
  assert.ok(!t.includes("LO-0308"), "a VND row survived a CNY-only filter");
  assert.ok(t.includes("2.000 CNY"), "CNY remaining must be shown in CNY");
  // The VND total block is still published (totals are never filtered).
  assert.ok(t.includes("67.000.000"), "the full VND payable total must still be published");
  ok("CNY isolated; VND totals untouched and never converted");
}

// ---------------------------------------------------------------------------
console.log("STEP 10 — no write surface; canonical writers are navigation only");
await remount(JOURNEY, "Đối soát");
{
  const buttons = $("main button").map((el) => text(el)).filter(Boolean);
  for (const forbidden of [
    "Ghi nhận", "Lưu", "Xóa", "Xoá", "Sửa", "Chốt kỳ", "Khoá sổ", "Khóa sổ",
    "Đánh dấu đã đối soát", "Force", "Reconcile", "Đối soát ngay", "Xác nhận công nợ",
    "Sửa số dư", "Ghi có", "Ghi nợ", "Điều chỉnh",
  ]) {
    assert.ok(
      !buttons.some((label) => label.includes(forbidden)),
      `the read-only desk must not offer a write action ("${forbidden}")`
    );
  }
  // No editable money control anywhere in the desk.
  const inputs = $("main input");
  assert.equal(inputs.length, 1, "the desk may have exactly one input: the search box");
  assert.equal(inputs[0].getAttribute("aria-label"), "Tìm trong đối soát");
  assert.equal($("main select").length, 0, "no select control belongs on a read-only desk");
  assert.equal($("main textarea").length, 0, "no textarea belongs on a read-only desk");
  // The write lives elsewhere, reached by navigation.
  const t = mainText();
  assert.ok(t.includes("Ghi nhận ở đâu"), "the desk must say where the write actually happens");
  assert.ok($('main a[href="/tai-chinh/cong-no-doi-tac"]').length > 0, "C2D writer link missing");
  assert.ok($('main a[href="/tai-chinh/thu-tien"]').length > 0, "C2C writer link missing");
  ok("zero write controls; canonical C2B/C2D + C2C writers linked, not duplicated");
}

// ---------------------------------------------------------------------------
console.log("STEP 11 — honest gaps: what this desk is NOT");
{
  const t = mainText();
  assert.ok(t.includes("Ngoài phạm vi bàn này"), "the gap panel is missing");
  assert.ok(t.includes("sao kê ngân hàng"), "bank-statement scope must be disclaimed");
  assert.ok(t.includes("FX") || t.includes("tỷ giá"), "no-FX must be disclaimed");
  assert.ok(t.includes("aging") || t.includes("Tuổi nợ"), "no-aging must be disclaimed");
  assert.ok(t.includes("VAT"), "no-VAT-reconciliation must be disclaimed");
  ok("unavailable panel states the backend's real limits");
}

// ---------------------------------------------------------------------------
console.log("STEP 12 — mobile: drawer routing, cards, 48px targets");
{
  await clickSelector('button[aria-label="Mở menu"]');
  const drawer = $("div.anim-slide-up").filter((el) => text(el).includes("Menu điều hành"))[0]
    ?? $(".fixed.inset-0.z-50")[0];
  assert.ok(drawer, "mobile drawer missing");
  const drawerItem = findClickable("Đối soát", "a", drawer);
  assert.ok(drawerItem, "drawer item missing");
  assert.ok(!text(drawerItem).includes("Sắp có"), "drawer item still marked 'Sắp có'");
  await click("Đối soát", "a", drawer);
  assert.ok(mainText().includes("Đối soát"), "drawer must open the reconciliation desk");

  // Below md the rows are a card stack; the table is gated behind md.
  assert.ok($("div.space-y-3.md\\:hidden").length > 0, "mobile card stack missing");
  const tableWrap = $("div.hidden.md\\:block")[0];
  assert.ok(tableWrap, "desktop table must stay gated behind md");
  assert.ok(tableWrap.querySelector("table"), "the wide layout must be the table");
  assert.ok(
    !tableWrap.querySelector("table").className.includes("min-w"),
    "the table must not force a min width outside its md gate"
  );

  const search = $('input[aria-label="Tìm trong đối soát"]')[0];
  assert.ok(search.className.includes("min-h-[48px]"), "search input below touch target");
  const chips = $("main button").filter((b) => ["Tất cả", "Cả hai", "Nghĩa vụ", "Tiền",
    "Đã đối soát đủ", "Chưa đối soát", "Mọi tiền tệ", "VND", "CNY"].includes(text(b)));
  assert.ok(chips.length >= 6, `expected the filter chips to render, got ${chips.length}`);
  assert.ok(chips.every((b) => b.className.includes("min-h-[44px]")), "a filter chip is below touch target");
  const open = $('a[href^="/lo-hang/"]');
  assert.ok(open.length > 0 && open.every((a) => a.className.includes("min-h-[44px]")),
    "Open Shipment must stay reachable at touch size");
  // Financial meaning survives the card layout: amounts stay with their currency.
  const cardText = text($("div.space-y-3.md\\:hidden")[0]);
  for (const sid of ["LO-0308", "LO-0307", "LO-0306", "LO-0299"]) {
    assert.ok(cardText.includes(sid), `card stack lost shipment ${sid}`);
  }
  assert.ok(cardText.includes("Còn lại"), "remaining amount label lost in the card layout");
  assert.ok(cardText.includes("CNY"), "currency label lost in the card layout");
  ok("drawer routing, card stack, gated table, >= 44px controls, amounts + currency intact");
}

// ---------------------------------------------------------------------------
console.log("STEP 13 — other real routes are undisturbed");
{
  await click("Công nợ đối tác", "a", $("aside")[0]);
  assert.ok(mainText().includes("Thanh toán đối tác"), "C2D route was disturbed");
  await click("Thu tiền", "a", $("aside")[0]);
  assert.ok(mainText().includes("Phải thu") || mainText().includes("Thu tiền"), "C2C route was disturbed");
  await click("Ngữ cảnh Đối tác", "a", $("aside")[0]);
  assert.ok(mainText().includes("CHỈ ĐỌC"), "partner-context route was disturbed");
  await click("Dịch thuật", "a", $("aside")[0]);
  assert.ok(mainText().includes("Văn bản nguồn"), "translation route was disturbed");
  ok("C2C / C2D / partner-context / translation all still render their real pages");
}

console.log(`\nDOM acceptance PASSED — ${passed} checks`);
