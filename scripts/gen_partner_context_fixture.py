#!/usr/bin/env python3
"""Generate the LOGI_PARTNER_CONTEXT_WORKSPACE_01 DOM-acceptance fixture.

Same contract as gen_c2d_fixture.py: boot the ISOLATED mongomock staging
transport (never production) and dump the real ``build_view_model()`` payload
verbatim, so the React bundle is driven by genuine backend truth rather than a
hand-written mock. This generator produces three states:

  1. ``empty``          — before any canonical payable exists: the picker has a
                          real partner (the authority_agents master record) but
                          NO finance row at all (UNKNOWN != ZERO proof),
  2. ``journey``        — after ONE partner obligation + ONE payment are recorded
                          through the SAME canonical C2B handlers the UI drives,
                          with ``AGT-PHUANH`` selected through the bounded
                          read-only dispatcher: real linked shipment + real
                          payable/paid/remaining per currency,
  3. ``unknownPartner`` — the same selection path for a partner key that does
                          not exist: the honest ``PARTNER_NOT_FOUND`` state.

LOGI_REAL_USE_CREATE_SHIPMENT_AGENT_MASTER_01 additionally generates the
agent-master management states (same contract: every write goes through the
SAME bounded dispatchers the UI drives, and the outcomes are stored under
``st.session_state["logi_last_writes"]`` exactly like views.logi_view_model.
dispatch() does, so ``lastWrites`` in each payload is the real readback):

  4. ``agentEditOk``    — AGT-PHUANH edited through authority_agent_save
                          (existing canonical writer) while selected: the
                          fresh view-model shows the updated master,
  5. ``agentCreateOk``  — a NEW agent master saved and auto-selected through
                          the same read-only selection event the picker uses,
  6. ``agentSaveError`` — a VIEWER attempt refused by RBAC: the ok=False
                          outcome the form must display (nothing persisted).

Run:  python scripts/gen_partner_context_fixture.py
Out:  tests/component/fixtures/view_model_partner_context.json
"""
from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

SHIPMENT = "LO-0308"
PARTNER = "AGT-PHUANH"
OUT = ROOT / "tests" / "component" / "fixtures" / "view_model_partner_context.json"


