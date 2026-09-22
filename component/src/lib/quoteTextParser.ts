// ============================================================================
// LOGI_QUOTE_COST_WORKFLOW_UX_01 — ONE deterministic quick-quote text parser.
//
// Shared by BOTH "DÁN BÁO GIÁ NHANH" (Báo Giá create/edit) and "DÁN THÔNG TIN
// KHÁCH / GIÁ CƯỚC" (Check chi phí). There is deliberately exactly one
// implementation: the cost-check workspace imports THIS module, it does not
// copy it.
//
// WHAT IT IS
//   A small, rule-based reader of the Vietnamese commercial shorthand the
//   Owner actually types in chat. It is NOT NLP and NOT an LLM integration:
//   no network, no model, no heuristics beyond the explicit rules below.
//
// WHAT IT MUST NEVER DO
//   UNKNOWN != ZERO. The parser never invents VAT, cost price, FX, customer,
//   validity, quantity, or an amount that the text does not state. A sentence
//   that carries no price becomes a quote ASSUMPTION, never a fake 0-price
//   service line. An amount introduced by "khoảng"/"ước tính" stays flagged as
//   an estimate requiring confirmation — it is never presented as a known cost.
// ============================================================================

/** A service line the operator really wrote in the pasted text. */
export interface ParsedQuoteLine {
  /** Display name, first letter capitalised; the operator's own wording. */
  name: string;
  /** Unit sell price exactly as stated. `null` when the text states none. */
  sell: number | null;
  /** VND / USD / CNY — only when the text says so (VND is the written default). */
  currency: string;
  /** "cont 20'", "cont", "kg", "cbm", "lô", "bill"… — "" when not stated. */
  unit: string;
  /** Conditional charge ("(nếu có)", "phát sinh"). */
  condition: "" | "IF_APPLICABLE";
  /** "khoảng"/"ước tính"/"chưa nắm rõ" → the amount is NOT a known cost. */
  status: "" | "ESTIMATE_REQUIRES_CONFIRMATION";
  /** Everything the operator wrote about this line, preserved verbatim. */
  note: string;
  /** The exact source line, for the review preview. */
  raw: string;
}

export interface ParsedQuote {
  incoterm: string;
  origin: string;
  destination: string;
  /** Số khối, when the text states one (Check chi phí). */
  cbm: number | null;
  /** Cân nặng in kg, when the text states one (Check chi phí). */
  weightKg: number | null;
  lines: ParsedQuoteLine[];
  /** General statements with no price — quote assumptions, never fake lines. */
  assumptions: string[];
  /** Lines the parser could not understand; shown to the operator as-is. */
  unparsed: string[];
}

export const EMPTY_PARSE: ParsedQuote = {
  incoterm: "",
  origin: "",
  destination: "",
  cbm: null,
  weightKg: null,
  lines: [],
  assumptions: [],
  unparsed: [],
};

const INCOTERMS = ["EXW", "FCA", "FAS", "FOB", "CFR", "CIF", "CPT", "CIP", "DAP", "DPU", "DDP"];

/** Section headers / separators that carry no business fact of their own. */
const SECTION_RE = /^(vn|việt nam|vietnam|tq|cn|trung quốc|china|nước ngoài|local charges?|phí địa phương)\s*:?\s*$/i;

/** Strip a leading bullet ("-", "•", "+", "1.") without touching the content. */
function stripBullet(line: string): string {
  return line.replace(/^\s*(?:[-–—•*]|\d+[.)])\s*/, "").trim();
}

function capitalise(text: string): string {
  const t = text.trim();
  if (!t) return "";
  return t.charAt(0).toUpperCase() + t.slice(1);
}

/**
 * One Vietnamese shorthand amount → a plain number.
 *
 *   "9.5 triệu" → 9500000   "9.5tr" → 9500000   "250k" → 250000
 *   "2 triệu"   → 2000000   "950"   → 950       "1.200.000" → 1200000
 *
 * `null` when the token is not an amount. Never rounds a stated value away.
 */
