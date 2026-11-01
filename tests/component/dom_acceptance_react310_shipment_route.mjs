// React #310 regression: a shipment disappears and reappears in a fresh
// Streamlit view-model while its /lo-hang/:id route stays active. The detail
// must remount, then opening "Sửa thông tin lô" must not crash the shell.
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { createRequire } from "node:module";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const require = createRequire(path.join(ROOT, "component/package.json"));
const { JSDOM } = require("jsdom");
const FIX = JSON.parse(readFileSync(path.join(ROOT, "tests/component/fixtures/view_model_contract_shipment_edit.json"), "utf8"));
const LOT = FIX.shipment;
const dom = new JSDOM("<!DOCTYPE html><html><body></body></html>", {
  url: `http://localhost:8501/lo-hang/${LOT}`,
  pretendToBeVisual: true,
});
const { window } = dom;
globalThis.window = window;
globalThis.document = window.document;
try { Object.defineProperty(globalThis, "navigator", { value: window.navigator, configurable: true }); } catch {}
for (const k of [
  "HTMLElement", "HTMLInputElement", "HTMLTextAreaElement", "HTMLSelectElement",
  "HTMLAnchorElement", "Event", "CustomEvent", "MouseEvent", "KeyboardEvent",
  "Node", "MutationObserver", "getComputedStyle",
]) globalThis[k] = window[k];
if (!globalThis.MessageChannel) globalThis.MessageChannel = window.MessageChannel;
window.HTMLElement.prototype.scrollIntoView = () => {};

const $ = (selector, root = document) => [...root.querySelectorAll(selector)];
const text = (node) => (node?.textContent || "").replace(/\s+/g, " ").trim();
const waitFor = async (read, message) => {
  const deadline = Date.now() + 5000;
  while (Date.now() < deadline) {
    const result = read();
    if (result) return result;
    await new Promise((resolve) => setTimeout(resolve, 25));
  }
  assert.fail(message);
};
const click = async (label, selector = "button", root = document) => {
  const target = await waitFor(() => $(selector, root).find((node) => text(node) === label)
    || $(selector, root).find((node) => text(node).includes(label)), `Missing clickable: ${label}`);
  target.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
  await new Promise((resolve) => setTimeout(resolve, 140));
};
const tick = (ms = 150) => new Promise((resolve) => setTimeout(resolve, ms));
const byTestId = (id) => document.querySelector(`[data-testid="${id}"]`);
const renderErrors = [];
const originalConsoleError = console.error;
console.error = (...args) => {
  const message = args.map(String).join(" ");
  renderErrors.push(message);
  originalConsoleError(...args);
};
window.addEventListener("error", (event) => renderErrors.push(String(event.error ?? event.message)));
const mount = (await import(pathToFileURL(path.join(ROOT, "component/dist/logi-shell.js")).href)).default;
const host = document.createElement("div");
document.body.appendChild(host);
const before = { ...FIX.shipmentBefore, lastWrites: [] };
const triggers = [];
const deliver = (data) => mount({
  name: "logi_shell", data, parentElement: host, setTriggerValue: (event, value) => triggers.push({ event, value }),
});

deliver(before);
await tick(180);
await click("Lô Hàng", "a", $("aside")[0]);
await click("Tất cả thời gian", "button", byTestId("shipment-period-controls"));
await click(LOT, "a", $("main")[0]);
await waitFor(() => byTestId("journey-global-page"), "shipment detail must mount");
if (!byTestId("shipment-header-edit-toggle")) {
  await click("MỞ THÔNG TIN LÔ");
}
await waitFor(() => byTestId("shipment-header-edit-toggle"), "detail must render with a real shipment");

// A fresh shipment can acquire Journey nodes on the same mounted detail.
// Use a real existing Journey projection; only transport it onto this test lot.
const journeyFixture = JSON.parse(readFileSync(path.join(ROOT, "tests/component/fixtures/view_model_journey_fresh_188.json"), "utf8"));
const journeyShipment = journeyFixture.before.shipments.find((row) => row.id === LOT);
assert.ok(journeyShipment?.journey?.nodes?.length, "real Journey projection for this lot must exist in fixture");
deliver({ ...before, shipments: before.shipments.map((row) => row.id === LOT ? { ...row, journey: journeyShipment.journey } : row) });
await tick();
await waitFor(() => byTestId("shipment-journey") && byTestId("shipment-journey").getAttribute("data-empty-journey") !== "true", "Journey nodes must arrive");
assert.ok(!text(document.body).includes("Logi-good shell gặp lỗi"), "adding Journey nodes must not change Hook order");
assert.ok(byTestId("shipment-journey"), "Journey renders after nodes arrive");
deliver(before);
await tick();
await waitFor(() => byTestId("shipment-journey")?.getAttribute("data-empty-journey") === "true", "Journey nodes must clear");
assert.ok(!text(document.body).includes("Logi-good shell gặp lỗi"), "removing Journey nodes must not change Hook order");

