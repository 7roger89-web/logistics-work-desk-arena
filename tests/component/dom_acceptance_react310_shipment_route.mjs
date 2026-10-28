// React #310 regression: a shipment disappears and reappears in a fresh
// Streamlit view-model while its /lo-hang/:id route stays active. The detail
// must remount, then opening "Sửa thông tin lô" must not crash the shell.
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
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
const click = async (label, selector = "button", root = document) => {
  const target = $(selector, root).find((node) => text(node) === label)
    || $(selector, root).find((node) => text(node).includes(label));
  assert.ok(target, `Missing clickable: ${label}`);
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
const mount = (await import(path.join(ROOT, "component/dist/logi-shell.js"))).default;
const host = document.createElement("div");
document.body.appendChild(host);
const before = { ...FIX.shipmentBefore, lastWrites: [] };
const deliver = (data) => mount({
  name: "logi_shell", data, parentElement: host, setTriggerValue: () => {},
});

deliver(before);
await tick(180);
await click("Lô Hàng", "a", $("aside")[0]);
await click("Tất cả thời gian", "button", byTestId("shipment-period-controls"));
await click(LOT, "a", $("main")[0]);
if (!byTestId("shipment-header-edit-toggle")) {
  const info = document.querySelector('[data-testid="journey-global-page"]');
  if (info) { info.dispatchEvent(new window.MouseEvent("click", { bubbles: true })); await tick(); }
}
assert.ok(byTestId("shipment-header-edit-toggle"), "detail must render with a real shipment");

deliver({ ...before, shipments: before.shipments.filter((row) => row.id !== LOT) });
await tick();
assert.ok(text(document.body).includes(`Không tìm thấy lô ${LOT}`), "safe fallback with missing shipment");
assert.ok(!text(document.body).includes("Logi-good shell gặp lỗi"), "no React error boundary for missing shipment");

deliver(before);
await tick();
const toggle = byTestId("shipment-header-edit-toggle");
assert.ok(toggle, "shipment must return without React #310");
toggle.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
await tick();
assert.equal(byTestId("shipment-header-edit-toggle")?.getAttribute("aria-expanded"), "true");
assert.ok(byTestId("shipment-customer-picker"), "edit disclosure contains customer selector");
assert.ok(!text(document.body).includes("Logi-good shell gặp lỗi"), "opening edit must not crash shell");

// The same instance must also close the edit disclosure without a hook error.
byTestId("shipment-header-edit-toggle").dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
await tick();
assert.equal(byTestId("shipment-header-edit-toggle")?.getAttribute("aria-expanded"), "false", "edit disclosure closes");
assert.ok(!byTestId("shipment-customer-picker"), "closed disclosure hides the customer selector");
assert.ok(!renderErrors.some((message) => /Rendered (more|fewer) hooks|Minified React error #310|React error #310/i.test(message)),
  `React hook-order warning/error: ${renderErrors.join(" | ")}`);
assert.ok(!text(document.body).includes("Logi-good shell gặp lỗi"), "closing edit must not crash shell");
console.error = originalConsoleError;
console.log("G1 React #310 shipment route transition + edit open/close PASS");
