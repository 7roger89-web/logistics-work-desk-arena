"""LOGI-GOOD EXACT — shared UI core for the Logi-good styled shell.

This module owns:

- the Logi-good design tokens / CSS skin applied on top of Streamlit DOM;
- tiny HTML helpers used by shell + pages (badges, section titles, rows…);
- formatting helpers that never convert UNKNOWN into 0;
- navigation registry (page key -> (label, icon, permission, render callable)).

Business logic stays in core.* / existing views; this file only presents it.
"""
from __future__ import annotations

import html as _html
import re
from typing import Any, Callable, Mapping

# --------------------------------------------------------------------------
# Design tokens (mirror design_reference/logi-good/src/index.css)
# --------------------------------------------------------------------------
NAVY_950 = "#0a1f3a"
NAVY_900 = "#0f2a4a"
NAVY_800 = "#14365e"
NAVY_700 = "#1a4d8f"
NAVY_600 = "#1e5aa8"
NAVY_100 = "#dbe7f5"
NAVY_50 = "#eef4fb"
PAGE_BG = "#eef1f6"
INK = "#1a2433"
MUTED = "#5b6b82"

# --------------------------------------------------------------------------
# Small text helpers
# --------------------------------------------------------------------------
UNKNOWN_LABEL = "Chưa có"


def esc(value: Any) -> str:
    """HTML-escape a value for safe injection into custom HTML blocks."""
    if value is None:
        return ""
    return _html.escape(str(value), quote=True)


def text(value: Any, default: str = UNKNOWN_LABEL) -> str:
    """Display text for a business value.  Never coerces to zero/empty."""
    if value is None:
        return default
    s = str(value).strip()
    if not s or s.upper() in {"UNKNOWN", "NONE", "NAN"}:
        return default
    return s


def money_number(value: Any) -> float | None:
    """Return float amount or None when blank/invalid (UNKNOWN != ZERO)."""
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip().replace(",", "").replace(" ", "")
    if not s or s.upper() in {"UNKNOWN", "NONE", "NAN", "-"}:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def fmt_vnd(value: Any, blank: str = "—") -> str:
    amount = money_number(value)
    if amount is None:
        return blank
    return f"{amount:,.0f} ₫".replace(",", ".")


def fmt_money(value: Any, ccy: str = "VND") -> str:
    amount = money_number(value)
    if amount is None:
        return "—"
    ccy_upper = str(ccy or "VND").upper()
    if ccy_upper == "VND":
        return f"{amount:,.0f} ₫".replace(",", ".")
    symbols = {"USD": "$", "CNY": "¥", "EUR": "€"}
    sym = symbols.get(ccy_upper, ccy_upper + " ")
    return f"{sym}{amount:,.2f}".replace(",", ".") if ccy_upper != "CNY" else f"{sym}{amount:,.2f}".replace(",", ".")


def short_money(value: Any, ccy: str = "VND") -> str:
    """Compact 'tr' style money for KPI cards; VND only."""
    amount = money_number(value)
    if amount is None:
        return "—"
    amount = amount / 1e6
    if abs(amount) >= 100:
        return f"{amount:,.0f} tr".replace(",", ".")
    return f"{amount:,.1f} tr".replace(",", ".")


def date_label(value: Any) -> str:
    """Format stored date values to dd/mm/yyyy when parseable, else blank-ish."""
    if value in (None, ""):
        return UNKNOWN_LABEL
    s = str(value).strip()
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        return f"{m.group(3)}/{m.group(2)}/{m.group(1)}"
    m = re.search(r"(\d{2})/(\d{2})/(\d{4})", s)
    if m:
        return f"{m.group(1)}/{m.group(2)}/{m.group(3)}"
    return s[:10]


def tone_for_status(status: Any) -> str:
    """Logi-good tone from raw shipment status."""
    s = str(status or "").strip().casefold()
    if s in {"done", "hoàn thành", "đã giao", "delivered"}:
        return "green"
    if s in {"cancel", "cancelled", "đã hủy", "hủy"}:
        return "gray"
    if s in {"pending", "đang thông quan/giao hàng", "delivering", "clearing"}:
        return "amber"
    return "blue"


