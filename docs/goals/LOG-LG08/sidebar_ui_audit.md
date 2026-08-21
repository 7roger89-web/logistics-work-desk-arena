# Sidebar UI Audit & Root Cause Analysis

## Findings from User Screenshot
- The sidebar background is dark (Navy/Slate).
- Buttons (like "Việc Cần Xử Lý", "Tạo Lô Mới") appear as **white boxes with very faint light text** inside.
- This indicates the `st.button` background is being forced to white (or a very light color) while the text color remains light blue/white, resulting in near-zero contrast.
- The "Tổng Quan Công Việc" button (Primary) is a solid blue with white text, which is readable, but the secondary buttons are broken.

## Root Cause in CSS
In `web_app.py`, the current CSS injection for sidebar buttons is:
```css
[data-testid="stSidebar"] button {
    background-color: transparent !important;
    color: #D9E7F2 !important;
    ...
}
```
However, Streamlit's internal CSS for `secondary` buttons often uses a specific selector that might be winning over the generic `button` selector if not targeted correctly, or the `backgroundColor` from `config.toml` is being applied to the button surface in a way that `transparent !important` doesn't fully hide.

## Solution Strategy
1.  **Hard Override Sidebar Buttons:** Target `[data-testid="stSidebar"] [data-testid="baseButton-secondary"]` and `[data-testid="stSidebar"] [data-testid="baseButton-primary"]` explicitly.
2.  **Force Dark Surface:** Ensure the background is either truly transparent or a dark navy, and the text is forced to white.
3.  **Expander Contrast:** The expander headers (VẬN HÀNH, etc.) also need forced contrast to ensure they don't inherit light colors from the main theme.
4.  **Remove Conflict:** Ensure `dashboard.py` doesn't have any global button rules that leak into the sidebar.
