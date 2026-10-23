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
import threading
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
TT_FINANCE_TRIAL_USERNAME = "tt.finance.truongthanh"
TT_FINANCE_TRIAL_PASSCODE = "TT-Finance-2026!"
TT_VIEWER_TRIAL_USERNAME = "tt.viewer"
TT_VIEWER_TRIAL_PASSCODE = "Viewer-Trial-2026!"

CUSTOMER_JOURNEY_STAGE_IDS: tuple[str, ...] = (
    "plan",
    "pickup",
    "road-ltl",
    "road-border",
    "customs-import",
    "delivery",
    "finance-reconciliation",
)

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
        TT_FINANCE_TRIAL_USERNAME,
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
SHIPMENT_A2_ID = "ROAD-LG-002"
SHIPMENT_B_ID = "ROAD-MD-002"
SHIPMENT_C_ID = "ROAD-AP-003"

QUOTE_A_ID = "Q-LG-ROAD-001"
QUOTE_A2_ID = "Q-LG-ROAD-002"
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
        self._finance_confirmation_lock = threading.RLock()

    def ensure_seeded(self, *, force_reset: bool = False) -> None:
        if self._seeded and not force_reset:
            from views import logi_sandbox

            if logi_sandbox.transport_name() != logi_sandbox.SANDBOX_TRANSPORT:
                raise RuntimeError(
                    "HEXA trial portal chỉ được chạy trên SANDBOX_STAGING, tuyệt đối không dùng DB thật."
                )
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
                "label": "Công ty TNHH Lục Giác (HEXA)",
                "principal": {
                    "authenticated": True,
                    "kind": "customer",
                    "customer_id": CUSTOMER_A_ID,
                    "display_name": "Công ty TNHH Lục Giác (HEXA)",
                },
                "default_shipment_id": SHIPMENT_A_ID,
            },
            token_customer_b: {
                "role_key": "customer_b",
                "label": "Công ty CP Minh Đức",
                "principal": {
                    "authenticated": True,
                    "kind": "customer",
                    "customer_id": CUSTOMER_B_ID,
                    "display_name": "Công ty CP Minh Đức",
                },
                "default_shipment_id": SHIPMENT_B_ID,
            },
            token_customer_c: {
                "role_key": "customer_c",
                "label": "Công ty TNHH Thiết bị An Phát",
                "principal": {
                    "authenticated": True,
                    "kind": "customer",
                    "customer_id": CUSTOMER_C_ID,
                    "display_name": "Công ty TNHH Thiết bị An Phát",
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
        # - tt.ops.truongthanh has role='operations' (operations_write only, NO finance_write)
        # - tt.finance.truongthanh has role='support' (has finance_write + operations_write)
        tt_staff_doc = core_users.build_user_document(
            TT_STAFF_TRIAL_USERNAME,
            TT_STAFF_TRIAL_PASSCODE,
            "Điều vận Trường Thành (TT Ops)",
            "support",
            active=True,
            created_by="system",
        )
        tt_staff_doc["role"] = "operations"
        tt_finance_doc = core_users.build_user_document(
            TT_FINANCE_TRIAL_USERNAME,
            TT_FINANCE_TRIAL_PASSCODE,
            "Kế toán Trường Thành (TT Finance)",
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
        db["users"].replace_one({"username": TT_FINANCE_TRIAL_USERNAME}, tt_finance_doc, upsert=True)
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
                    "label": "Công ty TNHH Lục Giác (HEXA)",
                    "display_name": "Công ty TNHH Lục Giác (HEXA)",
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
                    "label": "Công ty CP Minh Đức",
                    "display_name": "Công ty CP Minh Đức",
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
                    "label": "Công ty TNHH Thiết bị An Phát",
                    "display_name": "Công ty TNHH Thiết bị An Phát",
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
        quote_a2 = self._build_trial_quote(
            core_quotes,
            quote_id=QUOTE_A2_ID,
            quote_no="QT-20261023-LG02",
            customer_id=CUSTOMER_A_ID,
            customer_name="Công ty TNHH Lục Giác (HEXA)",
            factory_name=f"Zhongshan Hexa Lighting Factory [{SENTINEL_TT_PRIVATE_SUPPLIER}]",
            pickup_address="Guzhen, Zhongshan, Guangdong",
            lines=[
                {
                    "code": "ROAD-LTL-DH-HN",
                    "service_name": "Cước đường bộ Đông Hưng → Móng Cái → Long Biên, Hà Nội",
                    "unit": "Lô ghép",
                    "qty": 1,
                    "currency": "VND",
                    "cost_unit": 27000000,
                    "sell_unit": 35000000,
                    "tax_pct": 8,
                    "internal_note": f"Giá vốn lô 2 Lục Giác {SENTINEL_TT_INTERNAL_COST}",
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
        db["quotes"].replace_one({"id": QUOTE_A2_ID}, quote_a2, upsert=True)
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

        shipment_a2 = logi_staging_seed._shipment(
            sid=SHIPMENT_A2_ID,
            customer="Công ty TNHH Lục Giác (HEXA)",
            customer_id=CUSTOMER_A_ID,
            contract_id="HDMB-LG-2026-02",
            status="pending",
            created="2026-10-21",
            mode="Truck",
            incoterm="DAP",
            transport={
                "booking_no": "TRIP-ROAD-2026-03",
                "carrier": f"Nhà xe Việt Trung An Bình ({SENTINEL_TT_PRIVATE_SUPPLIER})",
                "etd": "2026-10-21",
                "eta": "2026-10-24",
                "pol": "Đông Hưng (Quảng Tây)",
                "pod": "Móng Cái → Long Biên, Hà Nội",
                "container_no": "29H-912.34",
                "qty_pkg": "Thiết bị chiếu sáng văn phòng — 10 pallet / 2.600 kg",
                "road_facts": {
                    "ltl_received_at": "2026-10-21T09:00",
                    "ltl_package_count": "10",
                    "ltl_weight_kg": "2600",
                    "ltl_consolidated_at": "2026-10-21T15:00",
                    "border_crossed_at": "2026-10-22T11:30",
                },
            },
            customs={
                "tk_no": "106688114455",
                "customs_status": True,
                "phan_luong": "Xanh",
            },
            arrival={"arrival_date": "2026-10-24", "free_time": 5},
            delivery={
                "truck_no": "29H-912.34",
                "seal_no": "SEAL-ROAD-912",
                "delivery_date": "",
                "addr": "Kho Lục Giác — Long Biên, Hà Nội",
                "is_delivered": False,
            },
            details=[
                logi_staging_seed._line(
                    "Cước đường bộ Đông Hưng → Long Biên, Hà Nội",
                    "ROAD-LTL-DH-HN",
                    1,
                    35000000,
                    27000000,
                    8,
                    note=f"Giá vốn nội bộ TT: {SENTINEL_TT_INTERNAL_COST}",
                ),
            ],
        )
        shipment_a2["sale_owner"] = "Minh Tú (CSKH & Sale Trường Thành)"

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
            (shipment_a2, "Hà Nội"),
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
        att_lg02_pl_v1 = self._upload_trial_pdf(
            core_att,
            shipment_id=SHIPMENT_A2_ID,
            file_name="Packing-List-Luc-Giac-Lo2-v1.pdf",
            category="transport",
            title="HEXA PACKING LIST LO 2 v1 (APPROVED FOR LUC GIAC)",
            lines=[
                f"Shipment: {SHIPMENT_A2_ID}",
                "Customer: Cong ty TNHH Luc Giac",
                "Version: v1 (TT verified and published)",
                "Cargo: 10 pallets / 2,600 kg",
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
                    "quote_no": "QT-20261022-LG01",
                    "quote_confirmation_status": "ĐÃ XÁC NHẬN",
                    "contract_no": "HDVC-LG-2026-01",
                    "contract_status": "ĐÃ KÝ KẾT (2026-10-17)",
                    "payment_terms": "Tạm ứng khi lấy hàng; đối soát & tất toán phần còn lại theo chứng từ giao hàng",
                    "entrusted_import_applicable": False,
                    "plan_verified": True,
                    "plan_verified_at": "2026-10-17T16:00:00Z",
                    "cargo_summary": "Nội thất văn phòng — 18 kiện / 4.200 kg",
                    "route_summary": "Bằng Tường (Quảng Tây) → Hữu Nghị → Cầu Giấy, Hà Nội",
                    "internal_cost_vnd": 42000000,
                    "internal_margin_vnd": 11000000,
                    "internal_supplier": f"Foshan Hexa Furniture Factory ({SENTINEL_TT_PRIVATE_SUPPLIER})",
                    "internal_carrier_vendor": "Nhà xe Việt Trung An Bình (hợp đồng mua chuyến nội bộ TT)",
                    "unverified_eta": f"2026-10-25 ({SENTINEL_TT_UNVERIFIED_ETA})",
                },
                {
                    "shipment_id": SHIPMENT_A2_ID,
                    "customer_id": CUSTOMER_A_ID,
                    "trip_id": "TRIP-ROAD-2026-03",
                    "shared_truck_plate": "29H-912.34",
                    "transport_mode": "ROAD",
                    "quote_id": QUOTE_A2_ID,
                    "quote_no": "QT-20261023-LG02",
                    "quote_confirmation_status": "ĐÃ XÁC NHẬN",
                    "contract_no": "HDUT-LG-2026-02",
                    "contract_status": "ĐÃ KÝ KẾT — ỦY THÁC NHẬP KHẨU (2026-10-19)",
                    "payment_terms": "Ứng trước tiền hàng ủy thác theo PI; phí dịch vụ & vận chuyển đối soát riêng khi giao hàng",
                    "entrusted_import_applicable": True,
                    "plan_verified": True,
                    "plan_verified_at": "2026-10-19T11:00:00Z",
                    "cargo_summary": "Thiết bị chiếu sáng văn phòng — 10 pallet / 2.600 kg",
                    "route_summary": "Đông Hưng (Quảng Tây) → Móng Cái → Long Biên, Hà Nội",
                    "internal_cost_vnd": 27000000,
                    "internal_margin_vnd": 8000000,
                    "internal_supplier": f"Zhongshan Hexa Lighting Factory ({SENTINEL_TT_PRIVATE_SUPPLIER})",
                    "internal_carrier_vendor": "Nhà xe Việt Trung An Bình",
                    "unverified_eta": "2026-10-24",
                },
                {
                    "shipment_id": SHIPMENT_B_ID,
                    "customer_id": CUSTOMER_B_ID,
                    "trip_id": SHARED_TRIP_ID,
                    "shared_truck_plate": SHARED_TRUCK_PLATE,
                    "transport_mode": "ROAD",
                    "quote_id": QUOTE_B_ID,
                    "quote_no": "QT-20261022-MD02",
                    "quote_confirmation_status": "ĐÃ XÁC NHẬN",
                    "contract_no": "HDVC-MD-2026-01",
                    "contract_status": "ĐÃ KÝ KẾT",
                    "payment_terms": "Thanh toán theo đối soát lô",
                    "entrusted_import_applicable": False,
                    "plan_verified": True,
                    "plan_verified_at": "2026-10-18T09:00:00Z",
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
                    "quote_no": "QT-20261022-AP03",
                    "quote_confirmation_status": "Chưa xác nhận",
                    "contract_no": "HDMB-AP-2026",
                    "contract_status": "Chưa xác nhận",
                    "payment_terms": "Chưa xác nhận",
                    "entrusted_import_applicable": False,
                    "plan_verified": False,
                    "plan_verified_at": "",
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
                {
                    "id": "EVT-LG02-01-PICKUP",
                    "version": "v1",
                    "customer_id": CUSTOMER_A_ID,
                    "shipment_id": SHIPMENT_A2_ID,
                    "trip_id": "TRIP-ROAD-2026-03",
                    "stage_id": "pickup",
                    "public_title": "Đã nhận 10 pallet thiết bị chiếu sáng Lục Giác tại kho Đông Hưng (xe 29H-912.34)",
                    "occurred_at": "2026-10-21T09:00:00Z",
                    "verified": True,
                    "verified_at": "2026-10-21T10:00:00Z",
                    "visibility": "CUSTOMER",
                    "private_notes": "",
                },
                {
                    "id": "EVT-LG02-02-CUSTOMS",
                    "version": "v1",
                    "customer_id": CUSTOMER_A_ID,
                    "shipment_id": SHIPMENT_A2_ID,
                    "trip_id": "TRIP-ROAD-2026-03",
                    "stage_id": "customs-import",
                    "public_title": "Đã hoàn tất thông quan nhập khẩu tại Móng Cái — xác nhận lịch giao kho Long Biên ngày 2026-10-24",
                    "occurred_at": "2026-10-22T15:30:00Z",
                    "verified": True,
                    "verified_at": "2026-10-22T16:00:00Z",
                    "visibility": "CUSTOMER",
                    "verified_warehouse_eta": "2026-10-24",
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
                    "id": "DOC-LG02-PL",
                    "version": "v1",
                    "customer_id": CUSTOMER_A_ID,
                    "shipment_id": SHIPMENT_A2_ID,
                    "trip_id": "TRIP-ROAD-2026-03",
                    "kind": "PL",
                    "status": "AVAILABLE",
                    "visibility": "CUSTOMER",
                    "verified": True,
                    "public_title": "Packing List Lục Giác Lô 2 (Bản v1 đã duyệt)",
                    "file_name": "Packing-List-Luc-Giac-Lo2-v1.pdf",
                    "attachment_id": att_lg02_pl_v1["id"],
                    "attachment_shipment_id": SHIPMENT_A2_ID,
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

        # 7. Seed canonical financial ledger records in SANDBOX_STAGING (core.financial_ledger collections:
        #    financial_obligations, financial_transactions, financial_allocations).
        #    - ROAD-LG-001 (normal service): confirmed LOGISTICS_SERVICE receivable 57,240,000 VND,
        #      confirmed advance payment 30,000,000 VND on 2026-10-20 (before delivery), remaining 27,240,000 VND.
        #      Also includes an internal partner payable (42,000,000 VND) that must NEVER leak to the customer portal.
        #    - ROAD-LG-002 (entrusted import): confirmed ENTRUSTED_GOODS_ADVANCE obligation 200,000,000 VND,
        #      confirmed received 150,000,000 VND, shortfall 50,000,000 VND; NO confirmed LOGISTICS_SERVICE obligation
        #      yet -> proves Node 06 & Dashboard show UNKNOWN / Chưa đối soát (never 0, never copying quote total!).
        from core.financial_ledger import ALLOCATIONS, CONFIRMED, OBLIGATIONS, TRANSACTIONS

        db[OBLIGATIONS].delete_many({})
        db[TRANSACTIONS].delete_many({})
        db[ALLOCATIONS].delete_many({})
        db["hexa_trial_stage_comments"].delete_many({})

        cust_a_party = {"party_type": "customer", "party_id": CUSTOMER_A_ID, "name": "Công ty TNHH Lục Giác (HEXA)"}
        tt_company_party = {"party_type": "company", "party_id": "TT-COMPANY", "name": "Công ty Trường Thành Logistics"}
        internal_partner_party = {
            "party_type": "partner",
            "party_id": "PARTNER-FOSHAN",
            "name": f"Foshan Hexa Furniture Factory ({SENTINEL_TT_PRIVATE_SUPPLIER})",
        }

        db[OBLIGATIONS].insert_many(
            [
                {
                    "id": "OBL-LG01-SVC-01",
                    "record_type": "obligation",
                    "from_party": cust_a_party,
                    "from_party_key": f"customer:{CUSTOMER_A_ID}",
                    "to_party": tt_company_party,
                    "to_party_key": "company:TT-COMPANY",
                    "shipment_ids": [SHIPMENT_A_ID],
                    "shipment_id": SHIPMENT_A_ID,
                    "purpose": "LOGISTICS_SERVICE",
                    "amount": 57240000.0,
                    "currency": "VND",
                    "status": "active",
                    "review_status": CONFIRMED,
                    "confirmed_by": TT_FINANCE_TRIAL_USERNAME,
                    "confirmed_by_role": "support",
                    "confirmed_by_finance_write": True,
                    "created_at": "2026-10-18T10:00:00Z",
                    "updated_at": "2026-10-20T15:00:00Z",
                    "note": "Nghĩa vụ phải thu cước & thủ tục đường bộ lô ROAD-LG-001 đã đối soát",
                },
                # Internal partner payable (used by shipment_partner_position — MUST NEVER leak to customer portal!)
                {
                    "id": "OBL-LG01-PARTNER-INTERNAL",
                    "record_type": "obligation",
                    "from_party": tt_company_party,
                    "from_party_key": "company:TT-COMPANY",
                    "to_party": internal_partner_party,
                    "to_party_key": "partner:PARTNER-FOSHAN",
                    "shipment_ids": [SHIPMENT_A_ID],
                    "shipment_id": SHIPMENT_A_ID,
                    "purpose": "SUPPLIER_PAYABLE",
                    "amount": 42000000.0,
                    "currency": "VND",
                    "status": "active",
                    "review_status": CONFIRMED,
                    "confirmed_by": TT_FINANCE_TRIAL_USERNAME,
                    "confirmed_by_role": "support",
                    "confirmed_by_finance_write": True,
                    "created_at": "2026-10-18T10:00:00Z",
                    "note": f"Công nợ nhà cung cấp nội bộ TT ({SENTINEL_TT_INTERNAL_COST})",
                },
                # Entrusted import goods advance for ROAD-LG-002 (separate from service receivable!)
                {
                    "id": "OBL-LG02-GOODS-ADV",
                    "record_type": "obligation",
                    "from_party": cust_a_party,
                    "from_party_key": f"customer:{CUSTOMER_A_ID}",
                    "to_party": tt_company_party,
                    "to_party_key": "company:TT-COMPANY",
                    "shipment_ids": [SHIPMENT_A2_ID],
                    "shipment_id": SHIPMENT_A2_ID,
                    "purpose": "ENTRUSTED_GOODS_ADVANCE",
                    "amount": 200000000.0,
                    "currency": "VND",
                    "status": "active",
                    "review_status": CONFIRMED,
                    "confirmed_by": TT_FINANCE_TRIAL_USERNAME,
                    "confirmed_by_role": "support",
                    "confirmed_by_finance_write": True,
                    "created_at": "2026-10-19T11:30:00Z",
                    "updated_at": "2026-10-21T10:00:00Z",
                    "note": "Tiền hàng cần ứng trước theo hợp đồng ủy thác nhập khẩu HDUT-LG-2026-02",
                },
            ]
        )

        db[TRANSACTIONS].insert_many(
            [
                {
                    "id": "TXN-LG01-PAY-01",
                    "record_type": "transaction",
                    "transaction_kind": "customer_payment",
                    "source_party": cust_a_party,
                    "source_party_key": f"customer:{CUSTOMER_A_ID}",
                    "holder_party": tt_company_party,
                    "holder_party_key": "company:TT-COMPANY",
                    "shipment_ids": [SHIPMENT_A_ID],
                    "shipment_id": SHIPMENT_A_ID,
                    "amount": 30000000.0,
                    "currency": "VND",
                    "occurred_at": "2026-10-20",
                    "classification_status": CONFIRMED,
                    "restriction": {"status": "NONE"},
                    "status": "active",
                    "confirmed_by": TT_FINANCE_TRIAL_USERNAME,
                    "confirmed_by_role": "support",
                    "confirmed_by_finance_write": True,
                    "created_at": "2026-10-20T15:00:00Z",
                    "note": "Lục Giác tạm ứng đợt 1 trước ngày giao hàng",
                },
                {
                    "id": "TXN-LG02-GOODS-01",
                    "record_type": "transaction",
                    "transaction_kind": "received_on_behalf",
                    "source_party": cust_a_party,
                    "source_party_key": f"customer:{CUSTOMER_A_ID}",
                    "holder_party": tt_company_party,
                    "holder_party_key": "company:TT-COMPANY",
                    "shipment_ids": [SHIPMENT_A2_ID],
                    "shipment_id": SHIPMENT_A2_ID,
                    "amount": 150000000.0,
                    "currency": "VND",
                    "occurred_at": "2026-10-21",
                    "classification_status": CONFIRMED,
                    "restriction": {"status": "NONE"},
                    "status": "active",
                    "confirmed_by": TT_FINANCE_TRIAL_USERNAME,
                    "confirmed_by_role": "support",
                    "confirmed_by_finance_write": True,
                    "created_at": "2026-10-21T10:00:00Z",
                    "note": "Lục Giác chuyển ứng trước tiền hàng ủy thác đợt 1",
                },
            ]
        )

        db[ALLOCATIONS].insert_many(
            [
                {
                    "id": "ALC-LG01-01",
                    "record_type": "allocation",
                    "transaction_id": "TXN-LG01-PAY-01",
                    "obligation_id": "OBL-LG01-SVC-01",
                    "shipment_ids": [SHIPMENT_A_ID],
                    "shipment_id": SHIPMENT_A_ID,
                    "amount": 30000000.0,
                    "currency": "VND",
                    "status": "active",
                    "confirmed_by": TT_FINANCE_TRIAL_USERNAME,
                    "confirmed_by_role": "support",
                    "confirmed_by_finance_write": True,
                    "created_at": "2026-10-20T15:00:00Z",
                },
                {
                    "id": "ALC-LG02-GOODS-01",
                    "record_type": "allocation",
                    "transaction_id": "TXN-LG02-GOODS-01",
                    "obligation_id": "OBL-LG02-GOODS-ADV",
                    "shipment_ids": [SHIPMENT_A2_ID],
                    "shipment_id": SHIPMENT_A2_ID,
                    "amount": 150000000.0,
                    "currency": "VND",
                    "status": "active",
                    "confirmed_by": TT_FINANCE_TRIAL_USERNAME,
                    "confirmed_by_role": "support",
                    "confirmed_by_finance_write": True,
                    "created_at": "2026-10-21T10:00:00Z",
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
        raw_pass = str(passcode or "").strip()
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
        raw_pass = str(passcode or "").strip()
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
        """Verify caller holds an authenticated TT staff session with ``operations_write`` or ``finance_write``."""
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
            and ("*" in perms or "operations_write" in perms or "finance_write" in perms)
        ):
            raise PublicationDenied()
        return copy.deepcopy(principal)

    def _require_authorized_tt_finance_staff(self, session_token: str | None) -> dict[str, Any]:
        """Verify caller holds an authenticated TT staff session with ``finance_write`` permission.

        ``operations_write`` does NOT substitute for ``finance_write``.
        """
        from core import auth as core_auth

        principal = self._require_authorized_tt_staff(session_token)
        role = str(principal.get("role") or "").strip().lower()
        perms = core_auth._role_permissions(role)
        if not ("*" in perms or "finance_write" in perms):
            raise PublicationDenied()
        return principal

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

        stage_comments = list(
            db["hexa_trial_stage_comments"].find(
                {"shipment_id": sid, "customer_id": cust_id},
                {"_id": 0},
            )
        )
        customer_submitted_documents = [
            {
                "id": str(doc.get("id") or ""),
                "version": str(doc.get("version") or ""),
                "stage_id": str(doc.get("stage_id") or ""),
                "kind": str(doc.get("kind") or ""),
                "public_title": str(doc.get("public_title") or ""),
                "file_name": str(doc.get("file_name") or ""),
                "verified": bool(doc.get("verified")),
                "verification_status": str(doc.get("verification_status") or ""),
                "revoked": bool(doc.get("revoked", False)),
            }
            for doc in raw_docs
            if doc.get("source_side") == "CUSTOMER"
        ]
        financial_obligations = list(
            db["financial_obligations"].find(
                {"shipment_id": sid, "is_deleted": False},
                {"_id": 0},
            )
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
            "stage_comments": stage_comments,
            "customer_submitted_documents": customer_submitted_documents,
            "financial_obligations": financial_obligations,
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

    @staticmethod
    def _financial_rows_for_shipment(db: Any, collection: str, shipment_id: str) -> list[dict[str, Any]]:
        sid = str(shipment_id or "").strip()
        rows: list[dict[str, Any]] = []
        for raw in db[collection].find({}, {"_id": 0}):
            row = copy.deepcopy(dict(raw))
            row.pop("_id", None)
            row_shipments = row.get("shipment_ids") or []
            if isinstance(row_shipments, str):
                row_shipments = [row_shipments]
            linked = {str(value or "").strip() for value in row_shipments if str(value or "").strip()}
            if str(row.get("shipment_id") or "").strip() == sid or sid in linked:
                rows.append(row)
        from core import database as core_db

        return sorted(
            rows,
            key=lambda row: (str(row.get("id") or ""), core_db._financial_fingerprint(row)),
        )

    @classmethod
    def _finance_source_fingerprint(
        cls,
        db: Any,
        *,
        shipment_id: str,
        customer_id: str,
    ) -> str:
        from core import database as core_db
        from core.financial_ledger import ALLOCATIONS, OBLIGATIONS, TRANSACTIONS

        source = {
            collection: cls._financial_rows_for_shipment(db, collection, shipment_id)
            for collection in (OBLIGATIONS, TRANSACTIONS, ALLOCATIONS)
        }
        return core_db._financial_fingerprint(
            {
                "shipment_id": str(shipment_id or "").strip(),
                "customer_id": str(customer_id or "").strip(),
                "records": source,
            }
        )

    def publish_shipment_for_customer(
        self,
        *,
        session_token: str | None,
        shipment_id: str,
        event_versions: Mapping[str, Any] | None = None,
        document_versions: Mapping[str, Any] | None = None,
        quote: Mapping[str, Any] | None = None,
        approve_finance: bool = False,
    ) -> dict[str, Any]:
        """Publish selected verified items; financial disclosure needs a separate finance_write approval."""
        from core import database as core_db

        self.ensure_seeded()
        finance_approval_requested = approve_finance is True
        try:
            principal = (
                self._require_authorized_tt_finance_staff(session_token)
                if finance_approval_requested
                else self._require_authorized_tt_staff(session_token)
            )
        except PublicationDenied:
            self._record_audit(
                action="PUBLISH_FINANCE" if finance_approval_requested else "PUBLISH_SHIPMENT",
                principal=self.resolve_principal(session_token),
                shipment_id=str(shipment_id or ""),
                allowed=False,
                detail=(
                    "denied: caller lacks finance_write permission to approve financial publication"
                    if finance_approval_requested
                    else "unauthorized caller attempted publish"
                ),
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
        current_finance_fingerprint = self._finance_source_fingerprint(
            db,
            shipment_id=sid,
            customer_id=cust_id,
        )
        prior_finance_fingerprint = str(existing.get("finance_source_fingerprint") or "")
        finance_published = finance_approval_requested or (
            existing.get("state") == "PUBLISHED"
            and existing.get("finance_published") is True
            and bool(prior_finance_fingerprint)
            and prior_finance_fingerprint == current_finance_fingerprint
        )
        finance_source_fingerprint = (
            current_finance_fingerprint if finance_approval_requested else prior_finance_fingerprint
        )
        finance_approved_by = (
            approver if finance_approval_requested else str(existing.get("finance_approved_by") or "")
        )
        finance_approved_at = (
            now_iso if finance_approval_requested else str(existing.get("finance_approved_at") or "")
        )
        history.append(
            {
                "action": "PUBLISHED",
                "actor": approver,
                "role": str(principal.get("role") or ""),
                "at": now_iso,
                "event_versions": dict(clean_events),
                "document_versions": dict(clean_docs),
                "quote": dict(clean_quote) if clean_quote else None,
                "finance_published": finance_published,
                "finance_source_fingerprint": finance_source_fingerprint,
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
            "finance_published": finance_published,
            "finance_source_fingerprint": finance_source_fingerprint,
            "finance_approved_by": finance_approved_by,
            "finance_approved_at": finance_approved_at,
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
                f"docs={list(clean_docs.keys())} quote={clean_quote} "
                f"finance_published={finance_published}"
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
        comment_ids: Sequence[str] | None = None,
        revoke_quote: bool = False,
        revoke_finance: bool = False,
    ) -> dict[str, Any]:
        """Revoke either specific published documents/events/comments/quote/finance or the entire shipment publication."""
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
        cmt_list = [str(x).strip() for x in (comment_ids or []) if str(x).strip()]
        is_partial = bool(doc_list or ev_list or cmt_list or revoke_quote or revoke_finance)

        for d_id in doc_list:
            db["hexa_trial_documents"].update_many(
                {"shipment_id": sid, "customer_id": cust_id, "id": d_id},
                {"$set": {"revoked": True, "revoked_by": actor, "revoked_at": now_iso}},
            )
        for c_id in cmt_list:
            db["hexa_trial_stage_comments"].update_many(
                {"shipment_id": sid, "customer_id": cust_id, "id": c_id},
                {"$set": {"revoked": True, "revoked_by": actor, "revoked_at": now_iso}},
            )

        if is_partial and existing.get("state") == "PUBLISHED":
            cur_events = dict(existing.get("event_versions") or {})
            cur_docs = dict(existing.get("document_versions") or {})
            cur_quote = copy.deepcopy(existing.get("quote"))
            approved_finance_fingerprint = str(existing.get("finance_source_fingerprint") or "")
            current_finance_fingerprint = self._finance_source_fingerprint(
                db,
                shipment_id=sid,
                customer_id=cust_id,
            )
            cur_fin_pub = (
                existing.get("finance_published") is True
                and bool(approved_finance_fingerprint)
                and approved_finance_fingerprint == current_finance_fingerprint
            )
            for d_id in doc_list:
                cur_docs.pop(d_id, None)
            for e_id in ev_list:
                cur_events.pop(e_id, None)
            if revoke_quote:
                cur_quote = None
            if revoke_finance:
                cur_fin_pub = False
            next_state = "PUBLISHED" if (cur_events or cur_docs or cur_quote) else "REVOKED"
            history.append(
                {
                    "action": "REVOKED_ITEMS",
                    "actor": actor,
                    "role": str(principal.get("role") or ""),
                    "at": now_iso,
                    "revoked_documents": doc_list,
                    "revoked_events": ev_list,
                    "revoked_comments": cmt_list,
                    "revoked_quote": bool(revoke_quote),
                    "revoked_finance": bool(revoke_finance),
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
                "finance_published": cur_fin_pub,
                "finance_source_fingerprint": approved_finance_fingerprint,
                "finance_approved_by": str(existing.get("finance_approved_by") or ""),
                "finance_approved_at": str(existing.get("finance_approved_at") or ""),
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
                "finance_published": False,
                "finance_source_fingerprint": str(existing.get("finance_source_fingerprint") or ""),
                "finance_approved_by": str(existing.get("finance_approved_by") or ""),
                "finance_approved_at": str(existing.get("finance_approved_at") or ""),
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
            detail=f"revoked_by={actor} state={pub_doc['state']} docs={doc_list or 'ALL'} comments={cmt_list}",
        )
        return {"ok": True, "publication": pub_doc}

    def submit_customer_stage_collaboration(
        self,
        *,
        session_token: str | None,
        shipment_id: str,
        stage_id: str,
        comment: str = "",
        file_name: str = "",
        mime: str = "",
        file_base64: str = "",
    ) -> dict[str, Any]:
        """Customer posts a comment and/or uploads a stage attachment on their own PUBLISHED shipment.

        Security & business rules:
        - Caller must be an authenticated customer owning ``shipment_id`` and the shipment must be PUBLISHED.
        - Uploaded file is validated & stored via ``core.shipment_attachments.upload_attachment`` in GridFS.
        - Uploaded file is recorded with ``verified=False`` and ``verification_status='SUBMITTED_UNVERIFIED'``
          ('Hồ sơ khách đã nộp — Chờ TT xác minh'): it NEVER auto-completes a stage and NEVER changes
          ``total_paid`` or ``remaining_balance``.
        """
        import base64
        from core import database as core_db
        from core import shipment_attachments as core_att

        self.ensure_seeded()
        principal = self.resolve_principal(session_token)
        cust_id = str(principal.get("customer_id") or "").strip()
        sid = str(shipment_id or "").strip()
        st_id = str(stage_id or "").strip()

        # Verify customer owns shipment and shipment is PUBLISHED (raises PublicationDenied otherwise)
        self.read_customer_publication(session_token=session_token, shipment_id=sid)

        if st_id not in CUSTOMER_JOURNEY_STAGE_IDS:
            raise PublicationDenied()

        db = core_db.get_db()
        if db is None:
            raise PublicationDenied()

        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        clean_comment = str(comment or "").strip()
        clean_fname = str(file_name or "").strip()
        clean_b64 = str(file_base64 or "").strip()

        if not clean_comment and not (clean_fname and clean_b64):
            raise PublicationDenied()

        created_comment: dict[str, Any] | None = None
        if clean_comment:
            cmt_id = f"CMT-{secrets.token_hex(4).upper()}"
            created_comment = {
                "id": cmt_id,
                "shipment_id": sid,
                "customer_id": cust_id,
                "stage_id": st_id,
                "author_side": "CUSTOMER",
                "author_display": str(principal.get("display_name") or cust_id),
                "comment": clean_comment[:2000],
                "visibility": "CUSTOMER",
                "published": True,
                "revoked": False,
                "created_at": now_iso,
            }
            db["hexa_trial_stage_comments"].insert_one(dict(created_comment))

        created_doc: dict[str, Any] | None = None
        if clean_fname and clean_b64:
            try:
                raw_bytes = base64.b64decode(clean_b64, validate=True)
            except Exception as exc:  # noqa: BLE001
                raise PublicationDenied() from exc

            upload_res = core_att.upload_attachment(
                shipment_id=sid,
                category="other",
                file_name=clean_fname,
                mime=str(mime or "application/pdf"),
                data=raw_bytes,
                uploaded_by=str(principal.get("username") or cust_id),
                storage_backend="gridfs",
            )
            if not upload_res.get("ok"):
                raise PublicationDenied()

            att_rec = dict(upload_res["record"])
            doc_id = f"SUBDOC-{secrets.token_hex(4).upper()}"
            created_doc = {
                "id": doc_id,
                "version": "v1",
                "customer_id": cust_id,
                "shipment_id": sid,
                "stage_id": st_id,
                "kind": "PAYMENT_REQUEST" if st_id == "finance-reconciliation" else "CUSTOMS",
                "status": "AVAILABLE",
                "visibility": "CUSTOMER",
                "source_side": "CUSTOMER",
                "verified": False,
                "verification_status": "SUBMITTED_UNVERIFIED",
                "verification_label": "Hồ sơ khách đã nộp — Chờ TT xác minh",
                "revoked": False,
                "public_title": f"[Khách nộp] {clean_fname}",
                "file_name": clean_fname,
                "attachment_id": att_rec["id"],
                "attachment_shipment_id": sid,
                "uploaded_at": now_iso,
            }
            db["hexa_trial_documents"].insert_one(dict(created_doc))

        self._record_audit(
            action="CUSTOMER_STAGE_SUBMISSION",
            principal=principal,
            shipment_id=sid,
            allowed=True,
            detail=f"stage={st_id} comment={bool(created_comment)} doc={(created_doc or {}).get('id')}",
        )
        return {
            "ok": True,
            "submission": {
                "shipment_id": sid,
                "stage_id": st_id,
                "comment": created_comment,
                "document": created_doc,
            },
        }

    def post_tt_stage_comment(
        self,
        *,
        session_token: str | None,
        shipment_id: str,
        stage_id: str,
        comment: str,
        visibility: str = "TT",
    ) -> dict[str, Any]:
        """Authorized TT staff posts a stage comment (internal 'TT' note or customer-published 'CUSTOMER' reply)."""
        from core import database as core_db

        self.ensure_seeded()
        principal = self._require_authorized_tt_staff(session_token)
        db = core_db.get_db()
        if db is None:
            raise PublicationDenied()

        sid = str(shipment_id or "").strip()
        st_id = str(stage_id or "").strip()
        shipment = self._load_adapted_shipment(db, sid)
        if not shipment or st_id not in CUSTOMER_JOURNEY_STAGE_IDS:
            raise PublicationDenied()
        cust_id = shipment["customer_id"]
        clean_comment = str(comment or "").strip()
        if not clean_comment:
            raise PublicationDenied()

        vis = "CUSTOMER" if str(visibility or "TT").strip().upper() == "CUSTOMER" else "TT"
        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        cmt_doc = {
            "id": f"CMT-TT-{secrets.token_hex(4).upper()}",
            "shipment_id": sid,
            "customer_id": cust_id,
            "stage_id": st_id,
            "author_side": "TT",
            "author_display": f"{principal.get('display_name') or principal.get('username')} (Trường Thành)",
            "comment": clean_comment[:2000],
            "visibility": vis,
            "published": vis == "CUSTOMER",
            "revoked": False,
            "created_at": now_iso,
            "created_by": str(principal.get("username") or ""),
        }
        db["hexa_trial_stage_comments"].insert_one(dict(cmt_doc))
        self._record_audit(
            action="TT_STAGE_COMMENT",
            principal=principal,
            shipment_id=sid,
            allowed=True,
            detail=f"stage={st_id} visibility={vis} id={cmt_doc['id']}",
        )
        return {"ok": True, "comment": cmt_doc}

    def confirm_tt_shipment_finance(
        self,
        *,
        session_token: str | None,
        shipment_id: str,
        transaction_id: str,
        obligation_id: str,
        amount: Any,
        currency: str = "VND",
        occurred_at: str = "",
        note: str = "",
        verified_document_id: str = "",
    ) -> dict[str, Any]:
        """Record a shipment payment and allocation through the canonical ledger.

        ``finance_write`` is checked at the trial boundary and again by the
        Financial Ledger. Transaction and allocation IDs are insert-only and
        share a stable request identity. The HEXA preview uses compensation for
        mongomock's no-op session; that is explicitly sandbox-only and is not a
        production transaction guarantee.
        """
        from core import database as core_db
        from core.financial_ledger import (
            ALLOCATIONS,
            CONFIRMED,
            OBLIGATIONS,
            TRANSACTIONS,
            allocate_transaction,
            party_key,
        )

        self.ensure_seeded()
        try:
            principal = self._require_authorized_tt_finance_staff(session_token)
        except PublicationDenied:
            self._record_audit(
                action="TT_CONFIRM_FINANCE",
                principal=self.resolve_principal(session_token),
                shipment_id=str(shipment_id or ""),
                allowed=False,
                detail="denied: caller lacks finance_write permission",
            )
            raise

        db = core_db.get_db()
        if db is None:
            raise PublicationDenied()

        sid = str(shipment_id or "").strip()
        shipment = self._load_adapted_shipment(db, sid)
        if not shipment:
            raise PublicationDenied()
        cust_id = str(shipment.get("customer_id") or "").strip()
        obl_id = str(obligation_id or "").strip()
        txn_id = str(transaction_id or "").strip()
        if not obl_id or not txn_id:
            raise PublicationDenied()

        obligation = db[OBLIGATIONS].find_one(
            {"id": obl_id, "shipment_id": sid},
            {"_id": 0},
        )
        if not obligation:
            raise PublicationDenied()
        obligation_shipments = obligation.get("shipment_ids") or []
        if isinstance(obligation_shipments, str):
            obligation_shipments = [obligation_shipments]
        linked_shipments = {str(value or "").strip() for value in obligation_shipments if str(value or "").strip()}
        if str(obligation.get("shipment_id") or "").strip():
            linked_shipments.add(str(obligation["shipment_id"]).strip())
        if linked_shipments != {sid}:
            raise PublicationDenied()

        customer_party = {"party_type": "customer", "party_id": cust_id, "name": cust_id}
        tt_party = {
            "party_type": "company",
            "party_id": "TT-COMPANY",
            "name": "Công ty Trường Thành Logistics",
        }
        if party_key(obligation.get("from_party")) != party_key(customer_party):
            raise PublicationDenied()
        if party_key(obligation.get("to_party")) != party_key(tt_party):
            raise PublicationDenied()

        verified_doc_id = str(verified_document_id or "").strip()
        verified_doc = None
        if verified_doc_id:
            verified_doc = db["hexa_trial_documents"].find_one(
                {"shipment_id": sid, "customer_id": cust_id, "id": verified_doc_id},
                {"_id": 0},
            )
            if not verified_doc:
                raise PublicationDenied()

        pay_date = str(occurred_at or "").strip()
        curr = str(currency or "VND").strip().upper()
        evidence_refs = (
            [{"kind": "hexa_trial_document", "reference": verified_doc_id}]
            if verified_doc_id
            else []
        )
        txn_doc: dict[str, Any] = {
            "id": txn_id,
            "record_type": "transaction",
            "transaction_kind": "customer_payment",
            "source_party": customer_party,
            "holder_party": tt_party,
            "shipment_ids": [sid],
            "shipment_id": sid,
            "amount": amount,
            "currency": curr,
            "classification_status": CONFIRMED,
            "restriction": {"status": "NONE"},
            "note": str(note or "Khoản thanh toán đã được Kế toán TT đối soát"),
            "evidence_refs": evidence_refs,
        }
        if pay_date:
            txn_doc["occurred_at"] = pay_date

        request_id = f"hexa-trial-finance:{sid}:{cust_id}:{txn_id}"
        with self._finance_confirmation_lock:
            ok, ledger_result, message = allocate_transaction(
                txn_id,
                obl_id,
                amount,
                request_id,
                currency=curr,
                shipment_ids=[sid],
                evidence_refs=evidence_refs,
                source_refs=[{"kind": "hexa_trial", "shipment_id": sid, "customer_id": cust_id}],
                actor=str(principal["username"]),
                transaction_document=txn_doc,
                sandbox_compensate=True,
            )
        if not ok:
            self._record_audit(
                action="TT_CONFIRM_FINANCE",
                principal=principal,
                shipment_id=sid,
                allowed=False,
                detail=f"financial ledger rejected txn={txn_id} obl={obl_id}: {message}",
            )
            raise PublicationDenied()

        saved_transaction = ledger_result.get("transaction")
        saved_allocation = ledger_result.get("allocation")
        if not isinstance(saved_transaction, Mapping):
            saved_transaction = db[TRANSACTIONS].find_one({"id": txn_id}, {"_id": 0}) or {}
        if not isinstance(saved_allocation, Mapping):
            saved_allocation = db[ALLOCATIONS].find_one(
                {"id": str(ledger_result.get("allocation_id") or ledger_result.get("id") or "")},
                {"_id": 0},
            ) or {}

        if verified_doc_id and verified_doc is not None:
            db["hexa_trial_documents"].update_one(
                {"shipment_id": sid, "customer_id": cust_id, "id": verified_doc_id},
                {
                    "$set": {
                        "verified": True,
                        "verification_status": "VERIFIED_BY_FINANCE",
                        "verification_label": "Đã được Kế toán TT đối soát & xác nhận",
                    }
                },
            )

        publication = db["hexa_trial_publications"].find_one(
            {"shipment_id": sid, "customer_id": cust_id},
            {"_id": 0},
        )
        if publication:
            updates: dict[str, Any] = {}
            if verified_doc_id and publication.get("state") == "PUBLISHED":
                document_versions = dict(publication.get("document_versions") or {})
                document_versions[verified_doc_id] = str((verified_doc or {}).get("version") or "v1")
                updates["document_versions"] = document_versions
            current_fingerprint = self._finance_source_fingerprint(
                db,
                shipment_id=sid,
                customer_id=cust_id,
            )
            approved_fingerprint = str(publication.get("finance_source_fingerprint") or "")
            if publication.get("finance_published") is True and (
                not approved_fingerprint or approved_fingerprint != current_fingerprint
            ):
                updates["finance_published"] = False
            if updates:
                db["hexa_trial_publications"].update_one(
                    {"shipment_id": sid, "customer_id": cust_id},
                    {"$set": updates},
                )

        confirmed_amount = saved_transaction.get("amount", amount)

        def _json_safe(value: Any) -> Any:
            if isinstance(value, datetime):
                aware = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
                return aware.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            if isinstance(value, Mapping):
                return {str(key): _json_safe(item) for key, item in value.items()}
            if isinstance(value, (list, tuple)):
                return [_json_safe(item) for item in value]
            return value

        self._record_audit(
            action="TT_CONFIRM_FINANCE",
            principal=principal,
            shipment_id=sid,
            allowed=True,
            detail=f"confirmed_by={principal['username']} txn={txn_id} obl={obl_id} amount={confirmed_amount} {curr}",
        )
        return {
            "ok": True,
            "transaction": _json_safe(saved_transaction),
            "allocation": _json_safe(saved_allocation),
        }

    def _project_customer_finance_and_plan(
        self,
        db: Any,
        *,
        shipment_id: str,
        customer_id: str,
        link: Mapping[str, Any],
        pub_payload: Mapping[str, Any],
        publication: Mapping[str, Any],
    ) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
        """Derive Node 00 (plan_detail), Node 06 (finance_detail), and Dashboard (debt_summary)
        strictly from customer-scoped canonical financial obligations & allocations.

        Never uses ``shipment_partner_position()`` (which projects partner payables)
        and never substitutes ``0`` or ``quote.selling_total_vnd`` when confirmed
        service receivable obligations are absent.
        """
        from core.financial_ledger import (
            ALLOCATIONS,
            CONFIRMED,
            OBLIGATIONS,
            TRANSACTIONS,
            derive_obligation_position,
            party_key,
        )

        cust_party_key = f"customer:{customer_id.strip().upper()}"
        tt_party_key = "company:TT-COMPANY"

        raw_obls = self._financial_rows_for_shipment(db, OBLIGATIONS, shipment_id)
        raw_txns = self._financial_rows_for_shipment(db, TRANSACTIONS, shipment_id)
        raw_allocs = self._financial_rows_for_shipment(db, ALLOCATIONS, shipment_id)
        current_finance_fingerprint = self._finance_source_fingerprint(
            db,
            shipment_id=shipment_id,
            customer_id=customer_id,
        )
        finance_published = (
            publication.get("state") == "PUBLISHED"
            and publication.get("finance_published") is True
            and bool(publication.get("finance_source_fingerprint"))
            and publication.get("finance_source_fingerprint") == current_finance_fingerprint
        )

        confirmed_allocs = [
            a
            for a in raw_allocs
            if a.get("status") == "active" and a.get("confirmed_by_finance_write") is True
        ]
        txn_by_id = {
            str(t.get("id") or ""): t
            for t in raw_txns
            if t.get("status") == "active" and t.get("confirmed_by_finance_write") is True
        }

        def _derive_for_purpose(purpose: str) -> dict[str, Any]:
            if not finance_published:
                return {
                    "status": "UNKNOWN",
                    "status_label": "UNKNOWN / Chưa đối soát",
                    "currency": None,
                    "total_payable": None,
                    "total_paid": None,
                    "remaining_balance": None,
                    "updated_at": None,
                }
            matched = [
                o
                for o in raw_obls
                if o.get("status") == "active"
                and o.get("review_status") == CONFIRMED
                and o.get("confirmed_by_finance_write") is True
                and party_key(o.get("from_party")) == cust_party_key
                and party_key(o.get("to_party")) == tt_party_key
                and str(o.get("purpose") or "") == purpose
            ]
            if not matched:
                return {
                    "status": "UNKNOWN",
                    "status_label": "UNKNOWN / Chưa đối soát",
                    "currency": None,
                    "total_payable": None,
                    "total_paid": None,
                    "remaining_balance": None,
                    "updated_at": None,
                }
            positions = [derive_obligation_position(o, confirmed_allocs) for o in matched]
            currencies = {str(p.get("currency") or "").upper() for p in positions if p.get("currency")}
            if len(currencies) != 1 or any(p.get("status") != CONFIRMED for p in positions):
                return {
                    "status": "UNKNOWN",
                    "status_label": "UNKNOWN / Chưa đối soát (khác loại tiền hoặc cần rà soát)",
                    "currency": None,
                    "total_payable": None,
                    "total_paid": None,
                    "remaining_balance": None,
                    "updated_at": None,
                }
            curr = next(iter(currencies))
            payable = sum(float(p["amount"]) for p in positions)
            paid = sum(float(p["allocated"]) for p in positions)
            remaining = sum(float(p["outstanding"]) for p in positions)

            alloc_ids = [aid for p in positions for aid in (p.get("allocation_ids") or [])]
            pay_dates: list[str] = []
            for a in confirmed_allocs:
                if str(a.get("id") or "") in alloc_ids:
                    t = txn_by_id.get(str(a.get("transaction_id") or ""))
                    if t and str(t.get("occurred_at") or "").strip():
                        pay_dates.append(str(t["occurred_at"]).strip())
            latest_date = max(pay_dates) if pay_dates else str(matched[0].get("updated_at") or "")[:10]
            status_label = (
                "Đã thanh toán khoản công bố — Chờ quyết toán"
                if remaining <= 0
                else "Đã đối soát — Còn công nợ"
            )
            return {
                "status": "CONFIRMED",
                "status_label": status_label,
                "currency": curr,
                "total_payable": payable,
                "total_paid": paid,
                "remaining_balance": remaining,
                "updated_at": latest_date or None,
            }

        debt_summary = _derive_for_purpose("LOGISTICS_SERVICE")

        quote = pub_payload.get("quote")
        entrusted_applicable = bool(link.get("entrusted_import_applicable", False))
        if entrusted_applicable:
            goods_pos = _derive_for_purpose("ENTRUSTED_GOODS_ADVANCE")
            req_amt = goods_pos["total_payable"]
            rec_amt = goods_pos["total_paid"]
            shortfall = goods_pos["remaining_balance"]
            entrusted_info = {
                "applicable": True,
                "currency": goods_pos["currency"] or "VND",
                "goods_advance_required": req_amt,
                "goods_advance_received": rec_amt,
                "goods_advance_shortfall": shortfall,
                "status_label": (
                    "Đã nhận đủ tiền hàng ứng trước"
                    if (req_amt is not None and shortfall is not None and shortfall <= 0)
                    else (
                        "Còn thiếu tiền hàng ứng trước"
                        if (req_amt is not None and shortfall is not None and shortfall > 0)
                        else "Chưa xác nhận"
                    )
                ),
            }
        else:
            entrusted_info = {
                "applicable": False,
                "currency": None,
                "goods_advance_required": None,
                "goods_advance_received": None,
                "goods_advance_shortfall": None,
                "status_label": "Không áp dụng (Khách hàng sử dụng dịch vụ thông thường)",
            }

        plan_verified = bool(link.get("plan_verified", False)) and (quote is not None)
        if entrusted_applicable:
            plan_completed = bool(
                plan_verified
                and entrusted_info["goods_advance_shortfall"] is not None
                and entrusted_info["goods_advance_shortfall"] <= 0
            )
        else:
            plan_completed = plan_verified

        plan_detail = {
            "quote_id": str((quote or {}).get("id") or link.get("quote_id") or ""),
            "quote_no": str(link.get("quote_no") or (quote or {}).get("id") or "Chưa xác nhận"),
            "quote_selling_total_vnd": (quote or {}).get("selling_total_vnd") if quote else None,
            "quote_confirmation_status": (
                str(link.get("quote_confirmation_status") or "ĐÃ XÁC NHẬN")
                if quote
                else "Chưa xác nhận"
            ),
            "contract_no": str(link.get("contract_no") or "Chưa xác nhận"),
            "contract_status": str(link.get("contract_status") or "Chưa xác nhận"),
            "payment_terms": str(link.get("payment_terms") or "Chưa xác nhận"),
            "entrusted_import": entrusted_info,
            "verified": plan_completed,
            "verified_at": str(link.get("plan_verified_at") or "") if plan_verified else "",
        }

        finance_detail = {
            **debt_summary,
            "reconciliation_status_label": debt_summary["status_label"],
            # The trial finance source has no canonical final-settlement confirmation.
            # A zero balance is payment evidence, not proof that the debt is closed.
            "completed": False,
        }
        return debt_summary, plan_detail, finance_detail

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

            publication = (
                db["hexa_trial_publications"].find_one(
                    {"shipment_id": sid, "customer_id": cust_id},
                    {"_id": 0},
                )
                or {}
            )
            debt_summary, plan_detail, finance_detail = self._project_customer_finance_and_plan(
                db,
                shipment_id=sid,
                customer_id=cust_id,
                link=link,
                pub_payload=pub_payload,
                publication=publication,
            )

            # Query customer-visible stage comments (NEVER include internal TT comments where visibility != 'CUSTOMER')
            raw_comments = list(
                db["hexa_trial_stage_comments"].find(
                    {
                        "shipment_id": sid,
                        "customer_id": cust_id,
                        "visibility": "CUSTOMER",
                        "published": True,
                        "revoked": {"$ne": True},
                    },
                    {"_id": 0},
                )
            )
            comments_by_stage: dict[str, list[dict[str, Any]]] = {}
            for cmt in raw_comments:
                st_c = str(cmt.get("stage_id") or "").strip()
                if st_c:
                    comments_by_stage.setdefault(st_c, []).append(
                        {
                            "id": str(cmt.get("id") or ""),
                            "stage_id": st_c,
                            "author_side": str(cmt.get("author_side") or ""),
                            "author_display": str(cmt.get("author_display") or ""),
                            "comment": str(cmt.get("comment") or ""),
                            "created_at": str(cmt.get("created_at") or ""),
                        }
                    )

            docs = list(pub_payload.get("documents") or [])
            quote = pub_payload.get("quote")

            # Also include customer-submitted stage documents (verified=False, SUBMITTED_UNVERIFIED) that belong to this customer and are not revoked
            raw_cust_sub_docs = list(
                db["hexa_trial_documents"].find(
                    {
                        "shipment_id": sid,
                        "customer_id": cust_id,
                        "source_side": "CUSTOMER",
                        "revoked": {"$ne": True},
                    },
                    {"_id": 0},
                )
            )
            pub_doc_ids = {str(d.get("id") or "") for d in docs}
            stage_docs_by_stage: dict[str, list[dict[str, Any]]] = {}
            for d in docs:
                doc_meta = (
                    db["hexa_trial_documents"].find_one(
                        {"shipment_id": sid, "customer_id": cust_id, "id": d.get("id")},
                        {"_id": 0},
                    )
                    or {}
                )
                if doc_meta.get("revoked") is True:
                    continue
                st_d = str(doc_meta.get("stage_id") or "pickup").strip()
                enriched_doc = {
                    **d,
                    "stage_id": st_d,
                    "source_side": str(doc_meta.get("source_side") or "TT"),
                    "verified": True,
                    "verification_status": str(doc_meta.get("verification_status") or "VERIFIED_BY_TT"),
                    "verification_label": str(doc_meta.get("verification_label") or "Đã xác minh & công bố"),
                }
                stage_docs_by_stage.setdefault(st_d, []).append(enriched_doc)

            for cdoc in raw_cust_sub_docs:
                cid = str(cdoc.get("id") or "")
                if cid in pub_doc_ids:
                    continue
                st_d = str(cdoc.get("stage_id") or "finance-reconciliation").strip()
                sub_entry = {
                    "id": cid,
                    "version": str(cdoc.get("version") or "v1"),
                    "kind": str(cdoc.get("kind") or "PAYMENT_REQUEST"),
                    "title": str(cdoc.get("public_title") or cdoc.get("file_name") or cid),
                    "stage_id": st_d,
                    "source_side": "CUSTOMER",
                    "verified": bool(cdoc.get("verified", False)),
                    "verification_status": str(cdoc.get("verification_status") or "SUBMITTED_UNVERIFIED"),
                    "verification_label": str(
                        cdoc.get("verification_label") or "Hồ sơ khách đã nộp — Chờ TT xác minh"
                    ),
                }
                stage_docs_by_stage.setdefault(st_d, []).append(sub_entry)

            customer_nodes: list[dict[str, Any]] = []
            verified_stage_label = "Chưa xác minh"
            is_complete = "delivery" in events_by_stage

            # Node 00 — KẾ HOẠCH (before pickup)
            plan_done = bool(plan_detail["verified"])
            plan_ent = plan_detail["entrusted_import"]
            if plan_ent["applicable"]:
                plan_state = "COMPLETED" if plan_done else "WAITING"
                plan_evidence = (
                    f"HĐ {plan_detail['contract_no']} · Báo giá {plan_detail['quote_no']} · {plan_ent['status_label']}"
                )
            else:
                plan_state = "COMPLETED" if plan_done else "UPCOMING"
                plan_evidence = (
                    f"HĐ {plan_detail['contract_no']} · Báo giá {plan_detail['quote_no']} ({plan_detail['quote_confirmation_status']})"
                    if plan_done
                    else "Chưa xác nhận kế hoạch thương mại"
                )
            customer_nodes.append(
                {
                    "id": "plan",
                    "index": "00",
                    "label": "KẾ HOẠCH",
                    "completed": plan_done,
                    "current": False,
                    "state": plan_state,
                    "evidence": plan_evidence,
                    "occurred_at": str(plan_detail.get("verified_at") or ""),
                    "plan_detail": plan_detail,
                    "stage_comments": comments_by_stage.get("plan", []),
                    "stage_documents": stage_docs_by_stage.get("plan", []),
                }
            )

            # Nodes 01..05 — 5 ROAD LTL transport stages (unchanged logic & labels)
            transport_idx = 1
            for raw_node in internal_journey.get("nodes") or []:
                n_id = str(raw_node.get("id") or "")
                if n_id == "MAIN_CARRIAGE":
                    continue
                n_label = str(raw_node.get("label") or n_id)
                # HEXA-CUSTOMER-JOURNEY-UI-FIDELITY:
                # Never mark a stage completed merely because a previous stage completed.
                # Specifically, a 'pickup' event does NOT automatically prove 'road-ltl' (consolidation) is completed.
                matched_ev = events_by_stage.get(n_id)
                is_done = matched_ev is not None
                is_current = bool(verified_stage_id and n_id == verified_stage_id and not is_complete)
                if verified_stage_id and n_id == verified_stage_id:
                    verified_stage_label = n_label
                customer_nodes.append(
                    {
                        "id": n_id,
                        "index": f"{transport_idx:02d}",
                        "label": n_label,
                        "completed": is_done,
                        "current": is_current,
                        "state": (
                            "CURRENT"
                            if is_current
                            else ("COMPLETED" if is_done else "UPCOMING")
                        ),
                        "evidence": (
                            str(matched_ev.get("title") or "")
                            if matched_ev
                            else "Chưa có mốc xác minh được công bố"
                        ),
                        "occurred_at": str(matched_ev.get("occurred_at") or "") if matched_ev else "",
                        "stage_comments": comments_by_stage.get(n_id, []),
                        "stage_documents": stage_docs_by_stage.get(n_id, []),
                    }
                )
                transport_idx += 1

            # Node 06 — THANH TOÁN & ĐỐI SOÁT (after delivery; independent of delivery completion!)
            fin_done = bool(finance_detail["completed"])
            if fin_done:
                fin_state = "COMPLETED"
            elif debt_summary["status"] == "CONFIRMED":
                fin_state = "WAITING"
            else:
                fin_state = "UPCOMING"
            customer_nodes.append(
                {
                    "id": "finance-reconciliation",
                    "index": "06",
                    "label": "THANH TOÁN & ĐỐI SOÁT",
                    "completed": fin_done,
                    "current": False,
                    "state": fin_state,
                    "evidence": str(debt_summary["status_label"]),
                    "occurred_at": str(debt_summary.get("updated_at") or ""),
                    "finance_detail": finance_detail,
                    "stage_comments": comments_by_stage.get("finance-reconciliation", []),
                    "stage_documents": stage_docs_by_stage.get("finance-reconciliation", []),
                }
            )

            customer_edges: list[dict[str, str]] = [
                {"from": customer_nodes[i]["id"], "to": customer_nodes[i + 1]["id"]}
                for i in range(len(customer_nodes) - 1)
            ]

            if verified_stage_id and verified_stage_label == "Chưa xác minh":
                verified_stage_label = verified_stage_id

            # HEXA-DASHBOARD-CUSTOMER-ACTION-BOUNDARY:
            # 1. Never read internal shipment['tasks'] or unapproved link['customer_actions'].
            # 2. TT staff work (responsible_side != 'CUSTOMER') and other customers' items are never customer actions.
            # 3. Because V1 has no separate TT publication approval mechanism for customer actions
            #    (build_customer_publication only approves event_versions, document_versions, and quote),
            #    keep customer_action=None, needs_customer_action=False, KPI=0, and label='Chưa có yêu cầu được xác nhận'.
            customer_action: dict[str, str] | None = None
            needs_customer_action = False

            if is_complete:
                next_step = "Đã giao hàng (xác minh hoàn tất)"
            elif verified_warehouse_eta:
                next_step = f"Theo dõi lịch giao kho đã xác minh ({verified_warehouse_eta}) — Chưa có yêu cầu được xác nhận"
            elif timeline:
                next_step = "Đang vận chuyển theo hành trình — Chưa có yêu cầu được xác nhận"
            else:
                next_step = "Chờ Trường Thành cập nhật mốc xác minh tiếp theo — Chưa có yêu cầu được xác nhận"

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
                    "customer_action": customer_action,
                    "next_step": next_step,
                    "contact_point": contact_point,
                    "debt_summary": debt_summary,
                    "plan_detail": plan_detail,
                    "finance_detail": finance_detail,
                    "journey": {
                        "current_stage_id": verified_stage_id or "",
                        "nodes": customer_nodes,
                        "edges": customer_edges,
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
        # Việc 2: Only count shipments with a TT-verified and published warehouse ETA.
        # Never infer from border/customs stage!
        verified_warehouse_eta_count = sum(
            1
            for r in rows
            if not r["is_complete"] and r["verified_warehouse_eta"] is not None
        )
        arriving_soon = verified_warehouse_eta_count
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
                "verified_warehouse_eta_count": verified_warehouse_eta_count,
                "arriving_soon": arriving_soon,
                "arriving_soon_label": "Có ETA kho đã xác minh",
                "customer_action_needed": customer_action_needed,
                "customer_action_status_label": (
                    f"{customer_action_needed} yêu cầu đang mở"
                    if customer_action_needed > 0
                    else "Chưa có yêu cầu được xác nhận"
                ),
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

        if doc_row.get("revoked") is True:
            self.denied_before_storage_reads += 1
            self._record_audit(
                action="DOWNLOAD_DOCUMENT",
                principal=principal,
                shipment_id=sid,
                allowed=False,
                detail=f"doc={doc_id}@{ver} revoked BEFORE storage read",
            )
            raise PublicationDenied()

        # Customer-submitted stage documents (source_side='CUSTOMER', verified=False) can be downloaded
        # ONLY by the owning customer while the shipment is PUBLISHED and the document is not revoked.
        is_own_customer_submission = bool(
            doc_row.get("source_side") == "CUSTOMER"
            and principal.get("authenticated") is True
            and principal.get("kind") == "customer"
            and cust_id
            and str(doc_row.get("customer_id") or "") == cust_id
            and str(doc_row.get("shipment_id") or "") == sid
            and str(doc_row.get("version") or "") == ver
            and publication.get("state") == "PUBLISHED"
            and candidate_doc.get("status") == "AVAILABLE"
        )

        if not is_own_customer_submission:
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


def seed_live_preview_publications(env: HexaTrialEnvironment | None = None) -> None:
    """Pre-publish 2 shipments for Lục Giác (ROAD-LG-001 + ROAD-LG-002) and 1 shipment for Minh Đức (ROAD-MD-002)
    via real TT staff approval for the standalone Live Preview server, while keeping ROAD-AP-003 (An Phát) UNPUBLISHED.

    - Lục Giác (2 shipments): opens Multi-Shipment Dashboard Overview -> select shipment -> Journey Map -> Back to Dashboard.
    - Minh Đức (1 shipment): opens straight into Journey Map.
    - An Phát (0 shipments): shows friendly empty state.
    - Note: ``HexaTrialEnvironment()`` by itself remains 100% default-deny ``UNPUBLISHED`` for unit/E2E tests.
    """
    target_env = env or get_trial_environment()
    target_env.ensure_seeded()
    tt_token, _ = target_env.authenticate_tt_staff_login(
        username=TT_STAFF_TRIAL_USERNAME,
        passcode=TT_STAFF_TRIAL_PASSCODE,
    )
    target_env.publish_shipment_for_customer(
        session_token=tt_token,
        shipment_id=SHIPMENT_A_ID,
        event_versions={
            "EVT-LG-01-PICKUP": "v1",
            "EVT-LG-02-BORDER": "v2",
        },
        document_versions={
            "DOC-LG-PL": "v2",
            "DOC-LG-PI": "v1",
        },
        quote={"id": QUOTE_A_ID, "version": "3"},
    )
    target_env.publish_shipment_for_customer(
        session_token=tt_token,
        shipment_id=SHIPMENT_A2_ID,
        event_versions={
            "EVT-LG02-01-PICKUP": "v1",
            "EVT-LG02-02-CUSTOMS": "v1",
        },
        document_versions={
            "DOC-LG02-PL": "v1",
        },
        quote={"id": QUOTE_A2_ID, "version": "1"},
    )
    target_env.publish_shipment_for_customer(
        session_token=tt_token,
        shipment_id=SHIPMENT_B_ID,
        event_versions={
            "EVT-MD-01-PICKUP": "v1",
        },
        document_versions={
            "DOC-MD-PL": "v1",
        },
        quote={"id": QUOTE_B_ID, "version": "1"},
    )


def _extract_cookie_from_raw(raw_cookie: str, cookie_name: str) -> str:
    if not raw_cookie:
        return ""
    try:
        cookie = SimpleCookie()
        cookie.load(raw_cookie)
        if cookie_name in cookie and cookie[cookie_name].value.strip():
            return cookie[cookie_name].value.strip()
    except Exception:  # noqa: BLE001
        pass
    for part in raw_cookie.split(";"):
        piece = part.strip()
        if "=" not in piece:
            continue
        k, v = piece.split("=", 1)
        if k.strip() == cookie_name and v.strip():
            return v.strip()
    return ""


def _extract_session_token(headers: Mapping[str, str]) -> str:
    """Extract customer session token strictly from HTTP headers or Cookie (NEVER from URL query params)."""
    custom_hdr = str(
        headers.get("X-Hexa-Session-Token") or headers.get("x-hexa-session-token") or ""
    ).strip()
    if custom_hdr:
        return custom_hdr
    auth_header = str(headers.get("Authorization") or headers.get("authorization") or "").strip()
    if auth_header.lower().startswith("bearer "):
        return auth_header[7:].strip()
    raw_cookie = str(headers.get("Cookie") or headers.get("cookie") or "").strip()
    return _extract_cookie_from_raw(raw_cookie, TRIAL_COOKIE_NAME)


def _extract_tt_session_token(headers: Mapping[str, str]) -> str:
    """Extract TT staff session token strictly from HTTP headers or Cookie (NEVER from URL query params)."""
    custom_hdr = str(
        headers.get("X-Hexa-Session-Token") or headers.get("x-hexa-session-token") or ""
    ).strip()
    if custom_hdr:
        return custom_hdr
    auth_header = str(headers.get("Authorization") or headers.get("authorization") or "").strip()
    if auth_header.lower().startswith("bearer "):
        return auth_header[7:].strip()
    raw_cookie = str(headers.get("Cookie") or headers.get("cookie") or "").strip()
    tt_val = _extract_cookie_from_raw(raw_cookie, TRIAL_TT_COOKIE_NAME)
    if tt_val:
        return tt_val
    return _extract_cookie_from_raw(raw_cookie, TRIAL_COOKIE_NAME)


def render_trial_portal_html() -> str:
    """Customer Map-First Journey Portal HTML (HEXA V0 / V1).

    Reuses ``component/dist/logi-shell.css``, ``component/src/assets/journey/vietnam-east-sea-chart.webp``,
    ``component/src/assets/journey/chart-paper.jpg``, and the ``JourneyMap.tsx`` + ``JourneyBubble.tsx``
    + ``ShipmentJourney.tsx`` DOM/geometry/pan-zoom-fit/bubble/modal contract over read-only
    TT-approved customer data.

    Contains ZERO TT internal screens, role-switching tabs, Customer A/B/C sample buttons,
    sample credentials, debug JSON, technical schema dumps, or internal TT holdback data.
    """
    return """<!doctype html>
<html lang="vi">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>HEXA V0 — Cổng Hành Trình Lô Hàng Khách Hàng</title>
  <link rel="stylesheet" href="/assets/journey/logi-shell.css" />
  <style>
    :root {
      --bg: #eef2f6;
      --surface: #ffffff;
      --border: #cbd5e1;
      --text: #0f172a;
      --muted: #475569;
      --primary: #1a4b75;
      --mono: "IBM Plex Mono", ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      --sans: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    * { box-sizing: border-box; }
    body { margin: 0; font-family: var(--sans); color: var(--text); background: var(--bg); line-height: 1.45; }
    .hidden { display: none !important; }
    .portal-header { background: linear-gradient(90deg, #0c233a 0%, #153c61 100%); color: #f8fafc; padding: 12px 20px; border-bottom: 2px solid #1e5b8f; }
    .portal-header-inner { max-width: 1380px; margin: 0 auto; display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 12px; }
    .brand-group { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
    .brand-badge { padding: 4px 10px; border-radius: 6px; background: rgba(255, 255, 255, 0.14); border: 1px solid rgba(255, 255, 255, 0.24); font-family: var(--mono); font-size: 11.5px; font-weight: 700; letter-spacing: 0.05em; }
    .brand-title { margin: 0; font-size: 16px; font-weight: 800; letter-spacing: -0.01em; }
    .brand-sub { font-size: 12px; color: #cbd5e1; font-weight: 500; }
    .portal-main { max-width: 1380px; margin: 14px auto; padding: 0 16px 36px; }
    .login-shell { max-width: 460px; margin: 48px auto; background: #ffffff; border: 1px solid #cbd5e1; border-radius: 12px; padding: 26px 28px; box-shadow: 0 18px 40px -18px rgba(15, 23, 42, 0.22); }
    .login-shell h2 { margin: 0 0 6px; font-size: 18px; font-weight: 800; color: #0f2942; }
    .login-shell p { margin: 0 0 16px; font-size: 13px; color: var(--muted); }
    .field-group { display: grid; gap: 6px; margin-bottom: 12px; }
    .field-group label { font-size: 12px; font-weight: 700; color: #334155; }
    .field-group input { padding: 9px 12px; border: 1px solid #cbd5e1; border-radius: 7px; font-size: 13.5px; font-family: var(--sans); }
    .btn-primary { cursor: pointer; border: 1px solid #1a4b75; background: #1a4b75; color: #fff; padding: 9px 14px; border-radius: 7px; font-size: 13px; font-weight: 700; }
    .btn-primary:hover { background: #123656; }
    .btn-ghost { cursor: pointer; border: 1px solid rgba(255, 255, 255, 0.35); background: rgba(255, 255, 255, 0.1); color: #fff; padding: 6px 12px; border-radius: 6px; font-size: 12px; font-weight: 700; }
    .customer-kpi-strip { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 10px; background: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px; padding: 8px 12px; margin-bottom: 10px; }
    .kpi-pills { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
    .kpi-pill { display: inline-flex; align-items: center; gap: 6px; padding: 4px 10px; border-radius: 6px; background: #f8fafc; border: 1px solid #e2e8f0; font-size: 12px; color: #334155; font-weight: 600; }
    .kpi-pill strong { font-family: var(--mono); font-size: 13px; color: #0f172a; }
    .shipment-selector-bar { background: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px; padding: 10px 12px; margin-bottom: 10px; }
    .shipment-selector-bar table, .doc-list-table { width: 100%; border-collapse: collapse; font-size: 12.5px; }
    .shipment-selector-bar th, .shipment-selector-bar td, .doc-list-table th, .doc-list-table td { padding: 7px 9px; border-bottom: 1px solid #e2e8f0; text-align: left; }
    .shipment-selector-bar th, .doc-list-table th { font-size: 11px; text-transform: uppercase; color: #475569; background: #f8fafc; }
    .readonly-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 10px; margin-bottom: 12px; }
    .readonly-box { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 7px; padding: 10px 12px; }
    .readonly-box .lbl { font-size: 10.5px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.05em; color: #64748b; }
    .readonly-box .val { font-size: 13px; font-weight: 700; color: #0f172a; margin-top: 3px; }
    .status-note { margin-top: 10px; padding: 8px 12px; border-radius: 7px; font-size: 12.5px; font-weight: 600; background: #f1f5f9; color: #334155; }
    /* Canonical G2 Map-First Journey layout rules ensuring 100% containment inside #journey-map-viewport */
    .journey-split.journey-map-first { position: relative; display: block; width: 100%; }
    .journey-split.journey-map-first .journey-canvas {
      position: relative !important;
      display: block;
      width: 100%;
      height: clamp(520px, calc(100vh - 230px), 660px);
      min-height: 520px;
      border-radius: 12px;
      border: 1px solid #D6DEE7;
      background-color: #EDF1F5;
      overflow: hidden !important;
      user-select: none;
      touch-action: none;
      cursor: grab;
    }
    .journey-split.journey-map-first .journey-canvas.is-dragging { cursor: grabbing; }
    .journey-sea-chart {
      position: absolute !important;
      inset: 0 !important;
      z-index: 0;
      pointer-events: none;
      background-color: #E9EFF5;
      background-repeat: no-repeat;
      background-size: cover;
      background-position: center center;
    }
    @media (max-width: 720px) and (orientation: portrait) {
      .journey-sea-chart { background-size: contain; background-position: center center; }
    }
    .journey-edges {
      position: absolute;
      left: 0;
      top: 0;
      width: 1080px;
      height: 520px;
      pointer-events: none;
      z-index: 1;
      overflow: visible;
    }
    .journey-node {
      position: absolute;
      width: 116px;
      height: 66px;
      overflow: hidden;
      border-radius: 10px;
      border: 1px solid #C9D4DF;
      background: #fff;
      color: #10263C;
      cursor: pointer;
      padding: 6px 8px 6px 10px;
      box-shadow: 0 8px 18px -12px rgba(16,38,60,.42);
      font-family: var(--sans);
      text-align: left;
      display: flex;
      flex-direction: column;
      z-index: 10;
      --stripe: #94A3B8;
    }
    .journey-bubble {
      position: absolute;
      z-index: 35;
      pointer-events: auto;
      background: #fff;
      border: 1px solid #C9D4DF;
      border-radius: 12px;
      padding: 0;
      overflow: hidden;
      color: #10263C;
      box-shadow: 0 18px 36px -14px rgba(16,38,60,.38);
    }
    .journey-bubble-above { transform: translateY(-100%); }
    .journey-bubble-dot {
      display: inline-grid;
      place-items: center;
      width: 18px;
      height: 18px;
      margin-top: 2px;
      border-radius: 999px;
      font-size: 10px;
      font-weight: 800;
      flex-shrink: 0;
    }
    .journey-bubble-dot.dot-done { background: #DCEDE4; color: #22614A; border: 1px solid #96C7AF; }
    .journey-bubble-dot.dot-info { background: #DCEBFA; color: #154C79; border: 1px solid #8EC0E8; }
    .journey-bubble-dot.dot-pending { background: #E7ECF2; color: #5B6875; border: 1px solid #C8D3DF; }
    .journey-bubble-open {
      cursor: pointer;
      border: none;
      background: transparent;
      color: #123A5E;
      font-size: 12px;
      font-weight: 800;
      padding: 0;
    }
    .journey-map-hint {
      position: absolute;
      bottom: 12px;
      left: 12px;
      z-index: 20;
      display: inline-flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 6px;
      padding: 7px 12px;
      border-radius: 10px;
      border: 1px solid #D6DEE7;
      background: rgba(255, 255, 255, 0.94);
      color: #10263C;
      font-size: 11.5px;
      font-weight: 600;
      box-shadow: 0 6px 16px -10px rgba(16, 38, 60, 0.35);
    }
    .journey-zoom-bar {
      position: absolute;
      bottom: 12px;
      right: 12px;
      z-index: 20;
      display: flex;
      align-items: center;
      gap: 4px;
      background: rgba(255, 255, 255, 0.94);
      border: 1px solid #D6DEE7;
      border-radius: 10px;
      padding: 4px;
      box-shadow: 0 6px 16px -10px rgba(16, 38, 60, 0.45);
    }
    .journey-side-head {
      background: #10263C;
      color: #fff;
      padding: 12px 16px;
      border-bottom: 1px solid #1E3E5C;
    }
    .journey-side-title-row { display: flex; align-items: flex-start; justify-content: space-between; gap: 10px; }
    .journey-side-kicker { font-family: var(--mono); font-size: 10.5px; font-weight: 700; color: #9CCAF0; letter-spacing: 0.08em; }
    .journey-side-title { margin: 3px 0 0; font-size: 16px; font-weight: 800; color: #fff; }
    .journey-side-sub { margin-top: 2px; font-size: 12px; color: #cbd5e1; }
    .journey-side-badge { padding: 3px 8px; border-radius: 999px; background: rgba(255,255,255,0.14); color: #fff; font-size: 11px; font-weight: 700; }
    .journey-modal-close { cursor: pointer; padding: 5px 10px; border-radius: 6px; border: 1px solid rgba(255,255,255,0.28); background: rgba(255,255,255,0.1); color: #fff; font-size: 12px; font-weight: 700; }
    .journey-side-body { padding: 14px 16px; overflow-y: auto; background: #fff; color: #0f172a; }
    .dash-table-desktop tbody tr { cursor: pointer; transition: background-color 0.14s ease; }
    .dash-table-desktop tbody tr:hover { background-color: #f1f5f9; }
    .dash-cards-mobile { display: none; gap: 10px; }
    .shipment-card-mobile {
      border: 1px solid #cbd5e1;
      border-radius: 10px;
      padding: 12px;
      background: #ffffff;
      display: grid;
      gap: 8px;
      cursor: pointer;
      box-shadow: 0 4px 12px -6px rgba(15, 23, 42, 0.15);
    }
    .shipment-card-top { display: flex; align-items: center; justify-content: space-between; gap: 6px; flex-wrap: wrap; }
    .shipment-card-meta { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; font-size: 11.5px; color: #334155; background: #f8fafc; padding: 7px 9px; border-radius: 6px; border: 1px solid #e2e8f0; }
    @media (max-width: 720px) {
      .dash-table-desktop { display: none !important; }
      .dash-cards-mobile { display: grid !important; }
    }
  </style>
</head>
<body>
  <header class="portal-header" data-testid="shipment-identity-bar">
    <div class="portal-header-inner">
      <div class="brand-group">
        <span class="brand-badge">HEXA V0 · JOURNEY MAP</span>
        <div>
          <h1 class="brand-title" id="customer-brand-title">Cổng Hành Trình Lô Hàng Khách Hàng</h1>
          <div class="brand-sub" id="customer-brand-sub">Theo dõi trực quan trên hải đồ theo dữ liệu Trường Thành đã xác minh</div>
        </div>
      </div>
      <div class="brand-group" id="header-auth-controls">
        <span id="session-pill" class="brand-badge">Chưa đăng nhập</span>
        <button id="btn-customer-logout" type="button" class="btn-ghost hidden" onclick="logoutCustomer()">Đăng xuất</button>
      </div>
    </div>
  </header>

  <main class="portal-main">
    <section id="customer-login-screen" class="login-shell" data-testid="customer-login-screen">
      <h2>Đăng nhập Cổng Khách Hàng</h2>
      <p>Vui lòng đăng nhập bằng tài khoản doanh nghiệp để xem hải đồ hành trình và chứng từ đã được Trường Thành công bố.</p>
      <form onsubmit="event.preventDefault(); loginCustomer();">
        <div class="field-group">
          <label for="cust-username">Tài khoản khách hàng</label>
          <input id="cust-username" type="text" autocomplete="username" placeholder="Nhập tài khoản doanh nghiệp" />
        </div>
        <div class="field-group">
          <label for="cust-passcode">Mật khẩu</label>
          <input id="cust-passcode" type="password" autocomplete="current-password" placeholder="Nhập mật khẩu" />
        </div>
        <div style="display:flex; gap:10px; align-items:center; margin-top:14px;">
          <button id="btn-customer-login" type="submit" class="btn-primary" onclick="loginCustomer()">Đăng nhập</button>
        </div>
      </form>
      <div id="customer-auth-note" class="status-note">Đăng nhập để mở bản đồ hành trình lô hàng của quý khách.</div>
    </section>

    <section id="journey-workspace-shell" class="hidden" data-testid="journey-workspace-shell">
      <div class="customer-kpi-strip">
        <div class="kpi-pills">
          <span class="kpi-pill">Đang theo dõi: <strong id="kpi-active-tracking">0</strong></span>
          <span class="kpi-pill">Có ETA kho đã xác minh: <strong id="kpi-arriving-soon">0</strong></span>
          <span class="kpi-pill">Cần khách xử lý: <strong id="kpi-customer-action">0</strong> (<span id="kpi-customer-action-sub">Chưa có yêu cầu được xác nhận</span>)</span>
        </div>
        <div style="display:flex; gap:8px; align-items:center; flex-wrap:wrap;">
          <input id="shipment-input" type="text" placeholder="Mã lô hàng" style="padding:5px 9px; border:1px solid #cbd5e1; border-radius:6px; font-family:var(--mono); font-size:12px; width:145px;" />
          <button type="button" class="journey-toolbar-btn" onclick="openRequestedShipmentInput()">Mở hành trình</button>
          <button type="button" class="journey-toolbar-btn" onclick="loadCustomerDashboard()">↻ Làm mới</button>
        </div>
      </div>

      <div id="customer-shipment-selector" class="shipment-selector-bar hidden" data-testid="customer-shipment-selector">
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px; margin-bottom:8px;">
          <div style="font-size:13px; font-weight:800; color:#0f2942;">Dashboard tổng quan các lô hàng đã công bố (chọn một lô để mở hải đồ Journey Map):</div>
        </div>
        <table class="dash-table-desktop">
          <thead>
            <tr>
              <th>Mã lô</th>
              <th>Hàng hóa &amp; Tuyến</th>
              <th>Phương thức</th>
              <th>Chặng xác minh</th>
              <th>ETA được xác minh</th>
              <th>Công nợ</th>
              <th>Cập nhật cuối</th>
              <th>Hành trình</th>
            </tr>
          </thead>
          <tbody id="dash-shipments-tbody"></tbody>
        </table>
        <div id="dash-shipments-cards" class="dash-cards-mobile" data-testid="dash-shipments-cards"></div>
      </div>

      <div id="shipment-journey-view" class="journey-demo" data-testid="shipment-journey">
        <div class="journey-toolbar" data-testid="journey-compact-toolbar">
          <button id="btn-back-to-dashboard" type="button" class="journey-toolbar-btn hidden" data-testid="btn-back-to-dashboard" onclick="backToDashboard()">
            ← Quay lại Dashboard
          </button>
          <span id="toolbar-id" class="journey-toolbar-id">—</span>
          <span id="toolbar-mode" class="journey-toolbar-chip">ROAD</span>
          <span id="toolbar-customer" class="journey-toolbar-customer">—</span>
          <span id="toolbar-route" class="journey-toolbar-route">—</span>
          <span id="toolbar-here" class="journey-toolbar-chip journey-toolbar-here">Đang ở: —</span>
          <span id="toolbar-eta" class="journey-toolbar-chip">ETA kho: Chưa xác minh</span>
          <span id="toolbar-next" class="journey-toolbar-next">—</span>
          <button type="button" class="journey-toolbar-btn" data-testid="journey-global-open" onclick="openGlobalModal('docs')">
            ▤ Chứng từ &amp; Báo giá
          </button>
        </div>

        <div class="journey-split journey-map-first">
          <div id="journey-map-viewport" class="journey-canvas" data-testid="journey-map-viewport" style="min-height:540px; cursor:grab; user-select:none;">
            <div class="journey-sea-chart" data-testid="journey-sea-chart" aria-hidden="true" style="background-image:url('/assets/journey/vietnam-east-sea-chart.webp');"></div>
            <div data-testid="journey-map-texture" aria-hidden="true" style="position:absolute; inset:0; background-image:url('/assets/journey/chart-paper.jpg'); background-size:460px 460px; background-repeat:repeat; opacity:0.16; mix-blend-mode:multiply; pointer-events:none; z-index:0;"></div>
            <div data-testid="journey-map-grid" aria-hidden="true" style="position:absolute; inset:0; background-image:linear-gradient(to right, rgba(20, 55, 85, 0.045) 1px, transparent 1px), linear-gradient(to bottom, rgba(20, 55, 85, 0.045) 1px, transparent 1px); background-size:52px 52px; pointer-events:none; z-index:0;"></div>

            <div style="position:absolute; top:12px; right:12px; z-index:18; pointer-events:auto;">
              <button type="button" data-testid="journey-utility-trigger" onclick="toggleUtilityBubble()" style="display:inline-flex; align-items:center; gap:7px; padding:6px 11px; border-radius:6px; border:1px solid rgba(26, 75, 117, 0.42); background:rgba(255, 255, 255, 0.94); color:#0f2236; font-size:11.5px; font-weight:800; cursor:pointer;">
                <span>▤ Hồ sơ &amp; Chứng từ</span>
                <span id="utility-doc-count" style="padding:1px 6px; border-radius:4px; background:#eff6ff; color:#1d4ed8; font-family:var(--mono); font-size:10.5px; font-weight:800;">0 tệp</span>
              </button>
              <div id="journey-utility-bubble" data-testid="journey-utility-bubble" class="hidden" style="margin-top:6px; width:280px; border-radius:8px; border:1px solid rgba(26, 75, 117, 0.38); background:rgba(255, 255, 255, 0.98); overflow:hidden;">
                <div style="padding:8px 11px; background:#0f2236; color:#f8fafc; font-size:10.5px; font-weight:800; text-transform:uppercase; display:flex; justify-content:space-between; align-items:center;">
                  <span>Dữ liệu Trường Thành đã duyệt</span>
                  <button type="button" onclick="toggleUtilityBubble(false)" style="border:none; background:transparent; color:#cbd5e1; cursor:pointer;">✕</button>
                </div>
                <div style="padding:6px; display:grid; gap:4px;">
                  <button type="button" onclick="openGlobalModal('docs')" style="display:flex; align-items:center; justify-content:space-between; padding:7px 9px; border-radius:6px; border:1px solid #e2e8f0; background:#f8fafc; color:#0f172a; font-size:11.5px; font-weight:700; cursor:pointer;">
                    <span>Chứng từ được phép tải</span>
                    <span id="utility-docs-sub" style="font-size:10.5px; color:#1d4ed8; font-family:var(--mono);">0 tệp</span>
                  </button>
                  <button type="button" onclick="openGlobalModal('quote')" style="display:flex; align-items:center; justify-content:space-between; padding:7px 9px; border-radius:6px; border:1px solid #e2e8f0; background:#f8fafc; color:#0f172a; font-size:11.5px; font-weight:700; cursor:pointer;">
                    <span>Báo giá bán đã duyệt</span>
                    <span id="utility-quote-sub" style="font-size:10.5px; color:#15803d; font-family:var(--mono);">—</span>
                  </button>
                </div>
              </div>
            </div>

            <div id="journey-zero-notice" class="journey-zero-notice hidden" data-testid="journey-zero-state" style="position:relative; z-index:12; margin:48px auto; max-width:520px; background:rgba(255,255,255,0.95);">
              <span class="journey-zero-kicker">TRẠNG THÁI CÔNG BỐ</span>
              <strong id="journey-zero-title" class="journey-zero-title">Trường Thành chưa công bố thông tin cho lô này</strong>
              <span id="journey-zero-summary" class="journey-zero-summary">Hành trình xác minh, báo giá bán và chứng từ sẽ xuất hiện trên hải đồ ngay khi Trường Thành duyệt công bố.</span>
            </div>

            <div id="journey-map-transform" data-testid="journey-map-transform" style="position:relative; width:1080px; height:520px; transform:translate(0px, 0px) scale(1); transform-origin:0 0; z-index:2;">
              <svg id="journey-edges-svg" class="journey-edges" viewBox="0 0 1080 520" preserveAspectRatio="none"></svg>
              <div id="journey-nodes-layer"></div>
              <div id="journey-bubble-slot"></div>
            </div>

            <div class="journey-map-hint" data-testid="journey-status-legend">
              <span><b>✓</b> Có bằng chứng</span>
              <span class="sep">·</span>
              <span><b>◐</b> Đang xử lý</span>
              <span class="sep">·</span>
              <span><b>◷</b> Chờ thông tin</span>
              <span class="sep">·</span>
              <span><b>·</b> Chưa bắt đầu</span>
              <span class="sep">·</span>
              <span id="journey-zoom-pct">100%</span>
            </div>

            <div class="journey-zoom-bar">
              <button type="button" class="journey-zoom-btn" data-testid="journey-zoom-in" onclick="zoomIn()" title="Phóng to">+</button>
              <button type="button" class="journey-zoom-btn" data-testid="journey-zoom-out" onclick="zoomOut()" title="Thu nhỏ">−</button>
              <div id="journey-zoom-level" class="journey-zoom-level" data-testid="journey-zoom-level">100%</div>
              <button type="button" class="journey-zoom-btn journey-zoom-text" data-testid="journey-zoom-fit" onclick="fitJourney()">⤢ Fit Journey</button>
              <button type="button" class="journey-zoom-btn journey-zoom-text" data-testid="journey-zoom-readable" onclick="resetReadable()">↺ Đọc rõ</button>
            </div>
          </div>

          <div id="journey-modal-layer" class="journey-modal-layer hidden" data-testid="journey-modal" role="dialog" aria-modal="true">
            <div class="journey-modal-backdrop" data-testid="journey-modal-backdrop" onclick="closeStageModal()"></div>
            <aside class="journey-side journey-modal-card" data-testid="journey-stage-workspace">
              <div class="journey-side-head">
                <div class="journey-side-title-row">
                  <div>
                    <div id="modal-kicker" class="journey-side-kicker">CHI TIẾT ĐÃ XÁC MINH (CHỈ ĐỌC)</div>
                    <h3 id="modal-title" class="journey-side-title">—</h3>
                    <div id="modal-sub" class="journey-side-sub">—</div>
                  </div>
                  <div style="display:flex; align-items:center; gap:8px;">
                    <span id="modal-badge" class="journey-side-badge">—</span>
                    <button type="button" class="journey-modal-close" data-testid="journey-modal-close" onclick="closeStageModal()">✕ Đóng</button>
                  </div>
                </div>
              </div>
              <div id="journey-modal-body" class="journey-side-body"></div>
            </aside>
          </div>
        </div>
      </div>

      <div id="download-status-banner" class="status-note hidden"></div>
    </section>
  </main>

  <script>
    const JOURNEY_NODE_W = 116;
    const JOURNEY_NODE_H = 66;
    const PITCH = 148;
    const PX = 24;
    const col = (c) => PX + c * PITCH;
    const DEMO_POS = {
      'plan':                   { x: col(0), y: 205 },
      'pickup':                 { x: col(1), y: 205 },
      'road-ltl':               { x: col(2), y: 205 },
      'road-border':            { x: col(3), y: 205 },
      'customs-import':         { x: col(4), y: 205 },
      'delivery':               { x: col(5), y: 205 },
      'finance-reconciliation': { x: col(6), y: 205 }
    };
    const JOURNEY_NODE_STATUS = {
      COMPLETED: 'CÓ BẰNG CHỨNG',
      CURRENT:   'ĐANG XỬ LÝ',
      WAITING:   'CHỜ THÔNG TIN',
      PROBLEM:   'CẦN XỬ LÝ',
      UPCOMING:  'CHƯA BẮT ĐẦU'
    };

    function clearChildren(el) {
      if (!el) return;
      while (el.firstChild) {
        el.removeChild(el.firstChild);
      }
      el.textContent = '';
    }

    function formatMoney(amount, currency) {
      if (typeof amount !== 'number' || Number.isNaN(amount)) return 'UNKNOWN / Chưa đối soát';
      const cur = String(currency || 'VND');
      return new Intl.NumberFormat('vi-VN').format(amount) + ' ' + cur;
    }

    let currentSession = { authenticated: false, principal: {}, default_shipment_id: '' };
    let activeAuthToken = '';
    try {
      if (typeof sessionStorage !== 'undefined') {
        activeAuthToken = sessionStorage.getItem('hexa_cust_token') || '';
      }
    } catch (_e) {}

    function setAuthToken(tok) {
      activeAuthToken = String(tok || '');
      try {
        if (typeof sessionStorage !== 'undefined') {
          if (activeAuthToken) sessionStorage.setItem('hexa_cust_token', activeAuthToken);
          else sessionStorage.removeItem('hexa_cust_token');
        }
      } catch (_e) {}
    }

    function apiFetch(url, opts) {
      const options = Object.assign({ credentials: 'same-origin' }, opts || {});
      const hdrs = Object.assign({}, options.headers || {});
      if (activeAuthToken) {
        hdrs['Authorization'] = 'Bearer ' + activeAuthToken;
        hdrs['X-Hexa-Session-Token'] = activeAuthToken;
      }
      options.headers = hdrs;
      return fetch(url, options);
    }

    let dashboardRows = [];
    let activeShipmentRow = null;
    let activePublication = null;
    let selectedNodeId = null;
    let currentScale = 1;
    let currentPan = { x: 0, y: 0 };

    function formatVnd(amount) {
      if (typeof amount !== 'number') return 'Chưa công bố';
      return new Intl.NumberFormat('vi-VN').format(amount) + ' VND';
    }

    function getNodePos(id, idx) {
      if (DEMO_POS[id]) return DEMO_POS[id];
      return { x: PX + idx * PITCH, y: 205 };
    }

    function journeyEdgePath(a, b) {
      const x1 = a.x + JOURNEY_NODE_W;
      const y1 = a.y + JOURNEY_NODE_H / 2;
      const x2 = b.x;
      const y2 = b.y + JOURNEY_NODE_H / 2;
      const dx = Math.max(40, Math.abs(x2 - x1) * 0.42);
      return `M ${x1} ${y1} C ${x1 + dx} ${y1}, ${x2 - dx} ${y2}, ${x2} ${y2}`;
    }

    function applyTransform() {
      const tf = document.getElementById('journey-map-transform');
      if (tf && tf.style) {
        tf.style.transform = `translate(${currentPan.x}px, ${currentPan.y}px) scale(${currentScale})`;
      }
      const pct = `${Math.round(currentScale * 100)}%`;
      const zl = document.getElementById('journey-zoom-level');
      if (zl) zl.textContent = pct;
      const zp = document.getElementById('journey-zoom-pct');
      if (zp) zp.textContent = pct;
    }

    function zoomIn() {
      currentScale = Math.min(1.85, Math.round((currentScale + 0.15) * 100) / 100);
      applyTransform();
    }

    function zoomOut() {
      currentScale = Math.max(0.55, Math.round((currentScale - 0.15) * 100) / 100);
      applyTransform();
    }

    function resetReadable() {
      currentScale = 1;
      currentPan = { x: 0, y: 0 };
      applyTransform();
    }

    function fitJourney() {
      const vp = document.getElementById('journey-map-viewport');
      const nodes = (activeShipmentRow && activeShipmentRow.journey && activeShipmentRow.journey.nodes) || [];
      if (!vp || nodes.length === 0) {
        resetReadable();
        return;
      }
      const positions = nodes.map((n, i) => getNodePos(n.id, i));
      const minX = Math.min(...positions.map(p => p.x));
      const maxX = Math.max(...positions.map(p => p.x + JOURNEY_NODE_W));
      const minY = Math.min(...positions.map(p => p.y));
      const maxY = Math.max(...positions.map(p => p.y + JOURNEY_NODE_H));
      const pad = 48;
      const boxW = Math.max(240, maxX - minX + pad * 2);
      const boxH = Math.max(180, maxY - minY + pad * 2);
      const vw = vp.clientWidth || 960;
      const vh = vp.clientHeight || 520;
      const nextScale = Math.max(0.65, Math.min(1.25, Math.min(vw / boxW, vh / boxH)));
      const cx = (minX + maxX) / 2;
      const cy = (minY + maxY) / 2;
      currentScale = Math.round(nextScale * 100) / 100;
      currentPan = {
        x: Math.round(vw / 2 - cx * currentScale),
        y: Math.round(vh / 2 - cy * currentScale)
      };
      applyTransform();
    }

    function toggleUtilityBubble(force) {
      const el = document.getElementById('journey-utility-bubble');
      if (!el) return;
      if (typeof force === 'boolean') {
        el.classList.toggle('hidden', !force);
      } else {
        el.classList.toggle('hidden');
      }
    }

    function applySessionState(data) {
      currentSession = data || { authenticated: false, principal: {} };
      const authed = Boolean(currentSession.authenticated);

      const loginScreen = document.getElementById('customer-login-screen');
      const workspaceShell = document.getElementById('journey-workspace-shell');
      const logoutBtn = document.getElementById('btn-customer-logout');
      const pill = document.getElementById('session-pill');
      const brandTitle = document.getElementById('customer-brand-title');
      const brandSub = document.getElementById('customer-brand-sub');

      if (!authed) {
        if (loginScreen) loginScreen.classList.remove('hidden');
        if (workspaceShell) workspaceShell.classList.add('hidden');
        if (logoutBtn) logoutBtn.classList.add('hidden');
        if (pill) pill.textContent = 'Chưa đăng nhập';
        if (brandTitle) brandTitle.textContent = 'Cổng Hành Trình Lô Hàng Khách Hàng';
        if (brandSub) brandSub.textContent = 'Theo dõi trực quan trên hải đồ theo dữ liệu Trường Thành đã xác minh';
        return false;
      }

      const p = currentSession.principal || {};
      const customerDisplay = String(p.display_name || currentSession.label || 'Khách hàng');
      if (loginScreen) loginScreen.classList.add('hidden');
      if (workspaceShell) workspaceShell.classList.remove('hidden');
      if (logoutBtn) logoutBtn.classList.remove('hidden');
      if (pill) pill.textContent = customerDisplay;
      if (brandTitle) brandTitle.textContent = customerDisplay;
      if (brandSub) brandSub.textContent = 'Hành trình lô hàng và chứng từ đã được Trường Thành duyệt công bố';

      if (currentSession.default_shipment_id) {
        const inp = document.getElementById('shipment-input');
        if (inp && !inp.value) inp.value = String(currentSession.default_shipment_id);
      }
      return true;
    }

    async function loadSession() {
      const res = await apiFetch('/api/hexa/v0/session');
      const data = await res.json();
      if (applySessionState(data)) {
        await loadCustomerDashboard();
      }
    }

    let loginInFlight = false;
    async function loginCustomer() {
      if (loginInFlight) return;
      const username = (document.getElementById('cust-username').value || '').trim();
      const passcode = (document.getElementById('cust-passcode').value || '').trim();
      const note = document.getElementById('customer-auth-note');
      if (!username || !passcode) {
        if (note) note.textContent = 'Vui lòng nhập đầy đủ tài khoản và mật khẩu khách hàng.';
        return;
      }
      loginInFlight = true;
      if (note) note.textContent = 'Đang xác thực tài khoản...';
      try {
        const res = await apiFetch('/api/hexa/v0/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username, passcode })
        });
        if (!res.ok) {
          if (note) note.textContent = 'Thông tin đăng nhập không hợp lệ hoặc không thuộc phạm vi khách hàng.';
          return;
        }
        const loginData = await res.json();
        if (loginData && loginData.session_token) {
          setAuthToken(String(loginData.session_token));
        }
        document.getElementById('cust-passcode').value = '';
        if (loginData && loginData.authenticated) {
          applySessionState(loginData);
          if (loginData.dashboard && Array.isArray(loginData.dashboard.shipments)) {
            await renderDashboardData(loginData.dashboard);
          } else {
            await loadCustomerDashboard();
          }
        } else {
          await loadSession();
        }
      } finally {
        loginInFlight = false;
      }
    }

    async function logoutCustomer() {
      await apiFetch('/api/hexa/v0/auth/logout', { method: 'POST' });
      setAuthToken('');
      dashboardRows = [];
      activeShipmentRow = null;
      activePublication = null;
      selectedNodeId = null;
      await loadSession();
    }

    function showUnpublishedState(shipmentCode) {
      const zeroEl = document.getElementById('journey-zero-notice');
      const zeroTitle = document.getElementById('journey-zero-title');
      const zeroSummary = document.getElementById('journey-zero-summary');
      const nodesLayer = document.getElementById('journey-nodes-layer');
      const edgesSvg = document.getElementById('journey-edges-svg');
      const bubbleSlot = document.getElementById('journey-bubble-slot');

      if (nodesLayer) clearChildren(nodesLayer);
      if (edgesSvg) clearChildren(edgesSvg);
      if (bubbleSlot) clearChildren(bubbleSlot);

      if (zeroTitle) zeroTitle.textContent = 'Trường Thành chưa công bố thông tin cho lô này';
      if (zeroSummary) {
        zeroSummary.textContent = shipmentCode
          ? `Lô ${shipmentCode} hiện chưa có bản công bố hợp lệ hoặc đã được thu hồi. Hành trình và chứng từ sẽ hiển thị ngay khi Trường Thành duyệt công bố.`
          : 'Hành trình xác minh, báo giá bán và chứng từ sẽ xuất hiện trên hải đồ ngay khi Trường Thành duyệt công bố.';
      }
      if (zeroEl) {
        if (zeroTitle && zeroSummary && (!zeroEl.children || zeroEl.children.length === 0)) {
          zeroEl.appendChild(zeroTitle);
          zeroEl.appendChild(zeroSummary);
        }
        zeroEl.classList.remove('hidden');
      }

      document.getElementById('toolbar-id').textContent = shipmentCode || '—';
      document.getElementById('toolbar-here').textContent = 'Trường Thành chưa công bố thông tin cho lô này';
      document.getElementById('toolbar-eta').textContent = 'ETA kho: Chưa xác minh';
      document.getElementById('toolbar-next').textContent = 'Chờ Trường Thành công bố mốc xác minh';
    }

    function buildDebtLinesDom(debtSummary) {
      const wrap = document.createElement('div');
      wrap.style.fontSize = '11.5px';
      wrap.style.lineHeight = '1.38';
      const debt = debtSummary || {};
      const confirmed = debt.status === 'CONFIRMED' && typeof debt.total_payable === 'number';
      const cur = String(debt.currency || 'VND');

      const l1 = document.createElement('div');
      l1.textContent = confirmed
        ? `Tổng phải thanh toán: ${formatMoney(debt.total_payable, cur)}`
        : 'Tổng phải thanh toán: UNKNOWN / Chưa đối soát';

      const l2 = document.createElement('div');
      l2.style.color = confirmed ? '#15803d' : '#64748b';
      l2.textContent = confirmed
        ? `Đã thanh toán: ${formatMoney(debt.total_paid, cur)}`
        : 'Đã thanh toán: UNKNOWN / Chưa đối soát';

      const l3 = document.createElement('div');
      l3.style.fontWeight = '700';
      l3.style.color = confirmed ? (debt.remaining_balance > 0 ? '#b45309' : '#0f766e') : '#64748b';
      l3.textContent = confirmed
        ? `Còn phải thanh toán: ${formatMoney(debt.remaining_balance, cur)}`
        : 'Còn phải thanh toán: UNKNOWN / Chưa đối soát';

      wrap.appendChild(l1);
      wrap.appendChild(l2);
      wrap.appendChild(l3);
      return wrap;
    }

    async function renderDashboardData(body) {
      const tbody = document.getElementById('dash-shipments-tbody');
      const cardsBox = document.getElementById('dash-shipments-cards');
      const selectorBox = document.getElementById('customer-shipment-selector');
      const journeyView = document.getElementById('shipment-journey-view');
      const backBtn = document.getElementById('btn-back-to-dashboard');
      if (tbody) clearChildren(tbody);
      if (cardsBox) clearChildren(cardsBox);

      const summary = (body && body.summary) || {};
      const brandTitle = document.getElementById('customer-brand-title');
      if (brandTitle && body && body.customer_name) {
        brandTitle.textContent = String(body.customer_name);
      }
      document.getElementById('toolbar-customer').textContent = String((body && body.customer_name) || '');
      document.getElementById('kpi-active-tracking').textContent = String(summary.active_tracking ?? 0);
      document.getElementById('kpi-arriving-soon').textContent = String(
        summary.verified_warehouse_eta_count ?? summary.arriving_soon ?? 0
      );
      document.getElementById('kpi-customer-action').textContent = String(summary.customer_action_needed ?? 0);
      document.getElementById('kpi-customer-action-sub').textContent = String(
        summary.customer_action_status_label || 'Chưa có yêu cầu được xác nhận'
      );

      dashboardRows = Array.isArray(body && body.shipments) ? body.shipments : [];

      dashboardRows.forEach(row => {
        const sid = String(row.shipment_id || '');
        const modeText = String(row.transport_mode || 'ROAD');
        const cargoText = String(row.cargo_summary || '');
        const routeText = String(row.route_summary || '');
        const stageLabel = String(row.verified_stage_label || 'Chưa xác minh');
        const stageTitle = String(row.verified_stage_title || '');
        const etaLabel = String(row.verified_warehouse_eta_label || 'Chưa xác minh');
        const updatedLabel = String(row.last_updated_label || row.last_updated_at || 'Chưa cập nhật');
        const nextStepText = String(row.next_step || '');
        const contactText = String(row.contact_point || '');

        // 1. Desktop table row
        const tr = document.createElement('tr');
        tr.dataset.testid = `shipment-row-${sid}`;
        tr.addEventListener('click', () => selectShipmentForJourney(sid));

        const tdId = document.createElement('td');
        const strongId = document.createElement('strong');
        strongId.textContent = sid;
        tdId.appendChild(strongId);

        const tdCargo = document.createElement('td');
        const divCargo = document.createElement('div');
        divCargo.style.fontWeight = '700';
        divCargo.textContent = cargoText;
        const divRoute = document.createElement('div');
        divRoute.style.fontSize = '11.5px';
        divRoute.style.color = '#64748b';
        divRoute.textContent = routeText;
        tdCargo.appendChild(divCargo);
        tdCargo.appendChild(divRoute);

        const tdMode = document.createElement('td');
        const spanMode = document.createElement('span');
        spanMode.className = 'journey-toolbar-chip';
        spanMode.textContent = modeText;
        tdMode.appendChild(spanMode);

        const tdStage = document.createElement('td');
        const spanStage = document.createElement('span');
        spanStage.style.fontWeight = '700';
        spanStage.textContent = stageLabel;
        const divStageTitle = document.createElement('div');
        divStageTitle.style.fontSize = '11.5px';
        divStageTitle.style.color = '#475569';
        divStageTitle.textContent = stageTitle;
        tdStage.appendChild(spanStage);
        tdStage.appendChild(divStageTitle);

        const tdEta = document.createElement('td');
        tdEta.textContent = etaLabel;

        const tdDebt = document.createElement('td');
        tdDebt.dataset.testid = `shipment-debt-${sid}`;
        tdDebt.appendChild(buildDebtLinesDom(row.debt_summary));

        const tdUpdated = document.createElement('td');
        const divUpdated = document.createElement('div');
        divUpdated.textContent = updatedLabel;
        const divNext = document.createElement('div');
        divNext.style.fontSize = '11px';
        divNext.style.color = '#64748b';
        divNext.textContent = `${nextStepText} · Đầu mối: ${contactText}`;
        tdUpdated.appendChild(divUpdated);
        tdUpdated.appendChild(divNext);

        const tdBtn = document.createElement('td');
        const btnOpen = document.createElement('button');
        btnOpen.type = 'button';
        btnOpen.className = 'journey-toolbar-btn';
        btnOpen.dataset.testid = `btn-open-journey-${sid}`;
        btnOpen.textContent = 'Xem hành trình';
        btnOpen.addEventListener('click', (ev) => {
          if (ev && ev.stopPropagation) ev.stopPropagation();
          selectShipmentForJourney(sid);
        });
        tdBtn.appendChild(btnOpen);

        tr.appendChild(tdId);
        tr.appendChild(tdCargo);
        tr.appendChild(tdMode);
        tr.appendChild(tdStage);
        tr.appendChild(tdEta);
        tr.appendChild(tdDebt);
        tr.appendChild(tdUpdated);
        tr.appendChild(tdBtn);
        if (tbody) tbody.appendChild(tr);

        // 2. Mobile compact card (no horizontal table scrolling on 390x844)
        const card = document.createElement('article');
        card.className = 'shipment-card-mobile';
        card.dataset.testid = `shipment-card-${sid}`;
        card.addEventListener('click', () => selectShipmentForJourney(sid));

        const cardTop = document.createElement('div');
        cardTop.className = 'shipment-card-top';
        const cardId = document.createElement('strong');
        cardId.style.fontFamily = 'var(--mono)';
        cardId.style.fontSize = '13.5px';
        cardId.textContent = sid;
        const cardBadges = document.createElement('div');
        cardBadges.style.display = 'flex';
        cardBadges.style.gap = '6px';
        const badgeMode = document.createElement('span');
        badgeMode.className = 'journey-toolbar-chip';
        badgeMode.textContent = modeText;
        const badgeStage = document.createElement('span');
        badgeStage.className = 'journey-toolbar-chip journey-toolbar-here';
        badgeStage.textContent = stageLabel;
        cardBadges.appendChild(badgeMode);
        cardBadges.appendChild(badgeStage);
        cardTop.appendChild(cardId);
        cardTop.appendChild(cardBadges);

        const cardCargo = document.createElement('div');
        cardCargo.style.fontSize = '12.5px';
        cardCargo.style.fontWeight = '700';
        cardCargo.textContent = cargoText;

        const cardRoute = document.createElement('div');
        cardRoute.style.fontSize = '11.5px';
        cardRoute.style.color = '#475569';
        cardRoute.textContent = routeText;

        const cardMeta = document.createElement('div');
        cardMeta.className = 'shipment-card-meta';
        const metaEta = document.createElement('div');
        metaEta.textContent = `ETA xác minh: ${etaLabel}`;
        const metaUpdated = document.createElement('div');
        metaUpdated.textContent = `Cập nhật: ${updatedLabel}`;
        cardMeta.appendChild(metaEta);
        cardMeta.appendChild(metaUpdated);

        const cardDebt = document.createElement('div');
        cardDebt.style.background = '#f8fafc';
        cardDebt.style.padding = '7px 9px';
        cardDebt.style.borderRadius = '6px';
        cardDebt.style.border = '1px solid #e2e8f0';
        cardDebt.appendChild(buildDebtLinesDom(row.debt_summary));

        const cardBtn = document.createElement('button');
        cardBtn.type = 'button';
        cardBtn.className = 'btn-primary';
        cardBtn.style.width = '100%';
        cardBtn.textContent = 'Xem hành trình →';
        cardBtn.addEventListener('click', (ev) => {
          if (ev && ev.stopPropagation) ev.stopPropagation();
          selectShipmentForJourney(sid);
        });

        card.appendChild(cardTop);
        card.appendChild(cardCargo);
        card.appendChild(cardRoute);
        card.appendChild(cardMeta);
        card.appendChild(cardDebt);
        card.appendChild(cardBtn);
        if (cardsBox) cardsBox.appendChild(card);
      });

      if (dashboardRows.length === 0) {
        if (selectorBox) selectorBox.classList.add('hidden');
        if (backBtn) backBtn.classList.add('hidden');
        if (journeyView) journeyView.classList.remove('hidden');
        const fallbackId = (document.getElementById('shipment-input').value || '').trim();
        showUnpublishedState(fallbackId);
        return;
      }

      if (dashboardRows.length === 1) {
        if (selectorBox) selectorBox.classList.add('hidden');
        if (backBtn) backBtn.classList.add('hidden');
        if (journeyView) journeyView.classList.remove('hidden');
        await selectShipmentForJourney(String(dashboardRows[0].shipment_id || ''));
        return;
      }

      // 2+ shipments: open Dashboard overview as the first screen; hide Journey Map until a shipment is selected
      if (selectorBox) selectorBox.classList.remove('hidden');
      if (journeyView) journeyView.classList.add('hidden');
      if (backBtn) backBtn.classList.remove('hidden');
    }

    async function loadCustomerDashboard() {
      const tbody = document.getElementById('dash-shipments-tbody');
      const cardsBox = document.getElementById('dash-shipments-cards');
      const selectorBox = document.getElementById('customer-shipment-selector');
      const journeyView = document.getElementById('shipment-journey-view');
      const backBtn = document.getElementById('btn-back-to-dashboard');
      if (tbody) clearChildren(tbody);
      if (cardsBox) clearChildren(cardsBox);

      const res = await apiFetch('/api/hexa/v0/dashboard');
      if (!res.ok) {
        if (selectorBox) selectorBox.classList.add('hidden');
        if (backBtn) backBtn.classList.add('hidden');
        if (journeyView) journeyView.classList.remove('hidden');
        showUnpublishedState('');
        return;
      }

      const body = await res.json();
      await renderDashboardData(body);
    }

    function backToDashboard() {
      closeStageModal();
      const selectorBox = document.getElementById('customer-shipment-selector');
      const journeyView = document.getElementById('shipment-journey-view');
      if (journeyView) journeyView.classList.add('hidden');
      if (selectorBox) selectorBox.classList.remove('hidden');
    }

    async function selectShipmentForJourney(shipmentId) {
      const sid = String(shipmentId || '').trim();
      if (!sid) return;
      const inp = document.getElementById('shipment-input');
      if (inp) inp.value = sid;
      const selectorBox = document.getElementById('customer-shipment-selector');
      const journeyView = document.getElementById('shipment-journey-view');
      const backBtn = document.getElementById('btn-back-to-dashboard');
      if (selectorBox) selectorBox.classList.add('hidden');
      if (journeyView) journeyView.classList.remove('hidden');
      if (backBtn) {
        if (dashboardRows.length >= 2) backBtn.classList.remove('hidden');
        else backBtn.classList.add('hidden');
      }
      const matched = dashboardRows.find(r => String(r.shipment_id) === sid) || null;
      activeShipmentRow = matched;
      if (matched && matched.journey && Array.isArray(matched.journey.nodes) && matched.journey.nodes.length > 0) {
        activePublication = matched;
        selectedNodeId = String(matched.journey.current_stage_id || matched.journey.nodes[0].id || '');
        renderJourneyMapForShipment(matched, matched);
        fitJourney();
        return;
      }
      await loadShipment(sid);
    }

    async function openRequestedShipmentInput() {
      const sid = (document.getElementById('shipment-input').value || '').trim();
      if (!sid) return;
      await selectShipmentForJourney(sid);
    }

    async function loadShipment(shipmentId) {
      const sid = String(shipmentId || (document.getElementById('shipment-input').value || '')).trim();
      if (!sid) {
        showUnpublishedState('');
        return;
      }
      const res = await apiFetch(`/api/hexa/v0/shipments/${encodeURIComponent(sid)}`);
      if (!res.ok) {
        activePublication = null;
        showUnpublishedState(sid);
        return;
      }
      const pub = await res.json();
      activePublication = pub;
      const row = dashboardRows.find(r => String(r.shipment_id) === sid) || activeShipmentRow || {
        shipment_id: pub.reference || sid,
        transport_mode: pub.transport_mode || 'ROAD',
        route_summary: 'Tuyến vận chuyển đã công bố',
        cargo_summary: 'Hàng hóa theo chứng từ công bố',
        verified_stage_id: (pub.timeline && pub.timeline[0] && pub.timeline[0].stage) || '',
        verified_stage_label: (pub.timeline && pub.timeline[0] && pub.timeline[0].stage) || 'Đang xử lý',
        verified_stage_title: (pub.timeline && pub.timeline[0] && pub.timeline[0].title) || '',
        verified_warehouse_eta_label: 'Chưa xác minh',
        next_step: 'Đang vận chuyển theo hành trình — Chưa có yêu cầu được xác nhận',
        contact_point: 'CSKH Trường Thành',
        journey: { nodes: [], edges: [] },
        timeline: pub.timeline || [],
        documents: pub.documents || [],
        quote: pub.quote || null
      };
      activeShipmentRow = row;
      renderJourneyMapForShipment(row, pub);
    }

    function renderJourneyMapForShipment(row, pub) {
      const zeroEl = document.getElementById('journey-zero-notice');
      if (zeroEl) zeroEl.classList.add('hidden');

      document.getElementById('toolbar-id').textContent = String(row.shipment_id || pub.reference || '');
      document.getElementById('toolbar-mode').textContent = String(row.transport_mode || pub.transport_mode || 'ROAD');
      document.getElementById('toolbar-route').textContent = `${String(row.route_summary || '')} · ${String(row.cargo_summary || '')}`;
      document.getElementById('toolbar-here').textContent = `Đang ở: ${String(row.verified_stage_label || 'Chưa xác minh')}`;
      document.getElementById('toolbar-eta').textContent = `ETA kho: ${String(row.verified_warehouse_eta_label || 'Chưa xác minh')}`;
      document.getElementById('toolbar-next').textContent = `${String(row.next_step || '')} · Đầu mối: ${String(row.contact_point || '')}`;

      const docs = (pub && Array.isArray(pub.documents)) ? pub.documents : (row.documents || []);
      const quote = (pub && pub.quote) ? pub.quote : row.quote;
      document.getElementById('utility-doc-count').textContent = `${docs.length} tệp`;
      document.getElementById('utility-docs-sub').textContent = `${docs.length} tệp đã duyệt`;
      document.getElementById('utility-quote-sub').textContent = quote ? formatVnd(quote.selling_total_vnd) : 'Chưa công bố';

      const journey = row.journey || { nodes: [], edges: [] };
      const nodes = Array.isArray(journey.nodes) ? journey.nodes : [];
      const edges = Array.isArray(journey.edges) && journey.edges.length > 0
        ? journey.edges
        : nodes.slice(0, -1).map((n, idx) => ({ from: n.id, to: nodes[idx + 1].id }));

      const posById = {};
      const nodeById = {};
      nodes.forEach((n, idx) => {
        posById[n.id] = getNodePos(n.id, idx);
        nodeById[n.id] = n;
      });

      const edgesSvg = document.getElementById('journey-edges-svg');
      if (edgesSvg) {
        clearChildren(edgesSvg);
        edges.forEach(e => {
          const a = posById[e.from];
          const b = posById[e.to];
          if (!a || !b) return;
          const fromNode = nodeById[e.from] || {};
          const pathEl = document.createElementNS
            ? document.createElementNS('http://www.w3.org/2000/svg', 'path')
            : document.createElement('path');
          const cls = ['journey-edge', fromNode.completed ? 'journey-edge-done' : ''].filter(Boolean).join(' ');
          pathEl.setAttribute('class', cls);
          pathEl.setAttribute('d', journeyEdgePath(a, b));
          edgesSvg.appendChild(pathEl);
        });
      }

      const nodesLayer = document.getElementById('journey-nodes-layer');
      if (nodesLayer) {
        clearChildren(nodesLayer);
        nodes.forEach((n, idx) => {
          const p = posById[n.id];
          const btn = document.createElement('button');
          btn.type = 'button';
          btn.dataset.testid = `journey-node-${n.id}`;
          btn.setAttribute('data-state', String(n.state || 'UPCOMING'));
          const classes = ['journey-node'];
          if (n.current) classes.push('journey-node-here');
          if (selectedNodeId === n.id) classes.push('journey-node-selected');
          btn.className = classes.join(' ');
          btn.style.left = `${p.x}px`;
          btn.style.top = `${p.y}px`;
          btn.style.width = `${JOURNEY_NODE_W}px`;
          btn.style.height = `${JOURNEY_NODE_H}px`;

          const topDiv = document.createElement('div');
          topDiv.className = 'journey-node-top';
          const idxSpan = document.createElement('span');
          idxSpan.className = 'journey-node-idx';
          idxSpan.textContent = String(n.index !== undefined ? n.index : idx).padStart(2, '0');
          topDiv.appendChild(idxSpan);

          const titleDiv = document.createElement('div');
          titleDiv.className = 'journey-node-title';
          titleDiv.textContent = String(n.label || '').toUpperCase();

          const footDiv = document.createElement('div');
          footDiv.className = 'journey-node-foot';
          const stSpan = document.createElement('span');
          stSpan.className = 'journey-node-status';
          stSpan.textContent = JOURNEY_NODE_STATUS[n.state] || 'CHƯA BẮT ĐẦU';
          footDiv.appendChild(stSpan);

          const stageDocs = Array.isArray(n.stage_documents) ? n.stage_documents : [];
          const stageCmts = Array.isArray(n.stage_comments) ? n.stage_comments : [];
          if (stageDocs.length > 0 || stageCmts.length > 0) {
            const cntSpan = document.createElement('span');
            cntSpan.className = 'journey-node-count';
            cntSpan.textContent = `📎${stageDocs.length} 💬${stageCmts.length}`;
            footDiv.appendChild(cntSpan);
          }

          btn.appendChild(topDiv);
          btn.appendChild(titleDiv);
          btn.appendChild(footDiv);
          btn.addEventListener('click', () => selectJourneyNode(String(n.id)));
          nodesLayer.appendChild(btn);
        });
      }

      if (selectedNodeId && nodeById[selectedNodeId]) {
        renderNodeBubble(nodeById[selectedNodeId], posById[selectedNodeId], docs);
      } else {
        const bubbleSlot = document.getElementById('journey-bubble-slot');
        if (bubbleSlot) clearChildren(bubbleSlot);
      }
    }

    function selectJourneyNode(nodeId) {
      if (!activeShipmentRow || !activeShipmentRow.journey) return;
      selectedNodeId = String(nodeId);
      renderJourneyMapForShipment(activeShipmentRow, activePublication);
    }

    function renderNodeBubble(node, pos, docs) {
      const bubbleSlot = document.getElementById('journey-bubble-slot');
      if (!bubbleSlot) return;
      clearChildren(bubbleSlot);
      if (!node || !pos) return;

      const bubbleW = 290;
      const left = Math.max(18, Math.min(1080 - bubbleW - 18, pos.x + JOURNEY_NODE_W / 2 - bubbleW / 2));
      const preferAbove = pos.y > 195;
      const top = preferAbove ? Math.max(12, pos.y - 12) : pos.y + JOURNEY_NODE_H + 12;

      const wrap = document.createElement('div');
      wrap.className = `journey-bubble ${preferAbove ? 'journey-bubble-above' : 'journey-bubble-below'}`;
      wrap.dataset.testid = 'journey-bubble';
      wrap.setAttribute('data-node', String(node.id));
      wrap.style.left = `${left}px`;
      wrap.style.top = `${top}px`;
      wrap.style.width = `${bubbleW}px`;

      const head = document.createElement('div');
      head.className = 'journey-bubble-head';
      const headTextWrap = document.createElement('div');
      const kicker = document.createElement('span');
      kicker.className = 'journey-bubble-kicker';
      kicker.textContent = String(node.label || '').toUpperCase();
      const stateSpan = document.createElement('span');
      stateSpan.className = 'journey-bubble-state';
      stateSpan.textContent = JOURNEY_NODE_STATUS[node.state] || 'CHƯA BẮT ĐẦU';
      headTextWrap.appendChild(kicker);
      headTextWrap.appendChild(stateSpan);

      const closeBtn = document.createElement('button');
      closeBtn.type = 'button';
      closeBtn.className = 'journey-bubble-close';
      closeBtn.dataset.testid = 'journey-bubble-close';
      closeBtn.textContent = '✕';
      closeBtn.addEventListener('click', () => {
        selectedNodeId = null;
        renderJourneyMapForShipment(activeShipmentRow, activePublication);
      });
      head.appendChild(headTextWrap);
      head.appendChild(closeBtn);

      const listDiv = document.createElement('div');
      listDiv.className = 'journey-bubble-list';

      const taskStage = document.createElement('button');
      taskStage.type = 'button';
      taskStage.className = `journey-bubble-task ${node.completed ? 'is-done' : ''}`;
      taskStage.dataset.testid = 'journey-bubble-task-stage';
      const dot1 = document.createElement('span');
      dot1.className = `journey-bubble-dot ${node.completed ? 'dot-done' : (node.current ? 'dot-info' : 'dot-pending')}`;
      dot1.textContent = node.completed ? '✓' : (node.current ? '◐' : '·');
      const body1 = document.createElement('span');
      body1.className = 'journey-bubble-task-body';
      const title1 = document.createElement('span');
      title1.className = 'journey-bubble-title';
      title1.textContent = String(node.evidence || 'Chưa có mốc xác minh được công bố');
      const meta1 = document.createElement('span');
      meta1.className = 'journey-bubble-meta';
      meta1.textContent = node.occurred_at ? `Xác minh: ${String(node.occurred_at)}` : 'Chưa có mốc thời gian xác minh';
      body1.appendChild(title1);
      body1.appendChild(meta1);
      taskStage.appendChild(dot1);
      taskStage.appendChild(body1);
      taskStage.addEventListener('click', () => openStageModal(String(node.id), 'info'));

      const taskDocs = document.createElement('button');
      taskDocs.type = 'button';
      taskDocs.className = `journey-bubble-task ${docs.length > 0 ? 'is-done' : ''}`;
      taskDocs.dataset.testid = 'journey-bubble-task-docs';
      const dot2 = document.createElement('span');
      dot2.className = `journey-bubble-dot ${docs.length > 0 ? 'dot-done' : 'dot-pending'}`;
      dot2.textContent = docs.length > 0 ? '📎' : '·';
      const body2 = document.createElement('span');
      body2.className = 'journey-bubble-task-body';
      const title2 = document.createElement('span');
      title2.className = 'journey-bubble-title';
      title2.textContent = `Chứng từ được phép tải (${docs.length} tệp)`;
      const meta2 = document.createElement('span');
      meta2.className = 'journey-bubble-meta';
      meta2.textContent = 'Nhấn để xem chi tiết chỉ-đọc và tải PDF đúng phiên bản';
      body2.appendChild(title2);
      body2.appendChild(meta2);
      taskDocs.appendChild(dot2);
      taskDocs.appendChild(body2);
      taskDocs.addEventListener('click', () => openStageModal(String(node.id), 'docs'));

      listDiv.appendChild(taskStage);
      listDiv.appendChild(taskDocs);

      const foot = document.createElement('div');
      foot.className = 'journey-bubble-foot';
      const openBtn = document.createElement('button');
      openBtn.type = 'button';
      openBtn.className = 'journey-bubble-open';
      openBtn.dataset.testid = 'journey-open-workspace';
      openBtn.textContent = 'Xem chi tiết chỉ-đọc →';
      openBtn.addEventListener('click', () => openStageModal(String(node.id), 'info'));
      foot.appendChild(openBtn);

      wrap.appendChild(head);
      wrap.appendChild(listDiv);
      wrap.appendChild(foot);
      bubbleSlot.appendChild(wrap);
    }

    function openStageModal(nodeId, tab) {
      if (!activeShipmentRow) return;
      const nodes = (activeShipmentRow.journey && activeShipmentRow.journey.nodes) || [];
      const node = nodes.find(n => String(n.id) === String(nodeId)) || nodes[0] || {
        id: nodeId,
        label: nodeId,
        state: 'UPCOMING',
        evidence: 'Chưa có mốc xác minh được công bố',
        occurred_at: ''
      };
      const modalLayer = document.getElementById('journey-modal-layer');
      if (modalLayer) modalLayer.classList.remove('hidden');

      document.getElementById('modal-kicker').textContent = `CHI TIẾT CÔNG ĐOẠN · ${String(activeShipmentRow.shipment_id || '')}`;
      document.getElementById('modal-title').textContent = String(node.label || '');
      document.getElementById('modal-sub').textContent = node.occurred_at
        ? `Thời điểm xác minh: ${String(node.occurred_at)}`
        : 'Chưa có thời điểm xác minh được công bố cho công đoạn này';
      document.getElementById('modal-badge').textContent = JOURNEY_NODE_STATUS[node.state] || 'CHƯA BẮT ĐẦU';

      renderReadonlyModalBody(node, tab || 'info');
    }

    function openGlobalModal(tab) {
      if (!activeShipmentRow) return;
      const nodes = (activeShipmentRow.journey && activeShipmentRow.journey.nodes) || [];
      const currentNode = nodes.find(n => n.current) || nodes[0] || {
        id: 'overview',
        label: 'Tổng quan Hồ sơ & Chứng từ đã công bố',
        state: 'CURRENT',
        evidence: String(activeShipmentRow.verified_stage_title || ''),
        occurred_at: String(activeShipmentRow.last_updated_at || '')
      };
      openStageModal(currentNode.id, tab || 'docs');
    }

    function closeStageModal() {
      const modalLayer = document.getElementById('journey-modal-layer');
      if (modalLayer) modalLayer.classList.add('hidden');
    }

    function renderReadonlyModalBody(node, activeTab) {
      const container = document.getElementById('journey-modal-body');
      if (!container) return;
      clearChildren(container);

      const row = activeShipmentRow || {};
      const pub = activePublication || {};
      const sid = String(row.shipment_id || pub.reference || '');
      const docs = Array.isArray(pub.documents) ? pub.documents : (row.documents || []);
      const timeline = Array.isArray(pub.timeline) ? pub.timeline : (row.timeline || []);
      const quote = pub.quote || row.quote || null;
      const stageId = String(node.id || 'pickup');

      const grid = document.createElement('div');
      grid.className = 'readonly-grid';

      const items = [
        ['Trạng thái công đoạn', JOURNEY_NODE_STATUS[node.state] || 'CHƯA BẮT ĐẦU'],
        ['Thời điểm xác minh', String(node.occurred_at || 'Chưa xác nhận')],
        ['ETA kho đã xác minh', String(row.verified_warehouse_eta_label || 'Chưa xác minh')],
        ['Đầu mối Trường Thành', String(row.contact_point || 'CSKH Trường Thành')],
        ['Báo giá bán đã duyệt', quote ? `${formatVnd(quote.selling_total_vnd)} (${String(quote.id || '')} · v${String(quote.version || '')})` : 'Chưa công bố']
      ];
      items.forEach(([lbl, val]) => {
        const box = document.createElement('div');
        box.className = 'readonly-box';
        const l = document.createElement('div');
        l.className = 'lbl';
        l.textContent = lbl;
        const v = document.createElement('div');
        v.className = 'val';
        v.textContent = val;
        box.appendChild(l);
        box.appendChild(v);
        grid.appendChild(box);
      });
      container.appendChild(grid);

      const evBox = document.createElement('div');
      evBox.className = 'readonly-box';
      evBox.style.marginBottom = '14px';
      const evLbl = document.createElement('div');
      evLbl.className = 'lbl';
      evLbl.textContent = 'Nội dung đã công bố tại công đoạn này';
      const evVal = document.createElement('div');
      evVal.className = 'val';
      evVal.textContent = String(node.evidence || 'Chưa có mốc xác minh được công bố');
      evBox.appendChild(evLbl);
      evBox.appendChild(evVal);
      container.appendChild(evBox);

      // Node 00 — KẾ HOẠCH (before pickup)
      if (stageId === 'plan') {
        const plan = node.plan_detail || row.plan_detail || {};
        const ent = plan.entrusted_import || { applicable: false };
        const planSec = document.createElement('div');
        planSec.dataset.testid = 'stage-plan-detail';
        planSec.style.marginBottom = '14px';

        const planTitle = document.createElement('h4');
        planTitle.style.margin = '12px 0 6px';
        planTitle.style.fontSize = '13px';
        planTitle.textContent = '00 · KẾ HOẠCH THƯƠNG MẠI & ĐIỀU KIỆN TRƯỚC VẬN CHUYỂN';
        planSec.appendChild(planTitle);

        const planGrid = document.createElement('div');
        planGrid.className = 'readonly-grid';
        const planRows = [
          ['Báo giá & Xác nhận báo giá', `${String(plan.quote_no || 'Chưa công bố')} — ${String(plan.quote_confirmation_status || 'Chưa xác nhận')}`],
          ['Hợp đồng & Tình trạng ký kết', `${String(plan.contract_no || 'Chưa xác nhận')} — ${String(plan.contract_status || 'Chưa xác nhận')}`],
          ['Điều kiện thanh toán', String(plan.payment_terms || 'Chưa xác nhận')],
          ['Phân loại dịch vụ', ent.applicable ? 'Ủy thác nhập khẩu (có điều kiện tiền hàng ứng trước)' : 'Dịch vụ vận chuyển thông thường (Không áp dụng tiền hàng ủy thác)']
        ];
        if (ent.applicable) {
          const reqAmt = ent.goods_advance_required !== undefined ? ent.goods_advance_required : ent.required_amount;
          const recAmt = ent.goods_advance_received !== undefined ? ent.goods_advance_received : ent.confirmed_received_amount;
          const remAmt = ent.goods_advance_remaining !== undefined ? ent.goods_advance_remaining : ent.remaining_shortfall;
          planRows.push(['Tiền hàng cần ứng trước cho Trường Thành', formatMoney(reqAmt, ent.currency)]);
          planRows.push(['Số tiền hàng Trường Thành đã xác nhận nhận', formatMoney(recAmt, ent.currency)]);
          planRows.push(['Số tiền hàng còn thiếu', formatMoney(remAmt, ent.currency)]);
          planRows.push(['Trạng thái xác nhận tiền hàng', String(ent.status_label || 'Chưa xác nhận')]);
        }
        planRows.forEach(([pl, pv]) => {
          const pbox = document.createElement('div');
          pbox.className = 'readonly-box';
          const lEl = document.createElement('div');
          lEl.className = 'lbl';
          lEl.textContent = pl;
          const vEl = document.createElement('div');
          vEl.className = 'val';
          vEl.textContent = pv;
          pbox.appendChild(lEl);
          pbox.appendChild(vEl);
          planGrid.appendChild(pbox);
        });
        planSec.appendChild(planGrid);
        container.appendChild(planSec);
      }

      // Node 06 — THANH TOÁN & ĐỐI SOÁT (after delivery)
      if (stageId === 'finance-reconciliation') {
        const fin = node.finance_detail || row.finance_detail || row.debt_summary || {};
        const confirmed = fin.reconciliation_status === 'CONFIRMED' || fin.status === 'CONFIRMED';
        const cur = String(fin.currency || 'VND');
        const finSec = document.createElement('div');
        finSec.dataset.testid = 'stage-finance-detail';
        finSec.style.marginBottom = '14px';

        const finTitle = document.createElement('h4');
        finTitle.style.margin = '12px 0 6px';
        finTitle.style.fontSize = '13px';
        finTitle.textContent = '06 · THANH TOÁN & ĐỐI SOÁT CÔNG NỢ DỊCH VỤ';
        finSec.appendChild(finTitle);

        const finGrid = document.createElement('div');
        finGrid.className = 'readonly-grid';
        const finRows = [
          ['Tổng phải thanh toán (đã đối soát)', confirmed ? formatMoney(fin.total_payable, cur) : 'UNKNOWN / Chưa đối soát'],
          ['Tổng đã thanh toán & phân bổ đúng lô', confirmed ? formatMoney(fin.total_paid, cur) : 'UNKNOWN / Chưa đối soát'],
          ['Còn phải thanh toán', confirmed ? formatMoney(fin.remaining_balance, cur) : 'UNKNOWN / Chưa đối soát'],
          ['Ngày cập nhật & Trạng thái đối soát', `${String(fin.updated_at || 'Chưa xác nhận')} · ${String(fin.reconciliation_status_label || fin.status_label || 'UNKNOWN / Chưa đối soát')}`]
        ];
        finRows.forEach(([fl, fv]) => {
          const fbox = document.createElement('div');
          fbox.className = 'readonly-box';
          const lEl = document.createElement('div');
          lEl.className = 'lbl';
          lEl.textContent = fl;
          const vEl = document.createElement('div');
          vEl.className = 'val';
          vEl.textContent = fv;
          fbox.appendChild(lEl);
          fbox.appendChild(vEl);
          finGrid.appendChild(fbox);
        });
        finSec.appendChild(finGrid);
        container.appendChild(finSec);
      }

      // Section 1: TRAO ĐỔI (Stage-scoped comments between Customer and TT)
      const cmtSec = document.createElement('div');
      cmtSec.dataset.testid = 'stage-comments-section';
      cmtSec.style.marginBottom = '14px';

      const cmtTitle = document.createElement('h4');
      cmtTitle.style.margin = '12px 0 6px';
      cmtTitle.style.fontSize = '13px';
      cmtTitle.textContent = `TRAO ĐỔI CÔNG ĐOẠN (${String(node.label || stageId)})`;
      cmtSec.appendChild(cmtTitle);

      const stageComments = Array.isArray(node.stage_comments) ? node.stage_comments : [];
      const cmtList = document.createElement('div');
      cmtList.style.display = 'grid';
      cmtList.style.gap = '6px';
      cmtList.style.marginBottom = '8px';
      if (stageComments.length === 0) {
        const emptyCmt = document.createElement('div');
        emptyCmt.className = 'readonly-box';
        emptyCmt.textContent = 'Chưa có trao đổi nào tại công đoạn này.';
        cmtList.appendChild(emptyCmt);
      } else {
        stageComments.forEach(c => {
          const cbox = document.createElement('div');
          cbox.className = 'readonly-box';
          const cHead = document.createElement('div');
          cHead.className = 'lbl';
          cHead.textContent = `${String(c.author_display || c.author_side || '')} · ${String(c.created_at || '')}`;
          const cBody = document.createElement('div');
          cBody.className = 'val';
          cBody.textContent = String(c.comment || '');
          cbox.appendChild(cHead);
          cbox.appendChild(cBody);
          cmtList.appendChild(cbox);
        });
      }
      cmtSec.appendChild(cmtList);

      const formBox = document.createElement('div');
      formBox.className = 'readonly-box';
      formBox.style.display = 'grid';
      formBox.style.gap = '6px';

      const formLbl = document.createElement('div');
      formLbl.className = 'lbl';
      formLbl.textContent = 'Gửi ghi chú trao đổi hoặc đính kèm chứng từ/ủy nhiệm chi cho công đoạn này (Chờ TT xác minh)';
      formBox.appendChild(formLbl);

      const cmtInput = document.createElement('input');
      cmtInput.type = 'text';
      cmtInput.id = 'stage-comment-input';
      cmtInput.placeholder = 'Nhập nội dung trao đổi tại công đoạn này...';
      cmtInput.style.width = '100%';
      cmtInput.style.padding = '7px 9px';
      cmtInput.style.border = '1px solid #cbd5e1';
      cmtInput.style.borderRadius = '6px';
      cmtInput.style.boxSizing = 'border-box';
      formBox.appendChild(cmtInput);

      const fileRow = document.createElement('div');
      fileRow.style.display = 'flex';
      fileRow.style.gap = '8px';
      fileRow.style.alignItems = 'center';
      fileRow.style.flexWrap = 'wrap';

      const fileInput = document.createElement('input');
      fileInput.type = 'file';
      fileInput.id = 'stage-file-input';
      fileInput.accept = '.pdf,.png,.jpg,.jpeg,.webp';
      fileInput.style.fontSize = '11.5px';
      fileRow.appendChild(fileInput);

      const btnSubmitCollab = document.createElement('button');
      btnSubmitCollab.type = 'button';
      btnSubmitCollab.id = 'btn-submit-stage-collab';
      btnSubmitCollab.className = 'btn-primary';
      btnSubmitCollab.style.padding = '6px 12px';
      btnSubmitCollab.style.fontSize = '12px';
      btnSubmitCollab.textContent = 'Gửi trao đổi / Đính chứng từ';
      btnSubmitCollab.addEventListener('click', () => submitStageCollaboration(sid, stageId));
      fileRow.appendChild(btnSubmitCollab);

      const statusSpan = document.createElement('div');
      statusSpan.id = 'stage-collab-status';
      statusSpan.style.fontSize = '11.5px';
      statusSpan.style.color = '#1d4ed8';

      formBox.appendChild(fileRow);
      formBox.appendChild(statusSpan);
      cmtSec.appendChild(formBox);
      container.appendChild(cmtSec);

      // Section 2: CHỨNG TỪ (Stage documents + published shipment documents)
      const docHeading = document.createElement('h4');
      docHeading.style.margin = '14px 0 6px';
      docHeading.style.fontSize = '13px';
      docHeading.textContent = 'CHỨNG TỪ CÔNG ĐOẠN & HỒ SƠ ĐƯỢC PHÉP TẢI';
      container.appendChild(docHeading);

      const stageDocs = Array.isArray(node.stage_documents) ? node.stage_documents : [];
      const combinedDocs = [];
      const seenDocIds = {};
      stageDocs.forEach(d => {
        const did = String(d.id || '');
        if (did && !seenDocIds[did]) {
          seenDocIds[did] = true;
          combinedDocs.push(d);
        }
      });
      docs.forEach(d => {
        const did = String(d.id || '');
        if (did && !seenDocIds[did]) {
          seenDocIds[did] = true;
          combinedDocs.push(Object.assign({ verification_label: 'Đã xác minh & công bố' }, d));
        }
      });

      const table = document.createElement('table');
      table.className = 'doc-list-table';
      table.dataset.testid = 'stage-documents-section';
      const thead = document.createElement('thead');
      const htr = document.createElement('tr');
      ['Mã chứng từ', 'Loại', 'Tên chứng từ', 'Trạng thái xác minh', 'Tải tệp'].forEach(h => {
        const th = document.createElement('th');
        th.textContent = h;
        htr.appendChild(th);
      });
      thead.appendChild(htr);
      table.appendChild(thead);

      const tbody = document.createElement('tbody');
      if (combinedDocs.length === 0) {
        const tr = document.createElement('tr');
        const td = document.createElement('td');
        td.colSpan = 5;
        td.textContent = 'Chưa có chứng từ được công bố tại công đoạn này.';
        tr.appendChild(td);
        tbody.appendChild(tr);
      } else {
        combinedDocs.forEach(doc => {
          const tr = document.createElement('tr');
          const tdId = document.createElement('td');
          tdId.textContent = String(doc.id || '');
          const tdKind = document.createElement('td');
          tdKind.textContent = String(doc.kind || '');
          const tdTitle = document.createElement('td');
          tdTitle.textContent = String(doc.title || '');
          const tdVer = document.createElement('td');
          tdVer.textContent = String(doc.verification_label || doc.version || 'Đã xác minh & công bố');
          const tdDl = document.createElement('td');
          const btnDl = document.createElement('button');
          btnDl.type = 'button';
          btnDl.className = 'btn-primary';
          btnDl.style.padding = '5px 10px';
          btnDl.style.fontSize = '12px';
          btnDl.textContent = '⬇ Tải PDF';
          btnDl.addEventListener('click', () => triggerDownload(
            sid,
            String(doc.id || ''),
            String(doc.version || 'v1')
          ));
          tdDl.appendChild(btnDl);

          tr.appendChild(tdId);
          tr.appendChild(tdKind);
          tr.appendChild(tdTitle);
          tr.appendChild(tdVer);
          tr.appendChild(tdDl);
          tbody.appendChild(tr);
        });
      }
      table.appendChild(tbody);
      container.appendChild(table);

      const tlTitle = document.createElement('h4');
      tlTitle.style.margin = '14px 0 6px';
      tlTitle.style.fontSize = '13px';
      tlTitle.textContent = 'Nhật ký mốc tiến độ Trường Thành đã xác minh & công bố';
      container.appendChild(tlTitle);

      const tlList = document.createElement('div');
      tlList.style.display = 'grid';
      tlList.style.gap = '6px';
      if (timeline.length === 0) {
        const emptyTl = document.createElement('div');
        emptyTl.className = 'readonly-box';
        emptyTl.textContent = 'Trường Thành chưa công bố mốc tiến độ nào cho lô này.';
        tlList.appendChild(emptyTl);
      } else {
        timeline.forEach(ev => {
          const item = document.createElement('div');
          item.className = 'readonly-box';
          const top = document.createElement('div');
          top.className = 'lbl';
          top.textContent = `${String(ev.stage || '')} · ${String(ev.occurred_at || '')} · Phiên bản ${String(ev.version || '')}`;
          const txt = document.createElement('div');
          txt.className = 'val';
          txt.textContent = String(ev.title || '');
          item.appendChild(top);
          item.appendChild(txt);
          tlList.appendChild(item);
        });
      }
      container.appendChild(tlList);
    }

    function readFileAsBase64(file) {
      return new Promise((resolve, reject) => {
        if (!file || typeof FileReader === 'undefined') {
          resolve('');
          return;
        }
        const reader = new FileReader();
        reader.onload = () => {
          const result = String(reader.result || '');
          const commaIdx = result.indexOf(',');
          resolve(commaIdx >= 0 ? result.slice(commaIdx + 1) : result);
        };
        reader.onerror = () => reject(new Error('READ_ERROR'));
        reader.readAsDataURL(file);
      });
    }

    async function submitStageCollaboration(shipmentId, stageId) {
      const cmtInp = document.getElementById('stage-comment-input');
      const fileInp = document.getElementById('stage-file-input');
      const statusEl = document.getElementById('stage-collab-status');
      const comment = cmtInp ? String(cmtInp.value || '').trim() : '';
      const fileObj = (fileInp && fileInp.files && fileInp.files[0]) ? fileInp.files[0] : null;
      if (!comment && !fileObj) {
        if (statusEl) statusEl.textContent = 'Vui lòng nhập nội dung trao đổi hoặc chọn tệp chứng từ.';
        return;
      }
      if (statusEl) statusEl.textContent = 'Đang gửi thông tin...';
      let fileBase64 = '';
      let fileName = '';
      let mime = 'application/pdf';
      if (fileObj) {
        fileName = String(fileObj.name || 'customer-upload.pdf');
        mime = String(fileObj.type || 'application/pdf');
        fileBase64 = await readFileAsBase64(fileObj);
      }
      const res = await apiFetch(
        `/api/hexa/v0/shipments/${encodeURIComponent(shipmentId)}/stages/${encodeURIComponent(stageId)}/submissions`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ comment, file_name: fileName, mime, file_base64: fileBase64 })
        }
      );
      if (!res.ok) {
        if (statusEl) statusEl.textContent = 'Không thể gửi thông tin (tệp không hợp lệ hoặc phiên hết hạn).';
        return;
      }
      if (cmtInp) cmtInp.value = '';
      if (fileInp) fileInp.value = '';
      if (statusEl) statusEl.textContent = 'Đã ghi nhận hồ sơ khách nộp (Chờ Trường Thành xác minh).';
      const dashRes = await apiFetch('/api/hexa/v0/dashboard');
      if (dashRes.ok) {
        const dashBody = await dashRes.json();
        dashboardRows = Array.isArray(dashBody.shipments) ? dashBody.shipments : [];
        const updatedRow = dashboardRows.find(r => String(r.shipment_id) === String(shipmentId)) || null;
        if (updatedRow) {
          activeShipmentRow = updatedRow;
          activePublication = updatedRow;
          renderJourneyMapForShipment(updatedRow, updatedRow);
          openStageModal(stageId, 'info');
        }
      }
    }

    async function triggerDownload(shipmentId, docId, version) {
      const url = `/api/hexa/v0/shipments/${encodeURIComponent(shipmentId)}/documents/${encodeURIComponent(docId)}/download?version=${encodeURIComponent(version)}`;
      const res = await apiFetch(url);
      const banner = document.getElementById('download-status-banner');
      if (banner) banner.classList.remove('hidden');
      if (res.ok) {
        const blob = await res.blob();
        if (banner) banner.textContent = `Đã tải chứng từ ${docId} (${version}) thành công (${blob.size} bytes PDF).`;
        if (typeof URL !== 'undefined' && URL.createObjectURL) {
          const dlUrl = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = dlUrl;
          a.download = `${docId}-${version}.pdf`;
          document.body.appendChild(a);
          a.click();
          if (a.remove) a.remove();
          URL.revokeObjectURL(dlUrl);
        }
      } else {
        if (banner) banner.textContent = `Chứng từ ${docId} (${version}) hiện không nằm trong danh mục được phép tải.`;
      }
    }

    window.addEventListener('DOMContentLoaded', async () => {
      const vp = document.getElementById('journey-map-viewport');
      if (vp && vp.addEventListener) {
        let dragState = null;
        vp.addEventListener('pointerdown', (e) => {
          if (e.target && e.target.closest && e.target.closest('.journey-node, .journey-zoom-bar, .journey-bubble')) return;
          dragState = { startX: e.clientX, startY: e.clientY, origX: currentPan.x, origY: currentPan.y };
          vp.style.cursor = 'grabbing';
        });
        vp.addEventListener('pointermove', (e) => {
          if (!dragState) return;
          currentPan = {
            x: dragState.origX + (e.clientX - dragState.startX),
            y: dragState.origY + (e.clientY - dragState.startY)
          };
          applyTransform();
        });
        const endDrag = () => { dragState = null; vp.style.cursor = 'grab'; };
        vp.addEventListener('pointerup', endDrag);
        vp.addEventListener('pointercancel', endDrag);
        vp.addEventListener('wheel', (e) => {
          if (!e.ctrlKey && !e.metaKey) return;
          e.preventDefault();
          const delta = e.deltaY < 0 ? 0.1 : -0.1;
          currentScale = Math.max(0.55, Math.min(1.85, Math.round((currentScale + delta) * 100) / 100));
          applyTransform();
        }, { passive: false });
      }
      await loadSession();
    });
  </script>
</body>
</html>
"""


def render_tt_login_html() -> str:
    """Minimal login page for authorized Trường Thành staff (/tt/login)."""
    return """<!doctype html>
<html lang="vi">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Trường Thành — Đăng nhập Bàn Duyệt Công Bố Nội Bộ</title>
  <style>
    body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f2236; color: #0f172a; display: grid; place-items: center; min-height: 100vh; }
    .card { width: 100%; max-width: 420px; background: #fff; border-radius: 10px; padding: 24px 26px; box-shadow: 0 20px 45px rgba(0,0,0,0.35); }
    h1 { margin: 0 0 12px; font-size: 17px; color: #0f2942; }
    input { width: 100%; padding: 9px 11px; margin-bottom: 12px; border: 1px solid #cbd5e1; border-radius: 6px; box-sizing: border-box; }
    button { width: 100%; padding: 9px 14px; border: none; border-radius: 6px; background: #0f4c81; color: #fff; font-weight: 700; cursor: pointer; }
    #tt-msg { margin-top: 10px; font-size: 12.5px; color: #b91c1c; font-weight: 600; }
  </style>
</head>
<body>
  <div class="card">
    <h1>Bàn Duyệt Công Bố Nội Bộ Trường Thành</h1>
    <form onsubmit="event.preventDefault(); loginTt();">
      <input id="tt-user" type="text" placeholder="Tài khoản nội bộ TT" />
      <input id="tt-pass" type="password" placeholder="Mật khẩu" />
      <button type="submit" onclick="loginTt()">Đăng nhập nội bộ TT</button>
    </form>
    <div id="tt-msg"></div>
  </div>
  <script>
    async function loginTt() {
      const username = (document.getElementById('tt-user').value || '').trim();
      const passcode = (document.getElementById('tt-pass').value || '').trim();
      const res = await fetch('/api/hexa/v0/tt/auth/login', {
        method: 'POST',
        credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, passcode })
      });
      if (!res.ok) {
        document.getElementById('tt-msg').textContent = 'Từ chối truy cập';
        return;
      }
      const data = await res.json();
      const tok = String((data && data.session_token) || '');
      try { if (tok && typeof sessionStorage !== 'undefined') sessionStorage.setItem('hexa_tt_token', tok); } catch (_e) {}
      const deskRes = await fetch('/tt', {
        credentials: 'same-origin',
        headers: tok ? { 'Authorization': 'Bearer ' + tok } : {}
      });
      if (deskRes.ok) {
        const html = await deskRes.text();
        window.__HEXA_TT_TOKEN = tok;
        document.open();
        document.write(html);
        document.close();
      } else {
        window.location.href = '/tt';
      }
    }
  </script>
</body>
</html>
"""


def render_tt_publish_desk_html() -> str:
    """Separated internal Trường Thành publication approval desk (/tt)."""
    return """<!doctype html>
<html lang="vi">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Nội bộ Trường Thành — Bàn Duyệt Công Bố Lô Hàng</title>
  <style>
    body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f1f5f9; color: #0f172a; }
    header { background: #0f2942; color: #fff; padding: 14px 22px; display: flex; justify-content: space-between; align-items: center; }
    main { max-width: 1120px; margin: 18px auto; padding: 0 18px 40px; display: grid; gap: 16px; }
    .card { background: #fff; border: 1px solid #cbd5e1; border-radius: 8px; padding: 16px 18px; }
    table { width: 100%; border-collapse: collapse; font-size: 13px; margin-top: 10px; }
    th, td { padding: 8px; border-bottom: 1px solid #e2e8f0; text-align: left; }
    button { cursor: pointer; padding: 7px 12px; border-radius: 6px; border: 1px solid #0f4c81; background: #0f4c81; color: #fff; font-weight: 600; }
    button.danger { background: #b91c1c; border-color: #b91c1c; }
  </style>
</head>
<body>
  <header>
    <strong>Nội bộ Trường Thành — Bàn Duyệt Công Bố &amp; Thu Hồi (Tách biệt khỏi Cổng Khách Hàng)</strong>
  </header>
  <main class="card">
    <div style="display:flex; gap:8px; align-items:center; flex-wrap:wrap;">
      <input id="tt-shipment-input" type="text" value="ROAD-LG-001" style="padding:6px 10px;" />
      <button type="button" onclick="loadTtShipment()">Mở hồ sơ lô</button>
      <button type="button" onclick="submitTtPublish()">✓ Duyệt &amp; Công bố</button>
      <button type="button" class="danger" onclick="submitTtRevokeAll()">✕ Thu hồi công bố</button>
    </div>
    <div id="tt-status" style="margin-top:8px; font-weight:700;"></div>
    <table><thead><tr><th>Chọn</th><th>Mã mốc</th><th>Phiên bản</th><th>Công đoạn</th><th>Nội dung</th></tr></thead><tbody id="tt-events-tbody"></tbody></table>
    <table><thead><tr><th>Chọn</th><th>Mã chứng từ</th><th>Phiên bản</th><th>Loại</th><th>Tiêu đề</th></tr></thead><tbody id="tt-docs-tbody"></tbody></table>
  </main>
  <script>
    let currentTtShipment = null;
    function getTtToken() {
      if (window.__HEXA_TT_TOKEN) return String(window.__HEXA_TT_TOKEN);
      try { if (typeof sessionStorage !== 'undefined') return sessionStorage.getItem('hexa_tt_token') || ''; } catch (_e) {}
      return '';
    }
    function ttFetch(url, opts) {
      const options = Object.assign({ credentials: 'same-origin' }, opts || {});
      const hdrs = Object.assign({}, options.headers || {});
      const tok = getTtToken();
      if (tok) hdrs['Authorization'] = 'Bearer ' + tok;
      options.headers = hdrs;
      return fetch(url, options);
    }
    async function loadTtShipment() {
      const sid = (document.getElementById('tt-shipment-input').value || '').trim();
      const res = await ttFetch(`/api/hexa/v0/tt/shipments/${encodeURIComponent(sid)}`);
      if (!res.ok) return;
      currentTtShipment = await res.json();
      const pub = currentTtShipment.publication || {};
      const pubEvents = pub.event_versions || {};
      const pubDocs = pub.document_versions || {};
      const evBody = document.getElementById('tt-events-tbody');
      evBody.textContent = '';
      (currentTtShipment.candidate_events || []).forEach(ev => {
        const tr = document.createElement('tr');
        const tdCk = document.createElement('td');
        const ck = document.createElement('input');
        ck.type = 'checkbox'; ck.className = 'tt-ev-ck'; ck.dataset.id = ev.id; ck.dataset.version = ev.version;
        ck.checked = (pubEvents[ev.id] === ev.version); ck.disabled = !ev.eligible_for_customer;
        tdCk.appendChild(ck);
        const tdId = document.createElement('td'); tdId.textContent = ev.id;
        const tdVer = document.createElement('td'); tdVer.textContent = ev.version;
        const tdSt = document.createElement('td'); tdSt.textContent = ev.stage;
        const tdTitle = document.createElement('td'); tdTitle.textContent = ev.title;
        tr.append(tdCk, tdId, tdVer, tdSt, tdTitle);
        evBody.appendChild(tr);
      });
      const docBody = document.getElementById('tt-docs-tbody');
      docBody.textContent = '';
      (currentTtShipment.candidate_documents || []).forEach(doc => {
        const tr = document.createElement('tr');
        const tdCk = document.createElement('td');
        const ck = document.createElement('input');
        ck.type = 'checkbox'; ck.className = 'tt-doc-ck'; ck.dataset.id = doc.id; ck.dataset.version = doc.version;
        ck.checked = (pubDocs[doc.id] === doc.version); ck.disabled = !doc.eligible_for_customer;
        tdCk.appendChild(ck);
        const tdId = document.createElement('td'); tdId.textContent = doc.id;
        const tdVer = document.createElement('td'); tdVer.textContent = doc.version;
        const tdKind = document.createElement('td'); tdKind.textContent = doc.kind;
        const tdTitle = document.createElement('td'); tdTitle.textContent = doc.title;
        tr.append(tdCk, tdId, tdVer, tdKind, tdTitle);
        docBody.appendChild(tr);
      });
    }
    async function submitTtPublish() {
      const sid = (document.getElementById('tt-shipment-input').value || '').trim();
      const event_versions = {};
      document.querySelectorAll('.tt-ev-ck:checked').forEach(cb => { event_versions[cb.dataset.id] = cb.dataset.version; });
      const document_versions = {};
      document.querySelectorAll('.tt-doc-ck:checked').forEach(cb => { document_versions[cb.dataset.id] = cb.dataset.version; });
      const q = currentTtShipment && currentTtShipment.candidate_quote;
      const quote = q ? { id: q.id, version: q.version } : null;
      const res = await ttFetch(`/api/hexa/v0/tt/shipments/${encodeURIComponent(sid)}/publish`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ event_versions, document_versions, quote })
      });
      document.getElementById('tt-status').textContent = res.ok ? `Đã công bố lô ${sid}` : 'Lỗi công bố';
      await loadTtShipment();
    }
    async function submitTtRevokeAll() {
      const sid = (document.getElementById('tt-shipment-input').value || '').trim();
      const res = await ttFetch(`/api/hexa/v0/tt/shipments/${encodeURIComponent(sid)}/revoke`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      });
      document.getElementById('tt-status').textContent = res.ok ? `Đã thu hồi công bố lô ${sid}` : 'Lỗi thu hồi';
      await loadTtShipment();
    }
    window.addEventListener('DOMContentLoaded', loadTtShipment);
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
            forwarded_proto = str(self.headers.get("X-Forwarded-Proto") or "").strip().lower()
            samesite_attr = (
                "SameSite=None; Secure; Partitioned"
                if forwarded_proto == "https"
                else "SameSite=Lax"
            )
            self.send_header(
                "Set-Cookie",
                f"{cookie_name}={set_cookie_token}; Path=/; HttpOnly; {samesite_attr}",
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

    def _send_static_asset(self, rel_path: str, content_type: str) -> None:
        from pathlib import Path

        repo_root = Path(__file__).resolve().parent.parent
        asset_path = (repo_root / rel_path).resolve()
        if not str(asset_path).startswith(str(repo_root)) or not asset_path.is_file():
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "NOT_FOUND"})
            return
        data = asset_path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "public, max-age=300")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(data)

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

        if path == "/tt/login":
            self._send_html(HTTPStatus.OK, render_tt_login_html())
            return

        if path in {"/tt", "/tt/publish"}:
            try:
                self.env._require_authorized_tt_staff(self._current_tt_token())
            except PublicationDenied as exc:
                self._send_json(HTTPStatus.FORBIDDEN, {"error": str(exc)})
                return
            self._send_html(HTTPStatus.OK, render_tt_publish_desk_html())
            return

        if path == "/assets/journey/vietnam-east-sea-chart.webp":
            self._send_static_asset("component/src/assets/journey/vietnam-east-sea-chart.webp", "image/webp")
            return

        if path == "/assets/journey/chart-paper.jpg":
            self._send_static_asset("component/src/assets/journey/chart-paper.jpg", "image/jpeg")
            return

        if path == "/assets/journey/logi-shell.css":
            self._send_static_asset("component/dist/logi-shell.css", "text/css; charset=utf-8")
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
                initial_dashboard = self.env.build_customer_dashboard(
                    session_token=issued_token,
                )
                self._send_json(
                    HTTPStatus.OK,
                    {
                        **summary,
                        "session_token": issued_token,
                        "dashboard": initial_dashboard,
                    },
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
                    {**summary, "session_token": issued_token},
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

        # Route: POST /api/hexa/v0/shipments/<shipment_id>/stages/<stage_id>/submissions (or /comments)
        if (
            len(parts) == 8
            and parts[:4] == ["api", "hexa", "v0", "shipments"]
            and parts[5] == "stages"
            and parts[7] in {"submissions", "comments"}
        ):
            shipment_id = parts[4]
            stage_id = parts[6]
            body = self._read_json_body()
            try:
                result = self.env.submit_customer_stage_collaboration(
                    session_token=self._current_token(),
                    shipment_id=shipment_id,
                    stage_id=stage_id,
                    comment=str(body.get("comment") or ""),
                    file_name=str(body.get("file_name") or ""),
                    mime=str(body.get("mime") or "application/pdf"),
                    file_base64=str(body.get("file_base64") or ""),
                )
                self._send_json(HTTPStatus.OK, result)
            except PublicationDenied as exc:
                self._send_json(HTTPStatus.FORBIDDEN, {"error": str(exc)})
            return

        # Route: POST /api/hexa/v0/tt/shipments/<shipment_id>/stages/<stage_id>/comments
        if (
            len(parts) == 9
            and parts[:5] == ["api", "hexa", "v0", "tt", "shipments"]
            and parts[6] == "stages"
            and parts[8] == "comments"
        ):
            shipment_id = parts[5]
            stage_id = parts[7]
            body = self._read_json_body()
            try:
                result = self.env.post_tt_stage_comment(
                    session_token=self._current_tt_token(),
                    shipment_id=shipment_id,
                    stage_id=stage_id,
                    comment=str(body.get("comment") or ""),
                    visibility=str(body.get("visibility") or "TT"),
                )
                self._send_json(HTTPStatus.OK, result)
            except PublicationDenied as exc:
                self._send_json(HTTPStatus.FORBIDDEN, {"error": str(exc)})
            return

        # Route: POST /api/hexa/v0/tt/shipments/<shipment_id>/finance/confirm (requires finance_write)
        if (
            len(parts) == 8
            and parts[:5] == ["api", "hexa", "v0", "tt", "shipments"]
            and parts[6] == "finance"
            and parts[7] == "confirm"
        ):
            shipment_id = parts[5]
            body = self._read_json_body()
            try:
                result = self.env.confirm_tt_shipment_finance(
                    session_token=self._current_tt_token(),
                    shipment_id=shipment_id,
                    transaction_id=str(body.get("transaction_id") or ""),
                    obligation_id=str(body.get("obligation_id") or ""),
                    amount=float(body.get("amount") or 0),
                    currency=str(body.get("currency") or "VND"),
                    occurred_at=str(body.get("occurred_at") or ""),
                    note=str(body.get("note") or ""),
                    verified_document_id=str(body.get("verified_document_id") or ""),
                )
                self._send_json(HTTPStatus.OK, result)
            except (PublicationDenied, ValueError, TypeError) as exc:
                self._send_json(HTTPStatus.FORBIDDEN, {"error": str(exc)})
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
                    approve_finance=body.get("approve_finance") is True,
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
            cmt_ids = body.get("comment_ids") if isinstance(body.get("comment_ids"), list) else None
            rev_quote = bool(body.get("revoke_quote", False))
            rev_finance = bool(body.get("revoke_finance", False))
            try:
                result = self.env.revoke_shipment_publication(
                    session_token=self._current_tt_token(),
                    shipment_id=shipment_id,
                    document_ids=doc_ids,
                    event_ids=ev_ids,
                    comment_ids=cmt_ids,
                    revoke_quote=rev_quote,
                    revoke_finance=rev_finance,
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
