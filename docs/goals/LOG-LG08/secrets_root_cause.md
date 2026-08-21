# Root cause — new app still Local Admin after Owner "xong" (2026-08-21 04:00)

## Facts
- App https://logisticspro-1.streamlit.app/ renders the full dashboard but in **Local Admin** mode: sidebar shows "Local Admin · admin" + "Đang chạy Local Admin. Bật AUTH_REQUIRED khi triển khai nhiều người dùng.", dashboard shows 0 shipments ("Không có lô hàng phù hợp với các bộ lọc hiện tại").
- Code path (core/auth.py require_login): if `AUTH_REQUIRED` is False → Local Admin user injected, no DB read. AUTH_REQUIRED comes from core/config.py get_setting("AUTH_REQUIRED", ("auth","required"), "AUTH_REQUIRED", default="false") — requires EXACT string true/1/yes/on.
- If mongo URI were wrong, `validate_mongo_identity()` would raise RuntimeError and the app would NOT render dashboard at all (it does render) — so the dashboard renders with NO DATA: meaning the dashboard probably catches the DB error and shows empty. But the Local Admin injection happens BEFORE any DB read, consistent with secrets missing/wrong for [auth].required.
- The app process restarts when secrets are saved on Streamlit Cloud; secrets editor content might have been saved but maybe the owner saved in the wrong place (e.g. old app), or content got altered (e.g. missing [auth] section, or TOML quote issue). Owner is non-technical; the most likely case is the secrets were pasted into the OLD app's settings, or the new app's "Edit secrets" wasn't actually saved for logisticspro-1.
- IMPORTANT: secrets.toml in repo is gitignored. Cloud secrets are only in the app settings.

## What must happen for verification
1. Secrets on logisticspro-1 must include `[auth] required = true` (exact) and full [mongo] block.
2. After saving, app redeploys; verify: login screen appears OR user badge shows real name, dashboard shows 91 shipments.

## Next action
Ask owner to re-check secrets on the NEW app specifically (logisticspro-1, not tienthanhlog), and paste again if needed. Offer to verify via screenshot from their browser: they should see đăng nhập screen when visiting the app in incognito.

## ✅ VERIFIED 2026-08-21 ~04:08 (sandbox browser)
- Login screen appeared (no Local Admin banner)
- Login admin / 7roger899 → SUCCESS → sidebar shows "Owner · admin", "Đăng xuất" present
- Dashboard: "13 lô cần xử lý", Bảng việc chính có dữ liệu (CÔNG TY CỔ PHẦN B&G GREEN...), Lịch sử đã xong (5)
- Footer: LOG-C07 · 3.1.3-router-hotfix → this is production branch build (b6fde2b)
- CONCLUSION: logisticspro-1.streamlit.app = LIVE PRODUCTION from branch production, secrets correct, DB connected.
