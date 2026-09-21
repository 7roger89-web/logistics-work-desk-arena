import { useEffect, useRef, useState } from "react";
import {
  LayoutDashboard, BellRing, Package, PlusCircle, Truck, Users, Handshake,
  Calculator, FileCheck2, FileText, Wallet, Scale, Building2, BarChart3,
  Search, BookOpen, Languages, ShieldCheck, Menu, X, Bell, CheckCircle2,
  AlertTriangle, OctagonAlert, Info, ChevronRight, ChevronDown, ArrowRight,
  CircleCheck, Clock, CircleAlert, Ban, FileDown, Eye, PenLine, Trash2,
  type LucideIcon,
} from "lucide-react";
import { cx, matchLoose } from "../lib/format";

export const ICONS: Record<string, LucideIcon> = {
  layout: LayoutDashboard,
  alarm: BellRing,
  box: Package,
  plus: PlusCircle,
  truck: Truck,
  users: Users,
  handshake: Handshake,
  calc: Calculator,
  filecheck: FileCheck2,
  filetext: FileText,
  wallet: Wallet,
  scale: Scale,
  building: Building2,
  chart: BarChart3,
  search: Search,
  book: BookOpen,
  lang: Languages,
  shield: ShieldCheck,
};

export function ToneBadge({ tone, children, size = "md" }: { tone: "green" | "amber" | "red" | "blue" | "gray"; children: React.ReactNode; size?: "sm" | "md" }) {
  const map = {
    green: "bg-emerald-50 text-emerald-800 border-emerald-200",
    amber: "bg-amber-50 text-amber-900 border-amber-200",
    red: "bg-red-50 text-red-800 border-red-200",
    blue: "bg-blue-50 text-blue-800 border-blue-200",
    gray: "bg-slate-100 text-slate-700 border-slate-200",
  } as const;
  return (
    <span className={cx("inline-flex items-center gap-1.5 font-semibold border rounded-full whitespace-nowrap", size === "sm" ? "text-[12.5px] px-2.5 py-1" : "text-[13.5px] px-3 py-1.5", map[tone])}>
      {children}
    </span>
  );
}

export function StatusDot({ tone }: { tone: string }) {
  const map: Record<string, string> = { green: "bg-emerald-500", amber: "bg-amber-500", red: "bg-red-500", blue: "bg-blue-500", gray: "bg-slate-400" };
  return <span className={cx("inline-block w-2.5 h-2.5 rounded-full shrink-0", map[tone] ?? "bg-slate-400")} />;
}

export function SectionTitle({ icon, title, sub, right }: { icon?: React.ReactNode; title: string; sub?: string; right?: React.ReactNode }) {
  return (
    <div className="flex items-start justify-between gap-3 mb-3">
      <div className="flex items-start gap-2.5">
        {icon && <span className="mt-0.5 w-9 h-9 rounded-xl bg-[#0f2a4a] text-white grid place-items-center shrink-0">{icon}</span>}
        <div>
          <h2 className="text-[17px] md:text-[19px] font-800 font-extrabold text-[#0f2a4a] leading-tight">{title}</h2>
          {sub && <p className="text-[13.5px] text-slate-500 mt-0.5">{sub}</p>}
        </div>
      </div>
      {right}
    </div>
  );
}

export function Field({ label, required, hint, error, children }: { label: string; required?: boolean; hint?: string; error?: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="block text-[14px] font-semibold text-slate-700 mb-1.5">
        {label} {required && <span className="text-red-600 font-bold">*</span>}
      </span>
      {children}
      {hint && !error && <span className="block text-[13px] text-slate-500 mt-1">{hint}</span>}
      {error && <span className="block text-[13.5px] text-red-700 font-medium mt-1">⚠ {error}</span>}
    </label>
  );
}

export const inputCls = (state?: "ok" | "missing" | "invalid") =>
  cx(
    "w-full rounded-xl border-2 bg-white px-3.5 text-[15.5px] min-h-[48px] py-2.5 placeholder:text-slate-400 transition-colors",
    state === "missing" && "border-amber-400 bg-amber-50/60",
    state === "invalid" && "border-red-400 bg-red-50/60",
    (!state || state === "ok") && "border-slate-200 focus:border-[#1e5aa8]"
  );

