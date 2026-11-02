// ============================================================================
// LOGI-255-RETURN-TO-LIST — DOM acceptance for the in-app "Về danh sách lô"
// control on the shipment detail screen, over the SHIPPED bundle
// component/dist/logi-shell.js.
//
// Consumes a LIVE ViewModel snapshot produced by Python (stdin JSON), so no
// static fixture can mask a backend/frontend contract mismatch.
//
// What this lane proves (and what it deliberately cannot):
//   * the list hands its exact location (q/status/period/from/to/archive) to
//     the detail screen through router state;
//   * the detail screen shows ONE explicit control back to that location, and
//     returning keeps the operator's filters and the visible row set;
//   * a direct entry (no list history) falls back to the plain list.
// It does NOT prove the browser's own Back button: the shell is a MemoryRouter,
// so native Back is measured separately with real Chromium (playwright/
// issue255_return_nav.py). Native Back must never be inferred from this lane.
// ============================================================================

import { readFileSync } from "node:fs";
import assert from "node:assert/strict";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";

// R255_DOM_ROOT lets the same lane run against another checkout (used once to
// prove the lane discriminates: on the pre-fix bundle it must fail).
const ROOT = process.env.R255_DOM_ROOT
  ? path.resolve(process.env.R255_DOM_ROOT)
  : path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const require = createRequire(path.join(ROOT, "component/package.json"));
const { JSDOM } = require("jsdom");

const SNAPSHOTS = JSON.parse(readFileSync(0, "utf8"));
// A query that isolates exactly one lot, taken from the live snapshot (never a
// hard-coded id, so the lane follows whatever the staging seed contains).
const Q = String(SNAPSHOTS.queryShipmentId ?? (SNAPSHOTS.shipmentIds || [])[0]);

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

