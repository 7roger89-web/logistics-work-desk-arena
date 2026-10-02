import { Link, useNavigate } from "react-router-dom";
import { Truck, FileCheck2, PackageCheck, FileWarning, ArrowRight, Wallet, Scale, FolderX, ListTodo } from "lucide-react";
import { ToneBadge, SectionTitle, StatusDot } from "../components/ui";
import AttentionNow from "../components/AttentionNow";
import { useStore } from "../lib/store";
import { shipmentPath } from "../lib/shipmentRoute";
import { cx, fmtMillions, fmtText } from "../lib/format";

// LOGI_FRONTEND_WORKFLOW_OVERHAUL_01 — Home is ONE work desk, not three
// stacked variants of the same page. The old composition said the same thing
// twice (a "VIỆC TIẾP THEO" tile row AND a "Chỉ số vận hành hôm nay" KPI row
// over the SAME tiles, plus a hero AND a NextActionBanner for the same
// focus). Now:
//
//   1. ONE priority area (hero states the single most important work + action);
//   2. exception/deadline list + running lots (operational visibility kept);
//   3. ONE compact operational snapshot (each tile rendered exactly once);
//   4. ONE money/docs attention strip with direct actions.
//
// Every number still comes from the backend's home projection — nothing was
// removed from view, only de-duplicated. FUNCTION > DECORATION: no hero
// artwork, no duplicated KPI shells.
const TILE_ICON: Record<string, { icon: typeof Truck; bar: string }> = {
  "Lô đang chạy": { icon: Truck, bar: "bg-slate-500" },
  "Chờ lấy hàng": { icon: PackageCheck, bar: "bg-slate-500" },
  "Đang vận chuyển": { icon: Truck, bar: "bg-blue-500" },
  "Chờ thông quan": { icon: FileCheck2, bar: "bg-amber-500" },
  "Chờ giao": { icon: PackageCheck, bar: "bg-blue-500" },
  "Đã giao": { icon: FileCheck2, bar: "bg-emerald-500" },
};
const FALLBACK_TILE = { icon: FileWarning, bar: "bg-red-500" };

