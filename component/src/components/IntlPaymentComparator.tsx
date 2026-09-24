// ============================================================================
// LOGI_INTL_PAYMENT_STANDALONE_TOOL_01 (Issue #109) — Thanh toán quốc tế.
//
// A stateless CALCULATOR mounted by the standalone page /thanh-toan-quoc-te
// (sidebar group CÔNG CỤ). It takes inputs and returns money. It is NOT a
// payment workflow, a money transfer, a contract record, an accounting entry
// or a snapshot archive: it imports no store/dispatcher, emits no event and
// persists nothing. Every value is local component state and is discarded on
// refresh/navigation.
//
// The formulas are the ones LOGI_CONTRACT_INTL_PAYMENT_COMPARATOR_01 already
// shipped (core/intl_payment_calculator.py mirrors them server-side); only
// where their inputs come from changed:
//   * "Tự nhập toàn bộ thông số" OFF — a rate is used only when its existing
//     projection status is genuinely OK (BOC USD→CNY, Agribank / BIDV USD
//     sell). BIDV with bidv_rate_status=UNAVAILABLE stays UNAVAILABLE: its
//     HTML fallback is never promoted to LIVE. Fees are the standard rules,
//     shown read-only so nothing hidden moves the result.
//   * ON — EVERY numeric assumption is a visible editable field and the
//     formula uses exactly the visible value. Blank/invalid is UNKNOWN, never
//     0: the dependent result renders "—" with a hint naming what is missing.
// ============================================================================

import { useState } from "react";
import type { IntlFxRates } from "../lib/viewmodel";
import { cx } from "../lib/format";

type Mode = "A" | "B";
type Route = "CHINA" | "HONG_KONG";
type Bank = "AGRIBANK" | "BIDV";
type Source = "LIVE" | "UNAVAILABLE" | "DEFAULT" | "MANUAL";
type Problem = "unavailable" | "missing" | "invalid";
type ParamKey =
  | "usdCny"
  | "agriSell"
  | "bidvSell"
  | "outsideRate"
  | "recipientFee"
  | "chinaFee"
  | "trancheSize"
  | "hkPct"
  | "vnSwift"
  | "vnPct";
type LiveKey = "usdCny" | "agriSell" | "bidvSell";

interface ParamDef {
  key: ParamKey;
  label: string;
  unit: string;
  /** positive: > 0 · nonNegative: >= 0 (0 is a real fee) · percent: 0 <= x < 100 */
  rule: "positive" | "nonNegative" | "percent";
  /** Standard fee rule — the same defaults as core/intl_payment_calculator.py. Rates have none. */
  standard?: string;
  note?: string;
}

// Every numeric assumption the formulas read. In manual mode each one is a
// visible editable field; nothing outside this list moves a result.
const PARAMS: ParamDef[] = [
  { key: "usdCny", label: "Tỷ giá USD→CNY", unit: "CNY/USD", rule: "positive" },
  { key: "agriSell", label: "Agribank bán USD", unit: "VND/USD", rule: "positive" },
  { key: "bidvSell", label: "BIDV bán USD", unit: "VND/USD", rule: "positive" },
  { key: "outsideRate", label: "CNY ngoài", unit: "VND/CNY", rule: "positive", note: "Chỉ dùng ở chế độ B (so sánh tệ ngoài)." },
  { key: "recipientFee", label: "Phí ngân hàng người nhận", unit: "USD", rule: "nonNegative", standard: "35" },
  { key: "chinaFee", label: "Phí đại lý Trung Quốc mỗi tranche", unit: "CNY", rule: "nonNegative", standard: "150", note: "Chỉ dùng cho đại lý Trung Quốc." },
  { key: "trancheSize", label: "Kích thước tranche", unit: "USD", rule: "positive", standard: "10000", note: "Chỉ dùng cho đại lý Trung Quốc." },
  { key: "hkPct", label: "Phí Hong Kong", unit: "%", rule: "percent", standard: "2", note: "Chỉ dùng cho đại lý Hong Kong." },
  { key: "vnSwift", label: "Phí SWIFT Việt Nam", unit: "USD", rule: "nonNegative", standard: "5" },
  { key: "vnPct", label: "Phí ngân hàng Việt Nam", unit: "%", rule: "percent", standard: "0.15" },
];
const PARAM = Object.fromEntries(PARAMS.map((p) => [p.key, p])) as Record<ParamKey, ParamDef>;
const LIVE_SOURCE: Record<LiveKey, string> = { usdCny: "Bank of China", agriSell: "Agribank", bidvSell: "BIDV" };
const RULE_TEXT: Record<ParamDef["rule"], string> = {
  positive: "phải lớn hơn 0",
  nonNegative: "không được âm (0 là hợp lệ)",
  percent: "từ 0 đến dưới 100",
};

