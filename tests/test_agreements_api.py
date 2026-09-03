from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from core import database as db

FIXTURES = {
    "AGR-1": {"id": "AGR-1", "customer_id": "C1", "goods": "sắt", "quote_amount": 1000},
    "AGR-2": {"id": "AGR-2", "customer_id": "C2", "goods": "nhôm", "quote_amount": 2000},
}


class _PersistenceCollection:
    def find_one(self, query, projection=None):
        del query, projection
        return None

    def insert_one(self, document, **kwargs):
        del document, kwargs
        return object()


class _PersistenceDatabase:
    def __init__(self):
        self.agreements = _PersistenceCollection()
        self.audit_logs = _PersistenceCollection()

    def __getitem__(self, name):
        return getattr(self, name)


class LoadAgreementsTests(unittest.TestCase):
    @patch.object(db, "_load_dict", return_value=FIXTURES)
    def test_load_agreements_returns_dict_from_load_dict(self, load_dict):
        result = db.load_agreements()
        self.assertEqual(result, FIXTURES)
        load_dict.assert_called_once_with("agreements", query={"is_deleted": {"$ne": True}})

    @patch.object(db, "_load_dict", return_value={})
    def test_load_agreements_returns_empty_dict_when_none_stored(self, load_dict):
        self.assertEqual(db.load_agreements(), {})


class SaveAgreementsToCloudTests(unittest.TestCase):
    @patch.object(db, "_save_document", return_value=True)
    def test_save_agreements_upserts_each_document(self, save_doc):
        sale_user = {
            "user_id": "sale-fixture-01",
            "username": "sale.fixture",
            "display_name": "Sale Fixture",
            "role": "sale",
        }
        with patch("core.auth.st", SimpleNamespace(session_state={"current_user": sale_user})), \
             patch.object(db, "get_db", return_value=_PersistenceDatabase()):
            ok = db.save_agreements_to_cloud(FIXTURES)
        self.assertTrue(ok)
        self.assertEqual(save_doc.call_count, 2)
        saved_ids = {call.args[1]["id"] for call in save_doc.call_args_list}
        self.assertEqual(saved_ids, {"AGR-1", "AGR-2"})

    @patch.object(db, "_save_document", return_value=False)
    def test_save_agreements_returns_false_on_partial_failure(self, save_doc):
        sale_user = {
            "user_id": "sale-fixture-01",
            "username": "sale.fixture",
            "display_name": "Sale Fixture",
            "role": "sale",
        }
        with patch("core.auth.st", SimpleNamespace(session_state={"current_user": sale_user})), \
             patch.object(db, "get_db", return_value=_PersistenceDatabase()):
            ok = db.save_agreements_to_cloud(FIXTURES)
        self.assertFalse(ok)


if __name__ == "__main__":
    unittest.main()
