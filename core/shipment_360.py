"""Read-only Shipment 360 projection.

This module deliberately does not persist anything.  It composes the finance
calculation that already exists in :mod:`core.logic` with explicitly linked
records from the current Mongo repositories.  Missing ledger concepts remain
``UNKNOWN`` instead of being represented by a guessed zero.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from core.logic import calculate_from_shipment
from core.utils import to_decimal


UNKNOWN = "UNKNOWN"
_RECEIVABLE_SOURCE = "core.logic.calculate_from_shipment / data.3.4.details+payments"
_AGENCY_SOURCE = "views.reports agency rule / data.3.4.agency"


def _text(value: Any, default: str = UNKNOWN) -> str:
    if value is None or value == "":
        return default
    return str(value).strip() or default


def _customer_key(mapping: Mapping[str, Any]) -> str:
    return str(mapping.get("customer_id") or mapping.get("customer") or mapping.get("client") or "").strip().casefold()


def _commercial_context(
    shipment_id: str,
    customer: str,
    agreements: Any,
    quotes: Any,
) -> dict[str, Any]:
    """Read-only commercial context for a shipment from the agreements/quotes stores."""

    if not isinstance(agreements, Mapping) and not isinstance(quotes, Mapping):
        return {}
    customer_key = customer.casefold()
    linked_agreements: list[Mapping[str, Any]] = []
    for item in (agreements.values() if isinstance(agreements, Mapping) else ()):
        if not isinstance(item, Mapping):
            continue
        if shipment_id in {str(entry) for entry in (item.get("shipment_ids") or [])}:
            linked_agreements.append(item)
            continue
        if _customer_key(item) and _customer_key(item) == customer_key:
            linked_agreements.append(item)
    agreement = linked_agreements[0] if linked_agreements else {}
    if not agreement and isinstance(quotes, Mapping):
        for item in quotes.values():
            if isinstance(item, Mapping) and str(item.get("shipment_id", "")).strip().casefold() == shipment_id.casefold():
                agreement = {"quote_only": True, "quote": item}
                break

    snapshot = _as_mapping(agreement.get("commercial_snapshot")) or {}
    readiness = _as_mapping(agreement.get("readiness")) or {}
    if not agreement:
        return {}
    return {
        "shipment_id": shipment_id,
        "agreement_id": _text(agreement.get("agreement_id"), ""),
        "agreement_reference": _text(agreement.get("agreement_no")),
        "agreement_status": _text(agreement.get("status")),
        "quote_reference": _text(agreement.get("quote_reference")),
        "incoterm": _text(snapshot.get("incoterm")),
        "services_sold": ", ".join(
            _text(line.get("service_name"))
            for line in snapshot.get("service_lines") or []
            if isinstance(line, Mapping)
        ) or UNKNOWN,
        "required_date": _text(snapshot.get("expected_delivery_date")),
        "handoff_readiness_label": _text(readiness.get("label"), ""),
        "handoff_reasons": list(readiness.get("reasons") or []),
        "source": "agreements/quotes stores; estimate only, not Finance Ledger",
    }


def _as_mapping(value: Any) -> Mapping[str, Any] | None:
    return value if isinstance(value, Mapping) else None


def _number(value: Any) -> float | None:
    """Convert an explicitly stored number without turning missing into zero."""

    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, str) and not value.strip():
        return None
    try:
        number = to_decimal(value)
    except (ArithmeticError, TypeError, ValueError):
        return None
    if not number.is_finite():
        return None
    return float(number)


def _number_or_zero(value: Any) -> float:
    number = _number(value)
    return number if number is not None else 0.0


def _reference(value: Any) -> str:
    return str(value or "").strip().upper()


def _same_reference(left: Any, right: Any) -> bool:
    return bool(_reference(left)) and _reference(left) == _reference(right)


def _records(value: Any) -> Iterable[Mapping[str, Any]]:
    """Iterate either a repository cache or one record without mutating it."""

    if isinstance(value, Mapping):
        record_keys = {
            "id",
            "shipment_id",
            "linked_id",
            "contract_id",
            "amount_vnd",
            "deposits",
        }
        if record_keys.intersection(value):
            yield value
            return
        for item in value.values():
            if isinstance(item, Mapping):
                yield item
        return
    if isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
        for item in value:
            if isinstance(item, Mapping):
                yield item


def _unknown(label: str, reason: str, currency: str | None = None) -> dict[str, Any]:
    return {
        "label": label,
        "value": None,
        "status": UNKNOWN,
        "currency": currency,
        "source": None,
        "reason": reason,
    }


def _known(
    label: str,
    value: float,
    source: str,
    currency: str,
    *,
    status: str = "KNOWN",
    reason: str | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "label": label,
        "value": value,
        "status": status,
        "currency": currency,
        "source": source,
    }
    if reason:
        result["reason"] = reason
    return result


def _first_number(record: Mapping[str, Any], keys: tuple[str, ...]) -> tuple[float | None, bool]:
    for key in keys:
        if key in record:
            return _number(record.get(key)), True
    return 0.0, False


def _contract_ids(shipment: Mapping[str, Any], data: Mapping[str, Any]) -> list[str]:
    raw_values: list[Any] = [shipment.get("contract_id"), data.get("contract_id")]
    contract_ids = shipment.get("contract_ids")
    if isinstance(contract_ids, Iterable) and not isinstance(contract_ids, (str, bytes, Mapping)):
        raw_values.extend(contract_ids)
    entrustment = _as_mapping(data.get("entrustment")) or {}
    raw_values.extend((entrustment.get("contract_id"), entrustment.get("contract_no")))
    result: list[str] = []
    for value in raw_values:
        reference = _reference(value)
        if reference and reference not in result:
            result.append(reference)
    return result


def _link_kind(record: Mapping[str, Any], shipment_id: str, contract_ids: list[str]) -> str | None:
    direct_fields = ("shipment_id", "shipment_code", "shipmentId", "linked_shipment_id", "linked_id")
    for field in direct_fields:
        if _same_reference(record.get(field), shipment_id):
            return "direct"

    contract_fields = ("contract_id", "contract_no", "linked_contract_id")
    for field in contract_fields:
        if _reference(record.get(field)) in contract_ids:
            return "contract"

    # Entrustment records commonly store the contract only in linked_id and
    # identify the link with a human-facing Vietnamese linked_type.
    if _reference(record.get("linked_id")) in contract_ids:
        return "contract"

    linked_type = _reference(record.get("linked_type"))
    if "HOP DONG" in linked_type or "CONTRACT" in linked_type:
        if _reference(record.get("linked_id")) in contract_ids:
            return "contract"
    return None


def _payment_rows(finance: Mapping[str, Any], currency: str) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    payments = finance.get("payments", [])
    if not isinstance(payments, Iterable) or isinstance(payments, (str, bytes, Mapping)):
        return result
    for payment in payments:
        if not isinstance(payment, Mapping):
            continue
        result.append(
            {
                "type": "customer_payment",
                "label": "Khách hàng đã chuyển",
                "id": payment.get("id"),
                "date": payment.get("date") or payment.get("created_at"),
                "amount": _number(payment.get("amount")),
                "currency": payment.get("currency") or currency,
                "note": payment.get("note") or payment.get("description") or "",
                "allocation_status": UNKNOWN,
                "source": "shipment.data.3.4.payments",
            }
        )
    return result


def _agency_payable(finance: Mapping[str, Any]) -> dict[str, Any]:
    agency = _as_mapping(finance.get("agency"))
    if agency is None:
        return {
            "label": "Phải trả tổng thể / đại lý",
            "scope": "agency_only",
            "known": False,
            "total": _unknown("Tổng phải trả", "Chưa có nguồn nghĩa vụ phải trả tổng thể cho shipment", "VND"),
            "paid": _unknown("Đã trả / cấn trừ", "Chưa có allocation/settlement source thống nhất", "VND"),
            "outstanding": _unknown("Còn phải trả", "Chưa có nguồn nghĩa vụ phải trả tổng thể cho shipment", "VND"),
            "source": None,
        }

    fee, fee_present = _first_number(agency, ("fee_vnd", "fee"))
    if not fee_present or fee is None:
        return {
            "label": "Phải trả tổng thể / đại lý",
            "scope": "agency_only",
            "known": False,
            "total": _unknown("Tổng phải trả", "Có mục agency nhưng thiếu fee_vnd/fee hợp lệ", "VND"),
            "paid": _unknown("Đã trả / cấn trừ", "Không thể tính settlement khi tổng nghĩa vụ chưa rõ", "VND"),
            "outstanding": _unknown("Còn phải trả", "Không thể tính khi tổng nghĩa vụ chưa rõ", "VND"),
            "source": _AGENCY_SOURCE,
        }

    collected, collected_present = _first_number(agency, ("collected_vnd", "collected"))
    paid, paid_present = _first_number(agency, ("paid_vnd", "paid"))
    if collected is None or paid is None:
        return {
            "label": "Phải trả đại lý (nguồn agency)",
            "scope": "agency_only",
            "known": False,
            "total": _known("Tổng phải trả", fee, _AGENCY_SOURCE, "VND"),
            "paid": _unknown("Đã trả / cấn trừ", "Agency có giá trị không hợp lệ", "VND"),
            "outstanding": _unknown("Còn phải trả", "Agency có giá trị không hợp lệ", "VND"),
            "source": _AGENCY_SOURCE,
        }

    settled = collected + paid
    return {
        "label": "Phải trả đại lý (nguồn agency)",
        "scope": "agency_only",
        "known": True,
        "total": _known("Tổng phải trả", fee, _AGENCY_SOURCE, "VND"),
        "collected": _known("Đã thu hộ / cấn trừ", collected, _AGENCY_SOURCE, "VND"),
        "paid": _known("Đã trả", paid, _AGENCY_SOURCE, "VND"),
        "settled": _known("Đã trả / cấn trừ", settled, _AGENCY_SOURCE, "VND"),
        "outstanding": _known("Còn phải trả", fee - settled, _AGENCY_SOURCE, "VND"),
        "source": _AGENCY_SOURCE,
        "fields_present": {"fee": fee_present, "collected": collected_present, "paid": paid_present},
    }


def _tax_summary(data: Mapping[str, Any]) -> dict[str, Any]:
    customs = _as_mapping(data.get("2.4")) or {}
    gnt = _as_mapping(customs.get("gnt")) or {}
    raw_rows = gnt.get("ds_thue")
    if not isinstance(raw_rows, list) or not raw_rows:
        return _unknown("Thuế có dữ liệu", "Chưa có dòng thuế GNT hợp lệ", "VND") | {"rows": []}

    rows: list[dict[str, Any]] = []
    total = 0.0
    invalid = 0
    for row in raw_rows:
        if not isinstance(row, Mapping):
            invalid += 1
            continue
        amount = _number(row.get("tien"))
        if amount is None:
            invalid += 1
        else:
            total += amount
        rows.append(
            {
                "name": row.get("ten") or "",
                "code": row.get("ndkt") or "",
                "amount": amount,
                "source": "shipment.data.2.4.gnt.ds_thue",
            }
        )

    if not rows or all(row.get("amount") is None for row in rows):
        return _unknown("Thuế có dữ liệu", "Dòng thuế tồn tại nhưng không có số tiền hợp lệ", "VND") | {"rows": rows}
    status = "PARTIAL" if invalid else "KNOWN"
    reason = "Có dòng thuế thiếu số tiền hợp lệ" if invalid else None
    return _known(
        "Thuế có dữ liệu",
        total,
        "shipment.data.2.4.gnt.ds_thue",
        "VND",
        status=status,
        reason=reason,
    ) | {"rows": rows}


def _explicit_metric(
    label: str,
    mappings: Iterable[Mapping[str, Any]],
    keys: tuple[str, ...],
    reason: str,
    currency: str,
) -> dict[str, Any]:
    for mapping in mappings:
        for key in keys:
            if key in mapping:
                value = _number(mapping.get(key))
                if value is None:
                    return _unknown(label, f"Trường {key} không phải số hợp lệ", currency)
                return _known(label, value, f"explicit field {key}", currency)
    return _unknown(label, reason, currency)


def _proxy_relations(
    shipment_id: str,
    contract_ids: list[str],
    records: Any,
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for record in _records(records):
        kind = _link_kind(record, shipment_id, contract_ids)
        if not kind:
            continue
        result.append(
            {
                "type": "proxy_payment",
                "label": "Thanh toán hộ / proxy payment",
                "id": record.get("id"),
                "link_kind": kind,
                "link_id": record.get("linked_id") or record.get("contract_id") or shipment_id,
                "amount_vnd": _number(record.get("amount_vnd")),
                "original_amount": _number(record.get("amount_fc_needed")),
                "paid_original_amount": _number(record.get("amount_fc_paid")),
                "remaining_original_amount": _number(record.get("amount_fc_remain")),
                "original_currency": record.get("currency"),
                "exchange_rate": _number(record.get("exchange_rate")),
                "rate_date": record.get("rate_date") or record.get("created_at"),
                "beneficiary": record.get("beneficiary"),
                "status": record.get("status"),
                "note": record.get("note") or "",
                "source": "proxy_payments",
            }
        )
    return result


def _entrustment_relations(
    shipment_id: str,
    contract_ids: list[str],
    records: Any,
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for record in _records(records):
        kind = _link_kind(record, shipment_id, contract_ids)
        if not kind:
            continue
        deposits: list[dict[str, Any]] = []
        for deposit in record.get("deposits", []) if isinstance(record.get("deposits"), list) else []:
            if not isinstance(deposit, Mapping):
                continue
            deposits.append(
                {
                    "date": deposit.get("Ngày nạp"),
                    "amount_vnd": _number(deposit.get("Số tiền (VND)")),
                    "note": deposit.get("Ghi chú") or "",
                }
            )
        payment_legs: list[dict[str, Any]] = []
        for payment in record.get("payments", []) if isinstance(record.get("payments"), list) else []:
            if not isinstance(payment, Mapping):
                continue
            payment_legs.append(
                {
                    "sequence": payment.get("Đợt/Lần"),
                    "currency": payment.get("Loại Tiền"),
                    "original_amount": _number(payment.get("Số Tiền Ngoại Tệ", payment.get("Số Tệ (CNY)"))),
                    "reported_rate": _number(payment.get("Tỷ giá Báo Khách")),
                    "actual_rate": _number(payment.get("Tỷ giá Thực Tế")),
                    "note": payment.get("Ghi chú") or "",
                }
            )
        result.append(
            {
                "type": "entrustment",
                "label": "Nhận hộ / trả hộ / ví ủy thác",
                "id": record.get("id"),
                "link_kind": kind,
                "link_id": record.get("linked_id") or record.get("contract_id") or shipment_id,
                "linked_type": record.get("linked_type"),
                "deposits": deposits,
                "payment_legs": payment_legs,
                "source": "entrustments",
                "settlement_status": UNKNOWN,
            }
        )
    return result


def _contract_relations(contract_ids: list[str]) -> list[dict[str, Any]]:
    return [
        {
            "type": "contract",
            "label": "Hợp đồng liên quan",
            "id": contract_id,
            "link_kind": "direct_or_legacy",
            "source": "shipment.contract_id / data.entrustment.contract_no",
        }
        for contract_id in contract_ids
    ]


def _money_map(
    shipment_id: str,
    customer: str,
    receivable: Mapping[str, Any],
    payable: Mapping[str, Any],
    relationships: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    result = [
        {
            "from": customer or "Khách hàng (chưa rõ tên)",
            "to": f"Shipment {shipment_id}",
            "nature": "phải thu",
            "amount": receivable.get("total", {}).get("value"),
            "currency": receivable.get("currency"),
            "status": receivable.get("total", {}).get("status"),
            "source": receivable.get("total", {}).get("source"),
        }
    ]
    result.append(
        {
            "from": f"Shipment {shipment_id}",
            "to": "Đại lý / bên phải trả (chưa thống nhất)",
            "nature": "phải trả",
            "amount": payable.get("total", {}).get("value"),
            "currency": payable.get("total", {}).get("currency"),
            "status": payable.get("total", {}).get("status"),
            "source": payable.get("total", {}).get("source"),
        }
    )
    for relation in relationships:
        if relation.get("type") == "contract":
            result.append(
                {
                    "from": f"Shipment {shipment_id}",
                    "to": relation.get("id"),
                    "nature": "hợp đồng liên quan",
                    "amount": None,
                    "currency": None,
                    "status": "LINKED",
                    "source": relation.get("source"),
                }
            )
        elif relation.get("type") in {"proxy_payment", "entrustment"}:
            result.append(
                {
                    "from": f"Shipment {shipment_id}",
                    "to": relation.get("beneficiary") or relation.get("label"),
                    "nature": relation.get("label"),
                    "amount": relation.get("amount_vnd"),
                    "currency": relation.get("original_currency") or "VND",
                    "status": relation.get("status") or relation.get("settlement_status") or UNKNOWN,
                    "source": relation.get("source"),
                }
            )
    return result


def build_shipment_360_summary(
    shipment: Mapping[str, Any],
    *,
    proxy_payments: Any = None,
    entrustments: Any = None,
    read_errors: Iterable[str] | None = None,
    agreements: Any = None,
    quotes: Any = None,
) -> dict[str, Any]:
    """Build a source-labelled, non-mutating Shipment 360 read model."""

    shipment_id = str(shipment.get("shipment_id") or shipment.get("id") or "").strip()
    data = _as_mapping(shipment.get("data")) or {}
    finance = _as_mapping(data.get("3.4"))
    currency = str(shipment.get("currency") or (finance or {}).get("currency") or "VND").upper()
    customer = str(shipment.get("customer") or shipment.get("client") or "").strip()
    operational_status = shipment.get("status") or (_as_mapping(data.get("0.0")) or {}).get("st") or UNKNOWN

    if finance is None:
        receivable = {
            "known": False,
            "total": _unknown("Tổng phải thu", "Shipment thiếu data.3.4", currency),
            "collected": _unknown("Đã thu", "Shipment thiếu data.3.4", currency),
            "outstanding": _unknown("Còn phải thu", "Shipment thiếu data.3.4", currency),
            "currency": currency,
            "source": None,
        }
        payments: list[dict[str, Any]] = []
        known_cost = _unknown("Chi phí/giá vốn đã biết", "Shipment thiếu data.3.4", currency)
        expected_profit = _unknown("Lợi nhuận dự kiến", "Shipment thiếu data.3.4", currency)
        summary: Mapping[str, Any] = {}
    else:
        try:
            summary = calculate_from_shipment(shipment)
        except (AttributeError, TypeError, ValueError, ArithmeticError):
            summary = {}
        if not summary:
            receivable = {
                "known": False,
                "total": _unknown("Tổng phải thu", "Không tính được từ cấu trúc finance hiện có", currency),
                "collected": _unknown("Đã thu", "Không tính được từ cấu trúc finance hiện có", currency),
                "outstanding": _unknown("Còn phải thu", "Không tính được từ cấu trúc finance hiện có", currency),
                "currency": currency,
                "source": None,
            }
        else:
            receivable = {
                "known": True,
                "total": _known("Tổng phải thu", _number_or_zero(summary.get("receivable")), _RECEIVABLE_SOURCE, currency),
                "collected": _known("Đã thu", _number_or_zero(summary.get("paid")), _RECEIVABLE_SOURCE, currency),
                "outstanding": _known("Còn phải thu", _number_or_zero(summary.get("debt")), _RECEIVABLE_SOURCE, currency),
                "currency": currency,
                "source": _RECEIVABLE_SOURCE,
            }
        payments = _payment_rows(finance, currency)
        if summary:
            known_cost = _known(
                "Chi phí/giá vốn đã biết",
                _number_or_zero(summary.get("cost")),
                _RECEIVABLE_SOURCE,
                currency,
                reason="Đây là chi phí/giá vốn theo dòng hiện có, không phải nghĩa vụ phải trả tổng thể",
            )
            expected_profit = _known(
                "Lợi nhuận dự kiến",
                _number_or_zero(summary.get("profit")),
                _RECEIVABLE_SOURCE,
                currency,
                status="ESTIMATE",
                reason="Tính từ doanh thu chưa VAT - giá vốn - hoa hồng hiện có",
            )
        else:
            known_cost = _unknown("Chi phí/giá vốn đã biết", "Không tính được từ cấu trúc finance hiện có", currency)
            expected_profit = _unknown("Lợi nhuận dự kiến", "Không tính được từ cấu trúc finance hiện có", currency)

    payable = _agency_payable(finance or {})
    tax = _tax_summary(data)
    contract_ids = _contract_ids(shipment, data)
    relationships = _contract_relations(contract_ids)
    relationships.extend(_proxy_relations(shipment_id, contract_ids, proxy_payments))
    relationships.extend(_entrustment_relations(shipment_id, contract_ids, entrustments))

    explicit_maps = (finance or {}, shipment)
    unallocated = _explicit_metric(
        "Tiền chưa phân bổ",
        explicit_maps,
        ("unallocated_amount", "unallocated", "unallocated_payment"),
        "Chưa có allocation source thống nhất",
        currency,
    )
    unreconciled = _explicit_metric(
        "Khoản chưa đối soát",
        explicit_maps,
        ("unreconciled_amount", "unreconciled", "unreconciled_total"),
        "Chưa có read model đối soát thống nhất",
        currency,
    )
    unconfirmed_costs = _explicit_metric(
        "Chi phí chưa xác nhận",
        explicit_maps,
        ("unconfirmed_costs", "pending_costs", "unknown_costs"),
        "Chưa có nguồn chi phí chờ xác nhận thống nhất",
        currency,
    )
    actual_profit = _explicit_metric(
        "Lợi nhuận thực tế",
        explicit_maps,
        ("actual_profit",),
        "Chưa có settlement/evidence source cho lợi nhuận thực tế",
        currency,
    )
    evidence = _unknown("Chứng từ/evidence đầy đủ", "Chưa có trạng thái completeness được chuẩn hóa", None)

    outstanding_receivable = receivable["outstanding"].get("value") if receivable.get("known") else None
    outstanding_payable = payable.get("outstanding", {}).get("value") if payable.get("known") else None
    if outstanding_receivable is None:
        financial_status = UNKNOWN
    elif outstanding_receivable > 0:
        financial_status = "CHỜ THU"
    elif outstanding_payable is not None and outstanding_payable > 0:
        financial_status = "CHỜ TRẢ"
    elif receivable["total"].get("value", 0) > 0:
        financial_status = "ĐÃ THU ĐỦ PHẢI THU — CHỜ ĐỐI SOÁT"
    elif outstanding_payable is not None:
        financial_status = "CHƯA PHÁT SINH PHẢI THU — CHỜ ĐỐI SOÁT"
    else:
        financial_status = "CHƯA PHÁT SINH / CHƯA ĐỦ DỮ LIỆU"

    attention: list[dict[str, Any]] = []
    if outstanding_receivable is not None and outstanding_receivable > 0:
        attention.append({"severity": "high", "label": "Khách hàng còn phải trả", "source": receivable["outstanding"].get("source")})
    if outstanding_payable is not None and outstanding_payable > 0:
        attention.append({"severity": "high", "label": "Còn phải trả đại lý theo nguồn agency", "source": payable.get("source")})
    if not payable.get("known"):
        attention.append({"severity": "info", "label": "Chưa có nguồn công nợ phải trả tổng thể", "source": payable.get("source")})
    for metric in (unallocated, unreconciled, unconfirmed_costs, evidence, actual_profit):
        if metric.get("status") == UNKNOWN:
            attention.append({"severity": "info", "label": metric.get("label"), "source": metric.get("reason")})
    if read_errors:
        for error in read_errors:
            attention.append({"severity": "warning", "label": "Không đọc được liên kết phụ", "source": error})

    sources = [
        {"label": receivable["total"]["label"], "status": receivable["total"]["status"], "source": receivable["total"].get("source") or receivable.get("source"), "reason": receivable["total"].get("reason")},
        {"label": payable["total"]["label"], "status": payable["total"]["status"], "source": payable["total"].get("source") or payable.get("source"), "reason": payable["total"].get("reason")},
        {"label": known_cost["label"], "status": known_cost["status"], "source": known_cost.get("source"), "reason": known_cost.get("reason")},
        {"label": tax["label"], "status": tax["status"], "source": tax.get("source"), "reason": tax.get("reason")},
        {"label": unallocated["label"], "status": unallocated["status"], "source": unallocated.get("source"), "reason": unallocated.get("reason")},
        {"label": unreconciled["label"], "status": unreconciled["status"], "source": unreconciled.get("source"), "reason": unreconciled.get("reason")},
        {"label": evidence["label"], "status": evidence["status"], "source": evidence.get("source"), "reason": evidence.get("reason")},
    ]
    money_map = _money_map(shipment_id, customer, receivable, payable, relationships)

    # LOG-C13: commercial context is read-only; no ledger mutation.
    commercial = _commercial_context(shipment_id, customer, agreements, quotes)

    return {
        "shipment_id": shipment_id,
        "customer": customer,
        "currency": currency,
        "commercial": commercial,
        "operational_status": operational_status,
        "financial_status": financial_status,
        "closure_status": "CHƯA THỂ TẤT TOÁN — CHƯA ĐỦ DỮ LIỆU ĐỐI SOÁT",
        "receivable": receivable,
        "payable": payable,
        "known_cost": known_cost,
        "tax": tax,
        "expected_profit": expected_profit,
        "actual_profit": actual_profit,
        "unallocated": unallocated,
        "unreconciled": unreconciled,
        "unconfirmed_costs": unconfirmed_costs,
        "evidence": evidence,
        "payments": payments,
        "relationships": relationships,
        "money_map": money_map,
        "attention": attention,
        "sources": sources,
        "read_only": True,
    }
