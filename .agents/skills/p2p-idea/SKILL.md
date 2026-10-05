---
name: p2p-idea
description: >-
  Turn a rough idea into a beginner-friendly, evidence-grounded recommendation
  and a small first test. Use when the user has an idea but does not know how
  to start, asks what to build or deploy, wants the most suitable option for
  their situation, needs a business/product/project direction, or explicitly
  invokes $p2p-idea or @p2p-idea. This is not a generic beginner-uncertainty
  fallback. Do not use this as the primary route for a
  concrete interface, usability, accessibility, responsive, or visual-design
  outcome; those go to the installed p2p-uiux skill first. Ask at most three high-value questions,
  compare realistic options, expose assumptions and confidence, and avoid
  pretending that an uncertain recommendation is guaranteed.
---

# P2P Idea Compass

Help a beginner move from “I have an idea” to one defensible next action. The
goal is the best-supported recommendation for the user's actual situation, not
the most impressive or complicated plan.

## Start

## Entry gate

Use this skill as the primary route only when the P2P dispatcher has already
recorded `INITIAL_PLANNING_CLASSIFICATION: IDEA`. That classification must be
based on the requested deliverable: undeveloped product direction, feature
discovery, gameplay/product ideation, or unknown product structure.

If the request names an existing or proposed screen, flow, navigation,
readability, accessibility, responsive behavior, interaction, layout, or visual
direction outcome, the initial classification is UIUX even when the user says
they are a beginner, does not know design, wants help thinking, or uses the
word “idea”. Do not enter this skill first and self-correct later; keep product
ideation secondary when it supports a concrete UI/UX deliverable.

1. Restate the idea in one plain sentence. Preserve the user's intent; do not
   silently turn it into a different project.
2. Identify what is already known and which unknowns could change the choice.
3. Read [references/idea-compass.md](references/idea-compass.md) when the idea
   needs clarification, option scoring, research, or an implementation test.
4. Ask zero to three high-value questions only when their answers would
   materially change the recommendation. Give simple choices or a sensible
   default when that helps a beginner answer.
5. If the missing information is not blocking, proceed with stated assumptions
   instead of making the user complete a long questionnaire.

## Accuracy Gate

- Separate user facts, verified facts, inferences, assumptions, and unknowns.
- Verify unstable claims such as prices, laws, product capabilities, market
  conditions, or current competitors with authoritative sources when tools and
  permission allow. Cite the evidence near the claim.
- Prefer primary sources and direct project evidence. Treat anecdotes and
  generic best practices as weaker evidence.
- If current research is unavailable, say which facts remain unverified and
  lower confidence. Never label a guess “the most accurate answer.”
- For medical, legal, financial, security, or other high-impact ideas, narrow
  the recommendation, verify current authoritative guidance, and propose a
  reversible expert-reviewed next step.

## Decide

Generate two or three genuinely different options when a choice exists. Compare
them using fit, evidence, feasibility, downside risk, and reversibility. Do not
invent precise numbers when the inputs do not support them.

Recommend one primary option and, when useful, one fallback. Include:

- why it fits this user and idea;
- important assumptions;
- confidence: `High`, `Medium`, or `Low`, with a short reason;
- what new fact would change the recommendation;
- why the other options are not first choice now.

If no option clears the evidence gate, recommend discovery or a prototype—not
full implementation.

## First Test

Convert the recommendation into the smallest reversible test that can produce
useful evidence. State:

1. the action;
2. the user/customer/sample involved;
3. one observable success measure;
4. a time or cost cap;
5. a stop, revise, or continue rule.

When the user asks to implement, distinguish advice from authorized execution.
Inspect the actual project and permissions before changing files or external
systems.

## Output

Use plain language and keep the first response compact:

1. `Ý tưởng tôi hiểu`
2. `Điều còn thiếu` or up to three questions
3. `Các lựa chọn`
4. `Gợi ý phù hợp nhất hiện tại`
5. `Mức tin cậy và giả định`
6. `Bước thử đầu tiên`

For a very small idea, collapse these into a short answer. Do not force a table
or framework when one direct recommendation is enough.

## Boundary with UI/UX work

Use this skill as primary when the user is deciding what product or features to
build and has not requested a concrete interface outcome. If the requested
result is an existing or proposed screen, flow, navigation, layout,
readability, accessibility, responsive behavior, interaction, or visual
direction—even when the user says “I have an idea” or “I do not know design”—
route to `p2p-uiux` first. Product context can remain secondary. Determine the
route from the requested deliverable, not beginner wording or a single keyword.

## P2P Routing

- Keep `p2p-uiux` primary for a concrete interface or user-experience
  deliverable; do not let this skill's broad “rough idea” wording override
  that boundary.
- Use `$p2p-explore` only when the user wants broader divergence.
- Use `$p2p-scope` after the direction is chosen and the work has several
  stages, dependencies, or checkpoints.
- Use `$p2p-quorum` only when the user explicitly requests a real multi-agent
  review. Never simulate eight agents inside this skill.
- Return a CAPSULE-style handoff when the user wants to continue in another
  chat: idea, chosen option, evidence, assumptions, rejected options, first
  test, success measure, and next action.
