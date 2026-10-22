"""Representative staging seed in the REAL Logistics document schema (Phase B).

These documents use the canonical shipment shape that ``core.database`` reads
and writes (``data["0.0"]`` / ``["1.2"]`` / ``["2.4"]`` / ``["2.6"]`` /
``["2.7"]`` / ``["3.4"]`` / ``["entrustment"]`` plus top-level identity), so the
existing readers, ``repair_data`` and the canonical writers all run unchanged.

This is STAGING data, not production truth. It exists so Phase B can prove the
real write → audit → fresh-read path end to end. Values the real model does not
carry are left absent rather than invented, and the presentation adapter keeps
them UNKNOWN (never zero).
"""

from __future__ import annotations

import copy
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def _now() -> datetime:
    return datetime.now(timezone.utc)


CUSTOMERS: list[dict[str, Any]] = [
    {"id": "CUST-ANPHAT", "name": "An Phát JSC", "tax_code": "0101234567",
     "address": "KCN Quế Võ, Bắc Ninh"},
    {"id": "CUST-DUCLONG", "name": "Đức Long Co.", "tax_code": "0312987654",
     "address": "KCN Nam Sơn, Hải Phòng"},
    {"id": "CUST-MINHDUC", "name": "Minh Đức JSC", "tax_code": "0102345678",
     "address": "KCN Yên Phong, Bắc Ninh"},
    {"id": "CUST-HONGHA", "name": "Hồng Hà Co.", "tax_code": "0103456789",
     "address": "KCN Yên Phong, Bắc Ninh"},
    {"id": "CUST-THIENAN", "name": "Thiên Ân JSC", "tax_code": "0104567890",
     "address": "TP. Thủ Đức, TP.HCM"},
]

CONTRACTS: list[dict[str, Any]] = [
    {"id": "HDMB-0306", "contract_no": "HDMB-0306", "hdmb_no": "HDMB-0306/2026",
     "hdmb_date": "2026-09-03", "customer": "An Phát JSC", "customer_id": "CUST-ANPHAT",
     "value": 385000000, "status": "active"},
    {"id": "HDNT-0307", "contract_no": "HDNT-0307", "hdnt_no": "HDNT-0307/2026",
     "hdnt_date": "2026-09-04", "customer": "Đức Long Co.", "customer_id": "CUST-DUCLONG",
     "value": 452000000, "status": "active"},
    {"id": "HDMB-0295", "contract_no": "HDMB-0295", "hdmb_no": "HDMB-0295/2026",
     "hdmb_date": "2026-09-02", "customer": "Thiên Ân JSC", "customer_id": "CUST-THIENAN",
     "value": 320000000, "status": "active"},
]

# Quote estimate is a SEPARATE business object from Finance Actual — the adapter
# must never present one as the other.
QUOTES: list[dict[str, Any]] = [
    {"id": "BG-0306", "customer": "An Phát JSC", "customer_id": "CUST-ANPHAT",
     "status": "accepted", "currency": "VND", "total": 385000000,
     "lines": [
         {"name": "Cước xe TQ Bằng Tường → Hữu Nghị", "amount": 28500000, "currency": "CNY"},
         {"name": "Thủ tục thông quan 2 đầu", "amount": 6500000, "currency": "VND"},
         {"name": "Xe VN Hữu Nghị → Quế Võ", "amount": 7800000, "currency": "VND"},
     ]},
    {"id": "BG-0307", "customer": "Đức Long Co.", "customer_id": "CUST-DUCLONG",
     "status": "accepted", "currency": "VND", "total": 452000000,
     "lines": [
         {"name": "Cước đường bộ TQ + container", "amount": 41200000, "currency": "CNY"},
         {"name": "Thủ tục thông quan", "amount": 8200000, "currency": "VND"},
     ]},
    {"id": "BG-0295", "customer": "Thiên Ân JSC", "customer_id": "CUST-THIENAN",
     "status": "accepted", "currency": "VND", "total": 320000000,
     "lines": [
         {"name": "Cước đường bộ TQ + VN", "amount": 35400000, "currency": "CNY"},
         {"name": "Thủ tục thông quan", "amount": 7400000, "currency": "VND"},
     ]},
]

