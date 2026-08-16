import streamlit as st
import pandas as pd
from core.database import get_worksheet, load_data, TAB_SHIPMENTS, safe_float
from core.utils import log_info, log_error
import time  # For retry

TAB_ARCHIVE = "Archive_Shipments"

def process_archiving():
    """
    1. Quét các lô 'done' và hết nợ.
    2. Copy sang Archive_Shipments.
    3. Xóa khỏi Shipments với batch delete.
    """
    # 1. Load dữ liệu ACTIVE hiện tại (bypass cache)
    current_data = load_data.__wrapped__(TAB_SHIPMENTS)
    
    to_archive = []
    ids_to_remove = []
    
    for sid, ship in current_data.items():
        status = ship.get('status', 'wait')
        if status != 'done': continue
        
        total = safe_float(ship.get('total_amount', 0))
        payments = ship.get('data', {}).get('3.4', {}).get('payments', [])
        paid = sum([safe_float(p.get('amount', 0)) for p in payments])
        debt = total - paid
        
        if debt <= 5000:  # Threshold configurable
            to_archive.append(ship)
            ids_to_remove.append(str(sid))  # Ensure str for comparison
    
    if not to_archive:
        return 0, "Không có lô nào đủ điều kiện lưu trữ (Phải xong & hết nợ)."

    ws_active = get_worksheet(TAB_SHIPMENTS)
    ws_archive = get_worksheet(TAB_ARCHIVE)
    
    if not ws_active or not ws_archive:
        return 0, "Lỗi kết nối Google Sheet."

    def retry_operation(func, max_retries=3, delay=2):
        for attempt in range(max_retries):
            try:
                return func()
            except Exception as e:
                log_error(f"Retry {attempt+1}/{max_retries}: {e}")
                time.sleep(delay)
        raise Exception("Max retries exceeded.")

    try:
        # A. Chuẩn bị rows cho archive
        rows_to_append = []
        for ship in to_archive:
            import json
            from core.database import json_serial
            nested_data = ship.get('data', {})
            details_json = json.dumps(nested_data, default=json_serial, ensure_ascii=False)
            
            row = [
                str(ship.get('id', '')), str(ship.get('customer', '')), str(ship.get('status', '')),
                str(ship.get('created_at', '')), str(ship.get('etd', '')), str(ship.get('eta', '')),
                str(ship.get('pol', '')), str(ship.get('pod', '')), str(ship.get('mbl', '')), str(ship.get('hbl', '')),
                str(ship.get('carrier', '')), str(ship.get('vessel', '')),
                safe_float(ship.get('vol')), safe_float(ship.get('gw')), safe_float(ship.get('qty')),
                safe_float(ship.get('total_amount')), 
                details_json
            ]
            rows_to_append.append(row)
        
        # B. Append to archive with retry
        def append_archive():
            ws_archive.append_rows(rows_to_append)
            log_info(f"Archived {len(rows_to_append)} shipments. IDs: {', '.join(ids_to_remove)}")
        retry_operation(append_archive)
        
        # C. Batch delete from active
        all_values = ws_active.get_all_values()
        header = all_values[0]
        data_rows = all_values[1:]
        
        # Find row indices to delete (reverse order for safe delete)
        rows_to_delete = []
        for idx, row in enumerate(data_rows, start=2):  # Start from row 2 (1-indexed)
            if row[0] in ids_to_remove:
                rows_to_delete.append(idx)
        
        if rows_to_delete:
            rows_to_delete.sort(reverse=True)  # Delete from bottom to top
            def delete_batch():
                for row_idx in rows_to_delete:
                    ws_active.delete_rows(row_idx)
            retry_operation(delete_batch)
            log_info(f"Deleted {len(rows_to_delete)} rows from active sheet.")
        
        # Clear Cache
        load_data.clear()
        
        return len(to_archive), f"Đã lưu trữ thành công {len(to_archive)} lô hàng!"

    except Exception as e:
        log_error(f"Archive Error: {e}")
        return 0, f"Lỗi quá trình lưu trữ: {e}"