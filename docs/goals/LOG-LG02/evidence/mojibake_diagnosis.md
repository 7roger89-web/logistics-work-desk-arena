# Mojibake diagnosis — LOG-LG02 cutover

## Fact pattern (2026-08-18)
- User's PC (D:\Logistics_App_GitHub, via My Browser screenshots) shows mojibake:
  "Äang cháº¡y Local Admin... Táº¡o LÃ´ Má»›i KhÃ¡ch HÃ ng Thá»a Thuáº­n Sá»• Tay Kinh Nghiá»‡m"
- Sandbox localhost:8501 now serves CORRECT Vietnamese (verified by curl + browser:
  "Đang chạy Local Admin... ➕ Tạo Lô Mới 👥 Khách Hàng 🤝 Thỏa Thuận & Bàn Giao
  📔 Sổ Tay Kinh Nghiệm") — after restoring backup + fix_mojibake.py +
  clearing __pycache__ + restart (the first restart was serving stale cached bytecode).

## Root cause hypothesis for user's PC
The views/web_app.py currently IN THE USER'S LOCAL REPO (D:\Logistics_App_GitHub)
is still the corrupted mojibake file. Fix_mojibake.py is pushed to GitHub branch
log-lg01-multi-user-internal-rc. The user must:
  1. git pull origin log-lg01-multi-user-internal-rc
  2. Replace his local views/web_app.py with the fixed file:
     git checkout views/web_app.py   (or let pull overwrite; he may have local edits)
  3. Delete __pycache__ under views/ (Windows: rd /s /q views\__pycache__)
  4. Restart: streamlit run web_app.py
His local repo has NO committed secrets, so git pull will not clobber anything
except his possibly-edited views/web_app.py — that file must be REVERTED to repo
version anyway (it's the mojibake source).

## Important: My Browser screenshot confusion
My Browser navigates http://localhost:8501 on the USER'S MACHINE (not sandbox).
So the mojibake screenshots were the user's PC app. Sandbox 8501 is only reachable
from inside sandbox. => The user's own `streamlit run` was serving the mojibake
file he has locally. Fixing is a git pull + restart on HIS PC.

## Sandbox verification result
Sandbox app: bootstrap form does NOT appear — it shows "Local Admin · admin"
because .streamlit/secrets.toml on sandbox has [auth].required=true but the
session cache/st.session_state keeps old bootstrap; and the running app loaded
secrets before restart. Verified secrets.toml has required=true, production DB
has users=0, customers=362, shipments=78, release_mode=true. Need hard restart
AND clear st cache; then verify bootstrap form appears (user_count==0 &&
AUTH_REQUIRED).

## Fix script status
docs/goals/LOG-LG02/tools/fix_mojibake.py — works idempotently (artifact-char
guard). Backup of pre-fix file: /tmp/web_app_before_fix.py.
views/web_app.py in repo: COMPILE_OK, all key Vietnamese strings verified present.
