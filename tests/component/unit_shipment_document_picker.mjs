import assert from "node:assert/strict";
import { importTs } from "./lib_loader.mjs";

const { projectShipmentDocumentCards } = await importTs("shipmentDocumentPicker.ts");
const catalog = [
  { id: "HDNT", label: "Hợp đồng nguyên tắc", category: "Hợp đồng", adapter: "CONTRACT_DOCGEN", documentType: "HDNT", active: true, available: true, availabilityReason: "" },
  { id: "PXK", label: "Phiếu xuất kho", category: "Kho", adapter: "PXK_DOCGEN", documentType: "PXK", active: true, available: true, availabilityReason: "" },
  { id: "GNT", label: "Giấy nộp thuế", category: "Hải quan", adapter: "GNT_BUILDER", documentType: "GNT", active: true, available: true, availabilityReason: "" },
  { id: "NEXT", label: "Chưa hỗ trợ", category: "", adapter: "UNSUPPORTED", documentType: "NEXT", active: true, available: true, availabilityReason: "" },
  { id: "OLD", label: "Ngừng hoạt động", category: "", adapter: "PXK_DOCGEN", documentType: "OLD", active: false, available: true, availabilityReason: "" },
];
const pxkHistory = {
  recordId: "PXK-1::R1", documentId: "PXK-1", documentType: "PXK", revision: 1,
  status: "GENERATED", fileName: "PXK_R1.xlsx", mime: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  attachmentId: "ATT-1", downloadAvailable: true,
};
const shipment = {
  id: "LOT-1",
  importInfo: { gnt: { readiness: { state: "MISSING_INFO", gate: "BLOCKED_MISSING_PREREQUISITES", reason: "Còn thiếu thuế.", missing: ["Thuế nhập khẩu"] } } },
  pxk: { readiness: { state: "MISSING_INFO", gate: "BLOCKED_NOT_DELIVERED", reason: "Chưa xác nhận giao.", missing: ["Xác nhận đã giao hàng"] }, documentHistory: [pxkHistory] },
};
const contract = {
  docCards: [{ document_type: "HDNT", state: "READY", reason: "", missing: [] }],
  documents: [],
};
const base = {
  catalog,
  selectedIds: ["HDNT", "PXK", "GNT", "NEXT", "OLD", "UNKNOWN"],
  shipment,
  linkedContract: contract,
  linkedContractCount: 1,
  canGenerate: true,
  storageConfigured: true,
};

const cards = projectShipmentDocumentCards(base);
assert.deepEqual(cards.map((card) => card.id), ["HDNT", "PXK", "GNT", "NEXT"], "unknown and inactive ids fail closed");
assert.equal(cards.find((card) => card.id === "HDNT").state, "READY");
assert.equal(cards.find((card) => card.id === "HDNT").action, "GENERATE_CONTRACT");
assert.equal(cards.find((card) => card.id === "PXK").state, "GENERATED", "real historical output takes precedence over current readiness");
assert.equal(cards.find((card) => card.id === "PXK").history.length, 1);
assert.equal(cards.find((card) => card.id === "PXK").openOutputAction, "OPEN_PXK");
assert.equal(cards.find((card) => card.id === "PXK").latestDownloadAvailable, true);
assert.equal(cards.find((card) => card.id === "PXK").createRevisionAction, undefined, "blocked canonical gate forbids a new revision");
assert.equal(cards.find((card) => card.id === "GNT").state, "MISSING_INFO");
assert.deepEqual(cards.find((card) => card.id === "GNT").missing, ["Thuế nhập khẩu"]);
assert.equal(cards.find((card) => card.id === "GNT").action, "OPEN_IMPORT");
assert.equal(cards.find((card) => card.id === "NEXT").state, "UNAVAILABLE", "unknown adapter remains fail-closed");

const deselected = projectShipmentDocumentCards({ ...base, selectedIds: ["HDNT"] });
assert.deepEqual(deselected.map((card) => card.id), ["HDNT"], "unselected history stays out of the picker projection");
assert.equal(shipment.pxk.documentHistory[0].recordId, "PXK-1::R1", "projection does not mutate historical output");

