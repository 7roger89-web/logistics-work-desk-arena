import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Eye } from 'lucide-react';
import { useAppData } from '../lib/dataContext';
import { formatVND } from '../lib/mockData';
import PageHeader from '../components/ui/PageHeader';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';

export default function Customers() {
  const navigate = useNavigate();
  const { customers } = useAppData();
  const [query, setQuery] = useState('');

  const filtered = customers.filter((c) => !query || c.name.toLowerCase().includes(query.toLowerCase()) || c.taxCode.includes(query));

  return (
    <div>
      <PageHeader title="Khách Hàng" subtitle={`${filtered.length} khách hàng đang được quản lý`} />
      <Card className="mb-4">
        <div className="flex items-center gap-2 bg-slate-100 rounded-xl px-3 h-11">
          <Search size={16} className="text-ink-400 shrink-0" />
          <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Tìm theo tên công ty hoặc mã số thuế..." className="bg-transparent flex-1 min-w-0 outline-none text-[14px]" />
        </div>
      </Card>

      <Card padded={false} className="hidden lg:block overflow-hidden">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-slate-50 text-[12px] text-ink-400 font-bold uppercase tracking-wide">
              <th className="px-4 py-3">Tên công ty</th>
              <th className="px-4 py-3">MST</th>
              <th className="px-4 py-3">Liên hệ</th>
              <th className="px-4 py-3">Sale</th>
              <th className="px-4 py-3">Số lô</th>
              <th className="px-4 py-3">Công nợ</th>
              <th className="px-4 py-3">Cập nhật</th>
              <th className="px-4 py-3">Hành động</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {filtered.map((c) => (
              <tr key={c.id} className="hover:bg-slate-50">
                <td className="px-4 py-3.5 font-bold text-navy-900 max-w-[260px]">{c.name}</td>
                <td className="px-4 py-3.5 text-[13.5px] text-ink-600 whitespace-nowrap">{c.taxCode}</td>
                <td className="px-4 py-3.5 text-[13.5px] text-ink-600 whitespace-nowrap">{c.contact} · {c.phone}</td>
                <td className="px-4 py-3.5 text-[13.5px] text-ink-600 whitespace-nowrap">{c.sale}</td>
                <td className="px-4 py-3.5 text-[13.5px] text-ink-600 text-center">{c.shipmentCount}</td>
                <td className="px-4 py-3.5">{c.debt > 0 ? <Badge variant="warning">{formatVND(c.debt)}</Badge> : <Badge variant="success">Không nợ</Badge>}</td>
                <td className="px-4 py-3.5 text-[12.5px] text-ink-400 whitespace-nowrap">{c.updatedAt}</td>
                <td className="px-4 py-3.5"><Button size="sm" variant="secondary" icon={<Eye size={14} />} onClick={() => navigate(`/khach-hang/${c.id}`)}>Xem</Button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>

      <div className="lg:hidden space-y-3">
        {filtered.map((c) => (
          <Card key={c.id} onClick={() => navigate(`/khach-hang/${c.id}`)} className="space-y-2">
            <div className="text-[15px] font-bold text-navy-900">{c.name}</div>
            <div className="text-[13px] text-ink-600">MST: {c.taxCode} · {c.contact}</div>
            <div className="flex items-center justify-between pt-2 border-t border-border">
              <span className="text-[12.5px] text-ink-400">{c.shipmentCount} lô · Sale: {c.sale}</span>
              {c.debt > 0 ? <Badge variant="warning">{formatVND(c.debt)}</Badge> : <Badge variant="success">Không nợ</Badge>}
            </div>
            <Button full variant="secondary" onClick={() => navigate(`/khach-hang/${c.id}`)}>Xem chi tiết</Button>
          </Card>
        ))}
      </div>
    </div>
  );
}
