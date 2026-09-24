import assert from "node:assert/strict";
import { importTs } from "./lib_loader.mjs";

const { findComparableCosts } = await importTs("component/src/lib/costHistory.ts");

const catalog = [
  { id: "P-SZX", kind: "PLACE", code: "CNSZX", name: "Shenzhen", aliases: [], active: true, zone_ids: ["PRD"] },
  { id: "P-NAN", kind: "PLACE", code: "CNNAN", name: "Nansha", aliases: [], active: true, zone_ids: ["PRD"] },
  { id: "P-HPH", kind: "PLACE", code: "VNHPH", name: "Hải Phòng", aliases: ["HPH"], active: true, zone_ids: ["HPH"] },
];

const row = (origin, equipment, amount) => ({
  id: "r-" + origin + equipment + amount,
  kind: "CHARGE",
  status: "AVAILABLE",
  chargeLabel: "Ocean Freight",
  carrier: { id: "C1", name: "COSCO", state: "CONFIRMED" },
  origin: { raw: origin, id: "", name: origin, zoneIds: origin === "Nansha" ? ["PRD"] : ["PRD"], state: "CONFIRMED" },
  destination: { raw: "HPH", id: "P-HPH", name: "Hải Phòng", zoneIds: ["HPH"], state: "CONFIRMED" },
  amount,
  currency: "USD",
  unit: "CONT",
  equipment,
  equipmentState: "CONFIRMED",
  rawLine: amount + " USD",
  confidence: "CONFIRMED",
});

const historicalRow = { ...row("Shenzhen", "20GP", 555), sourceDate: "2024-12-28" };

const rates = [
  {
    id: "RATE-OLD",
    record_type: "SUPPLIER_RATE_SNAPSHOT",
    status: "ACTIVE",
    received_at: "2025-01-01T00:00:00Z",
    supplier: "old agent",
    source_channel: "PASTE",
    raw_text: "old",
    parser_version: "1",
    rows: [row("Shenzhen", "20GP", 600)],
  },
  {
    id: "RATE-ZONE",
    record_type: "SUPPLIER_RATE_SNAPSHOT",
    status: "ACTIVE",
    received_at: "2026-09-22T00:00:00Z",
    supplier: "zone agent",
    source_channel: "PASTE",
    raw_text: "zone",
    parser_version: "1",
    rows: [row("Nansha", "20GP", 700)],
  },
  {
    id: "RATE-EXACT",
    record_type: "SUPPLIER_RATE_SNAPSHOT",
    status: "ACTIVE",
    received_at: "2026-09-23T00:00:00Z",
    supplier: "exact agent",
    source_channel: "PASTE",
    raw_text: "exact",
    parser_version: "1",
    rows: [row("Shenzhen", "20GP", 750)],
  },
  {
    id: "RATE-EXPIRED",
    record_type: "SUPPLIER_RATE_SNAPSHOT",
    status: "ACTIVE",
    received_at: "2026-09-20T00:00:00Z",
    supplier: "expired agent",
    source_channel: "PASTE",
    raw_text: "expired",
    parser_version: "1",
    rows: [{ ...row("Shenzhen", "20GP", 650), validUntil: "2026-09-21" }],
  },
  {
    id: "RATE-HISTORICAL-SECTION",
    record_type: "SUPPLIER_RATE_SNAPSHOT",
    status: "ACTIVE",
    received_at: "2026-09-24T00:00:00Z",
    supplier: "historical import",
    source_channel: "PASTE",
    raw_text: "historical section",
    parser_version: "1",
    rows: [historicalRow],
  },
  {
    id: "RATE-WRONG-EQ",
    record_type: "SUPPLIER_RATE_SNAPSHOT",
    status: "ACTIVE",
    received_at: "2026-09-24T00:00:00Z",
    supplier: "wrong equipment",
    source_channel: "PASTE",
    raw_text: "wrong",
    parser_version: "1",
    rows: [row("Shenzhen", "40HQ", 1200)],
  },
];

