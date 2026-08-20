# LOG-LG07 — State File

## Phase 1-3 COMPLETE:
- Git HEAD: f432077 (main) — includes LG07 requirements.txt fix
- requirements.txt updated with: python-calamine, pydantic, pyTelegramBotAPI added
- Cloud audit PASS: no Windows paths, no localhost, no subprocess, no hardcoded ports
- Secrets: .streamlit/secrets.toml is gitignored (not committed)
- Entrypoint: web_app.py
- DB: logistics_db on Atlas, PROD_INTERNAL

## Phase 4 IN PROGRESS:
- Attempting Streamlit Cloud deployment via share.streamlit.io
- Need GitHub OAuth login on Streamlit Cloud
- Owner's GitHub account: 7roger89-web

## TODO:
- Deploy via Streamlit Cloud web UI (may need Owner to login via GitHub)
- Set secrets on cloud dashboard
- Test via HTTPS URL

## Key data for Owner report:
- LOCAL PIDs: 8501=74938, 8502=74937
- DB: customers=362, shipments=91, users=4 (1 active admin + 3 inactive rehearsal)
- Team accounts to create: 7roger (SALE), sami (SUPPORT), fiona (SUPPORT)

## Streamlit Cloud Deployment Notes (2026-08-20):
- Owner logged into Streamlit Cloud (GitHub: 7roger89-web) on the browser
- The deploy page at share.streamlit.io/deploy renders a SPA that is slow
- The login page shows "Continue with GitHub" option
- Owner said "Tôi đã đăng nhập vào rồi" — GitHub OAuth should be active
- The page keeps showing blank/white — likely a rendering issue with the SPA
- Streamlit Community Cloud URL format: https://{app-name}.streamlit.app
- Deployment steps: 1) Sign in 2) Pick repo/branch/file 3) Deploy
- Repo: 7roger89-web/logistics-work-desk, Branch: main, File: web_app.py
- Need to set secrets: [mongo] uri + database, [env] identity, [auth] required, [gemini] api_key
