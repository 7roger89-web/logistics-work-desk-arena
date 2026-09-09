import type { ButtonHTMLAttributes, ReactNode } from 'react';

type Variant = 'primary' | 'secondary' | 'danger' | 'success' | 'ghost';
type Size = 'md' | 'sm' | 'lg';

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  icon?: ReactNode;
  full?: boolean;
}

const VARIANTS: Record<Variant, string> = {
  primary: 'bg-navy-900 text-white hover:bg-navy-800 active:bg-navy-950 shadow-sm shadow-navy-900/20',
  secondary: 'bg-white text-navy-900 border border-slate-300 hover:bg-slate-50 active:bg-slate-100',
  danger: 'bg-danger-500 text-white hover:bg-danger-600 shadow-sm shadow-danger-500/20',
  success: 'bg-success-500 text-white hover:bg-success-600 shadow-sm shadow-success-500/20',
  ghost: 'bg-transparent text-ink-600 hover:bg-slate-100',
};

const SIZES: Record<Size, string> = {
  sm: 'h-9 px-3 text-[13px] rounded-lg',
  md: 'h-11 px-4 text-[15px] rounded-xl',
  lg: 'h-13 px-6 text-[16px] rounded-xl',
};

export default function Button({ variant = 'primary', size = 'md', icon, full, className = '', children, ...rest }: Props) {
  return (
    <button
      className={`inline-flex items-center justify-center gap-2 font-semibold transition-colors disabled:opacity-40 disabled:cursor-not-allowed whitespace-nowrap ${VARIANTS[variant]} ${SIZES[size]} ${full ? 'w-full' : ''} ${className}`}
      {...rest}
    >
      {icon}
      {children}
    </button>
  );
}
