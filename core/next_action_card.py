"""Next-action card helper cho LOG-LG04.

Hiển thị "Việc tiếp theo" nổi bật theo mức độ với viền màu, icon, lý do và
người cần làm — không dựa vào màu sắc duy nhất (dùng viền dày + icon + chữ đậm).
Chỉ đọc (read-only presentation); không mutate dữ liệu.

Quy ước dữ liệu next_action (từ build_shipment_workspace_view):
{
  "code": "FREE_TIME_EXPIRING" | ...,
  "severity": "critical" | "warning" | "normal" | "info",
  "label": "Việc gì",
  "detail": "Vì sao",
  "source": "nguồn dữ liệu",
  "who": "ai cần làm (tuỳ chọn)",
}
"""

from __future__ import annotations

import streamlit as st

_ACTION_THEME = {
    "critical": {
        "border": "#C81E1E",
        "bg": "#FDECEC",
        "icon": "🚨",
        "level": "NGHIÊM TRỌNG",
    },
    "warning": {
        "border": "#B45309",
        "bg": "#FEF3E2",
        "icon": "⏰",
        "level": "CẦN XỬ LÝ SỚM",
    },
    "normal": {
        "border": "#0B6E99",
        "bg": "#F0F7FA",
        "icon": "✅",
        "level": "CÔNG VIỆC TIẾP THEO",
    },
    "info": {
        "border": "#475467",
        "bg": "#F6F8FA",
        "icon": "📋",
        "level": "GỢI Ý KIỂM TRA",
    },
}


def _value(value: object) -> str:
    if value is None or value == "":
        return "Chưa có thông tin"
    return str(value)


def _workspace_value(value: object) -> str:
    """Tương thích UNKNOWN marker của shipment workspace."""
    if value is None or value == "":
        return "UNKNOWN"
    return str(value)


def render_next_action_card(
    action: object,
    *,
    anchor: str | None = None,
) -> None:
    """Render card VIỆC TIẾP THEO nổi bật.

    ``anchor`` (tuỳ chọn) là tên bookmark HTML để "Xử lý ngay" cuộn tới khối
    nhập liên quan. Bookmark đặt bằng ``st.markdown(f'<a id="{anchor}">')``.
    """

    action = action or {}
    severity = action.get("severity") if isinstance(action, dict) else None
    theme = _ACTION_THEME.get(str(severity), _ACTION_THEME["info"])
    label = _value(action.get("label") if isinstance(action, dict) else None)
    detail = _value(action.get("detail") if isinstance(action, dict) else None)
    who = action.get("who") if isinstance(action, dict) else None
    source = action.get("source") if isinstance(action, dict) else None

    st.markdown(
        f"""
        <style>
        .lg04-next-card {{
            border: 3px solid {theme['border']};
            border-radius: 12px;
            background: {theme['bg']};
            padding: .9rem 1.1rem;
            margin: .4rem 0 .9rem;
        }}
        .lg04-next-card .kicker {{
            color: {theme['border']}; font-size: .72rem; font-weight: 900;
            letter-spacing: .12em;
        }}
        .lg04-next-card .task {{
            color: #102A43; font-size: 1.25rem; font-weight: 900; line-height: 1.2;
            margin: .2rem 0 .35rem;
        }}
        .lg04-next-card .why {{ color: #475467; font-size: .9rem; }}
        .lg04-next-card .who {{ color: #102A43; font-size: .85rem; font-weight: 800; margin-top: .3rem; }}
        @media (prefers-reduced-motion: reduce) {{
            *, *::before, *::after {{
                transition-duration: .01ms !important;
                animation-duration: .01ms !important;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="lg04-next-card">
            <div class="kicker">{theme['icon']} VIỆC TIẾP THEO · {theme['level']}</div>
            <div class="task">{label}</div>
            <div class="why">{detail}</div>
            {f"<div class='who'>👤 Người cần làm: {_value(who)}</div>" if who else ""}
        </div>
        """,
        unsafe_allow_html=True,
    )

    if source not in (None, "", "UNKNOWN"):
        st.caption(f"Nguồn: {_workspace_value(source)}")

    jump_label = "⬇ Xử lý ngay" if anchor else None
    if anchor and st.button(
        jump_label,
        key=f"lg04_next_action_jump_{anchor}",
        use_container_width=False,
    ):
        st.markdown(
            f"""
            <script>
            const target = document.getElementById('{anchor}');
            if (target) {{ target.scrollIntoView({{behavior: 'smooth', block: 'start'}}); }}
            </script>
            """,
            unsafe_allow_html=True,
        )
