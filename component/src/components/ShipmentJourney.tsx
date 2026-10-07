import { useEffect, useMemo, useState, useSyncExternalStore } from 'react';
import { ArrowRight, CheckCircle2, Circle, Clock, CircleAlert, ChevronDown, ChevronRight, Info, Layers, MapPin, Plus } from 'lucide-react';
import type { JourneyNode, Shipment, WorkModuleGuidance, WorkModuleRollup } from '../lib/viewmodel';
import { getViewModel, subscribeViewModel } from '../lib/viewmodel';
import { useStore } from '../lib/store';
import { cx, fmtCcy } from '../lib/format';
import { Field, inputCls } from './ui';

export const JOURNEY_WORK = [
  { id: 'overview', label: 'Tổng quan' }, { id: 'info', label: 'Thông tin' },
  { id: 'docs', label: 'Chứng từ' }, { id: 'costs', label: 'Chi phí' }, { id: 'history', label: 'Lịch sử' },
];
const META = {
  COMPLETED: { label: 'Hoàn thành', icon: CheckCircle2, cls: 'border-emerald-300 bg-emerald-50 text-emerald-900' },
  CURRENT: { label: 'Hiện tại', icon: MapPin, cls: 'border-blue-500 bg-blue-50 text-blue-950' },
  UPCOMING: { label: 'Chưa xác định / sắp tới', icon: Circle, cls: 'border-dashed border-slate-300 bg-slate-50 text-slate-700' },
  WAITING: { label: 'Đang chờ', icon: Clock, cls: 'border-dashed border-amber-400 bg-amber-50 text-amber-950' },
  PROBLEM: { label: 'Cần xử lý', icon: CircleAlert, cls: 'border-red-400 bg-red-50 text-red-900' },
};
// Issue #162 — the human half of a module: readable status + gate language.
const MODULE_STATUS_META: Record<string, { label: string; cls: string }> = {
  DONE: { label: 'Hoàn thành', cls: 'border-emerald-300 bg-emerald-50 text-emerald-900' },
  WAITING: { label: 'Đang chờ', cls: 'border-amber-300 bg-amber-50 text-amber-950' },
  BLOCKING: { label: 'Đang chặn', cls: 'border-red-300 bg-red-50 text-red-900' },
  UNKNOWN: { label: 'Chưa xác định', cls: 'border-slate-300 bg-slate-50 text-slate-700' },
};
const PROVENANCE_LABEL: Record<string, string> = {
  MANUAL_ADDITION: 'Thêm thủ công',
  COMPANY_STANDARD: 'Chuẩn công ty',
};
const GUIDANCE_ROWS: { key: keyof WorkModuleGuidance; label: string }[] = [
  { key: 'why', label: 'WHY — vì sao' },
  { key: 'what_to_do', label: 'WHAT TO DO — cần làm gì' },
  { key: 'who', label: 'WHO — ai làm' },
  { key: 'when', label: 'WHEN — khi nào' },
  { key: 'needs', label: 'NEEDS — cần gì' },
  { key: 'done_when', label: 'DONE WHEN — xong khi nào' },
  { key: 'impact', label: 'IMPACT if incomplete — nếu chưa xong' },
];
const SEA_POS: Record<string, [number, number]> = {
  booking: [0, 0], pickup: [1, 0], 'customs-export': [2, 0], 'si-vgm': [3, 0],
  'gate-in': [3, 1], etd: [2, 1], 'on-board': [1, 1], transit: [0, 1],
  arrival: [0, 2], 'customs-import': [1, 2], delivery: [2, 2],
};
function Status({ node }: { node: JourneyNode }) {
  const m = META[node.state]; const Icon = m.icon;
  return <span className="inline-flex items-center gap-1 text-xs font-bold"><Icon size={14} aria-hidden="true" />{m.label}</span>;
}

