"""Sandbox data store for the donor-exact UI.

Reuses the existing business readers/writers from the real Logistics app, but
falls back to in-memory mongomock + a curated seed dataset so the
Arena Preview can render every donor state without a production database.
"""
from __future__ import annotations

import json
import os
import uuid
from copy import deepcopy
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import streamlit as st

# Allow opting out of real DB by setting environment variable
USE_REAL_DB = os.environ.get("DONOR_USE_REAL_DB", "0") == "1"

if USE_REAL_DB:
    try:
        from core.database import (
            load_data as _real_load_shipments,
            load_customers as _real_load_customers,
            load_contracts as _real_load_contracts,
            load_agreements as _real_load_agreements,
            load_quotations as _real_load_quotations,
            save_shipment_atomic as _real_save_shipment,
        )
    except Exception:
        USE_REAL_DB = False


# ============================================================================
# SEED DATA — mirrors real Logistics domain but keeps preview isolated
# ============================================================================

SEED_CUSTOMERS = {
    "an_phat": {
        "id": "an_phat",
        "name": "Công ty TNHH Cơ Khí An Phát",
        "short": "An Phát",
        "mst": "0201884452",
        "address": "KCN Yên Phong, Bắc Ninh",
        "contact": "Phạm Minh Đức · 0987 654 321",
        "sale": "Minh Anh",
        "debt": 336_500_000,
        "lots": 3,
        "updated": "09/09/2026",
        "note": "Khách VIP — thanh toán đợt 50/50",
    },
    "minh_duc": {
        "id": "minh_duc",
        "name": "Công ty TNHH Thiết Bị Minh Đức",
        "short": "Minh Đức",
        "mst": "0200667788",
        "address": "KCN Tràng Duệ, Hải Phòng",
        "contact": "Nguyễn Hải Yến · 0912 345 678",
        "sale": "Hồng Nhung",
        "debt": 0,
        "lots": 1,
        "updated": "08/09/2026",
        "note": "",
    },
    "hong_ha": {
        "id": "hong_ha",
        "name": "Công ty TNHH Phụ Kiện Hồng Hà",
        "short": "Hồng Hà",
        "mst": "0102778899",
        "address": "KCN Từ Liêm, Hà Nội",
        "contact": "Trần Hồng Hà · 0935 111 222",
        "sale": "Minh Anh",
        "debt": 114_600_000,
        "lots": 2,
        "updated": "07/09/2026",
        "note": "",
    },
    "sao_viet": {
        "id": "sao_viet",
        "name": "Công ty CP Công Nghệ Sao Việt",
        "short": "Sao Việt",
        "mst": "0105998877",
        "address": "Tòa nhà Sao Việt, Cầu Giấy, Hà Nội",
        "contact": "Lê Quốc Bảo · 0903 222 111",
        "sale": "Hồng Nhung",
        "debt": 0,
        "lots": 1,
        "updated": "05/09/2026",
        "note": "",
    },
}

SEED_CONTRACTS = [
    {
        "id": "HDMB-PA-2026-031",
        "type": "HDMB",
        "company": "Công ty TNHH Cơ Khí An Phát",
        "companyLegal": "CÔNG TY TNHH CƠ KHÍ AN PHÁT",
        "companyAddr": "KCN Yên Phong, Bắc Ninh",
        "companyTax": "0201884452",
        "companyRep": "Phạm Minh Đức",
        "companyRole": "Giám đốc",
        "agent": "Phú Anh Logistics Việt Nam",
        "agentLegal": "CÔNG TY TNHH PHÚ ANH LOGISTICS VIỆT NAM",
        "agentAddr": "Số 88 Trần Thái Tông, Cầu Giấy, Hà Nội",
        "agentTax": "0108123456",
        "agentRep": "Nguyễn Phú Anh",
        "agentRole": "Giám đốc",
        "bankOwner": "CÔNG TY TNHH PHÚ ANH LOGISTICS VIỆT NAM",
        "bankNo": "0451000412345",
        "bankName": "Vietcombank Thanh Xuân",
        "value": 873_200_000,
        "validFrom": "01/06/2026",
        "validTo": "31/12/2026",
        "lots": 3,
        "status": "Còn hiệu lực",
        "statusTone": "green",
        "missingBuyerInfo": [],
        "goods": [
            {"desc": "Máy CNC 5 trục model VMC-850", "unit": "Máy", "qty": 2, "price": 380_000_000},
            {"desc": "Phụ kiện kèm theo", "unit": "Bộ", "qty": 2, "price": 26_000_000},
        ],
        "hdntNo": "",
        "hdntDate": "",
        "hdntFrom": "",
        "hdntTo": "",
        "plNo": "",
        "plDate": "",
        "hdmbNo": "HDMB-PA-2026-031",
        "hdmbDate": "15/06/2026",
        "reusableHdnt": False,
        "history": [
            {"type": "HDMB", "no": "HDMB-PA-2026-031", "date": "15/06/2026", "rev": "V1", "status": "ĐÃ PHÁT HÀNH", "by": "Thu Hằng", "created": "15/06/2026"},
        ],
        "linkedLots": [
            {"id": "LO-0306", "customer": "An Phát", "status": "Chờ thông quan", "delivery": "10/09/2026", "pxk": "—"},
            {"id": "LO-0295", "customer": "An Phát", "status": "Đã giao", "delivery": "07/09/2026", "pxk": "PXK-2026-0295"},
            {"id": "LO-0278", "customer": "An Phát", "status": "Đã giao", "delivery": "20/08/2026", "pxk": "PXK-2026-0278"},
        ],
    },
    {
        "id": "HDNT-PA-2026-118",
        "type": "HDNT",
        "company": "Công ty TNHH Phụ Kiện Hồng Hà",
        "companyLegal": "CÔNG TY TNHH PHỤ KIỆN HỒNG HÀ",
        "companyAddr": "KCN Từ Liêm, Hà Nội",
        "companyTax": "0102778899",
        "companyRep": "Trần Hồng Hà",
        "companyRole": "Tổng giám đốc",
        "agent": "Phú Anh Logistics Việt Nam",
        "agentLegal": "CÔNG TY TNHH PHÚ ANH LOGISTICS VIỆT NAM",
        "agentAddr": "Số 88 Trần Thái Tông, Cầu Giấy, Hà Nội",
        "agentTax": "0108123456",
        "agentRep": "Nguyễn Phú Anh",
        "agentRole": "Giám đốc",
        "bankOwner": "CÔNG TY TNHH PHÚ ANH LOGISTICS VIỆT NAM",
        "bankNo": "0451000412345",
        "bankName": "Vietcombank Thanh Xuân",
        "value": 214_600_000,
        "validFrom": "01/05/2026",
        "validTo": "30/04/2027",
        "lots": 1,
        "status": "Còn hiệu lực",
        "statusTone": "green",
        "missingBuyerInfo": [],
        "goods": [
            {"desc": "Phụ kiện nhựa công nghiệp", "unit": "Kiện", "qty": 1, "price": 198_703_704},
        ],
        "hdntNo": "HDNT-PA-2026-118",
        "hdntDate": "02/05/2026",
        "hdntFrom": "02/05/2026",
        "hdntTo": "30/04/2027",
        "plNo": "PL-118-A",
        "plDate": "05/09/2026",
        "hdmbNo": "",
        "hdmbDate": "",
        "reusableHdnt": True,
        "history": [
            {"type": "HDNT", "no": "HDNT-PA-2026-118", "date": "02/05/2026", "rev": "V1", "status": "ĐÃ PHÁT HÀNH", "by": "Thu Hằng", "created": "02/05/2026"},
            {"type": "PL", "no": "PL-118-A", "date": "05/09/2026", "rev": "V1", "status": "ĐÃ PHÁT HÀNH", "by": "Thu Hằng", "created": "05/09/2026"},
        ],
        "linkedLots": [
            {"id": "LO-0299", "customer": "Hồng Hà", "status": "Chờ giao", "delivery": "09/09/2026", "pxk": "—"},
        ],
    },
    {
        "id": "HDMB-PA-2026-028",
        "type": "HDMB",
        "company": "Công ty TNHH Thiết Bị Minh Đức",
        "companyLegal": "CÔNG TY TNHH THIẾT BỊ MINH ĐỨC",
        "companyAddr": "KCN Tràng Duệ, Hải Phòng",
        "companyTax": "0200667788",
        "companyRep": "",
        "companyRole": "",
        "agent": "Phú Anh Logistics Việt Nam",
        "agentLegal": "CÔNG TY TNHH PHÚ ANH LOGISTICS VIỆT NAM",
        "agentAddr": "Số 88 Trần Thái Tông, Cầu Giấy, Hà Nội",
        "agentTax": "0108123456",
        "agentRep": "Nguyễn Phú Anh",
        "agentRole": "Giám đốc",
        "bankOwner": "CÔNG TY TNHH PHÚ ANH LOGISTICS VIỆT NAM",
        "bankNo": "0451000412345",
        "bankName": "Vietcombank Thanh Xuân",
        "value": 425_000_000,
        "validFrom": "01/08/2026",
        "validTo": "31/12/2026",
        "lots": 1,
        "status": "Thiếu thông tin",
        "statusTone": "amber",
        "missingBuyerInfo": ["Thiếu người đại diện", "Thiếu chức vụ"],
        "goods": [
            {"desc": "Máy dập kim loại 200 tấn", "unit": "Máy", "qty": 1, "price": 393_518_519},
        ],
        "hdntNo": "",
        "hdntDate": "",
        "hdntFrom": "",
        "hdntTo": "",
        "plNo": "",
        "plDate": "",
        "hdmbNo": "HDMB-PA-2026-028",
        "hdmbDate": "12/08/2026",
        "reusableHdnt": False,
        "history": [
            {"type": "HDMB", "no": "HDMB-PA-2026-028", "date": "12/08/2026", "rev": "V1", "status": "ĐÃ PHÁT HÀNH", "by": "Thu Hằng", "created": "12/08/2026"},
        ],
        "linkedLots": [
            {"id": "LO-0308", "customer": "Minh Đức", "status": "Chờ lấy hàng", "delivery": "12/09/2026", "pxk": "—"},
        ],
    },
]


