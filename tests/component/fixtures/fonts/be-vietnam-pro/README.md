# Be Vietnam Pro — verification-only font fixture (Issue #190)

`component/dist/logi-shell.css` starts with

```css
@import "https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:...";
```

and `component/src/index.css` sets `--font-sans: 'Be Vietnam Pro', …`. In a
network-isolated verification sandbox that @import cannot be fetched, so the
browser silently falls back to another family. A different family has different
metrics, and different metrics change text wrapping, card heights and therefore
the very layout geometry this evidence lane is supposed to measure.

`tests/component/browser_journey_visual_fidelity_190.mjs` therefore intercepts
the Google Fonts request and fulfils it with these files, so the rendered
evidence uses the SAME family as production.

- Provenance: npm `@fontsource/be-vietnam-pro@5.3.0` (files/ directory), OFL-1.1.
- Subsets/weights: `vietnamese` + `latin`, 300/400/500/600/700/800 normal and 400 italic —
  exactly the axes requested by the shipped `@import`.
- Product source, `component/dist/*` and the acceptance hosts are NOT modified.
- `MANIFEST` is the file list the harness reads; keep it in sync with this directory.
