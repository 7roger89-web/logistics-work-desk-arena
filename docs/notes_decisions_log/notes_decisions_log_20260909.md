# Notes and Decisions Log — 2026-09-09

## LOGISTICS-HYBRID-DESIGN-DONOR-WITH-LEGACY-WORKFLOW-LOCKS-001

- Donor repo `7roger89-web/logistics-demo` was unreachable from the Arena sandbox (404). Decision: implement the donor
  look from the task's explicit token/typography/layout spec instead of transplanting React files; nothing from the
  donor (code or mock data) was copied.
- Architecture decision: donor parity is delivered through (a) `.streamlit/config.toml` theme, (b) `GLOBAL_CSS` in
  `views/web_app.py`, (c) shared helpers in new `views/ui_kit.py` (pure presentation, no session_state / business
  logic), (d) per-view presentation edits. Shipment views (`views/shipment.py`, `views/shipment_360.py`, entrustment,
  proxy payment, historical review, legacy sales) and `core/*` have zero diff.
- Top header and phone bottom nav are Streamlit keyed containers positioned with CSS (`position: fixed`); their
  empty in-flow wrappers are collapsed with `:has()` rules. Tablet drawer reuses Streamlit's native sidebar toggle.
- Dashboard "Hôm nay tôi cần làm gì?" sections use only `core.shipment_dashboard` projections (real data). Legacy
  filter/task/GetFly/tab structure and widget keys were kept so existing AppTests still drive the page.
- Level B rule applied: business function/data/state → current app wins; presentation → donor wins. Finance tables
  render via `ui_kit.data_table` (HTML table on desktop, label/value cards on phones); partner debt shows one row per
  currency and never sums across currencies; quotation surfaces are labelled BÁO GIÁ / DỰ KIẾN.
- `views/quotations.py` keeps CRLF line endings (patched via bytes round-trip).
- Regression gate: full pytest FAILED/ERROR id set identical to the pre-change baseline (13 environmental ids);
  focused RBAC / docgen / finance write-oracle / smoke suites green.
- Preview: read-only mongomock launcher outside the repo; no Production connection or mutation.

Related coder report: `reports/coder/rp_coder_260909_by_arena-agent_logistics-hybrid-design-donor-001.md`.
