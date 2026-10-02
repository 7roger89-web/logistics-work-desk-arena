import { ChevronDown, Download, FileText, Plus } from "lucide-react";
import { GhostBtn, PrimaryBtn, ToneBadge, SheetDialog } from "./ui";
import { cx } from "../lib/format";
import type {
  ShipmentDocumentAction,
  ShipmentDocumentCard,
  ShipmentDocumentHistoryItem,
} from "../lib/shipmentDocumentPicker";
import type { ShipmentDocumentTemplate } from "../lib/viewmodel";

export interface ShipmentDocumentSelectionControl {
  catalog: ShipmentDocumentTemplate[];
  savedIds: string[];
  draftIds: string[];
  canEdit: boolean;
  storageConfigured: boolean;
  open: boolean;
  pending: boolean;
  error: string;
  onOpen: () => void;
  onClose: () => void;
  onDraftChange: (ids: string[]) => void;
  onSave: () => void;
}

interface Props {
  shipmentId: string;
  cards: ShipmentDocumentCard[];
  selection: ShipmentDocumentSelectionControl;
  onAction: (card: ShipmentDocumentCard, action: ShipmentDocumentAction) => void;
  onDownload: (card: ShipmentDocumentCard, history: ShipmentDocumentHistoryItem) => void;
}

const STATUS: Record<ShipmentDocumentCard["state"], { label: string; tone: "green" | "amber" | "blue" | "gray" }> = {
  READY: { label: "Sẵn sàng", tone: "blue" },
  MISSING_INFO: { label: "Thiếu thông tin", tone: "amber" },
  GENERATED: { label: "Đã tạo", tone: "green" },
  UNAVAILABLE: { label: "Chưa khả dụng", tone: "gray" },
};

function canDownload(history: ShipmentDocumentHistoryItem, storageConfigured: boolean): boolean {
  return Boolean(history.downloadBase64 || (history.attachmentId && history.downloadAvailable && storageConfigured));
}

function actionLabel(action: ShipmentDocumentAction): string {
  switch (action) {
    case "GENERATE_CONTRACT": return "Tạo bản chứng từ";
    case "GENERATE_PXK": return "Tạo phiếu xuất kho";
    case "GENERATE_GNT": return "Tạo giấy nộp thuế";
    case "OPEN_CONTRACT": return "Mở hợp đồng để bổ sung";
    case "OPEN_CONTRACT_LIST": return "Mở danh sách hợp đồng";
    case "OPEN_COMMERCIAL_FLOW": return "Xác nhận hình thức nhập khẩu";
    case "OPEN_IMPORT": return "Bổ sung thông tin thuế";
    case "OPEN_DELIVERY": return "Mở xác nhận giao hàng";
    case "OPEN_PXK": return "Bổ sung thông tin PXK";
  }
}

function latestSummary(row: ShipmentDocumentHistoryItem): string {
  const revision = Number(row.revision) > 0 ? `R${row.revision}` : "Bản đã tạo";
  const details = [revision, row.fileName, row.generatedAt, row.generatedBy].filter(Boolean);
  return details.join(" · ");
}

