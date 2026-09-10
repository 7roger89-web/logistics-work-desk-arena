"""Bounded commercial quotation domain for LOG-C12.

Estimates remain separate from the canonical finance ledger.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Mapping
from uuid import uuid4

QUOTE_STATUSES = ("DRAFT", "READY_FOR_REVIEW", "SENT", "ACCEPTED", "REJECTED", "EXPIRED", "READY_TO_CREATE_SHIPMENT")
ENTRUSTED_IMPORT_NORMAL_RATE_RANGE = (Decimal("2"), Decimal("3"))
HIGH_VALUE_THRESHOLD_POLICY_NOT_CONFIGURED = "POLICY_NOT_CONFIGURED"
_ALLOWED_TRANSITIONS = {
    "DRAFT": {"READY_FOR_REVIEW", "REJECTED"},
    "READY_FOR_REVIEW": {"SENT", "ACCEPTED", "REJECTED", "DRAFT"},
    "SENT": {"ACCEPTED", "REJECTED", "EXPIRED", "DRAFT"},
    "ACCEPTED": {"READY_TO_CREATE_SHIPMENT"},
    "READY_TO_CREATE_SHIPMENT": set(), "REJECTED": set(), "EXPIRED": set(),
}


def _decimal(value: Any, default: str = "0") -> Decimal:
    try:
        if value is None or value == "":
            return Decimal(default)
        return Decimal(str(value).replace(",", "").strip())
    except (InvalidOperation, ValueError):
        return Decimal(default)


def _money(value: Decimal, currency: str = "VND") -> float:
    quantum = Decimal("1") if currency.upper() == "VND" else Decimal("0.01")
    return float(value.quantize(quantum, rounding=ROUND_HALF_UP))


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def new_quote_identity(now: date | None = None) -> tuple[str, str]:
    stamp = (now or date.today()).strftime("%Y%m%d")
    token = uuid4().hex[:8].upper()
    return f"Q-{stamp}-{token}", f"QT-{stamp}-{token}"


def normalize_fx_snapshot(snapshot: Mapping[str, Any] | None) -> dict[str, Any]:
    raw = dict(snapshot or {})
    rates = {str(code).upper(): _money(_decimal(rate), "VND") for code, rate in dict(raw.get("rates_to_vnd") or {}).items() if _decimal(rate) > 0}
    rates["VND"] = 1.0
    return {
        "base_currency": "VND",
        "rates_to_vnd": rates,
        "source": str(raw.get("source") or "Tỷ giá nhập khi báo giá; không phải tỷ giá giao dịch thực tế."),
        "captured_at": str(raw.get("captured_at") or _now()),
    }


def convert_to_vnd(amount: Any, currency: str, fx_snapshot: Mapping[str, Any]) -> Decimal:
    code = str(currency or "VND").upper()
    rates = dict(fx_snapshot.get("rates_to_vnd") or {})
    if code not in rates:
        raise ValueError(f"Thiếu tỷ giá báo giá {code} → VND.")
    return _decimal(amount) * _decimal(rates[code])


def calculate_remittance_estimate(remittance: Mapping[str, Any] | None, fx_snapshot: Mapping[str, Any]) -> dict[str, Any]:
    data = dict(remittance or {})
    amount = _decimal(data.get("remitted_amount_usd"))
    bank_pct = _decimal(data.get("bank_fee_pct"))
    swift = _decimal(data.get("swift_fee_usd"))
    receiving = _decimal(data.get("receiving_bank_fee_usd"))
    agent = _decimal(data.get("agent_conversion_fee_usd"))
    rmb = _decimal(data.get("rmb_conversion_fee_cny"))
    usd_rate = _decimal(fx_snapshot.get("rates_to_vnd", {}).get("USD"))
    cny_rate = _decimal(fx_snapshot.get("rates_to_vnd", {}).get("CNY"))
    bank_fee = amount * bank_pct / Decimal("100")
    total_usd = bank_fee + swift + receiving + agent
    total_vnd = total_usd * usd_rate + rmb * cny_rate
    return {
        "formula": "phí ngân hàng = số tiền chuyển × % phí; tổng = phí ngân hàng + SWIFT + receiving + agent + RMB",
        "remitted_amount_usd": _money(amount, "USD"), "bank_fee_pct": _money(bank_pct, "USD"),
        "bank_fee_usd": _money(bank_fee, "USD"), "swift_fee_usd": _money(swift, "USD"),
        "receiving_bank_fee_usd": _money(receiving, "USD"), "agent_conversion_fee_usd": _money(agent, "USD"),
        "rmb_conversion_fee_cny": _money(rmb, "CNY"), "estimated_total_usd": _money(total_usd, "USD"),
        "estimated_total_vnd": _money(total_vnd, "VND"),
        "source": str(data.get("source") or "Nhập theo báo giá ngân hàng/đại lý; chỉ là ước tính, không ghi sổ."),
    }


def calculate_quote(quote: Mapping[str, Any]) -> dict[str, Any]:
    result = deepcopy(dict(quote))
    fx = normalize_fx_snapshot(result.get("fx_snapshot"))
    result["fx_snapshot"] = fx
    line_results: list[dict[str, Any]] = []
    total_cost_vnd = Decimal("0")
    total_sell_vnd = Decimal("0")
    total_tax_vnd = Decimal("0")
    for index, raw_line in enumerate(result.get("service_lines") or [], start=1):
        line = deepcopy(dict(raw_line))
        qty = _decimal(line.get("qty"), "1")
        currency = str(line.get("currency") or "VND").upper()
        cost_unit = _decimal(line.get("cost_unit"))
        sell_unit = _decimal(line.get("sell_unit"))
        tax_pct = _decimal(line.get("tax_pct"))
        if qty <= 0 or cost_unit < 0 or sell_unit < 0 or tax_pct < 0 or tax_pct > 100:
            raise ValueError(f"Dòng dịch vụ {index}: số lượng/giá/thuế không hợp lệ.")
        cost = cost_unit * qty; sell = sell_unit * qty; tax = sell * tax_pct / Decimal("100")
        cost_vnd = convert_to_vnd(cost, currency, fx); sell_vnd = convert_to_vnd(sell, currency, fx); tax_vnd = convert_to_vnd(tax, currency, fx)
        line.update({
            "line_no": index, "currency": currency, "qty": _money(qty, currency),
            "cost_total": _money(cost, currency), "sell_total": _money(sell, currency), "tax_total": _money(tax, currency),
            "cost_vnd": _money(cost_vnd, "VND"), "sell_vnd": _money(sell_vnd, "VND"), "tax_vnd": _money(tax_vnd, "VND"),
            "calculation_basis": f"{line.get('service_name') or line.get('code') or 'Dịch vụ'}: {qty} × {sell_unit} {currency}; chi phí {cost_unit} {currency}; thuế {tax_pct}%",
        })
        line_results.append(line); total_cost_vnd += cost_vnd; total_sell_vnd += sell_vnd; total_tax_vnd += tax_vnd

    fees: dict[str, Any] = {}
    entrusted = dict(result.get("entrusted_import") or {})
    if entrusted.get("active"):
        goods_value = _decimal(entrusted.get("goods_value")); goods_currency = str(entrusted.get("goods_currency") or "USD").upper(); rate_pct = _decimal(entrusted.get("rate_pct"))
        if goods_value <= 0 or rate_pct <= 0:
            raise ValueError("Phí ủy thác đang bật nhưng thiếu giá trị hàng hoặc tỷ lệ phí.")
        basis_vnd = convert_to_vnd(goods_value, goods_currency, fx); amount_vnd = basis_vnd * rate_pct / Decimal("100")
        policy = dict(entrusted.get("high_value_review_policy") or {})
        threshold_raw = policy.get("threshold")
        threshold = _decimal(threshold_raw) if threshold_raw not in (None, "") else Decimal("0")
        policy_configured = threshold > 0
        policy_currency = str(policy.get("currency") or goods_currency).upper()
        high_value_by_policy = policy_configured and policy_currency == goods_currency and goods_value >= threshold
        review_reasons: list[str] = []
        if not (ENTRUSTED_IMPORT_NORMAL_RATE_RANGE[0] <= rate_pct <= ENTRUSTED_IMPORT_NORMAL_RATE_RANGE[1]):
            review_reasons.append("Tỷ lệ phí nằm ngoài khoảng commercial reference 2–3%; cần review.")
        if bool(entrusted.get("review_requested")):
            review_reasons.append(str(entrusted.get("review_reason") or "SALE/manager yêu cầu review thương mại."))
        if high_value_by_policy:
            review_reasons.append(str(policy.get("reason") or "Policy đã cấu hình yêu cầu review theo giá trị hàng."))
        fees["entrusted_import"] = {
            "basis": _money(basis_vnd, "VND"), "basis_original": _money(goods_value, goods_currency), "basis_currency": goods_currency,
            "rate_pct": _money(rate_pct, "USD"), "amount_vnd": _money(amount_vnd, "VND"),
            "formula": f"{goods_value} {goods_currency} × {rate_pct}% × tỷ giá báo giá → VND",
            "source": str(entrusted.get("source") or "Nhập thủ công; cần Sale/Trưởng nhóm xác nhận."),
            "commercial_review_required": bool(review_reasons),
            "commercial_review_reasons": review_reasons,
            "high_value_threshold": _money(threshold, goods_currency) if policy_configured and policy_currency == goods_currency else None,
            "high_value_threshold_currency": policy_currency if policy_configured else None,
            "high_value_threshold_status": "CONFIGURED" if policy_configured else HIGH_VALUE_THRESHOLD_POLICY_NOT_CONFIGURED,
        }
        total_cost_vnd += amount_vnd; total_sell_vnd += amount_vnd
    remittance = calculate_remittance_estimate(result.get("remittance_estimate"), fx)
    if result.get("include_remittance_in_cost"):
        total_cost_vnd += _decimal(remittance["estimated_total_vnd"])
    fees["remittance"] = remittance
    margin_vnd = total_sell_vnd - total_cost_vnd
    result["service_lines"] = line_results; result["fees"] = fees
    result["calculation"] = {
        "base_currency": "VND", "estimated_cost_vnd": _money(total_cost_vnd), "selling_price_before_tax_vnd": _money(total_sell_vnd),
        "estimated_output_tax_vnd": _money(total_tax_vnd), "selling_price_total_vnd": _money(total_sell_vnd + total_tax_vnd),
        "estimated_margin_vnd": _money(margin_vnd), "estimated_margin_pct": _money((margin_vnd / total_sell_vnd * Decimal("100")) if total_sell_vnd else Decimal("0"), "USD"),
        "calculated_at": _now(), "not_finance_ledger": True,
    }
    return result


def allowed_transitions(status: str) -> tuple[str, ...]:
    """Return the business-legal next statuses for a quote status (display only).

    The transition itself is still enforced by :func:`transition_quote`, which
    is the single source of truth; this helper only mirrors that map so a UI
    can offer the allowed choices without re-interpreting the rule.
    """
    return tuple(sorted(_ALLOWED_TRANSITIONS.get(str(status or "").upper(), set())))


def transition_quote(quote: Mapping[str, Any], next_status: str, actor: str = "system") -> dict[str, Any]:
    current = str(quote.get("status") or "DRAFT").upper(); target = str(next_status or "").upper()
    if target not in QUOTE_STATUSES or (target != current and target not in _ALLOWED_TRANSITIONS.get(current, set())):
        raise ValueError(f"Không thể chuyển báo giá từ {current} sang {target}.")
    updated = deepcopy(dict(quote)); updated["status"] = target; updated["version"] = int(updated.get("version") or 1) + (1 if target != current else 0); updated["updated_at"] = _now()
    history = list(updated.get("status_history") or [])
    if target != current: history.append({"from": current, "to": target, "at": _now(), "actor": actor})
    updated["status_history"] = history
    return updated


def build_shipment_draft(quote: Mapping[str, Any], shipment_id: str) -> dict[str, Any]:
    details = [{
        "name_full": line.get("service_name") or line.get("code") or "Dịch vụ báo giá", "display_name": line.get("service_name") or line.get("code") or "Dịch vụ báo giá",
        "code": line.get("code", ""), "qty": line.get("qty", 1), "price": line.get("sell_vnd", 0), "cost": line.get("cost_vnd", 0),
        "vat": line.get("tax_pct", 0), "vat_line": line.get("tax_pct", 0), "currency": "VND", "quote_estimate": True,
        "source_reference": line.get("cost_source") or line.get("source_reference") or "Theo báo giá đã chấp nhận",
    } for line in quote.get("service_lines") or []]
    lots = deepcopy(quote.get("factory_lots") or [])
    first_pickup = lots[0].get("pickup_address", "") if lots else ""
    return {
        "shipment_id": shipment_id, "id": shipment_id, "client": quote.get("customer_name", ""), "customer": quote.get("customer_name", ""), "customer_id": quote.get("customer_id", ""),
        "status": "wait", "currency": "VND", "quote_id": quote.get("id", ""), "quote_reference": quote.get("quote_no", ""), "shipment_creation_request_id": f"quote:{quote.get('id', '')}",
        "factory_lots": lots, "commercial_estimate": {"source_quote_id": quote.get("id", ""), "source_quote_reference": quote.get("quote_no", ""), "assumptions": deepcopy(quote.get("assumptions") or []), "calculation_snapshot": deepcopy(quote.get("calculation") or {}), "not_finance_ledger": True},
        "data": {
            "0.0": {"st": "wait", "created_at": str(date.today()), "mode": quote.get("transport_mode") or "Road", "incoterm": quote.get("incoterm") or "EXW"},
            "1.2": {"origin": quote.get("origin", ""), "destination": quote.get("destination", ""), "route": quote.get("route", "")},
            "2.4": {"goods_description": quote.get("goods_description", "")}, "2.6": {"arrival_date": quote.get("expected_delivery_date", "")}, "2.7": {"addr": first_pickup, "delivery_date": quote.get("expected_delivery_date", "")},
            "3.4": {"details": details, "commission": {"list": [], "total": 0}, "payments": []},
        }, "entrustment": {"active": bool((quote.get("entrusted_import") or {}).get("active"))},
    }


def new_quote_document(payload: Mapping[str, Any]) -> dict[str, Any]:
    quote_id, quote_no = new_quote_identity(); quote = deepcopy(dict(payload))
    quote.update({"id": quote_id, "quote_no": quote_no, "status": "DRAFT", "version": 1, "status_history": [{"from": None, "to": "DRAFT", "at": _now(), "actor": str(quote.get("sales_owner") or "system")}], "created_at": _now(), "updated_at": _now(), "is_estimate": True, "ledger_posted": False})
    return calculate_quote(quote)


def prepare_quote_for_persistence(quote: Mapping[str, Any], actor: str = "system") -> dict[str, Any]:
    """Validate and stamp a quote before the existing quote writer is called.

    The request identity is stable for a quote version, making a retry an
    idempotent upsert rather than a new commercial event. Provenance is kept in
    the quote document because the legacy quote writer has no separate audit API.
    """
    candidate = deepcopy(dict(quote))
    quote_id = str(candidate.get("id") or "").strip()
    quote_no = str(candidate.get("quote_no") or "").strip()
    status = str(candidate.get("status") or "").upper()
    version = int(candidate.get("version") or 0)
    if not quote_id or not quote_no:
        raise ValueError("Báo giá phải có mã và số tham chiếu trước khi lưu.")
    if status not in QUOTE_STATUSES:
        raise ValueError(f"Trạng thái báo giá không hợp lệ: {status}.")
    if version < 1:
        raise ValueError("Phiên bản báo giá không hợp lệ.")
    request_id = f"quote:{quote_id}:v{version}"
    candidate["write_request_id"] = request_id
    candidate["provenance"] = {
        "source": "LOG-C12 commercial quotation workspace",
        "actor": str(actor or "system"),
        "write_request_id": request_id,
        "quote_version": version,
        "status": status,
        "estimate_only": True,
        "ledger_posted": False,
        "updated_at": str(candidate.get("updated_at") or _now()),
    }
    candidate["is_estimate"] = True
    candidate["ledger_posted"] = False
    return candidate
