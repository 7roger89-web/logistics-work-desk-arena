import { contractPath } from "../lib/contractRoute";
import { useMemo, useState } from "react";
import { Link, NavLink, useLocation, useNavigate } from "react-router-dom";
import { Bell, Menu, X, Search, Plus, FileText, Package, Calculator, Wallet, Truck, ChevronRight } from "lucide-react";
import { NAV, ROLE_LABEL, SHIPMENTS, CONTRACTS, CUSTOMERS, QUOTES } from "../lib/data";
import type { Role } from "../lib/data";
import { ICONS, SheetDialog } from "./ui";
import { useStore } from "../lib/store";
import { cx } from "../lib/format";

function Logo({ sandbox }: { sandbox: boolean }) {
  return (
    <Link to="/" className="flex items-center gap-2.5 shrink-0">
      <span className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#1e5aa8] to-[#0a1f3a] grid place-items-center text-white font-extrabold text-[18px] shadow">T</span>
      <span className="leading-tight hidden sm:block">
        <span className="block font-extrabold text-[14.5px] text-[#0f2a4a]">TRƯỜNG THÀNH</span>
        <span className="block text-[11.5px] text-slate-500 font-medium">Phú Anh Logistics · Nội bộ</span>
      </span>
      {/* P2 — the PROTOTYPE chip marks the sandbox/prototype surface; a
          production-like runtime does not carry prototype residue. */}
      {sandbox && <span className="text-[11px] font-extrabold tracking-wider bg-violet-100 text-violet-800 border border-violet-300 rounded-md px-1.5 py-0.5 ml-1">PROTOTYPE</span>}
    </Link>
  );
}

