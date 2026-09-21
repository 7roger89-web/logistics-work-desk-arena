// ============================================================================
// LOGI_TRANSLATION_LOGISTICS_DEMO_PARITY_01 — /dich-thuat (Dịch thuật).
//
// Demo-look parity with the logistics-demo Translation page (centered language
// direction, LEFT source / RIGHT result workspace, full-width DỊCH NGAY, quick
// business glossary) over the EXISTING canonical REAL translation capability:
//   core/deepl_translation.py (DeepL V2 client) → views/translation.py
//   → ONE bounded "translate_text" event → the ONE Python dispatcher
//   → session readback → the bounded "translation" view-model field → here.
//
// The demo's fake/local dictionary engine is NOT imported: the BẢN DỊCH area
// shows ONLY text the provider actually returned, VERBATIM (line breaks,
// numbers, HS codes, shipment IDs and invoice references are never
// reformatted). Language options come from the backend's own supported sets;
// unconfigured / RBAC-denied / provider-error deployments show honest states
// instead of a fake translation. Donor UI patterns only — no new design
// system, router, store, API or worker.
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
import { PrimaryBtn } from "../components/ui";
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

/**
 * Quick sample chips — Trường Thành logistics sentences. A click fills the
 * SOURCE text only (exactly like typing the phrase); it NEVER dispatches a
 * translation and NEVER fabricates a translated output.
 */
const QUICK_PHRASES_VI: ReadonlyArray<string> = [
  "Vui lòng gửi hóa đơn và phiếu đóng gói trước khi xe lấy hàng.",
  "Xe dự kiến tới nhà máy lúc 8 giờ sáng ngày mai.",
  "Vui lòng gửi kích thước, số kiện và tổng trọng lượng hàng.",
  "Vui lòng gửi thông tin lái xe và biển số xe.",
  "Hàng sẽ làm thủ tục tại cửa khẩu.",
];

/** Equivalent quick set when the source language is Chinese. Source-only too. */
const QUICK_PHRASES_ZH: ReadonlyArray<string> = [
  "请在车辆提货前发送发票和装箱单。",
  "车辆预计明天早上8点到达工厂。",
  "请发送货物的尺寸、件数和总重量。",
  "请发送司机信息和车牌号。",
  "货物将在口岸办理手续。",
];

/**
 * TỪ ĐIỂN NGHIỆP VỤ NHANH — a REFERENCE glossary only. It never generates
 * translations, never overrides DeepL, and never acts as a provider fallback.
 */
const QUICK_GLOSSARY: ReadonlyArray<{ zh: string; pinyin: string; vi: string }> = [
  { zh: "你好", pinyin: "Nǐ hǎo", vi: "Xin chào, rất vui được hợp tác." },
  { zh: "发票", pinyin: "Fāpiào", vi: "Hóa đơn thương mại." },
  { zh: "装箱单", pinyin: "Zhuāngxiāng dān", vi: "Phiếu đóng gói chi tiết." },
  { zh: "提货单", pinyin: "Tíhuò dān", vi: "Phiếu nhận hàng tại kho." },
  { zh: "报关单", pinyin: "Bàoguān dān", vi: "Tờ khai hải quan." },
  { zh: "合同", pinyin: "Hétong", vi: "Hợp đồng vận chuyển." },
  { zh: "付款方式", pinyin: "Fùkuǎn fāngshì", vi: "Phương thức thanh toán." },
  { zh: "预付款", pinyin: "Yùfùkuǎn", vi: "Khoản tạm ứng." },
  { zh: "卡车", pinyin: "Kǎchē", vi: "Xe tải chở hàng." },
  { zh: "司机", pinyin: "Sījī", vi: "Lái xe đường dài." },
  { zh: "车牌号", pinyin: "Chēpái hào", vi: "Biển số xe container." },
  { zh: "验货", pinyin: "Yànhuò", vi: "Kiểm tra hàng trước khi nhận." },
  { zh: "口岸", pinyin: "Kǒu'àn", vi: "Cửa khẩu làm thủ tục." },
  { zh: "交货", pinyin: "Jiāohuò", vi: "Giao hàng tại nhà máy." },
  { zh: "谢谢", pinyin: "Xièxie", vi: "Cảm ơn, hẹn hợp tác lần sau." },
];

/** Contextual source-panel caption, derived from the chosen source language. */
function sourceCaption(sourceLang: string): string {
  switch (sourceLang) {
    case "VI":
      return "Nhập tiếng Việt";
    case "ZH":
      return "Nhập tiếng Trung";
    case "EN":
      return "Nhập tiếng Anh";
    default:
      return "Văn bản gốc";
  }
}

