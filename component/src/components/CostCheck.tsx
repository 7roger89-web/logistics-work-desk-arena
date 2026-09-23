// ============================================================================
// LOGI_QUOTE_COST_WORKFLOW_UX_01 — "CHECK CHI PHÍ" workspace.
//
// An INNER segmented view of the existing Báo Giá workspace (no new sidebar
// group, no new route). It answers one daily question: "lô tương tự trước đây
// chi phí bao nhiêu?" using ONLY data the app already has:
//   Finance ACTUAL lines of existing shipments  → SOURCE=THỰC TẾ
//   quote estimate projected on the lot         → SOURCE=BÁO GIÁ / DỰ KIẾN
// No new collection, no writer, no AI, no vector search.
// ============================================================================

import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, History, Search } from "lucide-react";
import { Field, PrimaryBtn, inputCls } from "./ui";
import QuickQuotePaste from "./QuickQuotePaste";
import { cx, fmtMoney } from "../lib/format";
import { findComparableCosts, type CostCriteria, type CostMatch } from "../lib/costHistory";
import type { ParsedQuote } from "../lib/quoteTextParser";
import type { Shipment } from "../lib/viewmodel";

interface Form {
  incoterm: string;
  cbm: string;
  weight: string;
  origin: string;
  destination: string;
  mode: string;
}

const EMPTY: Form = { incoterm: "", cbm: "", weight: "", origin: "", destination: "", mode: "" };

const numberOrNull = (text: string): number | null => {
  const raw = String(text || "").replace(/\s/g, "").replace(/\.(?=\d{3}\b)/g, "").replace(",", ".");
  if (!raw) return null;
  const value = Number(raw);
  return Number.isFinite(value) ? value : null;
};

