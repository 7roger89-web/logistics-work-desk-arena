// ============================================================================
// Báo Giá — Phase C1, donor Logi-good visual shell.
//
// Quotes are REAL LOG-C12 documents: created through core.quotations via the
// ONE bounded dispatcher (quote_create / quote_edit / quote_transition), RBAC
// sales_write, then read back fresh. Quote ESTIMATE stays distinct from the
// finance ledger — never presented as actual money.
// ============================================================================

import { useEffect, useMemo, useRef, useState, useSyncExternalStore } from "react";
import { useSearchParams } from "react-router-dom";
import { Search, Plus, PenLine, ArrowRight, Calculator, Trash2, FileDown } from "lucide-react";
import {
  CalcInput,
  Field,
  GhostBtn,
  PrimaryBtn,
  SearchPicker,
  SectionTitle,
  SuccessBtn,
  ToneBadge,
  inputCls,
} from "../components/ui";
import QuickQuotePaste from "../components/QuickQuotePaste";
import CostCheck from "../components/CostCheck";
import CostIntelligencePanel from "../components/CostIntelligence";
import ExcelQuoteWorkspace from "../components/ExcelQuoteWorkspace";
import type { ParsedQuote } from "../lib/quoteTextParser";
import type { CostMatch } from "../lib/costHistory";
import { useStore } from "../lib/store";
import { cx, downloadBinaryFile, fmtMoney, fmtText } from "../lib/format";
import { getViewModel, subscribeViewModel } from "../lib/viewmodel";
import type { Quote, QuoteServiceLine } from "../lib/viewmodel";

const STATUS_LABEL: Record<string, string> = {
  DRAFT: "Nháp",
  READY_FOR_REVIEW: "Chờ review",
  SENT: "Đã gửi khách",
  ACCEPTED: "Khách chốt",
  REJECTED: "Từ chối",
  EXPIRED: "Hết hạn",
  READY_TO_CREATE_SHIPMENT: "Sẵn sàng tạo lô",
};

const STATUS_TONE: Record<string, "green" | "amber" | "red" | "blue" | "gray"> = {
  DRAFT: "gray",
  READY_FOR_REVIEW: "blue",
  SENT: "amber",
  ACCEPTED: "green",
  REJECTED: "red",
  EXPIRED: "gray",
  READY_TO_CREATE_SHIPMENT: "green",
};

interface LineForm {
  code: string;
  serviceName: string;
  unit: string;
  qty: string;
  currency: string;
  costUnit: string;
  sellUnit: string;
  taxPct: string;
  /** LOGI_INTERNAL_UX_SIMPLIFY_01 — optional operator note, persisted on the
      canonical service line (`note`) and read back on edit. Never part of
      the price/tax/margin/FX arithmetic. */
  note: string;
}

/**
 * Quote-time FX rates, entered by the operator for THIS quote.
 *
 * NO FAKE FX: the quotation model needs a rate for every non-VND line and
 * refuses without one. The app never supplies a default of its own, so the
 * VND totals shown on the desk are always derived from a rate a human typed.
 */
interface FxForm {
  USD: string;
  CNY: string;
}

const FX_CODES = ["USD", "CNY"] as const;

interface QuoteForm {
  customerId: string;
  salesOwner: string;
  origin: string;
  destination: string;
  route: string;
  incoterm: string;
  transportMode: string;
  goodsDescription: string;
  expectedDeliveryDate: string;
  lines: LineForm[];
  fx: FxForm;
}

const EMPTY_LINE: LineForm = { code: "", serviceName: "", unit: "Lần", qty: "1", currency: "VND", costUnit: "", sellUnit: "", taxPct: "8", note: "" };

/** Card identity the operator reads. Service wording is the quote identity;
 *  an internal code is never shown here. */
function lineTitle(index: number, serviceName: string): string {
  const name = serviceName.trim();
  return name ? `Dòng ${index + 1} · ${name}` : `Dòng ${index + 1}`;
}

const EMPTY_FORM: QuoteForm = {
  customerId: "",
  salesOwner: "",
  origin: "",
  destination: "",
  route: "",
  incoterm: "EXW",
  transportMode: "Road",
  goodsDescription: "",
  expectedDeliveryDate: "",
  lines: [{ ...EMPTY_LINE }],
  fx: { USD: "", CNY: "" },
};

/** Rate text for one currency, or "" when the operator has not entered one. */
const rateText = (value: number | null | undefined): string =>
  value == null ? "" : Number(value).toLocaleString("vi-VN");

/** "Tỷ giá báo giá: CNY 3.650" — the disclosure behind a converted VND total. */
const fxNote = (x: Quote): string => {
  const rates = x.fxRatesToVnd ?? {};
  const parts = (x.fxNeededFor ?? [])
    .filter((code) => rates[code] != null)
    .map((code) => `${code} ${rateText(rates[code])}`);
  return parts.length ? "Tỷ giá báo giá: " + parts.join(" · ") : "";
};

function lineToForm(l: QuoteServiceLine): LineForm {
  return {
    code: l.code,
    serviceName: l.serviceName,
    unit: l.unit,
    qty: l.qty == null ? "" : String(l.qty),
    currency: l.currency,
    costUnit: l.costUnit == null ? "" : String(l.costUnit),
    sellUnit: l.sellUnit == null ? "" : String(l.sellUnit),
    taxPct: l.taxPct == null ? "" : String(l.taxPct),
    note: l.note ?? "",
  };
}