/** Issue #162 — ONE compact, readable rollup per attached module. */
function ModuleCard({ module: m, nodes, expanded, onToggle, onPick, selectedId }: {
  module: WorkModuleRollup; nodes: JourneyNode[]; expanded: boolean;
  onToggle: () => void; onPick: (id: string) => void; selectedId: string;
}) {
  const meta = MODULE_STATUS_META[m.status] ?? MODULE_STATUS_META.UNKNOWN;
  const Icon = m.status === 'DONE' ? CheckCircle2 : m.status === 'BLOCKING' ? CircleAlert : Clock;
  const stepIds = m.steps.map(s => s.id);
  return <article className="rounded-xl border border-slate-200 bg-white p-3" data-testid={`journey-module-${m.instanceId}`} data-module-status={m.status}>
    <div className="flex flex-wrap items-start gap-2">
      <div className="min-w-0 flex-1">
        <p className="text-[11px] font-bold tracking-wide text-slate-500">QUY TRÌNH PHÁT SINH · V{m.templateVersion}</p>
        <h4 className="font-extrabold text-[15px] text-[#0f2a4a]">{m.name}</h4>
      </div>
      <span className={cx('inline-flex items-center gap-1 rounded-lg border px-2 py-1 text-xs font-bold', meta.cls)} data-testid={`journey-module-status-${m.instanceId}`}>
        <Icon size={13} aria-hidden="true" />{meta.label}
      </span>
      <span className="rounded-lg border border-slate-200 bg-slate-50 px-2 py-1 text-xs font-bold text-slate-700" data-testid={`journey-module-progress-${m.instanceId}`}>{m.summary}</span>
    </div>
    {m.gateText
      ? <p className="mt-2 rounded-lg border border-red-200 bg-red-50 px-2 py-1 text-sm font-semibold text-red-900" data-testid={`journey-module-gate-${m.instanceId}`}>{m.gateText}</p>
      : m.status === 'UNKNOWN'
        ? <p className="mt-2 rounded-lg border border-slate-300 bg-slate-50 px-2 py-1 text-sm font-semibold text-slate-700" data-testid={`journey-module-gate-${m.instanceId}`}>Chưa xác định — không đọc được phiên bản quy trình đã gắn. UNKNOWN không được coi là hoàn thành.</p>
        : <p className="mt-2 text-sm text-slate-600">Không chặn cổng nào{m.anchorLabel ? ` · neo tại ${m.anchorLabel}` : ''}.</p>}
    <dl className="mt-2 grid grid-cols-1 gap-1 text-sm sm:grid-cols-2">
      <div><dt className="text-xs text-slate-500">Bước tiếp theo</dt><dd className="font-semibold">{m.nextStep || (m.status === 'DONE' ? 'Đã xong toàn bộ' : 'Chưa xác định')}</dd></div>
      <div><dt className="text-xs text-slate-500">Mốc / hạn gần nhất</dt><dd className="font-semibold">{m.deadline || 'Chưa ghi nhận'}</dd></div>
      {m.blocker && <div className="sm:col-span-2"><dt className="text-xs text-slate-500">Ảnh hưởng</dt><dd className="font-semibold text-red-900">{m.blocker}</dd></div>}
    </dl>
    <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-slate-500">
      <span>Nguồn: {PROVENANCE_LABEL[m.provenance] ?? m.provenance}</span>
      <span aria-hidden="true">·</span>
      <span>{m.addedBy || 'Chưa ghi nhận người thêm'}</span>
      {m.addedAt && <><span aria-hidden="true">·</span><span>{m.addedAt.slice(0, 10)}</span></>}
      <button type="button" onClick={onToggle} aria-expanded={expanded} data-testid={`journey-module-toggle-${m.instanceId}`}
        className="touch-target ml-auto inline-flex items-center gap-1 rounded-lg border px-2 py-1 font-bold text-slate-700">
        {expanded ? <ChevronDown size={14} aria-hidden="true" /> : <ChevronRight size={14} aria-hidden="true" />}
        {expanded ? 'Ẩn các bước' : `Xem ${stepIds.length} bước`}
      </button>
    </div>
    {expanded && <div className="mt-3 flex flex-wrap items-center gap-1 border-t pt-3" data-testid={`journey-module-steps-${m.instanceId}`}>
      {stepIds.map((stepId, index) => {
        const node = nodes.find(n => n.id === `wm-${m.instanceId}-${stepId}`);
        return <div key={stepId} className="flex items-center gap-1">
          {index > 0 && <span className="text-slate-400" aria-hidden="true">→</span>}
          {node && <ModuleStepButton node={node} onPick={onPick} selectedId={selectedId} />}
        </div>;
      })}
    </div>}
  </article>;
}

/**
 * ONE module step, rendered with the SAME node interaction as the base journey:
 * click → Quick Panel → Stage Workspace. There is deliberately no second
 * visual language and no expanded spaghetti graph by default.
 */
function ModuleStepButton({ node, onPick, selectedId }: {
  node: JourneyNode; onPick: (id: string) => void; selectedId: string;
}) {
  const id = node.id;
  const m = META[node.state]; const Icon = m.icon;
  return <button type="button" data-testid={`journey-node-${id}`} data-state={node.state}
    aria-pressed={selectedId === id} onClick={() => onPick(id)}
    className={cx('flex min-w-[168px] flex-col rounded-xl border-2 p-2 text-left focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-700', m.cls, selectedId === id && 'ring-2 ring-[#0f2a4a] ring-offset-2')}>
    <span className="inline-flex items-center gap-1 text-[11px] font-bold"><Icon size={13} aria-hidden="true" />{m.label}</span>
    <span className="mt-0.5 text-sm font-extrabold">{node.label}</span>
    <span className="text-[11px]">{node.evidence || 'Chưa có bằng chứng thực tế'}</span>
  </button>;
}

/**
 * Issue #184 — Customs Import Quick Panel (product slice 01).
 *
 * A V3-hierarchy projection of EXISTING product authorities for the real
 * `customs-import` node. It creates no store, no engine, no writer:
 *
 * - declaration / clearance / tax / VAT / GNT  <- s.importInfo
 * - legal importer                            <- s.commercialFlow
 * - partner obligations (multi-group, G06)    <- s.finance.partner
 * - workflow step states                      <- s.documentWorkflow
 * - module rollup                             <- s.journey.modules
 * - ONE primary action                        <- s.journey.primaryAction (-> runPrimary)
 *
 * Semantic locks enforced here:
 * - declaration registration != customs clearance (tk_no alone never renders
 *   "Đã thông quan"; only customsStatus/clearDate prove clearance).
 * - generated GNT != tax paid (three separate states; no payment authority
 *   exists, so "paid" honestly reports "no evidence").
 * - unknown money renders "—", never 0 (MaybeNum + fmtCcy).
 * - no cross-currency totals (per-group, per-currency rows only).
 *
 * Issue #184 §16 authority gap (documented, not worked around): no canonical
 * module/document/dependency authority currently links a specific invoice
 * attachment to the payment-request action, so this panel does NOT invent an
 * invoice prerequisite. Payment-request steps render their canonical
 * CONDITIONAL state and reason from the document workflow.
 */
