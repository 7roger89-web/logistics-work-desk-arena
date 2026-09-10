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

export interface Finance {
  quote: MoneyLine[];
  actual: MoneyLine[];
  currency?: string;
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
  payments: Payment[];
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

export interface Contract {
  id: string;
  company: string;
  agent: string;
  status: string;
  statusTone: Tone;
  companyLegal: string;
  value?: MaybeNum;
}

export interface Customer {
  name: string;
  short: string;
  mst: string;
}

export interface Quote {
  id: string;
  customer: string;
  status: string;
  total?: MaybeNum;
  currency?: string;
}

export interface Notif {
  id: string;
  title: string;
  desc: string;
  time: string;
  tone: "red" | "amber" | "blue";
  route?: string;
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
  notifications: Notif[];
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
