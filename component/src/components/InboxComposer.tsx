import { useEffect, useRef, useState, useSyncExternalStore, type ClipboardEvent } from "react";
import { ArrowLeft, Paperclip, X } from "lucide-react";
import { dispatchLogiEvent } from "../lib/dispatcher";
import { cx } from "../lib/format";
import { getViewModel, subscribeViewModel } from "../lib/viewmodel";
import { inputCls, PrimaryBtn } from "./ui";

const SOURCES: { id: string; label: string }[] = [
  { id: "", label: "Không ghi nguồn" },
  { id: "zalo", label: "Zalo" },
  { id: "wechat", label: "WeChat" },
  { id: "bank", label: "Ngân hàng" },
  { id: "other", label: "Khác" },
];

const CLIPBOARD_IMAGE_MIMES = new Set(["image/jpeg", "image/png"]);
const FALLBACK_ACCEPT = ".pdf,.jpg,.jpeg,.png,.doc,.docx,.xls,.xlsx,application/pdf,image/jpeg,image/png";
const MAX_FILES = 8;

type ClipboardImageMime = "image/jpeg" | "image/png";

function newRequestId(): string {
  return `INBOX-${Date.now().toString(36).toUpperCase()}-${Math.random().toString(36).slice(2, 8).toUpperCase()}`;
}

function normalizeClipboardImageMime(value: string): ClipboardImageMime | null {
  const mime = String(value || "").toLowerCase();
  return CLIPBOARD_IMAGE_MIMES.has(mime as ClipboardImageMime) ? (mime as ClipboardImageMime) : null;
}

function findClipboardImage(data: DataTransfer | null): { file: File; mime: ClipboardImageMime } | null {
  if (!data) return null;
  for (const item of Array.from(data.items || [])) {
    if (item.kind !== "file") continue;
    const mime = normalizeClipboardImageMime(item.type);
    if (!mime) continue;
    const file = item.getAsFile();
    if (file) return { file, mime };
  }
  for (const file of Array.from(data.files || [])) {
    const mime = normalizeClipboardImageMime(file.type);
    if (mime) return { file, mime };
  }
  return null;
}

function clipboardExtension(mime: ClipboardImageMime): "jpg" | "png" {
  return mime === "image/jpeg" ? "jpg" : "png";
}

function timestampForClipboardName(date = new Date()): string {
  const pad = (value: number) => String(value).padStart(2, "0");
  return `${date.getFullYear()}${pad(date.getMonth() + 1)}${pad(date.getDate())}-${pad(date.getHours())}${pad(date.getMinutes())}${pad(date.getSeconds())}`;
}

function generatedClipboardName(mime: ClipboardImageMime): string {
  return `anh-dan-${timestampForClipboardName()}.${clipboardExtension(mime)}`;
}

function isSensibleClipboardImageName(name: string, mime: ClipboardImageMime): boolean {
  const trimmed = String(name || "").trim();
  if (!trimmed || trimmed.length > 180) return false;
  if (/[\\/\u0000-\u001f\u007f]/.test(trimmed)) return false;
  const lower = trimmed.toLowerCase();
  if (mime === "image/png") return lower.endsWith(".png");
  return lower.endsWith(".jpg") || lower.endsWith(".jpeg");
}

function prepareClipboardFile({ file, mime }: { file: File; mime: ClipboardImageMime }): File {
  const fileName = isSensibleClipboardImageName(file.name, mime) ? file.name.trim() : generatedClipboardName(mime);
  if (file.name === fileName && file.type === mime) return file;
  return new File([file], fileName, { type: mime, lastModified: file.lastModified || Date.now() });
}

function readFileAsBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = () => reject(new Error("read-failed"));
    reader.onload = () => {
      const dataUrl = typeof reader.result === "string" ? reader.result : "";
      const comma = dataUrl.indexOf(",");
      resolve(comma >= 0 ? dataUrl.slice(comma + 1) : dataUrl);
    };
    reader.readAsDataURL(file);
  });
}