export function PrimaryBtn({ children, onClick, className, disabled, testId }: { children: React.ReactNode; onClick?: () => void; className?: string; disabled?: boolean; testId?: string }) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      {...(testId ? { "data-testid": testId } : {})}
      className={cx("btn-press touch-target inline-flex items-center justify-center gap-2 rounded-xl bg-[#0f2a4a] hover:bg-[#14365e] text-white font-bold text-[15.5px] px-5 min-h-[48px] shadow-md shadow-navy-900/20 disabled:opacity-50 disabled:cursor-not-allowed", className)}
    >
      {children}
    </button>
  );
}

export function SuccessBtn({ children, onClick, className, disabled, testId }: { children: React.ReactNode; onClick?: () => void; className?: string; disabled?: boolean; testId?: string }) {
  return (
    <button onClick={onClick} disabled={disabled} {...(testId ? { "data-testid": testId } : {})} className={cx("btn-press touch-target inline-flex items-center justify-center gap-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-[15.5px] px-5 min-h-[48px] shadow-md shadow-emerald-600/25 disabled:opacity-50 disabled:cursor-not-allowed", className)}>
      {children}
    </button>
  );
}

export function GhostBtn({ children, onClick, className, danger, disabled, testId }: { children: React.ReactNode; onClick?: () => void; className?: string; danger?: boolean; disabled?: boolean; testId?: string }) {
  return (
    <button onClick={onClick} disabled={disabled} {...(testId ? { "data-testid": testId } : {})} className={cx("btn-press touch-target inline-flex items-center justify-center gap-2 rounded-xl border-2 font-semibold text-[15px] px-4 min-h-[48px] bg-white disabled:opacity-50 disabled:cursor-not-allowed", danger ? "border-red-200 text-red-700 hover:bg-red-50" : "border-slate-200 text-[#0f2a4a] hover:bg-slate-50", className)}>
      {children}
    </button>
  );
}

export function NextActionBanner({ tone = "amber", title, desc, action, onAction }: { tone?: "amber" | "red" | "green" | "blue"; title: string; desc?: string; action?: string; onAction?: () => void }) {
  const styles = {
    amber: "border-amber-300 bg-gradient-to-r from-amber-50 to-orange-50/60",
    red: "border-red-300 bg-gradient-to-r from-red-50 to-orange-50/60",
    green: "border-emerald-300 bg-gradient-to-r from-emerald-50 to-teal-50/60",
    blue: "border-blue-300 bg-gradient-to-r from-blue-50 to-indigo-50/60",
  } as const;
  const Icon = tone === "red" ? OctagonAlert : tone === "green" ? CircleCheck : tone === "blue" ? Info : AlertTriangle;
  const iconBg = tone === "red" ? "bg-red-600" : tone === "green" ? "bg-emerald-600" : tone === "blue" ? "bg-blue-600" : "bg-amber-500";
  return (
    <div className={cx("rounded-2xl border-2 p-4 md:p-5 flex flex-col md:flex-row md:items-center gap-3 md:gap-4", styles[tone])}>
      <div className="flex items-start gap-3 flex-1 min-w-0">
        <span className={cx("w-11 h-11 rounded-xl text-white grid place-items-center shrink-0", iconBg)}><Icon size={22} /></span>
        <div className="min-w-0">
          <p className="text-[12.5px] font-bold uppercase tracking-wide text-slate-500">Việc tiếp theo</p>
          <p className="text-[16px] md:text-[18px] font-extrabold text-[#0f2a4a] leading-snug">{title}</p>
          {desc && <p className="text-[14px] text-slate-600 mt-1">{desc}</p>}
        </div>
      </div>
      {action && (
        <button onClick={onAction} className="btn-press touch-target shrink-0 inline-flex items-center justify-center gap-2 rounded-xl bg-[#0f2a4a] text-white font-bold text-[15.5px] px-6 min-h-[52px] shadow-lg w-full md:w-auto">
          {action} <ArrowRight size={18} />
        </button>
      )}
    </div>
  );
}