// --- parsing / formatting (unchanged semantics: "," and spaces are grouping) ---

function numOrNull(v: string): number | null {
  if (v == null || v === "") return null;
  const t = String(v).replace(/,/g, "").replace(/\s/g, "").trim();
  if (!t) return null;
  const n = Number(t);
  return Number.isFinite(n) ? n : null;
}
function positiveNumber(v: unknown): number | null {
  const n = typeof v === "number" ? v : typeof v === "string" ? numOrNull(v) : null;
  return n != null && Number.isFinite(n) && n > 0 ? n : null;
}
function fmt2(n: number): string {
  return n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}
function fmtVndNum(n: number): string {
  return Math.round(n).toLocaleString("vi-VN");
}
function fmtRate(n: number): string {
  return n.toLocaleString("en-US", { maximumFractionDigits: 4 });
}
function fmtVndRate(n: number): string {
  return n.toLocaleString("vi-VN", { maximumFractionDigits: 2 });
}
function fmtParam(key: ParamKey, n: number): string {
  if (key === "agriSell" || key === "bidvSell" || key === "outsideRate") return `${fmtVndRate(n)} ${PARAM[key].unit}`;
  if (key === "usdCny") return `${fmtRate(n)} ${PARAM[key].unit}`;
  if (PARAM[key].unit === "%") return `${n.toLocaleString("en-US", { maximumFractionDigits: 4 })}%`;
  return `${n.toLocaleString("en-US", { maximumFractionDigits: 2 })} ${PARAM[key].unit}`;
}

// --- rates: LIVE only when the existing projection says OK -------------------

function liveRates(fx: IntlFxRates | null): Record<LiveKey, number | null> {
  const boc = fx?.boc;
  const agri = fx?.agribank;
  const bidv = fx?.bidv;
  return {
    usdCny: boc?.status === "OK" ? positiveNumber(boc.usd_to_cny) : null,
    agriSell: agri?.status === "OK" ? positiveNumber(agri.usd_sell_vnd ?? agri.sell) : null,
    // The official BIDV source must be proven (bidv_rate_status). The HTML
    // fallback (html_sell / html_sell_vnd) is evidence only — never read here.
    bidvSell:
      bidv?.status === "OK" && bidv.bidv_rate_status !== "UNAVAILABLE"
        ? positiveNumber(bidv.usd_sell_vnd ?? bidv.sell)
        : null,
  };
}
function livePubTime(fx: IntlFxRates | null, key: LiveKey): string | null {
  const entry = key === "usdCny" ? fx?.boc : key === "agriSell" ? fx?.agribank : fx?.bidv;
  return entry?.pub_time ? String(entry.pub_time) : null;
}

interface Resolved {
  value: number | null;
  source: Source;
  problem: Problem | null;
}
type Params = Record<ParamKey, Resolved>;

function passesRule(def: ParamDef, n: number): boolean {
  if (def.rule === "positive") return n > 0;
  if (def.rule === "nonNegative") return n >= 0;
  return n >= 0 && n < 100;
}

function resolveParams(manualValues: Record<ParamKey, string> | null, live: Record<LiveKey, number | null>): Params {
  const out = {} as Params;
  for (const def of PARAMS) {
    if (manualValues) {
      // MANUAL — exactly the visible text. Blank = UNKNOWN (never 0).
      const raw = manualValues[def.key].trim();
      const n = numOrNull(raw);
      out[def.key] =
        raw === ""
          ? { value: null, source: "MANUAL", problem: "missing" }
          : n == null || !passesRule(def, n)
            ? { value: null, source: "MANUAL", problem: "invalid" }
            : { value: n, source: "MANUAL", problem: null };
    } else if (def.standard != null) {
      out[def.key] = { value: Number(def.standard), source: "DEFAULT", problem: null };
    } else {
      const v = def.key in live ? live[def.key as LiveKey] : null; // CNY ngoài has no live source
      out[def.key] = v != null ? { value: v, source: "LIVE", problem: null } : { value: null, source: "UNAVAILABLE", problem: "unavailable" };
    }
  }
  return out;
}

interface Need {
  hints: string[];
  unavailable: boolean;
}
function need(keys: ParamKey[], p: Params, extra: string[] = []): Need {
  const hints = [...extra];
  let unavailable = false;
  for (const k of keys) {
    const r = p[k];
    if (r.value != null) continue;
    const name = `${PARAM[k].label} (${PARAM[k].unit})`;
    if (r.problem === "unavailable") {
      unavailable = true;
      hints.push(`${name}: UNAVAILABLE`);
    } else if (r.problem === "invalid") {
      hints.push(`${name} không hợp lệ`);
    } else {
      hints.push(`Thiếu ${name}`);
    }
  }
  return { hints, unavailable };
}
function amountHints(label: string, n: number | null): string[] {
  if (n == null) return [`Thiếu ${label}`];
  if (n <= 0) return [`${label} phải lớn hơn 0`];
  return [];
}

