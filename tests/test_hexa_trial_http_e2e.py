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
    TRIAL_TT_COOKIE_NAME,
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
    _tt_login_and_publish_standard_fixtures(base_url)
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
    _tt_login_and_publish_standard_fixtures(base_url)
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
    _tt_login_and_publish_standard_fixtures(base_url)
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


def _extract_cookie_value(headers: dict[str, str], cookie_name: str) -> str:
    raw_set_cookie = headers.get("Set-Cookie") or headers.get("set-cookie") or ""
    for part in raw_set_cookie.split(";"):
        part = part.strip()
        if part.startswith(f"{cookie_name}="):
            return part.split("=", 1)[1].strip()
    return ""


def _tt_login_and_publish_standard_fixtures(base_url: str) -> str:
    """Test-only helper: authenticate as TT staff over HTTP and publish baseline items for tests that require PUBLISHED state."""
    st_login, hdrs_login, _ = _http_request(
        base_url,
        "/api/hexa/v0/tt/auth/login",
        method="POST",
        json_body={"username": "tt.ops.truongthanh", "passcode": "TT-Trial-2026!"},
    )
    assert st_login == 200
    tt_token = _extract_cookie_value(hdrs_login, "hexa_trial_tt_session")
    assert tt_token

    st_pub_a, _, _ = _http_request(
        base_url,
        f"/api/hexa/v0/tt/shipments/{SHIPMENT_A_ID}/publish",
        method="POST",
        session_token=tt_token,
        json_body={
            "event_versions": {
                "EVT-LG-01-PICKUP": "v1",
                "EVT-LG-02-BORDER": "v2",
            },
            "document_versions": {
                "DOC-LG-PL": "v2",
                "DOC-LG-PI": "v1",
            },
            "quote": {"id": QUOTE_A_ID, "version": "3"},
        },
    )
    assert st_pub_a == 200

    st_pub_b, _, _ = _http_request(
        base_url,
        f"/api/hexa/v0/tt/shipments/{SHIPMENT_B_ID}/publish",
        method="POST",
        session_token=tt_token,
        json_body={
            "event_versions": {"EVT-MD-01-PICKUP": "v1"},
            "document_versions": {"DOC-MD-PL": "v1"},
            "quote": {"id": QUOTE_B_ID, "version": "3"},
        },
    )
    assert st_pub_b == 200
    return tt_token


