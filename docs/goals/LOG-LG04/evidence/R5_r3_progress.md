# LOG-LG04 R3 — Progress Notes

## BASELINE FACTS (recovered)
- PR #3 HEAD: a7361fd (open)
- Branch: log-lg04-daily-work-simplification
- Production (machine Owner, port 8501): LG03 SHA 3c1e1c7 — untouched
- Main branch: aa5cef4 (LG03 terminal)
- Production DB: customers=362, shipments=78, users=4, quotes=1, agreements=1, financial_ledger=0

## PERFORMANCE PROFILING RESULTS (BEFORE optimization)

### Individual components:
- Import core.database: **3.758s** (module import overhead)
- Connect to MongoDB Atlas: **6.501s** (DNS + TLS handshake to cluster0.qvjh5ji.mongodb.net)
- count_documents(shipments): 0.557s
- find all shipments (78 docs): 1.145s
- find all customers (362 docs): 1.497s

### Full dashboard render (AppTest):
- **28.941s** total
- MongoDB calls: find=6, count=0, aggregate=0
- Total DB query time: ~0ms (the timer captured 0ms because patching at pymongo level doesn't intercept — the calls likely go through different path or the timer overhead is wrong)

### Root cause analysis:
1. **MongoDB Atlas connection latency (~6.5s per connect)** — this is network latency to Atlas M0 free tier server
2. **Module import overhead (~3.7s)** — loading pymongo + app modules
3. **6 find() calls per dashboard render** — if each find takes ~1-2s network latency, that's 6-12s
4. **Streamlit re-runs entire script on every interaction** — so nav changes re-execute everything

### Key insight:
The dominant lag is NOT code inefficiency — it's **Atlas M0 free-tier network latency** (~1-2s per query + 6.5s initial connect). Code optimizations can reduce the NUMBER of queries but cannot reduce Atlas latency.

## R3 WORK PLAN (from Owner instructions in pasted_content_5.txt)

### 1. Performance optimization (Phase 2)
- Use `@st.cache_resource` for MongoDB connection (avoid re-connecting)
- Use `@st.cache_data(ttl=30)` for read-only data (shipments, customers lists)
- Invalidate cache after writes (dashboard save_shipment_atomic etc.)
- Reduce number of queries (consolidate where possible)

### 2. Primary action change (Phase 3) — HIGHEST VALUE
- Change "MỞ HỒ SƠ LÔ 360°" → "XỬ LÝ LÔ" (primary button)
- Opens directly into editable work surface (ui_shipment_detail_tabs or embedded forms)
- Keep 360° as secondary "Xem hồ sơ tổng quan" button

### 3. Dashboard restructure (Phase 4)
- Replace big "Lô hàng cần xử lý" block with compact summary:
  🔴 X lô cần xử lý · Y quá hạn · Z thiếu chứng từ · N đang chờ
- Move queue-specific filters to "Việc cần xử lý" page
- Keep only time period + search on Dashboard

### 4. Remove "Ngữ cảnh đối tác" (Phase 5)
- Replace with "Khách hàng · Nhà máy · Đại lý" with guidance text
- Add "Liên hệ nhanh" compact section

### 5. Support finance authority (Phase 6 - already done in R2)
- support has finance_write permission
- Need to verify with test users

### 6. Two Support accounts (Phase 7 - OWNER GATE)
- Owner approved creating 2 Support accounts
- BUT: need actual names/usernames from Owner
- Cannot invent identities → STOP at this gate and ask Owner

### 7. Return-to-list state (Phase 6)
- Preserve time filter, search, page state when returning from shipment

## NEXT STEPS (in order):
1. Phase 2: Performance optimization (st.cache_resource for conn, st.cache_data for reads)
2. Phase 3: Primary action change ("XỬ LÝ LÔ" opens editable surface directly)
3. Phase 4: Dashboard compact summary + move queue filters
4. Phase 5: Remove "Ngữ cảnh đối tác"
5. Phase 6: Full regression + Role QA + browser QA
6. Phase 7: Update PR #3, write report, ask Owner for 2 Support account names

## KEY FILES TO MODIFY:
- core/database.py — add st.cache_resource for connection
- core/config.py — add caching where needed
- views/dashboard.py — compact summary, move filters, return-to-list
- views/shipment_360.py — primary action change
- views/shipment.py — editable surface improvements
- views/web_app.py — possibly lazy-load views

## PERFORMANCE OPTIMIZATION RESULTS (Phase 2)

**BEFORE optimization:**
- Cold start (first render): 28.941s
- Every subsequent rerun: ~27s (no caching at all)

**AFTER optimization (st.cache_resource + st.cache_data):**
- Cold start (first render): 27.644s (still slow due to Atlas M0 connection — unavoidable)
- Warm run (second render): **0.535s** — 54x faster!
- Warm run 2: similarly fast

**Analysis:**
1. The initial ~27s cold start is dominated by MongoDB Atlas M0 free-tier network latency (DNS + TLS handshake ≈ 6.5s, then 6 queries × 1-3s each). This CANNOT be eliminated by code changes — it's a property of the Atlas M0 free tier.
2. After the first render, `st.cache_resource` keeps the MongoDB connection alive and `st.cache_data` caches all read results for 30 seconds. Subsequent reruns (navigation, clicks) now take **under 1 second** instead of 27 seconds.
3. Cache is invalidated after every write (save_shipment_atomic, save_customer_to_cloud) to ensure data freshness.

**Owner-perceived improvement:**
- Opening app for first time: ~27s (same — Atlas limitation)
- Every subsequent action (click, navigate, open shipment): **< 1 second** (was 27s)
- This is the dominant perceived lag fix — Owner will no longer feel lag when using the app.

**Remaining recommendations (not blocking):**
- Upgrade from Atlas M0 (free) to M2/M5 for faster cold start
- Or deploy app closer to Atlas region (currently Vietnam → US East)

## KEY ARCHITECTURE INSIGHT (Phase 3 — Primary Action Change)

When dashboard button `dashboard_open_360_{sid}` is clicked:
1. Sets `st.session_state.active_shipment_id = sid` and `dashboard_active_shipment_id = sid`
2. `st.rerun()` re-renders the dashboard
3. In `ui_dashboard()` (dashboard.py line 612+), if `active_sid` is set and in `all_ships`:
   - If `can_edit`: calls `ui_shipment_detail_tabs(active_sid, ship_data)` — THIS IS THE EDITABLE WORK SURFACE
   - If `!can_edit`: shows read-only JSON

**CRITICAL FINDING:** The current code ALREADY opens the editable work surface (`ui_shipment_detail_tabs`) when clicking "MỞ HỒ SƠ LÔ 360°"! The Owner's complaint was that it "lands near the top but doesn't directly show the data-entry form."

The issue is that `ui_shipment_detail_tabs` renders tabs (LẤY HÀNG & XUẤT KHẨU / NHẬP KHẨU & GIAO HÀNG / DỊCH VỤ & DOANH THU / ...) and the user has to scroll or click a tab to find the form. The Owner wants the form to be IMMEDIATELY visible without extra navigation.

**R3 SOLUTION (Phase 3):**
1. Rename button from "MỞ HỒ SƠ LÔ 360°" to "XỬ LÝ LÔ" (primary action)
2. Keep 360° as secondary: add a small "Xem hồ sơ tổng quan" button that opens the full 360° workspace
3. When "XỬ LÝ LÔ" is clicked, open directly into editable surface AND scroll/set focus to the first work area
4. The `ui_shipment_detail_tabs` already shows 3 work areas — just need to make the first tab auto-selected and add visual emphasis

**Implementation approach:**
- In dashboard.py: change button label + add secondary 360° button
- In shipment.py: when opened from dashboard (check session_state flag), auto-focus to the first editable tab

## COMPLETE R3 REQUIREMENTS SUMMARY

From pasted_content_5.txt (full requirements):

### 1. PERFORMANCE (done)
- Before: ~27s per rerun
- After: cold ~27s (Atlas limitation), warm <1s (54x faster)
- Cache applied to: init_connection (cache_resource), load_data, load_customers, load_contracts, load_contract_transactions (cache_data, ttl=30s)
- Cache invalidation after writes

### 2. DASHBOARD INFORMATION HIERARCHY
- Replace large "Lô hàng cần xử lý" block with compact summary:
  "🔴 X lô cần xử lý · Y quá hạn · Z thiếu chứng từ · N đang chờ"
- Immediately after: search/time filter, then shipment list
- Do NOT let KPI cards push work down

### 3. MOVE QUEUE FILTERS
- Remove "Lọc & tìm trong queue" from Dashboard
- Queue filtering belongs in "Việc cần xử lý" page only
- Dashboard keeps: time period, quick search

### 4. CURRENT-MONTH DEFAULT (done in R2)
- Already set to "Tháng này" by default
- Carry-over warning for old unresolved shipments

### 5. PRIMARY ACTION CHANGE — "XỬ LÝ LÔ"
- Rename button from "MỞ HỒ SƠ LÔ 360°" to "XỬ LÝ LÔ"
- Opens directly into EDITABLE work surface (not 360° read-only)
- First viewport must contain actual work/input interface
- Keep 360° as SECONDARY "Xem hồ sơ tổng quan" button
- Support user should NOT need another navigation step to reach input

### 6. DIRECT DAILY-WORK SURFACE
- Show 3 work areas directly: A. LẤY HÀNG & XUẤT KHẨU, B. NHẬP KHẨU & GIAO HÀNG, C. CHI PHÍ & CÔNG NỢ
- Expose actual editable fields/actions directly (subject to RBAC)
- Avoid: summary → button → another page → tab → form
- Progressive disclosure for advanced details

### 7. SUPPORT FINANCE BUSINESS AUTHORITY (done in R2)
- Support can enter costs, sale price, confirm Finance Actual, record payments
- Already implemented in auth.py

### 8. REMOVE "NGỮ CẢNH ĐỐI TÁC" (partially done in R2)
- Rename to "Khách hàng · Nhà máy · Đại lý"
- Add guidance: "Thông tin liên hệ của các bên trong lô hàng..."
- Keep "Liên hệ nhanh" compact

### 9. TWO SUPPORT ACCOUNTS — OWNER GATE
- Do NOT invent fake identities
- If actual names NOT known: complete all other R3 work, then ask Owner for:
  - Support person 1 display name / username
  - Support person 2 display name / username

### 10. OWNER DAILY ACCOUNT RECOMMENDATION
- Recommend Owner use separate Sale account for daily work
- Reserve Admin for administration
- Do NOT create automatically

### 11. TERMINAL STATE
- READY_FOR_OWNER_LG04_R3_PREVIEW_GATE
- Do NOT merge PR #3, do NOT deploy, do NOT start LG05

## PHASE 3 IMPLEMENTATION — DIRECT WORK SURFACE

Key insight: dashboard.py ALREADY renders ui_shipment_detail_tabs() when active_shipment_id is set. The tabs show: PICKUP & XUẤT KHẨU / IMPORT & GIAO HÀNG / FINANCE.

The jump mechanism: shipment.py line 172 checks `st.session_state.pop("active_shipment_section")` to pick which tab to open by default (export=0, import=1, finance=2).

R3 approach for "XỬ LÝ LÔ" button:
- Set `st.session_state.active_shipment_section = "finance"` when clicking "XỬ LÝ LÔ"
- This makes the FINANCE tab open by default — where the actual daily work happens (entering costs, prices, payments)
- The Owner wants to see the INPUT form immediately, not a summary

The 360° secondary button ("📊 360°") will open the full overview workspace.

## R3 IMPLEMENTATION STATUS (updated)

### DONE:
1. **Performance caching** — st.cache_resource on connection, st.cache_data on load_data/load_customers/load_contracts/load_contract_transactions (ttl=30s), cache invalidation after writes. Before: 27s/rerun. After: warm <1s.
2. **Primary action button** — Changed "MỞ HỒ SƠ LÔ 360°" to "📝 XỬ LÝ LÔ" (primary, blue) + "📊 360°" (secondary, gray) in dashboard.py
3. **Direct work surface** — "XỬ LÝ LÔ" sets active_shipment_section="finance" which opens the FINANCE tab directly in ui_shipment_detail_tabs
4. **360° secondary view** — "📊 360°" renders the full shipment_360 workspace with proper view construction

### TODO (Phase 4 — Dashboard restructure):
- Replace large "Lô hàng cần xử lý" block with compact summary: "🔴 X lô cần xử lý · Y quá hạn · Z thiếu chứng từ · N đang chờ"
- Move queue-specific filters from Dashboard to "Việc cần xử lý" page
- Keep simple controls on Dashboard: time period, quick search
- Current-month default already done (index=0)
- Carry-over warning already implemented in R2

### TODO (Phase 5):
- "Ngữ cảnh đối tác" → already renamed to "Liên hệ nhanh" in R2, verify no remaining occurrences
- Add "Khách hàng · Nhà máy · Đại lý" section header with guidance text

### TODO (Phase 6):
- Full regression
- RBAC tests (Support finance write)
- Mojibake scan on changed files
- Secrets scan

### TODO (Phase 7):
- Update PR #3 (already on branch log-lg04-daily-work-simplification)
- Update state.json to READY_FOR_OWNER_LG04_R3_PREVIEW_GATE
- Write Owner preview checklist report

### TODO (Phase 8):
- Send Owner report with instructions
- Support accounts: need Owner to provide 2 Support staff identities


## R3 COMPLETE — 2026-08-19
- All 231 tests PASS (0 fail, 28 skip)
- Files modified: views/dashboard.py, views/shipment_360.py, core/auth.py, core/next_action_card.py, core/database.py, tests/test_dashboard_financial_write_oracle.py, tests/test_entity_context_ui.py, tests/test_lg04_daily_work_ui.py, tests/test_logc15_auth_rbac.py
- Remaining: update PR #3, write R3 preview report, send to Owner
