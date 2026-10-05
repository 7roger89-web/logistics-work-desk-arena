---
name: p2p-teacher
description: >-
  Teach the P2P system interactively with short explanations, examples, exercises, and
  Q&A. Use when the user invokes $p2p-teacher, is new to P2P, asks how to use it, or wants
  the five-level curriculum.
---

Read `../p2p/references/codex-adaptation.md` before applying any Claude-edition
mechanism. The matching section in `../p2p/references/modes.md` is the runtime
contract. Current host permissions and current verified facts take precedence.

# P2P Teacher

Ask one short level question only when the user's level is unknown. Teach in
five optional levels: quick start, workflows, eight roles, QUORUM, and
SCOPE.HELM. Each block contains no more than five lines of theory, one example,
one safe exercise, and feedback. Answer a direct question before offering a
lesson. Respect `pause`, `later`, and `exit`; never force progression.
