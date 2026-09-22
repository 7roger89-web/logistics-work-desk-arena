// ============================================================================
// LOGI_QUOTE_COST_WORKFLOW_UX_01 — safe mini calculator for quotation numbers.
//
// The Owner types "370*8", "=370*8", "9.5tr*2", "250k*4", "=SUM(370,80,50)"
// into money fields. This evaluates exactly that, with a recursive-descent
// parser over a CLOSED token allowlist.
//
// ABSOLUTELY FORBIDDEN and structurally impossible here: eval(), Function(),
// executing JavaScript or Python, cell references, file/network references,
// macros, and arbitrary identifiers. The only names accepted are the four
// functions below; anything else is a validation error, never an execution.
// ============================================================================

export interface CalcResult {
  ok: boolean;
  /** The evaluated number when ok. */
  value: number | null;
  /** A short Vietnamese validation message when not ok. */
  error: string;
}

const FUNCTIONS = new Set(["SUM", "ROUND", "MIN", "MAX"]);

type Token =
  | { t: "num"; v: number }
  | { t: "op"; v: "+" | "-" | "*" | "/" | "%" }
  | { t: "lp" }
  | { t: "rp" }
  | { t: "comma" }
  | { t: "fn"; v: string };

const SUFFIX = /^(tr|triệu|trieu|k|nghìn|nghin|ngàn|ngan|tỷ|tỉ|ty)/i;

function suffixFactor(raw: string): number {
  const s = raw.toLowerCase();
  if (s === "tr" || s === "triệu" || s === "trieu") return 1_000_000;
  if (s === "tỷ" || s === "tỉ" || s === "ty") return 1_000_000_000;
  return 1_000;
}

/** Tokenise, refusing anything outside the allowlist. */
function tokenize(input: string): { tokens: Token[]; error: string } {
  const tokens: Token[] = [];
  let i = 0;
  const src = input;
  while (i < src.length) {
    const ch = src[i];
    if (/\s/.test(ch)) { i += 1; continue; }
    if (ch === "(") { tokens.push({ t: "lp" }); i += 1; continue; }
    if (ch === ")") { tokens.push({ t: "rp" }); i += 1; continue; }
    if (ch === "," || ch === ";") {
      // A comma is a decimal separator only inside a number (handled below);
      // standing alone it separates function arguments.
      tokens.push({ t: "comma" }); i += 1; continue;
    }
    if ("+-*/".includes(ch)) { tokens.push({ t: "op", v: ch as "+" }); i += 1; continue; }
    if (ch === "%") { tokens.push({ t: "op", v: "%" }); i += 1; continue; }
    if (/[0-9.]/.test(ch)) {
      const m = src.slice(i).match(/^[0-9][0-9.]*|^\.[0-9]+/);
      if (!m) return { tokens, error: "Số không hợp lệ." };
      let digits = m[0];
      i += m[0].length;
      // "1.200.000" is a thousands grouping; "9.5" is a decimal.
      if (/^\d{1,3}(\.\d{3})+$/.test(digits)) digits = digits.replace(/\./g, "");
      let value = Number(digits);
      if (!Number.isFinite(value)) return { tokens, error: "Số không hợp lệ." };
      const sm = src.slice(i).match(SUFFIX);
      if (sm) { value *= suffixFactor(sm[0]); i += sm[0].length; }
      tokens.push({ t: "num", v: value });
      continue;
    }
    if (/[A-Za-zÀ-ỹ]/.test(ch)) {
      const m = src.slice(i).match(/^[A-Za-zÀ-ỹ]+/);
      const word = (m ? m[0] : ch);
      const upper = word.toUpperCase();
      if (FUNCTIONS.has(upper)) {
        tokens.push({ t: "fn", v: upper });
        i += word.length;
        continue;
      }
      return { tokens, error: `Không hiểu “${word}” — chỉ dùng số, + - * / ( ) %, k/tr, SUM, ROUND, MIN, MAX.` };
    }
    return { tokens, error: `Ký tự không hợp lệ: “${ch}”.` };
  }
  return { tokens, error: "" };
}

class Parser {
  private pos = 0;
  constructor(private readonly tokens: Token[]) {}

  peek(): Token | undefined { return this.tokens[this.pos]; }
  next(): Token | undefined { return this.tokens[this.pos++]; }

