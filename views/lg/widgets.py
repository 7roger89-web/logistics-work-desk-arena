"""HTML/Streamlit building blocks shared by the donor pages."""
from __future__ import annotations

from typing import Any, Iterable

from core.utils import safe_float

from .helpers import UNKNOWN
from . import theme


def _esc(value: Any) -> str:
    return theme.esc(value)


def badge(text: str, tone: str = "gray", size: str = "md", dot: bool = False) -> str:
    cls = theme.TONE_CLASS.get(tone, "b-gray")
    dot_html = f'<span class="dot {theme.DOT_CLASS.get(tone,"d-gray")}"></span>' if dot else ""
    return (
        f'<span class="lg-badge {cls} {size}">{dot_html}'
        f'{_esc(text or UNKNOWN)}</span>'
    )


def badge_html(label: str, tone: str = "gray", size: str = "md") -> str:
    return badge(label, tone, size=size)


def icon_badge(emoji: str, label: str, tone: str = "gray", title: str = "") -> str:
    t = f' title="{_esc(title)}"' if title else ""
    return (
        f'<span class="lg-badge {theme.TONE_CLASS.get(tone,"b-gray")}"{t}>'
        f'<span style="font-size:14px;line-height:1">{emoji}</span>{_esc(label)}</span>'
    )


def section_title(emoji: str, title: str, sub: str = "", right: str = "") -> str:
    ic = f'<span class="lg-t-ic">{emoji}</span>' if emoji else ""
    sub_html = f"<p>{_esc(sub)}</p>" if sub else ""
    right_html = f'<div class="lg-t-r">{right}</div>' if right else ""
    return (
        f'<div class="lg-title">{ic}<div><h2>{_esc(title)}</h2>{sub_html}</div>'
        f"{right_html}</div>"
    )


def card(title: str, body: str, emoji: str = "", sub: str = "", pad: bool = True) -> str:
    head = ""
    if title:
        sub_html = f'<div class="lg-muted" style="font-size:13px">{_esc(sub)}</div>' if sub else ""
        head = (
            f'<div class="lg-spread" style="margin-bottom:10px">'
            f'<div><b style="font-size:14.5px;color:#0f2a4a">{emoji} {_esc(title)}</b>{sub_html}</div></div>'
        )
    cls = "lg-card lg-card-pad" if pad else "lg-card"
    return f'<div class="{cls}">{head}{body}</div>'


def kpi(emoji: str, label: str, value: str, sub: str = "", solid: str | None = None) -> str:
    tone_cls = f" solid-{solid}" if solid else ""
    sub_html = f'<div class="k-sub">{_esc(sub)}</div>' if sub else ""
    return (
        f'<div class="lg-kpi{tone_cls}"><div style="display:flex;justify-content:space-between;'
        f'align-items:center">{_esc(emoji)}<span class="k-label">{_esc(label)}</span></div>'
        f'<div class="k-value">{_esc(value)}</div>{sub_html}</div>'
    )


def na_banner(tone: str, kicker: str, title: str, detail: str, icon: str = "!", action_html: str = "") -> str:
    ic_style = {
        "green": "background:#059669", "red": "background:#dc2626",
        "amber": "background:#d97706", "blue": "background:#2563eb",
    }
    ic_bg = ic_style.get(tone, "background:#2563eb")
    act = f'<div class="miss-act">{action_html}</div>' if action_html else ""
    return (
        f'<div class="lg-na na-{tone}"><div class="na-ic" style="{ic_bg}">{_esc(icon)}</div>'
        f'<div style="flex:1;min-width:220px"><p class="na-k">{_esc(kicker)}</p>'
        f'<p class="na-t">{_esc(title)}</p><p class="na-d">{_esc(detail)}</p></div>{act}</div>'
    )


def missing_box(what: str, where: str = "", action_label: str = "") -> str:
    act = (
        f'<span class="lg-btn lg-btn-white lg-btn-sm">{_esc(action_label)}</span>'
        if action_label
        else ""
    )
    where = f" · {_esc(where)}" if where else ""
    return (
        f'<div class="lg-missing"><span style="font-size:18px">⚠️</span>'
        f'<div><b>{_esc(what)}</b>{where}</div>{act}</div>'
    )


def state_rows(rows: Iterable[tuple[str, Any, str]]) -> str:
    html = []
    for label, value, tone in rows:
        v = _esc(value if value is not None else "")
        html.append(
            f'<div class="lg-state"><div class="sl">{_esc(label)}</div>'
            f'<div class="sv">{v}</div></div>'
        )
    return "".join(html)


def fmt_money(v: Any, currency: str = "VND") -> str:
    if v is None:
        return UNKNOWN
    num = safe_float(v)
    if num is None:
        return UNKNOWN
    return (f"{num:,.0f} ₫" if currency == "VND" else f"{num:,.2f} {currency}")
