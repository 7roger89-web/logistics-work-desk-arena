import { useEffect, useMemo, useRef, useState, useSyncExternalStore } from "react";
import {
  AlertTriangle,
  Check,
  Clipboard,
  Copy,
  FileImage,
  ImagePlus,
  Loader2,
  ShieldAlert,
  Trash2,
} from "lucide-react";
import { PrimaryBtn } from "../components/ui";
import { dispatchLogiEvent } from "../lib/dispatcher";
import { getViewModel, subscribeViewModel } from "../lib/viewmodel";

type SelectedImage = {
  file: File;
  dataBase64: string;
  previewUrl: string;
};

function bytesLabel(value: number): string {
  if (value >= 1024 * 1024) return `${(value / (1024 * 1024)).toFixed(1)} MB`;
  if (value >= 1024) return `${Math.round(value / 1024)} KB`;
  return `${value} B`;
}

function readAsBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = () => reject(new Error("Không đọc được ảnh."));
    reader.onload = () => {
      const value = String(reader.result || "");
      const comma = value.indexOf(",");
      if (comma < 0) reject(new Error("Dữ liệu ảnh không hợp lệ."));
      else resolve(value.slice(comma + 1));
    };
    reader.readAsDataURL(file);
  });
}

export default function OcrWorkspace() {
  useSyncExternalStore(subscribeViewModel, getViewModel, getViewModel);
  const vm = getViewModel();
  const slice = vm?.ocr ?? null;
  const capability = slice?.capability ?? null;
  const request = slice?.request ?? null;
  const result = slice?.result ?? null;

  const fileInput = useRef<HTMLInputElement>(null);
  const [selected, setSelected] = useState<SelectedImage | null>(null);
  const [selectionError, setSelectionError] = useState<string | null>(null);
  const [pendingRequestId, setPendingRequestId] = useState<string | null>(null);
  const [copyState, setCopyState] = useState<"idle" | "done" | "failed">("idle");
  const [dragging, setDragging] = useState(false);

  const configured = capability?.configured ?? false;
  const maxBytes = capability?.maxImageBytes ?? 10 * 1024 * 1024;
  const accepted = useMemo(
    () => new Set(capability?.acceptedMimeTypes ?? ["image/png", "image/jpeg", "image/webp"]),
    [capability?.acceptedMimeTypes]
  );

  const pending =
    pendingRequestId !== null &&
    request?.clientRequestId !== pendingRequestId;

  useEffect(() => {
    return () => {
      if (selected?.previewUrl) URL.revokeObjectURL(selected.previewUrl);
    };
  }, [selected?.previewUrl]);

  useEffect(() => {
    if (pendingRequestId && request?.clientRequestId === pendingRequestId) {
      setPendingRequestId(null);
    }
  }, [request?.clientRequestId, pendingRequestId]);

  useEffect(() => {
    const handlePaste = (event: ClipboardEvent) => {
      const item = Array.from(event.clipboardData?.items ?? []).find((it) =>
        it.type.startsWith("image/")
      );
      if (!item) return;
      event.preventDefault();
      void chooseFile(item.getAsFile());
    };
    window.addEventListener("paste", handlePaste);
    return () => window.removeEventListener("paste", handlePaste);
  });

  const chooseFile = async (file: File | null) => {
    setSelectionError(null);
    setCopyState("idle");
    if (!file) return;
    const mime = String(file.type || "").toLowerCase();
    if (!accepted.has(mime)) {
      setSelectionError("Chỉ nhận ảnh PNG, JPEG hoặc WEBP.");
      return;
    }
    if (file.size <= 0) {
      setSelectionError("Ảnh trống.");
      return;
    }
    if (file.size > maxBytes) {
      setSelectionError(`Ảnh vượt quá ${bytesLabel(maxBytes)}.`);
      return;
    }
    try {
      const dataBase64 = await readAsBase64(file);
      const previewUrl = URL.createObjectURL(file);
      setSelected((old) => {
        if (old?.previewUrl) URL.revokeObjectURL(old.previewUrl);
        return { file, dataBase64, previewUrl };
      });
    } catch (error) {
      setSelectionError(error instanceof Error ? error.message : "Không đọc được ảnh.");
    }
  };

  const clear = () => {
    setSelected((old) => {
      if (old?.previewUrl) URL.revokeObjectURL(old.previewUrl);
      return null;
    });
    setSelectionError(null);
    setPendingRequestId(null);
    setCopyState("idle");
    if (fileInput.current) fileInput.current.value = "";
  };

  const submit = () => {
    if (!selected || !configured || pending) return;
    const requestId =
      typeof crypto !== "undefined" && "randomUUID" in crypto
        ? crypto.randomUUID()
        : `${Date.now()}-${Math.random().toString(16).slice(2)}`;
    setPendingRequestId(requestId);
    setCopyState("idle");
    dispatchLogiEvent("ocr_image", {
      requestId,
      filename: selected.file.name,
      mimeType: selected.file.type,
      dataBase64: selected.dataBase64,
    });
  };

  const copyMarkdown = async () => {
    const value = result?.status === "extracted" ? result.text ?? "" : "";
    if (!value) return;
    try {
      await navigator.clipboard.writeText(value);
      setCopyState("done");
    } catch {
      setCopyState("failed");
    }
  };

  const extracted = result?.status === "extracted" ? result.text ?? "" : "";
  const providerError = result && result.status !== "extracted" ? result.error : null;

  return (
    <div className="space-y-4 max-w-[1200px]" data-testid="ocr-workspace">
      <div>
        <h1 className="text-[20px] md:text-[22px] font-extrabold text-[#0f2a4a] leading-tight">
          OCR Ảnh → Markdown
        </h1>
        <p className="text-[13.5px] text-slate-500 mt-1">
          Dán, kéo thả hoặc chọn một ảnh. Gemini chỉ trích xuất chữ nhìn thấy và trả kết quả để copy.
        </p>
      </div>

      {capability && !configured && (
        <div className="rounded-xl border border-amber-300 bg-amber-50 p-3 flex items-start gap-2.5 text-[13.5px] text-amber-900">
          <ShieldAlert size={17} className="shrink-0 mt-0.5" />
          <div>
            <p className="font-extrabold">Gemini OCR chưa được cấu hình</p>
            <p className="mt-0.5">{capability.configNotice}</p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4" data-testid="ocr-panels">
        <div className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5 min-w-0">
          <div className="flex items-center justify-between gap-2 mb-3">
            <div>
              <p className="text-[12.5px] font-extrabold uppercase tracking-wide text-slate-500">Ảnh gốc</p>
              <p className="text-[13px] text-slate-400">Ctrl+V cũng được — không cần lưu file trước.</p>
            </div>
            {selected && (
              <button
                type="button"
                onClick={clear}
                className="min-h-[44px] inline-flex items-center gap-1.5 rounded-lg px-3 text-[13.5px] font-bold text-slate-500 hover:bg-slate-100"
              >
                <Trash2 size={15} /> Xóa
              </button>
            )}
          </div>

          <input
            ref={fileInput}
            type="file"
            className="hidden"
            accept="image/png,image/jpeg,image/webp"
            onChange={(e) => void chooseFile(e.target.files?.[0] ?? null)}
            aria-label="Chọn ảnh OCR"
          />

          {!selected ? (
            <button
              type="button"
              onClick={() => fileInput.current?.click()}
              onDragEnter={(e) => { e.preventDefault(); setDragging(true); }}
              onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
              onDragLeave={() => setDragging(false)}
              onDrop={(e) => {
                e.preventDefault();
                setDragging(false);
                void chooseFile(e.dataTransfer.files?.[0] ?? null);
              }}
              data-testid="ocr-drop-zone"
              className={`w-full min-h-[300px] rounded-2xl border-2 border-dashed grid place-items-center px-6 py-8 text-center transition-colors ${
                dragging ? "border-[#1e5aa8] bg-blue-50" : "border-slate-300 bg-slate-50 hover:bg-slate-100"
              }`}
            >
              <span>
                <ImagePlus size={42} className="mx-auto text-[#1e5aa8]" />
                <span className="block mt-3 font-extrabold text-[16px] text-[#0f2a4a]">
                  Dán ảnh · Kéo thả · Chọn ảnh
                </span>
                <span className="block mt-1 text-[13.5px] text-slate-500">
                  PNG / JPEG / WEBP · tối đa {bytesLabel(maxBytes)}
                </span>
              </span>
            </button>
          ) : (
            <div className="space-y-2">
              <div className="rounded-2xl border border-slate-200 bg-slate-50 min-h-[300px] grid place-items-center overflow-hidden">
                <img
                  src={selected.previewUrl}
                  alt="Ảnh sẽ gửi tới Gemini OCR"
                  className="max-w-full max-h-[520px] object-contain"
                  data-testid="ocr-preview"
                />
              </div>
              <div className="flex items-center gap-2 text-[13px] text-slate-500 min-w-0">
                <FileImage size={15} className="shrink-0" />
                <span className="truncate">{selected.file.name}</span>
                <span className="shrink-0">· {bytesLabel(selected.file.size)}</span>
              </div>
            </div>
          )}

          {selectionError && (
            <div className="mt-3 rounded-xl border border-red-200 bg-red-50 p-3 flex items-start gap-2 text-[13.5px] text-red-800">
              <AlertTriangle size={16} className="shrink-0 mt-0.5" />
              <span>{selectionError}</span>
            </div>
          )}

          <PrimaryBtn
            onClick={submit}
            disabled={!selected || !configured || pending}
            className="w-full mt-4"
            testId="ocr-action"
          >
            {pending ? (
              <><Loader2 size={18} className="animate-spin" /> ĐANG TRÍCH XUẤT…</>
            ) : (
              <><Clipboard size={18} /> TRÍCH XUẤT NGUYÊN VĂN</>
            )}
          </PrimaryBtn>
        </div>

        <div className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5 min-w-0" data-testid="ocr-result-panel">
          <div className="flex items-center justify-between gap-2 mb-3">
            <div>
              <p className="text-[12.5px] font-extrabold uppercase tracking-wide text-slate-500">Markdown</p>
              <p className="text-[13px] text-slate-400">Kết quả Gemini trả về — không tự sửa chính tả, số tiền hay mã hàng.</p>
            </div>
            <button
              type="button"
              onClick={copyMarkdown}
              disabled={!extracted}
              className="min-h-[44px] inline-flex items-center gap-1.5 rounded-lg border border-slate-200 px-3 text-[13.5px] font-bold text-[#0f2a4a] hover:bg-slate-50 disabled:opacity-40"
              data-testid="ocr-copy"
            >
              {copyState === "done" ? <Check size={15} /> : <Copy size={15} />}
              {copyState === "done" ? "Đã copy" : "Copy Markdown"}
            </button>
          </div>

          {pending && (
            <div className="min-h-[360px] rounded-xl border-2 border-dashed border-blue-200 bg-blue-50 grid place-items-center text-blue-800" data-testid="ocr-pending">
              <span className="inline-flex items-center gap-2 font-semibold"><Loader2 size={18} className="animate-spin" /> Đang đọc ảnh bằng Gemini…</span>
            </div>
          )}

          {!pending && extracted && (
            <textarea
              readOnly
              aria-label="Kết quả OCR Markdown"
              value={extracted}
              className="w-full min-h-[360px] rounded-xl border-2 border-slate-200 bg-slate-50 px-3.5 py-3 text-[16px] leading-relaxed font-mono resize-y outline-none"
            />
          )}

          {!pending && providerError && (
            <div className="min-h-[360px] rounded-xl border border-red-200 bg-red-50 p-4 flex items-start gap-2.5 text-red-800" data-testid="ocr-error">
              <AlertTriangle size={18} className="shrink-0 mt-0.5" />
              <div>
                <p className="font-extrabold">Chưa trích xuất được ảnh này</p>
                <p className="text-[14px] mt-1">{providerError}</p>
              </div>
            </div>
          )}

          {!pending && !extracted && !providerError && (
            <div className="min-h-[360px] rounded-xl border-2 border-dashed border-slate-300 bg-slate-50 grid place-items-center px-6 text-center text-[14.5px] text-slate-400" data-testid="ocr-placeholder">
              — Markdown sẽ hiện ở đây —
            </div>
          )}

          {copyState === "failed" && (
            <p className="mt-2 text-[13px] text-amber-700 font-semibold">
              Trình duyệt chặn clipboard — chọn nội dung và copy thủ công.
            </p>
          )}
        </div>
      </div>

      {capability?.externalProvider && (
        <div className="flex items-start gap-2 text-[12.5px] text-slate-500">
          <ShieldAlert size={14} className="shrink-0 mt-0.5" />
          <p>{capability.privacyNotice}</p>
        </div>
      )}
    </div>
  );
}
