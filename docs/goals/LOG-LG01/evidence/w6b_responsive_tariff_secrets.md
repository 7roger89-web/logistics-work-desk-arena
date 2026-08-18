# LG01-T09: W6b Responsive / Tariff Boundary / Secret Scan

Branch: `log-lg01-multi-user-internal-rc`. Date: 2026-08-17. Baseline since commit `05fa777`.

## 1. Responsive / Accessibility bounded evidence

Evidence collected by code inspection (bounded — not full WCAG certification).

| Surface | Evidence |
|---|---|
| Dashboard | `views/dashboard.py` line 429 `@media (max-width: 900px)` responsive grid; line 434 `@media (prefers-reduced-motion: reduce)` |
| Shipment 360 | `views/shipment_360.py` lines 56-57 `@media (max-width: 900px)` title/signal sizing + reduced-motion |
| Review Queue | `views/review_queue.py` lines 130-131 `@media (max-width: 900px)` title sizing + reduced-motion |
| App shell | `views/web_app.py` line 155 `@media (prefers-reduced-motion: reduce)` |
| All views | `grid-template-columns: repeat(5, minmax(0, 1fr))` fluid grid — no fixed-px horizontal breakage pattern |

Findings: no material horizontal breakage patterns detected; text labels are descriptive Vietnamese strings (status chips carry text, not color-only); status states use UNKNOWN/WAITING text tokens. Keyboard/focus smoke: Streamlit default focus handling; not exhaustively certified.

Desktop + narrow (<900px) behavior covered via CSS media queries on the 4 key surfaces (Dashboard, Shipment 360, Review Queue, Login/Admin shell). Finance Review and Quotation/Agreement surfaces render within the same fluid grid shell.

## 2. Tariff boundary

`tariff.db` is NOT tracked in Git (`git ls-files` — zero matches). `views/tariff.py` (23.4 KB) uses local CSV/Excel import flow (`load_cbpg_data`, `check_cbpg_tax`, `ui_super_tariff_hub`) and guards every computation with `df.empty` checks. Empty-state message present: "Chưa có dòng hàng. Hãy thêm dòng trong bảng phía trên."

Verification with TEST DB `logistics_workdesk_LG01_E2E` (clean, no rate-card data): `load_rate_cards()` returns `{}` (empty) — no crash; imports clean. No real tariff dataset was populated in this Goal. Tariff results cannot be fabricated: missing reference data produces empty input table, not computed values.

## 3. Secret / security scan

Scan scope: 233 tracked files (patterns: `mongodb+srv://...`, `AKIA...`, `sk-...`, `ghp_...`, `PRIVATE KEY`). Result: 1 hit, false positive — `docs/LOG_C15_HANDOFF.md` contains the markdown prose text `` `mongodb+srv://` `` inside backticks (configuration convention description, no credential). No real credential in tracked material.

Large Goal changes since baseline (`git diff --name-only 05fa777..HEAD`, 13 files): ZERO credential hits. `.env.example` and `.streamlit/secrets.toml.example` are clean placeholders (`api_key = "YOUR_VALUE_HERE"`).

`.gitignore` explicitly excludes: `.env`, `.env.*` (except example), `.streamlit/secrets*.toml` (except example), `google_key.json`, `*.pem`, `*.key`. All secrets used for E2E testing live only at `D:\lg01_e2e\secrets.toml` — untracked, never committed.

Verdict: secret scan PASSES. No STOP condition triggered.

## 4. Build verification

`py_compile` (doraise) over all 23 views + 37 core modules: 60/60 compiled, 0 errors.
