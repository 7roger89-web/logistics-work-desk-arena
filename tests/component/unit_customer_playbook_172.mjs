import assert from "node:assert/strict";
import { importTs } from "./lib_loader.mjs";

const {
  buildCustomerPlaybook,
  customerIdFromPath,
  customerMasterFilterPath,
  customerPath,
} = await importTs("customerPlaybook.ts");

const customers = [
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
    note: "Trước khi giao hàng phải gửi biên bản kiểm đếm container qua email kho.",
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

const shipments = [
  {
    id: "S-C1-1",
    customerId: "C1",
    customer: "Công ty TNHH An Phát",
    customerMST: "0101234567",
    status: "Đang làm thủ tục nhập",
    statusTone: "amber",
    route: "Shanghai → Hải Phòng",
    nextAction: "Hoàn tất hồ sơ QC",
    nextActionDetail: "Còn thiếu biên bản kết quả",
    nextRoute: "/lo-hang/S-C1-1?tab=nhap",
    journey: {
      currentStageId: "customs-import",
      owner: "Sale A",
      positionNote: "",
      seaFacts: {},
      primaryAction: {
        text: "Hoàn tất hồ sơ QC",
        detail: "Còn thiếu biên bản kết quả",
        priority: "CanXuLy",
        route: "/lo-hang/S-C1-1?tab=nhap",
      },
      nodes: [
        {
          id: "customs-import",
          label: "Thông quan nhập khẩu",
          family: "IMPORT",
          targetTab: "nhap",
          completed: false,
          state: "CURRENT",
          factState: "KNOWN",
          evidence: "TK 10555",
          deadline: "",
          owned: true,
          current: true,
          blockers: [],
          dependencies: [],
          documentCategories: [],
          documentIds: [],
        },
      ],
      edges: [],
      modules: [
        {
          instanceId: "M1",
          templateId: "QC_CHECK",
          templateVersion: 1,
          name: "Kiểm định chất lượng",
          description: "Quy trình kiểm định chuyên ngành",
          status: "BLOCKING",
          summary: "1/2 bước",
          completedCount: 1,
          totalCount: 2,
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
          steps: [],
        },
      ],
    },
  },
  {
    id: "S-C1-2",
    customerId: "C1",
    customer: "Công ty TNHH An Phát",
    customerMST: "0101234567",
    status: "Chờ tàu cập cảng",
    statusTone: "blue",
    route: "Ningbo → Hải Phòng",
    nextAction: "Theo dõi tàu cập cảng",
    nextActionDetail: "",
    nextRoute: "/lo-hang/S-C1-2?tab=van-tai",
    journey: {
      currentStageId: "",
      owner: "Sale A",
      positionNote: "Chưa đủ mốc thực tế để xác định vị trí vận hành.",
      seaFacts: {},
      primaryAction: {
        text: "Theo dõi tàu cập cảng",
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
          description: "Quy trình kiểm định chuyên ngành",
          status: "WAITING",
          summary: "0/2 bước",
          completedCount: 0,
          totalCount: 2,
          nextStep: "Chuẩn bị hồ sơ",
          nextStepId: "prepare-file",
          deadline: "",
          blocker: "",
          // Template declares gate, but instance status is WAITING (not BLOCKING).
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
          templateId: "LEGACY_MOD",
          templateVersion: 9,
          name: "LEGACY_MOD",
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
  },
  // Negative challenge 1: identical customer name & MST, but NO customerId
  {
    id: "S-NAME-ONLY",
    customer: "Công ty TNHH An Phát",
    customerMST: "0101234567",
    status: "Đang vận chuyển",
    statusTone: "blue",
    route: "Shenzhen → Cát Lái",
    nextAction: "Kiểm tra chứng từ",
    nextRoute: "/lo-hang/S-NAME-ONLY",
  },
  // Negative challenge 2: empty string customerId + toneless name
  {
    id: "S-EMPTY-ID",
    customerId: "",
    customer: "Cong ty TNHH An Phat",
    customerMST: "0101234567",
    status: "Mới tạo",
    statusTone: "gray",
    route: "Qingdao → Hải Phòng",
    nextAction: "Khai báo lô",
    nextRoute: "/lo-hang/S-EMPTY-ID",
  },
  // Negative challenge 3: lowercase customerId ("c1" !== "C1")
  {
    id: "S-LOWERCASE-ID",
    customerId: "c1",
    customer: "Công ty TNHH An Phát",
    customerMST: "0101234567",
    status: "Mới tạo",
    statusTone: "gray",
    route: "Busan → Hải Phòng",
    nextAction: "Khai báo lô",
    nextRoute: "/lo-hang/S-LOWERCASE-ID",
  },
  // Negative challenge 4: belongs to C2
  {
    id: "S-C2-1",
    customerId: "C2",
    customer: "Công ty Cổ phần Minh Tâm",
    customerMST: "0309876543",
    status: "Đang vận chuyển",
    statusTone: "blue",
    route: "Kaohsiung → Cát Lái",
    nextAction: "Theo dõi ETA",
    nextRoute: "/lo-hang/S-C2-1?tab=van-tai",
  },
];

const attention = [
  {
    id: "ATT-BLOCK-C1",
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
    id: "ATT-UNKNOWN-C1",
    shipmentId: "S-C1-2",
    sourceType: "WORK_MODULE",
    sourceRef: "MODULE:S-C1-2:M-UNK",
    band: "ACTION",
    reason: "Không đọc được phiên bản quy trình đã gắn.",
    action: "Kiểm tra quy trình đã gắn",
    context: "LEGACY_MOD",
    route: "/lo-hang/S-C1-2?tab=nhap",
    owner: "",
    deadline: "",
    deadlineDate: "",
    blockedGate: "",
    primary: false,
    moduleTemplateId: "LEGACY_MOD",
    moduleName: "LEGACY_MOD",
    provenance: "work_module:LEGACY_MOD@9",
    unknown: true,
  },
  // Attention on name-similar unlinked shipment MUST NOT leak into C1 playbook
  {
    id: "ATT-NAME-ONLY-LEAK",
    shipmentId: "S-NAME-ONLY",
    sourceType: "TASK",
    sourceRef: "TASK:T-LEAK",
    band: "OVERDUE",
    reason: "Việc được giao",
    action: "Việc của lô chỉ trùng tên",
    context: "Công ty TNHH An Phát",
    route: "/lo-hang/S-NAME-ONLY?tab=lay-hang",
    owner: "Support A",
    deadline: "01/10/2026",
    deadlineDate: "2026-10-01",
    blockedGate: "",
    primary: false,
    provenance: "core.database.load_tasks",
    unknown: false,
  },
];

// --- Scenario A: Existing customer note ---
const c1Playbook = buildCustomerPlaybook({
  customerId: "C1",
  customers,
  shipments,
  attention,
});

assert.equal(c1Playbook.status, "FOUND");
assert.equal(c1Playbook.readOnly, true);
assert.equal(c1Playbook.exactLinkRule, "shipment.customerId === customer.id");
assert.equal(
  c1Playbook.customer.note,
  "Trước khi giao hàng phải gửi biên bản kiểm đếm container qua email kho."
);
assert.equal(c1Playbook.customer.hasOperatingNote, true);
assert.equal(c1Playbook.customer.operatingNoteLabel, "Ghi chú vận hành");
assert.equal(c1Playbook.customer.masterEditHref, "/khach-hang?q=C1");

// --- Scenario B: Exact customer identity & negative fuzzy challenges ---
assert.deepEqual(
  c1Playbook.linkedShipments.map((s) => s.id),
  ["S-C1-1", "S-C1-2"],
  "only exact customerId === C1 shipments may appear"
);
assert.equal(
  c1Playbook.linkedShipments[0].journeyPosition,
  "Thông quan nhập khẩu",
  "resolved current Journey node label"
);
assert.equal(
  c1Playbook.linkedShipments[1].journeyPosition,
  "",
  "shipment without currentStageId keeps empty position and uses positionNote"
);
assert.match(
  c1Playbook.linkedShipments[1].journeyPositionNote,
  /Chưa đủ mốc thực tế/
);

// --- Scenario C: Attention reuse & canonical route preservation ---
assert.deepEqual(
  c1Playbook.attention.items.map((i) => i.id),
  ["ATT-BLOCK-C1", "ATT-UNKNOWN-C1"],
  "unlinked name-similar shipment attention is excluded; shared order preserved"
);
assert.equal(c1Playbook.attention.items[0].band, "BLOCKING");
assert.equal(
  c1Playbook.attention.items[0].reason,
  "Chặn DELIVERY — còn thiếu Nhận kết quả kiểm định"
);
assert.equal(
  c1Playbook.attention.items[0].route,
  "/lo-hang/S-C1-1?tab=nhap&stage=wm-M1-result-received&work=info"
);

// --- Scenario D: No attention neutral empty state ---
const c2Playbook = buildCustomerPlaybook({
  customerId: "C2",
  customers,
  shipments,
  attention,
});
assert.equal(c2Playbook.customer.hasOperatingNote, false);
assert.equal(
  c2Playbook.customer.operatingNoteEmptyText,
  "Chưa ghi nhận ghi chú vận hành."
);
assert.deepEqual(
  c2Playbook.linkedShipments.map((s) => s.id),
  ["S-C2-1"]
);
assert.equal(c2Playbook.attention.totalCount, 0);
assert.equal(c2Playbook.attention.items.length, 0);
assert.doesNotMatch(
  c2Playbook.attention.emptyText,
  /healthy|safe|an toàn|ổn 100%|xanh/i
);

// --- Scenario E: Work Module & blocked gate concentration ---
const qcGroup = c1Playbook.concentration.modules.find(
  (m) => m.templateId === "QC_CHECK"
);
assert.ok(qcGroup, "QC_CHECK module group exists");
assert.equal(qcGroup.shipmentCount, 2);
assert.equal(qcGroup.instanceCount, 2);
assert.equal(qcGroup.blockingCount, 1);
assert.equal(qcGroup.waitingCount, 1);
assert.equal(qcGroup.doneCount, 0);
assert.deepEqual(qcGroup.blockedGates, ["DELIVERY"]);

const deliveryGate = c1Playbook.concentration.gates.find(
  (g) => g.key === "DELIVERY"
);
assert.ok(deliveryGate, "DELIVERY blocked gate group exists");
assert.equal(
  deliveryGate.shipmentCount,
  1,
  "only the actually BLOCKING instance counts as blocking DELIVERY"
);
assert.equal(deliveryGate.count, 1);
assert.deepEqual(deliveryGate.shipmentIds, ["S-C1-1"]);

// --- Scenario F: UNKNOWN semantics ---
assert.equal(c1Playbook.attention.unknownCount, 1);
assert.equal(c1Playbook.attention.items[1].unknown, true);
const legacyGroup = c1Playbook.concentration.modules.find(
  (m) => m.templateId === "LEGACY_MOD"
);
assert.ok(legacyGroup, "UNKNOWN module group exists");
assert.equal(legacyGroup.unknownCount, 1);
assert.equal(legacyGroup.doneCount, 0);
assert.equal(c1Playbook.linkedShipments[1].unknownModuleCount, 1);

// --- Route encoding & no score/recommendation fields ---
assert.equal(customerPath("CUST/01"), "/khach-hang/CUST%2F01");
assert.equal(customerIdFromPath("/khach-hang/CUST%2F01"), "CUST/01");
assert.equal(
  customerIdFromPath("/khach-hang/CUST%252F01", "CUST/01"),
  "CUST%2F01"
);
assert.equal(customerMasterFilterPath("CUST/01"), "/khach-hang?q=CUST%2F01");

const serialized = JSON.stringify(c1Playbook).toLowerCase();
for (const forbidden of [
  "score",
  "risky",
  "problematic",
  "healthy",
  "safe",
  "bottleneck",
  "recommend",
  "preference",
  "pipeline",
  "opportunity",
  "crm",
]) {
  assert.ok(
    !serialized.includes(forbidden),
    `projection must not contain forbidden term: ${forbidden}`
  );
}

console.log(
  "PASS unit_customer_playbook_172: exact linkage, negative fuzzy challenges, note authority, shared Attention reuse, neutral empty states, UNKNOWN semantics, factual module/gate concentration"
);
