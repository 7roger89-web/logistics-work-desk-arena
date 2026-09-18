---
name: frontend-design
description: "Design and implement context-fit frontend interfaces with deliberate art direction, accessible interaction, responsive behavior, complete states, and rendered verification. Use when creating or substantially reworking pages, components, product workspaces, dashboards, marketing sites, editorial surfaces, commerce flows, or justified immersive experiences."
license: Complete terms in LICENSE.txt
version: 2.0.0
---

# Frontend Design (P2P Wrapper over Curated Upstream)

This skill designs interfaces that are FIT FOR THEIR CONTEXT — users,
tasks, content, product category, and constraints — not interfaces that
all look loud, bold, or unforgettable.

## Relationship to p2p-uiux

- `p2p-uiux` remains PRIMARY for a concrete interface/UX outcome: product
  context, flows, navigation, Design System, accessibility baseline,
  evidence, and drift.
- This skill supplies the VISUAL-DIRECTION craft inside that outcome:
  design modes, visual thesis, hierarchy, typography, color, state
  completeness, and rendered verification.
- A trivial padding/color/spacing fix is a direct UIUX task and normally
  needs neither this skill's full workflow nor `p2p_aesthetica`.

## Activation Boundary

Use this skill for creative visual direction and interface design. Do NOT
apply one universal aesthetic (bold, maximalist, dark, hero-led, card
mosaic) to every surface. Operational dashboards, dense forms, admin
tools, elderly-first interfaces, and other context-sensitive products
follow the mode router below, not a house style.

Backend-only, data, or infrastructure work never loads this skill.

## Authoritative Design Workflow (Vendored Upstream)

The normative workflow is the verbatim upstream document:

- [`upstream-frontend-design-v2.md`](./upstream-frontend-design-v2.md) —
  PracticalSwan `frontend-design` v2 (context-fit modes, decision rubric,
  accessibility baseline, responsive/performance/state rules, component
  review rubric, verification protocol). Read it before designing.

Supporting upstream artifacts in this skill:

- [`references/accessibility-checklist.md`](./references/accessibility-checklist.md) —
  focused WCAG 2.2 AA checks; read for forms, dialogs, complex widgets,
  destructive actions, dense data, or accessibility reviews.
- [`scripts/contrast-checker.py`](./scripts/contrast-checker.py) —
  stdlib-only local contrast calculator (no install, no network).
- [`references/animejs.md`](./references/animejs.md) — existing P2P motion
  reference; specialist content, not a default.

Upstream provenance (upstream `SKILL.md` renamed to
`upstream-frontend-design-v2.md`; all other files byte-identical):

- Repository: `https://github.com/PracticalSwan/agent-skills.git`
- Observed commit: `ff6d12f61e8250dd1b988e101a482f6adc05c451`
- Upstream skill: `frontend-design` version `2.0`
- Rights: MIT AND Apache-2.0 (see `LICENSE.txt`,
  `LICENSE-APACHE-2.0.txt`, `LICENSE-GITHUB-MIT.txt`,
  `THIRD_PARTY_NOTICES.md`)

The upstream body's "Related Skills" links point at sibling skills in the
upstream monorepo. Inside P2P, use the local correspondences instead:
`frontend-code-review` (implementation review),
`react-best-practices` / `composition-patterns` (React engineering),
`baseline-ui` (deterministic UI guardrails), `p2p-uiux` (UX outcome),
`UI-animation-design` sub-skills (specialist motion only).

## Project Design-System Precedence

1. The target project's established design system, components, tokens,
   and brand contracts win over every default in this skill.
2. Reuse project components before creating new ones.
3. Never silently replace an approved project system; material changes to
   brand, navigation, tokens, hierarchy, or accessibility baseline need
   owner approval (see `p2p-uiux` Design System and Contract rules).

## Runtime Evidence Contract

A visual claim is not proven by source inspection, a static screenshot
alone, or an automated score. Follow the verification protocol in the
vendored upstream workflow (rendered checks at representative widths,
keyboard plus relevant pointer/touch input, honest limitation lists),
and the runtime evidence contract in `p2p-uiux`. Unverified visual
conclusions stay `NEEDS_EVIDENCE`.

## Anti-Patterns (Binding)

- Choosing a fashionable mode before understanding users, task, content,
  and constraints.
- Requiring heroes, cards, gradients, glass, dark themes, custom cursors,
  smooth scrolling, or 3D for "premium" quality.
- Approving fake data, incomplete states, inaccessible controls, broken
  examples, or unmeasured performance claims.
- Treating landing-page marketing direction as the default for
  operational, dense, or elderly-first products.