function DirectionSelect({
  value,
  options,
  onChange,
  ariaLabel,
}: {
  value: string;
  options: TranslationLanguage[];
  onChange: (code: string) => void;
  ariaLabel: string;
}) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      aria-label={ariaLabel}
      className="min-w-0 flex-1 sm:flex-none sm:w-[220px] rounded-xl border-2 border-slate-200 bg-white px-3 text-[15px] font-bold text-[#0f2a4a] min-h-[44px] py-2 focus:border-[#1e5aa8] outline-none"
    >
      {options.map((option) => (
        <option key={option.code} value={option.code}>
          {option.label}
        </option>
      ))}
    </select>
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
  const failureMessage =
    result && result.status !== "translated" ? result.error : null;
  const quickPhrases = sourceLang === "ZH" ? QUICK_PHRASES_ZH : QUICK_PHRASES_VI;

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

  const fillSource = (phrase: string) => {
    // Source-only: no dispatch, no fabricated output — exactly like typing.
    setText(phrase);
    setSubmitted(null);
    setCopyState("idle");
  };

  const sourceOptions = capability?.sourceLanguages ?? [];
  const targetOptions = capability?.targetLanguages ?? [];

  return (
    <div className="space-y-4 max-w-[1100px]">
      {/* Page header (demo parity) ---------------------------------------- */}
      <div>
        <h1 className="text-[20px] md:text-[22px] font-extrabold text-[#0f2a4a] leading-tight">
          Dịch Thuật
        </h1>
        <p className="text-[13.5px] text-slate-500 mt-1">
          Công cụ dịch nhanh các cụm từ nghiệp vụ thường dùng khi trao đổi với
          nhà máy và đại lý Trung Quốc.
        </p>
      </div>

      {/* Main workspace card ---------------------------------------------- */}
      <div className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5">
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

        {/* Centered language direction: source ⇄ target ------------------- */}
        <div
          className="flex items-center justify-center gap-2 sm:gap-3"
          data-testid="language-direction"
        >
          <DirectionSelect
            ariaLabel="Ngôn ngữ nguồn"
            value={sourceLang}
            options={sourceOptions}
            onChange={setSourceLang}
          />
          <button
            type="button"
            onClick={swap}
            aria-label="Đổi chiều dịch"
            title="Đổi chiều dịch"
            className="btn-press shrink-0 w-11 h-11 rounded-full border border-slate-200 bg-slate-100 text-[#0f2a4a] grid place-items-center hover:bg-slate-200"
          >
            <ArrowLeftRight size={18} />
          </button>
          <DirectionSelect
            ariaLabel="Ngôn ngữ đích"
            value={targetLang}
            options={targetOptions}
            onChange={setTargetLang}
          />
        </div>

        {/* Two-column workspace: LEFT source / RIGHT result ---------------- */}
        <div
          className="grid grid-cols-1 lg:grid-cols-2 gap-3 md:gap-4 mt-4"
          data-testid="translation-workspace"
        >
          {/* LEFT — what the operator needs translated -------------------- */}
          <div data-testid="source-panel" className="min-w-0">
            <div className="flex items-center justify-between gap-2 mb-1.5">
              <span className="text-[12.5px] font-extrabold uppercase tracking-wide text-slate-500">
                {sourceCaption(sourceLang)}
              </span>
              <button
                type="button"
                onClick={clear}
                aria-label="Xóa nội dung nhập"
                className="btn-press inline-flex items-center gap-1.5 rounded-lg px-2.5 min-h-[44px] text-[13.5px] font-bold text-slate-500 hover:bg-slate-100"
              >
                <Eraser size={15} /> Xóa
              </button>
            </div>
            <textarea
              value={text}
              onChange={(e) => {
                setText(e.target.value);
                setSubmitted(null);
              }}
              placeholder="Nhập văn bản cần dịch…"
              aria-label="Văn bản gốc"
              className="w-full rounded-xl border-2 border-slate-200 bg-white px-3.5 py-3 text-[16px] leading-relaxed min-h-[170px] focus:border-[#1e5aa8] outline-none resize-y"
            />
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

            {/* Quick sample chips — donor-shape pills (logistics-demo
                Translation.tsx): small, truncated, SOURCE text only. */}
            <div
              className="mt-2.5 flex flex-wrap gap-2"
              role="group"
              aria-label="Cụm từ nhanh"
            >
              {quickPhrases.map((phrase) => (
                <button
                  key={phrase}
                  type="button"
                  onClick={() => fillSource(phrase)}
                  title={phrase}
                  aria-label={phrase}
                  data-testid="quick-chip"
                  className="text-[12px] px-2.5 py-1 rounded-full bg-slate-100 text-slate-600 hover:bg-slate-200 min-h-[28px] max-w-[220px] truncate"
                >
                  {phrase.slice(0, 24)}…
                </button>
              ))}
            </div>
          </div>

          {/* RIGHT — the translation (always in place) -------------------- */}
          <div data-testid="result-panel" className="min-w-0">
            <div className="flex items-center mb-1.5 min-h-[44px]">
              <span className="text-[12.5px] font-extrabold uppercase tracking-wide text-slate-500">
                Bản dịch
              </span>
            </div>

            {copyState === "failed" && (
              <p className="mb-2 text-[13px] text-amber-800 font-semibold">
                Trình duyệt không cho phép sao chép tự động — hãy bôi đen bản dịch
                rồi sao chép thủ công.
              </p>
            )}

            {/* Pending: spinner stays INSIDE the result region. */}
            {pending && (
              <div
                data-testid="result-pending"
                className="w-full rounded-xl border-2 border-slate-200 bg-white min-h-[170px] grid place-items-center px-3.5 py-3"
                role="status"
                aria-label="Đang dịch"
              >
                <span className="inline-flex items-center gap-2 text-[15px] font-semibold text-slate-500">
                  <Loader2 size={20} className="animate-spin text-[#1e5aa8]" />
                  Đang dịch…
                </span>
              </div>
            )}

            {/* Translated: ONLY a real provider answer, rendered verbatim. */}
            {!pending && result?.status === "translated" && (
              <div data-testid="result-translated">
                {/* readOnly textarea: keeps the provider's line breaks and lets
                    the text be selected/scrolled on a phone. Nothing is
                    reformatted. */}
                <textarea
                  readOnly
                  value={translated}
                  aria-label="Bản dịch"
                  className="w-full rounded-xl border-2 border-slate-200 bg-slate-50 px-3.5 py-3 text-[16px] leading-relaxed min-h-[170px] resize-y whitespace-pre-wrap"
                />
                {/* LOGI_INTERNAL_UX_SIMPLIFY_01 — donor-position copy
                    action under the result; honest copied/failed states kept. */}
                <button
                  type="button"
                  onClick={copyResult}
                  className="mt-2 flex items-center gap-1.5 text-[13px] font-semibold text-[#1e5aa8] hover:underline"
                >
                  {copyState === "done" ? (
                    <>
                      <Check size={13} className="text-emerald-600" /> Đã sao chép
                    </>
                  ) : (
                    <>
                      <Copy size={13} /> Sao chép
                    </>
                  )}
                </button>
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

            {/* Error / refusal — the provider's own safe message, in place. */}
            {!pending && failureMessage && (
              <div
                data-testid="translation-error"
                className="w-full rounded-xl border border-red-200 bg-red-50 p-4 flex items-start gap-2.5 min-h-[170px]"
              >
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

            {/* Idle — honest placeholder, never a fabricated translation. */}
            {!pending && !result && (
              <div
                data-testid="result-placeholder"
                className="w-full rounded-xl border-2 border-dashed border-slate-300 bg-white min-h-[170px] grid place-items-center px-3.5 py-3 text-[14.5px] text-slate-400"
              >
                — Bản dịch sẽ hiển thị tại đây —
              </div>
            )}
          </div>
        </div>

        {/* ONE large full-width primary action ---------------------------- */}
        <PrimaryBtn
          onClick={submit}
          disabled={!canTranslate}
          className="w-full mt-4"
          testId="translate-action"
        >
          {pending ? (
            <>
              <Loader2 size={18} className="animate-spin" /> ĐANG DỊCH…
            </>
          ) : (
            <>
              <Languages size={18} /> DỊCH NGAY
            </>
          )}
        </PrimaryBtn>

        {/* Privacy boundary — the text really is sent to an external provider. */}
        {capability?.externalProvider && (
          <div className="mt-3 flex items-start gap-2 text-[12.5px] text-slate-500">
            <Info size={14} className="shrink-0 mt-0.5" />
            <p>{capability.privacyNotice}</p>
          </div>
        )}
      </div>

      {/* Quick business glossary — reference only --------------------------
          LOGI_INTERNAL_UX_SIMPLIFY_01 (Control Tower final visual repair) —
          donor structure from logistics-demo@main src/pages/Translation.tsx
          (blob a8b22a3): compact 2-col / sm:3-col cards. Pinyin stays small
          so the compact donor layout survives. */}
      <div className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5">
        <div className="text-[13px] font-bold text-[#0f2a4a] mb-2">
          Từ điển nghiệp vụ nhanh
        </div>
        <div data-testid="glossary" className="mt-2 grid grid-cols-2 sm:grid-cols-3 gap-2">
          {QUICK_GLOSSARY.map((g) => (
            <div
              key={g.zh}
              data-testid="glossary-item"
              className="rounded-lg bg-slate-50 px-2.5 py-2 min-w-0"
            >
              <p className="text-[13.5px] font-bold text-[#0f2a4a] truncate">{g.zh}</p>
              <p className="text-[11.5px] text-slate-400 truncate">{g.pinyin}</p>
              <p className="text-[12.5px] text-slate-600 truncate">{g.vi}</p>
            </div>
          ))}
        </div>
        <p className="text-[12.5px] text-slate-400 mt-2.5">
          Bảng tra cứu nhanh — bản dịch vẫn do {capability?.provider ?? "nhà cung cấp dịch"} trả về.
        </p>
      </div>
    </div>
  );
}
