"""Home page — exact donor structure with real Logistics data."""
from __future__ import annotations

import streamlit as st

from . import design, icons, store, ui


def render():
    kpi = store.get_kpi()
    ships = store.get_shipments()
    overdue = [t for t in store.get_tasks() if t.get("tone") == "red" or "hôm nay" in t.get("dueNote", "").lower() or t.get("level") == "Khan"][:3]

    # HERO BANNER
    ui.hero(
        kicker="Thứ Tư · 09/09/2026 · Ca sáng",
        title="Hôm nay tôi cần làm gì?",
        sub="3 việc khẩn trước 17:00 — bắt đầu từ <b style='color:#fff'>LO-0306 thiếu tờ khai</b>, sau đó <b style='color:#fff'>giao LO-0299 lúc 14:00</b>.",
        primary_label="XỬ LÝ NGAY",
        primary_to="/viec-can-xu-ly",
        secondary_label="Mở LO-0306",
        secondary_to="/lo-hang-detail?id=LO-0306&tab=nhap",
    )

    st.write("")

    # PRIMARY NEXT-ACTION BANNER (LO-0306)
    ui.next_action_banner(
        tone="red",
        kicker="Việc tiếp theo",
        title="LO-0306: bổ sung số tờ khai nhập khẩu trước 17:00 hôm nay",
        desc="Hiện trạng: hàng đã về bãi Hữu Nghị VN · Còn thiếu: số tờ khai + biên lai thuế · Phụ trách: Thu Hằng",
        action="XỬ LÝ NGAY",
        to="/lo-hang-detail?id=LO-0306&tab=nhap",
    )

    st.write("")

    # VIỆC TIẾP THEO — 5 cards
    ui.page_title("VIỆC TIẾP THEO", "Bấm vào từng thẻ để đi thẳng tới màn hình xử lý")
    next_cards = [
        {"icon": "truck", "bg": "#475569", "bar": "#475569", "title": "Lô cần lấy hàng", "count": 1, "desc": "LO-0308 · Minh Đức — thiếu xe TQ", "to": "/lo-hang-detail?id=LO-0308&tab=lay-hang", "cta": "Chốt xe ngay"},
        {"icon": "filecheck", "bg": "#f59e0b", "bar": "#f59e0b", "title": "Lô cần thông quan", "count": 1, "desc": "LO-0306 · An Phát — thiếu số tờ khai", "to": "/lo-hang-detail?id=LO-0306&tab=nhap", "cta": "Khai báo ngay"},
        {"icon": "package_check", "bg": "#2563eb", "bar": "#2563eb", "title": "Lô cần giao", "count": 1, "desc": "LO-0299 · Hồng Hà — giao 14:00 hôm nay", "to": "/lo-hang-detail?id=LO-0299&tab=nhap", "cta": "Xem lịch giao"},
        {"icon": "wallet", "bg": "#059669", "bar": "#059669", "title": "Khoản cần thu", "count": 3, "desc": "Còn phải thu 537,6 tr — 1 khoản hạn hôm nay", "to": "/tai-chinh/thu-tien", "cta": "Thu tiền"},
        {"icon": "file_warning", "bg": "#dc2626", "bar": "#dc2626", "title": "Hồ sơ thiếu chứng từ", "count": 4, "desc": "CO form E, Packing List, Ngày HDMB…", "to": "/viec-can-xu-ly", "cta": "Bổ sung"},
    ]
    ui.next_action_cards(next_cards)

    st.write("")

    # CHỈ SỐ VẬN HÀNH HÔM NAY
    ui.page_title("Chỉ số vận hành hôm nay", "Chỉ hiện số liệu giúp ra quyết định — bấm để lọc danh sách")
    kpi_items = [
        {"label": "Lô đang chạy", "value": str(kpi["shipments_running"]), "sub": "0306 · 0307 · 0308 · 0299", "to": "/lo-hang"},
        {"label": "Chờ lấy hàng", "value": "1", "sub": "LO-0308", "to": "/lo-hang-detail?id=LO-0308"},
        {"label": "Đang vận chuyển", "value": "1", "sub": "LO-0307", "to": "/lo-hang-detail?id=LO-0307"},
        {"label": "Chờ thông quan", "value": "1", "sub": "LO-0306", "to": "/lo-hang-detail?id=LO-0306&tab=nhap"},
        {"label": "Chờ giao", "value": "1", "sub": "LO-0299", "to": "/lo-hang-detail?id=LO-0299&tab=nhap"},
        {"label": "Đã giao hôm nay", "value": "1", "sub": "LO-0295 · 07:30", "to": "/lo-hang"},
        {"label": "Phải thu còn lại", "value": "537,6 tr ₫", "sub": "1 khoản hạn HÔM NAY → thu ngay", "to": "/tai-chinh/thu-tien", "tone": "green"},
        {"label": "Phải trả còn lại", "value": "73,8 tr ₫", "sub": "Chờ đối soát Bằng Tường", "to": "/tai-chinh/doi-soat", "tone": "amber"},
        {"label": "Việc quá hạn / khẩn", "value": "3 việc", "sub": "Xử lý trước 17:00 hôm nay", "to": "/viec-can-xu-ly", "tone": "red"},
    ]
    ui.kpi_grid(kpi_items, columns=5)

    st.write("")

    # QUÁ HẠN & SẮP TỚI HẠN + TRẠNG THÁI CÁC LÔ ĐANG CHẠY
    left_html = _render_overdue(overdue)
    right_html = _render_running(ships)
    ui.two_col(left_html, right_html)

    st.write("")

    # TIỀN HÔM NAY
    st.markdown(f"""
<div class="lg-card">
  <div class="lg-section-title" style="margin-bottom:12px">
    <h2 style="font-size:16.5px">Tiền hôm nay — hiện trạng → việc thiếu → hành động</h2>
    <a class="lg-link" href="?p=/tai-chinh/thu-tien" target="_self">Mở tài chính →</a>
  </div>
  <div class="lg-cols-3">
    <div style="background:#ecfdf5;border:1px solid #bbf7d0;border-radius:12px;padding:16px">
      <p style="font-size:13px;font-weight:600;color:#065f46;margin:0">Còn phải thu · 537.600.000 ₫</p>
      <p style="font-size:13.5px;color:#064e3b;margin:6px 0 0">Thiếu: tạm ứng đợt 2 LO-0306 (150 tr, hạn hôm nay)</p>
      <a class="lg-btn success" style="margin-top:10px" href="?p=/tai-chinh/thu-tien" target="_self">＋ GHI NHẬN THANH TOÁN</a>
    </div>
    <div style="background:#fff7ed;border:1px solid #fed7aa;border-radius:12px;padding:16px">
      <p style="font-size:13px;font-weight:600;color:#9a3412;margin:0">Còn phải trả · 73.800.000 ₫</p>
      <p style="font-size:13.5px;color:#7c2d12;margin:6px 0 0">Thiếu: đối soát cước xe TQ Bằng Tường tháng 9</p>
      <a class="lg-btn" style="background:#f59e0b;color:#fff;margin-top:10px" href="?p=/tai-chinh/doi-soat" target="_self">ĐỐI SOÁT NGAY</a>
    </div>
    <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:12px;padding:16px">
      <p style="font-size:13px;font-weight:600;color:#1e40af;margin:0">Đã thu hôm nay · 0 ₫</p>
      <p style="font-size:13.5px;color:#1e3a8a;margin:6px 0 0">Chưa ghi nhận khoản nào — thu LO-0306 để bắt đầu</p>
      <a class="lg-btn primary" style="margin-top:10px" href="?p=/tai-chinh/thu-tien" target="_self">MỞ SỔ THU TIỀN</a>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

    # Footer
    st.markdown("""
<div class="lg-footer">
  CÔNG TY TNHH GIAO NHẬN QUỐC TẾ TRƯỜNG THÀNH · Đại lý: Phú Anh Logistics Việt Nam · Bản prototype nội bộ — dữ liệu minh họa 09/09/2026
</div>
""", unsafe_allow_html=True)


def _render_overdue(tasks: list) -> str:
    rows = ""
    for t in tasks[:3]:
        tone = "red" if t.get("level") == "Khan" else "amber"
        due = t.get("due", "")
        route = t.get("route", "/viec-can-xu-ly")
        rows += f"""
<a class="lg-next-card" href="?p={route}" target="_self" style="min-height:0;padding:12px;align-items:center;gap:12px">
  <span class="lg-next-bar" style="width:10px;height:40px;background:{'#dc2626' if tone=='red' else '#f59e0b'};border-radius:6px"></span>
  <div style="flex:1;min-width:0">
    <p style="font-size:14.5px;font-weight:700;color:#0f2a4a;margin:0">{t.get('lot','')} · {t.get('job','')}</p>
    <p style="font-size:13px;color:#64748b;margin:2px 0 0">{due}</p>
  </div>
  <span style="font-size:13.5px;font-weight:700;color:#1e5aa8">Xử lý →</span>
</a>
"""
    return f"""
<div class="lg-card">
  <div class="lg-section-title" style="margin-bottom:12px">
    <h2 style="font-size:16.5px;display:flex;align-items:center;gap:8px">⏰ Quá hạn và sắp tới hạn</h2>
    <a class="lg-link" href="?p=/viec-can-xu-ly" target="_self">Tất cả →</a>
  </div>
  <div style="display:flex;flex-direction:column;gap:10px">{rows}</div>
</div>
"""


def _render_running(ships: list) -> str:
    rows = ""
    for s in ships[:5]:
        tone = s.get("statusTone", "gray")
        next_act = s.get("nextAction", "—")
        rows += f"""
<a class="lg-next-card" href="?p=/lo-hang-detail&id={s['id']}" target="_self" style="min-height:0;padding:12px;align-items:center;gap:12px">
  <span class="lg-dot {tone}"></span>
  <div style="flex:1;min-width:0">
    <p style="font-size:14.5px;font-weight:700;color:#0f2a4a;margin:0">{s['id']} · {s.get('customerShort','')}</p>
    <p style="font-size:13px;color:#64748b;margin:2px 0 0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">Tiếp theo: {next_act}</p>
  </div>
  <span class="lg-badge {tone} sm">{s.get('status','')}</span>
</a>
"""
    return f"""
<div class="lg-card">
  <div class="lg-section-title" style="margin-bottom:12px">
    <h2 style="font-size:16.5px">Trạng thái các lô đang chạy</h2>
    <a class="lg-link" href="?p=/lo-hang" target="_self">Tất cả lô →</a>
  </div>
  <div style="display:flex;flex-direction:column;gap:10px">{rows}</div>
  <div style="margin-top:12px;background:#eff6ff;border:1px solid #bfdbfe;border-radius:12px;padding:12px;display:flex;align-items:flex-start;gap:8px">
    <span style="color:#1e40af">{icons.info(17, "#1e5aa8")}</span>
    <p style="font-size:13.5px;color:#1e3a8a;margin:0"><b>Luồng gợi ý:</b> Tổng quan → mở lô → xử lý việc tiếp theo → hợp đồng → xuất chứng từ → thu tiền.</p>
  </div>
</div>
"""
