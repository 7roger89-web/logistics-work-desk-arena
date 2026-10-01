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
  // LOGI_CONTRACT_AND_SHIPMENT_CORE_GAPS_01 — the customer half of a lot's
  // name ("tên lô hàng" = mã lô + khách hàng) through the EXISTING canonical
  // writer core.database.update_shipment_customer. The lot code itself stays
  // read-only here: core.database.rename_shipment_id does not re-point
  // contracts.shipment_ids, so exposing it would silently break links.
  | "shipment_customer_save"
  | "shipment_transport_save"
  | "shipment_sea_facts_save"
  // LOGI_SHIPMENT_EXECUTION_PROFILE_01 — ONE bounded write for the shipment
  // execution profile (Incoterms code + version + named place, Trường Thành
  // service scope, load model, actual cargo insurance). It writes the EXISTING
  // `mode` / `incoterm` shipment paths plus one profile block, through the
  // existing atomic writer, with RBAC → audit → fresh readback.
  | "shipment_profile_save"
  // LOGI_SHIPMENT_DOCUMENT_WORKFLOW_01 — ONE bounded write for the
  // operator-confirmed commercial/import model: typed event → this bounded
  // dispatcher → shipment_edit RBAC → the existing atomic shipment writer →
  // audit → fresh readback (same contract as shipment_profile_save).
  | "shipment_commercial_flow_save"
  | "delivery_confirm"
  | "finance_actual_save"
  | "payment_record"
  | "payment_correction"
  // C2B — single-partner payable slice (canonical financial ledger).
  | "partner_payable_record"
  | "partner_payment_record"
  | "shipment_create"
  | "pxk_generate"
  | "gnt_generate"
  // LOGI_GETFLY_DSDH_IMPORT_PARITY_01 — real XLSX preview then explicit
  // commit. The browser sends bytes only for preview; commit references the
  // server-issued previewId and operator VAT choices.
  | "getfly_preview"
  | "getfly_import"
  // Phase C1 — business-contracts slice (KHÁCH HÀNG → BÁO GIÁ → THỎA THUẬN →
  // HỢP ĐỒNG → HÀNG HÓA → HDNT/PL/HDMB → LINK SHIPMENT → DOWNLOAD/HISTORY).
  | "customer_create"
  | "customer_edit"
  | "customer_archive"
  | "customer_import"
  // LOGI_CONTRACT_AND_SHIPMENT_CORE_GAPS_01 — paste a GetFly DSDH block in the
  // contract flow and take ONLY the customer identity it really carries
  // (Tên KH / Mã KH). Python parses it with core.getfly_reader's own column
  // keywords and hands the rows to the EXISTING customer_import writer: one
  // importer, one canonical writer, no invented contract/MST/company data.
  | "customer_getfly_import"
  | "quote_create"
  | "quote_edit"
  | "quote_transition"
  // LOGI_QUOTE_COST_WORKFLOW_UX_01 — ONE bounded READ-ONLY export event: the
  // server re-reads the canonical quote, renders the customer quotation XLSX
  // with the EXISTING core.excel_utils.generate_quote_excel and returns the
  // bytes on the SAME lastWrites channel PXK/GNT/attachment downloads use.
  // No mutation, no second exporter, no API server.
  | "quote_export_xlsx"
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
  // LOGI_REAL_USE_CREATE_SHIPMENT_AGENT_MASTER_01 — ONE bounded write event for
  // the "Đại Lý Trường Thành" agent master (authority_agents): CREATE or EDIT
  // through the EXISTING canonical writer core.database.save_authority_agent
  // (sales_write RBAC → upsert → audit → fresh readback). No new collection.
  | "authority_agent_save"
  // LOGI_RECONCILIATION_DESK_01 — bounded READ-ONLY filter event for
  // /tai-chinh/doi-soat. It mutates nothing: Python records only WHICH slice of
  // the existing canonical projection was asked for (query / currency / state /
  // side) and re-derives every amount, match state and currency total from
  // core.financial_ledger on the next fresh read. There is deliberately no
  // reconcile/write event: recording a payable or a payment stays on the
  // canonical C2B/C2D and C2C surfaces this desk links to.
  | "reconciliation_filter"
  // LOGI_USER_MANAGEMENT_01 — the bounded Admin write path for /nguoi-dung.
  // Every event is re-checked Admin-only server-side (core.auth.
  // can_operate_business("*")), reuses the EXISTING core.users transforms +
  // core.database writers, and returns its outcome via the same lastWrites
  // pattern every other write uses. No delete event exists.
  | "user_create"
  | "user_role_set"
  | "user_active_set"
  | "user_password_reset"
  | "notebooklm_registry_save"
  | "tariff_source_upload"
  // LOGI_SHIPMENT_DOCUMENTS_DRIVE_REINTEGRATE_02 — the bounded attachment pair
  // for the shipment "Chứng từ" tab. The upload event carries the ONE chosen
  // file as bounded base64 (the same transport the GetFly preview already uses)
  // and the server owns permission, validation, compression, the Drive upload
  // and the metadata write; the download event re-reads ONE stored file from
  // Drive server-side so no Drive id, folder id or token ever reaches the
  // browser. There is deliberately NO delete event.
  | "shipment_attachment_upload"
  | "attachment_download"
  // LOGI_TRADE_DOCUMENT_SHIPMENT_REVIEW_RUN3_01 — ONE bounded READ-ONLY event
  // for the shipment "Chứng từ / Tệp đính kèm" review surface. The payload
  // carries ONLY bounded identifiers ({ shipmentId, attachmentIds, requestId }):
  // never file bytes, never base64, never a storage/GridFS/Drive id, never a raw
  // SHA, never a credential. The server reads the selected files itself through
  // the EXISTING core.shipment_attachments.fetch_attachment_bytes after proving
  // ownership, runs the Run 2 reader + Run 1 cross-check, and keeps ONE
  // ephemeral session result. It is NOT a Phase-B business mutation: nothing is
  // written to the shipment, to shipment_attachments or to an audit log.
  | "shipment_document_review"
  // LOGI_CONTRACT_INTL_PAYMENT_COMPARATOR_01 — immutable payment snapshot
  | "contract_intl_snapshot_save"
  | "contract_payment_snapshot_save"
  // LOGI_COST_INTELLIGENCE_01 — bounded rate inbox + dynamic catalog.
  | "cost_rate_parse"
  | "cost_rate_save"
  | "cost_rate_status_set"
  | "cost_catalog_save"
  // LOGI_FREIGHTOS_MARKET_BENCHMARK_CANARY_01 — read-only marketplace estimate.
  | "cost_market_benchmark_fetch";

