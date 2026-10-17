// DOM contract for explicit workbook column mapping; no spreadsheet parser or
// quote-calculation authority runs in this browser lane.
import assert from "node:assert/strict";
import path from "node:path";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const COMPONENT = path.join(ROOT, "component");
const require = createRequire(path.join(COMPONENT, "package.json"));
const { createServer } = require("vite");
const { JSDOM } = require("jsdom");
const React = require("react");
const { act } = React;

const dom = new JSDOM("<!doctype html><html><body></body></html>", { url: "http://localhost/", pretendToBeVisual: true });
const { window } = dom;
globalThis.window = window;
globalThis.document = window.document;
globalThis.IS_REACT_ACT_ENVIRONMENT = true;
for (const key of ["HTMLElement", "HTMLInputElement", "HTMLTextAreaElement", "HTMLSelectElement", "Event", "MouseEvent", "Node"]) {
  globalThis[key] = window[key];
}
const { createRoot } = require("react-dom/client");

const vite = await createServer({ root: COMPONENT, server: { middlewareMode: true }, appType: "custom", logLevel: "error" });
try {
  const { default: ExcelWorkbookMapping } = await vite.ssrLoadModule("/src/components/ExcelWorkbookMapping.tsx");
  const page = {
    sheet: "Freight schedule", sheet_index: 1, classification: "UNCLASSIFIED", sheet_state: "visible",
    row_count: 4, column_count: 7, read_only: true, locked: false, merges: [],
    cells: [
      { r: 3, c: 2, value: "Service" }, { r: 3, c: 3, value: "Qty" }, { r: 3, c: 4, value: "Unit" },
      { r: 3, c: 5, value: "Rate" }, { r: 3, c: 6, value: "Currency" }, { r: 3, c: 7, value: "Notes" },
      { r: 4, c: 2, value: "Ocean freight 40HQ" }, { r: 4, c: 3, value: 1 }, { r: 4, c: 4, value: "container" },
      { r: 4, c: 5, value: 1250 }, { r: 4, c: 6, value: "USD" }, { r: 4, c: 7, value: "Valid through Dec 31" },
    ],
    column_widths: {}, row_heights: {}, hidden_rows: [], hidden_columns: [], frozen_panes: "", truncated: false,
    limits: { max_rows: 200, max_cols: 40, max_cells: 4000 },
  };
  const source = { file_name: "freight.xlsx", byte_size: 1234, sha256: "abc123", sheet_names: ["Freight schedule"],
    goods_sheet: "", parser_version: "unmapped/1", storage_file_id: "opaque-id" };
  let applied = [];
  const host = document.createElement("div");
  document.body.appendChild(host);
  const root = createRoot(host);
  const render = async () => act(async () => root.render(React.createElement(ExcelWorkbookMapping, { page, source, onApply: (draft) => applied.push(draft) })));
  const setControl = async (testId, value) => act(async () => {
    const element = host.querySelector(`[data-testid="${testId}"]`);
    assert.ok(element, `missing ${testId}`);
    const prototype = element.tagName === "SELECT" ? window.HTMLSelectElement.prototype : window.HTMLInputElement.prototype;
    Object.getOwnPropertyDescriptor(prototype, "value").set.call(element, value);
    element.dispatchEvent(new window.Event("input", { bubbles: true }));
    element.dispatchEvent(new window.Event("change", { bubbles: true }));
  });
  const click = async (testId) => act(async () => {
    const element = host.querySelector(`[data-testid="${testId}"]`);
    assert.ok(element, `missing ${testId}`);
    element.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
  });
  const value = (testId) => host.querySelector(`[data-testid="${testId}"]`)?.value;

  await render();
  // A service-only mapping cannot silently assume quantity=1.
  await setControl("excel-map-header-row", "3");
  await setControl("excel-map-first-row", "4");
  await setControl("excel-map-last-row", "4");
  await setControl("excel-map-column-name", "2");
  await setControl("excel-map-column-price", "5");
  await setControl("excel-map-fixed-currency", "USD");
  await click("excel-workbook-map-apply");
  assert.match(host.textContent, /không tự mặc định là 1/);
  assert.equal(applied.length, 0);
  console.log("  ✓ Missing service quantity is surfaced; mapping does not invent one");

  await setControl("excel-map-column-qty", "3");
  await setControl("excel-map-column-unit", "4");
  await setControl("excel-map-column-currency", "6");
  await setControl("excel-map-column-note", "7");
  await setControl("excel-map-price-role", "SELL");
  await click("excel-workbook-map-apply");
  assert.equal(applied.length, 1);
  assert.equal(applied[0].goods_mode, "SERVICE_ONLY");
  assert.deepEqual(applied[0].goods, []);
  const sellLine = applied[0].options.A.service_lines[0];
  assert.equal(sellLine.service_name, "Ocean freight 40HQ");
  assert.equal(sellLine.qty, "1");
  assert.equal(sellLine.unit, "container");
  assert.equal(sellLine.currency, "USD");
  assert.equal(sellLine.sell_unit, "1250");
  assert.equal(sellLine.cost_unit, null);
  assert.equal(sellLine.sell_confirmed, false);
  assert.equal(sellLine.internal_note, "Valid through Dec 31");
  console.log("  ✓ Explicit sell-price mapping creates a service-only draft without a fake goods row");

  await setControl("excel-map-price-role", "COST");
  await click("excel-workbook-map-apply");
  const costLine = applied[1].options.A.service_lines[0];
  assert.equal(costLine.cost_unit, "1250");
  assert.equal(costLine.sell_unit, null);
  assert.equal(costLine.sell_confirmed, false);
  assert.match(costLine.cost_source, /giá vốn/);
  console.log("  ✓ Explicit cost mapping remains internal and leaves customer selling price unknown");

  await act(async () => root.unmount());
  console.log("DOM WORKBOOK MAPPING PASS — explicit range/columns, currency and price role; no automatic assumptions");
} finally {
  await vite.close();
  dom.window.close();
}
