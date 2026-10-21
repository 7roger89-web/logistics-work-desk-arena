"""LOGI-GOOD-V6 Phase B — real Logistics backend in the frozen Logi-good shell.

Focused acceptance evidence for the Phase B write contract:

    frontend typed event → bounded dispatcher → current RBAC
      → existing writer/service → audit → fresh backend read

Every write assertion re-reads the shipment from the database
(``views.logi_view_model.read_shipment``), never from frontend state.

Transport: an isolated staging database (mongomock) running the CURRENT
canonical writers unchanged. The production database is never touched.
"""

from __future__ import annotations

import io
import zipfile

import pytest

from views import logi_real_data as rd
from views import logi_sandbox
from views import logi_view_model as vm


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def staging():
    """A clean isolated staging database + a deterministic staging actor."""
    import streamlit as st

    logi_sandbox.reset_backend()
    transport = logi_sandbox.ensure_backend()
    assert transport == logi_sandbox.SANDBOX_TRANSPORT
    # Deterministic identity for the write tests; RBAC tests swap it out and
    # this fixture restores it around every test.
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
    outcomes = vm.consume_phase_b_triggers({"seq": 0}, seq_fn(name, payload))
    assert len(outcomes) == 1
    return outcomes[0]


# ---------------------------------------------------------------------------
# Transport / plumbing
# ---------------------------------------------------------------------------

def test_sandbox_transport_is_isolated_and_not_production(staging):
    """Production DB is never used: staging identity + staging DB name."""
    from core import config as core_config

    assert staging == logi_sandbox.SANDBOX_TRANSPORT
    assert core_config.MONGO_DB_NAME == logi_sandbox.STAGING_DB_NAME
    assert core_config.MONGO_DB_NAME not in {"logistics_db"}
    assert core_config.ENV_IDENTITY in {"STAGING", "PREVIEW"}


def test_sandbox_session_shim_is_falsy_noop():
    """The shim grants nothing: it is falsy, so writers' sessions stay inert."""
    session = logi_sandbox._SandboxSession()
    assert bool(session) is False
    with logi_sandbox._SandboxSession() as outer:
        with outer.start_transaction() as txn:
            assert bool(txn) is False


def test_staging_seed_written_through_canonical_writer(staging):
    """The seed itself went through save_shipment_atomic, so audit is real."""
    from core.database import load_audit_logs, load_data

    data = load_data()
    assert {"LO-0295", "LO-0299", "LO-0306", "LO-0307", "LO-0308"} <= set(data)
    for sid in ("LO-0306", "LO-0295"):
        actions = [row.get("action") for row in load_audit_logs("shipment", sid, limit=10)]
        assert "create" in actions


# ---------------------------------------------------------------------------
# Write / fresh readback
# ---------------------------------------------------------------------------

def test_pickup_save_readback(staging, event_seq):
    """PICKUP_SAVE_READBACK — tab 1 pickup/export fields persist."""
    out = _dispatch(event_seq, "shipment_field_save", {
        "shipmentId": "LO-0307",
        "fields": {"pol": "Nam Ninh (Quảng Tây)", "etd": "08/09/2026",
                   "booking_no": "BKG-0307-PB"},
    })
    assert out["ok"], out["error"]
    fresh = vm.read_shipment("LO-0307")
    assert fresh["data"]["1.2"]["pol"] == "Nam Ninh (Quảng Tây)"
    assert fresh["data"]["1.2"]["booking_no"] == "BKG-0307-PB"
    # The dispatcher's own readback agrees with an independent fresh read.
    assert out["readback"]["transport"]["bookingNo"] == "BKG-0307-PB"
    assert out["version"] >= 1


def test_cn_truck_save_readback(staging, event_seq):
    """CN_TRUCK_SAVE_READBACK — CN truck/vehicle identity persists."""
    out = _dispatch(event_seq, "shipment_field_save", {
        "shipmentId": "LO-0307",
        "fields": {"container_no": "桂A·55B99", "carrier": "Bộ (đường bộ TQ–VN)"},
    })
    assert out["ok"], out["error"]
    fresh = vm.read_shipment("LO-0307")
    assert fresh["data"]["1.2"]["container_no"] == "桂A·55B99"
    assert out["readback"]["pickup"]["plate"] == "桂A·55B99"


