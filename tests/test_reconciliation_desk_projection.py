"""LOGI_RECONCILIATION_DESK_01 — focused tests for the READ-ONLY đối soát desk.

Two layers, deliberately:

1. ``reconciliation_projection`` / ``apply_filters`` are pure, so the
   reconciliation semantics (matched / partial / unmatched / unallocated,
   currency separation, UNKNOWN != ZERO, real shipment + transaction linkage)
   are proven deterministically with no database at all.
2. ``reconciliation_view`` + view-model exposure run against the isolated
   staging database (mongomock) with obligations and payments recorded through
   the SAME canonical C2B/C2D handlers the payables worklist uses, so the desk
   is proven to read real canonical truth rather than a hand-made shape.

Production database is never touched. No write path is exercised here: the desk
has none, and one test asserts that stays true.
"""

from __future__ import annotations

import pytest

from views import reconciliation_desk as desk


TT = {"party_type": "company", "party_id": "TT-COMPANY", "name": "Trường Thành"}
PARTNER = {"party_type": "agent", "party_id": "AGT-PHUANH", "name": "CÔNG TY TNHH PHÚ ANH LOGISTICS"}
OTHER = {"party_type": "agent", "party_id": "AGT-OTHER", "name": "Đối tác khác"}

SHIPMENT = "LO-0308"


# ---------------------------------------------------------------------------
# Fixtures — canonical shapes only (what shipment_partner_position returns)
# ---------------------------------------------------------------------------

def _obligation_row(
    obligation_id: str,
    *,
    amount: float,
    currency: str = "VND",
    allocated: float = 0.0,
    to_party: dict = PARTNER,
    allocation_ids: list[str] | None = None,
    purpose: str = "partner_cost_payable",
    status: str = "CONFIRMED",
    overallocated: bool = False,
    incompatible: list[str] | None = None,
    shipment_ids: list[str] | None = None,
) -> dict:
    allocation_ids = allocation_ids or []
    outstanding = amount - allocated
    return {
        "obligation_id": obligation_id,
        "purpose": purpose,
        "created_at": "2026-09-01",
        "shipment_ids": shipment_ids or [SHIPMENT],
        "from_party": dict(TT),
        "to_party": dict(to_party),
        "evidence_refs": [],
        "source_record_ids": [obligation_id, *allocation_ids],
        "amount": amount,
        "currency": currency,
        "allocated": allocated,
        "outstanding": outstanding,
        "allocation_ids": allocation_ids,
        "status": status,
        "incompatible_allocation_ids": incompatible or [],
        "overallocated": overallocated,
        "_partner_key": f"{to_party['party_type']}:{to_party['party_id']}",
    }


def _payment_row(
    transaction_id: str,
    *,
    amount: float,
    currency: str = "VND",
    allocated: float = 0.0,
    allocation_ids: list[str] | None = None,
    holder: dict = PARTNER,
    kind: str = "partner_payment",
    occurred_at: str = "2026-09-10",
    status: str = "CONFIRMED",
) -> dict:
    allocation_ids = allocation_ids or []
    return {
        "transaction_id": transaction_id,
        "request_id": f"REQ-{transaction_id}",
        "transaction_kind": kind,
        "occurred_at": occurred_at,
        "note": None,
        "source_party": dict(TT),
        "holder_party": dict(holder),
        "holder_party_key": f"{holder['party_type']}:{holder['party_id']}",
        "source_record_ids": [transaction_id, *allocation_ids],
        "amount": amount,
        "currency": currency,
        "allocated": allocated,
        "unallocated": amount - allocated,
        "allocation_ids": allocation_ids,
        "status": status,
        "incompatible_allocation_ids": [],
        "overallocated": False,
    }


