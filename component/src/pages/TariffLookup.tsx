// BIỂU THUẾ — fast indexed lookup over an Admin-managed SQLite asset.
// Runtime never loads the XLSX. ADMIN upload builds SQLite once server-side;
// code lookup uses a B-tree index and product/policy text uses FTS5.

import { useEffect, useRef, useState, useSyncExternalStore } from "react";
import {
  AlertTriangle,
  CloudUpload,
  Database,
  Info,
  LoaderCircle,
  Search,
} from "lucide-react";
import { SectionTitle } from "../components/ui";
import { dispatchLogiEvent } from "../lib/dispatcher";
import { UNKNOWN } from "../lib/format";
import {
  getViewModel,
  subscribeViewModel,
  type TariffRow,
} from "../lib/viewmodel";

const MAX_SOURCE_BYTES = 12 * 1024 * 1024;

function val(value: string | null | undefined): string {
  return value ? value : UNKNOWN;
}

function requestId(): string {
  return `TARIFF-${Date.now().toString(36).toUpperCase()}-${Math.random()
    .toString(36)
    .slice(2, 8)
    .toUpperCase()}`;
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
  const vm = useSyncExternalStore(subscribeViewModel, getViewModel, getViewModel);
  const tariff = vm?.tariff ?? null;
  const source = tariff?.source;

  const [query, setQuery] = useState("");
  const [submitted, setSubmitted] = useState("");
  const [sourceFile, setSourceFile] = useState<File | null>(null);
  const [pendingUpload, setPendingUpload] = useState("");
  const [uploadError, setUploadError] = useState("");
  const [uploadMessage, setUploadMessage] = useState("");
  const fileRef = useRef<HTMLInputElement | null>(null);

  const pending = submitted.length > 0 && submitted !== (tariff?.query ?? "");
  const rows = tariff?.rows ?? [];
  const showResults = Boolean(tariff?.searched) && !pending;

  useEffect(() => {
    if (!pendingUpload) return;
    const outcome = vm?.lastWrites?.find(
      (item) =>
        item.event === "tariff_source_upload" &&
        item.requestId === pendingUpload,
    );
    if (!outcome) return;
    setPendingUpload("");
    if (outcome.ok) {
      const readback = outcome.readback as
        | { sourceFile?: string; rows?: number; year?: string }
        | undefined;
      setUploadError("");
      setUploadMessage(
        `Đã cập nhật ${readback?.sourceFile || "BIỂU THUẾ"} · ${(
          readback?.rows ?? 0
        ).toLocaleString("vi-VN")} dòng mã HS${readback?.year ? ` · ${readback.year}` : ""}.`,
      );
      setSourceFile(null);
      if (fileRef.current) fileRef.current.value = "";
    } else {
      setUploadMessage("");
      setUploadError(outcome.error || "Không cập nhật được BIỂU THUẾ.");
    }
  }, [pendingUpload, vm?.lastWrites]);

  const submit = () => {
    const q = query.trim();
    if (q.length < 2 || !source?.configured) return;
    setSubmitted(q);
    dispatchLogiEvent("tariff_lookup", { query: q });
  };

  const upload = () => {
    setUploadError("");
    setUploadMessage("");
    if (!sourceFile) {
      setUploadError("Chưa chọn file BIỂU THUẾ .xlsx.");
      return;
    }
    if (!sourceFile.name.toLowerCase().endsWith(".xlsx")) {
      setUploadError("Chỉ nhận file .xlsx.");
      return;
    }
    if (sourceFile.size <= 0 || sourceFile.size > MAX_SOURCE_BYTES) {
      setUploadError("File phải lớn hơn 0 và không vượt 12 MB.");
      return;
    }

    const id = requestId();
    setPendingUpload(id);
    const reader = new FileReader();
    reader.onerror = () => {
      setPendingUpload("");
      setUploadError("Không đọc được file trên trình duyệt.");
    };
    reader.onload = () => {
      const dataUrl = typeof reader.result === "string" ? reader.result : "";
      const comma = dataUrl.indexOf(",");
      const base64 = comma >= 0 ? dataUrl.slice(comma + 1) : dataUrl;
      if (!base64) {
        setPendingUpload("");
        setUploadError("File không có dữ liệu.");
        return;
      }
      const sent = dispatchLogiEvent("tariff_source_upload", {
        fileName: sourceFile.name,
        mime: sourceFile.type,
        size: sourceFile.size,
        base64,
        requestId: id,
      });
      if (!sent) {
        setPendingUpload("");
        setUploadError("Component chưa kết nối backend.");
      }
    };
    reader.readAsDataURL(sourceFile);
  };

  return (
    <div className="max-w-[1400px] space-y-4">
      <div className="rounded-2xl border border-slate-200 bg-white p-4 md:p-5">
        <SectionTitle
          icon={<Search size={18} />}
          title="BIỂU THUẾ"
          sub="Gõ mã HS hoặc tên hàng; app chỉ query các dòng khớp từ SQLite có chỉ mục, không tải cả Excel lên màn hình."
        />

        {source?.canManage && (
          <details className="mb-4 rounded-xl border border-slate-200 bg-slate-50/60">
            <summary className="cursor-pointer px-3.5 py-3 text-[13px] font-extrabold text-[#0f2a4a]">
              Quản trị nguồn BIỂU THUẾ
            </summary>
            <div className="border-t border-slate-200 p-3.5">
              <p className="text-[12.5px] text-slate-600">
                ADMIN chọn file .xlsx mới. Backend build SQLite + index + FTS,
                nén và lưu bền trong Mongo. Những lần tra cứu sau không đọc Excel.
              </p>
              <div className="mt-3 flex flex-col gap-2 md:flex-row md:items-center">
                <input
                  ref={fileRef}
                  type="file"
                  accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                  onChange={(event) => {
                    setSourceFile(event.target.files?.[0] ?? null);
                    setUploadError("");
                    setUploadMessage("");
                  }}
                  className="min-h-[44px] min-w-0 flex-1 rounded-xl border border-slate-200 bg-white px-3 py-2 text-[13px]"
                  data-testid="tariff-source-file"
                />
                <button
                  type="button"
                  onClick={upload}
                  disabled={!sourceFile || Boolean(pendingUpload)}
                  className="inline-flex min-h-[44px] shrink-0 items-center justify-center gap-2 rounded-xl bg-[#0f2a4a] px-4 text-[13px] font-extrabold text-white disabled:opacity-40"
                  data-testid="tariff-source-upload"
                >
                  {pendingUpload ? (
                    <LoaderCircle size={16} className="animate-spin" />
                  ) : (
                    <CloudUpload size={16} />
                  )}
                  {pendingUpload ? "ĐANG BUILD DB…" : "CẬP NHẬT FILE"}
                </button>
              </div>
              {uploadError && (
                <p className="mt-2 rounded-lg bg-red-50 px-3 py-2 text-[12.5px] font-semibold text-red-700">
                  {uploadError}
                </p>
              )}
              {uploadMessage && (
                <p className="mt-2 rounded-lg bg-emerald-50 px-3 py-2 text-[12.5px] font-semibold text-emerald-800">
                  {uploadMessage}
                </p>
              )}
            </div>
          </details>
        )}

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
            disabled={query.trim().length < 2 || !source?.configured}
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
            {source?.configured
              ? "Nhập mã HS hoặc tên hàng để tra"
              : "Chưa có dữ liệu BIỂU THUẾ"}
          </h3>
          <p className="mt-1 text-[13.5px] text-slate-500">
            {source?.configured
              ? "Mã 8 số tra bằng index; mã ngắn tra prefix; tên hàng tra bằng FTS."
              : source?.canManage
                ? "Mở Quản trị nguồn BIỂU THUẾ phía trên và tải file .xlsx."
                : "Liên hệ ADMIN để nạp file BIỂU THUẾ."}
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
                      <span className="rounded-lg bg-slate-100 px-2 py-1 text-[12px] font-bold text-slate-600">
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
