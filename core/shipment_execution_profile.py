"""Shipment execution profile — Incoterms × mode × load model × scope × insurance.

LOGI_SHIPMENT_EXECUTION_PROFILE_01 (issue #76).

The Owner's ruling restated as code: **a shipment workflow is not universal.**
It is derived from the shipment's own execution profile:

    INCOTERM (code + version + named place)
      + TRƯỜNG THÀNH SERVICE SCOPE
      + PRIMARY MODE
      + LOAD MODEL / EQUIPMENT
      + ACTUAL CARGO INSURANCE
      + PERSISTED FACTS
        → the RELEVANT operational stages
        → the NEXT action that belongs to them

This module is the ONE pure semantics authority for that derivation. It is
deliberately not a service, not a store and not a workflow engine:

* no database access, no Streamlit, no I/O — a pure function of the shipment
  document plus the operator-confirmed profile block;
* no new truth for anything the repository already owns (``data.0.0.mode``,
  ``data.0.0.incoterm``, ``data.1.2.*`` transport facts, ``data.2.4`` customs
  facts, ``data.2.7`` delivery facts, the repeatable ``transport_legs`` unit
  collection) — every one of those is READ here and reused as-is;
* the only facts it consumes from the new profile block are ones no existing
  field could carry (Incoterms VERSION, named place, load model, the
  operator-confirmed service scope, actual cargo insurance).

External semantics authority (pinned by Issue #76 / CONTROL_TOWER_RESEARCH_RECEIPT):

* ICC Incoterms 2020 / 2010 / the legacy 2000-era terms (DAF, DDU);
* ICC Academy CIP/CIF cover guidance (CIF 2020 keeps Institute Cargo
  Clauses C as its default minimum; CIP 2020 raises it to Clauses A; that
  CIP-2020 semantics is NEVER projected backwards onto a 2010 shipment);
* Maersk (FCL vs LCL) and DHL (FTL vs LTL) for the load-model dimension,
  which is separate from the transport mode.

Hard rules encoded below, each with its own test:

* ``FOB + ROAD`` / ``CIF + AIR`` / ``CFR + ROAD`` / ``FAS + AIR`` are
  structurally invalid execution profiles — the UI must EXPLAIN the conflict
  and the writer must refuse a NEW save, but a historical document carrying
  such a combination is never mutated: it renders ``CONFIG_CHECK``;
* DAT exists in 2010 only, DPU exists in 2020 only;
* DAF/DDU are legacy Incoterms 2000-era terms, never offered as 2010/2020;
* CNF / C&F are user aliases of the canonical ICC rule CFR — normalized on the
  way in, with the ORIGINAL contract wording preserved as evidence;
* a bare ``FOB`` without a named place is operationally incomplete — and a place
  read out of the contract wording (``FOB Shenzhen``) is EVIDENCE that still has
  to be confirmed, never a written fact;
* ``UNKNOWN`` never becomes ``NO``, and an Incoterm insurance obligation is
  NEVER evidence that a policy/certificate actually exists;
* the NEXT action is the first unmet requirement of the RELEVANT stages, with
  the load-model requirement (FCL equipment / FTL truck) asked BEFORE the
  carriage documents it determines — and each persisted fact is asked for once
  (the FTL truck-type requirement belongs to the load-model stage, not to a
  second pickup prompt for the same ``data.1.2.pickup_truck_type``).
"""

from __future__ import annotations

import re
from typing import Any, Iterable, Mapping, Sequence

from core.customs_truth import customs_clearance_confirmed

# ---------------------------------------------------------------------------
# Incoterms versions
# ---------------------------------------------------------------------------

VERSION_2010 = "2010"
VERSION_2020 = "2020"
VERSION_LEGACY_2000 = "2000_LEGACY"

#: Offered in the UI, in the order the progressive flow shows them.
INCOTERM_VERSIONS: tuple[str, ...] = (VERSION_2020, VERSION_2010, VERSION_LEGACY_2000)

VERSION_LABELS: dict[str, str] = {
    VERSION_2020: "Incoterms 2020",
    VERSION_2010: "Incoterms 2010",
    VERSION_LEGACY_2000: "Incoterms 2000 (legacy — DAF/DDU)",
}

#: Rule scope per ICC: maritime rules may only carry a sea / inland-waterway
#: main carriage. Everything else is any-mode.
SCOPE_ANY_MODE = "ANY_MODE"
SCOPE_SEA_ONLY = "SEA_ONLY"

#: Canonical rule sets, in ICC order. 2010 legitimately carries DAT (renamed
#: DPU in 2020); 2020 legitimately carries DPU and no longer DAT.
RULES_2020: tuple[tuple[str, str], ...] = (
    ("EXW", SCOPE_ANY_MODE), ("FCA", SCOPE_ANY_MODE), ("CPT", SCOPE_ANY_MODE),
    ("CIP", SCOPE_ANY_MODE), ("DAP", SCOPE_ANY_MODE), ("DPU", SCOPE_ANY_MODE),
    ("DDP", SCOPE_ANY_MODE),
    ("FAS", SCOPE_SEA_ONLY), ("FOB", SCOPE_SEA_ONLY), ("CFR", SCOPE_SEA_ONLY),
    ("CIF", SCOPE_SEA_ONLY),
)

RULES_2010: tuple[tuple[str, str], ...] = (
    ("EXW", SCOPE_ANY_MODE), ("FCA", SCOPE_ANY_MODE), ("CPT", SCOPE_ANY_MODE),
    ("CIP", SCOPE_ANY_MODE), ("DAT", SCOPE_ANY_MODE), ("DAP", SCOPE_ANY_MODE),
    ("DDP", SCOPE_ANY_MODE),
    ("FAS", SCOPE_SEA_ONLY), ("FOB", SCOPE_SEA_ONLY), ("CFR", SCOPE_SEA_ONLY),
    ("CIF", SCOPE_SEA_ONLY),
)

#: Legacy 2000-era terms the Owner's historical contracts may really carry.
#: DES / DEQ were also 2000 terms but are NOT offered here: this slice supports
#: only the two labels Issue #76 requires (DAF, DDU) rather than a legacy
#: Incoterms 2000 catalogue nobody asked for.
RULES_2000_LEGACY: tuple[tuple[str, str], ...] = (
    ("DAF", SCOPE_ANY_MODE), ("DDU", SCOPE_ANY_MODE),
)

INCOTERM_RULES: dict[str, tuple[tuple[str, str], ...]] = {
    VERSION_2020: RULES_2020,
    VERSION_2010: RULES_2010,
    VERSION_LEGACY_2000: RULES_2000_LEGACY,
}

#: Business aliases → canonical ICC rule. Keys are the compact form (spaces,
#: dots, dashes and underscores removed, uppercased) so ``C&F``, ``CNF`` and
#: ``C& F`` all land on CFR.
INCOTERM_ALIASES: dict[str, str] = {
    "CNF": "CFR",
    "CANDF": "CFR",
    "CNFR": "CFR",
    "COSTANDFREIGHT": "CFR",
}

#: Every canonical code this module knows, across all versions.
ALL_CODES: tuple[str, ...] = tuple(
    dict.fromkeys(code for rules in INCOTERM_RULES.values() for code, _ in rules)
)

def _compact(value: Any) -> str:
    """Case/space/punctuation-insensitive form of ONE contract term.

    ``C&F`` and ``C and F`` collapse to the same key as ``CANDF`` so the
    business alias really resolves, and ``C.I.F.`` collapses onto ``CIF``.
    """

    text = str(value or "").strip().upper().replace("&", "AND")
    return re.sub(r"[\s.\-_/]+", "", text)


def normalize_incoterm(raw: Any) -> dict[str, Any]:
    """Normalize ONE raw contract/operator term into canonical Incoterms truth.

    Returns ``{"code", "rawLabel", "aliasNote", "inlinePlace", "recognized"}``:

    * ``code``   canonical ICC code (``CNF`` → ``CFR``), or ``""`` when the raw
      text is not a recognized rule at all — never a guess;
    * ``rawLabel`` the ORIGINAL text, preserved whenever it differs from the
      canonical code, because the historical contract wording is evidence and
      must never be silently rewritten;
    * ``aliasNote`` the operator-facing explanation of the normalization
      (``"CNF là cách gọi trong hợp đồng; Incoterms chuẩn hóa thành CFR."``),
      empty when nothing was normalized;
    * ``inlinePlace`` the place a contract wrote INSIDE the term
      (``"FOB Shenzhen"`` → ``"Shenzhen"``). It is evidence read from the
      contract text, offered as a suggestion when no named place has been
      confirmed yet — it is NEVER written by itself.
    """

    text = str(raw or "").strip()
    if not text:
        return {"code": "", "rawLabel": "", "aliasNote": "", "inlinePlace": "",
                "recognized": False}

    def recognized(code: str, *, alias: bool, inline_place: str = "") -> dict[str, Any]:
        return {
            "code": code,
            "rawLabel": text if _compact(text) != code else "",
            "aliasNote": (f"{text} là cách gọi trong hợp đồng; Incoterms chuẩn hóa thành {code}."
                          if alias and _compact(text) != code else ""),
            "inlinePlace": inline_place,
            "recognized": True,
        }

    compact = _compact(text)
    if compact in INCOTERM_ALIASES:
        return recognized(INCOTERM_ALIASES[compact], alias=True)
    if compact in ALL_CODES:
        return recognized(compact, alias=False)

    # A contract often writes the place inside the term: "FOB Shenzhen",
    # "CIF Hai Phong". The rule code is still canonical; only the place text
    # after it is surfaced as raw evidence.
    first, _, rest = text.partition(" ")
    candidate = _compact(first)
    if rest.strip() and candidate in INCOTERM_ALIASES:
        return recognized(INCOTERM_ALIASES[candidate], alias=True, inline_place=rest.strip())
    if rest.strip() and candidate in ALL_CODES:
        return recognized(candidate, alias=False, inline_place=rest.strip())
    return {"code": "", "rawLabel": text, "aliasNote": "", "inlinePlace": "",
            "recognized": False}


