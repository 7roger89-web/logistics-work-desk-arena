// ============================================================================
// LOGI_QUOTE_COST_WORKFLOW_UX_01 — "DÁN BÁO GIÁ NHANH" / "DÁN THÔNG TIN KHÁCH".
//
// ONE compact paste → PARSE → REVIEW → APPLY block, shared by the Báo Giá
// create/edit modal and the Check chi phí workspace. It uses the ONE shared
// deterministic parser (lib/quoteTextParser) — never a copy, never an LLM.
//
// UX CONTRACT (owner rule): pasting NEVER mutates anything. The operator must
// press PHÂN TÍCH to see a review preview, may edit the values afterwards in
// the real form, and only an explicit "ÁP DỤNG" writes into the form state.
// ============================================================================

import { useState } from "react";
import { CircleAlert, Eraser, ScanText, Wand2 } from "lucide-react";
import { cx, fmtMoney } from "../lib/format";
import { isEmptyParse, parseQuoteText, type ParsedQuote } from "../lib/quoteTextParser";

export interface QuickQuotePasteProps {
  /** Block heading, e.g. "DÁN BÁO GIÁ NHANH". */
  title: string;
  /** One-line explanation under the heading. */
  hint: string;
  /** Label of the apply button, e.g. "ÁP DỤNG VÀO BÁO GIÁ". */
  applyLabel: string;
  /** data-testid prefix so both hosts stay independently checkable. */
  testId: string;
  placeholder?: string;
  /** Called ONLY on an explicit apply click. */
  onApply: (parsed: ParsedQuote) => void;
}

