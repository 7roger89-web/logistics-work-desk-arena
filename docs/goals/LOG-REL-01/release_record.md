# LOG-REL-01 RELEASE RECORD: ENVIRONMENT ISOLATION

**Date:** Aug 21, 2026
**Status:** COMPLETED
**Release Lane:** Preview/Staging -> Production

## 1. Environment Configuration

| Environment | Branch | Database | App URL | Identity Badge |
| :--- | :--- | :--- | :--- | :--- |
| **Production** | `production` | `logistics_db` | https://tienthanhlog.streamlit.app/ | (None) |
| **Preview** | `main` | `logistics_staging` | https://logisticspro-1.streamlit.app/ | 🛠️ PREVIEW / STAGING |

## 2. Technical Implementation

- **Environment Detection:** Added `ENV_IDENTITY` and `MONGO_DB_NAME` logic to `core/config.py`.
- **Write Protection:** Implemented mandatory database identity validation in `core/database.py` to prevent cross-environment writes.
- **UI Safety:** Added conditional badge rendering in `views/web_app.py` based on `ENV_IDENTITY`.
- **Database Separation:** Created `logistics_staging` on MongoDB Atlas as a snapshot of Production.

## 3. Verification Results

- **Isolation Test:** PASS (Verified that writes to Staging do not affect Production).
- **Git Sync:** `main` and `production` branches are correctly aligned.
- **Security:** Credentials remain rotated and hidden from Git history.

## 4. Operational Procedure

1. **Development:** Commit changes to `main` branch.
2. **Preview:** Verify changes on https://logisticspro-1.streamlit.app/ using Staging data.
3. **Promotion:** Merge `main` to `production` only after explicit Owner approval.

---
**Verdict:** LOG_REL_01_ISOLATION_VERIFIED
