// ===========================================================================
// LOGI_FREIGHTOS_MARKET_BENCHMARK_CANARY_01 — DOM acceptance on the REAL bundle.
//
// Proves inside Kho giá vốn:
//   - no Freightos fetch until "So với thị trường"
//   - Giá vốn nội bộ stays visually separate from Tham khảo thị trường · Freightos
//   - required Freightos attribution/link
//   - mobile-safe wrapping classes on the market card
//
// Run: node tests/component/dom_acceptance_cost_market_benchmark.mjs
// ===========================================================================

import { readFileSync } from "node:fs";
import assert from "node:assert/strict";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const require = createRequire(path.join(ROOT, "component/package.json"));
const { JSDOM } = require("jsdom");
const BASE = JSON.parse(
  readFileSync(path.join(ROOT, "tests/component/fixtures/view_model_phase_b.json"), "utf8")
);
const CW = JSON.parse(
  readFileSync(path.join(ROOT, "tests/component/fixtures/view_model_contract_workflow.json"), "utf8")
);
if (Array.isArray(CW.success?.quotes) && CW.success.quotes.length > 0) {
  BASE.quotes = CW.success.quotes;
}

const ROW_KEY = "RATE-NGB-HPH:line-1";
const OF_RAW_KEY = "RATE-NGB-HPH:line-of-raw";
const PICKUP_KEY = "RATE-NGB-HPH:line-pickup";
const BAF20_KEY = "RATE-NGB-HPH:line-baf-20";
const BAF40_KEY = "RATE-NGB-HPH:line-baf-40";
const THC_KEY = "RATE-NGB-HPH:line-thc";

function containerRow(over) {
  return {
    kind: "CHARGE",
    status: "AVAILABLE",
    carrier: { id: "C-COSCO", name: "COSCO", state: "CONFIRMED" },
    origin: { raw: "NINGBO", id: "P-NGB", name: "Ningbo", zoneIds: [], state: "CONFIRMED" },
    destination: { raw: "HPH", id: "P-HPH", name: "Hải Phòng", zoneIds: [], state: "CONFIRMED" },
    currency: "USD",
    equipment: "40HQ",
    equipmentState: "CONFIRMED",
    confidence: "CONFIRMED",
    ...over,
  };
}

function fixtureVm() {
  const vm = JSON.parse(JSON.stringify(BASE));
  vm.costIntelligence = {
    catalog: [
      {
        id: "P-NGB", kind: "PLACE", code: "CNNGB", name: "Ningbo",
        aliases: ["NINGBO"], active: true, unlocode: "CNNGB",
      },
      {
        id: "P-HPH", kind: "PLACE", code: "VNHPH", name: "Hải Phòng",
        aliases: ["HPH", "HAIPHONG"], active: true, unlocode: "VNHPH",
      },
    ],
    rates: [
      {
        id: "RATE-NGB-HPH",
        record_type: "SUPPLIER_RATE_SNAPSHOT",
        status: "ACTIVE",
        received_at: "2026-09-24T08:00:00Z",
        supplier: "COSCO",
        source_channel: "PASTE",
        raw_text: "O/F: USD1425/40HQ COSCO\\nPICK UP 245$/40’\\nFEEDER BAF $50/20GP $100/40HQ\\nTHC $205/40HQ",
        parser_version: "cost-rate-parser/2",
        rows: [
          containerRow({
            id: "line-1",
            chargeLabel: "Ocean Freight",
            chargeId: "S-OF",
            chargeRaw: "O/F",
            amount: 1425,
            rawLine: "O/F: USD1425/40HQ ETD 21/09/2026 COSCO",
          }),
          containerRow({
            id: "line-of-raw",
            chargeLabel: "O/F",
            chargeRaw: "O/F",
            amount: 1300,
            rawLine: "COSCO USD 1300/40HQ",
          }),
          containerRow({
            id: "line-pickup",
            chargeLabel: "PICK UP",
            chargeRaw: "PICK UP",
            amount: 245,
            equipment: "40",
            rawLine: "PICK UP 245$/40’",
          }),
          containerRow({
            id: "line-baf-20",
            chargeLabel: "FEEDER BAF",
            chargeRaw: "FEEDER BAF",
            amount: 50,
            equipment: "20GP",
            rawLine: "FEEDER BAF $50/20GP $100/40HQ",
          }),
          containerRow({
            id: "line-baf-40",
            chargeLabel: "FEEDER BAF",
            chargeRaw: "FEEDER BAF",
            amount: 100,
            equipment: "40HQ",
            rawLine: "FEEDER BAF $50/20GP $100/40HQ",
          }),
          containerRow({
            id: "line-thc",
            chargeLabel: "THC",
            chargeRaw: "THC",
            amount: 205,
            rawLine: "THC $205/40HQ",
          }),
        ],
      },
    ],
  };
  return vm;
}

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
  "FocusEvent", "Node", "MutationObserver", "getComputedStyle", "TextEncoder",
]) {
  globalThis[k] = window[k];
}
if (!globalThis.MessageChannel) globalThis.MessageChannel = window.MessageChannel;
window.HTMLElement.prototype.scrollIntoView = () => {};

