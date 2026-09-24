from __future__ import annotations

from datetime import date

import mongomock

from core.cost_intelligence import (
    parse_cost_rate_text,
    prepare_rate_snapshot,
)
from core import database as dbmod


OWNER_RATE_SAMPLE = """NINGBO - HPH
COSCO USD 1300/40HQ 有效期到9.30
SNL 没仓位
---
THC $130/20GP $205/40HQ
REFUND 21$/RT
BUY EXPORT:100$/SET + TAX
O/F: USD1425/40HQ ETD 21/09/2026 COSCO
"""


def _catalog():
    return {
        "P-HPH": {
            "id": "P-HPH", "kind": "PLACE", "code": "VNHPH", "name": "Hải Phòng",
            "aliases": ["HPH", "HAIPHONG"], "zone_ids": ["ZONE-HPH"], "active": True,
        },
        "P-NAN": {
            "id": "P-NAN", "kind": "PLACE", "code": "CNNAN", "name": "Nansha",
            "aliases": ["HANGSHA"], "zone_ids": ["ZONE-PRD"], "active": True,
        },
        "P-NGB": {
            "id": "P-NGB", "kind": "PLACE", "code": "CNNGB", "name": "Ningbo",
            "aliases": ["NINGBO"], "zone_ids": ["ZONE-NGB"], "active": True,
        },
        "C-COSCO": {
            "id": "C-COSCO", "kind": "CARRIER", "code": "COSCO", "name": "COSCO",
            "aliases": ["COSCO SHIPPING"], "active": True,
        },
        "S-OF": {
            "id": "S-OF", "kind": "SERVICE", "code": "OF", "name": "Ocean Freight",
            "aliases": ["O/F"], "active": True,
        },
    }


def test_owner_rate_fixture_preserves_no_space_credit_tax_and_multi_equipment():
    parsed = parse_cost_rate_text(
        OWNER_RATE_SAMPLE,
        catalog=_catalog(),
        received_on=date(2026, 9, 24),
    )
    rows = parsed["rows"]

    no_space = next(row for row in rows if row["status"] == "NO_SPACE")
    assert no_space["carrier"]["name"] == "SNL"
    assert "amount" not in no_space, "NO_SPACE must never become a zero-price line"

    thc = [row for row in rows if row.get("chargeLabel") == "THC"]
    assert {(row["amount"], row["equipment"]) for row in thc} == {(130.0, "20GP"), (205.0, "40HQ")}

    refund = next(row for row in rows if row["kind"] == "CREDIT")
    assert refund["amount"] == 21.0
    assert refund["currency"] == "USD"
    assert refund["unit"] == "RT"

    buy = next(row for row in rows if row.get("chargeLabel") == "BUY EXPORT")
    assert buy["amount"] == 100.0
    assert buy["taxQualifier"] == "PLUS_TAX"

    cosco = next(row for row in rows if row.get("amount") == 1300.0)
    assert cosco["validUntil"] == "2026-09-30"
    assert cosco["destination"]["id"] == "P-HPH"

    ocean = next(row for row in rows if row.get("amount") == 1425.0)
    assert ocean["chargeId"] == "S-OF"
    assert ocean["chargeLabel"] == "Ocean Freight"
    assert ocean["etd"] == "2026-09-21"


def test_mixed_historical_sections_keep_their_own_source_dates_and_validity():
    parsed = parse_cost_rate_text(
        """NINGBO - HPH
O/F:USD1425/40HQ ETD:21/09/2026 COSCO
---
SHENZHEN - HPH
REFUND 21$/RT
28/12/2024
""",
        catalog=_catalog(),
        received_on=date(2026, 9, 24),
    )
    ocean = next(row for row in parsed["rows"] if row.get("amount") == 1425.0)
    refund = next(row for row in parsed["rows"] if row.get("kind") == "CREDIT")
    assert ocean.get("sourceDate") == ""
    assert refund.get("sourceDate") == "2024-12-28"

    # A line-specific validity must not leak into a later carrier rate.
    validity = parse_cost_rate_text(
        """NINGBO - HPH
COSCO USD 1300/40HQ 有效期到9.30
MSK USD 1200/40HQ
""",
        catalog=_catalog(),
        received_on=date(2026, 9, 24),
    )
    cosco = next(row for row in validity["rows"] if row.get("amount") == 1300.0)
    msk = next(row for row in validity["rows"] if row.get("amount") == 1200.0)
    assert cosco.get("validUntil") == "2026-09-30"
    assert msk.get("validUntil") == ""


