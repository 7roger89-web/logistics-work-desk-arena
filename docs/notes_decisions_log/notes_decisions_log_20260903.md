# Notes and Decisions — 2026-09-03

## LOGISTICS_DEEPL_TRANSLATION_V1

- P0 bound clean implementation worktree
  `feature/logistics-deepl-translation-v1` to fresh `origin/main` at PR #8
  merge `c1c9468`; the original detached checkout and untracked Owner work
  remain untouched.
- P1 service checkpoint: requests-based DeepL text client, endpoint inference,
  bounded retry/failover, explicit usage rows, list configuration, and
  key-free errors/logs are implemented. Focused service/config tests are
  `14/14 PASS` with fake keys only.
- Real DeepL smoke is intentionally not run until the Owner adds keys to the
  branch-local `.streamlit/secrets.toml`; no key value is recorded here.
- P2 route/UI checkpoint: `translation` is available to sale/support only;
  support mounted AppTest and the full focused family are `50/50 PASS`.
- Candidate is local-only and ready for Owner to add branch-local DeepL keys;
  no live API call or preview was started because the clean worktree has zero
  configured keys.
- Coder handoff report: `reports/coder/rp_coder_260903_175900_by_gpt-5-codex_logistics-deepl-translation-v1.md`.
- Exact Owner next action: `Thêm API DeepL vào .streamlit/secrets.toml local. Không gửi key vào chat/GitHub.`
- Supervisor reviewed the exact local candidate and returned PASS for the
  local/mock claim. Live API smoke and browser preview remain intentionally
  unrun until the Owner supplies local keys.
- Push, PR, merge, deployment, and production DB mutation remain forbidden for
  this task.
