// Supporting lib contract for the donor UI (lib/format).
// Pure browser utilities — no Node globals.

export function cx(
  ...parts: Array<string | false | null | undefined>
): string {
  return parts.filter(Boolean).join(" ");
}

/** Format a number with vi-VN grouping (no currency symbol). */
export function fmtMoney(n: number, _ccy?: string): string {
  if (n === null || n === undefined || Number.isNaN(Number(n))) return "0";
  return Number(n).toLocaleString("vi-VN");
}

/** Format VND with symbol. */
export function fmtVND(n: number): string {
  return `${fmtMoney(n)} ₫`;
}

/** Download a text file in the browser (prototype document export). */
export function downloadTextFile(name: string, content: string): void {
  const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  setTimeout(() => URL.revokeObjectURL(url), 4000);
}
