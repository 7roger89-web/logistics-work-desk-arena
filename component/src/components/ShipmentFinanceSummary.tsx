import { Link } from "react-router-dom";
import { shipmentPath } from "../lib/shipmentRoute";
import { listReturnState } from "../lib/listReturn";
import { UNKNOWN, cx, fmtCcy, isUnknown } from "../lib/format";
import type { Shipment } from "../lib/viewmodel";

/**
 * Issue #254 — compact read-only service debt summary ("Công nợ dịch vụ") for
 * `/lo-hang` (desktop table cell + mobile card).
 *
 * Truth contract (no calculation or FX conversion in React):
 * - Reads `shipment.finance` projected by `views.logi_real_data.finance_projection`
 *   over `core.logic.calculate_from_shipment(shipment)` (`data["3.4"]`).
 * - `UNKNOWN != 0`: when `hasActualLines` is false, `receivable` and `outstanding`
 *   render `"—"`; Quote Estimate (`finance.quote`) and partner payables are never
 *   substituted, and `"đã thanh toán đủ"` / `0 VND` is never claimed.
 * - Renders nothing when server-side `finance_view` is denied (`canView === false`).
 */
export function ShipmentFinanceSummary({
  shipment,
  variant = "desktop",
  listReturn,
}: {
  shipment: Shipment;
  variant?: "desktop" | "mobile";
  /** LOGI-255-RETURN-TO-LIST — the /lo-hang location this cluster was opened
   *  from, so the detail screen can return to the SAME filters. Omitted by
   *  every non-list caller (Receivables, PartnerPayables, …), which therefore
   *  keep the plain-list fallback instead of inventing a context. */
  listReturn?: string;
}) {
  const fin = shipment.finance;
  if (!fin || fin.canView === false) return null;

  const ccy = (fin.currency ?? "").trim().toUpperCase() || "VND";
  const hasActual = Boolean(fin.hasActualLines);
  const receivable = hasActual ? fin.receivable : null;
  const received = fin.received;
  const outstanding = hasActual ? fin.outstanding : null;

  const fmtDebtVal = (val: number | null | undefined): string =>
    isUnknown(val) ? UNKNOWN : fmtCcy(val, ccy);

  const hasOpenDebt = hasActual && !isUnknown(outstanding) && Number(outstanding) > 0;
  const isSettledBalance = hasActual && !isUnknown(outstanding) && Number(outstanding) <= 0;

  const surfaceCls = !hasActual
    ? "border-dashed border-slate-200 bg-slate-50/60 hover:border-slate-300"
    : hasOpenDebt
      ? "border-red-200/80 bg-red-50/30 hover:border-red-300"
      : isSettledBalance
        ? "border-emerald-200/80 bg-emerald-50/30 hover:border-emerald-300"
        : "border-slate-200 bg-slate-50/60 hover:border-slate-300";

  const receivableCls = !hasActual || isUnknown(receivable)
    ? "text-slate-400 font-semibold"
    : "text-[#0f2a4a] font-bold";

  const receivedCls = !isUnknown(received) && Number(received) > 0
    ? "text-emerald-700 font-bold"
    : "text-slate-600 font-semibold";

  const outstandingCls = !hasActual || isUnknown(outstanding)
    ? "text-slate-400 font-semibold"
    : hasOpenDebt
      ? "text-red-700 font-extrabold"
      : "text-emerald-700 font-extrabold";

  const detailHref = `${shipmentPath(shipment.id)}?tab=tai-chinh`;
  const hint = hasActual
    ? `Mở Tài chính / Công nợ lô ${shipment.id} (${ccy})`
    : `Chưa chốt dòng dịch vụ thực tế — mở Tài chính / Công nợ lô ${shipment.id}`;

  return (
    <Link
      to={detailHref}
      state={listReturn ? listReturnState(listReturn) : undefined}
      data-testid="shipment-finance-summary"
      data-shipment-id={shipment.id}
      data-currency={ccy}
      data-has-actual={hasActual ? "true" : "false"}
      title={hint}
      aria-label={`Công nợ dịch vụ lô ${shipment.id}`}
      className={cx(
        "block rounded-xl border transition-colors focus-visible:outline-2 focus-visible:outline-[#1e5aa8]",
        variant === "mobile" ? "mt-2.5 px-3 py-2" : "px-2 py-1.5",
        surfaceCls
      )}
    >
      {variant === "mobile" && (
        <div className="flex items-center justify-between gap-2 mb-1">
          <span className="text-[11px] font-bold uppercase tracking-wide text-slate-500">
            Công nợ dịch vụ
          </span>
          <span className="text-[11px] font-semibold text-[#1e5aa8]">
            {hasActual ? `Tài chính · ${ccy} →` : "Chưa chốt thực tế →"}
          </span>
        </div>
      )}
      <div className={cx("tnum space-y-0.5", variant === "mobile" ? "text-[12.5px] leading-snug" : "text-[11.5px] leading-[1.35]")}>
        <div className="flex items-baseline justify-between gap-1.5">
          <span className="text-slate-500 font-medium whitespace-nowrap">Phải thu</span>
          <span data-testid="debt-receivable" className={cx("tnum whitespace-nowrap text-right", receivableCls)}>
            {fmtDebtVal(receivable)}
          </span>
        </div>
        <div className="flex items-baseline justify-between gap-1.5">
          <span className="text-slate-500 font-medium whitespace-nowrap">Đã thu</span>
          <span data-testid="debt-received" className={cx("tnum whitespace-nowrap text-right", receivedCls)}>
            {fmtDebtVal(received)}
          </span>
        </div>
        <div className="flex items-baseline justify-between gap-1.5 pt-0.5 border-t border-slate-200/70">
          <span className="text-slate-600 font-semibold whitespace-nowrap">Còn phải thu</span>
          <span data-testid="debt-outstanding" className={cx("tnum whitespace-nowrap text-right", outstandingCls)}>
            {fmtDebtVal(outstanding)}
          </span>
        </div>
      </div>
    </Link>
  );
}
