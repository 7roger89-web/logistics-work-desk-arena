// ============================================================================
// LOGI_SHIPMENT_DOCUMENTS_GRIDFS_RUNTIME_01 — "TỆP ĐÍNH KÈM" for the shipment
// "Chứng từ" tab.
//
// The whole flow is the ONE existing write contract:
//
//   pick file → ONE typed `shipment_attachment_upload` event (bounded base64,
//   the same transport the GetFly preview already uses) → Python dispatcher
//   (RBAC → size/MIME validation → decode → SHA-256 → dedupe → image
//   optimization → selected server storage → Mongo metadata) → fresh shipment
//   readback → this list.
//
// Nothing here is authoritative: the list is rendered from the backend
// projection, the upload button shows a pending state until the backend's own
// outcome arrives in `lastWrites`, and a refusal (duplicate, oversize, RBAC,
// storage unavailable) is displayed verbatim instead of a fake success.
//
// The browser NEVER receives a storage file id, GridFS/Mongo id, credential or
// public link: opening a file is ONE `attachment_download` event that reads the
// bytes server-side, and only the attachment just requested carries them.
// ============================================================================

import { useEffect, useMemo, useRef, useState, useSyncExternalStore, type ClipboardEvent } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  CloudUpload,
  Download,
  FileCheck2,
  FileSearch,
  Info,
  LoaderCircle,
  Paperclip,
} from "lucide-react";
import { SectionTitle, ToneBadge, inputCls } from "./ui";
import { useStore } from "../lib/store";
import { downloadBinaryFile, cx } from "../lib/format";
import {
  getViewModel,
  subscribeViewModel,
  type AttachmentPolicy,
  type DocumentReviewDocument,
  type DocumentReviewFact,
  type ShipmentAttachment,
  type ShipmentDocumentReview,
} from "../lib/viewmodel";

/** The read-only review's own ceiling, mirrored for the local usability check
 *  only — the server enforces the identical bound and refuses before reading. */
const MAX_REVIEW_FILES = 6;

const ALWAYS_REVIEW_NOTE = "Kết quả chỉ để kiểm tra — chưa ghi vào hồ sơ lô hàng.";

const FACT_SECTIONS: { key: string; title: string; statuses: DocumentReviewFact["status"][] }[] = [
  { key: "can-xem", title: "CẦN XEM", statuses: ["CONFLICT", "UNKNOWN", "MISSING"] },
  { key: "tham-khao", title: "THAM KHẢO", statuses: ["SINGLE_SOURCE"] },
  { key: "da-khop", title: "ĐÃ KHỚP", statuses: ["SAME"] },
];

const STATUS_TONE: Record<DocumentReviewFact["status"], string> = {
  CONFLICT: "bg-red-50 border-red-200 text-red-800",
  UNKNOWN: "bg-amber-50 border-amber-200 text-amber-900",
  MISSING: "bg-orange-50 border-orange-200 text-orange-900",
  SINGLE_SOURCE: "bg-slate-50 border-slate-200 text-slate-700",
  SAME: "bg-emerald-50 border-emerald-200 text-emerald-800",
};

const DOC_STATE_TONE: Record<string, string> = {
  READABLE: "text-emerald-700",
  NEEDS_OCR_NOT_RUN: "text-amber-800",
  UNSUPPORTED_FORMAT: "text-slate-500",
  TOO_LARGE_FOR_REVIEW: "text-amber-800",
  READ_FAILED: "text-red-700",
};

function intentId(prefix: string): string {
  return `${prefix}-${Date.now().toString(36).toUpperCase()}-${Math.random().toString(36).slice(2, 8).toUpperCase()}`;
}

const FALLBACK_POLICY: AttachmentPolicy = {
  allowUpload: false,
  categories: [],
  allowedExtensions: [],
  accept: "",
  maxUploadBytes: 0,
  maxUploadLabel: "",
  storageBackend: "gridfs",
  storageConfigured: false,
  storageLabel: "Kho chứng từ",
};

type ClipboardImageMime = "image/jpeg" | "image/png";

type ClipboardImage = {
  file: File;
  mime: ClipboardImageMime;
};

