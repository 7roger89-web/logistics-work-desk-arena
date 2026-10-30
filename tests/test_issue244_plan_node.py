"""Issue #244 — Node 00 KẾ HOẠCH: báo giá → hợp đồng khách → tạm ứng.

Every assertion below is about TRUTH BOUNDARIES, not cosmetics:

1. the lot's quote comes from its exact ``quote_id`` (a same-customer sibling
   quote is never borrowed);
2. a customer contract is only the customer-facing instrument linked to this lot
   (a TT↔sub-agent purchase contract can never stand in for it);
3. `đã ký` requires recorded evidence — a linked contract / PDF is not a
   signature;
4. `đã nhận tiền` is unreachable: an unclassified receipt is "cần đối soát";
5. the customer sees ONLY the three published plan document kinds, metadata
   only, and a published file proves neither signature nor payment.
"""

from __future__ import annotations

from copy import deepcopy

import pytest

from core import customer_journey
from core import journey_notes
from core.shipment_plan import (
    ADVANCE_MODE_UNKNOWN,
    ADVANCE_NOT_APPLICABLE,
    ADVANCE_UNVERIFIED,
    CONTRACT_STATE_AMBIGUOUS,
    CONTRACT_STATE_LINKED,
    CONTRACT_STATE_MISSING,
    QUOTE_STATE_LINKED,
    QUOTE_STATE_MISSING,
    QUOTE_STATE_UNRESOLVED,
    SIGNATURE_ATTESTED,
    SIGNATURE_UNVERIFIED,
    build_plan_node,
    customer_plan_documents,
)
from views import journey_focus
from views import logi_real_data as rd
from views import journey_inline

SHIPMENT_ID = "LO-244"
CUSTOMER_ID = "CUST-ANPHAT"
OTHER_CUSTOMER_ID = "CUST-DUCLONG"


def shipment(**overrides):
    row = {
        "id": SHIPMENT_ID,
        "customer_id": CUSTOMER_ID,
        "customer": "An Phát JSC",
        "quote_id": "",
        "data": {"0.0": {"commercial_flow": {}}},
    }
    row.update(overrides)
    return row


def quote(identifier: str, customer_id: str, status: str = "SENT"):
    return {
        "id": identifier,
        "quote_no": identifier,
        "customer_id": customer_id,
        "status": status,
    }


def contract(identifier: str, *, customer_id: str = "", agent_id: str = "", **extra):
    row = {"id": identifier, "contract_no": identifier, "shipment_ids": [SHIPMENT_ID]}
    if customer_id:
        row["customer_id"] = customer_id
    if agent_id:
        row["agent_id"] = agent_id
    row.update(extra)
    return row


def flow(mode: str, confirmed: bool = True):
    return {"mode": mode, "confirmed": confirmed}


# --------------------------------------------------------------------------- #
# 1. Báo giá — exact quote_id only
# --------------------------------------------------------------------------- #

def test_quote_uses_only_the_exact_quote_id_and_never_a_sibling_quote():
    quotes = {
        "BG-244": quote("BG-244", CUSTOMER_ID, "ACCEPTED"),
        "BG-999": quote("BG-999", CUSTOMER_ID, "ACCEPTED"),
    }
    node = build_plan_node(shipment(quote_id="BG-999"), quotes=quotes)
    item = node["items"][0]
    assert item["state"] == QUOTE_STATE_LINKED
    assert item["quoteId"] == "BG-999"
    assert item["quoteNo"] == "BG-999"
    assert item["accepted"] is True


def test_lot_without_quote_stays_unlinked_even_if_the_customer_has_quotes():
    quotes = {"BG-244": quote("BG-244", CUSTOMER_ID, "ACCEPTED")}
    node = build_plan_node(shipment(), quotes=quotes)
    item = node["items"][0]
    assert item["state"] == QUOTE_STATE_MISSING
    assert item["stateLabel"] == "Chưa gắn báo giá"
    assert item["quoteId"] == ""
    # The customer's other accepted quote is never borrowed for this lot.
    assert "BG-244" not in node["evidence"]


