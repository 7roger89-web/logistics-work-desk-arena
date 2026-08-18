# LOG-LG03 — Thiết kế patch user API (bounded restore)

## Ngữ cảnh
- Commit 4578d3f có đầy đủ 4 hàm user API trong core/database.py (đã dump ra /tmp/db_4578d3f.py).
- Main hiện tại 09e2426 thiếu 4 hàm này → P1 latent bug (web_app.py line 305 imports load_users/update_user/delete_user; auth.py calls save_user in _complete_bootstrap).
- Owner vẫn login được trên production vì file database.py máy anh (pull từ rc ~4633711 era?) — kiểm tra sau.

## Contract của caller (đã xác nhận):
1. views/web_app.py `_render_user_management()` (line 303-365):
   - load_users() → dict[str, doc]
   - update_user(username=uname, payload={"role": new_role, "active": active}, actor=...) → result truthy/falsy
   - delete_user(uname, actor=...) → bool
   - _create_user_from_admin: from core.database import save_user; build_user_document(...) rồi save_user(document)
2. core/auth.py _complete_bootstrap: build_user_document → save_user(document)
3. core/users.py docstring: persistence lives in core.database (load_users/save_user/delete_user)

## VẤN ĐỀ SIGNATURE:
- web_app.py gọi update_user(username=..., payload=..., actor=...) — NHƯNG bản 4578d3f định nghĩa update_user(username, document, actor) với tham số thứ 2 là `document` (không có kwarg payload).
- Do đó khi restore từ 4578d3f, views/web_app.py sẽ lỗi TypeError khi đổi vai trò người dùng.
- Quyết định: restore 4 hàm nhưng RENAME tham số để khớp caller hiện tại:
  - def update_user(username: str, payload: dict[str, Any] = None, *, document: dict = None, actor: str = "system"):
    - nhận cả payload=... (views) và document=... (legacy); payload = $set partial update; document = full $set.
- load_users, save_user, delete_user giữ nguyên signature (save_user(document), delete_user(username, actor)).
- Cần kiểm tra auth.py _complete_bootstrap có gọi update_user với payload không — không, chỉ save_user.

## Nội dung patch (từ 4578d3f, sửa tham số):
```python
def load_users() -> dict[str, dict[str, Any]]:
    """Toàn bộ user documents (gồm password_hash — chỉ core.auth dùng để xác thực)."""
    db = get_db()
    if db is None:
        return {}
    return {
        str(doc["username"]): {k: v for k, v in doc.items() if k != "_id"}
        for doc in db.users.find({}, {"_id": 0})
        if doc.get("username") and not doc.get("is_deleted")
    }

def save_user(document: dict[str, Any]) -> bool:
    """Tạo hoặc cập nhật user theo khóa username; ghi audit."""
    db = get_db()
    if db is None or not document.get("username"):
        return False
    try:
        safe = {k: v for k, v in document.items() if k != "_id"}
        db.users.update_one(
            {"username": str(document["username"])},
            {"$set": safe},
            upsert=True,
        )
        _audit(db, "user", str(document["username"]), "create", after=safe)
        return True
    except Exception as exc:  # noqa: BLE001
        LOGGER.exception("save_user failed")
        return False

def update_user(username: str, payload: dict[str, Any] | None = None, *, document: dict[str, Any] | None = None, actor: str = "system") -> bool:
    """Cập nhật user đã tồn tại; không tạo mới.
    - payload={...}: partial $set (caller hiện tại views/web_app.py)
    - document={...}: full $set document (caller legacy)
    """
    db = get_db()
    if db is None:
        return False
    safe = (payload or document) or {}
    if not safe:
        return False
    try:
        result = db.users.update_one({"username": str(username)}, {"$set": safe})
        _audit(db, "user", str(username), "update", after=safe, actor=actor)
        return bool(result.matched_count)
    except Exception as exc:  # noqa: BLE001
        LOGGER.exception("update_user failed")
        return False

def delete_user(username: str, actor: str = "system") -> bool:
    """Soft delete user (giữ audit trail); hard delete chỉ khi is_deleted sẵn."""
    db = get_db()
    if db is None:
        return False
    old = db.users.find_one({"username": str(username)}, {"_id": 0})
    if old is None:
        return False
    if old.get("is_deleted"):
        result = db.users.delete_one({"username": str(username)})
        if result.deleted_count:
            _audit(db, "user", str(username), "hard_delete", before=old, actor=actor)
            return True
        return False
    result = db.users.update_one(
        {"username": str(username)},
        {"$set": {"is_deleted": True, "deleted_at": utc_now(), "deleted_by": str(actor)}},
    )
    if result.modified_count:
        _audit(db, "user", str(username), "soft_delete", before=old, actor=actor)
        return True
    return False
```

## Phụ thuộc đã xác nhận có trong database.py hiện tại:
- get_db() dòng 181 ✓; _audit(db,...actor=) dòng 365 ✓; utc_now() ✓; _actor() ✓ (delete_proxy_payment dùng)
- Cần kiểm tra LOGGER import ở đầu database.py (import từ 4578d3f: dùng LOGGER) — verify trước khi chèn.

## Vị trí chèn: cuối file core/database.py (sau delete_proxy_payment).

## Test plan:
- Unit test tests/test_users_persistence.py dùng FakeCollection/FakeDb như test_quotations.py (patch core.database.get_db), test:
  - save_user tạo mới + upsert idempotent, audit ghi
  - load_users trả về mapping, loại is_deleted
  - update_user payload partial; matched_count 0 khi không tồn tại
  - delete_user soft_delete + audit, hard delete khi sẵn is_deleted
  - finance collections KHÔNG bị chạm
- Rehearsal DB (local mongod logistics_workdesk_LG01_E2E) replay: seed_rehearsal_users.py sẽ chạy OK sau patch.

## Next steps LG03 (sau patch):
1. Language inventory toàn bộ views (W1)
2. Glossary tiếng Việt (W3)
3. Pilot: Dashboard (ui_dashboard), Review Queue (việc cần xử lý), Tạo Lô Mới (ui_create_new_shipment), Khách Hàng, Finance Review (Đối soát tài chính)
4. Scale còn lại, QA 3 role, regression toàn diện, Draft PR, state.json checkpoint
