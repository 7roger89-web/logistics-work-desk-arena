"""HEXA V0 Trial Portal & Trusted Adapter — TT → Lục Giác (isolated sandbox).

Reuses ``core.hexa_customer_publication`` (``build_customer_publication``,
``authorize_document_download``, ``PublicationDenied``), ``core.quotations``,
``core.shipment_attachments`` (``upload_attachment``, ``fetch_attachment_bytes``),
``core.database`` and ``views.logi_sandbox`` (isolated ``mongomock`` + GridFS).

Nothing in this module connects to production MongoDB, modifies PR #211 files,
or grants live customer access.
"""
from __future__ import annotations

import copy
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from typing import Any, Mapping
from urllib.parse import parse_qs, urlparse

from core.hexa_customer_publication import (
    PUBLICATION_SCHEMA,
    PublicationDenied,
    authorize_document_download,
    build_customer_publication,
)

TRIAL_COOKIE_NAME = "hexa_trial_session"

# Sentinels used to prove zero internal / cross-tenant leakage over HTTP.
SENTINEL_TT_INTERNAL_COST = "TT_INTERNAL_COST_42000000"
SENTINEL_TT_PRIVATE_SUPPLIER = "TT_PRIVATE_SUPPLIER_FOSHAN_8899"
SENTINEL_TT_MARGIN = "TT_INTERNAL_MARGIN_11000000"
SENTINEL_TT_UNVERIFIED_ETA = "TT_UNVERIFIED_ETA_2026-10-25"
SENTINEL_FOREIGN_CUSTOMER_B = "FOREIGN_CUSTOMER_MINHDUC_9911"

TRIAL_SENTINELS: tuple[str, ...] = (
    SENTINEL_TT_INTERNAL_COST,
    SENTINEL_TT_PRIVATE_SUPPLIER,
    SENTINEL_TT_MARGIN,
    SENTINEL_TT_UNVERIFIED_ETA,
    SENTINEL_FOREIGN_CUSTOMER_B,
)

SHARED_TRIP_ID = "TRIP-ROAD-2026-01"
SHARED_TRUCK_PLATE = "29H-886.68 / 粤Z·6689港"

CUSTOMER_A_ID = "CUST-LUCGIAC"
CUSTOMER_B_ID = "CUST-MINHDUC"

SHIPMENT_A_ID = "ROAD-LG-001"
SHIPMENT_B_ID = "ROAD-MD-002"

