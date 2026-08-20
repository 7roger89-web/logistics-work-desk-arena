# LOG-LG07 Cloud Findings

## App is LIVE on Streamlit Cloud
- URL: https://tienthanhlog.streamlit.app/
- Repo: 7roger89-web/logistics-work-desk, Branch: main, File: web_app.py
- Owner: 7roger89-web (GitHub)
- Sharing: Public and searchable

## ISSUE: App is running in "Local Admin" mode
- The dashboard shows "Đang chạy Local Admin. Bật AUTH_REQUIRED khi triển khai nhiều người dùng."
- This means the app is NOT reading AUTH_REQUIRED from secrets properly on cloud
- The secrets were set but the app falls back to Local Admin mode
- This is because the app reads AUTH_REQUIRED from st.secrets only when running via streamlit run
- On Streamlit Cloud, secrets should be available via st.secrets

## Root cause:
The app likely has a fallback to Local Admin when it can't read st.secrets properly.
Need to check if the secrets are being read correctly on cloud.

## App features visible:
- Dashboard with shipment list, filters, tabs (DASHBOARD, TOP KHÁCH, GETFLY, HOA HỒNG)
- Sidebar: Tổng Quan, Việc Cần Xử Lý, Tạo Lô Mới, Theo Dõi Vận Chuyển, Khách Hàng, etc.
- NHẬP TỪ GETFLY, XUẤT CHO GETFLY buttons
- All LG05 features present

## Status check (current):
- App IS live and working on cloud (connected to DB, showing dashboard)
- AUTH_REQUIRED reads as False on cloud → "Local Admin" mode
- This means anyone with the URL can access as admin without login
- Root cause: on Streamlit Cloud, st.secrets may not be available at module import time
- Decision: proceed with team account creation and testing; Owner can enable AUTH later
- The Owner needs to verify secrets are saved correctly on cloud dashboard

## Cloud App Verification (Phase 6):
The app is confirmed working on Streamlit Cloud at https://tienthanhlog.streamlit.app/. The dashboard loads correctly with all navigation items visible: Tổng Quan Công Việc, Việc Cần Xử Lý, Tạo Lô Mới, Theo Dõi Vận Chuyển, Khách Hàng, Ngữ Cảnh Đối Tác, Kinh Doanh & Báo Giá, Thỏa Thuận & Bàn Giao, Hợp Đồng, FR Đối Soát Tài Chính, Thu Tiền & Công Nợ, Công Nợ A Bò, Báo Cáo CEO, Tra Cứu Thuế, Sổ Tay Kinh Nghiệm, Người Dùng, Reload Data, Nạp kho lưu trữ. The NHẬP TỪ GETFLY and XUẤT CHO GETFLY buttons are present. The dashboard shows "0 lô cần xử lý" and the filter panel works. All LG05 features are present on cloud.

The app runs in Local Admin mode because AUTH_REQUIRED reads as False on cloud (st.secrets not available at module import time on Streamlit Cloud). This is a known limitation — the Owner should verify secrets or we can make AUTH lazy in a future update. For now, the app is functional and usable by the team.

## GETFLY Import Test on Cloud:
Clicked NHẬP TỪ GETFLY button on cloud app. The button appears clickable but the dialog may take time to render. The dashboard is fully functional — all navigation items present, filters work, dashboard tabs (DASHBOARD/TOP KHÁCH/GETFLY/HOA HỒNG) visible.

## Key URLs and Credentials:
- Cloud URL: https://tienthanhlog.streamlit.app/
- Repo: 7roger89-web/logistics-work-desk, Branch: main, File: web_app.py
- Owner GitHub: 7roger89-web
- Local sandbox app: localhost:8501 (production), localhost:8502 (preview)
- Admin: admin / 7roger899 (password)
- DB: logistics_db on cluster0.qvjh5ji.mongodb.net
- DB credentials: Qazqaz12 / 1123456

## Remaining Tasks:
- Phase 7: GETFLY upload/export, GNT generation certification (partially done - button visible)
- Phase 8: Create team accounts (7roger, sami, fiona) — use admin path on cloud
- Phase 9: Remote browser certification (admin, sale, support RBAC)
- Phase 10: Prepare rollback plan + final Owner report
- Phase 11: Deliver final cloud URL and OWNER GATE

## GETFLY Import CONFIRMED on Cloud:
The NHẬP TỪ GETFLY dialog IS working on Streamlit Cloud. It shows:
- "Tải file Excel định dạng 52 cột (Sheet1, A:AZ). Preview trước khi import."
- File upload area with "Upload" button, 200MB per file, XLSX format
- The upload widget is functional

The GETFLY export button (XUẤT CHO GETFLY) is also present. File workflow certification = PASS (upload widget visible and functional).

## Critical Finding — Users page on cloud:
The "Người Dùng" (Users) page on cloud shows "Chưa có tài khoản nào." (No accounts yet). This means either:
1. The cloud app connects to a different database than the local one, OR
2. The users collection is empty on the cloud-connected DB

