import { useMemo, useState } from "react";
import { ArrowRight, ListChecks } from "lucide-react";
import { Field, PrimaryBtn, inputCls } from "./ui";
import type { ExcelGoods, ExcelQuoteDraft, ExcelService, WorkbookCell, WorkbookPage } from "../lib/excelQuote";

// This is an explicit, user-confirmed column map over the bounded visible sheet
// page. It intentionally does not inspect labels or guess whether a number is
// a cost, sale price, quantity or currency.
type Target = "GOODS" | "SERVICE";
type PriceRole = "UNKNOWN" | "SELL" | "COST";
interface MappingForm {
  target: Target;
  priceRole: PriceRole;
  headerRow: string;
  firstRow: string;
  lastRow: string;
  columns: Record<"name" | "model" | "material" | "length" | "width" | "height" | "qty" | "price" | "currency" | "unit" | "note", string>;
  fixedCurrency: string;
  fixedQuantity: string;
}
const EMPTY: MappingForm = {
  target: "SERVICE", priceRole: "UNKNOWN", headerRow: "1", firstRow: "2", lastRow: "",
  columns: { name: "", model: "", material: "", length: "", width: "", height: "", qty: "", price: "", currency: "", unit: "", note: "" },
  fixedCurrency: "", fixedQuantity: "",
};
const excelColumnName = (column: number): string => {
  let value = column;
  let name = "";
  while (value > 0) {
    const rest = (value - 1) % 26;
    name = String.fromCharCode(65 + rest) + name;
    value = Math.floor((value - 1) / 26);
  }
  return name;
};
const allowedCurrency = (value: unknown): string => {
  const code = String(value ?? "").trim().toUpperCase();
  if (["CNY", "RMB"].includes(code)) return "CNY";
  if (code === "USD") return "USD";
  if (code === "VND") return "VND";
  return "";
};
const textValue = (value: unknown): string => value == null ? "" : String(value).trim();

