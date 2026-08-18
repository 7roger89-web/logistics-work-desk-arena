"""Khoi phuc core/database.py sach tu commit 82c8134 va ap lai cong R4.

Buoc:
1. Lay core/database.py tu 82c8134 (ban sach, truoc khi mojibake).
2. Thay the than ham delete_shipment bang phien ban co cong RBAC R4
   (has_write_permission("shipment_delete") -> PermissionDeniedError).
3. Compile + kiem tra Vietnamese + luu vao core/database.py.

Cong R4 da duoc kiem chung o buoc preflight R6 (trc khi mojibake xuat hien
la do push cua Owner lam hong encoding, khong phai do code sai).
"""
from __future__ import annotations

import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]

GATE_OLD = '''def delete_shipment(sid: str, reason: str = "") -> bool:
    db = get_db()
    if db is None:
        return False'''

GATE_NEW = '''def delete_shipment(sid: str, reason: str = "") -> bool:
    # LOG-LG02 R4 bounded tightening: backend gate, so soft delete can never
    # execute through a UI-only authorization defect.
    from core.auth import has_write_permission  # noqa: PLC0415
    if not has_write_permission("shipment_delete"):
        from core.auth import PermissionDeniedError  # noqa: PLC0415
        raise PermissionDeniedError("shipment_delete")
    db = get_db()
    if db is None:
        return False'''


def main() -> None:
    r = subprocess.run(
        ["git", "show", "82c8134:core/database.py"],
        capture_output=True, cwd=str(REPO),
    )
    assert r.returncode == 0, r.stderr.decode()
    base = r.stdout.decode("utf-8")

    assert GATE_OLD in base, "khong tim thay delete_shipment goc trong ban sach"
    fixed = base.replace(GATE_OLD, GATE_NEW, 1)

    dest = REPO / "core" / "database.py"
    fixed.encode("utf-8")
    compile(fixed, str(dest), "exec")
    dest.write_text(fixed, encoding="utf-8")

    fffd = fixed.count("\ufffd")
    import re
    moj = re.findall(r"Táº¡o|LÃ´|KhÃ¡ch|cháº¡y| triá»ƒn", fixed)
    print(f"RESULT: fffd={fffd} mojibake_samples={len(moj)} len={len(fixed)}",
          flush=True)


if __name__ == "__main__":
    main()
