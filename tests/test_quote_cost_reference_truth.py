"""PR205: the actual component read must not turn unknown booked cost into 0.

Only mongomock, injected into the existing reader; not real Mongo acceptance.
Historical stored records, canonical selling/profit arithmetic, and the
DEFAULT writer normalization remain untouched.
"""
from copy import deepcopy

import mongomock
import pytest

from core.database import repair_data
from core.logic import calculate_from_shipment
from views.logi_view_model import load_shipments
from views.logi_real_data import finance_projection


def source(cost=None, **extra):
    return {"id": "COST-TRUTH", "currency": "VND", "quote_id": "QUOTE-SELL40", "data": {
        "0.0": {"incoterm": "EXW", "mode": "Sea"},
        "3.4": {"details": [{"id": "actual-1", "name_full": "Synthetic actual", "price": 40000000,
                              "qty": 1, "unit": "CONT", "cost": cost, "vat_line": 0, **extra}], "payments": []},
    }}


def read(doc):
    db = mongomock.MongoClient()["pr205_test_only"]
    db.shipments.insert_one(deepcopy(doc))
    before = db.shipments.find_one({"id": doc["id"]}, {"_id": 0})
    loaded = load_shipments(db=db)[doc["id"]]
    assert db.shipments.find_one({"id": doc["id"]}, {"_id": 0}) == before
    # Read-only metadata/UNKNOWN retention must not alter historical arithmetic.
    legacy = repair_data({doc["id"]: doc})[doc["id"]]
    assert calculate_from_shipment(loaded) == calculate_from_shipment(legacy)
    assert loaded["data"]["3.4"]["profit"] == legacy["data"]["3.4"]["profit"]
    projected = finance_projection(loaded, {"QUOTE-SELL40": {"lines": [{"name": "SELL", "amount": 40000000, "currency": "VND"}]}})
    assert projected["actual"][0]["price"] == projected["actual"][0]["amount"] == 40000000
    assert projected["quote"][0]["amount"] == 40000000
    return loaded, projected


@pytest.mark.parametrize("unknown", [None, "", "  ", "UNKNOWN", False, "NaN"])
def test_unknown_cost_survives_real_component_read_without_zero_or_sell_fallback(unknown):
    doc = source(unknown)
    before = deepcopy(doc)
    loaded, projected = read(doc)
    assert loaded["data"]["3.4"]["details"][0]["cost"] is None
    assert projected["actual"][0]["cost"] is None
    assert doc == before


@pytest.mark.parametrize("cost", [0, "0", 32000000, "32.000.000", "32,000,000"])
def test_explicit_zero_and_true_buy_cost_survive_with_unit_and_currency(cost):
    _, projected = read(source(cost))
    row = projected["actual"][0]
    assert row["cost"] == (0 if cost in (0, "0") else 32000000)
    assert row["ccy"] == "VND" and row["unit"] == "CONT"


def test_absent_cost_and_legacy_buy_alias_are_not_sell_aliases():
    doc = source()
    del doc["data"]["3.4"]["details"][0]["cost"]
    _, projected = read(doc)
    assert projected["actual"][0]["cost"] is None
    doc["data"]["3.4"]["details"][0]["price_in"] = 32000000
    _, projected = read(doc)
    assert projected["actual"][0]["cost"] == 32000000


def test_unknown_source_currency_is_not_defaulted_to_vnd_for_cost_reference():
    doc = source(32000000)
    del doc["currency"]
    _, projected = read(doc)
    assert projected["actual"][0]["ccy"] == ""


def test_explicit_book_currency_is_a_valid_actual_cost_basis():
    doc = source(32000000)
    del doc["currency"]
    doc["data"]["3.4"]["currency"] = "USD"
    _, projected = read(doc)
    assert projected["actual"][0]["ccy"] == "USD"


@pytest.mark.parametrize("cost", [None, 0])
def test_legacy_service_columns_retain_unknown_vs_explicit_zero(cost):
    doc = source()
    finance = doc["data"]["3.4"]
    finance["details"] = []
    finance.update({"DV_1": "Legacy synthetic service", "Thu_1": 40000000, "Chi_1": cost})
    _, projected = read(doc)
    assert projected["actual"][0]["cost"] == cost
    assert projected["actual"][0]["unit"] == "", "never invent a missing legacy unit"


def test_default_normalization_is_unchanged_for_canonical_writers():
    doc = source(None)
    old = repair_data({doc["id"]: doc})[doc["id"]]
    assert old["data"]["3.4"]["details"][0]["cost"] == 0
    assert "_cost_reference_currency" not in old["data"]["3.4"]
