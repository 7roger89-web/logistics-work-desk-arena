// ============================================================================
// LOGI_QUOTE_COST_WORKFLOW_UX_01 — focused unit acceptance for the ONE shared
// quick-quote parser and the safe mini calculator.
//
// Run: node tests/component/unit_quote_parser_calculator.mjs
// ============================================================================

import assert from "node:assert/strict";
import { importTs } from "./lib_loader.mjs";

const { parseQuoteText, parseVnAmount } = await importTs("component/src/lib/quoteTextParser.ts");
const { evaluateAmountExpression } = await importTs("component/src/lib/miniCalc.ts");

let passed = 0;
const ok = (name) => { passed += 1; console.log(`  ✓ ${name}`); };

// ---------------------------------------------------------------------------
// The Owner's EXACT quick-quote fixture (mandatory).
// ---------------------------------------------------------------------------
const OWNER_SAMPLE = `FOB NINGBO - Hải Phòng:
Cước biển: 950 usd/ cont 20' - cước tại thời điểm này (nếu vượt 20 tấn + 80 usd/cont)
---
VN:
- Phụ phí hãng tàu: 9.5 triệu/cont 20'
- nâng cont, hạ vỏ: 2.6 triệu/cont 20'
- Hạ tầng: 250k/cont 20'
- thủ tục hải quan: 2 triệu/cont
- vận tải về Sơn Tây, Hà Nội: 6 tr/cont 20' (hàng về cảng lach huyện + 500k/cont) - theo giá cước xăng dầu tại thời điểm này
- kiểm hóa mở cont (nếu có): 4 triệu/cont - đối với hàng không phát hiện nghi vấn
- Kiểm hóa soi chiếu (nếu có): 2 triệu/cont - đối với hàng không phát hiện nghi vấn
- Nếu có phát sinh về xử lý hàng hóa, sẽ báo ngay tại thời điểm phát sinh.
- công bố hợp quy hàng thuộc Bộ Công An: KHOẢNG 10 triệu (chưa làm bao giờ nên chưa nắm rõ chi phí)`;

console.log("PARSER — Owner quick-quote fixture");
const p = parseQuoteText(OWNER_SAMPLE);

assert.equal(p.incoterm, "FOB");
assert.equal(p.origin, "NINGBO");
assert.equal(p.destination, "Hải Phòng");
ok("INCOTERM=FOB · ORIGIN=NINGBO · DESTINATION=Hải Phòng");

assert.equal(p.lines.length, 9, `expected 9 service lines, got ${p.lines.length}`);
assert.deepEqual(p.lines.map((l) => l.name), [
  "Cước biển",
  "Phụ phí hãng tàu",
  "Nâng cont, hạ vỏ",
  "Hạ tầng",
  "Thủ tục hải quan",
  "Vận tải về Sơn Tây, Hà Nội",
  "Kiểm hóa mở cont",
  "Kiểm hóa soi chiếu",
  "Công bố hợp quy hàng thuộc Bộ Công An",
]);
ok("9 service lines extracted (the unpriced sentence is NOT one of them)");

const byName = (needle) => p.lines.find((l) => l.name.toLowerCase().includes(needle.toLowerCase()));

const sea = byName("Cước biển");
assert.equal(sea.sell, 950);
assert.equal(sea.currency, "USD");
assert.equal(sea.unit, "cont 20'");
assert.ok(sea.note.includes("cước tại thời điểm này"), `sea note lost time clause: ${sea.note}`);
assert.ok(/vượt 20 tấn/i.test(sea.note) && /80 USD/i.test(sea.note), `sea note lost surcharge: ${sea.note}`);
ok("1. Cước biển = 950 USD / cont 20' + both conditional notes");

const carrier = byName("Phụ phí hãng tàu");
assert.equal(carrier.sell, 9500000, "9.5 triệu must be 9,500,000");
assert.equal(carrier.currency, "VND");
assert.equal(carrier.unit, "cont 20'");
ok("2. Phụ phí hãng tàu = 9,500,000 VND / cont 20' (9.5 triệu)");

