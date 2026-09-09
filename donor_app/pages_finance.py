"""Finance, CEO, Tools, Admin pages."""
from __future__ import annotations

import streamlit as st

from . import design, icons, store, ui


# ===========================================================================
# COLLECT (Thu Tiền & Công Nợ)
# ===========================================================================

def render_collect():
    recs = store.get_receivables()
    kpi = store.get_kpi()["totals"]

    # KPI strip
    kpi_cards = [
        {"label": "Tổng phải thu", "value": "1.087,6 tr", "sub": "", "tone": ""},
        {"label": "Đã thu", "value": "550,0 tr", "sub": "", "tone": "green"},
        {"label": "Còn phải thu", "value": "537,6 tr", "sub": "", "tone": "red-border"},
        {"label": "Quá hạn / hạn nay", "value": "1 khoản", "sub": "", "tone": "red"},
        {"label": "Phải trả đối tác", "value": "73,8 tr", "sub": "", "tone": "amber-border"},
    ]
    style = "grid-template-columns:repeat(5,1fr)"
    cards_html = ""
    for it in kpi_cards:
        tone = it["tone"]
        bg = "#fff;border:1px solid #e4e9f1"
        tc = "#0f2a4a"
        if tone == "green":
            bg = "#10b981;color:#fff"
            tc = "#fff"
        elif tone == "red":
            bg = "#dc2626;color:#fff"
            tc = "#fff"
        elif tone == "red-border":
            bg = "#fff;border:2px solid #fecaca"
            tc = "#b91c1c"
        elif tone == "amber-border":
            bg = "#fff;border:2px solid #fde68a"
            tc = "#0f2a4a"
        cards_html += f'<div style="background:{bg};border-radius:16px;padding:14px"><p style="font-size:12.5px;font-weight:600;opacity:.7;margin:0;color:{tc}">{it["label"]}</p><p style="font-size:22px;font-weight:800;margin:2px 0 0;color:{tc}">{it["value"]}</p></div>'

    st.markdown(f'<div class="lg-kpi-grid" style="{style};margin-bottom:16px">{cards_html}</div>', unsafe_allow_html=True)

    st.markdown("""
<div class="lg-card" style="margin-bottom:16px">
  <div class="lg-section-title">
    <div style="display:flex;align-items:flex-start;gap:10px">
      <span class="lg-section-icon">{{}}</span>
      <div>
        <h2 style="font-size:18px;font-weight:800;color:#0f2a4a;margin:0">Thu Tiền & Công Nợ</h2>
        <p style="font-size:13.5px;color:#64748b;margin:2px 0 0">Hiện trạng từng khoản → còn thiếu bao nhiêu → bấm thu ngay</p>
      </div>
    </div>
    <button class="lg-btn success" onclick="document.querySelector('button[data-action=&quot;open_pay&quot;]')?.click()">{icons.plus(17, "#fff")} GHI NHẬN THANH TOÁN</button>
  </div>
</div>
""".format(icons.wallet(20, "#fff")), unsafe_allow_html=True)

    # Table
    rows = []
    for r in recs:
        rest = r["must"] - r["got"]
        rows.append([
            f'<b>{r["customer"]}</b>',
            f'<a class="lg-link" data-to="/lo-hang-detail?id={r["lot"]}">{r["lot"]}</a><br><span style="font-size:12.5px;color:#64748b">{r["contract"]}</span>',
            f'<span style="white-space:nowrap">{design.fmt_vnd(r["must"])}</span>',
            f'<span style="white-space:nowrap;color:#047857;font-weight:600">{design.fmt_vnd(r["got"])}</span>',
            f'<span style="white-space:nowrap;font-weight:800;color:#b91c1c">{design.fmt_vnd(rest)}</span>',
            f'<span style="font-weight:600;white-space:nowrap">{r["due"]}</span>',
            f'<span class="lg-badge {r["tone"]} sm">{r["status"]}</span>',
            f'<button class="lg-btn success sm" onclick="window.parent.postMessage({{&quot;type&quot;:&quot;donor&quot;,&quot;action&quot;:&quot;pay_dialog&quot;,&quot;sid&quot;:&quot;{r["lot"]}&quot;}},\'*\')">THU NGAY</button>',
        ])

    from .pages_core import _render_table
    _render_table(["Khách hàng", "Lô · Hợp đồng", "Phải thu", "Đã thu", "Còn lại", "Hạn", "Trạng thái", ""], rows, min_width="940px")

    # Hidden button to open the pay dialog
    if st.button("OPEN_PAY_HIDDEN", key="open_pay", type="secondary"):
        st.session_state["pay_dialog_open"] = True

    ui._install_goto_bridge()

    # Payment dialog rendered in a modal via component
    if st.session_state.get("pay_dialog_open"):
        _render_pay_dialog()