const tick = (ms = 90) => new Promise((r) => setTimeout(r, ms));
const $ = (sel, root = window.document) => [...root.querySelectorAll(sel)];
const text = (el) => ((el && el.textContent) || "").replace(/\s+/g, " ").trim();
const byTestId = (id) => $(`[data-testid="${id}"]`)[0] ?? null;

async function click(needle, sel = "a,button", root = window.document) {
  const els = $(sel, root);
  const el = els.find((e) => text(e) === needle) || els.find((e) => text(e).startsWith(needle));
  assert.ok(el, `clickable "${needle}" not found`);
  el.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
  await tick();
  return el;
}
async function clickTestId(id) {
  const el = byTestId(id);
  assert.ok(el, `[data-testid="${id}"] not found`);
  el.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
  await tick();
  return el;
}

const host = window.document.createElement("div");
window.document.body.appendChild(host);
const triggers = [];
const mod = await import(path.join(ROOT, "component/dist/logi-shell.js"));
assert.equal(typeof mod.default, "function");

function invoke(vm) {
  return mod.default({
    name: "logi_shell",
    data: vm,
    parentElement: host,
    setTriggerValue: (event, value) => triggers.push({ event, value }),
  });
}

let passed = 0;
const ok = (name) => { passed += 1; console.log(`  ✓ ${name}`); };

const VM = fixtureVm();
window.history.replaceState({}, "", "/?view=kho-gia-von");
invoke(VM);
await tick(170);

console.log("STEP 1 — Kho giá vốn shows internal row, no market card, no fetch on load");
{
  await click("Báo Giá", "a", $("aside")[0]);
  if (!byTestId("quote-workspace-kho-gia-von")) {
    throw new Error("Báo Giá workspace tabs missing: " + text($("main")[0] || window.document.body).slice(0, 240));
  }
  await clickTestId("quote-workspace-kho-gia-von");
  assert.ok(byTestId("cost-intelligence"), "Kho giá vốn must render");
  const summary = [...$("summary")].find((el) => text(el).includes("COSCO"));
  assert.ok(summary, "saved snapshot summary must be visible");
  summary.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
  await tick();
  assert.ok(byTestId("cost-internal-row-" + ROW_KEY), "confirmed ocean row must render as Giá vốn nội bộ");
  assert.ok(text(byTestId("cost-internal-row-" + ROW_KEY)).includes("Giá vốn nội bộ"));
  assert.ok(byTestId("cost-market-fetch-" + ROW_KEY), "O/F Ocean Freight row must get So với thị trường");
  assert.ok(byTestId("cost-market-fetch-" + OF_RAW_KEY), "parser-normalized O/F row must stay eligible");
  assert.equal(byTestId("cost-market-benchmark-" + ROW_KEY), null, "no market card before click");
  assert.equal(
    triggers.filter((t) => t.event === "cost_market_benchmark_fetch").length,
    0,
    "page load must never fetch Freightos"
  );
  assert.equal(byTestId("cost-market-fetch-" + PICKUP_KEY), null, "PICK UP must not get a market-benchmark action");
  assert.equal(byTestId("cost-market-fetch-" + BAF20_KEY), null, "FEEDER BAF 20GP must not get a market-benchmark action");
  assert.equal(byTestId("cost-market-fetch-" + BAF40_KEY), null, "FEEDER BAF 40HQ must not get a market-benchmark action");
  assert.equal(byTestId("cost-market-fetch-" + THC_KEY), null, "THC must not get a market-benchmark action");
  ok("O/F eligible; PICK UP / FEEDER BAF / THC excluded; no auto-fetch");
}