export function MissingBox({ what, where, actionLabel, onAction }: { what: string; where?: string; actionLabel: string; onAction?: () => void }) {
  return (
    <div className="rounded-xl border-2 border-dashed border-amber-400 bg-amber-50 p-3.5 flex flex-col sm:flex-row sm:items-center gap-2.5">
      <div className="flex items-start gap-2 flex-1">
        <CircleAlert size={20} className="text-amber-600 shrink-0 mt-0.5" />
        <div>
          <p className="font-bold text-[15px] text-amber-900">Thiếu {what}</p>
          {where && <p className="text-[13.5px] text-amber-800">{where}</p>}
        </div>
      </div>
      <button onClick={onAction} className="btn-press touch-target inline-flex items-center justify-center gap-1.5 rounded-lg bg-amber-500 hover:bg-amber-600 text-white text-[14.5px] font-bold px-4 min-h-[44px] whitespace-nowrap">
        <PenLine size={16} /> {actionLabel}
      </button>
    </div>
  );
}

// ============================================================================
// LOGI_FRONTEND_WORKFLOW_OVERHAUL_01 — ONE accessible sheet/modal shell for
// the critical write overlays (payment, payment correction, delivery
// confirmation, quick add). Existing stack only: a small wrapper around the
// markup every sheet already used, adding the deterministic semantics the
// sheets were missing:
//
//   * role="dialog" + aria-modal + aria-labelledby (visible heading);
//   * useful initial focus (first field/control, else the panel);
//   * focus returns to the opener when the sheet unmounts;
//   * Escape closes — EXCEPT while `pending` (an outcome in flight must not
//     be dismissed by accident) ;
//   * backdrop click closes on the same pending rule;
//   * minimal focus trap so keyboard Tab stays inside the sheet.
//
// No UI framework, no portal, no animation library — the same fixed overlay
// the donor shell already rendered, now with real dialog semantics.
// ============================================================================
export function SheetDialog({
  id, labelledBy, onClose, pending, children, testId, width = 480,
}: {
  /** Stable DOM id for the overlay wrapper (tests + anchors). */
  id?: string;
  /** DOM id of the visible heading that names this dialog. */
  labelledBy: string;
  /** Close request. Ignored by the shell while `pending` is true. */
  onClose: () => void;
  /** True while a write outcome is in flight: Esc/backdrop must not dismiss. */
  pending?: boolean;
  children: React.ReactNode;
  testId?: string;
  width?: number;
}) {
  const panelRef = useRef<HTMLDivElement>(null);

  // LOGI_FRONTEND_WORKFLOW_OVERHAUL_01 visual-gate repair:
  // Components v2 renders inside an OPEN ShadowRoot. document.activeElement
  // therefore resolves only to the component HOST, not the focused control
  // inside the app. Capture/restore focus from the panel's own root so the
  // opener is the actual button the operator used.
  useEffect(() => {
    const panel = panelRef.current;
    if (!panel) return undefined;
    const root = panel.getRootNode() as Document | ShadowRoot;
    const opener = root.activeElement as HTMLElement | null;
    const first = panel.querySelector<HTMLElement>(
      "input:not([disabled]), select:not([disabled]), textarea:not([disabled]), button:not([disabled])"
    );
    (first ?? panel).focus();
    return () => {
      if (opener?.isConnected) opener.focus();
    };
  }, []);

  // Native capture listener on the SAME DOM root as the dialog. React's
  // wrapper-level onKeyDown was not sufficient at the final Tab boundary in
  // the real Components-v2 Shadow DOM: focus could escape to the global
  // search field. Capture before the browser's default focus move and keep
  // both Tab directions inside the panel. Escape is handled here too so a
  // pending financial write cannot be dismissed by an outer handler.
  useEffect(() => {
    const panel = panelRef.current;
    if (!panel) return undefined;
    const root = panel.getRootNode() as Document | ShadowRoot;

    const focusables = () => Array.from(
      panel.querySelectorAll<HTMLElement>(
        'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
      )
    );

    const onKey = (raw: Event) => {
      const e = raw as KeyboardEvent;
      if (e.key === "Escape") {
        e.preventDefault();
        e.stopPropagation();
        if (!pending) onClose();
        return;
      }
      if (e.key !== "Tab") return;

      const items = focusables();
      if (items.length === 0) {
        e.preventDefault();
        panel.focus();
        return;
      }

      const first = items[0];
      const last = items[items.length - 1];
      const active = root.activeElement as HTMLElement | null;
      const outside = !active || !panel.contains(active);

      if (e.shiftKey) {
        if (active === first || outside) {
          e.preventDefault();
          last.focus();
        }
      } else if (active === last || outside) {
        e.preventDefault();
        first.focus();
      }
    };

    root.addEventListener("keydown", onKey, true);
    return () => root.removeEventListener("keydown", onKey, true);
  }, [pending, onClose]);

  return (
    <div
      {...(id ? { id } : {})}
      className="fixed inset-0 z-50 flex items-end sm:items-center justify-center"
      {...(testId ? { "data-testid": testId } : {})}
    >
      <div className="absolute inset-0 bg-slate-900/55 anim-fade" aria-hidden="true" onClick={pending ? undefined : onClose} />
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={labelledBy}
        tabIndex={-1}
        className="relative bg-white w-full rounded-t-3xl sm:rounded-3xl p-5 anim-slide-up outline-none"
        style={{ maxWidth: width }}
      >
        {children}
      </div>
    </div>
  );
}

