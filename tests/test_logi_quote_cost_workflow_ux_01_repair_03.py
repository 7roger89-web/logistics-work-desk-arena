"""LOGI_QUOTE_COST_WORKFLOW_UX_01_REPAIR_03 — the projection must not lie about
which quote it read, or which currency it is showing.

REPAIR_02 made "no quote-time FX rate" a normal, savable state: a canonical
service line can legitimately carry ``sell_total = 950``, ``currency = "USD"``
and ``sell_vnd = None``. Two latent defects in
``views.logi_real_data._quote_lines()`` only became reachable because of that.

DEFECT A — a false currency label.
    The projection read ``sell_vnd if sell_vnd is not None else sell_total`` and
    then hard-coded ``ccy = "VND"``. With no FX it therefore published the
    ORIGINAL amount under a VND label: 950 USD rendered as "950 VND" on the
    Check chi phí screen — understated by roughly 24,000x. The label must always
    describe the amount actually being shown.

DEFECT B — the wrong quote entirely.
    ``build_shipment_draft`` stamps ``shipment.quote_id``, but the projection
    scanned the quote store by contract/customer, so a customer holding several
    quotes could have any of them projected onto the lot. The lot's own link is
    authoritative when present; legacy lots without one keep the old fallback.

Both are projection-only repairs. Nothing is converted here, no rate is
invented, and REPAIR_02's nullable arithmetic is untouched.

Transport: the isolated staging database (mongomock). Production is never
touched.
"""

from __future__ import annotations

import pytest

from views import logi_real_data as rd


CUSTOMER = "CUST-ANPHAT"


def _canonical_quote(qid: str, sell_unit: float, currency: str, *, sell_vnd=None,
                     name: str = "Cước biển", customer: str = CUSTOMER) -> dict:
    """A quote in the canonical LOG-C12 shape calculate_quote() produces."""
    return {
        "id": qid, "quote_no": qid, "customer_id": customer, "status": "ACCEPTED",
        "service_lines": [{
            "code": "DV-CUOC-BIEN", "service_name": name, "unit": "Cont 20'",
            "qty": 1, "currency": currency,
            "sell_unit": sell_unit, "sell_total": sell_unit, "sell_vnd": sell_vnd,
            "cost_unit": None, "cost_total": None, "cost_vnd": None,
            "tax_pct": None, "tax_total": None, "tax_vnd": None,
        }],
    }


def _shipment(**over) -> dict:
    base = {"shipment_id": "LO-TEST", "id": "LO-TEST", "customer_id": CUSTOMER,
            "currency": "VND", "data": {}}
    base.update(over)
    return base


# ---------------------------------------------------------------------------
# A — an unconverted amount is never labelled VND
# ---------------------------------------------------------------------------

def test_a_no_fx_projects_the_original_amount_with_its_own_currency():
    quotes = {"Q-USD": _canonical_quote("Q-USD", 950, "USD", sell_vnd=None)}
    lines = rd._quote_lines(_shipment(quote_id="Q-USD"), quotes)

    assert len(lines) == 1
    line = lines[0]
    assert line["amount"] == 950.0, "the original USD amount must survive"
    assert line["ccy"] == "USD", "950 USD must never be relabelled as 950 VND"
    assert line["kind"] == "quote"


def test_a2_a_vnd_line_without_conversion_is_still_vnd():
    """The VND case must not regress: its own currency IS VND."""
    quotes = {"Q-VND": _canonical_quote("Q-VND", 9_500_000, "VND", sell_vnd=9_500_000)}
    line = rd._quote_lines(_shipment(quote_id="Q-VND"), quotes)[0]
    assert line["amount"] == 9_500_000.0 and line["ccy"] == "VND"


