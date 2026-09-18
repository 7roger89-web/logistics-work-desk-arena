---
name: react-doctor
description: Use when asked to scan, triage, or clean up React diagnostics with the external React Doctor CLI. Pinned optional adapter; never blocks frontend work when unavailable.
version: 1.0.0
---

# React Doctor (Pinned External-Tool Adapter)

React Doctor is an EXTERNAL_TOOL, not P2P authority. This skill is a thin
pinned boundary over the upstream CLI. It does not reimplement, install,
wrap, or daemonize React Doctor.

## Upstream Identity (Observed, Pinned)

- Repository: `https://github.com/millionco/react-doctor.git`
- Observed commit: `499a0208fca5c0422b713bdedf2b83fcc8e29d20`
- Pinned CLI version: `react-doctor@0.9.14` (verified published on npm;
  `rules list` enumerates 906 rule entries at this version)
- Runtime: Node `^20.19.0 || >=22.13.0` (per upstream `package.json` engines)
- Engine: oxlint-based deterministic lint workers plus optional checks
  (supply-chain via Socket.dev, reduced-motion, security scan)

## Canonical Invocation (Pinned)

```bash
npx -y react-doctor@0.9.14 --verbose --scope changed
npx -y react-doctor@0.9.14 --verbose
npx -y react-doctor@0.9.14 --json --json-out <path> --verbose [paths...]
npx -y react-doctor@0.9.14 rules explain <rule>
```

## Prohibited Patterns

- NEVER use `react-doctor@latest` as canonical P2P behavior. `@latest` is a
  moving target; the pin above is the only reproducible invocation.
- NEVER fetch the upstream remote triage playbook at runtime (full URL is
  recorded in the intake report evidence section, not here). It is a
  moving remote prompt dependency; P2P behavior must not depend on it.
- NEVER auto-install or auto-run React Doctor against unrelated projects.
  Invoke only for an applicable React project and only when the task asks
  for a scan, triage, cleanup, or diagnostics review.

## Applicability Gate

- React projects only. A non-React task must not invoke this tool.
- The JSON report carries `reactDetected`; when it is false, stop and say
  so instead of reporting a vacuous clean bill.
- Backend-only work never loads this skill.

## Reading the Report Honestly (Schema v3)

`--json` emits the versioned `JsonReport` wire format. Branch on
`schemaVersion` (observed: `3`).

- `diagnostics[]`: each finding carries `plugin`, `rule`, `category`,
  `severity`, `normalizedFilePath`, and source span. Empty array proves
  nothing by itself.
- `projects[].complete`: true ONLY when every planned lint file completed
  and no check failed. `complete: false` plus `skippedCheckReasons` means
  a PARTIAL run (observed cause in constrained sandboxes: the oxlint
  worker killed by SIGABRT/OOM). NEVER claim clean from a partial run.
- `projects[].analyzedFileCount` / `analyzedFiles`: the coverage proof.
  Zero analyzed files is not a clean bill.
- `summary.score`: the 0-100 health score is computed by a REMOTE score
  API. Offline or unreachable API yields `score: null` with
  `Score API unreachable`. NEVER treat `score: null` as pass or fail;
  record `SCORE_UNAVAILABLE` with the reason.
- `mode`: `full`, `diff`, `staged`, or `baseline`. Scope every claim to
  the mode actually run.

What React Doctor proves: static deterministic diagnostics over the files
it actually analyzed, at the pinned version, in the mode run. It does NOT
prove visual correctness, rendered behavior, accessibility conformance, or
runtime UX quality. Runtime visual claims still need the p2p-uiux runtime
evidence contract, not this report.

## Unavailable-Tool Behavior (Fail Honest, Never Block)

If the CLI cannot run (no Node, no network for npx, OOM worker, license
notice, or any other failure):

1. Record `REACT_DOCTOR_UNAVAILABLE` with the exact reason.
2. Continue the frontend work with the local skills
   (`frontend-development` hub, `react-best-practices`,
   `composition-patterns`, `frontend-code-review`, `baseline-ui`).
3. NEVER convert unavailability into PASS, and NEVER let it disable core
   frontend work.

## Observed License Notice (Disclosure, Not a Filter)

Under agent/sandbox environments the CLI prints:

```text
react-doctor detected use in an AI or ML pipeline. This use requires
written permission under the react-doctor license - contact
founders@million.dev to request access.
```

Per task license policy (`DO_NOT_USE_AS_ADOPTION_FILTER`), this notice is
recorded as observed runtime behavior. It does not select or reject the
tool; local availability plus the applicability gate above decides use.

## Rule Tuning (Narrowest Control)

```bash
npx -y react-doctor@0.9.14 rules list
npx -y react-doctor@0.9.14 rules explain <rule>
npx -y react-doctor@0.9.14 rules disable|enable|set|category|ignore-tag ...
```

Tuning edits the target project's `doctor.config.*` (or
`package.json#reactDoctor`) in place. Prefer the narrowest control that
matches the user's intent; never disable whole categories casually.
