// ============================================================================
// View-model contract — LOGI-GOOD / Logistics Work Desk (Phase B)
//
// Typed contract for data that flows:
//   Python Logistics view-model (views/logi_real_data.py, over the CURRENT
//   Logistics readers) → Streamlit Components v2 `data` channel
//   → this module (applyViewModel) → React store / lib-data live arrays.
//
// Phase B changed the DATA SOURCE and the business actions. The visible donor
// UI is frozen, so the page-level field names are unchanged.
//
// UNKNOWN != ZERO
// ---------------
// A numeric the real Logistics model does not carry arrives as `null` and is
// rendered as an explicit "—". It is never coerced to 0, because for tax, VAT,
// pack count, weight, CBM, cost, Finance Actual, AR/AP and payments a blank is
// a statement about knowledge, not about money.
// ============================================================================

export type Tone = "green" | "amber" | "red" | "blue" | "gray";
export type Role = "ADMIN" | "SUPPORT" | "SALE" | "VIEWER" | string;
export type Priority = "Khan" | "CanXuLy" | "BinhThuong";
/** A real number, or null when the backend genuinely does not know it. */
export type MaybeNum = number | null;

export interface TimelineEntry {
  time: string;
  title: string;
  desc?: string;
  tone: "green" | "amber" | "red" | "blue";
}

export interface ShipmentDoc {
  name: string;
  ok: boolean;
  note?: string;
}

/**
 * LOGI_SHIPMENT_DOCUMENTS_DRIVE_REINTEGRATE_02 — ONE real attachment of a lot,
 * projected by the backend from the canonical attachment METADATA. Google Drive
 * holds the bytes, so this shape deliberately carries NO Drive file id, folder
 * id, raw SHA-256 or credential: only what the operator may see, plus (for the
 * single attachment just requested) the server-read base64 body used to save
 * the file.
 */
export interface ShipmentAttachment {
  id: string;
  name: string;
  category: string;
  categoryLabel: string;
  mime: string;
  originalSize: number;
  storedSize: number;
  /** Honest size text: "1.8 MB → 620 KB" only when the bytes really shrank. */
  sizeLabel: string;
  compressionMode: string;
  /** "Ảnh đã tối ưu" or "Giữ nguyên" — never a fake claim. */
  compressionLabel: string;
  compressionNote?: string;
  uploadedAt: string;
  uploadedBy: string;
  status: string;
  downloadAvailable: boolean;
  downloadBase64?: string | null;
  /** Increments on every backend download read, so the UI saves each new one. */
  downloadSeq?: number | null;
}

export interface AttachmentCategory {
  id: string;
  label: string;
}

/** Server-enforced attachment policy (the form never invents its own limits). */
export interface AttachmentPolicy {
  allowUpload: boolean;
  categories: AttachmentCategory[];
  allowedExtensions: string[];
  accept: string;
  maxUploadBytes: number;
  maxUploadLabel: string;
  driveConfigured: boolean;
}

export interface MoneyLine {
  label: string;
  amount: MaybeNum;
  ccy: string;
  /** QUOTE ESTIMATE and FINANCE ACTUAL are distinct objects server-side. */
  kind?: "quote" | "actual";
  cost?: MaybeNum;
  qty?: MaybeNum;
  vat?: MaybeNum;
}

/**
 * LOGI_FINANCE_ACTUAL_ENTRY_PARITY_01 — one booked Finance Actual service line.
 *
 * Every field is the canonical field of ``data["3.4"].details`` re-shaped for
 * display by ``views.logi_real_data.finance_projection`` — nothing here is
 * computed in the browser:
 *   id      canonical line id; sending it back on save UPDATES that row
 *   name    ``name_full`` (``label`` stays the display fallback)
 *   code    the service code (blank on a legacy row that never had one)
 *   unit    ``Lần`` / ``Cont`` … (blank when the stored row never said)
 *   qty / price / cost / vat / note  the operator-keyed facts
 * A field the document does not carry arrives as null/"" and renders as "—";
 * it is never filled with a fabricated 0 or a guessed service code.
 */
export interface FinanceActualLine extends MoneyLine {
  id: string;
  name: string;
  code: string;
  unit: string;
  note: string;
  /** Sell price — the same figure ``amount`` carries, named for the editor. */
  price: MaybeNum;
}

/**
 * One entry of the ONE canonical service catalog
 * (``core.config.GETFLY_SERVICES_LIST``), projected read-only by the backend
 * through ``views.logi_real_data.finance_service_catalog``. The component owns
 * no copy of this list: picking an entry only pre-fills the service line the
 * operator then books.
 */
export interface FinanceServiceCatalogEntry {
  code: string;
  name: string;
  unit: string;
  group: string;
}

export interface Payment {
  id?: string;
  requestId?: string;
  date: string;
  kind: string;
  amount: MaybeNum;
  ccy: string;
  by: string;
  note?: string;
  reversed?: boolean;
}

export interface Pickup {
  factory: string;
  address: string;
  contact: string;
  phone: string;
  pickupTime: string;
  truckType: string;
  plate: string;
  driver: string;
  driverPhone: string;
  eta: string;
  ata: string;
}

export interface Transport {
  bookingNo: string;
  carrier: string;
  mbl: string;
  hbl: string;
  vessel: string;
  etd: string;
  pol: string;
  pod: string;
  containerNo: string;
  qtyPkg: string;
}

export type TransportMode = "Truck" | "Sea" | "Air" | "Rail";

export interface TransportUnit {
  id: string;
  kind: "truck" | "container";
  number: string;
  typeSize: string;
  sealNo: string;
  driverName: string;
  driverPhone: string;
}

export interface TransportLeg {
  id: string;
  sequence: number;
  mode: TransportMode;
  origin: string;
  destination: string;
  carrier: string;
  etd: string;
  eta: string;
  atd: string;
  ata: string;
  bookingNo: string;
  mbl: string;
  hbl: string;
  vessel: string;
  voyage: string;
  mawb: string;
  hawb: string;
  flightNo: string;
  units: TransportUnit[];
}

