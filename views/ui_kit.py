"""Shared presentation kit for the hybrid (logistics-demo donor) UI.

Everything in this module is presentation only: HTML/CSS helpers rendered with
``st.markdown``.  No helper reads or writes business data, no helper touches
``st.session_state`` and nothing here is imported by ``core``.

Design tokens (cloned from the logistics-demo donor):

    navy-900 #061024  navy-800 #0b2545  navy-700 #123168  navy-600 #1c4482
    navy-500 #2c5aa0  blue-500 #2f6fed  blue-600 #1d54c9
    green #16a34a  amber #d97706  red #dc2626
    bg #eef2f8  surface #ffffff  line #e2e8f0
    ink #0f1c33  muted #4b5b72  faint #8695a8
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from html import escape
from typing import Any

import streamlit as st

TONES = ("neutral", "info", "ok", "warn", "danger", "navy")

_TONE_ICON = {
    "ok": "check_circle",
    "warn": "warning",
    "danger": "error",
    "info": "info",
    "neutral": "radio_button_unchecked",
    "navy": "flag",
}

# ---------------------------------------------------------------------------
# CSS shared by every page (injected once per run by views.web_app)
# ---------------------------------------------------------------------------
COMPONENT_CSS = """
/* ---- material ligature icon ---- */
.lg-ico { font-family: 'Material Symbols Rounded'; font-weight: normal; font-style: normal; font-size: 1.05em; line-height: 1; display: inline-block; vertical-align: -0.14em; white-space: nowrap; letter-spacing: normal; text-transform: none; -webkit-font-feature-settings: 'liga'; font-feature-settings: 'liga'; -webkit-font-smoothing: antialiased; }

