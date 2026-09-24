"""LOGI_COST_RATE_VIETNAMESE_PARSER_01 — Owner real-world Vietnamese rate contract.

Owner-verified production finding after PR106/PR107: the deterministic
Kho giá vốn parser returned "Chưa bóc được dòng giá nào. Giữ nguyên nội dung
và nhập/sửa thủ công thay vì đoán số." for normal Vietnamese logistics
typing such as ``950 usd/ cont 20'``, ``9.5 triệu/cont 20'``, ``250k/cont``,
``6 tr/cont`` and ``KHOẢNG 10 triệu``.

These tests pin the required semantics. They FAIL on the pre-repair parser
(root-cause proof) and must PASS after the bounded regex/token repair in
``core/cost_intelligence.py``. Pure deterministic parser tests — no DB, no
UI, no LLM.
"""
from __future__ import annotations

from datetime import date

from core.cost_intelligence import parse_cost_rate_text

RECEIVED = date(2026, 9, 24)

# Exact Owner fixture (production, verified). Must never be mutated: it is
# the parser contract for Vietnamese real-world rate text.
OWNER_FIXTURE = """\
FOB NINGBO - Hải Phòng:
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
- công bố hợp quy hàng thuộc Bộ Công An: KHOẢNG 10 triệu (chưa làm bao giờ nên chưa nắm rõ chi phí)
"""


def _catalog():
    return {
        "P-HPH": {
            "id": "P-HPH", "kind": "PLACE", "code": "VNHPH", "name": "Hải Phòng",
            "aliases": ["HPH", "HAIPHONG"], "zone_ids": ["ZONE-HPH"], "active": True,
        },
        "P-NGB": {
            "id": "P-NGB", "kind": "PLACE", "code": "CNNGB", "name": "Ningbo",
            "aliases": ["NINGBO"], "zone_ids": ["ZONE-NGB"], "active": True,
        },
    }


def _row(rows, amount, currency):
    return next(r for r in rows if r.get("amount") == amount and r.get("currency") == currency)


def test_a_amount_before_currency_with_space_slash():
    """A. 'Cước biển: 950 usd/ cont 20'' => 950 USD / 20GP."""
    rows = parse_cost_rate_text(
        "Cước biển: 950 usd/ cont 20'", catalog=_catalog(), received_on=RECEIVED,
    )["rows"]
    assert len(rows) == 1
    row = rows[0]
    assert row["amount"] == 950.0
    assert row["currency"] == "USD"
    assert row["equipment"] == "20GP"
    assert row["unit"] == "CONT"
    assert row["chargeLabel"] == "Cước biển"


def test_b_trieu_million_vnd_with_cont20():
    """B. 'Phụ phí hãng tàu: 9.5 triệu/cont 20'' => 9,500,000 VND / 20GP."""
    rows = parse_cost_rate_text(
        "Phụ phí hãng tàu: 9.5 triệu/cont 20'", catalog=_catalog(), received_on=RECEIVED,
    )["rows"]
    assert len(rows) == 1
    row = rows[0]
    assert row["amount"] == 9_500_000.0
    assert row["currency"] == "VND"
    assert row["equipment"] == "20GP"
    assert row["chargeLabel"] == "Phụ phí hãng tàu"


def test_c_k_thousand_vnd_with_cont20():
    """C. 'Hạ tầng: 250k/cont 20'' => 250,000 VND / 20GP."""
    rows = parse_cost_rate_text(
        "Hạ tầng: 250k/cont 20'", catalog=_catalog(), received_on=RECEIVED,
    )["rows"]
    assert len(rows) == 1
    row = rows[0]
    assert row["amount"] == 250_000.0
    assert row["currency"] == "VND"
    assert row["equipment"] == "20GP"