const lift = byName("Nâng cont");
assert.equal(lift.sell, 2600000);
assert.equal(lift.unit, "cont 20'");
ok("3. Nâng cont, hạ vỏ = 2,600,000 VND / cont 20'");

const infra = byName("Hạ tầng");
assert.equal(infra.sell, 250000, "250k must be 250,000");
assert.equal(infra.currency, "VND");
ok("4. Hạ tầng = 250,000 VND (250k)");

const customs = byName("Thủ tục hải quan");
assert.equal(customs.sell, 2000000);
assert.equal(customs.unit, "cont");
ok("5. Thủ tục hải quan = 2,000,000 VND / cont");

const trucking = byName("Vận tải về Sơn Tây");
assert.equal(trucking.sell, 6000000);
assert.equal(trucking.unit, "cont 20'");
assert.ok(/500000|500k/i.test(trucking.note), `trucking note lost Lạch Huyện surcharge: ${trucking.note}`);
assert.ok(/lach huyện|lạch huyện/i.test(trucking.note), `trucking note lost Lạch Huyện: ${trucking.note}`);
assert.ok(/xăng dầu/i.test(trucking.note), `trucking note lost fuel clause: ${trucking.note}`);
ok("6. Vận tải Sơn Tây = 6,000,000 VND + Lạch Huyện +500.000 + fuel clause");

const openCont = byName("Kiểm hóa mở cont");
assert.equal(openCont.sell, 4000000);
assert.equal(openCont.condition, "IF_APPLICABLE");
assert.ok(/nếu có|phát sinh/i.test(openCont.note), "conditional note missing");
ok("7. Kiểm hóa mở cont = 4,000,000 VND · IF_APPLICABLE · 'Có thể phát sinh (nếu có)'");

const xray = byName("Kiểm hóa soi chiếu");
assert.equal(xray.sell, 2000000);
assert.equal(xray.condition, "IF_APPLICABLE");
assert.ok(/nếu có|phát sinh/i.test(xray.note));
ok("8. Kiểm hóa soi chiếu = 2,000,000 VND · IF_APPLICABLE");

const conformity = byName("Công bố hợp quy");
assert.equal(conformity.sell, 10000000, "khoảng 10 triệu → 10,000,000 but flagged approximate");
assert.equal(conformity.status, "ESTIMATE_REQUIRES_CONFIRMATION");
assert.ok(/KHOẢNG 10 triệu/i.test(conformity.note), `lost the literal 'KHOẢNG 10 triệu': ${conformity.note}`);
assert.ok(/chưa làm bao giờ/i.test(conformity.note), `lost 'chưa làm bao giờ': ${conformity.note}`);
assert.ok(/chưa nắm rõ/i.test(conformity.note), `lost 'chưa nắm rõ chi phí': ${conformity.note}`);
ok("9. Công bố hợp quy ≈10,000,000 VND · ESTIMATE_REQUIRES_CONFIRMATION with original wording preserved");

// The unpriced sentence must be an ASSUMPTION, never a fake zero-price line.
const assumption = p.assumptions.find((a) => /Nếu có phát sinh về xử lý hàng hóa/i.test(a));
assert.ok(assumption, "the general 'phát sinh xử lý hàng hóa' sentence is not an assumption");
assert.ok(
  !p.lines.some((l) => /xử lý hàng hóa/i.test(l.name)),
  "the general sentence became a fake service line"
);
assert.ok(!p.lines.some((l) => l.sell === 0), "a line was fabricated with a 0 price (UNKNOWN != ZERO)");
ok("general unpriced sentence → quote assumption, NOT a 0-price service line");

