// ============================================================================
// Báo Giá — Phase C1, donor Logi-good visual shell.
//
// Quotes are REAL LOG-C12 documents: created through core.quotations via the
// ONE bounded dispatcher (quote_create / quote_edit / quote_transition), RBAC
// sales_write, then read back fresh. Quote ESTIMATE stays distinct from the
// finance ledger — never presented as actual money.
// ============================================================================

import { useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Search, Plus, PenLine, ArrowRight, Calculator, Trash2 } from "lucide-react";
import {
  Field,
  GhostBtn,
  PrimaryBtn,
  SearchPicker,
  SectionTitle,
  SuccessBtn,
  ToneBadge,
  inputCls,
} from "../components/ui";
import { useStore } from "../lib/store";
import { cx, fmtMoney, fmtText } from "../lib/format";
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
  const { quotes, customers, dispatch, toast } = useStore();
  const [q, setQState] = useState(sp.get("q") ?? "");
  const setQ = (v: string) => {
    setQState(v);
    const next = new URLSearchParams(sp);
    if (v) next.set("q", v); else next.delete("q");
    window.history.replaceState(null, "", `?${next.toString()}`);
  };
  const [status, setStatus] = useState("ALL");
  const [creating, setCreating] = useState(false);
  const [editing, setEditing] = useState<Quote | null>(null);
  const [form, setForm] = useState<QuoteForm>(EMPTY_FORM);

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
    setForm({ ...EMPTY_FORM, lines: [{ ...EMPTY_LINE }], fx: { USD: "", CNY: "" }, salesOwner: "Minh Tú" });
    setCreating(true);
  };
  const openEdit = (x: Quote) => {
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
    const serviceLines = buildServiceLines();
    if (serviceLines.length === 0) {
      toast("Thiếu dòng dịch vụ", "Cần ít nhất một dòng dịch vụ báo giá.", "red");
      return;
    }
    // Currencies the lines actually need a quote rate for.
    const neededFx = FX_CODES.filter((code) => serviceLines.some((l) => l.currency === code));
    const missingFx = neededFx.filter((code) => {
      const raw = String(form.fx[code] ?? "").replace(/\s|\./g, "").replace(",", ".");
      const value = Number(raw);
      return !(raw.trim() !== "" && Number.isFinite(value) && value > 0);
    });
    if (missingFx.length > 0) {
      toast("Thiếu tỷ giá báo giá",
        "Cần tỷ giá " + missingFx.map((c) => c + " → VND").join(", ")
        + " cho các dòng ngoại tệ. Hệ thống không tự đặt tỷ giá.", "red");
      return;
    }
    const fx: Record<string, number> = {};
    for (const code of neededFx) {
      const raw = String(form.fx[code]).replace(/\s|\./g, "").replace(",", ".");
      fx[code] = Number(raw);
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
        fx,
      });
      toast("Đã gửi tạo báo giá", "Backend tạo mã Q-… tự động, tính dự toán và audit.", "green");
    }
    setCreating(false);
    setEditing(null);
  };

  const transition = (x: Quote, next: string) => {
    dispatch("quote_transition", { id: x.id, nextStatus: next });
    toast("Đã gửi chuyển trạng thái " + x.id, `→ ${STATUS_LABEL[next] ?? next}. Backend kiểm tra đúng luồng.`, "blue");
  };

  return (
    <div className="space-y-4 max-w-[1300px]">
      <div className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5">
        <SectionTitle
          icon={<Calculator size={18} />}
          title="Báo Giá"
          sub="Báo giá (estimate) là dự toán LOG-C12 — tách bạch với tài chính thực thu/chi. Tìm theo mã · khách · tuyến."
          right={<button onClick={openCreate} className="btn-press touch-target hidden sm:inline-flex items-center gap-1.5 rounded-xl bg-[#0f2a4a] text-white font-bold text-[14.5px] px-4 min-h-[48px]"><Plus size={18} /> Tạo báo giá</button>}
        />
        <div className="flex gap-2">
          <div className="flex items-center flex-1 rounded-xl border-2 border-slate-200 focus-within:border-[#1e5aa8] bg-slate-50 overflow-hidden">
            <Search size={19} className="ml-3.5 text-slate-400 shrink-0" />
            <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Nhập mã (Q-…), khách (An Phát), tuyến…" className="w-full bg-transparent px-3 py-3 text-[15px] outline-none" />
          </div>
        </div>
        <div className="flex gap-2 mt-2.5 overflow-x-auto no-scrollbar pb-1">
          {statuses.map((s) => (
            <button key={s} onClick={() => setStatus(s)} className={cx("touch-target shrink-0 rounded-full border-2 px-4 min-h-[44px] text-[14px] font-bold whitespace-nowrap", status === s ? "border-[#0f2a4a] bg-[#0f2a4a] text-white" : "border-slate-200 bg-white text-slate-600")}>
              {s === "ALL" ? "Tất cả" : STATUS_LABEL[s] ?? s}
            </button>
          ))}
        </div>
        <p className="text-[13.5px] text-slate-500 mt-1.5">Tìm thấy <b className="text-[#0f2a4a]">{list.length} báo giá</b> · Trạng thái do backend quyết định theo luồng chốt khách.</p>
      </div>

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
                <p className="font-extrabold text-[15px] text-amber-900">Tỷ giá báo giá — bắt buộc cho dòng ngoại tệ</p>
                <p className="text-[13px] text-amber-800 mt-0.5">Tổng VND của báo giá được quy đổi theo tỷ giá bạn nhập ở đây. Hệ thống không tự đặt tỷ giá và đây không phải tỷ giá giao dịch thực tế.</p>
                <div className="grid grid-cols-2 gap-2.5 mt-2.5">
                  {neededFxCodes.map((code) => (
                    <Field key={code} label={`Tỷ giá ${code} → VND`} required hint="Số có dấu chấm phân cách hàng nghìn.">
                      <input value={form.fx[code]} onChange={(e) => setFx(code, e.target.value)} inputMode="decimal"
                        placeholder={code === "USD" ? "VD: 25.500" : "VD: 3.650"}
                        className={inputCls(!form.fx[code].trim() ? "missing" : "ok")} />
                    </Field>
                  ))}
                </div>
              </div>
            )}

            {/* LOGI_QUOTE_LINE_NOTE_CLARITY_01 — ONE CARD = ONE SERVICE LINE.
                Every card carries its own visible identity ("Dòng dịch vụ N")
                and its OWN "Ghi chú dòng này" field, rendered inside the same
                card as that line's mã/tên/số lượng/giá vốn/giá bán/thuế/tiền tệ.
                There is no quote-level shared note: the note travels to the
                canonical `service_lines[i].note` of exactly this card. */}
            <div className="mt-4">
              <div className="flex items-center justify-between mb-1">
                <p className="font-extrabold text-[15px] text-[#0f2a4a]">Các dòng dịch vụ</p>
                <button type="button" data-testid="quote-add-line" onClick={addLine} className="btn-press touch-target inline-flex items-center gap-1 rounded-lg border-2 border-slate-200 text-[13px] font-bold px-3 min-h-[40px]"><Plus size={15} /> Thêm dòng</button>
              </div>
              <p className="text-[13px] text-slate-500 mb-2.5">Mỗi dòng dịch vụ có ô ghi chú riêng của chính dòng đó — không có ghi chú dùng chung cho cả báo giá.</p>
              <div className="space-y-2.5">
                {form.lines.map((l, i) => (
                  <fieldset key={i} data-testid={`quote-line-${i + 1}`} className="rounded-xl border-2 border-slate-200 bg-white p-3 focus-within:border-[#1e5aa8]">
                    <legend className="sr-only">Dòng dịch vụ {i + 1}</legend>
                    <div className="flex items-center justify-between gap-2 mb-2">
                      <p data-testid={`quote-line-${i + 1}-title`} className="inline-flex items-center gap-1.5 rounded-full bg-[#0f2a4a] text-white font-extrabold text-[13.5px] px-3 py-1">Dòng dịch vụ {i + 1}</p>
                      {form.lines.length > 1 && (
                        <button type="button" data-testid={`quote-line-${i + 1}-remove`} onClick={() => removeLine(i)} className="btn-press touch-target inline-flex items-center gap-1 text-[13px] font-bold text-red-600 min-h-[36px]"><Trash2 size={14} /> Xóa dòng</button>
                      )}
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                      <Field label="Mã dịch vụ"><input value={l.code} onChange={(e) => setLine(i, "code", e.target.value)} placeholder="DV-VC-TQ" className={inputCls()} /></Field>
                      <Field label="Tên dịch vụ"><input value={l.serviceName} onChange={(e) => setLine(i, "serviceName", e.target.value)} placeholder="Cước xe TQ" className={inputCls()} /></Field>
                      <Field label="ĐVT"><input value={l.unit} onChange={(e) => setLine(i, "unit", e.target.value)} className={inputCls()} /></Field>
                      <Field label="Số lượng"><input value={l.qty} onChange={(e) => setLine(i, "qty", e.target.value)} inputMode="numeric" className={inputCls()} /></Field>
                      <Field label="Giá vốn (unit)"><input value={l.costUnit} onChange={(e) => setLine(i, "costUnit", e.target.value)} inputMode="numeric" className={inputCls()} /></Field>
                      <Field label="Giá bán (unit)"><input value={l.sellUnit} onChange={(e) => setLine(i, "sellUnit", e.target.value)} inputMode="numeric" className={inputCls()} /></Field>
                      <Field label="Thuế %"><input value={l.taxPct} onChange={(e) => setLine(i, "taxPct", e.target.value)} inputMode="numeric" className={inputCls()} /></Field>
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
