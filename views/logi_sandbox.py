"""Isolated staging transport for the Logi-good component (Phase B).

PRODUCTION DB IS NEVER USED BY THIS MODULE.

Transport selection (fail-safe, no credentials invented):

* If a real ``MONGO_URI`` is already configured, it takes precedence and this
  module patches NOTHING — the app talks to the real database exactly as
  before.
* Otherwise an isolated in-process ``mongomock`` transport is installed so the
  CURRENT canonical writers (``core.database.save_shipment_atomic``,
  ``save_direct_shipment_payment``, ``save_direct_payment_correction``, …) run
  **unchanged** against staging data.

Why a shim is needed at all
---------------------------
``core.database`` performs its shipment/financial writes inside
``client.start_session()`` + ``session.start_transaction()``.  mongomock 4.3
does not implement client sessions: every collection operation starts with
``if session: raise_not_implemented('session', …)``.

The smallest possible compatibility surface is therefore a session object that
is **falsy** (``__bool__ -> False``) and acts as a no-op context manager.  That
satisfies both ``with client.start_session()`` /
``with session.start_transaction()`` and mongomock's ``if session:`` guard, so
the canonical writers execute verbatim.  No business logic, ordering, audit
call, or fingerprint check is altered.

The shim is installed ONLY when the transport is mongomock.  A real pymongo
``ClientSession`` is truthy, so real transactional behaviour is untouched.
"""

from __future__ import annotations

import logging
from typing import Any

LOGGER = logging.getLogger("logistics_pro.logi_sandbox")

STAGING_DB_NAME = "logistics_staging"
STAGING_URI_PLACEHOLDER = "mongodb://mongomock.local/logistics_staging"

REAL_TRANSPORT = "REAL_MONGO"
SANDBOX_TRANSPORT = "SANDBOX_STAGING"


class _SandboxSession:
    """Falsy no-op session/transaction.

    * ``__bool__`` is False so mongomock's ``if session:`` guard is not tripped.
    * Usable as ``with client.start_session() as session`` and
      ``with session.start_transaction()``.
    * Carries no data and grants no capability — it exists purely so the
      existing transactional writers can run on the sandbox transport.
    """

    def __bool__(self) -> bool:  # pragma: no cover - trivial
        return False

    def __enter__(self) -> "_SandboxSession":
        return self

    def __exit__(self, *exc: Any) -> bool:
        return False

    def start_transaction(self) -> "_SandboxSession":
        return self

    def abort_transaction(self) -> None:
        return None

    def commit_transaction(self) -> None:
        return None


def _install_session_shim(client: Any) -> None:
    """Give a mongomock client the tiny session surface writers expect."""
    try:
        client.start_session()  # noqa: B018 - probe real capability
        return  # real sessions available; nothing to do
    except NotImplementedError:
        pass
    except Exception:  # pragma: no cover - unexpected transport behaviour
        return
    client.start_session = lambda *args, **kwargs: _SandboxSession()


_state: dict[str, Any] = {"transport": None, "client": None, "seeded": False}

# Captured at import, BEFORE the sandbox ever patches core.config, so the
# sandbox's own placeholder URI can never later be mistaken for a real one.
try:
    from core import config as _core_config_at_import

    _ORIGINAL_MONGO_URI = str(getattr(_core_config_at_import, "MONGO_URI", "") or "").strip()
except Exception:  # pragma: no cover - core.config always importable in-repo
    _ORIGINAL_MONGO_URI = ""

#: ``core.database._init_connection_impl`` as it was BEFORE any sandbox
#: install.  reset_backend() restores it (see below).
try:
    from core import database as _core_database_at_import

    _ORIGINAL_INIT_CONNECTION_IMPL = _core_database_at_import._init_connection_impl
except Exception:  # pragma: no cover - core.database always importable in-repo
    _ORIGINAL_INIT_CONNECTION_IMPL = None


def transport_name() -> str | None:
    return _state["transport"]


def _real_uri_configured() -> str:
    """The operator-supplied MONGO_URI, ignoring our own sandbox placeholder."""
    if _ORIGINAL_MONGO_URI and _ORIGINAL_MONGO_URI != STAGING_URI_PLACEHOLDER:
        return _ORIGINAL_MONGO_URI
    return ""