export default function ShipmentDocumentPicker({
  shipmentId,
  cards,
  selection,
  onAction,
  onDownload,
}: Props) {
  const selectedCount = selection.savedIds.length;
  const disabledOptionReasonId = (id: string) => `document-template-reason-${id}`;

  return (
    <section
      id="shipment-document-picker"
      data-testid="shipment-document-picker"
      className="xl:col-span-2 rounded-2xl bg-white border border-slate-200 p-4 md:p-5"
      aria-labelledby="shipment-document-picker-title"
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 id="shipment-document-picker-title" className="text-balance font-extrabold text-[17px] text-[#0f2a4a]">
            Biểu mẫu &amp; chứng từ
          </h3>
          <p className="text-pretty text-[13px] text-slate-500 mt-0.5">
            Chọn những biểu mẫu cần theo dõi cho riêng lô {shipmentId}. Bỏ chọn chỉ ẩn khỏi danh sách này, không xóa bản đã tạo.
          </p>
        </div>
        {selection.canEdit ? (
          <PrimaryBtn
            onClick={selection.onOpen}
            testId="shipment-document-picker-open"
            className="shrink-0"
          >
            <Plus size={17} aria-hidden="true" /> Chọn biểu mẫu
          </PrimaryBtn>
        ) : (
          <span className="text-[12.5px] text-slate-500" data-testid="shipment-document-picker-read-only">
            Chỉ xem — không có quyền lưu lựa chọn.
          </span>
        )}
      </div>

      {selection.error && !selection.open && (
        <p role="alert" className="mt-3 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-[13px] font-semibold text-red-800">
          {selection.error}
        </p>
      )}

      {cards.length === 0 ? (
        <div className="mt-4 rounded-xl border border-dashed border-slate-300 bg-slate-50 p-4 text-center" data-testid="shipment-document-picker-empty">
          <FileText size={20} className="mx-auto text-slate-400" aria-hidden="true" />
          <p className="text-[13.5px] font-semibold text-slate-700 mt-2">Chưa chọn biểu mẫu cho lô này.</p>
          {selection.canEdit && <p className="text-[12.5px] text-slate-500 mt-1">Chọn từ danh mục hiện có để bắt đầu.</p>}
        </div>
      ) : (
        <div className="mt-4 grid grid-cols-1 lg:grid-cols-2 gap-3" data-testid="shipment-document-cards">
          {cards.map((card) => {
            const status = STATUS[card.state];
            const latest = card.currentOutput ?? card.history[card.history.length - 1];
            const downloadEnabled = Boolean(latest && card.latestDownloadAvailable && canDownload(latest, selection.storageConfigured));
            return (
              <article
                key={card.id}
                data-testid="shipment-document-card"
                data-document-id={card.id}
                data-state={card.state}
                className="min-w-0 rounded-xl border border-slate-200 bg-white p-3.5"
              >
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div className="min-w-0">
                    <p className="font-extrabold text-[14.5px] text-[#0f2a4a]">{card.label}</p>
                    <p className="text-[11.5px] text-slate-500 mt-0.5">{card.category}</p>
                  </div>
                  <ToneBadge tone={status.tone} size="sm">{status.label}</ToneBadge>
                </div>

                {card.reason && (
                  <p className="text-pretty text-[12.5px] text-slate-600 mt-2" data-testid="shipment-document-reason">
                    {card.reason}
                  </p>
                )}
                {card.missing.length > 0 && (
                  <div className="mt-2 rounded-lg bg-amber-50 border border-amber-200 px-3 py-2">
                    <p className="text-[11.5px] font-bold uppercase text-amber-800">Cần bổ sung</p>
                    <ul className="mt-1 list-disc pl-4 text-[12.5px] text-amber-900">
                      {card.missing.map((item, index) => <li key={`${item}-${index}`}>{item}</li>)}
                    </ul>
                  </div>
                )}

                {latest && (
                  <div className="mt-3 rounded-lg border border-emerald-200 bg-emerald-50/70 p-2.5">
                    <p className="text-[11.5px] font-bold uppercase text-emerald-800">Bản mới nhất</p>
                    <p className="text-[12.5px] font-semibold text-emerald-950 break-words mt-0.5">{latestSummary(latest)}</p>
                    <button
                      type="button"
                      disabled={!downloadEnabled}
                      data-testid="shipment-document-download-latest"
                      onClick={() => onDownload(card, latest)}
                      className={cx(
                        "btn-press touch-target mt-2 inline-flex min-h-[40px] items-center gap-1.5 rounded-lg border px-3 text-[12.5px] font-bold",
                        downloadEnabled
                          ? "border-emerald-700 text-emerald-800 hover:bg-emerald-100"
                          : "cursor-not-allowed border-slate-200 text-slate-400"
                      )}
                      aria-label={downloadEnabled ? `Tải ${card.label} bản mới nhất` : `${card.label} chưa có tệp tải được`}
                    >
                      <Download size={15} aria-hidden="true" />
                      {downloadEnabled ? "Tải bản mới nhất" : "Tệp tải chưa khả dụng"}
                    </button>
                  </div>
                )}

                {card.action && card.state !== "GENERATED" && (
                  <button
                    type="button"
                    data-testid="shipment-document-primary-action"
                    onClick={() => onAction(card, card.action!)}
                    className="btn-press touch-target mt-3 inline-flex min-h-[42px] items-center justify-center rounded-lg bg-[#0f2a4a] px-3.5 text-[12.5px] font-bold text-white hover:bg-[#14365e]"
                  >
                    {actionLabel(card.action)}
                  </button>
                )}
                {card.openOutputAction && (
                  <button
                    type="button"
                    data-testid="shipment-document-open-output"
                    onClick={() => onAction(card, card.openOutputAction!)}
                    className="btn-press touch-target mt-3 inline-flex min-h-[42px] items-center justify-center rounded-lg border border-slate-300 px-3.5 text-[12.5px] font-semibold text-[#0f2a4a] hover:bg-slate-50"
                  >
                    Mở chứng từ / nơi quản lý
                  </button>
                )}
                {card.createRevisionAction && (
                  <button
                    type="button"
                    data-testid="shipment-document-create-revision"
                    onClick={() => onAction(card, card.createRevisionAction!)}
                    className="btn-press touch-target mt-2 inline-flex min-h-[40px] items-center rounded-lg border border-slate-300 px-3 text-[12.5px] font-semibold text-[#0f2a4a] hover:bg-slate-50"
                  >
                    Tạo bản mới
                  </button>
                )}

                {card.history.length > 0 && (
                  <details className="mt-3 border-t border-slate-100 pt-2" data-testid="shipment-document-history">
                    <summary className="flex cursor-pointer list-none items-center gap-1 text-[12.5px] font-semibold text-[#1e5aa8]">
                      <ChevronDown size={14} aria-hidden="true" /> Lịch sử ({card.history.length})
                    </summary>
                    <ol className="mt-2 space-y-2">
                      {card.history.map((row, index) => {
                        const enabled = canDownload(row, selection.storageConfigured);
                        return (
                          <li key={row.recordId || `${card.id}-${row.revision}-${index}`} className="flex flex-wrap items-center justify-between gap-2 rounded-lg bg-slate-50 px-2.5 py-2">
                            <div className="min-w-0">
                              <p className="text-[12px] font-semibold text-slate-800">R{row.revision} · {row.fileName || row.status}</p>
                              <p className="text-[11.5px] text-slate-500">{[row.generatedAt, row.generatedBy].filter(Boolean).join(" · ")}</p>
                            </div>
                            <button
                              type="button"
                              disabled={!enabled}
                              data-testid="shipment-document-download-history"
                              onClick={() => onDownload(card, row)}
                              className="btn-press touch-target inline-flex min-h-[36px] items-center gap-1 rounded-md border border-slate-200 px-2.5 text-[11.5px] font-bold text-[#0f2a4a] disabled:cursor-not-allowed disabled:text-slate-400"
                              aria-label={enabled ? `Tải ${card.label} bản R${row.revision}` : `${card.label} bản R${row.revision} chưa thể tải`}
                            >
                              <Download size={13} aria-hidden="true" /> Tải
                            </button>
                          </li>
                        );
                      })}
                    </ol>
                  </details>
                )}
              </article>
            );
          })}
        </div>
      )}

      <p className="text-[11.5px] text-slate-400 mt-3">Đã chọn {selectedCount} biểu mẫu · lịch sử chứng từ độc lập với lựa chọn hiện tại.</p>

      {selection.open && (
        <SheetDialog
          id="shipment-document-picker-dialog"
          testId="shipment-document-picker-dialog"
          labelledBy="shipment-document-picker-dialog-title"
          pending={selection.pending}
          width={560}
          onClose={selection.onClose}
        >
          <div className="flex items-start justify-between gap-3">
            <div>
              <h3 id="shipment-document-picker-dialog-title" className="text-balance text-[18px] font-extrabold text-[#0f2a4a]">
                Chọn biểu mẫu cho lô {shipmentId}
              </h3>
              <p className="text-pretty text-[13px] text-slate-500 mt-1">Có thể chọn nhiều biểu mẫu. Tệp đã tạo vẫn nằm trong lịch sử khi bỏ chọn.</p>
            </div>
            <button
              type="button"
              aria-label="Đóng chọn biểu mẫu"
              disabled={selection.pending}
              onClick={selection.onClose}
              className="btn-press touch-target grid size-10 shrink-0 place-items-center rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50 disabled:opacity-50"
            >
              <span aria-hidden="true">×</span>
            </button>
          </div>

          <fieldset className="mt-4 space-y-2" disabled={selection.pending}>
            <legend className="sr-only">Danh mục biểu mẫu</legend>
            {selection.catalog.map((template) => {
              const checked = selection.draftIds.includes(template.id);
              const disabled = !template.active || (!template.available && !checked);
              const reasonId = disabledOptionReasonId(template.id);
              return (
                <label
                  key={template.id}
                  data-testid="shipment-document-template-option"
                  data-template-id={template.id}
                  className={cx(
                    "flex min-h-[60px] items-start gap-3 rounded-xl border p-3",
                    checked ? "border-blue-300 bg-blue-50/70" : "border-slate-200 bg-white",
                    disabled ? "cursor-not-allowed opacity-60" : "cursor-pointer"
                  )}
                >
                  <input
                    type="checkbox"
                    id={`document-template-${template.id}`}
                    name="shipment-document-template"
                    value={template.id}
                    checked={checked}
                    disabled={disabled}
                    aria-describedby={!template.available ? reasonId : undefined}
                    onChange={(event) => {
                      const next = new Set(selection.draftIds);
                      if (event.currentTarget.checked) next.add(template.id);
                      else next.delete(template.id);
                      selection.onDraftChange(selection.catalog
                        .filter((entry) => entry.active && next.has(entry.id))
                        .map((entry) => entry.id));
                    }}
                    className="mt-1 size-4 shrink-0 accent-[#1e5aa8]"
                  />
                  <span className="min-w-0 flex-1">
                    <span className="block text-[13.5px] font-bold text-[#0f2a4a]">{template.label}</span>
                    <span className="block text-[11.5px] text-slate-500 mt-0.5">{template.category}</span>
                    {!template.available && (
                      <span id={reasonId} className="block text-[11.5px] text-amber-800 mt-1">{template.availabilityReason || "Hiện chưa sẵn sàng."}</span>
                    )}
                  </span>
                </label>
              );
            })}
          </fieldset>

          {selection.error && (
            <p role="alert" data-testid="shipment-document-selection-error" className="mt-3 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-[13px] font-semibold text-red-800">
              {selection.error}
            </p>
          )}
          {selection.pending && (
            <p role="status" data-testid="shipment-document-selection-pending" className="mt-3 rounded-lg bg-blue-50 px-3 py-2 text-[13px] font-semibold text-blue-800">
              Đang chờ backend xác nhận lựa chọn…
            </p>
          )}
          <div className="mt-4 flex flex-wrap justify-end gap-2 border-t border-slate-100 pt-3">
            <GhostBtn onClick={selection.onClose} disabled={selection.pending}>Hủy</GhostBtn>
            <PrimaryBtn onClick={selection.onSave} disabled={selection.pending} testId="shipment-document-selection-save">
              {selection.pending ? "Đang lưu…" : "Lưu lựa chọn"}
            </PrimaryBtn>
          </div>
        </SheetDialog>
      )}
    </section>
  );
}