def _mk_pickup(name="Nhà máy Cơ khí Quảng Tây", addr="Khu công nghiệp Bằng Tường, Quảng Tây", contact="Mr. Lưu", phone="+86 139 2611 8899", **over):
    base = {
        "factory": name, "address": addr, "contact": contact, "phone": phone,
        "truckType": "Cont 40HQ", "plate": "", "driver": "", "driverPhone": "",
        "eta": "10/09/2026", "ata": "—", "pickupTime": "",
    }
    base.update(over)
    return base


def _mk_import_info(border="Hữu Nghị (VN)", **over):
    base = {
        "borderVN": border, "declarationNo": "", "regDate": "", "tax": 0, "vat": 0,
        "inspection": "", "license": "", "truckVN": "Cont 40HQ",
        "plateVN": "", "driverVN": "", "schedule": "",
        "deliveryAddr": "", "receiver": "", "receiverPhone": "",
        "delivered": False, "actualDelivery": "", "clearDate": "",
    }
    base.update(over)
    return base


def _mk_cargo(**over):
    base = {
        "type": "Máy CNC 5 trục", "packs": 42, "weight": "12.800 kg", "cbm": 28,
        "dims": "6.0 x 2.4 x 2.6 m", "note": "Hàng dễ vỡ — bố trí khoang dưới cont",
    }
    base.update(over)
    return base


def _mk_export_info(**over):
    base = {
        "border": "Hữu Nghị (TQ)", "declarant": "Phú Anh — chi nhánh Bằng Tường",
        "eta": "10/09/2026", "ata": "—", "state": "Đã khai báo",
    }
    base.update(over)
    return base


def _mk_finance(receivable=486_500_000, received=150_000_000, payable=46_500_000, paid=10_000_000, payments=None, quote=None, actual=None):
    return {
        "receivable": receivable, "received": received,
        "payable": payable, "paid": paid,
        "payments": payments or [
            {"date": "05/09/2026", "kind": "Tạm ứng đợt 1", "amount": 150_000_000, "ccy": "VND", "by": "Thu Hằng", "note": "Theo PL-118-A"},
        ],
        "quote": quote or [
            {"label": "Vận tải TQ", "amount": 32_000_000, "ccy": "VND"},
            {"label": "Khai xuất khẩu", "amount": 3_500_000, "ccy": "VND"},
            {"label": "Cửa khẩu", "amount": 6_800_000, "ccy": "VND"},
            {"label": "Vận tải VN", "amount": 9_800_000, "ccy": "VND"},
            {"label": "Dịch vụ", "amount": 6_200_000, "ccy": "VND"},
            {"label": "Ủy thác", "amount": 4_500_000, "ccy": "VND"},
        ],
        "actual": actual or [
            {"label": "Vận tải TQ", "amount": 32_000_000, "ccy": "VND"},
            {"label": "Khai xuất khẩu", "amount": 3_500_000, "ccy": "VND"},
            {"label": "Cửa khẩu", "amount": 6_800_000, "ccy": "VND"},
            {"label": "Vận tải VN", "amount": 9_800_000, "ccy": "VND"},
            {"label": "Dịch vụ", "amount": 6_200_000, "ccy": "VND"},
            {"label": "Ủy thác", "amount": 4_500_000, "ccy": "VND"},
            {"label": "Thuế NK + VAT", "amount": 64_600_000, "ccy": "VND"},
        ],
    }


def _mk_pxk(**over):
    base = {"number": "", "date": "", "place": "", "receiver": "", "role": "Thủ kho", "source": "", "done": False}
    base.update(over)
    return base


def _mk_docs():
    return [
        {"name": "Hợp đồng mua bán (HDMB)", "ok": True, "note": "HDMB-PA-2026-031"},
        {"name": "Packing List", "ok": True, "note": "42 kiện / 12.800 kg"},
        {"name": "Invoice (Hóa đơn thương mại)", "ok": True, "note": "INV-2026-0612"},
        {"name": "CO Form E", "ok": False, "note": "Đã gửi đề nghị — chờ cấp"},
        {"name": "Tờ khai xuất khẩu", "ok": True, "note": "Số TK XK: 305877112"},
        {"name": "Giấy chứng nhận xuất xứ", "ok": True, "note": "C/O Form E — 09/2026"},
    ]


