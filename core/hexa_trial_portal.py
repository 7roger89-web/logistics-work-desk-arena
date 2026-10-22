"""HEXA V0 Trial Portal & Trusted Adapter — TT → Lục Giác (isolated sandbox).

Reuses ``core.hexa_customer_publication`` (``build_customer_publication``,
``authorize_document_download``, ``PublicationDenied``), ``core.quotations``,
``core.shipment_attachments`` (``upload_attachment``, ``fetch_attachment_bytes``),
``core.database`` and ``views.logi_sandbox`` (isolated ``mongomock`` + GridFS).

Security boundaries enforced on the HTTP trial portal:
- TT internal inspection data (cost, margin, supplier, unverified ETA, other
  customers on the shared truck) is strictly separated from the customer UI/API.
  Customer A, Customer B, internal ``viewer`` and anonymous callers are denied
  (``HTTP 403 CUSTOMER_RESOURCE_UNAVAILABLE``) on any inspector endpoint.
- HTTP clients cannot self-switch customer sessions or authenticate using
  predictable sample tokens (``sess-customer-lg``, ``sess-customer-md``, etc.).
  Session tokens are random per-boot opaque secrets issued server-side.
- Optional role switching for QA is disabled by default on the customer server
  (``internal_qa_mode=False``) and, even when enabled for an isolated internal
  QA harness, lives off the customer path under ``/internal/qa/*`` gated by a
  server-only ``X-Hexa-Internal-QA-Key``.

Nothing in this module connects to production MongoDB, modifies PR #211 files,
or grants live customer access.
"""
from __future__ import annotations

import copy
from datetime import datetime, timezone
import hmac
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import secrets
from typing import Any, Mapping, Sequence
from urllib.parse import parse_qs, urlparse

from core.hexa_customer_publication import (
    PUBLICATION_SCHEMA,
    PublicationDenied,
    authorize_document_download,
    build_customer_publication,
)

TRIAL_COOKIE_NAME = "hexa_trial_session"
TRIAL_TT_COOKIE_NAME = "hexa_trial_tt_session"
INTERNAL_QA_HEADER = "X-Hexa-Internal-QA-Key"

TT_STAFF_TRIAL_USERNAME = "tt.ops.truongthanh"
TT_STAFF_TRIAL_PASSCODE = "TT-Trial-2026!"
TT_VIEWER_TRIAL_USERNAME = "tt.viewer"
TT_VIEWER_TRIAL_PASSCODE = "Viewer-Trial-2026!"

CUSTOMER_A_TRIAL_USERNAME = "lucgiac.trial"
CUSTOMER_A_TRIAL_PASSCODE = "LG-Trial-2026!"
CUSTOMER_B_TRIAL_USERNAME = "minhduc.trial"
CUSTOMER_B_TRIAL_PASSCODE = "MD-Trial-2026!"
CUSTOMER_C_TRIAL_USERNAME = "anphat.trial"
CUSTOMER_C_TRIAL_PASSCODE = "AP-Trial-2026!"

# Static/sample token names that must NEVER be accepted as valid HTTP session tokens.
FORBIDDEN_SAMPLE_TOKENS: frozenset[str] = frozenset(
    {
        "sess-customer-lg",
        "sess-customer-md",
        "sess-customer-ap",
        "sess-internal-viewer",
        "sess-anonymous",
        "customer_a",
        "customer_b",
        "customer_c",
        "internal_viewer",
        "anonymous",
        TT_STAFF_TRIAL_USERNAME,
        TT_VIEWER_TRIAL_USERNAME,
        CUSTOMER_A_TRIAL_USERNAME,
        CUSTOMER_B_TRIAL_USERNAME,
        CUSTOMER_C_TRIAL_USERNAME,
    }
)

# Sentinels used to prove zero internal / cross-tenant leakage over HTTP.
SENTINEL_TT_INTERNAL_COST = "TT_INTERNAL_COST_42000000"
SENTINEL_TT_PRIVATE_SUPPLIER = "TT_PRIVATE_SUPPLIER_FOSHAN_8899"
SENTINEL_TT_MARGIN = "TT_INTERNAL_MARGIN_11000000"
SENTINEL_TT_UNVERIFIED_ETA = "TT_UNVERIFIED_ETA_2026-10-25"
SENTINEL_FOREIGN_CUSTOMER_B = "FOREIGN_CUSTOMER_MINHDUC_9911"
SENTINEL_FOREIGN_CUSTOMER_C = "FOREIGN_CUSTOMER_ANPHAT_7733"

TRIAL_SENTINELS: tuple[str, ...] = (
    SENTINEL_TT_INTERNAL_COST,
    SENTINEL_TT_PRIVATE_SUPPLIER,
    SENTINEL_TT_MARGIN,
    SENTINEL_TT_UNVERIFIED_ETA,
    SENTINEL_FOREIGN_CUSTOMER_B,
    SENTINEL_FOREIGN_CUSTOMER_C,
)

SHARED_TRIP_ID = "TRIP-ROAD-2026-01"
SHARED_TRUCK_PLATE = "29H-886.68 / 粤Z·6689港"

CUSTOMER_A_ID = "CUST-LUCGIAC"
CUSTOMER_B_ID = "CUST-MINHDUC"
CUSTOMER_C_ID = "CUST-ANPHAT"

SHIPMENT_A_ID = "ROAD-LG-001"
SHIPMENT_B_ID = "ROAD-MD-002"
SHIPMENT_C_ID = "ROAD-AP-003"

QUOTE_A_ID = "Q-LG-ROAD-001"
QUOTE_B_ID = "Q-MD-ROAD-002"
QUOTE_C_ID = "Q-AP-ROAD-003"

# Exact schema gap report required by Acceptance Criterion #7:
# "Nếu nguồn dữ liệu hiện tại thiếu trường bắt buộc, chỉ ra chính xác trường nào;
# không giả định hoặc chế dữ liệu thật."
SCHEMA_GAP_REPORT: tuple[dict[str, Any], ...] = (
    {
        "surface": "Phiên đăng nhập khách (principal)",
        "current_source": "core/users.py:18,52-75 & core/auth.py:72-122",
        "existing_fields": ["user_id", "username", "role (admin|sale|support|viewer)", "active"],
        "missing_required_fields": [
            "principal.kind == 'customer' (core/users.py chỉ có role nội bộ; role 'viewer' có quyền finance_view nên cấm dùng cho khách)",
            "principal.customer_id (ràng buộc tài khoản đăng nhập với đúng mã khách hàng từ session phía server)",
        ],
        "trial_handling": "Bảng phiên thử nghiệm phía server ánh xạ token ngẫu nhiên (opaque secret do server cấp) sang {authenticated, kind, customer_id}; cấm token mẫu và không cho phép client tự đổi phiên trên đường khách.",
    },
    {
        "surface": "Bản duyệt công bố của TT (publication manifest)",
        "current_source": "core/database.py (chưa có collection manifest công bố khách)",
        "existing_fields": [],
        "missing_required_fields": [
            "publication.state ('PUBLISHED')",
            "publication.customer_id",
            "publication.shipment_id",
            "publication.approved_by",
            "publication.approved_at (ISO timestamp)",
            "publication.event_versions (map event_id -> version đã duyệt)",
            "publication.document_versions (map document_id -> version đã duyệt)",
            "publication.quote ({id, version} của báo giá bán đã duyệt công bố)",
        ],
        "trial_handling": "Collection thử nghiệm cô lập hexa_trial_publications lưu manifest do TT duyệt trong mongomock; chưa có UI/collection duyệt manifest trên DB production.",
    },
    {
        "surface": "Lô hàng ROAD ghép xe nhiều khách (shipment)",
        "current_source": "core/database.py:563 & views/logi_staging_seed.py:254-308 & core/shipment_operations.py:19",
        "existing_fields": [
            "id / shipment_id",
            "customer_id (1 khách/lô)",
            "data['0.0']['mode'] ('Truck'|'Sea'|'Air'|'Rail')",
            "data['1.2']['eta'] / data['2.6']['arrival_date'] (ETA nội bộ chưa gắn cờ xác minh)",
        ],
        "missing_required_fields": [
            "shipment.transport_mode ở top-level theo enum {'ROAD','SEA','AIR','RAIL'} (schema hiện tại lưu data['0.0']['mode']='Truck')",
            "shipment.quote_id ở top-level nối trực tiếp sang báo giá đã gửi (schema hiện tại lưu contract_id hoặc agreement/quotation rời)",
            "Khóa chuyến xe ghép (trip_id / shared_unit_id) tách riêng khỏi shipment_id của từng khách khi 2 khách đi chung 1 xe ROAD",
        ],
        "trial_handling": "Adapter đọc shipment chuẩn từ mongomock, chuẩn hoá mode 'Truck' -> transport_mode='ROAD', nối quote_id đã liên kết, và giữ nguyên tách biệt lô từng khách trên cùng chuyến xe TRIP-ROAD-2026-01.",
    },
    {
        "surface": "Tiến độ chia sẻ cho khách & trạng thái xác minh ETA (events)",
        "current_source": "core/shipment_journey.py:124-149",
        "existing_fields": [
            "journey nodes suy diễn trực tiếp từ data['1.2'], data['2.4'], data['2.7'] (id, label, completed, evidence, deadline)",
        ],
        "missing_required_fields": [
            "event.id (định danh sự kiện công bố ổn định)",
            "event.version (phiên bản sự kiện để pin trong manifest)",
            "event.customer_id (tách chủ sở hữu sự kiện trên chuyến xe ghép)",
            "event.verified (bool) & event.verified_at (timestamp TT xác minh thực tế)",
            "event.visibility ('CUSTOMER' vs 'TT')",
            "event.public_title & event.occurred_at tách khỏi ghi chú nội bộ và ETA dự kiến chưa xác minh",
        ],
        "trial_handling": "Collection thử nghiệm hexa_trial_events lưu các sự kiện có verified/visibility/version; các mốc ETA nội bộ (data['1.2']['eta'], event verified=False hoặc visibility='TT') bị giữ lại phía TT.",
    },
    {
        "surface": "Chứng từ đính kèm & kiểm quyền tải theo phiên bản (documents)",
        "current_source": "core/shipment_attachments.py:567-583 & core/database.py:2558",
        "existing_fields": [
            "id (ATT-...)",
            "shipment_id",
            "storage_backend ('gridfs')",
            "storage_file_id",
            "original_name",
            "mime",
            "category ('customs'|'contract'|'transport'|'booking'|'si'|'vgm'|'other')",
            "status ('AVAILABLE')",
        ],
        "missing_required_fields": [
            "document.customer_id (bản ghi shipment_attachments hiện chỉ gắn shipment_id, chưa gắn customer_id)",
            "document.version (ví dụ 'v1', 'v2' — hiện chỉ dedupe theo sha256, chưa đánh version phát hành cho khách)",
            "document.kind theo tập ALLOWED_DOCUMENT_KINDS ('PL','PI','BOOKING','SI','BL','AWB','POD','CUSTOMS','CUSTOMER_INVOICE','CUSTOMER_CONTRACT','PAYMENT_REQUEST')",
            "document.visibility ('CUSTOMER' vs 'TT' để chặn chứng từ giá vốn/nội bộ)",
            "document.verified (bool) & document.public_title",
        ],
        "trial_handling": "File thật lưu trong GridFS qua upload_attachment + đọc qua fetch_attachment_bytes; bảng cầu nối hexa_trial_documents bổ sung customer_id, kind, version, visibility, verified để kiểm quyền trước khi gọi GridFS.",
    },
    {
        "surface": "Báo giá bán đã gửi (quote)",
        "current_source": "core/quotations.py:126-340",
        "existing_fields": [
            "id",
            "version",
            "customer_id",
            "status ('DRAFT'|'READY_FOR_REVIEW'|'SENT'|'ACCEPTED'|...)",
            "calculation.selling_price_total_vnd",
            "calculation.estimated_cost_vnd (nội bộ)",
            "calculation.estimated_margin_vnd (nội bộ)",
        ],
        "missing_required_fields": [
            "Liên kết shipment.quote_id bắt buộc trên lô hàng để đối chiếu 1-1 với publication.quote.id",
        ],
        "trial_handling": "Tạo báo giá thật bằng core.quotations (new_quote_document -> transition_quote('SENT')), có cả giá vốn & NCC nội bộ; core/hexa_customer_publication.py chỉ trích xuất selling_price_total_vnd.",
    },
)


def _pdf_bytes(title: str, body_lines: list[str]) -> bytes:
    """Build a small valid PDF binary that passes ``sniff_kind`` (``%PDF-``)."""
    text_rows = " / ".join([title, *body_lines])
    safe_ascii = text_rows.encode("ascii", errors="replace").decode("ascii")
    stream = f"BT /F1 12 Tf 36 740 Td ({safe_ascii}) Tj ET".encode("ascii")
    return (
        b"%PDF-1.4\n"
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n"
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R >> endobj\n"
        + f"4 0 obj << /Length {len(stream)} >> stream\n".encode("ascii")
        + stream
        + b"\nendstream endobj\n"
        b"xref\n0 5\n0000000000 65535 f \n"
        b"trailer << /Root 1 0 R /Size 5 >>\nstartxref\n0\n%%EOF\n"
    )


