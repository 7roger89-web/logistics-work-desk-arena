// ============================================================================
// Issue #254 DOM acceptance — Service debt at a glance on /lo-hang
// (desktop table + mobile card) over the shipped bundle component/dist/logi-shell.js.
//
// Consumes LIVE ViewModel snapshots produced by Python (stdin JSON) so zero
// static fixture drift can mask backend/frontend contract mismatches.
// ============================================================================

import { readFileSync } from "node:fs";
import assert from "node:assert/strict";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const require = createRequire(path.join(ROOT, "component/package.json"));
const { JSDOM } = require("jsdom");

const inputRaw = readFileSync(0, "utf8");
const SNAPSHOTS = JSON.parse(inputRaw);

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

const tick = (ms = 40) => new Promise((r) => setTimeout(r, ms));
const $ = (sel, root = window.document) => [...root.querySelectorAll(sel)];
const text = (el) => (el?.textContent || "").replace(/\s+/g, " ").trim();

async function waitFor(predicate, label, timeoutMs = 4000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    const val = predicate();
    if (val) return val;
    await tick(30);
  }
  assert.fail(`Timed out waiting for: ${label}`);
}

function findClickable(needle, sel = "a,button", root = window.document) {
  const els = $(sel, root);
  return els.find((el) => text(el) === needle)
    || els.find((el) => text(el).startsWith(needle))
    || els.find((el) => text(el).includes(needle))
    || null;
}

async function clickEl(el) {
  assert.ok(el, "clickable element missing");
  el.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
  await tick(50);
}

const host = window.document.createElement("div");
window.document.body.appendChild(host);

const triggers = [];
const mod = await import(path.join(ROOT, "component/dist/logi-shell.js"));
assert.equal(typeof mod.default, "function", "bundle must default-export mount");
const mount = mod.default;

function deliver(data) {
  mount({
    name: "logi_shell",
    data,
    parentElement: host,
    setTriggerValue: (event, value) => triggers.push({ event, value }),
  });
}

function clusterValues(container) {
  const summary = container.querySelector('[data-testid="shipment-finance-summary"]');
  if (!summary) return null;
  return {
    el: summary,
    ccy: summary.getAttribute("data-currency"),
    hasActual: summary.getAttribute("data-has-actual"),
    receivable: text(summary.querySelector('[data-testid="debt-receivable"]')),
    received: text(summary.querySelector('[data-testid="debt-received"]')),
    outstanding: text(summary.querySelector('[data-testid="debt-outstanding"]')),
    rawText: text(summary),
  };
}

// 1. Mount Support initial view-model and navigate to /lo-hang (all time)
deliver(SNAPSHOTS.supportInitial);
await waitFor(() => $("aside a").length > 0, "sidebar mounted");
await clickEl(findClickable("Lô Hàng", "a", $("aside")[0]));
const allTimeBtn = await waitFor(
  () => $('[data-testid="shipment-period-tat-ca"]')[0] || findClickable("Tất cả thời gian", "button"),
  "Tất cả thời gian period button"
);
await clickEl(allTimeBtn);
await waitFor(
  () => $('[data-testid="shipment-row"]').length === SNAPSHOTS.supportInitial.shipments.length,
  `all ${SNAPSHOTS.supportInitial.shipments.length} shipment rows rendered`
);

// Single compact column header (6 columns total, NEVER 3 separate money columns)
const headers = $("table.tbl thead th").map(text);
assert.equal(
  headers.length,
  6,
  `expected 6 desktop columns (including single Công nợ dịch vụ cluster), got ${headers.length}: ${JSON.stringify(headers)}`
);
assert.ok(headers.includes("Công nợ dịch vụ"), `missing Công nợ dịch vụ header: ${JSON.stringify(headers)}`);
assert.ok(headers.includes("Việc tiếp theo"), "Việc tiếp theo column must stay intact");

