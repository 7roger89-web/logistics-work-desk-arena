# V4 — Logi-good donor view layer (working note)

Run the donor UI (persistent left sidebar, top header, mobile drawer + bottom nav):

    streamlit run views/lg_app.py

## What this adds
- `views/lg_app.py` — donor entry point + router.
- `views/lg/` — donor view package:
  - `theme.py`      — donor CSS tokens / palette (navigate #0f2a4a, cards, badges, KPI).
  - `helpers.py`    — session/role/formatting helpers (RBAC via core.auth; UNKNOWN-safe).
  - `widgets.py`    — HTML/Streamlit building blocks (badges, KPIs, next-action banners, tables).
  - `shell.py`      — persistent left sidebar nav (native Streamlit, >=720), real hamburger
                      toggling `st.session_state["lg_mobile_nav_open"]` drawer, bottom quick-nav.
  - `svc.py`        — repository over real core readers + DEV mongomock stand-in.
  - `seed.py`       — DEV-only demo seed (clearly labelled, never PRODUCTION).
  - `pages.py`      — Home / Tasks / Shipments / New Shipment / Tracking / Shipment Detail (5 tabs).
  - `pages_misc.py` — Customers / Context / Quote / Agreements / Contracts / Finance / CEO / Tools / Admin.
- `tests/test_lg_v4_donor_shell.py` — AppTest smoke over all routes + detail tabs.

## Data
- Real deployment: reads through the existing `core.*` readers/services; writes via real writers.
- No live Mongo in sandbox: a DEV-only in-memory stand-in (mongomock) is seeded once so the
  donor UI renders. Clearly surfaced with a "dữ liệu mẫu (DEV)" banner; never touches a real DB.
- UNKNOWN is preserved (never coerced to 0).
