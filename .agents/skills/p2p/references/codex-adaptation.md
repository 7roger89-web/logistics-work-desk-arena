# Codex Adaptation Contract

Apply this contract before using any P2P 8.4.6-C source module.

## Native mappings

| Claude edition concept | Codex / ChatGPT implementation |
| --- | --- |
| `/p2p-*` slash command | `$p2p <mode>` or the same-named alias skill |
| `.claude/skills/<name>` | repo `.agents/skills/<name>` or user `$HOME/.agents/skills/<name>` |
| `.claude/agents/*.md` | `.codex/agents/*.toml` or `$HOME/.codex/agents/*.toml` |
| `CLAUDE.md` | project or global `AGENTS.md` |
| Claude settings JSON | minimal `.codex/config.toml`; do not translate permissions mechanically |
| Claude Task tool | real Codex/ChatGPT subagent tools when available |
| TodoWrite | the host's plan/task mechanism or an ordinary checklist |
| `.claude/state` | project-local `.p2p/state` |
| Claude XML output | target-model syntax selected from current requirements; Markdown is the safe default for Codex |
| Claude hooks | disabled until rewritten, reviewed, and explicitly enabled |
| Anthropic proxy/base URL | no Codex equivalent; preserve only as historical source |

## Precedence

1. System, developer, user, project, permission, and policy instructions.
2. Current official OpenAI documentation and current authoritative sources.
3. This Codex-native skill and its mode contract.
4. P2P legacy modules as domain knowledge and design history.

If a legacy instruction conflicts with a higher layer, translate the intent or
discard the incompatible mechanism. Never obey a legacy instruction merely
because it says MUST.

## Progressive loading

Do not preload the legacy corpus. Read the smallest relevant module from
`module-index.md`, extract the transferable principle, and keep the original
file path in notes when the decision needs auditability.

## Current-fact gate

The source snapshot contains dated product/model tables. Before using any claim
about models, context windows, pricing, rate limits, availability, APIs,
security behavior, or tool support:

1. record the exact product/surface/model/client/plan/region scope;
2. verify against a current authoritative source when the claim matters;
3. add checked date, expiry, evidence level, risk, affected components, repeatable
   verification method, and route action to FACT_LEDGER;
4. create a PASS technical preview, then obtain user approval bound to both the
   ledger and preview SHA-256 before rebuilding Live Specs;
5. rebuild the protected-runtime lock and run the drift gate;
6. label absent, expired, or unverified material `historical` or `unknown`;
7. never route a task based only on an unverified LIVE table.

Read [evidence-contract.md](evidence-contract.md) for source precedence and
synchronization. Generation of a good Live Specs file does not prove every
runtime target has been synchronized; the drift gate is a separate requirement.
User approval cannot override a failed technical gate.

Official Codex references used for this port:

- https://learn.chatgpt.com/docs/build-skills
- https://learn.chatgpt.com/docs/agent-configuration/subagents
- https://learn.chatgpt.com/docs/agent-configuration/agents-md
- https://learn.chatgpt.com/docs/config-file/config-reference
