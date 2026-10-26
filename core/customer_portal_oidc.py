"""Google OIDC adapter for the single Streamlit customer portal.

This module never invents or accepts a customer identity.  It only reads the
identity that Streamlit's OIDC callback verified into ``st.user``, checks that
the session belongs to this deployment, and returns a verified email to
``core.customer_portal.build_customer_principal``.  ``st.login("google")`` is
called only from an explicit customer-login button; the OAuth callback is
handled by Streamlit's existing ``/oauth2callback`` route and redirects to the
same app entrypoint.

No Client ID, Client Secret, cookie secret or provider credential is stored in
source.  Missing/placeholder configuration is detected before ``st.login`` and
the customer surface remains fail-closed.
"""
from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field
from importlib import metadata
from typing import Any, Mapping
from urllib.parse import urlparse

import streamlit as st

LOGGER = logging.getLogger("logistics.customer_portal_oidc")

GOOGLE_PROVIDER = "google"
GOOGLE_METADATA_HOST = "accounts.google.com"
GOOGLE_METADATA_PATH = "/.well-known/openid-configuration"

STATE_NONE = "NONE"
STATE_AUTHENTICATED = "AUTHENTICATED"
STATE_DENIED = "DENIED"
STATE_EXPIRED = "EXPIRED"
STATE_CONFIG_ERROR = "CONFIG_ERROR"

_PLACEHOLDER_MARKERS = ("YOUR_", "YOUR-", "REPLACE", "CHANGE_ME", "PLACEHOLDER", "XXX", "TODO")
_REQUIRED_SHARED = ("redirect_uri", "cookie_secret")
_REQUIRED_PROVIDER = ("client_id", "client_secret", "server_metadata_url")


@dataclass(frozen=True)
class OidcConfigStatus:
    ready: bool
    missing: tuple[str, ...]
    redirect_origin: str = ""
    client_id: str = field(default="", repr=False)


@dataclass(frozen=True)
class OidcSessionState:
    kind: str
    email: str = ""
    reason: str = ""


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _usable(value: Any, *, min_length: int = 1) -> bool:
    if not isinstance(value, str):
        return False
    text = value.strip()
    if len(text) < min_length:
        return False
    upper = text.upper()
    return not any(marker in upper for marker in _PLACEHOLDER_MARKERS)


def _auth_section(explicit: Mapping[str, Any] | None = None) -> Mapping[str, Any]:
    if explicit is not None:
        return _mapping(explicit)
    try:
        section = st.secrets.get("auth", {})
        if isinstance(section, Mapping) and section:
            return section
    except Exception:  # noqa: BLE001 - bare mode / missing secrets file
        pass
    try:
        # CLI fallback uses the same file-secrets loader as core.config; this
        # path is only for config inspection, never to mint an identity.
        from core.config import _load_file_secrets

        payload, _ = _load_file_secrets()
        return _mapping(payload.get("auth", {}))
    except Exception:  # noqa: BLE001
        return {}


def _authlib_ready() -> bool:
    try:
        raw = metadata.version("authlib")
    except metadata.PackageNotFoundError:
        return False
    except Exception:  # noqa: BLE001
        return False
    parts = tuple(int(part) for part in re.findall(r"\d+", raw)[:3])
    # Pad a short version (e.g. "1.3") with zeroes: 1.3.0 is NOT >= 1.3.2.
    return (parts + (0, 0, 0))[:3] >= (1, 3, 2)


