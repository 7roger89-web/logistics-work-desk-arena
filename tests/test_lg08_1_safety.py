import pytest
import os
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
    # Mock MONGO_RELEASE_MODE = True
    monkeypatch.setattr("core.config.MONGO_RELEASE_MODE", True)
    monkeypatch.setattr("core.config.MONGO_DB_NAME", "wrong_db")
    
    with pytest.raises(RuntimeError, match="không thuộc danh sách MONGO_ALLOWED_DB_NAMES"):
        validate_mongo_identity()
    
    # Verify get_db calls it
    with pytest.raises(RuntimeError):
        get_db()

def test_production_identity_pass(monkeypatch):
    monkeypatch.setattr("core.config.MONGO_RELEASE_MODE", True)
    monkeypatch.setattr("core.config.MONGO_DB_NAME", "logistics_db")
    # Should not raise
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
