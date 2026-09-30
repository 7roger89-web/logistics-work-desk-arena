// BIỂU THUẾ — fast indexed lookup over the governed SQLite tariff database.
// Runtime never loads the XLSX. HS code lookup uses the SQLite B-tree index;
// Vietnamese product/policy text uses FTS5. Only bounded matching rows reach UI.

import { useState, useSyncExternalStore } from "react";
import { AlertTriangle, Database, Info, Search } from "lucide-react";
import { SectionTitle } from "../components/ui";
import { dispatchLogiEvent } from "../lib/dispatcher";
import { UNKNOWN } from "../lib/format";
import {
  getViewModel,
  subscribeViewModel,
  type TariffRow,
} from "../lib/viewmodel";

function val(value: string | null | undefined): string {
  return value ? value : UNKNOWN;
}

function Rate({ label, value }: { label: string; value: string | null }) {
  return (
    <span className="inline-flex items-center gap-1 rounded-lg border border-slate-200 bg-slate-50 px-2 py-1 text-[12px]">
      <span className="font-semibold text-slate-500">{label}</span>
      <span className="font-extrabold text-[#0f2a4a]">{val(value)}</span>
    </span>
  );
}

function MoreRates({ row }: { row: TariffRow }) {
  if (!row.fields.length) return null;
  return (
    <details className="mt-2">
      <summary className="cursor-pointer text-[12.5px] font-bold text-[#1e5aa8]">
        Thuế FTA / XK / sắc thuế khác ({row.fields.length})
      </summary>
      <div className="mt-2 flex flex-wrap gap-1.5">
        {row.fields.map((field) => (
          <Rate key={field.label} label={field.label} value={field.value} />
        ))}
      </div>
    </details>
  );
}

