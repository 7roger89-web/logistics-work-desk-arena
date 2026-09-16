#!/usr/bin/env python3
"""Generate the LOGI_CONTRACT_AND_SHIPMENT_CORE_GAPS_01 DOM-acceptance fixture.

Same contract as ``scripts/gen_create_shipment_fixture.py``: boot the ISOLATED
mongomock staging transport (never production), run the writes through the
REAL bounded dispatcher so every state below is genuine backend readback, and
dump the resulting ``build_view_model()`` payloads.

Contract states (views /hop-dong/moi and /hop-dong/<id>):

  ``contractUnset``     — the seeded HDMB-0306: no buyer company chosen, no PL
                          answer, no contract date. The desk must render those
                          as "chưa chọn" and must NOT show "Không cần PL".
  ``contractEdited``    — after ONE ``contract_save`` that set the buyer
                          company, the signing date, the PL answer ("Có PL")
                          and the counterparty, all through
                          ``save_contract_to_cloud`` + audit + fresh read.
  ``contractPlNo``      — a second ``contract_save`` flipping only the PL
                          answer to "Không cần PL": proof the choice is
                          editable after create and preserved on readback.
  ``getflyOk``          — a pasted GetFly DSDH block handled by
                          ``customer_getfly_import``: the outcome (with the
                          operator's requestId) plus the fresh view-model that
                          really contains the new customer.
  ``getflyRefused``     — the fail-closed paste (no recognizable GetFly header)
                          with the backend's own message.

Shipment states (view /lo-hang/LO-0306):

  ``shipmentBefore``    — the seeded lot: creation date and An Phát JSC owner.
  ``shipmentDateSaved`` — after ``shipment_field_save {created_at}`` through
                          ``save_shipment_atomic`` + audit + fresh read.
  ``shipmentDateCleared`` — the same field saved BLANK: the readback must be
                          empty (UNKNOWN), never today and never 0.
  ``shipmentCustomerSaved`` — after ``shipment_customer_save`` through the
                          EXISTING ``core.database.update_shipment_customer``.
  ``shipmentViewerRefused`` — a VIEWER attempt at both writes, refused by RBAC
                          with the data genuinely unchanged: the DOM test asserts
                          the page never shows a locally invented success.

Run:  .venv/bin/python scripts/gen_contract_shipment_edit_fixture.py
Out:  tests/component/fixtures/view_model_contract_shipment_edit.json
"""
from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

OUT = ROOT / "tests" / "component" / "fixtures" / "view_model_contract_shipment_edit.json"

CONTRACT = "HDMB-0306"
SHIPMENT = "LO-0306"
BUYER = "TT-COMPANY"
NEW_CUSTOMER = "CUST-HNNEW"
NEW_CUSTOMER_NAME = "Hà Nội New Co"
OTHER_COMPANY = "TT-COMPANY-2"
OTHER_COMPANY_NAME = "CÔNG TY TNHH LOGISTICS PHÚ ANH"

#: Exactly what the operator copies out of the GetFly DSDH sheet: header + rows,
#: tab-separated, with one duplicated customer line and one line that has no
#: customer code (which must be reported as skipped, never invented).
GETFLY_TEXT = (
    "Mã ĐH\tNgày đặt hàng\tTên KH\tMã KH\tSố lượng\n"
    "DH-9001\t05/09/2026\tAn Phát JSC\tCUST-ANPHAT\t10\n"
    "DH-9001\t05/09/2026\tAn Phát JSC\tCUST-ANPHAT\t4\n"
    "DH-9002\t06/09/2026\tHà Nội New Co\tCUST-HNNEW\t2\n"
    "DH-9003\t07/09/2026\tKhách thiếu mã\t\t1\n"
)
GETFLY_BAD_TEXT = "cột không phải của GetFly\nabc\tdef"


