import { useState } from 'react';
import type { Shipment } from '../lib/viewmodel';
import { CheckCircle2, CircleAlert, CircleHelp, ChevronDown, MinusCircle } from 'lucide-react';
import { cx } from '../lib/format';

export type CompletionGoalState = 'EVIDENCED' | 'ACTION' | 'UNKNOWN' | 'NOT_APPLICABLE';

export interface CompletionGoal {
  id: string;
  title: string;
  state: CompletionGoalState;
  evidence: string;
  missing: string;
  doneWhen: string;
  tab: string;
}

const LABEL: Record<CompletionGoalState, string> = {
  EVIDENCED: 'Có bằng chứng',
  ACTION: 'Cần xử lý',
  UNKNOWN: 'Chưa xác định',
  NOT_APPLICABLE: 'Không áp dụng',
};

const STYLE: Record<CompletionGoalState, string> = {
  EVIDENCED: 'border-emerald-200 bg-emerald-50 text-emerald-900',
  ACTION: 'border-red-200 bg-red-50 text-red-900',
  UNKNOWN: 'border-slate-300 bg-slate-50 text-slate-700',
  NOT_APPLICABLE: 'border-slate-200 bg-white text-slate-500',
};

function nodeGroup(s: Shipment, ids: string[]) {
  const nodes = (s.journey?.nodes ?? []).filter(n => !n.moduleId && ids.includes(n.id));
  const problem = nodes.find(n => n.state === 'PROBLEM' || n.blockers.length > 0);
  const factual = nodes.filter(n => n.completed || Boolean(n.evidence));
  return { nodes, problem, factual };
}

