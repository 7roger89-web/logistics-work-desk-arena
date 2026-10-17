import { useEffect, useMemo, useState, useSyncExternalStore } from "react";
import { FileSpreadsheet, LockKeyhole, RefreshCw, RotateCcw, Save, TriangleAlert, Undo2 } from "lucide-react";
import { GhostBtn, PrimaryBtn, ToneBadge, inputCls } from "./ui";
import { useStore } from "../lib/store";
import { getViewModel, subscribeViewModel } from "../lib/viewmodel";
import { cx } from "../lib/format";
import type { WorkbookCell, WorkbookCellEdit, WorkbookPage, WorkbookView } from "../lib/excelQuote";
import type { LogiEventName } from "../lib/dispatcher";
import "./excelQuote.css";

/**
 * Source workbook viewer/editor. Original bytes stay immutable in GridFS;
 * edits are saved as a separate GridFS draft. The backend owns validation,
 * hashing, ownership and workbook serialization. Formulas are never evaluated.
 */
const CLASS_LABEL: Record<string, string> = {
  CUSTOMER: "Sheet khách",
  INTERNAL: "Sheet nội bộ",
  UNCLASSIFIED: "Chưa phân loại",
};
type EditKind = WorkbookCellEdit["type"];
type EditMap = Record<string, WorkbookCellEdit>;
interface Selection { sheet: string; r: number; c: number }
interface UndoState { edits: EditMap; restoreOriginal: boolean }

const editKey = (sheet: string, r: number, c: number) => `${sheet}:${r}:${c}`;
const editKind = (cell?: WorkbookCell): EditKind => cell?.kind === "formula" ? "formula" : typeof cell?.value === "number" ? "number" : "text";
const initialValue = (cell?: WorkbookCell) => cell?.kind === "formula" ? String(cell.f || "=") : cell?.value == null ? "" : String(cell.value);
const plainNumber = /^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$/;

function cellText(cell: WorkbookCell | undefined, edit?: WorkbookCellEdit): { text: string; badge: string } {
  if (edit) {
    if (edit.type === "blank") return { text: "", badge: "" };
    if (edit.type === "formula") return { text: `${edit.value} → chưa tính lại`, badge: "F · UNKNOWN" };
    return { text: edit.value, badge: edit.type === "number" ? "N*" : "" };
  }
  if (!cell) return { text: "", badge: "" };
  if (cell.kind === "formula") {
    if (cell.unknown || cell.value === "" || cell.value === undefined) {
      return { text: `${cell.f} → chưa có giá trị cache`, badge: "UNKNOWN" };
    }
    return { text: String(cell.display ?? cell.value), badge: "F" };
  }
  if (cell.value === undefined || cell.value === "") return { text: "", badge: "" };
  return { text: String(cell.display ?? cell.value), badge: cell.nf ? "N" : "" };
}

function excelColumnName(column: number): string {
  let value = column;
  let name = "";
  while (value > 0) {
    const remainder = (value - 1) % 26;
    name = String.fromCharCode(65 + remainder) + name;
    value = Math.floor((value - 1) / 26);
  }
  return name;
}
function excelColumnIndex(name: string): number {
  const value = String(name || "").trim().toUpperCase();
  if (!/^[A-Z]{1,3}$/.test(value)) return 0;
  let index = 0;
  for (const letter of value) index = index * 26 + letter.charCodeAt(0) - 64;
  return index;
}

function cellStyle(cell: WorkbookCell | undefined, edited: boolean, selected: boolean): React.CSSProperties {
  const style: React.CSSProperties = {};
  if (cell?.font?.bold) style.fontWeight = 700;
  if (cell?.font?.italic) style.fontStyle = "italic";
  if (cell?.font?.size) style.fontSize = `${Math.min(20, Math.max(9, cell.font.size))}px`;
  if (cell?.font?.color) style.color = cell.font.color;
  if (cell?.fill) style.background = cell.fill;
  if (cell?.align?.h === "center") style.textAlign = "center";
  if (cell?.align?.h === "right") style.textAlign = "right";
  if (cell?.align?.v === "top") style.verticalAlign = "top";
  if (cell?.align?.v === "center") style.verticalAlign = "middle";
  if (cell?.align?.wrap) style.whiteSpace = "pre-wrap";
  if (cell?.border) {
    const sides = cell.border.split(",");
    const width = (side: string) => (sides.some((s) => s.startsWith(side)) ? "1px solid #94a3b8" : undefined);
    style.borderTop = width("t");
    style.borderBottom = width("b");
    style.borderLeft = width("l");
    style.borderRight = width("r");
  }
  if (edited) style.background = "#fff7df";
  if (selected) style.boxShadow = "inset 0 0 0 2px #1e5aa8";
  return style;
}

