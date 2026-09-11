"""LOGI_PARTNER_CONTEXT_WORKSPACE_01 — focused backend acceptance for /ngu-canh-doi-tac.

Proves the bounded READ-ONLY partner-context adapter (``views.partner_context``)
and its view-model / dispatcher wiring over the EXISTING authoritative readers:

    core.entity_context (shipment-partner index)
    core.database.load_authority_agents (legal Agent master)
    views.logi_real_data.partner_payables_projection (canonical C2B/C2D ledger)

Business-truth invariants checked here:

- partner identity is the authority_agents master, verbatim — never invented
- a missing partner / missing master stays UNKNOWN (never a blank record)
- UNKNOWN != ZERO: no canonical payable ⇒ no row + UNKNOWN status, never 0
- financial figures pass through unchanged and currencies are never combined
- linked shipments are authoritative ids with the existing open-route only
- no relationship / risk / credit / tier / SLA / note / activity surface exists
- the workspace is read-only: no input mapping is mutated, nothing is written

Production database is never touched (isolated mongomock staging only).
"""

from __future__ import annotations

import copy
import json

import pytest

from views import logi_real_data as rd
from views import logi_sandbox
from views import logi_view_model as vm
from views import partner_context as pc


AGENT_ID = "AGT-PHUANH"
AGENT_NAME = "CÔNG TY TNHH PHÚ ANH LOGISTICS"
OTHER_ID = "AGT-KHAC"
OTHER_NAME = "ĐỐI TÁC KHAC CO."
SHIPMENT = "LO-0308"
CCY = "VND"
AMOUNT = 57_000_000.0


def _agents() -> dict:
    return {
        AGENT_ID: {
            "agent_id": AGENT_ID,
            "id": AGENT_ID,
            "legal_name": AGENT_NAME,
            "legal_code": "0315678910",
            "legal_address": "Số 45, Nguyễn Văn Linh, Quận 7, TP. Hồ Chí Minh",
            "legal_representative": "Phạm Văn Thành",
            "representative_title": "Giám đốc",
            "phone": "0281234567",
            "email": "sales@phuanh.vn",
            "bank_account_holder": "PHÚ ANH LOGISTICS",
            "bank_account_number": "9876543210",
            "bank_name": "Techcombank",
            "bank_branch": "Hội sở TP.HCM",
        }
    }


def _shipments() -> dict:
    """One shipment naming the partner, one naming a different partner."""
    return {
        SHIPMENT: {
            "id": SHIPMENT,
            "shipment_id": SHIPMENT,
            "customer": "An Phát JSC",
            "customer_id": "CUST-ANPHAT",
            "status": "pending",
            "partner": {"name": AGENT_NAME, "role": "Thủ tục hải quan"},
            "data": {
                "0.0": {"created_at": "2026-08-01", "mode": "Sea"},
                "1.2": {"pol": "Yantian", "pod": "Cat Lai"},
                "3.4": {"details": [], "payments": []},
            },
        },
        "LO-0909": {
            "id": "LO-0909",
            "shipment_id": "LO-0909",
            "customer": "Đức Long Co.",
            "status": "delivered",
            "partner": {"name": OTHER_NAME, "role": "Vận tải nội địa"},
            "data": {"0.0": {}, "1.2": {}, "3.4": {}},
        },
    }


def _payable_rows(partner_id: str = AGENT_ID, partner_name: str = AGENT_NAME,
                  shipment: str = SHIPMENT, **overrides) -> list[dict]:
    row = {
        "id": f"{shipment}|{partner_id}|{CCY}",
        "partnerId": partner_id,
        "partnerName": partner_name,
        "shipmentId": shipment,
        "currency": CCY,
        "payable": AMOUNT,
        "paid": 20_000_000.0,
        "remaining": 37_000_000.0,
        "status": "CONFIRMED",
        "obligationIds": ["OBL-1"],
    }
    row.update(overrides)
    return [row]


def _projection(selected, *, agents=None, shipments=None, rows=None, customers=None) -> dict:
    return pc.partner_context_projection(
        selected,
        agents=_agents() if agents is None else agents,
        customers={"CUST-ANPHAT": {"id": "CUST-ANPHAT", "name": "An Phát JSC"}} if customers is None else customers,
        shipments=_shipments() if shipments is None else shipments,
        payables={"rows": _payable_rows() if rows is None else rows},
    )


# ---------------------------------------------------------------------------
# Selection: the simplest authoritative lookup
# ---------------------------------------------------------------------------