def _render_pay_dialog():
    recs = store.get_receivables()
    lots = [r["lot"] for r in recs]
    if "pay_lot" not in st.session_state:
        st.session_state["pay_lot"] = lots[0] if lots else "LO-0306"
    if "pay_amt" not in st.session_state:
        st.session_state["pay_amt"] = ""
    if "pay_kind" not in st.session_state:
        st.session_state["pay_kind"] = "Thu tiền khách"

    from streamlit.components.v1 import html as components_html
    components_html("""
<style>
  .pay-mask { position:fixed; inset:0; background:rgba(15,23,42,.55); z-index:60; }
  .pay-sheet { position:fixed; left:50%; top:50%; transform:translate(-50%,-50%); background:#fff; width:480px; max-width:92vw; border-radius:24px; padding:20px; z-index:61; box-shadow:0 10px 30px rgba(0,0,0,.18); font-family:'Be Vietnam Pro', system-ui, sans-serif; }
  .pay-sheet h3 { font-size:18px; font-weight:800; color:#0f2a4a; margin:0 0 12px; }
  .pay-close { position:absolute; top:12px; right:12px; width:44px; height:44px; border:none; background:transparent; border-radius:12px; cursor:pointer; color:#0f2a4a; }
  .pay-close:hover { background:#f1f5f9; }
  .pay-amount { background:#ecfdf5; border:1px solid #bbf7d0; padding:10px 12px; border-radius:12px; font-size:13.5px; margin-bottom:12px; }
  .pay-amount b { color:#b91c1c; }
  .pay-btns { display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-top:12px; }
</style>
<div class="pay-mask" id="pay-mask"></div>
<div class="pay-sheet">
  <button class="pay-close" id="pay-close" aria-label="Đóng">✕</button>
  <h3>Ghi nhận thanh toán</h3>
  <p style="font-size:13.5px;color:#64748b;margin:0 0 8px">Còn phải thu: <b style="color:#b91c1c">336.500.000 ₫</b></p>
  <div style="display:flex;flex-direction:column;gap:12px">
    <div class="lg-field">
      <label class="lg-field-label">Lô hàng</label>
      <select class="lg-input" id="pay-lot">
        <option>LO-0306</option>
        <option>LO-0299</option>
        <option>LO-0295</option>
        <option>LO-0307</option>
        <option>LO-0308</option>
      </select>
    </div>
    <div class="lg-field">
      <label class="lg-field-label">Số tiền (VND) <span style="color:#dc2626">*</span></label>
      <input class="lg-input missing" id="pay-amt" placeholder="VD: 150000000" inputmode="numeric" />
      <p class="lg-field-error" id="pay-err" style="display:none">⚠ Nhập số tiền — VD: 150000000</p>
    </div>
    <div class="lg-field">
      <label class="lg-field-label">Hình thức</label>
      <select class="lg-input" id="pay-kind">
        <option>Chuyển khoản Vietcombank</option>
        <option>Chuyển khoản Techcombank</option>
        <option>Tiền mặt</option>
      </select>
    </div>
  </div>
  <div class="pay-btns">
    <button class="lg-btn ghost full" id="pay-cancel">Hủy</button>
    <button class="lg-btn success full" id="pay-save">💾 LƯU KHOẢN THU</button>
  </div>
</div>
<script>
  const send = (kind, payload) => {
    const url = new URL(window.parent.location);
    url.searchParams.set('_a', kind + ':' + (payload||'') + ':' + Date.now());
    window.parent.history.pushState({}, '', url.toString());
    window.parent.dispatchEvent(new PopStateEvent('popstate'));
  };
  document.getElementById('pay-mask').addEventListener('click', () => send('close_pay'));
  document.getElementById('pay-close').addEventListener('click', () => send('close_pay'));
  document.getElementById('pay-cancel').addEventListener('click', () => send('close_pay'));
  document.getElementById('pay-save').addEventListener('click', () => {
    const amt = (document.getElementById('pay-amt').value || '').replace(/\\D/g, '');
    const lot = document.getElementById('pay-lot').value;
    const kind = document.getElementById('pay-kind').value;
    if (!amt) {
      document.getElementById('pay-err').style.display = 'block';
      return;
    }
    send('record_payment', lot + '|' + amt + '|' + kind);
  });
</script>
""", height=560)
    st.session_state["pay_dialog_open"] = False


# ===========================================================================
# RECONCILE (Đối Soát Tài Chính)
# ===========================================================================