def _mk_timeline():
    return [
        {"time": "31/08 14:20", "title": "Đã tạo lô LO-0306", "desc": "Từ báo giá BG-2026-210 đã chốt", "tone": "blue"},
        {"time": "01/09 09:05", "title": "Đã chốt xe TQ", "desc": "Xe 粤A·88T36 · Mr. Lưu phụ trách", "tone": "blue"},
        {"time": "02/09 16:40", "title": "Lấy hàng xong tại nhà máy", "desc": "Đủ 42 kiện — đã niêm phong cont", "tone": "green"},
        {"time": "05/09 10:15", "title": "Xuất khẩu thông quan", "desc": "Tờ khai XK 305877112 — luồng xanh", "tone": "green"},
        {"time": "07/09 08:30", "title": "Hàng về bãi Hữu Nghị VN", "desc": "Sẵn sàng làm thủ tục nhập khẩu", "tone": "amber"},
    ]


SEED_SHIPMENTS = [
    {
        "id": "LO-0306",
        "customer": "Công ty TNHH Cơ Khí An Phát",
        "customerShort": "An Phát",
        "customerMST": "0201884452",
        "customer_id": "an_phat",
        "contract": "HDMB-PA-2026-031",
        "route": "Quảng Tây → Tân Thanh → Bắc Ninh",
        "borderVN": "Hữu Nghị",
        "sale": "Minh Anh",
        "support": "Thu Hằng",
        "status": "Chờ thông quan",
        "statusTone": "amber",
        "priority": "Khan",
        "nextAction": "Bổ sung số tờ khai nhập khẩu trước 17:00 hôm nay",
        "nextActionDetail": "Hàng đã về bãi Hữu Nghị VN · Còn thiếu: số tờ khai + biên lai thuế",
        "nextLabel": "XỬ LÝ NGAY",
        "nextRoute": "/lo-hang/LO-0306?tab=nhap",
        "updated": "09/09/2026 09:42",
        "pickup": _mk_pickup(plate="粤A·88T36", driver="Lưu Vĩ An", driverPhone="+86 139 2611 8899", pickupTime="02/09/2026 09:00", ata="02/09/2026 14:40"),
        "importInfo": _mk_import_info(border="Hữu Nghị (VN)", declarationNo="", regDate="", tax=48_200_000, vat=96_400_000, inspection="Luồng xanh", license="—", plateVN="", driverVN="", schedule="10/09/2026 14:00", deliveryAddr="KCN Yên Phong, Bắc Ninh", receiver="Phạm Minh Đức", receiverPhone="0987 654 321"),
        "cargo": _mk_cargo(),
        "exportInfo": _mk_export_info(eta="02/09/2026", ata="02/09/2026", state="Đã thông quan"),
        "docs": _mk_docs(),
        "pxk": _mk_pxk(source="HDMB-PA-2026-031"),
        "finance": _mk_finance(),
        "timeline": _mk_timeline(),
        "missingDocs": ["Số tờ khai nhập khẩu", "Biển số xe VN"],
    },
    {
        "id": "LO-0307",
        "customer": "Công ty CP Công Nghệ Sao Việt",
        "customerShort": "Sao Việt",
        "customerMST": "0105998877",
        "customer_id": "sao_viet",
        "contract": "HDMB-PA-2026-027",
        "route": "Quảng Đông → Hữu Nghị → Hà Nội",
        "borderVN": "Hữu Nghị",
        "sale": "Hồng Nhung",
        "support": "Thu Hằng",
        "status": "Đang vận chuyển",
        "statusTone": "blue",
        "priority": "BinhThuong",
        "nextAction": "Theo dõi lịch trình xe TQ — dự kiến về VN 10/09",
        "nextActionDetail": "Xe 粤B·22K15 đang ở Hà Khẩu — đã qua cửa khẩu phụ",
        "nextLabel": "MỞ LÔ",
        "nextRoute": "/lo-hang/LO-0307?tab=lay-hang",
        "updated": "09/09/2026 08:10",
        "pickup": _mk_pickup(name="Nhà máy Bo Yi Quảng Đông", addr="Khu công nghiệp Đông Hải, Quảng Đông", contact="Mr. Chen", phone="+86 138 2233 4455", plate="粤B·22K15", driver="Trần Kiến Bình", driverPhone="+86 138 2233 4455", pickupTime="07/09/2026 08:00", ata="07/09/2026 17:20"),
        "importInfo": _mk_import_info(border="Hữu Nghị (VN)", declarationNo="", regDate="", tax=18_400_000, vat=36_800_000, plateVN="29H-481.36", driverVN="Phạm Văn Hùng", schedule="11/09/2026 09:00", deliveryAddr="Tòa nhà Sao Việt, Cầu Giấy, Hà Nội", receiver="Lê Quốc Bảo", receiverPhone="0903 222 111"),
        "cargo": _mk_cargo(type="Bo mạch điện tử", packs=18, weight="3.800 kg", cbm=12, dims="2.4 x 1.6 x 1.8 m"),
        "exportInfo": _mk_export_info(eta="07/09/2026", ata="07/09/2026", state="Đã thông quan"),
        "docs": [
            {"name": "Hợp đồng mua bán (HDMB)", "ok": True, "note": "HDMB-PA-2026-027"},
            {"name": "Packing List", "ok": True, "note": "18 kiện / 3.800 kg"},
            {"name": "Invoice (Hóa đơn thương mại)", "ok": True, "note": "INV-2026-0611"},
            {"name": "CO Form E", "ok": True, "note": "C/O đã có"},
            {"name": "Tờ khai xuất khẩu", "ok": True, "note": "Số TK XK: 305866443"},
        ],
        "pxk": _mk_pxk(source="HDMB-PA-2026-027"),
        "finance": _mk_finance(receivable=246_000_000, received=200_000_000, payable=22_400_000, paid=22_400_000, payments=[
            {"date": "01/09/2026", "kind": "Tạm ứng", "amount": 200_000_000, "ccy": "VND", "by": "Thu Hằng", "note": "Theo PL-027"},
        ]),
        "timeline": [
            {"time": "30/08 11:00", "title": "Đã tạo lô LO-0307", "desc": "Từ báo giá BG-2026-208 đã chốt", "tone": "blue"},
            {"time": "05/09 14:30", "title": "Đã chốt xe TQ", "desc": "Xe 粤B·22K15", "tone": "blue"},
            {"time": "07/09 08:00", "title": "Lấy hàng xong", "desc": "Đủ 18 kiện", "tone": "green"},
            {"time": "08/09 15:00", "title": "Xuất khẩu thông quan", "desc": "Tờ khai XK 305866443", "tone": "green"},
        ],
        "missingDocs": [],
    },
    {
        "id": "LO-0308",
        "customer": "Công ty TNHH Thiết Bị Minh Đức",
        "customerShort": "Minh Đức",
        "customerMST": "0200667788",
        "customer_id": "minh_duc",
        "contract": "HDMB-PA-2026-028",
        "route": "Quảng Đông → Hữu Nghị → Hải Phòng",
        "borderVN": "Hữu Nghị",
        "sale": "Hồng Nhung",
        "support": "Thu Hằng",
        "status": "Chờ lấy hàng",
        "statusTone": "amber",
        "priority": "Khan",
        "nextAction": "Chốt xe TQ + giờ lấy hàng trước 12:00 hôm nay",
        "nextActionDetail": "Nhà máy cần báo trước 24h — đang chờ Bằng Tường xác nhận xe",
        "nextLabel": "CHỐT XE NGAY",
        "nextRoute": "/lo-hang/LO-0308?tab=lay-hang",
        "updated": "09/09/2026 07:55",
        "pickup": _mk_pickup(name="Nhà máy Thiết Bị Minh Đức — CN Quảng Đông", addr="Khu CNC Đông Quan, Quảng Đông", contact="Mr. Wang", phone="+86 137 5566 7788", plate="", driver="", driverPhone="", pickupTime=""),
        "importInfo": _mk_import_info(border="Hữu Nghị (VN)", declarationNo="", plateVN="", driverVN="", schedule="12/09/2026", deliveryAddr="KCN Tràng Duệ, Hải Phòng", receiver="Nguyễn Hải Yến", receiverPhone="0912 345 678"),
        "cargo": _mk_cargo(type="Máy dập kim loại 200 tấn", packs=1, weight="18.500 kg", cbm=22, dims="4.2 x 2.0 x 2.6 m", note="Yêu cầu xe cẩu chuyên dụng"),
        "exportInfo": _mk_export_info(state="Chờ lấy hàng"),
        "docs": [
            {"name": "Hợp đồng mua bán (HDMB)", "ok": True, "note": "HDMB-PA-2026-028"},
            {"name": "Packing List", "ok": False, "note": "Đang chờ nhà máy cập nhật"},
            {"name": "Invoice (Hóa đơn thương mại)", "ok": True, "note": "INV-2026-0613"},
            {"name": "CO Form E", "ok": False, "note": "Chưa gửi đề nghị"},
            {"name": "Tờ khai xuất khẩu", "ok": False, "note": "Chưa khai"},
        ],
        "pxk": _mk_pxk(source="HDMB-PA-2026-028"),
        "finance": _mk_finance(receivable=425_000_000, received=120_000_000, payable=58_000_000, paid=0, payments=[
            {"date": "20/08/2026", "kind": "Tạm ứng", "amount": 120_000_000, "ccy": "VND", "by": "Thu Hằng", "note": "Tạm ứng 30%"},
        ]),
        "timeline": [
            {"time": "02/09 16:00", "title": "Đã tạo lô LO-0308", "desc": "Từ báo giá BG-2026-214 đã chốt", "tone": "blue"},
            {"time": "05/09 09:00", "title": "Đã ký HDMB-PA-2026-028", "desc": "Đang chờ lấy hàng", "tone": "blue"},
        ],
        "missingDocs": ["Biển số xe TQ", "Tài xế TQ", "Ngày lấy hàng", "Packing List"],
    },
    {
        "id": "LO-0299",
        "customer": "Công ty TNHH Phụ Kiện Hồng Hà",
        "customerShort": "Hồng Hà",
        "customerMST": "0102778899",
        "customer_id": "hong_ha",
        "contract": "HDNT-PA-2026-118",
        "route": "Quảng Tây → Tân Thanh → Hà Nội",
        "borderVN": "Tân Thanh",
        "sale": "Minh Anh",
        "support": "Thu Hằng",
        "status": "Chờ giao",
        "statusTone": "violet",
        "priority": "CanXuLy",
        "nextAction": "Giao hàng Yên Phong lúc 14:00 hôm nay + xác nhận đã giao",
        "nextActionDetail": "Xe 29H-481.36 đang về kho khách — chuẩn bị giấy tờ giao nhận",
        "nextLabel": "XEM LỊCH GIAO",
        "nextRoute": "/lo-hang/LO-0299?tab=nhap",
        "updated": "09/09/2026 06:30",
        "pickup": _mk_pickup(name="Nhà máy Nhựa Hồng Hà — Quảng Tây", plate="桂A·11M28", driver="Lý Minh Khải", driverPhone="+86 159 7788 9900", pickupTime="30/08/2026 10:00", ata="30/08/2026 16:00"),
        "importInfo": _mk_import_info(border="Tân Thanh (VN)", declarationNo="105877332110", regDate="04/09/2026", tax=24_500_000, vat=49_000_000, inspection="Luồng vàng", plateVN="29C-118.55", driverVN="Nguyễn Văn Cường", schedule="09/09/2026 14:00", deliveryAddr="KCN Từ Liêm, Hà Nội", receiver="Trần Hồng Hà", receiverPhone="0935 111 222"),
        "cargo": _mk_cargo(type="Phụ kiện nhựa công nghiệp", packs=20, weight="5.400 kg", cbm=14, dims="3.0 x 1.8 x 2.0 m"),
        "exportInfo": _mk_export_info(eta="31/08/2026", ata="31/08/2026", state="Đã thông quan"),
        "docs": [
            {"name": "Hợp đồng nguyên tắc (HDNT)", "ok": True, "note": "HDNT-PA-2026-118"},
            {"name": "Phụ lục (PL)", "ok": True, "note": "PL-118-A"},
            {"name": "Packing List", "ok": True, "note": "20 kiện / 5.400 kg"},
            {"name": "Invoice (Hóa đơn thương mại)", "ok": True, "note": "INV-2026-0588"},
            {"name": "CO Form E", "ok": True, "note": "C/O đã có"},
            {"name": "Tờ khai xuất khẩu", "ok": True, "note": "Số TK XK: 305855211"},
        ],
        "pxk": _mk_pxk(source="PL-118-A"),
        "finance": _mk_finance(receivable=214_600_000, received=100_000_000, payable=24_000_000, paid=24_000_000, payments=[
            {"date": "20/08/2026", "kind": "Tạm ứng 50%", "amount": 100_000_000, "ccy": "VND", "by": "Thu Hằng", "note": "Theo PL-118-A"},
        ]),
        "timeline": [
            {"time": "25/08 14:00", "title": "Đã tạo lô LO-0299", "desc": "Theo PL-118-A", "tone": "blue"},
            {"time": "30/08 10:00", "title": "Lấy hàng xong", "desc": "Đủ 20 kiện", "tone": "green"},
            {"time": "31/08 18:00", "title": "Xuất khẩu thông quan", "desc": "Tờ khai XK 305855211", "tone": "green"},
            {"time": "04/09 09:30", "title": "Đã khai tờ khai nhập khẩu", "desc": "Số TK 105877332110", "tone": "green"},
            {"time": "06/09 14:00", "title": "Đã nộp thuế", "desc": "Biên lai thuế 24,5 tr + VAT 49 tr", "tone": "green"},
        ],
        "missingDocs": [],
    },
    {
        "id": "LO-0295",
        "customer": "Công ty TNHH Cơ Khí An Phát",
        "customerShort": "An Phát",
        "customerMST": "0201884452",
        "customer_id": "an_phat",
        "contract": "HDMB-PA-2026-031",
        "route": "Quảng Tây → Tân Thanh → Bắc Ninh",
        "borderVN": "Tân Thanh",
        "sale": "Minh Anh",
        "support": "Thu Hằng",
        "status": "Đã giao",
        "statusTone": "green",
        "priority": "BinhThuong",
        "nextAction": "Thu nốt công nợ & xuất PXK",
        "nextActionDetail": "Đã giao 07/09 — chờ thu đợt 2 theo PL-031",
        "nextLabel": "THU TIỀN",
        "nextRoute": "/tai-chinh/thu-tien",
        "updated": "07/09/2026 14:30",
        "pickup": _mk_pickup(plate="粤A·77H22", driver="Lưu Vĩ An", driverPhone="+86 139 2611 8899", pickupTime="25/08/2026 08:00", ata="25/08/2026 13:20"),
        "importInfo": _mk_import_info(border="Tân Thanh (VN)", declarationNo="105722118", regDate="29/08/2026", tax=42_000_000, vat=84_000_000, inspection="Luồng xanh", plateVN="29H-318.22", driverVN="Bùi Văn Toàn", schedule="07/09/2026 09:00", deliveryAddr="KCN Yên Phong, Bắc Ninh", receiver="Phạm Minh Đức", receiverPhone="0987 654 321", delivered=True, actualDelivery="07/09/2026 11:30"),
        "cargo": _mk_cargo(type="Phụ kiện máy CNC", packs=24, weight="6.200 kg", cbm=12, dims="2.4 x 1.8 x 2.0 m"),
        "exportInfo": _mk_export_info(eta="26/08/2026", ata="26/08/2026", state="Đã thông quan"),
        "docs": [
            {"name": "Hợp đồng mua bán (HDMB)", "ok": True, "note": "HDMB-PA-2026-031"},
            {"name": "Packing List", "ok": True, "note": "24 kiện / 6.200 kg"},
            {"name": "Invoice (Hóa đơn thương mại)", "ok": True, "note": "INV-2026-0590"},
            {"name": "CO Form E", "ok": True, "note": "C/O đã có"},
            {"name": "Tờ khai xuất khẩu", "ok": True, "note": "Số TK XK: 305821014"},
        ],
        "pxk": _mk_pxk(number="PXK-2026-0295", date="07/09/2026", place="KCN Yên Phong, Bắc Ninh", receiver="Phạm Minh Đức", role="Thủ kho", source="HDMB-PA-2026-031", done=True),
        "finance": _mk_finance(receivable=386_500_000, received=300_000_000, payable=46_000_000, paid=46_000_000, payments=[
            {"date": "20/08/2026", "kind": "Tạm ứng 50%", "amount": 200_000_000, "ccy": "VND", "by": "Thu Hằng", "note": "Theo PL-031"},
            {"date": "30/08/2026", "kind": "Tạm ứng đợt 2", "amount": 100_000_000, "ccy": "VND", "by": "Thu Hằng", "note": "Trước khi xuất hàng"},
        ]),
        "timeline": [
            {"time": "20/08 09:00", "title": "Đã tạo lô LO-0295", "desc": "Theo PL-031", "tone": "blue"},
            {"time": "25/08 08:00", "title": "Lấy hàng xong", "desc": "Đủ 24 kiện", "tone": "green"},
            {"time": "26/08 15:00", "title": "Xuất khẩu thông quan", "desc": "Tờ khai XK 305821014", "tone": "green"},
            {"time": "29/08 10:00", "title": "Đã khai tờ khai nhập khẩu", "desc": "Số TK 105722118", "tone": "green"},
            {"time": "02/09 16:00", "title": "Đã nộp thuế", "desc": "Biên lai 42 tr + VAT 84 tr", "tone": "green"},
            {"time": "07/09 11:30", "title": "Đã giao hàng", "desc": "Khách ký nhận đủ kiện", "tone": "green"},
        ],
        "missingDocs": [],
    },
]


