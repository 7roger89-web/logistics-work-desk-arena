from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from core.auth import can_edit_contract
from core.database import (
    load_contracts,
    delete_customer,
    delete_knowledge_entry,
    delete_proxy_payment,
    delete_shipment,
    save_agreements_to_cloud,
    save_contract_to_cloud,
    save_contract_transaction,
    save_customer_to_cloud,
    save_entrustment,
    save_proxy_payment,
    save_quotes_to_cloud,
    save_rate_card,
    save_cbpg_workspace,
    save_user,
    update_user,
    delete_user,
)
from core.financial_ledger import save_transaction
from tests.test_financial_ledger import _MemoryDatabase


class _Result:
    matched_count = 1
    modified_count = 1
    upserted_id = None


class _Collection:
    def __init__(self) -> None:
        self.docs: dict[str, dict] = {}

    @staticmethod
    def _matches(document: dict, query: dict) -> bool:
        for key, expected in query.items():
            actual = document.get(key)
            if isinstance(expected, dict) and "$ne" in expected:
                if actual == expected["$ne"]:
                    return False
            elif actual != expected:
                return False
        return True

    def find_one(self, query: dict, projection=None, **kwargs):
        del projection, kwargs
        for document in self.docs.values():
            if self._matches(document, query):
                return deepcopy(document)
        return None

    def find(self, query: dict | None = None, projection=None, **kwargs):
        del projection, kwargs
        return [
            deepcopy(document)
            for document in self.docs.values()
            if self._matches(document, query or {})
        ]

    def update_one(self, query: dict, update: dict, upsert=False, **kwargs):
        del kwargs
        current = self.find_one(query)
        if current is None and not upsert:
            return type("NoMatch", (), {"matched_count": 0, "modified_count": 0})()
        key = str(query.get("id") or query.get("username"))
        payload = current or {name: value for name, value in query.items() if not isinstance(value, dict)}
        payload.update(deepcopy(update.get("$set", {})))
        if current is None:
            payload.update(deepcopy(update.get("$setOnInsert", {})))
        self.docs[key] = payload
        return _Result()

    def insert_one(self, document: dict, **kwargs):
        del kwargs
        key = str(document.get("event_id") or document.get("id") or len(self.docs))
        self.docs[key] = deepcopy(document)
        return _Result()


class _Database:
    def __init__(self) -> None:
        self.contracts = _Collection()
        self.contract_transactions = _Collection()
        self.proxy_payments = _Collection()
        self.audit_logs = _Collection()

    def __getitem__(self, name: str) -> _Collection:
        return getattr(self, name)

    def __getattr__(self, name: str) -> _Collection:
        if name.startswith("_"):
            raise AttributeError(name)
        collection = _Collection()
        setattr(self, name, collection)
        return collection


SUPPORT = {
    "user_id": "support-user-01",
    "username": "support.minh",
    "display_name": "Minh Support",
    "role": "support",
}
SALE = {
    "user_id": "sale-user-01",
    "username": "sale.thanh",
    "display_name": "Thành Sale",
    "role": "sale",
}
ADMIN = {
    "user_id": "admin-user-01",
    "username": "admin",
    "display_name": "Admin",
    "role": "admin",
}
VIEWER = {
    "user_id": "viewer-user-01",
    "username": "viewer.read",
    "display_name": "Viewer",
    "role": "viewer",
}