def render_reconcile():
    rec = store.get_reconcile()

    st.markdown("""
<div class="lg-card" style="margin-bottom:16px">
  <div class="lg-section-title">
    <div style="display:flex;align-items:flex-start;gap:10px">
      <span class="lg-section-icon">{{}}</span>
      <div>
        <h2 style="font-size:18px;font-weight:800;color:#0f2a4a;margin:0">Đối Soát Tài Chính</h2>
        <p style="font-size:13.5px;color:#64748b;margin:2px 0 0">Chốt số với đại lý Bằng Tường — tiền Việt và tiền Trung tách riêng, không gộp</p>
      </div>
    </div>
  </div>
</div>
""".format(icons.scale(20, "#fff")), unsafe_allow_html=True)

    vnd = rec["VND"]
    cny = rec["CNY"]
    st.markdown(f"""
<div class="lg-2col">
  <div class="lg-card" style="border:2px solid #fde68a">
    <p style="font-size:13px;font-weight:800;color:#b45309;margin:0">SỔ VND — ĐẠI LÝ BẰNG TƯỜNG</p>
    <div style="margin-top:10px">
      <div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #f1f5f9"><span style="font-size:13.5px;color:#64748b">Số dư đầu kỳ</span><span style="font-weight:600">{design.fmt_vnd(vnd['open'])}</span></div>
      <div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #f1f5f9"><span style="font-size:13.5px;color:#64748b">Phát sinh tăng (cước 9 lô)</span><span style="font-weight:600">+ {design.fmt_vnd(vnd['incurred'])}</span></div>
      <div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #f1f5f9"><span style="font-size:13.5px;color:#64748b">Phát sinh giảm (đã thanh toán)</span><span style="font-weight:600">− {design.fmt_vnd(vnd['paid'])}</span></div>
      <div style="display:flex;justify-content:space-between;padding:8px 0"><span style="font-size:13.5px;color:#64748b">Số dư còn lại phải trả</span><span style="font-weight:800;font-size:19px;color:#b45309">{design.fmt_vnd(vnd['remain'])}</span></div>
    </div>
  </div>
  <div class="lg-card" style="border:2px solid #bfdbfe">
    <p style="font-size:13px;font-weight:800;color:#1e40af;margin:0">SỔ CNY — ĐẠI LÝ BẰNG TƯỜNG (¥)</p>
    <div style="margin-top:10px">
      <div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #f1f5f9"><span style="font-size:13.5px;color:#64748b">Số dư đầu kỳ</span><span style="font-weight:600">¥{cny['open']:,}</span></div>
      <div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #f1f5f9"><span style="font-size:13.5px;color:#64748b">Phát sinh tăng (xe TQ T9)</span><span style="font-weight:600">+ ¥{cny['incurred']:,}</span></div>
      <div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #f1f5f9"><span style="font-size:13.5px;color:#64748b">Đã thanh toán</span><span style="font-weight:600">− ¥{cny['paid']:,}</span></div>
      <div style="display:flex;justify-content:space-between;padding:8px 0"><span style="font-size:13.5px;color:#64748b">Số dư còn lại phải trả</span><span style="font-weight:800;font-size:19px;color:#1e40af">¥{cny['remain']:,}</span></div>
    </div>
    <p style="font-size:12.5px;color:#94a3b8;margin:8px 0 0">Tuyệt đối không quy đổi gộp 2 sổ — mỗi đồng tiền đối soát riêng.</p>
  </div>
</div>
""", unsafe_allow_html=True)

    st.markdown("""
<div class="lg-card" style="margin-top:16px">
  <h3 style="font-size:15.5px;font-weight:800;color:#0f2a4a;margin:0 0 12px">Checklist trước khi chốt</h3>
  <div style="display:flex;align-items:center;gap:10px;padding:8px 0;border-bottom:1px solid #f1f5f9;font-size:14.5px">
    <span style="width:24px;height:24px;border-radius:999px;background:#10b981;color:#fff;display:grid;place-items-center;font-size:13px;font-weight:700">✓</span>
    <span>Đủ biên lai 9 lô tháng 9</span>
  </div>
  <div style="display:flex;align-items:center;gap:10px;padding:8px 0;border-bottom:1px solid #f1f5f9;font-size:14.5px">
    <span style="width:24px;height:24px;border-radius:999px;background:#e2e8f0;color:#64748b;display:grid;place-items:center;font-size:13px;font-weight:700">·</span>
    <span style="font-weight:600">Cước xe TQ LO-0307 (9.200 CNY) đã khớp</span>
    <button class="lg-btn ghost sm" style="margin-left:auto">Bổ sung →</button>
  </div>
  <div style="display:flex;align-items:center;gap:10px;padding:8px 0;font-size:14.5px">
    <span style="width:24px;height:24px;border-radius:999px;background:#e2e8f0;color:#64748b;display:grid;place-items:center;font-size:13px;font-weight:700">·</span>
    <span style="font-weight:600">Thuế + VAT LO-0306 đã có biên lai</span>
    <button class="lg-btn ghost sm" style="margin-left:auto">Bổ sung →</button>
  </div>
  <button class="lg-btn primary" style="margin-top:12px">{icons.scale(18, "#fff")} CHỐT ĐỐI SOÁT THÁNG 9</button>
</div>
""", unsafe_allow_html=True)