function CustomsImportQuickPanel({ s, selected, onOpen, runPrimary }: {
  shipment: Shipment; selected: JourneyNode;
  onOpen: (node: JourneyNode, work: string) => void; runPrimary: () => void;
}) {
  const info = s.importInfo;
  const flow = s.commercialFlow;
  const partner = s.finance?.partner;
  const groups = partner?.partners ?? [];
  const gnt = info.gnt;
  const modules = s.journey?.modules ?? [];
  const module = modules.find(m => m.anchorLabel === selected.label)
    ?? modules.find(m => m.gate?.stage === selected.id)
    ?? modules[0];
  const primary = s.journey?.primaryAction;
  const workflowSteps = s.documentWorkflow?.steps ?? [];
  // Import-relevant workflow steps, most urgent first. BLOCKED beats
  // MISSING_INFO beats CONDITIONAL; the panel never invents urgency.
  const stepRank = (state: string) =>
    ({ BLOCKED: 0, MISSING_INFO: 1, CONDITIONAL: 2 } as Record<string, number>)[state] ?? 3;
  const urgentStep = [...workflowSteps]
    .filter(st => st.targetTab === 'nhap' || st.id === 'tax_payment')
    .sort((a, b) => stepRank(a.state) - stepRank(b.state))[0];
  const cleared = Boolean(info.customsStatus);
  const gntDoc = gnt?.document;
  const money = (n: number | null | undefined, ccy?: string | null) =>
    <span className="font-bold">{fmtCcy(n ?? null, ccy ?? 'VND')}</span>;
  return <div className="space-y-3" data-testid="customs-import-quick-panel">
    <div>
      <span className="text-xs font-bold text-slate-500">XEM NHANH</span>
      <h3 className="text-xl font-extrabold text-[#0f2a4a]">NHẬP KHẨU</h3>
      <Status node={selected} />
    </div>

    <div className="rounded-lg border border-slate-200 p-3 text-sm" data-testid="ci-registration-clearance">
      <div className="flex items-start justify-between gap-2">
        <span className="text-slate-500">Tờ khai (đăng ký)</span>
        <span className="text-right font-bold">{info.declarationNo || 'Chưa có thông tin'}{info.regDate ? ` · ${info.regDate}` : ''}</span>
      </div>
      <div className="mt-1 flex items-start justify-between gap-2">
        <span className="text-slate-500">Thông quan</span>
        {cleared
          ? <span className="text-right font-bold text-emerald-800">Đã xác nhận{info.clearDate ? ` · ${info.clearDate}` : ''}</span>
          : <span className="text-right font-bold text-red-700">Chưa xác nhận</span>}
      </div>
      {!cleared && info.declarationNo && <p className="mt-1 text-xs text-slate-500">Số tờ khai chỉ chứng minh đã đăng ký, chưa chứng minh đã thông quan.</p>}
    </div>

    {(primary?.text || urgentStep) && <div className="rounded-lg border-2 border-red-600 bg-red-50 p-3" data-testid="ci-next-action">
      <p className="text-xs font-extrabold tracking-wide text-red-700">CẦN LÀM NGAY</p>
      <p className="mt-0.5 font-extrabold text-red-900">{urgentStep && (urgentStep.state === 'BLOCKED' || urgentStep.state === 'MISSING_INFO') ? urgentStep.label : primary?.text}</p>
      <p className="mt-0.5 text-sm text-red-800">{urgentStep && (urgentStep.state === 'BLOCKED' || urgentStep.state === 'MISSING_INFO') ? urgentStep.reason : primary?.detail}</p>
      <button type="button" onClick={runPrimary} data-testid="ci-primary-cta"
        className="touch-target mt-2 w-full rounded-lg bg-red-600 px-4 py-2.5 font-extrabold text-white">{s.nextLabel || 'Xử lý ngay'}</button>
    </div>}

    <div>
      <p className="mb-1 text-xs font-extrabold tracking-wide text-slate-500">THÔNG TIN CHÍNH</p>
      <dl className="divide-y divide-slate-100 rounded-lg border border-slate-200 text-sm">
        <div className="flex items-start justify-between gap-2 px-3 py-1.5"><dt className="text-slate-500">Người nhập khẩu</dt><dd className="text-right font-bold">{flow?.legalImporterName || 'Chưa có thông tin'}</dd></div>
        <div className="flex items-start justify-between gap-2 px-3 py-1.5"><dt className="text-slate-500">Thuế NK</dt><dd className="text-right">{money(info.tax)}</dd></div>
        <div className="flex items-start justify-between gap-2 px-3 py-1.5"><dt className="text-slate-500">VAT</dt><dd className="text-right">{money(info.vat)}</dd></div>
        <div className="flex items-start justify-between gap-2 px-3 py-1.5"><dt className="text-slate-500">GNT đã tạo</dt><dd className="text-right font-bold">{gntDoc ? gntDoc.fileName || 'Đã tạo' : 'Chưa tạo'}</dd></div>
        <div className="flex items-start justify-between gap-2 px-3 py-1.5"><dt className="text-slate-500">Tệp GNT đính kèm</dt><dd className="text-right font-bold">{gntDoc?.attachmentId ? 'Đã đính kèm' : 'Chưa đính kèm'}</dd></div>
        <div className="flex items-start justify-between gap-2 px-3 py-1.5"><dt className="text-slate-500">Thuế đã nộp</dt><dd className="text-right font-bold text-slate-500">Chưa có bằng chứng</dd></div>
      </dl>
      <p className="mt-1 text-xs text-slate-500">Tạo GNT không đồng nghĩa đã nộp thuế. Số thuế/VAT do operator ghi từ chứng từ thực tế, không tự tính.</p>
    </div>

    <div data-testid="ci-partners">
      <p className="mb-1 text-xs font-extrabold tracking-wide text-slate-500">ĐỐI TÁC / TÀI CHÍNH</p>
      {groups.length > 1 ? groups.map(g => <div key={g.partnerKey || g.partnerId || g.partnerName} className="mb-2 rounded-lg border border-slate-200 p-2.5">
        <p className="font-extrabold text-sm">{g.partnerName || 'Đối tác chưa rõ'}</p>
        {Object.entries(g.totalsByCurrency).map(([ccy, t]) => <div key={ccy} className="mt-1 flex items-start justify-between gap-2 text-sm">
          <span className="text-slate-500">Phải trả ({ccy})</span>
          <span className="text-right">{money(t.payable, ccy)}{t.paid ? ` · đã trả ${fmtCcy(t.paid, ccy)}` : ''}</span>
        </div>)}
        {Object.keys(g.totalsByCurrency).length === 0 && <p className="text-sm text-slate-500">Chưa có thông tin</p>}
      </div>) : partner?.partnerName ? <div className="rounded-lg border border-slate-200 p-2.5 text-sm">
        <p className="font-extrabold">{partner.partnerName}</p>
        <div className="mt-1 flex items-start justify-between gap-2"><span className="text-slate-500">Phải trả</span><span className="text-right">{money(partner.payable, partner.currency)}</span></div>
      </div> : <p className="rounded-lg border border-slate-200 p-2.5 text-sm text-slate-500">Chưa có thông tin đối tác phải trả.</p>}
      <p className="mt-1 text-xs text-slate-500">Không cộng gộp tiền khác đơn vị khi chưa có tỷ giá.</p>
    </div>

    {module && <div className="rounded-lg border border-slate-200 bg-slate-50 p-3" data-testid="ci-module-rollup">
      <p className="text-xs font-bold text-slate-500">QUY TRÌNH PHÁT SINH</p>
      <p className="font-extrabold text-sm">{module.name}</p>
      <p className="text-xs text-slate-600">{module.summary} · {module.status === 'DONE' ? 'đã xong' : module.status === 'BLOCKING' ? 'đang chặn' : module.status === 'UNKNOWN' ? 'chưa xác định' : 'đang chờ'}</p>
      {module.gateText && <p className="mt-1 text-sm font-semibold text-red-900">{module.gateText}</p>}
      {module.nextStep && <p className="mt-1 text-xs text-slate-600">Bước tiếp theo: {module.nextStep}</p>}
    </div>}

    <button type="button" onClick={() => onOpen(selected, 'overview')} data-testid="ci-open-workspace"
      className="touch-target flex w-full items-center justify-center gap-2 rounded-xl bg-[#0f2a4a] px-3 py-3 font-bold text-white">MỞ CÔNG ĐOẠN →</button>
  </div>;
}

