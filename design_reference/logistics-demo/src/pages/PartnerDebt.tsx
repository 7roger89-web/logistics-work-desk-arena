import { useNavigate } from 'react-router-dom';
import { HandCoins } from 'lucide-react';
import { PARTNER_LEDGER, formatMoney } from '../lib/mockData';
import PageHeader from '../components/ui/PageHeader';
import Card, { CardTitle } from '../components/ui/Card';
import Badge from '../components/ui/Badge';

export default function PartnerDebt() {
  const navigate = useNavigate();
  const agents = Array.from(new Set(PARTNER_LEDGER.map((r) => r.agent)));

  return (
    <div>
      <PageHeader title="Công Nợ Đối Tác" subtitle="Sổ công nợ theo từng đại lý đối tác, tách riêng theo đơn vị tiền tệ để tránh cộng gộp nhầm lẫn." />

      <div className="space-y-4">
        {agents.map((agent) => {
          const rows = PARTNER_LEDGER.filter((r) => r.agent === agent);
          return (
            <Card key={agent}>
              <div className="flex items-center justify-between mb-3">
                <CardTitle className="mb-0"><HandCoins size={17} className="text-accent-500" /> {agent}</CardTitle>
                <button onClick={() => navigate('/ngu-canh-doi-tac')} className="text-[13px] font-semibold text-accent-600 hover:underline">Xem ngữ cảnh đối tác</button>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse min-w-[560px]">
                  <thead>
                    <tr className="bg-slate-50 text-[11.5px] text-ink-400 font-bold uppercase tracking-wide">
                      <th className="px-3 py-2.5">Đơn vị tiền</th>
                      <th className="px-3 py-2.5">Số dư đầu</th>
                      <th className="px-3 py-2.5">Phát sinh tăng</th>
                      <th className="px-3 py-2.5">Phát sinh giảm</th>
                      <th className="px-3 py-2.5">Đã thanh toán</th>
                      <th className="px-3 py-2.5">Số dư còn lại</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {rows.map((r) => {
                      const remaining = r.openingBalance + r.increase - r.decrease - r.paid;
                      return (
                        <tr key={r.currency}>
                          <td className="px-3 py-3"><Badge variant="neutral" icon={false}>{r.currency}</Badge></td>
                          <td className="px-3 py-3 text-[13.5px]">{formatMoney(r.openingBalance, r.currency)}</td>
                          <td className="px-3 py-3 text-[13.5px] text-danger-600">+{formatMoney(r.increase, r.currency)}</td>
                          <td className="px-3 py-3 text-[13.5px] text-ink-600">−{formatMoney(r.decrease, r.currency)}</td>
                          <td className="px-3 py-3 text-[13.5px] text-success-600 font-semibold">{formatMoney(r.paid, r.currency)}</td>
                          <td className="px-3 py-3 text-[14px] font-extrabold text-navy-900">{formatMoney(remaining, r.currency)}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
