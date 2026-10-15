import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { shipmentPath } from "../lib/shipmentRoute";
import { useQueryParam } from "../lib/queryParam";
import { Search, ArrowRight, Eye, SlidersHorizontal } from "lucide-react";
import { SectionTitle, ToneBadge, StatusDot } from "../components/ui";
import { ShipmentQuickFacts } from "../components/ShipmentQuickFacts";
import { useStore } from "../lib/store";
import { cx } from "../lib/format";
import { createdTs } from "../lib/costHistory";
import type { Shipment } from "../lib/viewmodel";
import GetFlyImport from "../components/GetFlyImport";

/**
 * LOGI_QUOTE_COST_WORKFLOW_UX_01 — "đã hoàn tất & thanh toán" is DERIVED, never
 * a stored flag and never a delete.
 *
 * A lot only counts as finished+paid when BOTH facts are KNOWN:
 *   operational completion/delivery is known complete, AND
 *   receivable/outstanding is known AND equals 0.
 * An UNKNOWN outstanding (null) is NOT paid: it stays in "Đang làm".
 */
export function isSettled(s: Shipment): boolean {
  const delivered = Boolean(s.importInfo?.delivered) || Boolean(s.importInfo?.actualDelivery);
  const outstanding = s.finance?.outstanding;
  if (outstanding == null || Number.isNaN(Number(outstanding))) return false; // UNKNOWN != paid
  return delivered && Number(outstanding) === 0;
}

type PeriodId = "thang-nay" | "thang-truoc" | "nam-nay" | "khac" | "tat-ca";

const PERIODS: Array<{ id: PeriodId; label: string }> = [
  { id: "thang-nay", label: "Tháng này" },
  { id: "thang-truoc", label: "Tháng trước" },
  { id: "nam-nay", label: "Năm nay" },
  { id: "khac", label: "Thời gian khác" },
];

/** Inclusive [from, to) UTC-midnight bounds for the operator's LOCAL calendar period. */
export function periodBounds(period: PeriodId, now: Date, from: string, to: string): [number, number] | null {
  // The shipment date is a date-only business fact. Pick the named month/year
  // from the browser's local calendar, then express those date-only boundaries
  // at UTC midnight so they compare directly with createdTs(). Using getUTC*
  // here makes 00:xx on the first day in UTC+7 still look like LAST month.
  const y = now.getFullYear();
  const m = now.getMonth();
  if (period === "thang-nay") return [Date.UTC(y, m, 1), Date.UTC(y, m + 1, 1)];
  if (period === "thang-truoc") return [Date.UTC(y, m - 1, 1), Date.UTC(y, m, 1)];
  if (period === "nam-nay") return [Date.UTC(y, 0, 1), Date.UTC(y + 1, 0, 1)];
  if (period === "khac") {
    const start = from ? Date.parse(`${from}T00:00:00Z`) : Number.NEGATIVE_INFINITY;
    const end = to ? Date.parse(`${to}T00:00:00Z`) + 86_400_000 : Number.POSITIVE_INFINITY;
    if (Number.isNaN(start) || Number.isNaN(end)) return null;
    return [start, end];
  }
  return null; // "tất cả"
}