export interface Cargo {
  goodsDescription: string;
  packs: MaybeNum;
  weight: MaybeNum;
  cbm: MaybeNum;
  dims: string;
  type: string;
  note?: string;
  qtyPkg?: string;
}

export interface ExportInfo {
  border: string;
  declarant: string;
  eta: string;
  ata: string;
  state: string;
  chinaDeclNo?: string;
}

export interface GntDocInfo {
  fileName: string;
  mime: string;
  generatedAt?: string;
  generatedBy?: string;
  downloadAvailable: boolean;
  downloadBase64?: string | null;
}

export interface GntInfo {
  payer: string;
  taxCode: string;
  address: string;
  customsOffice: string;
  customerHint?: string;
  customerTaxHint?: string;
  ready?: boolean;
  noPayable?: boolean;
  missing?: string[];
  done?: boolean;
  document?: GntDocInfo | null;
}

export interface ImportInfo {
  borderVN: string;
  declarationNo: string;
  regDate: string;
  clearDate?: string;
  /**
   * ACTUAL import duty / import VAT in VND (LOGI_GNT_CANONICAL_FIELDS_01,
   * Owner-approved 2026-09-12). Recorded by the operator from the real customs
   * notice or GNT — never calculated, never inferred from a rate or HS code.
   * Still null (renders "—") until an operator records them: a blank is a
   * statement about knowledge, not about money.
   */
  tax: MaybeNum;
  vat: MaybeNum;
  inspection: string;
  customsStatus?: boolean;
  license: string;
  gnt?: GntInfo;
  arrivalDate?: string;
  freeTime?: MaybeNum;
  truckVN: string;
  plateVN: string;
  driverVN: string;
  schedule: string;
  deliveryAddr: string;
  receiver: string;
  receiverPhone: string;
  receiverTitle?: string;
  deliveryLocation?: string;
  delivered: boolean;
  actualDelivery?: string;
}

export interface PartnerPaymentRow {
  id: string;
  requestId: string;
  date: string;
  kind: string;
  amount: MaybeNum;
  ccy: string;
  allocated?: MaybeNum;
  unallocated?: MaybeNum;
  note?: string;
}

/**
 * C2B — partner payable truth for THIS shipment, derived by the backend from
 * the canonical ledger. Every money figure is UNKNOWN (null) until a canonical
 * obligation/payment record exists — null is never rendered as 0.
 */
export interface PartnerFinance {
  partnerId: string | null;
  partnerName: string | null;
  /** True when partnerId is only a catalog suggestion (no ledger rows yet). */
  suggested?: boolean;
  status?: string;
  payable: MaybeNum;
  paid: MaybeNum;
  remaining: MaybeNum;
  currency?: string | null;
  payments: PartnerPaymentRow[];
}

export interface Finance {
  quote: MoneyLine[];
  /** Booked actual service lines — the canonical editor rows, see above. */
  actual: FinanceActualLine[];
  currency?: string;
  /** True when at least one actual service line is booked. Without one,
   *  actual revenue/cost/profit are UNKNOWN — never a manufactured 0. */
  hasActualLines?: boolean;
  receivable: MaybeNum;
  received: MaybeNum;
  receivableNet?: MaybeNum;
  outputVat?: MaybeNum;
  outstanding?: MaybeNum;
  payable: MaybeNum;
  /** No supplier-payment ledger on the shipment — null, never 0. */
  paid: MaybeNum;
  commission?: MaybeNum;
  profit?: MaybeNum;
  /** profit / revenue_net * 100 — UNKNOWN unless both are known. */
  profitMargin?: MaybeNum;
  payments: Payment[];
  /** Canonical partner payable block (C2B) — see PartnerFinance. */
  partner?: PartnerFinance;
  source?: string;
}

/**
 * One PXK that core.docgen really generated for the lot: metadata from the
 * canonical ``docgen_documents`` collection plus the file kept on the session
 * download store (bytes are session-scoped by design, metadata is durable).
 */
export interface PxkDocument {
  documentId?: string;
  recordId?: string;
  revision?: number;
  status?: string;
  fileName?: string;
  mime?: string;
  generatedAt?: string;
  generatedBy?: string;
  downloadAvailable?: boolean;
  downloadBase64?: string | null;
  number?: string;
  date?: string;
}

export interface Pxk {
  source?: string;
  sourceName?: string;
  delivered?: boolean;
  /** The real core.docgen delivery gate. */
  gateOpen?: boolean;
  missingDeliveryFacts?: string[];
  number?: string;
  date?: string;
  place?: string;
  receiver?: string;
  role?: string;
  done?: boolean;
  /** null while nothing has been generated — never a fabricated document. */
  document?: PxkDocument | null;
}

export interface OpsAlert {
  code: string;
  severity: string;
  title: string;
  message: string;
}

export interface Ops {
  financialFlag: string;
  financialLabel: string;
  alerts: OpsAlert[];
  arrivalDateLabel?: string;
  freeTimeExpiryLabel?: string;
  daysRemaining?: number | null;
}

export interface TrackingMilestone {
  time: string;
  title: string;
  desc: string;
  done: boolean;
  tone: "green" | "amber" | "red" | "blue";
}

export interface Tracking {
  status: string;
  statusTone: Tone;
  carrier: string;
  reference: string;
  trackingUrl: string;
  /** Never fabricated: the model has no live GPS feed. */
  hasLivePosition: boolean;
  positionNote: string;
  milestones: TrackingMilestone[];
}

export interface Shipment {
  id: string;
  customer: string;
  customerMST: string;
  customerId?: string;
  contract: string;
  route: string;
  borderVN: string;
  sale: string;
  support: string;
  status: string;
  statusTone: Tone;
  priority?: Priority;
  nextAction: string;
  nextActionDetail?: string;
  nextLabel?: string;
  nextRoute: string;
  updated: string;
  missingDocs: string[];
  docs: ShipmentDoc[];
  /** Real attachments of the lot (metadata only; bytes live in Google Drive). */
  attachments: ShipmentAttachment[];
  version?: number;
  rawStatus?: string;
  mode?: string;
  incoterm?: string;
  createdAt?: string;
  /** Ordered canonical legs, or a legacy read projection until explicitly saved. */
  transportLegs: TransportLeg[];
  transportLegsStructured: boolean;
  cargoStructured: boolean;
  pickup: Pickup;
  transport?: Transport;
  cargo: Cargo;
  exportInfo: ExportInfo;
  importInfo: ImportInfo;
  finance: Finance;
  pxk: Pxk;
  timeline: TimelineEntry[];
  ops?: Ops;
  tracking?: Tracking;
}

