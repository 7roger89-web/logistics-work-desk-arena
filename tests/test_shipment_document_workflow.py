from core.shipment_document_workflow import (
    FLOW_CUSTOMER_SELF,
    FLOW_TT_ENTRUSTED_DIRECT,
    FLOW_TT_ENTRUSTED_SUB,
    STATE_BLOCKED,
    STATE_NOT_APPLICABLE,
    STATE_PENDING_DOCUMENT,
    STATE_READY,
    build_document_workflow,
    gnt_flow_gate,
    match_sub_purchase_contract,
    pxk_flow_gate,
    project_commercial_flow,
    validate_flow_write,
)


def _shipment(customer_id="CUS-1", flow=None):
    head = {}
    if flow is not None:
        head["commercial_flow"] = flow
    return {
        "id": "SHIP-1",
        "customer_id": customer_id,
        "data": {"0.0": head},
    }


def _step(workflow, step_id):
    return next(row for row in workflow["steps"] if row["id"] == step_id)


def test_customer_self_requires_linked_customer_identity():
    document, errors = validate_flow_write(
        shipment=_shipment(customer_id=""),
        mode=FLOW_CUSTOMER_SELF,
    )
    assert document is None
    assert errors
    assert "mã khách hàng" in errors[0].lower()


FIXTURE_COMPANIES = {
    "TTL": {
        "company_id": "TTL",
        "legal_name": "CÔNG TY TNHH TRƯỜNG THÀNH (FIXTURE)",
        "tax_or_legal_code": "0109988776",
    },
    "IMP-A": {
        "company_id": "IMP-A",
        "legal_name": "CÔNG TY TNHH ĐỐI TÁC NHẬP KHẨU HỘ A (FIXTURE)",
        "tax_or_legal_code": "0317000001",
    },
}

FIXTURE_AGENTS = {
    "CONTRACT-B": {
        "agent_id": "CONTRACT-B",
        "legal_name": "CÔNG TY TNHH ĐẠI LÝ HỢP ĐỒNG B (FIXTURE)",
        "legal_code": "0317000002",
    },
}


def test_sub_entrust_requires_contract_agent_and_company_importer():
    document, errors = validate_flow_write(
        shipment=_shipment(),
        mode=FLOW_TT_ENTRUSTED_SUB,
        companies=FIXTURE_COMPANIES,
        agents=FIXTURE_AGENTS,
        sub_agent_id="CONTRACT-B",
    )
    assert document is None
    assert any("pháp nhân thực tế đứng tên nhập khẩu" in error for error in errors)

    document, errors = validate_flow_write(
        shipment=_shipment(),
        mode=FLOW_TT_ENTRUSTED_SUB,
        companies=FIXTURE_COMPANIES,
        agents={},
        company_id="TTL",
        sub_agent_id="CONTRACT-B",
        importer_company_id="IMP-A",
    )
    assert document is None
    assert errors

    document, errors = validate_flow_write(
        shipment=_shipment(),
        mode=FLOW_TT_ENTRUSTED_SUB,
        companies=FIXTURE_COMPANIES,
        agents=FIXTURE_AGENTS,
        company_id="TTL",
        sub_agent_id="CONTRACT-B",
        importer_company_id="IMP-A",
    )
    assert errors == []
    assert document == {
        "mode": FLOW_TT_ENTRUSTED_SUB,
        "confirmed": True,
        "company_id": "TTL",
        "sub_agent_id": "CONTRACT-B",
        "importer_company_id": "IMP-A",
    }


def test_sub_entrust_never_accepts_the_agent_id_as_the_importer_company():
    document, errors = validate_flow_write(
        shipment=_shipment(),
        mode=FLOW_TT_ENTRUSTED_SUB,
        companies=FIXTURE_COMPANIES,
        agents=FIXTURE_AGENTS,
        company_id="TTL",
        sub_agent_id="CONTRACT-B",
        importer_company_id="CONTRACT-B",
    )
    assert document is None
    assert any("Không tìm thấy pháp nhân" in error for error in errors)


def test_sub_entrust_rejects_the_signing_company_as_the_importer():
    document, errors = validate_flow_write(
        shipment=_shipment(),
        mode=FLOW_TT_ENTRUSTED_SUB,
        companies=FIXTURE_COMPANIES,
        agents=FIXTURE_AGENTS,
        company_id="TTL",
        sub_agent_id="CONTRACT-B",
        importer_company_id="TTL",
    )
    assert document is None
    assert any("phải khác pháp nhân Trường Thành" in error for error in errors)