const CLIPBOARD_IMAGE_MIMES = new Set<ClipboardImageMime>(["image/jpeg", "image/png"]);

function normalizeClipboardImageMime(value: string): ClipboardImageMime | null {
  const mime = String(value || "").toLowerCase();
  return CLIPBOARD_IMAGE_MIMES.has(mime as ClipboardImageMime) ? (mime as ClipboardImageMime) : null;
}

function findClipboardImage(data: DataTransfer): ClipboardImage | null {
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

function prepareClipboardFile({ file, mime }: ClipboardImage): File {
  const fileName = isSensibleClipboardImageName(file.name, mime) ? file.name.trim() : generatedClipboardName(mime);
  if (file.name === fileName && file.type === mime) return file;
  return new File([file], fileName, { type: mime, lastModified: file.lastModified || Date.now() });
}

export default function ShipmentAttachments({
  shipmentId,
  attachments,
  policy,
}: {
  shipmentId: string;
  attachments: ShipmentAttachment[];
  policy?: AttachmentPolicy;
}) {
  const { dispatch, toast } = useStore();
  const vm = useSyncExternalStore(subscribeViewModel, getViewModel, getViewModel);
  const lastWrites = vm?.lastWrites ?? [];
  const effective = policy ?? FALLBACK_POLICY;
  const storageLabel = effective.storageLabel || (effective.driveConfigured ? "Shared Drive" : "Kho chứng từ");
  const storageConfigured = effective.storageConfigured ?? effective.driveConfigured ?? false;

  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [category, setCategory] = useState(effective.categories[0]?.id ?? "other");
  const [file, setFile] = useState<File | null>(null);
  const [pendingUpload, setPendingUpload] = useState("");
  const [pendingDownload, setPendingDownload] = useState<{ requestId: string; attachmentId: string } | null>(null);
  const [localError, setLocalError] = useState("");
  const [outcomeText, setOutcomeText] = useState("");
  const [outcomeOk, setOutcomeOk] = useState(false);
  const handledDownloadSeq = useRef<Record<string, number>>({});

  // ---------------------------------------------------------------------------
  // LOGI_TRADE_DOCUMENT_SHIPMENT_REVIEW_RUN3_01 — read-only document review.
  //
  // Local selection only. The review itself runs server-side over the EXISTING
  // attachments: the browser sends { shipmentId, attachmentIds, requestId } and
  // never a byte, a base64 body or a storage id. The result is ONE ephemeral
  // session projection that is never written into the shipment record.
  // ---------------------------------------------------------------------------
  const serverReview = vm?.shipmentDocumentReview ?? null;
  const [selected, setSelected] = useState<string[]>([]);
  const [pendingReview, setPendingReview] = useState("");
  const [reviewError, setReviewError] = useState("");

  // The server's session slot is the authority for WHAT to show; it is guarded
  // by shipment id so a review belonging to another lot can never render here.
  const review: ShipmentDocumentReview | null =
    serverReview && serverReview.shipmentId === shipmentId ? serverReview : null;

  // Switching lots drops the stale local selection. The displayed result needs
  // no clearing: it is re-derived from the server slot, which carries its own
  // shipment id.
  useEffect(() => {
    setSelected([]);
    setPendingReview("");
    setReviewError("");
  }, [shipmentId]);

  const reviewableRows = useMemo(
    () => (Array.isArray(attachments) ? attachments : []).filter((item) => item.reviewSelectable === true),
    [attachments]
  );

  // The pending review settles ONLY on the outcome carrying the requestId this
  // form sent: a stale result from an earlier request cannot close it, and a
  // double click cannot start a second request while one is in flight. This is
  // deliberately separate from what is displayed — the displayed review is the
  // server's session truth, not something the browser has to remember.
  useEffect(() => {
    if (!pendingReview) return;
    const outcome = lastWrites.find(
      (row) => row.event === "shipment_document_review" && row.requestId === pendingReview
    );
    if (!outcome) return;
    setPendingReview("");
    if (!outcome.ok) {
      setReviewError(String(outcome.error || "Chưa kiểm tra được chứng từ."));
    } else {
      setReviewError("");
    }
  }, [lastWrites, pendingReview]);

  const toggleReviewSelection = (attachment: ShipmentAttachment) => {
    setReviewError("");
    setSelected((current) => {
      if (current.includes(attachment.id)) return current.filter((id) => id !== attachment.id);
      if (current.length >= MAX_REVIEW_FILES) return current;
      return [...current, attachment.id];
    });
  };

  const startDocumentReview = () => {
    setReviewError("");
    if (pendingReview) return;
    if (!selected.length) {
      setReviewError("Chưa chọn tệp nào để kiểm tra.");
      return;
    }
    if (selected.length > MAX_REVIEW_FILES) {
      // Usability check only — the server refuses the identical ceiling before
      // it reads a single byte.
      setReviewError(`Chỉ kiểm tra tối đa ${MAX_REVIEW_FILES} tệp một lần.`);
      return;
    }
    const requestId = intentId("ATTREV");
    setPendingReview(requestId);
    const sent = dispatch("shipment_document_review", {
      shipmentId,
      attachmentIds: selected,
      requestId,
    });
    if (!sent) {
      setPendingReview("");
      setReviewError("Không gửi được yêu cầu kiểm tra chứng từ tới backend.");
    }
  };


  // The backend's authoritative answer arrives in the NEXT view-model, matched
  // by the requestId this form sent — never assumed from the transport.
  useEffect(() => {
    if (!pendingUpload) return;
    const outcome = lastWrites.find(
      (row) => row.event === "shipment_attachment_upload" && row.requestId === pendingUpload
    );
    if (!outcome) return;
    setPendingUpload("");
    setOutcomeOk(Boolean(outcome.ok));
    // The backend's own wording wins: a SAME-SHIPMENT duplicate is ok=true with
    // its explicit message ("không tải lên bản sao"), and that is what the
    // operator must read — never a generic "saved" claim.
    const message = String(outcome.message || outcome.error || "");
    setOutcomeText(message || (outcome.ok ? "Đã lưu tệp đính kèm vào lô." : "Tải tệp thất bại."));
    if (outcome.ok) {
      setFile(null);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }, [lastWrites, pendingUpload]);

  useEffect(() => {
    if (!pendingDownload) return;
    const outcome = lastWrites.find(
      (row) => row.event === "attachment_download" && row.requestId === pendingDownload.requestId
    );
    if (!outcome) return;
    setPendingDownload(null);
    if (!outcome.ok) {
      setOutcomeOk(false);
      setOutcomeText(String(outcome.error || `Không đọc được tệp từ ${storageLabel}.`));
    }
  }, [lastWrites, pendingDownload]);

  // Server-authoritative download: the bytes come back on the attachment the
  // backend just read, tagged with a new `downloadSeq`. Saving the file here is
  // the last step of a request the server already authorised.
  useEffect(() => {
    for (const item of attachments) {
      if (!item.downloadAvailable || !item.downloadBase64) continue;
      const seq = item.downloadSeq ?? 0;
      if (handledDownloadSeq.current[item.id] === seq) continue;
      handledDownloadSeq.current[item.id] = seq;
      downloadBinaryFile(item.name, item.downloadBase64, item.mime || "application/octet-stream");
      toast("Đã tải " + item.name, `Bytes đọc từ ${storageLabel.toLowerCase()} qua máy chủ.`, "green");
    }
  }, [attachments, toast]);

  const accept = effective.accept || undefined;

  const handleClipboardPaste = (event: ClipboardEvent<HTMLDivElement>) => {
    const clipboardImage = findClipboardImage(event.clipboardData);
    if (!clipboardImage) return;

    event.preventDefault();
    event.stopPropagation();
    setOutcomeText("");

    const pastedFile = prepareClipboardFile(clipboardImage);
    if (effective.maxUploadBytes > 0 && pastedFile.size > effective.maxUploadBytes) {
      setFile(null);
      if (fileInputRef.current) fileInputRef.current.value = "";
      setLocalError(`Tệp vượt giới hạn ${effective.maxUploadLabel}. Chưa gửi lên máy chủ.`);
      return;
    }

    setFile(pastedFile);
    if (fileInputRef.current) fileInputRef.current.value = "";
    setLocalError("");
  };

  const startUpload = () => {
    setLocalError("");
    setOutcomeText("");
    if (!file) {
      setLocalError("Chưa chọn tệp.");
      return;
    }
    if (effective.maxUploadBytes > 0 && file.size > effective.maxUploadBytes) {
      // Usability check only — the server enforces the identical ceiling and
      // refuses before any Drive call.
      setLocalError(`Tệp vượt giới hạn ${effective.maxUploadLabel}. Chưa gửi lên máy chủ.`);
      return;
    }
    const requestId = intentId("ATT");
    setPendingUpload(requestId);
    const reader = new FileReader();
    reader.onerror = () => {
      setPendingUpload("");
      setLocalError("Không đọc được nội dung tệp đã chọn.");
    };
    reader.onload = () => {
      const dataUrl = typeof reader.result === "string" ? reader.result : "";
      const comma = dataUrl.indexOf(",");
      const contentBase64 = comma >= 0 ? dataUrl.slice(comma + 1) : dataUrl;
      if (!contentBase64) {
        setPendingUpload("");
        setLocalError("Tệp không có dữ liệu.");
        return;
      }
      const sent = dispatch("shipment_attachment_upload", {
        shipmentId,
        category,
        fileName: file.name,
        mime: file.type,
        size: file.size,
        base64: contentBase64,
        requestId,
      });
      if (!sent) {
        setPendingUpload("");
        setLocalError("Không gửi được tệp tới backend.");
      }
    };
    reader.readAsDataURL(file);
  };

  const startDownload = (attachment: ShipmentAttachment) => {
    setLocalError("");
    setOutcomeText("");
    const requestId = intentId("ATTDOWN");
    setPendingDownload({ requestId, attachmentId: attachment.id });
    const sent = dispatch("attachment_download", {
      shipmentId,
      attachmentId: attachment.id,
      requestId,
    });
    if (!sent) {
      setPendingDownload(null);
      setLocalError("Không gửi được yêu cầu mở tệp tới backend.");
    }
  };

  const rows = Array.isArray(attachments) ? attachments : [];

  return (
    <section className="mt-4 rounded-2xl bg-white border border-slate-200 p-4 md:p-5" data-testid="shipment-attachments">
      <SectionTitle
        icon={<Paperclip size={19} className="text-[#1e5aa8]" />}
        title="Tệp đính kèm lô hàng"
        sub={`Tệp thật của lô: nội dung tệp được lưu trong ${storageLabel}; thông tin mô tả được lưu cùng hồ sơ lô.`}
        right={
          <ToneBadge tone={rows.length > 0 ? "green" : "gray"} size="sm">
            {rows.length} tệp
          </ToneBadge>
        }
      />

      {effective.allowUpload ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-1">
          <label className="block min-w-0">
            <span className="block text-[13px] font-bold text-slate-600 mb-1">Loại chứng từ</span>
            <select
              id="fld-attach-category"
              data-testid="attachment-category"
              value={category}
              onChange={(event) => setCategory(event.target.value)}
              className={inputCls()}
            >
              {effective.categories.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.label}
                </option>
              ))}
            </select>
          </label>
          <label className="block min-w-0">
            <span className="block text-[13px] font-bold text-slate-600 mb-1">
              Chọn file (tối đa {effective.maxUploadLabel || "20 MB"})
            </span>
            <input
              ref={fileInputRef}
              id="fld-attach-file"
              data-testid="attachment-file"
              type="file"
              accept={accept}
              onChange={(event) => {
                setFile(event.target.files?.[0] ?? null);
                setLocalError("");
                setOutcomeText("");
              }}
              className={cx(
                "w-full max-w-full rounded-xl border-2 border-slate-200 bg-white px-3 py-2.5 text-[14px] min-h-[44px]",
                "file:mr-3 file:rounded-lg file:border-0 file:bg-[#0f2a4a] file:px-3 file:py-2 file:text-white file:font-bold"
              )}
            />
          </label>
          <div
            tabIndex={0}
            role="group"
            aria-label="Dán ảnh JPEG hoặc PNG từ clipboard vào tệp đính kèm"
            data-testid="attachment-paste-zone"
            onClick={(event) => event.currentTarget.focus()}
            onPaste={handleClipboardPaste}
            className={cx(
              "sm:col-span-2 min-w-0 rounded-xl border-2 border-dashed border-slate-200 bg-slate-50 px-3 py-2.5 text-[13px] text-slate-600 outline-none",
              "focus:border-[#1e5aa8] focus:bg-white focus:ring-2 focus:ring-[#1e5aa8]/20"
            )}
          >
            <p className="font-bold text-[#0f2a4a]">Dán ảnh vào tệp đính kèm</p>
            <p className="mt-0.5 break-words">
              Bấm vào khung này rồi nhấn Ctrl+V/Cmd+V với ảnh JPEG/PNG. Hệ thống chỉ chọn tệp, không tự tải lên.
            </p>
          </div>
        </div>
      ) : (
        <p className="text-[13.5px] text-amber-800 bg-amber-50 border border-amber-200 rounded-xl px-3 py-2.5" data-testid="attachment-readonly">
          Vai trò hiện tại chỉ được xem và tải tệp đính kèm — không được tải lên. Cần quyền sales_write.
        </p>
      )}

      {effective.allowUpload && (
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <button
            type="button"
            data-testid="attachment-upload"
            disabled={!file || Boolean(pendingUpload)}
            onClick={startUpload}
            className={cx(
              "btn-press touch-target inline-flex items-center gap-2 rounded-xl px-5 min-h-[48px] font-extrabold",
              !file || pendingUpload ? "bg-slate-300 text-slate-600" : "bg-[#0f2a4a] text-white"
            )}
          >
            {pendingUpload ? <LoaderCircle size={17} className="animate-spin" /> : <CloudUpload size={17} />}
            {pendingUpload ? `ĐANG LƯU VÀO ${storageLabel.toUpperCase()}…` : `LƯU VÀO ${storageLabel.toUpperCase()}`}
          </button>
          {file && (
            <span data-testid="attachment-selected-file" className="text-[13px] text-slate-600 min-w-0 break-words">
              Đã chọn: {file.name}
            </span>
          )}
          {!storageConfigured && (
            <span className="text-[13px] text-amber-800" data-testid="attachment-storage-state">
              {storageLabel} chưa sẵn sàng trên máy chủ — hệ thống sẽ từ chối trung thực.
            </span>
          )}
        </div>
      )}

      {localError && (
        <p className="mt-3 rounded-xl bg-red-50 border border-red-200 px-3 py-2 text-[13.5px] font-semibold text-red-700" data-testid="attachment-local-error">
          {localError}
        </p>
      )}
      {outcomeText && (
        <p
          data-testid="attachment-outcome"
          className={cx(
            "mt-3 rounded-xl border px-3 py-2 text-[13.5px] font-semibold",
            outcomeOk ? "bg-emerald-50 border-emerald-200 text-emerald-800" : "bg-amber-50 border-amber-200 text-amber-900"
          )}
        >
          {outcomeText}
        </p>
      )}

      {rows.length === 0 ? (
        <p className="mt-3 text-slate-500 text-[14px]" data-testid="attachment-empty">
          Lô chưa có tệp đính kèm nào.
        </p>
      ) : (
        <ul className="mt-3 space-y-2" data-testid="attachment-list">
          {rows.map((item) => (
            <li
              key={item.id}
              data-testid="attachment-row"
              data-attachment-id={item.id}
              data-review-selectable={item.reviewSelectable === true ? "true" : "false"}
              className="flex flex-wrap items-center gap-x-3 gap-y-2 rounded-xl border border-slate-200 p-3 min-w-0"
            >
              {/* LOGI_TRADE_DOCUMENT_SHIPMENT_REVIEW_RUN3_01 — one large,
                  finger-sized affordance for the files this run can read. A
                  non-selectable file stays visible with its honest reason and
                  is never implied to be damaged. */}
              {item.reviewSelectable === true ? (
                <label
                  className="inline-flex items-center gap-2 shrink-0 cursor-pointer touch-target min-h-[44px] px-1"
                  data-testid="attachment-review-toggle"
                >
                  <input
                    type="checkbox"
                    className="h-6 w-6 shrink-0 accent-[#0f2a4a]"
                    aria-label={`Chọn ${item.name} để kiểm tra chứng từ`}
                    checked={selected.includes(item.id)}
                    disabled={Boolean(pendingReview)}
                    onChange={() => toggleReviewSelection(item)}
                  />
                </label>
              ) : (
                <span
                  className="w-6 h-6 rounded-md border-2 border-dashed border-slate-300 grid place-items-center shrink-0"
                  aria-hidden="true"
                >
                  <Info size={13} className="text-slate-400" />
                </span>
              )}
              <span className="w-8 h-8 rounded-lg grid place-items-center bg-slate-100 text-[#0f2a4a] shrink-0">
                <FileCheck2 size={17} />
              </span>
              <div className="min-w-0 flex-1">
                <p className="font-bold text-[14.5px] text-[#0f2a4a] break-words">{item.name}</p>
                <p className="text-[12.5px] text-slate-500 break-words">
                  {item.categoryLabel} · {item.sizeLabel} · {item.uploadedAt || "—"}
                  {item.uploadedBy ? ` · ${item.uploadedBy}` : ""}
                </p>
                <p className="text-[12.5px] font-semibold text-slate-500">
                  {item.compressionLabel}
                  {item.compressionLabel === "Ảnh đã tối ưu" && item.compressionNote ? ` — ${item.compressionNote}` : ""}
                </p>
                {item.reviewSelectable !== true && (
                  <p
                    className="text-[12.5px] font-semibold text-slate-500 break-words"
                    data-testid="attachment-review-note"
                  >
                    {item.reviewNote || "Không hỗ trợ ở bước này"}
                  </p>
                )}
              </div>
              <button
                type="button"
                data-testid="attachment-download"
                disabled={Boolean(pendingDownload)}
                onClick={() => startDownload(item)}
                className="btn-press touch-target inline-flex items-center gap-1.5 rounded-xl border-2 border-[#0f2a4a] text-[#0f2a4a] font-bold px-4 min-h-[44px] shrink-0"
              >
                {pendingDownload?.attachmentId === item.id ? (
                  <LoaderCircle size={15} className="animate-spin" />
                ) : (
                  <Download size={15} />
                )}
                TẢI
              </button>
            </li>
          ))}
        </ul>
      )}

      <DocumentReviewPanel
        pendingReview={pendingReview}
        selectedCount={selected.length}
        reviewableCount={reviewableRows.length}
        reviewError={reviewError}
        review={review}
        onReview={startDocumentReview}
      />

      <p className="mt-3 text-[12.5px] text-slate-500">
        Tệp trùng trong cùng lô không được lưu bản sao lần hai. Tệp giữ nguyên quyền riêng tư trong kho chứng từ — hệ thống không tạo liên kết công khai.
      </p>
    </section>
  );
}

