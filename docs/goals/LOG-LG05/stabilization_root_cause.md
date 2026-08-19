# UX STABILIZATION — ROOT CAUSE ANALYSIS

## P0: Delete Safety
**Finding UX-014 was INACCURATE** — confirmation already exists!
- UI button: `views/dashboard.py:827` — `c_del.button("🗑️ XÓA", key="btn_del_top")`
- Action: Sets `confirm_delete_sid` + `st.rerun()`
- Confirmation: `views/dashboard.py:840-846` — Shows warning "Lô sẽ được đưa vào thùng lưu trữ..." + "✅ XÁC NHẬN XÓA" / "Hủy bỏ" buttons
- DB function: `core/database.py:769` — `delete_shipment()` = **SOFT DELETE** (is_deleted=True, deleted_at, deleted_by, delete_reason)
- Has: permission guard (has_write_permission), audit log
- **Action needed: NONE for delete path — already safe**
- However, we can improve UX by making confirmation more prominent

## P1: Stuck Loading on Close
**Root cause:** `views/web_app.py:412-413` — `st.spinner("Đang đồng bộ dữ liệu hệ thống...")` wraps `refresh_core_data()` on EVERY rerun, including form close/cancel.
- When user clicks ❌ to close form → `st.rerun()` → spinner shown → even though `refresh_core_data()` returns early (data_loaded=True, needs_refresh=False), the spinner still renders
- The visual spinner makes the page appear "stuck" even though no actual DB work is done
- **Fix:** Only show spinner when `not data_loaded or needs_refresh`

## P1: Login 60s Latency
**Root cause:** Same as above — first login triggers `refresh_core_data()` which calls:
- `load_data()` → st.cache_data(ttl=30) → DB query
- `load_customers()` → st.cache_data → DB query
- `load_contracts()` → DB query
- `load_agreements()` → DB query
- `load_rate_cards()` → DB query
- On COLD cache (first load), each DB query to MongoDB Atlas takes 1-5s
- 5 queries × 2-10s each = 10-50s total
- The `st.spinner` blocks the entire UI during this period
- **Fix:** (1) Only show spinner when needed, (2) Reduce number of queries on login, (3) Consider lazy-loading non-essential data

## P1: "Vì sao ra số này?" Overload
**Current behavior:** Each shipment card renders ALL UNKNOWN bullets in a collapsible `<details>` section
- 13 cards × 7 bullets = 91 bullets visible
- **Fix:** Show compact badge "7 mục chưa xác định" by default, expand only on click
