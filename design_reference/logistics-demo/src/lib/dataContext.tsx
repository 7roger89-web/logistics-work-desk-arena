import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from 'react';
import type {
  Shipment, Contract, Customer, Quote, Agreement, AppUser, Role, PaymentRecord, DocStatus, GoodsRow, ContractType,
} from './types';
import {
  SHIPMENTS, CONTRACTS, CUSTOMERS, QUOTES, AGREEMENTS, USERS,
} from './mockData';

// ---------- Toast ----------
export type ToastVariant = 'success' | 'warning' | 'danger' | 'info';
interface ToastMsg { id: string; message: string; variant: ToastVariant; }
interface ToastCtx { toasts: ToastMsg[]; push: (message: string, variant?: ToastVariant) => void; dismiss: (id: string) => void; }
const ToastContext = createContext<ToastCtx | null>(null);
export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error('useToast must be used inside AppProvider');
  return ctx;
}

// ---------- Role ----------
interface RoleCtx { role: Role; setRole: (r: Role) => void; userName: string; }
const RoleContext = createContext<RoleCtx | null>(null);
export function useRole() {
  const ctx = useContext(RoleContext);
  if (!ctx) throw new Error('useRole must be used inside AppProvider');
  return ctx;
}

const ROLE_NAMES: Record<Role, string> = {
  ADMIN: 'Đặng Hải Yến',
  SALE: 'Lê Minh Anh',
  SUPPORT: 'Nguyễn Thị Hải',
};

// ---------- App Data ----------
function todayVN() {
  const d = new Date();
  return d.toLocaleDateString('vi-VN');
}

function updateById<T extends { id: string }>(list: T[], id: string, updater: (item: T) => T): T[] {
  return list.map((item) => (item.id === id ? updater(item) : item));
}

interface AppDataCtx {
  shipments: Shipment[];
  contracts: Contract[];
  customers: Customer[];
  quotes: Quote[];
  agreements: Agreement[];
  users: AppUser[];
  getShipment: (id: string) => Shipment | undefined;
  getContract: (id: string) => Contract | undefined;
  getCustomer: (id: string) => Customer | undefined;
  addShipment: (data: Partial<Shipment> & { customer: string; customerId: string }) => string;
  updateShipmentFields: (shipmentId: string, patch: Partial<Shipment>) => void;
  setChecklistStatus: (shipmentId: string, name: string, status: DocStatus, note?: string) => void;
  confirmDelivery: (shipmentId: string) => void;
  addPayment: (shipmentId: string, payment: Omit<PaymentRecord, 'id'>) => void;
  amendPayment: (shipmentId: string, paymentId: string, reason: string) => void;
  issuePXK: (shipmentId: string, data: { location: string; receiver: string; position: string; sourceDoc: string }) => void;
  addContract: (data: Partial<Contract> & { type: ContractType; company: string; agent: string; customerId: string }) => string;
  addGoodsRow: (contractId: string) => void;
  updateGoodsRow: (contractId: string, stt: number, patch: Partial<GoodsRow>) => void;
  removeGoodsRow: (contractId: string, stt: number) => void;
  updateContractField: (contractId: string, patch: Partial<Contract>) => void;
  updatePartyField: (contractId: string, side: 'buyer' | 'seller', patch: Partial<Contract['buyer']>) => void;
  generateContractDocument: (contractId: string) => { ok: boolean; message: string };
  addQuote: (data: Omit<Quote, 'id' | 'createdAt' | 'status'>) => string;
  setQuoteStatus: (quoteId: string, status: Quote['status']) => void;
  addAgreement: (data: Omit<Agreement, 'id' | 'status' | 'step'>) => string;
  advanceAgreement: (agreementId: string) => void;
  setAgreementStatus: (agreementId: string, status: Agreement['status']) => void;
  toggleUserLock: (userId: string) => void;
  addUser: (data: { name: string; username: string; role: Role }) => void;
}
const AppDataContext = createContext<AppDataCtx | null>(null);
export function useAppData() {
  const ctx = useContext(AppDataContext);
  if (!ctx) throw new Error('useAppData must be used inside AppProvider');
  return ctx;
}

