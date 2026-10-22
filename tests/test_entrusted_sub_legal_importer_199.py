"""TT_ENTRUSTED_SUB — legal importer identity must come from authority_companies.

Owner decision (2026-10-19): the legal importer of a sub-entrustment is a
COMPANY record.  ``sub_agent_id`` remains the contract/agent relation and is
never promoted into the shipment's legal identity.

All names/MSTs below are explicit FIXTURE records inserted into the isolated
mongomock staging database.  No production master data is read or written.
"""

from __future__ import annotations

import copy
from pathlib import Path

import pytest

from core import database
from views import logi_sandbox
from views import logi_view_model as vm

SHIPMENT_OK = "LO-0308"
SHIPMENT_LEGACY = "LO-0307"
SHIPMENT_GNT = "LO-0306"

FIXTT = {
    "id": "FIX-TT",
    "company_id": "FIX-TT",
    "legal_name": "CÔNG TY TNHH TRƯỜNG THÀNH (FIXTURE)",
    "tax_or_legal_code": "0109988776",
    "is_deleted": False,
}
FIX_IMPORTER_A = {
    "id": "FIX-IMP-A",
    "company_id": "FIX-IMP-A",
    "legal_name": "CÔNG TY TNHH ĐỐI TÁC NHẬP KHẨU HỘ A (FIXTURE)",
    "tax_or_legal_code": "0317000001",
    "is_deleted": False,
}
FIX_CONTRACT_B = {
    "id": "FIX-CONTRACT-B",
    "agent_id": "FIX-CONTRACT-B",
    "legal_name": "CÔNG TY TNHH ĐẠI LÝ HỢP ĐỒNG B (FIXTURE)",
    "legal_code": "0317000002",
    "is_deleted": False,
}


@pytest.fixture()
def staging():
    import streamlit as st

    logi_sandbox.reset_backend()
    assert logi_sandbox.ensure_backend() == logi_sandbox.SANDBOX_TRANSPORT
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)
    st.session_state.pop(vm.LAST_WRITES_KEY, None)
    db = database.get_db()
    db["authority_companies"].insert_many([copy.deepcopy(FIXTT), copy.deepcopy(FIX_IMPORTER_A)])
    db["authority_agents"].insert_one(copy.deepcopy(FIX_CONTRACT_B))
    yield
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
    outcomes = vm.consume_phase_b_triggers({"seq": 0}, seq_fn(name, payload))
    assert len(outcomes) == 1
    return outcomes[0]


def _flow_payload(sid: str, request_id: str, **overrides) -> dict:
    payload = {
        "shipmentId": sid,
        "requestId": request_id,
        "mode": "TT_ENTRUSTED_SUB",
        "companyId": "FIX-TT",
        "subAgentId": "FIX-CONTRACT-B",
        "importerCompanyId": "FIX-IMP-A",
    }
    payload.update(overrides)
    return payload


def _save_gnt_facts(seq_fn, sid: str, taxpayer_tax_code: str) -> None:
    saved = _dispatch(seq_fn, "shipment_field_save", {
        "shipmentId": sid,
        "fields": {
            "gnt_taxpayer_name": "NGƯỜI NỘP THUẾ FIXTURE",
            "gnt_taxpayer_tax_code": taxpayer_tax_code,
            "gnt_taxpayer_address": "ĐỊA CHỈ FIXTURE",
            "tk_no": "FIX-TK-0317",
            "tk_date": "15/08/2026",
            "import_duty_amount": "5000000",
            "import_vat_amount": "800000",
        },
    })
    assert saved["ok"], saved.get("error")


def _shipment_row(model: dict, sid: str) -> dict:
    return next(row for row in model["shipments"] if row["id"] == sid)


