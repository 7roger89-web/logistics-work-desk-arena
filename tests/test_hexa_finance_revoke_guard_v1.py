"""HEXA finance revoke guard regression (V1).

Finding: Operations (``operations_write``, **no** ``finance_write``) could call
``POST /api/hexa/v0/tt/shipments/<id>/revoke`` with ``{"revoke_finance": true}``
and receive HTTP 200 while the customer-facing financial disclosure was switched
off. Revoke used to authorize the whole request with
``_require_authorized_tt_staff`` only, and ``revoke_finance`` was treated like
any other partial item.

Acceptance locked here:

1. Operations + ``revoke_finance=true`` -> 403, publication byte-identical, no
   success audit entry, and no partial write when the payload also names
   documents.
2. Finance + ``revoke_finance=true`` -> 200, financial disclosure withdrawn only;
   published documents / progress milestones / quote stay exactly as they were.
3. Operations can still revoke documents and progress milestones as before.
4. Whole-lot revoke (empty payload) is a separate, unchanged policy: it removes
   every published item from the customer and is still allowed for Operations.

Isolated ``SANDBOX_STAGING``/mongomock only; no production DB, no browser QA.
"""
from __future__ import annotations

import json
import threading
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from core import database as core_db
from core.hexa_trial_portal import (
    SHIPMENT_A_ID,
    HexaTrialEnvironment,
    create_trial_http_server,
    seed_live_preview_publications,
)

OPS_CREDENTIALS = ("tt.ops.truongthanh", "TT-Trial-2026!")
FINANCE_CREDENTIALS = ("tt.finance.truongthanh", "TT-Finance-2026!")
CUSTOMER_CREDENTIALS = ("lucgiac.trial", "LG-Trial-2026!")


