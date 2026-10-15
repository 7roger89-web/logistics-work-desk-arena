// ============================================================================
// DỊCH VỤ & CHI PHÍ THỰC TẾ — practical Finance Actual entry for
// Lô Hàng → Tài chính / Công nợ (LOGI_FINANCE_ACTUAL_ENTRY_PARITY_01).
//
// The previous Logistics app's operational experience on the SAME canonical
// model — no new finance table, ledger, API or service layer:
//
//   read  : views.logi_real_data.finance_projection → shipment.finance.actual
//           (the canonical data["3.4"].details rows, one per service line)
//   pick  : ViewModel.financeServiceCatalog — the ONE catalog
//           core.config.GETFLY_SERVICES_LIST projected read-only by the
//           backend. This file contains no service list of its own.
//   write : ONE typed event `finance_actual_save` → the single Python
//           dispatcher → finance_write RBAC → fresh shipment →
//           apply_financial_snapshot → save_shipment_atomic → audit →
//           fresh readback → forced fresh view-model.
//
// Editing sends the canonical line `id`, so the writer UPDATES that row and
// never appends a duplicate; a new line sends no id and the backend mints the
// canonical one. There is deliberately no delete: a wrong line is corrected by
// editing the same row, so the audit history is never silently destroyed.
//
// UNKNOWN != ZERO: cost, sell price and VAT are required, because a booked
// actual line is a claim about money that really happened. An explicit 0 is a
// valid answer; leaving the box blank is NOT — this form refuses locally and
// the writer refuses again server-side. Nothing is inferred and no FX exists:
// every amount stays in the lot's own currency.
// ============================================================================

import { useEffect, useMemo, useRef, useState } from "react";
import { CircleAlert, PenLine, Plus, Receipt, Save, X } from "lucide-react";
import { Field, GhostBtn, PrimaryBtn, inputCls } from "./ui";
import { cx, fmtCcy, fmtMoney, fmtNum, fmtText, parseAmountVN } from "../lib/format";
import type { LogiEventName } from "../lib/dispatcher";
import type {
  FinanceActualLine,
  FinanceServiceCatalogEntry,
  LastWriteOutcome,
  Shipment,
} from "../lib/viewmodel";

interface Props {
  shipment: Shipment;
  stageContext?: string;
  /** Catalog slice delivered by the backend (never copied into the UI). */
  services: FinanceServiceCatalogEntry[];
  /** The lot's one authoritative currency — amounts are never converted. */
  ccy: string;
  dispatch: (event: LogiEventName, payload: unknown) => boolean;
  toast: (title: string, desc?: string, tone?: "green" | "red" | "amber" | "blue") => void;
  /** Authoritative outcomes of the events the dispatcher handled. */
  lastWrites?: LastWriteOutcome[];
}

/** One line being added (id === "") or edited (id === canonical line id). */
interface LineDraft {
  id: string;
  journeyStage: string;
  code: string;
  name: string;
  unit: string;
  qty: string;
  cost: string;
  price: string;
  vat: string;
  note: string;
}

const BLANK_DRAFT: LineDraft = {
  id: "",
  journeyStage: "",
  code: "",
  name: "",
  unit: "",
  qty: "1",
  cost: "",
  price: "",
  // A NEW line has NO VAT rate until the operator states one. The desk's usual
  // 8% is not a starting value here: booking an actual line is a claim about
  // money that really happened, so UNKNOWN is neither 0 nor 8. Blank stays
  // blank, the form refuses it below, and the writer refuses it again.
  vat: "",
  note: "",
};

/** Prefill the editor from the row the backend actually stores. */
function draftFromLine(line: FinanceActualLine): LineDraft {
  return {
    id: line.id ?? "",
    journeyStage: line.journeyStage ?? "",
    code: line.code ?? "",
    name: line.name || line.label || "",
    unit: line.unit ?? "",
    qty: line.qty == null ? "" : String(line.qty),
    cost: line.cost == null ? "" : String(line.cost),
    price: line.price == null ? "" : String(line.price),
    vat: line.vat == null ? "" : String(line.vat),
    note: line.note ?? "",
  };
}

