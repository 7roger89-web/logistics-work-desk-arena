import { useNavigate } from 'react-router-dom';
import { CheckCircle2, Circle } from 'lucide-react';
import { useAppData } from '../lib/dataContext';
import PageHeader from '../components/ui/PageHeader';
import Card from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import { SHIPMENT_STATUS_LABEL, SHIPMENT_STATUS_VARIANT } from '../lib/status';
import type { ShipmentStatus } from '../lib/types';

const STEPS: { key: ShipmentStatus; label: string }[] = [
  { key: 'CHO_LAY_HANG', label: 'Chờ lấy hàng' },
  { key: 'DANG_VAN_CHUYEN', label: 'Đang vận chuyển' },
  { key: 'CHO_THONG_QUAN', label: 'Chờ thông quan' },
  { key: 'CHO_GIAO', label: 'Chờ giao' },
  { key: 'DA_GIAO', label: 'Đã giao' },
];

export default function Tracking() {
  const navigate = useNavigate();
  const { shipments } = useAppData();
  const active = shipments;

  return (
    <div>
      <PageHeader title="Theo Dõi Vận Chuyển" subtitle="Tiến trình thực tế của từng lô hàng qua các mốc vận hành chính, từ lấy hàng tới giao hàng." />
      <div className="space-y-4">
        {active.map((s) => {
          const currentIdx = STEPS.findIndex((st) => st.key === s.status);
          return (
            <Card key={s.id} className="hover:border-navy-700/30 transition-colors cursor-pointer" >
              <button onClick={() => navigate(`/lo-hang/${s.id}`)} className="w-full text-left">
                <div className="flex flex-wrap items-center justify-between gap-2 mb-4">
                  <div>
                    <span className="font-extrabold text-navy-900 text-[17px]">{s.id}</span>
                    <span className="text-ink-600 text-[13.5px] ml-2">{s.customer}</span>
                  </div>
                  <Badge variant={SHIPMENT_STATUS_VARIANT[s.status]}>{SHIPMENT_STATUS_LABEL[s.status]}</Badge>
                </div>
                <div className="flex items-center">
                  {STEPS.map((st, idx) => {
                    const done = idx < currentIdx || (idx === currentIdx && s.status === 'DA_GIAO');
                    const isCurrent = idx === currentIdx && s.status !== 'DA_GIAO';
                    return (
                      <div key={st.key} className="flex items-center flex-1 last:flex-none">
                        <div className="flex flex-col items-center gap-1.5 shrink-0">
                          {done ? <CheckCircle2 size={22} className="text-success-500" /> : isCurrent ? <span className="h-[22px] w-[22px] rounded-full bg-accent-500 flex items-center justify-center"><span className="h-2 w-2 rounded-full bg-white" /></span> : <Circle size={22} className="text-slate-300" />}
                          <span className={`text-[11px] font-semibold text-center w-20 leading-tight ${done || isCurrent ? 'text-navy-900' : 'text-ink-400'}`}>{st.label}</span>
                        </div>
                        {idx < STEPS.length - 1 && <div className={`h-[3px] flex-1 mx-1 rounded-full ${idx < currentIdx ? 'bg-success-500' : 'bg-slate-200'}`} />}
                      </div>
                    );
                  })}
                </div>
                <div className="mt-4 pt-3 border-t border-border text-[13.5px] text-navy-900 font-medium">➡ {s.nextAction}</div>
              </button>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