def _position(
    shipment_id: str = SHIPMENT,
    *,
    obligations: list[dict] | None = None,
    payments: list[dict] | None = None,
    partner: dict = PARTNER,
) -> dict:
    """One ``shipment_partner_position``-shaped result (top-level lists only)."""
    obligations = obligations or []
    payments = payments or []
    key = f"{partner['party_type']}:{partner['party_id']}"
    return {
        "shipment_id": shipment_id,
        "partners": [
            {
                "partner": dict(partner),
                "partner_key": key,
                "status": "CONFIRMED",
                "totals_by_currency": {},
                "obligations": obligations,
                "payments": payments,
            }
        ],
        "obligations": obligations,
        "payments": payments,
        "status": "CONFIRMED",
        "derived": True,
        "read_only": True,
    }


def _row(projection: dict, row_id: str) -> dict:
    return next(r for r in projection["rows"] if r["id"] == row_id)


# ---------------------------------------------------------------------------
# A — match semantics come from the canonical derived figures, nothing invented
# ---------------------------------------------------------------------------

def test_fully_allocated_obligation_is_matched():
    projection = desk.reconciliation_projection(
        [_position(obligations=[_obligation_row("OBL-1", amount=57_000_000.0, allocated=57_000_000.0,
                                               allocation_ids=["ALLOC-1"])])]
    )
    row = _row(projection, f"{SHIPMENT}|OB|OBL-1")
    assert row["matchState"] == desk.MATCHED
    assert row["matchLabel"] == "Đã đối soát đủ"
    assert row["amount"] == 57_000_000.0
    assert row["allocated"] == 57_000_000.0
    assert row["remaining"] == 0.0
    assert row["reviewReason"] is None


def test_partially_allocated_obligation_is_partial():
    projection = desk.reconciliation_projection(
        [_position(obligations=[_obligation_row("OBL-2", amount=57_000_000.0, allocated=20_000_000.0,
                                               allocation_ids=["ALLOC-2"])])]
    )
    row = _row(projection, f"{SHIPMENT}|OB|OBL-2")
    assert row["matchState"] == desk.PARTIAL
    assert row["remaining"] == 37_000_000.0
    assert row["status"] == "CONFIRMED"


def test_obligation_without_allocation_is_unmatched_not_settled():
    """An obligation nobody paid is UNMATCHED — never rendered as settled."""
    projection = desk.reconciliation_projection([_position(obligations=[_obligation_row("OBL-3", amount=10_000_000.0)])])
    row = _row(projection, f"{SHIPMENT}|OB|OBL-3")
    assert row["matchState"] == desk.UNMATCHED
    assert row["matchLabel"] == "Chưa đối soát"
    assert row["allocated"] == 0.0
    assert row["remaining"] == 10_000_000.0
    assert row["transactionIds"] == []


def test_money_without_allocation_is_unallocated():
    projection = desk.reconciliation_projection(
        [_position(payments=[_payment_row("TX-1", amount=25_000_000.0)])]
    )
    row = _row(projection, f"{SHIPMENT}|TX|TX-1")
    assert row["side"] == "money"
    assert row["matchState"] == desk.UNALLOCATED
    assert row["matchLabel"] == "Chưa phân bổ"
    assert row["remaining"] == 25_000_000.0
    assert row["obligationIds"] == []


def test_partially_allocated_money_is_partial():
    projection = desk.reconciliation_projection(
        [_position(
            obligations=[_obligation_row("OBL-4", amount=20_000_000.0, allocated=20_000_000.0,
                                         allocation_ids=["ALLOC-4"])],
            payments=[_payment_row("TX-2", amount=50_000_000.0, allocated=20_000_000.0,
                                   allocation_ids=["ALLOC-4"])],
        )]
    )
    row = _row(projection, f"{SHIPMENT}|TX|TX-2")
    assert row["matchState"] == desk.PARTIAL
    assert row["remaining"] == 30_000_000.0
    # The real obligation↔transaction link, recovered from the allocation.
    assert row["obligationIds"] == ["OBL-4"]
    assert _row(projection, f"{SHIPMENT}|OB|OBL-4")["transactionIds"] == ["TX-2"]


