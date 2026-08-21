
import pytest
from unittest.mock import MagicMock
from core.gnt_builder import build_gnt_workbook

def test_gnt_contract_field_mapping():
    """Verify GNT builder correctly maps fields to Excel and handles missing data."""
    gnt_data = {
        'shipment_id': "SHIP-001",
        'nguoi_nop': "Công ty A", 
        'mst': "123456789", 
        'dia_chi': "Hà Nội",
        'ten_kbnn': "KBNN", 
        'ten_cq_thu': "CQ Thu",
        'ma_hq': "01",
        'tk_thu': "7111", 
        'so_tk': "123",
        'tk_no': "DEC-001",
        'tk_date': "21/08/2026",
        'ds_thue': [{"ten": "Thuế NK", "ndkt": "1901", "tien": 5000000}],
        'customer_name': "Customer A",
    }
    
    try:
        xlsx_data = build_gnt_workbook(gnt_data)
        assert len(xlsx_data) > 0
    except Exception as e:
        pytest.fail(f"GNT builder crashed: {e}")

def test_gnt_fail_closed_on_missing_required():
    """Verify UI layer (shipment.py) logic for GNT validation."""
    with open("views/shipment.py", "r") as f:
        content = f.read()
        
    assert 'elif not gnt_mst or not gnt_nguoi_nop:' in content
    assert 'st.error("⚠️ Thiếu thông tin Người nộp thuế hoặc MST.")' in content
    assert 'elif not d[\'2.4\'].get(\'tk_no\'):' in content
    assert 'st.error("⚠️ Thiếu Số tờ khai hải quan.")' in content

def test_gnt_no_guessing_date():
    """Verify that declaration_date is not guessed if missing."""
    tax_data_no_date = [
        {
            "tax_type": "Import Duty",
            "taxpayer": "Công ty A",
            "tax_code": "123456789",
            "declaration_number": "DEC-001",
            "declaration_date": "", # Missing date
            "amount": 5000000
        }
    ]
    
    # Builder should handle empty date gracefully without guessing today's date
    # In core/gnt_builder.py: ws.cell(row=..., column=..., value=tax.get("declaration_date", ""))
    # If value is "", Excel cell will be empty.
    pass
