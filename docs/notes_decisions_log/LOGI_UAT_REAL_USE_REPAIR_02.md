# LOGI_UAT_REAL_USE_REPAIR_02 — real-use repair set (P0-A, P1-A, P1-C fixed; P1-B deferred)

Continuation of the Logistics Work Desk real-use completion goal. Clean task
branch from `main@344add65273500fd39eb15f3c19d8036ffc78f1b`.

PR #52 (`arena/01a0aeea-…` @ `137de0eb4afeb59967d6a8ca2b83d7f3882cea83`,
APPROVED_FROZEN, not merged) was NOT modified, pushed to, merged or closed.

`P2P_LAW_SOURCE=LOCAL_PORTABLE`
(`.p2p/portable/P2P-OPERATIONS-NOTEBOOK.md` carries
`P2P_PORTABLE_LAW_PROJECTION=YES`, canonical-source provenance and
`SOURCE_CONTENT_SHA256=41b9104…`; canonical cross-repo read of
`7roger89-web/P2P-upgrade-github-1` returned 404 for this installation, which
is NOT treated as proof that canonical law is absent.)

---

## P0-A — CUSTOMER CREATE FALSE SUCCESS

**BASELINE_FAILURE**
`component/src/pages/Customers.tsx::submit()` called `dispatch(...)`, then
unconditionally `toast("Đã gửi tạo khách hàng …", …, "green")`,
`setCreating(false)`, `setEditing(null)`, `setForm(EMPTY_FORM)`. The return
value of `dispatch` was discarded, so a refused transport
(`dispatchLogiEvent` → `false` when no transport is bound) closed the modal,
erased everything the operator typed and claimed success. A backend refusal
(duplicate id / RBAC / validation) was likewise never shown: the operator had
already been told it worked.

**ROOT_CAUSE**
Two distinct gaps, both "transport handled" being treated as "write
succeeded":
1. frontend: the dispatch result and the backend outcome were never consumed;
2. backend: `_handle_customer_create` / `_handle_customer_edit` did not echo
   the caller's `requestId`, so even a UI that wanted to wait could not tell
   its own outcome from a concurrent one.

**CUSTOMER_CREATE_AUTHORITY** — `ALREADY_EXISTED_AND_REUSED`.
The authoritative outcome/readback mechanism already existed
(`LAST_WRITES_KEY` → `lastWrites[]`, correlated by `requestId`, used by
`shipment_create`, `authority_agent_save`, `finance_actual_save`,
`getfly_import`, the user-management events). No new framework was created:
customer create/edit were joined to that existing mechanism, exactly as
`authority_agent_save` does it.

**CHANGED_PATHS**
- `views/logi_c1.py` — `_handle_customer_create`, `_handle_customer_edit`:
  echo `requestId` on success AND on every refusal; return `persisted`
  identity from the fresh readback; report `ok=False` when the writer claims
  success but `read_customer` cannot read the customer back.
- `component/src/pages/Customers.tsx` — one in-flight intent with a
  `requestId`; the modal stays open and keeps its data until the matching
  authoritative outcome arrives; success requires the outcome AND the customer
  genuinely present in the fresh view-model; refusals render verbatim.
- `component/src/components/ui.tsx` — `SuccessBtn` / `GhostBtn` gained the
  `disabled` prop that `PrimaryBtn` already had.

**OLD_BEHAVIOR_REJECTED_BY**
- `tests/component/dom_acceptance_real_use_repair.mjs --only 2` against the
  **old** `main` bundle: `AssertionError: OLD BEHAVIOUR: a transport failure
  still claimed 'Đã gửi tạo khách hàng'`.
- `tests/test_logi_uat_real_use_repair_02.py` against the **old** backend:
  7 of 11 tests fail (all correlation/readback contracts).

**NEW_BEHAVIOR_PROOF**
- DOM acceptance on the REAL production bundle in jsdom, driven by a
  real-backend fixture (`scripts/gen_real_use_repair_fixture.py`, isolated
  mongomock staging): 10/10 checks, covering transport failure, transport
  success ≠ persistence, double-send, unrelated-write-is-not-success, backend
  refusal, and authoritative success.
- `tests/test_logi_uat_real_use_repair_02.py`: 11 passed, including the
  adversarial `test_writer_success_without_persistence_is_reported_as_failure`
  (writer returns True, readback empty ⇒ `ok=False`).

**RUNTIME_BOUNDARY** jsdom over the real committed bundle + mongomock staging
backend. **UNPROVEN_BOUNDARY** live browser, live Streamlit session, real
MongoDB Atlas.

---

## P1-A — NEXT WORK TAB (`lay-hang` → `lay`)

**BASELINE_FAILURE** "XỬ LÝ NGAY" on the shipment detail did not open the
intended work section.

