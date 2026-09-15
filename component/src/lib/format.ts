// Supporting lib contract for the donor UI (lib/format).
// Pure browser utilities — no Node globals.

export function cx(
  ...parts: Array<string | false | null | undefined>
): string {
  return parts.filter(Boolean).join(" ");
}

/** The em dash shown for a value the backend genuinely does not know. */
export const UNKNOWN = "—";

/** True when a value is genuinely unknown (not merely zero). */
export function isUnknown(n: unknown): boolean {
  return n === null || n === undefined || n === "" ||
    (typeof n === "number" && Number.isNaN(n));
}

/**
 * Format a number with vi-VN grouping (no currency symbol).
 *
 * UNKNOWN != ZERO: a null/undefined/blank value renders as "—", never as "0".
 * Zero is a real amount and still renders as "0".
 */
export function fmtMoney(n: number | null | undefined, _ccy?: string): string {
  if (isUnknown(n)) return UNKNOWN;
  const value = Number(n);
  if (Number.isNaN(value)) return UNKNOWN;
  return value.toLocaleString("vi-VN");
}

/** Format VND with symbol; UNKNOWN renders as "— ₫". */
export function fmtVND(n: number | null | undefined): string {
  if (isUnknown(n)) return `${UNKNOWN} ₫`;
  return `${fmtMoney(n)} ₫`;
}

/**
 * Amount with its explicit currency code (VND / USD / CNY).
 *
 * NEVER converts. The backend carries one authoritative currency per shipment
 * (`shipments.currency` → `data["3.4"].currency`) and there is no FX engine in
 * the repository, so a USD amount is shown as a USD amount and is never summed
 * with another currency. The "VND" fallback mirrors core.logic's own default
 * (`shipment.get("currency", finance.get("currency", "VND"))`), it is not an
 * invented conversion.
 */
export function fmtCcy(n: number | null | undefined, ccy?: string | null): string {
  const code = (ccy || "VND").toUpperCase();
  if (isUnknown(n)) return `${UNKNOWN} ${code}`;
  return `${fmtMoney(n)} ${code}`;
}

/** Millions ("tr") tagged with the explicit currency. UNKNOWN stays UNKNOWN. */
export function fmtMillionsCcy(n: number | null | undefined, ccy?: string | null): string {
  const code = (ccy || "VND").toUpperCase();
  if (isUnknown(n)) return `${UNKNOWN} tr ${code}`;
  return `${(Number(n) / 1e6).toLocaleString("vi-VN")} tr ${code}`;
}

/** Percentage cell (actual margin). UNKNOWN renders as an em dash, never 0%. */
export function fmtPct(n: number | null | undefined): string {
  if (isUnknown(n)) return UNKNOWN;
  return `${Number(n).toLocaleString("vi-VN", { maximumFractionDigits: 2 })}%`;
}

/**
 * Millions ("tr") as used by the donor finance tiles.
 * UNKNOWN stays UNKNOWN instead of collapsing to "0 tr".
 */
export function fmtMillions(n: number | null | undefined): string {
  if (isUnknown(n)) return `${UNKNOWN} tr`;
  return `${(Number(n) / 1e6).toLocaleString("vi-VN")} tr`;
}

/**
 * Parse an amount the way the operator types it: `1.200.000`, `1,200,000`,
 * `1200000`, `8,5` or `8.5` → a number. `null` when nothing usable was typed.
 *
 * The RULES ARE THE APP'S OWN: this mirrors `core.utils.to_decimal`, the
 * canonical money parser already used by `safe_float` / `smart_money_parse` in
 * the Python writers, so a preview computed here cannot disagree with the
 * figure the backend books. It is a display/validation aid only — the amount
 * that is actually saved is the raw text the operator typed, re-read by the
 * backend. Returning `null` (instead of 0) for a blank is deliberate: UNKNOWN
 * != ZERO also holds in the browser.
 */
export function parseAmountVN(raw: string | number | null | undefined): number | null {
  if (raw == null) return null;
  if (typeof raw === "number") return Number.isFinite(raw) ? raw : null;
  const cleaned = String(raw).replace(/[^\d.,-]/g, "");
  if (!cleaned || !/\d/.test(cleaned)) return null;

  const lastComma = cleaned.lastIndexOf(",");
  const lastDot = cleaned.lastIndexOf(".");
  const commas = (cleaned.match(/,/g) || []).length;
  const dots = (cleaned.match(/\./g) || []).length;
  let normalized = cleaned;

  if (commas > 0 && dots > 0) {
    const decimal = lastComma > lastDot ? "," : ".";
    const grouping = decimal === "," ? "." : ",";
    const tail = cleaned.split(decimal).pop() ?? "";
    normalized = tail.length <= 2
      ? cleaned.split(grouping).join("").replace(decimal, ".")
      : cleaned.replace(/[.,]/g, "");
  } else if (commas > 1 || dots > 1) {
    normalized = cleaned.replace(/[.,]/g, "");
  } else if (commas === 1) {
    const [head, tail = ""] = cleaned.split(",");
    normalized = tail.length <= 2 ? `${head.replace(/,/g, "")}.${tail}` : cleaned.replace(/,/g, "");
  } else if (dots === 1) {
    const [head, tail = ""] = cleaned.split(".");
    if (tail.length === 3 && head.replace("-", "").length >= 1) normalized = cleaned.replace(/\./g, "");
  }

  const value = Number(normalized);
  return Number.isFinite(value) ? value : null;
}

/** Plain count/number cell with UNKNOWN support. */
export function fmtNum(n: number | string | null | undefined): string {
  if (isUnknown(n)) return UNKNOWN;
  const value = Number(n);
  if (Number.isNaN(value)) return String(n);
  return value.toLocaleString("vi-VN");
}

/** Text cell with UNKNOWN support. */
export function fmtText(value: string | null | undefined): string {
  const raw = (value ?? "").trim();
  return raw.length > 0 ? raw : UNKNOWN;
}

/**
 * Download a real generated Office file delivered by the backend.
 * Phase B removed the prototype .txt document export: PXK/HDMB/PL come from
 * core.docgen as real OOXML, never as a placeholder text file.
 */
export function downloadBinaryFile(
  name: string,
  base64: string | null,
  mime: string
): void {
  // A document that is not yet available on the session store has no bytes —
  // fail closed instead of throwing on an empty base64 payload.
  if (!base64) return;
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i += 1) bytes[i] = binary.charCodeAt(i);
  const blob = new Blob([bytes], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  setTimeout(() => URL.revokeObjectURL(url), 4000);
}