export default function ShipmentJourney({ shipment: s, activeStage, work, onOpen, onGlobal, runPrimary }: {
  shipment: Shipment; activeStage: string; work: string;
  onOpen: (node: JourneyNode, work: string) => void; onGlobal: () => void; runPrimary: () => void;
}) {
  const [picked, setPicked] = useState('');
  const [expandedModule, setExpandedModule] = useState('');
  const [attachOpen, setAttachOpen] = useState(false);
  const [chosen, setChosen] = useState('');
  const [attachPending, setAttachPending] = useState('');
  const [attachError, setAttachError] = useState('');
  const { dispatch } = useStore();
  const vm = useSyncExternalStore(subscribeViewModel, getViewModel, getViewModel);
  useEffect(() => { setPicked(activeStage || ''); }, [activeStage]);
  const journey = s.journey;
  const modules = useMemo(() => journey?.modules ?? [], [journey]);
  const attachOutcome = vm?.lastWrites?.find(w => w.event === 'work_module_attach' && w.requestId === attachPending);
  const attachLoading = Boolean(attachPending && !attachOutcome);
  useEffect(() => {
    if (!attachOutcome) return;
    if (attachOutcome.ok) { setAttachOpen(false); setChosen(''); setAttachPending(''); setAttachError(''); }
    else { setAttachError(String(attachOutcome.error || 'Backend từ chối gắn quy trình.')); setAttachPending(''); }
  }, [attachOutcome]);
  if (!journey?.nodes.length) return <section className="rounded-2xl border bg-white p-4"><h2 className="font-bold">Hành trình lô hàng</h2><p className="mt-1 text-sm text-slate-500">Chưa có công đoạn phù hợp. Bổ sung phạm vi dịch vụ trong thông tin vận chuyển.</p></section>;
  const nodes = journey.nodes;
  // Issue #162 — the base map stays the base map. Module steps are NOT drawn as
  // extra branches by default; they live inside the rollup card and are
  // revealed on demand (the graph is still fully present in the payload).
  const baseNodes = nodes.filter(n => !n.moduleId);
  const selected = nodes.find(n => n.id === picked) ?? nodes.find(n => n.id === activeStage) ?? baseNodes.find(n => n.current) ?? baseNodes[0];
  const stage = nodes.find(n => n.id === activeStage);
  const sea = baseNodes.some(n => n.id === 'booking');
  const pos = new Map(baseNodes.map((n, i) => [n.id, sea ? SEA_POS[n.id] ?? [i % 4, Math.floor(i / 4)] : [i % 4, Math.floor(i / 4)]]));
  const maxRow = Math.max(...[...pos.values()].map(p => p[1]));
  const primary = journey.primaryAction;
  const library = vm?.workModules;
  const choices = library?.templates ?? [];
  const canAttach = Boolean(library?.canAttach);
  const attach = () => {
    if (!chosen) { setAttachError('Chọn một quy trình đang dùng (ACTIVE).'); return; }
    const requestId = `WM-${crypto.randomUUID()}`;
    setAttachError(''); setAttachPending(requestId);
    if (!dispatch('work_module_attach', {
      shipmentId: s.id, templateId: chosen, requestId,
      expectedVersion: s.version ?? 0, provenance: 'MANUAL_ADDITION',
    })) { setAttachPending(''); setAttachError('Chưa kết nối backend.'); }
  };
  return <section className="rounded-2xl border border-slate-200 bg-white overflow-hidden" data-testid="shipment-journey">
    <div className="flex flex-wrap items-center gap-3 border-b p-4">
      <div className="min-w-0 flex-1"><h2 className="font-extrabold text-lg text-[#0f2a4a]">Hành trình lô hàng</h2>
        <p className="text-sm text-slate-500">{journey.currentStageId ? `Vị trí theo mốc thực tế: ${nodes.find(n => n.current)?.label}` : journey.positionNote}</p></div>
      {canAttach && <button type="button" onClick={() => { setAttachOpen(v => !v); setAttachError(''); }} data-testid="journey-add-module"
        className="touch-target inline-flex items-center gap-1 rounded-lg border px-3 py-2 text-sm font-bold"><Plus size={15} aria-hidden="true" />Thêm quy trình phát sinh</button>}
      <button type="button" onClick={onGlobal} className="touch-target rounded-lg border px-3 py-2 text-sm font-bold">Toàn bộ lô hàng</button>
    </div>
    {attachOpen && <div className="border-b bg-slate-50 p-4" data-testid="journey-add-module-panel">
      <h3 className="font-extrabold text-[#0f2a4a]">Thêm quy trình phát sinh</h3>
      <p className="text-sm text-slate-500">Chỉ gắn được quy trình đang dùng (ACTIVE). Bản nháp/ngừng dùng không gắn được.</p>
      {choices.length === 0
        ? <p className="mt-2 text-sm text-slate-600">Chưa có quy trình nào đang dùng trong thư viện.</p>
        : <ul className="mt-2 space-y-2">{choices.map(t => <li key={t.templateId}>
            <label className={cx('flex cursor-pointer flex-col rounded-xl border-2 bg-white p-3', chosen === t.templateId ? 'border-[#0f2a4a]' : 'border-slate-200')}>
              <span className="flex items-center gap-2">
                <input type="radio" name="wm-choice" value={t.templateId} checked={chosen === t.templateId}
                  onChange={() => setChosen(t.templateId)} aria-label={`Chọn ${t.name}`} />
                <span className="font-bold">{t.name}</span>
                <span className="text-xs text-slate-500">V{t.version} · {t.stepCount} bước</span>
              </span>
              <span className="mt-1 text-sm text-slate-600">{t.description || 'Chưa có mô tả.'}</span>
            </label>
          </li>)}</ul>}
      <div className="mt-3 flex flex-wrap items-center gap-2">
        <button type="button" disabled={!canAttach || attachLoading || !chosen} onClick={attach} data-testid="journey-add-module-confirm"
          className="touch-target rounded-lg bg-[#0f2a4a] px-4 py-2 font-bold text-white disabled:opacity-50">{attachLoading ? 'Đang chờ đọc lại…' : 'Gắn vào lô này'}</button>
        <button type="button" onClick={() => { setAttachOpen(false); setAttachError(''); }} className="touch-target rounded-lg border px-3 py-2 text-sm font-bold">Đóng</button>
        {attachLoading && <span className="text-sm text-slate-500">Đang ghi qua backend và chờ đọc lại.</span>}
      </div>
      {(attachError || (attachOutcome && !attachOutcome.ok)) && <p role="alert" className="mt-2 text-sm text-red-700">{attachError || attachOutcome?.error}</p>}
    </div>}
    {modules.length > 0 && <div className="border-b bg-slate-50/60 p-3" data-testid="journey-modules">
      <p className="mb-2 inline-flex items-center gap-1 text-xs font-bold tracking-wide text-slate-500"><Layers size={13} aria-hidden="true" />QUY TRÌNH ĐANG GẮN ({modules.length})</p>
      <div className="grid grid-cols-1 gap-2 xl:grid-cols-2">{modules.map(m => <ModuleCard key={m.instanceId} module={m} nodes={nodes}
        expanded={expandedModule === m.instanceId} onToggle={() => setExpandedModule(cur => cur === m.instanceId ? '' : m.instanceId)}
        selectedId={selected.id} onPick={setPicked} />)}</div>
    </div>}
    <div className="grid grid-cols-1 xl:grid-cols-[minmax(0,1fr)_300px]">
      <div className="min-w-0 p-3">
        <div className="overflow-x-auto rounded-xl bg-slate-50 p-2" aria-label="Bản đồ công đoạn, có thể cuộn ngang">
          <div className="relative min-w-[740px]" style={{ height: (maxRow + 1) * 145 }}>
            <svg className="absolute inset-0 h-full w-full pointer-events-none" viewBox={`0 0 740 ${(maxRow + 1) * 145}`} preserveAspectRatio="none" aria-hidden="true">
              <defs><marker id="journey-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5" markerHeight="5" orient="auto"><path d="M 0 0 L 10 5 L 0 10 z" fill="#94a3b8" /></marker></defs>
              {journey.edges.map(e => { const a = pos.get(e.from), b = pos.get(e.to); if (!a || !b) return null;
                const ax = a[0] * 185 + 84, ay = a[1] * 145 + 58, bx = b[0] * 185 + 84, by = b[1] * 145 + 58;
                const horizontal = a[1] === b[1]; const startX = horizontal ? ax + (bx > ax ? 82 : -82) : ax;
                const endX = horizontal ? bx + (bx > ax ? -82 : 82) : bx;
                const startY = horizontal ? ay : ay + 57, endY = horizontal ? by : by - 57;
                return <path key={`${e.from}-${e.to}`} d={`M ${startX} ${startY} L ${endX} ${endY}`} fill="none" stroke="#94a3b8" strokeWidth="2" markerEnd="url(#journey-arrow)" />; })}
            </svg>
            {baseNodes.map(n => { const [x, y] = pos.get(n.id)!;
              return <button key={n.id} type="button" data-testid={`journey-node-${n.id}`} data-state={n.state}
                aria-pressed={selected.id === n.id} onClick={() => setPicked(n.id)}
                className={cx('absolute flex flex-col text-left rounded-xl border-2 p-2.5 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-700', META[n.state].cls, selected.id === n.id && 'ring-2 ring-[#0f2a4a] ring-offset-2')}
                style={{ left: `${x * 25}%`, top: y * 145, width: '22.5%', height: 116 }}>
                <Status node={n} /><span className="mt-1 font-extrabold text-sm">{n.label}</span>
                <span className="text-xs line-clamp-2 mt-1">{n.evidence || 'Chưa có bằng chứng thực tế'}</span>
                <span className="mt-auto text-[11px] font-medium">{n.current ? '● Vị trí hiện tại · ' : ''}{n.documentIds.length} tệp · {n.owned ? 'TT phụ trách' : 'Tham chiếu phạm vi'}</span>
              </button>; })}
          </div>
        </div>
        {sea && baseNodes.some(n => n.id === 'si-vgm') && baseNodes.some(n => n.id === 'gate-in') && <p className="mt-2 text-xs text-slate-500">SI/VGM và Gate-in là hai nhánh song song. Lịch ETD không xác nhận hai nhánh đã hoàn tất; ATD ghi nhận được vẫn hiển thị độc lập.</p>}
      </div>
      <aside className="border-t xl:border-t-0 xl:border-l p-4 space-y-3" data-testid="journey-quick-panel">
        {selected.id === 'customs-import'
          ? <CustomsImportQuickPanel s={s} selected={selected} onOpen={onOpen} runPrimary={runPrimary} />
          : <>
        <div><span className="text-xs font-bold text-slate-500">XEM NHANH</span><h3 className="text-xl font-extrabold text-[#0f2a4a]">{selected.label}</h3><Status node={selected} /></div>
        {selected.moduleId && <div className="rounded-lg border border-slate-200 bg-slate-50 p-3" data-testid="journey-module-context">
          <p className="text-xs font-bold text-slate-500">QUY TRÌNH · V{selected.moduleTemplateVersion}</p>
          <p className="font-bold text-sm">{selected.moduleName}</p>
          <p className="text-xs text-slate-600">Nguồn: {PROVENANCE_LABEL[selected.moduleProvenance ?? ''] ?? selected.moduleProvenance} · {selected.moduleStatus === 'DONE' ? 'đã xong' : selected.moduleStatus === 'BLOCKING' ? 'đang chặn' : selected.moduleStatus === 'UNKNOWN' ? 'chưa xác định' : 'đang chờ'}</p>
          {selected.moduleGateText && <p className="mt-1 text-sm font-semibold text-red-900">{selected.moduleGateText}</p>}
          {selected.moduleSteps && <ol className="mt-2 space-y-0.5 text-sm">{selected.moduleSteps.map(step => <li key={step.id} className="flex items-center gap-1">
            {step.completed ? <CheckCircle2 size={13} className="text-emerald-700" aria-hidden="true" /> : <Circle size={13} className="text-slate-400" aria-hidden="true" />}
            <span className={step.completed ? 'text-slate-600 line-through' : 'font-semibold'}>{step.label}</span></li>)}</ol>}
        </div>}
        <div className="rounded-lg bg-slate-50 border p-3"><p className="text-xs font-bold text-slate-500">Support Sale cần làm gì</p>
          <p className="font-semibold mt-1 text-sm">{selected.blockers.join(' · ') || (selected.owned ? 'Kiểm tra bằng chứng và cập nhật tại bàn làm việc công đoạn.' : 'Theo dõi thông tin tham chiếu; chưa xác nhận Trường Thành phụ trách.')} </p></div>
        {selected.guidance && <div className="rounded-lg border border-slate-200 p-3" data-testid="journey-module-guidance">
          <p className="inline-flex items-center gap-1 text-xs font-bold text-slate-500"><Info size={13} aria-hidden="true" />HƯỚNG DẪN BƯỚC</p>
          <dl className="mt-1 space-y-1 text-sm">{GUIDANCE_ROWS.filter(row => selected.guidance?.[row.key]).map(row =>
            <div key={row.key}><dt className="text-xs text-slate-500">{row.label}</dt><dd className="font-medium">{selected.guidance?.[row.key]}</dd></div>)}</dl>
        </div>}
        <dl className="grid grid-cols-2 gap-3 text-sm"><div><dt className="text-xs text-slate-500">Owner lô hàng</dt><dd className="font-semibold">{journey.owner || 'Chưa phân công'}</dd></div><div><dt className="text-xs text-slate-500">Mốc dự kiến / cutoff</dt><dd className="font-semibold">{selected.deadline || 'Chưa ghi nhận'}</dd></div></dl>
        <div className="text-sm"><p className="text-xs font-bold text-slate-500">Phụ thuộc</p><p>{selected.dependencies.map(id => nodes.find(n => n.id === id)?.label).join(' + ') || 'Không có công đoạn trước trong phạm vi này'}</p></div>
        <div className="text-sm"><p className="text-xs font-bold text-slate-500">Next Action — toàn lô</p><p className="font-semibold">{primary.text}</p><button type="button" onClick={runPrimary} className="touch-target mt-1 text-blue-800 font-bold underline">{s.nextLabel || 'Xử lý ngay'}</button></div>
        <div className="text-sm"><p className="text-xs font-bold text-slate-500">Chứng từ / ảnh hưởng</p><p>{selected.documentIds.length} tệp liên quan. {selected.blockers.length ? selected.blockers.join(' · ') : 'Chưa có blocker được ghi nhận cho công đoạn này.'}</p></div>
        <div className="text-sm"><p className="text-xs font-bold text-slate-500">Thông tin có thể báo khách</p><p>{selected.evidence ? `${selected.label}: ${selected.evidence}.` : 'Chưa có bằng chứng để xác nhận tiến độ với khách.'}{selected.deadline ? ` Mốc dự kiến: ${selected.deadline}.` : ''}</p></div>
        <button type="button" onClick={() => onOpen(selected, 'overview')} data-testid="journey-open-workspace" className="touch-target w-full inline-flex items-center justify-center gap-2 rounded-xl bg-[#0f2a4a] text-white font-bold px-3 py-3">Mở bàn làm việc <ArrowRight size={16} /></button>
          </>}
      </aside>
    </div>
    {stage && <div className="border-t p-4" data-testid="journey-stage-workspace"><div className="flex flex-wrap gap-2 items-center"><h3 className="font-extrabold text-lg">{stage.label} · bàn làm việc</h3><span className="text-sm text-slate-500">{s.id}</span></div>
      <div className="flex gap-2 mt-3 overflow-x-auto" aria-label="Nội dung công đoạn">{JOURNEY_WORK.map(w => <button type="button" key={w.id} aria-pressed={work === w.id} onClick={() => onOpen(stage, w.id)} className={cx('touch-target whitespace-nowrap rounded-lg border px-3 py-2 text-sm font-bold', work === w.id && 'bg-[#0f2a4a] text-white')}>{w.label}</button>)}</div>
      {work === 'overview' && <div className="mt-4 text-sm space-y-2"><p>{stage.evidence || 'Chưa có bằng chứng hoàn thành. UNKNOWN được giữ nguyên.'}</p><p>{stage.blockers.join(' · ') || 'Không có blocker riêng được ghi nhận.'}</p><p>{stage.owned ? 'Công đoạn thuộc phạm vi đã xác nhận của Trường Thành.' : 'Thông tin tham chiếu, chưa phải công việc đã giao cho Trường Thành.'}</p></div>}
    </div>}
  </section>;
}

