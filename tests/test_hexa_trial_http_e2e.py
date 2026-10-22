"""End-to-end HTTP + GridFS verification for HEXA V0 TT -> Lục Giác ROAD trial.

Exercises the real HTTP server (``ThreadingHTTPServer``) over TCP loopback,
real ``core.quotations`` calculation, real ``core.shipment_attachments`` GridFS
upload/download, and ``core.hexa_customer_publication`` fail-closed guards.
"""
from __future__ import annotations

import json
import threading
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from core import database as core_db
from core import shipment_attachments as core_att
from core.hexa_trial_portal import (
    CUSTOMER_A_ID,
    CUSTOMER_B_ID,
    INTERNAL_QA_HEADER,
    QUOTE_A_ID,
    QUOTE_B_ID,
    SCHEMA_GAP_REPORT,
    SENTINEL_FOREIGN_CUSTOMER_B,
    SENTINEL_TT_INTERNAL_COST,
    SENTINEL_TT_MARGIN,
    SENTINEL_TT_PRIVATE_SUPPLIER,
    SENTINEL_TT_UNVERIFIED_ETA,
    SHARED_TRIP_ID,
    SHIPMENT_A_ID,
    SHIPMENT_B_ID,
    TRIAL_COOKIE_NAME,
    TRIAL_SENTINELS,
    HexaTrialEnvironment,
    create_trial_http_server,
)


def _http_request(
    base_url: str,
    path: str,
    *,
    method: str = "GET",
    session_token: str | None = None,
    headers: dict[str, str] | None = None,
    json_body: dict[str, Any] | None = None,
) -> tuple[int, dict[str, str], bytes]:
    req_headers: dict[str, str] = dict(headers or {})
    if session_token is not None:
        req_headers["Cookie"] = f"{TRIAL_COOKIE_NAME}={session_token}"
    data = None
    if json_body is not None:
        data = json.dumps(json_body).encode("utf-8")
        req_headers["Content-Type"] = "application/json"

    req = Request(f"{base_url}{path}", data=data, headers=req_headers, method=method)
    try:
        with urlopen(req, timeout=10) as resp:
            return resp.status, dict(resp.headers.items()), resp.read()
    except HTTPError as exc:
        return exc.code, dict(exc.headers.items()), exc.read()


def _server_issued_token(env: HexaTrialEnvironment, role_key: str, legacy_fallback: str) -> str:
    getter = getattr(env, "get_trial_session_token", None)
    if callable(getter):
        return str(getter(role_key))
    return legacy_fallback


@pytest.fixture()
def trial_server():
    env = HexaTrialEnvironment()
    env.ensure_seeded(force_reset=True)
    server = create_trial_http_server(host="127.0.0.1", port=0, env=env)
    host, port = server.server_address[:2]
    base_url = f"http://{host}:{port}"
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield base_url, env
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_ac1_tt_internal_store_holds_cost_supplier_and_shared_truck_data(trial_server) -> None:
    """AC #1: TT holds internal data including cost price and supplier info on the shared truck."""
    base_url, env = trial_server
    db = core_db.get_db()
    assert db is not None

    ship_a = db["shipments"].find_one({"id": SHIPMENT_A_ID})
    ship_b = db["shipments"].find_one({"id": SHIPMENT_B_ID})
    assert ship_a is not None and ship_b is not None

    # Both shipments share the same ROAD trip and truck plate in TT's internal store
    assert ship_a["data"]["1.2"]["booking_no"] == SHARED_TRIP_ID
    assert ship_b["data"]["1.2"]["booking_no"] == SHARED_TRIP_ID
    assert ship_a["data"]["1.2"]["container_no"] == ship_b["data"]["1.2"]["container_no"]

    # Quote A has real internal cost, supplier, and margin in TT's internal database
    quote_a = db["quotes"].find_one({"id": QUOTE_A_ID})
    assert quote_a is not None
    calc_a = quote_a["calculation"]
    assert calc_a["estimated_cost_vnd"] == 42000000.0
    assert calc_a["estimated_margin_vnd"] == 11000000.0
    assert calc_a["selling_price_total_vnd"] == 57240000.0
    assert SENTINEL_TT_PRIVATE_SUPPLIER in quote_a["factory_lots"][0]["factory_name"]

    # Internal Python snapshot (server-side only, never exposed on customer HTTP) holds TT truth
    inspector = env.build_trial_inspector_snapshot()
    assert inspector["tt_internal_only_data"]["cost_before_tax_vnd"] == 42000000.0
    assert inspector["tt_internal_only_data"]["selling_total_vnd"] == 57240000.0

    # Customer HTTP path MUST NOT serve the internal inspector to unauthenticated callers
    status, _hdrs, raw = _http_request(base_url, "/api/hexa/v0/trial-inspector")
    assert status == 403
    assert json.loads(raw.decode("utf-8")) == {"error": "CUSTOMER_RESOURCE_UNAVAILABLE"}


