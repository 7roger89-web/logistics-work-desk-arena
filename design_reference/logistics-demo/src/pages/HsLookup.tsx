import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Tag } from 'lucide-react';
import { useAppData } from '../lib/dataContext';
import { HS_CODES } from '../lib/mockData';
import PageHeader from '../components/ui/PageHeader';
import Card from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import Button from '../components/ui/Button';
import Modal from '../components/ui/Modal';
import EmptyState from '../components/ui/EmptyState';
import type { HsCode } from '../lib/types';

export default function HsLookup() {
  const navigate = useNavigate();
  const { shipments, updateShipmentFields } = useAppData();
  const [query, setQuery] = useState('');
  const [applyCode, setApplyCode] = useState<HsCode | null>(null);
  const [shipmentId, setShipmentId] = useState('');

  const filtered = HS_CODES.filter((h) => !query || h.code.toLowerCase().includes(query.toLowerCase()) || h.name.toLowerCase().includes(query.toLowerCase()));

  function apply() {
    const s = shipments.find((x) => x.id === shipmentId);
    if (!s || !applyCode) return;
    updateShipmentFields(s.id, { goods: { ...s.goods, note: `${s.goods.note ? s.goods.note + '; ' : ''}Áp mã HS ${applyCode.code} — ${applyCode.name}` } });
    setApplyCode(null);
    navigate(`/lo-hang/${s.id}?tab=pickup`);
  }

  return (
    <div>
      <PageHeader title="Tra Cứu Thuế / HS" subtitle="Tra cứu mã HS, thuế nhập khẩu, VAT và chính sách quản lý chuyên ngành liên quan tới hàng hoá thường nhập." />

      <Card className="mb-4">
        <div className="flex items-center gap-2 bg-slate-100 rounded-xl px-3 h-11">
          <Search size={16} className="text-ink-400 shrink-0" />
          <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Tìm theo mã HS hoặc tên hàng hoá..." className="bg-transparent flex-1 min-w-0 outline-none text-[14px]" />
        </div>
      </Card>

      {filtered.length === 0 ? <Card><EmptyState message="Không tìm thấy mã HS phù hợp." /></Card> : (
        <div className="space-y-3">
          {filtered.map((h) => (
            <Card key={h.code}>
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <Tag size={15} className="text-accent-500" />
                    <span className="font-mono font-extrabold text-navy-900 text-[16px]">{h.code}</span>
                  </div>
                  <div className="text-[14.5px] font-semibold text-ink-900">{h.name}</div>
                </div>
                <div className="flex gap-2">
                  <Badge variant="info" icon={false}>Thuế NK {h.importTax}%</Badge>
                  <Badge variant="neutral" icon={false}>VAT {h.vat}%</Badge>
                </div>
              </div>
              <div className="mt-3 pt-3 border-t border-border space-y-1.5">
                <p className="text-[13.5px] text-ink-600"><b className="text-navy-900">Chính sách:</b> {h.policy}</p>
                <p className="text-[13.5px] text-ink-400"><b className="text-ink-600">Ghi chú:</b> {h.note}</p>
              </div>
              <div className="mt-3">
                <Button size="sm" onClick={() => { setApplyCode(h); setShipmentId(''); }}>DÙNG CHO LÔ HÀNG</Button>
              </div>
            </Card>
          ))}
        </div>
      )}

      <Modal open={!!applyCode} onClose={() => setApplyCode(null)} title="Áp mã HS cho lô hàng">
        <div className="space-y-4">
          {applyCode && <div className="bg-slate-50 rounded-xl p-3 text-[14px]"><span className="font-mono font-bold text-navy-900">{applyCode.code}</span> — {applyCode.name}</div>}
          <div>
            <div className="text-[12.5px] font-medium text-ink-400 mb-1">Chọn lô hàng *</div>
            <select value={shipmentId} onChange={(e) => setShipmentId(e.target.value)} className="w-full h-11 rounded-xl border border-slate-300 px-3 text-[14px]">
              <option value="">— Chọn lô hàng —</option>
              {shipments.map((s) => <option key={s.id} value={s.id}>{s.id} — {s.customer}</option>)}
            </select>
          </div>
          <Button full disabled={!shipmentId} onClick={apply}>✅ Áp dụng cho lô hàng</Button>
        </div>
      </Modal>
    </div>
  );
}
