import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Search, ArrowRight, Eye, SlidersHorizontal } from "lucide-react";
import { SectionTitle, ToneBadge, StatusDot } from "../components/ui";
import { useStore } from "../lib/store";
import { cx } from "../lib/format";

export default function Shipments() {
  const { shipments } = useStore();
  const [q, setQ] = useState("");
  const [status, setStatus] = useState("ALL");
  const [showFilter, setShowFilter] = useState(false);
  const list = useMemo(() => shipments.filter((s) => (status === "ALL" || s.status === status) && (!q || (s.id + s.customer + s.contract + s.route + s.sale + s.support).toLowerCase().includes(q.toLowerCase()))), [shipments, q, status]);
  const statuses = ["ALL", ...Array.from(new Set(shipments.map((s) => s.status)))];

  return (
    <div className="space-y-4 max-w-[1300px]">
      <div className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5">
        <SectionTitle title="Lô Hàng" sub="Tìm theo mã lô · khách · container · hợp đồng · trạng thái · Sale · Support · tuyến · cửa khẩu" right={<Link to="/tao-lo-moi" className="btn-press touch-target hidden sm:inline-flex items-center gap-1.5 rounded-xl bg-[#0f2a4a] text-white font-bold text-[14.5px] px-4 min-h-[48px]">＋ Tạo lô mới</Link>} />
        <div className="flex gap-2">
          <div className="flex items-center flex-1 rounded-xl border-2 border-slate-200 focus-within:border-[#1e5aa8] bg-slate-50 overflow-hidden">
            <Search size={19} className="ml-3.5 text-slate-400 shrink-0" />
            <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Nhập mã lô (LO-0306), khách (An Phát), hợp đồng…" className="w-full bg-transparent px-3 py-3 text-[15px] outline-none" />
          </div>
          <button onClick={() => setShowFilter((v) => !v)} className={cx("touch-target shrink-0 inline-flex items-center gap-1.5 rounded-xl border-2 px-4 min-h-[52px] text-[14.5px] font-bold", showFilter ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 bg-white")}><SlidersHorizontal size={18} /> <span className="hidden sm:inline">Lọc</span></button>
        </div>
        {showFilter && (
          <div className="flex gap-2 mt-2.5 overflow-x-auto no-scrollbar pb-1">
            {statuses.map((s) => (
              <button key={s} onClick={() => setStatus(s)} className={cx("touch-target shrink-0 rounded-full border-2 px-4 min-h-[44px] text-[14px] font-bold whitespace-nowrap", status === s ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 bg-white text-slate-600")}>{s === "ALL" ? "Tất cả" : s}</button>
            ))}
          </div>
        )}
        <p className="text-[13.5px] text-slate-500 mt-2.5">Tìm thấy <b className="text-[#0f2a4a]">{list.length} lô</b>{q ? <> cho “{q}”</> : null} · Mỗi lô hiển thị: hiện trạng → việc tiếp theo → nút xử lý.</p>
      </div>

      <div className="hidden md:block rounded-2xl bg-white border border-slate-200 overflow-hidden">
        <div className="overflow-x-auto"><table className="tbl w-full text-[14px] min-w-[1080px]">
          <thead><tr><th>Mã lô</th><th>Khách hàng</th><th>Hợp đồng · Tuyến</th><th>Trạng thái</th><th>Việc tiếp theo</th><th>Sale · Support</th><th>Hành động</th></tr></thead>
          <tbody>
            {list.map((s) => (
              <tr key={s.id} className="hover:bg-slate-50">
                <td><Link to={"/lo-hang/" + s.id} className="font-extrabold text-[#1e5aa8] hover:underline text-[15px]">{s.id}</Link><span className="block text-[12px] text-slate-400">Cập nhật {s.updated}</span></td>
                <td className="font-semibold max-w-[180px]">{s.customer}</td>
                <td className="max-w-[220px]"><span className="block text-[13px] font-semibold text-slate-600">{s.contract}</span><span className="block text-[13px] text-slate-500">{s.route}</span></td>
                <td><ToneBadge tone={s.statusTone} size="sm">{s.status}</ToneBadge></td>
                <td className="max-w-[240px]"><span className="block font-semibold text-[13.5px]">{s.nextAction}</span></td>
                <td className="text-[13px]"><span className="block whitespace-nowrap">Sale: <b>{s.sale}</b></span><span className="block whitespace-nowrap">SP: <b>{s.support}</b></span></td>
                <td><div className="flex gap-1.5"><Link to={s.nextRoute} className="btn-press touch-target inline-flex items-center rounded-lg bg-[#0f2a4a] text-white text-[13px] font-bold px-3.5 min-h-[44px]">XỬ LÝ</Link><Link to={"/lo-hang/" + s.id} className="btn-press touch-target inline-flex items-center gap-1 rounded-lg border-2 border-slate-200 text-[13px] font-bold px-3 min-h-[44px]"><Eye size={15} /> 360°</Link></div></td>
              </tr>
            ))}
          </tbody>
        </table></div>
      </div>

      <div className="md:hidden space-y-3">
        {list.map((s) => (
          <div key={s.id} className="rounded-2xl bg-white border border-slate-200 overflow-hidden">
            <div className="p-4">
              <div className="flex items-center gap-2 flex-wrap">
                <StatusDot tone={s.statusTone} />
                <span className="font-extrabold text-[17px] text-[#0f2a4a]">{s.id}</span>
                <ToneBadge tone={s.statusTone} size="sm">{s.status}</ToneBadge>
              </div>
              <p className="font-semibold text-[14.5px] mt-1">{s.customer}</p>
              <p className="text-[13px] text-slate-500">{s.route}</p>
              <div className="mt-2.5 rounded-xl bg-amber-50 border border-amber-200 p-3">
                <p className="text-[11.5px] font-bold uppercase tracking-wide text-amber-700">Việc tiếp theo</p>
                <p className="text-[14px] font-semibold text-slate-800 mt-0.5">{s.nextAction}</p>
              </div>
              <p className="text-[12.5px] text-slate-400 mt-2">Sale {s.sale} · SP {s.support} · {s.updated}</p>
            </div>
            <div className="grid grid-cols-2 border-t">
              <Link to={s.nextRoute} className="touch-target flex items-center justify-center gap-1.5 bg-[#0f2a4a] text-white font-extrabold text-[15px] min-h-[52px]">XỬ LÝ <ArrowRight size={17} /></Link>
              <Link to={"/lo-hang/" + s.id} className="touch-target flex items-center justify-center gap-1.5 font-bold text-[15px] text-[#0f2a4a] min-h-[52px]"><Eye size={17} /> XEM 360°</Link>
            </div>
          </div>
        ))}
        {list.length === 0 && <div className="rounded-2xl bg-white border p-8 text-center"><p className="font-bold text-[16px]">Không tìm thấy lô nào</p><p className="text-[14px] text-slate-500 mt-1">Thử từ khóa khác hoặc tạo lô mới.</p><Link to="/tao-lo-moi" className="btn-press touch-target mt-3 inline-flex rounded-xl bg-[#0f2a4a] text-white font-bold px-5 min-h-[48px] items-center">＋ Tạo lô mới</Link></div>}
      </div>
    </div>
  );
}
