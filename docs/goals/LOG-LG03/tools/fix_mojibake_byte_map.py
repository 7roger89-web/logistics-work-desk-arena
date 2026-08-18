#!/usr/bin/env python3
"""LG03: Sửa mojibake stubborn (đoạn không round-trip hoàn hảo) bằng bảng map byte.
Chỉ thay các đoạn đã xác minh nguồn gốc. Áp dụng trên các file được phép.
--dry-run mặc định; --apply để ghi. Backup .mojibake.bak."""
from __future__ import annotations

import ast
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]

ALLOWED = [
    'views/proxy_payment.py', 'views/shipment_360.py',
    'core/database.py', 'core/excel_utils.py', 'core/getfly_reader.py',
    'core/shipment_360.py', 'core/shipment_dashboard.py',
]

# (mojibake-bytes, clean-utf8-bytes) — đã xác minh nghĩa gốc
MAP = [
    # "Lịch sử thanh toán"
    (b'L\xc3\xa1\xc2\xbb\xe2\x80\xb9ch s\xc3\xa1\xc2\xbb\xc2\xad thanh to\xc3\xa1n', 'Lịch sử thanh toán'.encode('utf-8')),
    # "đã" dạng \xc3\x84\xe2\x80\x98\xc3\xa3 (đ -> Ä‘ mojibake với smart quote giữa)
    (b'\xc3\x84\xe2\x80\x98\xc3\xa3', 'Đã'.encode('utf-8')),
    # "được"
    (b'\xc3\x84\xe2\x80\x98\xc6\xb0\xe1\xbb\xa3c', 'được'.encode('utf-8')),
    # "đã được" dạng \xc3\x84\xe2\x80\x98\xc3\xa3 \xc3\x84\xe2\x80\x98\xc6\xb0\xe1\xbb\xa3c
    (b'\xc3\x84\xe2\x80\x98\xc3\xa3 \xc3\x84\xe2\x80\x98\xc6\xb0\xe1\xbb\xa3c', 'đã được'.encode('utf-8')),
    # "ĐÃ THU ĐỦ"
    # "ĐÃ THANH TOÁN"
    # (KHÔNG PHẢI handled elsewhere)
    # "SỐ TIỀN THANH TOÁN PHẢI LỚN HƠN 0"
    (b'S\xc3\xa1\xc2\xbb\xe2\x80\x98 ti\xe1\xbb\x81n thanh to\xc3\xa1n ph\xe1\xba\xa3i l\xc3\xa1\xc2\xbb\xe2\x80\xban h\xc6\xa1n 0', 'Số tiền thanh toán phải lớn hơn 0'.encode('utf-8')),
    # "Khoản thu" 
    (b'Kho\xc3\xa1\xc2\xba\xc2\xa3n thu', 'Khoản thu'.encode('utf-8')),
    # "yêu cầu"
    (b'y\xc3\x83\xc2\xaau c\xe1\xba\xa7u', 'yêu cầu'.encode('utf-8')),
    # "đúng" 
    (b'\xc4\x91\xc3\x83\xc2\xb0ng', 'đúng'.encode('utf-8')),
    # "hợp đồng"
    (b'h\xe1\xbb\xa3p \xc3\x84\xe2\x80\x98\xc3\xa1\xc2\xbb\xe2\x80\x9cng', 'hợp đồng'.encode('utf-8')),
    # "giao dịch"
    (b'giao d\xc3\xa1\xc2\xbb\xe2\x80\xb9ch', 'giao dịch'.encode('utf-8')),
    # (không được dùng cho nội dung khác handled elsewhere)
    # "đã bị trùng nhưng không được lọc lại"
    (b'b\xc3\xa1\xc2\xbb\xe2\x80\xb9 tr\xc3\xb9ng nh\xc6\xb0ng', 'bị trùng nhưng'.encode('utf-8')),
    # "không lưu được"
    # "được thanh toán hộ"
    # "đủ" dạng \xc4\x90\xe1\xbb\xa7/\xc4\x90\xe1\xbb\xa6
    # "ĐÃ SỬA" (excel_utils comment)
    (b'\xc4\x90\xc3\x83 S\xc3\xa1\xc2\xbb\xc2\xacA', 'ĐÃ SỬA'.encode('utf-8')),
    # "ĐÃ BẮT CẮT MÔ TẢ CỦA GETFLY"
    (b'\xc4\x90\xc3\x83 B\xc3\xa1\xc2\xba\xc2\xaeT C\xc3\xa1\xc2\xbb\xc2\x98T', 'ĐÃ BẮT CẮT'.encode('utf-8')),
    (b'M\xc3\x94 T\xc3\x81\xc2\xa2 C\xc3\xa1\xc2\xbb\xc2\xa6A', 'MÔ TẢ CỦA'.encode('utf-8')),
    # "Cần đối soát"
    # "mô tả"
    # "bảng giá" ?
    (b'kh\xc3\x83\xc2\xb4ng', 'không'.encode('utf-8')),
    # "phải có"
    (b'ph\xc3\xa1\xc2\xba\xc2\xa3i c\xc3\x83\xc2\xb3', 'phải có'.encode('utf-8')),
    # "cần có"
    # "Mã hợp đồng"
    (b'm\xc3\xa3 h\xe1\xbb\xa3p \xc3\x84\xe2\x80\x98\xc3\xa1\xc2\xbb\xe2\x80\x9cng', 'mã hợp đồng'.encode('utf-8')),
    # "không cấp transaction cho giao dịch hợp đồng"
    (b'giao d\xc3\x83\xc2\xacch h\xe1\xbb\xa3p \xc3\x84\xe2\x80\x98\xc3\xa1\xc2\xbb\xe2\x80\x9cng', 'giao dịch hợp đồng'.encode('utf-8')),
    # "đã" đơn lẻ kiểu \xc3\x84\xe2\x80\x98\xc3\xa3 đã fix ở trên; dạng \xc3\x84\xe2\x80\x98\xc3\xa3 có thể đứng riêng
    # "bảng thanh toán hộ"
    (b'thanh to\xc3\xa1n h\xc3\xa1\xc2\xbb\xe2\x84\xa2', 'thanh toán hộ'.encode('utf-8')),
    # "thêm/xoá trực tiếp"
    (b'th\xc3\x83\xc2\xaam/xo\xc3\x83\xc2\xa1 tr\xc3\x83\xc2\xb9c ti\xc3\xa1\xc2\xba\xc2\xbfp', 'thêm/xoá trực tiếp'.encode('utf-8')),
    # "đổi ID hoặc xóa"
    (b'\xc3\x84\xe2\x80\x98\xe1\xbb\x95i ID ho\xe1\xba\xb7c xo\xc3\xa1', 'đổi ID hoặc xóa'.encode('utf-8')),
    # "đã xử lý trước đó"
    (b'\xc3\x84\xe2\x80\x98\xc3\xa3 \xc3\x84\xe2\x80\x98\xc6\xb0\xe1\xbb\xa3c x\xc3\xa1\xc2\xbb\xc2\xad l\xc3\x83\xc2\xbd tr\xc3\x86\xc2\xb0\xc3\xa1\xc2\xbb\xe2\x80\xbac \xc3\x84\xe2\x80\x98\xc3\xb3', 'đã được xử lý trước đó'.encode('utf-8')),
    # "Khoản thu phải có"
    (b'Kho\xc3\xa1\xc2\xba\xc2\xa3n thu ph\xc3\xa1\xc2\xba\xc2\xa3i c\xc3\x83\xc2\xb3', 'Khoản thu phải có'.encode('utf-8')),
    # "MongoDB chưa sẵn sàng"
    (b'MongoDB ch\xc3\x86\xc2\xb0a s\xc3\xa1\xc2\xba\xc2\xb5n s\xc3\x83\xc2\xa0ng', 'MongoDB chưa sẵn sàng'.encode('utf-8')),
    # "Khoản thu đã tồn tại và được khóa theo"
    (b'Kho\xc3\xa1\xc2\xba\xc2\xa3n thu \xc3\x84\xe2\x80\x98\xc3\x83\xc2\xa3 t\xc3\xa1\xc2\xbb\xe2\x80\x9cn t\xc3\xa1\xc2\xba\xc2\xa1i v\xc3\x83 \xc3\x84\xe2\x80\x98\xc3\x86\xc2\xb0\xc3\xa1\xc2\xbb\xc2\xa3c kh\xc3\x83\xc2\xb3a', 'Khoản thu đã tồn tại và được khóa'.encode('utf-8')),
    # "Reversal phải có original"
    (b'Correction ph\xc3\xa1\xc2\xba\xc2\xa3i c\xc3\x83\xc2\xb3 original, request identity v\xc3\x83\xa0 reason', 'Correction phải có original, request identity và reason'.encode('utf-8')),
    # "Entrustment batch phải có request identity"
    (b'Entrustment batch ph\xc3\xa1\xc2\xba\xc2\xa3i c\xc3\x83\xc2\xb3 request identity', 'Entrustment batch phải có request identity'.encode('utf-8')),
    # "Dữ liệu đã được người khác" (handled elsewhere - truncated form == clean bytes, gây loop)
    # "Khoản thu phải có shipment_id và request identity"
    (b'Kho\xc3\xa1\xc2\xba\xc2\xa3n thu ph\xc3\xa1\xc2\xba\xc2\xa3i c\xc3\x83\xc2\xb3 shipment_id v\xc3\x83\xa0 request identity', 'Khoản thu phải có shipment_id và request identity'.encode('utf-8')),
    # "Khoản thu đã được xử lý trước đó"
    (b'Kho\xc3\xa1\xc2\xba\xc2\xa3n thu \xc3\x84\xe2\x80\x98\xc3\x83\xc2\xa3 \xc3\x84\xe2\x80\x98\xc3\x86\xc2\xb0\xc3\xa1\xc2\xbb\xc2\xa3c x\xc3\xa1\xc2\xbb\xc2\xad l\xc3\x83\xc2\xbd tr\xc3\xa1\xc2\xbb\xe2\x80\xbac \xc3\x84\xe2\x80\x98\xc3\x83\xc2\xb3', 'Khoản thu đã được xử lý trước đó'.encode('utf-8')),
    # "MongoDB không cung cấp transaction cho financial write"
    (b'MongoDB kh\xc3\x83\xc2\xb4ng cung c\xc3\xa1\xc2\xba\xc2\xa5p transaction cho financial write', 'MongoDB không cung cấp transaction cho financial write'.encode('utf-8')),
    # "Request identity đã có nội dung khác"
    (b'Request identity \xc3\x84\xe2\x80\x98\xc3\x83\xc2\xa3 c\xc3\x83\xc2\xb3 n\xc3\xa1\xc2\xbb\xe2\x84\xa2i dung kh\xc3\x83\xc2\xa1c', 'Request identity đã có nội dung khác'.encode('utf-8')),
    # "Request identity Đã có nội dung khác" (dạng Đ đã in hoa)
    (b'Request identity \xc4\x90\xc3\xa3 c\xc3\xb3 n\xc3\xa1\xc2\xbb\xe2\x84\xa2i dung kh\xc3\xa1c', 'Request identity Đã có nội dung khác'.encode('utf-8')),
    # "THỰC TẾ ĐÃ CHUYỂN" (proxy_payment)
    (b'TH\xc4\x86\xc2\xb0C T\xc3\x82\xc2\xa2 \xc4\x90\xc3\x83 CHUY\xc3\x82\xc2\xa2N', 'THỰC TẾ ĐÃ CHUYỂN'.encode('utf-8')),
    # "TỔNG VNĐ ĐÃ THU" (proxy_payment)
    (b'T\xc3\x94NG VN\xc4\x90 \xc4\x90\xc3\x83 THU', 'TỔNG VNĐ ĐÃ THU'.encode('utf-8')),
    # "ĐÃ THU" metric (shipment_360) — mojibake: \xc4\x90\xc3\x83 = Đ + Ã
    # "ĐÃ TRẢ / CẤN TRỪ"
    (b'\xc4\x90\xc3\x83 TR\xc3\xa1\xc2\xba\xc2\xa2 / C\xc3\xa1\xc2\xba\xc2\xa4N TR\xc3\xa1\xc2\xbb\xc2\xaa', 'ĐÃ TRẢ / CẤN TRỪ'.encode('utf-8')),
    # "CHI PHÍ ĐÃ BIẾT"
    (b'CHI PH\xc3\x8d \xc4\x90\xc3\x83 BI\xc3\xa1\xc2\xba\xc2\xbeT', 'CHI PHÍ ĐÃ BIẾT'.encode('utf-8')),
    # "ĐÃ THU ĐỦ PHẢI THU — CHỜ" (shipment_360 financial_status)
    (b'\xc4\x90\xc3\x83 THU \xc4\x90\xe1\xbb\xa6 PH\xc3\xa1\xc2\xba\xc2\xa2I THU \xe2\x80\x94', 'ĐÃ THU ĐỦ PHẢI THU —'.encode('utf-8')),
    # "Khoản thu phải có request identity" dạng m\xc3\xa1
    (b'Kho\xc3\xa1\xc2\xba\xc2\xa3n thu m\xc3\xa1\xc2\xbb\xe2\x80\xbai ph\xc3\xa1\xc2\xba\xc2\xa3i c\xc3\xb3 request i', 'Khoản thu phải có request i'.encode('utf-8')),
    # "Lịch sử thanh toán không được thêm/xoá trực tiếp" dạng còn sót
    (b'L\xc3\xa1\xc2\xbb\xe2\x80\xb9ch s\xc3\xa1\xc2\xbb\xc2\xad thanh to\xc3\xa1n c\xc5\xa9', 'Lịch sử thanh toán cũ'.encode('utf-8')),
    # "được đổi ID hoặc xóa"
    (b'\xc4\x91\xc6\xb0\xe1\xbb\xa3c \xc3\x84\xe2\x80\x98\xc3\xa1\xc2\xbb\xe2\x80\xa2i ID ho\xc3\xa1\xc2\xba\xc2\xb7c xo\xc3\xa1', 'được đổi ID hoặc xóa'.encode('utf-8')),
    # "xử lý trước đó" dạng còn sót
    (b'x\xc3\xa1\xc2\xbb\xc2\xad l\xc3\xbd tr\xc3\x86\xc2\xb0\xc3\xa1\xc2\xbb\xe2\x80\xbac \xc3\x84\xe2\x80\x98\xc3\xb3', 'xử lý trước đó'.encode('utf-8')),
    # "Khoản thu Đã tồn tại và được khóa"
    (b'\xc3\xa1\xc2\xba\xc2\xa3n thu \xc4\x90\xc3\xa3 t\xc3\xa1\xc2\xbb\xe2\x80\x9cn t\xc3\xa1\xc2\xba\xc2\xa1i v\xc3\xa0 \xc4\x91\xc6\xb0\xe1\xbb\xa3c k', 'ản thu Đã tồn tại và được k'.encode('utf-8')),
    # "không được dùng cho nội dung khác"
    (b'\xc4\x91\xc6\xb0\xe1\xbb\xa3c d\xc3\xb9ng cho n\xc3\xa1\xc2\xbb\xe2\x84\xa2i dung kh\xc3\xa1c', 'được dùng cho nội dung khác'.encode('utf-8')),
    # "Thanh toán hộ cần có mã giao dịch"
    (b'Thanh to\xc3\xa1n h\xc3\xa1\xc2\xbb\xe2\x84\xa2 c\xc3\xa1\xc2\xba\xc2\xa7n c\xc3\xb3 m\xc3\xa3 giao d', 'Thanh toán hộ cần có mã giao d'.encode('utf-8')),
    # "cần có mã hợp đồng"
    (b'c\xc3\xa1\xc2\xba\xc2\xa7n c\xc3\xb3 m\xc3\xa3 h\xc3\xbb\xa3p \xc4\x90', 'cần có mã h'.encode('utf-8')),
    # "ĐÃ SỬA 1/2" comments (proxy_payment)
    (b'\xc4\x90\xc3\x83 S\xc3\xa1\xc2\xbb\xc2\xacA 1', 'ĐÃ SỬA 1'.encode('utf-8')),
    (b'\xc4\x90\xc3\x83 S\xc3\xa1\xc2\xbb\xc2\xacA 2', 'ĐÃ SỬA 2'.encode('utf-8')),
    # excel_utils comment "Đã SỬA"
    (b'\xc4\x90\xc3\x83 S\xc3\xa1\xc2\xbb\xc2\xacA', 'ĐÃ SỬA'.encode('utf-8')),
    # getfly comment "ĐÃ BẮT CẮT MÔ TẢ CỦA"
    (b'\xc4\x90\xc3\x83 B\xc3\xa1\xc2\xba\xc2\xaeT C\xc3\xa1\xc2\xbb\xc2\x98T M\xc3\x94 T\xc3\x81\xc2\xa2 C\xc3\xa1\xc2\xbb\xc2\xa6A', 'ĐÃ BẮT CẮT MÔ TẢ CỦA'.encode('utf-8')),
    # "Correction request bị trùng"
    (b'Correction request b\xc3\xa1\xc2\xbb\xe2\x80\xb9 tr\xc3\xb9ng', 'Correction request bị trùng'.encode('utf-8')),
    # "Entrustment request bị trùng"
    (b'Entrustment request b\xc3\xa1\xc2\xbb\xe2\x80\xb9 tr\xc3\xb9ng', 'Entrustment request bị trùng'.encode('utf-8')),
    # "Financial action request bị trùng"
    (b'Financial action request b\xc3\xa1\xc2\xbb\xe2\x80\xb9 tr\xc3\xb9ng', 'Financial action request bị trùng'.encode('utf-8')),
    # "Đã ghi nhận khoản" 
    (b'\x5c\x78\x63\x33\x5c\x78\x38\x34\x5c\x78\x63\x32\x5c\x78\x39\x30\x5c\x78\x63\x33\x5c\x78\x38\x33\x5c\x78\x63\x32\x5c\x78\x61\x33\x20\x67\x68\x69\x20\x6e\x68\xc3\xa1\xc2\xba\xc2\xad\x6e', 'Đã ghi nhận'.encode('utf-8')),
    # "reversal trước đó"
    (b'reversal tr\xc3\x86\xc2\xb0\xc3\xa1\xc2\xbb\xe2\x80\xbac \xc3\x84\xe2\x80\x98\xc3\xb3', 'reversal trước đó'.encode('utf-8')),
]


def main() -> None:
    apply_mode = '--apply' in sys.argv
    total = 0
    for rel in ALLOWED:
        p = REPO / rel
        if not p.exists():
            continue
        b = p.read_bytes()
        orig = b
        for moji, clean in MAP:
            if moji is None or clean is None or not moji:
                continue
            count = 0
            while moji in b and count < 500:
                b = b.replace(moji, clean, 1)
                total += 1
                count += 1
            if count >= 500:
                print(f'LOOP-GUARD: {rel} cặp {moji[:20]}')
        if b != orig:
            # verify syntax still valid
            try:
                ast.parse(b.decode('utf-8'))
            except SyntaxError as e:
                print(f'SYNTAX ERROR {rel}: {e}; rollback')
                continue
            if apply_mode:
                p.with_suffix(p.suffix + '.mojibake.bak').write_bytes(orig)
                p.write_bytes(b)
                print(f'APPLIED: {rel}')
            else:
                print(f'WOULD FIX: {rel} ({total} replacements)')
    print(f'TOTAL replacements: {total}')


if __name__ == '__main__':
    main()
