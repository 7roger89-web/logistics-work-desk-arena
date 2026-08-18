"""LG03 bounded restore #2: phuc hoi load_agreements + save_agreements_to_cloud.

Da bi mat trong commit 0d6ce55 (LG02 hotfix), gay ImportError tai
core/state.py + views/agreements.py (xac nhan ton tai tai baseline main).
Append cuoi file, khong sua dong nao khac.
"""

PATCH = '''

# ---------- LG03 restore #2 (83a567c): agreements API ----------

def load_agreements() -> dict[str, dict[str, Any]]:
    """Load LOG-C13 commercial agreements (agreed commercial terms, not finance)."""
    return _load_dict("agreements", query={"is_deleted": {"$ne": True}})

def save_agreements_to_cloud(agreements_dict: dict[str, dict[str, Any]]) -> bool:
    """Upsert commercial agreements. 0 canonical finance writes by contract."""
    return all(_save_document("agreements", document) for document in agreements_dict.values())

# ---------- /LG03 restore #2 ----------
'''


def main() -> int:
    path = "core/database.py"
    src = open(path, encoding="utf-8").read()
    if "def load_agreements()" in src:
        print("SKIP: load_agreements da co")
        return 0
    for name in ("_load_dict", "_save_document"):
        if name not in src:
            print(f"FAIL: phu thuoc {name} thieu")
            return 2
    open(path, "w", encoding="utf-8").write(src + PATCH)
    compile(open(path, encoding="utf-8").read(), path, "exec")
    print("OK: da append load_agreements + save_agreements_to_cloud")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
