---
name: p2p-karpathy
description: >-
  Apply P2P Karpathy Coding Mode for minimal, surgical, verified code changes. Use when
  the user invokes $p2p-karpathy or explicitly requests the smallest possible
  implementation with strict scope control.
---

Read `../p2p/references/codex-adaptation.md` before applying any Claude-edition
mechanism. The matching section in `../p2p/references/modes.md` is the runtime
contract. Current host permissions and current verified facts take precedence.

# P2P Karpathy Coding Mode

Before editing, state only material assumptions, ambiguity, scope, and the
smallest approach. Preserve unrelated code and user changes. Make the minimum
defensible patch, run focused checks, and report what changed and what was
intentionally untouched. Do not suppress necessary safety warnings or
user-requested explanations for the sake of terseness.
