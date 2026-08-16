"""Deterministic, read-only review work items for LOG-C10.

This module composes existing Dashboard, Shipment 360, and Shipment Workspace
projections. It deliberately has no repository or writer imports: a review
item is a signal with provenance and a next action, never a fabricated
resolution state.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import date
from typing import Any

from core.shipment_360 import UNKNOWN
from core.shipment_dashboard import (
    FINANCIAL_OPEN,
    FINANCIAL_REVIEW,
    FINANCIAL_UNKNOWN,
    CRITICAL,
    WARNING,
    build_shipment_dashboard_view,
    sort_dashboard_views,
)
from core.shipment_workspace import build_shipment_workspace_view
from core.utils import parse_date_optional


CATEGORY_OPERATIONAL = "OPERATIONAL"
CATEGORY_DOCUMENT = "DOCUMENT"
CATEGORY_DATA = "DATA QUALITY"
CATEGORY_FINANCIAL = "FINANCIAL"
CATEGORIES = (CATEGORY_OPERATIONAL, CATEGORY_DOCUMENT, CATEGORY_DATA, CATEGORY_FINANCIAL)

STATUS_CRITICAL = "CRITICAL"
STATUS_ATTENTION = "NEEDS ATTENTION"
STATUS_WAITING = "WAITING"
STATUS_REVIEW = "REVIEW"
STATUS_INFO = "INFO"
STATUSES = (STATUS_CRITICAL, STATUS_ATTENTION, STATUS_WAITING, STATUS_REVIEW, STATUS_INFO)

SEVERITY_ORDER = {
    STATUS_CRITICAL: 0,
    STATUS_ATTENTION: 1,
    STATUS_WAITING: 2,
    STATUS_REVIEW: 3,
    STATUS_INFO: 4,
}

_ACTIVE_STATUSES = {"active", "pending", "wait", "waiting", "in_progress", "processing"}
_KNOWN_DOCUMENT_TOKENS = ("known", "present", "available", "uploaded", "có dữ liệu", "đã có", "complete")
_WAITING_DOCUMENT_TOKENS = ("waiting", "wait", "pending", "awaiting", "đang chờ", "chờ")
_MISSING_DOCUMENT_TOKENS = ("missing", "not found", "chưa có", "thiếu", "không có")
_UNKNOWN_DOCUMENT_TOKENS = ("unknown", "chưa rõ", "chưa xác định")
_ISSUE_TOKENS = ("issue", "problem", "hold", "blocked", "delay", "error", "exception", "incident", "lỗi", "vướng")


def _text(value: Any, default: str = UNKNOWN) -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text and text.casefold() not in {"none", "nan", "null"} else default


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _data(shipment: Mapping[str, Any]) -> Mapping[str, Any]:
    return _mapping(shipment.get("data"))


def _section(shipment: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    return _mapping(_data(shipment).get(key))


def _first(shipment: Mapping[str, Any], aliases: Iterable[str], default: Any = None) -> Any:
    for alias in aliases:
        if alias in shipment and shipment.get(alias) not in (None, "", "None", "none"):
            return shipment.get(alias)
        for section in _data(shipment).values():
            if isinstance(section, Mapping) and alias in section and section.get(alias) not in (None, "", "None", "none"):
                return section.get(alias)
    return default


def _present(value: Any) -> bool:
    return value not in (None, "", "None", "none", UNKNOWN, "unknown")


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return _text(value, "").casefold() in {"1", "true", "yes", "y", "required", "có", "co"}


def _active(view: Mapping[str, Any]) -> bool:
    if view.get("is_complete") is True:
        return False
    return _text(view.get("operational_status"), "active").casefold() in _ACTIVE_STATUSES


def _document_bucket(status: Any) -> str:
    normalized = _text(status, UNKNOWN).casefold()
    # Check UNKNOWN before KNOWN: the word "unknown" contains "known".
    if any(token in normalized for token in _UNKNOWN_DOCUMENT_TOKENS):
        return "unknown"
    if any(token in normalized for token in _KNOWN_DOCUMENT_TOKENS):
        return "known"
    if any(token in normalized for token in _WAITING_DOCUMENT_TOKENS):
        return "waiting"
    if any(token in normalized for token in _MISSING_DOCUMENT_TOKENS):
        return "missing"
    return "unknown"


def _issue(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    normalized = _text(value, "").casefold()
    return bool(normalized) and any(token in normalized for token in _ISSUE_TOKENS)


def _identifier(shipment: Mapping[str, Any], fallback: Any = None) -> str:
    return _text(shipment.get("shipment_id") or shipment.get("id") or fallback)


def _entity_context(shipment: Mapping[str, Any], workspace: Mapping[str, Any]) -> dict[str, str]:
    context = _mapping(workspace.get("context"))
    lots = [row for row in workspace.get("factory_lots", []) if isinstance(row, Mapping)]
    factory = next((_text(row.get("factory")) for row in lots if _text(row.get("factory")) != UNKNOWN), UNKNOWN)
    partner = _text(context.get("agent"))
    customer = _text(workspace.get("customer"))
    customer_id = _text(workspace.get("customer_id"))
    return {
        "customer": customer,
        "customer_id": customer_id,
        "factory": factory,
        "partner": partner,
        "factory_key": factory,
        "partner_key": partner,
    }


def _target(kind: str, key: str, *, shipment_id: str) -> dict[str, str]:
    return {"kind": kind, "key": key, "shipment_id": shipment_id}


def _item(
    *,
    shipment_id: str,
    customer: str,
    owner: str,
    entity: Mapping[str, str],
    code: str,
    category: str,
    status: str,
    title: str,
    reason: str,
    next_action: str,
    source: str,
    evidence: str = UNKNOWN,
    target: Mapping[str, str] | None = None,
    detail_key: str = "",
) -> dict[str, Any]:
    return {
        "item_id": f"{shipment_id}:{code}:{detail_key}" if detail_key else f"{shipment_id}:{code}",
        "shipment_id": shipment_id,
        "customer": customer,
        "owner": owner,
        "factory": entity.get("factory", UNKNOWN),
        "partner": entity.get("partner", UNKNOWN),
        "category": category,
        "status": status,
        "severity_rank": SEVERITY_ORDER[status],
        "title": title,
        "reason": reason,
        "next_action": next_action,
        "source": source,
        "evidence": evidence,
        "target": dict(target or _target("shipment", shipment_id, shipment_id=shipment_id)),
        "read_only": True,
    }


def _status_for_alert(alert: Mapping[str, Any]) -> str:
    severity = _text(alert.get("severity"), "info").casefold()
    code = _text(alert.get("code"), "").casefold()
    if severity == CRITICAL or "overdue" in code or "risk" in code:
        return STATUS_CRITICAL
    if severity == WARNING:
        return STATUS_ATTENTION
    if code.startswith("promised") or code.startswith("next_action"):
        return STATUS_WAITING
    return STATUS_INFO


def _alert_category(code: str) -> str:
    normalized = code.casefold()
    if normalized.startswith("finance"):
        return CATEGORY_FINANCIAL
    if normalized in {"missing_customer"}:
        return CATEGORY_DATA
    return CATEGORY_OPERATIONAL


def _add_dashboard_alert_items(
    items: list[dict[str, Any]],
    dashboard: Mapping[str, Any],
    *,
    entity: Mapping[str, str],
) -> None:
    shipment_id = _text(dashboard.get("shipment_id"))
    for alert in dashboard.get("alerts", []):
        if not isinstance(alert, Mapping):
            continue
        code = _text(alert.get("code"), "ALERT")
        if code.casefold().startswith("finance"):
            continue
        category = _alert_category(code)
        status = _status_for_alert(alert)
        title = _text(alert.get("label"), "Cần kiểm tra")
        items.append(
            _item(
                shipment_id=shipment_id,
                customer=_text(dashboard.get("customer")),
                owner=_text(dashboard.get("owner")),
                entity=entity,
                code=code,
                category=category,
                status=status,
                title=title,
                reason=_text(alert.get("detail")),
                next_action=title,
                source=_text(alert.get("source")),
                evidence=_text(alert.get("source")),
            )
        )


def _add_explicit_operational_items(
    items: list[dict[str, Any]],
    shipment: Mapping[str, Any],
    dashboard: Mapping[str, Any],
    workspace: Mapping[str, Any],
    *,
    entity: Mapping[str, str],
    today: date,
) -> None:
    shipment_id = _text(dashboard.get("shipment_id"))
    customer = _text(dashboard.get("customer"))
    owner = _text(dashboard.get("owner"))
    active = _active(dashboard)
    lots = [row for row in workspace.get("factory_lots", []) if isinstance(row, Mapping)]

    if lots and any(_text(row.get("pickup_contact")) == UNKNOWN for row in lots):
        items.append(
            _item(
                shipment_id=shipment_id,
                customer=customer,
                owner=owner,
                entity=entity,
                code="FACTORY_CONTACT_MISSING",
                category=CATEGORY_OPERATIONAL,
                status=STATUS_ATTENTION,
                title="Thiếu factory contact",
                reason="Có factory/lot nhưng chưa có pickup contact để Support phối hợp.",
                next_action="Bổ sung contact nhà máy cho lot liên quan.",
                source="shipment.factories[*].pickup_contact",
                evidence="shipment.factories[*]",
                detail_key="factory-contact",
            )
        )

    ready_values = [row.get("ready_date") for row in lots if _text(row.get("ready_date")) != UNKNOWN]
    explicit_ready = _first(shipment, ("factory_ready_date", "ready_date"))
    if active and lots and not ready_values and not _present(explicit_ready):
        items.append(
            _item(
                shipment_id=shipment_id,
                customer=customer,
                owner=owner,
                entity=entity,
                code="FACTORY_READY_MISSING",
                category=CATEGORY_OPERATIONAL,
                status=STATUS_ATTENTION,
                title="Thiếu ready date",
                reason="Shipment có factory/lot nhưng chưa có mốc sẵn sàng để lập kế hoạch pickup.",
                next_action="Xác nhận ready date với nhà máy.",
                source="shipment.factories[*].ready_date",
                evidence="shipment.factories[*]",
                detail_key="ready-date",
            )
        )

    route = _section(shipment, "1.2")
    logistics = {**route, **_section(shipment, "2.6")}
    weight = _first(shipment, ("weight", "gross_weight", "weight_kg"))
    cbm = _first(shipment, ("cbm", "volume", "volume_cbm"))
    required_fields = _first(shipment, ("required_fields_missing", "missing_required_fields"), [])
    explicit_missing = isinstance(required_fields, (list, tuple, set)) and any(
        "weight" in _text(field, "").casefold() or "cbm" in _text(field, "").casefold()
        for field in required_fields
    )
    if active and ((not _present(weight) and not _present(cbm) and (_present(route.get("booking_no")) or lots)) or explicit_missing):
        items.append(
            _item(
                shipment_id=shipment_id,
                customer=customer,
                owner=owner,
                entity=entity,
                code="WEIGHT_CBM_MISSING",
                category=CATEGORY_OPERATIONAL,
                status=STATUS_ATTENTION,
                title="Thiếu weight / CBM",
                reason="Chưa có weight hoặc CBM để hoàn thiện dữ liệu vận hành của lô.",
                next_action="Bổ sung weight/CBM từ factory hoặc bộ phận vận hành.",
                source="shipment route/structured logistics fields",
                evidence="weight, gross_weight, cbm, volume",
                detail_key="weight-cbm",
            )
        )

    due = parse_date_optional(_first(shipment, ("next_action_due", "action_due_date", "next_action_deadline")))
    action = _first(shipment, ("next_action", "next_step", "action_required"))
    if active and due is not None and due < today and _present(action):
        items.append(
            _item(
                shipment_id=shipment_id,
                customer=customer,
                owner=owner,
                entity=entity,
                code="NEXT_ACTION_OVERDUE",
                category=CATEGORY_OPERATIONAL,
                status=STATUS_CRITICAL,
                title="Next action quá hạn",
                reason=f"Bước tiếp theo '{_text(action)}' có hạn {_text(due.strftime('%d/%m/%Y'))}.",
                next_action=_text(action),
                source="shipment.next_action_due",
                evidence="shipment.next_action + shipment.next_action_due",
                detail_key="next-action",
            )
        )

    for field, label in (("customs_issue", "Vướng mắc hải quan"), ("delivery_issue", "Vướng mắc giao hàng"), ("operational_issue", "Vướng mắc vận hành")):
        value = _first(shipment, (field,))
        if _issue(value):
            items.append(
                _item(
                    shipment_id=shipment_id,
                    customer=customer,
                    owner=owner,
                    entity=entity,
                    code=field.upper(),
                    category=CATEGORY_OPERATIONAL,
                    status=STATUS_CRITICAL,
                    title=label,
                    reason=_text(value),
                    next_action=f"Mở Shipment 360 để kiểm tra {label.casefold()}.",
                    source=f"shipment.{field}",
                    evidence=f"shipment.{field}",
                    detail_key=field,
                )
            )


def _add_document_items(
    items: list[dict[str, Any]],
    dashboard: Mapping[str, Any],
    workspace: Mapping[str, Any],
    *,
    entity: Mapping[str, str],
) -> None:
    shipment_id = _text(dashboard.get("shipment_id"))
    customer = _text(dashboard.get("customer"))
    owner = _text(dashboard.get("owner"))
    unknown_count = 0
    missing_evidence: list[str] = []
    for row in workspace.get("documents", []):
        if not isinstance(row, Mapping):
            continue
        name = _text(row.get("document"), "Chứng từ")
        bucket = _document_bucket(row.get("status"))
        required = _truthy(row.get("required"))
        source = _text(row.get("source"))
        if bucket == "known":
            if source == UNKNOWN:
                missing_evidence.append(name)
            continue
        if bucket == "waiting":
            items.append(
                _item(
                    shipment_id=shipment_id,
                    customer=customer,
                    owner=owner,
                    entity=entity,
                    code="DOCUMENT_WAITING",
                    category=CATEGORY_DOCUMENT,
                    status=STATUS_WAITING,
                    title=f"Đang chờ {name}",
                    reason=f"Trạng thái chứng từ: {_text(row.get('status'))}.",
                    next_action=f"Theo dõi người cung cấp {name}.",
                    source=source,
                    evidence=source,
                    detail_key=name,
                )
            )
        elif bucket == "missing":
            items.append(
                _item(
                    shipment_id=shipment_id,
                    customer=customer,
                    owner=owner,
                    entity=entity,
                    code="DOCUMENT_MISSING",
                    category=CATEGORY_DOCUMENT,
                    status=STATUS_ATTENTION,
                    title=f"Thiếu {name}",
                    reason=f"Chứng từ đang ở trạng thái {_text(row.get('status'))}.",
                    next_action=f"Bổ sung hoặc yêu cầu cung cấp {name}.",
                    source=source,
                    evidence=source,
                    detail_key=name,
                )
            )
        else:
            unknown_count += 1
            if required:
                missing_evidence.append(name)

    if unknown_count:
        items.append(
            _item(
                shipment_id=shipment_id,
                customer=customer,
                owner=owner,
                entity=entity,
                code="DOCUMENT_UNKNOWN",
                category=CATEGORY_DOCUMENT,
                status=STATUS_REVIEW,
                title="Chứng từ UNKNOWN",
                reason=f"Có {unknown_count} mục chứng từ chưa có trạng thái chuẩn; không thể kết luận đầy đủ.",
                next_action="Mở Shipment 360 và kiểm tra evidence hiện có.",
                source="core.shipment_workspace document projection",
                evidence=_text(workspace.get("documents_status")),
                detail_key="unknown",
            )
        )
    if missing_evidence:
        items.append(
            _item(
                shipment_id=shipment_id,
                customer=customer,
                owner=owner,
                entity=entity,
                code="DOCUMENT_EVIDENCE_MISSING",
                category=CATEGORY_DOCUMENT,
                status=STATUS_REVIEW,
                title="Thiếu evidence reference",
                reason="Chứng từ được ghi nhận nhưng chưa có reference/evidence để kiểm tra lại.",
                next_action="Bổ sung reference evidence cho: " + ", ".join(sorted(set(missing_evidence))),
                source="shipment documents/document_registry",
                evidence="document.source / document.evidence / document.uri",
                detail_key="evidence",
            )
        )


def _add_data_quality_items(
    items: list[dict[str, Any]],
    shipment: Mapping[str, Any],
    dashboard: Mapping[str, Any],
    *,
    entity: Mapping[str, str],
) -> None:
    shipment_id = _text(dashboard.get("shipment_id"))
    customer = _text(dashboard.get("customer"))
    owner = _text(dashboard.get("owner"))
    customer_id = _text(shipment.get("customer_id"))
    # A missing optional field is not itself an alert. Only flag an explicit
    # empty mapping slot, which is the source contract that can block context
    # resolution without inventing a mapping from the display name.
    if "customer_id" in shipment and customer not in {UNKNOWN, "Chưa có khách hàng"} and customer_id == UNKNOWN:
        items.append(
            _item(
                shipment_id=shipment_id,
                customer=customer,
                owner=owner,
                entity=entity,
                code="CUSTOMER_MAPPING_UNRESOLVED",
                category=CATEGORY_DATA,
                status=STATUS_REVIEW,
                title="Entity mapping chưa resolve",
                reason="Shipment có tên khách nhưng chưa có customer_id source-bound.",
                next_action="Kiểm tra Customer Context; không tự suy đoán mapping.",
                source="shipment.customer_id / shipment.customer",
                evidence="shipment.customer_id",
                target=_target("entity", customer, shipment_id=shipment_id),
                detail_key="customer",
            )
        )

    legacy = _first(shipment, ("legacy_id", "legacy_identifier", "getfly_id", "source_id"))
    resolved = _first(shipment, ("resolved_id", "canonical_id", "mapping_status"))
    if _present(legacy) and not _present(resolved):
        items.append(
            _item(
                shipment_id=shipment_id,
                customer=customer,
                owner=owner,
                entity=entity,
                code="LEGACY_IDENTIFIER_REVIEW",
                category=CATEGORY_DATA,
                status=STATUS_REVIEW,
                title="Legacy identifier cần kiểm tra",
                reason=f"Nguồn có identifier '{_text(legacy)}' nhưng chưa có mapping canonical rõ ràng.",
                next_action="Kiểm tra provenance trước khi mở hoặc liên kết dữ liệu.",
                source="shipment legacy/source identifier",
                evidence="legacy_id / canonical_id / mapping_status",
                detail_key="legacy",
            )
        )

    missing = _first(shipment, ("required_fields_missing", "missing_required_fields"), [])
    if isinstance(missing, (list, tuple, set)) and missing:
        labels = sorted({_text(value, "field") for value in missing})
        items.append(
            _item(
                shipment_id=shipment_id,
                customer=customer,
                owner=owner,
                entity=entity,
                code="REQUIRED_STRUCTURED_DATA_MISSING",
                category=CATEGORY_DATA,
                status=STATUS_ATTENTION,
                title="Thiếu structured data bắt buộc",
                reason="Các trường source đánh dấu thiếu: " + ", ".join(labels),
                next_action="Bổ sung đúng structured fields; không thay bằng text tự do.",
                source="shipment.required_fields_missing",
                evidence="shipment.required_fields_missing",
                detail_key="required-fields",
            )
        )


def _add_financial_items(
    items: list[dict[str, Any]],
    dashboard: Mapping[str, Any],
    *,
    entity: Mapping[str, str],
) -> None:
    shipment_id = _text(dashboard.get("shipment_id"))
    customer = _text(dashboard.get("customer"))
    owner = _text(dashboard.get("owner"))
    projection = _mapping(dashboard.get("financial_projection"))
    flag = _text(dashboard.get("financial_flag"), FINANCIAL_UNKNOWN)
    if flag in {FINANCIAL_OPEN, FINANCIAL_REVIEW, FINANCIAL_UNKNOWN}:
        if flag == FINANCIAL_OPEN:
            status = STATUS_ATTENTION
            title = "Canonical financial review-required"
            reason = "Projection cho thấy khoản tài chính còn mở; đây không phải thao tác thanh toán."
        elif flag == FINANCIAL_REVIEW:
            status = STATUS_REVIEW
            title = "Cần đối soát tài chính"
            reason = "Projection yêu cầu kiểm tra đối soát trước khi tin cậy số liệu."
        else:
            status = STATUS_REVIEW
            title = "Tài chính UNKNOWN"
            reason = "Chưa đủ dữ liệu/read model để kết luận trạng thái tài chính."
        items.append(
            _item(
                shipment_id=shipment_id,
                customer=customer,
                owner=owner,
                entity=entity,
                code="FINANCIAL_STATUS",
                category=CATEGORY_FINANCIAL,
                status=status,
                title=title,
                reason=reason,
                next_action="Mở Shipment 360 → finance projection để xem nguồn và lý do.",
                source=_text(projection.get("source"), "core.shipment_360 financial projection"),
                evidence=_text(projection.get("read_only"), "read-only projection"),
                detail_key=flag,
            )
        )

    for key, code, title, action in (
        ("unallocated", "FINANCIAL_UNALLOCATED", "Có khoản chưa phân bổ", "Kiểm tra allocation source hiện có."),
        ("unreconciled", "FINANCIAL_RECONCILIATION", "Cần reconciliation", "Kiểm tra read model đối soát hiện có."),
        ("unconfirmed_costs", "FINANCIAL_COST_EVIDENCE", "Thiếu evidence chi phí", "Kiểm tra evidence chi phí; không tự ghi nhận."),
    ):
        metric = _mapping(projection.get(key))
        if metric.get("status") not in (None, UNKNOWN, "UNKNOWN") and metric.get("value") not in (None, ""):
            items.append(
                _item(
                    shipment_id=shipment_id,
                    customer=customer,
                    owner=owner,
                    entity=entity,
                    code=code,
                    category=CATEGORY_FINANCIAL,
                    status=STATUS_REVIEW,
                    title=title,
                    reason=f"Projection ghi nhận giá trị {metric.get('value')} {metric.get('currency') or ''}.".strip(),
                    next_action=action,
                    source=_text(metric.get("source"), "Shipment 360 financial projection"),
                    evidence=_text(metric.get("reason"), UNKNOWN),
                    detail_key=key,
                )
            )


def _target_sort_key(item: Mapping[str, Any]) -> tuple[Any, ...]:
    return (
        int(item.get("severity_rank", 99)),
        _text(item.get("category")),
        _text(item.get("shipment_id")),
        _text(item.get("item_id")),
    )


def build_review_queue_items(
    shipments: Mapping[str, Mapping[str, Any]] | Iterable[Mapping[str, Any]],
    *,
    today: date | None = None,
) -> list[dict[str, Any]]:
    """Build actionable review items without mutating shipment inputs."""

    as_of = today or date.today()
    items: list[dict[str, Any]] = []
    iterable = shipments.items() if isinstance(shipments, Mapping) else enumerate(shipments)
    for key, shipment in iterable:
        if not isinstance(shipment, Mapping):
            continue
        dashboard = build_shipment_dashboard_view(shipment, today=as_of)
        workspace = build_shipment_workspace_view(shipment, today=as_of, financial_view=dashboard.get("financial_projection"))
        entity = _entity_context(shipment, workspace)
        _add_dashboard_alert_items(items, dashboard, entity=entity)
        _add_explicit_operational_items(items, shipment, dashboard, workspace, entity=entity, today=as_of)
        _add_document_items(items, dashboard, workspace, entity=entity)
        _add_data_quality_items(items, shipment, dashboard, entity=entity)
        _add_financial_items(items, dashboard, entity=entity)

    # Deduplicate only exact signal identities. Distinct reasons remain visible.
    deduplicated: dict[str, dict[str, Any]] = {}
    for item in items:
        deduplicated.setdefault(_text(item.get("item_id")), item)
    return sorted(deduplicated.values(), key=_target_sort_key)


def filter_review_queue_items(
    items: Iterable[Mapping[str, Any]],
    *,
    search: str = "",
    category: str | None = None,
    status: str | None = None,
    severity: str | None = None,
    shipment_id: str | None = None,
    customer: str | None = None,
    factory: str | None = None,
    partner: str | None = None,
) -> list[Mapping[str, Any]]:
    """Filter review items without changing their order or contents."""

    needle = search.strip().casefold()

    def selected(value: Any, wanted: str | None) -> bool:
        return not wanted or wanted in {"Tất cả", "__all__"} or _text(value) == wanted

    result: list[Mapping[str, Any]] = []
    for item in items:
        if not selected(item.get("category"), category) or not selected(item.get("status"), status):
            continue
        if severity and severity not in {"Tất cả", "__all__"} and _text(item.get("status")) != severity:
            continue
        if not selected(item.get("shipment_id"), shipment_id) or not selected(item.get("customer"), customer):
            continue
        if not selected(item.get("factory"), factory) or not selected(item.get("partner"), partner):
            continue
        if needle:
            haystack = " ".join(_text(item.get(key)) for key in ("item_id", "shipment_id", "customer", "owner", "factory", "partner", "title", "reason", "next_action", "source")).casefold()
            if needle not in haystack:
                continue
        result.append(item)
    return result


def summarize_review_queue(items: Iterable[Mapping[str, Any]]) -> dict[str, int]:
    rows = list(items)
    return {
        "total": len(rows),
        "critical": sum(1 for item in rows if item.get("status") == STATUS_CRITICAL),
        "attention": sum(1 for item in rows if item.get("status") == STATUS_ATTENTION),
        "waiting": sum(1 for item in rows if item.get("status") == STATUS_WAITING),
        "review": sum(1 for item in rows if item.get("status") == STATUS_REVIEW),
        "shipments": len({_text(item.get("shipment_id")) for item in rows}),
    }


__all__ = [
    "CATEGORIES",
    "CATEGORY_DATA",
    "CATEGORY_DOCUMENT",
    "CATEGORY_FINANCIAL",
    "CATEGORY_OPERATIONAL",
    "STATUSES",
    "STATUS_ATTENTION",
    "STATUS_CRITICAL",
    "STATUS_INFO",
    "STATUS_REVIEW",
    "STATUS_WAITING",
    "build_review_queue_items",
    "filter_review_queue_items",
    "summarize_review_queue",
]
