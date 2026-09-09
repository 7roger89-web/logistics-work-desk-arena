import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, ArrowRightCircle } from 'lucide-react';
import { TASKS } from '../lib/mockData';
import PageHeader from '../components/ui/PageHeader';
import Card from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import Button from '../components/ui/Button';
import { PRIORITY_LABEL, PRIORITY_VARIANT } from '../lib/status';

export default function Tasks() {
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [priority, setPriority] = useState('ALL');

  const filtered = useMemo(() => TASKS
    .filter((t) => priority === 'ALL' || t.priority === priority)
    .filter((t) => !query || t.action.toLowerCase().includes(query.toLowerCase()) || t.customer.toLowerCase().includes(query.toLowerCase()) || t.shipmentId.toLowerCase().includes(query.toLowerCase()))
    .sort((a, b) => (a.priority === 'KHAN' ? -1 : b.priority === 'KHAN' ? 1 : a.priority === 'CAN_XU_LY' ? -1 : 1)),
  [query, priority]);

  return (
    <div>
      <PageHeader title="Việc Cần Xử Lý" subtitle="Danh sách công việc đang chờ xử lý trên toàn bộ lô hàng, sắp xếp theo mức độ ưu tiên." />

      <Card className="mb-4 flex flex-col sm:flex-row gap-3 sm:items-center">
        <div className="flex items-center gap-2 bg-slate-100 rounded-xl px-3 h-11 flex-1">
          <Search size={16} className="text-ink-400 shrink-0" />
          <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Tìm theo mã lô, khách hàng, việc cần làm..." className="bg-transparent flex-1 min-w-0 outline-none text-[14px]" />
        </div>
        <div className="flex gap-2 overflow-x-auto no-scrollbar">
          {[['ALL', 'Tất cả'], ['KHAN', 'Khẩn'], ['CAN_XU_LY', 'Cần xử lý'], ['BINH_THUONG', 'Bình thường']].map(([val, label]) => (
            <button
              key={val}
              onClick={() => setPriority(val)}
              className={`shrink-0 px-3.5 h-11 rounded-xl text-[13.5px] font-semibold border ${priority === val ? 'bg-navy-900 text-white border-navy-900' : 'bg-white text-ink-600 border-slate-300 hover:bg-slate-50'}`}
            >
              {label}
            </button>
          ))}
        </div>
      </Card>

      {/* Desktop table */}
      <Card padded={false} className="hidden md:block overflow-hidden">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-slate-50 text-[12.5px] text-ink-400 font-bold uppercase tracking-wide">
              <th className="px-4 py-3">Ưu tiên</th>
              <th className="px-4 py-3">Mã lô</th>
              <th className="px-4 py-3">Khách hàng</th>
              <th className="px-4 py-3">Việc cần làm</th>
              <th className="px-4 py-3">Người phụ trách</th>
              <th className="px-4 py-3">Hạn</th>
              <th className="px-4 py-3">Trạng thái</th>
              <th className="px-4 py-3">Hành động</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {filtered.map((t) => (
              <tr key={t.id} className="hover:bg-slate-50">
                <td className="px-4 py-3.5"><Badge variant={PRIORITY_VARIANT[t.priority]}>{PRIORITY_LABEL[t.priority]}</Badge></td>
                <td className="px-4 py-3.5 font-bold text-navy-900">{t.shipmentId}</td>
                <td className="px-4 py-3.5 text-[13.5px] text-ink-600 max-w-[180px] truncate">{t.customer}</td>
                <td className="px-4 py-3.5 text-[13.5px] text-ink-900 max-w-[260px]">{t.action}</td>
                <td className="px-4 py-3.5 text-[13.5px] text-ink-600">{t.assignee}</td>
                <td className="px-4 py-3.5 text-[13.5px] text-ink-600 whitespace-nowrap">{t.due}</td>
                <td className="px-4 py-3.5 text-[13px] text-ink-600 whitespace-nowrap">{t.status}</td>
                <td className="px-4 py-3.5">
                  <Button size="sm" onClick={() => navigate(`/lo-hang/${t.shipmentId}?tab=${t.tab}`)}>XỬ LÝ NGAY</Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>

      {/* Mobile cards */}
      <div className="md:hidden space-y-3">
        {filtered.map((t) => (
          <Card key={t.id} className="space-y-2.5">
            <div className="flex items-center justify-between">
              <Badge variant={PRIORITY_VARIANT[t.priority]}>{PRIORITY_LABEL[t.priority]}</Badge>
              <span className="font-bold text-navy-900 text-[15px]">{t.shipmentId}</span>
            </div>
            <div className="text-[15px] font-semibold text-navy-900 leading-snug">{t.action}</div>
            <div className="text-[13px] text-ink-600">{t.customer}</div>
            <div className="flex items-center justify-between text-[12.5px] text-ink-400 pt-1 border-t border-border">
              <span>👤 {t.assignee}</span>
              <span>⏰ {t.due}</span>
            </div>
            <Button full onClick={() => navigate(`/lo-hang/${t.shipmentId}?tab=${t.tab}`)} icon={<ArrowRightCircle size={16} />}>XỬ LÝ NGAY</Button>
          </Card>
        ))}
      </div>
    </div>
  );
}
