# Notes and decisions — 2026-08-29

## 2026-08-29 00:00 UTC+7 — LOG-TRADE01 re-anchor

- Authority: current user request plus canonical repository `origin/main`.
- Planning mode: append — no existing LOG-TRADE01 execution plan in this checkout.
- Decision: use `D:\Logistics_App_GitHub\.tmp\log-trade01-github-canonical` as the single task-scoped Git worktree because the owner checkout is mid-revert; do not mutate that checkout.
- Decision: create a small `core/trade_compliance` pure-Python domain module because canonical HEAD has no LOG-SKILL01 or trade skill/runtime abstraction.
- Boundary: no UI wiring, crawler, database, production access, push, deploy, or P2P core changes.
- Historical note: deleted Copy checkout evidence and its uncommitted candidate are not recovered; prior observations are guidance only and must be revalidated.

## 2026-08-29 19:12:11 UTC+7 — focused validation

- Authority: LOG-TRADE01 user contract; no LOG-SKILL01 or trade abstraction exists at fresh canonical HEAD.
- Evidence: focused unittest passed 16/16; in-memory compile passed for 9 Python files; `git diff --check` passed.
- Decision: keep `compileall` cache-write failure visible as an environment limitation (WinError 5) and rely on the non-writing compile check rather than altering/deleting cache files.
- Source revalidation: VTIP, Vietnam Customs, and the Government legal-document portal remain official-source registry entry points; registry remains discovery-only with no tariff/legal rates.

## 2026-08-29 19:32:40 UTC+7 — Supervisor closure

- Evidence: fresh canonical remote recheck remained `main` at `bddcf24e10285dbc82a52a2e3640bf0bf63a5a23`; focused unittest remained 16/16; in-memory compile remained 9/9.
- Decision: accept the bounded implementation as `PASS` for Owner review; keep live-source retrieval, UI wiring, country adapters, push, merge, deploy, and production use outside this tranche.
- Additional guard: tax arithmetic revalidates official source scope/effective date at calculation time; stale manually assembled snapshots fail closed.