def main() -> None:
    import streamlit as st

    from views import logi_sandbox
    from views import logi_view_model as vm

    logi_sandbox.reset_backend()
    transport = logi_sandbox.ensure_backend()
    assert transport == logi_sandbox.SANDBOX_TRANSPORT, "this fixture must not touch production"
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)
    st.session_state.pop(vm.PARTNER_CONTEXT_KEY, None)

    # UNKNOWN != ZERO: a real partner exists, yet no payable is reported as 0.
    empty = vm.build_view_model()

    # Same partner, selected, BEFORE any canonical obligation exists: the finance
    # panel must say "chưa xác định", never 0.
    st.session_state[vm.PARTNER_CONTEXT_KEY] = PARTNER
    no_finance = vm.build_view_model()
    st.session_state.pop(vm.PARTNER_CONTEXT_KEY, None)

    seq = {"n": 0}

    def dispatch(name: str, payload: dict) -> list:
        seq["n"] += 1
        return vm.consume_phase_b_triggers(
            {"seq": 0}, {name: {"seq": seq["n"], "event": name, "payload": payload}}
        )

    def dispatch_c1(name: str, payload: dict) -> list:
        from views import logi_c1

        seq["n"] += 1
        return logi_c1.consume_c1_triggers(
            {"seq": 0}, {name: {"seq": seq["n"], "event": name, "payload": payload}}
        )

    obl = dispatch("partner_payable_record", {
        "shipmentId": SHIPMENT, "partnerId": PARTNER, "requestId": "PCX-FIX-OBL-1",
        "amount": 57_000_000, "currency": "VND",
        "note": "Phải trả chi phí đối tác theo thực tế lô",
    })[0]
    assert obl["ok"], obl["error"]
    pay = dispatch("partner_payment_record", {
        "shipmentId": SHIPMENT, "partnerId": PARTNER, "requestId": "PCX-FIX-PAY-1",
        "amount": 20_000_000, "currency": "VND", "date": "2026-09-10",
        "note": "Chuyển khoản thanh toán đối tác",
    })[0]
    assert pay["ok"], pay["error"]
    # Mirror what views.logi_view_model.dispatch() persists so the NEXT fresh
    # view-model embeds the authoritative outcomes (lastWrites).
    st.session_state[vm.LAST_WRITES_KEY] = [obl, pay]

    def select(key: str) -> None:
        # The selection goes through the SAME bounded read-only dispatcher the
        # UI uses, so the fixture carries exactly what a live click delivers.
        chosen = vm.consume_partner_context_triggers({"seq": 0}, {"partner_context_select": {
            "seq": 900, "event": "partner_context_select", "payload": {"entityKey": key},
        }})
        assert chosen[0]["ok"], chosen[0]["error"]

    select(f"  {PARTNER}  ")
    journey = vm.build_view_model()

    st.session_state[vm.PARTNER_CONTEXT_KEY] = "AGT-KHONG-TON-TAI"
    missing = vm.build_view_model()
    st.session_state.pop(vm.PARTNER_CONTEXT_KEY, None)

    # -------------------------------------------------------------------
    # LOGI_REAL_USE_CREATE_SHIPMENT_AGENT_MASTER_01 — agent master states
    # -------------------------------------------------------------------

    # 4. agentEditOk — the seeded AGT-PHUANH master edited while selected,
    #    through the EXISTING canonical writer (upsert + audit).
    edit_out = dispatch_c1("authority_agent_save", {
        "agentId": PARTNER, "legalName": "CÔNG TY TNHH PHÚ ANH LOGISTICS",
        "legalCode": "0315678910",
        "legalAddress": "Số 45, Nguyễn Văn Linh, Quận 7, TP. Hồ Chí Minh",
        "legalRepresentative": "Phạm Văn Thành", "representativeTitle": "Giám đốc",
        "phone": "0289999888", "email": "sales@phuanh.vn",
        "bankAccountHolder": "PHÚ ANH LOGISTICS", "bankAccountNumber": "9876543210",
        "bankName": "Techcombank", "bankBranch": "Hội sở TP.HCM",
        "requestId": "PCX-FIX-AGENT-EDIT-1",
    })[0]
    assert edit_out["ok"], edit_out["error"]
    st.session_state[vm.LAST_WRITES_KEY] = [edit_out]
    select(PARTNER)
    agent_edit_ok = vm.build_view_model()

    # 5. agentCreateOk — a NEW agent master saved and auto-selected exactly the
    #    way the UI does right after a successful create.
    create_out = dispatch_c1("authority_agent_save", {
        "agentId": "AGT-MINHPHAT",
        "legalName": "CÔNG TY TNHH ĐẠI LÝ MINH PHÁT",
        "legalCode": "0101234567", "legalAddress": "Số 1, Đường Test, Hà Nội",
        "legalRepresentative": "Nguyễn Minh Phát", "representativeTitle": "Giám đốc",
        "phone": "0912000111", "email": "phat@minhphat.vn",
        "bankAccountHolder": "ĐẠI LÝ MINH PHÁT", "bankAccountNumber": "1111222233",
        "bankName": "Vietcombank", "bankBranch": "CN Hà Nội",
        "requestId": "PCX-FIX-AGENT-NEW-1",
    })[0]
    assert create_out["ok"], create_out["error"]
    st.session_state[vm.LAST_WRITES_KEY] = [create_out]
    select("AGT-MINHPHAT")
    agent_create_ok = vm.build_view_model()

    # 6. agentSaveError — a VIEWER attempt refused by RBAC (nothing persisted):
    #    the ok=False outcome the form must display verbatim.
    st.session_state["current_user"] = {"username": "viewer.user", "role": "VIEWER",
                                        "user_id": "U-VIEWER"}
    err_out = dispatch_c1("authority_agent_save", {
        "agentId": "AGT-TRAITUYEN", "legalName": "CÔNG TY TRÁI TUYẾN",
        "requestId": "PCX-FIX-AGENT-ERR-1",
    })[0]
    assert not err_out["ok"] and "RBAC" in err_out["error"], err_out
    st.session_state[vm.LAST_WRITES_KEY] = [err_out]
    st.session_state.pop(vm.PARTNER_CONTEXT_KEY, None)
    agent_save_error = vm.build_view_model()
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)
    st.session_state.pop(vm.PARTNER_CONTEXT_KEY, None)
    st.session_state.pop(vm.LAST_WRITES_KEY, None)

    payload = {
        "generatedFrom": "scripts/gen_partner_context_fixture.py — isolated mongomock staging",
        "shipment": SHIPMENT,
        "partner": PARTNER,
        "journey": journey,
        "empty": empty,
        "noFinance": no_finance,
        "unknownPartner": missing,
        "agentEditOk": agent_edit_ok,
        "agentCreateOk": agent_create_ok,
        "agentSaveError": agent_save_error,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1, default=str), encoding="utf-8")

    view = journey["partnerContext"]
    print(f"wrote {OUT.relative_to(ROOT)}")
    print(f"  status={view['status']} options={view['optionCount']} "
          f"linked={view['shipmentCount']} canOpen={[r['canOpen'] for r in view['shipments']]}")
    for row in view["finance"]["rows"]:
        print(f"    {row['shipmentId']} {row['currency']} payable={row['payable']} "
              f"paid={row['paid']} remaining={row['remaining']} status={row['status']}")
    print(f"  empty: status={empty['partnerContext']['status']} "
          f"financeRows={len(empty['partnerContext'].get('finance', {}).get('rows', []))} "
          f"payables={len(empty['payables']['rows'])}")
    nf = no_finance["partnerContext"]
    print(f"  noFinance: status={nf['status']} financeRows={len(nf['finance']['rows'])} "
          f"financeStatus={nf['finance']['status']} gaps={len(nf['gaps'])}")
    print(f"  unknown: status={missing['partnerContext']['status']}")
    ae = agent_edit_ok["partnerContext"]
    print(f"  agentEditOk: selected={ae['selectedKey']} "
          f"phone={(ae.get('identity') or {}).get('party', {}).get('phone')} "
          f"lastWrites={[w.get('requestId') for w in agent_edit_ok.get('lastWrites', [])]}")
    ac = agent_create_ok["partnerContext"]
    print(f"  agentCreateOk: selected={ac['selectedKey']} "
          f"options={ac['optionCount']} master={[o['key'] for o in ac['options'] if o['master']]} "
          f"lastWrites={[w.get('requestId') for w in agent_create_ok.get('lastWrites', [])]}")
    print(f"  agentSaveError: lastWrites="
          f"{[(w.get('ok'), w.get('requestId')) for w in agent_save_error.get('lastWrites', [])]}")


if __name__ == "__main__":
    main()
