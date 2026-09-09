import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Send, CheckCircle2, Handshake, X } from 'lucide-react';
import { useAppData } from '../lib/dataContext';
import { ROUTES, BORDERS, GOODS_TYPES, formatMoney } from '../lib/mockData';
import PageHeader from '../components/ui/PageHeader';
import Card, { CardTitle } from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import Button from '../components/ui/Button';
import { QUOTE_STATUS_LABEL, QUOTE_STATUS_VARIANT } from '../lib/status';
import type { Currency } from '../lib/types';

const COST_LABELS = ['Vận tải TQ', 'Xuất khẩu', 'Cửa khẩu', 'Thuế', 'Vận tải VN', 'Dịch vụ', 'Ủy thác', 'Khác'];
const INCOTERMS = ['EXW', 'FOB', 'DAP', 'DDP'];

export default function Quotes() {
  const navigate = useNavigate();
  const { customers, quotes, addQuote, setQuoteStatus, addAgreement } = useAppData();
  const [showBuilder, setShowBuilder] = useState(false);

  const [customerId, setCustomerId] = useState('');
  const [incoterm, setIncoterm] = useState(INCOTERMS[2]);
  const [pickupPoint, setPickupPoint] = useState('');
  const [border, setBorder] = useState(BORDERS[0]);
  const [deliveryPoint, setDeliveryPoint] = useState('');
  const [goodsType, setGoodsType] = useState(GOODS_TYPES[0]);
  const [weightKg, setWeightKg] = useState('');
  const [cbm, setCbm] = useState('');
  const [costs, setCosts] = useState<{ label: string; amount: string; currency: Currency }[]>(
    COST_LABELS.map((label) => ({ label, amount: '', currency: 'VND' as Currency })),
  );
  const [sellPrice, setSellPrice] = useState('');

  const customer = customers.find((c) => c.id === customerId);

  const costGroups = useMemo(() => costs.reduce<Record<string, number>>((acc, c) => {
    const n = Number(c.amount) || 0;
    if (n > 0) acc[c.currency] = (acc[c.currency] || 0) + n;
    return acc;
  }, {}), [costs]);

  const vndCost = costGroups['VND'] || 0;
  const sell = Number(sellPrice) || 0;
  const profit = sell - vndCost;
  const margin = sell > 0 ? (profit / sell) * 100 : 0;

  function resetBuilder() {
    setCustomerId(''); setPickupPoint(''); setDeliveryPoint(''); setWeightKg(''); setCbm(''); setSellPrice('');
    setCosts(COST_LABELS.map((label) => ({ label, amount: '', currency: 'VND' as Currency })));
    setShowBuilder(false);
  }

  function handleCreate() {
    if (!customer) return;
    addQuote({
      customerId: customer.id,
      customer: customer.name,
      incoterm, pickupPoint, border, deliveryPoint, goodsType,
      weightKg: Number(weightKg) || 0,
      cbm: Number(cbm) || 0,
      costs: costs.filter((c) => Number(c.amount) > 0).map((c) => ({ label: c.label, amount: Number(c.amount), currency: c.currency })),
      sellPrice: sell,
      currency: 'VND',
    });
    resetBuilder();
  }

  return (
    <div>
      <PageHeader
        title="Kinh Doanh & Báo Giá"
        subtitle="Xây dựng báo giá dự kiến, theo dõi trạng thái gửi khách và chốt đơn."
        actions={<Button icon={<Plus size={17} />} onClick={() => setShowBuilder((v) => !v)}>{showBuilder ? 'Đóng biểu mẫu' : '➕ Tạo báo giá mới'}</Button>}
      />

      {showBuilder && (
        <Card className="mb-5 space-y-5">
          <div className="flex items-center justify-between">
            <CardTitle className="mb-0 text-accent-600">📘 BÁO GIÁ / DỰ KIẾN — Biểu mẫu tạo mới</CardTitle>
            <button onClick={resetBuilder} className="text-ink-400 hover:text-ink-600"><X size={18} /></button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="lg:col-span-2">
              <div className="text-[12.5px] font-medium text-ink-400 mb-1">Khách hàng *</div>
              <select value={customerId} onChange={(e) => setCustomerId(e.target.value)} className="w-full h-11 rounded-xl border border-slate-300 px-3 text-[14px]">
                <option value="">— Chọn khách hàng —</option>
                {customers.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            </div>
            <div>
              <div className="text-[12.5px] font-medium text-ink-400 mb-1">Incoterm</div>
              <select value={incoterm} onChange={(e) => setIncoterm(e.target.value)} className="w-full h-11 rounded-xl border border-slate-300 px-3 text-[14px]">
                {INCOTERMS.map((i) => <option key={i} value={i}>{i}</option>)}
              </select>
            </div>
            <div>
              <div className="text-[12.5px] font-medium text-ink-400 mb-1">Cửa khẩu</div>
              <select value={border} onChange={(e) => setBorder(e.target.value)} className="w-full h-11 rounded-xl border border-slate-300 px-3 text-[14px]">
                {BORDERS.map((b) => <option key={b} value={b}>{b}</option>)}
              </select>
            </div>
            <Input label="Điểm lấy hàng" value={pickupPoint} onChange={setPickupPoint} />
            <Input label="Điểm giao hàng" value={deliveryPoint} onChange={setDeliveryPoint} />
            <div>
              <div className="text-[12.5px] font-medium text-ink-400 mb-1">Loại hàng</div>
              <select value={goodsType} onChange={(e) => setGoodsType(e.target.value)} className="w-full h-11 rounded-xl border border-slate-300 px-3 text-[14px]">
                {GOODS_TYPES.map((g) => <option key={g} value={g}>{g}</option>)}
              </select>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <Input label="Trọng lượng (kg)" value={weightKg} onChange={(v) => setWeightKg(v.replace(/[^0-9]/g, ''))} />
              <Input label="CBM" value={cbm} onChange={(v) => setCbm(v.replace(/[^0-9.]/g, ''))} />
            </div>
          </div>

          <div>
            <div className="text-[13px] font-bold text-navy-900 mb-2">Chi phí dự kiến theo từng hạng mục</div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {costs.map((c, idx) => (
                <div key={c.label} className="flex items-center gap-2">
                  <span className="text-[13.5px] text-ink-600 w-24 shrink-0">{c.label}</span>
                  <input value={c.amount} onChange={(e) => setCosts((prev) => prev.map((p, i) => i === idx ? { ...p, amount: e.target.value.replace(/[^0-9]/g, '') } : p))} placeholder="0" className="flex-1 h-10 rounded-lg border border-slate-300 px-2.5 text-[13.5px]" />
                  <select value={c.currency} onChange={(e) => setCosts((prev) => prev.map((p, i) => i === idx ? { ...p, currency: e.target.value as Currency } : p))} className="h-10 rounded-lg border border-slate-300 px-2 text-[13px] w-20">
                    <option value="VND">VND</option>
                    <option value="USD">USD</option>
                    <option value="CNY">CNY</option>
                  </select>
                </div>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 bg-slate-50 rounded-xl p-4">
            <Input label="Giá bán báo khách (VND) *" value={sellPrice} onChange={(v) => setSellPrice(v.replace(/[^0-9]/g, ''))} />
            <div className="space-y-1.5 text-[13.5px]">
              <div className="flex justify-between"><span className="text-ink-600">Chi phí dự kiến (VND)</span><span className="font-bold text-navy-900">{formatMoney(vndCost, 'VND')}</span></div>
              {Object.entries(costGroups).filter(([cur]) => cur !== 'VND').map(([cur, amt]) => (
                <div key={cur} className="flex justify-between"><span className="text-ink-400">+ Chi phí khác đơn vị</span><span className="font-semibold text-ink-600">{formatMoney(amt, cur)}</span></div>
              ))}
              <div className="flex justify-between pt-1.5 border-t border-slate-200"><span className="text-ink-600 font-semibold">Lợi nhuận dự kiến (VND)</span><span className={`font-extrabold ${profit >= 0 ? 'text-success-600' : 'text-danger-600'}`}>{formatMoney(profit, 'VND')}</span></div>
              <div className="flex justify-between"><span className="text-ink-600 font-semibold">Margin</span><span className="font-extrabold text-navy-900">{margin.toFixed(1)}%</span></div>
            </div>
          </div>

          <Button size="lg" disabled={!customerId || !sellPrice} onClick={handleCreate}>💾 Lưu báo giá (Nháp)</Button>
        </Card>
      )}

      <div className="space-y-3">
        {quotes.map((q) => (
          <Card key={q.id}>
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-extrabold text-navy-900 text-[15.5px]">{q.id}</span>
                  <Badge variant={QUOTE_STATUS_VARIANT[q.status]}>{QUOTE_STATUS_LABEL[q.status]}</Badge>
                </div>
                <div className="text-[14px] font-semibold text-ink-900">{q.customer}</div>
                <div className="text-[13px] text-ink-600 mt-0.5">{q.incoterm} · {q.pickupPoint || '—'} → {q.border} → {q.deliveryPoint || '—'} · {q.goodsType}</div>
                <div className="text-[13px] text-ink-400 mt-0.5">Tạo ngày {q.createdAt}</div>
              </div>
              <div className="text-right shrink-0">
                <div className="text-[12px] text-ink-400 font-medium">Giá bán</div>
                <div className="text-[19px] font-extrabold text-navy-900">{formatMoney(q.sellPrice, q.currency)}</div>
              </div>
            </div>
            <div className="flex flex-wrap gap-2 mt-3 pt-3 border-t border-border">
              {q.status === 'DRAFT' && <Button size="sm" icon={<Send size={14} />} onClick={() => setQuoteStatus(q.id, 'SENT')}>GỬI KHÁCH</Button>}
              {q.status === 'SENT' && <Button size="sm" variant="success" icon={<CheckCircle2 size={14} />} onClick={() => setQuoteStatus(q.id, 'ACCEPTED')}>KHÁCH ĐÃ CHỐT</Button>}
              {q.status === 'SENT' && <Button size="sm" variant="danger" onClick={() => setQuoteStatus(q.id, 'REJECTED')}>Khách từ chối</Button>}
              {q.status === 'ACCEPTED' && (
                <Button size="sm" variant="secondary" icon={<Handshake size={14} />} onClick={() => { addAgreement({ customerId: q.customerId, customer: q.customer, incoterm: q.incoterm, scope: `Vận chuyển ${q.goodsType} theo Incoterm ${q.incoterm}`, paymentTerms: '', factoryContact: '', requiredDocs: ['Invoice', 'Packing List'], acceptanceEvidence: `Khách chốt báo giá ${q.id}` }); navigate('/thoa-thuan-ban-giao'); }}>
                  Tạo thoả thuận từ báo giá này
                </Button>
              )}
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}

function Input({ label, value, onChange }: { label: string; value: string; onChange: (v: string) => void }) {
  return (
    <div>
      <div className="text-[12.5px] font-medium text-ink-400 mb-1">{label}</div>
      <input value={value} onChange={(e) => onChange(e.target.value)} className="w-full h-11 rounded-xl border border-slate-300 px-3 text-[14px] outline-none focus:border-accent-500" />
    </div>
  );
}