def test_import_save_readback(staging, event_seq):
    """IMPORT_SAVE_READBACK — declaration, channel, customs flag persist."""
    out = _dispatch(event_seq, "shipment_field_save", {
        "shipmentId": "LO-0306",
        "fields": {"tk_no": "105588421330", "phan_luong": "Xanh",
                   "customs_status": True, "arrival_date": "08/09/2026",
                   "free_time": "14"},
    })
    assert out["ok"], out["error"]
    fresh = vm.read_shipment("LO-0306")
    assert fresh["data"]["2.4"]["tk_no"] == "105588421330"
    assert fresh["data"]["2.4"]["phan_luong"] == "Xanh"
    assert fresh["data"]["2.4"]["customs_status"] is True
    assert fresh["data"]["2.6"]["arrival_date"] == "2026-09-08"
    assert fresh["data"]["2.6"]["free_time"] == 14.0
    # Stage advances from real facts once the declaration exists.
    assert out["readback"]["importInfo"]["declarationNo"] == "105588421330"
    assert out["readback"]["status"] in {"Chờ thông quan", "Chờ giao"}


def test_vn_truck_save_readback(staging, event_seq):
    """VN_TRUCK_SAVE_READBACK — VN delivery vehicle + driver persist."""
    out = _dispatch(event_seq, "shipment_field_save", {
        "shipmentId": "LO-0306",
        "fields": {"truck_no": "29H-481.36", "seal_no": "Hùng Văn Bắc / 0912000111"},
    })
    assert out["ok"], out["error"]
    fresh = vm.read_shipment("LO-0306")
    assert fresh["data"]["2.7"]["truck_no"] == "29H-481.36"
    assert out["readback"]["importInfo"]["plateVN"] == "29H-481.36"
    assert "Hùng Văn Bắc" in out["readback"]["importInfo"]["driverVN"]


def test_goods_and_finance_actual_save_readback(staging, event_seq):
    """GOODS_SAVE_READBACK / FINANCE_ACTUAL_SAVE_READBACK.

    Finance Actual is a real service line in ``data.3.4.details``; the
    canonical snapshot (receivable/cost) is recomputed by core.logic.
    """
    before = vm.read_shipment("LO-0308")
    lines_before = len(before["data"]["3.4"]["details"])

    out = _dispatch(event_seq, "finance_actual_save", {
        "shipmentId": "LO-0308",
        "line": {"name": "Phí nâng hạ container", "qty": 2, "price": 1500000,
                 "cost": 1100000, "vat": 8, "unit": "Lần"},
    })
    assert out["ok"], out["error"]

    fresh = vm.read_shipment("LO-0308")
    details = fresh["data"]["3.4"]["details"]
    assert len(details) == lines_before + 1
    saved = next(d for d in details if d["id"] == out["lineId"])
    assert saved["name_full"] == "Phí nâng hạ container"
    assert saved["qty"] == 2.0
    assert saved["price"] == 1500000.0
    assert saved["cost"] == 1100000.0
    assert saved["vat_line"] == 8.0
    # core.logic snapshot recomputed on write.
    assert fresh["data"]["3.4"]["out"] == out["persisted"]["receivable"]
    assert fresh["data"]["3.4"]["in"] == out["persisted"]["cost"]
    assert out["persisted"]["receivable"] > 0


def test_finance_actual_blank_amount_is_refused_on_the_write_path(staging, event_seq):
    """UNKNOWN != ZERO (LOGI_FINANCE_ACTUAL_ENTRY_PARITY_01) on the writer.

    A blank price/cost on a booked actual line is REFUSED with an explicit
    Vietnamese message instead of being normalised into a business ``0``.
    """
    lines_before = len(vm.read_shipment("LO-0308")["data"]["3.4"]["details"])

    out = _dispatch(event_seq, "finance_actual_save", {
        "shipmentId": "LO-0308",
        "line": {"name": "Chi phí chờ xác nhận", "qty": 1, "price": "", "cost": ""},
    })
    assert out["ok"] is False
    assert "Chưa nhập" in out["error"]
    assert len(vm.read_shipment("LO-0308")["data"]["3.4"]["details"]) == lines_before