export default function Shipments() {
  const { shipments, attention } = useStore();
  // LOGI_FRONTEND_WORKFLOW_OVERHAUL_01 — query/status live in the route's own
  // search params: lọc → mở lô → Quay lại restores the exact list context.
  const [q, setQ] = useQueryParam("q");
  const [statusRaw, setStatusRaw] = useQueryParam("status");
  const status = statusRaw || "ALL";
  const setStatus = (v: string) => setStatusRaw(v === "ALL" ? "" : v);
  // Returning from a record with an active status filter re-opens the filter
  // panel, so the restored context is VISIBLE, not just applied silently.
  const [showFilter, setShowFilter] = useState(() => statusRaw !== "");

  // LOGI_QUOTE_COST_WORKFLOW_UX_01 — period + archive live in the SAME search
  // params convention as q/status, so Back restores the exact list context.
  // Defaults (no params): THÁNG NÀY + ĐANG LÀM. Nothing is deleted or migrated.
  const [periodRaw, setPeriodRaw] = useQueryParam("period");
  const period = (PERIODS.some((p) => p.id === periodRaw) || periodRaw === "tat-ca"
    ? periodRaw : "thang-nay") as PeriodId;
  const setPeriod = (v: PeriodId) => setPeriodRaw(v === "thang-nay" ? "" : v);
  const [dateFrom, setDateFrom] = useQueryParam("from");
  const [dateTo, setDateTo] = useQueryParam("to");
  const [archiveRaw, setArchiveRaw] = useQueryParam("archive");
  const archive = (["dang-lam", "hoan-tat", "tat-ca"].includes(archiveRaw) ? archiveRaw : "dang-lam") as
    "dang-lam" | "hoan-tat" | "tat-ca";
  const setArchive = (v: string) => setArchiveRaw(v === "dang-lam" ? "" : v);

  const bounds = useMemo(
    () => periodBounds(period, new Date(), dateFrom, dateTo),
    [period, dateFrom, dateTo]
  );

  const list = useMemo(() => shipments.filter((s) => {
    if (!(status === "ALL" || s.status === status)) return false;
    if (q && !(s.id + s.customer + s.contract + s.route + s.sale + s.support).toLowerCase().includes(q.toLowerCase())) return false;
    // Canonical shipment-created authority: `createdAt` (the same field the lot
    // header edits through shipment_field_save). A named/custom date period is
    // a positive inclusion rule: only a KNOWN, parseable creation date inside
    // the requested range belongs in it. Unknown dates remain reachable through
    // "Tất cả thời gian" instead of leaking into every month.
    if (bounds) {
      const ts = createdTs(s.createdAt);
      if (!ts || !(ts >= bounds[0] && ts < bounds[1])) return false;
    }
    const settled = isSettled(s);
    if (archive === "dang-lam" && settled) return false;
    if (archive === "hoan-tat" && !settled) return false;
    return true;
  }), [shipments, q, status, bounds, archive]);
  const statuses = ["ALL", ...Array.from(new Set(shipments.map((s) => s.status)))];

  // Issue #190 — list urgency comes ONLY from the canonical Attention bands.
  // We do not infer urgency from wording such as "free time", ETD/ETA text, or
  // red-looking labels. A small pulse is reserved for BLOCKING/OVERDUE and the
  // global prefers-reduced-motion rule disables it when requested.
  const alertByShipment = useMemo(() => {
    const rank: Record<string, number> = { BLOCKING: 0, OVERDUE: 1, DUE_SOON: 2 };
    const out = new Map<string, { band: string; reason: string }>();
    for (const item of attention ?? []) {
      if (!(item.band in rank)) continue;
      const current = out.get(item.shipmentId);
      if (!current || rank[item.band] < rank[current.band]) {
        out.set(item.shipmentId, { band: item.band, reason: item.reason || item.action || "" });
      }
    }
    return out;
  }, [attention]);

  const nextActionCell = (s: Shipment) => {
    const signal = alertByShipment.get(s.id);
    const urgent = signal?.band === "BLOCKING" || signal?.band === "OVERDUE";
    const dueSoon = signal?.band === "DUE_SOON";
    return <div className={cx("rounded-lg px-2 py-1.5 -mx-2 -my-1.5", urgent && "bg-red-50", dueSoon && "bg-amber-50")}>
      {signal && <span className={cx("mb-1 inline-flex items-center gap-1.5 text-[11px] font-extrabold uppercase tracking-wide",
        urgent ? "text-red-700" : "text-amber-700")}>
        <span className={cx("h-2 w-2 rounded-full", urgent ? "bg-red-600 pulse-dot" : "bg-amber-500")} aria-hidden="true" />
        {signal.band === "BLOCKING" ? "Đang chặn" : signal.band === "OVERDUE" ? "Quá hạn" : "Sắp tới hạn"}
      </span>}
      <span className={cx("block font-semibold text-[13.5px]", urgent && "text-red-900")}>{s.nextAction}</span>
    </div>;
  };

  return (
    <div className="space-y-4 max-w-[1300px]">
      <GetFlyImport />
      <div className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5">
        <SectionTitle title="Lô Hàng" sub="Tìm theo mã lô · khách · container · hợp đồng · trạng thái · Sale · Support · tuyến · cửa khẩu" right={<Link to="/tao-lo-moi" className="btn-press touch-target hidden sm:inline-flex items-center gap-1.5 rounded-xl bg-[#0f2a4a] text-white font-bold text-[14.5px] px-4 min-h-[48px]">＋ Tạo lô mới</Link>} />
        <div className="flex gap-2">
          <div className="flex items-center flex-1 rounded-xl border-2 border-slate-200 focus-within:border-[#1e5aa8] bg-slate-50 overflow-hidden">
            <Search size={19} className="ml-3.5 text-slate-400 shrink-0" />
            <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Nhập mã lô (LO-0306), khách (An Phát), hợp đồng…" className="w-full bg-transparent px-3 py-3 text-[15px] outline-none" />
          </div>
          <button onClick={() => setShowFilter((v) => !v)} className={cx("touch-target shrink-0 inline-flex items-center gap-1.5 rounded-xl border-2 px-4 min-h-[52px] text-[14.5px] font-bold", showFilter ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 bg-white")}><SlidersHorizontal size={18} /> <span className="hidden sm:inline">Lọc</span></button>
        </div>
        {/* Period + archive: derived views only. No DB flag, no delete. */}
        <div className="flex flex-wrap gap-2 mt-2.5" data-testid="shipment-period-controls">
          {[...PERIODS, { id: "tat-ca" as PeriodId, label: "Tất cả thời gian" }].map((p) => (
            <button
              key={p.id}
              onClick={() => setPeriod(p.id)}
              aria-pressed={period === p.id}
              data-testid={`shipment-period-${p.id}`}
              className={cx("touch-target shrink-0 rounded-full border-2 px-3.5 min-h-[44px] text-[13.5px] font-bold whitespace-nowrap",
                period === p.id ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 bg-white text-slate-600")}
            >
              {p.label}
            </button>
          ))}
        </div>
        {period === "khac" && (
          <div className="flex flex-wrap items-end gap-2 mt-2" data-testid="shipment-period-custom">
            <label className="text-[13px] font-semibold text-slate-600">
              Từ ngày
              <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)}
                data-testid="shipment-date-from"
                className="block mt-1 rounded-xl border-2 border-slate-200 bg-white px-3 min-h-[44px] text-[14px]" />
            </label>
            <label className="text-[13px] font-semibold text-slate-600">
              Đến ngày
              <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)}
                data-testid="shipment-date-to"
                className="block mt-1 rounded-xl border-2 border-slate-200 bg-white px-3 min-h-[44px] text-[14px]" />
            </label>
          </div>
        )}
        <div className="flex flex-wrap gap-2 mt-2" role="group" aria-label="Kho lưu" data-testid="shipment-archive-controls">
          {[
            { id: "dang-lam", label: "Đang làm" },
            { id: "hoan-tat", label: "Đã hoàn tất & thanh toán" },
            { id: "tat-ca", label: "Tất cả" },
          ].map((a) => (
            <button
              key={a.id}
              onClick={() => setArchive(a.id)}
              aria-pressed={archive === a.id}
              data-testid={`shipment-archive-${a.id}`}
              className={cx("touch-target shrink-0 rounded-full border-2 px-3.5 min-h-[44px] text-[13.5px] font-bold whitespace-nowrap",
                archive === a.id ? "border-emerald-600 bg-emerald-600 text-white" : "border-slate-200 bg-white text-slate-600")}
            >
              {a.label}
            </button>
          ))}
        </div>
        {showFilter && (
          <div className="flex gap-2 mt-2.5 overflow-x-auto no-scrollbar pb-1">
            {statuses.map((s) => (
              <button key={s} onClick={() => setStatus(s)} className={cx("touch-target shrink-0 rounded-full border-2 px-4 min-h-[44px] text-[14px] font-bold whitespace-nowrap", status === s ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 bg-white text-slate-600")}>{s === "ALL" ? "Tất cả" : s}</button>
            ))}
          </div>
        )}
        {/* LOGI_SHIPMENT_GLANCEABLE_SUPPORT_UX_01 (issue #86) — the reading order
            of a row is now the reading order of the page: identity → recognition
            facts → the one next action → who last touched it → the action. */}
        <p className="text-[13.5px] text-slate-500 mt-2.5" data-testid="shipment-list-summary">Tìm thấy <b className="text-[#0f2a4a]">{list.length} lô</b>{q ? <> cho “{q}”</> : null} · Mỗi lô: hiện trạng → Incoterm · phương thức · loại hàng · ETD/ETA → việc tiếp theo → nút xử lý.</p>
      </div>

      {/* ============ DESKTOP: FIVE INFORMATION REGIONS, NOT SEVEN COLUMNS ============
          LOGI_SHIPMENT_GLANCEABLE_SUPPORT_UX_01 (issue #86) — the Owner's repro was
          that this table read like a dense admin spreadsheet: one column per small
          fact, and the facts Sale/Support actually scan for (Incoterm, transport
          mode, load model, ETD, ETA) were not in it at all. The SAME information is
          recomposed into five regions: (1) identity + status, (2) the recognition
          facts (with a genuinely missing fact shown as an amber "—" chip — a DISPLAY
          gap only, never a new missingDoc/task/status/alert), (3) the ONE existing
          primary next action, (4) responsibility, (5) actions.
          Nothing here re-reads or re-derives anything: `executionProfile` and
          `transportLegs` are already on the row the backend projected once
          (EXECUTION_PROFILE_BUILDS_PER_ROW=1, PRIMARY_LIST_DB_READS_ADDED=0). */}
      <div className="hidden md:block rounded-2xl bg-white border border-slate-200 overflow-hidden">
        <div className="overflow-x-auto"><table className="tbl w-full text-[14px] min-w-[1000px]">
          <thead><tr><th>Lô · Khách hàng · Tuyến</th><th>Nhận dạng nhanh</th><th>Việc tiếp theo</th><th>Trách nhiệm</th><th>Hành động</th></tr></thead>
          <tbody>
            {list.map((s) => (
              <tr key={s.id} data-testid="shipment-row" data-shipment-id={s.id} className="hover:bg-slate-50 align-top">
                {/* 1 — IDENTITY: what this lot is and where it stands. */}
                <td className="max-w-[300px]">
                  <div className="flex flex-wrap items-center gap-1.5">
                    <Link to={shipmentPath(s.id)} className="font-mono font-bold text-[#1e5aa8] hover:underline text-[15px]">{s.id}</Link>
                    <ToneBadge tone={s.statusTone} size="sm">{s.status}</ToneBadge>
                  </div>
                  <span className="block text-[14px] font-semibold text-slate-800 mt-1 max-w-[280px]">{s.customer}</span>
                  <span className="block text-[12.5px] text-slate-500 mt-0.5">{s.route}</span>
                  <span className="block text-[12px] text-slate-400 mt-0.5">{s.contract} · cập nhật {s.updated}</span>
                </td>
                {/* 2 — QUICK FACTS (missing facts stay visible as amber "—"). */}
                <td className="max-w-[320px]"><ShipmentQuickFacts shipment={s} dense /></td>
                {/* 3 — the ONE primary action the backend composed (s.nextAction). */}
                <td className="max-w-[240px]" data-attention-band={alertByShipment.get(s.id)?.band || undefined}>{nextActionCell(s)}</td>
                {/* 4 — responsibility: `support` is `updated_by`, labelled truthfully. */}
                <td className="text-[13px] whitespace-nowrap"><span className="block">Phụ trách: <b>{s.sale}</b></span><span className="block whitespace-nowrap text-slate-500">Cập nhật bởi: <b>{s.support || "—"}</b></span></td>
                {/* 5 — actions: the same XỬ LÝ route and the same 360° entry. */}
                <td><div className="flex gap-1.5"><Link to={s.nextRoute} className="btn-press touch-target inline-flex items-center rounded-lg bg-[#0f2a4a] text-white text-[13px] font-bold px-3.5 min-h-[44px]">XỬ LÝ</Link><Link to={shipmentPath(s.id)} className="btn-press touch-target inline-flex items-center gap-1 rounded-lg border-2 border-slate-200 text-[13px] font-bold px-3 min-h-[44px]"><Eye size={15} /> 360°</Link></div></td>
              </tr>
            ))}
          </tbody>
        </table></div>
      </div>

      <div className="md:hidden space-y-3">
        {list.map((s) => (
          <div key={s.id} data-testid="shipment-mobile-card" data-shipment-id={s.id} className="rounded-2xl bg-white border border-slate-200 overflow-hidden">
            <div className="p-4">
              <div className="flex items-center gap-2 flex-wrap">
                <StatusDot tone={s.statusTone} />
                <span className="font-mono font-bold text-[17px] text-[#0f2a4a]">{s.id}</span>
                <ToneBadge tone={s.statusTone} size="sm">{s.status}</ToneBadge>
              </div>
              <p className="font-semibold text-[14.5px] mt-1">{s.customer}</p>
              <p className="text-[13px] text-slate-500">{s.route}</p>
              {/* LOGI_SHIPMENT_GLANCEABLE_SUPPORT_UX_01 — the recognition facts are
                  on the card itself, wrapping inside the card width: no horizontal
                  overflow, and no need to open the lot to read it. */}
              <div className="mt-2.5"><ShipmentQuickFacts shipment={s} dense /></div>
              <div className="mt-2.5 rounded-xl border border-slate-200 bg-slate-50 p-3" data-attention-band={alertByShipment.get(s.id)?.band || undefined}>
                <p className="text-[11.5px] font-bold uppercase tracking-wide text-slate-500">Việc tiếp theo</p>
                <div className="mt-1">{nextActionCell(s)}</div>
              </div>
              <p className="text-[12.5px] text-slate-400 mt-2">Phụ trách <b className="text-slate-600">{s.sale}</b> · cập nhật bởi {s.support || "—"} · {s.updated}</p>
            </div>
            <div className="grid grid-cols-2 border-t">
              <Link to={s.nextRoute} className="touch-target flex items-center justify-center gap-1.5 bg-[#0f2a4a] text-white font-extrabold text-[15px] min-h-[52px]">XỬ LÝ <ArrowRight size={17} /></Link>
              <Link to={shipmentPath(s.id)} className="touch-target flex items-center justify-center gap-1.5 font-bold text-[15px] text-[#0f2a4a] min-h-[52px]"><Eye size={17} /> XEM 360°</Link>
            </div>
          </div>
        ))}
        {list.length === 0 && <div className="rounded-2xl bg-white border p-8 text-center"><p className="font-bold text-[16px]">Không tìm thấy lô nào</p><p className="text-[14px] text-slate-500 mt-1">Thử từ khóa khác hoặc tạo lô mới.</p><Link to="/tao-lo-moi" className="btn-press touch-target mt-3 inline-flex rounded-xl bg-[#0f2a4a] text-white font-bold px-5 min-h-[48px] items-center">＋ Tạo lô mới</Link></div>}
      </div>
    </div>
  );
}