export function parseVnAmount(token: string): number | null {
  const raw = String(token || "").trim().toLowerCase();
  if (!raw) return null;
  const m = raw.match(/^([0-9][0-9.,\s]*)\s*(tr|triệu|trieu|k|nghìn|nghin|ngàn|ngan|tỷ|ty|tỉ)?$/);
  if (!m) return null;
  let digits = m[1].replace(/\s/g, "");
  // "1.200.000" / "1,200,000" are thousands groupings; "9.5" / "9,5" is a decimal.
  if (/^\d{1,3}([.,]\d{3})+$/.test(digits)) digits = digits.replace(/[.,]/g, "");
  else digits = digits.replace(/,/g, ".");
  const value = Number(digits);
  if (!Number.isFinite(value)) return null;
  const suffix = m[2] || "";
  if (suffix === "tr" || suffix === "triệu" || suffix === "trieu") return value * 1_000_000;
  if (suffix === "tỷ" || suffix === "ty" || suffix === "tỉ") return value * 1_000_000_000;
  if (suffix) return value * 1_000;
  return value;
}

/** Currency stated on an amount fragment. VND is the written default. */
function currencyOf(fragment: string): string {
  const f = fragment.toLowerCase();
  if (/\$|\busd\b|\bđô\b|\bdola\b/.test(f)) return "USD";
  if (/\brmb\b|\bcny\b|\btệ\b|\bte\b(?!n)/.test(f)) return "CNY";
  return "VND";
}

