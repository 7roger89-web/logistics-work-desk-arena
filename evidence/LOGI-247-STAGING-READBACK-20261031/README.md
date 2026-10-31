# LOGI-247-STAGING-READBACK-20261031 — Staging readback of PR #248

TASK_ID: `LOGI-247-STAGING-READBACK-20261031`
DATE: 2026-10-31
DESTINATION: ARENA (`NEW_CHAT`)
REQUIRED_SKILLS: `qa`
NATURE: read-only verification. No merge, no push to `main`, no staging mutation, no deploy.

## Accepted head under verification

`ACCEPTED_HEAD = 9012ee01763df491ec4d8bda9836cc3dee060aac`
(Owner/Control Tower declared this as the PR #248 head to be verified in staging.)

## Result summary

| # | Acceptance criterion | Measured | Verdict |
|---|---|---|---|
| 1 | PR #248 = MERGED | `state=open`, `merged=false`, `merged_at=null`, `/merge` endpoint 404 | **NOT MET** |
| 2 | Staging contains `9012ee0` in ancestry | staging `arena/ae5f9f47…` = `ba03ae7`; compare staging→`9012ee0` = `ahead_by=8, behind_by=0`, merge-base = `ba03ae7` | **NOT MET** |
| 3 | S1/S2/S3 source+test intact | byte-identical on the **PR branch** (`cmp` exit 0); **absent from staging** | **NOT MET in staging** |
| 4 | No Cloud/OIDC PASS inferred from a GitHub merge | no merge exists; no such claim made | **HONORED** |

`VERDICT=INCOMPLETE` — `BLOCKER=PR_248_NOT_MERGED_BY_OWNER`.

## What is true, precisely

1. **PR #248 is still open.** `gh api .../pulls/248` →
   `{"state":"open","merged":false,"merged_at":null,"mergeable":true,"mergeable_state":"clean","head":"9012ee0…","base":"arena/ae5f9f47-logistics-work-desk-arena"}`.
   The dedicated merge-state endpoint `.../pulls/248/merge` returns HTTP 404 / exit 1, which per GitHub
   REST means "has not been merged".

2. **`merge_commit_sha` on an open PR is a trap, not a merge.** The field
   `1540a04e1060933d184feb174fd42c0c100aa5ce` is GitHub's ephemeral *test-merge* commit
   (compare against staging = `ahead_by=9`). It is not on any branch and does not mean the PR was
   merged. `merged=false` on the same response is authoritative.

3. **There is no `staging` branch in this repository.** 124 branches, zero matching
   `staging|stage|preprod|uat`; `branches/staging` = 404. The branch this workflow calls "staging" is
   the PR #248 base `arena/ae5f9f47-logistics-work-desk-arena` at
   `ba03ae7ac27f2020c761bf405e1aaaab80709c62` (the PR body also measures it as `ba03ae7`, "read only").

4. **Staging does not contain the accepted head.** `9012ee0` is a *descendant* of staging:
   merge-base = `ba03ae7` = staging tip, `behind_by=0`, `ahead_by=8`. The 8 commits staging lacks:
   `661fdfc`, `cf30b3b`, `2941181`, `3516ce7`, `63f9594`, `c0460ea`, `20c9887`, `9012ee0`.
   Note the direction: `9012ee0` is `merge(staging): …` — the PR branch merged *staging into itself*
   (second parent `ba03ae7`). That is not a staging merge.

5. **`main` also does not contain it.** compare `main...9012ee0` = `diverged`, `ahead_by=102`,
   `behind_by=11`. Local HEAD = remote `main` tip = `cd57bb8`.

6. **S1/S2/S3 are intact — on the PR branch, not in staging.** SHA-256 of blob contents:

   | File | PR head `9012ee0` | `3516ce7` (reviewed S1) | staging `ba03ae7` | `main` |
   |---|---|---|---|---|
   | `core/database.py` (S1 product) | `cfe9edc4…770d56` | `cfe9edc4…770d56` (`cmp` exit 0) | `cde2e545…48bf002` | `464a044c…ff7ea` |
   | `tests/test_intl_payment_comparator.py` (S1 tests) | `a7ed0e8f…65c2d1a` | `a7ed0e8f…65c2d1a` | `0b05bd72…57bbbee` | `0b05bd72…57bbbee` |
   | `playwright/issue247_s2_browser.mjs` (S2) | `c9c15801…0c06ca0` | absent | **absent (404)** | **absent (404)** |
   | `playwright/issue247_s3_browser.mjs` (S3) | `118bdacc…e2bf386` | absent | **absent (404)** | **absent (404)** |
   | `tests/component/g15_lg_tt_discussion_runtime.py` (S3 fixture) | `a481e7cd…f519a2c` | `a05a2ce5…6ddd0d` | `a05a2ce5…6ddd0d` | **absent (404)** |

   The two PR-claimed hashes are reproduced exactly at the accepted head
   (`a7ed0e8f…` test file, `cfe9edc4…` product source), and `cmp` between `3516ce7` and `9012ee0`
   for the product source exits 0. So the reviewed bytes were not lost *within* the PR branch — they
   simply never reached staging. The 4 `test_s1_*` cases present at the accepted head are absent from
   the staging copy of the same file.

7. `contract-shape` CI check on the PR = `pass`. It is a structure/HEAD check only and is **not**
   evidence of merge, staging content, runtime behavior, or Cloud/OIDC state.

## Explicit non-claims

- No claim of `MERGED`, staging promotion, Cloud deploy, OIDC/auth, Atlas/Mongo durability, or
  browser runtime PASS is made here. A GitHub merge would not have proven any of those either.
- The two isolated full-suite runs (RUN A / RUN B, `2359 passed / 44 skipped / 0F / 0E`) cited by the
  PR body were **not** re-run by this readback; this task only measured refs, ancestry and blob
  identity. Re-running the suite is out of scope and would not change the blocked merge state.
- Mongo-fixture tests remain skipped by design; `mongomock` is not a real-Mongo proof.

## Files

| File | Contents |
|---|---|
| `transcript.txt` | full recorded run: A. PR #248 REST state + merge endpoint + CI; B. 124-branch inventory, no staging ref; C. accepted-head parents, staging→accepted and main→accepted compares, ephemeral test-merge check; D. per-ref SHA-256 of the five S1/S2/S3 files; E. S1 test additions diff and `cmp` |
| `collect.sh` | re-runs every measurement above (read-only, exit 0) |

Reproduce: `bash evidence/LOGI-247-STAGING-READBACK-20261031/collect.sh` (collector exit 0, rewrites `transcript.txt`).

## Required next step (Owner/Control Tower)

Merge PR #248 into its base `arena/ae5f9f47-logistics-work-desk-arena` (the "staging"), or state which
ref is meant by "staging". Then re-run this collector — criterion 2 becomes provable —
before any staging or Cloud claim. This readback deliberately did not perform that merge.
