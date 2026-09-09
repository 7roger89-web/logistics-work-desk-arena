import { useState } from 'react';
import { useAppData } from '../lib/dataContext';
import { formatVND } from '../lib/mockData';
import PageHeader from '../components/ui/PageHeader';
import Card, { CardTitle } from '../components/ui/Card';
import StatCard from '../components/ui/StatCard';
import { TrendingUp, PieChart, Users, AlertOctagon } from 'lucide-react';
import { SHIPMENT_STATUS_LABEL, SHIPMENT_STATUS_VARIANT } from '../lib/status';
import Badge from '../components/ui/Badge';
import type { ShipmentStatus } from '../lib/types';

const MONTHLY = [
  { label: 'T4', revenue: 820, profit: 145 },
  { label: 'T5', revenue: 910, profit: 168 },
  { label: 'T6', revenue: 780, profit: 132 },
  { label: 'T7', revenue: 1050, profit: 201 },
  { label: 'T8', revenue: 1180, profit: 224 },
  { label: 'T9', revenue: 690, profit: 138 },
];

const BOTTLENECKS = [
  { label: 'Thiếu Export Declaration trước giờ xe qua cửa khẩu', count: 4 },
  { label: 'Chậm bổ sung Packing List từ nhà máy TQ', count: 3 },
  { label: 'Khách chậm thanh toán quá 7 ngày', count: 2 },
  { label: 'Đại lý chậm gửi hồ sơ pháp lý ký hợp đồng', count: 2 },
];

export default function Reports() {
  const { shipments, customers } = useAppData();
  const [period, setPeriod] = useState<'Tuần' | 'Tháng' | 'Quý' | 'Năm'>('Tháng');

  const maxRevenue = Math.max(...MONTHLY.map((m) => m.revenue));
  const statusCounts = (['CHO_LAY_HANG', 'DANG_VAN_CHUYEN', 'CHO_THONG_QUAN', 'CHO_GIAO', 'DA_GIAO'] as ShipmentStatus[]).map((st) => ({
    status: st, count: shipments.filter((s) => s.status === st).length,
  }));
  const topCustomers = [...customers].sort((a, b) => b.shipmentCount - a.shipmentCount).slice(0, 4);
  const maxShipCount = Math.max(...topCustomers.map((c) => c.shipmentCount));

  const totalRevenue = 6430000000;
  const grossProfit = 1008000000;
  const margin = (grossProfit / totalRevenue) * 100;
  const totalReceivable = shipments.reduce((s, r) => s + Math.max(0, r.finance.receivable.total - r.finance.receivable.paid), 0);
  const totalPayable = shipments.reduce((s, r) => s + Math.max(0, r.finance.payable.total - r.finance.payable.paid), 0);

  return (
    <div>
      <PageHeader
        title="Báo Cáo CEO"
        subtitle="Tổng quan hiệu quả kinh doanh và vận hành toàn hệ thống."
        actions={
          <div className="flex gap-1.5 bg-slate-100 rounded-xl p-1">
            {(['Tuần', 'Tháng', 'Quý', 'Năm'] as const).map((p) => (
              <button key={p} onClick={() => setPeriod(p)} className={`px-3.5 h-9 rounded-lg text-[13px] font-semibold ${period === p ? 'bg-navy-900 text-white' : 'text-ink-600'}`}>{p}</button>
            ))}
          </div>
        }
      />

      <div className="grid grid-cols-2 lg:grid-cols-5 gap-3 mb-5">
        <StatCard label="Doanh thu" value={formatVND(totalRevenue)} icon={<TrendingUp size={16} />} tone="info" sub={`Theo ${period.toLowerCase()}`} />
        <StatCard label="Lợi nhuận gộp" value={formatVND(grossProfit)} icon={<TrendingUp size={16} />} tone="success" />
        <StatCard label="Margin" value={`${margin.toFixed(1)}%`} icon={<PieChart size={16} />} tone="neutral" />
        <StatCard label="Phải thu" value={formatVND(totalReceivable)} icon={<TrendingUp size={16} />} tone="danger" />
        <StatCard label="Phải trả" value={formatVND(totalPayable)} icon={<TrendingUp size={16} />} tone="warning" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-4">
        <Card className="lg:col-span-2">
          <CardTitle>Doanh thu &amp; Lợi nhuận theo tháng (triệu ₫)</CardTitle>
          <div className="flex items-end gap-4 h-52 pt-4">
            {MONTHLY.map((m) => (
              <div key={m.label} className="flex-1 flex flex-col items-center gap-1.5 h-full justify-end">
                <div className="w-full flex items-end gap-1 h-full justify-center">
                  <div className="w-1/2 bg-navy-800 rounded-t-md" style={{ height: `${(m.revenue / maxRevenue) * 100}%` }} title={`Doanh thu ${m.revenue}tr`} />
                  <div className="w-1/2 bg-success-500 rounded-t-md" style={{ height: `${(m.profit / maxRevenue) * 100}%` }} title={`Lợi nhuận ${m.profit}tr`} />
                </div>
                <span className="text-[12px] font-semibold text-ink-600">{m.label}</span>
              </div>
            ))}
          </div>
          <div className="flex items-center gap-4 mt-2 text-[12.5px] text-ink-600">
            <span className="flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-sm bg-navy-800" /> Doanh thu</span>
            <span className="flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-sm bg-success-500" /> Lợi nhuận gộp</span>
          </div>
        </Card>

        <Card>
          <CardTitle>Trạng thái lô hàng</CardTitle>
          <div className="space-y-3">
            {statusCounts.map((sc) => (
              <div key={sc.status}>
                <div className="flex items-center justify-between mb-1">
                  <Badge variant={SHIPMENT_STATUS_VARIANT[sc.status]}>{SHIPMENT_STATUS_LABEL[sc.status]}</Badge>
                  <span className="text-[13px] font-bold text-navy-900">{sc.count}</span>
                </div>
                <div className="h-2 rounded-full bg-slate-100 overflow-hidden">
                  <div className="h-full bg-navy-700" style={{ width: `${(sc.count / Math.max(1, shipments.length)) * 100}%` }} />
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card>
          <CardTitle><Users size={17} className="text-accent-500" /> Khách hàng hàng đầu</CardTitle>
          <div className="space-y-3">
            {topCustomers.map((c) => (
              <div key={c.id}>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[13.5px] font-semibold text-navy-900 truncate max-w-[70%]">{c.name}</span>
                  <span className="text-[13px] font-bold text-ink-600">{c.shipmentCount} lô</span>
                </div>
                <div className="h-2 rounded-full bg-slate-100 overflow-hidden">
                  <div className="h-full bg-accent-500" style={{ width: `${(c.shipmentCount / maxShipCount) * 100}%` }} />
                </div>
              </div>
            ))}
          </div>
        </Card>

        <Card>
          <CardTitle><AlertOctagon size={17} className="text-danger-500" /> Điểm nghẽn vận hành thường gặp</CardTitle>
          <div className="space-y-2.5">
            {BOTTLENECKS.map((b) => (
              <div key={b.label} className="flex items-center justify-between gap-3 py-1.5">
                <span className="text-[13.5px] text-ink-900">{b.label}</span>
                <Badge variant="danger">{b.count} lần</Badge>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}