def test_linked_quote_does_not_mean_accepted():
    quotes = {"BG-244": quote("BG-244", CUSTOMER_ID, "SENT")}
    item = build_plan_node(shipment(quote_id="BG-244"), quotes=quotes)["items"][0]
    assert item["state"] == QUOTE_STATE_LINKED
    assert item["accepted"] is False
    assert item["stateLabel"] == "Đã gửi khách"
    assert "Chưa có trạng thái khách chấp nhận" in item["detail"]


def test_quote_id_pointing_nowhere_is_reported_as_unresolved():
    item = build_plan_node(shipment(quote_id="BG-GONE"), quotes={})["items"][0]
    assert item["state"] == QUOTE_STATE_UNRESOLVED
    assert "BG-GONE" in item["detail"]


# --------------------------------------------------------------------------- #
# 2. Hợp đồng với khách — the right instrument, never the sub-agent one
# --------------------------------------------------------------------------- #

def test_sub_agent_contract_is_never_reported_as_the_customer_contract():
    contracts = {"HDMB-SUB": contract("HDMB-SUB", agent_id="AGT-PHUANH")}
    linked = {SHIPMENT_ID: contracts}
    item = build_plan_node(
        shipment(), contracts=contracts, linked_contracts=linked
    )["items"][1]
    assert item["state"] == CONTRACT_STATE_MISSING
    assert item["contractId"] == ""
    assert "Không dùng hợp đồng Trường Thành ↔ đơn vị nhập khẩu hộ" in item["detail"]


def test_customer_contract_link_is_not_a_signature():
    contracts = {"HDMB-244": contract("HDMB-244", customer_id=CUSTOMER_ID)}
    item = build_plan_node(
        shipment(),
        contracts=contracts,
        linked_contracts={SHIPMENT_ID: contracts},
    )["items"][1]
    assert item["state"] == CONTRACT_STATE_LINKED
    assert item["signature"] == SIGNATURE_UNVERIFIED
    assert item["signatureLabel"] == "Chưa xác minh chữ ký"
    assert "chưa có bằng chứng chữ ký" in item["detail"]
    # The only mention of signing is the explicit negation.
    assert "không đồng nghĩa đã ký" in item["detail"]
    assert "Đã ký" not in item["detail"]


def test_recorded_agreement_evidence_is_the_only_attestation():
    contracts = {"HDMB-244": contract("HDMB-244", customer_id=CUSTOMER_ID)}
    agreements = {
        "AGR-1": {
            "agreement_id": "AGR-1",
            "customer_id": CUSTOMER_ID,
            "shipment_ids": [SHIPMENT_ID],
            "status": "AGREED",
            "evidence": {"signed_contract": True},
        }
    }
    item = build_plan_node(
        shipment(),
        contracts=contracts,
        linked_contracts={SHIPMENT_ID: contracts},
        agreements=agreements,
    )["items"][1]
    assert item["signature"] == SIGNATURE_ATTESTED
    assert item["signatureLabel"] == "Đã có xác nhận ký"


def test_agreement_evidence_only_counts_for_the_right_lot_and_status():
    contracts = {"HDMB-244": contract("HDMB-244", customer_id=CUSTOMER_ID)}
    for index, agreement in enumerate((
        {"customer_id": CUSTOMER_ID, "shipment_ids": ["LO-OTHER"], "status": "AGREED",
         "evidence": {"signed_contract": True}},
        {"customer_id": CUSTOMER_ID, "shipment_ids": [SHIPMENT_ID], "status": "DRAFT",
         "evidence": {"signed_contract": True}},
        {"customer_id": OTHER_CUSTOMER_ID, "shipment_ids": [SHIPMENT_ID], "status": "AGREED",
         "evidence": {"signed_contract": True}},
    )):
        item = build_plan_node(
            shipment(),
            contracts=contracts,
            linked_contracts={SHIPMENT_ID: contracts},
            agreements={f"AGR-{index}": agreement},
        )["items"][1]
        assert item["signature"] == SIGNATURE_UNVERIFIED, agreement


