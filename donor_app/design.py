"""Donor design tokens — exact Logi-good colour, type, spacing system."""
from __future__ import annotations

DONOR_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700;800&display=swap');

:root {
  --lg-navy-950:#0a1f3a; --lg-navy-900:#0f2a4a; --lg-navy-800:#14365e;
  --lg-navy-700:#1a4d8f; --lg-navy-600:#1e5aa8; --lg-navy-100:#dbe7f5; --lg-navy-50:#eef4fb;
  --lg-bg:#eef1f6; --lg-ink:#1a2433; --lg-line:#e4e9f1; --lg-line-2:#e2e8f0;
  --lg-text:#0f2a4a; --lg-muted:#5b6b82; --lg-muted-2:#64748b; --lg-soft:#f1f5fa;
  --lg-amber:#f59e0b; --lg-red:#dc2626; --lg-green:#10b981; --lg-blue:#2563eb;
  --lg-amber-bg:#fff7ed; --lg-amber-border:#fed7aa;
  --lg-red-bg:#fef2f2; --lg-red-border:#fecaca;
  --lg-green-bg:#ecfdf5; --lg-green-border:#bbf7d0;
  --lg-blue-bg:#eff6ff; --lg-blue-border:#bfdbfe;
  --lg-shadow-card:0 1px 2px rgba(15,42,74,.04);
  --lg-shadow-lift:0 10px 28px -10px rgba(15,42,74,.25);
  --lg-shadow-header:0 1px 12px rgba(15,42,74,.08);
  --lg-shadow-soft:0 4px 14px rgba(15,42,74,.06);
}
html, body, .stApp { font-family:'Be Vietnam Pro', system-ui, -apple-system, sans-serif !important; background:var(--lg-bg) !important; color:var(--lg-ink) !important; font-size:15.5px; line-height:1.55; -webkit-font-smoothing:antialiased; }
.stApp > header { background: transparent !important; }
#MainMenu, footer, .viewerBadge, .stDeployButton { display:none !important; }
section.main > div.block-container { padding-top:0 !important; padding-bottom:0 !important; padding-left:0 !important; padding-right:0 !important; max-width:100% !important; }

