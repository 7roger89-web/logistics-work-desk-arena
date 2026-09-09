"""Reusable UI helpers for the donor page renderers."""
from __future__ import annotations

import streamlit as st

from . import design, icons, store


def href_for(to: str | None) -> str:
    """Format a target_self href query string from a route or action."""
    if not to:
        return ""
    if to.startswith("action:"):
        return f"?action={to.replace('action:', '')}"
    if to.startswith("?"):
        return to
    return f"?p={to}"


def page_title(title: str, sub: str = "", right=None):
    """Render the donor's SectionTitle pattern."""
    icon = '<span class="lg-section-icon">{}</span>'.format(icons.layout(20, "#fff"))
    right_html = f'<div>{right}</div>' if right else ""
    html = f"""
<div class="lg-section-title">
  <div style="display:flex;align-items:flex-start;gap:10px">
    {icon}
    <div>
      <h2>{title}</h2>
      {f'<p>{sub}</p>' if sub else ''}
    </div>
  </div>
  {right_html}
</div>
"""
    st.markdown(html, unsafe_allow_html=True)


def hero(
    kicker: str,
    title: str,
    sub: str,
    primary_label: str = None,
    primary_to: str = None,
    secondary_label: str = None,
    secondary_to: str = None,
):
    cta_html = ""
    if primary_label:
        cta_html += f'<a class="lg-btn-white" href="{href_for(primary_to)}" target="_self">{primary_label} →</a>'
    if secondary_label:
        cta_html += f'<a class="lg-btn-ghost" href="{href_for(secondary_to)}" target="_self">{secondary_label}</a>'
    st.markdown(f"""
<div class="lg-hero">
  <p class="lg-kicker">{kicker}</p>
  <h1>{title}</h1>
  <p>{sub}</p>
  <div class="lg-hero-ctas">{cta_html}</div>
</div>
""", unsafe_allow_html=True)


def next_action_banner(tone: str, kicker: str, title: str, desc: str = None, action: str = None, to: str = None):
    btn_html = f'<a class="lg-na-btn" href="{href_for(to)}" target="_self">{action} {icons.arrow_right(18, "#fff")}</a>' if action else ""
    desc_html = f'<p class="lg-na-desc">{desc}</p>' if desc else ""
    st.markdown(f"""
<div class="lg-na {tone}">
  <div style="display:flex;align-items:flex-start;gap:12px;flex:1;min-width:0">
    <div class="lg-na-icon {tone}">{_na_icon(tone)}</div>
    <div style="min-width:0">
      <p class="lg-na-kicker">{kicker}</p>
      <h3 class="lg-na-title">{title}</h3>
      {desc_html}
    </div>
  </div>
  {btn_html}
</div>
""", unsafe_allow_html=True)


def _na_icon(tone: str) -> str:
    if tone == "red":
        return icons.octagon_alert(22, "#fff")
    if tone == "green":
        return icons.circle_check(22, "#fff")
    if tone == "blue":
        return icons.info(22, "#fff")
    return icons.alert_triangle(22, "#fff")


def kpi_grid(items: list, columns: int = 5):
    """Render the donor's home KPI grid.

    Each item: dict with label/value/sub, optional tone ('green','red','amber'), optional to (link).
    """
    style = f"grid-template-columns:repeat({columns},1fr)"
    cards = []
    for it in items:
        tone = it.get("tone", "")
        cls = f"lg-kpi {tone}".strip()
        to = it.get("to")
        href = href_for(to) if to else ""
        tag_open = f'<a class="{cls}" href="{href}" target="_self">' if to else f'<div class="{cls}">'
        tag_close = "</a>" if to else "</div>"
        sub = it.get("sub", "")
        sub_html = f'<p class="sub">{sub}</p>' if sub else ""
        cards.append(f"""
{tag_open}
  <p class="label">{it.get('label','')}</p>
  <p class="value">{it.get('value','')}</p>
  {sub_html}
{tag_close}
""")
    st.markdown(f'<div class="lg-kpi-grid" style="{style}">{"".join(cards)}</div>', unsafe_allow_html=True)


def next_action_cards(items: list):
    """Render the donor's 5-column 'next action' cards row."""
    cards = []
    for it in items:
        icon_html = f'<span class="lg-next-icon" style="background:{it.get("bg","#475569")}">{_icon_for(it.get("icon","package"))}</span>'
        bar = f'<div class="lg-next-bar" style="background:{it.get("bar","#475569")}"></div>'
        href = href_for(it.get("to", "/"))
        cards.append(f"""
<a class="lg-next-card" href="{href}" target="_self">
  {bar}
  {icon_html}
  <div class="lg-next-card-body">
    <p class="lg-next-card-title">{it.get('title','')} <span class="lg-next-card-count">{it.get('count','')}</span></p>
    <p class="lg-next-card-desc">{it.get('desc','')}</p>
    <span class="lg-next-card-cta">{it.get('cta','Mở')} {icons.arrow_right(15, "#1e5aa8")}</span>
  </div>
</a>
""")
    st.markdown(f'<div class="lg-next-grid">{"".join(cards)}</div>', unsafe_allow_html=True)


def _icon_for(name: str) -> str:
    return {
        "truck": icons.truck(21, "#fff"),
        "filecheck": icons.file_check(21, "#fff"),
        "package_check": icons.circle_check(21, "#fff"),
        "wallet": icons.wallet(21, "#fff"),
        "file_warning": icons.file_text(21, "#fff"),
    }.get(name, icons.package(21, "#fff"))


def badge(text: str, tone: str = "gray", size: str = "md"):
    cls = f"lg-badge {tone} {size}".strip()
    st.markdown(f'<span class="{cls}">{text}</span>', unsafe_allow_html=True)


