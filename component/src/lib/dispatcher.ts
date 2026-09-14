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
  | "shipment_transport_save"
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
  | "tariff_lookup"
  // LOGI_TRANSLATION_WORKSPACE_01 — ONE bounded translation intent for
  // /dich-thuat. Not a business mutation (no document/ledger/shipment write):
  // Python performs ONE call through the EXISTING canonical DeepL client and
  // returns the readback in the next fresh view-model.
  | "translate_text"
  // LOGI_PARTNER_CONTEXT_WORKSPACE_01 — bounded READ-ONLY selection event for
  // /ngu-canh-doi-tac. It mutates nothing: Python records only WHICH existing
  // entity was picked and re-derives the whole context from the authoritative
  // readers (entity_context / authority_agents / C2D ledger) on the next read.
  | "partner_context_select"
  // LOGI_RECONCILIATION_DESK_01 — bounded READ-ONLY filter event for
  // /tai-chinh/doi-soat. It mutates nothing: Python records only WHICH slice of
  // the existing canonical projection was asked for (query / currency / state /
  // side) and re-derives every amount, match state and currency total from
  // core.financial_ledger on the next fresh read. There is deliberately no
  // reconcile/write event: recording a payable or a payment stays on the
  // canonical C2B/C2D and C2C surfaces this desk links to.
  | "reconciliation_filter";

const ALLOWED_EVENTS: ReadonlySet<string> = new Set<LogiEventName>([
  "shipment_update",
  "navigate",
  "shipment_field_save",
  "shipment_transport_save",
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
  "translate_text",
  "partner_context_select",
  "reconciliation_filter",
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
