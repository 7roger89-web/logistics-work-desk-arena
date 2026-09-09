"""Donor-aligned CSS theme + small HTML helpers for the Logi-good view layer.

Colors / geometry mirror ``design_reference/logi-good/src/index.css`` and the
donor component classes (cards, badges, buttons, section titles, tables).
Everything is Streamlit markdown injected once per page so the rendered
surfaces follow the donor look without a second front-end architecture.
"""
from __future__ import annotations

import html

NAVY = "#0f2a4a"
NAVY_DARK = "#0a1f3a"
NAVY_MID = "#1e5aa8"
BG = "#eef1f6"
INK = "#1a2433"

# Font stack from donor index.css (Be Vietnam Pro first, then fallbacks).
FONT = ("'Be Vietnam Pro','Segoe UI',system-ui,-apple-system,sans-serif")

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@300;400;500;600;700;800&display=swap');

.lg {{
  font-family: {FONT};
  color: {INK};
  line-height: 1.55;
}}
.stApp {{
  font-family: {FONT};
  color: {INK};
  background: {BG};
}}
.block-container {{ padding-top: 1rem; max-width: 1560px; }}

/* ---- donor section title ---- */
.lg-title {{ display:flex; align-items:flex-start; gap:10px; margin-bottom:12px; }}
.lg-title .lg-t-ic {{ width:36px; height:36px; border-radius:12px; background:{NAVY}; color:#fff;
  display:grid; place-items:center; flex-shrink:0; font-size:17px; }}
