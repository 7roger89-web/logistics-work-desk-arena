"""Small authoritative catalog for Shipment Detail's document picker.

This is a selector over existing document paths, not a template platform. The
catalog owns stable IDs and the existing adapter names; the view-model adds
only server-verified availability and the UI never invents an action.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

SELECTION_FIELD = "document_template_ids"


@dataclass(frozen=True)
class ShipmentDocumentTemplate:
    id: str
    label: str
    category: str
    adapter: str
    document_type: str
    active: bool = True


# V1 contains only current-main generators/actions. Owner-supplied samples are
# intentionally not included; their original binaries are not in this repo.
SHIPMENT_DOCUMENT_CATALOG: tuple[ShipmentDocumentTemplate, ...] = (
    ShipmentDocumentTemplate(
        "HDNT", "Hợp đồng nguyên tắc (HDNT)", "Hợp đồng", "CONTRACT_DOCGEN", "HDNT"
    ),
    ShipmentDocumentTemplate(
        "PL", "Phụ lục hợp đồng (PL)", "Hợp đồng", "CONTRACT_DOCGEN", "PL"
    ),
    ShipmentDocumentTemplate(
        "HDMB", "Hợp đồng mua bán (HDMB)", "Hợp đồng", "CONTRACT_DOCGEN", "HDMB"
    ),
    ShipmentDocumentTemplate(
        "PXK", "Phiếu xuất kho (PXK)", "Kho", "PXK_DOCGEN", "PXK"
    ),
    ShipmentDocumentTemplate(
        "GNT", "Giấy nộp thuế (GNT)", "Hải quan", "GNT_BUILDER", "GNT"
    ),
)


class SelectionValidationError(ValueError):
    """A fail-closed shipment document selection refusal."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def active_template_ids(
    catalog: Sequence[ShipmentDocumentTemplate] = SHIPMENT_DOCUMENT_CATALOG,
) -> tuple[str, ...]:
    return tuple(template.id for template in catalog if template.active)


def validate_selected_template_ids(
    value: Any,
    *,
    catalog: Sequence[ShipmentDocumentTemplate] = SHIPMENT_DOCUMENT_CATALOG,
) -> list[str]:
    """Validate the exact bounded ID list and return it in catalog order."""
    if not isinstance(value, list):
        raise SelectionValidationError(
            "INVALID_SELECTION", "Danh sách biểu mẫu phải là một danh sách mã hợp lệ."
        )

    by_id = {template.id: template for template in catalog}
    requested: set[str] = set()
    for raw in value:
        if not isinstance(raw, str) or not raw.strip():
            raise SelectionValidationError(
                "INVALID_TEMPLATE_ID", "Mã biểu mẫu không hợp lệ."
            )
        template_id = raw.strip()
        template = by_id.get(template_id)
        if template is None:
            raise SelectionValidationError(
                "UNKNOWN_TEMPLATE", f"Biểu mẫu {template_id} không có trong danh mục V1."
            )
        if not template.active:
            raise SelectionValidationError(
                "INACTIVE_TEMPLATE", f"Biểu mẫu {template_id} hiện không hoạt động."
            )
        if template_id in requested:
            raise SelectionValidationError(
                "DUPLICATE_TEMPLATE", f"Biểu mẫu {template_id} bị chọn lặp."
            )
        requested.add(template_id)

    # Catalog order is stable, independent of browser order.
    return [template.id for template in catalog if template.active and template.id in requested]


def project_selected_template_ids(
    value: Any,
    *,
    catalog: Sequence[ShipmentDocumentTemplate] = SHIPMENT_DOCUMENT_CATALOG,
) -> list[str]:
    """Project only recognized active IDs; corrupt/legacy values never enable actions."""
    if not isinstance(value, list):
        return []
    requested = {item.strip() for item in value if isinstance(item, str) and item.strip()}
    return [
        template.id
        for template in catalog
        if template.active and template.id in requested
    ]


def project_catalog(
    *,
    contract_templates_available: bool,
    pxk_template_available: bool,
    storage_configured: bool,
    catalog: Sequence[ShipmentDocumentTemplate] = SHIPMENT_DOCUMENT_CATALOG,
) -> list[dict[str, Any]]:
    """Project catalog entries with server-owned availability and no file paths."""
    rows: list[dict[str, Any]] = []
    for template in catalog:
        available = False
        reason = "Biểu mẫu không hoạt động."
        if template.active:
            if template.adapter == "CONTRACT_DOCGEN":
                available = bool(contract_templates_available)
                reason = "Mẫu hợp đồng hiện chưa sẵn sàng."
            elif template.adapter == "PXK_DOCGEN":
                available = bool(pxk_template_available and storage_configured)
                reason = (
                    "Mẫu PXK hiện chưa sẵn sàng."
                    if not pxk_template_available
                    else "Kho chứng từ chưa sẵn sàng để lưu tệp PXK."
                )
            elif template.adapter == "GNT_BUILDER":
                available = bool(storage_configured)
                reason = "Kho chứng từ chưa sẵn sàng để lưu tệp GNT."
            else:
                # Unknown adapters remain visible as unavailable and can never
                # be dispatched by a client that only understands V1 adapters.
                reason = "Tác vụ này chưa được hỗ trợ trong bộ chọn V1."

        rows.append(
            {
                "id": template.id,
                "label": template.label,
                "category": template.category,
                "adapter": template.adapter,
                "documentType": template.document_type,
                "active": bool(template.active),
                "available": available,
                "availabilityReason": "" if available else reason,
            }
        )
    return rows