export function composeShipmentCompletionGoals(s: Shipment): CompletionGoal[] {
  const profile = s.executionProfile;
  const origin = nodeGroup(s, ['booking', 'pickup', 'customs-export', 'si-vgm', 'gate-in', 'cfs-receipt', 'air-booking', 'air-acceptance', 'road-vehicle', 'road-ltl']);
  const main = nodeGroup(s, ['etd', 'on-board', 'transit', 'arrival', 'uplift', 'air-transit', 'air-arrival', 'road-border']);
  const importDelivery = nodeGroup(s, ['customs-import', 'delivery']);
  const steps = s.documentWorkflow?.steps ?? [];
  const applicableDocs = steps.filter(x => x.state !== 'NOT_APPLICABLE');
  const hardDoc = applicableDocs.find(x => x.state === 'BLOCKED' || x.state === 'MISSING_INFO');
  const completeDocs = applicableDocs.filter(x => x.state === 'COMPLETE');
  const customerOutstanding = s.finance.outstanding;
  const customerOutstandingKnown = customerOutstanding !== null && customerOutstanding !== undefined;
  const partner = s.finance.partner;
  const partnerGroups = partner?.partners ?? [];
  const partnerRelevant = partnerGroups.length > 0 || Boolean(partner && !partner.suggested && partner.partnerName);
  const partnerRemaining = partnerGroups.length > 0
    ? partnerGroups.flatMap(g => Object.values(g.totalsByCurrency).map(t => t.remaining))
    : partner && !partner.suggested && partner.partnerName ? [partner.remaining] : [];
  const knownPartnerRemaining = partnerRemaining.filter((v): v is number => v !== null && v !== undefined);
  const partnerUnknown = partnerRelevant && (partnerRemaining.length === 0 || knownPartnerRemaining.length !== partnerRemaining.length);
  const financeOpen = (customerOutstandingKnown && customerOutstanding !== 0)
    || knownPartnerRemaining.some(v => v !== 0);
  const financeKnown = customerOutstandingKnown || (partnerRelevant && !partnerUnknown && knownPartnerRemaining.length > 0);
  const modules = s.journey?.modules ?? [];
  const moduleBlocker = modules.find(m => m.status === 'BLOCKING');
  const moduleEvidence = modules.filter(m => m.status === 'DONE');

  return [
    {
      id: 'profile',
      title: 'Hồ sơ & phạm vi',
      state: profile?.state === 'PROFILE_READY' ? 'EVIDENCED' : profile?.state ? 'ACTION' : 'UNKNOWN',
      evidence: profile?.state === 'PROFILE_READY'
        ? (profile.serviceScopeSummary || 'Phạm vi lô đã được xác định.')
        : profile?.summaryLines?.[0] || 'Chưa đủ bằng chứng về phạm vi lô.',
      missing: profile?.issues?.map(x => x.message || x.code).filter(Boolean).slice(0, 2).join(' · ') || (profile?.state === 'PROFILE_READY' ? 'Không có thiếu sót hồ sơ đang được chiếu.' : 'Cần xác nhận hồ sơ/phạm vi.'),
      doneWhen: 'Thông tin lô và phạm vi dịch vụ được xác nhận; đây không phải trạng thái hoàn tất toàn lô.',
      tab: 'van-tai',
    },
    {
      id: 'origin',
      title: 'Chuẩn bị & đầu đi',
      state: origin.problem ? 'ACTION' : origin.factual.length ? 'EVIDENCED' : origin.nodes.length ? 'UNKNOWN' : 'NOT_APPLICABLE',
      evidence: origin.factual.map(n => n.evidence || n.label).filter(Boolean).slice(0, 2).join(' · ') || 'Chưa có bằng chứng mốc đầu đi.',
      missing: origin.problem?.blockers.join(' · ') || (origin.nodes.length ? 'Không có blocker riêng được ghi nhận.' : 'Không có công đoạn đầu đi trong Journey hiện tại.'),
      doneWhen: 'Các mốc đầu đi liên quan phải có bằng chứng thực tế; số tờ khai không tự chứng minh thông quan.',
      tab: 'lay-hang',
    },
    {
      id: 'main',
      title: 'Chặng chính / hàng đến',
      state: main.problem ? 'ACTION' : main.factual.length ? 'EVIDENCED' : main.nodes.length ? 'UNKNOWN' : 'NOT_APPLICABLE',
      evidence: main.factual.map(n => n.evidence || n.label).filter(Boolean).slice(0, 2).join(' · ') || 'Chưa có bằng chứng mốc thực tế của chặng chính.',
      missing: main.problem?.blockers.join(' · ') || (main.nodes.length ? 'ETD/ETA chỉ là lịch; cần mốc thực tế khi có.' : 'Không có chặng chính trong Journey hiện tại.'),
      doneWhen: 'ATD/ATA hoặc bằng chứng thực tế tương ứng được ghi nhận; lịch dự kiến không được coi là đã xảy ra.',
      tab: 'van-tai',
    },
    {
      id: 'import-delivery',
      title: 'Nhập khẩu & giao hàng',
      state: importDelivery.problem ? 'ACTION' : importDelivery.factual.length ? 'EVIDENCED' : importDelivery.nodes.length ? 'UNKNOWN' : 'NOT_APPLICABLE',
      evidence: importDelivery.factual.map(n => n.evidence || n.label).filter(Boolean).slice(0, 2).join(' · ') || 'Chưa có bằng chứng nhập khẩu/giao hàng.',
      missing: importDelivery.problem?.blockers.join(' · ') || (importDelivery.nodes.length ? 'Thông quan và giao thực tế phải được xác nhận riêng.' : 'Không có công đoạn nhập/giao trong phạm vi hiện tại.'),
      doneWhen: 'Đăng ký tờ khai, thông quan và giao thực tế giữ các bằng chứng riêng; bước sau không được suy ra từ bước trước.',
      tab: 'nhap',
    },
    {
      id: 'documents',
      title: 'Hồ sơ & chứng từ',
      state: hardDoc ? 'ACTION' : applicableDocs.length === 0 ? 'NOT_APPLICABLE' : completeDocs.length === applicableDocs.length ? 'EVIDENCED' : 'UNKNOWN',
      evidence: applicableDocs.length ? `${completeDocs.length}/${applicableDocs.length} mục có trạng thái COMPLETE.` : 'Không có chứng từ áp dụng trong workflow hiện tại.',
      missing: hardDoc ? `${hardDoc.label}: ${hardDoc.reason}` : applicableDocs.some(x => x.state !== 'COMPLETE') ? 'Còn mục đang chờ/điều kiện; không tự coi là blocker đóng lô.' : 'Không có thiếu sót chứng từ đang được chiếu.',
      doneWhen: 'Mỗi chứng từ dùng đúng trạng thái và bằng chứng của workflow; upload không tự hoàn thành nghiệp vụ.',
      tab: 'chung-tu',
    },
    {
      id: 'finance',
      title: 'Tài chính & đối soát',
      state: financeOpen ? 'ACTION' : partnerUnknown ? 'UNKNOWN' : financeKnown ? 'EVIDENCED' : 'UNKNOWN',
      evidence: financeOpen
        ? 'Đã có số dư tài chính còn mở cần rà soát.'
        : financeKnown && !partnerUnknown
          ? 'Các số dư closeout hiện có không ghi nhận khoản khác 0 đang mở.'
          : 'Chưa có đủ dữ liệu để kết luận số dư.',
      missing: financeOpen
        ? 'Còn công nợ/số dư phải xử lý hoặc đối soát; không được coi là tài chính đã khép.'
        : partnerUnknown
          ? 'Có đối tác/ledger liên quan nhưng số dư còn lại chưa đủ authority; giữ UNKNOWN.'
          : financeKnown
            ? 'Không có số dư mở được ghi nhận ở authority hiện có; đây vẫn chỉ là bằng chứng rà soát, không phải CLOSED toàn lô.'
            : 'UNKNOWN được giữ nguyên, không đổi thành 0/đã trả.',
      doneWhen: 'Khoản thu, phải trả và phân bổ được rà soát trên authority tài chính hiện có; không suy ra trạng thái CLOSED toàn lô.',
      tab: 'tai-chinh',
    },
    {
      id: 'modules',
      title: 'Quy trình phát sinh',
      state: moduleBlocker ? 'ACTION' : modules.length === 0 ? 'NOT_APPLICABLE' : moduleEvidence.length === modules.length ? 'EVIDENCED' : 'UNKNOWN',
      evidence: modules.length ? `${moduleEvidence.length}/${modules.length} quy trình gắn đã DONE.` : 'Lô không có Work Module đang gắn.',
      missing: moduleBlocker ? (moduleBlocker.gateText || moduleBlocker.blocker || 'Có quy trình đang chặn.') : modules.some(m => m.status !== 'DONE') ? 'Còn quy trình WAITING/UNKNOWN; không tự hoàn thành từ file upload.' : 'Không có bước module còn mở.',
      doneWhen: 'Từng bước Work Module phải có business fact hoàn thành theo writer hiện có.',
      tab: 'van-tai',
    },
  ];
}

