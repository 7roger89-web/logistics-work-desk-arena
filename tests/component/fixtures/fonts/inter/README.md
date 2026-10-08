
## inter/ — Journey-region typeface proxy (evidence harness only)

`component/src/index.css` sets `.journey-demo { font-family: Inter, ui-sans-serif, system-ui, … }`
but never fetches Inter, so production resolves it to whatever the operator's OS
provides (Segoe UI / SF / Roboto). A network-isolated sandbox has none of those
and falls back to DejaVu Sans, whose much wider metrics distort text block
heights. `@fontsource/inter@5.2.x` (latin + vietnamese, 400–800) is therefore
injected by the harness as the CSS's first-named family — the closest
deterministic proxy to the intended UI typeface. This is an EVIDENCE-HARNESS
decision, not a product change; product source and dist stay untouched.