// =============================================================================
// LOGI_TRADE_DOCUMENT_SHIPMENT_REVIEW_RUN3_01 — the bounded review surface.
//
// Renders ONLY the backend's bounded projection: document states first, then
// CẦN XEM (Lệch / Chưa xác định / Thiếu), then THAM KHẢO (Chỉ một nguồn), then
// ĐÃ KHỚP (Khớp). No score, no percentage, no invented quality metric, and a
// CONFLICT always shows every source side with an explicit "no winner chosen".
// =============================================================================

function DocumentReviewPanel({
  pendingReview,
  selectedCount,
  reviewableCount,
  reviewError,
  review,
  onReview,
}: {
  pendingReview: string;
  selectedCount: number;
  reviewableCount: number;
  reviewError: string;
  review: ShipmentDocumentReview | null;
  onReview: () => void;
}) {
  const pending = Boolean(pendingReview);
  if (reviewableCount === 0 && !review) return null;

  const counts = review?.statusCounts;
  const summaryChips: { label: string; value: number; tone: string }[] = counts
    ? [
        { label: "Lệch", value: counts.CONFLICT, tone: "bg-red-50 border-red-200 text-red-800" },
        { label: "Chưa xác định", value: counts.UNKNOWN, tone: "bg-amber-50 border-amber-200 text-amber-900" },
        { label: "Thiếu", value: counts.MISSING, tone: "bg-orange-50 border-orange-200 text-orange-900" },
        { label: "Chỉ một nguồn", value: counts.SINGLE_SOURCE, tone: "bg-slate-50 border-slate-200 text-slate-700" },
        { label: "Khớp", value: counts.SAME, tone: "bg-emerald-50 border-emerald-200 text-emerald-800" },
      ]
    : [];

  return (
    <section
      className="mt-4 rounded-xl border-2 border-slate-200 bg-slate-50 p-3 md:p-4"
      data-testid="document-review"
    >
      <div className="flex flex-wrap items-center gap-x-3 gap-y-2">
        <h4 className="font-extrabold text-[15px] text-[#0f2a4a] inline-flex items-center gap-2 min-w-0">
          <FileSearch size={17} className="text-[#1e5aa8] shrink-0" />
          <span className="break-words">Kiểm tra chứng từ</span>
        </h4>
        <span className="text-[13px] font-bold text-slate-600" data-testid="document-review-count">
          Đã chọn {selectedCount} tệp
        </span>
      </div>

      <p className="mt-1.5 text-[12.5px] text-slate-500">
        Chọn tối đa {MAX_REVIEW_FILES} tệp PDF/XLSX đã có sẵn của lô rồi bấm kiểm tra. Hệ thống đọc tệp
        trên máy chủ — không tải lên lại, không ghi vào hồ sơ lô.
      </p>

      <div className="mt-3 flex flex-wrap items-center gap-2">
        <button
          type="button"
          data-testid="document-review-run"
          disabled={pending || selectedCount === 0}
          onClick={onReview}
          className={cx(
            "btn-press touch-target inline-flex items-center gap-2 rounded-xl px-5 min-h-[48px] font-extrabold",
            pending || selectedCount === 0 ? "bg-slate-300 text-slate-600" : "bg-[#0f2a4a] text-white"
          )}
        >
          {pending ? <LoaderCircle size={17} className="animate-spin" /> : <FileSearch size={17} />}
          {pending ? "ĐANG KIỂM TRA…" : "KIỂM TRA CHỨNG TỪ"}
        </button>
        <span className="text-[12.5px] font-semibold text-slate-600" data-testid="document-review-ephemeral">
          {ALWAYS_REVIEW_NOTE}
        </span>
      </div>

      {reviewError && (
        <p
          data-testid="document-review-error"
          className="mt-3 rounded-xl bg-red-50 border border-red-200 px-3 py-2 text-[13.5px] font-semibold text-red-700"
        >
          {reviewError}
        </p>
      )}

      {review && <ReviewResult review={review} summaryChips={summaryChips} />}
    </section>
  );
}