# ---------------------------------------------------------------------------
# LOG-DOCGEN-01 authority masters (approved legal Company / Agent records).
# Staging identity only — production records live in the real database and are
# never invented by the sandbox.
# ---------------------------------------------------------------------------

# Owner cấp dữ liệu thật 2026-10-21 (nguyên văn: "Mst 0105937262, công ty trường
# thành logistics. Cả 3 tên đều như thế") ⇒ MỘT pháp nhân đứng ở CẢ BA vai trò
# của chuỗi TT_ENTRUSTED_SUB, nên 3 record dưới đây mang CÙNG `legal_name` +
# CÙNG MST và chỉ khác `id` + vai trò. Đây là SEED STAGING; master production
# vẫn ở DB thật và không được seed từ đây.
#
# Vì sao vẫn là 3 record riêng, không gộp thành 1:
#   * vai trò 1 (ký hợp đồng ủy thác) và vai trò 3 (đứng tên nhập khẩu) — writer
#     bắt buộc ``importer_company_id != company_id`` (xem
#     ``core.shipment_document_workflow.project_commercial_flow``) nên 2 id PHẢI
#     khác nhau;
#   * vai trò 2 (đối tác hợp đồng / sub agent) resolve từ ``authority_agents``
#     và KHÔNG BAO GIỜ được promote từ company master, nên phải có row AGENT
#     riêng, MST ghi đúng spelling của AGENT master là ``legal_code``.
# Hệ quả thiết kế: khi TÊN và MST trùng nhau thì thứ DUY NHẤT phân biệt 3 lựa
# chọn bên giao/bên nhận là NHÃN VAI TRÒ do
# ``core.shipment_document_workflow.entrustment_parties`` dựng.
# Id cũ ``TT-COMPANY`` được giữ cho vai trò 1 để không phá tham chiếu sẵn có
# (contract / shipment / partner index đều dùng id này).
AUTHORITY_COMPANIES: list[dict[str, Any]] = [
    {   # Vai trò 1 — pháp nhân ký hợp đồng ủy thác (id cũ, giữ nguyên).
        "company_id": "TT-COMPANY",
        "id": "TT-COMPANY",
        "legal_name": "CÔNG TY TRƯỜNG THÀNH LOGISTICS",
        "tax_or_legal_code": "0105937262",
        "legal_address": "Số 12, Đường Láng Hạ, Ba Đình, Hà Nội",
        "legal_representative": "Nguyễn Thị Thu Hằng",
        "representative_title": "Giám đốc",
        "phone": "0241234567",
        "email": "info@truongthanh.vn",
        "bank_account_holder": "CÔNG TY TRƯỜNG THÀNH LOGISTICS",
        "bank_account_number": "0123456789",
        "bank_name": "Vietcombank",
    },
    {   # Vai trò 3 — pháp nhân đứng tên nhập khẩu. Id KHÁC vai trò 1 (điều kiện
        # của writer); cùng pháp nhân nên cùng tên + cùng MST + cùng hồ sơ.
        "company_id": "TT-COMPANY-IMPORT",
        "id": "TT-COMPANY-IMPORT",
        "legal_name": "CÔNG TY TRƯỜNG THÀNH LOGISTICS",
        "tax_or_legal_code": "0105937262",
        "legal_address": "Số 12, Đường Láng Hạ, Ba Đình, Hà Nội",
        "legal_representative": "Nguyễn Thị Thu Hằng",
        "representative_title": "Giám đốc",
        "phone": "0241234567",
        "email": "info@truongthanh.vn",
        "bank_account_holder": "CÔNG TY TRƯỜNG THÀNH LOGISTICS",
        "bank_account_number": "0123456789",
        "bank_name": "Vietcombank",
    },
]