def test_d_trieu_bare_cont_unit_no_equipment():
    """D. 'thủ tục hải quan: 2 triệu/cont' => 2,000,000 VND / CONT (no equipment invented)."""
    rows = parse_cost_rate_text(
        "thủ tục hải quan: 2 triệu/cont", catalog=_catalog(), received_on=RECEIVED,
    )["rows"]
    assert len(rows) == 1
    row = rows[0]
    assert row["amount"] == 2_000_000.0
    assert row["currency"] == "VND"
    assert row["unit"] == "CONT"
    assert row["equipment"] == ""


def test_e_transport_primary_6m_conditional_500k_not_promoted():
    """E. primary 6,000,000 VND; the +500k condition is NOT a second main rate."""
    line = (
        "vận tải về Sơn Tây, Hà Nội: 6 tr/cont 20' "
        "(hàng về cảng lach huyện + 500k/cont) - theo giá cước xăng dầu tại thời điểm này"
    )
    parsed = parse_cost_rate_text(line, catalog=_catalog(), received_on=RECEIVED)
    rows = parsed["rows"]
    primary = _row(rows, 6_000_000.0, "VND")
    assert primary["equipment"] == "20GP"
    assert primary["confidence"] == "NEEDS_REVIEW"
    assert primary["rawLine"] == line, "full rawLine must be preserved"
    # The conditional surcharge is exposed, never silently promoted/summed.
    assert any("500k" in item for item in primary.get("conditionalAmounts", []))
    assert not any(r.get("amount") == 500_000.0 for r in rows), "conditional 500k must not become a main rate row"
    assert not any(r.get("amount") == 6_500_000.0 for r in rows), "no silent sum"


def test_f_ocean_primary_950_conditional_80_not_promoted():
    """F. primary 950 USD / 20GP; +80 usd/cont is NOT summed nor promoted."""
    line = "Cước biển: 950 usd/cont 20' - cước tại thời điểm này (nếu vượt 20 tấn + 80 usd/cont)"
    parsed = parse_cost_rate_text(line, catalog=_catalog(), received_on=RECEIVED)
    rows = parsed["rows"]
    primary = _row(rows, 950.0, "USD")
    assert primary["equipment"] == "20GP"
    assert primary["confidence"] == "NEEDS_REVIEW"
    assert any("80" in item for item in primary.get("conditionalAmounts", []))
    assert not any(r.get("amount") == 80.0 for r in rows), "conditional +80 must not become a main rate row"
    assert not any(r.get("amount") == 1030.0 for r in rows), "no silent 950+80 sum"


def test_g_approximate_khoang_requires_review_and_no_invented_unit():
    """G. 'KHOẢNG 10 triệu' => 10,000,000 VND, approximate, NEEDS_REVIEW, unit NOT invented."""
    line = "công bố hợp quy hàng thuộc Bộ Công An: KHOẢNG 10 triệu (chưa làm bao giờ nên chưa nắm rõ chi phí)"
    parsed = parse_cost_rate_text(line, catalog=_catalog(), received_on=RECEIVED)
    rows = parsed["rows"]
    assert len(rows) == 1
    row = rows[0]
    assert row["amount"] == 10_000_000.0
    assert row["currency"] == "VND"
    assert row["unit"] == "", "must not invent CONT/SET"
    assert row["equipment"] == ""
    assert row["confidence"] == "NEEDS_REVIEW"
    assert row.get("approximate") is True
    assert "công bố hợp quy" in row["chargeLabel"], "user wording preserved"
    assert row["chargeLabel"] != "KHOẢNG"
    assert row["rawLine"] == line


def test_h_non_price_sentence_never_becomes_zero_price_row():
    """H. UNKNOWN != ZERO: a non-price sentence never becomes a zero-price row."""
    sentence = "Nếu có phát sinh về xử lý hàng hóa, sẽ báo ngay tại thời điểm phát sinh."
    try:
        parse_cost_rate_text(sentence, catalog=_catalog(), received_on=RECEIVED)
    except ValueError as exc:
        assert "Chưa bóc được dòng giá nào" in str(exc)
    else:
        raise AssertionError("non-price sentence must not parse into any row")


