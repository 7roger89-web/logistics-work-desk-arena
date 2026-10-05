---
name: p2p-metrics
description: >-
  Summarize evidence-based P2P session metrics, corrections, blockers, and user ratings.
  Use when the user invokes $p2p-metrics or asks for a P2P progress and quality dashboard.
---

Read `../p2p/references/codex-adaptation.md` before applying any Claude-edition
mechanism. The matching section in `../p2p/references/modes.md` is the runtime
contract. Current host permissions and current verified facts take precedence.

# P2P Metrics

Report only observed counts and trends: tasks, completed steps, corrections,
ratings, blockers, and rework. Explain the denominator for any rate. Do not
invent measurements or present the legacy efficiency formula as calibrated
model quality.

Session metrics are not an eval. When the user asks whether P2P actually improves
the project, invoke `$p2p-eval` and compare paired representative tasks. For RAG,
report retrieval and grounding metrics separately from answer quality.
