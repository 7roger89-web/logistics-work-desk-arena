"""Canonical shipment transport legs and cargo-summary helpers.

V1 keeps operational facts inside ``data["1.2"]``:

* ``transport_legs`` is the authoritative ordered collection when the key is
  present (including an intentionally empty list);
* ``cargo_summary`` is the shipment-level cargo fact block;
* legacy scalar fields remain untouched and are used only as a read fallback
  for documents that do not yet carry the structured collection.

The module is deliberately pure.  It creates no service or storage boundary;
the existing shipment writer remains the only persistence path.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping

TRANSPORT_MODES = ("Truck", "Sea", "Air", "Rail")
_TRANSPORT_MODE_SET = frozenset(TRANSPORT_MODES)
_COMMON_LEG_TEXT_FIELDS = ("origin", "destination", "carrier")
_COMMON_LEG_DATE_FIELDS = ("etd", "eta", "atd", "ata")
_MODE_TEXT_FIELDS = {
    "Truck": (),
    "Sea": ("booking_no", "mbl", "hbl", "vessel", "voyage"),
    "Air": ("mawb", "hawb", "flight_no"),
    "Rail": (),
}
_CARGO_TEXT_FIELDS = ("goods_description", "package_type", "dimensions", "note")
_CARGO_NUMBER_FIELDS = ("package_count", "gross_weight_kg", "cbm")


def _text(value: Any, *, field: str, maximum: int = 500) -> str:
    if value is None:
        return ""
    result = str(value).strip()
    if len(result) > maximum:
        raise ValueError(f"{field} dài quá {maximum} ký tự.")
    return result


def _identifier(value: Any, *, field: str) -> str:
    result = _text(value, field=field, maximum=120)
    if not result:
        raise ValueError(f"{field} không được để trống.")
    return result


def _date_or_unknown(value: Any, *, field: str) -> str:
    if value is None or str(value).strip() == "":
        return ""
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    raw = str(value).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(raw[:10], fmt).date().isoformat()
        except ValueError:
            continue
    raise ValueError(f"{field} phải là ngày YYYY-MM-DD hoặc DD/MM/YYYY.")


def _sequence(value: Any, *, field: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{field} phải là số nguyên dương.")
    try:
        result = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} phải là số nguyên dương.") from exc
    if str(value).strip() not in {str(result), f"{result}.0"}:
        raise ValueError(f"{field} phải là số nguyên dương.")
    if result <= 0:
        raise ValueError(f"{field} phải lớn hơn 0.")
    return result


def _number_or_unknown(value: Any, *, field: str, integer: bool = False) -> int | float | None:
    if value is None or str(value).strip() == "":
        return None
    if isinstance(value, bool):
        raise ValueError(f"{field} phải là số không âm hoặc để trống.")
    raw = str(value).strip().replace(",", "")
    try:
        parsed = Decimal(raw)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field} phải là số không âm hoặc để trống.") from exc
    if not parsed.is_finite() or parsed < 0:
        raise ValueError(f"{field} phải là số không âm hoặc để trống.")
    if integer:
        if parsed != parsed.to_integral_value():
            raise ValueError(f"{field} phải là số nguyên không âm hoặc để trống.")
        return int(parsed)
    return float(parsed)


def normalize_transport_legs(value: Any) -> list[dict[str, Any]]:
    """Validate and normalize one complete V1 transport-leg collection.

    IDs and sequences are mandatory and unique.  Mode-specific facts are kept
    only for their selected mode, preventing hidden Sea facts from surviving a
    deliberate change to Air (and vice versa).  No capacity, count or route is
    inferred.
    """

    if not isinstance(value, list):
        raise ValueError("transport_legs phải là một danh sách.")

    result: list[dict[str, Any]] = []
    leg_ids: set[str] = set()
    sequences: set[int] = set()
    all_unit_ids: set[str] = set()

    for index, raw_leg in enumerate(value, start=1):
        if not isinstance(raw_leg, Mapping):
            raise ValueError(f"Chặng {index} không hợp lệ.")
        leg_id = _identifier(raw_leg.get("id"), field=f"Chặng {index}: id")
        if leg_id in leg_ids:
            raise ValueError(f"Trùng id chặng: {leg_id}.")
        leg_ids.add(leg_id)

        sequence = _sequence(raw_leg.get("sequence"), field=f"Chặng {index}: sequence")
        if sequence in sequences:
            raise ValueError(f"Trùng thứ tự chặng: {sequence}.")
        sequences.add(sequence)

        mode = _text(raw_leg.get("mode"), field=f"Chặng {index}: mode", maximum=20)
        if mode not in _TRANSPORT_MODE_SET:
            raise ValueError(f"Chặng {index}: mode phải là Truck, Sea, Air hoặc Rail.")

        leg: dict[str, Any] = {"id": leg_id, "sequence": sequence, "mode": mode}
        for key in _COMMON_LEG_TEXT_FIELDS:
            leg[key] = _text(raw_leg.get(key), field=f"Chặng {index}: {key}")
        for key in _COMMON_LEG_DATE_FIELDS:
            leg[key] = _date_or_unknown(raw_leg.get(key), field=f"Chặng {index}: {key}")
        for key in _MODE_TEXT_FIELDS[mode]:
            leg[key] = _text(raw_leg.get(key), field=f"Chặng {index}: {key}")

        raw_units = raw_leg.get("units", [])
        if raw_units is None:
            raw_units = []
        if not isinstance(raw_units, list):
            raise ValueError(f"Chặng {index}: units phải là một danh sách.")
        if mode in {"Air", "Rail"} and raw_units:
            raise ValueError(f"Chặng {index}: {mode} không nhận xe/container trong V1.")

        expected_kind = "truck" if mode == "Truck" else "container" if mode == "Sea" else None
        units: list[dict[str, Any]] = []
        for unit_index, raw_unit in enumerate(raw_units, start=1):
            if not isinstance(raw_unit, Mapping):
                raise ValueError(f"Chặng {index}, phương tiện {unit_index} không hợp lệ.")
            unit_id = _identifier(raw_unit.get("id"), field=f"Chặng {index}, phương tiện {unit_index}: id")
            if unit_id in all_unit_ids:
                raise ValueError(f"Trùng id phương tiện: {unit_id}.")
            all_unit_ids.add(unit_id)
            kind = _text(raw_unit.get("kind"), field=f"Phương tiện {unit_id}: kind", maximum=20)
            if kind != expected_kind:
                raise ValueError(f"Chặng {index}: {mode} chỉ nhận kind={expected_kind}.")

            unit: dict[str, Any] = {"id": unit_id, "kind": kind}
            # Truck cards carry driver facts; Sea cards carry seal.  Hidden
            # mode-inapplicable fields are intentionally not retained.
            allowed = ("number", "type_size", "driver_name", "driver_phone") if kind == "truck" else (
                "number", "type_size", "seal_no"
            )
            for key in allowed:
                unit[key] = _text(raw_unit.get(key), field=f"Phương tiện {unit_id}: {key}")
            units.append(unit)
        leg["units"] = units
        result.append(leg)

    return sorted(result, key=lambda row: row["sequence"])


def normalize_cargo_summary(value: Any) -> dict[str, Any]:
    """Validate shipment-level cargo summary without inventing zeroes."""

    if not isinstance(value, Mapping):
        raise ValueError("cargo_summary phải là một object.")
    result: dict[str, Any] = {}
    for key in _CARGO_TEXT_FIELDS:
        result[key] = _text(value.get(key), field=f"Hàng hóa: {key}", maximum=2000 if key == "note" else 500)
    result["package_count"] = _number_or_unknown(
        value.get("package_count"), field="Hàng hóa: package_count", integer=True
    )
    result["gross_weight_kg"] = _number_or_unknown(
        value.get("gross_weight_kg"), field="Hàng hóa: gross_weight_kg"
    )
    result["cbm"] = _number_or_unknown(value.get("cbm"), field="Hàng hóa: cbm")
    return result


def _data_section(shipment: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    data = shipment.get("data")
    if not isinstance(data, Mapping):
        return {}
    value = data.get(key)
    return value if isinstance(value, Mapping) else {}


def has_structured_transport(shipment: Mapping[str, Any]) -> bool:
    """Presence, not truthiness, selects the authoritative collection."""

    transport = _data_section(shipment, "1.2")
    return "transport_legs" in transport and isinstance(transport.get("transport_legs"), list)


def canonical_transport_legs(shipment: Mapping[str, Any]) -> list[dict[str, Any]] | None:
    """Return canonical legs, or ``None`` when legacy fallback must be used."""

    if not has_structured_transport(shipment):
        return None
    raw = _data_section(shipment, "1.2").get("transport_legs")
    return deepcopy([dict(row) for row in raw if isinstance(row, Mapping)])


def _fallback_unit(unit_id: str, kind: str, *, number: Any = "", type_size: Any = "",
                   seal_no: Any = "", driver_name: Any = "", driver_phone: Any = "") -> dict[str, Any]:
    unit = {
        "id": unit_id,
        "kind": kind,
        "number": str(number or "").strip(),
        "type_size": str(type_size or "").strip(),
    }
    if kind == "container":
        unit["seal_no"] = str(seal_no or "").strip()
    else:
        unit["driver_name"] = str(driver_name or "").strip()
        unit["driver_phone"] = str(driver_phone or "").strip()
    return unit


def legacy_transport_legs(shipment: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Lossless-enough read projection for pre-V1 scalar shipment documents.

    CN pickup and VN delivery are deliberately projected as separate legs.
    The combined legacy driver/SĐT value remains one exact ``driver_name``
    string; it is never guessed or split.
    """

    transport = _data_section(shipment, "1.2")
    delivery = _data_section(shipment, "2.7")
    arrival = _data_section(shipment, "2.6")
    head = _data_section(shipment, "0.0")
    mode = str(head.get("mode") or "").strip()
    if mode not in _TRANSPORT_MODE_SET:
        mode = "Truck"

    leg: dict[str, Any] = {
        "id": "legacy-primary-leg",
        "sequence": 1,
        "mode": mode,
        "origin": str(transport.get("pol") or "").strip(),
        "destination": str(transport.get("pod") or "").strip(),
        "carrier": str(transport.get("carrier") or "").strip(),
        "etd": str(transport.get("etd") or "").strip(),
        "eta": str(arrival.get("arrival_date") or "").strip(),
        "atd": "",
        "ata": "",
        # Existing scalar references remain visible in compatibility readers.
        # Mode-specific editors still expose only the fields relevant to the
        # selected mode.
        "booking_no": str(transport.get("booking_no") or "").strip(),
        "mbl": str(transport.get("mbl") or "").strip(),
        "hbl": str(transport.get("hbl") or "").strip(),
        "vessel": str(transport.get("vessel") or "").strip(),
        "voyage": str(transport.get("voyage") or "").strip(),
        "mawb": str(transport.get("mawb") or "").strip(),
        "hawb": str(transport.get("hawb") or "").strip(),
        "flight_no": str(transport.get("flight_no") or "").strip(),
        "units": [],
    }
    if mode == "Sea":
        for key in _MODE_TEXT_FIELDS["Sea"]:
            leg[key] = str(transport.get(key) or "").strip()
        number = transport.get("container_no")
        if number:
            leg["units"] = [_fallback_unit(
                "legacy-primary-unit", "container", number=number,
            )]
    elif mode == "Air":
        for key in _MODE_TEXT_FIELDS["Air"]:
            leg[key] = str(transport.get(key) or "").strip()
    elif mode == "Truck":
        if transport.get("container_no") or transport.get("pickup_truck_type"):
            leg["units"] = [_fallback_unit(
                "legacy-primary-unit", "truck", number=transport.get("container_no"),
                type_size=transport.get("pickup_truck_type"),
            )]

    # Keep the primary leg visible even if every scalar is blank: an old
    # shipment still opens as the mode it previously carried.  A legacy pickup
    # truck type on a non-Truck shipment is a separate pickup leg; it is never
    # mislabeled as a Sea container type.
    legs: list[dict[str, Any]] = []
    if mode != "Truck" and transport.get("pickup_truck_type"):
        legs.append({
            "id": "legacy-pickup-leg",
            "sequence": 1,
            "mode": "Truck",
            "origin": "",
            "destination": "",
            "carrier": "",
            "etd": "",
            "eta": "",
            "atd": "",
            "ata": "",
            "units": [_fallback_unit(
                "legacy-pickup-unit", "truck",
                type_size=transport.get("pickup_truck_type"),
            )],
        })
        leg["sequence"] = 2
    legs.append(leg)
    if delivery.get("truck_no") or delivery.get("seal_no"):
        legs.append({
            "id": "legacy-delivery-leg",
            "sequence": len(legs) + 1,
            "mode": "Truck",
            "origin": "",
            "destination": str(delivery.get("addr") or "").strip(),
            "carrier": "",
            "etd": str(delivery.get("delivery_date") or "").strip(),
            "eta": "",
            "atd": "",
            "ata": "",
            "units": [_fallback_unit(
                "legacy-delivery-unit", "truck", number=delivery.get("truck_no"),
                driver_name=delivery.get("seal_no"),
            )],
        })
    return legs


