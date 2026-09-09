import { useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  ArrowLeft, Edit3, Plus, Trash2, FileCheck2, Download, CheckCircle2, XCircle,
  Package, Wallet, History as HistoryIcon, ClipboardList,
} from 'lucide-react';
import { useAppData } from '../lib/dataContext';
import { formatMoney } from '../lib/mockData';
import Card, { CardTitle, Field } from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import Button from '../components/ui/Button';
import Tabs from '../components/ui/Tabs';
import Modal from '../components/ui/Modal';
import EmptyState from '../components/ui/EmptyState';
import { CONTRACT_STATUS_LABEL, CONTRACT_STATUS_VARIANT, SHIPMENT_STATUS_LABEL, SHIPMENT_STATUS_VARIANT } from '../lib/status';
import type { Party } from '../lib/types';

const REQUIRED_BUYER: (keyof Party)[] = ['legalName', 'address', 'taxCode', 'representative', 'position'];
const REQUIRED_SELLER: (keyof Party)[] = ['legalName', 'address', 'taxCode', 'representative', 'position', 'accountHolder', 'accountNumber', 'bank'];
const PARTY_LABELS: Record<keyof Party, string> = { company: 'Công ty', legalName: 'Tên pháp lý', address: 'Địa chỉ', taxCode: 'MST / Mã pháp lý', representative: 'Người đại diện', position: 'Chức vụ', accountHolder: 'Chủ tài khoản', accountNumber: 'Số tài khoản', bank: 'Ngân hàng' };

