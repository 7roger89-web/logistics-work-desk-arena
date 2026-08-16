# Sanitization verification

This application-only copy was created from the verified current Logistics worktree through LOG-C12. The original repository and its Git history were not copied or modified.

## Security checks

The sanitized project was scanned for private-key blocks, common cloud/API token formats, credential-bearing MongoDB URIs, and generic secret assignments. No credential-specific pattern was found, and prohibited paths such as `google_key.json`, `.streamlit/secrets.toml`, secret variants, the legacy `.git` directory, logs, P2P/agent state, archives, `tariff.db`, and test result directories are absent.

Twelve generic assignment-pattern detections remain in application configuration, tests, and input/utility code. They are code constructs for reading configuration or accepting input, not copied credential values. No secret value is recorded in this repository.

## Test checks

From this sanitized directory, the following checks passed:

- Python compile check for application, core, views, tests, and scripts.
- Full canonical Python test suite.
- Focused Dashboard, Shipment 360, Entity Context, Review Queue, Finance Review, Sales & Quotation, LOG-C12 host-native, and financial write-safety coverage.

## Local tariff data

The legacy `tariff.db` is intentionally excluded. It is initialized locally only when needed through `scripts/initialize_tariff_db.py`; see `data/README.md`.

## Git policy

The repository uses a new `.gitignore` that excludes local credentials, runtime artifacts, backups, local databases, and machine-specific agent/editor state. Do not force-push, publish, or add real credentials to this repository.