# ===========================================================================
# PARTNER DEBT
# ===========================================================================

def render_partner_debt():
    p_vnd = store.get_partner_vnd()
    p_cny = store.get_partner_cny()
    st.markdown("""
<div class="lg-card" style="margin-bottom:16px">
  <div class="lg-section-title">
    <div style="display:flex;align-items:flex-start;gap:10px">
      <span class="lg-section-icon">{{}}</span>
      <div>
        <h2 style="font-size:18px;font-weight:800;color:#0f2a4a;margin:0">Công Nợ Đối Tác</h2>
        <p style="font-size:13.5px;color:#64748b;margin:2px 0 0">Mỗi đối tác 1 sổ riêng — dư đầu, tăng, giảm, đã trả, còn lại</p>
      </div>
    </div>
  </div>
</div>
""".format(icons.building(20, "#fff")), unsafe_allow_html=True)

    st.markdown(f"""
<div class="lg-tbl-wrap">
  <div style="overflow-x:auto">
    <table class="lg-tbl" style="min-width:860px">
      <thead><tr><th>Đối tác</th><th>Số dư đầu</th><th>Phát sinh tăng</th><th>Phát sinh giảm</th><th>Đã thanh toán</th><th>Còn lại</th><th></th></tr></thead>
      <tbody>
        <tr>
          <td style="font-weight:700">Bằng Tường (VND)</td>
          <td>{p_vnd['Đầu kỳ']/1e6:.1f} tr</td>
          <td style="color:#b91c1c;font-weight:600">+{p_vnd['Tăng trong kỳ']/1e6:.1f} tr</td>
          <td>−{p_vnd['Đã thanh toán']/1e6:.1f} tr</td>
          <td>{p_vnd['Đã thanh toán']/1e6:.1f} tr</td>
          <td style="font-weight:800;color:#b45309">{p_vnd['Còn phải trả']/1e6:.1f} tr</td>
          <td><a class="lg-link" data-to="/tai-chinh/doi-soat">Đối soát →</a></td>
        </tr>
        <tr>
          <td style="font-weight:700">Bằng Tường (CNY)</td>
          <td>¥{p_cny['Đầu kỳ']:,}</td>
          <td style="font-weight:600">+¥{p_cny['Tăng trong kỳ']:,}</td>
          <td>−¥{p_cny['Đã thanh toán']:,}</td>
          <td>¥{p_cny['Đã thanh toán']:,}</td>
          <td style="font-weight:800">¥{p_cny['Còn phải trả']:,}</td>
          <td><a class="lg-link" data-to="/tai-chinh/doi-soat">Đối soát →</a></td>
        </tr>
        <tr>
          <td style="font-weight:700">Nhà xe Hải Phòng (VND)</td>
          <td>0</td>
          <td>+22,0 tr</td>
          <td>−22,0 tr</td>
          <td>22,0 tr</td>
          <td style="font-weight:700;color:#047857">0 ✓</td>
          <td><span style="color:#94a3b8;font-size:13px">Đã xong</span></td>
        </tr>
      </tbody>
    </table>
  </div>
</div>
""", unsafe_allow_html=True)
    ui._install_goto_bridge()


# ===========================================================================
# CEO REPORT
# ===========================================================================