def test_sub_entrust_rejects_unknown_importer_company():
    document, errors = validate_flow_write(
        shipment=_shipment(),
        mode=FLOW_TT_ENTRUSTED_SUB,
        companies=FIXTURE_COMPANIES,
        agents=FIXTURE_AGENTS,
        company_id="TTL",
        sub_agent_id="CONTRACT-B",
        importer_company_id="DELETED-COMPANY",
    )
    assert document is None
    assert any("Không tìm thấy pháp nhân" in error for error in errors)


def test_direct_entrust_may_use_single_authority_company_without_guessing_many():
    document, errors = validate_flow_write(
        shipment=_shipment(),
        mode=FLOW_TT_ENTRUSTED_DIRECT,
        companies={
            "TTL": {
                "company_id": "TTL",
                "legal_name": "CÔNG TY TNHH GIAO NHẬN QUỐC TẾ TRƯỜNG THÀNH",
            }
        },
    )
    assert errors == []
    assert document["company_id"] == "TTL"

    document, errors = validate_flow_write(
        shipment=_shipment(),
        mode=FLOW_TT_ENTRUSTED_DIRECT,
        companies={
            "A": {"company_id": "A"},
            "B": {"company_id": "B"},
        },
    )
    assert document is None
    assert errors


def test_project_flow_resolves_sub_company_importer_not_the_contract_agent():
    projected = project_commercial_flow(
        _shipment(
            flow={
                "mode": FLOW_TT_ENTRUSTED_SUB,
                "confirmed": True,
                "company_id": "TTL",
                "sub_agent_id": "CONTRACT-B",
                "importer_company_id": "IMP-A",
            }
        ),
        companies=FIXTURE_COMPANIES,
        agents=FIXTURE_AGENTS,
    )
    assert projected["ready"] is True
    assert projected["legalImporterKind"] == "COMPANY"
    assert projected["legalImporterId"] == "IMP-A"
    assert projected["importerCompanyId"] == "IMP-A"
    assert projected["legalImporterName"] == FIXTURE_COMPANIES["IMP-A"]["legal_name"]
    assert projected["legalImporterTaxCode"] == "0317000001"
    # The contract relation is untouched and clearly separate from the importer.
    assert projected["subAgentId"] == "CONTRACT-B"
    assert projected["subAgentName"] == FIXTURE_AGENTS["CONTRACT-B"]["legal_name"]


def test_project_flow_legacy_sub_without_company_link_stays_unknown():
    projected = project_commercial_flow(
        _shipment(
            flow={
                "mode": FLOW_TT_ENTRUSTED_SUB,
                "confirmed": True,
                "company_id": "TTL",
                "sub_agent_id": "CONTRACT-B",
            }
        ),
        companies=FIXTURE_COMPANIES,
        agents=FIXTURE_AGENTS,
    )
    assert projected["ready"] is False
    assert projected["legalImporterKind"] == ""
    assert projected["legalImporterId"] == ""
    assert projected["importerCompanyId"] == ""
    assert projected["legalImporterName"] == ""
    assert projected["legalImporterTaxCode"] == ""
    assert any("pháp nhân thực tế đứng tên nhập khẩu" in item for item in projected["missing"])
    # Historical data remains visible for reconciliation but is never
    # promoted into a legal identity.
    assert projected["subAgentName"] == FIXTURE_AGENTS["CONTRACT-B"]["legal_name"]


def test_project_flow_fails_closed_for_stale_company_and_signing_company_importer():
    stale = project_commercial_flow(
        _shipment(
            flow={
                "mode": FLOW_TT_ENTRUSTED_SUB,
                "confirmed": True,
                "company_id": "TTL",
                "sub_agent_id": "CONTRACT-B",
                "importer_company_id": "DELETED-COMPANY",
            }
        ),
        companies=FIXTURE_COMPANIES,
        agents=FIXTURE_AGENTS,
    )
    assert stale["ready"] is False
    assert stale["legalImporterId"] == ""
    assert stale["legalImporterName"] == ""

    same_as_signing = project_commercial_flow(
        _shipment(
            flow={
                "mode": FLOW_TT_ENTRUSTED_SUB,
                "confirmed": True,
                "company_id": "TTL",
                "sub_agent_id": "CONTRACT-B",
                "importer_company_id": "TTL",
            }
        ),
        companies=FIXTURE_COMPANIES,
        agents=FIXTURE_AGENTS,
    )
    assert same_as_signing["ready"] is False
    assert same_as_signing["legalImporterId"] == ""
    assert any("phải khác pháp nhân Trường Thành" in item for item in same_as_signing["missing"])


