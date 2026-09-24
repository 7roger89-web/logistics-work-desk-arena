// LOGI_COST_INTELLIGENCE_01 — explainable comparable-cost search.
import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, History, Search } from "lucide-react";
import { Field, PrimaryBtn, inputCls } from "./ui";
import QuickQuotePaste from "./QuickQuotePaste";
import { cx, fmtMoney } from "../lib/format";
import { findComparableCosts, type CostCriteria, type CostMatch } from "../lib/costHistory";
import type { ParsedQuote } from "../lib/quoteTextParser";
import type { Shipment } from "../lib/viewmodel";
import { useStore } from "../lib/store";

interface Form {
  incoterm: string;
  loadModel: string;
  equipment: string;
  cbm: string;
  weight: string;
  factory: string;
  pol: string;
  pod: string;
  delivery: string;
  mode: string;
  targetDate: string;
}

const EMPTY: Form = {
  incoterm: "", loadModel: "", equipment: "", cbm: "", weight: "",
  factory: "", pol: "", pod: "", delivery: "", mode: "Sea", targetDate: "",
};

const numberOrNull = (text: string): number | null => {
  const raw = String(text || "").replace(/\s/g, "").replace(/\.(?=\d{3}\b)/g, "").replace(",", ".");
  if (!raw) return null;
  const value = Number(raw);
  return Number.isFinite(value) ? value : null;
};

