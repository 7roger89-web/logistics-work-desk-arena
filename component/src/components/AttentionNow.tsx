import { Link } from "react-router-dom";
import { ArrowRight, CircleAlert, Clock3, LockKeyhole, ListTodo } from "lucide-react";
import type { AttentionItem } from "../lib/viewmodel";
import { cx } from "../lib/format";

const BAND_META: Record<
  AttentionItem["band"],
  { label: string; cls: string; icon: typeof CircleAlert }
> = {
  BLOCKING: { label: "Chặn", cls: "border-red-200 bg-red-50 text-red-800", icon: LockKeyhole },
  OVERDUE: { label: "Quá hạn", cls: "border-red-200 bg-red-50 text-red-800", icon: Clock3 },
  DUE_SOON: { label: "Sắp hạn", cls: "border-amber-200 bg-amber-50 text-amber-900", icon: Clock3 },
  ACTION: { label: "Cần làm", cls: "border-blue-200 bg-blue-50 text-blue-800", icon: ListTodo },
  INFO: { label: "Thông tin", cls: "border-slate-200 bg-slate-50 text-slate-700", icon: CircleAlert },
};

function actionLabel(item: AttentionItem): string {
  if (item.sourceType === "WORK_MODULE") return "Mở quy trình";
  if (item.sourceType === "TASK") return "Mở việc";
  return "Mở xử lý";
}

export default function AttentionNow({
  items,
  title = "Cần xử lý",
  emptyText = "Chưa có việc cần xử lý theo dữ liệu hiện có.",
  compact = false,
}: {
  items: AttentionItem[];
  title?: string;
  emptyText?: string;
  compact?: boolean;
}) {
  // Issue #190 — the Owner reference renders the shipment attention state as
  // ONE tinted single-row band: [CẦN XỬ LÝ (n)] title+reason · [XỬ LÝ →] ·
  // "ĐIỂM CHÚ Ý KHÁC" chips. The card list stays for surfaces that need the
  // full per-item detail (Home); the shipment Journey path uses this band so
  // the work below starts at the same rhythm as the reference.
  if (compact) {
    const [primary, ...rest] = items;
    return (
      <section
        data-testid="attention-now"
        data-attention-layout="compact"
        className={cx(
          "rounded-xl border",
          items.length > 0 ? "border-red-200 bg-[#f8f3f5]" : "border-slate-200 bg-white"
        )}
      >
        {items.length === 0 ? (
          <p className="px-3.5 py-2.5 text-[13px] text-slate-500" data-testid="attention-empty">
            {emptyText}
          </p>
        ) : (
          <div className="flex flex-wrap items-center gap-x-3 gap-y-1.5 px-3 py-1">
            <span className="inline-flex shrink-0 items-center gap-1.5 rounded-lg bg-red-600 px-2.5 py-1.5 text-[12px] font-extrabold text-white">
              <CircleAlert size={14} aria-hidden="true" /> CẦN XỬ LÝ ({items.length})
            </span>
            <div
              className="min-w-0 flex-1"
              data-testid={`attention-item-${primary.id}`}
              data-attention-band={primary.band}
              data-attention-source={primary.sourceType}
            >
              <span className="sr-only">{BAND_META[primary.band].label} · {actionLabel(primary)}: </span>
              <p className="truncate text-[14px] font-extrabold text-red-700">{primary.action}</p>
              {primary.reason && <p className="truncate text-[12.5px] text-red-600">{primary.reason}</p>}
            </div>
            <Link
              to={primary.route}
              className="btn-press touch-target inline-flex shrink-0 items-center gap-1.5 rounded-lg bg-red-600 px-3.5 text-[13px] font-extrabold text-white"
              style={{ minHeight: 38 }}
            >
              XỬ LÝ <ArrowRight size={14} /><span className="sr-only"> — {actionLabel(primary)}</span>
            </Link>
            {rest.length > 0 && (
              <div className="flex min-w-0 flex-wrap items-center gap-2">
                <span className="shrink-0 text-[12px] font-extrabold tracking-wide text-slate-500">
                  ĐIỂM CHÚ Ý KHÁC
                </span>
                {rest.map((item) => (
                  <Link
                    key={item.id}
                    to={item.route}
                    data-testid={`attention-item-${item.id}`}
                    data-attention-band={item.band}
                    data-attention-source={item.sourceType}
                    className={cx(
                      "inline-flex shrink-0 items-center gap-1 rounded-lg border px-2.5 py-1.5 text-[12px] font-bold",
                      BAND_META[item.band].cls
                    )}
                  >
                    {item.action}<span className="sr-only"> · {BAND_META[item.band].label} · {actionLabel(item)}</span>
                  </Link>
                ))}
              </div>
            )}
          </div>
        )}
      </section>
    );
  }
  return (
    <section
      className={cx("rounded-2xl bg-white border border-slate-200", compact ? "p-3.5" : "p-4 md:p-5")}
      data-testid="attention-now"
    >
      <div className="flex items-center justify-between gap-2 mb-2.5">
        <h2 className="font-extrabold text-[16px] text-[#0f2a4a] inline-flex items-center gap-2">
          <CircleAlert size={18} className="text-[#1e5aa8]" aria-hidden="true" />
          {title}
        </h2>
        {items.length > 0 && (
          <span className="text-[12px] font-bold text-slate-400">{items.length} mục</span>
        )}
      </div>

      {items.length === 0 ? (
        <p className="text-[13.5px] text-slate-500 py-1.5" data-testid="attention-empty">
          {emptyText}
        </p>
      ) : (
        <div className="space-y-2">
          {items.map((item) => {
            const meta =
              item.sourcePriority === "Khan"
                ? { label: "Gấp", cls: "border-red-200 bg-red-50 text-red-800", icon: CircleAlert }
                : BAND_META[item.band];
            const Icon = meta.icon;
            return (
              <article
                key={item.id}
                className="rounded-xl border border-slate-200 bg-white p-3"
                data-testid={`attention-item-${item.id}`}
                data-attention-band={item.band}
                data-attention-source={item.sourceType}
              >
                <div className="flex flex-wrap items-start gap-2">
                  <span className={cx(
                    "inline-flex items-center gap-1 rounded-lg border px-2 py-1 text-[12px] font-extrabold shrink-0",
                    meta.cls
                  )}>
                    <Icon size={13} aria-hidden="true" /> {meta.label}
                  </span>
                  <div className="flex-1 min-w-[220px]">
                    <p className="font-extrabold text-[14px] text-[#0f2a4a]">{item.action}</p>
                    {item.reason && <p className="text-[12.5px] text-slate-600 mt-0.5">{item.reason}</p>}
                    <div className="mt-1.5 flex flex-wrap gap-x-3 gap-y-1 text-[12px] text-slate-500">
                      {item.owner && <span>Phụ trách: <b className="text-slate-700">{item.owner}</b></span>}
                      {item.deadline && <span>Hạn: <b className="text-slate-700">{item.deadline}</b></span>}
                      {item.blockedGate && <span>Chặn: <b className="text-red-700">{item.blockedGate}</b></span>}
                      {item.context && <span>{item.context}</span>}
                      {item.unknown && <span className="font-semibold">Chưa xác định đủ dữ liệu</span>}
                    </div>
                  </div>
                  <Link
                    to={item.route}
                    className="btn-press touch-target shrink-0 inline-flex items-center gap-1.5 rounded-lg bg-[#0f2a4a] text-white text-[13px] font-bold px-3 min-h-[40px]"
                  >
                    {actionLabel(item)} <ArrowRight size={14} />
                  </Link>
                </div>
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}
