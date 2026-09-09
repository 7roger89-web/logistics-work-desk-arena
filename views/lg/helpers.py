"""Session / role / formatting helpers for the Logi-good donor view layer."""
from __future__ import annotations

from datetime import date, datetime
from typing import Any

from core.auth import current_user, has_permission
from core.utils import parse_date_optional

UNKNOWN = "UNKNOWN"

# Route slug -> required permission ("" => any authenticated operator).
# RBAC stays authoritative: permission checks reuse core.auth.has_permission.
ROUTE_PERMISSION: dict[str, str] = {
    "home": "dashboard_view",
    "tasks": "dashboard_view",
    "shipments": "shipment_read",
    "shipment_detail": "shipment_read",
    "new_shipment": "shipment_create",
    "tracking": "shipment_read",
    "customers": "customer_view",
    "context": "entity_context_view",
    "quote": "quote_view",
    "agreement": "agreement_view",
    "contracts": "contract_view",
    "contract_detail": "contract_view",
    "new_contract": "contract_write",
    "receive": "finance_view",
    "reconcile": "finance_view",
    "partner_debt": "finance_view",
    "ceo": "finance_view",
    "tariff": "tariff_view",
    "notebook": "knowledge_view",
    "translate": "translation_view",
    "admin": "user_admin",
}


def set_page(slug: str) -> None:
    st_session = _st()
    st_session["lg_page"] = slug
    # Preserve deep links (shipment detail) but clear stale detail when a top-level nav runs.
    if slug != "shipment_detail":
        st_session.pop("lg_shipment", None)
        st_session.pop("lg_tab", None)


def _st():
    import streamlit as st

    return st.session_state


def can_access(slug: str) -> bool:
    permission = ROUTE_PERMISSION.get(slug, "")
    return True if not permission else has_permission(permission)


def guard(slug: str) -> bool:
    """Return True if the user may access the given route; else render denial."""
    import streamlit as st

    if can_access(slug):
        return True
    st.markdown("### 🔒 Không có quyền truy cập")
    st.caption("Tài khoản hiện tại không có quyền với màn hình này.")
    return False


def actor() -> dict[str, str]:
    user = current_user()
    return {
        "username": str(user.get("username") or ""),
        "display_name": str(user.get("display_name") or user.get("username") or ""),
        "role": str(user.get("role") or "").lower(),
    }


def fmt_date(value: Any) -> str:
    parsed = parse_date_optional(value)
    return parsed.strftime("%d/%m/%Y") if parsed else UNKNOWN


def fmt_date_blank(value: Any) -> str:
    parsed = parse_date_optional(value)
    return parsed.strftime("%d/%m/%Y") if parsed else ""


def to_text(value: Any, default: str = UNKNOWN) -> str:
    if value is None:
        return default
    if isinstance(value, str):
        return value.strip() or default
    return str(value)


def money(value: Any, currency: str = "VND") -> str:
    """Format a numeric amount; unknown stays unknown and never becomes 0."""
    if value is None:
        return UNKNOWN
    try:
        num = float(value)
    except (TypeError, ValueError):
        return UNKNOWN
    if currency == "VND":
        return f"{num:,.0f} ₫"
    return f"{num:,.0f} {currency}"


def tone_for_status(status: str) -> str:
    s = (status or "").strip().lower()
    if s in ("done", "hoàn thành", "đã giao", "đã xong", "ok", "đã thu đủ"):
        return "green"
    if s in ("wait", "chờ chứng từ", "chưa xử lý", "pending pickup", "chờ lấy hàng"):
        return "amber"
    if s in ("cancel", "đã hủy", "blocked", "overdue", "quá hạn"):
        return "red"
    if s in ("pending", "đang thông quan/giao hàng", "đang xử lý", "đang giao"):
        return "blue"
    return "gray"
