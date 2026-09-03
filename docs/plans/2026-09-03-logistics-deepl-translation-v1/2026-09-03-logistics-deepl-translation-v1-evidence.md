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
  `219bd0aaf6dafbf2c6fd3d5340f6393d5ae3011f` with untracked Owner files.
  Reflog showed a transient `main -> origin/main` reset during setup; the
  ref was restored by an explicit expected-old-value update to
  `3c1e1c7bebd2b4313677ee5cdfdc484ade6b8a14`. The root working tree was not
  reset, cleaned, or modified. Local `main` remains diverged from origin/main
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

- `E2-P2A-IMPACT1`: refreshed Anvien detail/impact before and after route/RBAC
  wiring. `core/auth.py` is a CRITICAL shared permission surface affecting 5
  files/1 flow; `views/web_app.py` is MEDIUM with 2 affected files/1 flow.
  The edit remained one permission plus one route/group entry.
- `E2-P2A-RBAC1`: `translation` was added only to modern `sale` and `support`
  role sets; admin retains wildcard access and viewer/anonymous do not gain
  the permission. The route points to `views.translation.ui_translation` and
  is listed in `CÔNG CỤ & THAM KHẢO`.
- `E2-P2A-STALE1`: the existing C15 RBAC test contradicted the already merged
  PR #8 support-full-operational policy. Its stale expected set/test names were
  aligned to current `origin/main` policy; no permission policy was changed to
  make the test pass.
- `E2-P2A-TEST1`: `python -m unittest tests.test_deepl_route_rbac
  tests.test_logc15_auth_rbac -v` ran `33/33 PASS`.
- `E2-P2B-UI1`: `views/translation.py` is parsed with 20 symbols, 2 related
  files, and 9 linked flows. The view renders the accepted language controls,
  source text, context toggle, translation action, and explicit usage action.
- `E2-P2B-FLOW1`: focused AppTest exercised support mount, Chinese ->
  Vietnamese translation trigger, result text, detected source, billed
  characters, API index, swap to Vietnamese -> Chinese, and usage table.
- `E2-P2B-SEC1`: mocked UI visible-text scans found neither fake key in the
  rendered page; no database function is imported or called by the view.
  Unexpected provider errors are converted to generic UI text and are not
  logged with arbitrary exception content.
- `E2-P2C-TEST1`: the full focused family command ran `50/50 PASS` across
  service/config, route/RBAC, stale-policy alignment, and mounted UI tests.
- `E2-P2C-BUILD1`: `python -m py_compile views/translation.py
  views/web_app.py core/auth.py` passed; no Dockerfile exists in this repo.
- `E2-P2C-ANV1`: staged Anvien detect-changes found exactly 11 intended
  changed paths, 11 affected files, 9 affected flows, and HIGH aggregate risk
  due to the shared auth/router boundaries plus the new view/service links.
  `git diff --cached --check` passed; no unrelated source path entered the
  staged candidate.
- `E2-P2C-LOCAL1`: real DeepL smoke and a live Streamlit preview were not run
  because the clean branch has no configured local key. This is the required
  Owner gate, not mocked evidence of real API readiness.
- `E2-P2C-REVERSE1`: the mounted UI test also clicked DỊCH after selecting
  Vietnamese -> Simplified Chinese and asserted the service received `VI` ->
  `ZH-HANS`; this closes the reverse language workflow at the mocked boundary.

## Closure Evidence

Before the final Supervisor review, the candidate is frozen at implementation
commit `fb1c380bf079a901820426fe9869b914a08da5b3`, tree
`7351d073fe00e1780454bca6e2c8cb4f21029348`. It is three commits ahead of
fresh `origin/main` and its ancestry check passes. The coder report is
`reports/coder/rp_coder_260903_175900_by_gpt-5-codex_logistics-deepl-translation-v1.md`.
The closure package is now at `1f6469e0328f0ac78b63b060261a61747164bab2`
with tree `ea3568c7f93dcf88a8d868e566d91f6db9891161`, five commits ahead of
fresh `origin/main`; its ancestry check passes. Final Supervisor verdict,
Owner local key gate, and push/PR/deploy status are recorded in the report and
return packet.

- `E3-CLOSURE1`: implementation candidate `fb1c380bf079a901820426fe9869b914a08da5b3`
  has tree `7351d073fe00e1780454bca6e2c8cb4f21029348`, is three commits ahead
  of fresh `origin/main`, and passes the ancestry check.
- `E3-CLOSURE2`: final compileall and focused family validation completed with
  `50/50 PASS`; focused UI evidence covers both ZH -> VI and VI -> ZH-HANS at
  the mocked boundary. Credential-like literal scan is clean and no DeepL
  production file imports the database or another provider.
- `E3-CLOSURE3`: clean worktree has zero configured DeepL keys and no local
  secrets file. Real API smoke/live preview therefore remain `NOT_RUN` by the
  explicit Owner gate. No production DB mutation, push, PR, merge, or deploy
  occurred. Exact next action is: `Thêm API DeepL vào .streamlit/secrets.toml local. Không gửi key vào chat/GitHub.`
- `E3-CLOSURE4`: original root checkout remains detached with its untracked
  Owner work preserved; local `main` is restored to its pre-task divergent
  SHA. The branch is ready for exact Supervisor review and then Owner local
  visual gate, not production promotion.
- `E3-CLOSURE5`: the staged report/evidence closure package contains five
  intended documentation/report paths; Anvien detect-changes classified it
  LOW risk with zero affected runtime flows, and `git diff --cached --check`
  passed before the report checkpoint.