def test_two_matching_customer_contracts_stay_ambiguous():
    contracts = {
        "HDMB-1": contract("HDMB-1", customer_id=CUSTOMER_ID),
        "HDMB-2": contract("HDMB-2", customer_id=CUSTOMER_ID),
    }
    item = build_plan_node(
        shipment(), contracts=contracts, linked_contracts={SHIPMENT_ID: contracts}
    )["items"][1]
    assert item["state"] == CONTRACT_STATE_AMBIGUOUS
    assert item["stateLabel"] == "Chưa xác minh"
    assert item["contractId"] == ""


# --------------------------------------------------------------------------- #
# 3. Tạm ứng tiền hàng — applicability comes from the confirmed import flow
# --------------------------------------------------------------------------- #

def test_customer_self_flow_is_not_applicable():
    node = build_plan_node(shipment(), flow=flow("CUSTOMER_SELF"))
    item = node["items"][2]
    assert item["state"] == ADVANCE_NOT_APPLICABLE
    assert item["stateLabel"] == "Không áp dụng"
    assert item["received"] is False


@pytest.mark.parametrize("mode", ["TT_ENTRUSTED_DIRECT", "TT_ENTRUSTED_SUB"])
def test_entrusted_flow_is_unverified_and_never_paid(mode):
    item = build_plan_node(shipment(), flow=flow(mode))["items"][2]
    assert item["state"] == ADVANCE_UNVERIFIED
    assert item["stateLabel"] == "Chưa xác minh đã nhận"
    assert item["received"] is False


def test_unclassified_receipt_is_reconciliation_not_payment():
    payments = [
        {"id": "P1", "amount": 20000000, "kind": "Khoản thu", "reversed": False},
        {"id": "P2", "amount": 5000000, "kind": "Khoản thu", "reversed": True},
    ]
    item = build_plan_node(
        shipment(), flow=flow("TT_ENTRUSTED_DIRECT"), payments=payments
    )["items"][2]
    assert item["state"] == ADVANCE_UNVERIFIED
    assert item["reconcileCount"] == 1
    assert item["received"] is False
    assert "cần đối soát" in item["detail"]
    assert "không kết luận đã thanh toán" in item["detail"]
    # No amount ever crosses into the plan projection.
    assert "20000000" not in item["detail"]


def test_unknown_flow_keeps_advance_undetermined():
    node = build_plan_node(shipment(), flow={})
    item = node["items"][2]
    assert item["state"] == ADVANCE_MODE_UNKNOWN
    assert item["stateLabel"] == "Chưa xác nhận hình thức nhập khẩu"
    assert item["applicable"] is None


def test_unconfirmed_stored_mode_does_not_become_confirmed():
    node = build_plan_node(shipment(), flow=flow("TT_ENTRUSTED_SUB", confirmed=False))
    assert node["items"][2]["state"] == ADVANCE_MODE_UNKNOWN


# --------------------------------------------------------------------------- #
# 4. Node state + "what is missing / what next"
# --------------------------------------------------------------------------- #

def test_node_is_problem_without_a_quote():
    node = build_plan_node(shipment(), flow=flow("CUSTOMER_SELF"))
    assert node["state"] == "PROBLEM"
    assert node["label"] == "KẾ HOẠCH"
    assert any("Gắn báo giá" in action for action in node["nextActions"])


def test_node_waiting_when_contract_signature_is_unproven():
    quotes = {"BG-244": quote("BG-244", CUSTOMER_ID, "ACCEPTED")}
    contracts = {"HDMB-244": contract("HDMB-244", customer_id=CUSTOMER_ID)}
    node = build_plan_node(
        shipment(quote_id="BG-244"),
        quotes=quotes,
        contracts=contracts,
        linked_contracts={SHIPMENT_ID: contracts},
        flow=flow("CUSTOMER_SELF"),
    )
    assert node["state"] == "WAITING"
    assert any("chưa có bằng chứng chữ ký" in action for action in node["nextActions"])