export default function Home() {
  const { shipments, home, attention, environment } = useStore();
  const nav = useNavigate();

  const tiles = home?.tiles ?? [];
  const focus = home?.focus ?? null;
  const summary = home?.summary;
  const running = (home?.runningSummary ?? []);
  const today = new Date().toLocaleDateString("vi-VN", { weekday: "long", day: "2-digit", month: "2-digit", year: "numeric" });
  const urgentTotal = (summary?.critical ?? 0) + (home?.urgentCount ?? 0);

  return (
    <div className="space-y-4 max-w-[1200px]">
      {/* 1 — PRIORITY: what matters most now, with the direct way in */}
      <section className="rounded-2xl bg-gradient-to-br from-[#0a1f3a] via-[#0f2a4a] to-[#1e5aa8] text-white p-4 md:p-5">
        <p className="text-[12.5px] font-semibold text-blue-200 uppercase tracking-wider">{today}{environment?.isSandbox ? ` · ${environment.label}` : ""}</p>
        {focus ? (
          <>
            <h1 className="text-[19px] md:text-[23px] font-extrabold leading-snug mt-1">
              Ưu tiên bây giờ: <span className="text-white">{focus.id} — {focus.nextAction}</span>
            </h1>
            <p className="text-[13.5px] md:text-[14.5px] text-blue-100 mt-1 max-w-[760px]">
              {home?.urgentCount ?? 0} việc khẩn · {fmtText(focus.nextActionDetail)}
            </p>
            <div className="flex flex-wrap gap-2.5 mt-3.5">
              <button onClick={() => nav(focus.to)} className="btn-press touch-target inline-flex items-center gap-2 rounded-xl bg-white text-[#0f2a4a] font-extrabold text-[15px] px-5 min-h-[48px]">XỬ LÝ NGAY <ArrowRight size={18} /></button>
              <button onClick={() => nav(shipmentPath(focus.id))} className="btn-press touch-target inline-flex items-center gap-2 rounded-xl border-2 border-white/40 text-white font-bold text-[15px] px-5 min-h-[48px]">Mở {focus.id}</button>
              <Link to="/lo-hang" className="btn-press touch-target inline-flex items-center rounded-xl text-white/90 font-bold text-[14px] px-4 min-h-[48px] underline decoration-white/40 underline-offset-4">Xem tất cả lô hàng</Link>
            </div>
          </>
        ) : (
          <>
            <h1 className="text-[19px] md:text-[23px] font-extrabold leading-snug mt-1">Chưa có việc cần xử lý theo dữ liệu hiện có.</h1>
            <div className="flex flex-wrap gap-2.5 mt-3.5">
              <Link to="/lo-hang" className="btn-press touch-target inline-flex items-center gap-2 rounded-xl bg-white text-[#0f2a4a] font-extrabold text-[15px] px-5 min-h-[48px]">Mở danh sách lô <ArrowRight size={18} /></Link>
            </div>
          </>
        )}
      </section>

      {/* 2 — EXCEPTIONS + OPERATIONAL VISIBILITY: deadlines first, running lots beside */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        <AttentionNow
          items={(attention ?? []).slice(home?.focus ? 1 : 0, home?.focus ? 5 : 4)}
          title="Cần xử lý tiếp"
          compact
        />
        <section className="rounded-2xl bg-white border border-slate-200 p-4">
          <div className="flex items-center justify-between mb-2.5">
            <h3 className="font-extrabold text-[16px] text-[#0f2a4a]">Trạng thái các lô đang chạy</h3>
            <Link to="/lo-hang" className="text-[13px] font-bold text-[#1e5aa8] inline-flex items-center gap-1">Tất cả lô <ArrowRight size={14} /></Link>
          </div>
          <div className="space-y-2">
            {running.length === 0 && <p className="text-[14px] text-slate-500 py-2">Không có lô nào đang chạy.</p>}
            {running.map((s) => {
              const row = shipments.find((x) => x.id === s.id);
              return (
                <Link key={s.id} to={s.to} className="flex items-center gap-3 rounded-xl border border-slate-200 hover:border-[#1e5aa8] p-2.5 lift">
                  <StatusDot tone={row?.statusTone ?? "gray"} />
                  <span className="flex-1 min-w-0"><span className="block font-bold text-[14px] text-[#0f2a4a]">{s.id} · {s.customer}</span><span className="block text-[12.5px] text-slate-500 truncate">Tiếp theo: {s.nextAction}</span></span>
                  <ToneBadge tone={row?.statusTone ?? "gray"} size="sm">{s.status}</ToneBadge>
                </Link>
              );
            })}
          </div>
        </section>
      </div>

      {/* 3 — OPERATIONAL SNAPSHOT: each pipeline state appears exactly once */}
      <section>
        <SectionTitle title="Ảnh vận hành hôm nay" sub="Số liệu thật từ Logistics — bấm một ô để mở đúng danh sách lô" />
        <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-2.5" data-testid="home-snapshot">
          {tiles.map((k) => {
            const visual = TILE_ICON[k.label] ?? FALLBACK_TILE;
            const Icon = visual.icon;
            return (
              <Link key={k.label} to={k.to} className="lift btn-press rounded-2xl bg-white border border-slate-200 p-3 flex flex-col gap-1.5" title={k.sub}>
                <span className="flex items-center gap-1.5 text-[12.5px] font-semibold text-slate-500 truncate"><span className={cx("w-1.5 h-4 rounded-full shrink-0", visual.bar)} /><Icon size={15} className="shrink-0 text-slate-400" />{k.label}</span>
                <span className="tnum text-[22px] md:text-[24px] font-extrabold text-[#0f2a4a] leading-none">{k.value}</span>
                <span className="text-[12px] text-slate-400 leading-snug line-clamp-2 min-h-[2em]">{k.sub}</span>
              </Link>
            );
          })}
        </div>
      </section>

      {/* 4 — MONEY & DOCS ATTENTION: current state → the direct action */}
      <section>
        <SectionTitle title="Tiền & hồ sơ cần chú ý" sub="Hiện trạng → việc thiếu → bấm để xử lý ngay" />
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-3">
          <div className="rounded-xl bg-emerald-50 border border-emerald-200 p-3.5 flex flex-col">
            <p className="text-[12.5px] font-semibold text-emerald-800 flex items-center gap-1.5"><Wallet size={15} /> Còn phải thu · <span className="tnum font-extrabold">{fmtMillions(home?.outstandingTotal)} ₫</span></p>
            <p className="text-[13px] text-emerald-900 mt-1 flex-1">{home?.outstandingCount ?? 0} lô còn công nợ theo core.logic</p>
            <Link to="/tai-chinh/thu-tien" className="btn-press touch-target mt-2.5 flex items-center justify-center rounded-lg bg-emerald-600 text-white font-bold text-[14px] px-4 min-h-[44px]">GHI NHẬN THANH TOÁN</Link>
          </div>
          <div className="rounded-xl bg-amber-50 border border-amber-200 p-3.5 flex flex-col">
            <p className="text-[12.5px] font-semibold text-amber-800 flex items-center gap-1.5"><Scale size={15} /> Cần đối soát · <span className="tnum font-extrabold">{summary?.financialAttention ?? 0} lô</span></p>
            <p className="text-[13px] text-amber-900 mt-1 flex-1">Quote Estimate ≠ Finance Actual — đối soát từng lô</p>
            <Link to="/tai-chinh/doi-soat" className="btn-press touch-target mt-2.5 flex items-center justify-center rounded-lg bg-amber-500 text-white font-bold text-[14px] px-4 min-h-[44px]">ĐỐI SOÁT NGAY</Link>
          </div>
          <div className="rounded-xl bg-blue-50 border border-blue-200 p-3.5 flex flex-col">
            <p className="text-[12.5px] font-semibold text-blue-800 flex items-center gap-1.5"><FolderX size={15} /> Hồ sơ thiếu thông tin · <span className="tnum font-extrabold">{home?.missingDocsTotal ?? 0}</span></p>
            <p className="text-[13px] text-blue-900 mt-1 flex-1">{summary?.missingInfo ?? 0} lô thiếu dữ liệu bắt buộc</p>
            <Link to="/lo-hang" className="btn-press touch-target mt-2.5 flex items-center justify-center rounded-lg bg-[#0f2a4a] text-white font-bold text-[14px] px-4 min-h-[44px]">MỞ DANH SÁCH LÔ</Link>
          </div>
          <div className="rounded-xl bg-red-50 border border-red-200 p-3.5 flex flex-col">
            <p className="text-[12.5px] font-semibold text-red-800 flex items-center gap-1.5"><ListTodo size={15} /> Việc quá hạn / khẩn · <span className="tnum font-extrabold">{urgentTotal} việc</span></p>
            <p className="text-[13px] text-red-900 mt-1 flex-1">{summary?.deadlineSoon ?? 0} lô sắp tới hạn khách</p>
            <Link to="/lo-hang" className="btn-press touch-target mt-2.5 flex items-center justify-center rounded-lg bg-red-600 text-white font-bold text-[14px] px-4 min-h-[44px]">MỞ LÔ HÀNG</Link>
          </div>
        </div>
      </section>
    </div>
  );
}