# --------------------------------------------------------------------------
# HTML component helpers
# --------------------------------------------------------------------------
def badge(tone: str, label: Any, size: str = "md") -> str:
    tones = {
        "green": "background:#ecfdf5;color:#065f46;border-color:#a7f3d0;",
        "amber": "background:#fffbeb;color:#92400e;border-color:#fde68a;",
        "red": "background:#fef2f2;color:#991b1b;border-color:#fecaca;",
        "blue": "background:#eff6ff;color:#1e40af;border-color:#bfdbfe;",
        "gray": "background:#f1f5f9;color:#475569;border-color:#e2e8f0;",
        "violet": "background:#f5f3ff;color:#5b21b6;border-color:#ddd6fe;",
    }
    pad = "padding:2px 10px;font-size:12.5px;" if size == "sm" else "padding:4px 12px;font-size:13px;"
    return (
        f"<span style='display:inline-flex;align-items:center;gap:5px;border:1px solid;"
        f"border-radius:999px;font-weight:700;line-height:1.35;white-space:nowrap;{pad}{tones.get(tone, tones['gray'])}'>"
        f"{esc(label)}</span>"
    )


def pill(active: bool, label: Any) -> str:
    if active:
        return (
            f"<span style='display:inline-flex;align-items:center;border-radius:999px;padding:6px 16px;"
            f"font-size:13.5px;font-weight:700;color:#fff;background:{NAVY_900};border:2px solid {NAVY_900};"
            f"white-space:nowrap;'>{esc(label)}</span>"
        )
    return (
        f"<span style='display:inline-flex;align-items:center;border-radius:999px;padding:6px 16px;"
        f"font-size:13.5px;font-weight:700;color:#475569;background:#fff;border:2px solid #e2e8f0;"
        f"white-space:nowrap;'>{esc(label)}</span>"
    )


def section_title(icon: str, title: Any, sub: Any = None, right: str = "") -> str:
    sub_html = f"<p style='margin:2px 0 0;font-size:13.5px;color:{MUTED};'>{esc(sub)}</p>" if sub else ""
    right_html = f"<div style='display:flex;align-items:center;gap:8px;'>{right}</div>" if right else ""
    icon_html = (
        f"<span style='display:grid;place-items:center;width:36px;height:36px;border-radius:12px;"
        f"background:{NAVY_900};color:#fff;font-size:17px;flex:0 0 auto;'>{esc(icon)}</span>"
    )
    return (
        f"<div style='display:flex;align-items:flex-start;justify-content:space-between;gap:12px;margin-bottom:12px;'>"
        f"<div style='display:flex;gap:10px;align-items:flex-start;min-width:0;'>"
        f"{icon_html if icon else ''}"
        f"<div style='min-width:0;'><div style='font-size:17px;line-height:1.25;font-weight:800;color:{NAVY_900};'>"
        f"{esc(title)}</div>{sub_html}</div></div>{right_html}</div>"
    )


def state_row(label: Any, value: Any, *, big: bool = False, mono: bool = False) -> str:
    value_html = (
        f"<span style='text-align:right;font-weight:700;color:#1e293b;font-size:{'16px' if big else '14px'};"
        f"{'font-variant-numeric:tabular-nums;' if mono else ''}'>{value}</span>"
    )
    return (
        f"<div style='display:flex;align-items:flex-start;justify-content:space-between;gap:10px;"
        f"padding:7px 0;border-bottom:1px solid #f1f5f9;'><span style='font-size:13px;color:{MUTED};"
        f"font-weight:500;padding-top:2px;'>{esc(label)}</span>{value_html}</div>"
    )


def kv_mini(label: Any, value: Any) -> str:
    return (
        f"<div style='background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;padding:10px 12px;'>"
        f"<p style='margin:0;font-size:11px;font-weight:800;letter-spacing:.05em;text-transform:uppercase;"
        f"color:#94a3b8;'>{esc(label)}</p>"
        f"<p style='margin:2px 0 0;font-weight:800;font-size:14.5px;color:{NAVY_900};word-break:break-word;'>{value}</p></div>"
    )


def missing_box(what: str, where: str = "") -> str:
    """Logi-good amber dashed 'thiếu …' box (static HTML part)."""
    where_html = (
        f"<p style='margin:2px 0 0;font-size:13px;color:#92400e;'>{esc(where)}</p>" if where else ""
    )
    return (
        f"<div style='border:2px dashed #fbbf24;background:#fffbeb;border-radius:14px;padding:12px 14px;"
        f"display:flex;align-items:center;gap:10px;margin-bottom:10px;'>"
        f"<span style='font-size:18px;'>⚠️</span>"
        f"<div style='min-width:0;'><p style='margin:0;font-weight:800;font-size:14.5px;color:#78350f;'>Thiếu {esc(what)}</p>"
        f"{where_html}</div></div>"
    )


