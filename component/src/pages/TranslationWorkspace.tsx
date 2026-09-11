// ============================================================================
// LOGI_TRANSLATION_WORKSPACE_01 — /dich-thuat (Dịch thuật).
//
// PARTIAL_BACKED workspace over the EXISTING canonical translation capability:
//   core/deepl_translation.py (DeepL V2 client) → views/translation.py
//   → ONE bounded "translate_text" event → the ONE Python dispatcher
//   → session readback → the bounded "translation" view-model field → here.
//
// No mock translation is ever rendered: the result area shows ONLY text the
// provider actually returned, VERBATIM (line breaks, numbers, HS codes,
// shipment IDs and invoice references are never reformatted or "tidied").
// Language options come from the backend's own supported sets, and an
// unconfigured deployment shows an honest "chưa được cấu hình" state instead of
// a fake translation. Donor UI patterns only — no new design system, router,
// store, API or worker.
// ============================================================================

import { useMemo, useState, useSyncExternalStore } from "react";
import {
  AlertTriangle,
  ArrowLeftRight,
  Check,
  Copy,
  Eraser,
  Info,
  Languages,
  Loader2,
  ShieldAlert,
} from "lucide-react";
import { GhostBtn, PrimaryBtn, SectionTitle, inputCls } from "../components/ui";
import { dispatchLogiEvent } from "../lib/dispatcher";
import { UNKNOWN, cx } from "../lib/format";
import {
  getViewModel,
  subscribeViewModel,
  type TranslationLanguage,
} from "../lib/viewmodel";

/** UTF-8 byte length — the unit the backend limit is expressed in. */
function byteLength(value: string): number {
  if (typeof TextEncoder !== "undefined") {
    return new TextEncoder().encode(value).length;
  }
  return value.length;
}

/** Local identity of ONE translation intent (text + direction). */
function intentKey(text: string, sourceLang: string, targetLang: string): string {
  return `${sourceLang}\u0000${targetLang}\u0000${text}`;
}