.lg-title h2 {{ margin:0; font-size:19px; font-weight:800; color:{NAVY}; line-height:1.2; }}
.lg-title p {{ margin:2px 0 0; font-size:13.5px; color:#64748b; }}
.lg-title .lg-t-r {{ margin-left:auto; }}

/* ---- cards / shell ---- */
.lg-card {{ background:#fff; border:1px solid #e2e8f0; border-radius:16px; padding:16px; }}
.lg-card-pad {{ padding:18px; }}
.lg-grid {{ display:grid; gap:12px; }}
.lg-cols {{ display:grid; gap:14px; }}
.lg-row {{ display:flex; align-items:center; gap:10px; }}
.lg-spread {{ display:flex; align-items:center; justify-content:space-between; gap:10px; }}
.lg-gap2 {{ gap:8px; }}
.lg-muted {{ color:#64748b; }}
.lg-bold {{ font-weight:700; }}
.lg-ink {{ color:{NAVY}; }}
.lg-mt1 {{ margin-top:6px; }} .lg-mt2 {{ margin-top:12px; }} .lg-mt3 {{ margin-top:18px; }}
.lg-mb2 {{ margin-bottom:10px; }}
.lg-flexwrap {{ display:flex; flex-wrap:wrap; gap:8px; }}

/* ---- badges ---- */
.lg-badge {{ display:inline-flex; align-items:center; gap:6px; font-weight:700;
  border-radius:999px; white-space:nowrap; border:1px solid transparent; }}
.lg-badge.md {{ font-size:13px; padding:5px 12px; }}
.lg-badge.sm {{ font-size:12px; padding:3px 10px; }}
.b-green {{ background:#ecfdf5; color:#065f46; border-color:#a7f3d0; }}
.b-amber {{ background:#fffbeb; color:#78350f; border-color:#fde68a; }}
.b-red {{ background:#fef2f2; color:#991b1b; border-color:#fecaca; }}
.b-blue {{ background:#eff6ff; color:#1e40af; border-color:#bfdbfe; }}
.b-gray {{ background:#f1f5f9; color:#334155; border-color:#e2e8f0; }}
.b-violet {{ background:#f5f3ff; color:#5b21b6; border-color:#ddd6fe; }}
.dot {{ display:inline-block; width:10px; height:10px; border-radius:50%; }}
.d-green{{background:#10b981;}} .d-amber{{background:#f59e0b;}} .d-red{{background:#ef4444;}}
.d-blue{{background:#3b82f6;}} .d-gray{{background:#94a3b8;}}

/* ---- donor buttons ---- */
.lg-btn {{ display:inline-flex; align-items:center; justify-content:center; gap:6px;
  border-radius:12px; font-weight:700; font-size:14px; padding:9px 16px; min-height:40px;
  cursor:pointer; border:1px solid transparent; text-decoration:none; white-space:nowrap; }}
.lg-btn-navy {{ background:{NAVY}; color:#fff; }}
.lg-btn-navy:hover {{ background:{NAVY_MID}; color:#fff; }}
.lg-btn-white {{ background:#fff; color:{NAVY}; border:1px solid #e2e8f0; }}
.lg-btn-green {{ background:#059669; color:#fff; }}
.lg-btn-amber {{ background:#d97706; color:#fff; }}
.lg-btn-block {{ width:100%; }}
.lg-btn:disabled {{ opacity:.5; cursor:not-allowed; }}

/* ---- hero (Home) ---- */
.lg-hero {{ border-radius:24px; color:#fff; padding:22px 26px; position:relative; overflow:hidden;
  background: linear-gradient(135deg,{NAVY_DARK} 0%,{NAVY} 55%,{NAVY_MID} 100%); }}
.lg-hero .dec {{ position:absolute; border-radius:50%; background:rgba(255,255,255,.09); }}
.lg-hero p.kicker {{ margin:0; font-size:12.5px; font-weight:600; color:#bfdbfe; text-transform:uppercase;
  letter-spacing:.05em; }}
.lg-hero h1 {{ margin:6px 0 4px; font-size:26px; font-weight:800; line-height:1.2; }}
.lg-hero p.desc {{ margin:0; color:#dbeafe; max-width:640px; font-size:15px; }}
.lg-hero .hero-actions {{ display:flex; gap:10px; margin-top:14px; flex-wrap:wrap; }}

/* ---- KPI metric card ---- */
.lg-kpi {{ background:#fff; border:1px solid #e2e8f0; border-radius:16px; padding:14px; }}
.lg-kpi.solid-green {{ background:#059669; border:none; color:#fff; }}
.lg-kpi.solid-red {{ background:#dc2626; border:none; color:#fff; }}
.lg-kpi .k-label {{ font-size:13px; font-weight:600; color:#64748b; }}
.lg-kpi.solid-green .k-label, .lg-kpi.solid-red .k-label {{ color:rgba(255,255,255,.85); }}
.lg-kpi .k-value {{ font-size:24px; font-weight:800; color:{NAVY}; line-height:1.15; margin-top:2px; }}
.lg-kpi.solid-green .k-value, .lg-kpi.solid-red .k-value {{ color:#fff; }}
.lg-kpi .k-sub {{ font-size:12px; color:#94a3b8; margin-top:2px; }}

/* ---- next action banner ---- */
.lg-na {{ border-radius:16px; border:2px solid; padding:16px 18px; display:flex; align-items:center; gap:14px;
  flex-wrap:wrap; }}
.lg-na .na-ic {{ width:44px; height:44px; border-radius:12px; color:#fff; display:grid;
  place-items:center; flex-shrink:0; font-size:19px; font-weight:800; }}
.na-amber{{background:linear-gradient(90deg,#fffbeb,#fff7ed); border-color:#fcd34d;}}
.na-red{{background:linear-gradient(90deg,#fef2f2,#fff7ed); border-color:#fca5a5;}}
.na-green{{background:linear-gradient(90deg,#ecfdf5,#f0fdf4); border-color:#6ee7b7;}}
.na-blue{{background:linear-gradient(90deg,#eff6ff,#eef2ff); border-color:#93c5fd;}}
.lg-na .na-k {{ font-size:11.5px; font-weight:800; text-transform:uppercase; letter-spacing:.05em;
  color:#64748b; margin:0; }}
.lg-na .na-t {{ font-size:17px; font-weight:800; color:{NAVY}; margin:1px 0 0; }}
.lg-na .na-d {{ font-size:13.5px; color:#475569; margin:2px 0 0; }}

/* ---- missing box ---- */
.lg-missing {{ border:2px dashed #fbbf24; background:#fffbeb; border-radius:14px; padding:12px 14px;
  display:flex; align-items:center; gap:10px; flex-wrap:wrap; }}
.lg-missing b {{ color:#92400e; }}
.lg-missing .miss-act {{ margin-left:auto; }}

/* ---- state row ---- */
.lg-state {{ display:flex; align-items:flex-start; justify-content:space-between; gap:12px;
  padding:7px 0; border-bottom:1px solid #f1f5f9; }}
.lg-state:last-child {{ border-bottom:0; }}
.lg-state .sl {{ color:#64748b; font-size:13.5px; font-weight:500; }}
.lg-state .sv {{ text-align:right; font-weight:600; font-size:14.5px; color:#1f2937; }}

/* ---- responsive table ---- */
.lg-tablewrap {{ overflow-x:auto; border-radius:16px; background:#fff; border:1px solid #e2e8f0; }}
table.lg-tbl {{ width:100%; border-collapse:collapse; font-size:14px; min-width:720px; }}
.lg-tbl th {{ font-size:12px; text-transform:uppercase; letter-spacing:.04em; color:#5b6b82;
  font-weight:800; background:#f1f5fa; text-align:left; padding:12px 14px; }}
.lg-tbl td {{ padding:12px 14px; border-bottom:1px solid #eef2f7; text-align:left; vertical-align:middle; }}
.lg-tbl tr:last-child td {{ border-bottom:none; }}
.lg-tbl tbody tr:hover {{ background:#f8fafc; }}

/* status flow / progress (Tracking) */
.lg-progress {{ display:flex; gap:4px; overflow-x:auto; }}
.lg-progress .step {{ display:flex; flex-direction:column; align-items:center; flex-shrink:0; }}
.lg-progress .n {{ width:34px; height:34px; border-radius:50%; display:grid; place-items:center;
  font-weight:800; font-size:13px; }}
.stp-done{{background:#059669;color:#fff;}} .stp-cur{{background:#f59e0b;color:#fff;animation:pulse 1.6s infinite;}}
.stp-todo{{background:#f1f5f9;color:#94a3b8;}}
.lg-progress .l {{ font-size:11px; font-weight:700; margin-top:3px; }}
.lg-progress .bar {{ width:24px; height:4px; border-radius:4px; background:#e2e8f0; margin:0 2px 16px; }}
.lg-progress .bar.filled {{ background:#10b981; }}

@keyframes pulse {{ 0%,100%{{opacity:1;}} 50%{{opacity:.5;}} }}
.lg-timeline {{ position:relative; padding-left:22px; }}
.lg-timeline .ln {{ position:absolute; left:7px; top:8px; bottom:8px; width:2px; background:#e2e8f0; }}
.lg-timeline .it {{ position:relative; margin-bottom:14px; }}
.lg-timeline .dot {{ position:absolute; left:-20px; top:4px; width:14px; height:14px; border-radius:50%;
  border:3px solid #fff; box-shadow:0 0 0 1px #e2e8f0; }}
.lg-timeline .it b {{ color:{NAVY}; }}
.lg-timeline .it .tt {{ font-size:12px; color:#94a3b8; }}
</style>
"""


def esc(value) -> str:
    return html.escape(str(value if value is not None else ""))


def icon(emoji: str, size: int = 17) -> str:
    return f'<span style="font-size:{size}px;line-height:1">{emoji}</span>'


# Tailwind-style tone helpers reused by renderers
TONE_GREEN = "green"
TONE_AMBER = "amber"
TONE_RED = "red"
TONE_BLUE = "blue"
TONE_GRAY = "gray"
TONE_VIOLET = "violet"

TONE_CLASS = {
    "green": "b-green", "amber": "b-amber", "red": "b-red",
    "blue": "b-blue", "gray": "b-gray", "violet": "b-violet",
}
DOT_CLASS = {
    "green": "d-green", "amber": "d-amber", "red": "d-red",
    "blue": "d-blue", "gray": "d-gray",
}
