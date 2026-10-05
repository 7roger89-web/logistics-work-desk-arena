---
name: p2p-atlas
description: >-
  Show or update the P2P ATLAS task map with goal, progress, current and next steps,
  blockers, and success checks. Use when the user invokes $p2p-atlas or asks to track a
  multi-step P2P task.
---

Read `../p2p/references/codex-adaptation.md` before applying any Claude-edition
mechanism. The matching section in `../p2p/references/modes.md` is the runtime
contract. Current host permissions and current verified facts take precedence.

# P2P ATLAS

Maintain a compact task map containing `GOAL`, `PROGRESS`, `CURRENT`, `NEXT`,
`BLOCKERS`, and `SUCCESS CHECKS`. Update it after a step completes. Persist only
when requested; in a local project, use the main P2P state helper under
`../p2p/scripts/p2p_state.py`. Never invent completion or hide a blocker.