export interface Task {
  id: string;
  level: Priority;
  lot: string;
  customer: string;
  job: string;
  assignee: string;
  due: string;
  dueNote: string;
  status: string;
  statusTone: Tone;
  route: string;
  source?: string;
}

export interface Customer {
  id: string;
  name: string;
  short: string;
  mst: string;
  phone: string;
  email: string;
  contactPerson: string;
  taxCode: string;
  address: string;
  note: string;
}

export interface QuoteServiceLine {
  code: string;
  serviceName: string;
  unit: string;
  qty: MaybeNum;
  currency: string;
  costUnit: MaybeNum;
  sellUnit: MaybeNum;
  taxPct: MaybeNum;
  costTotal: MaybeNum;
  sellTotal: MaybeNum;
  costVnd: MaybeNum;
  sellVnd: MaybeNum;
}

export interface Quote {
  id: string;
  quoteNo: string;
  customerId: string;
  customer: string;
  salesOwner: string;
  status: string;
  statusLabel: string;
  origin: string;
  destination: string;
  route: string;
  incoterm: string;
  transportMode: string;
  goodsDescription: string;
  expectedDeliveryDate: string;
  currency: string;
  total?: MaybeNum;
  sellingPriceTotalVnd?: MaybeNum;
  estimatedCostVnd?: MaybeNum;
  estimatedMarginVnd?: MaybeNum;
  isEstimate?: boolean;
  ledgerPosted?: boolean;
  /**
   * Quote-time rates the operator entered for THIS quote (VND base). The VND
   * totals above are derived from them, so they are always disclosed next to
   * the total. NO FAKE FX: the app never invents a rate — a quote whose lines
   * need one cannot be saved without it.
   */
  fxRatesToVnd?: Record<string, number | null>;
  fxSource?: string;
  /** Line currencies that required a rate (empty for a VND-only quote). */
  fxNeededFor?: string[];
  serviceLines: QuoteServiceLine[];
  assumptions: string[];
  statusHistory: Array<Record<string, unknown>>;
  version?: number;
  shipmentId?: string;
  allowedTransitions: string[];
  source?: string;
}

export interface AgreementHandoff {
  state: string;
  label: string;
  reasons: string[];
  blocks_operations?: boolean;
  source?: string;
}

export interface Agreement {
  id: string;
  agreementNo: string;
  customerId: string;
  customer: string;
  quoteId: string;
  quoteReference: string;
  status: string;
  statusLabel: string;
  version?: number;
  effectiveDate: string;
  commercialSnapshot?: Record<string, unknown>;
  paymentTerms?: Record<string, unknown>;
  responsibilities?: Record<string, unknown>;
  requiredDocuments: Array<Record<string, unknown>>;
  factoryLots: Array<Record<string, unknown>>;
  assumptions: string[];
  unresolvedIssues: string[];
  evidence: Record<string, unknown>;
  shipmentIds: string[];
  statusHistory: Array<Record<string, unknown>>;
  handoff: AgreementHandoff;
  allowedTransitions: string[];
  source?: string;
}

export interface AuthorityParty {
  id: string;
  legalName: string;
  legalCode: string;
  legalAddress: string;
  representative: string;
  representativeTitle: string;
  phone: string;
  email: string;
  bankAccountHolder: string;
  bankAccountNumber: string;
  bankName: string;
  bankBranch: string;
}

export interface GoodsLine {
  stt: number;
  description: string;
  unit: string;
  quantity: MaybeNum;
  unitPrice: MaybeNum;
  vatRate: string;
  amount: MaybeNum;
}

export interface GoodsTotals {
  lines?: Array<Record<string, unknown>>;
  subtotal: number;
  vat_amount: number;
  total_after_vat: number;
  currency: string;
}

export interface DocCard {
  document_type: string;
  state: string;
  reason: string;
  missing: string[];
  source_ref?: string;
  goods_count?: number;
  applicable?: boolean;
}

export interface ContractDocument {
  id: string;
  documentId: string;
  documentType: string;
  documentTypeLabel: string;
  revision: number;
  status: string;
  fileName: string;
  mime: string;
  generatedAt: string;
  generatedBy: string;
  issuedAt: string;
  issuedBy: string;
  templateHash: string;
  outputHash: string;
  supersedes: string;
  supersededBy: string;
  downloadAvailable: boolean;
  downloadBase64: string | null;
}

export interface ContractIdentity {
  hdntNo: string;
  hdntDate: string;
  validFrom: string;
  validTo: string;
  plNo: string;
  plDate: string;
  hdmbNo: string;
  hdmbDate: string;
}

export interface LinkedShipment {
  id: string;
  customer: string;
  status: string;
  to: string;
}

export interface Contract {
  id: string;
  contractNo: string;
  kind: string;
  status: string;
  statusTone: Tone;
  client: string;
  customerId: string;
  company: string;
  companyLegal: string;
  agent: string;
  companyId: string;
  agentId: string;
  value?: MaybeNum;
  currency: string;
  note: string;
  contractDate: string;
  /**
   * LOGI_CONTRACT_AND_SHIPMENT_CORE_GAPS_01 — the operator's OWN phụ lục
   * decision, read back verbatim from the stored contract: "YES" (Có PL),
   * "NO" (Không cần PL) or "" (= chưa chọn). A legacy contract that never
   * recorded it reads back "" and the desk keeps asking; "" is never rendered
   * as "Không cần PL", exactly like an unknown amount is never 0.
   */
  plRequired: string;
  parties: { company: AuthorityParty | null; agent: AuthorityParty | null };
  goodsLines: GoodsLine[];
  /**
   * null while the authoritative rule cannot produce a reliable total (no goods
   * line yet, or a line with an UNKNOWN quantity/price). UNKNOWN != ZERO: the
   * HDNT+PL vs HDMB threshold decision is only shown for a real total.
   */
  goodsTotals: GoodsTotals | null;
  thresholdVnd: number;
  applicableDocuments: string[];
  docCards: DocCard[];
  hdntReuse: Record<string, unknown>;
  identity: ContractIdentity;
  linkedShipments: LinkedShipment[];
  documents: ContractDocument[];
  source?: string;
}