// --- formulas (LOGI_CONTRACT_INTL_PAYMENT_COMPARATOR_01, no hidden defaults) ---

function chinaForward(gross: number, rate: number, recipientFee: number, feePerTranche: number, trancheSize: number) {
  const trancheCount = gross <= 0 ? 0 : Math.ceil(gross / trancheSize);
  const chinaFee = trancheCount * feePerTranche;
  const afterBank = gross - recipientFee;
  const grossCny = afterBank * rate;
  const net = grossCny - chinaFee;
  return { afterBank, grossCny, chinaFee, net, trancheCount };
}
function hkForward(gross: number, rate: number, hkPct: number, recipientFee: number) {
  const afterBank = gross - recipientFee;
  const hkFee = afterBank * hkPct;
  const forConv = afterBank - hkFee;
  const net = forConv * rate;
  return { afterBank, hkFee, forConv, net };
}
function vnCost(gross: number, sell: number, swiftUsd: number, pct: number) {
  const principal = gross * sell;
  const swift = swiftUsd * sell;
  const pctFee = principal * pct;
  const total = principal + swift + pctFee;
  return { principal, swift, pctFee, total };
}
/** Reverse China: bounded iteration until the tranche count is stable. */
function chinaReverse(target: number, rate: number, recipientFee: number, feePerTranche: number, trancheSize: number) {
  let fee = feePerTranche;
  let gross = (target + fee) / rate + recipientFee;
  for (let i = 0; i < 10; i++) {
    const tranches = Math.ceil(gross / trancheSize);
    const newFee = tranches * feePerTranche;
    if (newFee === fee) {
      const checkGross = (target + newFee) / rate + recipientFee;
      if (Math.ceil(checkGross / trancheSize) === tranches) {
        gross = checkGross;
        fee = newFee;
        break;
      }
    }
    fee = newFee;
    gross = (target + fee) / rate + recipientFee;
  }
  const trancheCount = Math.ceil(gross / trancheSize);
  return { gross, trancheCount, chinaFee: trancheCount * feePerTranche };
}
function hkReverse(target: number, rate: number, hkPct: number, recipientFee: number) {
  return target / (rate * (1 - hkPct)) + recipientFee;
}

// --- UI -----------------------------------------------------------------------

const fieldCls = (problem: Problem | null) =>
  cx(
    "w-full rounded-xl border-2 bg-white px-3.5 min-h-[48px] py-2.5 text-[16px] font-semibold tabular-nums placeholder:font-normal placeholder:text-slate-400 transition-colors focus:outline-none",
    problem === "missing" && "border-amber-400 bg-amber-50/60",
    problem === "invalid" && "border-red-400 bg-red-50/60",
    !problem && "border-slate-200 focus:border-[#1e5aa8]"
  );

function SourceBadge({ source }: { source: Source }) {
  const map: Record<Source, string> = {
    LIVE: "bg-emerald-50 text-emerald-800 border-emerald-200",
    UNAVAILABLE: "bg-red-50 text-red-700 border-red-200",
    DEFAULT: "bg-slate-100 text-slate-700 border-slate-200",
    MANUAL: "bg-blue-50 text-blue-800 border-blue-200",
  };
  return (
    <span data-source-badge={source} className={cx("inline-flex items-center rounded-full border px-2 py-0.5 text-[11.5px] font-extrabold whitespace-nowrap", map[source])}>
      {source === "DEFAULT" ? "PHÍ CHUẨN" : source}
    </span>
  );
}

function Choice<T extends string>({ value, options, onChange, testIdPrefix, label }: {
  value: T;
  options: { id: T; label: string }[];
  onChange: (v: T) => void;
  testIdPrefix: string;
  label: string;
}) {
  return (
    <div role="group" aria-label={label} className="grid grid-cols-2 gap-2">
      {options.map((o) => (
        <button
          key={o.id}
          type="button"
          data-testid={`${testIdPrefix}-${o.id}`}
          aria-pressed={value === o.id}
          onClick={() => onChange(o.id)}
          className={cx(
            "btn-press touch-target min-h-[48px] rounded-xl border-2 px-3 text-[14.5px] font-bold",
            value === o.id ? "border-[#0f2a4a] bg-[#0f2a4a] text-white shadow" : "border-slate-200 bg-white text-slate-700"
          )}
        >
          {o.label}
        </button>
      ))}
    </div>
  );
}