AUTHORITY_AGENTS: list[dict[str, Any]] = [
    {   # Vai trò 2 — đối tác hợp đồng (sub agent). Cùng pháp nhân Trường Thành
        # nên cùng tên; MST ghi theo spelling của AGENT master: ``legal_code``.
        "agent_id": "AGT-TRUONGTHANH",
        "id": "AGT-TRUONGTHANH",
        "legal_name": "CÔNG TY TRƯỜNG THÀNH LOGISTICS",
        "legal_code": "0105937262",
        "legal_address": "Số 12, Đường Láng Hạ, Ba Đình, Hà Nội",
        "legal_representative": "Nguyễn Thị Thu Hằng",
        "representative_title": "Giám đốc",
        "phone": "0241234567",
        "email": "info@truongthanh.vn",
        "bank_account_holder": "CÔNG TY TRƯỜNG THÀNH LOGISTICS",
        "bank_account_number": "0123456789",
        "bank_name": "Vietcombank",
    },
    {   # Record Phú Anh lịch sử — KHÔNG phải một trong 3 vai trò của chuỗi ủy
        # thác, giữ nguyên để không phá tham chiếu partner/payable sẵn có
        # (contract/shipment cũ + fixture partner-context).
        "agent_id": "AGT-PHUANH",
        "id": "AGT-PHUANH",
        "legal_name": "CÔNG TY TNHH PHÚ ANH LOGISTICS",
        "legal_code": "0315678910",
        "legal_address": "Số 45, Nguyễn Văn Linh, Quận 7, TP. Hồ Chí Minh",
        "legal_representative": "Phạm Văn Thành",
        "representative_title": "Giám đốc",
        "phone": "0281234567",
        "email": "sales@phuanh.vn",
        "bank_account_holder": "PHÚ ANH LOGISTICS",
        "bank_account_number": "9876543210",
        "bank_name": "Techcombank",
        "bank_branch": "Hội sở TP.HCM",
    },
]


