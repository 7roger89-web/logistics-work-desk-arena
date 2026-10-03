/** Issue #172 focused DOM acceptance over the shipped React bundle. */
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

const c1 = {
  id: "C1",
  name: "Công ty An Phát",
  short: "Công ty An Phát",
  mst: "010-C1",
  taxCode: "010-C1",
  contactPerson: "Nguyễn Lan",
  phone: "0900000001",
  email: "lan@example.com",
  address: "KCN Quế Võ, Bắc Ninh",
  note: "Giao chứng từ cho chị Lan.\nKhông gửi bản scan khi chưa được xác nhận.",
};
const c2 = {
  id: "C2",
  name: "Công ty Bình Minh",
  short: "Công ty Bình Minh",
  mst: "010-C2",
  taxCode: "010-C2",
  contactPerson: "Trần Minh",
  phone: "0900000002",
  email: "minh@example.com",
  address: "Hải Phòng",
  note: "",
};
const moduleRollup = (overrides = {}) => ({
  instanceId: "WM-1",
  templateId: "QC-DEMO",
  templateVersion: 1,
  name: "QC kiểm hàng",
  description: "",
  status: "WAITING",
  summary: "1/2 bước",
  completedCount: 1,
  totalCount: 2,
  nextStep: "Result received",
  nextStepId: "result",
  deadline: "",
  blocker: "",
  gate: { stage: "delivery", label: "DELIVERY", type: "BLOCKING" },
  gateText: "",
  provenance: "MANUAL_ADDITION",
  addedBy: "",
  addedAt: "",
  reason: "",
  steps: [],
  ...overrides,
});
const shipment = (id, customerId, modules = [], overrides = {}) => {
  const base = structuredClone(raw.shipments[0]);
  const nextRoute = `/lo-hang/${encodeURIComponent(id)}?tab=nhap&stage=delivery`;
  return {
    ...base,
    id,
    customer: "Công ty An Phát",
    customerId,
    status: "Đang xử lý",
    statusTone: "amber",
    nextAction: "Chuẩn bị hồ sơ nhập khẩu",
    nextActionDetail: "Chờ kết quả kiểm tra.",
    nextLabel: "XỬ LÝ NGAY",
    nextRoute,
    journey: {
      nodes: [
        { id: "delivery", label: "Giao hàng", current: true },
        { id: "wm-WM-1-result", label: "Result received", current: false },
      ],
      edges: [],
      currentStageId: "delivery",
      owner: "",
      positionNote: "",
      seaFacts: {},
      primaryAction: {
        text: "Chuẩn bị hồ sơ nhập khẩu",
        detail: "Chờ kết quả kiểm tra.",
        priority: "CanXuLy",
        route: nextRoute,
      },
      modules,
    },
    ...overrides,
  };
};
const attentionItem = (id, shipmentId, overrides = {}) => ({
  id,
  shipmentId,
  sourceType: "WORK_MODULE",
  sourceRef: `MODULE:${shipmentId}:${id}`,
  band: "ACTION",
  reason: `Lý do ${id}`,
  action: `Việc ${id}`,
  context: "QC kiểm hàng",
  route: `/lo-hang/${encodeURIComponent(shipmentId)}?tab=nhap&stage=wm-WM-1-result&work=info`,
  owner: "",
  deadline: "",
  blockedGate: "",
  primary: false,
  moduleTemplateId: "QC-DEMO",
  moduleName: "QC kiểm hàng",
  provenance: "work_module:QC-DEMO@1",
  unknown: false,
  ...overrides,
});

