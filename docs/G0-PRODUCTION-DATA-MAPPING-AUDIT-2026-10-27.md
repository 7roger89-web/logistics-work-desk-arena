# G0 — Production read-only data mapping audit (27/10/2026)

**Project:** Logistics Work Desk / Trường Thành × Lục Giác (HEXA)  
**Source code baseline:** `dea6c3f05a8177528cac4c0307f9dc72d64a1c93` (`arena/ae5f9f47-logistics-work-desk-arena`)  
**Source data:** MongoDB Atlas Project 0 / Cluster0 / `logistics_db`  
**Access mode:** `READ_ONLY` — `aggregate`, `count`, `list_collections` only.  
**Safety:** no database write, no customer grant, no migration, no deployment, no identifiers/PII/financial amount exported to this report.  
**Runtime limitation:** Atlas DB content was verified, but no evidence that the currently deployed *internal* Streamlit production process connects to this exact database. Confirm live ENV/DB identity before any write.

## Owner's locked business decisions

1. **One customer = one immutable `customer_id`** even when the legal/display name changes. Historical document legal names retain their original snapshots.
2. Use **real production data for a read-only audit**; real production changes and customer-facing release require separately controlled Owner approval.
3. A Journey stage completes only after mode/scope-specific mandatory conditions and authorized human confirmation where required.
4. Verified physical progress may publish by controlled rules; price/document/finance require a separate publication approval.
5. **No quote prices on customer Dashboard.** Only the exact authorized quote *file and version* may be opened by the customer.
6. Approved customer receivables split **SERVICE** versus **ENTRUSTED_GOODS / advance payments**. Never treat quoted totals or internal expense as debt.
7. Customer portal eventually accepts comments, uploads, requests, and delivery confirmation with role/lot/activity audit; customer submissions do not auto-complete an internal stage.
8. All ROAD, SEA, AIR and applicable service profiles remain in target scope; stage applicability varies by service scope.
9. After an ACCEPTED quote, staff may adjust real incurred costs with reasons and full history. **Changing cost does NOT automatically change customer receivable**. Customer sell-side changes require a separate approved addendum/version; old quote/file remains immutable.

## 1. Production observations (anonymous aggregate evidence)

| Test | Observed |
| --- | ---: |
| `customers` records | 362 |
| `shipments` records | 95 |
| Unique exact valid `shipments.customer_id → customers.id` matches | 4 |
| Missing ID, exact customer *name* matches one master record (candidate only) | 87 |
| Missing ID, no unique customer-name match | 4 |
| Customer/Client cached display-name fields differ in same shipment | 6 |
| Customer-name groups duplicated in customer master (exact text) | 0 |
| `shipments.id == shipments.shipment_id` | 95 |
| Shipments with `quote_id` present as nonempty string | 0 |
| Shipments with numeric `version` field | 70 |
| SEA (`data["0.0"].mode = "Sea"`) | 69 |
| ROAD (`mode = "Truck"`) | 9 |
| AIR (`mode = "Air"`) | 4 |
| Mode absent/unknown | 13 |
| Shipments with nonempty `data["3.4"].details` | 80 |
| Finance detail line items (numerically populated buy/sell columns, *not verified/accounted*) | 223 |
| Shipments with nonempty `data["3.4"].payments` | 5 |
| Direct payment entries in those lists | 5 |
| Shipments carrying legacy finance `out` / `in` fields | 93 / 93 |
| Shipments carrying legacy `debt` / `paid` fields | 70 / 70 |
| `quotes` records | 1 |
| Quote with status `ACCEPTED` | 1 |
| Accepted quote with `customer_id` | 1 |
| Accepted quote with linked `shipment_id` | 0 |
| Accepted quote with `sent_versions` array | 0 |
| `contracts` / `agreements` | 9 / 1 |
| `financial_obligations`, `financial_transactions`, `financial_allocations`, `payment_receipts` | 0 / 0 / 0 / 0 |
| `customer_publications`, `public_events`, `public_documents` | 0 / 0 / 0 |
| `audit_logs` shipment updates with before/after | 61 |
| Of these 61 update events, finance detail-array snapshots differ | 52 |
| Of these 61 update events, finance payment-array snapshots differ | 3 |
| `audit_logs` quote entries | 0 |

