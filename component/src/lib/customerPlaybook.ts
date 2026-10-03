import { shipmentPath } from "./shipmentRoute";
import type { AttentionItem, Customer, Shipment, Tone } from "./viewmodel";

export const CUSTOMER_ROUTE_PREFIX = "/khach-hang/";
export const MAX_CUSTOMER_ATTENTION_ITEMS = 12;

export function customerPath(id: string): string {
  return CUSTOMER_ROUTE_PREFIX + encodeURIComponent(id.trim());
}

export function customerMasterFilterPath(id: string): string {
  return "/khach-hang?q=" + encodeURIComponent(id.trim());
}

/**
 * Decode the exact customer identity from `/khach-hang/:id` pathname once,
 * preserving literal percent-encoded characters such as `%2F` just like
 * `shipmentIdFromPath`.
 */
export function customerIdFromPath(pathname: string, paramId?: string): string {
  const fallback = (paramId ?? "").trim();
  if (!pathname.startsWith(CUSTOMER_ROUTE_PREFIX)) return fallback;
  const raw = pathname.slice(CUSTOMER_ROUTE_PREFIX.length).replace(/\/+$/, "");
  if (raw === "" || raw.includes("/")) return fallback;
  try {
    return decodeURIComponent(raw).trim();
  } catch {
    return fallback;
  }
}

export interface CustomerPlaybookIdentity {
  id: string;
  name: string;
  taxCode: string;
  contactPerson: string;
  phone: string;
  email: string;
  address: string;
  note: string;
  hasOperatingNote: boolean;
  operatingNoteLabel: string;
  operatingNoteEmptyText: string;
  masterEditHref: string;
  masterListHref: string;
}

export interface CustomerPlaybookShipmentRow {
  id: string;
  customerId: string;
  status: string;
  statusTone: Tone;
  route: string;
  journeyCurrentStageId: string;
  journeyPosition: string;
  journeyPositionNote: string;
  primaryAction: string;
  primaryActionDetail: string;
  primaryActionRoute: string;
  openHref: string;
  moduleCount: number;
  unknownModuleCount: number;
}

export interface CustomerPlaybookModuleGroup {
  key: string;
  templateId: string;
  label: string;
  instanceCount: number;
  shipmentCount: number;
  shipmentIds: string[];
  blockingCount: number;
  waitingCount: number;
  doneCount: number;
  unknownCount: number;
  blockedGates: string[];
}

export interface CustomerPlaybookGateGroup {
  key: string;
  label: string;
  count: number;
  shipmentCount: number;
  shipmentIds: string[];
  moduleNames: string[];
}

export interface CustomerPlaybookProjection {
  classification: "READ_ONLY_CUSTOMER_PLAYBOOK_V1";
  readOnly: true;
  exactLinkRule: "shipment.customerId === customer.id";
  status: "FOUND" | "NOT_FOUND";
  requestedId: string;
  customer: CustomerPlaybookIdentity | null;
  coverage: {
    exactLinkedShipmentCount: number;
    note: string;
  };
  attention: {
    items: AttentionItem[];
    visibleItems: AttentionItem[];
    totalCount: number;
    blockingCount: number;
    overdueCount: number;
    dueSoonCount: number;
    actionCount: number;
    unknownCount: number;
    truncated: boolean;
    emptyText: string;
  };
  linkedShipments: CustomerPlaybookShipmentRow[];
  concentration: {
    modules: CustomerPlaybookModuleGroup[];
    gates: CustomerPlaybookGateGroup[];
    hasConcentrationFacts: boolean;
    emptyText: string;
  };
}

export interface CustomerPlaybookInput {
  customerId: string;
  customers?: Customer[] | null;
  shipments?: Shipment[] | null;
  attention?: AttentionItem[] | null;
  maxAttentionItems?: number;
}

function cleanText(value: unknown): string {
  if (value === null || value === undefined) return "";
  return String(value).trim();
}

function resolveJourneyPosition(shipment: Shipment): {
  currentStageId: string;
  position: string;
  positionNote: string;
} {
  const journey = shipment.journey;
  if (!journey) {
    return {
      currentStageId: "",
      position: "",
      positionNote: "Chưa có dữ liệu hành trình.",
    };
  }
  const nodes = Array.isArray(journey.nodes) ? journey.nodes : [];
  const currentStageId = cleanText(journey.currentStageId);
  if (currentStageId) {
    const currentNode =
      nodes.find((n) => n && n.current) ??
      nodes.find((n) => n && cleanText(n.id) === currentStageId);
    const label = cleanText(currentNode?.label) || currentStageId;
    return {
      currentStageId,
      position: label,
      positionNote: cleanText(journey.positionNote),
    };
  }
  return {
    currentStageId: "",
    position: "",
    positionNote:
      cleanText(journey.positionNote) ||
      "Chưa đủ mốc thực tế để xác định vị trí vận hành.",
  };
}

