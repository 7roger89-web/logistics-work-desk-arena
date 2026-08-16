from __future__ import annotations

import copy
import unittest
from datetime import date

from core.review_queue import (
    CATEGORY_DOCUMENT,
    CATEGORY_FINANCIAL,
    CATEGORY_OPERATIONAL,
    STATUS_CRITICAL,
    STATUS_REVIEW,
    STATUS_WAITING,
    build_review_queue_items,
    filter_review_queue_items,
    summarize_review_queue,
)


def shipment_fixture() -> dict:
    return {
        "id": "S-100",
        "shipment_id": "S-100",
        "customer": "Factory Customer",
        "customer_id": "",
        "status": "pending",
        "data": {
            "0.0": {"st": "pending"},
            "1.2": {"booking_no": "BK-100", "pol": "VN", "pod": "US"},
            "2.6": {"arrival_date": "2026-08-01", "free_time": 2},
            "2.7": {},
            "3.4": {
                "receivable": 100,
                "payments": [],
                "unreconciled": 10,
            },
            "factories": [
                {
                    "factory_name": "Factory One",
                    "ready_date": "",
                    "pickup_contact": "",
                    "required_information_complete": False,
                }
            ],
            "documents": [
                {"name": "Packing list", "status": "waiting", "source": "supplier"},
                {"name": "Invoice", "status": "UNKNOWN", "required": True},
            ],
        },
        "next_action": "Confirm factory docs",
        "next_action_due": "2026-08-10",
    }


class ReviewQueueTests(unittest.TestCase):
    def test_builds_actionable_categories_and_unknown_documents(self) -> None:
        items = build_review_queue_items({"S-100": shipment_fixture()}, today=date(2026, 8, 16))
        categories = {item["category"] for item in items}
        codes = {item["item_id"].split(":")[1] for item in items}
        self.assertIn(CATEGORY_OPERATIONAL, categories)
        self.assertIn(CATEGORY_DOCUMENT, categories)
        self.assertIn(CATEGORY_FINANCIAL, categories)
        self.assertIn("DOCUMENT_WAITING", codes)
        self.assertIn("DOCUMENT_UNKNOWN", codes)

    def test_priority_is_deterministic_and_critical_first(self) -> None:
        first = build_review_queue_items({"S-100": shipment_fixture()}, today=date(2026, 8, 16))
        second = build_review_queue_items({"S-100": shipment_fixture()}, today=date(2026, 8, 16))
        self.assertEqual([row["item_id"] for row in first], [row["item_id"] for row in second])
        self.assertEqual(first[0]["status"], STATUS_CRITICAL)

    def test_waiting_and_review_filters_keep_source_rows(self) -> None:
        items = build_review_queue_items({"S-100": shipment_fixture()}, today=date(2026, 8, 16))
        waiting = filter_review_queue_items(items, status=STATUS_WAITING)
        review = filter_review_queue_items(items, status=STATUS_REVIEW)
        self.assertTrue(waiting)
        self.assertTrue(review)
        self.assertTrue(all(row["read_only"] for row in waiting + review))

    def test_search_and_category_filter(self) -> None:
        items = build_review_queue_items({"S-100": shipment_fixture()}, today=date(2026, 8, 16))
        result = filter_review_queue_items(items, search="packing", category=CATEGORY_DOCUMENT)
        self.assertEqual(len(result), 1)
        self.assertIn("DOCUMENT_WAITING", result[0]["item_id"])

    def test_summary_counts_unique_shipments(self) -> None:
        items = build_review_queue_items({"S-100": shipment_fixture()}, today=date(2026, 8, 16))
        summary = summarize_review_queue(items)
        self.assertEqual(summary["shipments"], 1)
        self.assertEqual(summary["total"], len(items))

    def test_projection_does_not_mutate_input(self) -> None:
        fixture = shipment_fixture()
        before = copy.deepcopy(fixture)
        build_review_queue_items({"S-100": fixture}, today=date(2026, 8, 16))
        self.assertEqual(fixture, before)


if __name__ == "__main__":
    unittest.main()
