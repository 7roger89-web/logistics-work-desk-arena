// LOGI_CONTRACT_INTL_PAYMENT_COMPARATOR_01 — Thanh toán quốc tế comparator
// Vietnamese-first, mobile-friendly, decision-support only (no money transfer).
import { useMemo, useState, useEffect } from "react";
import { useStore } from "../lib/store";
import type { Contract, IntlFxRates, IntlSnapshot } from "../lib/viewmodel";
import { fmtMoney, fmtText } from "../lib/format";

function numOrNull(v: string): number | null {
  if (v == null || v === "") return null;
  const t = String(v).replace(/,/g, "").replace(/\s/g, "").trim();
  if (!t) return null;
  const n = Number(t);
  return Number.isFinite(n) ? n : null;
}
function fmtUSD(n: number | null | undefined): string {
  if (n == null || !Number.isFinite(n)) return "—";
  return n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + " USD";
}
function fmtCNY(n: number | null | undefined): string {
  if (n == null || !Number.isFinite(n)) return "—";
  return n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + " CNY";
}
function fmtVND(n: number | null | undefined): string {
  if (n == null || !Number.isFinite(n)) return "—";
  return Math.round(n).toLocaleString("vi-VN") + " ₫";
}
function fmtRate(n: number | null | undefined, suffix = ""): string {
  if (n == null || !Number.isFinite(n)) return "—";
  return n.toLocaleString("en-US", { maximumFractionDigits: 4 }) + suffix;
}

function chinaForward(gross: number, rate: number, feePerTranche = 150, trancheSize = 10000, recipientFee = 35) {
  const trancheCount = gross <= 0 ? 0 : Math.ceil(gross / trancheSize);
  const chinaFee = trancheCount * feePerTranche;
  const afterBank = gross - recipientFee;
  const grossCny = afterBank * rate;
  const net = grossCny - chinaFee;
  return { afterBank, grossCny, chinaFee, net, trancheCount };
}
function hkForward(gross: number, rate: number, hkPct = 0.02, recipientFee = 35) {
  const afterBank = gross - recipientFee;
  const hkFee = afterBank * hkPct;
  const forConv = afterBank - hkFee;
  const net = forConv * rate;
  return { afterBank, hkFee, forConv, net };
}
function vnCost(gross: number, sell: number, swiftUsd = 5, pct = 0.0015) {
  const principal = gross * sell;
  const swift = swiftUsd * sell;
  const pctFee = principal * pct;
  const total = principal + swift + pctFee;
  return { principal, swift, pctFee, total };
}