export default function ContractDetail() {
  const { id = '' } = useParams();
  const navigate = useNavigate();
  const { getContract, shipments, updatePartyField, addGoodsRow, updateGoodsRow, removeGoodsRow, updateContractField, generateContractDocument } = useAppData();
  const contract = getContract(id);
  const [activeTab, setActiveTab] = useState('info');
  const [editSide, setEditSide] = useState<'buyer' | 'seller' | null>(null);
  const [partyForm, setPartyForm] = useState<Party | null>(null);
  const [genResult, setGenResult] = useState<{ ok: boolean; message: string } | null>(null);
  const [useExistingHdnt, setUseExistingHdnt] = useState(true);

  const linkedShipments = useMemo(() => contract ? shipments.filter((s) => contract.linkedShipmentIds.includes(s.id)) : [], [contract, shipments]);

  const totals = useMemo(() => {
    if (!contract) return { goods: 0, vat: 0, total: 0 };
    const goods = contract.goodsRows.reduce((s, r) => s + r.qty * r.unitPrice, 0);
    const vat = contract.goodsRows.reduce((s, r) => s + r.qty * r.unitPrice * (r.vatRate / 100), 0);
    return { goods, vat, total: goods + vat };
  }, [contract]);

  const route = totals.total >= 50000000 ? 'HDMB' : 'HDNT';

  if (!contract) {
    return <Card><EmptyState message={`Không tìm thấy hợp đồng "${id}".`} action={<Button onClick={() => navigate('/hop-dong')}>Về danh sách Hợp Đồng</Button>} /></Card>;
  }

  function missingFields(side: 'buyer' | 'seller') {
    const party = side === 'buyer' ? contract!.buyer : contract!.seller;
    const required = side === 'buyer' ? REQUIRED_BUYER : REQUIRED_SELLER;
    return required.filter((k) => !party[k]);
  }

  function openEdit(side: 'buyer' | 'seller') {
    setEditSide(side);
    setPartyForm({ ...(side === 'buyer' ? contract!.buyer : contract!.seller) });
  }

  function saveParty() {
    if (!editSide || !partyForm) return;
    updatePartyField(contract!.id, editSide, partyForm);
    setEditSide(null);
  }

  function handleGenerate() {
    const result = generateContractDocument(contract!.id);
    setGenResult(result);
  }

  const readiness = (() => {
    if (route === 'HDMB') {
      if (contract.goodsRows.length > 1) return { ready: false, msg: 'HDMB V1 hỗ trợ tối đa 1 dòng hàng hóa. Vui lòng gộp hoặc tách thành nhiều hợp đồng.' };
      if (!contract.hdmb?.ngayHDMB) return { ready: false, msg: 'Thiếu Ngày HDMB' };
      if (missingFields('buyer').length || missingFields('seller').length) return { ready: false, msg: 'Thiếu thông tin pháp lý Bên mua / Bên bán' };
      return { ready: true, msg: 'Sẵn sàng xuất HDMB' };
    }
    if (!useExistingHdnt && !contract.hdnt?.soHDNT) return { ready: false, msg: 'Thiếu số HDNT' };
    if (!contract.pl?.soPL || !contract.pl?.ngayPL) return { ready: false, msg: 'Thiếu số hoặc ngày Phụ lục (PL)' };
    if (missingFields('buyer').length || missingFields('seller').length) return { ready: false, msg: 'Thiếu thông tin pháp lý Bên mua / Bên bán' };
    return { ready: true, msg: 'Sẵn sàng xuất HDNT + PL' };
  })();

  const tabs = [
    { key: 'info', label: 'Thông Tin Hợp Đồng' },
    { key: 'goods', label: 'Hàng Hóa & Chứng Từ' },
    { key: 'shipments', label: 'Lô Hàng Liên Kết' },
    { key: 'finance', label: 'Tài Chính Hợp Đồng' },
    { key: 'history', label: 'Lịch Sử / Phụ Lục' },
  ];

  return (
    <div>
      <button onClick={() => navigate('/hop-dong')} className="flex items-center gap-1.5 text-[13.5px] font-semibold text-ink-600 hover:text-navy-900 mb-3"><ArrowLeft size={15} /> Quay lại Hợp Đồng</button>

      <Card className="mb-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <div className="flex items-center gap-2.5 mb-1">
              <h1 className="text-[22px] font-extrabold text-navy-900">{contract.id}</h1>
              <Badge variant={CONTRACT_STATUS_VARIANT[contract.status]}>{CONTRACT_STATUS_LABEL[contract.status]}</Badge>
              <Badge variant="neutral" icon={false}>{contract.type}</Badge>
            </div>
            <p className="text-[14px] text-ink-600">{contract.agent} ⇄ {contract.company}</p>
          </div>
          <Field label="Giá trị hợp đồng" value={contract.value ? formatMoney(contract.value, 'VND') : 'Chưa xác định'} />
        </div>
      </Card>

      <Card padded={false} className="mb-4"><Tabs tabs={tabs} active={activeTab} onChange={setActiveTab} /></Card>

      {activeTab === 'info' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <PartyCard title="Bên mua" party={contract.buyer} missing={missingFields('buyer')} onEdit={() => openEdit('buyer')} />
          <PartyCard title="Bên bán / Đại lý" party={contract.seller} missing={missingFields('seller')} onEdit={() => openEdit('seller')} isSeller />
        </div>
      )}

      {activeTab === 'goods' && (
        <div className="space-y-4">
          <Card padded={false} className="overflow-hidden">
            <div className="flex items-center justify-between px-4 sm:px-5 pt-4 sm:pt-5">
              <CardTitle className="mb-0"><Package size={17} className="text-accent-500" /> Dòng hàng hóa</CardTitle>
              <Button size="sm" icon={<Plus size={14} />} onClick={() => addGoodsRow(contract.id)}>THÊM DÒNG HÀNG HÓA</Button>
            </div>
            <div className="overflow-x-auto mt-3">
              <table className="w-full text-left border-collapse min-w-[700px]">
                <thead>
                  <tr className="bg-slate-50 text-[11.5px] text-ink-400 font-bold uppercase tracking-wide">
                    <th className="px-3 py-2.5 w-12">STT</th>
                    <th className="px-3 py-2.5">Mô tả hàng hóa</th>
                    <th className="px-3 py-2.5 w-24">Đơn vị</th>
                    <th className="px-3 py-2.5 w-24">Số lượng</th>
                    <th className="px-3 py-2.5 w-36">Đơn giá chưa VAT</th>
                    <th className="px-3 py-2.5 w-20">VAT</th>
                    <th className="px-3 py-2.5 w-40">Thành tiền</th>
                    <th className="px-3 py-2.5 w-14"></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {contract.goodsRows.map((r) => (
                    <tr key={r.stt}>
                      <td className="px-3 py-2 text-[13.5px] font-bold text-navy-900">{r.stt}</td>
                      <td className="px-3 py-2"><input value={r.desc} onChange={(e) => updateGoodsRow(contract.id, r.stt, { desc: e.target.value })} placeholder="Mô tả hàng hóa" className="w-full h-9 rounded-lg border border-slate-300 px-2 text-[13.5px]" /></td>
                      <td className="px-3 py-2"><input value={r.unit} onChange={(e) => updateGoodsRow(contract.id, r.stt, { unit: e.target.value })} className="w-full h-9 rounded-lg border border-slate-300 px-2 text-[13.5px]" /></td>
                      <td className="px-3 py-2"><input value={r.qty} type="number" onChange={(e) => updateGoodsRow(contract.id, r.stt, { qty: Number(e.target.value) || 0 })} className="w-full h-9 rounded-lg border border-slate-300 px-2 text-[13.5px]" /></td>
                      <td className="px-3 py-2"><input value={r.unitPrice} type="number" onChange={(e) => updateGoodsRow(contract.id, r.stt, { unitPrice: Number(e.target.value) || 0 })} className="w-full h-9 rounded-lg border border-slate-300 px-2 text-[13.5px]" /></td>
                      <td className="px-3 py-2 text-[13.5px] text-ink-600">{r.vatRate}%</td>
                      <td className="px-3 py-2 text-[13.5px] font-bold text-navy-900 whitespace-nowrap">{formatMoney(r.qty * r.unitPrice * (1 + r.vatRate / 100), 'VND')}</td>
                      <td className="px-3 py-2"><button onClick={() => removeGoodsRow(contract.id, r.stt)} className="h-9 w-9 flex items-center justify-center rounded-lg text-danger-500 hover:bg-danger-50"><Trash2 size={15} /></button></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="px-4 sm:px-5 py-4 mt-2 bg-slate-50 grid grid-cols-3 gap-3 text-center">
              <div><div className="text-[12px] text-ink-400 font-medium">Tiền hàng</div><div className="text-[15px] font-extrabold text-navy-900">{formatMoney(totals.goods, 'VND')}</div></div>
              <div><div className="text-[12px] text-ink-400 font-medium">VAT 8%</div><div className="text-[15px] font-extrabold text-navy-900">{formatMoney(totals.vat, 'VND')}</div></div>
              <div><div className="text-[12px] text-ink-400 font-medium">TỔNG SAU VAT</div><div className="text-[17px] font-extrabold text-accent-600">{formatMoney(totals.total, 'VND')}</div></div>
            </div>
          </Card>

          <Card className={route === 'HDMB' ? 'border-accent-500/40 bg-accent-500/5' : 'border-success-500/40 bg-success-50'}>
            <div className="flex items-center gap-2 mb-1">
              <FileCheck2 size={19} className={route === 'HDMB' ? 'text-accent-600' : 'text-success-600'} />
              <span className="text-[15px] font-extrabold text-navy-900">✅ PHƯƠNG ÁN CHỨNG TỪ: {route === 'HDMB' ? 'HDMB (Hợp đồng mua bán)' : 'HDNT + PL (Hợp đồng nguyên tắc + Phụ lục)'}</span>
            </div>
            <p className="text-[13.5px] text-ink-600">Tổng sau VAT {formatMoney(totals.total, 'VND')} {totals.total >= 50000000 ? '≥' : '<'} 50.000.000 ₫ → tự động áp dụng phương án trên.</p>
          </Card>

          {route === 'HDMB' ? (
            <Card>
              <CardTitle>Thông tin HDMB</CardTitle>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <TextField label="Số HDMB *" value={contract.hdmb?.soHDMB || contract.id} onChange={(v) => updateContractField(contract.id, { hdmb: { soHDMB: v, ngayHDMB: contract.hdmb?.ngayHDMB || '' } })} />
                <TextField label="Ngày HDMB *" value={contract.hdmb?.ngayHDMB || ''} placeholder="dd/mm/yyyy" onChange={(v) => updateContractField(contract.id, { hdmb: { soHDMB: contract.hdmb?.soHDMB || contract.id, ngayHDMB: v } })} />
              </div>
            </Card>
          ) : (
            <Card className="space-y-4">
              <CardTitle>Thông tin HDNT (Hợp đồng nguyên tắc)</CardTitle>
              {contract.hdnt?.soHDNT && (
                <label className="flex items-center gap-2.5 bg-success-50 border border-success-500/30 rounded-xl px-3.5 py-3 cursor-pointer">
                  <input type="checkbox" checked={useExistingHdnt} onChange={(e) => setUseExistingHdnt(e.target.checked)} className="h-4 w-4" />
                  <span className="text-[13.5px] font-semibold text-success-600">✅ CÓ THỂ TÁI SỬ DỤNG HDNT {contract.hdnt.soHDNT} (hiệu lực {contract.hdnt.hieuLucTu} - {contract.hdnt.hieuLucDen})</span>
                </label>
              )}
              {(!contract.hdnt?.soHDNT || !useExistingHdnt) && (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <TextField label="Số HDNT *" value={contract.hdnt?.soHDNT || ''} onChange={(v) => updateContractField(contract.id, { hdnt: { soHDNT: v, ngayKy: contract.hdnt?.ngayKy || '', hieuLucTu: contract.hdnt?.hieuLucTu || '', hieuLucDen: contract.hdnt?.hieuLucDen || '' } })} />
                  <TextField label="Ngày ký *" value={contract.hdnt?.ngayKy || ''} placeholder="dd/mm/yyyy" onChange={(v) => updateContractField(contract.id, { hdnt: { soHDNT: contract.hdnt?.soHDNT || '', ngayKy: v, hieuLucTu: contract.hdnt?.hieuLucTu || '', hieuLucDen: contract.hdnt?.hieuLucDen || '' } })} />
                  <TextField label="Hiệu lực từ *" value={contract.hdnt?.hieuLucTu || ''} placeholder="dd/mm/yyyy" onChange={(v) => updateContractField(contract.id, { hdnt: { soHDNT: contract.hdnt?.soHDNT || '', ngayKy: contract.hdnt?.ngayKy || '', hieuLucTu: v, hieuLucDen: contract.hdnt?.hieuLucDen || '' } })} />
                  <TextField label="Hiệu lực đến *" value={contract.hdnt?.hieuLucDen || ''} placeholder="dd/mm/yyyy" onChange={(v) => updateContractField(contract.id, { hdnt: { soHDNT: contract.hdnt?.soHDNT || '', ngayKy: contract.hdnt?.ngayKy || '', hieuLucTu: contract.hdnt?.hieuLucTu || '', hieuLucDen: v } })} />
                </div>
              )}
              <div className="pt-3 border-t border-border grid grid-cols-1 sm:grid-cols-2 gap-4">
                <TextField label="Số PL *" value={contract.pl?.soPL || ''} onChange={(v) => updateContractField(contract.id, { pl: { soPL: v, ngayPL: contract.pl?.ngayPL || '', hdntCha: contract.hdnt?.soHDNT || '' } })} />
                <TextField label="Ngày PL *" value={contract.pl?.ngayPL || ''} placeholder="dd/mm/yyyy" onChange={(v) => updateContractField(contract.id, { pl: { soPL: contract.pl?.soPL || '', ngayPL: v, hdntCha: contract.hdnt?.soHDNT || '' } })} />
              </div>
            </Card>
          )}

          <Card>
            <div className="flex items-center gap-2 mb-3">
              {readiness.ready ? <CheckCircle2 size={19} className="text-success-500" /> : <XCircle size={19} className="text-warning-500" />}
              <span className={`text-[15px] font-bold ${readiness.ready ? 'text-success-600' : 'text-warning-600'}`}>{readiness.ready ? '✅ Sẵn sàng xuất' : `⚠ ${readiness.msg}`}</span>
            </div>
            <Button size="lg" disabled={!readiness.ready} onClick={handleGenerate}>XUẤT CHỨNG TỪ SẴN SÀNG</Button>
            {genResult && (
              genResult.ok ? (
                <div className="mt-4 flex items-center gap-3 bg-success-50 border border-success-500/30 rounded-xl p-4">
                  <CheckCircle2 size={22} className="text-success-500 shrink-0" />
                  <div className="flex-1">
                    <div className="font-bold text-navy-900 text-[14.5px]">✅ ĐÃ TẠO THÀNH CÔNG</div>
                    <div className="text-[13px] text-ink-600 font-mono">{genResult.message}</div>
                  </div>
                  <Button size="sm" icon={<Download size={14} />} onClick={() => alert(`Đang tải "${genResult.message}" (mô phỏng)`)}>⬇ TẢI HỢP ĐỒNG</Button>
                </div>
              ) : (
                <div className="mt-4 bg-danger-50 border border-danger-500/30 rounded-xl p-4 text-[13.5px] text-danger-600 font-medium">⚠ {genResult.message}</div>
              )
            )}
          </Card>
        </div>
      )}

      {activeTab === 'shipments' && (
        <Card>
          <CardTitle><Package size={17} className="text-accent-500" /> Lô hàng liên kết với hợp đồng này</CardTitle>
          {linkedShipments.length === 0 ? (
            <EmptyState message="Chưa có lô hàng nào liên kết với hợp đồng này." action={<Button onClick={() => navigate('/tao-lo-moi')}>➕ Tạo lô mới</Button>} />
          ) : (
            <div className="divide-y divide-border">
              {linkedShipments.map((s) => (
                <div key={s.id} className="flex flex-wrap items-center justify-between gap-3 py-3">
                  <div>
                    <div className="font-bold text-navy-900 text-[14.5px]">{s.id}</div>
                    <div className="text-[13px] text-ink-600">{s.customer}</div>
                  </div>
                  <Badge variant={SHIPMENT_STATUS_VARIANT[s.status]}>{SHIPMENT_STATUS_LABEL[s.status]}</Badge>
                  <div className="text-[13px] text-ink-400">Giao: {s.truckVN.actualDate || 'Chưa giao'}</div>
                  <Badge variant={s.pxk.issued ? 'success' : 'neutral'}>{s.pxk.issued ? `PXK ${s.pxk.soPXK}` : 'Chưa lập PXK'}</Badge>
                  <div className="flex gap-2">
                    <Button size="sm" variant="secondary" onClick={() => navigate(`/lo-hang/${s.id}`)}>MỞ LÔ</Button>
                    <Button size="sm" onClick={() => navigate(`/lo-hang/${s.id}?tab=docs`)}>LÀM PXK</Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      )}

      {activeTab === 'finance' && (
        <Card>
          <CardTitle><Wallet size={17} className="text-accent-500" /> Tài chính tổng hợp theo lô hàng liên kết</CardTitle>
          {linkedShipments.length === 0 ? <EmptyState message="Chưa có dữ liệu tài chính vì hợp đồng chưa liên kết lô hàng nào." /> : (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse min-w-[600px]">
                <thead>
                  <tr className="bg-slate-50 text-[11.5px] text-ink-400 font-bold uppercase tracking-wide">
                    <th className="px-3 py-2.5">Mã lô</th>
                    <th className="px-3 py-2.5">Phải thu</th>
                    <th className="px-3 py-2.5">Đã thu</th>
                    <th className="px-3 py-2.5">Phải trả</th>
                    <th className="px-3 py-2.5">Đã trả</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {linkedShipments.map((s) => (
                    <tr key={s.id}>
                      <td className="px-3 py-2.5 font-bold text-navy-900">{s.id}</td>
                      <td className="px-3 py-2.5 text-[13.5px]">{formatMoney(s.finance.receivable.total, s.finance.receivable.currency)}</td>
                      <td className="px-3 py-2.5 text-[13.5px] text-success-600 font-semibold">{formatMoney(s.finance.receivable.paid, s.finance.receivable.currency)}</td>
                      <td className="px-3 py-2.5 text-[13.5px]">{formatMoney(s.finance.payable.total, s.finance.payable.currency)}</td>
                      <td className="px-3 py-2.5 text-[13.5px] text-navy-700 font-semibold">{formatMoney(s.finance.payable.paid, s.finance.payable.currency)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      )}

      {activeTab === 'history' && (
        <Card>
          <CardTitle><HistoryIcon size={17} className="text-accent-500" /> Lịch sử phát hành / Phụ lục</CardTitle>
          {contract.history.length === 0 ? <EmptyState message="Chưa có chứng từ nào được phát hành cho hợp đồng này." icon={<ClipboardList size={26} />} /> : (
            <div className="divide-y divide-border">
              {contract.history.map((h, i) => (
                <div key={i} className="flex flex-wrap items-center justify-between gap-3 py-3">
                  <div>
                    <div className="font-bold text-navy-900 text-[14.5px]">{h.type} — {h.number} <span className="text-ink-400 font-normal">({h.revision})</span></div>
                    <div className="text-[12.5px] text-ink-400">Tạo bởi {h.createdBy} ngày {h.createdAt}</div>
                  </div>
                  <Badge variant="success">{h.status}</Badge>
                  <div className="flex gap-2">
                    <Button size="sm" variant="secondary" onClick={() => alert(`Xem thông tin ${h.number} (mô phỏng)`)}>Xem thông tin</Button>
                    <Button size="sm" icon={<Download size={13} />} onClick={() => alert(`Đang tải lại ${h.number} (mô phỏng)`)}>Tải lại</Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      )}

      <Modal open={!!editSide} onClose={() => setEditSide(null)} title={`Bổ sung thông tin ${editSide === 'buyer' ? 'Bên mua' : 'Bên bán / Đại lý'}`}>
        {partyForm && (
          <div className="space-y-3.5">
            {(Object.keys(PARTY_LABELS) as (keyof Party)[]).filter((k) => k !== 'company' && (editSide === 'seller' || !['accountHolder', 'accountNumber', 'bank'].includes(k))).map((k) => (
              <TextField key={k} label={PARTY_LABELS[k]} value={partyForm[k] || ''} onChange={(v) => setPartyForm((f) => f && { ...f, [k]: v })} />
            ))}
            <Button full onClick={saveParty}>✅ Lưu thông tin</Button>
          </div>
        )}
      </Modal>
    </div>
  );
}

function PartyCard({ title, party, missing, onEdit, isSeller }: { title: string; party: Party; missing: (keyof Party)[]; onEdit: () => void; isSeller?: boolean }) {
  return (
    <Card>
      <div className="flex items-center justify-between mb-3">
        <CardTitle className="mb-0">{title}</CardTitle>
        <button onClick={onEdit} className="text-[13px] font-semibold text-accent-600 flex items-center gap-1 hover:underline"><Edit3 size={13} /> Bổ sung thông tin</button>
      </div>
      {missing.length > 0 && (
        <div className="mb-3 bg-warning-50 border border-warning-500/30 rounded-xl px-3.5 py-2.5 text-[13px] text-warning-600 font-semibold">
          ⚠ Thiếu {missing.map((m) => PARTY_LABELS[m]).join(', ')}
        </div>
      )}
      <div className="grid grid-cols-2 gap-4">
        <Field label="Công ty" value={party.company} />
        <Field label="Tên pháp lý" value={party.legalName} missing={!party.legalName} />
        <Field label="Địa chỉ" value={party.address} missing={!party.address} />
        <Field label="MST / Mã pháp lý" value={party.taxCode} missing={!party.taxCode} />
        <Field label="Người đại diện" value={party.representative} missing={!party.representative} />
        <Field label="Chức vụ" value={party.position} missing={!party.position} />
        {isSeller && (
          <>
            <Field label="Chủ tài khoản" value={party.accountHolder} missing={!party.accountHolder} />
            <Field label="Số tài khoản" value={party.accountNumber} missing={!party.accountNumber} />
            <Field label="Ngân hàng" value={party.bank} missing={!party.bank} />
          </>
        )}
      </div>
    </Card>
  );
}

function TextField({ label, value, onChange, placeholder }: { label: string; value: string; onChange: (v: string) => void; placeholder?: string }) {
  return (
    <div>
      <div className="text-[12.5px] font-medium text-ink-400 mb-1">{label}</div>
      <input value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder} className="w-full h-11 rounded-xl border border-slate-300 px-3 text-[14px] outline-none focus:border-accent-500" />
    </div>
  );
}
