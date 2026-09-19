# LOGI_COMPANY_IDENTITY_TRUTH_01 — Company display identity vs legal identity

Durable record for issue #69. Owner fact (durable): the operating/display
company is **Trường Thành Logistics**; the company is **NOT** Phú Anh Logistics.

## The authority split (proven)

| Identity kind | Authority | Consumed by |
| --- | --- | --- |
| **DISPLAY** (ordinary product surfaces) | `core.config.DISPLAY_COMPANY_NAME` — ONE bounded setting (env `DISPLAY_COMPANY_NAME` → secrets `[display].company_name` → default `Trường Thành Logistics`), delivered to the shell through the existing view-model `environment.displayName` channel | browser tab title (`views/web_app.py`), login card (`core/auth.py`), shell header subtitle (`component/src/components/Layout.tsx`) |
| **LEGAL** (contracts / payments / PXK / GNT documents) | `authority_companies` master via `core.database.load_authority_companies()` — UNCHANGED | `views/contracts.py` (BÊN MUA picker), `views/docgen.py` + `core/docgen/generator.py` (HDNT/HDMB/PXK/PL party facts), `views/logi_view_model._company_party()` (payer company) |

No legal fact (statutory name, tax code, address, representative, bank) was
invented, altered, or replaced by the display brand. The brand string is never
hard-coded inside the React bundle: without a vm value the header subtitle
degrades to a truthful unbranded `Nội bộ`.

## Audit — every "Phú Anh" occurrence, classified

| Location | What it says | Classification | Action |
| --- | --- | --- | --- |
| `views/web_app.py` (page title) | `Phú Anh Logistics · Nội bộ` | DISPLAY_BRAND (wrong) | replaced by DISPLAY authority |
| `core/auth.py` login card subtitle | `Phú Anh Logistics · Nội bộ` | DISPLAY_BRAND (wrong) | replaced by DISPLAY authority |
| `component/src/components/Layout.tsx` header subtitle (+ committed `component/dist` bundle) | `Phú Anh Logistics · Nội bộ` | DISPLAY_BRAND (wrong) | vm-sourced DISPLAY authority; bundle rebuilt |
| `playwright/acceptance_phase_a.py` STEP 2 | asserted the old brand subtitle | evidence tooling encoding the wrong brand | updated to `Trường Thành Logistics · Nội bộ` |
| `tests/component/dom_acceptance_phase_a.mjs` STEP 2 | asserted the old brand subtitle | evidence tooling encoding the wrong brand | updated + negative guard added |
| `component/src/components/Layout.tsx` footer | `CÔNG TY TNHH GIAO NHẬN QUỐC TẾ TRƯỜNG THÀNH · Đại lý: Phú Anh Logistics Việt Nam` | LEGAL attribution — names the authority_companies legal entity first; agent clause mirrors the `authority_agents` partner master | UNCHANGED |
| `component/src/pages/PartnerPayables.tsx` search placeholder | `đối tác (Phú Anh)` — example of a *partner* query | SAMPLE_LABEL, data-consistent (AGT-PHUANH is a real agent record) | UNCHANGED |
| `views/logi_seed.py` (9×) | contract `agent: "Đại lý: Phú Anh Logistics VN"`, shipment `declarant` | FIXTURE_ONLY — consumed solely by `tests/test_phase_a_component.py`; fixtures are hash-versioned | UNCHANGED |
| `tests/component/fixtures/view_model_*.json` | `AGT-PHUANH` / `CÔNG TY TNHH PHÚ ANH LOGISTICS` as agent/partner records | FIXTURE_ONLY mirror of the legal agent master | UNCHANGED |
| `views/logi_staging_seed.py` `AUTHORITY_AGENTS` | `AGT-PHUANH` = `CÔNG TY TNHH PHÚ ANH LOGISTICS` | LEGAL agent master record (partner of the company) | UNCHANGED |
| `tests/test_gnt_and_docgen_reality_check.py` | fabricated `CÔNG TY TNHH PHÚ ANH LOGISTICS` company record fed to docgen | FIXTURE_ONLY evidence that document generation renders whatever the master says (data-driven, not hard-coded) | UNCHANGED |
| `tests/component/fixtures/view_model_phase_a.json` | old vm snapshot | LEGACY_UNUSED (no consumer) | UNCHANGED |
| repo root `logo.png` | — | LEGACY_UNUSED (referenced nowhere) | UNCHANGED |

Root cause of the wrong brand: three hard-coded "Phú Anh Logistics · Nội bộ"
brand strings in the shell/login/tab-title surfaces (donor-app residue), plus
the same brand encoded in two acceptance scripts. The legal/business party
authority (`authority_companies`) was NEVER Phú Anh in any repo-visible copy —
every contract/payment/docgen path already derives from it.

## Production legal master

`PRODUCTION_LEGAL_MASTER_CORRECTION_REQUIRED=UNPROVEN` — this sandbox has no
production MongoDB access and no repo-visible evidence that the production
`authority_companies.legal_name` is Phú Anh (all traceable copies — staging
seed, tests, docgen flows — carry the Trường Thành company record). Owner
should confirm the live master record once; no production data was read or
mutated here.

## Evidence (P2P evidence-first)

- `tests/test_logi_company_identity_01.py` (10 focused tests): display
  authority default + env/secrets override precedence; login card carries the
  brand and never Phú Anh; AUTH gate boots without rendering Phú Anh; vm
  `environment.displayName` == the authority; payer `_company_party()` follows
  the authority master verbatim and fails closed with no master (no invented
  identity); staging legal master keeps its statutory fields intact; Phú Anh
  exists only as the agent master record.
- `tests/component/dom_acceptance_company_identity.mjs` (5 checks): REAL
  bundle source has no hard-coded operating brand; header subtitle renders
  `Trường Thành Logistics · Nội bộ` from the vm channel; old brand rendered
  nowhere; legal/attribution footer unchanged; truthful unbranded degradation
  without a vm value.
- Updated lanes: `dom_acceptance_phase_a.mjs` (32 checks PASS),
  `playwright/acceptance_phase_a.py`; neighbors re-run PASS:
  `dom_acceptance_partner_context.mjs` (13), `dom_acceptance_home_hierarchy.mjs`
  (5), `dom_acceptance_contract_core_edit.mjs` (8).
- Typecheck: `component && npm run typecheck` (tsc) PASS. Build: `npm run build`
  PASS (dist committed). Real-path boot: `streamlit run app.py` on scratch port
  9501 → HTTP 200, clean stop.
- Full pure suite differential (baseline vs change, same runner): zero new
  failures (1071 passed / 44 skipped / 14 pre-existing failures identical to
  main, incl. the stale `test_partner_reconciliation_desk_write_oracle` ROUTES
  import and the stale `dom_acceptance_consolidation.mjs` home-hero assertion).

## Safety

`PRODUCTION_MUTATIONS=0`, `PILOT_MUTATIONS=0`, no secrets changed
(`.streamlit/secrets.toml.example` documents the optional display key only),
no deploy, no `logistics_db`/`tienthanhlog` touch, no unrelated UI redesign.
