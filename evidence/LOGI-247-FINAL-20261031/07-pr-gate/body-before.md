## Task and locked spec
TASK_REF: #247
SPEC_REF: https://github.com/7roger89-web/logistics-work-desk-arena/issues/247#issuecomment-6537951726

This PR now contains three scoped, independently reviewed slices: **S1 immutable snapshot**, **S2 staff payment browser**, **S3 synthetic A/B customer isolation browser**. Neither closes Issue #247. The broader candidate specification remains [SPEC_LOCK v2](https://github.com/7roger89-web/logistics-work-desk-arena/issues/247#issuecomment-6537935415). Owner HOLD and independent-review requirements remain in force.

## Observable outcome
Original goal: one independently accepted staging candidate preserves existing safety checks, passes two independent clean full-suite runs at its exact final HEAD, and passes the real browser critical paths. **That goal is not complete.**

S1 candidate behavior, verified through the real `save_contract_intl_snapshot` persistence seam: Sale first save of `SNAP-001` produces one row and one audit; same-ID/same-financial-payload replay is idempotent, including driver-added `_id`; changed financial payload is rejected without overwrite; a failed pre-insert lookup fails closed with zero insert calls; Viewer is denied. First/replay/tamper, failed lookup and Viewer cases run with the canonical unique index both absent and present. A separate natural duplicate-key race is verified with the index present.

**Delivery verified:** Control Tower independently inspected source/test/committed readback and exact-HEAD full-suite logs, then fast-forwarded existing PR #248 branch **without force** from `2941181d0f17701a7039d431262a0f35e27a848b` to `3516ce702f90d5a4a8582702ab0f9e38a1bd8cc6` using expected-head lease. The S1 candidate is now the actual PR HEAD, with no new PR or staging merge.

## Source contract
Measured before S1: `2941181d0f17701a7039d431262a0f35e27a848b`; S1 tested application-code HEAD: `3516ce702f90d5a4a8582702ab0f9e38a1bd8cc6`. Current PR #248 HEAD **after staging process merge**: `9012ee01763df491ec4d8bda9836cc3dee060aac` (parents: `20c9887...` and staging `ba03ae7...`; S3 reviewed source/evidence at `c0460ea826bdd54319b6ee2c3d63ea9e745fc223`, unchanged blobs).
Measured staging `arena/ae5f9f47-logistics-work-desk-arena`: `ba03ae7ac27f2020c761bf405e1aaaab80709c62` (read only).

The bounded product repair is in `core/database.py::save_contract_intl_snapshot`: a pre-insert lookup exception returns False before insert; the DuplicateKeyError replay comparison excludes driver-assigned `_id` from a copy of the attempted payload. The shared `_financial_fingerprint`, auth policy, Mongo identity, global fixtures and other workflows are unchanged. Product diff: +9/-6. Test diff: +223/-0, seven isolated S1 cases using real mongomock persistence/audit readback and explicit Sale/Viewer fixtures.

The frozen fail-before test file and final test file are byte-identical (`cmp` exit 0), SHA-256 `a7ed0e8fc59251b0823359ea021188678b2a6bf1dfd85b2224e908eb565c2d1a`. Final product-source SHA-256: `cfe9edc4f2cbce0643cb8ea74de5e731f7d3e53fb4dd51df8ee13881ff770d56`. No existing tests were deleted, skipped, deselected or weakened. PR #250 is comparison-only and remains unmerged.

## Wrong PASS
A failed `find_one` treated as an empty ledger must not proceed to insert. A unique index does not excuse a write after an unreadable guard. A same-financial-payload duplicate-key replay must not become a rejection solely because the driver inserted `_id` into the attempted document. Return booleans alone are insufficient: each S1 case reads back rows and audit, checks insert calls where relevant, and verifies isolated database cleanup.

S1 tested product source at `3516ce702f90d5a4a8582702ab0f9e38a1bd8cc6` remains byte-identical in current PR `c0460ea826bdd54319b6ee2c3d63ea9e745fc223`; S2/S3 added only test harness/fixture/evidence and checkpoint. Final-head full-suite still pending. Two historical full suite runs were at S1 HEAD, **not re-executed on new final PR HEAD**. The original #247 final-HEAD test gate is still pending. `contract-shape` is not functional proof. `contract-shape` is not functional proof. No concurrent-uniqueness guarantee is claimed when the unique index is absent, and mongomock results are not a real Mongo/Atlas durability or concurrency proof.

