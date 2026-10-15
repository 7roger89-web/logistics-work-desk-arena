# LOGI-199 G1 — Shared Visual System (Mimo–Sonnet Family)

Scope: Shared visual primitives and shell (`component/src/components/Layout.tsx`, `component/src/components/ui.tsx`, `component/src/index.css`, `component/src/shell.css`) harmonized to the Mimo–Sonnet family:
- Ink: `#10263C`, Brand Navy: `#123A5E`, Maritime Blue: `#1D6FA8`, App Background: `#EDF1F5`, Surface: `#FFFFFF` / `#F8FAFC`, Border: `#D6DEE7`.
- Typography: `Be Vietnam Pro` (400–800) and `IBM Plex Mono` (400–700) locally bundled and verified `loaded` at runtime; all visible text `>= 12px`.
- Semantic status badges (`ToneBadge`, `StatusDot`, `AttentionNow`): `#DCEDE4/#22614A` (evidenced), `#DCEBFA/#154C79` (active), `#FBEBD3/#8A5209` (waiting), `#F6DFDB/#8E2F22` (problem/blocking), `#E7ECF2/#5B6875` (upcoming/neutral).

Proven on real app data at `1440×900` (`desktop-01-home.png`..`desktop-04-receivables.png`) and `390×844` (`mobile-01-home.png`..`mobile-04-receivables.png`), documented in `g1_report.json` (`overflowPx = 0`, `tooSmallCount = 0`, `errors = []`).
