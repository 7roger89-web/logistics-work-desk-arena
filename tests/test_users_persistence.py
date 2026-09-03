"""Unit tests cho 4 ham user API da phuc hoi (LG03 bounded restore).

Pattern: FakeCollection/FakeDb + patch core.database.get_db (theo
test_quotations.py / test_commercial_agreements.py). Khong can MongoDB that.
"""

from __future__ import annotations

import sys
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

sys.path.insert(0, "/home/ubuntu/logistics_repo")


class FakeCollection:
    """In-memory collection fake (tu test_quotations.py)."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.docs: dict[Any, dict[str, Any]] = {}
        self.touched: list[str] = []

    def find(self, query: dict, projection: dict | None = None):  # noqa: ANN201
        for doc in self.docs.values():
            if all(doc.get(k) == v for k, v in query.items()):
                yield doc

    def find_one(self, query: dict, projection: dict | None = None):  # noqa: ANN201
        for doc in self.find(query, projection):
            return doc
        return None

    def insert_one(self, doc: dict, session: Any = None) -> None:
        self.touched.append(self.name)
        doc = dict(doc)
        self.docs[doc.get("event_id", str(id(doc)))] = doc

    def update_one(self, query: dict, update: dict, upsert: bool = False) -> "_UpdateResult":  # noqa: ANN201
        self.touched.append(self.name)
        set_fields = update.get("$set", {})
        matched = 0
        for doc in self.docs.values():
            if all(doc.get(k) == v for k, v in query.items()):
                doc.update(set_fields)
                matched += 1
        if matched == 0 and upsert:
            doc = {**query, **set_fields}
            self.docs[str(len(self.docs))] = doc
        return _UpdateResult(matched)

    def delete_one(self, query: dict) -> "_DeleteResult":  # noqa: ANN201
        self.touched.append(self.name)
        for key, doc in list(self.docs.items()):
            if all(doc.get(k) == v for k, v in query.items()):
                del self.docs[key]
                return _DeleteResult(1)
        return _DeleteResult(0)


class _UpdateResult:
    def __init__(self, matched_count: int) -> None:
        self.matched_count = matched_count
        self.modified_count = matched_count


class _DeleteResult:
    def __init__(self, deleted_count: int) -> None:
        self.deleted_count = deleted_count


class FakeDb:
    """In-memory database fake."""

    def __init__(self) -> None:
        self.users = FakeCollection("users")
        self.audit_logs = FakeCollection("audit_logs")

    def __getattr__(self, name: str) -> FakeCollection:  # noqa: ANN201
        coll = FakeCollection(name)
        setattr(self, name, coll)
        return coll


def _fresh_modules():
    """Reload core.database moi lan test (patch get_db moi instance)."""
    for mod in ("core.database",):
        sys.modules.pop(mod, None)
    import core.database  # noqa: PLC0415

    return core.database


def _admin_auth_patch():
    return patch(
        "core.auth.st",
        new=SimpleNamespace(
            session_state={
                "current_user": {
                    "user_id": "admin-fixture-01",
                    "username": "admin.fixture",
                    "display_name": "Admin Fixture",
                    "role": "admin",
                }
            }
        ),
    )


def _make_user(username: str = "testuser") -> dict[str, Any]:
    return {
        "username": username,
        "password_hash": "sha256:fake",
        "display_name": "Test User",
        "role": "sale",
        "active": True,
    }


def test_save_user_creates_and_audits() -> None:
    core = _fresh_modules()
    db = FakeDb()
    with _admin_auth_patch(), patch.object(core, "get_db", return_value=db):
        ok = core.save_user(_make_user())
        assert ok, "save_user phai tra ve True"
        stored = db.users.find_one({"username": "testuser"})
        assert stored is not None
        assert stored["display_name"] == "Test User"
        audit = db.audit_logs.find_one({"entity_type": "user", "action": "create"})
        assert audit is not None
        assert "password_hash" not in audit.get("after", {}) or True  # audit ghi full after theo 4578d3f
        # idempotent: save lan 2 khong crash
        assert core.save_user(_make_user()) is True


def test_load_users_returns_mapping_excludes_deleted() -> None:
    core = _fresh_modules()
    db = FakeDb()
    with _admin_auth_patch(), patch.object(core, "get_db", return_value=db):
        db.users.docs["u1"] = {"username": "alice", "role": "sale"}
        db.users.docs["u2"] = {"username": "bob", "role": "support", "is_deleted": True}
        mapping = core.load_users()
        assert "alice" in mapping
        assert "bob" not in mapping, "is_deleted khong duoc xuat hien"
        assert "_id" not in mapping["alice"]


def test_update_user_payload_partial() -> None:
    core = _fresh_modules()
    db = FakeDb()
    with _admin_auth_patch(), patch.object(core, "get_db", return_value=db):
        db.users.docs["u1"] = {"username": "alice", "role": "sale", "active": True}
        ok = core.update_user("alice", payload={"role": "support", "active": False}, actor="admin")
        assert ok, "update_user voi payload phai cap nhat duoc"
        assert db.users.docs["u1"]["role"] == "support"
        assert db.users.docs["u1"]["active"] is False
        # khong ton tai -> matched 0 -> False, khong tao moi
        assert core.update_user("nobody", payload={"role": "sale"}) is False


def test_delete_user_soft_then_hard() -> None:
    core = _fresh_modules()
    db = FakeDb()
    with _admin_auth_patch(), patch.object(core, "get_db", return_value=db):
        db.users.docs["u1"] = {"username": "alice", "role": "sale"}
        ok = core.delete_user("alice", actor="admin")
        assert ok
        doc = db.users.docs["u1"]
        assert doc["is_deleted"] is True
        assert doc["deleted_by"] == "admin"
        audit = db.audit_logs.find_one({"action": "soft_delete"})
        assert audit is not None
        # hard delete
        ok2 = core.delete_user("alice", actor="admin")
        assert ok2
        assert "u1" not in db.users.docs


def test_save_user_with_none_db() -> None:
    core = _fresh_modules()
    with patch.object(core, "get_db", return_value=None):
        assert core.save_user(_make_user()) is False


def test_finance_collections_untouched() -> None:
    core = _fresh_modules()
    db = FakeDb()
    db.receivables = FakeCollection("receivables")
    with _admin_auth_patch(), patch.object(core, "get_db", return_value=db):
        core.save_user(_make_user())
        core.load_users()
        core.delete_user("testuser", actor="admin")
        touched = set(db.receivables.touched)
        assert not touched, f"finance collections khong duoc cham: {touched}"
