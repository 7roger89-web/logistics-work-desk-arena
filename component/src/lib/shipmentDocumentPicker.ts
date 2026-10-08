import type {
  Contract,
  ContractDocument,
  Shipment,
  ShipmentDocumentReadiness,
  ShipmentDocumentTemplate,
  ShipmentGeneratedDocumentHistory,
} from "./viewmodel";

export type ShipmentDocumentCardState = "READY" | "MISSING_INFO" | "GENERATED" | "UNAVAILABLE";

export type ShipmentDocumentAction =
  | "GENERATE_CONTRACT"
  | "GENERATE_PXK"
  | "GENERATE_GNT"
  | "GENERATE_FORM07"
  | "OPEN_CONTRACT"
  | "OPEN_CONTRACT_LIST"
  | "OPEN_COMMERCIAL_FLOW"
  | "OPEN_IMPORT"
  | "OPEN_DELIVERY"
  | "OPEN_PXK"
  | "OPEN_FORM07";

export interface ShipmentDocumentHistoryItem extends ShipmentGeneratedDocumentHistory {
  downloadBase64?: string | null;
}

export interface ShipmentDocumentCard {
  id: string;
  label: string;
  category: string;
  adapter: string;
  documentType: string;
  state: ShipmentDocumentCardState;
  reason: string;
  missing: string[];
  history: ShipmentDocumentHistoryItem[];
  /** Current output may be session-readable even when durable history is older or absent. */
  currentOutput?: ShipmentDocumentHistoryItem;
  action?: ShipmentDocumentAction;
  openOutputAction?: ShipmentDocumentAction;
  createRevisionAction?: ShipmentDocumentAction;
  latestDownloadAvailable: boolean;
}

interface CardProjectionInput {
  catalog: ShipmentDocumentTemplate[];
  selectedIds: string[];
  shipment: Shipment;
  linkedContract: Contract | null;
  linkedContractCount: number;
  canGenerate: boolean;
  storageConfigured: boolean;
  pxkDraft?: { number?: string; date?: string };
  /** Issue #168 — the operator-typed FORM_07 identity draft (never persisted). */
  form07Draft?: { number?: string; orderDate?: string };
}

const SUPPORTED_ADAPTERS = new Set(["CONTRACT_DOCGEN", "PXK_DOCGEN", "GNT_BUILDER", "FORM07_DOCGEN"]);
const GENERATION_ACTIONS = new Set<ShipmentDocumentAction>([
  "GENERATE_CONTRACT", "GENERATE_PXK", "GENERATE_GNT", "GENERATE_FORM07",
]);

function cleanList(values: unknown): string[] {
  return Array.isArray(values)
    ? values.filter((item): item is string => typeof item === "string" && item.trim().length > 0)
    : [];
}

function revisionOf(row: { revision?: number }): number {
  const value = Number(row.revision ?? 0);
  return Number.isFinite(value) && value > 0 ? value : 0;
}

function toContractHistory(document: ContractDocument): ShipmentDocumentHistoryItem {
  return {
    recordId: document.id,
    documentId: document.documentId,
    documentType: document.documentType,
    revision: revisionOf(document),
    status: document.status,
    fileName: document.fileName,
    mime: document.mime,
    generatedAt: document.generatedAt,
    generatedBy: document.generatedBy,
    attachmentId: "",
    downloadAvailable: Boolean(document.downloadAvailable || document.downloadBase64),
    downloadBase64: document.downloadBase64,
  };
}

function sortedHistory(rows: ShipmentDocumentHistoryItem[]): ShipmentDocumentHistoryItem[] {
  return [...rows].sort((a, b) => revisionOf(a) - revisionOf(b) || a.recordId.localeCompare(b.recordId));
}

function contractGate(contract: Contract | null, documentType: string): {
  state: string;
  reason: string;
  missing: string[];
} {
  const gate = contract?.docCards?.find((card) => card.document_type === documentType);
  if (!gate) {
    return {
      state: "UNKNOWN",
      reason: "Chưa đọc được cổng chứng từ canonical của hợp đồng.",
      missing: [],
    };
  }
  return {
    state: gate.state,
    reason: gate.reason || "",
    missing: cleanList(gate.missing),
  };
}

