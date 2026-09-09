import { NavLink } from 'react-router-dom';
import { X, Ship } from 'lucide-react';
import { NAV_GROUPS } from '../../lib/nav';

export default function NavDrawer({ open, onClose }: { open: boolean; onClose: () => void }) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-[110] lg:hidden">
      <div className="absolute inset-0 bg-navy-950/50" onClick={onClose} />
      <div className="absolute left-0 top-0 h-full w-[280px] bg-navy-900 text-white overflow-y-auto no-scrollbar animate-[fadeIn_0.15s_ease-out]">
        <div className="flex items-center justify-between px-5 pt-6 pb-5 border-b border-white/10">
          <div className="flex items-center gap-2.5">
            <div className="h-9 w-9 rounded-xl bg-accent-500 flex items-center justify-center">
              <Ship size={18} strokeWidth={2.5} />
            </div>
            <div className="font-extrabold text-[15px]">LogiDesk</div>
          </div>
          <button onClick={onClose} className="h-9 w-9 flex items-center justify-center rounded-lg hover:bg-white/10">
            <X size={20} />
          </button>
        </div>
        <nav className="px-3 py-4 space-y-5 pb-24">
          {NAV_GROUPS.map((group) => (
            <div key={group.title}>
              <div className="px-2.5 mb-1.5 text-[11px] font-bold tracking-wider text-white/35">{group.title}</div>
              <div className="space-y-0.5">
                {group.items.map((item) => {
                  const Icon = item.icon;
                  return (
                    <NavLink
                      key={item.path}
                      to={item.path}
                      end={item.path === '/'}
                      onClick={onClose}
                      className={({ isActive }) =>
                        `flex items-center gap-3 px-2.5 py-3 rounded-xl text-[15px] font-medium transition-colors ${
                          isActive ? 'bg-white text-navy-900 font-bold' : 'text-white/75 hover:bg-white/10'
                        }`
                      }
                    >
                      <Icon size={19} strokeWidth={2.2} />
                      <span>{item.label}</span>
                    </NavLink>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>
      </div>
    </div>
  );
}
