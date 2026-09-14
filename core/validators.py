"""Validation có cấu trúc cho Shipment và dữ liệu tài chính."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from core.logic import calculate_from_shipment
from core.utils import parse_date_optional, to_decimal


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str
    field: str = ""


@dataclass
class ValidationResult:
    errors: list[ValidationIssue] = field(default_factory=list)
    warnings: list[ValidationIssue] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.errors

    @property
    def message(self) -> str:
        issues = self.errors or self.warnings
        return "\n".join(issue.message for issue in issues) if issues else "Hợp lệ"


def validate_shipment(ship_obj: dict[str, Any]) -> ValidationResult:
    result = ValidationResult()
    sid = str(ship_obj.get("id") or ship_obj.get("shipment_id") or "").strip()
    customer = str(ship_obj.get("customer") or ship_obj.get("client") or "").strip()
    if not sid:
        result.errors.append(ValidationIssue("SHIPMENT_ID_REQUIRED", "Mã lô không được để trống.", "id"))
    if not customer or customer in {"--Chọn--", "None"}:
        result.errors.append(ValidationIssue("CUSTOMER_REQUIRED", "Vui lòng chọn khách hàng.", "customer"))

    data = ship_obj.get("data", {}) if isinstance(ship_obj.get("data", {}), dict) else {}
    etd = parse_date_optional(data.get("1.2", {}).get("etd"))
    eta = parse_date_optional(data.get("2.6", {}).get("arrival_date"))
    delivery = parse_date_optional(data.get("2.7", {}).get("delivery_date"))
    if etd and eta and etd > eta:
        result.warnings.append(ValidationIssue("ETD_AFTER_ETA", "ETD đang sau ETA; cần kiểm tra lại.", "data.1.2.etd"))
    if eta and delivery and delivery < eta:
        result.warnings.append(ValidationIssue("DELIVERY_BEFORE_ETA", "Ngày giao hàng đang trước ETA.", "data.2.7.delivery_date"))

    # LOGI_SHIPMENT_OPERATIONAL_DATA_V1: structured operational collections
    # are validated at the canonical shipment boundary too, not only by the
    # component handler.  This protects every existing save_shipment_atomic
    # caller while leaving legacy scalar-only documents untouched.
    from core.shipment_operations import normalize_cargo_summary, normalize_transport_legs

    transport = data.get("1.2", {}) if isinstance(data.get("1.2", {}), dict) else {}
    if "transport_legs" in transport:
        try:
            normalize_transport_legs(transport.get("transport_legs"))
        except ValueError as exc:
            result.errors.append(ValidationIssue(
                "INVALID_TRANSPORT_LEGS", str(exc), "data.1.2.transport_legs"
            ))
    if "cargo_summary" in transport:
        try:
            normalize_cargo_summary(transport.get("cargo_summary"))
        except ValueError as exc:
            result.errors.append(ValidationIssue(
                "INVALID_CARGO_SUMMARY", str(exc), "data.1.2.cargo_summary"
            ))

    finance = data.get("3.4", {}) if isinstance(data.get("3.4", {}), dict) else {}
    for index, item in enumerate(finance.get("details", [])):
        qty = to_decimal(item.get("qty", 1))
        cost = to_decimal(item.get("cost", item.get("price_in", 0)))
        price = to_decimal(item.get("price", item.get("price_out", 0)))
        vat = to_decimal(item.get("vat_line", item.get("vat", 0)))
        if qty <= 0:
            result.errors.append(ValidationIssue("INVALID_QTY", f"Dịch vụ dòng {index + 1} phải có số lượng lớn hơn 0.", f"data.3.4.details.{index}.qty"))
        if cost < 0 or price < 0:
            result.errors.append(ValidationIssue("NEGATIVE_PRICE", f"Dịch vụ dòng {index + 1} không được có giá âm.", f"data.3.4.details.{index}"))
        if vat < 0 or vat > 100:
            result.errors.append(ValidationIssue("INVALID_VAT", f"VAT dòng {index + 1} phải từ 0 đến 100%.", f"data.3.4.details.{index}.vat"))

    seen_payment_ids: set[str] = set()
    for index, payment in enumerate(finance.get("payments", [])):
        amount = to_decimal(payment.get("amount"))
        if amount <= 0:
            result.errors.append(ValidationIssue("INVALID_PAYMENT", f"Thanh toán dòng {index + 1} phải lớn hơn 0.", f"data.3.4.payments.{index}.amount"))
        pid = str(payment.get("id", "")).strip()
        if pid and pid in seen_payment_ids:
            result.errors.append(ValidationIssue("DUPLICATE_PAYMENT_ID", f"Thanh toán dòng {index + 1} bị trùng mã.", f"data.3.4.payments.{index}.id"))
        if pid:
            seen_payment_ids.add(pid)

    summary = calculate_from_shipment(ship_obj)
    if float(summary["profit"]) < 0:
        result.warnings.append(ValidationIssue("NEGATIVE_PROFIT", "Lô hàng đang lỗ theo doanh thu chưa VAT.", "data.3.4"))
    if float(summary["debt"]) < -1000:
        result.warnings.append(ValidationIssue("OVERPAYMENT", "Khách đã thanh toán vượt tổng phải thu trên 1.000 VNĐ.", "data.3.4.payments"))
    if ship_obj.get("status") == "done" and not data.get("2.7", {}).get("is_delivered", False):
        result.warnings.append(ValidationIssue("DONE_NOT_DELIVERED", "Lô đã hoàn thành nhưng chưa đánh dấu giao hàng.", "status"))
    return result


def validate_shipment_logic(ship_obj: dict[str, Any]) -> tuple[bool, str]:
    result = validate_shipment(ship_obj)
    return result.is_valid, result.message
