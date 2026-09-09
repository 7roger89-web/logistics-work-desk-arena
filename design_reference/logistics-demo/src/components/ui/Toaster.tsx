import { CheckCircle2, AlertTriangle, XCircle, Info, X } from 'lucide-react';
import { useToast } from '../../lib/dataContext';

const ICONS = { success: CheckCircle2, warning: AlertTriangle, danger: XCircle, info: Info };
const STYLES = {
  success: 'bg-navy-900 text-white',
  warning: 'bg-warning-600 text-white',
  danger: 'bg-danger-600 text-white',
  info: 'bg-accent-600 text-white',
};

export default function Toaster() {
  const { toasts, dismiss } = useToast();
  return (
    <div className="fixed z-[200] bottom-20 lg:bottom-6 left-1/2 -translate-x-1/2 lg:left-auto lg:right-6 lg:translate-x-0 flex flex-col gap-2 w-[92vw] max-w-sm">
      {toasts.map((t) => {
        const Icon = ICONS[t.variant];
        return (
          <div key={t.id} className={`flex items-center gap-2.5 rounded-xl px-4 py-3 shadow-lg text-[14px] font-semibold ${STYLES[t.variant]}`}>
            <Icon size={18} className="shrink-0" />
            <span className="flex-1">{t.message}</span>
            <button onClick={() => dismiss(t.id)} className="opacity-70 hover:opacity-100"><X size={16} /></button>
          </div>
        );
      })}
    </div>
  );
}
