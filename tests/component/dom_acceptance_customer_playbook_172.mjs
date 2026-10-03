/**
 * Issue #172 DOM acceptance: Customer Playbook V1 read-only operating context
 * over existing customer master, exact customerId shipments, shared Attention,
 * Journey, and Work Module rollups.
 */
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import { fileURLToPath, pathToFileURL } from "node:url";
import path from "node:path";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const require = createRequire(path.join(root, "component/package.json"));
const { JSDOM } = require("jsdom");

const raw = JSON.parse(
  readFileSync(
    path.join(root, "tests/component/fixtures/view_model_document_review.json"),
    "utf8"
  )
);

const baseShipment = raw.shipments[0];
assert.ok(baseShipment, "base fixture shipment exists");

const model = structuredClone(raw);

model.customers = [
  {
    id: "C1",
    name: "Công ty TNHH An Phát",
    short: "An Phát",
    mst: "0101234567",
    taxCode: "0101234567",
    contactPerson: "Nguyễn Thị Minh",
    phone: "0909111222",
    email: "ops@anphat.vn",
    address: "KCN Đình Vũ, Hải Phòng",
    note: "Ghi chú vận hành chuẩn: kiểm tra seal và gửi ảnh container trước khi kéo về kho.",
  },
  {
    id: "C2",
    name: "Công ty Cổ phần Minh Tâm",
    short: "Minh Tâm",
    mst: "0309876543",
    taxCode: "0309876543",
    contactPerson: "Trần Văn Hòa",
    phone: "0912333444",
    email: "hoa@minhtam.vn",
    address: "KCN Sóng Thần, Bình Dương",
    note: "",
  },
];

const s1 = {
  ...structuredClone(baseShipment),
  id: "S-C1-1",
  customerId: "C1",
  customer: "Công ty TNHH An Phát",
  customerMST: "0101234567",
  status: "Đang làm thủ tục nhập",
  statusTone: "amber",
  route: "Shanghai → Hải Phòng",
  nextAction: "Nhận kết quả kiểm định",
  nextActionDetail: "Chặn giao hàng cho đến khi có biên bản QC",
  nextRoute: "/lo-hang/S-C1-1?tab=nhap",
  journey: {
    currentStageId: "customs-import",
    owner: "Sale A",
    positionNote: "",
    seaFacts: {},
    primaryAction: {
      text: "Nhận kết quả kiểm định",
      detail: "Chặn giao hàng cho đến khi có biên bản QC",
      priority: "Khan",
      route: "/lo-hang/S-C1-1?tab=nhap",
    },
    nodes: [
      {
        id: "customs-import",
        label: "Thông quan nhập khẩu",
        family: "IMPORT",
        targetTab: "nhap",
        completed: false,
        state: "PROBLEM",
        factState: "KNOWN",
        evidence: "TK 10555",
        deadline: "",
        owned: true,
        current: true,
        blockers: ["Chặn DELIVERY — còn thiếu Nhận kết quả kiểm định"],
        dependencies: [],
        documentCategories: [],
        documentIds: [],
      },
      {
        id: "wm-M1-result-received",
        label: "Nhận kết quả kiểm định",
        family: "WORK_MODULE",
        targetTab: "nhap",
        completed: false,
        state: "PROBLEM",
        factState: "UNKNOWN",
        evidence: "",
        deadline: "",
        owned: true,
        current: false,
        blockers: [],
        dependencies: [],
        documentCategories: [],
        documentIds: [],
        moduleId: "M1",
        moduleTemplateId: "QC_CHECK",
        moduleTemplateVersion: 1,
        moduleName: "Kiểm định chất lượng",
        moduleNodeId: "result-received",
        moduleStatus: "BLOCKING",
        moduleGateText: "Chặn DELIVERY — còn thiếu Nhận kết quả kiểm định",
        moduleProvenance: "MANUAL_ADDITION",
        guidance: { what_to_do: "Tải biên bản kết quả kiểm định" },
        moduleSteps: [
          { id: "result-received", label: "Nhận kết quả kiểm định", completed: false },
        ],
      },
    ],
    edges: [],
    modules: [
      {
        instanceId: "M1",
        templateId: "QC_CHECK",
        templateVersion: 1,
        name: "Kiểm định chất lượng",
        description: "Kiểm định chuyên ngành",
        status: "BLOCKING",
        summary: "0/1 bước",
        completedCount: 0,
        totalCount: 1,
        nextStep: "Nhận kết quả kiểm định",
        nextStepId: "result-received",
        deadline: "",
        blocker: "Chặn giao hàng",
        gate: { stage: "delivery", label: "DELIVERY", type: "BLOCKING" },
        gateText: "Chặn DELIVERY — còn thiếu Nhận kết quả kiểm định",
        provenance: "MANUAL_ADDITION",
        addedBy: "support1",
        addedAt: "2026-10-01",
        reason: "",
        steps: [
          {
            id: "result-received",
            label: "Nhận kết quả kiểm định",
            completed: false,
            completedAt: "",
            completedBy: "",
            note: "",
            blockedBy: [],
            dependencies: [],
            informational: [],
            guidance: { what_to_do: "Tải biên bản kết quả kiểm định" },
            documentCategories: [],
            needsEvidence: true,
          },
        ],
      },
    ],
  },
};