def stat_cell(label: Any, value: Any, sub: Any = None, *, tone: str = "") -> str:
    tone_color = {"red": "#b91c1c", "green": "#047857", "amber": "#b45309", "navy": NAVY_900}.get(tone, NAVY_900)
    sub_html = f"<p style='margin:2px 0 0;font-size:12.5px;color:{MUTED};'>{esc(sub)}</p>" if sub else ""
    return (
        f"<div style='background:#fff;border:1px solid #e2e8f0;border-radius:16px;padding:14px 16px;"
        f"box-shadow:0 1px 2px rgba(15,42,74,.05);'>"
        f"<p style='margin:0;font-size:12.5px;font-weight:600;color:#64748b;'>{esc(label)}</p>"
        f"<p style='margin:4px 0 0;font-size:26px;line-height:1.1;font-weight:800;color:{tone_color};'>{value}</p>"
        f"{sub_html}</div>"
    )


def card_open(style: str = "", *, pad: bool = True) -> str:
    extra = f" style='{style}'" if style else ""
    padding = "padding:18px;" if pad else ""
    return f"<div class='lg-card'{extra}><div style='{padding}'>"


def card_close() -> str:
    return "</div></div>"


def page_max_width(width: str = "1300px") -> str:
    return f"<div style='max-width:{width};margin:0 auto;'>"


# --------------------------------------------------------------------------
# Real shipment data helpers (aliases mirror core.shipment_dashboard)
# --------------------------------------------------------------------------
def _data(shipment: Mapping[str, Any]) -> Mapping[str, Any]:
    d = shipment.get("data")
    return d if isinstance(d, Mapping) else {}


