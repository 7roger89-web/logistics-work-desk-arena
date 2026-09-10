import { Link, useNavigate } from "react-router-dom";
import { Truck, FileCheck2, PackageCheck, Wallet, FileWarning, ArrowRight, Clock, CircleAlert } from "lucide-react";
import { ToneBadge, SectionTitle, NextActionBanner, StatusDot } from "../components/ui";
import { useStore } from "../lib/store";
import { cx, fmtMillions, fmtText } from "../lib/format";

// Phase B: the donor composition is frozen — only the numbers moved. Every
// value below comes from the real Logistics view-model (home projection over
// the current readers). There is no fabricated KPI.
const TILE_ICON: Record<string, { icon: typeof Truck; bg: string; bar: string }> = {
  "Lô đang chạy": { icon: Truck, bg: "bg-slate-600", bar: "bg-slate-500" },
  "Chờ lấy hàng": { icon: PackageCheck, bg: "bg-slate-600", bar: "bg-slate-500" },
  "Đang vận chuyển": { icon: Truck, bg: "bg-blue-600", bar: "bg-blue-500" },
  "Chờ thông quan": { icon: FileCheck2, bg: "bg-amber-500", bar: "bg-amber-500" },
  "Chờ giao": { icon: PackageCheck, bg: "bg-blue-600", bar: "bg-blue-500" },
  "Đã giao": { icon: FileCheck2, bg: "bg-emerald-600", bar: "bg-emerald-500" },
};
const FALLBACK_TILE = { icon: FileWarning, bg: "bg-red-500", bar: "bg-red-500" };

