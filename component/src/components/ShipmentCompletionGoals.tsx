import type { Shipment } from '../lib/viewmodel';
import { CheckCircle2, CircleAlert, CircleHelp, MinusCircle } from 'lucide-react';
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
  const origin = nodeGroup(s, ['booking', 'pickup', 'customs-export', 'si-vgm', 'gate-in']);
  const main = nodeGroup(s, ['etd', 'on-board', 'transit', 'arrival']);
  const importDelivery = nodeGroup(s, ['customs-import', 'delivery']);
  const steps = s.documentWorkflow?.steps ?? [];
  const applicableDocs = steps.filter(x => x.state !== 'NOT_APPLICABLE');
  const hardDoc = applicableDocs.find(x => x.state === 'BLOCKED' || x.state === 'MISSING_INFO');
  const completeDocs = applicableDocs.filter(x => x.state === 'COMPLETE');
  const financeKnown = [s.finance.receivable, s.finance.outstanding, s.finance.payable, s.finance.paid]
    .some(v => v !== null && v !== undefined);
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
      state: financeKnown ? 'EVIDENCED' : 'UNKNOWN',
      evidence: financeKnown ? 'Đã có số liệu tài chính/ledger để kiểm tra.' : 'Chưa có đủ dữ liệu để kết luận số dư.',
      missing: financeKnown ? 'Mở Tài chính để kiểm tra khoản thu/phải trả/đối soát; có số liệu không đồng nghĩa đã tất toán.' : 'UNKNOWN được giữ nguyên, không đổi thành 0/đã trả.',
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
  const goals = composeShipmentCompletionGoals(s);
  const counted = goals.filter(g => g.state !== 'NOT_APPLICABLE');
  const evidenced = counted.filter(g => g.state === 'EVIDENCED').length;
  const action = counted.filter(g => g.state === 'ACTION').length;
  const unknown = counted.filter(g => g.state === 'UNKNOWN').length;
  return <section className="rounded-2xl border border-slate-200 bg-white p-4" data-testid="shipment-completion-goals">
    <div className="flex flex-wrap items-start justify-between gap-2">
      <div>
        <p className="text-[11px] font-extrabold uppercase tracking-widest text-slate-500">Mục tiêu hoàn tất lô · read-only</p>
        <h2 className="text-lg font-extrabold text-[#0f2a4a]">Còn gì phải rà trước khi coi là xử lý đủ?</h2>
        <p className="mt-1 text-sm text-slate-500">Đây là lớp hướng dẫn trên dữ liệu hiện có, không phải % hoàn thành hay trạng thái CLOSED.</p>
      </div>
      <p className="rounded-lg bg-slate-100 px-3 py-2 text-xs font-bold text-slate-700" data-testid="completion-goal-summary">
        {evidenced} mục có bằng chứng · {action} mục cần xử lý · {unknown} mục chưa xác định
      </p>
    </div>
    <div className="mt-3 grid grid-cols-1 gap-2 lg:grid-cols-2 xl:grid-cols-3">
      {goals.map(g => <article key={g.id} className={cx('rounded-xl border p-3', STYLE[g.state])} data-testid={`completion-goal-${g.id}`} data-state={g.state}>
        <div className="flex items-center gap-2"><Icon state={g.state} /><h3 className="font-extrabold">{g.title}</h3><span className="ml-auto text-[11px] font-bold">{LABEL[g.state]}</span></div>
        <dl className="mt-2 space-y-1 text-xs">
          <div><dt className="font-bold opacity-70">Bằng chứng hiện có</dt><dd>{g.evidence}</dd></div>
          <div><dt className="font-bold opacity-70">Còn thiếu / cần kiểm tra</dt><dd>{g.missing}</dd></div>
          <div><dt className="font-bold opacity-70">Xong khi</dt><dd>{g.doneWhen}</dd></div>
        </dl>
        {g.state !== 'NOT_APPLICABLE' && <button type="button" onClick={() => onOpenTab(g.tab)}
          className="touch-target mt-2 rounded-lg border border-current bg-white/70 px-2.5 py-1.5 text-xs font-extrabold">Mở chỗ xử lý →</button>}
      </article>)}
    </div>
  </section>;
}
