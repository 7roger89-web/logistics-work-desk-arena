from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
import re
import unicodedata
from typing import Any, Iterable, Mapping
from uuid import uuid4

PARSER_VERSION = "cost-rate-parser/1"
RATE_RECORD_TYPE = "SUPPLIER_RATE_SNAPSHOT"
CATALOG_KINDS = frozenset({"SERVICE", "CARRIER", "PLACE", "ZONE", "UNIT", "EQUIPMENT"})
RATE_STATUSES = frozenset({"ACTIVE", "SUPERSEDED", "EXPIRED", "WITHDRAWN"})

_KNOWN_CARRIERS = (
    "MAERSK", "MSK", "MSC", "COSCO", "OOCL", "MCC", "SITC", "SNL", "CMA CGM",
    "EVERGREEN", "ONE", "HAPAG-LLOYD", "WAN HAI",
)
_PLACE_ALIASES = {
    "HPH": "HAI PHONG",
    "HAIPHONG": "HAI PHONG",
    "HAI PHONG": "HAI PHONG",
    "NINGBO": "NINGBO",
    "SHENZHEN": "SHENZHEN",
    "NANSHA": "NANSHA",
}
_EQUIPMENT_ALIASES = {
    "20GP": "20GP", "20'": "20GP", "20’": "20GP", "20FT": "20GP",
    "40GP": "40GP", "40'": "40", "40’": "40", "40FT": "40",
    "40HQ": "40HQ", "40HC": "40HQ",
}
_UNIT_ALIASES = {
    "SET": "SET", "BL": "BL", "B/L": "BL", "BILL": "BILL", "RT": "RT",
    "CONT": "CONT", "CONTAINER": "CONT", "CBM": "CBM", "M3": "CBM",
}


def _clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def _fold(value: Any) -> str:
    text = unicodedata.normalize("NFD", _clean(value))
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = text.upper().replace("Đ", "D")
    return re.sub(r"[^A-Z0-9\u4e00-\u9fff]+", " ", text).strip()


def _decimal(value: Any) -> Decimal | None:
    try:
        raw = str(value or "").replace(",", "").strip()
        return Decimal(raw) if raw else None
    except (InvalidOperation, ValueError):
        return None


def _iso_date(value: str, *, year_hint: int | None = None) -> tuple[str, bool]:
    raw = _clean(value)
    if not raw:
        return "", False
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%m.%d.%Y"):
        try:
            return datetime.strptime(raw, fmt).date().isoformat(), False
        except ValueError:
            pass
    for fmt in ("%d/%m", "%d-%m", "%m.%d"):
        try:
            parsed = datetime.strptime(raw, fmt).date()
            year = year_hint or date.today().year
            return parsed.replace(year=year).isoformat(), True
        except ValueError:
            pass
    return "", False


def _catalog_entries(catalog: Mapping[str, Any] | Iterable[Mapping[str, Any]] | None) -> list[dict[str, Any]]:
    if catalog is None:
        return []
    values = catalog.values() if isinstance(catalog, Mapping) else catalog
    return [dict(x) for x in values if isinstance(x, Mapping) and x.get("active", True) is not False]


def _alias_maps(catalog: Mapping[str, Any] | Iterable[Mapping[str, Any]] | None) -> dict[str, dict[str, dict[str, Any]]]:
    maps = {kind: {} for kind in CATALOG_KINDS}
    for entry in _catalog_entries(catalog):
        kind = _clean(entry.get("kind")).upper()
        if kind not in maps:
            continue
        names = [
            entry.get("code"), entry.get("name"), *(entry.get("aliases") or []),
            *((entry.get("legacy_codes") or entry.get("legacyCodes") or []) if kind == "SERVICE" else []),
        ]
        for name in names:
            folded = _fold(name)
            if folded:
                maps[kind][folded] = entry
    return maps


