// ============================================================================
// View-model contract — LOGI-GOOD / Logistics Work Desk (Phase A)
//
// This is the typed contract for data that flows:
//   Python Logistics view-model → Streamlit Components v2 `data` channel
//   → this module (applyViewModel) → React store / lib-data live arrays.
//
// Phase A: the Python view-model is backed by sandbox seed data only
// (no production DB, no credentials). The shape mirrors the real Logistics
// app entities so Phase B can swap the Python source without touching UI.
// ============================================================================

export type Tone = "green" | "amber" | "red" | "blue" | "gray";
export type Role = "ADMIN" | "SUPPORT" | "SALE";
export type Priority = "Khan" | "CanXuLy" | "BinhThuong";

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
  amount: number;
  ccy: string;
}

export interface Payment {
  date: string;
  kind: string;
  amount: number;
  ccy: string;
  by: string;
  note?: string;
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

export interface Cargo {
  packs: number;
  weight: string;
  cbm: number;
  dims: string;
  type: string;
  note?: string;
}

export interface ExportInfo {
  border: string;
  declarant: string;
  eta: string;
  ata: string;
  state: string;
}

export interface ImportInfo {
  borderVN: string;
  declarationNo: string;
  regDate: string;
  tax: number;
  vat: number;
  inspection: string;
  license: string;
  truckVN: string;
  plateVN: string;
  driverVN: string;
  schedule: string;
  deliveryAddr: string;
  receiver: string;
  receiverPhone: string;
  delivered: boolean;
  actualDelivery?: string;
  clearDate?: string;
}

export interface Finance {
  quote: MoneyLine[];
  actual: MoneyLine[];
  receivable: number;
  received: number;
  payable: number;
  paid: number;
  payments: Payment[];
}

export interface Pxk {
  number?: string;
  date?: string;
  place?: string;
  receiver?: string;
  role?: string;
  source?: string;
  done?: boolean;
}

export interface Shipment {
  id: string;
  customer: string;
  customerMST: string;
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
  pickup: Pickup;
  cargo: Cargo;
  exportInfo: ExportInfo;
  importInfo: ImportInfo;
  finance: Finance;
  pxk: Pxk;
  timeline: TimelineEntry[];
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
}

export interface Contract {
  id: string;
  company: string;
  agent: string;
  status: string;
  statusTone: Tone;
  companyLegal: string;
  value?: number;
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
}

export interface Notif {
  id: string;
  title: string;
  desc: string;
  time: string;
  tone: "red" | "amber" | "blue";
}

export interface ViewModel {
  version: string;
  user: { name: string; role: Role };
  shipments: Shipment[];
  tasks: Task[];
  contracts: Contract[];
  customers: Customer[];
  quotes: Quote[];
  notifications: Notif[];
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
