# Upstream Notices — frontend-design (vendored PracticalSwan unit)

The `frontend-design` skill is a P2P wrapper (see `SKILL.md`) over a verbatim
vendored upstream unit completed under `P2P_FRONTEND_UPSTREAM_INTAKE_01`. No
vendored upstream byte was modified; `SKILL.md`, `references/animejs.md`
(pre-existing local file), and this notices file are the P2P-side files.

- Upstream repository: `https://github.com/PracticalSwan/agent-skills`
- Observed commit: `ff6d12f61e8250dd1b988e101a482f6adc05c451`
- Upstream path: `frontend-design/`
- Rights: MIT AND Apache-2.0. Upstream ships its own rights files, all
  vendored verbatim: `LICENSE.txt` (MIT), `LICENSE-APACHE-2.0.txt`,
  `LICENSE-GITHUB-MIT.txt`, and `THIRD_PARTY_NOTICES.md` (all four blob
  SHAs match upstream exactly).
- Taken verbatim: upstream `SKILL.md` (vendored as
  `upstream-frontend-design-v2.md`; renamed so the P2P wrapper keeps the
  canonical `SKILL.md` entrypoint — byte-identical, blob SHA verified),
  `references/accessibility-checklist.md`,
  `scripts/contrast-checker.py` (blob SHAs verified; the checker was
  smoke-tested: `12.92:1` AAA pass on the sample pair).
- Not taken: `CHANGELOG.md` (version history stays upstream),
  `agents/openai.yaml` (provider-specific binding; P2P core is
  provider-neutral), and every other top-level skill in the upstream
  monorepo (out of scope for this frontend intake).

Verification: every vendored-file blob SHA was compared against the upstream
commit and matches. See the intake report
`docs/p2p-development/research/P2P-FRONTEND-UPSTREAM-INTAKE-01.md`.