def test_ac2_and_ac4_lg_receives_only_published_progress_pinned_docs_sent_quote_and_no_unverified_eta(
    trial_server,
) -> None:
    """AC #2 & AC #4: LG receives only shared progress, pinned doc versions, sent selling quote, and zero unverified ETA."""
    base_url, env = trial_server
    token_a = _server_issued_token(env, "customer_a", "sess-customer-lg")

    status, _hdrs, raw = _http_request(
        base_url,
        f"/api/hexa/v0/shipments/{SHIPMENT_A_ID}",
        session_token=token_a,
    )
    assert status == 200
    text = raw.decode("utf-8")
    payload = json.loads(text)

    assert payload == {
        "schema": "hexa-customer-publication/v0",
        "reference": SHIPMENT_A_ID,
        "transport_mode": "ROAD",
        "timeline": [
            {
                "id": "EVT-LG-02-BORDER",
                "version": "v2",
                "stage": "road-border",
                "title": "Xe 29H-886.68 đã hoàn tất thông quan và qua cửa khẩu Hữu Nghị",
                "occurred_at": "2026-10-21T14:15:00Z",
            },
            {
                "id": "EVT-LG-01-PICKUP",
                "version": "v1",
                "stage": "pickup",
                "title": "Đã nhận 18 kiện hàng Lục Giác tại kho Bằng Tường và xếp lên xe 29H-886.68",
                "occurred_at": "2026-10-20T08:30:00Z",
            },
        ],
        "documents": [
            {
                "id": "DOC-LG-PL",
                "version": "v2",
                "kind": "PL",
                "title": "Packing List Lục Giác (Bản v2 đã duyệt)",
            },
            {
                "id": "DOC-LG-PI",
                "version": "v1",
                "kind": "PI",
                "title": "Proforma Invoice Lục Giác (Bản v1)",
            },
        ],
        "quote": {
            "id": QUOTE_A_ID,
            "version": "3",
            "status": "SENT",
            "selling_total_vnd": 57240000.0,
        },
    }

    # Unverified ETA date (2026-10-25) and all internal/foreign sentinels must be completely absent
    assert "2026-10-25" not in text
    assert "EVT-LG-03-ETA-UNVERIFIED" not in text
    assert "EVT-LG-04-ETA-INTERNAL" not in text
    assert "DOC-LG-COST" not in text
    assert "DOC-MD-PL" not in text
    for sentinel in TRIAL_SENTINELS:
        assert sentinel not in text


def test_ac3_cross_customer_isolation_on_same_truck_even_when_guessing_urls_or_lot_codes(
    trial_server,
) -> None:
    """AC #3: Customer A cannot view/download Customer B's info, even when guessing URLs or shipment codes (and vice versa)."""
    base_url, env = trial_server
    token_a = _server_issued_token(env, "customer_a", "sess-customer-lg")
    token_b = _server_issued_token(env, "customer_b", "sess-customer-md")
    token_viewer = _server_issued_token(env, "internal_viewer", "sess-internal-viewer")

    # 1. Customer A (Lục Giác) guesses Customer B's shipment code ROAD-MD-002
    for path in (
        f"/api/hexa/v0/shipments/{SHIPMENT_B_ID}",
        f"/api/hexa/v0/shipments/{SHIPMENT_B_ID}?customer_id={CUSTOMER_B_ID}",
        f"/api/hexa/v0/shipments/NON-EXISTENT-LOT",
    ):
        status, _hdrs, raw = _http_request(
            base_url,
            path,
            session_token=token_a,
            headers={"X-Customer-Id": CUSTOMER_B_ID},
        )
        assert status == 403
        assert json.loads(raw.decode("utf-8")) == {"error": "CUSTOMER_RESOURCE_UNAVAILABLE"}

    # 2. Customer B (Minh Đức) can view its own shipment ROAD-MD-002 on the same truck,
    #    but is blocked from Customer A's shipment ROAD-LG-001
    status_b_own, _hdrs, raw_b_own = _http_request(
        base_url,
        f"/api/hexa/v0/shipments/{SHIPMENT_B_ID}",
        session_token=token_b,
    )
    assert status_b_own == 200
    payload_b = json.loads(raw_b_own.decode("utf-8"))
    assert payload_b["reference"] == SHIPMENT_B_ID
    assert payload_b["quote"] == {
        "id": QUOTE_B_ID,
        "version": "3",
        "status": "SENT",
        "selling_total_vnd": 38880000.0,
    }
    assert [d["id"] for d in payload_b["documents"]] == ["DOC-MD-PL"]

    status_b_guess_a, _hdrs, raw_b_guess_a = _http_request(
        base_url,
        f"/api/hexa/v0/shipments/{SHIPMENT_A_ID}",
        session_token=token_b,
    )
    assert status_b_guess_a == 403
    assert json.loads(raw_b_guess_a.decode("utf-8")) == {"error": "CUSTOMER_RESOURCE_UNAVAILABLE"}

    # 3. Internal viewer role (has finance_view) and anonymous callers are denied
    for bad_session in (token_viewer, None, "forged-token"):
        status_bad, _hdrs, raw_bad = _http_request(
            base_url,
            f"/api/hexa/v0/shipments/{SHIPMENT_A_ID}",
            session_token=bad_session,
        )
        assert status_bad == 403
        assert json.loads(raw_bad.decode("utf-8")) == {"error": "CUSTOMER_RESOURCE_UNAVAILABLE"}