const s2 = {
  ...structuredClone(baseShipment),
  id: "S-C1-2",
  customerId: "C1",
  customer: "Công ty TNHH An Phát",
  customerMST: "0101234567",
  status: "Chờ tàu cập cảng",
  statusTone: "blue",
  route: "Ningbo → Hải Phòng",
  nextAction: "Theo dõi ETA tàu",
  nextActionDetail: "",
  nextRoute: "/lo-hang/S-C1-2?tab=van-tai",
  journey: {
    currentStageId: "",
    owner: "Sale A",
    positionNote: "Chưa đủ mốc thực tế để xác định vị trí vận hành.",
    seaFacts: {},
    primaryAction: {
      text: "Theo dõi ETA tàu",
      detail: "",
      priority: "BinhThuong",
      route: "/lo-hang/S-C1-2?tab=van-tai",
    },
    nodes: [],
    edges: [],
    modules: [
      {
        instanceId: "M2",
        templateId: "QC_CHECK",
        templateVersion: 1,
        name: "Kiểm định chất lượng",
        description: "Kiểm định chuyên ngành",
        status: "WAITING",
        summary: "0/1 bước",
        completedCount: 0,
        totalCount: 1,
        nextStep: "Chuẩn bị hồ sơ",
        nextStepId: "prepare",
        deadline: "",
        blocker: "",
        gate: { stage: "delivery", label: "DELIVERY", type: "BLOCKING" },
        gateText: "",
        provenance: "MANUAL_ADDITION",
        addedBy: "support1",
        addedAt: "2026-10-02",
        reason: "",
        steps: [],
      },
      {
        instanceId: "M-UNK",
        templateId: "UNKNOWN_MOD",
        templateVersion: 3,
        name: "UNKNOWN_MOD",
        description: "",
        status: "UNKNOWN",
        summary: "UNKNOWN",
        completedCount: 0,
        totalCount: 0,
        nextStep: "",
        nextStepId: "",
        deadline: "",
        blocker: "Không đọc được phiên bản quy trình đã gắn.",
        gate: {},
        gateText: "",
        provenance: "MANUAL_ADDITION",
        addedBy: "support1",
        addedAt: "2026-10-02",
        reason: "",
        unresolved: true,
        steps: [],
      },
    ],
  },
};

