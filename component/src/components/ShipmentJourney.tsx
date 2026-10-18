import { useEffect, useMemo, useRef, useState, useSyncExternalStore, type ReactNode } from 'react';
import { ArrowRight, CheckCircle2, Circle, Clock, CircleAlert, ChevronDown, ChevronRight, Info, Layers, MapPin, Plus } from 'lucide-react';
import type { AttentionItem, JourneyNode, Shipment, WorkModuleGuidance, WorkModuleRollup } from '../lib/viewmodel';
import { getViewModel, subscribeViewModel } from '../lib/viewmodel';
import { useStore } from '../lib/store';
import { cx, fmtCcy } from '../lib/format';
import { Field, inputCls } from './ui';
import JourneyMap, { JOURNEY_META as META, JourneyStatus } from './JourneyMap';
import JourneyQuickPanel, { stageAction } from './JourneyQuickPanel';
import JourneyBubble, { bubbleTasksFor } from './JourneyBubble';

export const JOURNEY_REGION_NODE_IDS: Record<'origin' | 'main' | 'import' | 'delivery', readonly string[]> = {
  // Sea has detailed node ids; Air/Rail/Road may project canonical profile
  // stage ids instead. Keep the five macro phases transport-mode neutral.
  origin: [
    'booking', 'pickup', 'customs-export', 'si-vgm', 'gate-in',
    'ORIGIN_HANDOFF', 'SEA_DOCUMENTS', 'AIR_DOCUMENTS',
    'SEA_EQUIPMENT', 'SEA_CONSOLIDATION',
    // LOGI-199 T2–T4 mode-specific origin nodes.
    'cfs-receipt', 'air-booking', 'air-acceptance', 'road-vehicle', 'road-ltl',
  ],
  main: [
    'etd', 'on-board', 'transit', 'arrival',
    'CROSS_BORDER', 'MAIN_CARRIAGE', 'RAIL_CARRIAGE',
    'ROAD_TRUCK_PROFILE', 'ROAD_CONSOLIDATION', 'INSURANCE_EVIDENCE',
    'uplift', 'air-transit', 'air-arrival', 'road-border',
  ],
  import: ['customs-import'],
  delivery: ['delivery'],
} as const;

export const JOURNEY_REGION_LABELS = {
  origin: 'Đầu đi',
  main: 'Chặng chính',
  import: 'Nhập khẩu',
  delivery: 'Giao hàng',
} as const;

export function journeyRegionNodeIds(nodeId: string): readonly string[] {
  const match = (Object.values(JOURNEY_REGION_NODE_IDS) as readonly (readonly string[])[])
    .find((ids) => ids.includes(nodeId));
  return match ?? [nodeId];
}

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
        <p className="text-[12px] font-bold tracking-wide text-slate-500">QUY TRÌNH PHÁT SINH · V{m.templateVersion}</p>
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
    <span className="inline-flex items-center gap-1 text-[12px] font-bold"><Icon size={13} aria-hidden="true" />{m.label}</span>
    <span className="mt-0.5 text-sm font-extrabold">{node.label}</span>
    <span className="text-[12px]">{node.evidence || 'Chưa có bằng chứng thực tế'}</span>
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
          <span className="inline-flex items-center gap-1 rounded-md border border-red-200 bg-red-50 px-1.5 py-0.5 text-[12px] font-extrabold text-red-700">
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

/**
 * Issue #199 follow-up — zero-node / missing-Journey exception only.
 * Keep the same full-width paper-chart map family as the populated Journey,
 * but show no invented nodes or stages. The truthful profile status and its
 * single CTA remain visible; the CTA only navigates to the real editor.
 *
 * The global branch preserves the whole-lot tabs and their existing children,
 * including the Execution Profile editor reached by the primary action.
 */