export default function IntlPaymentComparator({ contract, fxRates }: { contract: Contract; fxRates: IntlFxRates | null }) {
  const { dispatch, toast } = useStore();
  // Mode
  const [mode, setMode] = useState<"A" | "B">("B");
  // FX manual overrides — seeded from live when available
  const liveBocRate = fxRates?.boc?.usd_to_cny ?? null;
  const liveAgri = fxRates?.agribank?.usd_sell_vnd ?? fxRates?.agribank?.sell ?? null;
  const liveBidv = fxRates?.bidv?.usd_sell_vnd ?? fxRates?.bidv?.sell ?? null;
  const bocStatus = fxRates?.boc?.status ?? "RATE_UNAVAILABLE";
  const agriStatus = fxRates?.agribank?.status ?? "RATE_UNAVAILABLE";
  const bidvStatus = fxRates?.bidv?.status ?? "RATE_UNAVAILABLE";
  const bidvRateStatus = (fxRates?.bidv as unknown as { bidv_rate_status?: string })?.bidv_rate_status ?? bidvStatus;

  const [usdToCny, setUsdToCny] = useState<string>("");
  const [agriSell, setAgriSell] = useState<string>("");
  const [bidvSell, setBidvSell] = useState<string>("");
  const [outsideRate, setOutsideRate] = useState<string>("3900");

  // Mode A states
  const [grossUsd, setGrossUsd] = useState<string>("1500");
  const [agentRoute, setAgentRoute] = useState<"CHINA" | "HONG_KONG">("CHINA");
  const [vnBank, setVnBank] = useState<"AGRIBANK" | "BIDV">("AGRIBANK");

  // Mode B states
  const [targetCny, setTargetCny] = useState<string>("10000");

  // Fee assumptions editable
  const [showFees, setShowFees] = useState(false);
  const [recipientFee, setRecipientFee] = useState<string>("35");
  const [chinaFeePerTranche, setChinaFeePerTranche] = useState<string>("150");
  const [chinaTrancheSize, setChinaTrancheSize] = useState<string>("10000");
  const [hkPctStr, setHkPctStr] = useState<string>("2");
  const [vnSwift, setVnSwift] = useState<string>("5");
  const [vnPctStr, setVnPctStr] = useState<string>("0.15");

  // Seed from live once on mount / when fxRates arrives and fields still empty
  useEffect(() => {
    if (usdToCny === "" && liveBocRate != null) setUsdToCny(String(liveBocRate));
    // fallback sanity 6.6955 if live missing? keep empty to force manual
  }, [liveBocRate]); // eslint-disable-line
  useEffect(() => {
    if (agriSell === "" && liveAgri != null) setAgriSell(String(liveAgri));
  }, [liveAgri]); // eslint-disable-line
  useEffect(() => {
    if (bidvSell === "" && liveBidv != null) setBidvSell(String(liveBidv));
  }, [liveBidv]); // eslint-disable-line

  // Effective numbers for preview
  const effUsdToCny = useMemo(() => numOrNull(usdToCny) ?? liveBocRate ?? null, [usdToCny, liveBocRate]);
  const effAgri = useMemo(() => numOrNull(agriSell) ?? liveAgri ?? null, [agriSell, liveAgri]);
  const effBidv = useMemo(() => numOrNull(bidvSell) ?? liveBidv ?? null, [bidvSell, liveBidv]);
  const effOutside = useMemo(() => numOrNull(outsideRate), [outsideRate]);
  const effGross = useMemo(() => numOrNull(grossUsd), [grossUsd]);
  const effTarget = useMemo(() => numOrNull(targetCny), [targetCny]);
  const effRecipient = useMemo(() => numOrNull(recipientFee) ?? 35, [recipientFee]);
  const effChinaFee = useMemo(() => numOrNull(chinaFeePerTranche) ?? 150, [chinaFeePerTranche]);
  const effTrancheSize = useMemo(() => numOrNull(chinaTrancheSize) ?? 10000, [chinaTrancheSize]);
  const effHkPct = useMemo(() => {
    const v = numOrNull(hkPctStr);
    if (v == null) return 0.02;
    return v / 100;
  }, [hkPctStr]);
  const effVnSwift = useMemo(() => numOrNull(vnSwift) ?? 5, [vnSwift]);
  const effVnPct = useMemo(() => {
    const v = numOrNull(vnPctStr);
    if (v == null) return 0.0015;
    return v / 100;
  }, [vnPctStr]);

  // Previews
  const previewA = useMemo(() => {
    if (mode !== "A") return null;
    if (effGross == null || effUsdToCny == null) return null;
    if (agentRoute === "CHINA") {
      const f = chinaForward(effGross, effUsdToCny, effChinaFee, effTrancheSize, effRecipient);
      const sell = vnBank === "BIDV" ? effBidv : effAgri;
      const vnc = sell != null ? vnCost(effGross, sell, effVnSwift, effVnPct) : null;
      return { kind: "CHINA" as const, ...f, vnCost: vnc, sell };
    } else {
      const f = hkForward(effGross, effUsdToCny, effHkPct, effRecipient);
      const sell = vnBank === "BIDV" ? effBidv : effAgri;
      const vnc = sell != null ? vnCost(effGross, sell, effVnSwift, effVnPct) : null;
      return { kind: "HONG_KONG" as const, ...f, vnCost: vnc, sell };
    }
  }, [mode, effGross, effUsdToCny, agentRoute, effChinaFee, effTrancheSize, effRecipient, effHkPct, effAgri, effBidv, vnBank, effVnSwift, effVnPct]);

  const previewB = useMemo(() => {
    if (mode !== "B") return null;
    if (effTarget == null || effOutside == null || effUsdToCny == null || effAgri == null) return null;
    const outsideTotal = effTarget * effOutside;
    // China reverse solve with iteration until stable
    let chinaGross: number;
    {
      let fee = effChinaFee;
      let gross = (effTarget + fee) / effUsdToCny + effRecipient;
      for (let i = 0; i < 10; i++) {
        const tranches = Math.ceil(gross / effTrancheSize);
        const newFee = tranches * effChinaFee;
        if (newFee === fee) {
          const checkGross = (effTarget + newFee) / effUsdToCny + effRecipient;
          if (Math.ceil(checkGross / effTrancheSize) === tranches) {
            gross = checkGross;
            fee = newFee;
            break;
          }
        }
        fee = newFee;
        gross = (effTarget + fee) / effUsdToCny + effRecipient;
      }
      chinaGross = gross;
    }
    const hkGross = effTarget / (effUsdToCny * (1 - effHkPct)) + effRecipient;

    const build = (gross: number, sell: number | null) => {
      if (sell == null) return { available: false as const, status: "RATE_UNAVAILABLE" as const, gross, total: null as number | null, delta: null as number | null };
      const vc = vnCost(gross, sell, effVnSwift, effVnPct);
      return { available: true as const, status: "OK" as const, gross, total: vc.total, delta: vc.total - outsideTotal, breakdown: vc };
    };
    const chinaAgri = build(chinaGross, effAgri);
    const chinaBidv = effBidv != null ? build(chinaGross, effBidv) : { available: false as const, status: "RATE_UNAVAILABLE" as const, gross: chinaGross, total: null, delta: null };
    const hkAgri = build(hkGross, effAgri);
    const hkBidv = effBidv != null ? build(hkGross, effBidv) : { available: false as const, status: "RATE_UNAVAILABLE" as const, gross: hkGross, total: null, delta: null };

    // Determine cheapest among available
    const all = [
      { label: "USD→TQ via Agribank", data: chinaAgri },
      { label: "USD→TQ via BIDV", data: chinaBidv },
      { label: "USD→HK via Agribank", data: hkAgri },
      { label: "USD→HK via BIDV", data: hkBidv },
      { label: "Tệ ngoài", data: { available: true as const, status: "OK" as const, total: outsideTotal, delta: 0, gross: null as number | null } },
    ];
    const availableTotals = all.filter((x) => x.data.available && (x.data as { total: number | null }).total != null).map((x) => (x.data as { total: number }).total);
    const minTotal = availableTotals.length ? Math.min(...availableTotals) : null;

    return { outsideTotal, chinaGross, hkGross, chinaAgri, chinaBidv, hkAgri, hkBidv, effTarget, minTotal, all };
  }, [mode, effTarget, effOutside, effUsdToCny, effAgri, effBidv, effChinaFee, effTrancheSize, effRecipient, effHkPct, effVnSwift, effVnPct]);

  const handleSave = () => {
    const requestId = `req-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
    const payload: Record<string, unknown> = {
      contractId: contract.id,
      requestId,
      mode,
      usd_to_cny: usdToCny || (effUsdToCny != null ? String(effUsdToCny) : ""),
      agribank_sell_vnd: agriSell || (effAgri != null ? String(effAgri) : ""),
      bidv_sell_vnd: bidvSell || (effBidv != null ? String(effBidv) : ""),
      outside_cny_vnd: outsideRate,
      recipient_bank_fee_usd: recipientFee,
      china_fee_per_tranche_cny: chinaFeePerTranche,
      china_tranche_size_usd: chinaTrancheSize,
      hk_fee_pct: String(effHkPct),
      vn_swift_fee_usd: vnSwift,
      vn_pct_fee: String(effVnPct),
      fxBoc: fxRates?.boc ?? { status: bocStatus, source_url: "manual" },
      fxAgribank: fxRates?.agribank ?? { status: agriStatus, source_url: "manual" },
      fxBidv: fxRates?.bidv ?? { status: bidvStatus, source_url: "manual", bidv_rate_status: bidvRateStatus },
    };
    if (mode === "A") {
      payload.gross_usd = grossUsd;
      payload.agent_route = agentRoute;
      payload.vn_bank = vnBank;
    } else {
      payload.target_cny = targetCny;
    }
    const ok = dispatch("contract_intl_snapshot_save", payload);
    if (!ok) {
      // fallback alias
      const ok2 = dispatch("contract_payment_snapshot_save", payload);
      if (!ok2) {
        toast("Không gửi được", "Component chưa kết nối backend.", "red");
        return;
      }
    }
    toast("Đã gửi lưu snapshot", "Máy chủ sẽ tính lại bằng Decimal và lưu bất biến.", "blue");
  };

  const snapshots: IntlSnapshot[] = (contract as unknown as { intlSnapshots?: IntlSnapshot[] }).intlSnapshots ?? [];

  return (
    <div className="space-y-4">
      {/* Mode switch — large touch targets */}
      <div className="rounded-2xl bg-white border border-slate-200 p-3">
        <div className="flex gap-2">
          <button onClick={() => setMode("A")} className={`flex-1 min-h-[52px] rounded-xl font-extrabold text-[15px] border-2 ${mode === "A" ? "bg-[#0f2a4a] text-white border-[#0f2a4a] shadow" : "bg-white border-slate-200 text-slate-700"}`}>
            A · Tôi chuyển USD
          </button>
          <button onClick={() => setMode("B")} className={`flex-1 min-h-[52px] rounded-xl font-extrabold text-[15px] border-2 ${mode === "B" ? "bg-[#0f2a4a] text-white border-[#0f2a4a] shadow" : "bg-white border-slate-200 text-slate-700"}`}>
            B · Đại lý cần nhận CNY
          </button>
        </div>
        <p className="text-[12.5px] text-slate-500 mt-2 leading-snug">
          Công cụ hỗ trợ quyết định — không thực hiện chuyển tiền. Mọi số do máy chủ tính lại bằng Decimal trước khi lưu.
        </p>
      </div>

      {/* FX cards with provenance */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {/* BOC */}
        <div className="rounded-2xl bg-white border border-slate-200 p-3.5">
          <p className="font-extrabold text-[13.5px] text-[#0f2a4a]">USD→CNY · Bank of China</p>
          <p className="text-[11px] text-slate-500 break-all">{fxRates?.boc?.source_url ?? "https://www.boc.cn/sourcedb/whpj/enindex_1619.html"}</p>
          <div className="mt-2 flex items-center gap-2">
            <span className={`text-[11px] font-bold px-2 py-1 rounded-full ${bocStatus === "OK" ? "bg-emerald-50 text-emerald-700 border border-emerald-200" : "bg-amber-50 text-amber-800 border border-amber-200"}`}>{bocStatus === "OK" ? "LIVE" : bocStatus}</span>
            {fxRates?.boc?.pub_time && <span className="text-[11px] text-slate-500">Pub {fmtText(fxRates.boc.pub_time)}</span>}
          </div>
          <div className="mt-2 text-[13px]">
            <div className="flex justify-between"><span className="text-slate-500">Buying Rate</span><span className="font-bold">{fxRates?.boc?.buying_rate != null ? fmtRate(fxRates.boc.buying_rate) : "—"}</span></div>
            <div className="flex justify-between"><span className="text-slate-500">Middle</span><span>{fxRates?.boc?.middle_rate != null ? fmtRate(fxRates.boc.middle_rate) : "—"}</span></div>
            <div className="flex justify-between font-bold text-[#0f2a4a]"><span>USD→CNY (Buying/100)</span><span>{effUsdToCny != null ? fmtRate(effUsdToCny) : "—"}</span></div>
          </div>
          <div className="mt-2">
            <label className="text-[12px] font-bold text-slate-600">Tỷ giá USD→CNY (nhập tay khi cần)</label>
            <input value={usdToCny} onChange={(e) => setUsdToCny(e.target.value)} placeholder={liveBocRate != null ? String(liveBocRate) : "6.68"} inputMode="decimal" className="mt-1 w-full rounded-xl border-2 border-slate-200 px-3 py-2.5 text-[15px] font-semibold focus:border-[#0f2a4a] focus:outline-none min-h-[48px]" />
            {bocStatus !== "OK" && <p className="text-[11px] text-amber-700 mt-1">LIVE không có — đang dùng MANUAL. Nguồn sẽ được lưu trong snapshot.</p>}
            {usdToCny !== "" && bocStatus === "OK" && <p className="text-[11px] text-blue-700 mt-1">Đang ghi đè LIVE bằng MANUAL — provenance sẽ ghi MANUAL.</p>}
          </div>
        </div>
        {/* Agribank */}
        <div className="rounded-2xl bg-white border border-slate-200 p-3.5">
          <p className="font-extrabold text-[13.5px] text-[#0f2a4a]">USD bán · Agribank</p>
          <p className="text-[11px] text-slate-500 break-all">{fxRates?.agribank?.source_url ?? "https://www.agribank.com.vn/vn/ty-gia"}</p>
          <div className="mt-2 flex items-center gap-2">
            <span className={`text-[11px] font-bold px-2 py-1 rounded-full ${agriStatus === "OK" ? "bg-emerald-50 text-emerald-700 border border-emerald-200" : "bg-amber-50 text-amber-800 border border-amber-200"}`}>{agriStatus === "OK" ? "LIVE" : agriStatus}</span>
            {fxRates?.agribank?.pub_time && <span className="text-[11px] text-slate-500">{fmtText(fxRates.agribank.pub_time)}</span>}
          </div>
          <div className="mt-2 flex justify-between text-[13px]"><span className="text-slate-500">Giá bán</span><span className="font-bold">{effAgri != null ? fmtVND(effAgri) : "—"}</span></div>
          <div className="mt-2">
            <label className="text-[12px] font-bold text-slate-600">USD bán VND (Agribank)</label>
            <input value={agriSell} onChange={(e) => setAgriSell(e.target.value)} placeholder={liveAgri != null ? String(liveAgri) : "26180"} inputMode="numeric" className="mt-1 w-full rounded-xl border-2 border-slate-200 px-3 py-2.5 text-[15px] font-semibold focus:border-[#0f2a4a] focus:outline-none min-h-[48px]" />
          </div>
        </div>
        {/* BIDV */}
        <div className="rounded-2xl bg-white border border-slate-200 p-3.5">
          <p className="font-extrabold text-[13.5px] text-[#0f2a4a]">USD bán · BIDV</p>
          <p className="text-[11px] text-slate-500 break-all">{fxRates?.bidv?.source_url ?? "https://bidv.com.vn/vn/ty-gia-ngoai-te/"}</p>
          <div className="mt-2 flex items-center gap-2">
            <span className={`text-[11px] font-bold px-2 py-1 rounded-full ${bidvStatus === "OK" && bidvRateStatus !== "UNAVAILABLE" ? "bg-emerald-50 text-emerald-700 border border-emerald-200" : "bg-red-50 text-red-700 border border-red-200"}`}>{bidvRateStatus === "UNAVAILABLE" ? "UNAVAILABLE" : bidvStatus}</span>
            {fxRates?.bidv?.pub_time && <span className="text-[11px] text-slate-500">{fmtText(fxRates.bidv.pub_time)}</span>}
          </div>
          {bidvRateStatus === "UNAVAILABLE" && <p className="text-[11px] text-red-700 mt-1">Không có nguồn JSON chính thức được chứng minh — hệ thống giữ MANUAL. Không dùng tỷ giá bên thứ ba.</p>}
          <div className="mt-2 flex justify-between text-[13px]"><span className="text-slate-500">Giá bán</span><span className="font-bold">{effBidv != null ? fmtVND(effBidv) : "—"}</span></div>
          <div className="mt-2">
            <label className="text-[12px] font-bold text-slate-600">USD bán VND (BIDV) — nhập tay</label>
            <input value={bidvSell} onChange={(e) => setBidvSell(e.target.value)} placeholder={liveBidv != null ? String(liveBidv) : "26180"} inputMode="numeric" className="mt-1 w-full rounded-xl border-2 border-slate-200 px-3 py-2.5 text-[15px] font-semibold focus:border-[#0f2a4a] focus:outline-none min-h-[48px]" />
            <p className="text-[11px] text-slate-500 mt-1">Để trống = RATE_UNAVAILABLE (kênh BIDV sẽ ẩn trong so sánh).</p>
          </div>
        </div>
      </div>

      {/* Editors per mode */}
      {mode === "A" ? (
        <div className="rounded-2xl bg-white border border-slate-200 p-4 space-y-3">
          <h3 className="font-extrabold text-[16px] text-[#0f2a4a]">Mode A — Tôi chuyển USD</h3>
          <div className="grid sm:grid-cols-2 gap-3">
            <div>
              <label className="text-[13px] font-bold text-slate-700">Số USD gửi (gross)</label>
              <input value={grossUsd} onChange={(e) => setGrossUsd(e.target.value)} inputMode="decimal" className="mt-1 w-full rounded-xl border-2 border-slate-200 px-3 py-3 text-[16px] font-bold focus:border-[#0f2a4a] focus:outline-none min-h-[52px]" placeholder="1500" />
            </div>
            <div>
              <label className="text-[13px] font-bold text-slate-700">Đại lý</label>
              <div className="mt-1 flex gap-2">
                <button onClick={() => setAgentRoute("CHINA")} className={`flex-1 min-h-[52px] rounded-xl border-2 font-bold text-[14px] ${agentRoute === "CHINA" ? "bg-[#0f2a4a] text-white border-[#0f2a4a]" : "bg-white border-slate-200"}`}>Trung Quốc</button>
                <button onClick={() => setAgentRoute("HONG_KONG")} className={`flex-1 min-h-[52px] rounded-xl border-2 font-bold text-[14px] ${agentRoute === "HONG_KONG" ? "bg-[#0f2a4a] text-white border-[#0f2a4a]" : "bg-white border-slate-200"}`}>Hong Kong</button>
              </div>
            </div>
            <div>
              <label className="text-[13px] font-bold text-slate-700">Ngân hàng VN (để tính VND)</label>
              <div className="mt-1 flex gap-2">
                <button onClick={() => setVnBank("AGRIBANK")} className={`flex-1 min-h-[48px] rounded-xl border-2 font-bold text-[13px] ${vnBank === "AGRIBANK" ? "bg-emerald-600 text-white border-emerald-600" : "bg-white border-slate-200"}`}>Agribank</button>
                <button onClick={() => setVnBank("BIDV")} className={`flex-1 min-h-[48px] rounded-xl border-2 font-bold text-[13px] ${vnBank === "BIDV" ? "bg-emerald-600 text-white border-emerald-600" : "bg-white border-slate-200"}`}>BIDV</button>
              </div>
            </div>
          </div>

          {previewA ? (
            <div className="rounded-xl bg-slate-50 border border-slate-200 p-3.5 space-y-2 text-[14px]">
              <div className="flex justify-between"><span className="text-slate-600">Sau phí NH người nhận (35 USD)</span><span className="font-bold">{fmtUSD(previewA.afterBank)}</span></div>
              {previewA.kind === "CHINA" ? (
                <>
                  <div className="flex justify-between"><span className="text-slate-600">Phí đại lý TQ ({(previewA as { trancheCount: number }).trancheCount} tranche × {effChinaFee} CNY)</span><span className="font-bold text-amber-700">{fmtCNY((previewA as { chinaFee: number }).chinaFee)}</span></div>
                  <div className="flex justify-between"><span className="text-slate-600">CNY trước phí</span><span>{fmtCNY((previewA as { grossCny: number }).grossCny)}</span></div>
                  <div className="flex justify-between font-extrabold text-[#0f2a4a] text-[15px] border-t pt-2"><span>CNY thực nhận</span><span>{fmtCNY((previewA as { net: number }).net)}</span></div>
                </>
              ) : (
                <>
                  <div className="flex justify-between"><span className="text-slate-600">Phí HK (2%)</span><span className="font-bold text-amber-700">{fmtUSD((previewA as { hkFee: number }).hkFee)}</span></div>
                  <div className="flex justify-between"><span className="text-slate-600">USD sau phí HK để quy đổi</span><span>{fmtUSD((previewA as { forConv: number }).forConv)}</span></div>
                  <div className="flex justify-between font-extrabold text-[#0f2a4a] text-[15px] border-t pt-2"><span>CNY thực nhận</span><span>{fmtCNY((previewA as { net: number }).net)}</span></div>
                </>
              )}
              {previewA.vnCost && (
                <div className="pt-2 border-t space-y-1">
                  <p className="font-bold text-[13px] text-slate-700">Chi phí VN (tạm tính):</p>
                  <div className="flex justify-between text-[13px]"><span>Gốc VND</span><span>{fmtVND(previewA.vnCost.principal)}</span></div>
                  <div className="flex justify-between text-[13px]"><span>SWIFT 5 USD</span><span>{fmtVND(previewA.vnCost.swift)}</span></div>
                  <div className="flex justify-between text-[13px]"><span>Phí NH 0.15%</span><span>{fmtVND(previewA.vnCost.pctFee)}</span></div>
                  <div className="flex justify-between font-extrabold"><span>Tổng VND</span><span>{fmtVND(previewA.vnCost.total)}</span></div>
                  <p className="text-[11px] text-slate-500">Chưa gồm VAT/phí khác — hiển thị đúng quy tắc được nhập.</p>
                </div>
              )}
              <p className="text-[11px] text-slate-500">Preview tại trình duyệt (số thực JS) — máy chủ sẽ tính lại bằng Decimal khi lưu.</p>
            </div>
          ) : (
            <div className="rounded-xl bg-amber-50 border border-amber-200 p-3 text-[13px] text-amber-900">Nhập gross USD và tỷ giá USD→CNY để xem preview.</div>
          )}
        </div>
      ) : (
        <div className="rounded-2xl bg-white border border-slate-200 p-4 space-y-3">
          <h3 className="font-extrabold text-[16px] text-[#0f2a4a]">Mode B — Đại lý cần nhận X CNY</h3>
          <div className="grid sm:grid-cols-2 gap-3">
            <div>
              <label className="text-[13px] font-bold text-slate-700">Mục tiêu CNY (target)</label>
              <input value={targetCny} onChange={(e) => setTargetCny(e.target.value)} inputMode="numeric" className="mt-1 w-full rounded-xl border-2 border-slate-200 px-3 py-3 text-[16px] font-bold focus:border-[#0f2a4a] focus:outline-none min-h-[52px]" placeholder="10000" />
              <p className="text-[11px] text-slate-500 mt-1">Ví dụ kiểm thử: 10,000</p>
            </div>
            <div>
              <label className="text-[13px] font-bold text-slate-700">Tỷ giá tệ ngoài (VND/CNY) — nhập tay</label>
              <input value={outsideRate} onChange={(e) => setOutsideRate(e.target.value)} inputMode="numeric" className="mt-1 w-full rounded-xl border-2 border-slate-200 px-3 py-3 text-[16px] font-bold focus:border-[#0f2a4a] focus:outline-none min-h-[52px]" placeholder="3900" />
              <p className="text-[11px] text-slate-500 mt-1">Ví dụ kiểm thử: 3,900</p>
            </div>
          </div>

          {previewB ? (
            <>
              <div className="overflow-x-auto -mx-1">
                <table className="w-full text-[13px] min-w-[760px] border-collapse">
                  <thead>
                    <tr className="bg-slate-50 text-slate-600">
                      <th className="text-left p-2.5 border">Kênh</th>
                      <th className="text-right p-2.5 border">Gross USD cần</th>
                      <th className="text-right p-2.5 border">Tổng VND</th>
                      <th className="text-right p-2.5 border">Δ vs tệ ngoài</th>
                      <th className="text-center p-2.5 border">Rẻ nhất</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr className={previewB.minTotal === previewB.outsideTotal ? "bg-emerald-50 font-bold" : ""}>
                      <td className="p-2.5 border">Tệ ngoài ({fmtRate(effOutside, " ₫/CNY")})</td>
                      <td className="text-right p-2.5 border">—</td>
                      <td className="text-right p-2.5 border font-bold">{fmtVND(previewB.outsideTotal)}</td>
                      <td className="text-right p-2.5 border">0 ₫</td>
                      <td className="text-center p-2.5 border">{previewB.minTotal === previewB.outsideTotal ? "★" : ""}</td>
                    </tr>
                    {[
                      { label: "USD→TQ via Agribank", d: previewB.chinaAgri },
                      { label: "USD→TQ via BIDV", d: previewB.chinaBidv },
                      { label: "USD→HK via Agribank", d: previewB.hkAgri },
                      { label: "USD→HK via BIDV", d: previewB.hkBidv },
                    ].map((row) => {
                      const data = row.d as { available: boolean; total: number | null; delta: number | null; gross: number | null; status: string };
                      const isCheapest = data.available && data.total != null && data.total === previewB.minTotal;
                      return (
                        <tr key={row.label} className={isCheapest ? "bg-emerald-50 font-bold" : ""}>
                          <td className="p-2.5 border">
                            {row.label}
                            {!data.available && <span className="ml-2 text-[11px] px-1.5 py-0.5 rounded bg-red-100 text-red-700 border border-red-200">RATE_UNAVAILABLE</span>}
                          </td>
                          <td className="text-right p-2.5 border">{data.gross != null ? fmtUSD(data.gross) : "—"}</td>
                          <td className="text-right p-2.5 border">{data.total != null ? fmtVND(data.total) : "—"}</td>
                          <td className={`text-right p-2.5 border ${data.delta != null && data.delta < 0 ? "text-emerald-700" : data.delta != null && data.delta > 0 ? "text-red-600" : ""}`}>{data.delta != null ? (data.delta > 0 ? "+" : "") + fmtVND(data.delta) : "—"}</td>
                          <td className="text-center p-2.5 border">{isCheapest ? "★ rẻ nhất" : ""}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
              <div className="rounded-xl bg-blue-50 border border-blue-200 p-3 text-[13px] leading-snug">
                <p className="font-bold text-blue-900">Ghi chú công thức (lưu cùng snapshot):</p>
                <ul className="list-disc pl-5 mt-1 space-y-0.5 text-blue-800">
                  <li>TQ: gross = (target + phí_tranche)/rate + 35 — phí 150 CNY / tranche 10k USD, làm tròn lên.</li>
                  <li>HK: gross = target / (rate×0.98) + 35 — phí 2% trên USD sau 35.</li>
                  <li>VN: tổng = principal + 5×sell + principal×0.15% — không tự thêm VAT.</li>
                  <li>Hiển thị làm tròn 2 USD / nguyên VND; lưu tính bằng Decimal độ chính xác cao.</li>
                </ul>
                <p className="text-[11px] text-blue-700 mt-2">Bảng giữ đủ 5 kênh — dòng RATE_UNAVAILABLE vẫn hiển thị để không che giấu.</p>
              </div>
              <details className="rounded-xl bg-slate-50 border p-3">
                <summary className="font-bold text-[13px] cursor-pointer">Chi tiết tranche / phí (để kiểm tính)</summary>
                <div className="mt-2 text-[12.5px] space-y-1">
                  <div>China gross cần: {fmtUSD(previewB.chinaGross)} — tranche {Math.ceil(previewB.chinaGross / effTrancheSize)} × {effChinaFee} CNY = {fmtCNY(Math.ceil(previewB.chinaGross / effTrancheSize) * effChinaFee)}</div>
                  <div>HK gross cần: {fmtUSD(previewB.hkGross)} — phí HK {fmtUSD((previewB.hkGross - 35) * effHkPct)}</div>
                  <div>Tệ ngoài: {fmtCNY(effTarget)} × {fmtRate(effOutside)} = {fmtVND(previewB.outsideTotal)}</div>
                </div>
              </details>
            </>
          ) : (
            <div className="rounded-xl bg-amber-50 border border-amber-200 p-3 text-[13px] text-amber-900">Nhập target CNY, tệ ngoài và tỷ giá để xem so sánh 5 kênh. Ví dụ deterministic: target 10,000, outside 3,900, USD→CNY 6.68, Agribank 26,180.</div>
          )}
        </div>
      )}

      {/* Fee assumptions */}
      <div className="rounded-2xl bg-white border border-slate-200 p-3">
        <button onClick={() => setShowFees((v) => !v)} className="w-full flex items-center justify-between min-h-[48px] font-bold text-[14px] text-[#0f2a4a]">
          <span>⚙️ Quy tắc phí (cho xem/sửa — lưu cùng snapshot)</span>
          <span className="text-[18px]">{showFees ? "−" : "+"}</span>
        </button>
        {showFees && (
          <div className="grid sm:grid-cols-3 gap-3 mt-3">
            <div>
              <label className="text-[12px] font-bold text-slate-600">Phí NH người nhận (USD)</label>
              <input value={recipientFee} onChange={(e) => setRecipientFee(e.target.value)} className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2.5 text-[14px] min-h-[48px]" />
            </div>
            <div>
              <label className="text-[12px] font-bold text-slate-600">Phí TQ / tranche (CNY)</label>
              <input value={chinaFeePerTranche} onChange={(e) => setChinaFeePerTranche(e.target.value)} className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2.5 text-[14px] min-h-[48px]" />
            </div>
            <div>
              <label className="text-[12px] font-bold text-slate-600">Cỡ tranche (USD)</label>
              <input value={chinaTrancheSize} onChange={(e) => setChinaTrancheSize(e.target.value)} className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2.5 text-[14px] min-h-[48px]" />
            </div>
            <div>
              <label className="text-[12px] font-bold text-slate-600">Phí HK (%)</label>
              <input value={hkPctStr} onChange={(e) => setHkPctStr(e.target.value)} className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2.5 text-[14px] min-h-[48px]" />
            </div>
            <div>
              <label className="text-[12px] font-bold text-slate-600">SWIFT VN (USD)</label>
              <input value={vnSwift} onChange={(e) => setVnSwift(e.target.value)} className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2.5 text-[14px] min-h-[48px]" />
            </div>
            <div>
              <label className="text-[12px] font-bold text-slate-600">Phí NH VN (%)</label>
              <input value={vnPctStr} onChange={(e) => setVnPctStr(e.target.value)} className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2.5 text-[14px] min-h-[48px]" />
            </div>
            <p className="sm:col-span-3 text-[11px] text-slate-500">Mặc định: 35 USD nhận, 150 CNY/tranche 10k, HK 2%, SWIFT 5 USD, VN 0.15%. Sửa ở đây sẽ được ghi provenance và dùng khi tính lại ở server.</p>
          </div>
        )}
      </div>

      {/* Save */}
      <div className="rounded-2xl bg-white border border-slate-200 p-3">
        <button onClick={handleSave} className="w-full min-h-[56px] rounded-xl bg-[#0f2a4a] text-white font-extrabold text-[16px] shadow">💾 LƯU SNAPSHOT (bất biến)</button>
        <p className="text-[11px] text-slate-500 mt-2 leading-snug">Lưu toàn bộ: inputs, tỷ giá, nguồn, thời gian publish/captured, quy tắc phí, công thức 1.0.0, outputs. Snapshot mới không ghi đè cái cũ — tỷ giá sau này đổi không làm thay lịch sử.</p>
      </div>

      {/* History */}
      <div className="rounded-2xl bg-white border border-slate-200 p-4">
        <h4 className="font-extrabold text-[15px] text-[#0f2a4a]">Lịch sử snapshot (bất biến) — {snapshots.length} bản</h4>
        {snapshots.length === 0 ? (
          <p className="text-[13px] text-slate-500 mt-2">Chưa có snapshot nào cho hợp đồng này. Tính xong bấm “LƯU SNAPSHOT”.</p>
        ) : (
          <div className="space-y-2 mt-3">
            {snapshots.map((sn) => (
              <details key={sn.id} className="rounded-xl border border-slate-200 p-3 bg-slate-50">
                <summary className="font-bold text-[13px] cursor-pointer">
                  {sn.id} · {sn.mode === "A" ? "A · Tôi chuyển USD" : "B · Đại lý cần nhận"} · {new Date(sn.created_at).toLocaleString("vi-VN")} · v{sn.formula_version}
                </summary>
                <div className="mt-2 text-[12.5px] space-y-1">
                  <div><span className="font-semibold">Inputs:</span> <span className="font-mono text-[11px] break-all">{JSON.stringify(sn.inputs)}</span></div>
                  <div><span className="font-semibold">FX:</span> <span className="font-mono text-[11px] break-all">{JSON.stringify(sn.fx)}</span></div>
                  <div><span className="font-semibold">Fee rules:</span> <span className="font-mono text-[11px] break-all">{JSON.stringify(sn.fee_rules)}</span></div>
                  <div><span className="font-semibold">Outputs:</span> <pre className="bg-white border rounded-lg p-2 overflow-auto text-[11px] max-h-[320px]">{JSON.stringify(sn.outputs, null, 2)}</pre></div>
                  <div className="text-[11px] text-slate-500">Lưu bởi {fmtText((sn as unknown as { created_by?: string }).created_by)} — bất biến, không sửa/xóa.</div>
                </div>
              </details>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
