# Contracts, shipment filters, and CBPG redesign Benchmark

## Baseline

| Metric | Baseline | Source |
|--------|----------|--------|
| Existing unit tests | 15/15 in prior repository run | `tests/` run from previous evaluation; refresh during this plan |
| Shipment load | about 1.3 s for 78 records in prior direct check | Mongo direct-read note; refresh without exposing secrets |
| Dashboard date source | top-level `created_at` preferred | `E0-P0A-SRC1` |
| Contract shipment relation | legacy active entrustment number only | `E0-P0A-SRC3` |

## Latest measurements

| Metric | Latest | Command / evidence |
|--------|--------|--------------------|
| Unit tests | pending | pending |
| Dashboard smoke | pending | pending |
| Contract link reload | pending | pending |
| CBPG row normalization | pending | pending |
| Docker/container validation | pending | pending / explicit blocker if unavailable |

## Comparison rule

Record correctness first (wrong rows or lost selection is a failure), then latency. A slower but bounded query is preferable to an unbounded spinner or a silent date fallback.