const blockRoute = "/lo-hang/S1?tab=nhap&stage=wm-WM-1-result&work=info";
const model = structuredClone(raw);
model.customers = [c1, c2];
model.shipments = [
  shipment("S1", "C1", [moduleRollup({
    instanceId: "WM-1",
    status: "BLOCKING",
    gateText: "Chặn DELIVERY — còn thiếu Result received",
  })]),
  shipment("S2", "C1", [
    moduleRollup({ instanceId: "WM-2", status: "WAITING" }),
    moduleRollup({
      instanceId: "WM-UNKNOWN",
      templateId: "OLD-VERSION",
      name: "OLD-VERSION",
      status: "UNKNOWN",
      summary: "UNKNOWN",
      completedCount: 0,
      totalCount: 0,
      gate: {},
      gateText: "",
      unresolved: true,
    }),
  ]),
  // Same display name, deliberately unlinked. It must not leak into C1.
  shipment("UNLINKED", undefined, [moduleRollup({ instanceId: "WM-DECOY", status: "BLOCKING" })]),
  shipment("S3", "C2", []),
];
model.shipments[0].customer = "Công ty An Phát";
model.shipments[1].customer = "Công ty An Phát";
model.shipments[2].customer = "Công ty An Phát";
model.attention = [
  attentionItem("ATT-BLOCK", "S1", {
    band: "BLOCKING",
    reason: "Chặn DELIVERY — còn thiếu Result received",
    action: "Result received",
    route: blockRoute,
    blockedGate: "DELIVERY",
  }),
  attentionItem("ATT-UNKNOWN", "S2", {
    band: "ACTION",
    reason: "Không đọc được phiên bản quy trình đã gắn.",
    route: "/lo-hang/S2?tab=nhap&stage=UNKNOWN",
    unknown: true,
  }),
  attentionItem("ATT-UNLINKED", "UNLINKED", {
    band: "BLOCKING",
    route: "/lo-hang/UNLINKED?tab=nhap",
  }),
];

function installDom() {
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
  return dom;
}
const tick = (ms = 100) => new Promise((resolve) => setTimeout(resolve, ms));
const text = (el) => (el?.textContent || "").replace(/\s+/g, " ").trim();
const click = async (el) => {
  assert.ok(el, "expected link/button exists");
  el.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
  await tick();
};
const findCustomerLink = (id) => [...document.querySelectorAll('[data-testid="customer-open-playbook"]')]
  .find((link) => link.getAttribute("href") === `/khach-hang/${id}`);

const mount = (await import(pathToFileURL(path.join(root, "component/dist/logi-shell.js")))).default;
const dom1 = installDom();
const host1 = document.getElementById("host");
const triggers = [];
const unmount1 = mount({
  name: "logi_shell",
  data: model,
  parentElement: host1,
  setTriggerValue: (event, value) => triggers.push({ event, value }),
});
await tick();

const customersNav = [...document.querySelectorAll("a")].find((link) => text(link) === "Khách Hàng");
await click(customersNav);
await click(findCustomerLink("C1"));

const page = document.querySelector('[data-testid="customer-playbook"]');
assert.ok(page, "C1 detail route renders");
assert.equal(page.getAttribute("data-customer-id"), "C1");
assert.match(text(document.querySelector('[data-testid="customer-playbook-identity"]')), /Công ty An Phát/);
assert.equal(
  document.querySelector('[data-testid="customer-operating-note"]').textContent.includes(c1.note),
  true,
  "the exact existing multiline customer note is displayed",
);
assert.equal(document.querySelector('[data-testid="customer-operating-note"]').getAttribute("data-note-empty"), "false");

const linkedRows = [...document.querySelectorAll('[data-testid="customer-playbook-shipment"]')];
assert.deepEqual(linkedRows.map((row) => row.getAttribute("data-shipment-id")), ["S1", "S2"]);
assert.ok(!text(page).includes("UNLINKED"), "same-name unlinked shipment is excluded");
assert.equal(
  document.querySelector('[data-testid="customer-playbook-shipment-link"]').getAttribute("href"),
  "/lo-hang/S1",
  "shipment identity links to the existing direct shipment route",
);
assert.equal(
  document.querySelector('[data-testid="customer-playbook-primary-action"]').getAttribute("href"),
  "/lo-hang/S1?tab=nhap&stage=delivery",
  "existing primary action route is preserved",
);
assert.match(text(linkedRows[0]), /Vị trí Journey/);