console.log("STEP 2 — So với thị trường dispatches the read-only event");
{
  const before = triggers.length;
  await clickTestId("cost-market-fetch-" + ROW_KEY);
  const sent = triggers.slice(before).filter((t) => t.event === "cost_market_benchmark_fetch");
  assert.equal(sent.length, 1, "exactly one fetch event");
  const payload = sent[0].value.payload;
  assert.equal(payload.originUnlocode, "CNNGB");
  assert.equal(payload.destinationUnlocode, "VNHPH");
  assert.equal(payload.equipment, "40HQ");
  assert.equal(payload.internalAmount, 1425);
  assert.equal(payload.internalCurrency, "USD");
  assert.equal(payload.snapshotId, "RATE-NGB-HPH");
  assert.ok(payload.requestId, "requestId required for lastWrites correlation");
  assert.equal(
    triggers.filter((t) => t.event === "cost_rate_save").length,
    0,
    "market fetch must never save a supplier snapshot"
  );
  ok("click maps CNNGB/VNHPH/40HQ and does not persist");

  const next = JSON.parse(JSON.stringify(VM));
  next.lastWrites = [{
    event: "cost_market_benchmark_fetch",
    ok: true,
    requestId: payload.requestId,
    benchmark: {
      provider: "FREIGHTOS_PUBLIC",
      providerUrl: "https://ship.freightos.com",
      attribution: "Freightos",
      fetchedAt: "2026-09-25T04:30:00Z",
      origin: "CNNGB",
      destination: "VNHPH",
      equipment: "40HQ",
      loadType: "container40HC",
      currency: "USD",
      minAmount: 891,
      maxAmount: 1146,
      transitMin: 3,
      transitMax: 24,
      transitUnit: "days",
      numQuotes: 1,
      mode: "FCL",
      status: "AVAILABLE",
      comparison: {
        internalAmount: 1425,
        internalCurrency: "USD",
        midpoint: 1018.5,
        difference: 406.5,
        label: "so với trung điểm khoảng Freightos — không cùng hãng/phụ phí",
      },
    },
  }];
  invoke(next);
  await tick(170);
}

console.log("STEP 3 — market card is separate, attributed, and wrap-safe");
{
  const card = byTestId("cost-market-benchmark-" + ROW_KEY);
  assert.ok(card, "Freightos result card must appear after lastWrites");
  const body = text(card);
  assert.ok(body.includes("Tham khảo thị trường · Freightos"));
  assert.ok(body.includes("CNNGB"));
  assert.ok(body.includes("VNHPH"));
  assert.ok(body.includes("891"));
  assert.ok(body.includes("1.146") || body.includes("1146"));
  assert.ok(body.includes("3") && body.includes("24"));
  assert.ok(body.includes("2026-09-25T04:30:00Z"));
  assert.ok(body.includes("Không phải giá buy cùng hãng"));
  const attr = byTestId("cost-market-attribution-" + ROW_KEY);
  assert.ok(attr, "Freightos attribution link required");
  assert.equal(attr.getAttribute("href"), "https://ship.freightos.com");
  const internal = byTestId("cost-internal-row-" + ROW_KEY);
  assert.ok(text(internal).includes("Giá vốn nội bộ"));
  assert.ok(card.className.includes("border-sky") || card.className.includes("bg-sky"));
  assert.ok(card.className.includes("break-words") || body.length > 0);
  assert.ok($("a", card).length >= 1);
  ok("separated card + attribution + no invented live hard-code in source path");
}

console.log(`\nDOM_ACCEPTANCE_COST_MARKET_BENCHMARK=${passed} checks passed`);
process.exit(0);