const ALLOWED_EVENTS: ReadonlySet<string> = new Set<LogiEventName>([
  "shipment_update",
  "navigate",
  "shipment_field_save",
  "shipment_customer_save",
  "shipment_transport_save",
  "shipment_sea_facts_save",
  "shipment_profile_save",
  "shipment_commercial_flow_save",
  "delivery_confirm",
  "finance_actual_save",
  "payment_record",
  "payment_correction",
  "partner_payable_record",
  "partner_payment_record",
  "shipment_create",
  "pxk_generate",
  "gnt_generate",
  "getfly_preview",
  "getfly_import",
  "customer_create",
  "customer_edit",
  "customer_archive",
  "customer_import",
  "customer_getfly_import",
  "quote_create",
  "quote_edit",
  "quote_transition",
  "quote_export_xlsx",
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
  "authority_agent_save",
  "reconciliation_filter",
  "user_create",
  "user_role_set",
  "user_active_set",
  "user_password_reset",
  "notebooklm_registry_save",
  "tariff_source_upload",
  "shipment_attachment_upload",
  "attachment_download",
  "shipment_document_review",
  "contract_intl_snapshot_save",
  "contract_payment_snapshot_save",
  "cost_rate_parse",
  "cost_rate_save",
  "cost_rate_status_set",
  "cost_catalog_save",
  "cost_market_benchmark_fetch",
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