def _install_sandbox_transport():
    """Point ``core.database`` at an isolated mongomock staging database."""
    import mongomock

    # The default attachment backend is GridFS. Enable mongomock's isolated
    # GridFS integration for Preview/Staging only; this never changes the real
    # MongoDB path or any production configuration.
    try:
        import mongomock.gridfs
        mongomock.gridfs.enable_gridfs_integration()
    except Exception:  # pragma: no cover - version-specific optional shim
        pass

    from core import config as core_config
    from core import database as core_database

    client = mongomock.MongoClient()
    _install_session_shim(client)

    # LOG-REL-01 environment isolation is honoured for real (not stubbed):
    # the sandbox declares itself a staging identity with a staging DB name, so
    # core.config.validate_mongo_identity() passes on its own terms and would
    # still refuse a production DB name.
    core_config.MONGO_URI = STAGING_URI_PLACEHOLDER
    core_config.MONGO_DB_NAME = STAGING_DB_NAME
    core_config.ENV_IDENTITY = "PREVIEW"
    if STAGING_DB_NAME not in core_config.MONGO_ALLOWED_DB_NAMES:
        core_config.MONGO_ALLOWED_DB_NAMES = list(core_config.MONGO_ALLOWED_DB_NAMES) + [STAGING_DB_NAME]

    # core.database binds these names at import time; keep them consistent.
    core_database.MONGO_URI = STAGING_URI_PLACEHOLDER
    core_database.MONGO_DB_NAME = STAGING_DB_NAME

    def _staging_connection():
        return client

    core_database._init_connection_impl = _staging_connection

    _state["client"] = client
    _state["transport"] = SANDBOX_TRANSPORT
    return client


# The sandbox has no real user store, so it runs as one explicit staging
# operator. RBAC is still enforced for real against this identity by
# core.auth — this only supplies WHO the actor is, never WHAT is allowed.
STAGING_ACTOR = {
    "username": "staging.support",
    "full_name": "Thu Hằng (Preview/Staging)",
    "role": "SUPPORT",
    "user_id": "STAGING-SUPPORT",
}


def ensure_staging_actor() -> dict[str, str]:
    """Log in the explicit staging operator when nothing else is logged in.

    Never overrides a real login, and is only ever applied on the sandbox
    transport. The UI labels the environment honestly as Preview/Staging.
    """
    import streamlit as st

    existing = st.session_state.get("current_user")
    if isinstance(existing, dict) and existing.get("username"):
        return existing
    try:
        st.session_state["current_user"] = dict(STAGING_ACTOR)
    except Exception:  # pragma: no cover - non-Streamlit context
        pass
    return dict(STAGING_ACTOR)


def ensure_backend(*, force_reseed: bool = False) -> str:
    """Select the transport once and return which one is active.

    Returns ``REAL_MONGO`` when a real URI is configured, otherwise
    ``SANDBOX_STAGING`` (isolated mongomock, seeded with representative
    real-schema staging documents).
    """
    if _state["transport"] == REAL_TRANSPORT:
        return REAL_TRANSPORT

    if _real_uri_configured():
        # A real MONGO_URI always takes precedence outside the sandbox.
        _state["transport"] = REAL_TRANSPORT
        return REAL_TRANSPORT

    if _state["transport"] is None:
        _install_sandbox_transport()

    actor = ensure_staging_actor()

    if force_reseed or not _state["seeded"]:
        from views import logi_staging_seed

        logi_staging_seed.seed_staging(actor=actor.get("username", "staging.support"))
        _state["seeded"] = True

    return SANDBOX_TRANSPORT


def reset_backend() -> None:
    """Drop the sandbox transport (used by tests for a clean database).

    Dropping ``_state`` alone is not enough: ``_install_sandbox_transport``
    bound ``core.database._init_connection_impl`` to a closure over ITS client,
    so every reader kept talking to the previous, already-seeded mongomock
    database after a reset.  A later test then saw stale users/shipments it
    never created (Issue #247: the first-admin bootstrap screen silently became
    a login screen because the canonical user store still held three seeded
    accounts).  A reset must therefore also unbind that connection.
    """
    _state["transport"] = None
    _state["client"] = None
    _state["seeded"] = False
    if _ORIGINAL_INIT_CONNECTION_IMPL is not None:
        from core import database as core_database

        core_database._init_connection_impl = _ORIGINAL_INIT_CONNECTION_IMPL