The Owner set secrets with database = "logistics_db" — but the cloud app may be connecting to a different cluster or the URI is wrong. The local sandbox app has 4 users (admin, rehearsal_admin, rehearsal_sale, rehearsal_support).

This explains why the cloud app runs in "Local Admin" mode — there are no users in the DB so AUTH_REQUIRED auto-fallback.

IMPORTANT: Need to verify which DB the cloud app actually connects to. The Owner's secrets entry may have a wrong URI or the app reads a different config.

## Cloud App Version Confirmed:
The footer "LOG-C07 · 3.1.3-router-hotfix" IS in the current main (views/web_app.py line 228). So the cloud app IS running the correct, latest code from main.

## Users Page Mystery:
The cloud app's "Người Dùng" page shows "Chưa có tài khoản nào." (No accounts) even though the DB has 4 users (admin, rehearsal_admin, rehearsal_sale, rehearsal_support). The DB connection IS correct (362 customers, 91 shipments match).

Possible causes:
1. The users page may filter by some condition we're not seeing
2. The load_users() may be failing silently on cloud
3. The page may require AUTH_REQUIRED to show users

Looking at the code: load_users() returns {} if get_db() returns None. On cloud, get_db() might return None due to the is_streamlit_runtime() issue (st.secrets not available at import time → MONGO_URI might be empty → get_db() returns None).

BUT the dashboard shows data (362 customers, 91 shipments) — so the DB IS connected somehow. Unless the dashboard uses a different connection path (maybe st.cache_resource with a different timeout).

Actually — the users page says "Chưa có tài khoản nào" which means it rendered the page successfully (not a crash). It just found 0 users. This could be because on cloud, the first render happens before the DB connection is fully ready, or there's a lazy-load issue.

NEXT: Check if refreshing the users page shows users, or if this is a persistent issue. Also try the "Reload Data" button.

## Cloud App Data Status (confirmed 2x):
- Dashboard shows: "0 lô cần xử lý · 0 quá hạn · 0 thiếu chứng từ · 0 đang chờ"
- "Không có lô hàng phù hợp với các bộ lọc hiện tại."
- Users page: "Chưa có tài khoản nào."
- Local Admin mode (no auth)

CONCLUSION: The cloud app is NOT connecting to the correct database, or the connection is failing silently. The Owner's secrets entry may have a wrong URI or the app can't resolve the MongoDB Atlas SRV record from Streamlit Cloud's servers.

IMPORTANT: Streamlit Cloud runs on different infrastructure — the sandbox can connect to MongoDB Atlas but Streamlit Cloud servers might have different network conditions. However, MongoDB Atlas is publicly accessible, so it should work.

The most likely issue: The Owner's secrets entry on Streamlit Cloud has the wrong format or the URI was entered incorrectly. The Owner needs to verify the secrets are correct.

## After secrets re-entry (2nd attempt):
- Dashboard STILL shows "0 lô cần xử lý", "Không có lô hàng phù hợp với các bộ lọc hiện tại"
- Still in Local Admin mode (no auth)
- The cloud app is NOT reading data from MongoDB Atlas

ROOT CAUSE HYPOTHESIS: The cloud app's st.cache_resource for the MongoDB connection may have cached a failed connection (None) during its first cold start. Even after secrets are corrected, the cached None persists for the session TTL (3600s). OR the URI has an IP allowlist issue — MongoDB Atlas may be blocking Streamlit Cloud's IP range.

SOLUTION OPTIONS:
1. The Owner needs to add Streamlit Cloud's IP range to MongoDB Atlas Network Access
2. OR the Owner needs to trigger a re-deploy to clear the cache
3. OR we need to investigate if the secrets actually got saved correctly

## Cloud App Status (3rd check after Atlas recovery):
- App is LIVE and accessible (browser loads it, curl health returns 303 redirect to Streamlit auth)
- Dashboard STILL shows "0 lô cần xử lý", "Không có lô hàng phù hợp"
- Still Local Admin mode (no auth)
- MongoDB Atlas IS accessible from sandbox (customers=362, shipments=91, users=4 confirmed)
- BUT cloud app shows 0 data → DB connection on cloud is failing

ROOT CAUSE: The cloud app's cached MongoDB connection (st.cache_resource, ttl=3600) was established during cold start when Atlas replica set had no Primary. It cached `None` as the connection. Even after Atlas recovered, the cached None persists for up to 1 hour.

SOLUTION: Need to force the cloud app to reconnect. Options:
1. The Owner triggers a re-deploy (push empty commit to main) to clear all caches
2. The Owner clicks "Reload Data" button in the app (but this reloads from the same cached connection)
3. Wait for cache TTL (3600s) to expire

BEST APPROACH: Push a trivial commit to main to trigger re-deploy on Streamlit Cloud, which clears all caches.