def test_delivery_save_readback(staging, event_seq):
    """DELIVERY_SAVE_READBACK — ✅ XÁC NHẬN ĐÃ GIAO HÀNG persists + audits."""
    out = _dispatch(event_seq, "delivery_confirm", {
        "shipmentId": "LO-0299", "deliveredAt": "10/09/2026",
        "receiverName": "A. Nam", "receiverTitle": "Thủ kho",
    })
    assert out["ok"], out["error"]
    fresh = vm.read_shipment("LO-0299")
    assert fresh["data"]["2.7"]["is_delivered"] is True
    assert fresh["data"]["2.7"]["delivered_at"] == "2026-09-10"
    assert fresh["data"]["2.7"]["receiver_name"] == "A. Nam"
    assert fresh["status"] == "done"
    assert out["readback"]["status"] == "Đã giao"
    assert out["readback"]["importInfo"]["delivered"] is True


def test_delivery_confirm_is_idempotent(staging, event_seq):
    """Confirming twice does not create a second delivery event."""
    first = _dispatch(event_seq, "delivery_confirm", {"shipmentId": "LO-0299", "deliveredAt": "2026-09-10"})
    second = _dispatch(event_seq, "delivery_confirm", {"shipmentId": "LO-0299", "deliveredAt": "2026-09-10"})
    assert first["ok"] and second["ok"]
    assert second.get("alreadyConfirmed") is True
    assert vm.read_shipment("LO-0299")["data"]["2.7"]["delivered_at"] == "2026-09-10"


def test_payment_save_readback(staging, event_seq):
    """PAYMENT_SAVE_READBACK — real payment via the canonical writer."""
    out = _dispatch(event_seq, "payment_record", {
        "shipmentId": "LO-0307", "amount": 25000000, "requestId": "REQ-PB-0307-A",
        "date": "10/09/2026", "note": "Thu tạm ứng đợt 2",
    })
    assert out["ok"], out["error"]
    fresh = vm.read_shipment("LO-0307")
    payments = fresh["data"]["3.4"]["payments"]
    match = [p for p in payments if p.get("request_id") == "REQ-PB-0307-A"]
    assert len(match) == 1
    assert float(match[0]["amount"]) == 25000000.0
    assert match[0]["id"] == out["persisted"]["paymentId"]
    # Derived balances come from core.logic, not from the component.
    assert out["persisted"]["derivedPaid"] is not None
    assert out["readback"]["finance"]["received"] == out["persisted"]["derivedPaid"]


def test_payment_idempotency(staging, event_seq):
    """PAYMENT_IDEMPOTENCY — one request identity ⇒ exactly one payment."""
    payload = {"shipmentId": "LO-0307", "amount": 40000000,
               "requestId": "REQ-PB-IDEMPOTENT", "date": "2026-09-10", "note": "Thu đợt 1"}
    first = _dispatch(event_seq, "payment_record", payload)
    replay = _dispatch(event_seq, "payment_record", dict(payload))

    assert first["ok"] and replay["ok"]
    assert replay["persisted"]["paymentId"] == first["persisted"]["paymentId"]

    fresh = vm.read_shipment("LO-0307")
    rows = [p for p in fresh["data"]["3.4"]["payments"]
            if p.get("request_id") == "REQ-PB-IDEMPOTENT"]
    assert len(rows) == 1, "a replayed request identity must not double-post"

    registry = logi_sandbox._state["client"][logi_sandbox.STAGING_DB_NAME].financial_action_requests
    assert registry.count_documents({"request_id": "REQ-PB-IDEMPOTENT"}) == 1


def test_payment_rejects_non_positive_amount(staging, event_seq):
    """A zero/negative amount is refused by the canonical writer."""
    out = _dispatch(event_seq, "payment_record", {
        "shipmentId": "LO-0307", "amount": 0, "requestId": "REQ-PB-ZERO"})
    assert out["ok"] is False
    assert "lớn hơn 0" in out["error"]


def test_payment_correction_is_audited_not_deleted(staging, event_seq):
    """Correction reverses traceably; the original history row survives."""
    created = _dispatch(event_seq, "payment_record", {
        "shipmentId": "LO-0307", "amount": 15000000, "requestId": "REQ-PB-CORR",
        "date": "2026-09-10", "note": "Thu nhầm"})
    assert created["ok"], created["error"]
    payment_id = created["persisted"]["paymentId"]

    correction = _dispatch(event_seq, "payment_correction", {
        "shipmentId": "LO-0307", "paymentId": payment_id,
        "correctionRequestId": "REQ-PB-CORR-FIX", "reason": "Nhập sai số tiền"})
    assert correction["ok"], correction["error"]

    fresh = vm.read_shipment("LO-0307")
    original = next(p for p in fresh["data"]["3.4"]["payments"] if p["id"] == payment_id)
    assert original.get("is_reversed") is True or str(original.get("status", "")).lower() == "reversed"
    # History is preserved, never deleted.
    assert any(p["id"] == payment_id for p in fresh["data"]["3.4"]["payments"])