def _canonical_place(raw: str, aliases: Mapping[str, dict[str, Any]]) -> dict[str, Any]:
    folded = _fold(raw)
    hit = aliases.get(folded)
    if hit:
        return {
            "raw": _clean(raw),
            "id": _clean(hit.get("id")),
            "name": _clean(hit.get("name") or hit.get("code")),
            "zoneIds": list(hit.get("zone_ids") or hit.get("zoneIds") or []),
            "state": "CONFIRMED",
        }
    fallback = _PLACE_ALIASES.get(folded)
    return {
        "raw": _clean(raw),
        "id": "",
        "name": fallback or _clean(raw),
        "zoneIds": [],
        "state": "CONFIRMED" if fallback else "NEEDS_REVIEW",
    }


def _carrier_hits(line: str, aliases: Mapping[str, dict[str, Any]]) -> list[dict[str, Any]]:
    folded = _fold(line)
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for alias, entry in aliases.items():
        if alias and re.search(rf"(?:^|\s){re.escape(alias)}(?:$|\s)", folded):
            key = _clean(entry.get("id") or entry.get("code") or entry.get("name"))
            if key not in seen:
                seen.add(key)
                out.append({
                    "id": _clean(entry.get("id")),
                    "name": _clean(entry.get("name") or entry.get("code")),
                    "state": "CONFIRMED",
                })
    for carrier in _KNOWN_CARRIERS:
        if re.search(rf"(?:^|\s){re.escape(_fold(carrier))}(?:$|\s)", folded) and carrier not in seen:
            seen.add(carrier)
            out.append({"id": "", "name": carrier, "state": "CONFIRMED"})
    return out


def _canonical_service(raw: str, aliases: Mapping[str, dict[str, Any]]) -> dict[str, str]:
    folded = _fold(raw)
    if not folded:
        return {"raw": "", "id": "", "name": ""}
    hit = aliases.get(folded)
    if hit is None:
        # Prefer the longest matching alias to avoid a short code stealing a
        # more specific phrase. This is deterministic and catalog-driven.
        candidates = [
            (alias, entry)
            for alias, entry in aliases.items()
            if alias and re.search(rf"(?:^|\s){re.escape(alias)}(?:$|\s)", folded)
        ]
        if candidates:
            _, hit = max(candidates, key=lambda item: len(item[0]))
    if hit is None:
        return {"raw": _clean(raw), "id": "", "name": _clean(raw)}
    return {
        "raw": _clean(raw),
        "id": _clean(hit.get("id")),
        "name": _clean(hit.get("name") or hit.get("code")) or _clean(raw),
    }


def _route_from_line(line: str, place_aliases: Mapping[str, dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any]] | None:
    if re.search(r"(?:USD|CNY|RMB|\$|\d\s*/\s*(?:20|40|SET|BL|RT|CONT))", line, re.I):
        return None
    cleaned = re.sub(r"(?i)^\s*(?:CƯỚC\s+BIỂN|CUOC\s+BIEN|ROUTE)\s*[:：]?\s*", "", line).strip()
    m = re.search(r"^\s*([^–—-]{2,40}?)\s*[–—-]\s*([^–—-]{2,40}?)\s*$", cleaned)
    if not m:
        return None
    left, right = _clean(m.group(1)), _clean(m.group(2))
    right = re.sub(r"\s+\d{1,2}[./-]\d{1,2}(?:[./-]\d{2,4})?\s*$", "", right).strip()
    if len(left) > 36 or len(right) > 36:
        return None
    return _canonical_place(left, place_aliases), _canonical_place(right, place_aliases)


def _charge_label(line: str) -> str:
    m = re.search(
        r"(?i)(?:(?:USD|CNY|RMB|VND|\$)\s*/?\s*)?\d[\d,]*(?:\.\d+)?\s*\$?\s*/\s*[A-Z0-9/'’]+",
        line,
    )
    prefix = line[: m.start()] if m else line
    prefix = re.sub(r"[:：;\s]+$", "", prefix).strip()
    return prefix or "RATE"


