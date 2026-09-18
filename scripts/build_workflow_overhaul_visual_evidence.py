#!/usr/bin/env python3
"""Build the static visual-evidence pages for LOGI_FRONTEND_WORKFLOW_OVERHAUL_01.

Each page mounts the REAL production bundle (logi-shell.js + logi-shell.css —
copied verbatim from component/dist) with a backend-generated fixture, then
pre-drives the exact scenario so the reviewer SEES the changed UX in their own
browser (desktop ≈1440px or mobile ≈390px wide, resize as labelled).

PROXY_ONLY — NOT_RUNTIME_ACCEPTANCE.

These are static mounted-bundle pages (real production JS + backend-generated
fixtures), kept for DEBUG/INSPECTION value only: a reviewer can open one file
and see the changed UX without booting Streamlit. They are NOT real-browser
runtime verification and must never be counted as
DESKTOP/MOBILE_RUNTIME_VERIFIED or REAL_BROWSER_VERIFIED. The authoritative
real-browser lane is playwright/acceptance_phase_a.py on a machine with a
browser (per this repo's own protocol).
"""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "LOGI_FRONTEND_WORKFLOW_OVERHAUL_01" / "evidence" / "visual"

PHASE_B = json.loads((ROOT / "tests/component/fixtures/view_model_phase_b.json").read_text())
C2C = json.loads((ROOT / "tests/component/fixtures/view_model_c2c.json").read_text())
PAYCORR = json.loads((ROOT / "tests/component/fixtures/view_model_payment_correction.json").read_text())

# Current-shape repairs (same as the DOM tests use).
CW = json.loads((ROOT / "tests/component/fixtures/view_model_contract_workflow.json").read_text())
PHASE_B["contracts"] = CW["success"]["contracts"]
PHASE_B["receivables"] = C2C["journey"]["receivables"]

BANNER = (
    '<div style="position:fixed;top:0;left:0;right:0;z-index:9999;background:#7c2d12;color:#fff;'
    'font:700 12px/1.4 system-ui;padding:6px 14px;display:flex;gap:14px;align-items:center">'
    "<b>PROXY_ONLY · NOT_RUNTIME_ACCEPTANCE</b>"
    "<span>{label} — static mounted bundle + backend fixture for debug/inspection. "
    "This is NOT a real-browser runtime verification and NOT deployed-production proof.</span></div>"
    '<div style="height:28px"></div>'
)

PAGE = """<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="stylesheet" href="./logi-shell.css">
<style>
  body {{ margin: 0; background: #eef1f6; }}
  .hint {{ position: fixed; bottom: 8px; right: 10px; z-index: 9999; background: #ffffffcc; border: 1px solid #cbd5e1;
          color: #334155; font: 500 11.5px/1.4 system-ui; padding: 4px 10px; border-radius: 8px; }}
</style>
</head>
<body>
{banner}
<div id="root"></div>
<p class="hint">{hint}</p>
<script>
  window.__FIXTURE__ = {fixture};
  window.__SCENARIO_STEPS__ = {steps};
</script>
<script type="module">
  import mount from './logi-shell.js';
  const host = document.getElementById('root');
  const state = {{ vm: window.__FIXTURE__ }};
  const rerender = () => mount({{ name: 'logi_shell', data: state.vm, parentElement: host, setTriggerValue: () => {{}} }});
  rerender();
  const tick = (ms) => new Promise((r) => setTimeout(r, ms));
  const text = (el) => (el?.textContent || '').replace(/\\s+/g, ' ').trim();
  const byText = (needle, sel = 'a,button') =>
    [...document.querySelectorAll(sel)].find((el) => text(el).includes(needle));
  (async () => {{
    for (const step of window.__SCENARIO_STEPS__ || []) {{
      if (step.waitMs) {{ await tick(step.waitMs); continue; }}
      if (step.type === 'invoke') {{
        state.vm = step.data ?? state.vm;
        if (step.mutate === 'refusal') {{
          const id = [...document.querySelectorAll('[data-testid]')]
            .map((n) => (n.textContent || '').match(/PAY-REQ-[0-9A-Z-]+/)?.[0])
            .find(Boolean);
          state.vm = {{ ...state.vm, lastWrites: [{{ event: 'payment_record', ok: false, requestId: id, shipmentId: step.shipmentId, error: 'Bạn không có quyền thực hiện giao dịch tài chính.' }}] }};
        }}
        if (step.mutate === 'success') {{
          const id = [...document.querySelectorAll('[data-testid], #payment-record-sheet, #receivable-pay-sheet')]
            .map((n) => (n.textContent || '').match(/PAY-REQ-[0-9A-Z-]+/)?.[0])
            .find(Boolean);
          state.vm = {{ ...state.vm, lastWrites: [{{ event: 'payment_record', ok: true, requestId: id, shipmentId: step.shipmentId }}] }};
        }}
        rerender();
        await tick(240);
        continue;
      }}
      if (step.type === 'click') {{
        const el = byText(step.text, step.sel || 'a,button');
        if (el) {{ el.click(); await tick(160); }}
        continue;
      }}
      if (step.type === 'type') {{
        const input = [...document.querySelectorAll('input')].find((i) => (i.placeholder || '').startsWith(step.placeholder));
        if (input) {{
          const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
          setter.call(input, step.value);
          input.dispatchEvent(new Event('input', {{ bubbles: true }}));
          await tick(120);
        }}
        continue;
      }}
    }}
  }})();
</script>
</body>
</html>
"""

