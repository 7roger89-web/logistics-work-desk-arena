// LOGI_CONTRACT_INTL_PAYMENT_COMPARATOR_01 — Thanh toán quốc tế comparator
// Vietnamese-first, mobile-friendly, decision-support only (no money transfer).
import { useMemo, useState, useEffect, useRef } from "react";
import { useStore } from "../lib/store";
import type { Contract, IntlFxRates, IntlSnapshot } from "../lib/viewmodel";
import { fmtMoney, fmtText } from "../lib/format";

type SourceKind = "LIVE" | "MANUAL" | "UNAVAILABLE";

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
  const [mode, setMode] = useState<"A" | "B">("B");

  const liveBocRate = fxRates?.boc?.usd_to_cny ?? null;
  const liveAgri = fxRates?.agribank?.usd_sell_vnd ?? fxRates?.agribank?.sell ?? null;
  const liveBidv = fxRates?.bidv?.usd_sell_vnd ?? fxRates?.bidv?.sell ?? null;
  const bocStatus = fxRates?.boc?.status ?? "RATE_UNAVAILABLE";
  const agriStatus = fxRates?.agribank?.status ?? "RATE_UNAVAILABLE";
  const bidvStatus = fxRates?.bidv?.status ?? "RATE_UNAVAILABLE";
  const bidvRateStatus = (fxRates?.bidv as unknown as { bidv_rate_status?: string })?.bidv_rate_status ?? bidvStatus;

  // --- Per-rate explicit provenance state: LIVE | MANUAL | UNAVAILABLE ---
  const [usdValue, setUsdValue] = useState<string>("");
  const [usdKind, setUsdKind] = useState<SourceKind>("UNAVAILABLE");
  const [agriValue, setAgriValue] = useState<string>("");
  const [agriKind, setAgriKind] = useState<SourceKind>("UNAVAILABLE");
  const [bidvValue, setBidvValue] = useState<string>("");
  const [bidvKind, setBidvKind] = useState<SourceKind>("UNAVAILABLE");
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

  // Track operator editing flags to keep LIVE seeding from overwriting MANUAL
  const hasManuallyEditedUsd = useRef(false);
  const hasManuallyEditedAgri = useRef(false);
  const hasManuallyEditedBidv = useRef(false);

  // Seed LIVE only when: kind is UNAVAILABLE or LIVE and user never manually edited, or value empty and live available
  useEffect(() => {
    if (liveBocRate != null && !hasManuallyEditedUsd.current) {
      const liveStr = String(liveBocRate);
      // Only seed if currently not MANUAL, or if value empty / equals previous live
      if (usdKind !== "MANUAL") {
        setUsdValue(liveStr);
        setUsdKind(bocStatus === "OK" ? "LIVE" : "UNAVAILABLE");
      } else if (usdValue === "" ) {
        setUsdValue(liveStr);
        setUsdKind(bocStatus === "OK" ? "LIVE" : "UNAVAILABLE");
      }
    } else if (liveBocRate == null && usdKind === "LIVE") {
      setUsdKind("UNAVAILABLE");
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [liveBocRate, bocStatus]);

  useEffect(() => {
    if (liveAgri != null && !hasManuallyEditedAgri.current) {
      const liveStr = String(liveAgri);
      if (agriKind !== "MANUAL") {
        setAgriValue(liveStr);
        setAgriKind(agriStatus === "OK" ? "LIVE" : "UNAVAILABLE");
      }
    } else if (liveAgri == null && agriKind === "LIVE") {
      setAgriKind("UNAVAILABLE");
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [liveAgri, agriStatus]);

  useEffect(() => {
    if (liveBidv != null && !hasManuallyEditedBidv.current) {
      const liveStr = String(liveBidv);
      if (bidvKind !== "MANUAL") {
        setBidvValue(liveStr);
        // BIDV truthful: if live reports UNAVAILABLE, seeding should stay UNAVAILABLE even if numeric present (html fallback not official)
        const isLive = bidvStatus === "OK" && bidvRateStatus !== "UNAVAILABLE";
        setBidvKind(isLive ? "LIVE" : "UNAVAILABLE");
        if (!isLive && liveBidv != null) {
          // keep UNAVAILABLE provenance even though value exists in HTML fallback — manual required
          // Leave value empty to force manual? But we seeded numeric; better keep UNAVAILABLE and show manual hint
          // So keep value as typed but kind UNAVAILABLE
        }
      }
    } else if (liveBidv == null && bidvKind === "LIVE") {
      setBidvKind("UNAVAILABLE");
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [liveBidv, bidvStatus, bidvRateStatus]);

  const handleUsdChange = (v: string) => {
    if (v !== "") {
      setUsdValue(v);
      setUsdKind("MANUAL");
      hasManuallyEditedUsd.current = true;
      return;
    }
    // cleared — revert to LIVE if available else UNAVAILABLE
    if (liveBocRate != null && bocStatus === "OK") {
      setUsdValue(String(liveBocRate));
      setUsdKind("LIVE");
      hasManuallyEditedUsd.current = false;
    } else {
      setUsdValue("");
      setUsdKind("UNAVAILABLE");
      hasManuallyEditedUsd.current = true;
    }
  };
  const handleAgriChange = (v: string) => {
    setAgriValue(v);
    hasManuallyEditedAgri.current = true;
    if (v !== "") setAgriKind("MANUAL");
    else {
      if (liveAgri != null && agriStatus === "OK") { setAgriKind("LIVE"); hasManuallyEditedAgri.current = false; setAgriValue(String(liveAgri)); }
      else setAgriKind("UNAVAILABLE");
    }
  };
  const handleBidvChange = (v: string) => {
    setBidvValue(v);
    hasManuallyEditedBidv.current = true;
    if (v !== "") setBidvKind("MANUAL");
    else {
      const isLive = liveBidv != null && bidvStatus === "OK" && bidvRateStatus !== "UNAVAILABLE";
      if (isLive) { setBidvKind("LIVE"); hasManuallyEditedBidv.current = false; setBidvValue(String(liveBidv)); }
      else setBidvKind("UNAVAILABLE");
    }
  };

  const resetUsdToLive = () => {
    if (liveBocRate != null) {
      setUsdValue(String(liveBocRate));
      setUsdKind(bocStatus === "OK" ? "LIVE" : "UNAVAILABLE");
      hasManuallyEditedUsd.current = false;
    }
  };
  const resetAgriToLive = () => {
    if (liveAgri != null) {
      setAgriValue(String(liveAgri));
      setAgriKind(agriStatus === "OK" ? "LIVE" : "UNAVAILABLE");
      hasManuallyEditedAgri.current = false;
    }
  };
  const resetBidvToLive = () => {
    if (liveBidv != null && bidvStatus === "OK" && bidvRateStatus !== "UNAVAILABLE") {
      setBidvValue(String(liveBidv));
      setBidvKind("LIVE");
      hasManuallyEditedBidv.current = false;
    }
  };

  // Effective numbers for preview — MANUAL value wins, else live fallback, else null
  const effUsdToCny = useMemo(() => {
    const manual = numOrNull(usdValue);
    if (usdKind === "MANUAL" && manual != null) return manual;
    if (usdKind === "LIVE" && manual != null) return manual; // seeded live
    return manual ?? liveBocRate ?? null;
  }, [usdValue, usdKind, liveBocRate]);
  const effAgri = useMemo(() => {
    const manual = numOrNull(agriValue);
    if (agriKind === "MANUAL" && manual != null) return manual;
    if (agriKind === "LIVE" && manual != null) return manual;
    return manual ?? liveAgri ?? null;
  }, [agriValue, agriKind, liveAgri]);
  const effBidv = useMemo(() => {
    const manual = numOrNull(bidvValue);
    if (bidvKind === "MANUAL" && manual != null) return manual;
    if (bidvKind === "LIVE" && manual != null) return manual;
    // For BIDV when UNAVAILABLE, do not fallback to html live value — require MANUAL
    if (bidvKind === "UNAVAILABLE") return manual;
    return manual ?? liveBidv ?? null;
  }, [bidvValue, bidvKind, liveBidv]);
  const effOutside = useMemo(() => numOrNull(outsideRate), [outsideRate]);
  const effGross = useMemo(() => numOrNull(grossUsd), [grossUsd]);
  const effTarget = useMemo(() => numOrNull(targetCny), [targetCny]);
  const effRecipient = useMemo(() => {
    const v = numOrNull(recipientFee);
    return v !== null ? v : 35;
  }, [recipientFee]);
  const effChinaFee = useMemo(() => {
    const v = numOrNull(chinaFeePerTranche);
    return v !== null ? v : 150;
  }, [chinaFeePerTranche]);
  const effTrancheSize = useMemo(() => {
    const v = numOrNull(chinaTrancheSize);
    return v !== null ? v : 10000;
  }, [chinaTrancheSize]);
  const effHkPct = useMemo(() => {
    const v = numOrNull(hkPctStr);
    if (v == null) return 0.02;
    return v / 100;
  }, [hkPctStr]);
  const effVnSwift = useMemo(() => {
    const v = numOrNull(vnSwift);
    return v !== null ? v : 5;
  }, [vnSwift]);
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

  const buildProvenance = (kind: SourceKind, effectiveStr: string, effectiveNum: number | null, liveObj: unknown) => {
    const now = new Date().toISOString();
    if (kind === "LIVE" && liveObj && typeof liveObj === "object" && (liveObj as { status?: string }).status === "OK") {
      return liveObj as Record<string, unknown>;
    }
    if (kind === "UNAVAILABLE" && effectiveNum == null) {
      return { status: "RATE_UNAVAILABLE", source: "UNAVAILABLE", source_url: (liveObj as { source_url?: string })?.source_url ?? "manual", captured_at: now, reason: "source unavailable and no manual value" };
    }
    // MANUAL — truthful manual provenance with live_reference
    const base: Record<string, unknown> = {
      status: "MANUAL",
      source: "MANUAL",
      source_url: "manual",
      value: effectiveStr,
      captured_at: now,
    };
    // Preserve effective numeric in known keys for server verification
    if (effectiveNum != null) {
      // Provide both generic value and per-rate key
      base["value"] = effectiveStr;
    }
    if (liveObj && typeof liveObj === "object") {
      base["live_reference"] = liveObj;
    }
    return base;
  };

  const handleSave = () => {
    const requestId = `req-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
    // Effective strings for provenance — what calculation actually used
    const effUsdStr = effUsdToCny != null ? String(effUsdToCny) : usdValue;
    const effAgriStr = effAgri != null ? String(effAgri) : agriValue;
    const effBidvStr = effBidv != null ? String(effBidv) : bidvValue;

    const fxBocProv = buildProvenance(usdKind, effUsdStr, effUsdToCny, fxRates?.boc ?? null);
    // attach expected key for server verification
    (fxBocProv as Record<string, unknown>)["usd_to_cny"] = effUsdStr;
    const fxAgriProv = buildProvenance(agriKind, effAgriStr, effAgri, fxRates?.agribank ?? null);
    (fxAgriProv as Record<string, unknown>)["usd_sell_vnd"] = effAgriStr;
    (fxAgriProv as Record<string, unknown>)["sell"] = effAgriStr;
    const fxBidvProv = buildProvenance(bidvKind, effBidvStr, effBidv, fxRates?.bidv ?? null);
    (fxBidvProv as Record<string, unknown>)["usd_sell_vnd"] = effBidvStr;
    (fxBidvProv as Record<string, unknown>)["sell"] = effBidvStr;

    const payload: Record<string, unknown> = {
      contractId: contract.id,
      requestId,
      mode,
      usd_to_cny: effUsdStr,
      agribank_sell_vnd: effAgriStr,
      bidv_sell_vnd: bidvValue !== "" ? effBidvStr : "",
      outside_cny_vnd: outsideRate,
      recipient_bank_fee_usd: recipientFee,
      china_fee_per_tranche_cny: chinaFeePerTranche,
      china_tranche_size_usd: chinaTrancheSize,
      hk_fee_pct: String(effHkPct),
      vn_swift_fee_usd: vnSwift,
      vn_pct_fee: String(effVnPct),
      // Explicit provenance truth
      fxBoc: fxBocProv,
      fxAgribank: fxAgriProv,
      fxBidv: fxBidvProv,
      usdCnySourceKind: usdKind,
      agribankSourceKind: agriKind,
      bidvSourceKind: bidvKind,
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
      const ok2 = dispatch("contract_payment_snapshot_save", payload);
      if (!ok2) {
        toast("Không gửi được", "Component chưa kết nối backend.", "red");
        return;
      }
    }
    toast("Đã gửi lưu snapshot", "Máy chủ sẽ tính lại bằng Decimal và lưu bất biến.", "blue");
  };

  const snapshots: IntlSnapshot[] = (contract as unknown as { intlSnapshots?: IntlSnapshot[] }).intlSnapshots ?? [];

  // Helper to render kind badge
  const kindBadge = (kind: SourceKind, status: string) => {
    if (kind === "LIVE" && status === "OK") return <span className="text-[11px] font-bold px-2 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">LIVE</span>;
    if (kind === "MANUAL") return <span className="text-[11px] font-bold px-2 py-1 rounded-full bg-blue-50 text-blue-700 border border-blue-200">MANUAL</span>;
    return <span className="text-[11px] font-bold px-2 py-1 rounded-full bg-red-50 text-red-700 border border-red-200">UNAVAILABLE</span>;
  };

  return (
    <div className="space-y-4">
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

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <div className="rounded-2xl bg-white border border-slate-200 p-3.5">
          <p className="font-extrabold text-[13.5px] text-[#0f2a4a]">USD→CNY · Bank of China</p>
          <p className="text-[11px] text-slate-500 break-all">{fxRates?.boc?.source_url ?? "https://www.boc.cn/sourcedb/whpj/enindex_1619.html"}</p>
          <div className="mt-2 flex items-center gap-2">
            {kindBadge(usdKind, bocStatus)}
            {fxRates?.boc?.pub_time && <span className="text-[11px] text-slate-500">Pub {fmtText(fxRates.boc.pub_time)}</span>}
            {usdKind === "LIVE" && <span className="text-[11px] text-emerald-700">● đang dùng LIVE</span>}
            {usdKind === "MANUAL" && liveBocRate != null && <span className="text-[11px] text-blue-700">● ghi đè MANUAL</span>}
          </div>
          <div className="mt-2 text-[13px]">
            <div className="flex justify-between"><span className="text-slate-500">Buying Rate</span><span className="font-bold">{fxRates?.boc?.buying_rate != null ? fmtRate(fxRates.boc.buying_rate) : "—"}</span></div>
            <div className="flex justify-between"><span className="text-slate-500">Middle</span><span>{fxRates?.boc?.middle_rate != null ? fmtRate(fxRates.boc.middle_rate) : "—"}</span></div>
            <div className="flex justify-between font-bold text-[#0f2a4a]"><span>USD→CNY (Buying/100)</span><span>{effUsdToCny != null ? fmtRate(effUsdToCny) : "—"}</span></div>
          </div>
          <div className="mt-2">
            <label className="text-[12px] font-bold text-slate-600">Tỷ giá USD→CNY {usdKind === "LIVE" ? "(LIVE)" : "(MANUAL khi sửa)"}</label>
            <div className="flex gap-2">
              <input value={usdValue} onChange={(e) => handleUsdChange(e.target.value)} placeholder={liveBocRate != null ? String(liveBocRate) : "6.68"} inputMode="decimal" className="mt-1 flex-1 rounded-xl border-2 border-slate-200 px-3 py-2.5 text-[15px] font-semibold focus:border-[#0f2a4a] focus:outline-none min-h-[48px]" />
              {usdKind === "MANUAL" && liveBocRate != null && <button onClick={resetUsdToLive} className="mt-1 px-3 rounded-xl border-2 border-blue-200 bg-blue-50 text-blue-700 text-[12px] font-bold min-h-[48px]">Dùng LIVE</button>}
            </div>
            {bocStatus !== "OK" && <p className="text-[11px] text-amber-700 mt-1">LIVE không có — đang dùng {usdKind} . Nguồn sẽ được lưu trong snapshot.</p>}
            {usdKind === "MANUAL" && bocStatus === "OK" && <p className="text-[11px] text-blue-700 mt-1">Đã chỉnh MANUAL — provenance sẽ ghi MANUAL + live_reference.</p>}
            {usdKind === "LIVE" && <p className="text-[11px] text-emerald-700 mt-1">Đang dùng LIVE seeded — provenance LIVE.</p>}
          </div>
        </div>
        <div className="rounded-2xl bg-white border border-slate-200 p-3.5">
          <p className="font-extrabold text-[13.5px] text-[#0f2a4a]">USD bán · Agribank</p>
          <p className="text-[11px] text-slate-500 break-all">{fxRates?.agribank?.source_url ?? "https://www.agribank.com.vn/vn/ty-gia"}</p>
          <div className="mt-2 flex items-center gap-2">
            {kindBadge(agriKind, agriStatus)}
            {fxRates?.agribank?.pub_time && <span className="text-[11px] text-slate-500">{fmtText(fxRates.agribank.pub_time)}</span>}
            {agriKind === "LIVE" && <span className="text-[11px] text-emerald-700">● LIVE</span>}
            {agriKind === "MANUAL" && <span className="text-[11px] text-blue-700">● MANUAL</span>}
          </div>
          <div className="mt-2 flex justify-between text-[13px]"><span className="text-slate-500">Giá bán</span><span className="font-bold">{effAgri != null ? fmtVND(effAgri) : "—"}</span></div>
          <div className="mt-2">
            <label className="text-[12px] font-bold text-slate-600">USD bán VND (Agribank) {agriKind === "LIVE" ? "(LIVE)" : ""}</label>
            <div className="flex gap-2">
              <input value={agriValue} onChange={(e) => handleAgriChange(e.target.value)} placeholder={liveAgri != null ? String(liveAgri) : "26180"} inputMode="numeric" className="mt-1 flex-1 rounded-xl border-2 border-slate-200 px-3 py-2.5 text-[15px] font-semibold focus:border-[#0f2a4a] focus:outline-none min-h-[48px]" />
              {agriKind === "MANUAL" && liveAgri != null && <button onClick={resetAgriToLive} className="mt-1 px-3 rounded-xl border-2 border-blue-200 bg-blue-50 text-blue-700 text-[12px] font-bold min-h-[48px]">Dùng LIVE</button>}
            </div>
            {agriKind === "MANUAL" && <p className="text-[11px] text-blue-700 mt-1">MANUAL — sẽ lưu MANUAL + live_reference nếu có.</p>}
          </div>
        </div>
        <div className="rounded-2xl bg-white border border-slate-200 p-3.5">
          <p className="font-extrabold text-[13.5px] text-[#0f2a4a]">USD bán · BIDV</p>
          <p className="text-[11px] text-slate-500 break-all">{fxRates?.bidv?.source_url ?? "https://bidv.com.vn/vn/ty-gia-ngoai-te/"}</p>
          <div className="mt-2 flex items-center gap-2">
            <span className={`text-[11px] font-bold px-2 py-1 rounded-full ${bidvKind === "LIVE" ? "bg-emerald-50 text-emerald-700 border border-emerald-200" : bidvKind === "MANUAL" ? "bg-blue-50 text-blue-700 border border-blue-200" : "bg-red-50 text-red-700 border border-red-200"}`}>{bidvKind === "LIVE" ? "LIVE" : bidvKind === "MANUAL" ? "MANUAL" : "UNAVAILABLE"}</span>
            {fxRates?.bidv?.pub_time && <span className="text-[11px] text-slate-500">{fmtText(fxRates.bidv.pub_time)}</span>}
          </div>
          {bidvRateStatus === "UNAVAILABLE" && <p className="text-[11px] text-red-700 mt-1">Không có nguồn JSON chính thức — LIVE UNAVAILABLE, hãy nhập MANUAL.</p>}
          <div className="mt-2 flex justify-between text-[13px]"><span className="text-slate-500">Giá bán</span><span className="font-bold">{effBidv != null ? fmtVND(effBidv) : "—"}</span></div>
          <div className="mt-2">
            <label className="text-[12px] font-bold text-slate-600">USD bán VND (BIDV) — nhập tay</label>
            <div className="flex gap-2">
              <input value={bidvValue} onChange={(e) => handleBidvChange(e.target.value)} placeholder={liveBidv != null ? String(liveBidv) : "26180"} inputMode="numeric" className="mt-1 flex-1 rounded-xl border-2 border-slate-200 px-3 py-2.5 text-[15px] font-semibold focus:border-[#0f2a4a] focus:outline-none min-h-[48px]" />
              {bidvKind === "MANUAL" && bidvRateStatus !== "UNAVAILABLE" && liveBidv != null && <button onClick={resetBidvToLive} className="mt-1 px-3 rounded-xl border-2 border-blue-200 bg-blue-50 text-blue-700 text-[12px] font-bold min-h-[48px]">Dùng LIVE</button>}
            </div>
            <p className="text-[11px] text-slate-500 mt-1">{bidvKind === "UNAVAILABLE" && !bidvValue ? "Chưa nhập MANUAL — kênh BIDV = RATE_UNAVAILABLE." : bidvKind === "MANUAL" ? "MANUAL truth — sẽ lưu MANUAL." : "Để trống = RATE_UNAVAILABLE."}</p>
          </div>
        </div>
      </div>

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
                </ul>
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

      <div className="rounded-2xl bg-white border border-slate-200 p-3">
        <button onClick={() => setShowFees((v) => !v)} className="w-full flex items-center justify-between min-h-[48px] font-bold text-[14px] text-[#0f2a4a]">
          <span>⚙️ Quy tắc phí (cho xem/sửa — lưu cùng snapshot) — 0 là hợp lệ</span>
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
            <p className="sm:col-span-3 text-[11px] text-slate-500">0 là giá trị hợp lệ (đã sửa falsy → null-aware). Sửa ở đây sẽ được ghi provenance và dùng khi tính lại ở server với validation ≥0, tranche {">"}0, HK {"<"}100%.</p>
          </div>
        )}
      </div>

      <div className="rounded-2xl bg-white border border-slate-200 p-3">
        <button onClick={handleSave} className="w-full min-h-[56px] rounded-xl bg-[#0f2a4a] text-white font-extrabold text-[16px] shadow">💾 LƯU SNAPSHOT (bất biến)</button>
        <p className="text-[11px] text-slate-500 mt-2 leading-snug">Lưu toàn bộ: inputs, tỷ giá với provenance LIVE/MANUAL/UNAVAILABLE, quy tắc phí, công thức 1.0.0, outputs. Snapshot mới không ghi đè cái cũ.</p>
      </div>

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
                </div>
              </details>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
