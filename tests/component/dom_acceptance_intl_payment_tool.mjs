// ============================================================================
// LOGI_INTL_PAYMENT_STANDALONE_TOOL_01 — DOM acceptance for Issue #109
// (mounts the REAL committed bundle component/dist/logi-shell.js in jsdom).
//
//   1. CÔNG CỤ nav (desktop sidebar + mobile drawer) has "Thanh toán quốc tế".
//   2. /thanh-toan-quoc-te renders standalone — no contract, no contract ID.
//   3. Contract detail no longer has a Thanh toán quốc tế / TTQT tab.
//   4. No snapshot / save / history wording or button anywhere in the tool.
//   5. The "Tự nhập toàn bộ thông số" checkbox exists, is OFF, is usable.
//   6. OFF: only genuinely OK projections are LIVE; BIDV RATE_UNAVAILABLE (or
//      its HTML fallback) and a non-OK BOC never become numbers.
//   7. ON: all 10 formula inputs are visible, labelled and editable.
//   8. UNKNOWN != ZERO: blank/invalid → "—" + hint; typed 0 is a real 0.
//   9. Golden vector 14000 USD → 99,685.50 CNY (+ breakdown), Mode B vector.
//  10. No trigger (write event) and no Web Storage write from tool use.
//  11. Mobile ~390px — STRUCTURAL ONLY (no fixed width > viewport, touch
//      target sizes, 16px inputs, inputs → results → parameters order).
//  12. Desktop ~1440px — STRUCTURAL ONLY (inputs left, results right column).
//
// jsdom has NO layout engine: steps 11/12 prove class/DOM structure, not
// rendered pixels. Real-browser visual evidence is a separate item.
//
// Expected numbers were computed independently with the server-side Decimal
// mirror core/intl_payment_calculator.py (china_forward / hk_forward /
// china_reverse / hk_reverse / vietnam_bank_cost / outside_cny_route).
//
// Run: node tests/component/dom_acceptance_intl_payment_tool.mjs
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
  readFileSync(path.join(ROOT, "tests/component/fixtures/view_model_contract_workflow.json"), "utf8")
);

// Projection shapes of views/logi_view_model.py::_intl_fx_rates_projection.
// BIDV deliberately carries HTML-fallback numbers (html_sell + sell) that
// must NEVER surface: RATE_UNAVAILABLE stays unavailable.
const FX_OK = {
  boc: { status: "OK", currency: "USD", usd_to_cny: 7.0123, usd_to_cny_str: "7.0123", pub_time: "2026.09.24 09:30:00", source_url: "https://www.boc.cn/sourcedb/whpj/enindex_1619.html" },
  agribank: { status: "OK", currency: "USD", sell: 26180, usd_sell_vnd: 26180, usd_sell_vnd_str: "26180", pub_time: "24/09/2026 09:00", source_url: "https://www.agribank.com.vn/vn/ty-gia" },
  bidv: { status: "RATE_UNAVAILABLE", bidv_rate_status: "UNAVAILABLE", currency: "USD", sell: 26200, usd_sell_vnd: null, html_sell: "26,200", reason: "BIDV official JSON unavailable; HTML fallback is not a trusted rate" },
};
const clone = (o) => JSON.parse(JSON.stringify(o));
const vmWith = (fx) => ({ ...clone(FIX.success), intlFxRates: fx });

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
  "Node", "MutationObserver", "getComputedStyle", "TextEncoder",
]) {
  globalThis[k] = window[k];
}
if (!globalThis.MessageChannel) globalThis.MessageChannel = window.MessageChannel;
window.HTMLElement.prototype.scrollIntoView = () => {};

// Persistence spy: the calculator must never write Web Storage.
let storageWrites = 0;
const realSetItem = window.Storage.prototype.setItem;
window.Storage.prototype.setItem = function (...args) {
  storageWrites += 1;
  return realSetItem.apply(this, args);
};

const tick = (ms = 80) => new Promise((r) => setTimeout(r, ms));
const $ = (sel, root = window.document) => [...root.querySelectorAll(sel)];
const text = (el) => (el?.textContent || "").replace(/\s+/g, " ").trim();
const mainText = () => text($("main")[0] ?? window.document.body);
const byTestId = (id, root = window.document) => root.querySelector(`[data-testid="${id}"]`);
const tool = () => byTestId("intl-tool");
const toolText = () => text(byTestId("intl-payment-tool"));