def _valid_google_metadata(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = urlparse(value.strip())
    except ValueError:
        return False
    return (parsed.scheme == "https"
            and parsed.netloc == GOOGLE_METADATA_HOST
            and parsed.path.rstrip("/") == GOOGLE_METADATA_PATH.rstrip("/"))


def _redirect_origin(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    try:
        parsed = urlparse(value.strip())
    except ValueError:
        return ""
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return ""
    if not parsed.path.rstrip("/").endswith("oauth2callback"):
        return ""
    if parsed.query or parsed.fragment:
        return ""
    return f"{parsed.scheme}://{parsed.netloc}"


def inspect_oidc_config(auth_section: Mapping[str, Any] | None = None) -> OidcConfigStatus:
    """Return a secret-free readiness report for Streamlit's Google provider."""
    section = _mapping(_auth_section(auth_section))
    provider = _mapping(section.get(GOOGLE_PROVIDER))
    missing: list[str] = []

    for key in _REQUIRED_SHARED:
        if key not in section:
            missing.append(f"auth.{key}")
    origin = _redirect_origin(section.get("redirect_uri"))
    if "auth.redirect_uri" not in missing and not origin:
        missing.append("auth.redirect_uri.invalid")
    if "auth.cookie_secret" not in missing and not _usable(section.get("cookie_secret"), min_length=32):
        missing.append("auth.cookie_secret.invalid")

    for key in _REQUIRED_PROVIDER:
        if key not in provider or not _usable(provider.get(key), min_length=8):
            missing.append(f"auth.google.{key}")
    if "auth.google.server_metadata_url" not in missing and not _valid_google_metadata(provider.get("server_metadata_url")):
        missing.append("auth.google.server_metadata_url.invalid")

    if not _authlib_ready():
        missing.append("Authlib>=1.3.2")
    if not all(hasattr(st, name) for name in ("login", "logout", "user")):
        missing.append("streamlit>=1.51")

    ready = not missing
    return OidcConfigStatus(
        ready=ready,
        missing=tuple(missing),
        redirect_origin=origin if ready else "",
        client_id=str(provider.get("client_id") or "") if ready else "",
    )


def _read_user_info() -> dict[str, Any]:
    try:
        user = st.user
        raw = user.to_dict() if hasattr(user, "to_dict") else dict(user)
        return dict(raw) if isinstance(raw, Mapping) else {}
    except Exception:  # noqa: BLE001 - unconfigured OIDC is an anonymous session
        return {}


def _email_verified(value: Any) -> bool:
    return value is True or (isinstance(value, str) and value.strip().lower() == "true")


def _not_expired(value: Any, now: float | None = None) -> bool:
    try:
        expires_at = float(value)
    except (TypeError, ValueError):
        return False
    return expires_at > (time.time() if now is None else now)


def _normalize_verified_email(value: Any) -> str:
    # Imported lazily so importing the OIDC adapter on the internal login path
    # never pulls the database graph into that critical path.
    from core.customer_portal import normalize_email

    return normalize_email(value)


def current_oidc_session(auth_section: Mapping[str, Any] | None = None) -> OidcSessionState:
    """Interpret the post-redirect Streamlit OIDC session, fail-closed.

    ``provider``, ``origin``, ``aud`` and ``is_logged_in`` bind the cookie to
    this app's Google provider.  Google's ``email_verified`` claim and the ID
    token's ``exp`` claim are also checked before any customer lookup.
    """
    info = _read_user_info()
    if info.get("is_logged_in") is not True or info.get("provider") != GOOGLE_PROVIDER:
        return OidcSessionState(STATE_NONE)
    config = inspect_oidc_config(auth_section)
    if not config.ready:
        return OidcSessionState(STATE_CONFIG_ERROR, reason="oidc_config_incomplete")
    if str(info.get("origin") or "") != config.redirect_origin:
        return OidcSessionState(STATE_DENIED, reason="origin_mismatch")
    if str(info.get("aud") or "") != config.client_id:
        return OidcSessionState(STATE_DENIED, reason="audience_mismatch")
    issuer = str(info.get("iss") or "").strip().rstrip("/")
    if issuer not in {"https://accounts.google.com", "accounts.google.com"}:
        return OidcSessionState(STATE_DENIED, reason="issuer_mismatch")
    if not _email_verified(info.get("email_verified")):
        return OidcSessionState(STATE_DENIED, reason="email_not_verified")
    if not _not_expired(info.get("exp")):
        return OidcSessionState(STATE_EXPIRED, reason="identity_expired")
    email = _normalize_verified_email(info.get("email"))
    if not email:
        return OidcSessionState(STATE_DENIED, reason="email_missing")
    return OidcSessionState(STATE_AUTHENTICATED, email=email)


def start_customer_login(auth_section: Mapping[str, Any] | None = None) -> bool:
    """Start Google OIDC only when explicitly requested and config is valid."""
    if not inspect_oidc_config(auth_section).ready:
        return False
    try:
        st.login(GOOGLE_PROVIDER)
        return True
    except Exception as exc:  # noqa: BLE001 - show a generic config state, no secrets
        LOGGER.warning("CUSTOMER_PORTAL_LOGIN_START_FAILED type=%s", type(exc).__name__)
        return False


def activate_customer_session() -> None:
    """Keep an internal password session from coexisting with customer OIDC."""
    try:
        st.session_state.pop("current_user", None)
    except Exception:  # noqa: BLE001
        pass


def logout_customer() -> None:
    """Clear customer-only UI state, the internal session and the OIDC cookie."""
    try:
        for key in list(st.session_state.keys()):
            if str(key).startswith("customer_portal_"):
                st.session_state.pop(key, None)
        st.session_state.pop("current_user", None)
    except Exception:  # noqa: BLE001
        pass
    try:
        st.logout()
    except Exception as exc:  # noqa: BLE001 - st.logout may stop the script
        LOGGER.warning("CUSTOMER_PORTAL_LOGOUT_STOPPED type=%s", type(exc).__name__)
