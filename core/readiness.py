"""Deterministic Readiness & Next Action logic for Logistics App.

This module implements stage-aware readiness gates and derives the primary 
next action for a shipment based on canonical facts. It consumes data from 
the shipment document and related projections.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Mapping, Optional, List

from core.shipment_360 import UNKNOWN

# Readiness Status Vocabulary
READY = "READY"
NOT_READY = "NOT_READY"
BLOCKED = "BLOCKED"
WAITING_EXTERNAL = "WAITING_EXTERNAL"
REVIEW_REQUIRED = "REVIEW_REQUIRED"
FUTURE = "FUTURE"  # Not yet relevant

# Severity Levels
CRITICAL = "critical"
ACTION = "action"
WAITING = "waiting"
INFO = "info"
OK = "ok"

@dataclass
class ReadinessResult:
    stage: str
    status: str
    ready: bool
    reason: str = ""
    missing_items: List[str] = field(default_factory=list)
    blocking_items: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    recommended_action: str = ""
    owner_user_id: Optional[str] = None
    due_at: Optional[date] = None

@dataclass
class NextAction:
    label: str
    severity: str
    stage: str
    recommended_action: str = ""
    missing_items: List[str] = field(default_factory=list)
    owner_user_id: Optional[str] = None
    due_at: Optional[date] = None

def _get_field(shipment: Mapping[str, Any], path: str) -> Any:
    """Helper to get nested fields or top-level fields."""
    if "." not in path:
        return shipment.get(path)
    
    parts = path.split(".")
    current = shipment
    for part in parts:
        if isinstance(current, Mapping):
            current = current.get(part)
        else:
            return None
    return current

def _is_present(value: Any) -> bool:
    return value not in (None, "", UNKNOWN)

def evaluate_pickup_readiness(shipment: Mapping[str, Any]) -> ReadinessResult:
    res = ReadinessResult(stage="Pickup", status=READY, ready=True)
    
    # Facts
    factory = _get_field(shipment, "factory_name")
    contact = _get_field(shipment, "factory_contact")
    phone = _get_field(shipment, "factory_phone")
    address = _get_field(shipment, "pickup_address")
    ready_date = _get_field(shipment, "factory_ready_date")
    
    # Logic
    if not _is_present(factory):
        res.missing_items.append("Tên nhà máy")
    if not _is_present(contact):
        res.missing_items.append("Người liên hệ")
    if not _is_present(phone):
        res.missing_items.append("SĐT nhà máy")
    if not _is_present(address):
        res.missing_items.append("Địa chỉ pickup")
        
    if res.missing_items:
        res.status = NOT_READY
        res.ready = False
        res.reason = "Thiếu thông tin nhà máy/địa điểm để book xe"
        res.recommended_action = "Liên hệ nhà máy lấy thông tin pickup"
    else:
        res.reason = "Đủ thông tin để book xe pickup"
        
    return res

def evaluate_export_readiness(shipment: Mapping[str, Any]) -> ReadinessResult:
    res = ReadinessResult(stage="Xuất khẩu", status=READY, ready=True)
    
    # Context aware: if pickup not done, export is waiting
    pickup_status = _get_field(shipment, "pickup_status")
    if pickup_status != "done":
        res.status = WAITING_EXTERNAL
        res.ready = False
        res.reason = "Đang chờ hoàn tất pickup"
        return res

    # Facts
    china_agent = _get_field(shipment, "china_agent")
    decl_no = _get_field(shipment, "china_export_decl_no")
    
    if not _is_present(china_agent):
        res.missing_items.append("Đại lý Trung Quốc")
    if not _is_present(decl_no):
        res.missing_items.append("Số tờ khai xuất TQ")
        
    if res.missing_items:
        res.status = NOT_READY
        res.ready = False
        res.reason = "Thiếu thông tin thủ tục xuất khẩu"
        res.recommended_action = "Yêu cầu đại lý TQ cung cấp số tờ khai"
        
    return res

def evaluate_customs_readiness(shipment: Mapping[str, Any]) -> ReadinessResult:
    res = ReadinessResult(stage="Hải quan", status=READY, ready=True)
    
    # Facts
    arrival = _get_field(shipment, "border_arrival")
    decl_no = _get_field(shipment, "import_decl_no")
    decl_date = _get_field(shipment, "import_decl_date")
    
    if not _is_present(arrival):
        res.status = WAITING_EXTERNAL
        res.ready = False
        res.reason = "Đang chờ hàng về biên giới"
        return res
        
    if not _is_present(decl_no):
        res.missing_items.append("Số tờ khai nhập")
    if not _is_present(decl_date):
        res.missing_items.append("Ngày tờ khai")
        
    if res.missing_items:
        res.status = NOT_READY
        res.ready = False
        res.reason = "Thiếu thông tin tờ khai hải quan VN"
        res.recommended_action = "Nộp tờ khai hải quan"
        
    return res

def evaluate_delivery_readiness(shipment: Mapping[str, Any]) -> ReadinessResult:
    res = ReadinessResult(stage="Giao hàng", status=READY, ready=True)
    
    # Facts
    customs_status = _get_field(shipment, "customs_status")
    consignee = _get_field(shipment, "consignee")
    address = _get_field(shipment, "delivery_address")
    
    if customs_status != "done":
        res.status = WAITING_EXTERNAL
        res.ready = False
        res.reason = "Đang chờ thông quan"
        return res
        
    if not _is_present(consignee):
        res.missing_items.append("Người nhận hàng")
    if not _is_present(address):
        res.missing_items.append("Địa chỉ giao hàng")
        
    if res.missing_items:
        res.status = NOT_READY
        res.ready = False
        res.reason = "Thiếu thông tin giao hàng"
        res.recommended_action = "Xác nhận địa chỉ và người nhận hàng"
        
    return res

def evaluate_finance_readiness(shipment: Mapping[str, Any], dashboard: Mapping[str, Any]) -> ReadinessResult:
    res = ReadinessResult(stage="Finance", status=READY, ready=True)
    
    # Consume Finance truth from dashboard/projection
    flag = dashboard.get("financial_flag", UNKNOWN)
    
    if flag == "open":
        res.status = NOT_READY
        res.ready = False
        res.reason = "Công nợ còn mở"
        res.recommended_action = "Đối soát và thu hồi công nợ"
    elif flag == "review":
        res.status = REVIEW_REQUIRED
        res.ready = False
        res.reason = "Cần đối soát tài chính"
        res.recommended_action = "Kiểm tra lại các khoản thu/chi"
    elif flag == "unknown":
        res.status = REVIEW_REQUIRED
        res.ready = False
        res.reason = "Thiếu dữ liệu tài chính"
        res.recommended_action = "Bổ sung thông tin thanh toán/hợp đồng"
        
    return res

def get_all_readiness(shipment: Mapping[str, Any], dashboard: Mapping[str, Any]) -> List[ReadinessResult]:
    return [
        evaluate_pickup_readiness(shipment),
        evaluate_export_readiness(shipment),
        evaluate_customs_readiness(shipment),
        evaluate_delivery_readiness(shipment),
        evaluate_finance_readiness(shipment, dashboard)
    ]

def derive_next_action(shipment: Mapping[str, Any], readiness: List[ReadinessResult]) -> NextAction:
    # Priority: Pickup -> Export -> Customs -> Delivery -> Finance
    # Within each, CRITICAL > ACTION > WAITING
    
    # Check for overdue deadlines first (Global Critical)
    required_date = _get_field(shipment, "customer_required_date")
    if required_date and required_date < date.today():
        return NextAction(
            label="Quá hạn giao hàng cho khách",
            severity=CRITICAL,
            stage="Giao hàng",
            recommended_action="Ưu tiên thông quan và giao hàng gấp",
            due_at=required_date
        )

    # Find the first non-ready stage in operational order
    for res in readiness:
        if not res.ready:
            severity = ACTION
            if res.status == BLOCKED: severity = CRITICAL
            if res.status == WAITING_EXTERNAL: severity = WAITING
            
            return NextAction(
                label=res.reason,
                severity=severity,
                stage=res.stage,
                recommended_action=res.recommended_action,
                missing_items=res.missing_items,
                owner_user_id=res.owner_user_id
            )
            
    return NextAction(label="Lô hàng ổn định", severity=OK, stage="Hoàn thành")
