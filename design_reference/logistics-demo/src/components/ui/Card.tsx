import type { ReactNode } from 'react';

export default function Card({ children, className = '', padded = true, onClick }: { children: ReactNode; className?: string; padded?: boolean; onClick?: () => void }) {
  return (
    <div onClick={onClick} className={`bg-surface rounded-2xl border border-border shadow-sm ${padded ? 'p-4 sm:p-5' : ''} ${onClick ? 'cursor-pointer' : ''} ${className}`}>
      {children}
    </div>
  );
}

export function CardTitle({ children, className = '' }: { children: ReactNode; className?: string }) {
  return <h3 className={`text-[15px] font-bold text-navy-900 mb-3 flex items-center gap-2 ${className}`}>{children}</h3>;
}

export function Field({ label, value, required, missing }: { label: string; value: ReactNode; required?: boolean; missing?: boolean }) {
  return (
    <div>
      <div className="text-[12.5px] font-medium text-ink-400 mb-1">{label}{required && <span className="text-danger-500">*</span>}</div>
      <div className={`text-[15px] font-semibold ${missing ? 'text-warning-600' : 'text-ink-900'}`}>{value || (missing ? '— Chưa có —' : '—')}</div>
    </div>
  );
}
