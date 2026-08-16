# Notes & Decisions Log — 2026-08-16

## LOG-C10 Documents & Review Queue

- Implemented a deterministic, read-only review-item projection and a dedicated Review Queue route.
- Queue fields are limited to severity, category, work item, shipment, context, next action, and evidence/source; item detail is separate.
- Document signals preserve `UNKNOWN`; no document completeness is inferred and no Resolve writer exists.
- Queue navigation uses existing Shipment 360 and Entity Context destinations with bounded return-to-queue session context.
- First visible render was critiqued: the expanded filter panel pushed the table below the fold. Corrected to a compact popover and rerendered successfully.
- Evidence: `reports/QA/playwright/2026-08-16-log-c10-documents-review-queue.json` and four screenshots in the same directory.
- Validation: 6 focused queue tests, 19 focused cross-surface tests, 150 full tests with 2 skips, compileall PASS.
- Anvien final change detection reports broad critical aggregate risk because the shared worktree was already dirty. No unrelated files were staged or committed.
- Closure reports: `reports/coder/rp_coder_260816_163118_by_gpt-5-codex_log-c10-documents-review-queue.md` and `reports/supervisor/rp_supervisor_260816_163118_by_gpt-5-codex_log-c10-documents-review-queue.md`.
- Release state: local PASS, `NOT_RELEASED`; Docker/pytest limitations remain explicit.
