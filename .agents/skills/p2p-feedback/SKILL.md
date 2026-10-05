---
name: p2p-feedback
description: >-
  Record structured P2P quality feedback and a concrete correction for future routing. Use
  when the user invokes $p2p-feedback or rates a P2P result as good, acceptable, or bad.
---

Read `../p2p/references/codex-adaptation.md` before applying any Claude-edition
mechanism. The matching section in `../p2p/references/modes.md` is the runtime
contract. Current host permissions and current verified facts take precedence.

# P2P Feedback

Record the rating, target workflow or role, concrete issue, desired correction,
and what should change next time. Treat legacy percentage bias updates as
historical heuristics, not probabilities. Persist locally only when requested.
