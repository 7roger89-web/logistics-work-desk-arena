# Issue #166 — Support Attention / Now V1 — Evidence

## Exact state

- Base main: `13b194a0ca9355c7b5af70e4fbd1fb89ed6910ad`
- Final candidate branch: `ct/issue-166-support-attention-now-fresh-main`
- Product source exercised by browser: `7231800fbac74f6af4134f153da97be3a2df8c84`
- Browser evidence commit: `306c6c1f24f275a1aa414c87f017716305c3f8a7`
- Final focused verification run head: `ae0f12e2eacc34198cc364e761659876aa876787`
- Temporary verification workflows were removed before PR delivery.
- No merge and no deploy were performed.

## Architecture receipt

```text
ATTENTION_PROJECTION=views/support_attention.py; pure read-only projection
SOURCES=shipment primaryAction + canonical tasks + Work Module execution/rollup facts
ORDERING=BLOCKING > OVERDUE > DUE_SOON > ACTION > INFO; deterministic deadline/source tie-breaks
DEDUP=exact shipmentId + sourceType + sourceRef only; no fuzzy text merge
OWNER_SEMANTICS=task assignee for TASK; shipment owner only for primary action; updated_by never used as task owner
SECOND_TASK_STORE=NO
SECOND_ATTENTION_STORE=NO
JOURNEY_AUTHORITY_UNCHANGED=YES
```

Home and Shipment Detail consume the same `vm.attention` projection. Journey remains the operational-position/context surface and Work Module completion still uses the existing dispatcher/write/readback path.

## Automated verification

### Focused + bounded regressions

GitHub Actions run: **36998009759**

```text
97 passed in 7.39s
```

Bounded set:

- `tests/test_support_attention_now_166.py`
- `tests/test_visual_shipment_workspace.py`
- `tests/test_work_module_library_162.py`
- `tests/test_shipment_dashboard.py`
- `tests/test_logi_shipment_primary_action_unify_01.py`

The focused #166 tests challenge:

- transparent priority ordering;
- blocking vs gate-less module semantics;
- dependency-blocked gate-less step not falsely actionable;
- task assignee vs shipment last writer;
- structured deadline classification only;
- exact-source de-duplication;
- cross-shipment source identity isolation;
- physical Journey position not mutated;
- DONE/UNKNOWN/empty-state semantics;
- existing route/deep-link compatibility.

### Frontend / bundle / DOM regressions

GitHub Actions run: **36995582964**

Passed:

- `npm ci`
- `tsc --noEmit`
- Vite production build
- generated-dist process scan
- Issue #166 DOM acceptance
- Visual Shipment Workspace #160 DOM regression
- Work Module Library #162 DOM regression
- Shipment Document Picker overlap regression

The shipped `component/dist` was rebuilt from source by the verification runner; no hand edit was used.

### Real-browser acceptance

GitHub Actions browser run: **36997508016**

Chromium 141, real dispatcher + isolated authoritative persistence/readback host.

```text
PASS #166 browser:
blocking module
-> Attention before Journey
-> real completion readback updates next action
-> Home shares same truth
-> gate-less module ACTION without fake gate
-> 390px no overflow
```

Browser assertions also verified zero page errors and a tappable mobile Attention CTA.

## Durable visual evidence

- `desktop-1-action-before-journey.png`
  - primary action exists while Journey retains separate operational-position truth.
- `desktop-2-blocking-attention.png`
  - BLOCKING Work Module is visible before Journey; gate and next step are readable.
- `desktop-3-attention-after-authoritative-readback.png`
  - after persisted completion/readback, Attention advances to the next factual step.
- `desktop-4-home-same-attention-truth.png`
  - Home consumes the same Attention truth rather than a second priority engine.
- `desktop-5-gateless-action-no-fake-block.png`
  - gate-less module is ACTION only; no invented gate/blocker.
- `mobile-1-attention.png`
  - 390px reflow; no horizontal page overflow; CTA remains tappable.

Manual visual inspection confirmed:

- Attention hierarchy is clearly above Journey;
- blocking vs action states are distinguishable without relying on color alone;
- module gate wording remains explicit;
- gate-less module does not receive fake red/blocking semantics;
- mobile cards reflow vertically without clipping or horizontal overflow;
- Journey remains visible as context rather than being replaced.

## Acceptance status

```text
LANE=REDESIGN
TEST_PASS=PASS
DOM_ACCEPTANCE=PASS
VISUAL_PASS=PASS
INTERACTION_PASS=PASS
BUSINESS_PASS=NOT_CLAIMED
MERGE=NO
DEPLOY=NO
CONTROL_TOWER_STARTED=NO
CUSTOMER_PLAYBOOK_STARTED=NO
READY_FOR_INDEPENDENT_REVIEW=YES
```

Independent review is still required for merge acceptance.
