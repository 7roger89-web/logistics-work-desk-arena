"""Fixture-safe tests for the Shipment Dashboard 2.0 projection."""

from __future__ import annotations

from copy import deepcopy
from datetime import date

from core.shipment_dashboard import (
    CRITICAL,
    FINANCIAL_OK,
    FINANCIAL_OPEN,
    FINANCIAL_UNKNOWN,
    build_dashboard_summary,
    build_shipment_dashboard_view,
    filter_dashboard_views,
    sort_dashboard_views,
)


def luc_giac_fixture() -> dict:
    """Minimal in-memory fixture; it is never loaded by the application."""

    return {
        "shipment_id": "LG-001",
        "customer": "Lục Giác",
        "status": "pending",
        "internal_sale_owner": "SALE Thành",
        "assigned_date": "2026-08-01",
        "incoterm": "EXW",
        "production_expectation_days": 14,
        "data": {
            "2.6": {"arrival_date": "2026-08-05", "free_time": "7"},
            "2.7": {"delivery_date": "2026-08-30", "is_delivered": False},
        },
        "customer_required_date": "2026-08-30",
        "planned_delivery_date": "2026-08-31",
        "promised_date": "2026-08-13",
        "info_pending": True,
        "factories": [
            {
                "product": "Bộ gá",
                "quantity": 10,
                "weight": 12,
                "cbm": 0.8,
                "factory_ready_date": "2026-08-11",
                "pickup_contact": "Mai",
            },
            {"product": "Thiếu dữ liệu"},
            {
                "product": "Keo công nghiệp",
                "quantity": 20,
                "weight": 18,
                "cbm": 1.2,
                "factory_ready_date": "2026-08-12",
                "pickup_contact": "Hùng",
            },
        ],
    }


def test_projection_derives_free_time_deadline_and_separate_statuses() -> None:
    row = build_shipment_dashboard_view(
        luc_giac_fixture(),
        today=date(2026, 8, 14),
        financial_view={"financial_status": "CHỜ THU", "attention": [], "read_only": True},
    )

    assert row["operational_status"] == "pending"
    assert row["operational_status_label"] == "Đang xử lý"
    assert row["financial_flag"] == FINANCIAL_OPEN
    assert row["financial_status"] == "CHỜ THU"
    assert row["free_time_expiry"] == date(2026, 8, 12)
    assert row["days_remaining"] == -2
    assert row["deadline_soon"] is True
    assert row["factory_count"] == 3
    assert row["missing_factory_count"] == 1
    assert row["top_alert"]["severity"] == CRITICAL
    assert row["top_alert"]["code"] == "CUSTOMER_DEADLINE_RISK"


def test_projection_keeps_unknown_finance_explicit_and_does_not_mutate_source() -> None:
    source = luc_giac_fixture()
    before = deepcopy(source)
    row = build_shipment_dashboard_view(
        source,
        today=date(2026, 8, 14),
        financial_view={"financial_status": "UNKNOWN", "attention": [], "read_only": True},
    )

    assert source == before
    assert row["financial_flag"] == FINANCIAL_UNKNOWN
    assert row["financial_label"] == "UNKNOWN"
    assert any(alert["code"] == "FINANCE_UNKNOWN" for alert in row["alerts"])
    assert row["read_only_financial"] is True


def test_filters_and_sort_keep_sale_owner_workdesk_path_deterministic() -> None:
    luc_giac = build_shipment_dashboard_view(
        luc_giac_fixture(),
        today=date(2026, 8, 14),
        financial_view={"financial_status": "CHỜ THU", "attention": [], "read_only": True},
    )
    other = build_shipment_dashboard_view(
        {
            "shipment_id": "OTHER-001",
            "customer": "Khách khác",
            "status": "done",
            "internal_sale_owner": "SALE Khác",
            "data": {"2.6": {"arrival_date": "2026-08-01", "free_time": 14}},
        },
        today=date(2026, 8, 14),
        financial_view={"financial_status": "ĐÃ THU ĐỦ PHẢI THU", "attention": [], "read_only": True},
    )

    filtered = filter_dashboard_views(
        [other, luc_giac], owner="SALE Thành", has_alert=True, search="LG-001"
    )
    assert [row["shipment_id"] for row in filtered] == ["LG-001"]
    assert [row["shipment_id"] for row in sort_dashboard_views([other, luc_giac])] == ["LG-001", "OTHER-001"]


def test_dashboard_summary_handles_rows_without_alerts() -> None:
    assert build_dashboard_summary([{"top_alert": None, "alerts": [], "has_alert": False}]) == {
        "total": 1,
        "critical": 0,
        "warning": 0,
        "deadline_soon": 0,
        "financial_attention": 0,
        "missing_info": 0,
    }