export default function TariffLookup() {
  useSyncExternalStore(subscribeViewModel, getViewModel, getViewModel);
  const tariff = getViewModel()?.tariff ?? null;
  const [query, setQuery] = useState("");
  const [submitted, setSubmitted] = useState("");

  const pending = submitted.length > 0 && submitted !== (tariff?.query ?? "");
  const rows = tariff?.rows ?? [];
  const showResults = Boolean(tariff?.searched) && !pending;

  const submit = () => {
    const q = query.trim();
    if (q.length < 2) return;
    setSubmitted(q);
    dispatchLogiEvent("tariff_lookup", { query: q });
  };

  const source = tariff?.source;

  return (
    <div className="max-w-[1400px] space-y-4">
      <div className="rounded-2xl border border-slate-200 bg-white p-4 md:p-5">
        <SectionTitle
          icon={<Search size={18} />}
          title="BIỂU THUẾ"
          sub="Tra cứu Biểu thuế XNK 2026 theo mã HS hoặc tên hàng. Hệ thống chỉ query các dòng khớp từ SQLite có chỉ mục, không tải toàn bộ Excel lên màn hình."
        />

        <form
          className="flex flex-col gap-2.5 md:flex-row"
          onSubmit={(event) => {
            event.preventDefault();
            submit();
          }}
        >
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Ví dụ: 01012900, 0101, 9403.20 hoặc ghế gỗ…"
            className="min-h-[48px] flex-1 rounded-xl border-2 border-slate-200 px-4 font-mono text-[15px] outline-none placeholder:font-sans focus:border-[#1e5aa8]"
            aria-label="Mã HS hoặc tên hàng"
            autoComplete="off"
          />
          <button
            type="submit"
            disabled={query.trim().length < 2}
            className="inline-flex min-h-[48px] items-center justify-center gap-2 rounded-xl bg-[#0f2a4a] px-5 text-[14.5px] font-bold text-white disabled:pointer-events-none disabled:opacity-40"
          >
            <Search size={17} /> Tra cứu
          </button>
        </form>

        {source && (
          <div
            className={
              "mt-3 flex items-start gap-2.5 rounded-xl border p-3 text-[13px] " +
              (source.configured && source.rows
                ? "border-emerald-200 bg-emerald-50/50 text-slate-700"
                : "border-amber-200 bg-amber-50 text-amber-900")
            }
          >
            <Database size={16} className="mt-0.5 shrink-0" />
            {source.configured && source.rows ? (
              <div>
                <p>
                  <b>{source.sourceFile || "SQLite tariff_table"}</b>
                  {source.year ? ` · năm ${source.year}` : ""}
                  {" · "}
                  {source.rows.toLocaleString("vi-VN")} dòng có mã HS.
                </p>
                {source.searchMode && (
                  <p className="mt-0.5 text-[12px] text-slate-500">
                    {source.searchMode}
                  </p>
                )}
                {tariff?.truncated && (
                  <p className="mt-1 font-semibold">
                    Đang giới hạn {tariff.limit} kết quả — nhập mã/từ khóa cụ thể hơn.
                  </p>
                )}
              </div>
            ) : (
              <p className="font-semibold">{source.note}</p>
            )}
          </div>
        )}

        {tariff?.provenance && (
          <div className="mt-2.5 flex items-start gap-2.5 rounded-xl border border-amber-200 bg-amber-50/60 p-3 text-[12.5px] text-amber-900">
            <AlertTriangle size={16} className="mt-0.5 shrink-0" />
            <p>{tariff.provenance.note}</p>
          </div>
        )}
      </div>

      {pending && (
        <div className="rounded-2xl border border-slate-200 bg-white p-8 text-center">
          <p className="text-[15px] font-semibold text-slate-500">
            Đang tra “{submitted}”…
          </p>
        </div>
      )}

      {!pending && !showResults && (
        <div className="rounded-2xl border-2 border-dashed border-slate-300 bg-white p-10 text-center">
          <Search size={26} className="mx-auto text-slate-400" />
          <h3 className="mt-3 text-[16px] font-extrabold text-[#0f2a4a]">
            Nhập mã HS hoặc tên hàng để tra
          </h3>
          <p className="mt-1 text-[13.5px] text-slate-500">
            Mã 8 số tra trực tiếp bằng index; mã ngắn tra theo prefix; tên hàng tra bằng FTS.
          </p>
        </div>
      )}

      {showResults && tariff && rows.length === 0 && (
        <div className="rounded-2xl border border-slate-200 bg-white p-8 text-center">
          <Info size={26} className="mx-auto text-amber-700" />
          <h3 className="mt-3 text-[16px] font-extrabold text-[#0f2a4a]">
            Không tìm thấy kết quả
          </h3>
          <p className="mt-1 text-[14px] text-slate-500">{tariff.reason}</p>
        </div>
      )}

      {showResults && tariff && rows.length > 0 && (
        <div className="space-y-3">
          <p className="px-1 text-[13.5px] font-semibold text-slate-500">
            {tariff.count.toLocaleString("vi-VN")} dòng khớp “{tariff.query}”
          </p>

          {rows.map((row, index) => (
            <article
              key={(row.hsCode ?? "?") + "-" + index}
              className="rounded-2xl border border-slate-200 bg-white p-4"
            >
              <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-mono text-[18px] font-black text-[#0f2a4a]">
                      {val(row.hsCode)}
                    </span>
                    {row.unit && (
                      <span className="rounded-lg bg-slate-100 px-2 py-1 text-[11.5px] font-bold text-slate-600">
                        ĐVT: {row.unit}
                      </span>
                    )}
                  </div>
                  <p className="mt-1 text-[15px] font-semibold text-slate-800">
                    {val(row.descriptionVi)}
                  </p>
                </div>

                <div className="flex shrink-0 flex-wrap gap-1.5">
                  <Rate label="NK TT" value={row.importNormal} />
                  <Rate label="NK ưu đãi" value={row.importPreferential} />
                  <Rate label="VAT" value={row.vat} />
                </div>
              </div>

              {(row.policy || row.vatReduction) && (
                <div className="mt-3 grid gap-2 md:grid-cols-2">
                  {row.policy && (
                    <div className="rounded-xl border border-blue-100 bg-blue-50/50 p-3 text-[12.5px] text-slate-700">
                      <p className="mb-1 font-extrabold text-[#0f2a4a]">
                        Chính sách mặt hàng
                      </p>
                      <p>{row.policy}</p>
                    </div>
                  )}
                  {row.vatReduction && (
                    <div className="rounded-xl border border-amber-100 bg-amber-50/60 p-3 text-[12.5px] text-slate-700">
                      <p className="mb-1 font-extrabold text-amber-900">
                        Giảm VAT
                      </p>
                      <p>{row.vatReduction}</p>
                    </div>
                  )}
                </div>
              )}

              <MoreRates row={row} />
            </article>
          ))}
        </div>
      )}
    </div>
  );
}
