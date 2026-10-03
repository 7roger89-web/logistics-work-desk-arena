# Issue #170 — Operations Control Tower V1 — Evidence

## Exact state

- Base main at implementation start: `cec617ace5f6b7f74d34bb5118b61922a0e36713`
- Task branch: `ct/issue-170-operations-control-tower-v1`
- Final plain-language product source head: `e9f9a4cd94049322ad318035b44481d8bf3d4148`
- Standard verification generated-dist head: `690a23ecffc90696d9bbe943c0751ac4b3554304`
- Final real-browser evidence head: `2a2ab3ae4893a019bb96947dfe63ed769778996e`
- The closure commit that adds this receipt removes only the two temporary Issue #170 verification workflows in addition to this evidence file.
- No merge and no deploy were performed.

## Scope / architecture receipt

```text
MANAGER_PROJECTION=views/operations_control_tower.py; pure read-only projection
ATTENTION_REUSE=YES
SECOND_ATTENTION_ENGINE=NO
SECOND_TASK_STORE=NO
DATABASE_READS_IN_TOWER=NO
MANAGER_WRITES=NO
INTERVENTION_RULE=BLOCKING | OVERDUE | DUE_SOON | UNKNOWN | primary Khan
HORIZON=DATE_ONLY: overdue | today | next 1-3 days
OWNER_SEMANTICS=Attention owner only; task assignee stays authoritative; updated_by never becomes responsibility
UNASSIGNED_SENTINEL="Chưa phân công" normalized to explicit UNASSIGNED control gap
CONCENTRATION=customer | blocked gate | Work Module template; neutral counts only
CEO_REPORT_UNCHANGED=YES
CONTROL_TOWER_ROUTE=/dieu-hanh
```

The Tower consumes the same shared Attention projection as Shipment Detail and Home. It does not introduce a second manager priority algorithm, workflow authority, score, scheduler, data warehouse, or persistence model.

## Reality corrections proven during implementation

### Vietnam business date

Date-sensitive Attention and Tower classification now receive one shared business date:

`datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).date()`

This prevents a UTC-hosted runtime from classifying Vietnam's new business day one day late between local midnight and 06:59. The browser acceptance derives the Vietnam date independently with `Intl.DateTimeFormat(... timeZone: "Asia/Ho_Chi_Minh")` and asserts that the live Tower `horizon.asOf` matches it.

### Unassigned responsibility

The existing shipment-dashboard projection uses the display sentinel `"Chưa phân công"` when no canonical shipment owner exists. The manager projection treats that sentinel as an unassigned control gap instead of inventing a person named “Chưa phân công”. Task responsibility continues to come from canonical task assignee.

## Automated verification

### Focused + bounded regressions

GitHub Actions run: **37043127331**

At source head `e9f9a4cd94049322ad318035b44481d8bf3d4148`:

```text
116 passed in 8.24s
```

Passed:
- Issue #170 projection tests;
- Issue #166 Support Attention;
- #160/#161 Visual Shipment Workspace;
- #162 Work Module Library;
- CEO Report;
- shipment dashboard / primary action regressions;
- TypeScript typecheck;
- production Vite build;
- generated-dist executable-process scan;
- Issue #170 DOM acceptance;
- #166 DOM regression;
- #160 visual-workspace DOM regression;
- #162 Work Module DOM regression;
- CEO Report DOM regression;
- Shipment Document Picker unit + DOM regression.

Generated `component/dist` was rebuilt by CI; no hand-edit was used.

### Real-browser acceptance

GitHub Actions run: **37043127350**, rerun job **110958558445**.

Chromium 141 against the existing isolated authoritative Work Module host:

```text
PASS #170 browser:
real blocker
-> manager hero
-> factual filter
-> exact module drilldown
-> workload neutral
-> 390px no overflow
```

The browser path also proves:
- a real BLOCKING module is attached through the existing authoritative UI/write/readback path;
- the separate `Điều hành` route aggregates that shared truth;
- manager queue is visually prior to secondary horizon/context;
- blocking filter contains only real blocking items after navigation settles;
- drill-down lands in the exact existing module context;
- Vietnam business date is used;
- workload copy makes no employee-overload verdict;
- mobile 390px has no horizontal page overflow;
- zero page errors.

## Durable visual evidence

- `evidence/170/desktop-1-manager-queue-hero.png`
- `evidence/170/desktop-2-blocking-filter.png`
- `evidence/170/desktop-3-workload-and-horizon.png`
- `evidence/170/mobile-1-control-tower.png`

Independent visual inspection of the final screenshots confirmed:
- the manager intervention queue has the strongest visual hierarchy;
- coverage language is neutral and does not certify “healthy/safe”;
- source labels and limitation copy are plain Vietnamese rather than internal implementation jargon;
- the blocking gate is visible without relying on color alone;
- mobile content reflows into readable cards without a tiny portfolio map.

## Scope Reality Check

```text
CLAIM=One pure manager projection over shared Attention + one read-only route is sufficient for V1
REALISM=REALISTIC
SECOND_TRUTH=NO
FAKE_24H_CLOCK=NO
WAITING_ON_INVENTED=NO
EMPLOYEE_SCORE=NO
JOURNEY_OCCUPANCY_HERO=NO
CUSTOMER_PLAYBOOK_STARTED=NO
```

Waiting-on/chase age, manager mutation/escalation workflow, exact cutoff timestamps, AI priority, employee/risk/health scoring, generic BI, forecasting and Customer Playbook remain outside V1 because the current repo does not provide the required authority or they are separate roadmap slices.

## Acceptance status

```text
LANE=BUILD
TEST_PASS=PASS
DOM_ACCEPTANCE=PASS
RUNTIME_VISUAL_REVIEW=PASS
INTERACTION_PASS=PASS
BUSINESS_PASS=NOT_CLAIMED
MERGE=NO
DEPLOY=NO
CUSTOMER_PLAYBOOK_STARTED=NO
READY_FOR_INDEPENDENT_REVIEW=YES
LEARNING_RECONCILIATION=CANDIDATE
```

Candidate reusable corrections, not promoted authority:
1. Date-sensitive operational projections should share an explicit business timezone/date instead of inheriting host-local calendar semantics.
2. Display sentinels representing “unassigned” must never become workload identities.