# ---------------------------------------------------------------------------
# Shipment creation
# ---------------------------------------------------------------------------

def test_shipment_create_readback_and_duplicate_rejected(staging, event_seq):
    """CREATE_SHIPMENT — real creation logic, duplicate codes rejected."""
    out = _dispatch(event_seq, "shipment_create", {
        "shipmentId": "lo-0450", "customerId": "CUST-ANPHAT",
        "transport": {"mode": "Truck", "incoterm": "DAP", "pol": "Nam Ninh (Quảng Tây)",
                      "pod": "Hữu Nghị (Lạng Sơn)", "etd": "20/09/2026"},
        "delivery": {"addr": "Kho An Phát — KCN Quế Võ", "phone_receiver": "0912445778"},
    })
    assert out["ok"], out["error"]

    fresh = vm.read_shipment("LO-0450")
    assert fresh is not None
    assert fresh["customer"] == "An Phát JSC"
    assert fresh["data"]["1.2"]["pol"] == "Nam Ninh (Quảng Tây)"
    assert fresh["data"]["2.7"]["addr"].startswith("Kho An Phát")
    assert out["persisted"]["version"] >= 1

    duplicate = _dispatch(event_seq, "shipment_create", {
        "shipmentId": "LO-0450", "customerId": "CUST-ANPHAT"})
    assert duplicate["ok"] is False
    assert "đã tồn tại" in duplicate["error"]


def test_shipment_create_requires_customer(staging, event_seq):
    out = _dispatch(event_seq, "shipment_create", {"shipmentId": "LO-0451"})
    assert out["ok"] is False
    assert "khách hàng" in out["error"].lower()


# ---------------------------------------------------------------------------
# PXK — real delivery gate + real service
# ---------------------------------------------------------------------------

def _make_pxk_ready_shipment(event_seq) -> str:
    """Create a delivered shipment with exactly one goods line + HDMB source.

    core.docgen PXK V1 requires an explicitly selected HDMB/PL source resolving
    to exactly one goods line, so the fixture satisfies that real rule.
    """
    sid = "LO-0460"
    created = _dispatch(event_seq, "shipment_create", {
        "shipmentId": sid, "customerId": "CUST-ANPHAT", "contractId": "HDMB-0306",
        "transport": {"mode": "Truck", "pol": "Bằng Tường", "pod": "Hữu Nghị", "etd": "2026-09-12"},
        "delivery": {"addr": "Kho An Phát — KCN Quế Võ"},
    })
    assert created["ok"], created["error"]
    line = _dispatch(event_seq, "finance_actual_save", {
        "shipmentId": sid,
        "line": {"name": "Hàng tiêu dùng xuất khẩu", "qty": 1, "price": 120000000,
                 "cost": 108000000, "vat": 8},
    })
    assert line["ok"], line["error"]
    # PR140 precondition: confirm the entrusted import model through the
    # existing commercial-flow writer so the PXK applicability gate opens;
    # the downstream delivery/docgen gates under test stay exactly as before.
    flow = _dispatch(event_seq, "shipment_commercial_flow_save", {
        "shipmentId": sid,
        "requestId": f"REQ-FLOW-{sid}",
        "mode": "TT_ENTRUSTED_DIRECT",
        # Staging authority_companies carries ONE legal person in two role
        # records (signing + legal importer), so the writer's single-record
        # auto-fill no longer applies: the caller picks the signing role
        # explicitly. validate_flow_write itself is unchanged.
        "companyId": "TT-COMPANY",
        "subAgentId": "",
    })
    assert flow["ok"], flow["error"]
    return sid