function findClickable(needle, sel = "a,button", root = window.document) {
  const els = $(sel, root);
  return els.find((el) => text(el) === needle) || els.find((el) => text(el).startsWith(needle)) || null;
}
async function clickEl(el, label = "element") {
  assert.ok(el, `${label} not found`);
  el.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
  await tick();
  return el;
}
const click = (needle, sel = "a,button", root = window.document) =>
  clickEl(findClickable(needle, sel, root), `clickable "${needle}"`);
const clickId = (id) => clickEl(byTestId(id), `[data-testid="${id}"]`);
async function typeInput(input, value) {
  assert.ok(input, "input not found");
  const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
  setter.call(input, value);
  input.dispatchEvent(new window.Event("input", { bubbles: true }));
  await tick(60);
}
const typeId = (id, value) => typeInput(byTestId(id), value);
const setParam = (key, value) => typeId(`intl-param-${key}`, value);
const resultText = (id) => text(byTestId(id)?.querySelector("p.font-extrabold.tabular-nums"));

let passed = 0;
function ok(name) {
  passed += 1;
  console.log(`  ✓ ${name}`);
}

// Forbidden persistence / workflow wording (the required copy "không lưu dữ
// liệu" is the only allowed use of "lưu").
const FORBIDDEN = [/snapshot/i, /đã gửi lưu/i, /máy chủ/i, /bất biến/i, /lịch sử/i, /lưu snapshot/i, /đã lưu/i, /bút toán đã/i];
function assertNoPersistenceWording(where) {
  const t = toolText();
  for (const re of FORBIDDEN) assert.ok(!re.test(t), `${where}: forbidden wording ${re} present`);
  const stripped = t.replace("không lưu dữ liệu", "");
  assert.ok(!/\blưu\b/i.test(stripped), `${where}: unexpected "lưu" wording: ${stripped.match(/.{0,30}lưu.{0,30}/i)?.[0]}`);
  for (const b of $("button", byTestId("intl-payment-tool"))) {
    assert.ok(!/lưu|save|gửi|snapshot|lịch sử|history/i.test(text(b)), `${where}: forbidden button "${text(b)}"`);
  }
}

const host = window.document.createElement("div");
window.document.body.appendChild(host);
const triggers = [];
// BUNDLE_PATH lets a reviewer point the same checks at another build (e.g. the
// pre-change bundle, which must FAIL at step 1).
const mod = await import(process.env.BUNDLE_PATH || path.join(ROOT, "component/dist/logi-shell.js"));
assert.equal(typeof mod.default, "function");
const mount = (data) =>
  mod.default({
    name: "logi_shell",
    data,
    parentElement: host,
    setTriggerValue: (event, value) => triggers.push({ event, value }),
  });
mount(vmWith(clone(FX_OK)));
await tick(150);
const triggersAtStart = triggers.length;

// ---------------------------------------------------------------------------
console.log("STEP 1 — CÔNG CỤ nav item (desktop sidebar + mobile drawer)");
{
  const groupOf = (root, name) => $("p", root).find((p) => text(p) === name)?.parentElement ?? null;
  const asideGroup = groupOf($("aside")[0], "CÔNG CỤ");
  assert.ok(asideGroup, "sidebar group CÔNG CỤ missing");
  const link = $("a", asideGroup).find((a) => text(a) === "Thanh toán quốc tế");
  assert.ok(link, "sidebar CÔNG CỤ lacks Thanh toán quốc tế");
  assert.equal(link.getAttribute("href"), "/thanh-toan-quoc-te");
  assert.ok(link.querySelector("svg"), "nav item must carry the lucide icon");
  await clickEl($('button[aria-label="Mở menu"]')[0], "mobile menu button");
  const drawer = $("div.anim-slide-up").find((el) => text(el).includes("Menu điều hành"));
  assert.ok(drawer, "mobile drawer missing");
  const drawerGroup = groupOf(drawer, "CÔNG CỤ");
  assert.ok(drawerGroup, "drawer group CÔNG CỤ missing");
  const dlink = $("a", drawerGroup).find((a) => text(a) === "Thanh toán quốc tế");
  assert.ok(dlink && dlink.getAttribute("href") === "/thanh-toan-quoc-te", "drawer CÔNG CỤ lacks the item");
  await clickEl(dlink, "drawer link");
  assert.ok(tool(), "drawer link did not open the tool");
  ok("sidebar + drawer: CÔNG CỤ → Thanh toán quốc tế → /thanh-toan-quoc-te");
}

