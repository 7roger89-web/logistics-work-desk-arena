---
name: frontend-dev-guidelines
description: Use when the user asks to build or change frontend code.
---

# Frontend Development Hub

Thin routing hub for frontend engineering. This file routes; it does not
impose a stack. Stack-specific knowledge lives in the project's own
sources and in the specialized skills below, loaded one at a time.

## First: Inspect the Target Project's Actual Stack

Before advising or writing code, read the target project:

- `package.json` (framework, React/Vue/Svelte version, router, UI
  library, query/data layer, test runner)
- configs (`vite.config.*`, `next.config.*`, `tsconfig.*`, tailwind/MUI
  theme, eslint/oxlint config)
- existing conventions (aliases, directory layout, component patterns,
  state/data-fetching idioms)

Preserve the project's architecture. NEVER impose a generic stack
(UI-kit version, router choice, specific aliases, fixed directories,
fixed Suspense/query rules, or named local components) on a project
that does not already use it.

## Authority Precedence (Binding)

```text
PROJECT_INSTALLED_VERSION_SPECIFIC_GUIDANCE
  > CENTRAL_GENERIC_LIBRARY_GUIDANCE
```

- Prefer package-local, version-aligned agent guidance shipped with the
  project's installed dependencies (for example TanStack Intent skills
  under `node_modules/<package>/skills/<skill>/SKILL.md`, discoverable
  via the project's installed `intent` CLI) over stale generic central
  API rules.
- Never centrally hardcode library APIs when installed package-local
  guidance can supply version-aligned instructions.
- Project-local framework/library authority always beats this hub's
  generic text.

## Progressive Disclosure: Load Only What Fits

Backend-only task: load NOTHING from the frontend surface.

| Task | Load |
|---|---|
| Plain React implementation / performance | `react-best-practices` (Vercel: 70 rules, 8 categories) |
| Component API / composition architecture | `composition-patterns` (Vercel: compound components, state, variants) |
| Code review / PR / production readiness | `frontend-code-review` (severity-ordered, framework-boundary aware) |
| Baseline usability / accessibility guardrails | `baseline-ui` (deterministic constraints) |
| Creative visual direction | `frontend-design` (context-fit modes) |
| Broad UI/UX outcome | `p2p-uiux` remains primary |
| Motion audit / review / opportunity sweep | `UI-animation-design` sub-skills (specialist only, never default) |
| React diagnostics scan | `react-doctor` (pinned external tool, optional) |
| Design-quality critique vocabulary | `ui.design_quality` capability adapter when available |

Do not make every UI task load every frontend skill. One primary route;
add a secondary skill only when it materially changes the deliverable.

## Engineering Invariants

1. Inspect first; assume nothing about framework, router, styling, or
   data layer.
2. Reuse project components, tokens, aliases, and idioms; do not fork
   parallel patterns.
3. Keep framework mechanics in the skill that owns them; keep examples
   short, valid, and materially useful.
4. State completeness: loading, empty, error, disabled, permission, and
   stale states are product behavior, not polish.
5. Accessibility baseline follows `frontend-design` / `baseline-ui`;
   never claim conformance from a recommendation alone.
6. Runtime visual claims need rendered evidence per the `p2p-uiux`
   runtime evidence contract — never a source-only visual PASS.

## Related Skills

- `frontend-design`, `frontend-code-review`, `react-best-practices`,
  `composition-patterns`, `baseline-ui`, `react-doctor`, `p2p-uiux`
