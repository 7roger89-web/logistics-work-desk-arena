# Probe notes — 2026-08-21 (new app logisticspro-1)

- `curl https://logisticspro-1.streamlit.app/` => 303 redirect to `share.streamlit.io/-/auth/app?redirect_uri=...` — this is normal Streamlit Community Cloud auth gate (the app requires GitHub login or viewer access). Same 303 for old app tienthanhlog.
- Sandbox browser on `share.streamlit.io/app/logisticspro-1/` initially blank/loading, then resolved to: **"You do not have access to this app or it does not exist — Please sign in to continue."**
- Old app `share.streamlit.io/app/tienthanhlog/` also blank/loading in sandbox (screenshot failed, status page embedded iframe only).
- `_stcore/health` and `_stcore/stream` both return 303 (auth gate) — the app process itself may be up but viewer access is gated.
- Interpretation: the new app at logisticspro-1.streamlit.app is likely set to **Private** viewer access (default for newly deployed Streamlit Cloud apps from a private repo), hence sandbox (not logged in to GitHub) gets "no access". The old app may be Public.
- Owner said "xong" meaning secrets configured. App not yet verified by me due to auth gate.
- Next: ask Owner to set Viewer access to **Anyone with the link** (Public) on logisticspro-1 app settings, or verify via Owner's own browser. Alternatively I verify through Owner's My Browser is not relevant here — simpler to ask Owner to switch viewer access to public (the app has its own login anyway).