const sUnlinkedSimilarName = {
  ...structuredClone(baseShipment),
  id: "S-UNLINKED-ANPHAT",
  customerId: undefined,
  customer: "Công ty TNHH An Phát",
  customerMST: "0101234567",
  status: "Đang vận chuyển",
  statusTone: "blue",
  route: "Shenzhen → Cát Lái",
  nextAction: "Kiểm tra bill",
  nextRoute: "/lo-hang/S-UNLINKED-ANPHAT",
};

const sC2 = {
  ...structuredClone(baseShipment),
  id: "S-C2-1",
  customerId: "C2",
  customer: "Công ty Cổ phần Minh Tâm",
  customerMST: "0309876543",
  status: "Đang vận chuyển",
  statusTone: "blue",
  route: "Busan → Hải Phòng",
  nextAction: "Theo dõi lịch tàu",
  nextRoute: "/lo-hang/S-C2-1?tab=van-tai",
  journey: {
    currentStageId: "",
    owner: "Sale B",
    positionNote: "Chưa đủ mốc thực tế để xác định vị trí vận hành.",
    seaFacts: {},
    primaryAction: {
      text: "Theo dõi lịch tàu",
      detail: "",
      priority: "BinhThuong",
      route: "/lo-hang/S-C2-1?tab=van-tai",
    },
    nodes: [],
    edges: [],
    modules: [],
  },
};

model.shipments = [s1, s2, sUnlinkedSimilarName, sC2];

model.attention = [
  {
    id: "ATT-C1-BLOCK",
    shipmentId: "S-C1-1",
    sourceType: "WORK_MODULE",
    sourceRef: "MODULE:S-C1-1:M1",
    band: "BLOCKING",
    reason: "Chặn DELIVERY — còn thiếu Nhận kết quả kiểm định",
    action: "Nhận kết quả kiểm định",
    context: "Kiểm định chất lượng",
    route: "/lo-hang/S-C1-1?tab=nhap&stage=wm-M1-result-received&work=info",
    owner: "",
    deadline: "",
    deadlineDate: "",
    blockedGate: "DELIVERY",
    primary: false,
    moduleTemplateId: "QC_CHECK",
    moduleName: "Kiểm định chất lượng",
    provenance: "work_module:QC_CHECK@1",
    unknown: false,
  },
  {
    id: "ATT-C1-UNKNOWN",
    shipmentId: "S-C1-2",
    sourceType: "WORK_MODULE",
    sourceRef: "MODULE:S-C1-2:M-UNK",
    band: "ACTION",
    reason: "Không đọc được phiên bản quy trình đã gắn.",
    action: "Kiểm tra quy trình đã gắn",
    context: "UNKNOWN_MOD",
    route: "/lo-hang/S-C1-2?tab=nhap",
    owner: "",
    deadline: "",
    deadlineDate: "",
    blockedGate: "",
    primary: false,
    moduleTemplateId: "UNKNOWN_MOD",
    moduleName: "UNKNOWN_MOD",
    provenance: "work_module:UNKNOWN_MOD@3",
    unknown: true,
  },
  {
    id: "ATT-UNLINKED",
    shipmentId: "S-UNLINKED-ANPHAT",
    sourceType: "TASK",
    sourceRef: "TASK:T-999",
    band: "OVERDUE",
    reason: "Việc được giao",
    action: "Việc của lô chưa gắn mã khách hàng",
    context: "Công ty TNHH An Phát",
    route: "/lo-hang/S-UNLINKED-ANPHAT?tab=lay-hang",
    owner: "Support A",
    deadline: "01/10/2026",
    deadlineDate: "2026-10-01",
    blockedGate: "",
    primary: false,
    provenance: "core.database.load_tasks",
    unknown: false,
  },
];