# ---------------------------------------------------------------------------
# B — UNKNOWN != ZERO
# ---------------------------------------------------------------------------

def test_missing_derived_figure_stays_none_and_match_state_is_unknown():
    """A row the ledger could not derive is not silently treated as settled 0."""
    obligation = _obligation_row("OBL-5", amount=1_000_000.0)
    obligation["allocated"] = None
    obligation["outstanding"] = None
    projection = desk.reconciliation_projection([_position(obligations=[obligation])])
    row = _row(projection, f"{SHIPMENT}|OB|OBL-5")
    assert row["allocated"] is None
    assert row["remaining"] is None
    assert row["matchState"] is None
    assert row["matchLabel"] is None


def test_absent_shipment_contributes_no_row_rather_than_a_zero():
    """A shipment with no canonical record yields nothing, not a 0 payable."""
    projection = desk.reconciliation_projection([_position("LO-EMPTY")])
    assert projection["rows"] == []
    assert projection["totals"] == {}


def test_missing_currency_is_grouped_as_unknown_never_merged_into_a_real_currency():
    projection = desk.reconciliation_projection(
        [_position(obligations=[
            _obligation_row("OBL-VND", amount=10_000_000.0, currency="VND"),
            _obligation_row("OBL-NOCUR", amount=7.0, currency=""),
        ])]
    )
    assert set(projection["totals"]) == {"VND", desk.UNKNOWN_CURRENCY}
    assert projection["totals"]["VND"]["obligations"]["amount"] == 10_000_000.0
    assert projection["totals"][desk.UNKNOWN_CURRENCY]["obligations"]["amount"] == 7.0
    # UNKNOWN sorts last so it never leads the currency list.
    assert desk._currencies(projection) == ["VND", desk.UNKNOWN_CURRENCY]


# ---------------------------------------------------------------------------
# C — currencies stay separate (no FX, no fake grand total)
# ---------------------------------------------------------------------------

def test_multi_currency_totals_are_separate_and_never_summed():
    projection = desk.reconciliation_projection(
        [_position(obligations=[
            _obligation_row("OBL-VND", amount=10_000_000.0, currency="VND"),
            _obligation_row("OBL-CNY", amount=3_000.0, currency="CNY"),
            _obligation_row("OBL-USD", amount=500.0, currency="USD"),
        ])]
    )
    totals = projection["totals"]
    assert list(totals) == ["CNY", "USD", "VND"]
    assert totals["VND"]["obligations"]["amount"] == 10_000_000.0
    assert totals["CNY"]["obligations"]["amount"] == 3_000.0
    assert totals["USD"]["obligations"]["amount"] == 500.0
    # No cross-currency aggregate anywhere in the payload.
    assert "grandTotal" not in projection
    assert "total" not in projection
    for currency, bucket in totals.items():
        assert bucket["currency"] == currency
        assert bucket["obligations"]["count"] == 1


# ---------------------------------------------------------------------------
# D — review state is the canonical one, surfaced not hidden
# ---------------------------------------------------------------------------

def test_currency_incompatible_allocation_is_review_required_with_a_reason():
    projection = desk.reconciliation_projection(
        [_position(obligations=[
            _obligation_row("OBL-6", amount=100.0, currency="VND", allocated=0.0,
                            status="REVIEW_REQUIRED", incompatible=["ALLOC-BAD"]),
        ])]
    )
    row = _row(projection, f"{SHIPMENT}|OB|OBL-6")
    assert row["status"] == "REVIEW_REQUIRED"
    assert row["reviewReason"] == "Phân bổ lệch tiền tệ với chứng từ gốc"
    # The unconfirmed amount is totalled AND reported separately as review.
    bucket = projection["totals"]["VND"]
    assert bucket["review"]["count"] == 1
    assert bucket["review"]["amount"] == 100.0