export function StateRow({ label, value, big }: { label: string; value: React.ReactNode; big?: boolean }) {
  return (
    <div className="flex items-start justify-between gap-3 py-2 border-b border-slate-100 last:border-0">
      <span className="text-[13.5px] text-slate-500 font-medium shrink-0 pt-0.5">{label}</span>
      <span className={cx("text-right font-semibold text-slate-800", big ? "text-[17px]" : "text-[14.5px]")}>{value}</span>
    </div>
  );
}

export { Menu, X, Bell, CheckCircle2, ChevronRight, ChevronDown, ArrowRight, Clock, FileDown, Eye, Trash2, Ban, CircleCheck };
export type { LucideIcon };

// ============================================================================
// LOGI_CONTRACT_AND_SHIPMENT_CORE_GAPS_01 — two shared controls the contract
// and shipment desks were missing. Both are presentation only: they never hold
// business truth, they hand a value back to the page, and the page sends ONE
// typed event to the single Python dispatcher.
// ============================================================================

export interface PickerOption {
  id: string;
  label: string;
  sub?: string;
}

/**
 * A visible search-then-select control for one party (customer / company).
 *
 * A bare `<select>` over a real customer master (360+ rows) is not a search:
 * the operator cannot see what matches, so this renders an explicit "Tìm"
 * control, a filter field, the live match count and the picking list. An empty
 * master is stated honestly instead of being silently filled with an option.
 */
