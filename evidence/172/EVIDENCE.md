# Issue #172 — Customer Playbook V1 — Evidence

## Exact state

- Base main at implementation start: `ca3d9550b6de3484861e007c24b32b31658521bc`
- Task branch: `arena/01a0ffef-logistics-work-desk-arena`
- Detail route: `/khach-hang/:id`
- Existing customer list/master route: `/khach-hang` (preserved unchanged)
- Pure composition helper: `component/src/lib/customerPlaybook.ts`
- Read-only page: `component/src/pages/CustomerPlaybook.tsx`
- No merge and no deploy were performed.

## Scope / architecture receipt

```text
CUSTOMER_MASTER_REUSE=YES
CUSTOMER_NOTE_REUSE=YES
EXACT_LINK_RULE=shipment.customerId == customer.id
ATTENTION_REUSE=YES
JOURNEY_REUSE=YES
WORK_MODULE_REUSE=YES
NEW_CUSTOMER_STORE=NO
NEW_SCHEMA=NO
NEW_BUSINESS_WRITER=NO
CRM=NO
AI_RECOMMENDATION=NO
DETAIL_ROUTE=/khach-hang/:id
```

## Verification summary

1. **Focused unit tests (`tests/component/unit_customer_playbook_172.mjs`)**:
   - Exact `shipment.customerId === customer.id` linkage; rejects name-only, MST-only, toneless, lowercase, and empty `customerId` shipments.
   - Reuses existing `customer.note` as `Ghi chú vận hành`; neutral empty state when empty.
   - Reuses shared `Attention` projection filtered strictly by exact-linked shipment IDs, preserving band, order, reason, unknown flag, and canonical route.
   - Neutral empty state when no Attention exists (no `healthy`/`safe` certification).
   - Factual Work Module and canonical blocked-gate grouping without risk/bottleneck/preference scoring.
   - Preserves `UNKNOWN` on both Attention items and Work Modules without converting to zero, done, or safe.

2. **Focused DOM acceptance (`tests/component/dom_acceptance_customer_playbook_172.mjs`)**:
   - Navigates from `/khach-hang` via `Mở hồ sơ` to `/khach-hang/:id`.
   - Verifies maximum 4 primary blocks (`playbook-identity-note`, `playbook-attention-hero`, `playbook-linked-shipments`, `playbook-concentration`).
   - Exercises Acceptance Scenarios A–F and verifies zero write triggers (`triggers.length === 0`).

3. **Real-browser acceptance (`tests/component/browser_customer_playbook_172.mjs`)**:
   - Chromium against the isolated authoritative Work Module host (`1440x1000` desktop and `390x844` mobile).
   - Attaches a real `BLOCKING` Work Module through the existing UI/dispatcher, verifies it surfaces in Customer Playbook hero, drills down to exact shipment/module context, verifies neutral empty state, and proves zero horizontal overflow at `390px`.

## Durable visual evidence

- `evidence/172/desktop-1-customers-list.png`
- `evidence/172/desktop-2-customer-playbook-hero.png`
- `evidence/172/desktop-3-shipments-and-concentration.png`
- `evidence/172/desktop-4-attention-drilldown.png`
- `evidence/172/desktop-5-no-attention-neutral.png`
- `evidence/172/mobile-1-customer-playbook-390px.png`