export default function ExcelWorkbookMapping({ page, source, onApply }: {
  page: WorkbookPage;
  source: ExcelQuoteDraft["source"];
  onApply: (draft: ExcelQuoteDraft) => void;
}) {
  const [form, setForm] = useState<MappingForm>(() => ({
    ...EMPTY, headerRow: String(page.start_row || 1), firstRow: String((page.start_row || 1) + 1),
    lastRow: String(page.end_row || Math.min(page.row_count || page.limits.max_rows, page.limits.max_rows)),
  }));
  const [error, setError] = useState("");
  const cells = useMemo(() => new Map(page.cells.map((cell) => [`${cell.r}:${cell.c}`, cell])), [page]);
  const columnCount = Math.min(page.limits.max_cols, 40);
  const columns = useMemo(() => Array.from({ length: columnCount }, (_, i) => (page.start_col || 1) + i), [columnCount, page.start_col]);
  const headerRow = Number(form.headerRow) || 1;
  const columnName = (column: number) => {
    const cell = cells.get(`${headerRow}:${column}`);
    const label = cell?.kind === "formula" ? cell.f : cell?.display ?? cell?.value;
    return `${excelColumnName(column)}${label == null || label === "" ? "" : ` · ${String(label).slice(0, 70)}`}`;
  };
  const getCell = (row: number, field: keyof MappingForm["columns"]): WorkbookCell | undefined => {
    const column = Number(form.columns[field]);
    return column > 0 ? cells.get(`${row}:${column}`) : undefined;
  };
  const rawCell = (row: number, field: keyof MappingForm["columns"]): unknown => {
    const cell = getCell(row, field);
    if (!cell || (cell.kind === "formula" && cell.unknown)) return null;
    return cell.value;
  };
  const update = (change: Partial<MappingForm>) => setForm((old) => ({ ...old, ...change }));
  const selectColumn = (field: keyof MappingForm["columns"], value: string) =>
    update({ columns: { ...form.columns, [field]: value } });

  const apply = () => {
    setError("");
    const minRow = page.start_row || 1;
    const maxRow = page.end_row || (minRow + page.limits.max_rows - 1);
    const first = Number(form.firstRow);
    const last = form.lastRow.trim() ? Number(form.lastRow) : maxRow;
    const header = Number(form.headerRow);
    if (!Number.isInteger(header) || header < minRow || header > maxRow
        || !Number.isInteger(first) || first <= header || first > maxRow
        || !Number.isInteger(last) || last < first || last > maxRow) {
      setError(`Chọn hàng tiêu đề và vùng dữ liệu trong ${minRow}–${maxRow}; dòng dữ liệu bắt đầu sau tiêu đề.`);
      return;
    }
    if (!Number(form.columns.name)) {
      setError("Chọn cột chứa tên hàng hoặc tên dịch vụ.");
      return;
    }
    if (form.target === "SERVICE" && !Number(form.columns.qty) && !form.fixedQuantity.trim()) {
      setError("Dịch vụ cần cột số lượng hoặc số lượng cố định do bạn nhập; không tự mặc định là 1.");
      return;
    }
    if (form.target === "SERVICE" && !Number(form.columns.currency) && !form.fixedCurrency) {
      setError("Chọn cột tiền tệ hoặc xác nhận rõ một loại tiền cho các dòng này.");
      return;
    }
    if (form.target === "SERVICE" && form.fixedQuantity.trim()) {
      const fixed = Number(form.fixedQuantity);
      if (!Number.isFinite(fixed) || fixed <= 0) { setError("Số lượng cố định phải là số dương hợp lệ."); return; }
    }
    const rows = Array.from({ length: last - first + 1 }, (_, i) => first + i);
    const mappedRows = rows.map((row) => ({
      row,
      name: textValue(rawCell(row, "name")),
      model: textValue(rawCell(row, "model")),
      material: textValue(rawCell(row, "material")),
      length: rawCell(row, "length"), width: rawCell(row, "width"), height: rawCell(row, "height"),
      qty: rawCell(row, "qty"), price: rawCell(row, "price"),
      currency: Number(form.columns.currency) ? allowedCurrency(rawCell(row, "currency")) : form.fixedCurrency,
      unit: textValue(rawCell(row, "unit")), note: textValue(rawCell(row, "note")),
    })).filter((row) => row.name);
    if (!mappedRows.length) { setError("Không có dòng tên nào trong vùng chọn. Kiểm tra sheet, hàng bắt đầu và cột tên."); return; }
    if (form.target === "SERVICE" && mappedRows.length > 100) {
      setError("Mỗi phương án tối đa 100 dòng dịch vụ. Thu hẹp vùng dòng trước khi áp dụng.");
      return;
    }
    if (mappedRows.some((row) => !row.currency)) {
      const row = mappedRows.find((item) => !item.currency)?.row;
      setError(`Dòng ${row}: tiền tệ chưa được xác định. Chọn cột tiền tệ hoặc một loại tiền cố định.`);
      return;
    }

    let goods: ExcelGoods[] = [];
    let serviceLines: ExcelService[] = [];
    if (form.target === "GOODS") {
      goods = mappedRows.map((row) => ({
        id: `map-${page.sheet}-${row.row}`, description: row.name, model: row.model, material: row.material,
        length_mm: row.length == null ? null : String(row.length),
        width_mm: row.width == null ? null : String(row.width),
        height_mm: row.height == null ? null : String(row.height),
        qty: row.qty == null ? null : String(row.qty),
        unit_price: row.price == null ? null : String(row.price), currency: row.currency,
        note: row.note, source_sheet: page.sheet, source_row: row.row,
      }));
    } else {
      const fixedQty = form.fixedQuantity.trim();
      const mapped: ExcelService[] = [];
      for (const row of mappedRows) {
        const quantity = row.qty == null || textValue(row.qty) === "" ? fixedQty : String(row.qty);
        if (!quantity || !Number.isFinite(Number(quantity)) || Number(quantity) <= 0) {
          setError(`Dòng ${row.row}: số lượng chưa biết hoặc không hợp lệ. Sửa ô nguồn, ánh xạ cột số lượng hoặc nhập lượng cố định.`);
          return;
        }
        const sourcePrice = row.price == null ? "" : String(row.price);
        const service: ExcelService = {
          id: `map-${page.sheet}-${row.row}`, service_name: row.name, code: "", unit: row.unit,
          qty: quantity, currency: row.currency,
          cost_unit: form.priceRole === "COST" && sourcePrice ? sourcePrice : null,
          sell_unit: form.priceRole === "SELL" && sourcePrice ? sourcePrice : null,
          sell_confirmed: false, tax_pct: null,
          internal_note: row.note,
          public_note: "",
          cost_source: form.priceRole === "COST" ? `${source.file_name} · ${page.sheet} · dòng ${row.row} · giá vốn do Sale chọn` : "Workbook đã chọn · vai trò giá chưa xác nhận",
          valid_until: "", validity_status: "UNKNOWN", source_warning: "",
          condition: "UNCONFIRMED",
        };
        mapped.push(service);
      }
      serviceLines = mapped;
    }

    onApply({
      schema: "luc-giac/1",
      goods_mode: form.target === "GOODS" ? "GOODS" : "SERVICE_ONLY",
      goods, supplier: "",
      source,
      source_warnings: [], source_facts: {}, source_costs: [], disclosures: [],
      additional_public_notes: "", active_option: "A",
      options: { A: { scope: "", service_lines: serviceLines }, B: { scope: "", service_lines: [] } },
      shipment: { cbm: null, weight_kg: null, pol: "", pod: "", pickup: "", delivery: "", load_model: "", equipment: "" },
      customs: { confirmed: false, basis_vnd: null, basis_note: "", duty_pct: null, vat_pct: null, hs_code: "" },
      warning_notes: {},
    });
  };

  const columnPicker = (field: keyof MappingForm["columns"], label: string, optional = true) => (
    <Field key={field} label={label}>
      <select className={inputCls()} data-testid={`excel-map-column-${field}`} value={form.columns[field]} onChange={(event) => selectColumn(field, event.target.value)}>
        <option value="">{optional ? "Không dùng cột này" : "Chọn cột"}</option>
        {columns.map((column) => <option key={column} value={column}>{columnName(column)}</option>)}
      </select>
    </Field>
  );

  return (
    <section className="eq-card" data-testid="excel-workbook-mapping">
      <h3 className="eq-title"><ListChecks size={18} className="inline mr-2" />Chọn dữ liệu để đưa vào báo giá</h3>
      <p className="eq-muted">Không tự nhận diện hay mặc định số lượng, kích thước, tiền tệ hoặc vai trò giá. Chọn sheet/vùng/cột; chỉ dữ liệu bạn áp dụng mới vào báo giá. Ánh xạ dùng bản workbook đã lưu gần nhất.</p>
      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3 mt-3">
        <Field label="Dùng dòng cho">
          <select className={inputCls()} data-testid="excel-map-target" value={form.target} onChange={(event) => update({ target: event.target.value as Target })}>
            <option value="SERVICE">Phí dịch vụ logistics</option><option value="GOODS">Hàng hóa báo khách</option>
          </select>
        </Field>
        {form.target === "SERVICE" && <Field label="Vai trò cột đơn giá">
          <select className={inputCls()} data-testid="excel-map-price-role" value={form.priceRole} onChange={(event) => update({ priceRole: event.target.value as PriceRole })}>
            <option value="UNKNOWN">Chưa xác định · không đưa giá vào tính toán</option>
            <option value="SELL">Giá bán dự kiến cho khách · chưa xác nhận</option>
            <option value="COST">Giá mua / giá vốn tham khảo nội bộ</option>
          </select>
        </Field>}
        <Field label="Hàng tiêu đề"><input className={inputCls()} data-testid="excel-map-header-row" inputMode="numeric" value={form.headerRow} onChange={(event) => update({ headerRow: event.target.value })} /></Field>
        <Field label="Dòng dữ liệu đầu"><input className={inputCls()} data-testid="excel-map-first-row" inputMode="numeric" value={form.firstRow} onChange={(event) => update({ firstRow: event.target.value })} /></Field>
        <Field label="Dòng dữ liệu cuối" hint={`Vùng đang xem tới dòng ${page.end_row || page.limits.max_rows}.`}><input className={inputCls()} data-testid="excel-map-last-row" inputMode="numeric" value={form.lastRow} onChange={(event) => update({ lastRow: event.target.value })} placeholder="Cuối vùng xem" /></Field>
      </div>
      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3 mt-3">
        {columnPicker("name", form.target === "GOODS" ? "Cột tên hàng *" : "Cột tên dịch vụ *", false)}
        {form.target === "GOODS" && <>{columnPicker("model", "Model")}{columnPicker("material", "Vật liệu")}{columnPicker("length", "Dài · mm")}{columnPicker("width", "Rộng · mm")}{columnPicker("height", "Cao · mm")}</>}
        {columnPicker("qty", "Cột số lượng")}
        {columnPicker("price", form.target === "GOODS" ? "Cột đơn giá hàng (giá báo khách)" : "Cột đơn giá nguồn")}
        {columnPicker("currency", "Cột tiền tệ")}
        {form.target === "SERVICE" && columnPicker("unit", "Cột đơn vị tính")}
        {columnPicker("note", form.target === "GOODS" ? "Ghi chú công bố cho khách" : "Ghi chú nội bộ")}
      </div>
      <div className="grid sm:grid-cols-2 gap-3 mt-3">
        {form.target === "SERVICE" && !Number(form.columns.qty) && <Field label="Số lượng cố định do bạn xác nhận" hint="Không nhập thì ánh xạ phải có cột số lượng."><input className={inputCls()} data-testid="excel-map-fixed-quantity" inputMode="decimal" value={form.fixedQuantity} onChange={(event) => update({ fixedQuantity: event.target.value })} placeholder="Chưa xác nhận" /></Field>}
        {!Number(form.columns.currency) && <Field label="Tiền tệ cố định do bạn xác nhận"><select className={inputCls()} data-testid="excel-map-fixed-currency" value={form.fixedCurrency} onChange={(event) => update({ fixedCurrency: event.target.value })}><option value="">Chưa xác định</option><option value="USD">USD</option><option value="CNY">CNY / RMB</option><option value="VND">VND</option></select></Field>}
      </div>
      {form.target === "GOODS" && <p className="eq-alert border-amber-200 bg-amber-50 text-amber-900 mt-3">Chọn “Hàng hóa báo khách” là xác nhận đơn giá được chọn là giá sẽ đưa vào báo giá khách; không chọn nếu cột đó là giá mua/giá vốn.</p>}
      {form.target === "SERVICE" && form.priceRole === "COST" && <p className="eq-alert border-amber-200 bg-amber-50 text-amber-900 mt-3">Giá sẽ chỉ đi vào giá vốn nội bộ; không tạo giá bán và không xuất sang báo giá khách.</p>}
      {error && <p role="alert" className="eq-alert border-red-300 bg-red-50 text-red-900 mt-3">{error}</p>}
      <div className="mt-4 flex flex-wrap items-center gap-3">
        <PrimaryBtn testId="excel-workbook-map-apply" onClick={apply}><ArrowRight size={16} /> Dùng các dòng đã chọn trong bản nháp báo giá</PrimaryBtn>
        <span className="eq-muted">Mọi phép tính tiếp tục chạy ở backend; cần nhập/xác nhận tỷ giá, thuế và giá bán riêng trước khi gửi khách.</span>
      </div>
    </section>
  );
}