async function waitFor(predicate, label, timeoutMs = 5000) {
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
  await tick(60);
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

const qInput = () => $('input[placeholder*="Nhập mã lô"]')[0] || null;
const rows = () => $('[data-testid="shipment-row"]').map((el) => el.getAttribute("data-shipment-id"));
const backControl = () => $('[data-testid="shipment-back-to-list"]')[0] || null;
const onDetail = () => Boolean($('[data-testid="shipment-identity-bar"]')[0]);
const listSummary = () => text($('[data-testid="shipment-list-summary"]')[0]);

function setInputValue(el, value) {
  const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
  setter.call(el, value);
  el.dispatchEvent(new window.Event("input", { bubbles: true }));
}

async function gotoList() {
  if (onDetail()) {
    await clickEl($('a[aria-label="Về trang chủ"]')[0]);
    await tick(120);
  }
  await clickEl(await waitFor(() => findClickable("Lô Hàng", "a", $("aside")[0]), "sidebar Lô Hàng"));
  await waitFor(() => $('[data-testid="shipment-period-tat-ca"]')[0], "/lo-hang mounted");
}

async function allTime() {
  await clickEl(await waitFor(() => $('[data-testid="shipment-period-tat-ca"]')[0], "Tất cả thời gian"));
  await waitFor(() => rows().length > 0, "rows after all-time");
}

// ---------------------------------------------------------------- mount list
deliver(SNAPSHOTS.supportView);
await waitFor(() => $("aside a").length > 0, "sidebar mounted");
await gotoList();
await allTime();
const allRows = rows();
assert.ok(allRows.length >= 2, `expected several lots, got ${allRows.length}`);

// ------------------------------------------------- STEP 1: q filter -> detail
const input = qInput();
assert.ok(input, "search input missing");
setInputValue(input, Q);
await waitFor(() => rows().length === 1 && rows()[0] === Q, `list filtered to exactly ${Q}`);
const filteredRows = rows();
assert.deepEqual(filteredRows, [Q], "the q filter must isolate the lot");

const cluster = $('[data-testid="shipment-finance-summary"]')[0];
assert.ok(cluster, "finance cluster missing (finance_view actor expected)");
const clusterHref = cluster.getAttribute("href");
assert.ok(
  clusterHref && clusterHref.startsWith("/lo-hang/") && clusterHref.includes("tab=tai-chinh"),
  `cluster must open the lot's Tài chính tab, got ${clusterHref}`,
);
await clickEl(cluster);
await waitFor(() => onDetail(), "shipment detail opened from the debt cluster");

// ------------------------------------------------- STEP 2: control present
const control = await waitFor(() => backControl(), '"Về danh sách lô" control present');
assert.ok(text(control).includes("Về danh sách lô"), `control label, got "${text(control)}"`);
const returnTo = control.getAttribute("data-return-to");
assert.equal(
  control.getAttribute("href"),
  returnTo,
  "the control must be a real Link whose href is the remembered list location",
);
assert.ok(returnTo.startsWith("/lo-hang"), `must return to the list, got ${returnTo}`);
assert.ok(returnTo.includes(`q=${Q}`), `the remembered location must carry q=${Q}, got ${returnTo}`);
assert.ok(!returnTo.startsWith("/lo-hang/"), `must never return into a record, got ${returnTo}`);

// The detail itself is unchanged: it still opened on Tài chính with its figures.
assert.ok(
  text($('[data-testid="shipment-identity-bar"]')[0]).includes("Trường Thành Logistics"),
  "amount/identity rendering changed unexpectedly",
);

// ------------------------------------------------- STEP 3: return keeps filter
await clickEl(control);
await waitFor(() => !onDetail(), "returned to the list");
await waitFor(() => qInput(), "search input after return");
assert.equal(qInput().value, Q, "q must survive the in-app return");
assert.deepEqual(rows(), filteredRows, "the visible row set must be identical after returning");

// ------------------------------------------- STEP 4: combined filters survive
// q already = Q (one lot). Add the status that lot actually has, plus
// archive = Tất cả and a custom period, then open and return.
await clickEl(findClickable("Lọc", "button"));
await tick(100);
const rowText = text($(`[data-testid="shipment-row"][data-shipment-id="${Q}"]`)[0]);
const chipLabels = ["Chờ giao", "Chờ thông quan", "Đã giao", "Đang vận chuyển", "Hoàn tất"];
const statusLabel = chipLabels.find((label) => rowText.includes(label));
assert.ok(statusLabel, `could not read the lot status from the row: ${rowText.slice(0, 160)}`);
await clickEl(findClickable(statusLabel, "button"));
await waitFor(() => rows().length >= 1, `status ${statusLabel} keeps the lot visible`);
await clickEl($('[data-testid="shipment-archive-tat-ca"]')[0]);
await tick(150);
await clickEl($('[data-testid="shipment-period-khac"]')[0]);
await waitFor(() => $('[data-testid="shipment-date-from"]')[0], "custom period inputs");
setInputValue($('[data-testid="shipment-date-from"]')[0], "2020-01-01");
await tick(80);
setInputValue($('[data-testid="shipment-date-to"]')[0], "2030-12-31");
await tick(250);
const combinedRows = rows();
assert.ok(combinedRows.length > 0, "combined filters must keep at least one lot");
assert.ok(combinedRows.includes(Q), "combined filters must keep the chosen lot");

await clickEl(await waitFor(() => $(`[data-testid="shipment-row"][data-shipment-id="${Q}"] [data-testid="shipment-finance-summary"]`)[0], "cluster under combined filters"));
await waitFor(() => onDetail(), "detail opened under combined filters");
const control2 = await waitFor(() => backControl(), "control under combined filters");
const returnTo2 = control2.getAttribute("data-return-to");
for (const param of [`q=${Q}`, "period=khac", "from=2020-01-01", "to=2030-12-31", "archive=tat-ca", "status="]) {
  assert.ok(returnTo2.includes(param), `remembered list location missing ${param}: ${returnTo2}`);
}
await clickEl(control2);
await waitFor(() => !onDetail(), "returned under combined filters");
await waitFor(() => qInput(), "search input after combined return");
assert.equal(qInput().value, Q, "q must survive the combined-filter return");
assert.equal(
  $('[data-testid="shipment-date-from"]')[0].value,
  "2020-01-01",
  "from must survive the combined-filter return",
);
assert.equal($('[data-testid="shipment-date-to"]')[0].value, "2030-12-31", "to must survive");
assert.deepEqual(rows(), combinedRows, "combined-filter row set must be identical after returning");

// ---------------------------------------- STEP 5: direct entry -> safe fallback
await clickEl(await waitFor(() => $('aside a[href="/"]')[0], "sidebar Tổng quan link"));
await tick(150);
const homeOpen = await waitFor(
  () => $("button").find((b) => /^Mở LO-/.test(text(b))),
  "home priority card opens a lot directly",
);
await clickEl(homeOpen);
await waitFor(() => onDetail(), "detail opened from another entrypoint");
const control3 = await waitFor(() => backControl(), "control on direct entry");
assert.equal(
  control3.getAttribute("data-return-to"),
  "/lo-hang",
  "a direct entry must use the plain-list fallback, never stale filters",
);
await clickEl(control3);
await waitFor(() => !onDetail(), "direct-entry return left the detail");
await waitFor(() => $('[data-testid="shipment-list-summary"]')[0], "list visible after direct-entry return");

console.log("DOM_ACCEPTANCE_ISSUE255_RETURN=PASS");
