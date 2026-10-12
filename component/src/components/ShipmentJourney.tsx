import { useEffect, useMemo, useRef, useState, useSyncExternalStore, type ReactNode } from 'react';
import { ArrowRight, CheckCircle2, Circle, Clock, CircleAlert, ChevronDown, ChevronRight, Info, Layers, MapPin, Plus } from 'lucide-react';
import type { JourneyNode, Shipment, WorkModuleGuidance, WorkModuleRollup } from '../lib/viewmodel';
import { getViewModel, subscribeViewModel } from '../lib/viewmodel';
import { useStore } from '../lib/store';
import { cx, fmtCcy } from '../lib/format';
import { Field, inputCls } from './ui';
import JourneyMap, { JOURNEY_META as META, JourneyStatus } from './JourneyMap';
import JourneyQuickPanel, { stageAction } from './JourneyQuickPanel';

export const JOURNEY_REGION_NODE_IDS = {
  origin: ['booking', 'pickup', 'customs-export', 'si-vgm', 'gate-in'],
  main: ['etd', 'on-board', 'transit', 'arrival'],
  import: ['customs-import'],
  delivery: ['delivery'],
} as const;

export const JOURNEY_REGION_LABELS = {
  origin: 'Đầu đi',
  main: 'Chặng chính',
  import: 'Nhập khẩu',
  delivery: 'Giao hàng',
} as const;

export const JOURNEY_WORK = [
  { id: 'info', label: 'Công việc' },
  { id: 'docs', label: 'Chứng từ' },
];
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
function CustomsImportQuickPanel({ s, selected, onOpen, runPrimary, onClose }: {
  s: Shipment; selected: JourneyNode;
  onOpen: (node: JourneyNode, work: string) => void; runPrimary: () => void;
  onClose: () => void;
}) {
  const info = s.importInfo;
  const flow = s.commercialFlow;
  const partner = s.finance?.partner;
  const groups = partner?.partners ?? [];
  const gnt = info.gnt;
  const modules = s.journey?.modules ?? [];
  // B4 (Issue #184 repair): no broad fallback. A Work Module is shown only
  // when it is anchored/gated to the selected Customs Import context —
  // never an unrelated shipment module via `modules[0]`.
  const module = modules.find(m => m.anchorLabel === selected.label)
    ?? modules.find(m => m.gate?.stage === selected.id);
  const primary = s.journey?.primaryAction;
  const workflowSteps = s.documentWorkflow?.steps ?? [];
  // Import-relevant workflow steps, most urgent first. BLOCKED beats
  // MISSING_INFO beats CONDITIONAL; the panel never invents urgency.
  const stepRank = (state: string) =>
    ({ BLOCKED: 0, MISSING_INFO: 1, CONDITIONAL: 2 } as Record<string, number>)[state] ?? 3;
  const urgentStep = [...workflowSteps]
    .filter(st => st.targetTab === 'nhap' || st.id === 'tax_payment')
    .sort((a, b) => stepRank(a.state) - stepRank(b.state))[0];
  // B3 (Issue #184 repair): ONE canonical primary action. The dominant CTA
  // block always renders journey.primaryAction (text + detail) and executes
  // runPrimary. The urgent workflow step is contextual missing/blocking
  // evidence only — it never substitutes the CTA text, detail, or handler,
  // and no second priority engine is created.
  const urgentBlocked = (urgentStep?.state === 'BLOCKED' || urgentStep?.state === 'MISSING_INFO')
    ? urgentStep : undefined;
  const cleared = Boolean(info.customsStatus);
  const gntDoc = gnt?.document;
  const money = (n: number | null | undefined, ccy?: string | null) =>
    <span className="font-bold">{fmtCcy(n ?? null, ccy ?? 'VND')}</span>;
  return <div className="flex h-full min-h-0 flex-col bg-white" data-testid="customs-import-quick-panel">
    {/* Issue #190 repair — match the proven JourneyQuickPanel shell: fixed
        header, one bounded scrolling content region, then a fixed workspace
        footer. The declaration lead stays with the stage identity. */}
    <div className="shrink-0 border-b border-slate-300 px-4 pb-3 pt-3">
      <div className="flex items-center gap-2">
        <span className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-[#0f2a4a] text-white" aria-hidden="true"><Info size={16} /></span>
        <h3 className="text-xl font-extrabold tracking-tight text-[#0f2a4a]">NHẬP KHẨU</h3>
        {(selected.state === 'PROBLEM' || selected.blockers.length > 0) && (
          <span className="inline-flex items-center gap-1 rounded-md border border-red-200 bg-red-50 px-1.5 py-0.5 text-[11px] font-extrabold text-red-700">
            <CircleAlert size={12} aria-hidden="true" /> Cần xử lý
          </span>
        )}
        <button type="button" onClick={onClose} aria-label="Đóng Quick Panel" className="touch-target ml-auto grid h-9 w-9 place-items-center rounded-lg text-lg text-slate-400 hover:bg-slate-100">✕</button>
      </div>
      <p className="mt-1 text-[13.5px] leading-snug text-slate-700">
        {info.declarationNo
          ? <>Tờ khai NK <b>{info.declarationNo}</b> đã đăng ký · {cleared ? 'đã xác nhận thông quan' : 'chưa xác nhận thông quan'}.</>
          : <>Chưa có số tờ khai nhập khẩu · {cleared ? 'đã xác nhận thông quan' : 'chưa xác nhận thông quan'}.</>}
      </p>
    </div>

    <div className="min-h-0 flex-1 space-y-3 overflow-auto px-4 py-3" data-testid="ci-scroll-region">
    {primary?.text ? <div className="rounded-lg border-2 border-red-600 bg-red-50 p-3" data-testid="ci-next-action">
      <p className="text-xs font-extrabold tracking-wide text-red-700">CẦN LÀM NGAY</p>
      <p className="mt-0.5 font-extrabold text-red-900">{primary.text}</p>
      {primary.detail && <p className="mt-0.5 text-sm text-red-800">{primary.detail}</p>}
      <button type="button" onClick={runPrimary} data-testid="ci-primary-cta"
        className="touch-target mt-2 w-full rounded-lg bg-[#0f2a4a] px-4 py-2.5 font-extrabold text-white">{s.nextLabel || 'Xử lý ngay'}</button>
      {urgentBlocked && <p className="mt-2 text-xs text-slate-600">Thiếu/chặn liên quan: {urgentBlocked.label} — {urgentBlocked.reason}</p>}
    </div> : urgentBlocked ? <div className="rounded-lg border border-amber-300 bg-amber-50 p-3" data-testid="ci-blocked-evidence">
      <p className="text-xs font-extrabold tracking-wide text-amber-800">THIẾU / ĐANG CHẶN</p>
      <p className="mt-0.5 text-sm font-bold text-amber-900">{urgentBlocked.label}</p>
      <p className="mt-0.5 text-xs text-amber-800">{urgentBlocked.reason}</p>
    </div> : null}

    <div>
      <p className="mb-1 text-xs font-extrabold tracking-wide text-slate-500">THÔNG TIN CHÍNH</p>
      {/* Registration is a fact, not a competing action. Keep declaration
          registration and customs clearance visibly separate and below the
          ONE canonical next action. */}
      <div className="mb-2 rounded-lg border border-slate-200 p-3 text-sm" data-testid="ci-registration-clearance">
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
      </div>) : partner?.partnerName ? (
        // B6 (Issue #184 repair): a catalog suggestion must not look like an
        // established payable party. When suggested === true there are no
        // ledger rows behind this partner: qualify visibly and keep money
        // truthful (no payable is inferred from the catalog).
        partner.suggested ? <div className="rounded-lg border border-amber-300 bg-amber-50 p-2.5 text-sm" data-testid="ci-partner-suggested">
          <p className="font-extrabold">{partner.partnerName}</p>
          <p className="mt-0.5 text-xs font-bold text-amber-800">Đề xuất từ danh mục · chưa xác nhận đối tác phải trả</p>
          <p className="mt-1 text-xs text-slate-600">Chưa có thông tin phải trả.</p>
        </div> : <div className="rounded-lg border border-slate-200 p-2.5 text-sm">
          <p className="font-extrabold">{partner.partnerName}</p>
          <div className="mt-1 flex items-start justify-between gap-2"><span className="text-slate-500">Phải trả</span><span className="text-right">{money(partner.payable, partner.currency)}</span></div>
        </div>
      ) : <p className="rounded-lg border border-slate-200 p-2.5 text-sm text-slate-500">Chưa có thông tin đối tác phải trả.</p>}
      <p className="mt-1 text-xs text-slate-500">Không cộng gộp tiền khác đơn vị khi chưa có tỷ giá.</p>
    </div>

    {module && <div className="rounded-lg border border-slate-200 bg-slate-50 p-3" data-testid="ci-module-rollup">
      <p className="text-xs font-bold text-slate-500">QUY TRÌNH PHÁT SINH</p>
      <p className="font-extrabold text-sm">{module.name}</p>
      <p className="text-xs text-slate-600">{module.summary} · {module.status === 'DONE' ? 'đã xong' : module.status === 'BLOCKING' ? 'đang chặn' : module.status === 'UNKNOWN' ? 'chưa xác định' : 'đang chờ'}</p>
      {module.gateText && <p className="mt-1 text-sm font-semibold text-red-900">{module.gateText}</p>}
      {module.nextStep && <p className="mt-1 text-xs text-slate-600">Bước tiếp theo: {module.nextStep}</p>}
    </div>}
    </div>

    <div className="shrink-0 border-t border-slate-300 bg-white p-3" data-testid="ci-footer">
      <button type="button" onClick={() => onOpen(selected, 'overview')} data-testid="ci-open-workspace"
        className="touch-target flex w-full items-center justify-center gap-2 rounded-xl bg-slate-900 px-3 py-3 font-bold text-white">MỞ CÔNG ĐOẠN →</button>
    </div>
  </div>;
}