function ZeroNodeJourney({ shipment: s, onGlobal, runPrimary, children, globalActive = false, globalTab = 'van-tai' }: {
  shipment: Shipment;
  onGlobal: (tab?: string) => boolean;
  runPrimary: () => void;
  children?: ReactNode;
  globalActive?: boolean;
  globalTab?: string;
}) {
  const next = s.executionProfile?.nextAction;
  const profileState = s.executionProfile?.stateLabel || 'Hồ sơ lô còn thiếu';
  const tabs = [
    { id: 'van-tai', label: 'Thông tin' },
    { id: 'lay-hang', label: 'Xuất khẩu' },
    { id: 'nhap', label: 'Nhập & Giao' },
    { id: 'chung-tu', label: 'Chứng từ' },
    { id: 'tai-chinh', label: 'Tài chính' },
    { id: 'lich-su', label: 'Lịch sử' },
  ];
  return <section className="journey-demo min-w-0" data-testid="shipment-journey" data-empty-journey="true">
    {globalActive ? (
      <div className="flex h-full min-h-0 flex-col" data-testid="journey-global-workspace">
        <div className="border-b bg-slate-100 px-4 py-3">
          <h3 className="text-xl font-black">Toàn bộ lô hàng · {s.id}</h3>
          <p className="text-xs text-slate-500">Chưa có Journey chi tiết; UNKNOWN không được biến thành công đoạn giả.</p>
        </div>
        <div className="flex shrink-0 overflow-x-auto border-b px-2">
          {tabs.map(t => <button type="button" key={t.id} onClick={() => onGlobal(t.id)} aria-pressed={globalTab === t.id}
            className={cx('touch-target shrink-0 border-b-[3px] px-3 py-2 text-xs font-extrabold', globalTab === t.id ? 'border-slate-900' : 'border-transparent text-slate-500')}>{t.label}</button>)}
        </div>
        <div className="min-h-0 flex-1 space-y-4 overflow-auto p-4">{children}</div>
      </div>
    ) : (<>
      <div className="journey-focus-row" data-testid="journey-zero-focus-row">
        <div className="journey-toolbar" data-testid="journey-compact-toolbar">
          <span className="journey-toolbar-chip journey-toolbar-here">📍 Đang ở: Chưa xác định</span>
          <span className="journey-toolbar-next">Chưa đủ hồ sơ để xác định công đoạn chi tiết.</span>
          <span className="journey-toolbar-spacer" />
        </div>
      </div>
      <div className="journey-split journey-map-first journey-zero-map-first" data-testid="journey-zero-map-first"
        data-layout="full-width" style={{ width: '100%' }}>
        <JourneyMap shipment={s} nodes={[]} selectedId="" onPick={() => {}} collapsed={false} onExpand={() => {}} />
        <div className="journey-zero-notice" data-testid="journey-empty-map" role="status" aria-labelledby="journey-zero-title">
          <div className="journey-zero-profile" data-testid="journey-zero-profile">
            <p className="journey-zero-kicker">CẦN LÀM NGAY</p>
            <span className="journey-zero-profile-state" data-testid="journey-zero-profile-state">{profileState}</span>
            <h2 id="journey-zero-title" className="journey-zero-title">Chưa có sơ đồ Journey</h2>
            <p className="journey-zero-summary">Chưa đủ hồ sơ để xác định công đoạn chi tiết.</p>
            <p className="journey-zero-next-action" data-testid="journey-zero-next-action">{next?.label || 'Bổ sung hồ sơ thực hiện lô'}</p>
            <p className="journey-zero-detail">{next?.detail || 'Xác nhận dữ liệu hồ sơ và phạm vi dịch vụ của Trường Thành.'}</p>
            <button type="button" onClick={runPrimary} data-testid="journey-zero-primary-cta"
              className="touch-target journey-zero-cta">BỔ SUNG HỒ SƠ →</button>
          </div>
        </div>
      </div>
    </>)}
  </section>;
}


