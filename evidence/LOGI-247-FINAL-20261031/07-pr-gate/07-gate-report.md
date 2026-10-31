# 07 — PR #248 body gate closed (`contract-shape` = success)

TASK_ID `LOGI-247-FINAL-20261031` · PR HEAD `9012ee01763df491ec4d8bda9836cc3dee060aac` (unchanged)
No source, test, fixture or evidence inside the PR was modified. Only the PR body changed.

## 1. Authority for ticking the two boxes

| Box | Evidence cited in the body | Independently reviewed? |
|---|---|---|
| exact FINAL_HEAD two-run full suite | RUN A / RUN B raw stdout at commit `98f37fec…`, `GIT_HEAD=9012ee0…` in both environments, exit 0 / exit 0 | YES — review `6542747090` states it read those artifacts, exit files and ID sets, and re-parsed 2403/2403 collected IDs and the 44 skipped IDs |
| independent final-HEAD review | review comment `6542747090` | That comment **is** the review: `INDEPENDENT_REVIEW=PASS` naming `9012ee01763df491ec4d8bda9836cc3dee060aac` explicitly |

The review comment's own instruction was exactly this bookkeeping step: mark the two rows `[x]`
citing the A/B logs and the review, remove stale `NOT RUN` descriptions while preserving the real
OIDC/Cloud UNKNOWN, keep `FINAL_HEAD`, let `pull_request.edited` rerun, verify `contract-shape=PASS`,
keep the PR open. Nothing beyond that was changed.

## 2. Commands, exit codes, raw results

| # | Command | Exit | Note |
|---|---|---|---|
| 1 | `gh api repos/…/pulls/248 --jq .body` | 0 | body before, sha256 `74cd6e288c5dae4eed6604b56d89ebbfef0376c46448c9cb46d2584a97170aed`, 84 lines |
| 2 | `gh pr edit 248 --body-file …` | **1** | GraphQL failure: `Projects (classic) is being deprecated … (repository.pullRequest.projectCards)`; body verified **unchanged** afterwards, so nothing partial was applied |
| 3 | `gh api -X PATCH repos/…/pulls/248 --input patch.json` | **0** | REST fallback; `head=9012ee0…`, `state=open`, `mergeable_state=blocked`, `updated_at=11:41:25Z` |
| 4 | `gh api repos/…/pulls/248 --jq .body` (readback) | 0 | 0 unchecked / 8 checked; `FINAL_HEAD` exact |
| 5 | `gh api -X PATCH … --input patch2.json` | **0** | accuracy fix: the status line still said the check was pending after it had already passed; `updated_at=11:42:09Z` |
| 6 | `gh api …/commits/9012ee0…/check-runs` | 0 | latest run **success** |
| 7 | `gh api …/actions/jobs/<id>/logs` | 1 | blocked by the sandbox outbound allowlist (`productionresultssa3.blob.core.windows.net … EOF`); the check conclusion and per-step conclusions are authoritative and are stored as JSON instead |

Local dry-run of the workflow predicate on the exact body before each PATCH:
`PR_CONTRACT_SHAPE=PASS (structure + HEAD only)`, exit 0 — see `00-preflight.md` sibling evidence and
the reproduction script in `06-contract-shape.txt`.

## 3. GitHub Actions

| Run | Job | Started → completed | Conclusion | Steps |
|---|---|---|---|---|
| 41197894627 | 124527671598 | 11:41:30Z → 11:41:33Z | **success** | Set up job ✔ / Check task reference, acceptance evidence and final HEAD ✔ / Complete job ✔ |
| 41197947608 | 124527818627 | 11:42:14Z → 11:42:17Z | **success** | same three steps ✔ |
| 41189792585 | 124504024279 | earlier | failure (before the body fix) | — |
| 41189742090 | 124503880173 | earlier | failure (before the body fix) | — |

Trigger: `pull_request` / `edited` — confirming the workflow is re-evaluated on body edits.

## 4. Post-state

```
head            9012ee01763df491ec4d8bda9836cc3dee060aac   (identical before and after)
base            ba03ae7ac27f2020c761bf405e1aaaab80709c62
state           open          merged  false
mergeable       true          mergeable_state  clean
check           contract-shape = success (latest run 41197947608)
```

The PR was **not** merged, no checkbox was ticked without evidence, and Issue #247 remains OPEN for
Owner/Control Tower.