def rule_scope(version: str, code: str) -> str:
    """``SCOPE_SEA_ONLY`` for FAS/FOB/CFR/CIF, ``SCOPE_ANY_MODE`` otherwise."""

    for candidate, scope in INCOTERM_RULES.get(str(version), ()):  # type: ignore[arg-type]
        if candidate == code:
            return scope
    # Version-agnostic fallback: the maritime rules are maritime in every
    # version this module supports, so an UNKNOWN version still cannot make
    # FOB a road rule.
    for rules in INCOTERM_RULES.values():
        for candidate, scope in rules:
            if candidate == code:
                return scope
    return SCOPE_ANY_MODE


def versions_defining(code: str) -> tuple[str, ...]:
    return tuple(
        version for version, rules in INCOTERM_RULES.items()
        if any(candidate == code for candidate, _ in rules)
    )


def codes_for_version(version: str) -> tuple[str, ...]:
    return tuple(code for code, _ in INCOTERM_RULES.get(str(version), ()))


# ---------------------------------------------------------------------------
# Modes
# ---------------------------------------------------------------------------

MODE_ROAD = "ROAD"
MODE_SEA = "SEA"
MODE_AIR = "AIR"
MODE_RAIL = "RAIL"

#: Canonical execution-profile modes. The repository's EXISTING shipment mode
#: authority (`data.0.0.mode`) stores "Truck"/"Sea"/"Air"/"Rail" and is reused
#: unchanged — this map is only the display/derivation vocabulary.
CANONICAL_MODES: tuple[str, ...] = (MODE_ROAD, MODE_SEA, MODE_AIR, MODE_RAIL)

MODE_LABELS: dict[str, str] = {
    MODE_ROAD: "Đường bộ",
    MODE_SEA: "Đường biển",
    MODE_AIR: "Hàng không",
    MODE_RAIL: "Đường sắt",
}

#: canonical profile mode → the value the existing `data.0.0.mode` field holds.
STORED_MODE_BY_CANONICAL: dict[str, str] = {
    MODE_ROAD: "Truck", MODE_SEA: "Sea", MODE_AIR: "Air", MODE_RAIL: "Rail",
}

_MODE_ALIASES: dict[str, str] = {
    "truck": MODE_ROAD, "road": MODE_ROAD, "duongbo": MODE_ROAD, "bo": MODE_ROAD,
    "sea": MODE_SEA, "ocean": MODE_SEA, "duongbien": MODE_SEA, "bien": MODE_SEA,
    "air": MODE_AIR, "hangkhong": MODE_AIR, "fly": MODE_AIR,
    "rail": MODE_RAIL, "train": MODE_RAIL, "duongsat": MODE_RAIL, "sat": MODE_RAIL,
}


def canonical_mode(raw: Any) -> str:
    """Map any stored/entered mode onto ROAD|SEA|AIR|RAIL, else ``""`` (UNKNOWN)."""

    compact = _compact(raw)
    if not compact:
        return ""
    if compact in CANONICAL_MODES:
        return compact
    return _MODE_ALIASES.get(compact.lower(), "")


# ---------------------------------------------------------------------------
# Load models (separate from mode — Maersk FCL/LCL, DHL FTL/LTL)
# ---------------------------------------------------------------------------

LOADMODEL_FCL = "FCL"
LOADMODEL_LCL = "LCL"
LOADMODEL_FTL = "FTL"
LOADMODEL_LTL = "LTL"
LOADMODEL_AIR_DIRECT = "DIRECT"
LOADMODEL_AIR_CONSOLIDATED = "CONSOLIDATED"
LOADMODEL_OTHER = "OTHER"

LOAD_MODELS_BY_MODE: dict[str, tuple[tuple[str, str], ...]] = {
    MODE_SEA: (
        (LOADMODEL_FCL, "FCL — nguyên container"),
        (LOADMODEL_LCL, "LCL — hàng lẻ / ghép container"),
        (LOADMODEL_OTHER, "Khác / chưa xác định"),
    ),
    MODE_ROAD: (
        (LOADMODEL_FTL, "FTL — nguyên xe"),
        (LOADMODEL_LTL, "LTL — hàng lẻ / ghép xe"),
    ),
    MODE_AIR: (
        (LOADMODEL_AIR_DIRECT, "Hàng nguyên / chuyến trực tiếp"),
        (LOADMODEL_AIR_CONSOLIDATED, "Hàng lẻ / ghép lô"),
        (LOADMODEL_OTHER, "Khác / chưa xác định"),
    ),
    # Rail deliberately has NO preset family: this slice only guarantees that
    # RAIL is not forced into a road/sea/air assumption.
    MODE_RAIL: (),
}

LOAD_MODEL_LABELS: dict[str, str] = {
    LOADMODEL_FCL: "FCL (nguyên container)",
    LOADMODEL_LCL: "LCL (hàng lẻ, ghép container)",
    LOADMODEL_FTL: "FTL (nguyên xe)",
    LOADMODEL_LTL: "LTL (hàng lẻ, ghép xe)",
    LOADMODEL_AIR_DIRECT: "Hàng nguyên / trực tiếp",
    LOADMODEL_AIR_CONSOLIDATED: "Hàng lẻ / ghép lô",
    LOADMODEL_OTHER: "Khác / chưa xác định",
}


def load_models_for_mode(mode: str) -> tuple[tuple[str, str], ...]:
    return LOAD_MODELS_BY_MODE.get(str(mode), ())


def load_model_label(mode: str, load_model: str) -> str:
    """ONE label authority: the mode's own catalog, never a second wording.

    The client catalog is generated from ``projection_options()`` (i.e. from the
    per-mode catalogs), so the projected profile must read its label from the
    SAME place — otherwise a lot would show one wording in the picker and
    another in the summary.
    """

    code = _text(load_model).upper()
    if not code:
        return ""
    for value, label in load_models_for_mode(mode):
        if value == code:
            return label
    return LOAD_MODEL_LABELS.get(code, "")


def load_model_valid_for_mode(mode: str, load_model: str) -> bool:
    if not load_model:
        return True
    return any(code == load_model for code, _ in load_models_for_mode(mode))


# ---------------------------------------------------------------------------
# Operational presets (company operating profiles — NOT capacity regulations)
# ---------------------------------------------------------------------------

#: Trường Thành road operating presets for FTL. These are company operating
#: profiles ONLY: nothing here implies tonnes, CBM, price, package count, truck
#: count or route suitability.
TRUCK_PRESETS: tuple[tuple[str, str], ...] = (
    ("17.5m", "17,5 m"),
    ("13.5m", "13,5 m"),
    ("9.6m", "9,6 m"),
    ("6.8m", "6,8 m"),
    (LOADMODEL_OTHER, "Khác (tự nhập)"),
)

#: Sea FCL equipment presets. 20GP/40GP/40HC cover the current operation; every
#: other equipment (reefer, open top, flat rack…) is expressed through Khác
#: with free text, because the existing data carries no such catalogue and this
#: slice refuses to overbuild one. A shipment may carry SEVERAL units — the
#: equipment list is read from the EXISTING repeatable container units on the
#: transport legs, never from a single new string.
CONTAINER_PRESETS: tuple[tuple[str, str], ...] = (
    ("20GP", "20' GP (khô)"),
    ("40GP", "40' GP (khô)"),
    ("40HC", "40' HC (cao)"),
    (LOADMODEL_OTHER, "Khác (tự nhập)"),
)

CONTAINER_PRESET_CODES: tuple[str, ...] = tuple(code for code, _ in CONTAINER_PRESETS)
TRUCK_PRESET_CODES: tuple[str, ...] = tuple(code for code, _ in TRUCK_PRESETS)


# ---------------------------------------------------------------------------
# Trường Thành service scope — SEPARATE from the Incoterm
# ---------------------------------------------------------------------------

SCOPE_ORIGIN_PICKUP = "ORIGIN_PICKUP"
SCOPE_EXPORT_HANDLING = "EXPORT_HANDLING"
SCOPE_EXPORT_CUSTOMS = "EXPORT_CUSTOMS"
SCOPE_ORIGIN_TERMINAL_OR_BORDER = "ORIGIN_TERMINAL_OR_BORDER"
SCOPE_MAIN_CARRIAGE = "MAIN_CARRIAGE"
SCOPE_CROSS_BORDER_COORDINATION = "CROSS_BORDER_COORDINATION"
SCOPE_IMPORT_CUSTOMS = "IMPORT_CUSTOMS"
SCOPE_DESTINATION_TRUCKING = "DESTINATION_TRUCKING"
SCOPE_FINAL_DELIVERY = "FINAL_DELIVERY"
SCOPE_CARGO_INSURANCE_ARRANGEMENT = "CARGO_INSURANCE_ARRANGEMENT"