SEED_QUOTES = [
    {"id": "BG-2026-214", "customer": "Công ty TNHH Thiết Bị Minh Đức", "route": "Quảng Đông → Hữu Nghị → Hải Phòng", "goods": "Máy dập kim loại 200 tấn — 18.500 kg", "cost": 65_700_000, "price": 425_000_000, "margin": "84.5%", "status": "ACCEPTED"},
    {"id": "BG-2026-212", "customer": "Công ty TNHH Cơ Khí An Phát", "route": "Quảng Tây → Tân Thanh → Bắc Ninh", "goods": "Máy CNC 5 trục — 12.800 kg", "cost": 63_000_000, "price": 486_500_000, "margin": "87.0%", "status": "ACCEPTED"},
    {"id": "BG-2026-215", "customer": "Công ty CP Công Nghệ Sao Việt", "route": "Quảng Đông → Hữu Nghị → Hà Nội", "goods": "Bo mạch điện tử — 3.800 kg", "cost": 28_900_000, "price": 246_000_000, "margin": "88.2%", "status": "SENT"},
    {"id": "BG-2026-217", "customer": "Công ty TNHH Cơ Khí An Phát", "route": "Quảng Đông → Hữu Nghị → Hải Phòng", "goods": "Máy tiện CNC — 8.500 kg", "cost": 56_200_000, "price": 0, "margin": "—", "status": "DRAFT"},
]