function readinessFor(
  template: ShipmentDocumentTemplate,
  input: CardProjectionInput,
): { state: string; reason: string; missing: string[]; action?: ShipmentDocumentAction } {
  const { shipment, linkedContract, linkedContractCount } = input;
  if (!template.active || !SUPPORTED_ADAPTERS.has(template.adapter)) {
    return { state: "UNAVAILABLE", reason: "Biểu mẫu không hoạt động hoặc chưa có bộ xử lý được hỗ trợ.", missing: [] };
  }
  if (!template.available) {
    return {
      state: "UNAVAILABLE",
      reason: template.availabilityReason || "Tác vụ hiện chưa sẵn sàng.",
      missing: [],
    };
  }
  if (template.adapter === "CONTRACT_DOCGEN") {
    if (!linkedContract) {
      const reason = linkedContractCount > 1
        ? "Có nhiều hợp đồng liên kết; cần xác định đúng hợp đồng trước khi tạo."
        : "Chưa liên kết hợp đồng với lô này.";
      return {
        state: "MISSING_INFO",
        reason,
        missing: [reason],
        action: "OPEN_CONTRACT_LIST",
      };
    }
    const gate = contractGate(linkedContract, template.documentType);
    if (gate.state === "READY") return { ...gate, action: "GENERATE_CONTRACT" };
    if (gate.state === "MISSING_INFO" || gate.state === "BLOCKED" || gate.state === "DRAFT") {
      return { ...gate, state: "MISSING_INFO", action: "OPEN_CONTRACT" };
    }
    if (gate.state === "NOT_APPLICABLE" || gate.state === "OWNER_RULE_REQUIRED") {
      return { ...gate, state: "UNAVAILABLE" };
    }
    return {
      state: "UNAVAILABLE",
      reason: gate.reason || "Cổng chứng từ chưa xác định; tạo bị khóa an toàn.",
      missing: gate.missing,
    };
  }

  if (template.adapter === "GNT_BUILDER") {
    const gnt = shipment.importInfo?.gnt;
    const gate = gnt?.readiness;
    if (!gate || typeof gate.state !== "string") {
      return { state: "UNAVAILABLE", reason: "Chưa có readback cổng GNT từ backend.", missing: [] };
    }
    const missing = cleanList(gate.missing ?? gnt?.missing);
    if (gate.state === "READY") return { state: "READY", reason: gate.reason || "", missing, action: "GENERATE_GNT" };
    if (gate.state === "NOT_APPLICABLE") {
      return { state: "UNAVAILABLE", reason: gate.reason || "GNT không áp dụng cho dữ liệu hiện tại.", missing };
    }
    if (gate.state === "MISSING_INFO" || gate.state === "BLOCKED") {
      const action = gate.gate === "COMMERCIAL_FLOW_REQUIRED" || gate.gate === "LEGAL_IMPORTER_TAX_CODE_REQUIRED"
        ? "OPEN_COMMERCIAL_FLOW"
        : "OPEN_IMPORT";
      return { state: "MISSING_INFO", reason: gate.reason || "GNT còn thiếu thông tin.", missing, action };
    }
    return { state: "UNAVAILABLE", reason: gate.reason || "Cổng GNT chưa xác định; tạo bị khóa an toàn.", missing };
  }

  if (template.adapter === "FORM07_DOCGEN") {
    // Issue #168 — the server owns FORM_07 readiness from canonical facts; the
    // only client-side addition is the typed operator identity draft (same
    // pattern PXK uses for Số/Ngày), never a client-invented gate.
    const gate = shipment.form07?.readiness;
    if (!gate || typeof gate.state !== "string") {
      return { state: "UNAVAILABLE", reason: "Chưa có readback cổng FORM_07 từ backend.", missing: [] };
    }
    const missing = cleanList(gate.missing);
    const draftNumber = input.form07Draft?.number?.trim() || shipment.form07?.number?.trim() || "";
    const draftOrderDate = input.form07Draft?.orderDate?.trim() || shipment.form07?.orderDate?.trim() || "";
    const backendRequiresNumber = missing.some((item) => /thiếu số biên bản/i.test(item));
    const backendRequiresOrderDate = missing.some((item) => /thiếu ngày đơn đặt hàng/i.test(item));
    const otherMissing = missing.filter((item) =>
      !/thiếu (số biên bản|ngày đơn đặt hàng)/i.test(item)
    );
    const legalIdentityMissing = [
      ...(!draftNumber ? ["Số biên bản"] : []),
      ...(!draftOrderDate ? ["Ngày đơn đặt hàng"] : []),
    ];
    const hasOnlyOperatorIdentityBlock =
      gate.state === "MISSING_INFO" &&
      otherMissing.length === 0 &&
      (backendRequiresNumber || backendRequiresOrderDate);
    const mergedMissing = [...otherMissing, ...legalIdentityMissing];

    if (gate.state === "READY" || hasOnlyOperatorIdentityBlock) {
      if (legalIdentityMissing.length) {
        return {
          state: "MISSING_INFO",
          reason: "Nhập số biên bản và ngày đơn đặt hàng ở phần tạo biên bản.",
          missing: legalIdentityMissing,
          action: "OPEN_FORM07",
        };
      }
      return { state: "READY", reason: gate.reason || "", missing: [], action: "GENERATE_FORM07" };
    }
    if (gate.state === "NOT_APPLICABLE") {
      return { state: "UNAVAILABLE", reason: gate.reason || "FORM_07 không áp dụng cho dữ liệu hiện tại.", missing };
    }
    if (gate.state === "MISSING_INFO" || gate.state === "BLOCKED") {
      const action = gate.gate === "BLOCKED_NOT_DELIVERED" || gate.gate === "BLOCKED_MISSING_DELIVERY_FACTS"
        ? "OPEN_DELIVERY"
        : gate.gate === "BLOCKED_NO_SOURCE" || gate.gate === "BLOCKED_AMBIGUOUS_SOURCE"
          ? "OPEN_CONTRACT_LIST"
          : "OPEN_FORM07";
      return {
        state: "MISSING_INFO",
        reason: gate.reason || "FORM_07 còn thiếu thông tin.",
        missing: mergedMissing.length ? mergedMissing : missing,
        action,
      };
    }
    return { state: "UNAVAILABLE", reason: gate.reason || "Cổng FORM_07 chưa xác định; tạo bị khóa an toàn.", missing };
  }

  const gate = shipment.pxk?.readiness;
  if (!gate || typeof gate.state !== "string") {
    return { state: "UNAVAILABLE", reason: "Chưa có readback cổng PXK từ backend.", missing: [] };
  }
  const missing = cleanList(gate.missing);
  const draftNumber = input.pxkDraft?.number?.trim() || shipment.pxk?.number?.trim() || "";
  const draftDate = input.pxkDraft?.date?.trim() || shipment.pxk?.date?.trim() || "";
  const backendRequiresNumber = missing.some((item) => /thiếu số phiếu xuất kho/i.test(item));
  const backendRequiresDate = missing.some((item) => /thiếu ngày phiếu xuất kho/i.test(item));
  const otherMissing = missing.filter((item) =>
    !/thiếu (số|ngày) phiếu xuất kho/i.test(item)
  );
  const legalIdentityMissing = [
    ...(!draftNumber ? ["Số PXK"] : []),
    ...(!draftDate ? ["Ngày PXK"] : []),
  ];
  const hasOnlyOperatorIdentityBlock =
    gate.state === "MISSING_INFO" &&
    otherMissing.length === 0 &&
    (backendRequiresNumber || backendRequiresDate);
  const mergedMissing = [...otherMissing, ...legalIdentityMissing];

  if (gate.state === "READY" || hasOnlyOperatorIdentityBlock) {
    if (legalIdentityMissing.length) {
      return {
        state: "MISSING_INFO",
        reason: "Nhập số và ngày pháp lý của PXK ở phần tạo phiếu.",
        missing: legalIdentityMissing,
        action: "OPEN_PXK",
      };
    }
    return { state: "READY", reason: gate.reason || "", missing: [], action: "GENERATE_PXK" };
  }
  if (gate.state === "NOT_APPLICABLE") {
    return { state: "UNAVAILABLE", reason: gate.reason || "PXK không áp dụng cho luồng này.", missing };
  }
  if (gate.state === "MISSING_INFO" || gate.state === "BLOCKED") {
    const action = gate.gate === "COMMERCIAL_FLOW_REQUIRED" ? "OPEN_COMMERCIAL_FLOW"
      : gate.gate === "BLOCKED_NOT_DELIVERED" || gate.gate === "BLOCKED_MISSING_DELIVERY_FACTS" ? "OPEN_DELIVERY"
        : gate.gate === "BLOCKED_NO_SOURCE" || gate.gate === "BLOCKED_AMBIGUOUS_SOURCE" ? "OPEN_CONTRACT_LIST"
          : "OPEN_PXK";
    return {
      state: "MISSING_INFO",
      reason: gate.reason || "PXK còn thiếu thông tin.",
      missing: mergedMissing.length ? mergedMissing : missing,
      action,
    };
  }
  return { state: "UNAVAILABLE", reason: gate.reason || "Cổng PXK chưa xác định; tạo bị khóa an toàn.", missing };
}

