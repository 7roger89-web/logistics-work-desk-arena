# LOG-DOCGEN-01 — cumulative recovery and final HDNT correction

Date: 2026-09-08 (UTC)

## Delivery status and branch boundary

The cumulative candidate is on the fixed Arena session branch:
`arena/01a07fa2-logistics-work-desk-arena`.

**PR #1 has not been updated by this session.** Its branch is
`arena/01a07b55-logistics-work-desk-arena`, which this session is not authorised
to push. PR #1 was read back as OPEN at
`b9a597cc8bf1a546dedcae7e0408b78f0b13cd9a`. No second PR was created, no merge
was performed, and neither canonical nor production was touched.

The candidate is programmatically validated, but final delivery to the same
PR remains blocked on that branch boundary. Moving PR #1 requires a session
authorised for its existing branch, a lease pinned to the then-verified remote
head, and exact remote-SHA readback. Do not merge or treat the existing bad PR
head as the cumulative candidate.

## Recovery provenance

- Bad head: `b9a597cc8bf1a546dedcae7e0408b78f0b13cd9a`.
- Bad head's actual parent: `20e532b442ee8c7862d9ac6eb62100747098f4f6`.
- Recovery base: `9463d97a50bc6faa94c47fbd032f8099fd937087`.
- The fixed session branch was reset to the fetched recovery base, not rebased
  or branched from the bad head. The commit containing this report is the
  single final commit directly on that recovery base.
- All earlier repairs were verified as ancestors of the recovery base:

| Repair commit | Retained repairs |
| --- | --- |
| `3f9a049c864877552ac766aed04cb3f40bb6178f` | Conditional calcChain cleanup, including relationship/content type |
| `30254e7bdab7d3e945856ce3c90c09cd2bbf2568` | Summary formula caches, recalculation flags, print/layout repairs |
| `55047bcc3a63fbc68f2f20e3eede7d6320aa7586` | PL definedNames before calcPr |
| `4c1b237574937ac03660e3c860f8bab6fdd1bf44` | HDNT spacing, isolated non-wrapping E24 cloned style |
| `9463d97a50bc6faa94c47fbd032f8099fd937087` | Placeholder cleanup and HDMB honourific normalization |

Verification against the candidate commit:

```sh
BASE=9463d97a50bc6faa94c47fbd032f8099fd937087
git merge-base --is-ancestor "$BASE" HEAD
test "$(git rev-parse HEAD^)" = "$BASE"
test "$(git rev-list --count "$BASE"..HEAD)" = 1
```

## Exact production delta

Only **two production lines** differ from the recovery base, both in
`core/docgen/generator.py::build_docx_run_edits`:

1. Paragraph 9/run 1 becomes `/Bà ` plus the normalized agent representative.
2. Paragraph 15/run 2 uses the company's full stored representative, without
   stripping its honourific.

The generator and its original regression-test expectations exactly match
those two files from `b9a597`. The old engine regression was **not** copied.

Expected and tested text:

```text
Agent master: Ông Nguyễn Văn Anh
Paragraph 9: Đại diện: Ông/Bà Nguyễn Văn Anh  Chức vụ: Giám đốc

Company master: Bà Lê Thị Thu Hương
Paragraph 15: Đại diện : Bà Lê Thị Thu Hương  Chức vụ: Giám đốc
```

Run 0 remains `Đại diện: Ông`; run 2 is two spaces; run 3 holds the complete
title label and value. Company paragraph spacing remains minimal. Run
properties, paragraph properties and section settings remain intact.
HDMB A13/A20 still normalize the names after their existing `Ông/Bà` labels.
No master records are rewritten.

`core/docgen/template_engine.py`, `tests/test_ooxml_mutation.py`,
`core/docgen/rules.py`, `core/auth.py`, `core/database.py` and `views/docgen.py`
are byte-for-byte identical to the recovery base. Preserved Git blobs:

- Engine: `fd618971d47ec5800b2dd9f0f5366449c89db208`.
- Original OOXML regressions: `4f492ef865bc4dd2b641eb530a0237f7f24fbe41`.

The other changes are test-only synthetic fixture builders, the comprehensive
acceptance tests, and this report. No legal template binaries are included.

## Comprehensive focused sweep

Environment: Python 3.11.2, openpyxl 3.1.5, python-docx 1.2.0, lxml 6.1.3,
pytest 9.1.1, pytest-socket 0.8.1. Dependencies installed from the repository's
requirements plus pytest/pytest-socket in an ignored local virtual environment.

```sh
python -m pytest --disable-socket \
  tests/test_log_docgen_01.py \
  tests/test_ooxml_mutation.py \
  tests/test_log_docgen_01_cumulative.py \
  tests/test_logc15_auth_rbac.py \
  tests/test_log_rbac_support_01.py -q -ra
```

**Result: 210 passed, 10 skipped, 0 failures; 1 blocked-socket warning.**

