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
export interface ExcelQuoteDraft {
  schema: string;
  goods: ExcelGoods[];
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
  service_lines: Pick<ExcelService, "service_name" | "unit" | "qty" | "currency" | "sell_unit" | "sell_total" | "tax_pct" | "tax_total" | "public_note" | "condition">[];
  customer_notes: string[];
  goods_calculation: ExcelQuoteCalculation;
  services_calculation: ServiceCalculation;
  customs: { calculable: boolean; basis_vnd: number | null; duty_pct: number | null; vat_pct: number | null; duty_vnd: number | null; vat_vnd: number | null; total_vnd: number | null };
  fx_snapshot: { rates_to_vnd: Record<string, number> };
}
export const quoteRequestId = () => `excel-quote-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
export const emptyExcelService = (): ExcelService => ({
  id: quoteRequestId(), service_name: "", qty: "1", unit: "Lần", currency: "VND", cost_unit: "", sell_unit: "",
  sell_confirmed: false, tax_pct: "", internal_note: "", public_note: "", cost_source: "Nhập thủ công", valid_until: "", condition: "UNCONFIRMED",
});
