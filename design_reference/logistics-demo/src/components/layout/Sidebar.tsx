import { NavLink } from 'react-router-dom';
import { Ship } from 'lucide-react';
import { NAV_GROUPS } from '../../lib/nav';

export default function Sidebar() {
  return (
    <aside className="hidden lg:flex flex-col w-[268px] shrink-0 bg-navy-900 text-white h-screen sticky top-0 overflow-y-auto no-scrollbar">
      <div className="px-5 pt-6 pb-5 border-b border-white/10">
        <div className="flex items-center gap-2.5">
          <div className="h-10 w-10 rounded-xl bg-accent-500 flex items-center justify-center shrink-0">
            <Ship size={20} strokeWidth={2.5} />
          </div>
          <div className="min-w-0">
            <div className="font-extrabold text-[16px] leading-tight tracking-tight">LogiDesk</div>
            <div className="text-[12px] text-white/50 leading-tight">Bàn điều hành Logistics</div>
          </div>
        </div>
        <span className="inline-block mt-3 text-[10.5px] font-bold tracking-wider bg-warning-500/90 text-navy-950 px-2 py-0.5 rounded-full">PROTOTYPE</span>
      </div>
      <nav className="flex-1 px-3 py-4 space-y-5">
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
                    className={({ isActive }) =>
                      `flex items-center gap-3 px-2.5 py-2.5 rounded-xl text-[14px] font-medium transition-colors ${
                        isActive ? 'bg-white text-navy-900 font-bold shadow-sm' : 'text-white/75 hover:bg-white/10 hover:text-white'
                      }`
                    }
                  >
                    <Icon size={18} strokeWidth={2.2} className="shrink-0" />
                    <span className="truncate">{item.label}</span>
                  </NavLink>
                );
              })}
            </div>
          </div>
        ))}
      </nav>
      <div className="px-4 py-4 border-t border-white/10 text-[12px] text-white/40">
        © 2026 LogiDesk · Bản demo nội bộ
      </div>
    </aside>
  );
}