export default function QuickQuotePaste({
  title, hint, applyLabel, testId, placeholder, onApply,
}: QuickQuotePasteProps) {
  const [text, setText] = useState("");
  const [parsed, setParsed] = useState<ParsedQuote | null>(null);
  const [error, setError] = useState("");

  const analyse = () => {
    if (!text.trim()) {
      setParsed(null);
      setError("Chưa có nội dung để phân tích — dán báo giá vào ô trên.");
      return;
    }
    const result = parseQuoteText(text);
    if (isEmptyParse(result)) {
      setParsed(null);
      setError("Không đọc được thông tin nào — kiểm tra lại định dạng “tên dịch vụ: giá/đơn vị”.");
      return;
    }
    setError("");
    setParsed(result);
    // The review sits under the textarea inside a tall modal. Bring the
    // line count into view so a 9-line paste is not hidden below the fold.
    if (typeof requestAnimationFrame === "function") {
      requestAnimationFrame(() => {
        document.querySelector(`[data-testid="${testId}-preview"]`)?.scrollIntoView({ block: "start" });
      });
    }
  };

  const clear = () => { setParsed(null); setError(""); setText(""); };

  return (
    <section
      data-testid={testId}
      className="rounded-2xl border-2 border-[#1e5aa8]/30 bg-blue-50/50 p-3.5"
    >
      <div className="flex flex-wrap items-center gap-2">
        <p className="font-extrabold text-[15px] text-[#0f2a4a] flex items-center gap-1.5">
          <ScanText size={17} className="text-[#1e5aa8]" /> {title}
        </p>
      </div>
      <p className="text-[12.5px] text-slate-600 mt-0.5">{hint}</p>

      <label className="block mt-2.5">
        <span className="sr-only">{title}</span>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          data-testid={`${testId}-input`}
          aria-label={title}
          rows={5}
          placeholder={placeholder ?? "VD: FOB NINGBO - Hải Phòng:\nCước biển: 950 usd/ cont 20'\n- Hạ tầng: 250k/cont 20'"}
          className="w-full rounded-xl border-2 border-slate-200 bg-white px-3 py-2.5 text-[14.5px] focus:border-[#1e5aa8] outline-none"
        />
      </label>

      <div className="flex flex-wrap gap-2 mt-2">
        <button
          type="button"
          onClick={analyse}
          data-testid={`${testId}-parse`}
          className="btn-press touch-target inline-flex items-center gap-1.5 rounded-xl bg-[#0f2a4a] text-white font-bold text-[14px] px-4 min-h-[48px]"
        >
          <Wand2 size={16} /> PHÂN TÍCH
        </button>
        {parsed && (
          <button
            type="button"
            onClick={() => onApply(parsed)}
            data-testid={`${testId}-apply`}
            className="btn-press touch-target inline-flex items-center gap-1.5 rounded-xl bg-emerald-600 text-white font-bold text-[14px] px-4 min-h-[48px]"
          >
            {applyLabel}
          </button>
        )}
        {(parsed || text || error) && (
          <button
            type="button"
            onClick={clear}
            data-testid={`${testId}-clear`}
            className="btn-press touch-target inline-flex items-center gap-1.5 rounded-xl border-2 border-slate-200 bg-white text-[#0f2a4a] font-bold text-[14px] px-4 min-h-[48px]"
          >
            <Eraser size={16} /> XÓA KẾT QUẢ
          </button>
        )}
      </div>

      {error && (
        <p role="alert" data-testid={`${testId}-error`}
           className="mt-2 flex items-start gap-1.5 rounded-xl border-2 border-amber-300 bg-amber-50 px-3 py-2 text-[13px] font-semibold text-amber-900">
          <CircleAlert size={15} className="shrink-0 mt-0.5" /> {error}
        </p>
      )}

      {parsed && (
        <div data-testid={`${testId}-preview`} className="mt-3 rounded-xl border-2 border-slate-200 bg-white p-3">
          <p className="text-[12px] font-extrabold uppercase tracking-wide text-slate-500">
            Xem trước — kiểm tra rồi mới áp dụng
          </p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mt-2">
            <PreviewFact label="Incoterm" value={parsed.incoterm} testId={`${testId}-incoterm`} />
            <PreviewFact label="Nơi đi" value={parsed.origin} testId={`${testId}-origin`} />
            <PreviewFact label="Nơi đến" value={parsed.destination} testId={`${testId}-destination`} />
            <PreviewFact
              label="Số khối / cân nặng"
              value={[parsed.cbm != null ? `${parsed.cbm} CBM` : "", parsed.weightKg != null ? `${fmtMoney(parsed.weightKg)} kg` : ""].filter(Boolean).join(" · ")}
              testId={`${testId}-cargo`}
            />
          </div>

          {parsed.lines.length > 0 && (
            <div className="mt-2.5 space-y-1.5" data-testid={`${testId}-lines`}>
              <p className="text-[13px] font-extrabold text-[#0f2a4a]">
                {parsed.lines.length} dòng dịch vụ đọc được
              </p>
              {parsed.lines.map((l, i) => (
                <div
                  key={`${l.name}-${i}`}
                  data-testid={`${testId}-line-${i + 1}`}
                  className="rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-2"
                >
                  <div className="flex flex-wrap items-baseline gap-x-2 gap-y-1">
                    <span className="font-bold text-[13.5px] text-slate-800">{i + 1}. {l.name}</span>
                    <span className="font-extrabold text-[13.5px] text-[#1e5aa8]">
                      {l.sell == null ? "—" : fmtMoney(l.sell)} {l.currency}
                    </span>
                    {l.unit && <span className="text-[12.5px] text-slate-500">/ {l.unit}</span>}
                    {l.condition === "IF_APPLICABLE" && (
                      <span className={cx("rounded-full border px-2 py-0.5 text-[11.5px] font-bold",
                        "border-amber-300 bg-amber-50 text-amber-900")}
                        data-testid={`${testId}-line-${i + 1}-conditional`}>
                        ⚠ Có thể phát sinh (nếu có)
                      </span>
                    )}
                    {l.status === "ESTIMATE_REQUIRES_CONFIRMATION" && (
                      <span className="rounded-full border border-violet-300 bg-violet-50 px-2 py-0.5 text-[11.5px] font-bold text-violet-900"
                        data-testid={`${testId}-line-${i + 1}-estimate`}>
                        ⚠ Ước tính — cần xác nhận
                      </span>
                    )}
                  </div>
                  {l.note && <p className="text-[12.5px] text-slate-600 mt-0.5">Ghi chú: {l.note}</p>}
                </div>
              ))}
            </div>
          )}

          {parsed.assumptions.length > 0 && (
            <div className="mt-2.5" data-testid={`${testId}-assumptions`}>
              <p className="text-[13px] font-extrabold text-[#0f2a4a]">Ghi chú chung (không phải dòng dịch vụ)</p>
              <ul className="mt-1 space-y-0.5">
                {parsed.assumptions.map((a, i) => (
                  <li key={i} className="text-[12.5px] text-slate-600">• {a}</li>
                ))}
              </ul>
            </div>
          )}

          {parsed.unparsed.length > 0 && (
            <div className="mt-2.5" data-testid={`${testId}-unparsed`}>
              <p className="text-[13px] font-extrabold text-amber-800">Chưa hiểu được — vui lòng nhập tay</p>
              <ul className="mt-1 space-y-0.5">
                {parsed.unparsed.map((u, i) => (
                  <li key={i} className="text-[12.5px] text-amber-900">• {u}</li>
                ))}
              </ul>
            </div>
          )}

          <p className="text-[12px] text-slate-500 mt-2.5">
            Chưa có gì được lưu. Hệ thống không tự thêm VAT, giá vốn, tỷ giá hay khách hàng —
            chỉ lấy đúng những gì bản dán ghi.
          </p>
        </div>
      )}
    </section>
  );
}

function PreviewFact({ label, value, testId }: { label: string; value: string; testId: string }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-1.5">
      <p className="text-[11px] font-bold uppercase tracking-wide text-slate-400">{label}</p>
      <p data-testid={testId} className={cx("text-[13.5px] font-semibold", value ? "text-slate-800" : "text-slate-400")}>
        {value || "— chưa đọc được —"}
      </p>
    </div>
  );
}
