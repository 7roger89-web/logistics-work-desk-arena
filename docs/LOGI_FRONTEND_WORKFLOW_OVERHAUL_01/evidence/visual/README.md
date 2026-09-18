# PROXY_ONLY · NOT_RUNTIME_ACCEPTANCE

Static debug/inspection pages: each mounts the **real production bundle**
(`component/dist/logi-shell.js|css`) with a **backend-generated fixture**
(isolated mongomock staging) and pre-drives one scenario.

They exist so a reviewer can inspect the changed UX quickly without booting
Streamlit. They are **not** real-browser runtime verification, not screenshots,
and must not be counted toward `DESKTOP_RUNTIME_VERIFIED` /
`MOBILE_RUNTIME_VERIFIED` / `REAL_BROWSER_VERIFIED`.

Authoritative real-browser lane (when a browser is available):
`playwright/acceptance_phase_a.py` per the repo's own protocol.

| File | Scenario |
|---|---|
| 01/02 | Home desktop / mobile composition |
| 03 | Shipments list with route-backed filter context |
| 04 | Shipment Detail finance workspace (collapsed `Sửa thông tin lô`) |
| 05/06/07 | Payment sheet PENDING / REFUSED / correlated SUCCESS |
| 08 | Receivables search+filters in the route |
| 09/10 | Role preview (sandbox) vs actual-role-only (production-like) |