// Check every lot across BOTH desktop rows and mobile cards
for (const kind of ["shipment-row", "shipment-mobile-card"]) {
  const items = $(`[data-testid="${kind}"]`);
  assert.equal(items.length, SNAPSHOTS.supportInitial.shipments.length, `${kind} count mismatch`);

  const byId = new Map(items.map((el) => [el.getAttribute("data-shipment-id"), el]));

  // (a) VND lot with Finance Actual lines
  const vndCluster = clusterValues(byId.get(SNAPSHOTS.ids.vndActual));
  assert.ok(vndCluster, `${kind}: missing finance cluster on VND actual lot`);
  assert.equal(vndCluster.receivable, SNAPSHOTS.expected.vndInitial.receivable);
  assert.equal(vndCluster.received, SNAPSHOTS.expected.vndInitial.received);
  assert.equal(vndCluster.outstanding, SNAPSHOTS.expected.vndInitial.outstanding);

  // (b) WRONG_PASS guard: Quote-only lot (positive quote, zero Finance Actual lines)
  const quoteOnlyCluster = clusterValues(byId.get(SNAPSHOTS.ids.quoteOnly));
  assert.ok(quoteOnlyCluster, `${kind}: missing finance cluster on quote-only lot`);
  assert.equal(quoteOnlyCluster.hasActual, "false");
  assert.equal(quoteOnlyCluster.receivable, "—", "quote-only receivable must render —");
  assert.equal(quoteOnlyCluster.received, "0 VND", "valid zero receipt renders 0 VND");
  assert.equal(quoteOnlyCluster.outstanding, "—", "quote-only outstanding must render —, never 0 VND");
  assert.ok(!quoteOnlyCluster.rawText.includes(SNAPSHOTS.forbiddenQuoteFormatted), "quote estimate must never appear as debt");
  assert.ok(!quoteOnlyCluster.rawText.toLowerCase().includes("đã thanh toán đủ"), "quote-only must never claim settled");

  // (c) Quote-only lot WITH deposit already received (still no Finance Actual lines)
  const depositOnlyCluster = clusterValues(byId.get(SNAPSHOTS.ids.depositNoActual));
  assert.ok(depositOnlyCluster, `${kind}: missing finance cluster on deposit-without-actual lot`);
  assert.equal(depositOnlyCluster.receivable, "—");
  assert.equal(depositOnlyCluster.received, SNAPSHOTS.expected.depositNoActual.received);
  assert.equal(depositOnlyCluster.outstanding, "—", "deposit without actual lines must keep outstanding —");

  // (d) Multi-currency: USD and CNY lots show exact currency, zero FX conversion
  const usdCluster = clusterValues(byId.get(SNAPSHOTS.ids.usdActual));
  assert.equal(usdCluster.receivable, "2.400 USD");
  assert.equal(usdCluster.received, "900 USD");
  assert.equal(usdCluster.outstanding, "1.500 USD");

  const cnyCluster = clusterValues(byId.get(SNAPSHOTS.ids.cnySettled));
  assert.equal(cnyCluster.receivable, "18.000 CNY");
  assert.equal(cnyCluster.received, "18.000 CNY");
  assert.equal(cnyCluster.outstanding, "0 CNY");

  // Mobile card no-overflow structural check + single XỬ LÝ button rule
  if (kind === "shipment-mobile-card") {
    for (const card of items) {
      assert.equal($("[class*='overflow-x-auto']", card).length, 0, "mobile card must not add overflow-x-auto");
      assert.equal(
        $("*", card).filter((el) => /min-w-\[\d{3,}px\]/.test(String(el.className || ""))).length,
        0,
        "mobile card must not carry wide desktop min-width"
      );
    }
  } else {
    for (const row of items) {
      const actionHandles = $("a,button", row).filter((el) => text(el).includes("XỬ LÝ"));
      assert.equal(actionHandles.length, 1, "desktop row must keep exactly one XỬ LÝ primary handle");
    }
  }
}