/**
 * Issue #162 — Stage Workspace panel for ONE module step.
 *
 * Factual completion is a PERSISTED BUSINESS FACT: this button writes through
 * the ONE dispatcher (shipment_edit RBAC → version-guarded atomic shipment save
 * → audit), then waits for the authoritative outcome matched by requestId in
 * the next fresh view-model. It never marks the step complete locally, and an
 * uploaded document does NOT complete a step by itself.
 */
export function WorkModuleStepPanel({ shipment: s, node }: { shipment: Shipment; node: JourneyNode }) {
  const { dispatch } = useStore();
  const vm = useSyncExternalStore(subscribeViewModel, getViewModel, getViewModel);
  const [pending, setPending] = useState('');
  const [error, setError] = useState('');
  const access = vm?.userAccess?.currentUser;
  const canEdit = Boolean(access?.wildcard || access?.permissions.includes('shipment_edit'));
  const outcome = vm?.lastWrites?.find(w => w.event === 'work_module_step_complete' && w.requestId === pending);
  const loading = Boolean(pending && !outcome);
  useEffect(() => {
    if (!outcome) return;
    if (outcome.ok) { setPending(''); setError(''); }
    else { setError(String(outcome.error || 'Backend từ chối ghi nhận.')); setPending(''); }
  }, [outcome]);
  const step = vm?.shipments.find(row => row.id === s.id)?.journey?.modules
    ?.find(m => m.instanceId === node.moduleId)?.steps.find(x => x.id === node.moduleNodeId);
  const done = Boolean(step?.completed) || node.completed;
  const blocked = (step?.blockedBy ?? []).length > 0;
  const complete = () => {
    const requestId = `WMS-${crypto.randomUUID()}`;
    setError(''); setPending(requestId);
    if (!dispatch('work_module_step_complete', {
      shipmentId: s.id, instanceId: node.moduleId, nodeId: node.moduleNodeId, requestId,
      expectedVersion: s.version ?? 0,
    })) { setPending(''); setError('Chưa kết nối backend.'); }
  };
  return <section className="rounded-2xl border bg-white p-4 space-y-3" data-testid="work-module-step-panel">
    <div>
      <p className="text-xs font-bold text-slate-500">QUY TRÌNH · V{node.moduleTemplateVersion} · {node.moduleName}</p>
      <h3 className="font-extrabold text-[#0f2a4a]">{node.label}</h3>
      {node.moduleGateText && <p className="text-sm font-semibold text-red-900">{node.moduleGateText}</p>}
    </div>
    {step && <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
      <ol className="space-y-1 text-sm">{step.guidance && GUIDANCE_ROWS.filter(row => step.guidance[row.key]).map(row =>
        <li key={row.key}><span className="text-xs font-bold text-slate-500">{row.label}</span><p className="font-medium">{step.guidance[row.key]}</p></li>)}</ol>
      {!step.guidance || GUIDANCE_ROWS.every(row => !step.guidance?.[row.key]) ? <p className="text-sm text-slate-500">Bước này chưa có hướng dẫn chi tiết.</p> : null}
    </div>}
    <div className="text-sm">
      <p className="font-semibold">{done
        ? `Đã ghi nhận hoàn thành${step?.completedBy ? ` bởi ${step.completedBy}` : ''}${step?.completedAt ? ` lúc ${step.completedAt}` : ''}.`
        : blocked
          ? 'Chưa thể hoàn thành: bước trước đó chưa có bằng chứng hoàn thành.'
          : 'Chưa ghi nhận hoàn thành. Tệp đã tải lên không tự xác nhận bước này.'}</p>
      {!done && <p className="mt-1 text-xs text-slate-500">Ghi nhận này là dữ liệu nghiệp vụ đã lưu (ai · khi nào), không phải thao tác hiển thị.</p>}
    </div>
    <button type="button" disabled={!canEdit || loading || done || blocked} onClick={complete} data-testid="work-module-step-complete"
      className="touch-target rounded-lg bg-[#0f2a4a] px-4 py-2 font-bold text-white disabled:opacity-50">{loading ? 'Đang chờ đọc lại…' : done ? 'Đã xác nhận từ backend' : 'Ghi nhận hoàn thành bước'}</button>
    {!canEdit && <p className="text-sm text-slate-500">Tài khoản hiện tại chỉ đọc thông tin này.</p>}
    {(error || (outcome && !outcome.ok)) && <p role="alert" className="text-sm text-red-700">{error || outcome?.error}</p>}
  </section>;
}