def test_pxk_delivery_gate_blocks_undelivered(staging, event_seq):
    """PXK_DELIVERY_GATE — an undelivered shipment is blocked by rule."""
    sid = _make_pxk_ready_shipment(event_seq)
    out = _dispatch(event_seq, "pxk_generate", {"shipmentId": sid})
    assert out["ok"] is False
    assert out["gate"] == "BLOCKED_NOT_DELIVERED"
    assert out["delivered"] is False
    assert "chưa được xác nhận giao" in out["error"]


def test_pxk_gate_opens_after_delivery_then_uses_real_service(staging, event_seq):
    """PXK_REAL_SERVICE — the real docgen service runs; no prototype TXT."""
    from core.docgen import generator as docgen

    sid = _make_pxk_ready_shipment(event_seq)
    confirm = _dispatch(event_seq, "delivery_confirm", {
        "shipmentId": sid, "deliveredAt": "2026-09-12",
        "receiverName": "A. Nam", "receiverTitle": "Thủ kho",
        "deliveryLocation": "Kho An Phát — KCN Quế Võ"})
    assert confirm["ok"], confirm["error"]

    out = _dispatch(event_seq, "pxk_generate", {"shipmentId": sid})
    # The DELIVERY gate is now open — this is the point of the gate test.
    assert out["delivered"] is True
    assert out["gate"] != "BLOCKED_NOT_DELIVERED"

    if not out["ok"]:
        # Beyond delivery, PXK needs Owner-controlled legal identity
        # (authority company/agent records) and a legal XLSX template. Neither
        # ships in this repository, and inventing them is forbidden — so the
        # real docgen readiness engine must refuse, fail-closed, naming the
        # missing legal facts. It must never fall back to a prototype TXT.
        assert out["gate"] in {"MISSING_INFO", "BLOCKED"}
        assert out["missing"], "a refusal must name the missing legal facts"
        assert ".txt" not in out["error"].lower()
        assert "prototype" not in out["error"].lower()
    else:
        assert out["persisted"]["isOfficeFile"] is True
        assert out["persisted"]["fileName"].endswith(".xlsx")
        assert out["service"] == "core.docgen.generator.generate_document"

    # Independent proof that the docgen writer emits a real OOXML container
    # rather than a text placeholder, using a structural (non-legal) fixture.
    from openpyxl import Workbook

    from core.docgen.template_engine import mutate_xlsx

    book = Workbook()
    sheet = book.active
    sheet["A1"] = "CONTRACT_NO"
    buffer = io.BytesIO()
    book.save(buffer)
    fixture = "/tmp/logi_pbk_structural_fixture.xlsx"
    with open(fixture, "wb") as handle:
        handle.write(buffer.getvalue())

    produced = mutate_xlsx(fixture, {"A1": {"value": "PXK-STRUCT-001"}})
    assert produced[:2] == b"PK", "docgen output must be a real OOXML container"
    assert zipfile.ZipFile(io.BytesIO(produced)).namelist(), "must be a readable .xlsx"


