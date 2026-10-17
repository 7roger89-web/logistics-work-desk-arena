import { useEffect, useMemo, useState } from "react";
import { FileSpreadsheet, LockKeyhole, RefreshCw, TriangleAlert } from "lucide-react";
import { GhostBtn, PrimaryBtn, ToneBadge } from "./ui";
import { useStore } from "../lib/store";
import { getViewModel, subscribeViewModel } from "../lib/viewmodel";
import { useSyncExternalStore } from "react";
import { cx } from "../lib/format";
import type { WorkbookCell, WorkbookPage, WorkbookView } from "../lib/excelQuote";
import type { LogiEventName } from "../lib/dispatcher";
import "./excelQuote.css";

/**
 * BẢN XEM WORKBOOK GỐC — READ-ONLY.
 *
 * Requirement A: after a .xlsx upload the employee must be able to read the
 * workbook in its ORIGINAL shape — the real sheet names, in the real order, with
 * cells where they really are, merged cells, column widths, row heights, fonts,
 * fills, borders, alignment and number formats — instead of a parser summary.
 *
 * The bytes are the ones already stored in the existing GridFS attachment store;
 * this component only asks Python for one sheet at a time. It cannot write, it
 * cannot become an export of the source file, and it never replaces Bước 1/2
 * business tables. A sheet whose content is internal cost data stays locked
 * unless the server grants it, and the response always lists what is NOT
 * rendered, so nobody has to trust a "looks like Excel" claim.
 */
const CLASS_LABEL: Record<string, string> = {
  CUSTOMER: "Sheet khách",
  INTERNAL: "Sheet nội bộ",
  UNCLASSIFIED: "Chưa phân loại",
};

function cellStyle(cell: WorkbookCell): React.CSSProperties {
  const style: React.CSSProperties = {};
  if (cell.font?.bold) style.fontWeight = 700;
  if (cell.font?.italic) style.fontStyle = "italic";
  if (cell.font?.size) style.fontSize = `${Math.min(20, Math.max(9, cell.font.size))}px`;
  if (cell.font?.color) style.color = cell.font.color;
  if (cell.fill) style.background = cell.fill;
  if (cell.align?.h === "center") style.textAlign = "center";
  if (cell.align?.h === "right") style.textAlign = "right";
  if (cell.align?.v === "top") style.verticalAlign = "top";
  if (cell.align?.v === "center") style.verticalAlign = "middle";
  if (cell.align?.wrap) style.whiteSpace = "pre-wrap";
  if (cell.border) {
    const sides = cell.border.split(",");
    const width = (side: string) => (sides.some((s) => s.startsWith(side)) ? "1px solid #94a3b8" : undefined);
    style.borderTop = width("t");
    style.borderBottom = width("b");
    style.borderLeft = width("l");
    style.borderRight = width("r");
  }
  return style;
}

function cellText(cell: WorkbookCell | undefined): { text: string; badge: string } {
  if (!cell) return { text: "", badge: "" };
  if (cell.kind === "formula") {
    if (cell.unknown || cell.value === "" || cell.value === undefined) {
      // A formula the file never cached is UNKNOWN — never silently 0.
      return { text: `${cell.f} → chưa có giá trị cache`, badge: "UNKNOWN" };
    }
    return { text: String(cell.display ?? cell.value), badge: "F" };
  }
  if (cell.value === undefined || cell.value === "") return { text: "", badge: "" };
  return { text: String(cell.display ?? cell.value), badge: cell.nf ? "N" : "" };
}