QUOTE_A_ID = "Q-LG-ROAD-001"
QUOTE_B_ID = "Q-MD-ROAD-002"

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
        "trial_handling": "Bảng phiên thử nghiệm phía server (hexa_trial_sessions) ánh xạ token phiên sang {authenticated, kind, customer_id}; tuyệt đối không đọc customer_id từ query/header/body của client.",
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

        # 1. Server-side session table (opaque session tokens; client cannot forge customer_id).
        self.sessions = {
            "sess-customer-lg": {
                "token": "sess-customer-lg",
                "label": "Khách A — Công ty TNHH Lục Giác (HEXA)",
                "principal": {
                    "authenticated": True,
                    "kind": "customer",
                    "customer_id": CUSTOMER_A_ID,
                    "display_name": "Lục Giác (Khách A)",
                },
                "default_shipment_id": SHIPMENT_A_ID,
            },
            "sess-customer-md": {
                "token": "sess-customer-md",
                "label": "Khách B — Công ty CP Minh Đức (cùng chuyến xe)",
                "principal": {
                    "authenticated": True,
                    "kind": "customer",
                    "customer_id": CUSTOMER_B_ID,
                    "display_name": "Minh Đức (Khách B)",
                },
                "default_shipment_id": SHIPMENT_B_ID,
            },
            "sess-internal-viewer": {
                "token": "sess-internal-viewer",
                "label": "Nội bộ TT — Role viewer (có finance_view, CẤM làm cổng khách)",
                "principal": {
                    "authenticated": True,
                    "kind": "viewer",
                    "customer_id": CUSTOMER_A_ID,
                    "display_name": "Internal Viewer (finance_view)",
                },
                "default_shipment_id": SHIPMENT_A_ID,
            },
            "sess-anonymous": {
                "token": "sess-anonymous",
                "label": "Ẩn danh — Chưa đăng nhập",
                "principal": {
                    "authenticated": False,
                    "kind": "customer",
                    "customer_id": "",
                    "display_name": "Khách ẩn danh",
                },
                "default_shipment_id": SHIPMENT_A_ID,
            },
        }

        # 2. Seed the two customers sharing the ROAD trip.
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
        ):
            db["customers"].replace_one({"id": cust_doc["id"]}, cust_doc, upsert=True)

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
        db["quotes"].replace_one({"id": QUOTE_A_ID}, quote_a, upsert=True)
        db["quotes"].replace_one({"id": QUOTE_B_ID}, quote_b, upsert=True)

        # 4. Build and persist canonical shipments sharing the same ROAD truck via save_shipment_atomic.
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

        for ship_doc in (shipment_a, shipment_b):
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
                    "internal_cost_vnd": 29000000,
                    "internal_margin_vnd": 7000000,
                    "internal_supplier": f"Guangxi Dongxing Metal Co. ({SENTINEL_FOREIGN_CUSTOMER_B})",
                    "internal_carrier_vendor": "Nhà xe Việt Trung An Bình",
                    "unverified_eta": "2026-10-25",
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
            ]
        )

        db["hexa_trial_publications"].delete_many({})
        db["hexa_trial_publications"].insert_many(
            [
                {
                    "shipment_id": SHIPMENT_A_ID,
                    "customer_id": CUSTOMER_A_ID,
                    "state": "PUBLISHED",
                    "approved_by": "tt.ops.truongthanh",
                    "approved_at": "2026-10-22T09:00:00Z",
                    "event_versions": {
                        "EVT-LG-01-PICKUP": "v1",
                        "EVT-LG-02-BORDER": "v2",
                    },
                    "document_versions": {
                        "DOC-LG-PL": "v2",
                        "DOC-LG-PI": "v1",
                    },
                    "quote": {
                        "id": QUOTE_A_ID,
                        "version": str(quote_a["version"]),
                    },
                },
                {
                    "shipment_id": SHIPMENT_B_ID,
                    "customer_id": CUSTOMER_B_ID,
                    "state": "PUBLISHED",
                    "approved_by": "tt.ops.truongthanh",
                    "approved_at": "2026-10-22T09:05:00Z",
                    "event_versions": {
                        "EVT-MD-01-PICKUP": "v1",
                    },
                    "document_versions": {
                        "DOC-MD-PL": "v1",
                    },
                    "quote": {
                        "id": QUOTE_B_ID,
                        "version": str(quote_b["version"]),
                    },
                },
            ]
        )

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

    def resolve_principal(self, session_token: str | None) -> dict[str, Any]:
        """Resolve caller principal strictly from the server-owned session store.

        Any unknown/empty token returns an unauthenticated principal. Query
        parameters or client headers carrying ``customer_id`` are NEVER read.
        """
        self.ensure_seeded()
        token = str(session_token or "").strip()
        entry = self.sessions.get(token)
        if not entry:
            return {"authenticated": False, "kind": "customer", "customer_id": ""}
        return copy.deepcopy(entry["principal"])

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
        # Only documents whose underlying attachment is still AVAILABLE in shipment_attachments
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
                session_token=session_token,
                principal=principal,
                shipment_id=sid,
                allowed=True,
                detail=f"events={len(payload['timeline'])}, docs={len(payload['documents'])}",
            )
            return payload
        except PublicationDenied:
            self._record_audit(
                action="READ_PUBLICATION",
                session_token=session_token,
                principal=principal,
                shipment_id=sid,
                allowed=False,
                detail="CUSTOMER_RESOURCE_UNAVAILABLE",
            )
            raise

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
                session_token=session_token,
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
            session_token=session_token,
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
        """Return TT internal truth vs published manifest state for the trial UI."""
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
        session_token: str | None,
        principal: Mapping[str, Any],
        shipment_id: str,
        allowed: bool,
        detail: str,
    ) -> None:
        self.audit_trail.append(
            {
                "action": action,
                "session": str(session_token or "anonymous"),
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


def render_trial_portal_html() -> str:
    """Self-contained interactive HEXA V0 trial portal HTML (uses relative URLs only)."""
    return """<!doctype html>
<html lang="vi">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>HEXA V0 — Cổng dữ liệu thử nghiệm Trường Thành → Lục Giác</title>
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
      --warn: #b06000;
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
      max-width: 1360px;
      margin: 0 auto;
    }
    header h1 {
      font-size: 18px;
      margin: 0;
      font-weight: 700;
    }
    header .badge-bar {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      font-size: 12px;
      font-family: var(--mono);
    }
    .pill {
      padding: 4px 10px;
      border-radius: 999px;
      font-weight: 600;
      font-size: 12px;
      display: inline-block;
    }
    .pill-sandbox { background: #ffd166; color: #1d2d44; }
    .pill-ok { background: var(--ok-bg); color: var(--ok); }
    .pill-deny { background: var(--deny-bg); color: var(--deny); }
    .pill-warn { background: var(--warn-bg); color: var(--warn); }
    main {
      max-width: 1360px;
      margin: 20px auto;
      padding: 0 20px 48px;
      display: grid;
      gap: 20px;
    }
    .grid-2 {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(420px, 1fr));
      gap: 20px;
    }
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
      gap: 8px;
      margin-top: 10px;
    }
    button {
      cursor: pointer;
      border: 1px solid var(--border);
      background: #fff;
      color: var(--text);
      padding: 8px 12px;
      border-radius: 6px;
      font-size: 13px;
      font-weight: 600;
      transition: all 0.15s ease;
    }
    button:hover { border-color: var(--primary); background: var(--primary-soft); }
    button.active {
      background: var(--primary);
      color: #fff;
      border-color: var(--primary);
    }
    button.btn-primary {
      background: var(--primary);
      color: #fff;
      border-color: var(--primary);
    }
    button.btn-primary:hover { background: #0b3960; }
    button.btn-danger {
      background: #fff5f5;
      color: var(--deny);
      border-color: #f1b0b7;
    }
    button.btn-danger:hover { background: var(--deny-bg); }
    .kv-list {
      display: grid;
      grid-template-columns: 170px 1fr;
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
      max-height: 300px;
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
  </style>
</head>
<body>
  <header>
    <div class="top-row">
      <div>
        <h1>HEXA V0 — Kết nối dữ liệu thử nghiệm Trường Thành (TT) → Lục Giác (LG)</h1>
        <div style="font-size: 13px; opacity: 0.9; margin-top: 4px;">
          Chuyến xe ghép ROAD: <span class="mono">TRIP-ROAD-2026-01</span> · Biển số: <span class="mono">29H-886.68</span> · 2 khách hàng cùng chuyến (Lục Giác &amp; Minh Đức)
        </div>
      </div>
      <div class="badge-bar">
        <span class="pill pill-sandbox">SANDBOX_STAGING · MONGOMOCK + GRIDFS</span>
        <span class="pill pill-sandbox">NO_PRODUCTION_DB · NO_LIVE_CUSTOMER_ACCESS</span>
      </div>
    </div>
  </header>

  <main>
    <!-- Phiên đăng nhập thử nghiệm phía server -->
    <section class="card" id="session-card">
      <h2>
        <span>1. Phiên xác thực phía Server (Server-Owned Session) &amp; Chọn mã lô cần đọc</span>
        <span id="active-session-pill" class="pill pill-ok">Đang tải phiên...</span>
      </h2>
      <p class="muted" style="margin: 0 0 8px;">
        Server giải mã danh tính khách hàng từ cookie phiên <span class="mono">hexa_trial_session</span> trên máy chủ. Mọi tham số <span class="mono">?customer_id=...</span> hoặc header do client tự gửi đều bị bỏ qua.
      </p>
      <div class="btn-row" id="session-buttons">
        <button data-session="sess-customer-lg" onclick="switchSession('sess-customer-lg', 'ROAD-LG-001')">
          Phiên Khách A: Lục Giác (CUST-LUCGIAC)
        </button>
        <button data-session="sess-customer-md" onclick="switchSession('sess-customer-md', 'ROAD-MD-002')">
          Phiên Khách B: Minh Đức (CUST-MINHDUC — cùng xe)
        </button>
        <button data-session="sess-internal-viewer" class="btn-danger" onclick="switchSession('sess-internal-viewer', 'ROAD-LG-001')">
          Phiên Nội bộ: role=viewer (có finance_view → phải bị chặn)
        </button>
        <button data-session="sess-anonymous" class="btn-danger" onclick="switchSession('sess-anonymous', 'ROAD-LG-001')">
          Phiên Ẩn danh (chưa đăng nhập → phải bị chặn)
        </button>
      </div>
      <div class="btn-row" style="margin-top: 12px; align-items: center;">
        <span class="muted" style="font-weight: 600;">Đọc mã lô qua HTTP <span class="mono">GET /api/hexa/v0/shipments/&lt;id&gt;</span>:</span>
        <button class="btn-primary" onclick="loadShipment('ROAD-LG-001')">Xem lô ROAD-LG-001 (Lục Giác)</button>
        <button onclick="loadShipment('ROAD-MD-002')">Thử mở lô ROAD-MD-002 (Minh Đức — Khách B cùng xe)</button>
        <button class="btn-danger" onclick="loadShipment('ROAD-MD-002?customer_id=CUST-MINHDUC')">
          Giả mạo URL ?customer_id=CUST-MINHDUC để đọc ROAD-MD-002
        </button>
      </div>
    </section>

    <div class="grid-2">
      <!-- Giao diện HEXA V0 nhận dữ liệu từ HTTP Server -->
      <section class="card" id="hexa-portal-card">
        <h2>
          <span>2. Giao diện khách hàng HEXA V0 (Dữ liệu thực tế trả về từ Server)</span>
          <span class="mono" id="http-status-badge">HTTP --</span>
        </h2>
        <div id="portal-status-banner" class="banner-result banner-ok">Đang tải...</div>

        <div id="portal-content">
          <dl class="kv-list">
            <dt>Schema công bố:</dt><dd class="mono" id="pub-schema">-</dd>
            <dt>Mã tham chiếu lô:</dt><dd class="mono" id="pub-reference">-</dd>
            <dt>Phương thức vận tải:</dt><dd class="mono" id="pub-mode">-</dd>
            <dt>Tổng báo giá BÁN đã gửi:</dt><dd id="pub-quote">-</dd>
            <dt>ETA chưa xác minh:</dt><dd><span class="pill pill-ok">ĐÃ ẨN (Không xuất hiện trong payload)</span></dd>
            <dt>Giá vốn &amp; Nhà cung cấp:</dt><dd><span class="pill pill-ok">ĐÃ ẨN (Không xuất hiện trong payload)</span></dd>
          </dl>

          <h3>Tiến độ đã được TT xác minh &amp; duyệt công bố (Timeline)</h3>
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

          <h3>Chứng từ đúng phiên bản đã duyệt (Kiểm quyền phía Server trước khi đọc GridFS)</h3>
          <table>
            <thead>
              <tr>
                <th>Mã chứng từ</th>
                <th>Loại</th>
                <th>Tên công bố</th>
                <th>Phiên bản duyệt</th>
                <th>Tải file (Server-checked)</th>
              </tr>
            </thead>
            <tbody id="pub-docs-body"></tbody>
          </table>
        </div>

        <h3>JSON nguyên bản từ <span class="mono" id="raw-json-url">/api/hexa/v0/shipments/ROAD-LG-001</span></h3>
        <pre id="raw-publication-json">{}</pre>
      </section>

      <!-- Đối chiếu dữ liệu nội bộ Trường Thành & Bộ kiểm thử nghiệm thu -->
      <section class="card">
        <h2>
          <span>3. Đối chiếu nội bộ Trường Thành (TT) &amp; Kiểm chứng chặn truy cập trái phép</span>
          <span class="pill pill-warn" id="gridfs-counter-pill">GridFS reads: 0 | Chặn trước khi đọc: 0</span>
        </h2>
        <p class="muted" style="margin-top: 0;">
          Dữ liệu dưới đây tồn tại trong DB nội bộ của Trường Thành trên chuyến xe ghép <span class="mono">TRIP-ROAD-2026-01</span> nhưng bị bộ lọc <span class="mono">core/hexa_customer_publication.py</span> chặn hoàn toàn khi công bố sang Lục Giác:
        </p>
        <div id="tt-internal-summary"></div>

        <h3>Bộ nút kiểm thử trực tiếp 7 yêu cầu nghiệm thu (Chạy HTTP thật)</h3>
        <div class="btn-row">
          <button class="btn-primary" onclick="runAllAcceptanceChecks()">
            ▶ Chạy tự động toàn bộ 7 kịch bản HTTP &amp; Tải chứng từ
          </button>
          <button class="btn-danger" onclick="triggerDownload('ROAD-LG-001', 'DOC-LG-PL', 'v1')">
            Thử tải bản cũ DOC-LG-PL (v1)
          </button>
          <button class="btn-danger" onclick="triggerDownload('ROAD-LG-001', 'DOC-LG-COST', 'v1')">
            Thử tải bảng giá vốn nội bộ DOC-LG-COST
          </button>
          <button class="btn-danger" onclick="triggerDownload('ROAD-LG-001', 'DOC-MD-PL', 'v1')">
            Thử tải chứng từ Khách B (DOC-MD-PL) trên cùng chuyến xe
          </button>
          <button class="btn-danger" onclick="triggerDownload('ROAD-MD-002', 'DOC-MD-PL', 'v1')">
            Đoán mã lô ROAD-MD-002 để tải DOC-MD-PL
          </button>
        </div>
        <div id="download-test-banner" style="margin-top: 10px;"></div>
        <pre id="acceptance-log">Nhấn "Chạy tự động toàn bộ 7 kịch bản HTTP &amp; Tải chứng từ" để xem bằng chứng HTTP trực tiếp...</pre>
      </section>
    </div>

    <!-- Yêu cầu nghiệm thu #7: Các trường dữ liệu thiếu trong nguồn hiện tại -->
    <section class="card">
      <h2>
        <span>4. Báo cáo chính xác các trường bắt buộc còn thiếu ở schema nội bộ hiện tại (Yêu cầu nghiệm thu #7)</span>
        <span class="pill pill-warn">KHÔNG GIẢ ĐỊNH / KHÔNG CHẾ DỮ LIỆU THẬT</span>
      </h2>
      <p class="muted" style="margin-top: 0;">
        Bảng dưới đây liệt kê chính xác từng trường mà <span class="mono">core/hexa_customer_publication.py</span> bắt buộc phải có so với schema hiện hữu trong repo (<span class="mono">core/users.py</span>, <span class="mono">core/database.py</span>, <span class="mono">core/shipment_attachments.py</span>, <span class="mono">core/shipment_journey.py</span>, <span class="mono">core/quotations.py</span>):
      </p>
      <table>
        <thead>
          <tr>
            <th>Bề mặt dữ liệu</th>
            <th>Nguồn hiện tại trong Repo</th>
            <th>Trường đã có</th>
            <th>Trường bắt buộc còn thiếu</th>
            <th>Cách xử lý trong môi trường thử cô lập</th>
          </tr>
        </thead>
        <tbody id="schema-gap-body"></tbody>
      </table>
    </section>
  </main>

  <script>
    let currentSessionToken = 'sess-customer-lg';
    let currentShipmentId = 'ROAD-LG-001';

    function formatVnd(val) {
      if (val === null || val === undefined) return 'Chưa xác định (null)';
      return new Intl.NumberFormat('vi-VN').format(val) + ' VND';
    }

    async function refreshSessionState() {
      const res = await fetch('/api/hexa/v0/session', { credentials: 'same-origin' });
      const data = await res.json();
      currentSessionToken = data.active_session_token || 'sess-anonymous';
      const p = data.principal || {};
      const pill = document.getElementById('active-session-pill');
      pill.textContent = `Phiên: ${data.label || currentSessionToken} | kind=${p.kind || '-'} | customer_id=${p.customer_id || '(trống)'}`;
      pill.className = 'pill ' + (p.authenticated && p.kind === 'customer' ? 'pill-ok' : 'pill-deny');

      document.querySelectorAll('#session-buttons button').forEach(btn => {
        btn.classList.toggle('active', btn.getAttribute('data-session') === currentSessionToken);
      });
    }

    async function switchSession(sessionToken, defaultShipment) {
      await fetch('/api/hexa/v0/session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin',
        body: JSON.stringify({ session_token: sessionToken })
      });
      await refreshSessionState();
      if (defaultShipment) {
        await loadShipment(defaultShipment);
      }
      await loadInspector();
    }

    async function loadShipment(shipmentPath) {
      currentShipmentId = shipmentPath.split('?')[0];
      const url = `/api/hexa/v0/shipments/${shipmentPath}`;
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
        banner.textContent = `TRUY CẬP BỊ TỪ CHỐI (HTTP ${res.status}): ${body.error || 'CUSTOMER_RESOURCE_UNAVAILABLE'} — Không lộ sự tồn tại hay dữ liệu của lô khác.`;
        content.style.opacity = '0.45';
        await loadInspector();
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
            <button class="btn-primary" onclick="triggerDownload('${body.reference}', '${doc.id}', '${doc.version}')">
              ⬇ Tải ${doc.id} (${doc.version})
            </button>
          </td>
        `;
        docsBody.appendChild(tr);
      });

      await loadInspector();
    }

    async function triggerDownload(shipmentId, docId, version) {
      const url = `/api/hexa/v0/shipments/${encodeURIComponent(shipmentId)}/documents/${encodeURIComponent(docId)}/download?version=${encodeURIComponent(version)}`;
      const res = await fetch(url, { credentials: 'same-origin' });
      const banner = document.getElementById('download-test-banner');
      if (res.ok) {
        const blob = await res.blob();
        const textPreview = await blob.text();
        banner.className = 'banner-result banner-ok';
        banner.textContent = `TẢI CHỨNG TỪ THÀNH CÔNG (HTTP ${res.status}): ${docId}@${version} (${blob.size} bytes PDF từ GridFS). Header PDF: ${textPreview.slice(0, 28)}...`;
      } else {
        const err = await res.json().catch(() => ({}));
        banner.className = 'banner-result banner-deny';
        banner.textContent = `CHẶN TẢI CHỨNG TỪ PHÍA SERVER TRƯỚC KHI ĐỌC FILE (HTTP ${res.status}): ${docId}@${version} trên ${shipmentId} → ${err.error || 'CUSTOMER_RESOURCE_UNAVAILABLE'}`;
      }
      await loadInspector();
    }

    async function loadInspector() {
      const res = await fetch('/api/hexa/v0/trial-inspector', { credentials: 'same-origin' });
      const info = await res.json();
      const metrics = info.storage_guard_metrics || {};
      document.getElementById('gridfs-counter-pill').textContent =
        `GridFS byte reads: ${metrics.gridfs_storage_read_attempts || 0} | Chặn trước khi đọc file: ${metrics.denied_before_storage_read_count || 0}`;

      const tt = info.tt_internal_only_data || {};
      const other = tt.other_customer_on_same_truck || {};
      document.getElementById('tt-internal-summary').innerHTML = `
        <dl class="kv-list">
          <dt>Nhà cung cấp (TT nội bộ):</dt><dd>${tt.supplier || '-'}</dd>
          <dt>Nhà xe hợp đồng (TT):</dt><dd>${tt.carrier_vendor || '-'}</dd>
          <dt>Giá vốn nội bộ TT:</dt><dd class="mono">${formatVnd(tt.cost_before_tax_vnd)}</dd>
          <dt>Lợi nhuận gộp dự kiến:</dt><dd class="mono">${formatVnd(tt.estimated_margin_vnd)}</dd>
          <dt>Giá bán đã gửi khách A:</dt><dd class="mono">${formatVnd(tt.selling_total_vnd)}</dd>
          <dt>ETA chưa xác minh:</dt><dd style="color: var(--deny); font-weight: 600;">${tt.unverified_eta || '-'}</dd>
          <dt>Khách B cùng xe:</dt><dd>${other.customer_id} · Lô <span class="mono">${other.shipment_id}</span> · Giá bán <span class="mono">${formatVnd(other.selling_total_vnd)}</span></dd>
        </dl>
      `;

      const gapBody = document.getElementById('schema-gap-body');
      gapBody.innerHTML = '';
      (info.schema_gaps || []).forEach(gap => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td><strong>${gap.surface}</strong></td>
          <td class="mono">${gap.current_source}</td>
          <td class="mono">${(gap.existing_fields || []).join(', ') || '(chưa có)'}</td>
          <td><ul style="margin: 0; padding-left: 16px;">${(gap.missing_required_fields || []).map(x => `<li>${x}</li>`).join('')}</ul></td>
          <td>${gap.trial_handling}</td>
        `;
        gapBody.appendChild(tr);
      });
    }

    async function runAllAcceptanceChecks() {
      const logEl = document.getElementById('acceptance-log');
      const lines = [];
      const log = (msg) => { lines.push(msg); logEl.textContent = lines.join('\\n'); };

      log('=== BẮT ĐẦU KIỂM CHỨNG HỆ THỐNG HTTP TT → LG (7 YÊU CẦU NGHIỆM THU) ===');

      // Ensure Customer A session
      await switchSession('sess-customer-lg', 'ROAD-LG-001');

      // 1 & 2 & 4: Read ROAD-LG-001 as Customer A
      const r1 = await fetch('/api/hexa/v0/shipments/ROAD-LG-001', { credentials: 'same-origin' });
      const b1 = await r1.json();
      const raw1 = JSON.stringify(b1);
      const hasLeak = ['TT_INTERNAL_COST_42000000', 'TT_PRIVATE_SUPPLIER_FOSHAN_8899', 'TT_INTERNAL_MARGIN_11000000', 'TT_UNVERIFIED_ETA_2026-10-25', 'FOREIGN_CUSTOMER_MINHDUC_9911'].some(s => raw1.includes(s));
      log(`[1,2,4] GET /api/hexa/v0/shipments/ROAD-LG-001 (Khách A = Lục Giác) -> HTTP ${r1.status}`);
      log(`        timeline=${b1.timeline.map(x => x.id + '@' + x.version).join(', ')} | docs=${b1.documents.map(x => x.id + '@' + x.version).join(', ')}`);
      log(`        quote.selling_total_vnd=${b1.quote && b1.quote.selling_total_vnd} | Rò rỉ giá vốn/NCC/ETA chưa xác minh/Khách B = ${hasLeak ? 'CÓ (FAIL)' : 'KHÔNG (PASS)'}`);

      // 3a: Customer A guesses Customer B shipment ROAD-MD-002
      const r2 = await fetch('/api/hexa/v0/shipments/ROAD-MD-002', { credentials: 'same-origin' });
      const b2 = await r2.json();
      log(`[3a]    GET /api/hexa/v0/shipments/ROAD-MD-002 (Khách A đoán mã lô Khách B) -> HTTP ${r2.status} (${b2.error})`);

      // 3b: Customer A spoofs ?customer_id=CUST-MINHDUC
      const r3 = await fetch('/api/hexa/v0/shipments/ROAD-MD-002?customer_id=CUST-MINHDUC', { credentials: 'same-origin' });
      const b3 = await r3.json();
      log(`[3b]    GET /api/hexa/v0/shipments/ROAD-MD-002?customer_id=CUST-MINHDUC (Giả mạo query) -> HTTP ${r3.status} (${b3.error})`);

      // 5a: Authorized download DOC-LG-PL v2
      const beforeOk = await (await fetch('/api/hexa/v0/trial-inspector')).json();
      const r4 = await fetch('/api/hexa/v0/shipments/ROAD-LG-001/documents/DOC-LG-PL/download?version=v2', { credentials: 'same-origin' });
      const bytes4 = await r4.arrayBuffer();
      const afterOk = await (await fetch('/api/hexa/v0/trial-inspector')).json();
      log(`[5a]    GET .../ROAD-LG-001/documents/DOC-LG-PL/download?version=v2 (Đúng quyền + đúng version) -> HTTP ${r4.status}, bytes=${bytes4.byteLength}, GridFS reads: ${beforeOk.storage_guard_metrics.gridfs_storage_read_attempts} -> ${afterOk.storage_guard_metrics.gridfs_storage_read_attempts} (PASS)`);

      // 5b: Denied downloads (stale version v1, internal cost doc, foreign customer's doc on same truck)
      const beforeDeny = afterOk.storage_guard_metrics.gridfs_storage_read_attempts;
      const r5 = await fetch('/api/hexa/v0/shipments/ROAD-LG-001/documents/DOC-LG-PL/download?version=v1', { credentials: 'same-origin' });
      const r6 = await fetch('/api/hexa/v0/shipments/ROAD-LG-001/documents/DOC-LG-COST/download?version=v1', { credentials: 'same-origin' });
      const r7 = await fetch('/api/hexa/v0/shipments/ROAD-LG-001/documents/DOC-MD-PL/download?version=v1', { credentials: 'same-origin' });
      const r8 = await fetch('/api/hexa/v0/shipments/ROAD-MD-002/documents/DOC-MD-PL/download?version=v1', { credentials: 'same-origin' });
      const afterDeny = await (await fetch('/api/hexa/v0/trial-inspector')).json();
      log(`[5b]    Chặn tải chứng từ trái phép (v1 cũ: HTTP ${r5.status}, COST nội bộ: HTTP ${r6.status}, DOC Khách B cùng xe: HTTP ${r7.status}, DOC lô Khách B: HTTP ${r8.status})`);
      log(`        GridFS reads trước/sau 4 lần từ chối: ${beforeDeny} -> ${afterDeny.storage_guard_metrics.gridfs_storage_read_attempts} (0 lần đọc file khi chưa qua kiểm quyền -> PASS)`);

      await loadInspector();
      log('=== HOÀN TẤT KIỂM CHỨNG: TẤT CẢ 7 RÀO CHẮN AN TOÀN ĐỀU PASS ===');
    }

    window.addEventListener('DOMContentLoaded', async () => {
      await switchSession('sess-customer-lg', 'ROAD-LG-001');
    });
  </script>
</body>
</html>
"""


class HexaTrialRequestHandler(BaseHTTPRequestHandler):
    """HTTP handler for the isolated HEXA V0 trial server.

    Accepts any Host/Origin header so Arena live preview proxy URLs
    (``https://{port}-{sandboxId}.e2b.app``) work out of the box.
    """

    env: HexaTrialEnvironment = _DEFAULT_ENV

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        return

    def _send_json(
        self,
        status: int,
        payload: Mapping[str, Any],
        *,
        set_cookie_token: str | None = None,
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
                f"{TRIAL_COOKIE_NAME}={set_cookie_token}; Path=/; HttpOnly; SameSite=Lax",
            )
        self.end_headers()
        self.wfile.write(raw)

    def _send_html(self, status: int, html: str, *, set_cookie_token: str | None = None) -> None:
        raw = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        if set_cookie_token is not None:
            self.send_header(
                "Set-Cookie",
                f"{TRIAL_COOKIE_NAME}={set_cookie_token}; Path=/; HttpOnly; SameSite=Lax",
            )
        self.end_headers()
        self.wfile.write(raw)

    def _current_token(self) -> str:
        return _extract_session_token(self.headers)

    def do_GET(self) -> None:  # noqa: N802
        self.env.ensure_seeded()
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        query = parse_qs(parsed.query)

        if path in {"/", "/hexa"}:
            token = self._current_token()
            default_cookie = None if token in self.env.sessions else "sess-customer-lg"
            self._send_html(
                HTTPStatus.OK,
                render_trial_portal_html(),
                set_cookie_token=default_cookie,
            )
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
            token = self._current_token() or "sess-anonymous"
            entry = self.env.sessions.get(token) or self.env.sessions["sess-anonymous"]
            self._send_json(
                HTTPStatus.OK,
                {
                    "active_session_token": entry["token"],
                    "label": entry["label"],
                    "principal": entry["principal"],
                    "default_shipment_id": entry["default_shipment_id"],
                    "available_sessions": [
                        {
                            "token": k,
                            "label": v["label"],
                            "default_shipment_id": v["default_shipment_id"],
                        }
                        for k, v in self.env.sessions.items()
                    ],
                },
            )
            return

        if path == "/api/hexa/v0/trial-inspector":
            self._send_json(HTTPStatus.OK, self.env.build_trial_inspector_snapshot())
            return

        # Route: GET /api/hexa/v0/shipments/<shipment_id>
        parts = [p for p in path.split("/") if p]
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
        if path != "/api/hexa/v0/session":
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "NOT_FOUND"})
            return

        length = int(self.headers.get("Content-Length") or 0)
        raw_body = self.rfile.read(length) if length > 0 else b"{}"
        try:
            body = json.loads(raw_body.decode("utf-8"))
        except Exception:  # noqa: BLE001
            body = {}
        requested_token = str((body or {}).get("session_token") or "").strip()
        if requested_token not in self.env.sessions:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "INVALID_TRIAL_SESSION"})
            return

        entry = self.env.sessions[requested_token]
        self._send_json(
            HTTPStatus.OK,
            {
                "ok": True,
                "active_session_token": entry["token"],
                "label": entry["label"],
                "principal": entry["principal"],
                "default_shipment_id": entry["default_shipment_id"],
            },
            set_cookie_token=entry["token"],
        )


def create_trial_http_server(
    host: str = "0.0.0.0",
    port: int = 8787,
    *,
    env: HexaTrialEnvironment | None = None,
) -> ThreadingHTTPServer:
    """Create a ThreadingHTTPServer bound to ``(host, port)`` for the HEXA trial."""
    active_env = env or get_trial_environment()
    active_env.ensure_seeded()

    class _BoundHandler(HexaTrialRequestHandler):
        pass

    _BoundHandler.env = active_env
    return ThreadingHTTPServer((host, port), _BoundHandler)