def test_a3_a_mixed_quote_keeps_each_line_in_its_own_currency():
    quote = _canonical_quote("Q-MIX", 950, "USD", sell_vnd=None)
    quote["service_lines"].append({
        "code": "DV-THC", "service_name": "THC Hải Phòng", "unit": "Cont",
        "qty": 1, "currency": "VND", "sell_unit": 3_100_000,
        "sell_total": 3_100_000, "sell_vnd": 3_100_000,
        "cost_unit": None, "tax_pct": None,
    })
    lines = rd._quote_lines(_shipment(quote_id="Q-MIX"), {"Q-MIX": quote})
    assert [(l["amount"], l["ccy"]) for l in lines] == [(950.0, "USD"), (3_100_000.0, "VND")]


# ---------------------------------------------------------------------------
# B — a converted amount stays internally consistent
# ---------------------------------------------------------------------------

def test_b_with_fx_the_converted_amount_is_labelled_vnd():
    quotes = {"Q-FX": _canonical_quote("Q-FX", 950, "USD", sell_vnd=24_225_000)}
    line = rd._quote_lines(_shipment(quote_id="Q-FX"), quotes)[0]
    assert line["amount"] == 24_225_000.0
    assert line["ccy"] == "VND", "a converted figure is genuinely VND"


@pytest.mark.parametrize("sell_vnd,expected", [
    (None, (950.0, "USD")),          # unconverted → original currency
    (24_225_000, (24_225_000.0, "VND")),  # converted   → VND
])
def test_b2_amount_and_currency_are_always_the_same_fact(sell_vnd, expected):
    """Whatever the FX state, the pair (amount, ccy) must describe ONE reality."""
    quotes = {"Q": _canonical_quote("Q", 950, "USD", sell_vnd=sell_vnd)}
    line = rd._quote_lines(_shipment(quote_id="Q"), quotes)[0]
    assert (line["amount"], line["ccy"]) == expected


# ---------------------------------------------------------------------------
# C — the lot's own quote_id decides, not the customer
# ---------------------------------------------------------------------------

def test_c_two_quotes_same_customer_uses_the_linked_one_only():
    quotes = {
        "Q-A": _canonical_quote("Q-A", 800, "USD", sell_vnd=None),
        "Q-B": _canonical_quote("Q-B", 950, "USD", sell_vnd=None),
    }
    lines = rd._quote_lines(_shipment(quote_id="Q-B"), quotes)
    assert len(lines) == 1
    assert lines[0]["amount"] == 950.0, "the lot is linked to quote B, not A"
    assert lines[0]["ccy"] == "USD"

    # …and the link genuinely drives it: point the lot at A and A is projected.
    assert rd._quote_lines(_shipment(quote_id="Q-A"), quotes)[0]["amount"] == 800.0


def test_c2_a_dangling_quote_id_shows_nothing_rather_than_a_substitute():
    """A plausible wrong estimate is worse than a visible absence."""
    quotes = {"Q-OTHER": _canonical_quote("Q-OTHER", 800, "USD", sell_vnd=None)}
    assert rd._quote_lines(_shipment(quote_id="Q-GONE"), quotes) == []


def test_c3_quote_id_wins_even_when_a_contract_id_is_also_present():
    quotes = {
        "Q-A": _canonical_quote("Q-A", 800, "USD", sell_vnd=None),
        "Q-B": _canonical_quote("Q-B", 950, "USD", sell_vnd=None),
    }
    lines = rd._quote_lines(_shipment(quote_id="Q-B", contract_id="Q-A"), quotes)
    assert lines[0]["amount"] == 950.0, "the lot's quote link outranks contract matching"


# ---------------------------------------------------------------------------
# D — legacy shipments keep working
# ---------------------------------------------------------------------------

def test_d_legacy_shipment_without_quote_id_keeps_the_customer_fallback():
    quotes = {"Q-A": _canonical_quote("Q-A", 800, "USD", sell_vnd=None)}
    lines = rd._quote_lines(_shipment(), quotes)  # no quote_id at all
    assert len(lines) == 1 and lines[0]["amount"] == 800.0