**Evidence discipline:**
- 87 name-only matches are **NOT authorized `customer_id` links**, even if text is unique; no bulk auto-binding.
- Six discrepant `customer`/`client` name pairs need adjudication. None of the six simultaneously resolved to *different* existing customer IDs in the exact-name audit; that does not make them safe to auto-bind.
- 223 financial lines have numeric buy/sell fields but do **not** prove payable/receivable, FX, invoice, agreed quote, payment or bank evidence.
- 52 + 3 are changes detected between before/after **within 61 logged shipment update events**; this is not a claim of complete historic per-cost provenance.
- One existing `ACCEPTED` quote lacks `sent_versions`. Do **not** create fictitious historic sent documents.
- Collection counts and exact-name checks are snapshots, not validation of the production app's environment variables.

## 2. Single-source field mapping (G0 contract)

| Fact | Existing internal location | Intended trusted identity / source | Customer portal rule | Status |
| --- | --- | --- | --- | --- |
| Customer identity | `customers.id`; display `customers.name` | Immutable `customer_id`, legal-name history separate | Principal membership by ID only | BLOCKED: 91/95 shipments without valid ID |
| Shipment identity | `shipments.id` and `shipments.shipment_id` | Immutable `shipment_id` | Must bind to principal's exact `customer_id` | 95/95 IDs consistent |
| Cached customer name | `shipments.customer`, `shipments.client` | Display/legacy migration candidates, never auth | Legal and document snapshots not retro-edited | 6 mismatches need review |
| Transport mode | `shipments.data["0.0"].mode` | `Sea → SEA`, `Truck → ROAD`, `Air → AIR`; missing = UNKNOWN | Source mode-specific 00–06 labels; never infer from route string | 13 unknown, normalization required |
| Stage completion | internal execution profile, mode/load/service scope, evidence | Completion rule + evidence + human signoff where required | Only verified and allowed event; UNKNOWN/NOT_APPLICABLE != COMPLETED | Not connected |
| Quote identity | `quotes.id`, `quote_no`, `version`, `status`, `sent_versions` | Accepted revision + retained customer-facing document | **File link only**, signed and authorized per customer/lot/version; no amounts on Dashboard | Existing quote not versioned as sent |
| Quote/lot link | `shipments.quote_id`, quote `customer_id` | Exact ID relation after approval | Never join by customer name alone | 0/95 shipment quote links |
| Actual buy cost | `shipments.data["3.4"].details[].cost` | Internal actual expense, currency/evidence, actor + change reason | **PRIVATE** — no direct portal amount or history | 80 shipments with lines |
| Actual sell-side service line | `shipments.data["3.4"].details[].price` | Service receivable only after applicable invoice/obligation/review | Publish only approved receivable group, not price quote | Unverified as customer debt |
| Direct shipment payments | `shipments.data["3.4"].payments[]` | Stable request_id, anti-double-count reconciliation | Paid amount only after verified settlement/allocation | 5 entries, not yet reconciled to ledger |
| Ledger obligations | `financial_obligations` | SERVICE versus ENTRUSTED_GOODS distinct purpose | Approved obligation group; no mixing | Empty production collection |
| Ledger transactions | `financial_transactions` | Authenticated receipt/payment + beneficial owner | Show only after correct currency/party/lot binding | Empty |
| Allocation and corrections | `financial_allocations`, `financial_corrections` | Effective, reversible, immutable ledger history | `remaining = obligation − effective allocated receipts` per category/currency | No records ready |
| Customer document metadata | shipment attachment workflow / GridFS or Drive | Metadata and explicit approved version, no raw storage id | Owner-approved file/lot, streaming via server permission | Not yet linked |
| Internal change history | `audit_logs` on `save_shipment_atomic` | before/after, actor, timestamp, reason + evidence | **PRIVATE**: only explicitly approved change narratives visible to customer | Audit exists; reason/evidence not universally proven |
| Approved outbound data | `customer_publications`, `public_events`, `public_documents` | Customer+lot+version+authorized publish | Strict projection; no hidden internal data in payload | Empty in production |

## 3. Two distinct money histories