def main() -> None:
    import streamlit as st

    from core.database import save_authority_company
    from views import logi_c1, logi_sandbox
    from views import logi_view_model as vm

    logi_sandbox.reset_backend()
    transport = logi_sandbox.ensure_backend()
    assert transport == logi_sandbox.SANDBOX_TRANSPORT, "fixture must not touch production"
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)
    st.session_state.pop(vm.LAST_WRITES_KEY, None)

    seq = {"n": 0}

    def dispatch(name: str, payload: dict) -> dict:
        """The REAL trigger path: Phase B and C1 lanes, one shared seq counter."""
        seq["n"] += 1
        result = {name: {"seq": seq["n"], "event": name, "payload": payload}}
        session = {"seq": 0}
        outcomes = vm.consume_phase_b_triggers(session, result)
        outcomes = outcomes + logi_c1.consume_c1_triggers(session, result)
        assert len(outcomes) == 1, (name, outcomes)
        return outcomes[0]

    def state(_name: str, outcomes: list[dict] | None = None) -> dict:
        st.session_state[vm.LAST_WRITES_KEY] = list(outcomes or [])
        return vm.build_view_model()

    # A second company master record so the buyer search has something to
    # filter — created through the canonical writer, never by hand.
    assert save_authority_company({
        "id": OTHER_COMPANY, "company_id": OTHER_COMPANY,
        "legal_name": OTHER_COMPANY_NAME, "tax_or_legal_code": "0311112222",
        "legal_address": "Số 8, Phố Núi, Hải Phòng",
        "legal_representative": "Trần Minh Anh", "representative_title": "Giám đốc",
    }), "the second company must be written through the canonical writer"

    # ------------------------------------------------------------- contracts --
    contract_unset = state("contractUnset")

    edit_out = dispatch("contract_save", {
        "id": CONTRACT,
        "company_id": BUYER,
        "date": "2026-09-05",
        "pl_required": "Có PL",
        "customerId": "CUST-MINHDUC",
    })
    assert edit_out["ok"], edit_out["error"]
    contract_edited = state("contractEdited", [edit_out])

    flip_out = dispatch("contract_save", {"id": CONTRACT, "pl_required": "Không cần PL"})
    assert flip_out["ok"], flip_out["error"]
    contract_pl_no = state("contractPlNo", [flip_out])

    getfly_out = dispatch("customer_getfly_import", {"text": GETFLY_TEXT, "requestId": "REQ-GF-OK"})
    assert getfly_out["ok"], getfly_out["error"]
    getfly_ok = state("getflyOk", [getfly_out])

    getfly_bad = dispatch("customer_getfly_import", {"text": GETFLY_BAD_TEXT, "requestId": "REQ-GF-BAD"})
    assert not getfly_bad["ok"]
    getfly_refused = state("getflyRefused", [getfly_bad])

    # ------------------------------------------------------------- shipment --
    shipment_before = state("shipmentBefore")

    date_out = dispatch("shipment_field_save",
                        {"shipmentId": SHIPMENT, "fields": {"created_at": "12/09/2026"}})
    assert date_out["ok"], date_out["error"]
    shipment_date_saved = state("shipmentDateSaved", [date_out])

    clear_out = dispatch("shipment_field_save",
                         {"shipmentId": SHIPMENT, "fields": {"created_at": ""}})
    assert clear_out["ok"], clear_out["error"]
    shipment_date_cleared = state("shipmentDateCleared", [clear_out])

    cust_out = dispatch("shipment_customer_save",
                        {"shipmentId": SHIPMENT, "customerId": "CUST-MINHDUC"})
    assert cust_out["ok"], cust_out["error"]
    shipment_customer_saved = state("shipmentCustomerSaved", [cust_out])

    # RBAC refusal: a VIEWER may change neither field, and the data must be
    # genuinely unchanged in the fresh read the page renders.
    st.session_state["current_user"] = {"username": "viewer.gap", "role": "VIEWER",
                                        "user_id": "U-VIEWER"}
    refused_date = dispatch("shipment_field_save",
                            {"shipmentId": SHIPMENT, "fields": {"created_at": "01/01/2020"}})
    refused_customer = dispatch("shipment_customer_save",
                                {"shipmentId": SHIPMENT, "customerId": "CUST-HONGHA"})
    assert not refused_date["ok"] and not refused_customer["ok"]
    shipment_viewer_refused = state("shipmentViewerRefused", [refused_date, refused_customer])
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)
    st.session_state.pop(vm.LAST_WRITES_KEY, None)

    payload = {
        "generatedFrom": "scripts/gen_contract_shipment_edit_fixture.py — isolated mongomock staging",
        "contract": CONTRACT,
        "shipment": SHIPMENT,
        "buyerCompany": BUYER,
        "buyerLegalName": "CÔNG TY TNHH GIAO NHẬN QUỐC TẾ TRƯỜNG THÀNH",
        "otherCompany": OTHER_COMPANY,
        "otherCompanyName": OTHER_COMPANY_NAME,
        "getflyText": GETFLY_TEXT,
        "getflyBadText": GETFLY_BAD_TEXT,
        "newCustomerId": NEW_CUSTOMER,
        "newCustomerName": NEW_CUSTOMER_NAME,
        "contractUnset": contract_unset,
        "contractEdited": contract_edited,
        "contractPlNo": contract_pl_no,
        "getflyOk": getfly_ok,
        "getflyRefused": getfly_refused,
        "shipmentBefore": shipment_before,
        "shipmentDateSaved": shipment_date_saved,
        "shipmentDateCleared": shipment_date_cleared,
        "shipmentCustomerSaved": shipment_customer_saved,
        "shipmentViewerRefused": shipment_viewer_refused,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1, default=str), encoding="utf-8")

    def contract_row(model: dict):
        return next((c for c in model["contracts"] if c["id"] == CONTRACT), {})

    def shipment_row(model: dict):
        return next((x for x in model["shipments"] if x["id"] == SHIPMENT), {})

    print(f"wrote {OUT.relative_to(ROOT)}")
    print(f"  contractUnset:     pl={contract_row(contract_unset).get('plRequired')!r} "
          f"company={contract_row(contract_unset).get('companyId')!r} "
          f"date={contract_row(contract_unset).get('contractDate')!r}")
    print(f"  contractEdited:    pl={contract_row(contract_edited).get('plRequired')!r} "
          f"company={contract_row(contract_edited).get('companyId')!r} "
          f"client={contract_row(contract_edited).get('client')!r} "
          f"date={contract_row(contract_edited).get('contractDate')!r}")
    print(f"  contractPlNo:      pl={contract_row(contract_pl_no).get('plRequired')!r}")
    print(f"  getflyOk:          customers={getfly_out.get('customers')} "
          f"skipped={getfly_out.get('skippedMissing')}")
    print(f"  getflyRefused:     {getfly_bad['error'][:60]}…")
    print(f"  shipmentBefore:    createdAt={shipment_row(shipment_before).get('createdAt')!r}")
    print(f"  shipmentDateSaved: createdAt={shipment_row(shipment_date_saved).get('createdAt')!r}")
    print(f"  shipmentDateCleared: createdAt={shipment_row(shipment_date_cleared).get('createdAt')!r}")
    print(f"  shipmentCustomerSaved: customer={shipment_row(shipment_customer_saved).get('customer')!r}")
    print(f"  shipmentViewerRefused: customer={shipment_row(shipment_viewer_refused).get('customer')!r} "
          f"lastWrites={[(w['event'], w['ok']) for w in shipment_viewer_refused['lastWrites']]}")

    logi_sandbox.reset_backend()


if __name__ == "__main__":
    main()
