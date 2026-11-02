// ============================================================================
// LOGI-255-RETURN-STATE-PRESERVATION-20261102 — DOM acceptance over the SHIPPED
// bundle component/dist/logi-shell.js.
//
// SPEC_REF: Issue #254 / PR #255. The earlier lane
// (dom_acceptance_issue255_return_to_list.mjs) proved open -> return keeps the
// filters. THIS lane proves the sharper path: a REAL setSearchParams navigation
// (tab switch) inside the detail must NOT wipe location.state, otherwise
// "Về danh sách lô" loses the remembered list filters.
//
// On the pre-fix bundle (cb1870f) this lane fails exactly there:
//   after clicking the "Lịch sử" tab, data-return-to collapses from
//   "/lo-hang?...filters..." to "/lo-hang" and the return loses q + rows.
//
// It cannot exercise the browser's own Back button (MemoryRouter); native Back
// is measured separately with real Chromium (evidence/issue254/09-return-state).
// ============================================================================

import { readFileSync } from "node:fs";
import assert from "node:assert/strict";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";

const ROOT = process.env.R255_DOM_ROOT
  ? path.resolve(process.env.R255_DOM_ROOT)
  : path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const require = createRequire(path.join(ROOT, "component/package.json"));
const { JSDOM } = require("jsdom");

const SNAPSHOTS = JSON.parse(readFileSync(0, "utf8"));
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
} catch { /* keep node navigator */ }
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

const mod = await import(path.join(ROOT, "component/dist/logi-shell.js"));
const mount = mod.default;
function deliver(data) {
  mount({ name: "logi_shell", data, parentElement: host, setTriggerValue: () => {} });
}

const qInput = () => $('input[placeholder*="Nhập mã lô"]')[0] || null;
const rows = () => $('[data-testid="shipment-row"]').map((el) => el.getAttribute("data-shipment-id"));
const backControl = () => $('[data-testid="shipment-back-to-list"]')[0] || null;
const onDetail = () => Boolean($('[data-testid="shipment-identity-bar"]')[0]);
const workspace = () => $('[data-testid="journey-global-workspace"]')[0] || null;
const pressedTab = () => {
  const ws = workspace();
  if (!ws) return null;
  const b = $("button", ws).find((el) => el.getAttribute("aria-pressed") === "true");
  return b ? text(b) : null;
};

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

deliver(SNAPSHOTS.supportView);
await waitFor(() => $("aside a").length > 0, "sidebar mounted");
await gotoList();
await clickEl(await waitFor(() => $('[data-testid="shipment-period-tat-ca"]')[0], "Tất cả thời gian"));
await waitFor(() => rows().length > 0, "rows after all-time");
assert.ok(rows().length >= 2, `expected several lots, got ${rows().length}`);

// ------------------------------------------- STEP 1: q filter -> debt cluster
setInputValue(qInput(), Q);
await waitFor(() => rows().length === 1 && rows()[0] === Q, `list filtered to exactly ${Q}`);
const filteredRows = rows();
const cluster = await waitFor(() => $('[data-testid="shipment-finance-summary"]')[0], "finance cluster");
assert.ok((cluster.getAttribute("href") || "").includes("tab=tai-chinh"), "cluster opens tab=tai-chinh");
await clickEl(cluster);
await waitFor(() => onDetail(), "detail opened from the debt cluster");
await waitFor(() => workspace(), "global workspace visible (tab param present)");
assert.equal(pressedTab(), "Tài chính", "detail opened on the Tài chính tab");

// ------------------------------- STEP 2: remembered list location carries q
const control = await waitFor(() => backControl(), '"Về danh sách lô" control');
const returnToBefore = control.getAttribute("data-return-to");
assert.ok(returnToBefore.startsWith("/lo-hang?"), `remembered location must be the filtered list, got ${returnToBefore}`);
assert.ok(returnToBefore.includes(`q=${Q}`), `must carry q=${Q}, got ${returnToBefore}`);

// --------------- STEP 3 (discriminating): a REAL setSp tab switch in the detail
const tabBtn = await waitFor(
  () => $("button", workspace()).find((el) => text(el) === "Lịch sử"),
  '"Lịch sử" tab button inside the Global Workspace',
);
await clickEl(tabBtn);
await waitFor(() => pressedTab() === "Lịch sử", "setSp navigation switched the tab to Lịch sử");
assert.ok(onDetail(), "still on the detail after the tab switch");

// After the setSp navigation, location.state must STILL carry the list location.
const controlAfter = await waitFor(() => backControl(), "control after tab switch");
const returnToAfter = controlAfter.getAttribute("data-return-to");
assert.equal(
  returnToAfter,
  returnToBefore,
  `a tab switch (setSp) must not wipe location.state: before=${returnToBefore} after=${returnToAfter}`,
);
assert.ok(returnToAfter.includes(`q=${Q}`), "the remembered location must still carry q after the tab switch");

