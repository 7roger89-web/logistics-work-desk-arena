# LOGI_USER_ACCESS_WORKSPACE_01 — `/nguoi-dung` becomes a read-only user/access workspace

Bounded activation of an existing placeholder using ONLY the authentication,
user and RBAC capability that already exists in Logistics Work Desk. **Not** an
auth rewrite, **not** an IAM platform, **not** SSO, **not** a new identity
database. Read-only, one route, one presentation adapter, no new store, router,
API or permission framework.

## Decision gate

`USER_ACCESS_CLASSIFICATION = READ_ONLY_READY`

The repository already owns a real, mature auth/user/RBAC stack:

| Capability | Canonical source (reused unchanged) |
| --- | --- |
| Authoritative user store | `core.database.load_users()` — the same reader `core.auth` authenticates against |
| User document model / public view | `core.users` — `public_identity()` is a pick-list (user_id, username, display_name, email, role, active); hashing is PBKDF2-SHA256 |
| Authentication | `core/auth.py` — `require_login`, `_authenticate`, session identity |
| RBAC | `core/auth.ROLE_PERMISSIONS` — the single role → permission matrix (admin/sale/support + legacy accounting/operations/sales/viewer) |
| Account writers | `core.database.save_user / update_user / delete_user` — admin-gated (`*`), audited with `redact_password_material` |
| Auth mode | `core.config.AUTH_REQUIRED` (off ⇒ single Local Admin account) |
| Current user | `core.auth.current_user()` — already shown in the shell header |

Canonical writers exist and are admin-gated, but **no UI write channel is
exposed**, because the WRITE PATH HARD GATE cannot be fully proven from
existing behavior alone: the boundary set includes legacy roles (e.g.
`operations`, `viewer`) whose intentional clearance is only partially recorded,
and there is no existing canonical guard against an admin demoting/deactivating
themselves into lockout. Per the task law: any failed condition ⇒ READ-ONLY
ONLY. `WRITE_EXPOSED = NO`.

## What the page shows (all passthrough, zero invention)

- Accounts read through `load_users()` and delivered ONLY as the canonical
  `public_identity` fields — password material never enters the payload, not
  even masked (pick-list, not block-list; unknown source fields are dropped).
- The verbatim `ROLE_PERMISSIONS` matrix: permission chips per role, the admin
  `*` surfaced as "toàn quyền" (never as a permission name), assignable roles
  (`core.users.SUPPORTED_ROLES`) labelled separately from legacy roles.
- The real auth mode: `AUTH_REQUIRED` off ⇒ an explicit Local Admin note
  ("KHÔNG phải đăng nhập đa người dùng"); on ⇒ multi-user MongoDB login.
- The current-user indicator (same identity the header already shows).
- Honest empty state when the deployment has no accounts; honest truncation
  cap (`MAX_USERS = 100`) with the true total stated.
- A scope box stating exactly what the page does NOT do (no create/update/
  deactivate/reset/role-assignment, no secrets, no new roles).

Never displayed: password hashes, tokens, API keys, session material, internal
security metadata.

## Bridge (unchanged architecture)

    views/user_access.py (bounded projection, pure build)
      → views/logi_view_model.build_view_model() "userAccess" slice
        (bounded _users_reader over the EXISTING load_users reader)
      → existing React page component/src/pages/UserAccess.tsx
      → route /nguoi-dung + nav marker removal (component/src/App.tsx,
        component/src/lib/data.ts)

No event was added to the dispatcher (nothing to dispatch — the page writes
nothing), no second user route, no new API/router/store/design system.

## Verification

- `tests/test_user_access_workspace.py` — 16 focused tests: passthrough
  equality with `public_identity`/`public_summary`, credential-material
  absence (values and field names), unknown-field dropping, honest empty
  state, bounded payload, matrix verbatim equality, legacy-role separation,
  current-user indicator, Local Admin honesty, scope statements, no
  user-management event, staging view-model exposure.
- `tests/component/dom_acceptance_user_access.mjs` — 10 DOM checks on the
  production bundle (route activation, marker removal, honest empty state,
  account cards, secret-free DOM, no write controls, matrix verbatim,
  current-user + auth-mode truth, mobile card structure, neighbouring routes).
- `npm run typecheck`, `npm run build`, `scripts/scan_process.py` (0
  executable references), secret-marker scan over sources/fixtures/bundle.
- Streamlit preview on sandbox/staging only — no production mutation.