// ---------------------------------------------------------------------------
console.log("STEP 2 — standalone route, no contract coupling");
{
  const h1 = $("main h1")[0];
  assert.equal(text(h1), "Thanh toán quốc tế");
  assert.ok(
    toolText().includes("Công cụ tính tham khảo. Không thực hiện chuyển tiền và không lưu dữ liệu."),
    "required reference-only copy missing"
  );
  for (const c of FIX.success.contracts) {
    assert.ok(!toolText().includes(c.id), `tool shows contract id ${c.id}`);
  }
  assert.ok(!/hợp đồng/i.test(toolText()), "tool mentions a contract");
  ok("h1 + reference copy; no contract id / contract wording");
}

// ---------------------------------------------------------------------------
console.log("STEP 3 — contract detail has no TTQT tab");
{
  await click("Hợp đồng", "a", $("aside")[0]);
  await click("HDMB-0306", "a", $("main")[0]);
  assert.equal(text($("main h1")[0]), "HDMB-0306");
  for (const label of ["Tổng quan", "Hàng hóa hợp đồng", "Chứng từ HDNT/PL/HDMB", "Lô liên kết"]) {
    assert.ok(findClickable(label, "button", $("main")[0]), `contract tab "${label}" missing`);
  }
  const tabs = $("main button").map(text);
  assert.ok(!tabs.some((t) => t.includes("Thanh toán quốc tế") || t === "TTQT"), "TTQT tab still present");
  assert.ok(!mainText().includes("Thanh toán quốc tế"), "contract detail still renders intl payment");
  assert.ok(!tool(), "calculator still mounted inside contract detail");
  ok("contract detail: 4 remaining tabs, no Thanh toán quốc tế / TTQT, no calculator");
}

