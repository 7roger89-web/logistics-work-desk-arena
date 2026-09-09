import { useNavigate } from 'react-router-dom';
import { Wallet, HandCoins, AlertTriangle, Scale } from 'lucide-react';
import { useAppData } from '../lib/dataContext';
import { formatMoney } from '../lib/mockData';
import PageHeader from '../components/ui/PageHeader';
import Card from '../components/ui/Card';
import StatCard from '../components/ui/StatCard';
import Badge from '../components/ui/Badge';
import Button from '../components/ui/Button';

const DUE_DATES: Record<string, string> = {
  'LO-0306': '12/09/2026', 'LO-0307': '15/09/2026', 'LO-0308': '10/09/2026', 'LO-0304': '18/09/2026', 'LO-0302': '09/09/2026',
};

export default function Finance() {
  const navigate = useNavigate();
  const { shipments } = useAppData();

  const rows = shipments.filter((s) => s.finance.receivable.total > 0);
  const tongPhaiThu = rows.reduce((s, r) => s + r.finance.receivable.total, 0);
  const tongDaThu = rows.reduce((s, r) => s + r.finance.receivable.paid, 0);
  const tongPhaiTra = shipments.reduce((s, r) => s + r.finance.payable.total, 0);
  const quaHan = rows.filter((r) => r.finance.receivable.total > r.finance.receivable.paid && DUE_DATES[r.id] === '09/09/2026');
  const choDoiSoat = shipments.filter((s) => s.finance.payable.total > 0 && s.finance.payable.paid < s.finance.payable.total);

  return (
    <div>
      <PageHeader title="Thu Tiền & Công Nợ" subtitle="Theo dõi công nợ phải thu từ khách hàng trên toàn bộ lô hàng đang vận hành." />

      <div className="grid grid-cols-2 lg:grid-cols-5 gap-3 mb-5">
        <StatCard label="Tổng phải thu" value={formatMoney(tongPhaiThu, 'VND')} icon={<Wallet size={16} />} tone="danger" />
        <StatCard label="Đã thu" value={formatMoney(tongDaThu, 'VND')} icon={<Wallet size={16} />} tone="success" />
        <StatCard label="Quá hạn" value={quaHan.length} icon={<AlertTriangle size={16} />} tone="warning" />
        <StatCard label="Phải trả đại lý" value={formatMoney(tongPhaiTra, 'VND')} icon={<HandCoins size={16} />} tone="neutral" onClick={() => navigate('/cong-no-doi-tac')} />
        <StatCard label="Chờ đối soát" value={choDoiSoat.length} icon={<Scale size={16} />} tone="info" onClick={() => navigate('/doi-soat-tai-chinh')} />
      </div>

      <Card padded={false} className="hidden lg:block overflow-hidden">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-slate-50 text-[12px] text-ink-400 font-bold uppercase tracking-wide">
              <th className="px-4 py-3">Khách hàng</th>
              <th className="px-4 py-3">Lô</th>
              <th className="px-4 py-3">Hợp đồng</th>
              <th className="px-4 py-3">Phải thu</th>
              <th className="px-4 py-3">Đã thu</th>
              <th className="px-4 py-3">Còn lại</th>
              <th className="px-4 py-3">Hạn</th>
              <th className="px-4 py-3">Trạng thái</th>
              <th className="px-4 py-3">Hành động</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {rows.map((s) => {
              const remaining = s.finance.receivable.total - s.finance.receivable.paid;
              const due = DUE_DATES[s.id] || '—';
              const overdue = remaining > 0 && due === '09/09/2026';
              return (
                <tr key={s.id} className="hover:bg-slate-50">
                  <td className="px-4 py-3.5 text-[13.5px] font-semibold text-ink-900 max-w-[190px] truncate">{s.customer}</td>
                  <td className="px-4 py-3.5 font-bold text-navy-900 whitespace-nowrap">{s.id}</td>
                  <td className="px-4 py-3.5 text-[13px] text-ink-600 whitespace-nowrap">{s.contractNo || '—'}</td>
                  <td className="px-4 py-3.5 text-[13.5px] whitespace-nowrap">{formatMoney(s.finance.receivable.total, s.finance.receivable.currency)}</td>
                  <td className="px-4 py-3.5 text-[13.5px] text-success-600 font-semibold whitespace-nowrap">{formatMoney(s.finance.receivable.paid, s.finance.receivable.currency)}</td>
                  <td className="px-4 py-3.5 text-[13.5px] font-bold text-danger-600 whitespace-nowrap">{formatMoney(remaining, s.finance.receivable.currency)}</td>
                  <td className="px-4 py-3.5 text-[12.5px] text-ink-400 whitespace-nowrap">{due}</td>
                  <td className="px-4 py-3.5">
                    {remaining <= 0 ? <Badge variant="success">Đã thu đủ</Badge> : overdue ? <Badge variant="danger">Quá hạn</Badge> : <Badge variant="warning">Còn hạn</Badge>}
                  </td>
                  <td className="px-4 py-3.5">
                    <div className="flex gap-2">
                      <Button size="sm" onClick={() => navigate(`/lo-hang/${s.id}?tab=finance`)}>GHI NHẬN THANH TOÁN</Button>
                      <Button size="sm" variant="secondary" onClick={() => navigate('/doi-soat-tai-chinh')}>ĐỐI SOÁT</Button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </Card>

      <div className="lg:hidden space-y-3">
        {rows.map((s) => {
          const remaining = s.finance.receivable.total - s.finance.receivable.paid;
          const due = DUE_DATES[s.id] || '—';
          const overdue = remaining > 0 && due === '09/09/2026';
          return (
            <Card key={s.id} className="space-y-2.5">
              <div className="flex items-center justify-between">
                <span className="font-extrabold text-navy-900 text-[15px]">{s.id}</span>
                {remaining <= 0 ? <Badge variant="success">Đã thu đủ</Badge> : overdue ? <Badge variant="danger">Quá hạn</Badge> : <Badge variant="warning">Còn hạn</Badge>}
              </div>
              <div className="text-[14px] font-semibold text-ink-900">{s.customer}</div>
              <div className="grid grid-cols-3 gap-2 text-center bg-slate-50 rounded-lg p-2.5">
                <div><div className="text-[11px] text-ink-400">Phải thu</div><div className="text-[13px] font-bold text-navy-900">{formatMoney(s.finance.receivable.total, 'VND')}</div></div>
                <div><div className="text-[11px] text-ink-400">Đã thu</div><div className="text-[13px] font-bold text-success-600">{formatMoney(s.finance.receivable.paid, 'VND')}</div></div>
                <div><div className="text-[11px] text-ink-400">Còn lại</div><div className="text-[13px] font-bold text-danger-600">{formatMoney(remaining, 'VND')}</div></div>
              </div>
              <div className="flex gap-2">
                <Button full onClick={() => navigate(`/lo-hang/${s.id}?tab=finance`)}>GHI NHẬN THANH TOÁN</Button>
                <Button full variant="secondary" onClick={() => navigate('/doi-soat-tai-chinh')}>ĐỐI SOÁT</Button>
              </div>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