def build_canonical_quotes() -> list[dict[str, Any]]:
    """Canonical LOG-C12 quotes, built through the REAL quotation domain service.

    The legacy ``QUOTES`` list above keeps the Phase B finance-estimate shape;
    these are the real quote documents the C1 slice works on (status, service
    lines, calculation, status_history — all produced by ``core.quotations``).
    """
    from core.quotations import new_quote_document, prepare_quote_for_persistence, transition_quote

    def _quote(spec: dict[str, Any], target_status: str) -> dict[str, Any]:
        quote = new_quote_document(spec)
        # Walk the only legal transition path to the target status.
        path = {
            "DRAFT": [],
            "READY_FOR_REVIEW": ["READY_FOR_REVIEW"],
            "SENT": ["READY_FOR_REVIEW", "SENT"],
            "ACCEPTED": ["READY_FOR_REVIEW", "ACCEPTED"],
            "READY_TO_CREATE_SHIPMENT": ["READY_FOR_REVIEW", "ACCEPTED", "READY_TO_CREATE_SHIPMENT"],
        }[target_status]
        for status in path:
            quote = transition_quote(quote, status, actor="staging.seed")
        return prepare_quote_for_persistence(quote, actor="staging.seed")

    specs: list[tuple[dict[str, Any], str]] = [
        (
            {
                "customer_id": "CUST-ANPHAT",
                "customer_name": "An Phát JSC",
                "sales_owner": "Minh Tú",
                "origin": "Bằng Tường (Quảng Tây)",
                "destination": "KCN Quế Võ, Bắc Ninh",
                "route": "Hữu Nghị (Lạng Sơn)",
                "incoterm": "DAP",
                "transport_mode": "Road",
                "goods_description": "Linh kiện điện tử",
                "expected_delivery_date": "2026-09-20",
                "factory_lots": [{"lot_no": 1, "factory_name": "Shenzhen ABC Factory", "pickup_address": "Shenzhen, Guangdong"}],
                "service_lines": [
                    {"code": "DV-VC-TQ", "service_name": "Cước xe TQ Bằng Tường → Hữu Nghị", "unit": "Lần", "qty": 1, "currency": "VND", "cost_unit": 26000000, "sell_unit": 28500000, "tax_pct": 8},
                    {"code": "DV-TTQ", "service_name": "Thủ tục thông quan 2 đầu", "unit": "Lần", "qty": 1, "currency": "VND", "cost_unit": 5200000, "sell_unit": 6500000, "tax_pct": 8},
                ],
                "fx_snapshot": {"rates_to_vnd": {"USD": 25500, "CNY": 3500, "VND": 1}, "source": "Tỷ giá nhập khi báo giá."},
                "entrusted_import": {"active": False, "goods_value": 0, "goods_currency": "USD", "rate_pct": 0, "review_requested": False, "review_reason": "", "high_value_review_policy": {"status": "POLICY_NOT_CONFIGURED"}, "source": ""},
                "remittance_estimate": {"remitted_amount_usd": 0, "bank_fee_pct": 0, "swift_fee_usd": 0, "receiving_bank_fee_usd": 0, "agent_conversion_fee_usd": 0, "rmb_conversion_fee_cny": 0},
                "include_remittance_in_cost": False,
                "assumptions": ["Đây là estimate/quotation, chưa phải nghĩa vụ thanh toán."],
            },
            "ACCEPTED",
        ),
        (
            {
                "customer_id": "CUST-DUCLONG",
                "customer_name": "Đức Long Co.",
                "sales_owner": "Thu Hằng",
                "origin": "Nam Ninh (Quảng Tây)",
                "destination": "KCN Nam Sơn, Hải Phòng",
                "route": "Hữu Nghị (Lạng Sơn)",
                "incoterm": "FOB",
                "transport_mode": "Road",
                "goods_description": "Máy móc cơ khí",
                "expected_delivery_date": "2026-09-25",
                "factory_lots": [{"lot_no": 1, "factory_name": "Nanning Machinery", "pickup_address": "Nanning"}],
                "service_lines": [
                    {"code": "DV-VC-TQ", "service_name": "Cước đường bộ TQ + container", "unit": "Lần", "qty": 1, "currency": "VND", "cost_unit": 38000000, "sell_unit": 41200000, "tax_pct": 8},
                    {"code": "DV-TTQ", "service_name": "Thủ tục thông quan", "unit": "Lần", "qty": 1, "currency": "VND", "cost_unit": 6600000, "sell_unit": 8200000, "tax_pct": 8},
                ],
                "fx_snapshot": {"rates_to_vnd": {"USD": 25500, "CNY": 3500, "VND": 1}, "source": "Tỷ giá nhập khi báo giá."},
                "entrusted_import": {"active": False, "goods_value": 0, "goods_currency": "USD", "rate_pct": 0, "review_requested": False, "review_reason": "", "high_value_review_policy": {"status": "POLICY_NOT_CONFIGURED"}, "source": ""},
                "remittance_estimate": {"remitted_amount_usd": 0, "bank_fee_pct": 0, "swift_fee_usd": 0, "receiving_bank_fee_usd": 0, "agent_conversion_fee_usd": 0, "rmb_conversion_fee_cny": 0},
                "include_remittance_in_cost": False,
                "assumptions": ["Đây là estimate/quotation, chưa phải nghĩa vụ thanh toán."],
            },
            "READY_FOR_REVIEW",
        ),
    ]
    return [_quote(spec, status) for spec, status in specs]