const dom = new JSDOM('<!doctype html><body><div id="host"></div>', {
  url: "http://localhost:9510/",
  pretendToBeVisual: true,
});
globalThis.window = dom.window;
globalThis.document = dom.window.document;
Object.defineProperty(globalThis, "navigator", {
  value: dom.window.navigator,
  configurable: true,
});
for (const key of [
  "HTMLElement",
  "HTMLInputElement",
  "HTMLSelectElement",
  "HTMLTextAreaElement",
  "HTMLAnchorElement",
  "HTMLButtonElement",
  "Event",
  "CustomEvent",
  "MouseEvent",
  "KeyboardEvent",
  "Node",
  "Element",
  "MutationObserver",
  "getComputedStyle",
]) {
  globalThis[key] = dom.window[key];
}
dom.window.HTMLElement.prototype.scrollIntoView = () => {};

const mount = (
  await import(pathToFileURL(path.join(root, "component/dist/logi-shell.js")).href)
).default;
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

// Navigate to Customers (/khach-hang)
const navCustomers = [...document.querySelectorAll("aside a")].find(
  (a) => text(a) === "Khách Hàng"
);
assert.ok(navCustomers, "Customers sidebar link exists");
navCustomers.dispatchEvent(new MouseEvent("click", { bubbles: true, cancelable: true }));
await tick();

// Open C1 Playbook via explicit "Mở hồ sơ" action
const openC1 = document.querySelector('[data-testid="customer-open-playbook-C1"]');
assert.ok(openC1, "Explicit Mở hồ sơ button exists for C1");
assert.equal(openC1.getAttribute("href"), "/khach-hang/C1");
openC1.dispatchEvent(new MouseEvent("click", { bubbles: true, cancelable: true }));
await tick();

const playbook = document.querySelector('[data-testid="customer-playbook"]');
assert.ok(playbook, "CustomerPlaybook detail page rendered");
assert.equal(playbook.getAttribute("data-customer-id"), "C1");

// Maximum four primary blocks check
const primaryBlocks = [...playbook.querySelectorAll(":scope > section")];
assert.equal(primaryBlocks.length, 4, "Playbook renders exactly 4 primary blocks");
assert.deepEqual(
  primaryBlocks.map((s) => s.getAttribute("data-testid")),
  [
    "playbook-identity-note",
    "playbook-attention-hero",
    "playbook-linked-shipments",
    "playbook-concentration",
  ]
);

// Scenario A — customer with operational note
const noteEl = document.querySelector('[data-testid="playbook-operating-note-text"]');
assert.ok(noteEl, "Existing customer note is displayed");
assert.equal(
  text(noteEl),
  "Ghi chú vận hành chuẩn: kiểm tra seal và gửi ảnh container trước khi kéo về kho."
);
const editInMaster = document.querySelector('[data-testid="playbook-edit-in-master"]');
assert.ok(editInMaster, "Link back to existing customer master exists");
assert.equal(editInMaster.getAttribute("href"), "/khach-hang?q=C1");

// Scenario B — exact linked shipments (S-C1-1, S-C1-2 appear; S-UNLINKED-ANPHAT does not)
const shipmentRows = [...document.querySelectorAll('[data-testid="playbook-shipment-row"]')];
assert.deepEqual(
  shipmentRows.map((r) => r.getAttribute("data-shipment-id")),
  ["S-C1-1", "S-C1-2"],
  "Only exact customerId=C1 shipments appear"
);
assert.ok(
  !text(playbook).includes("S-UNLINKED-ANPHAT"),
  "Name-similar unlinked shipment must not appear anywhere on C1 playbook"
);
assert.match(text(shipmentRows[0]), /Thông quan nhập khẩu/);
assert.match(text(shipmentRows[0]), /Nhận kết quả kiểm định/);

// Scenario C & F — Attention reuse + UNKNOWN preservation
const attItems = [...document.querySelectorAll('[data-testid="playbook-attention-item"]')];
assert.equal(attItems.length, 2, "Only C1 linked shipment attention items appear");
assert.equal(attItems[0].getAttribute("data-attention-band"), "BLOCKING");
assert.match(text(attItems[0]), /Chặn DELIVERY — còn thiếu Nhận kết quả kiểm định/);
const attLink0 = attItems[0].querySelector('[data-testid="playbook-attention-link"]');
assert.equal(
  attLink0.getAttribute("href"),
  "/lo-hang/S-C1-1?tab=nhap&stage=wm-M1-result-received&work=info"
);