function MoneyCard({ testId, title, caption, value, unit, hints = [], needsManual, footnote, cheapest, size = "lg" }: {
  testId: string;
  title: string;
  caption?: string;
  value: number | null;
  unit: "CNY" | "VND";
  hints?: string[];
  needsManual?: boolean;
  footnote?: string;
  cheapest?: boolean;
  size?: "lg" | "md";
}) {
  const shown = value == null ? null : unit === "VND" ? fmtVndNum(value) : fmt2(value);
  return (
    <div
      data-testid={testId}
      data-value={value == null ? "" : String(value)}
      data-cheapest={cheapest ? "yes" : "no"}
      className={cx("rounded-2xl border-2 p-4 min-w-0", cheapest ? "border-emerald-500 bg-emerald-50" : "border-slate-200 bg-white")}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="font-extrabold text-[15px] text-[#0f2a4a] leading-snug">{title}</p>
          {caption && <p className="text-[12.5px] text-slate-500">{caption}</p>}
        </div>
        {cheapest && (
          <span className="shrink-0 rounded-full bg-emerald-600 px-2.5 py-1 text-[12px] font-extrabold text-white whitespace-nowrap">★ Rẻ nhất</span>
        )}
      </div>
      <p className={cx("mt-1.5 font-extrabold tabular-nums leading-tight break-words", size === "lg" ? "text-[28px] md:text-[32px]" : "text-[24px]", shown == null ? "text-slate-400" : "text-[#0f2a4a]")}>
        {shown == null ? "—" : (
          <>
            {shown} <span className={size === "lg" ? "text-[17px]" : "text-[15px]"}>{unit}</span>
          </>
        )}
      </p>
      {hints.length > 0 && (
        <ul className="mt-1.5 space-y-0.5 text-[13px] font-medium text-amber-800" data-testid={`${testId}-hints`}>
          {hints.map((h) => <li key={h}>{h}</li>)}
        </ul>
      )}
      {needsManual && <p className="mt-1 text-[12.5px] text-slate-600">Tick “Tự nhập toàn bộ thông số” để nhập tay.</p>}
      {footnote && <p className="mt-1 text-[12.5px] text-slate-500 break-words">{footnote}</p>}
    </div>
  );
}

function Line({ label, value, strong }: { label: string; value: string; strong?: boolean }) {
  return (
    <div className={cx("flex items-baseline justify-between gap-3", strong && "font-extrabold text-[#0f2a4a] border-t border-slate-200 pt-1.5")}>
      <span className="min-w-0 text-slate-600">{label}</span>
      <span className="shrink-0 tabular-nums text-right">{value}</span>
    </div>
  );
}

