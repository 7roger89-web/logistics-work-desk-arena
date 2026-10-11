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


# V1 contains only current-main generators/actions. Issue #168 adds the FIRST
# Owner-supplied sample (FORM_07) from its exact verified binary, sanitized and
# SHA-pinned in Git (assets/templates/form07/); the remaining six samples stay
# queued for later evidence-driven slices.
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
    ShipmentDocumentTemplate(
        "FORM_07",
        "Biên bản giao nhận hàng hóa (FORM_07)",
        "Giao nhận",
        "FORM07_DOCGEN",
        "FORM_07",
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


def with_uploaded_templates(
    uploaded: Sequence[ShipmentDocumentTemplate] = (),
    catalog: Sequence[ShipmentDocumentTemplate] = SHIPMENT_DOCUMENT_CATALOG,
) -> tuple[ShipmentDocumentTemplate, ...]:
    """The effective picker catalog: the code-owned V1 entries first, then the
    Admin-published uploads (Issue #193) in their own stable order.

    This is the ONLY place the two lists are joined, so selection validation,
    availability projection and the UI all see exactly one catalog.  A second
    document system is deliberately not created: uploaded templates are extra
    rows in the same catalog, dispatched through the same picker.
    """
    seen = {template.id for template in catalog}
    extra = tuple(
        template
        for template in uploaded
        if template.active and template.id and template.id not in seen
    )
    return tuple(catalog) + extra


def effective_catalog(
    catalog: Sequence[ShipmentDocumentTemplate] = SHIPMENT_DOCUMENT_CATALOG,
) -> tuple[ShipmentDocumentTemplate, ...]:
    """The ONE runtime picker catalog, including Admin-published uploads.

    LOGI-193.  This is the single authority both the picker projection and the
    selection validator resolve through, so an uploaded template is an extra
    row in the existing catalog rather than a second document system.  An
    unreadable template registry degrades to the code-owned catalog only — it
    never blanks the picker.
    """
    from core.docgen import uploaded_template_store as template_store

    try:
        uploaded = template_store.catalog_templates()
    except Exception:  # noqa: BLE001 - registry/storage failure degrades to V1
        uploaded = ()
    return with_uploaded_templates(uploaded, catalog=catalog)


def project_catalog(
    *,
    contract_templates_available: bool,
    pxk_template_available: bool,
    storage_configured: bool,
    form07_template_available: bool = False,
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
            elif template.adapter == "FORM07_DOCGEN":
                available = bool(form07_template_available and storage_configured)
                reason = (
                    "Mẫu biên bản giao nhận (FORM_07) chưa sẵn sàng."
                    if not form07_template_available
                    else "Kho chứng từ chưa sẵn sàng để lưu tệp biên bản giao nhận."
                )
            elif template.adapter == "UPLOADED_DOCGEN":
                # Issue #193 — an Admin-published upload only needs the existing
                # document store to save its output; the template bytes are
                # already in the store (a published version pinned them).
                available = bool(storage_configured)
                reason = "Kho chứng từ chưa sẵn sàng để lưu tệp biểu mẫu đã điền."
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