def test_overallocated_history_is_review_not_silently_settled():
    projection = desk.reconciliation_projection(
        [_position(obligations=[
            _obligation_row("OBL-7", amount=100.0, allocated=150.0,
                            status="REVIEW_REQUIRED", overallocated=True,
                            allocation_ids=["ALLOC-OVER"]),
        ])]
    )
    row = _row(projection, f"{SHIPMENT}|OB|OBL-7")
    assert row["reviewReason"] == "Phân bổ vượt số phải trả/phải thu"
    assert row["remaining"] == -50.0
    assert row["matchState"] == desk.MATCHED


# ---------------------------------------------------------------------------
# E — shipment linkage is real
# ---------------------------------------------------------------------------

def test_shipment_link_is_real_and_canopen_follows_the_known_shipments():
    projection = desk.reconciliation_projection(
        [_position("LO-0308", obligations=[_obligation_row("OBL-8", amount=1.0, shipment_ids=["LO-0308"])])],
        known_shipment_ids=["LO-0308"],
    )
    row = _row(projection, "LO-0308|OB|OBL-8")
    assert row["shipmentId"] == "LO-0308"
    assert row["openHref"] == "/lo-hang/LO-0308"
    assert row["canOpen"] is True

    unknown = desk.reconciliation_projection(
        [_position("LO-GONE", obligations=[_obligation_row("OBL-9", amount=1.0, shipment_ids=["LO-GONE"])])],
        known_shipment_ids=["LO-0308"],
    )
    gone = _row(unknown, "LO-GONE|OB|OBL-9")
    assert gone["canOpen"] is False


def test_two_partners_on_one_shipment_stay_two_rows():
    projection = desk.reconciliation_projection(
        [_position(obligations=[
            _obligation_row("OBL-A", amount=1.0, to_party=PARTNER),
            _obligation_row("OBL-B", amount=2.0, to_party=OTHER),
        ])]
    )
    by_id = {r["id"]: r for r in projection["rows"]}
    assert by_id[f"{SHIPMENT}|OB|OBL-A"]["partnerName"] == PARTNER["name"]
    assert by_id[f"{SHIPMENT}|OB|OBL-B"]["partnerName"] == OTHER["name"]
    assert len(projection["rows"]) == 2


# ---------------------------------------------------------------------------
# F — filters use only backend-supplied fields and never move the totals
# ---------------------------------------------------------------------------

def _three_row_projection() -> dict:
    return desk.reconciliation_projection(
        [
            _position(obligations=[
                _obligation_row("OBL-1", amount=10_000_000.0, currency="VND", allocated=10_000_000.0,
                                allocation_ids=["ALLOC-1"]),
                _obligation_row("OBL-2", amount=5_000_000.0, currency="VND"),
            ]),
            _position("LO-0400", obligations=[
                _obligation_row("OBL-3", amount=3_000.0, currency="CNY", allocated=1_000.0,
                                allocation_ids=["ALLOC-3"], shipment_ids=["LO-0400"]),
            ], payments=[_payment_row("TX-9", amount=900.0, currency="CNY")]),
        ]
    )


def test_filter_by_query_matches_shipment_obligation_and_partner():
    projection = _three_row_projection()
    assert desk.apply_filters(projection, query="LO-0400")["visibleCount"] == 2
    assert desk.apply_filters(projection, query="OBL-1")["visibleCount"] == 1
    # Both sides carry the partner identity (payable's to_party, money's holder),
    # so a partner search reaches all four rows across both sides.
    assert desk.apply_filters(projection, query="AGT-PHUANH")["visibleCount"] == 4
    assert desk.apply_filters(projection, query="nothing-matches")["visibleCount"] == 0


