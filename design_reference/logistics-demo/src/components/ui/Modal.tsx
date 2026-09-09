import type { ReactNode } from 'react';
import { X } from 'lucide-react';

export default function Modal({ open, onClose, title, children, width = 'max-w-lg' }: { open: boolean; onClose: () => void; title: string; children: ReactNode; width?: string }) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-[100] flex items-end sm:items-center justify-center p-0 sm:p-4">
      <div className="absolute inset-0 bg-navy-950/50 backdrop-blur-[2px]" onClick={onClose} />
      <div className={`relative bg-surface w-full ${width} rounded-t-2xl sm:rounded-2xl shadow-xl max-h-[92vh] overflow-y-auto animate-[fadeIn_0.15s_ease-out]`}>
        <div className="sticky top-0 bg-surface flex items-center justify-between px-5 py-4 border-b border-border z-10">
          <h3 className="text-[16px] font-bold text-navy-900">{title}</h3>
          <button onClick={onClose} className="h-9 w-9 flex items-center justify-center rounded-lg hover:bg-slate-100 text-ink-600">
            <X size={18} />
          </button>
        </div>
        <div className="p-5">{children}</div>
      </div>
    </div>
  );
}