def _sections(shipment: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    data = _data(shipment)
    sections: list[Mapping[str, Any]] = [shipment, data]
    for key in ("0.0", "1.2", "2.4", "2.6", "2.7", "3.4"):
        section = data.get(key)
        if isinstance(section, Mapping):
            sections.append(section)
    return sections


def first_value(shipment: Mapping[str, Any], aliases: tuple[str, ...]) -> Any:
    for section in _sections(shipment):
        for alias in aliases:
            value = section.get(alias)
            if value not in (None, ""):
                return value
    return None


def customer_name(shipment: Mapping[str, Any]) -> str:
    return text(
        shipment.get("customer")
        or shipment.get("customer_name")
        or shipment.get("client")
        or first_value(shipment, ("customer", "customer_name", "client_name")),
        "Chưa có khách hàng",
    )


def shipment_id(shipment: Mapping[str, Any]) -> str:
    return str(
        shipment.get("shipment_id")
        or shipment.get("id")
        or first_value(shipment, ("shipment_code", "code"))
        or ""
    )


def route_label(shipment: Mapping[str, Any]) -> str:
    """Tuyến: data.1.2.route/origin→destination else pol/pod else —."""
    r = _data(shipment).get("1.2")
    r = r if isinstance(r, Mapping) else {}
    route = text(r.get("route"), "")
    if route:
        return route
    origin = text(r.get("origin"), "")
    destination = text(r.get("destination"), "")
    if origin or destination:
        return f"{origin} → {destination}".replace(" → ", " → ") if origin and destination else origin or destination
    pol = text(r.get("pol"), "")
    pod = text(r.get("pod"), "")
    if pol or pod:
        return f"{pol} → {pod}" if pol and pod else pol or pod
    return UNKNOWN_LABEL


def contract_ids(shipment: Mapping[str, Any]) -> list[str]:
    ids: list[str] = []
    for value in (
        shipment.get("contract_id"),
        shipment.get("contract_no"),
        (_data(shipment).get("entrustment") or {}).get("contract_no")
        if isinstance(_data(shipment).get("entrustment"), Mapping)
        else None,
    ):
        if value:
            cleaned = str(value).strip().upper()
            if cleaned and cleaned not in ids:
                ids.append(cleaned)
    return ids


def owner_label(shipment: Mapping[str, Any]) -> str:
    return text(
        first_value(
            shipment,
            ("internal_sale_owner", "sale_owner", "sales_owner", "owner", "assigned_to", "assignee", "sale"),
        ),
        "Chưa phân công",
    )


def support_label(shipment: Mapping[str, Any]) -> str:
    return text(
        first_value(shipment, ("support_owner", "support", "ops_owner", "customer_support")),
        "Chưa phân công",
    )


def mst_of_customer(customer_doc: Mapping[str, Any] | None) -> str:
    if not customer_doc:
        return UNKNOWN_LABEL
    return text(customer_doc.get("tax_code") or customer_doc.get("mst") or customer_doc.get("tax"), UNKNOWN_LABEL)


def collection_first(shipment: Mapping[str, Any], aliases: tuple[str, ...]) -> list[Mapping[str, Any]]:
    """Return the first collection found among aliases as a list of mappings."""
    for section in _sections(shipment):
        for alias in aliases:
            value = section.get(alias)
            if isinstance(value, Mapping):
                if any(key in value for key in ("id", "name", "label", "type", "factory_name")):
                    return [value]
                return [item for item in value.values() if isinstance(item, Mapping)]
            if isinstance(value, (list, tuple)):
                return [item for item in value if isinstance(item, Mapping)]
    return []


def factory_lots(shipment: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    lots = collection_first(shipment, ("factory_lots", "factories", "factory_items"))
    if lots:
        return lots
    pickup = first_value(shipment, ("pickup", "pickup_info"))
    if isinstance(pickup, Mapping):
        return [pickup]
    return []


def audit_actors(audit_rows: list[Mapping[str, Any]]) -> Mapping[str, Any]:
    """Return most frequent actor display for header (latest wins)."""
    if not audit_rows:
        return {}
    return dict(audit_rows[0])


def today_vn() -> str:
    from datetime import date

    weekday_names = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]
    now = date.today()
    return f"{weekday_names[now.weekday()]} · {now.strftime('%d/%m/%Y')}"


def link_url(page: str, **params: Any) -> str:
    """Build relative anchor href (e.g. '?lg=shipment&sid=LO-1&tab=1')."""
    parts = [f"lg={page}"]
    for key, value in params.items():
        if value in (None, ""):
            continue
        parts.append(f"{key}={_html.escape(str(value), quote=True)}")
    return "?" + "&".join(parts)


_LABEL_KEY: dict[str, str] = {
    "Tổng Quan Công Việc": "home",
    "Việc Cần Xử Lý": "tasks",
    "Lô Hàng": "shipments",
    "Tạo Lô Mới": "new",
    "Khách Hàng": "customers",
    "Ngữ Cảnh Đối Tác": "partner",
    "Kinh Doanh & Báo Giá": "quotes",
    "Kinh doanh & Báo giá": "quotes",
    "Thỏa Thuận & Bàn Giao": "agreements",
    "Hợp Đồng": "contracts",
    "Thu Tiền & Công Nợ": "finance",
    "Đối Soát Tài Chính": "reconcile",
    "Công Nợ A Bò": "partnerdebt",
    "Báo Cáo CEO": "reports",
    "Tra Cứu Thuế": "tariff",
    "Theo Dõi Vận Chuyển": "tracking",
    "Sổ Tay Kinh Nghiệm": "handbook",
    "Dịch Thuật DeepL": "translate",
    "Dịch Thuật": "translate",
    "Người Dùng": "users",
}


def nav_to_page(label: Any) -> None:
    """Navigate between screens from inside real modules (legacy label API).

    Sets the legacy ``st.session_state.active_page``; for non-home screens the
    matching ``lg`` query parameter is written so the shell router lands on the
    right page and stale deep-link params (sid/tab/ov) are dropped.

    ``"Tổng Quan Công Việc"`` is intentionally left session-driven: modules use
    it together with an active shipment id to open the shipment workspace
    (resolver hijack) or with no id to reach the dashboard — writing ``lg=home``
    here would defeat that.
    """
    import streamlit as st  # noqa: PLC0415

    label_text = str(label or "Tổng Quan Công Việc").strip()
    st.session_state.active_page = label_text
    key = _LABEL_KEY.get(label_text, "")
    if not key or key == "home":
        return
    st.query_params["lg"] = key
    for name in ("sid", "tab", "ov"):
        if name in st.query_params:
            del st.query_params[name]


def a(text_content: str, page: str, *, cls: str = "", **params: Any) -> str:
    klass = f" class='{cls}'" if cls else ""
    return f"<a href='{link_url(page, **params)}'{klass}>{text_content}</a>"