def _http_request(
    base_url: str,
    path: str,
    *,
    method: str = "GET",
    session_token: str | None = None,
    json_body: dict[str, Any] | None = None,
) -> tuple[int, bytes]:
    headers: dict[str, str] = {}
    if session_token is not None:
        headers["Authorization"] = f"Bearer {session_token}"
    data = None
    if json_body is not None:
        data = json.dumps(json_body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = Request(f"{base_url}{path}", data=data, headers=headers, method=method)
    try:
        with urlopen(req, timeout=10) as resp:
            return resp.status, resp.read()
    except HTTPError as exc:
        return exc.code, exc.read()


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


def _login(base_url: str, credentials: tuple[str, str], path: str = "/api/hexa/v0/tt/auth/login") -> str:
    status, raw = _http_request(
        base_url, path, method="POST", json_body={"username": credentials[0], "passcode": credentials[1]}
    )
    assert status == 200, raw
    return json.loads(raw.decode("utf-8"))["session_token"]


def _publication(env: HexaTrialEnvironment) -> dict[str, Any]:
    db = core_db.get_db()
    assert db is not None
    return db["hexa_trial_publications"].find_one({"shipment_id": SHIPMENT_A_ID}, {"_id": 0}) or {}


def _customer_shipment(base_url: str, token: str) -> dict[str, Any]:
    status, raw = _http_request(base_url, "/api/hexa/v0/dashboard", session_token=token)
    assert status == 200, raw
    dashboard = json.loads(raw.decode("utf-8"))
    return next(item for item in dashboard["shipments"] if item["shipment_id"] == SHIPMENT_A_ID)


def _approve_finance(base_url: str, env: HexaTrialEnvironment, finance_token: str) -> None:
    publication = _publication(env)
    status, raw = _http_request(
        base_url,
        f"/api/hexa/v0/tt/shipments/{SHIPMENT_A_ID}/publish",
        method="POST",
        session_token=finance_token,
        json_body={
            "event_versions": publication.get("event_versions") or {},
            "document_versions": publication.get("document_versions") or {},
            "quote": publication.get("quote"),
            "approve_finance": True,
        },
    )
    assert status == 200, raw


def _revoke(base_url: str, token: str, payload: dict[str, Any]) -> tuple[int, bytes]:
    return _http_request(
        base_url,
        f"/api/hexa/v0/tt/shipments/{SHIPMENT_A_ID}/revoke",
        method="POST",
        session_token=token,
        json_body=payload,
    )


def _audit_entries(env: HexaTrialEnvironment, since: int) -> list[dict[str, Any]]:
    """Audit entries written since ``since``, limited to revoke actions."""
    return [
        entry
        for entry in env.audit_trail[since:]
        if str(entry.get("action") or "").startswith("REVOKE")
    ]


# --------------------------------------------------------------------------- #
# 1. Operations can never withdraw the financial disclosure.
# --------------------------------------------------------------------------- #
def test_operations_revoke_finance_is_denied_without_side_effects(trial_server) -> None:
    base_url, env = trial_server
    seed_live_preview_publications(env)
    ops_token = _login(base_url, OPS_CREDENTIALS)
    finance_token = _login(base_url, FINANCE_CREDENTIALS)
    customer_token = _login(base_url, CUSTOMER_CREDENTIALS, "/api/hexa/v0/auth/login")

    _approve_finance(base_url, env, finance_token)
    assert _publication(env).get("finance_published") is True
    assert _customer_shipment(base_url, customer_token)["debt_summary"]["status"] == "CONFIRMED"

    before = _publication(env)
    audit_mark = len(env.audit_trail)

    status, raw = _revoke(base_url, ops_token, {"revoke_finance": True})
    assert status == 403, raw

    # Nothing about the publication moved, and no success audit was fabricated.
    assert _publication(env) == before
    assert _customer_shipment(base_url, customer_token)["debt_summary"]["status"] == "CONFIRMED"
    entries = _audit_entries(env, audit_mark)
    assert [e for e in entries if e.get("allowed") is True] == []
    assert any(e.get("allowed") is False for e in entries)

    # A mixed payload is refused as a whole: the named document must NOT be revoked.
    published_docs = dict(before.get("document_versions") or {})
    assert published_docs, "fixture must publish at least one document"
    doc_id = sorted(published_docs)[0]
    audit_mark = len(env.audit_trail)
    status, raw = _revoke(base_url, ops_token, {"document_ids": [doc_id], "revoke_finance": True})
    assert status == 403, raw
    assert _publication(env) == before
    assert any(e.get("allowed") is False for e in _audit_entries(env, audit_mark))


# --------------------------------------------------------------------------- #
# 2. Finance may withdraw the disclosure, and only the disclosure.
# --------------------------------------------------------------------------- #
def test_finance_revoke_finance_keeps_documents_milestones_and_quote(trial_server) -> None:
    base_url, env = trial_server
    seed_live_preview_publications(env)
    finance_token = _login(base_url, FINANCE_CREDENTIALS)
    customer_token = _login(base_url, CUSTOMER_CREDENTIALS, "/api/hexa/v0/auth/login")

    _approve_finance(base_url, env, finance_token)
    before = _publication(env)
    assert before.get("finance_published") is True
    assert before.get("state") == "PUBLISHED"
    assert _customer_shipment(base_url, customer_token)["debt_summary"]["status"] == "CONFIRMED"

    audit_mark = len(env.audit_trail)
    status, raw = _revoke(base_url, finance_token, {"revoke_finance": True})
    assert status == 200, raw

    after = _publication(env)
    assert after.get("finance_published") is False
    # Hồ sơ / chứng từ / mốc tiến độ / báo giá đã công bố giữ nguyên.
    assert after.get("state") == "PUBLISHED"
    assert after.get("document_versions") == before.get("document_versions")
    assert after.get("event_versions") == before.get("event_versions")
    assert after.get("quote") == before.get("quote")
    assert after.get("approved_by") == before.get("approved_by")
    assert after.get("history")[-1].get("action") == "REVOKED_ITEMS"
    assert after.get("history")[-1].get("revoked_finance") is True

    shipment = _customer_shipment(base_url, customer_token)
    assert shipment["debt_summary"]["status"] == "UNKNOWN"
    assert shipment["debt_summary"]["total_payable"] is None
    assert shipment["debt_summary"]["remaining_balance"] is None
    assert {d["id"] for d in shipment["documents"]} == set(before.get("document_versions") or {})
    assert shipment["quote"] is not None

    # Success audit is real and names the finance scope.
    allowed = [e for e in _audit_entries(env, audit_mark) if e.get("allowed") is True]
    assert len(allowed) == 1
    assert allowed[0].get("action") == "REVOKE_PUBLICATION"
    assert "finance=True" in str(allowed[0].get("detail") or "")


# --------------------------------------------------------------------------- #
# 3. Operations keeps its existing document / milestone revoke authority.
# --------------------------------------------------------------------------- #
def test_operations_can_still_revoke_documents_and_milestones(trial_server) -> None:
    base_url, env = trial_server
    seed_live_preview_publications(env)
    ops_token = _login(base_url, OPS_CREDENTIALS)
    finance_token = _login(base_url, FINANCE_CREDENTIALS)

    _approve_finance(base_url, env, finance_token)
    before = _publication(env)
    doc_id = sorted(dict(before.get("document_versions") or {}))[0]
    ev_id = sorted(dict(before.get("event_versions") or {}))[0]

    status, raw = _revoke(base_url, ops_token, {"document_ids": [doc_id], "event_ids": [ev_id]})
    assert status == 200, raw

    after = _publication(env)
    assert after.get("state") == "PUBLISHED"
    assert doc_id not in (after.get("document_versions") or {})
    assert ev_id not in (after.get("event_versions") or {})
    # Revoking hồ sơ items does not silently drop the finance disclosure.
    assert after.get("finance_published") is True
    assert after.get("history")[-1].get("revoked_finance") is False


# --------------------------------------------------------------------------- #
# 4. Whole-lot revoke stays a separate, unchanged policy (Operations allowed).
# --------------------------------------------------------------------------- #
def test_operations_whole_lot_revoke_policy_is_unchanged(trial_server) -> None:
    base_url, env = trial_server
    seed_live_preview_publications(env)
    ops_token = _login(base_url, OPS_CREDENTIALS)
    finance_token = _login(base_url, FINANCE_CREDENTIALS)
    customer_token = _login(base_url, CUSTOMER_CREDENTIALS, "/api/hexa/v0/auth/login")

    _approve_finance(base_url, env, finance_token)
    assert _customer_shipment(base_url, customer_token)["debt_summary"]["status"] == "CONFIRMED"

    # Empty payload = "gỡ toàn bộ thông tin khỏi khách" (REVOKED_ALL), not a finance act.
    status, raw = _revoke(base_url, ops_token, {})
    assert status == 200, raw

    after = _publication(env)
    assert after.get("state") == "REVOKED"
    assert after.get("document_versions") == {}
    assert after.get("event_versions") == {}
    assert after.get("quote") is None
    assert after.get("finance_published") is False
    assert after.get("history")[-1].get("action") == "REVOKED_ALL"

    status, raw = _http_request(base_url, "/api/hexa/v0/dashboard", session_token=customer_token)
    assert status == 200
    assert SHIPMENT_A_ID not in raw.decode("utf-8")

    # After the whole-lot withdrawal the finance-only path is still finance_write gated.
    status, raw = _revoke(base_url, ops_token, {"revoke_finance": True})
    assert status == 403, raw