class HexaTrialEnvironment:
    """Isolated trial runtime backed by mongomock + GridFS."""

    def __init__(self) -> None:
        self.storage_read_attempts: int = 0
        self.denied_before_storage_reads: int = 0
        self.audit_trail: list[dict[str, Any]] = []
        self.sessions: dict[str, dict[str, Any]] = {}
        self._role_tokens: dict[str, str] = {}
        self.internal_qa_key: str = ""
        self._seeded: bool = False

    def ensure_seeded(self, *, force_reset: bool = False) -> None:
        if self._seeded and not force_reset:
            return

        import logging
        import mongomock.gridfs
        import streamlit as st
        from core import database as core_db
        from core import quotations as core_quotes
        from core import shipment_attachments as core_att
        from views import logi_sandbox
        from views import logi_staging_seed

        logging.getLogger("streamlit").setLevel(logging.ERROR)
        logging.getLogger("streamlit.runtime.scriptrunner_utils.script_run_context").setLevel(logging.ERROR)
        mongomock.gridfs.enable_gridfs_integration()
        if force_reset:
            logi_sandbox.reset_backend()
        transport = logi_sandbox.ensure_backend()
        if transport != logi_sandbox.SANDBOX_TRANSPORT:
            raise RuntimeError(
                "HEXA trial portal chỉ được chạy trên SANDBOX_STAGING (mongomock), tuyệt đối không dùng DB thật."
            )

        st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)
        db = core_db.get_db()
        if db is None:
            raise RuntimeError("Không khởi tạo được mongomock database cho HEXA trial.")

        self.storage_read_attempts = 0
        self.denied_before_storage_reads = 0
        self.audit_trail = []

        # 1. Server-side session table keyed ONLY by random per-boot opaque tokens.
        #    Predictable sample tokens ("sess-customer-lg", "sess-customer-md", etc.)
        #    are never registered and are explicitly rejected.
        token_customer_a = f"hx_live_{secrets.token_urlsafe(24)}"
        token_customer_b = f"hx_live_{secrets.token_urlsafe(24)}"
        token_customer_c = f"hx_live_{secrets.token_urlsafe(24)}"
        token_internal_viewer = f"hx_live_{secrets.token_urlsafe(24)}"
        self.internal_qa_key = f"hx_internal_qa_{secrets.token_urlsafe(24)}"

        self._role_tokens = {
            "customer_a": token_customer_a,
            CUSTOMER_A_ID: token_customer_a,
            "customer_b": token_customer_b,
            CUSTOMER_B_ID: token_customer_b,
            "customer_c": token_customer_c,
            CUSTOMER_C_ID: token_customer_c,
            "internal_viewer": token_internal_viewer,
        }
        self.sessions = {
            token_customer_a: {
                "role_key": "customer_a",
                "label": "Khách A — Công ty TNHH Lục Giác (HEXA)",
                "principal": {
                    "authenticated": True,
                    "kind": "customer",
                    "customer_id": CUSTOMER_A_ID,
                    "display_name": "Lục Giác (Khách A)",
                },
                "default_shipment_id": SHIPMENT_A_ID,
            },
            token_customer_b: {
                "role_key": "customer_b",
                "label": "Khách B — Công ty CP Minh Đức",
                "principal": {
                    "authenticated": True,
                    "kind": "customer",
                    "customer_id": CUSTOMER_B_ID,
                    "display_name": "Minh Đức (Khách B)",
                },
                "default_shipment_id": SHIPMENT_B_ID,
            },
            token_customer_c: {
                "role_key": "customer_c",
                "label": "Khách C — Công ty TNHH Thiết bị An Phát",
                "principal": {
                    "authenticated": True,
                    "kind": "customer",
                    "customer_id": CUSTOMER_C_ID,
                    "display_name": "An Phát (Khách C)",
                },
                "default_shipment_id": SHIPMENT_C_ID,
            },
            token_internal_viewer: {
                "role_key": "internal_viewer",
                "label": "Nội bộ TT — Role viewer (có finance_view, CẤM làm cổng khách)",
                "principal": {
                    "authenticated": True,
                    "kind": "viewer",
                    "customer_id": CUSTOMER_A_ID,
                    "display_name": "Internal Viewer (finance_view)",
                },
                "default_shipment_id": SHIPMENT_A_ID,
            },
        }

        # 2. Seed the three trial customers + trial accounts (PBKDF2-SHA256 via core.auth).
        from core import auth as core_auth
        from core import users as core_users

        for cust_doc in (
            {
                "id": CUSTOMER_A_ID,
                "name": "Công ty TNHH Lục Giác (HEXA)",
                "tax_code": "0108886688",
                "address": "Khu đô thị mới Cầu Giấy, Hà Nội",
            },
            {
                "id": CUSTOMER_B_ID,
                "name": "Công ty CP Minh Đức",
                "tax_code": "0102345678",
                "address": "KCN Yên Phong, Bắc Ninh",
            },
            {
                "id": CUSTOMER_C_ID,
                "name": "Công ty TNHH Thiết bị An Phát",
                "tax_code": "0201998877",
                "address": "KCN Đình Vũ, Hải Phòng",
            },
        ):
            db["customers"].replace_one({"id": cust_doc["id"]}, cust_doc, upsert=True)

        # Seed TT internal staff accounts in db["users"] (reusing core.users & core.auth PBKDF2-SHA256)
        tt_staff_doc = core_users.build_user_document(
            TT_STAFF_TRIAL_USERNAME,
            TT_STAFF_TRIAL_PASSCODE,
            "Điều vận Trường Thành (TT Ops)",
            "support",
            active=True,
            created_by="system",
        )
        tt_viewer_doc = {
            "user_id": "tt_viewer_01",
            "username": TT_VIEWER_TRIAL_USERNAME,
            "display_name": "Internal Viewer (finance_view)",
            "email": "",
            "role": "viewer",
            "active": True,
            "password_hash": core_auth.hash_password(TT_VIEWER_TRIAL_PASSCODE, iterations=120000),
            "created_by": "system",
        }
        db["users"].replace_one({"username": TT_STAFF_TRIAL_USERNAME}, tt_staff_doc, upsert=True)
        db["users"].replace_one({"username": TT_VIEWER_TRIAL_USERNAME}, tt_viewer_doc, upsert=True)

        # Seed trial customer login accounts in db["hexa_trial_customer_accounts"]
        # Each account binds 1 username -> 1 server-enforced customer_id (never client-chosen).
        db["hexa_trial_customer_accounts"].delete_many({})
        db["hexa_trial_customer_accounts"].insert_many(
            [
                {
                    "account_id": "cust_acct_lucgiac",
                    "username": CUSTOMER_A_TRIAL_USERNAME,
                    "password_hash": core_auth.hash_password(CUSTOMER_A_TRIAL_PASSCODE, iterations=120000),
                    "kind": "customer",
                    "customer_id": CUSTOMER_A_ID,
                    "role_key": "customer_a",
                    "label": "Khách A — Công ty TNHH Lục Giác (HEXA)",
                    "display_name": "Lục Giác (Khách A)",
                    "default_shipment_id": SHIPMENT_A_ID,
                    "active": True,
                },
                {
                    "account_id": "cust_acct_minhduc",
                    "username": CUSTOMER_B_TRIAL_USERNAME,
                    "password_hash": core_auth.hash_password(CUSTOMER_B_TRIAL_PASSCODE, iterations=120000),
                    "kind": "customer",
                    "customer_id": CUSTOMER_B_ID,
                    "role_key": "customer_b",
                    "label": "Khách B — Công ty CP Minh Đức",
                    "display_name": "Minh Đức (Khách B)",
                    "default_shipment_id": SHIPMENT_B_ID,
                    "active": True,
                },
                {
                    "account_id": "cust_acct_anphat",
                    "username": CUSTOMER_C_TRIAL_USERNAME,
                    "password_hash": core_auth.hash_password(CUSTOMER_C_TRIAL_PASSCODE, iterations=120000),
                    "kind": "customer",
                    "customer_id": CUSTOMER_C_ID,
                    "role_key": "customer_c",
                    "label": "Khách C — Công ty TNHH Thiết bị An Phát",
                    "display_name": "An Phát (Khách C)",
                    "default_shipment_id": SHIPMENT_C_ID,
                    "active": True,
                },
            ]
        )

        # 3. Build and persist canonical quotes through core.quotations (real calculation engine).
        quote_a = self._build_trial_quote(
            core_quotes,
            quote_id=QUOTE_A_ID,
            quote_no="QT-20261022-LG01",
            customer_id=CUSTOMER_A_ID,
            customer_name="Công ty TNHH Lục Giác (HEXA)",
            factory_name=f"Foshan Hexa Furniture Factory [{SENTINEL_TT_PRIVATE_SUPPLIER}]",
            pickup_address="Shunde, Foshan, Guangdong — Liên hệ NCC nội bộ TT: Mr. Chen",
            lines=[
                {
                    "code": "ROAD-LTL-BT-HN",
                    "service_name": "Cước xe ghép đường bộ Bằng Tường → Hà Nội",
                    "unit": "Lô ghép",
                    "qty": 1,
                    "currency": "VND",
                    "cost_unit": 36000000,
                    "sell_unit": 45000000,
                    "tax_pct": 8,
                    "internal_note": f"Giá vốn nhà xe ghép {SENTINEL_TT_INTERNAL_COST}",
                },
                {
                    "code": "CUSTOMS-HN",
                    "service_name": "Thủ tục thông quan & kiểm hóa cửa khẩu Hữu Nghị",
                    "unit": "Bộ",
                    "qty": 1,
                    "currency": "VND",
                    "cost_unit": 6000000,
                    "sell_unit": 8000000,
                    "tax_pct": 8,
                    "internal_note": f"Biên lợi nhuận nội bộ {SENTINEL_TT_MARGIN}",
                },
            ],
            target_status="SENT",
        )
        quote_b = self._build_trial_quote(
            core_quotes,
            quote_id=QUOTE_B_ID,
            quote_no="QT-20261022-MD02",
            customer_id=CUSTOMER_B_ID,
            customer_name="Công ty CP Minh Đức",
            factory_name=f"Guangxi Dongxing Metal Co. [{SENTINEL_FOREIGN_CUSTOMER_B}]",
            pickup_address="Dongxing, Guangxi",
            lines=[
                {
                    "code": "ROAD-LTL-BT-BN",
                    "service_name": "Cước xe ghép đường bộ Bằng Tường → Bắc Ninh",
                    "unit": "Lô ghép",
                    "qty": 1,
                    "currency": "VND",
                    "cost_unit": 29000000,
                    "sell_unit": 36000000,
                    "tax_pct": 8,
                },
            ],
            target_status="SENT",
        )
        quote_c = self._build_trial_quote(
            core_quotes,
            quote_id=QUOTE_C_ID,
            quote_no="QT-20261022-AP03",
            customer_id=CUSTOMER_C_ID,
            customer_name="Công ty TNHH Thiết bị An Phát",
            factory_name=f"Fangchenggang Electric Equipment Co. [{SENTINEL_FOREIGN_CUSTOMER_C}]",
            pickup_address="Fangchenggang, Guangxi",
            lines=[
                {
                    "code": "ROAD-LTL-DH-HP",
                    "service_name": "Cước đường bộ Đông Hưng → Móng Cái → Hải Phòng",
                    "unit": "Lô",
                    "qty": 1,
                    "currency": "VND",
                    "cost_unit": 24000000,
                    "sell_unit": 31000000,
                    "tax_pct": 8,
                },
            ],
            target_status="SENT",
        )
        db["quotes"].replace_one({"id": QUOTE_A_ID}, quote_a, upsert=True)
        db["quotes"].replace_one({"id": QUOTE_B_ID}, quote_b, upsert=True)
        db["quotes"].replace_one({"id": QUOTE_C_ID}, quote_c, upsert=True)

        # 4. Build and persist canonical shipments via save_shipment_atomic.
        shipment_a = logi_staging_seed._shipment(
            sid=SHIPMENT_A_ID,
            customer="Công ty TNHH Lục Giác (HEXA)",
            customer_id=CUSTOMER_A_ID,
            contract_id="HDMB-LG-2026",
            status="pending",
            created="2026-10-20",
            mode="Truck",
            incoterm="DAP",
            transport={
                "booking_no": SHARED_TRIP_ID,
                "carrier": f"Nhà xe Việt Trung An Bình ({SENTINEL_TT_PRIVATE_SUPPLIER})",
                "etd": "2026-10-20",
                "eta": f"2026-10-25 ({SENTINEL_TT_UNVERIFIED_ETA})",
                "pol": "Bằng Tường (Quảng Tây)",
                "pod": "Hữu Nghị → Cầu Giấy, Hà Nội",
                "container_no": SHARED_TRUCK_PLATE,
                "qty_pkg": "18 kiện / 4.200 kg (ghép chung xe với Minh Đức)",
                "road_facts": {
                    "ltl_received_at": "2026-10-20T08:30",
                    "ltl_package_count": "18",
                    "ltl_weight_kg": "4200",
                    "ltl_consolidated_at": "2026-10-20T16:00",
                    "border_crossed_at": "2026-10-21T14:15",
                },
            },
            customs={
                "tk_no": "106688112233",
                "customs_status": True,
                "phan_luong": "Xanh",
            },
            arrival={"arrival_date": "2026-10-25", "free_time": 7},
            delivery={
                "truck_no": "29H-886.68",
                "seal_no": "SEAL-ROAD-886",
                "delivery_date": "",
                "addr": "Kho Lục Giác — Cầu Giấy, Hà Nội",
                "is_delivered": False,
            },
            details=[
                logi_staging_seed._line(
                    "Cước xe ghép Bằng Tường → Hà Nội",
                    "ROAD-LTL-BT-HN",
                    1,
                    45000000,
                    36000000,
                    8,
                    note=f"Giá vốn nội bộ TT: {SENTINEL_TT_INTERNAL_COST} | NCC: {SENTINEL_TT_PRIVATE_SUPPLIER}",
                ),
                logi_staging_seed._line(
                    "Thủ tục thông quan cửa khẩu Hữu Nghị",
                    "CUSTOMS-HN",
                    1,
                    8000000,
                    6000000,
                    8,
                    note=f"Lợi nhuận dự kiến: {SENTINEL_TT_MARGIN}",
                ),
            ],
        )
        shipment_a["sale_owner"] = "Minh Tú (CSKH & Sale Trường Thành)"

        shipment_b = logi_staging_seed._shipment(
            sid=SHIPMENT_B_ID,
            customer="Công ty CP Minh Đức",
            customer_id=CUSTOMER_B_ID,
            contract_id="HDMB-MD-2026",
            status="pending",
            created="2026-10-20",
            mode="Truck",
            incoterm="DAP",
            transport={
                "booking_no": SHARED_TRIP_ID,
                "carrier": "Nhà xe Việt Trung An Bình",
                "etd": "2026-10-20",
                "eta": "2026-10-25",
                "pol": "Bằng Tường (Quảng Tây)",
                "pod": "Hữu Nghị → KCN Yên Phong, Bắc Ninh",
                "container_no": SHARED_TRUCK_PLATE,
                "qty_pkg": f"22 kiện / 5.800 kg ({SENTINEL_FOREIGN_CUSTOMER_B})",
            },
            customs={"tk_no": "106688990011", "customs_status": True, "phan_luong": "Xanh"},
            arrival={"arrival_date": "2026-10-25", "free_time": 7},
            delivery={
                "truck_no": "29H-886.68",
                "seal_no": "SEAL-ROAD-886",
                "delivery_date": "",
                "addr": "Kho Minh Đức — KCN Yên Phong, Bắc Ninh",
                "is_delivered": False,
            },
            details=[
                logi_staging_seed._line(
                    "Cước xe ghép Bằng Tường → Bắc Ninh",
                    "ROAD-LTL-BT-BN",
                    1,
                    36000000,
                    29000000,
                    8,
                    note=SENTINEL_FOREIGN_CUSTOMER_B,
                ),
            ],
        )
        shipment_b["sale_owner"] = "Hoàng Lan (CSKH & Sale Trường Thành)"

        shipment_c = logi_staging_seed._shipment(
            sid=SHIPMENT_C_ID,
            customer="Công ty TNHH Thiết bị An Phát",
            customer_id=CUSTOMER_C_ID,
            contract_id="HDMB-AP-2026",
            status="pending",
            created="2026-10-19",
            mode="Truck",
            incoterm="DAP",
            transport={
                "booking_no": "TRIP-ROAD-2026-02",
                "carrier": "Nhà xe Đông Bắc Logistics",
                "etd": "2026-10-19",
                "eta": "2026-10-23",
                "pol": "Đông Hưng (Quảng Tây)",
                "pod": "Móng Cái → KCN Đình Vũ, Hải Phòng",
                "container_no": "15H-339.12",
                "qty_pkg": f"12 pallet / 3.100 kg ({SENTINEL_FOREIGN_CUSTOMER_C})",
                "road_facts": {
                    "ltl_received_at": "2026-10-19T09:30",
                    "ltl_package_count": "12",
                    "ltl_weight_kg": "3100",
                    "ltl_consolidated_at": "2026-10-19T14:00",
                    "border_crossed_at": "2026-10-20T16:30",
                },
            },
            customs={"tk_no": "106688773311", "customs_status": True, "phan_luong": "Xanh"},
            arrival={"arrival_date": "2026-10-23", "free_time": 5},
            delivery={
                "truck_no": "15H-339.12",
                "seal_no": "SEAL-ROAD-339",
                "delivery_date": "",
                "addr": "Kho An Phát — KCN Đình Vũ, Hải Phòng",
                "is_delivered": False,
            },
            details=[
                logi_staging_seed._line(
                    "Cước đường bộ Đông Hưng → Hải Phòng",
                    "ROAD-LTL-DH-HP",
                    1,
                    31000000,
                    24000000,
                    8,
                    note=SENTINEL_FOREIGN_CUSTOMER_C,
                ),
            ],
        )
        shipment_c["sale_owner"] = "Quốc Khánh (CSKH & Sale Trường Thành)"

        for ship_doc, named_place in (
            (shipment_a, "Hà Nội"),
            (shipment_b, "Bắc Ninh"),
            (shipment_c, "Hải Phòng"),
        ):
            ship_doc.setdefault("data", {}).setdefault("0.0", {})["execution_profile"] = {
                "incoterm_version": "2020",
                "incoterm_named_place": named_place,
                "load_model": "LTL",
                "service_scope": [
                    "ORIGIN_PICKUP",
                    "CROSS_BORDER_COORDINATION",
                    "MAIN_CARRIAGE",
                    "IMPORT_CUSTOMS",
                    "FINAL_DELIVERY",
                ],
                "service_scope_confirmed": True,
                "cargo_insurance": {"status": "UNKNOWN"},
            }
            existing = db["shipments"].find_one({"id": ship_doc["id"]})
            if existing is None:
                ok = core_db.save_shipment_atomic(copy.deepcopy(ship_doc), actor="staging.support")
                if not ok:
                    raise RuntimeError(f"Không lưu được lô thử nghiệm {ship_doc['id']}: {core_db.get_last_db_error()}")

        # 5. Upload real PDF files into isolated GridFS via core.shipment_attachments.upload_attachment.
        att_lg_pl_v2 = self._upload_trial_pdf(
            core_att,
            shipment_id=SHIPMENT_A_ID,
            file_name="Packing-List-Luc-Giac-v2.pdf",
            category="transport",
            title="HEXA PACKING LIST v2 (APPROVED FOR LUC GIAC)",
            lines=[
                f"Shipment: {SHIPMENT_A_ID}",
                "Customer: Cong ty TNHH Luc Giac",
                "Version: v2 (TT verified and published)",
                "Cargo: 18 packages / 4,200 kg",
            ],
        )
        att_lg_pl_v1_stale = self._upload_trial_pdf(
            core_att,
            shipment_id=SHIPMENT_A_ID,
            file_name="Packing-List-Luc-Giac-v1-stale.pdf",
            category="transport",
            title="HEXA PACKING LIST v1 (STALE SUPERSEDED VERSION)",
            lines=[
                f"Shipment: {SHIPMENT_A_ID}",
                "Version: v1 (superseded by v2 - must not be downloadable)",
            ],
        )
        att_lg_pi_v1 = self._upload_trial_pdf(
            core_att,
            shipment_id=SHIPMENT_A_ID,
            file_name="Proforma-Invoice-Luc-Giac-v1.pdf",
            category="contract",
            title="HEXA PROFORMA INVOICE v1 (APPROVED FOR LUC GIAC)",
            lines=[
                f"Shipment: {SHIPMENT_A_ID}",
                "Customer: Cong ty TNHH Luc Giac",
                "Version: v1 (TT verified and published)",
            ],
        )
        att_lg_cost_internal = self._upload_trial_pdf(
            core_att,
            shipment_id=SHIPMENT_A_ID,
            file_name="Bang-Ke-Gia-Von-Noi-Bo-TT.pdf",
            category="other",
            title="TT INTERNAL COST SHEET (NEVER FOR CUSTOMER)",
            lines=[
                f"Internal cost sentinel: {SENTINEL_TT_INTERNAL_COST}",
                f"Supplier sentinel: {SENTINEL_TT_PRIVATE_SUPPLIER}",
                f"Margin sentinel: {SENTINEL_TT_MARGIN}",
            ],
        )
        att_md_pl_v1 = self._upload_trial_pdf(
            core_att,
            shipment_id=SHIPMENT_B_ID,
            file_name="Packing-List-Minh-Duc-v1.pdf",
            category="transport",
            title="MINH DUC PACKING LIST v1 (CUSTOMER B ON SAME TRUCK)",
            lines=[
                f"Shipment: {SHIPMENT_B_ID}",
                f"Foreign sentinel: {SENTINEL_FOREIGN_CUSTOMER_B}",
                "Customer: Cong ty CP Minh Duc",
            ],
        )
        att_ap_pl_v1 = self._upload_trial_pdf(
            core_att,
            shipment_id=SHIPMENT_C_ID,
            file_name="Packing-List-An-Phat-v1.pdf",
            category="transport",
            title="AN PHAT PACKING LIST v1 (APPROVED FOR AN PHAT)",
            lines=[
                f"Shipment: {SHIPMENT_C_ID}",
                "Customer: Cong ty TNHH Thiet bi An Phat",
                "Version: v1 (TT verified and published)",
                "Cargo: 12 pallets / 3,100 kg",
            ],
        )

        # 6. Populate trial adapter collections (explicitly bridging the schema gaps documented in SCHEMA_GAP_REPORT).
        db["hexa_trial_shipment_links"].delete_many({})
        db["hexa_trial_shipment_links"].insert_many(
            [
                {
                    "shipment_id": SHIPMENT_A_ID,
                    "customer_id": CUSTOMER_A_ID,
                    "trip_id": SHARED_TRIP_ID,
                    "shared_truck_plate": SHARED_TRUCK_PLATE,
                    "transport_mode": "ROAD",
                    "quote_id": QUOTE_A_ID,
                    "cargo_summary": "Nội thất văn phòng — 18 kiện / 4.200 kg",
                    "route_summary": "Bằng Tường (Quảng Tây) → Hữu Nghị → Cầu Giấy, Hà Nội",
                    "internal_cost_vnd": 42000000,
                    "internal_margin_vnd": 11000000,
                    "internal_supplier": f"Foshan Hexa Furniture Factory ({SENTINEL_TT_PRIVATE_SUPPLIER})",
                    "internal_carrier_vendor": "Nhà xe Việt Trung An Bình (hợp đồng mua chuyến nội bộ TT)",
                    "unverified_eta": f"2026-10-25 ({SENTINEL_TT_UNVERIFIED_ETA})",
                },
                {
                    "shipment_id": SHIPMENT_B_ID,
                    "customer_id": CUSTOMER_B_ID,
                    "trip_id": SHARED_TRIP_ID,
                    "shared_truck_plate": SHARED_TRUCK_PLATE,
                    "transport_mode": "ROAD",
                    "quote_id": QUOTE_B_ID,
                    "cargo_summary": "Linh kiện cơ khí — 22 kiện / 5.800 kg",
                    "route_summary": "Bằng Tường (Quảng Tây) → Hữu Nghị → KCN Yên Phong, Bắc Ninh",
                    "internal_cost_vnd": 29000000,
                    "internal_margin_vnd": 7000000,
                    "internal_supplier": f"Guangxi Dongxing Metal Co. ({SENTINEL_FOREIGN_CUSTOMER_B})",
                    "internal_carrier_vendor": "Nhà xe Việt Trung An Bình",
                    "unverified_eta": "2026-10-25",
                },
                {
                    "shipment_id": SHIPMENT_C_ID,
                    "customer_id": CUSTOMER_C_ID,
                    "trip_id": "TRIP-ROAD-2026-02",
                    "shared_truck_plate": "15H-339.12",
                    "transport_mode": "ROAD",
                    "quote_id": QUOTE_C_ID,
                    "cargo_summary": "Thiết bị điện công nghiệp — 12 pallet / 3.100 kg",
                    "route_summary": "Đông Hưng (Quảng Tây) → Móng Cái → KCN Đình Vũ, Hải Phòng",
                    "internal_cost_vnd": 24000000,
                    "internal_margin_vnd": 7000000,
                    "internal_supplier": f"Fangchenggang Electric Equipment Co. ({SENTINEL_FOREIGN_CUSTOMER_C})",
                    "internal_carrier_vendor": "Nhà xe Đông Bắc Logistics",
                    "unverified_eta": "2026-10-23",
                },
            ]
        )

        db["hexa_trial_events"].delete_many({})
        db["hexa_trial_events"].insert_many(
            [
                {
                    "id": "EVT-LG-01-PICKUP",
                    "version": "v1",
                    "customer_id": CUSTOMER_A_ID,
                    "shipment_id": SHIPMENT_A_ID,
                    "trip_id": SHARED_TRIP_ID,
                    "stage_id": "pickup",
                    "public_title": "Đã nhận 18 kiện hàng Lục Giác tại kho Bằng Tường và xếp lên xe 29H-886.68",
                    "occurred_at": "2026-10-20T08:30:00Z",
                    "verified": True,
                    "verified_at": "2026-10-20T09:15:00Z",
                    "visibility": "CUSTOMER",
                    "private_notes": f"Chi phí gom hàng nội bộ: {SENTINEL_TT_INTERNAL_COST}",
                },
                {
                    "id": "EVT-LG-02-BORDER",
                    "version": "v2",
                    "customer_id": CUSTOMER_A_ID,
                    "shipment_id": SHIPMENT_A_ID,
                    "trip_id": SHARED_TRIP_ID,
                    "stage_id": "road-border",
                    "public_title": "Xe 29H-886.68 đã hoàn tất thông quan và qua cửa khẩu Hữu Nghị",
                    "occurred_at": "2026-10-21T14:15:00Z",
                    "verified": True,
                    "verified_at": "2026-10-21T15:00:00Z",
                    "visibility": "CUSTOMER",
                    "private_notes": f"Nhà cung cấp nội bộ: {SENTINEL_TT_PRIVATE_SUPPLIER}",
                },
                {
                    "id": "EVT-LG-03-ETA-UNVERIFIED",
                    "version": "v1",
                    "customer_id": CUSTOMER_A_ID,
                    "shipment_id": SHIPMENT_A_ID,
                    "trip_id": SHARED_TRIP_ID,
                    "stage_id": "delivery",
                    "public_title": f"Dự kiến giao hàng tại Cầu Giấy ngày 2026-10-25 ({SENTINEL_TT_UNVERIFIED_ETA})",
                    "occurred_at": "2026-10-25T10:00:00Z",
                    "verified": False,
                    "verified_at": "",
                    "visibility": "CUSTOMER",
                    "private_notes": "ETA tài xế báo miệng, TT chưa xác minh — CẤM hiển thị cho khách",
                },
                {
                    "id": "EVT-LG-04-ETA-INTERNAL",
                    "version": "v1",
                    "customer_id": CUSTOMER_A_ID,
                    "shipment_id": SHIPMENT_A_ID,
                    "trip_id": SHARED_TRIP_ID,
                    "stage_id": "delivery",
                    "public_title": f"ETA điều vận nội bộ TT 2026-10-25 ({SENTINEL_TT_UNVERIFIED_ETA})",
                    "occurred_at": "2026-10-25T18:00:00Z",
                    "verified": True,
                    "verified_at": "2026-10-22T08:00:00Z",
                    "visibility": "TT",
                    "private_notes": "Mốc điều vận nội bộ của TT",
                },
                {
                    "id": "EVT-MD-02-SHARED-TRUCK",
                    "version": "v1",
                    "customer_id": CUSTOMER_B_ID,
                    "shipment_id": SHIPMENT_A_ID,
                    "trip_id": SHARED_TRIP_ID,
                    "stage_id": "pickup",
                    "public_title": f"Nhận 22 kiện của Minh Đức trên cùng chuyến xe ({SENTINEL_FOREIGN_CUSTOMER_B})",
                    "occurred_at": "2026-10-20T09:00:00Z",
                    "verified": True,
                    "verified_at": "2026-10-20T09:30:00Z",
                    "visibility": "CUSTOMER",
                    "private_notes": "Sự kiện của Khách B đi chung xe — Khách A không được thấy",
                },
                {
                    "id": "EVT-MD-01-PICKUP",
                    "version": "v1",
                    "customer_id": CUSTOMER_B_ID,
                    "shipment_id": SHIPMENT_B_ID,
                    "trip_id": SHARED_TRIP_ID,
                    "stage_id": "pickup",
                    "public_title": "Đã nhận 22 kiện hàng Minh Đức tại kho Bằng Tường (xe 29H-886.68)",
                    "occurred_at": "2026-10-20T09:00:00Z",
                    "verified": True,
                    "verified_at": "2026-10-20T09:30:00Z",
                    "visibility": "CUSTOMER",
                    "private_notes": "",
                },
                {
                    "id": "EVT-AP-01-PICKUP",
                    "version": "v1",
                    "customer_id": CUSTOMER_C_ID,
                    "shipment_id": SHIPMENT_C_ID,
                    "trip_id": "TRIP-ROAD-2026-02",
                    "stage_id": "pickup",
                    "public_title": "Đã nhận 12 pallet thiết bị điện An Phát tại kho Đông Hưng (xe 15H-339.12)",
                    "occurred_at": "2026-10-19T09:30:00Z",
                    "verified": True,
                    "verified_at": "2026-10-19T10:30:00Z",
                    "visibility": "CUSTOMER",
                    "private_notes": "",
                },
                {
                    "id": "EVT-AP-02-CUSTOMS",
                    "version": "v1",
                    "customer_id": CUSTOMER_C_ID,
                    "shipment_id": SHIPMENT_C_ID,
                    "trip_id": "TRIP-ROAD-2026-02",
                    "stage_id": "customs-import",
                    "public_title": "Đã thông quan nhập khẩu tại Móng Cái — xác nhận lịch giao kho Đình Vũ ngày 2026-10-23",
                    "occurred_at": "2026-10-21T11:00:00Z",
                    "verified": True,
                    "verified_at": "2026-10-21T11:30:00Z",
                    "visibility": "CUSTOMER",
                    "verified_warehouse_eta": "2026-10-23",
                    "private_notes": "",
                },
            ]
        )

        db["hexa_trial_documents"].delete_many({})
        db["hexa_trial_documents"].insert_many(
            [
                {
                    "id": "DOC-LG-PL",
                    "version": "v2",
                    "customer_id": CUSTOMER_A_ID,
                    "shipment_id": SHIPMENT_A_ID,
                    "trip_id": SHARED_TRIP_ID,
                    "kind": "PL",
                    "status": "AVAILABLE",
                    "visibility": "CUSTOMER",
                    "verified": True,
                    "public_title": "Packing List Lục Giác (Bản v2 đã duyệt)",
                    "file_name": "Packing-List-Luc-Giac-v2.pdf",
                    "attachment_id": att_lg_pl_v2["id"],
                    "attachment_shipment_id": SHIPMENT_A_ID,
                },
                {
                    "id": "DOC-LG-PL",
                    "version": "v1",
                    "customer_id": CUSTOMER_A_ID,
                    "shipment_id": SHIPMENT_A_ID,
                    "trip_id": SHARED_TRIP_ID,
                    "kind": "PL",
                    "status": "AVAILABLE",
                    "visibility": "CUSTOMER",
                    "verified": True,
                    "public_title": "Packing List Lục Giác (Bản v1 cũ - đã thu hồi)",
                    "file_name": "Packing-List-Luc-Giac-v1-stale.pdf",
                    "attachment_id": att_lg_pl_v1_stale["id"],
                    "attachment_shipment_id": SHIPMENT_A_ID,
                },
                {
                    "id": "DOC-LG-PI",
                    "version": "v1",
                    "customer_id": CUSTOMER_A_ID,
                    "shipment_id": SHIPMENT_A_ID,
                    "trip_id": SHARED_TRIP_ID,
                    "kind": "PI",
                    "status": "AVAILABLE",
                    "visibility": "CUSTOMER",
                    "verified": True,
                    "public_title": "Proforma Invoice Lục Giác (Bản v1)",
                    "file_name": "Proforma-Invoice-Luc-Giac-v1.pdf",
                    "attachment_id": att_lg_pi_v1["id"],
                    "attachment_shipment_id": SHIPMENT_A_ID,
                },
                {
                    "id": "DOC-LG-COST",
                    "version": "v1",
                    "customer_id": CUSTOMER_A_ID,
                    "shipment_id": SHIPMENT_A_ID,
                    "trip_id": SHARED_TRIP_ID,
                    "kind": "COST",
                    "status": "AVAILABLE",
                    "visibility": "TT",
                    "verified": True,
                    "public_title": f"Bảng tính giá vốn & NCC nội bộ TT ({SENTINEL_TT_INTERNAL_COST})",
                    "file_name": "Bang-Ke-Gia-Von-Noi-Bo-TT.pdf",
                    "attachment_id": att_lg_cost_internal["id"],
                    "attachment_shipment_id": SHIPMENT_A_ID,
                },
                # Foreign customer's document also present on the shared trip pool to test cross-customer filtering
                {
                    "id": "DOC-MD-PL",
                    "version": "v1",
                    "customer_id": CUSTOMER_B_ID,
                    "shipment_id": SHIPMENT_A_ID,
                    "trip_id": SHARED_TRIP_ID,
                    "kind": "PL",
                    "status": "AVAILABLE",
                    "visibility": "CUSTOMER",
                    "verified": True,
                    "public_title": f"Packing List Minh Đức trên cùng chuyến xe ({SENTINEL_FOREIGN_CUSTOMER_B})",
                    "file_name": "Packing-List-Minh-Duc-v1.pdf",
                    "attachment_id": att_md_pl_v1["id"],
                    "attachment_shipment_id": SHIPMENT_B_ID,
                },
                {
                    "id": "DOC-MD-PL",
                    "version": "v1",
                    "customer_id": CUSTOMER_B_ID,
                    "shipment_id": SHIPMENT_B_ID,
                    "trip_id": SHARED_TRIP_ID,
                    "kind": "PL",
                    "status": "AVAILABLE",
                    "visibility": "CUSTOMER",
                    "verified": True,
                    "public_title": "Packing List Minh Đức (Bản v1)",
                    "file_name": "Packing-List-Minh-Duc-v1.pdf",
                    "attachment_id": att_md_pl_v1["id"],
                    "attachment_shipment_id": SHIPMENT_B_ID,
                },
                {
                    "id": "DOC-AP-PL",
                    "version": "v1",
                    "customer_id": CUSTOMER_C_ID,
                    "shipment_id": SHIPMENT_C_ID,
                    "trip_id": "TRIP-ROAD-2026-02",
                    "kind": "PL",
                    "status": "AVAILABLE",
                    "visibility": "CUSTOMER",
                    "verified": True,
                    "public_title": "Packing List An Phát (Bản v1 đã duyệt)",
                    "file_name": "Packing-List-An-Phat-v1.pdf",
                    "attachment_id": att_ap_pl_v1["id"],
                    "attachment_shipment_id": SHIPMENT_C_ID,
                },
            ]
        )

        # Default-deny initial state: neither Lục Giác nor Minh Đức has a PUBLISHED
        # manifest on boot. There are no pre-populated approved_by/approved_at fields
        # and zero shared events, documents, or quotes until an authorized TT staff
        # member explicitly approves and publishes them.
        db["hexa_trial_publications"].delete_many({})

        self._seeded = True

    @staticmethod
    def _build_trial_quote(
        core_quotes: Any,
        *,
        quote_id: str,
        quote_no: str,
        customer_id: str,
        customer_name: str,
        factory_name: str,
        pickup_address: str,
        lines: list[dict[str, Any]],
        target_status: str,
    ) -> dict[str, Any]:
        spec = {
            "id": quote_id,
            "quote_no": quote_no,
            "customer_id": customer_id,
            "customer_name": customer_name,
            "sales_owner": "Minh Tú (TT Sale)",
            "origin": "Bằng Tường (Quảng Tây)",
            "destination": "Hà Nội / Bắc Ninh",
            "route": "Hữu Nghị (Lạng Sơn)",
            "incoterm": "DAP",
            "transport_mode": "Road",
            "goods_description": "Hàng nội thất / cơ khí ghép xe đường bộ",
            "expected_delivery_date": "2026-10-25",
            "factory_lots": [
                {
                    "lot_no": 1,
                    "factory_name": factory_name,
                    "pickup_address": pickup_address,
                }
            ],
            "service_lines": lines,
            "fx_snapshot": {
                "rates_to_vnd": {"USD": 25500, "CNY": 3550, "VND": 1},
                "source": "Tỷ giá nội bộ Trường Thành",
            },
            "entrusted_import": {
                "active": False,
                "goods_value": 0,
                "goods_currency": "USD",
                "rate_pct": 0,
                "review_requested": False,
                "review_reason": "",
                "high_value_review_policy": {"status": "POLICY_NOT_CONFIGURED"},
                "source": "",
            },
            "remittance_estimate": {
                "remitted_amount_usd": 0,
                "bank_fee_pct": 0,
                "swift_fee_usd": 0,
                "receiving_bank_fee_usd": 0,
                "agent_conversion_fee_usd": 0,
                "rmb_conversion_fee_cny": 0,
            },
            "include_remittance_in_cost": False,
            "assumptions": ["Báo giá dịch vụ vận chuyển đường bộ ghép xe."],
        }
        quote = core_quotes.new_quote_document(spec)
        quote["id"] = quote_id
        quote["quote_no"] = quote_no
        for next_state in ("READY_FOR_REVIEW", target_status):
            quote = core_quotes.transition_quote(quote, next_state, actor="tt.sale")
        return core_quotes.prepare_quote_for_persistence(quote, actor="tt.sale")

    @staticmethod
    def _upload_trial_pdf(
        core_att: Any,
        *,
        shipment_id: str,
        file_name: str,
        category: str,
        title: str,
        lines: list[str],
    ) -> dict[str, Any]:
        payload = _pdf_bytes(title, lines)
        outcome = core_att.upload_attachment(
            shipment_id=shipment_id,
            category=category,
            file_name=file_name,
            mime="application/pdf",
            data=payload,
            uploaded_by="staging.support",
            storage_backend="gridfs",
        )
        if not outcome.get("ok"):
            raise RuntimeError(f"Không tải lên được chứng từ thử nghiệm {file_name}: {outcome}")
        return dict(outcome["record"])

    def get_trial_session_token(self, role_or_customer: str) -> str:
        """Server-side helper for internal test/QA harnesses to obtain an opaque session token.

        Not exposed on any customer HTTP endpoint.
        """
        self.ensure_seeded()
        key = str(role_or_customer or "").strip()
        if key not in self._role_tokens:
            raise KeyError(f"Unknown trial role/customer key: {key}")
        return self._role_tokens[key]

    def verify_internal_qa_key(self, candidate_key: str | None) -> bool:
        """Constant-time check for the server-only internal QA key."""
        self.ensure_seeded()
        provided = str(candidate_key or "").strip()
        if not provided or not self.internal_qa_key:
            return False
        return hmac.compare_digest(provided, self.internal_qa_key)

    def resolve_principal(self, session_token: str | None) -> dict[str, Any]:
        """Resolve caller principal strictly from the server-owned session store.

        Any unknown, empty, or predictable sample token returns an
        unauthenticated principal. Query parameters or client headers carrying
        ``customer_id`` are NEVER read.
        """
        self.ensure_seeded()
        token = str(session_token or "").strip()
        if not token or token in FORBIDDEN_SAMPLE_TOKENS:
            return {"authenticated": False, "kind": "customer", "customer_id": ""}
        entry = self.sessions.get(token)
        if not entry:
            return {"authenticated": False, "kind": "customer", "customer_id": ""}
        return copy.deepcopy(entry["principal"])

    def resolve_session_summary(self, session_token: str | None) -> dict[str, Any]:
        """Return safe caller-scoped customer session metadata without exposing any session tokens."""
        self.ensure_seeded()
        token = str(session_token or "").strip()
        if not token or token in FORBIDDEN_SAMPLE_TOKENS or token not in self.sessions:
            return {
                "authenticated": False,
                "label": "Ẩn danh — Chưa đăng nhập",
                "principal": {
                    "authenticated": False,
                    "kind": "customer",
                    "customer_id": "",
                    "display_name": "Khách ẩn danh",
                },
                "default_shipment_id": "",
            }
        entry = self.sessions[token]
        if entry["principal"].get("kind") == "tt_staff":
            return {
                "authenticated": False,
                "label": "Ẩn danh — Chưa đăng nhập khách hàng",
                "principal": {
                    "authenticated": False,
                    "kind": "customer",
                    "customer_id": "",
                    "display_name": "Khách ẩn danh",
                },
                "default_shipment_id": "",
            }
        return {
            "authenticated": bool(entry["principal"].get("authenticated")),
            "label": entry["label"],
            "principal": copy.deepcopy(entry["principal"]),
            "default_shipment_id": entry["default_shipment_id"],
        }

    def resolve_tt_session_summary(self, session_token: str | None) -> dict[str, Any]:
        """Return safe TT staff session metadata without exposing any session tokens."""
        self.ensure_seeded()
        token = str(session_token or "").strip()
        if not token or token in FORBIDDEN_SAMPLE_TOKENS or token not in self.sessions:
            return {
                "authenticated": False,
                "label": "Chưa đăng nhập nhân sự Trường Thành",
                "principal": {
                    "authenticated": False,
                    "kind": "tt_staff",
                    "username": "",
                    "role": "",
                    "display_name": "Chưa xác thực",
                },
                "default_shipment_id": SHIPMENT_A_ID,
            }
        entry = self.sessions[token]
        principal = entry["principal"]
        if principal.get("kind") != "tt_staff" or not principal.get("authenticated"):
            return {
                "authenticated": False,
                "label": "Chưa đăng nhập nhân sự Trường Thành",
                "principal": {
                    "authenticated": False,
                    "kind": "tt_staff",
                    "username": "",
                    "role": "",
                    "display_name": "Chưa xác thực",
                },
                "default_shipment_id": SHIPMENT_A_ID,
            }
        return {
            "authenticated": True,
            "label": entry["label"],
            "principal": copy.deepcopy(principal),
            "default_shipment_id": entry["default_shipment_id"],
        }

    def authenticate_customer_login(
        self,
        *,
        username: str,
        passcode: str,
    ) -> tuple[str, dict[str, Any]]:
        """Authenticate a trial customer account and bind exactly 1 customer_id to an opaque server session.

        Logistics internal accounts (including ``viewer``) and invalid credentials
        are rejected with ``PublicationDenied``. Any client-supplied ``customer_id``
        is ignored by the caller.
        """
        from core import auth as core_auth
        from core import database as core_db

        self.ensure_seeded()
        db = core_db.get_db()
        if db is None:
            raise PublicationDenied()

        norm_user = str(username or "").strip().lower()
        raw_pass = str(passcode or "")
        if not norm_user or not raw_pass:
            self._record_audit(
                action="CUSTOMER_LOGIN",
                principal={"kind": "customer", "customer_id": ""},
                shipment_id="",
                allowed=False,
                detail="missing credentials",
            )
            raise PublicationDenied()

        account = db["hexa_trial_customer_accounts"].find_one({"username": norm_user}, {"_id": 0})
        if (
            not account
            or not account.get("active", False)
            or account.get("kind") != "customer"
            or not str(account.get("customer_id") or "").strip()
            or not core_auth.verify_password(raw_pass, str(account.get("password_hash") or ""))
        ):
            self._record_audit(
                action="CUSTOMER_LOGIN",
                principal={"kind": "customer", "customer_id": ""},
                shipment_id="",
                allowed=False,
                detail=f"denied login for username={norm_user}",
            )
            raise PublicationDenied()

        bound_customer_id = str(account["customer_id"]).strip()
        issued_token = f"hx_cust_{secrets.token_urlsafe(24)}"
        self.sessions[issued_token] = {
            "role_key": str(account.get("role_key") or "customer"),
            "label": str(account.get("label") or account.get("display_name") or bound_customer_id),
            "principal": {
                "authenticated": True,
                "kind": "customer",
                "customer_id": bound_customer_id,
                "username": norm_user,
                "display_name": str(account.get("display_name") or norm_user),
            },
            "default_shipment_id": str(account.get("default_shipment_id") or ""),
        }
        summary = self.resolve_session_summary(issued_token)
        self._record_audit(
            action="CUSTOMER_LOGIN",
            principal=summary["principal"],
            shipment_id=summary["default_shipment_id"],
            allowed=True,
            detail=f"username={norm_user} bound to customer_id={bound_customer_id}",
        )
        return issued_token, summary

    def authenticate_tt_staff_login(
        self,
        *,
        username: str,
        passcode: str,
    ) -> tuple[str, dict[str, Any]]:
        """Authenticate an authorized TT staff member (requires ``operations_write`` in ``core.auth``).

        Customers and ``viewer`` role accounts are rejected with ``PublicationDenied``.
        """
        from core import auth as core_auth
        from core import database as core_db
        from core import users as core_users

        self.ensure_seeded()
        db = core_db.get_db()
        if db is None:
            raise PublicationDenied()

        norm_user = str(username or "").strip().lower()
        raw_pass = str(passcode or "")
        if not norm_user or not raw_pass:
            self._record_audit(
                action="TT_STAFF_LOGIN",
                principal={"kind": "tt_staff", "customer_id": ""},
                shipment_id="",
                allowed=False,
                detail="missing credentials",
            )
            raise PublicationDenied()

        user_doc = db["users"].find_one({"username": norm_user}, {"_id": 0})
        authed = core_users.authenticate(user_doc or {}, raw_pass) if user_doc else None
        role = str((authed or {}).get("role") or "").strip().lower()
        perms = core_auth._role_permissions(role) if authed else set()
        if not authed or ("*" not in perms and "operations_write" not in perms):
            self._record_audit(
                action="TT_STAFF_LOGIN",
                principal={"kind": "tt_staff", "customer_id": ""},
                shipment_id="",
                allowed=False,
                detail=f"denied TT login for username={norm_user} role={role or 'none'}",
            )
            raise PublicationDenied()

        issued_token = f"hx_tt_{secrets.token_urlsafe(24)}"
        self.sessions[issued_token] = {
            "role_key": "tt_staff",
            "label": f"Nội bộ TT — {authed['display_name']} ({authed['username']})",
            "principal": {
                "authenticated": True,
                "kind": "tt_staff",
                "user_id": str(authed["user_id"]),
                "username": str(authed["username"]),
                "role": role,
                "display_name": str(authed["display_name"]),
                "customer_id": "",
            },
            "default_shipment_id": SHIPMENT_A_ID,
        }
        summary = self.resolve_tt_session_summary(issued_token)
        self._record_audit(
            action="TT_STAFF_LOGIN",
            principal=summary["principal"],
            shipment_id=SHIPMENT_A_ID,
            allowed=True,
            detail=f"username={norm_user} role={role}",
        )
        return issued_token, summary

    def logout_session(self, session_token: str | None) -> None:
        """Invalidate a dynamically minted login session token."""
        self.ensure_seeded()
        token = str(session_token or "").strip()
        if token and token not in self._role_tokens.values():
            self.sessions.pop(token, None)

    def _require_authorized_tt_staff(self, session_token: str | None) -> dict[str, Any]:
        """Verify caller holds an authenticated TT staff session with ``operations_write``."""
        from core import auth as core_auth

        self.ensure_seeded()
        token = str(session_token or "").strip()
        if not token or token in FORBIDDEN_SAMPLE_TOKENS or token not in self.sessions:
            raise PublicationDenied()
        principal = self.sessions[token]["principal"]
        role = str(principal.get("role") or "").strip().lower()
        perms = core_auth._role_permissions(role)
        if not (
            principal.get("authenticated") is True
            and principal.get("kind") == "tt_staff"
            and str(principal.get("username") or "").strip()
            and ("*" in perms or "operations_write" in perms)
        ):
            raise PublicationDenied()
        return copy.deepcopy(principal)

    def inspect_shipment_for_tt_staff(
        self,
        *,
        session_token: str | None,
        shipment_id: str,
    ) -> dict[str, Any]:
        """Return internal shipment file + candidate items + publication manifest for authorized TT staff."""
        from core import database as core_db

        self.ensure_seeded()
        try:
            principal = self._require_authorized_tt_staff(session_token)
        except PublicationDenied:
            self._record_audit(
                action="TT_INSPECT_SHIPMENT",
                principal=self.resolve_principal(session_token),
                shipment_id=str(shipment_id or ""),
                allowed=False,
                detail="unauthorized caller on TT shipment desk",
            )
            raise

        db = core_db.get_db()
        if db is None:
            raise PublicationDenied()

        sid = str(shipment_id or "").strip()
        shipment = self._load_adapted_shipment(db, sid)
        if not shipment:
            raise PublicationDenied()

        cust_id = shipment["customer_id"]
        cust_doc = db["customers"].find_one({"id": cust_id}, {"_id": 0}) or {}
        link = db["hexa_trial_shipment_links"].find_one({"shipment_id": sid}, {"_id": 0}) or {}
        quote_id = shipment["quote_id"]
        quote = db["quotes"].find_one({"id": quote_id}, {"_id": 0}) if quote_id else None
        calc = (quote or {}).get("calculation") or {}

        raw_events = list(
            db["hexa_trial_events"].find(
                {"shipment_id": sid, "customer_id": cust_id},
                {"_id": 0},
            )
        )
        candidate_events = [
            {
                "id": str(ev.get("id") or ""),
                "version": str(ev.get("version") or ""),
                "stage_id": str(ev.get("stage_id") or ""),
                "public_title": str(ev.get("public_title") or ""),
                "occurred_at": str(ev.get("occurred_at") or ""),
                "verified": bool(ev.get("verified")),
                "verified_at": str(ev.get("verified_at") or ""),
                "visibility": str(ev.get("visibility") or ""),
                "eligible_for_customer": bool(
                    ev.get("verified") is True
                    and str(ev.get("verified_at") or "").strip()
                    and ev.get("visibility") == "CUSTOMER"
                ),
            }
            for ev in raw_events
        ]

        raw_docs = list(
            db["hexa_trial_documents"].find(
                {"shipment_id": sid, "customer_id": cust_id},
                {"_id": 0},
            )
        )
        candidate_documents = [
            {
                "id": str(doc.get("id") or ""),
                "version": str(doc.get("version") or ""),
                "kind": str(doc.get("kind") or ""),
                "public_title": str(doc.get("public_title") or ""),
                "file_name": str(doc.get("file_name") or ""),
                "verified": bool(doc.get("verified")),
                "visibility": str(doc.get("visibility") or ""),
                "eligible_for_customer": bool(
                    doc.get("verified") is True
                    and doc.get("visibility") == "CUSTOMER"
                    and doc.get("status") == "AVAILABLE"
                ),
            }
            for doc in raw_docs
        ]

        publication = (
            db["hexa_trial_publications"].find_one(
                {"shipment_id": sid, "customer_id": cust_id},
                {"_id": 0},
            )
            or {
                "shipment_id": sid,
                "customer_id": cust_id,
                "state": "UNPUBLISHED",
                "approved_by": "",
                "approved_at": "",
                "revoked_by": "",
                "revoked_at": "",
                "event_versions": {},
                "document_versions": {},
                "quote": None,
                "history": [],
            }
        )

        return {
            "shipment": {
                "shipment_id": sid,
                "customer_id": cust_id,
                "customer_name": str(cust_doc.get("name") or cust_id),
                "transport_mode": shipment["transport_mode"],
                "trip_id": str(link.get("trip_id") or SHARED_TRIP_ID),
                "shared_truck_plate": str(link.get("shared_truck_plate") or SHARED_TRUCK_PLATE),
                "internal_status": shipment["status"],
                "unverified_eta_note": "ETA dự kiến 2026-10-25 (Tài xế báo miệng, TT chưa xác minh — hệ thống khóa chia sẻ)",
                "internal_cost_summary_vnd": calc.get("estimated_cost_vnd"),
                "internal_margin_summary_vnd": calc.get("estimated_margin_vnd"),
                "selling_total_vnd": calc.get("selling_price_total_vnd"),
            },
            "candidate_events": candidate_events,
            "candidate_documents": candidate_documents,
            "candidate_quote": (
                {
                    "id": str(quote.get("id") or ""),
                    "version": str(quote.get("version") or ""),
                    "status": str(quote.get("status") or ""),
                    "selling_total_vnd": calc.get("selling_price_total_vnd"),
                }
                if quote
                else None
            ),
            "publication": publication,
            "actor": principal["username"],
        }

    def publish_shipment_for_customer(
        self,
        *,
        session_token: str | None,
        shipment_id: str,
        event_versions: Mapping[str, Any] | None = None,
        document_versions: Mapping[str, Any] | None = None,
        quote: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Approve & publish selected verified milestones, document versions, and selling quote."""
        from core import database as core_db

        self.ensure_seeded()
        try:
            principal = self._require_authorized_tt_staff(session_token)
        except PublicationDenied:
            self._record_audit(
                action="PUBLISH_SHIPMENT",
                principal=self.resolve_principal(session_token),
                shipment_id=str(shipment_id or ""),
                allowed=False,
                detail="unauthorized caller attempted publish",
            )
            raise

        db = core_db.get_db()
        if db is None:
            raise PublicationDenied()

        sid = str(shipment_id or "").strip()
        shipment = self._load_adapted_shipment(db, sid)
        if not shipment:
            raise PublicationDenied()
        cust_id = shipment["customer_id"]

        clean_events: dict[str, str] = {}
        if isinstance(event_versions, Mapping):
            for raw_ev_id, raw_ver in event_versions.items():
                ev_id = str(raw_ev_id or "").strip()
                ev_ver = str(raw_ver or "").strip()
                if not ev_id or not ev_ver:
                    continue
                ev_row = db["hexa_trial_events"].find_one(
                    {
                        "shipment_id": sid,
                        "customer_id": cust_id,
                        "id": ev_id,
                        "version": ev_ver,
                        "verified": True,
                        "visibility": "CUSTOMER",
                    },
                    {"_id": 0},
                )
                if ev_row and str(ev_row.get("verified_at") or "").strip():
                    clean_events[ev_id] = ev_ver

        clean_docs: dict[str, str] = {}
        if isinstance(document_versions, Mapping):
            for raw_doc_id, raw_ver in document_versions.items():
                doc_id = str(raw_doc_id or "").strip()
                doc_ver = str(raw_ver or "").strip()
                if not doc_id or not doc_ver:
                    continue
                doc_row = db["hexa_trial_documents"].find_one(
                    {
                        "shipment_id": sid,
                        "customer_id": cust_id,
                        "id": doc_id,
                        "version": doc_ver,
                        "verified": True,
                        "visibility": "CUSTOMER",
                        "status": "AVAILABLE",
                    },
                    {"_id": 0},
                )
                if doc_row:
                    clean_docs[doc_id] = doc_ver

        clean_quote: dict[str, str] | None = None
        if isinstance(quote, Mapping):
            req_q_id = str(quote.get("id") or "").strip()
            req_q_ver = str(quote.get("version") or "").strip()
            if req_q_id and req_q_ver and req_q_id == shipment["quote_id"]:
                q_row = db["quotes"].find_one(
                    {"id": req_q_id, "customer_id": cust_id},
                    {"_id": 0},
                )
                if q_row and str(q_row.get("version") or "").strip() == req_q_ver:
                    clean_quote = {"id": req_q_id, "version": req_q_ver}

        existing = (
            db["hexa_trial_publications"].find_one(
                {"shipment_id": sid, "customer_id": cust_id},
                {"_id": 0},
            )
            or {}
        )
        history = list(existing.get("history") or [])
        approver = str(principal["username"])
        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        history.append(
            {
                "action": "PUBLISHED",
                "actor": approver,
                "role": str(principal.get("role") or ""),
                "at": now_iso,
                "event_versions": dict(clean_events),
                "document_versions": dict(clean_docs),
                "quote": dict(clean_quote) if clean_quote else None,
            }
        )
        pub_doc = {
            "shipment_id": sid,
            "customer_id": cust_id,
            "state": "PUBLISHED",
            "approved_by": approver,
            "approved_at": now_iso,
            "revoked_by": str(existing.get("revoked_by") or ""),
            "revoked_at": str(existing.get("revoked_at") or ""),
            "event_versions": clean_events,
            "document_versions": clean_docs,
            "quote": clean_quote,
            "history": history[-25:],
        }
        db["hexa_trial_publications"].replace_one(
            {"shipment_id": sid, "customer_id": cust_id},
            pub_doc,
            upsert=True,
        )
        self._record_audit(
            action="PUBLISH_SHIPMENT",
            principal=principal,
            shipment_id=sid,
            allowed=True,
            detail=(
                f"approved_by={approver} events={list(clean_events.keys())} "
                f"docs={list(clean_docs.keys())} quote={clean_quote}"
            ),
        )
        return {"ok": True, "publication": pub_doc}

    def revoke_shipment_publication(
        self,
        *,
        session_token: str | None,
        shipment_id: str,
        document_ids: Sequence[str] | None = None,
        event_ids: Sequence[str] | None = None,
        revoke_quote: bool = False,
    ) -> dict[str, Any]:
        """Revoke either specific published documents/events/quote or the entire shipment publication."""
        from core import database as core_db

        self.ensure_seeded()
        try:
            principal = self._require_authorized_tt_staff(session_token)
        except PublicationDenied:
            self._record_audit(
                action="REVOKE_PUBLICATION",
                principal=self.resolve_principal(session_token),
                shipment_id=str(shipment_id or ""),
                allowed=False,
                detail="unauthorized caller attempted revoke",
            )
            raise

        db = core_db.get_db()
        if db is None:
            raise PublicationDenied()

        sid = str(shipment_id or "").strip()
        shipment = self._load_adapted_shipment(db, sid)
        if not shipment:
            raise PublicationDenied()
        cust_id = shipment["customer_id"]

        existing = (
            db["hexa_trial_publications"].find_one(
                {"shipment_id": sid, "customer_id": cust_id},
                {"_id": 0},
            )
            or {}
        )
        history = list(existing.get("history") or [])
        actor = str(principal["username"])
        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        doc_list = [str(x).strip() for x in (document_ids or []) if str(x).strip()]
        ev_list = [str(x).strip() for x in (event_ids or []) if str(x).strip()]
        is_partial = bool(doc_list or ev_list or revoke_quote)

        if is_partial and existing.get("state") == "PUBLISHED":
            cur_events = dict(existing.get("event_versions") or {})
            cur_docs = dict(existing.get("document_versions") or {})
            cur_quote = copy.deepcopy(existing.get("quote"))
            for d_id in doc_list:
                cur_docs.pop(d_id, None)
            for e_id in ev_list:
                cur_events.pop(e_id, None)
            if revoke_quote:
                cur_quote = None
            next_state = "PUBLISHED" if (cur_events or cur_docs or cur_quote) else "REVOKED"
            history.append(
                {
                    "action": "REVOKED_ITEMS",
                    "actor": actor,
                    "role": str(principal.get("role") or ""),
                    "at": now_iso,
                    "revoked_documents": doc_list,
                    "revoked_events": ev_list,
                    "revoked_quote": bool(revoke_quote),
                    "event_versions": dict(cur_events),
                    "document_versions": dict(cur_docs),
                    "quote": copy.deepcopy(cur_quote),
                }
            )
            pub_doc = {
                "shipment_id": sid,
                "customer_id": cust_id,
                "state": next_state,
                "approved_by": str(existing.get("approved_by") or actor),
                "approved_at": str(existing.get("approved_at") or now_iso),
                "revoked_by": actor,
                "revoked_at": now_iso,
                "event_versions": cur_events,
                "document_versions": cur_docs,
                "quote": cur_quote,
                "history": history[-25:],
            }
        else:
            history.append(
                {
                    "action": "REVOKED_ALL",
                    "actor": actor,
                    "role": str(principal.get("role") or ""),
                    "at": now_iso,
                    "event_versions": {},
                    "document_versions": {},
                    "quote": None,
                }
            )
            pub_doc = {
                "shipment_id": sid,
                "customer_id": cust_id,
                "state": "REVOKED",
                "approved_by": str(existing.get("approved_by") or ""),
                "approved_at": str(existing.get("approved_at") or ""),
                "revoked_by": actor,
                "revoked_at": now_iso,
                "event_versions": {},
                "document_versions": {},
                "quote": None,
                "history": history[-25:],
            }

        db["hexa_trial_publications"].replace_one(
            {"shipment_id": sid, "customer_id": cust_id},
            pub_doc,
            upsert=True,
        )
        self._record_audit(
            action="REVOKE_PUBLICATION",
            principal=principal,
            shipment_id=sid,
            allowed=True,
            detail=f"revoked_by={actor} state={pub_doc['state']} docs={doc_list or 'ALL'}",
        )
        return {"ok": True, "publication": pub_doc}

    def _load_adapted_shipment(self, db: Any, shipment_id: str) -> dict[str, Any]:
        sid = str(shipment_id or "").strip()
        if not sid:
            return {}
        raw_ship = db["shipments"].find_one({"id": sid, "is_deleted": {"$ne": True}}, {"_id": 0})
        link = db["hexa_trial_shipment_links"].find_one({"shipment_id": sid}, {"_id": 0})
        if not raw_ship or not link:
            return {}
        mode_raw = str((raw_ship.get("data") or {}).get("0.0", {}).get("mode") or "").strip().upper()
        transport_mode = "ROAD" if mode_raw in {"TRUCK", "ROAD"} else str(link.get("transport_mode") or "")
        return {
            "id": str(raw_ship.get("id") or sid),
            "shipment_id": str(raw_ship.get("shipment_id") or sid),
            "customer_id": str(raw_ship.get("customer_id") or ""),
            "transport_mode": transport_mode,
            "quote_id": str(link.get("quote_id") or ""),
            "status": str(raw_ship.get("status") or ""),
            "eta": str((raw_ship.get("data") or {}).get("1.2", {}).get("eta") or ""),
            "internal_cost": link.get("internal_cost_vnd"),
            "supplier": link.get("internal_supplier"),
            "margin": link.get("internal_margin_vnd"),
        }

    def read_customer_publication(
        self,
        *,
        session_token: str | None,
        shipment_id: str,
    ) -> dict[str, Any]:
        """Server-authenticated read path from sandbox DB through ``build_customer_publication``."""
        from core import database as core_db

        self.ensure_seeded()
        principal = self.resolve_principal(session_token)
        db = core_db.get_db()
        if db is None:
            raise PublicationDenied()

        sid = str(shipment_id or "").strip()
        shipment = self._load_adapted_shipment(db, sid)
        cust_id = str(principal.get("customer_id") or "").strip()
        publication = (
            db["hexa_trial_publications"].find_one(
                {"shipment_id": sid, "customer_id": cust_id},
                {"_id": 0},
            )
            or {}
        )
        events = list(db["hexa_trial_events"].find({"shipment_id": sid}, {"_id": 0}))
        raw_docs = list(db["hexa_trial_documents"].find({"shipment_id": sid}, {"_id": 0}))
        documents: list[dict[str, Any]] = []
        for doc in raw_docs:
            att_row = core_db.load_shipment_attachment(str(doc.get("attachment_id") or ""))
            status = str((att_row or {}).get("status") or doc.get("status") or "")
            merged = dict(doc)
            merged["status"] = status
            documents.append(merged)

        quote_id = str(shipment.get("quote_id") or "").strip()
        quote = db["quotes"].find_one({"id": quote_id}, {"_id": 0}) if quote_id else None

        try:
            payload = build_customer_publication(
                shipment=shipment,
                principal=principal,
                publication=publication,
                events=events,
                documents=documents,
                quote=quote,
            )
            self._record_audit(
                action="READ_PUBLICATION",
                principal=principal,
                shipment_id=sid,
                allowed=True,
                detail=f"events={len(payload['timeline'])}, docs={len(payload['documents'])}",
            )
            return payload
        except PublicationDenied:
            self._record_audit(
                action="READ_PUBLICATION",
                principal=principal,
                shipment_id=sid,
                allowed=False,
                detail="CUSTOMER_RESOURCE_UNAVAILABLE",
            )
            raise

    def build_customer_dashboard(
        self,
        *,
        session_token: str | None,
    ) -> dict[str, Any]:
        """Build the reusable Map/Journey-first Customer Dashboard V1 for any authenticated customer.

        Reuses:
        - ``core.hexa_customer_publication.build_customer_publication`` (via ``read_customer_publication``)
        - ``core.shipment_dashboard.build_shipment_dashboard_view``
        - ``core.shipment_journey.build_journey``
        - ``core.shipment_execution_profile.build_execution_profile``
        - ``core.shipment_operations.compatibility_facts`` & ``transport_legs_for_read``

        Enforces:
        - Zero customer-name hardcoding: queries shipments purely by server-resolved ``principal['customer_id']``.
        - Default-deny / Revocation: unpublished or revoked shipments are skipped (never shown).
        - Truth guard: never defaults a shipment to completed and never exposes unverified ETA,
          internal cost, margin, supplier, or other customers' data.
        """
        from core import database as core_db
        from core.shipment_dashboard import build_shipment_dashboard_view
        from core.shipment_execution_profile import build_execution_profile
        from core.shipment_journey import build_journey
        from core.shipment_operations import compatibility_facts, transport_legs_for_read

        self.ensure_seeded()
        principal = self.resolve_principal(session_token)
        cust_id = str(principal.get("customer_id") or "").strip()
        if not (
            principal.get("authenticated") is True
            and principal.get("kind") == "customer"
            and cust_id
        ):
            self._record_audit(
                action="READ_DASHBOARD",
                principal=principal,
                shipment_id="*",
                allowed=False,
                detail="CUSTOMER_RESOURCE_UNAVAILABLE",
            )
            raise PublicationDenied()

        db = core_db.get_db()
        if db is None:
            raise PublicationDenied()

        cust_doc = db["customers"].find_one({"id": cust_id}, {"_id": 0}) or {}
        candidate_shipments = list(
            db["shipments"].find(
                {"customer_id": cust_id, "is_deleted": {"$ne": True}},
                {"_id": 0},
            )
        )

        rows: list[dict[str, Any]] = []
        for raw_ship in candidate_shipments:
            sid = str(raw_ship.get("id") or raw_ship.get("shipment_id") or "").strip()
            if not sid:
                continue
            try:
                pub_payload = self.read_customer_publication(
                    session_token=session_token,
                    shipment_id=sid,
                )
            except PublicationDenied:
                continue

            link = (
                db["hexa_trial_shipment_links"].find_one(
                    {"shipment_id": sid, "customer_id": cust_id},
                    {"_id": 0},
                )
                or {}
            )
            dash_view = build_shipment_dashboard_view(raw_ship)
            legs, _ = transport_legs_for_read(raw_ship)
            exec_profile = build_execution_profile(raw_ship, legs=legs)
            operational = compatibility_facts(raw_ship)
            internal_journey = build_journey(
                raw_ship,
                profile=exec_profile,
                operational=operational,
                primary={"text": "", "detail": "", "route": "", "priority": "NORMAL"},
                dashboard=dash_view,
                attachments=[],
            )

            timeline = list(pub_payload.get("timeline") or [])
            latest_event = timeline[0] if timeline else None
            verified_stage_id = str(latest_event.get("stage") or "") if latest_event else None
            verified_stage_title = (
                str(latest_event.get("title") or "")
                if latest_event
                else "Chưa có mốc tiến độ được xác minh"
            )
            last_updated_at = str(latest_event.get("occurred_at") or "") if latest_event else None

            # Map published timeline events by stage_id so Journey nodes reflect ONLY verified & published facts
            events_by_stage: dict[str, dict[str, Any]] = {}
            for ev in reversed(timeline):
                st_key = str(ev.get("stage") or "").strip()
                if st_key:
                    events_by_stage[st_key] = ev

            # Check if any published verified event carries a TT-verified warehouse ETA
            verified_warehouse_eta: str | None = None
            for ev in timeline:
                ev_id = str(ev.get("id") or "").strip()
                ev_ver = str(ev.get("version") or "").strip()
                if not ev_id or not ev_ver:
                    continue
                ev_doc = db["hexa_trial_events"].find_one(
                    {
                        "shipment_id": sid,
                        "customer_id": cust_id,
                        "id": ev_id,
                        "version": ev_ver,
                        "verified": True,
                        "visibility": "CUSTOMER",
                    },
                    {"_id": 0},
                )
                if ev_doc and str(ev_doc.get("verified_warehouse_eta") or "").strip():
                    verified_warehouse_eta = str(ev_doc["verified_warehouse_eta"]).strip()
                    break

            customer_nodes: list[dict[str, Any]] = []
            verified_stage_label = "Chưa xác minh"
            for raw_node in internal_journey.get("nodes") or []:
                n_id = str(raw_node.get("id") or "")
                if n_id == "MAIN_CARRIAGE":
                    continue
                n_label = str(raw_node.get("label") or n_id)
                matched_ev = events_by_stage.get(n_id)
                if matched_ev is None and n_id == "road-ltl" and "pickup" in events_by_stage:
                    matched_ev = events_by_stage["pickup"]
                is_done = matched_ev is not None
                is_current = bool(verified_stage_id and n_id == verified_stage_id)
                if is_current:
                    verified_stage_label = n_label
                customer_nodes.append(
                    {
                        "id": n_id,
                        "label": n_label,
                        "completed": is_done,
                        "current": is_current,
                        "state": (
                            "CURRENT"
                            if is_current
                            else ("VERIFIED_DONE" if is_done else "PENDING_VERIFICATION")
                        ),
                        "evidence": (
                            str(matched_ev.get("title") or "")
                            if matched_ev
                            else "Chưa có mốc xác minh được công bố"
                        ),
                        "occurred_at": str(matched_ev.get("occurred_at") or "") if matched_ev else "",
                    }
                )

            if verified_stage_id and verified_stage_label == "Chưa xác minh":
                verified_stage_label = verified_stage_id

            # Never default a shipment to completed unless a verified 'delivery' event was explicitly published
            is_complete = "delivery" in events_by_stage
            docs = list(pub_payload.get("documents") or [])
            quote = pub_payload.get("quote")
            needs_customer_action = bool((docs or quote) and not is_complete)

            if is_complete:
                next_step = "Đã giao hàng (xác minh hoàn tất)"
            elif verified_warehouse_eta:
                next_step = f"Chuẩn bị kho nhận hàng (ETA đã xác minh: {verified_warehouse_eta}) & kiểm tra chứng từ"
            elif docs or quote:
                next_step = "Kiểm tra chứng từ / báo giá đã công bố & theo dõi thông quan"
            elif timeline:
                next_step = "Đang vận chuyển — chờ Trường Thành công bố chứng từ tiếp theo"
            else:
                next_step = "Chờ Trường Thành cập nhật mốc xác minh tiếp theo"

            contact_point = str(dash_view.get("owner") or "CSKH Trường Thành")

            rows.append(
                {
                    "shipment_id": sid,
                    "transport_mode": pub_payload.get("transport_mode"),
                    "route_summary": str(link.get("route_summary") or "Đang cập nhật tuyến"),
                    "cargo_summary": str(link.get("cargo_summary") or "Hàng hóa theo Packing List công bố"),
                    "verified_stage_id": verified_stage_id,
                    "verified_stage_label": verified_stage_label,
                    "verified_stage_title": verified_stage_title,
                    "last_updated_at": last_updated_at,
                    "last_updated_label": last_updated_at or "Chưa có mốc xác minh",
                    "verified_warehouse_eta": verified_warehouse_eta,
                    "verified_warehouse_eta_label": (
                        f"{verified_warehouse_eta} (Đã xác minh)"
                        if verified_warehouse_eta
                        else "Chưa xác minh"
                    ),
                    "is_complete": is_complete,
                    "needs_customer_action": needs_customer_action,
                    "next_step": next_step,
                    "contact_point": contact_point,
                    "journey": {
                        "current_stage_id": verified_stage_id or "",
                        "nodes": customer_nodes,
                        "position_note": (
                            verified_stage_title
                            if verified_stage_id
                            else "Chưa có mốc thực tế được xác minh công bố."
                        ),
                    },
                    "timeline": timeline,
                    "documents": docs,
                    "quote": quote,
                }
            )

        rows.sort(key=lambda r: (str(r.get("last_updated_at") or ""), r["shipment_id"]), reverse=True)
        active_tracking = sum(1 for r in rows if not r["is_complete"])
        arriving_soon = sum(
            1
            for r in rows
            if not r["is_complete"]
            and (
                r["verified_warehouse_eta"] is not None
                or r["verified_stage_id"] in {"road-border", "customs-import", "arrival"}
            )
        )
        customer_action_needed = sum(1 for r in rows if r["needs_customer_action"])

        self._record_audit(
            action="READ_DASHBOARD",
            principal=principal,
            shipment_id="*",
            allowed=True,
            detail=f"published_shipments={len(rows)}",
        )
        return {
            "schema": "hexa-customer-dashboard/v1",
            "customer_id": cust_id,
            "customer_name": str(cust_doc.get("name") or cust_id),
            "summary": {
                "active_tracking": active_tracking,
                "arriving_soon": arriving_soon,
                "customer_action_needed": customer_action_needed,
                "total_published": len(rows),
            },
            "shipments": rows,
        }

    def download_customer_document(
        self,
        *,
        session_token: str | None,
        shipment_id: str,
        document_id: str,
        requested_version: str,
    ) -> dict[str, Any]:
        """Authorize on server BEFORE reading any file bytes from GridFS.

        Acceptance Criterion #5:
        ``authorize_document_download`` runs against server-loaded metadata and
        the verified session principal BEFORE ``fetch_attachment_bytes`` is
        called. Any denied request causes zero GridFS reads.
        """
        from core import database as core_db
        from core import shipment_attachments as core_att

        self.ensure_seeded()
        principal = self.resolve_principal(session_token)
        db = core_db.get_db()
        if db is None:
            self.denied_before_storage_reads += 1
            raise PublicationDenied()

        sid = str(shipment_id or "").strip()
        doc_id = str(document_id or "").strip()
        ver = str(requested_version or "").strip()

        shipment = self._load_adapted_shipment(db, sid)
        cust_id = str(principal.get("customer_id") or "").strip()
        publication = (
            db["hexa_trial_publications"].find_one(
                {"shipment_id": sid, "customer_id": cust_id},
                {"_id": 0},
            )
            or {}
        )

        # Resolve candidate document metadata from server storage (without reading GridFS bytes).
        doc_row = db["hexa_trial_documents"].find_one(
            {"shipment_id": sid, "id": doc_id, "version": ver},
            {"_id": 0},
        )
        if doc_row is None:
            doc_row = (
                db["hexa_trial_documents"].find_one(
                    {"shipment_id": sid, "id": doc_id},
                    {"_id": 0},
                )
                or {}
            )

        att_id = str(doc_row.get("attachment_id") or "").strip()
        att_meta = core_db.load_shipment_attachment(att_id) if att_id else None
        candidate_doc = dict(doc_row)
        if att_meta is not None:
            candidate_doc["status"] = str(att_meta.get("status") or "")

        try:
            authorize_document_download(
                shipment=shipment,
                principal=principal,
                publication=publication,
                document=candidate_doc,
                requested_id=doc_id,
                requested_version=ver,
            )
        except PublicationDenied:
            self.denied_before_storage_reads += 1
            self._record_audit(
                action="DOWNLOAD_DOCUMENT",
                principal=principal,
                shipment_id=sid,
                allowed=False,
                detail=f"doc={doc_id}@{ver} denied BEFORE storage read (storage_reads={self.storage_read_attempts})",
            )
            raise

        # Permission check passed -> now and only now read bytes from GridFS.
        self.storage_read_attempts += 1
        fetched = core_att.fetch_attachment_bytes(
            {"id": att_id},
            shipment_id=str(doc_row.get("attachment_shipment_id") or sid),
        )
        if not fetched.get("ok") or not fetched.get("data"):
            raise PublicationDenied()

        stored_record = fetched.get("record") or {}
        file_name = str(
            doc_row.get("file_name")
            or stored_record.get("original_name")
            or f"{doc_id}-{ver}.pdf"
        )
        mime = str(stored_record.get("mime") or "application/pdf")
        data = bytes(fetched["data"])
        self._record_audit(
            action="DOWNLOAD_DOCUMENT",
            principal=principal,
            shipment_id=sid,
            allowed=True,
            detail=f"doc={doc_id}@{ver} bytes={len(data)} (storage_reads={self.storage_read_attempts})",
        )
        return {
            "document_id": doc_id,
            "version": ver,
            "file_name": file_name,
            "mime": mime,
            "data": data,
        }

    def build_trial_inspector_snapshot(self) -> dict[str, Any]:
        """Server-internal TT truth snapshot (NEVER served on the customer HTTP surface)."""
        from core import database as core_db

        self.ensure_seeded()
        db = core_db.get_db()
        quote_a = db["quotes"].find_one({"id": QUOTE_A_ID}, {"_id": 0}) or {}
        quote_b = db["quotes"].find_one({"id": QUOTE_B_ID}, {"_id": 0}) or {}
        calc_a = (quote_a.get("calculation") or {})
        calc_b = (quote_b.get("calculation") or {})
        return {
            "environment": "SANDBOX_STAGING (mongomock + GridFS cô lập, 0 kết nối production)",
            "shared_road_trip": {
                "trip_id": SHARED_TRIP_ID,
                "truck_plate": SHARED_TRUCK_PLATE,
                "route": "Bằng Tường (Quảng Tây) → Cửa khẩu Hữu Nghị → Hà Nội / Bắc Ninh",
                "transport_mode": "ROAD (ghép xe LTL 2 khách hàng cùng chuyến)",
                "customers_on_truck": [
                    {
                        "slot": "Khách A (mục tiêu công bố HEXA)",
                        "customer_id": CUSTOMER_A_ID,
                        "customer_name": "Công ty TNHH Lục Giác (HEXA)",
                        "shipment_id": SHIPMENT_A_ID,
                        "cargo": "18 kiện / 4.200 kg",
                    },
                    {
                        "slot": "Khách B (đi ghép cùng xe — dùng kiểm chứng cô lập chéo)",
                        "customer_id": CUSTOMER_B_ID,
                        "customer_name": "Công ty CP Minh Đức",
                        "shipment_id": SHIPMENT_B_ID,
                        "cargo": "22 kiện / 5.800 kg",
                    },
                ],
            },
            "tt_internal_only_data": {
                "shipment_id": SHIPMENT_A_ID,
                "supplier": "Foshan Hexa Furniture Factory (Shunde, Foshan)",
                "carrier_vendor": "Nhà xe Việt Trung An Bình",
                "cost_before_tax_vnd": calc_a.get("estimated_cost_vnd"),
                "selling_before_tax_vnd": calc_a.get("selling_price_before_tax_vnd"),
                "vat_vnd": calc_a.get("estimated_output_tax_vnd"),
                "selling_total_vnd": calc_a.get("selling_price_total_vnd"),
                "estimated_margin_vnd": calc_a.get("estimated_margin_vnd"),
                "unverified_eta": "2026-10-25 (Tài xế báo dự kiến, TT chưa xác minh & chưa duyệt công bố)",
                "internal_documents": [
                    "DOC-LG-COST (v1, kind=COST, visibility=TT — Bảng tính giá vốn & NCC nội bộ)",
                    "DOC-LG-PL (v1, kind=PL — Bản cũ đã bị thay thế bởi v2)",
                ],
                "other_customer_on_same_truck": {
                    "customer_id": CUSTOMER_B_ID,
                    "shipment_id": SHIPMENT_B_ID,
                    "quote_id": QUOTE_B_ID,
                    "selling_total_vnd": calc_b.get("selling_price_total_vnd"),
                    "documents": ["DOC-MD-PL (v1 — Packing List của Minh Đức)"],
                },
            },
            "storage_guard_metrics": {
                "gridfs_storage_read_attempts": self.storage_read_attempts,
                "denied_before_storage_read_count": self.denied_before_storage_reads,
            },
            "schema_gaps": list(SCHEMA_GAP_REPORT),
            "recent_audit_trail": list(self.audit_trail[-20:]),
        }

    def _record_audit(
        self,
        *,
        action: str,
        principal: Mapping[str, Any],
        shipment_id: str,
        allowed: bool,
        detail: str,
    ) -> None:
        self.audit_trail.append(
            {
                "action": action,
                "principal_kind": str(principal.get("kind") or ""),
                "customer_id": str(principal.get("customer_id") or ""),
                "shipment_id": shipment_id,
                "allowed": allowed,
                "detail": detail,
            }
        )


_DEFAULT_ENV = HexaTrialEnvironment()


def get_trial_environment() -> HexaTrialEnvironment:
    _DEFAULT_ENV.ensure_seeded()
    return _DEFAULT_ENV


def _extract_session_token(headers: Mapping[str, str]) -> str:
    auth_header = str(headers.get("Authorization") or headers.get("authorization") or "").strip()
    if auth_header.lower().startswith("bearer "):
        return auth_header[7:].strip()
    raw_cookie = str(headers.get("Cookie") or headers.get("cookie") or "").strip()
    if raw_cookie:
        cookie = SimpleCookie()
        cookie.load(raw_cookie)
        if TRIAL_COOKIE_NAME in cookie:
            return cookie[TRIAL_COOKIE_NAME].value.strip()
    return ""


def _extract_tt_session_token(headers: Mapping[str, str]) -> str:
    auth_header = str(headers.get("Authorization") or headers.get("authorization") or "").strip()
    if auth_header.lower().startswith("bearer "):
        return auth_header[7:].strip()
    raw_cookie = str(headers.get("Cookie") or headers.get("cookie") or "").strip()
    if raw_cookie:
        cookie = SimpleCookie()
        cookie.load(raw_cookie)
        if TRIAL_TT_COOKIE_NAME in cookie and cookie[TRIAL_TT_COOKIE_NAME].value.strip():
            return cookie[TRIAL_TT_COOKIE_NAME].value.strip()
        if TRIAL_COOKIE_NAME in cookie:
            return cookie[TRIAL_COOKIE_NAME].value.strip()
    return ""


def render_trial_portal_html() -> str:
    """Two-screen HEXA V0 trial portal HTML (Trường Thành Publish Desk & Customer Portal).

    Contains ZERO TT internal cost, margin, supplier, unverified ETA, or other
    customer's information in static HTML, and provides NO self-service session
    switcher on the customer surface.
    """
    return """<!doctype html>
<html lang="vi">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>HEXA V0 — Luồng TT Duyệt Công Bố → Khách Hàng Đăng Nhập Xem Lô</title>
  <style>
    :root {
      --bg: #f4f6f9;
      --surface: #ffffff;
      --border: #d8dee9;
      --text: #1b2430;
      --muted: #526071;
      --primary: #0f4c81;
      --primary-soft: #e8f1f8;
      --ok: #137333;
      --ok-bg: #e6f4ea;
      --deny: #b3261e;
      --deny-bg: #fce8e6;
      --warn: #8a5300;
      --warn-bg: #fef7e0;
      --mono: "IBM Plex Mono", ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      --sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: var(--sans);
      color: var(--text);
      background: var(--bg);
      line-height: 1.5;
    }
    header {
      background: #0f2942;
      color: #fff;
      padding: 16px 24px;
      border-bottom: 3px solid #1e6091;
    }
    header .top-row {
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
      max-width: 1120px;
      margin: 0 auto;
    }
    header h1 {
      font-size: 18px;
      margin: 0;
      font-weight: 700;
    }
    .screen-tabs {
      max-width: 1120px;
      margin: 16px auto 0;
      padding: 0 20px;
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
    }
    .screen-tab-btn {
      padding: 12px 16px;
      border-radius: 10px;
      border: 2px solid var(--border);
      background: var(--surface);
      color: var(--text);
      text-align: left;
      cursor: pointer;
      transition: all 0.15s ease;
    }
    .screen-tab-btn.active {
      border-color: var(--primary);
      background: var(--primary-soft);
      color: var(--primary);
    }
    .screen-tab-btn .tab-title {
      display: block;
      font-size: 15px;
      font-weight: 700;
    }
    .screen-tab-btn .tab-sub {
      display: block;
      font-size: 12.5px;
      color: var(--muted);
      margin-top: 2px;
      font-weight: 500;
    }
    .pill {
      padding: 4px 10px;
      border-radius: 999px;
      font-weight: 600;
      font-size: 12px;
      display: inline-block;
    }
    .pill-ok { background: var(--ok-bg); color: var(--ok); }
    .pill-deny { background: var(--deny-bg); color: var(--deny); }
    .pill-warn { background: var(--warn-bg); color: var(--warn); }
    main {
      max-width: 1120px;
      margin: 16px auto;
      padding: 0 20px 48px;
      display: grid;
      gap: 20px;
    }
    .screen-pane { display: grid; gap: 18px; }
    .screen-pane.hidden { display: none; }
    .card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 18px 20px;
      box-shadow: 0 1px 3px rgba(15, 41, 66, 0.05);
    }
    .card h2 {
      margin: 0 0 10px;
      font-size: 16px;
      color: var(--primary);
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      flex-wrap: wrap;
    }
    .card h3 {
      margin: 14px 0 8px;
      font-size: 14px;
      color: var(--text);
    }
    .muted { color: var(--muted); font-size: 13px; }
    .mono { font-family: var(--mono); font-size: 12.5px; }
    .btn-row {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 10px;
      align-items: center;
    }
    input[type="text"], input[type="password"] {
      padding: 7px 10px;
      border: 1px solid var(--border);
      border-radius: 6px;
      font-family: var(--mono);
      font-size: 13px;
    }
    button {
      cursor: pointer;
      border: 1px solid var(--primary);
      background: var(--primary);
      color: #fff;
      padding: 8px 13px;
      border-radius: 6px;
      font-size: 13px;
      font-weight: 600;
    }
    button:hover { background: #0b3960; }
    button.btn-secondary {
      background: #fff;
      color: var(--primary);
      border-color: var(--primary);
    }
    button.btn-secondary:hover { background: var(--primary-soft); }
    button.btn-danger {
      background: var(--deny);
      border-color: var(--deny);
      color: #fff;
    }
    button.btn-danger:hover { background: #8c1d17; }
    .kv-list {
      display: grid;
      grid-template-columns: 210px 1fr;
      gap: 6px 12px;
      font-size: 13px;
      margin: 8px 0;
    }
    .kv-list dt { color: var(--muted); font-weight: 600; }
    .kv-list dd { margin: 0; font-weight: 500; }
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
      margin-top: 8px;
    }
    th, td {
      border: 1px solid var(--border);
      padding: 8px 10px;
      text-align: left;
      vertical-align: top;
    }
    th { background: #f8fafc; font-weight: 600; color: var(--text); }
    pre {
      background: #0f172a;
      color: #e2e8f0;
      padding: 12px;
      border-radius: 8px;
      overflow-x: auto;
      font-family: var(--mono);
      font-size: 12px;
      margin: 8px 0 0;
      max-height: 280px;
    }
    .banner-result {
      padding: 10px 14px;
      border-radius: 8px;
      font-size: 13px;
      font-weight: 600;
      margin-bottom: 12px;
    }
    .banner-ok { background: var(--ok-bg); color: var(--ok); border: 1px solid #a8dab5; }
    .banner-deny { background: var(--deny-bg); color: var(--deny); border: 1px solid #f6aea9; }
    .banner-warn { background: var(--warn-bg); color: var(--warn); border: 1px solid #f5d68e; }
    .helper-box {
      margin-top: 10px;
      padding: 10px 12px;
      background: #f8fafc;
      border: 1px dashed var(--border);
      border-radius: 8px;
      font-size: 12.5px;
      color: var(--muted);
    }
    .kpi-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 12px;
      margin: 10px 0 14px;
    }
    .kpi-card {
      background: #f8fafc;
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 12px 14px;
    }
    .kpi-card .kpi-label {
      font-size: 12.5px;
      color: var(--muted);
      font-weight: 600;
    }
    .kpi-card .kpi-val {
      font-size: 24px;
      font-weight: 700;
      color: var(--primary);
      margin-top: 4px;
      font-family: var(--mono);
    }
    .table-scroll {
      width: 100%;
      overflow-x: auto;
    }
    .journey-map-bar {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(165px, 1fr));
      gap: 10px;
      margin: 10px 0 16px;
    }
    .journey-node {
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 10px 12px;
      background: #f8fafc;
      font-size: 12.5px;
    }
    .journey-node.done {
      border-color: #a8dab5;
      background: var(--ok-bg);
    }
    .journey-node.current {
      border: 2px solid var(--primary);
      background: var(--primary-soft);
    }
    .journey-node .node-title {
      font-weight: 700;
      color: var(--text);
      margin-bottom: 4px;
    }
    @media (max-width: 768px) {
      .screen-tabs { grid-template-columns: 1fr; }
      .kpi-grid { grid-template-columns: 1fr; }
      .kv-list { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <header>
    <div class="top-row">
      <div>
        <h1>HEXA V1 — Dashboard Khách Hàng Dùng Chung Nền Tảng Logistics (Map / Journey-First)</h1>
        <div style="font-size: 13px; opacity: 0.9; margin-top: 4px;">
          Môi trường thử nghiệm cô lập (SANDBOX_STAGING) · Chỉ hiển thị đúng tiến độ đã xác minh, chứng từ đúng phiên bản và báo giá bán đã duyệt.
        </div>
      </div>
      <div style="display: flex; gap: 8px; flex-wrap: wrap;">
        <span id="tt-session-pill" class="pill pill-warn">TT: Chưa đăng nhập</span>
        <span id="active-session-pill" class="pill pill-deny">Khách: Chưa đăng nhập</span>
      </div>
    </div>
  </header>

  <nav class="screen-tabs" aria-label="Chuyển màn hình nghiệp vụ">
    <button id="tab-btn-customer" class="screen-tab-btn active" onclick="switchScreen('customer')">
      <span class="tab-title">Màn hình 2 — Dashboard Khách Hàng V1 (Lục Giác / Minh Đức / An Phát)</span>
      <span class="tab-sub">Bước khách hàng: Đăng nhập → Xem Dashboard tổng quan → Bấm lô mở Hành trình &amp; Chứng từ</span>
    </button>
    <button id="tab-btn-tt" class="screen-tab-btn" onclick="switchScreen('tt')">
      <span class="tab-title">Màn hình 1 — Nội bộ Trường Thành (Duyệt Công Bố)</span>
      <span class="tab-sub">Bước nhân sự TT: Mở lô (ROAD-LG-001 / ROAD-MD-002 / ROAD-AP-003) → Chọn mục → Công bố / Thu hồi</span>
    </button>
  </nav>

  <main>
    <!-- ==================== SCREEN 1: TRƯỜNG THÀNH STAFF ==================== -->
    <div id="screen-tt" class="screen-pane hidden">
      <section class="card">
        <h2>
          <span>Bước 1 (Trường Thành) — Đăng nhập nhân sự điều vận / chứng từ</span>
          <span id="tt-login-badge" class="pill pill-warn">Chưa xác thực TT</span>
        </h2>
        <div class="btn-row">
          <label for="tt-username" class="muted">Tài khoản TT:</label>
          <input id="tt-username" type="text" value="tt.ops.truongthanh" />
          <label for="tt-passcode" class="muted">Mã xác thực:</label>
          <input id="tt-passcode" type="password" value="TT-Trial-2026!" />
          <button onclick="loginTtStaff()">1. Đăng nhập Trường Thành</button>
          <button class="btn-secondary" onclick="logoutTtStaff()">Đăng xuất TT</button>
        </div>
        <div class="helper-box">
          Tài khoản nhân sự TT có quyền duyệt công bố trong môi trường thử nghiệm:
          <span class="mono">tt.ops.truongthanh</span> / <span class="mono">TT-Trial-2026!</span>
          (Tài khoản <span class="mono">tt.viewer</span> hoặc tài khoản khách hàng sẽ bị từ chối quyền duyệt).
        </div>
        <div id="tt-auth-banner" style="margin-top: 10px;"></div>
      </section>

      <section class="card">
        <h2>
          <span>Bước 2 &amp; 3 (Trường Thành) — Chọn mục chia sẻ → Duyệt công bố → Thu hồi</span>
          <div class="btn-row" style="margin-top: 0;">
            <label for="tt-shipment-input" class="muted">Mã lô:</label>
            <input id="tt-shipment-input" type="text" value="ROAD-LG-001" style="width: 140px;" />
            <button class="btn-secondary" onclick="loadTtShipmentDesk()">Mở hồ sơ lô</button>
            <button class="btn-secondary" onclick="pickTtShipment('ROAD-LG-001')">Lô ROAD-LG-001</button>
            <button class="btn-secondary" onclick="pickTtShipment('ROAD-MD-002')">Lô ROAD-MD-002</button>
            <button class="btn-secondary" onclick="pickTtShipment('ROAD-AP-003')">Lô ROAD-AP-003</button>
          </div>
        </h2>

        <div id="tt-desk-status" class="banner-result banner-warn">
          Hãy bấm "1. Đăng nhập Trường Thành" ở trên để mở hồ sơ nội bộ lô và duyệt công bố cho khách hàng tương ứng.
        </div>

        <div id="tt-desk-body" style="display: none;">
          <dl class="kv-list">
            <dt>Lô hàng / Khách hàng:</dt><dd id="tt-ship-summary">-</dd>
            <dt>Chuyến xe ghép:</dt><dd class="mono" id="tt-trip-summary">-</dd>
            <dt>Dữ liệu giữ lại nội bộ TT:</dt><dd id="tt-internal-holdback">-</dd>
          </dl>

          <h3>1. Chọn Mốc tiến độ đã xác minh để chia sẻ cho khách</h3>
          <div class="table-scroll">
            <table>
              <thead>
                <tr>
                  <th style="width: 70px;">Chọn</th>
                  <th>Mã mốc &amp; Phiên bản</th>
                  <th>Nội dung tiến độ</th>
                  <th>Trạng thái xác minh</th>
                </tr>
              </thead>
              <tbody id="tt-events-tbody"></tbody>
            </table>
          </div>

          <h3>2. Chọn Chứng từ &amp; Phiên bản cụ thể để cho phép khách tải</h3>
          <div class="table-scroll">
            <table>
              <thead>
                <tr>
                  <th style="width: 70px;">Chọn</th>
                  <th>Mã chứng từ &amp; Phiên bản</th>
                  <th>Loại</th>
                  <th>Tên chứng từ</th>
                  <th>Kiểm soát &amp; Thu hồi nhanh</th>
                </tr>
              </thead>
              <tbody id="tt-docs-tbody"></tbody>
            </table>
          </div>

          <h3>3. Chọn Phiên bản Báo giá BÁN muốn công bố</h3>
          <div id="tt-quote-box" class="helper-box" style="font-size: 13px; color: var(--text);"></div>

          <div class="btn-row" style="margin-top: 16px;">
            <button class="btn-secondary" onclick="selectAllEligibleTtItems()">☑ Tích chọn nhanh mục đủ điều kiện</button>
            <button onclick="submitTtPublish()">2. Công bố cho khách (Theo các mục đã tích chọn)</button>
            <button class="btn-danger" onclick="submitTtRevokeAll()">3. Thu hồi toàn bộ công bố lô này</button>
            <button class="btn-secondary" onclick="switchScreen('customer')">→ Sang Màn hình Khách hàng kiểm tra</button>
          </div>

          <h3>Bản ghi kiểm toán công bố tại Server (Ai duyệt · Lúc nào · Mục/Phiên bản nào)</h3>
          <dl class="kv-list">
            <dt>Trạng thái công bố:</dt><dd id="tt-pub-state">-</dd>
            <dt>Người duyệt gần nhất:</dt><dd class="mono" id="tt-pub-approved">-</dd>
            <dt>Người thu hồi gần nhất:</dt><dd class="mono" id="tt-pub-revoked">-</dd>
            <dt>Mục &amp; phiên bản hiệu lực:</dt><dd class="mono" id="tt-pub-items">-</dd>
          </dl>
          <pre id="tt-pub-history-json">{}</pre>
        </div>
      </section>
    </div>

    <!-- ==================== SCREEN 2: CUSTOMER DASHBOARD V1 ==================== -->
    <div id="screen-customer" class="screen-pane">
      <section class="card">
        <h2>
          <span>Bước 1 (Khách hàng) — Đăng nhập tài khoản khách thử nghiệm riêng</span>
          <span class="mono" id="http-status-badge">HTTP --</span>
        </h2>
        <div class="btn-row">
          <label for="cust-username" class="muted">Tài khoản khách:</label>
          <input id="cust-username" type="text" value="lucgiac.trial" />
          <label for="cust-passcode" class="muted">Mật khẩu:</label>
          <input id="cust-passcode" type="password" value="LG-Trial-2026!" />
          <button onclick="loginCustomer()">1. Đăng nhập Khách hàng</button>
          <button class="btn-secondary" onclick="logoutCustomer()">Đăng xuất</button>
          <button class="btn-secondary" onclick="switchScreen('tt')">⇄ Mở Màn hình Trường Thành (Duyệt/Thu hồi)</button>
        </div>
        <div class="btn-row" style="margin-top: 8px;">
          <span class="muted">Điền nhanh tài khoản thử nghiệm:</span>
          <button class="btn-secondary" onclick="fillCustomerCreds('lucgiac.trial', 'LG-Trial-2026!')">Khách A (lucgiac.trial)</button>
          <button class="btn-secondary" onclick="fillCustomerCreds('minhduc.trial', 'MD-Trial-2026!')">Khách B (minhduc.trial)</button>
          <button class="btn-secondary" onclick="fillCustomerCreds('anphat.trial', 'AP-Trial-2026!')">Khách C (anphat.trial)</button>
        </div>
        <div class="helper-box">
          <strong>3 Tài khoản khách thử nghiệm (Dùng chung 1 pipeline Dashboard, phân tách dữ liệu tại Server):</strong><br/>
          • Khách A (Lục Giác — lô <span class="mono">ROAD-LG-001</span>, đi ghép xe): <span class="mono">lucgiac.trial</span> / <span class="mono">LG-Trial-2026!</span><br/>
          • Khách B (Minh Đức — lô <span class="mono">ROAD-MD-002</span>, đi ghép cùng xe với A): <span class="mono">minhduc.trial</span> / <span class="mono">MD-Trial-2026!</span><br/>
          • Khách C (An Phát — lô <span class="mono">ROAD-AP-003</span>, kiểm chứng tái sử dụng): <span class="mono">anphat.trial</span> / <span class="mono">AP-Trial-2026!</span>
        </div>
        <div id="cust-auth-banner" style="margin-top: 10px;"></div>
      </section>

      <section class="card" id="customer-dashboard-card">
        <h2>
          <span>Bước 2 (Khách hàng) — Tổng quan Lô hàng đã được Trường Thành công bố</span>
          <button class="btn-secondary" onclick="loadCustomerDashboard()">↻ Làm mới Dashboard</button>
        </h2>
        <div id="dashboard-status-banner" class="banner-result banner-warn">
          Hãy đăng nhập tài khoản khách hàng ở Bước 1 để tải Dashboard tổng quan các lô hàng đã được Trường Thành duyệt công bố.
        </div>

        <div class="kpi-grid">
          <div class="kpi-card">
            <div class="kpi-label">Đang theo dõi</div>
            <div class="kpi-val" id="dash-count-tracking">0</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-label">Sắp giao (Đã qua cửa khẩu / Có ETA xác minh)</div>
            <div class="kpi-val" id="dash-count-arriving">0</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-label">Cần khách xử lý (Đối chiếu chứng từ / Chuẩn bị nhận)</div>
            <div class="kpi-val" id="dash-count-action">0</div>
          </div>
        </div>

        <div class="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Mã lô &amp; Phương thức</th>
                <th>Hàng hóa</th>
                <th>Chặng / Vị trí xác minh gần nhất</th>
                <th>Thời điểm cập nhật</th>
                <th>ETA kho (Chỉ hiện khi đã xác minh)</th>
                <th>Việc tiếp theo</th>
                <th>Đầu mối TT</th>
                <th>Chi tiết</th>
              </tr>
            </thead>
            <tbody id="dash-shipments-tbody">
              <tr>
                <td colspan="8" class="muted">Chưa có lô hàng nào được công bố hiển thị.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section class="card" id="hexa-portal-card">
        <h2>
          <span>Bước 3 (Khách hàng) — Bản đồ Hành trình (Journey) &amp; Chứng từ đúng phiên bản của lô</span>
          <div class="btn-row" style="margin-top: 0;">
            <label for="shipment-input" class="muted">Mã tham chiếu lô:</label>
            <input id="shipment-input" type="text" value="ROAD-LG-001" style="width: 140px;" />
            <button onclick="loadRequestedShipment()">Xem hành trình &amp; công bố</button>
          </div>
        </h2>
        <div id="portal-status-banner" class="banner-result banner-deny">Chưa tải dữ liệu lô hàng.</div>

        <div id="portal-content">
          <h3>Bản đồ Hành trình Lô hàng (Map / Journey-First — Chỉ đánh dấu hoàn thành các chặng đã xác minh)</h3>
          <div id="pub-journey-map" class="journey-map-bar">
            <div class="journey-node"><div class="node-title">Chưa chọn lô đã công bố</div><div class="muted">Bấm vào lô ở bảng trên để mở sơ đồ hành trình.</div></div>
          </div>

          <dl class="kv-list">
            <dt>Schema công bố:</dt><dd class="mono" id="pub-schema">-</dd>
            <dt>Mã tham chiếu lô:</dt><dd class="mono" id="pub-reference">-</dd>
            <dt>Phương thức vận tải:</dt><dd class="mono" id="pub-mode">-</dd>
            <dt>Tổng báo giá BÁN đã gửi:</dt><dd id="pub-quote">-</dd>
          </dl>

          <h3>Tiến độ đã xác minh &amp; công bố (Timeline)</h3>
          <div class="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Mã mốc</th>
                  <th>Công đoạn</th>
                  <th>Nội dung công bố</th>
                  <th>Thời điểm xảy ra</th>
                  <th>Phiên bản</th>
                </tr>
              </thead>
              <tbody id="pub-timeline-body"></tbody>
            </table>
          </div>

          <h3>Chứng từ được phép tải (Kiểm quyền phía Server trước khi đọc file)</h3>
          <div class="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Mã chứng từ</th>
                  <th>Loại</th>
                  <th>Tên công bố</th>
                  <th>Phiên bản</th>
                  <th>Tải file</th>
                </tr>
              </thead>
              <tbody id="pub-docs-body"></tbody>
            </table>
          </div>
        </div>

        <div id="download-status-banner" style="margin-top: 12px;"></div>
        <h3>Payload công bố (<span class="mono" id="raw-json-url">/api/hexa/v0/shipments/ROAD-LG-001</span>)</h3>
        <pre id="raw-publication-json">{}</pre>
      </section>

      <section class="card" id="sandbox-operational-notice">
        <h2>Lưu ý vận hành &amp; Giới hạn môi trường thử nghiệm (Owner Gate)</h2>
        <div class="helper-box" style="margin-top: 0; color: var(--text);">
          <strong>1. Dữ liệu giả lập (SANDBOX_STAGING):</strong> Ba tài khoản khách (<span class="mono">lucgiac.trial</span>, <span class="mono">minhduc.trial</span>, <span class="mono">anphat.trial</span>), nhân sự TT (<span class="mono">tt.ops.truongthanh</span>), các lô <span class="mono">ROAD-LG-001</span>, <span class="mono">ROAD-MD-002</span>, <span class="mono">ROAD-AP-003</span> và tệp PDF chỉ phục vụ kiểm thử trong sandbox; tuyệt đối không dùng tài khoản/mật khẩu demo cho hệ thống thật.<br/>
          <strong>2. Giới hạn bộ nhớ trong tiến trình (In-Memory Persistence):</strong> Dữ liệu đang chạy trên <span class="mono">mongomock</span> + <span class="mono">GridFS</span> trong bộ nhớ RAM của tiến trình thử nghiệm; khi khởi động lại tiến trình, trạng thái quay về mặc định chưa công bố (<span class="mono">UNPUBLISHED</span>).<br/>
          <strong>3. Chưa sẵn sàng vận hành thực tế (Production Readiness Gaps):</strong> Chưa kết nối MongoDB Atlas thật, chưa tạo collection manifest công bố và bảng tài khoản khách hàng riêng trên DB production, chưa qua kiểm thử trình duyệt thực tế (<span class="mono">BROWSER_QA</span>) trên máy có Chromium, và chưa cấp quyền truy cập cho khách hàng thật.
        </div>
      </section>
    </div>
  </main>

  <script>
    let currentTtDeskData = null;
    let currentDashboardShipments = {};

    function formatVnd(val) {
      if (val === null || val === undefined) return 'Chưa xác định (null)';
      return new Intl.NumberFormat('vi-VN').format(val) + ' VND';
    }

    function switchScreen(which) {
      const isTt = which === 'tt';
      document.getElementById('screen-tt').classList.toggle('hidden', !isTt);
      document.getElementById('screen-customer').classList.toggle('hidden', isTt);
      document.getElementById('tab-btn-tt').classList.toggle('active', isTt);
      document.getElementById('tab-btn-customer').classList.toggle('active', !isTt);
      if (isTt) {
        refreshTtSessionState();
      } else {
        refreshSessionState();
        loadCustomerDashboard();
        loadRequestedShipment();
      }
    }

    function pickTtShipment(sid) {
      document.getElementById('tt-shipment-input').value = sid;
      loadTtShipmentDesk();
    }

    function fillCustomerCreds(username, passcode) {
      document.getElementById('cust-username').value = username;
      document.getElementById('cust-passcode').value = passcode;
    }

    async function refreshSessionState() {
      const res = await fetch('/api/hexa/v0/session', { credentials: 'same-origin' });
      const data = await res.json();
      const p = data.principal || {};
      const pill = document.getElementById('active-session-pill');
      pill.textContent = `${data.label || 'Ẩn danh'} | customer_id=${p.customer_id || '(chưa xác thực)'}`;
      pill.className = 'pill ' + (p.authenticated && p.kind === 'customer' ? 'pill-ok' : 'pill-deny');
      if (data.default_shipment_id) {
        document.getElementById('shipment-input').value = data.default_shipment_id;
      }
    }

    async function loginCustomer() {
      const username = (document.getElementById('cust-username').value || '').trim();
      const passcode = document.getElementById('cust-passcode').value || '';
      const banner = document.getElementById('cust-auth-banner');
      const res = await fetch('/api/hexa/v0/auth/login', {
        method: 'POST',
        credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, passcode }),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        banner.className = 'banner-result banner-deny';
        banner.textContent = `ĐĂNG NHẬP KHÁCH BỊ TỪ CHỐI (HTTP ${res.status}): Sai thông tin hoặc tài khoản không phải khách hàng.`;
        await refreshSessionState();
        await loadCustomerDashboard();
        return;
      }
      banner.className = 'banner-result banner-ok';
      banner.textContent = `ĐĂNG NHẬP THÀNH CÔNG: ${body.label} (customer_id=${(body.principal || {}).customer_id})`;
      await refreshSessionState();
      await loadCustomerDashboard();
      await loadRequestedShipment();
    }

    async function logoutCustomer() {
      await fetch('/api/hexa/v0/auth/logout', { method: 'POST', credentials: 'same-origin' });
      const banner = document.getElementById('cust-auth-banner');
      banner.className = 'banner-result banner-warn';
      banner.textContent = 'Đã đăng xuất phiên khách hàng.';
      await refreshSessionState();
      await loadCustomerDashboard();
      await loadRequestedShipment();
    }

    async function loadCustomerDashboard() {
      const res = await fetch('/api/hexa/v0/dashboard', { credentials: 'same-origin' });
      const statusBanner = document.getElementById('dashboard-status-banner');
      const tbody = document.getElementById('dash-shipments-tbody');
      const body = await res.json().catch(() => ({}));
      currentDashboardShipments = {};

      if (!res.ok) {
        statusBanner.className = 'banner-result banner-deny';
        statusBanner.textContent = `CHƯA XÁC THỰC KHÁCH HÀNG (HTTP ${res.status}): Hãy đăng nhập tài khoản khách ở Bước 1 để xem Dashboard.`;
        document.getElementById('dash-count-tracking').textContent = '0';
        document.getElementById('dash-count-arriving').textContent = '0';
        document.getElementById('dash-count-action').textContent = '0';
        tbody.innerHTML = '<tr><td colspan="8" class="muted">Chưa đăng nhập phiên khách hàng.</td></tr>';
        return;
      }

      const summary = body.summary || {};
      document.getElementById('dash-count-tracking').textContent = String(summary.active_tracking ?? 0);
      document.getElementById('dash-count-arriving').textContent = String(summary.arriving_soon ?? 0);
      document.getElementById('dash-count-action').textContent = String(summary.customer_action_needed ?? 0);

      const shipments = body.shipments || [];
      if (shipments.length === 0) {
        statusBanner.className = 'banner-result banner-warn';
        statusBanner.textContent = `Khách hàng ${body.customer_name} (${body.customer_id}): Hiện chưa có lô hàng nào được Trường Thành duyệt công bố (Trạng thái mặc định: Chưa công bố / Đã thu hồi).`;
        tbody.innerHTML = '<tr><td colspan="8" class="muted">Không có dữ liệu lô đã công bố. Khi nhân sự TT duyệt công bố lô hàng, lô sẽ xuất hiện tại đây.</td></tr>';
        renderJourneyMap(null);
        return;
      }

      statusBanner.className = 'banner-result banner-ok';
      statusBanner.textContent = `Dashboard ${body.customer_name} (${body.customer_id}) — Đang hiển thị ${shipments.length} lô đã được Trường Thành công bố.`;
      tbody.innerHTML = '';

      shipments.forEach(row => {
        currentDashboardShipments[row.shipment_id] = row;
        const tr = document.createElement('tr');
        tr.style.cursor = 'pointer';
        tr.onclick = () => selectDashboardShipment(row.shipment_id);
        const etaHtml = row.verified_warehouse_eta
          ? `<span class="pill pill-ok">${row.verified_warehouse_eta_label}</span>`
          : `<span class="pill pill-warn">${row.verified_warehouse_eta_label}</span>`;
        tr.innerHTML = `
          <td class="mono"><strong>${row.shipment_id}</strong><br/><span class="pill pill-ok">${row.transport_mode || 'ROAD'}</span></td>
          <td>${row.cargo_summary}<br/><span class="muted">${row.route_summary}</span></td>
          <td><strong>${row.verified_stage_label}</strong><br/><span class="muted">${row.verified_stage_title}</span></td>
          <td class="mono">${row.last_updated_label}</td>
          <td>${etaHtml}</td>
          <td>${row.next_step}</td>
          <td>${row.contact_point}</td>
          <td>
            <button onclick="event.stopPropagation(); selectDashboardShipment('${row.shipment_id}')">
              Mở Hành trình &amp; Chứng từ
            </button>
          </td>
        `;
        tbody.appendChild(tr);
      });

      const firstSid = shipments[0].shipment_id;
      document.getElementById('shipment-input').value = firstSid;
      renderJourneyMap(shipments[0].journey);
    }

    function renderJourneyMap(journey) {
      const container = document.getElementById('pub-journey-map');
      if (!container) return;
      if (!journey || !Array.isArray(journey.nodes) || journey.nodes.length === 0) {
        container.innerHTML = '<div class="journey-node"><div class="node-title">Chưa có hành trình công bố</div><div class="muted">Lô chưa được công bố hoặc đã bị thu hồi.</div></div>';
        return;
      }
      container.innerHTML = '';
      journey.nodes.forEach((n, idx) => {
        const div = document.createElement('div');
        div.className = 'journey-node' + (n.current ? ' current' : (n.completed ? ' done' : ''));
        const badge = n.current
          ? '<span class="pill pill-ok">● Vị trí xác minh gần nhất</span>'
          : (n.completed ? '<span class="pill pill-ok">✓ Đã xác minh</span>' : '<span class="pill pill-warn">○ Chưa xác minh</span>');
        div.innerHTML = `
          <div class="node-title">${idx + 1}. ${n.label}</div>
          <div style="margin-bottom:6px;">${badge}</div>
          <div class="muted">${n.evidence || ''}</div>
          ${n.occurred_at ? `<div class="mono muted" style="margin-top:4px;">${n.occurred_at}</div>` : ''}
        `;
        container.appendChild(div);
      });
    }

    async function selectDashboardShipment(sid) {
      document.getElementById('shipment-input').value = sid;
      const row = currentDashboardShipments[sid];
      if (row && row.journey) {
        renderJourneyMap(row.journey);
      }
      await loadShipment(sid);
    }

    async function refreshTtSessionState() {
      const res = await fetch('/api/hexa/v0/tt/session', { credentials: 'same-origin' });
      const data = await res.json();
      const p = data.principal || {};
      const pill = document.getElementById('tt-session-pill');
      const badge = document.getElementById('tt-login-badge');
      if (data.authenticated && p.kind === 'tt_staff') {
        pill.textContent = `TT: ${p.username} (${p.role})`;
        pill.className = 'pill pill-ok';
        badge.textContent = `Đã xác thực: ${p.display_name} (${p.username})`;
        badge.className = 'pill pill-ok';
        await loadTtShipmentDesk();
      } else {
        pill.textContent = 'TT: Chưa đăng nhập';
        pill.className = 'pill pill-warn';
        badge.textContent = 'Chưa xác thực TT';
        badge.className = 'pill pill-warn';
      }
    }

    async function loginTtStaff() {
      const username = (document.getElementById('tt-username').value || '').trim();
      const passcode = document.getElementById('tt-passcode').value || '';
      const banner = document.getElementById('tt-auth-banner');
      const res = await fetch('/api/hexa/v0/tt/auth/login', {
        method: 'POST',
        credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, passcode }),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        banner.className = 'banner-result banner-deny';
        banner.textContent = `ĐĂNG NHẬP TT BỊ TỪ CHỐI (HTTP ${res.status}): Tài khoản không có quyền duyệt công bố.`;
        return;
      }
      banner.className = 'banner-result banner-ok';
      banner.textContent = `ĐĂNG NHẬP NHÂN SỰ TT THÀNH CÔNG: ${body.label}`;
      await refreshTtSessionState();
    }

    async function logoutTtStaff() {
      await fetch('/api/hexa/v0/tt/auth/logout', { method: 'POST', credentials: 'same-origin' });
      document.getElementById('tt-desk-body').style.display = 'none';
      const status = document.getElementById('tt-desk-status');
      status.className = 'banner-result banner-warn';
      status.textContent = 'Đã đăng xuất nhân sự Trường Thành.';
      await refreshTtSessionState();
    }

    async function loadTtShipmentDesk() {
      const sid = (document.getElementById('tt-shipment-input').value || 'ROAD-LG-001').trim();
      const res = await fetch(`/api/hexa/v0/tt/shipments/${encodeURIComponent(sid)}`, { credentials: 'same-origin' });
      const status = document.getElementById('tt-desk-status');
      const deskBody = document.getElementById('tt-desk-body');
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        deskBody.style.display = 'none';
        status.className = 'banner-result banner-deny';
        status.textContent = `KHÔNG MỞ ĐƯỢC HỒ SƠ NỘI BỘ (HTTP ${res.status}): Cần đăng nhập nhân sự TT có quyền duyệt công bố.`;
        return;
      }
      currentTtDeskData = body;
      deskBody.style.display = 'block';
      const s = body.shipment || {};
      status.className = 'banner-result banner-ok';
      status.textContent = `Đang mở hồ sơ nội bộ lô ${s.shipment_id} — Khách hàng: ${s.customer_name} (${s.customer_id})`;
      document.getElementById('tt-ship-summary').textContent = `${s.shipment_id} · ${s.customer_name} (${s.customer_id}) · Phương thức: ${s.transport_mode}`;
      document.getElementById('tt-trip-summary').textContent = `${s.trip_id} · Biển số: ${s.shared_truck_plate}`;
      document.getElementById('tt-internal-holdback').textContent =
        `Giá vốn: ${formatVnd(s.internal_cost_summary_vnd)} | Lợi nhuận dự kiến: ${formatVnd(s.internal_margin_summary_vnd)} | ${s.unverified_eta_note}`;

      renderTtSelectionTables(body);
      renderTtPublicationAudit(body.publication || {});
    }

    function renderTtSelectionTables(body) {
      const pub = body.publication || {};
      const approvedEvents = pub.event_versions || {};
      const approvedDocs = pub.document_versions || {};
      const approvedQuote = pub.quote || null;

      const evTbody = document.getElementById('tt-events-tbody');
      evTbody.innerHTML = '';
      (body.candidate_events || []).forEach(ev => {
        const checked = approvedEvents[ev.id] === ev.version && pub.state === 'PUBLISHED';
        const tr = document.createElement('tr');
        if (ev.eligible_for_customer) {
          tr.innerHTML = `
            <td><input type="checkbox" class="tt-ev-check" data-id="${ev.id}" data-version="${ev.version}" ${checked ? 'checked' : ''} /></td>
            <td class="mono">${ev.id}@${ev.version}</td>
            <td>${ev.public_title}</td>
            <td><span class="pill pill-ok">Đã xác minh (${ev.verified_at})</span></td>
          `;
        } else {
          tr.innerHTML = `
            <td><input type="checkbox" disabled /></td>
            <td class="mono">${ev.id}@${ev.version}</td>
            <td class="muted">${ev.public_title}</td>
            <td><span class="pill pill-deny">Khóa tự động (Chưa xác minh / Nội bộ TT)</span></td>
          `;
        }
        evTbody.appendChild(tr);
      });

      const docTbody = document.getElementById('tt-docs-tbody');
      docTbody.innerHTML = '';
      (body.candidate_documents || []).forEach(doc => {
        const isCurrentApproved = approvedDocs[doc.id] === doc.version && pub.state === 'PUBLISHED';
        const tr = document.createElement('tr');
        if (doc.eligible_for_customer) {
          tr.innerHTML = `
            <td><input type="checkbox" class="tt-doc-check" data-id="${doc.id}" data-version="${doc.version}" ${isCurrentApproved ? 'checked' : ''} /></td>
            <td class="mono">${doc.id}@${doc.version}</td>
            <td class="mono"><span class="pill pill-ok">${doc.kind}</span></td>
            <td>${doc.public_title} <span class="muted mono">(${doc.file_name})</span></td>
            <td>
              ${isCurrentApproved
                ? `<button class="btn-danger" style="padding:4px 8px;font-size:12px;" onclick="submitTtRevokeDoc('${doc.id}')">Thu hồi chứng từ ${doc.id}</button>`
                : '<span class="muted">Đủ điều kiện công bố</span>'}
            </td>
          `;
        } else {
          tr.innerHTML = `
            <td><input type="checkbox" disabled /></td>
            <td class="mono">${doc.id}@${doc.version}</td>
            <td class="mono"><span class="pill pill-deny">${doc.kind}</span></td>
            <td class="muted">${doc.public_title}</td>
            <td><span class="pill pill-deny">Khóa tự động (Chứng từ nội bộ TT)</span></td>
          `;
        }
        docTbody.appendChild(tr);
      });

      const qBox = document.getElementById('tt-quote-box');
      const q = body.candidate_quote;
      if (q && q.id) {
        const qChecked = approvedQuote && approvedQuote.id === q.id && String(approvedQuote.version) === String(q.version) && pub.state === 'PUBLISHED';
        qBox.innerHTML = `
          <label style="display:flex;align-items:center;gap:8px;cursor:pointer;">
            <input type="checkbox" id="tt-quote-check" data-id="${q.id}" data-version="${q.version}" ${qChecked ? 'checked' : ''} />
            <span>Chia sẻ báo giá bán <strong class="mono">${q.id}@v${q.version}</strong> (Trạng thái: <span class="mono">${q.status}</span>) — Tổng giá bán: <strong>${formatVnd(q.selling_total_vnd)}</strong> (Tự động ẩn giá vốn &amp; biên lợi nhuận nội bộ)</span>
          </label>
        `;
      } else {
        qBox.textContent = 'Không có báo giá bán đủ điều kiện.';
      }
    }

    function renderTtPublicationAudit(pub) {
      const stateEl = document.getElementById('tt-pub-state');
      const isPub = pub.state === 'PUBLISHED';
      stateEl.innerHTML = `<span class="pill ${isPub ? 'pill-ok' : 'pill-deny'}">${pub.state || 'UNPUBLISHED'}</span>`;
      document.getElementById('tt-pub-approved').textContent =
        pub.approved_by ? `${pub.approved_by} lúc ${pub.approved_at}` : '(Chưa có)';
      document.getElementById('tt-pub-revoked').textContent =
        pub.revoked_by ? `${pub.revoked_by} lúc ${pub.revoked_at}` : '(Chưa thu hồi)';
      const evStr = Object.entries(pub.event_versions || {}).map(([k, v]) => `${k}@${v}`).join(', ') || 'Không có';
      const docStr = Object.entries(pub.document_versions || {}).map(([k, v]) => `${k}@${v}`).join(', ') || 'Không có';
      const qStr = pub.quote ? `${pub.quote.id}@v${pub.quote.version}` : 'Không có';
      document.getElementById('tt-pub-items').textContent = `Tiến độ: [${evStr}] | Chứng từ: [${docStr}] | Báo giá: [${qStr}]`;
      document.getElementById('tt-pub-history-json').textContent = JSON.stringify(pub, null, 2);
    }

    function selectAllEligibleTtItems() {
      document.querySelectorAll('.tt-ev-check, .tt-doc-check').forEach(el => {
        if (!el.disabled) el.checked = true;
      });
      const qEl = document.getElementById('tt-quote-check');
      if (qEl && !qEl.disabled) qEl.checked = true;
    }

    async function submitTtPublish() {
      const sid = (document.getElementById('tt-shipment-input').value || 'ROAD-LG-001').trim();
      const event_versions = {};
      document.querySelectorAll('.tt-ev-check:checked').forEach(el => {
        event_versions[el.dataset.id] = el.dataset.version;
      });
      const document_versions = {};
      document.querySelectorAll('.tt-doc-check:checked').forEach(el => {
        document_versions[el.dataset.id] = el.dataset.version;
      });
      let quote = null;
      const qEl = document.getElementById('tt-quote-check');
      if (qEl && qEl.checked) {
        quote = { id: qEl.dataset.id, version: qEl.dataset.version };
      }

      const res = await fetch(`/api/hexa/v0/tt/shipments/${encodeURIComponent(sid)}/publish`, {
        method: 'POST',
        credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ event_versions, document_versions, quote }),
      });
      const status = document.getElementById('tt-desk-status');
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        status.className = 'banner-result banner-deny';
        status.textContent = `DUYỆT CÔNG BỐ THẤT BẠI (HTTP ${res.status})`;
        return;
      }
      status.className = 'banner-result banner-ok';
      status.textContent = `ĐÃ DUYỆT CÔNG BỐ CHO KHÁCH (${sid}) — Người duyệt: ${body.publication.approved_by} lúc ${body.publication.approved_at}`;
      await loadTtShipmentDesk();
    }

    async function submitTtRevokeDoc(docId) {
      const sid = (document.getElementById('tt-shipment-input').value || 'ROAD-LG-001').trim();
      const res = await fetch(`/api/hexa/v0/tt/shipments/${encodeURIComponent(sid)}/revoke`, {
        method: 'POST',
        credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ document_ids: [docId] }),
      });
      const status = document.getElementById('tt-desk-status');
      const body = await res.json().catch(() => ({}));
      if (res.ok) {
        status.className = 'banner-result banner-warn';
        status.textContent = `ĐÃ THU HỒI CHỨNG TỪ ${docId} — Khách hàng không thể tải chứng từ này nữa kể cả dùng link cũ.`;
        await loadTtShipmentDesk();
      }
    }

    async function submitTtRevokeAll() {
      const sid = (document.getElementById('tt-shipment-input').value || 'ROAD-LG-001').trim();
      const res = await fetch(`/api/hexa/v0/tt/shipments/${encodeURIComponent(sid)}/revoke`, {
        method: 'POST',
        credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      });
      const status = document.getElementById('tt-desk-status');
      const body = await res.json().catch(() => ({}));
      if (res.ok) {
        status.className = 'banner-result banner-warn';
        status.textContent = `ĐÃ THU HỒI TOÀN BỘ CÔNG BỐ LÔ ${sid} — Người thu hồi: ${body.publication.revoked_by} lúc ${body.publication.revoked_at}`;
        await loadTtShipmentDesk();
      }
    }

    async function loadRequestedShipment() {
      const sid = (document.getElementById('shipment-input').value || '').trim();
      if (!sid) return;
      await loadShipment(sid);
    }

    async function loadShipment(shipmentPath) {
      const url = `/api/hexa/v0/shipments/${encodeURIComponent(shipmentPath)}`;
      document.getElementById('raw-json-url').textContent = url;
      const res = await fetch(url, { credentials: 'same-origin' });
      const body = await res.json();

      const statusBadge = document.getElementById('http-status-badge');
      statusBadge.textContent = `HTTP ${res.status}`;
      statusBadge.className = 'pill ' + (res.ok ? 'pill-ok' : 'pill-deny');

      document.getElementById('raw-publication-json').textContent = JSON.stringify(body, null, 2);

      const banner = document.getElementById('portal-status-banner');
      const content = document.getElementById('portal-content');

      if (!res.ok) {
        banner.className = 'banner-result banner-deny';
        banner.textContent = `TRUY CẬP BỊ TỪ CHỐI (HTTP ${res.status}): ${body.error || 'CUSTOMER_RESOURCE_UNAVAILABLE'} (Chưa đăng nhập khách, lô chưa công bố, hoặc không thuộc quyền xem của bạn)`;
        content.style.opacity = '0.45';
        return;
      }

      content.style.opacity = '1';
      banner.className = 'banner-result banner-ok';
      banner.textContent = `ĐỌC DỮ LIỆU CÔNG BỐ THÀNH CÔNG (HTTP 200) — Lô ${body.reference} (${body.transport_mode})`;

      document.getElementById('pub-schema').textContent = body.schema || '-';
      document.getElementById('pub-reference').textContent = body.reference || '-';
      document.getElementById('pub-mode').textContent = body.transport_mode || '-';
      if (body.quote) {
        document.getElementById('pub-quote').innerHTML =
          `<strong>${formatVnd(body.quote.selling_total_vnd)}</strong> <span class="mono">(Mã: ${body.quote.id} · v${body.quote.version} · Trạng thái: ${body.quote.status})</span>`;
      } else {
        document.getElementById('pub-quote').textContent = 'Chưa có báo giá công bố';
      }

      const tlBody = document.getElementById('pub-timeline-body');
      tlBody.innerHTML = '';
      (body.timeline || []).forEach(ev => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td class="mono">${ev.id}</td>
          <td class="mono">${ev.stage}</td>
          <td>${ev.title}</td>
          <td class="mono">${ev.occurred_at}</td>
          <td class="mono">${ev.version}</td>
        `;
        tlBody.appendChild(tr);
      });

      const docsBody = document.getElementById('pub-docs-body');
      docsBody.innerHTML = '';
      (body.documents || []).forEach(doc => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td class="mono">${doc.id}</td>
          <td class="mono"><span class="pill pill-ok">${doc.kind}</span></td>
          <td>${doc.title}</td>
          <td class="mono">${doc.version}</td>
          <td>
            <button onclick="triggerDownload('${body.reference}', '${doc.id}', '${doc.version}')">
              ⬇ Tải ${doc.id} (${doc.version})
            </button>
          </td>
        `;
        docsBody.appendChild(tr);
      });
    }

    async function triggerDownload(shipmentId, docId, version) {
      const url = `/api/hexa/v0/shipments/${encodeURIComponent(shipmentId)}/documents/${encodeURIComponent(docId)}/download?version=${encodeURIComponent(version)}`;
      const res = await fetch(url, { credentials: 'same-origin' });
      const banner = document.getElementById('download-status-banner');
      if (res.ok) {
        const blob = await res.blob();
        banner.className = 'banner-result banner-ok';
        banner.textContent = `TẢI CHỨNG TỪ THÀNH CÔNG (HTTP ${res.status}): ${docId}@${version} (${blob.size} bytes PDF).`;
        const dlUrl = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = dlUrl;
        a.download = `${docId}-${version}.pdf`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(dlUrl);
      } else {
        const err = await res.json().catch(() => ({}));
        banner.className = 'banner-result banner-deny';
        banner.textContent = `TỪ CHỐI TẢI CHỨNG TỪ (HTTP ${res.status}): ${err.error || 'CUSTOMER_RESOURCE_UNAVAILABLE'}`;
      }
    }

    window.addEventListener('DOMContentLoaded', async () => {
      await refreshSessionState();
      await refreshTtSessionState();
      await loadCustomerDashboard();
      await loadRequestedShipment();
    });
  </script>
