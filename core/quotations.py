"""Bounded commercial quotation domain for LOG-C12.

Estimates remain separate from the canonical finance ledger.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import date, datetime, timezone
import re
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


def _optional_decimal(value: Any) -> Decimal | None:
    """A quote-line fact that may legitimately be UNKNOWN.

    LOGI_QUOTE_COST_WORKFLOW_UX_01_REPAIR_02 — ``_decimal()`` maps a blank to
    Decimal("0"), which is correct for the many callers whose fields are always
    present but WRONG for the three optional quotation facts (internal cost
    price, VAT, quote-time FX). A Sale pasting a customer message states SELL
    prices only; coercing the rest to zero manufactures a 100% margin and a 0%
    VAT commitment, and refusing the save forces the operator to invent numbers.

    ``None`` here means "chưa biết" and travels as ``None`` all the way out.
    An explicitly typed ``0`` is a real zero and is NOT treated as unknown.
    ``_decimal()`` itself is deliberately left unchanged.
    """
    if value is None:
        return None
    if isinstance(value, str) and not value.strip():
        return None
    try:
        return Decimal(str(value).replace(",", "").strip())
    except (InvalidOperation, ValueError):
        return None


def _money_or_none(value: Decimal | None, currency: str = "VND") -> float | None:
    """``_money`` that keeps UNKNOWN as UNKNOWN instead of rounding it to 0."""
    return None if value is None else _money(value, currency)


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
    rates = {str(code).upper(): float(_decimal(rate).quantize(Decimal("0.00000001"))) for code, rate in dict(raw.get("rates_to_vnd") or {}).items() if _decimal(rate).is_finite() and _decimal(rate) > 0}
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


def has_rate(currency: str, fx_snapshot: Mapping[str, Any]) -> bool:
    """True when the quote really stores a rate for this currency.

    The app never invents an FX rate, so a quote whose lines are in a currency
    with no stored rate simply has UNKNOWN VND figures — it is still a perfectly
    valid quotation in its own currency.
    """
    return str(currency or "VND").upper() in dict(fx_snapshot.get("rates_to_vnd") or {})


def _convert_or_none(amount: Decimal | None, currency: str,
                     fx_snapshot: Mapping[str, Any]) -> Decimal | None:
    """VND value of an amount, or None when the amount or the rate is UNKNOWN."""
    if amount is None or not has_rate(currency, fx_snapshot):
        return None
    return convert_to_vnd(amount, currency, fx_snapshot)


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


def calculate_quote(quote: Mapping[str, Any], *, allow_incomplete: bool = False) -> dict[str, Any]:
    """Price a quotation, keeping UNKNOWN facts UNKNOWN.

    LOGI_QUOTE_COST_WORKFLOW_UX_01_REPAIR_02 — a DRAFT quotation is savable from
    what the customer conversation actually states: service name, quantity,
    SELL price and currency. Three facts may legitimately be unknown:

      * ``cost_unit`` — the internal buy price, often not known when quoting;
      * ``tax_pct``   — VAT, frequently confirmed later;
      * the quote-time FX rate for a non-VND line.

    None of them is ever coerced to zero, and none of them blocks the save. An
    unknown input yields an unknown OUTPUT (``None``), and any aggregate that
    would have to consume it is ``None`` too — so a margin is never computed as
    though an unknown cost were 0, and a VND grand total never appears without
    the rate it would need. An explicitly typed ``0`` stays a real zero.
    """
    if isinstance(quote.get("excel_quote"), Mapping):
        return _calculate_excel_quote(quote)
    result = deepcopy(dict(quote))
    validate_quote_date(result.get("expected_delivery_date"))
    incomplete_draft = allow_incomplete and str(result.get("status") or "DRAFT") == "DRAFT"
    fx = normalize_fx_snapshot(result.get("fx_snapshot"))
    result["fx_snapshot"] = fx
    line_results: list[dict[str, Any]] = []
    total_cost_vnd = Decimal("0")
    total_sell_vnd = Decimal("0")
    total_tax_vnd = Decimal("0")
    # An aggregate stops being a number the moment one contributing fact is
    # unknown; it is then reported as UNKNOWN rather than as a smaller number.
    cost_vnd_known = True
    sell_vnd_known = True
    tax_vnd_known = True
    for index, raw_line in enumerate(result.get("service_lines") or [], start=1):
        line = deepcopy(dict(raw_line))
        qty = _decimal(line.get("qty"), "1")
        currency = str(line.get("currency") or "VND").upper()
        # REQUIRED: the customer-facing amount and how many of them.
        sell_unit = _optional_decimal(line.get("sell_unit"))
        if sell_unit is None and not incomplete_draft:
            raise ValueError(
                f"Dòng dịch vụ {index}: chưa có giá bán. "
                "Giá bán là con số báo cho khách nên bắt buộc phải có."
            )
        # OPTIONAL: may be unknown without making the quotation untruthful.
        cost_unit = _optional_decimal(line.get("cost_unit"))
        tax_pct = _optional_decimal(line.get("tax_pct"))
        if qty <= 0 or (sell_unit is not None and sell_unit < 0):
            raise ValueError(f"Dòng dịch vụ {index}: số lượng/giá bán không hợp lệ.")
        if cost_unit is not None and cost_unit < 0:
            raise ValueError(f"Dòng dịch vụ {index}: giá vốn không hợp lệ.")
        if tax_pct is not None and (tax_pct < 0 or tax_pct > 100):
            raise ValueError(f"Dòng dịch vụ {index}: thuế phải trong khoảng 0–100%.")

        # An Excel draft can retain a proposed price without confirming it.
        confirmed = line.get("sell_confirmed", True) is True
        sell = None if sell_unit is None or not confirmed else sell_unit * qty
        cost = None if cost_unit is None else cost_unit * qty
        tax = None if tax_pct is None or sell is None else sell * tax_pct / Decimal("100")

        # VND figures need BOTH the amount and a stored rate for this currency.
        sell_vnd = _convert_or_none(sell, currency, fx)
        cost_vnd = _convert_or_none(cost, currency, fx)
        tax_vnd = _convert_or_none(tax, currency, fx)

        unknown_bits = []
        if sell is None:
            unknown_bits.append("chưa có giá bán được xác nhận")
        if cost_unit is None:
            unknown_bits.append("chưa biết giá vốn")
        if tax_pct is None:
            unknown_bits.append("chưa biết thuế")
        if not has_rate(currency, fx):
            unknown_bits.append(f"chưa có tỷ giá {currency} → VND")
        basis = (f"{line.get('service_name') or line.get('code') or 'Dịch vụ'}: "
                 f"{qty} × {sell_unit} {currency}")
        if cost_unit is not None:
            basis += f"; chi phí {cost_unit} {currency}"
        if tax_pct is not None:
            basis += f"; thuế {tax_pct}%"
        if unknown_bits:
            basis += " (" + ", ".join(unknown_bits) + ")"

        line.update({
            "line_no": index, "currency": currency, "qty": float(qty),
            "cost_unit": _money_or_none(cost_unit, currency),
            "sell_unit": _money_or_none(sell_unit, currency),
            "tax_pct": _money_or_none(tax_pct, currency),
            "cost_total": _money_or_none(cost, currency),
            "sell_total": _money_or_none(sell, currency),
            "tax_total": _money_or_none(tax, currency),
            "cost_vnd": _money_or_none(cost_vnd, "VND"),
            "sell_vnd": _money_or_none(sell_vnd, "VND"),
            "tax_vnd": _money_or_none(tax_vnd, "VND"),
            "calculation_basis": basis,
        })
        line_results.append(line)
        if sell_vnd is None:
            sell_vnd_known = False
        else:
            total_sell_vnd += sell_vnd
        if cost_vnd is None:
            cost_vnd_known = False
        else:
            total_cost_vnd += cost_vnd
        if tax_vnd is None:
            tax_vnd_known = False
        else:
            total_tax_vnd += tax_vnd

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

    # Per-currency subtotals: the quotation is still fully useful in its own
    # currencies even when no FX rate exists, so these are ALWAYS known.
    per_currency: dict[str, dict[str, Any]] = {}
    for line in line_results:
        code = str(line.get("currency") or "VND").upper()
        bucket = per_currency.setdefault(
            code, {"sell_total": Decimal("0"), "sell_known": True, "tax_known": True, "tax_total": Decimal("0")})
        if line.get("sell_total") is None:
            bucket["sell_known"] = False
        else:
            bucket["sell_total"] += _decimal(line.get("sell_total"))
        if line.get("tax_total") is None:
            bucket["tax_known"] = False
        else:
            bucket["tax_total"] += _decimal(line.get("tax_total"))
    totals_by_currency = [
        {
            "currency": code,
            "sell_total": _money(data["sell_total"], code) if data["sell_known"] else None,
            "tax_total": _money(data["tax_total"], code) if data["tax_known"] else None,
            "sell_total_with_tax": (_money(data["sell_total"] + data["tax_total"], code)
                                    if data["tax_known"] and data["sell_known"] else None),
        }
        for code, data in sorted(per_currency.items())
    ]

    # A VND aggregate exists only when every contributing figure is known.
    sell_total_vnd = total_sell_vnd if sell_vnd_known else None
    cost_total_vnd = total_cost_vnd if cost_vnd_known else None
    tax_total_vnd = total_tax_vnd if tax_vnd_known else None
    grand_total_vnd = (sell_total_vnd + tax_total_vnd
                       if sell_total_vnd is not None and tax_total_vnd is not None else None)
    margin_vnd = (sell_total_vnd - cost_total_vnd
                  if sell_total_vnd is not None and cost_total_vnd is not None else None)
    margin_pct = (margin_vnd / sell_total_vnd * Decimal("100")
                  if margin_vnd is not None and sell_total_vnd else None)

    unknown_reasons: list[str] = []
    if not sell_vnd_known:
        unknown_reasons.append("Chưa xác định tổng VND: còn giá bán chưa xác nhận hoặc thiếu tỷ giá báo giá.")
    if not cost_vnd_known:
        unknown_reasons.append("Chưa biết tổng chi phí: có dòng chưa nhập giá vốn (hoặc thiếu tỷ giá).")
    if not tax_vnd_known:
        unknown_reasons.append("Chưa biết tổng thuế: có dòng chưa nhập VAT (hoặc thiếu tỷ giá).")

    result["service_lines"] = line_results; result["fees"] = fees
    result["calculation"] = {
        "base_currency": "VND",
        "estimated_cost_vnd": _money_or_none(cost_total_vnd),
        "selling_price_before_tax_vnd": _money_or_none(sell_total_vnd),
        "estimated_output_tax_vnd": _money_or_none(tax_total_vnd),
        "selling_price_total_vnd": _money_or_none(grand_total_vnd),
        "estimated_margin_vnd": _money_or_none(margin_vnd),
        "estimated_margin_pct": _money_or_none(margin_pct, "USD"),
        # Original-currency truth, always available.
        "totals_by_currency": totals_by_currency,
        # Why a VND figure above is UNKNOWN — never a silent blank.
        "unknown_reasons": unknown_reasons,
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
    if quote.get("excel_quote") and target not in {"DRAFT", "REJECTED"}:
        quote = calculate_quote({**dict(quote), "status": target})
    updated = deepcopy(dict(quote)); updated["status"] = target; updated["version"] = int(updated.get("version") or 1) + (1 if target != current else 0); updated["updated_at"] = _now()
    history = list(updated.get("status_history") or [])
    if target != current: history.append({"from": current, "to": target, "at": _now(), "actor": actor})
    updated["status_history"] = history
    if target == "SENT" and target != current:
        versions = deepcopy(updated.get("sent_versions") or [])
        versions.append({"version": updated["version"], "sent_at": _now(), "sent_by": actor,
                         "customer_snapshot": customer_quote_snapshot(updated)})
        updated["sent_versions"] = versions
    return updated


def build_shipment_draft(quote: Mapping[str, Any], shipment_id: str) -> dict[str, Any]:
    # LOGI_QUOTE_COST_WORKFLOW_UX_01_REPAIR_02 — the `, 0` fallbacks here used to
    # resurrect a quote's UNKNOWN cost/VAT as a confident zero on the new lot's
    # commercial estimate. A fact the quotation never knew must arrive at the
    # shipment as UNKNOWN (None) so the desk shows a gap, not a fabricated 0đ.
    # Finance Actual is a separate surface and is not touched by this.
    # The ORIGINAL currency amount is carried alongside, so a line whose VND
    # value is unknown for lack of FX is not silently emptied either.
    details = [{
        "name_full": line.get("service_name") or line.get("code") or "Dịch vụ báo giá", "display_name": line.get("service_name") or line.get("code") or "Dịch vụ báo giá",
        "code": line.get("code", ""), "qty": line.get("qty", 1),
        "price": line.get("sell_vnd"), "cost": line.get("cost_vnd"),
        "vat": line.get("tax_pct"), "vat_line": line.get("tax_pct"),
        "currency": "VND", "quote_estimate": True,
        "quote_currency": str(line.get("currency") or "VND").upper(),
        "quote_sell_total": line.get("sell_total"),
        "quote_cost_total": line.get("cost_total"),
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


# Excel quote is an extension of this authority, not a second price engine.
def validate_quote_date(value: Any) -> None:
    if value in (None, ""):
        return
    raw = str(value).strip()
    for pattern, fmt in ((r"\d{4}-\d{2}-\d{2}", "%Y-%m-%d"), (r"\d{2}/\d{2}/\d{4}", "%d/%m/%Y")):
        if re.fullmatch(pattern, raw):
            try:
                datetime.strptime(raw, fmt)
                return
            except ValueError:
                break
    raise ValueError("Ngày giao dự kiến không hợp lệ; dùng ngày thực YYYY-MM-DD hoặc DD/MM/YYYY.")


def _excel_number(value: Any, label: str, *, maximum: Decimal = Decimal("100000000000000")) -> Decimal | None:
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    number = _optional_decimal(value)
    if isinstance(value, bool) or number is None or not number.is_finite() or number < 0 or number > maximum:
        raise ValueError(f"{label}: phải là số không âm hợp lệ (ô trống là chưa biết).")
    return number


def _nullable_sum(values: list[Decimal | None]) -> Decimal | None:
    return None if any(v is None for v in values) else sum(values, Decimal("0"))


def _calculate_excel_quote(quote: Mapping[str, Any]) -> dict[str, Any]:
    """Goods/customs context composed with the existing service-line engine.

    A and B are independently priced with calculate_quote. No fee is inserted,
    copied between options, or inferred from Incoterm. Customs uses a separately
    confirmed VND basis, never a selling-price-derived basis.
    """
    from core.quote_excel_import import DISCLOSURES, PARSER_VERSION

    result = deepcopy(dict(quote))
    details = deepcopy(dict(result.pop("excel_quote")))
    if details.get("schema") != PARSER_VERSION:
        raise ValueError("Phiên bản bảng Excel không được hỗ trợ.")
    validate_quote_date(result.get("expected_delivery_date"))
    fx = normalize_fx_snapshot(result.get("fx_snapshot"))
    result["fx_snapshot"] = fx
    goods = details.get("goods")
    if not isinstance(goods, list) or not 1 <= len(goods) <= 200:
        raise ValueError("Bảng hàng hóa cần từ 1 đến 200 dòng.")
    goods_out, qty_values, goods_vnd = [], [], []
    buckets: dict[str, list[Decimal | None]] = {}
    for i, raw in enumerate(goods, 1):
        if not isinstance(raw, Mapping):
            raise ValueError("Dòng hàng hóa không hợp lệ.")
        currency = str(raw.get("currency") or "CNY").upper().replace("RMB", "CNY")
        if currency not in {"CNY", "USD", "VND"}:
            raise ValueError("Tiền hàng chỉ hỗ trợ CNY (RMB), USD, VND.")
        item = {k: str(raw.get(k) or "")[:2000] for k in ("id", "description", "model", "material", "note", "source_sheet")}
        item["source_row"] = raw.get("source_row") if isinstance(raw.get("source_row"), int) else None
        for field in ("length_mm", "width_mm", "height_mm", "qty", "unit_price"):
            n = _excel_number(raw.get(field), f"Hàng {i} · {field}")
            item[field] = float(n) if n is not None else None
        qty = _optional_decimal(item["qty"])
        price = _optional_decimal(item["unit_price"])
        amount = None if qty is None or price is None else qty * price
        item.update({"currency": currency, "line_total": _money_or_none(amount, currency)})
        goods_out.append(item)
        qty_values.append(qty)
        goods_vnd.append(_convert_or_none(amount, currency, fx))
        buckets.setdefault(currency, []).append(amount)
    details["goods"] = goods_out
    active = details.get("active_option", "A")
    if active not in {"A", "B"}:
        raise ValueError("Chọn phương án A hoặc B.")
    details["active_option"] = active
    options, priced_options = {}, {}
    for key in ("A", "B"):
        option = dict((details.get("options") or {}).get(key) or {})
        raw_lines = option.get("service_lines") or []
        if not isinstance(raw_lines, list) or len(raw_lines) > 100:
            raise ValueError("Mỗi phương án tối đa 100 dòng phí.")
        lines = []
        for i, raw in enumerate(raw_lines, 1):
            name = str(raw.get("service_name") or "").strip()
            if not name:
                raise ValueError(f"Phương án {key}, dòng {i}: thiếu tên dịch vụ.")
            line = {k: str(raw.get(k) or "")[:2000] for k in ("id", "code", "unit", "internal_note", "public_note", "cost_source", "valid_until", "condition", "rate_snapshot_id", "rate_row_id", "validity_status", "source_warning")}
            line.update({"service_name": name[:500], "currency": str(raw.get("currency") or "VND").upper(),
                         "sell_confirmed": raw.get("sell_confirmed") is True})
            if line["currency"] not in {"CNY", "USD", "VND"}:
                raise ValueError("Tiền dịch vụ chỉ hỗ trợ CNY, USD, VND.")
            for field in ("qty", "cost_unit", "sell_unit", "tax_pct"):
                n = _excel_number(raw.get(field), f"Phương án {key} · dòng {i} · {field}")
                line[field] = float(n) if n is not None else None
            if line["qty"] is None or line["qty"] <= 0:
                raise ValueError(f"Phương án {key}, dòng {i}: số lượng phải lớn hơn 0; không tự đổi 0 thành 1.")
            lines.append(line)
        # The existing arithmetic handles unknown sell, VAT, cost and FX.
        priced = calculate_quote({**result, "status": "DRAFT", "service_lines": lines}, allow_incomplete=True)
        priced_options[key] = priced
        options[key] = {"scope": str(option.get("scope") or "")[:4000], "service_lines": priced["service_lines"], "calculation": priced["calculation"]}
    details["options"] = options
    selected = priced_options[active]
    # Preserve the quote's actual status/identity, not the internal draft used
    # to compute inactive option B. This is not a status transition.
    selected["status"] = str(result.get("status") or "DRAFT")

    customs = dict(details.get("customs") or {})
    c = {k: str(customs.get(k) or "")[:4000] for k in ("basis_note", "hs_code")}
    c["confirmed"] = customs.get("confirmed") is True
    for key in ("basis_vnd", "duty_pct", "vat_pct"):
        n = _excel_number(customs.get(key), key, maximum=Decimal("100") if key.endswith("pct") else Decimal("100000000000000"))
        c[key] = float(n) if n is not None else None
    tax_known = c["confirmed"] and bool(c["basis_note"].strip()) and all(c[k] is not None for k in ("basis_vnd", "duty_pct", "vat_pct"))
    basis, duty, vat = None, None, None
    if tax_known:
        basis = _decimal(c["basis_vnd"])
        duty = basis * _decimal(c["duty_pct"]) / 100
        vat = (basis + duty) * _decimal(c["vat_pct"]) / 100
    c.update({"duty_vnd": _money_or_none(duty), "vat_vnd": _money_or_none(vat),
              "total_vnd": _money_or_none(None if duty is None or vat is None else duty + vat), "calculable": bool(tax_known)})
    details["customs"] = c
    disclosure_map = {x.get("id"): x for x in details.get("disclosures") or [] if isinstance(x, Mapping)}
    details["disclosures"] = [{"id": k, "text": text, "selected": disclosure_map.get(k, {}).get("selected") is True} for k, text in DISCLOSURES]
    details["additional_public_notes"] = str(details.get("additional_public_notes") or "")[:12000]
    details["supplier"] = str(details.get("supplier") or "")[:2000]
    shipment = dict(details.get("shipment") or {})
    details["shipment"] = {k: str(shipment.get(k) or "")[:2000] for k in ("pol", "pod", "pickup", "delivery", "load_model", "equipment")}
    for key in ("cbm", "weight_kg"):
        n = _excel_number(shipment.get(key), key)
        details["shipment"][key] = float(n) if n is not None else None
    details["warning_notes"] = {str(k): {"status": str(v.get("status") or "UNRESOLVED")[:30], "note": str(v.get("note") or "")[:2000]}
                                for k, v in dict(details.get("warning_notes") or {}).items() if isinstance(v, Mapping)}
    goods_total_vnd = _nullable_sum(goods_vnd)
    services = selected["calculation"]
    before_tax = _nullable_sum([goods_total_vnd, _optional_decimal(services["selling_price_before_tax_vnd"])])
    estimate = _nullable_sum([goods_total_vnd, _optional_decimal(services["selling_price_total_vnd"]), _optional_decimal(c["total_vnd"])])
    reasons = []
    if goods_total_vnd is None:
        reasons.append("Tiền hàng chưa đủ dữ liệu hoặc thiếu tỷ giá → không có tổng VND xác định.")
    if any(l.get("sell_total") is None for l in selected["service_lines"]):
        reasons.append("Còn phí chưa có giá bán xác nhận; chưa công bố các dòng này.")
    if services["selling_price_total_vnd"] is None:
        reasons.append("Phí dịch vụ chưa đủ giá bán, VAT dịch vụ hoặc tỷ giá.")
    if not tax_known:
        reasons.append("Thuế NK / VAT NK chưa xác định: cần trị giá hải quan, thuế suất và căn cứ riêng được xác nhận.")
    count = _nullable_sum(qty_values)
    details["calculation"] = {
        "row_count": len(goods_out), "quantity": float(count) if count is not None else None,
        "goods_totals": [{"currency": code, "amount": _money_or_none(_nullable_sum(amounts), code)} for code, amounts in sorted(buckets.items())],
        "goods_total_vnd": _money_or_none(goods_total_vnd), "before_tax_vnd": _money_or_none(before_tax),
        "estimate_vnd": _money_or_none(estimate), "unknown_reasons": reasons,
    }
    if selected["status"] not in {"DRAFT", "REJECTED", "EXPIRED"}:
        if any(g[k] is None for g in goods_out for k in ("qty", "unit_price", "length_mm", "width_mm", "height_mm")):
            raise ValueError("Cần bổ sung dữ liệu hàng hóa trước khi chuyển khỏi nháp.")
        if any(l["sell_total"] is None for l in selected["service_lines"]):
            raise ValueError("Phương án đang chọn còn dòng chưa xác nhận giá bán; chỉ bản nháp được lưu thiếu giá.")
        if not options[active]["scope"].strip():
            raise ValueError("Cần xác nhận phạm vi dịch vụ; Incoterm không tự phân trách nhiệm.")
    selected["excel_quote"] = details
    selected["customer_notes"] = [d["text"] for d in details["disclosures"] if d["selected"]]
    if details["additional_public_notes"].strip():
        selected["customer_notes"].append(details["additional_public_notes"])
    return selected


def customer_quote_snapshot(quote: Mapping[str, Any]) -> dict[str, Any]:
    """Single customer allowlist used by live preview, sent history and XLSX.

    Never copy an internal quote wholesale: cost, profit, source, warning notes,
    provenance and Sale audit/status history have no path to this object.
    """
    details = dict(quote.get("excel_quote") or {})
    active = str(details.get("active_option") or "A")
    out = {k: deepcopy(quote.get(k)) for k in ("id", "quote_no", "version", "status", "created_at", "customer_id", "customer_name", "customer_contact", "customer_email", "customer_phone", "goods_description", "origin", "destination", "route", "incoterm", "transport_mode", "expected_delivery_date")}
    out["fx_snapshot"] = {"base_currency": "VND", "rates_to_vnd": deepcopy((quote.get("fx_snapshot") or {}).get("rates_to_vnd") or {})}
    out["service_lines"] = [{k: deepcopy(l.get(k)) for k in ("service_name", "unit", "qty", "currency", "sell_unit", "sell_total", "tax_pct", "tax_total", "public_note", "condition")}
                            for l in quote.get("service_lines") or [] if l.get("sell_unit") is not None and l.get("sell_confirmed", True) is True]
    out["customer_notes"] = list(quote.get("customer_notes") or [])
    if details:
        out["goods"] = [{k: g.get(k) for k in ("description", "model", "material", "length_mm", "width_mm", "height_mm", "qty", "unit_price", "currency", "line_total", "note")} for g in details.get("goods") or []]
        out["option"] = active
        out["scope"] = str((details.get("options") or {}).get(active, {}).get("scope") or "")
        out["shipment"] = deepcopy(details.get("shipment") or {})
        out["customs"] = {k: details.get("customs", {}).get(k) for k in ("calculable", "basis_vnd", "duty_pct", "vat_pct", "duty_vnd", "vat_vnd", "total_vnd")}
        out["goods_calculation"] = deepcopy(details.get("calculation") or {})
        out["services_calculation"] = {k: quote.get("calculation", {}).get(k) for k in ("totals_by_currency", "selling_price_before_tax_vnd", "estimated_output_tax_vnd", "selling_price_total_vnd")}
    return out