def test_filter_by_currency_state_and_side():
    projection = _three_row_projection()
    assert desk.apply_filters(projection, currency="VND")["visibleCount"] == 2
    assert desk.apply_filters(projection, currency="CNY")["visibleCount"] == 2
    assert desk.apply_filters(projection, state=desk.MATCHED)["visibleCount"] == 1
    assert desk.apply_filters(projection, state=desk.PARTIAL)["visibleCount"] == 1
    assert desk.apply_filters(projection, state=desk.UNMATCHED)["visibleCount"] == 1
    assert desk.apply_filters(projection, state=desk.UNALLOCATED)["visibleCount"] == 1
    assert desk.apply_filters(projection, side=desk.OBLIGATION)["visibleCount"] == 3
    assert desk.apply_filters(projection, side=desk.MONEY)["visibleCount"] == 1
    assert desk.apply_filters(projection, state=desk.REVIEW)["visibleCount"] == 0


def test_filters_never_recompute_the_currency_totals():
    """A total that followed the search box would read as the real position."""
    projection = _three_row_projection()
    everything = desk.apply_filters(projection)
    filtered = desk.apply_filters(projection, query="LO-0400")
    assert filtered["visibleCount"] == 2
    assert filtered["totalCount"] == everything["totalCount"] == 4
    # apply_filters carries no totals of its own: the caller publishes the
    # unfiltered per-currency totals alongside the visible rows.
    assert "totals" not in filtered


# ---------------------------------------------------------------------------
# G — the desk has no writer
# ---------------------------------------------------------------------------

def test_module_exposes_no_write_capability():
    writers = [name for name in dir(desk) if name.startswith(("_handle", "save_", "allocate_", "reverse_"))]
    assert writers == []
    assert desk.reconciliation_view(selection=None, db=object.__new__(object) if False else None)["readOnly"] is True


# ---------------------------------------------------------------------------
# H — staging integration: real canonical records, real readback, empty honesty
# ---------------------------------------------------------------------------

@pytest.fixture()
def staging():
    """Clean isolated staging database + deterministic staging actor."""
    import streamlit as st

    from views import logi_sandbox

    logi_sandbox.reset_backend()
    transport = logi_sandbox.ensure_backend()
    assert transport == logi_sandbox.SANDBOX_TRANSPORT
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)
    yield transport
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)
    logi_sandbox.reset_backend()


@pytest.fixture()
def event_seq():
    state = {"n": 0}

    def _make(name: str, payload: dict) -> dict:
        state["n"] += 1
        return {name: {"seq": state["n"], "event": name, "payload": payload}}

    return _make


def _dispatch(seq_fn, name, payload):
    from views import logi_view_model as vm

    outcomes = vm.consume_phase_b_triggers({"seq": 0}, seq_fn(name, payload))
    assert len(outcomes) == 1
    return outcomes[0]


def _record_payable(seq_fn, request_id, amount, currency="VND", partner="AGT-PHUANH", shipment=SHIPMENT):
    return _dispatch(seq_fn, "partner_payable_record", {
        "shipmentId": shipment, "partnerId": partner, "requestId": request_id,
        "amount": amount, "currency": currency, "note": "Phải trả đối tác theo thực tế lô",
    })


def _record_payment(seq_fn, request_id, amount, currency="VND", partner="AGT-PHUANH", shipment=SHIPMENT):
    return _dispatch(seq_fn, "partner_payment_record", {
        "shipmentId": shipment, "partnerId": partner, "requestId": request_id,
        "amount": amount, "currency": currency, "date": "2026-09-10",
        "note": "Chuyển khoản thanh toán đối tác",
    })


def test_view_is_honest_empty_with_no_canonical_record(staging):
    """No obligation, no payment → EMPTY with zero rows, never a balanced 0 book."""
    view = desk.reconciliation_view()
    assert view["status"] == desk.EMPTY
    assert view["rows"] == []
    assert view["totals"] == {}
    assert view["currencies"] == []
    assert view["readOnly"] is True
    assert view["error"] is None


