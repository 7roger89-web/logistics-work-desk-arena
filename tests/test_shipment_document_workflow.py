from core.shipment_document_workflow import (
    FLOW_CUSTOMER_SELF,
    FLOW_TT_ENTRUSTED_DIRECT,
    FLOW_TT_ENTRUSTED_SUB,
    STATE_BLOCKED,
    STATE_NOT_APPLICABLE,
    STATE_PENDING_DOCUMENT,
    STATE_READY,
    build_document_workflow,
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


def test_sub_entrust_requires_real_agent_master():
    document, errors = validate_flow_write(
        shipment=_shipment(),
        mode=FLOW_TT_ENTRUSTED_SUB,
        agents={},
        sub_agent_id="PA",
    )
    assert document is None
    assert errors

    document, errors = validate_flow_write(
        shipment=_shipment(),
        mode=FLOW_TT_ENTRUSTED_SUB,
        agents={
            "PA": {
                "agent_id": "PA",
                "legal_name": "Công ty Phú Anh",
                "tax_code": "0101234567",
            }
        },
        sub_agent_id="PA",
    )
    assert errors == []
    assert document == {
        "mode": FLOW_TT_ENTRUSTED_SUB,
        "confirmed": True,
        "company_id": "",
        "sub_agent_id": "PA",
    }


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


def test_project_flow_resolves_sub_agent_as_legal_importer():
    projected = project_commercial_flow(
        _shipment(
            flow={
                "mode": FLOW_TT_ENTRUSTED_SUB,
                "confirmed": True,
                "sub_agent_id": "PA",
            }
        ),
        agents={
            "PA": {
                "agent_id": "PA",
                "legal_name": "Công ty Phú Anh",
                "tax_code": "0101234567",
            }
        },
    )
    assert projected["ready"] is True
    assert projected["legalImporterKind"] == "AGENT"
    assert projected["legalImporterName"] == "Công ty Phú Anh"
    assert projected["legalImporterTaxCode"] == "0101234567"


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
    workflow = build_document_workflow(
        flow={"mode": FLOW_TT_ENTRUSTED_SUB, "confirmed": True},
        quote_linked=True,
        gnt={"ready": True},
        delivered=True,
        pxk={"gateOpen": True},
        finance={"outstanding": 100},
    )
    purchase = _step(workflow, "sub_entrust_contract")
    pxk = _step(workflow, "warehouse_issue")
    assert purchase["state"] == STATE_PENDING_DOCUMENT
    assert "50 triệu" in purchase["reason"]
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
