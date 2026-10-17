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
  const { mergeMappedExcelQuoteDraft } = await vite.ssrLoadModule("/src/lib/excelQuote.ts");
  const page = {
    sheet: "Ocean Freight", sheet_index: 1, classification: "UNCLASSIFIED", sheet_state: "visible",
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
  const source = { file_name: "multi-sheet.xlsx", byte_size: 1234, sha256: "abc123", sheet_names: ["Ocean Freight", "Port charges", "Customer goods tab"],
    goods_sheet: "", parser_version: "unmapped/1", storage_file_id: "opaque-id" };
  const pagePort = {
    sheet: "Port charges", sheet_index: 1, classification: "UNCLASSIFIED", sheet_state: "visible",
    row_count: 3, column_count: 5, read_only: true, locked: false, merges: [],
    cells: [
      { r: 1, c: 1, value: "Service" }, { r: 1, c: 2, value: "Qty" }, { r: 1, c: 3, value: "Unit" },
      { r: 1, c: 4, value: "Cost" }, { r: 1, c: 5, value: "Currency" },
      { r: 2, c: 1, value: "THC" }, { r: 2, c: 2, value: 1 }, { r: 2, c: 3, value: "container" },
      { r: 2, c: 4, value: 210 }, { r: 2, c: 5, value: "USD" },
      { r: 3, c: 1, value: "D/O" }, { r: 3, c: 2, value: 1 }, { r: 3, c: 3, value: "shipment" },
      { r: 3, c: 4, value: 55 }, { r: 3, c: 5, value: "USD" },
    ],
    column_widths: {}, row_heights: {}, hidden_rows: [], hidden_columns: [], frozen_panes: "", truncated: false,
    limits: { max_rows: 200, max_cols: 40, max_cells: 4000 },
  };
  const pageGoods = {
    sheet: "Customer goods tab", sheet_index: 2, classification: "UNCLASSIFIED", sheet_state: "visible",
    row_count: 2, column_count: 3, read_only: true, locked: false, merges: [],
    cells: [
      { r: 1, c: 1, value: "Item" }, { r: 1, c: 2, value: "Currency" }, { r: 1, c: 3, value: "Supplier cost" },
      { r: 2, c: 1, value: "Cabinet" }, { r: 2, c: 2, value: "CNY" }, { r: 2, c: 3, value: 870 },
    ],
    column_widths: {}, row_heights: {}, hidden_rows: [], hidden_columns: [], frozen_panes: "", truncated: false,
    limits: { max_rows: 200, max_cols: 40, max_cells: 4000 },
  };
  let applied = [];
  const host = document.createElement("div");
  document.body.appendChild(host);
  const root = createRoot(host);
  const render = async (nextPage = page) => act(async () => root.render(React.createElement(ExcelWorkbookMapping, {
    key: `${source.sha256}:${nextPage.sheet}`, page: nextPage, source, onApply: (draft) => applied.push(draft),
  })));
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

  await render(pagePort);
  await setControl("excel-map-header-row", "1");
  await setControl("excel-map-first-row", "2");
  await setControl("excel-map-last-row", "2");
  await setControl("excel-map-column-name", "1");
  await setControl("excel-map-column-qty", "2");
  await setControl("excel-map-column-unit", "3");
  await setControl("excel-map-column-price", "4");
  await setControl("excel-map-column-currency", "5");
  await setControl("excel-map-price-role", "COST");
  await click("excel-workbook-map-apply");
  const portFirst = applied[2];
  assert.deepEqual(portFirst.options.A.service_lines.map((line) => line.service_name), ["THC"]);

  const serviceOnly = mergeMappedExcelQuoteDraft(null, applied[1]);
  const alternateOptionLine = { ...serviceOnly.options.A.service_lines[0], id: "existing-option-b", service_name: "Alternate option service" };
  const serviceOnlyWithAlternate = {
    ...serviceOnly,
    options: { ...serviceOnly.options, B: { ...serviceOnly.options.B, scope: "Alternate option", service_lines: [alternateOptionLine] } },
  };
  const afterPortFirst = mergeMappedExcelQuoteDraft(serviceOnlyWithAlternate, portFirst);
  assert.deepEqual(afterPortFirst.options.A.service_lines.map((line) => line.service_name), ["Ocean freight 40HQ", "THC"]);
  assert.deepEqual(afterPortFirst.options.B.service_lines, [alternateOptionLine]);
  await setControl("excel-map-last-row", "3");
  await click("excel-workbook-map-apply");
  const portMapping = applied[3];
  assert.deepEqual(portMapping.options.A.service_lines.map((line) => line.service_name), ["THC", "D/O"]);
  assert.ok(portMapping.options.A.service_lines.every((line) => line.sell_unit === null && line.tax_pct === null));
  assert.ok(portMapping.options.A.service_lines.every((line) => !line.id.includes("Port charges")));

  const multiSheetServices = mergeMappedExcelQuoteDraft(afterPortFirst, portMapping);
  assert.equal(multiSheetServices.goods_mode, "SERVICE_ONLY");
  assert.equal(multiSheetServices.goods.length, 0);
  assert.deepEqual(multiSheetServices.options.A.service_lines.map((line) => line.service_name), [
    "Ocean freight 40HQ", "THC", "D/O",
  ]);
  assert.equal(multiSheetServices.options.A.service_lines.length, 3);
  console.log("  ✓ Ocean Freight + overlapping Port charges ranges merge to three service rows in one option");

  const saleEdited = structuredClone(multiSheetServices);
  Object.assign(saleEdited.options.A.service_lines[1], {
    sell_unit: "300", sell_confirmed: true, tax_pct: "8", public_note: "Điều kiện báo giá",
  });
  const costReMap = structuredClone(portMapping);
  costReMap.options.A.service_lines[0].cost_unit = "212";
  const costReApplied = mergeMappedExcelQuoteDraft(saleEdited, costReMap);
  const keptThc = costReApplied.options.A.service_lines[1];
  assert.equal(costReApplied.options.A.service_lines.length, 3);
  assert.equal(keptThc.cost_unit, "212");
  assert.equal(keptThc.sell_unit, "300");
  assert.equal(keptThc.sell_confirmed, true);
  assert.equal(keptThc.tax_pct, "8");
  assert.equal(keptThc.public_note, "Điều kiện báo giá");
  assert.equal(costReApplied.options.A.service_lines[0].cost_unit, "1250");
  assert.equal(costReApplied.options.A.service_lines[2].service_name, "D/O");
  assert.deepEqual(costReApplied.options.B.service_lines, [alternateOptionLine]);
  console.log("  ✓ COST re-map refreshes cost and preserves confirmed Sale price, VAT and public note");

  const sellReMap = structuredClone(portMapping);
  sellReMap.options.A.service_lines[0].cost_unit = null;
  sellReMap.options.A.service_lines[0].sell_unit = "350";
  const sellConflict = mergeMappedExcelQuoteDraft(costReApplied, sellReMap);
  assert.equal(sellConflict.options.A.service_lines[1].cost_unit, "212");
  assert.equal(sellConflict.options.A.service_lines[1].sell_unit, "300");
  assert.equal(sellConflict.options.A.service_lines[1].sell_confirmed, true);
  assert.equal(sellConflict.options.A.service_lines[1].tax_pct, "8");
  assert.equal(sellConflict.options.A.service_lines[1].public_note, "Điều kiện báo giá");
  console.log("  ✓ Conflicting SELL re-map retains the confirmed price and existing internal cost");

  for (const [field, value] of [["qty", "2"], ["unit", "shipment"], ["currency", "CNY"]]) {
    const changedBasisMap = structuredClone(portMapping);
    changedBasisMap.options.A.service_lines[0][field] = value;
    const basisChanged = mergeMappedExcelQuoteDraft(costReApplied, changedBasisMap);
    const needsReconfirmation = basisChanged.options.A.service_lines[1];
    assert.equal(needsReconfirmation[field], value);
    assert.equal(needsReconfirmation.sell_unit, "300");
    assert.equal(needsReconfirmation.sell_confirmed, false);
    assert.equal(needsReconfirmation.tax_pct, "8");
    assert.equal(needsReconfirmation.public_note, "Điều kiện báo giá");
  }
  console.log("  ✓ Qty, unit or currency changes each preserve the draft price but clear confirmation");

  await click("excel-workbook-map-apply");
  const repeatedPortMapping = applied[4];
  assert.deepEqual(repeatedPortMapping.options.A.service_lines.map((line) => line.id),
    portMapping.options.A.service_lines.map((line) => line.id));
  const updatedPortMapping = structuredClone(repeatedPortMapping);
  updatedPortMapping.options.A.service_lines[0].cost_unit = "212";
  const upserted = mergeMappedExcelQuoteDraft(multiSheetServices, updatedPortMapping);
  assert.equal(upserted.options.A.service_lines.length, 3);
  assert.equal(upserted.options.A.service_lines[0].cost_unit, "1250");
  assert.equal(upserted.options.A.service_lines[1].cost_unit, "212");
  assert.equal(upserted.options.A.service_lines[2].service_name, "D/O");
  console.log("  ✓ Reapplying an overlapping source row updates it without duplicating it or dropping other rows");

  await render(pageGoods);
  await setControl("excel-map-target", "GOODS");
  await setControl("excel-map-header-row", "1");
  await setControl("excel-map-first-row", "2");
  await setControl("excel-map-last-row", "2");
  await setControl("excel-map-column-name", "1");
  await setControl("excel-map-column-currency", "2");
  await click("excel-workbook-map-apply");
  const goodsMapping = applied[5];
  assert.equal(goodsMapping.goods[0].qty, null);
  assert.equal(goodsMapping.goods[0].unit_price, null);
  const mixedDraft = mergeMappedExcelQuoteDraft(upserted, goodsMapping);
  assert.equal(mixedDraft.goods_mode, "GOODS");
  assert.equal(mixedDraft.goods.length, 1);
  assert.equal(mixedDraft.goods[0].description, "Cabinet");
  assert.equal(mixedDraft.goods[0].qty, null);
  assert.equal(mixedDraft.goods[0].unit_price, null);
  assert.equal(mixedDraft.options.A.service_lines.length, 3);
  console.log("  ✓ Goods from another sheet coexist with services; quantity and sale price stay unknown");

  const manualGoodsDraft = structuredClone(mixedDraft);
  Object.assign(manualGoodsDraft.goods[0], { qty: "4", unit_price: "950", currency: "CNY" });
  const goodsReMap = structuredClone(goodsMapping);
  Object.assign(goodsReMap.goods[0], { qty: "6", unit_price: "1200", currency: "USD" });
  const goodsReApplied = mergeMappedExcelQuoteDraft(manualGoodsDraft, goodsReMap);
  assert.equal(goodsReApplied.goods.length, 1);
  assert.equal(goodsReApplied.goods[0].qty, "4");
  assert.equal(goodsReApplied.goods[0].unit_price, "950");
  assert.equal(goodsReApplied.goods[0].currency, "CNY");
  assert.equal(goodsReApplied.options.A.service_lines.length, 3);
  assert.deepEqual(goodsReApplied.options.B.service_lines, [alternateOptionLine]);
  console.log("  ✓ Goods re-map retains Sale quantity/unit price and their currency basis without duplication");

  await act(async () => root.unmount());
  console.log("DOM WORKBOOK MAPPING PASS — multi-sheet merge/upsert, GOODS/SERVICE_ONLY, opaque row ids and no automatic assumptions");
} finally {
  await vite.close();
  dom.window.close();
}
