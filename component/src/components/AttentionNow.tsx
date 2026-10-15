import { Link } from "react-router-dom";
import { ArrowRight, CircleAlert, Clock3, LockKeyhole, ListTodo } from "lucide-react";
import type { AttentionItem } from "../lib/viewmodel";
import { cx } from "../lib/format";

const BAND_META: Record<
  AttentionItem["band"],
  { label: string; cls: string; icon: typeof CircleAlert }
> = {
  BLOCKING: { label: "Chặn", cls: "border-[#C0392B]/30 bg-[#F6DFDB] text-[#8E2F22]", icon: LockKeyhole },
  OVERDUE: { label: "Quá hạn", cls: "border-[#C0392B]/30 bg-[#F6DFDB] text-[#8E2F22]", icon: Clock3 },
  DUE_SOON: { label: "Sắp hạn", cls: "border-[#D97706]/30 bg-[#FBEBD3] text-[#8A5209]", icon: Clock3 },
  ACTION: { label: "Cần làm", cls: "border-[#1D6FA8]/30 bg-[#DCEBFA] text-[#154C79]", icon: ListTodo },
  INFO: { label: "Thông tin", cls: "border-[#C9D4DF] bg-[#E7ECF2] text-[#5B6875]", icon: CircleAlert },
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
          items.length > 0 ? "border-[#C0392B]/25 bg-[#F6DFDB]/45" : "border-[#D6DEE7] bg-white"
        )}
      >
        {items.length === 0 ? (
          <p className="px-3.5 py-2.5 text-[13px] text-[#5B6875]" data-testid="attention-empty">
            {emptyText}
          </p>
        ) : (
          <div className="flex flex-wrap items-center gap-x-2 gap-y-1 px-2.5 py-1.5 sm:gap-x-3 sm:gap-y-1.5 sm:px-3 sm:py-1">
            <span className="inline-flex shrink-0 items-center gap-1 rounded-lg bg-[#C0392B] px-2 py-0.5 sm:px-2.5 sm:py-1.5 text-[12px] font-extrabold text-white">
              <CircleAlert size={13} aria-hidden="true" /> CẦN XỬ LÝ ({items.length})
            </span>
            <div
              className="order-2 w-full min-w-0 sm:order-none sm:w-auto sm:flex-1"
              data-testid={`attention-item-${primary.id}`}
              data-attention-band={primary.band}
              data-attention-source={primary.sourceType}
            >
              <span className="sr-only">{BAND_META[primary.band].label} · {actionLabel(primary)}: </span>
              <p data-testid="attention-primary-action" className="break-words text-[13px] sm:text-[14px] font-extrabold leading-tight sm:leading-snug text-[#8E2F22] sm:truncate">{primary.action}</p>
              {primary.reason && <p className="hidden sm:block break-words text-[12.5px] text-[#8E2F22]/90 sm:truncate">{primary.reason}</p>}
            </div>
            <Link
              to={primary.route}
              data-testid="attention-primary-cta"
              className="btn-press order-1 ml-auto inline-flex shrink-0 items-center gap-1 rounded-lg bg-[#C0392B] hover:bg-[#8E2F22] px-2.5 py-0.5 min-h-[40px] sm:min-h-[38px] sm:px-3.5 text-[12px] sm:text-[13px] font-extrabold text-white sm:order-none sm:ml-0"
            >
              XỬ LÝ <ArrowRight size={13} /><span className="sr-only"> — {actionLabel(primary)}</span>
            </Link>
            {rest.length > 0 && (
              <div className="order-3 flex w-full min-w-0 flex-wrap items-center gap-2 sm:order-none sm:w-auto">
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
                      "inline-flex min-h-[36px] shrink-0 items-center gap-1 rounded-lg border px-2.5 py-1.5 text-[12px] font-bold",
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