let shipmentSeq = 309;
let contractSeqHDMB = 15;
let contractSeqHDNT = 32;
let quoteSeq = 64;
let agreementSeq = 64;

export function AppProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastMsg[]>([]);
  const [role, setRole] = useState<Role>('ADMIN');

  const push = useCallback((message: string, variant: ToastVariant = 'success') => {
    const id = 'toast-' + Math.random().toString(36).slice(2, 9);
    setToasts((t) => [...t, { id, message, variant }]);
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 3800);
  }, []);
  const dismiss = useCallback((id: string) => setToasts((t) => t.filter((x) => x.id !== id)), []);

  const [shipments, setShipments] = useState<Shipment[]>(SHIPMENTS);
  const [contracts, setContracts] = useState<Contract[]>(CONTRACTS);
  const [customers] = useState<Customer[]>(CUSTOMERS);
  const [quotes, setQuotes] = useState<Quote[]>(QUOTES);
  const [agreements, setAgreements] = useState<Agreement[]>(AGREEMENTS);
  const [users, setUsers] = useState<AppUser[]>(USERS);

  const getShipment = useCallback((id: string) => shipments.find((s) => s.id === id), [shipments]);
  const getContract = useCallback((id: string) => contracts.find((c) => c.id === id), [contracts]);
  const getCustomer = useCallback((id: string) => customers.find((c) => c.id === id), [customers]);

  const addShipment = useCallback((data: Partial<Shipment> & { customer: string; customerId: string }) => {
    shipmentSeq += 1;
    const id = `LO-0${shipmentSeq}`;
    const newShipment: Shipment = {
      id,
      customerId: data.customerId,
      customer: data.customer,
      contractId: data.contractId,
      contractNo: data.contractNo,
      route: data.route || '',
      border: data.border || '',
      sale: data.sale || ROLE_NAMES.SALE,
      support: data.support || ROLE_NAMES.SUPPORT,
      status: 'CHO_LAY_HANG',
      nextAction: 'Xác nhận lịch xe TQ tới lấy hàng tại nhà máy',
      updatedAt: todayVN() + ' ' + new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }),
      factory: data.factory || { name: '', address: '', contact: '', phone: '', pickupTime: '' },
      truckCN: data.truckCN || { vehicleType: '', plate: '', driver: '', phone: '', etaDate: '', actualDate: '' },
      goods: data.goods || { packages: 0, weightKg: 0, dimensions: '', cbm: 0, goodsType: '', note: '' },
      exportInfo: data.exportInfo || { border: data.border || '', declUnit: '', etaDate: '', actualDate: '', status: 'CHUA_KHAI' },
      checklist: [
        { name: 'Invoice', status: 'THIEU' },
        { name: 'Packing List', status: 'THIEU' },
        { name: 'Contract', status: data.contractId ? 'DU' : 'THIEU' },
        { name: 'Export Declaration', status: 'THIEU' },
        { name: 'Giấy phép', status: 'THIEU' },
      ],
      importInfo: { borderVN: data.border || '', declNo: '', regDate: '', clearDate: '', taxAmount: 0, vatAmount: 0, inspected: false, licenseStatus: 'THIEU' },
      truckVN: { driver: '', plate: '', address: '', receiver: '', phone: '', scheduledDate: '', actualDate: '' },
      finance: { quoted: [], actual: [], receivable: { total: 0, paid: 0, currency: 'VND' }, payable: { total: 0, paid: 0, currency: 'VND' }, history: [] },
      pxk: { issued: false, deliveredDone: false, deliveryDate: '', location: '', receiver: '', position: '', soPXK: '', ngayPXK: '', sourceDoc: data.contractNo || '' },
    };
    setShipments((prev) => [newShipment, ...prev]);
    push(`Đã tạo lô hàng ${id} thành công`, 'success');
    return id;
  }, [push]);

  const updateShipmentFields = useCallback((shipmentId: string, patch: Partial<Shipment>) => {
    setShipments((prev) => updateById(prev, shipmentId, (s) => ({ ...s, ...patch, updatedAt: todayVN() })));
    push('Đã cập nhật thông tin lô hàng', 'success');
  }, [push]);

  const setChecklistStatus = useCallback((shipmentId: string, name: string, status: DocStatus, note?: string) => {
    setShipments((prev) => updateById(prev, shipmentId, (s) => ({
      ...s,
      checklist: s.checklist.map((c) => (c.name === name ? { ...c, status, note } : c)),
    })));
    push(`Đã cập nhật "${name}" → ${status === 'DU' ? 'Đủ' : status === 'THIEU' ? 'Thiếu' : 'Bị chặn'}`, status === 'DU' ? 'success' : 'warning');
  }, [push]);

  const confirmDelivery = useCallback((shipmentId: string) => {
    const now = todayVN();
    setShipments((prev) => updateById(prev, shipmentId, (s) => ({
      ...s,
      status: 'DA_GIAO',
      nextAction: 'Lập phiếu xuất kho (PXK) để hoàn tất hồ sơ',
      truckVN: { ...s.truckVN, actualDate: now },
      pxk: { ...s.pxk, deliveredDone: true, deliveryDate: now },
      updatedAt: now,
    })));
    push('Đã xác nhận giao hàng thành công', 'success');
  }, [push]);

  const addPayment = useCallback((shipmentId: string, payment: Omit<PaymentRecord, 'id'>) => {
    setShipments((prev) => updateById(prev, shipmentId, (s) => {
      const id = 'TT-' + Math.random().toString(36).slice(2, 7);
      const history = [...s.finance.history, { ...payment, id }];
      const receivable = payment.type === 'THU'
        ? { ...s.finance.receivable, paid: s.finance.receivable.paid + payment.amount }
        : s.finance.receivable;
      const payable = payment.type === 'TRA'
        ? { ...s.finance.payable, paid: s.finance.payable.paid + payment.amount }
        : s.finance.payable;
      return { ...s, finance: { ...s.finance, history, receivable, payable } };
    }));
    push(payment.type === 'THU' ? 'Đã ghi nhận khoản thu' : 'Đã ghi nhận khoản trả', 'success');
  }, [push]);

  const amendPayment = useCallback((shipmentId: string, paymentId: string, reason: string) => {
    setShipments((prev) => updateById(prev, shipmentId, (s) => ({
      ...s,
      finance: {
        ...s.finance,
        history: s.finance.history.map((p) => (p.id === paymentId ? { ...p, amended: true, amendReason: reason } : p)),
      },
    })));
    push('Đã ghi nhận điều chỉnh giao dịch', 'warning');
  }, [push]);

  const issuePXK = useCallback((shipmentId: string, data: { location: string; receiver: string; position: string; sourceDoc: string }) => {
    const now = todayVN();
    const soPXK = 'PXK-' + shipmentId.replace('LO-', '');
    setShipments((prev) => updateById(prev, shipmentId, (s) => ({
      ...s,
      pxk: { ...s.pxk, issued: true, ngayPXK: now, soPXK, location: data.location, receiver: data.receiver, position: data.position, sourceDoc: data.sourceDoc },
    })));
    push(`Đã xuất phiếu xuất kho ${soPXK}`, 'success');
  }, [push]);

  const addContract = useCallback((data: Partial<Contract> & { type: ContractType; company: string; agent: string; customerId: string }) => {
    let id: string;
    if (data.type === 'HDMB') {
      contractSeqHDMB += 1;
      id = `HDMB-2026-${String(contractSeqHDMB).padStart(3, '0')}`;
    } else {
      contractSeqHDNT += 1;
      id = `HDNT-2026-${String(contractSeqHDNT).padStart(3, '0')}`;
    }
    const newContract: Contract = {
      id,
      type: data.type,
      agent: data.agent,
      company: data.company,
      customerId: data.customerId,
      value: 0,
      validFrom: '',
      validTo: '',
      status: 'DRAFT',
      buyer: { company: data.company, legalName: '', address: '', taxCode: '', representative: '', position: '' },
      seller: { company: data.agent, legalName: '', address: '', taxCode: '', representative: '', position: '' },
      goodsRows: [{ stt: 1, desc: '', unit: 'Kiện', qty: 1, unitPrice: 0, vatRate: 8 }],
      history: [],
      linkedShipmentIds: [],
    };
    setContracts((prev) => [newContract, ...prev]);
    push(`Đã tạo hợp đồng nháp ${id}`, 'success');
    return id;
  }, [push]);

  const addGoodsRow = useCallback((contractId: string) => {
    setContracts((prev) => updateById(prev, contractId, (c) => {
      const nextStt = c.goodsRows.length ? Math.max(...c.goodsRows.map((r) => r.stt)) + 1 : 1;
      return { ...c, goodsRows: [...c.goodsRows, { stt: nextStt, desc: '', unit: 'Kiện', qty: 1, unitPrice: 0, vatRate: 8 }] };
    }));
  }, []);

  const updateGoodsRow = useCallback((contractId: string, stt: number, patch: Partial<GoodsRow>) => {
    setContracts((prev) => updateById(prev, contractId, (c) => ({
      ...c,
      goodsRows: c.goodsRows.map((r) => (r.stt === stt ? { ...r, ...patch } : r)),
    })));
  }, []);

  const removeGoodsRow = useCallback((contractId: string, stt: number) => {
    setContracts((prev) => updateById(prev, contractId, (c) => {
      const filtered = c.goodsRows.filter((r) => r.stt !== stt);
      const renumbered = filtered.map((r, idx) => ({ ...r, stt: idx + 1 }));
      return { ...c, goodsRows: renumbered };
    }));
  }, []);

  const updateContractField = useCallback((contractId: string, patch: Partial<Contract>) => {
    setContracts((prev) => updateById(prev, contractId, (c) => ({ ...c, ...patch })));
  }, []);

  const updatePartyField = useCallback((contractId: string, side: 'buyer' | 'seller', patch: Partial<Contract['buyer']>) => {
    setContracts((prev) => updateById(prev, contractId, (c) => ({ ...c, [side]: { ...c[side], ...patch } })));
    push('Đã cập nhật thông tin pháp lý', 'success');
  }, [push]);

  const generateContractDocument = useCallback((contractId: string): { ok: boolean; message: string } => {
    const contract = contracts.find((c) => c.id === contractId);
    if (!contract) return { ok: false, message: 'Không tìm thấy hợp đồng' };
    const total = contract.goodsRows.reduce((sum, r) => sum + r.qty * r.unitPrice * (1 + r.vatRate / 100), 0);
    const route = total >= 50000000 ? 'HDMB' : 'HDNT';
    if (route === 'HDMB' && contract.goodsRows.length > 1) {
      return { ok: false, message: 'Chưa thể xuất HDMB. HDMB V1 hỗ trợ tối đa 1 dòng hàng hóa.' };
    }
    if (route === 'HDMB' && !contract.hdmb?.ngayHDMB) {
      return { ok: false, message: 'Thiếu Ngày HDMB. Vui lòng bổ sung trước khi xuất chứng từ.' };
    }
    if (route === 'HDNT' && !contract.hdnt?.soHDNT) {
      return { ok: false, message: 'Thiếu số HDNT. Vui lòng bổ sung hoặc chọn tái sử dụng HDNT còn hiệu lực.' };
    }
    if (!contract.buyer.taxCode || !contract.seller.representative) {
      return { ok: false, message: 'Thiếu thông tin pháp lý Bên mua/Bên bán. Vui lòng bổ sung trước khi xuất chứng từ.' };
    }
    const fileName = `${contractId}_${contract.company.split(' ').slice(-2).join('')}_v${(contract.history.length + 1)}.pdf`;
    setContracts((prev) => updateById(prev, contractId, (c) => ({
      ...c,
      status: 'DA_PHAT_HANH',
      value: total,
      lastGeneratedFile: fileName,
      history: [
        { type: route, number: route === 'HDMB' ? (c.hdmb?.soHDMB || contractId) : (c.pl?.soPL || c.hdnt?.soHDNT || contractId), date: todayVN(), revision: `V${c.history.length + 1}`, status: 'ĐÃ PHÁT HÀNH', createdBy: ROLE_NAMES.SALE, createdAt: todayVN() },
        ...c.history,
      ],
    })));
    push('Đã tạo chứng từ thành công', 'success');
    return { ok: true, message: fileName };
  }, [contracts, push]);

  const addQuote = useCallback((data: Omit<Quote, 'id' | 'createdAt' | 'status'>) => {
    quoteSeq += 1;
    const id = `BG-2026-${quoteSeq}`;
    const newQuote: Quote = { ...data, id, status: 'DRAFT', createdAt: todayVN() };
    setQuotes((prev) => [newQuote, ...prev]);
    push(`Đã tạo báo giá ${id}`, 'success');
    return id;
  }, [push]);

  const setQuoteStatus = useCallback((quoteId: string, status: Quote['status']) => {
    setQuotes((prev) => updateById(prev, quoteId, (q) => ({ ...q, status })));
    push(status === 'SENT' ? 'Đã gửi báo giá cho khách' : 'Khách hàng đã chốt báo giá', 'success');
  }, [push]);

  const addAgreement = useCallback((data: Omit<Agreement, 'id' | 'status' | 'step'>) => {
    agreementSeq += 1;
    const id = `TT-2026-${agreementSeq}`;
    const newAgreement: Agreement = { ...data, id, status: 'DRAFT', step: 2 };
    setAgreements((prev) => [newAgreement, ...prev]);
    push(`Đã tạo thỏa thuận ${id} từ báo giá đã chốt`, 'success');
    return id;
  }, [push]);

  const advanceAgreement = useCallback((agreementId: string) => {
    setAgreements((prev) => updateById(prev, agreementId, (a) => {
      const nextStep = Math.min(4, a.step + 1) as 1 | 2 | 3 | 4;
      return { ...a, step: nextStep, status: nextStep === 4 ? 'AGREED' : a.status };
    }));
    push('Đã chuyển sang bước tiếp theo', 'success');
  }, [push]);

  const setAgreementStatus = useCallback((agreementId: string, status: Agreement['status']) => {
    setAgreements((prev) => updateById(prev, agreementId, (a) => ({ ...a, status })));
    push('Đã cập nhật trạng thái thỏa thuận', 'success');
  }, [push]);

  const toggleUserLock = useCallback((userId: string) => {
    setUsers((prev) => updateById(prev, userId, (u) => ({ ...u, status: u.status === 'ACTIVE' ? 'LOCKED' : 'ACTIVE' })));
    push('Đã cập nhật trạng thái người dùng', 'success');
  }, [push]);

  const addUser = useCallback((data: { name: string; username: string; role: Role }) => {
    const id = 'U-' + Math.random().toString(36).slice(2, 6);
    setUsers((prev) => [{ id, name: data.name, username: data.username, role: data.role, status: 'ACTIVE', lastLogin: '—' }, ...prev]);
    push(`Đã tạo người dùng ${data.name}`, 'success');
  }, [push]);

  const value = useMemo<AppDataCtx>(() => ({
    shipments, contracts, customers, quotes, agreements, users,
    getShipment, getContract, getCustomer,
    addShipment, updateShipmentFields, setChecklistStatus, confirmDelivery, addPayment, amendPayment, issuePXK,
    addContract, addGoodsRow, updateGoodsRow, removeGoodsRow, updateContractField, updatePartyField, generateContractDocument,
    addQuote, setQuoteStatus, addAgreement, advanceAgreement, setAgreementStatus,
    toggleUserLock, addUser,
  }), [shipments, contracts, customers, quotes, agreements, users, getShipment, getContract, getCustomer,
    addShipment, updateShipmentFields, setChecklistStatus, confirmDelivery, addPayment, amendPayment, issuePXK,
    addContract, addGoodsRow, updateGoodsRow, removeGoodsRow, updateContractField, updatePartyField, generateContractDocument,
    addQuote, setQuoteStatus, addAgreement, advanceAgreement, setAgreementStatus, toggleUserLock, addUser]);

  const roleValue = useMemo(() => ({ role, setRole, userName: ROLE_NAMES[role] }), [role]);
  const toastValue = useMemo(() => ({ toasts, push, dismiss }), [toasts, push, dismiss]);

  return (
    <RoleContext.Provider value={roleValue}>
      <ToastContext.Provider value={toastValue}>
        <AppDataContext.Provider value={value}>
          {children}
        </AppDataContext.Provider>
      </ToastContext.Provider>
    </RoleContext.Provider>
  );
}
