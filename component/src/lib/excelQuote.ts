// Transport/form types only. All quote arithmetic lives in core/quotations.py.
export type DraftNumber = number | string | null;
export type OptionKey = "A" | "B";
export interface ExcelGoods {
  id: string;
  description: string;
  model: string;
  material: string;
  length_mm: DraftNumber;
  width_mm: DraftNumber;
  height_mm: DraftNumber;
  qty: DraftNumber;
  unit_price: DraftNumber;
  currency: string;
  line_total?: number | null;
  note: string;
  source_sheet?: string;
  source_row?: number | null;
}
export interface ExcelService {
  id: string;
  service_name: string;
  code?: string;
  unit: string;
  qty: DraftNumber;
  currency: string;
  cost_unit: DraftNumber;
  sell_unit: DraftNumber;
  sell_confirmed: boolean;
  tax_pct: DraftNumber;
  internal_note: string;
  public_note: string;
  cost_source: string;
  valid_until: string;
  validity_status?: string;
  source_warning?: string;
  condition: string;
  rate_snapshot_id?: string;
  rate_row_id?: string;
  sell_total?: number | null;
  tax_total?: number | null;
}
export interface ServiceCalculation {
  selling_price_before_tax_vnd: number | null;
  selling_price_total_vnd: number | null;
  totals_by_currency: Array<{ currency: string; sell_total: number | null; tax_total: number | null; sell_total_with_tax: number | null }>;
}
export interface ExcelQuoteCalculation {
  row_count: number;
  quantity: number | null;
  goods_totals: Array<{ currency: string; amount: number | null }>;
  goods_total_vnd: number | null;
  before_tax_vnd: number | null;
  estimate_vnd: number | null;
  unknown_reasons: string[];
}
/**
 * LOGI_EXCEL_FIDELITY_INLINE_EDIT_V1 — one text region of the customer document.
 *
 * `binding` is present only for a region whose text already owns a canonical
 * quote field (goods name/model/material/note, service name, published note,
 * scope, extra public notes, route/mặt hàng). Editing such a region writes that
 * field. A region without a binding is presentation wording and is stored as a
 * small override next to the quote. Amounts are never regions.
 */