// 2. Payment recorded -> reload updates /lo-hang desktop + mobile immediately
deliver(SNAPSHOTS.supportAfterPayment);
await tick(120);
for (const kind of ["shipment-row", "shipment-mobile-card"]) {
  const el = $(`[data-testid="${kind}"][data-shipment-id="${SNAPSHOTS.ids.vndActual}"]`)[0];
  const c = clusterValues(el);
  assert.equal(c.receivable, SNAPSHOTS.expected.vndAfterPayment.receivable);
  assert.equal(c.received, SNAPSHOTS.expected.vndAfterPayment.received);
  assert.equal(c.outstanding, SNAPSHOTS.expected.vndAfterPayment.outstanding);
}

// 3. WRONG_PASS guard: Payment reversed/cancelled -> reload updates /lo-hang (never stale)
deliver(SNAPSHOTS.supportAfterReversal);
await tick(120);
for (const kind of ["shipment-row", "shipment-mobile-card"]) {
  const el = $(`[data-testid="${kind}"][data-shipment-id="${SNAPSHOTS.ids.vndActual}"]`)[0];
  const c = clusterValues(el);
  assert.equal(c.receivable, SNAPSHOTS.expected.vndInitial.receivable);
  assert.equal(c.received, SNAPSHOTS.expected.vndInitial.received);
  assert.equal(c.outstanding, SNAPSHOTS.expected.vndInitial.outstanding);
}

// 4. Clicking the cluster opens ShipmentDetail directly on Tài chính / Công nợ tab
{
  const row = $(`[data-testid="shipment-row"][data-shipment-id="${SNAPSHOTS.ids.vndActual}"]`)[0];
  const summaryLink = row.querySelector('[data-testid="shipment-finance-summary"]');
  await clickEl(summaryLink);
  await waitFor(() => text(window.document.body).includes("Lịch sử thu / chi"), "Tài chính / Công nợ tab opened");
  const pageText = text(window.document.body);
  assert.ok(pageText.includes(`Lô hàng ${SNAPSHOTS.ids.vndActual}`), "clicking cluster must open shipment detail");
  assert.ok(pageText.includes("Lịch sử thu / chi"), "clicking cluster must open Tài chính / Công nợ tab");
  // Navigate back to /lo-hang
  await clickEl(findClickable("Lô Hàng", "a", $("aside")[0]));
  const allTimeAgain = await waitFor(
    () => $('[data-testid="shipment-period-tat-ca"]')[0] || findClickable("Tất cả thời gian", "button"),
    "Tất cả thời gian period button after return"
  );
  await clickEl(allTimeAgain);
  await waitFor(
    () => $('[data-testid="shipment-row"]').length === SNAPSHOTS.supportInitial.shipments.length,
    "returned to full /lo-hang list"
  );
}

// 5. WRONG_PASS guard: Sale role (no finance_view) sees ZERO finance clusters and ZERO debt figures
deliver(SNAPSHOTS.saleView);
await waitFor(() => $("table.tbl thead th").length === 5, "Sale 5-column table rendered");
assert.equal(
  $('[data-testid="shipment-finance-summary"]').length,
  0,
  "Sale without finance_view must see zero shipment-finance-summary clusters"
);
const saleHeaders = $("table.tbl thead th").map(text);
assert.equal(saleHeaders.length, 5, `Sale table must have 5 columns without Công nợ dịch vụ: ${JSON.stringify(saleHeaders)}`);
assert.ok(!saleHeaders.includes("Công nợ dịch vụ"), "Sale must not see Công nợ dịch vụ column");
const saleListText = text($("main")[0] || window.document.body);
for (const secret of SNAPSHOTS.secretFiguresForSale) {
  assert.ok(!saleListText.includes(secret), `Sale UI leaked unauthorized money figure: ${secret}`);
}

console.log("DOM_ACCEPTANCE_ISSUE254=PASS");