## Acceptance
- [x] Actual pre-change baseline at the current PR HEAD and frozen negative-test reproduction are recorded, including exit codes and persisted-state failures. This is evidence collection, not acceptance of the unrepaired PR HEAD.
- [x] S1 candidate fast-forwarded into the existing PR #248 head; independent source/negative-test review completed on SHA `3516ce702f90d5a4a8582702ab0f9e38a1bd8cc6`. No merge to staging.
- [x] Same-ID replay, tampering, index off/on, duplicate-key `_id` replay, failed-lookup/no-write and Viewer invariants pass on exact current PR HEAD (`3516ce702f90d5a4a8582702ab0f9e38a1bd8cc6`), with committed readback and fail-before proof.
- [x] **S2 staff** Chromium/Streamlit Components v2 write/readback at desktop/mobile: same DB payment+request+audit+event, pending no premature success, invalid input and Sale denial, reload preserved; independent artifacts reviewed at `63f959431b64e0c8a0103bd8214265f71852e6b2` (runner uses unchanged S1 product source).
- [x] **S3 A/B** real Chromium/Streamlit customer portal acceptance at desktop/mobile: two separately PUBLISHED lots with positive controls, A→B→A, private/stale draft isolation, forbidden metadata absent, ungranted/foreign accesses denied; source and screenshots reviewed at `c0460ea826bdd54319b6ee2c3d63ea9e745fc223`.
- [x] S1 product-code HEAD `3516ce702f90d5a4a8582702ab0f9e38a1bd8cc6`: two independent clean full-suite runs 2359 passed, 44 skipped, 0F/0E; collection/skip IDs unchanged. S2 added only `playwright/` test harness/evidence + docs; S3 also changes existing TEST-only fixture `tests/component/g15_lg_tt_discussion_runtime.py`, not app source or collected pytest tests.
- [ ] Original #247 **exact FINAL_HEAD** two-run full-suite gate still awaits final consolidation after S3 (no claiming the final full suite was rerun on `c0460ea826bdd54319b6ee2c3d63ea9e745fc223` when it was not).
- [ ] Independent final-HEAD review of original Issue #247 acceptance and the locked specifications, followed by no code/evidence mutation. Pending; Goal #247 is not DONE.

## Commands and results
All pytest results below were executor-run. Receipt-only flags do not deselect tests.

- Baseline at `2941181d0f17701a7039d431262a0f35e27a848b`: `python -m pytest tests -q -rs -p no:cacheprovider --junitxml=/home/user/s1-evidence/baseline.xml` — **2352 passed, 44 skipped, 10 subtests passed, 0F/0E, exit 0**.
- Frozen S1 tests before product repair at that same PR HEAD: `python -m pytest tests/test_intl_payment_comparator.py -q -p no:cacheprovider -o junit_family=xunit1 --junitxml=/home/user/s1-evidence/before.xml` — **3 failed, 48 passed, exit 1**. Failed IDs: duplicate-key driver-`_id` replay and failed lookup in both no-index/unique-index variants. Failed lookup returned True and persisted 1 row + 1 audit in both variants.
- At exact candidate `3516ce702f90d5a4a8582702ab0f9e38a1bd8cc6`, `python -m pytest tests/test_intl_payment_comparator.py -q` — **51 passed, 0 skipped, exit 0**.
- At that same candidate, `python -m pytest tests/test_intl_payment_comparator.py tests/test_lg08_1_safety.py -q` — **57 passed, 0 skipped, exit 0**.
- Clean full A: `python -m pytest tests -q -rs -p no:cacheprovider -o junit_family=xunit1 --junitxml=/home/user/s1-evidence/final-a.xml` — **2359 passed, 44 skipped, 10 subtests passed, 0F/0E, exit 0**, 155.09 s.
- Clean full B, independent `.venv/s1-b`: same command with `final-b.xml` — **2359 passed, 44 skipped, 10 subtests passed, 0F/0E, exit 0**, 152.89 s. Project bytecode was removed and pytest caching disabled before each run, in fresh processes. Dependency freezes match (`diff` exit 0); Python 3.11.2.
- Candidate collection: **2403**, baseline **2396**: exactly seven added S1 IDs, zero removed, zero added/removed skip IDs; the 44 baseline skip identities are unchanged. A/B collected-ID sets are identical.
- `cd component && npm ci --no-audit --no-fund` — exit 0, solely to install the existing jsdom dependency needed by the unchanged Python suite. No Node 06 work was performed in the S1 test run; S2 browser evidence is described separately below.
- `contract-shape` checks only PR structure/HEAD and may remain FAIL while incomplete acceptance is unchecked. Its observed run status is separate from the functional results; do not tick unfinished gates to force it green.

- S2: `node playwright/issue247_s2_browser.mjs --url http://127.0.0.1:9501/ --out evidence/issue247/s2 --chrome /tmp/chromium --puppeteer-core <installed-path>` — **12 PASS, browser exit 0**, real Chromium 153 + one test-only Streamlit process wrapping `app.py`. Backend validation: `python -m pytest tests/test_logi_interaction_latency_finalize_02.py -k payment_record_truthful_readback -q`: 1 passed, 17 deselected, exit 0. `python -m pytest tests/test_lg08_1_rbac_boundary.py -q`: 3 passed, exit 0. No full suite rerun after S2 evidence-only commit.

- S3: `LD_LIBRARY_PATH=/tmp/al2023/lib:/tmp node playwright/issue247_s3_browser.mjs --url http://127.0.0.1:9503/ --chrome /tmp/chromium --out evidence/issue247/s3 --puppeteer-core /tmp/pw-cli/node_modules/puppeteer-core` — **176 PASS (80 desktop/80 mobile/16 same-store server), browser exit 0**, Chromium 153, synthetic identities; focused customer/notes regressions **252 passed/exit 0**. These are Arena-run test logs, reviewed via source/evidence, NOT independently rerun here.

