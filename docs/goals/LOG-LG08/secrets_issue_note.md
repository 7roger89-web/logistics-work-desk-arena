# 2026-08-21 — New app loads but secrets NOT applied correctly

## Observation
App https://logisticspro-1.streamlit.app/ loads. BUT sidebar shows:
- "Local Admin · admin"
- "Đang chạy Local Admin. Bật AUTH_REQUIRED khi triển khai nhiều người dùng."
- Dashboard shows "0 lô cần xử lý", "Không có lô hàng phù hợp" → NO DB DATA.

=> The new app is running in **Local Admin / no-auth mode** because:
1. secrets.toml on the new app is missing/wrong, so `auth.required` not true → Local Admin
2. or the [mongo] section missing/wrong → no DB → 0 shipments

## Expected secrets.toml (what Owner must paste into Settings > Secrets):
```toml
[mongo]
uri = "mongodb+srv://Qazqaz12:1123456@cluster0.qvjh5ji.mongodb.net/?appName=Cluster0"
database = "logistics_db"
allowed_databases = ["logistics_db", "logistics_workdesk_logc14", "logistics_workdesk_LG01_E2E"]
release_mode = true

[env]
identity = "PROD_INTERNAL"

[auth]
required = true

[gemini]
api_key = ""

[telegram]
token = ""
chat_id = ""
```

## Correct verification criteria (after secrets fixed):
- Sidebar shows logged-in user (NOT "Local Admin")
- Dashboard shows shipments (91 total, lô cần xử lý > 0)
- Login screen appears when not authenticated

## Git state (unchanged):
- main = 5420058, production = b6fde2b
