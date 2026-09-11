// ============================================================================
// The ONE bounded event dispatcher (React UI → Python view-model).
//
// Phase B allows exactly these typed event names; anything else is dropped
// locally and never reaches Python. No sibling-iframe communication, no
// postMessage bridge, no query-param bridge — this is the Streamlit
// Components v2 native `setTriggerValue` API.
//
// WRITE CONTRACT
// Every material event goes:
//   typed event → bounded dispatcher → current RBAC → existing writer/service
//   → audit → fresh backend read → refreshed view-model (route/tab retained).
// A local optimistic update is only ever a rendering aid; the authoritative
// value always comes back from the backend.
// ============================================================================

export type LogiEventName =
  | "shipment_update"
  | "navigate"
  | "shipment_field_save"
  | "delivery_confirm"
  | "finance_actual_save"
  | "payment_record"
  | "payment_correction"
  // C2B — single-partner payable slice (canonical financial ledger).
  | "partner_payable_record"
  | "partner_payment_record"
  | "shipment_create"
  | "pxk_generate"
  // Phase C1 — business-contracts slice (KHÁCH HÀNG → BÁO GIÁ → THỎA THUẬN →
  // HỢP ĐỒNG → HÀNG HÓA → HDNT/PL/HDMB → LINK SHIPMENT → DOWNLOAD/HISTORY).
  | "customer_create"
  | "customer_edit"
  | "customer_archive"
  | "customer_import"
  | "quote_create"
  | "quote_edit"
  | "quote_transition"
  | "agreement_create"
  | "agreement_edit"
  | "agreement_transition"
  | "contract_create"
  | "contract_save"
  | "contract_goods_save"
  | "contract_docgen_generate"
  | "contract_docgen_issue"
  | "contract_shipment_link"
  // LOGI_TARIFF_LOOKUP_01 — bounded READ-ONLY query event (no mutation):
  // records the /tra-cuu-thue lookup query; the authoritative result always
  // comes back from the existing canonical reader in the next fresh read.
  | "tariff_lookup";

const ALLOWED_EVENTS: ReadonlySet<string> = new Set<LogiEventName>([
  "shipment_update",
  "navigate",
  "shipment_field_save",
  "delivery_confirm",
  "finance_actual_save",
  "payment_record",
  "payment_correction",
  "partner_payable_record",
  "partner_payment_record",
  "shipment_create",
  "pxk_generate",
  "customer_create",
  "customer_edit",
  "customer_archive",
  "customer_import",
  "quote_create",
  "quote_edit",
  "quote_transition",
  "agreement_create",
  "agreement_edit",
  "agreement_transition",
  "contract_create",
  "contract_save",
  "contract_goods_save",
  "contract_docgen_generate",
  "contract_docgen_issue",
  "contract_shipment_link",
  "tariff_lookup",
]);

type Transport = (event: string, value: unknown) => void;

let transport: Transport | null = null;
let seq = 0;

/** Bind the v2 component transport (called once per component invocation). */
export function bindTransport(t: Transport | null): void {
  transport = t;
}

export function dispatchLogiEvent(
  event: LogiEventName,
  payload: unknown
): boolean {
  if (!transport || !ALLOWED_EVENTS.has(event)) return false;
  seq += 1;
  transport(event, { seq, event, payload });
  return true;
}

export function currentSeq(): number {
  return seq;
}
