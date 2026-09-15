// ============================================================================
// C2C — global Owner-facing "THU TIỀN KHÁCH / PHẢI THU" workspace.
//
// A read-only projection over the EXISTING shipment/customer/finance truth
// (views.logi_real_data.receivables_projection), rendered in the donor's
// list-page + finance-tab structure: summary tiles grouped by currency,
// search + filters, a desktop table and mobile cards, per-row "open shipment"
// and "record receipt" actions.
//
// The receipt action is the SAME canonical writer proven in C2A
// (save_direct_shipment_payment) driven by the typed `payment_record` event,
// with one stable request identity per payment intent so a double click never
// double-posts and a new intent stays distinct.
// ============================================================================

import { useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, CircleAlert, Eye, Search, SlidersHorizontal, Wallet } from "lucide-react";
import { Field, GhostBtn, SectionTitle, StatusDot, SuccessBtn, ToneBadge, inputCls } from "../components/ui";
import { useStore } from "../lib/store";
import { cx, fmtCcy, fmtText, isUnknown, parseAmountVN } from "../lib/format";
import type { ReceivableRow } from "../lib/viewmodel";

export default function Receivables() {
  const { receivables, dispatch, toast } = useStore();
  const [q, setQ] = useState("");
  const [showFilter, setShowFilter] = useState(false);
  const [outstandingOnly, setOutstandingOnly] = useState(false);
  const [currency, setCurrency] = useState("ALL");
  const [sale, setSale] = useState("ALL");
  const [support, setSupport] = useState("ALL");
  const [status, setStatus] = useState("ALL");

  // Receipt sheet (per row) — mirrors the donor ShipmentDetail pay sheet.
  const [paying, setPaying] = useState<ReceivableRow | null>(null);
  const [payAmt, setPayAmt] = useState("");
  const [payKind, setPayKind] = useState("Thu tiền khách");
  const payRequestRef = useRef("");

  const rows = receivables.rows ?? [];
  const totals = receivables.totals ?? {};

  const currencies = ["ALL", ...Array.from(new Set(rows.map((r) => r.currency)))];
  const sales = ["ALL", ...Array.from(new Set(rows.map((r) => r.sale).filter((s) => s)))];
  const supports = ["ALL", ...Array.from(new Set(rows.map((r) => r.support).filter((s) => s)))];
  const statuses = ["ALL", ...Array.from(new Set(rows.map((r) => r.status)))];

  // Priority = biggest real outstanding first (authoritative, no aging invented).
  const list = useMemo(() => {
    const needle = q.trim().toLowerCase();
    return rows
      .filter((r) => {
        if (outstandingOnly && !(r.outstanding != null && r.outstanding > 0)) return false;
        if (currency !== "ALL" && r.currency !== currency) return false;
        if (sale !== "ALL" && (r.sale || "") !== sale) return false;
        if (support !== "ALL" && (r.support || "") !== support) return false;
        if (status !== "ALL" && r.status !== status) return false;
        if (needle && !(r.id + " " + r.customer + " " + (r.sale || "") + " " + (r.support || "")).toLowerCase().includes(needle)) return false;
        return true;
      })
      .sort((a, b) => (b.outstanding ?? -1) - (a.outstanding ?? -1));
  }, [rows, q, outstandingOnly, currency, sale, support, status]);

  const openPay = (row: ReceivableRow) => {
    payRequestRef.current = `PAY-REQ-${Date.now().toString(36).toUpperCase()}-${Math.random().toString(36).slice(2, 8).toUpperCase()}`;
    setPayAmt("");
    setPayKind("Thu tiền khách");
    setPaying(row);
  };

  const recordPay = () => {
    if (!paying) return;
    const raw = payAmt.trim();
    const parsed = parseAmountVN(raw);
    if (parsed == null || parsed <= 0) { toast("Chưa nhập số tiền", `Nhập số tiền ${paying.currency} rồi bấm Lưu — ví dụ 50.000.000.`, "red"); return; }
    const sent = dispatch("payment_record", {
      shipmentId: paying.id,
      amount: raw,
      requestId: payRequestRef.current,
      date: new Date().toISOString().slice(0, 10),
      note: payKind,
    });
    if (!sent) { toast("Không gửi được", "Component chưa kết nối backend.", "red"); return; }
    toast("Đã gửi khoản thu " + fmtCcy(parsed, paying.currency), "Ghi qua save_direct_shipment_payment — gửi lại cùng intent không nhân đôi.", "green");
    setPaying(null); setPayAmt("");
  };

  return (
    <div className="space-y-4 max-w-[1300px]">
      {/* HEADER */}
      <div className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5">
        <SectionTitle
          icon={<Wallet size={20} className="text-emerald-600" />}
          title="Thu tiền khách · Phải thu"
          sub="Toàn bộ phải thu khách hàng theo lô — đọc từ sổ tài chính thật (core.logic). Mỗi đồng tiền ghi rõ VND / USD / CNY, không gộp chung."
        />

        {/* SUMMARY TILES — grouped by currency, never summed across currencies */}
        <div className="grid gap-3 mt-3">
          {Object.keys(totals).length === 0 && (
            <p className="text-[14px] text-slate-500">Chưa có lô nào chốt dòng thực tế — phải thu đang <b>chưa xác định</b>, không phải 0.</p>
          )}
          {Object.entries(totals).map(([ccy, t]) => (
            <div key={ccy} className="rounded-2xl border-2 border-slate-100 bg-slate-50/60 p-3 md:p-4">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-[12px] font-extrabold uppercase tracking-wider text-slate-500">Tổng phải thu · {ccy}</span>
                <span className="text-[11px] text-slate-400">không quy đổi sang đồng tiền khác</span>
              </div>
              <div className="grid grid-cols-3 gap-2 text-center">
                <div className="rounded-xl bg-white border p-3">
                  <p className="text-[12px] text-slate-500 font-semibold">Phải thu</p>
                  <p className="font-extrabold text-[16px] md:text-[18px] text-[#0f2a4a]">{fmtCcy(t.receivable, ccy)}</p>
                </div>
                <div className="rounded-xl bg-emerald-50 border border-emerald-200 p-3">
                  <p className="text-[12px] text-emerald-700 font-semibold">Đã thu</p>
                  <p className="font-extrabold text-[16px] md:text-[18px] text-emerald-700">{fmtCcy(t.received, ccy)}</p>
                </div>
                <div className="rounded-xl bg-red-50 border border-red-200 p-3">
                  <p className="text-[12px] text-red-600 font-semibold">Còn lại</p>
                  <p className="font-extrabold text-[16px] md:text-[18px] text-red-700">{fmtCcy(t.outstanding, ccy)}</p>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* SEARCH + FILTERS */}
        <div className="flex gap-2 mt-4">
          <div className="flex items-center flex-1 rounded-xl border-2 border-slate-200 focus-within:border-[#1e5aa8] bg-slate-50 overflow-hidden">
            <Search size={19} className="ml-3.5 text-slate-400 shrink-0" />
            <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Tìm mã lô (LO-0306), khách (An Phát), Sale, Support…" className="w-full bg-transparent px-3 py-3 text-[15px] outline-none" />
          </div>
          <button onClick={() => setShowFilter((v) => !v)} className={cx("touch-target shrink-0 inline-flex items-center gap-1.5 rounded-xl border-2 px-4 min-h-[52px] text-[14.5px] font-bold", showFilter ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 bg-white")}><SlidersHorizontal size={18} /> <span className="hidden sm:inline">Lọc</span></button>
        </div>

        {showFilter && (
          <div className="mt-3 space-y-2.5">
            <button onClick={() => setOutstandingOnly((v) => !v)} className={cx("touch-target inline-flex items-center gap-2 rounded-xl border-2 px-4 min-h-[44px] text-[14px] font-bold", outstandingOnly ? "border-red-400 bg-red-50 text-red-700" : "border-slate-200 bg-white text-slate-600")}>
              <CircleAlert size={16} /> Chỉ lô còn phải thu
            </button>
            <div className="flex flex-wrap gap-2">
              <span className="self-center text-[13px] font-bold text-slate-500">Đồng tiền:</span>
              {currencies.map((c) => (
                <button key={c} onClick={() => setCurrency(c)} className={cx("touch-target shrink-0 rounded-full border-2 px-4 min-h-[44px] text-[14px] font-bold", currency === c ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 bg-white text-slate-600")}>{c === "ALL" ? "Tất cả" : c}</button>
              ))}
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="self-center text-[13px] font-bold text-slate-500">Sale:</span>
              {sales.map((s) => (
                <button key={s} onClick={() => setSale(s)} className={cx("touch-target shrink-0 rounded-full border-2 px-4 min-h-[44px] text-[14px] font-bold", sale === s ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 bg-white text-slate-600")}>{s === "ALL" ? "Tất cả" : fmtText(s)}</button>
              ))}
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="self-center text-[13px] font-bold text-slate-500">Support:</span>
              {supports.map((s) => (
                <button key={s} onClick={() => setSupport(s)} className={cx("touch-target shrink-0 rounded-full border-2 px-4 min-h-[44px] text-[14px] font-bold", support === s ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 bg-white text-slate-600")}>{s === "ALL" ? "Tất cả" : fmtText(s)}</button>
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

        <p className="text-[13.5px] text-slate-500 mt-2.5">Tìm thấy <b className="text-[#0f2a4a]">{list.length} lô</b> · Ưu tiên theo còn phải thu thực tế (lớn nhất trước) — không suy ra “quá hạn” từ ngày không có thật.</p>
      </div>

      {/* DESKTOP TABLE */}
      <div className="hidden md:block rounded-2xl bg-white border border-slate-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="tbl w-full text-[14px] min-w-[1080px]">
            <thead>
              <tr>
                <th>Lô</th><th>Khách hàng</th><th>Phải thu</th><th>Đã thu</th><th>Còn lại</th><th>Đồng tiền</th><th>Sale · Support</th><th>Trạng thái</th><th>Hành động</th>
              </tr>
            </thead>
            <tbody>
              {list.map((r) => (
                <tr key={r.id} className="hover:bg-slate-50">
                  <td><Link to={"/lo-hang/" + r.id + "?tab=tai-chinh"} className="font-extrabold text-[#1e5aa8] hover:underline text-[15px]">{r.id}</Link></td>
                  <td className="font-semibold max-w-[180px]">{fmtText(r.customer)}</td>
                  <td className="font-semibold">{fmtCcy(r.receivable, r.currency)}</td>
                  <td className="text-emerald-700 font-semibold">{fmtCcy(r.received, r.currency)}</td>
                  <td className={cx("font-extrabold", !isUnknown(r.outstanding) && (r.outstanding ?? 0) > 0 ? "text-red-700" : "text-slate-500")}>{fmtCcy(r.outstanding, r.currency)}</td>
                  <td><span className="rounded-md bg-slate-100 px-2 py-0.5 text-[12px] font-bold">{r.currency}</span></td>
                  <td className="text-[13px]"><span className="block whitespace-nowrap">Sale: <b>{fmtText(r.sale)}</b></span><span className="block whitespace-nowrap">SP: <b>{fmtText(r.support)}</b></span></td>
                  <td><ToneBadge tone={r.statusTone} size="sm">{fmtText(r.status)}</ToneBadge></td>
                  <td>
                    <div className="flex gap-1.5">
                      <Link to={"/lo-hang/" + r.id + "?tab=tai-chinh"} className="btn-press touch-target inline-flex items-center gap-1 rounded-lg border-2 border-slate-200 text-[13px] font-bold px-3 min-h-[44px]"><Eye size={15} /> Mở lô</Link>
                      {(r.outstanding ?? 0) > 0 && (
                        <button onClick={() => openPay(r)} className="btn-press touch-target inline-flex items-center gap-1 rounded-lg bg-emerald-600 text-white text-[13px] font-bold px-3 min-h-[44px]"><Wallet size={15} /> Thu tiền</button>
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
                <StatusDot tone={r.statusTone} />
                <span className="font-extrabold text-[17px] text-[#0f2a4a]">{r.id}</span>
                <ToneBadge tone={r.statusTone} size="sm">{fmtText(r.status)}</ToneBadge>
                <span className="ml-auto rounded-md bg-slate-100 px-2 py-0.5 text-[12px] font-bold">{r.currency}</span>
              </div>
              <p className="font-semibold text-[14.5px] mt-1">{fmtText(r.customer)}</p>
              <div className="grid grid-cols-3 gap-2 mt-2.5 text-center">
                <div className="rounded-xl bg-slate-50 border p-2.5"><p className="text-[11px] text-slate-500 font-semibold">Phải thu</p><p className="font-extrabold text-[14px]">{fmtCcy(r.receivable, r.currency)}</p></div>
                <div className="rounded-xl bg-emerald-50 border border-emerald-200 p-2.5"><p className="text-[11px] text-emerald-700 font-semibold">Đã thu</p><p className="font-extrabold text-[14px] text-emerald-700">{fmtCcy(r.received, r.currency)}</p></div>
                <div className="rounded-xl bg-red-50 border border-red-200 p-2.5"><p className="text-[11px] text-red-600 font-semibold">Còn lại</p><p className="font-extrabold text-[14px] text-red-700">{fmtCcy(r.outstanding, r.currency)}</p></div>
              </div>
              <p className="text-[12.5px] text-slate-400 mt-2">Sale {fmtText(r.sale)} · SP {fmtText(r.support)}</p>
            </div>
            <div className="grid grid-cols-2 border-t">
              <Link to={"/lo-hang/" + r.id + "?tab=tai-chinh"} className="touch-target flex items-center justify-center gap-1.5 font-bold text-[15px] text-[#0f2a4a] min-h-[52px]"><Eye size={17} /> MỞ LÔ</Link>
              {(r.outstanding ?? 0) > 0
                ? <button onClick={() => openPay(r)} className="touch-target flex items-center justify-center gap-1.5 bg-emerald-600 text-white font-extrabold text-[15px] min-h-[52px]"><Wallet size={17} /> THU TIỀN</button>
                : <span className="flex items-center justify-center font-bold text-[15px] text-slate-300 min-h-[52px]">Đã thu đủ</span>}
            </div>
          </div>
        ))}
        {list.length === 0 && (
          <div className="rounded-2xl bg-white border p-8 text-center">
            <p className="font-bold text-[16px]">Không tìm thấy lô nào</p>
            <p className="text-[14px] text-slate-500 mt-1">Thử từ khóa khác hoặc bỏ bớt bộ lọc.</p>
          </div>
        )}
      </div>

      {/* MODAL: record receipt */}
      {paying && (
        <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center">
          <div className="absolute inset-0 bg-slate-900/55 anim-fade" onClick={() => setPaying(null)} />
          <div className="relative bg-white w-full sm:max-w-[480px] rounded-t-3xl sm:rounded-3xl p-5 anim-slide-up">
            <h3 className="font-extrabold text-[18px] text-[#0f2a4a]">Ghi nhận khoản thu — {paying.id}</h3>
            <p className="text-[13.5px] text-slate-500 mt-1">Khách <b>{fmtText(paying.customer)}</b> · Còn phải thu: <b className="text-red-700">{fmtCcy(paying.outstanding, paying.currency)}</b></p>
            <div className="grid gap-3 mt-3">
              <Field label="Loại khoản"><select value={payKind} onChange={(e) => setPayKind(e.target.value)} className={inputCls()}><option>Thu tiền khách</option><option>Thu tạm ứng</option><option>Thu nốt công nợ</option></select></Field>
              <Field label={`Số tiền (${paying.currency})`} required error={!payAmt ? "Nhập số tiền — VD: 150000000" : undefined}><input value={payAmt} onChange={(e) => setPayAmt(e.target.value)} inputMode="numeric" placeholder="VD: 150000000" className={inputCls(!payAmt ? "missing" : "ok")} /></Field>
            </div>
            <p className="text-[12.5px] text-slate-400 mt-2">Ghi theo đồng tiền của lô ({paying.currency}) — không quy đổi. Gửi lại cùng lần nhập này sẽ không tạo khoản thu thứ hai.</p>
            <div className="grid grid-cols-2 gap-2.5 mt-4">
              <GhostBtn onClick={() => setPaying(null)}>Hủy</GhostBtn>
              <SuccessBtn onClick={recordPay}>💾 LƯU KHOẢN THU</SuccessBtn>
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