def build_seed_agreements(quotes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """One AGREED agreement frozen from an accepted quote (commercial handoff)."""
    from core.commercial_agreements import (
        build_agreement_from_quote,
        prepare_agreement_for_persistence,
        transition_agreement,
    )

    accepted = next((q for q in quotes if (q.get("status") or "").upper() in ("ACCEPTED", "READY_TO_CREATE_SHIPMENT")), None)
    if accepted is None:
        return []
    agreement = build_agreement_from_quote(accepted, actor="staging.seed")
    agreement = transition_agreement(agreement, "REVIEWING", actor="staging.seed")
    agreement = transition_agreement(agreement, "AGREED", actor="staging.seed")
    agreement["evidence"] = {
        "accepted_quotation": True,
        "signed_contract": False,
        "customer_confirmation": True,
        "entrusted_documentation": False,
        "notes": "Khách đã xác nhận qua email; bằng chứng đánh dấu thủ công.",
    }
    return [prepare_agreement_for_persistence(agreement, actor="staging.seed")]


USERS: list[dict[str, Any]] = [
    {"username": "admin", "full_name": "Quản trị hệ thống", "role": "ADMIN", "active": True},
    {"username": "thuhang", "full_name": "Thu Hằng", "role": "SUPPORT", "active": True},
    {"username": "minhtu", "full_name": "Minh Tú", "role": "SALE", "active": True},
]

TASKS: list[dict[str, Any]] = [
    {"task_id": "TASK-0306-TK", "content": "Khai tờ khai nhập khẩu LO-0306 + nộp thuế",
     "assignee": "thuhang", "deadline": "2026-09-10", "done": False,
     "shipment_id": "LO-0306"},
    {"task_id": "TASK-0308-XE", "content": "Chốt xe TQ và giờ lấy hàng LO-0308",
     "assignee": "thuhang", "deadline": "2026-09-10", "done": False,
     "shipment_id": "LO-0308"},
    {"task_id": "TASK-0295-THU", "content": "Thu nốt công nợ lô LO-0295",
     "assignee": "minhtu", "deadline": "2026-09-15", "done": False,
     "shipment_id": "LO-0295"},
]


def _line(name: str, code: str, qty: float, price: float, cost: float,
          vat: float = 0.0, note: str = "", unit: str = "Lần") -> dict[str, Any]:
    return {
        "id": str(uuid4()),
        "name_full": name,
        "display_name": name,
        "code": code,
        "unit": unit,
        "qty": qty,
        "price": price,
        "cost": cost,
        "vat_line": vat,
        "note": note,
    }


def _payment(request_id: str, date: str, amount: float, note: str,
             actor: str = "minhtu") -> dict[str, Any]:
    return {
        "id": f"PAY-{uuid4().hex.upper()}",
        "request_id": request_id,
        "date": date,
        "amount": amount,
        "note": note,
        "created_by": actor,
    }


def _shipment(
    *,
    sid: str,
    customer: str,
    customer_id: str,
    contract_id: str,
    status: str,
    created: str,
    mode: str = "Truck",
    incoterm: str = "DAP",
    transport: dict[str, Any] | None = None,
    customs: dict[str, Any] | None = None,
    arrival: dict[str, Any] | None = None,
    delivery: dict[str, Any] | None = None,
    details: list[dict[str, Any]] | None = None,
    payments: list[dict[str, Any]] | None = None,
    entrustment: dict[str, Any] | None = None,
    customer_required_date: str = "",
) -> dict[str, Any]:
    doc: dict[str, Any] = {
        "id": sid,
        "shipment_id": sid,
        "customer": customer,
        "client": customer,
        "customer_id": customer_id,
        "contract_id": contract_id,
        "status": status,
        "currency": "VND",
        "version": 0,
        "is_deleted": False,
        "is_archived": False,
        "created_at": _now(),
        "updated_at": _now(),
        **({"customer_required_date": customer_required_date} if customer_required_date else {}),
        "data": {
            "0.0": {"st": status, "created_at": created, "mode": mode, "incoterm": incoterm},
            "1.2": dict(transport or {}),
            "2.4": dict(customs or {}),
            "2.6": dict(arrival or {}),
            "2.7": dict(delivery or {}),
            "3.4": {
                "details": list(details or []),
                "payments": list(payments or []),
                "commission": {"list": [], "total": 0, "note": ""},
            },
            "entrustment": dict(entrustment or {"active": False}),
        },
    }
    return doc


def build_shipments() -> list[dict[str, Any]]:
    """Five shipments covering the operational states the work desk needs."""
    return [
        # 1. Waiting for customs — import declaration still missing.
        _shipment(
            sid="LO-0306", customer="An Phát JSC", customer_id="CUST-ANPHAT",
            contract_id="HDMB-0306", status="pending", created="2026-09-03",
            transport={
                "booking_no": "BKG-0306", "carrier": "Bộ (đường bộ TQ–VN)",
                "mbl": "", "hbl": "", "vessel": "",
                "etd": "2026-09-08", "pol": "Bằng Tường (Quảng Tây)",
                "pod": "Hữu Nghị (Lạng Sơn)", "container_no": "粤A·88T36",
                "qty_pkg": "24 kiện / 18.400 kg",
            },
            customs={
                "tk_no": "", "customs_status": False, "phan_luong": "",
                "gnt": {"nguoi_nop": "An Phát JSC", "mst": "0101234567",
                        "dia_chi": "KCN Quế Võ, Bắc Ninh", "ma_hq": ""},
            },
            arrival={"arrival_date": "2026-09-08", "free_time": 14},
            delivery={
                "truck_no": "", "seal_no": "", "delivery_date": "",
                "phone_receiver": "0912445778",
                "addr": "Kho An Phát — KCN Quế Võ, Bắc Ninh",
                "is_delivered": False,
            },
            details=[
                _line("Cước xe TQ Bằng Tường → Hữu Nghị", "DV-VC-TQ", 1, 98000000, 91000000, 8),
                _line("Thủ tục thông quan 2 đầu", "DV-TTQ", 1, 6500000, 5200000, 8),
            ],
            payments=[
                _payment("SEED-REQ-0306-1", "2026-09-03", 60000000, "Thu tạm ứng đợt 1 theo HDMB-0306"),
            ],
        ),
        # 2. In transit — declaration registered, awaiting clearance result.
        _shipment(
            sid="LO-0307", customer="Đức Long Co.", customer_id="CUST-DUCLONG",
            contract_id="HDNT-0307", status="pending", created="2026-09-04",
            transport={
                "booking_no": "BKG-0307", "carrier": "Bộ (đường bộ TQ–VN)",
                "etd": "2026-09-08", "pol": "Nam Ninh (Quảng Tây)",
                "pod": "Hữu Nghị → Hải Phòng", "container_no": "桂A·12D78",
                "qty_pkg": "40 kiện / 22.100 kg",
            },
            customs={
                "tk_no": "105588421330", "customs_status": False, "phan_luong": "Vàng",
                "gnt": {"nguoi_nop": "Đức Long Co.", "mst": "0312987654",
                        "dia_chi": "KCN Nam Sơn, Hải Phòng", "ma_hq": "14DQ"},
            },
            arrival={"arrival_date": "2026-09-09", "free_time": 10},
            delivery={
                "truck_no": "", "seal_no": "", "delivery_date": "",
                "phone_receiver": "0916778203",
                "addr": "Kho Đức Long — KCN Nam Sơn, Hải Phòng",
                "is_delivered": False,
            },
            details=[
                _line("Cước đường bộ TQ + container", "DV-VC-TQ", 1, 152000000, 141000000, 8),
                _line("Thủ tục thông quan", "DV-TTQ", 1, 8200000, 6600000, 8),
            ],
            payments=[
                _payment("SEED-REQ-0307-1", "2026-09-04", 90000000, "Thu tạm ứng đợt 1"),
            ],
        ),
        # 3. Waiting for pickup — not yet loaded.
        _shipment(
            sid="LO-0308", customer="Minh Đức JSC", customer_id="CUST-MINHDUC",
            contract_id="", status="wait", created="2026-09-06",
            customer_required_date="2026-09-12",
            transport={
                "booking_no": "", "carrier": "", "etd": "2026-09-12",
                "pol": "Đông Bằng (Quảng Tây)", "pod": "Hữu Nghị (Lạng Sơn)",
                "container_no": "", "qty_pkg": "",
            },
            customs={"tk_no": "", "customs_status": False, "phan_luong": ""},
            arrival={"arrival_date": "2026-09-12", "free_time": 14},
            delivery={
                "truck_no": "", "seal_no": "", "delivery_date": "",
                "phone_receiver": "", "addr": "Kho Minh Đức — KCN Yên Phong, Bắc Ninh",
                "is_delivered": False,
            },
            details=[
                _line("Cước xe TQ Đông Bằng → Hữu Nghị", "DV-VC-TQ", 1, 62000000, 57000000, 8),
            ],
            payments=[],
        ),
        # 4. Cleared, awaiting delivery confirmation.
        _shipment(
            sid="LO-0299", customer="Hồng Hà Co.", customer_id="CUST-HONGHA",
            contract_id="", status="pending", created="2026-09-01",
            customer_required_date="2026-09-08",
            transport={
                "booking_no": "BKG-0299", "carrier": "Bộ (đường bộ TQ–VN)",
                "etd": "2026-09-05", "pol": "Bằng Tường (Quảng Tây)",
                "pod": "Hữu Nghị (Lạng Sơn)", "container_no": "粤B·31K09",
                "qty_pkg": "18 kiện / 12.600 kg",
            },
            customs={
                "tk_no": "105579900211", "customs_status": True, "phan_luong": "Xanh",
                "gnt": {"nguoi_nop": "Hồng Hà Co.", "mst": "0103456789",
                        "dia_chi": "KCN Yên Phong, Bắc Ninh", "ma_hq": "14DQ"},
            },
            arrival={"arrival_date": "2026-09-06", "free_time": 7},
            delivery={
                "truck_no": "29H-481.36", "seal_no": "Lê Đức / 0904118822",
                "delivery_date": "2026-09-10", "phone_receiver": "0904118822",
                "addr": "Kho Hồng Hà — KCN Yên Phong, Bắc Ninh",
                "is_delivered": False,
            },
            details=[
                _line("Cước xe TQ + VN", "DV-VC-TQ", 1, 88000000, 79500000, 8),
                _line("Thủ tục thông quan", "DV-TTQ", 1, 6000000, 4800000, 8),
            ],
            payments=[
                _payment("SEED-REQ-0299-1", "2026-09-02", 60000000, "Thu tạm ứng đợt 1"),
            ],
        ),
        # 5. Delivered — PXK generation is permitted for this one.
        _shipment(
            sid="LO-0295", customer="Thiên Ân JSC", customer_id="CUST-THIENAN",
            contract_id="HDMB-0295", status="done", created="2026-09-02",
            transport={
                "booking_no": "BKG-0295", "carrier": "Bộ (đường bộ TQ–VN)",
                "etd": "2026-09-04", "pol": "Quảng Châu", "pod": "Mộc Bài (Tây Ninh)",
                "container_no": "粤B·90M21", "qty_pkg": "30 kiện / 19.800 kg",
            },
            customs={
                "tk_no": "105571288466", "customs_status": True, "phan_luong": "Xanh",
                "gnt": {"nguoi_nop": "Thiên Ân JSC", "mst": "0104567890",
                        "dia_chi": "TP. Thủ Đức, TP.HCM", "ma_hq": "47B1"},
            },
            arrival={"arrival_date": "2026-09-06", "free_time": 7},
            delivery={
                "truck_no": "51D-720.44", "seal_no": "Ngô Văn Hải / 0908334190",
                "delivery_date": "2026-09-09", "phone_receiver": "0908334190",
                "addr": "Kho Thiên Ân — KP.2, Thủ Đức, TP.HCM",
                "is_delivered": True,
                "delivered_at": "2026-09-09",
                "receiver_name": "A. Kiệt",
                "receiver_title": "Thủ kho",
                "delivery_location": "Kho Thiên Ân — KP.2, Thủ Đức, TP.HCM",
            },
            details=[
                _line("Cước đường bộ TQ + VN", "DV-VC-TQ", 1, 128000000, 119000000, 8),
                _line("Thủ tục thông quan", "DV-TTQ", 1, 7400000, 6100000, 8),
            ],
            payments=[
                _payment("SEED-REQ-0295-1", "2026-09-02", 100000000, "Thu tạm ứng đợt 1"),
                _payment("SEED-REQ-0295-2", "2026-09-08", 30000000, "Thu tạm ứng đợt 2"),
            ],
        ),
    ]


def seed_staging(actor: str = "staging.support") -> dict[str, int]:
    """Insert the staging seed into the active (staging) database.

    Reference rows (customers/contracts/quotes/tasks/users) are inserted
    directly — they represent data that already exists in a real database.
    Shipments are written through the CANONICAL writer
    ``core.database.save_shipment_atomic`` so the seed itself exercises the
    real validation → write → audit path and the Lịch sử tab shows genuine
    audit history rather than invented timeline entries.
    """
    from core.database import get_db, save_shipment_atomic

    db = get_db()
    if db is None:
        raise RuntimeError("Staging database unavailable — cannot seed.")

    counts: dict[str, int] = {}

    def _seed_many(collection: str, docs: list[dict[str, Any]], key: str) -> None:
        inserted = 0
        for doc in docs:
            payload = copy.deepcopy(doc)
            if db[collection].find_one({key: payload[key]}):
                continue
            payload.setdefault("created_at", _now())
            payload["updated_at"] = _now()
            db[collection].insert_one(payload)
            inserted += 1
        counts[collection] = inserted

    _seed_many("customers", CUSTOMERS, "id")
    _seed_many("contracts", CONTRACTS, "id")
    _seed_many("quotes", QUOTES, "id")
    _seed_many("users", USERS, "username")
    _seed_many("tasks", TASKS, "task_id")
    _seed_many("authority_companies", AUTHORITY_COMPANIES, "id")
    _seed_many("authority_agents", AUTHORITY_AGENTS, "id")
    # Issue #162 — the ONE neutral Work Module fixture, and ONLY in the isolated
    # staging sandbox. It is an architecture verification fixture, not a legal
    # claim about any commodity, and a real database is never given demo
    # procedures implicitly: operators publish templates through the bounded
    # authoring surface.
    from core.work_modules import demo_template

    _seed_many("work_module_templates", [demo_template()], "id")

    # Canonical LOG-C12 quotes + a commercial agreement, built through the REAL
    # domain services (core.quotations / core.commercial_agreements).
    canonical_quotes = build_canonical_quotes()
    _seed_many("quotes", canonical_quotes, "id")
    _seed_many("agreements", build_seed_agreements(canonical_quotes), "id")

    written = 0
    bootstrap = {
        "username": actor,
        "full_name": "Staging bootstrap",
        "role": "ADMIN",
        "user_id": "STAGING-BOOTSTRAP",
    }
    # Seeding the sandbox is a backend bootstrap step, not a user action, so it
    # runs under an explicit bootstrap identity and restores whatever actor was
    # logged in afterwards. RBAC is never bypassed for real user writes.
    try:
        import streamlit as st

        previous = st.session_state.get("current_user")
        st.session_state["current_user"] = dict(bootstrap)
    except Exception:  # pragma: no cover - non-Streamlit context
        previous = None

    try:
        for doc in build_shipments():
            sid = doc["id"]
            if db.shipments.find_one({"id": sid}):
                continue
            if save_shipment_atomic(copy.deepcopy(doc), actor=actor):
                written += 1
    finally:
        try:
            import streamlit as st

            st.session_state["current_user"] = previous
        except Exception:  # pragma: no cover
            pass

    counts["shipments"] = written
    return counts