function SheetGrid({ page }: { page: WorkbookPage }) {
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
    const maxRow = Math.min(page.row_count || 1, page.limits.max_rows);
    const maxCol = Math.min(page.column_count || 1, page.limits.max_cols);
    return { anchors, covered, rows: Array.from({ length: Math.max(1, maxRow) }, (_, i) => i + 1),
      cols: Array.from({ length: Math.max(1, maxCol) }, (_, i) => i + 1) };
  }, [page]);
  return (
    <div className="eq-wb-scroll" data-testid="workbook-grid" data-sheet={page.sheet}>
      <table className="eq-wb-table">
        <colgroup>
          <col style={{ width: 44 }} />
          {cols.map((column) => (
            <col key={column} style={{ width: `${Math.min(320, Math.max(58, (page.column_widths[String.fromCharCode(64 + column)] || 14) * 7))}px` }} />
          ))}
        </colgroup>
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
                const { text, badge } = cellText(cell);
                return (
                  <td key={column} style={cellStyle(cell || { r: row, c: column })}
                    rowSpan={anchor?.rs} colSpan={anchor?.cs}
                    data-testid={`workbook-cell-${key}`}
                    data-formula={cell?.kind === "formula" ? "true" : undefined}
                    data-unknown={cell?.unknown ? "true" : undefined}
                    title={[cell?.f, cell?.nf].filter(Boolean).join(" · ") || undefined}
                    className={cx(cell?.unknown && "eq-wb-unknown")}>
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

export default function ExcelSourceWorkbook({ quoteId, customerId, source, onRequestOpen }: {
  quoteId?: string;
  customerId: string;
  source?: { file_name: string; sha256: string; sheet_names: string[]; storage_file_id?: string };
  onRequestOpen?: () => void;
}) {
  const { dispatch } = useStore();
  const vm = useSyncExternalStore(subscribeViewModel, getViewModel, getViewModel);
  const [open, setOpen] = useState(false);
  const [requestId, setRequestId] = useState("");
  const [sheet, setSheet] = useState("");
  const [view, setView] = useState<WorkbookView | null>(null);
  const [error, setError] = useState("");

  const request = (nextSheet: string) => {
    if (!quoteId && !source?.storage_file_id) { setError("Chưa có tệp nguồn đã lưu để đối chiếu."); return; }
    const id = `workbook-view-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
    const payload: Record<string, unknown> = quoteId ? { id: quoteId, requestId: id } : { customerId, source, requestId: id };
    if (nextSheet) payload.sheet = nextSheet;
    if (dispatch("quote_source_workbook_view" as LogiEventName, payload)) {
      setRequestId(id);
      setError("");
    } else setError("Chưa kết nối backend; không hiển thị bản xem workbook.");
  };

  useEffect(() => {
    if (!requestId) return;
    const outcome = vm?.lastWrites?.find((write) => write.event === "quote_source_workbook_view" && write.requestId === requestId);
    if (!outcome) return;
    setRequestId("");
    if (!outcome.ok || !outcome.readback) { setView(null); setError(String(outcome.error || "Backend không trả về bản xem workbook.")); return; }
    const readback = outcome.readback as unknown as WorkbookView;
    setView(readback);
    setSheet((current) => current || readback.page?.sheet || readback.overview.customer_sheet || readback.overview.sheet_names[0] || "");
    setError("");
  }, [vm, requestId]);

  useEffect(() => { if (open && !view && !requestId) request(""); }, [open]); // eslint-disable-line react-hooks/exhaustive-deps

  const sheetInfo = view?.overview.sheets.find((item) => item.name === sheet);
  const notRendered = Object.entries({ ...(view?.overview.fidelity ? {} : {}), ...(sheetInfo?.not_rendered || {}) });

  if (!open) {
    return (
      <div className="mt-3 rounded-xl border border-slate-200 bg-slate-50 p-3" data-testid="excel-source-workbook-entry">
        <p className="text-[13px] text-slate-600">
          Bản xem workbook gốc: đúng tên sheet, thứ tự sheet, ô gộp, định dạng và công thức nguồn của tệp đã tải lên. Chỉ để đối chiếu.
        </p>
        <PrimaryBtn className="mt-2" testId="excel-source-workbook-open"
          disabled={!quoteId && !source?.storage_file_id}
          onClick={() => { setOpen(true); onRequestOpen?.(); }}>
          <FileSpreadsheet size={17} /> Mở workbook gốc (chỉ đọc)
        </PrimaryBtn>
      </div>
    );
  }

  return (
    <section className="eq-wb" data-testid="excel-source-workbook" data-readonly="true">
      <header className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <h4 className="eq-title mb-1"><FileSpreadsheet size={17} className="inline mr-2" />Workbook gốc · chỉ đọc</h4>
          <p className="eq-muted">
            {view?.file_name || source?.file_name || "Tệp nguồn"} · SHA256 {(view?.sha256 || source?.sha256 || "").slice(0, 16)}… ·
            {" "}Bản xem KHÔNG tuyên bố giữ nguyên 100% định dạng.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <GhostBtn testId="excel-source-workbook-refresh" disabled={!!requestId} onClick={() => request(sheet)}>
            <RefreshCw size={15} /> {requestId ? "Đang tải…" : "Tải lại sheet"}
          </GhostBtn>
          <GhostBtn testId="excel-source-workbook-close" onClick={() => setOpen(false)}>Đóng</GhostBtn>
        </div>
      </header>
      {error && <p role="alert" className="eq-alert border-red-300 bg-red-50 text-red-900 mt-3">{error}</p>}
      {view && (
        <>
          <div className="eq-wb-tabs" role="tablist" aria-label="Sheet trong workbook gốc">
            {view.overview.sheets.map((item) => (
              <button key={item.name} type="button" role="tab" aria-selected={item.name === sheet}
                data-testid={`workbook-tab-${item.index}`} data-classification={item.classification}
                className={cx("eq-wb-tab", item.name === sheet && "eq-wb-tab-active")}
                onClick={() => { setSheet(item.name); request(item.name); }}>
                <span className="eq-wb-tab-index">{item.index}</span>
                <span className="truncate">{item.name}</span>
                <span className={cx("eq-wb-tab-class", `eq-wb-class-${item.classification.toLowerCase()}`)}>{CLASS_LABEL[item.classification]}</span>
              </button>
            ))}
          </div>
          <p className="eq-muted mt-2" data-testid="workbook-sheet-order">
            Thứ tự sheet trong tệp gốc: {view.overview.sheet_names.join(" → ")}
          </p>
          {view.page?.locked ? (
            <div className="eq-alert border-amber-300 bg-amber-50 text-amber-900 mt-3" data-testid="workbook-locked">
              <LockKeyhole size={16} className="inline mr-2" />{view.page.reason}
              <span className="block mt-1">Sheet vẫn được liệt kê để bạn biết tệp có sheet nội bộ; nội dung không gửi tới trình duyệt.</span>
            </div>
          ) : view.page ? (
            <>
              <div className="flex flex-wrap items-center gap-2 mt-3 text-[13px]">
                <ToneBadge tone={view.page.classification === "CUSTOMER" ? "green" : "amber"}>{CLASS_LABEL[view.page.classification]}</ToneBadge>
                <span>{view.page.row_count} dòng × {view.page.column_count} cột · {view.page.merges.length} ô gộp</span>
                {view.page.sheet_state !== "visible" && <span className="font-semibold text-amber-800">Sheet đang bị ẩn trong tệp gốc</span>}
                {view.page.truncated && <span className="font-semibold text-amber-800">Chỉ hiển thị {view.page.limits.max_cells} ô đầu — phần còn lại chưa render</span>}
              </div>
              <SheetGrid page={view.page} />
            </>
          ) : null}
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