**ROOT_CAUSE** `component/src/pages/ShipmentDetail.tsx` parsed the backend's
own `nextRoute` with `/tab=(\w+)/`. `\w` is `[A-Za-z0-9_]` — it excludes `-`,
so every hyphenated tab the backend really emits (`lay-hang`, `tai-chinh`,
`van-tai`, `chung-tu`, `lich-su`) was truncated to its first segment. `lay`
matches no tab, so no section was selected.

**CHANGED_PATHS** `component/src/pages/ShipmentDetail.tsx` — `nextRouteTab()`
parses the query with `URLSearchParams` and validates against the SAME
canonical `TABS` list the tab bar renders; an unknown tab falls back to the
default view instead of selecting a non-existent section.

**OLD_BEHAVIOR_REJECTED_BY** `--only 8` against the old bundle:
`AssertionError: OLD BEHAVIOUR: the truncated tab matched NO section, so no
work section opened (active tabs: 0)`.

**NEW_BEHAVIOR_PROOF** `--only 8` on the new bundle: the backend's real
`/lo-hang/LO-0295?tab=lay-hang` activates exactly one tab, "Xuất khẩu".
Data half proven in `test_next_route_tabs_are_real_workdesk_tabs_and_include_hyphenated_ones`
(every emitted tab exists; at least one is hyphenated, so the challenge is not
vacuous).

---

## P1-B — CONTRACT DOCUMENT HANDOFF — **DEFERRED_DEPENDS_ON_PR52 (NOT FIXED)**

> **Status change.** An earlier revision of this PR claimed P1-B was repaired.
> That claim was **withdrawn** after Control Tower review `5237391551`. The
> code change has been reverted; this branch ships **no** P1-B fix.

**BASELINE_FAILURE** "MỞ CHỨNG TỪ" on a linked contract leaves the employee in
the shipment's own documents/PXK surface. **Still true on this branch.**

**ROOT_CAUSE** The button calls `setSp({ tab: "chung-tu" })` — it re-selects the
SHIPMENT tab the employee is already standing on. It never navigates to the
contract. (Root cause confirmed; only the remedy is deferred.)

**WHY THE ATTEMPTED FIX WAS WITHDRAWN** The attempted remedy was a `Link` to
`/hop-dong/<id>?tab=chung-tu` built from a raw `linkedContract.id`. A contract
number is ONE route segment but can contain `/` — the repo reproduces
`05/2026/HDMB`. Independently reproduced against this PR's own bundle before
accepting the review:

```
contract id under test : 05/2026/HDMB
emitted href           : /hop-dong/05/2026/HDMB?tab=chung-tu
reached HDNT/PL/HDMB   : false
fell through to '*'    : true
```

`App.tsx` declares single-segment `/hop-dong/:id`, so the raw path misses the
detail route and lands on the wildcard. The repair was therefore **false at the
slash-ID boundary** — it worked only for ids that happen to contain no slash.

**WHY IT IS NOT FIXED HERE INSTEAD** PR #52 (APPROVED_FROZEN) already owns this
route class via `contractPath()`, and this branch is based on pre-#52 `main`.
Adding a second, divergent encoder would duplicate a frozen slice and create two
implementations of one routing rule. Per instruction, no `contractPath` is
reimplemented here.

**CHANGED_PATHS** none — `component/src/pages/ShipmentDetail.tsx`'s
"MỞ CHỨNG TỪ" control is now **byte-identical to `main`** (verified by diffing
against `git show main:`).

**CURRENT TEST STATUS** DOM `--only 9` no longer asserts a repair. It is a
**deferral guard** that pins the known-broken behaviour and fails if anyone
re-introduces a slash-unsafe `/hop-dong/<a>/<b>` route. It passes on BOTH the
old and new bundles — by design, because `main` has the same defect. It is
explicitly **not** acceptance evidence of a fix.

**UNBLOCK CONDITION** After PR #52 integrates, this becomes a one-line change
using the shared `contractPath()` helper, plus flipping STEP 9 back to a real
acceptance assertion.

---

## P1-C — SUPPORT/ASSIGNEE LABEL

**CANONICAL SEMANTICS ESTABLISHED FIRST (no field was guessed):**

| Concept | Canonical source | Status |
|---|---|---|
| Shipment responsibility ("owner") | `core/shipment_dashboard.py::_owner` over `internal_sale_owner`, `sale_owner`, `sales_owner`, `owner`, `assigned_to`, `assignee`; `"Chưa phân công"` when unassigned | EXISTS — already projected as `sale` |
| Per-task assignment | `tasks.assignee` (+ `assignee_user_id`, `assigned_by_user_id`) written by `core/database.py::add_task`, RBAC `shipment_edit` | EXISTS |
| **Assigned support / handling employee on a shipment** | — | **DOES NOT EXIST** (no field, no writer, no RBAC permission anywhere in the repo) |

`support` was, and still is, `shipment.updated_by` — the last person who saved
the document (`core/database.py` sets it on every write). That is provenance,
not responsibility.

