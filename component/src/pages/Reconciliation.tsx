// ============================================================================
// LOGI_RECONCILIATION_DESK_01 — /tai-chinh/doi-soat (Đối soát).
//
// A REAL, READ-ONLY reconciliation desk over capability that already exists in
// Logistics Work Desk. It answers the one question the existing canonical
// ledger can actually answer:
//
//     "Mỗi nghĩa vụ đã được phân bổ tới đâu, và tiền nào chưa được phân bổ?"
//
//   obligation ↔ allocation  →  MATCHED / PARTIAL / UNMATCHED
//   transaction              →  ALLOCATED / PARTIAL / UNALLOCATED
//
// Every figure comes from `core.financial_ledger` through
// views/reconciliation_desk.py. This page computes no business truth: it never
// re-derives an amount, never nets a currency, never infers a settlement.
//
// Deliberately NOT built (no backend source exists — the panel says so instead
// of leaving a quiet empty tab): bank-statement ingestion, FX / cross-currency
// totals, aging buckets, invoice/journal/VAT matching, period close, approval
// workflow.
//
// NO WRITE. There is no "force reconcile", no "mark settled", no editable
// balance and no admin override here. Recording a payable or a payment stays on
// the canonical C2B/C2D and C2C surfaces, which this desk links to.
//
// Every filter goes through the ONE bounded typed `reconciliation_filter`
// event; the result always arrives from the next fresh view-model read, so the
// screen shows what the backend knows — including "unknown".
//
// UNKNOWN != ZERO: a null amount renders "—", a null match state renders
// "chưa xác định", and a currency the record does not carry is shown as its own
// UNKNOWN group rather than folded into a real one.
//
// Mobile: filters wrap with >= 48px targets, rows become stacked cards below
// `md` (no min-width table, no horizontal page scroll), amounts stay paired with
// their currency, and the Open-Shipment action is always reachable.
// ============================================================================

import { useMemo, useState, useSyncExternalStore } from "react";
import { Link } from "react-router-dom";
import {
  ArrowUpRight, Ban, CircleAlert, Eye, Info, Lock, Scale, Search, Wallet,
} from "lucide-react";
import { SectionTitle, ToneBadge } from "../components/ui";
import { dispatchLogiEvent } from "../lib/dispatcher";
import { cx, fmtCcy, fmtText, isUnknown, UNKNOWN } from "../lib/format";
import {
  getViewModel,
  subscribeViewModel,
  type ReconciliationRow,
  type ReconciliationSlice,
} from "../lib/viewmodel";

const SIDE_LABELS: Record<string, string> = {
  obligation: "Phải trả / nghĩa vụ",
  money: "Tiền đã phát sinh",
};

const STATE_TONE: Record<string, "green" | "amber" | "red" | "blue" | "gray"> = {
  MATCHED: "green",
  ALLOCATED: "green",
  PARTIAL: "amber",
  UNMATCHED: "red",
  UNALLOCATED: "red",
};

/** Chips offered for a given side; the ledger derives different states per side. */
function stateOptions(side: string): { value: string; label: string }[] {
  const base = [{ value: "ALL", label: "Tất cả" }];
  const review = [{ value: "REVIEW", label: "Cần rà soát" }];
  if (side === "obligation") {
    return [...base, { value: "MATCHED", label: "Đã đối soát đủ" },
      { value: "PARTIAL", label: "Một phần" }, { value: "UNMATCHED", label: "Chưa đối soát" }, ...review];
  }
  if (side === "money") {
    return [...base, { value: "ALLOCATED", label: "Đã phân bổ hết" },
      { value: "PARTIAL", label: "Một phần" }, { value: "UNALLOCATED", label: "Chưa phân bổ" }, ...review];
  }
  return [...base, { value: "MATCHED", label: "Đã đối soát đủ" }, { value: "ALLOCATED", label: "Đã phân bổ hết" },
    { value: "PARTIAL", label: "Một phần" }, { value: "UNMATCHED", label: "Chưa đối soát" },
    { value: "UNALLOCATED", label: "Chưa phân bổ" }, ...review];
}

const SIDES = [
  { value: "ALL", label: "Cả hai" },
  { value: "obligation", label: "Nghĩa vụ" },
  { value: "money", label: "Tiền" },
];

/**
 * Canonical identity of one filter intent, so a pending intent can be compared
 * with the filter the backend echoed back. Python strips the query and
 * upper-cases currency/state/side, so both sides are normalised the same way.
 */
