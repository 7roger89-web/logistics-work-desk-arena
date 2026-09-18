# Upstream Notices — react-best-practices

This P2P skill directory is a verbatim vendoring completed under
`P2P_FRONTEND_UPSTREAM_INTAKE_01`. No upstream byte in this directory was
modified; this notices file is the only P2P-added file.

- Upstream repository: `https://github.com/vercel-labs/agent-skills`
- Observed commit: `063bee94c3f4df8453406c830b0a7df0f2860278`
- Upstream path: `skills/react-best-practices/`
- Rights: MIT, per the vendored `SKILL.md` frontmatter
  (`license: MIT`, `author: vercel`). The upstream repository carries no
  root LICENSE file at the observed commit.
- Taken verbatim: `SKILL.md`, `AGENTS.md`, `metadata.json`, `rules/*.md`
  (72 rule files; `rules/` subtree hash matches upstream exactly).
- Not taken: upstream `README.md` (stays upstream; `SKILL.md` is the
  P2P entrypoint), every other skill under upstream `skills/`
  (`composition-patterns` is vendored separately as its own P2P skill;
  `deploy-to-vercel`, `react-native-skills`, `react-view-transitions`,
  `vercel-cli-with-tokens`, `vercel-optimize`, `web-design-guidelines`,
  `writing-guidelines` and the `*.zip` bundles were not selected).

Verification: `SKILL.md` / `AGENTS.md` / `metadata.json` blob SHAs and the
full `rules/` subtree SHA were compared against the upstream commit and
match. See the intake report
`docs/p2p-development/research/P2P-FRONTEND-UPSTREAM-INTAKE-01.md`.