// ---------------------------------------------------------------------------
console.log("STEP 4/5/6 — checkbox OFF: truthful LIVE / UNAVAILABLE, standard fees");
{
  await click("Thanh toán quốc tế", "a", $("aside")[0]);
  const cb = byTestId("intl-manual-toggle");
  assert.ok(cb && cb.type === "checkbox", "manual checkbox missing");
  assert.equal(cb.checked, false, "manual checkbox must default OFF");
  const lbl = cb.closest("label");
  assert.ok(lbl && text(lbl).includes("Tự nhập toàn bộ thông số"), "checkbox label text missing");
  assert.equal(byTestId("intl-params").getAttribute("data-mode"), "normal");
  assert.equal(byTestId("intl-mode-A").getAttribute("aria-pressed"), "true", "Mode A is the default");
  assert.equal(text(byTestId("intl-mode-A")), "A · Tôi có USD cần chuyển");
  assert.equal(text(byTestId("intl-mode-B")), "B · Đại lý cần nhận CNY");

  const row = (k) => byTestId(`intl-rate-${k}`);
  assert.equal(row("usdCny").getAttribute("data-source"), "LIVE");
  assert.ok(text(row("usdCny")).includes("7.0123 CNY/USD"));
  assert.equal(row("agriSell").getAttribute("data-source"), "LIVE");
  assert.ok(text(row("agriSell")).includes("26.180 VND/USD"));
  assert.equal(row("bidvSell").getAttribute("data-source"), "UNAVAILABLE");
  assert.ok(text(row("bidvSell")).includes("—") && text(row("bidvSell")).includes("UNAVAILABLE"));
  assert.equal(row("outsideRate").getAttribute("data-source"), "UNAVAILABLE");
  assert.ok(!/26[.,]?200/.test(toolText()), "BIDV HTML fallback number leaked into the tool");
  assert.equal($('[data-testid^="intl-param-"]').length, 0, "OFF mode must not expose parameter inputs");
  const fees = text(byTestId("intl-standard-fees"));
  for (const f of ["35 USD", "150 CNY", "10,000 USD", "2%", "5 USD", "0.15%"]) {
    assert.ok(fees.includes(f), `standard fee "${f}" not visible`);
  }
  assertNoPersistenceWording("OFF/initial");

  // Business amount blank → UNKNOWN, not 0.
  assert.equal(resultText("intl-result-cny"), "—");
  assert.ok(text(byTestId("intl-result-cny")).includes("Thiếu Số USD cần chuyển"));
  await typeId("intl-gross-usd", "14000");
  assert.equal(resultText("intl-result-cny"), "97,626.77 CNY");
  assert.ok(text(byTestId("intl-result-cny")).includes("USD→CNY 7.0123 (LIVE)"));
  assert.equal(resultText("intl-result-vnd"), "367.200.680 VND");
  assert.ok(text(byTestId("intl-result-vnd")).includes("Agribank bán USD 26.180 VND/USD (LIVE)"));
  await clickId("intl-route-HONG_KONG");
  assert.equal(resultText("intl-result-cny"), "95,968.23 CNY");
  await clickId("intl-route-CHINA");
  await clickId("intl-bank-BIDV");
  assert.equal(resultText("intl-result-vnd"), "—", "BIDV unavailable must not produce VND");
  const vt = text(byTestId("intl-result-vnd"));
  assert.ok(vt.includes("BIDV bán USD (VND/USD): UNAVAILABLE") && vt.includes("Tick “Tự nhập toàn bộ thông số” để nhập tay."));
  assert.equal(resultText("intl-result-cny"), "97,626.77 CNY", "CNY must not depend on the VN bank");
  await clickId("intl-bank-AGRIBANK");

  await clickId("intl-mode-B");
  await typeId("intl-target-cny", "10000");
  assert.equal(resultText("intl-result-b-CHINA-AGRIBANK"), "38.999.830 VND");
  assert.equal(resultText("intl-result-b-HONG_KONG-AGRIBANK"), "39.202.044 VND");
  for (const id of ["CHINA-BIDV", "HONG_KONG-BIDV"]) {
    assert.equal(resultText(`intl-result-b-${id}`), "—");
    assert.ok(text(byTestId(`intl-result-b-${id}`)).includes("BIDV bán USD (VND/USD): UNAVAILABLE"));
  }
  assert.equal(resultText("intl-result-b-OUTSIDE"), "—", "Tệ ngoài has no live source");
  assert.ok(text(byTestId("intl-result-b-OUTSIDE")).includes("CNY ngoài (VND/CNY): UNAVAILABLE"));
  const cheapest = $('[data-cheapest="yes"]');
  assert.equal(cheapest.length, 1, "exactly one cheapest");
  assert.equal(cheapest[0].getAttribute("data-testid"), "intl-result-b-CHINA-AGRIBANK");
  assertNoPersistenceWording("OFF/Mode B");
  ok("OFF: BOC/Agribank LIVE, BIDV + CNY ngoài UNAVAILABLE (no HTML fallback), standard fees shown");
  ok("OFF results: A 97,626.77 CNY / 367.200.680 VND, HK 95,968.23 CNY; B cheapest among available only");
}

// ---------------------------------------------------------------------------
console.log("STEP 6b — adversarial feeds never become numbers (same mount, rerun)");
{
  await clickId("intl-mode-A");
  // BIDV claims OK but the official source is not proven.
  const fxA = clone(FX_OK);
  fxA.bidv = { status: "OK", bidv_rate_status: "UNAVAILABLE", sell: 26200, usd_sell_vnd: 26200, html_sell: "26,200" };
  mount(vmWith(fxA));
  await tick(120);
  assert.ok(tool(), "rerun must keep the tool mounted");
  assert.equal(byTestId("intl-rate-bidvSell").getAttribute("data-source"), "UNAVAILABLE");
  assert.ok(!/26[.,]?200/.test(toolText()), "unproven BIDV rate surfaced");
  // BOC not OK but still carrying a number.
  const fxB = clone(FX_OK);
  fxB.boc = { status: "FETCH_ERROR", usd_to_cny: 7.0999, reason: "timeout" };
  mount(vmWith(fxB));
  await tick(120);
  assert.equal(byTestId("intl-rate-usdCny").getAttribute("data-source"), "UNAVAILABLE");
  assert.ok(!toolText().includes("7.0999"), "non-OK BOC number surfaced");
  assert.equal(resultText("intl-result-cny"), "—");
  assert.ok(text(byTestId("intl-result-cny")).includes("Tỷ giá USD→CNY (CNY/USD): UNAVAILABLE"));
  assert.equal(resultText("intl-result-vnd"), "367.200.680 VND", "VND must not depend on BOC");
  // No projection at all.
  const noFx = clone(FIX.success);
  delete noFx.intlFxRates;
  mount(noFx);
  await tick(120);
  for (const k of ["usdCny", "agriSell", "bidvSell", "outsideRate"]) {
    assert.equal(byTestId(`intl-rate-${k}`).getAttribute("data-source"), "UNAVAILABLE", `${k} without projection`);
  }
  assert.equal(resultText("intl-result-cny"), "—");
  assert.equal(resultText("intl-result-vnd"), "—");
  mount(vmWith(clone(FX_OK)));
  await tick(120);
  assert.equal(resultText("intl-result-cny"), "97,626.77 CNY");
  ok("BIDV OK+UNAVAILABLE, BOC FETCH_ERROR+number, missing projection → UNAVAILABLE / —");
}