def test_options_come_from_master_ledger_and_shipment_index() -> None:
    view = _projection(None)
    # Nothing selected yet ⇒ options only, no invented context.
    assert view["status"] == pc.NO_SELECTION
    keys = {option["key"] for option in view["options"]}
    # authority_agents master (AGT-PHUANH) and the shipment-partner index, whose
    # second partner name is NOT in any master — it still has to be selectable.
    assert AGENT_ID in keys and OTHER_NAME in keys
    master = next(o for o in view["options"] if o["key"] == AGENT_ID)
    assert master["master"] is True
    assert master["label"] == AGENT_NAME
    assert "authority_agents" in master["sources"]
    assert master["shipmentIds"] == [SHIPMENT]
    unmastered = next(o for o in view["options"] if o["key"] == OTHER_NAME)
    assert unmastered["master"] is False
    assert unmastered["sources"] == ["shipment partner/agent index"]


def test_no_partner_source_is_reported_as_unknown_not_empty() -> None:
    view = pc.partner_context_projection("AGT-X", agents={}, customers={}, shipments={},
                                         payables={"rows": []})
    assert view["status"] == pc.NO_SOURCE
    assert view["options"] == []
    # The honest reason must say nothing was fabricated.
    assert "không có dữ liệu mẫu" in view["reason"]


def test_missing_partner_fails_honest_and_keeps_options() -> None:
    view = _projection("AGT-KHONG-TON-TAI")
    assert view["status"] == pc.NOT_FOUND
    assert view["selectedKey"] is None and view["selectedLabel"] is None
    assert "identity" not in view and "shipments" not in view
    assert len(view["options"]) == 2
    assert "không có bản ghi nào được tạo thay thế" in view["reason"]


def test_multiple_partners_stay_separate() -> None:
    view = _projection(OTHER_NAME, rows=[])
    assert view["selectedLabel"] == OTHER_NAME
    assert [row["shipmentId"] for row in view["shipments"]] == ["LO-0909"]
    assert view["finance"]["rows"] == []


# ---------------------------------------------------------------------------
# Identity: authoritative master fields only
# ---------------------------------------------------------------------------

def test_identity_is_the_authority_agents_master_verbatim() -> None:
    view = _projection(AGENT_ID)
    identity = view["identity"]
    assert identity["masterStatus"] == "KNOWN"
    assert identity["masterSource"] == "authority_agents (legal Agent master)"
    party = identity["party"]
    assert party["legalName"] == AGENT_NAME
    assert party["legalCode"] == "0315678910"
    assert party["legalAddress"] == "Số 45, Nguyễn Văn Linh, Quận 7, TP. Hồ Chí Minh"
    assert party["representative"] == "Phạm Văn Thành"
    assert party["phone"] == "0281234567"
    assert party["bankAccountNumber"] == "9876543210"


def test_partner_without_master_record_stays_unknown() -> None:
    view = _projection(OTHER_NAME, rows=[])
    identity = view["identity"]
    assert identity["party"] is None
    assert identity["masterStatus"] == "UNKNOWN"
    assert any("master" in gap.lower() for gap in view["gaps"])
    # A contradicted "no master" gap must not be duplicated when a master exists.
    known = _projection(AGENT_ID)
    assert not [gap for gap in known["gaps"] if "contact data unknown" in gap.lower()]


def test_blank_master_fields_report_as_missing_not_empty_strings() -> None:
    thin = _agents()
    thin[AGENT_ID]["email"] = ""
    view = _projection(AGENT_ID, agents=thin)
    assert view["identity"]["party"]["email"] == ""       # passthrough, unedited
    assert any(gap.startswith("email") for gap in view["gaps"])


# ---------------------------------------------------------------------------
# Linked shipments
# ---------------------------------------------------------------------------

def test_linked_shipment_rows_use_authoritative_ids_and_existing_route() -> None:
    view = _projection(AGENT_ID)
    assert view["shipmentCount"] == 1
    row = view["shipments"][0]
    assert row["shipmentId"] == SHIPMENT
    assert row["openHref"] == "/lo-hang/LO-0308"
    assert row["canOpen"] is True
    assert row["role"] == "Thủ tục hải quan"
    assert "core.entity_context" in row["source"] or "shipment_dashboard" in row["source"]


def test_ledger_only_shipment_still_links_but_is_marked_unopenable() -> None:
    # A payable row for a shipment that is NOT in the current shipment list must
    # never be offered as a working Open Shipment action.
    view = _projection(AGENT_ID, shipments={})
    assert view["shipmentCount"] >= 1
    row = view["shipments"][0]
    assert row["canOpen"] is False
    assert "không có trong danh sách lô hiện tại" in row["source"]


def test_financial_projection_fields_do_not_duplicate_shipment_detail() -> None:
    view = _projection(AGENT_ID)
    row = view["shipments"][0]
    # The adapter links; it never re-renders a shipment detail page.
    assert not {"packages", "cargo", "transport", "documents", "finance"} & set(row)
    assert set(row) <= {
        "shipmentId", "status", "requiredDate", "plannedDate", "attention",
        "attentionDetail", "role", "route", "operationalContext", "source",
        "financeCurrencies", "openHref", "canOpen",
    }