function LanguageSelect({
  label,
  value,
  options,
  onChange,
  disabled,
}: {
  label: string;
  value: string;
  options: TranslationLanguage[];
  onChange: (code: string) => void;
  disabled?: boolean;
}) {
  return (
    <label className="block flex-1 min-w-0">
      <span className="block text-[14px] font-semibold text-slate-700 mb-1.5">
        {label}
      </span>
      <select
        value={value}
        disabled={disabled}
        onChange={(e) => onChange(e.target.value)}
        className={cx(inputCls(), "disabled:opacity-50")}
        aria-label={label}
      >
        {options.map((option) => (
          <option key={option.code} value={option.code}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}

export default function TranslationWorkspace() {
  useSyncExternalStore(subscribeViewModel, getViewModel, getViewModel);
  const vm = getViewModel();
  const slice = vm?.translation ?? null;
  const capability = slice?.capability ?? null;
  const request = slice?.request ?? null;
  const result = slice?.result ?? null;

  const [text, setText] = useState("");
  const [sourceLang, setSourceLang] = useState("AUTO");
  const [targetLang, setTargetLang] = useState("VI");
  const [submitted, setSubmitted] = useState<string | null>(null);
  const [copyState, setCopyState] = useState<"idle" | "done" | "failed">("idle");

  const maxBytes = capability?.maxTextBytes ?? 100_000;
  const bytes = useMemo(() => byteLength(text), [text]);
  const oversize = bytes > maxBytes;
  const configured = capability?.configured ?? false;
  const allowed = capability?.allowed ?? false;
  // One intent in flight: the button stays disabled until the backend readback
  // for THIS intent arrives, so a double click cannot pay the provider twice.
  // The comparison is over the intent itself (the server-side fingerprint is a
  // sha256 the browser deliberately never recomputes).
  const delivered = request
    ? intentKey(request.text, request.sourceLang, request.targetLang)
    : null;
  const pending = submitted !== null && submitted !== delivered;
  const canTranslate =
    configured && allowed && text.trim().length > 0 && !oversize && !pending;
  const translated = result?.status === "translated" ? result.text ?? "" : "";

  const submit = () => {
    if (!canTranslate) return;
    setCopyState("idle");
    setSubmitted(intentKey(text, sourceLang, targetLang));
    dispatchLogiEvent("translate_text", {
      text,
      sourceLang,
      targetLang,
    });
  };

  const swap = () => {
    if (!capability) return;
    const nextSource = capability.swapSource[targetLang];
    const nextTarget = capability.swapTarget[sourceLang];
    if (nextSource) setSourceLang(nextSource);
    if (nextTarget) setTargetLang(nextTarget);
  };

  const clear = () => {
    setText("");
    setSubmitted(null);
    setCopyState("idle");
  };

  const copyResult = async () => {
    if (!translated) return;
    try {
      await navigator.clipboard.writeText(translated);
      setCopyState("done");
    } catch {
      // Honest failure: never pretend the clipboard worked.
      setCopyState("failed");
    }
  };

  const sourceOptions = capability?.sourceLanguages ?? [];
  const targetOptions = capability?.targetLanguages ?? [];
  const failureMessage =
    result && result.status !== "translated" ? result.error : null;

  return (
    <div className="space-y-4 max-w-[1100px]">
      {/* Workspace card --------------------------------------------------- */}
      <div className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5">
        <SectionTitle
          icon={<Languages size={18} />}
          title="Dịch thuật"
          sub={`Dịch văn bản nghiệp vụ logistics qua ${
            capability?.provider ?? "nhà cung cấp dịch"
          } — nhập hoặc dán nội dung, chọn cặp ngôn ngữ rồi bấm Dịch.`}
        />

        {/* Honest configuration state — an unconfigured deployment never
            pretends to translate. */}
        {capability && !configured && (
          <div className="mb-3 rounded-xl border border-amber-300 bg-amber-50 p-3 flex items-start gap-2.5 text-[13.5px] text-amber-900">
            <ShieldAlert size={17} className="shrink-0 mt-0.5" />
            <div>
              <p className="font-extrabold">Translation service chưa được cấu hình</p>
              <p className="mt-0.5">{capability.configNotice}</p>
            </div>
          </div>
        )}

        {capability && configured && !allowed && (
          <div className="mb-3 rounded-xl border border-red-200 bg-red-50 p-3 flex items-start gap-2.5 text-[13.5px] text-red-800">
            <ShieldAlert size={17} className="shrink-0 mt-0.5" />
            <p className="font-semibold">
              Vai trò hiện tại không có quyền dịch thuật (quyền <b>translation</b>).
            </p>
          </div>
        )}

        {/* Privacy boundary — the text really is sent to an external provider. */}
        {capability?.externalProvider && (
          <div className="mb-3 rounded-xl border-2 border-dashed border-slate-300 bg-slate-50 p-3 flex items-start gap-2.5 text-[13px] text-slate-600">
            <Info size={16} className="shrink-0 mt-0.5" />
            <p>{capability.privacyNotice}</p>
          </div>
        )}

        {/* Direction row: source ⇄ target (mobile stacks, no overflow) */}
        <div className="flex flex-col md:flex-row md:items-end gap-2.5">
          <LanguageSelect
            label="Ngôn ngữ nguồn"
            value={sourceLang}
            options={sourceOptions}
            onChange={setSourceLang}
          />
          <div className="md:pb-1">
            <button
              type="button"
              onClick={swap}
              aria-label="Đổi chiều dịch"
              title="Đổi chiều dịch"
              className="btn-press touch-target w-full md:w-auto inline-flex items-center justify-center gap-2 rounded-xl border-2 border-slate-200 text-[#0f2a4a] font-bold text-[14.5px] px-4 min-h-[48px] hover:bg-slate-50"
            >
              <ArrowLeftRight size={17} /> Đổi chiều
            </button>
          </div>
          <LanguageSelect
            label="Ngôn ngữ đích"
            value={targetLang}
            options={targetOptions}
            onChange={setTargetLang}
          />
        </div>

        {/* Source text — 16px so mobile keyboards do not zoom the page. */}
        <label className="block mt-3">
          <span className="block text-[14px] font-semibold text-slate-700 mb-1.5">
            Văn bản nguồn
          </span>
          <textarea
            value={text}
            onChange={(e) => {
              setText(e.target.value);
              setSubmitted(null);
            }}
            placeholder="Dán nội dung cần dịch: email khách, mô tả hàng hóa, chứng từ…"
            aria-label="Văn bản nguồn"
            className="w-full rounded-xl border-2 border-slate-200 bg-white px-3.5 py-3 text-[16px] leading-relaxed min-h-[190px] focus:border-[#1e5aa8] outline-none resize-y"
          />
        </label>
        <p
          className={cx(
            "mt-1 text-[13px]",
            oversize ? "text-red-700 font-semibold" : "text-slate-500"
          )}
        >
          Kích thước: {bytes.toLocaleString("vi-VN")} /{" "}
          {maxBytes.toLocaleString("vi-VN")} bytes
          {oversize && " — nội dung quá lớn cho một yêu cầu, hãy rút gọn."}
        </p>

        <div className="flex flex-col sm:flex-row gap-2.5 mt-3">
          <PrimaryBtn onClick={submit} disabled={!canTranslate} className="flex-1">
            {pending ? (
              <>
                <Loader2 size={17} className="animate-spin" /> Đang dịch…
              </>
            ) : (
              <>
                <Languages size={17} /> Dịch
              </>
            )}
          </PrimaryBtn>
          <GhostBtn onClick={clear} className="sm:w-auto">
            <Eraser size={17} /> Xóa nội dung nhập
          </GhostBtn>
        </div>
      </div>

      {/* Loading state ---------------------------------------------------- */}
      {pending && (
        <div className="rounded-2xl bg-white border border-slate-200 p-8 text-center">
          <Loader2 size={24} className="mx-auto animate-spin text-[#1e5aa8]" />
          <p className="text-[15px] font-semibold text-slate-500 mt-2">
            Đang dịch qua {capability?.provider ?? "nhà cung cấp dịch"}…
          </p>
        </div>
      )}

      {/* Error / refusal state — the provider's own safe message. */}
      {!pending && failureMessage && (
        <div className="rounded-2xl border border-red-200 bg-red-50 p-4 flex items-start gap-2.5">
          <AlertTriangle size={18} className="shrink-0 mt-0.5 text-red-600" />
          <div>
            <p className="text-[15px] font-extrabold text-red-800">
              {result?.status === "config_required"
                ? "Translation service chưa được cấu hình"
                : "Chưa dịch được nội dung này"}
            </p>
            <p className="text-[14px] text-red-700 mt-0.5">{failureMessage}</p>
          </div>
        </div>
      )}

      {/* Result — ONLY a real provider answer, rendered verbatim. */}
      {!pending && result?.status === "translated" && (
        <div className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5">
          <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
            <h3 className="text-[16px] font-extrabold text-[#0f2a4a]">
              Kết quả dịch
            </h3>
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={copyResult}
                className="btn-press touch-target inline-flex items-center gap-2 rounded-xl border-2 border-slate-200 text-[#0f2a4a] font-bold text-[14px] px-4 min-h-[44px] hover:bg-slate-50"
              >
                {copyState === "done" ? (
                  <>
                    <Check size={16} className="text-emerald-600" /> Đã sao chép
                  </>
                ) : (
                  <>
                    <Copy size={16} /> Sao chép
                  </>
                )}
              </button>
            </div>
          </div>

          {copyState === "failed" && (
            <p className="mb-2 text-[13px] text-amber-800 font-semibold">
              Trình duyệt không cho phép sao chép tự động — hãy bôi đen bản dịch
              rồi sao chép thủ công.
            </p>
          )}

          {/* readOnly textarea: keeps the provider's line breaks and lets the
              text be selected/scrolled on a phone. Nothing is reformatted. */}
          <textarea
            readOnly
            value={translated}
            aria-label="Bản dịch"
            className="w-full rounded-xl border-2 border-slate-200 bg-slate-50 px-3.5 py-3 text-[16px] leading-relaxed min-h-[190px] resize-y whitespace-pre-wrap"
          />
          <p className="text-[13px] text-slate-500 mt-2">
            Ngôn ngữ nguồn phát hiện:{" "}
            <b>{result.detectedSourceLanguage ?? UNKNOWN}</b> · Ký tự tính phí:{" "}
            <b>
              {result.billedCharacters === null
                ? UNKNOWN
                : result.billedCharacters.toLocaleString("vi-VN")}
            </b>{" "}
            · <b>{result.apiLabel ?? UNKNOWN}</b>
          </p>
          {request && (
            <p className="text-[12.5px] text-slate-400 mt-1">
              Yêu cầu: {request.sourceLang} → {request.targetLang} · bản dịch giữ
              nguyên xuống dòng, số, mã HS và mã chứng từ như nhà cung cấp trả về.
            </p>
          )}
        </div>
      )}

      {/* Idle state — honest, never a fabricated translation. */}
      {!pending && !result && (
        <div className="rounded-2xl border-2 border-dashed border-slate-300 bg-white p-10 text-center">
          <span className="mx-auto w-14 h-14 rounded-2xl bg-slate-100 text-slate-400 grid place-items-center">
            <Languages size={26} />
          </span>
          <h3 className="text-[16px] font-extrabold text-[#0f2a4a] mt-3">
            Chưa có bản dịch
          </h3>
          <p className="text-[14px] text-slate-500 mt-1">
            Nhập văn bản, chọn cặp ngôn ngữ rồi bấm <b>Dịch</b>. Hệ thống không
            hiển thị kết quả mẫu thay thế.
          </p>
        </div>
      )}
    </div>
  );
}
