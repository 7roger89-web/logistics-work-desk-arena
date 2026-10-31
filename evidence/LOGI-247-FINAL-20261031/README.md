# LOGI-247-FINAL-20261031 — exact-HEAD clean-suite evidence for PR #248

```
TASK_ID=LOGI-247-FINAL-20261031          DESTINATION=ARENA            MODE=SAME_CHAT
SPEC_LOCK=issues/247#issuecomment-6541826895
PR248_HEAD_MEASURED=9012ee01763df491ec4d8bda9836cc3dee060aac   (REST == git fetch, match)
FINAL_SUITE=PROVEN (two clean independent full suites, exit 0, 0 FAILED / 0 ERROR)
PR248_VERDICT=INCOMPLETE
BLOCKER=required check `contract-shape` FAILURE on this HEAD (unchecked acceptance lines) + independent exact-HEAD review not yet performed
```

This bundle is stored on the **session branch** `arena/dfd56039-logistics-work-desk-arena`
(base `fd9b265…`). **No evidence was committed into the PR HEAD**, and the PR HEAD was not moved,
amended or force-pushed. Nothing was written to `main`, staging, Cloud, Atlas or production.

---

## 1. HEAD nguồn, HEAD kiểm thử, worktree, preflight

| Item | Value |
|---|---|
| Source (session branch) HEAD | `fd9b265596da33c49d74a07a487022ab4a1838ea` (`arena/dfd56039-…`, clean before this bundle) |
| Tested HEAD (PR #248) | `9012ee01763df491ec4d8bda9836cc3dee060aac` |
| Verification path 1 — REST | `gh api repos/…/pulls/248 --jq '{head,base,state}'` → `head=9012ee0…`, `base=ba03ae7…`, `state=open`, **exit 0, empty stderr** |
| Verification path 2 — Git | `git fetch origin pull/248/head` (exit 0) → `git rev-parse FETCH_HEAD` = `9012ee0…` |
| PR head/base refs | head `arena/f1a205f4-…`, base `arena/ae5f9f47-…` (staging) — matches SPEC_LOCK |
| Worktrees used | `/tmp/wtA`, `/tmp/wtB`, both `git worktree add --detach` at `9012ee0…`, both `rev-parse HEAD` = `9012ee0…`, both `status --short` empty |
| Existing worktree | left untouched — no `reset`, no `stash`, no checkout |

Preflight (details in `00-preflight.md`):

- `P2P_LAW_SOURCE=LOCAL_PORTABLE` — `.p2p/portable/P2P-OPERATIONS-NOTEBOOK.md` with
  `P2P_PORTABLE_LAW_PROJECTION=YES`, canonical provenance and package `8.4.7-C-codex.74`; canonical
  repo not reached in this session and **not probed** just to manufacture a fallback.
- `LAW_CHECK` — `AGENTS.md` read at PR HEAD (blob `2bd3867…`), portable skill manifest 53/53 hashes
  match, experience capsule hash matches its header.
- Skill receipt — `qa` @ `.agents/skills/qa/SKILL.md` sha256 `a377e48c…`, read and applied before
  substantive work (no-fix role honoured: zero product/test/fixture edits).
- Checkpoints 00/05/06 — **`ops/arena-control/00-05-06` do not exist at PR #248 HEAD** (they exist
  only on main `fd9b265`, added by PR #252). The numbered `evidence/issue247/00…08` logs **do** exist
  but are bound to historical SHAs (`1144af5`, `661fdfc`, `cf30b3b`) and are therefore **not used as
  proof** for `9012ee0`.
- `OE_VERDICT=DO_IT` — see `00-preflight.md` §4.

## 2. Hai full-suite (two separate processes, two separate environments)

Each run: fresh detached worktree at the same SHA, own `python -m venv`, own
`pip install -r requirements.txt pytest`, own `cd component && npm ci`, own process.

| | RUN A | RUN B |
|---|---|---|
| worktree | `/tmp/wtA` @ `9012ee0` | `/tmp/wtB` @ `9012ee0` |
| interpreter | `/tmp/venvA` (prefix `/tmp/venvA`) | `/tmp/venvB` (prefix `/tmp/venvB`) |
| python / pytest | 3.11.2 / pytest 9.2.0 | 3.11.2 / pytest 9.2.0 |
| `pip install -r requirements.txt pytest` | exit 0 | exit 0 (`pip freeze` identical, `diff` exit 0) |
| `cd component && npm ci` | **exit 0** | **exit 0** |
| command | `python -m pytest tests -q -rs -p no:cacheprovider` | same |
| **exit code** | **0** | **0** |
| PASSED | **2359** | **2359** |
| FAILED | **0** | **0** |
| ERROR | **0** | **0** |
| SKIPPED | **44** | **44** |
| xfail / xpass / deselected | 0 / 0 / 0 | 0 / 0 / 0 |
| subtests | 10 passed | 10 passed |
| wall | 151.55 s | 160.48 s |
| stderr | 0 bytes | 0 bytes |

Raw artifacts: `02-run-a/stdout.txt|stderr.txt|exit.txt|npm-ci.*`, `03-run-b/…`.

## 3. So sánh collected IDs, skipped IDs và bằng chứng

| Check | Result |
|---|---|
| Collected (A / B) | **2403 / 2403**, sets identical, sha256 `552021c2…` both |
| passed + skipped = collected | 2359 + 44 = 2403 ✔ |
| Collected vs S1 baseline (2396 @ `2941181`) | +7 new S1 IDs in `tests/test_intl_payment_comparator.py`, **0 lost**; 2396 + 7 = 2403 ✔ |
| Skipped IDs A / B / S1 | **44 / 44 / 44**, all three sets byte-identical, sha256 `12acbd9f…` |
| Skip expansion | **NONE** (7 mongo-by-design + 21 historical workbook + 6 excel + 10 docgen, same as S1) |
| Same SHA in both logs | YES — `git rev-parse HEAD` captured in each worktree = `9012ee0…`, equal to REST `.head.sha` |
| Cloud/OIDC claimed from mongomock | **NO** — `CLOUD_OIDC=NOT_VERIFIED`, `MONGO_PROOF=SKIPPED_BY_DESIGN` |

Details and full ID lists: `04-comparison.md`, `04-comparison.json`,
`02-run-a/skipped-ids.txt`, `03-run-b/skipped-ids.txt`, `s1-baseline-skipped-ids.txt`.

## 4. PR #248 — verdict, blockers

**PROVEN (suite gate):** the exact PR HEAD `9012ee0…` produces two clean full-suite runs, 0 FAILED,
0 ERROR, unchanged skip set, same SHA in both logs, in two independent processes/environments.

**INCOMPLETE (PR readiness):** PR #248 cannot be called ready for staging integration yet.

| Blocker | Evidence | Why it is a blocker, not a test failure |
|---|---|---|
| `contract-shape` = **FAILURE** on `9012ee0…` (2 runs, 09:41:56Z / 09:42:40Z) | `06-contract-shape.txt`; exact predicate reproduced locally → only failing rule is `Acceptance: include completed checks; do not leave unchecked acceptance` | It is a required Ruleset check; the two unchecked lines are "final-HEAD full suite" (now evidenced) and "independent review" (not self-certifiable). Ticking them to force green is the declared WRONG_PASS |
| Independent exact-HEAD review | not performed in this task by design | `AGENTS.md` / SPEC_LOCK acceptance 4–5: executor cannot self-certify review |
| Cloud / real Google OIDC | never exercised | out of scope; `CLOUD_OIDC=NOT_VERIFIED` |
| Real Mongo durability/concurrency | 7 Mongo tests skipped by design | `MONGO_PROOF=SKIPPED_BY_DESIGN`; mongomock is not Mongo |

`PR248_STATE=open`, `mergeable=true`, `mergeable_state=blocked` — the PR stays **HOLD**. No merge,
no PR body checkbox flipped, no new PR, no `main`/staging/Cloud write, Issue #247 **not** marked DONE.

## 5. File map

```
00-preflight.md                 law source, LAW_CHECK, skill receipt, checkpoint status, OE gate
01-pr248-head-verification.txt  raw REST + git transcripts with exit codes and stderr
02-run-a/                       full suite A: stdout, stderr, exit, collect-only, ids, env, freeze, npm ci, junit
03-run-b/                       full suite B: same set
04-comparison.md                ID/skip comparison and what it does not prove
04-comparison.json              machine-readable comparison
05-s1-s2-s3-preservation.md     S1/S2/S3 source+evidence identity at the PR HEAD
06-contract-shape.txt           required check state + deterministic local reproduction
s1-baseline-skipped-ids.txt     the 44 S1 skip IDs used as the comparison baseline
MANIFEST.sha256                 integrity manifest of every file above
```
