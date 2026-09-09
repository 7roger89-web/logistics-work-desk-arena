import { useMemo, useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Search, SlidersHorizontal, PackagePlus, Eye } from 'lucide-react';
import { useAppData } from '../lib/dataContext';
import PageHeader from '../components/ui/PageHeader';
import Card from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import Button from '../components/ui/Button';
import EmptyState from '../components/ui/EmptyState';
import { SHIPMENT_STATUS_LABEL, SHIPMENT_STATUS_VARIANT } from '../lib/status';
import type { ShipmentStatus } from '../lib/types';

export default function Shipments() {
  const navigate = useNavigate();
  const { shipments } = useAppData();
  const [searchParams] = useSearchParams();
  const [query, setQuery] = useState(searchParams.get('q') || '');
  const [status, setStatus] = useState<string>(searchParams.get('status') || 'ALL');
  const [docsFilter, setDocsFilter] = useState<string>(searchParams.get('docs') || '');
  const [sale, setSale] = useState('ALL');
  const [support, setSupport] = useState('ALL');
  const [showMoreFilters, setShowMoreFilters] = useState(false);

  useEffect(() => {
    if (searchParams.get('status')) setStatus(searchParams.get('status')!);
    if (searchParams.get('docs')) setDocsFilter(searchParams.get('docs')!);
    if (searchParams.get('q')) setQuery(searchParams.get('q')!);
  }, [searchParams]);

  const saleOptions = useMemo(() => Array.from(new Set(shipments.map((s) => s.sale))), [shipments]);
  const supportOptions = useMemo(() => Array.from(new Set(shipments.map((s) => s.support))), [shipments]);

  const filtered = shipments.filter((s) => {
    if (status !== 'ALL' && s.status !== status) return false;
    if (docsFilter === 'thieu' && !s.checklist.some((c) => c.status !== 'DU')) return false;
    if (sale !== 'ALL' && s.sale !== sale) return false;
    if (support !== 'ALL' && s.support !== support) return false;
    if (query) {
      const q = query.toLowerCase();
      const hay = `${s.id} ${s.customer} ${s.contractNo || ''} ${s.route} ${s.border}`.toLowerCase();
      if (!hay.includes(q)) return false;
    }
    return true;
  });

  return (
    <div>
      <PageHeader
        title="Lô Hàng"
        subtitle={`${filtered.length} lô hàng phù hợp bộ lọc hiện tại`}
        actions={<Button icon={<PackagePlus size={17} />} onClick={() => navigate('/tao-lo-moi')}>➕ Tạo lô mới</Button>}
      />

      <Card className="mb-4 space-y-3">
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="flex items-center gap-2 bg-slate-100 rounded-xl px-3 h-11 flex-1">
            <Search size={16} className="text-ink-400 shrink-0" />
            <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Mã lô, khách hàng, container, hợp đồng, tuyến, cửa khẩu..." className="bg-transparent flex-1 min-w-0 outline-none text-[14px]" />
          </div>
          <button onClick={() => setShowMoreFilters((v) => !v)} className="flex items-center gap-2 h-11 px-4 rounded-xl border border-slate-300 text-[13.5px] font-semibold text-ink-600 hover:bg-slate-50 shrink-0">
            <SlidersHorizontal size={15} /> Bộ lọc {showMoreFilters ? '▲' : '▼'}
          </button>
        </div>
        <div className="flex gap-2 overflow-x-auto no-scrollbar">
          {(['ALL', 'CHO_LAY_HANG', 'DANG_VAN_CHUYEN', 'CHO_THONG_QUAN', 'CHO_GIAO', 'DA_GIAO'] as const).map((s) => (
            <button
              key={s}
              onClick={() => setStatus(s)}
              className={`shrink-0 px-3.5 h-10 rounded-xl text-[13px] font-semibold border ${status === s ? 'bg-navy-900 text-white border-navy-900' : 'bg-white text-ink-600 border-slate-300 hover:bg-slate-50'}`}
            >
              {s === 'ALL' ? 'Tất cả trạng thái' : SHIPMENT_STATUS_LABEL[s as ShipmentStatus]}
            </button>
          ))}
        </div>
        {showMoreFilters && (
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 pt-2 border-t border-border">
            <div>
              <div className="text-[12.5px] font-medium text-ink-400 mb-1">Sale phụ trách</div>
              <select value={sale} onChange={(e) => setSale(e.target.value)} className="w-full h-10 rounded-lg border border-slate-300 px-2.5 text-[13.5px]">
                <option value="ALL">Tất cả</option>
                {saleOptions.map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
            <div>
              <div className="text-[12.5px] font-medium text-ink-400 mb-1">Support phụ trách</div>
              <select value={support} onChange={(e) => setSupport(e.target.value)} className="w-full h-10 rounded-lg border border-slate-300 px-2.5 text-[13.5px]">
                <option value="ALL">Tất cả</option>
                {supportOptions.map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
            <div>
              <div className="text-[12.5px] font-medium text-ink-400 mb-1">Chứng từ</div>
              <select value={docsFilter} onChange={(e) => setDocsFilter(e.target.value)} className="w-full h-10 rounded-lg border border-slate-300 px-2.5 text-[13.5px]">
                <option value="">Tất cả</option>
                <option value="thieu">Thiếu chứng từ</option>
              </select>
            </div>
          </div>
        )}
      </Card>

      {filtered.length === 0 ? (
        <Card><EmptyState message="Không có lô hàng nào khớp với bộ lọc hiện tại." action={<Button variant="secondary" onClick={() => { setStatus('ALL'); setQuery(''); setSale('ALL'); setSupport('ALL'); setDocsFilter(''); }}>Xoá bộ lọc</Button>} /></Card>
      ) : (
        <>
          <Card padded={false} className="hidden lg:block overflow-hidden">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50 text-[12px] text-ink-400 font-bold uppercase tracking-wide">
                  <th className="px-4 py-3">Mã lô</th>
                  <th className="px-4 py-3">Khách hàng</th>
                  <th className="px-4 py-3">Hợp đồng</th>
                  <th className="px-4 py-3">Tuyến</th>
                  <th className="px-4 py-3">Trạng thái</th>
                  <th className="px-4 py-3">Việc tiếp theo</th>
                  <th className="px-4 py-3">Sale</th>
                  <th className="px-4 py-3">Support</th>
                  <th className="px-4 py-3">Cập nhật</th>
                  <th className="px-4 py-3">Hành động</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {filtered.map((s) => (
                  <tr key={s.id} className="hover:bg-slate-50">
                    <td className="px-4 py-3.5 font-bold text-navy-900 whitespace-nowrap">{s.id}</td>
                    <td className="px-4 py-3.5 text-[13.5px] text-ink-600 max-w-[170px] truncate">{s.customer}</td>
                    <td className="px-4 py-3.5 text-[13px] text-ink-600 whitespace-nowrap">
                      {s.contractNo ? <button onClick={() => navigate(`/hop-dong/${s.contractId}`)} className="text-accent-600 font-semibold hover:underline">{s.contractNo}</button> : <span className="text-warning-600 font-semibold">⚠ Chưa có</span>}
                    </td>
                    <td className="px-4 py-3.5 text-[13px] text-ink-600 max-w-[170px] truncate">{s.route}</td>
                    <td className="px-4 py-3.5"><Badge variant={SHIPMENT_STATUS_VARIANT[s.status]}>{SHIPMENT_STATUS_LABEL[s.status]}</Badge></td>
                    <td className="px-4 py-3.5 text-[13px] text-ink-900 max-w-[220px]">{s.nextAction}</td>
                    <td className="px-4 py-3.5 text-[13px] text-ink-600 whitespace-nowrap">{s.sale}</td>
                    <td className="px-4 py-3.5 text-[13px] text-ink-600 whitespace-nowrap">{s.support}</td>
                    <td className="px-4 py-3.5 text-[12.5px] text-ink-400 whitespace-nowrap">{s.updatedAt}</td>
                    <td className="px-4 py-3.5">
                      <div className="flex items-center gap-2">
                        <Button size="sm" onClick={() => navigate(`/lo-hang/${s.id}`)}>XỬ LÝ</Button>
                        <Button size="sm" variant="secondary" icon={<Eye size={14} />} onClick={() => navigate(`/lo-hang/${s.id}?view=360`)}>360°</Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>

          <div className="lg:hidden space-y-3">
            {filtered.map((s) => (
              <Card key={s.id} className="space-y-2.5">
                <div className="flex items-center justify-between">
                  <span className="font-extrabold text-navy-900 text-[16px]">{s.id}</span>
                  <Badge variant={SHIPMENT_STATUS_VARIANT[s.status]}>{SHIPMENT_STATUS_LABEL[s.status]}</Badge>
                </div>
                <div className="text-[14px] font-semibold text-ink-900">{s.customer}</div>
                <div className="text-[13px] text-ink-600">{s.route}</div>
                <div className="text-[13px] text-navy-900 bg-slate-50 rounded-lg px-2.5 py-2 font-medium">➡ {s.nextAction}</div>
                <div className="flex items-center justify-between text-[12.5px] text-ink-400 pt-1 border-t border-border">
                  <span>Sale: {s.sale}</span>
                  <span>Support: {s.support}</span>
                </div>
                <div className="flex gap-2">
                  <Button full onClick={() => navigate(`/lo-hang/${s.id}`)}>XỬ LÝ</Button>
                  <Button full variant="secondary" icon={<Eye size={15} />} onClick={() => navigate(`/lo-hang/${s.id}?view=360`)}>XEM 360°</Button>
                </div>
              </Card>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