/** One intent identity: the backend echoes it, so a stale outcome is never re-read. */
const newIntentId = () =>
  `FACTUAL-REQ-${Date.now().toString(36).toUpperCase()}-${Math.random().toString(36).slice(2, 8).toUpperCase()}`;

/** One field cell: inline caption on mobile, shared header on desktop. */
function Cell({ label, className, children }: { label: string; className?: string; children: React.ReactNode }) {
  return (
    <div className={cx("min-w-0", className)}>
      <span className="block md:hidden text-[12px] font-extrabold uppercase tracking-wide text-slate-400">{label}</span>
      {children}
    </div>
  );
}

export default function FinanceActualEntry({ shipment, services, ccy, dispatch, toast, lastWrites, stageContext }: Props) {
  const [showUnassigned, setShowUnassigned] = useState(false);
  const allLines = shipment.finance.actual ?? [];
  const stageIds = new Set(shipment.journey?.nodes.map(n => n.id) ?? []);
  const unassigned = allLines.filter(l => !l.journeyStage || !stageIds.has(l.journeyStage));
  const lines = stageContext ? (showUnassigned ? unassigned : allLines.filter(l => l.journeyStage === stageContext)) : allLines;

  const [draft, setDraft] = useState<LineDraft>(BLANK_DRAFT);
  const [open, setOpen] = useState(false);
  const [localError, setLocalError] = useState("");
  const [backendError, setBackendError] = useState("");
  const [pending, setPending] = useState<{ requestId: string; mode: "new" | "edit" } | null>(null);
  const formRef = useRef<HTMLDivElement | null>(null);

  // Moving to another lot (or another tab of the same lot) never carries an
  // unsaved actual-line draft over.
  useEffect(() => {
    setOpen(false);
    setDraft(BLANK_DRAFT);
    setLocalError("");
    setBackendError("");
    setPending(null);
  }, [shipment.id]);

  const catalogByCode = useMemo(() => {
    const map = new Map<string, FinanceServiceCatalogEntry>();
    for (const entry of services) map.set(entry.code, entry);
    return map;
  }, [services]);

  const groupedServices = useMemo(() => {
    const groups: { group: string; entries: FinanceServiceCatalogEntry[] }[] = [];
    const index = new Map<string, number>();
    for (const entry of services) {
      const group = entry.group || "DỊCH VỤ";
      if (!index.has(group)) {
        index.set(group, groups.length);
        groups.push({ group, entries: [] });
      }
      groups[index.get(group)!].entries.push(entry);
    }
    return groups;
  }, [services]);

  /**
   * A row whose stored name is NOT the catalog name for its code (a legacy or
   * hand-kept service, including rows the reader best-matched to a generic
   * code) keeps its own identity: the editor shows its real name as free text
   * instead of force-matching it to a service that never existed on the row.
   */
  const isLegacyRow = (() => {
    if (!draft.id) return false;
    const entry = catalogByCode.get(draft.code);
    return !entry || entry.name.trim() !== draft.name.trim();
  })();

  const openFor = (line: FinanceActualLine | null) => {
    setDraft(line ? draftFromLine(line) : { ...BLANK_DRAFT, journeyStage: stageContext || "" });
    setLocalError("");
    setBackendError("");
    setPending(null);
    setOpen(true);
    window.setTimeout(() => formRef.current?.scrollIntoView({ behavior: "smooth", block: "center" }), 60);
  };

  const closeForm = () => {
    setOpen(false);
    setDraft(BLANK_DRAFT);
    setLocalError("");
    setBackendError("");
    setPending(null);
  };

  const set = <K extends keyof LineDraft>(key: K, value: LineDraft[K]) => {
    setDraft((d) => ({ ...d, [key]: value }));
    setLocalError("");
  };

  const pickService = (code: string) => {
    const entry = code ? catalogByCode.get(code) : undefined;
    if (!entry) {
      setDraft((d) => ({ ...d, code: "", name: "", unit: "" }));
      setLocalError("");
      return;
    }
    // Mã + Đơn vị come from the catalog; the operator only types the money.
    setDraft((d) => ({ ...d, code: entry.code, name: entry.name, unit: entry.unit || "Lần" }));
    setLocalError("");
  };

  const preview = useMemo(() => {
    const qty = parseAmountVN(draft.qty);
    const price = parseAmountVN(draft.price);
    const cost = parseAmountVN(draft.cost);
    const vat = parseAmountVN(draft.vat);
    const net = qty != null && price != null ? qty * price : null;
    return {
      net,
      withVat: net != null && vat != null ? net * (1 + vat / 100) : null,
      costTotal: qty != null && cost != null ? qty * cost : null,
    };
  }, [draft.qty, draft.price, draft.cost, draft.vat]);

  const save = () => {
    const name = draft.name.trim();
    if (!name) {
      setLocalError("Chọn dịch vụ trong danh mục — dòng thực tế không được để trống tên.");
      return;
    }
    const problems: string[] = [];
    const money: [string, string][] = [["Giá bán", draft.price], ["Giá vốn", draft.cost], ["VAT %", draft.vat]];
    for (const [caption, raw] of money) {
      if (!raw.trim()) problems.push(`${caption} chưa nhập`);
      else if (parseAmountVN(raw) == null) problems.push(`${caption} không phải số`);
    }
    const qtyText = draft.qty.trim();
    const qty = parseAmountVN(qtyText);
    if (qtyText && qty == null) problems.push("Số lượng không phải số");
    else if (qty != null && qty <= 0) problems.push("Số lượng phải lớn hơn 0");
    if (problems.length > 0) {
      setLocalError(
        `${problems.join(" · ")}. Dòng thực tế phải nêu rõ số tiền — 0 là giá trị hợp lệ, để trống thì không.`
      );
      return;
    }
    // A new line must come from the catalog (that is where code + unit come
    // from); an existing line keeps whatever identity it already carries.
    if (!draft.id && !catalogByCode.has(draft.code)) {
      setLocalError("Chọn dịch vụ từ danh mục để lấy mã phí và đơn vị tính.");
      return;
    }

    const requestId = newIntentId();
    const line: Record<string, string> = {
      name,
      code: draft.code,
      unit: draft.unit.trim() || "Lần",
      // A blank quantity travels blank: the writer applies the canonical
      // default of 1, so the UI never books a number of its own.
      qty: qtyText,
      cost: draft.cost.trim(),
      price: draft.price.trim(),
      vat: draft.vat.trim(),
      note: draft.note.trim(),
      journeyStage: draft.journeyStage,
    };
    // EDIT sends the canonical id → the SAME row is updated, never duplicated.
    if (draft.id) line.id = draft.id;

    const sent = dispatch("finance_actual_save", { shipmentId: shipment.id, line, requestId });
    if (!sent) {
      setLocalError("Component chưa kết nối backend — dữ liệu chưa được gửi đi.");
      return;
    }
    setBackendError("");
    setPending({ requestId, mode: draft.id ? "edit" : "new" });
  };

  // The authoritative answer arrives with the next fresh view-model. Success
  // closes the editor because the row itself comes back from the backend
  // readback (no optimistic business truth); a refusal keeps the draft and
  // shows the real reason the writer gave.
  useEffect(() => {
    if (!pending) return;
    const outcome = (lastWrites ?? []).find(
      (w) => w.event === "finance_actual_save" && w.requestId === pending.requestId
    );
    if (!outcome) return;
    if (outcome.ok) {
      const mode = pending.mode;
      closeForm();
      toast(
        mode === "edit" ? "Đã cập nhật dòng thực tế" : "Đã ghi nhận dịch vụ thực tế",
        "Backend lưu vào data['3.4'].details, tính lại phải thu · chi phí · lợi nhuận rồi đọc lại dữ liệu mới.",
        "green"
      );
    } else {
      const message = outcome.error || "Backend từ chối dòng thực tế này.";
      setPending(null);
      setBackendError(message);
      toast("Chưa lưu được dòng thực tế", message, "red");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lastWrites, pending]);

  return (
    <section className="rounded-2xl bg-white border-2 border-emerald-300 p-4 md:p-5" id="finance-actual-lines">
      {stageContext && <div className="mb-3 flex flex-wrap items-center gap-2 text-sm">
        <span>{showUnassigned ? "Chi phí chưa phân công / công đoạn khác" : `Chi phí công đoạn: ${shipment.journey?.nodes.find(n => n.id === stageContext)?.label || stageContext}`}</span>
        <button type="button" onClick={() => setShowUnassigned(v => !v)} className="touch-target rounded-lg border px-3 py-2 font-bold">{showUnassigned ? "Về công đoạn" : `Xem chưa phân công / khác (${unassigned.length})`}</button>
      </div>}
      <div className="flex flex-col sm:flex-row sm:items-start gap-3 mb-1">
        <div className="min-w-0">
          <h3 className="font-extrabold text-[16.5px] md:text-[18px] text-[#0f2a4a] flex items-center gap-2">
            <Receipt size={20} className="text-emerald-600" /> DỊCH VỤ &amp; CHI PHÍ THỰC TẾ
          </h3>
          <p className="text-[13px] text-slate-500 mt-0.5">
            Giá vốn · giá bán · VAT cho từng dịch vụ của lô, tiền {ccy} — không quy đổi. Sai thì sửa đúng dòng đó,
            không xóa lịch sử.
          </p>
        </div>
        <button
          onClick={() => (open && !draft.id ? closeForm() : openFor(null))}
          className="btn-press touch-target sm:ml-auto shrink-0 inline-flex items-center gap-1.5 rounded-xl border-2 border-[#1e5aa8] bg-white text-[#1e5aa8] font-extrabold px-4 min-h-[46px]"
        >
          <Plus size={17} /> THÊM DỊCH VỤ / CHI PHÍ
        </button>
      </div>

      {lines.length === 0 && (
        <div className="mt-3 rounded-xl border-2 border-dashed border-slate-300 p-5 text-center">
          <p className="font-bold text-slate-600 text-[14.5px]">Chưa có dòng dịch vụ thực tế nào cho lô này.</p>
          <p className="text-[13px] text-slate-500 mt-1">
            Bấm “+ THÊM DỊCH VỤ / CHI PHÍ” để ghi nhận. Doanh thu · chi phí · lợi nhuận thực tế đang chưa xác định,
            không phải 0.
          </p>
        </div>
      )}

      {lines.length > 0 && (
        <div className="mt-3 rounded-xl border border-slate-200 overflow-hidden">
          <div className="hidden md:grid md:grid-cols-12 gap-2 px-3 py-2 bg-slate-50 border-b border-slate-200 text-[12px] font-extrabold uppercase tracking-wide text-slate-500">
            <div className="md:col-span-3">Dịch vụ</div>
            <div className="md:col-span-2">Mã</div>
            <div className="md:col-span-1 text-right">SL</div>
            <div className="md:col-span-1">Đơn vị</div>
            <div className="md:col-span-2 text-right">Giá vốn</div>
            <div className="md:col-span-2 text-right">Giá bán</div>
            <div className="md:col-span-1 text-right">VAT</div>
          </div>
          <div className="divide-y divide-slate-100">
            {lines.map((line, index) => {
              const sell = line.qty != null && line.amount != null ? line.qty * line.amount : null;
              return (
                <div key={line.id || `${line.label}-${index}`} className="p-3">
                  <div className="grid grid-cols-2 md:grid-cols-12 gap-x-2 gap-y-1.5 items-baseline">
                    <Cell label="Dịch vụ" className="col-span-2 md:col-span-3">
                      <span className="font-bold text-[14.5px] text-[#0f2a4a] block" title={line.label}>{line.label}</span>
                    </Cell>
                    <Cell label="Mã" className="md:col-span-2">
                      <span className="text-[13px] font-bold text-slate-500">{fmtText(line.code)}</span>
                    </Cell>
                    <Cell label="SL" className="md:col-span-1 text-left md:text-right">
                      <span className="text-[14px] font-semibold">{fmtNum(line.qty)}</span>
                    </Cell>
                    <Cell label="Đơn vị" className="md:col-span-1">
                      <span className="text-[13.5px] text-slate-600">{fmtText(line.unit)}</span>
                    </Cell>
                    <Cell label="Giá vốn" className="md:col-span-2 text-right">
                      <span className="text-[14px] font-semibold text-slate-700">{fmtCcy(line.cost, line.ccy ?? ccy)}</span>
                    </Cell>
                    <Cell label="Giá bán" className="md:col-span-2 text-right">
                      <span className="text-[14.5px] font-extrabold">{fmtCcy(line.amount, line.ccy ?? ccy)}</span>
                    </Cell>
                    <Cell label="VAT" className="md:col-span-1 text-left md:text-right">
                      <span className="text-[13.5px] font-semibold text-slate-600">
                        {line.vat == null ? "—" : `VAT ${fmtNum(line.vat)}%`}
                      </span>
                    </Cell>
                  </div>
                  <div className="mt-1.5 flex flex-wrap items-center gap-2">
                    <span className="text-[12.5px] text-slate-500 flex-1 min-w-[150px]">
                      Ghi chú: {line.note && line.note.trim() ? line.note : "—"}
                      {sell != null ? ` · Thành tiền dòng ${fmtMoney(sell)} ${line.ccy ?? ccy}` : ""}
                    </span>
                    <button
                      onClick={() => openFor(line)}
                      disabled={!line.id}
                      title={line.id
                        ? "Sửa đúng dòng này — dòng cũ được cập nhật tại chỗ, không thêm dòng mới"
                        : "Dòng chưa có mã định danh — chưa sửa được qua màn hình này"}
                      className="btn-press touch-target inline-flex items-center gap-1.5 rounded-lg border-2 border-slate-200 bg-white text-[#1e5aa8] text-[13px] font-bold px-3 min-h-[40px] disabled:opacity-40"
                    >
                      <PenLine size={14} /> SỬA
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {open && (
        <div
          ref={formRef}
          className="mt-3 rounded-xl border-2 border-[#1e5aa8] bg-blue-50/40 p-3.5 md:p-4"
          id="finance-actual-form"
        >
          <div className="flex items-start gap-2 mb-2.5">
            <p className="font-extrabold text-[15px] text-[#0f2a4a]">
              {draft.id ? `SỬA DÒNG THỰC TẾ · ${draft.id}` : "THÊM DỊCH VỤ / CHI PHÍ THỰC TẾ"}
            </p>
            <button
              onClick={closeForm}
              aria-label="Đóng form"
              className="ml-auto touch-target rounded-lg p-1.5 text-slate-500 hover:bg-white"
            >
              <X size={18} />
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-12 gap-2.5">
            <div className="md:col-span-5">
              {isLegacyRow ? (
                <Field label="Dịch vụ (dòng cũ)" required hint="Dòng này không thuộc danh mục — tên đang lưu được giữ nguyên.">
                  <input
                    value={draft.name}
                    onChange={(e) => set("name", e.target.value)}
                    className={inputCls(draft.name.trim() ? "ok" : "missing")}
                  />
                </Field>
              ) : (
                <Field
                  label="Dịch vụ"
                  required
                  hint={services.length === 0 ? "Danh mục dịch vụ chưa được tải từ backend" : "Danh mục dùng chung của app"}
                >
                  <select
                    value={catalogByCode.has(draft.code) ? draft.code : ""}
                    onChange={(e) => pickService(e.target.value)}
                    className={inputCls(draft.name ? "ok" : "missing")}
                  >
                    <option value="">— Chọn dịch vụ —</option>
                    {groupedServices.map((group) => (
                      <optgroup key={group.group} label={group.group}>
                        {group.entries.map((entry) => (
                          <option key={entry.code} value={entry.code}>
                            {entry.name} ({entry.code})
                          </option>
                        ))}
                      </optgroup>
                    ))}
                  </select>
                </Field>
              )}
            </div>
            <Field label="Mã dịch vụ" hint="Tự lấy theo dịch vụ đã chọn">
              <input value={draft.code} readOnly placeholder="—" className={cx(inputCls(), "bg-slate-100 font-bold")} />
            </Field>
            <Field label="Đơn vị" hint="Thường là Lần">
              <input value={draft.unit} onChange={(e) => set("unit", e.target.value)} placeholder="Lần" className={inputCls()} />
            </Field>
            <Field label="Số lượng" hint="Mặc định 1">
              <input value={draft.qty} onChange={(e) => set("qty", e.target.value)} inputMode="decimal" placeholder="1" className={inputCls()} />
            </Field>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-12 gap-2.5 mt-2.5">
            <Field label={`Giá vốn (${ccy})`} required hint="Chi phí thực tế đã trả cho dịch vụ này">
              <input
                value={draft.cost}
                onChange={(e) => set("cost", e.target.value)}
                inputMode="decimal"
                placeholder="VD: 57000000"
                className={inputCls(draft.cost.trim() ? "ok" : "missing")}
              />
            </Field>
            <Field label={`Giá bán (${ccy})`} required hint="Giá bán thực tế cho khách">
              <input
                value={draft.price}
                onChange={(e) => set("price", e.target.value)}
                inputMode="decimal"
                placeholder="VD: 62000000"
                className={inputCls(draft.price.trim() ? "ok" : "missing")}
              />
            </Field>
            <Field label="VAT %" required hint="Phải tự nhập — 0 là giá trị hợp lệ (không VAT)">
              <input
                value={draft.vat}
                onChange={(e) => set("vat", e.target.value)}
                inputMode="decimal"
                placeholder="VD: 8"
                className={inputCls(draft.vat.trim() ? "ok" : "missing")}
              />
            </Field>
            <div className="sm:col-span-2 md:col-span-9">
              <Field label="Công đoạn chi phí">
                <select aria-label="Công đoạn chi phí" value={draft.journeyStage} onChange={e => set("journeyStage", e.target.value)} className={inputCls()}>
                  <option value="">Toàn lô / chưa phân công</option>
                  {shipment.journey?.nodes.map(n => <option key={n.id} value={n.id}>{n.label}</option>)}
                  {draft.journeyStage && !stageIds.has(draft.journeyStage) && <option value={draft.journeyStage}>Công đoạn trước đây: {draft.journeyStage}</option>}
                </select>
              </Field>
              <Field label="Ghi chú" hint="Không bắt buộc — VD: số hóa đơn, người chốt">
                <input value={draft.note} onChange={(e) => set("note", e.target.value)} placeholder="Ghi chú cho dòng này" className={inputCls()} />
              </Field>
            </div>
          </div>

          <p className="text-[13px] text-slate-600 mt-2.5">
            Tạm tính từ số vừa nhập (chỉ để soát, không phải số lưu): doanh thu {ccy}{" "}
            <b>{preview.net == null ? "—" : fmtMoney(preview.net)}</b>
            {" · "}sau VAT <b>{preview.withVat == null ? "—" : fmtMoney(preview.withVat)}</b>
            {" · "}chi phí <b>{preview.costTotal == null ? "—" : fmtMoney(preview.costTotal)}</b>. Số chính thức
            của lô do backend tính khi lưu.
          </p>

          {(localError || backendError) && (
            <div className="mt-2.5 rounded-xl border-2 border-red-300 bg-red-50 p-3 text-[13.5px] text-red-800 flex items-start gap-2">
              <CircleAlert size={17} className="shrink-0 mt-0.5" />
              <span>{localError || backendError}</span>
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 mt-3">
            <GhostBtn onClick={closeForm} className="min-h-[48px]">HỦY, KHÔNG LƯU</GhostBtn>
            <PrimaryBtn onClick={save} className="min-h-[48px]" disabled={pending != null}>
              <Save size={16} /> {draft.id ? "💾 LƯU LẠI DÒNG NÀY" : "💾 LƯU DÒNG THỰC TẾ"}
            </PrimaryBtn>
          </div>
        </div>
      )}
    </section>
  );
}