const EMPTY_PHASES = [
  { id: 'profile', label: 'HỒ SƠ', hint: 'Bổ sung hồ sơ & phạm vi', tab: 'van-tai' },
  { id: 'origin', label: 'ĐẦU ĐI', hint: 'Chưa xác định', tab: 'lay-hang' },
  { id: 'main', label: 'CHẶNG CHÍNH', hint: 'Chưa xác định', tab: 'van-tai' },
  { id: 'import', label: 'NHẬP KHẨU', hint: 'Chưa xác định', tab: 'nhap' },
  { id: 'delivery', label: 'GIAO HÀNG', hint: 'Chưa xác định', tab: 'nhap' },
  { id: 'finish', label: 'HOÀN TẤT', hint: 'Rà chứng từ / tài chính', tab: 'chung-tu' },
] as const;

/**
 * Issue #188 — a fresh shipment may truthfully have ZERO detailed Journey
 * nodes until mode/scope/profile facts are confirmed. Zero nodes must change
 * cockpit CONTENT, never make the approved cockpit shell disappear.
 *
 * This surface renders only the universal six-phase mental model plus the
 * existing Execution Profile projection. It deliberately does NOT fabricate
 * SEA/ROAD/AIR detailed stages merely to make the map look populated.
 */
function FreshShipmentCockpit({ shipment: s, onGlobal, runPrimary, children, globalActive = false, globalTab = 'van-tai' }: {
  shipment: Shipment;
  onGlobal: (tab?: string) => boolean;
  runPrimary: () => void;
  children?: ReactNode;
  globalActive?: boolean;
  globalTab?: string;
}) {
  const profile = s.executionProfile;
  const issues = profile?.issues ?? [];
  const next = profile?.nextAction;
  const tabs = [
    { id: 'van-tai', label: 'Thông tin' },
    { id: 'lay-hang', label: 'Xuất khẩu' },
    { id: 'nhap', label: 'Nhập & Giao' },
    { id: 'chung-tu', label: 'Chứng từ' },
    { id: 'tai-chinh', label: 'Tài chính' },
    { id: 'lich-su', label: 'Lịch sử' },
  ];
  return <section className="journey-demo rounded-xl border border-slate-300 bg-white overflow-hidden" data-testid="shipment-journey" data-empty-journey="true">
    <div className="flex flex-wrap items-center gap-3 border-b p-4">
      <div className="min-w-0 flex-1">
        <h2 className="font-extrabold text-lg text-[#0f2a4a]">Hành trình lô hàng</h2>
        <p className="text-sm text-slate-500">Chưa đủ hồ sơ để xác định công đoạn chi tiết. Khung Journey vẫn giữ nguyên; UNKNOWN không được biến thành công đoạn giả.</p>
      </div>
      <button type="button" onClick={() => onGlobal()} className="touch-target rounded-lg border px-3 py-2 text-sm font-bold">Toàn bộ lô hàng</button>
    </div>

    <nav className="border-b border-slate-300 bg-slate-50 p-2" aria-label="6 giai đoạn hành trình" data-testid="journey-phase-strip">
      <div className="grid grid-cols-2 gap-1 sm:grid-cols-3 xl:grid-cols-6">
        {EMPTY_PHASES.map((phase, index) => {
          const actionable = phase.id === 'profile';
          const Icon = actionable ? CircleAlert : Circle;
          return <button key={phase.id} type="button" data-testid={`journey-phase-${phase.id}`}
            data-state={actionable ? 'ACTION' : 'UNKNOWN'}
            onClick={actionable ? runPrimary : undefined}
            disabled={!actionable}
            aria-disabled={!actionable}
            className={cx('touch-target min-w-0 rounded-lg border-2 px-2 py-2 text-left',
              actionable ? 'border-amber-500 bg-amber-50 text-amber-950' : 'border-dashed border-slate-300 bg-slate-50 text-slate-500')}>
            <span className="flex items-center gap-1 text-[10px] font-extrabold tracking-wide"><Icon size={12} aria-hidden="true" />{index + 1}/6</span>
            <span className="mt-0.5 block truncate text-xs font-black">{phase.label}</span>
            <span className="mt-0.5 block text-[10px] font-medium opacity-80">{phase.hint}</span>
          </button>;
        })}
      </div>
    </nav>

    <div className="flex flex-wrap items-center gap-2 border-b border-slate-300 bg-white px-3 py-2" data-testid="journey-map-toolbar">
      <span className="rounded-md bg-amber-50 px-2 py-1 text-xs font-semibold text-amber-800">📍 Đang ở: HỒ SƠ · cần bổ sung phạm vi</span>
      <span className="text-xs text-slate-500">Công đoạn chi tiết sẽ xuất hiện khi có đủ authority để xác định phạm vi.</span>
    </div>

    <div className={cx('journey-split journey-split-fresh', globalActive && 'journey-split-wide')}>
      <div className="journey-canvas relative flex min-w-0 flex-1 items-center justify-center overflow-hidden p-6" data-testid="journey-empty-canvas">
        <div className="flex w-full max-w-[760px] flex-col items-center">
          <div className="rounded-full border-2 border-slate-400 bg-white px-8 py-2 text-xs font-extrabold tracking-widest text-slate-600">START</div>
          <div className="h-10 w-0.5 bg-slate-300" aria-hidden="true" />
          <div className="w-full max-w-[420px] rounded-2xl border-[3px] border-amber-500 bg-white p-5 shadow-lg">
            <div className="flex items-start gap-3">
              <CircleAlert className="mt-0.5 shrink-0 text-amber-600" size={28} aria-hidden="true" />
              <div className="min-w-0">
                <p className="text-xs font-extrabold tracking-wide text-amber-700">1/6 · HỒ SƠ</p>
                <h3 className="mt-1 text-xl font-black text-slate-900">{profile?.stateLabel || 'Hồ sơ lô còn thiếu'}</h3>
                <p className="mt-1 text-sm text-slate-600">{next?.detail || 'Bổ sung phương thức, Incoterm, loại hàng và phạm vi Trường Thành để dựng Journey đúng cho lô này.'}</p>
              </div>
            </div>
            {issues.length > 0 && <ul className="mt-3 space-y-1 border-t pt-3 text-sm text-slate-700" data-testid="journey-empty-profile-issues">
              {issues.slice(0, 4).map(issue => <li key={issue.code}>• {issue.message}</li>)}
            </ul>}
          </div>
          <div className="mt-5 grid w-full grid-cols-2 gap-2 sm:grid-cols-5" aria-label="Các giai đoạn chưa xác định">
            {EMPTY_PHASES.slice(1).map(phase => <div key={phase.id} className="rounded-lg border-2 border-dashed border-slate-300 bg-white/80 px-2 py-3 text-center text-xs font-bold text-slate-500">{phase.label}<span className="mt-1 block text-[10px] font-medium">Chưa xác định</span></div>)}
          </div>
        </div>
      </div>

      <aside className="journey-side" data-testid="journey-side-panel">
        {globalActive ? <div className="flex h-full min-h-0 flex-col" data-testid="journey-global-workspace">
          <div className="border-b bg-slate-100 px-4 py-3">
            <h3 className="text-xl font-black">Toàn bộ lô hàng · {s.id}</h3>
            <p className="text-xs text-slate-500">Dữ liệu hiện có vẫn dùng writer/authority cũ; Journey không tự sinh fact.</p>
          </div>
          <div className="flex shrink-0 overflow-x-auto border-b px-2">
            {tabs.map(t => <button type="button" key={t.id} onClick={() => onGlobal(t.id)} aria-pressed={globalTab === t.id}
              className={cx('touch-target shrink-0 border-b-[3px] px-3 py-2 text-xs font-extrabold', globalTab === t.id ? 'border-slate-900' : 'border-transparent text-slate-500')}>{t.label}</button>)}
          </div>
          <div className="min-h-0 flex-1 space-y-4 overflow-auto p-4">{children}</div>
        </div> : <div className="flex h-full flex-col bg-slate-50" data-testid="journey-overview-panel">
          <div className="border-b bg-white px-4 py-3">
            <p className="text-[10.5px] font-bold uppercase tracking-widest text-slate-500">Fresh shipment · onboarding</p>
            <h3 className="text-lg font-extrabold text-slate-900">HỒ SƠ & PHẠM VI</h3>
            <p className="text-xs text-slate-500">Làm rõ phạm vi trước; sau đó hệ thống mới hiện công đoạn thật.</p>
          </div>
          <div className="flex-1 space-y-3 overflow-auto p-4" data-testid="journey-quick-panel">
            <div className="rounded-lg border-2 border-amber-500 bg-amber-50 p-3">
              <p className="text-xs font-extrabold tracking-wide text-amber-800">CẦN LÀM NGAY</p>
              <p className="mt-1 text-lg font-extrabold text-amber-950">{next?.label || 'Bổ sung hồ sơ thực hiện lô'}</p>
              <p className="mt-1 text-sm text-amber-900">{next?.detail || 'Xác nhận dữ liệu hồ sơ và phạm vi dịch vụ của Trường Thành.'}</p>
              <button type="button" onClick={runPrimary} data-testid="journey-empty-primary-cta"
                className="touch-target mt-3 w-full rounded-lg bg-[#0f2a4a] px-4 py-3 font-extrabold text-white">BỔ SUNG HỒ SƠ →</button>
            </div>
            <div className="rounded-lg border bg-white p-3 text-sm">
              <p className="font-bold text-slate-900">Tại sao chưa có node chi tiết?</p>
              <p className="mt-1 text-slate-600">Mode/phạm vi chưa đủ authority. Hiển thị BOOKING, SI/VGM, Hải quan hay Giao hàng lúc này sẽ là đoán bừa.</p>
            </div>
            <button type="button" onClick={() => onGlobal('van-tai')} className="touch-target w-full rounded-lg border border-slate-800 px-3 text-sm font-bold">MỞ THÔNG TIN LÔ →</button>
          </div>
        </div>}
      </aside>
    </div>
  </section>;
}