#: Canonical operational order. The order IS the pipeline; membership is what
#: the operator confirms. An Incoterm NEVER adds a segment on its own.
SERVICE_SCOPE_SEGMENTS: tuple[tuple[str, str, str], ...] = (
    (SCOPE_ORIGIN_PICKUP, "Lấy hàng tại kho / nhà máy", "Lấy hàng"),
    (SCOPE_EXPORT_HANDLING, "Xử lý hàng xuất (đóng gói, bãi, chứng từ)", "Xử lý xuất"),
    (SCOPE_EXPORT_CUSTOMS, "Khai báo hải quan xuất", "HQ xuất"),
    (SCOPE_ORIGIN_TERMINAL_OR_BORDER, "Giao hàng tại bãi / cửa khẩu đi", "Cửa khẩu đi"),
    (SCOPE_MAIN_CARRIAGE, "Thu xếp chặng chính (biển / bay / sắt / bộ)", "Chặng chính"),
    (SCOPE_CROSS_BORDER_COORDINATION, "Điều phối qua biên giới / chuyển tải", "Qua biên giới"),
    (SCOPE_IMPORT_CUSTOMS, "Khai báo hải quan nhập", "HQ nhập"),
    (SCOPE_DESTINATION_TRUCKING, "Vận chuyển nội địa đến điểm giao", "Chạy nội địa"),
    (SCOPE_FINAL_DELIVERY, "Giao hàng tận nơi", "Giao hàng"),
    (SCOPE_CARGO_INSURANCE_ARRANGEMENT, "Thu xếp bảo hiểm hàng hóa", "Bảo hiểm"),
)

SERVICE_SCOPE_CODES: tuple[str, ...] = tuple(code for code, _, _ in SERVICE_SCOPE_SEGMENTS)
SCOPE_LABELS: dict[str, str] = {code: label for code, label, _ in SERVICE_SCOPE_SEGMENTS}
SCOPE_SHORT_LABELS: dict[str, str] = {code: short for code, _, short in SERVICE_SCOPE_SEGMENTS}


def normalize_service_scope(values: Any) -> list[str]:
    """Keep only known segment codes, in canonical pipeline order, deduplicated."""

    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        return []
    provided = {str(value).strip().upper() for value in values}
    return [code for code in SERVICE_SCOPE_CODES if code in provided]


def scope_summary(scope: Sequence[str]) -> str:
    """``"Cửa khẩu đi → Giao hàng"`` for a compact one-line profile summary."""

    ordered = normalize_service_scope(scope)
    if not ordered:
        return ""
    if len(ordered) == 1:
        return SCOPE_SHORT_LABELS.get(ordered[0], ordered[0])
    return f"{SCOPE_SHORT_LABELS.get(ordered[0], ordered[0])} → {SCOPE_SHORT_LABELS.get(ordered[-1], ordered[-1])}"


# ---------------------------------------------------------------------------
# Insurance — TWO DISTINCT TRUTHS
# ---------------------------------------------------------------------------

INSURANCE_SELLER_REQUIRED = "SELLER_REQUIRED"
INSURANCE_NOT_REQUIRED_BY_INCOTERM = "NOT_REQUIRED_BY_INCOTERM"

CLAUSE_C = "ICC_C"
CLAUSE_A = "ICC_A"
CLAUSE_2010_MINIMUM = "IC_2010_MINIMUM"
CLAUSE_UNKNOWN = ""

CLAUSE_LABELS: dict[str, str] = {
    CLAUSE_C: "mức tối thiểu Nhóm C (Institute Cargo Clauses C)",
    CLAUSE_A: "mức tối thiểu Nhóm A (Institute Cargo Clauses A)",
    CLAUSE_2010_MINIMUM: "mức bảo hiểm tối thiểu theo Incoterms 2010 (không áp dụng Nhóm A của bản 2020)",
    CLAUSE_UNKNOWN: "chưa xác định",
}

ACTUAL_INSURANCE_UNKNOWN = "UNKNOWN"
ACTUAL_INSURANCE_NO = "NO"
ACTUAL_INSURANCE_YES = "YES"
ACTUAL_INSURANCE_STATES: tuple[str, ...] = (
    ACTUAL_INSURANCE_UNKNOWN, ACTUAL_INSURANCE_YES, ACTUAL_INSURANCE_NO,
)
ACTUAL_INSURANCE_LABELS: dict[str, str] = {
    ACTUAL_INSURANCE_UNKNOWN: "Chưa xác nhận",
    ACTUAL_INSURANCE_NO: "Không có bảo hiểm",
    ACTUAL_INSURANCE_YES: "Đã có bảo hiểm",
}

#: A persisted ``NO`` is never silently rewritten into ``UNKNOWN``: when the
#: profile required cover, it is a CONFIRMED MISMATCH and the only honest
#: sentence is the exception itself. These are the two exact wordings the
#: operator sees (Incoterm-driven vs Trường Thành-scope-driven).
INSURANCE_MISMATCH_INCOTERM = (
    "Bảo hiểm thực tế đang ghi KHÔNG CÓ, nhưng điều kiện giao hàng yêu cầu "
    "người bán thu xếp bảo hiểm."
)
INSURANCE_MISMATCH_SCOPE = (
    "Bảo hiểm thực tế đang ghi KHÔNG CÓ, nhưng phạm vi Trường Thành thực hiện "
    "có thu xếp bảo hiểm hàng hóa."
)
INSURANCE_MISMATCH_LABEL = "Bảo hiểm: có yêu cầu nhưng thực tế ghi KHÔNG CÓ"


def incoterm_insurance(code: str, version: str) -> dict[str, Any]:
    """The DERIVED, read-only seller insurance obligation of ONE Incoterm rule.

    Never a statement that a policy exists. For every rule other than CIF/CIP
    the only truthful sentence is that the Incoterm does not oblige the seller
    to arrange insurance — NOT "there is no insurance".
    """

    if code == "CIF":
        if version == VERSION_2010:
            note = ("CIF 2010: người bán phải thu xếp bảo hiểm, mức tối thiểu Nhóm C "
                    "(Institute Cargo Clauses C / tương đương).")
        elif version == VERSION_LEGACY_2000:
            note = ("CIF (bản 2000 legacy): người bán phải thu xếp bảo hiểm theo quy tắc bản 2000. "
                    "Mức bảo hiểm tối thiểu của bản 2000 không được suy diễn từ bản 2020.")
        elif version == VERSION_2020:
            note = ("CIF 2020: người bán phải thu xếp bảo hiểm, mức tối thiểu Nhóm C "
                    "(Institute Cargo Clauses C / tương đương).")
        else:
            note = ("CIF: người bán phải thu xếp bảo hiểm, mức tối thiểu Nhóm C. "
                    "Phiên bản Incoterms của lô chưa được xác nhận.")
        clause = CLAUSE_2010_MINIMUM if version == VERSION_LEGACY_2000 else CLAUSE_C
        return {"obligation": INSURANCE_SELLER_REQUIRED, "clause": clause,
                "clauseLabel": CLAUSE_LABELS.get(clause, ""), "note": note,
                "versionSpecific": version in {VERSION_2010, VERSION_2020}}

    if code == "CIP":
        if version == VERSION_2020:
            clause = CLAUSE_A
            note = ("CIP 2020: người bán phải thu xếp bảo hiểm với mức tối thiểu Nhóm A "
                    "(Institute Cargo Clauses A / tương đương).")
        elif version == VERSION_2010:
            clause = CLAUSE_2010_MINIMUM
            note = ("CIP 2010: người bán phải thu xếp bảo hiểm theo mức tối thiểu của bản 2010. "
                    "KHÔNG áp dụng Nhóm A của CIP 2020 cho lô 2010 này.")
        elif version == VERSION_LEGACY_2000:
            clause = CLAUSE_UNKNOWN
            note = ("CIP (bản 2000 legacy): người bán phải thu xếp bảo hiểm; mức bảo hiểm tối thiểu "
                    "của bản 2000 không được suy diễn từ bản 2020.")
        else:
            clause = CLAUSE_UNKNOWN
            note = ("CIP: người bán phải thu xếp bảo hiểm. Nhóm A chỉ áp dụng cho CIP 2020, "
                    "nên mức tối thiểu chỉ được xác định khi biết phiên bản Incoterms của lô.")
        return {"obligation": INSURANCE_SELLER_REQUIRED, "clause": clause,
                "clauseLabel": CLAUSE_LABELS.get(clause, ""), "note": note,
                "versionSpecific": version in {VERSION_2010, VERSION_2020}}

    if not code:
        return {"obligation": "", "clause": CLAUSE_UNKNOWN, "clauseLabel": "",
                "note": "Chưa xác định điều kiện giao hàng nên chưa suy ra nghĩa vụ bảo hiểm.",
                "versionSpecific": False}

    return {
        "obligation": INSURANCE_NOT_REQUIRED_BY_INCOTERM,
        "clause": CLAUSE_UNKNOWN,
        "clauseLabel": "",
        "note": "Incoterm không bắt buộc người bán thu xếp bảo hiểm.",
        "versionSpecific": False,
    }


# ---------------------------------------------------------------------------
# Profile facts
# ---------------------------------------------------------------------------