def test_i_full_owner_fixture_produces_meaningful_rows():
    """I. Full Owner fixture => 9 meaningful rows, not 'Chưa bóc được dòng giá nào'."""
    parsed = parse_cost_rate_text(OWNER_FIXTURE, catalog=_catalog(), received_on=RECEIVED)
    rows = parsed["rows"]
    assert len(rows) == 9, f"expected 9 price rows, got {len(rows)}: {[r.get('rawLine') for r in rows]}"

    expected = [
        ("Cước biển", 950.0, "USD", "20GP"),
        ("Phụ phí hãng tàu", 9_500_000.0, "VND", "20GP"),
        ("nâng cont, hạ vỏ", 2_600_000.0, "VND", "20GP"),
        ("Hạ tầng", 250_000.0, "VND", "20GP"),
        ("thủ tục hải quan", 2_000_000.0, "VND", ""),
        ("vận tải về Sơn Tây, Hà Nội", 6_000_000.0, "VND", "20GP"),
        ("kiểm hóa mở cont", 4_000_000.0, "VND", ""),
        ("Kiểm hóa soi chiếu", 2_000_000.0, "VND", ""),
        ("công bố hợp quy hàng thuộc Bộ Công An", 10_000_000.0, "VND", ""),
    ]
    for label_fragment, amount, currency, equipment in expected:
        candidates = [
            r for r in rows
            if r.get("amount") == amount and r.get("currency") == currency and label_fragment in r.get("chargeLabel", "")
        ]
        assert candidates, f"no row for {label_fragment!r} {amount} {currency}"
        row = candidates[0]
        assert row["equipment"] == equipment
        assert row["amount"] != 0, "no zero-price row"

    # The non-price sentence must not become a row.
    assert not any("phát sinh về xử lý hàng hóa" in (r.get("rawLine") or "") for r in rows)

    # Route still recognised from the first line.
    ocean = _row(rows, 950.0, "USD")
    assert ocean["destination"]["name"] == "Hải Phòng"
    assert ocean["origin"]["name"] == "Ningbo"

    # Conditional surcharges and the approximate 10m are visible review rows.
    assert parsed["summary"]["needsReview"] >= 3
    assert any(w for w in parsed["warnings"] if "điều kiện" in w), "warning about conditional surcharges"
    assert parsed["rawText"] == OWNER_FIXTURE.strip(), "raw text preserved"


def test_legacy_forms_still_parse_unchanged():
    """J (guard). Existing supported forms keep working (no regression)."""
    parsed = parse_cost_rate_text(
        "MCC USD 675/20GP\nO/F:USD1425/40HQ ETD:21/09/2026 COSCO\nUSD1200/40HQ ETD:27/09 MSK\n"
        "THC $130/20GP $205/40HQ\nREFUND 21$/RT\nBUY EXPORT:100$/SET + TAX\n"
        "COSCO USD 1300/40HQ 有效期到9.30\nSNL 没仓位\n电放费 RMB500/SET",
        catalog=_catalog(),
        received_on=RECEIVED,
    )
    rows = parsed["rows"]
    mcc = _row(rows, 675.0, "USD")
    assert mcc["carrier"]["name"] == "MCC"
    assert mcc["equipment"] == "20GP"

    assert _row(rows, 1425.0, "USD")["chargeLabel"] == "O/F"
    assert _row(rows, 1200.0, "USD")["carrier"]["name"] == "MSK"
    assert {r["amount"] for r in rows if r.get("chargeLabel") == "THC"} == {130.0, 205.0}
    assert _row(rows, 21.0, "USD")["kind"] == "CREDIT"
    buy = _row(rows, 100.0, "USD")
    assert buy["taxQualifier"] == "PLUS_TAX"
    assert _row(rows, 1300.0, "USD")["validUntil"] == "2026-09-30"
    assert any(r["status"] == "NO_SPACE" and r["carrier"]["name"] == "SNL" for r in rows)
    rmb = _row(rows, 500.0, "CNY")
    assert rmb["unit"] == "SET"
    # "9.30" in the validity tail must not become a price row.
    assert not any(r.get("amount") in (9.3, 9.30) for r in rows)