function historyFor(template: ShipmentDocumentTemplate, input: CardProjectionInput): ShipmentDocumentHistoryItem[] {
  if (template.adapter === "CONTRACT_DOCGEN") {
    return sortedHistory(
      (input.linkedContract?.documents ?? [])
        .filter((document) => document.documentType === template.documentType)
        .map(toContractHistory),
    );
  }
  if (template.adapter === "GNT_BUILDER") {
    const gnt = input.shipment.importInfo?.gnt;
    const projected = Array.isArray(gnt?.documentHistory) ? gnt.documentHistory : [];
    const nested = Array.isArray(gnt?.document?.history) ? gnt.document.history : [];
    return sortedHistory((projected.length ? projected : nested).filter((row) => row.documentType === template.documentType));
  }
  if (template.adapter === "FORM07_DOCGEN") {
    const projected = Array.isArray(input.shipment.form07?.documentHistory) ? input.shipment.form07!.documentHistory! : [];
    const nested = Array.isArray(input.shipment.form07?.document?.history) ? input.shipment.form07!.document!.history! : [];
    return sortedHistory((projected.length ? projected : nested).filter((row) => row.documentType === template.documentType));
  }
  const projected = Array.isArray(input.shipment.pxk?.documentHistory) ? input.shipment.pxk.documentHistory : [];
  const nested = Array.isArray(input.shipment.pxk?.document?.history) ? input.shipment.pxk.document.history : [];
  return sortedHistory((projected.length ? projected : nested).filter((row) => row.documentType === template.documentType));
}