export default function CostCheck({ shipments }: { shipments: Shipment[] }) {
  const [form, setForm] = useState<Form>(EMPTY);
  const [criteria, setCriteria] = useState<CostCriteria | null>(null);
  /** Service lines from the pasted inquiry — a comparison block, never saved. */
  const [asked, setAsked] = useState<ParsedQuote | null>(null);

  const set = (k: keyof Form, v: string) => setForm((f) => ({ ...f, [k]: v }));

  const results = useMemo(
    () => (criteria ? findComparableCosts(shipments, criteria) : []),
    [criteria, shipments]
  );

  // The SAME parser Báo Giá uses — imported through QuickQuotePaste, not copied.
  const applyPaste = (parsed: ParsedQuote) => {
    setForm((f) => ({
      ...f,
      incoterm: parsed.incoterm || f.incoterm,
      origin: parsed.origin || f.origin,
      destination: parsed.destination || f.destination,
      cbm: parsed.cbm != null ? String(parsed.cbm) : f.cbm,
      weight: parsed.weightKg != null ? String(parsed.weightKg) : f.weight,
    }));
    setAsked(parsed.lines.length > 0 ? parsed : null);
  };

  const search = () => {
    setCriteria({
      incoterm: form.incoterm.trim().toUpperCase(),
      origin: form.origin.trim(),
      destination: form.destination.trim(),
      cbm: numberOrNull(form.cbm),
      weightKg: numberOrNull(form.weight),
      mode: form.mode.trim(),
    });
  };

  return (
    <div className="space-y-4" data-testid="cost-check">
      <QuickQuotePaste
        testId="cost-paste"
        title="DÁN THÔNG TIN KHÁCH / GIÁ CƯỚC"
        hint="Dán yêu cầu của khách (Incoterm, tuyến, số khối, cân nặng, giá đang hỏi) — hệ thống đọc thử rồi bạn xác nhận. Không có gì được lưu."
        applyLabel="ĐIỀN VÀO Ô TÌM KIẾM"
        placeholder={"VD: EXW Guangdong - Hà Nội\n5 khối\n800 kg"}
        onApply={applyPaste}
      />

      <section className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5">
        <p className="font-extrabold text-[16px] text-[#0f2a4a] flex items-center gap-2">
          <History size={18} className="text-[#1e5aa8]" /> Tiêu chí lô cần check
        </p>
        <p className="text-[13px] text-slate-500 mt-0.5">
          Điền những gì đã biết — càng nhiều tiêu chí, kết quả càng sát. Ô trống nghĩa là chưa biết,
          không phải bằng 0.
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 mt-3">
          <Field label="Điều kiện giao hàng / Incoterm">
            <input value={form.incoterm} onChange={(e) => set("incoterm", e.target.value.toUpperCase())}
              data-testid="cost-incoterm" placeholder="EXW / FOB / DAP…" className={inputCls()} />
          </Field>
          <Field label="Số khối (CBM)">
            <input value={form.cbm} onChange={(e) => set("cbm", e.target.value)} inputMode="decimal"
              data-testid="cost-cbm" placeholder="VD: 5" className={inputCls()} />
          </Field>
          <Field label="Cân nặng (kg)">
            <input value={form.weight} onChange={(e) => set("weight", e.target.value)} inputMode="decimal"
              data-testid="cost-weight" placeholder="VD: 800" className={inputCls()} />
          </Field>
          <Field label="Từ đâu / cảng đi">
            <input value={form.origin} onChange={(e) => set("origin", e.target.value)}
              data-testid="cost-origin" placeholder="VD: Guangdong" className={inputCls()} />
          </Field>
          <Field label="Đến đâu / cảng đến">
            <input value={form.destination} onChange={(e) => set("destination", e.target.value)}
              data-testid="cost-destination" placeholder="VD: Hà Nội" className={inputCls()} />
          </Field>
          <Field label="Phương thức vận chuyển" hint="Không bắt buộc.">
            <input value={form.mode} onChange={(e) => set("mode", e.target.value)}
              data-testid="cost-mode" placeholder="Truck / Sea / Air…" className={inputCls()} />
          </Field>
        </div>
        <div className="mt-3">
          <PrimaryBtn onClick={search} testId="cost-search" className="w-full sm:w-auto">
            <Search size={17} /> TÌM DỮ LIỆU CŨ
          </PrimaryBtn>
        </div>
      </section>

      {asked && (
        <section className="rounded-2xl border-2 border-blue-200 bg-blue-50/60 p-4" data-testid="cost-asked">
          <p className="text-[12px] font-extrabold uppercase tracking-wider text-blue-800 bg-blue-100 inline-block rounded-md px-2 py-0.5">
            Giá đang hỏi / dữ liệu mới — chưa lưu
          </p>
          <div className="mt-2 space-y-1.5">
            {asked.lines.map((l, i) => (
              <div key={i} className="flex flex-wrap items-baseline gap-x-2 text-[13.5px]">
                <span className="font-bold text-slate-800">{l.name}</span>
                <span className="font-extrabold text-[#1e5aa8]">
                  {l.sell == null ? "—" : fmtMoney(l.sell)} {l.currency}
                </span>
                {l.unit && <span className="text-slate-500">/ {l.unit}</span>}
                {l.condition === "IF_APPLICABLE" && <span className="text-amber-800 font-semibold">· có thể phát sinh</span>}
                {l.status === "ESTIMATE_REQUIRES_CONFIRMATION" && <span className="text-violet-800 font-semibold">· ước tính</span>}
              </div>
            ))}
          </div>
        </section>
      )}

      {criteria && (
        <section className="space-y-3" data-testid="cost-results">
          <p className="text-[14px] font-semibold text-slate-600" data-testid="cost-results-count">
            Tìm thấy <b className="text-[#0f2a4a]">{results.length}</b> lô tham chiếu từ dữ liệu đang có
            (lô thực tế được ưu tiên hơn số báo giá).
          </p>
          {results.length === 0 && (
            <div className="rounded-2xl bg-white border border-slate-200 p-6 text-center" data-testid="cost-empty">
              <p className="font-bold text-[15.5px]">Chưa có lô cũ nào đủ giống để tham chiếu</p>
              <p className="text-[13.5px] text-slate-500 mt-1">
                Thử bớt tiêu chí (ví dụ chỉ tuyến + Incoterm) — hệ thống không đoán con số nào cả.
              </p>
            </div>
          )}
          {results.map((r) => <CostResultCard key={r.shipmentId} match={r} />)}
        </section>
      )}
    </div>
  );
}