function filterKey(filter: { query?: string; currency?: string; state?: string; side?: string }): string {
  return [
    `q=${(filter.query ?? "").trim().toLowerCase()}`,
    `c=${(filter.currency ?? "ALL").trim().toUpperCase()}`,
    `s=${(filter.state ?? "ALL").trim().toUpperCase()}`,
    `d=${(filter.side ?? "ALL").trim().toUpperCase()}`,
  ].join("|");
}

/** Money with its currency; a genuine 0 stays "0", null stays "—". */
function Money({ value, ccy, strong }: { value: number | null; ccy: string; strong?: boolean }) {
  return (
    <span className={cx("tabular-nums whitespace-nowrap", strong ? "font-extrabold text-[#0f2a4a]" : "font-bold")}>
      {isUnknown(value) ? `${UNKNOWN} ${ccy}`.trim() : fmtCcy(value, ccy)}
    </span>
  );
}

function StateBadge({ row }: { row: ReconciliationRow }) {
  if (!row.matchState) {
    return <ToneBadge tone="gray" size="sm">trạng thái {UNKNOWN}</ToneBadge>;
  }
  return (
    <ToneBadge tone={STATE_TONE[row.matchState] ?? "gray"} size="sm">
      {row.matchLabel ?? row.matchState}
    </ToneBadge>
  );
}

function Refs({ row }: { row: ReconciliationRow }) {
  const parts = [
    row.obligationIds.length ? `nghĩa vụ: ${row.obligationIds.join(", ")}` : null,
    row.transactionIds.length ? `giao dịch: ${row.transactionIds.join(", ")}` : null,
    row.allocationIds.length ? `phân bổ: ${row.allocationIds.join(", ")}` : null,
  ].filter(Boolean) as string[];
  return (
    <p className="text-[12px] text-slate-500 break-words leading-relaxed">
      {parts.length ? parts.join(" · ") : `Chưa có tham chiếu phân bổ — ${UNKNOWN}`}
    </p>
  );
}

function OpenShipment({ row }: { row: ReconciliationRow }) {
  if (!row.canOpen) {
    return (
      <span className="touch-target inline-flex items-center gap-1.5 rounded-xl border-2 border-slate-200 text-slate-400 font-bold text-[13px] px-3.5 min-h-[44px]">
        <Lock size={14} /> Lô không có trong dữ liệu
      </span>
    );
  }
  return (
    <Link
      to={row.openHref}
      className="btn-press touch-target inline-flex items-center gap-1.5 rounded-xl bg-[#0f2a4a] text-white font-bold text-[13px] px-3.5 min-h-[44px]"
    >
      <Eye size={15} /> Mở lô {row.shipmentId}
    </Link>
  );
}

/** One row as a stacked card (the only layout below `md`). */
function RowCard({ row }: { row: ReconciliationRow }) {
  return (
    <div className="rounded-2xl bg-white border border-slate-200 p-4">
      <div className="flex items-center gap-2 flex-wrap">
        <span className="font-extrabold text-[16px] text-[#0f2a4a] break-all">{row.shipmentId}</span>
        <StateBadge row={row} />
        <ToneBadge tone={row.side === "obligation" ? "blue" : "gray"} size="sm">
          {SIDE_LABELS[row.side] ?? row.side}
        </ToneBadge>
        <span className="rounded-md bg-slate-100 px-2 py-0.5 text-[12px] font-bold">{row.currency}</span>
        {row.reviewReason ? <ToneBadge tone="amber" size="sm">cần rà soát</ToneBadge> : null}
      </div>
      <p className="text-[13.5px] text-slate-600 mt-1.5 break-words">
        {fmtText(row.partnerName)}{row.purpose ? ` · ${fmtText(row.purpose)}` : ""}
      </p>
      {row.occurredAt ? <p className="text-[12.5px] text-slate-500 mt-0.5">Phát sinh: {row.occurredAt}</p> : null}
      <div className="grid grid-cols-3 gap-2 mt-3">
        {[
          { label: row.side === "obligation" ? "Phải trả" : "Số tiền", value: row.amount },
          { label: "Đã phân bổ", value: row.allocated },
          { label: row.side === "obligation" ? "Còn lại" : "Chưa phân bổ", value: row.remaining },
        ].map((cell) => (
          <div key={cell.label} className="rounded-xl bg-slate-50 border border-slate-200 p-2 text-center">
            <p className="text-[12px] font-bold uppercase tracking-wide text-slate-500">{cell.label}</p>
            <p className="text-[13px] mt-0.5"><Money value={cell.value} ccy={row.currency} /></p>
          </div>
        ))}
      </div>
      {row.reviewReason ? (
        <p className="text-[13px] mt-2.5 inline-flex items-start gap-1.5 rounded-lg bg-amber-50 border border-amber-200 px-2.5 py-1.5 text-amber-800">
          <CircleAlert size={15} className="shrink-0 mt-0.5" />
          <span>{row.reviewReason}</span>
        </p>
      ) : null}
      <div className="mt-3"><Refs row={row} /></div>
      <div className="mt-3"><OpenShipment row={row} /></div>
    </div>
  );
}