SEED_AGREEMENTS = [
    {"id": "TT-BG-2026-212", "status": "AGREED", "customer": "Công ty TNHH Cơ Khí An Phát", "quote": "BG-2026-212", "incoterm": "DAP — Bắc Ninh", "payment": "Tạm ứng 50% / còn lại sau giao", "scope": "Vận chuyển TQ→VN, khai báo xuất nhập, giao tận kho", "handover": "Đã bàn giao cho Thu Hằng (Support) — 02/09/2026"},
    {"id": "TT-BG-2026-214", "status": "REVIEWING", "customer": "Công ty TNHH Thiết Bị Minh Đức", "quote": "BG-2026-214", "incoterm": "DDP — Hải Phòng", "payment": "Tạm ứng 30% / còn lại trước giao 7 ngày", "scope": "Vận chuyển + khai báo + thuế + giao tận kho", "handover": "Chờ Support ký xác nhận"},
]


SEED_HS = [
    {"hs": "8457", "nk": "0%", "vat": "8%", "desc": "Máy gia công kim loại bằng phương pháp bóc vật liệu (CNC)", "policy": "NK 0% theo FTA — yêu cầu C/O Form E", "note": "Phổ biến cho máy CNC, máy tiện, máy phay"},
    {"hs": "8460", "nk": "5%", "vat": "8%", "desc": "Máy mài, mài sắc, đánh bóng", "policy": "NK 5% (ưu đãi)", "note": "Có CO Form E giảm về 0%"},
    {"hs": "8504", "nk": "0%", "vat": "8%", "desc": "Biến thế, máy biến đổi điện tĩnh", "policy": "NK 0% cho biến tần công nghiệp", "note": ""},
    {"hs": "8537", "nk": "5%", "vat": "8%", "desc": "Bảng, panel điều khiển", "policy": "NK 5% — chứng nhận CE", "note": ""},
    {"hs": "8542", "nk": "0%", "vat": "8%", "desc": "Mạch điện tử tích hợp", "policy": "NK 0% theo ITA", "note": "Bo mạch, IC, chip nhớ"},
    {"hs": "3926", "nk": "8%", "vat": "8%", "desc": "Sản phẩm khác bằng plastic", "policy": "NK 8% — không ưu đãi", "note": "Phụ kiện nhựa công nghiệp"},
]