// ------------------------------------------- STEP 4: return keeps q and the rows
await clickEl(controlAfter);
await waitFor(() => !onDetail(), "returned to the list");
await waitFor(() => qInput(), "search input after return");
assert.equal(qInput().value, Q, "q must survive open -> tab switch -> return");
assert.deepEqual(rows(), filteredRows, "the visible row set must be identical after the tab-switch return");

// ------------------------------- STEP 5: combined filters survive the same path
await clickEl(findClickable("Lọc", "button"));
await tick(100);
const rowText = text($(`[data-testid="shipment-row"][data-shipment-id="${Q}"]`)[0]);
const chipLabels = ["Chờ giao", "Chờ thông quan", "Đã giao", "Đang vận chuyển", "Hoàn tất"];
const statusLabel = chipLabels.find((label) => rowText.includes(label));
assert.ok(statusLabel, `could not read the lot status from the row: ${rowText.slice(0, 160)}`);
await clickEl(findClickable(statusLabel, "button"));
await waitFor(() => rows().includes(Q), `status ${statusLabel} keeps the lot visible`);
await clickEl($('[data-testid="shipment-archive-tat-ca"]')[0]);
await tick(150);
await clickEl($('[data-testid="shipment-period-khac"]')[0]);
await waitFor(() => $('[data-testid="shipment-date-from"]')[0], "custom period inputs");
setInputValue($('[data-testid="shipment-date-from"]')[0], "2020-01-01");
await tick(80);
setInputValue($('[data-testid="shipment-date-to"]')[0], "2030-12-31");
await tick(250);
const combinedRows = rows();
assert.ok(combinedRows.includes(Q), "combined filters must keep the chosen lot");

await clickEl(await waitFor(
  () => $(`[data-testid="shipment-row"][data-shipment-id="${Q}"] [data-testid="shipment-finance-summary"]`)[0],
  "cluster under combined filters",
));
await waitFor(() => onDetail(), "detail opened under combined filters");
await waitFor(() => workspace(), "workspace under combined filters");
const ctl2 = await waitFor(() => backControl(), "control under combined filters");
const returnTo2 = ctl2.getAttribute("data-return-to");
for (const param of [`q=${Q}`, "period=khac", "from=2020-01-01", "to=2030-12-31", "archive=tat-ca", "status="]) {
  assert.ok(returnTo2.includes(param), `remembered location missing ${param}: ${returnTo2}`);
}
// tab switch again under combined filters — state must survive again
await clickEl(await waitFor(() => $("button", workspace()).find((el) => text(el) === "Thông tin"), '"Thông tin" tab'));
await waitFor(() => pressedTab() === "Thông tin", "setSp switched to tab van-tai (Thông tin)");
const ctl2b = await waitFor(() => backControl(), "control after combined tab switch");
assert.equal(ctl2b.getAttribute("data-return-to"), returnTo2, "combined-filter location must survive the tab switch");
await clickEl(ctl2b);
await waitFor(() => !onDetail(), "returned under combined filters");
await waitFor(() => qInput(), "search input after combined return");
assert.equal(qInput().value, Q, "q must survive the combined-filter tab-switch return");
assert.equal($('[data-testid="shipment-date-from"]')[0].value, "2020-01-01", "from must survive");
assert.equal($('[data-testid="shipment-date-to"]')[0].value, "2030-12-31", "to must survive");
assert.deepEqual(rows(), combinedRows, "combined-filter row set must be identical after the tab-switch return");

// ---------------------------------------- STEP 6: direct entry -> safe fallback
await clickEl(await waitFor(() => $('aside a[href="/"]')[0], "sidebar Tổng quan link"));
await tick(150);
const homeOpen = await waitFor(() => $("button").find((b) => /^Mở LO-/.test(text(b))), "home priority card");
await clickEl(homeOpen);
await waitFor(() => onDetail(), "detail opened from another entrypoint");
const ctl3 = await waitFor(() => backControl(), "control on direct entry");
assert.equal(ctl3.getAttribute("data-return-to"), "/lo-hang", "direct entry must keep the plain-list fallback");
// a tab switch on a direct entry must not invent a list location either
await clickEl(await waitFor(() => $('[data-testid="journey-global-page"]')[0], '"Toàn bộ lô hàng" opens the workspace'));
await waitFor(() => workspace(), "workspace on direct entry");
await clickEl(await waitFor(() => $("button", workspace()).find((el) => text(el) === "Lịch sử"), "tab on direct entry"));
await waitFor(() => pressedTab() === "Lịch sử", "tab switch on direct entry");
const ctl3b = await waitFor(() => backControl(), "control on direct entry after tab switch");
assert.equal(ctl3b.getAttribute("data-return-to"), "/lo-hang", "direct entry must STILL fall back to /lo-hang after a tab switch");
await clickEl(ctl3b);
await waitFor(() => !onDetail(), "direct-entry return left the detail");
await waitFor(() => $('[data-testid="shipment-list-summary"]')[0], "list visible after direct-entry return");

console.log("DOM_ACCEPTANCE_ISSUE255_RETURN_STATE=PASS");