def test_writer_readback_and_fresh_projection_use_company_importer(staging, event_seq):
    db = database.get_db()
    before = vm.read_shipment(SHIPMENT_OK)
    assert before is not None
    version_before = int(before.get("version") or 0)
    finance_before = copy.deepcopy((before.get("data") or {}).get("3.4"))
    contracts_before = list(db["contracts"].find({}, {"_id": 0}))

    outcome = _dispatch(event_seq, "shipment_commercial_flow_save",
                        _flow_payload(SHIPMENT_OK, "FIX-FLOW-SUB-1"))
    assert outcome["ok"], outcome.get("error")
    persisted = outcome["persisted"]["commercialFlow"]
    assert persisted == {
        "mode": "TT_ENTRUSTED_SUB",
        "confirmed": True,
        "company_id": "FIX-TT",
        "sub_agent_id": "FIX-CONTRACT-B",
        "importer_company_id": "FIX-IMP-A",
    }

    readback = outcome["readback"]["commercialFlow"]
    assert readback["importerCompanyId"] == "FIX-IMP-A"
    assert readback["legalImporterKind"] == "COMPANY"
    assert readback["legalImporterName"] == FIX_IMPORTER_A["legal_name"]
    assert readback["legalImporterTaxCode"] == "0317000001"
    assert readback["subAgentId"] == "FIX-CONTRACT-B"
    assert readback["subAgentName"] == FIX_CONTRACT_B["legal_name"]
    assert readback["ready"] is True
    assert readback["missing"] == []

    fresh = vm.read_shipment(SHIPMENT_OK)
    assert fresh is not None
    assert int(fresh.get("version") or 0) > version_before
    assert fresh["data"]["0.0"]["commercial_flow"]["importer_company_id"] == "FIX-IMP-A"

    model = vm.build_view_model()
    row = _shipment_row(model, SHIPMENT_OK)
    assert row["commercialFlow"]["importerCompanyId"] == "FIX-IMP-A"
    assert row["commercialFlow"]["legalImporterName"] == FIX_IMPORTER_A["legal_name"]
    assert row["commercialFlow"]["legalImporterTaxCode"] == "0317000001"
    assert row["commercialFlow"]["subAgentName"] == FIX_CONTRACT_B["legal_name"]

    # The importer correction must not rewrite contract/payable identity.
    assert list(db["contracts"].find({}, {"_id": 0})) == contracts_before
    assert copy.deepcopy((fresh.get("data") or {}).get("3.4")) == finance_before


def test_writer_refuses_sub_with_only_the_agent_relation(staging, event_seq):
    before = vm.read_shipment(SHIPMENT_OK)
    version_before = int(before.get("version") or 0)

    refused = _dispatch(event_seq, "shipment_commercial_flow_save",
                        _flow_payload(SHIPMENT_OK, "FIX-FLOW-SUB-NOIMP", importerCompanyId=""))
    assert refused["ok"] is False
    assert refused["gate"] == "COMMERCIAL_FLOW_REFUSED"
    assert "pháp nhân thực tế đứng tên nhập khẩu" in refused["error"]
    assert int(vm.read_shipment(SHIPMENT_OK).get("version") or 0) == version_before


def test_writer_refuses_agent_id_or_unknown_company_as_importer(staging, event_seq):
    agent_as_company = _dispatch(
        event_seq, "shipment_commercial_flow_save",
        _flow_payload(SHIPMENT_OK, "FIX-FLOW-SUB-AGENT", importerCompanyId="FIX-CONTRACT-B"),
    )
    assert agent_as_company["ok"] is False
    assert agent_as_company["gate"] == "COMMERCIAL_FLOW_REFUSED"
    assert "Không tìm thấy pháp nhân" in agent_as_company["error"]

    missing_company = _dispatch(
        event_seq, "shipment_commercial_flow_save",
        _flow_payload(SHIPMENT_OK, "FIX-FLOW-SUB-GONE", importerCompanyId="FIX-DELETED"),
    )
    assert missing_company["ok"] is False
    assert missing_company["gate"] == "COMMERCIAL_FLOW_REFUSED"

    same_as_signing = _dispatch(
        event_seq, "shipment_commercial_flow_save",
        _flow_payload(SHIPMENT_OK, "FIX-FLOW-SUB-SAME", importerCompanyId="FIX-TT"),
    )
    assert same_as_signing["ok"] is False
    assert "phải khác pháp nhân Trường Thành" in same_as_signing["error"]