SEED_USERS = [
    {"name": "Thu Hằng", "username": "thu.hang", "role": "ADMIN", "status": "Đang hoạt động", "last": "09/09/2026 09:15"},
    {"name": "Minh Anh", "username": "minh.anh", "role": "SALE", "status": "Đang hoạt động", "last": "08/09/2026 17:30"},
    {"name": "Hồng Nhung", "username": "hong.nhung", "role": "SALE", "status": "Đang hoạt động", "last": "08/09/2026 16:42"},
    {"name": "Trần Bình", "username": "tran.binh", "role": "SUPPORT", "status": "Đang hoạt động", "last": "09/09/2026 08:55"},
    {"name": "Phạm Long", "username": "pham.long", "role": "SUPPORT", "status": "Tạm khóa", "last": "01/09/2026 10:00"},
]

# Partner-ledger (currencies separated)
SEED_PARTNER_VND = {
    "Đầu kỳ": 120_000_000,
    "Tăng trong kỳ": 96_500_000,
    "Đã thanh toán": 142_700_000,
    "Còn phải trả": 73_800_000,
}
SEED_PARTNER_CNY = {
    "Đầu kỳ": 45_200,
    "Tăng trong kỳ": 27_700,
    "Đã thanh toán": 45_200,
    "Còn phải trả": 27_700,
}

# Reconciliation VND/CNY summaries
SEED_RECONCILE = {
    "VND": {"open": 120_000_000, "incurred": 96_500_000, "paid": 142_700_000, "remain": 73_800_000},
    "CNY": {"open": 45_200, "incurred": 27_700, "paid": 45_200, "remain": 27_700},
}

# Receivable debt by lot for Finance > Thu tiền
SEED_RECEIVABLES = [
    {"customer": "Công ty TNHH Cơ Khí An Phát", "lot": "LO-0306", "contract": "HDMB-PA-2026-031", "must": 486_500_000, "got": 150_000_000, "due": "09/09/2026", "status": "Hạn hôm nay", "tone": "red"},
    {"customer": "Công ty TNHH Phụ Kiện Hồng Hà", "lot": "LO-0299", "contract": "HDNT-PA-2026-118", "must": 214_600_000, "got": 100_000_000, "due": "12/09/2026", "status": "Còn 3 ngày", "tone": "amber"},
    {"customer": "Công ty TNHH Cơ Khí An Phát", "lot": "LO-0295", "contract": "HDMB-PA-2026-031", "must": 386_500_000, "got": 300_000_000, "due": "12/09/2026", "status": "Còn 3 ngày", "tone": "blue"},
    {"customer": "Công ty CP Công Nghệ Sao Việt", "lot": "LO-0307", "contract": "HDMB-PA-2026-027", "must": 246_000_000, "got": 200_000_000, "due": "15/09/2026", "status": "Còn 6 ngày", "tone": "blue"},
    {"customer": "Công ty TNHH Thiết Bị Minh Đức", "lot": "LO-0308", "contract": "HDMB-PA-2026-028", "must": 425_000_000, "got": 120_000_000, "due": "20/09/2026", "status": "Còn 11 ngày", "tone": "blue"},
]

# Top-level KPI for CEO / Home
SEED_KPI = {
    "totals": {
        "receivable": 1_087_600_000,
        "received": 550_000_000,
        "remain": 537_600_000,
        "payable": 73_800_000,
    },
    "shipments_running": 4,
    "shipments_today_delivered": 1,
    "today": "09/09/2026",
    "month_label": "Tháng 9",
    "revenue_month": 890_000_000,
    "profit_month": 148_000_000,
    "prev_revenue": 1_510_000_000,
    "prev_profit": 262_000_000,
    "prev_label": "T8",
    "utilization": {
        "wait": 1, "transport": 1, "clear": 1, "deliver": 1, "done": 3,
    },
    "top_customers": [
        {"name": "Cơ Khí An Phát", "value": 873_000_000, "share": 100},
        {"name": "Sao Việt", "value": 247_000_000, "share": 42},
        {"name": "Hồng Hà", "value": 215_000_000, "share": 36},
        {"name": "Minh Đức", "value": 172_000_000, "share": 28},
    ],
    "bottlenecks": [
        {"title": "Thông quan Hữu Nghị chậm 1,5 ngày", "desc": "LO-0306 thiếu tờ khai — xử lý trước 17:00", "to": "/lo-hang/LO-0306?tab=nhap"},
        {"title": "Xe TQ LO-0308 chưa chốt", "desc": "Nhà máy cần trước 24h — gọi Bằng Tường ngay", "to": "/lo-hang/LO-0308?tab=lay-hang"},
        {"title": "Công nợ An Phát 336,5 tr hạn hôm nay", "desc": "Thu tạm ứng đợt 2 — Minh Anh phụ trách", "to": "/tai-chinh/thu-tien"},
    ],
}