export interface Notif {
  id: string;
  title: string;
  desc: string;
  time: string;
  tone: "red" | "amber" | "blue";
  route?: string;
}

/**
 * C2C — one row of the global customer-receivable worklist. receivable /
 * outstanding are UNKNOWN (null) until an actual service line is booked;
 * received is the non-reversed customer receipt total (a genuine 0 when no
 * payment exists). Totals are grouped by currency — never summed across
 * currencies (no FX engine).
 */
export interface ReceivableRow {
  id: string;
  customer: string;
  customerId?: string;
  currency: string;
  receivable: MaybeNum;
  received: MaybeNum;
  outstanding: MaybeNum;
  sale: string;
  support: string;
  status: string;
  statusTone: Tone;
  hasActualLines: boolean;
}

export interface ReceivableTotals {
  [currency: string]: {
    receivable: MaybeNum;
    received: MaybeNum;
    outstanding: MaybeNum;
  };
}

export interface ReceivablesViewModel {
  rows: ReceivableRow[];
  totals: ReceivableTotals;
}

/**
 * C2D — one row of the global partner-payable (THANH TOÁN ĐỐI TÁC / PHẢI TRẢ)
 * worklist. Grain: SHIPMENT × PARTNER × CURRENCY. payable/paid/remaining are
 * derived from the canonical ledger (obligation + allocation history). A
 * shipment/partner with no canonical record contributes NO row at all
 * (UNKNOWN != ZERO — absence is never a manufactured 0). Currencies are
 * never summed together (no FX engine).
 */
export interface PartnerPayableRow {
  id: string;
  partnerId: string;
  partnerName: string;
  shipmentId: string;
  currency: string;
  payable: MaybeNum;
  paid: MaybeNum;
  remaining: MaybeNum;
  status: string;
  obligationIds: string[];
}

export interface PartnerPayableTotals {
  [currency: string]: {
    payable: number;
    paid: number;
    remaining: number;
    count: number;
  };
}

export interface PartnerPayablesViewModel {
  rows: PartnerPayableRow[];
  totals: PartnerPayableTotals;
  status?: string;
  derived?: boolean;
  readOnly?: boolean;
  error?: string;
}

export interface HomeTile {
  label: string;
  value: number;
  sub: string;
  to: string;
}

export interface HomeSummary {
  total: number;
  critical: number;
  warning: number;
  deadlineSoon: number;
  financialAttention: number;
  missingInfo: number;
}

export interface Home {
  tiles: HomeTile[];
  runningCount: number;
  runningSummary: { id: string; customer: string; status: string; nextAction: string; to: string }[];
  outstandingTotal: MaybeNum;
  outstandingTotalLabel: string;
  outstandingCount: number;
  summary: HomeSummary;
  urgentCount: number;
  focus: {
    id: string;
    customer: string;
    status: string;
    nextAction: string;
    nextActionDetail: string;
    priority: Priority;
    to: string;
  } | null;
  missingDocsTotal: number;
  taskCount: number;
}

export interface Environment {
  transport: string;
  label: string;
  isSandbox: boolean;
  database: string;
}

// ----------------------------------------------------------------------------
// LOGI_TARIFF_LOOKUP_01 — bounded read-only HS/tariff lookup slice, served by
// views/tariff_lookup.py over the EXISTING canonical reader. UNKNOWN != ZERO:
// every field the governed reference schema does not carry arrives as null and
// renders as an explicit "—"; values pass through verbatim, never reformatted.
// ----------------------------------------------------------------------------

export interface TariffField {
  label: string;
  value: string | null;
}

export interface TariffRow {
  hsCode: string | null;
  descriptionVi: string | null;
  descriptionEn: string | null;
  /** Verbatim extra columns of a richer deployment DB (uninterpreted). */
  fields: TariffField[];
}

export interface TariffSource {
  configured: boolean;
  path: string;
  rows: number | null;
  note: string | null;
}

export interface TariffProvenance {
  source: string | null;
  effectiveDate: string | null;
  authoritative: boolean;
  note: string;
}

export interface TariffLookup {
  query: string;
  searched: boolean;
  reason: string | null;
  rows: TariffRow[];
  count: number;
  truncated: boolean;
  limit: number;
  source: TariffSource;
  provenance: TariffProvenance;
}

// ----------------------------------------------------------------------------
// LOGI_TRANSLATION_WORKSPACE_01 — bounded /dich-thuat slice, served by
// views/translation.py over the EXISTING canonical DeepL client
// (core/deepl_translation.py). Nothing here is fabricated: `capability` says
// what the backend really accepts and whether it is configured at all, and
// `request` / `result` stay null until a translation actually happened.
//
// PRIVACY: `externalProvider` is always true — the text IS sent to DeepL. This
// workspace is never presented as a local/private translator.
//
// NO SECRETS: the slice carries `configured` / `apiCount` only, never a key.
// ----------------------------------------------------------------------------

export interface TranslationLanguage {
  code: string;
  label: string;
}

export interface TranslationCapability {
  provider: string;
  configured: boolean;
  apiCount: number;
  /** The existing RBAC answer for the `translation` permission. */
  allowed: boolean;
  autoDetectSupported: boolean;
  sourceLanguages: TranslationLanguage[];
  targetLanguages: TranslationLanguage[];
  maxTextBytes: number;
  logisticsContext: boolean;
  externalProvider: boolean;
  privacyNotice: string;
  /** Honest "chưa được cấu hình" state, null when keys exist. */
  configNotice: string | null;
  /** target code → source code (existing Streamlit view's own mapping). */
  swapSource: Record<string, string>;
  /** source code → target code (existing Streamlit view's own mapping). */
  swapTarget: Record<string, string>;
}

