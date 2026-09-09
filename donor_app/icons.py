"""SVG icon helpers — small inline icons used in the donor UI shell.

We keep these lightweight and inline so they don't depend on external CSS
or icon libraries. Each function returns an inline SVG string.
"""
from __future__ import annotations

def _wrap(path: str, size: int = 20, stroke: str = "currentColor", fill: str = "none", view_box: str = "0 0 24 24", extra: str = "") -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="{view_box}" fill="{fill}" stroke="{stroke}" stroke-width="2" '
        f'stroke-linecap="round" stroke-linejoin="round" {extra}>{path}</svg>'
    )

def search(size=20, stroke="currentColor"):
    return _wrap('<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>', size, stroke)

def bell(size=20, stroke="currentColor"):
    return _wrap('<path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/>', size, stroke)

def plus(size=20, stroke="currentColor"):
    return _wrap('<path d="M12 5v14M5 12h14"/>', size, stroke)

def menu(size=20, stroke="currentColor"):
    return _wrap('<path d="M4 6h16M4 12h16M4 18h16"/>', size, stroke)

def x(size=20, stroke="currentColor"):
    return _wrap('<path d="M18 6 6 18M6 6l12 12"/>', size, stroke)

def chevron_right(size=20, stroke="currentColor"):
    return _wrap('<path d="m9 18 6-6-6-6"/>', size, stroke)

def arrow_right(size=20, stroke="currentColor"):
    return _wrap('<path d="M5 12h14M12 5l7 7-7 7"/>', size, stroke)

def arrow_left(size=20, stroke="currentColor"):
    return _wrap('<path d="M19 12H5M12 19l-7-7 7-7"/>', size, stroke)

def layout(size=20, stroke="currentColor"):
    return _wrap('<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M9 21V9"/>', size, stroke)

def package(size=20, stroke="currentColor"):
    return _wrap('<path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><path d="M3.27 6.96 12 12.01l8.73-5.05M12 22.08V12"/>', size, stroke)

def file_text(size=20, stroke="currentColor"):
    return _wrap('<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6M16 13H8M16 17H8M10 9H8"/>', size, stroke)

def wallet(size=20, stroke="currentColor"):
    return _wrap('<path d="M19 7V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-2"/><path d="M3 5v14M21 12V9a2 2 0 0 0-2-2H7a2 2 0 0 0 0 4h12"/>', size, stroke)

def truck(size=20, stroke="currentColor"):
    return _wrap('<path d="M10 17h4V5H2v12h3"/><path d="M20 17h2v-3.34a4 4 0 0 0-1.17-2.83L19 9h-5"/><circle cx="7.5" cy="17.5" r="2.5"/><circle cx="17.5" cy="17.5" r="2.5"/>', size, stroke)

def calculator(size=20, stroke="currentColor"):
    return _wrap('<rect x="4" y="2" width="16" height="20" rx="2"/><path d="M8 6h8M8 10h.01M12 10h.01M16 10h.01M8 14h.01M12 14h.01M16 14h.01M8 18h.01M12 18h.01M16 18h.01"/>', size, stroke)

def handshake(size=20, stroke="currentColor"):
    return _wrap('<path d="m11 17 2 2a1 1 0 1 0 3-3"/><path d="m14 14 2.5 2.5a1 1 0 1 0 3-3l-3.88-3.88a3 3 0 0 0-4.24 0l-.88.88a1 1 0 1 1-3-3l2.81-2.81a5.79 5.79 0 0 1 7.06-.87l.47.28a2 2 0 0 0 1.42.25L21 4"/><path d="m21 3 1 11h-2"/><path d="M3 3 2 14l6.5 6.5a1 1 0 1 0 3-3"/><path d="M3 4h8"/>', size, stroke)

def building(size=20, stroke="currentColor"):
    return _wrap('<rect x="4" y="2" width="16" height="20" rx="2"/><path d="M9 22v-4h6v4M8 6h.01M16 6h.01M12 6h.01M12 10h.01M12 14h.01M16 10h.01M16 14h.01M8 10h.01M8 14h.01"/>', size, stroke)

def scale(size=20, stroke="currentColor"):
    return _wrap('<path d="M16 11h3l-3 9-3-9h3M2 16l3-6 3 6z"/><path d="M3 3h18M5 3v4h14V3"/>', size, stroke)