// ---------------------------------------------------------------------------
console.log("STEP 5/7 — checkbox ON: all 10 inputs visible, labelled, editable");
const EXPECTED_FIELDS = [
  ["usdCny", "Tỷ giá USD→CNY (CNY/USD)", "7.0123"],
  ["agriSell", "Agribank bán USD (VND/USD)", "26180"],
  ["bidvSell", "BIDV bán USD (VND/USD)", ""],
  ["outsideRate", "CNY ngoài (VND/CNY)", ""],
  ["recipientFee", "Phí ngân hàng người nhận (USD)", "35"],
  ["chinaFee", "Phí đại lý Trung Quốc mỗi tranche (CNY)", "150"],
  ["trancheSize", "Kích thước tranche (USD)", "10000"],
  ["hkPct", "Phí Hong Kong (%)", "2"],
  ["vnSwift", "Phí SWIFT Việt Nam (USD)", "5"],
  ["vnPct", "Phí ngân hàng Việt Nam (%)", "0.15"],
];
{
  // Tap the label TEXT (not the 24px box): the whole row is the touch target.
  const cb = byTestId("intl-manual-toggle");
  await clickEl(cb.closest("label").querySelector("span span"), "checkbox label text");
  assert.equal(byTestId("intl-manual-toggle").checked, true, "tapping the label must toggle the checkbox");
  assert.equal(byTestId("intl-params").getAttribute("data-mode"), "manual");
  assert.ok(text(byTestId("intl-params")).includes("MANUAL"), "manual state must be labelled");
  assert.ok(!text(byTestId("intl-params")).includes("LIVE ·"), "manual state must not be labelled LIVE");
  const inputs = $('[data-testid^="intl-param-"]');
  assert.equal(inputs.length, 10, `expected 10 editable parameters, got ${inputs.length}`);
  for (const [key, label, prefill] of EXPECTED_FIELDS) {
    const input = byTestId(`intl-param-${key}`);
    assert.ok(input, `param ${key} missing`);
    assert.equal(input.tagName, "INPUT");
    assert.ok(!input.disabled && !input.readOnly, `${key} must be editable`);
    assert.ok(text(input.closest("label")).startsWith(label), `${key} label "${label}" not visible`);
    assert.equal(input.value, prefill, `${key} prefill (visible = used)`);
    await typeInput(input, "123.5");
    assert.equal(byTestId(`intl-param-${key}`).value, "123.5", `${key} did not accept typing`);
    await typeInput(byTestId(`intl-param-${key}`), prefill);
  }
  assert.ok(text(byTestId("intl-param-bidvSell").closest("label")).includes("BIDV: không có giá LIVE"));
  assert.ok(text(byTestId("intl-param-usdCny").closest("label")).includes("Tham khảo LIVE Bank of China: 7.0123 CNY/USD"));
  assertNoPersistenceWording("ON/prefill");
  ok("label tap toggles; MANUAL labelled; 10 labelled editable inputs, prefilled visibly (BIDV/CNY ngoài blank)");
}