def _unit_identity(
    raw_unit: str,
    equipment_aliases: Mapping[str, dict[str, Any]],
    unit_aliases: Mapping[str, dict[str, Any]],
) -> tuple[str, str, str]:
    """Return (unit, equipment, equipment_state); empty tuple values = unknown token."""
    raw = raw_unit.upper().replace("’", "'")
    folded = _fold(raw)

    equipment_hit = equipment_aliases.get(folded)
    if equipment_hit:
        equipment = _clean(equipment_hit.get("code") or equipment_hit.get("name")).upper()
        return "CONT", equipment, "CONFIRMED"

    unit_hit = unit_aliases.get(folded)
    if unit_hit:
        unit = _clean(unit_hit.get("code") or unit_hit.get("name")).upper()
        return unit, "", "UNKNOWN"

    equipment = _EQUIPMENT_ALIASES.get(raw, "")
    if equipment:
        return "CONT", equipment, "NEEDS_REVIEW" if equipment == "40" else "CONFIRMED"

    unit = _UNIT_ALIASES.get(raw, "")
    if unit:
        return unit, "", "UNKNOWN"
    return "", "", "UNKNOWN"


def _money_matches(
    line: str,
    *,
    equipment_aliases: Mapping[str, dict[str, Any]] | None = None,
    unit_aliases: Mapping[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    normalized = line.replace("’", "'").replace("：", ":")
    equipment_aliases = equipment_aliases or {}
    unit_aliases = unit_aliases or {}
    token = r"[A-Z0-9/'-]{1,24}"
    amount = r"\d[\d,]*(?:\.\d+)?"
    patterns = [
        re.compile(rf"(?P<currency>USD|CNY|RMB|VND|\$)\s*/?\s*(?P<amount>{amount})\s*/\s*(?P<unit>{token})(?![A-Z0-9])", re.I),
        re.compile(rf"(?P<amount>{amount})\s*(?P<currency>\$)\s*/\s*(?P<unit>{token})(?![A-Z0-9])", re.I),
    ]
    found: list[tuple[int, int, dict[str, Any]]] = []
    for pattern in patterns:
        for m in pattern.finditer(normalized):
            raw_unit = m.group("unit")
            unit, equipment, equipment_state = _unit_identity(raw_unit, equipment_aliases, unit_aliases)
            if not unit and not equipment:
                continue
            currency = m.groupdict().get("currency") or ""
            currency = "USD" if currency == "$" else ("CNY" if currency.upper() == "RMB" else currency.upper())
            found.append((m.start(), m.end(), {
                "amount": float(Decimal(m.group("amount").replace(",", ""))),
                "currency": currency or "USD",
                "unit": unit,
                "equipment": equipment,
                "equipmentState": equipment_state,
                "rawPrice": m.group(0),
            }))
    occupied = [(a, b) for a, b, _ in found]
    inherited_currency = next((x[2]["currency"] for x in sorted(found) if x[2].get("currency")), "")
    implicit = re.compile(rf"(?<![\d.])(?P<amount>{amount})\s*/\s*(?P<unit>{token})(?![A-Z0-9])", re.I)
    for m in implicit.finditer(normalized):
        if any(not (m.end() <= a or m.start() >= b) for a, b in occupied):
            continue
        unit, equipment, equipment_state = _unit_identity(m.group("unit"), equipment_aliases, unit_aliases)
        if not unit and not equipment:
            continue
        found.append((m.start(), m.end(), {
            "amount": float(Decimal(m.group("amount").replace(",", ""))),
            "currency": inherited_currency or "USD",
            "unit": unit,
            "equipment": equipment,
            "equipmentState": equipment_state,
            "rawPrice": m.group(0),
            "currencyState": "INFERRED_FROM_LINE" if inherited_currency else "NEEDS_REVIEW",
        }))
    found.sort(key=lambda x: x[0])
    return [x[2] for x in found]


def _section_source_dates(lines: list[str], *, year_hint: int) -> dict[int, str]:
    """Map each raw line index to the explicit standalone date in its --- section.

    A pasted inbox may contain several historical messages from different dates.
    The date belongs to that bounded section, never to the entire paste.
    """
    out: dict[int, str] = {}
    section: list[int] = []

    def flush() -> None:
        if not section:
            return
        dates: list[str] = []
        for idx in section:
            raw = _clean(lines[idx])
            if not re.fullmatch(r"(?:\d{1,2}[./-]\d{1,2}[./-]\d{4}|\d{4}-\d{2}-\d{2})", raw):
                continue
            parsed, _ = _iso_date(raw, year_hint=year_hint)
            if parsed:
                dates.append(parsed)
        # Multiple explicit dates in one section are ambiguous; do not guess.
        source_date = dates[0] if len(set(dates)) == 1 else ""
        if source_date:
            for idx in section:
                out[idx] = source_date
        section.clear()

    for idx, raw in enumerate(lines):
        if re.fullmatch(r"[-_]{3,}", _clean(raw)):
            flush()
            continue
        section.append(idx)
    flush()
    return out


def parse_cost_rate_text(
    raw_text: str,
    *,
    catalog: Mapping[str, Any] | Iterable[Mapping[str, Any]] | None = None,
    received_on: date | None = None,
) -> dict[str, Any]:
    text = str(raw_text or "").strip()
    if not text:
        raise ValueError("Chưa có nội dung giá đầu vào để phân tích.")
    aliases = _alias_maps(catalog)
    year_hint = (received_on or date.today()).year
    raw_lines = text.splitlines()
    section_dates = _section_source_dates(raw_lines, year_hint=year_hint)
    origin = {"raw": "", "id": "", "name": "", "zoneIds": [], "state": "UNKNOWN"}
    destination = dict(origin)
    current_carrier: dict[str, Any] | None = None
    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    validity_context = ""

    for line_index, raw_line in enumerate(raw_lines):
        line = _clean(raw_line)
        if not line:
            continue
        standalone_date, _ = _iso_date(line, year_hint=year_hint)
        if standalone_date and re.fullmatch(r"(?:\d{1,2}[./-]\d{1,2}[./-]\d{4}|\d{4}-\d{2}-\d{2})", line):
            continue
        if re.fullmatch(r"[-_]{3,}", line):
            current_carrier = None
            validity_context = ""
            continue
        route = _route_from_line(line, aliases["PLACE"])
        if route:
            origin, destination = route
            continue
        carriers = _carrier_hits(line, aliases["CARRIER"])
        if "没仓位" in line:
            # A carrier named on THIS line is authoritative for the no-space
            # fact. Do not turn that into sticky context for later charge lines.
            carrier = carriers[0] if carriers else current_carrier
            carrier = carrier or {
                "id": "",
                "name": _clean(line.replace("没仓位", "")),
                "state": "NEEDS_REVIEW",
            }
            rows.append({
                "id": f"line-{len(rows)+1}",
                "kind": "AVAILABILITY",
                "status": "NO_SPACE",
                "carrier": carrier,
                "origin": origin,
                "destination": destination,
                "rawLine": raw_line,
                "confidence": "NEEDS_REVIEW" if carrier.get("state") == "NEEDS_REVIEW" else "CONFIRMED",
            })
            continue
        vm = re.search(r"有效期到\s*([0-9./-]+)", line)
        line_validity_raw = vm.group(1) if vm else ""
        etd_m = re.search(r"(?i)ETD\s*[:：]?\s*([0-9./-]+)", line)
        etd_iso, etd_inferred = _iso_date(etd_m.group(1), year_hint=year_hint) if etd_m else ("", False)
        prices = _money_matches(
            line,
            equipment_aliases=aliases["EQUIPMENT"],
            unit_aliases=aliases["UNIT"],
        )
        if not prices:
            if line_validity_raw:
                validity_context = line_validity_raw
            # Only a carrier mentioned on a NON-PRICE line becomes context.
            # Examples: a standalone "OOCL" heading or vessel/header line.
            # A priced line such as "... MSK" applies MSK to that row only and
            # must not leak into following LOCAL/DOC/THC rows.
            if carriers:
                current_carrier = carriers[0]
            continue
        line_carrier = carriers[0] if carriers else current_carrier
        raw_label = _charge_label(line)
        if prices and any(price.get("equipment") for price in prices):
            carrier_labels = {_fold(x.get("name")) for x in carriers if x.get("name")}
            if raw_label == "RATE" or _fold(raw_label) in carrier_labels:
                raw_label = "O/F"
        service = _canonical_service(raw_label, aliases["SERVICE"])
        label = service["name"] or raw_label
        upper = _fold(raw_label)
        semantic = "CREDIT" if "REFUND" in upper or "REBATE" in upper else "CHARGE"
        plus_tax = bool(re.search(r"(?i)\+\s*TAX|PLUS\s+TAX", line))
        effective_validity_raw = line_validity_raw or validity_context
        valid_until, valid_year_inferred = (
            _iso_date(effective_validity_raw, year_hint=year_hint)
            if effective_validity_raw else ("", False)
        )
        section_source_date = section_dates.get(line_index, "")
        for price in prices:
            confidence = "CONFIRMED"
            if price.get("equipmentState") == "NEEDS_REVIEW" or price.get("currencyState") == "NEEDS_REVIEW":
                confidence = "NEEDS_REVIEW"
            rows.append({
                "id": f"line-{len(rows)+1}",
                "kind": semantic,
                "status": "AVAILABLE",
                "chargeLabel": label,
                "chargeRaw": raw_label,
                "chargeId": service["id"],
                "carrier": line_carrier or {"id": "", "name": "", "state": "UNKNOWN"},
                "origin": origin,
                "destination": destination,
                "amount": price["amount"],
                "currency": price["currency"],
                "unit": price["unit"],
                "equipment": price.get("equipment", ""),
                "equipmentState": price.get("equipmentState", "UNKNOWN"),
                "taxQualifier": "PLUS_TAX" if plus_tax else "UNKNOWN",
                "etd": etd_iso,
                "etdYearInferred": etd_inferred,
                "validityRaw": effective_validity_raw,
                "validUntil": valid_until,
                "validUntilYearInferred": valid_year_inferred,
                "sourceDate": section_source_date,
                "rawLine": raw_line,
                "rawPrice": price.get("rawPrice", ""),
                "confidence": confidence,
            })
    if not rows:
        raise ValueError("Chưa bóc được dòng giá nào. Giữ nguyên nội dung và nhập/sửa thủ công thay vì đoán số.")
    unresolved = sum(
        1
        for row in rows
        if row.get("confidence") == "NEEDS_REVIEW"
        or row.get("carrier", {}).get("state") == "NEEDS_REVIEW"
        or row.get("origin", {}).get("state") == "NEEDS_REVIEW"
        or row.get("destination", {}).get("state") == "NEEDS_REVIEW"
    )
    if unresolved:
        warnings.append(f"Có {unresolved} dòng cần người dùng xác nhận địa điểm/thiết bị trước khi dùng làm giá vốn.")
    unique_source_dates = sorted({value for value in section_dates.values() if value})
    return {
        "parserVersion": PARSER_VERSION,
        "rawText": text,
        # Only auto-fill the overall source date when the pasted inbox has one
        # unambiguous standalone date. Mixed historical sections keep their own
        # row.sourceDate and leave this blank for the operator.
        "sourceDate": unique_source_dates[0] if len(unique_source_dates) == 1 else "",
        "rows": rows,
        "warnings": warnings,
        "summary": {
            "rowCount": len(rows),
            "needsReview": unresolved,
            "noSpace": sum(1 for row in rows if row.get("status") == "NO_SPACE"),
        },
    }


def catalog_lookup_keys(entry: Mapping[str, Any]) -> set[str]:
    """Canonical lookup keys used by both parser aliases and writer validation."""
    values = [
        entry.get("code"),
        entry.get("name"),
        entry.get("unlocode"),
        *(entry.get("aliases") or []),
        *(entry.get("legacy_codes") or entry.get("legacyCodes") or []),
    ]
    return {key for key in (_fold(value) for value in values) if key}


def normalize_catalog_entry(payload: Mapping[str, Any]) -> dict[str, Any]:
    kind = _clean(payload.get("kind")).upper()
    if kind not in CATALOG_KINDS:
        raise ValueError("Loại danh mục không được hỗ trợ.")
    identifier = _clean(payload.get("id")) or f"CAT-{uuid4().hex[:12].upper()}"
    name = _clean(payload.get("name"))
    code = _clean(payload.get("code")).upper()
    if not name and not code:
        raise ValueError("Danh mục cần tên hoặc mã.")
    aliases: list[str] = []
    seen: set[str] = set()
    for value in payload.get("aliases") or []:
        clean = _clean(value)
        folded = _fold(clean)
        if clean and folded not in seen:
            seen.add(folded)
            aliases.append(clean)
    out = {
        "id": identifier,
        "kind": kind,
        "code": code,
        "name": name or code,
        "aliases": aliases,
        "active": payload.get("active", True) is not False,
        "merged_into": _clean(payload.get("mergedInto") or payload.get("merged_into")),
    }
    if kind == "SERVICE":
        out.update({
            "unit": _clean(payload.get("unit")) or "Lần",
            "group": _clean(payload.get("group")) or "DỊCH VỤ XNK",
            "legacy_codes": [
                _clean(x).upper() for x in (payload.get("legacyCodes") or payload.get("legacy_codes") or [])
                if _clean(x)
            ],
        })
    if kind == "PLACE":
        out.update({
            "country": _clean(payload.get("country")).upper(),
            "unlocode": _clean(payload.get("unlocode")).upper(),
            "lat": payload.get("lat"),
            "lon": payload.get("lon"),
            "zone_ids": [str(x) for x in (payload.get("zoneIds") or payload.get("zone_ids") or []) if str(x).strip()],
        })
    return out


def json_safe(value: Any) -> Any:
    """Normalise stored documents into JSON-serialisable view-model data.

    Mongo/audit stamps (``created_at`` / ``updated_at`` /
    ``status_updated_at``) are ``datetime`` objects. The Streamlit component
    transports its args as JSON: one raw ``datetime`` inside the Cost
    Intelligence slice silently breaks arg delivery for every NEW browser
    session (the app then waits on "Đang tải dữ liệu vận hành…" forever).
    Convert at this boundary so operator saves can never poison the shell.
    """
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Mapping):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    return value


def prepare_rate_snapshot(payload: Mapping[str, Any], *, actor: str = "") -> dict[str, Any]:
    parsed = payload.get("parsed") if isinstance(payload.get("parsed"), Mapping) else payload
    raw_text = str(parsed.get("rawText") or "").strip()
    rows = parsed.get("rows") if isinstance(parsed.get("rows"), list) else []
    if not raw_text or not rows:
        raise ValueError("Snapshot cần raw text và ít nhất một dòng đã review.")
    unresolved = [
        row for row in rows
        if isinstance(row, Mapping) and (
            row.get("confidence") == "NEEDS_REVIEW"
            or (isinstance(row.get("carrier"), Mapping) and row["carrier"].get("state") == "NEEDS_REVIEW")
            or (isinstance(row.get("origin"), Mapping) and row["origin"].get("state") == "NEEDS_REVIEW")
            or (isinstance(row.get("destination"), Mapping) and row["destination"].get("state") == "NEEDS_REVIEW")
            or row.get("equipmentState") == "NEEDS_REVIEW"
        )
    ]
    if unresolved:
        raise ValueError(f"Còn {len(unresolved)} dòng cần xác nhận trước khi lưu giá vốn.")
    request_id = _clean(payload.get("requestId") or payload.get("request_id"))
    identifier = _clean(payload.get("id")) or request_id or f"RATE-{uuid4().hex[:12].upper()}"
    source_date = _clean(parsed.get("sourceDate"))
    received_at = (
        _clean(payload.get("receivedAt"))
        or (f"{source_date}T00:00:00Z" if source_date else "")
        or datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    )
    status = _clean(payload.get("status") or "ACTIVE").upper()
    if status not in RATE_STATUSES:
        raise ValueError("Trạng thái rate snapshot không hợp lệ.")
    return {
        "id": identifier,
        "record_type": RATE_RECORD_TYPE,
        "status": status,
        "received_at": received_at,
        "supplier": _clean(payload.get("supplier")),
        "source_channel": _clean(payload.get("sourceChannel") or "PASTE"),
        "raw_text": raw_text,
        "parser_version": _clean(parsed.get("parserVersion")) or PARSER_VERSION,
        "rows": rows,
        "warnings": list(parsed.get("warnings") or []),
        "created_by": actor,
        "request_id": request_id,
        "is_deleted": False,
    }