**Internal changes** (Trường Thành only): booked buy expense, changed quantities/FX, selling adjustments, cost variance, who/when/why/source. The initial accepted quote and released versions **must not be overwritten**. Cost correction carries a new audit/change event, not a silent `replace`.

**Customer-visible changes** (only after approval): revised customer *file* if sell terms changed, reconciled SERVICE and ENTRUSTED_GOODS obligations, confirmed customer payments, finance adjustments, and version/approval timestamps. Never expose cost, margin, internal negotiation or arbitrary audit before/after blobs. A change in internal buy cost does not itself authorize increased customer debt.

**Finance calculation:** keep each obligation/receipt's currency, purpose, status and effective allocation; an absent obligation is UNKNOWN, not 0. Invoice/obligation != quote estimate; direct payment != automatically allocated receipt. For mixed currencies, no arithmetic without a confirmed FX snapshot / conversion event.

## 4. G1 next bounded implementation gate

1. On an isolated task branch and test DB, add a **read-only link eligibility classifier** for all 95 source shipments. Output anonymized counts to shared evidence, and a controlled internal-review queue for the 87 name candidates + 4 missing. No automatic production UPDATE from exact name.
2. For **new** shipment writes, validate canonical `customer_id` and `quote_id` where the business relationship exists; handle legacy reads without automatic reassignment.
3. Show a reviewed `customer_id` and legal-name history separately; an approved rename must not silently change historical contracts/quote snapshots.
4. Add mode normalization from the actual `data["0.0"].mode` and UNKNOWN for 13 missing; all ROAD/SEA/AIR have tests; stage semantics scoped by `shipment_execution_profile.py`.
5. Add targeted negative tests: two customers same name, conflicting cached names, foreign customer_id, changed name, revoked portal user, old quote without sent_versions, buyer vs payer mismatch, and post-accepted buy-cost adjustment.
6. Run baseline vs candidate regression; require production-like *read-only* QA before permission-changing launch. A separate explicit Owner Gate is required for any live production data migration/write, customer grant, published file, or deployment.

**G1 acceptance:** 95/95 source shipments have one classified bucket (verified ID / needs review by name / unresolved); 0 auto-bind operations; 0 customer data cross-tenant exposure; non-matching/unknown conditions block client release; existing valid G1.5 Google/Journey preserved.

## 5. PR #226 hard blocker (currently draft, NOT merged)

The draft `arena/g15-approved-business-data-20261027` reader includes the customer-facing `quotes.calculation.selling_price_total_vnd` projection. This **contradicts Owner decision 5C**: no quote amounts on Dashboard. Do not merge PR #226 as-is.

Rework after G1 to:
- Replace amount publication with **authorized immutable quote document versions**, per recipient/customer/shipment and explicit grant, with server-side file access.
- Keep approved SERVICE and ENTRUSTED_GOODS debt balances separate from quote price.
- Derive journey completion from validated execution requirements; a lone approved event does not guarantee whole-stage completion.
- No auto-publication from raw `shipments` or `audit_logs`.

## 6. Security, scope and OE gate

**P2P_LAW_SOURCE:** CANONICAL_AUTHENTICATED (this actor read notebook main).  
**No mutation:** only Atlas count/aggregate/list; this report contains aggregate data and code field names, no customer names, per-lot identifiers, prices, credentials or storage references.  
**Không bị over engineering chứ?** SIMPLER_PATH=one audit report + reuse existing modules; MATERIAL_PROGRESS=95 links classified; NECESSITY=permission and finance integrity; CORE_BEFORE_SUPPORT=identity before file/finance; SMALLER_VERIFIABLE_SLICE=read-only G0 -> G1 test branch. `OE_VERDICT=DO_IT`.  
**Verdict:** `G0_SOURCE_MAPPING=PROVEN`, `G1_PRODUCTION_LINKAGE=NOT_READY`, `FINANCE_CUSTOMER_RELEASE=NOT_READY`, `PR226=HOLD`, `PRODUCTION_WRITE=NONE`.

**Recheck requirements:** Database contents can change after this snapshot; rerun counts and inspect live runtime DB identity before any authority-granting step. No customer ID mapping from name without responsible human approval.
