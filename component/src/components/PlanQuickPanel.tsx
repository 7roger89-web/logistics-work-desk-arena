import { AlertCircle, ArrowRight, CheckCircle2, Clock, FileText, Info } from 'lucide-react';
import { Link } from 'react-router-dom';
import type { PlanItem, PlanNode, Shipment } from '../lib/viewmodel';
import { cx } from '../lib/format';
import { JOURNEY_META, JourneyStatus, type PlanJourneyNode } from './JourneyMap';

/**
 * Issue #244 — Node 00 KẾ HOẠCH quick panel.
 *
 * Three compact rows (Báo giá → Hợp đồng với khách → Tạm ứng tiền hàng) plus the
 * ONE "Đang thiếu gì / cần làm gì tiếp?" answer, and a CTA into the writer that
 * already exists. This panel creates no writer, no payment, no signature and no
 * debt:
 *
 * - `plan` is server-built (`core.shipment_plan`) and every value is rendered
 *   verbatim; the browser never re-derives a status.
 * - `Đã ký` is never rendered: the contract row shows the recorded signature
 *   state (`Đã có xác nhận ký` only when the backend found evidence) and always
 *   tells the operator that a linked contract is not a signed one.
 * - `RECEIVED` is unreachable on the server, so no money can be shown as paid.
 */
const ITEM_ICON = {
  quotation: FileText,
  customer_contract: FileText,
  customer_advance: Info,
} as const;

const ROW_STATE_CLS: Record<string, string> = {
  LINKED: 'border-emerald-200 bg-emerald-50 text-emerald-900',
  ATTESTED: 'border-emerald-200 bg-emerald-50 text-emerald-900',
  UNVERIFIED: 'border-amber-300 bg-amber-50 text-amber-950',
  MODE_UNKNOWN: 'border-slate-300 bg-slate-50 text-slate-800',
  NOT_APPLICABLE: 'border-slate-300 bg-slate-100 text-slate-700',
  MISSING: 'border-red-300 bg-red-50 text-red-900',
  AMBIGUOUS: 'border-red-300 bg-red-50 text-red-900',
  UNRESOLVED: 'border-red-300 bg-red-50 text-red-900',
};

function rowClass(item: PlanItem) {
  if (item.id === 'customer_contract') {
    return ROW_STATE_CLS[item.signature === 'ATTESTED' ? 'ATTESTED' : 'UNVERIFIED'] ?? ROW_STATE_CLS.UNVERIFIED;
  }
  return ROW_STATE_CLS[item.state] ?? ROW_STATE_CLS.MODE_UNKNOWN;
}

function RowCta({ item, onOpenFinance }: { item: PlanItem; onOpenFinance: () => void }) {
  const label = item.actionLabel || 'Mở';
  const cls = 'touch-target mt-1.5 inline-flex min-h-[44px] items-center justify-center gap-1.5 rounded-lg border-2 border-slate-300 bg-white px-3 text-[13px] font-extrabold text-[#0f2a4a]';
  if (item.targetRoute) {
    return <Link to={item.targetRoute} data-testid={`plan-item-cta-${item.id}`} className={cls}>{label} <ArrowRight size={14} aria-hidden="true" /></Link>;
  }
  return <button type="button" onClick={onOpenFinance} data-testid={`plan-item-cta-${item.id}`} className={cls}>{label} <ArrowRight size={14} aria-hidden="true" /></button>;
}

