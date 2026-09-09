import { useNavigate } from 'react-router-dom';
import { Scale, CheckCircle2 } from 'lucide-react';
import { useAppData } from '../lib/dataContext';
import { formatMoney } from '../lib/mockData';
import PageHeader from '../components/ui/PageHeader';
import Card from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import Button from '../components/ui/Button';
import EmptyState from '../components/ui/EmptyState';

export default function Reconciliation() {
  const navigate = useNavigate();
  const { shipments, contracts, addPayment } = useAppData();

  const pending = shipments.filter((s) => s.finance.payable.total > 0 && s.finance.payable.paid < s.finance.payable.total);
  const settled = shipments.filter((s) => s.finance.payable.total > 0 && s.finance.payable.paid >= s.finance.payable.total);

  function contractAgent(s: typeof shipments[number]) {
    return contracts.find((c) => c.id === s.contractId)?.agent || '—';
  }

  return (
    <div>
      <PageHeader title="Đối Soát Tài Chính" subtitle="Rà soát các khoản phải trả đại lý đối tác chưa được thanh toán đầy đủ trước khi khoá sổ." />

      <Card className="mb-4">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-[15px] font-bold text-navy-900 flex items-center gap-2"><Scale size={17} className="text-warning-500" /> Chờ đối soát ({pending.length})</h2>
        </div>
        {pending.length === 0 ? <EmptyState message="Không còn khoản nào chờ đối soát. Tất cả đã được thanh toán đầy đủ." icon={<CheckCircle2 size={26} />} /> : (
          <div className="space-y-3">
            {pending.map((s) => {
              const remaining = s.finance.payable.total - s.finance.payable.paid;
              return (
                <div key={s.id} className="flex flex-wrap items-center justify-between gap-3 border border-warning-500/30 bg-warning-50 rounded-xl p-3.5">
                  <div>
                    <div className="font-bold text-navy-900 text-[14.5px]">{s.id} <span className="font-normal text-ink-600">· {s.customer}</span></div>
                    <div className="text-[12.5px] text-ink-600">Đại lý: {contractAgent(s)}</div>
                  </div>
                  <div className="text-right">
                    <div className="text-[12px] text-ink-400">Còn phải trả</div>
                    <div className="font-extrabold text-danger-600 text-[16px]">{formatMoney(remaining, s.finance.payable.currency)}</div>
                  </div>
                  <div className="flex gap-2">
                    <Button size="sm" variant="secondary" onClick={() => navigate(`/lo-hang/${s.id}?tab=finance`)}>Xem chi tiết</Button>
                    <Button size="sm" variant="success" onClick={() => addPayment(s.id, { type: 'TRA', amount: remaining, currency: s.finance.payable.currency, method: 'Chuyển khoản', note: 'Đối soát và thanh toán đủ cho đại lý', date: new Date().toLocaleDateString('vi-VN'), recordedBy: 'Bạn' })}>✅ Đánh dấu đã đối soát</Button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </Card>

      <Card>
        <h2 className="text-[15px] font-bold text-navy-900 mb-3">Đã đối soát ({settled.length})</h2>
        {settled.length === 0 ? <EmptyState message="Chưa có khoản nào được đối soát xong." /> : (
          <div className="divide-y divide-border">
            {settled.map((s) => (
              <div key={s.id} className="flex flex-wrap items-center justify-between gap-3 py-2.5">
                <div className="font-bold text-navy-900 text-[14px]">{s.id} <span className="font-normal text-ink-600">· {contractAgent(s)}</span></div>
                <Badge variant="success">{formatMoney(s.finance.payable.paid, s.finance.payable.currency)} · Đã thanh toán đủ</Badge>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