export default function ShipmentJourney({ shipment: s, activeStage, work, onOpen, onGlobal, runPrimary, children, globalActive = false, globalTab = "van-tai", globalRequest = 0, attachRequest = 0 }: {
  shipment: Shipment; activeStage: string; work: string;
  onOpen: (node: JourneyNode, work: string) => boolean; onGlobal: (tab?: string) => boolean; runPrimary: () => void;
  children?: ReactNode; globalActive?: boolean; globalTab?: string;
  /** Issue #190 — the reference composition has NO journey section header:
      the "Toàn bộ lô hàng" / "+ Quy trình" controls live in the page identity
      bar. The page forwards button presses through these counters. */
  globalRequest?: number; attachRequest?: number;
}) {
  const [picked, setPicked] = useState('');
  const [mapCollapsed, setMapCollapsed] = useState(false);
  // Issue #195 — the operational overview is the default: whole journey +
  // current/problem + next action visible at once. The detailed 11-node
  // JourneyMap stays intact and mounts only when the operator explicitly asks
  // for it. This is local UI state only: no second engine, no duplicated
  // journey state — the same `nodes`, the same `pick`, the same panels.
  const [detailMapOpen, setDetailMapOpen] = useState(false);
  const [panelMode, setPanelMode] = useState<'overview' | 'quick' | 'stage' | 'global'>(activeStage ? 'stage' : globalActive ? 'global' : 'overview');
  const [expandedModule, setExpandedModule] = useState('');
  const [attachOpen, setAttachOpen] = useState(false);
  const [chosen, setChosen] = useState('');
  const [attachPending, setAttachPending] = useState('');
  const [attachError, setAttachError] = useState('');
  const { dispatch } = useStore();
  const vm = useSyncExternalStore(subscribeViewModel, getViewModel, getViewModel);
  useEffect(() => { setPicked(activeStage || ''); setPanelMode(activeStage ? 'stage' : globalActive ? 'global' : 'overview'); }, [activeStage, work, globalActive, globalTab]);
  const journey = s.journey;
  const modules = useMemo(() => journey?.modules ?? [], [journey]);
  const attachOutcome = vm?.lastWrites?.find(w => w.event === 'work_module_attach' && w.requestId === attachPending);
  const attachLoading = Boolean(attachPending && !attachOutcome);
  useEffect(() => {
    if (!attachOutcome) return;
    if (attachOutcome.ok) { setAttachOpen(false); setChosen(''); setAttachPending(''); setAttachError(''); }
    else { setAttachError(String(attachOutcome.error || 'Backend từ chối gắn quy trình.')); setAttachPending(''); }
  }, [attachOutcome]);
  if (!journey?.nodes.length) return <FreshShipmentCockpit shipment={s} onGlobal={onGlobal} runPrimary={runPrimary} globalActive={globalActive} globalTab={globalTab}>{children}</FreshShipmentCockpit>;
  const nodes = journey.nodes;
  // Issue #162 — the base map stays the base map. Module steps are NOT drawn as
  // extra branches by default; they live inside the rollup card and are
  // revealed on demand (the graph is still fully present in the payload).
  const baseNodes = nodes.filter(n => !n.moduleId);
  // Issue #190 — Quick Panel opens the CURRENT / PROBLEM factual node by
  // default: an explicit problem beats the positional current marker.
  const problemNode = baseNodes.find(n => n.state === 'PROBLEM' || n.blockers.length);
  const selected = nodes.find(n => n.id === picked) ?? nodes.find(n => n.id === activeStage) ?? problemNode ?? baseNodes.find(n => n.current) ?? baseNodes[0] ?? nodes[0];
  const stage = nodes.find(n => n.id === activeStage);
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
  const pick = (id: string) => { setPicked(id); setPanelMode('quick'); };
  const open = (node: JourneyNode, targetWork: string) => { if (onOpen(node, targetWork)) { setPicked(node.id); setPanelMode('stage'); return true; } return false; };
  const openGlobal = (tab = 'van-tai') => {
    if (onGlobal(tab)) {
      setPanelMode('global');
      // Issue #190 — full existing tab content is not designed for a 420px
      // side pane. Reuse the approved PR177 collapsed-map rail so the real
      // workspace gets readable width; the operator can reopen the map.
      setMapCollapsed(true);
      return true;
    }
    return false;
  };
  const wide = panelMode === 'stage' || panelMode === 'global';
  // Issue #190 — the page identity bar owns the two journey-level controls in
  // the reference composition; presses arrive as monotonic counters.
  const seenGlobalReq = useRef(globalRequest);
  const seenAttachReq = useRef(attachRequest);
  useEffect(() => {
    if (globalRequest === seenGlobalReq.current) return;
    seenGlobalReq.current = globalRequest;
    openGlobal();
  }, [globalRequest]);
  useEffect(() => {
    if (attachRequest === seenAttachReq.current) return;
    seenAttachReq.current = attachRequest;
    setModulesOpen(true);
    setAttachOpen(true);
  }, [attachRequest]);
  const problem = problemNode;
  const [modulesOpen, setModulesOpen] = useState(() => modules.some(m => m.status === 'BLOCKING'));
  const prevModuleCount = useRef(modules.length);
  useEffect(() => {
    if (modules.length > prevModuleCount.current) setModulesOpen(true);
    prevModuleCount.current = modules.length;
  }, [modules]);
  // Issue #195 — ONE shared side-panel render: the detail map hosts it in
  // the 451px right rail, the compact overview stacks it below the step
  // strip. Same nodes, same pick, same panels — no duplicated journey
  // state, no second engine. A plain render function (not a component) so
  // panel-local state survives parent re-renders in both layouts.
  const currentNode = baseNodes.find(n => n.current);
  const currentRegion = (Object.entries(JOURNEY_REGION_NODE_IDS) as [keyof typeof JOURNEY_REGION_NODE_IDS, readonly string[]][])
    .find(([, ids]) => currentNode ? ids.includes(currentNode.id) : false)?.[0];
  const currentLabel = currentNode
    ? `${currentRegion ? JOURNEY_REGION_LABELS[currentRegion] + ' · ' : ''}${currentNode.label}`
    : 'Chưa xác định';
  const renderSidePanel = (extraClass: string) => (
    <aside className={cx('journey-side border-l-2 border-slate-400 bg-white shadow-[-6px_0_16px_-8px_rgba(15,23,42,0.25)]', extraClass)} data-testid="journey-side-panel">
        {panelMode === 'quick' && (selected.id === 'customs-import'
          ? <div className="h-full min-h-0" data-testid="journey-customs-import-panel"><CustomsImportQuickPanel s={s} selected={selected} onOpen={open} runPrimary={runPrimary} onClose={() => setPanelMode('overview')} /></div>
          : <JourneyQuickPanel key={selected.id} shipment={s} selected={selected} onOpen={open} runPrimary={runPrimary} onClose={() => setPanelMode('overview')} />)}
        {panelMode === 'overview' && <div className="flex h-full flex-col bg-slate-50" data-testid="journey-overview-panel">
          <div className="border-b bg-white px-4 py-3"><p className="text-[10.5px] font-bold uppercase tracking-widest text-slate-500">Shipment overview</p><h3 className="text-lg font-extrabold text-slate-900">Tổng quan lô hàng</h3><p className="text-xs text-slate-500">Chọn một công đoạn ở trên để xem việc cần làm.</p></div>
          <div className="flex-1 space-y-3 overflow-auto p-4" data-testid="journey-quick-panel">
            {problem && <button type="button" onClick={() => pick(problem.id)} className="w-full rounded-lg border-2 border-red-600 bg-red-50 p-3 text-left"><p className="text-xs font-bold text-red-700">⚠ Attention</p><p className="text-lg font-extrabold text-red-800">{problem.blockers[0]}</p><p className="text-xs text-red-700">{problem.label} → Xử lý ngay</p></button>}
            <div className="rounded-lg bg-slate-900 p-3 text-white"><p className="text-[10.5px] font-bold uppercase tracking-widest text-slate-400">Next Action — toàn lô</p><p className="mt-1 font-bold">{journey.primaryAction.text}</p><button type="button" onClick={runPrimary} className="touch-target mt-1 text-xs font-bold underline">{s.nextLabel || 'Xử lý ngay'}</button></div>
            <div className="grid grid-cols-2 gap-3"><div className="rounded-lg border bg-white p-3"><p className="text-xs text-slate-500">Current</p><p className="text-sm font-bold text-blue-700">{baseNodes.find(n => n.current)?.label || 'Chưa xác định'}</p></div><div className="rounded-lg border bg-white p-3"><p className="text-xs text-slate-500">Owner lô hàng</p><p className="text-sm font-bold">{journey.owner || 'Chưa phân công'}</p></div><button type="button" onClick={() => openGlobal('chung-tu')} className="rounded-lg border bg-white p-3 text-left"><p className="text-xs text-slate-500">Documents</p><p className="font-bold">{s.attachments?.length ?? 0} tệp đã ghi nhận</p></button><button type="button" onClick={() => openGlobal('tai-chinh')} className="rounded-lg border bg-white p-3 text-left"><p className="text-xs text-slate-500">Finance</p><p className="text-sm font-bold">Xem tài chính toàn lô →</p></button></div>
            <button type="button" onClick={() => openGlobal()} className="touch-target w-full rounded-lg border border-slate-800 px-3 text-sm font-bold">Mở Global Workspace →</button>
          </div>
        </div>}
        {panelMode === 'stage' && stage && <div className="flex h-full min-h-0 flex-col" data-testid="journey-stage-workspace">
          <div className="border-b border-slate-300 bg-slate-100 px-4 py-3" data-testid="journey-quick-panel">
            <div className="flex flex-wrap items-center gap-2 text-[10.5px] font-extrabold uppercase tracking-widest text-slate-500">Stage workspace · {s.id}<button type="button" onClick={() => { setPicked(stage.id); setPanelMode('quick'); }} className="touch-target ml-auto rounded border bg-white px-2 normal-case tracking-normal">← Quick panel</button><button type="button" onClick={() => setPanelMode('overview')} aria-label="Đóng bàn làm việc" className="touch-target text-base">✕</button></div>
            <div className="mt-1 flex flex-wrap items-center gap-3"><h3 className="text-2xl font-black tracking-tight text-slate-900">{stage.label}</h3><JourneyStatus node={stage} solid /></div>
            <div className={cx('mt-1.5 rounded px-2 py-1 text-[13px]', stage.state === 'PROBLEM' ? 'bg-red-600 text-white' : 'bg-white text-slate-800 ring-1 ring-slate-200')}><b>Việc cần làm: </b>{stageAction(stage)}<span className="mt-1 block text-xs">{stage.evidence || 'Chưa có bằng chứng thực tế'} · Owner lô: {journey.owner || 'Chưa phân công'}</span></div>
          </div>
          <div className="flex shrink-0 overflow-x-auto border-b border-slate-300 bg-white px-2" aria-label="Nội dung công đoạn">{JOURNEY_WORK.map(w => <button type="button" key={w.id} aria-pressed={work === w.id} onClick={() => open(stage, w.id)} className={cx('touch-target shrink-0 border-b-[3px] px-3 py-2.5 text-xs font-extrabold tracking-wide', work === w.id ? 'border-slate-900 text-slate-900' : 'border-transparent text-slate-500')}>{w.label}</button>)}</div>
          <div className="min-h-0 flex-1 space-y-4 overflow-auto p-4" data-testid="journey-workspace-content">
            {work === 'overview' ? <div className="space-y-3 text-sm"><p>{stage.evidence || 'Chưa có bằng chứng hoàn thành.'}</p><p>{stage.blockers.join(' · ') || 'Chưa có blocker riêng được ghi nhận.'}</p><p>{stage.owned ? 'Công đoạn thuộc phạm vi đã xác nhận của Trường Thành.' : 'Thông tin tham chiếu, chưa xác nhận Trường Thành phụ trách.'}</p><button type="button" onClick={() => open(stage, 'info')} className="touch-target rounded-lg border px-3 font-bold">Mở thông tin công đoạn →</button></div> : children}
          </div>
        </div>}
        {panelMode === 'global' && <div className="flex h-full min-h-0 flex-col" data-testid="journey-global-workspace"><div className="border-b bg-slate-100 px-4 py-3"><div className="flex items-center justify-between"><h3 className="text-xl font-black">Tổng quan lô hàng · {s.id}</h3><button type="button" onClick={() => setPanelMode('overview')} aria-label="Đóng Global Workspace" className="touch-target">✕</button></div></div><div className="flex shrink-0 overflow-x-auto border-b px-2">{[{id:'van-tai',label:'Thông tin'},{id:'lay-hang',label:'Xuất khẩu'},{id:'nhap',label:'Nhập & Giao'},{id:'chung-tu',label:'Chứng từ'},{id:'tai-chinh',label:'Tài chính'},{id:'lich-su',label:'Lịch sử'}].map(t => <button type="button" key={t.id} onClick={() => openGlobal(t.id)} aria-pressed={globalTab === t.id} className={cx('touch-target shrink-0 border-b-[3px] px-3 py-2 text-xs font-extrabold', globalTab === t.id ? 'border-slate-900' : 'border-transparent text-slate-500')}>{t.label}</button>)}</div><div className="min-h-0 flex-1 space-y-4 overflow-auto p-4">{children}</div></div>}
    </aside>
  );

  return <section className="journey-demo min-w-0" data-testid="shipment-journey">
    {/* Issue #190 — the reference composition starts the Journey workspace
        directly at the map+panel split: no section title row. Identity,
        position note and the global-workspace button live in the page
        identity bar (ShipmentDetail). */}
    {/* Issue #190 CONTINUE — the map card and the right panel are separate
        cards with a 12px gap (see .journey-split), matching the reference;
        the modules strip is its own card above the split. */}
    {/* Issue #190 CONTINUE — the identity bar's "+ Quy trình" button moved here:
        the strip renders whenever attaching is allowed, even with zero
        modules, so the capability is never orphaned. */}
    {/* Issue #195 — operational overview is the default: whole journey +
        current/problem + next action at a glance. The detailed 11-node map
        stays intact behind the explicit "Bản đồ chi tiết" control; the same
        toolbar closes it again. */}
    <div className="mb-3 flex flex-wrap items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2" data-testid="journey-compact-toolbar">
      <span className="rounded-md bg-blue-50 px-2 py-1 text-xs font-semibold text-blue-800">📍 Đang ở: {currentLabel}</span>
      {problem && <span className="rounded-md bg-red-50 px-2 py-1 text-xs font-extrabold text-red-700">⚠ {problem.blockers[0] || problem.label}</span>}
      <button type="button" onClick={() => setDetailMapOpen(v => !v)} aria-expanded={detailMapOpen} data-testid="journey-detail-map-toggle" className="touch-target ml-auto inline-flex items-center gap-1.5 rounded-lg bg-[#0f2a4a] px-3.5 py-2 text-sm font-extrabold text-white">{detailMapOpen ? 'Thu gọn bản đồ' : '🗺 Bản đồ chi tiết'}</button>
    </div>
    {detailMapOpen ? (
      <div className={cx('journey-split', wide && 'journey-split-wide', wide && mapCollapsed && 'journey-split-collapsed')}>
        <JourneyMap shipment={s} nodes={baseNodes} selectedId={panelMode === 'overview' || panelMode === 'global' ? '' : selected.id} onPick={pick} collapsed={wide && mapCollapsed} onExpand={() => setMapCollapsed(false)} />
        {renderSidePanel('')}
      </div>
    ) : (
      <div className="space-y-3" data-testid="journey-compact-overview">
        <JourneyStageSummaryCards s={s} nodes={baseNodes} onOpen={open} onGlobal={openGlobal}
          canAttachModule={canAttach} onAttachModule={() => { setModulesOpen(true); setAttachOpen(true); setAttachError(''); }} />
        {panelMode !== 'overview' && renderSidePanel('journey-compact-side')}
      </div>
    )}

    {/* Issue #190 repair — an EXISTING attached module remains below the five
        cards. The empty add-module affordance no longer creates an accidental
        first-screen row: it is available behind the HỒ SƠ card's existing
        “Thông tin thêm” disclosure and reveals this same canonical panel. */}

    {(modules.length > 0 || attachOpen) && <div className="mt-3 rounded-xl border border-slate-200 bg-white" data-testid={modules.length > 0 ? 'journey-modules' : 'journey-modules-empty'}>
      <div className="flex items-center gap-1 px-3 py-1.5">
        {modules.length > 0
          ? <button type="button" onClick={() => setModulesOpen(v => !v)} aria-expanded={modulesOpen} data-testid="journey-modules-toggle"
              className="touch-target flex min-w-0 flex-1 items-center gap-2 rounded-lg px-1 py-1 text-left">
              <Layers size={14} className="shrink-0 text-slate-500" aria-hidden="true" />
              <span className="truncate text-xs font-extrabold tracking-wide text-slate-600">QUY TRÌNH ĐANG GẮN ({modules.length})</span>
              {modules.some(m => m.status === 'BLOCKING') && <span className="shrink-0 rounded-full bg-red-600 px-2 py-0.5 text-[10px] font-bold text-white">Đang chặn</span>}
              <ChevronDown size={15} className={cx('ml-auto shrink-0 text-slate-500 transition-transform', modulesOpen && 'rotate-180')} aria-hidden="true" />
            </button>
          : <span className="flex min-w-0 flex-1 items-center gap-2 px-1 py-1 text-xs font-extrabold tracking-wide text-slate-400">
              <Layers size={14} className="shrink-0" aria-hidden="true" />QUY TRÌNH PHÁT SINH
            </span>}
        {canAttach && <button type="button" onClick={() => { setModulesOpen(true); setAttachOpen(v => !v); setAttachError(''); }} data-testid="journey-add-module"
          className="touch-target inline-flex shrink-0 items-center gap-1 rounded-lg border bg-white px-2.5 py-1.5 text-xs font-bold"><Plus size={13} aria-hidden="true" />Thêm quy trình</button>}
      </div>
      {(modulesOpen || (modules.length === 0 && attachOpen)) && <div className="space-y-2 px-3 pb-3">
        {attachOpen && <div className="rounded-xl border border-slate-200 bg-white p-4" data-testid="journey-add-module-panel">
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
        {modulesOpen && modules.length > 0 && <div className="grid grid-cols-1 gap-2 xl:grid-cols-2">{modules.map(m => <ModuleCard key={m.instanceId} module={m} nodes={nodes}
          expanded={expandedModule === m.instanceId} onToggle={() => setExpandedModule(cur => cur === m.instanceId ? '' : m.instanceId)}
          selectedId={selected.id} onPick={pick} />)}</div>}
      </div>}
    </div>}
  </section>;
}

function JourneyStageSummaryCards({ s, nodes, onOpen, onGlobal, canAttachModule, onAttachModule }: {
  s: Shipment;
  nodes: JourneyNode[];
  onOpen: (node: JourneyNode, work: string) => boolean;
  onGlobal: (tab?: string) => boolean;
  canAttachModule: boolean;
  onAttachModule: () => void;
}) {
  const node = (id: string) => nodes.find(n => n.id === id);
  const leg = s.transportLegs?.[0];
  type RegionKey = keyof typeof JOURNEY_REGION_NODE_IDS;

  const regionNodes = (region: RegionKey) =>
    JOURNEY_REGION_NODE_IDS[region].map(node).filter((n): n is JourneyNode => Boolean(n));
  const regionAnchor = (region: RegionKey, prefer: string) => {
    const found = regionNodes(region);
    return found.find(n => n.current)
      ?? found.find(n => n.state === 'PROBLEM' || n.blockers.length > 0)
      ?? node(prefer)
      ?? found[0];
  };
  const regionProblemCount = (region: RegionKey) =>
    regionNodes(region).filter(n => n.state === 'PROBLEM' || n.blockers.length > 0).length;
  const regionCurrent = (region: RegionKey) => regionNodes(region).some(n => n.current);
  const regionDone = (region: RegionKey) => {
    const found = regionNodes(region);
    return found.length > 0 && found.every(n => n.completed);
  };

  const booking = regionAnchor('origin', 'booking');
  const main = regionAnchor('main', 'arrival');
  const customs = regionAnchor('import', 'customs-import');
  const delivery = regionAnchor('delivery', 'delivery');
  const profileReady = s.executionProfile?.state === 'PROFILE_READY';

  const phaseRows: Array<{
    num: number; key: string; title: string; region?: RegionKey; n?: JourneyNode;
    summary: string; fallback: string;
  }> = [
    { num: 1, key: 'origin', title: 'Đầu đi', region: 'origin', n: booking,
      summary: s.transport?.bookingNo || leg?.bookingNo || booking?.deadline || 'Chưa có mốc chính', fallback: 'lay-hang' },
    { num: 2, key: 'main', title: 'Chặng chính', region: 'main', n: main,
      summary: leg?.ata ? `ATA ${leg.ata}` : leg?.eta ? `ETA ${leg.eta}` : main?.deadline || 'Chưa có ETA/ATA', fallback: 'van-tai' },
    { num: 3, key: 'import', title: 'Nhập khẩu', region: 'import', n: customs,
      summary: s.importInfo.customsStatus ? 'Đã thông quan' : s.importInfo.declarationNo ? `Tờ khai ${s.importInfo.declarationNo}` : 'Chưa có tờ khai', fallback: 'nhap' },
    { num: 4, key: 'delivery', title: 'Giao hàng', region: 'delivery', n: delivery,
      summary: s.importInfo.delivered ? 'Đã giao' : s.importInfo.schedule ? `Dự kiến ${s.importInfo.schedule}` : 'Chưa có lịch giao', fallback: 'nhap' },
    { num: 5, key: 'files-finance', title: 'Hồ sơ & Chi phí',
      summary: s.commercialFlow?.modeLabel || (profileReady ? 'Hồ sơ đã xác nhận' : 'Chưa xác nhận hình thức'), fallback: 'chung-tu' },
  ];

  const openStage = (row: typeof phaseRows[number], work: 'info' | 'docs') => {
    if (row.n) return onOpen(row.n, work);
    return onGlobal(work === 'docs' ? 'chung-tu' : row.fallback);
  };

  return <nav aria-label="Hành trình lô hàng" data-testid="journey-macro-steps"
    className="grid grid-cols-2 gap-2 rounded-xl border border-slate-200 bg-white p-2 sm:grid-cols-5">
    {phaseRows.map(row => {
      const isCurrent = row.region ? regionCurrent(row.region) : false;
      const problems = row.region ? regionProblemCount(row.region) : 0;
      const done = row.region ? regionDone(row.region) : profileReady;
      return <section key={row.key} data-testid={`journey-macro-step-${row.num}`}
        className={cx(
          'min-w-0 rounded-lg border-2 bg-white p-2',
          isCurrent ? 'border-blue-600 bg-blue-50/60' : problems > 0 ? 'border-red-300' : done ? 'border-emerald-300' : 'border-slate-200'
        )}>
        <div className="flex items-start gap-2">
          <span className={cx('grid h-6 w-6 shrink-0 place-items-center rounded-full text-xs font-black',
            isCurrent ? 'bg-blue-600 text-white' : done ? 'bg-emerald-600 text-white' : 'bg-slate-200 text-slate-700')}>{row.num}</span>
          <div className="min-w-0 flex-1">
            <div className="flex min-w-0 items-center gap-1">
              <h3 className="truncate text-[12.5px] font-black text-[#0f2a4a]">{row.title}</h3>
              {problems > 0 && <span className="shrink-0 text-[10px] font-extrabold text-red-700">⚠ {problems}</span>}
            </div>
            <p className={cx('truncate text-[10.5px] font-semibold', isCurrent ? 'text-blue-700' : 'text-slate-500')}>
              {isCurrent ? '📍 Đang ở đây' : row.summary}
            </p>
          </div>
        </div>
        {row.num < 5 ? <div className="mt-2 grid grid-cols-2 gap-1">
          <button type="button" onClick={() => openStage(row, 'info')} data-testid={`journey-macro-work-${row.num}`}
            className="touch-target rounded-md border border-slate-200 px-1.5 py-1 text-[10.5px] font-bold text-slate-700">Công việc</button>
          <button type="button" onClick={() => openStage(row, 'docs')} data-testid={`journey-macro-docs-${row.num}`}
            className="touch-target rounded-md border border-slate-200 px-1.5 py-1 text-[10.5px] font-bold text-slate-700">Chứng từ</button>
        </div> : <div className="mt-2 grid grid-cols-2 gap-1">
          <button type="button" onClick={() => onGlobal('chung-tu')} data-testid="journey-macro-files-5"
            className="touch-target rounded-md border border-slate-200 px-1.5 py-1 text-[10.5px] font-bold text-slate-700">Hồ sơ</button>
          <button type="button" onClick={() => onGlobal('tai-chinh')} data-testid="journey-macro-finance-5"
            className="touch-target rounded-md bg-[#0f2a4a] px-1.5 py-1 text-[10.5px] font-bold text-white">Chi phí</button>
          <button type="button" onClick={() => onGlobal('lich-su')} data-testid="journey-macro-history-5"
            className="touch-target col-span-2 rounded-md px-1.5 py-1 text-[10px] font-semibold text-slate-500">Lịch sử</button>
          {canAttachModule && <button type="button" onClick={onAttachModule} data-testid="journey-add-module-page"
            className="touch-target col-span-2 rounded-md border border-dashed border-slate-300 px-1.5 py-1 text-[10px] font-semibold text-slate-500">+ Quy trình phát sinh</button>}
        </div>}
      </section>;
    })}
  </nav>;
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