# Tasks
SEED_TASKS = [
    {"id": "T-301", "level": "Khan", "lot": "LO-0306", "customer": "Công ty TNHH Cơ Khí An Phát", "job": "Khai tờ khai nhập khẩu + nộp thuế NK/VAT", "assignee": "Thu Hằng", "due": "17:00 hôm nay", "dueNote": "09/09/2026", "status": "Đang chờ", "statusTone": "amber", "route": "/lo-hang/LO-0306?tab=nhap"},
    {"id": "T-302", "level": "Khan", "lot": "LO-0308", "customer": "Công ty TNHH Thiết Bị Minh Đức", "job": "Chốt xe TQ + giờ lấy hàng", "assignee": "Trần Bình", "due": "12:00 hôm nay", "dueNote": "09/09/2026", "status": "Đang chờ", "statusTone": "amber", "route": "/lo-hang/LO-0308?tab=lay-hang"},
    {"id": "T-303", "level": "Khan", "lot": "LO-0299", "customer": "Công ty TNHH Phụ Kiện Hồng Hà", "job": "Giao hàng + xác nhận đã giao", "assignee": "Trần Bình", "due": "14:00 hôm nay", "dueNote": "09/09/2026", "status": "Sẵn sàng", "statusTone": "green", "route": "/lo-hang/LO-0299?tab=nhap"},
    {"id": "T-304", "level": "CanXuLy", "lot": "LO-0306", "customer": "Công ty TNHH Cơ Khí An Phát", "job": "Bổ sung CO Form E cho lô", "assignee": "Hồng Nhung", "due": "10/09/2026", "dueNote": "Còn 1 ngày", "status": "Đang xử lý", "statusTone": "blue", "route": "/lo-hang/LO-0306?tab=chung-tu"},
    {"id": "T-305", "level": "CanXuLy", "lot": "—", "customer": "Bằng Tường (Đại lý)", "job": "Đối soát cước xe TQ tháng 9", "assignee": "Thu Hằng", "due": "12/09/2026", "dueNote": "Còn 3 ngày", "status": "Đang xử lý", "statusTone": "blue", "route": "/tai-chinh/doi-soat"},
    {"id": "T-306", "level": "CanXuLy", "lot": "LO-0308", "customer": "Công ty TNHH Thiết Bị Minh Đức", "job": "Yêu cầu nhà máy gửi Packing List", "assignee": "Trần Bình", "due": "10/09/2026", "dueNote": "Còn 1 ngày", "status": "Đang chờ", "statusTone": "amber", "route": "/lo-hang/LO-0308?tab=chung-tu"},
    {"id": "T-307", "level": "CanXuLy", "lot": "LO-0295", "customer": "Công ty TNHH Cơ Khí An Phát", "job": "Thu nốt công nợ 86,5 tr", "assignee": "Minh Anh", "due": "12/09/2026", "dueNote": "Còn 3 ngày", "status": "Sẵn sàng", "statusTone": "green", "route": "/tai-chinh/thu-tien"},
    {"id": "T-308", "level": "BinhThuong", "lot": "LO-0307", "customer": "Công ty CP Công Nghệ Sao Việt", "job": "Theo dõi lịch trình xe TQ về VN", "assignee": "Trần Bình", "due": "10/09/2026", "dueNote": "Còn 1 ngày", "status": "Đang xử lý", "statusTone": "blue", "route": "/lo-hang/LO-0307?tab=lay-hang"},
    {"id": "T-309", "level": "BinhThuong", "lot": "LO-0299", "customer": "Công ty TNHH Phụ Kiện Hồng Hà", "job": "Gửi báo cáo giao hàng cho Sale", "assignee": "Thu Hằng", "due": "11/09/2026", "dueNote": "Còn 2 ngày", "status": "Đang xỬ lý", "statusTone": "blue", "route": "/lo-hang/LO-0299?tab=lich-su"},
    {"id": "T-310", "level": "BinhThuong", "lot": "—", "customer": "—", "job": "Cập nhật danh bạ đối tác Bằng Tường", "assignee": "Thu Hằng", "due": "30/09/2026", "dueNote": "Còn 21 ngày", "status": "Mới", "statusTone": "gray", "route": "/ngu-canh-doi-tac"},
]

# Handbook content
SEED_HANDBOOK = [
    {"title": "Sale mới: từ báo giá tới hợp đồng", "read_time": "5 phút", "body": "1. Lập báo giá → 2. Gửi khách → 3. Khách chốt → 4. Lập thỏa thuận → 5. Tạo hợp đồng → 6. Gắn lô. Mỗi bước đều có nút dẫn tiếp."},
    {"title": "Support: xử lý lô từ lấy hàng tới giao", "read_time": "7 phút", "body": "Chốt xe TQ → theo dõi xuất khẩu → khai nhập (số TK 12 số) → nộp thuế → đặt xe VN → giao & xác nhận → xuất PXK → thu tiền."},
    {"title": "Khi thiếu chứng từ phải làm gì?", "read_time": "3 phút", "body": "Không bỏ qua cảnh báo: bấm BỔ SUNG ngay tại chỗ, tải file hoặc ghi lý do + hạn. Mọi cảnh báo đều kèm nút hành động."},
    {"title": "Ngưỡng 50 triệu: HDNT+PL hay HDMB?", "read_time": "2 phút", "body": "Tổng sau VAT dưới 50tr → HDNT + PL. Từ đúng 50tr trở lên → HDMB. Máy tự gợi ý, bạn chỉ nhập ngày ký."},
    {"title": "Đối soát với đại lý: tách VND / CNY", "read_time": "4 phút", "body": "Mỗi đồng tiền 1 sổ riêng. Tuyệt đối không quy đổi gộp. Đối soát tháng 9 của Bằng Tường: VND còn 73,8 tr, CNY còn ¥27.700."},
    {"title": "Quy tắc ngầm khi xếp lịch xe VN", "read_time": "3 phút", "body": "Đặt xe VN trước giờ giao ít nhất 4 tiếng. Xe Cont 40HQ ưu tiên chạy ca ngày. Bắc Ninh đi sáng sớm, Hải Phòng đi trưa."},
]

# Notifications
SEED_NOTIFS = [
    {"id": "N-901", "tone": "red", "title": "LO-0306 thiếu tờ khai — hạn 17:00 hôm nay", "desc": "Bổ sung số tờ khai + biên lai thuế để thông quan", "time": "5 phút trước"},
    {"id": "N-902", "tone": "amber", "title": "LO-0299 sắp tới giờ giao 14:00", "desc": "Kiểm tra xe VN 29H-481.36 đã về kho chưa", "time": "20 phút trước"},
    {"id": "N-903", "tone": "blue", "title": "Đại lý Bằng Tường đã gửi bảng kê cước T9", "desc": "Còn thiếu biên lai 2 lô — mở Đối soát để xử lý", "time": "1 giờ trước"},
    {"id": "N-904", "tone": "red", "title": "An Phát còn nợ 336,5 tr hạn hôm nay", "desc": "Thu tạm ứng đợt 2 — Minh Anh phụ trách", "time": "2 giờ trước"},
]


# ============================================================================
# State management — wired to the actual Logistics session_state where possible
# ============================================================================

def _ensure_store():
    """Initialize a sandbox data store if not already present."""
    st.session_state.setdefault("_donor_seed", False)
    st.session_state.setdefault("donor_shipments", [deepcopy(s) for s in SEED_SHIPMENTS])
    st.session_state.setdefault("donor_customers", deepcopy(SEED_CUSTOMERS))
    st.session_state.setdefault("donor_contracts", [deepcopy(c) for c in SEED_CONTRACTS])
    st.session_state.setdefault("donor_quotes", [deepcopy(q) for q in SEED_QUOTES])
    st.session_state.setdefault("donor_agreements", [deepcopy(a) for a in SEED_AGREEMENTS])
    st.session_state.setdefault("donor_hs", [deepcopy(h) for h in SEED_HS])
    st.session_state.setdefault("donor_users", [deepcopy(u) for u in SEED_USERS])
    st.session_state.setdefault("donor_tasks", [deepcopy(t) for t in SEED_TASKS])
    st.session_state.setdefault("donor_receivables", [deepcopy(r) for r in SEED_RECEIVABLES])
    st.session_state.setdefault("donor_partner_vnd", deepcopy(SEED_PARTNER_VND))
    st.session_state.setdefault("donor_partner_cny", deepcopy(SEED_PARTNER_CNY))
    st.session_state.setdefault("donor_reconcile", deepcopy(SEED_RECONCILE))
    st.session_state.setdefault("donor_kpi", deepcopy(SEED_KPI))
    st.session_state.setdefault("donor_handbook", deepcopy(SEED_HANDBOOK))
    st.session_state.setdefault("donor_notifs", deepcopy(SEED_NOTIFS))
    st.session_state.setdefault("donor_toasts", [])
    st.session_state.setdefault("donor_role", "ADMIN")
    st.session_state.setdefault("donor_user", {"name": "Thu Hằng", "display_name": "Thu Hằng", "username": "thu.hang", "role": "ADMIN"})
    st.session_state.setdefault("active_page", "home")
    st.session_state.setdefault("active_route", "/")
    st.session_state.setdefault("active_shipment_id", "LO-0306")
    st.session_state.setdefault("active_contract_id", "HDMB-PA-2026-031")
    st.session_state.setdefault("active_tab", "lay-hang")
    st.session_state.setdefault("active_contract_tab", "hang-hoa")


