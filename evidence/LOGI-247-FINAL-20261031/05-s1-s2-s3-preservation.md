# 05 — S1 / S2 / S3 source and evidence preservation at PR #248 HEAD

Scope: re-check that the reviewed S1/S2/S3 material is still present and byte-identical at
`9012ee01763df491ec4d8bda9836cc3dee060aac`. This is an identity check, **not** a re-run of the
browser flows.

## 1. S1 — immutable international-payment snapshot (`3516ce702f90d5a4a8582702ab0f9e38a1bd8cc6`)

| Check | Result |
|---|---|
| `git diff --stat 3516ce7 9012ee0 -- core/database.py tests/test_intl_payment_comparator.py evidence/issue247/s1` | **empty, exit 0** — byte-identical |
| `core/database.py` sha256 at HEAD | `cfe9edc4f2cbce0643cb8ea74de5e731f7d3e53fb4dd51df8ee13881ff770d56` (= SHA published in the PR body/S1 evidence) |
| `tests/test_intl_payment_comparator.py` sha256 | `a7ed0e8fc59251b0823359ea021188678b2a6bf1dfd85b2224e908eb565c2d1a` (= frozen fail-before test file; unchanged) |
| `evidence/issue247/s1/` (12 files incl. `baseline-collection.json.gz`, `source.diff`, `tests.diff`, `readback.json`) | present, unchanged |
| Product-code change after S1 | **none** (`git diff --name-status 3516ce7 9012ee0 -- core views component/src` shows nothing) |

## 2. S2 / S3 — reviewed browser evidence (`63f9594…`, `c0460ea…`)

| Artifact | State at `9012ee0` |
|---|---|
| `evidence/issue247/s2/` (24 files: browser-results.json, 10 screenshots, rbac-negative, readback-history) | present, added by `63f9594` |
| `playwright/issue247_s2_browser.mjs` / `issue247_s2_runtime.py` | present — sha256 `c9c1580…` / unchanged |
| `evidence/issue247/s3/` (33 files: 16 screenshots, server readback/negative/publications, fail-before baseline) | present, added by `c0460ea` |
| `playwright/issue247_s3_browser.mjs` | present — sha256 `118bdac…` |
| `tests/component/g15_lg_tt_discussion_runtime.py` | present — sha256 `a481e7cdfcbb4bc299025d662cb2fe3c5734ca4ae5aa0bbd8e91e963df519a2c` (TEST-only fixture changed by S3, as declared in the PR body) |
| Served component bundle `component/dist/logi-shell.js` / `.css` | sha256 `86136e87…` / `abb6e188…` — unchanged by the integration |

The only post-S1 source delta in the whole tree is that **test-only** fixture plus docs/CI/evidence
files:

```
A .github/pull_request_template.md
A .github/workflows/logi-pr-contract.yml
M AGENTS.md
M docs/NEXT.md
A evidence/issue247/s2/**   A evidence/issue247/s3/**
A playwright/issue247_s2_browser.mjs  A playwright/issue247_s2_runtime.py  A playwright/issue247_s3_browser.mjs
M tests/component/g15_lg_tt_discussion_runtime.py
```

## 3. Why the browser flows were not re-run

Per SPEC_LOCK acceptance 3 and OE_GATE `SMALLER_VERIFIABLE_SLICE`: the S2/S3 runners, fixtures and
product source are unchanged since their independent review, so re-running the identical 12-check and
176-check Chromium flows would add no decision value. Their status therefore stays
`S2=PASS / S3=PASS` **as reviewed at their own SHAs**, explicitly **not** upgraded to
"re-verified on `9012ee0`".

## 4. Merge integrity

```
git rev-list --parents -n1 9012ee0
9012ee01763df491ec4d8bda9836cc3dee060aac 20c9887a88bf94ab751e3553795ea8273f24eaf4 ba03ae7ac27f2020c761bf405e1aaaab80709c62
tree 9ca879480055cefcd8aeda3f66886ab2b4363aad
```

Two parents: the PR candidate `20c9887` and staging `ba03ae7` (PR #249 process gate) — matching the
SPEC_LOCK description. GitHub REST agrees: `base.sha = ba03ae7ac27f2020c761bf405e1aaaab80709c62`,
`mergeable = true`, `mergeable_state = blocked`.