const generatedFromCurrentSession = projectShipmentDocumentCards({
  ...base,
  selectedIds: ["GNT"],
  shipment: {
    ...shipment,
    importInfo: { gnt: {
      readiness: { state: "MISSING_INFO", reason: "Thiếu thuế.", missing: ["Thuế nhập khẩu"] },
      done: true,
      document: { recordId: "GNT-SESSION-1", revision: 2, fileName: "GNT_current.xlsx", mime: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", downloadAvailable: true, downloadBase64: "UEs=" },
      documentHistory: [],
    } },
  },
});
assert.equal(generatedFromCurrentSession[0].state, "GENERATED");
assert.equal(generatedFromCurrentSession[0].currentOutput.recordId, "GNT-SESSION-1");
assert.equal(generatedFromCurrentSession[0].history.length, 0, "session output is not fabricated into durable history");
assert.equal(generatedFromCurrentSession[0].latestDownloadAvailable, true);

const unavailable = projectShipmentDocumentCards({ ...base, canGenerate: false });
assert.equal(unavailable.find((card) => card.id === "HDNT").state, "UNAVAILABLE");
assert.match(unavailable.find((card) => card.id === "HDNT").reason, /quyền tạo chứng từ/);
const readOnlyGate = projectShipmentDocumentCards({ ...base, selectedIds: ["GNT"], canGenerate: false })[0];
assert.equal(readOnlyGate.state, "MISSING_INFO", "read-only users still see canonical readiness blockers");
assert.deepEqual(readOnlyGate.missing, ["Thuế nhập khẩu"]);
assert.equal(readOnlyGate.action, "OPEN_IMPORT", "read-only users can navigate to the existing information surface");

const pxkIdentityGate = {
  ...base,
  selectedIds: ["PXK"],
  shipment: {
    ...shipment,
    pxk: {
      readiness: {
        state: "MISSING_INFO",
        gate: "MISSING_INFO",
        reason: "Thiếu 2 thông tin để xuất PXK.",
        missing: ["Thiếu số Phiếu xuất kho.", "Thiếu ngày Phiếu xuất kho."],
      },
      documentHistory: [],
    },
  },
};
const pxkNeedsIdentity = projectShipmentDocumentCards(pxkIdentityGate)[0];
assert.equal(pxkNeedsIdentity.state, "MISSING_INFO");
assert.deepEqual(pxkNeedsIdentity.missing, ["Số PXK", "Ngày PXK"]);
assert.equal(pxkNeedsIdentity.action, "OPEN_PXK");
const pxkDeliveryFacts = projectShipmentDocumentCards({
  ...pxkIdentityGate,
  shipment: {
    ...pxkIdentityGate.shipment,
    pxk: {
      readiness: {
        state: "MISSING_INFO",
        gate: "BLOCKED_MISSING_DELIVERY_FACTS",
        reason: "Còn thiếu người nhận và nơi giao.",
        missing: ["Thiếu người nhận hàng.", "Thiếu địa điểm nhận hàng thực tế."],
      },
      documentHistory: [],
    },
  },
})[0];
assert.equal(pxkDeliveryFacts.action, "OPEN_DELIVERY", "delivery blockers route to the existing delivery confirmation action");
const pxkDraftReady = projectShipmentDocumentCards({
  ...pxkIdentityGate,
  pxkDraft: { number: "PXK-2026-01", date: "2026-10-02" },
})[0];
assert.equal(pxkDraftReady.state, "READY", "local legal identity satisfies only the operator-entered PXK fields");
assert.equal(pxkDraftReady.action, "GENERATE_PXK");
const pxkStillBlocked = projectShipmentDocumentCards({
  ...pxkIdentityGate,
  pxkDraft: { number: "PXK-2026-01", date: "2026-10-02" },
  shipment: {
    ...pxkIdentityGate.shipment,
    pxk: {
      ...pxkIdentityGate.shipment.pxk,
      readiness: {
        ...pxkIdentityGate.shipment.pxk.readiness,
        missing: ["Thiếu số Phiếu xuất kho.", "Thiếu ngày Phiếu xuất kho.", "Thiếu người nhận hàng."],
      },
    },
  },
})[0];
assert.equal(pxkStillBlocked.state, "MISSING_INFO", "operator-entered identity must not bypass other server blockers");
assert.deepEqual(pxkStillBlocked.missing, ["Thiếu người nhận hàng."]);

console.log("PASS: bounded selection projection, readiness, history retention, session output and fail-closed adapters");
