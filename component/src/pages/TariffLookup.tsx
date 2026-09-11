// ============================================================================
// LOGI_TARIFF_LOOKUP_01 — /tra-cuu-thue (Tra cứu HS & Thuế).
//
// REAL_BACKED read-only workspace over the EXISTING canonical reader
// (core.utils.fast_search_tariff → governed TARIFF_DB_PATH reference data).
// No mock data, no fabricated rates: every field the internal reference
// schema does not carry renders as an explicit "—" (UNKNOWN != ZERO), and
// the provenance banner states plainly that this is not an official
// customs ruling. Donor UI patterns only (search card + responsive
// table/cards) — no new design system, router, store or API.
// ============================================================================

import { useState, useSyncExternalStore } from "react";
import { Search, AlertTriangle, Info, Database } from "lucide-react";
import { SectionTitle, inputCls } from "../components/ui";
import { dispatchLogiEvent } from "../lib/dispatcher";
import { cx, UNKNOWN } from "../lib/format";
import {
  getViewModel,
  subscribeViewModel,
  type TariffRow,
} from "../lib/viewmodel";

function orUnknown(value: string | null | undefined): string {
  return value ? value : UNKNOWN;
}

function ExtraFields({ row, stacked }: { row: TariffRow; stacked?: boolean }) {
  if (!row.fields.length) return <span className="text-slate-400">{UNKNOWN}</span>;
  return (
    <span className={cx("text-[13.5px] text-slate-700", stacked && "block")}>
      {row.fields.map((f) => (
        <span key={f.label} className={cx(!stacked && "mr-3 whitespace-nowrap")}>
          <span className="font-semibold text-slate-500">{f.label}:</span>{" "}
          <span className="font-bold">{orUnknown(f.value)}</span>
        </span>
      ))}
    </span>
  );
}

