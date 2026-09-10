"""Presentation adapter: real Logistics readers → the frozen Logi-good shape.

Phase B replaces the Phase A sandbox seed projection with a read-only
projection over the CURRENT Logistics readers. There is no duplicate business
truth here: every value comes from ``core.database`` / ``core.logic`` /
``core.shipment_dashboard`` / ``core.docgen`` and is reshaped for display only.

UNKNOWN != ZERO
---------------
A numeric value the real model does not carry is projected as ``None`` and is
rendered as an explicit "—" by the UI. It is never coerced to ``0``, because
for tax, VAT, pack count, weight, CBM, cost, Finance Actual, AR/AP and payments
a blank is a statement about knowledge, not about money.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Mapping

UNKNOWN = None
UNKNOWN_LABEL = "—"


# --------------------------------------------------------------------------
# UNKNOWN-safe primitives
# --------------------------------------------------------------------------

def text(value: Any) -> str:
    """Text field: real value or blank. Never a fabricated placeholder."""
    if value is None:
        return ""
    return str(value).strip()


def num(value: Any) -> float | None:
    """Numeric field: real value or None (UNKNOWN). Never 0 for a blank."""
    if value is None or isinstance(value, bool):
        return None if value is None else float(value)
    if isinstance(value, (int, float)):
        return float(value)
    raw = str(value).strip()
    if not raw:
        return None
    try:
        return float(raw.replace(",", "").replace(".", "", raw.count(".") > 1))
    except ValueError:
        return None


def label(value: Any) -> str:
    """Display label: UNKNOWN renders as an explicit em dash."""
    if value is None:
        return UNKNOWN_LABEL
    raw = str(value).strip()
    return raw or UNKNOWN_LABEL


def money(value: Any) -> float | None:
    return num(value)


def _ddmmyyyy(value: Any) -> str:
    """Normalise an ISO/other date string to DD/MM/YYYY, blank when unknown."""
    raw = text(value)
    if not raw:
        return ""
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y"):
        try:
            return datetime.strptime(raw[:19] if len(raw) > 10 and "-" in raw else raw, fmt).strftime("%d/%m/%Y")
        except ValueError:
            continue
    return raw


def _money_label(value: Any) -> str:
    amount = num(value)
    if amount is None:
        return UNKNOWN_LABEL
    return f"{amount:,.0f}".replace(",", ".")


# --------------------------------------------------------------------------
# Canonical fact access
# --------------------------------------------------------------------------

def _section(shipment: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    data = shipment.get("data")
    if not isinstance(data, Mapping):
        return {}
    value = data.get(key)
    return value if isinstance(value, Mapping) else {}


def operational_stage(shipment: Mapping[str, Any]) -> tuple[str, str]:
    """Derive the operational stage from real shipment facts only.

    Returns ``(label, tone)`` for the donor status badge. No fabricated KPI.
    """
    delivery = _section(shipment, "2.7")
    customs = _section(shipment, "2.4")
    transport = _section(shipment, "1.2")
    arrival = _section(shipment, "2.6")
    status = text(shipment.get("status") or _section(shipment, "0.0").get("st"))

    if delivery.get("is_delivered"):
        return "Đã giao", "green"
    if status == "cancel":
        return "Đã hủy", "gray"
    if customs.get("customs_status"):
        return "Chờ giao", "blue"
    # A registered declaration, or goods already arrived at the border, both
    # mean the shipment is waiting on customs — derived from real facts only.
    if text(customs.get("tk_no")) or _arrived(arrival.get("arrival_date")):
        return "Chờ thông quan", "amber"
    # An ETD still in the future means the shipment has not departed yet.
    if text(transport.get("etd")) and _arrived(transport.get("etd")):
        return "Đang vận chuyển", "blue"
    return "Chờ lấy hàng", "gray"


def _arrived(value: Any) -> bool:
    """True when a real ETA/arrival date has already passed (goods at border)."""
    from core.utils import parse_date_optional

    parsed = parse_date_optional(value)
    return bool(parsed and parsed <= date.today())


def document_checklist(shipment: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Document completeness derived from real shipment facts (no invention)."""
    customs = _section(shipment, "2.4")
    delivery = _section(shipment, "2.7")
    tk = text(customs.get("tk_no"))
    rows = [
        {"name": "Số tờ khai nhập khẩu", "ok": bool(tk),
         "note": tk or "Chưa đăng ký tờ khai"},
        {"name": "Đã thông quan", "ok": bool(customs.get("customs_status")),
         "note": text(customs.get("phan_luong")) or ("Chờ kết quả phân luồng" if tk else "Chờ số tờ khai")},
        {"name": "Xe giao VN + tài xế", "ok": bool(text(delivery.get("truck_no"))),
         "note": text(delivery.get("truck_no")) or "Chưa đặt xe giao"},
        {"name": "Xác nhận đã giao hàng", "ok": bool(delivery.get("is_delivered")),
         "note": _ddmmyyyy(delivery.get("delivered_at")) or "Chưa xác nhận"},
    ]
    return rows


