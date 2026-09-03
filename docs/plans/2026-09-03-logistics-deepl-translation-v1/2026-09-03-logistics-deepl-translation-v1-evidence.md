# LOGISTICS DeepL Translation V1 Evidence Ledger

## Metadata

- Date: `2026-09-03`
- Plan: `docs/plans/2026-09-03-logistics-deepl-translation-v1/2026-09-03-logistics-deepl-translation-v1-plan.md`
- Evidence: `docs/plans/2026-09-03-logistics-deepl-translation-v1/2026-09-03-logistics-deepl-translation-v1-evidence.md`
- Benchmark: `docs/plans/2026-09-03-logistics-deepl-translation-v1/2026-09-03-logistics-deepl-translation-v1-benchmark.md`
- Actual status: `docs/plans/2026-09-03-logistics-deepl-translation-v1/2026-09-03-logistics-deepl-translation-v1-actual-status.md`

## Evidence Rules

- Fresh `origin/main` and the user-provided DeepL contract are the authority.
- The root detached checkout and existing worktrees are preserve-only.
- No real secret value may be read into evidence, tests, logs, UI, or reports.
- Mocked service evidence proves behavior only; it does not prove real API
  availability.
- Production and production databases are outside the runtime boundary.
- Detailed command output belongs here; benchmark files contain measurements
  only.

## E0 - P0 Evidence

Matching plan item(s): `P0-A`

- `E0-P0A-GIT1`: `git fetch origin --prune` completed. Fresh
  `origin/main` is `c1c9468a814a2c0e56cefcf2851a2cadf46df436` with tree
  `6466d7fa435b46d4d13b0b92558ed354f62c4363`; the merge subject is PR #8
  from `fix/support-full-operational-permissions`.
- `E0-P0A-BRANCH1`: clean worktree
  `D:\Logistics_App_GitHub\.tmp\logistics-deepl-translation-v1` is on
  `feature/logistics-deepl-translation-v1` at the exact fresh origin/main
  SHA/tree and tracks `origin/main`.
- `E0-P0A-PRESERVE1`: original `D:\Logistics_App_GitHub` is detached at
  `219bd0aaf6dafbf2c6fd3d5340f6393d5ae3011f` with untracked Owner files and
  was not reset, cleaned, or modified. Its local `main` at
  `3c1e1c7bebd2b4313677ee5cdfdc484ade6b8a14` is diverged from origin/main
  (93 commits only on origin/main and 3 only on local main), so a safe
  fast-forward of that ref is not possible and was not forced.
- `E0-P0A-ANV1`: Anvien baseline indexed 473 files, parsed 227 code files,
  had 0 parse failures, and built 36,985 graph nodes / 42,422 relationships.
- `E0-P0A-REL1`: Anvien file-detail relationship counts are config 3,
  auth 4, and web router 1 related file; all three are parsed, non-stale,
  high-risk surfaces. Web-router file impact was inspected before edits.
- `E0-P0A-SRC1`: existing config has `get_list_setting`; `requests` is already
  in `requirements.txt`; `core/auth.py` is the sole `ROLE_PERMISSIONS` matrix;
  `views/web_app.py` owns the route tuple and `CÔNG CỤ & THAM KHẢO` group.
- `E0-P0A-MISSING1`: `core/deepl_translation.py`, `views/translation.py`,
  and `tests/test_deepl_translation.py` are absent on the fresh branch.
- `E0-P0A-SECRET1`: only secret-path presence was checked. The clean branch
  has no `.streamlit/secrets.toml` and no `DEEPL_API_KEYS` environment value;
  the original root secret file was detected but not read or copied.
- `E0-P0A-BOUNDARY1`: no Dockerfile exists in the repository; this local-only
  Streamlit scope uses native Streamlit/AppTest/browser evidence and does not
  start production.

## E1 - P1 Evidence

Matching plan item(s): `P1-A`, `P1-B`, `P1-C`

- `E1-P1A-IMPACT1`: refreshed Anvien detail/impact after the service existed.
  `core/deepl_translation.py` is parsed with 87 symbols, 1 related file, and
  HIGH file impact over the service/test family; `core/config.py` remains a
  LOW-impact supporting config surface. The warning is contained to the new
  service/test flow and did not justify unrelated refactoring.
- `E1-P1A-CONFIG1`: `core/config.py` now loads `DEEPL_API_KEYS` through the
  existing `get_list_setting` convention; `.env.example` documents only fake
  placeholders. `python -m py_compile core/config.py core/deepl_translation.py`
  passed, and no real key value was read.
- `E1-P1A-TEST1`: `python -m unittest tests.test_deepl_translation -v` ran
  `14/14 PASS`, including TOML/env list loading, no-key fail-closed, and
  input-size validation.
- `E1-P1B-ROTATE1`: the focused mocks proved first-key success, HTTP 456
  rotation to API 2, 401/403 skip, same-key 429 retry, 5xx/network finite
  retry, and rate-limit failover. The test sleeper observed only bounded
  delays `[0.25, 0.5]` before failover/success.
- `E1-P1B-SEC1`: terminal/error/log assertions proved fake keys are absent
  from `DeepLTranslationError` and logger output; service logs contain only
  API index/count and status-safe text. No Gemini or other-provider fallback
  exists in the new path.
- `E1-P1C-USAGE1`: `check_usage()` mapped mocked character count/limit to
  used/limit/remaining and mapped HTTP 456 to `Hết quota`; `UsageRow` and
  `to_display_dict()` contain index/status/count fields only.
- `E1-P1C-BOUNDARY1`: translation success generated one POST request only;
  usage generated GET requests only after the explicit `check_usage()` call.
  No usage request is made at module import or by the translation method.
- `E1-P1C-ANV1`: staged Anvien detect-changes found exactly the nine intended
  changed paths (config, env example, service, focused tests, and four plan
  files), nine affected service/document flows, and HIGH aggregate risk driven
  by the new service boundary. No unrelated application path was included and
  `git diff --cached --check` passed.

## E2 - P2 Evidence

Matching plan item(s): `P2-A`, `P2-B`, `P2-C`

Implementation and local runtime evidence will be appended as each P2 slice
completes.

## Closure Evidence

Final branch identity, detect-changes, focused validation, supervisor verdict,
Owner local key gate, and push/PR/deploy status will be appended only after the
candidate is frozen.
