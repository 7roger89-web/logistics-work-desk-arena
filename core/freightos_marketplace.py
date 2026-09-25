"""Public Freightos marketplace estimate adapter for Cost Intelligence.

Live canary (Issue #115): CNNGB → VNHPH is covered by the public GET
marketplace calculator WITHOUT ``estimate=true``. The super-fast estimator
flag returns ``numQuotes=0`` on that lane and must not be sent.

This module never persists. It never talks to paid Freightos data APIs.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable, Mapping

FREIGHTOS_CALCULATOR_URL = "https://ship.freightos.com/api/shippingCalculator"
FREIGHTOS_ATTRIBUTION_URL = "https://ship.freightos.com"
FREIGHTOS_PROVIDER = "FREIGHTOS_PUBLIC"
DEFAULT_TIMEOUT_SECONDS = 12.0
DEFAULT_QUANTITY = 1

STATUS_AVAILABLE = "AVAILABLE"
STATUS_NO_COVERAGE = "NO_COVERAGE"
STATUS_PROVIDER_ERROR = "PROVIDER_ERROR"

# Existing Cost Intelligence equipment aliases → Freightos marketplace loadtype.
# 40HQ/40HC use container40HC. container40 is only for genuine 40' GP semantics.
_LOAD_TYPE_BY_EQUIPMENT = {
    "20GP": "container20",
    "20": "container20",
    "20FT": "container20",
    "40HQ": "container40HC",
    "40HC": "container40HC",
    "40GP": "container40",
    "40": "container40",
    "40FT": "container40",
}

RequestFn = Callable[..., Any]


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _fold_equipment(value: Any) -> str:
    return "".join(ch for ch in _clean(value).upper() if ch.isalnum())


def is_unlocode(value: Any) -> bool:
    code = _clean(value).upper()
    return len(code) == 5 and code.isalpha()


def map_load_type(equipment: Any) -> str | None:
    return _LOAD_TYPE_BY_EQUIPMENT.get(_fold_equipment(equipment))


def _as_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def _as_number(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        number = float(str(value).strip())
    except (TypeError, ValueError):
        return None
    if number != number:  # NaN
        return None
    return number


def _money(node: Any) -> tuple[float | None, str]:
    if not isinstance(node, Mapping):
        return None, ""
    money = node.get("moneyAmount")
    if not isinstance(money, Mapping):
        money = node
    amount = _as_number(money.get("amount") if isinstance(money, Mapping) else None)
    currency = _clean((money or {}).get("currency")).upper() if isinstance(money, Mapping) else ""
    return amount, currency


def _now_iso(clock: Callable[[], datetime] | None = None) -> str:
    now = clock() if clock else datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    return now.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _base(
    *,
    origin: str,
    destination: str,
    equipment: str,
    load_type: str,
    status: str,
    fetched_at: str,
    message: str = "",
) -> dict[str, Any]:
    return {
        "provider": FREIGHTOS_PROVIDER,
        "providerUrl": FREIGHTOS_ATTRIBUTION_URL,
        "attribution": "Freightos",
        "fetchedAt": fetched_at,
        "origin": origin,
        "destination": destination,
        "equipment": equipment,
        "loadType": load_type,
        "status": status,
        "message": message,
    }


def marketplace_params(origin: str, destination: str, load_type: str) -> dict[str, Any]:
    """Exact public GET used by the live canary. Never includes estimate=true."""
    return {
        "loadtype": load_type,
        "origin": origin,
        "destination": destination,
        "quantity": DEFAULT_QUANTITY,
        "format": "json",
    }


def _default_request(url: str, **kwargs: Any) -> Any:
    import requests

    return requests.get(url, **kwargs)


def normalize_marketplace_response(
    payload: Any,
    *,
    origin: str,
    destination: str,
    equipment: str,
    load_type: str,
    fetched_at: str,
) -> dict[str, Any]:
    """Copy only fields the provider actually returned. Never invent prices."""
    base = _base(
        origin=origin,
        destination=destination,
        equipment=equipment,
        load_type=load_type,
        status=STATUS_NO_COVERAGE,
        fetched_at=fetched_at,
        message="Freightos chưa có báo giá công khai cho tuyến/thiết bị này.",
    )
    root = payload.get("response") if isinstance(payload, Mapping) else None
    if not isinstance(root, Mapping):
        root = payload if isinstance(payload, Mapping) else {}
    if not isinstance(root, Mapping):
        return base

    errors = root.get("errors")
    if errors:
        base["providerWarning"] = _clean(errors) if not isinstance(errors, (list, tuple)) else _clean(" ".join(str(x) for x in errors))

    rates = root.get("estimatedFreightRates")
    if not isinstance(rates, Mapping):
        return base
    num_quotes = _as_int(rates.get("numQuotes"))
    if num_quotes is not None:
        base["numQuotes"] = num_quotes
    if not num_quotes:
        return base

    mode_block = rates.get("mode")
    if isinstance(mode_block, list):
        mode_block = next((item for item in mode_block if isinstance(item, Mapping)), None)
    if not isinstance(mode_block, Mapping):
        return base

    mode_name = _clean(mode_block.get("mode"))
    if mode_name:
        base["mode"] = mode_name

    price = mode_block.get("price") if isinstance(mode_block.get("price"), Mapping) else {}
    min_amount, min_ccy = _money(price.get("min") if isinstance(price, Mapping) else None)
    max_amount, max_ccy = _money(price.get("max") if isinstance(price, Mapping) else None)
    currency = min_ccy or max_ccy
    if currency:
        base["currency"] = currency
    if min_amount is not None:
        base["minAmount"] = min_amount
    if max_amount is not None:
        base["maxAmount"] = max_amount

    transit = mode_block.get("transitTimes") if isinstance(mode_block.get("transitTimes"), Mapping) else {}
    if isinstance(transit, Mapping):
        t_min = _as_int(transit.get("min"))
        t_max = _as_int(transit.get("max"))
        t_unit = _clean(transit.get("unit"))
        if t_min is not None:
            base["transitMin"] = t_min
        if t_max is not None:
            base["transitMax"] = t_max
        if t_unit:
            base["transitUnit"] = t_unit

    if min_amount is None and max_amount is None:
        return base

    base["status"] = STATUS_AVAILABLE
    base["message"] = ""
    return base


def compare_internal(
    benchmark: Mapping[str, Any],
    *,
    amount: Any,
    currency: Any,
    load_type: str,
) -> dict[str, Any] | None:
    """Difference only when currency, equipment/load type, and a range exist."""
    if benchmark.get("status") != STATUS_AVAILABLE:
        return None
    if _clean(benchmark.get("loadType")) != _clean(load_type):
        return None
    internal_ccy = _clean(currency).upper()
    market_ccy = _clean(benchmark.get("currency")).upper()
    if not internal_ccy or internal_ccy != market_ccy:
        return None
    internal = _as_number(amount)
    min_amount = _as_number(benchmark.get("minAmount"))
    max_amount = _as_number(benchmark.get("maxAmount"))
    if internal is None or min_amount is None or max_amount is None:
        return None
    midpoint = (min_amount + max_amount) / 2.0
    return {
        "internalAmount": internal,
        "internalCurrency": internal_ccy,
        "midpoint": midpoint,
        "difference": internal - midpoint,
        "label": "so với trung điểm khoảng Freightos — không cùng hãng/phụ phí",
    }


def fetch_public_estimate(
    *,
    origin: str,
    destination: str,
    equipment: str,
    load_type: str | None = None,
    request_fn: RequestFn | None = None,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    clock: Callable[[], datetime] | None = None,
) -> dict[str, Any]:
    fetched_at = _now_iso(clock)
    origin_code = _clean(origin).upper()
    dest_code = _clean(destination).upper()
    mapped = load_type or map_load_type(equipment)
    if not is_unlocode(origin_code) or not is_unlocode(dest_code) or not mapped:
        return _base(
            origin=origin_code,
            destination=dest_code,
            equipment=_clean(equipment).upper(),
            load_type=mapped or "",
            status=STATUS_PROVIDER_ERROR,
            fetched_at=fetched_at,
            message="Thiếu UN/LOCODE hoặc loại container chưa map được sang Freightos.",
        )

    params = marketplace_params(origin_code, dest_code, mapped)
    headers = {"Accept": "application/json"}
    fn = request_fn or _default_request
    try:
        response = fn(
            FREIGHTOS_CALCULATOR_URL,
            params=params,
            timeout=timeout,
            headers=headers,
        )
    except Exception as exc:  # noqa: BLE001 - fail-soft; never block Cost Intelligence
        return _base(
            origin=origin_code,
            destination=dest_code,
            equipment=_clean(equipment).upper(),
            load_type=mapped,
            status=STATUS_PROVIDER_ERROR,
            fetched_at=fetched_at,
            message="Không lấy được tham khảo thị trường lúc này. Kho giá vốn vẫn dùng bình thường.",
            # exception type only; no body dump
        ) | {"errorClass": type(exc).__name__}

    status_code = getattr(response, "status_code", None)
    if not isinstance(status_code, int) or status_code >= 400 or status_code < 200:
        return _base(
            origin=origin_code,
            destination=dest_code,
            equipment=_clean(equipment).upper(),
            load_type=mapped,
            status=STATUS_PROVIDER_ERROR,
            fetched_at=fetched_at,
            message="Không lấy được tham khảo thị trường lúc này. Kho giá vốn vẫn dùng bình thường.",
        ) | {"httpStatus": status_code}

    try:
        payload = response.json()
    except Exception:  # noqa: BLE001 - invalid body is a provider error, not coverage
        return _base(
            origin=origin_code,
            destination=dest_code,
            equipment=_clean(equipment).upper(),
            load_type=mapped,
            status=STATUS_PROVIDER_ERROR,
            fetched_at=fetched_at,
            message="Không lấy được tham khảo thị trường lúc này. Kho giá vốn vẫn dùng bình thường.",
        ) | {"httpStatus": status_code}

    result = normalize_marketplace_response(
        payload,
        origin=origin_code,
        destination=dest_code,
        equipment=_clean(equipment).upper(),
        load_type=mapped,
        fetched_at=fetched_at,
    )
    result["httpStatus"] = status_code
    return result