export default function ShipmentJourney({ shipment: s, activeStage, work, onOpen, onGlobal, runPrimary, children, stageContent, hasStageContent = false, globalActive = false, globalTab = "van-tai", attentionItems = [], globalRequest = 0, attachRequest = 0 }: {
  shipment: Shipment; activeStage: string; work: string;
  onOpen: (node: JourneyNode, work: string) => boolean; onGlobal: (tab?: string) => boolean; runPrimary: () => void;
  children?: ReactNode; stageContent?: ReactNode; hasStageContent?: boolean; globalActive?: boolean; globalTab?: string;
  attentionItems?: AttentionItem[];
  /** Issue #190 — the reference composition has NO journey section header:
      the "Toàn bộ lô hàng" / "+ Quy trình" controls live in the page identity
      bar. The page forwards button presses through these counters. */
  globalRequest?: number; attachRequest?: number;
}) {
  const [picked, setPicked] = useState('');
  // G2 — node-attached task bubble (Owner HTML): separate from the popup state.
  const [bubbleId, setBubbleId] = useState('');
  const [utilityOpen, setUtilityOpen] = useState(false);
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
  // Issue #197 hook-ordering repair — the zero-node early return MUST come
  // after every Hook. A shipment that gains Journey nodes while mounted would
  // otherwise render a different hook count and React throws "Rendered more
  // hooks than during the previous render". The hasNodes guards keep the
  // zero-node behavior identical: the request/module effects stay inert there.
  const hasNodes = Boolean(journey?.nodes.length);
  const modules = useMemo(() => journey?.modules ?? [], [journey]);
  const attachOutcome = vm?.lastWrites?.find(w => w.event === 'work_module_attach' && w.requestId === attachPending);
  const attachLoading = Boolean(attachPending && !attachOutcome);
  useEffect(() => {
    if (!attachOutcome) return;
    if (attachOutcome.ok) { setAttachOpen(false); setChosen(''); setAttachPending(''); setAttachError(''); }
    else { setAttachError(String(attachOutcome.error || 'Backend từ chối gắn quy trình.')); setAttachPending(''); }
  }, [attachOutcome]);
  const openGlobal = (tab = 'van-tai') => {
    if (onGlobal(tab)) {
      setPanelMode('global');
      // Owner 2026-10-13: the 340px Journey map stays visible alongside the
      // global workspace. Never collapse it to the rail.
      return true;
    }
    return false;
  };
  // Issue #190 — the page identity bar owns the two journey-level controls in
  // the reference composition; presses arrive as monotonic counters.
  const seenGlobalReq = useRef(globalRequest);
  const seenAttachReq = useRef(attachRequest);
  useEffect(() => {
    if (!hasNodes) return;
    if (globalRequest === seenGlobalReq.current) return;
    seenGlobalReq.current = globalRequest;
    openGlobal();
  }, [globalRequest, hasNodes]);
  useEffect(() => {
    if (!hasNodes) return;
    if (attachRequest === seenAttachReq.current) return;
    seenAttachReq.current = attachRequest;
    setModulesOpen(true);
    setAttachOpen(true);
  }, [attachRequest, hasNodes]);
  const [modulesOpen, setModulesOpen] = useState(() => modules.some(m => m.status === 'BLOCKING'));
  const prevModuleCount = useRef(modules.length);
  useEffect(() => {
    if (!hasNodes) return;
    if (modules.length > prevModuleCount.current) setModulesOpen(true);
    prevModuleCount.current = modules.length;
  }, [modules, hasNodes]);
  // LOGI #199 zero-node exception: render a full-width chart-paper empty state;
  // populated Journeys continue through the unchanged map-first branch below.
  // G2 — the popup is a modal over the map (desktop) / bottom sheet (mobile).
  const modalOpen = panelMode !== 'overview';
  // G2 — Escape closes the popup modal (keyboard parity with the backdrop).
  useEffect(() => {
    if (!modalOpen) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') setPanelMode('overview'); };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [modalOpen]);
  if (!hasNodes) return <ZeroNodeJourney shipment={s} onGlobal={onGlobal} runPrimary={runPrimary} globalActive={globalActive} globalTab={globalTab}>{children}</ZeroNodeJourney>;
  const nodes = journey?.nodes ?? [];
  // Issue #162 — the base map stays the base map. Module steps are NOT drawn as
  // extra branches by default; they live inside the rollup card and are
  // revealed on demand (the graph is still fully present in the payload).
  const baseNodes = nodes.filter(n => !n.moduleId);
  // Issue #190 — Quick Panel opens the CURRENT / PROBLEM factual node by
  // default: an explicit problem beats the positional current marker.
  const problemNode = baseNodes.find(n => n.state === 'PROBLEM' || n.blockers.length);
  const problem = problemNode;
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
  // G2 — a base node opens its task bubble on the map; a Work Module step (not
  // drawn as a base node) keeps the direct quick-panel path.
  const pick = (id: string) => {
    const n = nodes.find(x => x.id === id);
    setPicked(id);
    setUtilityOpen(false);
    if (n?.moduleId) { setBubbleId(''); setPanelMode('quick'); } else setBubbleId(id);
  };
  const open = (node: JourneyNode, targetWork: string) => { if (onOpen(node, targetWork)) { setPicked(node.id); setBubbleId(''); setUtilityOpen(false); setPanelMode('stage'); return true; } return false; };

  // Issue #195 — ONE shared side-panel render: the detail map hosts it in
  // the modal card over the map-first canvas (superseding journey-split-small-map).
  const currentNode = baseNodes.find(n => n.current);
  const currentRegion = (Object.entries(JOURNEY_REGION_NODE_IDS) as [keyof typeof JOURNEY_REGION_NODE_IDS, readonly string[]][])
    .find(([, ids]) => currentNode ? ids.includes(currentNode.id) : false)?.[0];
  const currentLabel = currentNode
    ? `${currentRegion ? JOURNEY_REGION_LABELS[currentRegion] + ' · ' : ''}${currentNode.label}`
    : 'Chưa xác định';
  const renderSidePanel = (extraClass: string) => (
    <aside className={cx('journey-side journey-modal-card bg-white', extraClass)} data-testid="journey-side-panel">
        {panelMode === 'quick' && (selected.id === 'customs-import'
          ? <div className="h-full min-h-0" data-testid="journey-customs-import-panel"><CustomsImportQuickPanel s={s} selected={selected} onOpen={open} runPrimary={runPrimary} onClose={() => setPanelMode('overview')} /></div>
          : <JourneyQuickPanel key={selected.id} shipment={s} selected={selected} onOpen={open} runPrimary={runPrimary} onClose={() => setPanelMode('overview')} />)}
        {panelMode === 'stage' && stage && <div className="flex h-full min-h-0 flex-col bg-white" data-testid="journey-stage-workspace">
          <div className="border-b border-[#1E3E5C] bg-[#10263C] px-4 py-3 text-white" data-testid="journey-quick-panel">
            <div className="flex flex-wrap items-center gap-2 font-mono text-[12px] font-bold uppercase tracking-wider text-[#9CCAF0]">
              <span>CÔNG ĐOẠN · {s.id}</span>
              <button type="button" onClick={() => setPanelMode('overview')} aria-label="Đóng công đoạn" className="touch-target ml-auto rounded-lg border border-[#355577] bg-[#173754] px-2.5 py-1 font-sans text-[12px] font-semibold normal-case tracking-normal text-[#D6E6F5] hover:bg-[#1E466A]">Đóng ✕</button>
            </div>
            <div className="mt-1 flex flex-wrap items-center gap-3">
              <h3 className="text-[18px] font-extrabold tracking-tight text-white">{stage.label}</h3>
              <JourneyStatus node={stage} solid />
            </div>
            <div className={cx('mt-2 rounded-lg px-3 py-1.5 text-[13px]', stage.state === 'PROBLEM' ? 'border border-[#E0A197] bg-[#F6DFDB] text-[#8E2F22]' : 'border border-[#2B4B6B] bg-[#173754] text-[#E6F0FA]')}>
              <b>Cần làm: </b>{stageAction(stage)}
              {stage.evidence && <span className="mt-0.5 block text-[12px] opacity-90">Bằng chứng: {stage.evidence}</span>}
            </div>
          </div>
          <div className="flex shrink-0 overflow-x-auto border-b border-[#D6DEE7] bg-[#F4F7FA] px-3" aria-label="Nội dung công đoạn">{JOURNEY_WORK.map(w => <button type="button" key={w.id} aria-pressed={work === w.id} onClick={() => open(stage, w.id)} className={cx('touch-target shrink-0 border-b-[3px] px-3 py-2 text-[12.5px] font-extrabold tracking-wide', work === w.id ? 'border-[#123A5E] text-[#10263C]' : 'border-transparent text-[#5B6875]')}>{w.label}</button>)}</div>
          <div className="min-h-0 flex-1 space-y-4 overflow-auto p-4" data-testid="journey-workspace-content">
            {work === 'overview' ? <div className="space-y-3 text-sm"><p>{stage.evidence || 'Chưa có bằng chứng hoàn thành.'}</p><p>{stage.blockers.join(' · ') || 'Chưa có việc chặn riêng.'}</p><button type="button" onClick={() => open(stage, 'info')} className="touch-target rounded-lg border px-3 font-bold">Mở công việc →</button></div>
              : work === 'info' && !hasStageContent ? <div className="space-y-3 text-sm" data-testid="journey-stage-work-summary">
                  <dl className="divide-y divide-slate-100 rounded-lg border border-slate-200 bg-white">
                    <div className="flex items-start justify-between gap-3 px-3 py-2"><dt className="text-slate-500">Trạng thái</dt><dd className="text-right font-bold"><Status node={stage} /></dd></div>
                    <div className="flex items-start justify-between gap-3 px-3 py-2"><dt className="text-slate-500">Mốc</dt><dd className="text-right font-bold">{stage.deadline || 'Chưa ghi nhận'}</dd></div>
                    <div className="flex items-start justify-between gap-3 px-3 py-2"><dt className="text-slate-500">Bằng chứng</dt><dd className="max-w-[70%] text-right font-bold">{stage.evidence || 'Chưa có'}</dd></div>
                  </dl>
                  {stage.blockers.length > 0 && <p className="rounded-lg bg-red-50 px-3 py-2 font-semibold text-red-800">⚠ {stage.blockers[0]}</p>}
                  <button type="button" onClick={() => openGlobal(stage.targetTab)} className="touch-target w-full rounded-lg border border-slate-300 bg-white px-3 py-2 font-bold text-[#0f2a4a]">Mở khu vực cập nhật</button>
                </div>
              : work === 'docs' ? <section className="space-y-3 text-sm" data-testid="journey-stage-documents">
                  <h4 className="font-extrabold text-[#10263C]">Chứng từ · {stage.label}</h4>
                  <p className="text-slate-600">Chỉ hiển thị loại chứng từ và tệp đã được liên kết rõ với công đoạn này; không tự gán tệp toàn lô.</p>
                  <div className="flex flex-wrap gap-2" data-testid="journey-stage-doc-categories">
                    {stage.documentCategories.length
                      ? stage.documentCategories.map(category => <span key={category} className="rounded-md border border-slate-300 bg-slate-50 px-2 py-1 font-semibold">{category}</span>)
                      : <span className="text-slate-500">Chưa có loại chứng từ được chỉ định cho công đoạn.</span>}
                  </div>
                  <p className="font-semibold">Tệp đã gắn với công đoạn ({(s.attachments ?? []).filter(f => stage.documentIds.includes(f.id)).length})</p>
                  {(s.attachments ?? []).some(f => stage.documentIds.includes(f.id))
                    ? <ul className="space-y-2" data-testid="journey-stage-doc-files">
                        {(s.attachments ?? []).filter(f => stage.documentIds.includes(f.id)).map(f =>
                          <li key={f.id} className="rounded-lg border border-slate-200 p-2">{f.name} <span className="text-slate-500">· {f.categoryLabel}</span></li>)}
                      </ul>
                    : <p className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-slate-600">Chưa có tệp nào được ghi nhận riêng cho công đoạn này.</p>}
                  <button type="button" onClick={() => openGlobal('chung-tu')} className="touch-target rounded-lg border border-[#123A5E] px-3 py-2 font-bold text-[#123A5E]">Mở kho chứng từ toàn lô →</button>
                </section>
              : stageContent}
          </div>
        </div>}
        {panelMode === 'global' && <div className="flex h-full min-h-0 flex-col bg-white" data-testid="journey-global-workspace">
          <div className="border-b border-[#1E3E5C] bg-[#10263C] px-4 py-3 text-white">
            <div className="flex items-center justify-between gap-2">
              <div>
                <div className="font-mono text-[12px] font-bold uppercase tracking-wider text-[#9CCAF0]">TIỆN ÍCH TOÀN LÔ · MÃ LÔ {s.id}</div>
                <h3 className="text-[18px] font-extrabold text-white">Tổng quan lô hàng · {s.id}</h3>
              </div>
              <button type="button" onClick={() => setPanelMode('overview')} aria-label="Đóng Global Workspace" className="touch-target rounded-lg border border-[#355577] bg-[#173754] px-2.5 py-1 text-[12px] font-semibold text-[#D6E6F5] hover:bg-[#1E466A]">Đóng ✕</button>
            </div>
          </div>
          <div className="flex shrink-0 overflow-x-auto border-b border-[#D6DEE7] bg-[#F4F7FA] px-3">{[{id:'van-tai',label:'Thông tin'},{id:'lay-hang',label:'Xuất khẩu'},{id:'nhap',label:'Nhập & Giao'},{id:'chung-tu',label:'Chứng từ'},{id:'tai-chinh',label:'Tài chính'},{id:'lich-su',label:'Lịch sử'}].map(t => <button type="button" key={t.id} onClick={() => openGlobal(t.id)} aria-pressed={globalTab === t.id} className={cx('touch-target shrink-0 border-b-[3px] px-3 py-2 text-[12.5px] font-extrabold', globalTab === t.id ? 'border-[#123A5E] text-[#10263C]' : 'border-transparent text-[#5B6875]')}>{t.label}</button>)}</div>
          <div className="min-h-0 flex-1 space-y-4 overflow-auto p-4">{children}</div>
        </div>}
    </aside>
  );

  // N2 — Floating top-right Hồ sơ & Tài chính control + utility bubble (matching Owner HTML ref-01 & ref-05).
  // Also hosts journey-overview-panel / journey-side-panel when no node bubble or modal is active.
  const overviewActive = !bubbleId && !modalOpen;
  const topRightUtility = (
    <div
      data-no-pan
      onPointerDown={e => e.stopPropagation()}
      data-testid={overviewActive ? 'journey-side-panel' : undefined}
      className="absolute right-3 top-3 z-30 hidden sm:flex flex-col items-end gap-1.5"
    >
      <div
        data-testid={overviewActive ? "journey-overview-panel" : "journey-utility-bar"}
        className="flex flex-wrap items-center justify-end gap-1.5"
      >
        {/* data-testid="journey-overview-panel" is active in overview state */}
        <div className="hidden md:flex items-center gap-1 rounded-xl border border-[#D6DEE7] bg-white/94 px-2 py-1 shadow-sm backdrop-blur-[2px]">
          <button
            type="button"
            onClick={() => { setUtilityOpen(false); openGlobal('van-tai'); }}
            className="rounded-lg px-2 py-1 text-[12px] font-bold text-[#123A5E] hover:bg-[#EAF2FA]"
          >
            Hồ sơ lô<span className="sr-only"> · Mở Global Workspace</span>
          </button>
          <span className="text-slate-300" aria-hidden="true">|</span>
          <button
            type="button"
            onClick={() => { setUtilityOpen(false); openGlobal('chung-tu'); }}
            className="rounded-lg px-2 py-1 text-[12px] font-bold text-[#123A5E] hover:bg-[#EAF2FA]"
          >
            Chứng từ ({(s.attachments ?? []).length})<span className="sr-only"> · Documents</span>
          </button>
          <span className="text-slate-300" aria-hidden="true">|</span>
          <button
            type="button"
            onClick={() => { setUtilityOpen(false); openGlobal('tai-chinh'); }}
            className="rounded-lg px-2 py-1 text-[12px] font-bold text-[#123A5E] hover:bg-[#EAF2FA]"
          >
            Tài chính
          </button>
        </div>
        <button
          type="button"
          data-node="utility-trigger"
          data-testid="journey-utility-trigger"
          onClick={() => { setBubbleId(''); setUtilityOpen(v => !v); }}
          className={cx(
            'flex items-center gap-2 rounded-xl border px-3 py-2 text-left shadow-[0_8px_20px_-6px_rgba(16,38,60,0.22)] transition',
            utilityOpen
              ? 'border-[#1D6FA8] bg-[#10263C] text-white ring-2 ring-[#1D6FA8]/35'
              : 'border-[#123A5E] bg-[#123A5E] text-white hover:bg-[#10263C]'
          )}
        >
          <span className="font-mono text-[13px] font-bold text-[#9CCAF0]">▤</span>
          <div>
            <div className="text-[12px] font-bold uppercase tracking-wider leading-tight">
              Hồ sơ &amp; Tài chính
            </div>
            <div className="hidden sm:block text-[12px] font-normal text-[#B9D6EE] leading-tight mt-0.5">
              Báo giá · Chứng từ · Công nợ · Lịch sử
            </div>
          </div>
        </button>
      </div>

      {utilityOpen && (
        <div
          data-testid="journey-utility-bubble"
          className="w-[336px] max-w-[calc(100vw-32px)] overflow-hidden rounded-xl border border-[#C9D4DF] bg-white shadow-[0_18px_36px_-14px_rgba(16,38,60,0.38)]"
        >
          <div className="flex items-start justify-between gap-2 border-b border-[#1E3E5C] bg-[#10263C] px-3.5 py-2.5 text-white">
            <div>
              <div className="font-mono text-[12px] font-bold uppercase tracking-wider text-[#9CCAF0]">Tiện ích toàn lô</div>
              <div className="text-[14px] font-extrabold text-white">Hồ sơ &amp; Tài chính · {s.id}</div>
            </div>
            <button
              type="button"
              onClick={() => setUtilityOpen(false)}
              aria-label="Đóng tiện ích hồ sơ"
              className="rounded-md border border-[#2B4B6B] bg-[#173754] px-2 py-0.5 text-[12px] font-semibold text-[#C8D9EA]"
            >
              ✕
            </button>
          </div>
          <div className="divide-y divide-[#E6ECF2]">
            {[
              { id: 'van-tai', title: 'Hồ sơ thực hiện lô & vận tải', sub: `${s.mode || '—'} · ${s.incoterm || '—'} · ${s.route || '—'}`, badge: s.executionProfile?.serviceScopeConfirmed ? '✓ Đã xác nhận' : '◷ Cần rà soát' },
              { id: 'chung-tu', title: 'Chứng từ & biểu mẫu (Documents)', sub: `${(s.attachments ?? []).length} tệp đính kèm · Kho biểu mẫu lô`, badge: s.missingDocs.length ? `! Thiếu ${s.missingDocs.length}` : '✓ Đủ danh mục' },
              { id: 'tai-chinh', title: 'Tài chính & công nợ', sub: `Đồng tiền: ${s.finance.currency || 'VND'} · Tách biệt VND/USD`, badge: s.finance.outstanding ? '◐ Đang theo dõi' : '✓ Cân đối' },
              { id: 'nhap', title: 'Nhập khẩu & giao hàng', sub: s.importInfo.declarationNo ? `TK ${s.importInfo.declarationNo}` : 'Chưa ghi nhận số tờ khai', badge: s.importInfo.delivered ? '✓ Đã giao' : '◐ Đang xử lý' },
              { id: 'lich-su', title: 'Lịch sử xử lý & kiểm toán', sub: `${(s.timeline ?? []).length} bản ghi sự kiện`, badge: 'Tra cứu' },
            ].map(item => (
              <button
                key={item.id}
                type="button"
                data-testid={`journey-utility-item-${item.id}`}
                onClick={() => { setUtilityOpen(false); openGlobal(item.id); }}
                className="flex w-full items-center justify-between gap-2 bg-white px-3.5 py-2.5 text-left hover:bg-[#F4F8FC]"
              >
                <span className="min-w-0 flex-1">
                  <span className="block text-[13px] font-bold text-[#10263C]">{item.title}</span>
                  <span className="block truncate font-mono text-[12px] text-[#5B6875]">{item.sub}</span>
                </span>
                <span className="shrink-0 rounded-md border border-[#C8D3DF] bg-[#F4F7FA] px-2 py-0.5 text-[12px] font-semibold text-[#123A5E]">
                  {item.badge}
                </span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );

  return <section className="journey-demo min-w-0" data-testid="shipment-journey">
    {/* One compact desktop status row. On mobile these remain stacked to preserve the approved top-chrome rhythm. */}
    <div className="journey-focus-row" data-testid="journey-focus-row">
      {/* Supersedes journey-split-small-map with journey-map-first (Owner Visual Fidelity Override 15/10/2026).
          Canonical action reference: journey?.primaryAction.text */}
      <div className="journey-toolbar" data-testid="journey-compact-toolbar">
      <span className="journey-toolbar-chip journey-toolbar-here">Đang ở: {currentLabel}</span>
      {problem && <span className="journey-toolbar-chip journey-toolbar-alert">⚠ {problem.blockers[0] || problem.label}</span>}
      {journey?.primaryAction?.text && <span className="journey-toolbar-next"><b>Việc tiếp:</b> {journey.primaryAction.text}</span>}
      <span className="journey-toolbar-spacer" />
      {canAttach && (
        <button
          type="button"
          onClick={() => { setModulesOpen(true); setAttachOpen(v => !v); setAttachError(''); }}
          className="journey-toolbar-btn"
          data-testid="journey-attach-open"
        >
          + Quy trình ({modules.length})
        </button>
      )}
      <button type="button" onClick={runPrimary} className="journey-toolbar-btn journey-toolbar-btn-primary">Xử lý →</button>
      <button type="button" onClick={() => openGlobal()} className="journey-toolbar-btn" data-testid="journey-global-open">▤ Hồ sơ &amp; Tài chính</button>
      </div>
    </div>
    <div className="journey-split journey-map-first" data-testid="journey-split-view">
      <JourneyMap shipment={s} nodes={baseNodes} selectedId={bubbleId || (modalOpen && panelMode !== 'global' ? selected.id : '')} onPick={pick} collapsed={false} onExpand={() => {}}
        bubbleNodeId={bubbleId}
        topRightOverlay={topRightUtility}
        renderBubble={(n, p, c, below) => <JourneyBubble node={n} pos={p} canvas={c} placeBelow={below}
          tasks={bubbleTasksFor(n, s, modules, (node, work) => { open(node, work); }, (stepId) => pick(stepId), nodes)}
          onClose={() => setBubbleId('')}
          onQuick={() => { setBubbleId(''); setPicked(n.id); setPanelMode('quick'); }} />} />
    </div>
    {modalOpen && <div className="journey-modal-layer" data-testid="journey-modal">
      <div className="journey-modal-backdrop" onClick={() => setPanelMode('overview')} aria-hidden="true" />
      {renderSidePanel('')}
    </div>}

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
              {modules.some(m => m.status === 'BLOCKING') && <span className="shrink-0 rounded-full bg-red-600 px-2 py-0.5 text-[12px] font-bold text-white">Đang chặn</span>}
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
  // LOGI-199 T1 — the backend declares which evidence facts belong to this
  // node (scope/load-model aware); the panel never invents its own field list.
  const fields = node?.factFields ?? [];
  const TITLES: Record<string, string> = { booking: 'Booking — xác nhận của hãng tàu', 'customs-export': 'Hải quan xuất — tờ khai và thông quan', 'gate-in': 'Container — cấp rỗng, đóng hàng, EIR, gate-in', 'on-board': 'Xếp hàng lên tàu — bằng chứng on-board', delivery: 'Đầu nhận — D/O, POD, trả rỗng', 'si-vgm': 'SI / VGM — ghi nhận bằng chứng', 'cfs-receipt': 'CFS — nhận hàng và ghép container', 'air-acceptance': 'Kho hàng không — nhận, cân, soi chiếu', uplift: 'Uplift — xác nhận hàng đã bay', 'road-ltl': 'Hàng lẻ — nhận và ghép xe', 'road-border': 'Cửa khẩu — mốc qua biên giới' };
  const save = () => {
    if (!Object.keys(draft).length) { setError('Chưa thay đổi trường nào.'); return; }
    const requestId = `SEA-${crypto.randomUUID()}`;
    setError(''); setPending(requestId);
    if (!dispatch('shipment_sea_facts_save', { shipmentId: s.id, fields: draft, requestId, expectedVersion })) {
      setPending(''); setError('Chưa kết nối backend.');
    }
  };
  return <section className="rounded-2xl border bg-white p-4 space-y-3" data-testid="sea-export-facts">
    <h3 className="font-extrabold text-[#0f2a4a]">{TITLES[stageId] ?? 'Ghi nhận bằng chứng'}</h3>
    <p className="text-sm text-slate-500">Tệp đã tải lên không tự xác nhận hãng tàu đã nhận hoặc chấp nhận. Chỉ ghi trạng thái có bằng chứng.</p>
    {(() => { const renderField = (f: typeof fields[number]) => <Field key={f.key} label={f.label}>
      {f.kind === 'status' ? <select aria-label={f.label} disabled={!canEdit || loading || !node?.owned} className={inputCls()} value={draft[f.key] ?? s.journey?.seaFacts[f.key] ?? 'UNKNOWN'} onChange={e => setDraft(d => ({ ...d, [f.key]: e.target.value }))}>
        {(f.options ?? []).map(o => <option key={o.value} value={o.value}>{o.label}</option>)}</select> :
        <input aria-label={f.label} type="text" placeholder={f.kind === 'text' ? f.label : f.kind === 'number' ? 'Để trống nếu chưa biết' : 'YYYY-MM-DD hoặc YYYY-MM-DDTHH:mm'} disabled={!canEdit || loading || !node?.owned} className={inputCls()} value={draft[f.key] ?? s.journey?.seaFacts[f.key] ?? ''} onChange={e => setDraft(d => ({ ...d, [f.key]: e.target.value }))} />}
    </Field>;
      const primary = fields.filter(f => !f.secondary), extra = fields.filter(f => f.secondary);
      return <>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">{primary.map(renderField)}</div>
        {extra.length > 0 && <details className="rounded-lg border border-slate-200 p-3" data-testid="fact-fields-secondary"><summary className="cursor-pointer text-sm font-bold text-slate-600">Chi tiết phụ ({extra.length})</summary><div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-3">{extra.map(renderField)}</div></details>}
      </>; })()}
    <button type="button" data-testid="sea-export-facts-save" disabled={!canEdit || loading || !node?.owned || saved} onClick={save} className="touch-target rounded-lg bg-[#0f2a4a] px-4 py-2 font-bold text-white disabled:opacity-50">{loading ? 'Đang chờ đọc lại…' : saved ? 'Đã xác nhận từ backend' : 'Lưu mốc có bằng chứng'}</button>
    {!canEdit && <p className="text-sm text-slate-500">Tài khoản hiện tại chỉ đọc thông tin này.</p>}
    {(error || outcome?.error) && <p role="alert" className="text-sm text-red-700">{error || outcome?.error}</p>}
  </section>;
}
