"""Bounded delivery-note XLSX generation from canonical shipment facts.

The production legal wording/layout remains Owner-controlled. This module only
fills a named worksheet contract (delivery_note) in the existing
truong-thanh-agent.xlsx template. It never synthesizes a production template
or legal numbering.

UNKNOWN != ZERO: absent cargo/delivery facts remain missing and block generation
when they are required; optional numeric facts are written blank, never as 0.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from core.docgen.template_engine import mutate_xlsx
from core.shipment_operations import cargo_summary_for_read, compatibility_facts
from core.utils import parse_date

DOCUMENT_TYPE = "DELIVERY_NOTE"
SHEET_NAME = "delivery_note"


class DeliveryNoteError(RuntimeError):
    """Fail-closed delivery-note generation error."""

    def __init__(self, code: str, reason: str, *, missing: tuple[str, ...] = ()) -> None:
        self.code = code
        self.reason = reason
        self.missing = missing
        super().__init__(reason)


def _text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _section(shipment: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    data = shipment.get("data")
    if not isinstance(data, Mapping):
        return {}
    value = data.get(key)
    return value if isinstance(value, Mapping) else {}


def _date_ddmmyyyy(value: Any) -> str:
    if value is None or str(value).strip() == "":
        return ""
    try:
        return parse_date(value).strftime("%d/%m/%Y")
    except Exception as exc:
        raise DeliveryNoteError("INVALID_DATE", f"Ngày phiếu giao hàng không hợp lệ: {value}") from exc


def _template_hash(template_path: str) -> str:
    try:
        raw = Path(template_path).read_bytes()
    except OSError as exc:
        raise DeliveryNoteError("TEMPLATE_NOT_FOUND", "Không đọc được template Phiếu giao hàng.") from exc
    return hashlib.sha256(raw).hexdigest()


def _assert_template_contract(template_path: str) -> None:
    """Require the Owner workbook to expose the bounded delivery-note sheet."""
    try:
        import openpyxl

        workbook = openpyxl.load_workbook(template_path, read_only=True, data_only=False)
        try:
            if SHEET_NAME not in workbook.sheetnames:
                raise DeliveryNoteError(
                    "TEMPLATE_SHEET_MISSING",
                    "Template XLSX chưa có sheet delivery_note; không tự chế mẫu pháp lý.",
                )
        finally:
            workbook.close()
    except DeliveryNoteError:
        raise
    except Exception as exc:
        raise DeliveryNoteError("TEMPLATE_INVALID", f"Template XLSX không hợp lệ: {exc}") from exc


def inspect_delivery_note_source(
    shipment: Mapping[str, Any],
    *,
    customer: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return canonical source facts and the exact missing-field list."""
    shipment_id = _text(shipment.get("id") or shipment.get("shipment_id"))
    customer = customer or {}
    customer_name = _text(
        shipment.get("customer")
        or shipment.get("client")
        or customer.get("name")
        or customer.get("legal_name")
    )
    customer_tax_code = _text(customer.get("tax_code") or customer.get("mst") or customer.get("legal_code"))

    delivery = _section(shipment, "2.7")
    delivered = bool(delivery.get("is_delivered"))
    delivery_date = _text(delivery.get("delivered_at") or delivery.get("delivery_date"))
    delivery_location = _text(delivery.get("delivery_location") or delivery.get("addr"))
    receiver_name = _text(delivery.get("receiver_name"))
    receiver_title = _text(delivery.get("receiver_title"))
    receiver_phone = _text(delivery.get("phone_receiver"))

    cargo, cargo_structured = cargo_summary_for_read(shipment)
    goods_description = _text(cargo.get("goods_description"))
    operational = compatibility_facts(shipment)
    delivery_unit = operational.get("delivery_unit")
    delivery_unit = delivery_unit if isinstance(delivery_unit, Mapping) else {}

    missing: list[str] = []
    if not shipment_id:
        missing.append("Thiếu mã lô hàng.")
    if not customer_name:
        missing.append("Thiếu khách hàng của lô.")
    if not delivered:
        missing.append("Lô chưa xác nhận đã giao hàng.")
    if not delivery_date:
        missing.append("Thiếu ngày giao hàng thực tế.")
    if not delivery_location:
        missing.append("Thiếu địa điểm giao hàng thực tế.")
    if not receiver_name:
        missing.append("Thiếu người nhận hàng.")
    if not goods_description:
        missing.append("Thiếu mô tả hàng hóa trong cargo_summary.")

    return {
        "ready": not missing,
        "missing": missing,
        "shipment_id": shipment_id,
        "customer_name": customer_name,
        "customer_tax_code": customer_tax_code,
        "delivery_date": delivery_date,
        "delivery_location": delivery_location,
        "receiver_name": receiver_name,
        "receiver_title": receiver_title,
        "receiver_phone": receiver_phone,
        "goods_description": goods_description,
        "package_count": cargo.get("package_count"),
        "package_type": _text(cargo.get("package_type")),
        "gross_weight_kg": cargo.get("gross_weight_kg"),
        "cbm": cargo.get("cbm"),
        "dimensions": _text(cargo.get("dimensions")),
        "cargo_note": _text(cargo.get("note")),
        "cargo_structured": bool(cargo_structured),
        "truck_plate": _text(delivery_unit.get("number")),
        "driver_name": _text(delivery_unit.get("driver_name")),
        "driver_phone": _text(delivery_unit.get("driver_phone")),
    }


