import type { AttentionItem, Customer, Shipment } from "./viewmodel";

/** Keep the customer hero bounded like the existing shipment Attention surface. */
export const CUSTOMER_PLAYBOOK_ATTENTION_LIMIT = 5;

export interface CustomerModuleGroup {
  key: string;
  templateId: string;
  templateVersion: number;
  name: string;
  moduleCount: number;
  shipmentCount: number;
  unknownCount: number;
}

export interface CustomerBlockedGateGroup {
  key: string;
  label: string;
  moduleCount: number;
  shipmentCount: number;
}

export interface CustomerPlaybookProjection {
  /** Only shipments with the exact canonical customerId are present. */
  linkedShipments: Shipment[];
  /** A stable prefix of the shared Attention order, with its source routes intact. */
  attention: AttentionItem[];
  attentionTotalCount: number;
  moduleGroups: CustomerModuleGroup[];
  blockedGates: CustomerBlockedGateGroup[];
}

/**
 * Compose the read-only customer surface from existing ViewModel truth.
 *
 * This deliberately has no name/tax/contact fallback, second attention rule,
 * customer score, or recommendation output. Module/gate counts describe only
 * attached rollups on exact-linked shipments; UNKNOWN remains an explicit
 * count and is never promoted to a completed or blocked state.
 */
export function composeCustomerPlaybook(
  customer: Pick<Customer, "id">,
  shipments: readonly Shipment[],
  attention: readonly AttentionItem[],
): CustomerPlaybookProjection {
  const linkedShipments = shipments.filter(
    (shipment) => shipment.customerId === customer.id,
  );
  const linkedShipmentIds = new Set(linkedShipments.map((shipment) => shipment.id));
  const linkedAttention = attention.filter((item) => linkedShipmentIds.has(item.shipmentId));

  const moduleGroups = new Map<string, CustomerModuleGroup & { shipmentIds: Set<string> }>();
  const blockedGates = new Map<string, CustomerBlockedGateGroup & { shipmentIds: Set<string> }>();

  for (const shipment of linkedShipments) {
    const modules = shipment.journey?.modules ?? [];
    modules.forEach((module, index) => {
      const templateId = (module.templateId ?? "").trim();
      const moduleName = (module.name ?? "").trim();
      const instanceId = (module.instanceId ?? "").trim();
      const identity = templateId
        ? `template:${templateId}`
        : moduleName
          ? `name:${moduleName}`
          : `instance:${instanceId || `${shipment.id}:${index}`}`;
      const key = JSON.stringify([identity, module.templateVersion]);
      let group = moduleGroups.get(key);
      if (!group) {
        group = {
          key,
          templateId,
          templateVersion: module.templateVersion,
          name: moduleName || templateId || "Chưa xác định tên quy trình",
          moduleCount: 0,
          shipmentCount: 0,
          unknownCount: 0,
          shipmentIds: new Set<string>(),
        };
        moduleGroups.set(key, group);
      }
      group.moduleCount += 1;
      group.shipmentIds.add(shipment.id);
      if (module.status === "UNKNOWN") group.unknownCount += 1;

      // A gate is shown as blocked only when the existing Work Module rollup
      // itself says BLOCKING and carries a canonical gate label/stage.
      if (module.status !== "BLOCKING") return;
      const stage = (module.gate?.stage ?? "").trim();
      const label = (module.gate?.label ?? "").trim() || stage;
      if (!label) return;

      const gateKey = JSON.stringify([stage || label, label]);
      let gateGroup = blockedGates.get(gateKey);
      if (!gateGroup) {
        gateGroup = {
          key: gateKey,
          label,
          moduleCount: 0,
          shipmentCount: 0,
          shipmentIds: new Set<string>(),
        };
        blockedGates.set(gateKey, gateGroup);
      }
      gateGroup.moduleCount += 1;
      gateGroup.shipmentIds.add(shipment.id);
    });
  }

  return {
    linkedShipments,
    attention: linkedAttention.slice(0, CUSTOMER_PLAYBOOK_ATTENTION_LIMIT),
    attentionTotalCount: linkedAttention.length,
    moduleGroups: [...moduleGroups.values()].map(({ shipmentIds, ...group }) => ({
      ...group,
      shipmentCount: shipmentIds.size,
    })),
    blockedGates: [...blockedGates.values()].map(({ shipmentIds, ...group }) => ({
      ...group,
      shipmentCount: shipmentIds.size,
    })),
  };
}
