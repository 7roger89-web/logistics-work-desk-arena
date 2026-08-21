
import pytest
from unittest.mock import MagicMock, patch
from core.database import save_shipment_atomic
from core.excel_roundtrip import merge_details_idempotent

def test_getfly_idempotency_no_duplicate_lines():
    """Verify that re-importing same data results in no changes (idempotent)."""
    existing_shipment = {
        "shipment_id": "TEST-001",
        "service_details": [
            {"service_name": "Vận chuyển", "amount": 1000, "currency": "USD", "provider": "ABC"}
        ],
        "version": 1
    }
    
    new_data = {
        "service_details": [
            {"service_name": "Vận chuyển", "amount": 1000, "currency": "USD", "provider": "ABC"}
        ]
    }
    
    # merge_details_idempotent should return (merged, stats)
    merged, stats = merge_details_idempotent(existing_shipment["service_details"], new_data["service_details"])
    
    assert len(merged) == 1
    assert stats["same"] == 1
    assert stats["new"] == 0
    assert merged == existing_shipment["service_details"]

def test_getfly_finance_protection():
    """Verify that financial fields are protected during re-import."""
    existing_shipment = {
        "shipment_id": "TEST-001",
        "service_details": [
            {
                "service_name": "Vận chuyển", 
                "amount": 1000, 
                "currency": "USD",
                "provider": "ABC",
                "payment_status": "Paid", # Financial field
                "paid_amount": 1000       # Financial field
            }
        ]
    }
    
    # New data from Getfly (which doesn't have payment info)
    new_data = {
        "service_details": [
            {
                "service_name": "Vận chuyển", 
                "amount": 1000,
                "currency": "USD",
                "provider": "ABC"
            }
        ]
    }
    
    merged, stats = merge_details_idempotent(existing_shipment["service_details"], new_data["service_details"])
    
    assert merged[0]["payment_status"] == "Paid"
    assert merged[0]["paid_amount"] == 1000
    assert stats["same"] == 1

def test_no_raw_update_one_in_dashboard():
    """Verify dashboard uses save_shipment_atomic, not raw update_one."""
    with open("views/dashboard.py", "r") as f:
        content = f.read()
    
    # Search for Getfly import section
    assert "save_shipment_atomic" in content
    # Ensure no raw update_one for shipments in the import loop
    # The import loop is around the Getfly button handler
    import_loop_start = content.find("btn_lg08_import_getfly")
    if import_loop_start != -1:
        relevant_code = content[import_loop_start:import_loop_start+5000]
        assert "update_one" not in relevant_code
        assert "save_shipment_atomic" in relevant_code