  parseExpression(): number {
    let left = this.parseTerm();
    for (;;) {
      const tk = this.peek();
      if (tk && tk.t === "op" && (tk.v === "+" || tk.v === "-")) {
        this.next();
        const right = this.parseTerm();
        left = tk.v === "+" ? left + right : left - right;
      } else return left;
    }
  }

  parseTerm(): number {
    let left = this.parseUnary();
    for (;;) {
      const tk = this.peek();
      if (tk && tk.t === "op" && (tk.v === "*" || tk.v === "/")) {
        this.next();
        const right = this.parseUnary();
        if (tk.v === "/") {
          if (right === 0) throw new Error("Không chia được cho 0.");
          left = left / right;
        } else left = left * right;
      } else return left;
    }
  }

  parseUnary(): number {
    const tk = this.peek();
    if (tk && tk.t === "op" && (tk.v === "+" || tk.v === "-")) {
      this.next();
      const value = this.parseUnary();
      return tk.v === "-" ? -value : value;
    }
    return this.parsePostfix();
  }

  parsePostfix(): number {
    let value = this.parsePrimary();
    for (;;) {
      const tk = this.peek();
      if (tk && tk.t === "op" && tk.v === "%") { this.next(); value = value / 100; }
      else return value;
    }
  }

  parsePrimary(): number {
    const tk = this.next();
    if (!tk) throw new Error("Biểu thức chưa hoàn chỉnh.");
    if (tk.t === "num") return tk.v;
    if (tk.t === "lp") {
      const value = this.parseExpression();
      const close = this.next();
      if (!close || close.t !== "rp") throw new Error("Thiếu dấu đóng ngoặc.");
      return value;
    }
    if (tk.t === "fn") {
      const open = this.next();
      if (!open || open.t !== "lp") throw new Error(`${tk.v} cần dấu ngoặc mở.`);
      const args: number[] = [];
      if (this.peek() && this.peek()!.t === "rp") this.next();
      else {
        for (;;) {
          args.push(this.parseExpression());
          const sep = this.next();
          if (sep && sep.t === "comma") continue;
          if (sep && sep.t === "rp") break;
          throw new Error(`${tk.v} thiếu dấu đóng ngoặc.`);
        }
      }
      if (args.length === 0) throw new Error(`${tk.v} cần ít nhất một số.`);
      if (tk.v === "SUM") return args.reduce((a, b) => a + b, 0);
      if (tk.v === "MIN") return Math.min(...args);
      if (tk.v === "MAX") return Math.max(...args);
      // ROUND(value, digits)
      const digits = args.length > 1 ? Math.trunc(args[1]) : 0;
      const factor = Math.pow(10, digits);
      return Math.round(args[0] * factor) / factor;
    }
    throw new Error("Biểu thức không hợp lệ.");
  }

  atEnd(): boolean { return this.pos >= this.tokens.length; }
}

/**
 * Evaluate ONE operator-typed money expression.
 *
 * A plain number ("2500000", "9.5tr") evaluates to itself, so the same helper
 * can normalise every quotation numeric field on blur/Enter.
 */
export function evaluateAmountExpression(input: string): CalcResult {
  const raw = String(input ?? "").trim();
  if (!raw) return { ok: true, value: null, error: "" };
  const body = raw.startsWith("=") ? raw.slice(1).trim() : raw;
  if (!body) return { ok: false, value: null, error: "Biểu thức trống." };
  if (body.length > 200) return { ok: false, value: null, error: "Biểu thức quá dài." };
  const { tokens, error } = tokenize(body);
  if (error) return { ok: false, value: null, error };
  if (tokens.length === 0) return { ok: false, value: null, error: "Biểu thức trống." };
  try {
    const parser = new Parser(tokens);
    const value = parser.parseExpression();
    if (!parser.atEnd()) return { ok: false, value: null, error: "Biểu thức không hợp lệ." };
    if (!Number.isFinite(value)) return { ok: false, value: null, error: "Kết quả không hợp lệ." };
    return { ok: true, value, error: "" };
  } catch (e) {
    return { ok: false, value: null, error: e instanceof Error ? e.message : "Biểu thức không hợp lệ." };
  }
}

/** True when the text is more than a plain number (worth showing a result). */
export function looksLikeExpression(input: string): boolean {
  const raw = String(input ?? "").trim();
  if (!raw) return false;
  if (raw.startsWith("=")) return true;
  return /[+\-*/()%]|[A-Za-zÀ-ỹ]/.test(raw.replace(/^[-+]/, ""));
}
