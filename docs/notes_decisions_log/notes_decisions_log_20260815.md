# Notes & Decisions Log — 2026-08-15

## LOG-C06 — Owner decisions applied to staging review

- Applied Owner-confirmed staging metadata for the six business decisions under
  batch `LOG-C06-OWNER-DECISIONS-2026-08-15`.
- Preserved source workbook hash
  `857DB72B86220A4AF302C0DE6900710C49F44B2223C458C009748DD767840B70`.
- Confirmed 24,576 CNY as embedded in the 99,824.43 CNY snapshot; excluded it
  from standalone opening contribution.
- Confirmed 62,464 CNY and 1,687 CNY as separate Thành
  `received_on_behalf` events; no shipment ID was invented.
- Kept 1,572 CNY `REVIEW_REQUIRED` and excluded it from opening/debit buckets.
- Represented 25,025 CNY B&G Green as two separate money legs and included it
  only in the paid-on-behalf group after Owner confirmation.
- Reconstructed 134,973 CNY from 11 components and 159,998 CNY from those
  components plus 25,025 CNY; summary/derived totals cannot be counted as new
  events.
- Historical received-group source sum is 349,448.3929340609 CNY versus the
  416,482.2426005565 CNY expectation; the 67,033.84966649559 CNY difference
  remains visible and blocks opening publication.
- Stored statuses: CONFIRMED 20, REVIEW_REQUIRED 170, RAW 39,
  NOT_APPLICABLE 60, PROPOSED 0. Canonical writes: 0.
- Cutover remains `DRAFT / NOT_APPROVED / NOT_LIVE`.
- Coder report: `reports/coder/rp_coder_260815_094910_by_gpt-5-codex_log_c06_owner_staging.md`
- Data-integrity report: `reports/Data-Integrity/rp_data_260815_094501_by_gpt-5-codex_log_c06_owner_staging.md`
- QA report: `reports/QA/playwright/2026-08-15-log-c06-owner-decisions-phase.md`
- Supervisor report: `reports/supervisor/rp_supervisor_260815_095407_by_gpt-5-codex_log_c06_owner_staging.md`

## Owner action still required

One reconciliation decision remains: identify the source lineage for the
67,033.84966649559 CNY gap or confirm which historical checkpoint basis governs.
No balancing event should be created from the difference alone.

## LOG-C06 terminal product closure — 2026-08-15

- Owner roadmap decision: close LOG-C06 as `PRODUCT_PASS`; do not spend more
  Goal time on complete A Bò historical reconciliation.
- Historical staging, historical provenance mechanism, Owner review,
  checkpoint reconstruction, double-count protection, and cutover sufficiency:
  `PASS`.
- Canonical financial mutation: `0`; A Bò historical live opening:
  `NOT_PUBLISHED`; cutover publication: `DEFERRED_OWNER_GATED`.
- `161,576.5473994435 CNY` remains historical reconciled
  candidate/checkpoint evidence only, never an approved/live opening.
- Remaining ambiguity is preserved in
  `.p2p/state/deferred-historical-reconciliation.json` and remains searchable;
  no guessing, deletion, balancing, or publication is allowed.
- Proven capabilities are partner-generic. A Bò remains one partner instance.
- LOG-C07 may start only in a new chat and must cover the whole Logistics
  product. No LOG-C07 work begins in this closure.
