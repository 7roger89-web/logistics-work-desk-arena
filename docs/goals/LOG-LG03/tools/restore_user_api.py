"""LG03 bounded restore: phuc hoi 4 ham user API da mat tu 4578d3f.

- load_users / save_user / delete_user: giong nguyen ban 4578d3f.
- update_user: nhan ca payload= (caller hien tai views/web_app.py)
  va document= (legacy), de khong gay TypeError khi doi vai tro nguoi dung.

An toan: chi APPEND cuoi file, khong sua bat ky dong nao khac.
"""

PATCH = '''

# ---------- LG03 restore (4578d3f): user persistence API ----------
# Da bi mat trong commit 0d6ce55 (LG02 mojibake hotfix). Phuc hoi co gioi han.

def load_users() -> dict[str, dict[str, Any]]:
    """Toan bo user documents (gom password_hash — chi core.auth dung de xac thuc)."""
    db = get_db()
    if db is None:
        return {}
    return {
        str(doc["username"]): {k: v for k, v in doc.items() if k != "_id"}
        for doc in db.users.find({}, {"_id": 0})
        if doc.get("username") and not doc.get("is_deleted")
    }

def save_user(document: dict[str, Any]) -> bool:
    """Tao hoac cap nhat user theo khoa username; ghi audit."""
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
    """Cap nhat user da ton tai; khong tao moi.
    - payload={{...}}: partial $set (caller hien tai views/web_app.py)
    - document={{...}}: full $set document (caller legacy)
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
    """Soft delete user (giu audit trail); hard delete chi khi is_deleted san."""
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
# ---------- /LG03 restore ----------
'''


def main() -> int:
    path = "core/database.py"
    src = open(path, encoding="utf-8").read()
    if "def load_users()" in src:
        print("SKIP: user API da co trong database.py")
        return 0
    for name in ("LOGGER", "utc_now", "_actor", "_audit", "get_db"):
        if name not in src:
            print(f"FAIL: phu thuoc {name} thieu trong database.py")
            return 2
    open(path, "w", encoding="utf-8").write(src + PATCH)
    compile(open(path, encoding="utf-8").read(), path, "exec")
    print("OK: da append 4 ham user API vao core/database.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