function Icon({ state }: { state: CompletionGoalState }) {
  if (state === 'EVIDENCED') return <CheckCircle2 size={16} aria-hidden="true" />;
  if (state === 'ACTION') return <CircleAlert size={16} aria-hidden="true" />;
  if (state === 'NOT_APPLICABLE') return <MinusCircle size={16} aria-hidden="true" />;
  return <CircleHelp size={16} aria-hidden="true" />;
}

export default function ShipmentCompletionGoals({ shipment: s, onOpenTab }: {
  shipment: Shipment;
  onOpenTab: (tab: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const goals = composeShipmentCompletionGoals(s);
  const counted = goals.filter(g => g.state !== 'NOT_APPLICABLE');
  const evidenced = counted.filter(g => g.state === 'EVIDENCED').length;
  const action = counted.filter(g => g.state === 'ACTION').length;
  const unknown = counted.filter(g => g.state === 'UNKNOWN').length;
  return <section className="rounded-xl border border-slate-200 bg-white" data-testid="shipment-completion-goals">
    <button type="button" onClick={() => setOpen(v => !v)} aria-expanded={open}
      className="touch-target flex w-full items-center gap-3 px-3 py-2.5 text-left" data-testid="completion-goal-toggle">
      <div className="min-w-0 flex-1">
        <p className="text-[12px] font-extrabold uppercase tracking-widest text-slate-500">Rà soát trước khi kết thúc lô · read-only</p>
        <p className="mt-0.5 text-[13px] font-semibold text-slate-600">Tự tổng hợp từ dữ liệu đang có — không phải các trường bắt buộc phải điền khi tạo lô, và không phải trạng thái CLOSED.</p>
      </div>
      <span className={cx('shrink-0 rounded-lg px-2.5 py-1.5 text-xs font-extrabold',
        action > 0 ? 'bg-red-50 text-red-800 ring-1 ring-red-200' : unknown > 0 ? 'bg-amber-50 text-amber-800 ring-1 ring-amber-200' : 'bg-slate-100 text-slate-700')}
        data-testid="completion-goal-summary">
        {action > 0 ? `${action} việc cần xử lý` : unknown > 0 ? `${unknown} mục chưa xác định` : `${evidenced} mục có bằng chứng`}
      </span>
      <ChevronDown size={17} className={cx('shrink-0 text-slate-500 transition-transform', open && 'rotate-180')} aria-hidden="true" />
    </button>
    {open && <div className="border-t border-slate-200 p-3" data-testid="completion-goal-details">
      <p className="mb-2 text-xs text-slate-500">Rà soát read-only: đây không phải % hoàn thành hay trạng thái CLOSED toàn lô — mỗi mục chỉ phản ánh bằng chứng đang có.</p>
      <div className="grid grid-cols-1 gap-2 lg:grid-cols-2 xl:grid-cols-3">
        {goals.map(g => <article key={g.id} className={cx('rounded-xl border p-3', STYLE[g.state])} data-testid={`completion-goal-${g.id}`} data-state={g.state}>
          <div className="flex items-center gap-2"><Icon state={g.state} /><h3 className="font-extrabold">{g.title}</h3><span className="ml-auto text-[12px] font-bold">{LABEL[g.state]}</span></div>
          <dl className="mt-2 space-y-1 text-xs">
            <div><dt className="font-bold opacity-70">Bằng chứng hiện có</dt><dd>{g.evidence}</dd></div>
            <div><dt className="font-bold opacity-70">Còn thiếu / cần kiểm tra</dt><dd>{g.missing}</dd></div>
            <div><dt className="font-bold opacity-70">Xong khi</dt><dd>{g.doneWhen}</dd></div>
          </dl>
          {g.state !== 'NOT_APPLICABLE' && <button type="button" onClick={() => onOpenTab(g.tab)}
            className="touch-target mt-2 rounded-lg border border-current bg-white/70 px-2.5 py-1.5 text-xs font-extrabold">Mở chỗ xử lý →</button>}
        </article>)}
      </div>
    </div>}
  </section>;
}
