import type { ReactNode } from 'react';
import { CheckCircle2, AlertTriangle, XCircle, Info, Circle } from 'lucide-react';

export type BadgeVariant = 'success' | 'warning' | 'danger' | 'info' | 'neutral';

const STYLES: Record<BadgeVariant, string> = {
  success: 'bg-success-50 text-success-600 border-success-500/30',
  warning: 'bg-warning-50 text-warning-600 border-warning-500/30',
  danger: 'bg-danger-50 text-danger-600 border-danger-500/30',
  info: 'bg-accent-500/10 text-accent-600 border-accent-500/30',
  neutral: 'bg-slate-100 text-ink-600 border-slate-300',
};

const ICONS: Record<BadgeVariant, typeof CheckCircle2> = {
  success: CheckCircle2,
  warning: AlertTriangle,
  danger: XCircle,
  info: Info,
  neutral: Circle,
};

export default function Badge({ variant = 'neutral', children, icon = true, className = '' }: { variant?: BadgeVariant; children: ReactNode; icon?: boolean; className?: string }) {
  const Icon = ICONS[variant];
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[13px] font-semibold leading-none whitespace-nowrap ${STYLES[variant]} ${className}`}>
      {icon && <Icon size={13} strokeWidth={2.5} />}
      {children}
    </span>
  );
}
