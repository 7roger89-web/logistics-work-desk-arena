/**
 * Issue #166 DOM acceptance: the SAME Attention projection drives Home and
 * Shipment Detail; Attention renders before Journey; neutral empty language.
 *
 * Run after component build:
 *   node tests/component/dom_acceptance_support_attention_166.mjs
 */
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import { fileURLToPath, pathToFileURL } from "node:url";
import path from "node:path";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const require = createRequire(path.join(root, "component/package.json"));
const { JSDOM } = require("jsdom");
const raw = JSON.parse(readFileSync(
  path.join(root, "tests/component/fixtures/view_model_document_review.json"),
  "utf8",
));
const shipmentId = raw.fixture.shipmentId;
const shipment = raw.shipments.find((row) => row.id === shipmentId);
assert.ok(shipment, "fixture shipment exists");

const model = structuredClone(raw);
const row = model.shipments.find((item) => item.id === shipmentId);
row.journey = {
  nodes: [{
    id: "transit", label: "TRANSIT", family: "TRANSIT", targetTab: "van-tai",
    completed: false, state: "CURRENT", factState: "KNOWN", evidence: "Transit fact",
    deadline: "", owned: false, current: true, blockers: [], dependencies: [],
    documentCategories: [], documentIds: [],
  }],
  edges: [],
  currentStageId: "transit",
  owner: row.sale || "",
  positionNote: "",
  seaFacts: {},
  primaryAction: {
    text: row.nextAction,
    detail: row.nextActionDetail || "",
    priority: row.priority || "CanXuLy",
    route: row.nextRoute,
  },
};
const moduleRoute = `/lo-hang/${encodeURIComponent(shipmentId)}?tab=nhap&stage=wm-M1-result&work=info`;
model.attention = [
  {
    id: "ATT-BLOCK",
    shipmentId,
    sourceType: "WORK_MODULE",
    sourceRef: `MODULE:${shipmentId}:M1`,
    band: "BLOCKING",
    reason: "Chặn DELIVERY — còn thiếu Result received",
    action: "Result received",
    context: "Demo gated",
    route: moduleRoute,
    owner: "",
    deadline: "",
    blockedGate: "DELIVERY",
    primary: false,
    provenance: "work_module:DEMO@1",
    unknown: false,
  },
  {
    id: "ATT-TASK",
    shipmentId,
    sourceType: "TASK",
    sourceRef: "TASK:T-166",
    band: "DUE_SOON",
    reason: "Việc được giao",
    action: "Nộp chứng từ nhập khẩu",
    context: row.customer,
    route: `/lo-hang/${encodeURIComponent(shipmentId)}?tab=lay-hang`,
    owner: "Support A",
    deadline: "04/10/2026",
    blockedGate: "",
    primary: false,
    provenance: "core.database.load_tasks",
    unknown: false,
  },
];
model.home = {
  ...(model.home || {}),
  urgentCount: 2,
  focus: {
    id: shipmentId,
    customer: row.customer,
    status: row.status,
    nextAction: model.attention[0].action,
    nextActionDetail: model.attention[0].reason,
    priority: "Khan",
    to: model.attention[0].route,
  },
};

const dom = new JSDOM("<!doctype html><body><div id=\"host\"></div>", {
  url: "http://localhost:9501/",
  pretendToBeVisual: true,
});
globalThis.window = dom.window;
globalThis.document = dom.window.document;
Object.defineProperty(globalThis, "navigator", { value: dom.window.navigator, configurable: true });
for (const key of [
  "HTMLElement", "HTMLInputElement", "HTMLSelectElement", "HTMLTextAreaElement",
  "HTMLAnchorElement", "HTMLButtonElement", "Event", "CustomEvent", "MouseEvent",
  "KeyboardEvent", "Node", "Element", "MutationObserver", "getComputedStyle",
]) globalThis[key] = dom.window[key];
dom.window.HTMLElement.prototype.scrollIntoView = () => {};

const mount = (await import(pathToFileURL(path.join(root, "component/dist/logi-shell.js")))).default;
const host = document.getElementById("host");
const triggers = [];
const deliver = (data) => mount({
  name: "logi_shell",
  data,
  parentElement: host,
  setTriggerValue: (event, value) => triggers.push({ event, value }),
});
const tick = (ms = 80) => new Promise((resolve) => setTimeout(resolve, ms));
const text = (el) => (el?.textContent || "").replace(/\s+/g, " ").trim();
const byId = (id) => document.querySelector(`[data-testid="${id}"]`);
const clickable = (label) => [...document.querySelectorAll("a,button")]
  .find((el) => text(el) === label || text(el).startsWith(label));

deliver(model);
await tick();

assert.match(document.querySelector("main").textContent, /Ưu tiên bây giờ/);
assert.match(document.querySelector("main").textContent, /Result received/);
assert.ok(byId("attention-item-ATT-TASK"), "Home bounded list uses the same Attention projection");

const hero = clickable("XỬ LÝ NGAY");
assert.ok(hero, "Home primary Attention drill-down exists");
hero.dispatchEvent(new MouseEvent("click", { bubbles: true, cancelable: true }));
await tick();

const attention = byId("attention-now");
const journey = byId("shipment-journey");
assert.ok(attention, "Shipment Attention is visible");
assert.ok(journey, "Journey stays available as context");
assert.ok(
  attention.compareDocumentPosition(journey) & Node.DOCUMENT_POSITION_FOLLOWING,
  "Attention renders before Journey",
);
assert.match(attention.textContent, /Chặn/);
assert.match(attention.textContent, /DELIVERY/);
assert.match(attention.textContent, /Result received/);
assert.match(attention.textContent, /Nộp chứng từ nhập khẩu/);
const moduleLink = [...attention.querySelectorAll("a")].find((a) => text(a).includes("Mở quy trình"));
assert.ok(moduleLink, "module Attention row exposes the existing-context link");
assert.ok(moduleLink.href.includes("stage=wm-M1-result"));
assert.equal(triggers.length, 0, "Attention navigation/rendering is read-only");

const empty = structuredClone(model);
empty.attention = [];
empty.home = { ...empty.home, focus: null, urgentCount: 0 };
deliver(empty);
await tick();
assert.match(byId("attention-now").textContent, /Chưa có việc cần xử lý theo dữ liệu hiện có/);
assert.doesNotMatch(document.querySelector("main").textContent, /toàn bộ lô hàng đang ổn định/i);
assert.ok(byId("shipment-journey"), "Journey remains visible when Attention is empty");

console.log("PASS #166: shared Home/Shipment Attention, exact drill-down, Attention before Journey, neutral empty state");