export default function IntlPaymentComparator({ fxRates }: { fxRates: IntlFxRates | null }) {
  const [mode, setMode] = useState<Mode>("A");
  // null = checkbox OFF. The first switch ON prefills every field with the
  // CURRENT effective value (LIVE rate or standard fee; blank when the source
  // is unavailable) — visibly, editable, and the formula uses exactly it.
  const [manualValues, setManualValues] = useState<Record<ParamKey, string> | null>(null);
  const [lastManual, setLastManual] = useState<Record<ParamKey, string> | null>(null);
  const [grossUsd, setGrossUsd] = useState("");
  const [route, setRoute] = useState<Route>("CHINA");
  const [bank, setBank] = useState<Bank>("AGRIBANK");
  const [targetCny, setTargetCny] = useState("");

  const live = liveRates(fxRates);
  const manual = manualValues != null;
  const p = resolveParams(manualValues, live);

  const toggleManual = (on: boolean) => {
    if (!on) {
      setLastManual(manualValues);
      setManualValues(null);
      return;
    }
    const prefill = {} as Record<ParamKey, string>;
    for (const def of PARAMS) {
      const liveValue = def.key in live ? live[def.key as LiveKey] : null;
      prefill[def.key] = def.standard ?? (liveValue != null ? String(liveValue) : "");
    }
    // Re-checking keeps what the operator already typed in this session.
    setManualValues(lastManual ?? prefill);
  };
  const setParam = (key: ParamKey, v: string) => setManualValues((cur) => (cur ? { ...cur, [key]: v } : cur));

  // ------------------------------------------------------------------ Mode A
  const gross = numOrNull(grossUsd);
  const grossHints = amountHints("Số USD cần chuyển", gross);
  const routeKeys: ParamKey[] = route === "CHINA" ? ["usdCny", "recipientFee", "chinaFee", "trancheSize"] : ["usdCny", "recipientFee", "hkPct"];
  const sellKey: ParamKey = bank === "BIDV" ? "bidvSell" : "agriSell";

  const cnyNeed = need(routeKeys, p, grossHints);
  let cnyValue: number | null = null;
  let china: ReturnType<typeof chinaForward> | null = null;
  let hk: ReturnType<typeof hkForward> | null = null;
  if (mode === "A" && cnyNeed.hints.length === 0 && gross != null) {
    const rate = p.usdCny.value as number;
    const fee = p.recipientFee.value as number;
    if (gross <= fee) {
      cnyNeed.hints.push("Số USD cần chuyển phải lớn hơn Phí ngân hàng người nhận");
    } else if (route === "CHINA") {
      china = chinaForward(gross, rate, fee, p.chinaFee.value as number, p.trancheSize.value as number);
      if (china.net < 0) cnyNeed.hints.push("Phí lớn hơn số tiền chuyển — CNY thực nhận sẽ âm");
      else cnyValue = china.net;
    } else {
      hk = hkForward(gross, rate, (p.hkPct.value as number) / 100, fee);
      cnyValue = hk.net;
    }
  }
  const vndNeed = need([sellKey, "vnSwift", "vnPct"], p, grossHints);
  const vnA = mode === "A" && vndNeed.hints.length === 0 && gross != null
    ? vnCost(gross, p[sellKey].value as number, p.vnSwift.value as number, (p.vnPct.value as number) / 100)
    : null;

  // ------------------------------------------------------------------ Mode B
  const target = numOrNull(targetCny);
  const targetHints = amountHints("Số CNY đại lý cần nhận", target);
  const chinaBNeed = need(["usdCny", "recipientFee", "chinaFee", "trancheSize"], p, targetHints);
  const hkBNeed = need(["usdCny", "recipientFee", "hkPct"], p, targetHints);
  const chinaB = mode === "B" && chinaBNeed.hints.length === 0 && target != null
    ? chinaReverse(target, p.usdCny.value as number, p.recipientFee.value as number, p.chinaFee.value as number, p.trancheSize.value as number)
    : null;
  const hkBGross = mode === "B" && hkBNeed.hints.length === 0 && target != null
    ? hkReverse(target, p.usdCny.value as number, (p.hkPct.value as number) / 100, p.recipientFee.value as number)
    : null;
  const outsideNeed = need(["outsideRate"], p, targetHints);
  const outsideTotal = mode === "B" && outsideNeed.hints.length === 0 && target != null ? target * (p.outsideRate.value as number) : null;

  const channels = ([
    ["CHINA", "AGRIBANK"],
    ["CHINA", "BIDV"],
    ["HONG_KONG", "AGRIBANK"],
    ["HONG_KONG", "BIDV"],
  ] as const).map(([r, b]) => {
    const routeNeed = r === "CHINA" ? chinaBNeed : hkBNeed;
    const bKey: ParamKey = b === "BIDV" ? "bidvSell" : "agriSell";
    const bankNeed = need([bKey, "vnSwift", "vnPct"], p);
    const hints = [...new Set([...routeNeed.hints, ...bankNeed.hints])];
    const routeGross = r === "CHINA" ? chinaB?.gross ?? null : hkBGross;
    const total = hints.length === 0 && routeGross != null
      ? vnCost(routeGross, p[bKey].value as number, p.vnSwift.value as number, (p.vnPct.value as number) / 100).total
      : null;
    const detail = routeGross == null
      ? undefined
      : r === "CHINA" && chinaB
        ? `Cần gửi ${fmt2(routeGross)} USD · ${chinaB.trancheCount} tranche × ${fmt2(p.chinaFee.value as number)} CNY`
        : `Cần gửi ${fmt2(routeGross)} USD · phí Hong Kong ${fmtParam("hkPct", p.hkPct.value as number)}`;
    const delta = total != null && outsideTotal != null ? total - outsideTotal : null;
    return {
      id: `${r}-${b}`,
      title: `${r === "CHINA" ? "Trung Quốc" : "Hong Kong"} · ${b === "BIDV" ? "BIDV" : "Agribank"}`,
      total,
      hints,
      unavailable: routeNeed.unavailable || bankNeed.unavailable,
      footnote: [detail, delta != null ? `Chênh so với tệ ngoài: ${delta > 0 ? "+" : ""}${fmtVndNum(delta)} VND` : null].filter(Boolean).join(" · ") || undefined,
    };
  });
  const available = [...channels.map((c) => c.total), outsideTotal].filter((t): t is number => t != null);
  const minTotal = available.length ? Math.min(...available) : null;

  const needsManualA = (n: Need) => !manual && n.unavailable;

  return (
    <div className="grid gap-4 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,1fr)] lg:items-start" data-testid="intl-tool">
      {/* 1 · INPUTS — mode, the manual switch, the business amount */}
      <section className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5 space-y-4 min-w-0 lg:col-start-1 lg:row-start-1" aria-label="Đầu vào">
        <Choice<Mode>
          label="Chế độ tính"
          testIdPrefix="intl-mode"
          value={mode}
          onChange={setMode}
          options={[
            { id: "A", label: "A · Tôi có USD cần chuyển" },
            { id: "B", label: "B · Đại lý cần nhận CNY" },
          ]}
        />

        <label
          data-testid="intl-manual-label"
          className={cx(
            "flex items-start gap-3 rounded-xl border-2 px-4 py-3 min-h-[56px] cursor-pointer select-none",
            manual ? "border-[#1e5aa8] bg-blue-50" : "border-slate-200 bg-slate-50"
          )}
        >
          <input
            type="checkbox"
            data-testid="intl-manual-toggle"
            checked={manual}
            onChange={(e) => toggleManual(e.target.checked)}
            className="mt-0.5 h-6 w-6 shrink-0 cursor-pointer accent-[#0f2a4a]"
          />
          <span className="min-w-0">
            <span className="block font-extrabold text-[15.5px] text-[#0f2a4a]">Tự nhập toàn bộ thông số</span>
            <span className="block text-[13px] text-slate-600 mt-0.5">
              {manual
                ? "Đang dùng đúng các số bạn nhập (MANUAL) cho mọi tỷ giá và phí."
                : "Đang dùng tỷ giá LIVE đáng tin cậy và phí chuẩn."}
            </span>
          </span>
        </label>

        {mode === "A" ? (
          <div className="grid gap-3 sm:grid-cols-2">
            <label className="block sm:col-span-2">
              <span className="block text-[14px] font-semibold text-slate-700 mb-1.5">Số USD cần chuyển (USD)</span>
              <input
                data-testid="intl-gross-usd"
                value={grossUsd}
                onChange={(e) => setGrossUsd(e.target.value)}
                inputMode="decimal"
                autoComplete="off"
                placeholder="VD: 14000"
                className={fieldCls(null)}
              />
            </label>
            <div>
              <p className="text-[14px] font-semibold text-slate-700 mb-1.5">Đại lý nhận</p>
              <Choice<Route>
                label="Đại lý nhận"
                testIdPrefix="intl-route"
                value={route}
                onChange={setRoute}
                options={[
                  { id: "CHINA", label: "Trung Quốc" },
                  { id: "HONG_KONG", label: "Hong Kong" },
                ]}
              />
            </div>
            <div>
              <p className="text-[14px] font-semibold text-slate-700 mb-1.5">Ngân hàng Việt Nam</p>
              <Choice<Bank>
                label="Ngân hàng Việt Nam"
                testIdPrefix="intl-bank"
                value={bank}
                onChange={setBank}
                options={[
                  { id: "AGRIBANK", label: "Agribank" },
                  { id: "BIDV", label: "BIDV" },
                ]}
              />
            </div>
          </div>
        ) : (
          <label className="block">
            <span className="block text-[14px] font-semibold text-slate-700 mb-1.5">Số CNY đại lý cần nhận (CNY)</span>
            <input
              data-testid="intl-target-cny"
              value={targetCny}
              onChange={(e) => setTargetCny(e.target.value)}
              inputMode="decimal"
              autoComplete="off"
              placeholder="VD: 100000"
              className={fieldCls(null)}
            />
          </label>
        )}
      </section>

      {/* 2 · RESULTS — the money. Right column on desktop, right after the
          business inputs on mobile. */}
      <section className="space-y-3 min-w-0 lg:col-start-2 lg:row-start-1 lg:row-span-2 xl:sticky xl:top-[80px]" aria-label="Kết quả" data-testid="intl-results">
        <div className="flex flex-wrap items-baseline justify-between gap-x-3">
          <h2 className="font-extrabold text-[17px] text-[#0f2a4a]">Kết quả</h2>
          <p className="text-[12.5px] text-slate-500">Số tham khảo — không phải báo giá cam kết của ngân hàng.</p>
        </div>

        {mode === "A" ? (
          <>
            <MoneyCard
              testId="intl-result-cny"
              title="CNY thực nhận"
              caption={route === "CHINA" ? "Đại lý Trung Quốc nhận" : "Đại lý Hong Kong nhận"}
              value={cnyValue}
              unit="CNY"
              hints={cnyNeed.hints}
              needsManual={needsManualA(cnyNeed)}
              footnote={p.usdCny.value != null ? `USD→CNY ${fmtRate(p.usdCny.value)} (${p.usdCny.source})` : undefined}
            />
            <MoneyCard
              testId="intl-result-vnd"
              title="Tổng VND cần trả"
              caption={`Chuyển qua ${bank === "BIDV" ? "BIDV" : "Agribank"}`}
              value={vnA ? vnA.total : null}
              unit="VND"
              hints={vndNeed.hints}
              needsManual={needsManualA(vndNeed)}
              footnote={p[sellKey].value != null ? `${bank === "BIDV" ? "BIDV" : "Agribank"} bán USD ${fmtParam(sellKey, p[sellKey].value as number)} (${p[sellKey].source})` : undefined}
            />
            {(china || hk || vnA) && (
              <details className="rounded-2xl border border-slate-200 bg-white px-4 py-1.5" data-testid="intl-breakdown">
                <summary className="touch-target cursor-pointer select-none py-2.5 font-bold text-[14px] text-[#0f2a4a]">Cách tính chi tiết</summary>
                <div className="mb-2.5 space-y-1.5 text-[13.5px]">
                  {gross != null && (china || hk) && (
                    <>
                      <Line label="Số USD cần chuyển" value={`${fmt2(gross)} USD`} />
                      <Line label={`Sau phí ngân hàng người nhận (${fmtParam("recipientFee", p.recipientFee.value as number)})`} value={`${fmt2((china ?? hk)!.afterBank)} USD`} />
                    </>
                  )}
                  {china && (
                    <>
                      <Line label={`CNY trước phí đại lý (× ${fmtRate(p.usdCny.value as number)})`} value={`${fmt2(china.grossCny)} CNY`} />
                      <Line label={`Phí đại lý Trung Quốc (${china.trancheCount} tranche × ${fmt2(p.chinaFee.value as number)} CNY)`} value={`${fmt2(china.chinaFee)} CNY`} />
                      {cnyValue != null && <Line strong label="CNY thực nhận" value={`${fmt2(cnyValue)} CNY`} />}
                    </>
                  )}
                  {hk && (
                    <>
                      <Line label={`Phí Hong Kong (${fmtParam("hkPct", p.hkPct.value as number)})`} value={`${fmt2(hk.hkFee)} USD`} />
                      <Line label={`USD quy đổi (× ${fmtRate(p.usdCny.value as number)})`} value={`${fmt2(hk.forConv)} USD`} />
                      <Line strong label="CNY thực nhận" value={`${fmt2(hk.net)} CNY`} />
                    </>
                  )}
                  {vnA && (
                    <div className="pt-2 space-y-1.5">
                      <Line label="Gốc (USD × tỷ giá bán)" value={`${fmtVndNum(vnA.principal)} VND`} />
                      <Line label={`Phí SWIFT Việt Nam (${fmtParam("vnSwift", p.vnSwift.value as number)})`} value={`${fmtVndNum(vnA.swift)} VND`} />
                      <Line label={`Phí ngân hàng Việt Nam (${fmtParam("vnPct", p.vnPct.value as number)})`} value={`${fmtVndNum(vnA.pctFee)} VND`} />
                      <Line strong label="Tổng VND cần trả" value={`${fmtVndNum(vnA.total)} VND`} />
                    </div>
                  )}
                </div>
              </details>
            )}
          </>
        ) : (
          <>
            <p className="text-[12.5px] text-slate-500">
              Tổng VND cần trả cho từng kênh. “Rẻ nhất” chỉ so trong các kênh tính được.
            </p>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-1 xl:grid-cols-2">
              {channels.map((c) => (
                <MoneyCard
                  key={c.id}
                  testId={`intl-result-b-${c.id}`}
                  size="md"
                  title={c.title}
                  caption="Tổng VND cần trả"
                  value={c.total}
                  unit="VND"
                  hints={c.hints}
                  needsManual={!manual && c.unavailable}
                  footnote={c.footnote}
                  cheapest={c.total != null && c.total === minTotal}
                />
              ))}
              <MoneyCard
                testId="intl-result-b-OUTSIDE"
                size="md"
                title="Tệ ngoài"
                caption="Tổng VND cần trả (mua CNY bên ngoài)"
                value={outsideTotal}
                unit="VND"
                hints={outsideNeed.hints}
                needsManual={!manual && outsideNeed.unavailable}
                footnote={outsideTotal != null && target != null ? `${fmt2(target)} CNY × ${fmtParam("outsideRate", p.outsideRate.value as number)}` : undefined}
                cheapest={outsideTotal != null && outsideTotal === minTotal}
              />
            </div>
          </>
        )}
      </section>

      {/* 3 · PARAMETERS — read-only LIVE/standard values, or every assumption
          as an editable field when "Tự nhập toàn bộ thông số" is checked. */}
      <section
        className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5 min-w-0 lg:col-start-1 lg:row-start-2"
        aria-label="Tỷ giá và phí"
        data-testid="intl-params"
        data-mode={manual ? "manual" : "normal"}
      >
        {manual && manualValues ? (
          <>
            <div className="flex items-center justify-between gap-2">
              <h2 className="font-extrabold text-[16px] text-[#0f2a4a]">Thông số tự nhập</h2>
              <SourceBadge source="MANUAL" />
            </div>
            <p className="text-[13px] text-slate-600 mt-1">
              Kết quả dùng đúng các số dưới đây. Ô trống = chưa biết, không tính là 0. Đã điền sẵn từ tỷ giá LIVE và phí chuẩn hiện có — sửa tùy ý.
            </p>
            <div className="grid gap-3 sm:grid-cols-2 mt-3">
              {PARAMS.map((def) => {
                const r = p[def.key];
                const liveValue = def.key in live ? live[def.key as LiveKey] : undefined;
                return (
                  <label key={def.key} className="block min-w-0">
                    <span className="block text-[14px] font-semibold text-slate-700 mb-1.5">{def.label} ({def.unit})</span>
                    <input
                      data-testid={`intl-param-${def.key}`}
                      value={manualValues[def.key]}
                      onChange={(e) => setParam(def.key, e.target.value)}
                      inputMode="decimal"
                      autoComplete="off"
                      aria-invalid={r.problem === "invalid" || undefined}
                      className={fieldCls(r.problem)}
                    />
                    {r.problem === "missing" && <span className="block text-[12.5px] font-medium text-amber-800 mt-1">Chưa nhập — kết quả liên quan hiển thị “—”.</span>}
                    {r.problem === "invalid" && <span className="block text-[12.5px] font-medium text-red-700 mt-1">Không hợp lệ — {RULE_TEXT[def.rule]}.</span>}
                    {liveValue !== undefined && (
                      <span className="block text-[12px] text-slate-500 mt-1">
                        {liveValue != null ? `Tham khảo LIVE ${LIVE_SOURCE[def.key as LiveKey]}: ${fmtParam(def.key, liveValue)}` : `${LIVE_SOURCE[def.key as LiveKey]}: không có giá LIVE`}
                      </span>
                    )}
                    {def.note && <span className="block text-[12px] text-slate-500 mt-0.5">{def.note}</span>}
                  </label>
                );
              })}
            </div>
          </>
        ) : (
          <>
            <h2 className="font-extrabold text-[16px] text-[#0f2a4a]">Tỷ giá & phí đang dùng</h2>
            <ul className="mt-2 divide-y divide-slate-100">
              {(["usdCny", "agriSell", "bidvSell", "outsideRate"] as ParamKey[]).map((key) => {
                const r = p[key];
                const pub = key === "outsideRate" ? null : livePubTime(fxRates, key as LiveKey);
                return (
                  <li key={key} data-testid={`intl-rate-${key}`} data-source={r.source} className="flex flex-wrap items-center justify-between gap-x-3 gap-y-1 py-2.5">
                    <span className="min-w-0">
                      <span className="block font-semibold text-[14px] text-slate-700">
                        {PARAM[key].label}
                        {key === "usdCny" && <span className="font-normal text-slate-500"> · {LIVE_SOURCE.usdCny}</span>}
                      </span>
                      {r.source === "LIVE" && pub && <span className="block text-[12px] text-slate-500">Cập nhật {pub}</span>}
                      {key === "outsideRate" && <span className="block text-[12px] text-slate-500">Không có nguồn LIVE — chỉ nhập tay.</span>}
                    </span>
                    <span className="flex shrink-0 items-center gap-2">
                      <span className="font-bold text-[14.5px] tabular-nums text-[#0f2a4a]">{r.value != null ? fmtParam(key, r.value) : "—"}</span>
                      <SourceBadge source={r.source} />
                    </span>
                  </li>
                );
              })}
            </ul>
            <div className="mt-2 rounded-xl bg-slate-50 border border-slate-200 p-3" data-testid="intl-standard-fees">
              <p className="text-[13px] font-bold text-slate-700">Phí chuẩn đang dùng</p>
              <ul className="mt-1 grid gap-x-4 gap-y-0.5 text-[13px] text-slate-600 sm:grid-cols-2">
                {PARAMS.filter((d) => d.standard != null).map((d) => (
                  <li key={d.key} className="flex justify-between gap-2">
                    <span className="min-w-0">{d.label}</span>
                    <span className="shrink-0 font-semibold tabular-nums text-slate-800">{fmtParam(d.key, Number(d.standard))}</span>
                  </li>
                ))}
              </ul>
            </div>
            <p className="text-[12.5px] text-slate-500 mt-2">Cần dùng số khác? Tick “Tự nhập toàn bộ thông số”.</p>
          </>
        )}
      </section>
    </div>
  );
}