const attentionBlock = document.querySelector('[data-testid="attention-item-ATT-BLOCK"]');
assert.ok(attentionBlock, "linked BLOCKING Attention appears in the customer hero");
assert.equal(attentionBlock.getAttribute("data-attention-band"), "BLOCKING");
assert.match(text(attentionBlock), /Chặn DELIVERY — còn thiếu Result received/);
assert.equal(attentionBlock.querySelector("a").getAttribute("href"), blockRoute);
assert.ok(document.querySelector('[data-testid="attention-item-ATT-UNKNOWN"]'), "linked UNKNOWN Attention remains visible");
assert.ok(!document.querySelector('[data-testid="attention-item-ATT-UNLINKED"]'), "unlinked Attention is excluded");

const qc = [...document.querySelectorAll('[data-testid="customer-playbook-module-group"]')]
  .find((row) => row.getAttribute("data-module-template") === "QC-DEMO");
assert.ok(qc);
assert.match(text(qc), /2 lần gắn · 2 lô liên kết/);
assert.match(text(document.querySelector('[data-testid="customer-playbook-blocked-gate"]')), /DELIVERY/);
assert.match(text(document.querySelector('[data-testid="customer-playbook-blocked-gate"]')), /1 quy trình · 1 lô liên kết/);
const unknownModule = [...document.querySelectorAll('[data-testid="customer-playbook-module-group"]')]
  .find((row) => row.getAttribute("data-module-template") === "OLD-VERSION");
assert.equal(unknownModule?.getAttribute("data-module-unknown-count"), "1");
assert.match(text(unknownModule), /UNKNOWN: 1 mục chưa xác định/);
assert.doesNotMatch(text(page), /risk score|recommendation|healthy|safe|khỏe|an toàn/i);
assert.equal(triggers.length, 0, "the detail route remains read-only");

// Editing stays on the existing customer master route; no cloned writer is exposed.
await click(document.querySelector('[data-testid="customer-playbook-master-link"]'));
assert.ok(document.querySelector('input[aria-label="Tìm khách hàng theo mã, tên, MST, SĐT, email"]'));
assert.equal(document.querySelectorAll('[data-testid="customer-playbook"]').length, 0);
unmount1();

// A customer with no linked Attention gets a neutral empty state, not a health claim.
const dom2 = installDom();
const modelWithoutAttention = structuredClone(model);
modelWithoutAttention.customers = [c2];
modelWithoutAttention.shipments = [model.shipments[3]];
modelWithoutAttention.attention = [];
const unmount2 = mount({
  name: "logi_shell",
  data: modelWithoutAttention,
  parentElement: document.getElementById("host"),
  setTriggerValue: (event, value) => triggers.push({ event, value }),
});
await tick();
const customersNav2 = [...document.querySelectorAll("a")].find((link) => text(link) === "Khách Hàng");
await click(customersNav2);
await click(findCustomerLink("C2"));
const noAttention = document.querySelector('[data-testid="customer-playbook-attention"]');
assert.ok(noAttention);
assert.match(text(noAttention), /Chưa có mục Attention liên kết được ghi nhận/);
assert.doesNotMatch(text(noAttention), /healthy|safe|khỏe|an toàn/i);
assert.equal(document.querySelector('[data-testid="customer-operating-note"]').getAttribute("data-note-empty"), "true");
assert.match(text(document.querySelector('[data-testid="customer-operating-note"]')), /Chưa ghi nhận ghi chú vận hành/);
assert.equal(triggers.length, 0);
unmount2();
dom1.window.close();
dom2.window.close();
console.log("PASS #172 DOM: exact note/linkage, shared Attention route/band/reason, current Journey/action links, module/gate counts, UNKNOWN, neutral no-Attention, read-only master return");
