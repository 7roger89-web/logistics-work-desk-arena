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

export interface Cargo {
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

export interface GntInfo {
  payer: string;
  taxCode: string;
  address: string;
  customsOffice: string;
}

export interface ImportInfo {
  borderVN: string;
  declarationNo: string;
  regDate: string;
  clearDate?: string;
  /** Not modelled on the shipment document — arrives null, renders "—". */
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
  actual: MoneyLine[];
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
  version?: number;
  rawStatus?: string;
  mode?: string;
  incoterm?: string;
  createdAt?: string;
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
  parties: { company: AuthorityParty | null; agent: AuthorityParty | null };
  goodsLines: GoodsLine[];
  goodsTotals: GoodsTotals;
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