function ReviewResult({
  review,
  summaryChips,
}: {
  review: ShipmentDocumentReview;
  summaryChips: { label: string; value: number; tone: string }[];
}) {
  const documents: DocumentReviewDocument[] = review.documents ?? [];
  const facts: DocumentReviewFact[] = review.facts ?? [];

  return (
    <div className="mt-3" data-testid="document-review-result" data-request-id={review.requestId}>
      <p
        className="rounded-xl bg-blue-50 border border-blue-200 px-3 py-2 text-[13.5px] font-bold text-blue-900"
        data-testid="document-review-not-saved"
      >
        {ALWAYS_REVIEW_NOTE}
      </p>

      <div className="mt-3 grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-2" data-testid="document-review-summary">
        {summaryChips.map((chip) => (
          <div
            key={chip.label}
            data-testid="document-review-chip"
            data-status-label={chip.label}
            className={cx("rounded-xl border px-3 py-2 text-center", chip.tone)}
          >
            <p className="text-[22px] font-extrabold leading-none">{chip.value}</p>
            <p className="mt-1 text-[12.5px] font-bold break-words">{chip.label}</p>
          </div>
        ))}
      </div>

      <p className="mt-2 text-[12.5px] font-semibold text-slate-600" data-testid="document-review-partial">
        Đã đọc {review.readableCount}/{review.selectedCount} tệp · {review.partialNote}
      </p>

      {documents.length > 0 && (
        <ul className="mt-3 space-y-1.5" data-testid="document-review-documents">
          {documents.map((doc) => (
            <li
              key={doc.attachmentId}
              data-testid="document-review-document"
              data-state={doc.state}
              className="rounded-xl border border-slate-200 bg-white px-3 py-2 min-w-0"
            >
              <p className="font-bold text-[13.5px] text-[#0f2a4a] break-words">{doc.fileName}</p>
              <p className={cx("text-[12.5px] font-semibold break-words", DOC_STATE_TONE[doc.state] || "text-slate-600")}>
                {doc.stateLabel}
                {doc.documentTypeLabel ? ` · ${doc.documentTypeLabel}` : ""}
              </p>
              {doc.reason && <p className="text-[12.5px] text-slate-500 break-words">{doc.reason}</p>}
            </li>
          ))}
        </ul>
      )}

      {facts.length === 0 ? (
        <p className="mt-3 text-[13.5px] font-semibold text-slate-600" data-testid="document-review-no-facts">
          Chưa đọc được nội dung chứng từ nào — chưa đối chiếu được thông tin.
        </p>
      ) : (
        FACT_SECTIONS.map((section) => {
          const items = facts.filter((fact) => section.statuses.includes(fact.status));
          if (items.length === 0) return null;
          return (
            <div key={section.key} className="mt-4" data-testid={`document-review-section-${section.key}`}>
              <h5 className="font-extrabold text-[14px] text-[#0f2a4a] tracking-wide">{section.title}</h5>
              <ul className="mt-2 space-y-2">
                {items.map((fact) => (
                  <FactCard key={fact.fieldKey} fact={fact} />
                ))}
              </ul>
            </div>
          );
        })
      )}
    </div>
  );
}