export default function CostCheck({ shipments, onUseMatch }: { shipments: Shipment[]; onUseMatch?: (match: CostMatch) => void }) {
  const { costIntelligence } = useStore();
  const [form, setForm] = useState<Form>(EMPTY);
  const [criteria, setCriteria] = useState<CostCriteria | null>(null);
  const [asked, setAsked] = useState<ParsedQuote | null>(null);
  const [selectedReference, setSelectedReference] = useState("");

  const set = (key: keyof Form, value: string) =>
    setForm((old) => ({
      ...old,
      [key]: value,
      ...(key === "loadModel" && value !== "FCL" ? { equipment: "" } : {}),
    }));

  const results = useMemo(
    () => criteria
      ? findComparableCosts(shipments, criteria, costIntelligence.rates, costIntelligence.catalog).slice(0, 5)
      : [],
    [criteria, shipments, costIntelligence]
  );

  const applyPaste = (parsed: ParsedQuote) => {
    setForm((old) => ({
      ...old,
      incoterm: parsed.incoterm || old.incoterm,
      pol: parsed.origin || old.pol,
      pod: parsed.destination || old.pod,
      cbm: parsed.cbm != null ? String(parsed.cbm) : old.cbm,
      weight: parsed.weightKg != null ? String(parsed.weightKg) : old.weight,
    }));
    setAsked(parsed.lines.length > 0 ? parsed : null);
  };

  const search = () => {
    setSelectedReference("");
    setCriteria({
      incoterm: form.incoterm.trim().toUpperCase(),
      origin: form.pol.trim(),
      destination: form.pod.trim(),
      factory: form.factory.trim(),
      pol: form.pol.trim(),
      pod: form.pod.trim(),
      delivery: form.delivery.trim(),
      loadModel: form.loadModel.trim().toUpperCase(),
      equipment: form.equipment.trim().toUpperCase(),
      cbm: numberOrNull(form.cbm),
      weightKg: numberOrNull(form.weight),
      mode: form.mode.trim(),
      targetDate: form.targetDate.trim(),
    });
  };

  return (
    <div className="space-y-4" data-testid="cost-check">
      <QuickQuotePaste
        testId="cost-paste"
        title="DÁN THÔNG TIN KHÁCH / GIÁ ĐANG HỎI"
        hint="Dán yêu cầu khách nếu có — chỉ điền giúp tiêu chí tìm kiếm. Không lưu và không tự chọn giá."
        applyLabel="ĐIỀN VÀO Ô TÌM KIẾM"
        placeholder={"VD: EXW Shenzhen - Hải Phòng\n20GP\nGiao Long Biên, Hà Nội"}
        onApply={applyPaste}
      />

      <section className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5">
        <p className="font-extrabold text-[16px] text-[#0f2a4a] flex items-center gap-2">
          <History size={18} className="text-[#1e5aa8]" /> Lô / giá cần tham khảo
        </p>
        <p className="text-[13px] text-slate-500 mt-0.5">
          Điền cái đã biết. Ô trống = chưa biết, không phải bằng 0. Chỉ lấy 5 tham chiếu gần nhất và giải thích lý do.
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 mt-3">
          <Field label="Incoterm"><input value={form.incoterm} onChange={(e) => set("incoterm", e.target.value.toUpperCase())} data-testid="cost-incoterm" placeholder="EXW / FOB / DAP…" className={inputCls()} /></Field>
          <Field label="Loại hàng">
            <select value={form.loadModel} onChange={(e) => set("loadModel", e.target.value)} className={inputCls()} data-testid="cost-load-model">
              <option value="">-- Chưa biết --</option><option value="FCL">FCL · nguyên container</option><option value="LCL">LCL · hàng lẻ</option>
            </select>
          </Field>
          <Field label="Container" hint={form.loadModel === "LCL" ? "LCL dùng CBM/kg bên dưới." : ""}>
            <select value={form.equipment} onChange={(e) => set("equipment", e.target.value)} disabled={form.loadModel === "LCL"} className={inputCls()} data-testid="cost-equipment">
              <option value="">-- Chưa biết --</option><option value="20GP">20GP</option><option value="40GP">40GP</option><option value="40HQ">40HQ</option>
            </select>
          </Field>
          <Field label="Nhà máy / nơi lấy hàng"><input value={form.factory} onChange={(e) => set("factory", e.target.value)} data-testid="cost-factory" placeholder="VD: Shenzhen, Guangdong" className={inputCls()} /></Field>
          <Field label="Cảng đi / POL"><input value={form.pol} onChange={(e) => set("pol", e.target.value)} data-testid="cost-pol" placeholder="VD: Shenzhen / Nansha" className={inputCls()} /></Field>
          <Field label="Cảng đến / POD"><input value={form.pod} onChange={(e) => set("pod", e.target.value)} data-testid="cost-pod" placeholder="VD: Hải Phòng" className={inputCls()} /></Field>
          <Field label="Giao cuối tại Việt Nam"><input value={form.delivery} onChange={(e) => set("delivery", e.target.value)} data-testid="cost-delivery" placeholder="VD: Long Biên, Hà Nội" className={inputCls()} /></Field>
          <Field label="Số khối (CBM)"><input value={form.cbm} onChange={(e) => set("cbm", e.target.value)} inputMode="decimal" data-testid="cost-cbm" placeholder="VD: 5" className={inputCls()} /></Field>
          <Field label="Cân nặng (kg)"><input value={form.weight} onChange={(e) => set("weight", e.target.value)} inputMode="decimal" data-testid="cost-weight" placeholder="VD: 800" className={inputCls()} /></Field>
          <Field label="Phương thức">
            <select value={form.mode} onChange={(e) => set("mode", e.target.value)} className={inputCls()} data-testid="cost-mode">
              <option value="">-- Chưa biết --</option><option value="Sea">Đường biển</option><option value="Road">Đường bộ</option><option value="Air">Hàng không</option><option value="Rail">Đường sắt</option>
            </select>
          </Field>
          <Field label="Ngày dự kiến" hint="Để trống = hôm nay."><input type="date" value={form.targetDate} onChange={(e) => set("targetDate", e.target.value)} data-testid="cost-target-date" className={inputCls()} /></Field>
        </div>
        <div className="mt-3"><PrimaryBtn onClick={search} testId="cost-search" className="w-full sm:w-auto"><Search size={17} /> TÌM GIÁ GẦN NHẤT</PrimaryBtn></div>
      </section>

      {asked && (
        <section className="rounded-2xl border-2 border-blue-200 bg-blue-50/60 p-4" data-testid="cost-asked">
          <p className="text-[12px] font-extrabold uppercase tracking-wider text-blue-800 bg-blue-100 inline-block rounded-md px-2 py-0.5">Giá đang hỏi / dữ liệu mới — chưa lưu</p>
          <div className="mt-2 space-y-1.5">
            {asked.lines.map((line, i) => (
              <div key={i} className="flex flex-wrap items-baseline gap-x-2 text-[13.5px]">
                <span className="font-bold text-slate-800">{line.name}</span>
                <span className="font-extrabold text-[#1e5aa8]">{line.sell == null ? "—" : fmtMoney(line.sell)} {line.currency}</span>
                {line.unit && <span className="text-slate-500">/ {line.unit}</span>}
              </div>
            ))}
          </div>
        </section>
      )}

      {criteria && (
        <section className="space-y-3" data-testid="cost-results">
          <p className="text-[14px] font-semibold text-slate-600" data-testid="cost-results-count">
            Top <b className="text-[#0f2a4a]">{results.length}</b> tham chiếu gần nhất · ưu tiên THỰC TẾ → GIÁ ĐẦU VÀO → BÁO GIÁ khi độ phù hợp tương đương.
          </p>
          {results.length === 0 && <div className="rounded-2xl bg-white border border-slate-200 p-6 text-center"><p className="font-bold text-[15.5px]">Chưa có dữ liệu đủ gần để tham khảo</p><p className="text-[13.5px] text-slate-500 mt-1">Thử bớt tiêu chí. Hệ thống không tự bịa giá khi không có nguồn phù hợp.</p></div>}
          {results.map((match) => <CostResultCard key={match.referenceId} match={match} selected={selectedReference === match.referenceId} onSelect={() => { setSelectedReference(match.referenceId); onUseMatch?.(match); }} />)}
          {selectedReference && <p className="rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-2 text-[13px] font-semibold text-emerald-900">Đã chọn một tham chiếu làm giá vốn. App chưa tự sửa báo giá hay cộng ghép nguồn khác.</p>}
        </section>
      )}
    </div>
  );
}