def test_pxk_operator_identity_generates_persisted_office_file(staging, event_seq):
    """PXK: operator-supplied legal identity → real generation → persistence.

    LOGI_REAL_USE_READINESS_01 repair pin. core.docgen refuses to invent the
    lot's own ``pxk_no`` / ``pxk_date`` (as the authoritative docgen desk does,
    they are operator inputs), so without them the gate must stay fail-closed
    and NAME the missing facts. With them, the real service must produce an
    OOXML file, persist canonical document metadata, and the fresh view model
    must read the document back (number/date/done + downloadable bytes) — the
    UI used to drop all three and only showed a toast.
    """
    import base64

    from core.database import get_db

    sid = _make_pxk_ready_shipment(event_seq)
    confirm = _dispatch(event_seq, "delivery_confirm", {
        "shipmentId": sid, "deliveredAt": "2026-09-12",
        "receiverName": "A. Nam", "receiverTitle": "Thủ kho",
        "deliveryLocation": "Kho An Phát — KCN Quế Võ"})
    assert confirm["ok"], confirm["error"]

    # (1) Fail closed while the legal identity is missing.
    out = _dispatch(event_seq, "pxk_generate", {"shipmentId": sid})
    assert out["ok"] is False
    assert out["gate"] == "MISSING_INFO"
    assert out["missing"], "a refusal must name the missing facts"
    assert "Phiếu xuất kho" in " ".join(out["missing"])
    assert get_db()["docgen_documents"].count_documents({"shipment_id": sid}) == 0

    # (2) With the operator's identity the real service generates + persists.
    out = _dispatch(event_seq, "pxk_generate", {
        "shipmentId": sid, "pxkNo": "PXK-2026-0460", "pxkDate": "2026-09-12"})
    assert out["ok"], out
    assert out["service"] == "core.docgen.generator.generate_document"
    assert out["persisted"]["isOfficeFile"] is True
    assert out["persisted"]["fileName"].endswith(".xlsx")
    assert out["persisted"]["pxkNo"] == "PXK-2026-0460"

    row = get_db()["docgen_documents"].find_one({"shipment_id": sid}, {"_id": 0})
    assert row is not None, "PXK metadata was not persisted canonically"
    assert row["document_type"] == "PXK"
    assert row["status"] == "GENERATED"
    assert row["output_file_name"].endswith(".xlsx")

    # (3) Fresh readback through a rebuilt view model (not frontend state).
    pxk = next(s["pxk"] for s in vm.build_view_model()["shipments"] if s["id"] == sid)
    assert pxk["done"] is True
    assert pxk["number"] == "PXK-2026-0460"
    assert pxk["date"] == "2026-09-12"
    assert pxk["source"] == "HDMB-0306"
    document = pxk["document"]
    assert document and document["status"] == "GENERATED"
    assert document["downloadAvailable"] is True
    raw = base64.b64decode(document["downloadBase64"])
    assert raw[:2] == b"PK", "the downloadable payload must be a real OOXML container"
    assert zipfile.ZipFile(io.BytesIO(raw)).namelist()

    from core.database import load_docgen_document, load_shipment_attachment
    from core.shipment_attachments import fetch_attachment_bytes
    import streamlit as st
    from views import logi_c1

    attachment_id = out["persisted"]["attachmentId"]
    attachment = load_shipment_attachment(attachment_id)
    assert attachment["shipment_id"] == sid
    assert attachment["category"] == "other"
    assert load_docgen_document(out["persisted"]["recordId"])["document_type"] == "PXK"

    # Clearing the session cache does not remove the normal durable attachment.
    st.session_state[logi_c1._outputs_key(sid)] = {}
    fetched = fetch_attachment_bytes({"id": attachment_id}, shipment_id=sid)
    assert fetched["ok"] is True
    assert fetched["data"] == raw


def test_pxk_requires_linked_source_contract(staging, event_seq):
    """PXK needs an explicitly linked HDMB/PL source — no invented legal data."""
    # PR140 precondition: while the import model is unconfirmed the server
    # refuses PXK outright — challenge that gate first.
    blocked = _dispatch(event_seq, "pxk_generate", {"shipmentId": "LO-0295"})
    assert blocked["ok"] is False
    assert blocked["gate"] == "COMMERCIAL_FLOW_REQUIRED"

    flow = _dispatch(event_seq, "shipment_commercial_flow_save", {
        "shipmentId": "LO-0295",
        "requestId": "REQ-FLOW-0295",
        "mode": "TT_ENTRUSTED_DIRECT",
        # Same explicit signing-role choice as the helper above (2 role records
        # for one legal person ⇒ no single-record auto-fill).
        "companyId": "TT-COMPANY",
        "subAgentId": "",
    })
    assert flow["ok"], flow["error"]

    out = _dispatch(event_seq, "pxk_generate", {"shipmentId": "LO-0295"})
    assert out["ok"] is False
    assert out["delivered"] is True
    assert out["gate"] in {"BLOCKED_NO_SOURCE", "MISSING_INFO", "BLOCKED"}


# ---------------------------------------------------------------------------
# RBAC — backend-enforced, not frontend display
# ---------------------------------------------------------------------------

def test_rbac_denies_finance_write_for_read_only_role(staging, event_seq, monkeypatch):
    """REAL_RBAC — a viewer role cannot post a payment."""
    import streamlit as st

    st.session_state["current_user"] = {"username": "viewer.user", "role": "VIEWER",
                                        "user_id": "U-VIEWER"}
    out = _dispatch(event_seq, "payment_record", {
        "shipmentId": "LO-0307", "amount": 1000000, "requestId": "REQ-RBAC-1"})
    assert out["ok"] is False
    assert "quyền" in out["error"]
    fresh = vm.read_shipment("LO-0307")
    assert not [p for p in fresh["data"]["3.4"]["payments"] if p.get("request_id") == "REQ-RBAC-1"]