function FactCard({ fact }: { fact: DocumentReviewFact }) {
  const sides = fact.sides ?? [];
  return (
    <li
      data-testid="document-review-fact"
      data-field-key={fact.fieldKey}
      data-status={fact.status}
      className={cx("rounded-xl border px-3 py-2.5 min-w-0", STATUS_TONE[fact.status] || "bg-white border-slate-200")}
    >
      <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
        <p className="font-extrabold text-[14px] break-words">{fact.label}</p>
        <ToneBadge tone={fact.status === "SAME" ? "green" : fact.status === "CONFLICT" ? "red" : "amber"} size="sm">
          {fact.statusLabel.toUpperCase()}
        </ToneBadge>
        <span className="text-[11.5px] font-bold opacity-70 break-all">{fact.fieldKey}</span>
      </div>

      {sides.length > 0 && (
        <ul className="mt-2 space-y-1.5" data-testid="document-review-fact-sides">
          {sides.map((side, index) => (
            <li
              key={`${side.documentLabel}-${index}`}
              data-testid="document-review-fact-side"
              className="rounded-lg bg-white/70 border border-white px-2.5 py-1.5 min-w-0"
            >
              <p className="text-[12px] font-bold opacity-80 break-words">
                {side.documentTypeLabel || side.fileName}
                {side.location ? ` · ${side.location}` : ""}
              </p>
              <p className="text-[14px] font-extrabold break-words">{side.rawValue}</p>
            </li>
          ))}
        </ul>
      )}

      {fact.operatorNote && (
        <p
          className="mt-2 inline-flex items-start gap-1.5 text-[12.5px] font-extrabold break-words"
          data-testid="document-review-conflict-note"
        >
          <AlertTriangle size={14} className="mt-0.5 shrink-0" />
          {fact.operatorNote}
        </p>
      )}
      {fact.status !== "CONFLICT" && fact.status !== "SAME" && (
        <p className="mt-1.5 text-[12px] font-semibold opacity-80 break-words">{fact.reason}</p>
      )}
      {fact.status === "SAME" && (
        <p className="mt-1.5 inline-flex items-center gap-1.5 text-[12px] font-semibold opacity-80">
          <CheckCircle2 size={13} className="shrink-0" />
          {sides.length} nguồn độc lập trùng nhau sau chuẩn hóa.
        </p>
      )}
    </li>
  );
}
