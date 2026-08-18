# Post-Cutover Production Probe (read-only via Atlas UI, Owner's browser)

Date: 2026-08-18 (UTC)

## Findings

| Item | Value |
|---|---|
| logistics_db size | 827.39 kB storage / 1.23 MB data — unchanged from R1 (no illicit mutation) |
| Collections | 20 / 52 indexes — identical to R1 inventory |
| Collection list (expanded tree) | audit_logs, contract_transactions, contracts, customers, entrustments, financial_action_requests, financial_allocations, financial_corrections, financial_obligations, financial_transactions, knowledge_base, legacy_historical_review_actions, legacy_historical_staging, notification_outbox, payment_receipts, proxy_payments, quick_notes, rate_cards, shipments, tasks |
| **users collection** | **NOT PRESENT in logistics_db** |

## Interpretation

The `users` collection is absent in production, which means `require_login()` should
see `user_count == 0` and render the bootstrap form — PROVIDED the app's config is
actually pointed at `logistics_db` and `AUTH_REQUIRED = true`.

The owner's screenshot showed "Local Admin · admin" and "Đang chạy Local Admin. Bật
AUTH_REQUIRED khi triển khai nhiều người dùng" — classic signature of `AUTH_REQUIRED`
being false. The owner reports editing secrets.toml but the form still does not
appear. Hypotheses (in order of likelihood):

1. The owner's `.streamlit/secrets.toml` is not the file being read (e.g., placed
   under a wrong `.streamlit` path, or the app was launched from a different working
   directory / stale Git checkout on the local machine).
2. Curly/typographic quotes broke TOML parsing so Streamlit fell back to defaults.
3. App launched before the secrets file was fixed; a rerun is needed.
4. The deployed (cloud) instance is what the owner keeps looking at; the deploy uses
   secrets set in the Streamlit Deploy UI, not local files.

## Next action

Run the candidate code in sandbox against the production URI (read-only probe first
via `probe_prod.py`; the owner already shared the URI template with `admin:<pwd>`;
use only if the owner confirms the exact working URI) to reproduce the bootstrap
behavior deterministically, then fix whatever prevents the form from rendering.

## Mojibake note

Vietnamese mojibake ("Đang cháº¡y...", "Äang cháº¥y") = UTF-8 bytes displayed as
Windows-1252/latin-1. This appears in the DEPLOYED app; the static Vietnamese
strings in the code are already correct UTF-8. The deployed env likely serves the
app with a wrong locale/encoding or the strings were saved mojibake at deploy time.
