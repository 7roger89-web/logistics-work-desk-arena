# 00 — P2P_LAW_PREFLIGHT, checkpoint status, skill receipt, OE_GATE

TASK_ID: `LOGI-247-FINAL-20261031` · DESTINATION=ARENA · MODE=SAME_CHAT · REQUIRED_SKILLS=`qa`
Measured PR #248 HEAD: `9012ee01763df491ec4d8bda9836cc3dee060aac` (see `01-pr248-head-verification.txt`)

## 1. P2P_LAW_SOURCE

```
P2P_LAW_SOURCE=LOCAL_PORTABLE
```

Reasoning, in the operational order of `AGENTS.md` at the measured PR HEAD (`AGENTS.md` blob
`2bd3867d8036fc410f01444aa4874d697bdea0ea`, sha256 `7a766bcafa0dab06c4c943182b8ab4cd4efffe3741851486eac235761c631c1e`):

1. `CANONICAL_AUTHENTICATED` — **not used**. `7roger89-web/P2P-upgrade-github-1` was not reached in
   this session, so canonical was not claimed. No cross-repository `gh`/API probe was issued merely
   to manufacture a fallback (explicit prohibition in `AGENTS.md`).
2. `LOCAL_INSTALLED` — **not applicable**. `.p2p/system` at the PR HEAD carries only
   `p2p_capabilities/review_extension_activation.py`; there is no installed law projection.
3. `LOCAL_PORTABLE` — **VALID, used**. `.p2p/portable/P2P-OPERATIONS-NOTEBOOK.md`
   (blob `6835301e1e1dc149b4f6170c0680e2489e86110c`,
   sha256 `75d4d1d589b3bfd4ef70a12a93878664766f65734075fd14f398a76a9fddde1e`) header:

   ```
   P2P_PORTABLE_LAW_PROJECTION=YES
   SCHEMA=p2p-portable-law-projection/1
   CANONICAL_SOURCE=7roger89-web/P2P-upgrade-github-1@main:docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md
   SOURCE_CONTENT_SHA256=11ce33bb9c514d32ad3aec3eb7d8b40f0d0290b1dbe79eaa15751ef34668bd4b
   PACKAGE_VERSION=8.4.7-C-codex.74
   PROJECTION_DO_NOT_EDIT=YES
   CANONICAL_WINS_WHEN_REACHABLE=YES
   ```

   Provenance, source identity and the no-edit projection marker are all present, so portable wins
   over the inline capsule (steps 4/5 unused).

### LAW_CHECK

| Check | Result | Evidence |
|---|---|---|
| `AGENTS.md` read at PR HEAD (not from local main) | YES | blob `2bd3867…`, 12 extra sections vs main `cdce5ac…` |
| Portable projection carries `P2P_PORTABLE_LAW_PROJECTION=YES` + canonical provenance | YES | header above |
| Portable skill manifest integrity | YES — 53/53 managed files present, 53/53 sha256 match | `.p2p/portable/P2P-SKILL-PROJECTION.json` recomputed |
| Portable experience capsule integrity | YES — sha256 `9b10fafe…` equals `PORTABLE_EXPERIENCE_CONTENT_SHA256` | `.p2p/portable/P2P-EXPERIENCE-CAPSULE.json` |
| No cross-repo probe solely for fallback | YES — zero requests to the canonical repo | this transcript |
| `P2P_EVIDENCE_FIRST_VERIFICATION_V1` applied | YES — capsule used (canonical profile unreachable): claim ≠ evidence, test pass proves only the exercised boundary, truthful verdict, no second classifier, no ceremonial ceremony | this bundle |
| Executor self-report treated as acceptance | NO — independent review remains the next gate | `README.md` §4 |

## 2. Skill receipt (`p2p-skill-consumption-receipt/1`)

