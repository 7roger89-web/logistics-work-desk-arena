# Local tariff reference data

The original `tariff.db` is deliberately not included in this sanitized repository.
Audit determined that it is a 13 MB SQLite reference database with no detected
credential or contact-data patterns, but its schema (`tariff`, `hs_notes`) does not
match the current application's `tariff_table` lookup query. It is therefore not a
required component for the application to boot or for the canonical LOG-C12 tests.

For development, initialize an empty compatible database:

```bash
python scripts/initialize_tariff_db.py --database data/tariff.db
```

To use approved tariff data later, obtain it through the organization's data-governance
process, validate schema and license, and set `TARIFF_DB_PATH` or the local Streamlit
secret to its local path. Never commit the populated database to this repository.
