---
name: p2p-download
description: >-
  Fetch and stage a new P2P release or LIVE specification from an explicit source for
  verification. Use when the user invokes $p2p-download, asks to refresh P2P data, or
  provides a new release URL or ZIP.
---

Read `../p2p/references/codex-adaptation.md` before applying any Claude-edition
mechanism. The matching section in `../p2p/references/modes.md` is the runtime
contract. Current host permissions and current verified facts take precedence.

# P2P Download and Refresh

Require an explicit URL, release, or attached ZIP. Use only an approved fetch
tool. Record source URL, retrieval date, byte size, and SHA-256 when bytes are
available. Store new material beside the baseline and run
`scripts/update_from_release.py`; never overwrite historical source or promote
LIVE claims to runtime before review.

A complete refresh has separate gates: source inventory, FACT_LEDGER review,
generated Live Specs synchronization, affected project evals, active-runtime
drift scan, rollback artifact, and final package validation. A PASS at one gate
does not imply the later gates passed. After every technical gate passes, create
an approval request bound to the exact candidate SHA-256. Do not promote or
release until the user approves that unchanged candidate.