function CostResultCard({ match }: { match: CostMatch }) {
  return (
    <article
      data-testid="cost-result"
      data-shipment-id={match.shipmentId}
      data-source={match.source}
      className="rounded-2xl bg-white border border-slate-200 p-4"
    >
      <div className="flex flex-wrap items-center gap-2">
        <span className="font-extrabold text-[15.5px] text-[#0f2a4a]">LÔ: {match.shipmentId}</span>
        {match.period && <span className="text-[13px] text-slate-500">THÁNG: {match.period}</span>}
        <span
          data-testid="cost-result-source"
          className={cx(
            "rounded-full border px-2.5 py-0.5 text-[12px] font-extrabold",
            match.source === "ACTUAL"
              ? "border-emerald-300 bg-emerald-50 text-emerald-800"
              : "border-violet-300 bg-violet-50 text-violet-800"
          )}
        >
          SOURCE: {match.sourceLabel}
        </span>
      </div>
      <p className="text-[13.5px] text-slate-700 mt-1">
        {[match.incoterm, `${match.origin || "—"} → ${match.destination || "—"}`].filter(Boolean).join(" · ")}
      </p>
      <p className="text-[13px] text-slate-500">
        {match.cbm != null ? `${match.cbm} CBM` : "— CBM"} · {match.weightKg != null ? `${fmtMoney(match.weightKg)} kg` : "— kg"}
        {match.customer ? ` · ${match.customer}` : ""}
      </p>
      <p className="text-[13px] font-semibold text-[#1e5aa8] mt-1" data-testid="cost-result-why">
        Khớp: {match.reasons.join(" + ")}
      </p>

      {match.source === "QUOTE" && (
        <p className="mt-2 rounded-lg border border-violet-200 bg-violet-50 px-2.5 py-1.5 text-[12.5px] font-semibold text-violet-900">
          Lô này chưa có dòng chi phí thực tế — đây là số BÁO GIÁ / DỰ KIẾN, không phải chi phí đã phát sinh.
        </p>
      )}

      <div className="mt-2.5 space-y-1.5">
        {match.lines.map((l, i) => (
          <div key={i} data-testid="cost-result-line" className="rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-2">
            <div className="flex flex-wrap items-baseline gap-x-2 gap-y-0.5">
              <span className="font-bold text-[13.5px] text-slate-800">{l.label}</span>
              <span className="font-extrabold text-[13.5px] text-[#0f2a4a]">
                {l.price == null ? "—" : fmtMoney(l.price)} {l.ccy}
              </span>
              {l.unit && <span className="text-[12.5px] text-slate-500">/ {l.unit}</span>}
              {l.qty != null && <span className="text-[12.5px] text-slate-500">· SL {fmtMoney(l.qty)}</span>}
              {l.vat != null && <span className="text-[12.5px] text-slate-500">· VAT {l.vat}%</span>}
            </div>
            {l.note && <p className="text-[12.5px] text-slate-600 mt-0.5">{l.note}</p>}
          </div>
        ))}
      </div>

      <div className="mt-2.5 flex flex-wrap items-center gap-2" data-testid="cost-result-totals">
        {match.totalsByCurrency.map((t) => (
          <span key={t.ccy} className="rounded-lg border border-slate-200 bg-white px-2.5 py-1 text-[13px] font-bold text-slate-700">
            Tổng {t.ccy}: {fmtMoney(t.amount)}
          </span>
        ))}
        <span className="text-[12px] text-slate-400">Mỗi đồng tiền tính riêng — không cộng gộp.</span>
      </div>

      <Link
        to={`/lo-hang/${match.shipmentId}?tab=tai-chinh`}
        data-testid="cost-result-open"
        className="btn-press touch-target mt-3 inline-flex items-center gap-1.5 rounded-xl border-2 border-[#0f2a4a] bg-white text-[#0f2a4a] font-bold text-[13.5px] px-3.5 min-h-[44px]"
      >
        XEM LÔ GỐC <ArrowRight size={15} />
      </Link>
    </article>
  );
}
