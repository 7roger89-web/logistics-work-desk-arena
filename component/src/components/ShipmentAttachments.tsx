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

import { useEffect, useRef, useState, useSyncExternalStore } from "react";
import { CloudUpload, Download, FileCheck2, LoaderCircle, Paperclip } from "lucide-react";
import { SectionTitle, ToneBadge, inputCls } from "./ui";
import { useStore } from "../lib/store";
import { downloadBinaryFile, cx } from "../lib/format";
import {
  getViewModel,
  subscribeViewModel,
  type AttachmentPolicy,
  type ShipmentAttachment,
} from "../lib/viewmodel";

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
          {file && <span className="text-[13px] text-slate-600 min-w-0 break-words">{file.name}</span>}
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
              className="flex flex-wrap items-center gap-x-3 gap-y-2 rounded-xl border border-slate-200 p-3 min-w-0"
            >
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

      <p className="mt-3 text-[12.5px] text-slate-500">
        Tệp trùng trong cùng lô không được lưu bản sao lần hai. Tệp giữ nguyên quyền riêng tư trong kho chứng từ — hệ thống không tạo liên kết công khai.
      </p>
    </section>
  );
}
