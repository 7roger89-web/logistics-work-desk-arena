# Notes and decisions — 2026-08-06

- Unified bank transfer, proxy payment, and entrustment wallet under the Contract workspace; kept customer-level `Thu tiền & Công nợ` as a separate bounded context.
- Canonical shipment relation is `contract_id`; legacy shipment and payment fields remain readable during migration.
- Bounded date filters now use nested shipment business date first and exclude missing/invalid dates instead of inventing today.
- CBPG dynamic rows receive sequential STT values and category-specific exception choices for Ghế/Bàn.
- Browser smoke passed the previous-month range and consolidated sidebar, but Mongo SRV DNS timeout blocked DB-backed persistence E2E.
- Coder report: `reports/coder/rp_coder_260806_095344_by_gpt-5-codex_contracts-filter-cbpg.md`.
- Supervisor verdict: `REJECT` pending reachable MongoDB and fresh write–reload–render evidence: `reports/supervisor/rp_supervisor_260806_095344_by_gpt-5-codex_contracts-filter-cbpg.md`.
