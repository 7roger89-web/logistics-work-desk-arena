from __future__ import annotations
import streamlit as st
"""Mounted, fixture-only proof that Dashboard 2.0 stays read-only.
This is intentionally a test/QA oracle.  It patches the existing financial
write boundaries, mounts the real Streamlit entry point with an in-memory
fixture, and fails if any writer is reached during the bounded dashboard
flow.  It never connects to MongoDB and never submits a business write.
"""
from contextlib import ExitStack
from copy import deepcopy
from datetime import date
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch
from streamlit.testing.v1 import AppTest
from core.shipment_dashboard import build_shipment_dashboard_view
APP_PATH = Path(__file__).resolve().parents[1] / "app.py"
FINANCIAL_WRITE_TARGETS = (
    # Shipment/payment writes used by the legacy financial surface.
    "core.database.save_shipment_atomic",
    "core.database.save_direct_shipment_payment",
    "core.database.save_direct_payment_correction",
    "core.database.save_contract_proxy_payment_atomic",
    "core.database.save_contract_transaction",
    "core.database.save_proxy_payment",
    "core.database.delete_proxy_payment",
    "core.database.save_entrustment",
    "core.database.save_entrustment_book",
    "core.logic.apply_financial_snapshot",
    # Canonical obligation / transaction / allocation families.
    "core.financial_ledger.save_obligation",
    "core.financial_ledger.save_transaction",
    "core.financial_ledger.allocate_transaction",
    "core.financial_ledger.reverse_allocation",
    "core.financial_ledger.link_financial_record_to_shipment",
    # Lump-sum receipt + allocation path.
    "core.payment_logic.apply_lump_sum_payment",
    # Mounted dashboard/detail aliases must be covered as well as definitions.
    "views.dashboard.save_shipment_atomic",
    "views.dashboard.delete_shipment",
    "views.dashboard.apply_financial_snapshot",
    "views.shipment.save_shipment_atomic",
    "views.shipment.save_direct_shipment_payment",
    "views.shipment.apply_financial_snapshot",
    "views.contracts.save_contract_proxy_payment_atomic",
    "views.contracts.save_contract_transaction",
    "views.contracts.save_proxy_payment",
    "views.proxy_payment.save_proxy_payment",
    "views.proxy_payment.delete_proxy_payment",
    "views.entrustment.save_entrustment_book",
    "views.entrustment.save_entrust_db",
    "views.finance.apply_lump_sum_payment",
)
def _shipment_fixture(shipment_id: str, customer: str, owner: str, status: str) -> dict:
    return {
        "id": shipment_id,
        "shipment_id": shipment_id,
        "customer": customer,
        "status": status,
        "internal_sale_owner": owner,
        "assigned_date": "2026-08-01",
        "incoterm": "EXW",
        "production_expectation_days": 14,
        "customer_required_date": "2026-08-30",
        "planned_delivery_date": "2026-08-31",
        "promised_date": "2026-08-13",
        "info_pending": True,
        "data": {
            "2.6": {"arrival_date": "2026-08-05", "free_time": 7},
            "2.7": {"delivery_date": "2026-08-30", "is_delivered": False},
            "3.4": {
                "out": 1_000_000,
                "in": 500_000,
                "payments": [{"id": "PAY-FIXTURE-001", "amount": 250_000, "date": "2026-08-10"}],
            },
        },
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
def _fixture_shipments() -> dict[str, dict]:
    first = _shipment_fixture("LG-001", "Lục Giác", "SALE Thành", "pending")
    second = _shipment_fixture("LG-002", "Khách B", "SALE Khác", "done")
    second["factories"] = []
    second["data"]["3.4"] = {"out": 0, "in": 0, "payments": []}
    return {"LG-001": first, "LG-002": second}
def _financial_snapshot(shipments: dict[str, dict]) -> dict[str, dict]:
    """Capture the financial collections carried by the fixture boundary."""
    return {
        shipment_id: {
            "data.3.4": deepcopy(shipment.get("data", {}).get("3.4", {})),
            "financial_obligations": deepcopy(shipment.get("financial_obligations", [])),
            "financial_transactions": deepcopy(shipment.get("financial_transactions", [])),
            "financial_allocations": deepcopy(shipment.get("financial_allocations", [])),
            "entrustment": deepcopy(shipment.get("data", {}).get("entrustment", {})),
            "reconciliation": deepcopy(shipment.get("reconciliation", [])),
            "debit": deepcopy(shipment.get("debit", [])),
        }
        for shipment_id, shipment in shipments.items()
    }

def _login_fixture(user):
    """Set the login fixture user into the Streamlit session and return it."""
    import streamlit as st
    st.session_state.current_user = user
    return user

class _FinancialWriteOracle:
    def __init__(self) -> None:
        self.calls: list[str] = []
    @property
    def financial_write_count(self) -> int:
        return len(self.calls)
    def record(self, target: str, *args, **kwargs):
        del args, kwargs
        self.calls.append(target)
        return False
def _selectbox(app: AppTest, key: str):
    return next(element for element in app.selectbox if element.key == key)
def _button(app: AppTest, key: str):
    return next(element for element in app.button if element.key == key)
def _assert_no_streamlit_exceptions(test_case: TestCase, app: AppTest) -> None:
    exceptions = [(element.type, str(element.value)) for element in app.exception]
    test_case.assertEqual(exceptions, [], msg=f"mounted dashboard exceptions: {exceptions}")
class DashboardFinancialWriteOracleTests(TestCase):
    def test_bounded_dashboard_flow_has_zero_financial_writes_and_no_financial_mutation(self) -> None:
        shipments = _fixture_shipments()
        financial_before = _financial_snapshot(shipments)
        oracle = _FinancialWriteOracle()
        # The pure projection is part of the same bounded flow and must label
        # its financial result as read-only before the mounted UI is exercised.
        projection = build_shipment_dashboard_view(
            shipments["LG-001"],
            today=date(2026, 8, 14),
        )
        self.assertTrue(projection["read_only_financial"])
        self.assertTrue(projection["financial_projection"].get("read_only"))
        with ExitStack() as stack:
            for target in FINANCIAL_WRITE_TARGETS:
                stack.enter_context(
                    patch(
                        target,
                        side_effect=lambda *args, _target=target, **kwargs: oracle.record(
                            _target, *args, **kwargs
                        ),
                    )
                )
            stack.enter_context(patch("views.web_app.require_login", side_effect=lambda: (_login_fixture({"username": "fixture", "display_name": "Fixture", "role": "admin"}), {"username": "fixture", "display_name": "Fixture", "role": "admin"})[-1]))
            stack.enter_context(patch("views.web_app.refresh_core_data", return_value=None))
            stack.enter_context(patch("views.dashboard.cached_load_data", return_value=shipments))
            stack.enter_context(patch("views.dashboard.load_tasks", return_value=[]))
            app = AppTest.from_file(str(APP_PATH), default_timeout=60)
            app.run()
            _assert_no_streamlit_exceptions(self, app)
            self.assertTrue(
                any("Tài chính:" in element.value for element in app.markdown),
                "dashboard did not render the separate financial status",
            )
            self.assertTrue(
                any(("Next action" in element.value or "Việc tiếp theo" in element.value) for element in app.markdown),
                "dashboard did not render a deterministic alert action",
            )
            # Owner semantics: SALE Thành is a real fixture owner, not a
            # value inferred from notes/customer/address text.
            _selectbox(app, "dashboard_owner_filter").set_value("SALE Thành")
            app.run()
            _assert_no_streamlit_exceptions(self, app)
            self.assertIn("dashboard_open_360_LG-001", {element.key for element in app.button})
            self.assertNotIn("dashboard_open_360_LG-002", {element.key for element in app.button})
            # Warning semantics: the factory-data warning isolates LG-001.
            _selectbox(app, "dashboard_owner_filter").set_value("Tất cả")
            _selectbox(app, "dashboard_attention_filter").set_value("Nhà máy chưa đủ dữ liệu")
            app.run()
            _assert_no_streamlit_exceptions(self, app)
            self.assertIn("dashboard_open_360_LG-001", {element.key for element in app.button})
            self.assertNotIn("dashboard_open_360_LG-002", {element.key for element in app.button})
            # First shipment: open the real mounted detail path, then return.
            _selectbox(app, "dashboard_attention_filter").set_value("Tất cả")
            app.run()
            _button(app, "dashboard_open_360_LG-001").click()
            app.run()
            _assert_no_streamlit_exceptions(self, app)
            self.assertIn("btn_close_top", {element.key for element in app.button})
            self.assertTrue(
                any("Shipment 360" in element.value for element in app.markdown),
                "first shipment did not render Shipment 360 financial projection",
            )
            _button(app, "btn_close_top").click()
            app.run()
            _assert_no_streamlit_exceptions(self, app)
            self.assertNotIn("btn_close_top", {element.key for element in app.button})
            # Second shipment: verify the list is restored and the second row
            # opens independently on the next click.
            _button(app, "dashboard_open_360_LG-002").click()
            app.run()
            _assert_no_streamlit_exceptions(self, app)
            self.assertIn("btn_close_top", {element.key for element in app.button})
            self.assertTrue(any("LG-002" in element.value for element in app.markdown))
        self.assertEqual(oracle.financial_write_count, 0)
        self.assertEqual(oracle.calls, [])
        self.assertEqual(_financial_snapshot(shipments), financial_before)