def render_ceo():
    kpi = store.get_kpi()
    st.markdown("""
<div class="lg-card" style="margin-bottom:16px">
  <div class="lg-section-title">
    <div style="display:flex;align-items:flex-start;gap:10px">
      <span class="lg-section-icon">{{}}</span>
      <div>
        <h2 style="font-size:18px;font-weight:800;color:#0f2a4a;margin:0">Báo Cáo CEO</h2>
        <p style="font-size:13.5px;color:#64748b;margin:2px 0 0">Doanh thu · lợi nhuận · công nợ · điểm nghẽn — chỉ hiện số giúp quyết định</p>
      </div>
    </div>
    <div style="display:flex;gap:6px">
      {''.join(f'<button class="lg-btn {("primary" if p=="Tháng" else "ghost")} sm" style="min-height:44px">{p}</button>' for p in ["Tuần","Tháng","Quý","Năm"])}
    </div>
  </div>
</div>
""".format(icons.bar_chart(20, "#fff")), unsafe_allow_html=True)

    # KPI cards
    kpis = [
        {"label": "Doanh thu tháng", "value": "1.510 tr ₫", "sub": "+22% vs kỳ trước", "tone": "text-emerald-700"},
        {"label": "Lợi nhuận gộp", "value": "262 tr ₫", "sub": "Margin 17,4%", "tone": "text-[#0f2a4a]"},
        {"label": "Phải thu còn lại", "value": "537,6 tr ₫", "sub": "1 khoản hạn hôm nay", "tone": "text-red-700"},
        {"label": "Phải trả còn lại", "value": "73,8 tr ₫", "sub": "Chờ đối soát", "tone": "text-amber-700"},
    ]
    cards_html = "".join(
        f'<div class="lg-kpi"><p class="label">{k["label"]}</p><p class="value {k["tone"]}" style="font-size:24px">{k["value"]}</p><p class="sub">{k["sub"]}</p></div>' for k in kpis
    )
    st.markdown(f'<div class="lg-kpi-grid" style="grid-template-columns:repeat(4,1fr);margin-bottom:16px">{cards_html}</div>', unsafe_allow_html=True)

    # Charts: bar + pie as simple HTML/SVG
    bar_chart = """
<div class="lg-card">
  <h3 style="font-size:15.5px;font-weight:800;margin:0 0 8px">Doanh thu & lợi nhuận (tr ₫) — *T9 tính tới 09/09</h3>
  <div style="height:240px;display:flex;align-items:flex-end;gap:24px;padding:0 16px;border-bottom:1px solid #e4e9f1">
    <div style="flex:1;display:flex;flex-direction:column;align-items:center;gap:4px">
      <div style="display:flex;align-items:flex-end;gap:4px;height:200px;width:60%">
        <div style="flex:1;background:#0f2a4a;border-radius:6px 6px 0 0;height:75%"></div>
        <div style="flex:1;background:#10b981;border-radius:6px 6px 0 0;height:15%"></div>
      </div>
      <span style="font-size:13px;font-weight:600">T6</span>
    </div>
    <div style="flex:1;display:flex;flex-direction:column;align-items:center;gap:4px">
      <div style="display:flex;align-items:flex-end;gap:4px;height:200px;width:60%">
        <div style="flex:1;background:#0f2a4a;border-radius:6px 6px 0 0;height:90%"></div>
        <div style="flex:1;background:#10b981;border-radius:6px 6px 0 0;height:18%"></div>
      </div>
      <span style="font-size:13px;font-weight:600">T7</span>
    </div>
    <div style="flex:1;display:flex;flex-direction:column;align-items:center;gap:4px">
      <div style="display:flex;align-items:flex-end;gap:4px;height:200px;width:60%">
        <div style="flex:1;background:#0f2a4a;border-radius:6px 6px 0 0;height:100%"></div>
        <div style="flex:1;background:#10b981;border-radius:6px 6px 0 0;height:22%"></div>
      </div>
      <span style="font-size:13px;font-weight:600">T8</span>
    </div>
    <div style="flex:1;display:flex;flex-direction:column;align-items:center;gap:4px">
      <div style="display:flex;align-items:flex-end;gap:4px;height:200px;width:60%">
        <div style="flex:1;background:#0f2a4a;border-radius:6px 6px 0 0;height:60%"></div>
        <div style="flex:1;background:#10b981;border-radius:6px 6px 0 0;height:12%"></div>
      </div>
      <span style="font-size:13px;font-weight:600">T9*</span>
    </div>
  </div>
</div>
"""
    pie = """
<div class="lg-card">
  <h3 style="font-size:15.5px;font-weight:800;margin:0 0 8px">Trạng thái lô hàng (7 lô gần nhất)</h3>
  <div style="display:flex;align-items:center;gap:16px">
    <div style="width:180px;height:180px;border-radius:50%;background:conic-gradient(#94a3b8 0% 14%, #3b82f6 14% 28%, #f59e0b 28% 42%, #8b5cf6 42% 56%, #10b981 56% 100%);position:relative">
      <div style="position:absolute;inset:24px;background:#fff;border-radius:50%;display:grid;place-items:center">
        <div style="text-align:center"><p style="font-size:13px;color:#64748b;margin:0">Tổng</p><p style="font-size:24px;font-weight:800;margin:0">7</p></div>
      </div>
    </div>
    <div style="flex:1;display:flex;flex-direction:column;gap:4px">
      <div style="display:flex;align-items:center;gap:6px;font-size:13px"><span style="width:10px;height:10px;border-radius:50%;background:#94a3b8"></span>Chờ lấy hàng: 1</div>
      <div style="display:flex;align-items:center;gap:6px;font-size:13px"><span style="width:10px;height:10px;border-radius:50%;background:#3b82f6"></span>Đang vận chuyển: 1</div>
      <div style="display:flex;align-items:center;gap:6px;font-size:13px"><span style="width:10px;height:10px;border-radius:50%;background:#f59e0b"></span>Chờ thông quan: 1</div>
      <div style="display:flex;align-items:center;gap:6px;font-size:13px"><span style="width:10px;height:10px;border-radius:50%;background:#8b5cf6"></span>Chờ giao: 1</div>
      <div style="display:flex;align-items:center;gap:6px;font-size:13px"><span style="width:10px;height:10px;border-radius:50%;background:#10b981"></span>Đã giao: 3</div>
    </div>
  </div>
</div>
"""
    st.markdown(f'<div class="lg-2col">{bar_chart}{pie}</div>', unsafe_allow_html=True)

    # Top customers + bottlenecks
    cust_rows = "".join(
        f'<div style="padding:8px 0;border-bottom:1px solid #f1f5f9"><div style="display:flex;justify-content:space-between;font-size:14px"><b>{c["name"]}</b><b>{c["value"]/1e6:.0f} tr ₫</b></div><div style="height:10px;background:#f1f5f9;border-radius:999px;margin-top:6px"><div style="height:10px;border-radius:999px;background:linear-gradient(90deg,#0f2a4a,#1e5aa8);width:{c["share"]}%"></div></div></div>' for c in kpi["top_customers"]
    )
    bottlenecks = "".join(
        f'<a class="lg-next-card" data-to="{b["to"]}" style="margin-bottom:8px;min-height:0;padding:12px;align-items:center;gap:12px"><span style="width:8px;height:40px;border-radius:6px;background:#dc2626"></span><div style="flex:1"><p style="font-size:14.5px;font-weight:700;color:#0f2a4a;margin:0">{b["title"]}</p><p style="font-size:13px;color:#64748b;margin:2px 0 0">{b["desc"]}</p></div><span style="color:#cbd5e1">→</span></a>' for b in kpi["bottlenecks"]
    )
    st.markdown(f"""
<div class="lg-2col" style="margin-top:16px">
  <div class="lg-card">
    <h3 style="font-size:15.5px;font-weight:800;margin:0 0 8px">Top khách hàng (doanh thu T8–T9)</h3>
    {cust_rows}
  </div>
  <div class="lg-card" style="border:2px solid #fecaca">
    <h3 style="font-size:15.5px;font-weight:800;color:#991b1b;margin:0 0 8px">⚠ Điểm nghẽn cần xử lý</h3>
    {bottlenecks}
  </div>
</div>
""", unsafe_allow_html=True)
    ui._install_goto_bridge()