def test_rmb_is_canonical_cny_and_unknown_no_space_requires_review():
    rmb = parse_cost_rate_text(
        "电放费 RMB500/SET",
        catalog=_catalog(),
        received_on=date(2026, 9, 24),
    )
    assert rmb["rows"][0]["amount"] == 500.0
    assert rmb["rows"][0]["currency"] == "CNY"

    unknown = parse_cost_rate_text(
        "ABC LINE 没仓位",
        catalog=_catalog(),
        received_on=date(2026, 9, 24),
    )
    assert unknown["rows"][0]["status"] == "NO_SPACE"
    assert unknown["rows"][0]["confidence"] == "NEEDS_REVIEW"
    assert unknown["summary"]["needsReview"] == 1


def test_priced_line_carrier_does_not_leak_into_following_local_charges():
    parsed = parse_cost_rate_text(
        "NINGBO - HPH\nO/F:USD1425/40HQ ETD:21/09/2026 COSCO\nUSD1200/40HQ ETD:27/09 MSK\nLOCAL:285$/40’\nDOC:75$/SET",
        catalog=_catalog(),
        received_on=date(2026, 9, 24),
    )
    rows = parsed["rows"]
    assert rows[0]["carrier"]["name"] == "COSCO"
    assert rows[1]["carrier"]["name"] == "MSK"
    assert rows[2]["carrier"]["name"] == ""
    assert rows[3]["carrier"]["name"] == ""


def test_dynamic_equipment_unit_and_legacy_service_aliases_are_operational():
    catalog = {
        **_catalog(),
        "EQ-45": {
            "id": "EQ-45", "kind": "EQUIPMENT", "code": "45HQ", "name": "45HQ",
            "aliases": ["45HC"], "active": True,
        },
        "UNIT-WM": {
            "id": "UNIT-WM", "kind": "UNIT", "code": "WM", "name": "W/M",
            "aliases": ["WM"], "active": True,
        },
        "S-NEW": {
            "id": "S-NEW", "kind": "SERVICE", "code": "OCEAN-FCL",
            "name": "Ocean Freight", "aliases": [], "legacy_codes": ["OF20"], "active": True,
        },
    }

    equipment = parse_cost_rate_text(
        "NINGBO - HPH\nOF20 USD 1,250/45HC",
        catalog=catalog,
        received_on=date(2026, 9, 24),
    )["rows"][0]
    assert equipment["chargeId"] == "S-NEW"
    assert equipment["chargeLabel"] == "Ocean Freight"
    assert equipment["equipment"] == "45HQ"
    assert equipment["amount"] == 1250.0

    unit = parse_cost_rate_text(
        "CFS USD 12/WM",
        catalog=catalog,
        received_on=date(2026, 9, 24),
    )["rows"][0]
    assert unit["unit"] == "WM"
    assert unit["amount"] == 12.0


def test_standalone_source_date_is_preserved_and_used_by_snapshot_fallback():
    parsed = parse_cost_rate_text(
        "SHENZHEN - HPH\nCFS:10$/RT\n28/12/2024",
        catalog=_catalog(),
        received_on=date(2026, 9, 24),
    )
    assert parsed["sourceDate"] == "2024-12-28"

    snapshot = prepare_rate_snapshot(
        {"parsed": parsed, "supplier": "historical agent"},
        actor="sale.test",
    )
    assert snapshot["received_at"] == "2024-12-28T00:00:00Z"


def test_backend_refuses_snapshot_with_unresolved_review_rows():
    parsed = parse_cost_rate_text(
        "HANGSHA - HPH\nUSD 900/40'",
        catalog={key: value for key, value in _catalog().items() if key != "P-NAN"},
        received_on=date(2026, 9, 24),
    )
    assert parsed["summary"]["needsReview"] > 0

    try:
        prepare_rate_snapshot({"parsed": parsed}, actor="sale.test")
    except ValueError as exc:
        assert "cần xác nhận" in str(exc)
    else:
        raise AssertionError("backend accepted unresolved rate rows")


def test_learned_place_alias_is_reused_without_guessing():
    parsed = parse_cost_rate_text(
        "HANGSHA - HPH\nUSD 900/20GP",
        catalog=_catalog(),
        received_on=date(2026, 9, 24),
    )
    row = parsed["rows"][0]
    assert row["origin"]["id"] == "P-NAN"
    assert row["origin"]["name"] == "Nansha"
    assert row["origin"]["state"] == "CONFIRMED"
    assert row["destination"]["id"] == "P-HPH"


def test_rate_snapshot_preserves_raw_multiline_evidence():
    parsed = parse_cost_rate_text(
        "NINGBO - HPH\nUSD 750/20GP",
        catalog=_catalog(),
        received_on=date(2026, 9, 24),
    )
    snapshot = prepare_rate_snapshot(
        {"parsed": parsed, "supplier": "OOCL", "receivedAt": "2026-09-24T08:00:00Z"},
        actor="sale.test",
    )
    assert snapshot["raw_text"] == "NINGBO - HPH\nUSD 750/20GP"
    assert snapshot["record_type"] == "SUPPLIER_RATE_SNAPSHOT"
    assert snapshot["created_by"] == "sale.test"