# ============================================================================
# Read-only accessors
# ============================================================================

def get_shipments():
    _ensure_store()
    return st.session_state.donor_shipments

def get_customers():
    _ensure_store()
    return st.session_state.donor_customers

def get_contracts():
    _ensure_store()
    return st.session_state.donor_contracts

def get_quotes():
    _ensure_store()
    return st.session_state.donor_quotes

def get_agreements():
    _ensure_store()
    return st.session_state.donor_agreements

def get_hs():
    _ensure_store()
    return st.session_state.donor_hs

def get_users():
    _ensure_store()
    return st.session_state.donor_users

def get_tasks():
    _ensure_store()
    return st.session_state.donor_tasks

def get_receivables():
    _ensure_store()
    return st.session_state.donor_receivables

def get_partner_vnd():
    _ensure_store()
    return st.session_state.donor_partner_vnd

def get_partner_cny():
    _ensure_store()
    return st.session_state.donor_partner_cny

def get_reconcile():
    _ensure_store()
    return st.session_state.donor_reconcile

def get_kpi():
    _ensure_store()
    return st.session_state.donor_kpi

def get_handbook():
    _ensure_store()
    return st.session_state.donor_handbook

def get_notifs():
    _ensure_store()
    return st.session_state.donor_notifs

def get_role():
    _ensure_store()
    return st.session_state.donor_role

def set_role(role: str):
    _ensure_store()
    st.session_state.donor_role = role
    st.session_state.donor_user = {"name": st.session_state.donor_user.get("name", "Thu Hằng"), "display_name": st.session_state.donor_user.get("name", "Thu Hằng"), "username": st.session_state.donor_user.get("username", "thu.hang"), "role": role}

def get_user():
    _ensure_store()
    return st.session_state.donor_user

def get_toasts():
    _ensure_store()
    return list(st.session_state.donor_toasts)

def push_toast(title: str, desc: str = "", tone: str = "blue"):
    _ensure_store()
    toast = {"id": str(uuid.uuid4()), "title": title, "desc": desc, "tone": tone, "ts": datetime.now().isoformat()}
    st.session_state.donor_toasts.append(toast)
    # cap to last 3
    if len(st.session_state.donor_toasts) > 3:
        st.session_state.donor_toasts = st.session_state.donor_toasts[-3:]

def dismiss_toast(toast_id: str):
    _ensure_store()
    st.session_state.donor_toasts = [t for t in st.session_state.donor_toasts if t["id"] != toast_id]


# ============================================================================
# Mutations — re-use the real Logistics writers if enabled, else mutate seed
# ============================================================================

def find_shipment(sid: str):
    for s in get_shipments():
        if s["id"] == sid:
            return s
    return None

def find_contract(cid: str):
    for c in get_contracts():
        if c["id"] == cid:
            return c
    return None

def find_customer(cid: str):
    return get_customers().get(cid)

def update_shipment(sid: str, updater):
    """Apply `updater(shipment)` to the shipment, persisting to the underlying store.

    updater receives the dict and may mutate it. Returns the updated shipment.
    """
    ships = get_shipments()
    for i, s in enumerate(ships):
        if s["id"] == sid:
            updated = updater(s)
            if updated is not None:
                ships[i] = updated
            return ships[i]
    return None

def update_contract(cid: str, updater):
    contracts = get_contracts()
    for i, c in enumerate(contracts):
        if c["id"] == cid:
            updated = updater(c)
            if updated is not None:
                contracts[i] = updated
            return contracts[i]
    return None

def update_customer(cid: str, updater):
    custs = get_customers()
    if cid in custs:
        updated = updater(custs[cid])
        if updated is not None:
            custs[cid] = updated
    return custs.get(cid)

def add_quote(quote: dict):
    q = get_quotes()
    q.insert(0, quote)
    return quote

def add_receivable(rec: dict):
    r = get_receivables()
    r.insert(0, rec)
    return rec

def record_payment(sid: str, amount: int, kind: str, note: str = ""):
    """Add a payment to a shipment's finance history and bump received total."""
    def updater(s):
        s["finance"]["received"] = s["finance"].get("received", 0) + amount
        s["finance"].setdefault("payments", []).append({
            "date": datetime.now().strftime("%d/%m/%Y"),
            "kind": kind,
            "amount": amount,
            "ccy": "VND",
            "by": "Thu Hằng",
            "note": note or "Ghi nhận từ workspace",
        })
        s["timeline"].append({
            "time": datetime.now().strftime("%d/%m %H:%M"),
            "title": f"Ghi nhận {kind} — {amount:,.0f} ₫".replace(",", "."),
            "desc": note or "Ghi nhận từ workspace",
            "tone": "green",
        })
        s["updated"] = datetime.now().strftime("%d/%m/%Y %H:%M")
        return s
    return update_shipment(sid, updater)


# ============================================================================
# Active page routing — drives the shell
# ============================================================================

def init_session_state():
    """Ensure session state and store defaults exist."""
    _ensure_store()


def get_active_page() -> str:
    _ensure_store()
    return st.session_state.get("active_page", "home")

def set_active_page(page: str, route: str = None):
    _ensure_store()
    st.session_state["active_page"] = page
    if route:
        st.session_state["active_route"] = route


def get_active_route() -> str:
    _ensure_store()
    return st.session_state.get("active_route", "/")


def get_shipment_id() -> str:
    _ensure_store()
    return st.session_state.get("active_shipment_id", "LO-0306")

def set_shipment_id(sid: str, tab: str = None):
    _ensure_store()
    st.session_state["active_shipment_id"] = sid
    if tab:
        st.session_state["active_tab"] = tab


def get_contract_id() -> str:
    _ensure_store()
    return st.session_state.get("active_contract_id", "HDMB-PA-2026-031")

def set_contract_id(cid: str, tab: str = None):
    _ensure_store()
    st.session_state["active_contract_id"] = cid
    if tab:
        st.session_state["active_contract_tab"] = tab


def get_active_tab() -> str:
    _ensure_store()
    return st.session_state.get("active_tab", "lay-hang")

def set_active_tab(tab: str):
    _ensure_store()
    st.session_state["active_tab"] = tab


def get_contract_tab() -> str:
    _ensure_store()
    return st.session_state.get("active_contract_tab", "hang-hoa")

def get_active_contract_tab() -> str:
    _ensure_store()
    return st.session_state.get("active_contract_tab", "hang-hoa")

def set_contract_tab(tab: str):
    _ensure_store()
    st.session_state["active_contract_tab"] = tab


# Backward-compat shim for views that use the original Logistics helpers
def load_data():
    """Alias used by some real writers — returns the sandbox shipments."""
    _ensure_store()
    return {s["id"]: s for s in get_shipments()}


def load_customers():
    _ensure_store()
    return get_customers()

def load_contracts():
    _ensure_store()
    return {c["id"]: c for c in get_contracts()}