def transport_legs_for_read(shipment: Mapping[str, Any]) -> tuple[list[dict[str, Any]], bool]:
    canonical = canonical_transport_legs(shipment)
    if canonical is not None:
        return canonical, True
    return legacy_transport_legs(shipment), False


def cargo_summary_for_read(shipment: Mapping[str, Any]) -> tuple[dict[str, Any], bool]:
    transport = _data_section(shipment, "1.2")
    raw = transport.get("cargo_summary")
    if isinstance(raw, Mapping):
        result = {key: raw.get(key, "") for key in _CARGO_TEXT_FIELDS}
        for key in _CARGO_NUMBER_FIELDS:
            result[key] = raw.get(key)
        return result, True
    return {
        "goods_description": "",
        "package_count": None,
        "package_type": "",
        "gross_weight_kg": None,
        "cbm": None,
        "dimensions": "",
        "note": str(transport.get("qty_pkg") or "").strip(),
    }, False


def compatibility_facts(shipment: Mapping[str, Any]) -> dict[str, Any]:
    """Derive explicit primary/first display facts from canonical legs.

    No scalar compatibility field is written.  Readers that still need one
    route, one container or one plate consume this projection instead of
    becoming a second business truth.
    """

    legs, structured = transport_legs_for_read(shipment)
    ordered = sorted(legs, key=lambda row: int(row.get("sequence") or 0))
    first = ordered[0] if ordered else {}
    main = next((row for row in ordered if row.get("mode") in {"Sea", "Air"}), first)
    truck_legs = [row for row in ordered if row.get("mode") == "Truck"]
    first_truck = truck_legs[0] if truck_legs and ordered.index(truck_legs[0]) == 0 else {}
    delivery_truck = truck_legs[-1] if truck_legs and ordered.index(truck_legs[-1]) > 0 else {}
    sea_leg = next((row for row in ordered if row.get("mode") == "Sea"), {})

    def first_unit(leg: Mapping[str, Any], kind: str) -> Mapping[str, Any]:
        units = leg.get("units") if isinstance(leg.get("units"), list) else []
        return next((unit for unit in units if isinstance(unit, Mapping) and unit.get("kind") == kind), {})

    pickup_unit = first_unit(first_truck, "truck")
    delivery_unit = first_unit(delivery_truck, "truck")
    container_unit = first_unit(sea_leg, "container")
    # A Sea shipment without a recorded container stays UNKNOWN; do not fill
    # its container compatibility slot with a pickup-truck plate.
    primary_unit = container_unit if sea_leg else pickup_unit

    route_origin = next((str(row.get("origin")) for row in ordered if row.get("origin")), "")
    route_destination = next((str(row.get("destination")) for row in reversed(ordered) if row.get("destination")), "")
    first_etd = next((str(row.get("etd")) for row in ordered if row.get("etd")), "")
    last_eta = next((str(row.get("eta")) for row in reversed(ordered) if row.get("eta")), "")

    return {
        "structured": structured,
        "mode": str(first.get("mode") or ""),
        "origin": route_origin,
        "destination": route_destination,
        "pickup_leg": first_truck,
        "pickup_unit": pickup_unit,
        "delivery_leg": delivery_truck,
        "delivery_unit": delivery_unit,
        "main_leg": main,
        "primary_unit": primary_unit,
        "carrier": str(main.get("carrier") or ""),
        "booking_no": str(main.get("booking_no") or ""),
        "mbl": str(main.get("mbl") or ""),
        "hbl": str(main.get("hbl") or ""),
        "vessel": str(main.get("vessel") or ""),
        "etd": first_etd,
        "eta": last_eta,
        "container_no": str(primary_unit.get("number") or ""),
    }
