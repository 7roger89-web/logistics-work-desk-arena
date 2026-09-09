import { useMemo, useState } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import {
  ArrowLeft, Factory, Truck, Boxes, FileOutput, ClipboardList, ShieldCheck,
  Edit3, CheckCircle2, PackageCheck, Wallet, HandCoins, Plus, FileText, Download, ArrowRightCircle,
} from 'lucide-react';
import { useAppData } from '../lib/dataContext';
import { formatMoney } from '../lib/mockData';
import Card, { CardTitle, Field } from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import Button from '../components/ui/Button';
import Tabs from '../components/ui/Tabs';
import Modal from '../components/ui/Modal';
import EmptyState from '../components/ui/EmptyState';
import { SHIPMENT_STATUS_LABEL, SHIPMENT_STATUS_VARIANT, DOC_STATUS_LABEL, DOC_STATUS_VARIANT } from '../lib/status';
import type { Currency, PaymentRecord } from '../lib/types';

const NEXT_TAB: Record<string, string> = { CHO_LAY_HANG: 'pickup', DANG_VAN_CHUYEN: 'pickup', CHO_THONG_QUAN: 'import', CHO_GIAO: 'import', DA_GIAO: 'docs' };

export default function ShipmentDetail() {
  const { id = '' } = useParams();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { getShipment, getContract, updateShipmentFields, setChecklistStatus, confirmDelivery, addPayment, amendPayment, issuePXK } = useAppData();
  const shipment = getShipment(id);
  const [activeTab, setActiveTab] = useState(searchParams.get('tab') || (shipment ? NEXT_TAB[shipment.status] : 'pickup'));

  const [checklistModal, setChecklistModal] = useState<string | null>(null);
  const [checklistNote, setChecklistNote] = useState('');
  const [truckModal, setTruckModal] = useState(false);
  const [truckForm, setTruckForm] = useState({ vehicleType: '', plate: '', driver: '', phone: '' });
  const [truckVNModal, setTruckVNModal] = useState(false);
  const [truckVNForm, setTruckVNForm] = useState({ driver: '', plate: '', scheduledDate: '' });
  const [declModal, setDeclModal] = useState(false);
  const [declForm, setDeclForm] = useState({ declNo: '', regDate: '' });
  const [deliveryConfirmOpen, setDeliveryConfirmOpen] = useState(false);
  const [paymentModalOpen, setPaymentModalOpen] = useState(false);
  const [paymentForm, setPaymentForm] = useState({ type: 'THU' as 'THU' | 'TRA', amount: '', currency: 'VND' as Currency, method: 'Chuyển khoản', note: '' });
  const [amendModal, setAmendModal] = useState<PaymentRecord | null>(null);
  const [amendReason, setAmendReason] = useState('');
  const [pxkForm, setPxkForm] = useState({ location: '', receiver: '', position: '' });

  const contract = shipment?.contractId ? getContract(shipment.contractId) : undefined;

  const currencyGroups = useMemo(() => {
    if (!shipment) return { quoted: {}, actual: {} };
    const group = (lines: typeof shipment.finance.quoted) => lines.reduce<Record<string, number>>((acc, l) => {
      acc[l.currency] = (acc[l.currency] || 0) + l.amount;
      return acc;
    }, {});
    return { quoted: group(shipment.finance.quoted), actual: group(shipment.finance.actual) };
  }, [shipment]);

  if (!shipment) {
    return (
      <Card>
        <EmptyState message={`Không tìm thấy lô hàng "${id}".`} action={<Button onClick={() => navigate('/lo-hang')}>Về danh sách Lô Hàng</Button>} />
      </Card>
    );
  }

  const tabs = [
    { key: 'pickup', label: 'Pickup & Xuất khẩu' },
    { key: 'import', label: 'Import & Giao hàng' },
    { key: 'finance', label: 'Finance / Công nợ' },
    { key: 'docs', label: 'Chứng từ' },
  ];

  return (
    <div>
      <button onClick={() => navigate('/lo-hang')} className="flex items-center gap-1.5 text-[13.5px] font-semibold text-ink-600 hover:text-navy-900 mb-3">
        <ArrowLeft size={15} /> Quay lại Lô Hàng
      </button>

      <Card className="mb-4">
        <div className="flex flex-wrap items-start justify-between gap-3 mb-4">
          <div>
            <div className="flex items-center gap-2.5">
              <h1 className="text-[24px] font-extrabold text-navy-900 tracking-tight">{shipment.id}</h1>
              <Badge variant={SHIPMENT_STATUS_VARIANT[shipment.status]}>{SHIPMENT_STATUS_LABEL[shipment.status]}</Badge>
            </div>
            <p className="text-[14px] text-ink-600 mt-1">{shipment.customer}</p>
          </div>
          <div className="text-right text-[12.5px] text-ink-400">Cập nhật cuối<div className="text-[13.5px] font-semibold text-ink-600">{shipment.updatedAt}</div></div>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4 pt-4 border-t border-border">
          <Field label="Tuyến" value={shipment.route} />
          <Field label="Cửa khẩu" value={shipment.border} />
          <Field label="Hợp đồng" value={shipment.contractNo ? <button onClick={() => navigate(`/hop-dong/${shipment.contractId}`)} className="text-accent-600 hover:underline">{shipment.contractNo}</button> : undefined} missing={!shipment.contractNo} />
          <Field label="Sale phụ trách" value={shipment.sale} />
          <Field label="Support phụ trách" value={shipment.support} />
          <Field label="Trạng thái" value={SHIPMENT_STATUS_LABEL[shipment.status]} />
        </div>
      </Card>

      <div className="mb-4 rounded-2xl border border-warning-500/30 bg-warning-50 p-4 flex flex-col sm:flex-row sm:items-center gap-3 justify-between">
        <div className="flex items-start gap-3">
          <span className="mt-0.5 shrink-0 h-8 w-8 rounded-full bg-warning-500 text-white flex items-center justify-center font-bold text-[15px]">!</span>
          <div>
            <div className="text-[12px] font-bold text-warning-600 uppercase tracking-wide">Việc tiếp theo</div>
            <div className="text-[15.5px] font-bold text-navy-900 leading-snug">{shipment.nextAction}</div>
          </div>
        </div>
        <Button variant="primary" icon={<ArrowRightCircle size={17} />} onClick={() => setActiveTab(NEXT_TAB[shipment.status])} className="shrink-0">ĐI TỚI BƯỚC NÀY</Button>
      </div>

      <Card padded={false} className="mb-4">
        <Tabs tabs={tabs} active={activeTab} onChange={setActiveTab} />
      </Card>

      {activeTab === 'pickup' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <Card>
            <CardTitle><Factory size={17} className="text-accent-500" /> Nhà máy</CardTitle>
            <div className="grid grid-cols-2 gap-4">
              <Field label="Tên nhà máy" value={shipment.factory.name} />
              <Field label="Thời gian lấy hàng" value={shipment.factory.pickupTime} />
              <Field label="Địa chỉ" value={shipment.factory.address} />
              <Field label="Người liên hệ" value={shipment.factory.contact} />
              <Field label="Điện thoại" value={shipment.factory.phone} />
            </div>
          </Card>

          <Card>
            <div className="flex items-center justify-between mb-3">
              <CardTitle className="mb-0"><Truck size={17} className="text-accent-500" /> Xe TQ</CardTitle>
              {!shipment.truckCN.plate && <button onClick={() => { setTruckForm({ vehicleType: shipment.truckCN.vehicleType, plate: '', driver: '', phone: '' }); setTruckModal(true); }} className="text-[13px] font-semibold text-accent-600 flex items-center gap-1 hover:underline"><Edit3 size={13} /> Bổ sung thông tin</button>}
            </div>
            <div className="grid grid-cols-2 gap-4">
              <Field label="Loại / kích thước xe" value={shipment.truckCN.vehicleType} />
              <Field label="Biển số" value={shipment.truckCN.plate} missing={!shipment.truckCN.plate} />
              <Field label="Tài xế" value={shipment.truckCN.driver} missing={!shipment.truckCN.driver} />
              <Field label="Điện thoại" value={shipment.truckCN.phone} missing={!shipment.truckCN.phone} />
              <Field label="Ngày dự kiến" value={shipment.truckCN.etaDate} />
              <Field label="Ngày thực tế" value={shipment.truckCN.actualDate} missing={!shipment.truckCN.actualDate} />
            </div>
          </Card>

          <Card>
            <CardTitle><Boxes size={17} className="text-accent-500" /> Hàng hoá</CardTitle>
            <div className="grid grid-cols-2 gap-4">
              <Field label="Số kiện" value={shipment.goods.packages} />
              <Field label="Trọng lượng" value={`${shipment.goods.weightKg.toLocaleString('vi-VN')} kg`} />
              <Field label="Kích thước" value={shipment.goods.dimensions} />
              <Field label="CBM" value={`${shipment.goods.cbm} m³`} />
              <Field label="Loại hàng" value={shipment.goods.goodsType} />
              <Field label="Ghi chú" value={shipment.goods.note || 'Không có'} />
            </div>
          </Card>

          <Card>
            <CardTitle><FileOutput size={17} className="text-accent-500" /> Xuất khẩu</CardTitle>
            <div className="grid grid-cols-2 gap-4 mb-3">
              <Field label="Cửa khẩu" value={shipment.exportInfo.border} />
              <Field label="Đơn vị khai báo" value={shipment.exportInfo.declUnit} />
              <Field label="Ngày dự kiến" value={shipment.exportInfo.etaDate} missing={!shipment.exportInfo.etaDate} />
              <Field label="Ngày thực tế" value={shipment.exportInfo.actualDate} missing={!shipment.exportInfo.actualDate} />
            </div>
            <Badge variant={shipment.exportInfo.status === 'DA_THONG_QUAN' ? 'success' : shipment.exportInfo.status === 'DANG_KHAI' ? 'warning' : 'neutral'}>
              {shipment.exportInfo.status === 'DA_THONG_QUAN' ? 'Đã thông quan' : shipment.exportInfo.status === 'DANG_KHAI' ? 'Đang khai báo' : 'Chưa khai báo'}
            </Badge>
          </Card>

          <Card className="lg:col-span-2">
            <CardTitle><ClipboardList size={17} className="text-accent-500" /> Checklist chứng từ xuất khẩu</CardTitle>
            <div className="divide-y divide-border">
              {shipment.checklist.map((c) => (
                <div key={c.name} className="flex flex-wrap items-center justify-between gap-2 py-3">
                  <div>
                    <div className="text-[14.5px] font-semibold text-navy-900">{c.name}</div>
                    {c.note && <div className="text-[12.5px] text-ink-400 mt-0.5">{c.note}</div>}
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant={DOC_STATUS_VARIANT[c.status]}>{DOC_STATUS_LABEL[c.status]}</Badge>
                    {c.status !== 'DU' && (
                      <Button size="sm" variant="secondary" icon={<Edit3 size={13} />} onClick={() => { setChecklistModal(c.name); setChecklistNote(''); }}>Bổ sung thông tin</Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>
      )}

      {activeTab === 'import' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <Card>
            <div className="flex items-center justify-between mb-3">
              <CardTitle className="mb-0"><ShieldCheck size={17} className="text-accent-500" /> Thông quan nhập khẩu</CardTitle>
              {!shipment.importInfo.declNo && <button onClick={() => { setDeclForm({ declNo: '', regDate: '' }); setDeclModal(true); }} className="text-[13px] font-semibold text-accent-600 flex items-center gap-1 hover:underline"><Edit3 size={13} /> Bổ sung thông tin</button>}
            </div>
            <div className="grid grid-cols-2 gap-4 mb-3">
              <Field label="Cửa khẩu VN" value={shipment.importInfo.borderVN} />
              <Field label="Số tờ khai" value={shipment.importInfo.declNo} missing={!shipment.importInfo.declNo} />
              <Field label="Ngày đăng ký" value={shipment.importInfo.regDate} missing={!shipment.importInfo.regDate} />
              <Field label="Ngày thông quan" value={shipment.importInfo.clearDate} missing={!shipment.importInfo.clearDate} />
              <Field label="Thuế nhập khẩu" value={shipment.importInfo.taxAmount ? formatMoney(shipment.importInfo.taxAmount, 'VND') : undefined} missing={!shipment.importInfo.taxAmount} />
              <Field label="VAT" value={shipment.importInfo.vatAmount ? formatMoney(shipment.importInfo.vatAmount, 'VND') : undefined} missing={!shipment.importInfo.vatAmount} />
            </div>
            <div className="flex items-center gap-2 flex-wrap">
              <Badge variant={shipment.importInfo.inspected ? 'warning' : 'neutral'}>{shipment.importInfo.inspected ? 'Có kiểm hoá' : 'Không kiểm hoá'}</Badge>
              <Badge variant={DOC_STATUS_VARIANT[shipment.importInfo.licenseStatus]}>Giấy phép: {DOC_STATUS_LABEL[shipment.importInfo.licenseStatus]}</Badge>
            </div>
          </Card>

          <Card>
            <div className="flex items-center justify-between mb-3">
              <CardTitle className="mb-0"><Truck size={17} className="text-accent-500" /> Vận chuyển VN</CardTitle>
              {!shipment.truckVN.driver && <button onClick={() => { setTruckVNForm({ driver: '', plate: '', scheduledDate: shipment.truckVN.scheduledDate }); setTruckVNModal(true); }} className="text-[13px] font-semibold text-accent-600 flex items-center gap-1 hover:underline"><Edit3 size={13} /> Bổ sung thông tin</button>}
            </div>
            <div className="grid grid-cols-2 gap-4">
              <Field label="Tài xế" value={shipment.truckVN.driver} missing={!shipment.truckVN.driver} />
              <Field label="Biển số" value={shipment.truckVN.plate} missing={!shipment.truckVN.plate} />
              <Field label="Địa chỉ giao" value={shipment.truckVN.address} />
              <Field label="Người nhận" value={shipment.truckVN.receiver} />
              <Field label="Điện thoại" value={shipment.truckVN.phone} />
              <Field label="Lịch giao" value={shipment.truckVN.scheduledDate} missing={!shipment.truckVN.scheduledDate} />
              <Field label="Ngày giao thực tế" value={shipment.truckVN.actualDate} missing={!shipment.truckVN.actualDate} />
            </div>
          </Card>

          <Card className="lg:col-span-2">
            {shipment.pxk.deliveredDone ? (
              <div className="flex items-center gap-3 bg-success-50 border border-success-500/30 rounded-xl p-4">
                <CheckCircle2 size={24} className="text-success-500 shrink-0" />
                <div>
                  <div className="font-bold text-navy-900 text-[15px]">Đã xác nhận giao hàng thành công</div>
                  <div className="text-[13px] text-ink-600">Ngày giao thực tế: {shipment.pxk.deliveryDate}. Có thể lập phiếu xuất kho tại tab Chứng từ.</div>
                </div>
                <Button size="sm" variant="secondary" className="ml-auto shrink-0" onClick={() => setActiveTab('docs')}>Đi tới Chứng từ</Button>
              </div>
            ) : (
              <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
                <div>
                  <div className="font-bold text-navy-900 text-[15.5px]">Hàng đã tới điểm giao?</div>
                  <div className="text-[13.5px] text-ink-600">Xác nhận khi tài xế đã giao hàng thành công cho người nhận để hoàn tất lô hàng.</div>
                </div>
                <Button size="lg" variant="success" icon={<PackageCheck size={19} />} onClick={() => setDeliveryConfirmOpen(true)} className="shrink-0 w-full sm:w-auto">✅ XÁC NHẬN ĐÃ GIAO HÀNG</Button>
              </div>
            )}
          </Card>
        </div>
      )}

      {activeTab === 'finance' && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card>
              <CardTitle className="text-accent-600">📘 BÁO GIÁ / DỰ KIẾN</CardTitle>
              <div className="divide-y divide-border">
                {shipment.finance.quoted.map((l, i) => (
                  <div key={i} className="flex items-center justify-between py-2 text-[14px]">
                    <span className="text-ink-600">{l.label}</span>
                    <span className="font-semibold text-navy-900">{formatMoney(l.amount, l.currency)}</span>
                  </div>
                ))}
              </div>
              <div className="mt-3 pt-3 border-t border-border space-y-1">
                {Object.entries(currencyGroups.quoted).map(([cur, amt]) => (
                  <div key={cur} className="flex justify-between text-[13.5px] font-bold text-navy-900"><span>Tổng ({cur})</span><span>{formatMoney(amt, cur)}</span></div>
                ))}
              </div>
            </Card>
            <Card>
              <CardTitle className="text-navy-900">📗 THỰC TẾ</CardTitle>
              {shipment.finance.actual.length === 0 ? (
                <EmptyState message="Chưa có chi phí thực tế nào được ghi nhận cho lô hàng này." />
              ) : (
                <>
                  <div className="divide-y divide-border">
                    {shipment.finance.actual.map((l, i) => (
                      <div key={i} className="flex items-center justify-between py-2 text-[14px]">
                        <span className="text-ink-600">{l.label}</span>
                        <span className="font-semibold text-navy-900">{formatMoney(l.amount, l.currency)}</span>
                      </div>
                    ))}
                  </div>
                  <div className="mt-3 pt-3 border-t border-border space-y-1">
                    {Object.entries(currencyGroups.actual).map(([cur, amt]) => (
                      <div key={cur} className="flex justify-between text-[13.5px] font-bold text-navy-900"><span>Tổng ({cur})</span><span>{formatMoney(amt, cur)}</span></div>
                    ))}
                  </div>
                </>
              )}
            </Card>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card>
              <CardTitle><Wallet size={17} className="text-success-500" /> Phải thu khách hàng</CardTitle>
              <MoneyProgress total={shipment.finance.receivable.total} paid={shipment.finance.receivable.paid} currency={shipment.finance.receivable.currency} tone="success" />
            </Card>
            <Card>
              <CardTitle><HandCoins size={17} className="text-navy-700" /> Phải trả đại lý</CardTitle>
              <MoneyProgress total={shipment.finance.payable.total} paid={shipment.finance.payable.paid} currency={shipment.finance.payable.currency} tone="navy" />
            </Card>
          </div>

          <Card>
            <div className="flex items-center justify-between mb-3">
              <CardTitle className="mb-0">Lịch sử thanh toán</CardTitle>
              <Button size="sm" icon={<Plus size={14} />} onClick={() => { setPaymentForm({ type: 'THU', amount: '', currency: 'VND', method: 'Chuyển khoản', note: '' }); setPaymentModalOpen(true); }}>GHI NHẬN THANH TOÁN</Button>
            </div>
            {shipment.finance.history.length === 0 ? (
              <EmptyState message="Chưa có giao dịch nào được ghi nhận." />
            ) : (
              <div className="space-y-2">
                {shipment.finance.history.map((p) => (
                  <div key={p.id} className="flex flex-wrap items-center gap-3 justify-between py-2.5 border-b border-border last:border-0">
                    <div className="flex items-center gap-2.5">
                      <Badge variant={p.type === 'THU' ? 'success' : 'warning'}>{p.type === 'THU' ? 'Thu' : 'Trả'}</Badge>
                      <div>
                        <div className="text-[14px] font-bold text-navy-900">{formatMoney(p.amount, p.currency)}</div>
                        <div className="text-[12.5px] text-ink-400">{p.date} · {p.method} · {p.recordedBy}{p.note ? ` · ${p.note}` : ''}</div>
                        {p.amended && <div className="text-[12px] text-warning-600 font-semibold mt-0.5">✏️ Đã điều chỉnh: {p.amendReason}</div>}
                      </div>
                    </div>
                    <Button size="sm" variant="secondary" icon={<Edit3 size={13} />} onClick={() => { setAmendModal(p); setAmendReason(''); }}>Điều chỉnh</Button>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>
      )}

      {activeTab === 'docs' && (
        <div className="space-y-4">
          <Card>
            <CardTitle><FileText size={17} className="text-accent-500" /> Hợp đồng liên kết</CardTitle>
            {contract ? (
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 flex-1">
                  <Field label="Số hợp đồng" value={contract.id} />
                  <Field label="Loại" value={contract.type} />
                  <Field label="Đại lý" value={contract.agent} />
                  <Field label="Giá trị" value={formatMoney(contract.value, 'VND')} />
                </div>
                <div className="flex gap-2 shrink-0">
                  <Button size="sm" variant="secondary" onClick={() => navigate(`/hop-dong/${contract.id}`)}>MỞ HỢP ĐỒNG</Button>
                  <Button size="sm" icon={<Download size={14} />} onClick={() => alert(`Đang tải "${contract.lastGeneratedFile || contract.id + '.pdf'}" (mô phỏng)`)}>TẢI HỢP ĐỒNG</Button>
                </div>
              </div>
            ) : (
              <EmptyState message="Lô hàng chưa liên kết hợp đồng nào. Vui lòng tạo hoặc gắn hợp đồng để có căn cứ xuất chứng từ." action={<Button onClick={() => navigate('/hop-dong')}>Đi tới Hợp Đồng</Button>} />
            )}
          </Card>

          <Card>
            <CardTitle><ClipboardList size={17} className="text-accent-500" /> Phiếu xuất kho (PXK)</CardTitle>
            {!shipment.pxk.deliveredDone ? (
              <div className="flex items-start gap-3 bg-warning-50 border border-warning-500/30 rounded-xl p-4">
                <span className="text-warning-500 font-bold text-[18px] shrink-0">⚠</span>
                <div className="flex-1">
                  <div className="font-bold text-navy-900 text-[14.5px]">Chưa thể lập PXK vì lô chưa xác nhận giao hàng</div>
                  <div className="text-[13px] text-ink-600 mt-0.5">Vui lòng xác nhận giao hàng ở tab Import & Giao hàng trước khi lập phiếu xuất kho.</div>
                </div>
                <Button size="sm" variant="secondary" onClick={() => setActiveTab('import')} className="shrink-0">Đi tới Import & Giao hàng</Button>
              </div>
            ) : shipment.pxk.issued ? (
              <div className="space-y-3">
                <div className="flex items-center gap-2 text-success-600 font-bold text-[14.5px]"><CheckCircle2 size={18} /> ĐÃ XUẤT PHIẾU XUẤT KHO</div>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                  <Field label="Số PXK" value={shipment.pxk.soPXK} />
                  <Field label="Ngày PXK" value={shipment.pxk.ngayPXK} />
                  <Field label="Nguồn HDMB/PL" value={shipment.pxk.sourceDoc} />
                  <Field label="Địa điểm nhận" value={shipment.pxk.location} />
                  <Field label="Người nhận" value={shipment.pxk.receiver} />
                  <Field label="Chức vụ" value={shipment.pxk.position} />
                </div>
                <Button size="sm" icon={<Download size={14} />} onClick={() => alert(`Đang tải "${shipment.pxk.soPXK}.pdf" (mô phỏng)`)}>⬇ Tải phiếu xuất kho</Button>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <div className="text-[12.5px] font-medium text-ink-400 mb-1">Đã giao hàng xong</div>
                    <Badge variant="success">Đã giao ngày {shipment.pxk.deliveryDate}</Badge>
                  </div>
                  <LabeledInput label="Địa điểm nhận *" value={pxkForm.location} onChange={(v) => setPxkForm((f) => ({ ...f, location: v }))} placeholder={shipment.truckVN.address} />
                  <LabeledInput label="Người nhận *" value={pxkForm.receiver} onChange={(v) => setPxkForm((f) => ({ ...f, receiver: v }))} placeholder={shipment.truckVN.receiver} />
                  <LabeledInput label="Chức vụ *" value={pxkForm.position} onChange={(v) => setPxkForm((f) => ({ ...f, position: v }))} placeholder="Ví dụ: Thủ kho" />
                  <Field label="Nguồn HDMB/PL" value={contract?.hdmb?.soHDMB || contract?.pl?.soPL || contract?.id || shipment.contractNo} />
                </div>
                <Button icon={<FileText size={17} />} onClick={() => issuePXK(shipment.id, {
                  location: pxkForm.location || shipment.truckVN.address,
                  receiver: pxkForm.receiver || shipment.truckVN.receiver,
                  position: pxkForm.position || 'Thủ kho',
                  sourceDoc: contract?.hdmb?.soHDMB || contract?.pl?.soPL || contract?.id || shipment.contractNo || '',
                })}>XUẤT PHIẾU XUẤT KHO</Button>
              </div>
            )}
          </Card>
        </div>
      )}

      {/* --- Modals --- */}
      <Modal open={!!checklistModal} onClose={() => setChecklistModal(null)} title={`Bổ sung thông tin: ${checklistModal || ''}`}>
        <div className="space-y-4">
          <p className="text-[14px] text-ink-600">Xác nhận chứng từ "{checklistModal}" đã được bổ sung đầy đủ. Ghi chú thêm nếu cần.</p>
          <LabeledTextarea label="Ghi chú" value={checklistNote} onChange={setChecklistNote} placeholder="Ví dụ: Đã nhận bản scan từ nhà máy qua email" />
          <Button full onClick={() => { if (checklistModal) setChecklistStatus(shipment.id, checklistModal, 'DU', checklistNote); setChecklistModal(null); }}>✅ Xác nhận đã bổ sung</Button>
        </div>
      </Modal>

      <Modal open={truckModal} onClose={() => setTruckModal(false)} title="Bổ sung thông tin xe TQ">
        <div className="space-y-4">
          <LabeledInput label="Loại / kích thước xe *" value={truckForm.vehicleType} onChange={(v) => setTruckForm((f) => ({ ...f, vehicleType: v }))} />
          <LabeledInput label="Biển số xe *" value={truckForm.plate} onChange={(v) => setTruckForm((f) => ({ ...f, plate: v }))} placeholder="Ví dụ: 粤B-88231" />
          <LabeledInput label="Tài xế *" value={truckForm.driver} onChange={(v) => setTruckForm((f) => ({ ...f, driver: v }))} />
          <LabeledInput label="Điện thoại *" value={truckForm.phone} onChange={(v) => setTruckForm((f) => ({ ...f, phone: v }))} />
          <Button full disabled={!truckForm.plate || !truckForm.driver} onClick={() => { updateShipmentFields(shipment.id, { truckCN: { ...shipment.truckCN, ...truckForm } }); setTruckModal(false); }}>✅ Lưu thông tin xe</Button>
        </div>
      </Modal>

      <Modal open={truckVNModal} onClose={() => setTruckVNModal(false)} title="Bổ sung thông tin xe VN">
        <div className="space-y-4">
          <LabeledInput label="Tài xế *" value={truckVNForm.driver} onChange={(v) => setTruckVNForm((f) => ({ ...f, driver: v }))} />
          <LabeledInput label="Biển số xe *" value={truckVNForm.plate} onChange={(v) => setTruckVNForm((f) => ({ ...f, plate: v }))} placeholder="Ví dụ: 29C-556.12" />
          <LabeledInput label="Lịch giao dự kiến" value={truckVNForm.scheduledDate} onChange={(v) => setTruckVNForm((f) => ({ ...f, scheduledDate: v }))} placeholder="dd/mm/yyyy" />
          <Button full disabled={!truckVNForm.driver || !truckVNForm.plate} onClick={() => { updateShipmentFields(shipment.id, { truckVN: { ...shipment.truckVN, ...truckVNForm } }); setTruckVNModal(false); }}>✅ Lưu thông tin xe</Button>
        </div>
      </Modal>

      <Modal open={declModal} onClose={() => setDeclModal(false)} title="Bổ sung số tờ khai hải quan">
        <div className="space-y-4">
          <LabeledInput label="Số tờ khai *" value={declForm.declNo} onChange={(v) => setDeclForm((f) => ({ ...f, declNo: v }))} />
          <LabeledInput label="Ngày đăng ký *" value={declForm.regDate} onChange={(v) => setDeclForm((f) => ({ ...f, regDate: v }))} placeholder="dd/mm/yyyy" />
          <Button full disabled={!declForm.declNo || !declForm.regDate} onClick={() => { updateShipmentFields(shipment.id, { importInfo: { ...shipment.importInfo, ...declForm } }); setDeclModal(false); }}>✅ Lưu thông tin tờ khai</Button>
        </div>
      </Modal>

      <Modal open={deliveryConfirmOpen} onClose={() => setDeliveryConfirmOpen(false)} title="Xác nhận đã giao hàng">
        <div className="space-y-4">
          <p className="text-[14.5px] text-ink-600">Bạn xác nhận lô <b className="text-navy-900">{shipment.id}</b> đã được giao thành công cho <b className="text-navy-900">{shipment.truckVN.receiver || 'người nhận'}</b>? Trạng thái lô sẽ chuyển sang <b>Đã giao</b> và không thể hoàn tác trực tiếp.</p>
          <div className="flex gap-3">
            <Button variant="secondary" full onClick={() => setDeliveryConfirmOpen(false)}>Huỷ</Button>
            <Button variant="success" full icon={<CheckCircle2 size={17} />} onClick={() => { confirmDelivery(shipment.id); setDeliveryConfirmOpen(false); }}>Xác nhận đã giao</Button>
          </div>
        </div>
      </Modal>

      <Modal open={paymentModalOpen} onClose={() => setPaymentModalOpen(false)} title="Ghi nhận thanh toán">
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <button onClick={() => setPaymentForm((f) => ({ ...f, type: 'THU' }))} className={`h-11 rounded-xl font-bold text-[14px] border ${paymentForm.type === 'THU' ? 'bg-success-500 text-white border-success-500' : 'bg-white text-ink-600 border-slate-300'}`}>Khoản Thu</button>
            <button onClick={() => setPaymentForm((f) => ({ ...f, type: 'TRA' }))} className={`h-11 rounded-xl font-bold text-[14px] border ${paymentForm.type === 'TRA' ? 'bg-navy-900 text-white border-navy-900' : 'bg-white text-ink-600 border-slate-300'}`}>Khoản Trả</button>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <LabeledInput label="Số tiền *" value={paymentForm.amount} onChange={(v) => setPaymentForm((f) => ({ ...f, amount: v.replace(/[^0-9]/g, '') }))} placeholder="0" />
            <div>
              <div className="text-[12.5px] font-medium text-ink-400 mb-1">Đơn vị tiền</div>
              <select value={paymentForm.currency} onChange={(e) => setPaymentForm((f) => ({ ...f, currency: e.target.value as Currency }))} className="w-full h-11 rounded-xl border border-slate-300 px-3 text-[14px]">
                <option value="VND">VND</option>
                <option value="USD">USD</option>
                <option value="CNY">CNY</option>
              </select>
            </div>
          </div>
          <div>
            <div className="text-[12.5px] font-medium text-ink-400 mb-1">Phương thức</div>
            <select value={paymentForm.method} onChange={(e) => setPaymentForm((f) => ({ ...f, method: e.target.value }))} className="w-full h-11 rounded-xl border border-slate-300 px-3 text-[14px]">
              <option>Chuyển khoản</option>
              <option>Tiền mặt</option>
              <option>Khác</option>
            </select>
          </div>
          <LabeledInput label="Ghi chú" value={paymentForm.note} onChange={(v) => setPaymentForm((f) => ({ ...f, note: v }))} placeholder="Ví dụ: Tạm ứng 30%" />
          <Button full disabled={!paymentForm.amount} onClick={() => {
            addPayment(shipment.id, { type: paymentForm.type, amount: Number(paymentForm.amount), currency: paymentForm.currency, method: paymentForm.method, note: paymentForm.note, date: new Date().toLocaleDateString('vi-VN'), recordedBy: 'Bạn' });
            setPaymentModalOpen(false);
          }}>✅ Ghi nhận thanh toán</Button>
        </div>
      </Modal>

      <Modal open={!!amendModal} onClose={() => setAmendModal(null)} title="Điều chỉnh giao dịch">
        <div className="space-y-4">
          <p className="text-[13.5px] text-ink-600">Giao dịch gốc không bị xoá — mọi điều chỉnh sẽ được lưu vết trong lịch sử để đảm bảo minh bạch đối soát.</p>
          {amendModal && <div className="bg-slate-50 rounded-xl p-3 text-[14px] font-semibold text-navy-900">{formatMoney(amendModal.amount, amendModal.currency)} · {amendModal.date}</div>}
          <LabeledTextarea label="Lý do điều chỉnh *" value={amendReason} onChange={setAmendReason} placeholder="Ví dụ: Khách chuyển thừa 500.000đ, đã đối chiếu lại với kế toán" />
          <Button full disabled={!amendReason} onClick={() => { if (amendModal) amendPayment(shipment.id, amendModal.id, amendReason); setAmendModal(null); }}>✅ Lưu điều chỉnh</Button>
        </div>
      </Modal>
    </div>
  );
}

function MoneyProgress({ total, paid, currency, tone }: { total: number; paid: number; currency: string; tone: 'success' | 'navy' }) {
  const remaining = Math.max(0, total - paid);
  const pct = total > 0 ? Math.min(100, (paid / total) * 100) : 0;
  const barColor = tone === 'success' ? 'bg-success-500' : 'bg-navy-700';
  return (
    <div className="space-y-3">
      <div className="grid grid-cols-3 gap-3 text-center">
        <div><div className="text-[12px] text-ink-400 font-medium">Tổng</div><div className="text-[16px] font-extrabold text-navy-900">{formatMoney(total, currency)}</div></div>
        <div><div className="text-[12px] text-ink-400 font-medium">Đã thanh toán</div><div className="text-[16px] font-extrabold text-success-600">{formatMoney(paid, currency)}</div></div>
        <div><div className="text-[12px] text-ink-400 font-medium">Còn lại</div><div className="text-[16px] font-extrabold text-danger-600">{formatMoney(remaining, currency)}</div></div>
      </div>
      <div className="h-2.5 rounded-full bg-slate-100 overflow-hidden">
        <div className={`h-full ${barColor}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

function LabeledInput({ label, value, onChange, placeholder }: { label: string; value: string; onChange: (v: string) => void; placeholder?: string }) {
  return (
    <div>
      <div className="text-[12.5px] font-medium text-ink-400 mb-1">{label}</div>
      <input value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder} className="w-full h-11 rounded-xl border border-slate-300 px-3 text-[14px] outline-none focus:border-accent-500" />
    </div>
  );
}
function LabeledTextarea({ label, value, onChange, placeholder }: { label: string; value: string; onChange: (v: string) => void; placeholder?: string }) {
  return (
    <div>
      <div className="text-[12.5px] font-medium text-ink-400 mb-1">{label}</div>
      <textarea value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder} rows={3} className="w-full rounded-xl border border-slate-300 px-3 py-2.5 text-[14px] outline-none focus:border-accent-500 resize-none" />
    </div>
  );
}
