import { Link } from "react-router-dom";
import { ArrowRight, CircleAlert, Clock3, LockKeyhole, ListTodo } from "lucide-react";
import type { AttentionItem } from "../lib/viewmodel";
import { cx } from "../lib/format";

const BAND_META: Record<AttentionItem["band"], { label: string; cls: string; icon: typeof CircleAlert }> = {
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
        <p className="text-[13.5px] text-slate-500 py-1.5" data-testid="attention-empty">{emptyText}</p>
      ) : (
        <div className="space-y-2">
          {items.map((item) => {
            const meta = item.sourcePriority === "Khan"\n              ? { label: "Gấp", cls: "border-red-200 bg-red-50 text-red-800", icon: CircleAlert }\n              : BAND_META[item.band];\n            const Icon = meta.icon;
            return (
              <article
                key={item.id}
                className="rounded-xl border border-slate-200 bg-white p-3"
                data-testid={`attention-item-${item.id}`}
                data-attention-band={item.band}
                data-attention-source={item.sourceType}
              >
                <div className="flex flex-wrap items-start gap-2">
                  <span className={cx("inline-flex items-center gap-1 rounded-lg border px-2 py-1 text-[11.5px] font-extrabold shrink-0", meta.cls)}>
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
