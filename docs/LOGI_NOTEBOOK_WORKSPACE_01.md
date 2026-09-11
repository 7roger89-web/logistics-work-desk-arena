# LOGI_NOTEBOOK_WORKSPACE_01 — `/so-tay` becomes a read-only handbook

Bounded activation of an existing placeholder. **Not** a CMS, wiki, knowledge
platform, RAG system or AI assistant. Read-only, one route, one presentation
adapter, no new store/router/API/database/search service.

## Decision gate

`NOTEBOOK_CAPABILITY_CLASSIFICATION = STATIC_CONTENT_READY`

The repository holds **no** curated SOP/handbook corpus, and the only
note-shaped content (`knowledge_base`) is per-deployment user data, not
authored reference material. Useful authoritative *static* operational
material does already exist — it is the reference data the running features
themselves use — and it needs no dedicated backend reader. `/so-tay` therefore
presents exactly that material, with no new content written in this task.

Rejected alternatives, with the reason:

| Option | Why not |
| --- | --- |
| `REAL_BACKED_READY` | would require asserting a curated handbook corpus exists; none does |
| Surface `knowledge_base` as "the handbook" | that collection is UGC notes, empty in staging, and its categories are not a content source |
| Seed starter articles | inventing customs/finance/workflow procedure was explicitly out of scope |
| Build a notes admin or markdown CMS | out of scope (§19) and unnecessary for read-only reference |

## Content map (all passthrough)

| Section | Existing source | Real material |
| --- | --- | --- |
| Luồng lô hàng | `core/config.py` `STATUS_OPTIONS/STATUS_LABELS/STATUS_MAP_FWD`; `views/logi_view_model.FIELD_PATHS` | 4 statuses with both app labels; stage → allowed-field map (the same whitelist that guards writes) |
| Chứng từ | `views/logi_real_data.document_checklist`; `core/docgen/rules` | the 4-item check frame; 4 doc types with their legal number/date keys, line limits and locked rule constants |
| Dịch vụ & mã phí | `core/config.GETFLY_SERVICES_LIST`, `INCOTERMS` | 27 service codes (code/name/unit/group); 11 accepted Incoterm values |
| Hải quan · tham chiếu | `core/trade_compliance/source_registry.json` via `load_official_source_registry()` | 3 official VN discovery sources with registry `version 0.1.0` and `evidence_status NOT_RETRIEVED` preserved |
| Công cụ & phân quyền | `core/config.CARRIER_LINKS`; `core/auth.ROLE_PERMISSIONS` | 12 carrier tracking URL templates; the full role → permission matrix |
| Ghi chú đội ngũ | `core/database.load_knowledge_base()` (existing reader) | whatever the deployment holds; displayed ≤ 60 with the true total stated |

Explicitly **not** displayed, because no source in the repo carries it: customs
rules, tax rates as legal claims, Incoterm rule definitions, finance/payment
procedures, step-by-step tutorials, internal policy text. The page states these
limits itself (`handbook.unavailable`).

## Architecture

```
core/config.py · core/docgen/rules.py · core/trade_compliance/sources.py
core/auth.py · views/logi_real_data.py · core/database.load_knowledge_base()
        → views/handbook.py            (bounded read-only projection, pure)
        → views/logi_view_model.py     ("handbook" section of the ONE payload)
        → component/src/lib/viewmodel.ts + store.tsx
        → component/src/pages/Notebook.tsx  (React, MemoryRouter route /so-tay)
```

* **No new backend event.** The content is static, so no server-side action is
  required: `ALL_EVENTS` is untouched (verified by test). Category selection,
  article open/back and the filter are local UI state.
* **Search is proportional**: one `<input type="search">` doing
  case-insensitive substring matching over the already-delivered text. No index,
  no full-text service, no embeddings.
* **No second content store**: the adapter imports the canonical constants and
  the one existing notebook reader; nothing is copied into a JSON/markdown
  file and no authoring path was created.
* **Bounded payload**: notes are capped at `MAX_NOTE_ENTRIES = 60`, with the
  true total shown, so a cap is never mistaken for the corpus.

## Provenance

Every section carries `source`, `version`, `updated`, `owner`, `note`. The only
versioned source in the repo is the trade-compliance registry (`0.1.0`), so that
is the only version displayed; `updated`/`owner` stay `None` and render as
"không có trong nguồn" rather than a manufactured date. Stored notes keep their
own recorded date, category, tags and `created_by/updated_by` author.
Legal/trade material is never labelled official: the registry's own
`NOT_RETRIEVED` evidence state is surfaced verbatim.

## Freshness

No source in the repository records an effective/expiry date for these
constants, so freshness is unknown and is not claimed. The docgen rules are
labelled with their own provenance (`LOG-DOCGEN-01 V1`, "locked business
rules"), i.e. internal rules of the document generator, not customs guidance.

## Navigation & mobile

* `Sắp có` removed **only** for `/so-tay`; `/nguoi-dung` keeps its honest marker
  (the consolidation DOM suite asserts the marker count is now 1).
* The sidebar hero promised "hướng dẫn từng bước" (step-by-step tutorials) —
  reworded to what the page actually is, so the chrome stays truthful.
* Phone behaviour: table rows become stacked cards below `48rem` (nothing forces
  horizontal scroll), long cells use `break-words`/`break-all`, search is
  `min-h-[48px]`, category chips `min-h-[44px]`, the back action is a labelled
  `touch-target`, and the layout is `min-w-0` at every grid level.
  `@media (min-width:48rem)` enclosure verified in the shipped CSS.

## Verification

* `tests/test_handbook.py` — 17 focused checks: per-section passthrough against
  the live constants, `document_checklist({})` equality, RBAC/registry
  passthrough, provenance never invents date/owner, empty-corpus honesty,
  bounded-note disclosure, no authoring/search surface, staging view-model bridge.
* `tests/component/dom_acceptance_handbook.mjs` — 11 checks on the real
  production bundle in jsdom with a staging-generated fixture: route activation,
  marker honesty, canonical values through an article walk, category chips,
  search + no-result, article open/back, empty vs real notes with their recorded
  metadata, mobile structural contract, neighbouring routes intact.
* `npm run typecheck` ✓ · `npm run build` ✓ · `npm run scan` →
  `FINAL_EXECUTABLE_PROCESS_REFERENCE_COUNT=0` ✓
* All 12 `tests/component/dom_acceptance_*.mjs` suites pass; the focused backend
  batch (handbook, phase A/B/C1, CEO, tariff, translation, reconciliation,
  partner context, docgen, auth/RBAC) passes.
* Live Preview: `python -m streamlit run app.py --server.port 8501
  --server.address 0.0.0.0` — `/so-tay` renders the handbook on staging
  (`SANDBOX_STAGING`, mongomock); `production DB never used`, no mutations.

## Repaired on the way (pre-existing staleness, not introduced here)

`tests/component/dom_acceptance_consolidation.mjs` still expected 3 "Sắp có"
markers while `main` had 2 since `LOGI_CEO_REPORT_01`, and still listed
`/bao-cao-ceo` as unbacked. Corrected to the true state (1 marker; CEO report and
the handbook counted as backed, each asserting its own honest no-data state for
that older fixture).

Known unrelated flake: `tests/test_logc15_auth_rbac.py::…unknown_role_falls_back_to_viewer`
fails when an earlier test leaves `st.session_state["current_user"]` set. It
reproduces on `main` combinations without any file from this change; this task's
own `staging` fixture restores the previous session value to avoid adding to it.