// ---------------------------------------------------------------------------
console.log("STEP 9 — GOLDEN: manual Mode A 14000 USD → 99,685.50 CNY");
{
  assert.equal(byTestId("intl-mode-A").getAttribute("aria-pressed"), "true");
  assert.equal(byTestId("intl-gross-usd").value, "14000");
  assert.equal(byTestId("intl-route-CHINA").getAttribute("aria-pressed"), "true");
  await setParam("usdCny", "7.15");
  await setParam("recipientFee", "30");
  await setParam("chinaFee", "100");
  await setParam("trancheSize", "10000");
  assert.equal(resultText("intl-result-cny"), "99,685.50 CNY");
  assert.equal(byTestId("intl-result-cny").getAttribute("data-value"), "99685.5");
  assert.ok(text(byTestId("intl-result-cny")).includes("USD→CNY 7.15 (MANUAL)"));
  const details = byTestId("intl-breakdown");
  assert.ok(details && details.tagName === "DETAILS" && !details.open, "breakdown must be secondary (collapsed)");
  const bd = text(details);
  for (const s of ["14,000.00 USD", "13,970.00 USD", "99,885.50 CNY", "2 tranche × 100.00 CNY", "200.00 CNY", "99,685.50 CNY"]) {
    assert.ok(bd.includes(s), `breakdown lacks "${s}"`);
  }
  assert.equal(resultText("intl-result-vnd"), "367.200.680 VND", "VND uses the visible Agribank 26180 / 5 USD / 0.15%");
  ok("GOLDEN 99,685.50 CNY (after bank 13,970.00 USD; 99,885.50 CNY; 2 tranche × 100 = 200.00 CNY)");
}

// ---------------------------------------------------------------------------
console.log("STEP 8 — UNKNOWN != ZERO");
{
  await setParam("recipientFee", "");
  assert.equal(resultText("intl-result-cny"), "—");
  assert.equal(byTestId("intl-result-cny").getAttribute("data-value"), "");
  assert.ok(text(byTestId("intl-result-cny")).includes("Thiếu Phí ngân hàng người nhận (USD)"));
  assert.ok(text(byTestId("intl-param-recipientFee").closest("label")).includes("Chưa nhập"));
  assert.ok(!toolText().includes("99,715.50"), "blank fee was coerced to 0");
  assert.equal(resultText("intl-result-vnd"), "367.200.680 VND", "independent result must stay");
  await setParam("recipientFee", "0");
  assert.equal(resultText("intl-result-cny"), "99,900.00 CNY", "typed 0 is a real zero fee");
  await setParam("recipientFee", "abc");
  assert.equal(resultText("intl-result-cny"), "—");
  assert.ok(text(byTestId("intl-result-cny")).includes("Phí ngân hàng người nhận (USD) không hợp lệ"));
  assert.equal(byTestId("intl-param-recipientFee").getAttribute("aria-invalid"), "true");
  await setParam("recipientFee", "30");
  await setParam("usdCny", "");
  assert.equal(resultText("intl-result-cny"), "—");
  assert.ok(text(byTestId("intl-result-cny")).includes("Thiếu Tỷ giá USD→CNY (CNY/USD)"));
  await setParam("usdCny", "7.15");
  await setParam("trancheSize", "0");
  assert.equal(resultText("intl-result-cny"), "—", "tranche size 0 is invalid, not a division result");
  assert.ok(text(byTestId("intl-result-cny")).includes("Kích thước tranche (USD) không hợp lệ"));
  await setParam("trancheSize", "10000");
  await setParam("vnSwift", "");
  assert.equal(resultText("intl-result-vnd"), "—");
  assert.ok(text(byTestId("intl-result-vnd")).includes("Thiếu Phí SWIFT Việt Nam (USD)"));
  await setParam("vnSwift", "5");
  await clickId("intl-bank-BIDV");
  assert.equal(resultText("intl-result-vnd"), "—");
  assert.ok(text(byTestId("intl-result-vnd")).includes("Thiếu BIDV bán USD (VND/USD)"));
  await clickId("intl-bank-AGRIBANK");
  await typeId("intl-gross-usd", "");
  assert.equal(resultText("intl-result-cny"), "—");
  assert.equal(resultText("intl-result-vnd"), "—");
  await typeId("intl-gross-usd", "14000");
  assert.equal(resultText("intl-result-cny"), "99,685.50 CNY");
  ok("blank/invalid → — + named hint (never 0); typed 0 = real 0; independent result unaffected");
}