def test_v1_fresh_sandbox_starts_default_deny_unpublished_with_zero_approved_metadata(
    trial_server,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Default-deny closure: a fresh trial environment starts UNPUBLISHED for both customers with no fake approved_by/approved_at and zero shared items."""
    base_url, env = trial_server
    db = core_db.get_db()
    assert db is not None

    real_fetch = core_att.fetch_attachment_bytes
    fetch_calls: list[tuple[Any, Any]] = []

    def _spy_fetch(record_or_id: Any, *, shipment_id: Any = None) -> dict[str, Any]:
        fetch_calls.append((record_or_id, shipment_id))
        return real_fetch(record_or_id, shipment_id=shipment_id)

    monkeypatch.setattr(core_att, "fetch_attachment_bytes", _spy_fetch)

    # 1. Verify raw DB state on fresh boot: no PUBLISHED manifest, no fake approved_by/approved_at
    for sid, cid in ((SHIPMENT_A_ID, CUSTOMER_A_ID), (SHIPMENT_B_ID, CUSTOMER_B_ID)):
        pub_doc = db["hexa_trial_publications"].find_one({"shipment_id": sid, "customer_id": cid}, {"_id": 0})
        if pub_doc is not None:
            assert pub_doc.get("state") == "UNPUBLISHED"
            assert not pub_doc.get("approved_by")
            assert not pub_doc.get("approved_at")
            assert not pub_doc.get("event_versions")
            assert not pub_doc.get("document_versions")
            assert pub_doc.get("quote") is None

    # 2. TT Staff inspects both shipments on fresh boot -> state is UNPUBLISHED, no fake approval metadata
    st_tt_login, hdrs_tt_login, _ = _http_request(
        base_url,
        "/api/hexa/v0/tt/auth/login",
        method="POST",
        json_body={"username": "tt.ops.truongthanh", "passcode": "TT-Trial-2026!"},
    )
    assert st_tt_login == 200
    tt_token = _extract_cookie_value(hdrs_tt_login, "hexa_trial_tt_session")
    for sid in (SHIPMENT_A_ID, SHIPMENT_B_ID):
        st_inspect, _, raw_inspect = _http_request(
            base_url,
            f"/api/hexa/v0/tt/shipments/{sid}",
            session_token=tt_token,
        )
        assert st_inspect == 200
        pub_view = json.loads(raw_inspect.decode("utf-8"))["publication"]
        assert pub_view["state"] == "UNPUBLISHED"
        assert pub_view["approved_by"] == ""
        assert pub_view["approved_at"] == ""
        assert pub_view["event_versions"] == {}
        assert pub_view["document_versions"] == {}
        assert pub_view["quote"] is None

    # 3. Both Lục Giác and Minh Đức log in BEFORE TT approves -> HTTP 403 on view and download, 0 GridFS bytes read
    for username, passcode, own_sid, own_doc, own_ver in (
        ("lucgiac.trial", "LG-Trial-2026!", SHIPMENT_A_ID, "DOC-LG-PL", "v2"),
        ("minhduc.trial", "MD-Trial-2026!", SHIPMENT_B_ID, "DOC-MD-PL", "v1"),
    ):
        st_login, hdrs_login, _ = _http_request(
            base_url,
            "/api/hexa/v0/auth/login",
            method="POST",
            json_body={"username": username, "passcode": passcode},
        )
        assert st_login == 200
        cust_token = _extract_cookie_value(hdrs_login, TRIAL_COOKIE_NAME)
        assert cust_token

        st_view, _, raw_view = _http_request(
            base_url,
            f"/api/hexa/v0/shipments/{own_sid}",
            session_token=cust_token,
        )
        assert st_view == 403
        assert json.loads(raw_view.decode("utf-8")) == {"error": "CUSTOMER_RESOURCE_UNAVAILABLE"}

        st_dl, _, raw_dl = _http_request(
            base_url,
            f"/api/hexa/v0/shipments/{own_sid}/documents/{own_doc}/download?version={own_ver}",
            session_token=cust_token,
        )
        assert st_dl == 403
        assert json.loads(raw_dl.decode("utf-8")) == {"error": "CUSTOMER_RESOURCE_UNAVAILABLE"}

    assert len(fetch_calls) == 0
    assert env.storage_read_attempts == 0


def test_v1_end_to_end_tt_approve_lg_login_view_download_and_revoke_flow(
    trial_server,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC1, AC2, AC3, AC4, AC5: Complete loop starting from fresh UNPUBLISHED sandbox -> LG denied -> TT selective approve -> LG login, view & download -> TT revoke document."""
    base_url, env = trial_server

    real_fetch = core_att.fetch_attachment_bytes
    fetch_calls: list[tuple[Any, Any]] = []

    def _spy_fetch(record_or_id: Any, *, shipment_id: Any = None) -> dict[str, Any]:
        fetch_calls.append((record_or_id, shipment_id))
        return real_fetch(record_or_id, shipment_id=shipment_id)

    monkeypatch.setattr(core_att, "fetch_attachment_bytes", _spy_fetch)

    # 1. Customer Lục Giác logs in on a brand-new sandbox BEFORE TT approves anything
    status_lg_login, hdrs_lg_login, raw_lg_login = _http_request(
        base_url,
        "/api/hexa/v0/auth/login",
        method="POST",
        json_body={
            "username": "lucgiac.trial",
            "passcode": "LG-Trial-2026!",
            # Tampered customer_id in login body must be ignored by server
            "customer_id": CUSTOMER_B_ID,
        },
    )
    assert status_lg_login == 200
    lg_session_info = json.loads(raw_lg_login.decode("utf-8"))
    assert lg_session_info["authenticated"] is True
    assert lg_session_info["principal"]["kind"] == "customer"
    assert lg_session_info["principal"]["customer_id"] == CUSTOMER_A_ID
    lg_token = _extract_cookie_value(hdrs_lg_login, TRIAL_COOKIE_NAME)
    assert lg_token and lg_token not in ("sess-customer-lg", CUSTOMER_A_ID)

    # 2. AC1 (Default-deny before TT approval): LG cannot view or download anything; 0 GridFS bytes read
    status_unpub_view, _hdrs, raw_unpub_view = _http_request(
        base_url,
        f"/api/hexa/v0/shipments/{SHIPMENT_A_ID}",
        session_token=lg_token,
    )
    assert status_unpub_view == 403
    assert json.loads(raw_unpub_view.decode("utf-8")) == {"error": "CUSTOMER_RESOURCE_UNAVAILABLE"}

    status_unpub_dl, _hdrs, _raw = _http_request(
        base_url,
        f"/api/hexa/v0/shipments/{SHIPMENT_A_ID}/documents/DOC-LG-PL/download?version=v2",
        session_token=lg_token,
    )
    assert status_unpub_dl == 403
    assert len(fetch_calls) == 0

    # 3. TT Staff logs in with trial TT staff account
    status_tt_login, hdrs_tt_login, raw_tt_login = _http_request(
        base_url,
        "/api/hexa/v0/tt/auth/login",
        method="POST",
        json_body={"username": "tt.ops.truongthanh", "passcode": "TT-Trial-2026!"},
    )
    assert status_tt_login == 200
    tt_session_info = json.loads(raw_tt_login.decode("utf-8"))
    assert tt_session_info["authenticated"] is True
    assert tt_session_info["principal"]["kind"] == "tt_staff"
    assert tt_session_info["principal"]["username"] == "tt.ops.truongthanh"
    tt_token = _extract_cookie_value(hdrs_tt_login, "hexa_trial_tt_session")
    assert tt_token and tt_token not in ("tt.ops.truongthanh", "sess-internal-viewer")

    # 4. AC2, AC4, AC5: TT inspects internal shipment and approves ONLY:
    #    EVT-LG-01-PICKUP@v1, DOC-LG-PL@v2, and quote Q-LG-ROAD-001@v3
    status_tt_view, _hdrs, raw_tt_view = _http_request(
        base_url,
        f"/api/hexa/v0/tt/shipments/{SHIPMENT_A_ID}",
        session_token=tt_token,
    )
    assert status_tt_view == 200
    tt_desk_data = json.loads(raw_tt_view.decode("utf-8"))
    assert tt_desk_data["shipment"]["shipment_id"] == SHIPMENT_A_ID
    assert tt_desk_data["shipment"]["customer_id"] == CUSTOMER_A_ID

    status_pub, _hdrs, raw_pub = _http_request(
        base_url,
        f"/api/hexa/v0/tt/shipments/{SHIPMENT_A_ID}/publish",
        method="POST",
        session_token=tt_token,
        json_body={
            "event_versions": {
                "EVT-LG-01-PICKUP": "v1",
                # Unverified ETA, internal ETA, and Minh Đức's event must be blocked by server
                "EVT-LG-03-ETA-UNVERIFIED": "v1",
                "EVT-LG-04-ETA-INTERNAL": "v1",
                "EVT-MD-02-SHARED-TRUCK": "v1",
            },
            "document_versions": {
                "DOC-LG-PL": "v2",
                # Internal cost sheet and Minh Đức's document must be blocked by server
                "DOC-LG-COST": "v1",
                "DOC-MD-PL": "v1",
            },
            "quote": {"id": QUOTE_A_ID, "version": "3"},
        },
    )
    assert status_pub == 200
    pub_manifest = json.loads(raw_pub.decode("utf-8"))["publication"]
    assert pub_manifest["state"] == "PUBLISHED"
    assert pub_manifest["approved_by"] == "tt.ops.truongthanh"
    assert pub_manifest["approved_at"]
    assert pub_manifest["event_versions"] == {"EVT-LG-01-PICKUP": "v1"}
    assert pub_manifest["document_versions"] == {"DOC-LG-PL": "v2"}
    assert pub_manifest["quote"] == {"id": QUOTE_A_ID, "version": "3"}

    # LG views the shipment and sees ONLY the approved items (no EVT-LG-02-BORDER, no DOC-LG-PI, no ETA, no internal cost)
    status_lg_view, _hdrs, raw_lg_view = _http_request(
        base_url,
        f"/api/hexa/v0/shipments/{SHIPMENT_A_ID}",
        session_token=lg_token,
    )
    assert status_lg_view == 200
    lg_text = raw_lg_view.decode("utf-8")
    lg_payload = json.loads(lg_text)
    assert lg_payload == {
        "schema": "hexa-customer-publication/v0",
        "reference": SHIPMENT_A_ID,
        "transport_mode": "ROAD",
        "timeline": [
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
        ],
        "quote": {
            "id": QUOTE_A_ID,
            "version": "3",
            "status": "SENT",
            "selling_total_vnd": 57240000.0,
        },
    }
    assert "EVT-LG-02-BORDER" not in lg_text
    assert "DOC-LG-PI" not in lg_text
    assert "2026-10-25" not in lg_text
    for sentinel in TRIAL_SENTINELS:
        assert sentinel not in lg_text

    # Unapproved document DOC-LG-PI@v1 cannot be downloaded (0 GridFS reads)
    status_unapproved_doc, _hdrs, _raw = _http_request(
        base_url,
        f"/api/hexa/v0/shipments/{SHIPMENT_A_ID}/documents/DOC-LG-PI/download?version=v1",
        session_token=lg_token,
    )
    assert status_unapproved_doc == 403
    assert len(fetch_calls) == 0

    # Approved document DOC-LG-PL@v2 CAN be downloaded by LG
    dl_url = f"/api/hexa/v0/shipments/{SHIPMENT_A_ID}/documents/DOC-LG-PL/download?version=v2"
    status_dl_ok, _hdrs_dl_ok, pdf_bytes = _http_request(
        base_url,
        dl_url,
        session_token=lg_token,
    )
    assert status_dl_ok == 200
    assert pdf_bytes.startswith(b"%PDF-1.4")
    assert b"HEXA PACKING LIST v2" in pdf_bytes
    assert len(fetch_calls) == 1

    # 5. AC3: TT revokes document DOC-LG-PL -> LG cannot download it anymore even using the exact old URL
    status_revoke_doc, _hdrs, raw_revoke_doc = _http_request(
        base_url,
        f"/api/hexa/v0/tt/shipments/{SHIPMENT_A_ID}/revoke",
        method="POST",
        session_token=tt_token,
        json_body={"document_ids": ["DOC-LG-PL"]},
    )
    assert status_revoke_doc == 200
    after_doc_revoke = json.loads(raw_revoke_doc.decode("utf-8"))["publication"]
    assert after_doc_revoke["document_versions"] == {}
    assert after_doc_revoke["revoked_by"] == "tt.ops.truongthanh"
    assert after_doc_revoke["revoked_at"]

    status_dl_after_revoke, _hdrs, raw_dl_after_revoke = _http_request(
        base_url,
        dl_url,
        session_token=lg_token,
    )
    assert status_dl_after_revoke == 403
    assert json.loads(raw_dl_after_revoke.decode("utf-8")) == {"error": "CUSTOMER_RESOURCE_UNAVAILABLE"}
    # Zero additional GridFS reads after revocation!
    assert len(fetch_calls) == 1


def test_v1_minh_duc_separate_login_and_strict_cross_tenant_and_role_boundaries(
    trial_server,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC6, AC7, AC8: Minh Đức separate login, Logistics viewer rejection, and TT publish/revoke authorization boundary."""
    base_url, env = trial_server

    real_fetch = core_att.fetch_attachment_bytes
    fetch_calls: list[tuple[Any, Any]] = []

    def _spy_fetch(record_or_id: Any, *, shipment_id: Any = None) -> dict[str, Any]:
        fetch_calls.append((record_or_id, shipment_id))
        return real_fetch(record_or_id, shipment_id=shipment_id)

    monkeypatch.setattr(core_att, "fetch_attachment_bytes", _spy_fetch)
    _tt_login_and_publish_standard_fixtures(base_url)

    # 1. Minh Đức logs in with separate trial customer account
    status_md_login, hdrs_md_login, raw_md_login = _http_request(
        base_url,
        "/api/hexa/v0/auth/login",
        method="POST",
        json_body={
            "username": "minhduc.trial",
            "passcode": "MD-Trial-2026!",
            "customer_id": CUSTOMER_A_ID,  # Attempted tampering ignored
        },
    )
    assert status_md_login == 200
    md_info = json.loads(raw_md_login.decode("utf-8"))
    assert md_info["principal"]["customer_id"] == CUSTOMER_B_ID
    md_token = _extract_cookie_value(hdrs_md_login, TRIAL_COOKIE_NAME)
    assert md_token

    # Minh Đức can view own shipment ROAD-MD-002
    status_md_own, _hdrs, raw_md_own = _http_request(
        base_url,
        f"/api/hexa/v0/shipments/{SHIPMENT_B_ID}",
        session_token=md_token,
    )
    assert status_md_own == 200
    assert json.loads(raw_md_own.decode("utf-8"))["reference"] == SHIPMENT_B_ID

    # Minh Đức CANNOT view Lục Giác's shipment or download Lục Giác's document (0 GridFS bytes read)
    status_md_lg, _hdrs, _raw = _http_request(
        base_url,
        f"/api/hexa/v0/shipments/{SHIPMENT_A_ID}?customer_id={CUSTOMER_A_ID}",
        session_token=md_token,
        headers={"X-Customer-Id": CUSTOMER_A_ID},
    )
    assert status_md_lg == 403
    status_md_lg_dl, _hdrs, _raw = _http_request(
        base_url,
        f"/api/hexa/v0/shipments/{SHIPMENT_A_ID}/documents/DOC-LG-PL/download?version=v2",
        session_token=md_token,
    )
    assert status_md_lg_dl == 403
    assert len(fetch_calls) == 0

    # 2. AC7: Logistics 'viewer' account and wrong passwords CANNOT log into customer portal or TT publish desk
    for bad_login_path in ("/api/hexa/v0/auth/login", "/api/hexa/v0/tt/auth/login"):
        for bad_creds in (
            {"username": "tt.viewer", "passcode": "Viewer-Trial-2026!"},
            {"username": "lucgiac.trial", "passcode": "wrong-passcode"},
            {"username": "unknown.user", "passcode": "TT-Trial-2026!"},
        ):
            st_bad, hdrs_bad, _ = _http_request(
                base_url,
                bad_login_path,
                method="POST",
                json_body=bad_creds,
            )
            assert st_bad == 403
            assert "Set-Cookie" not in hdrs_bad

    # Customer credentials CANNOT log into TT staff publish desk
    st_cust_on_tt, hdrs_cust_on_tt, _ = _http_request(
        base_url,
        "/api/hexa/v0/tt/auth/login",
        method="POST",
        json_body={"username": "lucgiac.trial", "passcode": "LG-Trial-2026!"},
    )
    assert st_cust_on_tt == 403
    assert "Set-Cookie" not in hdrs_cust_on_tt

    # 3. AC8: Customers, Logistics viewer, anonymous, and sample tokens CANNOT call TT publish/revoke/inspect endpoints
    token_a = _server_issued_token(env, "customer_a", "sess-customer-lg")
    token_viewer = _server_issued_token(env, "internal_viewer", "sess-internal-viewer")
    for unauthorized_token in (None, token_a, md_token, token_viewer, "sess-customer-lg", "tt.ops.truongthanh"):
        st_get_tt, _, _ = _http_request(
            base_url,
            f"/api/hexa/v0/tt/shipments/{SHIPMENT_A_ID}",
            session_token=unauthorized_token,
        )
        assert st_get_tt == 403

        st_pub_tt, _, _ = _http_request(
            base_url,
            f"/api/hexa/v0/tt/shipments/{SHIPMENT_A_ID}/publish",
            method="POST",
            session_token=unauthorized_token,
            json_body={
                "event_versions": {"EVT-LG-01-PICKUP": "v1"},
                "document_versions": {"DOC-LG-PL": "v2"},
                "quote": {"id": QUOTE_A_ID, "version": "3"},
            },
        )
        assert st_pub_tt == 403

        st_rev_tt, _, _ = _http_request(
            base_url,
            f"/api/hexa/v0/tt/shipments/{SHIPMENT_A_ID}/revoke",
            method="POST",
            session_token=unauthorized_token,
            json_body={},
        )
        assert st_rev_tt == 403


def test_dashboard_v1_default_deny_publish_journey_and_revoke_lifecycle(
    trial_server,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Dashboard V1 AC1, AC2, AC4: Default-deny empty dashboard -> TT publish -> dashboard summary, row fields, Journey map & unverified ETA guard -> TT revoke clears dashboard & blocks download."""
    base_url, env = trial_server

    real_fetch = core_att.fetch_attachment_bytes
    fetch_calls: list[tuple[Any, Any]] = []

    def _spy_fetch(record_or_id: Any, *, shipment_id: Any = None) -> dict[str, Any]:
        fetch_calls.append((record_or_id, shipment_id))
        return real_fetch(record_or_id, shipment_id=shipment_id)

    monkeypatch.setattr(core_att, "fetch_attachment_bytes", _spy_fetch)

    # 1. Anonymous and viewer cannot read customer dashboard
    st_anon, _, _ = _http_request(base_url, "/api/hexa/v0/dashboard")
    assert st_anon == 403
    token_viewer = _server_issued_token(env, "internal_viewer", "sess-internal-viewer")
    st_viewer, _, _ = _http_request(base_url, "/api/hexa/v0/dashboard", session_token=token_viewer)
    assert st_viewer == 403

    # 2. Customer Lục Giác logs in BEFORE TT publishes -> dashboard is empty (default-deny)
    st_lg_login, hdrs_lg, _ = _http_request(
        base_url,
        "/api/hexa/v0/auth/login",
        method="POST",
        json_body={"username": "lucgiac.trial", "passcode": "LG-Trial-2026!"},
    )
    assert st_lg_login == 200
    lg_token = _extract_cookie_value(hdrs_lg, TRIAL_COOKIE_NAME)

    st_dash_0, _, raw_dash_0 = _http_request(
        base_url,
        "/api/hexa/v0/dashboard",
        session_token=lg_token,
    )
    assert st_dash_0 == 200
    dash_0 = json.loads(raw_dash_0.decode("utf-8"))
    assert dash_0["summary"]["active_tracking"] == 0
    assert dash_0["summary"]["verified_warehouse_eta_count"] == 0
    assert dash_0["summary"]["arriving_soon"] == 0
    assert dash_0["summary"]["customer_action_needed"] == 0
    assert dash_0["summary"]["customer_action_status_label"] == "Chưa có yêu cầu được xác nhận"
    assert dash_0["summary"]["total_published"] == 0
    assert dash_0["shipments"] == []

    # 3. TT logs in and publishes ROAD-LG-001 (with pickup + border events, PL v2, and quote)
    st_tt_login, hdrs_tt, _ = _http_request(
        base_url,
        "/api/hexa/v0/tt/auth/login",
        method="POST",
        json_body={"username": "tt.ops.truongthanh", "passcode": "TT-Trial-2026!"},
    )
    assert st_tt_login == 200
    tt_token = _extract_cookie_value(hdrs_tt, TRIAL_TT_COOKIE_NAME)

    st_pub, _, _ = _http_request(
        base_url,
        f"/api/hexa/v0/tt/shipments/{SHIPMENT_A_ID}/publish",
        method="POST",
        session_token=tt_token,
        json_body={
            "event_versions": {
                "EVT-LG-01-PICKUP": "v1",
                "EVT-LG-02-BORDER": "v2",
            },
            "document_versions": {
                "DOC-LG-PL": "v2",
            },
            "quote": {"id": QUOTE_A_ID, "version": "3"},
        },
    )
    assert st_pub == 200

    # 4. Customer Lục Giác reloads dashboard -> sees published shipment + Journey + documents
    st_dash_1, _, raw_dash_1 = _http_request(
        base_url,
        "/api/hexa/v0/dashboard",
        session_token=lg_token,
    )
    assert st_dash_1 == 200
    dash_1_text = raw_dash_1.decode("utf-8")
    dash_1 = json.loads(dash_1_text)

    # ROAD-LG-001 is at border without verified warehouse ETA, and has no confirmed open customer action:
    # - verified_warehouse_eta_count / arriving_soon MUST be 0 (not inferred from border stage)
    # - customer_action_needed MUST be 0 (not inferred from having published docs/quote)
    assert dash_1["summary"]["active_tracking"] == 1
    assert dash_1["summary"]["verified_warehouse_eta_count"] == 0
    assert dash_1["summary"]["arriving_soon"] == 0
    assert dash_1["summary"]["customer_action_needed"] == 0
    assert dash_1["summary"]["customer_action_status_label"] == "Chưa có yêu cầu được xác nhận"
    assert dash_1["summary"]["total_published"] == 1
    assert len(dash_1["shipments"]) == 1
    row = dash_1["shipments"][0]
    assert row["shipment_id"] == SHIPMENT_A_ID
    assert row["transport_mode"] == "ROAD"
    assert "18 kiện" in row["cargo_summary"]
    assert row["verified_stage_id"] == "road-border"
    assert "Hữu Nghị" in row["verified_stage_title"]
    assert row["last_updated_at"] == "2026-10-21T14:15:00Z"
    # AC4: Unverified internal ETA (2026-10-25) MUST NOT be exposed as verified warehouse ETA, and shipment is NOT completed by default
    assert row["verified_warehouse_eta"] is None
    assert row["verified_warehouse_eta_label"] == "Chưa xác minh"
    assert row["is_complete"] is False
    assert row["needs_customer_action"] is False
    assert row["customer_action"] is None
    assert row["next_step"]
    assert row["contact_point"]
    assert "2026-10-25" not in dash_1_text
    for sentinel in TRIAL_SENTINELS:
        assert sentinel not in dash_1_text

    # Journey nodes reuse core/shipment_journey.py structure filtered strictly by published verified events
    journey_nodes = {n["id"]: n for n in row["journey"]["nodes"]}
    assert journey_nodes["pickup"]["completed"] is True
    assert journey_nodes["road-border"]["completed"] is True
    assert journey_nodes["road-border"]["current"] is True
    assert journey_nodes["customs-import"]["completed"] is False
    assert journey_nodes["delivery"]["completed"] is False

    # Clicking shipment opens Journey & exact published document version (DOC-LG-PL@v2)
    assert row["documents"] == [
        {
            "id": "DOC-LG-PL",
            "version": "v2",
            "kind": "PL",
            "title": "Packing List Lục Giác (Bản v2 đã duyệt)",
        }
    ]
    st_dl, _, pdf_bytes = _http_request(
        base_url,
        f"/api/hexa/v0/shipments/{SHIPMENT_A_ID}/documents/DOC-LG-PL/download?version=v2",
        session_token=lg_token,
    )
    assert st_dl == 200
    assert pdf_bytes.startswith(b"%PDF-1.4")
    assert len(fetch_calls) == 1

    # 5. AC2: TT revokes publication -> shipment disappears from dashboard and document download is blocked
    st_rev, _, _ = _http_request(
        base_url,
        f"/api/hexa/v0/tt/shipments/{SHIPMENT_A_ID}/revoke",
        method="POST",
        session_token=tt_token,
        json_body={},
    )
    assert st_rev == 200

    st_dash_2, _, raw_dash_2 = _http_request(
        base_url,
        "/api/hexa/v0/dashboard",
        session_token=lg_token,
    )
    assert st_dash_2 == 200
    dash_2 = json.loads(raw_dash_2.decode("utf-8"))
    assert dash_2["summary"]["total_published"] == 0
    assert dash_2["shipments"] == []

    st_dl_revoked, _, _ = _http_request(
        base_url,
        f"/api/hexa/v0/shipments/{SHIPMENT_A_ID}/documents/DOC-LG-PL/download?version=v2",
        session_token=lg_token,
    )
    assert st_dl_revoked == 403
    assert len(fetch_calls) == 1


def test_dashboard_v1_multi_tenant_reuse_across_three_customers_without_hardcoding(
    trial_server,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Dashboard V1 AC1, AC3, AC4: Reusable dashboard pipeline across 3 trial customers (Lục Giác, Minh Đức, An Phát) with strict cross-customer isolation and verified ETA gate."""
    base_url, _env = trial_server

    real_fetch = core_att.fetch_attachment_bytes
    fetch_calls: list[tuple[Any, Any]] = []

    def _spy_fetch(record_or_id: Any, *, shipment_id: Any = None) -> dict[str, Any]:
        fetch_calls.append((record_or_id, shipment_id))
        return real_fetch(record_or_id, shipment_id=shipment_id)

    monkeypatch.setattr(core_att, "fetch_attachment_bytes", _spy_fetch)

    # TT logs in and publishes shipments for all 3 trial customers:
    # - Customer A (Lục Giác): ROAD-LG-001
    # - Customer B (Minh Đức, shared truck with A): ROAD-MD-002
    # - Customer C (An Phát, 3rd customer): ROAD-AP-003 (first with only pickup event, then with verified ETA customs event)
    st_tt, hdrs_tt, _ = _http_request(
        base_url,
        "/api/hexa/v0/tt/auth/login",
        method="POST",
        json_body={"username": "tt.ops.truongthanh", "passcode": "TT-Trial-2026!"},
    )
    assert st_tt == 200
    tt_token = _extract_cookie_value(hdrs_tt, TRIAL_TT_COOKIE_NAME)

    _tt_login_and_publish_standard_fixtures(base_url)

    # Publish Customer C (ROAD-AP-003) initially with ONLY pickup event (no verified warehouse ETA yet)
    st_pub_c1, _, _ = _http_request(
        base_url,
        "/api/hexa/v0/tt/shipments/ROAD-AP-003/publish",
        method="POST",
        session_token=tt_token,
        json_body={
            "event_versions": {"EVT-AP-01-PICKUP": "v1"},
            "document_versions": {"DOC-AP-PL": "v1"},
            "quote": {"id": "Q-AP-ROAD-003", "version": "3"},
        },
    )
    assert st_pub_c1 == 200

    # Login all 3 customers
    tokens: dict[str, str] = {}
    for key, creds, expected_cust_id in (
        ("A", {"username": "lucgiac.trial", "passcode": "LG-Trial-2026!"}, CUSTOMER_A_ID),
        ("B", {"username": "minhduc.trial", "passcode": "MD-Trial-2026!"}, CUSTOMER_B_ID),
        ("C", {"username": "anphat.trial", "passcode": "AP-Trial-2026!"}, "CUST-ANPHAT"),
    ):
        st_login, hdrs_login, raw_login = _http_request(
            base_url,
            "/api/hexa/v0/auth/login",
            method="POST",
            json_body=creds,
        )
        assert st_login == 200
        info = json.loads(raw_login.decode("utf-8"))
        assert info["principal"]["customer_id"] == expected_cust_id
        tokens[key] = _extract_cookie_value(hdrs_login, TRIAL_COOKIE_NAME)

    # Verify each customer's dashboard contains ONLY their own published shipment, even if tampering query/header
    expected_map = {
        "A": (SHIPMENT_A_ID, CUSTOMER_A_ID, [SHIPMENT_B_ID, "ROAD-AP-003"], ["DOC-MD-PL", "DOC-AP-PL"]),
        "B": (SHIPMENT_B_ID, CUSTOMER_B_ID, [SHIPMENT_A_ID, "ROAD-AP-003"], ["DOC-LG-PL", "DOC-AP-PL"]),
        "C": ("ROAD-AP-003", "CUST-ANPHAT", [SHIPMENT_A_ID, SHIPMENT_B_ID], ["DOC-LG-PL", "DOC-MD-PL"]),
    }
    for key, (own_sid, _own_cid, foreign_sids, foreign_docs) in expected_map.items():
        st_d, _, raw_d = _http_request(
            base_url,
            f"/api/hexa/v0/dashboard?customer_id={CUSTOMER_A_ID}",
            session_token=tokens[key],
            headers={"X-Customer-Id": CUSTOMER_A_ID},
        )
        assert st_d == 200
        d_payload = json.loads(raw_d.decode("utf-8"))
        assert [s["shipment_id"] for s in d_payload["shipments"]] == [own_sid]
        d_text = raw_d.decode("utf-8")
        for f_sid in foreign_sids:
            assert f_sid not in d_text
            st_f, _, _ = _http_request(
                base_url,
                f"/api/hexa/v0/shipments/{f_sid}",
                session_token=tokens[key],
            )
            assert st_f == 403
        for f_doc in foreign_docs:
            assert f_doc not in d_text

    # Customer C (An Phát): with only EVT-AP-01-PICKUP published, verified_warehouse_eta is None
    st_c_dash1, _, raw_c_dash1 = _http_request(
        base_url,
        "/api/hexa/v0/dashboard",
        session_token=tokens["C"],
    )
    assert st_c_dash1 == 200
    c_dash_1 = json.loads(raw_c_dash1.decode("utf-8"))
    assert c_dash_1["summary"]["verified_warehouse_eta_count"] == 0
    assert c_dash_1["summary"]["arriving_soon"] == 0
    assert c_dash_1["summary"]["customer_action_needed"] == 0
    c_row_1 = c_dash_1["shipments"][0]
    assert c_row_1["shipment_id"] == "ROAD-AP-003"
    assert c_row_1["verified_stage_id"] == "pickup"
    assert c_row_1["verified_warehouse_eta"] is None
    assert c_row_1["verified_warehouse_eta_label"] == "Chưa xác minh"
    assert c_row_1["is_complete"] is False
    assert c_row_1["needs_customer_action"] is False

    # Now TT publishes EVT-AP-02-CUSTOMS@v1 (which has TT-verified warehouse ETA 2026-10-23)
    st_pub_c2, _, _ = _http_request(
        base_url,
        "/api/hexa/v0/tt/shipments/ROAD-AP-003/publish",
        method="POST",
        session_token=tt_token,
        json_body={
            "event_versions": {
                "EVT-AP-01-PICKUP": "v1",
                "EVT-AP-02-CUSTOMS": "v1",
            },
            "document_versions": {"DOC-AP-PL": "v1"},
            "quote": {"id": "Q-AP-ROAD-003", "version": "3"},
        },
    )
    assert st_pub_c2 == 200

    st_c_dash2, _, raw_c_dash2 = _http_request(
        base_url,
        "/api/hexa/v0/dashboard",
        session_token=tokens["C"],
    )
    assert st_c_dash2 == 200
    c_dash_2 = json.loads(raw_c_dash2.decode("utf-8"))
    assert c_dash_2["summary"]["verified_warehouse_eta_count"] == 1
    assert c_dash_2["summary"]["arriving_soon"] == 1
    assert c_dash_2["summary"]["customer_action_needed"] == 0
    c_row_2 = c_dash_2["shipments"][0]
    assert c_row_2["verified_stage_id"] == "customs-import"
    assert c_row_2["verified_warehouse_eta"] == "2026-10-23"
    assert "2026-10-23" in c_row_2["verified_warehouse_eta_label"]
    assert c_row_2["is_complete"] is False
    assert c_row_2["needs_customer_action"] is False

    # Customer C can download own published PDF DOC-AP-PL@v1
    st_c_dl, _, c_pdf = _http_request(
        base_url,
        "/api/hexa/v0/shipments/ROAD-AP-003/documents/DOC-AP-PL/download?version=v1",
        session_token=tokens["C"],
    )
    assert st_c_dl == 200
    assert c_pdf.startswith(b"%PDF-1.4")
    assert b"AN PHAT PACKING LIST v1" in c_pdf


def test_dashboard_v1_kpi_truth_and_safe_dom_rendering_against_html_script_injection(
    trial_server,
) -> None:
    """HEXA-DASHBOARD-V1-TRUTH-CLOSURE:
    1. 'Cần khách xử lý' is NOT inferred from having published docs/quote; only counts open, verified customer action requirements with responsible_party and action_text.
    2. 'Có ETA kho đã xác minh' is NOT inferred from border stage; only counts shipments with TT-verified & published warehouse ETA.
    3. Client DOM rendering uses textContent/safe DOM creation so HTML/script in shipment fields is rendered strictly as plain text, never parsed as HTML/script.
    """
    from core import database as core_db

    base_url, _env = trial_server
    _tt_login_and_publish_standard_fixtures(base_url)

    st_lg_login, hdrs_lg, _ = _http_request(
        base_url,
        "/api/hexa/v0/auth/login",
        method="POST",
        json_body={"username": "lucgiac.trial", "passcode": "LG-Trial-2026!"},
    )
    assert st_lg_login == 200
    lg_token = _extract_cookie_value(hdrs_lg, TRIAL_COOKIE_NAME)

    # 1. ROAD-LG-001 has published docs (PL v2, PI v1), published quote (Q-LG-ROAD-001 v3),
    # and border stage (EVT-LG-02-BORDER v2), but NO verified warehouse ETA and NO customer action item.
    st_d1, _, raw_d1 = _http_request(base_url, "/api/hexa/v0/dashboard", session_token=lg_token)
    assert st_d1 == 200
    d1 = json.loads(raw_d1.decode("utf-8"))
    assert d1["summary"]["active_tracking"] == 1
    assert d1["summary"]["arriving_soon"] == 0
    assert d1["summary"]["customer_action_needed"] == 0
    assert d1["summary"]["verified_warehouse_eta_count"] == 0
    assert d1["summary"]["arriving_soon_label"] == "Có ETA kho đã xác minh"
    assert d1["summary"]["customer_action_status_label"] == "Chưa có yêu cầu được xác nhận"
    row_1 = d1["shipments"][0]
    assert row_1["verified_stage_id"] == "road-border"
    assert row_1["verified_warehouse_eta"] is None
    assert row_1["needs_customer_action"] is False
    assert row_1["customer_action"] is None

    # 2. Internal TT tasks (on shipment.tasks or link.customer_actions assigned to TT staff),
    # cross-customer actions, and unapproved/unpublished customer_actions MUST NEVER appear or increment KPI!
    db = core_db.get_db()
    assert db is not None
    db["shipments"].update_one(
        {"id": SHIPMENT_A_ID},
        {
            "$set": {
                "tasks": [
                    {
                        "id": "TSK-TT-INTERNAL-01",
                        "status": "OPEN",
                        "verified": True,
                        "assignee": "tt.ops.truongthanh",
                        "responsible_party": "Nhân sự điều vận Trường Thành",
                        "content": "INTERNAL_TT_TASK_MUST_NEVER_LEAK",
                    }
                ]
            }
        },
    )
    db["hexa_trial_shipment_links"].update_one(
        {"shipment_id": SHIPMENT_A_ID, "customer_id": CUSTOMER_A_ID},
        {
            "$set": {
                "customer_actions": [
                    {
                        "id": "ACT-TT-STAFF-01",
                        "status": "OPEN",
                        "verified": True,
                        "customer_id": CUSTOMER_A_ID,
                        "responsible_side": "TT",
                        "responsible_party": "Nhân sự chứng từ Trường Thành (tt.ops.truongthanh)",
                        "action_text": "INTERNAL_TT_ACTION_MUST_NEVER_LEAK",
                    },
                    {
                        "id": "ACT-OTHER-CUST-01",
                        "status": "OPEN",
                        "verified": True,
                        "customer_id": CUSTOMER_B_ID,
                        "responsible_side": "CUSTOMER",
                        "responsible_party": "Khách hàng Minh Đức",
                        "action_text": "FOREIGN_CUSTOMER_ACTION_MUST_NEVER_LEAK",
                    },
                    {
                        "id": "ACT-LG-UNPUBLISHED-01",
                        "status": "OPEN",
                        "verified": True,
                        "customer_id": CUSTOMER_A_ID,
                        "responsible_side": "CUSTOMER",
                        "responsible_party": "Bộ phận XNK Lục Giác",
                        "action_text": "UNPUBLISHED_CUSTOMER_ACTION_MUST_NEVER_LEAK",
                    },
                ]
            }
        },
    )
    st_d2, _, raw_d2 = _http_request(base_url, "/api/hexa/v0/dashboard", session_token=lg_token)
    assert st_d2 == 200
    d2_text = raw_d2.decode("utf-8")
    d2 = json.loads(d2_text)
    assert d2["summary"]["customer_action_needed"] == 0
    assert d2["summary"]["customer_action_status_label"] == "Chưa có yêu cầu được xác nhận"
    assert d2["shipments"][0]["needs_customer_action"] is False
    assert d2["shipments"][0]["customer_action"] is None
    assert "INTERNAL_TT_TASK_MUST_NEVER_LEAK" not in d2_text
    assert "INTERNAL_TT_ACTION_MUST_NEVER_LEAK" not in d2_text
    assert "FOREIGN_CUSTOMER_ACTION_MUST_NEVER_LEAK" not in d2_text
    assert "UNPUBLISHED_CUSTOMER_ACTION_MUST_NEVER_LEAK" not in d2_text

    # Restore clean V1 state
    db["shipments"].update_one({"id": SHIPMENT_A_ID}, {"$unset": {"tasks": ""}})
    db["hexa_trial_shipment_links"].update_one(
        {"shipment_id": SHIPMENT_A_ID, "customer_id": CUSTOMER_A_ID},
        {"$unset": {"customer_actions": ""}},
    )


def test_dashboard_v1_safe_dom_rendering_blocks_html_script_execution_in_shipment_fields(
    trial_server,
) -> None:
    """HEXA-DASHBOARD-V1-TRUTH-CLOSURE (Việc 3):
    Verify client DOM rendering uses textContent/safe DOM creation (not innerHTML interpolation)
    for cargo_summary, route_summary, next_step, contact_point, shipment_id, verified_stage_label,
    verified_stage_title, and Journey/timeline/document titles so HTML/script payloads are rendered
    strictly as plain text and never parsed/executed as HTML.
    """
    import subprocess
    from core import database as core_db

    base_url, _env = trial_server
    _tt_login_and_publish_standard_fixtures(base_url)

    st_html, _, raw_html = _http_request(base_url, "/")
    assert st_html == 200
    html_text = raw_html.decode("utf-8")
    assert "Có ETA kho đã xác minh" in html_text
    assert "Chưa có yêu cầu được xác nhận" in html_text

    forbidden_innerhtml_interpolations = [
        "${row.cargo_summary}",
        "${row.route_summary}",
        "${row.next_step}",
        "${row.contact_point}",
        "${row.shipment_id}",
        "${row.verified_stage_label}",
        "${row.verified_stage_title}",
        "${n.label}",
        "${n.evidence}",
        "${ev.title}",
        "${doc.title}",
    ]
    for pattern in forbidden_innerhtml_interpolations:
        assert pattern not in html_text, f"Unsafe HTML interpolation found in template: {pattern}"

    # Inject HTML/script payloads into shipment link & event title and verify via API + Node DOM execution
    # that they are treated strictly as textContent and never assigned to innerHTML.
    xss_payload = '<img src=x onerror="globalThis.__xss_fired=1"><script>globalThis.__xss_fired=1</script>'
    db = core_db.get_db()
    assert db is not None
    db["hexa_trial_shipment_links"].update_one(
        {"shipment_id": SHIPMENT_A_ID, "customer_id": CUSTOMER_A_ID},
        {
            "$set": {
                "cargo_summary": f"18 kiện gỗ {xss_payload}",
                "route_summary": f"Foshan -> Hà Nội {xss_payload}",
            }
        },
    )

    st_lg_login, hdrs_lg, _ = _http_request(
        base_url,
        "/api/hexa/v0/auth/login",
        method="POST",
        json_body={"username": "lucgiac.trial", "passcode": "LG-Trial-2026!"},
    )
    assert st_lg_login == 200
    lg_token = _extract_cookie_value(hdrs_lg, TRIAL_COOKIE_NAME)

    st_dash, _, raw_dash = _http_request(base_url, "/api/hexa/v0/dashboard", session_token=lg_token)
    assert st_dash == 200
    dash_json = raw_dash.decode("utf-8")

    # Execute the actual client JS rendering functions from the served HTML inside a Node VM DOM spy
    # that throws if any dynamic shipment string containing `<script>` or `<img` is ever passed to `.innerHTML`.
    node_check_script = r"""
const fs = require('fs');
const vm = require('vm');
const html = fs.readFileSync(process.env.HTML_PATH, 'utf8');
const dashData = JSON.parse(fs.readFileSync(process.env.DASH_PATH, 'utf8'));
const scriptMatch = html.match(/<script>([\s\S]*?)<\/script>/);
if (!scriptMatch) {
  console.error('NO_SCRIPT_TAG');
  process.exit(2);
}
let innerHtmlViolations = [];
function makeEl(tag) {
  let _inner = '';
  let _text = '';
  const el = {
    tagName: (tag || 'div').toUpperCase(),
    style: {},
    dataset: {},
    className: '',
    value: '',
    children: [],
    classList: { toggle() {}, add() {}, remove() {} },
    appendChild(child) { this.children.push(child); return child; },
    addEventListener(ev, fn) { this['on' + ev] = fn; },
    setAttribute(k, v) { this[k] = v; },
    get textContent() {
      if (this.children.length > 0) {
        return _text + this.children.map(c => c.textContent).join(' ');
      }
      return _text;
    },
    set textContent(v) {
      _text = String(v ?? '');
      this.children = [];
    },
    get innerHTML() { return _inner; },
    set innerHTML(v) {
      const s = String(v ?? '');
      if (s.includes('<script') || s.includes('onerror=') || s.includes('<img')) {
        innerHtmlViolations.push(s);
      }
      _inner = s;
      if (s === '') { this.children = []; _text = ''; }
    }
  };
  return el;
}
const elements = {};
const document = {
  getElementById(id) {
    if (!elements[id]) elements[id] = makeEl('div');
    return elements[id];
  },
  createElement(tag) { return makeEl(tag); },
  querySelectorAll() { return []; },
  body: makeEl('body')
};
const window = { addEventListener() {} };
const sandbox = {
  document,
  window,
  Intl,
  encodeURIComponent,
  JSON,
  String,
  Array,
  Object,
  console,
  fetch: async (url) => {
    if (url === '/api/hexa/v0/dashboard') {
      return { ok: true, status: 200, json: async () => dashData };
    }
    const row = dashData.shipments[0];
    return {
      ok: true,
      status: 200,
      json: async () => ({
        schema: 'hexa-customer-publication/v0',
        reference: row.shipment_id,
        transport_mode: row.transport_mode,
        timeline: row.timeline.map(e => ({ ...e, title: e.title + ' <script>evil()</script>' })),
        documents: row.documents.map(d => ({ ...d, title: d.title + ' <img src=x onerror=evil()>' })),
        quote: row.quote
      })
    };
  }
};
vm.createContext(sandbox);
vm.runInContext(scriptMatch[1], sandbox);
(async () => {
  await sandbox.loadCustomerDashboard();
  await sandbox.loadShipment(dashData.shipments[0].shipment_id);
  if (innerHtmlViolations.length > 0) {
    console.error('UNSAFE_INNERHTML:', JSON.stringify(innerHtmlViolations));
    process.exit(1);
  }
  const tbodyText = elements['dash-shipments-tbody'].textContent;
  if (!tbodyText.includes('<script>globalThis.__xss_fired=1</script>')) {
    console.error('TEXTCONTENT_MISSING_LITERAL:', tbodyText);
    process.exit(1);
  }
  console.log('SAFE_DOM_RENDER_OK');
})();
"""
    import tempfile
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".html", delete=False) as fh_html, \
         tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False) as fh_json:
        fh_html.write(html_text)
        fh_json.write(dash_json)
        html_path = fh_html.name
        json_path = fh_json.name

    proc = subprocess.run(
        ["node", "-e", node_check_script],
        env={"PATH": "/usr/local/bin:/usr/bin:/bin", "HTML_PATH": html_path, "DASH_PATH": json_path},
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, f"Node DOM safety check failed: {proc.stdout} {proc.stderr}"
    assert "SAFE_DOM_RENDER_OK" in proc.stdout


def test_journey_ui_fidelity_pickup_does_not_mark_road_ltl_completed_and_stage_truth(
    trial_server,
) -> None:
    """HEXA-CUSTOMER-JOURNEY-UI-FIDELITY:
    1. A 'pickup' event MUST NEVER automatically mark 'road-ltl' (consolidation) as completed.
    2. Completing 'pickup' or 'road-border' without a verified 'road-ltl' event leaves 'road-ltl' in UPCOMING (completed=False).
    3. Customer journey payload includes node state aligned with JourneyMap (COMPLETED, CURRENT, UPCOMING) and SVG edges.
    """
    base_url, _env = trial_server

    st_tt, hdrs_tt, _ = _http_request(
        base_url,
        "/api/hexa/v0/tt/auth/login",
        method="POST",
        json_body={"username": "tt.ops.truongthanh", "passcode": "TT-Trial-2026!"},
    )
    assert st_tt == 200
    tt_token = _extract_cookie_value(hdrs_tt, TRIAL_TT_COOKIE_NAME)

    # 1. Publish ONLY pickup event for ROAD-LG-001
    st_pub_pickup_only, _, _ = _http_request(
        base_url,
        f"/api/hexa/v0/tt/shipments/{SHIPMENT_A_ID}/publish",
        method="POST",
        session_token=tt_token,
        json_body={
            "event_versions": {"EVT-LG-01-PICKUP": "v1"},
            "document_versions": {"DOC-LG-PL": "v2"},
            "quote": {"id": QUOTE_A_ID, "version": "3"},
        },
    )
    assert st_pub_pickup_only == 200

    st_lg, hdrs_lg, _ = _http_request(
        base_url,
        "/api/hexa/v0/auth/login",
        method="POST",
        json_body={"username": "lucgiac.trial", "passcode": "LG-Trial-2026!"},
    )
    assert st_lg == 200
    lg_token = _extract_cookie_value(hdrs_lg, TRIAL_COOKIE_NAME)

    st_d1, _, raw_d1 = _http_request(base_url, "/api/hexa/v0/dashboard", session_token=lg_token)
    assert st_d1 == 200
    d1 = json.loads(raw_d1.decode("utf-8"))
    nodes_1 = {n["id"]: n for n in d1["shipments"][0]["journey"]["nodes"]}

    assert nodes_1["pickup"]["completed"] is True
    assert nodes_1["pickup"]["current"] is True
    assert nodes_1["pickup"]["state"] == "CURRENT"
    # CRITICAL REGRESSION: pickup does NOT prove LTL consolidation is complete!
    assert nodes_1["road-ltl"]["completed"] is False
    assert nodes_1["road-ltl"]["current"] is False
    assert nodes_1["road-ltl"]["state"] == "UPCOMING"
    assert nodes_1["road-border"]["completed"] is False
    assert nodes_1["customs-import"]["completed"] is False
    assert nodes_1["delivery"]["completed"] is False

    # 2. Publish pickup + road-border (still no road-ltl event)
    _tt_login_and_publish_standard_fixtures(base_url)
    st_d2, _, raw_d2 = _http_request(base_url, "/api/hexa/v0/dashboard", session_token=lg_token)
    assert st_d2 == 200
    d2 = json.loads(raw_d2.decode("utf-8"))
    journey_2 = d2["shipments"][0]["journey"]
    nodes_2 = {n["id"]: n for n in journey_2["nodes"]}

    assert nodes_2["pickup"]["completed"] is True
    assert nodes_2["pickup"]["current"] is False
    assert nodes_2["pickup"]["state"] == "COMPLETED"
    assert nodes_2["road-ltl"]["completed"] is False
    assert nodes_2["road-ltl"]["current"] is False
    assert nodes_2["road-ltl"]["state"] == "UPCOMING"
    assert nodes_2["road-border"]["completed"] is True
    assert nodes_2["road-border"]["current"] is True
    assert nodes_2["road-border"]["state"] == "CURRENT"
    assert nodes_2["customs-import"]["completed"] is False
    assert nodes_2["customs-import"]["state"] == "UPCOMING"
    assert nodes_2["delivery"]["completed"] is False
    assert nodes_2["delivery"]["state"] == "UPCOMING"
    assert len(journey_2.get("edges") or []) == 4


def test_customer_html_strict_separation_and_reused_journey_assets(
    trial_server,
) -> None:
    """HEXA-CUSTOMER-JOURNEY-UI-FIDELITY:
    1. Customer HTML (GET / and GET /hexa) NEVER contains TT internal screen, role tabs,
       Customer A/B/C buttons, sample passwords, debug JSON, or technical schema/403 dumps.
    2. Real Journey Map assets (vietnam-east-sea-chart.webp, chart-paper.jpg, logi-shell.css) are served.
    3. TT approval desk (/tt) is separated from the customer portal and enforced by server-side auth.
    """
    base_url, _env = trial_server

    for path in ("/", "/hexa"):
        st_html, _, raw_html = _http_request(base_url, path)
        assert st_html == 200
        html_text = raw_html.decode("utf-8")

        forbidden_customer_html_tokens = [
            "Màn hình 1",
            "Nội bộ Trường Thành",
            "screen-tt",
            "tab-btn-tt",
            "switchScreen",
            "/api/hexa/v0/tt/",
            "Khách A",
            "Khách B",
            "Khách C",
            "fillCustomerLogin",
            "LG-Trial-2026!",
            "MD-Trial-2026!",
            "AP-Trial-2026!",
            "TT-Trial-2026!",
            "minhduc.trial",
            "anphat.trial",
            "tt.ops.truongthanh",
            "raw-publication-json",
            "SCHEMA_GAP_REPORT",
            "CUSTOMER_RESOURCE_UNAVAILABLE",
            "HTTP 403",
        ]
        for token in forbidden_customer_html_tokens:
            assert token not in html_text, f"Forbidden token leaked in customer HTML ({path}): {token}"

        # Must reference real reused Journey Map assets and classes
        assert "/assets/journey/vietnam-east-sea-chart.webp" in html_text
        assert "/assets/journey/chart-paper.jpg" in html_text
        assert "/assets/journey/logi-shell.css" in html_text
        assert "journey-map-viewport" in html_text
        assert "journey-sea-chart" in html_text
        assert "journey-bubble" in html_text

    # Reused assets are served over HTTP with exact file bytes
    st_webp, hdrs_webp, raw_webp = _http_request(base_url, "/assets/journey/vietnam-east-sea-chart.webp")
    assert st_webp == 200
    assert "image/webp" in hdrs_webp.get("Content-Type", "")
    assert len(raw_webp) > 50000

    st_jpg, hdrs_jpg, raw_jpg = _http_request(base_url, "/assets/journey/chart-paper.jpg")
    assert st_jpg == 200
    assert "image/jpeg" in hdrs_jpg.get("Content-Type", "")
    assert len(raw_jpg) > 100000

    st_css, hdrs_css, raw_css = _http_request(base_url, "/assets/journey/logi-shell.css")
    assert st_css == 200
    assert "text/css" in hdrs_css.get("Content-Type", "")
    assert b".journey-sea-chart" in raw_css

    # Separated TT page (/tt) requires server-side TT staff authentication
    st_tt_anon, _, _ = _http_request(base_url, "/tt")
    assert st_tt_anon == 403

    st_lg, hdrs_lg, _ = _http_request(
        base_url,
        "/api/hexa/v0/auth/login",
        method="POST",
        json_body={"username": "lucgiac.trial", "passcode": "LG-Trial-2026!"},
    )
    assert st_lg == 200
    lg_token = _extract_cookie_value(hdrs_lg, TRIAL_COOKIE_NAME)
    st_tt_as_cust, _, _ = _http_request(base_url, "/tt", session_token=lg_token)
    assert st_tt_as_cust == 403

    # Authorized TT staff can open /tt after logging in via /tt/login -> /api/hexa/v0/tt/auth/login
    st_tt_login_page, _, _ = _http_request(base_url, "/tt/login")
    assert st_tt_login_page == 200

    st_tt_auth, hdrs_tt, _ = _http_request(
        base_url,
        "/api/hexa/v0/tt/auth/login",
        method="POST",
        json_body={"username": "tt.ops.truongthanh", "passcode": "TT-Trial-2026!"},
    )
    assert st_tt_auth == 200
    tt_token = _extract_cookie_value(hdrs_tt, TRIAL_TT_COOKIE_NAME)
    st_tt_desk, _, raw_tt_desk = _http_request(
        base_url,
        "/tt",
        headers={"Cookie": f"{TRIAL_TT_COOKIE_NAME}={tt_token}"},
    )
    assert st_tt_desk == 200
    assert "Nội bộ Trường Thành" in raw_tt_desk.decode("utf-8")


def test_customer_map_first_dom_states_single_multi_unpublished_and_node_bubble_popup(
    trial_server,
) -> None:
    """HEXA-CUSTOMER-JOURNEY-UI-FIDELITY:
    Verify via Node VM DOM execution that the customer screen:
    - Shows a clean login card when unauthenticated (no HTTP 403 dump);
    - Shows 'Trường Thành chưa công bố thông tin cho lô này' when unpublished or revoked;
    - Auto-opens the Journey Map as the primary screen when 1 published shipment exists;
    - Shows a compact shipment selector when multiple shipments exist;
    - Opens node bubble -> read-only stage popup with verified status, timestamp, published content,
      and downloadable documents (with zero TT data-entry inputs).
    """
    import subprocess
    import tempfile

    base_url, _env = trial_server
    _tt_login_and_publish_standard_fixtures(base_url)

    st_html, _, raw_html = _http_request(base_url, "/")
    assert st_html == 200
    html_text = raw_html.decode("utf-8")

    st_lg, hdrs_lg, _ = _http_request(
        base_url,
        "/api/hexa/v0/auth/login",
        method="POST",
        json_body={"username": "lucgiac.trial", "passcode": "LG-Trial-2026!"},
    )
    assert st_lg == 200
    lg_token = _extract_cookie_value(hdrs_lg, TRIAL_COOKIE_NAME)
    st_dash, _, raw_dash = _http_request(base_url, "/api/hexa/v0/dashboard", session_token=lg_token)
    assert st_dash == 200
    dash_json = raw_dash.decode("utf-8")

    node_dom_script = r"""
const fs = require('fs');
const vm = require('vm');
const html = fs.readFileSync(process.env.HTML_PATH, 'utf8');
const dashData = JSON.parse(fs.readFileSync(process.env.DASH_PATH, 'utf8'));
const scriptMatch = html.match(/<script>([\s\S]*?)<\/script>/);
if (!scriptMatch) { console.error('NO_SCRIPT'); process.exit(2); }

function makeEl(tag) {
  let _text = '';
  const classes = new Set();
  const el = {
    tagName: (tag || 'div').toUpperCase(),
    style: {},
    dataset: {},
    attrs: {},
    value: '',
    children: [],
    className: '',
    classList: {
      add(...cs) { cs.forEach(c => classes.add(c)); el.className = Array.from(classes).join(' '); },
      remove(...cs) { cs.forEach(c => classes.delete(c)); el.className = Array.from(classes).join(' '); },
      toggle(c, force) {
        if (force === undefined) { classes.has(c) ? classes.delete(c) : classes.add(c); }
        else if (force) { classes.add(c); } else { classes.delete(c); }
        el.className = Array.from(classes).join(' ');
      },
      contains(c) { return classes.has(c); }
    },
    appendChild(child) { this.children.push(child); return child; },
    addEventListener(ev, fn) { this['on' + ev] = fn; },
    setAttribute(k, v) { this.attrs[k] = String(v); if (k === 'class') this.className = String(v); },
    getAttribute(k) { return this.attrs[k]; },
    getBoundingClientRect() { return { width: 1200, height: 640, left: 0, top: 0 }; },
    get clientWidth() { return 1200; },
    get clientHeight() { return 640; },
    get textContent() {
      if (this.children.length > 0) return _text + this.children.map(c => c.textContent).join(' ');
      return _text;
    },
    set textContent(v) { _text = String(v ?? ''); this.children = []; },
    set innerHTML(v) { if (v === '') { this.children = []; _text = ''; } }
  };
  return el;
}

const elements = {};
const document = {
  getElementById(id) {
    if (!elements[id]) elements[id] = makeEl('div');
    return elements[id];
  },
  createElement(tag) { return makeEl(tag); },
  createElementNS(_ns, tag) { return makeEl(tag); },
  querySelectorAll() { return []; },
  body: makeEl('body')
};
let mockAuthed = false;
let mockDash = { customer_id: 'CUST-HEXA-LG', customer_name: 'Công ty TNHH Lục Giác (HEXA)', summary: { active_tracking: 0, arriving_soon: 0, verified_warehouse_eta_count: 0, customer_action_needed: 0, customer_action_status_label: 'Chưa có yêu cầu được xác nhận', total_published: 0 }, shipments: [] };

const sandbox = {
  document,
  window: { addEventListener() {}, open() {} },
  Intl,
  encodeURIComponent,
  Math,
  Number,
  JSON,
  String,
  Array,
  Object,
  console,
  fetch: async (url) => {
    if (url === '/api/hexa/v0/session') {
      return {
        ok: true,
        status: 200,
        json: async () => mockAuthed
          ? { authenticated: true, label: 'Lục Giác', principal: { authenticated: true, customer_id: 'CUST-HEXA-LG', display_name: 'Công ty TNHH Lục Giác (HEXA)' }, default_shipment_id: 'ROAD-LG-001' }
          : { authenticated: false, label: 'Chưa đăng nhập', principal: { authenticated: false, customer_id: '', display_name: '' }, default_shipment_id: '' }
      };
    }
    if (url === '/api/hexa/v0/dashboard') {
      if (!mockAuthed) return { ok: false, status: 403, json: async () => ({ error: 'CUSTOMER_RESOURCE_UNAVAILABLE' }) };
      return { ok: true, status: 200, json: async () => mockDash };
    }
    const row = (mockDash.shipments || [])[0];
    if (!mockAuthed || !row) return { ok: false, status: 403, json: async () => ({ error: 'CUSTOMER_RESOURCE_UNAVAILABLE' }) };
    return {
      ok: true,
      status: 200,
      json: async () => ({
        schema: 'hexa-customer-publication/v0',
        reference: row.shipment_id,
        transport_mode: row.transport_mode,
        timeline: row.timeline,
        documents: row.documents,
        quote: row.quote
      })
    };
  }
};
vm.createContext(sandbox);
vm.runInContext(scriptMatch[1], sandbox);

(async () => {
  // 1. Unauthenticated -> clean login screen, journey shell hidden
  await sandbox.loadSession();
  if (elements['customer-login-screen'].classList.contains('hidden')) throw new Error('Login screen should be visible when unauthed');
  if (!elements['journey-workspace-shell'].classList.contains('hidden')) throw new Error('Journey workspace should be hidden when unauthed');

  // 2. Authenticated but 0 published shipments -> unpublished notice visible
  mockAuthed = true;
  await sandbox.loadSession();
  const zeroText = elements['journey-zero-notice'].textContent;
  if (!zeroText.includes('Trường Thành chưa công bố thông tin cho lô này')) {
    throw new Error('Missing unpublished notice: ' + zeroText);
  }

  // 3. Authenticated with 1 published shipment -> Journey Map auto-opens, selector hidden
  mockDash = dashData;
  await sandbox.loadCustomerDashboard();
  if (!elements['customer-shipment-selector'].classList.contains('hidden')) {
    throw new Error('Single shipment should hide multi-shipment selector');
  }
  const nodesLayerText = elements['journey-nodes-layer'].textContent;
  if (!nodesLayerText.includes('LẤY HÀNG') || !nodesLayerText.includes('QUA CỬA KHẨU')) {
    throw new Error('Journey Map nodes missing: ' + nodesLayerText);
  }

  // 4. Click node -> bubble opens -> click bubble item -> read-only stage popup opens
  sandbox.selectJourneyNode('road-border');
  const bubbleText = elements['journey-bubble-slot'].textContent;
  if (!bubbleText.includes('QUA CỬA KHẨU')) {
    throw new Error('Journey bubble did not open for road-border: ' + bubbleText);
  }
  sandbox.openStageModal('road-border', 'info');
  if (elements['journey-modal-layer'].classList.contains('hidden')) {
    throw new Error('Read-only stage modal did not open');
  }
  const modalText = elements['journey-modal-body'].textContent;
  if (!modalText.includes('Hữu Nghị') || !modalText.includes('Packing List Lục Giác')) {
    throw new Error('Modal missing published evidence or documents: ' + modalText);
  }

  // 5. Multiple shipments -> compact selector becomes visible
  mockDash = {
    ...dashData,
    shipments: [
      dashData.shipments[0],
      { ...dashData.shipments[0], shipment_id: 'ROAD-LG-002', route_summary: 'Shenzhen -> Hà Nội' }
    ]
  };
  await sandbox.loadCustomerDashboard();
  if (elements['customer-shipment-selector'].classList.contains('hidden')) {
    throw new Error('Multi-shipment selector should be visible when >1 shipment');
  }

  console.log('JOURNEY_UI_DOM_STATES_OK');
})();
"""
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".html", delete=False) as fh_html, \
         tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False) as fh_json:
        fh_html.write(html_text)
        fh_json.write(dash_json)
        html_path = fh_html.name
        json_path = fh_json.name

    proc = subprocess.run(
        ["node", "-e", node_dom_script],
        env={"PATH": "/usr/local/bin:/usr/bin:/bin", "HTML_PATH": html_path, "DASH_PATH": dash_json and json_path},
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, f"Node Journey DOM state test failed: {proc.stdout} {proc.stderr}"
    assert "JOURNEY_UI_DOM_STATES_OK" in proc.stdout


def test_customer_login_works_in_cookie_blocked_iframe_via_bearer_token_and_trimmed_passcode(
    trial_server,
) -> None:
    """Regression for Owner Live Preview report ('vào được link nhưng ấn đăng nhập không được'):
    In a cross-origin iframe (Arena Live Preview), browsers drop SameSite=Lax cookies.
    Verify that:
    1. POST /api/hexa/v0/auth/login returns session_token in JSON body (and tolerates accidental trailing space in copy-pasted passcode).
    2. Client JS loginCustomer() stores session_token and sends Authorization: Bearer <token> on subsequent
       /api/hexa/v0/session, /api/hexa/v0/dashboard, /api/hexa/v0/shipments/*, and document download calls,
       so clicking 'Đăng nhập' succeeds even when 100% of browser cookies are blocked.
    """
    import subprocess
    import tempfile

    base_url, _env = trial_server
    _tt_login_and_publish_standard_fixtures(base_url)

    # 1. Verify server login tolerates accidental trailing whitespace from copy-paste and returns session_token
    st_login, _hdrs, raw_login = _http_request(
        base_url,
        "/api/hexa/v0/auth/login",
        method="POST",
        json_body={"username": "  lucgiac.trial  ", "passcode": " LG-Trial-2026! "},
    )
    assert st_login == 200
    login_payload = json.loads(raw_login.decode("utf-8"))
    assert login_payload["authenticated"] is True
    issued_token = login_payload.get("session_token")
    assert isinstance(issued_token, str) and issued_token.startswith("hx_cust_")

    # Verify Bearer token works on /api/hexa/v0/dashboard without any Cookie header
    st_dash, _, raw_dash = _http_request(
        base_url,
        "/api/hexa/v0/dashboard",
        headers={"Authorization": f"Bearer {issued_token}"},
    )
    assert st_dash == 200
    dash_json = raw_dash.decode("utf-8")

    st_html, _, raw_html = _http_request(base_url, "/")
    assert st_html == 200
    html_text = raw_html.decode("utf-8")

    # 2. Simulate cookie-blocked iframe in Node VM: API calls ONLY succeed if Authorization: Bearer <token> is sent!
    node_iframe_script = r"""
const fs = require('fs');
const vm = require('vm');
const html = fs.readFileSync(process.env.HTML_PATH, 'utf8');
const dashData = JSON.parse(process.env.DASH_JSON);
const expectedToken = process.env.EXPECTED_TOKEN;
const scriptMatch = html.match(/<script>([\s\S]*?)<\/script>/);
if (!scriptMatch) { console.error('NO_SCRIPT'); process.exit(2); }

function makeEl(tag) {
  let _text = '';
  const classes = new Set();
  const el = {
    tagName: (tag || 'div').toUpperCase(),
    style: {},
    dataset: {},
    attrs: {},
    value: '',
    children: [],
    className: '',
    classList: {
      add(...cs) { cs.forEach(c => classes.add(c)); el.className = Array.from(classes).join(' '); },
      remove(...cs) { cs.forEach(c => classes.delete(c)); el.className = Array.from(classes).join(' '); },
      toggle(c, force) {
        if (force === undefined) { classes.has(c) ? classes.delete(c) : classes.add(c); }
        else if (force) { classes.add(c); } else { classes.delete(c); }
        el.className = Array.from(classes).join(' ');
      },
      contains(c) { return classes.has(c); }
    },
    appendChild(child) { this.children.push(child); return child; },
    addEventListener(ev, fn) { this['on' + ev] = fn; },
    setAttribute(k, v) { this.attrs[k] = String(v); if (k === 'class') this.className = String(v); },
    getAttribute(k) { return this.attrs[k]; },
    get clientWidth() { return 1200; },
    get clientHeight() { return 640; },
    get textContent() {
      if (this.children.length > 0) return _text + this.children.map(c => c.textContent).join(' ');
      return _text;
    },
    set textContent(v) { _text = String(v ?? ''); this.children = []; },
    set innerHTML(v) { if (v === '') { this.children = []; _text = ''; } }
  };
  return el;
}

const elements = {};
const document = {
  getElementById(id) {
    if (!elements[id]) elements[id] = makeEl('div');
    return elements[id];
  },
  createElement(tag) { return makeEl(tag); },
  createElementNS(_ns, tag) { return makeEl(tag); },
  querySelectorAll() { return []; },
  body: makeEl('body')
};

const sandbox = {
  document,
  window: { addEventListener() {}, open() {} },
  Intl,
  encodeURIComponent,
  Math,
  Number,
  JSON,
  String,
  Array,
  Object,
  console,
  fetch: async (url, opts = {}) => {
    const hdrs = opts.headers || {};
    const auth = hdrs['Authorization'] || hdrs['authorization'] || '';
    const hasValidBearer = (auth === 'Bearer ' + expectedToken);

    if (url === '/api/hexa/v0/auth/login') {
      return {
        ok: true,
        status: 200,
        json: async () => ({
          authenticated: true,
          session_token: expectedToken,
          label: 'Công ty TNHH Lục Giác (HEXA)',
          principal: { authenticated: true, kind: 'customer', customer_id: 'CUST-HEXA-LG', display_name: 'Công ty TNHH Lục Giác (HEXA)' },
          default_shipment_id: 'ROAD-LG-001'
        })
      };
    }
    if (url === '/api/hexa/v0/session') {
      if (!hasValidBearer) {
        return { ok: true, status: 200, json: async () => ({ authenticated: false, principal: { authenticated: false } }) };
      }
      return {
        ok: true,
        status: 200,
        json: async () => ({
          authenticated: true,
          label: 'Công ty TNHH Lục Giác (HEXA)',
          principal: { authenticated: true, kind: 'customer', customer_id: 'CUST-HEXA-LG', display_name: 'Công ty TNHH Lục Giác (HEXA)' },
          default_shipment_id: 'ROAD-LG-001'
        })
      };
    }
    if (url === '/api/hexa/v0/dashboard') {
      if (!hasValidBearer) return { ok: false, status: 403, json: async () => ({ error: 'CUSTOMER_RESOURCE_UNAVAILABLE' }) };
      return { ok: true, status: 200, json: async () => dashData };
    }
    if (url.startsWith('/api/hexa/v0/shipments/')) {
      if (!hasValidBearer) return { ok: false, status: 403, json: async () => ({ error: 'CUSTOMER_RESOURCE_UNAVAILABLE' }) };
      const row = dashData.shipments[0];
      return {
        ok: true,
        status: 200,
        json: async () => ({
          schema: 'hexa-customer-publication/v0',
          reference: row.shipment_id,
          transport_mode: row.transport_mode,
          timeline: row.timeline,
          documents: row.documents,
          quote: row.quote
        })
      };
    }
    return { ok: false, status: 404, json: async () => ({}) };
  }
};
vm.createContext(sandbox);
vm.runInContext(scriptMatch[1], sandbox);

(async () => {
  await sandbox.loadSession();
  document.getElementById('cust-username').value = 'lucgiac.trial';
  document.getElementById('cust-passcode').value = 'LG-Trial-2026!';
  await sandbox.loginCustomer();
  if (!elements['customer-login-screen'].classList.contains('hidden')) {
    throw new Error('Login screen still visible after loginCustomer() in cookie-blocked iframe!');
  }
  if (elements['journey-workspace-shell'].classList.contains('hidden')) {
    throw new Error('Journey workspace still hidden after loginCustomer() in cookie-blocked iframe!');
  }
  const nodesText = elements['journey-nodes-layer'].textContent;
  if (!nodesText.includes('QUA CỬA KHẨU')) {
    throw new Error('Journey Map nodes not rendered after iframe login: ' + nodesText);
  }
  console.log('IFRAME_BEARER_LOGIN_OK');
})();
"""
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".html", delete=False) as fh_html:
        fh_html.write(html_text)
        html_path = fh_html.name

    proc = subprocess.run(
        ["node", "-e", node_iframe_script],
        env={
            "PATH": "/usr/local/bin:/usr/bin:/bin",
            "HTML_PATH": html_path,
            "DASH_JSON": dash_json,
            "EXPECTED_TOKEN": issued_token,
        },
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, f"Iframe bearer login failed: {proc.stdout} {proc.stderr}"
    assert "IFRAME_BEARER_LOGIN_OK" in proc.stdout


def test_multi_shipment_dashboard_to_journey_navigation_revoke_and_no_url_token_leak(
    trial_server,
) -> None:
    """HEXA-MULTI-SHIPMENT-DASHBOARD-NAVIGATION:
    1. Uses 2 simulated shipments belonging to the SAME customer Lục Giác (CUST-LUCGIAC) in SANDBOX_STAGING:
       ROAD-LG-001 and ROAD-LG-002.
    2. 0 published shipments -> friendly empty state.
    3. 1 published shipment (e.g. Minh Đức ROAD-MD-002, or Lục Giác when only 1 is published) -> opens straight into Journey Map.
    4. 2 published shipments for Lục Giác (ROAD-LG-001 + ROAD-LG-002) -> opens Dashboard overview first (Journey Map hidden),
       shows shipment_id, cargo_summary, transport_mode, verified_stage_label, verified_warehouse_eta_label, last_updated_label
       (both desktop table rows and mobile compact cards), clicking a shipment opens its full-screen Journey Map with
       '← Quay lại Dashboard', and clicking '← Quay lại Dashboard' returns to the Dashboard overview.
    5. Revoking ROAD-LG-002 removes it from Lục Giác's Dashboard immediately.
    6. Foreign customer (Minh Đức) cannot access ROAD-LG-001 or ROAD-LG-002.
    7. Security: session token is NEVER placed in URLs (_hx_token removed from client & server query parsing);
       PDF download uses Authorization header in apiFetch + Blob in cookie-blocked iframe mode.
    """
    import subprocess
    import tempfile
    from core.hexa_trial_portal import seed_live_preview_publications

    base_url, env = trial_server
    seed_live_preview_publications(env)

    # 1. Verify customer HTML has no _hx_token URL parameter and includes Back to Dashboard button + mobile cards container
    st_html, _, raw_html = _http_request(base_url, "/")
    assert st_html == 200
    html_text = raw_html.decode("utf-8")
    assert "_hx_token" not in html_text
    assert "btn-back-to-dashboard" in html_text
    assert "Quay lại Dashboard" in html_text
    assert "dash-shipments-cards" in html_text

    # 2. Login as Lục Giác (2 published shipments: ROAD-LG-001 and ROAD-LG-002)
    st_login, _, raw_login = _http_request(
        base_url,
        "/api/hexa/v0/auth/login",
        method="POST",
        json_body={"username": "lucgiac.trial", "passcode": "LG-Trial-2026!"},
    )
    assert st_login == 200
    login_body = json.loads(raw_login.decode("utf-8"))
    issued_token = login_body.get("session_token", "")
    assert issued_token.startswith("hx_cust_")

    dash_2 = login_body.get("dashboard") or {}
    shipments_2 = dash_2.get("shipments") or []
    assert len(shipments_2) == 2
    assert {s["shipment_id"] for s in shipments_2} == {"ROAD-LG-001", "ROAD-LG-002"}
    assert dash_2.get("summary", {}).get("active_tracking") == 2
    assert dash_2.get("summary", {}).get("verified_warehouse_eta_count") == 1

    # 3. Security: query token ?_hx_token= MUST be rejected (403) without Authorization/Cookie header
    st_query_tok_dash, _, _ = _http_request(
        base_url,
        f"/api/hexa/v0/dashboard?_hx_token={issued_token}",
    )
    assert st_query_tok_dash == 403

    st_query_tok_pdf, _, _ = _http_request(
        base_url,
        f"/api/hexa/v0/shipments/ROAD-LG-001/documents/DOC-LG-PL/download?version=v2&_hx_token={issued_token}",
    )
    assert st_query_tok_pdf == 403

    # Authorization: Bearer header works for both dashboard and PDF download (used by apiFetch + Blob)
    st_bearer_pdf, _, raw_bearer_pdf = _http_request(
        base_url,
        "/api/hexa/v0/shipments/ROAD-LG-002/documents/DOC-LG02-PL/download?version=v1",
        headers={"Authorization": f"Bearer {issued_token}"},
    )
    assert st_bearer_pdf == 200
    assert raw_bearer_pdf.startswith(b"%PDF-")

    # 4. Cross-customer isolation: Minh Đức only sees ROAD-MD-002 (1 shipment) and cannot access ROAD-LG-002 (403)
    st_md_login, _, raw_md_login = _http_request(
        base_url,
        "/api/hexa/v0/auth/login",
        method="POST",
        json_body={"username": "minhduc.trial", "passcode": "MD-Trial-2026!"},
    )
    assert st_md_login == 200
    md_body = json.loads(raw_md_login.decode("utf-8"))
    md_token = md_body["session_token"]
    md_shipments = md_body.get("dashboard", {}).get("shipments") or []
    assert [s["shipment_id"] for s in md_shipments] == ["ROAD-MD-002"]

    st_md_forbid, _, _ = _http_request(
        base_url,
        "/api/hexa/v0/shipments/ROAD-LG-002",
        headers={"Authorization": f"Bearer {md_token}"},
    )
    assert st_md_forbid == 403

    # 5. An Phát has 0 published shipments
    st_ap_login, _, raw_ap_login = _http_request(
        base_url,
        "/api/hexa/v0/auth/login",
        method="POST",
        json_body={"username": "anphat.trial", "passcode": "AP-Trial-2026!"},
    )
    assert st_ap_login == 200
    ap_body = json.loads(raw_ap_login.decode("utf-8"))
    assert ap_body.get("dashboard", {}).get("shipments") == []

    # 6. Execute client DOM state machine in Node VM for:
    #    - 0 shipments (An Phát) -> empty state visible
    #    - 1 shipment (Minh Đức) -> straight into Journey Map, Dashboard selector hidden, Back button hidden
    #    - 2 shipments (Lục Giác) -> Dashboard overview visible FIRST, Journey Map hidden ->
    #      select ROAD-LG-002 -> Journey Map visible, Dashboard hidden, Back button visible ->
    #      click Back to Dashboard -> Dashboard visible again, Journey Map hidden ->
    #      select ROAD-LG-001 -> Journey Map of ROAD-LG-001 visible + triggerDownload uses Authorization header (no _hx_token in URL)
    node_nav_script = r"""
const fs = require('fs');
const vm = require('vm');
const html = fs.readFileSync(process.env.HTML_PATH, 'utf8');
const lgLogin = JSON.parse(process.env.LG_LOGIN_JSON);
const mdLogin = JSON.parse(process.env.MD_LOGIN_JSON);
const apLogin = JSON.parse(process.env.AP_LOGIN_JSON);
const scriptMatch = html.match(/<script>([\s\S]*?)<\/script>/);
if (!scriptMatch) { console.error('NO_SCRIPT'); process.exit(2); }

function makeEl(tag) {
  let _text = '';
  const classes = new Set();
  const el = {
    tagName: (tag || 'div').toUpperCase(),
    style: {},
    dataset: {},
    attrs: {},
    value: '',
    children: [],
    className: '',
    classList: {
      add(...cs) { cs.forEach(c => classes.add(c)); el.className = Array.from(classes).join(' '); },
      remove(...cs) { cs.forEach(c => classes.delete(c)); el.className = Array.from(classes).join(' '); },
      toggle(c, force) {
        if (force === undefined) { classes.has(c) ? classes.delete(c) : classes.add(c); }
        else if (force) { classes.add(c); } else { classes.delete(c); }
        el.className = Array.from(classes).join(' ');
      },
      contains(c) { return classes.has(c); }
    },
    appendChild(child) { this.children.push(child); return child; },
    addEventListener(ev, fn) { this['on' + ev] = fn; },
    setAttribute(k, v) { this.attrs[k] = String(v); if (k === 'class') this.className = String(v); },
    getAttribute(k) { return this.attrs[k]; },
    getBoundingClientRect() { return { width: 1280, height: 640, left: 0, top: 0 }; },
    get clientWidth() { return 1280; },
    get clientHeight() { return 640; },
    get textContent() {
      if (this.children.length > 0) return _text + this.children.map(c => c.textContent).join(' ');
      return _text;
    },
    set textContent(v) { _text = String(v ?? ''); this.children = []; },
    set innerHTML(v) { if (v === '') { this.children = []; _text = ''; } }
  };
  return el;
}

const elements = {};
for (const id of ['customer-shipment-selector', 'shipment-journey-view', 'btn-back-to-dashboard', 'journey-zero-notice', 'journey-modal-layer']) {
  elements[id] = makeEl('div');
  if (id !== 'shipment-journey-view') elements[id].classList.add('hidden');
}

const document = {
  getElementById(id) {
    if (!elements[id]) elements[id] = makeEl('div');
    return elements[id];
  },
  createElement(tag) { return makeEl(tag); },
  createElementNS(_ns, tag) { return makeEl(tag); },
  querySelectorAll() { return []; },
  body: makeEl('body')
};

let activeMockLogin = lgLogin;
let downloadedUrls = [];
let downloadedHeaders = [];

const sandbox = {
  document,
  window: { addEventListener() {}, open() {} },
  Intl,
  encodeURIComponent,
  Math,
  Number,
  JSON,
  String,
  Array,
  Object,
  console,
  fetch: async (url, opts = {}) => {
    if (url === '/api/hexa/v0/auth/login') {
      return { ok: true, status: 200, json: async () => activeMockLogin };
    }
    if (url.includes('/download')) {
      downloadedUrls.push(url);
      downloadedHeaders.push(opts.headers || {});
      return {
        ok: true,
        status: 200,
        blob: async () => ({ size: 1420 })
      };
    }
    return { ok: true, status: 200, json: async () => activeMockLogin.dashboard };
  }
};
vm.createContext(sandbox);
vm.runInContext(scriptMatch[1], sandbox);

(async () => {
  // Case A: 0 shipments (An Phát) -> empty state visible
  activeMockLogin = apLogin;
  document.getElementById('cust-username').value = 'anphat.trial';
  document.getElementById('cust-passcode').value = 'AP-Trial-2026!';
  await sandbox.loginCustomer();
  if (!elements['customer-shipment-selector'].classList.contains('hidden')) {
    throw new Error('0-shipment state must hide shipment selector');
  }
  if (elements['journey-zero-notice'].classList.contains('hidden')) {
    throw new Error('0-shipment state must show friendly empty state');
  }

  // Case B: 1 shipment (Minh Đức) -> straight into Journey Map, selector hidden, Back button hidden
  activeMockLogin = mdLogin;
  document.getElementById('cust-username').value = 'minhduc.trial';
  document.getElementById('cust-passcode').value = 'MD-Trial-2026!';
  await sandbox.loginCustomer();
  if (!elements['customer-shipment-selector'].classList.contains('hidden')) {
    throw new Error('1-shipment state must hide Dashboard selector and open Journey Map directly');
  }
  if (elements['shipment-journey-view'].classList.contains('hidden')) {
    throw new Error('1-shipment state must show Journey Map');
  }
  if (!elements['btn-back-to-dashboard'].classList.contains('hidden')) {
    throw new Error('1-shipment state must hide Back to Dashboard button');
  }
  if (document.getElementById('toolbar-id').textContent !== 'ROAD-MD-002') {
    throw new Error('1-shipment state did not load ROAD-MD-002 into Journey toolbar');
  }

  // Case C: 2 shipments (Lục Giác) -> Dashboard overview FIRST, Journey Map hidden until selection
  activeMockLogin = lgLogin;
  document.getElementById('cust-username').value = 'lucgiac.trial';
  document.getElementById('cust-passcode').value = 'LG-Trial-2026!';
  await sandbox.loginCustomer();
  if (elements['customer-shipment-selector'].classList.contains('hidden')) {
    throw new Error('2-shipment state must show Dashboard overview first');
  }
  if (!elements['shipment-journey-view'].classList.contains('hidden')) {
    throw new Error('2-shipment state must hide Journey Map until a shipment is selected');
  }

  // Check required fields in both desktop table and mobile cards
  const tableText = document.getElementById('dash-shipments-tbody').textContent;
  const cardsText = document.getElementById('dash-shipments-cards').textContent;
  for (const token of ['ROAD-LG-001', 'ROAD-LG-002', 'Nội thất văn phòng', 'Thiết bị chiếu sáng', 'ROAD', 'QUA CỬA KHẨU', 'Hải quan nhập', '2026-10-24', '2026-10-21T14:15:00Z', '2026-10-22T15:30:00Z', 'Xem hành trình']) {
    if (!tableText.includes(token)) throw new Error('Desktop Dashboard table missing required token: ' + token);
    if (!cardsText.includes(token)) throw new Error('Mobile Dashboard cards missing required token: ' + token);
  }

  // Select shipment ROAD-LG-002 from Dashboard -> opens full-screen Journey Map of ROAD-LG-002
  await sandbox.selectShipmentForJourney('ROAD-LG-002');
  if (!elements['customer-shipment-selector'].classList.contains('hidden')) {
    throw new Error('Selecting shipment must hide Dashboard overview');
  }
  if (elements['shipment-journey-view'].classList.contains('hidden')) {
    throw new Error('Selecting shipment must show Journey Map');
  }
  if (elements['btn-back-to-dashboard'].classList.contains('hidden')) {
    throw new Error('Multi-shipment Journey Map must show Back to Dashboard button');
  }
  if (document.getElementById('toolbar-id').textContent !== 'ROAD-LG-002') {
    throw new Error('Journey Map did not open ROAD-LG-002');
  }

  // Click '← Quay lại Dashboard' -> returns to Dashboard overview, hides Journey Map
  sandbox.backToDashboard();
  if (elements['customer-shipment-selector'].classList.contains('hidden')) {
    throw new Error('backToDashboard() must show Dashboard overview');
  }
  if (!elements['shipment-journey-view'].classList.contains('hidden')) {
    throw new Error('backToDashboard() must hide Journey Map');
  }

  // Select ROAD-LG-001 and verify Blob PDF download uses Authorization header with NO token in URL
  await sandbox.selectShipmentForJourney('ROAD-LG-001');
  if (document.getElementById('toolbar-id').textContent !== 'ROAD-LG-001') {
    throw new Error('Journey Map did not switch to ROAD-LG-001');
  }
  await sandbox.triggerDownload('ROAD-LG-001', 'DOC-LG-PL', 'v2');
  if (downloadedUrls.length !== 1 || downloadedUrls[0].includes('_hx_token') || downloadedUrls[0].includes('hx_cust_')) {
    throw new Error('PDF download URL leaked token: ' + JSON.stringify(downloadedUrls));
  }
  if (!String(downloadedHeaders[0]['Authorization'] || '').startsWith('Bearer hx_cust_')) {
    throw new Error('PDF download did not send Authorization Bearer header');
  }

  console.log('MULTI_SHIPMENT_NAV_OK');
})();
"""
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".html", delete=False) as fh_html:
        fh_html.write(html_text)
        html_path = fh_html.name

    proc = subprocess.run(
        ["node", "-e", node_nav_script],
        env={
            "PATH": "/usr/local/bin:/usr/bin:/bin",
            "HTML_PATH": html_path,
            "LG_LOGIN_JSON": json.dumps(login_body),
            "MD_LOGIN_JSON": json.dumps(md_body),
            "AP_LOGIN_JSON": json.dumps(ap_body),
        },
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, f"Multi-shipment nav test failed: {proc.stdout} {proc.stderr}"
    assert "MULTI_SHIPMENT_NAV_OK" in proc.stdout

    # 7. Revoke ROAD-LG-002 as TT staff -> ROAD-LG-002 disappears from Lục Giác's Dashboard, leaving 1 shipment (ROAD-LG-001)
    st_tt, hdrs_tt, _ = _http_request(
        base_url,
        "/api/hexa/v0/tt/auth/login",
        method="POST",
        json_body={"username": "tt.ops.truongthanh", "passcode": "TT-Trial-2026!"},
    )
    assert st_tt == 200
    tt_token = _extract_cookie_value(hdrs_tt, TRIAL_TT_COOKIE_NAME)

    st_rev, _, _ = _http_request(
        base_url,
        "/api/hexa/v0/tt/shipments/ROAD-LG-002/revoke",
        method="POST",
        headers={"Cookie": f"{TRIAL_TT_COOKIE_NAME}={tt_token}"},
        json_body={},
    )
    assert st_rev == 200

    st_dash_after_rev, _, raw_dash_after_rev = _http_request(
        base_url,
        "/api/hexa/v0/dashboard",
        headers={"Authorization": f"Bearer {issued_token}"},
    )
    assert st_dash_after_rev == 200
    dash_after_rev = json.loads(raw_dash_after_rev.decode("utf-8"))
    remaining_ids = [s["shipment_id"] for s in (dash_after_rev.get("shipments") or [])]
    assert remaining_ids == ["ROAD-LG-001"]








