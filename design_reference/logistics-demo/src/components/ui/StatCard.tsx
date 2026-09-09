import type { ReactNode } from 'react';

export default function StatCard({ label, value, icon, tone = 'neutral', sub, onClick }: { label: string; value: ReactNode; icon?: ReactNode; tone?: 'neutral' | 'success' | 'warning' | 'danger' | 'info'; sub?: string; onClick?: () => void }) {
  const toneMap: Record<string, string> = {
    neutral: 'text-navy-900 bg-slate-100',
    success: 'text-success-600 bg-success-50',
    warning: 'text-warning-600 bg-warning-50',
    danger: 'text-danger-600 bg-danger-50',
    info: 'text-accent-600 bg-accent-500/10',
  };
  const Comp: 'button' | 'div' = onClick ? 'button' : 'div';
  return (
    <Comp
      onClick={onClick}
      className={`bg-surface rounded-2xl border border-border shadow-sm p-4 text-left w-full ${onClick ? 'hover:border-navy-700/40 hover:shadow-md transition-all cursor-pointer' : ''}`}
    >
      <div className="flex items-start justify-between gap-2">
        <span className="text-[13px] font-medium text-ink-600">{label}</span>
        {icon && <span className={`rounded-lg p-1.5 ${toneMap[tone]}`}>{icon}</span>}
      </div>
      <div className="mt-2 text-[22px] font-extrabold text-navy-900 leading-tight">{value}</div>
      {sub && <div className="mt-1 text-[12.5px] text-ink-400">{sub}</div>}
    </Comp>
  );
}
