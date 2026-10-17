import { useEffect, useRef, useState } from "react";
import { PencilLine, RotateCcw } from "lucide-react";
import type { CustomerTextRegion } from "../lib/excelQuote";
import { cx } from "../lib/format";

/**
 * SỬA NỘI DUNG TRỰC TIẾP — click a piece of text in the customer quotation and
 * type the new wording in place.
 *
 * Contract kept by this component:
 *  * clicking (or Enter/Space on the focused region) turns the text into an
 *    input/textarea exactly where it is;
 *  * Enter (or Ctrl/Cmd+Enter inside a multi-line region) applies, Escape
 *    cancels, clicking away applies;
 *  * the applied value is handed to the workspace, which writes it to the ONE
 *    canonical field or to the presentation override and sends it to Python;
 *  * a region whose wording differs from its default shows a restore control.
 *
 * Read-only regions — every amount, FX rate, tax percentage and total — are not
 * rendered through this component at all: the customer document shows them as
 * backend-computed numbers.
 */
export default function InlineText({ region, enabled, onApply, onRestore, tag = "span", className, testPrefix = "eq-text" }: {
  region: CustomerTextRegion;
  enabled: boolean;
  onApply: (value: string) => void;
  onRestore: () => void;
  tag?: "span" | "p" | "h3" | "h4" | "b" | "strong" | "div";
  className?: string;
  testPrefix?: string;
}) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(region.value);
  const input = useRef<HTMLInputElement | HTMLTextAreaElement | null>(null);
  const changed = region.value !== region.default;
  const multiline = region.multiline;

  useEffect(() => {
    if (editing) {
      input.current?.focus();
      input.current?.select();
    }
  }, [editing]);

  const commit = () => {
    onApply(draft);
    setEditing(false);
  };
  const cancel = () => {
    setDraft(region.value);
    setEditing(false);
  };
  const start = () => {
    if (!enabled) return;
    setDraft(region.value);
    setEditing(true);
  };
  const Tag = tag as "span";
  const shared = {
    "data-testid": `${testPrefix}-${region.id}`,
    "data-region": region.id,
    "data-source": region.source,
    "data-bound": region.bound ? "canonical-field" : "presentation-override",
    "data-mismatch": region.guarded && (region.mismatch || changed) ? "true" : "false",
  };

  if (editing) {
    const common = {
      ...shared,
      value: draft,
      "aria-label": `Sửa: ${region.label}`,
      "data-testid": `${testPrefix}-input-${region.id}`,
      className: "eq-inline-input",
      onBlur: commit,
      onKeyDown: (event: React.KeyboardEvent) => {
        if (event.key === "Escape") { event.preventDefault(); cancel(); return; }
        if (event.key !== "Enter") return;
        if (multiline && !(event.ctrlKey || event.metaKey)) return;
        event.preventDefault();
        commit();
      },
    };
    return multiline
      ? <textarea {...common} rows={Math.min(6, Math.max(2, draft.split("\n").length))} onChange={(e) => setDraft(e.target.value)} />
      : <input {...common} type="text" onChange={(e) => setDraft(e.target.value)} />;
  }

  return (
    <Tag {...shared} className={cx(className, "eq-inline", changed && "eq-inline-changed", !enabled && "eq-inline-off",
      region.guarded && (region.mismatch || changed) && "eq-inline-warn")}
      role={enabled ? "button" : undefined}
      tabIndex={enabled ? 0 : undefined}
      title={enabled ? `${region.label} — nhấp để sửa nội dung này` : `${region.label} — bật chế độ sửa để chỉnh`}
      onClick={start}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") { event.preventDefault(); start(); }
      }}>
      {/* An empty region still needs a click target. A paragraph says so in words;
          a short cell inside a table line stays compact so the line reads as data
          instead of carrying a sentence in the middle of it. */}
      <span className="eq-inline-value">{region.value || (enabled ? (region.kind === "LONG" ? "— nhấp để nhập nội dung —" : "＋") : "—")}</span>
      {enabled && <PencilLine size={13} className="eq-inline-mark" aria-hidden />}
      {changed && enabled && (
        <button type="button" className="eq-inline-restore" data-testid={`${testPrefix}-restore-${region.id}`}
          aria-label={`Khôi phục nội dung mặc định: ${region.label}`}
          onClick={(event) => { event.stopPropagation(); onRestore(); }}>
          <RotateCcw size={13} />
        </button>
      )}
    </Tag>
  );
}
