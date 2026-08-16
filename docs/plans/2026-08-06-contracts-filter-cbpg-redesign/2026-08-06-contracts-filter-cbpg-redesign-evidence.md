# Contracts, shipment filters, and CBPG redesign Evidence

## Evidence IDs

### E0-P0 — Baseline before implementation

- `E0-P0A-SRC1`: `views/dashboard.py` loads `created_at` with top-level precedence and calls `parse_date`, whose default is today; selected detail is read from `all_ships`, while list filtering uses `ships_filtered`.
- `E0-P0A-SRC2`: `core/utils.py` defines `parse_date_optional` and `parse_date`; invalid/missing values can become today's date through the default path.
- `E0-P0A-SRC3`: `views/contracts.py` detects linked shipments only from active `data.entrustment.contract_no`; the contract tabs expose bank/T/T and proxy payment separately and do not include the entrustment wallet.
- `E0-P0A-SRC4`: `views/tariff.py` uses one static exception option list for all categories; it displays a regenerated `ID` but persists editor output without a pure normalization contract.
- `E0-P0A-SRC5`: `core/database.py` has separate `contracts`, `proxy_payments`, and `entrustments` collections and no canonical contract transaction collection/index.
- `E0-P0A-TEST1`: existing repository tests cover database/logic/router behavior but contain no regression test for month filter date precedence, selected-detail persistence, or chair/table exception constraints.

## Baseline runtime notes

- The repository is a Streamlit + MongoDB app. Existing working-tree changes are preserved; this plan touches only scope files and new plan/report artifacts.
- Earlier direct data inspection found that business dates and Mongo insert dates disagree for some shipments; this is why the current-month count is not a trustworthy baseline until canonical date parsing is added.
- Docker availability and exact runtime command must be rechecked during P1/P2 validation and recorded here.

## Slice evidence log

| Evidence ID | Slice | Command / observation | Result |
|-------------|-------|-----------------------|--------|
| E1-P1A-TEST | P1-A | `python -m unittest discover -s tests -v` | 24 tests passed, including nested-date precedence and no-invented-today helpers |
| E1-P1A-SRC | P1-A | `views/dashboard.py`, `views/reports.py` and GetFly month export use `get_shipment_business_date`; active detail state uses stable dashboard keys | pass by source inspection |
| E1-P1B-TEST | P1-B | `tests/test_tariff.py` | 3 focused tests passed: sequential STT, category option separation, invalid legacy repair |
| E1-P2A-SRC | P2-A | `core/database.py` | socket and wait queue bounds plus shipment/contract transaction indexes present |
| E1-P2B-TEST | P2-B | `tests/test_contracts.py` and source inspection | 3 relationship tests passed; unified contract finance workspace present |
| E1-P2C-TEST | P2-C | `tests/test_contracts.py` and source inspection | direct many-shipment link plus legacy entrustment fallback passed |
| E1-Pn-UI | Pn | Streamlit on `http://localhost:8515` | previous-month option and 01/07/2026–31/07/2026 range passed; Contract route mounted; sidebar no longer exposes separate proxy/wallet routes |
| E1-Pn-DB | Pn | `python scripts/check_config.py`; app banner | Mongo SRV DNS timed out; DB write -> reload -> render not run |

## Evidence rules

- Prefer source, unit-test, and fresh-runtime evidence over screenshots alone.
- Any DB-backed UI change must prove write -> reload -> render for a safe test record or a read-only existing record.
- Do not print secrets, connection strings, or customer financial values in reports.