const shipment = (id, actual, createdAt) => ({
  id,
  customer: id,
  createdAt,
  incoterm: "EXW",
  mode: "Sea",
  transport: { pol: "Shenzhen", pod: "Hải Phòng" },
  pickup: { factory: "Shenzhen" },
  importInfo: { deliveryAddr: "Long Biên" },
  cargo: { cbm: 5, weight: 800 },
  finance: actual
    ? { actual: [{ label: "Ocean Freight", unit: "CONT", qty: 1, cost: 730, ccy: "USD" }], quote: [] }
    : { actual: [], quote: [{ label: "Ocean Freight", qty: 1, amount: 760, ccy: "USD" }] },
});

const equipmentCriteria = {
  incoterm: "EXW",
  origin: "Shenzhen",
  destination: "Hải Phòng",
  factory: "Shenzhen",
  pol: "Shenzhen",
  pod: "Hải Phòng",
  delivery: "Long Biên",
  loadModel: "FCL",
  equipment: "20GP",
  cbm: 5,
  weightKg: 800,
  mode: "Sea",
  targetDate: "2026-09-24",
};

const equipmentResults = findComparableCosts([], equipmentCriteria, rates, catalog);

const exact = equipmentResults.find((x) => x.referenceId.startsWith("RATE-EXACT:"));
const zone = equipmentResults.find((x) => x.referenceId.startsWith("RATE-ZONE:"));
const old = equipmentResults.find((x) => x.referenceId.startsWith("RATE-OLD:"));
const expired = equipmentResults.find((x) => x.referenceId.startsWith("RATE-EXPIRED:"));
const wrong = equipmentResults.find((x) => x.referenceId.startsWith("RATE-WRONG-EQ:"));
const historical = equipmentResults.find((x) => x.referenceId.startsWith("RATE-HISTORICAL-SECTION:"));

assert.ok(exact && zone && old && expired && historical);
assert.equal(wrong, undefined, "40HQ must never be returned for a 20GP request");
assert.ok(exact.score > zone.score, "exact Shenzhen should outrank same-zone Nansha");
assert.ok(zone.reasons.some((x) => x.includes("cùng vùng logistics")));
assert.ok(zone.differences.some((x) => x.includes("Nansha")));
assert.ok(exact.score > old.score, "recent rate should outrank stale otherwise-similar rate");
assert.ok(historical.ageDays > 365, "section source date must control historical age, not recent ingestion time");
assert.ok(exact.score > historical.score, "fresh exact rate must outrank a recently imported but historically old section");
assert.equal(expired.expired, true, "past validity must be labelled expired");
assert.ok(expired.differences.some((x) => x.includes("hết hiệu lực")));

const trustCriteria = {
  incoterm: "",
  origin: "Shenzhen",
  destination: "Hải Phòng",
  pol: "Shenzhen",
  pod: "Hải Phòng",
  factory: "",
  delivery: "",
  loadModel: "",
  equipment: "",
  cbm: null,
  weightKg: null,
  mode: "Sea",
  targetDate: "2026-09-24",
};
const trustResults = findComparableCosts(
  [shipment("ACTUAL-1", true, "2026-09-23"), shipment("QUOTE-1", false, "2026-09-23")],
  trustCriteria,
  [rates.find((x) => x.id === "RATE-EXACT")],
  catalog
);
assert.deepEqual(
  trustResults.slice(0, 3).map((x) => x.source),
  ["ACTUAL", "INPUT_RATE", "QUOTE"],
  "when relevance is comparable, trust order must be ACTUAL > INPUT_RATE > QUOTE"
);

const mixedShipment = {
  ...shipment("MIXED", true, "2026-09-23"),
  finance: {
    actual: [
      { label: "USD fee", unit: "SET", qty: 1, cost: 10, ccy: "USD" },
      { label: "VND fee", unit: "SET", qty: 1, cost: 100000, ccy: "VND" },
    ],
    quote: [],
  },
};
const mixed = findComparableCosts([mixedShipment], trustCriteria, [], catalog)[0];
assert.deepEqual(
  mixed.totalsByCurrency.map((x) => x.ccy).sort(),
  ["USD", "VND"],
  "currencies stay separate and are never silently summed"
);

console.log("PASS — Cost Intelligence deterministic matcher");
