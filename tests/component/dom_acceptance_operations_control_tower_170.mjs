/**
 * Issue #170 DOM acceptance: separate read-only manager surface over shared Attention.
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
const row = raw.shipments.find((item) => item.id === shipmentId);
assert.ok(row, "fixture shipment exists");

const managerItems = [
  {
    id: "MGR-BLOCK",
    shipmentId,
    sourceType: "WORK_MODULE",
    sourceRef: `MODULE:${shipmentId}:M1`,
    band: "BLOCKING",
    reason: "Chặn DELIVERY — còn thiếu Result received",
    action: "Result received",
    context: "QC demo",
    route: `/lo-hang/${encodeURIComponent(shipmentId)}?tab=nhap&stage=wm-M1-result&work=info`,
    owner: "",
    deadline: "",
    deadlineDate: "",
    blockedGate: "DELIVERY",
    primary: false,
    moduleTemplateId: "QC",
    moduleName: "QC",
    provenance: "work_module:QC@1",
    unknown: false,
    customer: row.customer,
    shipmentStatus: row.status,
  },
  {
    id: "MGR-DUE",
    shipmentId,
    sourceType: "TASK",
    sourceRef: "TASK:T-170",
    band: "DUE_SOON",
    reason: "Việc được giao",
    action: "Nộp chứng từ nhập khẩu",
    context: row.customer,
    route: `/lo-hang/${encodeURIComponent(shipmentId)}?tab=lay-hang`,
    owner: "Support A",
    deadline: "03/10/2026",
    deadlineDate: "2026-10-03",
    blockedGate: "",
    primary: false,
    provenance: "core.database.load_tasks",
    unknown: false,
    customer: row.customer,
    shipmentStatus: row.status,
  },
  {
    id: "MGR-UNKNOWN",
    shipmentId,
    sourceType: "WORK_MODULE",
    sourceRef: `MODULE:${shipmentId}:UNKNOWN`,
    band: "ACTION",
    reason: "Không đọc được phiên bản quy trình đã gắn.",
    action: "Kiểm tra quy trình đã gắn",
    context: "UNKNOWN",
    route: `/lo-hang/${encodeURIComponent(shipmentId)}?tab=nhap`,
    owner: "",
    deadline: "",
    deadlineDate: "",
    blockedGate: "",
    primary: false,
    provenance: "work_module:UNKNOWN@1",
    unknown: true,
    customer: row.customer,
    shipmentStatus: row.status,
  },
];

const model = structuredClone(raw);
model.operationsControl = {
  classification: "READ_ONLY_ATTENTION_AGGREGATE_V1",
  readOnly: true,
  scope: {
    shipmentCount: model.shipments.length,
    attentionShipmentCount: 1,
    noSignalShipmentCount: Math.max(model.shipments.length - 1, 0),
    unknownShipmentCount: 1,
    managerItemCount: 3,
  },
  interventionQueue: managerItems,
  horizon: {
    asOf: "2026-10-02",
    precision: "DATE_ONLY",
    labels: { OVERDUE: "Quá hạn", TODAY: "Hôm nay", NEXT_3_DAYS: "1–3 ngày tới" },
    buckets: [
      { id: "OVERDUE", label: "Quá hạn", items: [], count: 0 },
      { id: "TODAY", label: "Hôm nay", items: [], count: 0 },
      { id: "NEXT_3_DAYS", label: "1–3 ngày tới", items: [managerItems[1]], count: 1 },
    ],
  },
  workload: [
    {
      ownerKey: "UNASSIGNED",
      owner: "Chưa phân công / Chưa xác định",
      blocking: 1,
      overdue: 0,
      dueSoon: 0,
      action: 1,
      unknown: 1,
      itemIds: ["MGR-BLOCK", "MGR-UNKNOWN"],
    },
    {
      ownerKey: "Support A",
      owner: "Support A",
      blocking: 0,
      overdue: 0,
      dueSoon: 1,
      action: 0,
      unknown: 0,
      itemIds: ["MGR-DUE"],
    },
  ],
  concentration: {
    customers: [{
      key: row.customer, label: row.customer, count: 3, blocking: 1, overdue: 0,
      dueSoon: 1, unknown: 1, itemIds: managerItems.map((item) => item.id),
    }],
    gates: [{
      key: "DELIVERY", label: "DELIVERY", count: 1, blocking: 1, overdue: 0,
      dueSoon: 0, unknown: 0, itemIds: ["MGR-BLOCK"],
    }],
    modules: [{
      key: "QC", label: "QC", count: 1, blocking: 1, overdue: 0,
      dueSoon: 0, unknown: 0, itemIds: ["MGR-BLOCK"],
    }],
  },
  unavailable: [
    "Chưa có nguồn canonical cho waiting-on party / chase age.",
    "Deadline hiện tại là theo ngày, không suy diễn thành đồng hồ <24h.",
  ],
};

const dom = new JSDOM("<!doctype html><body><div id=\"host\"></div>", {
  url: "http://localhost:9510/",
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
mount({
  name: "logi_shell",
  data: model,
  parentElement: host,
  setTriggerValue: (event, value) => triggers.push({ event, value }),
});
const tick = (ms = 100) => new Promise((resolve) => setTimeout(resolve, ms));
const text = (el) => (el?.textContent || "").replace(/\s+/g, " ").trim();
await tick();

const nav = [...document.querySelectorAll("a")].find((a) => text(a) === "Điều hành");
assert.ok(nav, "Control Tower navigation exists");
nav.dispatchEvent(new MouseEvent("click", { bubbles: true, cancelable: true }));
await tick();

const tower = document.querySelector('[data-testid="operations-control-tower"]');
const hero = document.querySelector('[data-testid="control-intervention-queue"]');
const horizon = document.querySelector('[data-testid="control-horizon"]');
assert.ok(tower && hero && horizon, "Tower and bounded blocks render");
assert.ok(
  hero.compareDocumentPosition(horizon) & Node.DOCUMENT_POSITION_FOLLOWING,
  "Manager intervention queue is above the horizon",
);
assert.match(text(tower), /Chưa có tín hiệu/);
assert.doesNotMatch(text(tower), /healthy|an toàn 100%/i);

const rows = [...document.querySelectorAll('[data-testid="control-intervention-row"]')];
assert.equal(rows.length, 3, "manager-grade queue renders exact bounded set");
assert.match(text(rows[0]), /Chặn/);
assert.match(text(rows[0]), /DELIVERY/);
assert.ok(rows[0].getAttribute("href")?.includes("stage=wm-M1-result"), "queue preserves exact drill-down route");

const workloadRows = [...document.querySelectorAll('[data-testid="control-workload-row"]')];
assert.equal(workloadRows.length, 2);
assert.doesNotMatch(workloadRows.map(text).join(" "), /quá tải|overloaded|leaderboard/i);

const blockFilter = [...hero.querySelectorAll("button")].find((b) => text(b) === "Chặn");
assert.ok(blockFilter, "blocking filter exists");
blockFilter.dispatchEvent(new MouseEvent("click", { bubbles: true, cancelable: true }));
await tick();
assert.equal(document.querySelectorAll('[data-testid="control-intervention-row"]').length, 1, "filter reduces queue to actual blocking item");

assert.equal(triggers.length, 0, "Tower interactions remain read-only");
console.log("PASS #170: separate manager queue, neutral coverage, exact drill-down, factual workload, read-only filters");