def build_delivery_note_fill(
    *,
    delivery_note_no: str,
    delivery_note_date: str,
    source: Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    """Build the bounded cell-fill contract for the Owner worksheet."""
    note_no = _text(delivery_note_no)
    note_date = _text(delivery_note_date)
    missing = []
    if not note_no:
        missing.append("Thiếu số Phiếu giao hàng.")
    if not note_date:
        missing.append("Thiếu ngày Phiếu giao hàng.")
    if missing:
        raise DeliveryNoteError("MISSING_DOCUMENT_IDENTITY", " ".join(missing), missing=tuple(missing))
    source_missing = tuple(str(item) for item in (source.get("missing") or []) if str(item).strip())
    if source_missing:
        raise DeliveryNoteError(
            "MISSING_SOURCE_FACTS",
            "Chưa đủ dữ liệu tạo Phiếu giao hàng: " + " ".join(source_missing),
            missing=source_missing,
        )

    def optional_number(value: Any) -> Any:
        return "" if value is None or str(value).strip() == "" else value

    return {
        SHEET_NAME: {
            "B4": note_no,
            "B5": _date_ddmmyyyy(note_date),
            "B6": _text(source.get("shipment_id")),
            "B7": _text(source.get("customer_name")),
            "B8": _text(source.get("customer_tax_code")),
            "B10": _date_ddmmyyyy(source.get("delivery_date")),
            "B11": _text(source.get("delivery_location")),
            "B12": _text(source.get("receiver_name")),
            "B13": _text(source.get("receiver_title")),
            "B14": _text(source.get("receiver_phone")),
            "B16": _text(source.get("goods_description")),
            "B17": optional_number(source.get("package_count")),
            "B18": _text(source.get("package_type")),
            "B19": optional_number(source.get("gross_weight_kg")),
            "B20": optional_number(source.get("cbm")),
            "B21": _text(source.get("dimensions")),
            "B22": _text(source.get("cargo_note")),
            "B24": _text(source.get("truck_plate")),
            "B25": _text(source.get("driver_name")),
            "B26": _text(source.get("driver_phone")),
        }
    }


def generate_delivery_note_xlsx(
    template_path: str,
    *,
    shipment: Mapping[str, Any],
    customer: Mapping[str, Any] | None,
    delivery_note_no: str,
    delivery_note_date: str,
) -> dict[str, Any]:
    """Generate XLSX bytes without persisting business or file state."""
    if not _text(template_path):
        raise DeliveryNoteError(
            "TEMPLATE_OWNER_GATE",
            "Chưa có template Phiếu giao hàng trong DOCGEN_TEMPLATE_DIR.",
        )
    _assert_template_contract(template_path)
    source = inspect_delivery_note_source(shipment, customer=customer)
    fill = build_delivery_note_fill(
        delivery_note_no=delivery_note_no,
        delivery_note_date=delivery_note_date,
        source=source,
    )
    output = mutate_xlsx(template_path, fill)
    if output[:2] != b"PK":
        raise DeliveryNoteError("OUTPUT_INVALID", "Phiếu giao hàng sinh ra không phải XLSX hợp lệ.")

    safe_no = _text(delivery_note_no).replace("/", "-").replace("\\", "-")
    return {
        "bytes": output,
        "document_type": DOCUMENT_TYPE,
        "output_file_name": f"PHIEU_GIAO_HANG_{safe_no}.xlsx",
        "output_hash": hashlib.sha256(output).hexdigest(),
        "template_hash": _template_hash(template_path),
        "source_snapshot": {
            "delivery_note_no": _text(delivery_note_no),
            "delivery_note_date": _text(delivery_note_date),
            **{key: value for key, value in source.items() if key not in {"ready", "missing"}},
        },
        "source_reference": f"shipment:{source.get('shipment_id')}:data.2.7+cargo_summary",
    }