- Integration: GitHub two-parent commit `9012ee01763df491ec4d8bda9836cc3dee060aac` merged existing PR branch with staging (`ba03ae7`) **without force**, tree verified to preserve S1/S2/S3 product/testing blobs plus staged process files; repository files are unchanged apart from reconciled docs/process. FINAL_HEAD full pytest command: **NOT RUN yet** at this merge commit; local attempt to clone via `git ls-remote` failed (DNS `Could not resolve host: github.com`, exit 128). Do not infer test PASS from earlier SHA.

## Evidence on final HEAD
FINAL_HEAD: 9012ee01763df491ec4d8bda9836cc3dee060aac

**The above is the current PR HEAD including staged AGENTS/process files and S1/S2/S3 evidence.** S1 product source SHA `3516ce702f90d5a4a8582702ab0f9e38a1bd8cc6` remains unchanged, but TEST-only fixture source under `tests/component/` changed in S3. Two exact-final-HEAD full-suite runs are not yet evidenced.
S1_ORIGIN_BRANCH: arena/5a8ce272-logistics-work-desk-arena
S1_PREVIOUS_PR_HEAD: 2941181d0f17701a7039d431262a0f35e27a848b

- [Complete S1 execution receipt and readback table](https://github.com/7roger89-web/logistics-work-desk-arena/pull/248#issuecomment-6538604550).
- [Exact candidate commit](https://github.com/7roger89-web/logistics-work-desk-arena/commit/3516ce702f90d5a4a8582702ab0f9e38a1bd8cc6) and [committed S1 evidence](https://github.com/7roger89-web/logistics-work-desk-arena/tree/3516ce702f90d5a4a8582702ab0f9e38a1bd8cc6/evidence/issue247/s1).
- [Full clean run A transcript](https://github.com/7roger89-web/logistics-work-desk-arena/pull/248#issuecomment-6538576370).
- [Full clean run B transcript](https://github.com/7roger89-web/logistics-work-desk-arena/pull/248#issuecomment-6538576546).
- [Exact-HEAD collection and skip-ID comparison](https://github.com/7roger89-web/logistics-work-desk-arena/pull/248#issuecomment-6538576720).
- [Current repaired PR source/diff](https://github.com/7roger89-web/logistics-work-desk-arena/pull/248/files); pre-S1 baseline remains at `2941181d0f17701a7039d431262a0f35e27a848b`.

The candidate was committed before both clean full runs. Its HEAD/worktree stayed unchanged. Post-commit transcripts are linked here rather than added in another commit, avoiding a self-referential change to the measured SHA.

- [S2 Chromium browser results, real screenshots and same-store raw readback](https://github.com/7roger89-web/logistics-work-desk-arena/tree/63f959431b64e0c8a0103bd8214265f71852e6b2/evidence/issue247/s2).
- [Independent S2 review receipt](https://github.com/7roger89-web/logistics-work-desk-arena/pull/248#issuecomment-6540139182).

- [S3 real-browser evidence, screenshots, independently PUBLISHED A/B source and server deny readback](https://github.com/7roger89-web/logistics-work-desk-arena/tree/c0460ea826bdd54319b6ee2c3d63ea9e745fc223/evidence/issue247/s3).
- [Independent S3 review](https://github.com/7roger89-web/logistics-work-desk-arena/pull/248#issuecomment-6541789903).

## Boundaries and unknowns
**S1=PASS | S2=PASS | S3=PASS (synthetic TEST) | FINAL_HEAD_FULL_SUITE=NOT_VERIFIED | ISSUE247_GOAL=INCOMPLETE | PR248_STAGING_MERGE=HOLD.**

**MERGE_CONFLICT=RESOLVED:** merge commit `9012ee01763df491ec4d8bda9836cc3dee060aac` has two parents (PR candidate + staging `ba03ae7`), reconciles `docs/NEXT.md` with the Owner's post-#249 process checkpoint and keeps staged `AGENTS.md`, `.github/pull_request_template.md`, `.github/workflows/logi-pr-contract.yml`. GitHub now reports `mergeable=true`, but `mergeable_state=blocked` until required check and final-HEAD review PASS. Staff payment and A/B tenant browser evidence independently reviewed; real Google OIDC, Cloud and final acceptance remain pending. No replacement PR, no Cloud/production approval.

S1 production repair limited to `core/database.py` and focused tests; S2/S3 add only test-only browser fixture/runner, evidence and docs/NEXT checkpoint. No product code changes after S1. No auth-policy, Mongo-identity, other UI/test or shared-fingerprint edits; no new framework, collection or writer. No Cloud/Atlas/Drive/production/main writes. PR #250 was read only and not merged. S2/S3 browser evidence independently reviewed, but branch conflict, final two clean suite runs and exact-final-HEAD holistic review remain outstanding. Do not declare Goal DONE.

