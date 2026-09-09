import { Link, useNavigate } from "react-router-dom";
import { Truck, FileCheck2, PackageCheck, Wallet, FileWarning, ArrowRight, Clock, CircleAlert } from "lucide-react";
import { ToneBadge, SectionTitle, NextActionBanner, StatusDot } from "../components/ui";
import { useStore } from "../lib/store";
import { cx } from "../lib/format";

const NEXT = [
  { icon: Truck, title: "Lô cần lấy hàng", count: 1, desc: "LO-0308 · Minh Đức — thiếu xe TQ", to: "/lo-hang/LO-0308?tab=lay-hang", cta: "Chốt xe ngay", bg: "bg-slate-600", bar: "bg-slate-500" },
  { icon: FileCheck2, title: "Lô cần thông quan", count: 1, desc: "LO-0306 · An Phát — thiếu số tờ khai", to: "/lo-hang/LO-0306?tab=nhap", cta: "Khai báo ngay", bg: "bg-amber-500", bar: "bg-amber-500" },
  { icon: PackageCheck, title: "Lô cần giao", count: 1, desc: "LO-0299 · Hồng Hà — giao 14:00 hôm nay", to: "/lo-hang/LO-0299?tab=nhap", cta: "Xem lịch giao", bg: "bg-blue-600", bar: "bg-blue-500" },
  { icon: Wallet, title: "Khoản cần thu", count: 3, desc: "Còn phải thu 537,6 tr — 1 khoản hạn hôm nay", to: "/tai-chinh/thu-tien", cta: "Thu tiền", bg: "bg-emerald-600", bar: "bg-emerald-500" },
  { icon: FileWarning, title: "Hồ sơ thiếu chứng từ", count: 4, desc: "CO form E, Packing List, Ngày HDMB…", to: "/viec-can-xu-ly", cta: "Bổ sung", bg: "bg-red-500", bar: "bg-red-500" },
];

