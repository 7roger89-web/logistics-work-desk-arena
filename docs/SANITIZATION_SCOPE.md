# Sanitized repository scope

This repository is a clean application-only checkpoint built from the current verified
Logistics worktree through LOG-C12. It intentionally omits the old `.git` history,
credentials, local databases, logs, temporary evidence, test results, old archives,
P2P install backups, agent/editor runtime state, and unknown machine-specific files.

The copy preserves application entrypoints, `core/`, `views/`, tests, safe Playwright
flows, dependency files, Streamlit configuration without secrets, selected continuity
plans, and safe documentation. Do not add credential-bearing files or local runtime
artifacts to Git.