def test_view_reads_canonical_matched_partial_and_unmatched_state(staging, event_seq):
    """One shipment: a fully paid obligation, a part-paid one, an unpaid one."""
    assert _record_payable(event_seq, "REC-OBL-FULL", 10_000_000.0)["ok"]
    assert _record_payment(event_seq, "REC-PAY-FULL", 10_000_000.0)["ok"]
    assert _record_payable(event_seq, "REC-OBL-PART", 50_000_000.0)["ok"]
    assert _record_payment(event_seq, "REC-PAY-PART", 20_000_000.0)["ok"]
    assert _record_payable(event_seq, "REC-OBL-NONE", 7_000_000.0)["ok"]

    view = desk.reconciliation_view()
    assert view["status"] in {desk.OK, desk.REVIEW_REQUIRED}
    obligations = [r for r in view["rows"] if r["side"] == "obligation"]
    states = {r["matchState"] for r in obligations}
    assert desk.MATCHED in states
    assert desk.PARTIAL in states
    assert desk.UNMATCHED in states

    matched = next(r for r in obligations if r["matchState"] == desk.MATCHED)
    assert matched["remaining"] == 0.0
    assert matched["transactionIds"], "a matched obligation must name the transaction that settled it"
    assert matched["openHref"] == f"/lo-hang/{SHIPMENT}"

    partial = next(r for r in obligations if r["matchState"] == desk.PARTIAL)
    assert partial["remaining"] == 30_000_000.0

    # Totals are the canonical ones for VND only, and agree with the ledger read.
    from core.financial_ledger import shipment_partner_position

    totals = shipment_partner_position(SHIPMENT)["partners"][0]["totals_by_currency"]["VND"]
    assert view["totals"]["VND"]["obligations"]["amount"] == totals["payable"]
    assert view["totals"]["VND"]["obligations"]["allocated"] == totals["paid"]
    assert view["totals"]["VND"]["obligations"]["remaining"] == totals["remaining"]


def test_view_separates_currencies_from_canonical_records(staging, event_seq):
    assert _record_payable(event_seq, "REC-VND", 10_000_000.0, currency="VND")["ok"]
    assert _record_payable(event_seq, "REC-USD", 1_500.0, currency="USD")["ok"]

    view = desk.reconciliation_view()
    assert set(view["totals"]) == {"USD", "VND"}
    assert view["currencies"] == ["USD", "VND"]
    assert view["totals"]["VND"]["obligations"]["amount"] == 10_000_000.0
    assert view["totals"]["USD"]["obligations"]["amount"] == 1_500.0


def test_view_model_exposes_the_reconciliation_slice(staging, event_seq):
    from views import logi_view_model as vm

    assert _record_payable(event_seq, "REC-VM", 12_000_000.0)["ok"]
    model = vm.build_view_model()
    assert "reconciliation" in model
    slice_ = model["reconciliation"]
    assert slice_["readOnly"] is True
    assert slice_["derived"] is True
    assert slice_["totalCount"] >= 1
    assert slice_["totals"]["VND"]["obligations"]["amount"] == 12_000_000.0
    assert slice_["unavailable"] == list(desk.UNAVAILABLE_CONTEXT)
    # Navigation to the canonical writers, never a second writer here.
    assert {action["href"] for action in slice_["actions"]} == {
        desk.PAYABLE_WORKLIST_ROUTE, desk.RECEIVABLE_WORKLIST_ROUTE
    }


def test_filter_selection_is_a_lookup_input_only(staging, event_seq):
    """The bounded event records a filter; it never mutates canonical truth."""
    from core.financial_ledger import OBLIGATIONS
    from core.database import get_db

    assert _record_payable(event_seq, "REC-FILTER", 42_000_000.0)["ok"]
    before = get_db()[OBLIGATIONS].count_documents({})

    view = desk.reconciliation_view({"query": "REC-FILTER", "currency": "VND", "state": "ALL", "side": "ALL"})
    assert view["query"] == "REC-FILTER"
    assert view["totalCount"] >= 1

    after = get_db()[OBLIGATIONS].count_documents({})
    assert before == after