export interface TranslationRequest {
  text: string;
  sourceLang: string;
  targetLang: string;
  /** Stable identity of ONE intent — the loading/duplicate guard key. */
  fingerprint: string;
}

export interface TranslationResult {
  /** "translated" | "invalid" | "error" | "config_required" */
  status: string;
  /** Verbatim provider text — null unless status === "translated". */
  text: string | null;
  error: string | null;
  detectedSourceLanguage: string | null;
  billedCharacters: number | null;
  apiLabel: string | null;
  provider: string;
}

export interface TranslationWorkspace {
  capability: TranslationCapability;
  request: TranslationRequest | null;
  result: TranslationResult | null;
}

// ----------------------------------------------------------------------------
// LOGI_PARTNER_CONTEXT_WORKSPACE_01 — bounded read-only partner-context slice,
// served by views/partner_context.py over the EXISTING authoritative readers:
// core.entity_context (shipment-partner index), the authority_agents legal
// master, and the C2D canonical payable projection built in the same render.
//
// NOTHING here is a CRM model: there is no relationship / risk / credit /
// reliability score, no tier, no account manager, no SLA, no note, no activity
// timeline and no tag. `unavailable` is the backend's honest list of exactly
// that. `identity.party` reuses the AuthorityParty master shape verbatim, so
// one master can never render differently on two screens.
//
// UNKNOWN != ZERO: absent fields stay null and render "—". A partner with no
// canonical payable gets NO finance row and status "UNKNOWN" — never 0.
// Amounts are the ledger's own, per currency; this slice never re-derives or
// sums them, and currencies are never combined.
// ----------------------------------------------------------------------------

export interface PartnerContextOption {
  key: string;
  label: string;
  /** True when an authority_agents master record backs this partner. */
  master: boolean;
  sources: string[];
  shipmentIds: string[];
  shipmentCount: number;
  currencies: string[];
  legalCode?: string | null;
  phone?: string | null;
  email?: string | null;
}

export interface PartnerContextIdentity {
  /** authority_agents master fields, verbatim; null when no approved master. */
  party: AuthorityParty | null;
  masterStatus: string;
  masterSource: string;
  displayName: string;
  displayId: string;
  /** What the shipment-partner index knows (may differ from the master). */
  contextName: string | null;
  contextId: string | null;
}

/** One linked shipment: identity + link ONLY (detail stays on /lo-hang/:id). */
export interface PartnerContextShipmentRow {
  shipmentId: string;
  status: string | null;
  requiredDate: string | null;
  plannedDate: string | null;
  attention: string | null;
  attentionDetail: string | null;
  role: string | null;
  route: string | null;
  operationalContext: string | null;
  source: string;
  financeCurrencies: string[];
  openHref: string;
  /** False when the existing shipment route cannot serve this id. */
  canOpen: boolean;
}

export interface PartnerPayableContextRow {
  id: string | null;
  shipmentId: string | null;
  currency: string | null;
  payable: MaybeNum;
  paid: MaybeNum;
  remaining: MaybeNum;
  status: string | null;
  obligationIds: string[];
  source: string;
}

export interface PartnerContextFinance {
  rows: PartnerPayableContextRow[];
  status: string;
  statusLabel: string;
  /** Counts per currency — deliberately NO partner-level payable total. */
  byCurrency: Record<string, { rowCount: number; shipmentIds: string[]; obligationCount: number }>;
  worklistHref: string;
  note: string;
}

export interface PartnerContextSlice {
  readOnly: boolean;
  /** OK | NO_SELECTION | NO_PARTNER_SOURCE | PARTNER_NOT_FOUND */
  status: string;
  reason: string | null;
  selectedKey: string | null;
  selectedLabel: string | null;
  matchedSources: string[];
  options: PartnerContextOption[];
  optionCount: number;
  optionTruncated: boolean;
  optionLimit: number;
  /** Exactly the terms this lookup genuinely supports. */
  searchFields: string[];
  identity?: PartnerContextIdentity;
  roles?: string[];
  shipments?: PartnerContextShipmentRow[];
  shipmentCount?: number;
  shipmentTruncated?: boolean;
  documents?: {
    shipmentId: string | null;
    document: string | null;
    status: string | null;
    source: string | null;
  }[];
  finance?: PartnerContextFinance;
  gaps?: string[];
  unavailable?: string[];
}

// ----------------------------------------------------------------------------
// LOGI_RECONCILIATION_DESK_01 — bounded read-only reconciliation slice for
// /tai-chinh/doi-soat, served by views/reconciliation_desk.py over the EXISTING
// canonical allocation truth (core.financial_ledger). Nothing here is computed
// in the browser: every amount, match state and currency total is what the
// ledger already derived.
//
// UNKNOWN != ZERO: `amount` / `allocated` / `remaining` are null when the
// canonical record genuinely carries no such figure, and `matchState` is null
// when the ledger could not derive one — both render as "—", never as 0 and
// never as "settled".
// ----------------------------------------------------------------------------

/** Obligation side vs money side of the reconciliation. */
export type ReconciliationSide = "obligation" | "money";

/**
 * Obligation rows: MATCHED | PARTIAL | UNMATCHED.
 * Money rows:      ALLOCATED | PARTIAL | UNALLOCATED.
 * null when the canonical figures were not derivable.
 */
export type ReconciliationState =
  | "MATCHED"
  | "PARTIAL"
  | "UNMATCHED"
  | "ALLOCATED"
  | "UNALLOCATED"
  | null;

