import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Plus, Search, ArrowRight, Eye } from "lucide-react";
import { SectionTitle, ToneBadge } from "../components/ui";
import { useStore } from "../lib/store";
import { fmtVND, cx } from "../lib/format";

export default function Contracts() {
  const { contracts } = useStore();
  const [q, setQ] = useState("");
  const [type, setType] = useState("ALL");
  const list = useMemo(() => contracts.filter((c) => (type === "ALL" || c.type === type) && (!q || (c.id + c.company + c.agent + c.linkedLots.map((l) => l.id).join(" ")).toLowerCase().includes(q.toLowerCase()))), [contracts, q, type]);

  return (
    <div className="space-y-4 max-w-[1300px]">
      <div className="rounded-2xl bg-gradient-to-br from-[#0f2a4a] to-[#1e5aa8] text-white p-5 md:p-6 flex flex-col md:flex-row md:items-center gap-4">
        <div className="flex-1">
          <h1 className="text-[20px] md:text-[24px] font-extrabold">Hợp Đồng — Bàn làm việc chính</h1>
          <p className="text-blue-100 text-[14.5px] mt-1">Tạo & quản lý HDMB / HDNT / Phụ lục tại đây. <b className="text-white">Không tạo hợp đồng trong màn hình Lô hàng</b> — lô chỉ gắn hợp đồng có sẵn.</p>
        </div>
        <Link to="/hop-dong/moi" className="btn-press touch-target inline-flex items-center justify-center gap-2 rounded-xl bg-white text-[#0f2a4a] font-extrabold text-[15.5px] px-6 min-h-[52px] whitespace-nowrap">➕ TẠO HỢP ĐỒNG MỚI</Link>
      </div>

      <div className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5">
        <div className="flex gap-2">
          <div className="flex items-center flex-1 rounded-xl border-2 border-slate-200 focus-within:border-[#1e5aa8] bg-slate-50 overflow-hidden">
            <Search size={19} className="ml-3.5 text-slate-400 shrink-0" />
            <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Tìm số hợp đồng · đại lý · công ty · mã lô…" className="w-full bg-transparent px-3 py-3 text-[15px] outline-none" />
          </div>
        </div>
        <div className="flex gap-2 mt-2.5 overflow-x-auto no-scrollbar">
          {[["ALL", "Tất cả"], ["HDMB", "HDMB"], ["HDNT", "HDNT / PL"]].map(([v, l]) => (
            <button key={v} onClick={() => setType(v)} className={cx("touch-target shrink-0 rounded-full border-2 px-4 min-h-[44px] text-[14px] font-bold", type === v ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 text-slate-600")}>{l}</button>
          ))}
        </div>
        <p className="text-[13.5px] text-slate-500 mt-2">Tìm thấy <b className="text-[#0f2a4a]">{list.length} hợp đồng</b> · Mỗi dòng: hiện trạng → việc thiếu → nút mở.</p>
      </div>

      <div className="hidden md:block rounded-2xl bg-white border border-slate-200 overflow-hidden">
        <div className="overflow-x-auto"><table className="tbl w-full text-[14px] min-w-[1020px]">
          <thead><tr><th>Số hợp đồng</th><th>Loại</th><th>Đại lý · Công ty</th><th>Giá trị</th><th>Hiệu lực</th><th>Số lô</th><th>Trạng thái</th><th></th></tr></thead>
          <tbody>
            {list.map((c) => (
              <tr key={c.id} className="hover:bg-slate-50">
                <td className="font-extrabold text-[#1e5aa8] whitespace-nowrap"><Link to={"/hop-dong/" + c.id} className="hover:underline">{c.id}</Link></td>
                <td><span className={cx("text-[12.5px] font-extrabold rounded-md px-2 py-1", c.type === "HDMB" ? "bg-blue-100 text-blue-800" : "bg-emerald-100 text-emerald-800")}>{c.type}</span></td>
                <td className="max-w-[230px]"><span className="block font-semibold">{c.company}</span><span className="block text-[12.5px] text-slate-500">{c.agent}</span></td>
                <td className="font-extrabold whitespace-nowrap">{c.value ? fmtVND(c.value) : <span className="text-amber-600">Chưa tính</span>}</td>
                <td className="text-[13px] whitespace-nowrap">{c.validFrom ? <>{c.validFrom} → {c.validTo}</> : <span className="text-amber-700 font-semibold">⚠ Thiếu ngày</span>}</td>
                <td className="text-center font-bold">{c.lots}</td>
                <td><ToneBadge tone={c.statusTone} size="sm">{c.status}</ToneBadge></td>
                <td><Link to={"/hop-dong/" + c.id} className="btn-press touch-target inline-flex items-center gap-1 rounded-lg bg-[#0f2a4a] text-white text-[13px] font-bold px-3.5 min-h-[44px] whitespace-nowrap">MỞ HỢP ĐỒNG <ArrowRight size={14} /></Link></td>
              </tr>
            ))}
          </tbody>
        </table></div>
      </div>

      <div className="md:hidden space-y-3">
        {list.map((c) => (
          <div key={c.id} className="rounded-2xl bg-white border border-slate-200 p-4">
            <div className="flex items-center gap-2 flex-wrap">
              <span className={cx("text-[12px] font-extrabold rounded-md px-2 py-1", c.type === "HDMB" ? "bg-blue-100 text-blue-800" : "bg-emerald-100 text-emerald-800")}>{c.type}</span>
              <ToneBadge tone={c.statusTone} size="sm">{c.status}</ToneBadge>
            </div>
            <p className="font-extrabold text-[16px] text-[#0f2a4a] mt-1.5">{c.id}</p>
            <p className="text-[14px] text-slate-600">{c.company}</p>
            <div className="mt-2 rounded-xl bg-slate-50 border p-3 text-[13.5px]">
              <p>Giá trị: <b className="text-[15px]">{c.value ? fmtVND(c.value) : "Chưa tính"}</b></p>
              <p className="text-slate-500">Hiệu lực: {c.validFrom ? `${c.validFrom} → ${c.validTo}` : "⚠ Thiếu ngày"} · {c.lots} lô liên kết</p>
            </div>
            {c.missingBuyerInfo.length > 0 && <p className="mt-2 text-[13px] font-semibold text-amber-800 bg-amber-50 border border-amber-200 rounded-lg p-2">⚠ Thiếu: {c.missingBuyerInfo.join(" · ")}</p>}
            <Link to={"/hop-dong/" + c.id} className="btn-press touch-target mt-3 flex items-center justify-center gap-2 rounded-xl bg-[#0f2a4a] text-white font-extrabold min-h-[52px]">MỞ HỢP ĐỒNG <ArrowRight size={17} /></Link>
          </div>
        ))}
        {list.length === 0 && (
          <div className="rounded-2xl bg-white border-2 border-dashed border-slate-300 p-10 text-center">
            <p className="font-bold text-[16px]">Chưa có hợp đồng nào cho Đại lý này.</p>
            <Link to="/hop-dong/moi" className="btn-press touch-target mt-3 inline-flex items-center gap-2 rounded-xl bg-[#0f2a4a] text-white font-bold px-6 min-h-[52px]"><Plus size={18} /> TẠO HỢP ĐỒNG</Link>
          </div>
        )}
      </div>

      <div className="md:hidden sticky-action -mx-3 px-3 py-3">
        <Link to="/hop-dong/moi" className="btn-press touch-target flex items-center justify-center gap-2 rounded-xl bg-[#0f2a4a] text-white font-extrabold min-h-[52px]">➕ TẠO HỢP ĐỒNG MỚI</Link>
      </div>
    </div>
  );
}
