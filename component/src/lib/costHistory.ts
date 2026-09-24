// ============================================================================
// LOGI_COST_INTELLIGENCE_01 — one explainable comparable-cost matcher.
//
// Sources, in trust order when relevance is otherwise comparable:
//   ACTUAL     booked shipment cost
//   INPUT_RATE immutable supplier/agent/carrier rate snapshot
//   QUOTE      historical quotation estimate
//
// No embeddings, vector DB, ML or LLM ranking. Place identity, logistics-zone
// proximity, recency and equipment compatibility are explicit and inspectable.
// Currencies are never merged.
// ============================================================================

import type {
  CostCatalogEntry,
  CostRateLine,
  CostRateSnapshot,
  MoneyLine,
  Shipment,
} from "./viewmodel";

export type CostSource = "ACTUAL" | "INPUT_RATE" | "QUOTE";

export interface CostCriteria {
  incoterm: string;
  origin: string;
  destination: string;
  cbm: number | null;
  weightKg: number | null;
  mode?: string;
  /** More precise aliases for Cost Intelligence V1. */
  factory?: string;
  pol?: string;
  pod?: string;
  delivery?: string;
  loadModel?: string;
  equipment?: string;
  targetDate?: string;
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
  /** Stable reference identity, shipment id or rate snapshot/group identity. */
  referenceId: string;
  /** Present only when the reference is a real shipment. */
  shipmentId: string;
  customer: string;
  supplier?: string;
  createdAt: string;
  period: string;
  source: CostSource;
  sourceLabel: string;
  incoterm: string;
  origin: string;
  destination: string;
  mode: string;
  equipment?: string;
  cbm: number | null;
  weightKg: number | null;
  reasons: string[];
  differences?: string[];
  score: number;
  ageDays?: number | null;
  expired?: boolean;
  lines: CostMatchLine[];
  totalsByCurrency: Array<{ ccy: string; amount: number }>;
}

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

export function periodOf(createdAt: string | undefined): string {
  const raw = String(createdAt || "").trim();
  let m = raw.match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (m) return `${m[2]}/${m[1]}`;
  m = raw.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})/);
  if (m) return `${m[2].padStart(2, "0")}/${m[3]}`;
  return "";
}

export function createdTs(createdAt: string | undefined): number {
  const raw = String(createdAt || "").trim();
  let m = raw.match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (m) return Date.UTC(Number(m[1]), Number(m[2]) - 1, Number(m[3]));
  m = raw.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})/);
  if (m) return Date.UTC(Number(m[3]), Number(m[2]) - 1, Number(m[1]));
  const parsed = Date.parse(raw);
  return Number.isFinite(parsed) ? parsed : 0;
}