def test_rbac_denies_unauthenticated_writer(staging, event_seq):
    """REAL_RBAC — with no authenticated actor, writes are refused."""
    import streamlit as st

    st.session_state["current_user"] = {}
    out = _dispatch(event_seq, "shipment_field_save", {
        "shipmentId": "LO-0307", "fields": {"tk_no": "111111111111"}})
    assert out["ok"] is False


def test_rbac_denies_shipment_create_for_viewer(staging, event_seq):
    import streamlit as st

    st.session_state["current_user"] = {"username": "viewer.user", "role": "VIEWER",
                                        "user_id": "U-VIEWER"}
    out = _dispatch(event_seq, "shipment_create", {
        "shipmentId": "LO-0470", "customerId": "CUST-ANPHAT"})
    assert out["ok"] is False
    assert vm.read_shipment("LO-0470") is None


# ---------------------------------------------------------------------------
# Audit
# ---------------------------------------------------------------------------

def test_real_audit_trail_records_every_material_write(staging, event_seq):
    """REAL_AUDIT — the canonical writer's audit log, read back from the DB."""
    from core.database import load_audit_logs

    _dispatch(event_seq, "shipment_field_save",
              {"shipmentId": "LO-0306", "fields": {"tk_no": "105500000001"}})
    _dispatch(event_seq, "payment_record",
              {"shipmentId": "LO-0306", "amount": 5000000, "requestId": "REQ-AUDIT-1"})
    _dispatch(event_seq, "delivery_confirm", {"shipmentId": "LO-0306", "deliveredAt": "2026-09-10"})

    rows = load_audit_logs("shipment", "LO-0306", limit=50)
    actions = [row.get("action") for row in rows]
    assert "update" in actions
    assert "direct_payment_created" in actions
    actors = {row.get("actor") for row in rows}
    assert actors, "audit must record a real actor"
    assert all(row.get("created_at") for row in rows)


# ---------------------------------------------------------------------------
# UNKNOWN != ZERO regression
# ---------------------------------------------------------------------------

def test_unknown_never_becomes_zero(staging):
    """Numeric business values the model does not carry stay UNKNOWN."""
    data = vm.load_shipments()
    for sid, ship in data.items():
        projection = rd.shipment_projection(ship)
        # Import tax/VAT are not modelled on the shipment document.
        assert projection["importInfo"]["tax"] is None, sid
        assert projection["importInfo"]["vat"] is None, sid
        # Pack count / weight / CBM live in one free-text field upstream.
        assert projection["cargo"]["packs"] is None, sid
        assert projection["cargo"]["weight"] is None, sid
        assert projection["cargo"]["cbm"] is None, sid
        # Supplier-side "already paid" has no ledger on the shipment.
        assert projection["finance"]["paid"] is None, sid
        # The projection renders UNKNOWN as an explicit dash, never "0".
        assert rd.label(None) == rd.UNKNOWN_LABEL
        assert rd.num("") is None
        assert rd.num(None) is None


def test_blank_fields_are_not_coerced_to_zero_on_write(staging, event_seq):
    """A blank text/number field is stored blank, not as 0."""
    out = _dispatch(event_seq, "shipment_field_save", {
        "shipmentId": "LO-0308",
        "fields": {"tk_no": "", "phan_luong": "", "free_time": ""},
    })
    assert out["ok"], out["error"]
    fresh = vm.read_shipment("LO-0308")
    assert fresh["data"]["2.4"]["tk_no"] == ""
    assert fresh["data"]["2.4"]["phan_luong"] == ""
    assert fresh["data"]["2.6"]["free_time"] == ""


# ---------------------------------------------------------------------------
# Dispatcher bounding
# ---------------------------------------------------------------------------

def test_dispatcher_rejects_unbounded_events_and_fields(staging):
    """Only the declared Phase B events and whitelisted fields are accepted."""
    assert vm.PHASE_B_EVENTS == set(vm._HANDLERS)

    unknown = vm.consume_phase_b_triggers({"seq": 0}, {
        "drop_database": {"seq": 1, "payload": {}}})
    assert unknown == []

    out = vm._handle_field_save({"shipmentId": "LO-0308",
                                 "fields": {"is_deleted": True, "customer": "Evil"}})
    assert out["ok"] is False
    assert set(out["rejected"]) == {"is_deleted", "customer"}
    assert vm.read_shipment("LO-0308")["customer"] == "Minh Đức JSC"


