// ============================================================================
// LOGI_QUOTE_COST_WORKFLOW_UX_01 — "Check chi phí" comparable-cost matching.
//
// NO NEW DATABASE. Historical cost reference is DERIVED from the shipments the
// view-model already projects:
//
//   FIRST     shipments that have Finance ACTUAL lines  → SOURCE=THỰC TẾ
//   FALLBACK  the quote estimate projected on the lot   → SOURCE=BÁO GIÁ / DỰ KIẾN
//
// Matching is deterministic and explainable: normalized Incoterm equality,
// accent-insensitive origin/destination text match, and nearest CBM/weight.
// There are deliberately NO embeddings, NO vector search and NO ML similarity.
// Currencies are NEVER summed across codes.
// ============================================================================

import type { MoneyLine, Shipment } from "./viewmodel";

export type CostSource = "ACTUAL" | "QUOTE";

export interface CostCriteria {
  incoterm: string;
  origin: string;
  destination: string;
  cbm: number | null;
  weightKg: number | null;
  mode?: string;
}

export interface CostMatchLine {
  label: string;
  unit: string;
  qty: number | null;
  price: number | null;
  vat: number | null;
  ccy: string;
  note: string;
}

export interface CostMatch {
  shipmentId: string;
  customer: string;
  createdAt: string;
  /** "06/2026" — the month the comparable lot was created. */
  period: string;
  source: CostSource;
  sourceLabel: string;
  incoterm: string;
  origin: string;
  destination: string;
  mode: string;
  cbm: number | null;
  weightKg: number | null;
  /** Human-readable reasons, e.g. ["tuyến", "Incoterm", "CBM gần nhất"]. */
  reasons: string[];
  /** Higher is a better comparable. */
  score: number;
  lines: CostMatchLine[];
  /** Per-currency subtotals — never merged across currencies. */
  totalsByCurrency: Array<{ ccy: string; amount: number }>;
}

/** Diacritic- and case-insensitive normalisation (same rule as the pickers). */
export function loose(text: string | null | undefined): string {
  return String(text ?? "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/đ/gi, "d")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
}

function textMatches(candidate: string, needle: string): boolean {
  const a = loose(candidate);
  const b = loose(needle);
  if (!a || !b) return false;
  return a.includes(b) || b.includes(a);
}

/** "01/09/2026" / "2026-09-01" → "09/2026". */
export function periodOf(createdAt: string | undefined): string {
  const raw = String(createdAt || "").trim();
  let m = raw.match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (m) return `${m[2]}/${m[1]}`;
  m = raw.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})/);
  if (m) return `${m[2].padStart(2, "0")}/${m[3]}`;
  return "";
}

/** Canonical createdAt → a comparable timestamp (0 when unknown). */
export function createdTs(createdAt: string | undefined): number {
  const raw = String(createdAt || "").trim();
  let m = raw.match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (m) return Date.UTC(Number(m[1]), Number(m[2]) - 1, Number(m[3]));
  m = raw.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})/);
  if (m) return Date.UTC(Number(m[3]), Number(m[2]) - 1, Number(m[1]));
  return 0;
}

function actualLines(s: Shipment): CostMatchLine[] {
  return (s.finance?.actual ?? []).map((l) => ({
    label: l.label || l.name || "Dịch vụ",
    unit: l.unit || "",
    qty: l.qty ?? null,
    price: l.price ?? l.amount ?? null,
    vat: l.vat ?? null,
    ccy: l.ccy || s.finance?.currency || "VND",
    note: l.note || "",
  }));
}

function quoteLines(s: Shipment): CostMatchLine[] {
  return (s.finance?.quote ?? []).map((l: MoneyLine) => ({
    label: l.label || "Dịch vụ (báo giá)",
    unit: "",
    qty: l.qty ?? null,
    price: l.amount ?? null,
    vat: l.vat ?? null,
    ccy: l.ccy || s.finance?.currency || "VND",
    note: "",
  }));
}

function totalsByCurrency(lines: CostMatchLine[]): Array<{ ccy: string; amount: number }> {
  const buckets = new Map<string, number>();
  for (const l of lines) {
    if (l.price == null) continue;
    const qty = l.qty == null ? 1 : l.qty;
    const code = (l.ccy || "VND").toUpperCase();
    buckets.set(code, (buckets.get(code) ?? 0) + l.price * qty);
  }
  return [...buckets.entries()].map(([ccy, amount]) => ({ ccy, amount }));
}