// Nothing invented.
for (const l of p.lines) {
  assert.ok(!("vat" in l) && !("taxPct" in l), "parser invented a VAT field");
  assert.ok(!("cost" in l) && !("costUnit" in l), "parser invented a cost price");
  assert.ok(!("fx" in l), "parser invented FX");
}
assert.ok(!("customer" in p) && !("validity" in p) && !("fx" in p), "parser invented customer/validity/FX");
ok("no VAT / cost / FX / customer / validity invented anywhere");

// ---------------------------------------------------------------------------
console.log("PARSER — Check chi phí paste");
const c = parseQuoteText("EXW Guangdong - Hà Nội\n5 khối\n800 kg");
assert.equal(c.incoterm, "EXW");
assert.equal(c.origin, "Guangdong");
assert.equal(c.destination, "Hà Nội");
assert.equal(c.cbm, 5);
assert.equal(c.weightKg, 800);
ok("EXW Guangdong → Hà Nội · 5 CBM · 800 kg prefilled from one paste");

// ---------------------------------------------------------------------------
console.log("PARSER — shorthand amounts");
assert.equal(parseVnAmount("10 triệu"), 10000000);
assert.equal(parseVnAmount("10tr"), 10000000);
assert.equal(parseVnAmount("9.5 triệu"), 9500000);
assert.equal(parseVnAmount("250k"), 250000);
assert.equal(parseVnAmount("1.200.000"), 1200000);
assert.equal(parseVnAmount("950"), 950);
assert.equal(parseVnAmount("abc"), null);
ok("10 triệu / 10tr / 9.5 triệu / 250k / 1.200.000 / 950 shorthand");

const rmb = parseQuoteText("Cước nội địa TQ: 1200 rmb/cbm");
assert.equal(rmb.lines[0].currency, "CNY");
assert.equal(rmb.lines[0].unit, "cbm");
const usd = parseQuoteText("Local charge: $450/bill");
assert.equal(usd.lines[0].currency, "USD");
assert.equal(usd.lines[0].unit, "bill");
ok("RMB/CNY and $ explicit currencies, /cbm and /bill units");

// ---------------------------------------------------------------------------
console.log("CALCULATOR — required proofs");
const calc = (expr) => evaluateAmountExpression(expr);
assert.deepEqual([calc("370*8").ok, calc("370*8").value], [true, 2960]);
assert.equal(calc("=370*8").value, 2960);
assert.equal(calc("9.5tr*2").value, 19000000);
assert.equal(calc("250k*4").value, 1000000);
assert.equal(calc("=SUM(370,80)").value, 450);
assert.equal(calc("=SUM(370,80,50)").value, 500);
assert.equal(calc("(370+80)*2").value, 900);
assert.equal(calc("=ROUND(1234.56,0)").value, 1235);
assert.equal(calc("2500000").value, 2500000);
ok("370*8=2960 · 9.5tr*2=19.000.000 · 250k*4=1.000.000 · SUM(370,80)=450 · ROUND · parentheses");

const divZero = calc("100/0");
assert.equal(divZero.ok, false);
assert.ok(/chia được cho 0|chia cho 0/i.test(divZero.error), divZero.error);
ok("division by zero refused with a readable message");

for (const bad of [
  "eval(1)", "Function('x')", "require('fs')", "A1+B2", "=A1*2",
  "__proto__", "process.exit(1)", "import('x')", "=SUM(", "370**", "fetch('http://x')",
  "=CELL(A1)", "@SUM(1)", "=1+", "'; DROP TABLE",
]) {
  const r = calc(bad);
  assert.equal(r.ok, false, `arbitrary token accepted: ${bad}`);
  assert.equal(r.value, null);
  assert.ok(r.error.length > 0, `no validation message for: ${bad}`);
}
ok("eval/Function/require/import/fetch/cell refs/file refs/arbitrary identifiers all REFUSED");

// The typed text is preserved by the caller; the helper never throws.
assert.doesNotThrow(() => calc("((("));
assert.equal(calc("").ok, true);
assert.equal(calc("").value, null);
ok("malformed input never throws; blank stays blank (UNKNOWN != ZERO)");

console.log(`\nPASS — ${passed} checks`);