def test_node_complete_only_with_evidence_everywhere():
    quotes = {"BG-244": quote("BG-244", CUSTOMER_ID, "ACCEPTED")}
    contracts = {"HDMB-244": contract("HDMB-244", customer_id=CUSTOMER_ID)}
    agreements = {"AGR-1": {
        "customer_id": CUSTOMER_ID,
        "shipment_ids": [SHIPMENT_ID],
        "status": "AGREED",
        "evidence": {"signed_contract": True},
    }}
    node = build_plan_node(
        shipment(quote_id="BG-244"),
        quotes=quotes,
        contracts=contracts,
        linked_contracts={SHIPMENT_ID: contracts},
        agreements=agreements,
        flow=flow("CUSTOMER_SELF"),
    )
    assert node["state"] == "COMPLETED"
    assert node["nextActions"] == []


# --------------------------------------------------------------------------- #
# 5. Integration: the real staff projection carries Node 00
# --------------------------------------------------------------------------- #

def test_staff_projection_exposes_node_00_from_real_sources():
    quotes = {
        "BG-244": quote("BG-244", CUSTOMER_ID, "ACCEPTED"),
        "BG-999": quote("BG-999", CUSTOMER_ID, "ACCEPTED"),
    }
    contracts = {"HDMB-244": contract("HDMB-244", customer_id=CUSTOMER_ID)}
    projected = rd.shipment_projection(
        shipment(quote_id="BG-244"),
        quotes=quotes,
        contracts=contracts,
        linked_contracts={SHIPMENT_ID: contracts},
        agreements={},
    )
    plan = projected["plan"]
    assert plan["id"] == "plan"
    assert plan["items"][0]["quoteId"] == "BG-244"
    assert plan["items"][1]["contractId"] == "HDMB-244"
    assert plan["items"][1]["signature"] == SIGNATURE_UNVERIFIED
    # The unrelated sibling quote never leaks into the payload.
    assert "BG-999" not in str(plan)


def test_staff_projection_payload_never_claims_signature_or_payment():
    projected = rd.shipment_projection(
        shipment(quote_id=""),
        quotes={},
        contracts={"HDMB-SUB": contract("HDMB-SUB", agent_id="AGT-PHUANH")},
        linked_contracts={SHIPMENT_ID: {"HDMB-SUB": contract("HDMB-SUB", agent_id="AGT-PHUANH")}},
    )
    plan_text = str(projected["plan"])
    for forbidden in ("'received': True", "'signature': 'ATTESTED'", "công nợ", "đã nhận tiền"):
        assert forbidden not in plan_text
    assert "'received': False" in plan_text


# --------------------------------------------------------------------------- #
# 6. The Node 00 discussion thread is the SAME canonical ``plan`` stage
# --------------------------------------------------------------------------- #

def test_node_00_maps_to_the_existing_plan_stage():
    assert journey_focus.resolve_node_stage("plan") == "plan"
    assert journey_focus.resolve_node_stage("plan", journey_focus.STAFF_NODE_STAGES) == "plan"
    assert "plan" in journey_notes.STAGE_IDS


def test_node_00_focus_still_requires_the_lot_to_belong_to_the_actor():
    request = {"shipment_id": SHIPMENT_ID, "stage_id": "plan", "username": "sale1"}
    cards = [{"id": SHIPMENT_ID, "customerId": CUSTOMER_ID}]
    resolved = journey_focus.for_staff(request, "sale1", cards)
    assert resolved is not None and resolved["stage_id"] == "plan"
    assert journey_focus.for_staff(request, "sale1", [{"id": "LO-OTHER", "customerId": CUSTOMER_ID}]) is None
    # A forged actor scope can only fail closed.
    assert journey_focus.for_staff({**request, "username": "khac"}, "sale1", cards) is None


def test_viewer_role_can_read_but_never_writes_a_plan_comment():
    from core.journey_notes import JourneyNoteDenied, create_stage_note

    assert journey_notes.user_may_write("viewer") is False
    assert journey_notes.user_may_write("admin") is True
    with pytest.raises(JourneyNoteDenied):
        create_stage_note(
            customer_id=CUSTOMER_ID,
            shipment_id=SHIPMENT_ID,
            stage_id="plan",
            body="Ghi chú trái quyền",
            actor={"kind": "user", "username": "viewer1", "role": "viewer"},
        )