/* ---- page header ---- */
.lg-page-head { display: flex; flex-wrap: wrap; align-items: flex-end; justify-content: space-between; gap: .5rem 1rem; margin: 0 0 .85rem; }
.lg-kicker { color: var(--lg-blue-600); font-size: .66rem; font-weight: 800; letter-spacing: .14em; text-transform: uppercase; margin-bottom: .2rem; }
.lg-partner-card { display: flex; align-items: center; gap: .8rem; flex-wrap: wrap; background: var(--lg-surface); border: 1px solid var(--lg-line); border-radius: 14px; padding: .8rem 1rem; margin: .4rem 0 .7rem; box-shadow: 0 1px 2px rgba(6,16,36,.04); }
.lg-partner-avatar { width: 44px; height: 44px; border-radius: 12px; background: var(--lg-navy-700); color: #fff; font-weight: 800; display: flex; align-items: center; justify-content: center; letter-spacing: .04em; flex: 0 0 auto; }
.lg-partner-name { font-weight: 800; color: var(--lg-navy-800); font-size: 1.05rem; line-height: 1.2; }
.lg-partner-sub { color: var(--lg-muted); font-size: .8rem; }
.lg-partner-card .lg-badge { margin-left: .1rem; }
.lg-page-head { display: block !important; padding-bottom: .15rem; }
.lg-page-head > div { display: block; width: 100%; }
.lg-page-title { color: var(--lg-navy-800); font-size: 1.6rem; line-height: 1.15; font-weight: 800; margin: 0; padding: 0; letter-spacing: -.01em; }
.lg-page-head h1.lg-page-title { padding: 0; margin: 0; }
.lg-page-sub { color: var(--lg-muted); font-size: .86rem; margin-top: .3rem; line-height: 1.45; }
.lg-page-badges { display: flex; flex-wrap: wrap; gap: .35rem; margin-top: .45rem; }

/* ---- summary cards ---- */
.lg-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: .65rem; margin: .35rem 0 .9rem; }
.lg-card { background: var(--lg-surface); border: 1px solid var(--lg-line); border-radius: 10px; padding: .8rem .95rem; box-shadow: 0 1px 2px rgba(6, 16, 36, .04); min-width: 0; }
.lg-card-label { color: var(--lg-muted); font-size: .66rem; font-weight: 800; letter-spacing: .08em; text-transform: uppercase; display: flex; align-items: center; gap: .3rem; }
.lg-card-value { color: var(--lg-navy-800); font-size: 1.32rem; font-weight: 800; line-height: 1.15; margin-top: .3rem; word-break: break-word; }
.lg-card-hint { color: var(--lg-faint); font-size: .72rem; margin-top: .25rem; line-height: 1.35; }
.lg-card--ok .lg-card-value { color: #15803d; }
.lg-card--warn .lg-card-value { color: #b45309; }
.lg-card--danger .lg-card-value { color: #b91c1c; }
.lg-card--info .lg-card-value { color: var(--lg-blue-600); }
.lg-card--navy { background: var(--lg-navy-800); border-color: var(--lg-navy-800); }
.lg-card--navy .lg-card-label { color: #b7c7e3; }
.lg-card--navy .lg-card-value { color: #fff; }
.lg-card--navy .lg-card-hint { color: #9fb3d6; }

/* ---- badges: icon + text + soft background + border (never colour alone) ---- */
.lg-badge { display: inline-flex; align-items: center; gap: .28rem; padding: .14rem .55rem; border-radius: 999px; font-size: .72rem; font-weight: 700; line-height: 1.35; border: 1px solid transparent; white-space: nowrap; vertical-align: middle; margin: .1rem .3rem .1rem 0; }
.lg-badge--neutral { background: #f1f5f9; color: var(--lg-muted); border-color: var(--lg-line); }
.lg-badge--info { background: #eef4ff; color: var(--lg-blue-600); border-color: #c7d7fb; }
.lg-badge--ok { background: #ecfdf3; color: #15803d; border-color: #a6e3bd; }
.lg-badge--warn { background: #fff7ed; color: #b45309; border-color: #fed7aa; }
.lg-badge--danger { background: #fef2f2; color: #b91c1c; border-color: #fecaca; }
.lg-badge--navy { background: var(--lg-navy-800); color: #fff; border-color: var(--lg-navy-800); }
.lg-badges { display: flex; flex-wrap: wrap; gap: .2rem .3rem; align-items: center; }

/* ---- section heading ---- */
.lg-section { display: flex; flex-wrap: wrap; align-items: baseline; gap: .35rem .75rem; margin: 1.15rem 0 .5rem; padding-left: .7rem; border-left: 4px solid var(--lg-blue-500); }
.lg-section-title { color: var(--lg-navy-800); font-size: .8rem; font-weight: 800; letter-spacing: .1em; text-transform: uppercase; }
.lg-section-note { color: var(--lg-muted); font-size: .78rem; }

/* ---- callouts ---- */
.lg-callout { border-left: 3px solid var(--lg-blue-500); background: #eef4ff; color: #1e3a8a; border-radius: 0 8px 8px 0; padding: .55rem .8rem; font-size: .82rem; line-height: 1.45; margin: .4rem 0 .7rem; }
.lg-callout--warn { border-color: #d97706; background: #fffbeb; color: #7c4a03; }
.lg-callout--danger { border-color: #dc2626; background: #fef2f2; color: #991b1b; }
.lg-callout--ok { border-color: #16a34a; background: #ecfdf3; color: #14532d; }
.lg-callout--neutral { border-color: #8695a8; background: #f4f7fc; color: var(--lg-muted); }

/* ---- stage indicator ---- */
.lg-stepper { display: flex; flex-wrap: wrap; gap: .4rem .25rem; align-items: stretch; background: var(--lg-surface); border: 1px solid var(--lg-line); border-radius: 10px; padding: .6rem .75rem; margin: .3rem 0 .9rem; }
.lg-step { display: flex; align-items: center; gap: .5rem; flex: 1 1 150px; min-width: 0; padding: .3rem .4rem; border-radius: 8px; }
.lg-step-num { flex: 0 0 auto; width: 26px; height: 26px; border-radius: 999px; display: inline-flex; align-items: center; justify-content: center; font-size: .74rem; font-weight: 800; background: #e2e8f0; color: var(--lg-muted); }
.lg-step-label { color: var(--lg-muted); font-size: .8rem; font-weight: 700; line-height: 1.2; }
.lg-step-desc { color: var(--lg-faint); font-size: .7rem; line-height: 1.3; }
.lg-step.is-done .lg-step-num { background: #16a34a; color: #fff; }
.lg-step.is-done .lg-step-label { color: #15803d; }
.lg-step.is-current { background: #eef4ff; }
.lg-step.is-current .lg-step-num { background: var(--lg-navy-800); color: #fff; box-shadow: 0 0 0 3px rgba(47, 111, 237, .25); }
.lg-step.is-current .lg-step-label { color: var(--lg-navy-800); }
.lg-step-arrow { align-self: center; color: #c3ccdb; font-size: 1rem; flex: 0 0 auto; }

/* ---- key/value grid ---- */
.lg-kv { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: .55rem .9rem; margin: .25rem 0 .6rem; }
.lg-kv > div { min-width: 0; }
.lg-kv dt { color: var(--lg-faint); font-size: .66rem; font-weight: 800; letter-spacing: .08em; text-transform: uppercase; margin: 0; }
.lg-kv dd { color: var(--lg-ink); font-size: .9rem; font-weight: 600; margin: .12rem 0 0; word-break: break-word; }
.lg-kv dd.is-missing { color: #b45309; }

/* ---- list rows ---- */
.lg-row { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: .3rem .9rem; }
.lg-row-title { color: var(--lg-navy-800); font-size: 1rem; font-weight: 800; letter-spacing: .01em; }
.lg-row-sub { color: var(--lg-muted); font-size: .8rem; line-height: 1.4; }
.lg-row-meta { color: var(--lg-faint); font-size: .74rem; }

/* ---- responsive data table (table on desktop, cards on phones) ---- */
.lg-table-wrap { width: 100%; overflow-x: auto; }
table.lg-table { width: 100%; border-collapse: separate; border-spacing: 0; background: var(--lg-surface); border: 1px solid var(--lg-line); border-radius: 10px; overflow: hidden; font-size: .82rem; }
table.lg-table th { background: #f4f7fc; color: var(--lg-muted); font-size: .66rem; font-weight: 800; letter-spacing: .08em; text-transform: uppercase; text-align: left; padding: .55rem .7rem; border-bottom: 1px solid var(--lg-line); white-space: nowrap; }
table.lg-table td { padding: .5rem .7rem; border-bottom: 1px solid #edf1f7; color: var(--lg-ink); vertical-align: top; }
table.lg-table tr:last-child td { border-bottom: 0; }
table.lg-table td.num, table.lg-table th.num { text-align: right; font-variant-numeric: tabular-nums; }
table.lg-table td.strong { font-weight: 700; color: var(--lg-navy-800); }
@media (max-width: 768px) {
  table.lg-table, table.lg-table tbody, table.lg-table tr, table.lg-table td { display: block; width: 100%; }
  table.lg-table thead { display: none; }
  table.lg-table tr { border-bottom: 1px solid var(--lg-line); padding: .4rem .2rem; }
  table.lg-table td { display: flex; justify-content: space-between; gap: .75rem; border: 0; padding: .22rem .5rem; text-align: right; }
  table.lg-table td.num { text-align: right; }
  table.lg-table td::before { content: attr(data-label); color: var(--lg-faint); font-size: .66rem; font-weight: 800; letter-spacing: .06em; text-transform: uppercase; text-align: left; flex: 0 0 45%; }
}

/* ---- empty state ---- */
.lg-empty { border: 1px dashed #c9d4e5; border-radius: 10px; background: var(--lg-surface); padding: 1rem 1.1rem; color: var(--lg-muted); font-size: .84rem; }
.lg-empty strong { color: var(--lg-navy-800); display: block; margin-bottom: .2rem; }

/* ---- desktop-only / mobile-only keyed containers ---- */
@media (max-width: 768px) { [class*="st-key-lgdesk_"] { display: none !important; } }
@media (min-width: 769px) { [class*="st-key-lgmob_"] { display: none !important; } }

/* ---- keyed button tones: success (genuine completion) and danger ---- */
[class*="st-key-lgok_"] button[kind="primary"] { background: #16a34a !important; border-color: #16a34a !important; color: #fff !important; }
[class*="st-key-lgok_"] button[kind="primary"]:hover { background: #15803d !important; border-color: #15803d !important; }
[class*="st-key-lgdanger_"] button { background: #fff !important; border-color: #fecaca !important; color: #b91c1c !important; }
[class*="st-key-lgdanger_"] button:hover { background: #fef2f2 !important; border-color: #dc2626 !important; }

/* ---- legacy review classes kept for review_queue / finance_review ---- */
.review-kicker { color: var(--lg-blue-600); font-size: .66rem; font-weight: 800; letter-spacing: .14em; text-transform: uppercase; }
.review-title { color: var(--lg-navy-800); font-size: 1.6rem; line-height: 1.15; margin: .15rem 0 .25rem; font-weight: 800; }
.review-note { color: var(--lg-muted); font-size: .82rem; border-left: 3px solid var(--lg-blue-500); background: #eef4ff; padding: .6rem .8rem; margin: .65rem 0 1rem; border-radius: 0 8px 8px 0; }
.review-readonly { color: var(--lg-faint); font-size: .76rem; }
.review-action { border-left: 3px solid #d97706; background: #fffbeb; padding: .55rem .75rem; color: #7c4a03; border-radius: 0 8px 8px 0; }
"""


# ---------------------------------------------------------------------------
# small formatting helpers
# ---------------------------------------------------------------------------
def text(value: Any, default: str = "—") -> str:
    """Escape a value for HTML output; blanks/None become ``default``."""
    if value is None:
        return escape(default)
    s = str(value).strip()
    return escape(s if s else default)


def money(value: Any, currency: str = "VND") -> str:
    """Format an amount with thousands separators; never converts currencies."""
    try:
        amount = float(value or 0)
    except (TypeError, ValueError):
        return f"{value} {currency}".strip()
    if currency.upper() == "VND":
        return f"{amount:,.0f} {currency}"
    return f"{amount:,.2f} {currency}"


def icon(name: str) -> str:
    """Inline Material Symbols icon (font is bundled with Streamlit)."""
    return f"<span class='lg-ico' aria-hidden='true'>{escape(name)}</span>"


def _tone(tone: str | None) -> str:
    return tone if tone in TONES else "neutral"


# ---------------------------------------------------------------------------
# components
# ---------------------------------------------------------------------------
def badge(label: Any, tone: str = "neutral", icon_name: str | None = None) -> str:
    """Return badge HTML: icon + text + soft background + border."""
    tone = _tone(tone)
    icon_html = icon(icon_name or _TONE_ICON[tone])
    return f"<span class='lg-badge lg-badge--{tone}'>{icon_html}<span>{text(label)}</span></span>"


def badges(items: Iterable[tuple[Any, str] | tuple[Any, str, str]]) -> None:
    """Render a row of badges. Each item is ``(label, tone)`` or ``(label, tone, icon)``."""
    html = "".join(badge(*item) for item in items)
    if html:
        st.markdown(f"<div class='lg-badges'>{html}</div>", unsafe_allow_html=True)


def page_header(
    title: str,
    subtitle: str | None = None,
    *,
    kicker: str | None = None,
    badge_items: Sequence[tuple[Any, str] | tuple[Any, str, str]] = (),
    native_title: bool = False,
) -> None:
    """Donor-style page header: kicker, title, subtitle and optional badges.

    ``native_title=True`` renders the title with ``st.title`` (kept for pages
    whose tests look for an ``st.title`` element)."""
    if native_title:
        if kicker:
            st.markdown(f"<div class='lg-kicker'>{text(kicker)}</div>", unsafe_allow_html=True)
        st.title(title)
        if subtitle:
            st.markdown(f"<div class='lg-page-sub'>{text(subtitle)}</div>", unsafe_allow_html=True)
    else:
        # single markdown block → one element container, no extra flex gaps
        parts = ["<div class='lg-page-head'>"]
        if kicker:
            parts.append(f"<div class='lg-kicker'>{text(kicker)}</div>")
        parts.append(f"<h1 class='lg-page-title'>{text(title)}</h1>")
        if subtitle:
            parts.append(f"<div class='lg-page-sub'>{text(subtitle)}</div>")
        parts.append("</div>")
        st.markdown("".join(parts), unsafe_allow_html=True)
    if badge_items:
        st.markdown(
            "<div class='lg-page-badges'>" + "".join(badge(*item) for item in badge_items) + "</div>",
            unsafe_allow_html=True,
        )


def section(title: str, note: str | None = None) -> None:
    """Uppercase section heading with the donor accent bar."""
    note_html = f"<span class='lg-section-note'>{text(note)}</span>" if note else ""
    st.markdown(
        f"<div class='lg-section'><span class='lg-section-title'>{text(title)}</span>{note_html}</div>",
        unsafe_allow_html=True,
    )


def summary_cards(cards: Sequence[Mapping[str, Any]]) -> None:
    """Grid of KPI cards. Keys: label, value, hint (optional), tone (optional), icon (optional)."""
    if not cards:
        return
    parts = []
    for card in cards:
        tone = _tone(card.get("tone"))
        icon_html = icon(card["icon"]) if card.get("icon") else ""
        hint = f"<div class='lg-card-hint'>{text(card.get('hint'))}</div>" if card.get("hint") else ""
        parts.append(
            f"<div class='lg-card lg-card--{tone}'>"
            f"<div class='lg-card-label'>{icon_html}<span>{text(card.get('label'))}</span></div>"
            f"<div class='lg-card-value'>{text(card.get('value'))}</div>{hint}</div>"
        )
    st.markdown(f"<div class='lg-cards'>{''.join(parts)}</div>", unsafe_allow_html=True)


def callout(body: str, tone: str = "info", *, title: str | None = None, allow_html: bool = False) -> None:
    """Short explanatory note (where am I / what is missing / what to do)."""
    tone = _tone(tone)
    inner = body if allow_html else text(body)
    if title:
        inner = f"<strong>{text(title)}:</strong> {inner}"
    st.markdown(f"<div class='lg-callout lg-callout--{tone}'>{inner}</div>", unsafe_allow_html=True)


def stage_indicator(stages: Sequence[tuple[str, str]], current: int, *, done_through: int | None = None) -> None:
    """Horizontal stepper. ``stages`` is ``[(label, description), ...]``.

    ``current`` is the 0-based index of the active stage (``-1`` = nothing
    active); stages before ``done_through`` (default ``current``) show as done."""
    done_upto = current if done_through is None else done_through
    parts = []
    for index, (label, desc) in enumerate(stages):
        state = ""
        if index < done_upto:
            state = "is-done"
        elif index == current:
            state = "is-current"
        num = icon("check") if state == "is-done" else str(index + 1)
        parts.append(
            f"<div class='lg-step {state}'><span class='lg-step-num'>{num}</span>"
            f"<span><div class='lg-step-label'>{text(label)}</div><div class='lg-step-desc'>{text(desc)}</div></span></div>"
        )
        if index < len(stages) - 1:
            parts.append(f"<span class='lg-step-arrow'>{icon('chevron_right')}</span>")
    st.markdown(f"<div class='lg-stepper'>{''.join(parts)}</div>", unsafe_allow_html=True)


def kv_grid(pairs: Sequence[tuple[str, Any]], *, missing_label: str = "Thiếu") -> None:
    """Definition grid; empty values are shown as ``Thiếu`` in amber (never hidden)."""
    parts = []
    for label, value in pairs:
        raw = "" if value is None else str(value).strip()
        if raw and raw.upper() not in {"UNKNOWN", "NONE", "NAN"}:
            parts.append(f"<div><dt>{text(label)}</dt><dd>{text(raw)}</dd></div>")
        else:
            parts.append(f"<div><dt>{text(label)}</dt><dd class='is-missing'>{icon('warning')} {text(missing_label)}</dd></div>")
    st.markdown(f"<dl class='lg-kv'>{''.join(parts)}</dl>", unsafe_allow_html=True)


def data_table(
    columns: Sequence[tuple[str, str] | tuple[str, str, str]],
    rows: Iterable[Mapping[str, Any]],
    *,
    empty: str = "Chưa có dữ liệu.",
    money_currency: str | None = None,
) -> None:
    """Responsive HTML table: ``columns`` = ``[(key, header[, 'num'|'strong'|'html'])]``.

    ``num`` cells holding numbers are formatted with thousands separators (and
    ``money_currency`` suffix when given); ``html`` cells are inserted as-is
    (use only with ``badge`` output or other trusted markup).
    On phones the rows collapse into label/value cards (no horizontal scroll)."""
    rows = list(rows)
    if not rows:
        st.markdown(f"<div class='lg-empty'>{text(empty)}</div>", unsafe_allow_html=True)
        return
    head = "".join(
        f"<th class='{col[2] if len(col) > 2 else ''}'>{text(col[1])}</th>" for col in columns
    )
    body_parts = []
    for row in rows:
        cells = []
        for col in columns:
            key, header = col[0], col[1]
            cls = col[2] if len(col) > 2 else ""
            value = row.get(key, "")
            if cls == "html" or (isinstance(value, str) and value.startswith("<span class='lg-badge")):
                cell = value if value not in (None, "") else "—"
                cls = "" if cls == "html" else cls
            elif cls == "num" and isinstance(value, (int, float)) and not isinstance(value, bool):
                cell = f"{value:,.0f}" if float(value).is_integer() or abs(value) >= 1000 else f"{value:,.2f}"
                if money_currency:
                    cell = f"{cell} {escape(money_currency)}"
            else:
                cell = text(value)
            cells.append(f"<td class='{cls}' data-label='{escape(header)}'>{cell}</td>")
        body_parts.append(f"<tr>{''.join(cells)}</tr>")
    st.markdown(
        f"<div class='lg-table-wrap'><table class='lg-table'><thead><tr>{head}</tr></thead>"
        f"<tbody>{''.join(body_parts)}</tbody></table></div>",
        unsafe_allow_html=True,
    )


def empty_state(title: str, hint: str | None = None) -> None:
    hint_html = text(hint) if hint else ""
    st.markdown(f"<div class='lg-empty'><strong>{text(title)}</strong>{hint_html}</div>", unsafe_allow_html=True)


def row_head(title: Any, subtitle: Any = None, *, badge_items: Sequence[tuple[Any, str] | tuple[Any, str, str]] = (), meta: Any = None) -> None:
    """Title line for a list row card: title + badges on the left, meta on the right."""
    badge_html = "".join(badge(*item) for item in badge_items)
    sub = f"<div class='lg-row-sub'>{text(subtitle)}</div>" if subtitle else ""
    meta_html = f"<div class='lg-row-meta'>{text(meta)}</div>" if meta else ""
    st.markdown(
        f"<div class='lg-row'><div><span class='lg-row-title'>{text(title)}</span> {badge_html}{sub}</div>{meta_html}</div>",
        unsafe_allow_html=True,
    )


__all__ = [
    "COMPONENT_CSS",
    "TONES",
    "badge",
    "badges",
    "callout",
    "data_table",
    "empty_state",
    "icon",
    "kv_grid",
    "money",
    "page_header",
    "row_head",
    "section",
    "stage_indicator",
    "summary_cards",
    "text",
]