export interface ReconciliationRow {
  id: string;
  side: ReconciliationSide;
  /** Real shipment this record is linked to. */
  shipmentId: string;
  shipmentIds: string[];
  partnerId: string | null;
  partnerName: string | null;
  counterparty: string | null;
  purpose: string | null;
  /** Money rows only: when the transaction occurred. */
  occurredAt?: string | null;
  /** "UNKNOWN" when the record carries no currency — never merged into a real one. */
  currency: string;
  amount: MaybeNum;
  allocated: MaybeNum;
  /** Obligation: outstanding. Money: unallocated. */
  remaining: MaybeNum;
  /** CONFIRMED | REVIEW_REQUIRED | UNKNOWN — the canonical record status. */
  status: string;
  matchState: ReconciliationState;
  matchLabel: string | null;
  allocationIds: string[];
  obligationIds: string[];
  transactionIds: string[];
  sourceRecordIds: string[];
  /** The canonical review signal, or null when the record is clean. */
  reviewReason: string | null;
  openHref: string;
  /** False when the existing /lo-hang/:id route cannot serve this shipment. */
  canOpen: boolean;
}

export interface ReconciliationCurrencyTotal {
  currency: string;
  obligations: { count: number; amount: number; allocated: number; remaining: number };
  money: { count: number; amount: number; allocated: number; unallocated: number };
  /** Unconfirmed amounts, reported separately so they cannot hide in a total. */
  review: { count: number; amount: number };
  states: Record<string, number>;
}

export interface ReconciliationAction {
  label: string;
  href: string;
  note: string;
}

export interface ReconciliationSlice {
  readOnly: boolean;
  derived: boolean;
  /** OK | EMPTY | NO_SOURCE | REVIEW_REQUIRED */
  status: string;
  rows: ReconciliationRow[];
  /** Per-currency totals over ALL rows — deliberately not filtered. */
  totals: Record<string, ReconciliationCurrencyTotal>;
  /**
   * Unfiltered count-only state summary over the same canonical rows. It is
   * null when the ledger is empty/unavailable, never a manufactured zero book.
   */
  summary?: {
    obligations: Record<string, number>;
    money: Record<string, number>;
    reviewCount: number;
  } | null;
  /** Currencies actually present, UNKNOWN last. */
  currencies: string[];
  visibleCount: number;
  totalCount: number;
  query: string;
  currency: string;
  state: string;
  side: string;
  truncated: boolean;
  maxRows: number;
  shipmentRoutePrefix: string;
  /** Navigation to the canonical writers — this desk exposes none. */
  actions: ReconciliationAction[];
  /** Reconciliation context this backend genuinely does not model. */
  unavailable: string[];
  error: string | null;
}

// ----------------------------------------------------------------------------
// LOGI_CEO_REPORT_01 — current-position management summary. All money comes
// from C2C/C2D's already-authoritative *per-currency* projections; there is no
// cross-currency grand total, forecast, target, profit or margin aggregation.
// ----------------------------------------------------------------------------

export interface CeoCurrencyPosition {
  currency: string;
  outstanding: MaybeNum;
  /** Existing source-row count whose outstanding amount is genuinely > 0. */
  openCount: number;
  /** Known source rows only; C2C grain: shipment; C2D: shipment × partner × currency. */
  rowCount: number;
  /** Missing/unsafe source rows excluded from this currency's amount/count. */
  incompleteRowCount: number;
}

export interface CeoStatusCount {
  status: string;
  count: number;
  /**
   * count / the REAL current shipment row count (every row counted once).
   * null only when there is no shipment row at all — never an invented total.
   */
  share: number | null;
}

/** LOGI_CEO_REPORT_REAL_PARITY_01 — current ACTUAL position of one currency. */
export interface CeoFinancePosition {
  currency: string;
  /** core.logic revenue_net of booked Finance Actual rows, same currency only. */
  revenueNet: MaybeNum;
  /** core.logic cost of the SAME booked rows, same currency only. */
  cost: MaybeNum;
  /** core.logic profit; UNKNOWN until at least one actual line is booked. */
  profit: MaybeNum;
  /** profit / revenueNet × 100 inside this currency; null when revenue ≤ 0/unknown. */
  marginPct: MaybeNum;
  rowCount: number;
  /** Booked rows whose figures were unsafe; excluded, never zero-filled. */
  incompleteRowCount: number;
}

/** Actual-revenue ranking strictly INSIDE one currency. */
export interface CeoTopCustomerGroup {
  currency: string;
  customers: { name: string; revenueNet: number; shipmentCount: number }[];
}

/** One real actionable row passed through from the existing task projection. */
export interface CeoActionable {
  id: string;
  level: "Khan" | "CanXuLy" | string;
  shipmentId: string;
  customer: string;
  job: string;
  detail: string | null;
  route: string;
}

export interface CeoReport {
  classification: "PARTIAL_BACKED_READY" | string;
  readOnly: boolean;
  operations: {
    totalShipmentCount: number;
    /** Existing Home meaning: not delivered and not cancelled; null if absent. */
    openShipmentCount: number | null;
    statusCounts: CeoStatusCount[];
    /** Existing work-desk meaning: Khẩn + Cần xử lý. */
    actionableTaskCount: number;
  };
  /** Bounded top of the already-ordered real task projection (read-only). */
  actionables: CeoActionable[];
  receivables: {
    positions: CeoCurrencyPosition[];
    shipmentRowCount: number;
    hasAuthoritativeAmounts: boolean;
  };
  payables: {
    positions: CeoCurrencyPosition[];
    recordCount: number;
    hasCanonicalRecords: boolean;
    status: string;
    error: string | null;
  };
  /** Current actual revenue/cost/profit per currency — never cross-currency. */
  financeActual: {
    positions: CeoFinancePosition[];
    available: boolean;
  };
  /** Top customers by actual revenue, ranked inside one currency only. */
  topCustomers: CeoTopCustomerGroup[];
  finance: {
    /** No Finance Actual ⇒ excluded from AR sums, never treated as zero. */
    incompleteShipmentCount: number;
  };
  reconciliation: {
    status: string;
    available: boolean;
    obligations: Record<string, number | null> | null;
    money: Record<string, number | null> | null;
    reviewCount: number | null;
    error: string | null;
  };
  quickLinks: { label: string; href: string; note: string }[];
  unavailable: string[];
}

