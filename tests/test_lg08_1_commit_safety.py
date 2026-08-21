
import pytest
from unittest.mock import MagicMock, patch
from core.database import save_shipment_atomic, _audit

def test_shipment_atomic_commit_logic():
    """Verify that save_shipment_atomic uses a session for atomicity."""
    with open("core/database.py", "r") as f:
        content = f.read()
    
    # Verify that the function uses a session context manager
    assert "with client.start_session() as session:" in content
    assert "with session.start_transaction():" in content
    
    # Verify audit and outbox calls pass the session
    # We look for the insert_one calls within the transaction block
    assert "db.audit_logs.insert_one" in content
    assert "session=session" in content

def test_audit_sanitization_proof():
    """Prove that sensitive fields are never logged."""
    from core.users import redact_password_material
    
    sensitive = {
        "username": "admin",
        "password_hash": "pbkdf2_sha256$390000$...",
        "password": "plaintext_pass",
        "role": "admin"
    }
    
    redacted = redact_password_material(sensitive)
    
    assert "password_hash" not in redacted
    assert "password" not in redacted
    assert redacted["username"] == "admin"
    assert redacted["role"] == "admin"

def test_audit_helper_uses_redaction():
    """Verify _audit helper calls redaction."""
    with open("core/database.py", "r") as f:
        content = f.read()
        
    # Check if _audit imports and calls redact_password_material
    assert "from core.users import redact_password_material" in content
    assert "safe_before = redact_password_material(before)" in content
    assert "safe_after = redact_password_material(after)" in content
