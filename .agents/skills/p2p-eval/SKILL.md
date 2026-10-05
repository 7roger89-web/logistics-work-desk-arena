---
name: p2p-eval
description: >-
  Create, run, validate, or summarize a project-specific P2P evaluation suite that compares
  the same real tasks with and without P2P. Use when the user invokes $p2p-eval, asks whether
  P2P improves their project, wants regression tests for prompts/workflows, or needs retrieval
  quality checks.
---

# P2P Project Eval

Measure P2P on representative tasks from this project. Do not substitute a public benchmark or
another project's scores.

## Workflow

1. Select at least five frequent, consequential, failure-prone, boundary, and regression tasks.
   Freeze their input fixtures, remove secrets, and record each fixture SHA-256.
2. For each case, define observable checks before running either variant. Include correctness,
   format, safety, project conventions, and cost/time only when those values are actually recorded.
3. Run at least two isolated baseline trials and two isolated P2P trials per case with the same
   input, model, surface, environment, and tool access. Do not carry memory or results between
   trials. Randomize order when practical.
4. Record model, surface, environment ID, date, score, unexpected writes, evidence path, and
   evidence SHA-256 for every trial.
5. Compare paired case means, pass rate, per-case regressions, and score spread. Report
   uncertainty; never generalize beyond the sampled project tasks.
6. For RAG cases, also use `../p2p/references/rag-safety.md` and record recall at k, grounding
   rate, citation verifiability, and injection resistance. Hash the index snapshot/manifest and
   every query evidence file; a path without its matching SHA-256 is not release evidence.

Use the installed helper when present:

```text
python .p2p/system/scripts/p2p_eval.py init --project .
python .p2p/system/scripts/p2p_eval.py design --project . --goal-contract .p2p/state/goal-contract.json
python .p2p/system/scripts/p2p_eval.py validate --suite .p2p/evals/suite.json
python .p2p/system/scripts/p2p_eval.py summary --suite .p2p/evals/suite.json
python .p2p/system/scripts/p2p_eval.py gate --suite .p2p/evals/suite.json
```

In the unpacked portable package, use `scripts/p2p_eval.py` instead. `design`
derives five small project-specific cases from the Goal Contract and project
markers. It creates only a missing suite; a valid existing suite returns
`REUSED` and is not regenerated. Initialization never overwrites an existing
suite.

## Guardrails

- Do not use hidden chain-of-thought as eval evidence.
- Keep test fixtures separate from the prompt or skill being evaluated when leakage would make
  the result easier.
- A model or prompt update must rerun affected cases through the drift gate before release.
- Fewer representative cases with clear graders are stronger than many vague synthetic cases.
- Schema v1 suites are not release-ready. Use `migrate`, then reclassify cases, hash fixtures,
  rerun trials, and hash evidence before running the gate.
- A user approval cannot override a failed eval gate.