export default function TariffLookup() {
  useSyncExternalStore(subscribeViewModel, getViewModel, getViewModel);
  const vm = getViewModel();
  const tariff = vm?.tariff ?? null;
  const [query, setQuery] = useState("");
  const [submitted, setSubmitted] = useState("");

  const pending = submitted.length > 0 && submitted !== (tariff?.query ?? "");
  const rows = tariff?.rows ?? [];
  // The delivered slice is the last AUTHORITATIVE read for tariff.query — it
  // stays visible across navigation; `pending` covers only the in-flight gap
  // between submit and the fresh readback.
  const showResults = Boolean(tariff?.searched) && !pending;

  const submit = () => {
    const q = query.trim();
    if (q.length < 2) return; // the canonical reader requires >= 2 chars
    setSubmitted(q);
    dispatchLogiEvent("tariff_lookup", { query: q });
  };

  const source = tariff?.source;
  const provenance = tariff?.provenance;

  return (
    <div className="space-y-4 max-w-[1300px]">
      {/* Search card — exact / partial HS code or product keyword. All three
          inputs are genuinely supported by the existing LIKE-based reader. */}
      <div className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5">
        <SectionTitle
          icon={<Search size={18} />}
          title="Tra cứu HS & Thuế"
          sub="Tra cứu mã HS và mô tả hàng hóa tại cơ sở dữ liệu tham chiếu nội bộ — nhập mã HS (chính xác hoặc một phần) hoặc tên hàng."
        />
        <form
          className="flex flex-col md:flex-row gap-2.5"
          onSubmit={(e) => {
            e.preventDefault();
            submit();
          }}
        >
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ví dụ: 9401, 9403.20 hoặc ghế gỗ…"
            className="flex-1 rounded-xl border-2 border-slate-200 px-4 min-h-[48px] text-[15px] font-mono placeholder:font-sans focus:border-[#1e5aa8] outline-none"
            aria-label="Mã HS hoặc tên hàng"
          />
          <button
            type="submit"
            disabled={query.trim().length < 2}
            className="btn-press touch-target inline-flex items-center justify-center gap-2 rounded-xl bg-[#0f2a4a] text-white font-bold text-[14.5px] px-5 min-h-[48px] disabled:opacity-40 disabled:pointer-events-none"
          >
            <Search size={17} /> Tra cứu
          </button>
        </form>

        {/* Honest data-source status — what the backend actually knows. */}
        {source && (
          <div
            className={cx(
              "mt-3 rounded-xl border p-3 flex items-start gap-2.5 text-[13px]",
              source.configured && source.rows
                ? "border-slate-200 bg-slate-50 text-slate-600"
                : "border-amber-200 bg-amber-50 text-amber-900"
            )}
          >
            <Database size={16} className="shrink-0 mt-0.5" />
            <div>
              {source.configured && source.rows ? (
                <p>
                  Nguồn nội bộ: <b>tariff_table</b> · {source.rows.toLocaleString("vi-VN")} dòng ·{" "}
                  <span className="font-mono text-[12px] break-all">{source.path}</span>
                </p>
              ) : (
                <p className="font-semibold">{source.note}</p>
              )}
              {tariff?.truncated && (
                <p className="mt-1 font-semibold">
                  Kết quả bị giới hạn {tariff.limit} dòng — hãy nhập mã HS cụ thể hơn.
                </p>
              )}
            </div>
          </div>
        )}

        {/* Provenance banner — preserved from the backend, never invented.
            This is NOT an official customs ruling. */}
        {provenance && (
          <div className="mt-2.5 rounded-xl border-2 border-dashed border-amber-300 bg-amber-50/60 p-3 flex items-start gap-2.5 text-[13px] text-amber-900">
            <AlertTriangle size={16} className="shrink-0 mt-0.5" />
            <p>{provenance.note}</p>
          </div>
        )}
      </div>

      {/* Pending state */}
      {pending && (
        <div className="rounded-2xl bg-white border border-slate-200 p-8 text-center">
          <p className="text-[15px] font-semibold text-slate-500">Đang tra cứu “{submitted}”…</p>
        </div>
      )}

      {/* Idle state — obvious, honest, no fake rows */}
      {!pending && !showResults && (
        <div className="rounded-2xl border-2 border-dashed border-slate-300 bg-white p-10 text-center">
          <span className="mx-auto w-14 h-14 rounded-2xl bg-slate-100 text-slate-400 grid place-items-center">
            <Search size={26} />
          </span>
          <h3 className="text-[16px] font-extrabold text-[#0f2a4a] mt-3">Bảng kết quả đang trống</h3>
          <p className="text-[14px] text-slate-500 mt-1">
            Nhập mã HS hoặc tên hàng phía trên rồi bấm <b>Tra cứu</b>.
          </p>
        </div>
      )}

      {/* No-match state */}
      {showResults && tariff && rows.length === 0 && (
        <div className="rounded-2xl bg-white border border-slate-200 p-8 text-center">
          <span className="mx-auto w-14 h-14 rounded-2xl bg-amber-100 text-amber-700 grid place-items-center">
            <Info size={26} />
          </span>
          <h3 className="text-[16px] font-extrabold text-[#0f2a4a] mt-3">Không tìm thấy kết quả</h3>
          <p className="text-[14px] text-slate-500 mt-1">{tariff.reason}</p>
        </div>
      )}

      {/* Results */}
      {showResults && tariff && rows.length > 0 && (
        <div className="space-y-4">
          <p className="text-[13.5px] font-semibold text-slate-500 px-1">
            Tìm thấy {tariff.count.toLocaleString("vi-VN")} dòng khớp “{tariff.query}” — mã HS và mô tả
            theo dữ liệu tham chiếu nội bộ.
          </p>

          {/* Desktop table */}
          <div className="hidden md:block rounded-2xl bg-white border border-slate-200 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="tbl w-full text-[14.5px]">
                <thead>
                  <tr>
                    <th className="w-[150px]">Mã HS</th>
                    <th>Mô tả tiếng Việt</th>
                    <th>Mô tả tiếng Anh</th>
                    <th>Thông tin khác (nguyên văn)</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row, i) => (
                    <tr key={(row.hsCode ?? "?") + i} className="hover:bg-slate-50">
                      <td className="font-mono font-extrabold text-[15px] text-[#0f2a4a] whitespace-nowrap">
                        {orUnknown(row.hsCode)}
                      </td>
                      <td className="font-semibold">{orUnknown(row.descriptionVi)}</td>
                      <td className="text-slate-600">{orUnknown(row.descriptionEn)}</td>
                      <td><ExtraFields row={row} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Mobile cards */}
          <div className="md:hidden space-y-3">
            {rows.map((row, i) => (
              <div key={(row.hsCode ?? "?") + i} className="rounded-2xl bg-white border border-slate-200 p-4">
                <p className="font-mono font-extrabold text-[17px] text-[#0f2a4a] break-all">
                  {orUnknown(row.hsCode)}
                </p>
                <p className="text-[15px] font-semibold text-slate-800 mt-1.5">
                  {orUnknown(row.descriptionVi)}
                </p>
                <p className="text-[13px] text-slate-500 mt-0.5">{orUnknown(row.descriptionEn)}</p>
                {row.fields.length > 0 && (
                  <div className="mt-2.5 rounded-xl bg-slate-50 border border-slate-200 p-3">
                    <p className="text-[12px] font-bold uppercase tracking-wide text-slate-400">
                      Thông tin khác (nguyên văn)
                    </p>
                    <div className="mt-1">
                      <ExtraFields row={row} stacked />
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
