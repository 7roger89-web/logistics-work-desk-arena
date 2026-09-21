// ============================================================================
// LOGI_SHIPMENT_GLANCEABLE_SUPPORT_UX_01 (issue #86) — the shared GLANCEABLE
// recognition strip used by the lot detail header and the Lô Hàng list.
//
// WHY THIS FILE EXISTS
// Sale/Support recognize a shipment by five facts: Incoterm, transport mode,
// load model, ETD, ETA. Before this slice none of them was rendered in the list
// at all, and on the detail page they only appeared inside the profile editor /
// transport tab — so every row had to be OPENED before it could be read. All
// five facts are ALREADY on the row the backend projects (`executionProfile` +
// `transportLegs`), so this module only FORMATS what it is handed. One formatter
// exists so the list and the detail header can never drift apart.
//
// WHAT THIS MODULE DELIBERATELY IS NOT
//   * not a reader — no fetch, no store subscription, no query, no view model;
//     it renders the shipment row it receives and nothing else;
//   * not a persistence surface — it writes nothing, owns no state/draft, and
//     NO duplicated display summary is ever saved: the strip is derived at
//     render time from the existing projection;
//   * not a business authority — it derives no operational stage, no task, no
//     missingDoc, no status, no dashboard alert and no next action. An unknown
//     fact renders as an explicit "—" (a DISPLAY gap), never as a silent hole
//     that makes an incomplete lot look complete;
//   * not metadata infrastructure — five labels, one date formatter, one strip.
//
// ETD/ETA MEANING IS THE EXISTING CANONICAL ONE, mirrored from
// `core.shipment_operations.compatibility_facts()`:
//   etd = FIRST non-empty ETD over the legs ordered by `sequence`
//   eta = LAST  non-empty ETA over those same legs
// There is deliberately no "main leg" guess and no new backend reader; this copy
// exists only so the browser can label the row it was already given.
// ============================================================================

import { cx } from "../lib/format";
import type { Shipment } from "../lib/viewmodel";

/** The app's own em dash for a value the backend genuinely does not know. */
const GAP = "—";

/** The five recognition facts, already formatted for display ("" = unknown). */
export interface ShipmentQuickFactRow {
  /** Incoterms code as the execution profile projects it ("CIF"). */
  incoterm: string;
  /** Vietnamese mode label from the SAME profile ("Đường biển"). */
  modeLabel: string;
  /** Compact load-model wording ("FCL" from "FCL — nguyên container"). */
  loadLabel: string;
  /** ETD for the strip ("05/09"), "" when no leg states one. */
  etd: string;
  /** ETA for the strip ("12/09"), "" when no leg states one. */
  eta: string;
  /** Full ETD for the hover/accessible hint ("05/09/2026"), "" when unknown. */
  etdFull: string;
  /** Full ETA for the hover/accessible hint, "" when unknown. */
  etaFull: string;
}

type QuickFactsInput = Pick<Shipment, "executionProfile" | "transportLegs">;

const ISO_DATE = /^(\d{4})-(\d{2})-(\d{2})/;
const DMY_DATE = /^(\d{1,2})\/(\d{1,2})\/(\d{4})$/;

/** The parts of a date the app may receive: ISO, ISO datetime or DD/MM/YYYY. */
function dateParts(raw: string): { dd: string; mm: string; yyyy: string } | null {
  const value = raw.trim();
  const iso = ISO_DATE.exec(value);
  if (iso) return { yyyy: iso[1], mm: iso[2], dd: iso[3] };
  const dmy = DMY_DATE.exec(value);
  if (dmy) {
    return {
      dd: dmy[1].padStart(2, "0"),
      mm: dmy[2].padStart(2, "0"),
      yyyy: dmy[3],
    };
  }
  return null;
}

/**
 * Compact recognition form `dd/mm`.
 *
 * A date the app cannot parse is shown EXACTLY as stored rather than dropped:
 * a differently typed value is still a fact the operator recorded, and silently
 * hiding it would understate what the lot already has.
 */
function shortDate(raw: string): string {
  const value = raw.trim();
  if (!value) return "";
  const parts = dateParts(value);
  return parts ? `${parts.dd}/${parts.mm}` : value;
}

/** The full `dd/mm/yyyy` hint behind the compact form (year is never invented). */
function fullDate(raw: string): string {
  const value = raw.trim();
  if (!value) return "";
  const parts = dateParts(value);
  return parts ? `${parts.dd}/${parts.mm}/${parts.yyyy}` : value;
}

/**
 * The load-model chip: "FCL — nguyên container" → "FCL".
 *
 * The explanation half belongs to the profile editor, not to a row that must be
 * scanned in a second; a label without a ` — ` separator (e.g. "Khác / chưa xác
 * định") is kept whole because shortening it would change its meaning.
 */
function loadChip(label: string): string {
  const value = label.trim();
  if (!value) return "";
  const [code] = value.split("—");
  return (code ?? "").trim() || value;
}

