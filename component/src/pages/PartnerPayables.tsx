// ============================================================================
// C2D — global Owner-facing "THANH TOÁN ĐỐI TÁC / PHẢI TRẢ" workspace.
//
// A read-only projection over the EXISTING canonical partner ledger truth
// (views.logi_real_data.partner_payables_projection → core.financial_ledger.
// shipment_partner_position), rendered in the donor's list-page + finance-tab
// structure: per-currency summary tiles, search + filters, a desktop table,
// mobile cards, per-row "open shipment" and "record partner payment" actions.
//
// The payment action is the SAME canonical C2B path (save_transaction +
// allocate_transaction) driven by the typed `partner_payment_record` event,
// with one stable request identity per payment intent so a double click never
// double-posts and a new intent stays distinct.
//
// UNKNOWN != ZERO: a shipment/partner with no canonical obligation/payment
// record simply has NO row here — absence is never rendered as a 0 payable.
// Currencies (VND / USD / CNY) are never summed together (no FX engine).
// ============================================================================

import { useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, Building2, CircleAlert, Eye, Search, SlidersHorizontal, Wallet } from "lucide-react";
import { Field, GhostBtn, SectionTitle, StatusDot, SuccessBtn, ToneBadge, inputCls } from "../components/ui";
import { useStore } from "../lib/store";
import { shipmentPath } from "../lib/shipmentRoute";
import { cx, fmtCcy, fmtText, isUnknown, parseAmountVN } from "../lib/format";
import type { PartnerPayableRow } from "../lib/viewmodel";

const toneFor = (status: string): "green" | "amber" | "red" | "blue" | "gray" =>
  status === "CONFIRMED" ? "blue" : status === "REVIEW_REQUIRED" ? "amber" : "gray";

