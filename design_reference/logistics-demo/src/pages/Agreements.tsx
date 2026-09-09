import { useNavigate } from 'react-router-dom';
import { CheckCircle2, Circle, ArrowRight } from 'lucide-react';
import { useAppData } from '../lib/dataContext';
import PageHeader from '../components/ui/PageHeader';
import Card, { CardTitle, Field } from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import Button from '../components/ui/Button';
import EmptyState from '../components/ui/EmptyState';
import { AGREEMENT_STATUS_LABEL, AGREEMENT_STATUS_VARIANT } from '../lib/status';

const STEP_LABELS = ['Báo giá', 'Khách chốt', 'Thỏa thuận', 'Bàn giao Support'];

export default function Agreements() {
  const navigate = useNavigate();
  const { agreements, advanceAgreement, setAgreementStatus } = useAppData();

  return (
    <div>
      <PageHeader title="Thỏa Thuận & Bàn Giao" subtitle="Theo dõi hành trình từ báo giá được chốt tới khi bàn giao đầy đủ cho đội Support vận hành." />

      {agreements.length === 0 ? (
        <Card><EmptyState message="Chưa có thoả thuận nào. Thoả thuận được tạo tự động khi khách hàng chốt báo giá." action={<Button onClick={() => navigate('/kinh-doanh-bao-gia')}>Đi tới Báo Giá</Button>} /></Card>
      ) : (
        <div className="space-y-4">
          {agreements.map((a) => (
            <Card key={a.id}>
              <div className="flex flex-wrap items-start justify-between gap-3 mb-4">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-extrabold text-navy-900 text-[15.5px]">{a.id}</span>
                    <Badge variant={AGREEMENT_STATUS_VARIANT[a.status]}>{AGREEMENT_STATUS_LABEL[a.status]}</Badge>
                  </div>
                  <div className="text-[14px] font-semibold text-ink-900">{a.customer}</div>
                </div>
              </div>

              <div className="flex items-center mb-5">
                {STEP_LABELS.map((label, idx) => {
                  const stepNum = idx + 1;
                  const done = stepNum < a.step;
                  const isCurrent = stepNum === a.step;
                  return (
                    <div key={label} className="flex items-center flex-1 last:flex-none">
                      <div className="flex flex-col items-center gap-1.5 shrink-0">
                        {done ? <CheckCircle2 size={22} className="text-success-500" /> : isCurrent ? <span className="h-[22px] w-[22px] rounded-full bg-accent-500 flex items-center justify-center text-white text-[11px] font-bold">{stepNum}</span> : <Circle size={22} className="text-slate-300" />}
                        <span className={`text-[11px] font-semibold text-center w-24 leading-tight ${done || isCurrent ? 'text-navy-900' : 'text-ink-400'}`}>{label}</span>
                      </div>
                      {idx < STEP_LABELS.length - 1 && <div className={`h-[3px] flex-1 mx-1 rounded-full ${stepNum < a.step ? 'bg-success-500' : 'bg-slate-200'}`} />}
                    </div>
                  );
                })}
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
                <Field label="Incoterm" value={a.incoterm} />
                <Field label="Phạm vi dịch vụ" value={a.scope} missing={!a.scope} />
                <Field label="Điều khoản thanh toán" value={a.paymentTerms} missing={!a.paymentTerms} />
                <Field label="Liên hệ nhà máy" value={a.factoryContact} missing={!a.factoryContact} />
                <Field label="Lô hàng liên kết" value={a.linkedShipmentId ? <button onClick={() => navigate(`/lo-hang/${a.linkedShipmentId}`)} className="text-accent-600 hover:underline">{a.linkedShipmentId}</button> : undefined} missing={!a.linkedShipmentId} />
                <Field label="Chứng từ yêu cầu" value={a.requiredDocs.length ? a.requiredDocs.join(', ') : undefined} missing={a.requiredDocs.length === 0} />
                <Field label="Bằng chứng chấp thuận" value={a.acceptanceEvidence} missing={!a.acceptanceEvidence} />
              </div>

              <div className="flex flex-wrap gap-2 pt-3 border-t border-border">
                {a.step < 4 && a.status !== 'VOID' && (
                  <Button size="sm" icon={<ArrowRight size={14} />} onClick={() => advanceAgreement(a.id)}>
                    {a.step === 3 ? 'BÀN GIAO CHO SUPPORT' : 'CHUYỂN BƯỚC TIẾP THEO'}
                  </Button>
                )}
                {a.status === 'DRAFT' && <Button size="sm" variant="secondary" onClick={() => setAgreementStatus(a.id, 'REVIEWING')}>Gửi xem xét</Button>}
                {a.status === 'REVIEWING' && <Button size="sm" variant="secondary" onClick={() => setAgreementStatus(a.id, 'REVISED')}>Yêu cầu điều chỉnh</Button>}
                {a.step === 4 && !a.linkedShipmentId && <Button size="sm" variant="secondary" onClick={() => navigate('/tao-lo-moi')}>➕ Tạo lô từ thoả thuận</Button>}
                {a.status !== 'VOID' && <Button size="sm" variant="danger" onClick={() => setAgreementStatus(a.id, 'VOID')}>Huỷ thoả thuận</Button>}
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
