"""Source parsing and official-source registry for LOG-TRADE01.

The registry is intentionally a set of official entry points.  It does not
pretend that a discovered page is a retrieved legal conclusion.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlparse

from .models import (
    EvidenceStatus,
    SourceAuthority,
    SourceRecord,
    _normalise_tuple,
)


REGISTRY_PATH = Path(__file__).with_name("source_registry.json")


def _as_optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _validate_https(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError("official source URL must use HTTPS")


def parse_source_record(raw: Mapping[str, Any], *, default_jurisdiction: str | None = None) -> SourceRecord:
    """Parse and validate one source result without promoting its authority."""

    if not isinstance(raw, Mapping):
        raise TypeError("source record must be a mapping")
    jurisdiction = _as_optional_text(raw.get("jurisdiction")) or _as_optional_text(default_jurisdiction)
    if not jurisdiction:
        raise ValueError("jurisdiction is required")
    authority = _as_optional_text(raw.get("authority"))
    source_url = _as_optional_text(raw.get("source_url") or raw.get("url"))
    if not authority or not source_url:
        raise ValueError("authority and source_url are required")
    _validate_https(source_url)

    raw_status = raw.get("evidence_status", raw.get("status", EvidenceStatus.NOT_RETRIEVED.value))
    evidence_status = raw_status if isinstance(raw_status, EvidenceStatus) else EvidenceStatus(str(raw_status))
    raw_authority_level = raw.get("authority_level", SourceAuthority.OFFICIAL.value)
    authority_level = (
        raw_authority_level
        if isinstance(raw_authority_level, SourceAuthority)
        else SourceAuthority(str(raw_authority_level))
    )
    retrieved_at = _as_optional_text(raw.get("retrieved_at"))
    if retrieved_at:
        _parse_temporal(retrieved_at, allow_datetime=True)
    effective_from = _as_optional_text(raw.get("effective_from"))
    effective_to = _as_optional_text(raw.get("effective_to"))
    if effective_from:
        _parse_temporal(effective_from, allow_datetime=False)
    if effective_to:
        _parse_temporal(effective_to, allow_datetime=False)
    if evidence_status in {
        EvidenceStatus.VERIFIED,
        EvidenceStatus.PARTIALLY_VERIFIED,
        EvidenceStatus.STALE,
        EvidenceStatus.CONFLICTING,
    } and not retrieved_at:
        raise ValueError("retrieved_at is required for retrieved source evidence")

    confidence = raw.get("confidence")
    scope = raw.get("product_hs_scope", raw.get("hs_scope", ()))
    if isinstance(scope, str):
        scope = (scope,)
    else:
        scope = tuple(str(item) for item in _normalise_tuple(scope))

    return SourceRecord(
        jurisdiction=jurisdiction,
        authority=authority,
        source_url=source_url,
        retrieved_at=retrieved_at,
        effective_from=effective_from,
        effective_to=effective_to,
        product_hs_scope=scope,
        scope_description=_as_optional_text(raw.get("scope")),
        conclusion=raw.get("conclusion"),
        confidence=confidence,
        evidence_status=evidence_status,
        authority_level=authority_level,
        source_reference=_as_optional_text(raw.get("source_reference") or raw.get("reference")),
    )


def _parse_temporal(value: str, *, allow_datetime: bool) -> date | datetime:
    text = str(value).strip()
    try:
        if allow_datetime and "T" in text:
            return datetime.fromisoformat(text.replace("Z", "+00:00"))
        return date.fromisoformat(text[:10])
    except ValueError as exc:
        raise ValueError(f"invalid source date/time: {value}") from exc


@dataclass(frozen=True)
class OfficialSourceRegistry:
    registry_id: str
    version: str
    jurisdictions: dict[str, tuple[SourceRecord, ...]]
    live_source_poc: bool = False

    def for_jurisdiction(self, jurisdiction: str) -> tuple[SourceRecord, ...]:
        key = str(jurisdiction or "").strip().upper()
        return self.jurisdictions.get(key, ())

    def to_dict(self) -> dict[str, Any]:
        return {
            "registry_id": self.registry_id,
            "version": self.version,
            "live_source_poc": self.live_source_poc,
            "jurisdictions": {
                key: [record.to_dict() for record in records]
                for key, records in self.jurisdictions.items()
            },
        }


def load_official_source_registry(path: Path | str | None = None) -> OfficialSourceRegistry:
    registry_path = Path(path) if path is not None else REGISTRY_PATH
    payload = json.loads(registry_path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("source registry must be an object")
    registry_id = _as_optional_text(payload.get("registry_id"))
    version = _as_optional_text(payload.get("version"))
    if not registry_id or not version:
        raise ValueError("registry_id and version are required")
    raw_jurisdictions = payload.get("jurisdictions")
    if not isinstance(raw_jurisdictions, Mapping):
        raise ValueError("jurisdictions must be an object")
    jurisdictions: dict[str, tuple[SourceRecord, ...]] = {}
    for jurisdiction, raw_records in raw_jurisdictions.items():
        if not isinstance(raw_records, list):
            raise ValueError(f"source list required for {jurisdiction}")
        records = tuple(
            parse_source_record(record, default_jurisdiction=str(jurisdiction).upper())
            for record in raw_records
        )
        for record in records:
            if record.authority_level not in {
                SourceAuthority.OFFICIAL,
                SourceAuthority.OFFICIAL_DISCOVERY,
            }:
                raise ValueError("official registry cannot contain non-official source authority")
        jurisdictions[str(jurisdiction).upper()] = records
    return OfficialSourceRegistry(
        registry_id=registry_id,
        version=version,
        jurisdictions=jurisdictions,
        live_source_poc=bool(payload.get("live_source_poc", False)),
    )
