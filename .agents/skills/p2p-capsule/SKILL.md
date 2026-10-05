---
name: p2p-capsule
description: >-
  Create or restore a concise P2P CAPSULE so another Codex or ChatGPT chat can continue
  the work. Use when the user invokes $p2p-capsule, asks to save context, hand off work,
  or resume from a prior capsule.
---

Read `../p2p/references/codex-adaptation.md` before applying any Claude-edition
mechanism. The matching section in `../p2p/references/modes.md` is the runtime
contract. Current host permissions and current verified facts take precedence.

# P2P CAPSULE profiles

Choose one profile before saving:

- `task`: objective, progress, decisions, constraints, verified evidence,
  artifacts, blockers, and one next action;
- `brainstorm`: original seed, promising options, valuable wording/voice,
  rejected options with reasons, unresolved tensions, and next experiment;
- `research`: question, source/claim IDs, confirmed facts, inferences, disputes,
  unknowns, retrieval gaps, and next query;
- `incident`: impact, timeline, current state, evidence, hypotheses clearly marked
  as hypotheses, actions/owners, rollback state, and next checkpoint.

Exclude hidden reasoning, raw logs, credentials, and unnecessary personal data.
Return Markdown in hosted chat; save under `.p2p/state/capsules/` only when local
persistence is requested. The normal project workflow may persist a compact
task capsule automatically; it must reference the Goal Contract, project
status, eval, governance, trusted-evidence, report, and Execution Ledger paths
instead of duplicating their contents. For a Goal, include the eligibility
class, mandatory and already-PASS criteria, reusable evidence, current
bottleneck, work type, active lane, failed approaches, OUT-OF-SCOPE/BACKLOG,
approval state, and terminal status. Include schema/profile/version so a later
update can migrate the capsule instead of guessing its shape.
