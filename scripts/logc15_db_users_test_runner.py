"""Chạy bộ kiểm thử users store trên database MONGO_DB_NAME hiện cấu hình.

Được gọi bởi scripts/logc15_db_users_test.py (subprocess + env override).
Không in bất kỳ credential nào; cuối cùng dọn sạch toàn bộ database test.
"""
from __future__ import annotations

import importlib
import sys
import traceback

import pymongo

from core.users import build_user_document, change_password, public_identity, set_active


def main() -> int:
    results = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        results.append((name, ok, detail))
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))

    # 1. Override database về DB test riêng (runtime-override an toàn — app vẫn dùng
    # secrets theo thứ tự ưu tiên mặc định; chỉ ảnh hưởng process kiểm thử này)
    test_db_name = "logistics_workdesk_logc15"
    import core.config as _core_config
    _core_config.MONGO_DB_NAME = test_db_name
    core_db = importlib.import_module("core.database")
    client = core_db.init_connection()
    if client is None:
        print("ERROR: không kết nối được MongoDB — kiểm tra cấu hình secrets")
        return 2
    db = client[test_db_name]

    # Dọn DB test trước khi chạy (chỉ chứa fixture từ các lần chạy trước — an toàn).
    for cname in db.list_collection_names():
        db[cname].drop()

    # 2. Tạo index trên DB test qua chính ensure_indexes() của ứng dụng
    ok = core_db.ensure_indexes()
    check("ensure_indexes chạy thành công (DB test)", bool(ok))

    # 3. Create users
    admin_doc = build_user_document("owner.admin", "Admin-2026-Strong", "Owner", "admin", created_by="bootstrap")
    sale_doc = build_user_document("lan.sale", "Sale-2026-Strong", "Lan", "sale", created_by="owner.admin")
    sup_doc = build_user_document("mai.support", "Support-2026-Strong", "Mai", "support", created_by="owner.admin")
    check("save_user admin", core_db.save_user(admin_doc))
    check("save_user sale", core_db.save_user(sale_doc))
    check("save_user support", core_db.save_user(sup_doc))

    users = core_db.load_users()
    check("load_users trả về 3 user", len(users) == 3, f"{len(users)}")

    # 4. Duplicate username phải fail (unique index) — trigger E11000 trực tiếp
    from pymongo.errors import DuplicateKeyError
    dup_ok = False
    dup_err = None
    try:
        db.users.insert_one({"username": "lan.sale", "role": "sale", "password_hash": "pbkdf2_sha256$x$y$z"})
    except DuplicateKeyError:
        dup_ok = True
    except Exception as exc:  # noqa: BLE001
        dup_err = f"{type(exc).__name__}: {str(exc)[:150]}"
    check("unique index chặn trùng username", dup_ok, dup_err)

    # 5. Authenticate đúng/sai
    from core.users import authenticate
    check("authenticate đúng mật khẩu", authenticate(users["owner.admin"], "Admin-2026-Strong") is not None)
    check("authenticate sai mật khẩu trả None", authenticate(users["owner.admin"], "wrong-password") is None)

    # 6. Deactivate user
    deactivated = set_active(users["mai.support"], False, actor="owner.admin")
    check("set_active deactivate", deactivated.get("active") is False)
    ok2 = core_db.update_user("mai.support", deactivated)
    check("update_user deactivate", ok2)
    fresh = core_db.load_users()["mai.support"]
    check("authenticate user bị vô hiệu trả None", authenticate(fresh, "Support-2026-Strong") is None)

    # 7. Đổi mật khẩu
    new_doc = change_password(fresh, "Support-2026-Newer", actor="owner.admin")
    ok3 = core_db.update_user("mai.support", new_doc)
    check("update_user đổi mật khẩu", ok3)
    fresh2 = core_db.load_users()["mai.support"]
    # User vẫn đang inactive — login mật khẩu mới cũng trả None (không lộ trạng thái).
    check("user inactive vẫn không đăng nhập được (mật khẩu mới)", authenticate(fresh2, "Support-2026-Newer") is None)
    check("mật khẩu cũ không còn dùng được", authenticate(fresh2, "Support-2026-Strong") is None)
    # Re-enable rồi xác nhận mật khẩu mới hoạt động.
    reenabled = set_active(fresh2, True, actor="owner.admin")
    core_db.update_user("mai.support", reenabled)
    fresh3 = core_db.load_users()["mai.support"]
    check("đăng nhập mật khẩu mới sau khi kích hoạt lại", authenticate(fresh3, "Support-2026-Newer") is not None)
    check("mật khẩu cũ vẫn không dùng được sau khi kích hoạt lại", authenticate(fresh3, "Support-2026-Strong") is None)
    check("public_identity không chứa password_hash", "password_hash" not in public_identity(users["mai.support"]))


    # 9. Soft delete + hard delete
    check("soft delete mai.support", core_db.delete_user("mai.support", actor="owner.admin"))
    users = core_db.load_users()
    check("user soft-deleted không còn trong load_users", "mai.support" not in users)
    check("hard delete (lần 2)", core_db.delete_user("mai.support", actor="owner.admin"))
    n_remaining = db.users.count_documents({}) if _can_count(db) else len(core_db.load_users())
    remaining_names = sorted(core_db.load_users().keys())
    check("hard delete giảm số user còn 2", len(remaining_names) == 2, f"{remaining_names}")

    # 8. Audit trail (kiểm tra cuối quy trình để bao gồm cả soft/hard delete)
    audits = list(db.audit_logs.find({"entity_type": "user"}, {"_id": 0}).sort("created_at", -1))
    check("audit_logs có sự kiện user", len(audits) >= 8, f"{len(audits)} events")
    actions = [a["action"] for a in audits]
    check("audit chứa update", "update" in actions, str(actions[:10]))

    # 10. redact_for_audit
    redacted = core_db.redact_for_audit(users["owner.admin"])
    check("redact_for_audit loại password_hash", "password_hash" not in redacted)

    failed = [r for r in results if not r[1]]
    return 0 if not failed else 1


def _can_count(db) -> bool:
    """count_documents có thể fail trên Atlas khi thiếu quyền collStats."""
    try:
        db.users.count_documents({})
        return True
    except Exception:  # noqa: BLE001
        return False


if __name__ == "__main__":
    raise SystemExit(main())