def test_d2_legacy_quote_shape_with_its_own_lines_still_projects():
    """Pre-LOG-C12 quotes carry `lines` that already state their currency."""
    legacy = {"id": "Q-LEGACY", "customer_id": CUSTOMER,
              "lines": [{"name": "Cước biển", "amount": 500, "currency": "USD"}]}
    lines = rd._quote_lines(_shipment(), {"Q-LEGACY": legacy})
    assert lines == [{"label": "Cước biển", "amount": 500.0, "ccy": "USD", "kind": "quote"}]
    # …and it is equally reachable through an explicit link.
    linked = rd._quote_lines(_shipment(quote_id="Q-LEGACY"), {"Q-LEGACY": legacy})
    assert linked[0]["amount"] == 500.0 and linked[0]["ccy"] == "USD"


def test_d3_legacy_contract_id_match_is_preserved():
    """The legacy rule matches on contract_id OR customer_id — unchanged.

    Note this is exactly the imprecision REPAIR_03 fixes for modern lots: with
    no quote_id the first quote satisfying either condition wins. It is kept
    verbatim for historical shipments (no migration, no rewrite), and pinned
    here so a future change to the fallback is a deliberate one.
    """
    quotes = {
        "Q-A": _canonical_quote("Q-A", 800, "USD", sell_vnd=None, customer="OTHER-CUST"),
        "Q-B": _canonical_quote("Q-B", 950, "USD", sell_vnd=None, customer="NOT-THIS-ONE"),
    }
    # contract_id names Q-B while the lot's customer matches Q-A: the scan order
    # decides, as it always has.
    lines = rd._quote_lines(_shipment(contract_id="Q-B", customer_id="OTHER-CUST"), quotes)
    assert lines[0]["amount"] == 800.0

    # A contract_id whose quote is the ONLY candidate still resolves.
    only = rd._quote_lines(_shipment(contract_id="Q-B", customer_id="NOBODY"),
                           {"Q-B": quotes["Q-B"]})
    assert only[0]["amount"] == 950.0


# ---------------------------------------------------------------------------
# E — the whole read path Check chi phí actually consumes
# ---------------------------------------------------------------------------

def test_e_finance_projection_feeds_cost_check_the_linked_quote_in_usd():
    """canonical quote → shipment.quote_id → finance_projection → finance.quote.

    This is the exact object ``component/src/lib/costHistory.ts::quoteLines()``
    reads, so proving it here proves what Check chi phí renders: 950 USD from
    quote B — not 800 from quote A, and not "950 VND".
    """
    quotes = {
        "Q-A": _canonical_quote("Q-A", 800, "USD", sell_vnd=None),
        "Q-B": _canonical_quote("Q-B", 950, "USD", sell_vnd=None),
    }
    shipment = _shipment(shipment_id="LO-0999", id="LO-0999", quote_id="Q-B")

    finance = rd.finance_projection(shipment, quotes)
    quote_lines = finance["quote"]

    assert len(quote_lines) == 1
    assert quote_lines[0]["label"] == "Cước biển"
    assert quote_lines[0]["amount"] == 950.0
    assert quote_lines[0]["ccy"] == "USD"
    assert quote_lines[0]["kind"] == "quote"

    # The estimate never leaks into Finance Actual, which stays empty here.
    assert finance["actual"] == []
    assert finance["hasActualLines"] is False


def test_e2_cost_check_line_shape_carries_qty_and_vat_without_inventing_them():
    """costHistory.ts reads l.qty / l.vat / l.amount / l.ccy — all must be honest."""
    quotes = {"Q-B": _canonical_quote("Q-B", 950, "USD", sell_vnd=None)}
    line = rd.finance_projection(_shipment(quote_id="Q-B"), quotes)["quote"][0]
    assert line["qty"] == 1.0
    assert line["vat"] is None, "an unknown VAT must stay UNKNOWN in the projection"
    assert line["amount"] == 950.0 and line["ccy"] == "USD"