const UNIT_PATTERNS: Array<[RegExp, string]> = [
  [/cont(?:ainer)?\s*40\s*(?:'|hc|hq|feet|ft)?/i, "cont 40'"],
  [/cont(?:ainer)?\s*20\s*(?:'|feet|ft)?/i, "cont 20'"],
  [/\bcont(?:ainer)?\b/i, "cont"],
  [/\bcbm\b|\bkhối\b|\bkhoi\b|\bm3\b/i, "cbm"],
  [/\bkgs?\b|\bkí\b|\bkilo\b/i, "kg"],
  [/\btấn\b|\btan\b/i, "tấn"],
  [/\bbill\b|\bb\/l\b|\bhbl\b|\bmbl\b/i, "bill"],
  [/\blô\b|\blo\b|\bshipment\b/i, "lô"],
  [/\bxe\b|\btruck\b/i, "xe"],
  [/\bchuyến\b/i, "chuyến"],
  [/\bkiện\b/i, "kiện"],
  [/\blần\b/i, "lần"],
];

function unitOf(fragment: string): string {
  for (const [re, unit] of UNIT_PATTERNS) if (re.test(fragment)) return unit;
  return "";
}

/**
 * The first amount inside a value fragment, with its currency and unit.
 * Returns `null` when the fragment states no amount at all.
 */
function readAmount(fragment: string): { sell: number; currency: string; unit: string } | null {
  // number [currency] [ / unit ]  — currency may precede or follow the number.
  const re = /(?:\$\s*)?([0-9][0-9.,]*)\s*(usd|uds|\$|rmb|cny|tệ|triệu|trieu|tr|k|nghìn|nghin|ngàn|ngan|tỷ|ty|tỉ)?\b/i;
  const m = fragment.match(re);
  if (!m) return null;
  const numberPart = m[1];
  const suffix = (m[2] || "").toLowerCase();
  const isCurrency = /^(usd|uds|\$|rmb|cny|tệ)$/.test(suffix);
  const amount = parseVnAmount(isCurrency || !suffix ? numberPart : `${numberPart}${suffix}`);
  if (amount == null) return null;
  const head = fragment.slice(0, (m.index ?? 0) + m[0].length + 6);
  const currency = isCurrency ? currencyOf(suffix) : currencyOf(head);
  // The unit is what follows the slash after the amount ("950 usd/ cont 20'").
  const after = fragment.slice((m.index ?? 0) + m[0].length);
  const slash = after.match(/^\s*(?:usd|rmb|cny|\$)?\s*\/\s*([^,;()]*)/i);
  const unit = unitOf(slash ? slash[1] : after.split(/[-–—(]/)[0] || "");
  return { sell: amount, currency, unit };
}

/** "vượt 20 tấn + 80 usd/cont" → a normalised, explicit surcharge sentence. */
function surchargeNotes(text: string): string[] {
  const out: string[] = [];
  const over = text.match(/vượt\s+([0-9.,]+)\s*(tấn|tan|kg|cbm|khối)[^+]*\+\s*([0-9][0-9.,]*\s*(?:usd|\$|rmb|cny|tr|triệu|k|nghìn)?)\s*(?:\/\s*([^\s,;)]+))?/i);
  if (over) {
    const amount = readAmount(over[3]);
    const per = over[4] ? `/${over[4]}` : "";
    if (amount) out.push(`Nếu vượt ${over[1]} ${over[2]}: +${amount.sell} ${amount.currency}${per}`);
  }
  const plus = text.match(/(?<!vượt[^+]{0,40})\+\s*([0-9][0-9.,]*\s*(?:usd|\$|rmb|cny|tr|triệu|k|nghìn|nghin)?)\s*(?:\/\s*([^\s,;)]+))?/i);
  if (plus && !over) {
    const amount = readAmount(plus[1]);
    if (amount) out.push(`Phụ phí thêm: +${amount.sell} ${amount.currency}${plus[2] ? `/${plus[2]}` : ""}`);
  }
  return out;
}

/** Route/Incoterm header: "FOB NINGBO - Hải Phòng:" / "EXW Guangdong - Hà Nội". */
function readRouteHeader(line: string): { incoterm: string; origin: string; destination: string } | null {
  const text = line.replace(/:\s*$/, "").trim();
  const m = text.match(
    new RegExp(`^(${INCOTERMS.join("|")})\\b[\\s:.-]*(.*)$`, "i")
  );
  if (!m) return null;
  const incoterm = m[1].toUpperCase();
  const rest = (m[2] || "").trim();
  const parts = rest.split(/\s+(?:-|–|—|→|=>|>)\s+|\s*→\s*/).map((p) => p.trim()).filter(Boolean);
  return {
    incoterm,
    origin: parts[0] ? parts[0].replace(/[:,]$/, "") : "",
    destination: parts[1] ? parts[1].replace(/[:,]$/, "") : "",
  };
}

/** "5 khối" / "5 cbm" → 5. */
function readCbm(line: string): number | null {
  const m = line.match(/([0-9][0-9.,]*)\s*(?:cbm|khối|khoi|m3)\b/i);
  if (!m) return null;
  return parseVnAmount(m[1]);
}

/** True when a fragment states ONLY a cargo quantity ("5 khối", "800 kg"). */
function isCargoFactOnly(fragment: string): boolean {
  const text = fragment.trim();
  if (!text) return false;
  return /^[0-9][0-9.,]*\s*(?:cbm|khối|khoi|m3|kgs?|kí|kilo|tấn|tan)$/i.test(text);
}

/** "800 kg" / "0.8 tấn" → kilograms. */
function readWeight(line: string): number | null {
  const kg = line.match(/([0-9][0-9.,]*)\s*(?:kgs?|kí|kilo)\b/i);
  if (kg) return parseVnAmount(kg[1]);
  const tan = line.match(/([0-9][0-9.,]*)\s*(?:tấn|tan)\b/i);
  if (tan) {
    const value = parseVnAmount(tan[1]);
    return value == null ? null : value * 1000;
  }
  return null;
}

/**
 * Parse pasted quick-quote text into a REVIEWABLE draft.
 *
 * The caller must show the result to the operator and apply it only on an
 * explicit click — this function performs no mutation of its own.
 */
export function parseQuoteText(input: string): ParsedQuote {
  const result: ParsedQuote = { ...EMPTY_PARSE, lines: [], assumptions: [], unparsed: [] };
  const rawLines = String(input || "").split(/\r?\n/);

  for (const rawLine of rawLines) {
    const trimmed = rawLine.trim();
    if (!trimmed) continue;
    if (/^[-–—=_*]{2,}$/.test(trimmed)) continue; // "---" separator
    const body = stripBullet(trimmed);
    if (!body) continue;
    if (SECTION_RE.test(body)) continue;

    // 1 — route / Incoterm header. A customer often states the whole inquiry on
    // ONE line ("EXW Guangdong - Hà Nội / 5 khối / 800 kg"), so the trailing
    // slash-separated CARGO facts are split off first and the route is read
    // from what remains. A segment is only removed when it is nothing BUT a
    // cargo fact, so a place name containing "/" is never eaten.
    let routeText = body;
    const trailingCargo: string[] = [];
    if (/^\s*(?:[A-Za-z]{3})\b/.test(body) && body.includes("/")) {
      const segments = body.split("/").map((part) => part.trim());
      while (segments.length > 1 && isCargoFactOnly(segments[segments.length - 1])) {
        trailingCargo.unshift(segments.pop() as string);
      }
      if (trailingCargo.length > 0) routeText = segments.join("/").trim();
    }
    const header = readRouteHeader(routeText);
    if (header && !result.incoterm) {
      result.incoterm = header.incoterm;
      if (header.origin) result.origin = header.origin;
      if (header.destination) result.destination = header.destination;
      for (const fact of trailingCargo) {
        const cbm = readCbm(fact);
        if (cbm != null && result.cbm == null) { result.cbm = cbm; continue; }
        const weight = readWeight(fact);
        if (weight != null && result.weightKg == null) result.weightKg = weight;
      }
      continue;
    }

    // 2 — standalone cargo facts used by Check chi phí.
    const looksLikeService = body.includes(":");
    if (!looksLikeService) {
      const cbm = readCbm(body);
      const weight = readWeight(body);
      if (cbm != null && result.cbm == null && /cbm|khối|khoi|m3/i.test(body)) {
        result.cbm = cbm;
        if (weight != null && result.weightKg == null) result.weightKg = weight;
        continue;
      }
      if (weight != null && result.weightKg == null && /kgs?|kí|kilo|tấn|tan/i.test(body)) {
        result.weightKg = weight;
        continue;
      }
    }

    // 3 — "name: value" service line, or a general statement.
    const colon = body.indexOf(":");
    if (colon <= 0) {
      // No price, no colon → an assumption the quotation must carry.
      result.assumptions.push(body);
      continue;
    }
    const namePart = body.slice(0, colon).trim();
    const valuePart = body.slice(colon + 1).trim();
    const amount = readAmount(valuePart);
    if (!amount) {
      // A statement written with a colon but carrying no amount is STILL an
      // assumption — never a service line priced at a fabricated 0.
      result.assumptions.push(body);
      continue;
    }

    const conditional = /\(\s*nếu có\s*\)|\bnếu có\b|\bphát sinh\b|\bnếu phát sinh\b/i.test(namePart);
    const approximate = /\bkhoảng\b|\bước tính\b|\buoc tinh\b|\btạm tính\b|\bchưa nắm rõ\b|\bchưa rõ\b/i.test(body);

    const cleanName = capitalise(
      namePart.replace(/\(\s*nếu có\s*\)/gi, "").replace(/\s{2,}/g, " ").trim()
    );

    // Everything the operator wrote ABOUT the price, preserved verbatim.
    const noteParts: string[] = [];
    if (conditional) noteParts.push("Có thể phát sinh (nếu có)");
    if (approximate) noteParts.push("Ước tính — cần xác nhận, chưa phải chi phí chắc chắn");
    const afterAmount = valuePart.slice(0);
    const trailing = afterAmount
      .split(/\s+[-–—]\s+/)
      .slice(1)
      .join(" - ")
      .trim();
    const parenthetical = [...afterAmount.matchAll(/\(([^)]*)\)/g)].map((m) => m[1].trim());
    for (const p of parenthetical) if (p) noteParts.push(p);
    if (trailing) noteParts.push(trailing.replace(/\([^)]*\)/g, "").trim());
    for (const s of surchargeNotes(afterAmount)) noteParts.push(s);
    if (approximate) {
      const literal = afterAmount.match(/(khoảng|KHOẢNG|ước tính)\s*[0-9][^,;()]*/i);
      if (literal) noteParts.push(literal[0].trim());
    }

    const note = noteParts
      .map((p) => p.replace(/\s{2,}/g, " ").trim())
      .filter((p, i, arr) => p && arr.indexOf(p) === i)
      .join(" · ");

    result.lines.push({
      name: cleanName,
      sell: amount.sell,
      currency: amount.currency,
      unit: amount.unit,
      condition: conditional ? "IF_APPLICABLE" : "",
      status: approximate ? "ESTIMATE_REQUIRES_CONFIRMATION" : "",
      note,
      raw: trimmed,
    });
  }

  // A route stated without an Incoterm keyword ("Ningbo - Hải Phòng").
  if (!result.origin && !result.destination) {
    for (const rawLine of rawLines) {
      const t = rawLine.trim();
      if (!t || t.includes(":")) continue;
      const m = t.match(/^([^-–—>]{2,40})\s+(?:-|–|—|→|>)\s+([^-–—>]{2,40})$/);
      if (m) {
        result.origin = m[1].trim();
        result.destination = m[2].trim();
        break;
      }
    }
  }

  return result;
}

/** True when a parse produced nothing an operator could review. */
export function isEmptyParse(p: ParsedQuote): boolean {
  return (
    !p.incoterm && !p.origin && !p.destination && p.cbm == null && p.weightKg == null
    && p.lines.length === 0 && p.assumptions.length === 0
  );
}