// ----------------------------------------------------------------------------
// LOGI_NOTEBOOK_WORKSPACE_01 — bounded /so-tay handbook slice.
//
// Everything below is reference material this repository already owns (the
// status/Incoterm/service-code constants the app runs on, the locked docgen
// rules, the official trade-compliance source registry, the single RBAC matrix)
// plus the team's own notes read through the existing knowledge_base reader.
// The page is READ-ONLY: no authoring event, no search backend, no second
// content store. `provenance` mirrors only what a source actually records —
// a missing version/owner/date stays null and is rendered as "không có".
// ----------------------------------------------------------------------------

export interface HandbookProvenance {
  source: string;
  version: string | null;
  updated: string | null;
  owner: string | null;
  note: string | null;
}

export interface HandbookTable {
  columns: string[];
  rows: string[][];
}

export interface HandbookLink {
  label: string;
  href: string;
}

export interface HandbookEntry {
  id: string;
  title: string;
  summary: string;
  bullets: string[];
  table: HandbookTable | null;
  links: HandbookLink[];
  tags: string[];
  /** Per-item provenance when the source carries its own (e.g. a team note). */
  provenance?: HandbookProvenance | null;
}

export interface HandbookSection {
  id: string;
  label: string;
  icon: string;
  lead: string;
  provenance: HandbookProvenance;
  entries: HandbookEntry[];
  /** Honest empty/unavailable state, shown instead of fabricated material. */
  state: { tone: "gray" | "amber" | string; text: string } | null;
}

export interface HandbookCounts {
  sectionCount: number;
  availableSectionCount: number;
  entryCount: number;
  /** Entries delivered to the page (bounded by MAX_NOTE_ENTRIES on the server). */
  noteCount: number;
  /** Full source count, so a bounded payload is not mistaken for the corpus. */
  noteTotal: number;
}

export interface NotebookHandbook {
  classification: "STATIC_CONTENT_READY" | string;
  readOnly: boolean;
  sections: HandbookSection[];
  counts: HandbookCounts;
  /** Explicit scope limits of this page — stated, never filled with guesses. */
  unavailable: string[];
  sectionsAvailable: string[];
  sectionsUnavailable: string[];
}

// ----------------------------------------------------------------------------
// LOGI_USER_ACCESS_WORKSPACE_01 — bounded /nguoi-dung user & access slice.
//
// A READ-ONLY projection over capability the backend already owns: the user
// store read through the canonical password-free public view, the single
// ROLE_PERMISSIONS matrix (verbatim — no role or permission is added here),
// the real authentication mode (multi-user vs Local Admin) and the current
// session identity.
//
// LOGI_USER_MANAGEMENT_01 — an Admin session additionally gets `canManage:
// true`, which is a DISPLAY hint only (whether to offer the account-
// management controls at all); the real Admin-only boundary is re-checked
// server-side on every mutation by core.database, never by this flag. No
// credential material (password / password_hash) is ever carried here.
// ----------------------------------------------------------------------------

export interface UserAccessAccount {
  user_id: string;
  username: string;
  display_name: string;
  email: string;
  role: string;
  active: boolean;
}

export interface UserAccessRoleRow {
  role: string;
  permissions: string[];
  /** Canonical admin wildcard "*" present — rendered as "toàn quyền". */
  wildcard: boolean;
  permissionCount: number;
}

export interface UserAccessCurrentUser {
  present: boolean;
  username: string;
  displayName: string;
  role: string;
  permissions: string[];
  wildcard: boolean;
}

export interface UserAccessAuthMode {
  /** True when AUTH_REQUIRED is on (real multi-user login). */
  required: boolean;
  mode: "multi_user" | "local_admin" | string;
  label: string;
  note: string;
}

export interface UserAccessWorkspace {
  classification: "READ_ONLY_READY" | string;
  /** True for every non-Admin viewer; false once `canManage` is true. */
  readOnly: boolean;
  /** LOGI_USER_MANAGEMENT_01 — display hint: offer the Admin controls. */
  canManage: boolean;
  authMode: UserAccessAuthMode;
  currentUser: UserAccessCurrentUser;
  users: UserAccessAccount[];
  roles: {
    /** Roles an account can actually hold (core.users.SUPPORTED_ROLES). */
    assignable: string[];
    /** Compatibility roles kept in the matrix for legacy fixtures. */
    legacy: string[];
    source: string;
  };
  /** The single canonical matrix, verbatim from core.auth.ROLE_PERMISSIONS. */
  permissionMatrix: UserAccessRoleRow[];
  counts: {
    userCount: number;
    userShown: number;
    activeCount: number;
    inactiveCount: number;
    roleCount: number;
    assignableRoleCount: number;
  };
  /** Explicit scope limits — stated, never filled with guessed features. */
  unavailable: string[];
}

// ----------------------------------------------------------------------------
// LOGI_REAL_USE_CREATE_SHIPMENT_AGENT_MASTER_01 — authoritative write outcomes.
//
// The bounded Python dispatcher stores the result of every business event it
// handled (RBAC → canonical writer → audit → fresh read) in the session and
// embeds it in the NEXT fresh view-model. The UI must never treat "event was
// transported" as "write succeeded": success, duplicate/RBAC/validation
// refusals and the fresh readback all arrive here. Outcomes are matched to the
// originating click by the `requestId` the component sent with the event.
// ----------------------------------------------------------------------------

export interface LastWriteOutcome {
  event: string;
  ok: boolean;
  error?: string;
  /** Phase B shipment-scoped events carry shipmentId; C1 events carry id. */
  shipmentId?: string;
  id?: string;
  /** Echoed identity of the UI request that produced this outcome. */
  requestId?: string;
  /** Fresh backend readback (e.g. the created shipment / saved agent). */
  readback?: unknown;
  [extra: string]: unknown;
}

export interface GetFlyServiceLine {
  lineId: string;
  code: string;
  name: string;
  description: string;
  qty: MaybeNum;
  cost: MaybeNum;
  price: MaybeNum;
  revenue: MaybeNum;
  profit: MaybeNum;
}

export interface GetFlyOrderPreview {
  orderId: string;
  customer: string;
  customerName?: string;
  customerCode: string;
  customerId: string;
  customerMatch: "MATCHED_BY_CODE" | "MATCHED_BY_NAME" | "UNKNOWN" | string;
  orderDate: string;
  sourceStatus: string;
  existing: boolean;
  serviceLines: GetFlyServiceLine[];
  revenue: MaybeNum;
  profit: MaybeNum;
}