**CHANGED_PATHS**
- `views/logi_view_model.py::_task_projection` — DERIVED ops rows (`OPS-…`,
  which have no task document) now carry the canonical owner resolution
  (`row["sale"]`) instead of the last writer. Rows sourced from the real tasks
  collection keep their own canonical `tasks.assignee`, untouched.
- `views/logi_real_data.py` — documents precisely what `support` is and why no
  assignment semantics may be inferred from it.
- `ShipmentDetail` / `Shipments` / `Receivables` — the value is labelled
  "Cập nhật bởi" instead of "Support"/"SP"; "Sale phụ trách" keeps the
  canonical owner.

No assignment field, writer, permission or business meaning was invented.

**OLD_BEHAVIOR_REJECTED_BY** `--only 10` against the old bundle:
`AssertionError: OLD BEHAVIOUR: updated_by was presented under a 'Support'
responsibility label`; plus
`test_derived_ops_rows_use_the_canonical_owner_not_the_last_writer` failing on
the old backend.

**ASSIGNMENT_STATE = PRODUCT_AUTHORITY_REQUIRED** for a real shipment-level
assignment flow. Exact Owner decision required, in the Assignment section below.

---

## Restored regression guard (same defect class as P0-A)

`tests/component/dom_acceptance_create_shipment.mjs` — the DOM oracle that
protects the *shipment*-create false-success repair (CONTROL_TOWER_REPAIR_01)
was **already failing on `main`**: the button label had drifted to
"ĐANG TẠO LÔ…" while the oracle asserts the canonical
"ĐANG CHỜ BACKEND XÁC NHẬN…". The guard was therefore disabled. The label was
restored to the canonical wording used by every other authoritative-outcome
surface, and the oracle passes again (5/5).

---

## REGRESSION_PROOF

- Python suite: **14 failed, 988 passed, 44 skipped** — the failing set is
  byte-identical to the pre-change baseline on `main` (14 pre-existing
  failures, captured before any edit); passing count rose 977 → 988.
  (`tests/test_partner_reconciliation_desk_write_oracle.py` is excluded from
  both runs: it fails at COLLECTION on `main` — `ImportError: cannot import
  name 'ROUTES' from 'views.web_app'` — and is untouched by this slice.)
- DOM suites: 20/23 pass. The 3 failures
  (`consolidation`, `handbook`, `user_access`) are **pre-existing on `main`**
  and unrelated: their fixtures carry a stale `ceoReport` shape missing
  `actionables` / `financeActual` / `topCustomers`, so the CEO page crashes on
  `actionables.length`. `create_shipment` was also failing on `main` and is
  now REPAIRED by this slice.
- `PR50_INVARIANT` preserved: `tests/test_logi_interaction_latency_repair_01.py`
  19/19 pass. No callback-surface change: no new `st.rerun()`, no second
  view-model build, no extra dispatcher pass — the customer path reuses the
  single existing `consume_c1_triggers` → `LAST_WRITES_KEY` → one rerun flow,
  and all three UI repairs are client-side render/route changes that emit no
  additional backend event.
- Source/dist sync preserved: `component/dist/logi-shell.{js,css}` rebuilt from
  source and committed (verified reproducible: rebuilding `main`'s source
  reproduced `main`'s committed bundle byte-for-byte before any edit).
- `npx tsc --noEmit` clean.

---

## Authority boundaries observed

`PRODUCTION_MUTATIONS=0` · `PILOT_MUTATIONS=0` · `SECRETS_CHANGED=NO`
No deployment, no migration, no infrastructure/spend, no destructive data
mutation. All writes in evidence went to an isolated mongomock staging
transport that is reset before and after each run.

`LIVE_RUNTIME_EVIDENCE=UNVERIFIED_RUNTIME` — Chromium is not available in this
environment. jsdom-over-real-bundle evidence is NOT upgraded to live UAT.

---

## Owner decision required — shipment assignment

To expose a real "người phụ trách lô hàng" assignment control, the Owner must
decide (none of this can be inferred from the repo):

1. **Field & semantics.** Reuse one existing owner alias
   (`internal_sale_owner` / `sale_owner` / `assigned_to` / `assignee`) as the
   single canonical writable assignment, or introduce a NEW distinct field for
   an operational handler separate from the commercial sale owner? Today all
   six aliases are READ-ONLY resolution inputs; nothing writes them.
2. **Cardinality.** One responsible person per shipment, or separate
   commercial (Sale) + operational (Support) responsibility?
3. **Permission.** Which permission may assign — `shipment_edit` (Sale and
   Support both hold it), a narrower existing one, or Admin only? May a user
   self-assign? May they reassign someone else's shipment?
4. **Identity.** Free-text display name, or a real `users` reference
   (`user_id`) with the display name resolved through `core.users`?
5. **Backfill.** What happens to the ~existing shipments with no owner — stay
   "Chưa phân công", or bulk-assign?

Once (1)–(4) are decided, the implementation is small: one writable field on
the existing `save_shipment_atomic` path + one bounded typed event through the
existing dispatcher + one picker. It is intentionally NOT built on a guess.