def test_missing_data_and_financial_filters_are_explicit() -> None:
    missing = build_shipment_dashboard_view(
        {"shipment_id": "MISSING-001", "status": "pending"},
        today=date(2026, 8, 14),
        financial_view={"financial_status": "ĐÃ THU ĐỦ", "attention": []},
    )
    assert missing["customer"] == "Chưa có khách hàng"
    assert {alert["code"] for alert in missing["alerts"]} >= {"MISSING_CUSTOMER", "MISSING_ETA"}

    nested_customer = build_shipment_dashboard_view(
        {
            "shipment_id": "NESTED-001",
            "status": "pending",
            "data": {"0.0": {"customer": "Khách trong section"}, "2.6": {"arrival_date": "2026-08-10"}},
        },
        today=date(2026, 8, 14),
        financial_view={"financial_status": "ĐÃ THU ĐỦ", "attention": []},
    )
    assert nested_customer["customer"] == "Khách trong section"
    assert not any(alert["code"] == "MISSING_CUSTOMER" for alert in nested_customer["alerts"])

    active_settled = build_shipment_dashboard_view(
        {
            "shipment_id": "ACTIVE-SETTLED",
            "customer": "Khách A",
            "status": "pending",
            "data": {"2.6": {"arrival_date": "2026-08-10"}},
        },
        today=date(2026, 8, 14),
        financial_view={"financial_status": "ĐÃ THU ĐỦ", "attention": []},
    )
    assert active_settled["financial_flag"] == FINANCIAL_OK

    complete_open = build_shipment_dashboard_view(
        {"shipment_id": "COMPLETE-OPEN", "customer": "Khách B", "status": "done"},
        today=date(2026, 8, 14),
        financial_view={"financial_status": "CHỜ THU", "attention": []},
    )
    assert complete_open["financial_flag"] == FINANCIAL_OPEN
    assert [row["shipment_id"] for row in filter_dashboard_views(
        [active_settled, complete_open], financial_flag=FINANCIAL_OPEN
    )] == ["COMPLETE-OPEN"]


def test_explicit_next_action_is_used_only_when_no_higher_alert_exists() -> None:
    row = build_shipment_dashboard_view(
        {
            "shipment_id": "ACTION-001",
            "customer": "Khách C",
            "status": "pending",
            "next_action": "Xác nhận booking với nhà máy",
            "data": {"2.6": {"arrival_date": "2026-08-01"}},
        },
        today=date(2026, 8, 14),
        financial_view={"financial_status": "ĐÃ THU ĐỦ", "attention": []},
    )
    assert row["next_action"]["code"] == "NEXT_ACTION"
    assert row["next_action"]["detail"] == "Xác nhận booking với nhà máy"


def test_rule_boundaries_are_deterministic() -> None:
    today = date(2026, 8, 14)

    free_time_warning = {
        "shipment_id": "FT-WARN",
        "customer": "Lục Giác",
        "status": "pending",
        "data": {"2.6": {"arrival_date": "2026-08-10", "free_time": 6}},
    }
    assert any(
        alert["code"] == "FREE_TIME_SOON"
        for alert in build_shipment_dashboard_view(free_time_warning, today=today, financial_view={"financial_status": "ĐÃ THU ĐỦ", "attention": []})["alerts"]
    )

    free_time_overdue = {
        "shipment_id": "FT-OVERDUE",
        "customer": "Lục Giác",
        "status": "pending",
        "data": {"2.6": {"arrival_date": "2026-08-01", "free_time": 7}},
    }
    assert any(
        alert["code"] == "FREE_TIME_OVERDUE"
        for alert in build_shipment_dashboard_view(free_time_overdue, today=today, financial_view={"financial_status": "ĐÃ THU ĐỦ", "attention": []})["alerts"]
    )

    deadline_soon = {"shipment_id": "DL-SOON", "customer": "Lục Giác", "status": "pending", "customer_required_date": "2026-08-17"}
    assert any(
        alert["code"] == "CUSTOMER_DEADLINE_SOON"
        for alert in build_shipment_dashboard_view(deadline_soon, today=today, financial_view={"financial_status": "ĐÃ THU ĐỦ", "attention": []})["alerts"]
    )

    deadline_risk = {"shipment_id": "DL-RISK", "customer": "Lục Giác", "status": "pending", "customer_required_date": "2026-08-17", "planned_delivery_date": "2026-08-20"}
    assert any(
        alert["code"] == "CUSTOMER_DEADLINE_RISK"
        for alert in build_shipment_dashboard_view(deadline_risk, today=today, financial_view={"financial_status": "ĐÃ THU ĐỦ", "attention": []})["alerts"]
    )

    promised_waiting = {"shipment_id": "PROMISED", "customer": "Lục Giác", "status": "pending", "promised_date": "2026-08-13", "info_pending": True}
    assert any(
        alert["code"] == "PROMISED_INFO_OVERDUE"
        for alert in build_shipment_dashboard_view(promised_waiting, today=today, financial_view={"financial_status": "ĐÃ THU ĐỦ", "attention": []})["alerts"]
    )

    completed = {"shipment_id": "DONE", "customer": "Lục Giác", "status": "Hoàn thành", "data": {"2.6": {"arrival_date": "2026-08-01", "free_time": 1}}, "customer_required_date": "2026-08-02"}
    completed_row = build_shipment_dashboard_view(completed, today=today, financial_view={"financial_status": "ĐÃ THU ĐỦ", "attention": []})
    assert completed_row["operational_status"] == "done"
    assert not any(alert["code"].startswith(("FREE_TIME", "CUSTOMER_DEADLINE")) for alert in completed_row["alerts"])