def test_gnt_gate_compares_the_real_company_importer_tax_code():
    projected = project_commercial_flow(
        _shipment(
            flow={
                "mode": FLOW_TT_ENTRUSTED_SUB,
                "confirmed": True,
                "company_id": "TTL",
                "sub_agent_id": "CONTRACT-B",
                "importer_company_id": "IMP-A",
            }
        ),
        companies=FIXTURE_COMPANIES,
        agents=FIXTURE_AGENTS,
    )
    assert gnt_flow_gate(projected, "0317000001")["allowed"] is True
    mismatch = gnt_flow_gate(projected, FIXTURE_AGENTS["CONTRACT-B"]["legal_code"])
    assert mismatch["allowed"] is False
    assert mismatch["gate"] == "GNT_TAXPAYER_MISMATCH"


def test_importer_change_does_not_move_the_contract_partner_match():
    flow = project_commercial_flow(
        _shipment(
            flow={
                "mode": FLOW_TT_ENTRUSTED_SUB,
                "confirmed": True,
                "company_id": "TTL",
                "sub_agent_id": "CONTRACT-B",
                "importer_company_id": "IMP-A",
            }
        ),
        companies=FIXTURE_COMPANIES,
        agents=FIXTURE_AGENTS,
    )
    contracts = {
        "C-1": {"id": "C-1", "contract_no": "FIX-01/2026", "company_id": "TTL", "agent_id": "CONTRACT-B"},
    }
    before = match_sub_purchase_contract(flow, contracts)
    other_importer = project_commercial_flow(
        _shipment(
            flow={
                "mode": FLOW_TT_ENTRUSTED_SUB,
                "confirmed": True,
                "company_id": "TTL",
                "sub_agent_id": "CONTRACT-B",
                "importer_company_id": "IMP-C",
            }
        ),
        companies={**FIXTURE_COMPANIES, "IMP-C": {
            "company_id": "IMP-C",
            "legal_name": "CÔNG TY TNHH ĐỐI TÁC NHẬP KHẨU HỘ C (FIXTURE)",
            "tax_or_legal_code": "0317000003",
        }},
        agents=FIXTURE_AGENTS,
    )
    after = match_sub_purchase_contract(other_importer, contracts)
    assert before == after
    assert after["status"] == "LINKED"
    assert after["id"] == "C-1"
    assert other_importer["legalImporterId"] == "IMP-C"
    assert other_importer["subAgentId"] == "CONTRACT-B"


def test_customer_self_makes_truong_thanh_pxk_not_applicable():
    workflow = build_document_workflow(
        flow={"mode": FLOW_CUSTOMER_SELF, "confirmed": True},
        quote_linked=True,
        gnt={"ready": True},
        delivered=True,
        pxk={"gateOpen": True},
        finance={"outstanding": 100},
    )
    pxk = _step(workflow, "warehouse_issue")
    assert pxk["state"] == STATE_NOT_APPLICABLE
    assert "khách hàng tự đứng tên" in pxk["reason"].lower()


def test_sub_entrust_requires_purchase_contract_and_can_make_pxk_ready():
    flow = {
        "mode": FLOW_TT_ENTRUSTED_SUB,
        "confirmed": True,
        "companyId": "TTL",
        "subAgentId": "PA",
    }
    purchase_match = match_sub_purchase_contract(
        flow,
        {"C-PA": {"id": "C-PA", "contract_no": "01/2026", "company_id": "TTL", "agent_id": "PA"}},
    )
    workflow = build_document_workflow(
        flow=flow,
        quote_linked=True,
        gnt={"ready": True},
        delivered=True,
        pxk={"gateOpen": True},
        finance={"outstanding": 100},
        sub_purchase_contract=purchase_match,
    )
    purchase = _step(workflow, "sub_entrust_contract")
    pxk = _step(workflow, "warehouse_issue")
    assert purchase_match["status"] == "LINKED"
    assert purchase["state"] == STATE_READY
    assert "01/2026" in purchase["reason"]
    assert purchase["targetRoute"] == "/hop-dong/C-PA"
    assert pxk["state"] == STATE_READY


def test_unconfirmed_flow_blocks_conditional_document_set():
    workflow = build_document_workflow(
        flow={"mode": "", "confirmed": False},
        quote_linked=False,
        gnt={},
        delivered=False,
        pxk={},
        finance={},
    )
    assert _step(workflow, "customer_contract")["state"] == STATE_BLOCKED
    assert _step(workflow, "tax_payment")["state"] == STATE_BLOCKED


