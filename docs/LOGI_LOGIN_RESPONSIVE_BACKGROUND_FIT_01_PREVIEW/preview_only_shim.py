"""Preview-only staging shim for the LIVE PR #102 owner preview.

NOT APPLICATION CODE. This module is never imported by the app; it is loaded only
when a preview/test process puts this directory on `PYTHONPATH` (as `sitecustomize`).
It is kept in `docs/` purely so the preview run is reproducible.


Two preview-layer capabilities, neither of which changes the repository code:

1. Staging transport: `pymongo.MongoClient` -> in-process `mongomock`, the
   sandbox/preview transport this repository already declares in
   requirements.txt, plus one local staging user so the real LOGIN form renders.
   No production URI / credential / database is used or contacted.

2. Optional background pinning for Owner inspection ONLY:
   `?bg=1..10` selects a specific Owner artwork in the preview. With no `bg`
   parameter the shipped per-visit rotation behaviour is used unchanged
   (the original function is called untouched). `core/auth.py` is not modified;
   this wrapper lives only in the preview process.
"""

from __future__ import annotations

import os


def _install_pymongo_staging() -> None:
    try:
        import mongomock
        import pymongo
    except Exception:  # pragma: no cover
        return
    if getattr(pymongo, "_lg_preview_mongomock", False):
        return
    pymongo.MongoClient = mongomock.MongoClient  # type: ignore[assignment]
    pymongo._lg_preview_mongomock = True  # type: ignore[attr-defined]
    try:
        import secrets

        import core.database as dbmod
        from core.auth import hash_password

        db = dbmod.get_db()
        if db is None:
            return
        username = os.getenv("LG_PREVIEW_USER", "preview.owner")
        if db.users.find_one({"username": username}) is None:
            db.users.insert_one(
                {
                    "username": username,
                    "display_name": "Preview Owner",
                    "role": "admin",
                    "is_active": True,
                    "is_deleted": False,
                    "password_hash": hash_password(secrets.token_urlsafe(24)),
                }
            )
    except Exception:  # pragma: no cover
        pass


def _install_bg_pinning() -> None:
    """Preview-only `?bg=N` pin. Falls back to the shipped rotation."""
    try:
        import core.auth as auth
    except Exception:  # pragma: no cover
        return
    original = auth._current_login_bg_index

    def pinned() -> int:
        try:
            import streamlit as st

            raw = st.query_params.get("bg")
            if raw is not None:
                idx = int(str(raw).strip())
                if 1 <= idx <= auth._LOGIN_BG_COUNT and (auth._LOGIN_BG_DIR / f"login-bg-{idx:02d}.webp").is_file():
                    st.session_state[auth._LOGIN_BG_SESSION_KEY] = idx
                    return idx
        except Exception:
            pass
        return original()

    auth._current_login_bg_index = pinned  # type: ignore[assignment]


_install_pymongo_staging()
_install_bg_pinning()