# ===========================================================================
# TOOLS — HS lookup, Handbook, Translate, Tracking, Users
# ===========================================================================

def render_hs_lookup():
    hs = store.get_hs()
    q = st.text_input("", placeholder="VD: 8457 (máy CNC) hoặc 'board mạch'…", key="hs_q", label_visibility="collapsed")
    filtered = [h for h in hs if not q or q.lower() in (h["hs"] + h["desc"]).lower()]
    st.markdown("""
<div class="lg-card" style="margin-bottom:16px">
  <div class="lg-section-title">
    <div style="display:flex;align-items:flex-start;gap:10px">
      <span class="lg-section-icon">{{}}</span>
      <div>
        <h2 style="font-size:18px;font-weight:800;color:#0f2a4a;margin:0">Tra Cứu Thuế / HS</h2>
        <p style="font-size:13.5px;color:#64748b;margin:2px 0 0">Nhập mã HS hoặc tên hàng — xem thuế NK, VAT, chính sách</p>
      </div>
    </div>
  </div>
</div>
""".format(icons.search(20, "#fff")), unsafe_allow_html=True)

    cards = ""
    for h in filtered:
        cards += f"""
<div class="lg-card" style="margin-bottom:12px">
  <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap">
    <span style="font-size:17px;font-weight:800;color:#0f2a4a">HS {h['hs']}</span>
    <span style="background:#dbeafe;color:#1e40af;font-size:12.5px;font-weight:700;border-radius:6px;padding:2px 8px">NK {h['nk']}</span>
    <span style="background:#d1fae5;color:#047857;font-size:12.5px;font-weight:700;border-radius:6px;padding:2px 8px">VAT {h['vat']}</span>
  </div>
  <p style="font-weight:600;font-size:14.5px;margin:6px 0 0">{h['desc']}</p>
  <p style="font-size:13.5px;color:#475569;margin:4px 0 0">📌 Chính sách: {h['policy']}</p>
  <p style="font-size:13px;color:#64748b;margin:2px 0 0">📝 {h.get('note','')}</p>
  <button class="lg-btn primary full" style="margin-top:12px">DÙNG CHO LÔ HÀNG</button>
</div>
"""
    if not cards:
        cards = '<div class="lg-card" style="text-align:center;padding:32px;border:2px dashed #cbd5e1;color:#64748b">Không tìm thấy mã HS. Thử "8457", "máy", "mạch" hoặc "phụ kiện".</div>'
    st.markdown(f'<div class="lg-2col">{cards}</div>', unsafe_allow_html=True)