def test_shared_pxk_gate_blocks_unknown_and_customer_self():
    unknown = pxk_flow_gate({"mode": "", "confirmed": False})
    assert unknown["allowed"] is False
    assert unknown["gate"] == "COMMERCIAL_FLOW_REQUIRED"

    customer_self = pxk_flow_gate({"mode": FLOW_CUSTOMER_SELF, "confirmed": True})
    assert customer_self["allowed"] is False
    assert customer_self["gate"] == "PXK_NOT_APPLICABLE"

    entrusted = pxk_flow_gate({"mode": FLOW_TT_ENTRUSTED_DIRECT, "confirmed": True})
    assert entrusted["allowed"] is True


def test_gnt_gate_requires_confirmed_importer_tax_identity_and_rejects_mismatch():
    unknown = gnt_flow_gate({"mode": "", "confirmed": False}, "0101")
    assert unknown["gate"] == "COMMERCIAL_FLOW_REQUIRED"

    missing_master_tax = gnt_flow_gate(
        {"mode": FLOW_TT_ENTRUSTED_SUB, "confirmed": True, "legalImporterTaxCode": ""},
        "0101",
    )
    assert missing_master_tax["gate"] == "LEGAL_IMPORTER_TAX_CODE_REQUIRED"

    mismatch = gnt_flow_gate(
        {"mode": FLOW_TT_ENTRUSTED_SUB, "confirmed": True, "legalImporterTaxCode": "0101"},
        "0202",
    )
    assert mismatch["allowed"] is False
    assert mismatch["gate"] == "GNT_TAXPAYER_MISMATCH"

    match = gnt_flow_gate(
        {"mode": FLOW_TT_ENTRUSTED_SUB, "confirmed": True, "legalImporterTaxCode": "0101"},
        "0101",
    )
    assert match["allowed"] is True


def test_customer_self_with_historical_pxk_keeps_conflict_visible():
    workflow = build_document_workflow(
        flow={"mode": FLOW_CUSTOMER_SELF, "confirmed": True},
        quote_linked=True,
        gnt={"ready": True, "taxCode": "0101"},
        delivered=True,
        pxk={"done": True, "document": {"fileName": "PXK-old.xlsx"}},
        finance={"outstanding": 0},
    )
    pxk = _step(workflow, "warehouse_issue")
    assert pxk["state"] == STATE_BLOCKED
    assert "lịch sử" in pxk["reason"].lower()


def test_sub_purchase_contract_match_is_fail_closed_on_multiple_matches():
    flow = {
        "mode": FLOW_TT_ENTRUSTED_SUB,
        "confirmed": True,
        "companyId": "TTL",
        "subAgentId": "PA",
    }
    matched = match_sub_purchase_contract(
        flow,
        {
            "C1": {"id": "C1", "company_id": "TTL", "agent_id": "PA"},
            "C2": {"id": "C2", "company_id": "TTL", "agent_id": "PA"},
            "OTHER": {"id": "OTHER", "company_id": "TTL", "agent_id": "OTHER"},
        },
    )
    assert matched["status"] == "AMBIGUOUS"
    workflow = build_document_workflow(
        flow=flow,
        quote_linked=True,
        gnt={"ready": True},
        delivered=False,
        pxk={},
        finance={},
        sub_purchase_contract=matched,
    )
    purchase = _step(workflow, "sub_entrust_contract")
    assert purchase["state"] == STATE_BLOCKED
    assert "2 hợp đồng" in purchase["reason"]


def test_project_flow_reads_authority_company_mst_field_for_direct_company():
    # Company authority masters carry MST in ``tax_or_legal_code`` (the field
    # every company form/writer/docgen rule uses in this repo) — NOT
    # ``legal_code``.  A representative master row must resolve the importer.
    projected = project_commercial_flow(
        _shipment(
            flow={
                "mode": FLOW_TT_ENTRUSTED_DIRECT,
                "confirmed": True,
                "company_id": "TTL",
            }
        ),
        companies={
            "TTL": {
                "company_id": "TTL",
                "legal_name": "CÔNG TY TNHH GIAO NHẬN QUỐC TẾ TRƯỜNG THÀNH",
                "tax_or_legal_code": "0109988776",
            }
        },
    )
    assert projected["ready"] is True
    assert projected["legalImporterKind"] == "COMPANY"
    assert projected["legalImporterTaxCode"] == "0109988776"


def test_customer_contract_does_not_masquerade_as_agent_company_docgen():
    workflow = build_document_workflow(
        flow={"mode": FLOW_CUSTOMER_SELF, "confirmed": True},
        quote_linked=True,
        gnt={"ready": False, "missing": ["Mã số thuế"]},
        delivered=False,
        pxk={},
        finance={},
    )
    customer_contract = _step(workflow, "customer_contract")
    assert customer_contract["state"] == STATE_PENDING_DOCUMENT
    assert customer_contract["targetRoute"] == ""
    assert "không dùng nhầm docgen" in customer_contract["reason"].lower()