| Module | Passed | Skipped |
| --- | ---: | ---: |
| Original DOCGEN rules/service tests | 78 | 10 |
| Preserved OOXML regressions | 6 | 0 |
| New cumulative acceptance | 88 | 0 |
| C15 auth/RBAC | 28 | 0 |
| Support RBAC | 10 | 0 |

The 10 skips are the original private-template-dependent tests: six file
checks, three successful-generation RBAC checks, and one supersede check.
Their external legal assets are absent in Arena. The new cumulative module
executes corresponding programmatic checks using explicitly synthetic
packages; it does **not** pretend these are the private templates. No new
cumulative test is skipped. A broader existing route-import test emitted a
warning when the socket guard blocked socket creation; no connection was
allowed.

Before the two production changes, the new cumulative tests reported
**82 passed, 6 failed**, with all six failures showing the missing `/Bà`
prefix in rendered HDNT paragraph 9. After the changes all 88 pass, including
full stored company honourific assertions.

### Executed acceptance dimensions

| Dimension | Executable evidence |
| --- | --- |
| HDNT | Exact paragraph 9/15 concatenation for Ông, Bà, and unprefixed agent names; company Ông/Bà retained; no duplicate honourific, missing suffix, huge spaces, tabs/newlines or detached title; run/paragraph/section properties retained |
| PL | F28/F29/F30 formula text and non-stale numeric caches checked in raw XML and separate formula/data-only openpyxl loads; 18 goods lines and VND rounding; auto/full recalculation; definedNames before calcPr with existing or newly created names; scoped row-9 print title, repeat mutation without duplication; row 6 height 75 |
| HDMB | F25/F26/F27 formula text and caches checked in XML and both openpyxl modes; full recalculation; E24 separate cloned style, shrinkToFit on, wrapText off; F24 and every old style retained; font, border, fill, number format and alignment preserved; A13/A20 normalized |
| PXK | B15/C15/D15 literal source values for explicit PL and HDMB sources, with empty or conflicting goods editor; source revision/snapshot readback; conditional calcChain cleanup with no dangling relationship/content type and no unrelated relationship changes |
| PXK layout | Long seller/address/receiver/location text retained; rows 6/7 height 40, rows 10/11 height 30; wrapping in all four cells without altering old shared styles; expected merges; portrait, fitToWidth=1, fitToHeight=0, fitToPage=true; worksheet element order |
| Conditional preservation | Both shared-string and inline-string paths; calcChain retained byte-for-byte for cache-only writes, literal-only templates, ordinary text writes, empty/unknown-sheet/unknown-cell fills; unaffected workbook parts byte-identical |
| Source immutability | Every new synthetic source is read-only and SHA-256, mtime, size and mode checked after use, including repeat-generation inputs; masters and source snapshots compared before/after |
| RBAC | All four document types through generation/download permission boundary for admin/support/sale/viewer/unknown/anonymous; issue/supersede admin/support allowed, sale/viewer/unknown/anonymous denied without writes |
| Issue/supersede | New logical replacement ID, exact frozen old record except controlled supersede link, second issue rejected, idempotent same link, different second link rejected, 12 immutable-field attacks rejected without writes, previous revisions retained for all four types |
| Finance safety | Production persistence functions execute only against a recording, fail-closed in-memory document/audit store; forbidden collection access is recorded and fails teardown even if swallowed; no Finance Actual writes or Mongo connections |

## Import / compile

```sh
python -m compileall -q core views tests app.py web_app.py bot_service.py archiver.py
python -m pip check
```

PASS. Separate socket-disabled import smoke passed for:
`core.docgen.template_engine`, `core.docgen.rules`, `core.docgen.generator`,
`core.auth`, `core.database`, and `views.docgen`. MongoClient was prohibited
and asserted uncalled. `CachedFormulaValue` imports successfully from the
recovered engine. Dependency check: no broken requirements.

Local execution logs/JUnit live under ignored `.tmp/log-docgen-01/`; generated
fixtures and virtual-environment files are not part of the commit.

## Safety and remaining owner gate

```text
SOURCE_TEMPLATE_MUTATIONS=0
LEGAL_TEMPLATE_BINARIES_IN_CANDIDATE=0
FINANCE_WRITES=0
CANONICAL_MUTATIONS=0
PRODUCTION_MUTATIONS=0
NATIVE_OFFICE_FINAL_SINGLE_PASS_REQUIRED=YES
NATIVE_OFFICE_PASS=NOT_CLAIMED
PR1_UPDATED_BY_THIS_SESSION=NO
```

No private legal templates were supplied, modified, staged, or generated into
the candidate. The inherited unrelated owner-feedback DOCX and synthetic
Getfly XLSX are unchanged. No deployment, canonical write, production access,
merge, or new PR occurred.

After the same PR is updated by an authorised session, run one final combined
Native Word/Excel pass on the actual unchanged owner templates for HDNT, PL,
HDMB and PXK: no repair prompt; correct representative text; displayed cached
totals and formulas; PL repeated row 9 and long row 6; HDMB E24 fitting without
wrapping; PXK long-text readability and one-page-wide print setup. Recheck
source hashes. The Arena OOXML/library tests do not replace that native gate.
