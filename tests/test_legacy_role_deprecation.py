"""Phase F — khóa hợp đồng deprecation role legacy.

Hợp đồng:

* 4 role legacy (accounting/operations/sales/viewer) vẫn đọc được: ma trận quyền
  trong ``core.auth.ROLE_PERMISSIONS`` và tài khoản cũ vẫn đăng nhập nguyên trạng;
* chúng không assignable: không nằm trong ``core.users.SUPPORTED_ROLES`` và
  ``normalize_role`` từ chối;
* mỗi role legacy phát DeprecationWarning đúng một lần/process khi được dùng;
* role được hỗ trợ và role lạ (fallback viewer) không thay đổi hành vi.
Không có hệ quyền/thứ hai router nào được tạo ra trong test này.
"""
from __future__ import annotations

import warnings

import pytest

import core.auth as auth
from core.auth import (
    LEGACY_ROLE_DEPRECATION_DATE,
    LEGACY_ROLES,
    ROLE_PERMISSIONS,
    hash_password,
    is_legacy_role,
)
from core.users import SUPPORTED_ROLES, UserError, authenticate, normalize_role


@pytest.fixture(autouse=True)
def _reset_role_warnings():
    saved = auth._WARNED_LEGACY_ROLES.copy()
    auth._WARNED_LEGACY_ROLES.clear()
    yield
    auth._WARNED_LEGACY_ROLES.clear()
    auth._WARNED_LEGACY_ROLES.update(saved)


def test_role_matrix_shape_and_legacy_boundary():
    assert set(ROLE_PERMISSIONS) == {
        "admin", "sale", "support", "accounting", "operations", "sales", "viewer",
    }
    assert set(LEGACY_ROLES) == {"accounting", "operations", "sales", "viewer"}
    assert set(SUPPORTED_ROLES) == {"admin", "sale", "support"}
    # Không một role legacy nào được gán mới từ UI.
    assert LEGACY_ROLES.isdisjoint(SUPPORTED_ROLES)
    assert all(is_legacy_role(role) for role in LEGACY_ROLES)
    assert not any(is_legacy_role(role) for role in SUPPORTED_ROLES)


def test_legacy_roles_are_not_assignable():
    for role in LEGACY_ROLES:
        with pytest.raises(UserError):
            normalize_role(role)
    # Ba role hỗ trợ vẫn gán được như cũ.
    for role in SUPPORTED_ROLES:
        assert normalize_role(role) == role


def test_legacy_roles_remain_readable_with_their_permissions():
    for role in LEGACY_ROLES:
        assert auth._role_permissions(role) == ROLE_PERMISSIONS[role]
    # Spot-check quyền cụ thể để khóa hành vi, không chỉ khóa tên.
    assert "finance_view" in ROLE_PERMISSIONS["accounting"]
    assert "operations_write" in ROLE_PERMISSIONS["operations"]
    assert "sales_write" in ROLE_PERMISSIONS["sales"]
    assert ROLE_PERMISSIONS["viewer"].isdisjoint({"sales_write", "operations_write"})


def test_legacy_user_document_still_authenticates_with_stored_role():
    document = {
        "user_id": "legacy0001",
        "username": "legacy.user",
        "display_name": "Legacy User",
        "email": "",
        "role": "accounting",
        "active": True,
        "password_hash": hash_password("correct horse"),
    }
    identity = authenticate(document, "correct horse")
    assert identity is not None
    assert identity["role"] == "accounting"  # đọc nguyên trạng, không tự đổi role
    assert authenticate(document, "wrong password") is None


def test_legacy_role_warns_once_per_process_with_deprecation_date():
    with warnings.catch_warnings(record=True) as record:
        warnings.simplefilter("always")
        auth._role_permissions("accounting")
        auth._role_permissions("accounting")  # lần hai không cảnh báo lại
        auth._role_permissions("operations")
    messages = [str(w.message) for w in record if issubclass(w.category, DeprecationWarning)]
    assert len(messages) == 2
    assert all(LEGACY_ROLE_DEPRECATION_DATE in m for m in messages)
    assert any("accounting" in m for m in messages)
    assert any("operations" in m for m in messages)
    assert set(auth._WARNED_LEGACY_ROLES) == {"accounting", "operations"}


def test_supported_role_and_unknown_fallback_do_not_warn():
    with warnings.catch_warnings(record=True) as record:
        warnings.simplefilter("always")
        assert auth._role_permissions("sale") == ROLE_PERMISSIONS["sale"]
        # Role lạ rơi về viewer (hành vi cũ giữ nguyên); viewer là legacy nên cảnh báo
        # cho 'viewer', nhưng KHÔNG có cảnh báo nào nhắc đến role lạ 'martian'.
        fallback = auth._role_permissions("martian")
    assert fallback == ROLE_PERMISSIONS["viewer"]
    joined = " ".join(str(w.message) for w in record)
    assert "sale" not in joined
    assert "martian" not in joined