export function SeaExportFacts({ shipment: s, stageId }: { shipment: Shipment; stageId: string }) {
  const { dispatch } = useStore();
  const vm = useSyncExternalStore(subscribeViewModel, getViewModel, getViewModel);
  const [draft, setDraft] = useState<Record<string, string>>({});
  const [pending, setPending] = useState(''); const [error, setError] = useState('');
  const [expectedVersion] = useState(s.version ?? 0);
  const access = vm?.userAccess?.currentUser;
  const canEdit = Boolean(access?.wildcard || access?.permissions.includes('shipment_edit'));
  const node = s.journey?.nodes.find(n => n.id === stageId);
  const outcome = vm?.lastWrites?.find(w => w.event === 'shipment_sea_facts_save' && w.requestId === pending);
  const loading = Boolean(pending && !outcome);
  const saved = Boolean(outcome?.ok);
  const fields = stageId === 'customs-export' ? [{ key: 'export_declaration_no', label: 'Số tờ khai xuất (đã đăng ký)' }] : stageId === 'gate-in' ? [{ key: 'gate_in_at', label: 'Gate-in thực tế' }] : [
    { key: 'si_status', label: 'Trạng thái SI' }, { key: 'vgm_status', label: 'Trạng thái VGM' },
    { key: 'si_cutoff', label: 'SI cutoff' }, { key: 'vgm_cutoff', label: 'VGM cutoff' },
  ];
  const save = () => {
    if (!Object.keys(draft).length) { setError('Chưa thay đổi trường nào.'); return; }
    const requestId = `SEA-${crypto.randomUUID()}`;
    setError(''); setPending(requestId);
    if (!dispatch('shipment_sea_facts_save', { shipmentId: s.id, fields: draft, requestId, expectedVersion })) {
      setPending(''); setError('Chưa kết nối backend.');
    }
  };
  return <section className="rounded-2xl border bg-white p-4 space-y-3" data-testid="sea-export-facts">
    <h3 className="font-extrabold text-[#0f2a4a]">{stageId === 'customs-export' ? 'Tờ khai xuất — dữ liệu hiện có' : stageId === 'gate-in' ? 'Mốc vào bãi container' : 'SI / VGM — ghi nhận bằng chứng'}</h3>
    <p className="text-sm text-slate-500">Tệp đã tải lên không tự xác nhận hãng tàu đã nhận hoặc chấp nhận. Chỉ ghi trạng thái có bằng chứng.</p>
    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">{fields.map(f => <Field key={f.key} label={f.label}>
      {f.key.endsWith('_status') ? <select aria-label={f.label} disabled={!canEdit || loading || !node?.owned} className={inputCls()} value={draft[f.key] ?? s.journey?.seaFacts[f.key] ?? 'UNKNOWN'} onChange={e => setDraft(d => ({ ...d, [f.key]: e.target.value }))}>
        {['UNKNOWN', 'RECEIVED', 'SUBMITTED', 'ACCEPTED'].map((k, i) => <option key={k} value={k}>{['Chưa biết', 'Đã nhận hồ sơ', 'Đã gửi hãng tàu', 'Hãng tàu đã chấp nhận'][i]}</option>)}</select> :
        <input aria-label={f.label} type="text" placeholder={f.key === 'export_declaration_no' ? 'Số tờ khai' : 'YYYY-MM-DD hoặc YYYY-MM-DDTHH:mm'} disabled={!canEdit || loading || !node?.owned} className={inputCls()} value={draft[f.key] ?? s.journey?.seaFacts[f.key] ?? ''} onChange={e => setDraft(d => ({ ...d, [f.key]: e.target.value }))} />}
    </Field>)}</div>
    <button type="button" disabled={!canEdit || loading || !node?.owned || saved} onClick={save} className="touch-target rounded-lg bg-[#0f2a4a] px-4 py-2 font-bold text-white disabled:opacity-50">{loading ? 'Đang chờ đọc lại…' : saved ? 'Đã xác nhận từ backend' : 'Lưu mốc có bằng chứng'}</button>
    {!canEdit && <p className="text-sm text-slate-500">Tài khoản hiện tại chỉ đọc thông tin này.</p>}
    {(error || outcome?.error) && <p role="alert" className="text-sm text-red-700">{error || outcome?.error}</p>}
  </section>;
}