export default function PartnerPayables() {
  const { payables, dispatch, toast } = useStore();
  const [q, setQ] = useState("");
  const [showFilter, setShowFilter] = useState(false);
  const [outstandingOnly, setOutstandingOnly] = useState(false);
  const [currency, setCurrency] = useState("ALL");
  const [partner, setPartner] = useState("ALL");
  const [status, setStatus] = useState("ALL");

  // Partner payment sheet (per row) — mirrors the C2B ShipmentDetail pay path.
  const [paying, setPaying] = useState<PartnerPayableRow | null>(null);
  const [payAmt, setPayAmt] = useState("");
  const payRequestRef = useRef("");

  const rows = payables.rows ?? [];
  const totals = payables.totals ?? {};

  const currencies = ["ALL", ...Array.from(new Set(rows.map((r) => r.currency)))];
  const partners = ["ALL", ...Array.from(new Set(rows.map((r) => r.partnerId)))];
  const statuses = ["ALL", ...Array.from(new Set(rows.map((r) => r.status)))];

  const partnerLabel = (id: string) =>
    rows.find((r) => r.partnerId === id)?.partnerName ?? id;

  // Priority = biggest real remaining first (authoritative, no aging invented).
  const list = useMemo(() => {
    const needle = q.trim().toLowerCase();
    return rows
      .filter((r) => {
        if (outstandingOnly && !(r.remaining != null && r.remaining > 0)) return false;
        if (currency !== "ALL" && r.currency !== currency) return false;
        if (partner !== "ALL" && r.partnerId !== partner) return false;
        if (status !== "ALL" && r.status !== status) return false;
        if (needle && !(r.shipmentId + " " + r.partnerName + " " + r.partnerId).toLowerCase().includes(needle)) return false;
        return true;
      })
      .sort((a, b) => (b.remaining ?? -1) - (a.remaining ?? -1));
  }, [rows, q, outstandingOnly, currency, partner, status]);

  const openPay = (row: PartnerPayableRow) => {
    payRequestRef.current = `PPAY-REQ-${Date.now().toString(36).toUpperCase()}-${Math.random().toString(36).slice(2, 8).toUpperCase()}`;
    setPayAmt("");
    setPaying(row);
  };

  const recordPay = () => {
    if (!paying) return;
    const raw = payAmt.trim();
    const parsed = parseAmountVN(raw);
    if (parsed == null || parsed <= 0) { toast("Chưa nhập số tiền", `Nhập số tiền ${paying.currency} rồi bấm Lưu.`, "red"); return; }
    const sent = dispatch("partner_payment_record", {
      shipmentId: paying.shipmentId,
      partnerId: paying.partnerId,
      amount: raw,
      currency: paying.currency,
      requestId: payRequestRef.current,
      date: new Date().toISOString().slice(0, 10),
      note: "Trả đối tác từ bàn công nợ đối tác",
    });
    if (!sent) { toast("Không gửi được", "Component chưa kết nối backend.", "red"); return; }
    toast("Đã gửi thanh toán " + fmtCcy(parsed, paying.currency), "Ghi qua canonical ledger (transaction + allocation) — backend sẽ đọc lại còn phải trả.", "green");
    setPaying(null); setPayAmt("");
  };

  return (
    <div className="space-y-4 max-w-[1300px]">
      {/* HEADER */}
      <div className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5">
        <SectionTitle
          icon={<Wallet size={20} className="text-[#1e5aa8]" />}
          title="Thanh toán đối tác · Phải trả"
          sub="Toàn bộ phải trả đối tác theo lô — đọc từ sổ tài chính canonical (nghĩa vụ + thanh toán + phân bổ). Mỗi đồng tiền ghi rõ VND / USD / CNY, không gộp chung."
        />

        {/* SUMMARY TILES — grouped by currency, never summed across currencies */}
        <div className="grid gap-3 mt-3">
          {Object.keys(totals).length === 0 && (
            <p className="text-[14px] text-slate-500">Chưa có khoản phải trả đối tác nào được ghi nhận — phải trả đang <b>chưa xác định</b>, không phải 0.</p>
          )}
          {Object.entries(totals).map(([ccy, t]) => (
            <div key={ccy} className="rounded-2xl border-2 border-slate-100 bg-slate-50/60 p-3 md:p-4">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-[12px] font-extrabold uppercase tracking-wider text-slate-500">Tổng phải trả · {ccy}</span>
                <span className="text-[11px] text-slate-400">không quy đổi sang đồng tiền khác</span>
              </div>
              <div className="grid grid-cols-3 gap-2 text-center">
                <div className="rounded-xl bg-white border p-3">
                  <p className="text-[12px] text-slate-500 font-semibold">Phải trả</p>
                  <p className="font-extrabold text-[16px] md:text-[18px] text-[#0f2a4a]">{fmtCcy(t.payable, ccy)}</p>
                </div>
                <div className="rounded-xl bg-blue-50 border border-blue-200 p-3">
                  <p className="text-[12px] text-blue-700 font-semibold">Đã trả</p>
                  <p className="font-extrabold text-[16px] md:text-[18px] text-blue-700">{fmtCcy(t.paid, ccy)}</p>
                </div>
                <div className="rounded-xl bg-amber-50 border border-amber-200 p-3">
                  <p className="text-[12px] text-amber-700 font-semibold">Còn lại</p>
                  <p className="font-extrabold text-[16px] md:text-[18px] text-amber-800">{fmtCcy(t.remaining, ccy)}</p>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* SEARCH + FILTERS */}
        <div className="flex gap-2 mt-4">
          <div className="flex items-center flex-1 rounded-xl border-2 border-slate-200 focus-within:border-[#1e5aa8] bg-slate-50 overflow-hidden">
            <Search size={19} className="ml-3.5 text-slate-400 shrink-0" />
            <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Tìm mã lô (LO-0308), đối tác (Phú Anh), mã đối tác…" className="w-full bg-transparent px-3 py-3 text-[15px] outline-none" />
          </div>
          <button onClick={() => setShowFilter((v) => !v)} className={cx("touch-target shrink-0 inline-flex items-center gap-1.5 rounded-xl border-2 px-4 min-h-[52px] text-[14.5px] font-bold", showFilter ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 bg-white")}><SlidersHorizontal size={18} /> <span className="hidden sm:inline">Lọc</span></button>
        </div>

        {showFilter && (
          <div className="mt-3 space-y-2.5">
            <button onClick={() => setOutstandingOnly((v) => !v)} className={cx("touch-target inline-flex items-center gap-2 rounded-xl border-2 px-4 min-h-[44px] text-[14px] font-bold", outstandingOnly ? "border-amber-400 bg-amber-50 text-amber-800" : "border-slate-200 bg-white text-slate-600")}>
              <CircleAlert size={16} /> Chỉ còn phải trả
            </button>
            <div className="flex flex-wrap gap-2">
              <span className="self-center text-[13px] font-bold text-slate-500">Đồng tiền:</span>
              {currencies.map((c) => (
                <button key={c} onClick={() => setCurrency(c)} className={cx("touch-target shrink-0 rounded-full border-2 px-4 min-h-[44px] text-[14px] font-bold", currency === c ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 bg-white text-slate-600")}>{c === "ALL" ? "Tất cả" : c}</button>
              ))}
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="self-center text-[13px] font-bold text-slate-500">Đối tác:</span>
              {partners.map((p) => (
                <button key={p} onClick={() => setPartner(p)} className={cx("touch-target shrink-0 rounded-full border-2 px-4 min-h-[44px] text-[14px] font-bold", partner === p ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 bg-white text-slate-600")}>{p === "ALL" ? "Tất cả" : fmtText(partnerLabel(p))}</button>
              ))}
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="self-center text-[13px] font-bold text-slate-500">Trạng thái:</span>
              {statuses.map((s) => (
                <button key={s} onClick={() => setStatus(s)} className={cx("touch-target shrink-0 rounded-full border-2 px-4 min-h-[44px] text-[14px] font-bold", status === s ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 bg-white text-slate-600")}>{s === "ALL" ? "Tất cả" : s}</button>
              ))}
            </div>
          </div>
        )}

        <p className="text-[13.5px] text-slate-500 mt-2.5">Tìm thấy <b className="text-[#0f2a4a]">{list.length} dòng</b> · Ưu tiên theo còn phải trả thực tế (lớn nhất trước) — không suy ra “quá hạn” từ ngày không có thật.</p>
      </div>

      {/* DESKTOP TABLE */}
      <div className="hidden md:block rounded-2xl bg-white border border-slate-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="tbl w-full text-[14px] min-w-[1080px]">
            <thead>
              <tr>
                <th>Lô</th><th>Đối tác</th><th>Phải trả</th><th>Đã trả</th><th>Còn lại</th><th>Đồng tiền</th><th>Trạng thái</th><th>Hành động</th>
              </tr>
            </thead>
            <tbody>
              {list.map((r) => (
                <tr key={r.id} className="hover:bg-slate-50">
                  <td><Link to={shipmentPath(r.shipmentId) + "?tab=tai-chinh"} className="font-extrabold text-[#1e5aa8] hover:underline text-[15px]">{r.shipmentId}</Link></td>
                  <td className="font-semibold max-w-[220px]">
                    <span className="inline-flex items-center gap-1.5"><Building2 size={15} className="text-[#1e5aa8] shrink-0" /> {fmtText(r.partnerName)}</span>
                    <span className="block text-[12px] text-slate-400 font-normal">{r.partnerId}</span>
                  </td>
                  <td className="font-semibold">{fmtCcy(r.payable, r.currency)}</td>
                  <td className="text-blue-700 font-semibold">{fmtCcy(r.paid, r.currency)}</td>
                  <td className={cx("font-extrabold", !isUnknown(r.remaining) && (r.remaining ?? 0) > 0 ? "text-amber-800" : "text-slate-500")}>{fmtCcy(r.remaining, r.currency)}</td>
                  <td><span className="rounded-md bg-slate-100 px-2 py-0.5 text-[12px] font-bold">{r.currency}</span></td>
                  <td><ToneBadge tone={toneFor(r.status)} size="sm">{r.status}</ToneBadge></td>
                  <td>
                    <div className="flex gap-1.5">
                      <Link to={shipmentPath(r.shipmentId) + "?tab=tai-chinh"} className="btn-press touch-target inline-flex items-center gap-1 rounded-lg border-2 border-slate-200 text-[13px] font-bold px-3 min-h-[44px]"><Eye size={15} /> Mở lô</Link>
                      {(r.remaining ?? 0) > 0 && (
                        <button onClick={() => openPay(r)} className="btn-press touch-target inline-flex items-center gap-1 rounded-lg bg-[#0f2a4a] text-white text-[13px] font-bold px-3 min-h-[44px]"><Wallet size={15} /> Trả đối tác</button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* MOBILE CARDS */}
      <div className="md:hidden space-y-3">
        {list.map((r) => (
          <div key={r.id} className="rounded-2xl bg-white border border-slate-200 overflow-hidden">
            <div className="p-4">
              <div className="flex items-center gap-2 flex-wrap">
                <StatusDot tone={toneFor(r.status)} />
                <span className="font-extrabold text-[17px] text-[#0f2a4a]">{r.shipmentId}</span>
                <ToneBadge tone={toneFor(r.status)} size="sm">{r.status}</ToneBadge>
                <span className="ml-auto rounded-md bg-slate-100 px-2 py-0.5 text-[12px] font-bold">{r.currency}</span>
              </div>
              <p className="font-semibold text-[14.5px] mt-1">{fmtText(r.partnerName)} <span className="text-slate-400 font-normal text-[12.5px]">{r.partnerId}</span></p>
              <div className="grid grid-cols-3 gap-2 mt-2.5 text-center">
                <div className="rounded-xl bg-slate-50 border p-2.5"><p className="text-[11px] text-slate-500 font-semibold">Phải trả</p><p className="font-extrabold text-[14px]">{fmtCcy(r.payable, r.currency)}</p></div>
                <div className="rounded-xl bg-blue-50 border border-blue-200 p-2.5"><p className="text-[11px] text-blue-700 font-semibold">Đã trả</p><p className="font-extrabold text-[14px] text-blue-700">{fmtCcy(r.paid, r.currency)}</p></div>
                <div className="rounded-xl bg-amber-50 border border-amber-200 p-2.5"><p className="text-[11px] text-amber-700 font-semibold">Còn lại</p><p className="font-extrabold text-[14px] text-amber-800">{fmtCcy(r.remaining, r.currency)}</p></div>
              </div>
            </div>
            <div className="grid grid-cols-2 border-t">
              <Link to={shipmentPath(r.shipmentId) + "?tab=tai-chinh"} className="touch-target flex items-center justify-center gap-1.5 font-bold text-[15px] text-[#0f2a4a] min-h-[52px]"><Eye size={17} /> MỞ LÔ</Link>
              {(r.remaining ?? 0) > 0
                ? <button onClick={() => openPay(r)} className="touch-target flex items-center justify-center gap-1.5 bg-[#0f2a4a] text-white font-extrabold text-[15px] min-h-[52px]"><Wallet size={17} /> TRẢ ĐỐI TÁC</button>
                : <span className="flex items-center justify-center font-bold text-[15px] text-slate-300 min-h-[52px]">Đã trả đủ</span>}
            </div>
          </div>
        ))}
        {list.length === 0 && (
          <div className="rounded-2xl bg-white border p-8 text-center">
            <p className="font-bold text-[16px]">Chưa có khoản phải trả đối tác</p>
            <p className="text-[14px] text-slate-500 mt-1">Chưa có nghĩa vụ / thanh toán canonical nào cho các lô hiện tại — phải trả là “chưa xác định”, không phải 0.</p>
          </div>
        )}
      </div>

      {/* MODAL: record partner payment */}
      {paying && (
        <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center">
          <div className="absolute inset-0 bg-slate-900/55 anim-fade" onClick={() => setPaying(null)} />
          <div className="relative bg-white w-full sm:max-w-[480px] rounded-t-3xl sm:rounded-3xl p-5 anim-slide-up">
            <h3 className="font-extrabold text-[18px] text-[#0f2a4a]">Ghi nhận thanh toán đối tác — {paying.shipmentId}</h3>
            <p className="text-[13.5px] text-slate-500 mt-1">Đối tác <b>{fmtText(paying.partnerName)}</b> ({paying.partnerId}) · Còn phải trả: <b className="text-amber-800">{fmtCcy(paying.remaining, paying.currency)}</b></p>
            <div className="grid gap-3 mt-3">
              <Field label={`Số tiền (${paying.currency})`} required error={!payAmt ? "Nhập số tiền — VD: 20000000" : undefined}><input value={payAmt} onChange={(e) => setPayAmt(e.target.value)} inputMode="numeric" placeholder="VD: 20000000" className={inputCls(!payAmt ? "missing" : "ok")} /></Field>
            </div>
            <p className="text-[12.5px] text-slate-400 mt-2">Ghi theo đồng tiền của lô ({paying.currency}) — không quy đổi. Gửi lại cùng lần nhập này sẽ không tạo khoản trả thứ hai.</p>
            <div className="grid grid-cols-2 gap-2.5 mt-4">
              <GhostBtn onClick={() => setPaying(null)}>Hủy</GhostBtn>
              <SuccessBtn onClick={recordPay}>💸 LƯU THANH TOÁN</SuccessBtn>
            </div>
          </div>
        </div>
      )}

      {/* sticky mobile primary */}
      {list.length > 0 && (
        <div className="md:hidden sticky-action -mx-3 px-3 py-3 flex gap-2">
          <Link to="/lo-hang" className="btn-press touch-target flex-1 rounded-xl bg-[#0f2a4a] text-white font-extrabold min-h-[52px] flex items-center justify-center">XEM LÔ HÀNG <ArrowRight size={17} /></Link>
        </div>
      )}
    </div>
  );
}