def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _section(shipment: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    data = shipment.get("data")
    if not isinstance(data, Mapping):
        return {}
    value = data.get(key)
    return value if isinstance(value, Mapping) else {}


def _profile_block(shipment: Mapping[str, Any]) -> Mapping[str, Any]:
    head = _section(shipment, "0.0")
    block = head.get("execution_profile")
    return block if isinstance(block, Mapping) else {}


def profile_facts(shipment: Mapping[str, Any]) -> dict[str, Any]:
    """Read the operator-confirmed profile facts + the persisted shipment facts.

    Every value is READ from the shipment document. Nothing is defaulted, so a
    legacy document that only carries ``mode`` + ``incoterm`` yields honest
    UNKNOWN/blank profile facts and its projection is ``PROFILE_INCOMPLETE``.
    """

    head = _section(shipment, "0.0")
    block = _profile_block(shipment)
    insurance = block.get("cargo_insurance")
    insurance = insurance if isinstance(insurance, Mapping) else {}

    stored_mode = _text(head.get("mode"))
    raw_incoterm = _text(head.get("incoterm"))
    normalized = normalize_incoterm(raw_incoterm)

    version = _text(block.get("incoterm_version"))
    version = version if version in INCOTERM_VERSIONS else ""
    raw_evidence = _text(block.get("incoterm_raw_label")) or normalized["rawLabel"]
    # The raw contract wording survives in its OWN block field, so the alias
    # explanation is re-derived from that evidence rather than from the already
    # normalized code in `data.0.0.incoterm`.
    alias_note = normalized["aliasNote"]
    if not alias_note and raw_evidence and raw_evidence.upper() != normalized["code"].upper():
        alias_note = normalize_incoterm(raw_evidence)["aliasNote"]
    named_place = _text(block.get("incoterm_named_place"))
    place_source = "CONFIRMED" if named_place else ""
    if not named_place and normalized["inlinePlace"]:
        # Read from the contract text ("CIF Hai Phong") — evidence, not a
        # confirmation, and never written back by itself.
        named_place = normalized["inlinePlace"]
        place_source = "CONTRACT_LABEL"

    actual_status = _text(insurance.get("status")).upper()
    actual_status = actual_status if actual_status in ACTUAL_INSURANCE_STATES else ""

    return {
        "storedMode": stored_mode,
        "mode": canonical_mode(stored_mode),
        "incoterm": normalized["code"],
        "incotermRawInput": raw_incoterm,
        "incotermRawLabel": raw_evidence,
        "incotermAliasNote": alias_note,
        "incotermRecognized": normalized["recognized"],
        "incotermVersion": version,
        "incotermNamedPlace": named_place,
        "incotermPlaceSource": place_source,
        "loadModel": _text(block.get("load_model")).upper(),
        "serviceScope": normalize_service_scope(block.get("service_scope")),
        "serviceScopeConfirmed": bool(block.get("service_scope_confirmed")),
        "cargoInsuranceStatus": actual_status,
        "cargoInsuranceArrangedBy": _text(insurance.get("arranged_by")),
        "cargoInsuranceInsurer": _text(insurance.get("insurer_name")),
        "cargoInsurancePolicyNo": _text(insurance.get("policy_or_certificate_number")),
        "cargoInsuranceCoverageNote": _text(insurance.get("coverage_or_notes")),
    }


def persisted_facts(shipment: Mapping[str, Any], *,
                    legs: Sequence[Mapping[str, Any]] | None = None) -> dict[str, Any]:
    """Read the operational facts the execution profile depends on.

    Every key below is an EXISTING canonical path; this function adds no field
    and issues no read. ``transport_legs`` (with its legacy read fallback) stays
    the ONE authority for repeatable trucks and containers. A caller that has
    already derived the legs for this render hands them in through ``legs`` so
    the same pure projection is not computed twice.
    """

    from core.shipment_operations import compatibility_facts, transport_legs_for_read

    transport = _section(shipment, "1.2")
    customs = _section(shipment, "2.4")
    delivery = _section(shipment, "2.7")
    # The main-carriage document facts come from the EXISTING canonical
    # projection: for a structured document they live on the legs, for a legacy
    # one on the scalar fields in `data.1.2`. Reusing that projection is what
    # keeps this module from becoming a second reader of the same truth.
    operational = compatibility_facts(shipment)
    if legs is None:
        legs, structured = transport_legs_for_read(shipment)
    else:
        legs, structured = list(legs), True

    containers: list[dict[str, Any]] = []
    trucks: list[dict[str, Any]] = []
    for leg in legs:
        for unit in (leg.get("units") or []):
            if not isinstance(unit, Mapping):
                continue
            row = {
                "id": _text(unit.get("id")),
                "number": _text(unit.get("number")),
                "typeSize": _text(unit.get("type_size")),
                "sealNo": _text(unit.get("seal_no")),
                "legMode": _text(leg.get("mode")),
            }
            if _text(unit.get("kind")) == "container":
                containers.append(row)
            elif _text(unit.get("kind")) == "truck":
                trucks.append(row)

    return {
        "structuredTransport": bool(structured),
        "bookingNo": _text(operational.get("booking_no")),
        "carrier": _text(operational.get("carrier")),
        "mbl": _text(operational.get("mbl")),
        "hbl": _text(operational.get("hbl")),
        "vessel": _text(operational.get("vessel")),
        # AIR: mode-specific identity must come from the real main transport leg,
        # not the legacy sea MBL/HBL compatibility slots.
        "mawb": _text((operational.get("main_leg") or {}).get("mawb")),
        "hawb": _text((operational.get("main_leg") or {}).get("hawb")),
        "flightNo": _text((operational.get("main_leg") or {}).get("flight_no")),
        "etd": _text(operational.get("etd")) or _text(transport.get("etd")),
        "pol": _text(operational.get("origin")) or _text(transport.get("pol")),
        "pod": _text(operational.get("destination")) or _text(transport.get("pod")),
        "qtyPkg": _text(transport.get("qty_pkg")),
        "containerNo": _text(transport.get("container_no")),
        "containers": containers,
        "containerCount": len(containers),
        "containerTypes": sorted({row["typeSize"] for row in containers if row["typeSize"]}),
        "trucks": trucks,
        "pickupTruckType": _text(transport.get("pickup_truck_type")),
        "customsDeclarationNo": _text(customs.get("tk_no")),
        "customsDeclarationDate": _text(customs.get("tk_date")),
        "customsStatus": customs.get("customs_status"),
        # LOGI-199 T2/T4 — consolidation is an occurrence fact, never implied
        # by choosing LCL/LTL as the load model.
        "seaConsolidatedAt": _text((transport.get("sea_export") or {}).get("consolidated_at")
                                   if isinstance(transport.get("sea_export"), Mapping) else ""),
        "roadConsolidatedAt": _text((transport.get("road_facts") or {}).get("ltl_consolidated_at")
                                    if isinstance(transport.get("road_facts"), Mapping) else ""),
        "delivered": bool(delivery.get("is_delivered")),
        "deliveredAt": _text(delivery.get("delivered_at") or delivery.get("delivery_date")),
        "deliveryLocation": _text(delivery.get("delivery_location") or delivery.get("addr")),
    }


def truck_profile(facts: Mapping[str, Any]) -> dict[str, Any]:
    """The ROAD truck profile, from EXISTING facts only.

    ``data.1.2.pickup_truck_type`` (LOGI_CN_TRUCK_TYPE_PERSIST_01) stays the
    canonical free-text truck fact; a truck unit's ``type_size`` on the
    transport legs is the same truth in the structured model. Both are read;
    neither is invented, and truck length never implies capacity.
    """

    pickup = _text(facts.get("pickupTruckType"))
    unit_types = [_text(row.get("typeSize")) for row in (facts.get("trucks") or []) if _text(row.get("typeSize"))]
    preset = next((value for value in ([pickup] + unit_types)
                   if value.upper() in {code.upper() for code, _ in TRUCK_PRESETS}), "")
    return {
        "pickupTruckType": pickup,
        "unitTypes": unit_types,
        "known": bool(pickup or unit_types),
        "preset": preset,
        "presetLabel": next((label for code, label in TRUCK_PRESETS if code.upper() == preset.upper()), ""),
    }


def equipment_profile(facts: Mapping[str, Any]) -> dict[str, Any]:
    """The SEA FCL equipment list, read from the EXISTING repeatable units."""

    containers = list(facts.get("containers") or [])
    presets: list[dict[str, Any]] = []
    for code, _label in CONTAINER_PRESETS:
        if code == LOADMODEL_OTHER:
            continue
        count = sum(1 for row in containers if row.get("typeSize", "").upper() == code)
        if count:
            presets.append({"code": code, "count": count})
    other = sum(1 for row in containers
                if row.get("typeSize") and row.get("typeSize", "").upper() not in
                {code for code, _ in CONTAINER_PRESETS if code != LOADMODEL_OTHER})
    # One typed container does NOT complete a multi-container FCL booking.
    # Every already-recorded unit must have an explicit equipment type; the
    # number/type of additional, unrecorded units is never inferred.
    missing_type_count = sum(1 for row in containers if not _text(row.get("typeSize")))
    return {
        "units": containers,
        "count": len(containers),
        "presets": presets,
        "otherCount": other,
        "missingTypeCount": missing_type_count,
        "known": bool(containers) and missing_type_count == 0,
    }


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

ISSUE_INVALID_COMBINATION = "INVALID_COMBINATION"
ISSUE_UNKNOWN_INCOTERM = "UNKNOWN_INCOTERM"
ISSUE_VERSION_MISMATCH = "VERSION_MISMATCH"
ISSUE_MISSING_VERSION = "MISSING_VERSION"
ISSUE_MISSING_PLACE = "MISSING_PLACE"
ISSUE_MISSING_MODE = "MISSING_MODE"
ISSUE_MISSING_LOAD_MODEL = "MISSING_LOAD_MODEL"
ISSUE_INVALID_LOAD_MODEL = "INVALID_LOAD_MODEL"
ISSUE_MISSING_SERVICE_SCOPE = "MISSING_SERVICE_SCOPE"
ISSUE_INSURANCE_EVIDENCE = "INSURANCE_EVIDENCE_MISSING"

#: The issues that are CONFLICTS — an impossible or self-contradictory
#: configuration the operator really did state (FOB + ROAD, DAT + 2020, an
#: unrecognized term they typed, a load model from another mode). Everything
#: else is a fact that simply has not been stated YET, which is a legitimate
#: state for a NEW shipment ("bổ sung sau"): it makes the profile INCOMPLETE,
#: and it must never refuse creating the lot.
BLOCKING_WRITE_ISSUES: frozenset[str] = frozenset({
    ISSUE_INVALID_COMBINATION,
    ISSUE_VERSION_MISMATCH,
    ISSUE_INVALID_LOAD_MODEL,
})


def blocking_issues(issues: Iterable[Mapping[str, Any]],
                    facts: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
    """The subset of issues that block: they are conflicts, not open questions.

    ``UNKNOWN_INCOTERM`` only blocks when the operator actually stated something
    that could not be recognized — a BLANK contract term is the honest
    "not stated yet" state and must never be turned into an invented code (nor
    into ``CẤU HÌNH CẦN KIỂM TRA``, which is reserved for real conflicts).
    """

    facts = facts or {}
    blocking = [dict(issue) for issue in issues if issue.get("code") in BLOCKING_WRITE_ISSUES]
    if _text(facts.get("incotermRawInput")):
        blocking.extend(dict(issue) for issue in issues if issue.get("code") == ISSUE_UNKNOWN_INCOTERM)
    return blocking


#: The write gate calls the same rule by its write-side name.
blocking_write_issues = blocking_issues


def validate_profile(facts: Mapping[str, Any], *, for_write: bool = False) -> list[dict[str, Any]]:
    """Every reason the profile is not a valid execution profile.

    ``for_write=True`` is the WRITE gate: it additionally requires the operator
    facts a NEW configuration must state (version, named place, mode, load
    model where the mode has a family, an explicit service-scope confirmation).
    A historical document is NEVER validated this way — it is read with
    ``for_write=False`` so it keeps opening, honestly flagged.
    """

    issues: list[dict[str, Any]] = []
    code = _text(facts.get("incoterm"))
    version = _text(facts.get("incotermVersion"))
    mode = _text(facts.get("mode"))
    load_model = _text(facts.get("loadModel"))

    def add(kind: str, message: str) -> None:
        issues.append({"code": kind, "message": message})

    if not code:
        raw = _text(facts.get("incotermRawInput"))
        add(ISSUE_UNKNOWN_INCOTERM,
            f"Chưa nhận diện được điều kiện giao hàng “{raw}”." if raw
            else "Chưa có điều kiện giao hàng (Incoterm).")
    else:
        defining = versions_defining(code)
        if version and code not in codes_for_version(version):
            if code == "DAT":
                add(ISSUE_VERSION_MISMATCH,
                    "DAT là điều kiện của Incoterms 2010 (đã được đổi tên thành DPU trong bản 2020).")
            elif code == "DPU":
                add(ISSUE_VERSION_MISMATCH,
                    "DPU là điều kiện của Incoterms 2020 (bản 2010 dùng DAT).")
            elif code in {"DAF", "DDU"}:
                add(ISSUE_VERSION_MISMATCH,
                    f"{code} là điều kiện legacy của Incoterms 2000, không thuộc Incoterms 2010/2020.")
            else:
                add(ISSUE_VERSION_MISMATCH,
                    f"{code} không thuộc {VERSION_LABELS.get(version, version)}. "
                    f"Bản này chỉ có: {', '.join(codes_for_version(version))}.")
        elif not version and defining == (VERSION_LEGACY_2000,):
            add(ISSUE_MISSING_VERSION,
                f"{code} chỉ hợp lệ ở chế độ legacy Incoterms 2000 — cần ghi rõ phiên bản.")
        elif not version and for_write:
            # LOGI_INCOTERMS_VERSION_UX_SIMPLIFY_01: version is implicit 2020
            # for new profiles. Only legacy / DAT-type codes still require an
            # explicit version; current 2020 codes are auto-assigned.
            if code in codes_for_version(VERSION_2020):
                pass  # implicit 2020 — no missing-version error
            else:
                add(ISSUE_MISSING_VERSION, "Chưa chọn phiên bản Incoterms cho lô.")

        if mode:
            scope = rule_scope(version, code)
            if scope == SCOPE_SEA_ONLY and mode != MODE_SEA:
                add(ISSUE_INVALID_COMBINATION,
                    f"{code} chỉ áp dụng cho chặng chính đường biển / đường thủy nội địa; "
                    f"không dùng được với {MODE_LABELS.get(mode, mode)}. "
                    f"Chọn FCA/CPT/CIP/DAP/DDP nếu hàng đi {MODE_LABELS.get(mode, mode).lower()}.")

    if for_write and not mode:
        add(ISSUE_MISSING_MODE, "Chưa chọn phương thức vận chuyển.")

    if for_write and code and not _text(facts.get("incotermNamedPlace")):
        add(ISSUE_MISSING_PLACE,
            f"{code} cần đi kèm địa điểm/cảng/điểm giao cụ thể (VD: {code} · Pingxiang Warehouse).")

    if mode:
        family = load_models_for_mode(mode)
        if family and load_model and not load_model_valid_for_mode(mode, load_model):
            add(ISSUE_INVALID_LOAD_MODEL,
                f"Loại hàng “{load_model}” không thuộc {MODE_LABELS.get(mode, mode)}. "
                f"Chọn: {', '.join(code_ for code_, _ in family)}.")
        elif family and for_write and not load_model:
            add(ISSUE_MISSING_LOAD_MODEL,
                f"Chưa chọn loại hàng cho {MODE_LABELS.get(mode, mode)} "
                f"({', '.join(code_ for code_, _ in family)}).")

    if for_write and not facts.get("serviceScopeConfirmed"):
        add(ISSUE_MISSING_SERVICE_SCOPE,
            "Chưa xác nhận phạm vi Trường Thành thực hiện cho lô này.")

    if for_write:
        status = _text(facts.get("cargoInsuranceStatus"))
        if not status:
            add(ISSUE_INSURANCE_EVIDENCE,
                "Chưa xác nhận thực tế bảo hiểm hàng hóa (Chưa xác nhận / Không có / Đã có).")

    return issues


# ---------------------------------------------------------------------------
# Workflow derivation (deterministic projection — no BPM engine)
# ---------------------------------------------------------------------------

REASON_INCOTERM_EXPECTATION = "INCOTERM_EXPECTATION"
REASON_SERVICE_SCOPE = "SERVICE_SCOPE"
REASON_MODE_REQUIREMENT = "MODE_REQUIREMENT"
REASON_LOAD_MODEL_REQUIREMENT = "LOAD_MODEL_REQUIREMENT"
REASON_PERSISTED_FACT_DEPENDENCY = "PERSISTED_FACT_DEPENDENCY"

REASON_LABELS: dict[str, str] = {
    REASON_INCOTERM_EXPECTATION: "Theo điều kiện giao hàng",
    REASON_SERVICE_SCOPE: "Theo phạm vi Trường Thành",
    REASON_MODE_REQUIREMENT: "Theo phương thức vận chuyển",
    REASON_LOAD_MODEL_REQUIREMENT: "Theo loại hàng",
    REASON_PERSISTED_FACT_DEPENDENCY: "Theo dữ liệu đã ghi của lô",
}


def _stage(code: str, label: str, reason: str, *, done: bool, detail: str = "",
           prompt: str = "", mismatch: bool = False) -> dict[str, Any]:
    return {
        "code": code,
        "label": label,
        "reason": reason,
        "reasonLabel": REASON_LABELS.get(reason, reason),
        "detail": detail,
        "done": bool(done),
        #: What the operator still has to record for this stage ("" = nothing).
        "missing": "" if done else prompt,
        #: A CONFIRMED contradiction between two persisted truths (not a gap).
        "mismatch": bool(mismatch),
    }


def derive_stages(profile: Mapping[str, Any], facts: Mapping[str, Any]) -> list[dict[str, Any]]:
    """The RELEVANT operational stages of THIS shipment, each with its reason.

    A stage appears only when the profile makes it relevant: its service-scope
    segment is owned by Trường Thành, OR the mode/load model requires it, OR the
    shipment already carries the fact (so a persisted fact is never hidden by
    the UI). Nothing else is ever shown — in particular no factory pickup for a
    scope that starts at a named handoff, and no container stage for road LTL.
    """

    facts = facts or {}
    scope = list(profile.get("serviceScope") or [])
    mode = _text(profile.get("mode"))
    load_model = _text(profile.get("loadModel"))
    insurance = profile.get("insurance") or {}
    stages: list[dict[str, Any]] = []

    in_scope = lambda segment: segment in scope  # noqa: E731 - tiny local predicate

    # --- origin side: only what Trường Thành really owns -------------------
    # For ROAD + FTL the truck type IS the FTL requirement, and it is owned by
    # the load-model stage below — a second prompt for the same persisted fact
    # would just ask the operator twice ("Ghi nhận xe lấy hàng" vs "Xác nhận
    # loại xe"). Every other profile keeps its own pickup-vehicle prompt.
    ftl_owns_truck = mode == MODE_ROAD and load_model == LOADMODEL_FTL
    if in_scope(SCOPE_ORIGIN_PICKUP):
        stages.append(_stage(
            "ORIGIN_PICKUP", "Lấy hàng tại kho / nhà máy", REASON_SERVICE_SCOPE,
            done=bool(facts.get("pickupTruckType") or facts.get("trucks")),
            detail="Phạm vi Trường Thành có lấy hàng tận kho/nhà máy.",
            prompt="" if ftl_owns_truck else "Ghi nhận xe lấy hàng (loại xe / biển số)."))

    if in_scope(SCOPE_EXPORT_HANDLING) or in_scope(SCOPE_EXPORT_CUSTOMS):
        stages.append(_stage(
            "EXPORT_HANDLING", "Xử lý hàng xuất & hải quan xuất", REASON_SERVICE_SCOPE,
            done=True,
            detail="Phạm vi Trường Thành gồm xử lý xuất / khai báo hải quan xuất."))

    # --- handoff / border --------------------------------------------------
    if in_scope(SCOPE_ORIGIN_TERMINAL_OR_BORDER):
        stages.append(_stage(
            "ORIGIN_HANDOFF", "Giao hàng tại bãi / cửa khẩu đi", REASON_SERVICE_SCOPE,
            done=True, detail="Phạm vi Trường Thành gồm bàn giao tại bãi/cửa khẩu đi."))
    if in_scope(SCOPE_CROSS_BORDER_COORDINATION):
        stages.append(_stage(
            "CROSS_BORDER", "Điều phối qua biên giới", REASON_SERVICE_SCOPE,
            done=True, detail="Phạm vi Trường Thành gồm điều phối qua biên giới/chuyển tải."))

    # --- main carriage: scope OR mode/load-model requirement OR facts ------
    main_documents = bool(facts.get("bookingNo") or facts.get("carrier") or facts.get("mbl")
                          or facts.get("hbl") or facts.get("vessel") or facts.get("mawb")
                          or facts.get("hawb") or facts.get("flightNo"))
    if in_scope(SCOPE_MAIN_CARRIAGE):
        stages.append(_stage(
            "MAIN_CARRIAGE", "Chặng chính", REASON_SERVICE_SCOPE,
            done=True, detail="Phạm vi Trường Thành gồm thu xếp chặng chính."))
    elif main_documents:
        stages.append(_stage(
            "MAIN_CARRIAGE", "Chặng chính", REASON_PERSISTED_FACT_DEPENDENCY,
            done=True, detail="Lô đã có chứng từ chặng chính (booking/hãng/vận đơn)."))

    # Mode documents prompt ONLY for the carrier-side work Trường Thành really
    # owns. When the main carriage belongs to the counterparty (FOB/CIF/CFR
    # seller side) the already-recorded documents stay visible as read-only
    # evidence — no Trường Thành task is invented from them.
    owns_main = in_scope(SCOPE_MAIN_CARRIAGE)
    mode_docs_reason = REASON_MODE_REQUIREMENT if owns_main else REASON_PERSISTED_FACT_DEPENDENCY
    if mode == MODE_SEA and (owns_main or main_documents):
        if owns_main:
            missing = [label for label, value in (("hãng tàu", facts.get("carrier")),
                                                  ("số booking", facts.get("bookingNo")),
                                                  ("vận đơn (MBL/HBL)",
                                                   facts.get("mbl") or facts.get("hbl")))
                       if not value]
            prompt = ("Còn thiếu: " + ", ".join(missing)) if missing else ""
            done = not missing
        else:
            prompt, done = "", True
        stages.append(_stage(
            "SEA_DOCUMENTS", "Chứng từ đường biển", mode_docs_reason, done=done,
            detail="Hàng đi đường biển: booking / hãng tàu / vận đơn là chứng từ của chặng chính.",
            prompt=prompt))

    if mode == MODE_AIR and (owns_main or main_documents):
        if owns_main:
            # Carrier name or sea MBL/HBL alone never proves air documentation.
            # An owned air-carriage task needs both an AWB and its flight.
            missing = [label for label, present in (
                ("MAWB/HAWB", bool(facts.get("mawb") or facts.get("hawb"))),
                ("số chuyến bay", bool(facts.get("flightNo"))),
            ) if not present]
            stages.append(_stage(
                "AIR_DOCUMENTS", "Chứng từ hàng không", mode_docs_reason,
                done=not missing,
                detail="Hàng đi hàng không: MAWB/HAWB và chuyến bay là chứng từ của chặng chính.",
                prompt=("Còn thiếu: " + ", ".join(missing)) if missing else ""))
        else:
            # Outside our service scope means NO owned task, not factual proof
            # that the counterparty has actually issued a waybill or flight.
            observed = bool(facts.get("mawb") or facts.get("hawb")) and bool(facts.get("flightNo"))
            stages.append(_stage(
                "AIR_DOCUMENTS", "Chứng từ hàng không", mode_docs_reason, done=observed,
                detail="Chặng bay ngoài phạm vi Trường Thành thu xếp; chỉ ghi nhận MAWB/HAWB và chuyến bay khi có dữ liệu thực tế.",
                prompt=""))

    if mode == MODE_RAIL and (owns_main or main_documents):
        rail_known = bool(facts.get("carrier") or facts.get("mbl"))
        stages.append(_stage(
            "RAIL_CARRIAGE", "Chặng đường sắt", mode_docs_reason, done=rail_known,
            detail="Hàng đi đường sắt: tuyến, hãng và mốc ngày của chặng chính.",
            prompt="" if (rail_known or not owns_main) else "Ghi nhận tuyến/hãng đường sắt."))

    # --- load model: only where it actually applies ------------------------
    if mode == MODE_SEA and load_model == LOADMODEL_FCL:
        equipment = profile.get("equipment") or {}
        stages.append(_stage(
            "SEA_EQUIPMENT", "Thiết bị container (FCL)", REASON_LOAD_MODEL_REQUIREMENT,
            done=bool(equipment.get("known")),
            detail="FCL: container dành riêng cho lô này — ghi nhận đủ từng container/thiết bị.",
            prompt=(f"Bổ sung loại container cho {equipment['missingTypeCount']} container chưa xác nhận (20GP / 40GP / 40HC / khác)."
                    if equipment.get("missingTypeCount") else
                    "Bổ sung loại container (20GP / 40GP / 40HC / khác).")))
    elif mode == MODE_SEA and load_model == LOADMODEL_LCL:
        stages.append(_stage(
            "SEA_CONSOLIDATION", "Hàng lẻ ghép container (LCL)", REASON_LOAD_MODEL_REQUIREMENT,
            # Selecting LCL is NOT evidence that the cargo was consolidated.
            # The CFS/consolidation work lives on the Journey node; no next
            # action is invented here (prompt stays empty).
            done=bool(facts.get("seaConsolidatedAt")),
            detail="LCL: hàng ghép chung với hàng khác — lô không sở hữu nguyên container, "
                   "nên không yêu cầu số container/seal/VGM riêng. Ghép hàng chỉ hoàn thành khi có mốc thực tế."))

    if mode == MODE_ROAD and load_model == LOADMODEL_FTL:
        truck = profile.get("truck") or {}
        stages.append(_stage(
            "ROAD_TRUCK_PROFILE", "Xe tải (FTL — nguyên xe)", REASON_LOAD_MODEL_REQUIREMENT,
            done=bool(truck.get("known")),
            detail="FTL: lô đi nguyên xe — cần loại xe Trường Thành vận hành.",
            prompt="Xác nhận loại xe (17,5 m / 13,5 m / 9,6 m / 6,8 m / khác)."))
    elif mode == MODE_ROAD and load_model == LOADMODEL_LTL:
        stages.append(_stage(
            "ROAD_CONSOLIDATION", "Hàng lẻ ghép xe (LTL)", REASON_LOAD_MODEL_REQUIREMENT,
            # Selecting LTL is NOT evidence that the cargo was received and
            # consolidated; the Journey node owns that work (no invented prompt).
            done=bool(facts.get("roadConsolidatedAt")),
            detail="LTL: hàng ghép xe — không yêu cầu loại xe riêng cho đến khi có xe cụ thể."))

    # --- import side -------------------------------------------------------
    if in_scope(SCOPE_IMPORT_CUSTOMS):
        declared = bool(facts.get("customsDeclarationNo"))
        stages.append(_stage(
            "IMPORT_CUSTOMS", "Khai báo hải quan nhập", REASON_SERVICE_SCOPE,
            done=declared or (customs_clearance_confirmed(facts.get("customsStatus"))),
            detail="Phạm vi Trường Thành gồm khai báo hải quan nhập.",
            prompt="" if (declared or customs_clearance_confirmed(facts.get("customsStatus"))) else "Bổ sung số tờ khai nhập khẩu."))

    delivery_fact = bool(facts.get("delivered") or facts.get("deliveryLocation"))
    if in_scope(SCOPE_DESTINATION_TRUCKING) or in_scope(SCOPE_FINAL_DELIVERY):
        stages.append(_stage(
            "DELIVERY", "Giao hàng tận nơi", REASON_SERVICE_SCOPE,
            done=bool(facts.get("delivered")),
            detail="Phạm vi Trường Thành gồm vận chuyển nội địa / giao hàng.",
            prompt="" if facts.get("delivered") else "Ghi nhận điểm giao và xác nhận đã giao."))
    elif delivery_fact:
        stages.append(_stage(
            "DELIVERY", "Giao hàng tận nơi", REASON_PERSISTED_FACT_DEPENDENCY,
            done=bool(facts.get("delivered")),
            detail="Lô đã có dữ liệu giao hàng.", prompt=""))

    # --- insurance: the Incoterm obligation is NOT evidence ---------------
    #
    # TWO truths, and they are compared rather than merged:
    #   * the DERIVED obligation (CIF/CIP oblige the seller to arrange cover,
    #     or Trường Thành's own confirmed scope includes arranging it);
    #   * the PERSISTED actual state (UNKNOWN / NO / YES).
    # `NO` is useful EVIDENCE, not a synonym for "nothing to do": when the
    # profile required cover, an explicit NO is a CONFIRMED MISMATCH and the
    # stage stays outstanding. `NO` only settles the question when neither the
    # Incoterm nor the confirmed scope required insurance at all.
    obligation = _text(insurance.get("obligation"))
    status = _text(insurance.get("actualStatus"))
    obligation_required = obligation == INSURANCE_SELLER_REQUIRED
    scope_required = in_scope(SCOPE_CARGO_INSURANCE_ARRANGEMENT)
    needs_evidence = scope_required or obligation_required
    if needs_evidence:
        reason = REASON_SERVICE_SCOPE if scope_required else REASON_INCOTERM_EXPECTATION
        mismatch = status == ACTUAL_INSURANCE_NO
        if status == ACTUAL_INSURANCE_YES:
            done, prompt = True, ""
        elif mismatch:
            done = False
            prompt = (INSURANCE_MISMATCH_SCOPE if scope_required else INSURANCE_MISMATCH_INCOTERM)
        else:
            done, prompt = False, "Kiểm tra chứng từ bảo hiểm."
        if mismatch:
            detail = ("Phạm vi Trường Thành gồm thu xếp bảo hiểm, nhưng hồ sơ đang ghi thực tế KHÔNG CÓ bảo hiểm."
                      if scope_required
                      else "Incoterm bắt buộc người bán thu xếp bảo hiểm, nhưng hồ sơ đang ghi thực tế KHÔNG CÓ bảo hiểm.")
        else:
            detail = ("Phạm vi Trường Thành gồm thu xếp bảo hiểm." if scope_required
                      else "Incoterm bắt buộc người bán thu xếp bảo hiểm — cần kiểm tra chứng từ thực tế.")
        stages.append(_stage(
            "INSURANCE_EVIDENCE", "Chứng từ bảo hiểm hàng hóa", reason,
            done=done, detail=detail, prompt=prompt, mismatch=mismatch))

    return stages


def _conflicts_for_next_action(issues: Sequence[Mapping[str, Any]],
                               profile: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Conflicts — the SAME rule the profile state is derived from.

    A BLANK term is an open question (``PROFILE_INCOMPLETE``); a term the
    operator stated that could not be recognized is a real configuration
    problem, and the next action must agree with the state banner.
    """

    conflicts = [dict(issue) for issue in issues if issue.get("code") in BLOCKING_WRITE_ISSUES]
    if _text(profile.get("incotermRawLabel")):
        conflicts.extend(dict(issue) for issue in issues if issue.get("code") == ISSUE_UNKNOWN_INCOTERM)
    return conflicts


def derive_next_action(profile: Mapping[str, Any], stages: Sequence[Mapping[str, Any]],
                       facts: Mapping[str, Any], issues: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """The ONE next step that belongs to the RELEVANT stages of this profile."""

    def action(label: str, detail: str, *, reason: str, code: str,
               tone: str = "amber") -> dict[str, Any]:
        return {"code": code, "label": label, "detail": detail, "reason": reason,
                "reasonLabel": REASON_LABELS.get(reason, reason), "tone": tone}

    conflicts = _conflicts_for_next_action(issues, profile)
    if conflicts:
        return action("Kiểm tra cấu hình lô", conflicts[0].get("message", ""),
                      reason=REASON_INCOTERM_EXPECTATION, code="CONFIG_CHECK", tone="red")

    incomplete = list(issues)
    if incomplete:
        return action("Bổ sung hồ sơ thực hiện lô", incomplete[0].get("message", ""),
                      reason=REASON_PERSISTED_FACT_DEPENDENCY, code="PROFILE_INCOMPLETE")

    insurance_gap = next(
        (stage for stage in stages
         if stage.get("code") == "INSURANCE_EVIDENCE" and stage.get("missing")), None)

    if facts.get("delivered"):
        # A delivered lot is finished — EXCEPT when the confirmed profile still
        # owes what it was configured to obtain: an UNKNOWN insurance document
        # is NOT the honest end of the workflow, and an explicit "no insurance"
        # under a CIF/CIP obligation (or under Trường Thành's own confirmed
        # scope) is a CONFIRMED MISMATCH, never a finished lot.
        if insurance_gap is not None:
            return action(insurance_gap["missing"], insurance_gap.get("detail", ""),
                          reason=str(insurance_gap.get("reason")),
                          code=str(insurance_gap.get("code")),
                          tone="red" if insurance_gap.get("mismatch") else "amber")
        return action("Hoàn thành", "Lô đã được xác nhận giao hàng.",
                      reason=REASON_PERSISTED_FACT_DEPENDENCY, code="DONE", tone="green")

    # The load-model requirement is asked for FIRST when it is still unmet: for
    # FCL the container type determines the booking itself, so demanding the
    # carriage documents first would ask the operator for an answer they cannot
    # have yet. Every other requirement keeps the operational stage order.
    unmet = [stage for stage in stages if stage.get("missing")]
    ordered = ([stage for stage in unmet if stage.get("reason") == REASON_LOAD_MODEL_REQUIREMENT]
               + [stage for stage in unmet if stage.get("reason") != REASON_LOAD_MODEL_REQUIREMENT])
    for stage in ordered:
        return action(stage["missing"], stage.get("detail", ""),
                      reason=str(stage.get("reason")), code=str(stage.get("code")),
                      tone="red" if stage.get("mismatch") else "amber")

    return action("Theo dõi lô theo hồ sơ đã xác nhận",
                  "Mọi bước thuộc phạm vi Trường Thành đã có dữ liệu.",
                  reason=REASON_PERSISTED_FACT_DEPENDENCY, code="MONITOR", tone="blue")


# ---------------------------------------------------------------------------
# The one projection
# ---------------------------------------------------------------------------

STATE_READY = "PROFILE_READY"
STATE_INCOMPLETE = "PROFILE_INCOMPLETE"
STATE_CONFIG_CHECK = "CONFIG_CHECK"

STATE_LABELS: dict[str, str] = {
    STATE_READY: "Hồ sơ lô đã đủ",
    STATE_INCOMPLETE: "Hồ sơ lô còn thiếu",
    STATE_CONFIG_CHECK: "CẤU HÌNH CẦN KIỂM TRA",
}


def build_execution_profile(shipment: Mapping[str, Any] | None, *,
                            legs: Sequence[Mapping[str, Any]] | None = None) -> dict[str, Any]:
    """Project ONE shipment document into its execution profile.

    Pure and deterministic. A legacy document carrying only ``mode`` +
    ``incoterm`` projects as ``PROFILE_INCOMPLETE`` with blank version/place/
    load-model/scope/insurance — never as an invented configuration.
    """

    shipment = shipment or {}
    cfg = profile_facts(shipment)
    facts = persisted_facts(shipment, legs=legs)
    issues = validate_profile(cfg, for_write=False)

    mode = cfg["mode"]
    load_model = cfg["loadModel"]
    insurance = incoterm_insurance(cfg["incoterm"], cfg["incotermVersion"])
    insurance["actualStatus"] = cfg["cargoInsuranceStatus"] or ACTUAL_INSURANCE_UNKNOWN
    insurance["actualStatusLabel"] = ACTUAL_INSURANCE_LABELS[insurance["actualStatus"]]
    insurance["actualStatusStated"] = bool(cfg["cargoInsuranceStatus"])
    insurance["evidence"] = {
        "arrangedBy": cfg["cargoInsuranceArrangedBy"],
        "insurerName": cfg["cargoInsuranceInsurer"],
        "policyNo": cfg["cargoInsurancePolicyNo"],
        "coverageNote": cfg["cargoInsuranceCoverageNote"],
    }

    truck = truck_profile(facts)
    equipment = equipment_profile(facts)

    profile: dict[str, Any] = {
        "mode": mode,
        "storedMode": cfg["storedMode"],
        "modeLabel": MODE_LABELS.get(mode, ""),
        "incoterm": cfg["incoterm"],
        "incotermVersion": cfg["incotermVersion"],
        "incotermVersionLabel": VERSION_LABELS.get(cfg["incotermVersion"], ""),
        "incotermNamedPlace": cfg["incotermNamedPlace"],
        "incotermPlaceSource": cfg["incotermPlaceSource"],
        "incotermRawLabel": cfg["incotermRawLabel"],
        "incotermAliasNote": cfg["incotermAliasNote"],
        "incotermRuleScope": rule_scope(cfg["incotermVersion"], cfg["incoterm"]) if cfg["incoterm"] else "",
        "loadModel": load_model,
        "loadModelLabel": load_model_label(mode, load_model),
        "serviceScope": cfg["serviceScope"],
        "serviceScopeLabels": [SCOPE_LABELS[code] for code in cfg["serviceScope"]],
        "serviceScopeSummary": scope_summary(cfg["serviceScope"]),
        "serviceScopeConfirmed": cfg["serviceScopeConfirmed"],
        "insurance": insurance,
        "truck": truck,
        "equipment": equipment,
        "issues": issues,
    }

    if cfg["incoterm"] and not cfg["incotermVersion"]:
        # A legacy document (or a contract that simply never stated a version)
        # is incomplete, not wrong. It is never silently upgraded to 2020.
        if not any(issue["code"] == ISSUE_INVALID_COMBINATION for issue in issues):
            issues.append({
                "code": ISSUE_MISSING_VERSION,
                "message": "Chưa xác nhận phiên bản Incoterms của lô (2010 / 2020 / legacy 2000).",
            })
    if cfg["incoterm"] and not cfg["incotermNamedPlace"] and not any(
            issue["code"] in {ISSUE_UNKNOWN_INCOTERM, ISSUE_VERSION_MISMATCH} for issue in issues):
        issues.append({
            "code": ISSUE_MISSING_PLACE,
            "message": f"{cfg['incoterm']} chưa có địa điểm/cảng/điểm giao cụ thể.",
        })
    profile["issues"] = issues

    if blocking_issues(issues, cfg):
        profile["state"] = STATE_CONFIG_CHECK
    elif issues:
        profile["state"] = STATE_INCOMPLETE
    else:
        profile["state"] = STATE_READY
    profile["stateLabel"] = STATE_LABELS[profile["state"]]

    stages = derive_stages(profile, facts)
    profile["stages"] = stages
    profile["persisted"] = facts
    profile["nextAction"] = derive_next_action(profile, stages, facts, issues)
    profile["summaryLines"] = summary_lines(profile)
    return profile


def summary_lines(profile: Mapping[str, Any]) -> list[str]:
    """The compact profile summary the detail header shows.

    LOGI_INCOTERMS_VERSION_UX_SIMPLIFY_01: ordinary new profile (2020) shows
    just ``FCA`` — no ``Incoterms 2020`` waste. Historical non-2020 shows a
    small contextual version note (e.g. ``FCA · Incoterms 2010``).
    Unknown halves are simply absent — never rendered as an invented value.
    """

    lines: list[str] = []
    code = _text(profile.get("incoterm"))
    raw = _text(profile.get("incotermRawLabel"))
    version = _text(profile.get("incotermVersion"))
    if code:
        # Version 2020 is the implicit current standard — do not waste space.
        # Show version only for historical non-current records (2010 / legacy).
        if version in (VERSION_2010, VERSION_LEGACY_2000):
            incoterm_line = f"{code} · {VERSION_LABELS.get(version, version)}"
        else:
            incoterm_line = code
        if raw and raw.upper() != code:
            incoterm_line += f" (hợp đồng ghi: {raw})"
        lines.append(incoterm_line)
    elif raw:
        lines.append(f"Chưa nhận diện: {raw}")

    place = _text(profile.get("incotermNamedPlace"))
    if place:
        if _text(profile.get("incotermPlaceSource")) == "CONTRACT_LABEL":
            # The place was read from the contract wording ("CIF Hai Phong"),
            # never confirmed — the summary says so instead of implying it.
            place = f"{place} (đọc từ hợp đồng — cần xác nhận)"
        lines.append(place)

    mode = _text(profile.get("mode"))
    load_model = _text(profile.get("loadModel"))
    transport = MODE_LABELS.get(mode, "")
    if load_model:
        transport = f"{transport} · {load_model}" if transport else load_model
    equipment = profile.get("equipment") or {}
    if mode == MODE_SEA and load_model == LOADMODEL_FCL and equipment.get("count"):
        parts = [f"{row['count']} × {row['code']}" for row in equipment.get("presets") or []]
        if equipment.get("otherCount"):
            parts.append(f"{equipment['otherCount']} × khác")
        if parts:
            transport = f"{transport} · {', '.join(parts)}"
    if transport:
        lines.append(transport)

    scope = _text(profile.get("serviceScopeSummary"))
    lines.append(f"Phạm vi TT: {scope}" if scope else "Phạm vi TT: chưa xác nhận")

    insurance = profile.get("insurance") or {}
    obligation = _text(insurance.get("obligation"))
    status_label = _text(insurance.get("actualStatusLabel"))
    status = _text(insurance.get("actualStatus"))
    scope_requires = SCOPE_CARGO_INSURANCE_ARRANGEMENT in (_text(item) for item in
                                                           (profile.get("serviceScope") or []))
    mismatch = status == ACTUAL_INSURANCE_NO and (
        obligation == INSURANCE_SELLER_REQUIRED or scope_requires)
    if obligation == INSURANCE_SELLER_REQUIRED:
        clause = _text(insurance.get("clauseLabel"))
        lines.append("Bảo hiểm theo Incoterm: người bán phải thu xếp"
                     + (f" ({clause})" if clause else ""))
        lines.append(f"Chứng từ bảo hiểm: {status_label}")
    else:
        lines.append(f"Bảo hiểm hàng hóa: {status_label}")
    if mismatch:
        lines.append(INSURANCE_MISMATCH_LABEL)
    return lines


def projection_options() -> dict[str, Any]:
    """The option catalog the client renders — generated from THIS module.

    The client needs the matrices locally (a Streamlit re-run per keystroke
    would be absurd), so the options are handed to it inside the projection
    instead of being re-typed in TypeScript. ``scripts/gen_execution_profile_catalog.py``
    emits exactly this payload as the client catalog, and the test suite pins
    the two against each other.
    """

    return {
        "versions": [{"code": code, "label": VERSION_LABELS[code]} for code in INCOTERM_VERSIONS],
        "rules": {
            version: [{"code": code, "scope": scope} for code, scope in rules]
            for version, rules in INCOTERM_RULES.items()
        },
        "codes": list(ALL_CODES),
        "aliases": dict(INCOTERM_ALIASES),
        "modes": [
            {"code": code, "label": MODE_LABELS[code], "stored": STORED_MODE_BY_CANONICAL[code]}
            for code in CANONICAL_MODES
        ],
        "loadModels": {
            mode: [{"code": code, "label": label} for code, label in family]
            for mode, family in LOAD_MODELS_BY_MODE.items()
        },
        "truckPresets": [{"code": code, "label": label} for code, label in TRUCK_PRESETS],
        "containerPresets": [{"code": code, "label": label} for code, label in CONTAINER_PRESETS],
        "serviceScope": [
            {"code": code, "label": label, "short": short}
            for code, label, short in SERVICE_SCOPE_SEGMENTS
        ],
        "insuranceStatuses": [
            {"code": code, "label": ACTUAL_INSURANCE_LABELS[code]}
            for code in ACTUAL_INSURANCE_STATES
        ],
    }


def write_issues(payload: Mapping[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    """Validate ONE operator profile submission. Returns ``(facts, issues, normalized)``.

    Used by the bounded write handler: a NEW configuration must be complete and
    structurally possible before anything is written, and impossible
    combinations are REFUSED with the explanation the UI shows — never silently
    corrected, never partially saved.
    """

    raw_incoterm = payload.get("incoterm")
    normalized = normalize_incoterm(raw_incoterm)
    if not normalized["recognized"] and raw_incoterm:
        # A free-text rule is only accepted when it carries raw contract
        # evidence; the code itself must normalize onto a real ICC rule.
        normalized = {"code": "", "rawLabel": _text(raw_incoterm), "aliasNote": "", "recognized": False}

    version = _text(payload.get("incotermVersion"))
    insurance_payload = payload.get("cargoInsurance")
    insurance_payload = insurance_payload if isinstance(insurance_payload, Mapping) else {}
    actual_status = _text(insurance_payload.get("status")).upper()

    facts: dict[str, Any] = {
        "mode": canonical_mode(payload.get("mode")),
        "storedMode": _text(payload.get("mode")),
        "incoterm": normalized["code"],
        "incotermRawInput": _text(raw_incoterm),
        "incotermRawLabel": normalized["rawLabel"],
        "incotermVersion": version if version in INCOTERM_VERSIONS else "",
        "incotermNamedPlace": _text(payload.get("namedPlace")),
        "loadModel": _text(payload.get("loadModel")).upper(),
        "serviceScope": normalize_service_scope(payload.get("serviceScope")),
        "serviceScopeConfirmed": bool(payload.get("serviceScopeConfirmed")),
        "cargoInsuranceStatus": actual_status if actual_status in ACTUAL_INSURANCE_STATES else "",
        "cargoInsuranceArrangedBy": _text(insurance_payload.get("arrangedBy")),
        "cargoInsuranceInsurer": _text(insurance_payload.get("insurerName")),
        "cargoInsurancePolicyNo": _text(insurance_payload.get("policyNo")),
        "cargoInsuranceCoverageNote": _text(insurance_payload.get("coverageNote")),
    }

    issues = validate_profile(facts, for_write=True)
    if actual_status and actual_status not in ACTUAL_INSURANCE_STATES:
        issues.append({"code": ISSUE_INSURANCE_EVIDENCE,
                       "message": "Trạng thái bảo hiểm thực tế không hợp lệ."})
    if facts["cargoInsuranceStatus"] != ACTUAL_INSURANCE_YES:
        # Insurance evidence only exists behind an explicit YES; a NO/UNKNOWN
        # never silently keeps policy details from an earlier state.
        facts.update({
            "cargoInsuranceArrangedBy": "",
            "cargoInsuranceInsurer": "",
            "cargoInsurancePolicyNo": "",
            "cargoInsuranceCoverageNote": "",
        })
    return facts, issues, normalized


def profile_document(facts: Mapping[str, Any]) -> dict[str, Any]:
    """The persisted ``data.0.0.execution_profile`` block for validated facts.

    Only operator-confirmed facts are written. Blank stays blank (UNKNOWN is
    never written as a value, and never as a default such as 2020 or EXW).
    """

    block: dict[str, Any] = {
        "incoterm_version": _text(facts.get("incotermVersion")),
        "incoterm_named_place": _text(facts.get("incotermNamedPlace")),
        "load_model": _text(facts.get("loadModel")).upper(),
        "service_scope": list(normalize_service_scope(facts.get("serviceScope"))),
        "service_scope_confirmed": bool(facts.get("serviceScopeConfirmed")),
        "cargo_insurance": {
            "status": _text(facts.get("cargoInsuranceStatus")) or ACTUAL_INSURANCE_UNKNOWN,
            "arranged_by": _text(facts.get("cargoInsuranceArrangedBy")),
            "insurer_name": _text(facts.get("cargoInsuranceInsurer")),
            "policy_or_certificate_number": _text(facts.get("cargoInsurancePolicyNo")),
            "coverage_or_notes": _text(facts.get("cargoInsuranceCoverageNote")),
        },
    }
    raw_label = _text(facts.get("incotermRawLabel"))
    code = _text(facts.get("incoterm"))
    # Raw contract wording survives as evidence ONLY when it really differs.
    if raw_label and raw_label.upper() != code.upper():
        block["incoterm_raw_label"] = raw_label
    return block