/** Filter chip row: one bounded read-only event per tap. */
function Chips({ options, value, onPick, ariaLabel }: {
  options: { value: string; label: string }[];
  value: string;
  onPick: (value: string) => void;
  ariaLabel: string;
}) {
  return (
    <div className="flex flex-wrap gap-2" role="group" aria-label={ariaLabel}>
      {options.map((option) => (
        <button
          key={option.value}
          onClick={() => onPick(option.value)}
          aria-pressed={option.value === value}
          className={cx(
            "btn-press touch-target rounded-xl border-2 px-3.5 min-h-[44px] text-[13.5px] font-bold",
            option.value === value
              ? "border-[#0f2a4a] bg-[#0f2a4a] text-white"
              : "border-slate-200 bg-white text-[#0f2a4a]"
          )}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}

export default function Reconciliation() {
  useSyncExternalStore(subscribeViewModel, getViewModel, getViewModel);
  const slice: ReconciliationSlice | null = getViewModel()?.reconciliation ?? null;

  const [query, setQuery] = useState("");
  const [pending, setPending] = useState<string | null>(null);

  const rows = slice?.rows ?? [];
  const totals = slice?.totals ?? {};
  const currencies = slice?.currencies ?? [];
  const side = slice?.side ?? "ALL";
  const state = slice?.state ?? "ALL";
  const currency = slice?.currency ?? "ALL";

  const reviewRows = useMemo(() => rows.filter((r) => r.reviewReason), [rows]);

  /** Send ONE bounded read-only filter intent; the readback is authoritative. */
  const apply = (next: { query?: string; currency?: string; state?: string; side?: string }) => {
    const payload = {
      query: next.query ?? query,
      currency: next.currency ?? currency,
      state: next.state ?? state,
      side: next.side ?? side,
    };
    // A state that the new side cannot produce would silently hide everything,
    // so switching side resets the state chip back to ALL.
    if (next.side && next.side !== side && !next.state) payload.state = "ALL";
    setPending(filterKey(payload));
    dispatchLogiEvent("reconciliation_filter", payload);
  };

  const clearFilters = () => {
    setQuery("");
    const empty = { query: "", currency: "ALL", state: "ALL", side: "ALL" };
    setPending(filterKey(empty));
    dispatchLogiEvent("reconciliation_filter", empty);
  };

  /** The readback is authoritative: pending only between intent and fresh read. */
  const echoed = slice ? filterKey({
    query: slice.query, currency: slice.currency, state: slice.state, side: slice.side,
  }) : null;
  const isPending = pending !== null && echoed !== null && pending !== echoed;

  const filtersActive = Boolean(slice && (slice.query || slice.currency !== "ALL" || slice.state !== "ALL" || slice.side !== "ALL"));

  return (
    <div className="space-y-4 max-w-[1300px]">
      {/* HEADER + FILTERS */}
      <div className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5">
        <SectionTitle
          icon={<Scale size={20} className="text-white" />}
          title="Đối soát"
          sub="Nghĩa vụ đã được phân bổ tới đâu, và khoản tiền nào chưa được phân bổ — đọc từ ledger canonical. Màn hình chỉ đọc, không ghi, không sửa số dư."
          right={
            <span className="hidden sm:inline-flex items-center gap-1.5 rounded-lg bg-slate-100 px-2.5 py-1 text-[12px] font-bold text-slate-600">
              <Lock size={13} /> CHỈ ĐỌC
            </span>
          }
        />

        <div className="flex items-center gap-2 mt-3 rounded-xl border-2 border-slate-200 focus-within:border-[#1e5aa8] bg-slate-50 overflow-hidden">
          <Search size={19} className="ml-3.5 text-slate-400 shrink-0" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter") apply({ query }); }}
            placeholder="Tìm theo mã lô, mã nghĩa vụ, mã giao dịch, phân bổ hoặc tên đối tác…"
            aria-label="Tìm trong đối soát"
            className="w-full bg-transparent px-3 py-3 min-h-[48px] text-[15px] outline-none"
          />
          <button
            onClick={() => apply({ query })}
            className="btn-press touch-target shrink-0 mr-2 rounded-lg bg-[#1e5aa8] text-white font-bold text-[13.5px] px-3.5 min-h-[40px]"
          >
            Tìm
          </button>
        </div>

        <div className="mt-3 space-y-2.5">
          <Chips ariaLabel="Lọc theo loại dòng" options={SIDES} value={side} onPick={(value) => apply({ side: value })} />
          <Chips
            ariaLabel="Lọc theo trạng thái đối soát"
            options={stateOptions(side)}
            value={stateOptions(side).some((o) => o.value === state) ? state : "ALL"}
            onPick={(value) => apply({ state: value })}
          />
          <Chips
            ariaLabel="Lọc theo tiền tệ"
            options={[{ value: "ALL", label: "Mọi tiền tệ" }, ...currencies.map((c) => ({ value: c, label: c }))]}
            value={currency}
            onPick={(value) => apply({ currency: value })}
          />
        </div>

        <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mt-3">
          <p className="text-[13px] text-slate-500">
            Hiển thị <b>{slice?.visibleCount ?? 0}</b> / {slice?.totalCount ?? 0} dòng
            {slice?.truncated ? ` (giới hạn ${slice?.maxRows})` : ""}
          </p>
          {filtersActive ? (
            /* Stated explicitly so a filtered view is never mistaken for the book. */
            <p className="text-[12.5px] text-slate-400">
              Bộ lọc chỉ thu hẹp danh sách — tổng theo tiền tệ ở dưới vẫn là toàn bộ ledger.
            </p>
          ) : null}
          {filtersActive ? (
            <button
              onClick={clearFilters}
              className="btn-press touch-target inline-flex items-center gap-1.5 rounded-xl border-2 border-slate-200 px-3.5 min-h-[44px] text-[13.5px] font-bold text-slate-600"
            >
              <Ban size={15} /> Bỏ lọc
            </button>
          ) : null}
        </div>
      </div>

      {/* PENDING: the readback is authoritative, so nothing is rendered early */}
      {isPending && (
        <div className="rounded-2xl bg-white border border-slate-200 p-8 text-center">
          <p className="text-[15px] font-semibold text-slate-500">Đang đọc ledger canonical…</p>
        </div>
      )}

      {/* NO SOURCE — the database could not be read. Never a balanced 0 book. */}
      {slice && slice.status === "NO_SOURCE" && (
        <div className="rounded-2xl bg-white border-2 border-dashed border-red-300 p-8 text-center">
          <span className="mx-auto w-14 h-14 rounded-2xl bg-red-50 text-red-600 grid place-items-center">
            <CircleAlert size={26} />
          </span>
          <h3 className="text-[16px] font-extrabold text-[#0f2a4a] mt-3">Chưa đọc được ledger canonical</h3>
          <p className="text-[14px] text-slate-500 mt-1 max-w-[640px] mx-auto leading-relaxed">
            {slice.error ?? "Không có kết nối tới cơ sở dữ liệu."} Hệ thống không tự tạo số liệu thay thế:
            trạng thái là <b>chưa xác định</b>, không phải 0.
          </p>
        </div>
      )}

      {/* EMPTY — real ledger, no reconciliation record yet */}
      {slice && slice.status === "EMPTY" && (
        <div className="rounded-2xl border-2 border-dashed border-slate-300 bg-white p-10 text-center">
          <span className="mx-auto w-14 h-14 rounded-2xl bg-slate-100 text-slate-400 grid place-items-center">
            <Scale size={26} />
          </span>
          <h3 className="text-[16px] font-extrabold text-[#0f2a4a] mt-3">Chưa có bản ghi đối soát</h3>
          <p className="text-[14px] text-slate-500 mt-1 max-w-[620px] mx-auto leading-relaxed">
            Chưa có nghĩa vụ hay giao dịch canonical nào gắn với lô hàng. Đây là trạng thái
            <b> chưa có dữ liệu</b>, không phải công nợ bằng 0.
          </p>
        </div>
      )}

      {slice && slice.status !== "EMPTY" && slice.status !== "NO_SOURCE" && (
        <>
          {/* PER-CURRENCY TOTALS — separate blocks; never summed across currencies */}
          {currencies.length > 0 && (
            <div className="grid gap-3 md:grid-cols-2">
              {currencies.map((ccy) => {
                const bucket = totals[ccy];
                if (!bucket) return null;
                const states = bucket.states ?? {};
                return (
                  <div key={ccy} className="rounded-2xl bg-white border border-slate-200 p-4">
                    <div className="flex items-center gap-2 flex-wrap">
                      <h3 className="text-[16px] font-extrabold text-[#0f2a4a]">{ccy}</h3>
                      {ccy === "UNKNOWN" ? (
                        <ToneBadge tone="gray" size="sm">chưa rõ tiền tệ</ToneBadge>
                      ) : null}
                      {bucket.review.count > 0 ? (
                        <ToneBadge tone="amber" size="sm">{bucket.review.count} dòng cần rà soát</ToneBadge>
                      ) : null}
                    </div>
                    <p className="text-[12px] text-slate-400 mt-0.5">
                      {bucket.obligations.count} nghĩa vụ · {bucket.money.count} giao dịch
                    </p>
                    <div className="grid grid-cols-3 gap-2 mt-3">
                      <div className="rounded-xl bg-slate-50 border border-slate-200 p-2.5 text-center">
                        <p className="text-[12px] font-bold uppercase tracking-wide text-slate-500">Phải trả</p>
                        <p className="text-[13.5px] mt-0.5"><Money value={bucket.obligations.amount} ccy={ccy} /></p>
                      </div>
                      <div className="rounded-xl bg-slate-50 border border-slate-200 p-2.5 text-center">
                        <p className="text-[12px] font-bold uppercase tracking-wide text-slate-500">Đã phân bổ</p>
                        <p className="text-[13.5px] mt-0.5"><Money value={bucket.obligations.allocated} ccy={ccy} /></p>
                      </div>
                      <div className="rounded-xl bg-amber-50 border border-amber-200 p-2.5 text-center">
                        <p className="text-[12px] font-bold uppercase tracking-wide text-amber-700">Còn lại</p>
                        <p className="text-[13.5px] mt-0.5"><Money value={bucket.obligations.remaining} ccy={ccy} strong /></p>
                      </div>
                    </div>
                    <p className="text-[12.5px] text-slate-500 mt-2.5">
                      Tiền chưa phân bổ: <Money value={bucket.money.unallocated} ccy={ccy} />
                    </p>
                    <div className="flex flex-wrap gap-1.5 mt-2.5">
                      {Object.entries(states).filter(([, count]) => count > 0).map(([key, count]) => (
                        <span key={key} className="rounded-md bg-slate-100 px-2 py-0.5 text-[12px] font-semibold text-slate-600">
                          {key}: {count}
                        </span>
                      ))}
                    </div>
                    {bucket.review.count > 0 ? (
                      <p className="text-[12.5px] mt-2 text-amber-800">
                        Trong đó cần rà soát: <Money value={bucket.review.amount} ccy={ccy} />
                      </p>
                    ) : null}
                  </div>
                );
              })}
            </div>
          )}

          {/* REVIEW FIRST — the point of a reconciliation desk */}
          {reviewRows.length > 0 && (
            <div className="rounded-2xl bg-amber-50 border-2 border-amber-200 p-4">
              <p className="inline-flex items-center gap-1.5 text-[14px] font-extrabold text-amber-900">
                <CircleAlert size={16} /> {reviewRows.length} dòng cần rà soát
              </p>
              <ul className="mt-2 space-y-1">
                {reviewRows.slice(0, 8).map((row) => (
                  <li key={row.id} className="text-[13px] text-amber-900 break-words">
                    <b>{row.shipmentId}</b> · {fmtText(row.partnerName)} · {row.currency} — {row.reviewReason}
                  </li>
                ))}
              </ul>
              <p className="text-[12.5px] text-amber-800 mt-2">
                Dòng cần rà soát vẫn được cộng trong tổng của tiền tệ đó và được nêu riêng ở đây —
                không bị ẩn, cũng không tự động coi là đã đối soát.
              </p>
            </div>
          )}

          {/* ROWS */}
          {rows.length === 0 ? (
            <div className="rounded-2xl border-2 border-dashed border-slate-300 bg-white p-8 text-center">
              <p className="text-[15px] font-extrabold text-[#0f2a4a]">Không có dòng nào khớp bộ lọc</p>
              <p className="text-[13.5px] text-slate-500 mt-1">
                Tổng theo tiền tệ ở trên vẫn là toàn bộ ledger — bộ lọc không làm thay đổi số tổng.
              </p>
            </div>
          ) : (
            <>
              {/* Mobile / narrow: stacked cards, no horizontal page scroll */}
              <div className="space-y-3 md:hidden">
                {rows.map((row) => <RowCard key={row.id} row={row} />)}
              </div>

              {/* Wide: table */}
              <div className="hidden md:block rounded-2xl bg-white border border-slate-200 overflow-hidden">
                <table className="w-full text-[13.5px]">
                  <thead className="bg-slate-50 text-slate-500">
                    <tr>
                      {["Lô hàng", "Đối tác", "Loại", "Trạng thái", "Số tiền", "Đã phân bổ", "Còn lại", "Tiền tệ", "Thao tác"]
                        .map((head) => (
                          <th key={head} className="text-left font-bold text-[12px] uppercase tracking-wide px-3 py-2.5">{head}</th>
                        ))}
                    </tr>
                  </thead>
                  <tbody>
                    {rows.map((row) => (
                      <tr key={row.id} className="border-t border-slate-100 align-top">
                        <td className="px-3 py-2.5">
                          <p className="font-extrabold text-[#0f2a4a] break-all">{row.shipmentId}</p>
                          <Refs row={row} />
                        </td>
                        <td className="px-3 py-2.5 break-words">
                          <p className="font-semibold">{fmtText(row.partnerName)}</p>
                          {row.purpose ? <p className="text-[12px] text-slate-500">{row.purpose}</p> : null}
                          {row.occurredAt ? <p className="text-[12px] text-slate-500">{row.occurredAt}</p> : null}
                        </td>
                        <td className="px-3 py-2.5 whitespace-nowrap">{SIDE_LABELS[row.side] ?? row.side}</td>
                        <td className="px-3 py-2.5">
                          <StateBadge row={row} />
                          {row.reviewReason ? (
                            <p className="text-[12px] text-amber-800 mt-1 break-words">{row.reviewReason}</p>
                          ) : null}
                        </td>
                        <td className="px-3 py-2.5"><Money value={row.amount} ccy={row.currency} /></td>
                        <td className="px-3 py-2.5"><Money value={row.allocated} ccy={row.currency} /></td>
                        <td className="px-3 py-2.5"><Money value={row.remaining} ccy={row.currency} strong /></td>
                        <td className="px-3 py-2.5 whitespace-nowrap font-bold">{row.currency}</td>
                        <td className="px-3 py-2.5"><OpenShipment row={row} /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}

          {/* WHERE THE WRITE LIVES — navigation only, never a second writer */}
          <div className="rounded-2xl bg-white border border-slate-200 p-4">
            <p className="inline-flex items-center gap-1.5 text-[13px] font-extrabold uppercase tracking-wide text-slate-500">
              <Wallet size={15} /> Ghi nhận ở đâu
            </p>
            <p className="text-[13px] text-slate-500 mt-1">
              Bàn đối soát không ghi. Ghi nhận phải trả, thanh toán đối tác và thu tiền khách
              vẫn đi qua writer canonical có RBAC, audit và idempotency riêng.
            </p>
            <div className="flex flex-wrap gap-2 mt-3">
              {(slice.actions ?? []).map((action) => (
                <Link
                  key={action.href}
                  to={action.href}
                  className="btn-press touch-target inline-flex items-center gap-1.5 rounded-xl border-2 border-[#1e5aa8] text-[#1e5aa8] font-bold text-[13.5px] px-3.5 min-h-[44px]"
                >
                  <ArrowUpRight size={15} /> {action.label}
                </Link>
              ))}
            </div>
          </div>

          {/* HONEST GAPS — what this desk is NOT, stated rather than implied */}
          {(slice.unavailable ?? []).length > 0 && (
            <div className="rounded-2xl bg-slate-50 border border-slate-200 p-4">
              <p className="inline-flex items-center gap-1.5 text-[13px] font-extrabold uppercase tracking-wide text-slate-500">
                <Info size={15} /> Ngoài phạm vi bàn này
              </p>
              <ul className="mt-2 space-y-1">
                {(slice.unavailable ?? []).map((item) => (
                  <li key={item} className="text-[13px] text-slate-600 break-words">· {item}</li>
                ))}
              </ul>
            </div>
          )}
        </>
      )}
    </div>
  );
}