def render_handbook():
    items = store.get_handbook()
    st.markdown("""
<div class="lg-card" style="margin-bottom:16px">
  <div class="lg-section-title">
    <div style="display:flex;align-items:flex-start;gap:10px">
      <span class="lg-section-icon">{{}}</span>
      <div>
        <h2 style="font-size:18px;font-weight:800;color:#0f2a4a;margin:0">Sổ Tay Kinh Nghiệm</h2>
        <p style="font-size:13.5px;color:#64748b;margin:2px 0 0">Hướng dẫn từng bước bằng tiếng Việt đơn giản — cho người mới & cô chú lớn tuổi</p>
      </div>
    </div>
  </div>
</div>
""".format(icons.book(20, "#fff")), unsafe_allow_html=True)
    cards = ""
    for it in items:
        cards += f"""
<div class="lg-card" style="display:flex;gap:14px;align-items:flex-start;margin-bottom:12px">
  <span class="lg-section-icon" style="width:44px;height:44px;flex-shrink:0">{icons.book(20, "#fff")}</span>
  <div>
    <p style="font-weight:800;font-size:15.5px;color:#0f2a4a;margin:0">{it['title']} <span style="font-size:12px;font-weight:600;color:#94a3b8">· {it['read_time']} đọc</span></p>
    <p style="font-size:14px;color:#475569;margin:4px 0 0">{it['body']}</p>
  </div>
</div>
"""
    st.markdown(cards, unsafe_allow_html=True)


def render_translate():
    if "tr_src" not in st.session_state:
        st.session_state["tr_src"] = "装箱单 — 42件, 毛重12800KG"
    src = st.text_area("Tiếng Trung (dán nội dung chứng từ)", value=st.session_state["tr_src"], key="tr_input", height=100)
    if "装箱" in src:
        out = "Phiếu đóng gói — 42 kiện, trọng lượng cả bì 12.800 KG"
    elif "发票" in src:
        out = "Hóa đơn thương mại"
    elif "提单" in src:
        out = "Vận đơn đường biển"
    elif "原产地证" in src:
        out = "Giấy chứng nhận xuất xứ"
    else:
        out = "Nhập câu tiếng Trung để xem bản dịch Việt (bản mẫu: 装箱单 / 发票 / 提单 / 原产地证)."
    st.markdown("""
<div class="lg-card" style="max-width:900px">
  <div class="lg-section-title">
    <div style="display:flex;align-items:flex-start;gap:10px">
      <span class="lg-section-icon">{{}}</span>
      <div>
        <h2 style="font-size:18px;font-weight:800;color:#0f2a4a;margin:0">Dịch Thuật</h2>
        <p style="font-size:13.5px;color:#64748b;margin:2px 0 0">Dịch nhanh chứng từ Trung ↔ Việt cho Support</p>
      </div>
    </div>
  </div>
  <div class="lg-field"><label class="lg-field-label">Tiếng Trung (dán nội dung chứng từ)</label><textarea class="lg-textarea" rows="3">{src}</textarea></div>
  <div style="display:flex;gap:8px;flex-wrap:wrap">
    {''.join(f'<button class="lg-btn ghost sm" style="min-height:44px">{w}</button>' for w in ["装箱单","商业发票","提单","原产地证"])}
  </div>
  <div style="background:#ecfdf5;border:1px solid #bbf7d0;border-radius:12px;padding:16px;margin-top:12px">
    <p style="font-size:12.5px;font-weight:700;text-transform:uppercase;letter-spacing:.04em;color:#047857;margin:0">Tiếng Việt</p>
    <p style="font-weight:700;font-size:16px;margin:4px 0 0">{out}</p>
  </div>
  <button class="lg-btn primary" style="margin-top:12px">{icons.lang(17, "#fff")} CHÉP BẢN DỊCH</button>
</div>
""".format(icons.lang(20, "#fff")), unsafe_allow_html=True)


