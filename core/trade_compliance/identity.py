"""Deterministic product-identity normalization for customer-provided input."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping
from typing import Any

from .models import FieldState, ProductIdentity, IDENTITY_FIELD_NAMES


def _key(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-zA-Z0-9]+", "_", text).strip("_").lower()
    return text


def _text(value: Any) -> str | None:
    if value is None or isinstance(value, Mapping):
        return None
    if isinstance(value, (list, tuple, set, frozenset)):
        value = ", ".join(str(item).strip() for item in value if str(item).strip())
    text = str(value).strip()
    return text or None


def _present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, Mapping):
        return bool(value)
    if isinstance(value, (list, tuple, set, frozenset)):
        return bool(value)
    return True


def _flatten_input(raw: Mapping[str, Any] | str) -> tuple[dict[str, Any], str | None]:
    if isinstance(raw, str):
        text = raw.strip()
        return {"commercial_name": text, "product_name": text}, text or None
    if not isinstance(raw, Mapping):
        raise TypeError("product input must be a mapping or string")

    nested: dict[str, Any] = {}
    for key in ("product_identity", "product", "cargo", "item"):
        value = raw.get(key)
        if isinstance(value, Mapping):
            nested.update(value)
            break
    nested.update(raw)
    description = (
        _text(raw.get("customer_description"))
        or _text(raw.get("description"))
        or _text(raw.get("cargo_description"))
    )
    return nested, description


ALIASES: dict[str, tuple[str, ...]] = {
    "commercial_name": ("commercial_name", "commercial", "ten_thuong_mai", "commercial_name_vn"),
    "product_name": ("product_name", "name", "ten_hang", "cargo_name", "item_name"),
    "model": ("model", "model_number", "product_model", "ma_model"),
    "manufacturer": ("manufacturer", "maker", "nha_san_xuat"),
    "brand": ("brand", "thuong_hieu"),
    "intended_use": ("intended_use", "use", "purpose", "muc_dich_su_dung"),
    "function": ("function", "function_description", "chuc_nang", "cong_dung"),
    "material": ("material", "materials", "vat_lieu", "chat_lieu"),
    "composition": ("composition", "ingredients", "thanh_phan"),
    "operating_principle": ("operating_principle", "principle", "nguyen_ly_hoat_dong"),
    "technical_specifications": (
        "technical_specifications",
        "technical_specs",
        "specifications",
        "specs",
        "thong_so_ky_thuat",
    ),
    "voltage": ("voltage", "dien_ap"),
    "power": ("power", "capacity_power", "cong_suat"),
    "capacity": ("capacity", "throughput", "nang_luc"),
    "dimensions": ("dimensions", "size", "kich_thuoc"),
    "chemical_identifiers": ("chemical_identifiers", "cas", "cas_number", "chemical_id", "ma_hoa_chat"),
    "medical_device_status": ("medical_device_status", "medical_device", "is_medical_device"),
    "dangerous_goods_status": ("dangerous_goods_status", "dangerous_goods", "dg_status", "is_dangerous_goods"),
    "origin_country": ("origin_country", "origin", "country_of_origin", "nuoc_xuat_xu"),
    "category": ("category", "product_category", "loai_hang", "commodity_category"),
}


def _lookup(data: Mapping[str, Any], field_name: str) -> Any:
    aliases = {_key(alias) for alias in ALIASES[field_name]}
    for key, value in data.items():
        if _key(key) in aliases:
            return value
    return None


def _infer_category(data: Mapping[str, Any]) -> str:
    explicit = _text(_lookup(data, "category"))
    if explicit:
        normalized = _key(explicit)
        if normalized in {"chemical", "chemicals", "hoa_chat"}:
            return "chemical"
        if normalized in {"medical", "medical_device", "medical_equipment", "thiet_bi_y_te"}:
            return "medical_device"
        if normalized in {"machine", "machinery", "equipment", "may_moc", "thiet_bi"}:
            return "machine"
        if normalized in {"unknown", "other", "khac"}:
            return "unknown"

    text_parts = []
    for field_name in ("commercial_name", "product_name", "function", "intended_use", "description"):
        value = _lookup(data, field_name) if field_name != "description" else data.get("description")
        if value is not None:
            text_parts.append(_key(value))
    text = " ".join(text_parts)
    if any(token in text for token in ("chemical", "hoa_chat", "reagent", "solvent", "acid", "sds", "msds")):
        return "chemical"
    if any(token in text for token in ("medical", "medical_device", "y_te", "surgical", "diagnostic")):
        return "medical_device"
    if any(token in text for token in ("machine", "machinery", "equipment", "may", "thiet_bi", "industrial")):
        return "machine"
    return "unknown"


def _as_specifications(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return {str(key): item for key, item in value.items()}
    text = _text(value)
    return {"raw": text} if text else {}


def _as_identifiers(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, Mapping):
        values = value.values()
    elif isinstance(value, (list, tuple, set, frozenset)):
        values = value
    else:
        values = re.split(r"[,;|]", str(value))
    return tuple(str(item).strip() for item in values if str(item).strip())


def _required_fields(category: str) -> tuple[str, ...]:
    common = ("product_name",)
    by_category = {
        "machine": ("function", "technical_specifications"),
        "chemical": ("composition", "chemical_identifiers", "intended_use"),
        "medical_device": ("model", "manufacturer", "intended_use", "medical_device_status"),
        "unknown": ("function", "intended_use"),
    }
    return common + by_category.get(category, by_category["unknown"])


def _not_relevant_fields(category: str) -> tuple[str, ...]:
    if category == "machine":
        return ("chemical_identifiers", "medical_device_status")
    if category == "chemical":
        return ("medical_device_status", "voltage", "power")
    if category == "medical_device":
        return ("chemical_identifiers",)
    return ()


def normalize_product_identity(raw: ProductIdentity | Mapping[str, Any] | str) -> ProductIdentity:
    """Normalize customer input without treating it as verified product identity."""

    if isinstance(raw, ProductIdentity):
        raw.validate()
        return raw
    data, description = _flatten_input(raw)
    category = _infer_category(data)
    values: dict[str, Any] = {}
    for field_name in IDENTITY_FIELD_NAMES:
        value = _lookup(data, field_name)
        if field_name == "technical_specifications":
            values[field_name] = _as_specifications(value)
        elif field_name == "chemical_identifiers":
            values[field_name] = _as_identifiers(value)
        else:
            values[field_name] = _text(value)

    if not values["product_name"]:
        values["product_name"] = values["commercial_name"] or description
    if not values["commercial_name"]:
        values["commercial_name"] = values["product_name"]
    if category == "medical_device" and values["medical_device_status"] is None:
        values["medical_device_status"] = "POSSIBLE_MEDICAL_DEVICE"

    states: dict[str, FieldState] = {}
    not_relevant = set(_not_relevant_fields(category))
    required = set(_required_fields(category))
    for field_name in IDENTITY_FIELD_NAMES:
        value = values[field_name]
        if field_name in not_relevant:
            states[field_name] = FieldState.NOT_RELEVANT
        elif _present(value):
            states[field_name] = FieldState.PROVIDED
        elif field_name in required:
            states[field_name] = FieldState.REQUIRED_FOR_THIS_PRODUCT
        else:
            states[field_name] = FieldState.UNKNOWN

    return ProductIdentity(
        **values,
        category=category,
        customer_description=description,
        identity_status="NORMALIZED_UNVERIFIED",
        field_states=states,
    )


def missing_product_fields(identity: ProductIdentity | Mapping[str, Any] | str) -> tuple[str, ...]:
    normalized = normalize_product_identity(identity)
    return normalized.missing_fields
