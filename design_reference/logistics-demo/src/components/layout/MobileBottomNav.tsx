import { NavLink } from 'react-router-dom';
import { MoreHorizontal } from 'lucide-react';
import { MOBILE_NAV } from '../../lib/nav';

export default function MobileBottomNav({ onMore }: { onMore: () => void }) {
  return (
    <nav className="lg:hidden fixed bottom-0 left-0 right-0 z-[90] bg-white border-t border-border flex items-stretch h-16 pb-[env(safe-area-inset-bottom)]">
      {MOBILE_NAV.map((item) => {
        const Icon = item.icon;
        return (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.path === '/'}
            className={({ isActive }) =>
              `flex-1 flex flex-col items-center justify-center gap-0.5 text-[11px] font-semibold ${
                isActive ? 'text-navy-900' : 'text-ink-400'
              }`
            }
          >
            {({ isActive }) => (
              <>
                <Icon size={20} strokeWidth={isActive ? 2.5 : 2} />
                {item.label}
              </>
            )}
          </NavLink>
        );
      })}
      <button onClick={onMore} className="flex-1 flex flex-col items-center justify-center gap-0.5 text-[11px] font-semibold text-ink-400">
        <MoreHorizontal size={20} />
        Thêm
      </button>
    </nav>
  );
}