export interface TextRegionBinding { scope: "header" | "goods" | "service" | "option"; field: string; key?: string; index?: number }
export interface CustomerTextRegion {
  id: string;
  kind: "SHORT" | "LONG";
  group: string;
  label: string;
  value: string;
  default: string;
  source: "SOURCE" | "SYSTEM_DEFAULT" | "SALE_EDITED" | "UNKNOWN";
  editable: boolean;
  bound: boolean;
  binding: TextRegionBinding | null;
  /** Legal entity / customer identity: formatting may change, a mismatch is warned. */
  guarded: boolean;
  mismatch: boolean;
  multiline: boolean;
}
export interface CustomerTextMap {
  schema: string;
  regions: CustomerTextRegion[];
  values: Record<string, string>;
  overridden: string[];
  mismatches: string[];
  editable_region_count: number;
  /** Where the customer XLSX prints each published region (Finding 6). */
  export_rules?: Record<string, string | null>;
  /** Published regions with NO XLSX rule. Must stay empty. */
  unmapped?: string[];
}
/** READ-ONLY view of the ORIGINAL uploaded workbook (sheet tabs + one sheet). */
export interface WorkbookSheetInfo {
  name: string; index: number; classification: "CUSTOMER" | "INTERNAL" | "UNCLASSIFIED";
  state: string; row_count: number; column_count: number; merged_count: number;
  not_rendered: Record<string, number>;
}
export interface WorkbookOverview {
  sheet_names: string[];
  sheets: WorkbookSheetInfo[];
  customer_sheet: string;
  fidelity: { supported: string[]; not_rendered: string[]; claim: string };
}
export interface WorkbookCell {
  r: number; c: number;
  value?: string | number | boolean;
  display?: string;
  kind?: "value" | "formula";
  f?: string;
  unknown?: boolean;
  nf?: string;
  font?: { bold?: boolean; italic?: boolean; size?: number; name?: string; color?: string };
  fill?: string;
  border?: string;
  align?: { h?: string; v?: string; wrap?: boolean };
}
export interface WorkbookMerge { min_row: number; min_col: number; max_row: number; max_col: number; ref: string }
export interface WorkbookPage {
  sheet: string; sheet_index: number; classification: string; sheet_state: string;
  row_count: number; column_count: number; read_only: boolean; locked: boolean;
  cells: WorkbookCell[]; merges: WorkbookMerge[];
  column_widths: Record<string, number>; row_heights: Record<string, number>;
  hidden_rows: number[]; hidden_columns: string[]; frozen_panes: string;
  start_row?: number; start_col?: number; end_row?: number; end_col?: number;
  truncated: boolean; limits: { max_rows: number; max_cols: number; max_cells: number; start_row?: number; start_col?: number };
  reason?: string;
}
export interface WorkbookDraftState { saved: boolean; version: number; sha256: string; updated_at?: string }
export interface WorkbookCellEdit { sheet: string; r: number; c: number; type: "text" | "number" | "formula" | "blank"; value: string }
export interface WorkbookView {
  read_only: boolean; sha256: string; file_name?: string;
  overview: WorkbookOverview; page: WorkbookPage | null; draft?: WorkbookDraftState | null; note: string;
  can_download_source?: boolean;
}
export interface ExcelQuoteDraft {
  schema: string;
  /** Presentation-only customer wording, keyed by stable region id. */
  customer_text?: { schema: string; overrides: Record<string, string> };
  goods: ExcelGoods[];
  /** Explicit user choice required for service-only quote drafts. */
  goods_mode?: "GOODS" | "SERVICE_ONLY";
  supplier: string;
  source: { file_name: string; byte_size: number; sha256: string; sheet_names: string[]; goods_sheet: string; parser_version: string; storage_file_id?: string };
  source_warnings: Array<{ id: string; text: string }>;
  source_facts: Record<string, unknown>;
  source_costs: Array<{ label: string; amount: number | null; source_sheet: string; condition: string }>;
  disclosures: Array<{ id: string; text: string; selected: boolean }>;
  additional_public_notes: string;
  active_option: OptionKey;
  options: Record<OptionKey, { scope: string; service_lines: ExcelService[]; calculation?: ServiceCalculation }>;
  shipment: { cbm: DraftNumber; weight_kg: DraftNumber; pol: string; pod: string; pickup: string; delivery: string; load_model: string; equipment: string };
  customs: { confirmed: boolean; basis_vnd: DraftNumber; basis_note: string; duty_pct: DraftNumber; vat_pct: DraftNumber; hs_code: string; duty_vnd?: number | null; vat_vnd?: number | null; total_vnd?: number | null; calculable?: boolean };
  warning_notes: Record<string, { status: string; note: string }>;
  calculation?: ExcelQuoteCalculation;
}
export interface CustomerQuotePreview {
  goods_mode?: "GOODS" | "SERVICE_ONLY";
  /** Assigned when the quote is saved; the paper shows it when present. */
  quote_no?: string;
  customer_name: string;
  goods_description: string;
  incoterm: string;
  transport_mode: string;
  route: string;
  option: OptionKey;
  scope: string;
  shipment: ExcelQuoteDraft["shipment"];
  expected_delivery_date?: string;
  goods: Omit<ExcelGoods, "id" | "source_sheet" | "source_row">[];
  service_lines: Pick<ExcelService, "id" | "service_name" | "unit" | "qty" | "currency" | "sell_unit" | "sell_total" | "tax_pct" | "tax_total" | "public_note" | "condition">[];
  customer_notes: string[];
  goods_calculation: ExcelQuoteCalculation;
  services_calculation: ServiceCalculation;
  customs: { calculable: boolean; basis_vnd: number | null; duty_pct: number | null; vat_pct: number | null; duty_vnd: number | null; vat_vnd: number | null; total_vnd: number | null };
  fx_snapshot: { rates_to_vnd: Record<string, number> };
  /** Resolved customer text map — the SAME map the XLSX exporter reads. */
  text?: CustomerTextMap;
  /** Where each published region is printed in the customer XLSX (Finding 6). */
  export_rules?: Record<string, string | null>;
  /** Published regions with no XLSX rule. Must stay empty. */
  unmapped?: string[];
  /** Ids of the published disclosure lines, so each has its own text region. */
  published_notes?: Array<{ id: string; text: string }>;
}
export const quoteRequestId = () => `excel-quote-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
export const emptyExcelService = (): ExcelService => ({
  id: quoteRequestId(), service_name: "", qty: "1", unit: "Lần", currency: "VND", cost_unit: "", sell_unit: "",
  sell_confirmed: false, tax_pct: "", internal_note: "", public_note: "", cost_source: "Nhập thủ công", valid_until: "", condition: "UNCONFIRMED",
});

/**
 * Merge one explicit workbook mapping into the current Excel quote draft.
 * Mapping ids are stable for a source workbook + sheet + source row, so a
 * repeated/overlapping mapping is an upsert: that row is replaced in place and
 * rows outside the mapped range are retained. Services go into the currently
 * selected option; mapping goods/services for the same source row replaces its
 * prior type. A different workbook is an explicit draft replacement, not a
 * cross-workbook merge with misleading single-source provenance.
 */
export function mergeMappedExcelQuoteDraft(
  current: ExcelQuoteDraft | null | undefined,
  mapped: ExcelQuoteDraft,
): ExcelQuoteDraft {
  const sameSource = !!current?.source?.sha256 && current.source.sha256 === mapped.source.sha256;
  if (!sameSource || !current) return mapped;

  const mappedGoods = mapped.goods || [];
  const mappedServices = mapped.options?.A?.service_lines || [];
  if (!mappedGoods.length && !mappedServices.length) return current;

  const incomingIds = new Set(
    [...mappedGoods, ...mappedServices].map((row) => row.id).filter(Boolean),
  );
  const options = {} as ExcelQuoteDraft["options"];
  const activeOption: OptionKey = current.active_option === "B" ? "B" : "A";
  const upsert = <T extends { id: string }>(existing: T[], incoming: T[]): T[] => {
    const rows = new Map<string, T>();
    existing.forEach((row, index) => rows.set(row.id ? `id:${row.id}` : `existing:${index}`, row));
    incoming.forEach((row, index) => rows.set(row.id ? `id:${row.id}` : `incoming:${index}`, row));
    return [...rows.values()];
  };

  let goods = upsert(current.goods || [], mappedGoods);
  if (mappedServices.length) goods = goods.filter((row) => !incomingIds.has(row.id));
  for (const key of ["A", "B"] as const) {
    const option = current.options?.[key] || { scope: "", service_lines: [] };
    let serviceLines = option.service_lines || [];
    if (mappedGoods.length) serviceLines = serviceLines.filter((line) => !incomingIds.has(line.id));
    if (mappedServices.length && key === activeOption) {
      serviceLines = upsert(serviceLines, mappedServices);
    }
    options[key] = { ...option, service_lines: serviceLines };
  }

  return {
    ...current,
    schema: mapped.schema,
    source: mapped.source,
    goods,
    goods_mode: goods.length ? "GOODS" : "SERVICE_ONLY",
    active_option: activeOption,
    options,
  };
}
