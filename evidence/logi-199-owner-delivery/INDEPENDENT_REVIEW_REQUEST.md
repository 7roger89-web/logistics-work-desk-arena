# LOGI #199 — Independent Review request, exact 8932fcb

STATUS=HANDOFF_PREPARED_NOT_DISPATCHED; INDEPENDENT_REVIEW=INCOMPLETE.
Attempt to post this handoff to issue #199 via `gh issue comment 199` failed
with `Resource not accessible by integration` (exit 1). No reviewer was
assigned/notified; an Owner/Control Tower with comment permission must route
this handoff. This is an executable handoff, NOT a reviewer verdict. No independent agent
invocation tool is exposed in the current Arena session; no Codex/Claude CLI
was installed; GitHub collaborator lookup returned only Owner `7roger89-web`.
Do not represent author checks or CI as independent review.

## Target (frozen)

Repository: 7roger89-web/logistics-work-desk-arena
Branch: arena/d657fb56-logistics-work-desk-arena
Candidate: 8932fcb4aa2e7705b1e0963a830758bd3d9849ae
Compare A/B changes against: abf3c0edca0e0c24e7cba840ca2923623454653e
The candidate must not be replaced with the HEAD of subsequent documentation.
No source changes, G0–G5 recertification, business-data writes, main merge,
production deploy, new hosting, or paid service are authorized by this handoff.

## P2P_LAW_PREFLIGHT (reviewer must perform their OWN read)

Read repository-root AGENTS.md. Canonical law wins only if already successfully
reachable by this actor/session; otherwise installed > valid portable > fresh
inline capsule > blocked. In this repo-scoped clone, read the valid portable
projection directly, not a cross-repo probe solely to induce fallback.
Emit exactly one P2P_LAW_SOURCE=<actual source>, plus actor-own
LAW_CHECK=PASS | SOURCE=<actual> | SOURCE_SHA256=<actual source identity>,
or LAW_CHECK=BLOCKED. Never inherit the executor's receipt.
Portable recorded SOURCE_CONTENT_SHA256 at handoff:
11ce33bb9c514d32ad3aec3eb7d8b40f0d0290b1dbe79eaa15751ef34668bd4b.
Perform bounded ACTIVE experience lookup and emit EXPERIENCE_CHECK.
REQUIRED_SKILLS=p2p-uiux:
`.agents/skills/p2p-uiux/SKILL.md`, SHA-256
98f26873e48cc87e34d132478f73672a80d20b3a8e1a2256bdcdab4d6107e7b2.
Read/apply it; return exact p2p-skill-consumption-receipt/1. Missing/hash mismatch
=> LOAD_FAILED, stop. Owner authority is not expanded by skills or receipts.

## OE_GATE

Ask exactly `Không bị over engineering chứ?`; evaluate SIMPLER_PATH,
MATERIAL_PROGRESS, NECESSITY, CORE_BEFORE_SUPPORT, SMALLER_VERIFIABLE_SLICE;
return OE_VERDICT=DO_IT|SKIP_IT|DEFER_UNTIL_NEEDED with a concrete reason.
Use the smallest meaningful A/B challenge. Do not restage G0–G5.

## Review only these boundaries

1. **A: mobile initial camera.** Inspect JourneyMap.tsx diff and source-built
   dist. At 390×844 fresh T6-FCL should begin BOOKING → PICKUP → CUSTOMS EXPORT
   (third card partially visible as disclosed), 11 nodes / 20 edges, 100%.
   `Đọc rõ` keeps real problem/current access; selected node focus, pan/zoom/Fit
   stay usable. No fake state/node or business-data substitution.
2. **B: meaningful persistence.** Check capture_fix_ab.py and metrics.json:
   OLD 2026-10-11, NEW 2026-10-04, Save tapped, full reload then persisted
   readback NEW, OLD != NEW required. Reject same-value-save evidence. Verify
   screenshots before/fill/readback and fail-closed verdict predicates.
3. **Paper preservation.** Original Owner HTML SHA-256
   26e2e5cf81db1d991a9442872cfde1b7b6a7726e8f0832c76e23a52189c3647f;
   JPEG asset SHA-256
   e3cb46df825b3a9d5427aa734113f2975ca7c25cd52a2ff1eeb780008d040627.
   #EDF1F5, 760px repeat, 0.34 multiply, 52×52 rgba(120,146,170,0.16) grid.
   Compare baseline to exact candidate; do not re-design it.
4. Evidence provenance: `evidence/logi-199-final-fix/` at **8932fcb**: README,
   source/dist/harness hashes in metrics.json, before/after and OLD→NEW PNGs.
   capture_base_head records pre-commit baseline; do not relabel it as candidate.
   Independently compare recorded file hashes with blobs at candidate SHA.

If replay needed, only use `scripts/logi199_t6_staging_app.py` on isolated
Mongomock. Require STAGING_ISOLATION_PROOF=PASS before fixtures, no real Mongo
or production credentials. Local loopback only if AUTH_REQUIRED=false.
Do not publish unauthenticated staging or claim Linux tests certify Windows.

## Required output

Independent Review PASS / REJECT / INCOMPLETE, reviewer identity and actor-own
receipts, exact reviewed SHA, reviewed files/screenshots, reproducible checks,
findings with source/evidence, residual blockers. PASS applies only to A/B +
paper preservation, NOT Owner UAT, Windows runtime or production authorization.
Post the result in issue #199; Owner/Control Tower must route to a genuinely
separate reviewer. Request posted != reviewer accepted != review completed.
