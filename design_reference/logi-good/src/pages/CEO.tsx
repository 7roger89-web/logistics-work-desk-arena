import { useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, BarChart3 } from "lucide-react";
import { SectionTitle, ToneBadge } from "../components/ui";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line, CartesianGrid } from "recharts";
import { cx } from "../lib/format";

const REV = [
  { m: "T6", dt: 980, ln: 162 },
  { m: "T7", dt: 1240, ln: 205 },
  { m: "T8", dt: 1510, ln: 262 },
  { m: "T9*", dt: 890, ln: 148 },
];
const PIE = [
  { name: "Chờ lấy hàng", value: 1 },
  { name: "Đang vận chuyển", value: 1 },
  { name: "Chờ thông quan", value: 1 },
  { name: "Chờ giao", value: 1 },
  { name: "Đã giao", value: 3 },
];
const COLORS = ["#94a3b8", "#3b82f6", "#f59e0b", "#8b5cf6", "#10b981"];

export default function CEO() {
  const [period, setPeriod] = useState("Tháng");
  return (
    <div className="space-y-4 max-w-[1300px]">
      <div className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5 flex flex-col md:flex-row md:items-center gap-3">
        <div className="flex-1">
          <SectionTitle title="Báo Cáo CEO" sub="Doanh thu · lợi nhuận · công nợ · điểm nghẽn — chỉ hiện số giúp quyết định" />
        </div>
        <div className="flex gap-2">
          {["Tuần", "Tháng", "Quý", "Năm"].map((p) => (
            <button key={p} onClick={() => setPeriod(p)} className={cx("touch-target rounded-xl border-2 px-4 min-h-[44px] text-[14px] font-bold", period === p ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 text-slate-600")}>{p}</button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-2 xl:grid-cols-4 gap-3">
        {[
          ["Doanh thu " + period.toLowerCase(), "1.510 tr ₫", "+22% vs kỳ trước", "text-emerald-700"],
          ["Lợi nhuận gộp", "262 tr ₫", "Margin 17,4%", "text-[#0f2a4a]"],
          ["Phải thu còn lại", "537,6 tr ₫", "1 khoản hạn hôm nay", "text-red-700"],
          ["Phải trả còn lại", "73,8 tr ₫", "Chờ đối soát", "text-amber-700"],
        ].map(([l, v, s, c]) => (
          <div key={l as string} className="rounded-2xl bg-white border border-slate-200 p-4">
            <p className="text-[13px] font-semibold text-slate-500">{l}</p>
            <p className={cx("text-[22px] md:text-[26px] font-extrabold", c as string)}>{v}</p>
            <p className="text-[12.5px] text-slate-400">{s}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        <section className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5">
          <h3 className="font-extrabold text-[15.5px] mb-1">Doanh thu & lợi nhuận (tr ₫) — *T9 tính tới 09/09</h3>
          <div className="h-[240px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={REV}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="m" tick={{ fontSize: 13 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Bar dataKey="dt" name="Doanh thu" fill="#0f2a4a" radius={[6, 6, 0, 0]} />
                <Bar dataKey="ln" name="Lợi nhuận" fill="#10b981" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>
        <section className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5">
          <h3 className="font-extrabold text-[15.5px] mb-1">Trạng thái lô hàng (7 lô gần nhất)</h3>
          <div className="h-[240px]">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={PIE} dataKey="value" nameKey="name" outerRadius={88} label={{ fontSize: 12 }}>
                  {PIE.map((_, i) => (<Cell key={i} fill={COLORS[i % COLORS.length]} />))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="flex flex-wrap gap-1.5 mt-1">{PIE.map((p, i) => (<span key={p.name} className="text-[12px] font-semibold inline-flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full" style={{ background: COLORS[i] }} />{p.name}: {p.value}</span>))}</div>
        </section>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        <section className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5">
          <h3 className="font-extrabold text-[15.5px] mb-2">Top khách hàng (doanh thu T8–T9)</h3>
          {[["Cơ Khí An Phát", "873 tr", 100], ["Sao Việt", "247 tr", 42], ["Hồng Hà", "215 tr", 36], ["Minh Đức", "172 tr", 28]].map(([n, v, w]) => (
            <div key={n as string} className="py-2 border-b last:border-0">
              <div className="flex justify-between text-[14px]"><b>{n}</b><b>{v} ₫</b></div>
              <div className="h-2.5 bg-slate-100 rounded-full mt-1.5"><div className="h-2.5 rounded-full bg-gradient-to-r from-[#0f2a4a] to-[#1e5aa8]" style={{ width: (w as number) + "%" }} /></div>
            </div>
          ))}
        </section>
        <section className="rounded-2xl bg-white border-2 border-red-200 p-4 md:p-5">
          <h3 className="font-extrabold text-[15.5px] text-red-800 mb-2">⚠ Điểm nghẽn cần xử lý</h3>
          {[
            ["Thông quan Hữu Nghị chậm 1,5 ngày", "LO-0306 thiếu tờ khai — xử lý trước 17:00", "/lo-hang/LO-0306?tab=nhap"],
            ["Xe TQ LO-0308 chưa chốt", "Nhà máy cần trước 24h — gọi Bằng Tường ngay", "/lo-hang/LO-0308?tab=lay-hang"],
            ["Công nợ An Phát 336,5 tr hạn hôm nay", "Thu tạm ứng đợt 2 — Minh Anh phụ trách", "/tai-chinh/thu-tien"],
          ].map(([t, d, to]) => (
            <Link key={t as string} to={to as string} className="flex items-center gap-3 rounded-xl border border-red-100 hover:border-red-400 p-3 mb-2">
              <span className="w-2 h-10 rounded-full bg-red-500 shrink-0" />
              <span className="flex-1"><span className="block font-bold text-[14.5px]">{t}</span><span className="block text-[13px] text-slate-500">{d}</span></span>
              <ArrowRight size={17} className="text-slate-300 shrink-0" />
            </Link>
          ))}
        </section>
      </div>
    </div>
  );
}
