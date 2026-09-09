export type Role = 'ADMIN' | 'SUPPORT' | 'SALE';

export type Currency = 'VND' | 'USD' | 'CNY';

export type DocStatus = 'DU' | 'THIEU' | 'CHAN';

export type ShipmentStatus =
  | 'CHO_LAY_HANG'
  | 'DANG_VAN_CHUYEN'
  | 'CHO_THONG_QUAN'
  | 'CHO_GIAO'
  | 'DA_GIAO';

export interface Money {
  amount: number;
  currency: Currency;
}

export interface ChecklistItem {
  name: string;
  status: DocStatus;
  note?: string;
}

export interface Factory {
  name: string;
  address: string;
  contact: string;
  phone: string;
  pickupTime: string;
}

export interface TruckCN {
  vehicleType: string;
  plate: string;
  driver: string;
  phone: string;
  etaDate: string;
  actualDate: string;
}

export interface GoodsInfo {
  packages: number;
  weightKg: number;
  dimensions: string;
  cbm: number;
  goodsType: string;
  note: string;
}

export interface ExportInfo {
  border: string;
  declUnit: string;
  etaDate: string;
  actualDate: string;
  status: 'CHUA_KHAI' | 'DANG_KHAI' | 'DA_THONG_QUAN';
}

export interface ImportInfo {
  borderVN: string;
  declNo: string;
  regDate: string;
  clearDate: string;
  taxAmount: number;
  vatAmount: number;
  inspected: boolean;
  licenseStatus: DocStatus;
}

export interface TruckVN {
  driver: string;
  plate: string;
  address: string;
  receiver: string;
  phone: string;
  scheduledDate: string;
  actualDate: string;
}

export interface CostLine {
  label: string;
  amount: number;
  currency: Currency;
}

export interface PaymentRecord {
  id: string;
  date: string;
  amount: number;
  currency: Currency;
  type: 'THU' | 'TRA';
  method: string;
  note: string;
  recordedBy: string;
  amended?: boolean;
  amendReason?: string;
}

export interface ShipmentFinance {
  quoted: CostLine[];
  actual: CostLine[];
  receivable: { total: number; paid: number; currency: Currency };
  payable: { total: number; paid: number; currency: Currency };
  history: PaymentRecord[];
}

export interface PXK {
  issued: boolean;
  deliveredDone: boolean;
  deliveryDate: string;
  location: string;
  receiver: string;
  position: string;
  soPXK: string;
  ngayPXK: string;
  sourceDoc: string;
}

export interface Shipment {
  id: string;
  customerId: string;
  customer: string;
  contractId?: string;
  contractNo?: string;
  route: string;
  border: string;
  sale: string;
  support: string;
  status: ShipmentStatus;
  nextAction: string;
  updatedAt: string;
  factory: Factory;
  truckCN: TruckCN;
  goods: GoodsInfo;
  exportInfo: ExportInfo;
  checklist: ChecklistItem[];
  importInfo: ImportInfo;
  truckVN: TruckVN;
  finance: ShipmentFinance;
  pxk: PXK;
}

export interface GoodsRow {
  stt: number;
  desc: string;
  unit: string;
  qty: number;
  unitPrice: number;
  vatRate: number;
}

export type ContractType = 'HDMB' | 'HDNT';
export type ContractStatus = 'DRAFT' | 'DA_PHAT_HANH' | 'HET_HIEU_LUC';

export interface Party {
  company: string;
  legalName: string;
  address: string;
  taxCode: string;
  representative: string;
  position: string;
  accountHolder?: string;
  accountNumber?: string;
  bank?: string;
}

export interface ContractHistoryItem {
  type: string;
  number: string;
  date: string;
  revision: string;
  status: string;
  createdBy: string;
  createdAt: string;
}

export interface Contract {
  id: string;
  type: ContractType;
  agent: string;
  company: string;
  customerId: string;
  value: number;
  validFrom: string;
  validTo: string;
  status: ContractStatus;
  buyer: Party;
  seller: Party;
  goodsRows: GoodsRow[];
  hdnt?: { soHDNT: string; ngayKy: string; hieuLucTu: string; hieuLucDen: string };
  pl?: { soPL: string; ngayPL: string; hdntCha: string };
  hdmb?: { soHDMB: string; ngayHDMB: string };
  history: ContractHistoryItem[];
  linkedShipmentIds: string[];
  lastGeneratedFile?: string;
}

export interface Customer {
  id: string;
  name: string;
  taxCode: string;
  contact: string;
  phone: string;
  sale: string;
  shipmentCount: number;
  debt: number;
  updatedAt: string;
  address: string;
  note: string;
}

export type QuoteStatus = 'DRAFT' | 'SENT' | 'ACCEPTED' | 'REJECTED';

export interface Quote {
  id: string;
  customerId: string;
  customer: string;
  incoterm: string;
  pickupPoint: string;
  border: string;
  deliveryPoint: string;
  goodsType: string;
  weightKg: number;
  cbm: number;
  costs: CostLine[];
  sellPrice: number;
  currency: Currency;
  status: QuoteStatus;
  createdAt: string;
}

export type AgreementStatus = 'DRAFT' | 'REVIEWING' | 'AGREED' | 'REVISED' | 'VOID';

export interface Agreement {
  id: string;
  customerId: string;
  customer: string;
  step: 1 | 2 | 3 | 4;
  incoterm: string;
  scope: string;
  paymentTerms: string;
  factoryContact: string;
  linkedShipmentId?: string;
  requiredDocs: string[];
  acceptanceEvidence: string;
  status: AgreementStatus;
}

export interface AppUser {
  id: string;
  name: string;
  username: string;
  role: Role;
  status: 'ACTIVE' | 'LOCKED';
  lastLogin: string;
}

export interface HsCode {
  code: string;
  name: string;
  importTax: number;
  vat: number;
  policy: string;
  note: string;
}

export interface TaskItem {
  id: string;
  priority: 'KHAN' | 'CAN_XU_LY' | 'BINH_THUONG';
  shipmentId: string;
  customer: string;
  action: string;
  assignee: string;
  due: string;
  status: string;
  tab: string;
}