export default function SalesQuotes() {
  // LOGI_FRONTEND_WORKFLOW_OVERHAUL_01 — the global search lands here with
  // ?q=<quote> so the exact quote is already filtered, no second search.
  const [sp] = useSearchParams();
  const { quotes, customers, shipments, dispatch, toast } = useStore();
  const [q, setQState] = useState(sp.get("q") ?? "");
  const setQ = (v: string) => {
    setQState(v);
    const next = new URLSearchParams(sp);
    if (v) next.set("q", v); else next.delete("q");
    window.history.replaceState(null, "", `?${next.toString()}`);
  };
  const [status, setStatus] = useState("ALL");
  // LOGI_QUOTE_COST_WORKFLOW_UX_01 — inner segmented view of the SAME Báo Giá
  // workspace (no new sidebar group, no new route): BÁO GIÁ | CHECK CHI PHÍ.
  const initialWorkspace = sp.get("view");
  const [workspace, setWorkspaceState] = useState<"bao-gia" | "check-chi-phi" | "kho-gia-von">(
    initialWorkspace === "check-chi-phi" || initialWorkspace === "kho-gia-von"
      ? initialWorkspace
      : "bao-gia"
  );
  const setWorkspace = (v: "bao-gia" | "check-chi-phi" | "kho-gia-von") => {
    setWorkspaceState(v);
    const next = new URLSearchParams(window.location.search);
    if (v === "bao-gia") next.delete("view"); else next.set("view", v);
    window.history.replaceState(null, "", `?${next.toString()}`);
  };
  const [creating, setCreating] = useState(false);
  const [excelOpen, setExcelOpen] = useState(false);
  const [excelEditing, setExcelEditing] = useState<Quote | null>(null);
  const [editing, setEditing] = useState<Quote | null>(null);
  const [form, setForm] = useState<QuoteForm>(EMPTY_FORM);
  /**
   * CUSTOMER-FACING general notes ("Nếu có phát sinh về xử lý hàng hóa, sẽ báo
   * ngay tại thời điểm phát sinh."). They are persisted on the canonical quote
   * as `customer_notes`, round trip on reopen, and are the ONLY notes printed
   * in the XLSX "Ghi chú" block — the quote's internal `assumptions` list stays
   * internal.
   */
  const [customerNotes, setCustomerNotes] = useState<string[]>([]);
  const lineSectionRef = useRef<HTMLDivElement | null>(null);
  /** LOGI_QUOTE_COST_WORKFLOW_UX_01 — the ONE in-flight quote export intent. */
  const [exporting, setExporting] = useState<{ id: string; requestId: string } | null>(null);
  const vm = useSyncExternalStore(subscribeViewModel, getViewModel, getViewModel);

  const list = useMemo(
    () =>
      quotes.filter(
        (x) =>
          (status === "ALL" || x.status === status) &&
          (!q || (x.id + x.quoteNo + x.customer + x.salesOwner + x.origin + x.destination).toLowerCase().includes(q.toLowerCase()))
      ),
    [quotes, q, status]
  );
  const statuses = ["ALL", ...Array.from(new Set(quotes.map((x) => x.status)))];
  // Currencies the lines currently being edited need a quote rate for.
  const neededFxCodes = FX_CODES.filter((code) =>
    form.lines.some((l) => (l.currency || "VND").trim().toUpperCase() === code));
  // LOGI_INTERNAL_UX_SIMPLIFY_01 — searchable customer options (name / code /
  // MST); the picked value still binds the exact customerId, never a copy.
  const customerOptions = useMemo(
    () =>
      customers.map((c) => ({
        id: c.id,
        label: `${c.name} (${c.id})`,
        sub: [c.taxCode || c.mst, c.phone].filter(Boolean).join(" · ") || c.id,
      })),
    [customers]
  );
  const pickedCustomer = customers.find((c) => c.id === form.customerId) ?? null;

  const set = (k: keyof Omit<QuoteForm, "lines">, v: string) => setForm((f) => ({ ...f, [k]: v }));
  const setFx = (code: keyof FxForm, v: string) => setForm((f) => ({ ...f, fx: { ...f.fx, [code]: v } }));
  const setLine = (i: number, k: keyof LineForm, v: string) =>
    setForm((f) => ({ ...f, lines: f.lines.map((l, idx) => (idx === i ? { ...l, [k]: v } : l)) }));
  const addLine = () => setForm((f) => ({ ...f, lines: [...f.lines, { ...EMPTY_LINE }] }));
  const removeLine = (i: number) => setForm((f) => ({ ...f, lines: f.lines.length > 1 ? f.lines.filter((_, idx) => idx !== i) : f.lines }));

  const openCreate = () => {
    setCustomerNotes([]);
    setForm({ ...EMPTY_FORM, lines: [{ ...EMPTY_LINE }], fx: { USD: "", CNY: "" }, salesOwner: "Minh Tú" });
    setCreating(true);
  };
  const useCostReference = (match: CostMatch) => {
    const usable = match.lines.filter((line) => line.price != null);
    const lines: LineForm[] = usable.length
      ? usable.map((line) => ({
          code: "",
          serviceName: line.label,
          unit: line.unit || "Lần",
          qty: line.qty == null ? "1" : String(line.qty),
          currency: line.ccy || "VND",
          // Negative input-rate credits/refunds are evidence, not a normal quote
          // cost field. Keep them visible in the note and ask the operator to
          // decide how to apply them instead of writing an invalid negative cost.
          costUnit: line.price != null && line.price >= 0 ? String(line.price) : "",
          sellUnit: "",
          taxPct: "",
          note:
            (line.price != null && line.price < 0
              ? "Credit/refund tham chiếu " + String(line.price) + " " + line.ccy + ". "
              : "") +
            "Nguồn giá vốn: " + match.sourceLabel + " · " + match.referenceId,
        }))
      : [{ ...EMPTY_LINE }];

    setCustomerNotes([]);
    setForm({
      ...EMPTY_FORM,
      salesOwner: "Minh Tú",
      origin: match.origin || "",
      destination: match.destination || "",
      route: [match.origin, match.destination].filter(Boolean).join(" → "),
      incoterm: match.incoterm || "",
      transportMode: match.mode || "Sea",
      lines,
      fx: { USD: "", CNY: "" },
    });
    setEditing(null);
    setWorkspace("bao-gia");
    setCreating(true);
    toast(
      "Đã nạp giá vốn tham chiếu",
      "Các dòng chi phí đã vào bản nháp; Giá bán vẫn để trống để Sale quyết định trước khi lưu.",
      "green"
    );
  };

  const openEdit = (x: Quote) => {
    if (x.excelQuote) { setExcelEditing(x); setExcelOpen(true); return; }
    // Restore what the customer was shown: reopening a saved quote must not
    // silently drop its general notes.
    setCustomerNotes([...(x.customerNotes ?? [])]);
    setForm({
      customerId: x.customerId,
      salesOwner: x.salesOwner,
      origin: x.origin,
      destination: x.destination,
      route: x.route,
      incoterm: x.incoterm,
      transportMode: x.transportMode,
      goodsDescription: x.goodsDescription,
      expectedDeliveryDate: x.expectedDeliveryDate,
      lines: x.serviceLines.length ? x.serviceLines.map(lineToForm) : [{ ...EMPTY_LINE }],
      // Pre-fill with the rates already stored on the quote so an edit keeps
      // (and can correct) the same disclosed rate instead of losing it.
      fx: { USD: rateText(x.fxRatesToVnd?.USD), CNY: rateText(x.fxRatesToVnd?.CNY) },
    });
    setEditing(x);
  };

  const buildServiceLines = () =>
    form.lines
      .filter((l) => l.code.trim() || l.serviceName.trim())
      .map((l) => ({
        code: l.code.trim(),
        serviceName: l.serviceName.trim(),
        unit: l.unit.trim() || "Lần",
        qty: l.qty.trim() === "" ? "" : Number(l.qty),
        currency: l.currency.trim() || "VND",
        costUnit: l.costUnit.trim() === "" ? "" : Number(l.costUnit),
        sellUnit: l.sellUnit.trim() === "" ? "" : Number(l.sellUnit),
        taxPct: l.taxPct.trim() === "" ? "" : Number(l.taxPct),
        note: l.note.trim(),
      }));

  const submit = () => {
    if (!form.customerId) {
      toast("Chưa chọn khách hàng", "Chọn khách hàng trước khi tạo báo giá.", "red");
      return;
    }
    const unnamed = form.lines
      .map((l, idx) => ({ l, idx }))
      .filter(({ l }) => !l.code.trim() && !l.serviceName.trim()
        && (l.sellUnit.trim() || l.costUnit.trim() || l.note.trim()))
      .map(({ idx }) => `Dòng ${idx + 1}: Dịch vụ`);
    if (unnamed.length > 0) {
      toast("Thiếu tên dịch vụ",
        unnamed.slice(0, 4).join(" · ")
        + " — ghi đúng tên dịch vụ khách đang hỏi. Không chọn mã nội bộ.",
        "red");
      return;
    }
    const serviceLines = buildServiceLines();
    if (serviceLines.length === 0) {
      toast("Thiếu dòng dịch vụ", "Cần ít nhất một dòng dịch vụ báo giá.", "red");
      return;
    }
    // UNKNOWN != ZERO, and UNKNOWN != SAVE BLOCKER.
    // Only GIÁ BÁN is genuinely required: it is the number quoted to the
    // customer. Giá vốn and Thuế % are internal facts the Sale often does not
    // have while writing the quote — REPAIR_01 blocked the save on them, which
    // just pushed the operator to type a fake 0. They now stay blank, are sent
    // as UNKNOWN, and every total derived from them is reported as UNKNOWN.
    const gaps: string[] = [];
    form.lines
      .filter((l) => l.code.trim() || l.serviceName.trim())
      .forEach((l, idx) => {
        if (String(l.sellUnit ?? "").trim() === "") gaps.push(`Dòng ${idx + 1}: Giá bán (unit)`);
      });
    if (gaps.length > 0) {
      toast("Thiếu giá bán",
        gaps.slice(0, 4).join(" · ")
        + (gaps.length > 4 ? ` · +${gaps.length - 4} dòng nữa` : "")
        + " — giá bán là con số báo cho khách nên bắt buộc. Giá vốn / thuế có thể để trống nếu chưa biết.",
        "red");
      return;
    }

    // Quote-time FX is OPTIONAL context: without it the quote stays truthful in
    // its own currency and simply has no VND grand total. The system never
    // invents a rate, and never refuses the save for the lack of one.
    const neededFx = FX_CODES.filter((code) => serviceLines.some((l) => l.currency === code));
    const fx: Record<string, number> = {};
    const badFx: string[] = [];
    for (const code of neededFx) {
      const raw = String(form.fx[code] ?? "").replace(/\s|\./g, "").replace(",", ".");
      if (raw.trim() === "") continue; // chưa biết tỷ giá — bỏ qua, không quy đổi
      const value = Number(raw);
      if (!Number.isFinite(value) || value <= 0) { badFx.push(code); continue; }
      fx[code] = value;
    }
    if (badFx.length > 0) {
      toast("Tỷ giá không hợp lệ",
        "Tỷ giá " + badFx.map((c) => c + " → VND").join(", ")
        + " phải là số lớn hơn 0. Để trống nếu chưa biết.", "red");
      return;
    }
    if (editing) {
      dispatch("quote_edit", {
        id: editing.id,
        sales_owner: form.salesOwner.trim(),
        origin: form.origin.trim(),
        destination: form.destination.trim(),
        route: form.route.trim(),
        incoterm: form.incoterm.trim(),
        goods_description: form.goodsDescription.trim(),
        expected_delivery_date: form.expectedDeliveryDate.trim(),
        serviceLines,
        customerNotes,
        fx,
      });
      toast("Đã gửi cập nhật " + editing.id, "Backend tính lại giá bán + audit.", "green");
    } else {
      dispatch("quote_create", {
        customerId: form.customerId,
        salesOwner: form.salesOwner.trim(),
        origin: form.origin.trim(),
        destination: form.destination.trim(),
        route: form.route.trim(),
        incoterm: form.incoterm.trim(),
        transportMode: form.transportMode.trim(),
        goodsDescription: form.goodsDescription.trim(),
        expectedDeliveryDate: form.expectedDeliveryDate.trim(),
        serviceLines,
        customerNotes,
        fx,
      });
      toast("Đã gửi tạo báo giá", "Backend tạo mã Q-… tự động, tính dự toán và audit.", "green");
    }
    setCreating(false);
    setEditing(null);
  };

  /**
   * LOGI_QUOTE_COST_WORKFLOW_UX_01 — APPLY the reviewed paste into the form.
   *
   * This runs ONLY from the explicit "ÁP DỤNG VÀO BÁO GIÁ" click. It fills the
   * existing per-line cards (PR #91 ownership untouched: each parsed note goes
   * to ITS OWN line's `note`). It invents nothing: qty stays 1, VAT/giá vốn
   * stay EMPTY unless the operator types them, and no FX is assumed.
   */
  const applyParsedQuote = (parsed: ParsedQuote) => {
    const lines: LineForm[] = parsed.lines.map((l) => {
      const notes = [l.note].filter(Boolean);
      if (l.condition === "IF_APPLICABLE" && !/nếu có|phát sinh/i.test(l.note)) {
        notes.unshift("Có thể phát sinh (nếu có)");
      }
      return {
        code: "",
        serviceName: l.name,
        unit: l.unit || "Lần",
        qty: "1",
        currency: l.currency || "VND",
        // UNKNOWN != ZERO — the paste states a selling price only.
        costUnit: "",
        sellUnit: l.sell == null ? "" : String(l.sell),
        taxPct: "",
        note: notes.join(" · "),
      };
    });
    setForm((f) => ({
      ...f,
      incoterm: parsed.incoterm || f.incoterm,
      origin: parsed.origin || f.origin,
      destination: parsed.destination || f.destination,
      lines: lines.length ? lines : f.lines,
    }));
    setCustomerNotes((prev) => [...prev, ...parsed.assumptions.filter((a) => !prev.includes(a))]);
    toast(
      "Đã áp dụng bản dán",
      `${lines.length} dòng dịch vụ đã điền vào form — kiểm tra và sửa trước khi lưu.`,
      "green"
    );
    // The modal is taller than the viewport. Land on the line list so the
    // operator sees the count and the named cards instead of the fields above.
    if (typeof requestAnimationFrame === "function") {
      requestAnimationFrame(() => {
        lineSectionRef.current?.scrollIntoView({ block: "start" });
      });
    }
  };

  /**
   * Ask the backend for the customer quotation XLSX of ONE quote.
   *
   * READ-ONLY: the server re-reads the canonical quote and renders it with the
   * EXISTING core.excel_utils.generate_quote_excel. The browser only saves the
   * bytes the backend returned — it builds no workbook of its own.
   */
  const exportQuote = (x: Quote) => {
    if (exporting) return;
    const requestId = `quote-xlsx-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
    const sent = dispatch("quote_export_xlsx", { id: x.id, requestId });
    if (!sent) { toast("Không gửi được", "Component chưa kết nối backend.", "red"); return; }
    setExporting({ id: x.id, requestId });
    toast("Đang tạo file báo giá " + x.id, "Backend dựng file XLSX rồi trả về để tải.", "blue");
  };

  // The authoritative outcome arrives on the SAME lastWrites channel every
  // other download uses; transport success alone is never treated as a file.
  useEffect(() => {
    if (!exporting || !vm) return;
    const outcome = (vm.lastWrites ?? []).find(
      (w) => w.event === "quote_export_xlsx" && w.requestId === exporting.requestId
    );
    if (!outcome) return;
    setExporting(null);
    if (!outcome.ok) {
      toast("Không xuất được báo giá", String(outcome.error || "Backend từ chối."), "red");
      return;
    }
    const doc = outcome.document as { fileName?: string; mime?: string; downloadBase64?: string } | undefined;
    if (!doc?.downloadBase64) {
      toast("Chưa có file", "Backend báo thành công nhưng không kèm dữ liệu file.", "red");
      return;
    }
    downloadBinaryFile(
      doc.fileName || `BAOGIA_${exporting.id}.xlsx`,
      doc.downloadBase64,
      doc.mime || "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    );
    toast("Đã tải báo giá " + exporting.id, "File do backend dựng từ dữ liệu báo giá hiện tại.", "green");
  }, [vm, exporting, toast]);

  const transition = (x: Quote, next: string) => {
    dispatch("quote_transition", { id: x.id, nextStatus: next });
    toast("Đã gửi chuyển trạng thái " + x.id, `→ ${STATUS_LABEL[next] ?? next}. Backend kiểm tra đúng luồng.`, "blue");
  };

  if (excelOpen) return <ExcelQuoteWorkspace initialQuote={excelEditing} onClose={() => { setExcelOpen(false); setExcelEditing(null); }} />;

  return (
    <div className="space-y-4 max-w-[1300px]">
      {workspace === "bao-gia" && <section className="rounded-2xl border border-blue-200 bg-blue-50 p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div><h2 className="font-extrabold text-[17px] text-[#0f2a4a]">Báo giá từ Excel khách gửi</h2><p className="text-[13px] text-slate-600 mt-1">1. Xem lại hàng hóa → 2. Tính giá nội bộ → 3. Chọn nội dung gửi khách</p></div>
        <PrimaryBtn testId="quote-excel-open" onClick={() => { setExcelEditing(null); setExcelOpen(true); }}>Nhập Excel khách gửi</PrimaryBtn>
      </section>}
      <div className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5">
        <SectionTitle
          icon={<Calculator size={18} />}
          title="Báo Giá"
          sub="Báo giá (estimate) là dự toán LOG-C12 — tách bạch với tài chính thực thu/chi. Tìm theo mã · khách · tuyến."
          right={<button onClick={openCreate} className="btn-press touch-target hidden sm:inline-flex items-center gap-1.5 rounded-xl bg-[#0f2a4a] text-white font-bold text-[14.5px] px-4 min-h-[48px]"><Plus size={18} /> Tạo báo giá</button>}
        />
        {/* LOGI_QUOTE_COST_WORKFLOW_UX_01 — inner segmented view: the cost check
            lives INSIDE the Báo Giá workspace, not in a new sidebar group. */}
        <div className="flex gap-2 mb-3" role="tablist" aria-label="Khu làm việc báo giá" data-testid="quote-workspace-tabs">
          {([
            { id: "bao-gia", label: "BÁO GIÁ" },
            { id: "check-chi-phi", label: "CHECK CHI PHÍ" },
            { id: "kho-gia-von", label: "KHO GIÁ VỐN" },
          ] as const).map((t) => (
            <button
              key={t.id}
              role="tab"
              aria-selected={workspace === t.id}
              onClick={() => setWorkspace(t.id)}
              data-testid={`quote-workspace-${t.id}`}
              className={cx(
                "touch-target shrink-0 rounded-xl border-2 px-4 min-h-[48px] text-[14.5px] font-extrabold",
                workspace === t.id ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 bg-white text-slate-600"
              )}
            >
              {t.label}
            </button>
          ))}
        </div>
        {workspace === "bao-gia" && (
          <button type="button" onClick={openCreate} className="btn-press touch-target sm:hidden mb-3 inline-flex w-full items-center justify-center gap-1.5 rounded-xl bg-[#0f2a4a] text-white font-bold text-[15px] min-h-[48px]"><Plus size={18} /> Tạo báo giá</button>
        )}
        {workspace === "bao-gia" && (
        <div className="flex gap-2">
          <div className="flex items-center flex-1 rounded-xl border-2 border-slate-200 focus-within:border-[#1e5aa8] bg-slate-50 overflow-hidden">
            <Search size={19} className="ml-3.5 text-slate-400 shrink-0" />
            <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Nhập mã (Q-…), khách (An Phát), tuyến…" className="w-full bg-transparent px-3 py-3 text-[15px] outline-none" />
          </div>
        </div>
        )}
        {workspace === "bao-gia" && (
        <div className="flex gap-2 mt-2.5 overflow-x-auto no-scrollbar pb-1">
          {statuses.map((s) => (
            <button key={s} onClick={() => setStatus(s)} className={cx("touch-target shrink-0 rounded-full border-2 px-4 min-h-[44px] text-[14px] font-bold whitespace-nowrap", status === s ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 bg-white text-slate-600")}>
              {s === "ALL" ? "Tất cả" : STATUS_LABEL[s] ?? s}
            </button>
          ))}
        </div>
        )}
        {workspace === "bao-gia" && (
          <p className="text-[13.5px] text-slate-500 mt-1.5">Tìm thấy <b className="text-[#0f2a4a]">{list.length} báo giá</b> · Trạng thái do backend quyết định theo luồng chốt khách.</p>
        )}
        {workspace === "check-chi-phi" && (
          <p className="text-[13.5px] text-slate-500">Tra chi phí tương đồng từ dữ liệu Trường Thành: ưu tiên <b>thực tế đã chạy</b>, sau đó giá đầu vào supplier/carrier, rồi mới tới báo giá dự kiến.</p>
        )}
        {workspace === "kho-gia-von" && (
          <p className="text-[13.5px] text-slate-500">Nuôi bộ nhớ giá vốn: dán bảng giá mới, sửa chỗ chưa chắc, lưu lịch sử và tự quản mã/alias ngay trong app.</p>
        )}
      </div>

      {workspace === "check-chi-phi" && <CostCheck shipments={shipments} onUseMatch={useCostReference} />}
      {workspace === "kho-gia-von" && <CostIntelligencePanel />}

      {workspace === "bao-gia" && (
      <>

      <div className="hidden md:block rounded-2xl bg-white border border-slate-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="tbl w-full text-[14px] min-w-[960px]">
            <thead>
              <tr><th>Mã báo giá</th><th>Khách hàng</th><th>Tuyến</th><th>Sale</th><th>Tổng (VND)</th><th>Trạng thái</th><th>Hành động</th></tr>
            </thead>
            <tbody>
              {list.map((x) => (
                <tr key={x.id} className="hover:bg-slate-50">
                  <td><span className="font-extrabold text-[#1e5aa8] text-[15px]">{x.id}</span><span className="block text-[12px] text-slate-400">{x.quoteNo}</span></td>
                  <td className="font-semibold max-w-[180px]">{x.customer}</td>
                  <td className="max-w-[220px] text-[13px] text-slate-600">{fmtText(x.origin)} → {fmtText(x.destination)}</td>
                  <td>{fmtText(x.salesOwner)}</td>
                  <td className="font-bold">{fmtMoney(x.sellingPriceTotalVnd ?? x.total, "VND")}
                    {/* A converted total is never shown without the rate behind it. */}
                    {fxNote(x) && <span className="block text-[11.5px] font-semibold text-slate-400">{fxNote(x)}</span>}
                  </td>
                  <td><ToneBadge tone={STATUS_TONE[x.status] ?? "gray"} size="sm">{x.statusLabel || x.status}</ToneBadge></td>
                  <td>
                    <div className="flex flex-wrap gap-1.5">
                      {x.allowedTransitions.map((t) => (
                        <button key={t} onClick={() => transition(x, t)} className="btn-press touch-target inline-flex items-center rounded-lg bg-[#0f2a4a] text-white text-[12.5px] font-bold px-2.5 min-h-[40px]">
                          {STATUS_LABEL[t] ?? t}
                        </button>
                      ))}
                      <button onClick={() => openEdit(x)} className="btn-press touch-target inline-flex items-center gap-1 rounded-lg border-2 border-slate-200 text-[12.5px] font-bold px-2.5 min-h-[40px]"><PenLine size={14} /> Sửa</button>
                      <button onClick={() => exportQuote(x)} disabled={!!exporting} data-testid={`quote-export-${x.id}`} className="btn-press touch-target inline-flex items-center gap-1 rounded-lg border-2 border-slate-200 text-[12.5px] font-bold px-2.5 min-h-[40px] disabled:opacity-50"><FileDown size={14} /> {exporting?.id === x.id ? "ĐANG TẠO…" : "Xuất XLSX"}</button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {list.length === 0 && (
          <div className="p-8 text-center">
            <p className="font-bold text-[16px]">Không tìm thấy báo giá nào</p>
            <p className="text-[14px] text-slate-500 mt-1">Tạo báo giá từ khách hàng đã có.</p>
            <button onClick={openCreate} className="btn-press touch-target mt-3 inline-flex rounded-xl bg-[#0f2a4a] text-white font-bold px-5 min-h-[48px] items-center gap-1.5"><Plus size={17} /> Tạo báo giá</button>
          </div>
        )}
      </div>

      <div className="md:hidden space-y-3">
        {list.map((x) => (
          <div key={x.id} className="rounded-2xl bg-white border border-slate-200 overflow-hidden">
            <div className="p-4">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="font-extrabold text-[16px] text-[#0f2a4a]">{x.id}</span>
                <ToneBadge tone={STATUS_TONE[x.status] ?? "gray"} size="sm">{x.statusLabel || x.status}</ToneBadge>
              </div>
              <p className="font-semibold text-[14.5px] mt-1">{x.customer}</p>
              <p className="text-[13px] text-slate-500">{fmtText(x.origin)} → {fmtText(x.destination)}</p>
              <p className="font-extrabold text-[16px] mt-1.5">{fmtMoney(x.sellingPriceTotalVnd ?? x.total, "VND")} ₫</p>
              {fxNote(x) && <p className="text-[12px] font-semibold text-slate-400 mt-0.5">{fxNote(x)}</p>}
            </div>
            <div className="border-t p-3 flex flex-wrap gap-2">
              {x.allowedTransitions.map((t) => (
                <button key={t} onClick={() => transition(x, t)} className="btn-press touch-target rounded-lg bg-[#0f2a4a] text-white text-[13px] font-bold px-3 min-h-[44px]">{STATUS_LABEL[t] ?? t}</button>
              ))}
              <button onClick={() => openEdit(x)} className="btn-press touch-target inline-flex items-center gap-1 rounded-lg border-2 border-slate-200 text-[13px] font-bold px-3 min-h-[44px]"><PenLine size={14} /> Sửa</button>
              <button onClick={() => exportQuote(x)} disabled={!!exporting} className="btn-press touch-target inline-flex items-center gap-1 rounded-lg border-2 border-slate-200 text-[13px] font-bold px-3 min-h-[44px] disabled:opacity-50"><FileDown size={14} /> {exporting?.id === x.id ? "ĐANG TẠO…" : "Xuất XLSX"}</button>
            </div>
          </div>
        ))}
        {list.length === 0 && (
          <div className="rounded-2xl bg-white border p-8 text-center">
            <p className="font-bold text-[16px]">Không tìm thấy báo giá nào</p>
            <button onClick={openCreate} className="btn-press touch-target mt-3 inline-flex rounded-xl bg-[#0f2a4a] text-white font-bold px-5 min-h-[48px] items-center"><Plus size={17} /> Tạo báo giá</button>
          </div>
        )}
      </div>

      </>
      )}

      {/* MODAL: create / edit */}
      {(creating || editing) && (
        <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center">
          <div className="absolute inset-0 bg-slate-900/55 anim-fade" onClick={() => { setCreating(false); setEditing(null); }} />
          <div className="relative bg-white w-full sm:max-w-[760px] rounded-t-3xl sm:rounded-3xl p-5 pb-8 anim-slide-up max-h-[92vh] overflow-auto" style={{ paddingBottom: "calc(env(safe-area-inset-bottom) + 20px)" }}>
            <h3 className="font-extrabold text-[18px] text-[#0f2a4a]">{editing ? "Sửa báo giá " + editing.id : "Tạo báo giá mới"}</h3>
            <p className="text-[13.5px] text-slate-500">Dự toán chi phí & giá bán — đi qua backend LOG-C12 (tính toán + audit), không ghi sổ tài chính.</p>
            <div className="grid sm:grid-cols-2 gap-3 mt-4">
              {/* LOGI_INTERNAL_UX_SIMPLIFY_01 — the create-quote customer
                  control is the existing searchable SearchPicker (a native
                  select only jumped by first letter). On edit the customer
                  stays read-only: quote_edit has no customer-change writer. */}
              {editing ? (
                <Field label="Khách hàng">
                  <input
                    value={pickedCustomer ? `${pickedCustomer.name} (${pickedCustomer.id})` : form.customerId}
                    disabled
                    aria-label="Khách hàng của báo giá (không đổi khi sửa)"
                    className={inputCls()}
                  />
                </Field>
              ) : (
                <SearchPicker
                  label="Khách hàng"
                  testId="quote-customer-picker"
                  required
                  options={customerOptions}
                  selectedId={form.customerId}
                  selectedLabel={pickedCustomer ? `${pickedCustomer.name} (${pickedCustomer.id})` : ""}
                  placeholder="Gõ tên, mã khách hoặc MST để tìm…"
                  emptyHint="Chưa có khách hàng nào — tạo mới ở mục Khách Hàng trước."
                  onSelect={(id) => set("customerId", id)}
                />
              )}
              <Field label="Sale phụ trách"><input value={form.salesOwner} onChange={(e) => set("salesOwner", e.target.value)} className={inputCls()} /></Field>
              <Field label="Nơi lấy (origin)"><input value={form.origin} onChange={(e) => set("origin", e.target.value)} placeholder="VD: Bằng Tường (Quảng Tây)" className={inputCls()} /></Field>
              <Field label="Nơi giao (destination)"><input value={form.destination} onChange={(e) => set("destination", e.target.value)} placeholder="VD: KCN Quế Võ, Bắc Ninh" className={inputCls()} /></Field>
              <Field label="Tuyến / cửa khẩu"><input value={form.route} onChange={(e) => set("route", e.target.value)} placeholder="VD: Hữu Nghị (Lạng Sơn)" className={inputCls()} /></Field>
              <Field label="Incoterm"><input value={form.incoterm} onChange={(e) => set("incoterm", e.target.value)} className={inputCls()} /></Field>
              <Field label="Phương thức"><input value={form.transportMode} onChange={(e) => set("transportMode", e.target.value)} className={inputCls()} /></Field>
              <Field label="Ngày giao dự kiến"><input value={form.expectedDeliveryDate} onChange={(e) => set("expectedDeliveryDate", e.target.value)} placeholder="VD: 2026-09-20" className={inputCls()} /></Field>
            </div>
            <Field label="Mô tả hàng hóa"><input value={form.goodsDescription} onChange={(e) => set("goodsDescription", e.target.value)} placeholder="VD: Linh kiện điện tử" className={cx(inputCls(), "mt-3")} /></Field>

            {neededFxCodes.length > 0 && (
              <div className="mt-4 rounded-xl border-2 border-amber-300 bg-amber-50/70 p-3.5">
                <p className="font-extrabold text-[15px] text-amber-900">Tỷ giá quy đổi VND (nếu muốn tính tổng VND)</p>
                <p className="text-[13px] text-amber-800 mt-0.5">Không bắt buộc. Để trống vẫn lưu được — báo giá giữ nguyên số tiền theo từng loại tiền, chỉ là chưa có tổng VND. Hệ thống không tự đặt tỷ giá và đây không phải tỷ giá giao dịch thực tế.</p>
                <div className="grid grid-cols-2 gap-2.5 mt-2.5">
                  {neededFxCodes.map((code) => (
                    <Field key={code} label={`Tỷ giá ${code} → VND (nếu đã biết)`} hint="Số có dấu chấm phân cách hàng nghìn.">
                      <input value={form.fx[code]} onChange={(e) => setFx(code, e.target.value)} inputMode="decimal"
                        placeholder={code === "USD" ? "VD: 25.500" : "VD: 3.650"}
                        className={inputCls(form.fx[code].trim() ? "ok" : undefined)} />
                    </Field>
                  ))}
                </div>
              </div>
            )}

            {/* LOGI_QUOTE_COST_WORKFLOW_UX_01 — DÁN BÁO GIÁ NHANH.
                PASTE → PARSE → REVIEW → (operator may edit) → APPLY. Pasting
                alone mutates nothing; only the apply click fills the cards. */}
            <div className="mt-4">
              <QuickQuotePaste
                testId="quote-paste"
                title="DÁN BÁO GIÁ NHANH"
                hint="Dán báo giá bạn vừa gõ trong chat — hệ thống đọc thử tuyến / Incoterm / dòng dịch vụ / giá / đơn vị / ghi chú điều kiện, bạn xem lại rồi mới áp dụng."
                applyLabel="ÁP DỤNG VÀO BÁO GIÁ"
                onApply={applyParsedQuote}
              />
            </div>

            {customerNotes.length > 0 && (
              <div className="mt-3 rounded-xl border-2 border-slate-200 bg-slate-50 p-3" data-testid="quote-assumptions">
                <p className="font-extrabold text-[14px] text-[#0f2a4a]">Ghi chú chung gửi khách</p>
                <p className="text-[12.5px] text-slate-500">
                  Các câu không có giá — giữ làm điều kiện chung, không tạo dòng dịch vụ giá 0.
                  Được lưu cùng báo giá và in vào mục “Ghi chú” của file gửi khách.
                </p>
                <ul className="mt-1.5 space-y-1">
                  {customerNotes.map((a, i) => (
                    <li key={i} className="flex items-start gap-2" data-testid={`quote-customer-note-${i + 1}`}>
                      <span className="text-[13px] text-slate-700 flex-1">• {a}</span>
                      <button
                        type="button"
                        onClick={() => setCustomerNotes((prev) => prev.filter((_, idx) => idx !== i))}
                        data-testid={`quote-customer-note-${i + 1}-remove`}
                        aria-label={`Bỏ ghi chú ${i + 1}`}
                        className="btn-press shrink-0 rounded-lg border-2 border-slate-200 bg-white px-2 py-0.5 text-[12px] font-bold text-slate-500"
                      >
                        Bỏ
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* LOGI_QUICK_QUOTE_LINE_INTEGRITY_AND_SERVICE_NAME_01
                ONE CARD = ONE SERVICE LINE. The service wording is the identity.
                An internal service code is kept in form state for historical
                quotes and is never a visible quotation field. */}
            <div className="mt-4" ref={lineSectionRef} data-testid="quote-line-section">
              <div className="sticky top-0 z-10 -mx-1 px-1 pt-1 pb-2 bg-white">
                <div className="flex items-center justify-between gap-2 mb-1">
                  <p data-testid="quote-line-count" className="font-extrabold text-[15px] text-[#0f2a4a]">Các dòng dịch vụ · {form.lines.length} dòng</p>
                  <button type="button" data-testid="quote-add-line" onClick={addLine} className="btn-press touch-target inline-flex items-center gap-1 rounded-lg border-2 border-slate-200 text-[13px] font-bold px-3 min-h-[40px]"><Plus size={15} /> Thêm dòng</button>
                </div>
                <p className="text-[13px] text-slate-500">Mỗi dòng dịch vụ có ô ghi chú riêng của chính dòng đó — không có ghi chú dùng chung cho cả báo giá.</p>
                {form.lines.length > 3 && (
                  <p data-testid="quote-line-scroll-hint" className="text-[12.5px] font-semibold text-[#1e5aa8] mt-1">
                    Khung bên dưới cuộn được — đủ {form.lines.length} dòng, kéo để xem dòng 4–{form.lines.length}.
                  </p>
                )}
              </div>
              <div data-testid="quote-lines" className="space-y-2.5 max-h-[min(52vh,520px)] overflow-y-auto overscroll-contain rounded-xl border-2 border-slate-200 p-2">
                {form.lines.map((l, i) => (
                  <fieldset key={i} data-testid={`quote-line-${i + 1}`} className="rounded-xl border-2 border-slate-200 bg-white p-3 focus-within:border-[#1e5aa8]">
                    <legend className="sr-only">{lineTitle(i, l.serviceName)}</legend>
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <p data-testid={`quote-line-${i + 1}-title`} className="rounded-xl bg-[#0f2a4a] text-white font-extrabold text-[13.5px] leading-snug px-3 py-1">{lineTitle(i, l.serviceName)}</p>
                      {form.lines.length > 1 && (
                        <button type="button" data-testid={`quote-line-${i + 1}-remove`} onClick={() => removeLine(i)} className="btn-press touch-target inline-flex items-center gap-1 text-[13px] font-bold text-red-600 min-h-[36px] shrink-0"><Trash2 size={14} /> Xóa dòng</button>
                      )}
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                      <div className="col-span-2 md:col-span-4">
                        <Field label="Dịch vụ">
                          <input
                            data-testid={`quote-line-${i + 1}-service`}
                            value={l.serviceName}
                            onChange={(e) => setLine(i, "serviceName", e.target.value)}
                            placeholder="VD: Cước biển"
                            aria-label={`Dịch vụ dòng ${i + 1}`}
                            className={inputCls()}
                          />
                        </Field>
                      </div>
                      <Field label="ĐVT"><input value={l.unit} onChange={(e) => setLine(i, "unit", e.target.value)} className={inputCls()} /></Field>
                      {/* LOGI_QUOTE_COST_WORKFLOW_UX_01 — these accept a small
                          Excel-like expression (370*8, =SUM(370,80), 9.5tr*2)
                          evaluated SAFELY on Enter/blur; persistence always
                          receives a plain number. */}
                      <Field label="Số lượng"><CalcInput value={l.qty} onChange={(v) => setLine(i, "qty", v)} testId={`quote-line-${i + 1}-qty`} ariaLabel={`Số lượng dòng ${i + 1}`} /></Field>
                      <Field label="Giá vốn (nếu đã biết)"><CalcInput value={l.costUnit} onChange={(v) => setLine(i, "costUnit", v)} testId={`quote-line-${i + 1}-cost`} ariaLabel={`Giá vốn dòng ${i + 1}`} /></Field>
                      <Field label="Giá bán (unit)" required><CalcInput value={l.sellUnit} onChange={(v) => setLine(i, "sellUnit", v)} testId={`quote-line-${i + 1}-sell`} ariaLabel={`Giá bán dòng ${i + 1}`} /></Field>
                      <Field label="Thuế % (nếu đã biết)"><CalcInput value={l.taxPct} onChange={(v) => setLine(i, "taxPct", v)} testId={`quote-line-${i + 1}-tax`} ariaLabel={`Thuế phần trăm dòng ${i + 1}`} /></Field>
                      <Field label="Tiền tệ"><select value={l.currency} onChange={(e) => setLine(i, "currency", e.target.value)} className={inputCls()}><option>VND</option><option>USD</option><option>CNY</option></select></Field>
                    </div>
                    <div data-testid={`quote-line-${i + 1}-note-block`} className="mt-2.5 rounded-lg border border-slate-200 bg-slate-50 p-2.5">
                      <Field label="Ghi chú dòng này" hint={`Chỉ áp dụng cho dòng dịch vụ ${i + 1}.`}>
                        <input
                          data-testid={`quote-line-${i + 1}-note`}
                          value={l.note}
                          onChange={(e) => setLine(i, "note", e.target.value)}
                          placeholder="Không bắt buộc — VD: Giá đã gồm bốc xếp"
                          className={inputCls()}
                        />
                      </Field>
                    </div>
                  </fieldset>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2.5 mt-5">
              <GhostBtn onClick={() => { setCreating(false); setEditing(null); }}>Hủy</GhostBtn>
              <SuccessBtn onClick={submit}>💾 {editing ? "LƯU BÁO GIÁ" : "TẠO BÁO GIÁ"}</SuccessBtn>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