function CostResultCard({ match, selected, onSelect }: { match: CostMatch; selected: boolean; onSelect: () => void }) {
  const sourceTone = match.source === "ACTUAL"
    ? "border-emerald-300 bg-emerald-50 text-emerald-800"
    : match.source === "INPUT_RATE"
    ? "border-blue-300 bg-blue-50 text-blue-800"
    : "border-violet-300 bg-violet-50 text-violet-800";

  return (
    <article data-testid="cost-result" data-reference-id={match.referenceId} data-shipment-id={match.shipmentId} data-source={match.source}
      className={cx("rounded-2xl bg-white border-2 p-4", selected ? "border-emerald-400" : "border-slate-200")}>
      <div className="flex flex-wrap items-center gap-2">
        <span className="font-extrabold text-[15.5px] text-[#0f2a4a]">{match.shipmentId ? "LÔ: " + match.shipmentId : match.supplier || "GIÁ ĐẦU VÀO"}</span>
        {match.period && <span className="text-[13px] text-slate-500">THÁNG: {match.period}</span>}
        <span className={cx("rounded-full border px-2.5 py-0.5 text-[12px] font-extrabold", sourceTone)}>{match.sourceLabel}</span>
        {match.ageDays != null && <span className="text-[12px] font-semibold text-slate-500">{match.ageDays} ngày trước</span>}
      </div>

      <p className="text-[13.5px] text-slate-700 mt-1">{[match.equipment, match.incoterm, (match.origin || "—") + " → " + (match.destination || "—")].filter(Boolean).join(" · ")}</p>
      {(match.cbm != null || match.weightKg != null || match.customer) && <p className="text-[13px] text-slate-500">{match.cbm != null ? String(match.cbm) + " CBM" : ""}{match.weightKg != null ? " · " + fmtMoney(match.weightKg) + " kg" : ""}{match.customer ? " · " + match.customer : ""}</p>}
      <p className="text-[13px] font-semibold text-[#1e5aa8] mt-1" data-testid="cost-result-why">Khớp: {match.reasons.join(" + ")}</p>

      {match.differences && match.differences.length > 0 && <div className="mt-2 rounded-lg border border-amber-200 bg-amber-50 px-2.5 py-2 text-[12.5px] text-amber-900"><b>Khác / cần lưu ý:</b> {match.differences.join(" · ")}</div>}
      {match.expired && <p className="mt-2 rounded-lg border border-red-200 bg-red-50 px-2.5 py-1.5 text-[12.5px] font-bold text-red-800">Dữ liệu cũ/hết hiệu lực — chỉ tham khảo, không phải giá hiện tại.</p>}
      {match.source === "QUOTE" && <p className="mt-2 rounded-lg border border-violet-200 bg-violet-50 px-2.5 py-1.5 text-[12.5px] font-semibold text-violet-900">Đây là BÁO GIÁ / DỰ KIẾN, không phải chi phí đã phát sinh thực tế.</p>}

      <div className="mt-2.5 space-y-1.5">
        {match.lines.map((line, i) => <div key={i} className="rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-2"><div className="flex flex-wrap items-baseline gap-x-2"><span className="font-bold text-[13.5px] text-slate-800">{line.label}</span><span className="font-extrabold text-[13.5px] text-[#0f2a4a]">{line.price == null ? "—" : fmtMoney(line.price)} {line.ccy}</span>{line.unit && <span className="text-[12.5px] text-slate-500">/ {line.unit}</span>}</div>{line.note && <p className="text-[12.5px] text-slate-600 mt-0.5">{line.note}</p>}</div>)}
      </div>

      {match.totalsByCurrency.length > 0 ? <div className="mt-2.5 flex flex-wrap items-center gap-2" data-testid="cost-result-totals">{match.totalsByCurrency.map((total) => <span key={total.ccy} className="rounded-lg border border-slate-200 bg-white px-2.5 py-1 text-[13px] font-bold text-slate-700">Tổng {total.ccy}: {fmtMoney(total.amount)}</span>)}<span className="text-[12px] text-slate-400">Mỗi đồng tiền tính riêng · không cộng gộp.</span></div> : match.source === "INPUT_RATE" ? <p className="mt-2 text-[12px] text-slate-400">Không tự cộng các phí /CONT, /SET, /BL khác đơn vị thành một “tổng” giả.</p> : null}

      <div className="mt-3 flex flex-wrap gap-2">
        <button type="button" onClick={onSelect} className={cx("btn-press touch-target inline-flex items-center rounded-xl px-3.5 min-h-[44px] text-[13.5px] font-bold", selected ? "bg-emerald-700 text-white" : "border-2 border-emerald-700 bg-white text-emerald-800")}>{selected ? "ĐÃ CHỌN LÀM THAM CHIẾU" : "DÙNG LÀM GIÁ VỐN"}</button>
        {match.shipmentId && <Link to={"/lo-hang/" + match.shipmentId + "?tab=tai-chinh"} data-testid="cost-result-open" className="btn-press touch-target inline-flex items-center gap-1.5 rounded-xl border-2 border-[#0f2a4a] bg-white text-[#0f2a4a] font-bold text-[13.5px] px-3.5 min-h-[44px]">XEM LÔ GỐC <ArrowRight size={15} /></Link>}
      </div>
    </article>
  );
}
