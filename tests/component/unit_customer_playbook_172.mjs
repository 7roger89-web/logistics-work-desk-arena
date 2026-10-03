import assert from "node:assert/strict";
import { importTs } from "./lib_loader.mjs";

const { composeCustomerPlaybook, CUSTOMER_PLAYBOOK_ATTENTION_LIMIT } = await importTs("customerPlaybook.ts");

const moduleRollup = (overrides = {}) => ({
  instanceId: "WM-1",
  templateId: "QC-DEMO",
  templateVersion: 2,
  name: "QC demo",
  status: "WAITING",
  gate: { stage: "delivery", label: "DELIVERY", type: "BLOCKING" },
  ...overrides,
});
const shipment = (id, customerId, modules = [], extra = {}) => ({
  id,
  customerId,
  customer: "Same Customer Name",
  journey: { modules },
  ...extra,
});
const attentionItem = (id, shipmentId, overrides = {}) => ({
  id,
  shipmentId,
  sourceType: "TASK",
  sourceRef: `TASK:${id}`,
  band: "ACTION",
  reason: `Reason ${id}`,
  action: `Action ${id}`,
  context: "",
  route: `/lo-hang/${shipmentId}?tab=nhap&from=${id}`,
  owner: "",
  deadline: "",
  blockedGate: "",
  primary: false,
  provenance: "shared Attention",
  unknown: false,
  ...overrides,
});

const blockRoute = "/lo-hang/S-1?tab=nhap&stage=wm-WM-1-result&work=info";
const blockingAttention = attentionItem("ATT-BLOCK", "S-1", {
  band: "BLOCKING",
  reason: "Chặn DELIVERY — còn thiếu Result",
  action: "Result received",
  route: blockRoute,
  blockedGate: "DELIVERY",
});
const unknownAttention = attentionItem("ATT-UNKNOWN", "S-2", {
  band: "ACTION",
  unknown: true,
  reason: "Chưa xác định đủ dữ liệu",
  route: "/lo-hang/S-2?tab=nhap&stage=UNKNOWN",
});
const linkedShipments = [
  shipment("S-1", "C1", [
    moduleRollup({ instanceId: "WM-1", status: "BLOCKING", gateText: "Chặn DELIVERY" }),
    moduleRollup({
      instanceId: "WM-OLD",
      templateId: "OLD-VERSION",
      name: "OLD-VERSION",
      status: "UNKNOWN",
      gate: {},
      gateText: "",
    }),
  ]),
  shipment("S-2", "C1", [
    moduleRollup({ instanceId: "WM-2", status: "WAITING" }),
  ]),
  // Similar display name and tax/contact-like data are deliberately insufficient.
  shipment("S-NAME-ONLY", undefined, [
    moduleRollup({ instanceId: "WM-DECOY", status: "BLOCKING" }),
  ], { customer: "Same Customer Name", customerMST: "C1" }),
  shipment("S-OTHER", "C2", [moduleRollup({ instanceId: "WM-OTHER", status: "BLOCKING" })]),
];
const attention = [
  blockingAttention,
  attentionItem("ATT-NAME-ONLY", "S-NAME-ONLY", { band: "BLOCKING" }),
  unknownAttention,
  attentionItem("ATT-3", "S-1"),
  attentionItem("ATT-4", "S-2"),
  attentionItem("ATT-5", "S-1"),
  attentionItem("ATT-6", "S-2"),
  attentionItem("ATT-7", "S-1"),
];

const projection = composeCustomerPlaybook({ id: "C1" }, linkedShipments, attention);

// Exact identity only: no customer-name/MST fallback for an unlinked shipment.
assert.deepEqual(projection.linkedShipments.map((row) => row.id), ["S-1", "S-2"]);
assert.ok(!projection.linkedShipments.some((row) => row.id === "S-NAME-ONLY"));
assert.ok(!projection.linkedShipments.some((row) => row.id === "S-OTHER"));

// Attention is a subset of the existing ordered projection; fields and the
// canonical drill-down route are passed through without remapping.
assert.equal(projection.attentionTotalCount, 7);
assert.equal(projection.attention.length, CUSTOMER_PLAYBOOK_ATTENTION_LIMIT);
assert.deepEqual(projection.attention.map((row) => row.id), [
  "ATT-BLOCK", "ATT-UNKNOWN", "ATT-3", "ATT-4", "ATT-5",
]);
assert.equal(projection.attention[0].band, "BLOCKING");
assert.equal(projection.attention[0].reason, "Chặn DELIVERY — còn thiếu Result");
assert.equal(projection.attention[0].route, blockRoute);
assert.equal(projection.attention[1].unknown, true);
assert.equal(projection.attention[1].band, "ACTION");

// Factual Work Module grouping counts attached rollups and unique linked lots.
const qc = projection.moduleGroups.find((group) => group.templateId === "QC-DEMO");
assert.ok(qc);
assert.equal(qc.name, "QC demo");
assert.equal(qc.templateVersion, 2);
assert.equal(qc.moduleCount, 2);
assert.equal(qc.shipmentCount, 2);

// UNKNOWN remains explicitly unknown and cannot create a blocked-gate group.
const unknown = projection.moduleGroups.find((group) => group.templateId === "OLD-VERSION");
assert.ok(unknown);
assert.equal(unknown.unknownCount, 1);
assert.deepEqual(projection.blockedGates.map((group) => group.label), ["DELIVERY"]);
assert.equal(projection.blockedGates[0].moduleCount, 1);
assert.equal(projection.blockedGates[0].shipmentCount, 1);

// No supported Attention is a neutral empty result, not a health/safety claim.
const noAttention = composeCustomerPlaybook({ id: "C1" }, linkedShipments, []);
assert.deepEqual(noAttention.attention, []);
assert.equal(noAttention.attentionTotalCount, 0);

// The helper's output is a read-only composition, not a score or advice model.
assert.deepEqual(Object.keys(projection), [
  "linkedShipments", "attention", "attentionTotalCount", "moduleGroups", "blockedGates",
]);
assert.equal("riskScore" in projection, false);
assert.equal("recommendations" in projection, false);
assert.equal("customerPreference" in projection, false);

console.log("PASS #172 unit: exact customerId only, shared Attention order/routes, neutral empty, UNKNOWN, factual module/gate groups, no score/recommendation fields");
