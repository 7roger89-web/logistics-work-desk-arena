import pytest
import os
from unittest.mock import MagicMock, patch

from core.config import _parse_bool, MONGO_RELEASE_MODE, validate_mongo_identity
from core.database import get_db

def test_parse_bool():
    assert _parse_bool(True) is True
    assert _parse_bool(False) is False
    assert _parse_bool("true") is True
    assert _parse_bool("TRUE") is True
    assert _parse_bool("1") is True
    assert _parse_bool("yes") is True
    assert _parse_bool("on") is True
    assert _parse_bool("false") is False
    assert _parse_bool("0") is False
    assert _parse_bool("no") is False
    assert _parse_bool("off") is False
    assert _parse_bool(None) is False
    assert _parse_bool("") is False
    assert _parse_bool("random") is False

def test_identity_gate_enforcement(monkeypatch):
    """An unknown database name is refused by the fail-closed identity gate.

    The gate now reasons about the ENVIRONMENT IDENTITY first (LOG-REL-01):
    a STAGING/PREVIEW process may only use a staging/allowed database, and a
    PRODUCTION process may only use the production database with
    MONGO_RELEASE_MODE=true. Both branches are asserted here so a future
    relaxation of either one fails this test; the process identity is pinned
    explicitly because a previous test may have installed the sandbox identity
    (PREVIEW) on the shared ``core.config`` module.
    """
    # An explicit URI is required before the identity gate is even reached; it
    # is never dialed here (validate_mongo_identity performs no I/O), and no
    # credential of any kind is involved.
    monkeypatch.setattr("core.config.MONGO_URI", "mongodb://identity-gate.invalid:27017")
    monkeypatch.setattr("core.config.MONGO_RELEASE_MODE", True)
    monkeypatch.setattr("core.config.MONGO_DB_NAME", "wrong_db")

    # (a) PRODUCTION identity + a non-production database name.
    monkeypatch.setattr("core.config.ENV_IDENTITY", "PRODUCTION")
    with pytest.raises(RuntimeError, match="LỖI CÁCH LY"):
        validate_mongo_identity()

    # (b) STAGING/PREVIEW identity + a database that is neither staging nor
    # allowlisted → refused, and the message names the allowed staging DB.
    monkeypatch.setattr("core.config.ENV_IDENTITY", "PREVIEW")
    with pytest.raises(RuntimeError, match="yêu cầu database staging hoặc được phép"):
        validate_mongo_identity()

    # (c) The same guard is reached through the real connection seam: a client
    # handle exists, so get_db() must run the identity validation before it
    # returns a database. The handle is a stub — nothing connects.
    with patch("core.database.init_connection", return_value=MagicMock()):
        with pytest.raises(RuntimeError):
            get_db()


def test_production_identity_pass(monkeypatch):
    """PRODUCTION + production DB + release mode passes; each omission fails."""
    monkeypatch.setattr("core.config.MONGO_URI", "mongodb://identity-gate.invalid:27017")
    monkeypatch.setattr("core.config.MONGO_DB_NAME", "logistics_db")

    # Release mode OFF → production is refused.
    monkeypatch.setattr("core.config.MONGO_RELEASE_MODE", False)
    monkeypatch.setattr("core.config.ENV_IDENTITY", "PRODUCTION")
    with pytest.raises(RuntimeError, match="MONGO_RELEASE_MODE=true"):
        validate_mongo_identity()

    # Release mode ON → the documented production configuration passes.
    monkeypatch.setattr("core.config.MONGO_RELEASE_MODE", True)
    validate_mongo_identity()

    # The same production database is REFUSED when the process claims
    # STAGING/PREVIEW: no environment may write the production DB by accident.
    for identity in ("STAGING", "PREVIEW"):
        monkeypatch.setattr("core.config.ENV_IDENTITY", identity)
        with pytest.raises(RuntimeError, match="LỖI CÁCH LY NGUY HIỂM"):
            validate_mongo_identity()

def test_audit_redaction_sensitive_fields():
    """Verify password_hash is redacted in audit logs."""
    from core.database import _audit
    from unittest.mock import MagicMock
    from typing import Mapping
    
    mock_db = MagicMock()
    sensitive_data = {"username": "testuser", "password_hash": "secret_hash", "role": "admin"}
    
    _audit(mock_db, "user", "testuser", "update", before=None, after=sensitive_data)
    
    # Check the call to insert_one
    args, kwargs = mock_db.audit_logs.insert_one.call_args
    audit_doc = args[0]
    
    assert audit_doc["after"]["username"] == "testuser"
    assert "password_hash" not in audit_doc["after"]
    assert audit_doc["after"]["role"] == "admin"
