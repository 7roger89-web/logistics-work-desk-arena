# Issue #247 — S1 immutable international-payment snapshot

SPEC_LOCK: https://github.com/7roger89-web/logistics-work-desk-arena/issues/247#issuecomment-6537951726

## Identity and delivery boundary

- Measured PR #248 HEAD before changes: `2941181d0f17701a7039d431262a0f35e27a848b`.
- Measured staging HEAD: `ba03ae7ac27f2020c761bf405e1aaaab80709c62` (branch `arena/ae5f9f47-logistics-work-desk-arena`).
- Execution branch: `arena/5a8ce272-logistics-work-desk-arena`. This Arena session is restricted to that branch and cannot push the existing PR head branch. The Owner chose bounded evidence on the session branch, with an explicit delivery blocker instead of creating another PR.
- The exact S1 candidate commit is the commit containing this directory. PR #248 remains on its old HEAD until an authorized executor transfers this commit. **S1 candidate behavior is not evidence that the current PR HEAD contains the repair.**
- No new PR, no merge, no Cloud/Atlas/Drive/production/main write. PR #250 was read only for comparison and was not merged.

## Reproduction before product source changed

The final challenge test file was frozen before editing `core/database.py`; its SHA-256 is in `environment.json`. The after-fix test file is byte-identical (`cmp`, exit 0). Existing tests were not deleted, skipped, deselected or weakened.

Command:

```
python -m pytest tests/test_intl_payment_comparator.py -q -p no:cacheprovider -o junit_family=xunit1 --junitxml=/home/user/s1-evidence/before.xml
```

Result: **3 failed, 48 passed, exit 1**. Full traceback: `before-fix.txt`.

1. `test_s1_failed_lookup_never_inserts[no-index]`: lookup raised `PyMongoError`; writer nevertheless returned True and persisted 1 snapshot + 1 audit.
2. `test_s1_failed_lookup_never_inserts[unique-index]`: same failed lookup also called insert and persisted 1 snapshot + 1 audit. The index does not excuse calling a write after a failed guard read.
3. `test_s1_duplicate_key_replay_ignores_driver_id`: a competing real save won between lookup and insert. The unique index rejected the second row, but the driver-added internal `_id` changed the attempted fingerprint; the same-payload replay returned False. Persisted state stayed 1 row + 1 audit.

Ordinary first save/replay/tamper and Viewer denial already passed with the canonical unique index both absent and present. No change was made to those behaviors, auth policy, Mongo identity, the shared fingerprint helper, or the global fixture.

An initial test draft incorrectly expected the caller's dictionary to gain `_id`; the writer deep-copies its input. That assumption was corrected before any product edit. The committed fail-before evidence uses the final frozen tests and a real competing write, not a mocked writer return.

## Bounded repair and cause

`source.diff` and `tests.diff` are the exact deltas from the measured PR HEAD. Product changes are confined to `save_contract_intl_snapshot`:

- A pre-insert lookup exception now publishes the error and returns False before any insert. An unreadable guard is not an empty ledger.
- In the DuplicateKeyError branch only, compare a copy of the attempted payload without driver-assigned `_id`. Financial fields remain in the fingerprint. The shared `_financial_fingerprint` behavior for other ledgers is unchanged.

Seven new parametrized cases exercise the real writer, real mongomock persistence and audit readback. Only handle/session resolution and the named lookup fault/interleaving are patched. The canonical `ensure_indexes()` creates the unique-index variant; no second index policy is introduced.

## Focused results and persisted state

- Exact `python -m pytest tests/test_intl_payment_comparator.py -q`: **51 passed, 0 skipped, exit 0** (`focused-final.txt`).
- Comparator + identity safety: **57 passed, 0 skipped, exit 0** (`security-focused.txt`).
- Machine-readable assertions/readback: `readback.json`.

| Case | Rows | Audit rows | Insert calls / result |
|---|---:|---:|---|
| First Sale save, index off/on | 1 | 1 | True |
| Same-ID replay, including stored `_id`, index off/on | 1 | 1 | True; full state unchanged |
| Tampered financial payload, index off/on | 1 | 1 | False; full state unchanged |
| Competing same-payload write then duplicate-key replay | 1 | 1 | 2 insert attempts: one wins, one conflicts; replay True |
| Failed pre-insert lookup, index off/on | 0 | 0 | 0; False |
| Viewer, index off/on | 0 | 0 | 0; False |

Each S1 test uses a fresh `test_logi_s1_<uuid>` mongomock database. Teardown drops it, checks absence, closes the client, and records `s1_test_db_cleanup=true`, including for the fail-before cases. No app database is used. No real Mongo/Atlas concurrency or durability claim is made.

## Full-suite comparison at the exact candidate HEAD

The pre-change full baseline was actually executed at PR HEAD `2941181d...`: **2352 passed, 44 skipped, 0 failed/error, 10 subtests passed, exit 0** (`baseline-full.txt`). Collection: 2396 tests; sorted-ID SHA-256 and all 44 skip IDs are in `baseline-collection.json.gz`.

To avoid changing HEAD after measuring it, the two independent clean full-suite transcripts and collection/skip comparison for the commit containing this evidence are published as inspectable comments on PR #248 and linked from its body. They bind the exact candidate SHA, commands, exit codes, counts, failure IDs, collection delta and skip-ID parity. This directory intentionally does not embed a self-referential commit SHA or claim those post-commit runs before they occurred.

## Remaining gates

- S1 delivery to PR #248 head: **BLOCKED** by the session branch restriction; independent review must inspect the candidate commit and an authorized executor must place it on the existing PR branch without opening a replacement PR.
- Independent S1 source review: pending; executor self-report is not acceptance.
- Real Chromium/Streamlit critical path, original #247 acceptance and independent final review: not performed in this assignment.
- Node 06 feature work: not performed. `npm ci` was used only to install the existing jsdom dependency needed by the unchanged Python suite.
- `contract-shape` is not functional proof and must not be made green by ticking unverified original-goal gates.