export default function InboxComposer({
  onCancel,
  onSaved,
  onPendingChange,
}: {
  onCancel: () => void;
  onSaved: (keepOpen: boolean) => void;
  onPendingChange?: (pending: boolean) => void;
}) {
  const vm = useSyncExternalStore(subscribeViewModel, getViewModel, getViewModel);
  const policy = vm?.attachmentPolicy;
  const maxBytes = policy?.maxUploadBytes ?? 20 * 1024 * 1024;
  const maxLabel = policy?.maxUploadLabel || "20 MB";
  const accept = policy?.accept || FALLBACK_ACCEPT;
  const [rawText, setRawText] = useState("");
  const [source, setSource] = useState("");
  const [title, setTitle] = useState("");
  const [sourceRef, setSourceRef] = useState("");
  const [occurredAt, setOccurredAt] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [pending, setPending] = useState("");
  const [pendingEvent, setPendingEvent] = useState<"inbox_snippet_create" | "inbox_snippet_attach">("inbox_snippet_create");
  const [keepOpen, setKeepOpen] = useState(false);
  const [error, setError] = useState("");
  const [snippetId, setSnippetId] = useState("");
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const lock = useRef(false);

  useEffect(() => {
    onPendingChange?.(Boolean(pending));
  }, [pending, onPendingChange]);

  useEffect(() => {
    if (!pending) return;
    const outcome = (vm?.lastWrites ?? []).find(
      (row) => row.event === pendingEvent && row.requestId === pending
    );
    if (!outcome) return;
    lock.current = false;
    setPending("");
    onPendingChange?.(false);
    if (!outcome.ok) {
      setError(outcome.error || "Không lưu được mẩu tin.");
      return;
    }
    const savedId = String(outcome.id || (outcome.readback as { id?: string } | undefined)?.id || snippetId);
    if (savedId) setSnippetId(savedId);
    const failedRaw = (outcome as unknown as { failedFiles?: { fileName?: string }[] }).failedFiles;
    const failed = Array.isArray(failedRaw) ? failedRaw : [];
    if (Boolean(outcome.partial) || failed.length) {
      const failedNames = new Set(failed.map((row) => String(row.fileName || "")));
      setFiles((current) => current.filter((file) => failedNames.has(file.name)));
      setError(String(outcome.message || outcome.error || "Một số tệp chưa vào kho. Thử lại các tệp lỗi — không tạo mẩu mới."));
      return;
    }
    setRawText("");
    setTitle("");
    setSourceRef("");
    setOccurredAt("");
    setFiles([]);
    setSnippetId("");
    setError("");
    if (fileInputRef.current) fileInputRef.current.value = "";
    onSaved(keepOpen);
  }, [vm?.lastWrites, pending, pendingEvent, keepOpen, onSaved, snippetId]);

  const addFiles = (incoming: File[]) => {
    if (!incoming.length) return;
    const next = [...files];
    for (const file of incoming) {
      if (maxBytes > 0 && file.size > maxBytes) {
        setError(`Tệp vượt giới hạn ${maxLabel}. Chưa gửi lên máy chủ.`);
        continue;
      }
      if (next.length >= MAX_FILES) {
        setError(`Mỗi mẩu tin tối đa ${MAX_FILES} tệp.`);
        break;
      }
      next.push(file);
    }
    setFiles(next);
  };

  const handleClipboardPaste = (event: ClipboardEvent<HTMLDivElement>) => {
    const clipboardImage = findClipboardImage(event.clipboardData);
    if (!clipboardImage) return;
    event.preventDefault();
    event.stopPropagation();
    addFiles([prepareClipboardFile(clipboardImage)]);
  };

  const save = async (continueAfter: boolean, retryFailed = false) => {
    if (lock.current) return;
    const text = rawText.trim();
    if (!text && files.length === 0) {
      setError("Nhập nội dung hoặc đính kèm tệp.");
      return;
    }
    lock.current = true;
    const requestId = newRequestId();
    setError("");
    setKeepOpen(continueAfter);
    const eventName = retryFailed && snippetId ? "inbox_snippet_attach" : "inbox_snippet_create";
    setPendingEvent(eventName);
    setPending(requestId);
    let encoded: { fileName: string; mime: string; size: number; base64: string }[] = [];
    try {
      encoded = await Promise.all(
        files.map(async (file) => ({
          fileName: file.name,
          mime: file.type,
          size: file.size,
          base64: await readFileAsBase64(file),
        }))
      );
    } catch {
      lock.current = false;
      setPending("");
      setError("Không đọc được nội dung tệp đã chọn.");
      return;
    }
    const payload: Record<string, unknown> = {
      requestId,
      rawText: text,
      source,
      title: title.trim(),
      sourceRef: sourceRef.trim(),
      occurredAt: occurredAt.trim(),
      files: encoded,
    };
    if (eventName === "inbox_snippet_attach") payload.snippetId = snippetId;
    const ok = dispatchLogiEvent(eventName, payload);
    if (!ok) {
      lock.current = false;
      setPending("");
      setError("Component chưa kết nối backend.");
    }
  };

  return (
    <div data-testid="inbox-composer" className="space-y-3">
      <button
        type="button"
        onClick={onCancel}
        className="touch-target inline-flex items-center gap-1.5 text-[13.5px] font-semibold text-slate-600 hover:text-[#0f2a4a]"
      >
        <ArrowLeft size={16} /> Về danh sách thêm
      </button>
      <div>
        <p className="font-extrabold text-[18px] text-[#0f2a4a]">Ghi chú nhanh</p>
        <p className="text-[13.5px] text-slate-500 mt-1">
          Dán chữ, ảnh JPEG/PNG hoặc chọn tệp ngay. Chưa cần chọn hợp đồng hay lô hàng.
          Mẩu tin gốc được giữ nguyên — đây chưa phải giao dịch đã thanh toán.
        </p>
      </div>
      <label className="block">
        <span className="block text-[13px] font-bold text-slate-600 mb-1">Nội dung</span>
        <textarea
          data-testid="inbox-composer-text"
          value={rawText}
          onChange={(e) => setRawText(e.target.value)}
          rows={7}
          autoFocus
          placeholder="Dán tin nhắn, số tiền, số hợp đồng… tiếng Việt hoặc tiếng Trung. Có thể để trống nếu chỉ đính kèm tệp."
          className="w-full rounded-xl border-2 border-slate-200 focus:border-[#1e5aa8] bg-white px-3.5 py-3 text-[15px] min-h-[160px] placeholder:text-slate-400"
        />
      </label>
      <div
        tabIndex={0}
        role="group"
        aria-label="Dán ảnh JPEG hoặc PNG từ clipboard vào mẩu tin"
        data-testid="inbox-composer-paste"
        onClick={(event) => event.currentTarget.focus()}
        onPaste={handleClipboardPaste}
        className={cx(
          "rounded-xl border-2 border-dashed border-slate-200 bg-slate-50 px-3 py-2.5 text-[13px] text-slate-600 outline-none",
          "focus:border-[#1e5aa8] focus:bg-white focus:ring-2 focus:ring-[#1e5aa8]/20"
        )}
      >
        <p className="font-bold text-[#0f2a4a]">Dán ảnh JPEG/PNG</p>
        <p className="mt-0.5 break-words">
          Bấm vào khung này rồi nhấn Ctrl+V/Cmd+V. Ảnh được thêm vào danh sách tệp, không tự tải lên.
        </p>
      </div>
      <label className="block">
        <span className="block text-[13px] font-bold text-slate-600 mb-1">
          Chọn tệp PDF / JPG / PNG / DOC / XLS (tối đa {maxLabel} mỗi tệp)
        </span>
        <input
          ref={fileInputRef}
          data-testid="inbox-composer-file"
          type="file"
          multiple
          accept={accept}
          onChange={(event) => {
            addFiles(Array.from(event.target.files || []));
            event.currentTarget.value = "";
          }}
          className={cx(
            "w-full max-w-full rounded-xl border-2 border-slate-200 bg-white px-3 py-2.5 text-[14px] min-h-[44px]",
            "file:mr-3 file:rounded-lg file:border-0 file:bg-[#0f2a4a] file:px-3 file:py-2 file:text-white file:font-bold"
          )}
        />
      </label>
      {files.length > 0 && (
        <ul className="space-y-1.5" data-testid="inbox-composer-files">
          {files.map((file, index) => (
            <li key={`${file.name}-${index}`} className="flex items-center gap-2 rounded-xl border border-slate-200 px-3 py-2 text-[13.5px]">
              <Paperclip size={14} className="text-slate-400 shrink-0" />
              <span className="min-w-0 flex-1 truncate">{file.name}</span>
              <button
                type="button"
                aria-label={`Gỡ ${file.name}`}
                onClick={() => setFiles((current) => current.filter((_, item) => item !== index))}
                className="touch-target w-10 h-10 grid place-items-center rounded-lg hover:bg-slate-100"
              >
                <X size={16} />
              </button>
            </li>
          ))}
        </ul>
      )}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <label className="block">
          <span className="block text-[13px] font-bold text-slate-600 mb-1">Nguồn (không bắt buộc)</span>
          <select
            data-testid="inbox-composer-source"
            value={source}
            onChange={(e) => setSource(e.target.value)}
            className={inputCls()}
          >
            {SOURCES.map((row) => (
              <option key={row.id || "none"} value={row.id}>{row.label}</option>
            ))}
          </select>
        </label>
        <label className="block">
          <span className="block text-[13px] font-bold text-slate-600 mb-1">Ngày trên tin (không bắt buộc)</span>
          <input
            data-testid="inbox-composer-date"
            value={occurredAt}
            onChange={(e) => setOccurredAt(e.target.value)}
            placeholder="YYYY-MM-DD — để trống = chưa biết"
            className={inputCls()}
          />
        </label>
        <label className="block">
          <span className="block text-[13px] font-bold text-slate-600 mb-1">Tiêu đề / tag (không bắt buộc)</span>
          <input
            data-testid="inbox-composer-title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Ví dụ: chuyển USD, nhà máy trả RMB"
            className={inputCls()}
          />
        </label>
        <label className="block">
          <span className="block text-[13px] font-bold text-slate-600 mb-1">Mã tham chiếu nguồn (không bắt buộc)</span>
          <input
            data-testid="inbox-composer-ref"
            value={sourceRef}
            onChange={(e) => setSourceRef(e.target.value)}
            placeholder="Số tin, mã giao dịch giả lập…"
            className={inputCls()}
          />
        </label>
      </div>
      {error && <p className="text-[13.5px] font-medium text-red-700" role="alert">{error}</p>}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 pt-1">
        <PrimaryBtn
          testId="inbox-composer-save"
          disabled={Boolean(pending)}
          onClick={() => void save(false, Boolean(snippetId && files.length))}
        >
          {pending && !keepOpen ? "Đang lưu…" : snippetId && files.length ? "Thử lại tệp lỗi" : "Lưu"}
        </PrimaryBtn>
        <button
          type="button"
          data-testid="inbox-composer-save-next"
          disabled={Boolean(pending)}
          onClick={() => void save(true)}
          className="btn-press touch-target inline-flex items-center justify-center rounded-xl border-2 border-[#0f2a4a] text-[#0f2a4a] font-bold text-[15.5px] px-5 min-h-[48px] disabled:opacity-50"
        >
          {pending && keepOpen ? "Đang lưu…" : "Lưu & ghi tiếp"}
        </button>
      </div>
    </div>
  );
}