class SupportContractPersistenceTests(TestCase):
    def _with_user(self, user):
        return patch("core.auth.st", type("AuthStreamlit", (), {"session_state": {"current_user": user}})())

    def test_support_contract_create_edit_save_and_reopen_persisted_values(self) -> None:
        db = _Database()
        with self._with_user(SUPPORT), patch("core.database.get_db", return_value=db):
            self.assertTrue(can_edit_contract())
            created = {
                "id": "CT-SUPPORT-01",
                "contract_no": "CT-SUPPORT-01",
                "client": "Khách Support",
                "date": "2026-09-03",
                "value": 125000000,
                "currency": "VND",
                "note": "Điều khoản ban đầu",
            }
            self.assertTrue(save_contract_to_cloud(created))

            first_readback = load_contracts()
            self.assertEqual(first_readback["CT-SUPPORT-01"]["client"], "Khách Support")
            self.assertEqual(first_readback["CT-SUPPORT-01"]["value"], 125000000)

            updated = {**created, "value": 145000000, "note": "Phụ lục đã xác nhận"}
            self.assertTrue(save_contract_to_cloud(updated))
            self.assertTrue(save_contract_transaction({
                "id": "TX-SUPPORT-01",
                "contract_id": "CT-SUPPORT-01",
                "transaction_type": "bank_transfer",
                "amount": 50000000,
            }))

            reopened = load_contracts()
            self.assertEqual(reopened["CT-SUPPORT-01"]["value"], 145000000)
            self.assertEqual(reopened["CT-SUPPORT-01"]["note"], "Phụ lục đã xác nhận")
            self.assertEqual(reopened["CT-SUPPORT-01"]["updated_by_user_id"], SUPPORT["user_id"])
            self.assertEqual(reopened["CT-SUPPORT-01"]["updated_by_role"], "support")
            self.assertEqual(len(db.contract_transactions.docs), 1)
            self.assertTrue(all(row["actor_user_id"] == SUPPORT["user_id"] for row in db.audit_logs.docs.values()))
            self.assertTrue(all(row["actor_role"] == "support" for row in db.audit_logs.docs.values()))
            self.assertTrue(all(row["created_at"] for row in db.audit_logs.docs.values()))

    def test_unauthorized_contract_service_call_fails_before_persistence(self) -> None:
        db = _Database()
        with self._with_user(VIEWER), patch("core.database.get_db", return_value=db):
            self.assertFalse(can_edit_contract())
            self.assertFalse(save_contract_to_cloud({"id": "CT-DENIED", "client": "Không được ghi"}))
        self.assertEqual(db.contracts.docs, {})
        self.assertEqual(db.audit_logs.docs, {})

    def test_support_route_visibility_keeps_admin_only_user_route_hidden(self) -> None:
        from views.web_app import _visible_routes

        with self._with_user(SUPPORT):
            support_permissions = {route.permission for route in _visible_routes()}
        with self._with_user(SALE):
            sale_permissions = {route.permission for route in _visible_routes()}
        with self._with_user(ADMIN):
            admin_permissions = {route.permission for route in _visible_routes()}

        from views.web_app import ROUTES

        employee_permissions = {route.permission for route in ROUTES if route.permission != "admin"}
        self.assertTrue(employee_permissions.issubset(support_permissions))
        self.assertTrue({"contracts", "customers", "shipment_create", "receivables"}.issubset(support_permissions))
        self.assertNotIn("admin", support_permissions)
        self.assertNotIn("receivables", sale_permissions)
        self.assertIn("admin", admin_permissions)