def bar_chart(size=20, stroke="currentColor"):
    return _wrap('<path d="M3 3v18h18"/><path d="M18 17V9M13 17V5M8 17v-3"/>', size, stroke)

def book(size=20, stroke="currentColor"):
    return _wrap('<path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2zM22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>', size, stroke)

def lang(size=20, stroke="currentColor"):
    return _wrap('<path d="m5 8 6 6M4 14l6-6 2-3M2 5h12M7 2h1M22 22l-5-10-5 10M14 18h6"/>', size, stroke)

def shield(size=20, stroke="currentColor"):
    return _wrap('<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/><path d="m9 12 2 2 4-4"/>', size, stroke)

def users(size=20, stroke="currentColor"):
    return _wrap('<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/>', size, stroke)

def file_check(size=20, stroke="currentColor"):
    return _wrap('<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6M9 15l2 2 4-4"/>', size, stroke)

def eye(size=20, stroke="currentColor"):
    return _wrap('<path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7z"/><circle cx="12" cy="12" r="3"/>', size, stroke)

def pen(size=20, stroke="currentColor"):
    return _wrap('<path d="M12 20h9M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4z"/>', size, stroke)

def download(size=20, stroke="currentColor"):
    return _wrap('<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"/>', size, stroke)

def trash(size=20, stroke="currentColor"):
    return _wrap('<path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M10 11v6M14 11v6"/>', size, stroke)

def circle_check(size=20, stroke="currentColor"):
    return _wrap('<circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/>', size, stroke)

def circle_alert(size=20, stroke="currentColor"):
    return _wrap('<circle cx="12" cy="12" r="10"/><path d="M12 8v4M12 16h.01"/>', size, stroke)

def alert_triangle(size=20, stroke="currentColor"):
    return _wrap('<path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><path d="M12 9v4M12 17h.01"/>', size, stroke)

def info(size=20, stroke="currentColor"):
    return _wrap('<circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/>', size, stroke)

def map_pin(size=20, stroke="currentColor"):
    return _wrap('<path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0z"/><circle cx="12" cy="10" r="3"/>', size, stroke)

def phone(size=20, stroke="currentColor"):
    return _wrap('<path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>', size, stroke)

def clock(size=20, stroke="currentColor"):
    return _wrap('<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>', size, stroke)

def check(size=20, stroke="currentColor"):
    return _wrap('<path d="M20 6 9 17l-5-5"/>', size, stroke)

def layers(size=20, stroke="currentColor"):
    return _wrap('<path d="M12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 3.91a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 0-1.83Z"/><path d="M2 12a1 1 0 0 0 .58.91l8.6 3.91a2 2 0 0 0 1.65 0l8.58-3.9A1 1 0 0 0 22 12M2 17a1 1 0 0 0 .58.91l8.6 3.91a2 2 0 0 0 1.65 0l8.58-3.9A1 1 0 0 0 22 17"/>', size, stroke)

def circle_help(size=20, stroke="currentColor"):
    return _wrap('<circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3M12 17h.01"/>', size, stroke)

def filter_icon(size=20, stroke="currentColor"):
    return _wrap('<path d="M3 6h18M7 12h10M10 18h4"/>', size, stroke)

def plus_circle(size=20, stroke="currentColor"):
    return _wrap('<circle cx="12" cy="12" r="10"/><path d="M12 8v8M8 12h8"/>', size, stroke)

def ban(size=20, stroke="currentColor"):
    return _wrap('<circle cx="12" cy="12" r="10"/><path d="m4.93 4.93 14.14 14.14"/>', size, stroke)

def octagon_alert(size=20, stroke="currentColor"):
    return _wrap('<path d="M7.86 2h8.28L22 7.86v8.28L16.14 22H7.86L2 16.14V7.86z"/><path d="M12 8v4M12 16h.01"/>', size, stroke)

# Sidebar navigation icons
NAV_ICONS = {
    "layout": layout,
    "package": package,
    "file_text": file_text,
    "wallet": wallet,
    "truck": truck,
    "users": users,
    "handshake": handshake,
    "calculator": calculator,
    "scale": scale,
    "building": building,
    "bar_chart": bar_chart,
    "book": book,
    "lang": lang,
    "shield": shield,
    "circle_check": circle_check,
    "clock": clock,
    "alert_triangle": alert_triangle,
    "package_check": circle_check,
    "file_warning": file_text,
}