function normalizeModuleStatus(rawStatus: unknown, unresolved?: boolean): "DONE" | "WAITING" | "BLOCKING" | "UNKNOWN" {
  if (unresolved) return "UNKNOWN";
  const upper = cleanText(rawStatus).toUpperCase();
  if (upper === "DONE") return "DONE";
  if (upper === "WAITING") return "WAITING";
  if (upper === "BLOCKING") return "BLOCKING";
  return "UNKNOWN";
}

/**
 * Pure read-only Customer Playbook V1 composition over existing ViewModel
 * `customers`, `shipments`, and `attention`.
 *
 * Load-bearing rules:
 * - Customer `note` from the existing customer master is the sole operating note.
 * - Shipment linkage uses exact `shipment.customerId === customer.id` only.
 *   Never fuzzy-matches customer name, taxCode/MST, phone, email, or contact.
 * - Attention reuses the shared `attention` list filtered by exact linked
 *   shipment IDs, preserving band, order, reason, unknown, and canonical route.
 * - Operational concentration groups only factual attached Work Modules and
 *   canonical blocked gates on linked shipments without risk/preference scoring.
 */
export function buildCustomerPlaybook(
  input: CustomerPlaybookInput
): CustomerPlaybookProjection {
  const requestedId = cleanText(input.customerId);
  const customers = Array.isArray(input.customers) ? input.customers : [];
  const shipments = Array.isArray(input.shipments) ? input.shipments : [];
  const attentionList = Array.isArray(input.attention) ? input.attention : [];
  const limit =
    typeof input.maxAttentionItems === "number" && input.maxAttentionItems > 0
      ? Math.floor(input.maxAttentionItems)
      : MAX_CUSTOMER_ATTENTION_ITEMS;

  const matchedCustomer =
    requestedId !== ""
      ? customers.find((c) => c && cleanText(c.id) === requestedId) ?? null
      : null;

  const emptyAttentionText =
    "Chưa ghi nhận mục cần chú ý từ nguồn Attention hiện tại cho các lô đã liên kết mã khách hàng này. Trạng thái trống chỉ phản ánh dữ liệu hiện có — không phải xác nhận mọi lô đều hoàn tất hay không còn việc phát sinh.";
  const emptyConcentrationText =
    "Chưa có quy trình phát sinh hoặc cổng đang bị chặn trên các lô liên kết hiện tại.";

  if (!matchedCustomer) {
    return {
      classification: "READ_ONLY_CUSTOMER_PLAYBOOK_V1",
      readOnly: true,
      exactLinkRule: "shipment.customerId === customer.id",
      status: "NOT_FOUND",
      requestedId,
      customer: null,
      coverage: {
        exactLinkedShipmentCount: 0,
        note: "Chỉ tổng hợp các lô có liên kết chính xác mã khách hàng (shipment.customerId === customer.id).",
      },
      attention: {
        items: [],
        visibleItems: [],
        totalCount: 0,
        blockingCount: 0,
        overdueCount: 0,
        dueSoonCount: 0,
        actionCount: 0,
        unknownCount: 0,
        truncated: false,
        emptyText: emptyAttentionText,
      },
      linkedShipments: [],
      concentration: {
        modules: [],
        gates: [],
        hasConcentrationFacts: false,
        emptyText: emptyConcentrationText,
      },
    };
  }

  const canonicalId = cleanText(matchedCustomer.id);
  const rawNote = typeof matchedCustomer.note === "string" ? matchedCustomer.note.trim() : "";
  const customerIdentity: CustomerPlaybookIdentity = {
    id: canonicalId,
    name: cleanText(matchedCustomer.name),
    taxCode: cleanText(matchedCustomer.taxCode || matchedCustomer.mst),
    contactPerson: cleanText(matchedCustomer.contactPerson),
    phone: cleanText(matchedCustomer.phone),
    email: cleanText(matchedCustomer.email),
    address: cleanText(matchedCustomer.address),
    note: rawNote,
    hasOperatingNote: rawNote.length > 0,
    operatingNoteLabel: "Ghi chú vận hành",
    operatingNoteEmptyText: "Chưa ghi nhận ghi chú vận hành.",
    masterEditHref: customerMasterFilterPath(canonicalId),
    masterListHref: "/khach-hang",
  };

  // Exact customerId linkage ONLY. Never fallback to name, MST, phone, or email.
  const exactShipments = shipments.filter(
    (s) => Boolean(s) && cleanText(s.id) !== "" && s.customerId === canonicalId
  );
  const linkedShipmentIds = new Set(exactShipments.map((s) => cleanText(s.id)));

  // Preserve shared Attention order and item fields verbatim for linked shipments.
  const customerAttention = attentionList
    .filter((item) => Boolean(item) && linkedShipmentIds.has(cleanText(item.shipmentId)))
    .map((item) => ({
      ...item,
      unknown: Boolean(item.unknown),
    }));

  const shipmentRows: CustomerPlaybookShipmentRow[] = exactShipments.map((s) => {
    const sid = cleanText(s.id);
    const { currentStageId, position, positionNote } = resolveJourneyPosition(s);
    const primaryActionText =
      cleanText(s.journey?.primaryAction?.text) || cleanText(s.nextAction);
    const primaryActionDetail =
      cleanText(s.journey?.primaryAction?.detail) || cleanText(s.nextActionDetail);
    const primaryActionRoute =
      cleanText(s.journey?.primaryAction?.route) ||
      cleanText(s.nextRoute) ||
      shipmentPath(sid);
    const modules = Array.isArray(s.journey?.modules) ? s.journey.modules : [];
    const unknownModuleCount = modules.filter(
      (m) => normalizeModuleStatus(m?.status, m?.unresolved) === "UNKNOWN"
    ).length;

    return {
      id: sid,
      customerId: canonicalId,
      status: cleanText(s.status) || "—",
      statusTone: s.statusTone || "gray",
      route: cleanText(s.route),
      journeyCurrentStageId: currentStageId,
      journeyPosition: position,
      journeyPositionNote: positionNote,
      primaryAction: primaryActionText,
      primaryActionDetail,
      primaryActionRoute,
      openHref: shipmentPath(sid),
      moduleCount: modules.length,
      unknownModuleCount,
    };
  });

  // Factual Work Module and canonical blocked-gate concentration across linked shipments.
  const moduleMap = new Map<
    string,
    {
      key: string;
      templateId: string;
      label: string;
      instanceCount: number;
      shipmentSet: Set<string>;
      blockingCount: number;
      waitingCount: number;
      doneCount: number;
      unknownCount: number;
      gateSet: Set<string>;
    }
  >();

  const gateMap = new Map<
    string,
    {
      key: string;
      label: string;
      count: number;
      shipmentSet: Set<string>;
      moduleSet: Set<string>;
    }
  >();

  const seenModuleSourceRefs = new Set<string>();
  const seenGateBlockingRefs = new Set<string>();

  const recordModuleFact = (params: {
    shipmentId: string;
    templateId: string;
    label: string;
    status: "DONE" | "WAITING" | "BLOCKING" | "UNKNOWN";
    blockedGate: string;
    sourceRef?: string;
  }) => {
    const key = params.templateId || params.label || "UNKNOWN";
    const label = params.label || params.templateId || "UNKNOWN";
    if (params.sourceRef) {
      seenModuleSourceRefs.add(params.sourceRef);
    }
    let group = moduleMap.get(key);
    if (!group) {
      group = {
        key,
        templateId: key,
        label,
        instanceCount: 0,
        shipmentSet: new Set<string>(),
        blockingCount: 0,
        waitingCount: 0,
        doneCount: 0,
        unknownCount: 0,
        gateSet: new Set<string>(),
      };
      moduleMap.set(key, group);
    }
    group.instanceCount += 1;
    group.shipmentSet.add(params.shipmentId);
    if (params.status === "BLOCKING") {
      group.blockingCount += 1;
      if (params.blockedGate) {
        group.gateSet.add(params.blockedGate);
      }
    } else if (params.status === "WAITING") {
      group.waitingCount += 1;
    } else if (params.status === "DONE") {
      group.doneCount += 1;
    } else {
      group.unknownCount += 1;
    }
  };

  const recordBlockedGateFact = (params: {
    shipmentId: string;
    gate: string;
    moduleLabel?: string;
    dedupRef?: string;
  }) => {
    const gate = cleanText(params.gate);
    if (!gate) return;
    if (params.dedupRef) {
      if (seenGateBlockingRefs.has(params.dedupRef)) return;
      seenGateBlockingRefs.add(params.dedupRef);
    }
    let group = gateMap.get(gate);
    if (!group) {
      group = {
        key: gate,
        label: gate,
        count: 0,
        shipmentSet: new Set<string>(),
        moduleSet: new Set<string>(),
      };
      gateMap.set(gate, group);
    }
    group.count += 1;
    group.shipmentSet.add(params.shipmentId);
    const modLabel = cleanText(params.moduleLabel);
    if (modLabel) {
      group.moduleSet.add(modLabel);
    }
  };

  for (const s of exactShipments) {
    const sid = cleanText(s.id);
    const modules = Array.isArray(s.journey?.modules) ? s.journey.modules : [];
    for (let idx = 0; idx < modules.length; idx += 1) {
      const m = modules[idx];
      if (!m) continue;
      const instanceId = cleanText(m.instanceId) || `IDX-${idx}`;
      const templateId = cleanText(m.templateId) || cleanText(m.name) || "UNKNOWN";
      const label = cleanText(m.name) || templateId;
      const status = normalizeModuleStatus(m.status, m.unresolved);
      const rawGate = cleanText(m.gate?.label || m.gate?.stage);
      const canonicalBlockedGate = status === "BLOCKING" ? rawGate : "";
      const sourceRef = `MODULE:${sid}:${instanceId}`;

      recordModuleFact({
        shipmentId: sid,
        templateId,
        label,
        status,
        blockedGate: canonicalBlockedGate,
        sourceRef,
      });

      if (canonicalBlockedGate) {
        recordBlockedGateFact({
          shipmentId: sid,
          gate: canonicalBlockedGate,
          moduleLabel: label,
          dedupRef: sourceRef,
        });
      }
    }
  }

  for (const item of customerAttention) {
    const sid = cleanText(item.shipmentId);
    const sourceRef = cleanText(item.sourceRef) || cleanText(item.id);
    const blockedGate = cleanText(item.blockedGate);
    const isWorkModule = cleanText(item.sourceType) === "WORK_MODULE";
    const moduleTemplateId = cleanText(item.moduleTemplateId);
    const moduleName = cleanText(item.moduleName) || moduleTemplateId;

    if (
      isWorkModule &&
      (moduleTemplateId || moduleName || item.unknown) &&
      !seenModuleSourceRefs.has(sourceRef)
    ) {
      const status: "BLOCKING" | "WAITING" | "UNKNOWN" = item.unknown
        ? "UNKNOWN"
        : item.band === "BLOCKING"
          ? "BLOCKING"
          : "WAITING";
      recordModuleFact({
        shipmentId: sid,
        templateId: moduleTemplateId || moduleName || "UNKNOWN",
        label: moduleName || moduleTemplateId || "UNKNOWN",
        status,
        blockedGate: status === "BLOCKING" ? blockedGate : "",
        sourceRef,
      });
    }

    if (blockedGate) {
      recordBlockedGateFact({
        shipmentId: sid,
        gate: blockedGate,
        moduleLabel: moduleName,
        dedupRef: sourceRef,
      });
    }
  }

  const moduleGroups: CustomerPlaybookModuleGroup[] = Array.from(moduleMap.values())
    .map((g) => ({
      key: g.key,
      templateId: g.templateId,
      label: g.label,
      instanceCount: g.instanceCount,
      shipmentCount: g.shipmentSet.size,
      shipmentIds: Array.from(g.shipmentSet),
      blockingCount: g.blockingCount,
      waitingCount: g.waitingCount,
      doneCount: g.doneCount,
      unknownCount: g.unknownCount,
      blockedGates: Array.from(g.gateSet),
    }))
    .sort((a, b) => b.instanceCount - a.instanceCount || a.label.localeCompare(b.label));

  const gateGroups: CustomerPlaybookGateGroup[] = Array.from(gateMap.values())
    .map((g) => ({
      key: g.key,
      label: g.label,
      count: g.count,
      shipmentCount: g.shipmentSet.size,
      shipmentIds: Array.from(g.shipmentSet),
      moduleNames: Array.from(g.moduleSet),
    }))
    .sort((a, b) => b.count - a.count || a.label.localeCompare(b.label));

  return {
    classification: "READ_ONLY_CUSTOMER_PLAYBOOK_V1",
    readOnly: true,
    exactLinkRule: "shipment.customerId === customer.id",
    status: "FOUND",
    requestedId,
    customer: customerIdentity,
    coverage: {
      exactLinkedShipmentCount: shipmentRows.length,
      note: `Chỉ tổng hợp các lô có liên kết chính xác mã khách hàng (customerId = ${canonicalId}). Không tự động gán các lô chỉ trùng tên, MST, SĐT hoặc email.`,
    },
    attention: {
      items: customerAttention,
      visibleItems: customerAttention.slice(0, limit),
      totalCount: customerAttention.length,
      blockingCount: customerAttention.filter((i) => i.band === "BLOCKING").length,
      overdueCount: customerAttention.filter((i) => i.band === "OVERDUE").length,
      dueSoonCount: customerAttention.filter((i) => i.band === "DUE_SOON").length,
      actionCount: customerAttention.filter((i) => i.band === "ACTION").length,
      unknownCount: customerAttention.filter((i) => i.unknown).length,
      truncated: customerAttention.length > limit,
      emptyText: emptyAttentionText,
    },
    linkedShipments: shipmentRows,
    concentration: {
      modules: moduleGroups,
      gates: gateGroups,
      hasConcentrationFacts: moduleGroups.length > 0 || gateGroups.length > 0,
      emptyText: emptyConcentrationText,
    },
  };
}
