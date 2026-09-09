import type { ReactNode } from 'react';
import { Inbox } from 'lucide-react';

export default function EmptyState({ message, action, icon }: { message: string; action?: ReactNode; icon?: ReactNode }) {
  return (
    <div className="flex flex-col items-center justify-center text-center py-12 px-4">
      <div className="rounded-full bg-slate-100 text-ink-400 p-4 mb-4">{icon || <Inbox size={28} />}</div>
      <p className="text-[15px] font-medium text-ink-600 max-w-sm mb-4">{message}</p>
      {action}
    </div>
  );
}