export function SearchPicker({
  label, testId, options, selectedId, selectedLabel, placeholder, emptyHint, required, onSelect,
}: {
  label: string;
  testId: string;
  options: PickerOption[];
  selectedId: string;
  selectedLabel?: string;
  placeholder?: string;
  emptyHint?: string;
  required?: boolean;
  onSelect: (id: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const needle = query.trim();
  // LOGI_INTERNAL_UX_SIMPLIFY_01 — diacritic-insensitive, undefined-safe
  // matching (same helper as the desks), so "an phat" finds "An Phát".
  const matched = needle
    ? options.filter((o) => matchLoose([o.id, o.label, o.sub].join(" "), needle))
    : options;

  const pick = (id: string) => {
    onSelect(id);
    setQuery("");
    setOpen(false);
  };

  return (
    <div
      className="rounded-xl border-2 border-slate-200 bg-white p-2.5"
      data-testid={testId}
      data-selected={selectedId || ""}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="text-[12px] font-bold uppercase tracking-wide text-slate-400">
            {label}{required ? " *" : ""}
          </p>
          <p
            className={cx("truncate text-[14.5px] font-semibold mt-0.5", selectedId ? "text-slate-800" : "text-slate-400")}
            data-testid={`${testId}-value`}
          >
            {selectedLabel || selectedId || "— chưa chọn —"}
          </p>
        </div>
        <button
          type="button"
          onClick={() => setOpen((v) => !v)}
          aria-expanded={open}
          className={cx(
            "btn-press touch-target shrink-0 inline-flex items-center gap-1.5 rounded-lg border-2 px-3 min-h-[40px] text-[13px] font-bold",
            open ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 bg-white text-slate-600"
          )}
          data-testid={`${testId}-toggle`}
        >
          <Search size={15} /> {open ? "Đóng" : "Tìm / đổi"}
        </button>
      </div>

      {open && (
        <div className="mt-2.5 space-y-2" data-testid={`${testId}-panel`}>
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={placeholder ?? "Gõ tên hoặc mã để tìm…"}
            className={inputCls()}
            aria-label={`Tìm ${label.toLowerCase()}`}
            data-testid={`${testId}-search`}
          />
          {options.length === 0 ? (
            <p className="rounded-lg bg-amber-50 px-2.5 py-2 text-[13px] font-semibold text-amber-800" data-testid={`${testId}-empty`}>
              {emptyHint ?? "Danh bạ đang trống — chưa có gì để chọn."}
            </p>
          ) : (
            <>
              <p className="text-[12.5px] text-slate-500" data-testid={`${testId}-count`}>
                Thấy <b className="text-[#0f2a4a]">{matched.length}</b>/{options.length}
                {needle ? ` cho “${query.trim()}”` : null}
              </p>
              <div className="max-h-[240px] overflow-y-auto space-y-1" data-testid={`${testId}-list`}>
                {matched.map((option) => (
                  <button
                    key={option.id}
                    type="button"
                    onClick={() => pick(option.id)}
                    className={cx(
                      "btn-press touch-target w-full rounded-lg border-2 px-2.5 py-2 text-left text-[13.5px] font-semibold",
                      option.id === selectedId ? "border-[#0f2a4a] bg-[#eef4fb] text-[#0f2a4a]" : "border-slate-200 bg-white text-slate-700"
                    )}
                    data-testid={`${testId}-option-${option.id}`}
                  >
                    <span className="block truncate">{option.label}</span>
                    <span className="block text-[12px] font-medium text-slate-400">{option.sub ?? option.id}</span>
                  </button>
                ))}
                {matched.length === 0 && (
                  <p className="rounded-lg bg-slate-50 px-2.5 py-2 text-[13px] font-semibold text-slate-500" data-testid={`${testId}-nomatch`}>
                    Không có mục nào khớp “{query.trim()}”.
                  </p>
                )}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}

/**
 * The explicit, operator-controlled PL choice.
 *
 * Three states are possible on purpose: `YES` ("Có PL"), `NO` ("Không cần PL")
 * and `""` (chưa chọn). `""` is rendered as its own honest chip and is what a
 * legacy contract reads back — choosing "Không cần PL" is an action, never a
 * default. The current value is marked so the operator sees what is STORED,
 * not what was last clicked.
 */
export function PlChoice({
  value, onChange, testId, stored,
}: {
  value: string;
  onChange: (next: "YES" | "NO" | "") => void;
  testId: string;
  /** Optional caption of what the backend currently holds. */
  stored?: string;
}) {
  const options: { key: "YES" | "NO" | ""; label: string }[] = [
    { key: "YES", label: "Có PL" },
    { key: "NO", label: "Không cần PL" },
    { key: "", label: "Chưa chọn" },
  ];
  const current = value === "YES" || value === "NO" ? value : "";
  return (
    <div className="space-y-1.5" data-testid={testId}>
      <p className="text-[12px] font-bold uppercase tracking-wide text-slate-400">
        Phụ lục (PL){stored ? ` · đang lưu: ${stored}` : ""}
      </p>
      <div className="flex flex-wrap gap-1.5">
        {options.map((option) => (
          <button
            key={option.key || "unknown"}
            type="button"
            onClick={() => onChange(option.key)}
            aria-pressed={current === option.key}
            className={cx(
              "btn-press touch-target rounded-lg border-2 px-3 min-h-[40px] text-[13.5px] font-bold",
              current === option.key
                ? "border-[#0f2a4a] bg-[#0f2a4a] text-white"
                : "border-slate-200 bg-white text-slate-600"
            )}
            data-testid={`${testId}-${option.key || "unknown"}`}
          >
            {option.label}
          </button>
        ))}
      </div>
    </div>
  );
}
