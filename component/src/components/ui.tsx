import {
  LayoutDashboard, BellRing, Package, PlusCircle, Truck, Users, Handshake,
  Calculator, FileCheck2, FileText, Wallet, Scale, Building2, BarChart3,
  Search, BookOpen, Languages, ShieldCheck, Menu, X, Bell, CheckCircle2,
  AlertTriangle, OctagonAlert, Info, ChevronRight, ChevronDown, ArrowRight,
  CircleCheck, Clock, CircleAlert, Ban, FileDown, Eye, PenLine, Trash2,
  type LucideIcon,
} from "lucide-react";
import { cx } from "../lib/format";

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

export function PrimaryBtn({ children, onClick, className, disabled }: { children: React.ReactNode; onClick?: () => void; className?: string; disabled?: boolean }) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={cx("btn-press touch-target inline-flex items-center justify-center gap-2 rounded-xl bg-[#0f2a4a] hover:bg-[#14365e] text-white font-bold text-[15.5px] px-5 min-h-[48px] shadow-md shadow-navy-900/20 disabled:opacity-50 disabled:cursor-not-allowed", className)}
    >
      {children}
    </button>
  );
}

export function SuccessBtn({ children, onClick, className }: { children: React.ReactNode; onClick?: () => void; className?: string }) {
  return (
    <button onClick={onClick} className={cx("btn-press touch-target inline-flex items-center justify-center gap-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-[15.5px] px-5 min-h-[48px] shadow-md shadow-emerald-600/25", className)}>
      {children}
    </button>
  );
}

export function GhostBtn({ children, onClick, className, danger }: { children: React.ReactNode; onClick?: () => void; className?: string; danger?: boolean }) {
  return (
    <button onClick={onClick} className={cx("btn-press touch-target inline-flex items-center justify-center gap-2 rounded-xl border-2 font-semibold text-[15px] px-4 min-h-[48px] bg-white", danger ? "border-red-200 text-red-700 hover:bg-red-50" : "border-slate-200 text-[#0f2a4a] hover:bg-slate-50", className)}>
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
