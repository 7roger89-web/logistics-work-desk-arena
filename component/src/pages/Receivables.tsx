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

import { useEffect, useMemo, useRef, useState, useSyncExternalStore } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { ArrowRight, CircleAlert, Eye, Search, SlidersHorizontal, Wallet } from "lucide-react";
import { Field, GhostBtn, SectionTitle, SheetDialog, StatusDot, SuccessBtn, ToneBadge, inputCls } from "../components/ui";
import { useStore } from "../lib/store";
import { useQueryParam, useQueryFlag } from "../lib/queryParam";
import { getViewModel, subscribeViewModel } from "../lib/viewmodel";
import { cx, fmtCcy, fmtText, isUnknown, parseAmountVN } from "../lib/format";
import type { ReceivableRow } from "../lib/viewmodel";

export default function Receivables() {
  const { receivables, dispatch, toast } = useStore();
  // The authoritative outcome of a recorded receipt arrives in the NEXT fresh
  // view-model (`lastWrites`), correlated by requestId — never from the
  // transport (LOGI_FRONTEND_WORKFLOW_OVERHAUL_01, P0 payment trust).
  const vm = useSyncExternalStore(subscribeViewModel, getViewModel, getViewModel);
  const [receivableParams] = useSearchParams();
  // LOGI_FRONTEND_WORKFLOW_OVERHAUL_01 — the whole worklist context (search +
  // every important filter) lives in the route's search params: lọc → mở lô →
  // Quay lại restores the exact slice the operator was working on.
  const [q, setQ] = useQueryParam("q");
  // Returning to the desk with any active filter re-opens the filter panel,
  // so the restored context is VISIBLE, not just applied silently.
  const [showFilter, setShowFilter] = useState(() =>
    ["noPaid", "ccy", "sale", "support", "status"].some((k) => receivableParams.get(k))
  );
  const [outstandingOnly, setOutstandingOnly] = useQueryFlag("noPaid");
  const [currencyRaw, setCurrencyRaw] = useQueryParam("ccy");
  const currency = currencyRaw || "ALL";
  const setCurrency = (v: string) => setCurrencyRaw(v === "ALL" ? "" : v);
  const [saleRaw, setSaleRaw] = useQueryParam("sale");
  const sale = saleRaw || "ALL";
  const setSale = (v: string) => setSaleRaw(v === "ALL" ? "" : v);
  const [supportRaw, setSupportRaw] = useQueryParam("support");
  const support = supportRaw || "ALL";
  const setSupport = (v: string) => setSupportRaw(v === "ALL" ? "" : v);
  const [statusRaw, setStatusRaw] = useQueryParam("status");
  const status = statusRaw || "ALL";
  const setStatus = (v: string) => setStatusRaw(v === "ALL" ? "" : v);

  // Receipt sheet (per row) — mirrors the donor ShipmentDetail pay sheet.
  const [paying, setPaying] = useState<ReceivableRow | null>(null);
  const [payAmt, setPayAmt] = useState("");
  const [payKind, setPayKind] = useState("Thu tiền khách");
  const payRequestRef = useRef("");
  const [payPending, setPayPending] = useState("");
  const payPendingRef = useRef(""); // synchronous guard: two clicks in one tick
  const [payError, setPayError] = useState("");

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
    payPendingRef.current = "";
    setPayPending("");
    setPayError("");
    setPayAmt("");
    setPayKind("Thu tiền khách");
    setPaying(row);
  };

  // ONE click = ONE payment intent. The sheet stays open while the backend
  // decides: submit is disabled, the pending line is shown, and the fresh
  // view-model's `lastWrites` entry correlated by requestId is the ONLY thing
  // that closes the sheet (success) or surfaces the refusal inline (error).
  const recordPay = () => {
    if (payPendingRef.current) return; // outcome in flight: never double-send
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
    setPayError("");
    payPendingRef.current = payRequestRef.current;
    setPayPending(payRequestRef.current);
  };

  useEffect(() => {
    if (!payPending) return;
    // Correlation is scoped to the PENDING request id: a stale refusal for an
    // OLDER requestId in the same lastWrites array can never settle this retry.
    const outcome = (vm?.lastWrites ?? []).find(
      (w) => w.event === "payment_record" && (w.requestId as string | undefined) === payPending
    );
    if (!outcome) return; // still waiting for the authoritative backend answer
    if (outcome.ok) {
      // Success requires BOTH the correlated ok AND the authoritative finance
      // readback in the SAME fresh view-model (finance.payments[].requestId).
      const fresh = (vm?.shipments ?? []).find((x) => x.id === paying?.id);
      const readbackConfirmed = !!fresh?.finance?.payments?.some(
        (p) => (p.requestId as string | undefined) === payPending
      );
      if (!readbackConfirmed) return; // ok without readback = not yet refreshed; stay pending
      setPaying(null);
      setPayAmt("");
      setPayError("");
      payPendingRef.current = "";
      setPayPending("");
      toast("Đã ghi nhận khoản thu",
        "Backend đã xác nhận ghi sổ — khoản thu với mã yêu cầu này đã hiển thị trong sổ tài chính đọc lại.",
        "green");
    } else {
      // Refusal keeps the form (amount/kind preserved); the refused request
      // stays historical and the NEXT retry is a NEW intent with a FRESH id.
      payPendingRef.current = "";
      setPayPending("");
      setPayError(outcome.error || "Backend từ chối khoản thu này.");
      payRequestRef.current = `PAY-REQ-${Date.now().toString(36).toUpperCase()}-${Math.random().toString(36).slice(2, 8).toUpperCase()}`;
      toast("Chưa ghi nhận được", outcome.error || "Backend từ chối khoản thu.", "red");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [vm?.lastWrites, payPending]);

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
            <button onClick={() => setOutstandingOnly(!outstandingOnly)} className={cx("touch-target inline-flex items-center gap-2 rounded-xl border-2 px-4 min-h-[44px] text-[14px] font-bold", outstandingOnly ? "border-red-400 bg-red-50 text-red-700" : "border-slate-200 bg-white text-slate-600")}>
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
                  <td className="text-[13px]"><span className="block whitespace-nowrap">Sale: <b>{fmtText(r.sale)}</b></span><span className="block whitespace-nowrap">Cập nhật bởi: <b>{fmtText(r.support)}</b></span></td>
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
              <p className="text-[12.5px] text-slate-400 mt-2">Sale {fmtText(r.sale)} · cập nhật bởi {fmtText(r.support)}</p>
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

      {/* MODAL: record receipt — authoritative outcome sheet */}
      {paying && (
        <SheetDialog id="receivable-pay-sheet" testId="receivable-pay-sheet" labelledBy="receivable-pay-title" pending={!!payPending} width={480} onClose={() => setPaying(null)}>
            <h3 id="receivable-pay-title" className="font-extrabold text-[18px] text-[#0f2a4a]">Ghi nhận khoản thu — {paying.id}</h3>
            <p className="text-[13.5px] text-slate-500 mt-1">Khách <b>{fmtText(paying.customer)}</b> · Còn phải thu: <b className="text-red-700">{fmtCcy(paying.outstanding, paying.currency)}</b></p>
            <div className="grid gap-3 mt-3">
              <Field label="Loại khoản"><select value={payKind} disabled={!!payPending} onChange={(e) => { setPayKind(e.target.value); payRequestRef.current = `PAY-REQ-${Date.now().toString(36).toUpperCase()}-${Math.random().toString(36).slice(2, 8).toUpperCase()}`; }} className={inputCls()}><option>Thu tiền khách</option><option>Thu tạm ứng</option><option>Thu nốt công nợ</option></select></Field>
              <Field label={`Số tiền (${paying.currency})`} required error={!payAmt ? "Nhập số tiền — VD: 150000000" : undefined}><input value={payAmt} disabled={!!payPending} onChange={(e) => { setPayAmt(e.target.value); payRequestRef.current = `PAY-REQ-${Date.now().toString(36).toUpperCase()}-${Math.random().toString(36).slice(2, 8).toUpperCase()}`; }} inputMode="numeric" placeholder="VD: 150000000" className={inputCls(!payAmt ? "missing" : "ok")} /></Field>
            </div>
            {payPending ? (
              <p role="status" data-testid="receivable-pay-pending" className="mt-2.5 rounded-lg bg-blue-50 border border-blue-200 px-3 py-2 text-[13.5px] font-semibold text-blue-800">
                ⏳ ĐANG CHỜ BACKEND XÁC NHẬN… Không gửi lại và không đóng trang.
              </p>
            ) : (
              <p className="text-[12.5px] text-slate-400 mt-2">Ghi theo đồng tiền của lô ({paying.currency}) — không quy đổi. Gửi lại cùng lần nhập này sẽ không tạo khoản thu thứ hai.</p>
            )}
            {payError && (
              <p role="alert" id="receivable-pay-error" className="mt-2 rounded-lg bg-red-50 border border-red-200 px-3 py-2 text-[13px] font-semibold text-red-700">{payError}</p>
            )}
            <p className="text-[12.5px] text-slate-400 mt-2">Mã yêu cầu: <b className="font-mono">{payRequestRef.current}</b></p>
            <div className="grid grid-cols-2 gap-2.5 mt-4">
              <GhostBtn onClick={() => setPaying(null)} disabled={!!payPending}>Hủy</GhostBtn>
              <SuccessBtn onClick={recordPay} testId="receivable-pay-submit" disabled={!!payPending}>
                {payPending ? "⏳ ĐANG CHỜ BACKEND XÁC NHẬN…" : "💾 LƯU KHOẢN THU"}
              </SuccessBtn>
            </div>
        </SheetDialog>
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