/* ===== HEADER ===== */
.lg-header { position:sticky; top:0; z-index:40; background:#fff; border-bottom:1px solid var(--lg-line-2); box-shadow:var(--lg-shadow-header); }
.lg-header-inner { display:flex; align-items:center; gap:8px; padding:0 16px; height:64px; max-width:1600px; margin:0 auto; }
.lg-logo { display:flex; align-items:center; gap:10px; flex-shrink:0; text-decoration:none; }
.lg-logo-mark { width:40px; height:40px; border-radius:12px; background:linear-gradient(135deg,#1e5aa8,#0a1f3a); display:grid; place-items:center; color:#fff; font-weight:800; font-size:18px; box-shadow:0 1px 2px rgba(0,0,0,.18); }
.lg-logo-text { line-height:1.1; }
.lg-logo-title { display:block; font-weight:800; font-size:14.5px; color:var(--lg-text); }
.lg-logo-sub { display:block; font-size:11.5px; color:#64748b; font-weight:500; }
.lg-pill { font-size:11px; font-weight:800; letter-spacing:.04em; background:#ede9fe; color:#5b21b6; border:1px solid #c4b5fd; border-radius:6px; padding:2px 6px; margin-left:6px; }

.lg-search { flex:1; max-width:560px; margin:0 auto; position:relative; }
.lg-search-input { display:flex; align-items:center; background:#f8fafc; border:2px solid var(--lg-line-2); border-radius:12px; padding:0 8px 0 12px; height:48px; transition:border-color .15s; }
.lg-search-input:focus-within { border-color:#1e5aa8; background:#fff; }
.lg-search-input input { border:none; outline:none; background:transparent; width:100%; font-size:15px; padding:6px 8px; color:var(--lg-ink); }
.lg-search-input input::placeholder { color:#94a3b8; }
.lg-search-icon { color:#94a3b8; flex-shrink:0; }

.lg-icon-btn { width:44px; height:44px; display:grid; place-items:center; border-radius:12px; background:transparent; border:none; cursor:pointer; color:var(--lg-text); position:relative; }
.lg-icon-btn:hover { background:#f1f5f9; }
.lg-icon-btn .lg-badge { position:absolute; top:2px; right:2px; min-width:20px; height:20px; padding:0 5px; border-radius:999px; background:#dc2626; color:#fff; font-size:11px; font-weight:800; display:grid; place-items:center; }
.lg-add-btn { display:inline-flex; align-items:center; gap:6px; height:44px; padding:0 18px; border-radius:12px; background:var(--lg-navy-900); color:#fff; font-weight:700; font-size:14.5px; border:none; cursor:pointer; }
.lg-add-btn:hover { background:var(--lg-navy-800); }
.lg-role-chip { display:flex; align-items:center; gap:8px; border:2px solid var(--lg-line-2); border-radius:12px; padding:4px 12px 4px 6px; background:#fff; cursor:pointer; }
.lg-role-avatar { width:32px; height:32px; border-radius:8px; display:grid; place-items:center; color:#fff; font-weight:800; font-size:13px; }
.lg-role-name { font-size:13px; font-weight:700; color:var(--lg-text); line-height:1.1; }
.lg-role-meta { font-size:11.5px; color:#64748b; line-height:1.1; }

/* ===== MAIN GRID ===== */
.lg-shell { display:flex; max-width:1600px; margin:0 auto; }
.lg-sidebar { width:264px; flex-shrink:0; background:#fff; border-right:1px solid var(--lg-line); padding:12px 12px 40px; position:sticky; top:64px; align-self:flex-start; max-height:calc(100vh - 64px); overflow-y:auto; }
.lg-main { flex:1; min-width:0; padding:16px 20px 100px; }
@media (max-width:1023px) { .lg-sidebar { display:none; } .lg-main { padding:12px 12px 110px; } }

.lg-nav-group { margin-bottom:16px; }
.lg-nav-heading { padding:0 12px 6px; font-size:11.5px; font-weight:800; letter-spacing:.04em; color:#94a3b8; text-transform:uppercase; }
.lg-nav-item { display:flex; align-items:center; gap:10px; padding:10px 12px; border-radius:12px; font-size:14.5px; font-weight:500; color:#334155; margin-bottom:2px; text-decoration:none; }
.lg-nav-item:hover { background:#f1f5f9; color:var(--lg-text); }
.lg-nav-item.active { background:var(--lg-navy-900); color:#fff; box-shadow:0 4px 8px rgba(15,42,74,.18); }
.lg-nav-item .lg-nav-count { margin-left:auto; background:#dc2626; color:#fff; border-radius:999px; font-size:11px; font-weight:800; min-width:22px; height:22px; padding:0 6px; display:grid; place-items:center; }
.lg-help-card { margin:8px 4px 0; padding:16px; border-radius:16px; background:linear-gradient(135deg,#0f2a4a,#1e5aa8); color:#fff; }
.lg-help-card h4 { font-size:14px; font-weight:700; margin:0 0 4px; }
.lg-help-card p { font-size:12.5px; color:#bfdbfe; margin:0 0 10px; }
.lg-help-card a { display:inline-flex; align-items:center; gap:4px; background:#fff; color:var(--lg-navy-900); padding:8px 12px; border-radius:8px; font-size:13.5px; font-weight:700; text-decoration:none; }

/* ===== CARDS / SURFACES ===== */
.lg-card { background:#fff; border:1px solid var(--lg-line); border-radius:16px; padding:16px; box-shadow:var(--lg-shadow-card); }
.lg-card-soft { background:#f8fafc; border:1px solid var(--lg-line); border-radius:12px; padding:14px; }
.lg-section-title { display:flex; align-items:flex-start; justify-content:space-between; gap:12px; margin-bottom:12px; }
.lg-section-title h2 { font-size:18px; font-weight:800; color:var(--lg-text); margin:0; }
.lg-section-title p { font-size:13.5px; color:var(--lg-muted); margin:2px 0 0; }
.lg-section-icon { width:36px; height:36px; border-radius:10px; background:var(--lg-navy-900); color:#fff; display:grid; place-items:center; flex-shrink:0; }

/* HERO BANNER */
.lg-hero { border-radius:24px; background:linear-gradient(135deg,#0a1f3a 0%,#0f2a4a 45%,#1e5aa8 100%); color:#fff; padding:24px 28px; position:relative; overflow:hidden; }
.lg-hero::after { content:""; position:absolute; right:-64px; top:-64px; width:256px; height:256px; border-radius:50%; background:rgba(255,255,255,.10); }
.lg-hero::before { content:""; position:absolute; right:40px; bottom:0; width:128px; height:128px; border-radius:50%; background:rgba(255,255,255,.05); }
.lg-hero .lg-kicker { font-size:13px; color:#bfdbfe; font-weight:600; letter-spacing:.04em; text-transform:uppercase; }
.lg-hero h1 { font-size:24px; font-weight:800; margin:4px 0 0; }
.lg-hero p { font-size:15px; color:#bfdbfe; margin:6px 0 0; max-width:640px; }
.lg-hero .lg-hero-ctas { display:flex; flex-wrap:wrap; gap:8px; margin-top:14px; }
.lg-btn-white { background:#fff; color:var(--lg-navy-900); padding:12px 20px; border-radius:12px; font-weight:800; font-size:15px; display:inline-flex; align-items:center; gap:6px; border:none; cursor:pointer; min-height:48px; }
.lg-btn-ghost { background:transparent; color:#fff; padding:12px 20px; border-radius:12px; font-weight:700; font-size:15px; border:2px solid rgba(255,255,255,.4); cursor:pointer; min-height:48px; }

/* TONE BADGES */
.lg-badge { display:inline-flex; align-items:center; gap:6px; font-weight:600; border:1px solid; border-radius:999px; padding:6px 12px; font-size:13.5px; white-space:nowrap; }
.lg-badge.sm { font-size:12.5px; padding:4px 10px; }
.lg-badge.green { background:#ecfdf5; color:#065f46; border-color:#bbf7d0; }
.lg-badge.amber { background:#fff7ed; color:#9a3412; border-color:#fed7aa; }
.lg-badge.red { background:#fef2f2; color:#991b1b; border-color:#fecaca; }
.lg-badge.blue { background:#eff6ff; color:#1e40af; border-color:#bfdbfe; }
.lg-badge.gray { background:#f1f5f9; color:#334155; border-color:#e2e8f0; }

.lg-dot { display:inline-block; width:10px; height:10px; border-radius:50%; }
.lg-dot.green { background:#10b981; }
.lg-dot.amber { background:#f59e0b; }
.lg-dot.red { background:#dc2626; }
.lg-dot.blue { background:#2563eb; }
.lg-dot.gray { background:#94a3b8; }

/* NEXT-ACTION BANNER */
.lg-na { border:2px solid; border-radius:16px; padding:16px 20px; display:flex; flex-direction:row; align-items:center; gap:16px; }
.lg-na.red { background:linear-gradient(90deg,#fef2f2,#fff7ed); border-color:#fecaca; }
.lg-na.amber { background:linear-gradient(90deg,#fff7ed,#fffbeb); border-color:#fed7aa; }
.lg-na.green { background:linear-gradient(90deg,#ecfdf5,#f0fdfa); border-color:#bbf7d0; }
.lg-na.blue { background:linear-gradient(90deg,#eff6ff,#eef2ff); border-color:#bfdbfe; }
.lg-na-icon { width:44px; height:44px; border-radius:12px; display:grid; place-items:center; color:#fff; flex-shrink:0; }
.lg-na-icon.red { background:#dc2626; }
.lg-na-icon.amber { background:#f59e0b; }
.lg-na-icon.green { background:#10b981; }
.lg-na-icon.blue { background:#2563eb; }
.lg-na-kicker { font-size:12.5px; font-weight:700; color:#64748b; text-transform:uppercase; letter-spacing:.04em; }
.lg-na-title { font-size:17px; font-weight:800; color:var(--lg-text); margin:0; }
.lg-na-desc { font-size:14px; color:#475569; margin:4px 0 0; }
.lg-na-btn { background:var(--lg-navy-900); color:#fff; padding:14px 24px; border-radius:12px; font-weight:800; font-size:15.5px; display:inline-flex; align-items:center; gap:6px; border:none; cursor:pointer; min-height:52px; box-shadow:0 8px 18px rgba(15,42,74,.22); flex-shrink:0; }

/* NEXT-ACTION CARDS GRID */
.lg-next-grid { display:grid; grid-template-columns:repeat(5, 1fr); gap:12px; }
@media (max-width:1279px) { .lg-next-grid { grid-template-columns:repeat(2, 1fr); } }
.lg-next-card { background:#fff; border:1px solid var(--lg-line); border-radius:16px; padding:14px; display:flex; gap:12px; text-decoration:none; color:inherit; transition:transform .15s, box-shadow .15s; overflow:hidden; min-height:88px; }
.lg-next-card:hover { transform:translateY(-2px); box-shadow:var(--lg-shadow-lift); }
.lg-next-bar { width:6px; border-radius:6px; }
.lg-next-icon { width:44px; height:44px; border-radius:12px; display:grid; place-items:center; color:#fff; flex-shrink:0; }
.lg-next-card-body { flex:1; min-width:0; }
.lg-next-card-title { font-weight:800; color:var(--lg-text); font-size:15px; display:flex; align-items:center; gap:8px; }
.lg-next-card-count { font-size:12px; font-weight:800; background:#dc2626; color:#fff; border-radius:999px; min-width:24px; height:24px; padding:0 6px; display:grid; place-items:center; }
.lg-next-card-desc { font-size:13px; color:#64748b; margin:2px 0 0; line-height:1.4; }
.lg-next-card-cta { display:inline-flex; align-items:center; gap:4px; font-size:13.5px; font-weight:700; color:#1e5aa8; margin-top:6px; }

/* KPI GRID */
.lg-kpi-grid { display:grid; grid-template-columns:repeat(5, 1fr); gap:12px; }
@media (max-width:1023px) { .lg-kpi-grid { grid-template-columns:repeat(2, 1fr); } }
.lg-kpi { background:#fff; border:1px solid var(--lg-line); border-radius:16px; padding:14px 16px; text-decoration:none; color:inherit; transition:transform .15s, box-shadow .15s; }
.lg-kpi:hover { transform:translateY(-2px); box-shadow:var(--lg-shadow-lift); }
.lg-kpi .label { font-size:13px; font-weight:600; color:#64748b; }
.lg-kpi .value { font-size:26px; font-weight:800; color:var(--lg-text); line-height:1.1; margin-top:2px; }
.lg-kpi .sub { font-size:12.5px; color:#94a3b8; margin-top:2px; }
.lg-kpi.green { background:#10b981; color:#fff; }
.lg-kpi.green .label, .lg-kpi.green .sub { color:#d1fae5; }
.lg-kpi.green .value { color:#fff; }
.lg-kpi.red { background:#dc2626; color:#fff; }
.lg-kpi.red .label, .lg-kpi.red .sub { color:#fecaca; }
.lg-kpi.red .value { color:#fff; }
.lg-kpi.amber { background:#fff; border-color:#fde68a; }
.lg-kpi.amber .value { color:var(--lg-text); }
.lg-kpi.amber .sub { color:#b45309; font-weight:600; }

/* TWO-COL LAYOUT */
.lg-2col { display:grid; grid-template-columns:1fr 1fr; gap:16px; }
@media (max-width:1023px) { .lg-2col { grid-template-columns:1fr; } }

/* TABLE */
.lg-tbl { width:100%; border-collapse:collapse; font-size:14px; min-width:980px; }
.lg-tbl th { font-size:12.5px; text-transform:uppercase; letter-spacing:.04em; color:#5b6b82; font-weight:700; background:#f1f5fa; padding:12px 14px; text-align:left; border-bottom:1px solid var(--lg-line); }
.lg-tbl td { padding:12px 14px; border-bottom:1px solid var(--lg-line); vertical-align:middle; }
.lg-tbl tr:last-child td { border-bottom:none; }
.lg-tbl tr:hover td { background:#f8fafc; }
.lg-tbl-wrap { overflow-x:auto; background:#fff; border:1px solid var(--lg-line); border-radius:16px; }

/* BUTTONS */
.lg-btn { display:inline-flex; align-items:center; justify-content:center; gap:6px; padding:12px 20px; border-radius:12px; font-weight:700; font-size:15.5px; min-height:48px; border:1px solid transparent; cursor:pointer; text-decoration:none; }
.lg-btn.primary { background:var(--lg-navy-900); color:#fff; box-shadow:0 4px 10px rgba(15,42,74,.16); }
.lg-btn.primary:hover { background:var(--lg-navy-800); }
.lg-btn.success { background:#059669; color:#fff; box-shadow:0 4px 10px rgba(5,150,105,.18); }
.lg-btn.success:hover { background:#047857; }
.lg-btn.ghost { background:#fff; color:var(--lg-text); border-color:#cbd5e1; }
.lg-btn.ghost:hover { background:#f8fafc; }
.lg-btn.danger { background:#fff; color:#b91c1c; border-color:#fecaca; }
.lg-btn.danger:hover { background:#fef2f2; }
.lg-btn.sm { padding:8px 12px; min-height:40px; font-size:13.5px; border-radius:10px; }
.lg-btn.lg { padding:14px 24px; min-height:56px; font-size:17px; }
.lg-btn.full { width:100%; }

/* TABS */
.lg-tabs { display:flex; gap:8px; overflow-x:auto; padding:12px 16px 0; border-top:1px solid var(--lg-line); margin-top:12px; }
.lg-tab { padding:12px 16px; border-radius:12px; font-size:14.5px; font-weight:700; background:#fff; border:2px solid var(--lg-line); color:#475569; cursor:pointer; white-space:nowrap; min-height:48px; }
.lg-tab.active { background:var(--lg-navy-900); color:#fff; border-color:var(--lg-navy-900); }

/* INPUTS / FIELDS */
.lg-field { display:block; margin-bottom:12px; }
.lg-field-label { display:block; font-size:14px; font-weight:600; color:#475569; margin-bottom:6px; }
.lg-field-label .req { color:#dc2626; font-weight:700; }
.lg-field-hint { display:block; font-size:13px; color:#64748b; margin-top:4px; }
.lg-field-error { display:block; font-size:13.5px; color:#b91c1c; font-weight:600; margin-top:4px; }
.lg-input, .lg-select, .lg-textarea { width:100%; border:2px solid var(--lg-line-2); background:#fff; border-radius:12px; padding:12px 14px; font-size:15.5px; min-height:48px; color:var(--lg-ink); }
.lg-input.missing, .lg-select.missing, .lg-textarea.missing { border-color:#fbbf24; background:#fffbeb; }
.lg-input.invalid, .lg-select.invalid, .lg-textarea.invalid { border-color:#f87171; background:#fef2f2; }
.lg-input:focus, .lg-select:focus, .lg-textarea:focus { outline:none; border-color:#1e5aa8; }
.lg-textarea { min-height:96px; resize:vertical; font-family:inherit; }

/* STATE ROW */
.lg-state-row { display:flex; justify-content:space-between; gap:12px; padding:8px 0; border-bottom:1px solid #f1f5f9; }
.lg-state-row:last-child { border-bottom:none; }
.lg-state-row .lbl { font-size:13.5px; color:#64748b; font-weight:500; flex-shrink:0; }
.lg-state-row .val { text-align:right; font-weight:600; color:#1e293b; font-size:14.5px; }

/* MISSING BOX */
.lg-missing { border:2px dashed #fbbf24; background:#fffbeb; border-radius:12px; padding:14px; display:flex; flex-direction:row; align-items:center; gap:10px; }
.lg-missing .body { flex:1; }
.lg-missing .body h5 { font-size:15px; color:#92400e; font-weight:700; margin:0; }
.lg-missing .body p { font-size:13.5px; color:#b45309; margin:2px 0 0; }
.lg-missing .btn { background:#f59e0b; color:#fff; padding:10px 16px; border-radius:10px; font-weight:700; font-size:14.5px; border:none; cursor:pointer; min-height:44px; white-space:nowrap; }
.lg-missing .btn:hover { background:#d97706; }

/* STICKY MOBILE ACTION */
.lg-sticky-mobile { position:fixed; left:0; right:0; bottom:0; background:rgba(255,255,255,.96); backdrop-filter:blur(8px); border-top:1px solid var(--lg-line-2); padding:10px 12px calc(env(safe-area-inset-bottom) + 10px); z-index:30; display:none; }
@media (max-width:1023px) { .lg-sticky-mobile { display:block; } }

/* MOBILE BOTTOM NAV */
.lg-mobile-nav { position:fixed; left:0; right:0; bottom:0; background:#fff; border-top:1px solid var(--lg-line-2); box-shadow:0 -4px 20px rgba(0,0,0,.08); display:none; z-index:40; padding-bottom:env(safe-area-inset-bottom); }
@media (max-width:1023px) { .lg-mobile-nav { display:grid; grid-template-columns:repeat(5,1fr); } }
.lg-mobile-nav a, .lg-mobile-nav button { background:transparent; border:none; padding:8px 4px 6px; display:flex; flex-direction:column; align-items:center; gap:2px; text-decoration:none; color:#94a3b8; font-size:11.5px; font-weight:600; cursor:pointer; }
.lg-mobile-nav a.active { color:var(--lg-navy-900); }
.lg-mobile-nav a.active svg { stroke-width:2.4; }
.lg-mobile-nav .active-bar { width:32px; height:4px; border-radius:999px; background:var(--lg-navy-900); margin-top:2px; }
.lg-mobile-nav .add-pill { width:44px; height:32px; margin-top:-12px; border-radius:16px; background:var(--lg-navy-900); color:#fff; display:grid; place-items:center; box-shadow:0 4px 12px rgba(15,42,74,.28); }
@media (min-width:1024px) { .lg-mobile-nav { display:none !important; } }

/* DRAWER (mobile nav) */
.lg-drawer-mask { position:fixed; inset:0; background:rgba(15,23,42,.5); z-index:50; }
.lg-drawer { position:fixed; left:0; top:0; bottom:0; width:300px; max-width:85vw; background:#fff; box-shadow:0 10px 40px rgba(0,0,0,.18); z-index:51; overflow-y:auto; }
.lg-drawer-header { display:flex; align-items:center; justify-content:space-between; padding:14px 16px; border-bottom:1px solid var(--lg-line); background:#fff; position:sticky; top:0; }
.lg-drawer-header h4 { font-size:15px; font-weight:800; color:var(--lg-text); margin:0; }
.lg-drawer-close { width:44px; height:44px; display:grid; place-items:center; border:none; background:transparent; border-radius:12px; cursor:pointer; }
.lg-drawer-close:hover { background:#f1f5f9; }
@media (min-width:1024px) { .lg-drawer, .lg-drawer-mask { display:none !important; } }

/* QUICK ADD BOTTOM SHEET */
.lg-sheet-mask { position:fixed; inset:0; background:rgba(15,23,42,.5); z-index:60; }
.lg-sheet { position:fixed; left:0; right:0; bottom:0; background:#fff; border-top-left-radius:24px; border-top-right-radius:24px; padding:20px 20px calc(env(safe-area-inset-bottom) + 20px); z-index:61; max-height:90vh; overflow-y:auto; box-shadow:0 -10px 30px rgba(0,0,0,.18); }
@media (min-width:640px) { .lg-sheet { left:50%; transform:translateX(-50%); right:auto; width:520px; max-width:92vw; bottom:auto; top:50%; transform:translate(-50%,-50%); border-radius:24px; padding:20px; } }
.lg-sheet-grab { width:48px; height:6px; background:#cbd5e1; border-radius:999px; margin:0 auto 12px; }
.lg-sheet h3 { font-size:18px; font-weight:800; color:var(--lg-text); margin:0 0 4px; }
.lg-sheet p.hint { font-size:13.5px; color:#64748b; margin:0 0 12px; }
.lg-sheet-row { display:flex; align-items:center; gap:12px; padding:14px; border:2px solid #f1f5f9; border-radius:16px; background:#fff; cursor:pointer; text-align:left; width:100%; }
.lg-sheet-row:hover { border-color:#1e5aa8; }
.lg-sheet-row + .lg-sheet-row { margin-top:8px; }
.lg-sheet-row .ico { width:44px; height:44px; border-radius:12px; display:grid; place-items:center; flex-shrink:0; }
.lg-sheet-row .ttl { font-size:15px; font-weight:700; color:var(--lg-text); }
.lg-sheet-row .dsc { font-size:13px; color:#64748b; }

/* NOTIF DRAWER */
.lg-notif { position:fixed; right:0; top:0; bottom:0; width:380px; max-width:92vw; background:#fff; box-shadow:0 10px 30px rgba(0,0,0,.18); z-index:61; display:flex; flex-direction:column; }
.lg-notif-header { display:flex; align-items:center; justify-content:space-between; padding:14px 16px; border-bottom:1px solid var(--lg-line); }
.lg-notif-header h4 { font-size:16px; font-weight:800; color:var(--lg-text); margin:0; }
.lg-notif-list { flex:1; overflow-y:auto; padding:10px; }
.lg-notif-item { background:#fff; border:1px solid var(--lg-line); border-radius:16px; padding:12px; margin-bottom:8px; transition:box-shadow .15s, transform .15s; }
.lg-notif-item:hover { box-shadow:var(--lg-shadow-soft); transform:translateY(-1px); }
.lg-notif-item .dot { width:10px; height:10px; border-radius:50%; flex-shrink:0; margin-top:6px; }
.lg-notif-item h5 { font-size:14.5px; color:var(--lg-text); font-weight:700; margin:0; }
.lg-notif-item p { font-size:13.5px; color:#475569; margin:2px 0 0; }
.lg-notif-item time { font-size:12px; color:#94a3b8; }
.lg-notif-foot { padding:10px; border-top:1px solid var(--lg-line); }

/* TOAST */
.lg-toast-stack { position:fixed; left:12px; right:12px; bottom:90px; z-index:70; display:flex; flex-direction:column; gap:8px; pointer-events:none; }
@media (min-width:768px) { .lg-toast-stack { left:auto; right:24px; bottom:24px; width:380px; } }
.lg-toast { background:var(--lg-navy-900); color:#fff; padding:14px 16px; border-radius:16px; display:flex; align-items:flex-start; gap:10px; box-shadow:0 10px 30px rgba(0,0,0,.2); pointer-events:auto; }
.lg-toast .ico { width:36px; height:36px; border-radius:10px; display:grid; place-items:center; flex-shrink:0; color:#fff; font-weight:800; }
.lg-toast .body { flex:1; min-width:0; }
.lg-toast .body h5 { font-size:14.5px; margin:0; font-weight:700; }
.lg-toast .body p { font-size:13px; color:#bfdbfe; margin:2px 0 0; }
.lg-toast .close { background:rgba(255,255,255,.1); border:none; width:32px; height:32px; border-radius:8px; color:#fff; cursor:pointer; }

/* SEARCH RESULTS */
.lg-search-results { position:absolute; top:56px; left:0; right:0; background:#fff; border-radius:16px; border:1px solid var(--lg-line); box-shadow:0 20px 40px rgba(15,42,74,.16); padding:6px; z-index:50; max-height:70vh; overflow:auto; }
.lg-search-row { display:flex; align-items:center; gap:10px; padding:10px 12px; border-radius:12px; text-decoration:none; color:inherit; cursor:pointer; }
.lg-search-row:hover { background:#f8fafc; }
.lg-search-row .ico { width:36px; height:36px; border-radius:10px; display:grid; place-items:center; }
.lg-search-row .title { font-size:14.5px; font-weight:700; color:var(--lg-text); display:block; }
.lg-search-row .meta { font-size:12.5px; color:#64748b; }

/* FOOTER */
.lg-footer { margin-top:40px; padding:16px; text-align:center; font-size:12.5px; color:#94a3b8; }

/* HIDE Streamlit default widgets where we have our own custom HTML */
.lg-hide-input { display:none; }

/* Donor's little utility classes */
.lg-link { color:#1e5aa8; font-weight:700; text-decoration:none; }
.lg-link:hover { text-decoration:underline; }
.lg-mono { font-family: 'JetBrains Mono', ui-monospace, monospace; }
.lg-text-muted { color:#64748b; }
.lg-text-ink { color:var(--lg-text); }
.lg-text-red { color:#b91c1c; }
.lg-text-green { color:#047857; }
.lg-text-amber { color:#b45309; }
.lg-text-sm { font-size:13.5px; }
.lg-text-xs { font-size:12.5px; }
.lg-mt-1 { margin-top:6px; } .lg-mt-2 { margin-top:12px; } .lg-mt-3 { margin-top:16px; } .lg-mt-4 { margin-top:24px; }
.lg-mb-1 { margin-bottom:6px; } .lg-mb-2 { margin-bottom:12px; } .lg-mb-3 { margin-bottom:16px; } .lg-mb-4 { margin-bottom:24px; }
.lg-flex { display:flex; } .lg-grid { display:grid; } .lg-cols-2 { grid-template-columns:1fr 1fr; gap:12px; }
.lg-cols-3 { grid-template-columns:repeat(3,1fr); gap:12px; }
.lg-cols-4 { grid-template-columns:repeat(4,1fr); gap:12px; }
@media (max-width:768px) { .lg-cols-2, .lg-cols-3, .lg-cols-4 { grid-template-columns:1fr; } }
.lg-gap-1 { gap:6px; } .lg-gap-2 { gap:12px; } .lg-gap-3 { gap:16px; }
.lg-items-center { align-items:center; } .lg-justify-between { justify-content:space-between; }
.lg-fw-700 { font-weight:700; } .lg-fw-800 { font-weight:800; }
.lg-text-right { text-align:right; }

/* Streamlit form/metric overrides */
[data-testid="stMetricValue"] { font-size:24px !important; }
div[data-testid="stForm"] { background:transparent !important; border:none !important; padding:0 !important; }
.stTabs [data-baseweb="tab-list"] { gap:8px; }
.stTabs [data-baseweb="tab"] { padding:12px 16px; font-size:14.5px; font-weight:700; }

/* Pulse dot */
.lg-pulse { animation: lgPulse 1.6s ease-in-out infinite; }
@keyframes lgPulse { 0%,100% { opacity:1; transform:scale(1);} 50% { opacity:.55; transform:scale(.8);} }
.lg-anim-slide-up { animation: lgSlideUp .28s ease both; }
@keyframes lgSlideUp { from { opacity:0; transform:translateY(14px);} to { opacity:1; transform:translateY(0);} }
</style>
"""

# Donor colour helpers
NAVY = "#0f2a4a"
NAVY_2 = "#1e5aa8"
AMBER = "#f59e0b"
RED = "#dc2626"
GREEN = "#10b981"
BLUE = "#2563eb"
GRAY = "#94a3b8"

# Status tone mapping
STATUS_TONE = {
    "Chờ lấy hàng": "amber",
    "Đang vận chuyển": "blue",
    "Chờ thông quan": "amber",
    "Chờ giao": "violet",
    "Đã giao": "green",
    "Hoàn thành": "green",
    "Đã hủy": "red",
    "Đã thông quan": "green",
    "Tạm khóa": "red",
    "Đang hoạt động": "green",
    "ĐÃ PHÁT HÀNH": "green",
    "AGREED": "green",
    "REVIEWING": "amber",
    "VOID": "red",
    "DRAFT": "gray",
    "SENT": "blue",
    "ACCEPTED": "green",
    "REJECTED": "red",
    "ĐÃ CHỐT": "green",
    "ĐÃ GỬI": "blue",
    "TỪ CHỐI": "red",
    "NHÁP": "gray",
    "Hạn hôm nay": "red",
    "Còn 3 ngày": "amber",
    "Quá hạn": "red",
    "HDMB": "blue",
    "HDNT": "emerald",
    "Khẩn": "red",
    "Cần xử lý": "amber",
    "Bình thường": "gray",
    "ok": "green",
    "ok ": "green",
    "open": "amber",
    "review": "blue",
    "unknown": "gray",
    "done": "green",
    "wait": "amber",
    "pending": "blue",
    "cancel": "red",
}

def tone_for(status: str) -> str:
    s = (status or "").strip()
    return STATUS_TONE.get(s, STATUS_TONE.get(s.lower(), "gray"))


def fmt_money(amount, ccy: str = "VND") -> str:
    """Format money in Vietnamese style."""
    if amount is None or amount == "":
        return "—"
    try:
        v = float(amount)
    except (TypeError, ValueError):
        return str(amount)
    if ccy == "VND":
        if abs(v) >= 1_000_000_000:
            return f"{v/1_000_000_000:.1f} tỷ ₫"
        if abs(v) >= 1_000_000:
            return f"{v/1_000_000:.1f} tr ₫"
        return f"{v:,.0f} ₫".replace(",", ".")
    if ccy == "USD":
        return f"${v:,.2f}"
    if ccy == "CNY":
        return f"¥{v:,.0f}"
    return f"{v:,.0f} {ccy}"


def fmt_vnd(amount) -> str:
    if amount is None or amount == "":
        return "—"
    try:
        v = int(float(amount))
    except (TypeError, ValueError):
        return str(amount)
    return f"{v:,} ₫".replace(",", ".")


def status_label(s: str) -> str:
    """Pass-through Vietnamese label, ensuring consistency."""
    return s or "—"
