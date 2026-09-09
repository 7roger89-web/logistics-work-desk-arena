import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Phone, MapPin, ShieldCheck, ListChecks, FileText, Package } from 'lucide-react';
import { useAppData } from '../lib/dataContext';
import { PARTNER_PROFILES } from '../lib/mockData';
import PageHeader from '../components/ui/PageHeader';
import Card, { CardTitle } from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import Button from '../components/ui/Button';

const RELIABILITY_LABEL = { 'CAO': 'Độ tin cậy cao', 'TRUNG BINH': 'Độ tin cậy trung bình', 'CAN THEO DOI': 'Cần theo dõi sát' } as const;
const RELIABILITY_VARIANT = { 'CAO': 'success', 'TRUNG BINH': 'warning', 'CAN THEO DOI': 'danger' } as const;

export default function PartnerContext() {
  const navigate = useNavigate();
  const { contracts, shipments } = useAppData();
  const [selected, setSelected] = useState(PARTNER_PROFILES[0].name);
  const profile = PARTNER_PROFILES.find((p) => p.name === selected)!;

  const linkedContracts = contracts.filter((c) => c.agent === selected);
  const linkedShipmentIds = new Set(linkedContracts.flatMap((c) => c.linkedShipmentIds));
  const linkedShipments = shipments.filter((s) => linkedShipmentIds.has(s.id));

  return (
    <div>
      <PageHeader title="Ngữ Cảnh Đối Tác" subtitle="Hồ sơ làm việc, đặc điểm hợp tác và ghi chú kinh nghiệm với từng đại lý đối tác." />

      <div className="grid grid-cols-1 lg:grid-cols-[280px_1fr] gap-4">
        <div className="space-y-2.5">
          {PARTNER_PROFILES.map((p) => (
            <Card key={p.name} onClick={() => setSelected(p.name)} className={`!p-3.5 ${selected === p.name ? 'border-navy-700 ring-2 ring-navy-700/20' : ''}`}>
              <div className="font-bold text-navy-900 text-[14px] leading-snug">{p.name}</div>
              <div className="text-[12px] text-ink-400 mt-1">{p.region}</div>
              <Badge variant={RELIABILITY_VARIANT[p.reliability]} className="mt-2">{RELIABILITY_LABEL[p.reliability]}</Badge>
            </Card>
          ))}
        </div>

        <div className="space-y-4">
          <Card>
            <div className="flex flex-wrap items-start justify-between gap-3 mb-4">
              <div>
                <h2 className="text-[19px] font-extrabold text-navy-900">{profile.name}</h2>
                <p className="text-[13.5px] text-ink-600 flex items-center gap-1.5 mt-1"><MapPin size={14} /> {profile.region}</p>
              </div>
              <Badge variant={RELIABILITY_VARIANT[profile.reliability]}>{RELIABILITY_LABEL[profile.reliability]}</Badge>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <div className="text-[12.5px] font-medium text-ink-400 mb-1">Người liên hệ chính</div>
                <div className="text-[14.5px] font-semibold text-navy-900">{profile.contact}</div>
              </div>
              <div>
                <div className="text-[12.5px] font-medium text-ink-400 mb-1 flex items-center gap-1"><Phone size={12} /> Điện thoại</div>
                <div className="text-[14.5px] font-semibold text-navy-900">{profile.phone}</div>
              </div>
              <div>
                <div className="text-[12.5px] font-medium text-ink-400 mb-1">Tuyến hợp tác</div>
                <div className="text-[13.5px] text-ink-900">{profile.routes.join(' · ')}</div>
              </div>
              <div>
                <div className="text-[12.5px] font-medium text-ink-400 mb-1 flex items-center gap-1"><ShieldCheck size={12} /> Điều khoản thanh toán</div>
                <div className="text-[13.5px] text-ink-900">{profile.paymentTerms}</div>
              </div>
            </div>
            <div className="mt-4 pt-4 border-t border-border">
              <div className="text-[12.5px] font-medium text-ink-400 mb-2">Thế mạnh</div>
              <div className="flex flex-wrap gap-2">
                {profile.specialties.map((s) => <Badge key={s} variant="info" icon={false}>{s}</Badge>)}
              </div>
            </div>
          </Card>

          <Card>
            <CardTitle><ListChecks size={17} className="text-accent-500" /> Ghi chú kinh nghiệm làm việc</CardTitle>
            <ul className="space-y-2">
              {profile.workingNotes.map((n, i) => (
                <li key={i} className="flex gap-2.5 text-[14px] text-ink-900"><span className="text-accent-500 shrink-0">●</span>{n}</li>
              ))}
            </ul>
          </Card>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Card>
              <div className="flex items-center justify-between mb-3">
                <CardTitle className="mb-0"><FileText size={16} className="text-accent-500" /> Hợp đồng liên quan</CardTitle>
              </div>
              {linkedContracts.length === 0 ? <p className="text-[13.5px] text-ink-400">Chưa có hợp đồng nào.</p> : (
                <div className="space-y-2">
                  {linkedContracts.map((c) => (
                    <button key={c.id} onClick={() => navigate(`/hop-dong/${c.id}`)} className="w-full text-left text-[13.5px] font-semibold text-accent-600 hover:underline">{c.id} — {c.company}</button>
                  ))}
                </div>
              )}
            </Card>
            <Card>
              <div className="flex items-center justify-between mb-3">
                <CardTitle className="mb-0"><Package size={16} className="text-accent-500" /> Lô hàng liên quan</CardTitle>
              </div>
              {linkedShipments.length === 0 ? <p className="text-[13.5px] text-ink-400">Chưa có lô hàng nào.</p> : (
                <div className="space-y-2">
                  {linkedShipments.map((s) => (
                    <button key={s.id} onClick={() => navigate(`/lo-hang/${s.id}`)} className="w-full text-left text-[13.5px] font-semibold text-accent-600 hover:underline">{s.id} — {s.customer}</button>
                  ))}
                </div>
              )}
            </Card>
          </div>
          <Button variant="secondary" onClick={() => navigate('/cong-no-doi-tac')}>Xem công nợ với đại lý này</Button>
        </div>
      </div>
    </div>
  );
}