function SheetGrid({ page, editable, edits, selection, onSelect, onPaste }: {
  page: WorkbookPage;
  editable: boolean;
  edits: EditMap;
  selection: Selection | null;
  onSelect: (r: number, c: number, cell?: WorkbookCell) => void;
  onPaste: (event: React.ClipboardEvent<HTMLDivElement>) => void;
}) {
  const index = useMemo(() => new Map(page.cells.map((cell) => [`${cell.r}:${cell.c}`, cell])), [page]);
  const { anchors, covered, rows, cols } = useMemo(() => {
    const anchors = new Map<string, { rs: number; cs: number }>();
    const covered = new Set<string>();
    for (const merge of page.merges) {
      const rs = merge.max_row - merge.min_row + 1;
      const cs = merge.max_col - merge.min_col + 1;
      anchors.set(`${merge.min_row}:${merge.min_col}`, { rs, cs });
      for (let r = merge.min_row; r <= merge.max_row; r += 1) {
        for (let c = merge.min_col; c <= merge.max_col; c += 1) {
          if (r !== merge.min_row || c !== merge.min_col) covered.add(`${r}:${c}`);
        }
      }
    }
    const maxRow = Math.max(1, page.limits.max_rows);
    const maxCol = Math.max(1, page.limits.max_cols);
    return { anchors, covered, rows: Array.from({ length: maxRow }, (_, i) => (page.start_row || 1) + i),
      cols: Array.from({ length: maxCol }, (_, i) => (page.start_col || 1) + i) };
  }, [page]);
  return (
    <div className="eq-wb-scroll" data-testid="workbook-grid" data-sheet={page.sheet} tabIndex={editable ? 0 : undefined} onPaste={onPaste}>
      <table className="eq-wb-table">
        <colgroup>
          <col style={{ width: 44 }} />
          {cols.map((column) => (
            <col key={column} style={{ width: `${Math.min(320, Math.max(58, (page.column_widths[excelColumnName(column)] || 14) * 7))}px`,
              display: page.hidden_columns.includes(excelColumnName(column)) ? "none" : undefined }} />
          ))}
        </colgroup>
        <thead><tr><th className="eq-wb-colcorner" aria-hidden="true" />{cols.map((column) => <th key={column} scope="col" className="eq-wb-colhead">{excelColumnName(column)}</th>)}</tr></thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row} style={{ height: page.row_heights[String(row)] ? `${Math.min(120, page.row_heights[String(row)])}px` : undefined }}
              data-hidden={page.hidden_rows.includes(row) ? "true" : undefined} className={cx(page.hidden_rows.includes(row) && "eq-wb-hidden")}>
              <th scope="row" className="eq-wb-rownum">{row}</th>
              {cols.map((column) => {
                const key = `${row}:${column}`;
                if (covered.has(key)) return null;
                const cell = index.get(key);
                const anchor = anchors.get(key);
                const changed = edits[editKey(page.sheet, row, column)];
                const selected = selection?.sheet === page.sheet && selection.r === row && selection.c === column;
                const { text, badge } = cellText(cell, changed);
                return (
                  <td key={column} style={{ ...cellStyle(cell, !!changed, !!selected),
                    display: page.hidden_columns.includes(excelColumnName(column)) ? "none" : undefined }}
                    rowSpan={anchor?.rs} colSpan={anchor?.cs}
                    data-testid={`workbook-cell-${row}:${column}`}
                    data-formula={cell?.kind === "formula" ? "true" : undefined}
                    data-unknown={cell?.unknown || changed?.type === "formula" ? "true" : undefined}
                    data-edited={changed ? "true" : undefined}
                    aria-label={`Ô ${excelColumnName(column)}${row}${changed ? ", đã sửa" : ""}`}
                    title={[cell?.f, cell?.nf].filter(Boolean).join(" · ") || undefined}
                    className={cx(cell?.unknown && "eq-wb-unknown", editable && "eq-wb-cell-editable", selected && "eq-wb-cell-selected")}
                    onClick={(event) => {
                      if (!editable || covered.has(key)) return;
                      onSelect(row, column, cell);
                      (event.currentTarget.closest(".eq-wb-scroll") as HTMLDivElement | null)?.focus({ preventScroll: true });
                    }}>
                    {text}
                    {badge && <span className="eq-wb-badge">{badge}</span>}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function ExcelSourceWorkbook({ quoteId, customerId, source, onRequestOpen, onView, onDirtyChange, autoOpen = false }: {
  quoteId?: string;
  customerId: string;
  source?: { file_name: string; sha256: string; sheet_names: string[]; storage_file_id?: string };
  onRequestOpen?: () => void;
  onView?: (view: WorkbookView) => void;
  onDirtyChange?: (dirty: boolean) => void;
  autoOpen?: boolean;
}) {
  const { dispatch } = useStore();
  const vm = useSyncExternalStore(subscribeViewModel, getViewModel, getViewModel);
  const [open, setOpen] = useState(false);
  const [requestId, setRequestId] = useState("");
  const [requestEvent, setRequestEvent] = useState<"quote_source_workbook_view" | "quote_workbook_draft_save">("quote_source_workbook_view");
  const [sheet, setSheet] = useState("");
  const [startRow, setStartRow] = useState("1");
  const [startColumn, setStartColumn] = useState("A");
  const [view, setView] = useState<WorkbookView | null>(null);
  const [edits, setEdits] = useState<EditMap>({});
  const [undoStack, setUndoStack] = useState<UndoState[]>([]);
  const [restoreOriginal, setRestoreOriginal] = useState(false);
  const [selection, setSelection] = useState<Selection | null>(null);
  const [editorType, setEditorType] = useState<EditKind>("text");
  const [editorValue, setEditorValue] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    setView(null);
    setEdits({});
    setUndoStack([]);
    setRestoreOriginal(false);
    setSelection(null);
    setSheet("");
    if (autoOpen && (source?.storage_file_id || quoteId)) {
      setOpen(true);
      sendView("");
    }
  }, [source?.sha256, quoteId, autoOpen]); // eslint-disable-line react-hooks/exhaustive-deps

  const sendView = (nextSheet: string, row = 1, column = 1) => {
    if (!quoteId && !source?.storage_file_id) { setError("Chưa có tệp nguồn đã lưu để đối chiếu."); return; }
    const id = `workbook-view-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
    const payload: Record<string, unknown> = { customerId, requestId: id };
    if (quoteId) payload.id = quoteId;
    if (source) payload.source = source;
    if (nextSheet) { payload.sheet = nextSheet; payload.startRow = row; payload.startCol = column; }
    if (dispatch("quote_source_workbook_view" as LogiEventName, payload)) {
      setRequestEvent("quote_source_workbook_view");
      setRequestId(id);
      setError("");
    } else setError("Chưa kết nối backend; không hiển thị bản xem workbook.");
  };

  const sendSave = () => {
    if (!view || !view.can_download_source) { setError("Quyền thao tác workbook chưa được cấp; không gửi nội dung ô."); return; }
    if (!Object.keys(edits).length && !restoreOriginal) return;
    const id = `workbook-save-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
    const payload: Record<string, unknown> = {
      customerId, source, requestId: id, sheet,
      startRow: Number(startRow) || 1, startCol: excelColumnIndex(startColumn) || 1,
      expectedVersion: view.draft?.version ?? 0,
      edits: Object.values(edits), restoreOriginal,
    };
    if (quoteId) payload.id = quoteId;
    if (dispatch("quote_workbook_draft_save" as LogiEventName, payload)) {
      setRequestEvent("quote_workbook_draft_save");
      setRequestId(id);
      setError("");
    } else setError("Chưa kết nối backend; bản chỉnh sửa chưa được lưu.");
  };

  useEffect(() => {
    if (!requestId) return;
    const outcome = vm?.lastWrites?.find((write) => write.event === requestEvent && write.requestId === requestId);
    if (!outcome) return;
    setRequestId("");
    if (!outcome.ok || !outcome.readback) {
      setError(String(outcome.error || "Backend không trả về bản workbook đã xác minh."));
      return;
    }
    const readback = outcome.readback as unknown as WorkbookView;
    setView(readback);
    onView?.(readback);
    setError("");
    if (requestEvent === "quote_workbook_draft_save") {
      setEdits({});
      setUndoStack([]);
      setRestoreOriginal(false);
      setSelection(null);
    }
    const nextSheet = sheet || readback.page?.sheet || readback.overview.customer_sheet || readback.overview.sheet_names[0] || "";
    setSheet(nextSheet);
    if (readback.page) {
      setStartRow(String(readback.page.start_row || 1));
      setStartColumn(excelColumnName(readback.page.start_col || 1));
    }
    if (requestEvent === "quote_source_workbook_view" && !readback.page && nextSheet) sendView(nextSheet, 1, 1);
  }, [vm, requestId, requestEvent, onView]);

  useEffect(() => { if (open && !view && !requestId) sendView(""); }, [open]); // eslint-disable-line react-hooks/exhaustive-deps

  const page = view?.page;
  const canEdit = !!view?.can_download_source && !!page && !page.locked;
  const isDirty = Object.keys(edits).length > 0 || restoreOriginal;
  useEffect(() => { onDirtyChange?.(isDirty); }, [isDirty, onDirtyChange]);
  const index = useMemo(() => new Map((page?.cells || []).map((cell) => [`${cell.r}:${cell.c}`, cell])), [page]);
  const selectedCell = selection ? index.get(`${selection.r}:${selection.c}`) : undefined;
  const selectedEdit = selection ? edits[editKey(selection.sheet, selection.r, selection.c)] : undefined;
  const selectedRef = selection ? `${excelColumnName(selection.c)}${selection.r}` : "";
  const sheetInfo = view?.overview.sheets.find((item) => item.name === sheet);
  const notRendered = Object.entries(sheetInfo?.not_rendered || {});

  const rememberUndo = () => setUndoStack((old) => [...old.slice(-19), { edits, restoreOriginal }]);
  const selectCell = (row: number, column: number, cell?: WorkbookCell) => {
    const selected = { sheet, r: row, c: column };
    const edit = edits[editKey(sheet, row, column)];
    setSelection(selected);
    setEditorType(edit?.type ?? editKind(cell));
    setEditorValue(edit?.value ?? initialValue(cell));
  };
  const updateSelected = (value: string, kind = editorType) => {
    if (!selection) return;
    const key = editKey(selection.sheet, selection.r, selection.c);
    rememberUndo();
    setEditorValue(value);
    setEditorType(kind);
    setEdits((old) => ({ ...old, [key]: { ...selection, type: kind, value } }));
  };
  const goToRange = () => {
    const row = Number(startRow);
    const column = excelColumnIndex(startColumn);
    if (!Number.isInteger(row) || row < 1 || row > 1_048_576 || !column || column > 16_384) {
      setError("Nhập vùng Excel hợp lệ: dòng 1–1.048.576, cột A–XFD.");
      return;
    }
    setSelection(null);
    sendView(sheet, row, column);
  };
  const onPaste = (event: React.ClipboardEvent<HTMLDivElement>) => {
    if (!canEdit || !selection || (event.target instanceof HTMLElement && ["INPUT", "TEXTAREA", "SELECT"].includes(event.target.tagName))) return;
    const pasted = event.clipboardData.getData("text/plain");
    if (!pasted) return;
    event.preventDefault();
    const rows = pasted.replace(/\r/g, "").split("\n");
    if (rows.length > 1 && rows[rows.length - 1] === "") rows.pop();
    const cells = rows.map((row) => row.split("\t"));
    const count = cells.reduce((total, row) => total + row.length, 0);
    if (count + Object.keys(edits).length > 4000) { setError("Vùng dán vượt giới hạn 4.000 ô thay đổi."); return; }
    const viewStartRow = page?.start_row || 1;
    const viewStartCol = page?.start_col || 1;
    if (selection.r < viewStartRow || selection.c < viewStartCol
        || selection.r + cells.length - 1 > viewStartRow + (page?.limits.max_rows || 200) - 1
        || selection.c + Math.max(...cells.map((row) => row.length)) - 1 > viewStartCol + (page?.limits.max_cols || 40) - 1) {
      setError("Vùng dán vượt phần sheet đang mở (tối đa 200 dòng × 40 cột). Chọn ô đầu vùng nhỏ hơn."); return;
    }
    rememberUndo();
    const next = { ...edits };
    cells.forEach((row, rowIndex) => row.forEach((value, columnIndex) => {
      const r = selection.r + rowIndex;
      const c = selection.c + columnIndex;
      const originalCell = index.get(`${r}:${c}`);
      const key = editKey(sheet, r, c);
      let type: EditKind = value === "" ? "blank" : value.startsWith("=") ? "formula"
        : plainNumber.test(value) ? "number" : "text";
      if (originalCell?.kind === "formula" && value === String(originalCell.f || "")) type = "formula";
      next[key] = { sheet, r, c, type, value };
    }));
    setEdits(next);
    setRestoreOriginal(false);
    setError("");
  };
  const undo = () => {
    const last = undoStack[undoStack.length - 1];
    if (!last) return;
    setEdits(last.edits);
    setRestoreOriginal(last.restoreOriginal);
    setUndoStack((old) => old.slice(0, -1));
    setError("");
  };
  const restore = () => {
    rememberUndo();
    setEdits({});
    setRestoreOriginal(true);
    setSelection(null);
    setError("");
  };
  const closeWorkbook = () => {
    if (requestId) return;
    if (isDirty && !window.confirm("Workbook có ô thay đổi chưa lưu. Đóng và bỏ các thay đổi này?")) return;
    if (isDirty) {
      setEdits({});
      setUndoStack([]);
      setRestoreOriginal(false);
      setSelection(null);
      setError("");
    }
    setOpen(false);
  };

  if (!open) {
    return (
      <div className="mt-3 rounded-xl border border-slate-200 bg-slate-50 p-3" data-testid="excel-source-workbook-entry">
        <p className="text-[13px] text-slate-600">
          Tên và thứ tự sheet, ô gộp, định dạng, chữ, số và công thức được đọc từ workbook gốc. Bản sửa lưu riêng; một số đối tượng Excel không được hiển thị hoặc bảo toàn.
        </p>
        <PrimaryBtn className="mt-2" testId="excel-source-workbook-open"
          disabled={!quoteId && !source?.storage_file_id}
          onClick={() => { setOpen(true); onRequestOpen?.(); }}>
          <FileSpreadsheet size={17} /> Mở và sửa workbook
        </PrimaryBtn>
      </div>
    );
  }

  return (
    <section className="eq-wb" data-testid="excel-source-workbook" data-readonly={!canEdit}>
      <header className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <h4 className="eq-title mb-1"><FileSpreadsheet size={17} className="inline mr-2" />Workbook · bản gốc không đổi</h4>
          <p className="eq-muted">
            {view?.file_name || source?.file_name || "Tệp nguồn"} · SHA256 {(view?.sha256 || source?.sha256 || "").slice(0, 16)}… ·
            {" "}Bản sửa riêng {view?.draft?.saved ? `v${view.draft.version}` : "chưa lưu"}. Công thức không được tính lại trong trình duyệt; bản xem KHÔNG tuyên bố giữ nguyên 100% định dạng.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <GhostBtn testId="excel-source-workbook-refresh" disabled={!!requestId} onClick={() => sendView(sheet, Number(startRow) || 1, excelColumnIndex(startColumn) || 1)}>
            <RefreshCw size={15} /> {requestId ? "Đang tải…" : "Tải lại sheet"}
          </GhostBtn>
          <GhostBtn testId="excel-source-workbook-close" disabled={!!requestId} onClick={closeWorkbook}>Đóng</GhostBtn>
        </div>
      </header>
      {error && <p role="alert" className="eq-alert border-red-300 bg-red-50 text-red-900 mt-3">{error}</p>}
      {view && (
        <>
          <div className="eq-wb-tabs" role="tablist" aria-label="Sheet trong workbook">
            {view.overview.sheets.map((item) => (
              <button key={item.name} type="button" role="tab" aria-selected={item.name === sheet}
                data-testid={`workbook-tab-${item.index}`} data-classification={item.classification}
                className={cx("eq-wb-tab", item.name === sheet && "eq-wb-tab-active")}
                onClick={() => { setSheet(item.name); setSelection(null); setStartRow("1"); setStartColumn("A"); sendView(item.name, 1, 1); }}>
                <span className="eq-wb-tab-index">{item.index}</span>
                <span className="truncate">{item.name}</span>
                <span className={cx("eq-wb-tab-class", `eq-wb-class-${item.classification.toLowerCase()}`)}>{CLASS_LABEL[item.classification]}</span>
              </button>
            ))}
          </div>
          <p className="eq-muted mt-2" data-testid="workbook-sheet-order">
            Thứ tự sheet trong tệp gốc: {view.overview.sheet_names.join(" → ")}
          </p>
          {view.page && !view.page.locked && <div className="eq-wb-range" data-testid="workbook-range-controls">
            <label>Dòng bắt đầu<input className={inputCls()} data-testid="workbook-start-row" inputMode="numeric" value={startRow} onChange={(event) => setStartRow(event.target.value)} /></label>
            <label>Cột bắt đầu<input className={inputCls()} data-testid="workbook-start-column" value={startColumn} onChange={(event) => setStartColumn(event.target.value.toUpperCase())} placeholder="A–XFD" /></label>
            <GhostBtn testId="workbook-go-to-range" disabled={!!requestId} onClick={goToRange}>{requestId ? "Đang mở…" : "Mở vùng"}</GhostBtn>
            <span className="eq-muted">Tối đa {view.page.limits.max_rows} dòng × {view.page.limits.max_cols} cột mỗi lần xem; nhập vị trí bảng để đi tới vùng xa hơn.</span>
          </div>}
          {view.page?.locked ? (
            <div className="eq-alert border-amber-300 bg-amber-50 text-amber-900 mt-3" data-testid="workbook-locked">
              <LockKeyhole size={16} className="inline mr-2" />{view.page.reason}
              <span className="block mt-1">Sheet vẫn được liệt kê; nội dung workbook và bản sửa không gửi tới trình duyệt khi thiếu quyền.</span>
            </div>
          ) : view.page ? (
            <>
              <div className="flex flex-wrap items-center gap-2 mt-3 text-[13px]">
                <ToneBadge tone={view.page.classification === "CUSTOMER" ? "green" : "amber"}>{CLASS_LABEL[view.page.classification]}</ToneBadge>
                <span>{view.page.row_count} dòng × {view.page.column_count} cột · đang xem {view.page.start_row || 1}–{view.page.end_row || view.page.limits.max_rows}, {excelColumnName(view.page.start_col || 1)}–{excelColumnName(view.page.end_col || view.page.limits.max_cols)} · {view.page.merges.length} ô gộp</span>
                {view.page.sheet_state !== "visible" && <span className="font-semibold text-amber-800">Sheet đang bị ẩn trong tệp gốc</span>}
                {view.page.truncated && <span className="font-semibold text-amber-800">Còn vùng khác chưa hiển thị — dùng “Mở vùng” để đi tới hàng/cột xa hơn.</span>}
              </div>
              {canEdit && (
                <div className="eq-wb-editor" data-testid="workbook-cell-editor">
                  <div className="flex flex-wrap items-end gap-2">
                    <div className="min-w-[72px] text-[13px] font-bold text-[#0f2a4a]" aria-live="polite">{selectedRef || "Chọn ô"}</div>
                    <label className="eq-wb-edit-kind">Kiểu ô
                      <select value={editorType} disabled={!selection} onChange={(event) => updateSelected(editorValue, event.target.value as EditKind)}>
                        <option value="text">Văn bản</option><option value="number">Số</option><option value="formula">Công thức</option><option value="blank">Xóa ô</option>
                      </select>
                    </label>
                    <label className="eq-wb-edit-value">Giá trị ô
                      <textarea rows={2} value={editorType === "blank" ? "" : editorValue} disabled={!selection || editorType === "blank"}
                        onChange={(event) => updateSelected(event.target.value)} placeholder="Chọn một ô trong sheet…" data-testid="workbook-cell-value" />
                    </label>
                  </div>
                  {selection && selectedCell?.kind === "formula" && <p className="text-[12px] text-amber-900 mt-1">Công thức nguồn: {selectedCell.f}. Khi sửa workbook, công thức được lưu nhưng openpyxl không tính lại giá trị.</p>}
                  <div className="flex flex-wrap items-center gap-2 mt-2">
                    <GhostBtn testId="workbook-undo" onClick={undo} disabled={!undoStack.length || !!requestId}><Undo2 size={15} /> Hoàn tác ô</GhostBtn>
                    <GhostBtn testId="workbook-restore-original" onClick={restore} disabled={!!requestId || restoreOriginal}><RotateCcw size={15} /> Khôi phục workbook gốc</GhostBtn>
                    <SuccessWorkbookButton dirty={isDirty} busy={!!requestId} onClick={sendSave} />
                    <span className="text-[12px] text-slate-600" aria-live="polite">
                      {isDirty ? `${Object.keys(edits).length} ô thay đổi chưa lưu` : view.draft?.saved ? `Đã lưu bản sửa riêng · v${view.draft.version}` : "Chưa có thay đổi"}
                    </span>
                  </div>
                  <p className="eq-muted mt-2">Copy ô/vùng từ sheet khác rồi dán vào ô đã chọn (Ctrl/Cmd+V). Số, chữ và công thức chỉ được ghi theo kiểu bạn chọn; công thức chưa tính lại sẽ là CHƯA BIẾT, không phải 0.</p>
                </div>
              )}
              <SheetGrid page={view.page} editable={canEdit} edits={edits} selection={selection}
                onSelect={selectCell} onPaste={onPaste} />
            </>
          ) : requestId ? <p className="eq-muted mt-3">Đang mở sheet…</p> : null}
          <details className="eq-wb-fidelity" data-testid="workbook-fidelity">
            <summary>Mức độ giữ định dạng: cái gì đã render, cái gì chưa</summary>
            <div className="grid sm:grid-cols-2 gap-3 mt-2 text-[13px]">
              <div>
                <b className="text-emerald-800">Đã render</b>
                <ul className="mt-1 space-y-1">{view.overview.fidelity.supported.map((item) => <li key={item}>• {item}</li>)}</ul>
              </div>
              <div>
                <b className="text-amber-800">CHƯA render (ghi rõ, không tuyên bố 100%)</b>
                <ul className="mt-1 space-y-1">{view.overview.fidelity.not_rendered.map((item) => <li key={item}>• {item}</li>)}</ul>
              </div>
            </div>
            {notRendered.length > 0 && (
              <p className="mt-2 text-[13px] text-amber-900"><TriangleAlert size={14} className="inline mr-1" />
                Sheet này thực tế có: {notRendered.map(([key, count]) => `${key}×${count}`).join(", ")}
              </p>
            )}
            <p className="eq-muted mt-2">{view.note}</p>
          </details>
        </>
      )}
    </section>
  );
}

function SuccessWorkbookButton({ dirty, busy, onClick }: { dirty: boolean; busy: boolean; onClick: () => void }) {
  return <button type="button" className="eq-wb-save" data-testid="workbook-draft-save" onClick={onClick}
    disabled={!dirty || busy} aria-disabled={!dirty || busy}>
    <Save size={15} /> {busy ? "Đang lưu…" : "Lưu bản sửa riêng"}
  </button>;
}