export default function Home() {
  const { shipments, home, tasks, environment } = useStore();
  const nav = useNavigate();

  const tiles = home?.tiles ?? [];
  const focus = home?.focus ?? null;
  const summary = home?.summary;
  // Real overdue/upcoming work, straight from the readiness evidence.
  const dueSoon = (tasks ?? []).slice(0, 3);
  const running = (home?.runningSummary ?? []);
  const today = new Date().toLocaleDateString("vi-VN", { weekday: "long", day: "2-digit", month: "2-digit", year: "numeric" });

  return (
    <div className="space-y-5 max-w-[1200px]">
      <div className="rounded-3xl bg-gradient-to-br from-[#0a1f3a] via-[#0f2a4a] to-[#1e5aa8] text-white p-5 md:p-7 relative overflow-hidden">
        <div className="absolute -right-16 -top-16 w-64 h-64 rounded-full bg-white/10" />
        <div className="absolute right-10 bottom-0 w-32 h-32 rounded-full bg-white/5" />
        <p className="text-[13px] font-semibold text-blue-200 uppercase tracking-wider">{today}{environment?.isSandbox ? ` · ${environment.label}` : ""}</p>
        <h1 className="text-[22px] md:text-[30px] font-extrabold leading-tight mt-1">Hôm nay tôi cần làm gì?</h1>
        <p className="text-[14.5px] md:text-[16px] text-blue-100 mt-1.5 max-w-[640px]">
          {focus
            ? <>{home?.urgentCount ?? 0} việc khẩn · bắt đầu từ <b className="text-white">{focus.id} — {focus.nextAction}</b>.</>
            : "Không có việc khẩn. Toàn bộ lô hàng đang ổn định."}
        </p>
        <div className="flex flex-wrap gap-2.5 mt-4">
          <Link to="/viec-can-xu-ly" className="btn-press touch-target inline-flex items-center gap-2 rounded-xl bg-white text-[#0f2a4a] font-extrabold text-[15px] px-5 min-h-[48px]">XỬ LÝ NGAY <ArrowRight size={18} /></Link>
          {focus && <Link to={`/lo-hang/${focus.id}`} className="btn-press touch-target inline-flex items-center gap-2 rounded-xl border-2 border-white/40 text-white font-bold text-[15px] px-5 min-h-[48px]">Mở {focus.id}</Link>}
        </div>
      </div>

      {focus && (
        <NextActionBanner
          tone={focus.priority === "Khan" ? "red" : "amber"}
          title={`${focus.id}: ${focus.nextAction}`}
          desc={fmtText(focus.nextActionDetail)}
          action="XỬ LÝ NGAY"
          onAction={() => { nav(focus.to); }}
        />
      )}

      <section>
        <SectionTitle title="VIỆC TIẾP THEO" sub="Bấm vào từng thẻ để đi thẳng tới màn hình xử lý" />
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-5 gap-3">
          {tiles.map((t) => {
            const visual = TILE_ICON[t.label] ?? FALLBACK_TILE;
            const Icon = visual.icon;
            return (
              <Link key={t.label} to={t.to} className="lift btn-press rounded-2xl bg-white border border-slate-200 overflow-hidden flex sm:flex-col min-h-[88px]">
                <div className={cx("w-1.5 sm:w-full sm:h-1.5 shrink-0", visual.bar)} />
                <div className="p-3.5 flex items-center sm:items-start gap-3 sm:flex-col sm:gap-2 flex-1">
                  <span className={cx("w-11 h-11 rounded-xl text-white grid place-items-center shrink-0", visual.bg)}><Icon size={21} /></span>
                  <div className="flex-1 min-w-0">
                    <p className="font-extrabold text-[15px] text-[#0f2a4a] flex items-center gap-2">{t.label} <span className="text-[12px] font-extrabold bg-red-600 text-white rounded-full min-w-[24px] h-6 px-1.5 grid place-items-center">{t.value}</span></p>
                    <p className="text-[13px] text-slate-500 mt-0.5 leading-snug truncate">{t.sub}</p>
                    <span className="inline-flex items-center gap-1 text-[13.5px] font-bold text-[#1e5aa8] mt-1.5">Xem lô <ArrowRight size={15} /></span>
                  </div>
                </div>
              </Link>
            );
          })}
        </div>
      </section>

      <section>
        <SectionTitle title="Chỉ số vận hành hôm nay" sub="Chỉ hiện số liệu giúp ra quyết định — bấm để lọc danh sách" />
        <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-5 gap-3">
          {tiles.map((k) => (
            <Link key={k.label} to={k.to} className="lift rounded-2xl bg-white border border-slate-200 p-4">
              <p className="text-[13px] font-semibold text-slate-500">{k.label}</p>
              <p className="text-[24px] md:text-[28px] font-extrabold text-[#0f2a4a] leading-tight mt-0.5">{k.value}</p>
              <p className="text-[12.5px] text-slate-400 mt-0.5 truncate">{k.sub}</p>
            </Link>
          ))}
          <Link to="/tai-chinh/thu-tien" className="lift rounded-2xl bg-emerald-600 text-white p-4">
            <p className="text-[13px] font-semibold text-emerald-100">Phải thu còn lại</p>
            <p className="text-[24px] md:text-[26px] font-extrabold leading-tight mt-0.5">{fmtMillions(home?.outstandingTotal)}</p>
            <p className="text-[12.5px] text-emerald-100 mt-0.5">{home?.outstandingCount ?? 0} lô còn công nợ</p>
          </Link>
          <Link to="/tai-chinh/doi-soat" className="lift rounded-2xl bg-white border-2 border-amber-300 p-4">
            <p className="text-[13px] font-semibold text-slate-500">Cần đối soát tài chính</p>
            <p className="text-[24px] md:text-[26px] font-extrabold text-[#0f2a4a] leading-tight mt-0.5">{summary?.financialAttention ?? 0}</p>
            <p className="text-[12.5px] text-amber-700 font-semibold mt-0.5">Theo Shipment 360</p>
          </Link>
          <Link to="/viec-can-xu-ly" className="lift rounded-2xl bg-red-600 text-white p-4 col-span-2 md:col-span-1">
            <p className="text-[13px] font-semibold text-red-100">Việc quá hạn / khẩn</p>
            <p className="text-[24px] md:text-[28px] font-extrabold leading-tight mt-0.5">{(summary?.critical ?? 0) + (home?.urgentCount ?? 0)} việc</p>
            <p className="text-[12.5px] text-red-100 mt-0.5">{summary?.deadlineSoon ?? 0} lô sắp tới hạn khách</p>
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
            {dueSoon.length === 0 && <p className="text-[14px] text-slate-500 py-3">Không có việc tới hạn theo readiness hiện tại.</p>}
            {dueSoon.map((t) => (
              <Link key={t.id} to={t.route} className="flex items-center gap-3 rounded-xl border border-slate-200 hover:border-[#1e5aa8] p-3 lift">
                <span className={cx("w-2.5 h-10 rounded-full shrink-0",
                  t.statusTone === "red" ? "bg-red-500" : t.statusTone === "amber" ? "bg-amber-500" : t.statusTone === "blue" ? "bg-blue-500" : "bg-slate-400")} />
                <span className="flex-1 min-w-0"><span className="block font-bold text-[14.5px] text-[#0f2a4a]">{t.lot} · {t.job}</span><span className="block text-[13px] text-slate-500">{fmtText(t.due)} · {fmtText(t.dueNote)}</span></span>
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
            {running.length === 0 && <p className="text-[14px] text-slate-500 py-3">Không có lô nào đang chạy.</p>}
            {running.map((s) => {
              const row = shipments.find((x) => x.id === s.id);
              return (
                <Link key={s.id} to={s.to} className="flex items-center gap-3 rounded-xl border border-slate-200 hover:border-[#1e5aa8] p-3 lift">
                  <StatusDot tone={row?.statusTone ?? "gray"} />
                  <span className="flex-1 min-w-0"><span className="block font-bold text-[14.5px] text-[#0f2a4a]">{s.id} · {s.customer}</span><span className="block text-[13px] text-slate-500 truncate">Tiếp theo: {s.nextAction}</span></span>
                  <ToneBadge tone={row?.statusTone ?? "gray"} size="sm">{s.status}</ToneBadge>
                </Link>
              );
            })}
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
            <p className="text-[13px] font-semibold text-emerald-800">Còn phải thu · {fmtMillions(home?.outstandingTotal)} ₫</p>
            <p className="text-[13.5px] text-emerald-900 mt-1">{home?.outstandingCount ?? 0} lô còn công nợ theo core.logic</p>
            <Link to="/tai-chinh/thu-tien" className="btn-press touch-target mt-2.5 flex items-center justify-center rounded-lg bg-emerald-600 text-white font-bold text-[14.5px] px-4 min-h-[44px]">GHI NHẬN THANH TOÁN</Link>
          </div>
          <div className="rounded-xl bg-amber-50 border border-amber-200 p-4">
            <p className="text-[13px] font-semibold text-amber-800">Cần đối soát · {summary?.financialAttention ?? 0} lô</p>
            <p className="text-[13.5px] text-amber-900 mt-1">Quote Estimate ≠ Finance Actual — đối soát từng lô</p>
            <Link to="/tai-chinh/doi-soat" className="btn-press touch-target mt-2.5 flex items-center justify-center rounded-lg bg-amber-500 text-white font-bold text-[14.5px] px-4 min-h-[44px]">ĐỐI SOÁT NGAY</Link>
          </div>
          <div className="rounded-xl bg-blue-50 border border-blue-200 p-4">
            <p className="text-[13px] font-semibold text-blue-800">Hồ sơ thiếu thông tin · {home?.missingDocsTotal ?? 0}</p>
            <p className="text-[13.5px] text-blue-900 mt-1">{summary?.missingInfo ?? 0} lô thiếu dữ liệu bắt buộc</p>
            <Link to="/viec-can-xu-ly" className="btn-press touch-target mt-2.5 flex items-center justify-center rounded-lg bg-[#0f2a4a] text-white font-bold text-[14.5px] px-4 min-h-[44px]">MỞ DANH SÁCH VIỆC</Link>
          </div>
        </div>
      </section>
    </div>
  );
}