```
receipt_schema=p2p-skill-consumption-receipt/1
required_skills=qa
skill_id=qa
path=.agents/skills/qa/SKILL.md
sha256=a377e48cf5b3f8415208b40eac44ba3a6df6fd407215d01354fe079e09d2f2f2
measured_ref=9012ee01763df491ec4d8bda9836cc3dee060aac
read_before_substantive_work=YES
applied_rules=QA_NO_FIX | RUNTIME_AND_LOG_EVIDENCE_OVER_CLAIM | TESTS_ARE_SUPPORTING_EVIDENCE | BLOCKER_PROPAGATION | NO_UNVERIFIED_PASS
skill_check=MATCH (exact repo-local id 'qa' requested and resolved)
```

Application in this task: QA is a no-fix role — no product, test, fixture or spec file was modified;
findings are reported, and `Blocked`/`Unknown` is used instead of a pass wherever evidence is absent
(e.g. Cloud/OIDC, independent review). The skill's full-release-QA ceremony (visible Owner-PC Chrome,
Anvien sweep) is declared **outstanding** below rather than silently waived.

## 3. Checkpoint 00 / 05 / 06 at PR HEAD

Two artifacts can carry those numbers; both were checked instead of assuming one:

| Reading | At PR #248 HEAD `9012ee0` | Validity |
|---|---|---|
| `ops/arena-control/00-LUAT.md`, `05-TRANG-THAI.md`, `06-NHAT-KY.md` (Control Tower set) | **ABSENT** — `git ls-tree 9012ee0 ops/arena-control/` and `git ls-tree ba03ae7 ops/arena-control/` are both empty; the directory exists only on main `fd9b265` (introduced by PR #252 after this PR's base) | NOT VERIFIABLE at PR HEAD |
| `evidence/issue247/00-baseline-head-1144af5-40f.txt`, `05-clean-b-fresh-venv-no-pycache.txt`, `06-final-clean-1.txt` | PRESENT | **HISTORICAL ONLY** — bound to `1144af5`, `661fdfc`, `cf30b3b`. Under the task MUST NOT they are *not* admissible as pytest proof for `9012ee0` |

Consequence recorded, not worked around: the Control Tower checkpoint files are simply not part of
this PR's tree, so they were read from the session branch's base (`fd9b265`) for the process rules,
while **no historical `evidence/issue247/*` run log is used as HEAD proof**. `docs/NEXT.md` at the PR
HEAD (`20c9887` reconciliation) was read as the current mutable goal checkpoint.

## 4. OE_GATE — "Không bị over engineering chứ?"

- **SIMPLER_PATH** — A single worktree plus a second `venv` would have been enough to satisfy
  "two independent processes/environments". Two fully detached worktrees were still cheaper than the
  alternative of reasoning about cross-run contamination, and they cost 2 × ~0.9 s to create.
- **MATERIAL_PROGRESS** — Every step buys a decision: exit codes decide `FINAL_SUITE`, the two venv
  paths inside the SKIPPED summary prove the runs really were separate interpreters, the ID diff
  decides "no lost tests", and the REST check decides whether the SHA is the PR's.
- **NECESSITY** — Nothing was added beyond the acceptance list: no CI job, no new framework, no
  Docker, no mutation campaign, no third full suite. The one extra focused run (7 files, 1.6 s) exists
  only to turn the aggregated `SKIPPED [N]` lines into per-test IDs for an honest ID diff.
- **CORE_BEFORE_SUPPORT** — The core gate (two clean full suites on the exact HEAD) ran first and in
  isolation; contract-shape, evidence bundling and the PR comment came after the suites were green.
- **SMALLER_VERIFIABLE_SLICE** — The smallest slice that can prove the claim was chosen over a broad
  re-certification: S1–S3 browser flows were **not** re-run (no product/runner source changed after
  their review), only their presence and blob identity were re-checked (`05-s1-s2-s3-preservation.md`).

```
OE_VERDICT=DO_IT
reason=Two detached worktrees + two fresh venvs are the minimum that makes "two clean independent
full suites on one immutable SHA" falsifiable; every additional artifact either decides a verdict or
was dropped.
```

Known over-engineering risk that was deliberately **not** taken: re-running the 176-check Chromium S3
flow, creating a new CI workflow, or editing the PR body to force `contract-shape` green.