SCENARIOS = [
    {
        "file": "01_home_desktop.html",
        "title": "Home — desktop",
        "label": "01 · Home ≈1440×900",
        "hint": "Home: 1 priority area → exceptions/running → 1 snapshot (tiles ONCE) → money & docs",
        "vm": PHASE_B,
        "steps": [{"waitMs": 400}],
    },
    {
        "file": "02_home_mobile.html",
        "title": "Home — mobile",
        "label": "02 · Home ≈390×844",
        "hint": "Resize window to ≈390px for the mobile card layout + bottom nav",
        "vm": PHASE_B,
        "steps": [{"waitMs": 400}],
    },
    {
        "file": "03_shipments_filtered.html",
        "title": "Shipments — filter context",
        "label": "03 · Shipments (lọc)",
        "hint": "Search 'LO-03' + status chip — context lives in the route params now",
        "vm": PHASE_B,
        "steps": [
            {"type": "click", "text": "Lô Hàng"},
            {"waitMs": 200},
            {"type": "type", "placeholder": "Nhập mã lô", "value": "LO-03"},
            {"type": "click", "text": "Lọc"},
            {"type": "click", "text": "Chờ thông quan"},
            {"waitMs": 200},
        ],
    },
    {
        "file": "04_shipment_detail_finance.html",
        "title": "Shipment Detail — finance workspace",
        "label": "04 · Detail · Tài chính",
        "hint": "Collapsed 'Sửa thông tin lô' disclosure; tabs right under the next action",
        "vm": PAYCORR["before"],
        "steps": [
            {"type": "click", "text": "Lô Hàng"},
            {"waitMs": 200},
            {"type": "click", "text": PAYCORR["shipment"]},
            {"waitMs": 200},
            {"type": "click", "text": "Tài chính / Công nợ"},
            {"waitMs": 300},
        ],
    },
    {
        "file": "05_payment_sheet_pending.html",
        "title": "Payment sheet — pending (ĐANG CHỜ BACKEND XÁC NHẬN)",
        "label": "05 · Pay sheet · PENDING",
        "hint": "Submit → pending: sheet open, fields frozen, truthful waiting state, no green",
        "vm": PAYCORR["before"],
        "steps": [
            {"type": "click", "text": "Lô Hàng"},
            {"waitMs": 200},
            {"type": "click", "text": PAYCORR["shipment"]},
            {"waitMs": 200},
            {"type": "click", "text": "Tài chính / Công nợ"},
            {"waitMs": 200},
            {"type": "click", "text": "GHI NHẬN THANH TOÁN"},
            {"waitMs": 200},
            {"type": "type", "placeholder": "VD: 150000000", "value": "50.000.000"},
            {"type": "click", "text": "LƯU KHOẢN THU"},
            {"waitMs": 300},
        ],
    },
    {
        "file": "06_payment_sheet_refused.html",
        "title": "Payment sheet — backend refusal keeps the form",
        "label": "06 · Pay sheet · REFUSED",
        "hint": "Refusal: sheet stays open, amount preserved, backend error inline, no fake success",
        "vm": PAYCORR["before"],
        "steps": [
            {"type": "click", "text": "Lô Hàng"},
            {"waitMs": 200},
            {"type": "click", "text": PAYCORR["shipment"]},
            {"waitMs": 200},
            {"type": "click", "text": "Tài chính / Công nợ"},
            {"waitMs": 200},
            {"type": "click", "text": "GHI NHẬN THANH TOÁN"},
            {"waitMs": 200},
            {"type": "type", "placeholder": "VD: 150000000", "value": "50.000.000"},
            {"type": "click", "text": "LƯU KHOẢN THU"},
            {"waitMs": 300},
            {"type": "invoke", "mutate": "refusal", "shipmentId": PAYCORR["shipment"]},
            {"waitMs": 300},
        ],
    },
    {
        "file": "07_payment_sheet_success.html",
        "title": "Payment sheet — correlated success closes, THEN green",
        "label": "07 · Pay sheet · SUCCESS",
        "hint": "Only the correlated backend answer closes the sheet and shows green",
        "vm": PAYCORR["before"],
        "steps": [
            {"type": "click", "text": "Lô Hàng"},
            {"waitMs": 200},
            {"type": "click", "text": PAYCORR["shipment"]},
            {"waitMs": 200},
            {"type": "click", "text": "Tài chính / Công nợ"},
            {"waitMs": 200},
            {"type": "click", "text": "GHI NHẬN THANH TOÁN"},
            {"waitMs": 200},
            {"type": "type", "placeholder": "VD: 150000000", "value": "50.000.000"},
            {"type": "click", "text": "LƯU KHOẢN THU"},
            {"waitMs": 300},
            {"type": "invoke", "mutate": "success", "shipmentId": PAYCORR["shipment"]},
            {"waitMs": 300},
        ],
    },
    {
        "file": "08_receivables_context.html",
        "title": "Receivables — search + filters in the route",
        "label": "08 · Receivables",
        "hint": "Thu tiền desk: search + outstanding filter restored after back-navigation",
        "vm": PHASE_B,
        "steps": [
            {"type": "click", "text": "Thu tiền"},
            {"waitMs": 200},
            {"type": "type", "placeholder": "Tìm mã lô (LO-0306)", "value": "LO-03"},
            {"type": "click", "text": "Lọc"},
            {"type": "click", "text": "Chỉ lô còn phải thu"},
            {"waitMs": 200},
        ],
    },
    {
        "file": "09_role_sandbox.html",
        "title": "Role preview — sandbox only, labelled Xem trước",
        "label": "09 · Role preview (sandbox)",
        "hint": "Sandbox: switcher labelled 'Xem trước', menu states display-only",
        "vm": {**PHASE_B, "environment": {**PHASE_B["environment"], "isSandbox": True}},
        "steps": [
            {"waitMs": 300},
            {"type": "click", "text": "Thu Hằng"},
            {"waitMs": 200},
        ],
    },
    {
        "file": "10_role_production.html",
        "title": "Role — production-like runtime shows the actual role only",
        "label": "10 · Role (production-like)",
        "hint": "No switcher, no role buttons — just the logged-in identity + role",
        "vm": {**PHASE_B, "environment": {**PHASE_B["environment"], "isSandbox": False, "label": "Production", "transport": "REAL_MONGO"}},
        "steps": [{"waitMs": 300}],
    },
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for sc in SCENARIOS:
        html = PAGE.format(
            title=sc["title"],
            label=sc["label"],
            hint=sc["hint"],
            banner=BANNER.format(label=sc["label"]),
            fixture=json.dumps(sc["vm"], ensure_ascii=False),
            steps=json.dumps(sc["steps"], ensure_ascii=False),
        )
        (OUT / sc["file"]).write_text(html, encoding="utf-8")
        print("wrote", sc["file"])
    index_rows = "\n".join(
        f'<li><a href="./{sc["file"]}">{sc["label"]}</a> — {sc["title"]}</li>' for sc in SCENARIOS
    )
    index = (
        "<!DOCTYPE html><html lang='vi'><head><meta charset='utf-8'>"
        "<title>Visual evidence index</title>"
        "<style>body{font:15px/1.6 system-ui;max-width:860px;margin:40px auto;padding:0 16px}"
        "h1{color:#0f2a4a}li{margin:6px 0}a{color:#1e5aa8;font-weight:600}</style></head><body>"
        "<h1>LOGI_FRONTEND_WORKFLOW_OVERHAUL_01 — visual evidence (sandbox)</h1>"
        "<p>Each page mounts the <b>real production bundle</b> (component/dist) with a "
        "<b>backend-generated fixture</b> (isolated mongomock staging) and pre-drives the scenario. "
        "Open a page, then resize the window to the labelled viewport (desktop ≈1440×900, "
        "mobile ≈390×844). Sandbox visual behavior only — not deployed-production proof.</p>"
        f"<ol>{index_rows}</ol></body></html>"
    )
    (OUT / "index.html").write_text(index, encoding="utf-8")
    print("wrote index.html")


if __name__ == "__main__":
    main()
