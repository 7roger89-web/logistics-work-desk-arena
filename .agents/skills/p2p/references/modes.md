# P2P Modes

Use only the section matching the requested mode.

## idea

Invoke `$p2p-idea` with the user's raw idea and stated constraints. Preserve the
user's wording and experience level. The result must expose assumptions,
confidence, and a small evidence-producing test; it must not promise a
guaranteed “best” answer.

## prompt / dispatcher

Classify intent and tier, build the nine-part task contract, then either execute
the task or return a ready-to-use prompt. If the target model is not known and
syntax materially matters, ask one short question. Otherwise default to clear
Markdown and state the assumption.

## quorum

Invoke `$p2p-quorum`. Full mode requires eight distinct successful subagent
threads. Never write eight simulated viewpoints in the parent response.

## debug

Reproduce or restate the failure, classify it, locate the smallest likely cause,
patch only the failed contract or step, and verify against the original success
condition. Preserve working parts. Historical Type A–P and G1–G20 labels are `HISTORICAL_ONLY: taxonomy, not runtime facts.`
Diagnostic labels are not substitutes for current evidence.

## scope

Create an ATLAS with goal, atomic steps, current step, next step, success checks,
dependencies, blockers, and stop conditions. Ask for approval only when a
material choice or permission boundary requires it. Update ATLAS after each
completed step. Save state only when the user requests persistence.

## explore

Keep generation divergent before convergence. Mark tentative hypotheses,
include at least one unconventional option when useful, then rank options by
fit, evidence, cost, risk, and reversibility. Exit exploration before execution.

## atlas

Show or update: `GOAL`, `PROGRESS`, `CURRENT`, `NEXT`, `BLOCKERS`, and
`SUCCESS CHECKS`. For local persistence, use `scripts/p2p_state.py atlas ...`.

## capsule

Save only what another chat needs: project, objective, progress, key decisions,
constraints, verified sources, unresolved questions, next action, and artifact
paths. Do not copy hidden reasoning or raw logs. Use Markdown in hosted chat or
`scripts/p2p_state.py capsule ...` in a local project. Select `task` for delivery
work, `brainstorm` to preserve candidate wording and tensions, `research` for
claims/sources/unknowns, or `incident` for timeline, impact, hypotheses, actions,
and rollback state.

## metrics

Report counts and trends only from available evidence: tasks, completed steps,
corrections, user ratings, blockers, and rework. Do not invent precision or
claim that a heuristic efficiency score measures model quality.

## eval

Invoke `$p2p-eval`. Build cases from real project work, freeze fixtures, define
graders before running, isolate baseline and P2P variants, and record model,
surface, date, permissions, evidence, score, cost, and latency only when observed.
Run affected cases after prompt, model, retrieval, skill, agent, or Live Specs
changes. Do not generalize a project result into a universal P2P benchmark.

## chain

Parse only recognized roles: IRIS, TECTON, AXIOM, VECTOR, DATOS, ANON,
ARCHITECTON, HELIOS. Use a distinct real subagent thread per role when the host
supports it and delegation was explicitly requested. Pass distilled outputs,
not hidden reasoning. If real agents are unavailable, stop or ask whether the
user wants a single-agent analysis; do not silently simulate the chain.

## feedback

Record the user's rating, target workflow/agent, concrete issue, correction, and
what should change next time. Treat percentage biases from the Claude edition
as historical heuristics, not calibrated probabilities.

## karpathy

Before code, state only material assumptions, ambiguity, scope, and the smallest
approach. Make surgical edits, preserve unrelated code, run focused checks, and
finish with what changed and what was intentionally untouched. Do not suppress
necessary explanations, safety warnings, or user-requested comments merely to
be terse.

## teacher

Ask one level question if needed, then teach in short theory/example/exercise
blocks. Levels: quick start, workflows, agents, QUORUM, and SCOPE.HELM. Never
force progression. Answer direct questions directly before offering a lesson.

## download

Require an explicit URL or release. Fetch only with an available approved tool.
Record URL, retrieval date, hash when bytes are available, and verification
status. Store the new material beside—not over—the historical snapshot. Do not
promote it to runtime until reviewed.
Add verified claims to FACT_LEDGER, create the hash-bound technical preview,
obtain the required promotion approval, build Live Specs, run affected project
evals, then pass the drift gate. Keep a rollback artifact and obtain a second,
candidate-bound approval before release; inventory alone authorizes neither
promotion nor release.

## pxpipe

Treat PXPIPE as disabled experimental source. Its Anthropic token formula,
reader gate, proxy settings, and model claims are not native Codex behavior.
Allow offline inspection or measurement only after dependency and security
review; never send sensitive text through an untrusted proxy or replace text
handoffs with images by default.

## compatibility prefixes

- `Q:` → `quorum`; the prefix itself is explicit authorization to delegate.
- `AUTO:` → quality-first dispatcher; still respect permissions, evidence, and
  proportional cost.
- `MANUAL:` → expose material trade-offs and ask the user to choose.
- `MAX:` → comprehensive answer with evidence, assumptions, validation, and
  visible metrics; never reveal private reasoning or raw hidden logs.
- `full ui menu` → show the native compact menu plus this prefix mapping. Do not
  reproduce a 42-item wall unless the user specifically asks for the historical
  menu.

## direct role prefixes

Recognize `T:`/`@TECTON:`, `I:`/`@IRIS:`, `A:`/`@ANON:`, `@AXIOM:`,
`@VECTOR:`, `@DATOS:`, `@ARCHITECTON:`, and `@HELIOS:`. A direct prefix is an
explicit request for one real named custom-agent thread. If the profile or
subagent runtime is unavailable, report that boundary instead of role-playing
the agent in the parent thread.