export interface GetFlyNormalizedRow {
  order_id: string;
  line_id: string;
  source_row: number;
  product_code: string;
  product_name: string;
  product_note: string;
  qty: MaybeNum;
  cost: MaybeNum;
  price: MaybeNum;
  revenue: MaybeNum;
  profit: MaybeNum;
}

export interface GetFlyPreview {
  status: "EMPTY" | "READY" | string;
  previewId: string;
  requestId?: string;
  filename: string;
  fingerprint?: string;
  normalizedRows?: GetFlyNormalizedRow[];
  orders: GetFlyOrderPreview[];
  summary: { orders: number; revenue: MaybeNum; profit: MaybeNum };
  error?: string;
}

export interface ViewModel {
  version: string;
  environment?: Environment;
  user: { name: string; role: Role; username?: string; displayOnly?: boolean };
  shipments: Shipment[];
  home?: Home;
  tasks: Task[];
  contracts: Contract[];
  customers: Customer[];
  quotes: Quote[];
  agreements?: Agreement[];
  authority?: { companies: AuthorityParty[]; agents: AuthorityParty[] };
  notifications: Notif[];
  /** C2C — global customer-receivable worklist (read-only projection). */
  receivables?: ReceivablesViewModel;
  /** C2D — global partner-payable worklist (read-only projection). */
  payables?: PartnerPayablesViewModel;
  /** LOGI_TARIFF_LOOKUP_01 — read-only HS/tariff lookup slice. */
  tariff?: TariffLookup;
  /** LOGI_TRANSLATION_WORKSPACE_01 — bounded DeepL translation slice. */
  translation?: TranslationWorkspace;
  /** LOGI_PARTNER_CONTEXT_WORKSPACE_01 — read-only partner-context slice. */
  partnerContext?: PartnerContextSlice;
  /** LOGI_RECONCILIATION_DESK_01 — read-only đối soát slice. */
  reconciliation?: ReconciliationSlice;
  /** LOGI_CEO_REPORT_01 — bounded read-only current-position summary. */
  ceoReport?: CeoReport;
  /** LOGI_NOTEBOOK_WORKSPACE_01 — bounded read-only /so-tay handbook slice. */
  handbook?: NotebookHandbook;
  /** LOGI_USER_ACCESS_WORKSPACE_01 — bounded read-only /nguoi-dung slice. */
  userAccess?: UserAccessWorkspace;
  /**
   * LOGI_FINANCE_ACTUAL_ENTRY_PARITY_01 — read-only service catalog slice
   * (``core.config.GETFLY_SERVICES_LIST`` projected by the backend) used by the
   * Finance Actual editor's service picker. Absent = not delivered yet, which
   * the page renders as an honest empty picker, never a hard-coded list.
   */
  financeServiceCatalog?: FinanceServiceCatalogEntry[];
  /** LOGI_GETFLY_DSDH_IMPORT_PARITY_01 — ephemeral server-authoritative XLSX preview. */
  getfly?: GetFlyPreview;
  /**
   * LOGI_SHIPMENT_DOCUMENTS_DRIVE_REINTEGRATE_02 — the server's own attachment
   * policy. Absent = not delivered: the form stays hidden rather than inventing
   * its own extension list or size limit.
   */
  attachmentPolicy?: AttachmentPolicy;
  /** Authoritative outcomes of the last handled business events (see above). */
  lastWrites?: LastWriteOutcome[];
  unknownLabel?: string;
}

// ----------------------------------------------------------------------------
// Live holder: the view-model as delivered by Python. Replaced in place on
// each component data update; subscribers (React store) are notified.
// ----------------------------------------------------------------------------

let current: ViewModel | null = null;
const listeners = new Set<() => void>();

export function applyViewModel(next: ViewModel): void {
  if (!next || typeof next !== "object") return;
  // A payload from before this slice (or an older fixture) carries no
  // attachment list. Normalise it to an empty array so the shipment document
  // tab renders an honest empty state instead of crashing on a missing field.
  for (const shipment of next.shipments ?? []) {
    if (!Array.isArray(shipment.attachments)) shipment.attachments = [];
  }
  const prev = current;
  current = next;
  if (prev === next) return;
  for (const fn of Array.from(listeners)) {
    try {
      fn();
    } catch {
      // listener errors must never break data delivery
    }
  }
}

export function getViewModel(): ViewModel | null {
  return current;
}

export function subscribeViewModel(fn: () => void): () => void {
  listeners.add(fn);
  return () => {
    listeners.delete(fn);
  };
}

/** The em dash used for UNKNOWN, shared with the Python projection. */
export function unknownLabel(): string {
  return current?.unknownLabel ?? "—";
}

/** The read-only tariff lookup slice (null until Python delivers it). */
export function tariffLookup(): TariffLookup | null {
  return current?.tariff ?? null;
}

/** The bounded /dich-thuat translation slice (null until Python delivers it). */
export function translationWorkspace(): TranslationWorkspace | null {
  return current?.translation ?? null;
}

/** The bounded /ngu-canh-doi-tac partner-context slice (null until delivered). */
export function partnerContext(): PartnerContextSlice | null {
  return current?.partnerContext ?? null;
}

/** The bounded /tai-chinh/doi-soat reconciliation slice (null until delivered). */
export function reconciliationDesk(): ReconciliationSlice | null {
  return current?.reconciliation ?? null;
}

/** The bounded /nguoi-dung user & access slice (null until delivered). */
export function userAccessWorkspace(): UserAccessWorkspace | null {
  return current?.userAccess ?? null;
}

/**
 * The read-only service catalog the backend projected from
 * ``core.config.GETFLY_SERVICES_LIST`` (empty until delivered). This is the
 * component's ONLY source of service codes — the list is never copied here.
 */
export function financeServiceCatalog(): FinanceServiceCatalogEntry[] {
  return current?.financeServiceCatalog ?? [];
}
