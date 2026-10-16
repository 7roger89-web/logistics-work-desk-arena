// LOGI-199 Home layout regression: the content-sized urgent-work panel must not
// stretch to the height of the adjacent running-shipment list at wide screens.
// Drives the real compiled React bundle with the existing canonical Home fixture.
import { readFileSync } from "node:fs";
import assert from "node:assert/strict";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const require = createRequire(path.join(ROOT, "component/package.json"));
const { JSDOM } = require("jsdom");
const fixture = JSON.parse(readFileSync(path.join(ROOT, "tests/component/fixtures/view_model_phase_b.json"), "utf8"));
const css = readFileSync(path.join(ROOT, "component/dist/logi-shell.css"), "utf8");

const dom = new JSDOM("<!doctype html><html><body></body></html>", {
  url: "http://localhost/",
  pretendToBeVisual: true,
});
const { window } = dom;
globalThis.window = window;
globalThis.document = window.document;
try { Object.defineProperty(globalThis, "navigator", { value: window.navigator, configurable: true }); } catch {}
for (const key of ["HTMLElement", "HTMLInputElement", "HTMLTextAreaElement", "HTMLSelectElement", "HTMLAnchorElement", "Event", "CustomEvent", "MouseEvent", "KeyboardEvent", "Node", "MutationObserver", "getComputedStyle"]) {
  globalThis[key] = window[key];
}
if (!globalThis.MessageChannel) globalThis.MessageChannel = window.MessageChannel;
window.HTMLElement.prototype.scrollIntoView = () => {};
window.URL.createObjectURL = () => "blob:home-layout-test";
window.URL.revokeObjectURL = () => {};

const host = window.document.createElement("div");
window.document.body.appendChild(host);
const { default: mount } = await import(path.join(ROOT, "component/dist/logi-shell.js"));
mount({
  name: "logi_shell",
  data: fixture,
  parentElement: host,
  setTriggerValue: () => {},
});
await new Promise((resolve) => setTimeout(resolve, 120));

const attention = window.document.querySelector('[data-testid="attention-now"]');
assert.ok(attention, "Home urgent-work panel is present");
const grid = attention.parentElement;
assert.ok(grid.classList.contains("xl:grid-cols-2"), "the panel remains in the existing two-column desktop layout");
assert.ok(grid.classList.contains("xl:items-start"), "desktop grid aligns panels to content height instead of stretching the urgent-work tint");
assert.ok([...window.document.querySelectorAll("h3")].some((heading) => heading.textContent.includes("Trạng thái các lô đang chạy")),
  "the adjacent running-shipment list remains visible");

const rule = css.match(/\.xl\\:items-start\{[^}]+\}/);
assert.ok(rule, "the production CSS bundle contains the responsive xl alignment utility");
assert.match(rule[0], /align-items:flex-start/, "the production utility prevents grid-item stretch");

console.log("HOME_ATTENTION_LAYOUT_DOM=PASS: urgent-work panel keeps its own content height; running-shipment list and production responsive CSS remain present");
