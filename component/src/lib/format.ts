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
 * Millions ("tr") as used by the donor finance tiles.
 * UNKNOWN stays UNKNOWN instead of collapsing to "0 tr".
 */
export function fmtMillions(n: number | null | undefined): string {
  if (isUnknown(n)) return `${UNKNOWN} tr`;
  return `${(Number(n) / 1e6).toLocaleString("vi-VN")} tr`;
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
