#!/usr/bin/env python3
"""Generate the LOGI_USER_ACCESS_WORKSPACE_01 / _MANAGEMENT_01 DOM fixture.

The fixture comes from the real, isolated mongomock staging view-model — never
from hand-written browser data and never from production. It captures:

* ``empty``: the staging deployment as it is, with NO account in the user
  collection and NO session logged in. The /nguoi-dung page must render the
  canonical permission matrix plus an honest empty state for accounts (no
  fabricated user), and stays read-only (no session ⇒ no Admin).
* ``journey``: three accounts created through the EXISTING canonical user
  builder + writer (``core.users.build_user_document`` +
  ``core.database.save_user``), viewed by a NON-ADMIN session (Support) — the
  read-only DOM acceptance runs against THIS variant: no management control
  may render for a non-Admin viewer.
* ``journeyAdmin``: the exact same accounts, viewed by the Admin session that
  created them (``canManage: true``) — the Admin-capable DOM acceptance runs
  against THIS variant: "+ THÊM TÀI KHOẢN" and the per-account management
  actions must render.

Run:  .venv/bin/python scripts/gen_user_access_fixture.py
Out:  tests/component/fixtures/view_model_user_access.json
"""

from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
OUT = ROOT / "tests" / "component" / "fixtures" / "view_model_user_access.json"

# (username, display name, role, active) — roles are exactly SUPPORTED_ROLES.
USERS = (
    ("thu-hang", "Thu Hằng", "support", True),
    ("minh-tu", "Minh Tú", "sale", True),
    ("lan-viewer", "Lan (tạm khóa)", "sale", False),
)


def main() -> None:
    import streamlit as st

    from core.database import get_db, save_user
    from core.users import build_user_document, set_active
    from views import logi_sandbox
    from views import logi_view_model as vm

    logi_sandbox.reset_backend()
    transport = logi_sandbox.ensure_backend()
    assert transport == logi_sandbox.SANDBOX_TRANSPORT, "fixture must not touch production"

    previous = st.session_state.get("current_user")

    # The staging seed carries three reference accounts; the ``empty`` variant
    # below must show the page's honest no-accounts state, so the users
    # collection is cleared on the isolated mongomock staging database only.
    seeded = vm.build_view_model()
    assert seeded["userAccess"]["counts"]["userCount"] == 3, (
        "expected the three staging seed accounts"
    )
    get_db().users.delete_many({})
    st.session_state.pop("current_user", None)

    empty = vm.build_view_model()
    assert empty["userAccess"]["readOnly"] is True
    assert empty["userAccess"]["canManage"] is False
    assert empty["userAccess"]["counts"]["userCount"] == 0
    assert empty["userAccess"]["users"] == []
    assert empty["userAccess"]["counts"]["roleCount"] > 0, "matrix must exist with no account"

    # save_user is Admin-gated on purpose — the fixture logs a staging Admin
    # in so the CANONICAL writer (not a direct collection insert) is used.
    st.session_state["current_user"] = {
        "user_id": "STAGING-ADMIN",
        "username": "staging.admin",
        "display_name": "Quản trị (Preview/Staging)",
        "role": "admin",
    }
    documents = []
    for username, display_name, role, active in USERS:
        document = build_user_document(
            username=username,
            password="staging-only-passphrase",
            display_name=display_name,
            role=role,
            created_by="staging.admin",
        )
        if not active:
            document = set_active(document, False, actor="staging.admin")
        assert save_user(document), f"staging user write failed for {username}"
        documents.append(document)

    journey_admin = vm.build_view_model()
    user_access_admin = journey_admin["userAccess"]
    assert user_access_admin["counts"]["userCount"] == len(USERS)
    assert user_access_admin["currentUser"]["username"] == "staging.admin"
    assert user_access_admin["canManage"] is True
    assert user_access_admin["readOnly"] is False

    # The SAME accounts, viewed by a non-Admin (Support) session — proves the
    # management controls never render for a non-Admin viewer, even though
    # the account list itself is identical.
    st.session_state["current_user"] = {
        "user_id": "STAGING-SUPPORT",
        "username": "thu-hang",
        "display_name": "Thu Hằng",
        "role": "support",
    }
    journey = vm.build_view_model()
    user_access = journey["userAccess"]
    assert user_access["counts"]["userCount"] == len(USERS)
    assert user_access["currentUser"]["username"] == "thu-hang"
    assert user_access["canManage"] is False
    assert user_access["readOnly"] is True

    # The password used to build the fixtures must never reach either payload.
    for payload in (user_access, user_access_admin):
        assert "staging-only-passphrase" not in repr(payload)
        assert "pbkdf2_sha256$" not in repr(payload)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {
                "generatedFrom": "scripts/gen_user_access_fixture.py — isolated mongomock staging",
                "empty": empty,
                "journey": journey,
                "journeyAdmin": journey_admin,
            },
            ensure_ascii=False,
            indent=1,
            default=str,
        ),
        encoding="utf-8",
    )

    print(f"wrote {OUT.relative_to(ROOT)}")
    print(
        "  empty: "
        f"users={empty['userAccess']['counts']['userCount']} "
        f"roles={empty['userAccess']['counts']['roleCount']}"
    )
    print(
        "  journey (non-admin): "
        f"users={user_access['counts']['userCount']} "
        f"active={user_access['counts']['activeCount']} "
        f"roles={user_access['counts']['roleCount']} "
        f"currentUser={user_access['currentUser']['username']} "
        f"canManage={user_access['canManage']}"
    )
    print(
        "  journeyAdmin: "
        f"users={user_access_admin['counts']['userCount']} "
        f"currentUser={user_access_admin['currentUser']['username']} "
        f"canManage={user_access_admin['canManage']}"
    )

    logi_sandbox.reset_backend()
    if previous is None:
        st.session_state.pop("current_user", None)
    else:
        st.session_state["current_user"] = previous


if __name__ == "__main__":
    main()