deliver({ ...before, shipments: before.shipments.filter((row) => row.id !== LOT) });
await tick();
await waitFor(() => text(document.body).includes(`Không tìm thấy lô ${LOT}`), "safe fallback with missing shipment");
assert.ok(!text(document.body).includes("Logi-good shell gặp lỗi"), "no React error boundary for missing shipment");

deliver(before);
await tick();
const toggle = await waitFor(() => byTestId("shipment-header-edit-toggle"), "shipment must return without React #310");
assert.ok(toggle, "shipment must return without React #310");
toggle.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
await tick();
await waitFor(() => byTestId("shipment-header-edit-toggle")?.getAttribute("aria-expanded") === "true", "edit disclosure opens");
assert.ok(byTestId("shipment-customer-picker"), "edit disclosure contains customer selector");
assert.ok(!text(document.body).includes("Logi-good shell gặp lỗi"), "opening edit must not crash shell");

// The same instance must also close the edit disclosure without a hook error.
byTestId("shipment-header-edit-toggle").dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
await tick();
await waitFor(() => byTestId("shipment-header-edit-toggle")?.getAttribute("aria-expanded") === "false", "edit disclosure closes");
assert.ok(!byTestId("shipment-customer-picker"), "closed disclosure hides the customer selector");

// A date send is not a save: only this request's backend success AND matching
// canonical readback may display success. This catches the runtime viewer
// failure: the writer refused while saveHeaderDate toasted green immediately.
await click("Sửa thông tin lô");
const editDate = async (value) => {
  const input = document.querySelector('#fld-created-at');
  Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set.call(input, value);
  input.dispatchEvent(new window.Event('input', { bubbles: true }));
  await tick();
};
const sendDate = async (value) => {
  await editDate(value);
  await click('LƯU NGÀY TẠO');
  return triggers.filter(t => t.event === 'shipment_field_save').at(-1).value.payload;
};
const pending = await sendDate('21/10/2026');
assert.ok(pending.requestId);
assert.ok(byTestId('shipment-header-date-pending'));
assert.ok(!text(document.body).includes('Đã lưu ngày tạo'), 'sending must never toast success');
await click('LƯU NGÀY TẠO');
assert.equal(triggers.filter(t => t.event === 'shipment_field_save').length, 1, 'pending date must not send twice');
const outcome = (requestId, ok, extra = {}) => ({event:'shipment_field_save',shipmentId:LOT,requestId,ok,...extra});
deliver({...before,lastWrites:[outcome('stale-request',true,{persisted:{created_at:'2026-10-21'}})]});
await tick();
assert.ok(byTestId('shipment-header-date-pending'), 'stale success cannot settle new intent');
deliver({...before,lastWrites:[outcome(pending.requestId,false,{error:'RBAC: không có quyền shipment_edit.'})]});
await tick();
assert.match(text(byTestId('shipment-header-date-error')),/RBAC/);
assert.ok(!text(document.body).includes('Đã lưu ngày tạo'), 'denied date must not toast success');
const mismatched = await sendDate('21/10/2026');
deliver({...before,lastWrites:[outcome(mismatched.requestId,true,{persisted:{created_at:'2026-10-21'}})]});
await tick();
assert.match(text(byTestId('shipment-header-date-error')),/đọc lại chưa khớp/);
assert.ok(!text(document.body).includes('Đã lưu ngày tạo'), 'success without matching VM is unconfirmed');
const accepted = await sendDate('21/10/2026');
const saved = {...before, shipments:before.shipments.map(s=>s.id===LOT?{...s,createdAt:'21/10/2026'}:s),
  lastWrites:[outcome(accepted.requestId,true,{persisted:{created_at:'2026-10-21'}})]};
deliver(saved);await tick();
assert.ok(text(document.body).includes('Đã lưu ngày tạo 21/10/2026'));
assert.ok(!byTestId('shipment-header-date-pending'));
assert.equal(document.querySelector('#fld-created-at').value,'21/10/2026');
const cleared = await sendDate('');
deliver({...saved,shipments:saved.shipments.map(s=>s.id===LOT?{...s,createdAt:''}:s),
  lastWrites:[outcome(cleared.requestId,true,{persisted:{created_at:''}})]});await tick();
assert.equal(document.querySelector('#fld-created-at').value,'');
assert.ok(text(document.body).includes('Đã xoá ngày tạo'));
console.log('Header date pending/stale/denied/mismatched/confirmed/blank outcomes PASS');
assert.ok(!renderErrors.some((message) => /Rendered (more|fewer) hooks|Minified React error #310|React error #310/i.test(message)),
  `React hook-order warning/error: ${renderErrors.join(" | ")}`);
assert.ok(!text(document.body).includes("Logi-good shell gặp lỗi"), "closing edit must not crash shell");
console.error = originalConsoleError;
console.log("G1 React #310 Journey empty/ready + shipment absent/present + edit open/close PASS");