class SupportOperationalWriterTests(TestCase):
    def _with_user(self, user):
        return patch("core.auth.st", type("AuthStreamlit", (), {"session_state": {"current_user": user}})())

    def test_support_can_write_mapped_operational_collections(self) -> None:
        db = _Database()
        with self._with_user(SUPPORT), patch("core.database.get_db", return_value=db):
            self.assertTrue(save_customer_to_cloud({"id": "CUS-SUPPORT", "name": "Khách Support"}))
            self.assertTrue(save_quotes_to_cloud({"Q-SUPPORT": {"id": "Q-SUPPORT", "status": "DRAFT"}}))
            self.assertTrue(save_agreements_to_cloud({"A-SUPPORT": {"id": "A-SUPPORT", "agreement_id": "A-SUPPORT"}}))
            self.assertTrue(save_entrustment({"id": "ENT-SUPPORT", "linked_id": "SHP-SUPPORT"}))
            self.assertTrue(save_proxy_payment({"id": "PX-SUPPORT", "amount_vnd": 1000}))
            self.assertTrue(save_rate_card({"id": "RC-SUPPORT", "history": []}))
            self.assertTrue(save_cbpg_workspace("USD", 100.0, []))

        self.assertIn("CUS-SUPPORT", db.customers.docs)
        self.assertIn("Q-SUPPORT", db.quotes.docs)
        self.assertIn("A-SUPPORT", db.agreements.docs)
        self.assertIn("ENT-SUPPORT", db.entrustments.docs)
        self.assertIn("PX-SUPPORT", db.proxy_payments.docs)
        self.assertIn("RC-SUPPORT", db.rate_cards.docs)
        self.assertIn("default", db.cbpg_workspaces.docs)
        self.assertGreaterEqual(len(db.audit_logs.docs), 2)

    def test_viewer_is_rejected_before_operational_writer_mutation(self) -> None:
        db = _Database()
        with self._with_user(VIEWER), patch("core.database.get_db", return_value=db) as get_db:
            self.assertFalse(save_customer_to_cloud({"id": "CUS-DENIED", "name": "Không được ghi"}))
            self.assertFalse(save_quotes_to_cloud({"Q-DENIED": {"id": "Q-DENIED"}}))
            self.assertFalse(save_agreements_to_cloud({"A-DENIED": {"id": "A-DENIED"}}))
            self.assertFalse(save_entrustment({"id": "ENT-DENIED"}))
            self.assertFalse(save_proxy_payment({"id": "PX-DENIED"}))
            self.assertFalse(save_rate_card({"id": "RC-DENIED"}))
            self.assertFalse(save_cbpg_workspace("USD", 100.0, []))

        get_db.assert_not_called()
        self.assertEqual(db.audit_logs.docs, {})

    def test_support_cannot_use_admin_only_destructive_writers(self) -> None:
        db = _Database()
        with self._with_user(SUPPORT), patch("core.database.get_db", return_value=db) as get_db:
            self.assertFalse(delete_customer("CUS-1", reason="test"))
            self.assertFalse(delete_knowledge_entry("KB-1"))
            self.assertFalse(delete_proxy_payment("PX-1", reason="test"))
            with self.assertRaises(RuntimeError):
                delete_shipment("SHP-1", reason="test")

        get_db.assert_not_called()
        self.assertEqual(db.audit_logs.docs, {})

    def test_support_can_write_canonical_finance_actual_but_viewer_cannot(self) -> None:
        db = _MemoryDatabase()
        transaction = {
            "id": "TX-SUPPORT-ACTUAL",
            "source_party": {"party_type": "customer", "party_id": "CUS-SUPPORT", "name": "Khách Support"},
            "holder_party": {"party_type": "company", "party_id": "LOGISTICS", "name": "Logistics"},
            "beneficial_owner": {"party_type": "customer", "party_id": "CUS-SUPPORT", "name": "Khách Support"},
            "amount": 2500000,
            "currency": "VND",
            "transaction_kind": "payment",
            "classification_status": "CONFIRMED",
            "restriction": {"status": "NONE"},
        }
        with self._with_user(SUPPORT), patch("core.database.get_db", return_value=db):
            created = save_transaction(transaction, "REQ-SUPPORT-ACTUAL", actor="ignored-display-name")
        self.assertTrue(created[0], created[2])
        saved = db.financial_transactions.find_one({"id": "TX-SUPPORT-ACTUAL"})
        self.assertEqual(saved["created_by_user_id"], SUPPORT["user_id"])
        self.assertEqual(saved["created_by_role"], "support")

        with self._with_user(VIEWER), patch("core.database.get_db", return_value=db) as get_db:
            denied = save_transaction(transaction, "REQ-VIEWER-ACTUAL", actor="viewer-string")
        self.assertFalse(denied[0])
        get_db.assert_not_called()
        self.assertIsNone(db.financial_transactions.find_one({"id": "TX-VIEWER-ACTUAL"}))

    def test_support_cannot_call_admin_user_service(self) -> None:
        db = _Database()
        with self._with_user(SUPPORT), patch("core.database.get_db", return_value=db) as get_db:
            self.assertFalse(save_user({"username": "blocked-admin", "role": "admin"}))
            self.assertFalse(update_user("someone", payload={"role": "admin"}, actor="support-string"))
            self.assertFalse(delete_user("someone", actor="support-string"))
        self.assertEqual(db.users.docs, {})
        get_db.assert_not_called()

    def test_admin_retains_wildcard_business_authority(self) -> None:
        with self._with_user(ADMIN):
            from core.auth import can_operate_business

            self.assertTrue(can_operate_business("shipment_create"))
            self.assertTrue(can_operate_business("finance_write"))
            self.assertTrue(can_operate_business("admin_write"))


class SupportContractMountedUiTests(TestCase):
    APP_PATH = Path(__file__).resolve().parents[1] / "app.py"

    @staticmethod
    def _login():
        import streamlit as st

        st.session_state.current_user = dict(SUPPORT)
        return dict(SUPPORT)

    def test_support_contract_form_is_mounted_and_save_control_is_enabled(self) -> None:
        db = _Database()
        with patch("views.web_app.require_login", side_effect=self._login), \
             patch("views.web_app.refresh_core_data", return_value=None), \
             patch("views.dashboard.cached_load_data", return_value={}), \
             patch("views.dashboard.load_tasks", return_value=[]), \
             patch("views.contracts.load_proxy_payments", return_value={}), \
             patch("views.contracts.load_entrustments", return_value={}), \
             patch("core.database.get_db", return_value=db):
            app = AppTest.from_file(str(self.APP_PATH), default_timeout=60)
            app.run()
            self.assertEqual(list(app.exception), [])
            route_button = next(button for button in app.sidebar.button if "Hợp Đồng" in button.label)
            route_button.click()
            app.run()
            self.assertEqual(list(app.exception), [])
            save_button = next(button for button in app.button if button.label == "🚀 Lưu hợp đồng")
            self.assertFalse(save_button.disabled)