def test_replayed_sequence_is_ignored(staging):
    """A stale/replayed seq can never re-execute a write."""
    session = {"seq": 5}
    stale = vm.consume_phase_b_triggers(session, {
        "shipment_field_save": {"seq": 3, "payload": {"shipmentId": "LO-0308", "fields": {"tk_no": "9"}}}})
    assert stale == []
    assert session["seq"] == 5


# ---------------------------------------------------------------------------
# Read side — the frozen UI receives real data
# ---------------------------------------------------------------------------

def test_view_model_is_built_from_real_readers(staging):
    """Home / Tasks / Shipments / Shipment Detail are all real-backed."""
    model = vm.build_view_model()

    assert model["environment"]["isSandbox"] is True
    assert model["environment"]["label"] == "Preview / Staging"
    assert model["user"]["displayOnly"] is True

    ids = {row["id"] for row in model["shipments"]}
    assert {"LO-0295", "LO-0299", "LO-0306", "LO-0307", "LO-0308"} <= ids

    # Home tiles are counts of real shipments, not hardcoded KPI.
    tile_labels = {tile["label"] for tile in model["home"]["tiles"]}
    assert {"Lô đang chạy", "Chờ lấy hàng", "Chờ thông quan", "Chờ giao"} <= tile_labels
    assert model["home"]["summary"]["total"] == len(model["shipments"])
    assert model["home"]["focus"] is not None

    # Tasks are derived from real readiness/alerts or the real tasks collection.
    assert model["tasks"], "Tasks must come from real evidence"
    for task in model["tasks"]:
        assert task["source"] in {"core.shipment_dashboard (readiness/alerts)",
                                  "core.database.load_tasks"}
        assert task["route"].startswith("/lo-hang")

    # Every shipment row carries the five-tab payloads.
    for row in model["shipments"]:
        for key in ("pickup", "transport", "cargo", "exportInfo", "importInfo",
                    "finance", "pxk", "timeline", "tracking", "ops"):
            assert key in row, f"{row['id']} missing {key}"
        assert row["finance"]["source"].startswith("core.logic")
        # QUOTE ESTIMATE and FINANCE ACTUAL stay distinct collections.
        assert all(line["kind"] == "quote" for line in row["finance"]["quote"])
        assert all(line["kind"] == "actual" for line in row["finance"]["actual"])

    # Tracking never fabricates a live position.
    for row in model["shipments"]:
        assert row["tracking"]["hasLivePosition"] is False
        assert row["tracking"]["positionNote"]


def test_shipment_detail_tabs_have_real_evidence(staging, event_seq):
    """Five-tab payload is populated from real facts, including history."""
    _dispatch(event_seq, "shipment_field_save",
              {"shipmentId": "LO-0307", "fields": {"tk_no": "105588421330"}})
    model = vm.build_view_model()
    row = next(r for r in model["shipments"] if r["id"] == "LO-0307")

    assert row["importInfo"]["declarationNo"] == "105588421330"          # tab 2
    assert row["finance"]["actual"], "tab 3 needs real Finance Actual"   # tab 3
    assert row["pxk"]["source"] or row["pxk"]["gateOpen"] is False       # tab 4
    assert row["timeline"], "tab 5 must show the real audit trail"       # tab 5
    assert any(entry["title"] for entry in row["timeline"])
    assert row["transport"]["pol"], "tab 1 needs real transport facts"    # tab 1


def test_write_then_rebuild_view_model_reflects_database(staging, event_seq):
    """The refreshed view-model comes from the DB, not from frontend state."""
    _dispatch(event_seq, "shipment_field_save",
              {"shipmentId": "LO-0306", "fields": {"truck_no": "29H-999.99"}})
    model = vm.build_view_model()
    row = next(r for r in model["shipments"] if r["id"] == "LO-0306")
    assert row["importInfo"]["plateVN"] == "29H-999.99"


def test_payload_version_changes_only_with_data(staging, event_seq):
    first = vm.build_view_model()["version"]
    second = vm.build_view_model()["version"]
    assert first == second
    _dispatch(event_seq, "shipment_field_save",
              {"shipmentId": "LO-0306", "fields": {"tk_no": "105512345678"}})
    assert vm.build_view_model()["version"] != first
