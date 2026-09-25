"""Issue #115 — Freightos public marketplace benchmark for Kho giá vốn.

Deterministic tests. No live Freightos. The live CNNGB→VNHPH canary is
coverage evidence only; production always fetches the provider response.
"""
from __future__ import annotations

from datetime import datetime, timezone

from core.freightos_marketplace import (
    FREIGHTOS_ATTRIBUTION_URL,
    FREIGHTOS_CALCULATOR_URL,
    compare_internal,
    fetch_public_estimate,
    map_load_type,
    marketplace_params,
    normalize_marketplace_response,
)
from views.logi_cost_intelligence import handle_cost_market_benchmark_fetch
from views import logi_c1
from views import logi_view_model as vm


class DummyResponse:
    def __init__(self, status_code, payload=None):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        if self._payload is None:
            raise ValueError("not json")
        return self._payload


def _clock():
    return datetime(2026, 9, 25, 4, 30, tzinfo=timezone.utc)


def _available_payload(min_amount=891, max_amount=1146, num_quotes=1):
    return {
        "response": {
            "_comment": ["© Freightos Ltd"],
            "estimatedFreightRates": {
                "numQuotes": num_quotes,
                "mode": {
                    "mode": "FCL",
                    "price": {
                        "min": {"moneyAmount": {"amount": min_amount, "currency": "USD"}},
                        "max": {"moneyAmount": {"amount": max_amount, "currency": "USD"}},
                    },
                    "transitTimes": {"unit": "days", "min": 3, "max": 24},
                },
            },
        }
    }


def test_equipment_maps_20gp_and_40hq_not_generic_40():
    assert map_load_type("20GP") == "container20"
    assert map_load_type("20'") == "container20"
    assert map_load_type("40HQ") == "container40HC"
    assert map_load_type("40HC") == "container40HC"
    assert map_load_type("40GP") == "container40"
    assert map_load_type("40'") == "container40"
    assert map_load_type("THC") is None
    assert map_load_type("") is None


def test_marketplace_params_never_send_estimate_true():
    params = marketplace_params("CNNGB", "VNHPH", "container40HC")
    assert params["origin"] == "CNNGB"
    assert params["destination"] == "VNHPH"
    assert params["loadtype"] == "container40HC"
    assert params["quantity"] == 1
    assert params["format"] == "json"
    assert "estimate" not in params


def test_normalize_does_not_invent_missing_price_fields():
    out = normalize_marketplace_response(
        {"response": {"estimatedFreightRates": {"numQuotes": 1, "mode": {"mode": "FCL"}}}},
        origin="CNNGB",
        destination="VNHPH",
        equipment="40HQ",
        load_type="container40HC",
        fetched_at="2026-09-25T04:30:00Z",
    )
    assert out["status"] == "NO_COVERAGE"
    assert "minAmount" not in out
    assert "maxAmount" not in out
    assert "currency" not in out
    assert out["numQuotes"] == 1
    assert out["mode"] == "FCL"


def test_empty_quotes_are_no_coverage():
    out = normalize_marketplace_response(
        {"response": {"estimatedFreightRates": {"numQuotes": 0}}},
        origin="CNNGB",
        destination="VNHPH",
        equipment="20GP",
        load_type="container20",
        fetched_at="2026-09-25T04:30:00Z",
    )
    assert out["status"] == "NO_COVERAGE"
    assert out["numQuotes"] == 0
    assert "minAmount" not in out


def test_fetch_available_40hq_shape_from_mocked_provider():
    seen = {}

    def request_fn(url, params=None, timeout=None, headers=None):
        seen["url"] = url
        seen["params"] = dict(params)
        seen["timeout"] = timeout
        seen["headers"] = dict(headers or {})
        return DummyResponse(200, _available_payload())

    out = fetch_public_estimate(
        origin="CNNGB",
        destination="VNHPH",
        equipment="40HQ",
        request_fn=request_fn,
        clock=_clock,
    )
    assert seen["url"] == FREIGHTOS_CALCULATOR_URL
    assert "estimate" not in seen["params"]
    assert seen["params"]["loadtype"] == "container40HC"
    assert seen["timeout"] == 12.0
    assert out["status"] == "AVAILABLE"
    assert out["minAmount"] == 891
    assert out["maxAmount"] == 1146
    assert out["currency"] == "USD"
    assert out["mode"] == "FCL"
    assert out["transitMin"] == 3
    assert out["transitMax"] == 24
    assert out["transitUnit"] == "days"
    assert out["providerUrl"] == FREIGHTOS_ATTRIBUTION_URL
    assert out["fetchedAt"] == "2026-09-25T04:30:00Z"