const NEAR_RATIO = 0.5; // ±50% counts as "comparable"

function nearness(candidate: number | null | undefined, wanted: number): number | null {
  if (candidate == null || !Number.isFinite(candidate) || candidate <= 0) return null;
  const diff = Math.abs(candidate - wanted) / Math.max(wanted, 1);
  return diff <= NEAR_RATIO ? diff : null;
}

/**
 * Find comparable historical lots for the supplied criteria.
 *
 * A lot with real Finance Actual lines always outranks the same lot's quote
 * estimate: the estimate is only used when NO actual line exists, and it is
 * then labelled honestly.
 */
export function findComparableCosts(shipments: Shipment[], criteria: CostCriteria): CostMatch[] {
  const wantIncoterm = (criteria.incoterm || "").trim().toUpperCase();
  const wantOrigin = (criteria.origin || "").trim();
  const wantDest = (criteria.destination || "").trim();
  const wantCbm = criteria.cbm;
  const wantWeight = criteria.weightKg;
  const wantMode = (criteria.mode || "").trim();
  const supplied = [wantIncoterm, wantOrigin, wantDest, wantCbm, wantWeight].filter(
    (v) => v !== "" && v != null
  ).length;
  if (supplied === 0) return [];

  const out: CostMatch[] = [];
  for (const s of shipments) {
    const reasons: string[] = [];
    let score = 0;
    let disqualified = false;

    const incoterm = (s.incoterm || s.executionProfile?.incoterm || "").toUpperCase();
    if (wantIncoterm) {
      if (incoterm === wantIncoterm) { score += 40; reasons.push("Incoterm"); }
      else if (incoterm) disqualified = true;
    }

    const origin = s.transport?.pol || s.pickup?.factory || "";
    const destination = s.transport?.pod || s.importInfo?.deliveryAddr || "";
    const route = s.route || "";
    if (wantOrigin) {
      if (textMatches(origin, wantOrigin) || textMatches(route, wantOrigin)) {
        score += 25; reasons.push("nơi đi");
      }
    }
    if (wantDest) {
      if (textMatches(destination, wantDest) || textMatches(route, wantDest)) {
        score += 25; reasons.push("nơi đến");
      }
    }
    if (reasons.includes("nơi đi") && reasons.includes("nơi đến")) {
      // Collapse the two route reasons into the single "tuyến" wording.
      reasons.splice(reasons.indexOf("nơi đi"), 1);
      reasons.splice(reasons.indexOf("nơi đến"), 1);
      reasons.unshift("tuyến");
    }

    const cbm = s.cargo?.cbm ?? null;
    if (wantCbm != null) {
      const near = nearness(cbm, wantCbm);
      if (near != null) { score += Math.round(20 * (1 - near)); reasons.push("CBM gần nhất"); }
    }
    const weight = s.cargo?.weight ?? null;
    if (wantWeight != null) {
      const near = nearness(weight, wantWeight);
      if (near != null) { score += Math.round(20 * (1 - near)); reasons.push("cân nặng gần nhất"); }
    }
    if (wantMode) {
      const mode = s.mode || s.executionProfile?.mode || "";
      if (mode && loose(mode) === loose(wantMode)) { score += 8; reasons.push("phương thức"); }
    }

    if (disqualified || score <= 0 || reasons.length === 0) continue;

    const actual = actualLines(s);
    const useActual = actual.length > 0;
    const lines = useActual ? actual : quoteLines(s);
    if (lines.length === 0) continue;

    out.push({
      shipmentId: s.id,
      customer: s.customer || "",
      createdAt: s.createdAt || "",
      period: periodOf(s.createdAt),
      source: useActual ? "ACTUAL" : "QUOTE",
      sourceLabel: useActual ? "THỰC TẾ" : "BÁO GIÁ / DỰ KIẾN",
      incoterm,
      origin: origin || route,
      destination: destination || route,
      mode: s.mode || s.executionProfile?.mode || "",
      cbm,
      weightKg: weight,
      // More supplied criteria present → a stronger comparable.
      reasons,
      score: score + (useActual ? 15 : 0),
      lines,
      totalsByCurrency: totalsByCurrency(lines),
    });
  }

  // Closeness first, then recency. Deterministic, explainable, no ML.
  return out.sort((a, b) => (b.score - a.score) || (createdTs(b.createdAt) - createdTs(a.createdAt)));
}
