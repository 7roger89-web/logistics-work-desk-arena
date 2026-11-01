# G1.5 independent acceptance review — PR #232 (staging)

Reviewer: Arena agent on branch `arena/5bc30481-chunli` (NOT the author of the
`db9015e` content-integrity fix). Repository: `7roger89-web/logistics-work-desk-arena`.

PR HEAD reviewed: `968e7cfb945a2e2b269a2829576d86df021f27b5` + this review commit.
Runtime: Python 3.11.2, pytest 9.2.0, streamlit 1.66.1, mongomock 4.3.0,
pymongo 4.19.0, jsdom 30 (component DOM test). Isolated in-memory Mongo only —
no Cloud, no production, no real customer data.

## What was challenged

The reported blocker: Admin publishes `E/v1`, then a source field is edited
while the id/version/verified flags stay the same — the customer must not see
the edited content.

| Check | Result |
| --- | --- |
| Focused G1/G1.5 suites at this HEAD | 186 passed (incl. 29 new independent tests) |
| Same-version edit of title / occurred_at / stage / document title / kind | denied, whole card hidden |
| Content swapped between two approved events | denied |
| Approved source deleted / transport_mode changed / verified or visibility revoked | denied |
| New pin added to a manifest without a new approval | denied |
| Missing `approved_content_sha256` on a pinned manifest | denied |
| Forged digest of an attacker-built projection | denied |
| Digest copied from another lot | denied |
| Unpinned legacy release | visible with empty timeline/documents, no data invented |
| Whitespace-only source edit | still visible (no false revocation) |
| Other customer principal / foreign manifest | denied, no cross-tenant text |
| Viewer/sale/support/operations/unknown write | `PublicationWriteDenied`, no manifest written |
| Streamlit rerender after mutation (AppTest) | payload drops the lot, unapproved text absent |
| Tenant switch on the same mounted component | payload resets, previous customer's text absent |

## Mutation proof the tests are not vacuous

Disabling only the content-digest check in `core/customer_portal.py`
(`if manifest.get("event_versions") or ...` -> `if False:`) makes **25 tests
fail**, 13 of them from the new independent challenge file. Command:
`python -m pytest tests/test_customer_portal_g15_independent_challenge.py tests/test_customer_portal_sources_g15.py tests/test_customer_portal_publish_g15.py -q`.

## One test repaired (real regression from the fix)

`tests/test_customer_portal_hexa_reference_ui_g15.py::test_owner_granted_publication_fields_reach_the_ui_without_scope_change`
failed at PR HEAD: it added pins to a legacy seed manifest that carries no
`approved_content_sha256`, which the new rule (correctly) rejects. The test now
creates the release through the real Admin publisher
(`core.customer_portal_publish.publish_verified_sources`), so it still proves an
Owner-approved release reaches the UI and never widens the tenant — and it now
exercises the actual approval path instead of a hand-built manifest.

## Full-suite comparison (same environment, same command)

`python -m pytest tests -q --continue-on-collection-errors -p no:cacheprovider`

- PR HEAD (before this commit): **38 failed, 2115 passed, 45 skipped**
- After this commit: **35 failed, 2148 passed, 44 skipped**

Fixed: the reference-UI test above, the component tenant-reset DOM test, the
inbox DOM test and one React header regression test (the last three only need
`npm install` in `component/`). No new failure set; the single difference
`test_gnt_revision_comes_from_durable_docgen_metadata_after_session_clear`
passes in isolation on both trees (order-dependent flake, unrelated to G1.5).

## Verdict

`PROVEN` for the code/test layer at this HEAD on isolated data.
Still **not** proven here (separate gates, unchanged):
`CLOUD_QA=BLOCKED` (deployed SHA and runtime DB identity unverified), real
Google OIDC login, and the completeness of real Lục Giác approved business
provenance. No merge to `main`, no production deploy, no writes to real
customer data.