def missing_docs(shipment: Mapping[str, Any]) -> list[str]:
    return [row["name"] for row in document_checklist(shipment) if not row["ok"]]


# --------------------------------------------------------------------------
# Finance projection — QUOTE ESTIMATE stays separate from FINANCE ACTUAL
# --------------------------------------------------------------------------

def _quote_lines(shipment: Mapping[str, Any], quotes: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Quote estimate lines from the linked accepted quote (separate object)."""
    customer_id = text(shipment.get("customer_id"))
    contract_id = text(shipment.get("contract_id"))
    for quote in quotes.values():
        if not isinstance(quote, Mapping):
            continue
        if contract_id and text(quote.get("id")) == contract_id:
            pass
        elif text(quote.get("customer_id")) != customer_id:
            continue
        lines = quote.get("lines")
        if not isinstance(lines, list):
            continue
        return [
            {
                "label": text(line.get("name")) or "Dòng báo giá",
                "amount": num(line.get("amount")),
                "ccy": text(line.get("currency")) or "VND",
                "kind": "quote",
            }
            for line in lines
            if isinstance(line, Mapping)
        ]
    return []


def finance_projection(shipment: Mapping[str, Any], quotes: Mapping[str, Any]) -> dict[str, Any]:
    """Finance Actual from the canonical snapshot; AR/AP from core.logic.

    ``quote`` (estimate) and ``actual`` (booked service lines) are sourced from
    different objects and are never merged or interchanged.
    """
    from core.logic import calculate_from_shipment

    finance = _section(shipment, "3.4")
    details = finance.get("details") if isinstance(finance.get("details"), list) else []
    summary = calculate_from_shipment(shipment)
    currency = text(shipment.get("currency") or finance.get("currency") or "VND")

    actual = [
        {
            "label": text(line.get("display_name") or line.get("name_full") or line.get("name")) or "Dịch vụ",
            "amount": num(line.get("price", line.get("price_out"))),
            "cost": num(line.get("cost", line.get("price_in"))),
            "qty": num(line.get("qty")),
            "vat": num(line.get("vat_line", line.get("vat"))),
            "ccy": currency,
            "kind": "actual",
        }
        for line in details
        if isinstance(line, Mapping)
    ]

    payments_raw = finance.get("payments") if isinstance(finance.get("payments"), list) else []
    payments = [
        {
            "id": text(p.get("id")),
            "requestId": text(p.get("request_id")),
            "date": _ddmmyyyy(p.get("date")),
            "kind": text(p.get("note")) or "Khoản thu",
            "amount": num(p.get("amount")),
            "ccy": currency,
            "by": text(p.get("created_by") or p.get("created_by_username")),
            "note": text(p.get("note")),
            "reversed": bool(p.get("is_reversed")) or text(p.get("status")).lower() in {"reversed", "cancelled", "void"},
        }
        for p in payments_raw
        if isinstance(p, Mapping)
    ]

    return {
        "quote": _quote_lines(shipment, quotes),
        "actual": actual,
        "currency": currency,
        # AR — canonical snapshot from core.logic (receivable = net + output VAT).
        "receivable": num(summary.get("receivable")),
        "received": num(summary.get("paid")),
        "receivableNet": num(summary.get("revenue_net")),
        "outputVat": num(summary.get("output_vat")),
        "outstanding": num(summary.get("debt")),
        # AP — cost side of the same service lines.
        "payable": num(summary.get("cost")),
        # The shipment document does not carry a supplier-payment ledger, so
        # "already paid to partners" is UNKNOWN, not zero.
        "paid": UNKNOWN,
        "commission": num((finance.get("commission") or {}).get("total") if isinstance(finance.get("commission"), Mapping) else finance.get("commission")),
        "profit": num(summary.get("profit")),
        "payments": payments,
        "source": "core.logic.calculate_from_shipment over data.3.4",
    }


# --------------------------------------------------------------------------
# History — real audit only
# --------------------------------------------------------------------------

def timeline_projection(shipment_id: str, limit: int = 30) -> list[dict[str, Any]]:
    from core.database import load_audit_logs

    rows = load_audit_logs("shipment", shipment_id, limit=limit) or []
    out: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        created = row.get("created_at")
        stamp = created.strftime("%d/%m %H:%M") if isinstance(created, datetime) else _ddmmyyyy(created)
        action = text(row.get("action"))
        out.append({
            "time": stamp,
            "title": action or "Cập nhật",
            "desc": text(row.get("actor")) or text(row.get("actor_username")),
            "tone": "green" if action in {"create", "direct_payment_created", "delivered"} else "blue",
        })
    return out


# --------------------------------------------------------------------------
# Shipment projection
# --------------------------------------------------------------------------

def shipment_projection(
    shipment: Mapping[str, Any],
    *,
    customers: Mapping[str, Any] | None = None,
    contracts: Mapping[str, Any] | None = None,
    quotes: Mapping[str, Any] | None = None,
    dashboard: Mapping[str, Any] | None = None,
    history: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Project one canonical shipment document into the frozen UI shape."""
    customers = customers or {}
    contracts = contracts or {}
    quotes = quotes or {}

    sid = text(shipment.get("id") or shipment.get("shipment_id"))
    transport = _section(shipment, "1.2")
    customs = _section(shipment, "2.4")
    arrival = _section(shipment, "2.6")
    delivery = _section(shipment, "2.7")
    head = _section(shipment, "0.0")

    customer_id = text(shipment.get("customer_id"))
    customer_doc = customers.get(customer_id) if isinstance(customers.get(customer_id), Mapping) else {}
    customer_name = text(shipment.get("customer") or shipment.get("client") or customer_doc.get("name"))

    contract_id = text(shipment.get("contract_id") or _section(shipment, "entrustment").get("contract_no"))
    status_label, status_tone = operational_stage(shipment)

    view = dashboard or {}
    next_action = view.get("next_action") if isinstance(view.get("next_action"), Mapping) else {}
    top_alert = view.get("top_alert") if isinstance(view.get("top_alert"), Mapping) else {}

    next_text = text(next_action.get("label") or top_alert.get("label"))
    if not next_text:
        next_text = "Lô hàng ổn định — không có cảnh báo"
    next_detail = text(next_action.get("detail") or top_alert.get("detail"))

    missing = missing_docs(shipment)
    severity = text(top_alert.get("severity"))
    priority = "Khan" if severity == "critical" else ("CanXuLy" if severity in {"warning", "info"} else "BinhThuong")

    tab = "nhap" if status_label in {"Chờ thông quan", "Chờ giao"} else ("lay-hang" if status_label == "Chờ lấy hàng" else "lay-hang")

    qty_pkg = text(transport.get("qty_pkg"))

    return {
        "id": sid,
        "customer": customer_name,
        "customerMST": text(customer_doc.get("tax_code")),
        "customerId": customer_id,
        "contract": contract_id,
        "route": " → ".join(part for part in (text(transport.get("pol")), text(transport.get("pod"))) if part) or UNKNOWN_LABEL,
        "borderVN": text(transport.get("pod")) or UNKNOWN_LABEL,
        "sale": "",
        "support": text(shipment.get("updated_by")),
        "status": status_label,
        "statusTone": status_tone,
        "priority": priority,
        "nextAction": next_text,
        "nextActionDetail": next_detail,
        "nextLabel": "XỬ LÝ NGAY" if priority in {"Khan", "CanXuLy"} else "XEM LÔ",
        "nextRoute": f"/lo-hang/{sid}?tab={tab}",
        "updated": _ddmmyyyy(shipment.get("updated_at")) if not isinstance(shipment.get("updated_at"), datetime)
        else shipment["updated_at"].strftime("%d/%m/%Y %H:%M"),
        "missingDocs": missing,
        "docs": document_checklist(shipment),
        "version": int(shipment.get("version") or 0),
        "rawStatus": text(shipment.get("status") or head.get("st")),
        "mode": text(head.get("mode")),
        "incoterm": text(head.get("incoterm")),
        "createdAt": _ddmmyyyy(head.get("created_at")),
        # --- TAB 1: pickup & export (real fields only; unsupported = blank) ---
        "pickup": {
            "factory": text(shipment.get("factory_name")),
            "address": text(transport.get("pol")),
            "contact": text(shipment.get("factory_contact")),
            "phone": text(shipment.get("factory_phone")),
            "pickupTime": _ddmmyyyy(transport.get("etd")),
            "truckType": "",
            "plate": text(transport.get("container_no")),
            "driver": "",
            "driverPhone": "",
            "eta": _ddmmyyyy(arrival.get("arrival_date")),
            "ata": "",
        },
        "transport": {
            "bookingNo": text(transport.get("booking_no")),
            "carrier": text(transport.get("carrier")),
            "mbl": text(transport.get("mbl")),
            "hbl": text(transport.get("hbl")),
            "vessel": text(transport.get("vessel")),
            "etd": _ddmmyyyy(transport.get("etd")),
            "pol": text(transport.get("pol")),
            "pod": text(transport.get("pod")),
            "containerNo": text(transport.get("container_no")),
            "qtyPkg": qty_pkg,
        },
        # The canonical model stores pack count/weight as one free-text field;
        # separate numeric pack/CBM/weight are therefore UNKNOWN, not zero.
        "cargo": {
            "packs": UNKNOWN,
            "weight": UNKNOWN,
            "cbm": UNKNOWN,
            "dims": "",
            "type": "",
            "note": qty_pkg,
            "qtyPkg": qty_pkg,
        },
        "exportInfo": {
            "border": text(transport.get("pol")),
            "declarant": text(shipment.get("china_agent")),
            "eta": _ddmmyyyy(transport.get("etd")),
            "ata": "",
            "state": text(transport.get("carrier")),
            "chinaDeclNo": text(shipment.get("china_export_decl_no")),
        },
        # --- TAB 2: import & delivery ---
        "importInfo": {
            "borderVN": text(transport.get("pod")),
            "declarationNo": text(customs.get("tk_no")),
            "regDate": _ddmmyyyy(customs.get("reg_date")),
            "clearDate": _ddmmyyyy(customs.get("clearance_date")),
            # Import tax / VAT are not modelled on the shipment document, so
            # they stay UNKNOWN until a real source exists.
            "tax": UNKNOWN,
            "vat": UNKNOWN,
            "inspection": text(customs.get("phan_luong")),
            "customsStatus": bool(customs.get("customs_status")),
            "license": "",
            "gnt": {
                "payer": text((customs.get("gnt") or {}).get("nguoi_nop")),
                "taxCode": text((customs.get("gnt") or {}).get("mst")),
                "address": text((customs.get("gnt") or {}).get("dia_chi")),
                "customsOffice": text((customs.get("gnt") or {}).get("ma_hq")),
            },
            "arrivalDate": _ddmmyyyy(arrival.get("arrival_date")),
            "freeTime": num(arrival.get("free_time")),
            "truckVN": "",
            "plateVN": text(delivery.get("truck_no")),
            "driverVN": text(delivery.get("seal_no")),
            "schedule": _ddmmyyyy(delivery.get("delivery_date")),
            "deliveryAddr": text(delivery.get("addr")),
            "receiver": text(delivery.get("receiver_name")),
            "receiverPhone": text(delivery.get("phone_receiver")),
            "receiverTitle": text(delivery.get("receiver_title")),
            "deliveryLocation": text(delivery.get("delivery_location")),
            "delivered": bool(delivery.get("is_delivered")),
            "actualDelivery": _ddmmyyyy(delivery.get("delivered_at") or delivery.get("delivery_date"))
            if delivery.get("is_delivered") else "",
        },
        # --- TAB 3 ---
        "finance": finance_projection(shipment, quotes),
        # --- TAB 4 ---
        "pxk": pxk_projection(shipment, contracts),
        # --- TAB 5 ---
        "timeline": list(history or []),
        # Dashboard/readiness evidence (canonical projection, read-only).
        "ops": {
            "financialFlag": text(view.get("financial_flag")),
            "financialLabel": text(view.get("financial_label")),
            "alerts": [
                {"code": text(a.get("code")), "severity": text(a.get("severity")),
                 "title": text(a.get("label")), "message": text(a.get("detail"))}
                for a in (view.get("alerts") or []) if isinstance(a, Mapping)
            ],
            "arrivalDateLabel": text(view.get("arrival_date_label")),
            "freeTimeExpiryLabel": text(view.get("free_time_expiry_label")),
            "daysRemaining": view.get("days_remaining"),
        },
        # --- Tracking: only real transport/state facts, no fabricated GPS ---
        "tracking": tracking_projection(shipment),
    }


def pxk_projection(shipment: Mapping[str, Any], contracts: Mapping[str, Any]) -> dict[str, Any]:
    """PXK facts + the real delivery gate, from core.docgen rules."""
    from core.docgen import rules as docgen_rules

    delivery = _section(shipment, "2.7")
    delivered = bool(delivery.get("is_delivered"))
    missing_delivery = docgen_rules.delivery_facts_missing(delivery) if delivered else []
    contract_id = text(shipment.get("contract_id") or _section(shipment, "entrustment").get("contract_no"))
    contract = contracts.get(contract_id) if isinstance(contracts.get(contract_id), Mapping) else {}

    return {
        "source": contract_id,
        "sourceName": text(contract.get("contract_no") or contract.get("hdmb_no") or contract.get("hdnt_no")),
        "delivered": delivered,
        "gateOpen": delivered and not missing_delivery,
        "missingDeliveryFacts": list(missing_delivery),
        "number": "",
        "date": "",
        "place": text(delivery.get("delivery_location") or delivery.get("addr")),
        "receiver": text(delivery.get("receiver_name")),
        "role": text(delivery.get("receiver_title")),
        "done": False,
    }


def tracking_projection(shipment: Mapping[str, Any]) -> dict[str, Any]:
    """Tracking from real transport/state facts. No invented GPS position."""
    from core.config import CARRIER_LINKS

    transport = _section(shipment, "1.2")
    customs = _section(shipment, "2.4")
    delivery = _section(shipment, "2.7")
    arrival = _section(shipment, "2.6")
    status_label, tone = operational_stage(shipment)

    carrier = text(transport.get("carrier"))
    reference = text(transport.get("booking_no") or transport.get("mbl") or transport.get("container_no"))
    link_template = CARRIER_LINKS.get(carrier)
    tracking_url = link_template.format(ref=reference) if link_template and reference else ""

    milestones: list[dict[str, Any]] = []
    if text(transport.get("etd")):
        milestones.append({"time": _ddmmyyyy(transport.get("etd")), "title": "ETD — rời nơi lấy hàng",
                           "desc": text(transport.get("pol")), "done": True, "tone": "green"})
    if text(arrival.get("arrival_date")):
        milestones.append({"time": _ddmmyyyy(arrival.get("arrival_date")), "title": "ETA — về cửa khẩu/kho đích",
                           "desc": text(transport.get("pod")), "done": bool(customs.get("tk_no")), "tone": "blue"})
    if text(customs.get("tk_no")):
        milestones.append({"time": _ddmmyyyy(customs.get("reg_date")), "title": "Đăng ký tờ khai nhập khẩu",
                           "desc": f"TK {text(customs.get('tk_no'))} · luồng {text(customs.get('phan_luong')) or 'chờ phân luồng'}",
                           "done": True, "tone": "blue"})
    if customs.get("customs_status"):
        milestones.append({"time": _ddmmyyyy(customs.get("clearance_date")), "title": "Đã thông quan",
                           "desc": "", "done": True, "tone": "green"})
    if text(delivery.get("delivery_date")):
        milestones.append({"time": _ddmmyyyy(delivery.get("delivery_date")), "title": "Lịch giao hàng",
                           "desc": text(delivery.get("addr")), "done": bool(delivery.get("is_delivered")),
                           "tone": "green" if delivery.get("is_delivered") else "amber"})
    if delivery.get("is_delivered"):
        milestones.append({"time": _ddmmyyyy(delivery.get("delivered_at")), "title": "Đã giao hàng",
                           "desc": text(delivery.get("receiver_name")), "done": True, "tone": "green"})

    return {
        "status": status_label,
        "statusTone": tone,
        "carrier": carrier,
        "reference": reference,
        "trackingUrl": tracking_url,
        "hasLivePosition": False,
        "positionNote": "Không có dữ liệu vị trí thời gian thực — chỉ hiển hiện trạng thái và mốc vận chuyển có thật.",
        "milestones": milestones,
    }