def card(content: str, css_class: str = "lg-card"):
    st.markdown(f'<div class="{css_class}">{content}</div>', unsafe_allow_html=True)


def table(headers: list, rows: list, min_width: str = "980px", key_col: int = None):
    """Render a donor-style responsive table."""
    head = "".join(f"<th>{h}</th>" for h in headers)
    body = ""
    for r in rows:
        cells = r if isinstance(r, list) else list(r)
        body += "<tr>"
        for i, c in enumerate(cells):
            body += f"<td>{c}</td>"
        body += "</tr>"
    st.markdown(f"""
<div class="lg-tbl-wrap">
  <div style="overflow-x:auto">
    <table class="lg-tbl" style="min-width:{min_width}">
      <thead><tr>{head}</tr></thead>
      <tbody>{body}</tbody>
    </table>
  </div>
</div>
""", unsafe_allow_html=True)


def two_col(left_html: str, right_html: str):
    st.markdown(f'<div class="lg-2col"><div>{left_html}</div><div>{right_html}</div></div>', unsafe_allow_html=True)


def field(label: str, required: bool = False, hint: str = None, error: str = None, key: str = None, default: str = "", placeholder: str = "", input_type: str = "text", options: list = None, value: str = None):
    """Render a Streamlit form field that mimics the donor's Field component."""
    label_html = f'{label} <span style="color:#dc2626">*</span>' if required else label
    if input_type == "select":
        if value is None:
            value = default
        idx = options.index(value) if value in options else 0
        new = st.selectbox(label_html, options, index=idx, key=key, help=hint, placeholder=placeholder)
        if error:
            st.markdown(f'<p class="lg-field-error">⚠ {error}</p>', unsafe_allow_html=True)
        return new
    if input_type == "textarea":
        new = st.text_area(label_html, value=default, key=key, placeholder=placeholder, help=hint)
        if error:
            st.markdown(f'<p class="lg-field-error">⚠ {error}</p>', unsafe_allow_html=True)
        return new
    if input_type == "number":
        new = st.number_input(label_html, value=float(default) if default else 0.0, key=key, help=hint)
        if error:
            st.markdown(f'<p class="lg-field-error">⚠ {error}</p>', unsafe_allow_html=True)
        return new
    new = st.text_input(label_html, value=default, key=key, placeholder=placeholder, help=hint)
    if error:
        st.markdown(f'<p class="lg-field-error">⚠ {error}</p>', unsafe_allow_html=True)
    return new


def primary_button(label: str, key: str = None, full: bool = False, kind: str = "primary"):
    cls = f"lg-btn {kind}" + (" full" if full else "")
    return st.button(label, key=key, type="primary" if kind == "primary" else "secondary", use_container_width=full)


def ghost_button(label: str, key: str = None, full: bool = False):
    return st.button(label, key=key, type="secondary", use_container_width=full)


def success_button(label: str, key: str = None, full: bool = False):
    return st.button(label, key=key, type="primary", use_container_width=full)


def missing_box(what: str, where: str = None, action_label: str = "Bổ sung ngay", to: str = None):
    where_html = f'<p>{where}</p>' if where else ""
    href = href_for(to) if to else ""
    btn = f'<a class="btn" href="{href}" target="_self">{icons.pen(16, "#fff")} {action_label}</a>' if to else f'<span class="btn">{icons.pen(16, "#fff")} {action_label}</span>'
    st.markdown(f"""
<div class="lg-missing">
  <span class="body">
    <h5>⚠ Thiếu {what}</h5>
    {where_html}
  </span>
  {btn}
</div>
""", unsafe_allow_html=True)


def tabs(labels: list, active_id: str, key: str = "donor_tab") -> str:
    """Render the donor's horizontal tab strip and return the selected tab id."""
    options = [lbl["id"] for lbl in labels]
    idx = options.index(active_id) if active_id in options else 0
    selected = st.radio(
        "Tabs",
        options=options,
        index=idx,
        key=key,
        format_func=lambda x: next((lbl["label"] for lbl in labels if lbl["id"] == x), x),
        label_visibility="collapsed",
        horizontal=True,
    )
    return selected


def _next_action_banner_html(s: dict) -> str:
    """Return HTML for a shipment-specific next-action banner."""
    tone = s.get("statusTone", "red")
    kicker = "Việc tiếp theo"
    title = s.get("nextAction", "Tiếp tục xử lý lô hàng")
    desc = s.get("nextActionDetail", "")
    to = s.get("nextRoute", "/lo-hang-detail?id=" + s.get("id", ""))
    btn = ""
    if to:
        href = href_for(to)
        btn = f'<a class="lg-na-btn" href="{href}" target="_self">XỬ LÝ NGAY {icons.arrow_right(18, "#fff")}</a>'
    desc_html = f'<p class="lg-na-desc">{desc}</p>' if desc else ""
    return f"""
<div class="lg-na {tone}">
  <div style="display:flex;align-items:flex-start;gap:12px;flex:1;min-width:0">
    <div class="lg-na-icon {tone}">{_na_icon(tone)}</div>
    <div style="min-width:0">
      <p class="lg-na-kicker">{kicker}</p>
      <h3 class="lg-na-title">{title}</h3>
      {desc_html}
    </div>
  </div>
  {btn}
</div>
"""


def fmt_vnd(amount) -> str:
    return design.fmt_vnd(amount)


def fmt_money(amount, ccy: str = "VND") -> str:
    return design.fmt_money(amount, ccy)


def status_dot(tone: str) -> str:
    return f'<span class="lg-dot {tone}"></span>'


def status_badge(text: str, tone: str = "gray", size: str = "md") -> str:
    return f'<span class="lg-badge {tone} {size}">{text}</span>'