def test_legacy_sub_row_stays_unknown_and_cannot_generate_gnt(staging, event_seq):
    _save_gnt_facts(event_seq, SHIPMENT_LEGACY, FIX_CONTRACT_B["legal_code"])
    db = database.get_db()
    # The section key is the LITERAL string "0.0" (not nested paths), so this
    # legacy row is written with a direct document replace — bypassing only the
    # current validator, never production data.  No importer_company_id is
    # added: this is exactly the historical shape under test.
    legacy = db["shipments"].find_one({"id": SHIPMENT_LEGACY})
    assert legacy is not None
    legacy.setdefault("data", {}).setdefault("0.0", {})["commercial_flow"] = {
        "mode": "TT_ENTRUSTED_SUB",
        "confirmed": True,
        "company_id": "FIX-TT",
        "sub_agent_id": "FIX-CONTRACT-B",
    }
    db["shipments"].replace_one({"id": SHIPMENT_LEGACY}, legacy)

    model = vm.build_view_model()
    row = _shipment_row(model, SHIPMENT_LEGACY)
    flow = row["commercialFlow"]
    assert flow["confirmed"] is True
    assert flow["ready"] is False
    assert flow["legalImporterKind"] == ""
    assert flow["legalImporterId"] == ""
    assert flow["importerCompanyId"] == ""
    assert flow["legalImporterName"] == ""
    assert flow["legalImporterTaxCode"] == ""
    assert any("pháp nhân thực tế đứng tên nhập khẩu" in item for item in flow["missing"])
    # Historical agent relation is still visible, but only as a contract party.
    assert flow["subAgentName"] == FIX_CONTRACT_B["legal_name"]

    blocked = _dispatch(event_seq, "gnt_generate", {"shipmentId": SHIPMENT_LEGACY})
    assert blocked["ok"] is False
    assert blocked["gate"] == "LEGAL_IMPORTER_TAX_CODE_REQUIRED"
    assert blocked["legalImporterName"] == ""


def test_gnt_taxpayer_gate_uses_company_importer_tax_code(staging, event_seq):
    saved_flow = _dispatch(event_seq, "shipment_commercial_flow_save",
                           _flow_payload(SHIPMENT_GNT, "FIX-FLOW-SUB-GNT"))
    assert saved_flow["ok"], saved_flow.get("error")

    # The agent's MST is NOT the importer's MST: the gate must compare against
    # the company master's tax_or_legal_code.
    _save_gnt_facts(event_seq, SHIPMENT_GNT, FIX_CONTRACT_B["legal_code"])
    mismatch = _dispatch(event_seq, "gnt_generate", {"shipmentId": SHIPMENT_GNT})
    assert mismatch["ok"] is False
    assert mismatch["gate"] == "GNT_TAXPAYER_MISMATCH"
    assert mismatch["legalImporterName"] == FIX_IMPORTER_A["legal_name"]
    assert mismatch["legalImporterTaxCode"] == "0317000001"

    _save_gnt_facts(event_seq, SHIPMENT_GNT, FIX_IMPORTER_A["tax_or_legal_code"])
    matched = _dispatch(event_seq, "gnt_generate", {"shipmentId": SHIPMENT_GNT})
    assert matched["ok"] is True, matched.get("error")
    assert matched["gate"] == "READY"


def test_ui_and_bundle_separate_contract_agent_from_company_importer():
    src = Path("component/src/pages/ShipmentDetail.tsx").read_text(encoding="utf-8")
    assert 'data-testid="commercial-flow-contract-agent"' in src
    assert 'data-testid="commercial-flow-importer-company"' in src
    assert "importerCompanyId:" in src
    assert "flowImporterCompanyOptions" in src
    assert "authorityCompanies.filter" in src
    # The old label that called the agent the importer must be gone.
    assert 'label="Đơn vị đứng nhập khẩu hộ"' not in src

    dist = Path("component/dist/logi-shell.js").read_text(encoding="utf-8")
    assert "importerCompanyId" in dist
    assert "commercial-flow-importer-company" in dist
    assert "commercial-flow-contract-agent" in dist