export default function PlanQuickPanel({ shipment: s, plan, onOpenFinance, onClose }: {
  shipment: Shipment; plan: PlanNode; onOpenFinance: () => void; onClose: () => void;
}) {
  const meta = JOURNEY_META[(plan.state === 'COMPLETED' ? 'COMPLETED' : plan.state === 'PROBLEM' ? 'PROBLEM' : 'WAITING')];
  const StateIcon = plan.state === 'COMPLETED' ? CheckCircle2 : plan.state === 'PROBLEM' ? AlertCircle : Clock;
  return <div className="flex h-full min-h-0 flex-col bg-white" data-testid="plan-quick-panel" data-plan-state={plan.state}>
    <div className={cx('shrink-0 border-b-4 bg-white px-4 pb-3 pt-3', plan.state === 'PROBLEM' ? 'border-red-600' : plan.state === 'COMPLETED' ? 'border-emerald-500' : 'border-slate-300')}>
      <div className="flex items-start justify-between gap-2">
        <div className="text-[10.5px] font-bold uppercase tracking-widest text-slate-500">Node 00 · {s.id}</div>
        <button type="button" onClick={onClose} aria-label="Đóng Node 00" data-testid="plan-panel-close" className="touch-target -mr-1 -mt-1 rounded px-1 text-lg text-slate-400">✕</button>
      </div>
      <div className="flex flex-wrap items-center gap-2">
        <h3 className="text-[22px] font-black tracking-tight text-slate-900">00 · {plan.label}</h3>
        <span className={cx('inline-flex items-center gap-1 rounded-lg border-2 px-2 py-0.5 text-[11.5px] font-extrabold', meta.cls)} data-testid="plan-state-badge">
          <StateIcon size={13} aria-hidden="true" />{meta.label}
        </span>
      </div>
      <p className="mt-0.5 text-[13px] font-semibold text-slate-700">{plan.evidence}</p>
    </div>

    <div className="min-h-0 flex-1 space-y-3 overflow-auto px-4 py-3" data-testid="plan-scroll-region">
      <section data-testid="plan-next-actions">
        <p className="mb-1 text-[10.5px] font-bold uppercase tracking-widest text-slate-500">Đang thiếu gì / cần làm gì tiếp?</p>
        {plan.nextActions.length === 0
          ? <p className="rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-[13px] font-semibold text-emerald-900">Không còn việc nào từ các nguồn hiện có.</p>
          : <ul className="space-y-1.5">{plan.nextActions.map((action, index) => (
            <li key={`${index}-${action}`} className="flex items-start gap-2 rounded-lg border border-amber-300 bg-amber-50 px-3 py-2 text-[13px] font-semibold text-amber-950">
              <span className="mt-0.5 shrink-0 font-black" aria-hidden="true">›</span><span>{action}</span>
            </li>
          ))}</ul>}
      </section>

      <section>
        <p className="mb-1 text-[10.5px] font-bold uppercase tracking-widest text-slate-500">Ba mục kế hoạch</p>
        <div className="space-y-2">
          {plan.items.map((item, index) => {
            const Icon = ITEM_ICON[item.id as keyof typeof ITEM_ICON] ?? Info;
            return <article key={item.id} data-testid={`plan-item-${item.id}`} data-item-state={item.state} data-signature={item.signature ?? ''}
              className={cx('rounded-xl border-2 p-2.5', rowClass(item))}>
              <div className="flex items-start gap-2">
                <span className="grid h-6 w-6 shrink-0 place-items-center rounded-full bg-white/70 text-[11px] font-black" aria-hidden="true">{index + 1}</span>
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-1.5">
                    <p className="text-[13.5px] font-extrabold">{item.label}</p>
                    <span className="inline-flex items-center gap-1 rounded border border-current/30 bg-white/70 px-1.5 py-0.5 text-[11px] font-extrabold">
                      <Icon size={11} aria-hidden="true" />{item.stateLabel}
                    </span>
                  </div>
                  <p className="mt-1 text-[12.5px] leading-snug">{item.detail}</p>
                  {item.id === 'customer_contract' && item.signatureLabel && (
                    <p data-testid="plan-signature-state" data-signature={item.signature ?? ''}
                      className="mt-1 w-fit rounded border border-current/30 bg-white/70 px-1.5 py-0.5 text-[11px] font-extrabold">
                      {item.signatureLabel}
                    </p>
                  )}
                  {item.id === 'customer_advance' && (item.reconcileCount ?? 0) > 0 && (
                    <p className="mt-1 text-[12px] font-bold">Có khoản thu cần đối soát — chưa kết luận tiền hàng đã thanh toán.</p>
                  )}
                  {item.id === 'customer_contract' && item.signature !== 'ATTESTED' && (
                    <p className="mt-1 text-[11.5px] font-semibold opacity-90">Hợp đồng đã link hoặc chứng từ PDF đã tạo không đồng nghĩa đã ký.</p>
                  )}
                  <RowCta item={item} onOpenFinance={onOpenFinance} />
                </div>
              </div>
            </article>;
          })}
        </div>
      </section>

      <p className="text-[11.5px] text-slate-500">
        Kế hoạch chỉ đọc từ nguồn thực: báo giá gắn đúng lô, hợp đồng khách gắn lô và khoản thu đã được phân loại.
        Không có nghĩa vụ thanh toán nào được tạo từ đây.
      </p>
    </div>
  </div>;
}

export type { PlanJourneyNode };