export default function Home() {
  const { shipments } = useStore();
  const nav = useNavigate();
  // Router adaptation (allowed): component-local navigation instead of the
  // donor's full-page window.location.href — same destination, no page reload.
  return (
    <div className="space-y-5 max-w-[1200px]">
      <div className="rounded-3xl bg-gradient-to-br from-[#0a1f3a] via-[#0f2a4a] to-[#1e5aa8] text-white p-5 md:p-7 relative overflow-hidden">
        <div className="absolute -right-16 -top-16 w-64 h-64 rounded-full bg-white/10" />
        <div className="absolute right-10 bottom-0 w-32 h-32 rounded-full bg-white/5" />
        <p className="text-[13px] font-semibold text-blue-200 uppercase tracking-wider">Thứ Tư · 09/09/2026 · Ca sáng</p>
        <h1 className="text-[22px] md:text-[30px] font-extrabold leading-tight mt-1">Hôm nay tôi cần làm gì?</h1>
        <p className="text-[14.5px] md:text-[16px] text-blue-100 mt-1.5 max-w-[640px]">3 việc khẩn trước 17:00 — bắt đầu từ <b className="text-white">LO-0306 thiếu tờ khai</b>, sau đó <b className="text-white">giao LO-0299 lúc 14:00</b>.</p>
        <div className="flex flex-wrap gap-2.5 mt-4">
          <Link to="/viec-can-xu-ly" className="btn-press touch-target inline-flex items-center gap-2 rounded-xl bg-white text-[#0f2a4a] font-extrabold text-[15px] px-5 min-h-[48px]">XỬ LÝ NGAY <ArrowRight size={18} /></Link>
          <Link to="/lo-hang/LO-0306?tab=nhap" className="btn-press touch-target inline-flex items-center gap-2 rounded-xl border-2 border-white/40 text-white font-bold text-[15px] px-5 min-h-[48px]">Mở LO-0306</Link>
        </div>
      </div>

      <NextActionBanner tone="red" title="LO-0306: bổ sung số tờ khai nhập khẩu trước 17:00 hôm nay" desc="Hiện trạng: hàng đã về bãi Hữu Nghị VN · Còn thiếu: số tờ khai + biên lai thuế · Phụ trách: Thu Hằng" action="XỬ LÝ NGAY" onAction={() => { nav("/lo-hang/LO-0306?tab=nhap"); }} />

      <section>
        <SectionTitle title="VIỆC TIẾP THEO" sub="Bấm vào từng thẻ để đi thẳng tới màn hình xử lý" />
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-5 gap-3">
          {NEXT.map((n) => (
            <Link key={n.title} to={n.to} className="lift btn-press rounded-2xl bg-white border border-slate-200 overflow-hidden flex sm:flex-col min-h-[88px]">
              <div className={cx("w-1.5 sm:w-full sm:h-1.5 shrink-0", n.bar)} />
              <div className="p-3.5 flex items-center sm:items-start gap-3 sm:flex-col sm:gap-2 flex-1">
                <span className={cx("w-11 h-11 rounded-xl text-white grid place-items-center shrink-0", n.bg)}><n.icon size={21} /></span>
                <div className="flex-1 min-w-0">
                  <p className="font-extrabold text-[15px] text-[#0f2a4a] flex items-center gap-2">{n.title} <span className="text-[12px] font-extrabold bg-red-600 text-white rounded-full min-w-[24px] h-6 px-1.5 grid place-items-center">{n.count}</span></p>
                  <p className="text-[13px] text-slate-500 mt-0.5 leading-snug">{n.desc}</p>
                  <span className="inline-flex items-center gap-1 text-[13.5px] font-bold text-[#1e5aa8] mt-1.5">{n.cta} <ArrowRight size={15} /></span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </section>

      <section>
        <SectionTitle title="Chỉ số vận hành hôm nay" sub="Chỉ hiện số liệu giúp ra quyết định — bấm để lọc danh sách" />
        <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-5 gap-3">
          {[
            { label: "Lô đang chạy", value: "4", sub: "0306 · 0307 · 0308 · 0299", to: "/lo-hang" },
            { label: "Chờ lấy hàng", value: "1", sub: "LO-0308", to: "/lo-hang/LO-0308" },
            { label: "Đang vận chuyển", value: "1", sub: "LO-0307", to: "/lo-hang/LO-0307" },
            { label: "Chờ thông quan", value: "1", sub: "LO-0306", to: "/lo-hang/LO-0306?tab=nhap" },
            { label: "Chờ giao", value: "1", sub: "LO-0299", to: "/lo-hang/LO-0299?tab=nhap" },
            { label: "Đã giao hôm nay", value: "1", sub: "LO-0295 · 07:30", to: "/lo-hang" },
          ].map((k) => (
            <Link key={k.label} to={k.to} className="lift rounded-2xl bg-white border border-slate-200 p-4">
              <p className="text-[13px] font-semibold text-slate-500">{k.label}</p>
              <p className="text-[24px] md:text-[28px] font-extrabold text-[#0f2a4a] leading-tight mt-0.5">{k.value}</p>
              <p className="text-[12.5px] text-slate-400 mt-0.5 truncate">{k.sub}</p>
            </Link>
          ))}
          <Link to="/tai-chinh/thu-tien" className="lift rounded-2xl bg-emerald-600 text-white p-4">
            <p className="text-[13px] font-semibold text-emerald-100">Phải thu còn lại</p>
            <p className="text-[24px] md:text-[26px] font-extrabold leading-tight mt-0.5">537,6 tr ₫</p>
            <p className="text-[12.5px] text-emerald-100 mt-0.5">1 khoản hạn HÔM NAY → thu ngay</p>
          </Link>
          <Link to="/tai-chinh/doi-soat" className="lift rounded-2xl bg-white border-2 border-amber-300 p-4">
            <p className="text-[13px] font-semibold text-slate-500">Phải trả còn lại</p>
            <p className="text-[24px] md:text-[26px] font-extrabold text-[#0f2a4a] leading-tight mt-0.5">73,8 tr ₫</p>
            <p className="text-[12.5px] text-amber-700 font-semibold mt-0.5">Chờ đối soát Bằng Tường</p>
          </Link>
          <Link to="/viec-can-xu-ly" className="lift rounded-2xl bg-red-600 text-white p-4 col-span-2 md:col-span-1">
            <p className="text-[13px] font-semibold text-red-100">Việc quá hạn / khẩn</p>
            <p className="text-[24px] md:text-[28px] font-extrabold leading-tight mt-0.5">3 việc</p>
            <p className="text-[12.5px] text-red-100 mt-0.5">Xử lý trước 17:00 hôm nay</p>
          </Link>
        </div>
      </section>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        <section className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-extrabold text-[16.5px] text-[#0f2a4a] flex items-center gap-2"><Clock size={19} className="text-red-600" /> Quá hạn và sắp tới hạn</h3>
            <Link to="/viec-can-xu-ly" className="text-[13.5px] font-bold text-[#1e5aa8] inline-flex items-center gap-1">Tất cả <ArrowRight size={15} /></Link>
          </div>
          <div className="space-y-2.5">
            {[
              { lot: "LO-0306", job: "Khai tờ khai nhập khẩu + nộp thuế", due: "Hạn 17:00 hôm nay", tone: "bg-red-500", to: "/lo-hang/LO-0306?tab=nhap" },
              { lot: "LO-0299", job: "Giao hàng Yên Phong + xác nhận đã giao", due: "14:00 hôm nay", tone: "bg-amber-500", to: "/lo-hang/LO-0299?tab=nhap" },
              { lot: "LO-0308", job: "Chốt xe TQ + giờ lấy hàng", due: "12:00 hôm nay", tone: "bg-amber-500", to: "/lo-hang/LO-0308?tab=lay-hang" },
            ].map((t) => (
              <Link key={t.lot} to={t.to} className="flex items-center gap-3 rounded-xl border border-slate-200 hover:border-[#1e5aa8] p-3 lift">
                <span className={cx("w-2.5 h-10 rounded-full shrink-0", t.tone)} />
                <span className="flex-1 min-w-0"><span className="block font-bold text-[14.5px] text-[#0f2a4a]">{t.lot} · {t.job}</span><span className="block text-[13px] text-slate-500">{t.due}</span></span>
                <span className="touch-target inline-flex items-center text-[13.5px] font-bold text-[#1e5aa8]">Xử lý <ArrowRight size={15} /></span>
              </Link>
            ))}
          </div>
        </section>
        <section className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-extrabold text-[16.5px] text-[#0f2a4a]">Trạng thái các lô đang chạy</h3>
            <Link to="/lo-hang" className="text-[13.5px] font-bold text-[#1e5aa8] inline-flex items-center gap-1">Tất cả lô <ArrowRight size={15} /></Link>
          </div>
          <div className="space-y-2.5">
            {shipments.map((s) => (
              <Link key={s.id} to={"/lo-hang/" + s.id} className="flex items-center gap-3 rounded-xl border border-slate-200 hover:border-[#1e5aa8] p-3 lift">
                <StatusDot tone={s.statusTone} />
                <span className="flex-1 min-w-0"><span className="block font-bold text-[14.5px] text-[#0f2a4a]">{s.id} · {s.customer}</span><span className="block text-[13px] text-slate-500 truncate">Tiếp theo: {s.nextAction}</span></span>
                <ToneBadge tone={s.statusTone} size="sm">{s.status}</ToneBadge>
              </Link>
            ))}
          </div>
          <div className="mt-3 rounded-xl bg-blue-50 border border-blue-200 p-3 flex items-start gap-2">
            <CircleAlert size={17} className="text-blue-700 mt-0.5 shrink-0" />
            <p className="text-[13.5px] text-blue-900"><b>Luồng gợi ý:</b> Tổng quan → mở lô → xử lý việc tiếp theo → hợp đồng → xuất chứng từ → thu tiền.</p>
          </div>
        </section>
      </div>

      <section className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-extrabold text-[16.5px] text-[#0f2a4a]">Tiền hôm nay — hiện trạng → việc thiếu → hành động</h3>
          <Link to="/tai-chinh/thu-tien" className="text-[13.5px] font-bold text-[#1e5aa8] inline-flex items-center gap-1">Mở tài chính <ArrowRight size={15} /></Link>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div className="rounded-xl bg-emerald-50 border border-emerald-200 p-4">
            <p className="text-[13px] font-semibold text-emerald-800">Còn phải thu · 537.600.000 ₫</p>
            <p className="text-[13.5px] text-emerald-900 mt-1">Thiếu: tạm ứng đợt 2 LO-0306 (150 tr, hạn hôm nay)</p>
            <Link to="/tai-chinh/thu-tien" className="btn-press touch-target mt-2.5 flex items-center justify-center rounded-lg bg-emerald-600 text-white font-bold text-[14.5px] px-4 min-h-[44px]">GHI NHẬN THANH TOÁN</Link>
          </div>
          <div className="rounded-xl bg-amber-50 border border-amber-200 p-4">
            <p className="text-[13px] font-semibold text-amber-800">Còn phải trả · 73.800.000 ₫</p>
            <p className="text-[13.5px] text-amber-900 mt-1">Thiếu: đối soát cước xe TQ Bằng Tường tháng 9</p>
            <Link to="/tai-chinh/doi-soat" className="btn-press touch-target mt-2.5 flex items-center justify-center rounded-lg bg-amber-500 text-white font-bold text-[14.5px] px-4 min-h-[44px]">ĐỐI SOÁT NGAY</Link>
          </div>
          <div className="rounded-xl bg-blue-50 border border-blue-200 p-4">
            <p className="text-[13px] font-semibold text-blue-800">Đã thu hôm nay · 0 ₫</p>
            <p className="text-[13.5px] text-blue-900 mt-1">Chưa ghi nhận khoản nào — thu LO-0306 để bắt đầu</p>
            <Link to="/tai-chinh/thu-tien" className="btn-press touch-target mt-2.5 flex items-center justify-center rounded-lg bg-[#0f2a4a] text-white font-bold text-[14.5px] px-4 min-h-[44px]">MỞ SỔ THU TIỀN</Link>
          </div>
        </div>
      </section>
    </div>
  );
}