// UNKNOWN item check
assert.equal(attItems[1].getAttribute("data-attention-unknown"), "true");
assert.ok(
  attItems[1].querySelector('[data-testid="playbook-attention-unknown-badge"]'),
  "UNKNOWN badge rendered on unknown attention item"
);

// Scenario E — Work Modules & canonical blocked gate concentration
const modGroups = [...document.querySelectorAll('[data-testid="playbook-module-group"]')];
const qcGroup = modGroups.find(
  (g) => g.getAttribute("data-module-template") === "QC_CHECK"
);
assert.ok(qcGroup, "QC_CHECK module group rendered");
assert.match(text(qcGroup), /2 lô · 2 lần gắn/);
assert.match(text(qcGroup), /Đang chặn: 1/);
assert.match(text(qcGroup), /Đang chờ: 1/);
assert.match(text(qcGroup), /Cổng đang bị chặn: DELIVERY/);

const unkGroup = modGroups.find(
  (g) => g.getAttribute("data-module-template") === "UNKNOWN_MOD"
);
assert.ok(unkGroup, "UNKNOWN_MOD group rendered");
assert.match(text(unkGroup), /UNKNOWN \(Chưa xác định\): 1/);

const gateGroups = [...document.querySelectorAll('[data-testid="playbook-gate-group"]')];
assert.equal(gateGroups.length, 1);
assert.equal(gateGroups[0].getAttribute("data-gate-key"), "DELIVERY");
assert.match(text(gateGroups[0]), /1 lô · 1 mục chặn/);

// No forbidden risk/health/score/recommendation claims
assert.doesNotMatch(
  text(playbook),
  /healthy|safe|risky|problematic|bottleneck|leaderboard|điểm rủi ro|điểm sức khỏe/i
);

// Click BLOCKING Attention link -> reaches existing shipment/module context
attLink0.dispatchEvent(new MouseEvent("click", { bubbles: true, cancelable: true }));
await tick(150);
const moduleContext = document.querySelector('[data-testid="journey-module-context"]');
assert.ok(
  moduleContext,
  "Clicking BLOCKING Attention item reaches existing ShipmentDetail module context"
);
assert.match(text(moduleContext), /Kiểm định chất lượng/);
assert.match(text(moduleContext), /Nhận kết quả kiểm định/);

// Scenario D — Customer C2 with linked shipment, empty note, and no Attention
navCustomers.dispatchEvent(new MouseEvent("click", { bubbles: true, cancelable: true }));
await tick();
const openC2 = document.querySelector('[data-testid="customer-open-playbook-C2"]');
assert.ok(openC2, "Mở hồ sơ exists for C2");
openC2.dispatchEvent(new MouseEvent("click", { bubbles: true, cancelable: true }));
await tick();

const emptyNote = document.querySelector('[data-testid="playbook-operating-note-empty"]');
assert.ok(emptyNote, "Empty note state rendered for C2");
assert.equal(text(emptyNote), "Chưa ghi nhận ghi chú vận hành.");

const emptyAtt = document.querySelector('[data-testid="playbook-attention-empty"]');
assert.ok(emptyAtt, "Neutral empty attention state rendered for C2");
assert.doesNotMatch(text(emptyAtt), /healthy|safe|an toàn|ổn 100%/i);

const emptyConc = document.querySelector('[data-testid="playbook-concentration-empty"]');
assert.ok(emptyConc, "Honest empty concentration state rendered when no modules/gates exist");

assert.equal(triggers.length, 0, "Customer Playbook V1 emits zero write triggers");
console.log(
  "PASS dom_acceptance_customer_playbook_172: A–F scenarios, 4-block read-only layout, exact linkage, shared Attention drilldown, UNKNOWN preservation"
);