# ---------------------------------------------------------------------------
# Finance: reuse C2B/C2D truth, never recompute
# ---------------------------------------------------------------------------

def test_finance_rows_are_the_c2d_projection_verbatim() -> None:
    view = _projection(AGENT_ID)
    finance = view["finance"]
    assert len(finance["rows"]) == 1
    row = finance["rows"][0]
    assert row["payable"] == AMOUNT
    assert row["paid"] == 20_000_000.0
    assert row["remaining"] == 37_000_000.0
    assert row["currency"] == CCY
    assert row["status"] == "CONFIRMED"
    assert row["obligationIds"] == ["OBL-1"]
    assert "shipment_partner_position" in row["source"]


def test_no_partner_level_payable_summary_is_invented() -> None:
    view = _projection(AGENT_ID, rows=[
        *_payable_rows(),
        _payable_rows(shipment="LO-0404", currency="USD", payable=1_000.0,
                      paid=400.0, remaining=600.0)[0],
    ])
    finance = view["finance"]
    # Grouping is by currency, and it carries COUNTS only — no amounts.
    assert set(finance["byCurrency"]) == {CCY, "USD"}
    assert finance["byCurrency"][CCY] == {"rowCount": 1, "shipmentIds": [SHIPMENT], "obligationCount": 1}
    assert finance["byCurrency"]["USD"]["rowCount"] == 1
    assert not {"total", "totals", "sum", "grandTotal"} & set(finance)
    assert "không quy đổi tiền tệ" in finance["note"]
    assert finance["worklistHref"] == "/tai-chinh/cong-no-doi-tac"


def test_unknown_not_zero_without_canonical_payable() -> None:
    view = _projection(AGENT_ID, rows=[])
    finance = view["finance"]
    assert finance["rows"] == []
    assert finance["status"] == "UNKNOWN"
    assert finance["statusLabel"] == "CHƯA XÁC ĐỊNH"
    assert finance["byCurrency"] == {}
    assert any("CHƯA XÁC ĐỊNH, không phải 0" in gap for gap in view["gaps"])


def test_review_required_status_is_preserved() -> None:
    view = _projection(AGENT_ID, rows=_payable_rows(status="REVIEW_REQUIRED"))
    assert view["finance"]["status"] == "REVIEW_REQUIRED"
    assert view["finance"]["statusLabel"] == "CẦN REVIEW"


# ---------------------------------------------------------------------------
# No CRM surface, and read-only
# ---------------------------------------------------------------------------

FORBIDDEN_KEYS = {
    "relationshipScore", "riskScore", "creditScore", "reliabilityScore",
    "paymentBehaviorScore", "partnerTier", "tier", "accountManager", "sla",
    "notes", "partnerNote", "activity", "activityTimeline", "tags", "documents",
}


def test_no_crm_fields_exist_anywhere_in_the_payload() -> None:
    payload = _projection(AGENT_ID)
    # documents is legitimately the EXISTING per-shipment evidence passthrough;
    # everything CRM-shaped must be absent.
    assert "Điểm quan hệ đối tác" in " ".join(payload["unavailable"])

    def _keys(node) -> set[str]:
        if isinstance(node, dict):
            return set(node) | {k for child in node.values() for k in _keys(child)}
        if isinstance(node, list):
            return {k for child in node for k in _keys(child)}
        return set()

    assert not _keys(payload) & (FORBIDDEN_KEYS - {"documents"})


def test_workspace_is_read_only_and_inputs_are_untouched() -> None:
    agents, shipments = _agents(), _shipments()
    before = (copy.deepcopy(agents), copy.deepcopy(shipments))
    view = _projection(AGENT_ID, agents=agents, shipments=shipments)
    assert view["readOnly"] is True
    assert (agents, shipments) == before
    assert "readOnly" not in view or view["readOnly"] is True


def test_unknown_sentinel_from_entity_context_never_leaks_as_a_word() -> None:
    # core.entity_context writes the literal "UNKNOWN"; the adapter must deliver
    # None so the UI renders an explicit em dash rather than a magic string.
    view = _projection(AGENT_ID, shipments=_shipments())
    assert view["identity"]["contextId"] is None
    assert all(row["plannedDate"] is None or row["plannedDate"] != "UNKNOWN"
               for row in view["shipments"])


# ---------------------------------------------------------------------------
# View-model + the ONE bounded read-only selection event
# ---------------------------------------------------------------------------