export default function Layout({ children }: { children: React.ReactNode }) {
  const { role, setRole, userName, query, setQuery, searchOpen, setSearchOpen, navOpen, setNavOpen, notifOpen, setNotifOpen, quickAddOpen, setQuickAddOpen, toasts, dismissToast, toast, notifications, tasks, environment } = useStore();
  // Real alerts from the Logistics readiness projection (no fixed demo list).
  const notifs = notifications;
  const notifCount = notifs.length;
  // Real open-work count from the task projection (Khẩn + Cần xử lý) — never
  // the donor's hardcoded sample number.
  const openTaskCount = tasks.filter((t) => t.level === "Khan" || t.level === "CanXuLy").length;
  const nav = useNavigate();
  const loc = useLocation();
  const [roleMenu, setRoleMenu] = useState(false);

  const results = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (q.length < 2) return null;
    const lots = SHIPMENTS.filter((s) => (s.id + s.customer + (s as any).contract + s.route).toLowerCase().includes(q)).slice(0, 4);
    const cts = CONTRACTS.filter((c) => (c.id + c.company + c.agent).toLowerCase().includes(q)).slice(0, 3);
    const cus = CUSTOMERS.filter((c) => (c.name + c.mst).toLowerCase().includes(q)).slice(0, 3);
    const quo = QUOTES.filter((x) => (x.id + x.customer).toLowerCase().includes(q)).slice(0, 2);
    return { lots, cts, cus, quo };
  }, [query]);

  const goSearch = (path: string) => { setSearchOpen(false); setQuery(""); nav(path); setNavOpen(false); };

  return (
    <div className="min-h-screen flex flex-col">
      {/* ===== TOP HEADER ===== */}
      <header className="no-print sticky top-0 z-40 bg-white border-b border-slate-200 shadow-[0_1px_12px_rgba(15,42,74,.08)]">
        <div className="flex items-center gap-2 md:gap-4 px-3 md:px-5 h-[64px] max-w-[1600px] mx-auto">
          <button onClick={() => setNavOpen(true)} className="lg:hidden touch-target w-11 h-11 grid place-items-center rounded-xl hover:bg-slate-100" aria-label="Mở menu">
            <Menu size={22} className="text-[#0f2a4a]" />
          </button>
          <Logo sandbox={environment?.isSandbox === true} />
          {/* search desktop */}
          <div className="hidden md:flex flex-1 max-w-[560px] mx-auto relative">
            <div className="flex items-center w-full rounded-xl border-2 border-slate-200 focus-within:border-[#1e5aa8] bg-slate-50 overflow-hidden">
              <Search size={19} className="ml-3.5 text-slate-400 shrink-0" />
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onFocus={() => setSearchOpen(true)}
                placeholder="Tìm mã lô · khách hàng · hợp đồng · container · báo giá…"
                className="w-full bg-transparent px-3 py-2.5 text-[15px] outline-none placeholder:text-slate-400"
              />
              {query && <button onClick={() => setQuery("")} className="mr-2 w-8 h-8 grid place-items-center rounded-lg hover:bg-slate-200"><X size={16} /></button>}
            </div>
            {searchOpen && results && (
              <div className="absolute top-[52px] left-0 right-0 bg-white rounded-2xl border border-slate-200 shadow-2xl p-2 z-50 anim-slide-up max-h-[70vh] overflow-auto">
                {results.lots.length + results.cts.length + results.cus.length + results.quo.length === 0 && (
                  <p className="p-4 text-[14.5px] text-slate-500">Không tìm thấy “{query}”. Thử lại theo <b>mã lô</b>, <b>tên khách hàng</b> hoặc <b>số hợp đồng</b> đang có trong hệ thống.</p>
                )}
                {results.lots.map((s) => (
                  <button key={s.id} onClick={() => goSearch(`/lo-hang/${s.id}`)} className="w-full text-left px-3 py-2.5 rounded-xl hover:bg-slate-50 flex items-center gap-3">
                    <span className="w-9 h-9 rounded-lg bg-blue-100 grid place-items-center"><Package size={17} className="text-blue-700" /></span>
                    <span><span className="block font-bold text-[14.5px] text-[#0f2a4a]">{s.id} · {s.customer}</span><span className="block text-[12.5px] text-slate-500">Lô hàng — {s.status}</span></span>
                  </button>
                ))}
                {results.cts.map((c) => (
                  <button key={c.id} onClick={() => goSearch(contractPath(c.id))} className="w-full text-left px-3 py-2.5 rounded-xl hover:bg-slate-50 flex items-center gap-3">
                    <span className="w-9 h-9 rounded-lg bg-emerald-100 grid place-items-center"><FileText size={17} className="text-emerald-700" /></span>
                    <span><span className="block font-bold text-[14.5px] text-[#0f2a4a]">{c.id} · {c.company}</span><span className="block text-[12.5px] text-slate-500">Hợp đồng — {c.status}</span></span>
                  </button>
                ))}
                {results.cus.map((c) => (
                  // LOGI_FRONTEND_WORKFLOW_OVERHAUL_01 — no customer detail
                  // route exists, so the destination RECEIVES the entity:
                  // /khach-hang opens with the exact customer already
                  // filtered — never a generic list to search again.
                  <button key={c.mst} onClick={() => goSearch(`/khach-hang?q=${encodeURIComponent(c.name || c.short || c.mst)}`)} className="w-full text-left px-3 py-2.5 rounded-xl hover:bg-slate-50 flex items-center gap-3">
                    <span className="w-9 h-9 rounded-lg bg-amber-100 grid place-items-center"><Truck size={17} className="text-amber-700" /></span>
                    <span><span className="block font-bold text-[14.5px] text-[#0f2a4a]">{c.short} · MST {c.mst}</span><span className="block text-[12.5px] text-slate-500">Khách hàng</span></span>
                  </button>
                ))}
                {results.quo.map((q) => (
                  // Same for quotes: land with the exact quote filtered.
                  <button key={q.id} onClick={() => goSearch(`/kinh-doanh-bao-gia?q=${encodeURIComponent(q.id)}`)} className="w-full text-left px-3 py-2.5 rounded-xl hover:bg-slate-50 flex items-center gap-3">
                    <span className="w-9 h-9 rounded-lg bg-violet-100 grid place-items-center"><Calculator size={17} className="text-violet-700" /></span>
                    <span><span className="block font-bold text-[14.5px] text-[#0f2a4a]">{q.id} · {q.customer}</span><span className="block text-[12.5px] text-slate-500">Báo giá — {q.status}</span></span>
                  </button>
                ))}
                <button onClick={() => setSearchOpen(false)} className="w-full text-center py-2 text-[13px] text-slate-400 font-medium">Nhấn ra ngoài để đóng</button>
              </div>
            )}
          </div>
          <div className="flex-1 md:hidden" />
          {/* mobile search icon */}
          <button onClick={() => setSearchOpen(!searchOpen)} className="md:hidden touch-target w-11 h-11 grid place-items-center rounded-xl hover:bg-slate-100" aria-label="Tìm kiếm">
            <Search size={21} className="text-[#0f2a4a]" />
          </button>
          {/* role switcher — LOGI_FRONTEND_WORKFLOW_OVERHAUL_01 (P1.5):
              the ADMIN/SUPPORT/SALE switcher is a UI-only PREVIEW for the
              sandbox. It never mutates canonical RBAC, so in a normal
              (production-like) runtime it is not rendered at all — the header
              shows only the actual logged-in role. Sandbox keeps the preview,
              visibly labelled as display-only. core/auth.py is untouched. */}
          {environment?.isSandbox ? (
          <div className="relative hidden sm:block" data-testid="role-preview-switcher">
            <button onClick={() => setRoleMenu((v) => !v)} aria-haspopup="menu" aria-expanded={roleMenu} className="flex items-center gap-2 rounded-xl border-2 border-slate-200 pl-1.5 pr-2.5 py-1 hover:border-[#1e5aa8]">
              <span className={cx("w-8 h-8 rounded-lg grid place-items-center text-white text-[13px] font-extrabold", role === "ADMIN" ? "bg-violet-600" : role === "SUPPORT" ? "bg-[#1e5aa8]" : "bg-emerald-600")}>{userName.charAt(0)}</span>
              <span className="text-left leading-tight"><span className="block text-[13px] font-bold text-[#0f2a4a]">{userName}</span><span className="block text-[11.5px] text-slate-500">{ROLE_LABEL[role]} · {role}</span></span>
              <span className="text-[10px] font-extrabold tracking-wider uppercase rounded-md bg-violet-100 text-violet-800 border border-violet-300 px-1.5 py-0.5">Xem trước</span>
            </button>
            {roleMenu && (
              <div className="absolute right-0 top-[52px] w-[260px] bg-white rounded-2xl border shadow-2xl p-2 z-50 anim-slide-up" role="menu" data-testid="role-preview-menu">
                <p className="px-3 pt-2 pb-1 text-[12px] font-bold uppercase tracking-wide text-slate-400">Xem trước giao diện theo vai trò — chỉ thay hiển thị, quyền thật theo tài khoản đăng nhập</p>
                {(["ADMIN", "SUPPORT", "SALE"] as Role[]).map((r) => (
                  <button key={r} role="menuitem" onClick={() => { setRole(r); setRoleMenu(false); toast(`Đang XEM TRƯỚC giao diện ${ROLE_LABEL[r]}`, "Chỉ thay đổi hiển thị trong sandbox — quyền thật vẫn theo tài khoản đăng nhập.", "blue"); }} className={cx("w-full text-left px-3 py-2.5 rounded-xl flex items-center justify-between hover:bg-slate-50", role === r && "bg-blue-50")}>
                    <span><span className="block font-bold text-[14.5px]">{ROLE_LABEL[r]}</span><span className="block text-[12px] text-slate-500">{r}</span></span>
                    {role === r && <span className="text-blue-700 font-bold text-[13px]">● Đang xem</span>}
                  </button>
                ))}
              </div>
            )}
          </div>
          ) : (
          <div className="hidden sm:block" data-testid="actual-role-badge" title="Vai trò của tài khoản đăng nhập">
            <div className="flex items-center gap-2 rounded-xl border-2 border-transparent pl-1.5 pr-2.5 py-1">
              <span className={cx("w-8 h-8 rounded-lg grid place-items-center text-white text-[13px] font-extrabold", role === "ADMIN" ? "bg-violet-600" : role === "SUPPORT" ? "bg-[#1e5aa8]" : "bg-emerald-600")}>{userName.charAt(0)}</span>
              <span className="text-left leading-tight"><span className="block text-[13px] font-bold text-[#0f2a4a]">{userName}</span><span className="block text-[11.5px] text-slate-500">{ROLE_LABEL[role]} · {role}</span></span>
            </div>
          </div>
          )}
          {/* notif */}
          <button onClick={() => setNotifOpen(true)} className="relative touch-target w-11 h-11 grid place-items-center rounded-xl hover:bg-slate-100" aria-label="Thông báo">
            <Bell size={21} className="text-[#0f2a4a]" />
            {notifCount > 0 && <span className="absolute top-1 right-1 min-w-[20px] h-5 px-1 rounded-full bg-red-600 text-white text-[11px] font-extrabold grid place-items-center">{notifCount}</span>}
          </button>
          <button onClick={() => setQuickAddOpen(true)} className="hidden md:inline-flex touch-target items-center gap-1.5 rounded-xl bg-[#0f2a4a] text-white font-bold text-[14.5px] px-4 min-h-[44px] hover:bg-[#14365e]">
            <Plus size={18} /> Thêm
          </button>
        </div>
        {/* mobile search bar expand */}
        {searchOpen && (
          <div className="md:hidden px-3 pb-3 anim-slide-up">
            <div className="flex items-center rounded-xl border-2 border-[#1e5aa8] bg-slate-50">
              <Search size={18} className="ml-3 text-slate-400" />
              <input autoFocus value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Tìm mã lô · khách · hợp đồng…" className="w-full bg-transparent px-2.5 py-3 text-[15px] outline-none" />
              <button onClick={() => { setSearchOpen(false); setQuery(""); }} className="mr-1 w-10 h-10 grid place-items-center"><X size={18} /></button>
            </div>
            {results && (
              <div className="mt-2 bg-white rounded-2xl border shadow-xl divide-y max-h-[50vh] overflow-auto">
                {results.lots.map((s) => (
                  <button key={s.id} onClick={() => goSearch(`/lo-hang/${s.id}`)} className="w-full text-left p-3.5 flex items-center gap-3">
                    <Package size={18} className="text-blue-700 shrink-0" />
                    <span><span className="block font-bold text-[15px]">{s.id} · {s.customer}</span><span className="block text-[13px] text-slate-500">{s.status} — {s.nextAction}</span></span>
                  </button>
                ))}
                {results.cts.map((c) => (
                  <button key={c.id} onClick={() => goSearch(contractPath(c.id))} className="w-full text-left p-3.5 flex items-center gap-3">
                    <FileText size={18} className="text-emerald-700 shrink-0" />
                    <span><span className="block font-bold text-[15px]">{c.id}</span><span className="block text-[13px] text-slate-500">{c.company} — {c.status}</span></span>
                  </button>
                ))}
                {(results.lots.length + results.cts.length === 0) && <p className="p-4 text-[14px] text-slate-500">Không tìm thấy. Thử lại theo mã lô, tên khách hàng hoặc số hợp đồng.</p>}
              </div>
            )}
          </div>
        )}
      </header>

      <div className="flex flex-1 max-w-[1600px] w-full mx-auto">
        {/* ===== SIDEBAR desktop ===== */}
        <aside className="no-print hidden lg:block w-[264px] shrink-0 border-r border-slate-200 bg-white min-h-[calc(100vh-64px)] sticky top-[64px] self-start max-h-[calc(100vh-64px)] overflow-y-auto">
          <nav className="p-3 pb-10">
            {NAV.map((g) => (
              <div key={g.group} className="mb-4">
                <p className="px-3 mb-1.5 text-[11.5px] font-extrabold tracking-wider text-slate-400">{g.group}</p>
                {g.items.map((it) => {
                  const Icon = ICONS[it.icon] ?? Package;
                  return (
                    <NavLink key={it.to} to={it.to} className={({ isActive }) => cx("flex items-center gap-3 px-3 py-2.5 rounded-xl text-[14.5px] font-medium mb-0.5 transition-colors", isActive || (it.to !== "/" && loc.pathname.startsWith(it.to)) ? "bg-[#0f2a4a] text-white shadow-md" : "text-slate-700 hover:bg-slate-100")}>
                      <Icon size={19} className="shrink-0" />
                      <span className="flex-1">{it.label}</span>
                      {it.to === "/viec-can-xu-ly" && openTaskCount > 0 && <span className="text-[11px] font-extrabold bg-red-500 text-white rounded-full min-w-[22px] h-[22px] grid place-items-center px-1">{openTaskCount}</span>}
                      {it.soon && <span className="text-[10.5px] font-extrabold uppercase tracking-wide rounded-full border border-slate-300 bg-slate-100 text-slate-500 px-2 py-0.5">Sắp có</span>}
                    </NavLink>
                  );
                })}
              </div>
            ))}
            <div className="mx-1 mt-2 rounded-2xl bg-gradient-to-br from-[#0f2a4a] to-[#1e5aa8] text-white p-4">
              <p className="font-bold text-[14px]">Cần hỗ trợ thao tác?</p>
              <p className="text-[12.5px] text-blue-100 mt-1">Sổ tay tra cứu quy trình, chứng từ và phân quyền cho Sale & Support.</p>
              <Link to="/so-tay" className="mt-2.5 inline-flex items-center gap-1.5 bg-white text-[#0f2a4a] text-[13.5px] font-bold rounded-lg px-3 py-2">Mở sổ tay <ChevronRight size={15} /></Link>
            </div>
          </nav>
        </aside>

        {/* ===== DRAWER tablet/mobile ===== */}
        {navOpen && (
          <div className="no-print fixed inset-0 z-50 lg:hidden">
            <div className="absolute inset-0 bg-slate-900/50 anim-fade" onClick={() => setNavOpen(false)} />
            <div className="absolute left-0 top-0 bottom-0 w-[300px] max-w-[85vw] bg-white shadow-2xl overflow-y-auto anim-slide-up">
              <div className="flex items-center justify-between p-4 border-b sticky top-0 bg-white z-10">
                <span className="font-extrabold text-[#0f2a4a]">Menu điều hành</span>
                <button onClick={() => setNavOpen(false)} className="touch-target w-11 h-11 grid place-items-center rounded-xl hover:bg-slate-100"><X size={20} /></button>
              </div>
              <div className="p-3">
                {/* P1.5 — role preview only exists in the sandbox; a normal
                    runtime shows the actual logged-in role without any
                    switcher. */}
                {environment?.isSandbox && (
                  <div className="flex gap-2 mb-3" data-testid="role-preview-mobile">
                    {(["ADMIN", "SUPPORT", "SALE"] as Role[]).map((r) => (
                      <button key={r} onClick={() => { setRole(r); toast(`Đang XEM TRƯỚC giao diện ${ROLE_LABEL[r]}`, "Chỉ thay đổi hiển thị trong sandbox.", "blue"); }} className={cx("flex-1 touch-target rounded-xl border-2 text-[13px] font-bold py-2", role === r ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 text-slate-600")}>{r}</button>
                    ))}
                  </div>
                )}
                <p className="px-2 text-[12px] text-slate-500 mb-2">Đang dùng: <b>{userName}</b> · {ROLE_LABEL[role]}{environment?.isSandbox ? " (xem trước giao diện)" : ""}</p>
                {NAV.map((g) => (
                  <div key={g.group} className="mb-3">
                    <p className="px-2 mb-1 text-[11px] font-extrabold tracking-wider text-slate-400">{g.group}</p>
                    {g.items.map((it) => {
                      const Icon = ICONS[it.icon] ?? Package;
                      const active = it.to === "/" ? loc.pathname === "/" : loc.pathname.startsWith(it.to);
                      return (
                        <NavLink key={it.to} to={it.to} onClick={() => setNavOpen(false)} className={cx("flex items-center gap-3 px-3 py-3 rounded-xl text-[15px] font-medium mb-0.5", active ? "bg-[#0f2a4a] text-white" : "text-slate-700 hover:bg-slate-100")}>
                          <Icon size={20} className="shrink-0" />{it.label}
                          {it.to === "/viec-can-xu-ly" && openTaskCount > 0 && <span className="ml-auto text-[11px] font-extrabold bg-red-500 text-white rounded-full min-w-[22px] h-[22px] grid place-items-center px-1">{openTaskCount}</span>}
                          {it.soon && <span className="ml-auto text-[10.5px] font-extrabold uppercase tracking-wide rounded-full border border-slate-300 bg-slate-100 text-slate-500 px-2 py-0.5">Sắp có</span>}
                        </NavLink>
                      );
                    })}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ===== MAIN ===== */}
        <main className="flex-1 min-w-0 px-3 md:px-6 py-4 md:py-6 pb-28 md:pb-10 w-full">
          {children}
          <footer className="mt-10 text-center text-[12.5px] text-slate-400 pb-4">
            CÔNG TY TNHH GIAO NHẬN QUỐC TẾ TRƯỜNG THÀNH · Đại lý: Phú Anh Logistics Việt Nam · {environment?.isSandbox ? "Bản nội bộ — môi trường staging cách ly, mọi ghi nhận đi qua writer/RBAC/audit thật" : "Bản nội bộ — dữ liệu thật từ hệ thống Logistics, cập nhật liên tục"}
          </footer>
        </main>
      </div>

      {/* ===== MOBILE BOTTOM NAV ===== */}
      <nav className="no-print md:hidden fixed bottom-0 left-0 right-0 z-40 bg-white border-t border-slate-200 shadow-[0_-4px_20px_rgba(0,0,0,.08)]" style={{ paddingBottom: "env(safe-area-inset-bottom)" }}>
        <div className="grid grid-cols-5">
          {[
            { to: "/", label: "Tổng quan", icon: ICONS.layout },
            { to: "/lo-hang", label: "Lô hàng", icon: Package },
            { to: "/hop-dong", label: "Hợp đồng", icon: FileText },
            { to: "/tai-chinh/thu-tien", label: "Tài chính", icon: Wallet },
          ].map((b) => {
            const active = b.to === "/" ? loc.pathname === "/" : loc.pathname.startsWith(b.to);
            const Icon = b.icon;
            return (
              <NavLink key={b.to} to={b.to} className={cx("touch-target flex flex-col items-center justify-center gap-0.5 py-2 text-[11.5px] font-semibold", active ? "text-[#0f2a4a]" : "text-slate-400")}>
                <Icon size={22} strokeWidth={active ? 2.4 : 1.8} />
                {b.label}
                {active && <span className="w-8 h-1 rounded-full bg-[#0f2a4a]" />}
              </NavLink>
            );
          })}
          <button onClick={() => setQuickAddOpen(true)} className="touch-target flex flex-col items-center justify-center gap-0.5 py-1.5 text-[11.5px] font-semibold text-slate-500">
            <span className="w-11 h-8 -mt-3 rounded-2xl bg-[#0f2a4a] text-white grid place-items-center shadow-lg"><Plus size={22} /></span>
            Thêm
          </button>
        </div>
      </nav>

      {/* ===== NOTIF DRAWER ===== */}
      {notifOpen && (
        <div className="no-print fixed inset-0 z-50">
          <div className="absolute inset-0 bg-slate-900/50 anim-fade" onClick={() => setNotifOpen(false)} />
          <div className="absolute right-0 top-0 bottom-0 w-[380px] max-w-[92vw] bg-white shadow-2xl flex flex-col anim-slide-up">
            <div className="flex items-center justify-between p-4 border-b">
              <p className="font-extrabold text-[16px] text-[#0f2a4a]">Thông báo · {notifCount} chưa đọc</p>
              <button onClick={() => setNotifOpen(false)} className="touch-target w-11 h-11 grid place-items-center rounded-xl hover:bg-slate-100"><X size={20} /></button>
            </div>
            <div className="flex-1 overflow-y-auto p-3 space-y-2">
              {notifs.length === 0 && <p className="text-[14px] text-slate-500 p-4 text-center">Không có cảnh báo nào theo dữ liệu hiện tại.</p>}
              {notifs.map((n) => (
                <div key={n.id} className="rounded-2xl border border-slate-200 p-3.5 lift">
                  <div className="flex items-start gap-2.5">
                    <span className={cx("w-2.5 h-2.5 rounded-full mt-1.5 shrink-0", n.tone === "red" ? "bg-red-500 pulse-dot" : n.tone === "amber" ? "bg-amber-500" : "bg-blue-500")} />
                    <div><p className="font-bold text-[14.5px] text-[#0f2a4a]">{n.title}</p><p className="text-[13.5px] text-slate-600 mt-0.5">{n.desc}</p><p className="text-[12px] text-slate-400 mt-1">{n.time}</p></div>
                  </div>
                </div>
              ))}
            </div>
            <div className="p-3 border-t"><button onClick={() => { setNotifOpen(false); nav("/viec-can-xu-ly"); }} className="w-full touch-target rounded-xl bg-[#0f2a4a] text-white font-bold py-3">Mở Việc Cần Xử Lý</button></div>
          </div>
        </div>
      )}

      {/* ===== QUICK ADD SHEET ===== */}
      {quickAddOpen && (
        <SheetDialog id="quick-add-sheet" testId="quick-add-sheet" labelledBy="quick-add-title" width={520} onClose={() => setQuickAddOpen(false)}>
          <div className="no-print">
            <div className="w-12 h-1.5 bg-slate-200 rounded-full mx-auto mb-4 sm:hidden" />
            <div className="flex items-center justify-between mb-1"><p id="quick-add-title" className="font-extrabold text-[18px] text-[#0f2a4a]">Thêm mới nhanh</p><button onClick={() => setQuickAddOpen(false)} aria-label="Đóng thêm mới nhanh" className="touch-target w-11 h-11 grid place-items-center rounded-xl hover:bg-slate-100"><X size={20} /></button></div>
            <p className="text-[13.5px] text-slate-500 mb-4">Chọn việc muốn làm — mỗi nút dẫn thẳng tới màn hình nhập liệu.</p>
            <div className="grid gap-2.5">
              {[
                { label: "Tạo lô hàng mới", desc: "Từ báo giá đã chốt hoặc nhập tay", to: "/tao-lo-moi", icon: Package, bg: "bg-blue-50 text-blue-700" },
                { label: "Tạo hợp đồng mới", desc: "HDMB / HDNT + phụ lục", to: "/hop-dong/moi", icon: FileText, bg: "bg-emerald-50 text-emerald-700" },
                { label: "Tạo báo giá", desc: "Dự toán chi phí & giá bán", to: "/kinh-doanh-bao-gia", icon: Calculator, bg: "bg-violet-50 text-violet-700" },
                { label: "Ghi nhận thanh toán", desc: "Thu tiền khách / trả đối tác", to: "/tai-chinh/thu-tien", icon: Wallet, bg: "bg-amber-50 text-amber-700" },
                { label: "Tra cứu thuế / HS", desc: "Mã HS & mô tả hàng hóa", to: "/tra-cuu-thue", icon: Truck, bg: "bg-slate-100 text-slate-700" },
              ].map((a) => (
                <button key={a.label} onClick={() => { setQuickAddOpen(false); nav(a.to); }} className="touch-target flex items-center gap-3 rounded-2xl border-2 border-slate-100 hover:border-[#1e5aa8] p-3.5 text-left lift bg-white">
                  <span className={cx("w-11 h-11 rounded-xl grid place-items-center shrink-0", a.bg)}><a.icon size={21} /></span>
                  <span className="flex-1"><span className="font-bold text-[15px] text-[#0f2a4a] flex items-center gap-2">{a.label}</span><span className="block text-[13px] text-slate-500">{a.desc}</span></span>
                  <ChevronRight size={19} className="text-slate-300" />
                </button>
              ))}
            </div>
          </div>
        </SheetDialog>
      )}

      {/* ===== TOASTS ===== */}
      <div className="no-print fixed z-[60] left-3 right-3 bottom-[84px] md:left-auto md:right-6 md:bottom-6 md:w-[380px] space-y-2">
        {toasts.map((t) => (
          <div key={t.id} className="toast-in rounded-2xl bg-[#0f2a4a] text-white p-4 shadow-2xl flex items-start gap-3">
            <span className={cx("w-9 h-9 rounded-xl grid place-items-center shrink-0", t.tone === "green" ? "bg-emerald-500" : t.tone === "red" ? "bg-red-500" : t.tone === "amber" ? "bg-amber-500" : "bg-blue-500")}>
              {t.tone === "green" ? "✓" : t.tone === "red" ? "!" : t.tone === "amber" ? "⚠" : "i"}
            </span>
            <div className="flex-1 min-w-0"><p className="font-bold text-[14.5px]">{t.title}</p>{t.desc && <p className="text-[13px] text-blue-100 mt-0.5">{t.desc}</p>}</div>
            <button onClick={() => dismissToast(t.id)} className="w-8 h-8 grid place-items-center rounded-lg hover:bg-white/10 shrink-0"><X size={16} /></button>
          </div>
        ))}
      </div>
      {searchOpen && <div className="fixed inset-0 z-30 hidden md:block" onClick={() => setSearchOpen(false)} />}
    </div>
  );
}