function actualLines(s: Shipment): CostMatchLine[] {
  return (s.finance?.actual ?? []).map((l) => ({
    label: l.label || l.name || "Dịch vụ",
    unit: l.unit || "",
    qty: l.qty ?? null,
    price: l.cost ?? l.price ?? l.amount ?? null,
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

const NEAR_RATIO = 0.5;

function nearness(candidate: number | null | undefined, wanted: number): number | null {
  if (candidate == null || !Number.isFinite(candidate) || candidate <= 0) return null;
  const diff = Math.abs(candidate - wanted) / Math.max(wanted, 1);
  return diff <= NEAR_RATIO ? diff : null;
}

function targetTs(criteria: CostCriteria): number {
  const ts = createdTs(criteria.targetDate);
  return ts || Date.now();
}

function ageDays(createdAt: string, target: number): number | null {
  const ts = createdTs(createdAt);
  if (!ts) return null;
  return Math.max(0, Math.round((target - ts) / 86_400_000));
}

function recencyBonus(days: number | null): { score: number; reason: string } {
  if (days == null) return { score: 0, reason: "" };
  if (days <= 14) return { score: 15, reason: "giá rất mới" };
  if (days <= 30) return { score: 12, reason: "giá mới" };
  if (days <= 90) return { score: 7, reason: "trong 90 ngày" };
  if (days <= 180) return { score: 3, reason: "trong 6 tháng" };
  if (days > 365) return { score: -8, reason: "dữ liệu cũ > 1 năm" };
  return { score: 0, reason: "" };
}

function catalogPlace(text: string, catalog: CostCatalogEntry[]): CostCatalogEntry | null {
  const wanted = loose(text);
  if (!wanted) return null;
  return (
    catalog.find((x) => {
      if (x.kind !== "PLACE" || x.active === false) return false;
      return [x.name, x.code, x.unlocode, ...(x.aliases || [])].some(
        (v) => loose(v) === wanted
      );
    }) ?? null
  );
}

function sameZone(a: string[], b: string[]): boolean {
  if (!a.length || !b.length) return false;
  const right = new Set(b);
  return a.some((x) => right.has(x));
}

function placeScore(
  candidateName: string,
  candidateZones: string[],
  wantedText: string,
  catalog: CostCatalogEntry[],
  label: string
): { score: number; reason?: string; difference?: string } {
  if (!wantedText.trim()) return { score: 0 };
  if (textMatches(candidateName, wantedText)) {
    return { score: 25, reason: label };
  }
  const wanted = catalogPlace(wantedText, catalog);
  const candidate = catalogPlace(candidateName, catalog);
  const wantedZones = wanted?.zone_ids || [];
  const zones = candidateZones.length ? candidateZones : candidate?.zone_ids || [];
  if (sameZone(zones, wantedZones)) {
    return {
      score: 12,
      reason: `${label} cùng vùng logistics`,
      difference: `${label}: ${candidateName || "—"} thay vì ${wantedText}`,
    };
  }
  return {
    score: 0,
    difference: candidateName ? `${label} khác: ${candidateName}` : undefined,
  };
}

function shipmentMatch(
  s: Shipment,
  criteria: CostCriteria,
  catalog: CostCatalogEntry[],
  target: number
): CostMatch | null {
  const wantIncoterm = (criteria.incoterm || "").trim().toUpperCase();
  const wantPol = (criteria.pol || criteria.origin || "").trim();
  const wantPod = (criteria.pod || criteria.destination || "").trim();
  const wantFactory = (criteria.factory || "").trim();
  const wantDelivery = (criteria.delivery || "").trim();
  const wantCbm = criteria.cbm;
  const wantWeight = criteria.weightKg;
  const wantMode = (criteria.mode || "").trim();
  const wantEquipment = (criteria.equipment || "").trim().toUpperCase();

  const reasons: string[] = [];
  const differences: string[] = [];
  let score = 0;
  let disqualified = false;

  const incoterm = (s.incoterm || s.executionProfile?.incoterm || "").toUpperCase();
  if (wantIncoterm) {
    if (incoterm === wantIncoterm) {
      score += 35;
      reasons.push("Incoterm");
    } else if (incoterm) {
      disqualified = true;
    }
  }

  const pol = s.transport?.pol || "";
  const pod = s.transport?.pod || "";
  const route = s.route || "";
  const factory = s.pickup?.factory || "";
  const delivery = s.importInfo?.deliveryAddr || "";

  const originResult = placeScore(pol || factory || route, [], wantPol, catalog, "POL/nơi đi");
  const destResult = placeScore(pod || delivery || route, [], wantPod, catalog, "POD/nơi đến");
  const factoryResult = placeScore(factory, [], wantFactory, catalog, "nhà máy");
  const deliveryResult = placeScore(delivery, [], wantDelivery, catalog, "giao cuối");
  for (const result of [originResult, destResult, factoryResult, deliveryResult]) {
    score += result.score;
    if (result.reason) reasons.push(result.reason);
    if (result.difference) differences.push(result.difference);
  }

  const cbm = s.cargo?.cbm ?? null;
  if (wantCbm != null) {
    const near = nearness(cbm, wantCbm);
    if (near != null) {
      score += Math.round(20 * (1 - near));
      reasons.push("CBM gần nhất");
    }
  }
  const weight = s.cargo?.weight ?? null;
  if (wantWeight != null) {
    const near = nearness(weight, wantWeight);
    if (near != null) {
      score += Math.round(20 * (1 - near));
      reasons.push("cân nặng gần nhất");
    }
  }
  if (wantMode) {
    const mode = s.mode || s.executionProfile?.mode || "";
    if (mode && loose(mode) === loose(wantMode)) {
      score += 8;
      reasons.push("phương thức");
    }
  }

  // Shipment rows usually do not retain container size as one canonical field.
  // Do not invent a mismatch. Equipment is a hard gate only for input rates
  // that explicitly state it.
  if (wantEquipment) differences.push("lô cũ không có equipment chuẩn để đối chiếu");

  if (disqualified || score <= 0 || reasons.length === 0) return null;

  const actual = actualLines(s);
  const useActual = actual.length > 0;
  const lines = useActual ? actual : quoteLines(s);
  if (!lines.length) return null;

  const days = ageDays(s.createdAt || "", target);
  const recent = recencyBonus(days);
  score += recent.score;
  if (recent.reason) reasons.push(recent.reason);
  score += useActual ? 18 : 0;

  return {
    referenceId: s.id,
    shipmentId: s.id,
    customer: s.customer || "",
    createdAt: s.createdAt || "",
    period: periodOf(s.createdAt),
    source: useActual ? "ACTUAL" : "QUOTE",
    sourceLabel: useActual ? "THỰC TẾ" : "BÁO GIÁ / DỰ KIẾN",
    incoterm,
    origin: pol || factory || route,
    destination: pod || delivery || route,
    mode: s.mode || s.executionProfile?.mode || "",
    cbm,
    weightKg: weight,
    reasons,
    differences,
    score,
    ageDays: days,
    lines,
    totalsByCurrency: totalsByCurrency(lines),
  };
}

interface InputRateGroup {
  key: string;
  carrier: string;
  origin: string;
  destination: string;
  originZones: string[];
  destinationZones: string[];
  loadModel: string;
  equipment: string;
  validUntil: string;
  rows: CostRateLine[];
}

function inputRateGroups(snapshot: CostRateSnapshot): InputRateGroup[] {
  const groups = new Map<string, InputRateGroup>();
  for (const row of snapshot.rows || []) {
    if (row.status !== "AVAILABLE" || row.amount == null) continue;
    const carrier = row.carrier?.name || "";
    const origin = row.origin?.name || row.origin?.raw || "";
    const destination = row.destination?.name || row.destination?.raw || "";
    const equipment = (row.equipment || "").toUpperCase();
    const loadModel = equipment ? "FCL" : ["CBM", "RT"].includes((row.unit || "").toUpperCase()) ? "LCL" : "";
    const validUntil = row.validUntil || "";
    const key = [carrier, origin, destination, loadModel, equipment, validUntil].join("|");
    const existing = groups.get(key);
    if (existing) {
      existing.rows.push(row);
    } else {
      groups.set(key, {
        key,
        carrier,
        origin,
        destination,
        originZones: row.origin?.zoneIds || [],
        destinationZones: row.destination?.zoneIds || [],
        loadModel,
        equipment,
        validUntil,
        rows: [row],
      });
    }
  }
  return [...groups.values()];
}

function inputRateMatches(
  snapshots: CostRateSnapshot[],
  criteria: CostCriteria,
  catalog: CostCatalogEntry[],
  target: number
): CostMatch[] {
  const wantPol = (criteria.pol || criteria.origin || "").trim();
  const wantPod = (criteria.pod || criteria.destination || "").trim();
  const wantEquipment = (criteria.equipment || "").trim().toUpperCase();
  const wantLoadModel = (criteria.loadModel || "").trim().toUpperCase();
  const wantMode = (criteria.mode || "").trim();
  const out: CostMatch[] = [];

  for (const snapshot of snapshots) {
    if (!["ACTIVE", "SUPERSEDED", "EXPIRED"].includes((snapshot.status || "ACTIVE").toUpperCase())) continue;
    for (const group of inputRateGroups(snapshot)) {
      const reasons: string[] = [];
      const differences: string[] = [];
      let score = 10; // INPUT_RATE trust: below ACTUAL, above QUOTE.

      if (wantMode && !["sea", "ocean"].includes(loose(wantMode))) continue;
      if (wantMode) {
        score += 8;
        reasons.push("phương thức biển");
      }

      if (wantLoadModel) {
        if (group.loadModel && group.loadModel !== wantLoadModel) continue;
        if (group.loadModel === wantLoadModel) {
          score += 16;
          reasons.push(wantLoadModel === "FCL" ? "đúng FCL" : "đúng LCL");
        } else {
          differences.push("giá đầu vào chưa ghi rõ FCL/LCL");
        }
      }

      if (wantEquipment) {
        if (group.equipment) {
          if (group.equipment !== wantEquipment) continue;
          score += 24;
          reasons.push("đúng container");
        } else {
          differences.push("giá đầu vào chưa ghi loại container");
        }
      }

      const originResult = placeScore(group.origin, group.originZones, wantPol, catalog, "POL/nơi đi");
      const destResult = placeScore(group.destination, group.destinationZones, wantPod, catalog, "POD/nơi đến");
      for (const result of [originResult, destResult]) {
        score += result.score;
        if (result.reason) reasons.push(result.reason);
        if (result.difference) differences.push(result.difference);
      }

      // Input ocean rates rarely state the customer's Incoterm. Unknown is not
      // a mismatch; disclose it instead of inventing EXW/FOB.
      if (criteria.incoterm) differences.push("giá carrier không ghi Incoterm");

      const days = ageDays(snapshot.received_at, target);
      const recent = recencyBonus(days);
      score += recent.score;
      if (recent.reason) reasons.push(recent.reason);

      let expired = false;
      if (group.validUntil) {
        const expiry = createdTs(group.validUntil);
        if (expiry && expiry < target) {
          expired = true;
          score -= 25;
          differences.push(`đã hết hiệu lực ${group.validUntil}`);
        } else if (expiry) {
          reasons.push("còn hiệu lực theo nguồn");
        }
      }
      if ((snapshot.status || "").toUpperCase() === "EXPIRED") {
        expired = true;
        score -= 25;
        differences.push("snapshot đã đánh dấu hết hạn");
      }

      if (score <= 0 || reasons.length === 0) continue;
      const lines: CostMatchLine[] = group.rows.map((row) => ({
        label: row.chargeLabel || (row.kind === "CREDIT" ? "Refund/Credit" : "Dòng giá đầu vào"),
        unit: row.equipment || row.unit || "",
        qty: 1,
        price: row.kind === "CREDIT" ? -(row.amount || 0) : row.amount ?? null,
        vat: null,
        ccy: row.currency || "",
        note: [
          row.carrier?.name,
          row.etd ? `ETD ${row.etd}` : "",
          row.taxQualifier === "PLUS_TAX" ? "+ TAX" : "",
          row.rawLine,
        ].filter(Boolean).join(" · "),
      }));

      out.push({
        referenceId: `${snapshot.id}:${group.key}`,
        shipmentId: "",
        customer: "",
        supplier: snapshot.supplier || group.carrier,
        createdAt: snapshot.received_at,
        period: periodOf(snapshot.received_at),
        source: "INPUT_RATE",
        sourceLabel: "GIÁ ĐẦU VÀO",
        incoterm: "",
        origin: group.origin,
        destination: group.destination,
        mode: "Sea",
        equipment: group.equipment,
        cbm: null,
        weightKg: null,
        reasons,
        differences,
        score,
        ageDays: days,
        expired,
        lines,
        // Do not manufacture a package total across mixed /CONT /SET /BL units.
        totalsByCurrency: [],
      });
    }
  }
  return out;
}

/**
 * Find comparable historical costs and supplier input rates.
 *
 * Extra arguments are optional so old callers/tests remain valid while the
 * one matching authority learns the new source.
 */
export function findComparableCosts(
  shipments: Shipment[],
  criteria: CostCriteria,
  inputRates: CostRateSnapshot[] = [],
  catalog: CostCatalogEntry[] = []
): CostMatch[] {
  const supplied = [
    criteria.incoterm,
    criteria.origin,
    criteria.destination,
    criteria.pol,
    criteria.pod,
    criteria.factory,
    criteria.delivery,
    criteria.cbm,
    criteria.weightKg,
    criteria.mode,
    criteria.loadModel,
    criteria.equipment,
  ].filter((v) => v !== "" && v != null).length;
  if (supplied === 0) return [];

  const target = targetTs(criteria);
  const out = shipments
    .map((s) => shipmentMatch(s, criteria, catalog, target))
    .filter((x): x is CostMatch => x !== null);

  out.push(...inputRateMatches(inputRates, criteria, catalog, target));

  return out.sort(
    (a, b) =>
      (b.score - a.score) ||
      (createdTs(b.createdAt) - createdTs(a.createdAt)) ||
      a.referenceId.localeCompare(b.referenceId)
  );
}