def test_ac5_document_download_enforces_server_permission_before_reading_gridfs_bytes(
    trial_server,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC #5: Document download checks permission on server BEFORE reading file bytes from GridFS."""
    base_url, env = trial_server
    token_a = _server_issued_token(env, "customer_a", "sess-customer-lg")
    token_b = _server_issued_token(env, "customer_b", "sess-customer-md")
    token_viewer = _server_issued_token(env, "internal_viewer", "sess-internal-viewer")

    real_fetch = core_att.fetch_attachment_bytes
    fetch_calls: list[tuple[Any, Any]] = []

    def _spy_fetch(record_or_id: Any, *, shipment_id: Any = None) -> dict[str, Any]:
        fetch_calls.append((record_or_id, shipment_id))
        return real_fetch(record_or_id, shipment_id=shipment_id)

    monkeypatch.setattr(core_att, "fetch_attachment_bytes", _spy_fetch)

    # All unauthorized / wrong-version / internal-doc / cross-customer download attempts MUST fail BEFORE fetch_attachment_bytes
    denied_paths = [
        # Stale version v1 of DOC-LG-PL when only v2 is published in manifest
        (token_a, f"/api/hexa/v0/shipments/{SHIPMENT_A_ID}/documents/DOC-LG-PL/download?version=v1"),
        # Unapproved version v3
        (token_a, f"/api/hexa/v0/shipments/{SHIPMENT_A_ID}/documents/DOC-LG-PL/download?version=v3"),
        # Missing version query parameter
        (token_a, f"/api/hexa/v0/shipments/{SHIPMENT_A_ID}/documents/DOC-LG-PL/download"),
        # Internal TT cost sheet on the same shipment
        (token_a, f"/api/hexa/v0/shipments/{SHIPMENT_A_ID}/documents/DOC-LG-COST/download?version=v1"),
        # Customer B's document on the shared trip pool under ROAD-LG-001
        (token_a, f"/api/hexa/v0/shipments/{SHIPMENT_A_ID}/documents/DOC-MD-PL/download?version=v1"),
        # Customer A guessing Customer B's shipment URL & document URL
        (token_a, f"/api/hexa/v0/shipments/{SHIPMENT_B_ID}/documents/DOC-MD-PL/download?version=v1"),
        # Customer B guessing Customer A's approved document URL
        (token_b, f"/api/hexa/v0/shipments/{SHIPMENT_A_ID}/documents/DOC-LG-PL/download?version=v2"),
        # Internal viewer role attempting download
        (token_viewer, f"/api/hexa/v0/shipments/{SHIPMENT_A_ID}/documents/DOC-LG-PL/download?version=v2"),
        # Anonymous attempting download
        (None, f"/api/hexa/v0/shipments/{SHIPMENT_A_ID}/documents/DOC-LG-PL/download?version=v2"),
    ]

    for token, path in denied_paths:
        status, _hdrs, raw = _http_request(base_url, path, session_token=token)
        assert status == 403, f"Expected 403 for {token} -> {path}, got {status}"
        assert json.loads(raw.decode("utf-8")) == {"error": "CUSTOMER_RESOURCE_UNAVAILABLE"}

    # Zero GridFS reads occurred across all 9 denied requests!
    assert len(fetch_calls) == 0
    assert env.storage_read_attempts == 0
    assert env.denied_before_storage_reads == len(denied_paths)

    # Now perform an authorized download: Customer A downloading DOC-LG-PL version=v2
    status_ok, hdrs_ok, pdf_bytes = _http_request(
        base_url,
        f"/api/hexa/v0/shipments/{SHIPMENT_A_ID}/documents/DOC-LG-PL/download?version=v2",
        session_token=token_a,
    )
    assert status_ok == 200
    assert pdf_bytes.startswith(b"%PDF-1.4")
    assert b"HEXA PACKING LIST v2" in pdf_bytes
    assert "Packing-List-Luc-Giac-v2.pdf" in hdrs_ok.get("Content-Disposition", "")
    assert len(fetch_calls) == 1
    assert env.storage_read_attempts == 1


def test_ac6_and_ac7_trial_portal_ui_and_schema_gap_report_are_served_over_http(
    trial_server,
) -> None:
    """AC #6 & AC #7: Runnable HTTP customer portal UI is served without leaking internal TT data or auto-issuing sessions."""
    base_url, _env = trial_server

    status_ui, hdrs_ui, html_bytes = _http_request(base_url, "/")
    assert status_ui == 200
    assert "text/html" in hdrs_ui.get("Content-Type", "")
    # Anonymous GET / must NOT automatically grant a customer session cookie
    assert "Set-Cookie" not in hdrs_ui
    html = html_bytes.decode("utf-8")
    assert "HEXA V0" in html

    # Verify schema gap report completeness (AC #7)
    assert len(SCHEMA_GAP_REPORT) == 6
    surfaces = {item["surface"] for item in SCHEMA_GAP_REPORT}
    assert "Phiên đăng nhập khách (principal)" in surfaces
    assert "Bản duyệt công bố của TT (publication manifest)" in surfaces
    assert "Lô hàng ROAD ghép xe nhiều khách (shipment)" in surfaces
    assert "Tiến độ chia sẻ cho khách & trạng thái xác minh ETA (events)" in surfaces
    assert "Chứng từ đính kèm & kiểm quyền tải theo phiên bản (documents)" in surfaces
    assert "Báo giá bán đã gửi (quote)" in surfaces


def test_security_inspector_and_customer_ui_do_not_leak_tt_internal_or_other_customer_data(
    trial_server,
) -> None:
    """Repair #1: Customer A, Customer B, viewer, and anonymous callers CANNOT call inspector or customer UI/API to read TT cost, margin, supplier, or the other customer's data."""
    base_url, env = trial_server
    token_a = _server_issued_token(env, "customer_a", "sess-customer-lg")
    token_b = _server_issued_token(env, "customer_b", "sess-customer-md")
    token_viewer = _server_issued_token(env, "internal_viewer", "sess-internal-viewer")

    forbidden_leaks = (
        "42000000",
        "11000000",
        "29000000",
        "Foshan Hexa",
        "Việt Trung An Bình",
        "tt_internal_only_data",
        "cost_before_tax_vnd",
        "estimated_margin_vnd",
        "other_customer_on_same_truck",
        *TRIAL_SENTINELS,
    )

    for caller_token in (None, token_a, token_b, token_viewer, "sess-customer-lg", "sess-customer-md"):
        for path in ("/api/hexa/v0/trial-inspector", "/internal/qa/inspector"):
            status, _hdrs, raw = _http_request(base_url, path, session_token=caller_token)
            body_text = raw.decode("utf-8")
            assert status == 403, f"Expected 403 on {path} for caller={caller_token}, got {status}: {body_text}"
            assert json.loads(body_text) == {"error": "CUSTOMER_RESOURCE_UNAVAILABLE"}
            for secret in forbidden_leaks:
                assert secret not in body_text

    # Customer HTML page (GET / and GET /hexa) must not embed TT internal inspector calls or TT internal secrets
    for ui_path in ("/", "/hexa"):
        status_ui, _hdrs_ui, raw_ui = _http_request(base_url, ui_path, session_token=token_a)
        assert status_ui == 200
        ui_text = raw_ui.decode("utf-8")
        assert "/api/hexa/v0/trial-inspector" not in ui_text
        for secret in forbidden_leaks:
            assert secret not in ui_text


def test_security_http_client_cannot_self_switch_session_or_use_sample_tokens(
    trial_server,
) -> None:
    """Repair #2: HTTP clients cannot impersonate another customer via sample tokens, GET /api/hexa/v0/session token listing, or POST /api/hexa/v0/session."""
    base_url, env = trial_server
    token_a = _server_issued_token(env, "customer_a", "sess-customer-lg")

    # 1. Predictable sample tokens must be rejected by the server on all shipment & download endpoints
    for sample_token in (
        "sess-customer-lg",
        "sess-customer-md",
        "sess-internal-viewer",
        "sess-anonymous",
        CUSTOMER_A_ID,
        CUSTOMER_B_ID,
    ):
        for ship_id in (SHIPMENT_A_ID, SHIPMENT_B_ID):
            status_ship, _hdrs, raw_ship = _http_request(
                base_url,
                f"/api/hexa/v0/shipments/{ship_id}",
                session_token=sample_token,
            )
            assert status_ship == 403, f"Sample token {sample_token} must be rejected on {ship_id}"
            assert json.loads(raw_ship.decode("utf-8")) == {"error": "CUSTOMER_RESOURCE_UNAVAILABLE"}

    # 2. GET /api/hexa/v0/session must NOT expose available_sessions or any session token strings
    status_sess, _hdrs_sess, raw_sess = _http_request(
        base_url,
        "/api/hexa/v0/session",
        session_token=token_a,
    )
    assert status_sess == 200
    sess_info = json.loads(raw_sess.decode("utf-8"))
    assert "available_sessions" not in sess_info
    assert "active_session_token" not in sess_info
    assert sess_info["principal"]["customer_id"] == CUSTOMER_A_ID

    # 3. POST /api/hexa/v0/session (self-service session switching) must be rejected on the customer path
    for payload in (
        {"session_token": "sess-customer-md"},
        {"role": "customer_b"},
        {"customer_id": CUSTOMER_B_ID},
    ):
        status_post, hdrs_post, raw_post = _http_request(
            base_url,
            "/api/hexa/v0/session",
            method="POST",
            session_token=token_a,
            json_body=payload,
        )
        assert status_post == 403
        assert "Set-Cookie" not in hdrs_post
        assert json.loads(raw_post.decode("utf-8")) == {"error": "CUSTOMER_RESOURCE_UNAVAILABLE"}

    # 4. On the default customer server (internal_qa_mode=False), even /internal/qa/session is disabled
    status_qa_off, hdrs_qa_off, raw_qa_off = _http_request(
        base_url,
        "/internal/qa/session",
        method="POST",
        session_token=token_a,
        headers={INTERNAL_QA_HEADER: env.internal_qa_key},
        json_body={"role": "customer_b"},
    )
    assert status_qa_off == 403
    assert "Set-Cookie" not in hdrs_qa_off
    assert json.loads(raw_qa_off.decode("utf-8")) == {"error": "CUSTOMER_RESOURCE_UNAVAILABLE"}

    # 5. Even when an isolated internal QA server is explicitly started (internal_qa_mode=True),
    #    customers without the server-only X-Hexa-Internal-QA-Key are still denied on /internal/qa/*
    #    and on /api/hexa/v0/session.
    qa_server = create_trial_http_server(host="127.0.0.1", port=0, env=env, internal_qa_mode=True)
    qa_host, qa_port = qa_server.server_address[:2]
    qa_url = f"http://{qa_host}:{qa_port}"
    qa_thread = threading.Thread(target=qa_server.serve_forever, daemon=True)
    qa_thread.start()
    try:
        status_no_key, hdrs_no_key, _ = _http_request(
            qa_url,
            "/internal/qa/session",
            method="POST",
            session_token=token_a,
            json_body={"role": "customer_b"},
        )
        assert status_no_key == 403
        assert "Set-Cookie" not in hdrs_no_key

        status_cust_inspector, _, _ = _http_request(
            qa_url,
            "/api/hexa/v0/trial-inspector",
            session_token=token_a,
            headers={INTERNAL_QA_HEADER: env.internal_qa_key},
        )
        assert status_cust_inspector == 403

        # Internal QA harness WITH server-only key can switch role on isolated /internal/qa/session
        status_with_key, hdrs_with_key, raw_with_key = _http_request(
            qa_url,
            "/internal/qa/session",
            method="POST",
            headers={INTERNAL_QA_HEADER: env.internal_qa_key},
            json_body={"role": "customer_b"},
        )
        assert status_with_key == 200
        assert TRIAL_COOKIE_NAME in hdrs_with_key.get("Set-Cookie", "")
        assert json.loads(raw_with_key.decode("utf-8"))["principal"]["customer_id"] == CUSTOMER_B_ID
    finally:
        qa_server.shutdown()
        qa_server.server_close()
        qa_thread.join(timeout=5)