@pytest.fixture()
def staging():
    import streamlit as st

    logi_sandbox.reset_backend()
    transport = logi_sandbox.ensure_backend()
    assert transport == logi_sandbox.SANDBOX_TRANSPORT
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)
    st.session_state.pop(vm.PARTNER_CONTEXT_KEY, None)
    yield transport
    st.session_state.pop(vm.PARTNER_CONTEXT_KEY, None)
    logi_sandbox.reset_backend()


def test_selection_event_is_bounded_and_read_only() -> None:
    assert vm.PARTNER_CONTEXT_EVENTS == {"partner_context_select"}
    assert "partner_context_select" in vm.ALL_EVENTS
    # No partner edit/note/tag/task/CRM events were introduced.
    assert not {"partner_edit", "partner_note", "partner_activity", "partner_tag"} & vm.ALL_EVENTS


def test_dispatcher_records_selection_and_refuses_replay(staging) -> None:
    import streamlit as st

    trigger = {"partner_context_select": {"seq": 7, "event": "partner_context_select",
                                          "payload": {"entityKey": "  " + AGENT_ID + "  "}}}
    outcomes = vm.consume_partner_context_triggers({"seq": 0}, trigger)
    assert len(outcomes) == 1 and outcomes[0]["ok"] is True
    assert st.session_state[vm.PARTNER_CONTEXT_KEY] == AGENT_ID   # trimmed, not padded
    # Same seq replayed ⇒ ignored (one-shot trigger protection).
    assert vm.consume_partner_context_triggers({"seq": 7}, trigger) == []
    assert st.session_state[vm.PARTNER_CONTEXT_KEY] == AGENT_ID
    # An empty selection clears the workspace instead of leaving a stale partner.
    clear = {"partner_context_select": {"seq": 8, "event": "partner_context_select",
                                        "payload": {"entityKey": ""}}}
    assert vm.consume_partner_context_triggers({"seq": 0}, clear)[0]["ok"] is True
    assert vm.PARTNER_CONTEXT_KEY not in st.session_state
    # Foreign events are never consumed here.
    assert vm.consume_partner_context_triggers(
        {"seq": 0}, {"partner_payable_record": {"seq": 9, "payload": {}}}) == []


def test_view_model_exposes_the_partner_context_slice(staging) -> None:
    model = vm.build_view_model()
    view = model["partnerContext"]
    assert view["readOnly"] is True
    assert AGENT_ID in {option["key"] for option in view["options"]}
    assert view["status"] == pc.NO_SELECTION
    # The slice never becomes a second payable summary of its own.
    assert "payables" in model and model["payables"]["rows"] == []


def test_real_canonical_payable_links_shipment_and_amounts(staging) -> None:
    """End-to-end on staging: one C2B obligation ⇒ real linked shipment."""
    import streamlit as st

    outcome = vm.consume_phase_b_triggers({"seq": 0}, {"partner_payable_record": {
        "seq": 1, "event": "partner_payable_record",
        "payload": {"shipmentId": SHIPMENT, "partnerId": AGENT_ID, "requestId": "PCX-1",
                    "amount": AMOUNT, "currency": CCY, "note": "Chi phí đối tác"},
    }})[0]
    assert outcome["ok"], outcome["error"]

    st.session_state[vm.PARTNER_CONTEXT_KEY] = AGENT_ID
    view = vm.build_view_model()["partnerContext"]
    assert view["status"] == pc.OK
    assert [row["shipmentId"] for row in view["shipments"]] == [SHIPMENT]
    assert view["shipments"][0]["canOpen"] is True
    assert view["shipments"][0]["openHref"] == "/lo-hang/" + SHIPMENT
    row = view["finance"]["rows"][0]
    assert (row["payable"], row["currency"], row["status"]) == (AMOUNT, CCY, "CONFIRMED")
    assert row["remaining"] == AMOUNT          # nothing paid yet: remaining == payable
    # The C2D worklist is the SAME truth — the adapter did not re-derive it.
    model = vm.build_view_model()
    assert model["payables"]["rows"][0]["payable"] == row["payable"]
    assert model["payables"]["rows"][0]["remaining"] == row["remaining"]
    # No master gap is reported for a partner that has one.
    assert not [gap for gap in view["gaps"] if "master" in gap.lower() and "không có" in gap.lower()]
    # And the projection is a passthrough: no extra amount key was created.
    assert set(row) == {"id", "shipmentId", "currency", "payable", "paid", "remaining",
                        "status", "obligationIds", "source"}


def test_serialisable_payload(staging) -> None:
    """JSON-cleanliness is part of the component contract (no stray objects)."""
    import streamlit as st

    st.session_state[vm.PARTNER_CONTEXT_KEY] = AGENT_ID
    json.dumps(vm.build_view_model()["partnerContext"], ensure_ascii=False)
    assert rd.UNKNOWN is None
