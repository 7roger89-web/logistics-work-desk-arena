import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, Eye, Plus, Search } from "lucide-react";
import { SectionTitle, ToneBadge } from "../components/ui";
import { CUSTOMERS } from "../lib/data";
import { fmtVND } from "../lib/format";
import { useStore } from "../lib/store";

export function Customers() {
  const [q, setQ] = useState("");
  const list = useMemo(() => CUSTOMERS.filter((c) => !q || (c.name + c.mst + c.contact).toLowerCase().includes(q.toLowerCase())), [q]);
  const { toast } = useStore();
  return (
    <div className="space-y-4 max-w-[1300px]">
      <div className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5">
        <SectionTitle title="Khách Hàng" sub="Hiện trạng công nợ → hành động: tạo báo giá, tạo lô, xem hợp đồng" />
        <div className="flex items-center rounded-xl border-2 border-slate-200 focus-within:border-[#1e5aa8] bg-slate-50 overflow-hidden">
          <Search size={19} className="ml-3.5 text-slate-400 shrink-0" />
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Tìm tên công ty, MST, liên hệ…" className="w-full bg-transparent px-3 py-3 text-[15px] outline-none" />
        </div>
      </div>
      <div className="hidden md:block rounded-2xl bg-white border border-slate-200 overflow-hidden">
        <div className="overflow-x-auto"><table className="tbl w-full text-[14px] min-w-[960px]">
          <thead><tr><th>Khách hàng</th><th>MST · Liên hệ</th><th>Sale</th><th>Số lô</th><th>Công nợ</th><th>Cập nhật</th><th>Hành động</th></tr></thead>
          <tbody>{list.map((c) => (
            <tr key={c.mst} className="hover:bg-slate-50">
              <td className="font-bold max-w-[240px]">{c.name}</td>
              <td className="text-[13px]"><span className="block font-semibold">{c.mst}</span><span className="block text-slate-500">{c.contact}</span></td>
              <td>{c.sale}</td><td className="text-center font-bold">{c.lots}</td>
              <td className={c.debt ? "font-extrabold text-red-700" : "font-bold text-emerald-700"}>{c.debt ? fmtVND(c.debt) : "Hết nợ ✓"}</td>
              <td className="text-[13px] text-slate-500">{c.updated}</td>
              <td><div className="flex gap-1.5 flex-wrap"><Link to="/kinh-doanh-bao-gia" className="touch-target inline-flex items-center rounded-lg bg-[#0f2a4a] text-white text-[12.5px] font-bold px-2.5 min-h-[40px]">＋ Báo giá</Link><Link to="/tao-lo-moi" className="touch-target inline-flex items-center rounded-lg border-2 border-slate-200 text-[12.5px] font-bold px-2.5 min-h-[40px]">＋ Lô</Link><Link to="/hop-dong" className="touch-target inline-flex items-center rounded-lg border-2 border-slate-200 text-[12.5px] font-bold px-2.5 min-h-[40px]">Hợp đồng</Link></div></td>
            </tr>))}</tbody>
        </table></div>
      </div>
      <div className="md:hidden space-y-3">
        {list.map((c) => (
          <div key={c.mst} className="rounded-2xl bg-white border border-slate-200 p-4">
            <p className="font-extrabold text-[15.5px] text-[#0f2a4a]">{c.short}</p>
            <p className="text-[13px] text-slate-500">{c.name} · MST {c.mst}</p>
            <p className="text-[13.5px] mt-1">📞 {c.contact} · Sale {c.sale} · {c.lots} lô</p>
            <div className={c.debt ? "mt-2 rounded-xl bg-red-50 border border-red-200 p-2.5 text-[14px]" : "mt-2 rounded-xl bg-emerald-50 border border-emerald-200 p-2.5 text-[14px]"}>
              Công nợ: <b>{c.debt ? fmtVND(c.debt) : "Hết nợ ✓"}</b>
              {c.debt > 0 && <Link to="/tai-chinh/thu-tien" className="ml-2 font-bold text-[#1e5aa8]">Thu ngay →</Link>}
            </div>
            {c.note && <p className="text-[13px] text-slate-500 mt-1.5">📝 {c.note}</p>}
            <div className="grid grid-cols-3 gap-2 mt-3">
              <Link to="/kinh-doanh-bao-gia" className="touch-target flex items-center justify-center rounded-xl bg-[#0f2a4a] text-white text-[13.5px] font-bold min-h-[48px]">＋ Báo giá</Link>
              <Link to="/tao-lo-moi" className="touch-target flex items-center justify-center rounded-xl border-2 border-slate-200 text-[13.5px] font-bold min-h-[48px]">＋ Tạo lô</Link>
              <Link to="/hop-dong" className="touch-target flex items-center justify-center rounded-xl border-2 border-slate-200 text-[13.5px] font-bold min-h-[48px]">Hợp đồng</Link>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export function PartnerContext() {
  const { toast } = useStore();
  return (
    <div className="space-y-4 max-w-[1000px]">
      <SectionTitle title="Ngữ Cảnh Đối Tác" sub="Đại lý & cửa khẩu — ai làm gì, liên hệ ai, số dư ra sao" />
      <div className="grid md:grid-cols-2 gap-4">
        <section className="rounded-2xl bg-white border border-slate-200 p-5">
          <h3 className="font-extrabold text-[16.5px] text-[#0f2a4a]">Đại lý: Phú Anh Logistics Việt Nam</h3>
          <div className="text-[14px] mt-2 space-y-1.5">
            <p><span className="text-slate-500">Pháp lý:</span> <b>CÔNG TY TNHH PHÚ ANH LOGISTICS VIỆT NAM</b></p>
            <p><span className="text-slate-500">MST:</span> 0108123456 · <span className="text-slate-500">Đại diện:</span> Nguyễn Phú Anh (Giám đốc)</p>
            <p><span className="text-slate-500">Đầu TQ:</span> chi nhánh Bằng Tường — Mr. Lưu (+86 139 2611 8899)</p>
            <p><span className="text-slate-500">Kho VN:</span> Lạng Sơn + Bắc Ninh — Thu Hằng điều phối</p>
            <p><span className="text-slate-500">TK:</span> 0451000412345 · Vietcombank Thanh Xuân</p>
          </div>
          <div className="mt-3 rounded-xl bg-amber-50 border border-amber-200 p-3 text-[13.5px]">Số dư phải trả Bằng Tường: <b>73.800.000 ₫</b> + <b>27.700 CNY</b> — <Link to="/tai-chinh/doi-soat" className="font-bold text-[#1e5aa8]">Đối soát →</Link></div>
        </section>
        <section className="rounded-2xl bg-white border border-slate-200 p-5">
          <h3 className="font-extrabold text-[16.5px] text-[#0f2a4a]">Cửa khẩu & tuyến trọng điểm</h3>
          <div className="space-y-2.5 mt-2">
            {[["Hữu Nghị (TQ↔VN)", "Cont 40HQ · 6–8 tiếng · LO-0306, 0308 đang đi", "amber"], ["Tân Thanh (TQ↔VN)", "Xe tải · 3–5 tiếng · LO-0307, 0299 đang đi", "blue"]].map(([t, d, tone]) => (
              <div key={t as string} className="rounded-xl border p-3"><p className="font-bold text-[14.5px]">{t}</p><p className="text-[13px] text-slate-500">{d}</p></div>
            ))}
          </div>
          <button onClick={() => toast("Đã lưu ghi chú đối tác", "Ghi chú hiển thị cho mọi lô dùng tuyến này.", "green")} className="btn-press touch-target mt-3 w-full rounded-xl border-2 border-slate-200 font-bold min-h-[48px]">＋ Thêm ghi chú đối tác</button>
        </section>
      </div>
    </div>
  );
}
