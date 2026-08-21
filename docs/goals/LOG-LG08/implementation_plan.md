# LOG-LG08 Remaining Implementation

## Features to add (minimal affected surface):

### 1. "Việc của tôi" (My Work) — in views/dashboard.py
- Add to the task display section (lines 715-765)
- Show a third column/section filtered by current user
- Use display_name matching (current users all have user_id now, but legacy tasks use display_name)
- Label: "📌 Việc của tôi"

### 2. Global Search — in views/web_app.py
- Add a search input in sidebar (below brand, above nav groups)
- Search across: shipment IDs, customer names, task content, knowledge base
- Respect RBAC — only show results from routes user has permission to see
- Navigate to the matching item when clicked

### 3. Role-specific Dashboard emphasis — in views/dashboard.py
- Sales role: emphasize "Việc của tôi" + shipments relevant to their work
- Support role: emphasize tasks + operational queue
- Admin: full view (already the case)

### 4. Compact Navigation (collapsible groups) — in views/web_app.py
- Use st.expander for each nav group
- Only expand the group containing the active page

### 5. Role Truth Verification Tests — in tests/

## Files to modify:
- views/dashboard.py (my work section, role emphasis, assignee_user_id in add_task)
- views/web_app.py (global search, collapsible navigation)
- core/database.py (add assignee_user_id to add_task)
- tests/ (identity tests)