def test_timeout_4xx_5xx_and_network_are_provider_error():
    class Boom(Exception):
        pass

    timeout = fetch_public_estimate(
        origin="CNNGB", destination="VNHPH", equipment="20GP",
        request_fn=lambda *a, **k: (_ for _ in ()).throw(TimeoutError("slow")),
        clock=_clock,
    )
    assert timeout["status"] == "PROVIDER_ERROR"
    assert "minAmount" not in timeout

    http4 = fetch_public_estimate(
        origin="CNNGB", destination="VNHPH", equipment="20GP",
        request_fn=lambda *a, **k: DummyResponse(429, {"error": "quota"}),
        clock=_clock,
    )
    assert http4["status"] == "PROVIDER_ERROR"

    http5 = fetch_public_estimate(
        origin="CNNGB", destination="VNHPH", equipment="20GP",
        request_fn=lambda *a, **k: DummyResponse(500, None),
        clock=_clock,
    )
    assert http5["status"] == "PROVIDER_ERROR"

    network = fetch_public_estimate(
        origin="CNNGB", destination="VNHPH", equipment="20GP",
        request_fn=lambda *a, **k: (_ for _ in ()).throw(Boom("dns")),
        clock=_clock,
    )
    assert network["status"] == "PROVIDER_ERROR"
    assert network["errorClass"] == "Boom"


def test_comparison_requires_same_currency_and_range():
    bench = {
        "status": "AVAILABLE",
        "loadType": "container40HC",
        "currency": "USD",
        "minAmount": 891,
        "maxAmount": 1146,
    }
    ok = compare_internal(bench, amount=1425, currency="USD", load_type="container40HC")
    assert ok is not None
    assert ok["internalAmount"] == 1425
    assert ok["midpoint"] == (891 + 1146) / 2
    assert "không cùng hãng" in ok["label"]

    assert compare_internal(bench, amount=1425, currency="VND", load_type="container40HC") is None
    assert compare_internal(bench, amount=1425, currency="USD", load_type="container20") is None
    missing = dict(bench)
    missing.pop("maxAmount")
    assert compare_internal(missing, amount=1425, currency="USD", load_type="container40HC") is None


def test_handler_is_read_only_and_does_not_touch_snapshots(monkeypatch):
    calls = {"save": 0}

    def _explode(*args, **kwargs):
        calls["save"] += 1
        raise AssertionError("benchmark must never persist a supplier snapshot")

    monkeypatch.setattr("core.database.save_cost_rate_snapshot", _explode, raising=False)

    def request_fn(*args, **kwargs):
        return DummyResponse(200, _available_payload(504, 759))

    outcome = handle_cost_market_benchmark_fetch(
        {
            "originUnlocode": "CNNGB",
            "destinationUnlocode": "VNHPH",
            "equipment": "20GP",
            "internalAmount": 750,
            "internalCurrency": "USD",
            "snapshotId": "RATE-1",
            "rowId": "line-1",
            "requestId": "REQ-M1",
        },
        {
            "_result": lambda event, entity_id, ok, error="", **extra: {
                "event": event, "id": entity_id, "ok": ok, "error": error, **extra
            },
            "request_fn": request_fn,
        },
    )
    assert outcome["ok"] is True
    assert outcome["event"] == "cost_market_benchmark_fetch"
    assert outcome["benchmark"]["status"] == "AVAILABLE"
    assert outcome["benchmark"]["minAmount"] == 504
    assert outcome["benchmark"]["maxAmount"] == 759
    assert outcome["benchmark"]["comparison"]["internalAmount"] == 750
    assert calls["save"] == 0
    assert "record_type" not in outcome["benchmark"]


def test_handler_fail_soft_on_provider_error_does_not_block():
    outcome = handle_cost_market_benchmark_fetch(
        {
            "originUnlocode": "CNNGB",
            "destinationUnlocode": "VNHPH",
            "equipment": "40HQ",
            "requestId": "REQ-ERR",
        },
        {
            "_result": lambda event, entity_id, ok, error="", **extra: {
                "event": event, "id": entity_id, "ok": ok, "error": error, **extra
            },
            "request_fn": lambda *a, **k: DummyResponse(503, None),
        },
    )
    assert outcome["ok"] is True
    assert outcome["benchmark"]["status"] == "PROVIDER_ERROR"


def test_event_is_wired_into_existing_dispatcher():
    assert "cost_market_benchmark_fetch" in logi_c1.C1_EVENTS
    assert "cost_market_benchmark_fetch" in logi_c1._HANDLERS
    assert logi_c1.C1_EVENTS <= vm.ALL_EVENTS


def test_consume_c1_does_not_persist_on_benchmark(monkeypatch):
    monkeypatch.setattr(
        "core.database.save_cost_rate_snapshot",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("no snapshot write")),
        raising=False,
    )

    def fake_handle(payload, deps):
        return deps["_result"](
            "cost_market_benchmark_fetch", "", True, requestId=payload.get("requestId"),
            benchmark={"status": "NO_COVERAGE", "provider": "FREIGHTOS_PUBLIC"},
        )

    monkeypatch.setattr(
        "views.logi_cost_intelligence.handle_cost_market_benchmark_fetch",
        fake_handle,
    )
    outcomes = logi_c1.consume_c1_triggers(
        {"seq": 0},
        {
            "cost_market_benchmark_fetch": {
                "seq": 1,
                "event": "cost_market_benchmark_fetch",
                "payload": {
                    "originUnlocode": "CNNGB",
                    "destinationUnlocode": "VNHPH",
                    "equipment": "40HQ",
                    "requestId": "REQ-C1",
                },
            }
        },
    )
    assert len(outcomes) == 1
    assert outcomes[0]["ok"] is True
    assert outcomes[0]["benchmark"]["status"] == "NO_COVERAGE"