</body>
</html>
"""


class HexaTrialRequestHandler(BaseHTTPRequestHandler):
    """HTTP handler for the isolated HEXA V0 trial server.

    By default ``internal_qa_mode`` is ``False``:
    - Customer UI (``/``, ``/hexa``) never auto-mints customer cookies and
      never embeds internal TT data.
    - ``/api/hexa/v0/trial-inspector`` and ``POST /api/hexa/v0/session`` are
      rejected with ``HTTP 403 CUSTOMER_RESOURCE_UNAVAILABLE``.
    - ``/internal/qa/*`` is disabled unless ``internal_qa_mode=True`` AND the
      caller supplies the server-generated ``X-Hexa-Internal-QA-Key`` header.
    """

    env: HexaTrialEnvironment = _DEFAULT_ENV
    internal_qa_mode: bool = False

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        return

    def _send_json(
        self,
        status: int,
        payload: Mapping[str, Any],
        *,
        set_cookie_token: str | None = None,
        cookie_name: str = TRIAL_COOKIE_NAME,
    ) -> None:
        raw = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        if set_cookie_token is not None:
            self.send_header(
                "Set-Cookie",
                f"{cookie_name}={set_cookie_token}; Path=/; HttpOnly; SameSite=Lax",
            )
        self.end_headers()
        self.wfile.write(raw)

    def _send_html(self, status: int, html: str) -> None:
        raw = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def _current_token(self) -> str:
        return _extract_session_token(self.headers)

    def _current_tt_token(self) -> str:
        return _extract_tt_session_token(self.headers)

    def _read_json_body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length") or 0)
        raw_body = self.rfile.read(length) if length > 0 else b"{}"
        try:
            parsed = json.loads(raw_body.decode("utf-8"))
            return parsed if isinstance(parsed, dict) else {}
        except Exception:  # noqa: BLE001
            return {}

    def _is_authorized_internal_qa(self) -> bool:
        if not self.internal_qa_mode:
            return False
        qa_key = (
            self.headers.get(INTERNAL_QA_HEADER)
            or self.headers.get(INTERNAL_QA_HEADER.lower())
            or ""
        )
        return self.env.verify_internal_qa_key(qa_key)

    def do_GET(self) -> None:  # noqa: N802
        self.env.ensure_seeded()
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        query = parse_qs(parsed.query)

        if path in {"/", "/hexa"}:
            self._send_html(HTTPStatus.OK, render_trial_portal_html())
            return

        if path == "/api/hexa/v0/health":
            self._send_json(
                HTTPStatus.OK,
                {
                    "ok": True,
                    "schema": PUBLICATION_SCHEMA,
                    "transport": "SANDBOX_STAGING",
                },
            )
            return

        if path == "/api/hexa/v0/session":
            self._send_json(
                HTTPStatus.OK,
                self.env.resolve_session_summary(self._current_token()),
            )
            return

        if path == "/api/hexa/v0/tt/session":
            self._send_json(
                HTTPStatus.OK,
                self.env.resolve_tt_session_summary(self._current_tt_token()),
            )
            return

        if path == "/api/hexa/v0/dashboard":
            try:
                payload = self.env.build_customer_dashboard(
                    session_token=self._current_token(),
                )
                self._send_json(HTTPStatus.OK, payload)
            except PublicationDenied as exc:
                self._send_json(HTTPStatus.FORBIDDEN, {"error": str(exc)})
            return

        # Customer API NEVER exposes TT internal inspector data.
        if path == "/api/hexa/v0/trial-inspector":
            self._send_json(
                HTTPStatus.FORBIDDEN,
                {"error": "CUSTOMER_RESOURCE_UNAVAILABLE"},
            )
            return

        # Isolated internal QA inspector (disabled by default; requires server-only X-Hexa-Internal-QA-Key).
        if path == "/internal/qa/inspector":
            if not self._is_authorized_internal_qa():
                self._send_json(
                    HTTPStatus.FORBIDDEN,
                    {"error": "CUSTOMER_RESOURCE_UNAVAILABLE"},
                )
                return
            self._send_json(HTTPStatus.OK, self.env.build_trial_inspector_snapshot())
            return

        parts = [p for p in path.split("/") if p]

        # Route: GET /api/hexa/v0/tt/shipments/<shipment_id> (Authorized TT staff only)
        if len(parts) == 6 and parts[:5] == ["api", "hexa", "v0", "tt", "shipments"]:
            shipment_id = parts[5]
            try:
                payload = self.env.inspect_shipment_for_tt_staff(
                    session_token=self._current_tt_token(),
                    shipment_id=shipment_id,
                )
                self._send_json(HTTPStatus.OK, payload)
            except PublicationDenied as exc:
                self._send_json(HTTPStatus.FORBIDDEN, {"error": str(exc)})
            return

        # Route: GET /api/hexa/v0/shipments/<shipment_id>
        if len(parts) == 5 and parts[:4] == ["api", "hexa", "v0", "shipments"]:
            shipment_id = parts[4]
            try:
                payload = self.env.read_customer_publication(
                    session_token=self._current_token(),
                    shipment_id=shipment_id,
                )
                self._send_json(HTTPStatus.OK, payload)
            except PublicationDenied as exc:
                self._send_json(HTTPStatus.FORBIDDEN, {"error": str(exc)})
            return

        # Route: GET /api/hexa/v0/shipments/<shipment_id>/documents/<doc_id>/download?version=<ver>
        if (
            len(parts) == 8
            and parts[:4] == ["api", "hexa", "v0", "shipments"]
            and parts[5] == "documents"
            and parts[7] == "download"
        ):
            shipment_id = parts[4]
            document_id = parts[6]
            requested_version = str((query.get("version") or [""])[0] or "").strip()
            try:
                download = self.env.download_customer_document(
                    session_token=self._current_token(),
                    shipment_id=shipment_id,
                    document_id=document_id,
                    requested_version=requested_version,
                )
            except PublicationDenied as exc:
                self._send_json(HTTPStatus.FORBIDDEN, {"error": str(exc)})
                return

            data = download["data"]
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", download["mime"])
            self.send_header("Content-Length", str(len(data)))
            self.send_header(
                "Content-Disposition",
                f'attachment; filename="{download["file_name"]}"',
            )
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(data)
            return

        self._send_json(HTTPStatus.NOT_FOUND, {"error": "NOT_FOUND"})

    def do_POST(self) -> None:  # noqa: N802
        self.env.ensure_seeded()
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        parts = [p for p in path.split("/") if p]

        # Customer path NEVER allows self-service session switching.
        if path == "/api/hexa/v0/session":
            self._send_json(
                HTTPStatus.FORBIDDEN,
                {"error": "CUSTOMER_RESOURCE_UNAVAILABLE"},
            )
            return

        # Server-verified Customer trial login (binds 1 customer_id on server; ignores client customer_id)
        if path == "/api/hexa/v0/auth/login":
            body = self._read_json_body()
            username = str(body.get("username") or "").strip()
            passcode = str(body.get("passcode") or body.get("access_code") or "")
            try:
                issued_token, summary = self.env.authenticate_customer_login(
                    username=username,
                    passcode=passcode,
                )
                self._send_json(
                    HTTPStatus.OK,
                    summary,
                    set_cookie_token=issued_token,
                    cookie_name=TRIAL_COOKIE_NAME,
                )
            except PublicationDenied as exc:
                self._send_json(HTTPStatus.FORBIDDEN, {"error": str(exc)})
            return

        if path == "/api/hexa/v0/auth/logout":
            self.env.logout_session(self._current_token())
            self._send_json(
                HTTPStatus.OK,
                self.env.resolve_session_summary(""),
                set_cookie_token="",
                cookie_name=TRIAL_COOKIE_NAME,
            )
            return

        # Server-verified TT Staff trial login (requires operations_write permission)
        if path == "/api/hexa/v0/tt/auth/login":
            body = self._read_json_body()
            username = str(body.get("username") or "").strip()
            passcode = str(body.get("passcode") or body.get("access_code") or "")
            try:
                issued_token, summary = self.env.authenticate_tt_staff_login(
                    username=username,
                    passcode=passcode,
                )
                self._send_json(
                    HTTPStatus.OK,
                    summary,
                    set_cookie_token=issued_token,
                    cookie_name=TRIAL_TT_COOKIE_NAME,
                )
            except PublicationDenied as exc:
                self._send_json(HTTPStatus.FORBIDDEN, {"error": str(exc)})
            return

        if path == "/api/hexa/v0/tt/auth/logout":
            self.env.logout_session(self._current_tt_token())
            self._send_json(
                HTTPStatus.OK,
                self.env.resolve_tt_session_summary(""),
                set_cookie_token="",
                cookie_name=TRIAL_TT_COOKIE_NAME,
            )
            return

        # Route: POST /api/hexa/v0/tt/shipments/<shipment_id>/publish
        if (
            len(parts) == 7
            and parts[:5] == ["api", "hexa", "v0", "tt", "shipments"]
            and parts[6] == "publish"
        ):
            shipment_id = parts[5]
            body = self._read_json_body()
            try:
                result = self.env.publish_shipment_for_customer(
                    session_token=self._current_tt_token(),
                    shipment_id=shipment_id,
                    event_versions=body.get("event_versions") if isinstance(body.get("event_versions"), Mapping) else {},
                    document_versions=body.get("document_versions") if isinstance(body.get("document_versions"), Mapping) else {},
                    quote=body.get("quote") if isinstance(body.get("quote"), Mapping) else None,
                )
                self._send_json(HTTPStatus.OK, result)
            except PublicationDenied as exc:
                self._send_json(HTTPStatus.FORBIDDEN, {"error": str(exc)})
            return

        # Route: POST /api/hexa/v0/tt/shipments/<shipment_id>/revoke
        if (
            len(parts) == 7
            and parts[:5] == ["api", "hexa", "v0", "tt", "shipments"]
            and parts[6] == "revoke"
        ):
            shipment_id = parts[5]
            body = self._read_json_body()
            doc_ids = body.get("document_ids") if isinstance(body.get("document_ids"), list) else None
            ev_ids = body.get("event_ids") if isinstance(body.get("event_ids"), list) else None
            rev_quote = bool(body.get("revoke_quote", False))
            try:
                result = self.env.revoke_shipment_publication(
                    session_token=self._current_tt_token(),
                    shipment_id=shipment_id,
                    document_ids=doc_ids,
                    event_ids=ev_ids,
                    revoke_quote=rev_quote,
                )
                self._send_json(HTTPStatus.OK, result)
            except PublicationDenied as exc:
                self._send_json(HTTPStatus.FORBIDDEN, {"error": str(exc)})
            return

        # Isolated internal QA session switcher (only when internal_qa_mode=True + valid X-Hexa-Internal-QA-Key).
        if path == "/internal/qa/session":
            if not self._is_authorized_internal_qa():
                self._send_json(
                    HTTPStatus.FORBIDDEN,
                    {"error": "CUSTOMER_RESOURCE_UNAVAILABLE"},
                )
                return

            body = self._read_json_body()
            role_key = str((body or {}).get("role") or "").strip()
            if role_key == "anonymous":
                self._send_json(
                    HTTPStatus.OK,
                    self.env.resolve_session_summary(""),
                    set_cookie_token="",
                )
                return
            try:
                issued_token = self.env.get_trial_session_token(role_key)
            except KeyError:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": "INVALID_TRIAL_ROLE"})
                return

            self._send_json(
                HTTPStatus.OK,
                self.env.resolve_session_summary(issued_token),
                set_cookie_token=issued_token,
            )
            return

        self._send_json(HTTPStatus.NOT_FOUND, {"error": "NOT_FOUND"})


def create_trial_http_server(
    host: str = "0.0.0.0",
    port: int = 8787,
    *,
    env: HexaTrialEnvironment | None = None,
    internal_qa_mode: bool = False,
) -> ThreadingHTTPServer:
    """Create a ThreadingHTTPServer bound to ``(host, port)`` for the HEXA trial.

    ``internal_qa_mode`` defaults to ``False`` (strict customer boundary).
    """
    active_env = env or get_trial_environment()
    active_env.ensure_seeded()

    class _BoundHandler(HexaTrialRequestHandler):
        pass

    _BoundHandler.env = active_env
    _BoundHandler.internal_qa_mode = bool(internal_qa_mode)
    return ThreadingHTTPServer((host, port), _BoundHandler)