// ---------------------------------------------------------------------------
console.log("STEP 9b — manual Mode B vector");
{
  await clickId("intl-mode-B");
  assert.equal(byTestId("intl-target-cny").value, "10000");
  await setParam("usdCny", "6.68");
  await setParam("recipientFee", "35");
  await setParam("chinaFee", "150");
  await setParam("outsideRate", "3900");
  assert.equal(resultText("intl-result-b-CHINA-AGRIBANK"), "40.887.735 VND");
  assert.equal(resultText("intl-result-b-HONG_KONG-AGRIBANK"), "41.100.007 VND");
  assert.equal(resultText("intl-result-b-OUTSIDE"), "39.000.000 VND");
  for (const id of ["CHINA-BIDV", "HONG_KONG-BIDV"]) {
    assert.equal(resultText(`intl-result-b-${id}`), "—");
    assert.ok(text(byTestId(`intl-result-b-${id}`)).includes("Thiếu BIDV bán USD (VND/USD)"));
  }
  let cheapest = $('[data-cheapest="yes"]');
  assert.equal(cheapest.length, 1);
  assert.equal(cheapest[0].getAttribute("data-testid"), "intl-result-b-OUTSIDE");
  assert.ok(text(cheapest[0]).includes("★ Rẻ nhất"));
  await setParam("bidvSell", "26000");
  const cards = $('[data-testid^="intl-result-b-"][data-value]').filter((el) => el.getAttribute("data-value") !== "");
  assert.equal(cards.length, 5, "all 5 channels computable once BIDV is typed");
  const min = Math.min(...cards.map((el) => Number(el.getAttribute("data-value"))));
  cheapest = $('[data-cheapest="yes"]');
  assert.equal(cheapest.length, 1);
  assert.equal(Number(cheapest[0].getAttribute("data-value")), min, "highlight must be the minimum");
  assertNoPersistenceWording("ON/Mode B");
  ok("B: China/Agri 40.887.735, HK/Agri 41.100.007, Tệ ngoài 39.000.000 (Rẻ nhất), BIDV — until typed");
}

// ---------------------------------------------------------------------------
console.log("STEP 9c — manual state is local; OFF returns to LIVE truth");
{
  await clickEl(byTestId("intl-manual-toggle"), "checkbox");
  assert.equal(byTestId("intl-manual-toggle").checked, false);
  assert.equal($('[data-testid^="intl-param-"]').length, 0);
  assert.equal(byTestId("intl-rate-usdCny").getAttribute("data-source"), "LIVE");
  assert.ok(text(byTestId("intl-rate-usdCny")).includes("7.0123"), "OFF must show the LIVE rate, not 6.68");
  assert.equal(resultText("intl-result-b-CHINA-AGRIBANK"), "38.999.830 VND");
  assert.equal(resultText("intl-result-b-OUTSIDE"), "—", "manual CNY ngoài must not leak into OFF mode");
  await clickEl(byTestId("intl-manual-toggle"), "checkbox");
  assert.equal(byTestId("intl-param-usdCny").value, "6.68", "re-checking keeps this session's manual values");
  ok("untick → LIVE + standard fees again; re-tick restores the local manual values");
}

// ---------------------------------------------------------------------------
console.log("STEP 10 — no write event, no persistence");
{
  assert.equal(triggers.length, triggersAtStart, `tool emitted ${triggers.length - triggersAtStart} trigger(s)`);
  assert.equal(storageWrites, 0, "tool wrote Web Storage");
  assert.ok(!triggers.some((t) => /intl|snapshot|payment/i.test(String(t.event))), "intl/snapshot trigger seen");
  ok(`0 triggers (of ${triggers.length} total since mount), 0 Web Storage writes`);
  // Positive control: the SAME spy does capture a real bounded event, so the
  // zero above is evidence, not a dead channel.
  await click("Tra cứu thuế / HS", "a", $("aside")[0]);
  await typeInput($('input[aria-label="Mã HS hoặc tên hàng"]')[0], "9403");
  const before = triggers.length;
  await click("Tra cứu", "button");
  await tick(120);
  assert.equal(triggers.slice(before).filter((t) => t.event === "tariff_lookup").length, 1, "trigger spy is dead");
  await click("Thanh toán quốc tế", "a", $("aside")[0]);
  assert.ok(tool(), "back to the tool");
  ok("control: the same spy records exactly one tariff_lookup from the tariff page");
  // Navigation discards everything: nothing was persisted anywhere.
  assert.equal(byTestId("intl-gross-usd").value, "", "amount survived navigation");
  assert.equal(byTestId("intl-manual-toggle").checked, false, "manual mode survived navigation");
  assert.equal(byTestId("intl-mode-A").getAttribute("aria-pressed"), "true");
  ok("leaving and re-opening the tool starts clean (local state only)");
}