/** First non-empty value in the given order — never a fabricated fallback. */
function firstFilled(values: readonly string[]): string {
  return values.map((v) => (v ?? "").trim()).find((v) => v.length > 0) ?? "";
}

/**
 * The five recognition facts of ONE already-projected shipment row.
 *
 * PURE: same row in, same labels out. It is called once per rendered row (the
 * row itself is built once by the backend — `EXECUTION_PROFILE_BUILDS_PER_ROW=1`
 * is untouched because no profile is built here at all).
 */
export function quickFactsFor(shipment: QuickFactsInput): ShipmentQuickFactRow {
  const profile = shipment.executionProfile;
  // Same ordering rule as `compatibility_facts()`: legs by `sequence`, then the
  // first non-empty ETD forward and the last non-empty ETA backward.
  const ordered = [...(shipment.transportLegs ?? [])].sort(
    (a, b) => (Number(a?.sequence) || 0) - (Number(b?.sequence) || 0)
  );
  const etdRaw = firstFilled(ordered.map((leg) => leg?.etd ?? ""));
  const etaRaw = firstFilled([...ordered].reverse().map((leg) => leg?.eta ?? ""));
  return {
    incoterm: (profile?.incoterm ?? "").trim(),
    modeLabel: (profile?.modeLabel ?? "").trim(),
    loadLabel: loadChip(profile?.loadModelLabel ?? ""),
    etd: shortDate(etdRaw),
    eta: shortDate(etaRaw),
    etdFull: fullDate(etdRaw),
    etaFull: fullDate(etaRaw),
  };
}

/**
 * One recognition chip.
 *
 * Known → neutral slate. Unknown → restrained amber + the label spelled out
 * with an em dash ("Incoterm —"), so the GAP itself is readable, is announced to
 * a screen reader, and does not depend on colour alone.
 */
function FactChip({
  testId, label, value, dense,
}: {
  testId: string;
  label: string;
  value: string;
  dense?: boolean;
}) {
  const known = value.length > 0;
  return (
    <span
      data-testid={testId}
      data-known={known ? "true" : "false"}
      title={known ? `${label}: ${value}` : `${label}: chưa có`}
      className={cx(
        "inline-flex items-center rounded-lg border font-bold whitespace-nowrap",
        dense ? "px-2 py-0.5 text-[12px]" : "px-2.5 py-1 text-[13px]",
        known
          ? "border-slate-200 bg-slate-50 text-slate-800"
          : "border-dashed border-amber-400 bg-amber-50 text-amber-900"
      )}
    >
      {known ? value : `${label} ${GAP}`}
    </span>
  );
}

/**
 * The quick-facts strip: `[CIF] [Đường biển] [FCL]  ETD 05/09 → ETA 12/09`.
 *
 * `dense` is the list-row variant (tighter chips); the detail header uses the
 * comfortable one. Neither variant adds a click, a fetch or a state — the strip
 * is pure presentation over the row that is already on screen.
 */
export function ShipmentQuickFacts({
  shipment, dense, className,
}: {
  shipment: QuickFactsInput;
  dense?: boolean;
  className?: string;
}) {
  const facts = quickFactsFor(shipment);
  const gapCount = [facts.incoterm, facts.modeLabel, facts.loadLabel, facts.etd, facts.eta]
    .filter((value) => value.length === 0).length;
  return (
    <div
      role="group"
      aria-label="Thông tin nhận dạng nhanh của lô"
      data-testid="shipment-quick-facts"
      data-gap-count={gapCount}
      className={cx("flex flex-wrap items-center gap-1.5", className)}
    >
      <FactChip testId="quick-fact-incoterm" label="Incoterm" value={facts.incoterm} dense={dense} />
      <FactChip testId="quick-fact-mode" label="Phương thức" value={facts.modeLabel} dense={dense} />
      <FactChip testId="quick-fact-load" label="Loại hàng" value={facts.loadLabel} dense={dense} />
      <span
        data-testid="quick-fact-schedule"
        data-etd-known={facts.etd ? "true" : "false"}
        data-eta-known={facts.eta ? "true" : "false"}
        title={`ETD ${facts.etdFull || GAP} → ETA ${facts.etaFull || GAP}`}
        aria-label={`ETD ${facts.etdFull || "chưa có"} → ETA ${facts.etaFull || "chưa có"}`}
        className={cx(
          "inline-flex items-center gap-1.5 rounded-lg border font-bold whitespace-nowrap tabular-nums",
          dense ? "px-2 py-0.5 text-[12px]" : "px-2.5 py-1 text-[13px]",
          facts.etd && facts.eta
            ? "border-slate-200 bg-slate-50 text-slate-800"
            : "border-dashed border-amber-400 bg-amber-50 text-amber-900"
        )}
      >
        <span data-testid="quick-fact-etd">ETD {facts.etd || GAP}</span>
        <span aria-hidden="true" className="text-slate-400">→</span>
        <span data-testid="quick-fact-eta">ETA {facts.eta || GAP}</span>
      </span>
    </div>
  );
}
