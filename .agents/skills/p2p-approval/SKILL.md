---
name: p2p-approval
description: >-
  Prepare, explain, verify, or finalize mandatory P2P user-approval gates for
  persistent skills, Live Specs, external actions, destructive changes,
  releases, and deployments. Use when the user invokes $p2p-approval, asks what
  is waiting for approval, or wants to approve a protected P2P action.
---

# P2P User Approval Gate

Keep technical validation and user consent separate. Run every required
technical gate first. A user approval cannot turn a failed eval, drift,
security, data-boundary, or rollback gate into a pass.

## Required behavior

1. Identify the exact protected action, scope, subject, SHA-256, risks, and
   reversible alternative.
2. Run the action's technical gates and save their report. If any gate fails,
   stop without requesting approval.
3. Require the report to say `status: PASS`, contain no failures, name the same
   action, and bind the current subject SHA-256. Create a pending request with
   `p2p_approval.py request`. Do not approve it.
4. Show the user the action, subject hash, technical report, risk summary,
   expiry, and one exact interactive command.
5. Accept only an explicit, scoped decision. Silence, a previous unrelated
   “yes”, or an agent's own judgment is not approval.
6. Recompute the subject hash before execution. Any change after approval
   invalidates the record and requires new technical gates and approval.

## Strong approval path

After installation, the user—not the agent—runs:

```text
py .p2p/system/scripts/p2p_approval.py approve --request <request.json> --by <your-name>
```

The command requires an interactive terminal and an exact confirmation phrase.
The agent may explain or verify the resulting record, but must never type the
confirmation phrase or run the approval command on the user's behalf.

For releases or deployments, use `p2p_gate.py prepare`, then the interactive
approval above, then `p2p_gate.py finalize`. Finalization must bind the approval
to both the technical-report hash and the unchanged subject hash.

For FACT_LEDGER promotion, run `p2p_governance.py prepare-live` first. Create the
`promote_live_specs` request with both the ledger and preview report, obtain the
user's decision, then run `build-live --technical-report ... --approval ...`.
Never build first and ask the user afterward.

## Boundary

This is an auditable workflow control, not proof of operating-system identity.
Host permissions, sandboxes, access control, backups, and external-system
authorization remain separate security boundaries.