// ---------------------------------------------------------------------------
console.log("STEP 11 — mobile ~390px (STRUCTURAL ONLY: jsdom has no layout)");
{
  await clickEl(byTestId("intl-manual-toggle"), "checkbox"); // expose all 10 inputs
  assert.equal($('[data-testid^="intl-param-"]').length, 10);
  const root = byTestId("intl-payment-tool");
  const all = [root, ...$("*", root)];
  const px = (cls, re) => [...cls.matchAll(re)].map((m) => Number(m[1]));
  for (const el of all) {
    const cls = String(el.getAttribute("class") || "");
    for (const n of [...px(cls, /(?:^|\s)min-w-\[(\d+)px\]/g), ...px(cls, /(?:^|\s)w-\[(\d+)px\]/g)]) {
      assert.ok(n <= 358, `fixed width ${n}px exceeds a 390px viewport: ${cls}`);
    }
  }
  assert.equal($("table", root).length, 0, "no wide table in the tool");
  const cbLabel = byTestId("intl-manual-label");
  assert.ok(/min-h-\[(5[6-9]|[6-9]\d)px\]/.test(cbLabel.className), "checkbox row must be a >=56px touch target");
  assert.ok(byTestId("intl-manual-toggle").className.includes("h-6 w-6"), "checkbox box must be 24px");
  for (const input of $("input:not([type=checkbox])", root)) {
    assert.ok(input.className.includes("text-[16px]"), "inputs must be 16px (readable, no iOS zoom)");
    assert.ok(input.className.includes("min-h-[48px]"), "inputs must be >=48px tall");
  }
  for (const b of $("button[aria-pressed]", root)) {
    assert.ok(/min-h-\[(4[4-9]|5\d)px\]/.test(b.className), `choice "${text(b)}" below 44px`);
  }
  const [inputsSec, resultsSec, paramsSec] = ["Đầu vào", "Kết quả", "Tỷ giá và phí"].map((l) =>
    root.querySelector(`section[aria-label="${l}"]`)
  );
  assert.ok(inputsSec.compareDocumentPosition(resultsSec) & window.Node.DOCUMENT_POSITION_FOLLOWING);
  assert.ok(resultsSec.compareDocumentPosition(paramsSec) & window.Node.DOCUMENT_POSITION_FOLLOWING);
  for (const sec of [inputsSec, resultsSec, paramsSec]) {
    assert.ok(sec.className.includes("min-w-0"), "grid children must be allowed to shrink");
  }
  ok("no fixed width > 358px, no table; 56px checkbox row; 16px/48px inputs; inputs → results → params");
}

// ---------------------------------------------------------------------------
console.log("STEP 12 — desktop ~1440px (STRUCTURAL ONLY: jsdom has no layout)");
{
  await clickId("intl-mode-A");
  const grid = tool();
  assert.ok(grid.className.includes("lg:grid-cols-["), "desktop two-column grid missing");
  const sec = (l) => grid.querySelector(`section[aria-label="${l}"]`);
  assert.ok(sec("Đầu vào").className.includes("lg:col-start-1") && sec("Đầu vào").className.includes("lg:row-start-1"));
  assert.ok(sec("Tỷ giá và phí").className.includes("lg:col-start-1") && sec("Tỷ giá và phí").className.includes("lg:row-start-2"));
  assert.ok(sec("Kết quả").className.includes("lg:col-start-2") && sec("Kết quả").className.includes("lg:row-span-2"));
  const headline = byTestId("intl-result-cny").querySelector("p.font-extrabold.tabular-nums");
  assert.ok(headline.className.includes("text-[28px]") && headline.className.includes("md:text-[32px]"), "result must dominate");
  ok("inputs + parameters left, results right (row-span 2); 28–32px result vs 16px inputs; breakdown collapsed");
}

console.log(`\nPASS — ${passed} checks`);