def test_customer_actor_cannot_be_mistaken_for_staff():
    assert journey_inline.staff_actor({"username": "x"}) is None
    assert journey_inline.staff_actor({"username": "x", "role": ""}) is None


# --------------------------------------------------------------------------- #
# 7. Customer side — only the three published plan kinds
# --------------------------------------------------------------------------- #

def published_rows():
    return [
        {"id": "Q1", "version": "3", "kind": "CUSTOMER_QUOTE", "title": "Báo giá LOGI"},
        {"id": "C1", "version": "1", "kind": "CUSTOMER_CONTRACT", "title": "Hợp đồng 0306"},
        {"id": "R1", "version": "2", "kind": "PAYMENT_REQUEST", "title": "Đề nghị tạm ứng"},
        {"id": "BL1", "version": "1", "kind": "BL", "title": "Bill of lading"},
        {"id": "CI1", "version": "1", "kind": "CUSTOMER_INVOICE", "title": "Hoá đơn"},
    ]


def test_customer_plan_documents_is_an_explicit_kind_filter():
    rows = customer_plan_documents(published_rows())
    assert [row["kind"] for row in rows] == [
        "CUSTOMER_QUOTE", "CUSTOMER_CONTRACT", "PAYMENT_REQUEST",
    ]
    assert [row["label"] for row in rows] == ["Báo giá", "Hợp đồng", "Đề nghị thanh toán"]


def test_customer_plan_documents_carry_no_money_and_no_bytes():
    rows = customer_plan_documents([
        {**row, "amount": 385000000, "bytes": "JVBERi0=", "storage_id": "drive-1",
         "cost": 300000000, "margin": 85000000}
        for row in published_rows()
    ])
    for row in rows:
        assert set(row) == {"kind", "label", "title", "version"}
    text = str(rows)
    assert "385000000" not in text and "JVBERi0" not in text and "drive-1" not in text


def test_customer_plan_documents_rejects_unversioned_or_unidentified_rows():
    assert customer_plan_documents([{"kind": "CUSTOMER_QUOTE", "title": "không id"}]) == []
    assert customer_plan_documents([{"id": "Q1", "kind": "INTERNAL_QUOTE"}]) == []


class _Card:
    reference = SHIPMENT_ID
    status_label = "Đang thực hiện"
    transport_mode = "SEA"
    publication_version = "7"
    approved_at = "2026-10-30T08:00:00+00:00"
    timeline = ()
    quote = None

    def __init__(self, documents):
        self.documents = tuple(documents)


def test_customer_lot_model_publishes_only_plan_kinds_and_keeps_stage_documents_empty():
    lot = customer_journey.build_lot_model(_Card(published_rows()))
    assert [row["kind"] for row in lot["plan_documents"]] == [
        "CUSTOMER_QUOTE", "CUSTOMER_CONTRACT", "PAYMENT_REQUEST",
    ]
    plan_node = next(node for node in lot["journey"]["nodes"] if node["id"] == "plan")
    # Intentionally unchanged: a document has no approved stage binding in G1.
    assert plan_node["stage_documents"] == []
    # A published document is not a completed stage.
    assert plan_node["state"] == "UNKNOWN"


def test_customer_lot_model_states_the_empty_case_explicitly():
    lot = customer_journey.build_lot_model(_Card([
        {"id": "BL1", "version": "1", "kind": "BL", "title": "Bill of lading"},
    ]))
    assert lot["plan_documents"] == []
    assert lot["plan_documents_empty_label"] == "Chưa có hồ sơ Kế hoạch được công bố"


def test_customer_lot_model_ignores_a_stale_or_unpublished_document():
    """The publication allowlist already filtered these out — no row arrives."""
    published = deepcopy(published_rows())
    lot = customer_journey.build_lot_model(_Card([
        row for row in published if row["id"] != "C1"
    ]))
    assert [row["kind"] for row in lot["plan_documents"]] == [
        "CUSTOMER_QUOTE", "PAYMENT_REQUEST",
    ]
