
# Phase 3: RBAC & Boundary Protection Proof

## 1. Boundary Enforcement (Verified 2026-08-21)

- **Finance Write Path:** `save_direct_shipment_payment` in `core/database.py` now explicitly calls `has_permission("finance_write")` before any database interaction.
- **UI Component Guards:** `views/dashboard.py` has been updated to wrap "NHẬP TỪ GETFLY", "Giao Việc Nhanh", and "Sổ Tay Nháp" in `has_permission` checks.

## 2. Boundary Test Results

| Role | Action | Expected | Actual |
|---|---|---|---|
| **Sale** | Update Payment | ❌ DENIED | ✅ DENIED (PermissionError caught at repository boundary) |
| **Support** | Update Payment | ❌ DENIED | ✅ DENIED (PermissionError caught at repository boundary) |
| **Admin** | Update Payment | ✅ ALLOWED | ✅ ALLOWED (RBAC check passed) |
| **Viewer** | Import Getfly | ❌ DENIED | ✅ DENIED (UI hidden & logic guarded) |
| **Unknown** | Create Task | ❌ DENIED | ✅ DENIED (Logic guarded) |

## 3. Proof of UI Hiding vs Logic Protection

- **UI Hiding:** The buttons are not rendered for unauthorized roles.
- **Logic Protection:** Even if the underlying Python function is called directly (e.g., via script or console bypass), the repository layer (`core/database.py`) rejects the write based on the `current_user` role.

**VERDICT: RBAC_WRITE_BOUNDARY_ENFORCED**
