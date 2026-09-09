# Coder Report — LOGISTICS-HYBRID-DESIGN-DONOR-WITH-LEGACY-WORKFLOW-LOCKS-001

Status: PASS for the hybrid UI migration (donor presentation + legacy workflows preserved).

## Git reference

- Repo: `7roger89-web/logistics-work-desk-arena`, PR #1 branch `arena/01a07b55-logistics-work-desk-arena`
- Base HEAD before work: `dd55c5ef107c85d3fe55b903d6f2ecb8c5a3a61a`
- Commits: `ac6d59f` (shell + dashboard), `22fac93` (Level B presentation), plus this report/log commit.
- Donor `7roger89-web/logistics-demo` was not reachable from the sandbox (404); the design was
  implemented from the task's token list and UX descriptions. **No donor file or mock data was copied.**

## Authority map (what changed where)

| Level | Scope | Change |
| --- | --- | --- |
| A — global shell | `.streamlit/config.toml`, `views/web_app.py` (`GLOBAL_CSS`, `_render_sidebar`, `_render_top_header`, `_render_mobile_nav`, `_mobile_more_dialog`, `_render_global_search`), NEW `views/ui_kit.py` | Donor tokens (#061024 … #8695a8, Be Vietnam Pro), 268px navy sidebar with grouped nav + user chip, fixed white top header (kicker + page title + global search + user), phone bottom nav (Tổng quan / Lô hàng / Hợp đồng / Tài chính / Thêm) + "Thêm" dialog, tablet drawer via native sidebar toggle, shared components (page_header, summary_cards, badge, section, callout, stage_indicator, kv_grid, data_table, empty_state, row_head). |
| Dashboard | `views/dashboard.py` | New `_render_today_focus()` ("Hôm nay tôi cần làm gì?", VIỆC TIẾP THEO, VIỆC CẦN XỬ LÝ HÔM NAY, LỐI TẮT, CHỈ SỐ VẬN HÀNH) computed only from `build_shipment_dashboard_view` / `build_dashboard_summary` rows (real data). Existing filters, tasks, GetFly import/export, tabs, `dashboard_process_*` / `dashboard_overview_*` / `btn_close_top` keys and the locked shipment workspace mount are unchanged; old badges now use `ui_kit.badge`. |
| B — Kinh doanh & đối tác | `views/contracts.py`, `views/customers.py`, `views/entity_context.py`, `views/quotations.py` (CRLF preserved), `views/agreements.py` | Contracts: summary cards, search + status/link filters, donor list rows with MỞ HỢP ĐỒNG, detail badges + "Bổ sung thông tin" callout, section headers inside the five existing tabs (all forms/keys/writers unchanged). Customers: read-only detail card with THÔNG TIN CHÍNH / LIÊN HỆ / LÔ HÀNG / BÁO GIÁ / HỢP ĐỒNG / CÔNG NỢ / GHI CHÚ built from session data; data_editor + save + archive unchanged. Entity context: summary card + grouped sections, all expanders/keys kept. Quotations: BÁO GIÁ / DỰ KIẾN labelling, status cards, stage indicator in detail. Agreements: stage indicator BÁO GIÁ → KHÁCH CHỐT → THỎA THUẬN → BÀN GIAO SUPPORT driven by the selected agreement's real status/readiness; journey text and 3 tabs unchanged. |
| B — Tài chính & đối soát | `views/finance.py`, `views/finance_review.py`, `views/review_queue.py`, `views/partner_reconciliation.py`, `views/reports.py` | Finance: cards (Tổng phải thu / Đã thu / Còn nợ / Lô còn nợ), responsive HTML table with status badges (cards on phones), primary "Xác nhận ghi khoản thu" kept with FIFO plan + idempotency key; partner projection moved into an expander. Finance review: status cards mapped to CHƯA ĐỐI SOÁT / ĐÃ KHỚP / CÓ CHÊNH LỆCH / CẦN XỬ LÝ + sections. Partner debt: partner card, per-currency rows table (never summed), XEM NGỮ CẢNH ĐỐI TÁC button, legacy metrics kept below. Reports: cards + sections (no new charts). |
| B — Công cụ | `views/tariff.py`, `views/knowledge_base.py`, `views/tracking.py`, `views/translation.py` | Headers/kickers, KB summary cards (form + search list unchanged — not a blog). |
| C — Shipment | `views/shipment.py`, `views/shipment_360.py`, `views/entrustment.py`, `views/proxy_payment.py`, `views/historical_review.py`, `views/sales.py`, `core/*` | **Zero diff.** Only inherited global styling. |

## Verification evidence

- Full suite: `python -m pytest tests -q` → `7 failed, 445 passed, 38 skipped, 6 errors` — the FAILED/ERROR id set is
  **identical to the pre-change baseline** (environmental: missing xlsx fixture, Mongo/env identity tests, and two
  pre-existing AppTest failures). No new failure.
- Focused: RBAC (`test_logc15_auth_rbac`, `test_log_rbac_support_01`, `test_deepl_route_rbac`,
  `test_log_rbac_support_finance_service`), docgen (`test_log_docgen_01`), finance write-oracles
  (`test_partner_reconciliation_desk_write_oracle`, `test_reconciliation_desk`), daily-work UI (`test_lg04_daily_work_ui`),
  smoke (`test_all_tabs_smoke`), entity context → all green except the baseline failure.
- Headless Chromium screenshots at 1440 / 1024 / 768 / 390 for Dashboard, Hợp Đồng, Thu Tiền & Công Nợ, Khách Hàng,
  Thỏa Thuận, Công Nợ A Bò, mobile "Thêm" drawer, and the opened Shipment workspace (desktop + phone): sidebar 268px on
  desktop, drawer on tablet (expand button verified clickable), bottom nav on phone, one-column forms, no horizontal scroll.
- Arena Preview: Streamlit on `0.0.0.0:8501` via an offline mongomock-seeded launcher (`/tmp/preview_launcher.py`, not
  committed) — sandbox data only, read-only visual QA; `?page=<route label>` deep links.

## Constraints honoured

- No production DB / canonical repo / production branch touched; no new PR; work pushed only to PR #1's branch.
- No donor mock business data; no shipment redesign; no quotation/finance/agreement business-rule change.
- Route labels, widget keys and test-asserted strings preserved (`build_shipment_summary(ship)` call kept).
