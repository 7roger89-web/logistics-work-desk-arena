import { useMemo, useRef, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Menu, Search, Bell, ChevronDown, Package, FileText, Users as UsersIcon, Calculator, X } from 'lucide-react';
import { useAppData, useRole } from '../../lib/dataContext';
import type { Role } from '../../lib/types';

const ROLE_LABEL: Record<Role, string> = { ADMIN: 'Quản trị viên', SUPPORT: 'Nhân viên vận hành', SALE: 'Nhân viên kinh doanh' };

const NOTIFICATIONS = [
  { id: 1, text: 'Lô LO-0307 đang thiếu Export Declaration trước khi qua cửa khẩu Tân Thanh', path: '/lo-hang/LO-0307' },
  { id: 2, text: 'Khách hàng Hoàng Gia vừa chốt báo giá BG-2026-058', path: '/kinh-doanh-bao-gia' },
  { id: 3, text: 'Hợp đồng HDMB-2026-014 đã phát hành thành công', path: '/hop-dong/HDMB-2026-014' },
  { id: 4, text: 'Lô LO-0308 đã giao — cần lập phiếu xuất kho', path: '/lo-hang/LO-0308' },
];

export default function TopHeader({ onOpenDrawer }: { onOpenDrawer: () => void }) {
  const navigate = useNavigate();
  const { role, setRole, userName } = useRole();
  const { shipments, contracts, customers } = useAppData();
  const [query, setQuery] = useState('');
  const [showResults, setShowResults] = useState(false);
  const [showNotif, setShowNotif] = useState(false);
  const [showRole, setShowRole] = useState(false);
  const boxRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function onClickOutside(e: MouseEvent) {
      if (boxRef.current && !boxRef.current.contains(e.target as Node)) setShowResults(false);
    }
    document.addEventListener('mousedown', onClickOutside);
    return () => document.removeEventListener('mousedown', onClickOutside);
  }, []);

  const results = useMemo(() => {
    if (query.trim().length < 1) return null;
    const q = query.toLowerCase();
    return {
      shipments: shipments.filter((s) => s.id.toLowerCase().includes(q) || s.customer.toLowerCase().includes(q)).slice(0, 4),
      contracts: contracts.filter((c) => c.id.toLowerCase().includes(q) || c.agent.toLowerCase().includes(q) || c.company.toLowerCase().includes(q)).slice(0, 4),
      customers: customers.filter((c) => c.name.toLowerCase().includes(q) || c.taxCode.includes(q)).slice(0, 4),
    };
  }, [query, shipments, contracts, customers]);

  const hasResults = results && (results.shipments.length + results.contracts.length + results.customers.length > 0);

  return (
    <header className="sticky top-0 z-[80] bg-white border-b border-border">
      <div className="flex items-center gap-3 px-3 sm:px-5 h-16">
        <button onClick={onOpenDrawer} className="lg:hidden h-10 w-10 flex items-center justify-center rounded-lg hover:bg-slate-100 text-navy-900 shrink-0">
          <Menu size={22} />
        </button>

        <div ref={boxRef} className="relative flex-1 max-w-xl">
          <div className="flex items-center gap-2 bg-slate-100 rounded-xl px-3 h-11">
            <Search size={17} className="text-ink-400 shrink-0" />
            <input
              value={query}
              onChange={(e) => { setQuery(e.target.value); setShowResults(true); }}
              onFocus={() => setShowResults(true)}
              placeholder="Tìm mã lô, khách hàng, hợp đồng, container, báo giá, đại lý..."
              className="bg-transparent flex-1 min-w-0 outline-none text-[14px] placeholder:text-ink-400"
            />
            {query && (
              <button onClick={() => setQuery('')} className="text-ink-400 hover:text-ink-600"><X size={15} /></button>
            )}
          </div>
          {showResults && query && (
            <div className="absolute left-0 right-0 top-[calc(100%+6px)] bg-white rounded-xl border border-border shadow-lg max-h-[70vh] overflow-y-auto">
              {!hasResults && (
                <div className="p-4 text-[14px] text-ink-400">Không tìm thấy kết quả cho "{query}"</div>
              )}
              {results && results.shipments.length > 0 && (
                <div className="p-2">
                  <div className="px-2 py-1 text-[11px] font-bold text-ink-400 flex items-center gap-1.5"><Package size={12} /> LÔ HÀNG</div>
                  {results.shipments.map((s) => (
                    <button key={s.id} onClick={() => { navigate(`/lo-hang/${s.id}`); setShowResults(false); setQuery(''); }} className="w-full text-left px-2 py-2 rounded-lg hover:bg-slate-100 flex flex-col">
                      <span className="text-[14px] font-bold text-navy-900">{s.id}</span>
                      <span className="text-[12.5px] text-ink-600 truncate">{s.customer}</span>
                    </button>
                  ))}
                </div>
              )}
              {results && results.contracts.length > 0 && (
                <div className="p-2 border-t border-border">
                  <div className="px-2 py-1 text-[11px] font-bold text-ink-400 flex items-center gap-1.5"><FileText size={12} /> HỢP ĐỒNG</div>
                  {results.contracts.map((c) => (
                    <button key={c.id} onClick={() => { navigate(`/hop-dong/${c.id}`); setShowResults(false); setQuery(''); }} className="w-full text-left px-2 py-2 rounded-lg hover:bg-slate-100 flex flex-col">
                      <span className="text-[14px] font-bold text-navy-900">{c.id}</span>
                      <span className="text-[12.5px] text-ink-600 truncate">{c.agent} · {c.company}</span>
                    </button>
                  ))}
                </div>
              )}
              {results && results.customers.length > 0 && (
                <div className="p-2 border-t border-border">
                  <div className="px-2 py-1 text-[11px] font-bold text-ink-400 flex items-center gap-1.5"><UsersIcon size={12} /> KHÁCH HÀNG</div>
                  {results.customers.map((c) => (
                    <button key={c.id} onClick={() => { navigate(`/khach-hang/${c.id}`); setShowResults(false); setQuery(''); }} className="w-full text-left px-2 py-2 rounded-lg hover:bg-slate-100 flex flex-col">
                      <span className="text-[14px] font-bold text-navy-900">{c.name}</span>
                      <span className="text-[12.5px] text-ink-600 truncate">MST: {c.taxCode}</span>
                    </button>
                  ))}
                </div>
              )}
              {hasResults && (
                <div className="p-2 border-t border-border">
                  <button onClick={() => { navigate(`/lo-hang?q=${encodeURIComponent(query)}`); setShowResults(false); }} className="w-full flex items-center gap-1.5 justify-center text-[13px] font-semibold text-accent-600 py-2 hover:bg-slate-50 rounded-lg">
                    <Calculator size={13} /> Xem tất cả kết quả liên quan
                  </button>
                </div>
              )}
            </div>
          )}
        </div>

        <div className="flex items-center gap-1.5 sm:gap-2 ml-auto shrink-0">
          <div className="relative">
            <button onClick={() => { setShowNotif((v) => !v); setShowRole(false); }} className="relative h-10 w-10 flex items-center justify-center rounded-lg hover:bg-slate-100 text-navy-900">
              <Bell size={19} />
              <span className="absolute top-2 right-2 h-2 w-2 rounded-full bg-danger-500" />
            </button>
            {showNotif && (
              <div className="absolute right-0 top-[calc(100%+8px)] w-80 bg-white rounded-xl border border-border shadow-lg overflow-hidden">
                <div className="px-4 py-3 border-b border-border font-bold text-[14px] text-navy-900">Thông báo</div>
                {NOTIFICATIONS.map((n) => (
                  <button key={n.id} onClick={() => { navigate(n.path); setShowNotif(false); }} className="w-full text-left px-4 py-3 text-[13.5px] text-ink-600 hover:bg-slate-50 border-b border-border last:border-0 leading-snug">
                    {n.text}
                  </button>
                ))}
              </div>
            )}
          </div>

          <div className="relative">
            <button onClick={() => { setShowRole((v) => !v); setShowNotif(false); }} className="flex items-center gap-2 pl-1.5 pr-2.5 h-10 rounded-lg hover:bg-slate-100">
              <div className="h-8 w-8 rounded-full bg-navy-900 text-white flex items-center justify-center font-bold text-[13px] shrink-0">
                {userName.split(' ').slice(-1)[0][0]}
              </div>
              <div className="hidden md:flex flex-col items-start leading-tight">
                <span className="text-[13px] font-bold text-navy-900">{userName}</span>
                <span className="text-[11px] text-ink-400">{ROLE_LABEL[role]}</span>
              </div>
              <ChevronDown size={15} className="text-ink-400 hidden md:block" />
            </button>
            {showRole && (
              <div className="absolute right-0 top-[calc(100%+8px)] w-64 bg-white rounded-xl border border-border shadow-lg overflow-hidden">
                <div className="px-4 py-2.5 border-b border-border text-[12px] font-bold text-ink-400">CHUYỂN VAI TRÒ (DEMO)</div>
                {(['ADMIN', 'SUPPORT', 'SALE'] as Role[]).map((r) => (
                  <button
                    key={r}
                    onClick={() => { setRole(r); setShowRole(false); }}
                    className={`w-full text-left px-4 py-2.5 text-[13.5px] flex items-center justify-between hover:bg-slate-50 ${role === r ? 'font-bold text-navy-900' : 'text-ink-600'}`}
                  >
                    {ROLE_LABEL[r]}
                    {role === r && <span className="h-2 w-2 rounded-full bg-accent-500" />}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