def test_cost_rate_snapshot_is_insert_only_and_idempotent(monkeypatch):
    client = mongomock.MongoClient()
    database = client["cost_test"]
    database.rate_cards.create_index("id", unique=True)

    monkeypatch.setattr(dbmod, "get_db", lambda: database)
    monkeypatch.setattr(dbmod, "_require_business_permission", lambda *args, **kwargs: True)
    monkeypatch.setattr(dbmod, "_audit", lambda *args, **kwargs: None)

    base = {
        "id": "RATE-IMMUTABLE-1",
        "record_type": "SUPPLIER_RATE_SNAPSHOT",
        "status": "ACTIVE",
        "received_at": "2026-09-24T08:00:00Z",
        "supplier": "OOCL",
        "raw_text": "USD 750/20GP",
        "rows": [{"amount": 750.0, "currency": "USD", "equipment": "20GP"}],
    }
    assert dbmod.save_cost_rate_snapshot(base)
    assert dbmod.save_cost_rate_snapshot(base), "exact replay should be idempotent"
    assert database.rate_cards.count_documents({"id": base["id"]}) == 1

    changed = {**base, "rows": [{"amount": 999.0, "currency": "USD", "equipment": "20GP"}]}
    assert not dbmod.save_cost_rate_snapshot(changed), "same id with changed facts must not overwrite history"
    stored = database.rate_cards.find_one({"id": base["id"]})
    assert stored["rows"][0]["amount"] == 750.0


def test_catalog_rejects_ambiguous_alias_and_invalid_merge(monkeypatch):
    client = mongomock.MongoClient()
    database = client["cost_test"]
    database.cost_catalog.create_index("id", unique=True)

    monkeypatch.setattr(dbmod, "get_db", lambda: database)
    monkeypatch.setattr(dbmod, "_require_business_permission", lambda *args, **kwargs: True)
    monkeypatch.setattr(dbmod, "_audit", lambda *args, **kwargs: None)

    assert dbmod.save_cost_catalog_entry({
        "id": "PLACE-HPH",
        "kind": "PLACE",
        "code": "VNHPH",
        "name": "Hải Phòng",
        "aliases": ["HPH"],
    })

    assert not dbmod.save_cost_catalog_entry({
        "id": "PLACE-OTHER",
        "kind": "PLACE",
        "code": "VNXXX",
        "name": "Điểm khác",
        "aliases": ["HPH"],
    })
    assert "PLACE-HPH" in dbmod.get_last_db_error()

    assert not dbmod.save_cost_catalog_entry({
        "id": "PLACE-SELF",
        "kind": "PLACE",
        "code": "SELF",
        "name": "Self",
        "mergedInto": "PLACE-SELF",
        "active": False,
    })
    assert "chính nó" in dbmod.get_last_db_error()

    assert dbmod.save_cost_catalog_entry({
        "id": "SERVICE-1",
        "kind": "SERVICE",
        "code": "OF",
        "name": "Ocean Freight",
        "aliases": [],
    })
    assert not dbmod.save_cost_catalog_entry({
        "id": "PLACE-MERGE",
        "kind": "PLACE",
        "code": "MERGE",
        "name": "Merge test",
        "active": False,
        "mergedInto": "SERVICE-1",
    })
    assert "cùng loại" in dbmod.get_last_db_error()


def test_master_code_can_change_without_changing_stable_identity(monkeypatch):
    client = mongomock.MongoClient()
    database = client["cost_test"]
    database.cost_catalog.create_index("id", unique=True)

    monkeypatch.setattr(dbmod, "get_db", lambda: database)
    monkeypatch.setattr(dbmod, "_require_business_permission", lambda *args, **kwargs: True)
    monkeypatch.setattr(dbmod, "_audit", lambda *args, **kwargs: None)

    first = {
        "id": "CAT-SVC-1", "kind": "SERVICE", "code": "OF20",
        "name": "Cước biển", "aliases": ["O/F"], "unit": "CONT",
    }
    renamed = {
        **first, "code": "OCEAN-FCL", "name": "Ocean Freight",
        "aliases": ["O/F", "CƯỚC BIỂN"],
    }
    assert dbmod.save_cost_catalog_entry(first)
    assert dbmod.save_cost_catalog_entry(renamed)

    docs = list(database.cost_catalog.find({}, {"_id": 0}))
    assert len(docs) == 1
    assert docs[0]["id"] == "CAT-SVC-1"
    assert docs[0]["code"] == "OCEAN-FCL"
    assert "O/F" in docs[0]["aliases"]