def render_tracking():
    ships = store.get_shipments()
    st.markdown("""
<div class="lg-card" style="margin-bottom:16px">
  <div class="lg-section-title">
    <div style="display:flex;align-items:flex-start;gap:10px">
      <span class="lg-section-icon">{{}}</span>
      <div>
        <h2 style="font-size:18px;font-weight:800;color:#0f2a4a;margin:0">Theo Dõi Vận Chuyển</h2>
        <p style="font-size:13.5px;color:#64748b;margin:2px 0 0">Vị trí & mốc thời gian từng lô — xe TQ tới đâu, hàng đang ở đâu</p>
      </div>
    </div>
  </div>
</div>
""".format(icons.truck(20, "#fff")), unsafe_allow_html=True)
    for s in ships:
        done_idx = {"LO-0295": 5, "LO-0299": 4, "LO-0306": 3, "LO-0307": 2}.get(s["id"], 1)
        steps_html = ""
        for i, st_name in enumerate(["Lấy hàng", "Xuất khẩu", "Cửa khẩu", "Thông quan", "Giao hàng"]):
            done = i < done_idx
            current = i == done_idx
            bg = "#10b981" if done else ("#f59e0b" if current else "#f1f5f9")
            color = "#fff" if (done or current) else "#94a3b8"
            mark = "✓" if done else str(i + 1)
            if current:
                mark_html = f'<span class="lg-pulse">{mark}</span>'
            else:
                mark_html = mark
            steps_html += f"""
<div style="display:flex;align-items:center;gap:4px;flex-shrink:0">
  <div style="display:flex;flex-direction:column;align-items:center">
    <span style="width:36px;height:36px;border-radius:999px;background:{bg};color:{color};display:grid;place-items:center;font-size:13px;font-weight:800">{mark_html}</span>
    <span style="font-size:11.5px;font-weight:700;margin-top:4px;white-space:nowrap;color:{'#0f2a4a' if (done or current) else '#94a3b8'}">{st_name}</span>
  </div>
  {f'<span style="width:32px;height:4px;border-radius:999px;background:{"#10b981" if i < done_idx - 1 else "#e2e8f0"};margin-bottom:18px"></span>' if i < 4 else ''}
</div>
"""
        last = s.get("timeline", [])[-1] if s.get("timeline") else {"title":"—","time":""}
        st.markdown(f"""
<div class="lg-card" style="margin-bottom:12px">
  <div style="display:flex;flex-wrap:wrap;align-items:center;gap:8px">
    <span style="font-size:16.5px;font-weight:800;color:#0f2a4a">{s['id']}</span>
    <span class="lg-badge {s.get('statusTone','gray')} sm">{s.get('status','')}</span>
    <a class="lg-link" style="margin-left:auto" data-to="/lo-hang-detail?id={s['id']}">Mở workspace →</a>
  </div>
  <div style="display:flex;align-items:center;gap:4px;overflow-x:auto;margin-top:12px">{steps_html}</div>
  <p style="font-size:13.5px;color:#475569;margin:12px 0 0">📍 {last.get('title','')} — {last.get('time','')}</p>
</div>
""", unsafe_allow_html=True)
    ui._install_goto_bridge()


def render_users():
    role = store.get_role()
    if role != "ADMIN":
        st.markdown("""
<div class="lg-card" style="border:2px solid #fecaca;text-align:center;padding:32px;max-width:560px;margin:0 auto">
  <p style="font-weight:800;font-size:19px;color:#991b1b;margin:0">⛔ Khu vực Admin</p>
  <p style="font-size:14.5px;color:#475569;margin:8px 0 0">Vì sao bị chặn: vai trò hiện tại là <b>SUPPORT</b> — chỉ ADMIN được xem & đổi quyền người dùng.</p>
  <p style="font-size:14px;color:#64748b;margin:4px 0 0">Tiếp theo: chuyển vai trò sang ADMIN ở góc phải header để xem mẫu.</p>
</div>
""", unsafe_allow_html=True)
        return
    users = store.get_users()
    st.markdown("""
<div class="lg-card" style="margin-bottom:16px">
  <div class="lg-section-title">
    <div style="display:flex;align-items:flex-start;gap:10px">
      <span class="lg-section-icon">{{}}</span>
      <div>
        <h2 style="font-size:18px;font-weight:800;color:#0f2a4a;margin:0">Người Dùng (Admin)</h2>
        <p style="font-size:13.5px;color:#64748b;margin:2px 0 0">Tên · tài khoản · vai trò · trạng thái · đăng nhập cuối</p>
      </div>
    </div>
    <button class="lg-btn primary">{icons.plus(17, "#fff")} Tạo người dùng</button>
  </div>
</div>
""".format(icons.shield(20, "#fff")), unsafe_allow_html=True)

    rows = []
    for u in users:
        role_bg = {"ADMIN": "#ede9fe;color:#5b21b6", "SUPPORT": "#dbeafe;color:#1e40af", "SALE": "#d1fae5;color:#047857"}.get(u["role"], "")
        status = f'<span style="color:#b91c1c;font-weight:700">🔒 Tạm khóa</span>' if u["status"] == "Tạm khóa" else f'<span style="color:#047857;font-weight:700">● Đang hoạt động</span>'
        rows.append([
            f'<b>{u["name"]}</b>',
            f'<span style="color:#64748b">{u["username"]}</span>',
            f'<span style="background:{role_bg.split(";")[0]};color:{role_bg.split(";")[1] if ";" in role_bg else "#0f2a4a"};font-size:12.5px;font-weight:800;border-radius:999px;padding:4px 10px">{u["role"]} ⇄</span>',
            status,
            f'<span style="font-size:13px;color:#64748b">{u.get("last","")}</span>',
            f'<button class="lg-btn ghost sm">{"Mở khóa" if u["status"] == "Tạm khóa" else "Khóa TK"}</button>',
        ])

    from .pages_core import _render_table
    _render_table(["Tên", "Tài khoản", "Vai trò", "Trạng thái", "Đăng nhập cuối", "Hành động"], rows, min_width="820px")