function currentOutputFor(
  template: ShipmentDocumentTemplate,
  input: CardProjectionInput,
): ShipmentDocumentHistoryItem | undefined {
  if (template.adapter === "CONTRACT_DOCGEN") return undefined;
  const document = template.adapter === "GNT_BUILDER"
    ? input.shipment.importInfo?.gnt?.document
    : template.adapter === "FORM07_DOCGEN"
      ? input.shipment.form07?.document
      : input.shipment.pxk?.document;
  if (!document) return undefined;
  const revision = Number(document.revision ?? 0);
  const fileName = document.fileName || "";
  if (!fileName && !document.downloadBase64 && !document.attachmentId && !document.downloadAvailable) return undefined;
  return {
    recordId: document.recordId || document.documentId || `${template.documentType}-current-output`,
    documentId: document.documentId,
    documentType: template.documentType,
    revision: Number.isFinite(revision) && revision > 0 ? revision : 1,
    status: document.status || "GENERATED",
    fileName,
    mime: document.mime || "application/octet-stream",
    generatedAt: document.generatedAt,
    generatedBy: document.generatedBy,
    attachmentId: document.attachmentId,
    downloadAvailable: Boolean(document.downloadAvailable || document.downloadBase64),
    downloadBase64: document.downloadBase64,
  };
}

function isHistoryDownloadAvailable(
  row: ShipmentDocumentHistoryItem,
  template: ShipmentDocumentTemplate,
  storageConfigured: boolean,
): boolean {
  if (row.downloadBase64) return true;
  if (template.adapter === "CONTRACT_DOCGEN") return false;
  return Boolean(row.attachmentId && storageConfigured);
}

/** Pure adapter from server catalog + canonical shipment gates to UI cards. */
export function projectShipmentDocumentCards(input: CardProjectionInput): ShipmentDocumentCard[] {
  const selected = new Set(cleanList(input.selectedIds));
  return input.catalog
    .filter((template) => template.active && selected.has(template.id))
    .map((template) => {
      const history = historyFor(template, input);
      const currentOutput = currentOutputFor(template, input);
      const latest = currentOutput ?? history[history.length - 1];
      const readiness = readinessFor(template, input);
      const created = history.length > 0 || Boolean(currentOutput);
      const permissionReason = input.canGenerate ? "" : "Tài khoản hiện không có quyền tạo chứng từ.";
      const state: ShipmentDocumentCardState = created
        ? "GENERATED"
        : !input.canGenerate && readiness.state === "READY"
          ? "UNAVAILABLE"
          : readiness.state as ShipmentDocumentCardState;
      const reason = created
        ? [
            readiness.state === "READY"
              ? "Đã có bản tạo; lịch sử được giữ nguyên khi bỏ chọn biểu mẫu."
              : `Đã có bản tạo. ${readiness.reason}`.trim(),
            permissionReason,
          ].filter(Boolean).join(" ")
        : !input.canGenerate && readiness.state === "READY"
          ? permissionReason
          : readiness.reason;
      const createRevisionAction = created && input.canGenerate && readiness.state === "READY"
        ? readiness.action
        : undefined;
      const primaryAction = !input.canGenerate && readiness.action && GENERATION_ACTIONS.has(readiness.action)
        ? undefined
        : readiness.action;
      const openOutputAction: ShipmentDocumentAction | undefined = created
        ? template.adapter === "CONTRACT_DOCGEN" ? "OPEN_CONTRACT"
          : template.adapter === "GNT_BUILDER" ? "OPEN_IMPORT"
            : template.adapter === "FORM07_DOCGEN" ? "OPEN_FORM07"
              : "OPEN_PXK"
        : undefined;
      return {
        id: template.id,
        label: template.label,
        category: template.category,
        adapter: template.adapter,
        documentType: template.documentType,
        state,
        reason,
        missing: readiness.missing,
        history,
        currentOutput,
        action: created ? undefined : primaryAction,
        openOutputAction,
        createRevisionAction,
        latestDownloadAvailable: latest
          ? isHistoryDownloadAvailable(latest, template, input.storageConfigured)
          : false,
      };
    });
}
